#!/usr/bin/env python3
"""
Nephi City PLANNING COMMISSION vote extractor.

Reads the ~70 planning-commission minutes markdown files under
planning_commission/minutes/<year>/<week-monday>/ (indexed by
planning_commission/minutes_index.csv), parses every recorded motion, and emits:
  - one JSON per meeting under planning_commission/votes/<year>/<week>/<date>_*.json
    (resumable; skip existing unless --force)
  - planning_commission/all_votes.csv  (long format; body="PlanningCommission",
    title="Planning Commission" on every row; EXACT 13-col council schema:
      date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source)
  - planning_commission/roster.csv (commissioner,first_seen,last_seen,n_meetings)

TWO MINUTE FORMATS
------------------
A) NARRATIVE (the 2020-2021 + many later files):
     "<Name> moved/motioned to <action>. <Name> seconded. The motion passed
      on a unanimous vote."  (mover may instead trail: "Motion was made to <..>
      by <Name>" / "on a motion by <Name> and a second by <Name>").
B) STRUCTURED (2022-2023, some 2024+):
     A section heading / "Motion: To <action>" action item, then a vote line
       "Motion: <Mover>  Second: <Seconder>  [Opposed: <Names>]  [Outcome: <text>]"
     Outcome / "Roll Call- Name: Yea, ..." may sit on the next line(s).

Most votes are UNANIMOUS narrative/tally-only -> names_recorded=false, ONE summary
row carrying mover+seconder+result. We NEVER guess who voted which way from a
"unanimous" result. Per-member rows are only emitted when the minutes name voters
(a "Roll Call-" line, an "Opposed:" name, or an inline named dissent).

RECOMMENDATION vs FINAL ACTION (encoded in `result`; see CLAUDE.md)
------------------------------------------------------------------
PC FORWARDS recommendations to the City Council on rezones/zone changes/plats/
subdivisions/annexations/general-plan/ordinance & code amendments, OR whenever the
motion text says "recommend"/"forward to Council":
    -> "Positive recommendation"  / "Negative recommendation"  (+ " N:N" iff a
       tally/roll-call is recorded).
PC takes FINAL ACTION on conditional-use permits, home-occupation permits/licenses,
site plans, business licenses, sign permits, lot-line/boundary adjustments:
    -> "Approved (Final Action)" / "Denied (Final Action)"  (with "N:N " PREFIX iff
       a tally is recorded, per spec: "N:N Approved (Final Action)").
Procedural (minutes/agenda/adjourn/prayer/elect officers/table/postpone/continue/
schedule public hearing):
    -> "Pass" / "Fail"  (with "N:N " prefix iff a tally is recorded).
If NO tally is given (the overwhelming majority), the number is omitted entirely --
we never invent counts. A "(unanimous)" suffix is added when the minutes say so; a
named dissent is appended as " (<Name> opposed)".
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Page-footer stripping (running footer bleeds into captured motion text)
# ---------------------------------------------------------------------------
# The PDF minutes carry a two-line running footer at every page break: a lone
# centered page-number line, then "Nephi City Planning Commission   <Month D, YYYY>".
# When a motion's action prose straddles a page break the footer text bled into the
# captured `motion` string (e.g. "...it's subsequent 4 Nephi City Planning Commissi").
# Removing the two footer lines rejoins the prose across the break; all 176 running-
# footer lines in the corpus are preceded by a lone page-number line (verified), so
# this strips ONLY footer text and never a real motion sentence. (Mirrors the SSL
# FOOTER_RE approach used in the sibling extractors.)
FOOTER_RE = re.compile(
    r"^[ \t]*\d{1,3}[ \t]*\r?\n"                       # lone centered page-number line
    r"[ \t]*Nephi City Planning Commission[ \t]{2,}"   # running footer label
    r"[A-Z][a-z]+ \d{1,2},? \d{4}[ \t]*\r?\n?",        # trailing meeting date
    re.M)


def strip_footers(text):
    """Remove the two-line running page footer wherever it appears, rejoining the
    prose that straddled the page break. Leaves the leading newline of the preceding
    prose line intact, so line structure elsewhere is unchanged."""
    return FOOTER_RE.sub("", text)


ROOT = Path(__file__).resolve().parent
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"
REPO_ROOT = ROOT.parent

# ---------------------------------------------------------------------------
# People / name normalization (commissioners + alternates only)
# ---------------------------------------------------------------------------
FIRST_CANON = {
    "glenn": "Glenn Greenhalgh", "brent": "Brent Arns", "karl": "Karl Brough",
    "cory": "Cory Thomson", "kent": "Kent Heap", "ann": "Ann Peterson",
    "alan": "Alan Hancock", "heather": "Heather Robertson", "fran": "Fran Petersen",
    "john": "John Ford", "terry": "Terry Cook", "jim": "Jim Nelson",
    "meadow": "Meadow Perides",
}
LAST_CANON = {
    "greenhalgh": "Glenn Greenhalgh", "arns": "Brent Arns", "brough": "Karl Brough",
    "thomson": "Cory Thomson", "thompson": "Cory Thomson", "heap": "Kent Heap",
    "hancock": "Alan Hancock", "robertson": "Heather Robertson",
    "roberson": "Heather Robertson", "roberston": "Heather Robertson",
    "ford": "John Ford", "cook": "Terry Cook",
    "nelson": "Jim Nelson", "perides": "Meadow Perides",
}
# Peterson/Petersen surname is shared by Ann Peterson and Fran Petersen -> needs a
# first name (or tenure) to disambiguate; never guessed otherwise.
PETERSON_SET = {"peterson", "petersen"}

CANON_FIRSTNAME = {full: full.split()[0].lower() for full in set(FIRST_CANON.values())}

ROLE_WORDS = (
    r"Commissioners?|Chair(?:man|woman|person)?|Vice[-\s]?Chair(?:man|woman|person)?|"
    r"Alternate|Acting|Interim|Newly\s+appointed|City\s+Council\s+Member|"
    r"Council\s+Member|Mr\.|Ms\.|Mrs\.|Dr\."
)
ROLE_STRIP_RE = re.compile(rf"^(?:{ROLE_WORDS})\s+", re.I)


def _clean_name(raw):
    s = raw.strip()
    s = re.sub(r"\([^)]*\)", " ", s)          # drop parentheticals "(Chair)" etc.
    s = re.sub(r"[’‘`]", "'", s)
    s = s.strip("*").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip(".,;:()-").strip()
    prev = None
    while prev != s:
        prev = s
        s = ROLE_STRIP_RE.sub("", s).strip()
    return s


def normalize_name(raw, date=None, present=None):
    """Canonical commissioner full name, or None if not a recognizable commissioner.

    `present` (optional) is the set of canonical commissioners seated at this meeting, used
    to resolve a bare 'Peterson'/'Petersen' surname when only ONE of Ann Peterson / Fran
    Petersen is in attendance (header-based, not a guess)."""
    if not raw:
        return None
    s = _clean_name(raw)
    if not s:
        return None
    toks = [t for t in re.split(r"\s+", s) if t]
    toks = [t for t in toks if re.match(r"[A-Za-z]", t)]
    if not toks:
        return None
    low = [t.lower().strip(".,;:'") for t in toks]

    # Peterson/Petersen handling (Ann vs Fran)
    if any(t in PETERSON_SET for t in low):
        if "ann" in low:
            return "Ann Peterson"
        if "fran" in low:
            return "Fran Petersen"
        # bare surname -> resolve from attendance if exactly one Peterson(en) is seated
        if present:
            seated = [n for n in ("Ann Peterson", "Fran Petersen") if n in present]
            if len(seated) == 1:
                return seated[0]
        # else tenure: only Ann before Fran joined (late 2021)
        if date and date < "2021-10-01":
            return "Ann Peterson"
        return None  # ambiguous -> never guess

    if len(low) == 1:
        t = low[0]
        if t in FIRST_CANON:
            return FIRST_CANON[t]
        if t in LAST_CANON:
            return LAST_CANON[t]
        return None

    # multi-token: trust the last token's surname, but verify the first token is
    # consistent (guards against e.g. "Lisa Brough" -> NOT Karl Brough).
    last = low[-1]
    first = low[0]
    cand = LAST_CANON.get(last)
    if cand:
        cf = cand.split()[0].lower()
        if first == cf or len(first) <= 2 or first not in FIRST_CANON and first not in LAST_CANON:
            # consistent first name, an initial, or an unknown middle token
            if first in FIRST_CANON and FIRST_CANON[first] != cand:
                return None  # first name names a different commissioner
            return cand
        return None
    # last token unknown -> try first token as a first name
    if first in FIRST_CANON:
        return FIRST_CANON[first]
    return None


# ---------------------------------------------------------------------------
# Motion-type taxonomy (reuse the council 12-category classifier)
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"budget amendment|amend(?:ed|ing)? (?:the )?budget|budget adjustment", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t):
        return "Grant-Funding"
    if re.search(r"\bappoint\b|appointment|elect(?:ed|ion)?\s+(?:a\s+)?(?:chair|vice)|"
                 r"nominat|\bappointed\b|fill the (?:commission )?vacancy", t):
        return "Appointment"
    if re.search(r"\bplat\b|subdivision|rezone|re-zone|zoning|zone change|zone map|annex|"
                 r"annexation|conditional use|\bcup\b|home occupation|land use|general plan|"
                 r"master plan|preliminary plat|final plat|amended plat|lot line|site plan|"
                 r"boundary adjustment|setback|variance", t):
        return "Land-Use/Zoning"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|professional services|"
                 r"agreement with|lease|easement|\bbid\b", t):
        return "Contract/Purchase"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing|open the (?:public )?hearing|close the (?:public )?hearing|"
                 r"continue the public hearing|schedule.*hearing|call.*hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|\bminutes\b|approve the agenda|"
                 r"amend the agenda|\btable\b|postpone|continue|prayer|"
                 r"business license|sign permit", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Disposition: recommendation vs final action vs procedural -> result string
# ---------------------------------------------------------------------------
PROCEDURAL_RE = re.compile(
    r"\b(minutes|agenda|adjourn|recess|prayer|elect|nominat|chair(?:man|woman|person)?|"
    r"vice[-\s]?chair|\btable\b|postpone|continue|excuse|schedule.*hearing|"
    r"set.*hearing|call.*for.*hearing|open the .*hearing|close the .*hearing|"
    r"welcome|approve the order)\b", re.I)
RECOMMEND_RE = re.compile(
    r"\brecommend|\bforward(?:ed|ing)?\b.*council|to the council|city council approval", re.I)
TOCOUNCIL_CAT_RE = re.compile(
    r"\bplat\b|subdivision|\brezone\b|re-zone|zone change|zone map|\bzoning\b|annex|"
    r"annexation|general plan|master plan|\bordinance\b|code (?:change|amendment|revision)|"
    r"amend.*code|land use code", re.I)
FINAL_CAT_RE = re.compile(
    r"conditional use|\bcup\b|home occupation|site plan|business license|sign permit|"
    r"\bsign\b|lot line|boundary adjustment|home-based business", re.I)
DENY_RE = re.compile(r"\bden(?:y|ied|ial)\b|\breject|disapprove|\bdo not approve\b|not approve", re.I)


def build_result(motion_text, outcome_pass, aye_n=None, nay_n=None, unanimous=False,
                 dissent_names=None):
    t = motion_text.lower()
    denial_intent = bool(DENY_RE.search(t))
    effective_positive = denial_intent is False
    if not outcome_pass:
        effective_positive = not effective_positive  # a failed motion flips the disposition

    tally = None
    if aye_n is not None and nay_n is not None:
        tally = f"{aye_n}:{nay_n}"

    procedural = bool(PROCEDURAL_RE.search(t)) and not RECOMMEND_RE.search(t)
    is_reco = bool(RECOMMEND_RE.search(t)) or (not procedural and bool(TOCOUNCIL_CAT_RE.search(t)))
    is_final = (not procedural and not is_reco) and bool(FINAL_CAT_RE.search(t))

    if is_reco:
        head = "Positive recommendation" if effective_positive else "Negative recommendation"
        res = f"{head} {tally}" if tally else head
        cls = "recommendation"
    elif is_final:
        disp = "Approved (Final Action)" if effective_positive else "Denied (Final Action)"
        res = f"{tally} {disp}" if tally else disp
        cls = "final_action"
    else:
        disp = "Pass" if outcome_pass else "Fail"
        res = f"{tally} {disp}" if tally else disp
        cls = "procedural"

    if unanimous and not tally:
        res += " (unanimous)"
    if dissent_names:
        res += f" ({', '.join(dissent_names)} opposed)"
    return res, cls


# ---------------------------------------------------------------------------
# Roster: per-meeting attendance of canonical commissioners
# ---------------------------------------------------------------------------
def header_region(text):
    """Region of the file holding the attendance / opening roster."""
    cut = len(text)
    for marker in (r"\bPRAYER\b", r"\bWelcome to the Planning", r"\n1\.\s",
                   r"called the (?:meeting|hearing|regular)", r"opened the (?:meeting|hearing)"):
        m = re.search(marker, text, re.I)
        if m:
            cut = min(cut, m.end() + 80)
    return text[:max(cut, 500)]


ATTEND_BLOCK_RE = re.compile(
    r"(?:Commissioners?|Attendance|Attendees|In attendance|Present)\s*:(.+?)"
    r"(?:\n\s*\n|\nStaff|\nPublic|\nGuests|\nScribe|\nRecorder|\nExcused|\nPRAYER|\Z)",
    re.S | re.I)


def detect_attendance(text, date):
    """Set of canonical commissioners marked present at this meeting.

    Scans the FULL document, not just the opening header: early (2020-2021) and
    public-hearing minutes place the attendance roster at the BOTTOM (either a
    two-column "Name, Planning Commission Member" list or a bare-name list under an
    "Attendance:" label, often mixed with members of the public). normalize_name
    restricts every match to the 13 canonical commissioners, so staff/public/council
    names are dropped.
    """
    present = set()
    region = text

    # 1) Excused/absent block -> exclude those explicitly
    excused = set()
    for em in re.finditer(r"Excused\s*:([^\n]*(?:\n(?![A-Z][a-z]+:)[^\n]*)?)", region, re.I):
        for nm in re.split(r",|;|\band\b", em.group(1)):
            c = normalize_name(nm, date)
            if c:
                excused.add(c)

    # 2) Labeled "Commissioners:/Attendees:/Present:" lists
    cand = []
    for bm in ATTEND_BLOCK_RE.finditer(region):
        cand.append(bm.group(1))
    # 3) two-column 2020 style: "Name, Planning Commission Member" / ", Chairman"
    for rm in re.finditer(
            r"^([A-Z][A-Za-z.'\- ]+?),\s*(?:Alt\.?\s*)?(?:Chair(?:man|woman|person)?\b|"
            r"(?:Alt\.?\s*)?Planning Commission|Commission Member)", region, re.M):
        cand.append(rm.group(1))
    # 4) inline "Commissioner <Name>" / "Chairman <Name>" anywhere in header region
    for rm in re.finditer(
            r"(?:Commissioner|Chair(?:man|woman|person)?|Alternate Commissioner)\s+"
            r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2})", region):
        cand.append(rm.group(1))

    for chunk in cand:
        # split a chunk into individual names on commas / semicolons / "and" / newlines
        for piece in re.split(r",|;|\n|\band\b|\bExcused\b|\bStaff\b|\bPublic\b|\bScribe\b|"
                              r"\bRecorder\b", chunk):
            c = normalize_name(piece, date)
            if c:
                present.add(c)

    present -= excused
    return present


# ---------------------------------------------------------------------------
# Vote parsing
# ---------------------------------------------------------------------------
NAME = r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2}"
ROLE_OPT = (r"(?:Commissioner|Chair(?:man|woman|person)?|Vice[-\s]?Chair|"
            r"Alternate(?:\s+Commissioner)?|Acting\s+Chair(?:man|woman)?|Mr\.|Ms\.|Mrs\.)?\s*")

# Structured vote anchors. Every structured motion (2022-2026) carries a "Second:" label,
# so we anchor on it and read the controlling "Motion:"/"Made by:" label + "Outcome:".
SECOND_LABEL_RE = re.compile(r"\bSecond(?:ed)?\s*:", re.I)
MOTION_LABEL_RE = re.compile(r"\b(?:Motion|Mad[ey] by)\s*:\s*", re.I)
MOTION_VERB_RE = re.compile(
    r"\b(?:motions?|moves?|moved|motioned|mad[ey]\s+(?:a|the)\s+motion|"
    r"makes?\s+(?:a|the)\s+motion|nominate[sd]?|"
    r"accepts?|accepted|approves?|approved|approval|recommends?|recommended|"
    r"denies|denied|calls?\s+for)\b", re.I)
OUTCOME_FAIL_RE = re.compile(
    r"\b(?:fail(?:ed|s)?|defeat(?:ed)?|did\s+not\s+(?:pass|carry)|"
    r"does\s+not\s+(?:pass|carry)|withdraw\w*|no\s+action|tabled|postpone\w*)\b", re.I)

# narrative result clause
NARR_RESULT_RE = re.compile(
    r"(?:[Tt]he\s+)?motion\s+(?P<verb>passed|carried|failed|died)\b", re.I)

ROLLCALL_RE = re.compile(r"Roll\s*Call\s*[-:–]?\s*(?P<body>.+)$", re.I | re.M)
VOTE_WORD = {"yea": "aye", "yes": "aye", "aye": "aye", "for": "aye", "in favor": "aye",
             "nay": "nay", "nae": "nay", "no": "nay", "against": "nay", "opposed": "nay",
             "abstain": "abstain", "abstained": "abstain", "abstaining": "abstain",
             "recuse": "recuse", "recused": "recuse", "absent": "absent",
             "excused": "absent"}

UNANIM_RE = re.compile(r"unanim", re.I)


def parse_rollcall(s, date, present=None):
    """Parse a named roll call into buckets. Handles BOTH orderings seen in the minutes:
      form 1 (Name: Vote): "Roll Call- Hancock: Nay, Thomson: Yea, Fran: Yea, Ford: Yea"
      form 2 (Vote, Name):  "Nay, Commissioner Cory Thomson. Yea, Commissioner Heather
                             Robertson, Commissioner Fran Petersen, ..."
    Returns empty buckets when no Yea/Nay tokens are present (the usual case)."""
    buckets = {"aye": [], "nay": [], "abstain": [], "recuse": [], "absent": []}
    if not s:
        return buckets
    # form 1: Name <sep> Vote   (sep is ':' or '-'/'–'; e.g. "Hancock: Aye", "Cory – NAY")
    found = False
    for nm, vt in re.findall(
            r"([A-Za-z.'’ ]+?)\s*[:\-–]\s*"
            r"(Yea|Yes|Aye|Nay|Nae|No|Abstain(?:ed)?|Recuse[d]?|Absent|Excused)\b",
            s, re.I):
        c = normalize_name(nm, date, present)
        b = VOTE_WORD.get(vt.lower().strip())
        if c and b and c not in buckets[b]:
            buckets[b].append(c)
            found = True
    if found:
        return buckets
    # form 2: Vote, Name, Name. Vote, Name ...
    # Stop the scan at the first outcome DECLARATION ("Motion Passes" / "Motion is
    # approved" ...): real vote lists always precede it, while the prose after it can
    # re-mention a commissioner ("Motion Passes, Chairman Ann Peterson will serve for
    # the 2024 year") -- reading a vote out of that prose fabricated a duplicate
    # Ann Peterson=Absent row on 2024-01-10. Roll calls written inside the Outcome
    # block ("Outcome: Nay, X. Yea, Y, ... Motion is approved.", 2024-12-11) end
    # before the declaration too, so they are preserved.
    s = re.split(r"\bMotion\s+(?:is\s+|was\s+)?"
                 r"(?:approved|passes|passed|carried|carries|denied|failed|fails)\b",
                 s, flags=re.I)[0]
    parts = re.split(r"\b(Yea|Yes|Aye|Nay|Nae|No|Abstain\w*|Recused?|Absent|Excused)\b",
                     s, flags=re.I)
    cur = None
    for i, tok in enumerate(parts):
        if i % 2 == 1:
            cur = VOTE_WORD.get(tok.lower())
        elif cur:
            for c in _split_name_list(tok, date, present):
                if c not in buckets[cur]:
                    buckets[cur].append(c)
    return buckets


def _split_name_list(s, date, present=None):
    out = []
    for piece in re.split(r",|;|&|\band\b", s):
        c = normalize_name(piece, date, present)
        if c and c not in out:
            out.append(c)
    return out


def find_motion_text_before(text, pos, floor=0):
    """For a structured name-form vote line at `pos`, find the action/motion text above
    (never reaching back before `floor`, which bounds it to the current motion block)."""
    pre = text[max(floor, pos - 900):pos]
    # explicit action item phrasing closest to the vote line
    pats = [
        r"Motion:\s*(?:To|That)\b(?P<t>[^\n]+(?:\n(?!\s*Motion:)[^\n]+){0,2})",
        r"(?:asked for a motion|made\s+(?:a|the)\s+motion|moved|motioned)\s+to\b"
        r"(?P<t>[^\n]+(?:\n[^\n]+)?)",
        r"\bmotion\s+(?:was\s+made\s+)?to\b(?P<t>[^\n]+(?:\n[^\n]+)?)",
    ]
    best = None
    for p in pats:
        for m in re.finditer(p, pre, re.I):
            best = m  # take last (closest to vote line)
        if best:
            return _clean_motion(best.group("t"))
    # fall back to nearest preceding heading line, SKIPPING generic agenda sub-headings
    # ("Commission Discussion", "Action Item", "Staff Presentation", ...) so we reach the
    # substantive numbered agenda-item title (e.g. a plat/site-plan/rezone name).
    generic = re.compile(
        r"^(?:commission(?:er)?s?\s+(?:discussion|questions?|comments?)|action\s+items?|"
        r"staff\s+(?:presentation|report)|public\s+(?:comment|hearing|input)|"
        r"open(?:ing)?\s+(?:the\s+)?public\s+hearing|close\s+(?:the\s+)?public\s+hearing|"
        r"discussion|motion|prayer|pledge|take\s+public\s+comment|new\s+business|"
        r"old\s+business|welcome\b.*)\s*$", re.I)
    lines = [ln for ln in pre.split("\n") if ln.strip()]
    for ln in reversed(lines):
        s = ln.strip()
        s = re.sub(r"^(?:\d+\.|[a-z]\)|[a-z]\.|[ivx]+\.)\s*", "", s)
        s = re.sub(r"\s*[-–:]?\s*Action Items?.*$", "", s, flags=re.I).strip()
        if len(s) <= 3 or generic.match(s):
            continue
        if (re.match(r"^(?:\d+\.|[a-z]\.)\s*", ln.strip()) or ln.strip().isupper()
                or re.search(r"approv|plat|rezone|re-zone|\bzone\b|zoning|site plan|"
                             r"subdivision|conditional|\bcup\b|hearing|license|annex|"
                             r"ordinance|minutes|adjourn|appoint|elect|nominat|chair|"
                             r"home occupation|amend|code|general plan|split|lot line|"
                             r"boundary|variance|permit", s, re.I)):
            return _clean_motion(s)
    return "(motion text not captured)"


def _clean_motion(t):
    if not t:
        return "(motion text not captured)"
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^(?:[a-z]\.|\d+\.)\s+", "", t, flags=re.I)   # leading list marker "a." / "1."
    t = re.sub(r"\s+[a-z]\.?$", "", t, flags=re.I)            # trailing stray list marker " b"
    t = re.sub(r"^\s*(?:to|that|for|and|of)\s+", "", t, flags=re.I)
    t = t.strip(" .;,:-")
    return t[:600] if t else "(motion text not captured)"


MOVER_PATS = [
    re.compile(r"(?P<n>" + NAME +
               r")\s+(?:moved|moves|motioned|motions|nominate[sd]?|"
               r"mak[e]?s?\s+(?:a|the)\s+motion|mad[ey]\s+(?:a|the)\s+motion)", re.I),
    re.compile(r"(?:made\s+(?:a|the)\s+motion|motion\s+(?:was\s+)?made|a\s+motion)\b[^.]*?\bby\s+(?P<n>" + NAME + r")", re.I),
    re.compile(r"\bmotion\s+by\s+(?P<n>" + NAME + r")", re.I),
    re.compile(r"(?P<n>" + NAME + r")\s+called\s+for", re.I),
]
SECOND_PATS = [
    re.compile(r"(?P<n>" + NAME + r")\s+seconded", re.I),
    re.compile(r"second(?:ed)?\s+by\s+(?P<n>" + NAME + r")", re.I),
    re.compile(r"\bSecond:\s*(?P<n>" + NAME + r")", re.I),
]


def _last_match(pats, s, date, present=None):
    best = None
    for p in pats:
        for m in p.finditer(s):
            if best is None or m.start() > best[0]:
                cand = normalize_name(m.group("n"), date, present)
                if cand:
                    best = (m.start(), cand, m)
    return best


def _nearest_motion_action(text, label_abs, floor=0):
    """Action text from the nearest preceding 'Motion:' line(s) that is itself an action
    statement (not a vote line carrying 'Second:', and not a bare commissioner name).
    Used for the 2022 'Made by:' form where the action sits on a separate 'Motion:' line.
    Bounded by `floor` so it never crosses into the previous motion's block."""
    pre = text[max(floor, label_abs - 800):label_abs]
    best = None
    for m in re.finditer(
            r"(?im)^[ \t]*(?:[a-z\d]\.\s*)?Motion\s*:\s*(?P<t>[^\n]+"
            r"(?:\n(?![ \t]*(?:[a-z\d]\.\s*)?(?:Made by|Second|Outcome|Motion)\s*:)"
            r"[^\n]+){0,3})", pre):
        seg = m.group("t")
        if re.search(r"\bSecond\s*:", seg, re.I):
            continue
        t = re.sub(r"^\s*the\s+motion\s+was\s+made\s*", "", seg.strip(), flags=re.I)
        t = re.sub(r"^\s*(?:to|that)\s+", "", t, flags=re.I)
        if len(t.split()) <= 3 and normalize_name(t, None):
            continue  # a bare-name mover line, not the action
        best = t
    return _clean_motion(best) if best else None


