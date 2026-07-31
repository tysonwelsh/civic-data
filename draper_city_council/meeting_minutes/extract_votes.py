#!/usr/bin/env python3
"""
Draper City Council vote extractor  (PURE deterministic — no LLM, no network).

Reads the council-meeting markdown under meeting_minutes/minutes/<year>/<week>/, parses
every recorded motion + its named per-member roll-call GRID, and emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<slug>.json  (resumable)
  - meeting_minutes/all_votes.csv  (13-col long format, one row per member-vote)

Draper's council vote grammar (verified 2024-12-03 full minutes):
    Councilmember Green moved to approve Ordinance #1628.
    Councilmember Johnson seconded the motion.
    A roll call vote was taken. The motion passed unanimously.
                                  Yes No Absent
    Councilmember Green            X
    Councilmember Johnson          X
    Councilmember T. Lowery        X
    Councilmember F. Lowry         X
    Councilmember Vawdrey          X

Grid parsing: the header row ("Yes No Absent") fixes each column's start position; each
member row's X is mapped to the NEAREST column by horizontal offset (pdftotext -layout
preserves columns). Yes->Aye, No->Nay, Absent->Absent. A named dissent is an X in the No
column — captured per member.

Some outcomes are recorded WITHOUT a named grid (voice votes, e.g. adjournment "passed by
unanimous voice vote (5-0)"); those become tally-only rows (member/vote blank), never guessed.

MAYOR: Mayor Troy K. Walker PRESIDES but does NOT vote. He is NEVER in the roll-call grid
(exactly the 5 at-large councilmembers appear; max tally 5). The grid is authoritative for
who voted, so the mayor is naturally excluded; a defensive guard also drops him if seen.

Roster note: T. Lowery (Tasha Lowery) and F. Lowry (Fred Lowry) are DISTINCT members with
near-identical surnames — the grid prints the disambiguating initial and we preserve it.
Roster drift Vawdrey (through 2025) -> Dahlin (2026) is handled by trusting the grid names.
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
BODY = "Council"

MAYOR_TOKENS = {"walker"}          # Mayor Troy K. Walker — normally NON-voting
MAYOR_NAME = "Mayor Troy K. Walker"

# member-name prefix used in the grid (Council). "Board Member" is the title the
# ceremonial BOARD OF CANVASSERS minutes use for the SAME five councilmembers in the
# mover/seconder lines (the roll-call GRID rows still print "Councilmember"); it is
# included so the canvass certification motion is recognized. council_surname() reduces
# "Board Member Green" -> "Green" the same as "Councilmember Green".
NAME_PREFIX = r"(?:Council\s*member|Council\s*Member|Councilman|Councilwoman|Board\s*Member|Mayor\s*Pro\s*Tem(?:pore)?)"

# A grid mark may be an "X" OR a spelled-out vote word in place of the X (e.g. a member
# who "recused"/"excused"/"absent" is written as the word, not an X).
VOTE_WORDS = {
    "recused": "recuse", "recuse": "recuse", "recusing": "recuse",
    "excused": "absent", "absent": "absent", "abstained": "abstain",
    "abstain": "abstain", "abstaining": "abstain", "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
}
VOTE_WORD_RE = re.compile(r"\b(recus(?:ed|ing)?|excused|absent|abstain(?:ed|ing)?)\b", re.I)

# ---- grid header detection ----
# A grid header line contains the vote-column labels. Council uses Yes/No/Absent.
COL_LABELS = ["Yes", "No", "Abstained", "Abstain", "Not Participating", "Absent", "Recuse"]
LABEL_TO_BUCKET = {
    "yes": "aye", "no": "nay",
    "abstained": "abstain", "abstain": "abstain",
    "not participating": "recuse", "recuse": "recuse",
    "absent": "absent",
}


def find_columns(line):
    """Return [(col_start, bucket), ...] for a candidate grid-header line, or None.
    Requires at least a Yes and a No/Absent column to qualify as a vote grid header."""
    cols = []
    used = [False] * (len(line) + 1)
    # match multi-word labels first (Not Participating) then singles
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
    header starts at or before the X. This correctly separates the narrow, adjacent
    No/Absent columns (a No X landing between them is not mis-read as Absent)."""
    chosen = cols[0][1]
    for start, bucket in cols:
        if start <= xpos:
            chosen = bucket
        else:
            break
    return chosen


