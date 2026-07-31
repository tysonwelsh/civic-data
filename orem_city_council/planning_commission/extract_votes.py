#!/usr/bin/env python3
"""
Orem CITY PLANNING COMMISSION vote extractor.

PURE PYTHON / REGEX. No LLM, no network. Reads planning_commission/minutes_index.csv and
the markdown minutes under planning_commission/minutes/<year>/<week-monday>/<date>_<slug>.md,
and produces, per meeting, a JSON of recorded Planning Commission votes
(planning_commission/votes/<year>/<week>/<date>_planning-commission-meeting.json), then
rebuilds planning_commission/all_votes.csv (long format, one row per member-vote) and
planning_commission/roster.csv.

Orem PC records each motion in prose. THREE recorded formats are handled:

  (A) Classic prose roll-call (2020-2024 + OCR + docx):
      "Planning Commission Action: Jim Condie moved to vacate Lot 1 ... Amber Pope seconded
       the motion. Those voting aye: Haysam Sakar, Jim Condie, ... and Murray Low. The motion
       passed unanimously."
      ("Those voting nay:" / "Those abstaining:" appear when contested.)

  (B) Late-2025/2026 labelled-block roll-call (YES:/NO:/ABSTAIN:):
      "Planning Commission Action: Vice Chair Mike Carpenter motioned to approve ... Rod
       Erickson seconded the motion.  YES: Madeline Komen, Mike Carpenter, ...  NO: None
       ABSTAIN: None"
      (Outcome may be a separate sentence -- "the motion failed" under a supermajority rule --
       or absent, in which case majority of the recorded names decides pass/fail.)

  (C) Mid-2025 summary minutes (tally-only, NO per-member names):
      "Commissioner Hawkes made the motion, and Commissioner Carpenter seconded. The motion
       passed unanimously."  /  "Vote: Passed unanimously."
      Recorded names_recorded=False, EMPTY member lists (CARDINAL RULE: never guess who voted).

result column (machine-detectable PC disposition; documented in CLAUDE.md):
  - recommendation to City Council (rezone/plat/subdivision/GP amendment/annexation/ordinance):
        "Positive recommendation A:N" / "Negative recommendation A:N" / "Neutral recommendation A:N"
  - final action by the PC itself (conditional use / site plan / plat approval, etc.):
        "A:N Approved (Final Action)" / "A:N Denied (Final Action)"
  - procedural (minutes / continue / adjourn / officer election / consent):
        "A:N Pass" / "A:N Fail"
  Tally-only motions (format C) drop the "A:N" and keep just the word(s).

Run from anywhere:  python3 planning_commission/extract_votes.py
"""

import csv
import json
import os
import re

# ---------------------------------------------------------------- paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # planning_commission/
REPO_ROOT = os.path.dirname(SCRIPT_DIR)                          # orem_city_council/
MINUTES_DIR = os.path.join(SCRIPT_DIR, "minutes")
VOTES_DIR = os.path.join(SCRIPT_DIR, "votes")
INDEX_CSV = os.path.join(SCRIPT_DIR, "minutes_index.csv")
ALL_VOTES_CSV = os.path.join(SCRIPT_DIR, "all_votes.csv")
ROSTER_CSV = os.path.join(SCRIPT_DIR, "roster.csv")
VALIDATION_TXT = os.path.join(VOTES_DIR, "_validation_report.txt")

TITLE = "Planning Commission"
BODY = "PlanningCommission"

# ---------------------------------------------------------------- name normalization
# PC minutes give FULL names in the roll-call lists, so vote-list members are taken verbatim
# (only spelling/OCR drift folded). Movers/seconders are often titled short forms
# ("Mr. Roberts", "Commissioner Erickson", "Vice Chair Carpenter") -> resolved by surname.
FULLNAME_VARIANTS = {
    "haysam sakar": "Haysam Sakar", "haysam saakar": "Haysam Sakar",
    "haysatn sakar": "Haysam Sakar", "haysam sakar via zoom": "Haysam Sakar",
    "madeline komen": "Madeline Komen",
    "barry roberts": "Barry Roberts",
    "gerald crismon": "Gerald Crismon", "jerry crismon": "Gerald Crismon",
    "gerald crimson": "Gerald Crismon", "jerry crimson": "Gerald Crismon",
    "mickey cochran": "Mickey Cochran",
    "james hawkes": "James Hawkes", "jim hawkes": "James Hawkes",
    "james jim hawkes": "James Hawkes",
    "murray low": "Murray Low", "murry low": "Murray Low",
    "ross spencer": "Ross Spencer",
    "carl cook": "Carl Cook",
    "mike carpenter": "Mike Carpenter", "michael carpenter": "Mike Carpenter",
    "camille jensen": "Camille Jensen",
    "helena kleinlein": "Helena Kleinlein",
    "marisa bentley": "Marisa Bentley",
    "mike staker": "Mike Staker", "michael staker": "Mike Staker",
    "shauna mecham": "Shauna Mecham",
    "tina okolowitz": "Tina Okolowitz",
    "jim condie": "Jim Condie", "james condie": "Jim Condie", "jim condig": "Jim Condie",
    "amber pope": "Amber Pope",
    "rod erickson": "Rod Erickson", "rod erikson": "Rod Erickson",
    "rodney erickson": "Rod Erickson",
    "britton runolfson": "Britton Runolfson",
    # 2026 commission (near-complete turnover); OCR spelling drift folded
    "darren hawkins": "Darren Hawkins",
    "jeff reeves": "Jeff Reeves", "jeffrey reeves": "Jeff Reeves",
    "susan madsen": "Susan Madsen",
    "karl radmall": "Karl Radmall", "karl radmill": "Karl Radmall",
    "micah ladle": "Micah Ladle", "micah ladel": "Micah Ladle",
}
SURNAME_CANON = {
    "sakar": "Haysam Sakar", "saakar": "Haysam Sakar",
    "komen": "Madeline Komen",
    "roberts": "Barry Roberts",
    "crismon": "Gerald Crismon", "crimson": "Gerald Crismon", "grismon": "Gerald Crismon",
    "cochran": "Mickey Cochran",
    "hawkes": "James Hawkes",
    "low": "Murray Low",
    "spencer": "Ross Spencer",   # Ross is the only Planning Commissioner named Spencer;
                                 # liaison "Dave Spencer" never moves/seconds/votes in PC.
    "cook": "Carl Cook",
    "carpenter": "Mike Carpenter",
    "jensen": "Camille Jensen",
    "kleinlein": "Helena Kleinlein",
    "bentley": "Marisa Bentley",
    "staker": "Mike Staker",
    "mecham": "Shauna Mecham",
    "okolowitz": "Tina Okolowitz",
    "condie": "Jim Condie",
    "pope": "Amber Pope",
    "erickson": "Rod Erickson", "erikson": "Rod Erickson",
    "runolfson": "Britton Runolfson",
    "hawkins": "Darren Hawkins",
    "reeves": "Jeff Reeves",
    "madsen": "Susan Madsen",
    "radmall": "Karl Radmall", "radmill": "Karl Radmall",
    "ladle": "Micah Ladle", "ladel": "Micah Ladle",
}
# canonical commissioner set (for surname-uniqueness / roster membership)
COMMISSIONERS = set(SURNAME_CANON.values())

