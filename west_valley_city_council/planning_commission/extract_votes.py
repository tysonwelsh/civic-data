#!/usr/bin/env python3
"""
extract_votes.py — West Valley City PLANNING COMMISSION vote extraction.

Reads the 263 minutes markdown files listed in
`planning_commission/minutes_index.csv` (covers BOTH "Planning Commission
Meeting"/regular and "Planning Commission Study Meeting"), finds each recorded
motion (mover / seconder / per-member roll call or voice-vote tally), tags it
recommendation-vs-final-action, and emits:

  - one JSON per meeting -> planning_commission/votes/<year>/<week>/<date>_<slug>.json
  - a rebuilt long-format CSV  -> planning_commission/all_votes.csv
  - roster.csv                 -> planning_commission/roster.csv
  - a validation report        -> planning_commission/votes/_validation_report.txt

CARDINAL RULE: never fabricate. A voice-vote / tally with no per-member names
("A voice vote was taken, and all five Commissioners were in favor") is recorded
with names_recorded:false and EMPTY member lists — the count/result is kept, the
individual votes are NOT guessed.

body = "PlanningCommission" on EVERY row (regular AND study); title="Planning
Commission". The `source` column keeps the markdown path (which encodes regular
vs study via the slug).

Run:  python3 planning_commission/extract_votes.py
Resumable: skips meetings whose JSON already exists unless --force is passed.
"""
import os, re, csv, json, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = os.path.join(REPO, "planning_commission")
MIN_DIR = os.path.join(PC, "minutes")
VOTES_DIR = os.path.join(PC, "votes")
INDEX = os.path.join(PC, "minutes_index.csv")
ALL_VOTES = os.path.join(PC, "all_votes.csv")
ROSTER = os.path.join(PC, "roster.csv")
VALIDATION = os.path.join(VOTES_DIR, "_validation_report.txt")

FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# Canonical roster.  Roll-call / motion lines name members by ROLE + LAST name
# ("Commissioner Porter", "Chair Fuller", "Vice Chairperson Lovato").  Last
# names are unique across the 2020-2026 Planning Commission, so we map last name
# -> canonical full name.  OCR / clerical spelling variants are folded in.
# (Full names harvested from the attendance headers; see roster.csv.)
# ---------------------------------------------------------------------------
LASTNAME_TO_FULL = {
    "fuller":   "Brent Fuller",
    "meaders":  "Clover Meaders",
    "mcewen":   "David McEwen",
    "winters":  "Martell Winters",
    "wood":     "Cindy Wood",
    "lovato":   "Mathew Lovato",
    "porter":   "Darrick Porter",
    "woodruff": "Harold Woodruff",
    "drozdek":  "Nancy Drozdek",
    "layton":   "Renee Layton",
    "durfee":   "Rob Durfee",
    "matagi":   "Pauline Matagi",
    "ramirez":  "Adrianne Ramirez",
}
# spelling variants seen in the corpus -> canonical last-name key
LASTNAME_ALIASES = {
    "woodruf":  "woodruff",
    "levato":   "lovato",
    "mcewan":   "mcewen",
    "mcewen":   "mcewen",
}
# full-name typos seen in attendance headers -> canonical full name
FULLNAME_FIX = {
    "martel winters": "Martell Winters",
    "mathew levato":  "Mathew Lovato",
}

ROLE = r"(?:Commissioner|Commission|Chair(?:person|man|woman)?|Vice[\s-]?Chair(?:person|man|woman)?)"

VOTE_TOK = r"(Yes|No|Aye|Nay|Abstain(?:ed)?|Absent|Excused|Recuse(?:d)?|N/?A|Conflict(?:ed)?)"

VOTE_NORM = {
    "yes": "Aye", "aye": "Aye",
    "no": "Nay", "nay": "Nay",
    "abstain": "Abstain", "abstained": "Abstain",
    "absent": "Absent", "excused": "Absent",
    "recuse": "Recuse", "recused": "Recuse",
    "n/a": "Recuse", "na": "Recuse", "conflict": "Recuse", "conflicted": "Recuse",
}