def parse_structured(text, date, present=None):
    """Parse every structured motion (anchored on a 'Second:' label).

    Handles all of:
      * 2022 'Made by:' form  -> action on a preceding 'Motion:' line, then
            'Made by: <mover>  Second: <sec>  Outcome: <text>'
      * 2022-2023 single line -> 'Motion: <mover> Second: <sec> [Opposed:] Outcome: <text>'
      * 2024-2026 multi line   -> 'Motion: <mover> motions that <action>' / 'Second: <sec>' /
                                  'Outcome: <text>'  (verbs: approved/passes/denied/...)
    Returns (votes, consumed_spans)."""
    votes = []
    spans = []
    for sm in SECOND_LABEL_RE.finditer(text):
        p = sm.start()
        ls = text.rfind("\n", 0, p) + 1
        le = text.find("\n", p)
        if le == -1:
            le = len(text)
        before = text[ls:p]

        # seconder: text after 'Second:' up to Outcome/Opposed/end-of-line
        after = text[sm.end():le + 1]
        sec_seg = re.split(r"\bOutcome\s*:|\bOpposed\s*:", after, 1, flags=re.I)[0]
        sec_seg = re.sub(r"\bseconded\b.*$", "", sec_seg, flags=re.I)
        seconder = normalize_name(sec_seg, date, present)

        # Bound the backward search so a motion block can't reach past the PRIOR motion's
        # closing 'Outcome:'/'TIME:' line (prevents an unlabeled narrative motion -- e.g. an
        # adjourn/minutes motion -- from re-grabbing the previous motion's 'Motion:' label).
        prev_end = 0
        for pm in re.finditer(r"\b(?:Outcome|TIME|Time)\s*:[^\n]*", text[max(0, p - 1200):p], re.I):
            prev_end = max(0, p - 1200) + pm.end()
        region_start = max(prev_end, p - 900)
        region = text[region_start:p]

        head_seg = None
        label_abs = region_start
        mover = None
        motion_text = None

        # 1) Motion:/Made by: label on THIS line before 'Second:' (single-line forms)
        ml = None
        for m in MOTION_LABEL_RE.finditer(before):
            ml = m
        if ml and before[ml.end():].strip():
            head_seg = before[ml.end():].strip()
            label_abs = ls + ml.start()
        else:
            # 2) nearest Motion:/Made by: label vs nearest narrative mover within the region;
            #    take whichever sits closer to the 'Second:' anchor.
            last_lbl = None
            for mm in MOTION_LABEL_RE.finditer(region):
                last_lbl = mm
            mv_nar = _last_match(MOVER_PATS, region, date, present)
            lbl_pos = last_lbl.start() if last_lbl else -1
            nar_pos = mv_nar[0] if mv_nar else -1
            if last_lbl and lbl_pos >= nar_pos:
                head_seg = region[last_lbl.end():].strip()
                label_abs = region_start + last_lbl.start()
            elif mv_nar:
                mover = mv_nar[1]
                label_abs = region_start + mv_nar[0]
                seg = re.sub(
                    r"^.*?(?:moved|motioned|motions?|moves?|made\s+(?:a|the)\s+motion|"
                    r"called\s+for|by)\s+", "", region[mv_nar[0]:], count=1, flags=re.I)
                seg = re.sub(r"^\s*(?:that|to|of)\s+", "", seg, flags=re.I)
                motion_text = _clean_motion(seg)
        if head_seg is None and mover is None:
            continue  # 'Second:' with no resolvable motion -> not a structured vote

        # parse a label-form head segment for mover + inline action
        if head_seg is not None:
            vm = MOTION_VERB_RE.search(head_seg)
            if vm:
                mover = normalize_name(head_seg[:vm.start()], date, present)
                action_part = re.sub(r"^\s*(?:that|to|of)\s+", "", head_seg[vm.end():].strip(),
                                     flags=re.I)
                if len(action_part) > 3:
                    motion_text = _clean_motion(action_part)
            elif len(head_seg.split()) <= 4:
                mover = normalize_name(head_seg, date, present)
            else:
                bym = re.search(r"\bby\s+(" + NAME + r")\s*$", head_seg, re.I)
                if bym:
                    mover = normalize_name(bym.group(1), date, present)
                motion_text = _clean_motion(
                    re.sub(r"^\s*the\s+motion\s+was\s+made\s*", "", head_seg, flags=re.I))

        if not motion_text or motion_text == "(motion text not captured)" or len(motion_text) < 4:
            motion_text = _nearest_motion_action(text, label_abs, region_start) or \
                find_motion_text_before(text, label_abs, region_start)

        # outcome block: from 'Outcome:' to the block's closing 'TIME:' (every structured
        # motion ends with a 'd. TIME:' line) / next motion label / triple blank line.
        # NOTE: do NOT stop at numbered list items -- roll calls are written "1. Name: Aye".
        out_seg = ""
        om = re.search(
            r"\bOutcome\s*:\s*(?P<o>.+?)"
            r"(?:\b(?:TIME|Time)\s*:|\n[ \t]*(?:[a-z\d]\.\s*)?(?:Motion|Mad[ey] by)\s*:|"
            r"\n[ \t]*\n|\Z)",
            text[p:p + 1000], re.I | re.S)
        if om:
            out_seg = re.sub(r"[ \t]+", " ", om.group("o")).strip()
        low_out = out_seg.lower()

        # named votes. Scan the whole motion->outcome region for a roll call: it may sit
        # right after 'Second:' (before 'Outcome:', e.g. "Thomson: Nay, Peterson: Aye ...")
        # OR inside the outcome block (numbered "1. Name - Aye" lists).
        buckets = {"aye": [], "nay": [], "abstain": [], "recuse": [], "absent": []}
        vote_region = text[ls:(p + om.end()) if om else p + 300]
        # A labeled dissent list ("Opposed:"/"Nay:") names ONLY the dissenters (ayes not
        # enumerated) -> capture as dissent, never as a 0:N tally.
        for opp in re.finditer(r"\b(?:Opposed|Nay)\s*:\s*([^\n]+)", vote_region, re.I):
            for c in _split_name_list(opp.group(1), date, present):
                if c not in buckets["nay"]:
                    buckets["nay"].append(c)
        for k, names in parse_rollcall(vote_region, date, present).items():
            for c in names:
                if c not in buckets[k]:
                    buckets[k].append(c)

        outcome_pass = not bool(OUTCOME_FAIL_RE.search(low_out))
        named = sum(len(buckets[k]) for k in buckets)
        names_recorded = named > 0
        # A full tally (N:N) is reported ONLY when the ayes were actually enumerated (a real
        # roll call). A dissent-only record ("Opposed:"/"Nay:"/narrative) keeps "(X opposed)".
        aye_n = nay_n = None
        if buckets["aye"]:
            aye_n = len(buckets["aye"])
            nay_n = len(buckets["nay"])
        dissent = list(buckets["nay"]) if (buckets["nay"] and aye_n is None) else None
        # 'unanimous' suffix only when there is no recorded dissent (avoid "unanimous ... opposed")
        unanimous = ("unanim" in low_out) and not buckets["nay"]

        result, cls = build_result(motion_text, outcome_pass, aye_n, nay_n, unanimous, dissent)
        votes.append(_mk_vote(motion_text, result, cls, mover, seconder, buckets,
                              names_recorded, label_abs))
        spans.append((label_abs, p + (om.end() if om else 200)))
    return votes, spans


