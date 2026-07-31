#!/usr/bin/env python3
"""
extract_votes.py — Lehi City Council vote extraction.

Reads the 175 minutes markdown files under meeting_minutes/minutes/<year>/<week>/
(indexed in meeting_minutes/minutes_index.csv), parses each recorded motion + roll-call
vote, emits one JSON per meeting to meeting_minutes/votes/<year>/<week>/<date>_<slug>.json,
then rebuilds meeting_minutes/all_votes.csv (long format, one row per member-vote).

Lehi Granicus minutes record motions in "Motion:" / "Roll Call Vote:" blocks. The roll
call comes in TWO shapes (both handled):

  Format A — per-member inline (most common):
      Roll Call Vote: Councilor Albrecht, Yes; Councilor Condie, Yes; Councilor Hancock,
      Absent; Councilor Newall, Yes; and Councilor Stallings, No. The motion passed with
      3 in favor, 1 opposed, and 1 absent.

  Format B — label blocks (2025+ and some older):
      Roll Call Vote:   YES: Paige Albrecht, Chris Condie, Paul Hancock, Heather Newall,
                        Michelle Stallings.   NO: None. The motion carried: 4 - 0

Name lists WRAP across lines, so the whole vote block is flattened to one string with
[\s\S] semantics (we join the buffered lines) before parsing — never anchor on a single
line. Names separate by comma AND/OR "and" AND/OR semicolon; we anchor on roster surnames
so the exact separator does not matter.

Mayor is NON-VOTING (presides) and is NOT on the voting roster — he is excluded from vote
rows UNLESS the minutes explicitly record him casting a tie-break vote in the roll call
(e.g. "...Mayor Johnson, No."), in which case that single row is emitted and flagged.
"Mayor Pro Tempore <Surname>" is a COUNCILOR acting as chair — mapped to that councilor,
NOT to the mayor.

When only a tally / "passed unanimously" is given with NO per-member names we set
names_recorded=false and leave the member lists EMPTY — we never guess who voted how.

Run:  python3 meeting_minutes/extract_votes.py          (resumable: skips existing JSON)
      python3 meeting_minutes/extract_votes.py --force   (re-extract all)

See meeting_minutes/CLAUDE.md for the full pipeline + heuristics writeup.
"""
import argparse
import csv
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINUTES_INDEX = os.path.join(REPO, "meeting_minutes", "minutes_index.csv")
VOTES_DIR = os.path.join(REPO, "meeting_minutes", "votes")
ALL_VOTES_CSV = os.path.join(REPO, "meeting_minutes", "all_votes.csv")

# ---------------------------------------------------------------------------
# Canonical roster. Surname key -> canonical "First Last". Built from the
# minutes corpus (2020-2026). 5 at-large seats, staggered terms; the people who
# have held them across the window:
#   Albrecht, Condie, Hancock, Koivisto, Southwick  (2020-2025 cohort)
#   Newall, Stallings                               (carry into current)
#   Freeman, Harrison, Lockhart                     (current cohort, 2025+)
# Mayor Mark Johnson (2020-2025) and Mayor Paul Binns (current) PRESIDE and do
# NOT vote — they are kept OUT of ROSTER and live in MAYORS below, only emitted
# when an explicit tie-break vote is recorded.
# ---------------------------------------------------------------------------
ROSTER = {
    "albrecht": "Paige Albrecht",
    "condie": "Chris Condie",
    "hancock": "Paul Hancock",
    "koivisto": "Katie Koivisto",
    "southwick": "Mike Southwick",
    "newall": "Heather Newall",
    "stallings": "Michelle Stallings",
    "freeman": "Rachel Freeman",
    "harrison": "James Harrison",
    "lockhart": "Emily Lockhart",
}
# Mayors (non-voting). Only emitted on an explicit recorded tie-break vote.
MAYORS = {
    "johnson": "Mark Johnson",
    "binns": "Paul Binns",
}
MAYOR_ALIASES = {"jonson": "johnson", "jhonson": "johnson", "johnston": "johnson"}
# OCR / typo / spelling variants -> canonical surname key above.
SURNAME_ALIASES = {
    "codie": "condie", "conde": "condie",
    "albreht": "albrecht", "albrect": "albrecht",
    "hanock": "hancock", "hancok": "hancock",
    "newell": "newall", "newal": "newall",
    "stalling": "stallings",
    "koiviso": "koivisto", "koivsto": "koivisto",
    "southwic": "southwick",
}


