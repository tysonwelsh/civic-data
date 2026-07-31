#!/usr/bin/env python3
"""
Extract recorded council votes from West Jordan meeting-minutes markdown.

For each meeting it captures one JSON under votes/<year>/<week>/<date>_<slug>.json
and rebuilds all_votes.csv (long format, one row per member-vote).

Vote formats handled (verified against the corpus):
  1. Named "The vote was recorded as follows" + YES:/NO:/ABSENT:/ABSTAIN:/RECUSED:
     comma lists (also lowercase Yes:/No:/Abstained:/Absent:). Names may wrap onto
     the next indented line. Names may also appear on the LINE BELOW the label
     (docx-text collapsed file). ~142 files.
  2. Tabular roll-call: "A roll call vote was taken" then rows "<Member>  Yes|No|absent|Abstain".
  3. Narrative unanimous: "All voted in favor ... unanimously" / "passed by unanimous
     vote (7-0)" with NO per-member names -> names_recorded:false, empty member lists.
  4. "failed for lack of (a) second" -> recorded motion, no vote, names_recorded:false.

NEVER invents who voted which way. Tally-only votes leave member lists empty.

Run:  python3 extract_votes.py            (resumable; skips existing JSONs)
      python3 extract_votes.py --force    (re-extract all)
"""
import csv
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))          # meeting_minutes/
REPO = os.path.dirname(ROOT)                               # repo root
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")

# ---- Council roster: 4 district + 3 at-large = 7 voting. Mayor Burton EXCLUDED. ----
# Canonical surname -> full name. Built from attendance + election winners.
NAME_CANON = {
    "mcconnehey": "Chris McConnehey",
    "green": "Kelvin Green",
    "jacob": "Zach Jacob",
    "lamb": "Chad Lamb",
    "pack": "David Pack",
    "whitelock": "Kayleen Whitelock",
    "worthen": "Melissa Worthen",
    "bloom": "Pamela Bloom",
    "bedore": "Bob Bedore",
    "shelton": "Kent Shelton",
    "bennett": "Rob Bennett",          # Robert "Rob" Bennett, appointed 2023 (Dist 2); confirmed in minutes + 2025 ballot
    "harris": "Annette Harris",        # elected 2025
    "wignall": "Jessica Wignall",      # elected 2025
}
# Non-voting / excluded names that may appear in YES lists by error — Mayor never votes.
EXCLUDE = {"burton", "dirk burton", "dirk"}

# Tokens that are titles, not part of a name.
TITLE_RE = re.compile(
    r"^(council\s*member|councilmember|board\s*member|boardmember|"
    r"agency\s*member|agencymember|council\s*chair|board\s*chair|agency\s*chair|"
    r"acting\s*chair|vice[\s-]*chairperson|chairperson|chair|vice[\s-]*chair|"
    r"mayor|council|board|agency)\b",
    re.I,
)


_FIRST_TO_FULL = {}
for _sur, _full in NAME_CANON.items():
    _FIRST_TO_FULL.setdefault(_full.split()[0].lower(), _full)


def norm_name(raw):
    """Return canonical full name for a member, or None if not a known member."""
    if not raw:
        return None
    s = unicodedata.normalize("NFKD", raw)
    s = s.replace("&", " ").strip().strip(".,;:")
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    low = s.lower()
    if low in EXCLUDE:
        return None
    # strip leading title words
    s2 = TITLE_RE.sub("", s).strip().strip(".,;:")
    s2 = re.sub(r"\s+", " ", s2)
    low2 = s2.lower()
    if low2 in EXCLUDE or not s2:
        return None
    # match by surname token against canon. Full-name gate: reject a surname fold
    # only when the preceding first name belongs to a DIFFERENT known member (a real
    # shared-surname collision), never for a nickname/OCR variant. No-op today
    # (surnames unique); future-proofs against a second same-surname member.
    tokens = [t.strip(".,;:") for t in low2.split()]
    for i in range(len(tokens) - 1, -1, -1):
        tok = tokens[i]
        if tok in NAME_CANON:
            cand = NAME_CANON[tok]
            if i > 0:
                pfx = tokens[i - 1].strip(".")
                cf = cand.split()[0].lower()
                other = _FIRST_TO_FULL.get(pfx)
                if (pfx.isalpha() and len(pfx) > 1 and pfx != cf and not cf.startswith(pfx)
                        and other is not None and other != cand):
                    return None
            return cand
    # full-name fuzzy: check each surname appears
    for sur, full in NAME_CANON.items():
        if re.search(r"\b" + re.escape(sur) + r"\b", low2):
            return full
    return None


