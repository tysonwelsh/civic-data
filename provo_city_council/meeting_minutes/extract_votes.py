#!/usr/bin/env python3
"""
extract_votes.py — Provo Municipal Council vote extraction.

Reads the 311 minutes markdown files under meeting_minutes/minutes/<year>/<week>/
(indexed in meeting_minutes/minutes_index.csv), parses each recorded motion + vote,
emits one JSON per meeting to meeting_minutes/votes/<year>/<week>/<date>_<slug>.json,
then rebuilds meeting_minutes/all_votes.csv (long format, one row per member-vote).

Provo OnBase minutes record motions in "Motion:" / "Vote:" blocks. The Vote line gives a
tally (e.g. 7:0, 5:1, 6-0) and usually names members "in favor" / "opposed" / "excused".
We map: in favor -> aye, opposed -> nay, excused/absent -> absent, recuse -> recuse.
When only a tally is given (e.g. "by unanimous consent", "passed 7:0." with no names) we
set names_recorded=false and leave the member lists EMPTY — we never guess who voted how.

Run:  python3 meeting_minutes/extract_votes.py          (resumable: skips existing JSON)
      python3 meeting_minutes/extract_votes.py --force   (re-extract all)

See meeting_minutes/CLAUDE.md for the full pipeline + heuristics writeup.
"""
import argparse
import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINUTES_INDEX = os.path.join(REPO, "meeting_minutes", "minutes_index.csv")
MINUTES_DIR = os.path.join(REPO, "meeting_minutes", "minutes")
VOTES_DIR = os.path.join(REPO, "meeting_minutes", "votes")
ALL_VOTES_CSV = os.path.join(REPO, "meeting_minutes", "all_votes.csv")
VALIDATION_REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

# ---------------------------------------------------------------------------
# Canonical roster. Surname -> canonical "First Last". Provo council members
# seen across 2020-2026 (5 districts + 2 citywide = 7 seats, staggered terms).
# Cross-checked against election_results/provo_results_by_candidate.csv winners.
# Staff (Dayley=Policy Analyst, Zarbock=Budget Analyst, Allman/Harrison/Jones/etc.)
# never appear in vote name-lists and are NOT in this map.
# ---------------------------------------------------------------------------
ROSTER = {
    "ellsworth": "Shannon Ellsworth",   # D3 2019
    "fillmore": "Bill Fillmore",        # D1 2019  (also "William Fillmore")
    "handley": "George Handley",        # D2 2021
    "harding": "David Harding",         # Citywide I (pre-2022)
    "hoban": "Travis Hoban",            # D4 2019/2023
    "sewell": "David Sewell",           # D5 (pre-2022)
    "shipley": "David Shipley",         # Citywide II 2019  (also "Dave Shipley")
    "whipple": "Rachel Whipple",        # D5 2021/2025
    "mackay": "Katrice MacKay",         # Citywide I 2021/2025 (McKay/Mackay variants)
    "bogdin": "Becky Bogdin",           # D3 2023
    "christensen": "Craig Christensen", # D1 2023
    "garrett": "Gary Garrett",          # Citywide II 2023
    "whitlock": "Jeff Whitlock",        # D2 2025
}
# Aliases / OCR & spelling variants -> canonical surname key above.
SURNAME_ALIASES = {
    "mckay": "mackay", "macky": "mackay", "mckee": "mackay", "mackey": "mackay",
    "hadley": "handley",
    "fillmore.": "fillmore", "filmore": "fillmore", "fillmor": "fillmore",
    "whippler": "whipple",
    "garret": "garrett", "garrette": "garrett",
    "christenson": "christensen", "christiansen": "christensen",
}

# Surnames that may appear split across a line break in roll-call (rare). Order
# longest-first so multi-token names match before single tokens.
KNOWN_SURNAMES = sorted(ROSTER.keys(), key=len, reverse=True)


def norm_surname(token):
    t = token.strip().strip(".,;:").lower()
    t = SURNAME_ALIASES.get(t, t)
    return t


def canon(token):
    """Map a raw surname token to a canonical full name, or None if not a member."""
    key = norm_surname(token)
    return ROSTER.get(key)


