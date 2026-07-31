#!/usr/bin/env python3
"""
St. George, UT council vote extractor.

Reads the markdown minutes under meeting_minutes/minutes/<year>/<week>/<file>.md
(indexed by meeting_minutes/minutes_index.csv), parses the highly-regular
MOTION: / SECOND: / VOTE: roll-call blocks, and emits:

  - one JSON per meeting -> meeting_minutes/votes/<year>/<week>/<file>.json
  - a rebuilt long-format meeting_minutes/all_votes.csv
  - a validation report -> meeting_minutes/votes/_validation_report.txt

Design notes / heuristics live in meeting_minutes/CLAUDE.md.

NEVER invents who voted which way. If a VOTE: block has no per-member lines
(tally/outcome only) the member lists stay empty and names_recorded=False.
"""

import csv
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MINUTES_DIR = os.path.join(HERE, "minutes")
VOTES_DIR = os.path.join(HERE, "votes")
INDEX_CSV = os.path.join(HERE, "minutes_index.csv")
ALL_VOTES_CSV = os.path.join(HERE, "all_votes.csv")
VALIDATION_REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------
# St. George = Mayor + 5 at-large councilmembers. Surnames appearing in roll
# calls 2022-2026 (cross-checked vs election winners in
# election_results/st_george_results_by_candidate.csv):
#   Hughes, McArthur, Larkin, Larsen, Tanner, Kemp, Anderson  (+ Mayor Randall)
# We normalize on surname -> canonical "First Last".
SURNAME_TO_FULL = {
    "hughes": "Jimmie Hughes",
    "mcarthur": "Gregg McArthur",
    "larkin": "Dannielle Larkin",
    "larsen": "Natalie Larsen",
    "tanner": "Michelle Tanner",
    "kemp": "Steve Kemp",
    "anderson": "Austin Anderson",
    "randall": "Michele Randall",  # Mayor 2021-2025
    # Earlier roster (2020-2021), confirmed vs election winners:
    "pike": "Jon Pike",            # Mayor 2014-2021 (before Randall)
    "curtis": "Vardell Curtis",
    "smethurst": "Bryan Smethurst",
    "arial": "Bette Arial",
    # OCR / typo guards
    "lasen": "Natalie Larsen",   # seen: "Councilmember Lasen to adjourn"
    "larson": "Natalie Larsen",
}

# ---------------------------------------------------------------------------
# Body tagging
# ---------------------------------------------------------------------------
# `body` values emitted into all_votes.csv (after `title`):
#   Council            St. George City Council (the default / the core 163)
#   RDA                Neighborhood Redevelopment Agency  (council sitting AS the board)
#   CRA                Community Reinvestment Agency       (post-2016 successor; none seen yet)
#   MBA                Municipal Building Authority        (none seen yet)
#   PlanningCommission Planning Commission   (SEPARATE body — different people)
#   ArtsCommission     Arts Commission       (SEPARATE body — different people)
#   Canvass            Board of Canvassers (the council canvassing an election)
BODY_COUNCIL = "Council"
BODY_RDA = "RDA"
BODY_CRA = "CRA"
BODY_MBA = "MBA"
BODY_PLANNING = "PlanningCommission"
BODY_ARTS = "ArtsCommission"
BODY_CANVASS = "Canvass"

# Bodies whose members are the SAME people as the council sitting in another
# capacity -> surnames map to the canonical council member name.
COUNCIL_AS_BOARD = {BODY_COUNCIL, BODY_RDA, BODY_CRA, BODY_MBA, BODY_CANVASS}

# Role prefix (lowercased, normalized whitespace) -> which body that role
# implies for the person voting under it.
def role_to_body(role):
    r = re.sub(r"\s+", " ", (role or "").strip().lower())
    if r in ("councilmember", "council member", "mayor", "mayor pro tem"):
        return BODY_COUNCIL
    if r in ("agency member", "board member"):
        return BODY_RDA  # RDA is the only board that has appeared in St. George
    if r == "planning commission member":
        return BODY_PLANNING
    if r in ("commission member", "commissioner"):
        return BODY_ARTS  # bare "Commission Member" = Arts (only such body seen)
    if r in ("chairwoman", "chairman", "chairperson", "chair", "vice chair"):
        return None  # ambiguous on its own (RDA chair vs commission chair) -> infer from meeting
    return None