NAME_ROW_RE = re.compile(
    r"^\s*(" + NAME_PREFIX + r")?\s*([A-Z][A-Za-z.'\- ]*?)\s+(X)\s*$")
# also allow rows where the X sits far right (columns) — we detect X by position instead.


# Canonicalize a council name to ONE identity across the grid era (which prints the
# disambiguating initial "T. Lowery" / "F. Lowry") and the 2020-2021 narrative era (which
# prints bare surnames "Lowery"/"Lowry" or full names "Tasha Lowery"/"Fred Lowry").
# The two near-identical surnames are the ONLY collision (recon §2): the SPELLING itself
# disambiguates them — "Lowery"=Tasha, "Lowry"=Fred — so map each to the initialed form.
COUNCIL_SPECIAL = {"lowery": "T. Lowery", "lowry": "F. Lowry"}


def council_surname(toks):
    """Reduce a 1-3 token council name (possibly an initial + surname, or first+last) to
    its canonical surname form."""
    toks = [t for t in toks if t]
    if not toks:
        return ""
    last = toks[-1]
    if re.fullmatch(r"[A-Za-z]\.?", last) and len(toks) >= 2:
        last = toks[-2]        # trailing bare initial -> the surname is the token before it
    key = last.lower()
    if key in COUNCIL_SPECIAL:
        return COUNCIL_SPECIAL[key]
    return last[:1].upper() + last[1:]


def classify_member(raw):
    """(canonical_name, is_mayor) for a grid member label, or (None, False).
    Preserves the F./T. disambiguating initial. The Mayor (Walker) is returned with
    is_mayor=True so a genuine mayoral tie-break can be captured + flagged (he is
    otherwise non-voting and never appears in the grid)."""
    s = re.sub(r"[_]+", " ", raw)        # underscore vote-cell fillers ("__x_ ___ ___")
    s = re.sub(r"\s+", " ", s).strip(" .:")
    # strip vote-word remnants that may trail the name (e.g. "F. Lowry recused")
    s = VOTE_WORD_RE.sub("", s).strip(" .:,")
    toks = re.findall(r"[A-Za-z']+", s.lower())
    if any(t in MAYOR_TOKENS for t in toks):
        return MAYOR_NAME, True
    s = re.sub(r"^(?:" + NAME_PREFIX + r")\s*", "", s, flags=re.I).strip()
    if not s or not re.search(r"[A-Za-z]", s):
        return None, False
    return "Councilmember " + council_surname(s.split()), False


def norm_name(raw):
    """Council-member canonical name (mover/seconder use). None for the mayor / non-members."""
    canon, is_mayor = classify_member(raw)
    return None if is_mayor else canon


# ---- motion intro / result ----
MOVE_RE = re.compile(
    r"(" + NAME_PREFIX + r")\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z.'\-]+)?)"
    r"\s+(?:moved|motioned|made\s+a\s+motion)\b", re.I)
SECOND_RE = re.compile(
    r"(" + NAME_PREFIX + r")\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z.'\-]+)?)"
    r"\s+seconded\b", re.I)
ROLLCALL_RE = re.compile(r"roll\s*call\s*vote\s*was\s*taken", re.I)
VOICE_RE = re.compile(
    r"(?:unanimous\s+voice\s+vote|voice\s+vote|by\s+(?:unanimous\s+)?consent)"
    r".{0,40}?\(?\s*(\d)\s*[-–]\s*(\d)\s*\)?|passed\s+by\s+unanimous\s+voice\s+vote", re.I)
OUTCOME_UNANIMOUS = re.compile(r"passed\s+unanimously|carried\s+unanimously|"
                               r"approved\s+unanimously", re.I)