# Non-commissioners that must never be emitted as a voting member: council liaisons,
# staff, legal counsel whose names can leak into a mover/seconder capture.
NON_COMMISSIONERS = {
    "dave spencer", "david spencer", "crystal muhlestein", "terry peterson",
    "ryan clark", "ryan l clark", "jason bench", "jason w bench", "steve earl",
    "aaron mcknight", "jared hall", "grant allen", "grace bjarnson",
    "rebecca gourley", "gary mcginn", "cheryl vargas", "rachel stevens",
    "matt taylor", "kathi lewis", "nate prescott", "sam kelly",
}

TITLE_RE = re.compile(
    r"^(vice[\s\-]+chair|chairman|chairwoman|chairperson|chair|commissioner|"
    r"mr|mrs|ms|miss|dr|councilmember)\b[.\s]*", re.I)

ZW = dict.fromkeys(map(ord, "​‌‍‎‏﻿ "), None)


def clean_text(s):
    s = s.translate(ZW)
    s = s.replace(" ", " ")
    s = s.replace("**", "").replace("__", "")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return s


def _strip_titles(n):
    prev = None
    while n and n != prev:
        prev = n
        n = TITLE_RE.sub("", n).strip()
    return n


_FIRST_TO_FULL = {}
for _sur, _full in SURNAME_CANON.items():
    _FIRST_TO_FULL.setdefault(_full.split()[0].lower(), _full)


def normalize_name(raw):
    """Map a raw name token to a canonical commissioner name; None if junk/non-member."""
    if not raw:
        return None
    n = clean_text(raw).strip()
    n = re.sub(r"\((?:via\s+)?[^)]*\)", " ", n, flags=re.I)   # drop "(via Zoom)" etc.
    n = n.strip().strip(".,;:")
    n = _strip_titles(n)
    n = re.sub(r"\b(jr|sr|ii|iii|iv|esq)\.?$", "", n, flags=re.I).strip().strip(".,;:")
    if not n:
        return None
    key = re.sub(r"[^a-z ]", "", n.lower()).strip()
    key = re.sub(r"\s+", " ", key)
    if not key:
        return None
    if key in NON_COMMISSIONERS:
        return None
    if key in FULLNAME_VARIANTS:
        return FULLNAME_VARIANTS[key]
    tokens = [t for t in re.split(r"\s+", n) if t]
    # surname = last alpha token
    surname = re.sub(r"[^a-z]", "", tokens[-1].lower()) if tokens else ""
    if surname in SURNAME_CANON:
        cand = SURNAME_CANON[surname]
        # Full-name gate: reject the fold only when the preceding first name belongs to
        # a DIFFERENT known member (real shared-surname collision), not for a nickname
        # (nicknames are already folded via FULLNAME_VARIANTS above). No-op today.
        if len(tokens) >= 2:
            pfx = re.sub(r"[^a-z]", "", tokens[-2].lower())
            cf = cand.split()[0].lower()
            other = _FIRST_TO_FULL.get(pfx)
            if (len(pfx) > 1 and pfx != cf and not cf.startswith(pfx)
                    and other is not None and other != cand):
                return " ".join(w.capitalize() for w in tokens)
        return cand
    for tok in tokens:
        k = re.sub(r"[^a-z]", "", tok.lower())
        if k in SURNAME_CANON:
            return SURNAME_CANON[k]
    # Unknown name: keep only if it is a plausible full (>=2 token) human name; drop bare
    # single tokens ("Br", stray titles) so we never emit a bogus member.
    real_tokens = [t for t in tokens if len(re.sub(r"[^a-zA-Z]", "", t)) >= 2]
    if len(real_tokens) < 2:
        return None
    return " ".join(w.capitalize() for w in real_tokens)


STOPWORDS = {"the", "and", "of", "to", "a", "an", "in", "on", "for", "with", "city",
             "council", "commission", "motion", "passed", "failed", "minutes", "video",
             "meeting", "section", "code", "ordinance", "resolution", "as", "that", "this",
             "by", "or", "at", "draft", "presented", "page", "those", "voting", "aye",
             "nay", "yes", "no", "none", "abstain", "abstaining", "planning", "recommendation",
             "positive", "negative", "neutral", "forward", "forwarded", "vote"}