# Vote-value normalization
VOTE_AYE = "Aye"
VOTE_NAY = "Nay"
VOTE_ABSTAIN = "Abstain"
VOTE_ABSENT = "Absent"
VOTE_RECUSE = "Recuse"

# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories)
# ---------------------------------------------------------------------------
MOTION_TYPES = {
    "Ordinance", "Resolution", "Budget Amendment", "Grant-Funding",
    "Interlocal", "Appointment", "Public Hearing Action",
    "Procedural/Administrative", "Ceremonial", "Contract/Purchase",
    "Land-Use/Zoning", "Other",
}


def classify_motion(section_header, motion_text):
    """Infer a motion_type from the agenda section header + motion text.

    Order matters: the most specific / highest-signal categories win.
    `section_header` is the ALLCAPS agenda heading the motion sits under
    (may be ""), `motion_text` is the verbatim motion sentence.
    """
    h = (section_header or "").lower()
    m = (motion_text or "").lower()
    blob = h + " || " + m

    def has(*words):
        return any(w in blob for w in words)

    # Procedural housekeeping first (adjourn / consent / minutes / open-close)
    if re.search(r"\b(adjourn|recess|reconvene)\b", m):
        return "Procedural/Administrative"
    if "consent calendar" in m or "consent calendar" in h:
        return "Procedural/Administrative"
    if has("approval of the minutes", "approve the minutes", "minutes of the"):
        return "Procedural/Administrative"
    if re.search(r"\b(open|close|continue|table|postpone|reopen)\b.*public hearing", m) \
            or re.search(r"public hearing.*\b(open|close|continue)\b", m):
        return "Public Hearing Action"

    # Land use / zoning (very common in St. George)
    if has("zone change", "zoning", "rezone", "ordinance amending the city zoning map",
           "general plan", "subdivision", "preliminary plat", "final plat", "plat",
           "hillside development", "conditional use", "annexation", "petition for annexation",
           "planned development", "lot split", "development agreement", "right-of-way",
           "vacate", "easement", "land use", "zone map", "site plan"):
        return "Land-Use/Zoning"

    # Budget amendment
    if has("budget amendment", "amend the budget", "amending the budget",
           "final budget", "tentative budget", "adopt the budget", "budget for fiscal"):
        return "Budget Amendment"

    # Grants
    if has("grant", "rap tax", "cdbg", "award funds"):
        return "Grant-Funding"

    # Interlocal / agreements between governments
    if has("interlocal", "inter-local", "intergovernmental"):
        return "Interlocal"

    # Appointments
    if has("appoint", "appointment", "reappoint", "designation and appointment",
           "representatives to", "board and commission", "boards and commissions",
           "swearing in", "fill the vacancy", "vacant city council seat"):
        return "Appointment"

    # Contract / purchase / bid / agreement (non-interlocal)
    if has("contract", "purchase", "bid", "agreement", "professional services",
           "task order", "change order", "amendment to the agreement", "lease",
           "memorandum of understanding", "mou", "license agreement"):
        return "Contract/Purchase"

    # Ceremonial / proclamation
    if has("proclamation", "recognize", "recognition", "honoring", "award of",
           "key to the city", "ceremonial"):
        return "Ceremonial"

    # Generic ordinance vs resolution by the explicit instrument named.
    # (Checked late so land-use ordinances are tagged Land-Use/Zoning above.)
    if re.search(r"\bordinance\b", blob):
        return "Ordinance"
    if re.search(r"\bresolution\b", blob):
        return "Resolution"

    return "Other"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
# Header style: ALLCAPS line ending in ":" (e.g. "ZONE CHANGE/ORDINANCE:")
SECTION_RE = re.compile(r"^\s*([A-Z][A-Z0-9 ,/&.'()\"-]{4,})\s*:\s*$")

# Role prefixes that introduce a voting person. Captured (group 1) so the
# caller can tell which BODY the person voted as:
#   - council roles (Councilmember / Mayor / Mayor Pro Tem)  -> Council
#   - board roles   (Agency Member / Chair[wo]man / Board Member / Director,
#                    "Trustee") -> RDA/CRA/MBA (the council sitting AS the board;
#                    SAME people -> surname maps to the council member name)
#   - "Planning Commission Member" -> PlanningCommission (SEPARATE people)
#   - "Commission Member" (bare)   -> a commission (Arts, etc.) — SEPARATE people
ROLE_PREFIX = (
    r"(?:Planning\s+Commission\s+Member|Commission\s+Member|Commissioner|"
    r"Agency\s+Member|Board\s+Member|"
    r"Chairwoman|Chairman|Chairperson|Chair|Vice\s+Chair|"
    r"Mayor\s+Pro\s+Tem|Councilmember|Council\s+Member|Mayor)"
)

