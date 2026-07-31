#!/usr/bin/env python3
"""
extract_votes.py — Taylorsville (Utah) Planning Commission vote extractor.

PURE deterministic (no LLM, no network, resumable). Reads the PC minutes markdown
listed in planning_commission/minutes_index.csv, parses every recorded motion +
its vote, writes one JSON per meeting under
planning_commission/votes/<year>/<week-monday>/<slug>.json, then rebuilds
planning_commission/all_votes.csv (13-col long format, one row per member-vote;
body="PlanningCommission", title="Planning Commission" on EVERY row) and roster.csv.

THREE vote-grammar formats — the parser handles ALL THREE, unified on the `MOTION:`
header as the primary anchor (present across every year):

 1. NARRATIVE TALLY (2020-2023, all years for consent/adjourn):
      MOTION: Commissioner X - I move to approve the Consent Agenda ...
      SECOND: Commissioner Y.
      VOTE: All Commissioners voted in favor. Motion passes unanimously.
    -> tally-only, names NOT listed -> names_recorded:false, EMPTY member lists.

 2. NAMED INLINE ROLL-CALL (2020-2024):
      VOTE:/ROLL CALL VOTE: Commissioner Wright - AYE, Commissioner McElreath - AYE,
      ... Commissioner Willardson - NAY. Motion passes 6 to 1.
    -> each named vote captured (labels wrap across pdftotext line breaks -> region
       is FLATTENED before token matching).

 3. TABULAR ROLL-CALL (2024-12 onward, 2025-2026):
      Commissioner Wendel     Aye
      Commissioner Quigley    Aye
      Commissioner McElreath: Absent
      Motion Passed 6-1
    -> one member per line (colon or space separated); page-break footers flattened
       out first so the block is contiguous.

 Plus PROSE outcomes woven into the MOTION block (2024-2026):
      "... seconded by Commissioner X and passed unanimously."
      "... passed unanimously, although both Commissioners Wendel and Wilkey abstained."
      "... passed with one abstention (Commissioner Wilkey)."
      "... with Chair Wilkey recusing herself ..."
    -> tally-only for the (unnamed) majority, BUT the explicitly-named abstainer/recuser
       is captured faithfully into abstain/recuse (source names them). names_recorded
       stays False because the assenting majority is never named.

 Secondary pass: 2020-2023 "ADJOURNMENT: By motion of Commissioner X ..." adjournments
 that carry no MOTION: header (2024+ adjourns use a MOTION: header, primary pass).

RESULT / DIRECTION taxonomy (encoded in `result`, city-faithful tally kept verbatim):
 - motion text has "recommend"/"forward" -> RECOMMENDATION to City Council:
     "Positive recommendation N-M" / "Negative recommendation N-M"
     (rezones / text amendments / general-plan / plats forwarded to Council)
 - else -> PC FINAL ACTION (CUP / site-plan / preliminary-plat / permitted use):
     "N-M Approved (Final Action)" / "N-M Denied (Final Action)"
 - procedural (minutes / consent / adjourn / table / continue / elect chair) -> "N-M Pass".
 Direction: a positive-rec motion that FAILS forwards a Negative recommendation, and a
 carried "deny/revoke" is a Denial (XOR of proposes-approval and passed).

CASE NUMBERS: <seq><letter><yy> (12Z20 Z=rezone/text, 2G20 G=general-plan, 1S21 S=subdivision,
 3P23 P=permitted-use site plan, 8C22/CUP-... C=conditional use) captured from the motion
 text (falls back to the nearest preceding "File #<code>" item header) into motion["case_no"].

CARDINAL RULE — never fabricate. Unanimous/tally-only stays names_recorded:false with empty
 lists; an OCR-garbled name that cannot be resolved to the roster is dropped (never guessed);
 the printed numeric tally is kept as tally_text and cross-checked (never auto-corrected).
"""
import csv
import json
import re
import sys
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent            # planning_commission/
MIN_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
OUT_CSV = ROOT / "all_votes.csv"
ROSTER_CSV = ROOT / "roster.csv"

BODY = "PlanningCommission"
TITLE = "Planning Commission"

