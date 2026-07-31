#!/usr/bin/env python3
"""
St. George, UT *Planning Commission* vote extractor.

Reads the markdown minutes indexed by planning_commission/minutes_index.csv,
parses the two roll-call block formats St. George PC minutes use, and emits:

  - one JSON per meeting -> planning_commission/votes/<year>/<week>/<file>.json
  - a rebuilt long-format planning_commission/all_votes.csv
    (13-col schema identical to the council extractor; body="PlanningCommission",
     title="Planning Commission" on every row)
  - a validation report -> planning_commission/votes/_validation_report.txt

Two source formats (auto-detected per motion block):

  (A) "AYES (n) / NAYS (m)" tally-with-names blocks  (most 2020-2023 PMN files,
      plus a few Revize files). Names are listed under each AYES/NAYS header:
          MOTION: Commissioner Brager made a motion to recommend approval ...
          SECOND: Commissioner Draper
          [ROLL CALL VOTE:]
          AYES (6)
              Chairman Nathan Fisher
              ...
          NAYS (0)
          Motion carries
      Empty placeholder blocks for postponed items
      ("MOTION: Commissioner" / "SECOND: Commissioner" / AYES (0) / NAYS (0))
      have no mover and no votes -> skipped (no real motion happened).

  (B) "VOTE:" per-member lines  (Revize 2024+):
          MOTION: A motion was made by Planning Commission Member X to recommend ...
          SECOND: ... seconded by Planning Commission Member Y.
          VOTE: ... called for a vote, as follows:
              Planning Commission Member X - aye
              ...
          The vote was unanimous the motion passed

NEVER invents who voted which way. A block with only a numeric tally and no
per-member names contributes a JSON record with names_recorded=False and ZERO
rows to all_votes.csv.

See planning_commission/CLAUDE.md for the recommendation-vs-final-action rule,
name normalization (incl. the Anderson / Draper surname collisions), and the
2020-21 fragmentation handling.

Usage:
  python3 planning_commission/extract_votes.py [--force]
    --force   re-write per-meeting JSON even if it already exists (resumable;
              all_votes.csv + roster.csv + report are ALWAYS rebuilt in full).
"""

import csv
import json
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
INDEX_CSV = os.path.join(HERE, "minutes_index.csv")
VOTES_DIR = os.path.join(HERE, "votes")
ALL_VOTES_CSV = os.path.join(HERE, "all_votes.csv")
ROSTER_CSV = os.path.join(HERE, "roster.csv")
VALIDATION_REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

BODY = "PlanningCommission"
TITLE = "Planning Commission"

VOTE_AYE = "Aye"
VOTE_NAY = "Nay"
VOTE_ABSTAIN = "Abstain"
VOTE_ABSENT = "Absent"
VOTE_RECUSE = "Recuse"

# ---------------------------------------------------------------------------
# Name normalization (Planning Commission roster)
# ---------------------------------------------------------------------------
# Unambiguous surname -> canonical "First Last" for the commissioners that have
# served 2020-2026 (reconstructed from PRESENT/EXCUSED attendee headers).
PC_SURNAME = {
    "fisher": "Nathan Fisher",
    "andrus": "Emily Andrus",
    "west": "Elise West",
    "chapman": "Lori Chapman",
    "kemp": "Steve Kemp",
    "casey": "Kelly Casey",
    "rogers": "Ben Rogers",
    "larsen": "Natalie Larsen",
    "curtis": "Vardell Curtis",
    "brager": "David Brager",
    "nelson": "Roger Nelson",
    "taysom": "Kelly Taysom",
}

# Full-name spelling variants -> canonical.
PC_FULLNAME_VARIANTS = {
    "terri draper": "Teri Draper",
    "teri draper": "Teri Draper",
    "ray draper": "Ray Draper",
    "b. anderson": "Brandon Anderson",
    "b anderson": "Brandon Anderson",
    "brandon anderson": "Brandon Anderson",
    "austin anderson": "Austin Anderson",
}

# Role tokens that prefix a person's name in attendee/roll-call lines.
# (Matched case-insensitively; the corpus mixes "Pro Tem"/"Pro tem", etc.)
ROLE_PREFIX = (
    r"(?:Planning\s+Commission\s+Member|Planning\s+Commission\s+Vice\s+Chair|"
    r"Planning\s+Commission\s+Chair|Commissioner|Chairwoman|Chairman|"
    r"Pro\s+Tem\s+Vice\s+Chair|Pro\s+Tem\s+Chair|Vice\s+Chair\s+Pro\s+Tem|"
    r"Chair\s+Pro\s+Tem|Pro\s+Tem|Vice\s+Chair|Chairperson|Chair)"
)

# Lenient role-prefix stripper for roll-call name lines (any case, any order of
# the common role words). Used so "Pro tem Chair Steve Kemp" -> "Steve Kemp".
ROLE_STRIP_RE = re.compile(
    r"^(?:\s*(?:planning\s+commission\s+|pro\s+tem\s+|vice\s+|acting\s+)?"
    r"(?:member|chair|chairman|chairwoman|chairperson|commissioner)\b\.?\s*)+",
    re.IGNORECASE,
)