# First-name (uniqueness) gate — latent hardening; a PURE NO-OP for WVC today.
# ---------------------------------------------------------------------------
# Roll-call lines name commissioners by LAST name only, so surname->full
# resolution is the sole attribution path.  Every WVC PC surname is unique
# across 2020-2026, so each surname maps to exactly ONE full (first+last) name
# and the gate below always passes -> byte-identical output.  It exists so that
# if a future roster ever REUSED a surname across eras (the "Deborah vs Lisa
# Jensen" collision that bit other cities), surname resolution would REFUSE
# (return None -> keep the printed name) rather than silently attribute the
# vote to whichever full name happened to sit in the dict.  We never guess.
SURNAME_TO_FULLS = {}
for _last, _full in LASTNAME_TO_FULL.items():
    SURNAME_TO_FULLS.setdefault(_last, set()).add(_full)


def canon_last(token):
    t = token.strip().strip(".,'").lower()
    t = LASTNAME_ALIASES.get(t, t)
    # exact surname match, gated on a UNIQUE full-name resolution (first-name
    # gate): resolve only when the surname maps to exactly one full name.
    fulls = SURNAME_TO_FULLS.get(t)
    if fulls is not None:
        return next(iter(fulls)) if len(fulls) == 1 else None
    # unique-prefix fallback for truncations (already gated: single candidate)
    if len(t) >= 5:
        cands = {full for last, full in LASTNAME_TO_FULL.items()
                 if last.startswith(t) or t.startswith(last)}
        if len(cands) == 1:
            return next(iter(cands))
    return None


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
# Motion statement: "<Role> <Last> motioned/moved/made a motion to|for ..."
RE_MOVED = re.compile(
    ROLE + r"\s+([A-Z][A-Za-z'\-]+)\s+"
    r"(?:motioned|moved|made\s+a\s+motion)\s+"
    r"(to|for|that)\s+(.+?)(?=(?:\.\s)|(?:\.\n)|\n\s*\n|$)",
    re.DOTALL | re.IGNORECASE)

RE_SECOND = re.compile(
    ROLE + r"\s+([A-Z][A-Za-z'\-]+)\s+seconded",
    re.IGNORECASE)

# A per-member roll-call line: "<Role> <Last>   Yes/No".  An optional leading
# vote-block label ("Vote:", "VOTE:", "Roll Call Vote:") may share the line with
# the first voter, e.g. "VOTE:   Commissioner McEwen   Yes".
RE_ROLLCALL_LINE = re.compile(
    r"^[ \t]*(?:(?:Roll\s*Call\s+)?Vote:\s*)?(?:"
    # role-prefixed form: "Commissioner Porter   Yes"  -> groups 1,2
    + ROLE + r"\s+([A-Z][A-Za-z'\-]+)\s+" + VOTE_TOK
    # bare colon form (seen 2025-02-26): "Porter: Yes"  -> groups 3,4
    + r"|([A-Z][A-Za-z'\-]+):\s*" + VOTE_TOK
    + r")\b",
    re.IGNORECASE)

# noise inside a roll-call block (page footers, page numbers, headers)
RE_NOISE = re.compile(
    r"^\s*(?:"
    r"(?:Minutes of\b.*)"
    r"|(?:.*Planning Commission.*(?:Minutes|Public Hearing|Meeting).*)"
    r"|(?:WEST VALLEY CITY\b.*)"
    r"|(?:Page\s+\d+\s+of\s+\d+.*)"
    r"|(?:-?\s*\d+\s*-?\s*)"
    r")$", re.IGNORECASE)

# Outcome line after a vote block (or standalone for tally-only).
RE_OUTCOME = re.compile(
    r"(Unanimous(?:ly)?|Majority)?[^\n]*?"
    r"\b(Approved?|Denied|Deny|Continued?|Tabled?|Withdrawn|Pass(?:ed)?|"
    r"Carried|Fail(?:ed)?|FAIL)\b",
    re.IGNORECASE)

# Narrative tally verdicts with no per-member list and no dash-result line, e.g.
# "Vote: Motion passed unanimously.", "Motion carried.", "Motion failed.",
# "all members voted in favor".
RE_TALLY_VERDICT = re.compile(
    r"motion\s+(?:passed|carried|failed|approved|denied)(?:\s+unanimously)?"
    r"|(?:passed|carried)\s+unanimously"
    r"|all\s+(?:members|commissioners)\s+(?:voted\s+)?in\s+favor",
    re.IGNORECASE)

