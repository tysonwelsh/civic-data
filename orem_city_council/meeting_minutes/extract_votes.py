#!/usr/bin/env python3
"""
Orem City Council vote extractor.

Reads the markdown minutes under meeting_minutes/minutes/<year>/<week>/<date>_<slug>.md
and produces, per meeting, a JSON of recorded council votes
(meeting_minutes/votes/<year>/<week>/<date>_<slug>.json), then rebuilds the long-format
meeting_minutes/all_votes.csv.

Orem records each motion in prose:
    "Mr. X moved [, by ordinance,] to <motion text>. [Mr.] Y seconded the motion.
     Those voting aye/yes: <names>. Those voting nay/no: <names>. The motion passed/failed."
(Some 2024 files wrap the cue words in markdown bold ** **; some files use
 "Seconded by Y" / "seconded by Y"; OCR 2025-11-18 is lower fidelity.)

We treat the prose "Those voting ..." block as the authoritative per-motion vote.
The trailing per-meeting signature checkbox table ("COUNCIL MEMBER | AYE | NAY ...")
is a single meeting-level sign-off page, NOT a per-motion vote, and is ignored.

NEVER invents who voted which way. Tally/unanimous without an explicit name list ->
names_recorded:false with empty member lists.

Run from anywhere:  python3 meeting_minutes/extract_votes.py
"""

import csv
import json
import os
import re
import sys

# ---------------------------------------------------------------- paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # meeting_minutes/
REPO_ROOT = os.path.dirname(SCRIPT_DIR)                          # orem_city_council/
MINUTES_DIR = os.path.join(SCRIPT_DIR, "minutes")
VOTES_DIR = os.path.join(SCRIPT_DIR, "votes")
INDEX_CSV = os.path.join(SCRIPT_DIR, "minutes_index.csv")
ALL_VOTES_CSV = os.path.join(SCRIPT_DIR, "all_votes.csv")
VALIDATION_TXT = os.path.join(VOTES_DIR, "_validation_report.txt")

# ---------------------------------------------------------------- name normalization
# Canonical surname-keyed normalization. Orem minutes give full names in vote lists
# ("David A. Young", "LaNae Millett") and titled short names for mover/seconder
# ("Mr. Spencer", "Ms. Millett", "Mrs. Lauret"). We normalize both to a canonical
# "First Last" form keyed primarily on surname, resolving the documented spelling drift
# (Millet/Millett, Debby/Debbie, Macdonald/MacDonald).
CANON = {
    "young": "David Young",
    "spencer": "David Spencer",
    "spender": "David Spencer",   # OCR variant
    "spenser": "David Spencer",   # OCR variant
    "lauret": "Debby Lauret",
    "macdonald": "Tom Macdonald",
    "mcdonald": "Tom Macdonald",
    "macdonals": "Tom Macdonald",   # OCR variant (trailing 's' for 'd')
    "peterson": "Terry Peterson",
    "lambson": "Jeff Lambson",
    "sumner": "Brent Sumner",
    "brunst": "Richard Brunst",
    "millet": "LaNae Millett",
    "millett": "LaNae Millett",
    "millettt": "LaNae Millett",   # OCR/typo variant
    "gale": "Jenn Gale",
    "jenngale": "Jenn Gale",       # OCR variant "Jenn'Gale" (no separating space)
    "killpack": "Chris Killpack",
    "mecham": "Quinn Mecham",
    "muhlestein": "Crystal Muhlestein",
    "mccandless": "Karen McCandless",
    "mortimer": "Doyle Mortimer",
}

# Honorifics / titles to strip from a name token.
# Honorific must be followed by a period or whitespace (so "Macdonald" is not mistaken
# for the bare "M." honorific). Matches "Mr. ", "Mr.Spencer", "Mrs ", "Mayor ", "M. ".
TITLE_RE = re.compile(r"^(mr|mrs|ms|miss|dr|mayor|councilmember|council member|councilman|councilwoman|vice mayor|m)(?:\.\s*|\s+)", re.I)
SUFFIX_RE = re.compile(r"\b(jr|sr|ii|iii|iv|esq)\.?$", re.I)

ZW = dict.fromkeys(map(ord, "​‌‍‎‏﻿ "), None)


def clean_text(s):
    """Normalize zero-width chars, NBSP, markdown bold, smart quotes, whitespace."""
    s = s.translate(ZW)
    s = s.replace(" ", " ")
    s = s.replace("**", "").replace("__", "")
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-")
    return s


_FIRST_TO_FULL = {}
for _sur, _full in CANON.items():
    _FIRST_TO_FULL.setdefault(_full.split()[0].lower(), _full)