def clean_ws(text):
    return re.sub(r"[ \t]+", " ", text)


def body_for_meeting(slug, title):
    """Tag the governing body from a meeting's slug/title.

    West Jordan holds SEPARATE Redevelopment Agency (RDA) and Municipal Building
    Authority (MBA) meetings — the council adjourns/recesses and reconvenes as the
    agency board (same 7 members, no Mayor). In-council references to the RDA are
    only narrative recess motions (the actual agency votes live in the separate
    RDA/MBA minutes), so council/COTW meetings are always body=Council. West Jordan
    uses "Redevelopment Agency" (RDA), never the CRA/CDRA name; there is no LBA.
    """
    s = f"{slug} {title}".lower()
    if "redevelopment" in s:
        return "RDA"
    if "municipal building authority" in s:
        return "MBA"
    if "community reinvestment" in s:
        return "CRA"
    if "community development" in s and "renewal" in s:
        return "CDRA"
    return "Council"


# first names of known members -> used to detect a name-list wrap that broke
# between a member's first and last name (e.g. blob ends "... Kayleen").
_FIRST_NAMES = {full.split()[0].lower() for full in NAME_CANON.values()}


def blob_last_token_is_firstname(blob):
    toks = re.findall(r"[A-Za-z'\-]+", blob)
    if not toks:
        return False
    return toks[-1].lower() in _FIRST_NAMES


def parse_name_list(blob):
    """Parse a comma/space separated member list -> list of canonical names."""
    blob = blob.replace("\n", " ")
    blob = clean_ws(blob).strip().strip(".,;:")
    if not blob:
        return []
    # split on commas; some lists also use ' and '
    parts = re.split(r",| and ", blob)
    out = []
    for p in parts:
        n = norm_name(p)
        if n and n not in out:
            out.append(n)
    return out


RESULT_RE = re.compile(
    r"\bmotion\s+(?P<word>pass(?:ed|es|e)?|fail(?:ed|s|e)?|carries|carried|"
    r"was approved|approved|den(?:ied|y)|tie[sd]?)\b[^0-9\n]{0,40}?"
    r"(?P<a>\d+)\s*-\s*(?P<b>\d+)",
    re.I,
)
TALLY_ONLY_RE = re.compile(r"\((?P<a>\d+)\s*-\s*(?P<b>\d+)\)")
UNAN_RE = re.compile(
    r"unanimous(?:ly)?|all\s+voted\s+in\s+favor|all\s+in\s+favor", re.I
)


def parse_result(text):
    """Extract a verbatim tally+outcome from a block of minutes text after a motion."""
    m = RESULT_RE.search(text)
    if m:
        a, b = int(m.group("a")), int(m.group("b"))
        word = m.group("word").lower()
        if "fail" in word or "den" in word or word.startswith("tie"):
            # a tied vote does not carry the motion ("The motion tied 3-3",
            # 2023-12-20 — a second adjourn motion was then made and passed)
            outcome = "Fail"
        else:
            outcome = "Pass"
        return f"{a}-{b} {outcome}", a, b
    # bare "passed 7-0" / "(7-0)"
    m = re.search(r"\b(pass(?:ed|es)?|fail(?:ed|s)?)\b[^0-9\n]{0,30}?(\d+)\s*-\s*(\d+)", text, re.I)
    if m:
        a, b = int(m.group(2)), int(m.group(3))
        outcome = "Fail" if "fail" in m.group(1).lower() else "Pass"
        return f"{a}-{b} {outcome}", a, b
    if UNAN_RE.search(text):
        m2 = TALLY_ONLY_RE.search(text)
        if m2:
            a, b = int(m2.group("a")), int(m2.group("b"))
            return f"{a}-{b} Pass (unanimous)", a, b
        return "unanimous", None, None
    return None, None, None