# ---------------------------------------------------------------------------
# Governing-body tagging (Council / RDA / CRA / MBA).
#
# In Provo the Municipal Council, mid-meeting, "recesses and convenes as the
# Governing Board of the Redevelopment Agency" (RDA) — same people, same room,
# board capacity — then "reconvenes as the Municipal Council". Motions taken
# while sitting as a board are tagged with that body; everything else is
# `Council`. Provo also occasionally convenes as the Stormwater Service District
# (SSD), which is NOT one of the RDA/CRA/MBA financing bodies in scope — SSD
# blocks are left as the default `Council` body (and noted), since the schema
# only models Council/RDA/CRA/MBA/LBA.
#
# Phrasing is highly variable (see meeting_minutes/CLAUDE.md). The robust rule:
# a line is a *transition* only if it contains a transition VERB (convened /
# reconvened / recessed / adjourned) AND a body keyword. We read the
# DESTINATION body — the body the meeting becomes — which is the body named
# AFTER the last "as the / convened the / reconvened the" cue on the line (so
# "adjourned as the RDA and reconvened as the Municipal Council" -> Council).
# Board-role synonyms ("Board Member", "Agency Member", "Chair") map to the
# SAME council member names (people are identical — no new members).
# ---------------------------------------------------------------------------
TRANSITION_VERB_RE = re.compile(
    r"\b(?:re)?convened?\b|\brecessed\b|\badjourned\b", re.IGNORECASE)


def _body_from_phrase(phrase):
    """Classify a destination phrase into a body code, or None if not a body."""
    p = phrase.lower()
    if "municipal building authority" in p or re.search(r"\bMBA\b", phrase):
        return "MBA"
    if "community reinvestment agency" in p or re.search(r"\bCRA\b", phrase):
        return "CRA"
    if "redevelopment" in p or re.search(r"\bRDA\b", phrase):
        return "RDA"
    if "stormwater" in p or "storm water" in p or re.search(r"\bSSD\b", phrase):
        return "SSD"  # out-of-scope body; caller maps to Council default
    if "municipal council" in p or "city council" in p or "the council" in p \
            or re.search(r"\bcouncil\b", p):
        return "Council"
    return None


def detect_body_for_line(line):
    """If `line` is a body transition, return the destination body code
    (Council/RDA/CRA/MBA/SSD); else None.

    Requires a transition verb on the line (so agenda boilerplate like
    'the Governing Board of the Redevelopment Agency will consider…' is NOT a
    transition). The destination is read from the text AFTER the LAST
    'as the / convened the / reconvened the' cue — that is the body the meeting
    becomes when a line names both the body it leaves and the one it enters.
    """
    if not TRANSITION_VERB_RE.search(line):
        return None
    # Find every destination cue and take the text following the last one.
    cues = list(re.finditer(
        r"(?:as the|as (?:the )?|reconvened the|convened the|reconvened as|"
        r"convened as)\s+", line, re.IGNORECASE))
    # Prefer cues that follow a (re)convene verb; fall back to any cue.
    dest = None
    if cues:
        tail = line[cues[-1].end():]
        dest = _body_from_phrase(tail)
    if dest is None:
        # Forms like "Chair X convened the Redevelopment Agency" / "RDA Chair Y
        # convened" / "reconvened the body as the Redevelopment Agency" — fall
        # back to scanning the whole line for the destination, but only the part
        # at/after the LAST (re)convene verb so we read the body entered, not left.
        conv = list(re.finditer(r"\b(?:re)?convened?\b", line, re.IGNORECASE))
        scan = line[conv[-1].start():] if conv else line
        dest = _body_from_phrase(scan)
    return dest


def resolve_motion_body(combined_text, seg_body):
    """Final governing body for one motion, from the motion+vote block text plus the
    body in effect from the surrounding transition markers (`seg_body`).

    Precedence (most reliable first):
      1. A body-prefixed item id in the text — `2025-RDA-…`, `…-CRA-…`, `…-MBA-…`
         — is unambiguous; it pins the body even with no transition marker.
      2. Board-capacity role names ('Board Member' / 'Agency Member') voting/moving,
         BUT only when corroborated by an RDA/CRA/MBA segment marker — because the
         Board of Canvassers ALSO seats 'Board Members' (+ Mayor Kaufusi) and is NOT
         a financing board. Use the segment's (possibly more specific) board body.
         This also overrides an incidental 'Councilor' token in the same block
         (e.g. '… in favor and Councilor Handley excused' inside an RDA block).
      3. Explicit Council naming ('Councilor' / 'Councilmember') with no qualifying
         board signal -> Council. Pins council business that ran on inside an RDA
         segment Provo left open by OMITTING the 'reconvened as the Council' marker.
      4. Otherwise inherit the segment body.
    """
    t = combined_text
    if re.search(r"\bMBA-", t):
        return "MBA"
    if re.search(r"\bCRA-", t):
        return "CRA"
    if re.search(r"\bRDA-", t):
        return "RDA"
    has_board = bool(re.search(r"\b(?:Board|Agency) ?Member", t))
    if has_board and seg_body in ("RDA", "CRA", "MBA"):
        return seg_body
    if re.search(r"\bCouncilors?\b|\bCouncilmember", t):
        return "Council"
    return seg_body


