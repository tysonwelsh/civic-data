#!/usr/bin/env python3
"""
extract_votes.py — West Valley City council vote extraction.

Reads the 465 minutes markdown files under meeting_minutes/minutes/<year>/<week>/,
finds each recorded motion (mover / seconder / roll-call or tally), classifies it
into the fixed 12-category motion_type taxonomy, and emits:

  - one JSON per meeting -> meeting_minutes/votes/<year>/<week>/<date>_<slug>.json
  - a rebuilt long-format CSV   -> meeting_minutes/all_votes.csv
  - a validation report         -> meeting_minutes/votes/_validation_report.txt

NEVER invents who voted which way. When the minutes give only a tally
("voice vote ... all members voted in favor" / "Unanimous." with no per-member
roll call) the motion is recorded with names_recorded:false and EMPTY member lists.

Run:  python3 meeting_minutes/extract_votes.py
Resumable: skips meetings whose JSON already exists unless --force is passed.
"""
import os, re, csv, json, sys, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_DIR = os.path.join(REPO, "meeting_minutes", "minutes")
VOTES_DIR = os.path.join(REPO, "meeting_minutes", "votes")
INDEX = os.path.join(REPO, "meeting_minutes", "minutes_index.csv")
ALL_VOTES = os.path.join(REPO, "meeting_minutes", "all_votes.csv")
VALIDATION = os.path.join(VOTES_DIR, "_validation_report.txt")

FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# Canonical roster.  Roll-call lines name members by LAST name (e.g. "Mr.
# Huynh", "Councilmember Whetstone", "Mayor Lang", "Mayor Pro-Tem Buhler").
# Last names are unique across the 2020-2026 council, so we map last name ->
# canonical full name.  OCR spelling variants are folded in.
# ---------------------------------------------------------------------------
LASTNAME_TO_FULL = {
    "bigelow": "Ron Bigelow",
    "lang": "Karen Lang",
    "nordfelt": "Lars Nordfelt",
    "christensen": "Don Christensen",
    "huynh": "Tom Huynh",
    "buhler": "Steve Buhler",
    "harmon": "Scott Harmon",
    "whetstone": "William Whetstone",
    "fitisemanu": "Jake Fitisemanu",
    "wood": "Cindy Wood",
}
# OCR / spelling variants seen in the corpus -> canonical last-name key
LASTNAME_ALIASES = {
    "scot": "harmon",   # "Scot Harmon"
    "harman": "harmon",
}

# Full-name normalization for names captured in mover/seconder/present lists
FIRSTLAST_NORMALIZE = {
    "will whetstone": "William Whetstone",
    "scot harmon": "Scott Harmon",
}

PRESIDING_PREFIXES = ("mayor pro tem", "mayor pro-tem", "mayor", "councilmember",
                      "council member", "acting mayor", "mr.", "ms.", "mrs.")

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
# A "moved" statement: "Councilmember X moved to <verb> ..."  (X may be a
# multi-word name, possibly "Mayor Pro Tem X").
# Member-role prefixes.  Includes board-capacity synonyms (Board Member /
# Agency Member / Authority Member / Trustee / Chair / Director) so that if a
# separate RDA/MBA meeting is later acquired the SAME people are recognized as
# movers/seconders/voters under their board titles (they map to the identical
# council member names — no new members are created).
_ROLE_PREFIX = (r"(?:Council[A-Za-z]+|Council\s+Member|Mayor(?:\s+Pro[\s-]?\s?Tem)?|"
                r"Acting\s+Mayor|Board\s+Member|Agency\s+Member|Authority\s+Member|"
                r"Trustee|Chair(?:man|woman|person)?|Director|Mr\.|Ms\.|Mrs\.)")

RE_MOVED = re.compile(
    _ROLE_PREFIX + r"\s+"
    r"([A-Z][A-Za-z.''\-]+(?:\s+[A-Z][A-Za-z.''\-]+){0,2}?)\s+moved\s+to\s+(.+?)(?=\.\s|\.$|\n\n)",
    re.DOTALL)

RE_SECOND = re.compile(
    _ROLE_PREFIX + r"\s+"
    r"([A-Z][A-Za-z.''\-]+(?:\s+[A-Z][A-Za-z.''\-]+){0,2}?)\s+seconded\s+the\s+motion")

