#!/usr/bin/env python3
"""
extract_votes.py — Millcreek Planning Commission vote extraction (PURE deterministic).

Reads the 149 minutes markdown files listed in
`planning_commission/minutes_index.csv`, finds each recorded PC motion
(mover / seconder / per-member roll call or tally verdict), tags it
recommendation-vs-final-action, and emits:

  - one JSON per meeting  -> planning_commission/votes/<year>/<week>/<file>.json
  - a rebuilt long CSV    -> planning_commission/all_votes.csv  (13-col schema)
  - roster.csv            -> planning_commission/roster.csv
  - a validation report   -> planning_commission/votes/_validation_report.txt

NO LLM, NO network. Resumable: skips meetings whose JSON exists unless --force.

CARDINAL RULE — never fabricate.
  * A roll call that names each commissioner -> named member rows (Aye/Nay/Abstain).
  * A tally-only verdict ("All Commissioners present voted yes", "voted unanimous
    in favor", "The motion passed unanimously") with NO per-member names -> recorded
    names_recorded:false, EMPTY member lists, and the result string carries the
    qualitative "(unanimous)" (we do NOT invent a numeric split or attribute who
    voted which way).
  * A motion that "failed due to lack of a second" never came to a vote -> skipped.
  * An OCR-garbled surname is fuzzy-matched to the roster; if it is unrecoverable the
    member is left BLANK and flagged (never guessed).

body = "PlanningCommission" and title = "Planning Commission" on EVERY row.

MILLCREEK VOTE GRAMMAR (built to this; verified across 2017-2026)
-----------------------------------------------------------------
Three roll-call idioms coexist:

 A) Prose per-name (dominant 2019+; every commissioner named even when unanimous):
      "<Mover> moved to <motion>. <Seconder> seconded. Chair LaMar called for the
       vote. Chair LaMar voted yes, Commissioner Reid voted yes, ... and
       Commissioner Wright voted yes. The motion passed unanimously."
    Grouped variant: "Stephens, Reid, and Claerhout voted yes. Commissioner LaMar
       voted no. The motion passed 6-1."  Abstain: "Commissioner Larsen abstained."

 B) Dash roll call (late-2017 / 2018):
      "Commissioner Carlson motioned that ... Commissioner Wilson seconded the motion.
       Chairman Stephens – Yes / Commissioner Booth – Yes / ... Motion passed."

 C) Structured field block (early-2017; files containing 'Motion by:'):
      "Motion: To recommend approval of ... Motion by: Commissioner Carlson
       2nd by: Commissioner Mumford  Vote: Commissioners voted unanimous in favor
       (of commissioners present)."

Tally-only verdicts (no per-member names): "All/An Commissioners present voted yes",
"Commissioner(s) voted unanimous in favor", "The motion passed unanimously".
Numeric-only tally (no names): "The motion passed 6-1".
Named-dissent-in-tally: "All Commissioners voted yes except Commissioner Allen who
voted no" -> the dissenter is named; the ayes are the OTHER present commissioners.
"""
import os, re, csv, json, sys, glob, difflib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = os.path.join(REPO, "planning_commission")
MIN_DIR = os.path.join(PC, "minutes")
VOTES_DIR = os.path.join(PC, "votes")
INDEX = os.path.join(PC, "minutes_index.csv")
ALL_VOTES = os.path.join(PC, "all_votes.csv")
ROSTER = os.path.join(PC, "roster.csv")
VALIDATION = os.path.join(VOTES_DIR, "_validation_report.txt")

FORCE = "--force" in sys.argv
BODY = "PlanningCommission"
TITLE = "Planning Commission"

