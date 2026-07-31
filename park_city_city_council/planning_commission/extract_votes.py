#!/usr/bin/env python3
"""
extract_votes.py — Park City (Utah) PLANNING COMMISSION vote extraction.

Reads the 160 minutes markdown files under planning_commission/minutes/<year>/<week>/
(indexed in planning_commission/minutes_index.csv), parses each recorded motion + vote,
emits one JSON per meeting to planning_commission/votes/<year>/<week>/<date>_<slug>.json,
then rebuilds planning_commission/all_votes.csv (long format, one row per member-vote).

The Planning Commission is an APPOINTED body — there is NO mayor, NO elections, and the
Chair votes like any other member. Park City CivicClerk minutes use a strict
"MOTION:" / "VOTE:" convention:

  MOTION: Commissioner Kenworthy moved to forward a NEGATIVE recommendation to the City
          Council for consideration ... Commissioner Suesser seconded the motion.
  VOTE:   Commissioner Kenworthy-Aye; Commissioner Hall-Nay; Commissioner Johnson-Aye;
          Commissioner Van Dine-Nay; Commissioner Suesser-Aye. The motion passed 3-to-2.

Three VOTE forms occur:
  (a) Per-name roll call: "Commissioner X-Aye; Commissioner Y-Nay; ... The motion
      passed N-to-M."  (also "Yes/No" instead of "Aye/Nay"; role words "Chair X-Aye").
  (b) Tally-only "The motion passed with the unanimous consent of the Commission." or
      "The motion passed unanimously." — NO names → names_recorded:false (never guessed).
  (c) "The motion failed for lack of a second." — no roll call, recorded as a failed motion.

Many PC motions are a RECOMMENDATION TO COUNCIL (forward a POSITIVE / NEGATIVE
recommendation on a plat / MPD / rezone / annexation) rather than a PC-final action
(CUPs, design review, appeals are usually PC-final). We capture the recommendation
direction + tally in `result` ("Positive recommendation 4-1", "Denied 2-3", ...) and tag
each motion `action_type` = Recommendation / Final Action / Procedural.

CRITICAL source-quality fixes baked in:
  1. The `-layout` PDF->text conversion stamps a vertical "APPROVED/DRAFT" watermark and
     page numbers into the LEFT/CENTER margin as stray short tokens on their own lines
     ("D", "O", "VE", "ed", "ro", "Ap", "03", ...). These are stripped before parsing so
     they cannot split a "Commissioner X-\n  ro \n  Vote" sequence or corrupt motion text.
  2. Per-name vote lists wrap across lines (and around injected page headers); we capture
     the whole VOTE window with [\s\S] and regex every "Commissioner <Name>-<Vote>" pair.
  3. OCR/spelling variants folded: VanDine->Van Dine, Kenworth->Kenworthy (and the roster
     keys Sara->Sarah Hall, Rich->Rick Shand). Names not on the roster (staff, applicants,
     public) are dropped, never invented.

Run:  python3 planning_commission/extract_votes.py          (resumable: skips existing JSON)
      python3 planning_commission/extract_votes.py --force   (re-extract all)
"""
import argparse
import csv
import json
import os
import re

PC = os.path.dirname(os.path.abspath(__file__))
MINUTES_INDEX = os.path.join(PC, "minutes_index.csv")
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES_CSV = os.path.join(PC, "all_votes.csv")
BODY = "PlanningCommission"

# ---------------------------------------------------------------------------
# Canonical roster. Surname-key -> "First Last". 14 appointed commissioners,
# 2020-2026 (date ranges in the validator). No mayor, no elections; the Chair is
# a seated commissioner and votes. Built from the minutes' attendee headers and
# every per-name VOTE list. Surname keys are lowercased & space-stripped, so
# "Van Dine" and the OCR run-together "VanDine" both key to "vandine".
# ---------------------------------------------------------------------------
ROSTER = {
    "phillips":  "John Phillips",       # Chair 2020-01..2022-07
    "sletten":   "Mark Sletten",        # 2020-01..2020-10
    "thimm":     "Doug Thimm",          # 2020-01..2022-05
    "kenworthy": "John Kenworthy",      # 2020-01..2023-06
    "hall":      "Sarah Hall",          # later Chair; OCR "Sara Hall"; 2020-01..2025-04
    "suesser":   "Laura Suesser",       # later Chair; 2020-01..2025-06
    "vandine":   "Christin Van Dine",   # later Vice Chair; 2020-01..2026-01
    "johnson":   "Bill Johnson",        # 2021-05..2025-11 (present 2025-11-12 per minutes)
    "frontero":  "John Frontero",       # 2022-08..2026-05
    "sigg":      "Henry Sigg",          # 2022-10..2026-05
    "shand":     "Rick Shand",          # OCR "Rich Shand"; 2023-07..2026-05
    "tilson":    "Grant Tilson",        # 2025-05..2026-05
    "beal":      "Seth Beal",           # 2025-07..2026-05
    "strachan":  "Adam Strachan",       # 2026-04..2026-05
}
# OCR / spelling variants folded onto a roster surname key.
SURNAME_ALIASES = {
    "kenworth": "kenworthy",   # OCR truncation
    "vandine": "vandine",
    "sara": "hall",            # first-name leak guard (roster keys on surname anyway)
    "rich": "shand",
}