# A roll-call vote line: "Councilmember Hughes – aye" (en-dash or hyphen),
# also "Mayor Randall – aye", "Mayor Pro Tem Larkin – aye",
# "Agency Member Hughes – aye", "Chairwoman Randall – aye",
# "Commission Member Wilson – aye", and recusal phrasing
# "Councilmember McArthur – recused himself".
# group 1 = role prefix, group 2 = surname, group 3 = vote value.
VOTE_LINE_RE = re.compile(
    r"^\s*(" + ROLE_PREFIX + r")\s+"
    r"([A-Z][A-Za-z'.-]+)\s*[–—-]\s*(.+?)\s*$"
)

# Mover: "A motion was made by Councilmember Larkin to ..."
# Guard against the OCR transposition "Councilmember to Larkin".
# group 1 = role prefix, group 2 = surname.
MOVER_RE = re.compile(
    r"motion was made by\s+(" + ROLE_PREFIX + r")\s+"
    r"(?:to\s+)?([A-Z][A-Za-z'.-]+)",
    re.IGNORECASE,
)
SECONDER_RE = re.compile(
    r"motion was seconded by\s+(" + ROLE_PREFIX + r")\s+"
    r"(?:to\s+)?([A-Z][A-Za-z'.-]+)",
    re.IGNORECASE,
)

# group 1 = role prefix, group 2 = full name.
PRESENT_NAME_RE = re.compile(
    r"^\s*(" + ROLE_PREFIX + r")\s+"
    r"([A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+)*?)\s*(?:[–—-].*)?$"
)

# Outcome lines that close a vote block.
OUTCOME_RE = re.compile(
    r"(vote was unanimous|motion carried|motion failed|motion passed|"
    r"motion did not carry|motion was denied|motion fail)", re.IGNORECASE
)

# Lines that are page-break noise inside a vote block.
NOISE_RE = re.compile(
    r"^\s*(St\. George City Council Minutes|Page [A-Za-z0-9]+|"
    r"[A-Z][a-z]+ \d{1,2}, \d{4})\s*$"
)


def normalize_name(raw, body=BODY_COUNCIL):
    """Surname or full name -> canonical 'First Last'.

    For council-as-board bodies (Council/RDA/CRA/MBA/Canvass) the people are the
    SAME councilmembers wearing a board hat, so surnames map to the canonical
    council member name (Hughes -> "Jimmie Hughes"). For genuinely-separate
    bodies (Planning Commission, Arts Commission) we must NOT pretend their
    members are councilmembers — their surnames stay as-is, title-cased.
    """
    if not raw:
        return raw
    raw = raw.strip().rstrip(".")
    if body in COUNCIL_AS_BOARD:
        surname = raw.split()[-1].lower()
        if surname in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[surname]
    # Separate body, or unknown council name -> title-case as-is
    return raw.title()


def classify_body_from_title(title):
    """Best-guess body for a whole meeting from its index `title`.

    Used as the default/fallback; the per-vote voter role can override it
    (e.g. a council-as-RDA block inside an RDA-titled meeting). Returns a body
    string. Joint Council/Commission meetings whose recorded *motions* are
    councilmember votes resolve to Council via the per-vote role anyway, so the
    title only needs to flag the single-body cases.
    """
    t = (title or "").lower()
    # Single dedicated commission meetings (different people)
    if "arts commission" in t:
        return BODY_ARTS
    if "planning commission" in t and "city council" not in t:
        return BODY_PLANNING
    if "canvass" in t:
        return BODY_CANVASS
    if "community reinvestment" in t or re.search(r"\bcra\b", t):
        return BODY_CRA
    if "municipal building authority" in t or re.search(r"\bmba\b", t):
        return BODY_MBA
    if "redevelopment" in t or re.search(r"\brda\b", t):
        return BODY_RDA
    return BODY_COUNCIL


def normalize_vote_value(raw):
    v = raw.strip().lower()
    if v.startswith("aye") or v in ("yes", "yea", "for"):
        return VOTE_AYE
    if v.startswith("nay") or v in ("no", "against"):
        return VOTE_NAY
    if "abstain" in v:
        return VOTE_ABSTAIN
    if "absent" in v or "excused" in v:
        return VOTE_ABSENT
    if "recus" in v:
        return VOTE_RECUSE
    return None  # unrecognized -> caller logs


