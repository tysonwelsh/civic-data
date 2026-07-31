#!/usr/bin/env python3
"""Town of Alta vote extractor (PURE deterministic — no LLM, no network).

Parameterized by body (council | pc). Reads the minutes markdown under
<body>/minutes/<year>/<week>/, parses every recorded motion, normalizes member
names against a roster map BUILT FROM THE CORPUS ITSELF (role-prefixed full names),
and emits one JSON per meeting + <body>/all_votes.csv (13-col standard).

THE MAYOR VOTES in Alta (Utah Town form): the Mayor (Roger Bourke throughout
2020->2026) is an ordinary voting member; a full roll call tops out at 5
(Mayor + 4 at-large councilmembers). No mayor tie-break special-casing.

Motion anchor: the clerk's uppercase "MOTION:" / "MOTION AMENDED:" label (case-
SENSITIVE, colon required) — narrative "the motion passed" (lowercase) is never a
motion. Every recorded Alta motion carries this label.

Alta vote grammar (all handled):
  * Unanimous tally-only (NO names -> names_recorded False, one placeholder row):
      "VOTE: All in favor." / "unanimously approved/adopted" / "was adjourned".
  * NAMED, several equivalent forms:
      1. Per-member roll call: "ROLL CALL VOTE [BY JEN CLANCY]: Councilmember Byrne -
         yes, ... Mayor Bourke - yes" (role prefix optional; bare "John Byrne - yes"
         also occurs). Clerk token 'I' is a checkmark = AYE (confirmed by trailing
         "Against: no votes / All in favor").
      2. In-favor / against lists: "VOTE: In favor: Bourke, Davis, Byrne, Morgan and
         Anctil. None opposed." / "In favor: no votes. Against: ... The motion failed."
      3. Narrative dissent: "Carolyn Anctil voted nay." (ayes unnamed -> names_recorded
         False for the majority; the dissent is captured).
  * "RESULT: APPROVED/DENIED" line (newer docs) captured verbatim.
  * 2021 narrative grammar (T3.1(a) fixes, 2026-07-12):
      - narrative vote EVENTS anchor the operative segment: "A [voice] vote on/to ...
        was taken", "called the question" (bare = event; CAPS "CALLED the Question
        on <target>" at line start = its own parliamentary motion row);
      - named lists "X, Y, and Z voted/voting "Aye."/"Nay."" (quoted or bare);
      - a two-column "Ayes / Nays" name grid (2021-07-14);
      - "(No vote was taken...)" / "not voted ... at this time" windows emit
        RECORDED (no vote line), never a fabricated APPROVED;
      - outcome is WORD-PRIORITY: an explicit "carried/passed/failed/did not pass"
        sentence wins over name-bucket heuristics.
Names captured AS PRINTED, normalized to canonical "First Last"; the printed roll
call is authoritative (roster turns over across the span). Names resolve PER FILE
first (PRESENT block / role-prefixed full names in that meeting's minutes), then
against the corpus roster — the Bourke seat is held by DIFFERENT people across the
span (Roger Bourke council 2020, Margaret Bourke council 2021, Roger Bourke mayor
2022+) and Mayor Sondak (2020-21) must never resolve to Mayor Bourke (2022+).
"""
import csv, json, os, re, sys
from pathlib import Path

TAG = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("council", "pc") else "council"
FORCE = "--force" in sys.argv
ROOT = Path("/Users/tysonwelsh/civic-data/alta_city_council")
DIR = ROOT / ("meeting_minutes" if TAG == "council" else "planning_commission")
BODY = "Council" if TAG == "council" else "PlanningCommission"
MINUTES_DIR = DIR / "minutes"
VOTES_DIR = DIR / "votes"
INDEX = DIR / "minutes_index.csv"
ALL_VOTES = DIR / "all_votes.csv"

VOTE_MAP = {
    "yes": "aye", "aye": "aye", "y": "aye", "i": "aye",
    "no": "nay", "nay": "nay", "n": "nay",
    "abstain": "abstain", "abstained": "abstain", "abstention": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse", "recusal": "recuse",
}
VOTE_LABEL = {"aye": "Aye", "nay": "Nay", "abstain": "Abstain",
              "absent": "Absent", "recuse": "Recuse"}
DASH = r"[‐-―\-~]"   # incl. OCR tilde ("Schilling ~ yes", 2025-09-10)
ROLE = (r"(?:Planning\s*Commission\s*members?|Council\s*members?|Coun[a-z]{1,4}members?|"
        r"Board\s*members?|Commission\s*members?|Commissioners?|"
        r"Chair(?:man|person|woman)?|Mr\.?|Ms\.?|Mrs\.?|Dr\.?|Mayor\s*Pro\s*Tem(?:pore)?|Mayor)")