# ---------------------------------------------------------------------------
# Roster.  surname(lower) -> canonical display name.  Built from the per-meeting
# attendance headers across 2020->2026 (see roster.csv); the set drifts:
#   2020-2021: Barbieri/Burggraaf/McElreath/Quigley/Wendel/Wright/Willardson/Russell
#   2023+:     +Wilkey +Young        2025+: +Munoz      2026: +Murphy (alternate)
# OCR spelling variants folded via SURNAME_VARIANTS + a difflib fuzzy fallback.
# ---------------------------------------------------------------------------
SURNAME_MAP = {
    "quigley": "Don Quigley",
    "wright": "David Wright",
    "wendel": "Lynette Wendel",
    "mcelreath": "Marc McElreath",
    "wilkey": "Cindy Wilkey",
    "burggraaf": "Kent Burggraaf",
    "russell": "Don Russell",
    "willardson": "Gordon Willardson",
    "young": "David Young",
    "barbieri": "Anna Barbieri",
    "munoz": "Barbara Munoz",
    "murphy": "B. Murphy",          # alternate, seated 2026 (moves motions; never in a roll call)
}
# explicit OCR / typo variants -> canonical surname key
SURNAME_VARIANTS = {
    "wendell": "wendel", "wendal": "wendel", "wendelwho": "wendel",
    "wikley": "wilkey",
    "berggraaf": "burggraaf",
    "russel": "russell", "rusell": "russell",
    "willard": "willardson",
    "mufioz": "munoz", "mufoz": "munoz", "mujioz": "munoz", "muioz": "munoz",
    "quigly": "quigley",
    "mcelreth": "mcelreath", "melreath": "mcelreath",
}
# Unambiguous given names (Don/David are shared -> deliberately excluded).
FIRST_MAP = {
    "marc": "Marc McElreath",
    "kent": "Kent Burggraaf",
    "cindy": "Cindy Wilkey",
    "gordon": "Gordon Willardson",
    "lynette": "Lynette Wendel",
    "anna": "Anna Barbieri",
    "barbara": "Barbara Munoz",
}
SURNAMES = list(SURNAME_MAP.keys())

# SAFE full-name gate (memory: prefer-full-name-vote-resolution): a surname fold is rejected
# ONLY when the token immediately preceding the matched surname names a DIFFERENT roster
# member. LATENT hardening — every PC surname is unique (and the two shared first names,
# Don/David, are already excluded from FIRST_MAP), so the gate never fires (proven by
# byte-identical all_votes.csv); it guards a FUTURE second same-surname commissioner (the
# Provo Deborah/Lisa Jensen failure mode), never altering today's output. First-name folds
# (FIRST_MAP) are unaffected — the gate applies only to the surname exact/variant/fuzzy paths.
_FIRST_TO_FULL = {full.split()[0].lower(): full for full in SURNAME_MAP.values()}


def _reject_surname_fold(pfx, cand):
    """True iff the token `pfx` preceding the surname names a DIFFERENT roster member.
    Folds through nicknames (pfx not a known first name) and the member's own first name."""
    if not pfx:
        return False
    pfx = re.sub(r"[^a-z]", "", pfx.lower())
    if len(pfx) < 2:
        return False
    cand_first = cand.split()[0].lower()
    if pfx == cand_first:                 # this member's own first name -> fold
        return False
    if cand_first.startswith(pfx):        # a nickname/prefix of the own first name -> fold
        return False
    mapped = _FIRST_TO_FULL.get(pfx)
    return mapped is not None and mapped != cand   # a known OTHER member -> reject the fold


def _pfx_word(words, w):
    """Token immediately preceding the first occurrence of `w` in the ORIGINAL word order."""
    try:
        idx = words.index(w)
    except ValueError:
        return None
    return words[idx - 1] if idx > 0 else None

# name-resolution stats (OCR fuzzy-match rate) — written to votes/_extract_stats.json
_STATS = {"resolutions": 0, "fuzzy": 0, "variant": 0}

ROLE_RE = re.compile(
    r"\b(commissioners?|commissioner['’]s|vice[-\s]*chair(?:man|woman|person)?|"
    r"acting[-\s]*chair|chair(?:man|woman|person)?|chair|alternate|mayor|staff|"
    r"councilman|councilmembers?|council)\b", re.I)


def _clean_token(tok):
    tok = tok.replace("’", "'")
    tok = re.sub(r"[^A-Za-z'\.\- ]", " ", tok)
    return re.sub(r"\s+", " ", tok).strip()


