#!/usr/bin/env python3
"""
Extract motions + roll-call votes from Salt Lake City PLANNING COMMISSION minutes.

PURE, DETERMINISTIC PYTHON. This module parses the local markdown with regex only.
It does NOT import or call anthropic / any LLM / any network API. (An earlier version
delegated to the Anthropic API; that approach is gone -- everything here is local text
parsing, exactly like the council extractor's architecture: read an index, parse each
file, write one JSON per meeting, then rebuild the long-format all_votes.csv + roster.)

    votes/<year>/<week-monday>/<date>_planning-commission-meeting.json   per-meeting
    all_votes.csv     long format, one row per NAMED member-vote (the analysis file)
    roster.csv        reconstructed commissioner roster

CARDINAL RULE -- never fabricate. A motion whose minutes give only a tally
("the motion passed", "passed unanimously", "seven 'yes' votes") with NO per-member
name list is recorded as a tally with names_recorded=false and EMPTY aye/nay/abstain/
recuse lists. We never guess who voted which way. Such motions contribute zero member
rows to all_votes.csv; they live fully in the JSON and are counted in coverage.

Usage:
    python3 extract_votes.py            # parse meetings without a JSON yet, then build
    python3 extract_votes.py --force    # discard ALL existing JSONs and rebuild from scratch
    python3 extract_votes.py --build-only   # just rebuild all_votes.csv + roster.csv
"""

import argparse
import csv
import difflib
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

PC_DIR = Path(__file__).resolve().parent
REPO_ROOT = PC_DIR.parent
INDEX_CSV = PC_DIR / "minutes_index.csv"
VOTES_DIR = PC_DIR / "votes"
ALL_CSV = PC_DIR / "all_votes.csv"
ROSTER_CSV = PC_DIR / "roster.csv"

BODY = "PlanningCommission"
TITLE = "Planning Commission"

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

ROLE_WORDS = re.compile(
    r"\b(?:Chairperson|Chair|Vice[\-\s]?Chairperson|Vice[\-\s]?Chair|"
    r"Commissioners|Commissioner|Acting)\b",
    re.I,
)
WORD_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

# curly quotes / straight quotes used around vote words
Q = r"[\"“”‘’']*"


def num(token):
    """A digit string or an English number word -> int, else None."""
    if token is None:
        return None
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return WORD_NUM.get(token)


# Latin presentation-form ligatures pdftotext emits (e.g. "Rosenﬁeld", "deﬁnition").
# They break surname matching (attendance "Rosenﬁeld" vs vote-line "Rosenfield") and
# FTS, so normalize to ASCII the moment a meeting's text is read.
LIGATURES = str.maketrans({
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi",
    "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
})


def deligature(s):
    return (s or "").translate(LIGATURES)