def norm_surname(token):
    t = token.strip().strip(".,;:").lower()
    return SURNAME_ALIASES.get(t, t)


def canon(token):
    """Map a raw surname token to a canonical council member name, or None."""
    return ROSTER.get(norm_surname(token))


def canon_mayor(token):
    """Map a raw surname token to a canonical mayor name, or None."""
    t = norm_surname(token)
    t = MAYOR_ALIASES.get(t, t)
    return MAYORS.get(t)


# ---------------------------------------------------------------------------
# Governing-body tagging (Council / RDA / MBA).
#
# Slug drives the default: building-authority-meeting -> MBA, city-council-meeting
# -> Council. Within a council meeting, Lehi sometimes "recesses to conduct the
# Redevelopment Agency Meeting" then "reconvened" as the council. Motions taken
# while recessed as the RDA are tagged body=RDA; everything else Council.
#
# In practice Lehi minutes the RDA business in its own record and the council file
# only shows the recess + an immediate reconvene (back-to-back), so the RDA bracket
# usually contains zero motions — but the bracket detection is here so any inline
# RDA motion is tagged correctly. We track an OPEN/CLOSE state machine: a recess/
# adjourn line naming the Redevelopment Agency OPENS the bracket; the next
# "reconvened" line CLOSES it. The motion that *moves* to recess (a "Motion:" line,
# or any line containing "motion") is itself Council business and must NOT open the
# bracket, so opener lines that mention a motion are excluded.
# ---------------------------------------------------------------------------
RDA_OPEN_RE = re.compile(
    r"(recess|recessed|adjourn|adjourned|went into|move[d]? into|move[d]? to)"
    r"[\s\S]{0,80}?(redevelopment|\bRDA\b)", re.IGNORECASE)
MBA_OPEN_RE = re.compile(
    r"(recess|recessed|adjourn|adjourned|went into|move[d]? into|move[d]? to)"
    r"[\s\S]{0,80}?(building authority|\bMBA\b|\bLBA\b)", re.IGNORECASE)
RECONVENE_RE = re.compile(r"\breconven", re.IGNORECASE)


def body_marker_for_line(line):
    """Return ('open','RDA'|'MBA') / ('close',None) / None for a transition line.

    A line that contains the word 'motion' is a motion to recess (Council
    business), not the recess narrative itself, so it does not open a bracket.
    """
    if RECONVENE_RE.search(line):
        return ("close", None)
    has_motion = re.search(r"\bmotion\b", line, re.IGNORECASE) is not None
    if not has_motion:
        if MBA_OPEN_RE.search(line):
            return ("open", "MBA")
        if RDA_OPEN_RE.search(line):
            return ("open", "RDA")
    return None


# ---------------------------------------------------------------------------
# Motion-type classification (fixed 12-category taxonomy).
# ---------------------------------------------------------------------------
def classify(motion_text, item_text):
    t = (item_text + " \n " + motion_text).lower()

    landuse_kw = ["zone", "zoning", "rezone", "general plan", "overlay", "subdivision",
                  "plat", "annex", "right-of-way", "right of way", "vacat", "land use",
                  "setback", "conditional use", "development code", "preliminary",
                  "site plan", "pud", "planned unit", "concept plan", "final plan",
                  "development agreement", "area plan"]
    if any(k in t for k in landuse_kw):
        return "Land-Use/Zoning"

    if ("budget amendment" in t or "amend the budget" in t or "tentative budget" in t
            or "final budget" in t or "truth in taxation" in t
            or re.search(r"budget.{0,30}amend", t) or "adopting a budget" in t
            or "adopt the budget" in t):
        return "Budget Amendment"
    if "interlocal" in t or "inter-local" in t or "mutual aid" in t:
        return "Interlocal"
    if "grant" in t and any(k in t for k in ["apply", "accept", "award", "funding",
                                             "application", "cdbg", "fund"]):
        return "Grant-Funding"
    if ("appoint" in t or "reappoint" in t or "ratify the appointment" in t
            or "appointing" in t):
        return "Appointment"
    if any(k in t for k in ["contract", "agreement", "purchase", "bid", "procure",
                            "professional services", "lease", "task order",
                            "change order"]) and "interlocal" not in t:
        if "resolution" not in t and "ordinance" not in t:
            return "Contract/Purchase"
    if "ordinance" in t:
        return "Ordinance"
    if "resolution" in t:
        return "Resolution"
    if re.search(r"\b(proclamation|recognition|recognizing|honoring|"
                 r"commend(?:ing|ation)?|ceremonial|in memoriam|oath of office|"
                 r"presentation)\b", t):
        return "Ceremonial"
    if any(k in t for k in ["open the public hearing", "close the public hearing",
                            "open public comment", "close public comment",
                            "continue the public hearing", "public hearing"]):
        return "Public Hearing Action"
    proc_kw = ["minutes", "consent agenda", "agenda", "continue", "table", "consent",
               "adjourn", "ratify", "set the date", "schedule", "closed session",
               "closed meeting", "executive session", "recess", "mayor pro tem",
               "rules of order", "calendar", "pulled", "approve the order",
               "move into", "temporarily leave", "leave the council",
               "rda meeting", "redevelopment agency meeting",
               "building authority meeting"]
    if any(k in t for k in proc_kw):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Roll-call parsing.
