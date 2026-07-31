#!/usr/bin/env python3
"""
Vineyard, UT — PLANNING COMMISSION vote extraction.

Reads planning_commission/minutes_index.csv, parses recorded roll-call motions out of
the markdown minutes, and emits:
  - per-meeting JSON  -> planning_commission/votes/<year>/<week-monday>/<date>_planning-commission-meeting.json
  - long-format CSV   -> planning_commission/all_votes.csv  (rebuilt from the JSONs; body="PlanningCommission")
  - roster            -> planning_commission/roster.csv     (commissioner, first_seen, last_seen, n_meetings)

Adapts the council extractor (meeting_minutes/extract_votes.py). Differences:
  * Roles are CHAIR / VICE-CHAIR / ACTING CHAIR / CHAIR (PRO) TEMPORE / CHAIRPERSON /
    COMMISSIONER / ALTERNATE COMMISSIONER.  COUNCILMEMBER / MAYOR are *excluded* (joint
    sessions occasionally embed a council roll-call inside a PC minutes file).
  * Member identity is the commissioner's FULL NAME (two commissioners share the surname
    Blackburn — Tim 2020-23 and Spencer 2020/2022 — disambiguated via meeting attendance).
  * `result` encodes the recommendation/final-action/procedural distinction (see README/CLAUDE.md):
       recommendation  -> "Positive recommendation N:N" / "Negative recommendation N:N"
       final action    -> "N:N Approved (Final Action)" / "N:N Denied (Final Action)"
       procedural      -> "N:N Pass" / "N:N Fail"
  * Roll formats seen: ALL-CAPS inline, "ROLL (CALL) WENT AS FOLLOW(S/ED):",
    "ALL IN FAVOR VOTED YES: <bare surnames>", 2026 structured "Yes:/No:/Absent:",
    and tally-only "CARRIED UNANIMOUSLY" (-> names_recorded=false, empty member lists).

CARDINAL RULE: never fabricate. Tally-only motions keep empty member lists. Names are only
mapped to the commissioner allowlist; staff/residents/councilmembers are dropped, never guessed.
"""
import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "minutes_index.csv"
VOTES_DIR = ROOT / "votes"
ALL_VOTES_CSV = ROOT / "all_votes.csv"
ROSTER_CSV = ROOT / "roster.csv"

BODY = "PlanningCommission"
TITLE = "Planning Commission"

# ---- commissioner roster / name normalization --------------------------------
# canonical UPPER surname -> canonical full name (the dataset's commissioner identity)
FULLNAME = {
    "ANDERSON": "Steve Anderson",
    "BOWN": "Craig Bown",
    "BRADY": "Bryce Brady",
    "BRAMWELL": "Christopher Bramwell",
    "CHRISTENSEN": "Jordan Christensen",
    "EVANS": "Daria Evans",
    "FAGG": "Brad Fagg",
    "GUDMUNDSON": "Tay Gudmundson",
    "HARBIN": "Natalie Harbin",
    "HUNTINGTON": "Martina Huntington",
    "JENKINS": "Anthony Jenkins",
    "JESSOP": "Marcus Jessop",
    "KNIGHTON": "Jeff Knighton",
    "OSTLER": "Graden Ostler",
    "PEARCE": "David Pearce",
    "PRICE": "Kristal Price",
    "RASMUSSEN": "Amber Rasmussen",
    "RHOTON": "Caden Rhoton",
    "STEELE": "Nathan Steele",
    "SULLIVAN": "Shan Sullivan",
    "WELCH": "Jessica Welch",
    # BLACKBURN handled specially (two people) — see resolve_blackburn / norm_name
}
# OCR / spelling variants -> canonical UPPER surname (folded into FULLNAME lookup)
VARIANTS = {
    "BLAKBURN": "BLACKBURN",
    "GUDMUDSON": "GUDMUNDSON", "GUDMUNDON": "GUDMUNDSON", "GUDMUNDSEN": "GUDMUNDSON",
    "GUDMUNSON": "GUDMUNDSON", "GUNDMENDSON": "GUDMUNDSON", "GUNDMUNDSON": "GUDMUNDSON",
    "GUNDMUNSON": "GUDMUNDSON", "GUNDMUNDON": "GUDMUNDSON",
    "JENKIN": "JENKINS", "JEKNINS": "JENKINS",
    "KINGTON": "KNIGHTON",
    "OSTER": "OSTLER",  # source typo in the recovered 2023-06-21 minutes ("Graden Oster")
    "RASSMUSSEN": "RASMUSSEN", "RASUMSSEN": "RASMUSSEN", "RASMUSEN": "RASMUSSEN",
    "HRBIN": "HARBIN",
    "RHOTTON": "RHOTON", "RHOOTON": "RHOTON",
    "STEEL": "STEELE", "STELE": "STEELE",
    "PIERCE": "PEARCE",
    "WELSH": "WELCH",   # OCR of commissioner Jessica Welch (council "Cristy Welsh" is
                        # excluded by role-awareness: COUNCILMEMBER/MAYOR -> None)
}
# the surname shared by two distinct people
SHARED = {"BLACKBURN"}