def squash(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def clean_name(raw):
    """Strip role words / filler from a person fragment."""
    s = ROLE_WORDS.sub(" ", raw)
    s = re.sub(r"[“”\"'.,;:()]", " ", s)
    s = re.sub(r"\b(?:and|was|were|is|on|leave|excused|absent|present|the|from|of|voting|"
               r"meeting|not|in|attendance|a|both)\b", " ", s, flags=re.I)
    s = re.sub(r"(?:^|(?<=\s))-+|-+(?=\s|$)", " ", s)   # drop dangling hyphens (OCR wraps)
    return squash(s)


def split_people(blob):
    """Split an attendance blob into individual full-name strings."""
    blob = re.sub(r"\(.*?\)", " ", blob)
    blob = re.sub(r"\s+", " ", blob)     # join wrapped lines ("Bree\nScheer" -> "Bree Scheer")
    # turn role words into delimiters so "Commissioner A Commissioner B" splits cleanly
    blob = ROLE_WORDS.sub(",", blob)
    parts = re.split(r",|\band\b|;|•", blob)
    names = []
    for p in parts:
        n = clean_name(p)
        if not n:
            continue
        toks = [t for t in n.split() if re.match(r"^[A-Z][A-Za-z.\-']+$", t)]
        if 2 <= len(toks) <= 3:
            names.append(" ".join(toks))
    seen, out = set(), []
    for n in names:
        if n.lower() not in seen:
            seen.add(n.lower()); out.append(n)
    return out


# ---------------------------------------------------------------------------
# attendance
# ---------------------------------------------------------------------------

def parse_attendance(text):
    """Return (present, absent) lists of full commissioner names (staff excluded)."""
    present, absent = [], []

    # Format 1 (slcdocs / laserfiche narrative):
    #   "Present for the Planning Commission meeting were: <list>." then
    #   "<Name> was excused / absent / not in attendance / on leave."
    m = re.search(
        r"Present for the Planning Commission meeting were:?\s*(.*?)(?:\n\s*\n|"
        r"Staff members|Planning Staff|City Staff|The meeting was called)",
        text, re.I | re.S)
    if m:
        blob = m.group(1)
        present_blob, absent_blob = blob, ""
        am = re.search(r"\.\s*(.*?(?:excused|absent|not in attendance|on leave).*)$",
                       blob, re.I | re.S)
        if am:
            present_blob = blob[:am.start()]
            absent_blob = am.group(1)
        present = split_people(present_blob)
        if absent_blob:
            absent = split_people(absent_blob)
        tail = text[m.end():m.end() + 600]
        for sm in re.finditer(
                r"((?:[A-Z][A-Za-z.\-']+\s+){1,3})(?:was|were)\s+"
                r"(?:excused|absent|not in attendance|on leave)", tail):
            for n in split_people(sm.group(1)):
                if n not in absent:
                    absent.append(n)
        return present, absent

    # Format 2 (slc.gov 2026 labeled block):
    #   "Commissioners Present   <names>"   "Commissioners Absent   <names|None>"
    mp = re.search(r"Commissioners?\s+Present\s+(.*?)Commissioners?\s+Absent",
                   text, re.I | re.S)
    ma = re.search(r"Commissioners?\s+Absent\s+(.*?)(?:City\s+Staff|Staff|The meeting)",
                   text, re.I | re.S)
    if mp:
        present = split_people(mp.group(1))
    if ma:
        ab = ma.group(1)
        if not re.match(r"\s*None\b", ab, re.I):
            absent = split_people(ab)
    return present, absent


# ---------------------------------------------------------------------------
# roster canonicalization (deterministic variant folding)
# ---------------------------------------------------------------------------

NICKNAMES = {("mike", "michael"), ("jon", "john"), ("rich", "richard"),
             ("matt", "matthew"), ("jeff", "jeffrey")}


def _same_person(n1, n2):
    """Fold two full names iff same surname (typo/prefix tolerant) AND same first name
    (equal / prefix / close / known nickname). Keeps distinct first names apart
    (e.g. Mike vs McCall Christensen)."""
    t1, t2 = n1.split(), n2.split()
    f1, l1 = t1[0].lower(), t1[-1].lower()
    f2, l2 = t2[0].lower(), t2[-1].lower()
    last_ok = (l1 == l2 or l1.startswith(l2) or l2.startswith(l1)
               or difflib.SequenceMatcher(None, l1, l2).ratio() >= 0.88)
    if not last_ok:
        return False
    if f1 == f2:
        return True
    short, lng = sorted([f1, f2], key=len)
    if len(short) >= 3 and lng.startswith(short):
        return True
    if difflib.SequenceMatcher(None, f1, f2).ratio() >= 0.85:
        return True
    return (f1, f2) in NICKNAMES or (f2, f1) in NICKNAMES


def build_canonical_map(name_counts):
    """name -> canonical name. Greedy clustering; canonical = most-seen (then longest)."""
    order = sorted(name_counts, key=lambda n: (-name_counts[n], -len(n), n))
    clusters = []           # each: {"rep": name, "members": [names]}
    for n in order:
        for c in clusters:
            if _same_person(n, c["rep"]):
                c["members"].append(n)
                break
        else:
            clusters.append({"rep": n, "members": [n]})
    return {m: c["rep"] for c in clusters for m in c["members"]}


class _SurnameMap(dict):
    """surname(lower) -> full name, plus .fullnames: every known attendee full name.
    The full-name list lets scanners resolve SHARED surnames (Mike vs McCall
    Christensen) by exact full-name match before falling back to bare surnames."""
    fullnames = ()


def build_surname_map(present, absent):
    """surname(lower) -> full name. Present takes priority over absent for duplicates."""
    m = _SurnameMap()
    for n in absent:                       # fill absent first so present overwrites
        if n:
            m[n.split()[-1].lower()] = n
    for n in present:
        if n:
            m[n.split()[-1].lower()] = n
    m.fullnames = [n for n in list(absent) + list(present) if n]
    # UNIQUE first names among attendees -> full name (2021 minutes sometimes list a
    # roll by first names only: "Commissioners Andra, Andres, Maurine, ... voted "yes"";
    # T3.1(b) 2026-07-12). Ambiguous first names are excluded, never guessed.
    firsts = {}
    for n in m.fullnames:
        toks = n.split()
        if len(toks) >= 2:
            firsts.setdefault(toks[0].lower(), set()).add(n)
    m.firstnames = {k: next(iter(v)) for k, v in firsts.items() if len(v) == 1}
    return m


def surname_scan(blob, surname_map):
    """Full names whose surname appears (whole word, fuzzy fallback) in blob, ordered
    by first position. Used for vote lists / tables.

    Pass 0 matches EXACT full names first (whitespace-tolerant, so wrapped lines work)
    and consumes those spans, so that when two attendees share a surname (Mike vs
    McCall Christensen) a printed full name resolves to the right person instead of
    whichever full name happened to win the surname->name map (the 2024-10-23 /
    2024-11-13 McCall->Mike vote misattributions). Bare-surname behavior for
    single-holder surnames is unchanged."""
    fullnames = getattr(surname_map, "fullnames", None) or list(surname_map.values())
    surnames = list(surname_map.keys())
    hits = {}
    consumed = []
    for fn in fullnames:
        toks = fn.split()
        if len(toks) < 2:
            continue
        pat = r"\b" + r"\s+".join(re.escape(t) for t in toks) + r"\b"
        m = re.search(pat, blob, re.I)
        if m:
            hits.setdefault(fn, m.start())
            consumed.append((m.start(), m.end()))

    def free(pos):
        return not any(s <= pos < e for s, e in consumed)

    for sn in surnames:
        wm = re.search(r"\b" + re.escape(sn) + r"\b", blob, re.I)
        if wm and free(wm.start()):
            hits.setdefault(surname_map[sn], wm.start())
    # unique FIRST names (2021 first-name roll lists), exact word match only
    for fn, full in getattr(surname_map, "firstnames", {}).items():
        wm = re.search(r"\b" + re.escape(fn) + r"\b", blob, re.I)
        if wm and free(wm.start()) and full not in hits:
            hits[full] = wm.start()
            consumed.append((wm.start(), wm.end()))
    for tm in re.finditer(r"\b[A-Z][A-Za-z\-']{2,}\b", blob):
        tok = tm.group(0).lower()
        if tok in surname_map or not free(tm.start()):
            continue
        close = difflib.get_close_matches(tok, surnames, n=1, cutoff=0.84)
        if close:
            hits.setdefault(surname_map[close[0]], tm.start())
    return [n for n, _ in sorted(hits.items(), key=lambda kv: kv[1])]


def map_one(fragment, surname_map):
    """Map a single name fragment (full or surname) to a roster full name, else cleaned."""
    frag = clean_name(fragment)
    if not frag:
        return ""
    fullnames = getattr(surname_map, "fullnames", None) or list(surname_map.values())
    for fn in fullnames:                   # exact full-name match wins (shared surnames)
        if frag.lower() == fn.lower():
            return fn
    last = frag.split()[-1].lower()
    if last in surname_map:
        return surname_map[last]
    close = difflib.get_close_matches(last, list(surname_map.keys()), n=1, cutoff=0.84)
    if close:
        return surname_map[close[0]]
    return frag


# ---------------------------------------------------------------------------
# outcome anchors + tally
# ---------------------------------------------------------------------------

OUTCOME_RE = re.compile(
    r"(?:The\s+)?(?:substitute\s+|amended\s+|main\s+)?motion\s+"
    r"(passed|passes|failed|fails|carried|carries|did\s+not\s+(?:pass|carry))",
    re.I)
NON_VOTE_RE = re.compile(r"did\s+not\s+receive\s+a\s+second", re.I)


def passed(word):
    return bool(re.match(r"pass|carr", word, re.I))


def parse_tally_from_text(outcome_tail):
    """Parse a tally out of the outcome sentence tail. Handles 'unanimously, 9-0',
    '6-1', '4 to one', "with seven 'yes' and one 'no' votes", "seven 'yes' votes,
    and one abstention/recusal/not present"."""
    t = outcome_tail
    yes = no = abst = rec = absent = None
    unanimous = bool(re.search(r"unanim", t, re.I))

    m = re.search(r"(\d+)\s*[-:–]\s*(\d+)", t)
    if m:
        yes, no = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"\b(\d+|" + "|".join(WORD_NUM) + r")\s+to\s+("
                      + "|".join(WORD_NUM) + r"|\d+)\b", t, re.I)
        if m:
            yes, no = num(m.group(1)), num(m.group(2))

    if yes is None:
        my = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s*" + Q + r"\s*yes", t, re.I)
        if my:
            yes = num(my.group(1))
    if no is None:
        mn = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s*" + Q + r"\s*(?:no|nay)\b", t, re.I)
        if mn:
            no = num(mn.group(1))
    ma = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s+(?:" + Q + r")?abstention", t, re.I)
    if ma:
        abst = num(ma.group(1))
    mr = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s+(?:" + Q + r")?recus", t, re.I)
    if mr:
        rec = num(mr.group(1))
    mab = re.search(r"(\d+|" + "|".join(WORD_NUM) + r")\s+(?:not\s+present|absent)", t, re.I)
    if mab:
        absent = num(mab.group(1))

    return {"yes": yes, "no": no, "abstain": abst, "recuse": rec, "absent": absent,
            "unanimous": unanimous}