def normalize_pc_name(role, name, year, andersons=None):
    """Resolve a roll-call/attendee name token to a canonical commissioner name.

    `role` is the (raw) role prefix that introduced the name (may be ""),
    `name` is everything after the role prefix, `year` is the meeting year (int),
    `andersons` is the set of canonical Anderson names on THIS meeting's roster
    (parsed from PRESENT/EXCUSED); it drives attendance-based disambiguation of
    the two surname collisions documented in CLAUDE.md:

      * Anderson  -> Austin Anderson (the seated PC Chair 2021-Jan-2026) vs
        Brandon Anderson ("B. Anderson" / Member from Dec-2023). Resolution
        (2026-07-19 — attendance-based, replacing the old year GUESS because
        BOTH serve 2024-2025 and the year alone can't tell them apart):
          - explicit first name ("Austin"/"Brandon"/"B.") wins outright;
          - role "Chair" (not Vice) -> Austin (the Chair throughout his tenure);
          - role "Member" -> Brandon when Brandon is on the meeting roster (he is
            the Member; Austin holds the Chair), else Austin if only Austin is
            rostered;
          - a BARE "Anderson" (no first name, no disambiguating role) resolves
            from attendance only when exactly ONE Anderson is rostered; when BOTH
            (or NEITHER) are rostered it ABSTAINS -> the printed token is left
            title-cased ("Anderson") rather than guessed.
      * Draper    -> Ray Draper (2020-2022) vs Teri Draper (2023+). They never
        serve as commissioners simultaneously, so split by year (unambiguous).
    """
    raw = (name or "").strip().rstrip(".,;")
    if not raw:
        return ""
    low = raw.lower()
    rl = re.sub(r"\s+", " ", (role or "").strip().lower())

    # Full "First Last" given outright (2020-23 AYES blocks list full names).
    if low in PC_FULLNAME_VARIANTS:
        return PC_FULLNAME_VARIANTS[low]

    tokens = raw.split()
    surname = tokens[-1].lower().rstrip(".,;")

    # --- Anderson collision (attendance-based) ---
    if surname == "anderson":
        # Non-surname name tokens can themselves carry role words when the mover
        # regex didn't split them off (e.g. "Commission Member Anderson"), so read
        # role signal + any explicit first name from BOTH `rl` and those tokens.
        nonsurname = [t.lower().rstrip(".,;") for t in tokens[:-1]]
        roleblob = (rl + " " + " ".join(nonsurname)).strip()
        if "brandon" in nonsurname or "b" in nonsurname:
            return "Brandon Anderson"
        if "austin" in nonsurname:
            return "Austin Anderson"
        chair = "chair" in roleblob and "vice" not in roleblob
        member = "member" in roleblob and "chair" not in roleblob
        has_a = bool(andersons) and "Austin Anderson" in andersons
        has_b = bool(andersons) and "Brandon Anderson" in andersons
        if chair:
            # "Chair Anderson" is Austin; abstain only in the (non-occurring)
            # case where Austin is provably NOT on this PC roster but Brandon is.
            if andersons is not None and has_b and not has_a:
                return raw.title()
            return "Austin Anderson"
        if member:
            if andersons is not None:
                if has_b:
                    return "Brandon Anderson"
                if has_a:
                    return "Austin Anderson"
                return raw.title()          # neither rostered -> abstain
            return "Brandon Anderson" if year >= 2024 else "Austin Anderson"
        # bare "Anderson": resolve only when exactly one is rostered, else abstain
        if andersons is not None:
            if has_a and not has_b:
                return "Austin Anderson"
            if has_b and not has_a:
                return "Brandon Anderson"
            return raw.title()              # both or neither -> ABSTAIN
        return "Austin Anderson" if year <= 2023 else raw.title()

    # --- Draper collision ---
    if surname == "draper":
        first = tokens[0].lower().rstrip(".") if len(tokens) > 1 else ""
        if first in ("ray", "r"):
            return "Ray Draper"
        if first in ("teri", "terri", "t"):
            return "Teri Draper"
        return "Ray Draper" if year <= 2022 else "Teri Draper"

    # Unambiguous surname-only.
    if len(tokens) == 1 and surname in PC_SURNAME:
        return PC_SURNAME[surname]

    # Full "First Last" we know by surname -> prefer canonical full name.
    if len(tokens) >= 2 and surname in PC_SURNAME:
        return PC_SURNAME[surname]

    # Otherwise title-case what we have (single unknown surname or full name).
    return raw.title()


