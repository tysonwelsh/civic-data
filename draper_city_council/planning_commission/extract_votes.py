#!/usr/bin/env python3
"""
Draper Planning Commission vote extractor  (PURE deterministic — no LLM, no network).

Reads PC-meeting markdown under planning_commission/minutes/<year>/<week>/, parses every
recorded motion + its named per-member roll-call GRID, and emits:
  - one JSON per meeting under planning_commission/votes/<year>/<week>/<slug>.json
  - planning_commission/all_votes.csv  (13-col long format; every row body=PlanningCommission)

Draper PC vote grammar (verified 2025-11-20 minutes):
    Motion: Commissioner Fowler moved to APPROVE the Conditional Use Permit, ... application
            2025-0253-USE, based on the following Findings for Approval ...
    Second: Commissioner Shirey seconded the motion.
    Vote on Motion: 4-to-0 in favor.
         Commissioner   Yes    No   Abstained   Not Participating   Absent
         Chair Adams                              X
         Fowler         X
         Squire         X
         Nixon                                                       X
         Shirey         X
         ...
         Green,         X
         Alternate

Grid columns: Yes->Aye, No->Nay, Abstained->Abstain, "Not Participating"->Recuse,
Absent->Absent. Column start positions are read from the header line; each member row's X
is mapped to the NEAREST column (pdftotext -layout preserves columns). Wrapped
", Alternate" role suffixes on their own line are dropped (the X sits on the name line).
Alternates DO vote when seated (e.g. Green in the sample cast the 4th Yes) and are captured.

Land-use CASE NUMBERS (YYYY-NNNN-<TYPE>, e.g. 2025-0253-USE) and PC->Council recommendation
language ("forward a NEGATIVE/POSITIVE recommendation to the City Council") are captured in
the motion text + result string for the referral layer. Recommendation motions vs final
actions (APPROVE/DENY a CUP/site plan) are distinguished in `result`.

As with Council, UNANIMOUS ("N-to-0" / "in favor" with no dissent) grids get a drift-collapse
(any 'nay' folded into 'aye' — see the council extractor's note on pdftotext column drift);
genuinely contested grids are kept and cross-checked by validate_votes.py.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
BODY = "PlanningCommission"

ROLE_PREFIX = r"(?:Commissioner|Vice[-\s]?Chair|Chair|Alternate\s+Commissioner)"

LABEL_TO_BUCKET = {
    "yes": "aye", "no": "nay",
    "abstained": "abstain", "abstain": "abstain",
    "not participating": "recuse", "recuse": "recuse",
    "absent": "absent",
}


def find_columns(line):
    cols = []
    used = [False] * (len(line) + 1)
    for label in ["Not Participating", "Abstained", "Abstain", "Absent", "Recuse",
                  "Yes", "No"]:
        for m in re.finditer(r"\b" + re.escape(label) + r"\b", line):
            s = m.start()
            if any(used[s:m.end()]):
                continue
            for k in range(s, m.end()):
                used[k] = True
            cols.append((s, LABEL_TO_BUCKET[label.lower()]))
    if not cols:
        return None
    buckets = {b for _, b in cols}
    if "aye" not in buckets or not ({"nay", "absent", "abstain", "recuse"} & buckets):
        return None
    cols.sort()
    return cols


def nearest_bucket(cols, xpos):
    """Assign an X mark to a column by RANGE, not nearest-start: an X always renders at or
    to the RIGHT of its column's left edge, so it belongs to the rightmost column whose
    header starts at or before the X. Correctly separates adjacent narrow columns."""
    chosen = cols[0][1]
    for start, bucket in cols:
        if start <= xpos:
            chosen = bucket
        else:
            break
    return chosen


# A grid mark may be an "X"/"x" OR a spelled-out vote word in place of the X.
VOTE_WORDS = {
    "recused": "recuse", "recuse": "recuse", "recusing": "recuse",
    "excused": "absent", "absent": "absent", "abstained": "abstain",
    "abstain": "abstain", "abstaining": "abstain", "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
}
VOTE_WORD_RE = re.compile(
    r"\b(recus(?:ed|ing)?|excused|absent|abstain(?:ed|ing)?)\b", re.I)


# Source-typo / spelling aliases folded to one canonical surname (the source itself is
# inconsistent across 2020-2026 minutes — full names vs surnames, one OCR typo, a dropped
# "Van"). Surname resolution is safe here: no two Draper commissioners share a surname.
SURNAME_ALIAS = {
    "Odgen": "Ogden",        # OCR typo of Gary Ogden
    "Gunderson": "Gundersen",  # spelling variant (same commissioner)
    "Hoff": "Van Hoff",      # dropped "Van" (John Van Hoff)
    "VanHoff": "Van Hoff",   # unspaced variant (2020-21 narrative minutes)
    "Von": "Van Hoff",       # "Von Hoff" OCR/typo of Van Hoff (2020-09-10)
}


def to_surname(toks):
    """Reduce a 1-3 token name to its canonical surname. 'Van Hoff' is a two-word surname."""
    if len(toks) >= 2 and toks[-2].lower() in ("van", "von") and toks[-1].lower() == "hoff":
        sn = "Van Hoff"
    else:
        sn = toks[-1]
        if re.fullmatch(r"[A-Za-z]\.?", sn) and len(toks) >= 2:
            sn = toks[-2]    # trailing initial -> real surname is the token before it
    sn = sn[:1].upper() + sn[1:]
    return SURNAME_ALIAS.get(sn, sn)


def norm_name(raw):
    """Normalize a PC name label to a canonical 'Commissioner <Surname>'. Accepts grid
    labels (bare surname / 'Chair Adams' / 'Green, Alternate') AND narrative full names
    ('Mary Squire' -> 'Squire'). Returns None if not a member label."""
    s = re.sub(r"[_]+", " ", raw)        # underscore vote-cell fillers ("__x_ ___ ___")
    s = re.sub(r"\s+", " ", s).strip(" .:")
    s = VOTE_WORD_RE.sub("", s).strip(" .:,")
    s = re.sub(r"\(\s*(?:Vice[-\s]?)?Chair\s*\)", "", s, flags=re.I).strip()  # "Adams (Chair)"
    s = re.sub(r",?\s*Alternate\b", "", s, flags=re.I).strip(" ,")
    s = re.sub(r"^(?:Chairman|Chairwoman|Vice[-\s]?Chair|Chair|Commissioners?)\s+", "",
               s, flags=re.I).strip()
    s = re.sub(r"^(?:Chairman|Chairwoman|Vice[-\s]?Chair|Chair|Commissioners?)$", "",
               s, flags=re.I).strip()
    if not s or not re.search(r"[A-Za-z]", s):
        return None
    toks = s.split()
    if len(toks) > 3:
        return None
    if not re.match(r"^[A-Z]", s):
        return None
    return "Commissioner " + to_surname(toks)


MOVE_RE = re.compile(
    r"(?:Motion:\s*)?(?:" + ROLE_PREFIX + r")\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?"
    r"(?:\s+[A-Z][A-Za-z.'\-]+)?)\s+(?:moved|motioned|made\s+a\s+motion)\b", re.I)
SECOND_RE = re.compile(
    r"(?:Second:\s*)?(?:" + ROLE_PREFIX + r")\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?"
    r"(?:\s+[A-Z][A-Za-z.'\-]+)?)\s+seconded\b", re.I)
# "Moved by: Commissioner X        Seconded by: Commissioner Y" summary line
# (2020-12-10 COVID-era form, PMN-promoted 2026-07-16; absent from every other doc —
# grep-verified. Checked BEFORE SECOND_RE because on such a line SECOND_RE mis-captures
# the MOVER: "...Commissioner X   Seconded by..." matches <X> seconded.)
SECONDED_BY_RE = re.compile(
    r"Seconded\s+by:\s*(?:" + ROLE_PREFIX + r"\s+)?"
    r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2})")
VOTE_RE = re.compile(
    r"Vote\s+on\s+Motion:?\s*(\d+)\s*(?:-to-|-|to)\s*(\d+)\s*"
    r"(in\s+favor|against|opposed)?", re.I)
MOTION_PASSED_RE = re.compile(
    r"Motion\s+(passed|carried|failed|denied)(?:[^.\n]{0,30}?(\d+)\s*(?:-to-|-|to)\s*(\d+))?",
    re.I)
MOTION_VERB_LINE = re.compile(r"\bmoved\b", re.I)
ROLLCALL_RE = re.compile(r"vote\s+on\s+motion|roll\s*call", re.I)
CASE_RE = re.compile(r"\b(20\d{2}-\d{3,4}-[A-Z]{2,4})\b")


def classify_motion(text):
    t = text.lower()
    if re.search(r"recommendation to the city council|forward a (?:positive|negative)|"
                 r"rezone|rezoning|zone change|zoning map|zoning ordinance|\bzone\b|"
                 r"annex|subdivision|\bplat\b|conditional use|land use|general plan|"
                 r"development agreement|overlay|site plan|preliminary plan|final plan|"
                 r"vacat|home occupation|master plan|text amendment|map amendment|"
                 r"lot line|variance|use permit", t):
        return "Land-Use/Zoning"
    if re.search(r"appoint|elect.*chair|nominate|liaison", t):
        return "Appointment"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"recess|adjourn|convene|reconvene|approve the (?:agenda|minutes|order)|"
                 r"approve the .*minutes|\btable\b|continue|postpone|amend the agenda|"
                 r"move to", t):
        return "Procedural/Administrative"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    return "Other"


# ---- pre-2024 NARRATIVE vote format ----
# "Second: Commissioner DeLaina Tonks."  (no 'seconded' verb)
SECOND_ALT_RE = re.compile(
    r"Second:\s*(?:" + ROLE_PREFIX + r"\s+)?"
    r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2})")
# "Commissioners Ogden, Fowler, Tonks, Nixon, and Bingham voted, "Aye"."  — name tokens
# are anchored Capitalized (NO re.I) so motion prose ("moved to approve...") can't leak in.
_NARR_NAME = r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2}"
NARR_VOTE_RE = re.compile(
    r"Commissioners?\s+(" + _NARR_NAME +
    r"(?:\s*,\s*(?:and\s+)?" + _NARR_NAME + r")*(?:\s*,?\s*and\s+" + _NARR_NAME + r")?)"
    # the clerk sometimes puts a comma before the verb ("...Squire, voted, "Aye."",
    # 2022-08-11 — the dropped aye list flipped a carried 3-2 negative rec to 0-2 Fail;
    # T3.1(j) 2026-07-12)
    r"\s*,?\s*vote[ds][,]?\s*[\"“”']?\s*(Aye|AYE|Yes|YES|Nay|NAY|No|NO)\b")
# "voting 5-to-0 in favor" / "5-to-0 in favor" / "voting 3-2 in favor"
NARR_TALLY_RE = re.compile(
    r"voting\s+(\d+)\s*-?\s*(?:to-?\s*)?(\d+)\s+in\s+favor|"
    r"voting\s+(\d+)\s*-?\s*to-?\s*(\d+)|"
    r"(\d+)\s*-\s*to\s*-\s*(\d+)\s+in\s+favor", re.I)

# ---- 2020-2021 NARRATIVE-ERA RECOVERY grammar (draper PC narrative-era pass, 2026-07-17)
# ----
# The audited 2020-21 PC minutes record roll-call outcomes in prose the primary
# NARR_VOTE_RE (which needs a quoted "Aye"/"No") does NOT see. Three additive forms,
# used ONLY on the recovery path (year<=2021, and only when the primary narrative parse
# found NO attribution — so every currently-named motion stays byte-identical):
#   (a) named in-favor list:  'Commissioners Hawker, Player, Ogden and VanHoff voting
#       in favor of the motion.'  -> ayes.  (A bare 'Commissioners voting in favor'
#       with no name before 'voting' captures nothing — the name group needs a Capital.)
#   (b) named dissent:  'Commissioner Squire voted in opposition to the motion.' /
#       'Commissioner Fowler voting nay.' / 'Commissioner Van Hoff voted no.'  -> nays.
#   (c) oriented item tally:  'This item passed with a 4 to 1 vote.' / 'item passed with
#       a vote of 3 to 2.' / 'The item did not pass with a 2 to 3 vote.'  -> tally +
#       Pass/Fail.  Only consulted when the majority is UNNAMED (never overrides a named
#       roll — the west_valley/T3.1(j) precedent: the truthful named roll wins over a
#       printed tally, cf. 2020-04-02 m9 where '5 to 0' boilerplate sits over a named 4-1).
# Names-only vote word (lowercase allowed) — names stay Capital-anchored (no global re.I).
NARR_VOTE_CI_RE = re.compile(
    r"Commissioners?\s+(" + _NARR_NAME +
    r"(?:\s*,\s*(?:and\s+)?" + _NARR_NAME + r")*(?:\s*,?\s*and\s+" + _NARR_NAME + r")?)"
    r"\s*,?\s*vote[ds][,]?\s*[\"“”']?\s*"
    r"(Aye|AYE|aye|Yes|YES|yes|Nay|NAY|nay|No|NO|no)\b")
NARR_INFAVOR_RE = re.compile(
    r"Commissioners?\s+(" + _NARR_NAME +
    r"(?:\s*,\s*(?:and\s+)?" + _NARR_NAME + r")*(?:\s*,?\s*and\s+" + _NARR_NAME + r")?)"
    r"\s+voting\s+in\s+favor")
NARR_DISSENT_RE = re.compile(
    r"Commissioners?\s+(" + _NARR_NAME +
    r"(?:\s*,\s*(?:and\s+)?" + _NARR_NAME + r")*(?:\s*,?\s*and\s+" + _NARR_NAME + r")?)"
    r"\s+(?:voted\s+in\s+opposition|voting\s+in\s+opposition|voting\s+nay\b|"
    r"voted\s+nay\b|voted\s+no\b)", re.I)
NARR_ITEM_TALLY_RE = re.compile(
    r"\bitem\s+(passed|carried|did\s+not\s+pass|failed)\s+with\s+a\s+"
    r"(?:vote\s+of\s+)?(\d+)\s*(?:-\s*to\s*-|to|-)\s*(\d+)", re.I)
# COVID-era BLOCK-LIST vote form (only the 2020-12-10 meeting, PMN-promoted 2026-07-16;
# grep-verified absent from every other doc in the corpus):
#   Vote: AYE: Chairperson Andrew Adams, Commissioners Kent Player, and Mary Squire, ...
#   NAY: Members: none
#   Absent: None
NARR_AYELIST_RE = re.compile(
    r"Vote:?\s*A(?:YE|ye):\s*(.*?)\s*(?=NAY\b|Nay:|The\s+motion|Motion\s+re:|$)")
NARR_NAYLIST_RE = re.compile(
    r"NAY:?\s*(?:Members:?\s*)?(.*?)\s*(?=Absent\b|ABSENT\b|The\s+motion|$)")
ROLE_WORDS_RE = re.compile(
    r"\b(?:Chairperson|Chairman|Chairwoman|Vice[-\s]?Chair|Chair|Alternate|"
    r"Commissioners?)\b", re.I)


def names_from_rolelist(clause):
    """Names from a role-word-laden full-name list ('Chairperson Andrew Adams,
    Commissioners Kent Player, and Mary Squire, Gary Ogden, John Van Hoff and
    Alternate Commissioners Lisa Fowler'). 'none'/'None' yields no names."""
    clause = ROLE_WORDS_RE.sub(" ", clause)
    out = []
    for chunk in re.split(r",|\band\b", clause):
        chunk = re.sub(r"\s+", " ", chunk).strip(" .:")
        if not chunk or chunk.lower() in ("none", "members"):
            continue
        if not (1 <= len(chunk.split()) <= 3):
            continue
        canon = norm_name("Commissioner " + chunk)
        if canon and canon not in out:
            out.append(canon)
    return out


def names_from_clause(clause):
    chunks = [c.strip(" .") for c in re.split(r",|\band\b", clause) if c.strip(" .")]
    # A missing comma can join two surnames ("Hawker Squire"). When the clause is
    # surname-style (most chunks are single-token), split a multi-token chunk into
    # separate surnames — but never split the two-word surname "Van Hoff".
    single_style = sum(1 for c in chunks if len(c.split()) == 1) >= len(chunks) / 2
    out = []
    for chunk in chunks:
        toks = chunk.split()
        if single_style and len(toks) > 1 and not re.search(r"\bV[ao]n\s+Hoff\b", chunk, re.I):
            subnames = toks
        else:
            subnames = [chunk]
        for sn in subnames:
            canon = norm_name("Commissioner " + sn)
            if canon and canon not in out:
                out.append(canon)
    return out


def parse_narrative(window):
    """(aye, nay, tally|None, found) from the pre-2024 narrative vote form."""
    aye, nay = [], []
    found = False
    for m in NARR_VOTE_RE.finditer(window):
        found = True
        names = names_from_clause(m.group(1))
        val = m.group(2).lower()
        for nm in names:
            if nm in aye or nm in nay:
                continue
            (aye if val in ("aye", "yes") else nay).append(nm)
    # COVID-era block-list form ("Vote: AYE: <names> ... NAY: Members: none")
    for m in NARR_AYELIST_RE.finditer(window):
        names = names_from_rolelist(m.group(1))
        if not names:
            continue
        found = True
        for nm in names:
            if nm not in aye and nm not in nay:
                aye.append(nm)
        mn = NARR_NAYLIST_RE.search(window, m.end())
        if mn:
            for nm in names_from_rolelist(mn.group(1)):
                if nm not in aye and nm not in nay:
                    nay.append(nm)
    recuse = []
    for m in re.finditer(r"Commissioners?\s+(" + _NARR_NAME + r")\s+recused\s+"
                         r"(?:himself|herself|themselves)", window):
        for nm in names_from_clause(m.group(1)):
            if nm not in aye and nm not in nay and nm not in recuse:
                recuse.append(nm)
                found = True
    tally = None
    tm = NARR_TALLY_RE.search(window)
    if tm:
        g = [x for x in tm.groups() if x is not None]
        tally = (int(g[0]), int(g[1]))
    return aye, nay, recuse, tally, found


def parse_narrative_recovery(window):
    """2020-21 narrative-era recovery (draper PC narrative pass, 2026-07-17). Returns
    (aye, nay, recuse, tally|None, outcome, found). Called ONLY when the primary
    narrative parse found NO attribution, so it cannot alter any already-named motion.
    Captures the named in-favor list, named dissenters, and the oriented item tally.
    The named roll is authoritative: the item tally is used only to give the numeric
    outcome — it never invents or overrides a named voter."""
    aye, nay = [], []
    # (a) named in-favor list -> ayes
    for m in NARR_INFAVOR_RE.finditer(window):
        for nm in names_from_clause(m.group(1)):
            if nm not in aye and nm not in nay:
                aye.append(nm)
    # explicit "voted Aye/Yes/No/Nay" incl. lowercase (e.g. Player voted "nay")
    for m in NARR_VOTE_CI_RE.finditer(window):
        val = m.group(2).lower()
        for nm in names_from_clause(m.group(1)):
            if nm in aye or nm in nay:
                continue
            (aye if val in ("aye", "yes") else nay).append(nm)
    # (b) named dissenters -> nays
    for m in NARR_DISSENT_RE.finditer(window):
        for nm in names_from_clause(m.group(1)):
            if nm not in aye and nm not in nay:
                nay.append(nm)
    recuse = []
    for m in re.finditer(r"Commissioners?\s+(" + _NARR_NAME + r")\s+recused\s+"
                         r"(?:himself|herself|themselves)", window):
        for nm in names_from_clause(m.group(1)):
            if nm not in aye and nm not in nay and nm not in recuse:
                recuse.append(nm)
    # (c) oriented tally: prefer the explicit "voting N-M in/against" form, else the
    # "item passed/did not pass with a N to M" form.
    tally = None
    outcome = "Pass"
    tm = NARR_TALLY_RE.search(window)
    if tm:
        g = [x for x in tm.groups() if x is not None]
        tally = (int(g[0]), int(g[1]))
        outcome = "Pass" if tally[0] >= tally[1] else "Fail"
    else:
        im = NARR_ITEM_TALLY_RE.search(window)
        if im:
            verb = im.group(1).lower()
            outcome = "Fail" if ("did not" in verb or verb == "failed") else "Pass"
            tally = (int(im.group(2)), int(im.group(3)))
    found = bool(aye or nay or recuse or tally)
    return aye, nay, recuse, tally, outcome, found


def recommendation_label(text, outcome):
    t = text.lower()
    if "negative recommendation" in t or re.search(r"forward a negative", t):
        return "Negative Recommendation"
    if "positive recommendation" in t or re.search(r"forward a positive", t):
        return "Positive Recommendation"
    if "recommendation to the city council" in t:
        return "Recommendation"
    if re.search(r"\bden(?:y|ied|ial)\b", t):
        return "Denied (Final Action)"
    if re.search(r"\bapprov", t):
        return "Approved (Final Action)"
    return outcome


def load_rows(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for ln in text.split("\n"):
        ln = ln.replace("\x0c", "")     # form-feed page marks split grids — drop them
        s = ln.strip()
        if re.match(r"^\d+\s*\|\s*P\s*a\s*g\s*e\s*$", s, re.I):   # "1|Page" & "17 | P a g e"
            continue
        if re.match(r"^Page\s+\d+(?:\s+of\s+\d+)?\s*$", s, re.I):   # "Page 3" & "Page 3 of 5"
            continue
        # running meeting header/footer ("Draper City Planning Commission Meeting")
        if re.match(r"^Draper (?:City )?Planning Commission\b", s, re.I):
            continue
        # running date footer ("November 20, 2025")
        if re.match(r"^(?:January|February|March|April|May|June|July|August|September|"
                    r"October|November|December)\s+\d{1,2},\s+\d{4}\s*$", s, re.I):
            continue
        # running title footer ("... (Planning Commission) ... (Meeting) Minutes – <date>")
        if re.search(r"(?:Approved )?(?:Meeting )?Minutes\s*[–—-]\s*"
                     r"(?:January|February|March|April|May|June|July|August|September|"
                     r"October|November|December)\s+\d", s, re.I):
            continue
        if re.match(r"^Draper (?:City )?Planning Commission.*Minutes\b", s, re.I):
            continue
        out.append(ln.rstrip("\n"))
    return out


def parse_grid(lines, start):
    cols = find_columns(lines[start])
    if not cols:
        return None
    buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    i = start + 1
    n = len(lines)
    seen = set()
    got = 0
    blanks = 0
    since_last = 0
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            blanks += 1
            if blanks >= 6 and got:
                break
            i += 1
            continue
        blanks = 0
        xs = [m.start() for m in re.finditer(r"(?<![A-Za-z])[Xx](?![A-Za-z])", raw)]
        wordvote = VOTE_WORD_RE.search(raw)
        if not xs and not wordvote:
            # role-noise continuation (a wrapped ", Alternate" / "Vice-Chair" line) -> skip
            if re.fullmatch(r"(?:Alternate|Alt|Vice[-\s]?Chair|Chair|Commissioner)[,.]?",
                            s, re.I):
                i += 1
                continue
            if (MOTION_VERB_LINE.search(s) or ROLLCALL_RE.search(s) or find_columns(raw)
                    or re.match(r"^\d+\.?[a-z]?\.?\s+\S", s) or len(s.split()) > 6):
                break
            # a name-only row (a commissioner present with no recorded mark, or a wrapped
            # name fragment) -> SKIP, do not terminate the grid.
            if got and (re.match(r"^(?:Commissioner|Vice[-\s]?Chair|Chair)\b", s, re.I)
                        or re.fullmatch(r"[A-Z][A-Za-z.'\- ]{0,25}", s)):
                since_last += 1
                if since_last > 6:
                    break
                i += 1
                continue
            if got:
                break
            i += 1
            continue
        namepart = raw
        for x in xs:
            namepart = namepart[:x] + " " + namepart[x + 1:]
        # wrapped surname (older layout): the surname wraps to the next line
        adv = 0
        namepart_str = re.sub(r"\s+", " ", namepart).strip()
        name_after = re.sub(r"^(?:Commissioner|Vice[-\s]?Chair|Chair)\s*", "",
                            namepart_str, flags=re.I).strip(" .,")
        name_after = re.sub(r",?\s*Alternate$", "", name_after, flags=re.I).strip()
        if (name_after == "" or re.search(r"\b[A-Z]\.\s*$", namepart_str)) and i + 1 < n:
            nxt = lines[i + 1].strip()
            if re.fullmatch(r"[A-Z][a-z']+", nxt):
                namepart = namepart_str + " " + nxt
                adv = 1
        canon = norm_name(namepart)
        if canon is None:
            i += 1
            continue
        if canon in seen:
            i += 1 + adv
            continue
        if xs:
            bucket = nearest_bucket(cols, xs[0])
        else:
            bucket = VOTE_WORDS.get(wordvote.group(1).lower(), None)
            if bucket is None:
                i += 1
                continue
        seen.add(canon)
        buckets[bucket].append(canon)
        got += 1
        since_last = 0
        i += 1 + adv
    if got == 0:
        return None
    return buckets, i, got


def result_from(window):
    m = VOTE_RE.search(window)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        favor = (m.group(3) or "").lower()
        outcome = "Fail" if ("against" in favor or "opposed" in favor) else \
            ("Pass" if a >= b else "Fail")
        return outcome, (a, b), True
    m = MOTION_PASSED_RE.search(window)
    if m:
        verb = m.group(1).lower()
        outcome = "Fail" if verb in ("failed", "denied") else "Pass"
        if m.group(2):
            return outcome, (int(m.group(2)), int(m.group(3))), True
        return outcome, None, True
    return "Pass", None, False   # NO vote evidence in the window (default)


def parse_meeting(lines, narrative_recovery=False):
    n = len(lines)
    votes = []
    i = 0
    while i < n:
        line = lines[i]
        mv = MOVE_RE.search(line)
        if not mv:
            i += 1
            continue
        mover = norm_name(mv.group(1))
        seconder = None
        motion_parts = [re.sub(r"^Motion:\s*", "", line[mv.start():].strip())]
        j = i + 1
        grid = None
        scan_limit = min(n, i + 60)
        while j < scan_limit:
            lj = lines[j]
            sj = lj.strip()
            if seconder is None:
                sm = (SECONDED_BY_RE.search(lj) if "Seconded by:" in lj else None) \
                    or SECOND_RE.search(lj) or SECOND_ALT_RE.search(lj)
                if sm:
                    seconder = norm_name(sm.group(1))
                    j += 1
                    continue
            if find_columns(lj):
                g = parse_grid(lines, j)
                if g:
                    grid = g
                    break
            if j > i and MOVE_RE.search(lj) and "second" not in sj.lower():
                break
            if seconder is None and len(motion_parts) < 14 and \
                    not re.match(r"^(?:Second:|Vote on Motion)", sj):
                motion_parts.append(sj)
            j += 1

        motion_text = re.sub(r"\s+", " ",
                             " ".join(p for p in motion_parts if p)).strip(" .;,")
        motion_text = re.split(r"Second:\s*" + ROLE_PREFIX, motion_text)[0].strip(" .;,")
        mtype = classify_motion(motion_text)
        window = " ".join(x.strip() for x in lines[i:(grid[1] if grid else j)])
        outcome, tally, vote_evidence = result_from(window)
        rec = recommendation_label(motion_text, outcome)

        buckets = grid[0] if grid else {"aye": [], "nay": [], "abstain": [],
                                        "absent": [], "recuse": []}
        names_recorded = grid is not None
        if grid:
            unanimous = (tally is not None and tally[1] == 0)
            if unanimous and buckets["nay"]:
                for nm in buckets["nay"]:
                    if nm not in buckets["aye"]:
                        buckets["aye"].append(nm)
                buckets["nay"] = []
            na, nn = len(buckets["aye"]), len(buckets["nay"])
            if tally is None:
                tally = (na, nn)
            result_str = f"{na}-{nn} {rec}"
        else:
            # pre-2024 NARRATIVE form: named voters are listed in prose, not a grid
            n_aye, n_nay, n_recuse, n_tally, found = parse_narrative(window)
            if found:
                buckets["aye"], buckets["nay"] = n_aye, n_nay
                buckets["recuse"] = n_recuse
                names_recorded = True
                if n_tally is not None:
                    tally = n_tally
                    outcome = "Pass" if n_tally[0] >= n_tally[1] else "Fail"
                na, nn = len(n_aye), len(n_nay)
                # unanimous-declared with a printed N-0 but only some ayes named -> trust names
                if tally:
                    result_str = f"{tally[0]}-{tally[1]} {rec}"
                elif na or nn:
                    result_str = f"{na}-{nn} {rec}"
                else:
                    # only a recusal/absence was named (voice vote otherwise)
                    result_str = f"{rec} (voice/tally-only)"
            else:
                # 2020-21 NARRATIVE-ERA RECOVERY (draper PC narrative pass, 2026-07-17):
                # the primary parse found NO attribution — try the prose in-favor list /
                # named dissent / oriented item tally. Gated to the audited 2020-21 era.
                r_aye, r_nay, r_recuse, r_tally, r_outcome, r_found = (
                    parse_narrative_recovery(window) if narrative_recovery
                    else ([], [], [], None, "Pass", False))
                if r_found and (r_aye or r_nay or r_tally):
                    buckets["aye"], buckets["nay"] = r_aye, r_nay
                    buckets["recuse"] = r_recuse
                    if r_tally is not None:
                        tally = r_tally
                        outcome = r_outcome
                    else:
                        tally = (len(r_aye), len(r_nay))
                    # names_recorded ONLY when the MAJORITY (winning) side is fully named
                    # — the sandy/magna dissent-only precedent: a named dissenter over an
                    # unnamed majority is honest data with names_recorded=False.
                    maj = tally[0] if outcome != "Fail" else tally[1]
                    maj_named = len(r_aye) if outcome != "Fail" else len(r_nay)
                    names_recorded = maj > 0 and maj_named >= maj
                    result_str = f"{tally[0]}-{tally[1]} {rec}"
                elif tally:
                    result_str = f"{tally[0]}-{tally[1]} {rec}"
                elif outcome == "Fail":
                    result_str = f"Died/Failed ({rec})"
                elif not vote_evidence and re.search(
                        r"(?:application|item)\s+was\s+(?:formally\s+)?withdrawn|"
                        r"formally\s+withdrawn\s+by\s+the\s+applicant", window, re.I):
                    # a moved-but-never-voted item the applicant withdrew mid-discussion
                    # (2020-11-19; T3.1(j)) — never a fabricated voice-vote pass/denial
                    result_str = "No vote (application withdrawn)"
                else:
                    result_str = f"{rec} (voice/tally-only)"

        cases = CASE_RE.findall(motion_text)
        votes.append({
            "body": BODY,
            "motion": motion_text[:600],
            "motion_type": mtype,
            "result": result_str,
            "mover": mover,
            "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
            "absent": buckets["absent"], "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "printed_tally": list(tally) if tally else None,
            "case_numbers": cases,
        })
        i = grid[1] if grid else max(j, i + 1)
    return votes


def main():
    force = "--force" in sys.argv
    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    for r in rows:
        rel = r["path"]
        path = ROOT / rel
        if not path.exists():
            print(f"MISSING: {rel}", file=sys.stderr)
            continue
        week = Path(rel).parent.name
        year = r["year"]
        slug = Path(rel).stem
        out_dir = VOTES_DIR / year / week
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(load_rows(path),
                              narrative_recovery=int(year) <= 2021)
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        payload = {"date": r["date"], "year": int(year), "title": r["title"],
                   "source": rel, "votes": votes}
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON  (skipped {skipped} existing)")
    build_all_votes()


def build_all_votes():
    # provenance (trailing 14th column, the ogden/herriman promotion convention):
    # 'minutes' = audited Granicus doc; 'pmn_minutes' = Utah Public Notice recovery
    # promoted into this layer (minutes_index.csv source=pmn) — 2026-07-16.
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    prov_by_path = {}
    for r in csv.DictReader(INDEX.open()):
        prov_by_path[r["path"]] = (
            "pmn_minutes" if r.get("source", "").strip().lower() == "pmn" else "minutes")
    n_rows = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            if jp.name.startswith("_"):
                continue
            data = json.loads(jp.read_text())
            prov = prov_by_path.get(data["source"], "minutes")
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                   ("absent", "Absent"), ("recuse", "Recuse")):
                    for member in v.get(key, []):
                        w.writerow(base + [member, label, data["source"], prov])
                        n_rows += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"], prov])
                    n_rows += 1
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")


if __name__ == "__main__":
    main()