# ---------------------------------------------------------------------------
# per-block named vote-list extraction
# ---------------------------------------------------------------------------

def extract_named_lists(region, surname_map, present):
    """Pull per-member vote lists from a motion's text region.
    Returns dict aye/nay/abstain/recuse (full names) or None if tally-only."""
    # -- Table form (2024 laserfiche): "Commissioner Yes No" then "Surname x" rows.
    tm = re.search(r"Commissioner\s+Yes\s+No", region, re.I)
    if tm:
        out_tail = region[tm.end():]
        rows = re.findall(r"^[ \t]*([A-Z][A-Za-z\-']+(?:\s+[A-Z][A-Za-z\-']+){0,2})"
                          r"[ \t]+x[ \t]*$", out_tail, re.M)
        names, seen = [], set()
        for r in rows:
            full = map_one(r, surname_map)
            if full and full not in seen:
                seen.add(full); names.append(full)
        # The Yes/No column is lost on conversion ("Surname x"): trust it ONLY when
        # unanimous; non-unanimous -> dissenter unknown -> tally-only. If there were no
        # "x" rows at all, this isn't that table -> fall through to the other parsers.
        if names:
            if re.search(r"unanim", out_tail, re.I):
                return {"aye": names, "nay": [], "abstain": [], "recuse": []}
            return None

    # -- Bullet / labeled form (2025 laserfiche, 2026 slc.gov)
    if re.search(r"\bYes\s*:", region):
        # Stop a vote-list at the next label -- whether it's on a new line (2026 layout)
        # or inline on the same physical line (some 2025 files put a whole meeting on one
        # line: "... • Yes: A, B • No: C • Abstain: Motion passed ...").
        stop = (r"(?=\s*[•]\s*(?:Yes|No|Nay|Abstain\w*|Recus\w*)\b|"
                r"\s+(?:Yes|No|Nay|Abstain\w*|Recus\w*)\s*:|"   # inline "No:" w/o bullet
                r"\s+(?:Motion|Result|Vote)\b|\bThe\s+motion\b|"
                r"\n\s*(?:Yes|No|Nay|Abstain\w*|Recus\w*|Result|Motion|Vote)\b|\n\s*\n|$)")

        def line_names(label):
            # colon REQUIRED (so "No" inside words isn't a label); only spaces/tabs may
            # follow the colon so an empty label line can't swallow the next line.
            m = re.search(label + r"[ \t]*:[ \t]*(.*?)" + stop, region, re.I | re.S)
            if not m:
                return []
            return surname_scan(m.group(1), surname_map)
        aye = line_names(r"(?:[•]\s*)?Yes")
        nay = line_names(r"(?:[•]\s*)?(?:No|Nay)")
        abstain = line_names(r"(?:[•]\s*)?Abstain(?:ed)?")
        recuse = line_names(r"(?:[•]\s*)?Recus(?:e|ed)?")
        if aye or nay or abstain or recuse:
            return {"aye": aye, "nay": nay, "abstain": abstain, "recuse": recuse}
        return None

    # -- Full-name Y/N table (slc.gov 2024): rows "Full Name  Y [note]" / "Name  N".
    #    Unlike the laserfiche "Surname x" table the mark letter is preserved, so trust it.
    nt = r"(?!(?:Yes|No|Y|N|Abstain\w*|Recus\w*|Absent)\b)[A-Z][A-Za-z'\-]+"
    ynrows = re.findall(
        r"^[ \t]*(" + nt + r"(?:\s+" + nt + r"){0,2})[ \t]+"
        r"(Y|N|Yes|No|Abstain\w*|Recus\w*)\b", region, re.M)
    if len(ynrows) >= 2:
        aye, nay, abstain, recuse = [], [], [], []
        for name, mark in ynrows:
            full = map_one(name, surname_map)
            mk = mark.lower()
            if mk in ("y", "yes"):
                aye.append(full)
            elif mk in ("n", "no"):
                nay.append(full)
            elif mk.startswith("abstain"):
                abstain.append(full)
            elif mk.startswith("recus"):
                recuse.append(full)
        if aye or nay or abstain or recuse:
            return {"aye": aye, "nay": nay, "abstain": abstain, "recuse": recuse}

    # -- Narrative form (slcdocs). Flatten newlines so a name list wrapped across lines
    #    ("Commissioners Barry,\nBachman, ...") stays in one preamble.
    nregion = re.sub(r"\s+", " ", region)
    if re.search(r"all\s+commissioners?\s+voted\s+" + Q + r"(?:aye|yes)", nregion, re.I):
        return {"aye": list(present), "nay": [], "abstain": [], "recuse": []}
    # "Brenda abstained. All OTHER Commissioners voted "yes"." (2022-02-23): the ayes
    # are everyone present who isn't named in another bucket — resolved after the loops
    all_other = bool(re.search(r"all\s+other\s+commissioners?\s+voted\s+" + Q +
                               r"(?:aye|yes)", nregion, re.I))

    aye, nay, abstain, recuse = [], [], [], []
    found = False
    # the vote word follows "voted", OR — clerk scrivener form (2022-07-27) — sits
    # directly after the name list as a QUOTED word: "..., and Adrienne Bell, "yes"."
    for vm in re.finditer(r"([^.;]{0,220}?)(?:\bvoted\s*,?\s*" + Q +
                          r"|,\s*[\"“”‘’'])(aye|yes|no|nay)" + Q,
                          nregion, re.I):
        names = surname_scan(vm.group(1), surname_map)
        if not names and re.search(r"\b(?:the\s+)?chair(?:person)?\b[\s,]*$",
                                   vm.group(1), re.I) and getattr(surname_map, "chair", None):
            # "The Chair voted Nay as a tie breaker" (2021-09-08) — a bare title vote
            names = [surname_map.chair]
        if not names:
            continue
        found = True
        if re.match(r"[ay]", vm.group(2), re.I):
            aye += [n for n in names if n not in aye]
        else:
            nay += [n for n in names if n not in nay]
    for am in re.finditer(r"([^.;]{0,180}?)\babstain(?:ed|ing)?\b", nregion, re.I):
        for n in surname_scan(am.group(1), surname_map):
            if n not in abstain:
                abstain.append(n); found = True
    for rm in re.finditer(r"([^.;]{0,180}?)\brecus(?:ed|ing|e)?\b", nregion, re.I):
        for n in surname_scan(rm.group(1), surname_map):
            if n not in recuse:
                recuse.append(n); found = True

    if all_other:
        for p in present:
            if p not in aye and p not in nay and p not in abstain and p not in recuse:
                aye.append(p); found = True

    if found:
        # a person can't be in two categories; keep the strongest signal
        # (explicit dissent > aye > abstain > recuse) so narrative re-mentions across a
        # sentence boundary can't double-count someone.
        aye = [n for n in aye if n not in nay]
        abstain = [n for n in abstain if n not in aye and n not in nay]
        recuse = [n for n in recuse if n not in aye and n not in nay and n not in abstain]
        return {"aye": aye, "nay": nay, "abstain": abstain, "recuse": recuse}
    return None