# A roll-call member/vote line:  "<prefix> <Lastname>   Yes/No"
# Prefixes seen in the corpus: Councilman / Councilwoman / Councilmember,
# Mr. / Ms. / Mrs., Mayor, Mayor Pro Tem / Pro-Tem / Pro- Tem, Acting Mayor.
RE_ROLLCALL_LINE = re.compile(
    r"^[ \t]*(Mayor\s+Pro[\s-]?\s?Tem|Mayor|Acting\s+Mayor|Council[A-Za-z]+|"
    r"Board\s+Member|Agency\s+Member|Authority\s+Member|Trustee|"
    r"Chair(?:man|woman|person)?|Director|Mr\.|Ms\.|Mrs\.)"
    r"\s+([A-Za-z.''\-]+)\s+"
    r"(Yes|No|Aye|Nay|Abstain|Abstained|Absent|Excused|Recuse|Recused|"
    r"N/A|N\\A|Conflict|Conflicted)\b",
    re.IGNORECASE)

RE_ROLLCALL_START = re.compile(r"A\s+roll\s*call\s+vote\s+was\s+taken", re.IGNORECASE)
RE_VOICE = re.compile(r"voice\s+vote\s+was\s+taken", re.IGNORECASE)

# Result/tally tokens that may appear after a roll call
RE_RESULT_WORD = re.compile(r"^\s*(Unanimous|Majority|The motion (?:carried|failed|passed)|Motion (?:carried|failed|passed)|Tie)\b",
                            re.IGNORECASE)

# Page-break / footer noise that can interrupt a roll-call block mid-list:
#   "MINUTES OF COUNCIL REGULAR MEETING – FEBRUARY 4, 2020"
#   "-10-"   (page number)
#   form-feed / blank
RE_NOISE = re.compile(
    r"^\s*(?:"
    r"MINUTES OF\b.*"                 # "MINUTES OF COUNCIL REGULAR MEETING – ..."
    r"|WEST VALLEY CITY\b.*"
    r"|City Council .*Minutes.*"
    r"|-?\s*\d+\s*-?\s*"              # page number  "-10-"
    r"|\f.*"
    r")$")

# ---------------------------------------------------------------------------
# Governing body ("body" column) detection.
#
# In Utah the council usually sits AS the board of the Redevelopment Agency
# (RDA), Community Reinvestment / Community Development & Renewal Agency
# (CRA/CDRA), and the Municipal Building Authority (MBA) — same members, often
# the same night.  Two ways this shows up:
#   (1) a SEPARATE meeting whose title is "Redevelopment Agency" / "Municipal
#       Building Authority" / etc. -> tag ALL its motions with that body; or
#   (2) an agenda block INSIDE a council meeting bracketed by "convened as the
#       Governing Board of the Redevelopment Agency" ... "reconvened as the
#       City Council" -> tag motions inside the bracket.
#
# West Valley City (this corpus): the acquired minutes are City Council meeting
# types ONLY (OnBase mtids 109/110/111).  WVC runs its RDA / MBA / CRA business
# in SEPARATE agency meetings (a distinct OnBase meeting type that was NOT
# acquired) — the council minutes merely "REVIEW AGENDA FOR SPECIAL
# REDEVELOPMENT AGENCY/MUNICIPAL BUILDING AUTHORITY" and note items that
# "require approval from both the City Council and the Redevelopment Agency
# Board."  Every recorded mover/seconder in the whole corpus is a
# "Councilmember" (or the Mayor) — there are NO board-capacity motions and NO
# in-council "convened as the … board" brackets.  So every motion here tags
# body=Council.  The detection below is kept general so that if the separate
# agency meetings are later acquired (or an in-council convene-block appears)
# they tag correctly with no further code changes.
# ---------------------------------------------------------------------------

# Title -> body, for the separate-meeting case (matched against the meeting
# `title` from minutes_index.csv).  Order matters: CRA/CDRA before RDA so a
# "Community Reinvestment / Development & Renewal Agency" title isn't shadowed.
BODY_TITLE_PATTERNS = [
    ("MBA",  re.compile(r"municipal building authority", re.I)),
    ("LBA",  re.compile(r"local building authority", re.I)),
    ("CRA",  re.compile(r"community reinvestment agency", re.I)),
    ("CDRA", re.compile(r"community development (?:and|&) renewal agency", re.I)),
    ("RDA",  re.compile(r"redevelopment agency", re.I)),
]