# ---------------------------------------------------------------------------
# motion_type taxonomy (same fixed set as the council extractor)
# ---------------------------------------------------------------------------
def classify_motion(section_header, motion_text):
    h = (section_header or "").lower()
    m = (motion_text or "").lower()
    blob = h + " || " + m

    def has(*words):
        return any(w in blob for w in words)

    if re.search(r"\b(adjourn|recess|reconvene|dismiss)\b", m):
        return "Procedural/Administrative"
    if re.search(r"\bnominate\b", m) or re.search(r"make .* the (vice )?chair", m):
        return "Procedural/Administrative"
    if "consent" in m and ("calendar" in m or "agenda" in m):
        return "Procedural/Administrative"
    if has("approval of the minutes", "approve the minutes", "minutes of the",
           "meeting minutes", "minutes from", "minutes dated", "the minutes",
           "approve the agenda", "elect", "election of officers"):
        return "Procedural/Administrative"
    if re.search(r"\b(continue|table|postpone|tabled)\b", m) and not has("subdivision", "plat"):
        return "Procedural/Administrative"
    if re.search(r"\b(open|close|continue)\b.*public hearing", m) \
            or re.search(r"public hearing.*\b(open|close|continue)\b", m):
        return "Public Hearing Action"

    if has("zone change", "zoning", "rezone", "zoning map", "general plan",
           "subdivision", "preliminary plat", "final plat", "plat",
           "hillside", "conditional use", "cup", "annexation",
           "planned development", "pd amendment", "pda", "lot split",
           "development agreement", "right-of-way", "vacate", "easement",
           "land use", "site plan", "ridgeline", "setback", "sign ordinance",
           "off-premises sign", "master sign"):
        return "Land-Use/Zoning"

    if has("budget amendment", "amend the budget", "amending the budget",
           "final budget", "tentative budget", "adopt the budget"):
        return "Budget Amendment"
    if has("grant", "cdbg", "award funds"):
        return "Grant-Funding"
    if has("interlocal", "inter-local", "intergovernmental"):
        return "Interlocal"
    if has("appoint", "reappoint", "fill the vacancy"):
        return "Appointment"
    if has("contract", "purchase", "bid", "agreement", "professional services",
           "lease", "memorandum of understanding", "mou"):
        return "Contract/Purchase"
    if has("proclamation", "recognize", "recognition", "honoring"):
        return "Ceremonial"
    if re.search(r"\bordinance\b", blob):
        return "Ordinance"
    if re.search(r"\bresolution\b", blob):
        return "Resolution"
    # PC-docket fallback: a substantive recommendation/approval that cites an
    # agenda item or land-use-ish noun (the Planning Commission's docket is
    # overwhelmingly land use; the motion text often only says "Item 2A").
    if re.search(r"recommend|forward|approve|approval|denial", m) and \
            has("item ", "phase", " pod", "as presented", "as written",
                "preliminary", "amendment", "request", " lot", "acres",
                "development", "townhome", "subdivision", "plat"):
        return "Land-Use/Zoning"
    return "Other"


# ---------------------------------------------------------------------------
# result encoding: recommendation vs final action vs procedural
# ---------------------------------------------------------------------------
PROCEDURAL_RE = re.compile(
    r"\b(adjourn|recess|reconvene|minutes|approve the agenda|elect|nominate|"
    r"election of officers|continue this item|continue the item|"
    r"to continue|to table|tabl|postpone|set the)\b",
    re.IGNORECASE,
)


def encode_result(motion_text, declared_ayes, declared_nays, passed):
    """Build the `result` string per the PC encoding contract (CLAUDE.md).

    DB keys: substring "recommend"/"forward" -> pc_recommendation (else
    pc_final_action); "positive"/"negative" -> direction.
    """
    m = (motion_text or "").lower()
    tally = f"{declared_ayes}:{declared_nays}"
    suffix = "" if passed else " (failed)"

    is_recommendation = bool(re.search(r"recommend|forward", m))
    if is_recommendation:
        # Negative = the motion's intent is denial. Key off explicit denial
        # phrasing only -- NOT a bare "negative", which appears in descriptive
        # text like "mitigated any negative effects".
        negative = bool(
            re.search(r"\b(denial|deny|denied)\b|negative recommendation|do not approve", m)
        ) and not re.search(r"without recommendation", m)
        direction = "Negative" if negative else "Positive"
        return f"{direction} recommendation {tally}{suffix}"

    # procedural housekeeping
    if PROCEDURAL_RE.search(m):
        word = "Pass" if passed else "Fail"
        return f"{tally} {word}"

    # final action (approve/deny CUP, site plan, hillside, subdivision, etc.)
    denied = bool(re.search(r"\b(deny|denial|denied)\b", m))
    if denied:
        action = "Denied" if passed else "Approved"  # a failed denial leaves it approved-ish
        # be explicit: failed motion -> mark failed, keep the verb of the motion
        if not passed:
            return f"{tally} Denied (Final Action) (failed)"
        return f"{tally} Denied (Final Action)"
    # default: an approval motion
    if not passed:
        return f"{tally} Approved (Final Action) (failed)"
    return f"{tally} Approved (Final Action)"


# ---------------------------------------------------------------------------
# Parsing primitives
# ---------------------------------------------------------------------------
SECTION_RE = re.compile(r"^\s*([A-Z][A-Z0-9 ,/&.'()\"#-]{4,})\s*:\s*$")

MOTION_HDR_RE = re.compile(r"^\s*MOTION\s*:\s*(.*)$")
SECOND_HDR_RE = re.compile(r"^\s*SECOND\s*:\s*(.*)$")
VOTE_HDR_RE = re.compile(r"^\s*VOTE\s*:\s*(.*)$")
ROLLCALL_HDR_RE = re.compile(r"^\s*ROLL\s*CALL\s*VOTE\s*:\s*(.*)$", re.IGNORECASE)
TALLY_HDR_RE = re.compile(
    r"^\s*(AYES|NAYS|NOES|ABSTAIN(?:ED)?|ABSENT|RECUSED?|EXCUSED)\s*\(\s*(\d+)\s*\)\s*$",
    re.IGNORECASE,
)

# Mover phrasings:
#   "A motion was made by <role> <name> to ..."
#   "<role> <name> made a motion to ..."
MOVER_RE_A = re.compile(
    r"motion was made by\s+(" + ROLE_PREFIX + r")?\s*([A-Z][A-Za-z'.\- ]+?)\s+to\b",
    re.IGNORECASE,
)
MOVER_RE_B = re.compile(
    r"^(?:\s*)(" + ROLE_PREFIX + r")?\s*([A-Z][A-Za-z'.\- ]+?)\s+made a motion\b",
    re.IGNORECASE,
)
SECONDED_BY_RE = re.compile(
    r"seconded by\s+(" + ROLE_PREFIX + r")?\s*([A-Z][A-Za-z'.\- ]+?)[\.\s]*$",
    re.IGNORECASE,
)
SECOND_NAME_RE = re.compile(
    r"^(" + ROLE_PREFIX + r")?\s*([A-Z][A-Za-z'.\- ]+?)\s*$"
)

