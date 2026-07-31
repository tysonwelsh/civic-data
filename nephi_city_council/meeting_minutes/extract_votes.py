#!/usr/bin/env python3
"""
Nephi City Council vote extractor.

Reads the ~243 council-meeting markdown files under
meeting_minutes/minutes/<year>/<week>/, parses every recorded motion, tags the
governing `body` (Council default; CRA for the Community Reinvestment Agency
meeting / agency agenda blocks), normalizes member names, and emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<date>_*.json (resumable)
  - meeting_minutes/all_votes.csv (long format, one row per member-vote OR one summary
    row when names were not recorded, WITH a body column).

NEPHI FORMAT (narrative-only, NO per-member roll-call grid in the usual case)
----------------------------------------------------------------------------
The overwhelmingly dominant motion form is a narrative sentence:

    Councilor <Name> moved to <action>. Councilor <Name> seconded the motion.
    The motion passed on a unanimous vote.            (or "passed unanimously",
                                                       "carried on a unanimous vote")

For these we capture mover + seconder + result string + motion text and set
`names_recorded:false` -> ONE summary row (empty member/vote). We never invent
who voted which way from a "unanimous" result.

Only a MINORITY of motions name voters. Those forms are all handled:
  * Block roll call introduced by "...on the following [roll call] vote:" /
    "...with the following vote:" / "The vote was as follows:" followed by either
      - label lists:   "Yes: Councilor Ostler" / "Nay: Councilor Jones"
                       "Yes: Councilors Shari Cowan, Tate Douglas, JD Parady"
                       (names continue on indented bare lines under the label), or
      - tabular rows:  "Kent Jones    Nay" / "Larry Ostler    Yes"  (name then vote)
  * Mayor tie-break:  "...passed with the Mayor breaking the following tie vote:" or a
    tabular 2-2 block closed by "Mayor <X> broke the tie with a 'Yes' vote."  The Mayor
    is otherwise NON-VOTING (strong-mayor form); a mayor vote is flagged and counted.
  * Inline named dissent / absentee: "...passed 4-0. Councilor Worwood was absent..."
  * Inline numeric tally: "passed N-M" / "N to M" (for a FAILED vote of N-M the larger
    side is AGAINST -- oriented by outcome, never guessed from a unanimous result).

WORWOOD DISAMBIGUATION (two different people)
---------------------------------------------
"Skip Worwood" (councilor 2020-2025) and "Travis L. Worwood" (councilor 2024+) are
DIFFERENT people who overlapped on the council in 2024-2025. A reference that gives a
first name is mapped directly; a bare "Councilor Worwood" is resolved from the meeting
header's seated Worwood(s) -- and if BOTH are seated it is left as
"Worwood (ambiguous)" rather than guessed.

See CLAUDE.md for the body-tagging and narrative-only documentation.
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
REPO_ROOT = ROOT.parent

# ---------------------------------------------------------------------------
# People / name normalization
# ---------------------------------------------------------------------------
# Canonical full names keyed by surname (last token). Worwood handled separately.
SURNAME_CANON = {
    "nielson": "Glade R. Nielson",
    "nielsen": "Glade R. Nielson",
    "seely": "Justin D. Seely",
    "jones": "Kent Jones",
    "memmott": "Nathan Memmott",
    "memott": "Nathan Memmott",
    "ostler": "Larry Ostler",
    "oster": "Larry Ostler",     # OCR/typo variant ("Ost.er", "Oster")
    "callaway": "Jeramie Callaway",
    "callway": "Jeramie Callaway",
    "jeramie": "Jeramie Callaway",  # first-name-only reference (unambiguous)
    "parady": "JD Parady",
    "pardy": "JD Parady",        # typo variant
    "cowan": "Shari Cowan",
    "cown": "Shari Cowan",       # typo variant
    "douglas": "Tate Douglas",
}

WORWOOD_TRAVIS = "Travis L. Worwood"
WORWOOD_SKIP = "Skip Worwood"
WORWOOD_AMBIG = "Worwood (ambiguous)"
# Surname typo variants that must route through the Worwood disambiguation logic.
WORWOOD_VARIANTS = {"worwood", "wowood", "worwod", "worrwood", "worwoood"}

ROLE_WORDS = (
    r"Councilors?|Council\s*Member|Councilmember|Director|Board\s*Member|"
    r"Agency\s*Member|Chair(?:man|woman|person)?|Vice[-\s]?Chair|Secretary|"
    r"Mayor\s*Pro\s*Tem(?:pore)?|Mayor|Mr\.|Ms\.|Mrs\."
)
ROLE_STRIP_RE = re.compile(rf"^(?:{ROLE_WORDS})\s+", re.I)


def _clean_name(raw):
    s = raw.strip()
    s = s.strip("*").strip()
    s = re.sub(r"[’`]", "'", s)
    s = re.sub(r"\s+", " ", s)
    s = s.strip(".,;:()-").strip()
    # strip one or more leading role words
    prev = None
    while prev != s:
        prev = s
        s = ROLE_STRIP_RE.sub("", s).strip()
    return s


def normalize_name(raw, worwoods=None):
    """Return canonical member name, or None if not a recognizable council member.

    `worwoods` is the set of seated Worwood canonical names for the meeting, used to
    resolve a bare "Worwood" reference.
    """
    if not raw:
        return None
    s = _clean_name(raw)
    if not s:
        return None
    toks = s.lower().split()
    if not toks:
        return None
    if "worwood" in toks or any(t in WORWOOD_VARIANTS for t in toks):
        if "travis" in toks:
            return WORWOOD_TRAVIS
        if "skip" in toks:
            return WORWOOD_SKIP
        # bare reference -> resolve from seated roster
        w = worwoods or set()
        if len(w) == 1:
            return next(iter(w))
        if WORWOOD_TRAVIS in w and WORWOOD_SKIP in w:
            return WORWOOD_AMBIG
        return WORWOOD_AMBIG  # never guess
    # surname is normally the last token
    if toks[-1] in SURNAME_CANON:
        return SURNAME_CANON[toks[-1]]
    if toks[0] in SURNAME_CANON:
        return SURNAME_CANON[toks[0]]
    # OCR-split surname with an internal period ("Ost.er" -> "oster"): try the
    # period-stripped form ONLY at final lookup (never for Worwood detection, so a
    # spurious "...Worwood. Councilor Ostler" span still falls through to Ostler).
    for t in (toks[-1], toks[0]):
        tt = t.replace(".", "")
        if len(tt) > 1 and tt in SURNAME_CANON:
            return SURNAME_CANON[tt]
    return None


def mayor_for(date):
    """Return the elected (non-voting) Mayor for a meeting date (ISO string)."""
    # Glade R. Nielson served as Mayor through 2021; Justin D. Seely from 2022-01.
    return "Glade R. Nielson" if date < "2022-01-01" else "Justin D. Seely"


def detect_worwoods(header, date):
    """Set of seated Worwood canonical names, from the header attendance region."""
    s = set()
    for m in re.finditer(r"(Travis|Skip)[^\n]{0,14}?Worwood", header, re.I):
        s.add(WORWOOD_TRAVIS if m.group(1).lower() == "travis" else WORWOOD_SKIP)
    if not s and re.search(r"Worwood", header, re.I):
        # bare "Worwood" in header with no first name -> fall back by tenure dates
        if date < "2024-01-01":
            s = {WORWOOD_SKIP}
        elif date < "2026-01-01":
            s = {WORWOOD_SKIP, WORWOOD_TRAVIS}
        else:
            s = {WORWOOD_TRAVIS}
    return s


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories)
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"budget amendment|amend(?:ed|ing)? (?:the )?budget|budget adjustment|"
                 r"tentative budget|biennial budget|amended budget|final budget", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t):
        return "Grant-Funding"
    if re.search(r"\bappoint\b|appointment|ratify the hiring|hiring of|liaison|"
                 r"\bappointed\b|fill the (?:council )?vacancy|to the (?:planning|library|"
                 r"board)", t):
        return "Appointment"
    if re.search(r"\bplat\b|subdivision|rezone|zoning|zone change|zone map|annex|annexation|"
                 r"conditional use|land use|general plan|master plan|preliminary plat|"
                 r"final plat|amended plat|lot line", t):
        return "Land-Use/Zoning"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|notice of award|"
                 r"professional services|agreement with|services agreement|lease|"
                 r"sign the agreement|sign the contract|easement|authorize the mayor to sign|"
                 r"bid|proposal", t):
        return "Contract/Purchase"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing|open the (?:public )?hearing|close the (?:public )?hearing|"
                 r"continue the public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|arbor day", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed (?:session|meeting)|"
                 r"executive session|approve the consent|approve the agenda|"
                 r"approve the minutes|amend the agenda|table|postpone|continue|"
                 r"suspend the rules|ratify|business license|beer license", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
NAME = r"(?:[A-Z]\.?\s+)?[A-Z][A-Za-z.'’\-]+(?:\s+(?:[A-Z]\.?|[A-Z][A-Za-z.'’\-]+)){0,2}"
ROLE = (r"(?:Councilor|Council\s*Member|Councilmember|Director|Board\s*Member|"
        r"Agency\s*Member|Chair(?:man|woman|person)?|Vice[-\s]?Chair|"
        r"Mayor\s*Pro\s*Tem(?:pore)?)")

ANCHOR_RE = re.compile(
    rf"(?:{ROLE}\s+)?(?P<name>{NAME})\s+(?:moved\b|made\s+(?:a|the)\s+motion)", re.I)
SECOND_RE = re.compile(rf"(?:{ROLE}\s+)?(?P<name>{NAME})\s+seconded", re.I)

# Result resolution: a narrative outcome clause OR a "vote was as follows" block intro.
RESULT_RE = re.compile(
    r"[Tt]he\s+(?:motion|ordinance|resolution)\s+"
    r"(?P<verb>passed|carried|failed|died)\b(?P<tail>[^\n]*)"
    r"|(?P<asfollows>[Tt]he\s+vote\s+was\s+as\s+follows\s*:)",
    re.I)

BLOCK_INTRO_RE = re.compile(
    r"following\s+(?:roll\s*call\s+)?vote|with\s+the\s+following\s+vote|"
    r"breaking\s+the\s+following\s+tie\s+vote|vote\s+was\s+as\s+follows|"
    r"on\s+following\s+vote", re.I)

LABEL_RE = re.compile(
    r"^\s*(Yes|Yea|Ayes?|No|Nays?|Abstain(?:ing|ed)?|Absent|Excused|Recused?)"
    r"\s*:\s*(.*)$", re.I)
TABULAR_RE = re.compile(
    r"^\s*(?P<name>.+?)\s{2,}(?P<vote>Yes|Yea|Aye|No|Nay|Absent|Excused|"
    r"Abstain(?:ed)?|Recused?)\s*$", re.I)
RECUSE_RE = re.compile(
    r"\*?\s*(?:Councilor\s+|Council\s*Member\s+)?(?P<name>" + NAME +
    r")\s+recused\s+(?:him|her)self", re.I)
TIEBREAK_RE = re.compile(
    r"Mayor[^\n]*?broke\s+the\s+tie\s+with\s+a\s+[\"“'`]?(?P<dir>Yes|Yea|No|Nay)", re.I)

VOTE_BUCKET = {
    "yes": "aye", "yea": "aye", "aye": "aye", "ayes": "aye",
    "no": "nay", "nay": "nay", "nays": "nay",
    "abstain": "abstain", "abstaining": "abstain", "abstained": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}

# Inline named dissent in narrative tails: "X and Y opposed", "X, Y voted nay", etc.
MINORITY_RE = re.compile(
    r"(?P<names>[A-Z][A-Za-z.'’\-]+(?:\s+[A-Z][A-Za-z.'’\-]+){0,2}"
    r"(?:(?:\s*,\s*|\s*,?\s*and\s+)(?:Councilor\s+|Council\s*Member\s+)?"
    r"[A-Z][A-Za-z.'’\-]+(?:\s+[A-Z][A-Za-z.'’\-]+){0,2})*)\s+"
    r"(?:opposed|dissent(?:ed|ing)?|voted\s+(?:no|nay|against)|"
    r"in\s+opposition|voting\s+(?:no|nay|against))",
    re.I)
ABSENT_NAME_RE = re.compile(
    r"(?:Councilor\s+|Council\s*Member\s+)?(?P<name>" + NAME +
    r")\s+(?:was|were)\s+absent", re.I)
TALLY_RE = re.compile(r"(\d+)\s*(?:-|–|to)\s*(\d+)")


HEADING_RE = re.compile(r"^\s*[A-Z0-9][A-Z0-9 ,.'’&/\-()]{6,}:\s*$")


def _split_names(rest, worwoods):
    """Split a label's inline name list ('Councilors A, B and C') into canon names."""
    out = []
    rest = re.sub(r"^\s*Councilors?\s+", "", rest, flags=re.I)
    for part in re.split(r"\s*,\s*|\s+and\s+", rest):
        nm = normalize_name(part, worwoods)
        if nm and nm not in out:
            out.append(nm)
    return out