def canon(phrase):
    """Map a name phrase to a roster display name, or None if unresolvable (never guesses)."""
    if not phrase:
        return None
    t = ROLE_RE.sub(" ", phrase)
    t = _clean_token(t)
    if not t:
        return None
    words = [w.strip("'.-").lower() for w in t.split() if w.strip("'.-")]
    words = [w for w in words if len(w) >= 2]
    if not words:
        return None
    # 1. exact surname / variant / given-name (surname position first, then any word)
    ordered = [words[-1]] + words
    for w in ordered:
        if w in SURNAME_MAP:
            cand = SURNAME_MAP[w]
            if _reject_surname_fold(_pfx_word(words, w), cand):
                continue
            _STATS["resolutions"] += 1
            return cand
        if w in SURNAME_VARIANTS:
            cand = SURNAME_MAP[SURNAME_VARIANTS[w]]
            if _reject_surname_fold(_pfx_word(words, w), cand):
                continue
            _STATS["resolutions"] += 1
            _STATS["variant"] += 1
            return cand
        if w in FIRST_MAP:                       # first-name path — unambiguous, not gated
            _STATS["resolutions"] += 1
            return FIRST_MAP[w]
    # 2. fuzzy surname (OCR garble) — high cutoff, surname position preferred
    for w in ordered:
        if len(w) < 4:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.8)
        if m:
            cand = SURNAME_MAP[m[0]]
            if _reject_surname_fold(_pfx_word(words, w), cand):
                continue
            _STATS["resolutions"] += 1
            _STATS["fuzzy"] += 1
            return cand
        m = difflib.get_close_matches(w, list(SURNAME_VARIANTS), n=1, cutoff=0.85)
        if m:
            cand = SURNAME_MAP[SURNAME_VARIANTS[m[0]]]
            if _reject_surname_fold(_pfx_word(words, w), cand):
                continue
            _STATS["resolutions"] += 1
            _STATS["fuzzy"] += 1
            return cand
    return None


# ---------------------------------------------------------------------------
# Footer / page-break stripping — flattens tabular roll-call blocks that are
# interrupted by running page footers (critical: e.g. 2025-06-10 splits a roll
# call across a "Page 12" footer).
# ---------------------------------------------------------------------------
MONTHS = (r"January|February|March|April|May|June|July|August|September|October|"
          r"November|December")
FOOTER_PATTERNS = [
    re.compile(r"^\s*City of Taylorsville\s*$", re.I),
    re.compile(r"^\s*Taylorsville Planning Commission\s*$", re.I),
    re.compile(r"^\s*Planning Commission (Meeting )?Minutes\s*$", re.I),
    re.compile(r"^\s*Meeting Minutes\s*$", re.I),
    re.compile(r"^\s*Page\s*\d+(\s*of\s*\d+)?\s*$", re.I),
    re.compile(r"^\s*\d+\s*of\s*\d+\s*$"),
    re.compile(rf"^\s*(?:{MONTHS})\s+\d{{1,2}},?\s+\d{{4}}\s*$", re.I),
]


def strip_footers(text):
    out = []
    for ln in text.split("\n"):
        if any(p.match(ln) for p in FOOTER_PATTERNS):
            continue
        out.append(ln)
    return out


# ---------------------------------------------------------------------------
# Motion typing (fixed taxonomy, PC-weighted; land-use checked first)
# ---------------------------------------------------------------------------
def motion_type(text, cases=None):
    mt = text.upper()
    if re.search(r"\bADJOURN", mt):
        return "Procedural/Administrative"
    if re.search(r"ELECT\w*|NOMINAT\w*", mt) and re.search(r"CHAIR", mt):
        return "Appointment"
    if re.search(r"PUBLIC HEARING", mt) and re.search(r"\bOPEN|\bCLOSE", mt):
        return "Public Hearing Action"
    if re.search(r"\bMINUTES\b|CONSENT AGENDA|\bTABLE\b|CONTINUE|POSTPONE|CANCEL|"
                 r"RECESS|WITHDRAW|AMEND.*AGENDA|APPROVE.*AGENDA|SEPARATE AGENDA ITEM|"
                 r"90-?DAY EXTENSION|CLOSED SESSION", mt):
        return "Procedural/Administrative"
    if re.search(r"REZON|ZONE CHANGE|ZONING (MAP|TEXT)|RECLASSIF|STREET VACATION|VACAT|"
                 r"ANNEX|CONDITIONAL USE|\bCUP\b|\bPLAT\b|SUBDIVI|GENERAL PLAN|"
                 r"LAND (USE|DEVELOPMENT) CODE|\bLDC\b|OVERLAY|DESIGN REVIEW|SITE PLAN|"
                 r"PLANNED (UNIT )?DEVELOPMENT|\bPUD\b|LOT LINE|PRELIMINARY|FINAL PLAT|"
                 r"VARIANCE|PERMITTED USE|TEXT AMENDMENT|\bADU\b|ACCESSORY DWELLING|"
                 r"MAP AMENDMENT|RECOMMENDATION TO THE CITY COUNCIL|EXEMPTION|"
                 r"CURB AND GUTTER|SETBACK|§ ?13\.|SECTION 13\.", mt):
        return "Land-Use/Zoning"
    # a captured land-use case number (<n>Z/G/S/C/P<yy>, CUP-/SUB-/PU-/SI-...) => land-use
    if cases:
        return "Land-Use/Zoning"
    if "ORDINANCE" in mt:
        return "Ordinance"
    if "RESOLUTION" in mt:
        return "Resolution"
    return "Other"