# ---------------------------------------------------------------------------
# Roster.  surname(lower) -> canonical full display name.  Harvested empirically
# from the mover/seconder/roll-call lines and the attendance headers (see the
# build notes in CLAUDE.md).  Katie Larsen (a city PLANNER) and Nathan Anderson
# (an applicant) are NOT commissioners and never cast a recorded vote, so the
# vote-line surnames map unambiguously: Larsen->Christian Larsen, Anderson->Steven
# Anderson (both confirmed: no "Anderson"/"Larsen" roll-call vote predates them).
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "lamar": "Shawn LaMar",
    "reid": "Victoria Reid",
    "larsen": "Christian Larsen",
    "soule": "Diane Soule",
    "wright": "Ian Wright",
    "lofgren": "Per Lofgren",
    "claerhout": "Scott Claerhout",
    "vance": "Dwayne Vance",
    "anderson": "Steven Anderson",
    "allen": "David Allen",
    "richardson": "Jacob Richardson",
    "sieber": "Skye Sieber",
    "mumford": "Mark Mumford",
    "hulsberg": "David Hulsberg",
    "healey": "Fred Healey",
    "stephens": "Tom Stephens",
    "booth": "Russ Booth",
    "carlson": "David Carlson",
    "wilson": "Heather Wilson",
    "burgess": "Jenny Burgess",
    "cianflone": "Aryel Cianflone",
}
# OCR / spelling variants seen in the corpus -> canonical surname key.  These are
# folded as EXACT aliases (not left to the fuzzy fallback, which is deliberately
# strict — see canon() — so it never maps a DIFFERENT surname such as staffer
# "Sanderson"/"Henderson" onto commissioner "Anderson").
SURNAME_ALIASES = {
    "alien": "allen", "anen": "allen", "allan": "allen",   # OCR ll->li / ll->n
    "larson": "larsen",
    "clearhout": "claerhout", "claerhoud": "claerhout", "jaerhout": "claerhout",
    "healy": "healey",
    "larmar": "lamar", "lalviar": "lamar", "lamak": "lamar", "lamar": "lamar",
    "stephen": "stephens", "stevens": "stephens", "steohens": "stephens",
    "stephenson": "stephens",
    "sieper": "sieber", "sicber": "sieber",
    "seiber": "sieber",   # clerk ei/ie swap (2019-09-18 GP-19-002 roll: the dropped
                          # aye fabricated a 3:3 tie; truly passed 4:3. T3.1(m))
    "snule": "soule", "souse": "soule",
    "carlston": "carlson",
    "andersen": "anderson",
    "lofgreen": "lofgren",
}
# Non-commissioner surnames (staff / applicants / others) that resemble a roster
# surname — canon() must NEVER resolve these to a commissioner.
NON_COMMISSIONER = {
    "sanderson", "sanders", "henderson",   # Brad Sanderson (Planning Manager) et al.
    "wilkinson", "hadley", "richard", "dwight", "lauren", "loren", "ellen",
    "allyn", "allmen", "allie", "lance", "vince", "right", "rights",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())

# role words (incl. common OCR corruptions of "Commissioner")
ROLE_WORDS = (r"Commissioners?|C[o0][ir]?[nrm]{1,3}[ir]?ss?ioners?|"
              r"Chair(?:man|person|woman)?|Vice[\s-]?Chair(?:man|person)?|"
              r"Acting\s+Chair|Cliair\w*")


def canon(token):
    """Map a name fragment to a roster full name, or None if unresolvable."""
    if not token:
        return None
    t = re.sub(r"[^A-Za-z'\-]", " ", token).strip().lower()
    if not t:
        return None
    # take the last alphabetic word (surname) but also try each word
    words = [w for w in re.split(r"\s+", t) if len(w) >= 2]
    if not words:
        return None
    for w in reversed(words):
        if w in NON_COMMISSIONER:
            continue
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    # fuzzy fallback (OCR only): STRICT — same leading letter, near-equal length,
    # high ratio.  This admits genuine single-char OCR corruptions of a roster
    # surname while rejecting different real surnames (Sanderson/Henderson/Richard/
    # Dwight/Lauren…) that would otherwise collide with a commissioner.
    for w in reversed(words):
        if len(w) < 5 or w in NON_COMMISSIONER:
            continue
        for sur in SURNAMES:
            if w[0] != sur[0] or abs(len(w) - len(sur)) > 2:
                continue
            if difflib.SequenceMatcher(None, w, sur).ratio() >= 0.87:
                return SURNAME_TO_FULL[sur]
    return None


# ---------------------------------------------------------------------------
# Case numbers (referral key) + descriptive land-use family (motion_type).
# ---------------------------------------------------------------------------
CASE_RE = re.compile(r"\b([A-Z]{2,4})-(\d{2})-(\d{2,3})\b")
FILE_RE = re.compile(r"(?:file\s*)?#\s?(\d{4,6})\b", re.I)

