#!/usr/bin/env python3
"""
extract_votes.py — Lehi PLANNING COMMISSION vote extraction.

Adapted from meeting_minutes/extract_votes.py (the council extractor). Reads the 160
Planning Commission minutes markdown files indexed in planning_commission/minutes_index.csv,
parses each recorded Motion + roll-call Vote, emits one JSON per meeting to
planning_commission/votes/<year>/<week>/<date>_planning-commission-meeting.json, then
rebuilds planning_commission/all_votes.csv (long format, one row per member-vote).

KEY DIFFERENCES FROM THE COUNCIL EXTRACTOR
------------------------------------------
1. APPOINTED BODY / DYNAMIC ROSTER. The PC has no fixed elected roster — commissioners
   rotate over 2020-2026. The roster is reconstructed FROM the "Members Present:" headers
   in the minutes themselves (build_roster()). Two people share the surname "Peterson"
   (Jared 2020-2021, Greg 2020-2021); they overlap in time but NEVER appear in a roll call,
   so "Peterson" is resolved per-meeting from that meeting's present-set and skipped if
   ambiguous. There is NO mayor; the Chair/Vice-Chair vote like any member.

2. RECOMMENDATION vs FINAL ACTION. Most PC actions on plats/subdivisions/rezones/
   annexations/GPAs are RECOMMENDATIONS forwarded to City Council ("forward a positive/
   negative recommendation"). CUPs, site plans, design review, consent, nominations etc.
   are PC FINAL ACTIONS. The result string encodes this so the DB stage logic can key on it:
     recommendation -> "Positive recommendation 6:0" / "Negative recommendation 3:2"
                       (substring "recommend" present; "positive"/"negative" = direction)
     final action   -> "5:0 Approved (Final Action)" / "0:5 Denied (Final Action)"
                       (no "recommend" substring)
   Direction keys on the OPERATIVE/earliest verb in the flattened Motion line (so a downstream
   "denial"/"Conditions of Approval" does not flip an approve motion).

3. ROLL-CALL FORMAT. Per-member inline only (no YES:/NO: label blocks in the PC corpus):
     "Vote: Commissioner Nielsen, yes; Commissioner Peterson; yes; Commissioner Ellis, yes;
      ... The motion passed unanimously."
   Separators drift: comma, semicolon, a STRAY semicolon between name and yes/no
   ("Peterson; yes"), bare space ("Everett no"), or a period in 2026 ("Gehman, yes."). We
   anchor on roster surnames and tolerate any of those separators. Tally-only forms
   ("passed unanimously", "four in favor, one against", "failed 2 to 4") set
   names_recorded=false with an EMPTY member list — we never guess who voted how.

Run:  python3 planning_commission/extract_votes.py          (resumable: skips existing JSON)
      python3 planning_commission/extract_votes.py --force   (re-extract all)

See planning_commission/CLAUDE.md for the full writeup.
"""
import argparse
import csv
import json
import os
import re
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = os.path.join(REPO, "planning_commission")
MINUTES_INDEX = os.path.join(PC, "minutes_index.csv")
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES_CSV = os.path.join(PC, "all_votes.csv")
ROSTER_CSV = os.path.join(PC, "roster.csv")

TITLE = "Planning Commission"
BODY = "PlanningCommission"   # exact string the DB build keys on (all rows)

# ---------------------------------------------------------------------------
# Name normalization.
# Full-name OCR/short-form folds (variant -> canonical full name). Built from the
# corpus headers (build_roster output cross-checked). Greg vs Jared Peterson are
# DISTINCT people and are NOT folded.
# ---------------------------------------------------------------------------
NAME_FOLD = {
    "abe nielsen": "Abram Nielsen",
    "greg jackson": "Gregory Jackson",
    "kenneth roberts": "Ken Roberts",
    "lindsay gheman": "Lindsay Gehman",
    "emily briton": "Emily Britton",
}
# Surname spelling drift seen in the roll-call Vote: lines (variant -> canonical key).
SURNAME_ALIASES = {
    "newell": "newall", "newal": "newall",
    "briton": "britton",
    "carlsson": "carlson",
    "petersen": "peterson",
    "nielson": "nielsen",
    "gheman": "gehman",
}