# ---------------------------------------------------------------------------
VOTE_WORDS = {
    "yes": "aye", "aye": "aye", "yea": "aye", "y": "aye",
    "no": "nay", "nay": "nay", "n": "nay",
    "absent": "absent", "excused": "absent",
    "abstain": "abstain", "abstained": "abstain", "abstaining": "abstain",
    "recuse": "recuse", "recused": "recuse",
}
# A capitalized name token (handles Mc/Mac, hyphenated names left alone).
NAME_TOKEN = r"(?:Mc|Mac)?[A-Z][a-z]+"

# Format A: "<...words...> Surname, Vote" pairs separated by ; or , or 'and'.
# We capture the LAST capitalized token before the comma (the surname) and the
# vote word after it. Role prefixes (Councilor / Mayor Pro Tempore / Mr. / Ms.)
# precede the surname and are ignored — the surname resolves via canon().
PAIR_RE = re.compile(
    r"(" + NAME_TOKEN + r")\s*,\s*"
    r"(Yes|Aye|Yea|No|Nay|Absent|Excused|Abstained?|Abstaining|Recused?)\b",
    re.IGNORECASE)

# Format B label segmentation.
LABEL_RE = re.compile(
    r"\b(YES|AYE|NO|NAY|ABSTAIN(?:ING)?|ABSTENTIONS?|ABSENT|EXCUSED|RECUSED?)\s*:",
    re.IGNORECASE)
LABEL_TO_BUCKET = {
    "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
    "abstain": "abstain", "abstaining": "abstain", "abstention": "abstain",
    "abstentions": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}

RESULT_CUT_RE = re.compile(r"\bThe\s+motion\b|\bThe\s+Motion\b|\bMotion\s+(?:passed|"
                           r"failed|carried)\b", re.IGNORECASE)


def _mark_mayor_in_pair(name_token, prefix_text):
    """A pair is a Mayor tie-break only when the role prefix is the actual mayor
    ('Mayor Johnson'), NOT 'Mayor Pro Tempore <Councilor>'. The prefix_text is the
    text immediately preceding the surname token."""
    if canon_mayor(name_token) is None:
        return None
    # token resolved to a mayor surname; confirm it isn't a councilor pro-tem case
    # (mayors Johnson/Binns are not roster surnames, so canon() is None for them).
    return canon_mayor(name_token)


def extract_names_from_segment(segment):
    """Return (council_names, mayor_names) for roster/mayor surnames in a Format-B
    label segment. 'None' (no one) yields empty lists."""
    council, mayors = [], []
    if re.search(r"\bNone\b", segment, re.IGNORECASE) and not re.search(
            r"[A-Z][a-z]+\s*,", segment):
        # "None" with no real names
        pass
    for m in re.finditer(r"\b" + NAME_TOKEN + r"\b", segment):
        tok = m.group(0)
        if tok in ("Councilor", "Councilors", "Councilmember", "Council", "Chair",
                   "Vice", "Mayor", "Pro", "Tempore", "Tempe", "Tem", "Member",
                   "Members", "None", "Mr", "Ms", "Mrs", "The", "Acting"):
            continue
        c = canon(tok)
        if c:
            council.append(c)
            continue
        mm = canon_mayor(tok)
        if mm:
            mayors.append(mm)
    return council, mayors