# ---------------------------------------------------------------------------
# mover / seconder / motion text / classification
# ---------------------------------------------------------------------------

def find_mover_seconder(region, surname_map):
    mover = seconder = ""
    sec = None
    for m in re.finditer(
            r"(?:Chair(?:person)?|Vice[\-\s]?Chair(?:person)?|Commissioner)\s+"
            r"([A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+){0,2}?)\s+seconded", region):
        sec = m
    if sec:
        seconder = map_one(sec.group(1), surname_map)
    mv = None
    for m in re.finditer(
            r"(?:Chair(?:person)?|Vice[\-\s]?Chair(?:person)?|Commissioner)\s+"
            r"([A-Z][A-Za-z.\-']+(?:\s+[A-Z][A-Za-z.\-']+){0,2}?)\s+"
            r"(?:motioned|motions?|moved|moves?|move\b|recommended|stated)", region):
        if sec is None or m.start() <= sec.start():
            mv = m
    if mv:
        mover = map_one(mv.group(1), surname_map)
    return mover, seconder


def find_motion_text(region):
    """Best-effort short description of what was moved. Take the motion-verb occurrence
    CLOSEST to the vote (the last one in the block), since a block can contain earlier
    discussion that also mentions moving."""
    last = None
    for m in re.finditer(
            r"(?:motioned|motions?\s+to|moved|moves?|recommended|I\s+move)\s+"
            r"(?:that\s+(?:the\s+)?(?:Commission|Planning\s+Commission)\s+)?(?:to\s+)?(.*?)"
            r"(?:\.|Commissioner\s+[A-Z][A-Za-z.\-']+\s+seconded|\bseconded\b|\n\s*\n)",
            region, re.I | re.S):
        if squash(m.group(1)):
            last = m
    if last:
        return squash(last.group(1))[:300]
    return ""