def looks_like_name(part):
    p = part.strip().strip(".")
    if not p:
        return False
    if p.lower() in ("none", "n/a", "na", "no one", "nobody", "unanimous"):
        return False
    if any(ch.isdigit() for ch in p):
        return False
    p2 = re.sub(r"\((?:via\s+)?[^)]*\)", " ", p, flags=re.I)
    tokens = [t for t in re.split(r"\s+", p2) if t]
    if not tokens or len(tokens) > 4:
        return False
    for t in tokens:
        bare = re.sub(r"[^a-zA-Z]", "", t)
        if len(bare) <= 1:
            continue
        if bare.lower() in STOPWORDS:
            return False
    if not any(t[:1].isupper() for t in tokens):
        return False
    return True


def split_names(blob):
    """Split 'A, B, C and D' into canonical commissioner names (drops junk, never invents)."""
    if not blob:
        return []
    blob = clean_text(blob).strip()
    if blob.lower().startswith("none"):
        return []
    # protect initials and honorific periods from the sentence cut
    guarded = re.sub(r"\b([A-Z])\.", r"\1<DOT>", blob)
    guarded = re.sub(r"\b(Mr|Mrs|Ms|Miss|Dr)\.", r"\1<DOT>", guarded, flags=re.I)
    cut = re.search(r"\.\s", guarded)
    if cut:
        guarded = guarded[:cut.start()]
    blob = guarded.replace("<DOT>", ".")
    blob = re.sub(r"\s+and\s+", ", ", blob)
    blob = re.sub(r"\s*&\s*", ", ", blob)
    out, seen = [], set()
    for p in blob.split(","):
        if not looks_like_name(p):
            continue
        nm = normalize_name(p)
        if nm and nm not in seen:
            seen.add(nm)
            out.append(nm)
    return out


def resolve_actor(capture):
    """Resolve a (possibly noisy) mover/seconder capture to a canonical commissioner."""
    if not capture:
        return ""
    cap = clean_text(capture).strip()
    cap = re.sub(r"\((?:via\s+)?[^)]*\)", " ", cap, flags=re.I)
    if ". " in cap:
        cap = re.split(r"\.\s+(?=[A-Z])", cap)[-1]
    cap = _strip_titles(cap)
    tokens = [t for t in re.split(r"\s+", cap) if t]
    # scan right-to-left for a known surname
    for tok in reversed(tokens):
        k = re.sub(r"[^a-z]", "", tok.lower())
        if k in SURNAME_CANON:
            return SURNAME_CANON[k]
    tail = " ".join(tokens[-3:]) if len(tokens) >= 2 else (tokens[-1] if tokens else "")
    return normalize_name(tail) or ""


# ---------------------------------------------------------------- footers / flatten
FOOTER_PATTERNS = [
    r"A complete video of the meeting can be found at www\.orem\.org\S*",
    r"A recording of (?:the|this) (?:meeting|discussion)[^.]*?(?:can be )?(?:viewed|found)[^.]*?(?:online[^.]*?)?(?:https?://\S+)?",
    r"https?://www\.youtube\.com/\S+",
    r"https?://\S*youtu\.be/\S+",
    r"Orem\.gov/meetings",
    r"Planning Commission minutes for [A-Z][a-z]+ \d{1,2},? \d{4}",
]
FOOTER_RE = re.compile("|".join(FOOTER_PATTERNS), re.I)
# Late-2025 all-caps page header "MINUTES FOR DECEMBER 17, 2025". Case-SENSITIVE and
# line-anchored so it never eats a lowercase "minutes for <date>" inside a real motion
# ("moved to approve the meeting minutes for January 15, 2020").
PAGE_HEADER_RE = re.compile(r"^\s*MINUTES FOR [A-Z]+ \d{1,2},? \d{4}\s*$", re.M)


def flatten(text):
    t = PAGE_HEADER_RE.sub(" ", text)
    t = FOOTER_RE.sub(" ", t)
    t = re.sub(r"\bDRAFT\b", " ", t)
    t = re.sub(r"\(p\.?\s*\d+\)|\(pg\.?\s*\d+\)", " ", t, flags=re.I)
    t = re.sub(r"^\s*\d{1,3}\s*$", " ", t, flags=re.M)        # bare page-number lines
    t = re.sub(r"\s+", " ", t)
    return t


# ---------------------------------------------------------------- headings
HEADING_KEYWORDS = ("PUBLIC HEARING", "PRELIMINARY PLAT", "FINAL PLAT", "PLAT AMENDMENT",
                    "SITE PLAN", "CONDITIONAL USE", "GENERAL PLAN", "ANNEXATION",
                    "REZONE", "ELECTION", "CONSENT", "ACTION ITEM", "AGENDA ITEM",
                    "ORDINANCE", "MINUTES", "SCHEDULED ITEM")


def is_heading(line):
    s = clean_text(line).strip(" -•\t#")
    if len(s) < 4:
        return False
    if re.search(r"those voting|moved|motioned|seconded|motion (passed|failed)", s, re.I):
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio > 0.7 and len(s) < 200:
        return True
    if re.match(r"^(Agenda Item|Action Item)\b", s, re.I):
        return True
    if any(s.upper().startswith(k) for k in HEADING_KEYWORDS):
        return True
    return False


def locate_headings(raw_lines, flat):
    located, cursor = [], 0
    for ln in raw_lines:
        if not is_heading(ln):
            continue
        key = re.sub(r"\s+", " ", clean_text(ln).strip(" -•\t#"))
        if len(key) < 4:
            continue
        probe = key[:45]
        idx = flat.find(probe, cursor)
        if idx == -1:
            idx = flat.find(probe)
        if idx != -1:
            located.append((idx, key))
            cursor = idx + 1
    located.sort()
    return located