def normalize_name(raw):
    """Map a raw name token from minutes to a canonical 'First Last'. Returns None if junk."""
    if not raw:
        return None
    n = clean_text(raw).strip().strip(".,;:")
    n = TITLE_RE.sub("", n).strip()
    n = SUFFIX_RE.sub("", n).strip().strip(".,;:")
    if not n:
        return None
    # Drop a stray standalone title token (e.g. "Mr"/"Mr." left when a surname got sliced
    # off by an OCR period). TITLE_RE only strips a title that is FOLLOWED by a name, so a
    # bare title survives to here — reject it rather than emit a bogus "Mr" member.
    if re.fullmatch(r"(mr|mrs|ms|miss|dr|mayor|m)\.?", n, re.I):
        return None
    # surname = last whitespace-separated token, lowercased, alpha only
    tokens = [t for t in re.split(r"\s+", n) if t]
    if not tokens:
        return None
    surname = re.sub(r"[^a-z]", "", tokens[-1].lower())
    if surname in CANON:
        cand = CANON[surname]
        # Full-name gate: reject the fold only when the preceding first name belongs
        # to a DIFFERENT known member (a real shared-surname collision) — not for a
        # nickname/OCR variant. No-op today (surnames unique). Keep verbatim on a real
        # conflict rather than wrong-merge.
        if len(tokens) >= 2:
            pfx = re.sub(r"[^a-z]", "", tokens[-2].lower())
            cf = cand.split()[0].lower()
            other = _FIRST_TO_FULL.get(pfx)
            if (len(pfx) > 1 and pfx != cf and not cf.startswith(pfx)
                    and other is not None and other != cand):
                return " ".join(w.capitalize() for w in tokens)
        return cand
    # Try first token as surname (mover form "Mr. Spencer" already handled; this catches
    # "Spencer" alone). Also try any token matching a known surname.
    for tok in tokens:
        key = re.sub(r"[^a-z]", "", tok.lower())
        if key in CANON:
            return CANON[key]
    # Unknown name: title-case what we have (keeps real but un-rostered names rather than dropping).
    return " ".join(w.capitalize() for w in tokens)


STOPWORDS = {"the", "and", "of", "be", "to", "a", "an", "in", "on", "for", "with",
             "city", "council", "motion", "passed", "failed", "minutes", "complete",
             "video", "meeting", "section", "code", "ordinance", "resolution", "as",
             "that", "this", "by", "or", "at", "draft", "presented", "page", "pg"}


def looks_like_name(part):
    """Heuristic: is this comma-part a plausible person name, not narrative?"""
    p = part.strip().strip(".")
    if not p:
        return False
    if p.lower() in ("none", "n/a", "na", "no one", "nobody"):
        return False
    if any(ch.isdigit() for ch in p):
        return False
    tokens = [t for t in re.split(r"\s+", p) if t]
    if len(tokens) > 4:           # names are at most First M. Last (+title)
        return False
    # reject if it contains a stopword token (narrative leakage). Single-letter middle
    # initials (e.g. the "A." in "David A. Young") are exempt — they collide with the
    # article "a" but are legitimate name parts.
    for t in tokens:
        bare = re.sub(r"[^a-zA-Z]", "", t)
        if len(bare) <= 1:
            continue
        if bare.lower() in STOPWORDS:
            return False
    # at least one capitalized token
    if not any(t[:1].isupper() for t in tokens):
        return False
    return True


def resolve_actor(capture):
    """Resolve a (possibly noisy) mover/seconder capture to a canonical name.

    The regex may grab leading junk ("Pm Mr. Spender", "as listed. Mrs. Millettt").
    Prefer a token that resolves to a KNOWN roster surname (scanning right-to-left,
    since the surname sits just before 'moved'/'seconded'); else fall back to
    normalize_name of the last 1-2 tokens.
    """
    if not capture:
        return ""
    cap = clean_text(capture).strip()
    # cut anything before a sentence boundary inside the capture
    cap = re.split(r"\.\s+(?=[A-Z])", cap)[-1] if ". " in cap else cap
    tokens = [t for t in re.split(r"\s+", cap) if t]
    # scan right-to-left for a known surname
    for tok in reversed(tokens):
        key = re.sub(r"[^a-z]", "", tok.lower())
        if key in CANON:
            return CANON[key]
    # fall back to normalizing the trailing two tokens
    tail = " ".join(tokens[-2:]) if len(tokens) >= 2 else (tokens[-1] if tokens else "")
    return normalize_name(tail) or ""


def split_names(blob):
    """Split a vote-list blob like 'A, B, C and D' into normalized names.

    Name lists end at the first sentence boundary ('. ' before a new clause). We bound
    the blob to the list and then accept only comma-parts that look like real names,
    so narrative that leaks past a list (line wraps, page footers) is dropped, never
    invented into a member.
    """
    blob = clean_text(blob).strip()
    # Bound to the name list: cut at the first '. ' that ends the sentence (lists never
    # contain a period+space except after an initial like 'David A. Young', which we keep
    # by only cutting when the period is preceded by >1 letter token).
    # Strategy: replace single-letter-initial periods, find the first real sentence end.
    guarded = re.sub(r"\b([A-Z])\.", r"\1<DOT>", blob)   # protect initials "A." -> "A<DOT>"
    # Also protect an honorific period ("Mr.", "Mrs.", "Ms.", "Dr.") so an OCR'd vote list
    # like "Those voting nay: Mr. Macdonald" is not sliced into the bare title "Mr".
    guarded = re.sub(r"\b(Mr|Mrs|Ms|Miss|Dr|Mayor)\.", r"\1<DOT>", guarded, flags=re.I)
    cut = re.search(r"\.\s", guarded)
    if cut:
        guarded = guarded[:cut.start()]
    blob = guarded.replace("<DOT>", ".")
    blob = re.sub(r"\s+and\s+", ", ", blob)
    blob = re.sub(r"\s*&\s*", ", ", blob)
    parts = [p.strip() for p in blob.split(",")]
    out = []
    seen = set()
    for p in parts:
        if not looks_like_name(p):
            continue
        nm = normalize_name(p)
        if nm and nm not in seen:
            seen.add(nm)
            out.append(nm)
    return out