# role tokens that mark a *commissioner* name (stripped to reach the surname)
COMM_ROLE = (r"(?:ALTERNATE\s+COMMISSIONERS?|OTHER\s+COMMISSIONERS?|COMMISSIONERS?|"
             r"ACTING\s+CHAIR|VICE[-\s]?CHAIR|CHAIRPERSON|CHAIR[-\s]?PRO[-\s]?TEMPORE|"
             r"CHAIR[-\s]?TEMPORE|CHAIR)")
# role tokens that mark a NON-commissioner (council member in a joint session) -> drop
NONCOMM_ROLE = re.compile(r"\b(?:COUNCIL\s*MEMBERS?|COUNCILMEMBERS?|MAYOR\s+PRO\s+TEM\w*|"
                          r"MAYOR)\b", re.I)
ROLE_PREFIX = re.compile(r"^(?:" + COMM_ROLE + r"|MR\.?|MS\.?|MRS\.?)\s+", re.I)


def _surname_to_canon(up, blackburn_full=None):
    """UPPER surname token -> canonical full name, honoring variants & the Blackburn split."""
    up = VARIANTS.get(up, up)
    if up in SHARED:
        # Two distinct commissioners share this surname (Tim / Spencer Blackburn); they
        # never co-occur. Resolve ONLY from this meeting's own text (blackburn_full, set
        # by resolve_blackburn). When it can't be told apart, keep the printed surname —
        # NEVER silently default to a person (cardinal rule: never fabricate). A bare
        # "Blackburn" is not on the FULLNAME allowlist, so an unresolved token stays an
        # honest, un-merged surname rather than a guessed attribution.
        return blackburn_full or "Blackburn"
    return FULLNAME.get(up)


def norm_name(raw, blackburn_full=None):
    """Map a raw 'role + name' token to a canonical commissioner full name, else None.

    Role-aware: a COUNCILMEMBER/MAYOR token (joint-session council roll) returns None."""
    if not raw:
        return None
    if NONCOMM_ROLE.search(raw):
        return None
    s = raw.strip().strip(".,'’“”() ")
    s = ROLE_PREFIX.sub("", s).strip()
    toks = re.findall(r"[A-Za-z]+", s)
    if not toks:
        return None
    # try last token (surname), then any token
    cand = _surname_to_canon(toks[-1].upper(), blackburn_full)
    if cand:
        return cand
    for t in toks:
        cand = _surname_to_canon(t.upper(), blackburn_full)
        if cand:
            return cand
    return None


def split_names(blob, blackburn_full=None):
    """Split an 'A, B, AND C' list (roles optional; bare surnames OK) into canonical names."""
    if not blob:
        return []
    blob = re.sub(r"\bAND\b", ",", blob, flags=re.I).replace("&", ",").replace(";", ",")
    out, seen = [], set()
    for piece in blob.split(","):
        n = norm_name(piece, blackburn_full)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


# ---- attendance (roster) -----------------------------------------------------
# A present-roster header: the region START. (Council:/joint subheaders are not matched;
# the 'Planning Commission:' subheader IS, so joint meetings start at the PC block.)
PRESENT_HDR = re.compile(
    r"(?im)^[ \t]*(?:(?:PLANNING\s+)?COMMISSION(?:ERS)?(?:\s+MEMBERS)?\s+PRESENT\s*:?"
    r"|(?:PLANNING\s+)?COMMISSION(?:ERS?)?(?:\s+MEMBERS)?\s*:"
    r"|Planning\s+Commission\s*:"
    r"|Present\s*:?)[ \t]*$")
EXCUSED_HDR = re.compile(
    r"(?im)^[ \t]*(?:(?:PLANNING\s+)?COMMISSIONERS?\s+EXCUSED\s*:?"
    r"|Those\s+excused\s*:?"
    r"|(?:PLANNING\s+)?COMMISSION(?:ERS)?\s+(?:ABSENT|NOT\s+PRESENT)\s*:?)")