def fold_fullname(name):
    name = " ".join(name.split()).strip(" .,;")
    # strip a stray leading role word
    name = re.sub(r"^(Commissioner|Commission|Chair|Vice)\s+", "", name)
    return NAME_FOLD.get(name.lower(), name)


def surname_key(fullname):
    last = fullname.split()[-1].lower().strip(".,;:")
    return SURNAME_ALIASES.get(last, last)


# ---------------------------------------------------------------------------
# Roster reconstruction from "Members Present:" headers.
# ---------------------------------------------------------------------------
PRESENT_HEADER_RE = re.compile(
    r"Members\s+Present\s*:(.*?)(?:Others\s+Present|Members\s+Absent|Excused|_{5,}|"
    r"Regular\s+Session|Work\s+Session|Study\s+Session)",
    re.IGNORECASE | re.DOTALL)
ABSENT_HEADER_RE = re.compile(
    r"Members\s+Absent\s*:(.*?)(?:Others\s+Present|Excused|_{5,}|Regular\s+Session|"
    r"Work\s+Session|Study\s+Session)",
    re.IGNORECASE | re.DOTALL)
# A "First Last[, Role]" entry: 2-3 capitalized tokens then an optional role.
ENTRY_RE = re.compile(
    r"([A-Z][A-Za-z’'\-]+(?:\s+[A-Z][A-Za-z’'\-\.]+){1,2}?)\s*[,;]?\s*"
    r"(Commission(?:er)?\b|Alternate\b|$)")


def parse_present_block(block):
    """Return a list of canonical full names found in a present/absent header block."""
    names = []
    # split on newlines and semicolons (some headers are inline semicolon-separated)
    for chunk in re.split(r"[\n;]", block):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = ENTRY_RE.match(chunk)
        if not m:
            continue
        nm = fold_fullname(m.group(1))
        # require a plausible 2-token person name
        if len(nm.split()) >= 2 and nm.split()[0] not in (
                "Others", "Members", "Lehi", "City", "Planning", "Regular", "Work"):
            names.append(nm)
    # de-dup preserving order
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n); out.append(n)
    return out


def meeting_present(text):
    m = PRESENT_HEADER_RE.search(text)
    return parse_present_block(m.group(1)) if m else []


def meeting_absent(text):
    m = ABSENT_HEADER_RE.search(text)
    return parse_present_block(m.group(1)) if m else []


# ---------------------------------------------------------------------------
# Motion-type classification (reuse the council 12-category taxonomy).
# ---------------------------------------------------------------------------
def classify(motion_text, item_text):
    t = (item_text + " \n " + motion_text).lower()
    landuse_kw = ["zone", "zoning", "rezone", "general plan", "overlay", "subdivision",
                  "plat", "annex", "right-of-way", "right of way", "vacat", "land use",
                  "setback", "conditional use", "development code", "preliminary",
                  "site plan", "pud", "planned unit", "concept plan", "final plan",
                  "development agreement", "area plan", "design review", "lot line",
                  "amended plat", "master plan"]
    if any(k in t for k in landuse_kw):
        return "Land-Use/Zoning"
    if ("budget amendment" in t or "amend the budget" in t or "tentative budget" in t
            or "final budget" in t or re.search(r"budget.{0,30}amend", t)):
        return "Budget Amendment"
    if "interlocal" in t or "inter-local" in t:
        return "Interlocal"
    if "grant" in t and any(k in t for k in ["apply", "accept", "award", "funding",
                                             "application", "cdbg", "fund"]):
        return "Grant-Funding"
    if "appoint" in t or "reappoint" in t or "appointing" in t:
        return "Appointment"
    if any(k in t for k in ["contract", "agreement", "purchase", "bid", "procure",
                            "professional services", "lease"]) and "interlocal" not in t:
        if "resolution" not in t and "ordinance" not in t:
            return "Contract/Purchase"
    if "ordinance" in t:
        return "Ordinance"
    if "resolution" in t:
        return "Resolution"
    if re.search(r"\b(proclamation|recognition|recognizing|honoring|ceremonial|"
                 r"presentation)\b", t):
        return "Ceremonial"
    if any(k in t for k in ["open the public hearing", "close the public hearing",
                            "continue the public hearing", "public hearing"]):
        return "Public Hearing Action"
    proc_kw = ["minutes", "consent agenda", "agenda", "continue", "table", "consent",
               "adjourn", "ratify", "set the date", "schedule", "bylaw", "by-law",
               "nominate", "nomination", "elect ", "re-elect", "chair", "vice chair",
               "rules of order", "calendar", "pulled", "recess"]
    if any(k in t for k in proc_kw):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Recommendation vs final-action + direction.