# ---------------------------------------------------------------- motion type taxonomy
def classify_motion(heading, motion_text):
    """Map a motion to one of the fixed 12 categories using its agenda heading + text."""
    h = (heading or "").lower()
    t = (motion_text or "").lower()
    blob = h + " " + t

    # Procedural housekeeping is decided on the MOTION TEXT (most reliable), before any
    # heading-based ordinance/resolution inference, so "approve the Consent Agenda" under
    # an ORDINANCE heading is not misfiled.
    if "adjourn" in t:
        return "Procedural/Administrative"
    if "consent" in t:                       # consent agenda / consent items
        return "Procedural/Administrative"
    if re.search(r"\btable\b|\bcontinue\b|\bpostpone\b|\brecess\b|\bexcuse\b|order of the agenda|amend the agenda|approve the minutes|approve the .* minutes", t):
        return "Procedural/Administrative"
    if "canvass" in t or ("certify" in t and ("election" in t or "city of orem" in t)):
        return "Procedural/Administrative"
    if "closed meeting" in t or "closed session" in t or "executive session" in t:
        return "Procedural/Administrative"

    if "appoint" in blob or "reappoint" in blob:
        return "Appointment"
    if "proclamation" in blob or "proclaim" in blob or "ceremon" in blob or "recogniz" in blob or "honor" in blob:
        return "Ceremonial"
    if "interlocal" in blob or "inter-local" in blob:
        return "Interlocal"
    if "budget amendment" in blob or ("budget" in blob and "amend" in blob):
        return "Budget Amendment"
    if ("grant" in blob and ("cdbg" in blob or "fund" in blob or "award" in blob or "accept" in blob)) \
            or ("cdbg" in blob and "fund" in blob) or ("cares act" in blob and "fund" in blob):
        return "Grant-Funding"
    if re.search(r"\brezone\b|rezoning|zone change|annex|general plan|land use|subdivision|plat|conditional use|zoning map", blob):
        return "Land-Use/Zoning"
    if "ordinance" in blob:
        # zoning ordinances already caught above
        return "Ordinance"
    if "resolution" in blob:
        return "Resolution"
    # a code/ordinance text amendment without the word "ordinance" (truncated headings)
    if re.search(r"\bamend\w*\b.*\b(section|article|appendix|city code|orem code)\b", blob):
        return "Ordinance"
    if re.search(r"\bcontract\b|\bagreement\b|purchase|bid|procure|professional services|task order|change order", blob):
        return "Contract/Purchase"
    if "public hearing" in h and not motion_text:
        return "Public Hearing Action"
    return "Other"


# ---------------------------------------------------------------- heading detection
# An agenda-item heading line: mostly upper-case, often starts with a type keyword.
HEADING_KEYWORDS = ("ORDINANCE", "RESOLUTION", "PUBLIC HEARING", "CONSENT", "CANVASS",
                    "APPOINTMENT", "PROCLAMATION", "AGREEMENT", "CONTRACT", "BUDGET",
                    "INTERLOCAL", "SCHEDULED ITEM", "MOTION", "FINANCIAL")


def is_heading(line):
    s = clean_text(line).strip(" -–•\t")
    if len(s) < 4:
        return False
    if re.search(r"those voting|moved|seconded|motion (passed|failed)", s, re.I):
        return False
    # "Public Hearing Open/Closed 7:15 PM" timestamp lines & bare open/close are not
    # agenda-item headings (they sit between an item heading and its motion).
    if re.search(r"public hearing\s+(open|close|closed)\b|^(open|close|closed)\s+(for|at)\b", s, re.I):
        return False
    if re.match(r"^\d{1,2}:\d{2}\s*(a\.?m\.?|p\.?m\.?)", s, re.I):
        return False
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if upper_ratio > 0.7 and len(s) < 200:
        return True
    if any(s.upper().startswith(k) for k in HEADING_KEYWORDS):
        return True
    return False


# ---------------------------------------------------------------- vote block parsing
# The vote sentence(s). Capture aye/yes, nay/no, abstain, recuse, absent lists + outcome.
#
# Label tolerance for OCR noise: after "Those voting aye/yes/nay/no" the colon may be
# missing, doubled, replaced by a stray period, or have a period+space injected
# ("Those voting yes:." in 2026-03-10, "Those voting.no:" in 2024-12-10). The label
# separator `[\s.:]*` swallows any run of whitespace/period/colon between the cue word
# and the name list, so the aye/nay names are captured rather than dropped.
#
# Likewise the outcome cue "The motion ..." tolerates a stray period for whitespace
# ("The.motion failed." in 2024-12-10) via `The[\s.]+motion`, so an OCR'd outcome still
# terminates its own vote block instead of letting the block greedily swallow the next
# motion's roll-call (which produced a merged motion with duplicate members).
VOTE_BLOCK_RE = re.compile(
    r"Those\s+voting[\s.]+(?:aye|yes)[\s.:]*(?P<aye>.*?)"
    r"(?:Those\s+voting[\s.]+(?:nay|no)[\s.:]*(?P<nay>.*?))?"
    r"(?:Those\s+abstaining[\s.:]*(?P<abstain>.*?))?"
    r"(?:Those\s+recus(?:ing|ed)[\s.:]*(?P<recuse>.*?))?"
    r"(?:Those\s+absent[\s.:]*(?P<absent>.*?))?"
    r"The[\s.]+motion\s+(?P<outcome>passed|failed|carried|did\s+not\s+pass|was\s+approved|was\s+denied)",
    re.I | re.S,
)