TYPE_PATTERNS = [
    ("Master Plan Amendment", r"master\s+plan|general\s+plan"),
    ("Zoning Map Amendment", r"zoning\s+map\s+amendment|rezone|zoning\s+amendment|map\s+amendment"),
    ("Zoning Text Amendment", r"zoning\s+text\s+amendment|text\s+amendment"),
    ("Street/Alley Closure", r"street\s+(?:closure|vacation)|alley\s+(?:closure|vacation)|"
                             r"street\s+vacation|right[\-\s]?of[\-\s]?way\s+vacat|partial\s+street"),
    ("Conditional Use", r"conditional\s+use"),
    ("Planned Development", r"planned\s+development"),
    ("Design Review", r"design\s+review"),
    ("Subdivision/Plat", r"subdivision|preliminary\s+plat|final\s+plat|\bplat\b|condominium"),
    ("Special Exception", r"special\s+exception"),
    ("Minutes", r"\bminutes\b"),
    ("Consent Agenda", r"consent\s+agenda"),
    ("Appointment/Election", r"\belect|officer|nominat"),
]


def classify(motion_text, region):
    """Return (motion_type, action_class). The motion text is authoritative for the type;
    the agenda-item context (region) is only a fallback so an unrelated item nearby (e.g.
    a Planned Development discussed right before a 'approve the consent agenda' motion)
    can't mislabel it."""
    mt = motion_text.lower()
    mtype = "Other"
    for label, pat in TYPE_PATTERNS:
        if re.search(pat, mt):
            mtype = label
            break
    if mtype == "Other":
        for label, pat in TYPE_PATTERNS:
            if re.search(pat, region.lower()):
                mtype = label
                break

    # A real recommendation forwards something to the CITY COUNCIL -- not merely "as
    # recommended by staff" (which accompanies a final action).
    ml = motion_text.lower()
    is_recommend = bool(
        re.search(r"forward\s+a?\s*(?:positive\s+|negative\s+|favorable\s+)?recommendation",
                  ml)
        or ("recommend" in ml and "city council" in ml)
        or ("recommendation" in ml and ("forward" in ml or "city council" in ml)))
    legislative = mtype in {"Master Plan Amendment", "Zoning Map Amendment",
                            "Zoning Text Amendment", "Street/Alley Closure"}
    quasi = mtype in {"Conditional Use", "Planned Development", "Design Review",
                      "Subdivision/Plat", "Special Exception"}
    procedural = mtype in {"Minutes", "Consent Agenda", "Appointment/Election"}

    if procedural and not is_recommend:
        return mtype, "procedural"
    if is_recommend or legislative:
        return mtype, "recommendation"
    if quasi:
        return mtype, "final_action"
    if re.search(r"\b(table|continue[d]?|postpone[d]?|leave\s+of\s+absence|"
                 r"findings\s+of\s+fact)\b", motion_text, re.I):
        return "Procedural/Administrative", "procedural"
    return mtype, "procedural"