# A VOTE: per-member line: "Planning Commission Member Fisher - aye".
# The role prefix is a RUN of role tokens (same token class as ROLE_STRIP_RE),
# not the fixed ROLE_PREFIX alternation: the clerk mixes nonstandard multi-word
# titles ("Planning Commission Commissioner Chapman – aye", 2025-02-25 m1/m2)
# and a single unmatched line used to hard-stop the block, silently dropping
# every roll line after it.
ROLE_RUN = (
    r"(?:(?:Planning\s+Commission\s+|Pro\s+Tem\s+|Vice\s+|Acting\s+)*"
    r"(?:Member|Chair(?:man|woman|person)?|Commissioner)\b\.?\s+)+"
)
VOTE_LINE_RE = re.compile(
    r"^\s*(" + ROLE_RUN + r")([A-Z][A-Za-z'.\-]+(?:\s+[A-Z][A-Za-z'.\-]+)?)\s*[–—-]+\s*(.+?)\s*$",
    re.IGNORECASE,
)

# An attendee/name line (under AYES/NAYS or PRESENT) with a role prefix.
NAME_LINE_RE = re.compile(
    r"^\s*(" + ROLE_PREFIX + r")\s+([A-Z][A-Za-z'.\-]+(?:\s+[A-Z][A-Za-z'.\-]+){0,2})\s*$",
    re.IGNORECASE,
)

# A bare person name (after role tokens are stripped): 1-4 capitalized tokens,
# no digits, no vote dash. Used to capture roll-call names robustly.
BARE_NAME_RE = re.compile(r"^[A-Z][A-Za-z'.\-]*(?:\s+[A-Z][A-Za-z'.\-]+){0,3}$")


def ayes_name(line, year, andersons=None):
    """Extract a canonical commissioner name from a roll-call name line under an
    AYES/NAYS/ABSTAIN bucket, or None if the line isn't a person name."""
    s = line.strip().rstrip(".,;")
    if not s or NOISE_RE.match(line):
        return None
    m = ROLE_STRIP_RE.match(s)
    role = m.group(0).strip() if m else ""
    stripped = (s[m.end():] if m else s).strip().rstrip(".,;")
    if not stripped or not BARE_NAME_RE.match(stripped):
        return None
    # Voter names are Title Case; ALLCAPS lines are slide/section titles
    # (e.g. "CONFLICTS OF", "INTEREST", "TOPICS"), never a person -> reject.
    if stripped.upper() == stripped:
        return None
    return normalize_pc_name(role, stripped, year, andersons)

OUTCOME_RE = re.compile(
    r"(vote was unanimous|motion carrie|motion fail|motion passe|"
    r"motion did not carry|motion was denied|motion carries|motion failed|"
    r"unanimous|carries|carried|passed|failed|denied)",
    re.IGNORECASE,
)

NOISE_RE = re.compile(
    r"^\s*(Planning Commission Minutes|Planning Commission Agenda|"
    r"Page \d+ of \d+|\d+\s*\|\s*Page|Page [A-Za-z]+|"
    r"St\. George Planning Commission Minutes|St\. George Planning Commission Agenda|"
    r"[A-Z][A-Za-z]+\.?\s+\d{1,2},?\s+\d{4}|"
    r"Agenda Packet.*|Link to .*)\s*$"
)


def normalize_vote_value(raw):
    v = raw.strip().lower()
    if v.startswith("aye") or v in ("yes", "yea", "for"):
        return VOTE_AYE
    if v.startswith("nay") or v.startswith("no") or v == "against":
        return VOTE_NAY
    if "abstain" in v:
        return VOTE_ABSTAIN
    if "absent" in v or "excused" in v:
        return VOTE_ABSENT
    if "recus" in v:
        return VOTE_RECUSE
    return None


def collapse(text):
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------------------
# Line-number-gutter tolerance
# ---------------------------------------------------------------------------
# A handful of St. George born-digital PC minutes PDFs are printed with a
# left-margin LINE-NUMBER GUTTER: every physical line begins with a per-page
# line number (resetting each page) then whitespace, e.g.
#       25         MOTION:
#       34                Planning Commission Chair Anderson – nay
# which defeats the MOTION:/VOTE: header + roll-call regexes and yields 0
# extracted motions (e.g. the 2024-12-10 3-to-2 failed hillside vote).
# `_strip_line_number_gutter` detects that layout (a high fraction of body
# lines begin with a small SEQUENTIAL number) and, ONLY for such files, removes
# the gutter token, leaving the content intact. Non-gutter files are returned
# byte-identical, so their extraction is unchanged. Detected affected files
# score frac 0.68-0.81; every non-gutter file scores 0.00 -> a wide margin.
GUTTER_LINE_RE = re.compile(r"^ ?(\d{1,3})\s{2,}(\S.*)$")
GUTTER_NUM_ONLY_RE = re.compile(r"^ ?\d{1,3}\s*$")


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


def strip_role(line):
    """Return (role, name) from an attendee/name line, or (None, None)."""
    mm = NAME_LINE_RE.match(line)
    if mm:
        return mm.group(1), mm.group(2)
    return None, None