# voice-vote / tally-only marker
RE_VOICE = re.compile(
    r"(?:a\s+)?voice\s+vote\s+was\s+taken[,.]?\s*and\s+all\s+"
    r"(?:(\w+)\s+)?[Cc]ommissioners?\s+were\s+in\s+favor",
    re.IGNORECASE)
RE_VOICE_SIMPLE = re.compile(r"voice\s+vote\s+was\s+taken", re.IGNORECASE)

# A motion that never came to a vote: "failed/died for lack of a second", "no second".
RE_NO_SECOND = re.compile(
    r"(?:fail(?:ed)?|died)\s+(?:due\s+to|for|because\s+of)\s+(?:a\s+)?lack\s+of\s+a?\s*second"
    r"|lack\s+of\s+a\s+second|no\s+second\s+(?:was\s+)?(?:made|received|offered)",
    re.IGNORECASE)

# A genuine STANDALONE result line for a tally-only vote (not the motion's own
# "approve" verb): "Unanimously – C-1-2020 – Approved", "Majority … Continued",
# "– FAIL", "APPROVE … FAIL".  Requires either a Unanimous/Majority lead-in or a
# dash immediately before the outcome word.
RE_TALLY_RESULT = re.compile(
    r"(?:(?:Unanimous(?:ly)?|Majority)\b[^\n]*?\b"
    r"(Approved?|Denied|Continued?|Tabled?|Withdrawn|Fail(?:ed)?))"
    r"|(?:[–—-]\s*(Approved?|Denied|Continued?|Tabled?|Withdrawn|FAIL|Failed)\b)",
    re.IGNORECASE)

NUM_WORDS = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
             "eight":8,"nine":9,"ten":10,"eleven":11}

# Case-number prefix -> (motion_type, action_category)
# action_category: "recommendation" (forwarded to City Council — legislative)
#                  "final"          (Planning Commission final action)
PREFIX_INFO = [
    ("ZSMI", "Site Plan", "final"),
    ("ZPR",  "Other Land-Use", "final"),
    ("GPZ",  "General Plan & Rezone", "recommendation"),
    ("PUD",  "Planned Unit Development", "recommendation"),
    ("SMI",  "Site Plan", "final"),
    ("ZT",   "Zone Text Amendment", "recommendation"),
    ("SD",   "Subdivision", "recommendation"),
    ("SV",   "Street Vacation", "recommendation"),
    ("SA",   "Subdivision Amendment", "recommendation"),
    ("CA",   "Conditional Use", "final"),
    ("GP",   "General Plan Amendment", "recommendation"),
    ("AD",   "Other Land-Use", "final"),
    ("PR",   "Other Land-Use", "final"),
    ("C",    "Conditional Use", "final"),
    ("Z",    "Rezone", "recommendation"),
    ("S",    "Subdivision", "recommendation"),
    ("M",    "Code Exception", "final"),
    ("B",    "Other Land-Use", "final"),
]
# longest-first alternation for case-number detection
_PREFIX_ALT = "|".join(p for p, _, _ in sorted(PREFIX_INFO, key=lambda x: -len(x[0])))
RE_CASE = re.compile(r"\b(" + _PREFIX_ALT + r")-\d{1,3}-20\d{2}", re.IGNORECASE)


def case_info(motion_text):
    m = RE_CASE.search(motion_text)
    if not m:
        return None, None
    pref = m.group(1).upper()
    for p, mt, cat in PREFIX_INFO:
        if p == pref:
            return mt, cat
    return None, None


# ---------------------------------------------------------------------------
# Attendance parsing (roster)
# ---------------------------------------------------------------------------
RE_ATT_HDR = re.compile(
    r"(WEST VALLEY CITY PLANNING COMMISSION MEMBERS|THE FOLLOWING MEMBERS WERE PRESENT:)",
    re.IGNORECASE)