def norm_surname(token):
    t = re.sub(r"[^a-z]", "", token.lower())
    return SURNAME_ALIASES.get(t, t)


def canon(token):
    return ROSTER.get(norm_surname(token))


# ---------------------------------------------------------------------------
# Watermark / page-furniture filtering. The -layout conversion injects:
#   * a vertical "APPROVED"/"DRAFT" watermark as lone short tokens, indented:
#       "                       ed" / "       O" / "                 VE"
#   * page numbers as lone digits ("1", "03"), and repeated page headers:
#       "Park City Municipal Corporation" / "Planning Commission Meeting" / "<Month> N, YYYY"
# We drop these lines wholesale before parsing so they can't split a roll-call
# "Commissioner X-\n <watermark> \n Vote" sequence or pollute motion text.
# ---------------------------------------------------------------------------
NOISE_TOKEN_RE = re.compile(r"^[A-Za-z]{1,4}$")          # ed, ro, VE, Ap, PR, City, th, ...
NOISE_NUM_RE = re.compile(r"^\d{1,3}$")                  # 1, 03, page numbers
# The -layout conversion sometimes stamps the same furniture tokens with a TRAILING
# PERIOD as a LONE line ("1.", "3.", "04.", the watermark letter "D."). These sit
# mid-sentence between "The motion" and its outcome verb, silently splitting a folded
# outcome sentence — the un-fixed audit root cause (2026-07-19 fix #1). clean_lines()
# does NOT drop them GLOBALLY (that would strip the same shapes from stored motion text
# — real Findings/Conditions carry a bare "3." on their own line mid-list, so removing
# them corpus-wide shifts the 600-char motion snapshots). Instead folded_vote_window()
# drops these lone-line shapes LOCALLY, on the outcome window only, so the outcome
# sentence reunites while every stored motion string stays byte-identical to pre-fix.
NOISE_DOTTED_NUM_RE = re.compile(r"^\d{1,3}\.$")         # 1.  3.  04.  (page numbers)
NOISE_DOTTED_LETTER_RE = re.compile(r"^[A-Za-z]\.$")     # D.  O.  (watermark letters)
HEADER_LINE_RE = re.compile(
    r"^\s*("
    r"Park City Municipal Corporation"
    r"|Planning Commission Meeting"
    r"|Park City Planning Commission"
    r"|(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s+\d{4}"
    r")\s*$",
    re.IGNORECASE)


def clean_lines(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            out.append("")
            continue
        if NOISE_TOKEN_RE.match(s) or NOISE_NUM_RE.match(s):
            continue
        if HEADER_LINE_RE.match(ln):
            continue
        out.append(ln)
    return out


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories, shared across cities). PC business
# is land-use heavy, so most land here.
# ---------------------------------------------------------------------------
def classify(text):
    t = " ".join(text.split()).lower()
    landuse_kw = ["zone", "zoning", "rezone", "general plan", "overlay", "subdivision",
                  "plat", "annex", "right-of-way", "right of way", "vacat", "land use",
                  "land management code", "lmc", "setback", "conditional use", "cup",
                  "pud", "master plan", "mpd", "development agreement", "design review",
                  "specially planned area", "spa", "easement", "lot line", "condominium",
                  "record of survey", "steep slope", "appeal", "variance", "site plan"]
    if any(k in t for k in landuse_kw):
        return "Land-Use/Zoning"
    if "budget amendment" in t or re.search(r"budget.{0,30}amend", t):
        return "Budget Amendment"
    if "interlocal" in t or "inter-local" in t:
        return "Interlocal"
    if "grant" in t and any(k in t for k in ("apply", "accept", "award", "funding",
                                             "application", "cdbg")):
        return "Grant-Funding"
    if "appoint" in t or "reappoint" in t or "nominat" in t or "elect" in t and "chair" in t:
        return "Appointment"
    if any(k in t for k in ["contract", "agreement", "purchase", "professional services",
                            "lease", "task order"]) and "development agreement" not in t:
        return "Contract/Purchase"
    if "ordinance" in t:
        return "Ordinance"
    if "resolution" in t:
        return "Resolution"
    if any(k in t for k in ["open the public hearing", "close the public hearing",
                            "continue the public hearing"]):
        return "Public Hearing Action"
    proc_kw = ["minutes", "agenda", "continue", "table", "consent", "adjourn", "recess",
               "ratify", "set the date", "schedule", "work session", "election of",
               "chair", "vice chair", "calendar", "reconsider"]
    if any(k in t for k in proc_kw):
        return "Procedural/Administrative"
    return "Other"


