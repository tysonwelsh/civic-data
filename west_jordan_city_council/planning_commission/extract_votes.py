#!/usr/bin/env python3
"""
Extract West Jordan PLANNING COMMISSION motions + votes from minutes markdown.

For each meeting it writes one JSON under
  votes/<year>/<week-monday>/<date>_<slug>.json
and rebuilds all_votes.csv (long format, one row per recorded member-vote) plus
roster.csv (commissioner, first_seen, last_seen, n_meetings).

West Jordan PC minutes are almost entirely TALLY-ONLY: a motion reads
  "MOTION: <Name> moved to ... The motion was seconded by <Name> and passed 6-0
   in favor."
No per-member "the vote was recorded as follows" roll calls exist in this corpus.
The ONLY per-member attributions are the named dissenters/abstainers on CONTESTED
motions ("... passed 5-1 in favor with Jay Thomas casting the negative vote",
"... failed 3-4 with Commissioners X, Y, Z, and W casting the negative votes",
"... with Commissioner Anderson abstaining") and named ABSENT/EXCUSED members.

CARDINAL RULE: never fabricate. The affirmative ("aye") majority is never named in
these minutes, so the aye list is ALWAYS empty (we record the tally, not guessed
names). names_recorded is true only when at least one per-member VOTE
(nay/abstain/recuse) is individually attributed -> a PARTIAL roll call.

result encoding (machine-detectable; see CLAUDE.md):
  recommendation  -> "Positive recommendation N:N" / "Negative recommendation N:N"
  final action    -> "N:N Approved (Final Action)" / "N:N Denied (Final Action)"
  procedural      -> "N:N Pass"  (or "N:N Fail")
Direction/type keys off the motion wording ("recommend"/"forward" -> recommendation),
and a FAILED motion is oriented by OUTCOME (a failed approve = Denied; a failed
positive-recommendation = Negative recommendation).

Run:  python3 extract_votes.py           (resumable; skips existing JSONs)
      python3 extract_votes.py --force    (re-extract all)
"""
import csv
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))          # planning_commission/
REPO = os.path.dirname(ROOT)                               # repo root
MIN_DIR = os.path.join(ROOT, "minutes")
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")

# ---- Planning Commission roster: appointed (no election). Canonical surname -> full name.
#      Built from attendee headers + movers across 2020-2026 (see CLAUDE.md). ----
NAME_CANON = {
    "allen": "Ammon Allen",
    "shelton": "Kent Shelton",
    "quinney": "Matt Quinney",
    "hatch": "Trish Hatch",
    "thomas": "Jay Thomas",
    "winn": "George Winn",
    "marchant": "McKenna Marchant",
    "hollingsworth": "Tom Hollingsworth",
    "roberts": "John Roberts",
    "gonzalez": "Emily Gonzalez",
    "anderson": "Jimmy Anderson",     # James "Jimmy" Anderson (oath of office 2024)
    "richardson": "Catherine Richardson",  # Catherine Paquette-Richardson
    "acker": "Cheryl Acker",
    "bloom": "Pamela Bloom",
    "england": "Corbin England",
}
# OCR / spelling variants -> canonical surname key above.
VARIANTS = {
    "alien": "allen",          # OCR "Ammon Alien"
    "gonzales": "gonzalez",    # spelling variant
    "quiney": "quinney",       # OCR "Matt Quiney"
    "paquette": "richardson",  # Catherine Paquette-Richardson
}
# First name -> canonical member, used to detect when an explicit first name points
# to a DIFFERENT roster member who shares the surname (a real collision) vs. a mere
# nickname/OCR variant of the matched member. Surnames are unique here today, so this
# index never fires — it is future-proofing against a second same-surname member.
FIRST_TO_FULL = {}
for _sur, _full in NAME_CANON.items():
    FIRST_TO_FULL.setdefault(_full.split()[0].lower(), _full)

# Council-only members who appear ONLY in the 4 joint Council+PC work sessions.
# A motion moved by one of these is a CITY COUNCIL action -> skipped (PC body only).
COUNCIL_ONLY = {
    "mcconnehey", "green", "jacob", "lamb", "pack", "whitelock", "worthen",
    "bedore", "bennett", "harris", "wignall", "burton", "dirk",
}