def parse_present(lines):
    """Return list of canonical COUNCIL names appearing under a PRESENT: block.

    Only council roles (Councilmember/Mayor/Agency Member/Chair[wo]man — the
    council sitting as itself or as the RDA/Canvass board) feed the council
    roster. Planning/Arts commission members are a SEPARATE body and are NOT
    added to the council roster (we must not pretend they are councilmembers).
    """
    present = []
    in_present = False
    for ln in lines:
        s = ln.strip()
        if re.match(r"^PRESENT\s*:\s*$", s):
            in_present = True
            continue
        if in_present:
            if not s:
                # blank line may separate; keep going until a new section header
                continue
            if SECTION_RE.match(ln) and not PRESENT_NAME_RE.match(ln):
                break
            mm = PRESENT_NAME_RE.match(ln)
            if mm:
                role = mm.group(1)
                rbody = role_to_body(role)
                surname = mm.group(2).strip().rstrip(".").split()[-1].lower()
                # skip separate-body commission members
                if rbody in (BODY_PLANNING, BODY_ARTS):
                    continue
                # ambiguous "Chair" -> include only if a known council surname
                if rbody is None and surname not in SURNAME_TO_FULL:
                    continue
                present.append(normalize_name(mm.group(2), body=BODY_COUNCIL))
            else:
                # a non-name, non-blank line ends the present block
                low = s.lower()
                if not low.startswith(("mayor", "councilmember", "council member",
                                       "agency member", "chairwoman", "chairman",
                                       "board member", "chairperson", "chair",
                                       "commission member", "commissioner",
                                       "planning commission")):
                    break
                # commission line that didn't match name regex -> just skip it
                continue
    # dedupe preserving order
    seen = set()
    out = []
    for p in present:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def collapse(text):
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Line-number-gutter tolerance
# ---------------------------------------------------------------------------
# A handful of St. George born-digital minutes PDFs are printed with a
# left-margin LINE-NUMBER GUTTER: every physical line begins with a per-page
# line number (resetting each page) then whitespace, e.g.
#       25         MOTION:
#       34                Councilmember Hughes – aye
# which defeats the ^\s*MOTION:/VOTE: header + roll-call regexes and yields 0
# extracted motions. `_strip_line_number_gutter` detects that layout (a high
# fraction of body lines begin with a small SEQUENTIAL number) and, ONLY for
# such files, removes the gutter token, leaving the content intact. Non-gutter
# files are returned byte-identical, so their extraction is unchanged. Detected
# affected files (2022-08-25 RDA council; 2022-06-09 / 2024-04-09 / 2024-12-10
# PC) score frac 0.68-0.81; every non-gutter file scores 0.00 -> a wide margin.
GUTTER_LINE_RE = re.compile(r"^ ?(\d{1,3})\s{2,}(\S.*)$")
GUTTER_NUM_ONLY_RE = re.compile(r"^ ?\d{1,3}\s*$")

# Some council minutes (e.g. the 2022-01-03 swearing-in regular meeting, and the
# original 2020-21 PMN backfill before it was normalized) print the block header
# and its text on the SAME physical line, e.g.
#       MOTION:        A motion was made by Councilmember Hughes to appoint ...
#       SECOND:        The motion was seconded by Councilmember McArthur.
#       VOTE:          Mayor Randall called for a roll call vote, as follows:
# The standalone-header regexes (`^\s*MOTION\s*:\s*$`) then never fire, so the
# whole meeting extracts 0 motions. `_split_inline_headers` splits an inline
# header onto its own line (identical to the documented 2020-21 normalization),
# which only transforms lines that ACTUALLY carry an inline header -> files that
# already use standalone headers are returned byte-identical.
INLINE_HDR_RE = re.compile(r"^(\s*)(MOTION|SECOND|VOTE)\s*:\s+(\S.*)$")


def _split_inline_headers(raw_lines):
    out = []
    for l in raw_lines:
        m = INLINE_HDR_RE.match(l.rstrip("\n"))
        if m:
            out.append(f"{m.group(1)}{m.group(2)}:\n")
            out.append(f"{m.group(1)}     {m.group(3)}\n")
        else:
            out.append(l)
    return out