def nearest_heading(headings, pos):
    chosen = ""
    for off, txt in headings:
        if off <= pos:
            chosen = txt
        else:
            break
    return chosen


# ---------------------------------------------------------------- motion text / actors
MOVER_RE = re.compile(
    r"((?:Vice[\s\-]+Chair\s+|Chair\s+|Commissioner\s+|Chairman\s+|Mr\.?\s*|Ms\.?\s*|Mrs\.?\s*)?"
    r"[A-Z][A-Za-z.'()\-]*(?:\s+[A-Z][A-Za-z.'()\-]*){0,3})"
    r"\s+(?:then\s+|also\s+|subsequently\s+)?(?:moved|motioned|made\s+a\s+motion|made\s+the\s+motion)\b",
)
MOTION_MADE_BY_RE = re.compile(
    r"motion\s+was\s+made\s+by\s+((?:Commissioner\s+|Vice[\s\-]+Chair\s+|Chair\s+|Mr\.?\s*|Ms\.?\s*)?"
    r"[A-Z][A-Za-z.'\-]*(?:\s+[A-Z][A-Za-z.'\-]*){0,3})", re.I)
SECOND_BY_RE = re.compile(
    r"(?:seconded\s+by|second\s+from)\s+((?:Commissioner\s+|Vice[\s\-]+Chair\s+|Chair\s+|"
    r"Mr\.?\s*|Ms\.?\s*|Mrs\.?\s*)?[A-Z][A-Za-z.'\-]*(?:\s+[A-Z][A-Za-z.'\-]*){0,3})", re.I)
SECONDER_RE = re.compile(
    r"((?:Vice[\s\-]+Chair\s+|Chair\s+|Commissioner\s+|Mr\.?\s*|Ms\.?\s*|Mrs\.?\s*)?"
    r"[A-Z][A-Za-z.'\-]*(?:\s+[A-Z][A-Za-z.'\-]*){0,3})\s+seconded\b", re.I)


def find_mover(pre):
    cands = list(MOVER_RE.finditer(pre))
    if cands:
        return resolve_actor(cands[-1].group(1))
    mb = list(MOTION_MADE_BY_RE.finditer(pre))
    if mb:
        return resolve_actor(mb[-1].group(1))
    return ""


def find_seconder(pre):
    sb = SECOND_BY_RE.search(pre)
    if sb:
        return resolve_actor(sb.group(1))
    so = list(SECONDER_RE.finditer(pre))
    if so:
        return resolve_actor(so[-1].group(1))
    return ""


def parse_motion_text(pre):
    m = list(re.finditer(r"\b(?:moved|motioned|made\s+a\s+motion|made\s+the\s+motion)\b",
                         pre, re.I))
    if m:
        rest = pre[m[-1].end():]
    else:
        mb = MOTION_MADE_BY_RE.search(pre)
        if mb:
            rest = pre[mb.end():]
        else:
            # no actor+verb ("[Chair] called for a motion to approve the minutes ...
            # Mr. Staker seconded") -> take the text after the last "motion to" so the
            # motion text is the action, not a leaked roll-call name list.
            mt = list(re.finditer(r"\bmotion\s+to\b", pre, re.I))
            rest = pre[mt[-1].start():] if mt else pre
            rest = re.sub(r"^\s*motion\s+to\s+", "", rest, flags=re.I)
    # NB: case-SENSITIVE on purpose. Under re.I, "[A-Z]" also matches lowercase, so the
    # {0,3} name prefix would greedily swallow the motion's own last words
    # ("to adjourn. Mr. Cook seconded" -> "to "). Real seconder names are capitalized.
    rest = re.split(r"(?:[A-Z][\w.'\-]*\s+){0,3}[Ss]econded\b|[Ss]econded\s+by|"
                    r"[Ss]econd\s+from", rest)[0]
    rest = re.split(r"those voting|\bYES\s*:", rest, flags=re.I)[0]
    rest = re.sub(r"^\s*[,]?\s*", "", rest)
    rest = re.sub(r"^by\s+(an?\s+)?(ordinance|resolution)\s*,?\s*", r"by \2, ", rest, flags=re.I)
    rest = re.sub(r"^\s*to\s+", "", rest, flags=re.I)
    rest = clean_text(rest).strip().strip(".")
    rest = re.sub(r"\s+", " ", rest)
    rest = re.sub(r"[.,]?\s+(Mr|Mrs|Ms|Chair|Commissioner)\.?\s*$", "", rest).strip()
    rest = re.sub(r"\s+made(\s+and)?$", "", rest).strip()   # "... Plat made and" -> "... Plat"
    return rest[:400].strip()


# ---------------------------------------------------------------- classification
def classify_motion_type(heading, motion_text):
    blob = ((heading or "") + " " + (motion_text or "")).lower()
    t = (motion_text or "").lower()
    if re.search(r"\badjourn", t):
        return "Procedural/Administrative"
    if re.search(r"\b(elect|reelect|appoint|nominat)\w*\b.{0,40}(chair|vice[\s\-]?chair)"
                 r"|adjust the roles|(chair|vice[\s\-]?chair)\b.{0,20}\b(elect|nominat)", blob):
        return "Appointment"
    if re.search(r"\bminute[s]?\b", t) and re.search(r"approve|adopt|review", t):
        return "Procedural/Administrative"
    if re.search(r"\b(continue|continued|table|tabled|postpone|recess|excuse|reconsider|"
                 r"remove from the agenda|order of the agenda|consent agenda)\b", t):
        return "Procedural/Administrative"
    if re.search(r"\bannex", blob):
        return "Annexation"
    if re.search(r"general plan", blob):
        return "General Plan"
    if re.search(r"conditional use|\bcup\b", blob):
        return "Conditional Use"
    if re.search(r"site plan", blob):
        return "Site Plan"
    if re.search(r"\bplat\b|subdivision|\bvacat", blob):
        return "Plat/Subdivision"
    if re.search(r"rezon|zone change|zoning map|zone map|change the zone", blob):
        return "Rezone"
    if re.search(r"\bordinance\b|land use code|development code|\bamend\w*\b.{0,45}\b("
                 r"sections?|articles?|appendix|appendices|chapters?|city code|orem code|"
                 r"standard land use|development code)\b|text amendment", blob):
        return "Code/Ordinance Amendment"
    return "Other"