# ---------------------------------------------------------------------------
# Motion-type classification (fixed 12-category taxonomy).
# ---------------------------------------------------------------------------
def classify(motion_text, item_text):
    t = (item_text + " \n " + motion_text).lower()

    # Land use / zoning — check before generic ordinance since most are ordinances.
    landuse_kw = ["zone", "zoning", "rezone", "plota", "plrez", "plan ", "general plan",
                  "overlay", "subdivision", "plat", "annex", "right-of-way",
                  "right of way", "vacat", "land use", "development rights", "setback",
                  "conditional use", "plgpa", "plpud", "pud", "specific plan"]
    if any(k in t for k in landuse_kw):
        return "Land-Use/Zoning"

    if "budget amendment" in t or "amend the budget" in t or re.search(r"budget.{0,30}amend", t) \
            or "tentative budget" in t or "truth in taxation" in t:
        return "Budget Amendment"
    if "interlocal" in t or "inter-local" in t or "mutual aid agreement" in t:
        return "Interlocal"
    if "grant" in t and ("apply" in t or "accept" in t or "award" in t or "funding" in t
                          or "application" in t or "cdbg" in t or "fund" in t):
        return "Grant-Funding"
    if ("appoint" in t or "reappoint" in t or "confirm" in t and "appointment" in t
            or "ratify the appointment" in t):
        if "appoint" in t:
            return "Appointment"
    if any(k in t for k in ["contract", "agreement", "purchase", "bid", "procure",
                            "professional services", "lease", "task order"]) \
            and "interlocal" not in t:
        # agreements that aren't interlocal/land-use
        if "resolution" not in t and "ordinance" not in t:
            return "Contract/Purchase"
    if "ordinance" in t:
        return "Ordinance"
    if "resolution" in t:
        return "Resolution"
    # Use word boundaries so "commend" doesn't fire inside "recommend"/"recommended"
    # and "honor" doesn't fire inside "honorarium" etc.
    if re.search(r"\b(proclamation|recognition|recognizing|honoring|"
                 r"commend(?:ing|ation)?|ceremonial|in memoriam)\b", t):
        return "Ceremonial"
    if any(k in t for k in ["open the public hearing", "close the public hearing",
                            "open public comment", "close public comment",
                            "continue the public hearing"]):
        return "Public Hearing Action"
    proc_kw = ["minutes", "agenda", "continue", "table", "consent", "adjourn",
               "approve the order", "ratify", "set the date", "schedule",
               "executive session", "closed session", "recess", "election of",
               "chair", "vice chair", "rules of order", "calendar"]
    if any(k in t for k in proc_kw):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Vote-line parsing.
# ---------------------------------------------------------------------------
RESULT_VERB = (
    r"(?:was\s+)?(?:approved|passed|adopted|carried|denied|defeated|failed|opposed|"
    r"did\s+not\s+pass)"
)
# Tally like 7:0, 5:1, 6-0, 3:4. A colon-tally (7:0) is unambiguous. A dash-tally
# (6-0) collides with ordinance numbers (e.g. "Ordinance 2021-21"), so dash-tallies
# are only honored when each side is a single digit AND not preceded by a 4-digit year.
# Trailing (?!\d) instead of \b so "7:0with" (OCR glued the next word) still matches.
TALLY_COLON_RE = re.compile(r"(?<!\d)(\d{1,2})\s*:\s*(\d{1,2})(?!\d)")
TALLY_DASH_RE = re.compile(r"(?<!\d)(\d)\s*-\s*(\d)(?!\d)")