# ---------------------------------------------------------------------------
def _earliest(text, words):
    best = None
    for w in words:
        i = text.find(w)
        if i != -1 and (best is None or i < best):
            best = i
    return best


def stage_and_direction(motion_text):
    """Return (stage, direction).
    stage: 'recommendation' | 'final'
    direction: for recommendation -> 'positive'|'negative'
               for final         -> 'approve'|'deny'|None  (None = procedural)
    Keyed on the operative/earliest verb so a downstream 'denial'/'Conditions of
    Approval' does not flip an approve motion."""
    low = " ".join(motion_text.lower().split())

    is_rec = ("recommend" in low) or bool(
        re.search(r"\bforward(?:ed|ing|s)?\b.{0,90}\bcouncil\b", low)) or bool(
        re.search(r"\bsend\b.{0,40}\bcouncil\b.{0,40}recommendation", low))

    if is_rec:
        neg_idx = _earliest(low, ["negative recommendation", "unfavorable",
                                  "recommend denial", "recommend the denial",
                                  "negative", "denial", "deny"])
        pos_idx = _earliest(low, ["positive recommendation", "favorable",
                                  "recommend approval", "recommend the approval",
                                  "positive", "approval", "approve"])
        if neg_idx is not None and (pos_idx is None or neg_idx < pos_idx):
            return "recommendation", "negative"
        return "recommendation", "positive"

    # final action: operative approve vs deny verb (earliest wins)
    deny_idx = _earliest(low, ["deny", "denial", "denied", "reject", "rejection",
                               "disapprove"])
    appr_idx = _earliest(low, ["approve", "approval", "accept", "adopt", "grant"])
    if deny_idx is not None and (appr_idx is None or deny_idx < appr_idx):
        return "final", "deny"
    if appr_idx is not None:
        return "final", "approve"
    return "final", None


# ---------------------------------------------------------------------------
# Roll-call parsing.
# ---------------------------------------------------------------------------
VOTE_WORDS = {
    "yes": "aye", "aye": "aye", "yea": "aye", "approve": "aye", "favor": "aye",
    "no": "nay", "nay": "nay", "oppose": "nay", "opposed": "nay",
    "absent": "absent", "excused": "absent",
    "abstain": "abstain", "abstained": "abstain", "abstaining": "abstain",
    "recuse": "recuse", "recused": "recuse",
}
VOTE_WORD_RE = (r"(yes|aye|yea|no|nay|absent|excused|abstain|abstained|abstaining|"
                r"recuse|recused)")
RESULT_CUT_RE = re.compile(
    r"\bThe\s+motion\b|\bMotion\s+(?:passed|failed|fails|fail|carried|was|did)\b|"
    r"\b(?:passed|failed|fails)\s+unanimously\b|\bThe\s+vote\b", re.IGNORECASE)

WORD_NUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "unanimous": None}


def _num(tok):
    tok = tok.lower()
    if tok.isdigit():
        return int(tok)
    return WORD_NUM.get(tok)