PROC_ACTION_RE = re.compile(
    r"\b(adjourn|continue|continued|table|tabled|postpone|recess|excuse|reconsider|"
    r"approve\s+the\s+(?:meeting\s+)?minutes|approve\s+minutes|consent agenda|"
    r"approve\s+the\s+agenda|approve\s+the\s+\w+\s+calendar|approve\s+the\s+calendar|"
    r"remove from the agenda|order of the agenda)\b", re.I)
APPOINT_ACTION_RE = re.compile(
    r"(elect|reelect|appoint|nominat)\w*.{0,40}(chair|vice[\s\-]?chair)|adjust the roles", re.I)
REC_RE = re.compile(r"\brecommend", re.I)
DENY_RE = re.compile(r"\b(deny|denial|denied|recommend\s+denial)\b", re.I)
APPROVE_RE = re.compile(r"\b(approve|approval|vacate|grant|adopt)\b", re.I)


def direction_of(text, window):
    # Polarity from the MOTION TEXT first (authoritative); only if absent, peek at the
    # immediate disposition sentence (first ~150 chars of the forward window) so a
    # "forward a recommendation ... Forwarded a neutral recommendation" reads correctly
    # without leaking the NEXT agenda item's "Staff recommends ... positive".
    for src in (text, window[:150]):
        b = src.lower()
        if "negative recommendation" in b or re.search(r"\bnegative\b.{0,20}recommend", b):
            return "Negative"
        if "neutral recommendation" in b or re.search(r"\bneutral\b.{0,20}recommend", b):
            return "Neutral"
        if "positive recommendation" in b or re.search(r"\bpositive\b.{0,20}recommend", b):
            return "Positive"
    return "Positive"


def compose_result(motion_text, window, passed, n_aye, n_nay, names_recorded):
    """Build the PC `result` string (action class + tally + disposition).

    The action CLASS (procedural / recommendation / final action) is decided on the MOTION
    TEXT only -- never the forward window -- so an adjacent item's "Staff recommends ..."
    cannot turn a final-action plat approval into a recommendation."""
    t = motion_text or ""
    tally = f"{n_aye}:{n_nay}" if names_recorded else ""
    # action class
    if APPOINT_ACTION_RE.search(t) or PROC_ACTION_RE.search(t):
        word = "Pass" if passed else "Fail"
        return (f"{tally} {word}").strip(), "Procedural"
    if REC_RE.search(t):
        d = direction_of(t, window)
        base = f"{d} recommendation"
        if tally:
            base += f" {tally}"
        if not passed:
            base += " (Failed)"
        # Orem PC's FOUR-CONCURRING-VOTES rule: a carried 3:2 / tied 3:3 forward goes
        # to Council as NO recommendation — the minutes say so explicitly ("Forwarded
        # a neutral recommendation", "forwarded ... with no recommendation", "Due to a
        # lack of four positive or negative votes"). Keep the proposed direction but
        # mark the forwarded recommendation neutral (T1.3 orem m921/m988/m1051,
        # 2026-07-12); db recommendation_of maps the marker to NULL.
        if re.search(r"neutral recommendation|with no recommendation|"
                     r"no recommendation to the (?:city )?council|"
                     r"lack of four (?:positive|negative)", window, re.I):
            base += " (forwarded neutral — four-concurring-votes rule)"
        return base.strip(), "Recommendation"
    # final action (PC itself approves/denies)
    motion_is_deny = bool(DENY_RE.search(t)) and not APPROVE_RE.search(t)
    if motion_is_deny:
        disp = "Denied" if passed else "Approved"
    else:
        disp = "Approved" if passed else "Denied"
    note = ""
    if not passed:
        note = ", motion failed" if not motion_is_deny else ", denial failed"
    out = f"{tally} {disp} (Final Action{note})".strip()
    return out, "Final Action"


# ---------------------------------------------------------------- outcome detection
FAIL_CUE_RE = re.compile(
    r"\b(?:the\s+)?motion[^.]{0,40}?(?:did\s+not\s+pass|failed|was\s+not\s+approved|"
    r"not\s+approved)\b|motion\s+to\s+reconsider\s+was\s+not\s+approved", re.I)
PASS_CUE_RE = re.compile(
    r"\b(?:the\s+)?motion[^.]{0,40}?(?:passed|carried|was\s+approved|was\s+adopted)\b|"
    r"\bpassed\s+unanimously\b|\ball\s+commissioners\s+voted\s+(?:yes|aye|in favor)\b|"
    r"\bvote:\s*passed\b", re.I)


def detect_outcome(window, n_aye, n_nay):
    """Return True(passed)/False(failed). Explicit cue wins; else majority of names."""
    fail = FAIL_CUE_RE.search(window)
    apass = PASS_CUE_RE.search(window)
    if fail and (not apass or fail.start() < apass.start()):
        return False
    if apass:
        return True
    return n_aye > n_nay