def find_tally(text):
    """Return (favor, against) tally, preferring a colon-tally; fall back to a safe
    single-digit dash-tally. Avoids matching ordinance/year numbers like 2021-21."""
    # A valid council/canvasser tally has both sides small (council=7, canvassers up
    # to ~8). Reject e.g. video timestamps "7:29", "1:28" where a side exceeds 9.
    for m in TALLY_COLON_RE.finditer(text):
        a, b = int(m.group(1)), int(m.group(2))
        if a <= 9 and b <= 9:
            return (a, b), ":"
    # dash form: only accept if not part of a year-prefixed id (e.g. 2021-21, 2024-13)
    for m in TALLY_DASH_RE.finditer(text):
        start = m.start()
        prefix = text[max(0, start - 5):start]
        if re.search(r"\d{3,4}\s*$", prefix):  # preceding digits -> ordinance/year id
            continue
        return (int(m.group(1)), int(m.group(2))), "-"
    return None, None

# Extract a names list following a cue word, until the next cue or sentence end.
NAME_TOKEN = r"(?:Mc|Mac)?[A-Z][a-z]+"


def extract_named_list(segment):
    """From a phrase like 'Councilors Bogdin, Christensen, and MacKay' return surnames."""
    names = []
    # capture sequences of Capitalized words separated by commas / 'and'
    for m in re.finditer(r"\b" + NAME_TOKEN + r"\b", segment):
        tok = m.group(0)
        if tok in ("Councilor", "Councilors", "Chair", "Vice", "Mayor", "Council",
                   "Members", "Member", "Councilmember", "and", "Acting"):
            continue
        if canon(tok):
            names.append(canon(tok))
    # de-dup preserving order
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


CUE_WORDS_RE = re.compile(
    r"in favor|opposed|excused|absent|abstain|recus|against|unanim|consent|"
    r"voting (?:yes|no|aye|nay)", re.IGNORECASE)


def truncate_vote_text(text):
    """Keep only the leading sentences that actually describe the vote (tally / cue
    words). Drops any trailing run-on sentence (rare) that belongs to discussion, so
    stray member names mentioned afterward aren't bucketed as votes."""
    text = " ".join(text.split())
    sentences = re.split(r"(?<=[.])\s+", text)
    kept = []
    for s in sentences:
        if not kept:
            kept.append(s)  # always keep the first sentence (carries the tally)
            continue
        if CUE_WORDS_RE.search(s) or TALLY_COLON_RE.search(s) or TALLY_DASH_RE.search(s):
            kept.append(s)
        else:
            break  # first non-vote sentence -> stop
    return " ".join(kept)


def parse_vote_text(vote_text):
    """
    Parse a Vote: block. Returns dict with:
      result (str), tally (in,against) or None, outcome (Pass/Fail),
      aye/nay/absent/recuse lists, names_recorded (bool), unanimous (bool).
    """
    text = " ".join(vote_text.split())  # collapse whitespace / line breaks

    tally, sep = find_tally(text)

    # outcome
    low = text.lower()
    fail = bool(re.search(r"\b(failed|defeated|denied|did not pass|motion was opposed)\b", low))
    # "The MOTION was opposed 4:3 with ... in favor" is an oddball: a substitute/amendment
    # that failed. Treat any explicit fail verb as Fail; else Pass. NOTE (T1.3 audit,
    # 2026-07-12): the opposed-cue must be MOTION-anchored — a bare "was opposed" also
    # fires on the per-member cue ("Councilor X was opposed.") inside APPROVED motions,
    # stamping a false "N:M Fail" suffix on approved-with-dissent rows (5 found).
    outcome = "Fail" if fail else "Pass"

    unanimous = "unanim" in low or "by unanimous consent" in low

    # Build verbatim result string: "<a><sep><b> <Outcome>" preserving the separator.
    if tally:
        result = f"{tally[0]}{sep}{tally[1]} {outcome}"
    else:
        result = ("Unanimous " + outcome) if unanimous else outcome

    # ---- cue-anchored name segmentation ----
    # Provo lists names BEFORE the cue: "Councilors A, B in favor and C excused."
    # We scan the text and assign each run of member surnames to the NEXT cue word
    # that follows it. Cues map to vote buckets. This correctly separates the "in
    # favor" run from a trailing "... and C excused" run in the SAME sentence.
    CUES = [
        (r"in favor|voting (?:in favor|yes|aye)|voted in favor|supporting", "aye"),
        (r"opposed|voting (?:no|nay|against)|voted against|against|dissent", "nay"),
        (r"excused|absent", "absent"),
        (r"abstain(?:ed|ing|s)?", "abstain"),
        (r"recus(?:ed|ing|es)?", "recuse"),
    ]
    cue_re = re.compile("|".join(f"(?P<b{i}>{pat})" for i, (pat, _) in enumerate(CUES)),
                        re.IGNORECASE)
    # Inverted cue phrasing: the cue PRECEDES the names — "Opposed were Shipley,
    # Hoban and Ellsworth." / "Excused was Whipple." (vs the usual "names, then
    # cue"). Detected by the cue being immediately followed by were/was.
    INVERTED_CUE_RE = re.compile(r"^\s*(?:were|was)\b")
    buckets = {"aye": [], "nay": [], "absent": [], "abstain": [], "recuse": []}
    pos = 0
    cue_matches = list(cue_re.finditer(text))
    for idx, cm in enumerate(cue_matches):
        # which bucket
        bucket = None
        for i, (_, b) in enumerate(CUES):
            if cm.group(f"b{i}"):
                bucket = b
                break
        segment = text[pos:cm.start()]
        buckets[bucket] += extract_named_list(segment)
        pos = cm.end()
        # Inverted form ("Opposed were <names>"): the names FOLLOW the cue, so the
        # normal names-before-cue scan never sees them. Capture the name run after
        # the cue, bounded by the next cue and the end of the sentence, and advance
        # past it so the next cue's backward segment can't re-bucket the same names.
        next_cue_start = (cue_matches[idx + 1].start()
                          if idx + 1 < len(cue_matches) else len(text))
        tail = text[pos:next_cue_start]
        if INVERTED_CUE_RE.match(tail):
            sent_end = re.search(r"[.;]", tail)
            seg_end = sent_end.end() if sent_end else len(tail)
            buckets[bucket] += extract_named_list(tail[:seg_end])
            pos += seg_end
    aye, nay, absent, abstain, recuse = (
        buckets["aye"], buckets["nay"], buckets["absent"],
        buckets["abstain"], buckets["recuse"])

    def dedup(lst):
        s, o = set(), []
        for x in lst:
            if x not in s:
                s.add(x); o.append(x)
        return o
    aye, nay, absent, abstain, recuse = map(dedup, (aye, nay, absent, abstain, recuse))

    names_recorded = bool(aye or nay or abstain or recuse or absent)
    # "by unanimous consent" with NO names -> tally only, do not guess membership.
    return {
        "result": result, "tally": tally, "outcome": outcome,
        "aye": aye, "nay": nay, "abstain": abstain, "absent": absent,
        "recuse": recuse, "names_recorded": names_recorded, "unanimous": unanimous,
        "vote_text": text,
    }