# ---------------------------------------------------------------------------
# Attendee parsing -> per-meeting roster
# ---------------------------------------------------------------------------
ATTEND_HDR_RE = re.compile(r"^\s*(PRESENT|EXCUSED|ABSENT)\s*:\s*(.*)$")
STOP_HDR_RE = re.compile(
    r"^\s*(CITY STAFF|STAFF|STAFF MEMBERS PRESENT|OTHERS PRESENT|CALL TO ORDER|"
    r"PLEDGE|MINUTES|APPROVAL OF)\b", re.IGNORECASE)


def parse_attendees(lines, year):
    """Return (present_names, member_span_names).

    present_names: canonical commissioners listed PRESENT (counts toward
    n_meetings). member_span_names: PRESENT + EXCUSED (counts toward
    first_seen/last_seen membership span).
    """
    present, span = [], []
    i, n = 0, len(lines)
    while i < n:
        m = ATTEND_HDR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        kind = m.group(1).upper()
        bucket_present = (kind == "PRESENT")
        # the header line itself may carry the first name after the colon
        first_inline = m.group(2).strip()
        names_here = []
        if first_inline:
            r, nm = strip_role(first_inline if first_inline.lower().startswith(
                ("planning", "commissioner", "chair", "vice", "pro", "chairman", "chairwoman"))
                else "")
            if nm:
                names_here.append((r, nm))
        i += 1
        while i < n:
            ln = lines[i]
            s = ln.strip()
            if not s:
                # blank line: peek; attendee blocks sometimes have trailing blank
                i += 1
                # stop if next non-blank is a stop header / section
                continue
            if STOP_HDR_RE.match(ln) or ATTEND_HDR_RE.match(ln) or SECTION_RE.match(ln):
                break
            r, nm = strip_role(ln)
            if nm:
                names_here.append((r, nm))
                i += 1
                continue
            # a non-name, non-blank line ends this attendee block
            break
        for (r, nm) in names_here:
            canon = normalize_pc_name(r, nm, year)
            if not canon:
                continue
            span.append(canon)
            if bucket_present:
                present.append(canon)

    def dedupe(seq):
        seen, out = set(), []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return dedupe(present), dedupe(span)


# ---------------------------------------------------------------------------
# Motion-block parsing
# ---------------------------------------------------------------------------
def parse_meeting(path, date, year):
    with open(path, encoding="utf-8") as fh:
        raw_lines = fh.readlines()
    raw_lines = _strip_line_number_gutter(raw_lines)

    present, span = parse_attendees(raw_lines, year)

    # Anderson attendance scope for THIS meeting (present ∪ excused) -> drives the
    # Austin/Brandon Anderson disambiguation in normalize_pc_name (see its docstring).
    andersons = {nm for nm in set(present) | set(span)
                 if nm in ("Austin Anderson", "Brandon Anderson")}

    votes = []
    n = len(raw_lines)
    i = 0
    current_section = ""
    motion_no = 0

    while i < n:
        line = raw_lines[i]
        sec = SECTION_RE.match(line)
        if sec:
            g = sec.group(1).upper()
            if not any(k in g for k in ("MOTION", "SECOND", "VOTE", "PRESENT",
                                        "EXCUSED", "ABSENT", "AYES", "NAYS",
                                        "ROLL CALL")):
                current_section = collapse(sec.group(1))

        mh = MOTION_HDR_RE.match(line)
        if mh:
            block, end = _consume_motion_block(raw_lines, i, year, andersons)
            if block is not None:
                motion_no += 1
                block["motion_no"] = motion_no
                block["section_header"] = current_section
                votes.append(block)
                i = end
                continue
        i += 1

    out = []
    for b in votes:
        mtype = classify_motion(b["section_header"], b["motion"])
        names_recorded = bool(b["aye"] or b["nay"] or b["abstain"]
                              or b["absent"] or b["recuse"])
        # tally for the result string: authoritative NAMED counts when members
        # are listed; fall back to the declared (n) numbers only for tally-only
        # blocks (no per-member names).
        if names_recorded:
            d_ayes, d_nays = len(b["aye"]), len(b["nay"])
        else:
            d_ayes = b["declared_ayes"] if b["declared_ayes"] is not None else 0
            d_nays = b["declared_nays"] if b["declared_nays"] is not None else 0
        result = encode_result(b["motion"], d_ayes, d_nays, b["passed"])
        out.append(OrderedDict([
            ("motion_no", b["motion_no"]),
            ("section", b["section_header"]),
            ("body", BODY),
            ("motion", b["motion"]),
            ("motion_type", mtype),
            ("result", result),
            ("mover", b["mover"]),
            ("seconder", b["seconder"]),
            ("aye", b["aye"]),
            ("nay", b["nay"]),
            ("abstain", b["abstain"]),
            ("absent", b["absent"]),
            ("recuse", b["recuse"]),
            ("declared_ayes", b["declared_ayes"]),
            ("declared_nays", b["declared_nays"]),
            ("outcome_verbatim", b["outcome"]),
            ("names_recorded", names_recorded),
            ("style", b["style"]),
        ]))
    return out, present, span


def _extract_mover(motion_text, year, andersons=None):
    mm = MOVER_RE_A.search(motion_text)
    if mm:
        return normalize_pc_name(mm.group(1) or "", mm.group(2), year, andersons)
    mm = MOVER_RE_B.match(motion_text)
    if mm:
        return normalize_pc_name(mm.group(1) or "", mm.group(2), year, andersons)
    return ""