# ---------------------------------------------------------------- vote-block anchors
# Prose roll-call labels (case-insensitive).
AYE_LABEL_RE = re.compile(r"Those\s+voting\s+(?:aye|yes)\s*[:.]?", re.I)
NAY_LABEL_RE = re.compile(r"Those\s+voting\s+(?:nay|no)\s*[:.]?|(?<![A-Za-z])NO\s*:")
ABS_LABEL_RE = re.compile(r"Those\s+abstaining\s*[:.]?|Those\s+voting\s+abstain\w*\s*[:.]?|"
                          r"(?<![A-Za-z])ABSTAIN(?:ING)?\s*:")
# Bare labelled-block label (late-2025/2026). ALWAYS all-caps "YES:" -> case SENSITIVE and a
# colon required, so it never matches a lowercase "... yes." inside ordinary prose.
YES_LABEL_RE = re.compile(r"(?<![A-Za-z])YES\s*:")
LIST_END_RE = re.compile(
    r"Those\s+voting|Those\s+abstaining|(?<![A-Za-z])NO\s*:|(?<![A-Za-z])ABSTAIN|"
    r"(?<![A-Za-z])YES\s*:|(?:The\s+)?[Mm]otion\b|Planning Commission Action|"
    r"Agenda Item|Action Item|Adjourn|Final Meeting|\d\.\d")


def _take_list(text, start):
    end = LIST_END_RE.search(text, start)
    seg = text[start:end.start()] if end else text[start:start + 200]
    return seg


def extract_file(path, meeting):
    raw = open(path, encoding="utf-8", errors="replace").read()
    lines = raw.split("\n")
    flat = flatten(clean_text(raw))
    headings = locate_headings(lines, flat)

    collected = []
    named_spans = []

    # --- anchors: prose "Those voting aye/yes" + block "YES:"
    anchors = []
    for m in AYE_LABEL_RE.finditer(flat):
        anchors.append((m.start(), m.end(), "prose"))
    for m in YES_LABEL_RE.finditer(flat):
        anchors.append((m.start(), m.end(), "block"))
    anchors.sort()

    anchor_starts = [a[0] for a in anchors]

    for idx, (a_start, a_end, kind) in enumerate(anchors):
        next_anchor = anchor_starts[idx + 1] if idx + 1 < len(anchors) else len(flat)
        # aye list
        aye_seg = _take_list(flat, a_end)
        aye = split_names(aye_seg)
        # nay
        nay = []
        nm = NAY_LABEL_RE.search(flat, a_end, next_anchor)
        if nm:
            nay = split_names(_take_list(flat, nm.end()))
        # abstain
        abstain = []
        am = ABS_LABEL_RE.search(flat, a_end, min(next_anchor, a_end + 400))
        if am:
            abstain = split_names(_take_list(flat, am.end()))
        names_recorded = bool(aye or nay or abstain)
        if not names_recorded:
            continue
        block_end = max(a_end, nm.end() if nm else a_end, am.end() if am else a_end)
        named_spans.append((a_start, block_end))

        # outcome window: from block_end forward to next anchor (cap ~700 chars),
        # CUT at the next numbered agenda heading — an adjacent item's recap ("Due to
        # an insufficient number of votes, the motion on the item failed") must not
        # bleed a Fail onto this motion (T3.1(m) 2026-07-12: m1057/m1060 4:0 true
        # passes stored Fail).
        out_win = flat[block_end:min(next_anchor, block_end + 700)]
        hcut = re.search(r"\b\d{1,2}\.\d{1,2}\s+[A-Z]{3,}", out_win)
        if hcut:
            out_win = out_win[:hcut.start()]
        passed = detect_outcome(out_win, len(aye), len(nay))

        # preceding window for mover/seconder/motion text
        prev_end = named_spans[-2][1] if len(named_spans) >= 2 else 0
        win_start = max(prev_end, a_start - 1600)
        pre = flat[win_start:a_start]
        pca = list(re.finditer(r"Planning Commission Action|DRC Action", pre))
        if pca:
            pre = pre[pca[-1].start():]
        mover = find_mover(pre)
        seconder = find_seconder(pre)
        motion_text = parse_motion_text(pre)
        heading = nearest_heading(headings, a_start)
        if not motion_text or len(motion_text) < 4:
            motion_text = heading
        rec_window = pre[-400:] + " " + out_win
        result, action_class = compose_result(
            motion_text, rec_window, passed, len(aye), len(nay), True)
        motion_type = classify_motion_type(heading, motion_text)

        collected.append((a_start, {
            "motion": motion_text, "body": BODY, "motion_type": motion_type,
            "action_class": action_class, "result": result, "outcome": "Passed" if passed else "Failed",
            "mover": mover, "seconder": seconder, "names_recorded": True,
            "aye": aye, "nay": nay, "abstain": abstain, "absent": [], "recuse": [],
        }))

    # --- tally-only pass (formats C / summary): a motion with NO per-member roll-call list.
    # Anchored on the outcome cue ("(The) Motion ... passed/failed", "Vote: Motion passed").
    # Covers both "<Name> moved ... seconded ... Motion passed unanimously" and the anonymous
    # "Motion (to <text>) made and seconded ... Motion passed 5-0." A numeric tally, when the
    # minutes print one, is captured into result; member names are NEVER invented
    # (names_recorded=False, empty member lists) per the CARDINAL RULE.
    TALLY_OUTCOME_RE = re.compile(
        r"(?:Vote\s*:\s*)?(?:The\s+)?\bMotion\b[^.]{0,50}?"
        r"\b(passed|failed|carried|did\s+not\s+pass|was\s+approved|was\s+denied|"
        r"was\s+not\s+approved)\b(?P<tail>[^.]{0,30})", re.I)
    NUM_TALLY_RE = re.compile(r"(\d{1,2})\s*(?:[-:]|to|-)\s*(\d{1,2})")
    for m in TALLY_OUTCOME_RE.finditer(flat):
        s, e = m.start(), m.end()
        if any(ns <= s < ne or ns < e <= ne or (s <= ns and e >= ne) for ns, ne in named_spans):
            continue
        # skip if this outcome cue is the trailing "The motion passed" of a named roll-call
        # block we already captured (its named_span ends just before this cue).
        if any(s - ne <= 300 and ne <= s for _, ne in named_spans):
            continue
        # require a 'second' within the preceding ~500 chars to confirm a real motion
        prev_named_end = max([ne for _, ne in named_spans if ne <= s] + [0])
        back = flat[max(prev_named_end, s - 500):s]
        if not re.search(r"second", back, re.I):
            continue
        outcome_word = m.group(1).lower()
        passed = outcome_word not in ("failed", "did not pass", "did  not  pass",
                                      "was not approved") and "not" not in outcome_word
        if "did not pass" in m.group(0).lower() or "not approved" in m.group(0).lower():
            passed = False
        # numeric tally if printed
        n_aye = n_nay = None
        mt = NUM_TALLY_RE.search(m.group("tail"))
        if mt:
            n_aye, n_nay = int(mt.group(1)), int(mt.group(2))
        mover = find_mover(back)
        seconder = find_seconder(back)
        motion_text = parse_motion_text(back)

        def _bad(txt):
            # reject a fragment that isn't a real motion clause (starts non-alpha, is a
            # leaked "present:" roster list, etc.)
            if not txt or len(txt) < 4 or not txt[0].isalpha():
                return True
            return txt.count(",") >= 2 and not re.search(
                r"\b(approve|continue|adjourn|recommend|vacate|amend|deny|adopt|elect|"
                r"table|postpone|reconsider|forward)\b", txt, re.I)

        if _bad(motion_text):
            mm = re.search(r"[Mm]otion(?:\s+made(?:\s+and\s+seconded)?)?\s+to\s+"
                           r"(.{3,120}?)(?:\.\s|\bmade\b|\bwas\s+made\b|\bseconded\b)", back)
            if not mm:
                mm = re.search(r"\bto\s+(approve|continue|adjourn|recommend|vacate|amend|"
                               r"deny|adopt|reconsider|forward)\b(.{0,110})", back)
            if mm:
                motion_text = clean_text(" ".join(g for g in mm.groups() if g)).strip(" .")
        heading = nearest_heading(headings, s)
        if _bad(motion_text):
            motion_text = heading
        has_tally = n_aye is not None
        result, action_class = compose_result(
            motion_text, "", passed, n_aye or 0, n_nay or 0, has_tally)
        if not has_tally:
            # strip the leading "0:0 " that compose_result would not have added (it didn't,
            # since has_tally False -> tally ""). result already has no tally. ok.
            pass
        motion_type = classify_motion_type(heading, motion_text)
        collected.append((s, {
            "motion": motion_text, "body": BODY, "motion_type": motion_type,
            "action_class": action_class, "result": result,
            "outcome": "Passed" if passed else "Failed",
            "mover": mover, "seconder": seconder, "names_recorded": False,
            "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": [],
        }))

    collected.sort(key=lambda x: x[0])
    votes = []
    for i, (_, v) in enumerate(collected, start=1):
        vv = {"motion_no": i}
        vv.update(v)
        votes.append(vv)

    return {
        "date": meeting["date"], "title": TITLE, "body": BODY,
        "source": meeting["path"], "format": meeting.get("format", ""),
        "votes": votes,
    }