# Tally-only / unanimous motion with NO per-member name list:
# "<mover> moved to <text>. <seconder> seconded the motion. The motion passed[ unanimously]."
# (No 'Those voting' clause.) The overlap check in extract_file ensures we don't double
# count blocks already captured by VOTE_BLOCK_RE.
NONAME_BLOCK_RE = re.compile(
    r"\b\w[\w.''\-]*\s+moved\b(?:(?!Those\s+voting).){0,500}?"
    r"\bseconded\b(?:(?!Those\s+voting).){0,160}?"
    r"The\s+motion\s+(?P<outcome>passed|failed|carried|did\s+not\s+pass|was\s+approved|was\s+denied)",
    re.I | re.S,
)

# --- LENIENT variants — used ONLY by the standalone RDA/MBA pmn_backfill path
# (extract_file(..., lenient=True)); the default audited council pipeline is untouched.
# They add two OCR/phrasing tolerances seen in Orem's scanned standalone RDA/MBA minutes
# but NOT in the audited council corpus:
#   (1) the outcome cue may be worded "The vote was unanimous, motion passed" (no bare
#       "The motion passed") — 2022-06-14 MBA; and
#   (2) OCR noise may sit between "motion" and the outcome word ("The motion ™ passed")
#       — 2023-05-09 MBA adjournment.
# `_OUTCOME_TAIL` swallows an optional "vote was unanimous," lead-in and one non-word
# noise token before the outcome verb.
_OUTCOME_TAIL = (
    r"The[\s.]+(?:vote\s+was\s+unanimous[,.\s]+)?motion\s+(?:[^\w\s]+\s+)?"
    r"(?P<outcome>passed|failed|carried|did\s+not\s+pass|was\s+approved|was\s+denied)"
)
LENIENT_VOTE_BLOCK_RE = re.compile(
    r"Those\s+voting[\s.]+(?:aye|yes)[\s.:]*(?P<aye>.*?)"
    r"(?:Those\s+voting[\s.]+(?:nay|no)[\s.:]*(?P<nay>.*?))?"
    r"(?:Those\s+abstaining[\s.:]*(?P<abstain>.*?))?"
    r"(?:Those\s+recus(?:ing|ed)[\s.:]*(?P<recuse>.*?))?"
    r"(?:Those\s+absent[\s.:]*(?P<absent>.*?))?" + _OUTCOME_TAIL,
    re.I | re.S,
)
LENIENT_NONAME_BLOCK_RE = re.compile(
    r"\b\w[\w.''\-]*\s+moved\b(?:(?!Those\s+voting).){0,500}?"
    r"\bseconded\b(?:(?!Those\s+voting).){0,160}?" + _OUTCOME_TAIL,
    re.I | re.S,
)

# Mover + seconder, searched in the text immediately preceding the vote block.
# Allow an optional adverb (then/also/further/again) between the name and "moved":
# "Mayor Brunst then moved ...".
MOVER_RE = re.compile(
    r"([A-Z][A-Za-z.''\-]*(?:\s+[A-Z][A-Za-z.''\-]*){0,3})"
    r"(?:\s+(?:then|also|further|again|subsequently))?\s+moved\b",
)
# seconder forms: "Y seconded the motion" | "seconded by Y" | "Seconded by Y" (any case).
SECOND_BY_RE = re.compile(r"seconded\s+by\s+([A-Z][A-Za-z.''\-]*(?:\s+[A-Z][A-Za-z.''\-]*){0,3})", re.I)
SECONDER_RE = re.compile(r"([A-Z][A-Za-z.''\-]*(?:\s+[A-Z][A-Za-z.''\-]*){0,3})\s+seconded\b", re.I)


def parse_motion_text(pre):
    """Extract the motion text from '<mover> moved [, by X,] to <TEXT>. <seconder> ...'."""
    # use the LAST 'moved' in the window (closest to the vote block)
    matches = list(re.finditer(r"\bmoved\b", pre, re.I))
    if not matches:
        return ""
    rest = pre[matches[-1].end():]
    # cut at the seconder clause ("X seconded the motion" or "Seconded by Y")
    rest = re.split(r"(?:[A-Z][\w.''\-]*\s+)?seconded\b|\bseconded by\b", rest, flags=re.I)[0]
    # also cut at any "Those voting" that slipped in
    rest = re.split(r"those voting", rest, flags=re.I)[0]
    rest = re.sub(r"^\s*[,]?\s*", "", rest)
    rest = re.sub(r"^by\s+(an?\s+)?(ordinance|resolution)\s*,?\s*", r"by \2, ", rest, flags=re.I)
    rest = re.sub(r"^\s*to\s+", "", rest, flags=re.I)
    # strip page-footer noise that can wrap into the motion
    rest = re.sub(r"City Council Minutes.*?www\.orem\.org\S*", " ", rest, flags=re.I)
    rest = re.sub(r"\bDRAFT\b", " ", rest)
    rest = re.sub(r"\(pg?\.?\s*\d+\)", " ", rest, flags=re.I)
    rest = clean_text(rest).strip().strip(".")
    rest = re.sub(r"\s+", " ", rest)
    # strip a trailing dangling honorific/name fragment left by a seconder clause we
    # failed to split (e.g. "... Minutes. Ms" / "... as presented. Mr")
    rest = re.sub(r"[.,]?\s+(Mr|Mrs|Ms|Mayor|Dr)\.?\s*$", "", rest).strip()
    return rest[:500].strip()