# ---------------------------------------------------------------------------
# Anchors
# ---------------------------------------------------------------------------
# MOTION header — uppercase MOTION + optional "#N", optionally prefixed by an item
# number ("3.6      MOTION:", "4.9 MOTION #1:"); reliably a header (prose uses lowercase).
MOTION_HDR = re.compile(r"\bMOTION\s*(?:#\s*\d+)?\s*[:;]")
MOTION_STRIP = re.compile(r".*?\bMOTION\s*(?:#\s*\d+)?\s*[:;]\s*", re.S)
NAME_ROLE = r"(?:Commissioner|Vice[-\s]*Chair|Chair|Alternate)"
VOTE_MARK = re.compile(r"(?:ROLL\s*CALL\s*VOTE|VOTE)\s*:", re.I)

VLABEL = (r"AYE|Aye|aye|YES|Yes|yes|NAY|Nay|nay|NO|No|no|"
          r"ABSTAIN(?:ED)?|Abstain(?:ed)?|abstain(?:ed)?|"
          r"ABSENT|Absent|absent|RECUSED?|Recused?|recused?")
# inline "Commissioner X - AYE" token — separator OPTIONAL (some roll calls drop the
# dash: "Commissioner Russell  AYE"); region is flattened + gated by a VOTE: marker.
NAMED_TOKEN = re.compile(
    NAME_ROLE + r"\s+([A-Za-zéíñ'\.]+)\s*[–—\-:]?\s*(" + VLABEL + r")\b")
# tabular one-member-per-line "Commissioner X[:]  Aye [trailing OCR punct :;.,]"
TAB_LINE = re.compile(
    r"^\s*" + NAME_ROLE + r"\s+([A-Za-zéíñ'\.]+)\s*:?\s+(" + VLABEL + r")\s*[.:;,]*\s*$")

TALLY_NUM = re.compile(r"[Mm]otion\s+[Pp]ass\w*\s+(\d+)\s*(?:[–—\-]|\bto\b)\s*(\d+)")
TALLY_FAVOR = re.compile(r"(\d+)\s+in\s+favor,?\s+(?:and\s+)?(\d+)\s+in\s+opposition", re.I)
UNANIM = re.compile(r"pass\w*\s+.{0,20}?unanimous|unanimous|voted\s+in\s+favor", re.I)
FAILED = re.compile(r"motion\s+(?:was\s+)?(?:fail|den)|did not (?:pass|carry)|"
                    r"does not (?:pass|carry)|motion\s+fails", re.I)

VOTE_MAP = {
    "aye": "aye", "yes": "aye",
    "nay": "nay", "no": "nay",
    "abstain": "abstain", "abstained": "abstain",
    "absent": "absent",
    "recuse": "recuse", "recused": "recuse",
}


def vlabel_bucket(lbl):
    l = lbl.lower()
    if l.startswith("abstain"):
        return "abstain"
    if l.startswith("recus"):
        return "recuse"
    if l.startswith("absent"):
        return "absent"
    return VOTE_MAP.get(l, "aye")


CASE_SHORT = re.compile(r"\b(\d{1,3}[A-Z]{1,3}\d{2,3})\b")
CASE_LONG = re.compile(r"\b((?:CUP|SUB|PU|SI|RA|SP|TA|GP|LU)[-\s]?[A-Z]{0,3}[-\s]?\d{3,6}"
                       r"(?:[-\s]?\d{2,4})?)\b")