def _strip_line_number_gutter(raw_lines):
    body_idx = [k for k, l in enumerate(raw_lines)
                if l.strip() and not l.lstrip().startswith((">", "#", "---", "*"))]
    if len(body_idx) < 5:
        return raw_lines
    nums, hits = [], 0
    for k in body_idx:
        m = GUTTER_LINE_RE.match(raw_lines[k].rstrip("\n"))
        if m:
            hits += 1
            nums.append(int(m.group(1)))
        else:
            nums.append(None)
    frac = hits / len(body_idx)
    seq, prev = 0, None
    for x in nums:
        if x is not None and prev is not None and x == prev + 1:
            seq += 1
        prev = x if x is not None else prev
    if not (frac > 0.5 and seq >= 10):
        return raw_lines
    out = []
    for l in raw_lines:
        s = l.rstrip("\n")
        m = GUTTER_LINE_RE.match(s)
        if m:
            out.append(m.group(2) + "\n")
        elif GUTTER_NUM_ONLY_RE.match(s):
            out.append("\n")   # a lone gutter number (blank content line)
        else:
            out.append(l)      # frontmatter / already-clean line
    return out


def parse_meeting(path, title=""):
    """Parse a single minutes .md file -> list of vote dicts + roster.

    `title` is the index meeting title; it seeds the default `body` for each
    motion, which the per-motion voter role can refine (e.g. an "Agency Member"
    roll call -> RDA even in a council-titled file).
    """
    with open(path, encoding="utf-8") as fh:
        raw_lines = fh.readlines()
    raw_lines = _strip_line_number_gutter(raw_lines)
    raw_lines = _split_inline_headers(raw_lines)

    roster = parse_present(raw_lines)
    default_body = classify_body_from_title(title)

    votes = []
    n = len(raw_lines)
    i = 0
    current_section = ""
    motion_no = 0

    while i < n:
        line = raw_lines[i]
        sec = SECTION_RE.match(line)
        if sec and "MOTION" not in sec.group(1) and "SECOND" not in sec.group(1) \
                and "VOTE" not in sec.group(1) and "PRESENT" not in sec.group(1):
            current_section = collapse(sec.group(1))

        # Detect a MOTION: block
        if re.match(r"^\s*MOTION\s*:\s*$", line):
            block = _consume_motion_block(raw_lines, i, default_body)
            if block is not None:
                motion_no += 1
                block["motion_no"] = motion_no
                block["section_header"] = current_section
                votes.append(block)
                i = block["_end"]
                continue
        i += 1

    # finalize
    out = []
    for b in votes:
        motion_text = b["motion"]
        mtype = classify_motion(b["section_header"], motion_text)
        result = b["result"]
        names_recorded = bool(
            b["aye"] or b["nay"] or b["abstain"] or b["absent"] or b["recuse"]
        )
        out.append(OrderedDict([
            ("motion_no", b["motion_no"]),
            ("section", b["section_header"]),
            ("body", b["body"]),
            ("motion", motion_text),
            ("motion_type", mtype),
            ("result", result),
            ("mover", b["mover"]),
            ("seconder", b["seconder"]),
            ("aye", b["aye"]),
            ("nay", b["nay"]),
            ("abstain", b["abstain"]),
            ("absent", b["absent"]),
            ("recuse", b["recuse"]),
            ("names_recorded", names_recorded),
        ]))
    return out, roster