# ---- motion_type taxonomy (fixed 12) ----
def classify(motion_text):
    t = motion_text.lower()
    if re.search(r"\black of (?:a )?second\b", t):
        pass  # still classify by content below
    if re.search(r"\bordinance\b", t):
        # ordinances are often zoning/land-use; check for that signal
        if re.search(r"\brezone|zoning|general plan|land use|annex|subdivision|plat|"
                     r"variance|conditional use|development (agreement|plan)|"
                     r"\bpc\b|planned community", t):
            return "Land-Use/Zoning"
        return "Ordinance"
    if re.search(r"\brezone|zoning|general plan land use|land use map|annex|"
                 r"subdivision|preliminary plat|final plat|\bplat\b|variance|"
                 r"conditional use|development (agreement|plan)|planned community", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend the budget|amend.*budget|budget adjust", t):
        return "Budget Amendment"
    if re.search(r"\bgrant\b|funding application|cdbg|award.*grant|accept.*grant", t):
        return "Grant-Funding"
    if re.search(r"interlocal|inter-local|cooperative agreement", t):
        return "Interlocal"
    if re.search(r"\bappoint|appointment|reappoint|to serve on|to sit on|board member", t):
        return "Appointment"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"contract|purchase|agreement for|award.*bid|professional services|"
                 r"task order|change order|procurement|amend.*agreement", t):
        return "Contract/Purchase"
    if re.search(r"public hearing|open.*hearing|close.*hearing|continue.*hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recogniz|honor|in memoriam|small business saturday|"
                 r"\bday\b.*recogniz", t):
        return "Ceremonial"
    if re.search(r"adjourn|recess|consent agenda|approve.*minutes|reconvene|convene|"
                 r"closed session|go into|suspend the rules|agenda|table|postpone|"
                 r"continue|excuse|ratif|set.*public hearing|schedule", t):
        return "Procedural/Administrative"
    return "Other"


MOTION_HDR_RE = re.compile(r"^[ \t]*MOTION\s*:[ \t]*", re.I | re.M)
# "made a motion" with an optional qualifier — the minutes also say "made a
# SECOND motion" (2023-12-20 double adjourn) and "made a substitute motion";
# without the qualifier the second motion never anchors and its result bleeds
# into the previous motion's block (the 2023-12-20 roll/result mis-pairing).
MADE_MOTION = r"made\s+a(?:nother)?\s+(?:\w+\s+)?motion"
# narrative motion anchor: "<Name> moved to ..." / "made a (second) motion"
NARR_MOTION_RE = re.compile(r"\b(?:moved to|" + MADE_MOTION + r")\b", re.I)
VOTE_FOLLOWS_RE = re.compile(r"vote was recorded as follows", re.I)
ROLLCALL_RE = re.compile(r"roll call vote was taken", re.I)
LABEL_RE = re.compile(
    r"^[ \t]*(YES|NO|ABSENT|ABSTAIN(?:ED)?|RECUSED?|AYE|NAY)\s*:[ \t]*(.*)$",
    re.I | re.M,
)
# tabular roll-call row: "<name words>   Yes|No|Absent|Abstain"
# The vote token is anchored to END OF LINE (the roll-call column), which lets us
# accept a single space separator — pdftotext sometimes collapses the column gap
# to one space (e.g. "Councilmember Whitelock Yes"), which a {2,}-space rule drops.
# Requiring a title prefix (Councilmember/Council Member/Chair/Vice Chair/Mayor)
# keeps narrative sentences ending in "... No." from matching.
TAB_ROW_RE = re.compile(
    r"^[ \t]*((?:Council\s*member|Councilmember|"
    r"Board\s+Member|Boardmember|Agency\s+Member|Agencymember|"
    r"Board\s+Vice\s+Chair(?:person)?|Board\s+Chair(?:person)?|Agency\s+Chair(?:person)?|"
    r"Vice\s+Chairperson|Chairperson|"
    r"Council\s+Vice\s+Chair|Council\s+Chair|Acting\s+Chair|Vice\s*Chair|Chair|"
    r"Mayor(?:\s+Pro\s+Tem)?)[ \t]+"
    r"[A-Z][A-Za-z'\-]+(?:[ \t]+[A-Z][A-Za-z'\-]+){0,2})[ \t]+"
    r"(Yes|No|Absent|Abstain(?:ed)?|Aye|Nay|Recused?)[ \t]*$",
    re.I | re.M,
)