def parse_rollcall(block, present_map, ambiguous_surnames):
    """Parse a flattened roll-call (or tally-only) block.

    present_map: surname_key -> canonical full name (this meeting's voters).
    ambiguous_surnames: set of surname_keys present >1 person (skip, never guess).

    Returns components; the caller builds the final result string (it needs the
    motion's stage/direction)."""
    text = " ".join(block.split())
    low = text.lower()

    buckets = {"aye": [], "nay": [], "absent": [], "abstain": [], "recuse": []}

    # result sentence region (outcome + printed tally live here, not in the names)
    cut = RESULT_CUT_RE.search(text)
    names_region = text[:cut.start()] if cut else text
    result_region = text[cut.start():] if cut else text
    rlow = result_region.lower()

    fail = bool(re.search(r"\b(fail(?:s|ed)?|defeated|denied|did not pass|"
                          r"was not approved|do(?:es)? not pass|was denied|"
                          r"was defeated|lack of a second|died for lack)\b", rlow))
    outcome = "Fail" if fail else "Pass"
    unanimous = "unanim" in rlow

    # The result sentence sometimes states the EFFECTIVE recommendation direction
    # explicitly (e.g. a 3-3 split "forwarded with a negative recommendation"); when
    # present this is authoritative (reading the source, not guessing).
    stated_dir = None
    if re.search(r"negative\s+recommendation", rlow):
        stated_dir = "negative"
    elif re.search(r"positive\s+recommendation", rlow):
        stated_dir = "positive"

    # ----- named roll call: anchor on this meeting's present surnames -----
    spelling_to_fn = {}     # spelling -> full name (skip ambiguous)
    for skey, fn in present_map.items():
        if skey in ambiguous_surnames:
            continue
        spelling_to_fn[skey] = fn
    for alias, target in SURNAME_ALIASES.items():
        if target in present_map and target not in ambiguous_surnames:
            spelling_to_fn[alias] = present_map[target]
    if spelling_to_fn:
        alts = sorted(spelling_to_fn, key=len, reverse=True)
        pat = re.compile(
            r"\b(" + "|".join(re.escape(a) for a in alts) + r")\b\s*[,;]?\s*"
            + VOTE_WORD_RE + r"\b", re.IGNORECASE)
        for m in pat.finditer(names_region):
            fn = spelling_to_fn[m.group(1).lower()]
            bucket = VOTE_WORDS.get(m.group(2).lower())
            if bucket:
                buckets[bucket].append(fn)

    # de-dup, preserve order
    def dedup(lst):
        s, o = set(), []
        for x in lst:
            if x not in s:
                s.add(x); o.append(x)
        return o
    for k in buckets:
        buckets[k] = dedup(buckets[k])

    names_recorded = any(buckets[k] for k in buckets)
    n_aye, n_nay = len(buckets["aye"]), len(buckets["nay"])

    # ----- printed tally from the result sentence -----
    printed = None
    fm = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s+in\s+favor", rlow)
    om = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s+(?:opposed|against)", rlow)
    if fm:
        a = _num(fm.group(1)); b = _num(om.group(1)) if om else 0
        if a is not None and b is not None:
            printed = (a, b)
    if printed is None:
        tm = re.search(
            r"(?:passed|carried|fail(?:s|ed)?)\s*:?\s*(\d+)\s*(?:to|[:\-–])\s*(\d+)",
            rlow)
        if tm:
            printed = (int(tm.group(1)), int(tm.group(2)))

    return {
        "buckets": buckets, "names_recorded": names_recorded, "unanimous": unanimous,
        "outcome": outcome, "n_aye": n_aye, "n_nay": n_nay, "printed": printed,
        "stated_dir": stated_dir, "vote_text": text,
    }