RE_STOP_HDR = re.compile(
    r"^\s*(WEST VALLEY|ABSENT|PLANNING DIVISION|LEGAL|ADMINISTRATION|AUDIENCE|"
    r"STAFF|THE FOLLOWING|OTHERS)", re.IGNORECASE)
RE_ABSENT_HDR = re.compile(r"^\s*ABSENT\b", re.IGNORECASE)


def _names_from_block(lines, start):
    buf = []
    j = start
    while j < len(lines):
        s = lines[j].strip()
        if RE_STOP_HDR.match(s):
            break
        if s:
            buf.append(s)
        elif buf:
            break
        j += 1
    out = []
    for chunk in re.split(r",|\band\b", " ".join(buf)):
        nm = re.sub(r"\b(Chair(?:person)?|Vice\s+Chair(?:person)?|Commissioner)\b", "",
                    chunk, flags=re.IGNORECASE).strip().strip(".")
        nm = " ".join(nm.split())
        m = re.match(r"^([A-Z][a-z]+)\s+([A-Z][A-Za-z'\-]+)$", nm)
        if m:
            full = FULLNAME_FIX.get(nm.lower(), nm)
            # only keep names whose last name is a known commissioner
            if canon_last(full.split()[-1]):
                out.append(canon_last(full.split()[-1]))
    return out


def parse_attendance(text):
    """Return set of canonical commissioner full names present at the meeting."""
    lines = text.split("\n")
    present = set()
    absent = set()
    for i, l in enumerate(lines):
        if RE_ATT_HDR.search(l):
            for nm in _names_from_block(lines, i + 1):
                present.add(nm)
        elif RE_ABSENT_HDR.match(l):
            for nm in _names_from_block(lines, i + 1):
                absent.add(nm)
    return present - absent if present else present


# ---------------------------------------------------------------------------
# Roll-call block parser
# ---------------------------------------------------------------------------
def parse_rollcall_block(lines, start_idx, bound_idx):
    members = {}
    unknown = []
    i = start_idx
    collected = False
    blanks = 0
    while i < len(lines) and i < bound_idx:
        line = lines[i]
        m = RE_ROLLCALL_LINE.match(line)
        if m:
            name_tok = m.group(1) or m.group(3)
            vote_tok = m.group(2) or m.group(4)
            full = canon_last(name_tok)
            vote = VOTE_NORM.get(re.sub(r"[^a-z/]", "", vote_tok.lower()),
                                 vote_tok.capitalize())
            if full:
                members[full] = vote
            else:
                unknown.append((name_tok, vote_tok))
            collected = True
            blanks = 0
            i += 1
            continue
        if line.strip() == "":
            blanks += 1
            if collected and blanks >= 5:
                break
            i += 1
            continue
        if RE_NOISE.match(line):
            i += 1
            continue
        if collected:
            break
        if i - start_idx > 8:
            break
        i += 1
    return members, unknown, i


# ---------------------------------------------------------------------------
# Outcome / result-string logic
# ---------------------------------------------------------------------------
def motion_verb(motion_text):
    t = motion_text.lower()
    if re.search(r"\b(continue|continuance|table|postpone)\b", t):
        return "continue"
    if re.search(r"\bden(?:y|ial)\b", t):
        return "deny"
    if re.search(r"\bwithdraw", t):
        return "withdraw"
    if re.search(r"\b(approv|adopt|recommend|grant)\b", t):
        return "approve"
    if re.search(r"\b(elect|nominate|appoint)\b", t):
        return "elect"
    return "approve"  # default land-use motions are approvals


def is_procedural(motion_text):
    t = motion_text.lower()
    if re.search(r"\b(adjourn|recess|reconvene)\b", t):
        return True
    if re.search(r"minutes", t) and re.search(r"\b(approve|adopt)\b", t):
        return True
    return False


def is_appointment(motion_text):
    return bool(re.search(r"\b(elect|nominate|appoint|reappoint)\b", motion_text, re.I))


def outcome_from_line(result_line):
    """Return one of approved/denied/continued/failed/withdrawn/tabled/None."""
    if not result_line:
        return None
    m = RE_OUTCOME.search(result_line)
    if not m:
        return None
    w = m.group(2).lower()
    if w.startswith("approv"):
        return "approved"
    if w.startswith("den") or w == "deny":
        return "denied"
    if w.startswith("continu"):
        return "continued"
    if w.startswith("tabl"):
        return "tabled"
    if w.startswith("withdraw"):
        return "withdrawn"
    if w.startswith("fail") or w == "fail":
        return "failed"
    if w.startswith("pass") or w == "carried":
        return "passed"
    return None