def motion_direction(motion_text):
    if re.search(r"\b(den(?:y|ial|ied)|negative|disapprov|reject)\b", motion_text, re.I):
        return "negative"
    return "positive"


def build_result(action_class, direction, passed_flag, tally):
    y, n = tally.get("yes"), tally.get("no")
    nn = f"{y if y is not None else '?'}:{n if n is not None else '?'}"
    if action_class == "recommendation":
        eff_pos = (direction == "positive") == passed_flag
        return f"{'Positive' if eff_pos else 'Negative'} recommendation {nn}"
    if action_class == "final_action":
        approved = (direction == "positive") == passed_flag
        return f"{nn} {'Approved' if approved else 'Denied'} (Final Action)"
    return f"{nn} {'Pass' if passed_flag else 'Fail'}"


# ---------------------------------------------------------------------------
# parse one meeting
# ---------------------------------------------------------------------------

def parse_meeting(text, present, absent):
    surname_map = build_surname_map(present, absent)
    # this meeting's presiding chair (for bare "The Chair voted ..." tie-break rows)
    chair_freq = {}
    for cmatch in re.finditer(r"\bChair(?:person)?\s+([A-Z][A-Za-z\-']+"
                              r"(?:\s+[A-Z][A-Za-z\-']+)?)", text):
        full = map_one(cmatch.group(1), surname_map)
        if full and " " in full:
            chair_freq[full] = chair_freq.get(full, 0) + 1
    surname_map.chair = max(chair_freq, key=chair_freq.get) if chair_freq else None
    votes = []
    last_ac = last_dir = None
    last_pflag = True

    anchors = [m for m in OUTCOME_RE.finditer(text)
               if not NON_VOTE_RE.search(text[max(0, m.start() - 60):m.end() + 60])]
    prev_end = 0
    for a in anchors:
        block = text[prev_end:a.start()]
        # tally tail = the outcome SENTENCE only (cut at first newline or period after the
        # numbers), so a following case number / address can't pollute the tally.
        raw = text[a.start():a.start() + 180]
        cut = len(raw)
        nl = raw.find("\n")
        if nl != -1:
            cut = min(cut, nl)
        pd = raw.find(".")
        if pd != -1:
            cut = min(cut, pd + 1)
        tail = raw[:cut]
        prev_end = a.end()

        pflag = passed(a.group(1))

        sec_pos = max((m.end() for m in re.finditer(r"\bseconded\b", block)), default=None)
        lbl_pos = max((m.start() for m in re.finditer(r"\b(?:MOTION|Motion|Vote)\b", block)),
                      default=None)
        start_region = max([p for p in (sec_pos, lbl_pos, len(block) - 1200)
                            if p is not None], default=0)
        region = block[max(0, start_region):] + tail

        mover, seconder = find_mover_seconder(block, surname_map)
        motion_text = find_motion_text(block)
        mtype, action_class = classify(motion_text, block[-1500:])
        direction = motion_direction(motion_text)

        lists = extract_named_lists(region, surname_map, present)
        tally_text = parse_tally_from_text(tail)

        # PHANTOM-motion guard (2022-04-27): a duplicated mid-roll "The motion passed."
        # splits one motion in two — the second block holds only the roll's tail (nays /
        # abstentions) with NO motion language. Merge its votes into the previous motion
        # instead of fabricating a text-less 0:N row.
        if (votes and votes[-1]["names_recorded"]
                and lists is not None and any(lists[k] for k in ("aye", "nay", "abstain", "recuse"))
                and not mover and not seconder and not motion_text
                and len(block.strip()) < 400
                and not re.search(r"\bmov(?:ed?|es|ing)\b|\bmotion\b|\bseconded\b|"
                                  r"\bpetition\b|\bPLN[A-Z]*\s*\d{4}-\d+", block, re.I)):
            prev = votes[-1]
            already = set(prev["aye"] + prev["nay"] + prev["abstain"] + prev["recuse"])
            for k in ("aye", "nay", "abstain", "recuse"):
                prev[k].extend(n for n in lists[k] if n not in already)
            prev["names_recorded"] = True
            prev["tally"] = {"yes": len(prev["aye"]), "no": len(prev["nay"]),
                             "abstain": len(prev["abstain"]), "recuse": len(prev["recuse"]),
                             "absent": 0}
            prev["result"] = build_result(last_ac, last_dir, last_pflag, prev["tally"])
            continue

        # SCRIVENER-contradiction guard (2022-10-26): a motion that CARRIED cannot have
        # zero ayes — when the printed roll is all-nay but the outcome sentence carries
        # an explicit yes>0 tally, the roll is a clerk copy error (who voted which way
        # is unknowable) -> honest tally-only, never a fabricated attribution.
        if (lists is not None and pflag and not lists["aye"] and lists["nay"]
                and (tally_text["yes"] or 0) > 0):
            lists = None

        if lists is not None and any(lists[k] for k in ("aye", "nay", "abstain", "recuse")):
            names_recorded = True
            aye, nay = lists["aye"], lists["nay"]
            abstain, recuse = lists["abstain"], lists["recuse"]
            tally = {"yes": len(aye), "no": len(nay), "abstain": len(abstain),
                     "recuse": len(recuse), "absent": 0}
        else:
            names_recorded = False
            aye, nay, abstain, recuse = [], [], [], []   # DISTINCT lists (a later
            # phantom-merge mutates them; aliasing would mirror one bucket into all)
            yes, no = tally_text["yes"], tally_text["no"]
            if yes is None and tally_text["unanimous"] and present:
                yes, no = len(present), 0   # unanimous among those present (documented)
            tally = {"yes": yes, "no": no if no is not None else 0,
                     "abstain": tally_text["abstain"], "recuse": tally_text["recuse"],
                     "absent": tally_text["absent"]}

        result = build_result(action_class, direction, pflag, tally)

        votes.append({
            "motion": motion_text or "(motion text not captured)",
            "description": motion_text,
            "motion_type": mtype,
            "action_class": action_class,
            "mover": mover,
            "seconder": seconder,
            "result": result,
            "tally": {k: tally.get(k) for k in ("yes", "no", "abstain", "recuse", "absent")},
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain, "recuse": recuse, "absent": [],
        })
        last_ac, last_dir, last_pflag = action_class, direction, pflag
    return votes