def action_type(motion_text):
    """Recommendation to Council vs PC-final action vs procedural housekeeping."""
    t = motion_text.lower()
    if "recommendation" in t and ("council" in t or "forward" in t):
        return "Recommendation"
    if re.search(r"\bforward (a |an )?(positive|negative|favorable)", t):
        return "Recommendation"
    proc = ["minutes", "adjourn", "agenda", "continue", "work session", "elect",
            "chair pro tem", "recess", "schedule"]
    if any(k in t for k in proc) and "recommend" not in t:
        return "Procedural"
    return "Final Action"


# ---------------------------------------------------------------------------
# Name-list / mover-seconder parsing.
# ---------------------------------------------------------------------------
ROLE = r"(?:Commissioners?|Vice\s+Chair|Acting\s+Chair|Chair\s+Pro\s+Tem|Chair)"
NAME = r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)"        # "Suesser", "Van Dine", "VanDine"
# mover/seconder may be given as a FULL name ("Christin Van Dine moved", 3 tokens) or
# just a surname; capture up to 3 capitalized tokens and resolve the roster surname.
NAMES = r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})"
VOTE_PAIR_RE = re.compile(
    rf"{ROLE}\s+{NAME}\s*-\s*(Aye|Nay|Yes|No|Abstain(?:ed)?|Absent|Recused?)\b",
    re.IGNORECASE)
MOVED_RE = re.compile(
    rf"{ROLE}\s+{NAMES}\s+(?:moved|made\s+a\s+motion|motioned|nominated)",
    re.IGNORECASE)
SECOND_RE = re.compile(rf"{ROLE}\s+{NAMES}\s+seconded", re.IGNORECASE)
SECOND_BY_RE = re.compile(rf"seconded\s+by\s+{ROLE}?\s*{NAMES}", re.IGNORECASE)


def resolve_person(span):
    """Resolve a roster member from a 1-3 token name span ('Christin Van Dine',
    'Van Dine', 'Suesser'). The surname is the trailing token(s); try the last two
    joined first ('Van Dine'), then each single token."""
    toks = span.split()
    if len(toks) >= 2:
        c = canon(toks[-2] + toks[-1])          # 'Van'+'Dine' -> vandine
        if c:
            return c
    for tok in reversed(toks):
        c = canon(tok)
        if c:
            return c
    return None

VOTE_WORD_BUCKET = {
    "aye": "aye", "yes": "aye",
    "nay": "nay", "no": "nay",
    "abstain": "abstain", "abstained": "abstain",
    "absent": "absent",
    "recuse": "recuse", "recused": "recuse",
}


def parse_rollcall(window):
    """Return {bucket: [names]} from a per-name VOTE window. Only the segment up to
    the terminal 'The motion ...' sentence is the roll call; anything after is
    narrative."""
    buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    seen = set()
    for m in VOTE_PAIR_RE.finditer(window):
        full = canon(m.group(1))
        if not full:
            continue
        bucket = VOTE_WORD_BUCKET[m.group(2).lower()]
        if full in seen:
            continue
        seen.add(full)
        buckets[bucket].append(full)
    return buckets


# ---------------------------------------------------------------------------
# Outcome / result construction.
# ---------------------------------------------------------------------------
TALLY_RE = re.compile(r"(\d+)\s*-?\s*to\s*-?\s*(\d+)", re.IGNORECASE)   # 3-to-2
TALLY2_RE = re.compile(r"\b(\d+)\s*-\s*(\d+)\b")                        # 4-0