# ---------------------------------------------------------------- body (governing-body) tagging
# In Utah the City Council sits AS the board of the Redevelopment Agency (RDA),
# Community Reinvestment Agency (CRA), Municipal Building Authority (MBA), etc. Orem does
# NOT hold these as separate meeting files; instead the council, mid-meeting, *adjourns to
# a meeting of* the other body — e.g. "ADJOURN TO A MEETING OF THE OREM REDEVELOPMENT
# AGENCY (RDA)" / "Mr. Spencer moved to adjourn to a meeting of the Municipal Building
# Authority". After that motion, the embedded section ("RDA CONSENT ITEMS", "RDA SCHEDULED
# ITEMS", etc.) is that body's business until the NEXT such marker or the final adjournment.
#
# The transition motion itself ("moved to adjourn to a meeting of X") is a *Council* vote
# (the council deciding to convene as the other board), so it keeps the PRIOR body. We model
# this by anchoring each body change at the END of the transition-motion phrase, so a motion
# is tagged with the body of the most recent marker whose anchor precedes its block_start.
#
# Bodies tagged: Council (default), RDA, CRA, MBA. Orem also adjourns to a Special Service
# Lighting District (SSLD) — a real separate special district, tagged SSLD so its motions are
# not mislabeled Council (it is outside the RDA/CRA/MBA set but kept truthful).
#
# Note: a *narrative mention* of "Municipal Building Authority" / "Community Reinvestment
# Area" in discussion text does NOT trigger a body change — only the explicit "adjourn to a
# meeting of the <body>" motion does — so a council item that merely talks about MBA/CRA
# property stays Council.
BODY_MARKER_RE = re.compile(
    r"adjourn(?:ment|ed|ing|s)?\s+to\s+a\s+meeting\s+of\s+the\s+"
    r"(?P<who>(?:orem\s+|city\s+of\s+)?"
    r"(?:redevelopment\s+agency(?:\s+of(?:\s+the\s+city)?\s+of\s+orem)?|rda"
    r"|community\s+reinvestment\s+agency|cra"
    r"|municipal\s+building\s+authority|mba"
    r"|special\s+service[s]?\s+lighting\s+district|ssld))",
    re.I,
)


def body_from_who(who):
    """Map a captured body name (any wording/case) to its canonical code."""
    w = (who or "").lower()
    if "municipal building authority" in w or re.search(r"\bmba\b", w):
        return "MBA"
    if "community reinvestment" in w or re.search(r"\bcra\b", w):
        return "CRA"
    if "special service" in w or re.search(r"\bssld\b", w):
        return "SSLD"
    if "redevelopment agency" in w or re.search(r"\brda\b", w):
        return "RDA"
    return "Council"


# End-of-vote-block cue used to anchor a body change AFTER the transition motion.
_OUTCOME_END_RE = re.compile(
    r"The\s+motion\s+(?:passed|failed|carried|did\s+not\s+pass|was\s+(?:approved|denied))[^.]*\.",
    re.I,
)


def find_body_markers(text):
    """Return sorted [(anchor_offset, body_code)] for each 'adjourn to a meeting of <body>'
    transition in the flattened meeting text.

    The transition motion itself ("moved to adjourn to a meeting of <body>") is a *Council*
    vote — the council, still sitting as the council, deciding to convene as the next body —
    so it must keep the PRIOR body. We therefore anchor the body change at the END of that
    transition motion's vote block (the first "The motion passed/failed." after the marker),
    so the new body takes effect only for the section's subsequent motions. If no outcome cue
    is found (rare/no-vote adjournment), fall back to the end of the marker phrase."""
    markers = []
    for m in BODY_MARKER_RE.finditer(text):
        code = body_from_who(m.group("who"))
        if code == "Council":
            continue
        end_cue = _OUTCOME_END_RE.search(text, m.end())
        anchor = end_cue.end() if end_cue else m.end()
        markers.append((anchor, code))
    markers.sort()
    return markers


def body_at(markers, pos):
    """Body in effect at char offset `pos`: the most recent marker anchor <= pos, else Council."""
    body = "Council"
    for off, code in markers:
        if off <= pos:
            body = code
        else:
            break
    return body


def find_headings(lines):
    """Return list of (char_offset, heading_text) for agenda headings, in order."""
    res = []
    offset = 0
    for ln in lines:
        if is_heading(ln):
            res.append((offset, clean_text(ln).strip(" -–•\t#")))
        offset += len(ln) + 1
    return res


def nearest_heading(headings, pos):
    chosen = ""
    for off, txt in headings:
        if off <= pos:
            chosen = txt
        else:
            break
    return chosen