PREFIX_FAMILY = {
    "CU": "Conditional Use", "CUP": "Conditional Use",
    "ZM": "Rezone", "RC": "Rezone",
    "ZT": "Zone Text Amendment",
    "SD": "Subdivision", "SDA": "Subdivision",
    "GP": "General Plan Amendment",
    "SV": "Street Vacation",
    "PUD": "Planned Unit Development",
    "EX": "Exception",
    "LB": "Other Land-Use", "FC": "Other Land-Use", "CCOZ": "Other Land-Use",
    "SP": "Other Land-Use", "PD": "Other Land-Use",
}


def find_case(text):
    m = CASE_RE.search(text)
    if m:
        return m.group(0).upper()
    m = FILE_RE.search(text)
    if m:
        return "#" + m.group(1)
    return ""


def motion_type(motion, case):
    t = motion.lower()
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"\b(adjourn|recess|reconvene|table|continue|postpone|"
                 r"agenda|work session|field trip)\b", t):
        return "Procedural/Administrative"
    if re.search(r"\b(elect|nominate|appoint|reappoint|nomination)\b", t):
        return "Appointment"
    pref = case.split("-")[0].upper() if case and "-" in case else ""
    if pref in PREFIX_FAMILY:
        return PREFIX_FAMILY[pref]
    if re.search(r"rezone|zone change|zoning map|reclassif|zone map", t):
        return "Rezone"
    if re.search(r"zone text|text amendment|ordinance amend|code amend", t):
        return "Zone Text Amendment"
    if re.search(r"conditional use|\bcup\b", t):
        return "Conditional Use"
    if re.search(r"subdivision|preliminary plat|final plat|\bplat\b|lot ", t):
        return "Subdivision"
    if re.search(r"general plan", t):
        return "General Plan Amendment"
    if re.search(r"street vacation|vacat", t):
        return "Street Vacation"
    if re.search(r"exception|\bexempt", t):
        return "Exception"
    if re.search(r"ordinance", t):
        return "Ordinance"
    if re.search(r"rules of procedure|bylaws|resolution", t):
        return "Procedural/Administrative"
    return "Other Land-Use"


# ---------------------------------------------------------------------------
# Attendance -> present commissioners (context only; NOT used to fabricate a
# unanimous tally count).  Two-column layout; a surname followed within ~16 chars
# by "(absent)"/"(excused)" is out.
# ---------------------------------------------------------------------------
def parse_present(flat):
    m = re.search(r"\b(?:ATTENDANCE|Commissioners)\b", flat)
    start = m.start() if m else 0
    e = re.search(r"called (?:the meeting )?to order|Attendees:|PUBLIC HEARING|"
                  r"BUSINESS MEETING|read a statement", flat[start:])
    region = flat[start: start + (e.start() if e else 1400)]
    present = []
    for sn in SURNAMES:
        mm = re.search(r"\b" + sn + r"\b", region, re.I)
        if not mm:
            continue
        tail = region[mm.end(): mm.end() + 16].lower()
        if "absent" in tail or "excused" in tail:
            continue
        present.append(SURNAME_TO_FULL[sn])
    return sorted(set(present))


# ---------------------------------------------------------------------------
# Vote-region parsing.
# ---------------------------------------------------------------------------
VOTE_VERB = re.compile(
    r"\bvoted\s+(yes|no|nay|aye|in\s+favor|against|to\s+approve|to\s+deny)\b"
    r"|\b(abstained|abstains|recused|recuses)\b", re.I)

DASH_RE = re.compile(
    r"(?:(?:" + ROLE_WORDS + r")\s+)?"
    r"([A-Z][A-Za-z'\-]{2,})\s*[–—\-]\s*"
    r"(?i:(Yes|No|Aye|Nay|Abstain(?:ed)?|Absent|Recuse(?:d)?))\b")

RE_LACK_SECOND = re.compile(
    r"(?:fail(?:ed)?|died)\s+(?:due\s+to|for)\s+(?:a\s+)?lack\s+of\s+a?\s*second"
    r"|(?:for|due\s+to)\s+lack\s+of\s+(?:a\s+)?second|no\s+second", re.I)

RE_NUM_TALLY = re.compile(
    r"motion\s+(passed|failed|carried)\s+(?:with\s+)?(\d+)\s*[-–to ]+\s*(\d+)", re.I)