def parse_rollcall(block):
    """Parse a flattened roll-call block string. Returns dict with bucket lists
    (canonical council names), mayor_votes {name: bucket}, names_recorded, and the
    cleaned result string + outcome + tally."""
    text = " ".join(block.split())  # flatten line wraps

    buckets = {"aye": [], "nay": [], "absent": [], "abstain": [], "recuse": []}
    mayor_votes = {}  # full name -> bucket ('aye'/'nay'/...)

    # ----- outcome from the result sentence -----
    low = text.lower()
    fail = bool(re.search(r"\b(failed|defeated|denied|did not pass|was not approved|"
                          r"does not pass)\b", low))
    outcome = "Fail" if fail else "Pass"
    unanimous = "unanim" in low

    # ----- region that holds the names (cut off the result sentence) -----
    cut = RESULT_CUT_RE.search(text)
    names_region = text[:cut.start()] if cut else text

    # ----- Format B (label blocks) if a YES:/NO: label is present -----
    if LABEL_RE.search(names_region):
        labels = list(LABEL_RE.finditer(names_region))
        for idx, lm in enumerate(labels):
            bucket = LABEL_TO_BUCKET.get(lm.group(1).lower())
            if bucket is None:
                continue
            seg_end = labels[idx + 1].start() if idx + 1 < len(labels) else len(names_region)
            seg = names_region[lm.end():seg_end]
            council, mayors = extract_names_from_segment(seg)
            for c in council:
                buckets[bucket].append(c)
            for mname in mayors:
                mayor_votes[mname] = bucket
    else:
        # ----- Format A (per-member inline pairs) -----
        for m in PAIR_RE.finditer(text):
            tok = m.group(1)
            vote_word = m.group(2).lower().rstrip("ed").rstrip("ing")
            # normalize via VOTE_WORDS using the full original word
            vw = m.group(2).lower()
            bucket = VOTE_WORDS.get(vw) or VOTE_WORDS.get(vote_word)
            if bucket is None:
                continue
            c = canon(tok)
            if c:
                buckets[bucket].append(c)
                continue
            mm = canon_mayor(tok)
            if mm:
                mayor_votes[mm] = bucket

    # ----- narrative Mayor tie-break (either format) -----
    # When the council ties, the Mayor's vote is often recorded in PROSE rather than
    # in a label/pair: "Mayor Johnson voted YES.", "Mayor Jonson was asked to break
    # the tie and voted Yes." Capture it if not already seen as a pair/label.
    if not mayor_votes:
        nm = re.search(
            r"Mayor\s+(" + NAME_TOKEN + r")\b[^.]*?\bvoted\s+"
            r"(yes|aye|no|nay|in favor|against|to approve|to deny)",
            text, re.IGNORECASE)
        if nm:
            mname = canon_mayor(nm.group(1))
            if mname:
                d = nm.group(2).lower()
                mb = "aye" if d in ("yes", "aye", "in favor", "to approve") else "nay"
                mayor_votes[mname] = mb

    # de-dup council buckets, preserve order
    def dedup(lst):
        s, o = set(), []
        for x in lst:
            if x not in s:
                s.add(x); o.append(x)
        return o
    for k in buckets:
        buckets[k] = dedup(buckets[k])

    # ----- tallies -----
    # Council-only counts plus mayor's tie-break vote folded into the final tally.
    n_aye = len(buckets["aye"]) + sum(1 for v in mayor_votes.values() if v == "aye")
    n_nay = len(buckets["nay"]) + sum(1 for v in mayor_votes.values() if v == "nay")

    names_recorded = any(buckets[k] for k in buckets) or bool(mayor_votes)

    # printed tally from the minutes' own result sentence. The favor / opposed counts
    # are each labeled and may be separated by commas OR "and" ("4 in favor and 1
    # opposed", "3 in favor, 2 opposed, and 1 absent"), so scan each independently;
    # absent/abstain counts are NOT part of the for/against tally. Fall back to a
    # dash/colon tally ("carried 3-2", "passed 4:3"; hyphen or en-dash).
    printed = None
    fm = re.search(r"(\d+)\s+in favor", low)
    om = re.search(r"(\d+)\s+(?:opposed|against)", low)
    if fm:
        printed = (int(fm.group(1)), int(om.group(1)) if om else 0)
    if printed is None:
        # prefer the FINAL outcome tally (carried/passed/failed) over an interim
        # "tied: 2-2" that a Mayor tie-break then resolves ("carried 3-2").
        tm = re.search(r"(?:carried|passed|failed)\s*:?\s*(\d+)\s*[:\-–]\s*(\d+)", low)
        if tm is None:
            tm = re.search(r"tied\s*:?\s*(\d+)\s*[:\-–]\s*(\d+)", low)
        if tm:
            printed = (int(tm.group(1)), int(tm.group(2)))

    if names_recorded:
        result = f"{n_aye}:{n_nay} {outcome}"
    elif printed is not None:
        a, b = printed
        # orient by outcome: on a FAIL the larger side is the losing/against count
        result = f"{a}:{b} {outcome}"
    elif unanimous:
        result = f"Unanimous {outcome}"
    else:
        result = outcome

    return {
        "buckets": buckets,
        "mayor_votes": mayor_votes,
        "names_recorded": names_recorded,
        "unanimous": unanimous,
        "outcome": outcome,
        "result": result,
        "n_aye": n_aye,
        "n_nay": n_nay,
        "printed": printed,
        "vote_text": text,
    }