def extract_mover_seconder(block):
    """From a MOTION block, get mover and seconder canonical names."""
    mover = seconder = None
    mm = re.search(
        r"(?:^|\n)\s*(?:MOTION:\s*)?(.{0,80}?)\b(?:moved|" + MADE_MOTION + r")\b",
        block, re.S | re.I,
    )
    if mm:
        mover = norm_name(mm.group(1).split("\n")[-1])
    ms = re.search(r"([A-Za-z .'\-]{0,60}?)\bseconded\b", block)
    if ms:
        seconder = norm_name(ms.group(1).split("\n")[-1].split(".")[-1])
    return mover, seconder


def get_motion_text(block):
    """Extract a concise motion description from a MOTION block."""
    # take text after 'moved to' / 'made a motion to' up to 'seconded' or end
    m = re.search(r"\b(?:moved|" + MADE_MOTION + r")\b\s*(.*?)(?:\.\s*\n|\bseconded\b)",
                  block, re.S | re.I)
    if m:
        txt = clean_ws(m.group(1).replace("\n", " ")).strip()
    else:
        # fallback: first ~200 chars after MOTION:
        txt = clean_ws(block.replace("\n", " ")).strip()
        txt = re.sub(r"^\s*MOTION:\s*", "", txt, flags=re.I)
    txt = txt.strip().strip(".,;: ")
    if len(txt) > 400:
        txt = txt[:400].rsplit(" ", 1)[0] + "…"
    return txt


def parse_named_block(seg):
    """Parse a YES/NO/ABSENT/... labeled block. Returns dict of vote->names, or None."""
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    found = False
    lines = seg.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^[ \t]*(YES|NO|ABSENT|ABSTAIN(?:ED)?|RECUSED?|AYE|NAY)\s*:[ \t]*(.*)$",
                     lines[i], re.I)
        if m:
            found = True
            label = m.group(1).upper()
            rest = m.group(2)
            # gather continuation lines (indented, not a new label, not a result line)
            blob = rest
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if re.match(r"^[ \t]*(YES|NO|ABSENT|ABSTAIN(?:ED)?|RECUSED?|AYE|NAY)\s*:",
                            nxt, re.I):
                    break
                if re.search(r"\bmotion\b.*\b(pass|fail|carr|den)", nxt, re.I):
                    break
                stripped = nxt.strip()
                if not stripped:
                    # blank line. Normally a blank ends the label's list, BUT a
                    # page-break wrap leaves the list dangling (trailing comma or a
                    # bare first name like "...Kayleen") with the continuation a few
                    # blank lines below (the running header was stripped out). When
                    # the blob clearly dangles mid-list, skip the blank and keep
                    # scanning so the trailing names ("Whitelock, Jessica Wignall")
                    # are absorbed. Cap the look-ahead so we never run forever.
                    dangling = bool(
                        blob.rstrip().endswith(",")
                        or (parse_name_list(blob) and blob_last_token_is_firstname(blob))
                    )
                    if blob.strip() and not dangling:
                        break
                    if dangling and (j - i) > 6:
                        break
                    j += 1
                    continue
                # names continuation (indented OR the docx case: names on line below label).
                # Also catch an UNINDENTED wrap: a comma-list that overran the page
                # width drops to column 0 (e.g. "...David Pack, Kayleen" \n
                # "Whitelock, Melissa Worthen"). Absorb such a line when the running
                # blob ended mid-list (trailing comma or a dangling first-name) AND
                # the next line is a short proper-noun/comma list of known members.
                looks_like_namelist = bool(
                    re.fullmatch(r"[A-Z][A-Za-z'.\-]+(?:[ ,]+[A-Z][A-Za-z'.\-]+)*[ ,]*",
                                 stripped)
                    and len(stripped) <= 80
                    and parse_name_list(stripped)
                )
                blob_dangling = bool(
                    blob.rstrip().endswith(",")
                    or (parse_name_list(blob) and blob_last_token_is_firstname(blob))
                )
                if re.match(r"^[ \t]+", nxt) or (not blob.strip()):
                    blob += " " + stripped
                    j += 1
                elif looks_like_namelist and blob_dangling:
                    blob += " " + stripped
                    j += 1
                else:
                    break
            names = parse_name_list(blob)
            key = {"YES": "aye", "AYE": "aye", "NO": "nay", "NAY": "nay",
                   "ABSENT": "absent", "ABSTAIN": "abstain", "ABSTAINED": "abstain",
                   "RECUSE": "recuse", "RECUSED": "recuse"}[label]
            for n in names:
                if n not in res[key]:
                    res[key].append(n)
            i = j
        else:
            i += 1
    return res if found else None