def parse_meeting(path, date):
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("\f", "\n").replace("�", "ti")  # ligature corruption -> 'ti'
    text = strip_footers(raw)  # remove running page footer so it can't bleed into motion text
    present = detect_attendance(text, date)  # used to disambiguate bare 'Peterson' surnames

    # ---- STRUCTURED events (anchored on 'Second:' labels) ----
    votes, consumed = parse_structured(text, date, present)

    # ---- NARRATIVE events ----
    for rm in NARR_RESULT_RE.finditer(text):
        rpos = rm.start()
        if any(a <= rpos <= b for a, b in consumed):
            continue
        verb = rm.group("verb").lower()
        outcome_pass = verb in ("passed", "carried")

        # backward window bounded by previous event/result/heading
        prev = 0
        for pm in NARR_RESULT_RE.finditer(text, 0, rpos):
            prev = pm.end()
        win_start = max(prev, rpos - 800)
        window = text[win_start:rpos]

        mv = _last_match(MOVER_PATS, window, date, present)
        if not mv:
            continue  # a result with no identifiable mover -> skip (likely a stray phrase)
        mover = mv[1]
        sc = _last_match(SECOND_PATS, window, date, present)
        seconder = sc[1] if sc else None

        # motion text: from the mover anchor to the result, minus seconder clause
        seg = window[mv[0]:]
        seg = re.sub(r"^.*?(?:moved|motioned|made\s+(?:a|the)\s+motion|called\s+for|by)\s+",
                     "", seg, count=1, flags=re.I)
        if sc:
            cut = seg.lower().find("second")
            if cut > 0:
                seg = seg[:cut]
        # strip any residual "[bleed.] <Role> <Name> moved/moves to" lead-in
        seg = re.sub(
            r"^.*?\b(?:moved|moves|motioned|made\s+(?:a|the)\s+motion)\b\s*(?:to|that)?\s*",
            "", seg, count=1, flags=re.I | re.S)
        motion_text = _clean_motion(seg)
        if motion_text == "(motion text not captured)":
            # mover trailed the action ("Motion was made to <..> by X") -> use full window
            motion_text = _clean_motion(re.sub(r"\bby\s+" + re.escape(mv[2].group("n")) + r".*$",
                                               "", window, flags=re.I | re.S))

        # named dissent in the result sentence
        post = text[rpos:rpos + 260]
        scan = window[-200:] + " " + post
        dissent = []
        dm = re.search(r"(?P<names>" + NAME + r"(?:(?:\s*,\s*|\s+and\s+)" + NAME + r")*)\s+"
                       r"(?:opposed|dissent|voted\s+(?:no|nay|against)|in\s+opposition)",
                       scan, re.I)
        if dm:
            dissent = _split_name_list(dm.group("names"), date, present)
        buckets = {"aye": [], "nay": dissent, "abstain": [], "recuse": [], "absent": []}
        unanimous = bool(re.search(r"unanim", post + window[-80:], re.I)) and not dissent
        names_recorded = bool(dissent)

        result, cls = build_result(motion_text, outcome_pass, None, None,
                                   unanimous, dissent or None)
        votes.append(_mk_vote(motion_text, result, cls, mover, seconder, buckets,
                              names_recorded, rpos))

    votes.sort(key=lambda v: v.pop("_pos"))
    for k, v in enumerate(votes, 1):
        v["motion_no"] = k
    return votes