def find_cases(text):
    out = []
    for m in CASE_SHORT.finditer(text):
        c = m.group(1)
        if c not in out:
            out.append(c)
    for m in CASE_LONG.finditer(text):
        c = re.sub(r"\s", "-", m.group(1))
        if c not in out:
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# Result / direction classification
# ---------------------------------------------------------------------------
def classify(motion, aye_n, nay_n, passed, names_recorded, printed, unanimous):
    m = motion.lower()
    procedural = bool(re.search(
        r"\bminutes\b|consent agenda|continuance|continue|\btable\b|postpone|adjourn|"
        r"recess|withdraw|amend the agenda|approve the agenda|90-?day extension", m))
    is_elect = bool(re.search(r"elect|nominat", m) and "chair" in m)
    # a RECOMMENDATION to Council (not an incidental "recommend that staff …" clause):
    is_rec = bool(re.search(
        r"(?:forward|send|make)\s+(?:a|any)\b[^.]{0,55}recommendation|"
        r"recommendation\b[^.]{0,35}\bto the\b[^.]{0,25}council|"
        r"\bpositive recommendation\b|\bnegative recommendation\b|"
        r"\bfavorable recommendation\b|recommendation of (?:approval|denial)", m))
    pos_rec = "positive recommendation" in m
    neg_rec = "negative recommendation" in m
    proposes_denial = bool(re.search(r"\bden(?:y|ial|ied)\b|revok", m))
    proposes_approval = bool(re.search(r"approv|grant", m)) and not proposes_denial

    if names_recorded:
        tally = f"{aye_n}-{nay_n}"
    elif printed:
        tally = f"{printed[0]}-{printed[1]}"
    elif unanimous:
        tally = "unanimous"
    else:
        tally = "n/a"

    def with_tally(base):
        return f"{base} (unanimous)" if tally == "unanimous" else f"{base} {tally}"

    if is_elect:
        return (f"{tally} Pass" if passed else f"{tally} Fail"), "procedural"
    if procedural and not is_rec:
        if tally in ("unanimous", "n/a"):
            return ("Pass (unanimous)" if passed else "Fail"), "procedural"
        return (f"{tally} Pass" if passed else f"{tally} Fail"), "procedural"

    if is_rec:
        # report the PROPOSED direction (from the motion verb) + whether it carried —
        # never relabel a FAILED motion as the opposite direction (avoids the tie/flip trap).
        if pos_rec:
            proposed = "Positive"
        elif neg_rec or proposes_denial:
            proposed = "Negative"
        elif proposes_approval:
            proposed = "Positive"
        else:
            proposed = "Positive"
        if passed:
            return with_tally(f"{proposed} recommendation"), "recommendation"
        base = f"{proposed} recommendation — motion failed"
        return (base if tally in ("unanimous", "n/a") else f"{base} {tally}"), "recommendation"

    # final action
    if proposes_denial:
        approved = not passed
    elif proposes_approval:
        approved = passed
    else:
        approved = passed
    disp = "Approved" if approved else "Denied"
    if tally in ("unanimous", "n/a"):
        return f"{disp} (Final Action, unanimous)", "final_action"
    return f"{tally} {disp} (Final Action)", "final_action"