OUTCOME_FAIL = re.compile(r"motion\s+(?:failed|did\s+not\s+(?:pass|carry))|"
                          r"failed\s+for\s+lack|died\s+for\s+lack|no\s+second", re.I)
OUTCOME_TALLY = re.compile(
    r"(?:(?:motion|item)\s+(?:was\s+)?(?:passed|carried|approved|failed|denied)[^.\n]{0,40}?)"
    r"\(?\s*(\d)\s*(?:[-–]|to)\s*(\d)\s*\)?", re.I)
MOTION_VERB_LINE = re.compile(r"\b(moved|motioned|made a motion)\b", re.I)

# ---- pre-2022 NARRATIVE vote form ----
# "A roll call vote was taken with Councilmembers Green, Lowery, Lowry, Roberts, and
#  Vawdrey voting in favor. The motion passed unanimously."  (name tokens anchored
# Capitalized — NO re.I — so prose can't leak in; 'voting'/direction are lowercase.)
_CNARR_NAME = r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z.'\-]+)?"
_CNARR_LIST = (_CNARR_NAME + r"(?:\s*,\s*(?:and\s+)?" + _CNARR_NAME + r")*"
               r"(?:\s*,?\s*and\s+" + _CNARR_NAME + r")?")
# "in favor" -> aye ; "against"/"in opposition" -> nay. "voting to deny/approve" is
# ACTION-relative (a motion-to-deny inverts it), so it is deliberately NOT interpreted —
# such motions fall through to tally-only rather than risk mis-bucketing a vote.
CNARR_VOTE_RE = re.compile(
    r"Councilmembers?\s+(" + _CNARR_LIST + r")\s*,?\s+"
    r"voting\s+(in favor|against|in opposition|opposed)\b")
# single-member (or short-list) dissent: "Councilmember Green opposed" / "voted against"
CNARR_OPP_RE = re.compile(
    r"Councilmembers?\s+(" + _CNARR_LIST + r")\s+"
    r"(?:opposed|voted\s+against|voted\s+in\s+opposition|voted\s+no\b|voted\s+nay\b)")


def council_names_from_clause(clause):
    out = []
    for chunk in re.split(r",|\band\b", clause):
        canon, is_m = classify_member("Councilmember " + chunk.strip())
        if canon and not is_m and canon not in out:
            out.append(canon)
    return out


def parse_narrative(window):
    """(aye, nay, found) from the 2020-2021 narrative vote form."""
    aye, nay = [], []
    found = False
    for m in CNARR_VOTE_RE.finditer(window):
        found = True
        against = ("against" in m.group(2) or "opposition" in m.group(2)
                   or "opposed" in m.group(2))
        for nm in council_names_from_clause(m.group(1)):
            if nm in aye or nm in nay:
                continue
            (nay if against else aye).append(nm)
    for m in CNARR_OPP_RE.finditer(window):
        for nm in council_names_from_clause(m.group(1)):
            if nm in aye:
                aye.remove(nm)
            if nm not in nay:
                nay.append(nm)
                found = True
    return aye, nay, found


def classify_motion(text):
    t = text.lower()
    if re.search(r"rezone|rezoning|zone change|zoning map|zoning ordinance|\bzone\b|"
                 r"annex|subdivision|\bplat\b|conditional use|land use|general plan|"
                 r"development agreement|overlay|site plan|preliminary plan|final plan|"
                 r"vacat|amend.*zoning|amend.*development code|master plan|"
                 r"community reinvestment|redevelopment|project area", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend.*budget|tentative budget|final budget|"
                 r"adopt.*budget|budget for|appropriat|cip|capital improvement", t):
        return "Budget"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t):
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|mayor pro tem|liaison|ratify|canvass|"
                 r"board|commission member|committee member", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|agreement with|services agreement|"
                 r"enter into an agreement|task order|change order", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial|"
                 r"presentation", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|executive session|"
                 r"approve the (?:consent|agenda|minutes|order)|approve the .*minutes|"
                 r"\btable\b|continue|postpone|amend the agenda|consent (?:item|agenda)|"
                 r"move to", t):
        return "Procedural/Administrative"
    return "Other"