# Section boundaries that END a roster block (must NOT appear before the present header,
# which is why the region only starts AT a present header).
SECTION_END = re.compile(
    r"(?im)^[ \t]*(?:STAFF\b|Others?\b|Also\s+Present|Anderson\s+Geneva|Council\s*:|"
    r"Heritage\s+Commission|Bicycle\s+Advisory|REGULAR\s+(?:SESSION|MEETING)|WORK\s+SESSION|"
    r"CALL\s+TO\s+ORDER|INVOCATION|PLEDGE|PUBLIC\s+NOTICE|MINUTES\s+OF|\d+\.\s|"
    r"COMMISSIONERS?\s+EXCUSED|Those\s+excused)")


def _block_after(head, start_pos):
    end = SECTION_END.search(head, start_pos)
    return head[start_pos: end.start() if end else start_pos + 350]


def attendance(text, blackburn_full):
    """Return (present_set, excused_set) of canonical commissioner full names."""
    present, excused = set(), set()
    head = text[:4000]
    for m in PRESENT_HDR.finditer(head):
        block = m.group(0) + " " + _block_after(head, m.end())
        flat = re.sub(r"\s+", " ", block)
        for n in split_names(flat, blackburn_full):
            present.add(n)
        for mm in re.finditer(r"(" + COMM_ROLE + r")\s+([A-Z][a-zA-Z'’]+(?:\s+[A-Z][a-zA-Z'’]+)?)",
                              block):
            n = norm_name(mm.group(0), blackburn_full)
            if n:
                present.add(n)
    for m in EXCUSED_HDR.finditer(head):
        block = _block_after(head, m.end())
        for n in split_names(re.sub(r"\s+", " ", block), blackburn_full):
            excused.add(n)
    # a commissioner can't be both present and excused in the same meeting; excused wins
    present -= excused
    return present, excused


def resolve_blackburn(text):
    """Which Blackburn sits in this meeting? Resolve from the full name printed in the
    meeting's own attendance header + body.

    Two distinct commissioners share the surname — Tim Blackburn (2020-2023) and Spencer
    Blackburn (2020, 2022) — and they NEVER co-occur in a meeting. Returns the canonical
    full name only when exactly one of the two is named in this text. Returns None when it
    cannot be told apart — neither full name present, OR (defensively) both present — so a
    bare "Blackburn" roll token is left UNRESOLVED (kept as the printed surname by
    _surname_to_canon) rather than guessed. No silent default-to-Tim."""
    has_spencer = bool(re.search(r"Spencer\s+Blackburn", text, re.I))
    has_tim = bool(re.search(r"Tim(?:othy)?\s+Blackburn", text, re.I))
    if has_spencer and not has_tim:
        return "Spencer Blackburn"
    if has_tim and not has_spencer:
        return "Tim Blackburn"
    return None  # ambiguous (neither, or — defensively — both): do NOT guess


# ---- motion-type classification (12-cat taxonomy, mirrors council) ------------
def classify(text):
    t = text.lower()
    if re.search(r"\bopen the public hearing|close the public hearing|"
                 r"open.{0,15}public hearing|close.{0,15}public hearing", t):
        return "Public Hearing Action"
    if re.search(r"\badjourn|recess|go into a closed session|closed session|"
                 r"reconvene|approve the agenda|amend the agenda|adopt the agenda|"
                 r"continue|table\b|postpone|excuse|election of|elect a |nominat", t):
        return "Procedural/Administrative"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bbudget amendment|amend.{0,20}budget|tentative budget|"
                 r"final budget|adopt.{0,20}budget|certified tax rate", t):
        return "Budget Amendment"
    if re.search(r"\bgrant\b|cdbg|funding application|apply for", t):
        return "Grant-Funding"
    if re.search(r"\binterlocal|cooperative agreement|joint resolution", t):
        return "Interlocal"
    if re.search(r"\bappoint|reappoint|swear", t):
        return "Appointment"
    if re.search(r"\brezone|rezoning|zoning map|general plan|\bplat\b|subdivision|"
                 r"site plan|land use|annex|conditional use|\bcup\b|preliminary|final plat|"
                 r"development agreement|setback|density|overlay|waiver|design review|"
                 r"design standard|sign standard|concept plan|master plan", t):
        return "Land-Use/Zoning"
    if re.search(r"\b(?:contract|agreement|purchase|bid|professional\s+services|"
                 r"task\s+order|change\s+order|lease)\b|award.{0,20}(bid|contract)", t):
        return "Contract/Purchase"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"\b(?:proclaim|proclamation|recogniz\w*|honor|commend|memoriam)\b", t):
        return "Ceremonial"
    if re.search(r"\bconsent (item|agenda|calendar)|approve.{0,15}minutes|"
                 r"approval of.{0,20}minutes|minutes as recorded", t):
        return "Procedural/Administrative"
    return "Other"