# ---------------------------------------------------------------------------
# Parse one motion block  (block_lines[0] is the MOTION: header line)
# ---------------------------------------------------------------------------
def parse_block(block_lines, all_lines, motion_abs_idx):
    head = " ".join(l.strip() for l in block_lines[:4])
    head_after = re.split(r"\bMOTION\s*(?:#\s*\d+)?\s*[:;]", head, maxsplit=1)
    head_after = head_after[1] if len(head_after) > 1 else head

    # ---- mover: first roster name after "MOTION:"
    mover = None
    mm = re.search(NAME_ROLE + r"\.?\s+([A-Za-zñ'\.\-]+)", head_after)
    if mm:
        mover = canon(mm.group(0))

    # ---- motion text: MOTION: .. up to SECOND: / VOTE: / roll call / outcome
    block_text = "\n".join(block_lines)
    cut = re.split(r"\bSECOND\s*[:;]|\bROLL\s*CALL\s*VOTE|\bVOTE\s*:|"
                   r"\bThe motion was seconded|\bseconded by|\bseconded the motion|"
                   r"[Mm]otion\s+[Pp]ass\w*\s+\d",
                   re.sub(r"\s+", " ", block_text), maxsplit=1)
    motion_text = MOTION_STRIP.sub("", cut[0], count=1).strip(" .;,-")
    if not motion_text:
        motion_text = re.sub(r"\s+", " ", head_after).strip(" .;,-")
    motion_text = motion_text[:600]

    # ---- seconder
    seconder = None
    sm = re.search(r"SECOND\s*[:;]\s*(" + NAME_ROLE + r"\s+[A-Za-zñ'\.\-]+)",
                   block_text, re.I)
    if not sm:
        sm = re.search(r"seconded by\s+(?:the motion\s+by\s+)?(" + NAME_ROLE +
                       r"\s+[A-Za-zñ'\.\-]+)", block_text, re.I)
    if not sm:
        sm = re.search(r"(" + NAME_ROLE + r"\s+[A-Za-zñ'\.\-]+)\s+seconded",
                       block_text, re.I)
    if sm:
        seconder = canon(sm.group(1))

    buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    names_recorded = False

    def add(bucket, name):
        if name and name not in buckets[bucket]:
            # a member can only sit in one bucket
            for b in buckets.values():
                if name in b:
                    return
            buckets[bucket].append(name)

    # ---- (1) NAMED INLINE — only when a VOTE:/ROLL CALL VOTE: marker exists
    vmark = None
    for i, l in enumerate(block_lines):
        if VOTE_MARK.search(l):
            vmark = i
            break
    vote_format = "narrative-tally"
    if vmark is not None:
        # flatten the vote region (labels wrap across pdftotext line breaks)
        region = []
        for l in block_lines[vmark:vmark + 12]:
            if MOTION_HDR.search(l) and not VOTE_MARK.search(l):
                break
            region.append(l.strip())
            if TALLY_NUM.search(l) or re.search(r"unanimous", l, re.I):
                break
        region_str = re.sub(r"\s+", " ", " ".join(region))
        toks = NAMED_TOKEN.findall(region_str)
        for raw, lbl in toks:
            nm = canon(raw)
            if nm:
                add(vlabel_bucket(lbl), nm)
        if sum(len(v) for v in buckets.values()) >= 2:
            names_recorded = True
            vote_format = "named-inline"

    # ---- (2) TABULAR — one member per line
    if not names_recorded:
        tab = []
        for l in block_lines:
            tmatch = TAB_LINE.match(l)
            if tmatch:
                nm = canon(tmatch.group(1))
                if nm:
                    tab.append((nm, vlabel_bucket(tmatch.group(2))))
        if len(tab) >= 2:
            for nm, bk in tab:
                add(bk, nm)
            names_recorded = True
            vote_format = "tabular"

    # ---- outcome / printed tally (search the whole block)
    flat = re.sub(r"\s+", " ", block_text)
    printed = None
    tm = TALLY_NUM.search(flat) or TALLY_FAVOR.search(flat)
    if tm:
        printed = (int(tm.group(1)), int(tm.group(2)))
    unanimous = bool(UNANIM.search(flat))
    failed = bool(FAILED.search(flat))
    tally_text = f"{printed[0]}-{printed[1]}" if printed else ""

    # ---- (3) PROSE-named abstain / recuse (majority stays unnamed)
    if not names_recorded:
        for km in re.finditer(r"(recus\w+|abstain\w*|abstention)", flat, re.I):
            lo = max(0, km.start() - 70)
            win = flat[lo:km.end() + 30]
            bucket = "recuse" if km.group(1).lower().startswith("recus") else "abstain"
            for nmatch in re.finditer(NAME_ROLE + r"s?\s+([A-Za-zñ'\.\-]+)"
                                      r"(?:\s+and\s+(?:Commissioner\s+)?([A-Za-zñ'\.\-]+))?",
                                      win):
                for g in (nmatch.group(1), nmatch.group(2)):
                    nm = canon(g) if g else None
                    if nm:
                        add(bucket, nm)

    aye_n, nay_n = len(buckets["aye"]), len(buckets["nay"])
    outcome_detected = bool(names_recorded or printed or unanimous or failed or
                            re.search(r"\bpass\w*|carr\w*|adopt|adjourn|declared the "
                                      r"meeting", flat, re.I))
    if names_recorded:
        passed = aye_n > nay_n
    elif failed:
        passed = False
    elif printed:
        passed = printed[0] >= printed[1]
    else:
        # motions are recorded because they carried; absent an explicit fail/minority
        # tally, assume PASS (keeps recommendation DIRECTION aligned to the motion verb).
        passed = True

    # case numbers: from motion text, else nearest preceding "File #<code>"
    cases = find_cases(motion_text)
    if not cases:
        for j in range(motion_abs_idx - 1, max(-1, motion_abs_idx - 90), -1):
            fm = re.search(r"File\s*#?\s*([A-Za-z0-9/\-]+)", all_lines[j])
            if fm:
                c = find_cases(fm.group(0))
                if c:
                    cases = c
                    break

    result, kind = classify(motion_text, aye_n, nay_n, passed, names_recorded,
                            printed, unanimous)
    if not outcome_detected:
        # a MOTION was made but NO vote is recorded (superseded/competing motion, or
        # tabled for lack of quorum) — never fabricate a pass.
        result = "No recorded vote"
    # explicit no-vote FATES (T3.1(l) 2026-07-12): when there is no roll, no printed
    # tally, and no unanimity, the block's stated fate wins — died-for-lack-of-second /
    # withdrawn / tabled-for-no-quorum motions must not default to Pass. Superseded-but-
    # carried motions (2021-07-27 4.8, 2023-05-09 4.9 — the vote lives on the companion
    # "motion stands"/amended row) keep the bare "No recorded vote" -> Pass, per audit.
    if not names_recorded and not printed and not unanimous:
        if re.search(r"motion\s+died\s+for\s+lack\s+of\s+a\s+second", flat, re.I):
            result = "Died (no second)"
        elif re.search(r"motion[^.]{0,80}?\bwas\s+withdrawn|withdrew\s+the\s+motion",
                       flat, re.I):
            result = "Withdrawn (no vote)"
        elif re.search(r"not\s+a\s+quorum", flat, re.I) and \
                re.search(r"\btabled\b", flat, re.I):
            result = "Tabled (no quorum)"
    mtype = motion_type(motion_text, cases)
    if mtype == "Other" and kind in ("recommendation", "final_action"):
        mtype = "Land-Use/Zoning"        # a PC rec/final action is inherently land-use
    return {
        "body": BODY,
        "motion": motion_text,
        "motion_type": mtype,
        "result": result,
        "kind": kind,
        "mover": mover,
        "seconder": seconder,
        "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
        "absent": buckets["absent"], "recuse": buckets["recuse"],
        "names_recorded": names_recorded,
        "vote_format": vote_format,
        "outcome_detected": outcome_detected,
        "tally_text": tally_text,
        "case_no": cases,
    }