# In-council "convened as the … board" brackets.  group->body.
RE_CONVENE_AS = re.compile(
    r"(?:convened|reconvened|recessed and reconvened|now meeting|sit(?:ting)?)\s+as\s+"
    r"(?:the\s+)?(?:governing\s+board\s+of\s+(?:the\s+)?|board\s+of\s+(?:the\s+)?)?"
    r"(redevelopment agency|community reinvestment agency|"
    r"community development (?:and|&) renewal agency|municipal building authority|"
    r"local building authority)",
    re.I)
RE_RECONVENE_COUNCIL = re.compile(
    r"(?:reconvened|convened|recessed and reconvened|now meeting)\s+as\s+"
    r"(?:the\s+)?city\s+council",
    re.I)

_BODY_FROM_PHRASE = [
    ("MBA",  re.compile(r"municipal building authority", re.I)),
    ("LBA",  re.compile(r"local building authority", re.I)),
    ("CRA",  re.compile(r"community reinvestment agency", re.I)),
    ("CDRA", re.compile(r"community development (?:and|&) renewal agency", re.I)),
    ("RDA",  re.compile(r"redevelopment agency", re.I)),
]


def body_for_title(title):
    """Return the body if the meeting itself IS an agency meeting (separate
    meeting case), else 'Council'."""
    for body, pat in BODY_TITLE_PATTERNS:
        if pat.search(title or ""):
            return body
    return "Council"


def _phrase_to_body(phrase):
    for body, pat in _BODY_FROM_PHRASE:
        if pat.search(phrase):
            return body
    return "Council"


def build_body_spans(text, default_body):
    """Scan the meeting text for 'convened as the … Agency/Authority Board' /
    'reconvened as the City Council' brackets and return a list of
    (char_start, char_end, body) spans.  If the meeting is itself an agency
    meeting (default_body != Council) the whole document is that body and no
    brackets are needed.  When there are no convene markers, returns a single
    span covering the whole document with default_body."""
    if default_body != "Council":
        return [(0, len(text), default_body)]
    # collect markers
    markers = []  # (pos, body)  body=='Council' for reconvene-to-council
    for mm in RE_CONVENE_AS.finditer(text):
        markers.append((mm.start(), _phrase_to_body(mm.group(1))))
    for mm in RE_RECONVENE_COUNCIL.finditer(text):
        markers.append((mm.start(), "Council"))
    if not markers:
        return [(0, len(text), "Council")]
    markers.sort()
    spans = []
    cur_body = "Council"
    cur_start = 0
    for pos, body in markers:
        if body != cur_body:
            spans.append((cur_start, pos, cur_body))
            cur_start = pos
            cur_body = body
    spans.append((cur_start, len(text), cur_body))
    return spans


def body_at(spans, char_pos):
    for s, e, b in spans:
        if s <= char_pos < e:
            return b
    return "Council"


VOTE_NORM = {
    "yes": "Aye", "aye": "Aye",
    "no": "Nay", "nay": "Nay",
    "abstain": "Abstain", "abstained": "Abstain",
    "absent": "Absent", "excused": "Absent",
    "recuse": "Recuse", "recused": "Recuse",
    # "N/A" in a roll call = member sat out due to a declared conflict of
    # interest -> treated as Recuse (distinct from Nay and from Absent).
    "n/a": "Recuse", "n\\a": "Recuse",
    "conflict": "Recuse", "conflicted": "Recuse",
}


# First-name (uniqueness) gate — latent hardening; a PURE NO-OP for WVC today.
# ---------------------------------------------------------------------------
# Roll-call lines name voters by LAST name only, so surname->full resolution is
# the sole attribution path.  Every WVC council surname is unique across
# 2020-2026, so each surname maps to exactly ONE full (first+last) name and the
# gate below always passes -> byte-identical output.  It exists so that if a
# future roster ever REUSED a surname across eras (the "Deborah vs Lisa Jensen"
# collision that bit other cities), surname resolution would REFUSE (return
# None -> keep the printed name) instead of silently attributing every roll-call
# "Jensen" to whichever full name happened to sit in the dict.  We never guess.
SURNAME_TO_FULLS = {}
for _last, _full in LASTNAME_TO_FULL.items():
    SURNAME_TO_FULLS.setdefault(_last, set()).add(_full)