def load_rows(path):
    """Raw lines (layout preserved) minus the running page footer that Draper prints
    ('1|Page' and 'Draper City Council Approved Meeting Minutes – <date>')."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    out = []
    for ln in lines:
        ln = ln.replace("\x0c", "")     # form-feed page marks split grids — drop them
        s = ln.strip()
        if re.match(r"^\d+\s*\|\s*P\s*a\s*g\s*e\s*$", s, re.I):   # "1|Page" & "17 | P a g e"
            continue
        if re.match(r"^Page\s+\d+(?:\s+of\s+\d+)?\s*$", s, re.I):   # "Page 3" & "Page 3 of 5"
            continue
        # running title footer, in all observed forms:
        #   "Draper City Council Approved Meeting Minutes – January 7, 2025"
        #   "City Council Approved Meeting Minutes – July 19, 2022"
        #   "Draper City Council Special Meeting Approved Meeting Minutes – ..."
        if re.search(r"(?:Approved )?(?:Meeting )?Minutes\s*[–—-]\s*"
                     r"(?:January|February|March|April|May|June|July|August|September|"
                     r"October|November|December)\s+\d", s, re.I):
            continue
        # a bare running date-only footer ("July 19, 2022")
        if re.match(r"^(?:January|February|March|April|May|June|July|August|September|"
                    r"October|November|December)\s+\d{1,2},\s+\d{4}\s*$", s, re.I):
            continue
        out.append(ln.rstrip("\n"))
    return out


def parse_grid(lines, start):
    """Parse a roll-call grid beginning at header-line index `start`.
    Returns (buckets, end_index, n_rows, mayor_voted) or None. A member row's vote is
    an "X" under a column OR a spelled-out vote word ("recused"/"excused"/"absent"/
    "abstained") in place of the X. A Mayor row carrying a mark is a genuine tie-break —
    captured (member=Mayor) and flagged mayor_voted (he is otherwise non-voting)."""
    cols = find_columns(lines[start])
    if not cols:
        return None
    buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    rows_info = []                    # (canon, x_pos|None, row_indent, word_bucket|None)
    i = start + 1
    n = len(lines)
    seen = set()
    got = 0
    blanks = 0
    since_last = 0     # non-recording lines seen since the last captured member row
    mayor_voted = False
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            # a page break inserts blank+footer(stripped)+blank INSIDE a grid, so blanks
            # do NOT terminate a grid; only a real terminator line (below) does. Bail out
            # if the blank run is very long (grid genuinely ended).
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
            # terminators: new motion, fresh roll-call, a new grid header, a numbered
            # agenda section, or any multi-word narrative sentence.
            if (MOTION_VERB_LINE.search(s) or ROLLCALL_RE.search(s) or find_columns(raw)
                    or re.match(r"^\d+\.?[a-z]?\.?\s+\S", s) or len(s.split()) > 6):
                break
            # a name-only row: a member PRESENT but with no recorded vote mark (e.g. a
            # member unable to vote), or a wrapped name fragment. SKIP it (do not guess a
            # vote, do not terminate the grid). A short capitalized token qualifies.
            if got and (re.match(r"^(?:" + NAME_PREFIX + r")\b", s, re.I)
                        or re.fullmatch(r"[A-Z][A-Za-z.'\- ]{0,25}", s)):
                since_last += 1
                if since_last > 6:      # runaway guard — grid genuinely ended
                    break
                i += 1
                continue
            if got:
                break
            i += 1
            continue
        # isolate the name text (remove X marks and any trailing vote word)
        namepart = raw
        for x in xs:
            namepart = namepart[:x] + " " + namepart[x + 1:]
        # WRAPPED SURNAME (older layout): the surname wraps to the FOLLOWING line, leaving
        # either a dangling initial ("Councilmember     T." -> "Lowery") or an empty name
        # ("Councilmember                 X" -> "Vawdrey"). Pull the surname up.
        adv = 0
        namepart_str = re.sub(r"\s+", " ", namepart).strip()
        name_after = re.sub(r"^(?:" + NAME_PREFIX + r")\s*", "", namepart_str,
                            flags=re.I).strip(" .")
        if (name_after == "" or re.search(r"\b[A-Z]\.\s*$", namepart_str)) and i + 1 < n:
            nxt = lines[i + 1].strip()
            if re.fullmatch(r"[A-Z][a-z']+", nxt):
                namepart = namepart_str + " " + nxt
                adv = 1
        canon, is_mayor = classify_member(namepart)
        if canon is None:
            i += 1
            continue
        if canon in seen:
            i += 1 + adv
            continue
        # determine the vote bucket: X-position wins; else the spelled-out vote word
        indent = len(raw) - len(raw.lstrip())
        if xs:
            bucket = nearest_bucket(cols, xs[0])
            rows_info.append((canon, xs[0], indent, None))
        else:
            bucket = VOTE_WORDS.get(wordvote.group(1).lower(), None)
            if bucket is None:
                i += 1
                continue
            rows_info.append((canon, None, indent, bucket))
        seen.add(canon)
        buckets[bucket].append(canon)
        if is_mayor:
            mayor_voted = True
        got += 1
        since_last = 0
        i += 1 + adv
    if got == 0:
        return None
    # PAGE-BREAK indent repair (T3.1(j) 2026-07-12): rows re-rendered after a page
    # footer gain a constant left indent, shifting every X into the Absent column
    # (2025-01-07 Ord #1630, 2025-05-06 — "passed unanimously" grids read as 0-0/1-0
    # with 3-5 phantom Absents). An absent-majority grid is physically impossible for
    # a voted motion (no quorum), so re-bucket with each row's X normalized by its
    # own indent; keep the repair only if it yields a plausible (aye-bearing) roll.
    if (len(buckets["absent"]) >= 3
            and len(buckets["absent"]) > len(buckets["aye"]) + len(buckets["nay"])):
        rebuckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        for canon, x, indent, wbucket in rows_info:
            b = wbucket if x is None else nearest_bucket(cols, x - indent)
            rebuckets[b].append(canon)
        if len(rebuckets["aye"]) > len(buckets["aye"]):
            buckets = rebuckets
    return buckets, i, got, mayor_voted


def parse_meeting(lines):
    n = len(lines)
    votes = []
    i = 0
    while i < n:
        line = lines[i]
        mv = MOVE_RE.search(line)
        if not mv:
            i += 1
            continue
        mover = norm_name(mv.group(1) + " " + mv.group(2))
        is_board = re.match(r"\s*Board", mv.group(1), re.I) is not None
        # collect motion text + look ahead for seconder, result narrative, and grid
        seconder = None
        motion_parts = [line[mv.start():].strip()]
        j = i + 1
        grid = None
        result_line = None
        # scan forward a bounded window for the seconder, result, and grid header
        scan_limit = min(n, i + 40)
        while j < scan_limit:
            lj = lines[j]
            sj = lj.strip()
            if seconder is None:
                sm = SECOND_RE.search(lj)
                if sm:
                    seconder = norm_name(sm.group(1) + " " + sm.group(2))
                    motion_parts.append(lj[:sm.start()].strip())
                    j += 1
                    continue
            # grid header?
            if find_columns(lj):
                g = parse_grid(lines, j)
                if g:
                    grid = g
                    break
            # a fresh motion before any grid -> this motion had no roll-call grid
            if j > i and MOVE_RE.search(lj):
                break
            if result_line is None and (OUTCOME_UNANIMOUS.search(sj) or
                                        OUTCOME_FAIL.search(sj) or
                                        OUTCOME_TALLY.search(sj) or VOICE_RE.search(sj)):
                result_line = sj
            if seconder is None and len(motion_parts) < 12:
                motion_parts.append(sj)
            j += 1

        # BOARD OF CANVASSERS (ceremonial certification body): capture a "Board Member"-
        # moved motion ONLY when it carries a named roll-call GRID (the canvass
        # certification, e.g. Resolution #25-42). A "Board Member"-moved motion with NO
        # grid is the pro-forma tally-only adjournment — non-legislative trivia that would
        # otherwise add a blank placeholder row; skip it. (Regular meetings' Councilmember-
        # moved tally-only motions are unaffected — this guard is scoped to the Board title.)
        if is_board and grid is None:
            i = max(j, i + 1)
            continue

        motion_text = re.sub(r"\s+", " ", " ".join(p for p in motion_parts if p)).strip(" .;,")
        motion_text = re.split(r"\.\s+" + NAME_PREFIX + r"\s+\S+\s+seconded",
                               motion_text, flags=re.I)[0].strip(" .;,")
        mtype = classify_motion(motion_text)

        # find a result narrative in the window i..(grid end or scan)
        window = " ".join(x.strip() for x in lines[i:(grid[1] if grid else j)])
        outcome, tally = result_from(window)

        buckets = grid[0] if grid else {"aye": [], "nay": [], "abstain": [],
                                        "absent": [], "recuse": []}
        mayor_voted = grid[3] if grid else False
        names_recorded = grid is not None
        if grid:
            # DRIFT COLLAPSE: pdftotext -layout column positions drift right on later
            # pages (a page break can split a grid), and the Yes/No columns sit only ~3
            # chars apart — so a page-2 "Yes" X can land under "No". When the outcome is
            # UNANIMOUS (printed N-0 or narrative "unanimously"), there are provably ZERO
            # real No votes, so any 'nay' here is a drift artifact -> fold it into 'aye'.
            # Absent/Abstain/Recuse (well-separated, further right) are kept as mapped.
            # Genuinely contested grids (real dissent) are NOT collapsed; the validator
            # cross-checks named counts vs the printed tally and flags any residual.
            unanimous = (tally is not None and tally[1] == 0) or \
                (OUTCOME_UNANIMOUS.search(window) and outcome == "Pass" and tally is None)
            if unanimous and buckets["nay"]:
                for nm in buckets["nay"]:
                    if nm not in buckets["aye"]:
                        buckets["aye"].append(nm)
                buckets["nay"] = []
            na, nn = len(buckets["aye"]), len(buckets["nay"])
            if tally is None:
                tally = (na, nn)
            result_str = f"{na}-{nn} {outcome}"
        else:
            # 2020-2021 NARRATIVE form: named voters are listed in prose, not a grid
            n_aye, n_nay, found = parse_narrative(window)
            if found:
                buckets["aye"], buckets["nay"] = n_aye, n_nay
                names_recorded = True
                if tally is None:
                    tally = (len(n_aye), len(n_nay))
                # printed tally is authoritative for the result string; when it exceeds the
                # named count the source named only the in-favor side (dissenters honestly
                # unnamed) — the validator surfaces the gap, we never invent the nays.
                result_str = f"{tally[0]}-{tally[1]} {outcome}"
            elif tally:
                result_str = f"{tally[0]}-{tally[1]} {outcome}"
            elif outcome == "Fail":
                result_str = "Died/Failed (no roll call)"
            else:
                result_str = "Unanimous (voice/tally-only)"

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
            "mayor_voted": mayor_voted,
        })
        i = grid[1] if grid else max(j, i + 1)
    return votes


def result_from(window):
    """(outcome, printed_tally|None) from a result narrative window."""
    if OUTCOME_FAIL.search(window):
        m = OUTCOME_TALLY.search(window)
        return "Fail", ((int(m.group(1)), int(m.group(2))) if m else None)
    m = OUTCOME_TALLY.search(window)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return ("Pass" if a >= b else "Fail"), (a, b)
    vm = VOICE_RE.search(window)
    if vm and vm.group(1):
        return "Pass", (int(vm.group(1)), int(vm.group(2)))
    if OUTCOME_UNANIMOUS.search(window) or vm:
        return "Pass", None
    return "Pass", None


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
        votes = parse_meeting(load_rows(path))
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