AGENDA_HDR = re.compile(
    r"^\s*\d+\.\s+\S|Consideration|Recommendation to the|approval for|"
    r"Public Hearing and", re.I)


def parse_orphan_tabular(lines, run, covered):
    """Build a motion from a header-less tabular roll call (run = matching line idxs)."""
    buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    for r in run:
        tm = TAB_LINE.match(lines[r])
        nm = canon(tm.group(1))
        if nm and all(nm not in b for b in buckets.values()):
            buckets[vlabel_bucket(tm.group(2))].append(nm)
    printed = None
    for r in range(run[-1] + 1, min(run[-1] + 4, len(lines))):
        tmt = TALLY_NUM.search(lines[r]) or TALLY_FAVOR.search(lines[r])
        if tmt:
            printed = (int(tmt.group(1)), int(tmt.group(2)))
            break
    # motion text: nearest preceding agenda-item header, else a case-number line
    mtext = ""
    for b in range(run[0] - 1, max(-1, run[0] - 60), -1):
        if b in covered:
            break
        if AGENDA_HDR.search(lines[b]):
            mtext = re.sub(r"\s+", " ", lines[b]).strip()
            break
    cases = find_cases(mtext) if mtext else []
    aye_n, nay_n = len(buckets["aye"]), len(buckets["nay"])
    names_recorded = (aye_n + nay_n + len(buckets["abstain"]) + len(buckets["recuse"])) >= 2
    if not names_recorded and not printed:
        return None
    passed = (printed[0] >= printed[1]) if printed else (aye_n >= nay_n)
    result, kind = classify(mtext, aye_n, nay_n, passed, names_recorded, printed, False)
    return {
        "body": BODY, "motion": mtext or "(agenda item — header not printed; see minutes)",
        "motion_type": motion_type(mtext, cases), "result": result, "kind": kind,
        "mover": None, "seconder": None,
        "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
        "absent": buckets["absent"], "recuse": buckets["recuse"],
        "names_recorded": names_recorded, "vote_format": "tabular",
        "outcome_detected": True,
        "tally_text": f"{printed[0]}-{printed[1]}" if printed else "", "case_no": cases,
    }


ADJOURN_PROSE = re.compile(
    r"ADJOURNMENT\s*[:;].*?By motion of\s+(" + NAME_ROLE + r"\s+[A-Za-zñ'\.\-]+"
    r"(?:\s+[A-Za-zñ'\.\-]+)?)", re.I)


def find_motions(text):
    lines = strip_footers(text)
    n = len(lines)
    hdr_idx = [i for i, l in enumerate(lines) if MOTION_HDR.search(l)]

    motions = []
    for k, idx in enumerate(hdr_idx):
        end = hdr_idx[k + 1] if k + 1 < len(hdr_idx) else n
        block = lines[idx:end]
        mo = parse_block(block, lines, idx)
        motions.append(mo)

    # secondary: ORPHAN tabular roll calls with NO "MOTION:" header (a few 2024+ meetings
    # print the vote block + "Motion passed N-M" but drop the header). Capture what's there;
    # never invent missing names — an incomplete OCR roll call is flagged by the validator.
    covered = set()
    for k, idx in enumerate(hdr_idx):
        end = hdr_idx[k + 1] if k + 1 < len(hdr_idx) else n
        covered.update(range(idx, end))
    i = 0
    while i < n:
        if i in covered or not TAB_LINE.match(lines[i]):
            i += 1
            continue
        run, j = [], i
        while j < n:
            if TAB_LINE.match(lines[j]):
                run.append(j)
                j += 1
            elif not lines[j].strip():
                j += 1
            else:
                break
        if len(run) >= 2 and not any(r in covered for r in run):
            mo = parse_orphan_tabular(lines, run, covered)
            if mo:
                motions.append(mo)
            covered.update(range(run[0], run[-1] + 1))
        i = max(j, i + 1)

    # secondary: 2020-2023 "ADJOURNMENT: By motion of Commissioner X" (no MOTION: header)
    joined = "\n".join(lines)
    if not any(re.search(r"adjourn", m["motion"], re.I) for m in motions):
        am = ADJOURN_PROSE.search(joined)
        if am:
            mover = canon(am.group(1))
            sm = re.search(r"second(?:ed)? by\s+(" + NAME_ROLE +
                           r"\s+[A-Za-zñ'\.\-]+)", am.group(0), re.I)
            motions.append({
                "body": BODY, "motion": "By motion the meeting was adjourned.",
                "motion_type": "Procedural/Administrative",
                "result": "Pass (unanimous)", "kind": "procedural",
                "mover": mover, "seconder": canon(sm.group(1)) if sm else None,
                "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": [],
                "names_recorded": False, "vote_format": "narrative-tally",
                "outcome_detected": True, "tally_text": "", "case_no": [],
            })

    for i, mo in enumerate(motions, 1):
        mo["motion_no"] = i
    return motions