def canon_last(token):
    t = token.strip().strip(".,").lower()
    t = LASTNAME_ALIASES.get(t, t)
    # exact surname match, gated on a UNIQUE full-name resolution (first-name
    # gate): resolve only when the surname maps to exactly one full name.
    fulls = SURNAME_TO_FULLS.get(t)
    if fulls is not None:
        return next(iter(fulls)) if len(fulls) == 1 else None
    # OCR truncation/typo: unique prefix match against the known roster
    # (e.g. "Christense" -> "christensen").  Require >=5 chars to avoid
    # spurious matches.  (Already gated: resolves only on a single candidate.)
    if len(t) >= 5:
        cands = [full for last, full in LASTNAME_TO_FULL.items()
                 if last.startswith(t) or t.startswith(last)]
        if len(set(cands)) == 1:
            return cands[0]
    return None


def normalize_full(name):
    """Normalize a captured first+last (or multi-word) name for mover/seconder."""
    if not name:
        return ""
    n = " ".join(name.split())
    key = n.lower()
    if key in FIRSTLAST_NORMALIZE:
        return FIRSTLAST_NORMALIZE[key]
    # If it's a single token, treat as last name and expand
    parts = n.split()
    if len(parts) == 1:
        full = canon_last(parts[0])
        return full or n
    # multi-word: try last token as a known last name to canonicalize spelling
    full = canon_last(parts[-1])
    if full:
        return full
    return n


# ---------------------------------------------------------------------------
# Motion-type classification (fixed 12-category taxonomy)
# ---------------------------------------------------------------------------
def classify(motion_text, context):
    """context = the ~600 chars of agenda heading preceding the motion."""
    t = (motion_text + " " + context).lower()
    mt = motion_text.lower()

    # adjournment / minutes approval / procedural
    if re.search(r"\b(adjourn|recess|reconvene)\b", mt):
        return "Procedural/Administrative"
    if "minutes of" in mt and "approve" in mt:
        return "Procedural/Administrative"
    if re.search(r"\b(open|close|continue)\b.*public hearing", mt) or \
       re.search(r"public hearing", mt) and re.search(r"\b(open|close)\b", mt):
        return "Public Hearing Action"

    # appointment / election to a body or office
    if re.search(r"\b(appoint|elect|nominate|reappoint)\b", mt) or \
       re.search(r"mayor pro tem", mt):
        return "Appointment"

    # land use / zoning
    if re.search(r"\b(zone change|zoning|rezone|subdivision|plat|conditional use|"
                 r"general plan|land use|annex|vacate|right[\s-]?of[\s-]?way|"
                 r"development agreement|preliminary|final plat)\b", t):
        return "Land-Use/Zoning"

    # budget amendment
    if re.search(r"budget amendment|amend.*budget|appropriat", t):
        return "Budget Amendment"

    # grant funding
    if re.search(r"\bgrant\b", t):
        return "Grant-Funding"

    # interlocal
    if re.search(r"interlocal|cooperation agreement|inter[\s-]?local", t):
        return "Interlocal"

    # contract / purchase / procurement / bid / award
    if re.search(r"\b(contract|purchase|procure|procurement|bid|award|agreement to|"
                 r"professional services|lease|warranty deed|quit claim)\b", t):
        return "Contract/Purchase"

    # ordinance vs resolution (by what the motion approves)
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"

    # ceremonial
    if re.search(r"proclaim|proclamation|recognition|honor|commend", t):
        return "Ceremonial"

    return "Other"


# ---------------------------------------------------------------------------
# Per-meeting extraction
# ---------------------------------------------------------------------------
def parse_rollcall_block(lines, start_idx):
    """Starting just after 'A roll call vote was taken', collect member/vote lines.
    Returns (votes_dict, result_str, end_idx). votes_dict maps canonical name->vote.
    Stops at the result word (Unanimous/Majority/...) or a blank gap / non-matching
    run after we've started collecting."""
    members = {}
    unknown = []
    result = ""
    i = start_idx
    n = len(lines)
    collected = False
    blanks = 0
    while i < n:
        line = lines[i]
        m = RE_ROLLCALL_LINE.match(line)
        if m:
            last = m.group(2)
            vote_raw = m.group(3).lower()
            full = canon_last(last)
            vote = VOTE_NORM.get(vote_raw, vote_raw.capitalize())
            if full:
                members[full] = vote
            else:
                unknown.append((last, vote))
            collected = True
            blanks = 0
            i += 1
            continue
        rw = RE_RESULT_WORD.match(line)
        if rw and collected:
            result = rw.group(1).strip().rstrip(".")
            i += 1
            break
        if line.strip() == "":
            blanks += 1
            if collected and blanks >= 4:
                break
            i += 1
            continue
        # page-break / footer noise (header line, page number) — skip and keep
        # collecting; a roll-call list often straddles a page boundary.
        if RE_NOISE.match(line):
            i += 1
            continue
        # a non-blank, non-matching, non-noise line
        if collected:
            break
        # not collecting yet; allow page-break/header noise for a few lines
        if i - start_idx > 10:
            break
        i += 1
    return members, unknown, result, i