def _consume_motion_block(lines, start, year, andersons=None):
    """Parse one MOTION block from index `start`. Returns (block|None, end_idx)."""
    n = len(lines)
    mh = MOTION_HDR_RE.match(lines[start])
    motion_parts = []
    if mh.group(1).strip():
        motion_parts.append(mh.group(1).strip())
    i = start + 1

    # 1) motion text until SECOND / VOTE / ROLL CALL / tally header / next MOTION
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if SECOND_HDR_RE.match(ln) or VOTE_HDR_RE.match(ln) \
                or ROLLCALL_HDR_RE.match(ln) or TALLY_HDR_RE.match(ln) \
                or MOTION_HDR_RE.match(ln):
            break
        if NOISE_RE.match(ln):
            i += 1
            continue
        if s:
            motion_parts.append(s)
        i += 1
    motion_text = collapse(" ".join(motion_parts))
    mover = _extract_mover(motion_text, year, andersons)

    # 2) SECOND block
    seconder = ""
    sh = SECOND_HDR_RE.match(lines[i]) if i < n else None
    if sh:
        # seconder may be inline after "SECOND:" (AYES style) or on the
        # "seconded by ..." sentence (VOTE style).
        inline = sh.group(1).strip()
        if inline:
            sm = SECONDED_BY_RE.search(inline)
            if sm:
                seconder = normalize_pc_name(sm.group(1) or "", sm.group(2), year, andersons)
            else:
                nm = SECOND_NAME_RE.match(inline)
                if nm and nm.group(2):
                    seconder = normalize_pc_name(nm.group(1) or "", nm.group(2), year, andersons)
        i += 1
        # continuation lines of the SECOND sentence until VOTE/ROLL CALL/tally
        while i < n:
            ln = lines[i]
            if VOTE_HDR_RE.match(ln) or ROLLCALL_HDR_RE.match(ln) \
                    or TALLY_HDR_RE.match(ln) or MOTION_HDR_RE.match(ln):
                break
            s = ln.strip()
            if NOISE_RE.match(ln) or not s:
                i += 1
                continue
            if not seconder:
                sm = SECONDED_BY_RE.search(s)
                if sm:
                    seconder = normalize_pc_name(sm.group(1) or "", sm.group(2), year, andersons)
            i += 1

    # 3) VOTE block — detect style
    aye, nay, abstain, absent, recuse = [], [], [], [], []
    declared = {"ayes": None, "nays": None}
    outcome = ""

    # skip a bare ROLL CALL VOTE: / VOTE: header preamble line
    style = None
    # Determine which style by scanning ahead a little.
    j = i
    while j < n and j < i + 6:
        if TALLY_HDR_RE.match(lines[j]):
            style = "AYES"
            break
        if VOTE_LINE_RE.match(lines[j]):
            style = "VOTE"
            break
        if MOTION_HDR_RE.match(lines[j]):
            break
        j += 1

    if style == "AYES":
        i, declared, lists, outcome = _parse_ayes_block(lines, i, year, andersons)
        aye, nay, abstain, absent, recuse = lists
    elif style == "VOTE":
        i, lists, outcome = _parse_voteline_block(lines, i, year, andersons)
        aye, nay, abstain, absent, recuse = lists
    else:
        # No recognizable vote block. If the motion text has no real content
        # (empty "MOTION: Commissioner" placeholder) -> skip entirely.
        if not mover and len(motion_text) < 25:
            return None, i
        # A motion sentence with no vote (withdrawn/superseded) -> skip.
        return None, i

    # Blank placeholder motion ("MOTION: Commissioner" with no mover and no real
    # text) -> skip, even when a template roll call (all-present AYES) follows.
    # We cannot characterize what was decided, so recording it would be a guess.
    core = re.sub(r"^commissioner\b", "", motion_text, flags=re.IGNORECASE).strip()
    if not mover and len(core) < 15:
        return None, i

    # passed? (named counts are authoritative; declared (n) numbers are advisory
    # and are frequently a source typo -- see CLAUDE.md tally-mismatch handling)
    o = outcome.lower()
    named = bool(aye or nay or abstain or absent or recuse)
    if named:
        d_ayes, d_nays = len(aye), len(nay)
    else:
        d_ayes = declared["ayes"] if declared["ayes"] is not None else 0
        d_nays = declared["nays"] if declared["nays"] is not None else 0
    if "fail" in o or "denied" in o or "did not carry" in o:
        passed = False
    elif "carri" in o or "pass" in o or "unanimous" in o or "approved" in o:
        passed = True
    else:
        passed = d_ayes >= d_nays

    return {
        "motion": motion_text,
        "mover": mover,
        "seconder": seconder,
        "aye": aye, "nay": nay, "abstain": abstain,
        "absent": absent, "recuse": recuse,
        "declared_ayes": declared["ayes"],
        "declared_nays": declared["nays"],
        "outcome": outcome,
        "passed": passed,
        "style": style,
    }, i