# ---------------------------------------------------------------------------
# index / IO
# ---------------------------------------------------------------------------

def read_index():
    """Read minutes_index.csv (STANDARD schema: date,year,title,slug,path,source,
    source_url,format -- migrated 2026-07-02; the legacy file is frozen as
    minutes_index_legacy.csv). Tolerates the legacy header (meeting_date/file) so an
    old checkout still parses. week_start (the votes/<year>/<week>/ bucket) is derived
    from the path layout minutes/<year>/<week-monday>/<date>_<slug>.md."""
    rows = []
    with open(INDEX_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r = {k: (v or "").strip() for k, v in r.items()}
            if "date" not in r and "meeting_date" in r:      # legacy header
                r["date"] = r["meeting_date"]
            if "path" not in r and "file" in r:
                r["path"] = r["file"]
            if not r.get("week_start"):
                parts = r["path"].replace("\\", "/").split("/")
                r["week_start"] = parts[-2] if len(parts) >= 2 else r["date"]
            rows.append(r)
    return rows


def vote_json_path(meeting_date, week_start, year):
    return VOTES_DIR / year / week_start / f"{meeting_date}_planning-commission-meeting.json"


def process(row, force):
    meeting_date, year, week_start = row["date"], row["year"], row["week_start"]
    rel = row["path"]                       # city-root-relative
    md = REPO_ROOT / rel
    if not md.exists():
        print(f"  MISSING {rel}")
        return None
    out = vote_json_path(meeting_date, week_start, year)
    if out.exists() and not force:
        return out
    text = deligature(md.read_text(encoding="utf-8", errors="replace"))
    present, absent = parse_attendance(text)
    votes = parse_meeting(text, present, absent)
    meta = {
        "date": meeting_date, "year": year, "title": TITLE, "body": BODY,
        "source": row.get("source", ""), "source_url": row.get("source_url", ""),
        "minutes_file": rel, "present": present, "absent": absent,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"meta": meta, "votes": votes}, indent=2), encoding="utf-8")
    return out


NAME_KEYS = ("present", "absent")
VOTE_NAME_KEYS = ("aye", "nay", "abstain", "recuse", "absent")


