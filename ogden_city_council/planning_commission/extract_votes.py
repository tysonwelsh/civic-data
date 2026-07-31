#!/usr/bin/env python3
"""
extract_votes.py - Ogden City PLANNING COMMISSION vote extractor (PURE REGEX).

No LLM / network. Reads planning_commission/minutes_index.csv, parses each minutes
markdown file, emits one JSON per meeting under
  planning_commission/votes/<year>/<week-monday>/<date>_planning-commission-meeting.json
then rebuilds planning_commission/all_votes.csv (long format, one row per member-vote,
13-col schema identical to the council extractor) and planning_commission/roster.csv.

TWO source formats coexist (see CLAUDE.md):
  * 2020-2023 (+4 in 2024) = BORN-DIGITAL, mixed case:
      "MOTION: A motion was made by Commissioner Garner to recommend approval ...
       Motion was seconded by Commissioner Graf and passed unanimously, with
       Commissioners Blaisdell, Boykin, ... and Southwick voting aye."
      "... passed 7-1 with Commissioners A,B... voting aye and Commissioner Z voting no."
  * 2024-2026 = OCR'd, UPPERCASE roll-call (same shape as the council minutes):
      "COMMISSIONER X MOVED TO ... MOTION WAS SECONDED BY COMMISSIONER Y AND PASSED
       UPON BY THE FOLLOWING ROLL CALL VOTE: VOTING AYE - COMMISSIONERS AABERG, ROSS,
       SANDAU, SHALE, AKHMEDOV, AND CHAIR SHINODA. VOTING NO - NONE."
      "COMMISSIONER X MADE A MOTION TO ... COMMISSIONER Y SECONDED THE MOTION, ALL VOTING AYE."

CARDINAL RULE: never fabricate. Tally-only / "ALL VOTING AYE" with no per-member
names -> record the tally, names_recorded=False, EMPTY member lists, never guess.

The roster (surname -> display name) is reconstructed at runtime from the
"Members Present" / "Members Excused" headers, folding OCR variants (Jennifer/Jenny
Sandau, Jordon/Jordan Aaberg, Ahkmedov/Akhmedov) by multiset similarity.
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # planning_commission/
REPO = ROOT.parent                              # ogden_city_council/
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
OUT_CSV = ROOT / "all_votes.csv"
ROSTER_CSV = ROOT / "roster.csv"

BODY = "PlanningCommission"
TITLE = "Planning Commission"
CORRECTIONS_CSV = ROOT / "vote_corrections.csv"

# --- recovery-channel provenance ------------------------------------------
# Audited portal/DocumentCenter minutes carry NO provenance header comment ->
# 'minutes'. The 2026-07-19 gap recovery stamped each recovered file with a
# `<!-- provenance: ... -->` header that IS the ledger; the channel keyword in
# it distinguishes the two recovery classes. Channel-keyed (not date-keyed) so
# any future same-channel recovery tags itself. Every recovered PC file (and
# ONLY recovered files) carries this comment — a clean 1:1 marker.
PROVENANCE_RE = re.compile(r"<!--\s*provenance:(.*?)-->", re.S | re.I)

def classify_provenance(text):
    m = PROVENANCE_RE.search(text)
    if not m:
        return "minutes"                          # audited primary (no recovery header)
    if re.search(r"packet[\s-]*carve", m.group(1), re.I):
        return "packet_carve"                     # carved from a following-meeting agenda packet
    return "doccenter_draft"                       # standalone DocumentCenter draft minutes

ROLE_WORDS = re.compile(
    r"\b(VICE[\s-]*CHAIR|ACTING[\s-]*CHAIR|CHAIR|COMMISSIONERS?|MEMBERS?|VIA\s+ZOOM|"
    r"ONLINE|MR\.?|MS\.?|MRS\.?)\b", re.I)

# ---------------------------------------------------------------------------
# Similarity (OCR-tolerant): max of ordered-overlap ratio and multiset overlap.
# Multiset handles letter transpositions (AHKMEDOV vs AKHMEDOV -> 1.0).
# ---------------------------------------------------------------------------
def _ordered(a, b):
    if not a or not b:
        return 0.0
    i = j = m = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            m += 1; i += 1; j += 1
        elif len(a) - i > len(b) - j:
            i += 1
        else:
            j += 1
    return 2.0 * m / (len(a) + len(b))

def _sim(a, b):
    """OCR-tolerant similarity. Ordered-overlap ratio is primary. A near-identical
    letter *multiset* (>=0.92, length within 1) is accepted ONLY as a transposition
    rescue (AHKMEDOV vs AKHMEDOV -> 1.0). Without the length+0.92 guard the multiset
    over-matches prose anagrams (FOREST / stores / Others all share STOKER's letters)."""
    if not a or not b:
        return 0.0
    o = _ordered(a, b)
    if o >= 0.80:
        return o
    ca, cb = Counter(a), Counter(b)
    inter = sum((ca & cb).values())
    mset = 2.0 * inter / (len(a) + len(b))
    if mset >= 0.92 and abs(len(a) - len(b)) <= 1:
        return mset
    return o

def _norm(tok):
    return re.sub(r"[^A-Z]", "", tok.upper())

# ---------------------------------------------------------------------------
# Roster reconstruction
# ---------------------------------------------------------------------------
def split_name_line(line):
    """A header attendee line -> a clean 'First Last' or None."""
    line = line.strip().strip("|").strip("-").strip("—").strip()
    if not line:
        return None
    # cut at role / status delimiters (comma, dash, or any role/status keyword).
    # No PC commissioner has a hyphenated surname, so '-'/'—' are safe delimiters.
    line = re.split(r"[,\-—]|\bvia\b|\bVice\b|\bChair\b|\bZoom\b|\bOnline\b|\bOn\b|"
                    r"\bExcused\b|\bAbsent\b|\bPresent\b", line, flags=re.I)[0]
    line = re.sub(r"\s+", " ", line).strip(" -—")
    if not line or not re.match(r"^[A-Za-z .'’]+$", line):
        return None
    parts = line.split()
    if len(parts) < 2:
        return None
    # guard against staff/role lines leaking in
    if re.search(r"\b(Planner|Director|Manager|Attorney|Technician|Assistant|Engineer"
                 r"|Deputy|Senior|Administrative|Secretary)\b", line, re.I):
        return None
    return line

def attendee_blocks(text):
    """Return (present_names, excused_names) lists for one meeting."""
    def grab(label, stops):
        m = re.search(r"Members\s+" + label + r"\s*:?[\s—|-]*(.*?)(?:" + "|".join(stops) + r")",
                      text, re.S | re.I)
        if not m:
            return []
        names = []
        for ln in m.group(1).splitlines():
            nm = split_name_line(ln)
            if nm:
                names.append(nm)
        return names
    # NB "City Council" stop: the 2020-10-22 East Central Town Meeting minutes list
    # "Members Present" for the PC and then a separate "City Council / Members
    # Present" block — the capture must stop at that sub-heading so council
    # attendees (and the literal words "City Council") don't leak into the PC roster.
    present = grab("Present", [r"Members\s+Excused", r"Members\s+Absent",
                               r"Staff\s+Present", r"Others\s+Present",
                               r"City\s+Council", r"\n\s*\n\s*\d"])
    excused = grab("Excused", [r"Staff\s+Present", r"Others\s+Present", r"Members\s+Absent",
                               r"\n\s*\n"])
    excused += grab("Absent", [r"Staff\s+Present", r"Others\s+Present", r"\n\s*\n"])
    return present, excused

def build_roster(rows):
    """Scan every meeting's headers. Returns:
        SURNAMES: dict surname-token -> canonical display name
        stats:    dict display name -> {first_seen,last_seen,n_meetings}
    """
    name_counts = Counter()           # full-name spelling -> times present
    surname_full = defaultdict(Counter)   # surname token -> Counter(full names)
    seen = defaultdict(list)          # display surname -> [dates present]
    raw_present = []                  # (date, [surnames present])

    for r in rows:
        p = REPO / r["path"]
        if not p.exists():
            continue
        text = p.read_text(errors="replace")
        present, _excused = attendee_blocks(text)
        sset = []
        for nm in present:
            sn = _norm(nm.split()[-1])
            if len(sn) < 3:
                continue
            name_counts[nm] += 1
            surname_full[sn][nm] += 1
            sset.append(sn)
        raw_present.append((r["date"], sset))

    # Cluster surname tokens: frequent tokens are canonical; rare tokens fold into
    # the most similar frequent token (OCR variants), else stand alone.
    freq = {s: sum(c.values()) for s, c in surname_full.items()}
    canon_tokens = sorted([s for s, n in freq.items() if n >= 3],
                          key=lambda s: -freq[s])
    fold = {}      # token -> canonical token
    for s in surname_full:
        if s in canon_tokens:
            fold[s] = s
            continue
        best, bestsc = None, 0.0
        for c in canon_tokens:
            sc = _sim(s, c)
            if sc > bestsc:
                bestsc, best = sc, c
        fold[s] = best if (best and bestsc >= 0.80) else s

    # canonical display name per canonical token = most common full-name spelling
    merged_full = defaultdict(Counter)
    for s, ctr in surname_full.items():
        merged_full[fold[s]] += ctr
    SURNAMES = {}
    display_of_token = {}
    for ctok, ctr in merged_full.items():
        display = ctr.most_common(1)[0][0]
        display_of_token[ctok] = display
    # map every observed token (incl. folded variants) to the canonical display
    for s in surname_full:
        SURNAMES[s] = display_of_token[fold[s]]

    # stats per display name
    stats = defaultdict(lambda: {"first_seen": None, "last_seen": None, "n_meetings": 0})
    for date, sset in raw_present:
        seen_disp = set()
        for s in sset:
            disp = SURNAMES.get(s)
            if not disp:
                continue
            seen_disp.add(disp)
        for disp in seen_disp:
            st = stats[disp]
            st["n_meetings"] += 1
            if st["first_seen"] is None or date < st["first_seen"]:
                st["first_seen"] = date
            if st["last_seen"] is None or date > st["last_seen"]:
                st["last_seen"] = date
    return SURNAMES, dict(stats)

# ---------------------------------------------------------------------------
# Name matching against the roster
# ---------------------------------------------------------------------------
def make_canon(SURNAMES):
    toks = list(SURNAMES.keys())
    def canon(token):
        s = _norm(token)
        if len(s) < 3:
            return None
        if s in SURNAMES:
            return SURNAMES[s]
        best, bestsc = None, 0.0
        for t in toks:
            sc = _sim(s, t)
            if sc > bestsc:
                bestsc, best = sc, t
        if best and bestsc >= 0.80:
            return SURNAMES[best]
        return None
    return canon

CONNECTORS = {"COMMISSIONER", "COMMISSIONERS", "CHAIR", "VICE", "MEMBER", "MEMBERS", "AND"}

def names_from_segment(seg, canon):
    """Pull roster display names out of an AYE/NO segment.

    Connector-aware: a surname is accepted ONLY when it directly follows a connector
    (COMMISSIONER(S)/CHAIR/VICE/AND or a comma/colon/dash). This captures clean comma
    lists ('AABERG, ROSS, SANDAU ... AND CHAIR SAFSTEN') AND multi-dissenter NO lists
    interleaved with explanation prose ('COMMISSIONER AABERG, STATING ... AND
    COMMISSIONER ROSS, WHO FELT ...') without ever picking up a surname that merely
    appears inside narrative text (it would not be preceded by a connector)."""
    if not seg:
        return []
    up = seg.upper()
    if re.search(r"\bNONE\b", up) and not re.search(r"COMMISSIONER", up):
        return []
    toks = re.findall(r"[A-Z'’]+|[,:;.—\-]", up)
    out = []
    expect = True          # the segment opens right after 'VOTING NO —'
    for tok in toks:
        if tok in (",", ":", ";", ".", "—", "-"):
            # '.' is a separator too: OCR writes 'GARNER. SANDAU' for 'GARNER, SANDAU'
            expect = True
            continue
        if tok in CONNECTORS:
            expect = True
            continue
        nm = canon(tok) if expect else None
        if nm:
            if nm not in out:
                out.append(nm)
            expect = False     # need another connector before the next name
        else:
            expect = False     # a prose word ends the current name run
    return out

# ---------------------------------------------------------------------------
# Roll-call / vote-block parsing
# ---------------------------------------------------------------------------
def parse_ocr_rollcall(block, canon):
    """OCR uppercase form: 'VOTING AYE - <list>. VOTING NO - <list>.'
    AYE and NO captured INDEPENDENTLY, each spanning line wraps ([\s\S]); the NO
    list ends at the first sentence period so trailing prose can't leak. Anchoring
    on roster surnames means explanatory prose ('STATING HE THOUGHT...') is ignored.
    Returns (aye, nay) or None when no enumerated AYE list is present."""
    # AYE runs to the next 'VOTING NO' or the sentence period. Do NOT bound on a blank
    # line: OCR routinely injects a blank line right after 'COMMISSIONERS' and before the
    # name list, which would truncate the whole list. The connector-aware name extractor
    # guards against any trailing prose being mistaken for a voter.
    ma = re.search(r"(?<!ALL\s)VOTING\s*AYE\s*[-–—:~]+\s*([\s\S]{0,600}?)"
                   r"(?=VOTING\s*NO\b|\.\s|\.\n|\.$|$)", block, re.I)
    if not ma:
        return None
    aye = names_from_segment(ma.group(1), canon)
    nay = []
    mn = re.search(r"VOTING\s*NO\s*[-–—:~]+\s*([\s\S]{0,500}?)"
                   r"(?=\.\s|\.\n|\.$|\n\s*\n|$)", block, re.I)
    if mn:
        nay = names_from_segment(mn.group(1), canon)
    if not aye and not nay:
        return None
    return aye, nay

def parse_born_rollcall(block, canon):
    """Born-digital form: 'with Commissioners <list> voting aye [and Commissioner(s)
    <list> voting no]'. Returns (aye, nay) or None.

    The leading 'with' is matched OCR/typo-tolerantly: a one-char corruption of the
    word ('wit' — dropped h, 2020-05-06 m9; 'wth' — dropped i; 'w ith' — split by a
    stray space) is accepted so the named roll isn't silently dropped to tally-only.
    The alternation is explicit (not a loose `w\\w*`) and remains gated by the strong
    `Commissioners? … voting aye` frame, so it cannot fire inside narrative prose."""
    ma = re.search(r"\b(?:with|wit|wth|w\s+ith)\s+Commissioners?\s+([\s\S]{0,400}?)\s+voting\s+aye",
                   block, re.I)
    if not ma:
        return None
    aye = names_from_segment(ma.group(1), canon)
    nay = []
    mn = re.search(r"voting\s+aye\s+and\s+(?:Commissioners?|Vice[\s-]*Chair|Chair)?\s*"
                   r"([\s\S]{0,300}?)\s+voting\s+no", block, re.I)
    if mn:
        nay = names_from_segment(mn.group(1), canon)
    if not aye and not nay:
        return None
    return aye, nay

# ---------------------------------------------------------------------------
# Motion typing + recommendation/final classification
# ---------------------------------------------------------------------------
def motion_type(text):
    t = text.upper()
    if re.search(r"\bAGENDA\b", t) and re.search(r"APPROVE|ADOPT|AMEND", t):
        return "Procedural/Administrative"
    if "MINUTES" in t and re.search(r"APPROVE|ADOPT|AS PREPARED|AS PRESENTED|AS AMENDED|AS CORRECTED", t):
        return "Procedural/Administrative"
    if re.search(r"\bADJOURN", t):
        return "Procedural/Administrative"
    if re.search(r"PUBLIC HEARING", t) and re.search(r"CLOSE|OPEN|CONTINUE", t):
        return "Procedural/Administrative"
    if re.search(r"\bELECT\b|NOMINAT|OFFICER", t) and re.search(r"CHAIR|VICE|OFFICER", t):
        return "Procedural/Administrative"
    if re.search(r"\bTABL|CONTINU|POSTPON|RECESS|WITHDRAW", t):
        return "Procedural/Administrative"
    # Specific petition types FIRST: the substantive object of "approve/recommend the X"
    # wins over boilerplate findings language ("consistent with the General Plan", "comply
    # with land use ordinances") that appears in nearly every motion.
    if re.search(r"CONDITIONAL USE", t):
        return "Conditional Use Permit"
    if re.search(r"DESIGN REVIEW", t):
        return "Design Review"
    if re.search(r"SITE PLAN", t):
        return "Site Plan"
    if re.search(r"ANNEX", t):
        return "Annexation"
    if re.search(r"VACAT", t):
        return "Street/Alley Vacation"
    if re.search(r"REZON|RECLASSIF|ZONING MAP|ZONE CHANGE|ZONING CHANGE|CHANGE.{0,12}ZON", t):
        return "Rezone"
    if re.search(r"SUBDIVI|\bPLAT\b|PRUD|CONDOMINIUM", t):
        return "Subdivision/Plat"
    if re.search(r"(GENERAL PLAN|ZONING|LAND USE CODE|TEXT|ORDINANCE|COMMUNITY PLAN|"
                 r"SPECIFIC PLAN).{0,20}AMENDMENT|"
                 r"AMEND\w*\s+.{0,40}(GENERAL PLAN|COMMUNITY PLAN|ZONING|ORDINANCE|"
                 r"LAND USE CODE|PLAN\b)|TEXT AMENDMENT|ORDINANCE AMENDMENT", t):
        return "Zoning Text/General Plan Amendment"
    return "Other"

PROCEDURAL_RE = re.compile(
    r"\bAGENDA\b|\bMINUTES\b|\bADJOURN|PUBLIC HEARING|\bELECT\b|NOMINAT|"
    r"\bTABL|CONTINU|POSTPON|RECESS|WITHDRAW|OFFICER", re.I)
# A *recommendation to Council*, NOT "subject to staff RECOMMENDED conditions".
# Require the recommend verb to be followed by approval/denial/preliminary/that/the,
# or an explicit forward-to-Council / recommendation-of-(approval|denial) phrase.
RECOMMEND_RE = re.compile(
    r"\bRECOMMEND(?:S|ING)?\s+(?:PRELIMINARY\s+|FINAL\s+|CONDITIONAL\s+)?"
    r"(?:APPROVAL|DENIAL|APPROVE|DENY|THAT|THE\b)|"
    r"RECOMMENDATION\s+(?:OF|FOR)\s+(?:APPROVAL|DENIAL)|"
    r"FORWARD.{0,40}\bCOUNCIL\b|"
    r"\bTO\s+THE\s+(?:CITY\s+)?COUNCIL\b", re.I)
NEG_RE = re.compile(r"\bDENY\b|\bDENIAL\b|\bDENIED\b|\bREJECT", re.I)

def classify_result(motion, aye, nay, names_recorded, explicit_tally, unanimous):
    up = motion.upper()
    # counts string
    if names_recorded:
        counts = f"{len(aye)}:{len(nay)}"
        have_nums = True
        a, n = len(aye), len(nay)
    elif explicit_tally:
        a, n = explicit_tally
        counts = f"{a}:{n}"
        have_nums = True
    elif unanimous:
        counts = "unanimous"; have_nums = False; a = n = 0
    else:
        counts = "recorded"; have_nums = False; a = n = 0

    if have_nums:
        passed = a > n
    else:
        passed = True   # 'passed unanimously' / 'ALL VOTING AYE' / voice pass

    mtype = motion_type(motion)
    is_proc = (mtype == "Procedural/Administrative")
    verb_negative = bool(NEG_RE.search(up))
    base_positive = not verb_negative
    effective_positive = (base_positive == passed)

    if is_proc:
        return (f"{counts} Pass" if passed else f"{counts} Fail"), "procedural"
    # Ogden PC: rezones / zoning + general-plan amendments / subdivisions / annexations /
    # street vacations are RECOMMENDATIONS forwarded to the City Council (Council finalizes
    # the ordinance). CUP / design review / site plan are the PC's own FINAL ACTIONS. The
    # explicit "recommend approval/denial ... to Council" verb also forces a recommendation.
    if mtype in FINAL_TYPES:
        is_rec = False
    elif mtype in REC_TYPES or RECOMMEND_RE.search(up):
        is_rec = True
    else:
        is_rec = False
    if is_rec:
        sign = "Positive recommendation" if effective_positive else "Negative recommendation"
        return f"{sign} {counts}", "recommendation"
    disp = "Approved" if effective_positive else "Denied"
    return f"{counts} {disp} (Final Action)", "final"

REC_TYPES = {"Rezone", "Zoning Text/General Plan Amendment", "Subdivision/Plat",
             "Annexation", "Street/Alley Vacation"}
FINAL_TYPES = {"Conditional Use Permit", "Design Review", "Site Plan"}

# ---------------------------------------------------------------------------
# Motion finding
# ---------------------------------------------------------------------------
MOVER_OCR = re.compile(r"COMMISSIONER\s+([A-Z][A-Za-z'’-]+)\s+(?:MADE A MOTION|MOVED)")
MOVER_OCR2 = re.compile(r"([A-Z][A-Z'’-]{3,})\s+MOVED\b")   # 'WILLIAMS MOVED'
MOVER_BORN = re.compile(r"motion was (?:then\s+|again\s+|also\s+)?made by\s+"
                        r"Commissioner\s+([A-Za-z'’-]+)", re.I)
SEC_OCR = re.compile(r"SECONDED BY\s+(?:VICE\s*CHAIR|CHAIR|COMMISSIONER)?\s*([A-Z][A-Za-z'’-]+)")
SEC_OCR2 = re.compile(r"COMMISSIONER\s+([A-Z][A-Za-z'’-]+)\s+SECONDED")
SEC_BORN = re.compile(r"seconded by\s+(?:Vice\s*Chair|Chair|Commissioner)?\s*([A-Za-z'’-]+)", re.I)

ANCHOR = re.compile(r"(?i:motion was (?:then\s+|again\s+|also\s+)?made by)|"
                    r"MADE A MOTION|\bMOVED\b")

def find_motions(text, canon):
    flat = re.sub(r"\n\s*Minutes of .*?Page\s*\d*\s*\n", "\n", text)
    flat = re.sub(r"\n\s*Page\s*\d*\s*\n", "\n", flat)
    # inline running footers: the born-digital drafts print "Page N of M" (and
    # "Page | N") wherever the page break fell — including MID roll-call list
    # ("passed 8-1 with Commissioners Page 9 of 13 Blaisdell, ..."), which broke
    # the connector chain and silently dropped the first voter after the footer.
    flat = re.sub(r"Page\s*\|?\s*\d+\s+of\s+\d+", " ", flat)
    flat = re.sub(r"Page\s*\|\s*\d+", " ", flat)

    anchors = sorted(set(m.start() for m in ANCHOR.finditer(flat)))
    # merge anchors that are very close (same motion mentioned twice)
    merged = []
    for a in anchors:
        if merged and a - merged[-1] < 25:
            continue
        merged.append(a)
    anchors = merged

    motions = []
    for ai, start in enumerate(anchors):
        end = anchors[ai + 1] if ai + 1 < len(anchors) else len(flat)
        # The vote block always sits between this motion's anchor and the NEXT anchor,
        # so the window is exactly [start, end). Extending past `end` double-counts the
        # next motion's roll-call (a public-hearing-close motion stealing the rezone vote).
        seg = flat[start:end]

        # ---- mover / seconder
        # The OCR anchor sits ON 'MADE A MOTION'/'MOVED', so the mover ('COMMISSIONER X')
        # precedes the window start -- look back a little to catch it.
        mover = seconder = None
        mover_win = flat[max(0, start - 80):start + 60]
        m = (MOVER_OCR.search(mover_win) or MOVER_BORN.search(mover_win)
             or MOVER_OCR2.search(mover_win))
        if m:
            mover = canon(m.group(1))
        ms = SEC_OCR.search(seg) or SEC_OCR2.search(seg) or SEC_BORN.search(seg)
        if ms:
            seconder = canon(ms.group(1))

        # ---- vote block
        named = parse_ocr_rollcall(seg, canon)
        if named is None:
            named = parse_born_rollcall(seg, canon)

        aye, nay, abstain, absent, recuse = [], [], [], [], []
        names_recorded = False
        if named is not None:
            aye, nay = list(named[0]), list(named[1])
            names_recorded = bool(aye or nay)

        # recuse / abstain near this vote (both cases). Stay within this motion's
        # window (seg) so a later motion's recusal note is not pulled forward.
        tail = seg
        for rm in re.finditer(
                r"(?:COMMISSIONER|CHAIR|Commissioner|Chair)\s+([A-Za-z'’-]+)\s+"
                r"(?:HAD\s+)?(?:RECUSED|recused)\b", tail):
            nm = canon(rm.group(1))
            if nm and nm not in recuse:
                recuse.append(nm)
        for rm in re.finditer(
                r"(?:COMMISSIONER|CHAIR|Commissioner|Chair)\s+([A-Za-z'’-]+)\s+"
                r"(?:WAS\s+)?(?:ABSTAIN|abstain)", tail):
            nm = canon(rm.group(1))
            if nm and nm not in abstain:
                abstain.append(nm)
        for L in (recuse, abstain):
            for nm in L:
                if nm in aye: aye.remove(nm)
                if nm in nay: nay.remove(nm)
        # Source contradiction guard (never fabricate): if the minutes list a member in
        # BOTH aye and nay (a clerk typo, e.g. 2020-07-01 m9 'Stoker' in both), keep the
        # aye placement (it matches the stated tally count) and drop the duplicate nay.
        for nm in list(nay):
            if nm in aye:
                nay.remove(nm)

        # ---- motion text (the substantive action, between the anchor and the vote).
        # Normalize whitespace FIRST so the cut markers ('MOTION WAS SECONDED') still match
        # when the clerk wrapped them across a line break.
        mt = re.sub(r"\s+", " ", seg)
        cut = re.search(r"FOLLOWING ROLL CALL|ALL VOTING AYE|ALL VOTED AYE|VOTING AYE|"
                        r"passed unanimously|passed \d|PASSED UPON|by a voice vote|"
                        r"\bSECONDED\b", mt, re.I)
        if cut:
            mt = mt[:cut.start()]
        mt = mt.strip()
        # strip the motion-introduction preamble, keeping the action ("to ...").
        # NB: require a colon on the MOTION label so the *word* "motion" in
        # "motion was made by" is not eaten.
        mt = re.sub(r"^MOTION\s*:\s*", "", mt, flags=re.I)
        mt = re.sub(r"^(?:A\s+)?motion was (?:then\s+|again\s+|also\s+)?made by\s+"
                    r"Commissioner\s+\S+\s+", "", mt, flags=re.I)
        mt = re.sub(r"^COMMISSIONER\s+\S+\s+(?:MADE A MOTION|MOVED)\s*",
                    "", mt, flags=re.I)
        mt = re.sub(r"^\S+\s+MOVED\s+", "", mt)  # 'WILLIAMS MOVED THE MEETING ...'
        mt = mt.strip().strip(".,").strip()[:600]
        if not mt:
            mt = re.sub(r"\s+", " ", seg).strip()[:200]

        # ---- explicit tally + unanimous flags
        explicit_tally = None
        et = re.search(r"(?:passed|failed|carried)\s+(\d+)\s*[-–]\s*(\d+)", seg, re.I)
        if et:
            explicit_tally = (int(et.group(1)), int(et.group(2)))
        unanimous = bool(re.search(r"passed unanimously|ALL VOTING AYE|ALL VOTED AYE|"
                                   r"UNANIMOUS", seg, re.I))

        result, classification = classify_result(
            mt, aye, nay, names_recorded, explicit_tally, unanimous)

        motions.append({
            "motion_no": len(motions) + 1,
            "body": BODY,
            "motion": mt,
            "motion_type": motion_type(mt),
            "result": result,
            "classification": classification,
            "mover": mover, "seconder": seconder,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
            "names_recorded": names_recorded,
            "unanimous": unanimous,
            "explicit_tally": list(explicit_tally) if explicit_tally else None,
        })
    return motions

# ---------------------------------------------------------------------------
# Documented vote corrections (planning_commission/vote_corrections.csv)
# ---------------------------------------------------------------------------
# The 2020-2023 born-digital drafts contain a recurring clerk-typo class where a
# failed motion prints BOTH name lists as "voting aye" (the second list should
# read "voting no"). Left as parsed, the second list is dropped and the motion
# reads N:0 PASSED — reversing the true outcome. Corrections are applied ONLY
# from vote_corrections.csv, each row citing its city source (an approved
# correction in the following meeting's minutes, or the motion's own printed
# tally). The minutes markdown stays verbatim; this hook fixes the DERIVED vote
# rows only. A snippet that matches zero or 2+ motions is NOT applied (warns).
def load_corrections():
    out = defaultdict(list)
    if CORRECTIONS_CSV.exists():
        for r in csv.DictReader(open(CORRECTIONS_CSV)):
            out[r["date"].strip()].append(r)
    return out

def apply_corrections(date, motions, canon, corrections):
    for c in corrections.get(date, []):
        hits = [m for m in motions
                if c["match_snippet"].lower() in (m["motion"] or "").lower()]
        if len(hits) != 1:
            print(f"WARNING vote_corrections {date}: snippet matched {len(hits)} "
                  f"motions — NOT applied", file=sys.stderr)
            continue
        mo = hits[0]
        if c["set_aye"].strip():
            mo["aye"] = [canon(t.strip()) for t in c["set_aye"].split(";") if canon(t.strip())]
        if c["set_nay"].strip():
            mo["nay"] = [canon(t.strip()) for t in c["set_nay"].split(";") if canon(t.strip())]
        mo["names_recorded"] = True
        et = tuple(mo["explicit_tally"]) if mo.get("explicit_tally") else None
        mo["result"], mo["classification"] = classify_result(
            mo["motion"], mo["aye"], mo["nay"], True, et, mo["unanimous"])
        mo["correction_source"] = c["source"]
    return motions

# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def load_index():
    rows = []
    with open(INDEX, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({k: (v.strip() if isinstance(v, str) else v) for k, v in r.items()})
    return rows

def json_path(rel):
    jrel = rel.replace("planning_commission/minutes/", "", 1)
    return (VOTES_DIR / jrel).with_suffix(".json")

def main(rebuild_only=False):
    rows = load_index()
    SURNAMES, stats = build_roster(rows)
    canon = make_canon(SURNAMES)
    corrections = load_corrections()

    processed = 0
    for r in rows:
        path = REPO / r["path"]
        if not path.exists():
            continue
        jpath = json_path(r["path"])
        if rebuild_only and jpath.exists():
            processed += 1
            continue
        text = path.read_text(errors="replace")
        motions = find_motions(text, canon)
        motions = apply_corrections(r["date"], motions, canon, corrections)
        jpath.parent.mkdir(parents=True, exist_ok=True)
        obj = {
            "date": r["date"], "year": int(r["year"]), "title": TITLE,
            "body": BODY, "format": r.get("format", ""), "source": r["path"],
            "provenance": classify_provenance(text),
            "votes": motions,
        }
        jpath.write_text(json.dumps(obj, indent=1))
        processed += 1

    rebuild_csv(rows)
    write_roster(stats)
    return processed, SURNAMES, stats

def rebuild_csv(rows):
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    out = []
    for r in rows:
        jpath = json_path(r["path"])
        if not jpath.exists():
            continue
        obj = json.loads(jpath.read_text())
        prov = obj.get("provenance", "minutes")
        for mo in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=TITLE, body=BODY,
                        motion_no=mo["motion_no"], motion=mo["motion"],
                        motion_type=mo["motion_type"], result=mo["result"],
                        mover=mo.get("mover") or "", seconder=mo.get("seconder") or "",
                        source=obj["source"], provenance=prov)
            members = ([(m, "Aye") for m in mo["aye"]] + [(m, "Nay") for m in mo["nay"]] +
                       [(m, "Abstain") for m in mo["abstain"]] +
                       [(m, "Absent") for m in mo["absent"]] +
                       [(m, "Recuse") for m in mo["recuse"]])
            if members:
                for mem, v in members:
                    row = dict(base); row["member"] = mem; row["vote"] = v
                    out.append(row)
            else:
                row = dict(base); row["member"] = ""; row["vote"] = ""
                out.append(row)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in out:
            w.writerow(row)
    return len(out)

def write_roster(stats):
    with open(ROSTER_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for name in sorted(stats, key=lambda n: (-stats[n]["n_meetings"], n)):
            st = stats[name]
            w.writerow([name, st["first_seen"], st["last_seen"], st["n_meetings"]])

if __name__ == "__main__":
    n, SURNAMES, stats = main(rebuild_only="--rebuild" in sys.argv)
    print(f"processed {n} meetings -> {OUT_CSV}")
    print(f"roster: {len(stats)} commissioners -> {ROSTER_CSV}")