def build_result(parsed, stage, direction):
    """Compose the machine-detectable result string."""
    if stage == "recommendation" and parsed.get("stated_dir"):
        direction = parsed["stated_dir"]   # source's explicit disposition wins
    n_aye, n_nay = parsed["n_aye"], parsed["n_nay"]
    outcome = parsed["outcome"]
    if parsed["names_recorded"]:
        tally = f"{n_aye}:{n_nay}"
    elif parsed["printed"]:
        tally = f"{parsed['printed'][0]}:{parsed['printed'][1]}"
    elif parsed["unanimous"]:
        tally = "Unanimous"
    else:
        tally = ""

    if stage == "recommendation":
        dword = "Positive" if direction == "positive" else "Negative"
        base = f"{dword} recommendation"
        if outcome == "Fail":
            base += " FAILED"
        return (base + " " + tally).strip()

    # final action
    if direction in ("approve", "deny"):
        disp = "Approved" if direction == "approve" else "Denied"
        if outcome == "Fail":
            disp = "Failed"
        return (f"{tally} {disp} (Final Action)").strip()
    # procedural final action (nominations, minutes, table, continue, adjourn...)
    return (f"{tally} {outcome}").strip()


def parse_motion_meta(motion_text, present_map, ambiguous_surnames):
    """Extract mover + seconder, resolved against this meeting's present surnames."""
    t = " ".join(motion_text.split())
    spellings = {}
    for skey, fn in present_map.items():
        if skey not in ambiguous_surnames:
            spellings[skey] = fn
    for alias, target in SURNAME_ALIASES.items():
        if target in present_map and target not in ambiguous_surnames:
            spellings[alias] = present_map[target]
    if not spellings:
        return None, None
    alts = "|".join(re.escape(a) for a in sorted(spellings, key=len, reverse=True))

    mover = seconder = None
    mm = re.search(r"\b(" + alts + r")\b\s+(?:moved|move|moves|nominated|motioned|"
                   r"made\s+a\s+(?:substitute\s+)?motion|made\s+the\s+motion|"
                   r"forwarded|amended|recommended|recommends|recommend)",
                   t, re.IGNORECASE)
    if mm:
        mover = spellings[mm.group(1).lower()]
    sm = re.search(r"seconded\s+by\s+(?:Commissioner\s+)?(" + alts + r")\b", t,
                   re.IGNORECASE)
    if not sm:
        sm = re.search(r"\b(" + alts + r")\b\s+seconded", t, re.IGNORECASE)
    if sm:
        seconder = spellings[sm.group(1).lower()]
    return mover, seconder


# ---------------------------------------------------------------------------
# Meeting parsing.
# ---------------------------------------------------------------------------
# Top-level items use "1." / "2)"; sub-items use "4.1 " (decimal, no trailing punct).
# Agenda item headers: "4." / "4)" (integer needs trailing punct, so "20 citizens" is
# not an item), and sub-items "4.1 " / "4.1)" / "4.4)" (decimal, optional trailing punct).
ITEM_HEADER_RE = re.compile(
    r"^\s{0,12}((?:\d{1,2}\.\d+[.)]?)|(?:\d{1,2}[.)]))\s+(\S.*)$")
# A motion line, optionally prefixed by an agenda-item number ("3.4 Motion: ...").
MOTION_LABEL_RE = re.compile(
    r"^\s*(?:\d{1,2}(?:\.\d+)?\s*[.)]?\s+)?(?:Amended\s+|Substitute\s+)?Motion:\s*(.*)$",
    re.IGNORECASE)
# An attorney/recorder re-reading a PRIOR meeting's motion + vote "for the record"
# (a quoted historical action, not a vote taken at this meeting) — skip it.
REREAD_RE = re.compile(r"read\b[^.]{0,40}\bfor the record", re.IGNORECASE)
VOTE_LABEL_RE = re.compile(r"^\s*(?:Roll\s*Call\s+)?Vote:\s*(.*)$", re.IGNORECASE)
OUTCOME_RE = re.compile(
    r"motion\s+(?:passed|fail(?:s|ed)?|carried|did\s+not|was\s+(?:approved|denied|"
    r"defeated))|(?:passed|failed|fails)\s+unanimously", re.IGNORECASE)