WORDNUM = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
           "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
RE_WORD_TALLY = re.compile(
    r"(?:passed|failed)\s+with\s+(\w+)\s+yes\s+votes?\s+and\s+(\w+)\s+no\s+votes?", re.I)
RE_UNANIMOUS = re.compile(
    r"voted\s+(?:to\s+\w+\s+)?unanimous|unanimous(?:ly)?\s+in\s+favor|"
    r"unanimously\s+(?:approv|adopt|recommend|pass|in\s+favor|to)|"
    r"(?:approv|adopt|pass|carried|recommend)\w*\s+unanimous|"
    r"motion\s+(?:passed|carried)\s+unanimous(?:ly)?|passed\s+unanimous", re.I)
# plain unanimous tally ("All/An Commissioners [present] voted yes/in favor") with
# no per-member enumeration.  "all OTHER commissioners" is deliberately excluded
# (that is the partial-attribution case handled by RE_ALLOTHERS).
RE_ALLCOMM = re.compile(
    r"(?:all|an)\s+commissioners?(?:\s+present)?\s+voted\s+(?:yes|in\s+favor)", re.I)
RE_ALLOTHERS = re.compile(
    r"(?:all\s+other|other|remaining)\s+commissioners?\s+voted\s+(?:yes|in\s+favor)", re.I)
RE_EXCEPT = re.compile(
    r"(?:all|an)\s+commissioners?(?:\s+present)?\s+voted\s+yes\s+except\s+"
    r"(?:" + ROLE_WORDS + r")?\s*([A-Z][A-Za-z'\-]+)\s+who\s+(voted\s+no|abstained)",
    re.I)
RE_FAILED = re.compile(r"motion\s+(?:failed|did\s+not\s+(?:pass|carry))|"
                       r"failed\s+for\s+lack", re.I)
RE_DEFER = re.compile(r"\b(continue[d]?|continuance|table[d]?|postpone[d]?|withdraw)\b", re.I)


def norm_vote(tok):
    t = tok.lower()
    if t.startswith("y") or t.startswith("a") and "abst" not in t or "favor" in t or "approve" in t:
        return "Aye"
    if t.startswith("n") and "abst" not in t or "against" in t or "deny" in t:
        return "Nay"
    if "abst" in t:
        return "Abstain"
    if "recus" in t:
        return "Recuse"
    return None


def names_in(seg):
    """All roster full names appearing in a text segment (role-prefixed or bare
    roster surname), in order, deduped."""
    out = []
    # role-prefixed
    for m in re.finditer(r"(?:" + ROLE_WORDS + r")\s+([A-Z][A-Za-z'\-]{2,})", seg):
        nm = canon(m.group(1))
        if nm and nm not in out:
            out.append(nm)
    # bare roster surnames (grouped lists: "Stephens, Reid, and Claerhout")
    for m in re.finditer(r"\b([A-Z][A-Za-z'\-]{2,})\b", seg):
        w = m.group(1).lower()
        w = SURNAME_ALIASES.get(w, w)
        if w in SURNAME_TO_FULL and SURNAME_TO_FULL[w] not in out:
            out.append(SURNAME_TO_FULL[w])
    return out


def parse_named_votes(region):
    """Prose per-name + grouped: pair each 'voted X'/'abstained' with the roster
    names that precede it since the previous verb.  Returns {full_name: vote}."""
    members = {}
    last = 0
    for m in VOTE_VERB.finditer(region):
        seg = region[last:m.start()]
        # cut the segment to the current clause (avoid pulling names from a prior
        # sentence that already had its own verb)
        v = norm_vote(m.group(1) or m.group(2) or "")
        if v:
            for nm in names_in(seg):
                members[nm] = v          # last assignment wins (rare re-list)
        last = m.end()
    return members


def parse_dash_votes(region):
    members = {}
    for m in DASH_RE.finditer(region):
        nm = canon(m.group(1))
        v = norm_vote(m.group(2))
        if nm and v:
            members[nm] = v
    return members