class _V(dict):
    pass


def _mk_vote(motion_text, result, cls, mover, seconder, buckets, names_recorded, pos):
    v = {
        "body": "PlanningCommission",
        "motion": motion_text,
        "motion_type": classify_motion(motion_text),
        "result": result,
        "action_class": cls,
        "mover": mover,
        "seconder": seconder,
        "aye": buckets["aye"],
        "nay": buckets["nay"],
        "abstain": buckets["abstain"],
        "recuse": buckets["recuse"],
        "absent": buckets["absent"],
        "names_recorded": names_recorded,
        "_pos": pos,
    }
    return v


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-extract even if JSON exists")
    args = ap.parse_args()

    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    attendance = {}  # date -> set(commissioners)

    for r in rows:
        rel = r["path"]
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"MISSING: {rel}", file=sys.stderr)
            continue
        date, year = r["date"], r["year"]
        week = Path(rel).parent.name
        out_dir = VOTES_DIR / year / week
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = Path(rel).stem
        out_json = out_dir / f"{slug}.json"

        text = path.read_text(encoding="utf-8", errors="replace").replace("�", "ti")
        attendance[date] = detect_attendance(text, date)

        if out_json.exists() and not args.force:
            skipped += 1
        else:
            votes = parse_meeting(path, date)
            payload = {
                "date": date,
                "year": int(year),
                "title": "Planning Commission",
                "body": "PlanningCommission",
                "source": rel,
                "attendance": sorted(attendance[date]),
                "votes": votes,
            }
            out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
            processed += 1

    print(f"Extracted {processed} meetings ({skipped} skipped existing) -> JSON")
    build_all_votes()
    build_roster(rows, attendance)


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n_rows = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], "Planning Commission",
                        "PlanningCommission", v["motion_no"], v["motion"],
                        v["motion_type"], v["result"], v.get("mover") or "",
                        v.get("seconder") or ""]
                emitted = False
                if v.get("names_recorded"):
                    for key, label in (("aye", "Aye"), ("nay", "Nay"),
                                       ("abstain", "Abstain"), ("recuse", "Recuse"),
                                       ("absent", "Absent")):
                        for member in v.get(key, []):
                            w.writerow(base + [member, label, data["source"]])
                            n_rows += 1
                            emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")


def build_roster(rows, attendance):
    seen = {}
    for r in rows:
        d = r["date"]
        for c in attendance.get(d, ()):  # noqa
            s = seen.setdefault(c, {"first": d, "last": d, "n": 0})
            s["first"] = min(s["first"], d)
            s["last"] = max(s["last"], d)
            s["n"] += 1
    with ROSTER.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for c in sorted(seen, key=lambda k: (seen[k]["first"], k)):
            w.writerow([c, seen[c]["first"], seen[c]["last"], seen[c]["n"]])
    print(f"Wrote {ROSTER} with {len(seen)} commissioners")


if __name__ == "__main__":
    main()