TITLE_RE = re.compile(
    r"^(commissioner|commission|chairperson|chair|vice[\s-]*chair|"
    r"council\s*member|councilmember|board\s*member|member|mayor)\b",
    re.I,
)


def norm_name(raw):
    """Return canonical PC commissioner full name, or None if not a known PC member."""
    if not raw:
        return None
    s = unicodedata.normalize("NFKD", raw)
    s = s.replace("&", " ").strip().strip(".,;:()")
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    # strip leading title words (possibly several: "Planning Commission Chair Member")
    prev = None
    while prev != s:
        prev = s
        s = TITLE_RE.sub("", s).strip().strip(".,;:()")
        s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    low = s.lower()
    tokens = [t.strip(".,;:()") for t in low.split()]

    def _first_name_conflicts(i, canon_full):
        # Full-name gate: a surname is NOT unique across a roster's history. Reject a
        # surname fold ONLY when the preceding first name belongs to a DIFFERENT known
        # roster member (a genuine shared-surname collision, e.g. Deborah vs Lisa
        # Jensen) — NOT for a mere nickname/OCR variant (Matthew vs Matt Quinney),
        # which must still fold. No-op while every surname is unique.
        if i <= 0:
            return False
        pfx = tokens[i - 1].strip(".")
        if not (pfx.isalpha() and len(pfx) > 1):
            return False
        cf = canon_full.split()[0].lower()
        if pfx == cf or cf.startswith(pfx):        # matches this member's own first name
            return False
        other = FIRST_TO_FULL.get(pfx)
        return other is not None and other != canon_full

    # surname token match (try each token, prefer last)
    for i in range(len(tokens) - 1, -1, -1):
        tok = tokens[i]
        if tok in COUNCIL_ONLY:
            return None
        sur = tok if tok in NAME_CANON else VARIANTS.get(tok)
        if sur in NAME_CANON:
            if _first_name_conflicts(i, NAME_CANON[sur]):
                return None
            return NAME_CANON[sur]
    # fuzzy: any canonical/variant surname appears as a whole word
    for sur in NAME_CANON:
        if re.search(r"\b" + re.escape(sur) + r"\b", low):
            return NAME_CANON[sur]
    for var, sur in VARIANTS.items():
        if re.search(r"\b" + re.escape(var) + r"\b", low):
            return NAME_CANON[sur]
    return None


def clean_ws(text):
    return re.sub(r"[ \t]+", " ", text)


def parse_name_list(blob):
    """Parse a comma/'and' separated member list -> list of canonical PC names."""
    blob = blob.replace("\n", " ")
    blob = clean_ws(blob).strip().strip(".,;:()")
    if not blob:
        return []
    parts = re.split(r",|\.| and | & ", blob)
    out = []
    for p in parts:
        n = norm_name(p)
        if n and n not in out:
            out.append(n)
    return out


_DASHES = dict.fromkeys(
    [0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212, 0xFE58, 0xFE63, 0xFF0D],
    ord("-"),
)


def normalize_text(text):
    text = text.translate(_DASHES)
    text = text.replace("\x0c", "\n")
    return text


# ------------------------------------------------------------------ motion split
MOTION_HDR_RE = re.compile(r"^[ \t_]*MOTION\s*:[ \t_]*", re.I | re.M)
NARR_MOTION_RE = re.compile(r"\b(?:moved to|moved,|made a motion)\b", re.I)


def split_motions(text):
    """Yield each motion block (MOTION: headers + narrative 'moved' anchors)."""
    anchors = [m.start() for m in MOTION_HDR_RE.finditer(text)]
    hdr_set = set(anchors)
    for m in NARR_MOTION_RE.finditer(text):
        seg_start = text.rfind("\n", 0, m.start())
        prev_period = text.rfind(". ", 0, m.start())
        start = max(seg_start, prev_period)
        start = start + 1 if start >= 0 else 0
        # skip passive/non-motion uses of "moved" ("...it be moved to the back lots",
        # "the item was moved to the next agenda") that are not somebody making a motion.
        pre = text[max(0, m.start() - 7):m.start()].lower()
        if re.search(r"\b(be|been|being|was|were|is|are|to|not|get|gets)\s+$", pre):
            continue
        covered = any(-5 <= m.start() - h <= 600 for h in hdr_set)
        if not covered:
            anchors.append(start)
    anchors = sorted(set(anchors))
    for k, start in enumerate(anchors):
        end = anchors[k + 1] if k + 1 < len(anchors) else len(text)
        yield text[start:min(end, start + 2500)]