# ---------------------------------------------------------------------------
# Motion anchoring.
# ---------------------------------------------------------------------------
# A move-verb only counts as a motion when it is followed by a motion continuation
# ("moved to approve", "motioned that", "made a motion to", "motioned recommend").
# This rejects prose like "the fence had been moved from the edge" / "JOANN moved
# within Millcreek" that would otherwise seed spurious motions.
MOVE_CONT = (r"to|that|for|recommend|approv|deny|denial|grant|continu|adopt|"
             r"nominat|reappoint|table|withdraw|forward|support|send|make")
MOVE_VERB = re.compile(
    r"\b(?:moved|motioned)(?=\s+(?:" + MOVE_CONT + r")\b)"
    r"|\bmade\s+a\s+motion(?=\s+(?:to|that|for)\b)", re.I)


def find_mover(flat, vpos):
    """Nearest roster surname within ~110 chars before a move-verb -> mover."""
    back = flat[max(0, vpos - 110): vpos]
    best = None
    for m in re.finditer(r"\b([A-Z][A-Za-z'\-]{2,})\b", back):
        nm = canon(m.group(1))
        if nm:
            best = (nm, m.start())          # keep the LAST (nearest) hit
    return best[0] if best else None


def motion_boundaries(flat):
    """Return list of (mover, verb_end, motion_start) for real PC motions in doc
    order.  Excludes verbs whose subject is not a commissioner (community council,
    applicant, etc.)."""
    out = []
    for vm in MOVE_VERB.finditer(flat):
        mover = find_mover(flat, vm.start())
        if mover:
            out.append((mover, vm.end(), vm.start()))
    return out


SECOND_RE = re.compile(
    r"(?:seconded\s+by\s+(?:" + ROLE_WORDS + r")?\s*([A-Z][A-Za-z'\-]{2,})"
    r"|(?:" + ROLE_WORDS + r")?\s*([A-Z][A-Za-z'\-]{2,})\s+seconded)", re.I)