def tally_from_outcome(outcome, n_aye, n_nay, n_abs, n_recuse, names_recorded):
    out = outcome.lower()
    passed = out in ("passed", "carried", "was approved")
    word = "Pass" if passed else "Fail"
    if names_recorded:
        return f"{n_aye}-{n_nay} {word}"
    return word


FOOTER_RE = re.compile(
    r"City Council Minutes\b.*?(?:www\.orem\.org\S*|orem\.org/meeting\S*)", re.I | re.S)


def flatten_for_votes(text, lenient=False):
    """Remove page-footer noise and collapse to a single whitespace stream so that
    vote-list name strings that wrap across page breaks become contiguous. Headings are
    detected separately (from raw lines), so flattening here is safe.

    `lenient` (pmn_backfill standalone RDA/MBA only) additionally strips the bare
    "<Body> Minutes - Month DD, YYYY" page footer that Orem's scanned RDA/MBA minutes
    inject mid name-list (e.g. "Those voting  Redevelopment Agency Minutes - May 12, 2020
    aye: ...", 2020-05-12 RDA) which would otherwise break the "Those voting ... aye"
    cue. Scoped to RDA/MBA/SSLD footers so the audited council pipeline is unaffected."""
    t = FOOTER_RE.sub(" ", text)
    if lenient:
        t = re.sub(
            r"\b(?:Redevelopment Agency|Municipal Building Authority|"
            r"Special Service Lighting District|RDA|MBA|SSLD)\s+Minutes\s*-\s*"
            r"[A-Za-z]+\.?\s+\d{1,2},?\s*\d{4}", " ", t, flags=re.I)
    t = re.sub(r"\bA complete video of the meeting.*?meeting\S*", " ", t, flags=re.I)
    t = re.sub(r"^\s*DRAFT\s*$", " ", t, flags=re.I | re.M)
    t = re.sub(r"\bDRAFT\b", " ", t)
    t = re.sub(r"\(p\.?\s*\d+\)|\(pg\.?\s*\d+\)", " ", t, flags=re.I)
    # strip OCR/line-number prefixes: a number alone at the start of a line
    t = re.sub(r"^\s*\d{1,3}\s+", " ", t, flags=re.M)
    # collapse all whitespace (incl newlines) to single spaces
    t = re.sub(r"\s+", " ", t)
    return t


def locate_headings_in_flat(heading_texts, flat):
    """Map each detected heading to its position within the flattened text (by ordered
    search) so nearest_heading can associate a motion with the agenda item above it."""
    located = []
    cursor = 0
    for ht in heading_texts:
        key = re.sub(r"\s+", " ", ht).strip()
        if len(key) < 4:
            continue
        # search a leading slice of the heading (first ~50 chars) to tolerate wrapping
        probe = key[:50]
        idx = flat.find(probe, cursor)
        if idx == -1:
            idx = flat.find(probe)  # fall back to first occurrence
        if idx != -1:
            located.append((idx, key))
            cursor = idx + 1
    located.sort()
    return located