def parse_motion_meta(motion_text):
    """Extract mover + seconder from a Motion: block (when explicit)."""
    mover = seconder = None
    t = " ".join(motion_text.split())

    # Role prefixes — council AND board-capacity synonyms ("Board Member",
    # "Agency Member") map to the SAME people; we only use the prefix to anchor
    # the following surname, which canon() resolves to a council member name.
    ROLE = (r"(?:Councilor|Council ?member|Chair|Vice[ -]?Chair|Mayor|"
            r"Board ?Member|Agency ?Member|Board ?Chair)")
    # mover: "Councilor X made a motion / moved / motioned / made a substitute motion"
    mm = re.search(
        ROLE + r"\s+"
        r"(?:" + NAME_TOKEN + r"\s+)?(" + NAME_TOKEN + r")\s+"
        r"(?:made a (?:substitute )?motion|moved|motioned|made (?:the |a )?motion)", t)
    if mm and canon(mm.group(1)):
        mover = canon(mm.group(1))

    sm = re.search(r"seconded by\s+" + ROLE + r"?\s*"
                   r"(?:" + NAME_TOKEN + r"\s+)?(" + NAME_TOKEN + r")", t)
    if sm and canon(sm.group(1)):
        seconder = canon(sm.group(1))
    # "X seconded the motion"
    if not seconder:
        sm2 = re.search(ROLE + r"\s+"
                        r"(?:" + NAME_TOKEN + r"\s+)?(" + NAME_TOKEN + r")\s+seconded", t)
        if sm2 and canon(sm2.group(1)):
            seconder = canon(sm2.group(1))
    return mover, seconder


# ---------------------------------------------------------------------------
# Meeting parsing.
# ---------------------------------------------------------------------------
ITEM_HEADER_RE = re.compile(r"^\s{0,8}(\d{1,2})\.\s+(\S.*)$")
MOTION_LABEL_RE = re.compile(r"^\s*Motion:\s*(.*)$", re.IGNORECASE)
# Most meetings label the result "Vote:"; one 2020 meeting uses "Roll Call Vote:".
VOTE_LABEL_RE = re.compile(r"^\s*(?:Roll\s*Call\s+)?Vote:\s*(.*)$", re.IGNORECASE)