def _is_name_continuation(s, worwoods):
    if len(s) > 45:
        return False
    if LABEL_RE.match(s) or TABULAR_RE.match(s):
        return False
    toks = s.split()
    if len(toks) > 4:
        return False
    if re.search(r"\b(motion|moved|second|seconded|approve|adopt|carried|passed|failed|"
                 r"vote|council|meeting|the|to|that|broke|tie)\b", s, re.I):
        return False
    return normalize_name(s, worwoods) is not None


def parse_block(lines, start_idx, worwoods, mayor):
    """Parse a roll-call block beginning at line index start_idx.

    Returns (buckets, mayor_tiebreak_dir, closing_verb, end_idx).
    """
    buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
    cur = None
    tiebreak = None
    closing_verb = None
    got = False
    blanks = 0
    j = start_idx
    n = len(lines)
    while j < n and j < start_idx + 30:
        ln = lines[j]
        s = ln.strip()
        if not s:
            blanks += 1
            if got and blanks >= 2:
                break
            j += 1
            continue
        blanks = 0

        tb = TIEBREAK_RE.search(s)
        if tb:
            tiebreak = "aye" if tb.group("dir").lower() in ("yes", "yea") else "nay"
            cv = re.search(r"motion\s+(carried|passed|failed)", s, re.I)
            if cv:
                closing_verb = cv.group(1).lower()
            got = True
            j += 1
            continue

        cv = re.match(r"(?:the\s+)?(?:motion|ordinance)\s+(carried|passed|failed)\b", s, re.I)
        if cv and got:
            closing_verb = cv.group(1).lower()
            j += 1
            break

        lab = LABEL_RE.match(ln)
        if lab:
            cur = VOTE_BUCKET.get(lab.group(1).lower())
            rest = lab.group(2).strip()
            if rest and cur:
                for nm in _split_names(rest, worwoods):
                    if nm not in buckets[cur]:
                        buckets[cur].append(nm)
            got = True
            j += 1
            continue

        tab = TABULAR_RE.match(ln)
        if tab:
            nm = normalize_name(tab.group("name"), worwoods)
            bkt = VOTE_BUCKET.get(tab.group("vote").lower())
            if nm and bkt and nm not in buckets[bkt]:
                buckets[bkt].append(nm)
                got = True
                cur = None
                j += 1
                continue

        rec = RECUSE_RE.search(s)
        if rec:
            nm = normalize_name(rec.group("name"), worwoods)
            if nm and nm not in buckets["recuse"]:
                buckets["recuse"].append(nm)
            got = True
            j += 1
            continue

        if cur and _is_name_continuation(s, worwoods):
            nm = normalize_name(s, worwoods)
            if nm and nm not in buckets[cur]:
                buckets[cur].append(nm)
            j += 1
            continue

        if got:
            break
        if HEADING_RE.match(ln):
            break
        if j - start_idx > 5:
            break
        j += 1

    # Mayor tie-break: add the (non-voting) Mayor to the broken-tie side.
    if tiebreak:
        if mayor not in buckets[tiebreak]:
            buckets[tiebreak].append(mayor)
    return buckets, tiebreak, closing_verb, j