# ---- result / tally extraction -----------------------------------------------
WORDNUM = {"ZERO": 0, "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
           "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10, "NONE": 0}


def find_outcome(tail):
    """Return (verb, stated_yes, stated_no) — verb in {Pass,Fail,None}; stated tally or None."""
    # 2026 structured: "Motion Passed/Failed N-N"
    m = re.search(r"Motion\s+(Passed|Failed|Carried|Tied)\s+(\d+)\s*[-–]\s*(\d+)", tail, re.I)
    if m:
        verb = "Fail" if m.group(1).lower() == "failed" else "Pass"
        return verb, int(m.group(2)), int(m.group(3))
    # caps inline: "MOTION CARRIED/PASSED/FAILED N-N" or "... WITH N TO N" or "FOUR (4) TO ONE (1)"
    m = re.search(r"(CARRIED|PASSED|FAILED)\s+(?:WITH\s+)?(\d+)\s*[-–]\s*(\d+)", tail, re.I)
    if m:
        verb = "Fail" if m.group(1).upper() == "FAILED" else "Pass"
        return verb, int(m.group(2)), int(m.group(3))
    m = re.search(r"(CARRIED|PASSED|FAILED)\s+(?:WITH\s+)?([A-Z]+)\s*(?:\((\d+)\))?\s*TO\s+"
                  r"([A-Z]+)\s*(?:\((\d+)\))?", tail, re.I)
    if m:
        a = m.group(3) or WORDNUM.get(m.group(2).upper())
        b = m.group(5) or WORDNUM.get(m.group(4).upper())
        verb = "Fail" if m.group(1).upper() == "FAILED" else "Pass"
        return verb, (int(a) if a is not None else None), (int(b) if b is not None else None)
    # failed (no number)
    if re.search(r"\bMOTION\s+FAILED\b|\bVOTE\s+FAILED\b|FAILED\s+TO\s+PASS|FAILED\s+FOR\s+LACK|"
                 r"NO\s+SECOND\s+WAS\s+OFFERED|DIED\s+FOR\s+LACK", tail, re.I):
        return "Fail", None, None
    # carried/passed (unanimous or bare); also "THE VOTE CARRIED/WAS UNANIMOUS"
    if re.search(r"\bCARRIED\b|\bPASSED\b|(?:MOTION|VOTE)\s+WAS\s+UNANIMOUS|UNANIMOUS",
                 tail, re.I):
        return "Pass", None, None
    return None, None, None


# ---- vote-list extraction ----------------------------------------------------
def extract_votes_inline(tail, bb):
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    verb_pat = re.compile(
        r"\bVOTED\s+(?:AYE|YES)\b"
        r"|\bVOTED\s+IN\s+(?:FAVOR|SUPPORT|THE\s+AFFIRMATIVE)\b"
        r"|\bVOTED\s+(?:NAY|NO)\b"
        r"|\bVOTED\s+(?:IN\s+OPPOSITION(?:\s+TO)?|AGAINST|IN\s+THE\s+NEGATIVE)\b"
        r"|\bABSTAINED\b|\bABSTAIN(?:ED)?\s+FROM\s+VOTING\b"
        r"|\b(?:WAS|WERE)\s+(?:ABSENT|EXCUSED)\b"
        r"|\bRECUSED\b",
        re.I,
    )
    last = 0
    for m in verb_pat.finditer(tail):
        clause = tail[last:m.start()]
        last = m.end()
        # names = trailing run of this clause (after the last sentence period)
        seg = clause.split(".")[-1]
        # strip leading roll markers so they don't block the name run
        seg = re.sub(r"(?i).*ROLL\s+(?:CALL\s+)?WENT\s+AS\s+FOLLOW(?:S|ED)?", "", seg)
        seg = re.sub(r"(?i).*ALL\s+IN\s+FAVOR\s+VOTED\s+YES\s*:?", "", seg)
        seg = re.sub(r"(?i).*ROLL\s+CALL\s*:", "", seg)
        names = split_names(seg, bb)
        if not names:
            continue
        verb = m.group(0).upper()
        if "AYE" in verb or "YES" in verb or "FAVOR" in verb or "SUPPORT" in verb \
                or "AFFIRMATIVE" in verb:
            res["aye"] += names
        elif "NAY" in verb or "NO" in verb or "OPPOSITION" in verb \
                or "AGAINST" in verb or "NEGATIVE" in verb:
            res["nay"] += names
        elif "ABSTAIN" in verb:
            res["abstain"] += names
        elif "ABSENT" in verb or "EXCUSED" in verb:
            res["absent"] += names
        else:
            res["recuse"] += names
    return _dedupe(res)


# leading-label phrasings: "<label>: <names>" where the label sets the direction.
# Covers: "Those voting aye:", "THOSE WHO VOTED IN FAVOR:", "ALL IN FAVOR:",
# "ALL IN FAVOR VOTED/SAID YES:", "ALL VOTED YES:", "ROLL FOR YES WENT AS FOLLOWS:",
# bare "VOTED YES:/SAID YES:" (catches OCR mid-word wraps like "ALL IN F AVOR VOTED YES:").
LEADING_LABELS = [
    ("aye", r"(?:those\s+(?:\w+\s+){0,2}vot(?:ing|ed)\s+(?:aye|yes|in\s+favor)"
            r"|those\s+in\s+favor(?:\s+(?:voted|said)\s+(?:yes|aye|in\s+favor))?"
            r"|all\s+in\s+favor(?:\s+(?:voted|said)\s+(?:yes|aye|in\s+favor))?"
            r"|all\s+voted\s+(?:yes|aye|in\s+favor)"
            r"|roll\s+for\s+yes\s+went\s+as\s+follow(?:s|ed)?"
            r"|(?:voted|said)\s+(?:yes|aye|in\s+favor)\s*(?=:))"),
    ("nay", r"(?:those\s+(?:\w+\s+){0,2}vot(?:ing|ed)\s+(?:nay|no|against)"
            r"|those\s+(?:who\s+)?opposed"
            r"|(?:voted|said)\s+(?:no|nay|against)\s*(?=:))"),
    ("abstain", r"(?:those\s+(?:who\s+)?abstain(?:ing|ed)?|abstain(?:ed)?\s+from\s+voting)"),
    ("recuse", r"(?:those\s+(?:who\s+)?recus(?:ing|ed)?)"),
]
_STOP = (r"(?=\.\s|\bthe\s+(?:motion|vote)\b|\bmotion\s+(?:carried|passed|failed)\b"
         r"|those\s+(?:\w+\s+){0,2}vot|those\s+(?:who\s+)?opposed|all\s+voted|"
         r"roll\s+for|(?:voted|said)\s+(?:yes|no|aye|nay)\s*:|$)")

# first names (unique across the commission) — used ONLY by the per-member
# "NAME, YES;" parser, never by general name resolution (a planner "Anthony Fletcher"
# must not become Jenkins).
FIRSTNAME = {full.split()[0].upper(): full for full in FULLNAME.values()}
FIRSTNAME.update({"TIM": "Tim Blackburn", "SPENCER": "Spencer Blackburn",
                  "CHRIS": "Christopher Bramwell"})


def extract_votes_leading(tail, bb):
    """Parse leading-label phrasings (label precedes the name list; bare surnames OK)."""
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    flat = re.sub(r"\s+", " ", tail)
    for key, lab in LEADING_LABELS:
        for m in re.finditer(lab + r"\s*:?\s*(.*?)" + _STOP, flat, re.I):
            res[key] += split_names(m.group(1), bb)
    return _dedupe(res)


def extract_votes_permember(tail, bb):
    """Parse per-member 'NAME, YES; NAME, NO;' rolls (rare; first-name or surname)."""
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    flat = re.sub(r"\s+", " ", tail)
    pairs = re.findall(r"\b([A-Z][a-zA-Z'’]+)\s*,\s*(YES|AYE|NO|NAY|ABSTAIN(?:ED)?|ABSENT)\b",
                       flat, re.I)
    if len(pairs) < 2:
        return res
    for tok, vote in pairs:
        up = tok.upper()
        person = _surname_to_canon(VARIANTS.get(up, up), bb) or FIRSTNAME.get(up)
        if not person:
            continue
        vu = vote.upper()
        bucket = ("aye" if vu in ("YES", "AYE") else "nay" if vu in ("NO", "NAY")
                  else "absent" if vu == "ABSENT" else "abstain")
        res[bucket].append(person)
    return _dedupe(res)


def extract_votes_structured(tail, bb):
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    flat = re.sub(r"\s+", " ", tail)
    labels = [("aye", r"Yes"), ("nay", r"No"), ("abstain", r"Abstain(?:ed)?"),
              ("absent", r"Absent"), ("recuse", r"Recus(?:ed|al)?")]
    for key, lab in labels:
        for m in re.finditer(
            rf"\b{lab}\s*:\s*(.*?)(?=(?:\s*(?:Yes|No|Absent|Abstain|Recus|"
            rf"Motion|Second)\b\s*[:\.])|$)", flat, re.I):
            blob = re.split(r"\.\s", m.group(1))[0]
            if re.match(r"^\s*(none|n/?a)\b", blob, re.I):
                continue
            res[key] += split_names(blob, bb)
    return _dedupe(res)


def _dedupe(res):
    for k in res:
        seen, out = set(), []
        for n in res[k]:
            if n not in seen:
                seen.add(n)
                out.append(n)
        res[k] = out
    specific = set(res["nay"]) | set(res["abstain"]) | set(res["recuse"]) | set(res["absent"])
    res["aye"] = [n for n in res["aye"] if n not in specific]
    return res


# ---- mover / seconder --------------------------------------------------------
def extract_mover_seconder(block, bb):
    mover = seconder = None
    m = re.search(COMM_ROLE + r"\s+[A-Z][A-Za-z’']+(?:\s+[A-Z][A-Za-z’']+)?\s+"
                  r"(?:MOTIONED|MOVED|MADE\s+A\s+MOTION|NOMINATED)", block, re.I)
    if m:
        mover = norm_name(m.group(0), bb)
    if mover is None:
        m = re.search(r"Motion:\s*(.*?)\s+(?:motioned|moved|made\s+a\s+motion|nominated)",
                      block, re.I)
        if m:
            mover = norm_name(m.group(1).split(",")[-1], bb)
    m = re.search(COMM_ROLE + r"\s+[A-Z][A-Za-z’']+(?:\s+[A-Z][A-Za-z’']+)?\s+SECONDED",
                  block, re.I)
    if m:
        seconder = norm_name(m.group(0), bb)
    if seconder is None:
        m = re.search(r"Second(?:ed)?\s*:\s*([^\n,.]*)", block, re.I)
        if m:
            seconder = norm_name(m.group(1), bb)
    return mover, seconder


# ---- motion text -------------------------------------------------------------
def motion_text(block):
    m = re.search(r"Motion:\s*(.*?)(?:SECONDED|Second(?:ed)?\s*:|ROLL\s+|"
                  r"ALL\s+IN\s+FAVOR|\bVOTED\s+(?:AYE|YES|NAY|NO)|\bYes\s*:|\bNo\s*:)",
                  block, re.I | re.S)
    raw = m.group(1) if m else block[:400]
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r"^" + COMM_ROLE + r"\s+[A-Za-z’']+(?:\s+[A-Za-z’']+)?\s+"
                 r"(?:MOTIONED|MOVED|MADE\s+A\s+MOTION|NOMINATED)\s+(?:TO\s+)?",
                 "", raw, flags=re.I).strip()
    raw = re.sub(COMM_ROLE + r"\s+[A-Za-z’']+\s*$", "", raw, flags=re.I).strip()
    raw = raw.rstrip(". ").strip()
    if len(raw) > 300:
        raw = raw[:297].rstrip() + "..."
    return raw or "(motion text not captured)"