def canonicalize_jsons():
    """Second pass: fold name variants across ALL meetings so the roster + CSV use one
    canonical spelling per commissioner. Rewrites present/absent + vote lists +
    mover/seconder in every per-meeting JSON. Deterministic (no network)."""
    counts = defaultdict(int)
    files = sorted(VOTES_DIR.rglob("*.json"))
    for jf in files:
        d = json.loads(jf.read_text(encoding="utf-8"))
        for n in d["meta"].get("present", []):
            counts[n] += 1
        for n in d["meta"].get("absent", []):
            counts.setdefault(n, 0)   # known, but present spellings outrank as canonical
    canon = build_canonical_map(dict(counts))

    # global surname -> canonical full name, so a bare surname that voted in a meeting
    # whose attendance list missed that person (late arrival / OCR gap) still resolves to
    # a real roster name instead of failing the off-roster check.
    gsur = {}
    for rep in sorted(set(canon.values()), key=lambda r: -counts.get(r, 0)):
        toks = rep.split()
        if len(toks) >= 2:
            gsur.setdefault(toks[-1].lower(), rep)

    def fix(n):
        c = canon.get(n, n)
        toks = c.split()
        if len(toks) == 1:                      # bare surname -> resolve to a full name
            last = toks[0].lower()
            if last in gsur:
                return gsur[last]
            for k, full in gsur.items():
                if last.startswith(k) or k.startswith(last):
                    return full
            close = difflib.get_close_matches(last, list(gsur), n=1, cutoff=0.84)
            if close:
                return gsur[close[0]]
        return c

    for jf in files:
        d = json.loads(jf.read_text(encoding="utf-8"))
        meta = d["meta"]
        for k in NAME_KEYS:
            meta[k] = list(dict.fromkeys(fix(n) for n in meta.get(k, [])))
        for v in d["votes"]:
            for k in VOTE_NAME_KEYS:
                v[k] = list(dict.fromkeys(fix(n) for n in v.get(k, [])))
            v["mover"] = fix(v.get("mover", ""))
            v["seconder"] = fix(v.get("seconder", ""))
        jf.write_text(json.dumps(d, indent=2), encoding="utf-8")
    return len(canon)


CSV_COLS = ["date", "year", "body", "title", "motion_no", "motion", "motion_type",
            "action_class", "result", "mover", "seconder", "names_recorded",
            "member", "vote", "source"]


def rebuild_csv():
    rows = []
    for jf in sorted(VOTES_DIR.rglob("*.json")):
        d = json.loads(jf.read_text(encoding="utf-8"))
        meta = d["meta"]
        for i, v in enumerate(d["votes"], 1):
            base = {
                "date": meta["date"], "year": meta["year"], "body": BODY, "title": TITLE,
                "motion_no": i, "motion": v.get("motion", ""),
                "motion_type": v.get("motion_type", ""),
                "action_class": v.get("action_class", ""), "result": v.get("result", ""),
                "mover": v.get("mover", ""), "seconder": v.get("seconder", ""),
                "names_recorded": v.get("names_recorded", False),
                "source": meta.get("minutes_file", meta.get("source", "")),
            }
            for vote, members in (("Aye", v.get("aye", [])), ("Nay", v.get("nay", [])),
                                  ("Abstain", v.get("abstain", [])),
                                  ("Recuse", v.get("recuse", [])),
                                  ("Absent", v.get("absent", []))):
                for m in members:
                    rows.append({**base, "member": m, "vote": vote})
    rows.sort(key=lambda r: (r["date"], r["motion_no"], r["vote"], r["member"]))
    with open(ALL_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader(); w.writerows(rows)
    return len(rows)


def build_roster():
    """commissioner, first_seen, last_seen, n_meetings (meetings present)."""
    seen = defaultdict(lambda: {"first": None, "last": None, "present": 0})
    for jf in sorted(VOTES_DIR.rglob("*.json")):
        d = json.loads(jf.read_text(encoding="utf-8"))
        dt = d["meta"]["date"]
        for n in d["meta"].get("present", []):
            r = seen[n]
            r["first"] = dt if r["first"] is None else min(r["first"], dt)
            r["last"] = dt if r["last"] is None else max(r["last"], dt)
            r["present"] += 1
        for n in d["meta"].get("absent", []):
            r = seen[n]
            r["first"] = dt if r["first"] is None else min(r["first"], dt)
            r["last"] = dt if r["last"] is None else max(r["last"], dt)
    rows = [{"commissioner": n, "first_seen": v["first"], "last_seen": v["last"],
             "n_meetings": v["present"]}
            for n, v in seen.items()]
    rows.sort(key=lambda r: (-r["n_meetings"], r["commissioner"]))
    with open(ROSTER_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["commissioner", "first_seen", "last_seen",
                                          "n_meetings"])
        w.writeheader(); w.writerows(rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Pure-regex PC vote extractor")
    ap.add_argument("--force", action="store_true",
                    help="discard ALL existing JSONs and rebuild from scratch")
    ap.add_argument("--build-only", action="store_true",
                    help="just rebuild all_votes.csv + roster.csv from existing JSONs")
    args = ap.parse_args()

    if args.build_only:
        canonicalize_jsons()
        n = rebuild_csv(); r = build_roster()
        print(f"Rebuilt {ALL_CSV.name} ({n} member-vote rows), {ROSTER_CSV.name} ({r}).")
        return

    if args.force and VOTES_DIR.exists():
        shutil.rmtree(VOTES_DIR)
        print(f"--force: removed all existing JSONs under {VOTES_DIR}")

    index = read_index()
    done = 0
    for row in index:
        if process(row, args.force):
            done += 1
    canonicalize_jsons()
    n = rebuild_csv(); r = build_roster()
    print(f"Parsed {done}/{len(index)} meetings.")
    print(f"{ALL_CSV.name}: {n} member-vote rows. {ROSTER_CSV.name}: {r} commissioners.")


if __name__ == "__main__":
    main()