# page-continuation header / footer / watermark lines to drop before parsing
DROP_LINE_RE = re.compile(
    r"^\s*(?:Lehi\s+City.*Planning\s+Commission|Planning\s+Commission.*\d{4}|"
    r"Page\s+\d+|\d{1,3}|DRAFT|153\s+North\s+100\s+East|Lehi,\s+UT|\(801\))\s*$",
    re.IGNORECASE)


def clean_lines(text):
    out = []
    for ln in text.split("\n"):
        if DROP_LINE_RE.match(ln):
            continue
        out.append(ln)
    return out


def build_global_surnames(index_rows):
    """surname_key -> set(canonical full names) across the whole corpus, built from the
    'Members Present:' / 'Members Absent:' headers. Used to anchor roll-call name
    matching: roll calls sometimes name a commissioner that meeting's header omitted
    (or contradictorily marks excused), so matching against the GLOBAL roster — not
    just the per-meeting present-set — is what catches every real vote."""
    by_surname = defaultdict(set)
    for row in index_rows:
        md = os.path.join(REPO, row["path"])
        if not os.path.exists(md):
            continue
        t = open(md, encoding="utf-8").read()
        for nm in meeting_present(t) + meeting_absent(t):
            by_surname[surname_key(nm)].add(nm)
    return by_surname


def resolve_for_meeting(global_by_surname, present_names):
    """surname_key -> canonical full name for THIS meeting. Globally-unique surnames
    map directly; a surname held by >1 person (only 'peterson') is disambiguated by who
    is present this meeting. Returns (resolved_map, ambiguous_set)."""
    present_set = set(present_names)
    resolved, ambiguous = {}, set()
    for skey, fns in global_by_surname.items():
        if len(fns) == 1:
            resolved[skey] = next(iter(fns))
        else:
            here = [fn for fn in fns if fn in present_set]
            if len(here) == 1:
                resolved[skey] = here[0]
            else:
                ambiguous.add(skey)   # both/neither present -> never guess
    return resolved, ambiguous