def _parse_ayes_block(lines, i, year, andersons=None):
    """Parse AYES (n) / NAYS (m) [/ ABSTAIN .. / ABSENT ..] block with names."""
    n = len(lines)
    declared = {"ayes": None, "nays": None}
    aye, nay, abstain, absent, recuse = [], [], [], [], []
    outcome = ""
    bucket = None  # current list to append names to

    # skip leading ROLL CALL VOTE: / VOTE: header if present
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s or NOISE_RE.match(ln):
            i += 1
            continue
        if ROLLCALL_HDR_RE.match(ln) or VOTE_HDR_RE.match(ln):
            i += 1
            continue
        th = TALLY_HDR_RE.match(ln)
        if th:
            kind = th.group(1).upper()
            cnt = int(th.group(2))
            if kind == "AYES":
                bucket, declared["ayes"] = aye, cnt
            elif kind in ("NAYS", "NOES"):
                bucket, declared["nays"] = nay, cnt
            elif kind.startswith("ABSTAIN"):
                bucket = abstain
            elif kind == "ABSENT":
                bucket = absent
            elif kind.startswith("RECUS"):
                bucket = recuse
            elif kind == "EXCUSED":
                bucket = absent
            i += 1
            continue
        # outcome line ends the block (but not if it's actually a name line)
        if OUTCOME_RE.search(s) and not NAME_LINE_RE.match(ln):
            outcome = collapse(s)
            i += 1
            break
        # next MOTION / section header ends the block
        if MOTION_HDR_RE.match(ln) or SECTION_RE.match(ln):
            break
        # a name line -> append to current bucket (lenient role stripping)
        canon = ayes_name(ln, year, andersons)
        if canon and bucket is not None:
            bucket.append(canon)
            i += 1
            continue
        # unknown / non-name line: end the block if we've started collecting
        if bucket is not None or declared["ayes"] is not None:
            break
        i += 1

    return i, declared, (aye, nay, abstain, absent, recuse), outcome