def build_result(category, verb, outcome, ayes, nays, passed, proc):
    """Compose the `result` string per the required encoding."""
    tally = f"{ayes}:{nays}"
    # Procedural / appointment -> "N:N Pass|Fail"
    if proc:
        return f"{tally} {'Pass' if passed else 'Fail'}"

    # Continuances / tabling are deferrals, not a recommendation or final action.
    if outcome in ("continued", "tabled") or (verb == "continue" and outcome in (None, "passed")):
        word = "Continued" if outcome != "tabled" else "Tabled"
        return f"{tally} {'Pass' if passed else 'Fail'} ({word})"
    if outcome == "withdrawn" or verb == "withdraw":
        return f"{tally} {'Pass' if passed else 'Fail'} (Withdrawn)"

    # Decide approved vs denied for the application.
    # outcome word governs when present; otherwise derive from verb + pass/fail.
    if outcome == "approved":
        approved = True
    elif outcome == "denied":
        approved = False                     # minutes say the application ended denied
    elif outcome == "failed":
        approved = (verb == "deny")          # a "deny" motion that failed -> app not denied
    else:  # no outcome word: derive from the motion verb + whether it passed
        approved = (not passed) if verb == "deny" else passed

    if category == "recommendation":
        direction = "Positive" if approved else "Negative"
        return f"{direction} recommendation {tally}"
    else:  # final action
        word = "Approved" if approved else "Denied"
        return f"{tally} {word} (Final Action)"