def _consume_motion_block(lines, start, default_body=BODY_COUNCIL):
    """From a 'MOTION:' header index, gather motion text, second, vote lines,
    and the outcome. Returns a dict with raw member lists, or None if no usable
    vote followed (e.g. a withdrawn motion with no VOTE block before EOF/next
    section)."""
    n = len(lines)
    i = start + 1

    # 1) motion text: lines until SECOND:/VOTE:/blank-then-header. A nested
    # "MOTION:" header, a died-for-lack-of-second sentence, a withdrawal sentence,
    # or a prose outcome sentence ends THIS motion — previously loop (1) swallowed
    # every following sibling motion until the next literal SECOND:/VOTE:, so a
    # died/withdrawn motion inherited the next voted sibling's roll + result
    # (T3.1(i) 2026-07-12: 2022-08-18 truth-in-taxation sequence and kin).
    motion_parts = []
    died = withdrawn = superseded = False
    voice_result = ""
    while i < n:
        s = lines[i].strip()
        if re.match(r"^(SECOND|VOTE)\s*:\s*$", s):
            break
        if motion_parts and re.match(r"^\s*MOTION\s*:\s*$", s):
            superseded = True
            break
        if re.search(r"motion (?:died|dies|failed) for (?:the )?lack of a second|"
                     r"motion (?:died|failed) due to (?:the |a )?lack of a second", s, re.I):
            died = True
            i += 1
            break
        if re.search(r"previous motions? (?:was|were) withdrawn|motion was withdrawn", s, re.I):
            withdrawn = True
            i += 1
            break
        if motion_parts and OUTCOME_RE.search(s) and not re.match(r"^Link to ", s):
            # a prose (voice-vote) outcome with no VOTE: block
            voice_result = collapse(s)
            i += 1
            break
        if SECTION_RE.match(lines[i]) and not motion_parts:
            # malformed; stop
            break
        if NOISE_RE.match(lines[i]):
            i += 1
            continue
        if s:
            # strip "Link to ..." video pointer lines inside motion text
            if not re.match(r"^Link to ", s) and not re.match(r"^Agenda Packet", s):
                motion_parts.append(s)
        i += 1
    motion_text = collapse(" ".join(motion_parts))
    # mover/seconder captured raw (role, surname); normalized once body is known
    mover_raw = None  # (role, surname)
    mm = MOVER_RE.search(motion_text)
    if mm:
        mover_raw = (mm.group(1), mm.group(2))

    if died or withdrawn or superseded or voice_result:
        # a motion with no roll-call block of its own: died / withdrawn /
        # superseded by the next MOTION: / resolved by a prose voice-vote sentence
        if died:
            result_str = "Died (no second)"
        elif withdrawn:
            result_str = "Withdrawn (no vote)"
        elif voice_result:
            result_str = voice_result
        else:
            result_str = "No vote recorded (superseded)"
        return {
            "body": default_body,
            "motion": motion_text,
            "mover": normalize_name(mover_raw[1], body=default_body) if mover_raw else "",
            "seconder": "",
            "result": result_str,
            "outcome_verbatim": result_str,
            "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": [],
            "_end": i,
        }

    seconder_raw = None
    # 2) SECOND: block
    while i < n and not re.match(r"^\s*VOTE\s*:\s*$", lines[i]):
        s = lines[i].strip()
        if re.match(r"^\s*SECOND\s*:\s*$", lines[i]):
            i += 1
            continue
        sm = SECONDER_RE.search(s)
        if sm:
            seconder_raw = (sm.group(1), sm.group(2))
        # also catch recusal between second and vote (no action needed for text)
        if re.match(r"^(MOTION)\s*:\s*$", lines[i]):
            # next motion began without a VOTE -> abort this block
            break
        i += 1

    # raw vote tuples: (role, surname, normalized_value)
    raw_votes = []
    result = ""

    if i < n and re.match(r"^\s*VOTE\s*:\s*$", lines[i]):
        i += 1
        # 3) VOTE: block -> per-member lines until outcome line / next section
        while i < n:
            line = lines[i]
            s = line.strip()
            if not s:
                i += 1
                continue
            if NOISE_RE.match(line):
                i += 1
                continue
            om = OUTCOME_RE.search(s)
            vm = VOTE_LINE_RE.match(line)
            if vm:
                val = normalize_vote_value(vm.group(3))
                if val is not None:
                    raw_votes.append((vm.group(1), vm.group(2), val))
                # unrecognized vote value -> ignore line value but keep going
                i += 1
                continue
            if om:
                result = collapse(s)
                i += 1
                break
            # "called for a vote/roll call vote, as follows:" preamble
            if re.search(r"called for a (roll call )?vote", s, re.IGNORECASE):
                i += 1
                continue
            # a new section header or MOTION ends the vote block
            if SECTION_RE.match(line) or re.match(r"^\s*MOTION\s*:\s*$", line):
                break
            i += 1
    else:
        # no VOTE block found
        return None

    # ---- determine the BODY of this motion from the dominant voter role ----
    # The roll-call roles are the most reliable signal (an "Agency Member" block
    # is RDA even inside a council-titled file; a "Commission Member" block is a
    # separate commission). Fall back to the meeting-level default for ambiguous
    # roles (e.g. "Chair") or when no roll-call names were recorded.
    role_bodies = [role_to_body(r) for (r, _s, _v) in raw_votes]
    decided = [b for b in role_bodies if b is not None]
    if decided:
        # majority vote of decided roles
        body = max(set(decided), key=decided.count)
    else:
        body = default_body
    # A dedicated council-as-board meeting (Canvass/RDA/CRA/MBA) often addresses
    # its members as "Councilmember" in the roll call. The people are identical,
    # so when the role says Council but the meeting itself is a council-as-board
    # session, prefer the meeting's board identity (Council -> Canvass/RDA/...).
    if body == BODY_COUNCIL and default_body in COUNCIL_AS_BOARD \
            and default_body != BODY_COUNCIL:
        body = default_body

    # ---- now normalize names under the resolved body ----
    def nm(surname):
        return normalize_name(surname, body=body)

    aye, nay, abstain, absent, recuse = [], [], [], [], []
    for (_role, surname, val) in raw_votes:
        name = nm(surname)
        if val == VOTE_AYE:
            aye.append(name)
        elif val == VOTE_NAY:
            nay.append(name)
        elif val == VOTE_ABSTAIN:
            abstain.append(name)
        elif val == VOTE_ABSENT:
            absent.append(name)
        elif val == VOTE_RECUSE:
            recuse.append(name)

    mover = nm(mover_raw[1]) if mover_raw else ""
    seconder = nm(seconder_raw[1]) if seconder_raw else ""

    # build a tally result string when members are named, else keep outcome verbatim
    named = aye or nay or abstain or absent or recuse
    if named:
        a, ny = len(aye), len(nay)
        passed = "Pass"
        rl = result.lower()
        if "fail" in rl or "denied" in rl or "did not carry" in rl:
            passed = "Fail"
        tally = f"{a}-{ny}"
        result_str = f"{tally} {passed}"
        if result:
            result_str += f" ({result})"
    else:
        result_str = result or "(no outcome recorded)"

    return {
        "body": body,
        "motion": motion_text,
        "mover": mover,
        "seconder": seconder,
        "result": result_str,
        "outcome_verbatim": result,
        "aye": aye, "nay": nay, "abstain": abstain,
        "absent": absent, "recuse": recuse,
        "_end": i,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def load_index():
    rows = []
    with open(INDEX_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r.get("date") or r["date"] == "date":
                continue
            rows.append(r)
    return rows


def votes_json_path(row):
    # mirror minutes path: minutes/<year>/<week>/<file>.md -> votes/.../<file>.json
    rel = row["path"]  # meeting_minutes/minutes/<year>/<week>/<file>.md
    rel = rel.replace("meeting_minutes/minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def main():
    rows = load_index()
    validation_lines = []
    all_rows = []
    stats = {
        "meetings_processed": 0,
        "motions_extracted": 0,
        "member_vote_rows": 0,
        "named_rollcall_motions": 0,
        "tally_only_motions": 0,
        "contested_motions": 0,
        "validation_mismatches": 0,
        "unparsed_meetings": [],
    }
    roster_by_year = {}
    by_body_rows = {}        # member-vote rows per body
    by_body_motions = {}     # motions per body
    body_members = {}        # body -> set of distinct member names

    for row in rows:
        md_path = os.path.join(REPO, row["path"])
        if not os.path.exists(md_path):
            stats["unparsed_meetings"].append(row["path"] + " (missing file)")
            continue
        try:
            votes, roster = parse_meeting(md_path, row["title"])
        except Exception as e:  # noqa
            stats["unparsed_meetings"].append(f"{row['path']} (error: {e})")
            continue

        stats["meetings_processed"] += 1
        year = row["year"]
        if roster:
            roster_by_year.setdefault(year, set()).update(roster)

        if not votes:
            # No motion/vote blocks (e.g. work meeting that only discussed)
            validation_lines.append(f"INFO  {row['path']}: no MOTION/VOTE blocks parsed")

        meeting_json = OrderedDict([
            ("date", row["date"]),
            ("year", int(year)),
            ("title", row["title"]),
            ("source", row["path"]),
            ("roster_present", roster),
            ("votes", []),
        ])

        for v in votes:
            stats["motions_extracted"] += 1
            by_body_motions[v["body"]] = by_body_motions.get(v["body"], 0) + 1
            named = v["names_recorded"]
            if named:
                stats["named_rollcall_motions"] += 1
            else:
                stats["tally_only_motions"] += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                stats["contested_motions"] += 1

            jvote = OrderedDict([
                ("motion_no", v["motion_no"]),
                ("section", v["section"]),
                ("body", v["body"]),
                ("motion", v["motion"]),
                ("motion_type", v["motion_type"]),
                ("result", v["result"]),
                ("mover", v["mover"]),
                ("seconder", v["seconder"]),
                ("aye", v["aye"]),
                ("nay", v["nay"]),
                ("abstain", v["abstain"]),
                ("absent", v["absent"]),
                ("recuse", v["recuse"]),
                ("names_recorded", named),
            ])
            meeting_json["votes"].append(jvote)

            # validation: tally vs outcome
            _validate(row, v, validation_lines, stats)

            # emit all_votes rows (one per member; a motion with NO member rows —
            # died / withdrawn / superseded, T3.1(i) 2026-07-12 — gets the standard
            # single placeholder row with blank member so it reaches the db)
            b = v["body"]
            emitted = False
            for vlist, vval in ((v["aye"], "Aye"), (v["nay"], "Nay"),
                                (v["abstain"], "Abstain"), (v["absent"], "Absent"),
                                (v["recuse"], "Recuse")):
                for member in vlist:
                    all_rows.append(_row(row, v, member, vval))
                    by_body_rows[b] = by_body_rows.get(b, 0) + 1
                    body_members.setdefault(b, set()).add(member)
                    emitted = True
            if not emitted:
                all_rows.append(_row(row, v, "", ""))

        # write per-meeting JSON
        out_path = votes_json_path(row)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(meeting_json, fh, indent=2, ensure_ascii=False)

    stats["member_vote_rows"] = len(all_rows)

    # rebuild all_votes.csv
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "year", "title", "body", "motion_no", "motion",
                    "motion_type", "result", "mover", "seconder",
                    "member", "vote", "source"])
        for r in all_rows:
            w.writerow(r)

    # validation report
    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(VALIDATION_REPORT, "w", encoding="utf-8") as fh:
        fh.write("St. George vote-extraction validation report\n")
        fh.write("=" * 60 + "\n")
        fh.write(f"meetings_processed: {stats['meetings_processed']}\n")
        fh.write(f"motions_extracted: {stats['motions_extracted']}\n")
        fh.write(f"named_rollcall_motions: {stats['named_rollcall_motions']}\n")
        fh.write(f"tally_only_motions: {stats['tally_only_motions']}\n")
        fh.write(f"contested_motions: {stats['contested_motions']}\n")
        fh.write(f"validation_mismatches: {stats['validation_mismatches']}\n")
        fh.write(f"member_vote_rows: {stats['member_vote_rows']}\n")
        fh.write("=" * 60 + "\n\n")
        for ln in validation_lines:
            fh.write(ln + "\n")

    # roster summary
    roster_years = {y: sorted(v) for y, v in sorted(roster_by_year.items())}
    stats["roster_years"] = roster_years
    stats["by_body_rows"] = dict(sorted(by_body_rows.items()))
    stats["by_body_motions"] = dict(sorted(by_body_motions.items()))
    stats["body_members"] = {b: sorted(m) for b, m in sorted(body_members.items())}

    print(json.dumps({k: (v if k != "unparsed_meetings" else v)
                      for k, v in stats.items()}, indent=2, default=str))
    return stats


def _row(meeting_row, v, member, vote_val):
    return [
        meeting_row["date"], meeting_row["year"], meeting_row["title"],
        v["body"], v["motion_no"], v["motion"], v["motion_type"], v["result"],
        v["mover"], v["seconder"], member, vote_val, meeting_row["path"],
    ]


def _validate(meeting_row, v, log, stats):
    """Cross-check the member tally against the verbatim outcome text."""
    outcome = (v["result"] or "").lower()
    a, ny = len(v["aye"]), len(v["nay"])
    ab, rc = len(v["abstain"]), len(v["recuse"])
    if not v["names_recorded"]:
        return
    # unanimous claim but a dissent recorded
    if "unanimous" in outcome and (ny > 0):
        stats["validation_mismatches"] += 1
        log.append(f"MISMATCH {meeting_row['path']} motion {v['motion_no']}: "
                   f"outcome says unanimous but {ny} nay recorded -> {v['result']}")
    # outcome says carried but more nays than ayes (excluding abstain/absent)
    if ("carried" in outcome or "passed" in outcome) and ny > a:
        stats["validation_mismatches"] += 1
        log.append(f"MISMATCH {meeting_row['path']} motion {v['motion_no']}: "
                   f"outcome says carried but nay({ny}) > aye({a})")
    if "failed" in outcome and a > ny:
        stats["validation_mismatches"] += 1
        log.append(f"MISMATCH {meeting_row['path']} motion {v['motion_no']}: "
                   f"outcome says failed but aye({a}) > nay({ny})")


if __name__ == "__main__":
    main()