def parse_motion_meta(motion_text):
    """Extract mover + seconder from a Motion: block. Handles 'Councilor X moved',
    'Heather Newall moved', 'Mr. Hancock moved', 'Mayor Pro Tempore Condie moved',
    'Council Condie amended his motion', and '... seconded the motion'."""
    t = " ".join(motion_text.split())
    mover = seconder = None

    mm = re.search(r"(" + NAME_TOKEN + r")\s+"
                   r"(?:moved|move|moves|made\s+a\s+(?:substitute\s+)?motion|"
                   r"made\s+the\s+motion|amended\s+(?:his|her|the|their)\s+motion)", t)
    if mm and canon(mm.group(1)):
        mover = canon(mm.group(1))

    sm = re.search(r"seconded\s+by\s+(?:[A-Z][a-z]+\.?\s+)*?(" + NAME_TOKEN + r")", t)
    if sm and canon(sm.group(1)):
        seconder = canon(sm.group(1))
    if not seconder:
        sm2 = re.search(r"(" + NAME_TOKEN + r")\s+seconded", t)
        if sm2 and canon(sm2.group(1)):
            seconder = canon(sm2.group(1))
    return mover, seconder


# ---------------------------------------------------------------------------
# Meeting parsing.
# ---------------------------------------------------------------------------
ITEM_HEADER_RE = re.compile(r"^\s{0,8}(\d{1,2}(?:\.\d+)?)\s*[.)]\s+(\S.*)$")
MOTION_LABEL_RE = re.compile(
    r"^\s*(?:Amended\s+|Substitute\s+)?Motion:\s*(.*)$", re.IGNORECASE)
VOTE_LABEL_RE = re.compile(r"^\s*(?:Roll\s*Call\s+)?Vote:\s*(.*)$", re.IGNORECASE)