def motion_substance(block):
    """Full motion text from 'moved ...' up to 'seconded'/sentence end (untruncated)."""
    m = re.search(r"\b(?:moved|made a motion)\b[, ]*(.*?)(?:\.\s*\n|\bThe motion was seconded\b|\bseconded\b)",
                  block, re.S | re.I)
    if m:
        return clean_ws(m.group(1).replace("\n", " ")).strip().strip(".,;: ")
    txt = clean_ws(block.replace("\n", " ")).strip()
    txt = re.sub(r"^[ _]*MOTION:\s*", "", txt, flags=re.I)
    return txt.strip().strip(".,;: ")


def motion_display(substance):
    # drop the trailing lead-in to the seconding clause ("... moving forward. The
    # motion was") that the substance capture sometimes keeps when a newline split
    # "The motion\nwas seconded".
    txt = re.sub(r"[.,;:\s]*The motion(?: was)?\s*$", "", substance, flags=re.I).strip()
    if len(txt) > 400:
        txt = txt[:400].rsplit(" ", 1)[0] + "…"
    return txt


def extract_mover_seconder(block):
    mover = seconder = None
    mm = re.search(r"(?:^|\n)[ _]*(?:MOTION:\s*)?(.{0,80}?)\b(?:moved|made a motion)\b",
                   block, re.S | re.I)
    if mm:
        mover = norm_name(mm.group(1).split("\n")[-1])
    ms = re.search(r"seconded by\s+([A-Za-z .'\-]{0,40})", block, re.I)
    if ms:
        seconder = norm_name(ms.group(1).split(".")[0])
    return mover, seconder


# ------------------------------------------------------------------ outcome/tally
OUTCOME_RE = re.compile(
    r"\b(passed|failed|carried|approved|denied|defeated)\b[^0-9\n]{0,30}?"
    r"(\d+)\s*-\s*(\d+)", re.I)
UNAN_RE = re.compile(r"\b(passed|carried)\b[^.\n]{0,40}\bunanimous", re.I)


def parse_outcome(block):
    """Return (passed:bool|None, ayes:int|None, nays:int|None)."""
    m = OUTCOME_RE.search(block)
    if m:
        word = m.group(1).lower()
        passed = word in ("passed", "carried", "approved")
        a, b = int(m.group(2)), int(m.group(3))
        return passed, a, b
    if UNAN_RE.search(block) or re.search(r"\bpassed unanimously\b", block, re.I):
        return True, None, None
    return None, None, None


# ----------------------------------------------------------- per-member capture
NEG_RE = re.compile(
    r"with\s+(.+?)\s+(?:casting (?:the )?negative vote|casting (?:the )?negative votes|"
    r"voting (?:in opposition|against|no|nay)|opposed)",
    re.I | re.S)
ABSTAIN_RE = re.compile(
    r"with\s+(.+?)\s+abstain(?:ing|ed)|(\b[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)\s+abstain(?:ing|ed)",
    re.I | re.S)
RECUSE_RE = re.compile(
    r"(.{0,60}?)\s+recus(?:ed|ing|al)", re.I | re.S)