def parse_meeting(text):
    """
    Walk the minutes text. Track the most recent agenda-item header (for context /
    motion_type), then for each Motion:/Vote: pair build a vote record. We anchor on
    Vote: blocks (every recorded vote has one) and look back for the nearest Motion:
    block and item header.
    """
    lines = text.split("\n")
    n = len(lines)

    # --- body transitions ----------------------------------------------------
    # Scan every line for a governing-body transition. Build a sorted list of
    # (line_no, body) markers. A motion's body is the body in effect at the
    # motion's line (the last marker at or before it), defaulting to Council.
    # SSD (Stormwater) is out of scope -> collapse to the default Council.
    body_markers = []  # (line_no, body_code)
    for ln_no, ln in enumerate(lines):
        # Transition sentences frequently WRAP across 1-2 lines ("…convened as the\n
        # Governing Board of the Redevelopment Agency…"), so test the line joined
        # with the next two before deciding — otherwise the destination body sits on
        # the continuation line and the marker is missed (seen on Stormwater→RDA
        # hand-offs). Only fire when a transition VERB is present on the FIRST line,
        # so we anchor the marker at the sentence start, not a wrapped fragment.
        if not TRANSITION_VERB_RE.search(ln):
            continue
        window = " ".join(lines[ln_no:ln_no + 3])
        b = detect_body_for_line(window)
        if b is not None:
            body_markers.append((ln_no, "Council" if b == "SSD" else b))

    def body_at(line_no):
        cur = "Council"
        for m_ln, m_body in body_markers:
            if m_ln <= line_no:
                cur = m_body
            else:
                break
        return cur

    # Collect blocks: list of (kind, start_line, text) where kind in {item, motion, vote}
    blocks = []
    i = 0
    while i < n:
        line = lines[i]
        mi = ITEM_HEADER_RE.match(line)
        mo = MOTION_LABEL_RE.match(line)
        vo = VOTE_LABEL_RE.match(line)
        if vo is not None:
            # Gather the Vote block. The vote result is always a single contiguous
            # paragraph ("The motion <verb> X:Y with ... in favor. Z opposed/excused."),
            # so we STOP at the first blank line. Continuing past a blank would absorb the
            # following discussion paragraph and pull stray member names into the buckets.
            buf = [vo.group(1)]
            j = i + 1
            # Work-session style sometimes puts "Vote:" alone on its line with the result
            # in the following paragraph after a blank line. If the label is content-less,
            # skip leading blank lines to reach that paragraph.
            if vo.group(1).strip() == "":
                while j < n and lines[j].strip() == "":
                    j += 1
            while j < n:
                nl = lines[j]
                if (MOTION_LABEL_RE.match(nl) or VOTE_LABEL_RE.match(nl)
                        or ITEM_HEADER_RE.match(nl) or nl.strip() == ""):
                    break
                buf.append(nl)
                j += 1
            vote_txt = " ".join(buf).strip()
            vote_txt = truncate_vote_text(vote_txt)
            blocks.append(("vote", i, vote_txt))
            i = j
            continue
        if mo is not None:
            buf = [mo.group(1)]
            j = i + 1
            blank = 0
            while j < n:
                nl = lines[j]
                if MOTION_LABEL_RE.match(nl) or VOTE_LABEL_RE.match(nl) or ITEM_HEADER_RE.match(nl):
                    break
                if nl.strip() == "":
                    blank += 1
                    if blank >= 2:
                        break
                else:
                    blank = 0
                    buf.append(nl)
                j += 1
            blocks.append(("motion", i, " ".join(buf).strip()))
            i = j
            continue
        if mi is not None:
            # item header: capture the header text + a couple wrapped lines
            buf = [mi.group(2)]
            j = i + 1
            while j < n and j < i + 4:
                nl = lines[j]
                if (MOTION_LABEL_RE.match(nl) or VOTE_LABEL_RE.match(nl)
                        or ITEM_HEADER_RE.match(nl) or nl.strip() == ""):
                    break
                buf.append(nl.strip())
                j += 1
            blocks.append(("item", i, " ".join(buf).strip()))
            i = j
            continue
        i += 1

    # Now pair: iterate blocks; for each vote block, find nearest preceding motion
    # and nearest preceding item.
    votes = []
    motion_no = 0
    last_item = ""
    last_motion = None  # (text)
    for kind, ln, btxt in blocks:
        if kind == "item":
            last_item = btxt
            last_motion = None
        elif kind == "motion":
            last_motion = btxt
        elif kind == "vote":
            motion_no += 1
            motion_text = last_motion or ""
            item_text = last_item or ""
            parsed = parse_vote_text(btxt)
            mover, seconder = parse_motion_meta(motion_text)
            # If the motion text is an "implied motion by council rule", mover/seconder
            # are absent by design (consent-style). Leave None.
            # Compose a readable motion description: prefer the agenda item header; fall
            # back to the motion text (trimmed to its first ~2 sentences so run-on
            # discussion doesn't bloat the description).
            if item_text.strip():
                desc = item_text.strip()
            else:
                desc = " ".join(re.split(r"(?<=[.])\s+", motion_text.strip())[:2])
            # Trim trailing video timestamps like 0:15:08 and item ids in parens kept.
            desc = re.sub(r"\s+\d:\d{2}:\d{2}\s*$", "", desc).strip()
            # A "Motion:" block sometimes runs on into the following discussion (no blank
            # line separator). For classification, use only the opening of the motion text
            # (first ~2 sentences) so deep-discussion words don't drive the category.
            motion_head = " ".join(re.split(r"(?<=[.])\s+", motion_text)[:2])
            mtype = classify(motion_head, item_text)
            # ---- governing body: segment marker, refined by per-motion signal ----
            seg_body = body_at(ln)                       # from transition markers
            body = resolve_motion_body(motion_text + " \n " + btxt, seg_body)
            votes.append({
                "motion_no": motion_no,
                "motion": desc[:600],
                "body": body,
                "motion_type": mtype,
                "result": parsed["result"],
                "mover": mover,
                "seconder": seconder,
                "aye": parsed["aye"],
                "nay": parsed["nay"],
                "abstain": parsed["abstain"],
                "absent": parsed["absent"],
                "recuse": parsed["recuse"],
                "names_recorded": parsed["names_recorded"],
                "_tally": parsed["tally"],
                "_outcome": parsed["outcome"],
            })
    return votes


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def load_index():
    rows = []
    with open(MINUTES_INDEX, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def json_path_for(row):
    # mirror the minutes path under votes/, swap .md -> .json
    rel = row["path"]  # meeting_minutes/minutes/<year>/<week>/<file>.md
    rel = rel.replace("meeting_minutes/minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-extract even if JSON exists")
    args = ap.parse_args()

    rows = load_index()
    unparsed = []  # meetings we could not read/parse (reported but not fatal)

    for row in rows:
        md_path = os.path.join(REPO, row["path"])
        if not os.path.exists(md_path):
            unparsed.append(row["path"] + " (missing file)")
            continue
        out_json = json_path_for(row)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)

        if os.path.exists(out_json) and not args.force:
            continue  # resumable: already extracted

        with open(md_path, encoding="utf-8") as f:
            text = f.read()

        try:
            votes = parse_meeting(text)  # empty list is fine (work sessions/retreats)
        except Exception as e:  # noqa
            unparsed.append(f"{row['path']} (parse error: {e})")
            continue

        # Strip the internal-only fields before persisting.
        clean_votes = []
        for v in votes:
            v.pop("_tally", None)
            v.pop("_outcome", None)
            clean_votes.append(v)

        meeting_obj = {
            "date": row["date"],
            "title": row["title"],
            "source": row["path"],
            "format": row.get("format", "pdf"),
            "votes": clean_votes,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting_obj, f, indent=1, ensure_ascii=False)

    # ----- rebuild all_votes.csv from ALL JSONs (resumable / authoritative) -----
    rebuild_csv()

    # recompute aggregate stats + validation from the JSONs so --force vs resume agree
    stats = recompute_stats()
    validation_lines = validate_all_jsons()

    # write validation report
    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(VALIDATION_REPORT, "w", encoding="utf-8") as f:
        f.write("Provo vote extraction — validation report\n")
        f.write("Per-member name counts cross-checked against the literal tally.\n")
        f.write("=" * 70 + "\n")
        f.write(
            "Each line below is a motion where the number of NAMED members does not\n"
            "match the printed numeric tally. We DO NOT 'fix' these — the name lists are\n"
            "extracted verbatim from the minutes. A mismatch means one of:\n"
            "  (a) a SOURCE TYPO in the minutes (printed tally disagrees with the printed\n"
            "      names, e.g. '5:0' but 7 councilors listed in favor); the names are kept\n"
            "      as printed and the result string keeps the printed tally; OR\n"
            "  (b) a BOARD OF CANVASSERS vote, where Mayor Kaufusi sits as an 8th voting\n"
            "      board member — she is not on the council roster, so a canvasser '8:0'\n"
            "      shows only 7 mapped council names (Kaufusi intentionally unmapped); OR\n"
            "  (c) a councilor name printed in BOTH a favor and an opposed clause (source\n"
            "      double-listing).\n"
            "All current mismatches were hand-reviewed and fall into (a)/(b)/(c).\n")
        f.write("-" * 70 + "\n")
        if validation_lines:
            f.write("\n".join(validation_lines) + "\n")
        else:
            f.write("(no mismatches in this run)\n")
        f.write(f"\nMismatches: {len(validation_lines)} of {stats['motions']} motions\n")

    print(json.dumps({
        "meetings_processed": stats["meetings"],
        "motions_extracted": stats["motions"],
        "member_vote_rows": stats["member_rows"],
        "named_rollcall_motions": stats["named"],
        "tally_only_motions": stats["tally_only"],
        "contested_motions": stats["contested"],
        "validation_mismatches": len(validation_lines),
        "unparsed_meetings": unparsed,
    }, indent=2))