def parse_meeting(text, default_body):
    lines = text.split("\n")
    n = len(lines)

    # --- body brackets: ONLY honor a MATCHED open(recess->RDA/MBA) ... close
    # (reconvene) pair. Lehi minutes RDA/MBA business in a SEPARATE record, so a
    # council file that "recessed for an RDA meeting" but never records a
    # "reconvened" line is just pointing at that separate meeting — its later
    # motions are still Council business (the reconvene is omitted). An UNMATCHED
    # open is therefore discarded (collapses to Council), and a reconvene with no
    # open pending is a no-op. The genuine inline brackets Lehi does record are
    # back-to-back (recess at 8:00 / reconvened at 8:05) and contain no motions.
    spans = []                       # (open_line, close_line, body)
    open_stack = []                  # [(open_line, body)]
    if default_body == "Council":    # brackets only meaningful inside council mtgs
        for ln_no, ln in enumerate(lines):
            mark = body_marker_for_line(ln)
            if mark is None:
                continue
            kind, body = mark
            if kind == "open":
                open_stack.append((ln_no, body))
            elif kind == "close" and open_stack:
                o_ln, o_body = open_stack.pop()
                spans.append((o_ln, ln_no, o_body))
    # unmatched opens left in open_stack are intentionally dropped.

    def body_at(line_no):
        b = default_body
        for o_ln, c_ln, o_body in spans:
            if o_ln <= line_no < c_ln:
                b = o_body          # innermost matched bracket wins
        return b

    # --- collect blocks ---
    blocks = []
    i = 0
    while i < n:
        line = lines[i]
        vo = VOTE_LABEL_RE.match(line)
        mo = MOTION_LABEL_RE.match(line)
        mi = ITEM_HEADER_RE.match(line)
        if vo is not None:
            buf = [vo.group(1)]
            j = i + 1
            if vo.group(1).strip() == "":
                while j < n and lines[j].strip() == "":
                    j += 1
            while j < n:
                nl = lines[j]
                if (MOTION_LABEL_RE.match(nl) or VOTE_LABEL_RE.match(nl)
                        or ITEM_HEADER_RE.match(nl)):
                    break
                if nl.strip() == "":
                    # The result clause ("The motion FAILED with 2 in favor, 3
                    # opposed.") is sometimes set off by a blank line from the
                    # roll-call names. Peek past blanks: ONLY if the next content line
                    # is unambiguously that result clause do we absorb it (and only it,
                    # up to the next blank) so outcome/tie-break aren't lost — then
                    # stop. We do NOT continue on generic "The motion …" / "Mayor …"
                    # lines, which are discussion and would leak the next motion in.
                    k = j
                    while k < n and lines[k].strip() == "":
                        k += 1
                    if k < n and re.match(
                            r"\s*The\s+motion\s+(?:passed|failed|carried|tied|"
                            r"did\s+not|was\s+(?:approved|denied|defeated))\b",
                            lines[k], re.IGNORECASE):
                        while k < n and lines[k].strip() != "":
                            buf.append(lines[k])
                            k += 1
                        j = k
                    break
                buf.append(nl)
                j += 1
            blocks.append(("vote", i, " ".join(buf).strip()))
            i = j
            continue
        if mo is not None:
            buf = [mo.group(1)]
            j = i + 1
            blank = 0
            while j < n:
                nl = lines[j]
                if (MOTION_LABEL_RE.match(nl) or VOTE_LABEL_RE.match(nl)
                        or ITEM_HEADER_RE.match(nl)):
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

    # --- pair votes with nearest preceding motion + item ---
    votes = []
    motion_no = 0
    last_item = ""
    last_motion = None
    for kind, ln, btxt in blocks:
        if kind == "item":
            last_item = btxt
        elif kind == "motion":
            last_motion = btxt
        elif kind == "vote":
            motion_no += 1
            motion_text = last_motion or ""
            item_text = last_item or ""
            parsed = parse_rollcall(btxt)
            mover, seconder = parse_motion_meta(motion_text)

            motion_head = " ".join(re.split(r"(?<=[.])\s+", motion_text)[:2])
            # A procedural SUB-motion (recess / move into a board meeting / closed
            # session / table / adjourn) sits UNDER a substantive agenda item but is
            # not about it — describe & classify it from the MOTION text, not the
            # item header it inherits, so e.g. "move into an RDA meeting" isn't typed
            # Land-Use because it happens to sit under a zoning item.
            proc_motion = re.search(
                r"\b(recess|temporarily leave|moved? into|adjourn|closed session|"
                r"closed meeting|table the|tabled\b|into an?\s+(?:RDA|Redevelopment|"
                r"Building Authority|Local Building Authority))\b",
                motion_text, re.IGNORECASE)
            if proc_motion:
                desc = " ".join(re.split(r"(?<=[.])\s+", motion_text.strip())[:2])
                mtype = classify(motion_head, "")
            elif item_text.strip():
                desc = item_text.strip()
                mtype = classify(motion_head, item_text)
            else:
                desc = " ".join(re.split(r"(?<=[.])\s+", motion_text.strip())[:2])
                mtype = classify(motion_head, item_text)
            desc = re.sub(r"\s+\d:\d{2}:\d{2}\s*$", "", desc).strip()
            body = body_at(ln)

            # build member lists; mayor tie-break folded into aye/nay buckets as
            # the mayor's full name, plus a flag.
            aye = list(parsed["buckets"]["aye"])
            nay = list(parsed["buckets"]["nay"])
            abstain = list(parsed["buckets"]["abstain"])
            absent = list(parsed["buckets"]["absent"])
            recuse = list(parsed["buckets"]["recuse"])
            mayor_tiebreak = False
            mayor_name = None
            for mname, mbucket in parsed["mayor_votes"].items():
                mayor_tiebreak = True
                mayor_name = mname
                {"aye": aye, "nay": nay, "abstain": abstain,
                 "absent": absent, "recuse": recuse}[mbucket].append(mname)

            votes.append({
                "motion_no": motion_no,
                "motion": desc[:600],
                "body": body,
                "motion_type": mtype,
                "result": parsed["result"],
                "mover": mover,
                "seconder": seconder,
                "aye": aye,
                "nay": nay,
                "abstain": abstain,
                "absent": absent,
                "recuse": recuse,
                "names_recorded": parsed["names_recorded"],
                "mayor_tiebreak": mayor_tiebreak,
                "mayor": mayor_name,
                # printed tally from the minutes' own result sentence ("4 in favor,
                # 1 opposed" / "carried: 4 - 0" / "passed 4:3"), kept so validation
                # can cross-check it against the named counts independently.
                "printed_tally": list(parsed["printed"]) if parsed["printed"] else None,
            })
    return votes


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def load_index():
    with open(MINUTES_INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def body_for_slug(slug):
    if "building-authority" in (slug or ""):
        return "MBA"
    return "Council"


def json_path_for(row):
    rel = row["path"].replace("meeting_minutes/minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-extract even if JSON exists")
    args = ap.parse_args()

    rows = load_index()
    unparsed = []

    for row in rows:
        md_path = os.path.join(REPO, row["path"])
        if not os.path.exists(md_path):
            unparsed.append(row["path"] + " (missing file)")
            continue
        out_json = json_path_for(row)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        if os.path.exists(out_json) and not args.force:
            continue
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
        default_body = body_for_slug(row.get("slug", ""))
        try:
            votes = parse_meeting(text, default_body)
        except Exception as e:  # noqa
            unparsed.append(f"{row['path']} (parse error: {e})")
            continue
        meeting_obj = {
            "date": row["date"],
            "title": row["title"],
            "slug": row.get("slug", ""),
            "default_body": default_body,
            "source": row["path"],
            "format": row.get("format", "text"),
            "votes": votes,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting_obj, f, indent=1, ensure_ascii=False)

    rebuild_csv()
    stats = recompute_stats()
    print(json.dumps({
        "meetings_with_json": stats["meetings"],
        "motions_extracted": stats["motions"],
        "member_vote_rows": stats["member_rows"],
        "named_rollcall_motions": stats["named"],
        "tally_only_motions": stats["tally_only"],
        "contested_motions": stats["contested"],
        "mayor_vote_rows": stats["mayor_rows"],
        "body_counts": stats["body_counts"],
        "unparsed_meetings": unparsed,
    }, indent=2))


def iter_jsons():
    for dirpath, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dirpath, fn)


MAYOR_NAMES = set(MAYORS.values())


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
                r = dict(base); r["member"] = ""; r["vote"] = ""
                rows_out.append(r)
    rows_out.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows_out:
            w.writerow({c: r.get(c, "") for c in cols})


def recompute_stats():
    meetings = motions = member_rows = named = tally_only = contested = mayor_rows = 0
    body_counts = {"Council": 0, "RDA": 0, "MBA": 0}
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        for v in mtg["votes"]:
            motions += 1
            body_counts[v.get("body", "Council")] = body_counts.get(
                v.get("body", "Council"), 0) + 1
            if v.get("names_recorded"):
                named += 1
            else:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                for m in v[k]:
                    member_rows += 1
                    if m in MAYOR_NAMES:
                        mayor_rows += 1
    return {"meetings": meetings, "motions": motions, "member_rows": member_rows,
            "named": named, "tally_only": tally_only, "contested": contested,
            "mayor_rows": mayor_rows, "body_counts": body_counts}


if __name__ == "__main__":
    main()