STOP = {"the", "pro", "tem", "tempore", "by", "jen", "clancy", "on", "amendment",
        "and", "council", "member", "members", "mayor", "commissioner", "commission",
        "chair", "chairman", "chairperson", "planning", "meeting", "motion", "town",
        "vote", "roll", "call", "of", "a", "mr", "ms", "mrs", "dr",
        # vote-context filler that can land in a name slot — never a member:
        "all", "none", "majority", "everyone", "nobody", "unanimous", "unanimously",
        "favor", "opposed", "against", "item", "items", "staff", "financial", "report",
        "reports", "consent", "agenda", "ordinance", "resolution", "budget", "minutes",
        "no", "votes", "in", "aye", "nay", "yes", "councilmember", "councilmembers",
        # pronouns / auxiliaries that land in a name slot after a sentence boundary
        # ("... Contract. He moved to ..." must never mint a person):
        "he", "she", "they", "it", "was", "were", "there", "this", "that", "who"}

# ---------------------------------------------------------------------------
# Roster map, built from the corpus (role-prefixed "First Last")
# ---------------------------------------------------------------------------
FULLNAME_RE = re.compile(
    r"(?:Planning\s*Commission\s*[Mm]ember|Council\s*[Mm]ember|Coun[a-z]{1,4}member|"
    r"Commission\s*[Mm]ember|Commissioner|Chair(?:man|person|woman)?|"
    r"Mayor\s*Pro\s*Tem(?:pore)?)\s+"
    r"([A-Z][a-z]+)\s+([A-Z][a-z]+)\b")