def parse_meeting(text, global_by_surname):
    present = meeting_present(text)
    present_map, ambiguous = resolve_for_meeting(global_by_surname, present)
    lines = clean_lines(text)
    n = len(lines)

    # --- collect blocks (item / motion / vote) ---
    blocks = []
    i = 0
    skip_motion = skip_vote = False   # for a re-read "for the record" historical block
    while i < n:
        line = lines[i]
        # the cue can wrap ("...read it" / "for the record:"), so test a 2-line window
        window = line + " " + (lines[i + 1] if i + 1 < n else "")
        if REREAD_RE.search(window):
            skip_motion = True
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
                    k = j
                    while k < n and lines[k].strip() == "":
                        k += 1
                    if k < n and re.match(
                            r"\s*(?:The\s+)?[Mm]otion\s+(?:passed|failed|fails|fail|"
                            r"carried|tied|did\s+not|was\s+(?:approved|denied|"
                            r"defeated))\b", lines[k]):
                        while k < n and lines[k].strip() != "":
                            buf.append(lines[k]); k += 1
                        j = k
                    break
                buf.append(nl)
                j += 1
            if skip_vote:
                skip_vote = False          # drop the re-read historical roll call
            else:
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
            if skip_motion:
                skip_motion = False        # drop the re-read historical motion...
                skip_vote = True           # ...and its following roll call
            else:
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

    votes = []
    motion_no = 0
    last_item = ""
    pending_motion = None

    def emit(motion_text, vote_block):
        nonlocal motion_no
        parsed = parse_rollcall(vote_block, present_map, ambiguous)
        mover, seconder = parse_motion_meta(motion_text, present_map, ambiguous)
        stage, direction = stage_and_direction(motion_text)
        if stage == "recommendation" and parsed.get("stated_dir"):
            direction = parsed["stated_dir"]   # source's explicit disposition wins
        result = build_result(parsed, stage, direction)

        item_text = last_item
        proc_motion = re.search(
            r"\b(recess|adjourn|table the|tabled\b|nominat\w*|re-?elect\w*|elect\w*|"
            r"approve the minutes|approve the consent|by-?laws?)\b",
            motion_text, re.IGNORECASE)
        motion_head = " ".join(re.split(r"(?<=[.])\s+", motion_text)[:2])
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

        motion_no += 1
        votes.append({
            "motion_no": motion_no,
            "motion": desc[:600],
            "body": BODY,
            "motion_type": mtype,
            "stage": "pc_recommendation" if stage == "recommendation"
                     else "pc_final_action",
            "direction": direction,
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "aye": list(parsed["buckets"]["aye"]),
            "nay": list(parsed["buckets"]["nay"]),
            "abstain": list(parsed["buckets"]["abstain"]),
            "absent": list(parsed["buckets"]["absent"]),
            "recuse": list(parsed["buckets"]["recuse"]),
            "names_recorded": parsed["names_recorded"],
            "outcome": parsed["outcome"],
            "printed_tally": list(parsed["printed"]) if parsed["printed"] else None,
        })

    for kind, ln, btxt in blocks:
        if kind == "item":
            last_item = btxt
        elif kind == "motion":
            # flush a previous motion that carried an inline tally-only outcome
            if pending_motion is not None and OUTCOME_RE.search(pending_motion):
                emit(pending_motion, pending_motion)
            pending_motion = btxt
        elif kind == "vote":
            emit(pending_motion or "", btxt)
            pending_motion = None
    if pending_motion is not None and OUTCOME_RE.search(pending_motion):
        emit(pending_motion, pending_motion)

    return votes, present, meeting_absent(text)


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def load_index():
    with open(MINUTES_INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def json_path_for(row):
    rel = row["path"].replace("planning_commission/minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rows = load_index()
    global_by_surname = build_global_surnames(rows)
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
        try:
            votes, present, absent = parse_meeting(text, global_by_surname)
        except Exception as e:  # noqa
            unparsed.append(f"{row['path']} (parse error: {e})")
            continue
        meeting_obj = {
            "date": row["date"],
            "title": TITLE,
            "body": BODY,
            "slug": row.get("slug", ""),
            "source": row["path"],
            "format": row.get("format", "text"),
            "members_present": present,
            "members_absent": absent,
            "votes": votes,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting_obj, f, indent=1, ensure_ascii=False)

    rebuild_csv()
    build_roster()
    stats = recompute_stats()
    print(json.dumps(stats, indent=2))
    if unparsed:
        print("UNPARSED:", json.dumps(unparsed, indent=2))


def iter_jsons():
    for dirpath, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dirpath, fn)


def rebuild_csv():
    rows_out = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        date = mtg["date"]; year = date[:4]; source = mtg["source"]
        for v in mtg["votes"]:
            base = {
                "date": date, "year": year, "title": TITLE, "body": BODY,
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


def build_roster():
    """Aggregate present-appearances across all meetings -> roster.csv."""
    first, last, count = {}, {}, {}
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        d = mtg["date"]
        for name in mtg.get("members_present", []):
            count[name] = count.get(name, 0) + 1
            if name not in first or d < first[name]:
                first[name] = d
            if name not in last or d > last[name]:
                last[name] = d
    with open(ROSTER_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for name in sorted(count, key=lambda x: (-count[x], x)):
            w.writerow([name, first[name], last[name], count[name]])


def recompute_stats():
    meetings = motions = member_rows = named = tally_only = contested = 0
    recs = finals = 0
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        for v in mtg["votes"]:
            motions += 1
            named += 1 if v.get("names_recorded") else 0
            tally_only += 0 if v.get("names_recorded") else 1
            recs += 1 if v.get("stage") == "pc_recommendation" else 0
            finals += 1 if v.get("stage") == "pc_final_action" else 0
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                member_rows += len(v[k])
    return {"meetings": meetings, "motions": motions, "member_vote_rows": member_rows,
            "named_motions": named, "tally_only_motions": tally_only,
            "recommendations": recs, "final_actions": finals,
            "contested": contested}


if __name__ == "__main__":
    main()