# ---------------------------------------------------------------------------
# Per-meeting extraction
# ---------------------------------------------------------------------------
def extract_meeting(path, rel_source, date, title):
    text = open(path, encoding="utf-8").read()
    # pdftotext emits a form-feed (\x0c) at page breaks; it sometimes glues to the
    # start of a real content line (e.g. "\x0cCommissioner Woodruff No"). Strip it
    # so such lines parse as ordinary roll-call lines.
    text = text.replace("\f", "")
    lines = text.split("\n")
    present = sorted(parse_attendance(text))

    votes = []
    motion_no = 0

    for m in RE_MOVED.finditer(text):
        mover = canon_last(m.group(1)) or m.group(1)
        connector = m.group(2).lower()
        rest = re.sub(r"\s+", " ", m.group(3)).strip()
        # reconstruct readable motion text: "to approve X" / "that X be approved"
        motion_text = (rest if connector == "that" else "to " + rest).strip()
        if len(motion_text) > 400:
            motion_text = motion_text[:400].rsplit(" ", 1)[0] + "…"

        # bound the search window at the next motion so a vote isn't stolen
        nxt = RE_MOVED.search(text, m.end())
        bound_char = nxt.start() if nxt else len(text)
        window = text[m.start():bound_char]

        # seconder
        sm = RE_SECOND.search(window)
        seconder = (canon_last(sm.group(1)) or sm.group(1)) if sm else ""

        # roll-call block: first per-member vote line within the window
        members, unknown = {}, []
        names_recorded = False
        result_line = ""
        rc_search_from = m.end()
        # find first roll-call line position
        rc_match = RE_ROLLCALL_LINE.search(text, rc_search_from, bound_char) \
            if False else None
        # line-based scan
        start_line = text[:m.end()].count("\n")
        bound_line = text[:bound_char].count("\n") + 1
        first_rc = None
        for li in range(start_line, min(bound_line, len(lines))):
            if RE_ROLLCALL_LINE.match(lines[li]):
                first_rc = li
                break
        if first_rc is not None:
            members, unknown, end_line = parse_rollcall_block(lines, first_rc, bound_line)
            if members or unknown:
                names_recorded = True
                # result line is the next meaningful (non-noise) line(s)
                for li in range(end_line, min(end_line + 6, len(lines))):
                    s = lines[li]
                    if s.strip() == "" or RE_NOISE.match(s):
                        continue
                    if RE_OUTCOME.search(s):
                        result_line = s.strip()
                    break

        # tally-only / voice vote
        voice_count = None
        if not names_recorded:
            # Motions that failed for lack of a second never came to a vote -> skip.
            if RE_NO_SECOND.search(window):
                continue
            vm = RE_VOICE.search(window)
            if vm:
                voice_count = NUM_WORDS.get((vm.group(1) or "").lower())
            else:
                vm = RE_VOICE_SIMPLE.search(window)
            # find a GENUINE standalone result line (not the motion's own "approve"
            # verb): a dash/Unanimous/Majority result line, or a narrative verdict
            # ("Motion passed unanimously.", "all members voted in favor").
            om = RE_TALLY_RESULT.search(window) or RE_TALLY_VERDICT.search(window)
            if om:
                pos = m.start() + om.start()
                ln = text[:pos].count("\n")
                result_line = lines[ln].strip()
            if not vm and not om:
                # no recorded vote outcome near this motion -> not a vote, skip
                continue

        # classify
        proc = is_procedural(motion_text)
        appt = is_appointment(motion_text)
        verb = motion_verb(motion_text)
        if proc or appt:
            motion_type = "Appointment" if appt else "Procedural/Administrative"
            category = "procedural"
        else:
            # The motion text is truncated and sometimes omits the case number
            # (e.g. "Commissioner X motioned to approve."); the case number always
            # appears in the result line and the agenda heading above, so search
            # those too (motion text first so it wins when present).
            ctx = motion_text + " " + result_line + " " + \
                text[max(0, m.start() - 600):m.start()]
            mt, cat = case_info(ctx)
            if cat is None:
                # no case number: fall back on keywords
                t = motion_text.lower()
                if re.search(r"general plan|rezone|zone change|zoning text|ordinance amend|vacat|annex", t):
                    mt, cat = "Other Land-Use", "recommendation"
                elif re.search(r"conditional use|site plan|subdivision|plat", t):
                    mt, cat = "Other Land-Use", "final"
                else:
                    mt, cat = "Other", "final"
            motion_type = mt
            category = cat

        # tally
        aye = sorted([k for k, v in members.items() if v == "Aye"])
        nay = sorted([k for k, v in members.items() if v == "Nay"])
        abstain = sorted([k for k, v in members.items() if v == "Abstain"])
        absent = sorted([k for k, v in members.items() if v == "Absent"])
        recuse = sorted([k for k, v in members.items() if v == "Recuse"])

        outcome = outcome_from_line(result_line)

        if names_recorded:
            ayes, nays = len(aye), len(nay)
            passed = ayes > nays if (ayes or nays) else True
        else:
            # voice / tally vote: no per-member names (CARDINAL RULE -> member lists
            # stay empty, we never attribute individual votes).  We DO record the
            # count: from an explicit number in the wording ("all five
            # Commissioners"), else — when the minutes explicitly say the vote was
            # unanimous / all in favor — the count is the number of commissioners
            # present (a count inference, not a per-member guess); else 0:0.
            unanimous = bool(re.search(
                r"unanimous|all\s+(?:members|commissioners)\b[^\n]*favor", result_line, re.I)) or \
                (vm is not None and "favor" in
                 window[vm.start():vm.start() + 120].lower())
            if voice_count is not None:
                ayes, nays = voice_count, 0
            elif unanimous and present:
                ayes, nays = len(present), 0
            else:
                ayes, nays = 0, 0
            # A unanimous vote passed the motion (even a "to deny" motion, which
            # enacts a denial). Only a genuinely FAILED motion is passed=False; the
            # substantive approved-vs-denied direction is handled by build_result.
            passed = (outcome != "failed")

        # If outcome word contradicts tally pass/fail, the per-member tally governs.
        result_str = build_result(category, verb, outcome, ayes, nays, passed,
                                  proc or appt)

        motion_no += 1
        rec = {
            "motion_no": motion_no,
            "motion": motion_text,
            "body": "PlanningCommission",
            "motion_type": motion_type,
            "action_category": "procedural" if (proc or appt) else category,
            "result": result_str,
            "result_source": result_line,
            "outcome_word": outcome or "",
            "mover": mover,
            "seconder": seconder,
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
        }
        if not names_recorded:
            rec["tally_only"] = {"ayes": ayes, "nays": nays,
                                 "source": result_line or "voice vote"}
        if unknown:
            rec["_unknown_rollcall"] = unknown
        votes.append(rec)

    return {
        "date": date,
        "title": "Planning Commission",
        "meeting_type": "study" if "study" in rel_source else "regular",
        "body": "PlanningCommission",
        "present": present,
        "source": rel_source,
        "votes": votes,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)

    all_csv_rows = []
    val_lines = []
    stats = dict(meetings=0, motions=0, member_rows=0, named=0, tally=0,
                 contested=0, mismatches=0, recommendations=0, final=0,
                 procedural=0, study_no_votes=0, unparsed=[])
    roster = {}  # full name -> dict(first, last, n)
    tally_mismatches = []

    for row in rows:
        path = os.path.join(REPO, row["path"])
        if not os.path.exists(path):
            stats["unparsed"].append(row["path"] + " (missing file)")
            continue
        rel_source = row["path"].replace("planning_commission/", "", 1)
        year = row["year"]
        parts = row["path"].split("/")
        week = parts[-2]
        out_dir = os.path.join(VOTES_DIR, year, week)
        out_json = os.path.join(out_dir, parts[-1].replace(".md", ".json"))

        if os.path.exists(out_json) and not FORCE:
            meeting = json.load(open(out_json, encoding="utf-8"))
        else:
            try:
                meeting = extract_meeting(path, rel_source, row["date"], row["title"])
            except Exception as e:
                stats["unparsed"].append(row["path"] + f" (parse error: {e})")
                continue
            os.makedirs(out_dir, exist_ok=True)
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(meeting, f, indent=1, ensure_ascii=False)

        stats["meetings"] += 1
        date = meeting["date"]

        # roster from attendance header UNION anyone who cast a roll-call vote
        # (a recorded vote is the strongest evidence of presence; some minutes'
        # attendance headers omit a member who clearly voted — e.g. Drozdek on
        # 2024-07-03 — so the roll call governs).
        attendees = set(meeting.get("present", []))
        for v in meeting["votes"]:
            for grp in ("aye", "nay", "abstain", "absent", "recuse"):
                if grp == "absent":
                    continue  # marked Absent != present
                attendees.update(v[grp])
        for nm in attendees:
            r = roster.setdefault(nm, {"first": date, "last": date, "n": 0})
            r["first"] = min(r["first"], date)
            r["last"] = max(r["last"], date)
            r["n"] += 1

        is_study = meeting.get("meeting_type") == "study"
        if is_study and not meeting["votes"]:
            stats["study_no_votes"] += 1

        for v in meeting["votes"]:
            stats["motions"] += 1
            cat = v.get("action_category")
            if cat == "recommendation":
                stats["recommendations"] += 1
            elif cat == "final":
                stats["final"] += 1
            else:
                stats["procedural"] += 1
            if v["names_recorded"]:
                stats["named"] += 1
            else:
                stats["tally"] += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                stats["contested"] += 1

            # validation: roll-call names within roster; result-vs-tally sanity
            if v["names_recorded"]:
                for grp in ("aye", "nay", "abstain", "absent", "recuse"):
                    for nm in v[grp]:
                        if nm not in LASTNAME_TO_FULL.values():
                            val_lines.append(f"{date} motion {v['motion_no']}: "
                                             f"off-roster name {nm!r}")
                        elif nm in roster and not (roster[nm]["first"] <= date <= roster[nm]["last"]):
                            pass  # range fills incrementally; final pass below
                if "_unknown_rollcall" in v:
                    val_lines.append(f"{date} motion {v['motion_no']}: "
                                     f"unrecognized roll-call name(s): {v['_unknown_rollcall']}")
                # source typo: minutes printed "Unanimous(ly)" but a Nay exists
                src = (v.get("result_source") or "")
                nays = len(v["nay"])
                if re.search(r"unanimous", src, re.I) and nays > 0:
                    tally_mismatches.append(
                        f"{date} motion {v['motion_no']}: minutes printed "
                        f"{src!r} but the roll call shows {nays} Nay — roll call retained "
                        f"as truth ({v['result']})")

            # CSV rows
            base = dict(date=date, year=year, title="Planning Commission",
                        body="PlanningCommission",
                        motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v["mover"], seconder=v["seconder"],
                        source=rel_source)
            if v["names_recorded"]:
                for grp, label in (("aye", "Aye"), ("nay", "Nay"),
                                   ("abstain", "Abstain"), ("absent", "Absent"),
                                   ("recuse", "Recuse")):
                    for member in v[grp]:
                        r = dict(base); r["member"] = member; r["vote"] = label
                        all_csv_rows.append(r); stats["member_rows"] += 1
            else:
                r = dict(base); r["member"] = ""; r["vote"] = ""
                all_csv_rows.append(r)

    # second pass: validate roll-call dates within finalized roster ranges
    offrange = []
    for r in all_csv_rows:
        nm = r["member"]
        if nm and nm in roster:
            if not (roster[nm]["first"] <= r["date"] <= roster[nm]["last"]):
                offrange.append(f"{r['date']} {nm} voted outside attendance range "
                                f"({roster[nm]['first']}..{roster[nm]['last']})")
    # dedupe
    offrange = sorted(set(offrange))

    # write all_votes.csv
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    with open(ALL_VOTES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_csv_rows:
            w.writerow({k: r.get(k, "") for k in cols})

    # roster.csv
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(roster, key=lambda n: roster[n]["first"]):
            r = roster[nm]
            w.writerow([nm, r["first"], r["last"], r["n"]])

    # validation report
    with open(VALIDATION, "w", encoding="utf-8") as f:
        f.write("West Valley City PLANNING COMMISSION — vote extraction validation\n")
        f.write("=" * 64 + "\n\n")
        f.write(f"Meetings processed   : {stats['meetings']}\n")
        f.write(f"Motions extracted    : {stats['motions']}\n")
        f.write(f"Member-vote rows     : {stats['member_rows']}\n")
        f.write(f"Named roll-calls     : {stats['named']}\n")
        f.write(f"Tally-only motions   : {stats['tally']}\n")
        f.write(f"Recommendations      : {stats['recommendations']}\n")
        f.write(f"Final actions        : {stats['final']}\n")
        f.write(f"Procedural/appoint   : {stats['procedural']}\n")
        f.write(f"Contested motions    : {stats['contested']}\n")
        f.write(f"Study mtgs, no votes : {stats['study_no_votes']}\n")
        f.write(f"Distinct commissioners: {len(roster)}\n\n")
        f.write(f"Off-roster names     : {sum(1 for l in val_lines if 'off-roster' in l)}\n")
        f.write(f"Out-of-range votes   : {len(offrange)}\n\n")
        if offrange:
            f.write("Out-of-range roll-call votes:\n")
            for l in offrange:
                f.write("  - " + l + "\n")
            f.write("\n")
        if stats["unparsed"]:
            f.write("Unparsed / missing meetings:\n")
            for u in stats["unparsed"]:
                f.write("  - " + u + "\n")
            f.write("\n")
        f.write(f"Tally mismatches (source typos): {len(tally_mismatches)}\n")
        for l in tally_mismatches:
            f.write("  - " + l + "\n")
        f.write("\nIssues:\n")
        for l in val_lines:
            f.write("  - " + l + "\n")
        if not val_lines:
            f.write("  (none)\n")

    print(json.dumps({
        "meetings_processed": stats["meetings"],
        "motions_extracted": stats["motions"],
        "member_vote_rows": stats["member_rows"],
        "named_rollcall_motions": stats["named"],
        "tally_only_motions": stats["tally"],
        "recommendations": stats["recommendations"],
        "final_actions": stats["final"],
        "procedural": stats["procedural"],
        "contested_motions": stats["contested"],
        "study_meetings_no_votes": stats["study_no_votes"],
        "distinct_commissioners": len(roster),
        "off_roster": sum(1 for l in val_lines if "off-roster" in l),
        "out_of_range": len(offrange),
        "tally_mismatches": tally_mismatches,
        "unparsed_meetings": stats["unparsed"],
    }, indent=2))


if __name__ == "__main__":
    main()