# ---------------------------------------------------------------------------
# Folded-outcome grammar (Park City CivicClerk, sporadic from 2024-06, then
# UNIVERSAL from 2024-10-09 onward). The separate "VOTE:" marker was dropped and
# the outcome sentence is folded INTO the MOTION: block (optionally with a
# "Vote on Motion:" per-name roll call and/or a trailing named-dissent clause):
#
#   MOTION: Commissioner Van Dine moved to APPROVE the Plat ... The motion was
#           seconded by Commissioner Sigg. The motion passed with the unanimous
#           consent of the Commission.
#
# A handful of pre-2024 meetings also misprint the OUTCOME under a "MOTION:"
# label (an outcome sentence, no motion verb — e.g. 2020-03-11 "MOTION: The
# motion passed 4-1. Commissioner Suesser voted against the motion.").
#
# FOLDED_OUTCOME_RE finds the outcome sentence that carries a genuine RESULT verb
# so it skips the "The motion was seconded by X." sentence that precedes it.
# ---------------------------------------------------------------------------
FOLDED_OUTCOME_RE = re.compile(
    r"[Tt]he\s+motion\s+(?:was\s+)?[^.]*?"
    r"\b(?:passed|failed|carried|denied|approved|did\s+not)\b[^.]*\.",
    re.IGNORECASE)
MOTION_VERB_RE = re.compile(
    r"\bmoved\b|\bmade\s+a\s+motion\b|\bmotioned\b|\bnominated\b", re.IGNORECASE)
VOTE_ON_MOTION_RE = re.compile(r"Vote on Motion\s*:", re.IGNORECASE)
# Named dissent/abstention folded into a tally-only outcome sentence. Observed forms:
#   "... with Commissioner Frontero voting Nay"
#   "... with Commissioners Suesser and Sigg voting No ..."         (shared prefix)
#   "... Commissioner Tilson and Commissioner Shand voted "No.""    (repeated prefix,
#                                                                    curly-quoted verb)
#   "... Commissioner Suesser voted against the motion"
#   "... with Commissioner Strachan abstaining from the vote"
#   "... 4-0, with an abstention from Commissioner Suesser"         (name AFTER verb)
# A name-list may join with "and" and repeat the "Commissioner" prefix; the vote word
# may be wrapped in straight or curly quotes. Only dissenters/abstainers are ever named
# in these sentences (the majority stays "unanimous"/a tally), so every named roster
# member in the clause takes the clause's single dissent direction.
_NAMELIST = r"([A-Z][A-Za-z]+(?:\s+(?:and\s+)?(?:Commissioners?\s+)?[A-Z][A-Za-z]+)*)"
_QNAY = r"[\"“”']?(?:Nay|No)"
INLINE_NAY_RE = re.compile(
    rf"Commissioners?\s+{_NAMELIST}\s+(?:vot(?:ing|ed)\s+{_QNAY}\b|voted\s+against\b)",
    re.IGNORECASE)
INLINE_ABSTAIN_BEFORE_RE = re.compile(
    rf"Commissioners?\s+{_NAMELIST}\s+abstain(?:ing|ed|s)?\b", re.IGNORECASE)
INLINE_ABSTAIN_AFTER_RE = re.compile(
    rf"abstention[s]?\s+(?:from|by)\s+Commissioners?\s+{_NAMELIST}", re.IGNORECASE)