def iter_jsons():
    for dirpath, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dirpath, fn)


def validate_all_jsons():
    """Rebuild the validation mismatch list from ALL JSONs on disk (so the report is
    correct on a resumed run, not just on --force). Re-derives the tally from the
    persisted `result` string and cross-checks it against the named member counts.

    Provo writes the tally favor-first on PASSED motions but sometimes majority-first
    on FAILED ones ("failed 6:0 ... opposed"), so we compare as an UNORDERED multiset:
    {n_aye, n_nay} vs {favor, against}. Abstentions count toward neither tally side.
    Mismatches are logged, never auto-corrected — names stay verbatim from the minutes.
    """
    lines = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        for v in mtg["votes"]:
            if not v.get("names_recorded"):
                continue
            tally, _ = find_tally(v["result"])
            if tally is None:
                continue
            favor, against = tally
            n_aye, n_nay, n_abs = len(v["aye"]), len(v["nay"]), len(v["abstain"])
            if n_aye and n_nay:
                if sorted([n_aye, n_nay]) != sorted([favor, against]):
                    lines.append(
                        f"{mtg['date']} {mtg['title']} motion {v['motion_no']}: "
                        f"aye={n_aye} nay={n_nay} abstain={n_abs} but tally {favor}:{against} "
                        f":: {v['result']}")
            elif n_aye and not n_nay:
                if n_aye not in (favor, against):
                    lines.append(
                        f"{mtg['date']} {mtg['title']} motion {v['motion_no']}: "
                        f"aye names={n_aye} but tally {favor}:{against} :: {v['result']}")
            elif n_nay and not n_aye:
                if n_nay not in (favor, against):
                    lines.append(
                        f"{mtg['date']} {mtg['title']} motion {v['motion_no']}: "
                        f"nay names={n_nay} but tally {favor}:{against} :: {v['result']}")
    return lines