def parse_tabular(seg):
    """Parse a tabular roll-call block. Returns vote->names dict or None."""
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    found = False
    for m in TAB_ROW_RE.finditer(seg):
        name = norm_name(m.group(1))
        if not name:
            continue
        v = m.group(2).lower()
        if v.startswith("yes") or v.startswith("aye"):
            key = "aye"
        elif v.startswith("no") or v.startswith("nay"):
            key = "nay"
        elif v.startswith("abstain"):
            key = "abstain"
        elif v.startswith("recus"):
            key = "recuse"
        elif v.startswith("absent"):
            key = "absent"
        else:
            continue
        found = True
        if name not in res[key]:
            res[key].append(name)
    return res if found else None


def split_motions(text):
    """Yield each motion block.

    Anchors are EITHER a 'MOTION:' / 'Motion:' header OR a narrative
    '<Name> moved to ...' / 'made a motion' occurrence. Narrative anchors that
    fall inside an already-claimed header block are ignored so the same motion is
    not double-counted. A block runs from one anchor to the next.
    """
    anchors = [m.start() for m in MOTION_HDR_RE.finditer(text)]
    hdr_set = set(anchors)
    # add narrative anchors; we want the start of the sentence (the name), so
    # back up to the previous sentence boundary / line start.
    for m in NARR_MOTION_RE.finditer(text):
        # find start of this motion sentence
        seg_start = text.rfind("\n", 0, m.start())
        prev_period = text.rfind(". ", 0, m.start())
        start = max(seg_start, prev_period)
        start = start + 1 if start >= 0 else 0
        # skip if this narrative anchor is the 'moved to' that belongs to a
        # 'MOTION:' header block. A header introduces the same motion, so any
        # narrative anchor whose backed-up start sits at/after a header and
        # before that header's block end is a duplicate. Use a generous window:
        # if ANY header lies within 600 chars before this 'moved', it's covered.
        covered = False
        for h in hdr_set:
            if -5 <= m.start() - h <= 600:
                covered = True
                break
        if not covered:
            anchors.append(start)
    anchors = sorted(set(anchors))
    for k, start in enumerate(anchors):
        end = anchors[k + 1] if k + 1 < len(anchors) else len(text)
        # cap block length so a narrative motion doesn't swallow huge discussion —
        # but NEVER truncate mid-roll: when a vote lead-in starts before the cap,
        # extend far enough to keep its whole roll block (T3.1(m) 2026-07-12:
        # 2022-06-22 Res 22-027 lost 6 of 7 named votes, incl. Green's Nay, to the
        # hard cap after ~30 lines of discussion).
        cap = start + 2500
        if end > cap:
            vm = (VOTE_FOLLOWS_RE.search(text, start, cap)
                  or ROLLCALL_RE.search(text, start, cap))
            if vm:
                cap = max(cap, min(end, vm.end() + 700))
        yield text[start:min(end, cap)]


_DASHES = dict.fromkeys(
    [0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0xFE58, 0xFE63, 0xFF0D],
    ord("-"),
)


def normalize_dashes(text):
    return text.translate(_DASHES)


# pdftotext page-break artifacts that split roll-call name lists across pages.
# A "Page N" footer, a running header ("City Council ... Minutes ... <date>"),
# and the surrounding blank lines are inserted mid-roster, dropping the names
# that fall after the break. Remove these artifact lines so a vote block's names
# are contiguous before parsing.
PAGE_NUM_RE = re.compile(r"^[ \t]*Page\s+\d+(?:\s+of\s+\d+)?[ \t]*$", re.I)
RUNNING_HDR_RE = re.compile(
    r"^[ \t]*City Council\b.*\bMinutes\b.*$"
    r"|^[ \t]*City Council\b.*\bWork Session\b.*$"
    # separate RDA/MBA meetings carry their own running-header/footer lines that
    # split roll-call rosters the same way (e.g. "Redevelopment Agency Minutes …
    # Tuesday, May 12, 2026   Page 1"). Strip them so the YES: list stays contiguous.
    r"|^[ \t]*(?:Redevelopment Agency|Municipal Building Authority|"
    r"Community Reinvestment Agency|Community Development(?: & | and )Renewal Agency)\b.*$"
    r"|^[ \t]*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b.*$"
    r"|^[ \t]*(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4}[ \t]*$",
    re.I,
)