def folded_vote_window(seg):
    """If a MOTION segment folds its own outcome in (the 2024-06+/2024-10-09+ grammar
    that dropped the separate VOTE: marker), return a synthetic vote window that the
    normal emit() path parses exactly like a real VOTE block: any 'Vote on Motion:'
    per-name roll call, the outcome sentence, and an immediately-trailing named-dissent
    clause. Return None when the segment records NO outcome (e.g. a bare 'moved to
    ADJOURN' with only 'The meeting adjourned ...') so nothing is fabricated, and for
    a 'failed for lack of a second' segment (handled by the no_second path)."""
    # Drop lone-line page/watermark furniture WITH a trailing period ("1.", "3.", "D.")
    # that clean_lines keeps (it strips only the period-less shapes). Done here, on the
    # outcome window ONLY, so the stored motion text stays byte-identical to the pre-fix
    # corpus while a token wedged between "The motion" and its outcome verb no longer
    # severs the folded outcome sentence (audit fix #1: recovers the 2024-11-13
    # continuance + heals the 5 "passed with the <N>." garbles). A lone "3." is page
    # furniture; a real "3. Findings of Fact ..." keeps its text on the line and is NOT
    # a lone token, so it is untouched.
    seg = "\n".join(
        ln for ln in seg.split("\n")
        if not (NOISE_DOTTED_NUM_RE.match(ln.strip())
                or NOISE_DOTTED_LETTER_RE.match(ln.strip())))
    # collapse line-wraps first: the outcome sentence often breaks mid-phrase (even
    # "The\nmotion passed") and the roll call / dissent clause wrap across lines.
    seg = re.sub(r"\s+", " ", seg)
    if re.search(r"failed for lack of a second", seg, re.IGNORECASE):
        return None
    om = FOLDED_OUTCOME_RE.search(seg)
    if not om:
        return None
    names_region = ""
    vm = VOTE_ON_MOTION_RE.search(seg)
    if vm and vm.start() < om.start():
        names_region = seg[vm.start():om.start()]
    win = seg[om.start():om.end()]
    # Reunite a -layout SCRAMBLE (audit fix #1, the 2025-04-02 m6 "D" case): the
    # boilerplate outcome completion ("unanimous consent of the Commission." /
    # "unanimously") is sometimes hoisted ABOVE a truncated "The motion passed with the
    # <agenda-marker>." head, so FOLDED_OUTCOME_RE stops at the spurious marker period
    # and the outcome reads as garbage ("passed with the D."). The head has a genuine
    # result verb but its tail carries NO tally / "unanim" / "consent" / "carri" /
    # lack-of-second — i.e. it was severed. When that severed head is followed only by a
    # short furniture/agenda token (single letter or ≤3 digits + '.') AND the verbatim
    # completion phrase exists elsewhere in THIS segment (a folded segment = exactly one
    # motion, so the phrase is this motion's own outcome), splice the two source
    # fragments back into the sentence the minutes printed — never inventing words.
    _wlow = win.lower()
    _severed = not (TALLY_RE.search(win) or TALLY2_RE.search(win) or any(
        k in _wlow for k in ("unanim", "consent", "carri", "lack of a second",
                             "did not", "denied", "withdraw", "tabl")))
    if _severed and re.search(r"\bpass(?:ed)?\b\s+with\s+the\s+\S{1,4}\.$", win, re.I):
        comp = re.search(
            r"(?:with\s+the\s+)?unanimous\s+consent\s+of\s+the\s+Commission\.?"
            r"|unanimously\b", seg, re.IGNORECASE)
        if comp:
            head = re.sub(r"\s+\S{1,4}\.$", "", win)   # drop the trailing junk token
            comp_txt = comp.group(0).rstrip(".")
            comp_txt = re.sub(r"^with\s+the\s+", "", comp_txt, flags=re.IGNORECASE)
            win = f"{head} {comp_txt}."
    # a dissent attribution printed as its OWN sentence right after the outcome
    # ("The motion passed 4-1. Commissioner Suesser voted against the motion.";
    #  "The motion passed 5-2. Commissioner Tilson and Commissioner Shand voted "No."")
    tail = seg[om.end():om.end() + 220]
    tm = re.match(
        r"\s*([^.]*?\b(?:voted\s+against|vot(?:ing|ed)\s+[\"“”']?(?:Nay|No)"
        r"|abstain[a-z]*|abstention[a-z]*)\b[^.]*?\.)",
        tail, re.IGNORECASE)
    if tm:
        win += " " + tm.group(1)
    return (names_region + " " + win).strip()


def _add_named(namelist, bucket, buckets):
    """Split a 'Suesser and Sigg' / 'Tilson and Commissioner Shand' / 'Van Dine'
    name-list, resolve each roster member (multi-token surnames handled), and add to
    the given bucket. Non-roster tokens (staff, the stray word 'Commissioner') resolve
    to None and are dropped, never invented."""
    for part in re.split(r"\band\b|,", namelist, flags=re.IGNORECASE):
        part = re.sub(r"\bCommissioners?\b", " ", part, flags=re.IGNORECASE).strip()
        if not part:
            continue
        c = resolve_person(part)
        if c and c not in buckets[bucket]:
            buckets[bucket].append(c)


def capture_inline_dissent(window, buckets):
    """Attribute dissenters/abstainers named in a folded outcome sentence's prose.
    Only called for folded windows with no per-name roll call, so the printed tally
    stays authoritative and no majority name is invented."""
    for m in INLINE_NAY_RE.finditer(window):
        _add_named(m.group(1), "nay", buckets)
    for rx in (INLINE_ABSTAIN_BEFORE_RE, INLINE_ABSTAIN_AFTER_RE):
        for m in rx.finditer(window):
            _add_named(m.group(1), "abstain", buckets)