# acting-member full names harvested from mover/seconder narrative (both bodies)
NARR_FULLNAME_RE = re.compile(
    r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+(?:motioned|moved|seconded|made a motion)\b")
MAYOR_ONE_RE = re.compile(r"\bMayor\s+(?!Pro\b|Roger\b)([A-Z][a-z]{2,})\b")
MAYOR_TWO_RE = re.compile(r"\bMayor\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)\b")

ROSTER = {}          # surname(lower) -> "First Last"
FIRST_NAMES = {}     # first(lower) -> "First Last"  (mover/first-name fallback)
MAYOR_SURNAME = None
MAYOR_FULL = None

def build_roster(md_files):
    global ROSTER, FIRST_NAMES, MAYOR_SURNAME, MAYOR_FULL
    freq = {}
    mayor_one = {}
    mayor_two_full = {}   # "First Last" (from "Mayor First Last") -> count, keyed by surname
    for p in md_files:
        txt = p.read_text(encoding="utf-8", errors="replace")
        for m in list(FULLNAME_RE.finditer(txt)) + list(NARR_FULLNAME_RE.finditer(txt)):
            first, last = m.group(1), m.group(2)
            if first.lower() in STOP or last.lower() in STOP:
                continue
            freq[(last.lower(), f"{first} {last}")] = freq.get((last.lower(), f"{first} {last}"), 0) + 1
        for m in MAYOR_ONE_RE.finditer(txt):
            s = m.group(1).lower()
            if s not in STOP:
                mayor_one[s] = mayor_one.get(s, 0) + 1
        for m in MAYOR_TWO_RE.finditer(txt):
            first, last = m.group(1), m.group(2)
            if first.lower() in STOP or last.lower() in STOP:
                continue
            mayor_two_full[(last.lower(), f"{first} {last}")] = \
                mayor_two_full.get((last.lower(), f"{first} {last}"), 0) + 1
    best = {}
    for (key, full), c in freq.items():
        if key not in best or c > best[key][1]:
            best[key] = (full, c)
    ROSTER = {k: v[0] for k, v in best.items()}
    # single most-frequent mayor surname (from "Mayor <Surname>" one-token form)
    if mayor_one:
        MAYOR_SURNAME = max(mayor_one, key=mayor_one.get)
    elif mayor_two_full:
        MAYOR_SURNAME = max(mayor_two_full, key=mayor_two_full.get)[0]
    if MAYOR_SURNAME:
        # canonical mayor full name: prefer the "Mayor First Last" spelling, NOT a
        # role-prefixed councilmember spelling (which can be a same-surname resident).
        cands = {full: c for (key, full), c in mayor_two_full.items() if key == MAYOR_SURNAME}
        if cands:
            MAYOR_FULL = max(cands, key=cands.get)
        else:
            MAYOR_FULL = ROSTER.get(MAYOR_SURNAME, MAYOR_SURNAME.capitalize())
        ROSTER[MAYOR_SURNAME] = MAYOR_FULL   # bourke -> Roger Bourke (mayor wins)
    for surname, full in ROSTER.items():
        parts = full.split()
        if len(parts) == 2:
            FIRST_NAMES.setdefault(parts[0].lower(), full)


# per-FILE name resolution (set before parsing each meeting): the Bourke seat is
# held by different people across the span and the mayor turns over, so the names
# printed IN THIS FILE (PRESENT block, role-prefixed full names) beat the corpus
# roster. LOCAL["roster"]: surname -> "First Last"; LOCAL["mayor_*"]: this file's mayor.
LOCAL = {"roster": {}, "mayor_surname": None, "mayor_full": None}

def set_local_roster(txt):
    LOCAL["roster"] = {}
    LOCAL["mayor_surname"] = LOCAL["mayor_full"] = None
    freq = {}
    for m in list(FULLNAME_RE.finditer(txt)) + list(NARR_FULLNAME_RE.finditer(txt)):
        first, last = m.group(1), m.group(2)
        if first.lower() in STOP or last.lower() in STOP:
            continue
        freq[(last.lower(), f"{first} {last}")] = freq.get((last.lower(), f"{first} {last}"), 0) + 1
    best = {}
    for (key, full), c in freq.items():
        if key not in best or c > best[key][1]:
            best[key] = (full, c)
    LOCAL["roster"] = {k: v[0] for k, v in best.items()}
    mayor2 = {}
    for m in MAYOR_TWO_RE.finditer(txt):
        first, last = m.group(1), m.group(2)
        if first.lower() in STOP or last.lower() in STOP:
            continue
        mayor2[(last.lower(), f"{first} {last}")] = mayor2.get((last.lower(), f"{first} {last}"), 0) + 1
    if mayor2:
        (LOCAL["mayor_surname"], LOCAL["mayor_full"]) = max(mayor2, key=mayor2.get)
        LOCAL["roster"].setdefault(LOCAL["mayor_surname"], LOCAL["mayor_full"])


def _lookup(surname):
    loc, glob = LOCAL["roster"].get(surname), ROSTER.get(surname)
    if loc and glob and loc != glob:
        # same surname, different first name: a DIFFERENT PERSON (Margaret vs Roger
        # Bourke -> trust this file) unless the first names share a >=3-char prefix
        # (Dave/David Abraham -> a nickname variant; keep the corpus canonical form).
        lf, gf = loc.split()[0].lower(), glob.split()[0].lower()
        n = 0
        for a, b in zip(lf, gf):
            if a != b:
                break
            n += 1
        return glob if n >= 3 else loc
    return loc or glob


def canon(name_phrase):
    """Resolve a printed name phrase -> (canonical 'First Last', is_mayor)."""
    phrase = name_phrase.strip()
    is_mayor = bool(re.match(r"\s*(?:the\s+)?Mayor(?!\s*Pro)", phrase, re.I))
    core = re.sub(ROLE, " ", phrase, flags=re.I)
    toks = [t.rstrip(".") for t in re.findall(r"[A-Za-z][A-Za-z.'-]+", core)]
    toks = [t for t in toks if t and t.lower() not in STOP]
    surname = toks[-1].lower() if toks else None
    # this FILE's mayor beats the corpus-modal mayor (Bourke is a councilmember
    # surname in 2020-21 under Mayor Sondak)
    if surname and surname == (LOCAL["mayor_surname"] or MAYOR_SURNAME):
        is_mayor = True
    if is_mayor:
        # a SURNAMED mayor phrase resolves by that surname (Mayor Sondak 2020-21
        # must not resolve to the corpus-modal Mayor Bourke); bare "the Mayor"
        # falls back to this file's mayor, then the corpus mayor.
        if surname:
            full = _lookup(surname)
            if full:
                return full, True
            if surname == LOCAL["mayor_surname"]:
                return LOCAL["mayor_full"], True
            if surname == MAYOR_SURNAME and MAYOR_FULL:
                return MAYOR_FULL, True
            return surname.capitalize(), True
        return (LOCAL["mayor_full"] or MAYOR_FULL), True
    if not surname:
        return None, False
    full = _lookup(surname)
    if full is None and surname in FIRST_NAMES:
        full = FIRST_NAMES[surname]      # first name printed where surname expected
    if full is None:
        full = " ".join(w.capitalize() for w in toks[-2:]) if len(toks) >= 2 else toks[-1].capitalize()
    return full, False

# ---------------------------------------------------------------------------
# Motion-type taxonomy (city-native)
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|conditional use|land use|land-use|"
                 r"general plan|subdivision|\bplat\b|site plan|setback|variance|lot line|"
                 r"annex|development agreement|overlay|master plan", t):
        return "Land-Use/Zoning"
    if re.search(r"consent agenda|approve.*minutes|meeting minutes|financial report|staff report", t):
        return "Consent/Minutes"
    if re.search(r"budget|appropriat|tax rate|property tax|transient room tax|fee schedule|"
                 r"certified tax|water rate|sewer rate", t):
        return "Budget/Finance"
    if re.search(r"appoint|reappoint|mayor pro tem|liaison|nominate|ratif|canvass|vacancy|"
                 r"swearing|treasurer", t):
        return "Appointment"
    if re.search(r"interlocal|inter-local|cooperation agreement|mutual aid", t):
        return "Interlocal"
    if re.search(r"\bcontract\b|purchase|procure|\baward\b|professional services|agreement with|"
                 r"\blease\b|grant application|\bgrant\b|\bbid\b|memorandum of understanding|\bmou\b", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b|\b\d{4}-o-\d", t):
        return "Ordinance"
    if re.search(r"\bresolution\b|\b\d{4}-r-\d", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed|executive session|agenda|"
                 r"\btable\b|continue|postpone|excuse|to order", t):
        return "Procedural/Administrative"
    return "Other"

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
NAMECAP = (r"((?:the\s+)?(?:Mayor(?:\s+Pro\s+Tem(?:pore)?)?\s+)?"
           r"(?:Planning\s*Commission\s*[Mm]ember\s+|Council\s*[Mm]ember\s+|"
           r"Coun[a-z]{1,4}member\s+|Commission\s*[Mm]ember\s+|Commissioner\s+|"
           r"Chair(?:man|person|woman)?\s+|Mr\.?\s+|Ms\.?\s+|Mrs\.?\s+)?"
           r"[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){0,2})")
MOTION_VERB = (r"(?:motioned|moved|makes? a motion|made a motion|introduced? a motion|"
               r"offered a motion|put (?:forth|forward) a motion|presented a motion)")
# case-SENSITIVE (council); the clerk sometimes numbers the label into a
# parliamentary sequence: "3. (A continuance of #2) MOTION: ..." (2021-06-16).
MOTION_ANCHOR = re.compile(
    r"^\s*(?:\d{1,2}\.\s*)?(?:\([^)]{0,60}\)\s*)?MOTION(?:\s+AMENDED)?\s*[:;]")
# a CAPS "CALLED the Question on <target>" at line start is its own parliamentary
# motion (the vote it carries is a real, separately-recorded decision: 2021-06-16 #3,
# 2021-09-08 item 12, 2021-06-16 R-10). Lowercase / bare "called the question" is
# only a vote EVENT (see EVENT_RE), never a motion row.
CQ_ANCHOR = re.compile(
    r"^\s*(?:\d{1,2}\.\s*)?(?:\([^)]{0,60}\)\s*)?(?:MOTION\s*[:;]\s*)?"
    r"[A-Z][^.!?\n]{0,60}?CALLED\s+the\s+Question\s+on\b")
# narrative motion (PC + some council): "<Name> moved/motioned/made a motion to <action>"
NARR_MOTION = re.compile(
    NAMECAP + r"\s+" + MOTION_VERB + r"\s+to\s+"
    r"(?:approve|adopt|deny|recommend|accept|grant|authoriz|appoint|adjourn|table|"
    r"continue|amend|reconsider|forward|ratif|nominate|open|close|direct|send|"
    r"recess|convene|reconvene|enter|go into|hold|schedule|set|postpone|strike|"
    r"add|remove|change|modify|revise|update|refer)", re.I)
ITEM_RE = re.compile(r"^\s*\d{1,2}\.\s+(.*)")
MOVER_RE = re.compile(NAMECAP + r"\s+" + MOTION_VERB + r"\b", re.I)
CLAUSE_RE = re.compile(MOTION_VERB + r"\s+to\s+(.+)", re.I)
SECOND_RE = re.compile(NAMECAP + r"\s+seconded", re.I)
BAD_HEADING = re.compile(r"\bcall\b|to order|adjourn|recess|questions regarding|"
                         r"mayor'?s report|report\s*$|public comment|introduction", re.I)
VOTE_KEYWORD_RE = re.compile(
    r"ROLL\s*CALL\s*VOTE[^:;]{0,40}[:;]|(?<![A-Za-z])VOTE\b[^:;.]{0,40}[:;]", re.I)
# vote EVENTS = the explicit labels above (incl. qualified "VOTE on the amended
# motion:") + the 2021 narrative event phrases; the operative segment is anchored
# on these (see parse_meeting seg selection).
EVENT_RE = re.compile(
    r"ROLL\s*CALL\s*VOTE[^:;]{0,40}[:;]|(?<![A-Za-z])VOTE\b[^:;.]{0,40}[:;]|"
    r"\bA\s+(?:voice\s+|roll\s*call\s+)?vote\b[^.]{0,80}?\bwas\s+taken|"
    r"\bcalled?\s+the\s+question\b", re.I)
# "(No vote was taken [at that time])" / "not voted on at this time" — the motion was
# deferred/restated; the window must NOT fabricate an APPROVED from the default path.
NOT_VOTED_RE = re.compile(
    r"no vote was taken|not voted\s+(?:up)?on\s+(?:at th(?:is|at) time|until)|was not voted",
    re.I)
RESULT_RE = re.compile(r"^[\s.\-|:]*RESULT\s*[:;]?\s*([A-Za-z ]+)")
MEMBER_TOKEN_RE = re.compile(
    r"([A-Za-z.'][A-Za-z.'\- ]{1,40}?)\s*" + DASH +
    # tolerate a stray OCR / table-artifact glyph (. | ! , ; : _ · *) between the dash
    # and a LINE-WRAPPED vote token: the clerk's roll wraps a member mid-token
    # ("Councilmember Byrne — .\nyes" / "Mayor Bourke — |\nyes" / "Morgan — !\nyes"),
    # which collapses to "... — . yes" in the joined blob. Without this the member is
    # silently DROPPED and the derived N-0 tally understated (audit 2026-07-12,
    # fixed 2026-07-19). The class excludes letters, so it never crosses into the next
    # name; the vote word still anchors the match.
    r"[\s.|!,;:_·*]*(yes|aye|no|nay|abstain(?:ed)?|abstention|absent|excused|recuse[d]?|recusal|i)\b",
    re.I)
INFAVOR_RE = re.compile(r"\bin favor\s*:\s*(.+?)(?:$|\.(?:\s|$))", re.I)
AGAINST_RE = re.compile(r"\b(?:against|opposed)\s*:\s*(.+?)(?:$|\.(?:\s|$))", re.I)
# a comma/and-joined list of CAPITALIZED names only (won't cross lowercase filler
# like "voted I in favor of the ordinance" — so aye and nay lists stay separate).
# Each list element may carry an OPTIONAL role prefix: without it, the plural-role
# FULL-NAME form "Mayor Sondak and Council Members Elise Morgan and Cliff Curry
# voted "Aye."" (2020-06-17, PMN-promoted) exceeds the 3-token name cap, breaking
# the chain and silently DROPPING the leading Mayor's vote. canon() strips the
# role words, so the prefix never lands in a person name. (2026-07-16 fix.)
_ROLEPFX = (r"(?:(?:the\s+)?Mayor(?:\s+Pro\s+Tem(?:pore)?)?\s+|Council\s*Members?\s+|"
            r"Planning\s*Commission\s*Members?\s+|Commission\s*Members?\s+|Commissioners?\s+)?")
_NAME = _ROLEPFX + r"[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+){0,2}"   # no '.': a name list must not cross a sentence boundary ("Anctil. None opposed")
# separators: ", " / ", and " / " and " uniformly — a bare "and" may appear
# mid-list before a final ", and" ("Morgan and Curry, and Mayor Sondak", 2021-05-12)
NAMELIST = (r"(" + _NAME + r"(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+)" + _NAME + r")*)")
# narrative named lists: "<names> voted [I/aye/yes] in favor" AND the 2021 quoted
# forms "<names> voted/voting "Aye."" / ""Nay."" (curly or straight quotes, bare ok)
NARR_AYE_RE = re.compile(
    NAMELIST + r"\s+vot(?:ed|ing)\s+(?:[“\"']?(?:I\b|[Aa]ye|[Yy]es)[.,”\"']*(?:\s+in\s+favor)?"
    r"|in\s+favor)")
NARR_NAY_RE = re.compile(
    NAMELIST + r"(?:\s+vot(?:ed|ing)\s+[“\"']?(?:[Nn]ay|[Nn]o(?![a-z])|[Aa]gainst|in opposition)"
    r"|(?<!None)(?<!none)\s+opposed\b(?!\s+to\b))")
NARR_ABSTAIN_RE = re.compile(NAMELIST + r"\s+(?:abstain(?:ed|ing)?|abstention)", re.I)
NARR_ABSENT_RE = re.compile(NAMELIST + r"\s+(?:was|were)\s+(?:absent|excused)", re.I)
# outcome clause tied to the thing decided (last match near the operative vote wins)
OUTCOME_RE = re.compile(
    r"(?:motion|amendment|resolution|ordinance|request|application|item|minutes|"
    r"consent agenda|variance|permit|appointment|plan|budget|proposal)s?\b[^.]{0,70}?"
    r"\b((?:not|did not|does not|was not|were not)\s+(?:adopt|approv|pass|carri)\w*|"
    r"pass(?:ed|es)?|carri(?:ed|es)|approve[ds]?|adopt(?:ed|s)?|grant(?:ed|s)?|"
    r"fail(?:ed|s)?|denie[ds]|defeat(?:ed)?|was lost|tabled|withdrawn)", re.I)
OUTCOME_FAIL = re.compile(r"fail|denied|defeat|\bnot\b|does not|did not|lost|withdraw|tabl", re.I)
# a bare-infinitive outcome word is a motion CLAUSE, not a result ("CALLED the
# Question on the original motion to approve Resolution 2021-R-10" is not a Pass)
_BARE_INF = {"approve", "pass", "adopt", "grant", "fail"}

def outcome_clauses(text, pos=0, endpos=None):
    return [o for o in OUTCOME_RE.finditer(text, pos, len(text) if endpos is None else endpos)
            if o.group(1).lower().strip() not in _BARE_INF]

def parse_column_grid(raw_lines):
    """Two-column 'Ayes / Nays' surname grid (2021-07-14). Column membership is by
    character offset against the header's 'Nays' position. Returns (ayes, nays) or None."""
    for wi, wl in enumerate(raw_lines):
        if not re.match(r"^\s*Ayes(?:\s{2,}Nays)?\s*$", wl):
            continue
        nay_col = wl.find("Nays")
        ayes, nays = [], []
        for nl in raw_lines[wi + 1:]:
            s = nl.strip()
            if not s or re.search(r"\bmotion\b|\bvote\b", s, re.I) or \
                    not re.match(r"^[A-Z][A-Za-z.'\- ]*$", s):
                break
            for nm in re.finditer(r"[A-Z][A-Za-z.'-]+(?: [A-Z][A-Za-z.'-]+)?", nl):
                (nays if (nay_col >= 0 and nm.start() >= nay_col - 3) else ayes).append(nm.group(0))
        if ayes or nays:
            return ayes, nays
    return None


def split_names(s):
    s = re.sub(r"\bnone\b|no votes?|\bnobody\b", " ", s, flags=re.I)
    out = []
    for p in re.split(r",|\band\b|;", s):
        p = p.strip(" .")
        if not p:
            continue
        full, is_m = canon(p)
        if full:
            out.append((full, is_m))
    return out

# ---------------------------------------------------------------------------
# Line loading / footer stripping
# ---------------------------------------------------------------------------
TS_RE = re.compile(r"^\s*\d{1,2}:\d{2}:\d{2}\s*$")
FOOTER_RE = re.compile(r"^\s*(?:Alta\s+Town\s+Council|Alta\s+Planning\s+Commission|"
                       r"Town\s+of\s+Alta|Alta\s+Council\s+Meeting|Planning\s+Commission)"
                       r"(?:\s+Meeting)?\s*$", re.I)
DATE_FOOTER_RE = re.compile(
    r"^\s*[-|.\s]*(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s+\d{4}[-|.\s\d]*$", re.I)
PAGENUM_RE = re.compile(r"^\s*[-|.\s]*\d{1,3}[-|.\s]*$")

def load_lines(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        text = text.split("---", 2)[-1]
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if TS_RE.match(s) or FOOTER_RE.match(s) or DATE_FOOTER_RE.match(s) or PAGENUM_RE.match(s):
            continue
        out.append(ln)
    return out

# ---------------------------------------------------------------------------
# Parse one meeting
# ---------------------------------------------------------------------------
def parse_meeting(lines):
    n = len(lines)
    # motion anchors: the uppercase "MOTION:" label (council) OR a narrative motion
    # ("<Name> moved/motioned to <action>", PC + some council). Merge anchors closer
    # than 3 lines (a label + its own narrative verb wrapping) so each motion counts once.
    # narrative motions can wrap a line break ("Mr. Niermeyer introduced\n a motion to
    # approve ...") — probe each line joined with the next.
    narr = [i for i in range(n)
            if NARR_MOTION.search(lines[i] + " " + (lines[i + 1] if i + 1 < n else ""))]
    cq = [i for i, ln in enumerate(lines) if CQ_ANCHOR.match(ln)]
    raw = sorted(set([i for i, ln in enumerate(lines) if MOTION_ANCHOR.match(ln)] + narr + cq))
    motion_idx = []
    for i in raw:
        if motion_idx and i - motion_idx[-1] < 3:
            continue
        motion_idx.append(i)
    next_boundary = {}
    for idx, i in enumerate(motion_idx):
        next_boundary[i] = motion_idx[idx + 1] if idx + 1 < len(motion_idx) else n

    votes = []
    for mno, i in enumerate(motion_idx, 1):
        boundary = next_boundary[i]
        # nearest agenda item heading above (for rich motion text; join continuations)
        last_item = None
        for k in range(i, max(-1, i - 30), -1):
            im = ITEM_RE.match(lines[k])
            if im and len(im.group(1).strip()) > 8:
                parts = [im.group(1).strip()]
                for kk in range(k + 1, min(k + 4, i)):
                    s = lines[kk].strip()
                    letters = re.sub(r"[^A-Za-z]", "", s)
                    if not s or TS_RE.match(s) or ITEM_RE.match(lines[kk]) or \
                       MOTION_ANCHOR.match(lines[kk]) or not letters or not letters.isupper():
                        break
                    parts.append(s)
                last_item = re.sub(r"\s+", " ", " ".join(parts)).strip()
                break
        # motion sentence: from the anchor line up to 'seconded' / vote / boundary
        mtxt = [MOTION_ANCHOR.sub("", lines[i]).strip()]
        j = i + 1
        while j < boundary and j < i + 8:
            lj = lines[j]
            if VOTE_KEYWORD_RE.search(lj) or RESULT_RE.match(lj):
                break
            mtxt.append(lj.strip())
            if re.search(r"seconded", lj, re.I):
                j += 1; break
            j += 1
        motion_blob = re.sub(r"\s+", " ", " ".join(mtxt)).strip(" .;,")

        def known_member(full):
            # movers/seconders must resolve to a harvested person — otherwise a
            # sentence fragment ("Contract. He") mints a phantom db person.
            if not full:
                return None
            parts = full.split()
            if parts[-1].lower() in ROSTER or parts[-1].lower() in LOCAL["roster"] \
                    or parts[0].lower() in FIRST_NAMES or full in (MAYOR_FULL, LOCAL["mayor_full"]):
                return full
            return None

        mover = seconder = None
        mv = MOVER_RE.search(motion_blob)
        if mv and mv.group(1).strip():
            f, _ = canon(mv.group(1))
            mover = known_member(f)
        sc = SECOND_RE.search(motion_blob)
        if sc:
            f, _ = canon(sc.group(1))
            seconder = known_member(f)

        clause = None
        cm = CLAUSE_RE.search(motion_blob)
        if cm:
            clause = re.split(r"\.\s|\bseconded\b", cm.group(1))[0].strip(" .;,|")
        heading_ok = (last_item and len(last_item) > 20 and not BAD_HEADING.search(last_item)
                      and re.search(r"adopt|approv|resolution|ordinance|appoint|authoriz|accept|"
                                    r"action|amend|consider|contract|budget|plan|recommend|"
                                    r"variance|public hearing|consent|agreement|purchase", last_item, re.I))
        if CQ_ANCHOR.match(lines[i]):
            # a called-question motion IS its own row; its text is the CQ sentence
            # (never the agenda heading — that names the underlying item, and never
            # the following roll-call narrative).
            motion_text = re.split(r"(?<=[.?!])\s+", motion_blob, 1)[0]
        elif clause and re.search(r"adjourn|recess|to order|closed session", clause, re.I):
            motion_text = clause
        elif heading_ok:
            motion_text = last_item
        else:
            motion_text = clause or motion_blob
        motion_text = re.sub(r"\s+", " ", motion_text).strip(" .;,|")[:600]

        # ---- vote: scan the whole motion span (anchor..next motion, cap 45 lines) ----
        wend = min(boundary, i + 45)
        rawwin = lines[i:wend]                       # unstripped (column-grid offsets)
        window = [x.strip() for x in rawwin]
        wblob = re.sub(r"\s+", " ", " ".join(window)).strip()
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        names_recorded = False
        outcome = "Pass"
        mayor_in = False
        result_str = None

        # explicit RESULT: line (newer council docs) — normalize to a controlled keyword
        # (OCR trails punctuation/stray letters after the word).
        for k in range(i, wend):
            rm = RESULT_RE.match(lines[k])
            if rm:
                rr = rm.group(1).strip().upper()
                if "APPROV" in rr or "ADOPT" in rr or "PASS" in rr or "CARRI" in rr or "GRANT" in rr:
                    result_str = "APPROVED"
                elif "DEN" in rr or "FAIL" in rr or "DEFEAT" in rr:
                    result_str = "DENIED"
                elif "ADJOURN" in rr:
                    result_str = "ADJOURNED"
                elif "CONTINU" in rr or "TABL" in rr:
                    result_str = "CONTINUED"
                elif "WITHDR" in rr:
                    result_str = "WITHDRAWN"
                else:
                    result_str = rr.split()[0] if rr.split() else None
                break

        # did a vote/decision actually occur in this span?
        voted = bool(re.search(
            r"ROLL\s*CALL|VOTE\b|in favor|\bunanimous|none opposed|voted\s+(?:nay|no|aye|yes|i\b)|"
            # "consent of the Council/commission" is a vote phrase ("[unanimous]
            # consent of the Council") — but "advice and consent of the council"
            # (appointment-power boilerplate) and "written consent of the other
            # party" (contract text) are NOT votes (2026-07-16 fix: the promoted
            # 2020-06-17 R-12 original motion was getting a fabricated APPROVED).
            r"(?<!advice and )(?<!written )consent of the|"
            r"the motion (?:was )?(?:passed|carried|failed|denied|approved|adopted)|"
            r"motion (?:passed|carried|failed|denied)|was (?:approved|adopted|carried|denied|"
            r"passed|adjourned)|were approved|passed unanimous", wblob, re.I)) or result_str is not None
        # "(No vote was taken at that time)" windows: unless a real vote event or an
        # outcome sentence FOLLOWS the marker, nothing was decided here — the motion
        # was deferred/restated (its vote lives on a later row). Never fabricate.
        nv = NOT_VOTED_RE.search(wblob)
        if voted and nv and result_str is None and not EVENT_RE.search(wblob, nv.end()) \
                and not outcome_clauses(wblob, nv.end()):
            voted = False

        if voted:
            # ---- operative-vote SEGMENT selection (2021 narrative grammar aware) ----
            # Vote EVENTS = explicit labels (ROLL CALL VOTE:, VOTE:) + narrative
            # phrases ("A [voice] vote ... was taken", "called the question").
            #   * an outcome sentence BETWEEN the motion sentence and the first event
            #     means the motion resolved in narrative BEFORE the event (the event
            #     belongs to other business in the span) -> segment ends at the event;
            #   * an "AMENDMENT VOTE:"-labelled event -> the LAST plain event is the
            #     main vote (documented amendment-then-main design, 2022-10-12);
            #   * otherwise the FIRST event (collapsing a run of adjacent events),
            #     ending at the NEXT event so a later re-vote of a different motion
            #     in the same span can't bleed in (2021-05-12 amendment-then-main).
            sec_m = re.search(r"seconded", wblob, re.I)
            msent_end = sec_m.end() if sec_m else 0
            events = list(EVENT_RE.finditer(wblob))
            seg_start, seg_end = msent_end, len(wblob)
            if events:
                amend = [e for e in events
                         if "AMENDMENT" in wblob[max(0, e.start() - 12):e.start()].upper()
                         or "AMENDMENT" in e.group(0).upper()]
                plain = [e for e in events if e not in amend]
                if outcome_clauses(wblob, msent_end, events[0].start()):
                    seg_end = events[0].start()
                elif amend and plain:
                    seg_start = plain[-1].end()
                else:
                    evs = plain or amend
                    k = 0
                    while k + 1 < len(evs) and evs[k + 1].start() - evs[k].end() < 60:
                        k += 1
                    seg_start = evs[k].end()
                    if k + 1 < len(evs):
                        seg_end = evs[k + 1].start()
            seg = wblob[seg_start:seg_end][:700]
            cut = re.search(r"\s\d{1,2}\.\s+[A-Z]", seg)   # next numbered agenda item
            if cut:
                seg = seg[:cut.start()]

            # outcome from the last RESULT clause in the segment (bare-infinitive
            # motion clauses excluded). WORD-PRIORITY: an explicit carriage word is
            # authoritative; name-bucket heuristics below never override it.
            outcome_word = None
            oms = outcome_clauses(seg)
            if oms:
                outcome_word = "Fail" if OUTCOME_FAIL.search(oms[-1].group(1)) else "Pass"
            if outcome_word == "Fail":
                outcome = "Fail"

            pairs = []
            for tm in MEMBER_TOKEN_RE.finditer(seg):
                full, is_m = canon(tm.group(1))
                bucket = VOTE_MAP.get(tm.group(2).lower())
                if full and bucket:
                    pairs.append((full, bucket, is_m))
            if len(pairs) >= 2:
                seen = set()
                for full, bucket, is_m in pairs:
                    if full in seen:
                        continue
                    seen.add(full)
                    buckets[bucket].append(full)
                    if is_m:
                        mayor_in = True
                names_recorded = True
            else:
                infm = INFAVOR_RE.search(seg)
                agm = AGAINST_RE.search(seg)
                aye_names = list(split_names(infm.group(1))) if infm else []
                nay_names = list(split_names(agm.group(1))) if agm else []
                for nm in NARR_AYE_RE.finditer(seg):
                    aye_names += split_names(nm.group(1))
                for nm in NARR_NAY_RE.finditer(seg):
                    nay_names += split_names(nm.group(1))
                nay_set = {x for x, _ in nay_names}
                for full, is_m in aye_names:
                    if full not in buckets["aye"] and full not in nay_set:
                        buckets["aye"].append(full); mayor_in |= is_m
                for full, is_m in nay_names:
                    if full not in buckets["nay"] and full not in buckets["aye"]:
                        buckets["nay"].append(full); mayor_in |= is_m
                # narrative abstain/absent ("Council Member Morgan abstaining from the vote")
                for nm in NARR_ABSTAIN_RE.finditer(seg):
                    for full, is_m in split_names(nm.group(1)):
                        if full not in buckets["abstain"] and full not in buckets["aye"] + buckets["nay"]:
                            buckets["abstain"].append(full); mayor_in |= is_m
                for nm in NARR_ABSENT_RE.finditer(seg):
                    for full, is_m in split_names(nm.group(1)):
                        if full not in buckets["absent"] and full not in \
                                buckets["aye"] + buckets["nay"] + buckets["abstain"]:
                            buckets["absent"].append(full)
                if not (buckets["aye"] or buckets["nay"]):
                    g = parse_column_grid(rawwin)      # "Ayes / Nays" name grid (2021-07-14)
                    if g:
                        for nm in g[0]:
                            full, is_m = canon(nm)
                            if full and full not in buckets["aye"]:
                                buckets["aye"].append(full); mayor_in |= is_m
                        for nm in g[1]:
                            full, is_m = canon(nm)
                            if full and full not in buckets["aye"] + buckets["nay"]:
                                buckets["nay"].append(full); mayor_in |= is_m
                if buckets["aye"] or buckets["nay"]:
                    names_recorded = True
                    # heuristic only when no explicit carriage word exists (word-priority)
                    if outcome_word is None and not buckets["aye"] and buckets["nay"] \
                            and not re.search(r"none opposed|no votes?\s+against", seg, re.I):
                        outcome = "Fail"

            if result_str is None:
                motion_is_adjourn = bool(re.search(r"adjourn|recess|to order", motion_text, re.I))
                if outcome == "Fail":
                    result_str = "FAILED"
                elif motion_is_adjourn and re.search(r"adjourn", wblob, re.I) and not names_recorded:
                    result_str = "ADJOURNED"
                else:
                    result_str = "APPROVED"
            elif result_str in ("DENIED", "FAILED", "DEFEATED"):
                outcome = "Fail"
        else:
            result_str = "RECORDED (no vote line)"

        n_aye, n_nay = len(buckets["aye"]), len(buckets["nay"])
        result_final = f"{result_str} ({n_aye}-{n_nay})" if names_recorded else result_str

        votes.append({
            "body": BODY, "motion_no": mno, "motion": motion_text,
            "motion_type": classify_motion(motion_text), "result": result_final,
            "mover": mover, "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
            "absent": buckets["absent"], "recuse": buckets["recuse"],
            "names_recorded": names_recorded, "mayor_voted": mayor_in,
        })
    return votes

# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    md_files = sorted(MINUTES_DIR.rglob("*.md"))
    build_roster(md_files)
    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    for r in rows:
        path = DIR / r["path"]
        if not path.exists():
            print("MISSING", r["path"], file=sys.stderr); continue
        week = Path(r["path"]).parent.name
        year = r["year"]
        slug = Path(r["path"]).stem
        out_dir = VOTES_DIR / year / week
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not FORCE:
            skipped += 1; continue
        out_dir.mkdir(parents=True, exist_ok=True)
        set_local_roster(path.read_text(encoding="utf-8", errors="replace"))
        votes = parse_meeting(load_lines(path))
        payload = {"date": r["date"], "year": int(year), "title": r["title"],
                   "source": r["path"], "votes": votes}
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"[{TAG}] processed {processed} (skipped {skipped}); "
          f"roster={len(ROSTER)} mayor={MAYOR_FULL!r}")
    build_all_votes()

def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            if jp.name.startswith("_"):
                continue
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key in ("aye", "nay", "abstain", "absent", "recuse"):
                    for mbr in v.get(key, []):
                        w.writerow(base + [mbr, VOTE_LABEL[key], data["source"]])
                        n += 1; emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n += 1
    print(f"[{TAG}] wrote {ALL_VOTES} ({n} rows)")

if __name__ == "__main__":
    main()