# ---- recommendation / final-action / procedural result encoding --------------
PROCEDURAL = re.compile(
    r"\bminutes\b|\bagenda\b|\badjourn|\brecess|reconvene|\bcontinue\b|\btable\b|"
    r"\bpostpone|\bexcuse|open\s+the\s+(public\s+hearing|meeting)|close\s+the\s+public\s+hearing|"
    r"public\s+hearing|elect|nominat|chair\s*-?\s*tempore|vacate|closed\s+session", re.I)
RECOMMEND = re.compile(r"\brecommend|\bforward", re.I)
NEGATIVE = re.compile(r"\bden(?:y|ial|ying|ied)\b|negative\s+recommend|recommend\w*\s+den|"
                      r"\bagainst\b|\bdisapprov", re.I)


def encode_result(motion, verb, yes, no):
    """Build the spec result string. yes/no are the final tallies (ints)."""
    tally = f"{yes}:{no}"
    is_proc = bool(PROCEDURAL.search(motion)) and not RECOMMEND.search(motion)
    is_rec = bool(RECOMMEND.search(motion))
    is_neg = bool(NEGATIVE.search(motion))
    passed = (verb != "Fail")
    if is_rec:
        direction = "Negative" if is_neg else "Positive"
        s = f"{direction} recommendation {tally}"
        if not passed:
            s += " (Failed)"
        return s
    if is_proc:
        return f"{tally} {'Pass' if passed else 'Fail'}"
    # final action
    if is_neg or not passed:
        s = f"{tally} Denied (Final Action)"
        if not passed:
            # keep the explicit carriage word — a FAILED approve motion can carry a
            # majority-looking tally under a majority-of-the-body rule ("THE MOTION
            # FAILED TO PASS" at 2:1, 2022-07-06; T3.1(m) 2026-07-12): without the
            # word, the db outcome_of trusts the tally and stores Pass.
            s += " — motion failed"
        return s
    return f"{tally} Approved (Final Action)"