def parse_outcome_sentence(window):
    """Find the 'The motion ...' outcome sentence and return (passed, tally_str)."""
    m = re.search(r"[Tt]he motion\s+([^.]*)\.", window)
    sent = m.group(1) if m else ""
    low = sent.lower()
    if "fail" in low or "did not" in low or "denied" in low:
        passed = False
    elif "pass" in low or "carri" in low or "approv" in low or "unanim" in low:
        passed = True
    else:
        passed = None
    tally = ""
    tm = TALLY_RE.search(sent) or TALLY2_RE.search(sent)
    if tm:
        tally = f"{tm.group(1)}-{tm.group(2)}"
    elif "unanim" in low:
        tally = "unanimous"
    return passed, tally, sent.strip()


def direction(motion_text):
    """Semantic outcome label from the motion's OPERATIVE verb / recommendation
    direction. The motion text begins right after 'moved to', so the EARLIEST-
    appearing keyword is the operative one — a later mention of (e.g.) 'denial'
    inside the Conditions of Approval must not flip an APPROVE motion to 'Denied'."""
    t = motion_text.lower()
    patterns = [
        (r"(positive|favorable)\s+recommendation", "Positive recommendation"),
        (r"negative\s+recommendation", "Negative recommendation"),
        (r"forward a positive", "Positive recommendation"),
        (r"forward a negative", "Negative recommendation"),
        (r"\b(deny|denial|denying)\b", "Denied"),
        (r"\bapprov", "Approved"),
        (r"\bcontinu", "Continued"),
        (r"\btabl(e|ing)\b", "Tabled"),
        (r"\bwithdraw", "Withdrawn"),
    ]
    best_pos, best_lab = len(t) + 1, ""
    for pat, lab in patterns:
        m = re.search(pat, t)
        if m and m.start() < best_pos:
            best_pos, best_lab = m.start(), lab
    return best_lab


def build_result(motion_text, passed, tally, n_aye, n_nay, no_second=False):
    if no_second:
        return "Failed (no second)"
    lab = direction(motion_text)
    if n_aye or n_nay:
        tally = f"{n_aye}-{n_nay}"
    if passed is False:
        base = lab if lab in ("", ) else f"Failed ({lab})"
        if lab == "":
            base = "Failed"
        return f"{base} {tally}".strip()
    # passed (or unknown -> treat as recorded outcome)
    if lab:
        return f"{lab} {tally}".strip()
    return f"Passed {tally}".strip() if tally else "Passed"


# ---------------------------------------------------------------------------
# Meeting parse.
# ---------------------------------------------------------------------------
MARKER_RE = re.compile(r"(?m)^[ \t]*(MOTION|VOTE)\s*:")
SECTION_BREAK_RE = re.compile(r"(?m)^\s*\d{1,2}\.\s+[A-Z]")  # numbered agenda item


def extract_motion_text(seg):
    """From a MOTION: segment, return (text, mover, seconder, no_second)."""
    flat = " ".join(seg.split())
    flat = re.sub(r"^MOTION\s*:\s*", "", flat, flags=re.IGNORECASE)
    mover = seconder = None
    mv = MOVED_RE.search(flat)
    if mv:
        mover = resolve_person(mv.group(1))
    # seconder
    sm = SECOND_RE.search(flat) or SECOND_BY_RE.search(flat)
    if sm:
        seconder = resolve_person(sm.group(1))
    # motion text = from the mover verb up to the seconded clause
    text = flat
    if mv:
        tail = flat[mv.end():]
        # strip leading "to " after "moved"
        cut = None
        scut = re.search(rf"\.?\s*{ROLE}\s+\S.*?seconded", tail, re.IGNORECASE)
        sbcut = re.search(r",?\s*(?:and\s+)?seconded\s+by", tail, re.IGNORECASE)
        ends = [c.start() for c in (scut, sbcut) if c]
        if ends:
            cut = min(ends)
        text = (tail[:cut] if cut is not None else tail).strip(" .,:;")
        text = re.sub(r"^(to|that the Planning Commission)\s+", "", text, flags=re.IGNORECASE)
        if not text:
            text = flat
    # In the folded grammar the outcome (and any "Vote on Motion:" roll call /
    # "There was no second" note) trails the motion when there was no matchable
    # seconded clause to cut at -- trim it so the stored motion text stays clean.
    # (Classic motion text ends before "seconded"/the VOTE block, so this never fires
    # on the pre-folded corpus.)
    # NB: only trims folded-grammar tails (all folded outcomes are "passed"; a
    # no-second folded adjourn reads "There was no second"). "The motion failed for
    # lack of a second" is deliberately EXCLUDED so classic no-second motion text
    # stays byte-identical to the pre-folded corpus.
    tail_cut = re.search(
        r"\.\s+(?:Vote on Motion\s*:|There was no second\b|"
        r"[Tt]he motion\s+(?:was\s+seconded|passed|carried)\b)",
        text)
    if tail_cut:
        text = text[:tail_cut.start()].strip(" .,:;")
    no_second = bool(re.search(r"failed for lack of a second", flat, re.IGNORECASE))
    return text.strip(), mover, seconder, no_second