def strip_page_artifacts(text):
    """Drop pdftotext page-header/footer lines so roll-call rosters stay contiguous.

    Only removes lines that match a known page artifact pattern; never touches
    lines that carry vote labels, member rows, or motion text.
    """
    # Form-feed (\x0c) marks a pdftotext page break and is often glued to the
    # start of the first line of the next page (e.g. "\x0cABSENT: Chad Lamb"),
    # which defeats line-start anchors and misfiles that line. Turn each form-feed
    # into a newline so the following label/row parses cleanly.
    text = text.replace("\x0c", "\n")
    out = []
    for ln in text.split("\n"):
        if PAGE_NUM_RE.match(ln):
            continue
        if RUNNING_HDR_RE.match(ln) and not re.search(
            r"\b(Yes|No|Absent|Abstain|Aye|Nay|Recus)\b", ln, re.I
        ):
            continue
        out.append(ln)
    return "\n".join(out)


def extract_meeting(path, rel_source):
    raw = open(path, encoding="utf-8", errors="replace").read()
    raw = normalize_dashes(raw)
    raw = strip_page_artifacts(raw)
    votes = []
    motion_no = 0
    for block in split_motions(raw):
        motion_no_candidate = motion_no + 1
        motion_text = get_motion_text(block)
        if not motion_text:
            continue
        mover, seconder = extract_mover_seconder(block)
        result, a, b = parse_result(block)
        names_recorded = False
        vlists = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}

        # find vote block within this motion block
        if VOTE_FOLLOWS_RE.search(block):
            seg = block[VOTE_FOLLOWS_RE.search(block).start():]
            # Named YES:/NO: comma lists are the dominant 2022-2026 form, but the
            # 2021 minutes put one member per line in TABULAR form under the same
            # "vote was recorded as follows" lead-in. Try named first; if it yields
            # nothing, fall back to the tabular parser so 2021 is captured.
            parsed = parse_named_block(seg)
            if not (parsed and any(parsed.values())):
                parsed = parse_tabular(seg)
            if parsed and any(parsed.values()):
                vlists = parsed
                names_recorded = True
        elif ROLLCALL_RE.search(block):
            seg = block[ROLLCALL_RE.search(block).start():]
            parsed = parse_tabular(seg)
            if not (parsed and any(parsed.values())):
                parsed = parse_named_block(seg)
            if parsed and any(parsed.values()):
                vlists = parsed
                names_recorded = True
        else:
            # maybe a named block without the 'vote was recorded' lead-in
            parsed = parse_named_block(block)
            if not (parsed and any(parsed.values())):
                parsed = parse_tabular(block)
            if parsed and any(parsed.values()):
                vlists = parsed
                names_recorded = True

        # lack-of-second -> recorded motion, no vote
        lack = re.search(r"failed for lack of (?:a )?second|lack of (?:a )?second",
                         block, re.I)
        if lack and not result:
            result = "Failed (no second)"

        # Only record if there's a real motion outcome OR member votes
        if not result and not names_recorded:
            # no detectable vote outcome -> skip (likely a "moved" inside narrative)
            # but keep if it clearly is a motion w/ second
            if not re.search(r"\bseconded\b", block, re.I):
                continue
            result = result or "Recorded (no tally)"

        motion_no = motion_no_candidate
        v = {
            "motion_no": motion_no,
            "motion": motion_text,
            "motion_type": classify(motion_text),
            "result": result or "",
            "mover": mover or "",
            "seconder": seconder or "",
            "aye": vlists["aye"],
            "nay": vlists["nay"],
            "abstain": vlists["abstain"],
            "absent": vlists["absent"],
            "recuse": vlists["recuse"],
            "names_recorded": names_recorded,
        }
        votes.append(v)
    return votes