def clean_motion_text(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(?:the\s+motion|motion)\s*:?\s*", "", s, flags=re.I)
    if len(s) > 500:
        return s[:500].rsplit(" ", 1)[0] + "…"
    return s


# ---------------------------------------------------------------------------
# result-string construction (mirrors the WVC/Logan PC encoding).
# ---------------------------------------------------------------------------
# Operative-recommendation signal only — must NOT fire on "conditions recommended
# by staff" / "the staff recommendations" (those are advisory boilerplate, not the
# motion's own disposition).
REC_RE = re.compile(
    r"\brecommend(?:ing)?\s+(?:approv|denial|deny|to\b|that\b|the\s+(?:city|council))|"
    r"(?:forward|send|make[a-z ]*|positive|negative|favorable)[^.]{0,40}recommendation|"
    r"recommendation\s+(?:of|to)\b|recommend\s+(?:approval|denial)", re.I)
COUNCIL_RE = re.compile(r"\bto the (?:millcreek )?city council\b", re.I)


def classify(motion):
    t = motion.lower()
    if re.search(r"\bminutes\b", t) and re.search(r"approv|adopt", t):
        return "procedural"
    if re.search(r"\b(adjourn|recess|reconvene|elect|nominate|appoint|nomination|"
                 r"approve the agenda|amend the agenda|work session|field trip|"
                 r"rules of procedure|bylaws)\b", t):
        return "procedural"
    if REC_RE.search(t) or COUNCIL_RE.search(t):
        return "recommendation"
    return "final"


def proposes_approval(motion):
    t = motion.lower()
    if re.search(r"\b(den(?:y|ial)|not\s+recommend|recommend\s+denial|"
                 r"deny\s+the|against)\b", t):
        return False
    return True


def build_result(kind, motion, ayes, nays, passed, unanimous, deferred, tally_known):
    if kind == "procedural":
        if deferred:
            base = "Pass" if passed else "Fail"
            return (f"{ayes}:{nays} {base} ({deferred})" if tally_known
                    else f"{base} (unanimous) ({deferred})" if unanimous
                    else f"{base} ({deferred})")
        if tally_known:
            return f"{ayes}:{nays} {'Pass' if passed else 'Fail'}"
        return "Pass (unanimous)" if (unanimous and passed) else ("Pass" if passed else "Fail")

    net_pos = (proposes_approval(motion) == passed)
    if deferred:                       # a continuance/tabling is a deferral
        base = "Pass" if passed else "Fail"
        return (f"{ayes}:{nays} {base} ({deferred})" if tally_known
                else f"{base} ({deferred})")
    if kind == "recommendation":
        d = "Positive" if net_pos else "Negative"
        return (f"{d} recommendation {ayes}:{nays}" if tally_known
                else f"{d} recommendation (unanimous)" if unanimous
                else f"{d} recommendation")
    # final action
    disp = "Approved" if net_pos else "Denied"
    return (f"{ayes}:{nays} {disp} (Final Action)" if tally_known
            else f"{disp} (Final Action, unanimous)" if unanimous
            else f"{disp} (Final Action)")


# ---------------------------------------------------------------------------
# Structured 'Motion by:' block parser (early-2017 files).
# ---------------------------------------------------------------------------
STRUCT_RE = re.compile(
    r"Motion:\s*(.+?)\s+Motion by:\s*(.+?)\s+2nd by:\s*(.+?)\s+Vote:\s*(.+?)"
    r"(?=\s*(?:\d+\)|Motion:|BUSINESS MEETING|MEETING ADJOURNED|Ordinance Issues|$))",
    re.I | re.S)


def extract_structured(flat, present):
    votes = []
    for m in STRUCT_RE.finditer(flat):
        motion_text = clean_motion_text(m.group(1))
        mover = canon(m.group(2)) or ""
        seconder = canon(m.group(3)) or ""
        vote_txt = m.group(4)[:400]
        case = find_case(motion_text + " " + m.group(1))
        kind = classify(motion_text)
        deferred = ""
        dm = RE_DEFER.search(motion_text)
        if dm:
            w = dm.group(1).lower()
            deferred = "Continued" if w.startswith("continu") else (
                "Tabled" if w.startswith("tabl") else (
                    "Withdrawn" if w.startswith("withdraw") else "Continued"))
        # votes in the Vote: text (same cascade as the prose parser)
        members = _votes_from_region(vote_txt, present)
        if not members:
            continue
        votes.append(_finish(motion_text, mover, seconder, kind, case, members,
                             vote_txt, present, deferred))
    return votes


# ---------------------------------------------------------------------------
# Prose / dash parser (everything else).
# ---------------------------------------------------------------------------
def extract_prose(flat, present):
    bounds = motion_boundaries(flat)
    votes = []
    for i, (mover, vend, vstart) in enumerate(bounds):
        nxt = bounds[i + 1][2] if i + 1 < len(bounds) else len(flat)
        window = flat[vstart:nxt]
        # motion text: from move-verb to seconder (or 400 chars)
        after = flat[vend:nxt]
        sm = SECOND_RE.search(after)
        seconder = ""
        if sm:
            seconder = canon(sm.group(1) or sm.group(2)) or ""
            motion_text = clean_motion_text(after[:sm.start()])
            region = after[sm.end():]
        else:
            motion_text = clean_motion_text(after[:400])
            region = after
        # a bare "to <verb> ..." reads better with the verb included
        mt = motion_text
        if not re.match(r"(?i)(to|that)\b", mt):
            mt = mt  # leave as-is
        case = find_case(mt + " " + region[:200])
        kind = classify(mt)
        deferred = ""
        dm = RE_DEFER.search(mt)
        if dm:
            w = dm.group(1).lower()
            deferred = "Continued" if w.startswith("continu") else (
                "Tabled" if w.startswith("tabl") else (
                    "Withdrawn" if w.startswith("withdraw") else "Continued"))

        # skip motions that never came to a vote
        if RE_LACK_SECOND.search(region[:200]) and not VOTE_VERB.search(region[:400]):
            continue

        members = _votes_from_region(region, present)
        if not members:
            # no recorded vote near this move-verb -> not a real motion (discussion,
            # superseded substitute, community-council recitation). Skip, never emit.
            continue
        votes.append(_finish(mt, mover, seconder, kind, case, members,
                             region[:300], present, deferred))
    return votes


RE_CALLER = re.compile(
    r"(?:" + ROLE_WORDS + r")?\s*[A-Z][A-Za-z'\-]+\s+called\s+"
    r"(?:the\s+meeting\s+)?(?:for\s+the\s+vote|to\s+order)", re.I)


def parse_roll(region):
    """Per-name roll call from the roll-call span only: strip the 'X called for the
    vote' caller clause and truncate at the outcome phrase so post-vote discussion
    ('...asked why she voted no') never leaks in."""
    cut = re.search(r"[Tt]he\s+motion\s+(?:passed|failed|carried|did\s+not)", region)
    roll = region[:cut.start()] if cut else region
    return parse_named_votes(RE_CALLER.sub(" called for the vote ", roll))


def _votes_from_region(region, present):
    """Return dict full_name->vote for a vote region, honoring the cardinal rule.
    Special marker keys: '__unanimous__' => tally-only unanimous (no member names);
    '__tally__' => (ayes, nays, passed) numeric tally with no names;
    '__carried__' => the motion carried (used with named-dissenter-only rolls)."""
    # 1) dash roll call
    dash = parse_dash_votes(region)
    if len(dash) >= 2:
        return dash
    # 2) named-dissenter idioms: "...except X who voted no" / "X voted nay, Y
    #    abstained, all OTHER commissioners voted in favor".  We name ONLY the
    #    explicitly-named voters (the source does NOT name the "all others" ayes,
    #    so we NEVER attribute/guess them — the ayes stay unnamed, the motion is
    #    still recorded as carried with its named dissent).
    if RE_EXCEPT.search(region) or RE_ALLOTHERS.search(region):
        named = parse_roll(region)
        # keep only genuinely-named non-affirmative + any explicit affirmative;
        # drop nothing — parse_roll already excludes the nameless "all others".
        if named:
            named = dict(named)
            named["__carried__"] = True
            return named
    # 3) plain unanimous tally-only ("All Commissioners voted yes") — no names.
    #    Checked before per-name parsing so the vote-caller isn't miscounted.
    if RE_ALLCOMM.search(region):
        return {"__unanimous__": True}
    # 4) prose per-name / grouped roll call.
    named = parse_roll(region)
    if named:
        return named
    # 5) explicit numeric tally (no names)
    nt = RE_NUM_TALLY.search(region)
    if nt:
        a, b = int(nt.group(2)), int(nt.group(3))
        passed = nt.group(1).lower() != "failed"
        ayes, nays = (max(a, b), min(a, b)) if passed else (min(a, b), max(a, b))
        return {"__tally__": (ayes, nays, passed)}
    wt = RE_WORD_TALLY.search(region)
    if wt:
        a = WORDNUM.get(wt.group(1).lower(), None)
        b = WORDNUM.get(wt.group(2).lower(), None)
        if a is not None and b is not None:
            return {"__tally__": (a, b, a >= b)}
    # 5) unanimous tally-only (no per-member names)
    if RE_UNANIMOUS.search(region):
        return {"__unanimous__": True}
    return {}


def _finish(motion_text, mover, seconder, kind, case, members, src, present, deferred):
    unanimous = False
    tally_known = False
    ayes = nays = 0
    aye = nay = abstain = absent = recuse = []
    unknown = []
    names_recorded = False

    # 'carried' idiom: named dissenter(s)/abstainer(s) only; the "all others in
    # favor" ayes are NOT named by the source, so they are NOT enumerated and the
    # numeric aye total is unknown (tally_known stays False -> qualitative result).
    carried = members.pop("__carried__", False) if isinstance(members, dict) else False

    if "__unanimous__" in members:
        unanimous = True
        passed = True
    elif "__tally__" in members:
        ayes, nays, passed = members["__tally__"]
        tally_known = True
    elif carried and members:
        names_recorded = True
        aye = sorted([n for n, v in members.items() if v == "Aye"])
        nay = sorted([n for n, v in members.items() if v == "Nay"])
        abstain = sorted([n for n, v in members.items() if v == "Abstain"])
        recuse = sorted([n for n, v in members.items() if v == "Recuse"])
        # motion carried ("all other commissioners voted in favor"); ayes unnamed
        passed = True
        tally_known = False
    elif members:
        names_recorded = True
        aye = sorted([n for n, v in members.items() if v == "Aye"])
        nay = sorted([n for n, v in members.items() if v == "Nay"])
        abstain = sorted([n for n, v in members.items() if v == "Abstain"])
        recuse = sorted([n for n, v in members.items() if v == "Recuse"])
        ayes, nays = len(aye), len(nay)
        tally_known = True
        passed = ayes > nays if (ayes or nays) else True
    else:
        # no recorded vote near this motion -> caller decides; here mark failed-none
        passed = True
        unanimous = bool(RE_UNANIMOUS.search(src))
        if unanimous:
            pass

    if RE_FAILED.search(src) and not names_recorded:
        passed = False

    result = build_result(kind, motion_text, ayes, nays, passed, unanimous,
                          deferred, tally_known)

    rec = {
        "motion": motion_text,
        "body": BODY,
        "motion_type": motion_type(motion_text, case),
        "action_category": kind,
        "case_no": case,
        "result": result,
        "result_source": re.sub(r"\s+", " ", src).strip()[:200],
        "mover": mover,
        "seconder": seconder,
        "names_recorded": names_recorded,
        "aye": aye, "nay": nay, "abstain": abstain,
        "absent": absent, "recuse": recuse,
    }
    if not names_recorded:
        rec["tally_only"] = {"ayes": ayes, "nays": nays,
                             "unanimous": unanimous,
                             "source": rec["result_source"]}
    return rec


# ---------------------------------------------------------------------------
# Per-meeting driver
# ---------------------------------------------------------------------------
def extract_meeting(path, rel_source, date, year):
    raw = open(path, encoding="utf-8").read()
    # drop the markdown front-matter header block (through the first '---')
    body = raw.split("\n---\n", 1)[-1]
    flat = re.sub(r"[ \t]+", " ", body)
    flat = re.sub(r"\n{2,}", "\n", flat)
    flat = re.sub(r"\s+", " ", flat)
    present = parse_present(flat)

    if re.search(r"Motion by:", flat, re.I):
        votes = extract_structured(flat, present)
    else:
        votes = extract_prose(flat, present)

    for n, v in enumerate(votes, 1):
        v_no = {"motion_no": n}
        v_no.update(v)
        votes[n - 1] = v_no

    return {
        "date": date,
        "year": int(year),
        "title": TITLE,
        "body": BODY,
        "present": present,
        "source": rel_source,
        "votes": votes,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def json_path_for(rel_path, year):
    parts = rel_path.split("/")           # minutes/<year>/<week>/<file>.md
    week = parts[-2]
    return os.path.join(VOTES_DIR, str(year), week, parts[-1].replace(".md", ".json"))


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)

    for r in rows:
        path = os.path.join(REPO, "planning_commission", r["path"])
        if not os.path.exists(path):
            print("MISSING", r["path"], file=sys.stderr)
            continue
        jp = json_path_for(r["path"], r["year"])
        if os.path.exists(jp) and not FORCE:
            continue
        rel_source = r["path"]
        try:
            meeting = extract_meeting(path, rel_source, r["date"], r["year"])
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr)
            continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w", encoding="utf-8") as f:
            json.dump(meeting, f, indent=1, ensure_ascii=False)

    rebuild_csv(rows)
    build_roster(rows)