def parse_meeting(text):
    lines = clean_lines(text)
    body = "\n".join(lines)
    markers = list(MARKER_RE.finditer(body))
    votes = []
    motion_no = 0
    pending = None   # dict with motion seg info awaiting a VOTE

    def emit(motion_info, vote_window, folded=False):
        nonlocal motion_no
        mtext = motion_info["text"]
        no_second = motion_info["no_second"]
        if no_second:
            # motion that recorded its own failure for lack of a second (definitive;
            # takes priority over any window)
            passed, tally, sent = False, "", "failed for lack of a second"
            buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
            names_recorded = False
            names_mode = "tally"
            result = build_result(mtext, False, "", 0, 0, no_second=True)
        elif vote_window is None:
            # unpaired motion with NO recorded outcome anywhere -> honestly not a
            # recorded vote; drop (never fabricate an outcome).
            return
        else:
            buckets = parse_rollcall(vote_window)
            rollcall_named = any(buckets.values())
            passed, tally, sent = parse_outcome_sentence(vote_window)
            # one-off abstention named in tally-only prose ("...with one abstention by
            # Commissioner Johnson")
            abst = re.search(r"abstention by (?:Commissioner|Chair)\s+" + NAME, vote_window)
            if abst and not rollcall_named:
                c = canon(abst.group(1))
                if c:
                    buckets["abstain"].append(c)
            # folded-grammar outcome sentences name dissenters/abstainers in prose
            # rather than a "X-Nay" roll call; attribute them without touching the
            # printed tally.
            if folded and not rollcall_named:
                capture_inline_dissent(vote_window, buckets)
            names_recorded = any(buckets[b] for b in ("aye", "nay", "abstain", "recuse"))
            # when the whole roll call was named, its counts are the authoritative
            # tally; when names are only a supplemental dissent attribution, keep the
            # tally the source printed (n_aye/n_nay=0 leaves build_result's tally as-is).
            if rollcall_named:
                n_aye, n_nay = len(buckets["aye"]), len(buckets["nay"])
            else:
                n_aye = n_nay = 0
            result = build_result(mtext, passed, tally, n_aye, n_nay)
            # names_mode: "rollcall" = a full per-name roll call (tally == names);
            # "partial" = only dissenters/abstainers named beside a printed tally
            # (the folded / name-only-dissenters grammar); "tally" = no names.
            if rollcall_named:
                names_mode = "rollcall"
            elif names_recorded:
                names_mode = "partial"
            else:
                names_mode = "tally"
        motion_no += 1
        rec = {
            "motion_no": motion_no,
            "motion": mtext[:600],
            "body": BODY,
            "motion_type": classify(mtext),
            "action_type": action_type(mtext),
            "result": result,
            "result_text": sent[:200],
            "mover": motion_info["mover"],
            "seconder": motion_info["seconder"],
            "aye": buckets["aye"],
            "nay": buckets["nay"],
            "abstain": buckets["abstain"],
            "absent": buckets["absent"],
            "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "names_mode": names_mode,
        }
        votes.append(rec)

    for idx, mk in enumerate(markers):
        kind = mk.group(1).upper()
        seg_start = mk.start()
        seg_end = markers[idx + 1].start() if idx + 1 < len(markers) else len(body)
        seg = body[seg_start:seg_end]
        if kind == "MOTION":
            # A "MOTION:"-labeled block that is really just an OUTCOME (an outcome
            # sentence, no motion verb) belongs to the PENDING motion. This covers
            # the sporadic pre-2024 mislabel ("MOTION: The motion passed 4-1. ...")
            # and never fires on a real motion (which carries "moved"/"made a motion").
            own_window = folded_vote_window(seg)
            if (own_window is not None and not MOTION_VERB_RE.search(seg)
                    and pending is not None):
                emit(pending, own_window, folded=True)
                pending = None
                continue
            # a previous pending motion with no VOTE before this one is emitted now:
            # if it folded its OWN outcome in (2024-06+ grammar) use that window,
            # else it is a superseded restatement / outcome-less motion -> dropped
            # (unless it recorded a no-second failure).
            if pending is not None:
                pw = pending.get("own_window")
                emit(pending, pw, folded=pw is not None)
            mtext, mover, seconder, no_second = extract_motion_text(seg)
            pending = {"text": mtext, "mover": mover, "seconder": seconder,
                       "no_second": no_second, "own_window": own_window}
        else:  # VOTE
            # Source-error guard: a handful of meetings misprint a motion under a
            # "VOTE:" label ("VOTE: Commissioner X moved to forward ..."). If a VOTE
            # segment carries a motion verb but NO outcome sentence, treat it as the
            # (pending) motion so the next real VOTE pairs with it — don't emit a
            # hollow record.
            has_outcome = re.search(r"[Tt]he motion\s+(passed|failed|carried|did not)",
                                    seg)
            if not has_outcome and re.search(r"\bmoved to\b|made a motion", seg,
                                              re.IGNORECASE):
                if pending is not None:
                    pw = pending.get("own_window")
                    emit(pending, pw, folded=pw is not None)
                remotion = re.sub(r"^[ \t]*VOTE\s*:", "MOTION:", seg)
                mtext, mover, seconder, no_second = extract_motion_text(remotion)
                pending = {"text": mtext, "mover": mover, "seconder": seconder,
                           "no_second": no_second,
                           "own_window": folded_vote_window(remotion)}
                continue
            # vote window = the VOTE segment up to & incl the outcome sentence
            window = seg
            om = re.search(r"[Tt]he motion\s+[^.]*\.", seg)
            if om:
                window = seg[:om.end()]
            if pending is None:
                pending = {"text": "", "mover": None, "seconder": None,
                           "no_second": False, "own_window": None}
            emit(pending, window)
            pending = None
    if pending is not None:
        pw = pending.get("own_window")
        emit(pending, pw, folded=pw is not None)
    return votes


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def load_index():
    with open(MINUTES_INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def json_path_for(row):
    rel = row["path"].replace("minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def rebuild_csv():
    rows_out = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        date, title, source = mtg["date"], mtg["title"], mtg["source"]
        year = date[:4]
        for v in mtg["votes"]:
            base = {
                "date": date, "year": year, "title": title, "body": v.get("body", BODY),
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": source,
            }
            emitted = False
            for label, key in (("Aye", "aye"), ("Nay", "nay"), ("Abstain", "abstain"),
                               ("Absent", "absent"), ("Recuse", "recuse")):
                for member in v.get(key, []):
                    r = dict(base); r["member"] = member; r["vote"] = label
                    rows_out.append(r); emitted = True
            if not emitted:
                r = dict(base); r["member"] = ""; r["vote"] = ""
                rows_out.append(r)
    rows_out.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows_out:
            w.writerow([r.get(c, "") for c in cols])
    return len(rows_out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rows = load_index()
    unparsed = []
    for row in rows:
        md_path = os.path.join(PC, row["path"])
        if not os.path.exists(md_path):
            unparsed.append(row["path"] + " (missing file)")
            continue
        out_json = json_path_for(row)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        if os.path.exists(out_json) and not args.force:
            continue
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
        try:
            votes = parse_meeting(text)
        except Exception as e:  # noqa
            unparsed.append(f"{row['path']} (parse error: {e})")
            continue
        meeting_obj = {
            "date": row["date"],
            "title": row["title"],
            "body": BODY,
            "body_slug": row.get("slug", "planning-commission-meeting"),
            "source": row["path"],
            "format": row.get("format", "text"),
            "votes": votes,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting_obj, f, indent=1, ensure_ascii=False)

    n_rows = rebuild_csv()

    meetings = motions = contested = tally_only = recs = finals = 0
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        for v in mtg["votes"]:
            motions += 1
            if not v["names_recorded"]:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            if v.get("action_type") == "Recommendation":
                recs += 1
            elif v.get("action_type") == "Final Action":
                finals += 1
    print(json.dumps({
        "meetings_processed": meetings,
        "motions_extracted": motions,
        "member_vote_rows": n_rows,
        "tally_only_motions": tally_only,
        "contested_motions": contested,
        "recommendations": recs,
        "final_actions": finals,
        "unparsed_meetings": unparsed,
    }, indent=2))


if __name__ == "__main__":
    main()