def _parse_voteline_block(lines, i, year, andersons=None):
    """Parse VOTE: block with per-member 'Role Name - aye' lines."""
    n = len(lines)
    aye, nay, abstain, absent, recuse = [], [], [], [], []
    outcome = ""

    # skip the VOTE: header + "called for a vote" preamble
    while i < n:
        ln = lines[i]
        s = ln.strip()
        if not s or NOISE_RE.match(ln):
            i += 1
            continue
        if VOTE_HDR_RE.match(ln) or ROLLCALL_HDR_RE.match(ln):
            i += 1
            continue
        if re.search(r"called for a (roll call )?vote", s, re.IGNORECASE):
            i += 1
            continue
        vm = VOTE_LINE_RE.match(ln)
        if vm:
            val = normalize_vote_value(vm.group(3))
            if val is not None:
                canon = normalize_pc_name(vm.group(1), vm.group(2), year, andersons)
                if val == VOTE_AYE:
                    aye.append(canon)
                elif val == VOTE_NAY:
                    nay.append(canon)
                elif val == VOTE_ABSTAIN:
                    abstain.append(canon)
                elif val == VOTE_ABSENT:
                    absent.append(canon)
                elif val == VOTE_RECUSE:
                    recuse.append(canon)
            i += 1
            continue
        if OUTCOME_RE.search(s):
            outcome = collapse(s)
            i += 1
            break
        if MOTION_HDR_RE.match(ln) or SECTION_RE.match(ln):
            break
        # stray line inside vote block -> stop
        break

    return i, (aye, nay, abstain, absent, recuse), outcome


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
    rel = row["path"].replace("planning_commission/minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def main():
    force = "--force" in sys.argv
    rows = load_index()
    validation_lines = []
    all_rows = []
    stats = {
        "pc_meetings_parsed": 0,
        "motions": 0,
        "member_vote_rows": 0,
        "recommendations": 0,
        "final_actions": 0,
        "procedural": 0,
        "contested": 0,
        "tally_only_motions": 0,
        "named_motions": 0,
        "tally_mismatches": [],
        "unparsed_meetings": [],
        "by_year_pmn_vs_revize": {},
    }
    roster_present_count = {}      # name -> n_meetings present
    roster_first = {}             # name -> first date seen (present/excused)
    roster_last = {}              # name -> last date seen
    commissioners_by_year = {}    # year -> set of canonical names seen in votes/attend

    for row in rows:
        md_path = os.path.join(REPO, row["path"])
        if not os.path.exists(md_path):
            stats["unparsed_meetings"].append(row["path"] + " (missing)")
            continue
        year = int(row["year"])
        src = row.get("source", "")
        try:
            votes, present, span = parse_meeting(md_path, row["date"], year)
        except Exception as e:  # noqa
            stats["unparsed_meetings"].append(f"{row['path']} (error: {e})")
            continue

        stats["pc_meetings_parsed"] += 1
        by = stats["by_year_pmn_vs_revize"].setdefault(
            row["year"], {"pmn": 0, "revize": 0, "motions": 0})
        by[src] = by.get(src, 0) + 1

        # roster bookkeeping
        for nm in present:
            roster_present_count[nm] = roster_present_count.get(nm, 0) + 1
        for nm in span:
            d = row["date"]
            if nm not in roster_first or d < roster_first[nm]:
                roster_first[nm] = d
            if nm not in roster_last or d > roster_last[nm]:
                roster_last[nm] = d
            commissioners_by_year.setdefault(row["year"], set()).add(nm)

        if not votes:
            validation_lines.append(f"INFO  {row['path']}: no motion/vote blocks")

        meeting_json = OrderedDict([
            ("date", row["date"]),
            ("year", year),
            ("title", TITLE),
            ("body", BODY),
            ("source", row["path"]),
            ("source_format", src),
            ("roster_present", present),
            ("votes", []),
        ])

        for v in votes:
            stats["motions"] += 1
            by["motions"] += 1
            named = v["names_recorded"]
            if named:
                stats["named_motions"] += 1
            else:
                stats["tally_only_motions"] += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                stats["contested"] += 1
            r = v["result"]
            if "recommend" in r.lower():
                stats["recommendations"] += 1
            elif "final action" in r.lower():
                stats["final_actions"] += 1
            else:
                stats["procedural"] += 1

            # roster span covers every recorded appearance (attendee OR vote);
            # a few source minutes list a voter who is absent from their own
            # PRESENT block (stale roll-call template, e.g. Emily Andrus in the
            # Jan-2024 files), so include voter dates to keep the span truthful.
            for nm in (v["aye"] + v["nay"] + v["abstain"]
                       + v["absent"] + v["recuse"]):
                commissioners_by_year.setdefault(row["year"], set()).add(nm)
                d = row["date"]
                if nm not in roster_first or d < roster_first[nm]:
                    roster_first[nm] = d
                if nm not in roster_last or d > roster_last[nm]:
                    roster_last[nm] = d

            jvote = OrderedDict([
                ("motion_no", v["motion_no"]),
                ("section", v["section"]),
                ("body", BODY),
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

            _validate(row, v, validation_lines, stats)

            for vlist, vval in ((v["aye"], "Aye"), (v["nay"], "Nay"),
                                (v["abstain"], "Abstain"), (v["absent"], "Absent"),
                                (v["recuse"], "Recuse")):
                for member in vlist:
                    all_rows.append([
                        row["date"], row["year"], TITLE, BODY, v["motion_no"],
                        v["motion"], v["motion_type"], v["result"], v["mover"],
                        v["seconder"], member, vval, row["path"],
                    ])

        out_path = votes_json_path(row)
        if force or not os.path.exists(out_path):
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(meeting_json, fh, indent=2, ensure_ascii=False)

    stats["member_vote_rows"] = len(all_rows)

    # all_votes.csv (13-col schema)
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "year", "title", "body", "motion_no", "motion",
                    "motion_type", "result", "mover", "seconder",
                    "member", "vote", "source"])
        for r in all_rows:
            w.writerow(r)

    # roster.csv
    roster_names = sorted(set(list(roster_first.keys()) + list(roster_present_count.keys())))
    with open(ROSTER_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for nm in roster_names:
            w.writerow([nm, roster_first.get(nm, ""), roster_last.get(nm, ""),
                        roster_present_count.get(nm, 0)])

    # validation report
    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(VALIDATION_REPORT, "w", encoding="utf-8") as fh:
        fh.write("St. George Planning Commission vote-extraction validation report\n")
        fh.write("=" * 64 + "\n")
        for k in ("pc_meetings_parsed", "motions", "member_vote_rows",
                  "recommendations", "final_actions", "procedural",
                  "named_motions", "tally_only_motions", "contested"):
            fh.write(f"{k}: {stats[k]}\n")
        fh.write(f"tally_mismatches: {len(stats['tally_mismatches'])}\n")
        fh.write("=" * 64 + "\n\n")
        fh.write("TALLY MISMATCHES (declared (n) vs named count, or outcome vs tally):\n")
        for ln in stats["tally_mismatches"]:
            fh.write("  " + ln + "\n")
        fh.write("\nPER-YEAR (source format / motions):\n")
        for y in sorted(stats["by_year_pmn_vs_revize"]):
            d = stats["by_year_pmn_vs_revize"][y]
            fh.write(f"  {y}: pmn={d.get('pmn',0)} revize={d.get('revize',0)} "
                     f"motions={d.get('motions',0)}\n")
        fh.write("\nINFO / no-vote meetings:\n")
        for ln in validation_lines:
            fh.write("  " + ln + "\n")
        fh.write("\nUNPARSED:\n")
        for ln in stats["unparsed_meetings"]:
            fh.write("  " + ln + "\n")

    # roster-range validation: members in votes within their roster span/year
    stats["commissioners_by_year"] = {y: sorted(s) for y, s in
                                      sorted(commissioners_by_year.items())}
    stats["distinct_commissioners"] = len(roster_names)

    print(json.dumps(stats, indent=2, default=str))
    return stats


def _validate(meeting_row, v, log, stats):
    """Cross-check declared (n) header counts vs named lists, and outcome vs tally."""
    p = meeting_row["path"]
    mno = v["motion_no"]
    src = meeting_row.get("source", "")
    tag = "[PMN]" if src == "pmn" else "[REVIZE]"
    # declared vs named (AYES style only has declared numbers)
    if v["declared_ayes"] is not None and v["aye"] and \
            v["declared_ayes"] != len(v["aye"]):
        stats["tally_mismatches"].append(
            f"{tag} {p} m{mno}: AYES declared {v['declared_ayes']} but "
            f"{len(v['aye'])} names listed")
    if v["declared_nays"] is not None and v["nay"] and \
            v["declared_nays"] != len(v["nay"]):
        stats["tally_mismatches"].append(
            f"{tag} {p} m{mno}: NAYS declared {v['declared_nays']} but "
            f"{len(v['nay'])} names listed")
    # outcome says unanimous but a nay recorded
    o = (v.get("outcome_verbatim") or "").lower()
    if "unanimous" in o and (len(v["nay"]) > 0 or (v["declared_nays"] or 0) > 0):
        stats["tally_mismatches"].append(
            f"{tag} {p} m{mno}: outcome 'unanimous' but nay recorded "
            f"({v.get('outcome_verbatim')})")


if __name__ == "__main__":
    main()