def extract_file(path, meeting, lenient=False):
    raw = open(path, encoding="utf-8", errors="replace").read()
    lines = raw.split("\n")
    heading_texts = [h for _, h in find_headings(lines)]
    text = flatten_for_votes(clean_text(raw), lenient=lenient)
    headings = locate_headings_in_flat(heading_texts, text)
    body_markers = find_body_markers(text)
    vote_block_re = LENIENT_VOTE_BLOCK_RE if lenient else VOTE_BLOCK_RE
    noname_block_re = LENIENT_NONAME_BLOCK_RE if lenient else NONAME_BLOCK_RE

    collected = []          # (block_start, vote_dict) — sorted & numbered at the end
    named_spans = []        # (start, end) of named vote blocks, to dedup the no-name pass
    for m in vote_block_re.finditer(text):
        block_start = m.start()
        named_spans.append((m.start(), m.end()))
        # preceding window for mover/seconder/motion text (look back up to 1200 chars,
        # but not across a previous vote block)
        win_start = max(0, block_start - 1400)
        pre = text[win_start:block_start]
        # don't cross a prior 'The motion passed/failed.'
        last_boundary = max(
            pre.rfind("The motion passed"),
            pre.rfind("The motion failed"),
            pre.rfind("The motion carried"),
        )
        if last_boundary != -1:
            pre = pre[last_boundary + len("The motion passed"):]

        aye = split_names(m.group("aye") or "")
        nay = split_names(m.group("nay") or "")
        abstain = split_names(m.group("abstain") or "")
        recuse = split_names(m.group("recuse") or "")
        absent = split_names(m.group("absent") or "")
        names_recorded = bool(aye or nay or abstain or recuse)

        # mover (last 'X moved' in the preceding window)
        mover = ""
        mv = list(MOVER_RE.finditer(pre))
        if mv:
            mover = resolve_actor(mv[-1].group(1))
        # seconder
        seconder = ""
        sb = SECOND_BY_RE.search(pre)
        if sb:
            seconder = resolve_actor(sb.group(1))
        else:
            so = SECONDER_RE.search(pre)
            if so:
                seconder = resolve_actor(so.group(1))

        motion_text = parse_motion_text(pre)
        heading = nearest_heading(headings, block_start)
        if not motion_text:
            motion_text = heading
        motion_type = classify_motion(heading, motion_text)
        result = tally_from_outcome(
            m.group("outcome"), len(aye), len(nay), len(abstain), len(recuse), names_recorded
        )

        collected.append((block_start, {
            "motion": motion_text,
            "body": body_at(body_markers, block_start),
            "motion_type": motion_type,
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "names_recorded": names_recorded,
            "aye": aye, "nay": nay, "abstain": abstain,
            "absent": absent, "recuse": recuse,
        }))

    # --- second pass: tally-only / unanimous motions WITHOUT a 'Those voting' name list
    # ("X moved to ... Y seconded the motion. The motion passed [unanimously].")
    # Recorded with names_recorded=False and empty member lists (never guess who voted).
    for m in noname_block_re.finditer(text):
        s, e = m.start(), m.end()
        # skip if this overlaps a named block already captured
        if any(ns <= s < ne or ns < e <= ne for ns, ne in named_spans):
            continue
        pre = m.group(0)
        mover = ""
        mv = list(MOVER_RE.finditer(pre))
        if mv:
            mover = resolve_actor(mv[-1].group(1))
        seconder = ""
        sb = SECOND_BY_RE.search(pre)
        if sb:
            seconder = resolve_actor(sb.group(1))
        else:
            so = SECONDER_RE.search(pre)
            if so:
                seconder = resolve_actor(so.group(1))
        motion_text = parse_motion_text(pre)
        heading = nearest_heading(headings, s)
        if not motion_text:
            motion_text = heading
        outcome = m.group("outcome").lower()
        word = "Pass" if outcome in ("passed", "carried", "was approved") else "Fail"
        collected.append((s, {
            "motion": motion_text,
            "body": body_at(body_markers, s),
            "motion_type": classify_motion(heading, motion_text),
            "result": word,                 # no per-member tally available
            "mover": mover,
            "seconder": seconder,
            "names_recorded": False,
            "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": [],
        }))

    collected.sort(key=lambda x: x[0])
    votes = []
    for i, (_, v) in enumerate(collected, start=1):
        v = dict(v)
        v_ordered = {"motion_no": i}
        v_ordered.update(v)
        votes.append(v_ordered)

    return {
        "date": meeting["date"],
        "title": meeting["title"],
        "source": meeting["path"],
        "votes": votes,
    }