def load_index():
    rows = []
    with open(INDEX, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


VALIDATION_REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
TALLY_IN_RESULT_RE = re.compile(r"(\d+)\s*-\s*(\d+)")

# Known SOURCE typos in the minutes' result strings (the tally as printed in the
# minutes disagrees with the named roll call). These are clerical errors in the
# original document, NOT parse bugs — they stay flagged, never "fixed".
KNOWN_SOURCE_TYPOS = {
    ("2021-03-10", 4): "minutes print '7-0' but the named roll call is Jacob=No + "
                       "6 Yes (a 6-1); the printed tally is a clerical error.",
    ("2021-09-22", 1): "named roll call is 3 Yes / 2 No / 2 Abstain; minutes print "
                       "'failed 4-3' (abstentions counted into the tally in the source).",
    ("2023-03-08", 8): "source lists 'Green' in BOTH the Yes list and as the No vote "
                       "(Kelvin Green); the printed '6-1' is right, the Yes list double-"
                       "counts Green — a source typo, captured verbatim.",
    # ("2023-12-20", 7) removed 2026-07-02 (Phase 3.5): the double-adjourn
    # mis-pairing was an extractor gap, now fixed — "made a SECOND motion"
    # anchors its own block and "The motion tied 3-3" parses as 3-3 Fail.
    ("2024-03-27", 4): "named roll call is Green=Yes (1) vs 6 No → a 1-6 fail; minutes "
                       "print 'failed 6-1' (transposed digits) — a source typo.",
    ("2025-01-28", 1): "RDA consent-agenda motion: the minutes' named roll call lists all "
                       "6 present members under NO: (with empty YES:) yet print 'passed "
                       "6-0' — the YES/NO labels are swapped in the source. Captured "
                       "verbatim (all 6 as Nay); the printed tally is the clerical error.",
}


def write_validation_report(all_meetings):
    """Per-motion tally-vs-result consistency check.

    For every motion where member names were recorded, compare the named vote
    counts (aye+nay+abstain+recuse, and separately absent) against the tally
    printed in `result`. Classify each mismatch as a likely PARSE issue (fewer
    names captured than the tally implies) or a likely SOURCE typo (the minutes'
    printed tally itself is internally inconsistent). Never alters votes.
    """
    lines = []
    total_motions = 0
    named_motions = 0
    consistent = 0
    mismatches = []  # (date, motion_no, kind, detail)

    for date, source, votes in sorted(all_meetings):
        for v in votes:
            total_motions += 1
            if not v.get("names_recorded"):
                continue
            named_motions += 1
            aye, nay = len(v["aye"]), len(v["nay"])
            abst, rec = len(v["abstain"]), len(v["recuse"])
            absent = len(v["absent"])
            cast = aye + nay + abst + rec  # members who actually voted

            m = TALLY_IN_RESULT_RE.search(v["result"] or "")
            if not m:
                # named votes but no numeric tally to check against
                continue
            ta, tb = int(m.group(1)), int(m.group(2))
            tally_total = ta + tb

            # result tally counts only Aye/Nay (abstain/recuse/absent are noted
            # separately in the narrative). Compare the "for/against" portion.
            for_against = aye + nay
            ok_pair = (aye == ta and nay == tb)
            # A full 7-member council: cast+absent should be <= 7.
            roster_ok = (cast + absent) <= 7

            if ok_pair and roster_ok:
                consistent += 1
                continue

            # classify
            note = KNOWN_SOURCE_TYPOS.get((date, v["motion_no"]))
            if note:
                kind = "SOURCE-TYPO (verified — left as printed, names captured correctly)"
            elif for_against < tally_total:
                # fewer named for/against than the printed tally -> names dropped
                kind = "PARSE? (named for/against < printed tally)"
            elif for_against > tally_total:
                kind = "PARSE? (named for/against > printed tally)"
            elif not roster_ok:
                kind = "PARSE? (named members exceed 7-seat roster)"
            else:
                kind = "SOURCE-TYPO? (named split differs from printed tally)"
            detail = (f"result='{v['result']}' aye={aye} nay={nay} "
                      f"abstain={abst} recuse={rec} absent={absent} "
                      f"| motion: {v['motion'][:70]}")
            if note:
                detail += f"\n    VERIFIED: {note}"
            mismatches.append((date, v["motion_no"], kind, detail, source))

    lines.append("VOTE EXTRACTION — TALLY-vs-RESULT VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append(f"meetings checked        : {len(all_meetings)}")
    lines.append(f"motions total           : {total_motions}")
    lines.append(f"named roll-call motions : {named_motions}")
    verified_typos = sum(1 for m in mismatches if m[2].startswith("SOURCE-TYPO ("))
    lines.append(f"consistent (aye/nay==tally & roster<=7): {consistent}")
    lines.append(f"mismatches flagged      : {len(mismatches)}")
    lines.append(f"  of which verified source typos (not parse bugs): {verified_typos}")
    lines.append(f"  unexplained / to review : {len(mismatches) - verified_typos}")
    lines.append("")
    lines.append("A 'consistent' motion = the recorded Aye count == result's first")
    lines.append("number, Nay count == second number, and named members fit the")
    lines.append("7-seat council. Tally-only/unanimous motions (no per-member names)")
    lines.append("are not checked. PARSE? = likely an extractor coverage gap;")
    lines.append("SOURCE-TYPO? = the minutes' own printed tally is inconsistent with")
    lines.append("its named roll call (a clerical error in the source — left as-is,")
    lines.append("never 'corrected', and never invented).")
    lines.append("")
    lines.append("FLAGGED MOTIONS")
    lines.append("-" * 70)
    if not mismatches:
        lines.append("(none — every named roll-call motion is internally consistent)")
    for date, mno, kind, detail, source in mismatches:
        lines.append(f"[{date}] motion #{mno}  {kind}")
        lines.append(f"    {detail}")
        lines.append(f"    src: {source}")
    lines.append("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(VALIDATION_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(mismatches)


def main():
    force = "--force" in sys.argv
    rows = load_index()
    all_rows = []  # for all_votes.csv
    processed = 0
    motions_total = 0
    member_rows = 0
    named_motions = 0
    tally_only = 0
    contested = 0
    by_body = {}           # body -> motion count
    contested_by_body = {}  # body -> contested motion count
    unparsed = []
    all_meetings = []  # (date, source, votes) for the validation report

    for r in rows:
        relpath = r["path"]
        date = r["date"]
        year = r["year"]
        title = r["title"]
        slug = r["slug"]
        abspath = os.path.join(REPO, relpath)
        if not os.path.exists(abspath):
            unparsed.append(relpath + " (missing)")
            continue
        # week folder = parent dir name
        week = os.path.basename(os.path.dirname(relpath))
        out_dir = os.path.join(VOTES_DIR, year, week)
        out_path = os.path.join(out_dir, f"{date}_{slug}.json")

        body = body_for_meeting(slug, title)
        if os.path.exists(out_path) and not force:
            data = json.load(open(out_path, encoding="utf-8"))
            # backfill body on JSONs written before the body column existed
            if data.get("body") != body:
                data["body"] = body
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=1)
        else:
            votes = extract_meeting(abspath, relpath)
            data = {"date": date, "title": title, "body": body,
                    "source": relpath, "votes": votes}
            os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)

        processed += 1
        all_meetings.append((data["date"], data["source"], data["votes"]))
        if not data["votes"]:
            unparsed.append(relpath + " (no votes found)")
        mbody = data.get("body", "Council")
        for v in data["votes"]:
            motions_total += 1
            by_body[mbody] = by_body.get(mbody, 0) + 1
            if v["names_recorded"]:
                named_motions += 1
            else:
                tally_only += 1
            is_contested = False
            if v["nay"] or v["abstain"]:
                is_contested = True
            elif re.search(r"\b\d+-\d+\s+Fail|\bFail\b", v["result"]) and "no second" not in v["result"]:
                is_contested = True
            if is_contested:
                contested += 1
                contested_by_body[mbody] = contested_by_body.get(mbody, 0) + 1
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v[key]:
                    member_rows += 1
                    all_rows.append({
                        "date": data["date"], "year": year, "title": data["title"],
                        "body": data.get("body", "Council"),
                        "motion_no": v["motion_no"], "motion": v["motion"],
                        "motion_type": v["motion_type"], "result": v["result"],
                        "mover": v["mover"], "seconder": v["seconder"],
                        "member": member, "vote": vote, "source": data["source"],
                    })

    # rebuild all_votes.csv
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"])
        w.writeheader()
        for row in sorted(all_rows, key=lambda x: (x["date"], x["motion_no"])):
            w.writerow(row)

    validation_mismatches = write_validation_report(all_meetings)

    stats = {
        "meetings_processed": processed,
        "motions_extracted": motions_total,
        "member_vote_rows": member_rows,
        "named_rollcall_motions": named_motions,
        "tally_only_motions": tally_only,
        "contested_motions": contested,
        "motions_by_body": by_body,
        "contested_by_body": contested_by_body,
        "validation_mismatches": validation_mismatches,
        "unparsed_meetings": unparsed,
    }
    print(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    main()