# ---- per-file processing -----------------------------------------------------
def process_text(text):
    text = re.sub(r"(?m)^\s*Page \d+ of \d+;.*$", " ", text)
    # Clerk-typo motion header: "MOTION. Craig Bown made a motion ..." (period instead of
    # colon; seen only in the recovered 2023-06-21 minutes). Rewritten ONLY when UPPERCASE
    # "MOTION." starts a line AND is followed by a Mixed-Case name — wrap-continuation
    # lines ("... SECONDED THE\nMOTION. ROLL WENT AS FOLLOWS ...") are followed by CAPS
    # and never match (verified corpus-wide, 2026-07-02).
    text = re.sub(r"(?m)^(\s*)MOTION\s*\.(?=[ \t]+[A-Z][a-z]+[ \t])", r"\1Motion:", text)
    bb = resolve_blackburn(text)
    anchors = [m.start() for m in re.finditer(r"(?im)^\s*Motion\s*:", text)]
    votes = []
    motion_no = 0
    for j, start in enumerate(anchors):
        end = anchors[j + 1] if j + 1 < len(anchors) else len(text)
        block = text[start:end]
        # skip COUNCIL votes embedded in joint City Council + Planning Commission meetings
        # (the mover is a councilmember/mayor) — these are council actions, not PC motions.
        mline = re.search(r"Motion\s*:\s*(.{0,40}?)(?:MOVED|MOTIONED|MADE\s+A\s+MOTION|"
                          r"NOMINATED)", block, re.I)
        if mline and NONCOMM_ROLE.search(mline.group(1)):
            continue
        # cut the block at the result sentence (+a little) so we don't pull next item's names
        cut = re.search(r"(?:THE\s+)?(?:MOTION|VOTE)\s+(?:CARRIED|PASSED|FAILED|"
                        r"WAS\s+UNANIMOUS)[^\n]*?(?:\.|\n)", block, re.I)
        if not cut:
            cut = re.search(r"Motion\s+(?:Passed|Failed|Carried|Tied)[^\n]*", block, re.I)
        if not cut:
            cut = re.search(r"(?:passed|carried)\s+unanimously[^\n]*", block, re.I)
        if not cut:
            cut = re.search(r"NO\s+SECOND\s+WAS\s+OFFERED|FAILED\s+FOR\s+LACK|"
                            r"DIED\s+FOR\s+LACK", block, re.I)
        tail = block[: cut.end() + 80] if cut else block[:1500]

        is_structured = bool(re.search(r"\bYes\s*:", tail)) or bool(
            re.search(r"Motion\s+(Passed|Failed)\s+\d", tail, re.I))
        has_leading = bool(re.search(
            r"those\s+(?:who\s+)?vot|those\s+(?:who\s+)?opposed|those\s+in\s+favor|"
            r"all\s+(?:in\s+favor\s+)?voted|all\s+voted\s+in\s+favor|abstained\s+from\s+voting",
            tail, re.I))
        has_inline = bool(re.search(
            r"VOTED\s+(?:AYE|YES|NAY|NO)|VOTED\s+IN\s+(?:FAVOR|SUPPORT|THE\s+AFFIRMATIVE|"
            r"OPPOSITION|THE\s+NEGATIVE)|VOTED\s+AGAINST|ABSTAIN|(?:WAS|WERE)\s+(?:ABSENT|"
            r"EXCUSED)|RECUSED|CARRIED|PASSED|FAILED|UNANIMOUS|NO\s+SECOND\s+WAS\s+OFFERED",
            tail, re.I))
        if not (is_structured or has_leading or has_inline):
            continue

        mover, seconder = extract_mover_seconder(block, bb)
        verb, syes, sno = find_outcome(tail)

        vote_src = tail
        if re.search(r"CHANGED\s+(?:HER|HIS|THEIR)\s+VOTE", tail, re.I):
            rolls = list(re.finditer(r"ROLL\s+(?:CALL\s+)?WENT\s+AS\s+FOLLOW", tail, re.I))
            if rolls:
                vote_src = tail[rolls[-1].end():]

        if is_structured:
            lists = extract_votes_structured(vote_src, bb)
            if not any(lists.values()):
                lists = extract_votes_inline(vote_src, bb)
        else:
            # trailing-verb ("NAMES VOTED AYE"), leading-label ("Those voting aye: NAMES"),
            # and per-member ("NAME, YES;") are complementary; run and merge.
            inl = extract_votes_inline(vote_src, bb)
            led = extract_votes_leading(vote_src, bb)
            lists = {k: inl[k] + [n for n in led[k] if n not in inl[k]] for k in inl}
            if not any(lists[k] for k in ("aye", "nay", "abstain")):
                pm = extract_votes_permember(vote_src, bb)
                lists = {k: lists[k] + [n for n in pm[k] if n not in lists[k]] for k in lists}
            lists = _dedupe(lists)

        names_recorded = any(lists[k] for k in ("aye", "nay", "abstain"))
        mtext = motion_text(block)

        # N:N for the result string: use the SOURCE's stated tally when it gives an
        # explicit number (so the validator can flag a clerk's tally typo against the
        # named roll); otherwise fall back to the named count; else 0:0 (tally-only,
        # no number — never invented).
        ayes, nays = len(lists["aye"]), len(lists["nay"])
        if syes is not None:
            yes, no = syes, (sno if sno is not None else 0)
        elif names_recorded:
            yes, no = ayes, nays
        else:
            yes, no = 0, 0

        result = encode_result(mtext, verb, yes, no)

        motion_no += 1
        votes.append({
            "motion_no": motion_no, "body": BODY, "motion": mtext,
            "motion_type": classify(mtext), "result": result,
            "mover": mover, "seconder": seconder, "names_recorded": names_recorded,
            "aye": lists["aye"], "nay": lists["nay"], "abstain": lists["abstain"],
            "absent": lists["absent"], "recuse": lists["recuse"],
        })
    return votes, bb