# ---------------------------------------------------------------------------
# Attendance (for roster.csv)
# ---------------------------------------------------------------------------
ATTEND_RE = re.compile(r"^\s*(Attendance|ATTENDANCE)\s*[:]?", )
ATTEND_STOP = re.compile(r"BRIEFING|GENERAL MEETING|REGULAR SESSION|PRE-?MEETING|"
                         r"CITIZEN|GUESTS|CONSENT AGENDA|Roll Call", re.I)


def parse_present(text):
    lines = strip_footers(text)
    present = []
    for i, ln in enumerate(lines):
        if ATTEND_RE.match(ln):
            for j in range(i + 1, min(i + 22, len(lines))):
                if ATTEND_STOP.search(lines[j]):
                    break
                # a commissioner name usually leads the line (staff sit in the 2nd column)
                lead = lines[j].strip()
                nm = canon(lead[:40])
                if nm and nm not in present:
                    present.append(nm)
            break
    return present


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def load_index():
    with open(INDEX, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in list(r):
            if r[k] is not None:
                r[k] = r[k].replace("\r", "").strip()
    return rows


def json_path_for(rel):
    jrel = re.sub(r"^minutes/", "", rel)
    return (VOTES_DIR / jrel).with_suffix(".json")


def main(force=False):
    rows = load_index()
    processed = 0
    for r in rows:
        path = ROOT / r["path"]
        if not path.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        jpath = json_path_for(r["path"])
        if jpath.exists() and not force:
            processed += 1
            continue
        text = path.read_text(errors="replace").replace("\r", "")
        motions = find_motions(text)
        present = parse_present(text)
        jpath.parent.mkdir(parents=True, exist_ok=True)
        obj = {
            "date": r["date"], "year": int(r["year"]), "title": TITLE, "body": BODY,
            "slug": r["slug"], "format": r.get("format", ""),
            "source": r["path"], "present": present, "votes": motions,
        }
        jpath.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
        processed += 1
    n_rows = rebuild_csv(rows)
    n_ros = build_roster(rows)
    (VOTES_DIR / "_extract_stats.json").write_text(json.dumps(_STATS, indent=1))
    print(f"processed {processed} meetings -> {OUT_CSV} ({n_rows} rows); roster {n_ros}")
    print(f"name resolutions={_STATS['resolutions']} fuzzy={_STATS['fuzzy']} "
          f"variant={_STATS['variant']}")
    return processed


def build_roster(rows):
    seen = {}
    for r in rows:
        jpath = json_path_for(r["path"])
        if not jpath.exists():
            continue
        obj = json.loads(jpath.read_text())
        date = obj["date"]
        people = set(obj.get("present", []))
        for mo in obj["votes"]:
            for k in ("mover", "seconder"):
                if mo.get(k):
                    people.add(mo[k])
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                people.update(mo.get(k, []))
        for p in people:
            seen.setdefault(p, set()).add(date)
    out = []
    for name, dates in seen.items():
        ds = sorted(dates)
        out.append((name, ds[0], ds[-1], len(ds)))
    out.sort(key=lambda x: (x[1], x[0]))
    with open(ROSTER_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        w.writerows(out)
    return len(out)


def rebuild_csv(rows):
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    out = []
    for r in rows:
        jpath = json_path_for(r["path"])
        if not jpath.exists():
            continue
        obj = json.loads(jpath.read_text())
        for mo in obj["votes"]:
            base = [obj["date"], obj["year"], TITLE, mo["body"], mo["motion_no"],
                    mo["motion"], mo["motion_type"], mo["result"],
                    mo.get("mover") or "", mo.get("seconder") or ""]
            members = ([(m, "Aye") for m in mo["aye"]] +
                       [(m, "Nay") for m in mo["nay"]] +
                       [(m, "Abstain") for m in mo["abstain"]] +
                       [(m, "Absent") for m in mo.get("absent", [])] +
                       [(m, "Recuse") for m in mo.get("recuse", [])])
            if members:
                for mem, v in members:
                    out.append(base + [mem, v, obj["source"]])
            else:
                out.append(base + ["", "", obj["source"]])
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        w.writerows(out)
    return len(out)


if __name__ == "__main__":
    main(force="--force" in sys.argv)