ABSENT_RE = re.compile(
    r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?(?:\s*,\s*[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)*"
    r"(?:\s*,?\s+and\s+[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)?)\s+(?:was|were)\s+(?:absent|excused)",
    re.I)


def outcome_window(block):
    """Slice the result SENTENCE(S) right after the tally, where dissent/absent are
    stated. Restricting capture here prevents later-discussion bleed (a stray
    '... not opposed ...' in the next agenda item) from being read as a vote."""
    m = OUTCOME_RE.search(block) or UNAN_RE.search(block)
    if not m:
        return ""
    seg = block[m.start():m.start() + 450]
    # stop at the next motion anchor or an asterisk separator line
    cut = re.search(r"\n[ \t]*MOTION\s*:|\n\s*[*#=]{3,}|\bMOTION:", seg)
    if cut:
        seg = seg[:cut.start()]
    return seg


def capture_members(block):
    """Return dict vote->[names] from the contested-motion outcome sentence.
    aye stays empty (the affirmative majority is never named in WJ PC minutes)."""
    res = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    block = outcome_window(block)
    if not block:
        return res
    # negative voters
    for m in NEG_RE.finditer(block):
        for n in parse_name_list(m.group(1)):
            if n not in res["nay"]:
                res["nay"].append(n)
    # abstain
    for m in ABSTAIN_RE.finditer(block):
        seg = m.group(1) or m.group(2) or ""
        for n in parse_name_list(seg):
            if n not in res["abstain"]:
                res["abstain"].append(n)
    # recuse (only if clearly a vote recusal, not narrative "he should recuse")
    for m in RECUSE_RE.finditer(block):
        seg = m.group(1)
        if re.search(r"\b(should|whether|if|while|consider|question|process)\b", seg, re.I):
            continue
        for n in parse_name_list(seg):
            if n not in res["recuse"] and n not in res["nay"]:
                res["recuse"].append(n)
    # absent / excused
    for m in ABSENT_RE.finditer(block):
        for n in parse_name_list(m.group(1)):
            if n not in res["absent"]:
                res["absent"].append(n)
    return res


# ----------------------------------------------------------------- classification
def classify_action(substance):
    """Return ('recommendation'|'final'|'procedural', direction) where direction is
    'positive'/'negative' (recommendation) or 'approve'/'deny' (final) or '' (proc)."""
    t = substance.lower()
    # procedural FIRST: a deferral/administrative verb governs even when the motion
    # body mentions "recommended by staff" (e.g. "moved that the PC TABLE the decision
    # ... with suggestions as recommended by staff").
    if re.search(r"\bminutes\b|\bnominate\b|\belect\b|\bappoint\b|\bvice[\s-]*chair\b|"
                 r"\badjourn|\brecess|\bcontinue\b|\btable\b|\bpostpone|\bexcuse\b|"
                 r"\bagenda\b|\bclosed session\b|design review committee|\bratif|"
                 r"\bschedule\b|order of the agenda|amend the order|"
                 r"\bto serve as\b.*\bchair\b|"
                 r"\bmove (?:the |this )?(?:item|decision|matter|application|"
                 r"public hearing|consideration)\b", t):
        return "procedural", ""
    # recommendation: a recommendation FORWARDED to City Council. Match "recommend"
    # or "forward ... (recommendation|council)" but NOT the idiom "moving forward".
    if re.search(r"\brecommend", t) or \
       re.search(r"\bforward(?:s|ed|ing)?\b[^.]{0,40}\b(?:recommendation|council)\b", t):
        if re.search(r"negative recommendation|recommendation of denial|denial|\bdeny\b", t):
            return "recommendation", "negative"
        return "recommendation", "positive"
    # final action
    if re.search(r"\bdeny\b|\bdenial\b", t):
        return "final", "deny"
    return "final", "approve"


def build_result(kind, direction, passed, a, b):
    """Encode the verbatim-derived result string (see module docstring)."""
    if a is None:
        tally = "unanimous"
        if passed is False:
            tally = "fail"
    else:
        tally = f"{a}:{b}"
    # orient by outcome: a failed motion produces the OPPOSITE substantive result
    eff = direction
    if passed is False:
        if direction == "positive":
            eff = "negative"
        elif direction == "negative":
            eff = "positive"
        elif direction == "approve":
            eff = "deny"
        elif direction == "deny":
            eff = "approve"

    if kind == "recommendation":
        label = "Positive recommendation" if eff == "positive" else "Negative recommendation"
        if a is None:
            return f"{label} ({'unanimous' if passed else 'failed'})"
        return f"{label} {tally}"
    if kind == "final":
        label = "Approved (Final Action)" if eff == "approve" else "Denied (Final Action)"
        if a is None:
            return f"{label} ({'unanimous' if passed else 'failed'})"
        return f"{tally} {label}"
    # procedural
    if a is None:
        return f"Pass (unanimous)" if passed else "Fail"
    return f"{tally} {'Pass' if passed else 'Fail'}"


# --------------------------------------------------------------------- meeting
def extract_meeting(path, rel_source):
    raw = open(path, encoding="utf-8", errors="replace").read()
    raw = normalize_text(raw)
    votes = []
    motion_no = 0
    for block in split_motions(raw):
        substance = motion_substance(block)
        if not substance or len(substance) < 4:
            continue
        mover, seconder = extract_mover_seconder(block)
        # Skip City Council actions embedded in the joint Council+PC work sessions:
        # capture the raw text introducing the motion ("<who> moved …") and, when it
        # is NOT a PC commissioner, drop it if it names a council-only member or a
        # council title (e.g. "Council Vice Chair Kelvin Green moved to adjourn").
        rawm = re.search(r"(?:^|\n)[ _]*(?:MOTION:\s*)?(.{0,70}?)\b(?:moved|made a motion)\b",
                         block, re.S | re.I)
        mover_phrase = (rawm.group(1).split("\n")[-1] if rawm else "").lower()
        if mover is None and (
            re.search(r"council\s*member|councilmember|council\s*(?:vice\s*)?chair", mover_phrase)
            or any(re.search(r"\b" + s + r"\b", mover_phrase) for s in COUNCIL_ONLY)
        ):
            continue
        passed, a, b = parse_outcome(block)
        members = capture_members(block)

        # lack of a second -> recorded motion, no vote
        lack = re.search(r"lack of (?:a )?second", block, re.I)
        if passed is None and not any(members[k] for k in ("nay", "abstain", "recuse")):
            if lack:
                kind, direction = classify_action(substance)
                votes.append(_mk(motion_no + 1, substance, kind, direction,
                                 "Failed (no second)", mover, seconder, members))
                motion_no += 1
                continue
            # no detectable outcome -> not a real recorded motion, skip
            if not re.search(r"\bseconded\b", block, re.I):
                continue

        kind, direction = classify_action(substance)
        result = build_result(kind, direction, passed if passed is not None else True, a, b)
        votes.append(_mk(motion_no + 1, substance, kind, direction, result,
                         mover, seconder, members))
        motion_no += 1
    return votes


def _mk(no, substance, kind, direction, result, mover, seconder, members):
    names_recorded = bool(members["nay"] or members["abstain"] or members["recuse"])
    return {
        "motion_no": no,
        "motion": motion_display(substance),
        "motion_type": motion_type(substance, kind),
        "action_class": ("pc_recommendation" if kind == "recommendation"
                         else "pc_final_action" if kind == "final" else "procedural"),
        "result": result,
        "mover": mover or "",
        "seconder": seconder or "",
        "aye": members["aye"],
        "nay": members["nay"],
        "abstain": members["abstain"],
        "absent": members["absent"],
        "recuse": members["recuse"],
        "names_recorded": names_recorded,
    }


def motion_type(substance, kind):
    t = substance.lower()
    if re.search(r"\bminutes\b", t):
        return "Procedural/Administrative"
    if re.search(r"\bnominate\b|\belect\b|\bchair\b|design review committee|appoint", t):
        return "Appointment"
    if re.search(r"adjourn|recess|continue|table|postpone|agenda|excuse|closed session", t):
        return "Procedural/Administrative"
    if re.search(r"rezone|zoning|general plan|land use|annex|subdivision|plat|variance|"
                 r"conditional use|development (agreement|plan)|master development|"
                 r"site plan|planned community|text amendment|ordinance", t):
        return "Land-Use/Zoning"
    return "Other"


# ------------------------------------------------------------------- roster
HDR_RE = re.compile(
    r"^[ \t]*(?:PRESENT|COMMISSION|COMMISSIONERS(?:\s+PRESENT)?|MEMBERS\s+PRESENT)\s*:[ \t]*(.*)$",
    re.I)


def parse_attendance(path):
    """Return list of canonical commissioners marked PRESENT in this meeting."""
    raw = normalize_text(open(path, encoding="utf-8", errors="replace").read())
    lines = raw.split("\n")
    present = []
    for i, ln in enumerate(lines):
        m = HDR_RE.match(ln)
        if not m:
            continue
        blob = m.group(1)
        j = i + 1
        while j < len(lines) and j < i + 4:
            nxt = lines[j]
            if re.match(r"^[ \t]*(STAFF|PUBLIC|EXCUSED|ABSENT|STUDENT)\s*:", nxt, re.I):
                break
            if re.match(r"^[ \t]*\*+\s*$", nxt) or re.match(r"^[ \t]*[A-Z]{3,}", nxt.strip()[:5] if False else ""):
                pass
            if re.match(r"^\s*[*#=]{3,}", nxt) or re.match(r"^\s*\d+\.\s", nxt):
                break
            if not nxt.strip():
                break
            blob += " " + nxt
            j += 1
        # the PRESENT roster is the FIRST sentence; anything after the first period
        # ("... and Jimmy Anderson. Emily Gonzalez was excused.") is attendance prose
        # about excused/absent members -> drop it so absentees aren't counted present.
        blob = re.split(r"\.\s|\.$", blob, 1)[0]
        blob = re.split(r"\b(?:was|were)\b\s+(?:excused|absent)", blob, 1)[0]
        for n in parse_name_list(blob):
            if n not in present:
                present.append(n)
    return present


# ------------------------------------------------------------------ validation
VALIDATION_REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
TALLY_RE = re.compile(r"(\d+)\s*:\s*(\d+)")


def write_validation_report(all_meetings, roster_span):
    lines = []
    total = named = consistent = 0
    mismatches = []
    offroster = []
    for date, source, votes in sorted(all_meetings):
        yr = date[:4]
        for v in votes:
            total += 1
            # off-roster / out-of-range check on every captured member
            for key in ("nay", "abstain", "absent", "recuse", "aye"):
                for mem in v[key]:
                    fs, lsx = roster_span.get(mem, (None, None))
                    if fs is None:
                        offroster.append((date, mem, "off-roster", source))
                    elif not (fs <= date <= lsx):
                        offroster.append((date, mem, f"out-of-range ({fs}..{lsx})", source))
            if not v["names_recorded"]:
                continue
            named += 1
            m = TALLY_RE.search(v["result"])
            if not m:
                continue
            ta, tb = int(m.group(1)), int(m.group(2))
            nay = len(v["nay"]) + len(v["recuse"])
            # PC minutes name only the dissent side; aye list is intentionally empty.
            # Consistency = named nays do not exceed the tally's against-count, and
            # for a clear contested motion the named nays equal the smaller side.
            against = min(ta, tb)
            if len(v["nay"]) <= max(ta, tb) and (len(v["nay"]) == against or len(v["nay"]) == tb):
                consistent += 1
            else:
                mismatches.append((date, v["motion_no"],
                                   f"named nays={len(v['nay'])} vs tally {ta}:{tb}",
                                   v["motion"][:70], source))

    lines.append("PLANNING COMMISSION VOTE EXTRACTION - VALIDATION REPORT")
    lines.append("=" * 70)
    lines.append(f"meetings checked         : {len(all_meetings)}")
    lines.append(f"motions total            : {total}")
    lines.append(f"partial roll-call motions: {named}  (named dissent/abstain/recuse)")
    lines.append(f"  consistent             : {consistent}")
    lines.append(f"  tally mismatches       : {len(mismatches)}")
    lines.append(f"off-roster/out-of-range members: {len(offroster)}")
    lines.append("")
    lines.append("NOTE: WJ PC minutes are tally-only; only the DISSENT side is ever")
    lines.append("named. The aye majority is never listed and is left EMPTY (never")
    lines.append("guessed). Consistency here = named nays fit the printed tally.")
    lines.append("")
    lines.append("TALLY MISMATCHES")
    lines.append("-" * 70)
    if not mismatches:
        lines.append("(none)")
    for date, mno, detail, motion, source in mismatches:
        lines.append(f"[{date}] motion #{mno}: {detail} | {motion}")
        lines.append(f"    src: {source}")
    lines.append("")
    lines.append("OFF-ROSTER / OUT-OF-RANGE")
    lines.append("-" * 70)
    if not offroster:
        lines.append("(none - every captured commissioner is within roster range)")
    for date, mem, why, source in offroster:
        lines.append(f"[{date}] {mem}: {why}")
        lines.append(f"    src: {source}")
    lines.append("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(VALIDATION_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(mismatches), len(offroster)


# ----------------------------------------------------------------------- main
def load_index():
    with open(INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    force = "--force" in sys.argv
    rows = load_index()
    all_rows = []
    all_meetings = []
    roster = {}  # name -> [first_seen, last_seen, n_meetings]
    processed = motions_total = member_rows = 0
    named_motions = tally_only = contested = recs = finals = ocr_meetings = 0
    ocr_motions = 0
    unparsed = []

    for r in rows:
        relpath = r["path"]
        date, year, title, slug = r["date"], r["year"], r["title"], r["slug"]
        fmt = r.get("format", "text")
        abspath = os.path.join(REPO, relpath)
        if not os.path.exists(abspath):
            unparsed.append(relpath + " (missing)")
            continue
        week = os.path.basename(os.path.dirname(relpath))
        out_dir = os.path.join(VOTES_DIR, year, week)
        out_path = os.path.join(out_dir, f"{date}_{slug}.json")

        # roster from attendance (always recompute - cheap, deterministic)
        for name in parse_attendance(abspath):
            if name not in roster:
                roster[name] = [date, date, 0]
            roster[name][0] = min(roster[name][0], date)
            roster[name][1] = max(roster[name][1], date)
            roster[name][2] += 1

        if os.path.exists(out_path) and not force:
            data = json.load(open(out_path, encoding="utf-8"))
        else:
            votes = extract_meeting(abspath, relpath)
            data = {"date": date, "title": "Planning Commission",
                    "body": "PlanningCommission", "format": fmt,
                    "source": relpath, "votes": votes}
            os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)

        processed += 1
        if fmt == "ocr":
            ocr_meetings += 1
        all_meetings.append((data["date"], data["source"], data["votes"]))
        if not data["votes"]:
            unparsed.append(relpath + " (no votes found)")
        for v in data["votes"]:
            motions_total += 1
            if fmt == "ocr":
                ocr_motions += 1
            # extend roster membership span to any role appearance (mover/seconder/
            # named dissent/abstain/recuse/absent) so a member who was ABSENT at their
            # last meetings (and so missing from PRESENT) still spans to that date.
            roles = [v["mover"], v["seconder"]]
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                roles += v[k]
            for name in roles:
                if not name:
                    continue
                if name not in roster:
                    roster[name] = [date, date, 0]
                roster[name][0] = min(roster[name][0], date)
                roster[name][1] = max(roster[name][1], date)
            if v["names_recorded"]:
                named_motions += 1
            else:
                tally_only += 1
            ac = v.get("action_class")
            if ac == "pc_recommendation":
                recs += 1
            elif ac == "pc_final_action":
                finals += 1
            if v["nay"] or v["abstain"] or v["recuse"] or " Fail" in v["result"] \
               or "failed" in v["result"].lower():
                contested += 1
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v[key]:
                    member_rows += 1
                    all_rows.append({
                        "date": data["date"], "year": year,
                        "title": "Planning Commission", "body": "PlanningCommission",
                        "motion_no": v["motion_no"], "motion": v["motion"],
                        "motion_type": v["motion_type"], "result": v["result"],
                        "mover": v["mover"], "seconder": v["seconder"],
                        "member": member, "vote": vote, "source": data["source"],
                    })

    # all_votes.csv (exact 13-col schema)
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"])
        w.writeheader()
        for row in sorted(all_rows, key=lambda x: (x["date"], x["motion_no"], x["member"])):
            w.writerow(row)

    # roster.csv
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for name in sorted(roster, key=lambda n: (roster[n][0], n)):
            fs, ls, n = roster[name]
            w.writerow([name, fs, ls, n])

    roster_span = {n: (v[0], v[1]) for n, v in roster.items()}
    val_mismatch, val_offroster = write_validation_report(all_meetings, roster_span)

    stats = {
        "meetings_processed": processed,
        "ocr_meetings": ocr_meetings,
        "motions_extracted": motions_total,
        "ocr_motions": ocr_motions,
        "member_vote_rows": member_rows,
        "partial_rollcall_motions": named_motions,
        "tally_only_motions": tally_only,
        "recommendations": recs,
        "final_actions": finals,
        "contested_motions": contested,
        "distinct_commissioners": len(roster),
        "validation_tally_mismatches": val_mismatch,
        "validation_offroster": val_offroster,
        "unparsed_or_emptyvote_meetings": unparsed,
    }
    print(json.dumps(stats, indent=2))
    return stats


if __name__ == "__main__":
    main()