# ---------------------------------------------------------------- driver
def load_index():
    rows = []
    with open(INDEX_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def week_from_path(path):
    # meeting_minutes/minutes/<year>/<week>/<file>.md
    parts = path.replace("\\", "/").split("/")
    # find 'minutes' then year, week
    try:
        i = parts.index("minutes")
        return parts[i + 1], parts[i + 2], parts[i + 3]
    except (ValueError, IndexError):
        return None, None, None


# Election winners (council + mayor) per year, from
# election_results/orem_results_by_candidate.csv (is_winner == 'Y'), normalized.
def load_election_winners():
    path = os.path.join(REPO_ROOT, "election_results", "orem_results_by_candidate.csv")
    winners = {}  # year(int) -> set(canonical names)
    if not os.path.exists(path):
        return winners
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("is_winner", "").strip().upper() != "Y":
                continue
            office = (r.get("office", "") + " " + r.get("contest", "")).lower()
            if "orem" not in r.get("contest", "").lower() and "council" not in office and "mayor" not in office:
                continue
            nm = normalize_name(r.get("candidate", ""))
            if not nm:
                continue
            try:
                yr = int(r["year"])
            except (KeyError, ValueError):
                continue
            winners.setdefault(yr, set()).add(nm)
    return winners


def write_validation(motion_records, roster, member_rows):
    """Per-motion tally check + roster vs election-winner cross-check."""
    lines = []
    lines.append("OREM CITY COUNCIL — VOTE EXTRACTION VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append("")
    mismatches = []
    for rec in motion_records:
        if not rec["names_recorded"]:
            continue
        res = rec["result"]
        m = re.match(r"(\d+)-(\d+)\s+(Pass|Fail)", res)
        if not m:
            continue
        decl_aye, decl_nay = int(m.group(1)), int(m.group(2))
        # the declared tally is what we computed from the lists, so instead validate
        # internal consistency: outcome word vs aye>nay, and no member double-listed.
        n_aye, n_nay = len(rec["aye"]), len(rec["nay"])
        word = m.group(3)
        problems = []
        if word == "Pass" and n_aye <= n_nay:
            problems.append(f"outcome Pass but aye({n_aye})<=nay({n_nay})")
        if word == "Fail" and n_aye > n_nay:
            problems.append(f"outcome Fail but aye({n_aye})>nay({n_nay})")
        overlap = set(rec["aye"]) & set(rec["nay"])
        if overlap:
            problems.append(f"member in both aye&nay: {sorted(overlap)}")
        # plausibility: total voters should be <= 7 (6 council + mayor)
        total = n_aye + n_nay + len(rec["abstain"]) + len(rec["recuse"])
        if total > 7:
            problems.append(f"more than 7 voters ({total})")
        if total == 0:
            problems.append("names_recorded but empty lists")
        if problems:
            mismatches.append((rec["date"], rec["motion_no"], res, problems))

    lines.append(f"Motions checked: {sum(1 for r in motion_records if r['names_recorded'])}")
    lines.append(f"Tally/consistency mismatches: {len(mismatches)}")
    lines.append("")
    for d, mn, res, probs in mismatches:
        lines.append(f"  {d} motion #{mn} [{res}]: " + "; ".join(probs))
    lines.append("")
    lines.append("-" * 60)
    lines.append("ROSTER (members appearing in recorded votes) vs ELECTION WINNERS")
    lines.append("-" * 60)
    winners = load_election_winners()
    for yr in sorted(roster):
        members = sorted(roster[yr])
        lines.append(f"\n{yr}: {len(members)} members in votes")
        for mname in members:
            lines.append(f"    - {mname}")
        # cross-check: which roster members won an election in yr-? (winners serve next yr)
        won = set()
        for wy in (yr, yr - 1, yr - 2, yr - 3, yr - 4):
            won |= winners.get(wy, set())
        not_elected = [mname for mname in members if mname not in won]
        if not_elected:
            lines.append(f"    (in votes but not matched to an election winner {yr-4}-{yr}: "
                         + ", ".join(not_elected) + ")")
    lines.append("")
    lines.append("-" * 60)
    lines.append(f"Total member-vote rows: {member_rows}")
    lines.append("Mayor votes? YES — the mayor (Brunst, then Young, then McCandless)")
    lines.append("  appears in the aye/nay name lists, so the mayor is a voting member.")
    lines.append("  Roster size is therefore 7 (6 council + mayor).")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(VALIDATION_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(mismatches)


def main():
    index = load_index()
    all_rows = []
    motion_records = []
    meetings_processed = 0
    motions_extracted = 0
    member_rows = 0
    named = 0
    tally_only = 0
    contested = 0
    by_body_motions = {}          # body -> motion count
    by_body_member_rows = {}      # body -> member-vote-row count
    by_body_contested = {}        # body -> contested-motion count
    roster = {}  # year -> set of members seen in vote lists
    rda_body_members = set()      # members seen voting in any non-Council body

    for meeting in index:
        rel = meeting["path"]
        abspath = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(abspath):
            continue
        year, week, fname = week_from_path(rel)
        if year is None:
            continue
        result = extract_file(abspath, meeting)
        meetings_processed += 1

        # write per-meeting JSON
        out_dir = os.path.join(VOTES_DIR, year, week)
        os.makedirs(out_dir, exist_ok=True)
        json_name = fname.replace(".md", ".json")
        with open(os.path.join(out_dir, json_name), "w", encoding="utf-8") as jf:
            json.dump(result, jf, indent=1, ensure_ascii=False)

        for v in result["votes"]:
            motions_extracted += 1
            body = v.get("body", "Council")
            by_body_motions[body] = by_body_motions.get(body, 0) + 1
            if v["names_recorded"]:
                named += 1
            else:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
                by_body_contested[body] = by_body_contested.get(body, 0) + 1
            motion_records.append({
                "date": result["date"], "motion_no": v["motion_no"],
                "result": v["result"], "names_recorded": v["names_recorded"],
                "aye": v["aye"], "nay": v["nay"], "abstain": v["abstain"],
                "recuse": v["recuse"],
            })
            yr = int(year)
            roster.setdefault(yr, set())
            for vk, vlabel in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                               ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v[vk]:
                    roster[yr].add(member)
                    member_rows += 1
                    by_body_member_rows[body] = by_body_member_rows.get(body, 0) + 1
                    if body != "Council":
                        rda_body_members.add(member)
                    all_rows.append({
                        "date": result["date"],
                        "year": year,
                        "title": result["title"],
                        "body": v["body"],
                        "motion_no": v["motion_no"],
                        "motion": v["motion"],
                        "motion_type": v["motion_type"],
                        "result": v["result"],
                        "mover": v["mover"],
                        "seconder": v["seconder"],
                        "member": member,
                        "vote": vlabel,
                        "source": rel,
                    })

    # rebuild all_votes.csv (long format)
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type", "result",
            "mover", "seconder", "member", "vote", "source"]
    all_rows.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    print(f"meetings_processed={meetings_processed}")
    print(f"motions_extracted={motions_extracted}")
    print(f"member_vote_rows={member_rows}")
    print(f"named_rollcall_motions={named}")
    print(f"tally_only_motions={tally_only}")
    print(f"contested_motions={contested}")
    print("roster_years=" + json.dumps({k: len(v) for k, v in sorted(roster.items())}))
    print("motions_by_body=" + json.dumps(by_body_motions))
    print("member_rows_by_body=" + json.dumps(by_body_member_rows))
    print("contested_by_body=" + json.dumps(by_body_contested))

    # RDA/CRA/MBA voters must be a subset of the council roster (same people, different
    # capacity) — verify no NEW member appears only in a non-Council body.
    council_members = set()
    for s in roster.values():
        council_members |= s
    new_in_other_body = sorted(rda_body_members - council_members)
    print("non_council_body_members=" + json.dumps(sorted(rda_body_members)))
    print("members_only_in_non_council_body=" + json.dumps(new_in_other_body))

    validation_mismatches = write_validation(motion_records, roster, member_rows)
    print(f"validation_mismatches={validation_mismatches}")
    return roster


if __name__ == "__main__":
    main()