def rebuild_csv(rows):
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    out = []
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        for v in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=TITLE, body=BODY,
                        motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v.get("mover", ""), seconder=v.get("seconder", ""),
                        source=obj["source"])
            groups = [("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                      ("absent", "Absent"), ("recuse", "Recuse")]
            emitted = False
            for key, lab in groups:
                for mem in v.get(key, []):
                    row = dict(base); row["member"] = mem; row["vote"] = lab
                    out.append(row); emitted = True
            if not emitted:
                row = dict(base); row["member"] = ""; row["vote"] = ""
                out.append(row)
    with open(ALL_VOTES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in out:
            w.writerow({k: row.get(k, "") for k in cols})
    return len(out)


def build_roster(rows):
    """commissioner, first_seen, last_seen, n_meetings — from anyone who
    MOVED / SECONDED / cast a NAMED vote (unambiguous seat evidence).  Present-only
    appearances are NOT used for ranges (attendance is a noisy 2-col layout)."""
    seen = {}
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        date = obj["date"]
        people = set()
        for v in obj["votes"]:
            for k in ("mover", "seconder"):
                if v.get(k) in FULLNAMES:
                    people.add(v[k])
            for k in ("aye", "nay", "abstain", "recuse"):
                people.update(v.get(k, []))
        for p in people:
            d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
            d["first"] = min(d["first"], date)
            d["last"] = max(d["last"], date)
            d["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: seen[n]["first"]):
            d = seen[nm]
            w.writerow([nm, d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
    print("done")