# ---------------------------------------------------------------- attendance roster
PRESENT_RE = re.compile(r"Those\s+present\s*:?(.*?)(?:Planning Commission|;|\n\n)", re.I | re.S)
EXCUSED_RE = re.compile(r"Those\s+excused\s*:?(.*?)(?:Planning Commission|;|\n\n)", re.I | re.S)


def attendance_members(raw):
    found = set()
    flat = re.sub(r"\s+", " ", clean_text(raw))
    for rx in (PRESENT_RE, EXCUSED_RE):
        for m in rx.finditer(flat):
            for nm in split_names(m.group(1)):
                found.add(nm)
    return found


# ---------------------------------------------------------------- appointment cross-check
def pc_appointments_from_council():
    path = os.path.join(REPO_ROOT, "meeting_minutes", "all_votes.csv")
    appts = {}
    if not os.path.exists(path):
        return appts
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            motion = r.get("motion", "")
            if re.search(r"to the planning commission", motion, re.I) and \
               re.search(r"appoint|reappoint", motion, re.I):
                m = re.search(r"appoint(?:ing|ed)?\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3})\s+to the [Pp]lanning",
                              motion)
                if m:
                    nm = normalize_name(m.group(1))
                    if nm:
                        appts.setdefault(nm, r.get("date", ""))
    return appts


# ---------------------------------------------------------------- driver
def week_from_path(path):
    parts = path.replace("\\", "/").split("/")
    try:
        i = parts.index("minutes")
        return parts[i + 1], parts[i + 2], parts[i + 3]
    except (ValueError, IndexError):
        return None, None, None