def _line_index_map(text):
    offs = [0]
    for line in text.split("\n"):
        offs.append(offs[-1] + len(line) + 1)
    return offs


def _pos_to_line(offs, pos):
    # binary-ish linear search (files are small)
    lo, hi = 0, len(offs) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if offs[mid] <= pos:
            lo = mid + 1
        else:
            hi = mid
    return max(0, lo - 1)


NOISE_RE = re.compile(
    r"^\s*(Page\s+\d+\s+of\s+\d+|Page\s+\d+|\d+\s*\|\s*Page|"
    r"# Nephi City .*|ATTEST:.*|_{3,}.*)\s*$", re.I)


def parse_meeting(path, title, date):
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("\f", "\n")
    lines = [ln for ln in raw.split("\n") if not NOISE_RE.match(ln)]
    text = "\n".join(lines)

    # header / context region (stop at the guest list or the call to order)
    cut = len(text)
    for marker in (r"\bGuests?:", r"called the (?:meeting|regular|hearing|public)"):
        m = re.search(marker, text, re.I)
        if m:
            cut = min(cut, m.start())
    header = text[:max(cut, 400)]

    worwoods = detect_worwoods(header, date)
    mayor = mayor_for(date)

    # file-level body
    file_body = "Council"
    htop = text[:900].lower()
    if "community reinvestment agency" in htop or "community reinvestment agency" in title.lower():
        file_body = "CRA"
    elif "redevelopment agency" in htop or "redevelopment agency" in title.lower():
        file_body = "RDA"
    elif "municipal building authority" in htop or "municipal building authority" in title.lower():
        file_body = "MBA"

    # in-meeting convene-as-agency blocks (rare): switch body between markers
    body_at = {}
    cur_body = file_body
    convene_re = re.compile(
        r"(?:convened?|recess(?:ed)?|reconvened?)\s+(?:into|as|and convene)?[^\n]*?"
        r"(redevelopment agency|community reinvestment agency|municipal building authority)",
        re.I)
    back_re = re.compile(
        r"reconvened?\s+(?:the\s+)?(?:regular\s+)?(?:city\s+)?council|"
        r"reconvened?\s+(?:into|as)\s+(?:the\s+)?(?:regular\s+)?council", re.I)
    for idx, ln in enumerate(lines):
        low = ln.lower()
        if file_body == "Council":
            mb = convene_re.search(low)
            if mb and "executive" not in low:
                token = mb.group(1)
                cur_body = ("RDA" if "redevelopment" in token else
                            "CRA" if "reinvestment" in token else "MBA")
            elif back_re.search(low):
                cur_body = "Council"
        body_at[idx] = cur_body

    offs = _line_index_map(text)
    anchors = list(ANCHOR_RE.finditer(text))
    votes = []

    for ai, am in enumerate(anchors):
        mover = normalize_name(am.group("name"), worwoods)
        if mover is None:
            continue
        win_start = am.end()
        win_end = anchors[ai + 1].start() if ai + 1 < len(anchors) else len(text)
        # cap window so a motion with no result doesn't swallow the rest of the file
        win_end = min(win_end, win_start + 4000)
        window = text[win_start:win_end]

        rm = RESULT_RE.search(window)
        if not rm:
            continue  # no recorded result -> not a completed vote

        result_abs = win_start + rm.start()
        # seconder: first "seconded" before the result
        seconder = None
        sm = SECOND_RE.search(window[:rm.start()])
        if sm:
            seconder = normalize_name(sm.group("name"), worwoods)

        # motion text: from after the verb up to the result, minus the seconder sentence
        motion_text = window[:rm.start()]
        if sm:
            motion_text = window[:sm.start()]
        motion_text = re.sub(r"^\s*(to|that|and)\s+", "", motion_text.strip(), flags=re.I)
        motion_text = re.sub(r"\s+", " ", motion_text).strip(" .;,")
        if not motion_text:
            motion_text = "(motion text not captured)"

        anchor_line = _pos_to_line(offs, win_start)
        body = body_at.get(anchor_line, file_body)
        # procedural "convene/recess into <agency>" motion itself is a council act
        if body in ("RDA", "CRA", "MBA") and file_body == "Council":
            if re.search(r"convene|recess|reconvene|adjourn", motion_text, re.I):
                body = "Council"

        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        names_recorded = False
        mayor_vote = False

        verb = (rm.group("verb") or "").lower()
        tail = rm.group("tail") or ""
        asfollows = rm.group("asfollows")

        is_block = bool(asfollows) or bool(BLOCK_INTRO_RE.search(tail))

        if is_block:
            block_line = _pos_to_line(offs, win_start + rm.end())
            buckets, tiebreak, closing_verb, _ = parse_block(
                lines, block_line + 1, worwoods, mayor)
            if not verb:
                verb = closing_verb or ("passed" if tiebreak == "aye" else
                                        "failed" if tiebreak == "nay" else "")
            outcome = "Pass" if verb in ("passed", "carried") else (
                "Fail" if verb in ("failed", "died") else "")
            if not outcome:
                outcome = "Pass" if len(buckets["aye"]) >= len(buckets["nay"]) else "Fail"
            # Mayor tie-break announced in the intro ("...breaking the following tie
            # vote:") with no separate "broke the tie" line: the Mayor breaks toward
            # the stated outcome.
            if tiebreak is None and re.search(r"tie\s+vote", tail, re.I):
                tiebreak = "aye" if outcome == "Pass" else "nay"
                if mayor not in buckets[tiebreak]:
                    buckets[tiebreak].append(mayor)
            named = sum(len(buckets[k]) for k in ("aye", "nay", "abstain", "recuse", "absent"))
            names_recorded = named > 0
            if mayor in buckets["aye"] or mayor in buckets["nay"]:
                mayor_vote = True
            if names_recorded:
                result_str = f"{len(buckets['aye'])}-{len(buckets['nay'])} {outcome}".strip()
                if tiebreak:
                    result_str += " (Mayor tie-break)"
                if buckets["recuse"]:
                    result_str += f" ({len(buckets['recuse'])} recused)"
            else:
                result_str = outcome or "Recorded vote"
        else:
            outcome = "Pass" if verb in ("passed", "carried") else "Fail"
            low_tail = tail.lower()
            scan = tail
            # extend scan to the rest of the sentence / next line for dissent + absentees
            nxt = window[rm.end():rm.end() + 240]
            scan_full = tail + " " + nxt

            if "unanimous" in low_tail:
                mt = TALLY_RE.search(tail)
                result_str = (f"{mt.group(1)}-{mt.group(2)} {outcome} (unanimous)"
                              if mt else f"{outcome} (unanimous)")
            else:
                # named dissent?
                mm = MINORITY_RE.search(scan_full)
                if mm:
                    for nm in _split_names(mm.group("names"), worwoods):
                        if nm not in buckets["nay"]:
                            buckets["nay"].append(nm)
                mt = TALLY_RE.search(tail)
                if mt:
                    n1, n2 = int(mt.group(1)), int(mt.group(2))
                    k_nay = len(buckets["nay"])
                    if k_nay and k_nay in (n1, n2):
                        nay_ct = k_nay
                        aye_ct = n2 if k_nay == n1 else n1
                    elif outcome == "Fail":
                        aye_ct, nay_ct = min(n1, n2), max(n1, n2)
                    else:
                        aye_ct, nay_ct = max(n1, n2), min(n1, n2)
                    result_str = f"{aye_ct}-{nay_ct} {outcome}"
                else:
                    result_str = outcome
                if buckets["nay"]:
                    names_recorded = True  # explicit dissenters named
                    result_str += f" ({', '.join(buckets['nay'])} opposed)"

            # absentees noted (kept in result string; not a names_recorded roster)
            absents = []
            for amt in ABSENT_NAME_RE.finditer(scan_full):
                nm = normalize_name(amt.group("name"), worwoods)
                if nm and nm not in absents and nm != mayor:
                    absents.append(nm)
            if absents:
                result_str += f" ({', '.join(absents)} absent)"

        votes.append({
            "body": body,
            "motion": motion_text[:600],
            "motion_type": classify_motion(motion_text),
            "result": result_str,
            "mover": mover,
            "seconder": seconder,
            "aye": buckets["aye"],
            "nay": buckets["nay"],
            "abstain": buckets["abstain"],
            "absent": buckets["absent"],
            "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "mayor_vote": mayor_vote,
        })

    return votes


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    rows = list(csv.DictReader(INDEX.open()))
    processed = 0
    for r in rows:
        rel = r["path"]
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"MISSING: {rel}", file=sys.stderr)
            continue
        date, year = r["date"], r["year"]
        week = Path(rel).parent.name
        out_dir = VOTES_DIR / year / week
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = Path(rel).stem
        out_json = out_dir / f"{slug}.json"

        votes = parse_meeting(path, r["title"], date)
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        payload = {
            "date": date,
            "year": int(year),
            "title": r["title"],
            "source": rel,
            "votes": votes,
        }
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON")
    build_all_votes()


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n_rows = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                if v.get("names_recorded"):
                    for key, label in (("aye", "Aye"), ("nay", "Nay"),
                                       ("abstain", "Abstain"), ("absent", "Absent"),
                                       ("recuse", "Recuse")):
                        for member in v.get(key, []):
                            w.writerow(base + [member, label, data["source"]])
                            n_rows += 1
                            emitted = True
                if not emitted:
                    # narrative tally-only / unanimous -> single summary row
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")


if __name__ == "__main__":
    main()