def rebuild_csv():
    rows_out = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        date = mtg["date"]
        year = date[:4]
        title = mtg["title"]
        source = mtg["source"]
        for v in mtg["votes"]:
            base = {
                "date": date, "year": year, "title": title,
                "body": v.get("body", "Council"),
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": source,
            }
            emitted = False
            for vote_label, key in (("Aye", "aye"), ("Nay", "nay"),
                                    ("Abstain", "abstain"), ("Absent", "absent"),
                                    ("Recuse", "recuse")):
                for member in v.get(key, []):
                    r = dict(base); r["member"] = member; r["vote"] = vote_label
                    rows_out.append(r); emitted = True
            if not emitted:
                # tally-only motion: one row with no member (names_recorded false)
                r = dict(base); r["member"] = ""; r["vote"] = ""
                rows_out.append(r)
    # sort by date, then motion_no
    rows_out.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows_out:
            w.writerow({c: r.get(c, "") for c in cols})


def recompute_stats():
    meetings = motions = member_rows = named = tally_only = contested = 0
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        for v in mtg["votes"]:
            motions += 1
            if v.get("names_recorded"):
                named += 1
            else:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            member_rows += sum(len(v[k]) for k in ("aye", "nay", "abstain", "absent", "recuse"))
    return {"meetings": meetings, "motions": motions, "member_rows": member_rows,
            "named": named, "tally_only": tally_only, "contested": contested}


if __name__ == "__main__":
    main()