def main():
    with open(INDEX_CSV, newline="", encoding="utf-8") as f:
        index = list(csv.DictReader(f))

    all_rows = []
    motion_records = []
    roster = {}            # year -> set members
    member_stats = {}      # member -> dict(years,aye,nay,abstain,motions,first,last,via)
    attendance_only = {}   # member -> set years (seen in attendance but never in a vote)
    meetings_parsed = 0
    motions = 0
    member_rows = 0
    named = 0
    tally_only = 0
    contested = 0
    recommendations = 0
    final_actions = 0
    ocr_meetings = 0
    by_type = {}
    by_format = {}
    meetings_without_votes = []

    for meeting in index:
        rel = meeting["path"]
        abspath = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(abspath):
            continue
        year, week, fname = week_from_path(rel)
        if year is None:
            continue
        yr = int(year)
        fmt = meeting.get("format", "")
        by_format[fmt] = by_format.get(fmt, 0) + 1
        if fmt == "ocr":
            ocr_meetings += 1

        result = extract_file(abspath, meeting)
        meetings_parsed += 1

        out_dir = os.path.join(VOTES_DIR, year, week)
        os.makedirs(out_dir, exist_ok=True)
        json_name = fname.replace(".md", ".json")
        with open(os.path.join(out_dir, json_name), "w", encoding="utf-8") as jf:
            json.dump(result, jf, indent=1, ensure_ascii=False)

        if not result["votes"]:
            meetings_without_votes.append(meeting["date"])

        # attendance roster (commissioners present/excused)
        raw = open(abspath, encoding="utf-8", errors="replace").read()
        att = attendance_members(raw)

        voted_members_this_meeting = set()
        for v in result["votes"]:
            motions += 1
            by_type[v["motion_type"]] = by_type.get(v["motion_type"], 0) + 1
            if v["action_class"] == "Recommendation":
                recommendations += 1
            elif v["action_class"] == "Final Action":
                final_actions += 1
            if v["names_recorded"]:
                named += 1
            else:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            motion_records.append({
                "date": result["date"], "motion_no": v["motion_no"], "result": v["result"],
                "outcome": v["outcome"], "names_recorded": v["names_recorded"],
                "aye": v["aye"], "nay": v["nay"], "abstain": v["abstain"],
                "action_class": v["action_class"],
            })
            roster.setdefault(yr, set())
            for vk, vlabel in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                               ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v[vk]:
                    roster[yr].add(member)
                    voted_members_this_meeting.add(member)
                    member_rows += 1
                    st = member_stats.setdefault(member, {
                        "years": set(), "Aye": 0, "Nay": 0, "Abstain": 0,
                        "motions": 0, "first": result["date"], "last": result["date"]})
                    st["years"].add(yr)
                    st[vlabel] = st.get(vlabel, 0) + 1
                    if vlabel in ("Aye", "Nay", "Abstain"):
                        st["motions"] += 1
                    st["first"] = min(st["first"], result["date"])
                    st["last"] = max(st["last"], result["date"])
                    all_rows.append({
                        "date": result["date"], "year": year, "title": TITLE, "body": BODY,
                        "motion_no": v["motion_no"], "motion": v["motion"],
                        "motion_type": v["motion_type"], "result": v["result"],
                        "mover": v["mover"], "seconder": v["seconder"],
                        "member": member, "vote": vlabel, "source": rel,
                    })
        # attendance-only members (present but never appeared in a recorded vote anywhere)
        for nm in att:
            if nm in COMMISSIONERS or len(nm.split()) >= 2:
                attendance_only.setdefault(nm, set()).add(yr)

    # rebuild all_votes.csv
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    all_rows.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    # roster.csv
    appts = pc_appointments_from_council()
    voted_members = set(member_stats)
    all_members = set(member_stats) | {m for m in attendance_only if m in COMMISSIONERS
                                       or m in voted_members}
    # only keep attendance-only names that are recognized commissioners (avoid staff leakage)
    roster_members = set(member_stats) | (set(attendance_only) & COMMISSIONERS)
    rcols = ["member", "first_year", "last_year", "years_active", "vote_motions",
             "aye", "nay", "abstain", "in_recorded_votes", "council_appointment_date"]
    with open(ROSTER_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rcols)
        w.writeheader()
        for m in sorted(roster_members):
            st = member_stats.get(m)
            yrs = set()
            if st:
                yrs |= st["years"]
            yrs |= attendance_only.get(m, set())
            yrs = sorted(yrs)
            w.writerow({
                "member": m,
                "first_year": yrs[0] if yrs else "",
                "last_year": yrs[-1] if yrs else "",
                "years_active": ";".join(str(y) for y in yrs),
                "vote_motions": st["motions"] if st else 0,
                "aye": st["Aye"] if st else 0,
                "nay": st["Nay"] if st else 0,
                "abstain": st["Abstain"] if st else 0,
                "in_recorded_votes": "true" if st else "false",
                "council_appointment_date": appts.get(m, ""),
            })

    distinct = len(roster_members)
    print(f"pc_meetings_parsed={meetings_parsed}")
    print(f"motions={motions}")
    print(f"member_vote_rows={member_rows}")
    print(f"named_rollcall_motions={named}")
    print(f"tally_only_motions={tally_only}")
    print(f"contested_motions={contested}")
    print(f"recommendations={recommendations}")
    print(f"final_actions={final_actions}")
    print(f"ocr_meetings={ocr_meetings}")
    print(f"distinct_commissioners={distinct}")
    print(f"meetings_without_votes={len(meetings_without_votes)} {meetings_without_votes}")
    print("by_format=" + json.dumps(by_format))
    print("by_motion_type=" + json.dumps(by_type))
    print("roster_by_year=" + json.dumps({k: len(v) for k, v in sorted(roster.items())}))
    print("appointment_crosscheck=" + json.dumps(appts))

    return {
        "meetings_parsed": meetings_parsed, "motions": motions, "member_rows": member_rows,
        "named": named, "tally_only": tally_only, "contested": contested,
        "recommendations": recommendations, "final_actions": final_actions,
        "ocr_meetings": ocr_meetings, "distinct": distinct, "roster": roster,
        "motion_records": motion_records, "by_type": by_type, "by_format": by_format,
        "appts": appts, "meetings_without_votes": meetings_without_votes,
        "roster_members": roster_members, "member_stats": member_stats,
    }


if __name__ == "__main__":
    main()