# ---- driver ------------------------------------------------------------------
def read_index():
    rows = []
    with INDEX.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-extract even if JSON exists")
    args = ap.parse_args()

    rows = []
    roster = {}  # full name -> {"first": date, "last": date, "n": meetings present}
    summary = {"meetings": 0, "motions": 0, "named": 0, "tally_only": 0,
               "contested": 0, "member_rows": 0, "recommendations": 0,
               "final_actions": 0, "procedural": 0}

    for r in read_index():
        date = r["date"]
        md_path = ROOT / r["path"]
        if not md_path.exists():
            continue
        week = md_path.parent.name
        year = r["year"]
        out_json = VOTES_DIR / year / week / f"{date}_planning-commission-meeting.json"
        source = f"planning_commission/{r['path']}"

        text = md_path.read_text(encoding="utf-8", errors="replace")
        bb = resolve_blackburn(text)
        present, excused = attendance(text, bb)

        if out_json.exists() and not args.force:
            d = json.loads(out_json.read_text())
            votes = d["votes"]
            present = set(d.get("names_present", present))
        else:
            votes, _ = process_text(text)
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(
                {"date": date, "title": TITLE, "body": BODY, "source": source,
                 "names_present": sorted(present), "votes": votes},
                indent=2, ensure_ascii=False), encoding="utf-8")

        # participants = present-roster ∪ everyone who appears in a vote list (voting
        # implies presence; covers attendance-header formats the parser can't reach).
        voters = set()
        for v in votes:
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                voters.update(v[k])
        participants = present | voters
        for nm in participants:
            e = roster.setdefault(nm, {"first": date, "last": date, "n": 0})
            e["first"] = min(e["first"], date)
            e["last"] = max(e["last"], date)
            e["n"] += 1
        for nm in excused:  # extends tenure range but is not a meeting attended
            e = roster.setdefault(nm, {"first": date, "last": date, "n": 0})
            e["first"] = min(e["first"], date)
            e["last"] = max(e["last"], date)

        summary["meetings"] += 1
        for v in votes:
            summary["motions"] += 1
            res = v["result"]
            if "recommend" in res.lower():
                summary["recommendations"] += 1
            elif "(Final Action)" in res:
                summary["final_actions"] += 1
            else:
                summary["procedural"] += 1
            if v["names_recorded"]:
                summary["named"] += 1
            else:
                summary["tally_only"] += 1
            if v["nay"] or v["abstain"]:
                summary["contested"] += 1
            for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                               ("absent", "Absent"), ("recuse", "Recuse")):
                for nm in v[key]:
                    summary["member_rows"] += 1
                    rows.append({
                        "date": date, "year": year, "title": TITLE, "body": BODY,
                        "motion_no": v["motion_no"], "motion": v["motion"],
                        "motion_type": v["motion_type"], "result": v["result"],
                        "mover": v["mover"] or "", "seconder": v["seconder"] or "",
                        "member": nm, "vote": label, "source": source,
                    })

    rows.sort(key=lambda x: (x["date"], x["motion_no"], x["member"]))
    with ALL_VOTES_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "year", "title", "body", "motion_no",
                                          "motion", "motion_type", "result", "mover",
                                          "seconder", "member", "vote", "source"])
        w.writeheader()
        w.writerows(rows)

    with ROSTER_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(roster, key=lambda n: (roster[n]["first"], n)):
            e = roster[nm]
            w.writerow([nm, e["first"], e["last"], e["n"]])

    summary["distinct_commissioners"] = len(roster)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