def tally_string(members, result):
    ayes = sum(1 for v in members.values() if v == "Aye")
    nays = sum(1 for v in members.values() if v == "Nay")
    abst = sum(1 for v in members.values() if v == "Abstain")
    base = f"{ayes}-{nays}"
    if abst:
        base += f"-{abst}A"
    outcome = result
    # derive pass/fail if result word present
    rl = result.lower()
    if "fail" in rl:
        passfail = "Fail"
    elif rl in ("unanimous", "majority", "carried", "passed") or "pass" in rl or "carr" in rl:
        passfail = "Pass"
    elif ayes > nays:
        passfail = "Pass"
    elif nays >= ayes and (ayes or nays):
        passfail = "Fail"
    else:
        passfail = ""
    parts = [base]
    if outcome:
        parts.append(outcome)
    if passfail and passfail.lower() not in rl:
        parts.append(passfail)
    return " ".join(parts).strip()


def extract_meeting(path, rel_source, date, title):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    n = len(lines)
    votes = []
    motion_no = 0

    # Governing-body resolution: meeting-level default (separate agency meeting?)
    # plus any in-council "convened as the … board" brackets.
    default_body = body_for_title(title)
    body_spans = build_body_spans(text, default_body)

    # Find each "moved to" statement and process it as a motion candidate.
    for m in RE_MOVED.finditer(text):
        mover_raw = m.group(1)
        verb_and_rest = m.group(2)
        mover = normalize_full(mover_raw)
        if not mover or mover_raw.strip().lower() in ("pro", "pro tem"):
            mover = normalize_full(mover_raw)

        # Build motion text: "<verb> <rest>" cleaned up
        motion_text = ("to " + verb_and_rest).strip()
        motion_text = re.sub(r"\s+", " ", motion_text)
        # truncate very long motion text at the first period-ish boundary already done by regex
        if len(motion_text) > 400:
            motion_text = motion_text[:400].rsplit(" ", 1)[0] + "…"

        # Skip pure adjournment "all voted in favor to adjourn" handled below;
        # but "moved to adjourn" with no roll call -> still a procedural motion.
        start_char = m.end()
        # window after the motion to look for second + roll call (next ~2500 chars)
        window = text[m.start(): m.start() + 3000]

        # seconder
        sm = RE_SECOND.search(window)
        seconder = normalize_full(sm.group(1)) if sm else ""

        # context heading: ~600 chars BEFORE the motion (agenda item title)
        context = text[max(0, m.start() - 700): m.start()]

        # Determine vote type: roll call vs voice vote, whichever comes first
        rc = RE_RESULT_WORD  # noqa
        roll_pos = None
        rm = RE_ROLLCALL_START.search(window)
        vm = RE_VOICE.search(window)
        # find char index of next motion to bound the window (avoid stealing next motion's vote)
        next_moved = RE_MOVED.search(text, m.end())
        bound = next_moved.start() if next_moved else len(text)

        members = {}
        unknown = []
        result = ""
        names_recorded = False

        if rm and (m.start() + rm.start()) < bound:
            # roll call within this motion's span
            rc_line_idx = text[:m.start() + rm.start()].count("\n")
            members, unknown, result, _ = parse_rollcall_block(lines, rc_line_idx + 1)
            if members or unknown:
                names_recorded = True
        if not names_recorded:
            # voice vote / tally only
            if vm and (m.start() + vm.start()) < bound:
                # "voice vote was taken and all members voted in favor"
                seg = window[vm.start(): vm.start() + 200].lower()
                if "favor" in seg:
                    result = "Voice vote - all in favor"
                else:
                    result = "Voice vote"
            else:
                # look for a nearby tally word
                seg = window[:1200]
                rwm = re.search(r"(Unanimous|Majority|motion (?:carried|failed|passed)|all voted in favor|all members voted in favor)",
                                seg, re.IGNORECASE)
                if rwm and (m.start() + rwm.start()) < bound:
                    result = rwm.group(1)
                else:
                    # no recorded vote outcome found near this motion -> skip
                    # (e.g. a motion that was superseded by a substitute motion)
                    continue

        motion_no += 1
        mt = classify(motion_text, context)

        aye = sorted([k for k, v in members.items() if v == "Aye"])
        nay = sorted([k for k, v in members.items() if v == "Nay"])
        abstain = sorted([k for k, v in members.items() if v == "Abstain"])
        absent = sorted([k for k, v in members.items() if v == "Absent"])
        recuse = sorted([k for k, v in members.items() if v == "Recuse"])

        if names_recorded:
            result_str = tally_string(members, result)
        else:
            result_str = result

        vote_rec = {
            "motion_no": motion_no,
            "motion": motion_text,
            "body": body_at(body_spans, m.start()),
            "motion_type": mt,
            "result": result_str,
            "mover": mover,
            "seconder": seconder,
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
        }
        if unknown:
            vote_rec["_unknown_rollcall"] = unknown
        votes.append(vote_rec)

    return {
        "date": date,
        "title": title,
        "body": default_body,  # meeting-level default body (Council unless the
                               # meeting itself is a separate RDA/MBA/CRA meeting)
        "source": rel_source,
        "votes": votes,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)
    processed = 0
    all_csv_rows = []
    val_lines = []
    stats = dict(meetings=0, motions=0, member_rows=0, named=0, tally=0,
                 contested=0, mismatches=0, unparsed=[])
    roster_years = {}
    by_body = {}              # body -> motion count
    contested_by_body = {}    # body -> contested motion count
    members_by_body = {}      # body -> set of voter names (validation)

    for row in rows:
        path = os.path.join(REPO, row["path"])
        if not os.path.exists(path):
            stats["unparsed"].append(row["path"] + " (missing file)")
            continue
        rel_source = row["path"].replace("meeting_minutes/", "", 1)
        year = row["year"]
        # week folder from path
        parts = row["path"].split("/")
        week = parts[-2]
        slug = os.path.splitext(parts[-1])[0]
        out_dir = os.path.join(VOTES_DIR, year, week)
        out_json = os.path.join(out_dir, parts[-1].replace(".md", ".json"))

        try:
            meeting = extract_meeting(path, rel_source, row["date"], row["title"])
        except Exception as e:
            stats["unparsed"].append(row["path"] + f" (parse error: {e})")
            continue

        os.makedirs(out_dir, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting, f, indent=1, ensure_ascii=False)
        processed += 1
        stats["meetings"] += 1

        # roster tracking (from named roll calls)
        for v in meeting["votes"]:
            for grp in ("aye", "nay", "abstain", "absent", "recuse"):
                for name in v[grp]:
                    roster_years.setdefault(year, set()).add(name)

        for v in meeting["votes"]:
            stats["motions"] += 1
            if v["names_recorded"]:
                stats["named"] += 1
            else:
                stats["tally"] += 1
            mbody = v.get("body", "Council")
            by_body[mbody] = by_body.get(mbody, 0) + 1
            for grp in ("aye", "nay", "abstain", "absent", "recuse"):
                for name in v[grp]:
                    members_by_body.setdefault(mbody, set()).add(name)
            contested = bool(v["nay"] or v["abstain"] or v["recuse"])
            if contested:
                stats["contested"] += 1
                contested_by_body[mbody] = contested_by_body.get(mbody, 0) + 1

            # validation: tally consistency
            if v["names_recorded"]:
                ayes = len(v["aye"]); nays = len(v["nay"])
                res = v["result"].lower()
                if "unanimous" in res and nays > 0:
                    stats["mismatches"] += 1
                    val_lines.append(f"{row['date']} {row['title']} motion {v['motion_no']}: "
                                     f"SOURCE DISCREPANCY — minutes printed 'Unanimous.' but the "
                                     f"per-member roll call shows {nays} Nay vote(s). The roll call "
                                     f"governs (result: {v['result']}). Verified clerical error in the "
                                     f"official minutes; per-member data retained.")
                if "majority" in res and nays == 0 and ayes > 0:
                    stats["mismatches"] += 1
                    val_lines.append(f"{row['date']} {row['title']} motion {v['motion_no']}: "
                                     f"result says Majority but no Nay recorded: {v['result']}")
                if "fail" in res and ayes > nays:
                    stats["mismatches"] += 1
                    val_lines.append(f"{row['date']} {row['title']} motion {v['motion_no']}: "
                                     f"result says Fail but ayes>nays: {v['result']}")
                if "_unknown_rollcall" in v:
                    val_lines.append(f"{row['date']} {row['title']} motion {v['motion_no']}: "
                                     f"unrecognized roll-call name(s): {v['_unknown_rollcall']}")

            # CSV rows
            base = dict(date=row["date"], year=row["year"], title=row["title"],
                        body=v.get("body", "Council"),
                        motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v["mover"], seconder=v["seconder"],
                        source=rel_source)
            if v["names_recorded"]:
                for grp, vote_label in (("aye", "Aye"), ("nay", "Nay"),
                                        ("abstain", "Abstain"), ("absent", "Absent"),
                                        ("recuse", "Recuse")):
                    for member in v[grp]:
                        r = dict(base); r["member"] = member; r["vote"] = vote_label
                        all_csv_rows.append(r); stats["member_rows"] += 1
            else:
                # tally-only: one summary row, member + vote blank
                r = dict(base); r["member"] = ""; r["vote"] = ""
                all_csv_rows.append(r)

    # write all_votes.csv
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    with open(ALL_VOTES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_csv_rows:
            w.writerow(r)

    # validation report
    with open(VALIDATION, "w", encoding="utf-8") as f:
        f.write("West Valley City — vote extraction validation report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Meetings processed : {stats['meetings']}\n")
        f.write(f"Motions extracted  : {stats['motions']}\n")
        f.write(f"Member-vote rows   : {stats['member_rows']}\n")
        f.write(f"Named roll-calls   : {stats['named']}\n")
        f.write(f"Tally-only motions : {stats['tally']}\n")
        f.write(f"Contested motions  : {stats['contested']}\n")
        f.write(f"Validation issues  : {len(val_lines)}\n\n")
        f.write("Motions by body:\n")
        for b in sorted(by_body):
            f.write(f"  {b:8s}: {by_body[b]} motions "
                    f"({contested_by_body.get(b, 0)} contested)\n")
        f.write("\nDistinct voters by body (must be a subset of the council "
                "roster — no new members in agency capacity):\n")
        council_voters = members_by_body.get("Council", set())
        for b in sorted(members_by_body):
            extra = members_by_body[b] - council_voters if b != "Council" else set()
            f.write(f"  {b:8s}: {sorted(members_by_body[b])}\n")
            if extra:
                f.write(f"           !! NOT in council roster: {sorted(extra)}\n")
        f.write("\n")
        if stats["unparsed"]:
            f.write("Unparsed / missing meetings:\n")
            for u in stats["unparsed"]:
                f.write("  - " + u + "\n")
            f.write("\n")
        f.write("Issues:\n")
        for l in val_lines:
            f.write("  - " + l + "\n")

    rj = {y: sorted(s) for y, s in sorted(roster_years.items())}
    print(json.dumps({
        "meetings_processed": stats["meetings"],
        "motions_extracted": stats["motions"],
        "member_vote_rows": stats["member_rows"],
        "named_rollcall_motions": stats["named"],
        "tally_only_motions": stats["tally"],
        "contested_motions": stats["contested"],
        "motions_by_body": by_body,
        "contested_by_body": contested_by_body,
        "agency_members_match_council": all(
            (members_by_body.get(b, set()) - members_by_body.get("Council", set())) == set()
            for b in members_by_body if b != "Council"),
        "validation_mismatches": stats["mismatches"],
        "validation_issues_logged": len(val_lines),
        "unparsed_meetings": stats["unparsed"],
        "roster_years": {y: len(v) for y, v in rj.items()},
    }, indent=2))
    # dump roster detail to a sidecar for the CLAUDE.md / inspection
    with open(os.path.join(VOTES_DIR, "_roster_by_year.json"), "w") as f:
        json.dump(rj, f, indent=2)


if __name__ == "__main__":
    main()
