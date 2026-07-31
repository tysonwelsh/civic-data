#!/usr/bin/env python3
"""normalize_donors.py — deterministic tier-1 donor/vendor normalization + donor_type,
self-funding, and family-of-candidate classification + alias-file application.

Conservative and reviewable (SCHEMA.md §Donor normalization / §donor_type). No fuzzy
auto-merging: cross-spelling merges happen ONLY via a curated `donor_aliases.csv`. The
tier-1 pass strips artifacts, collapses whitespace, de-caps SHOUTED tokens, and reorders a
*simple* `Last, First` to `First Last` (never a joint / "and" donor, to avoid mangling).

donor_type enum (owner-locked 2026-07-05):
  candidate-self | family-of-candidate | individual | business | pac | party |
  loan | carryover | anonymous | aggregate-unitemized | other | unknown
"""
from __future__ import annotations

import csv
import os
import re

# ------------------------------------------------------------------ tier-1 normalization

_BUSINESS_TOKENS = re.compile(
    r"\b(LLC|L\.L\.C|Inc|Incorporated|Corp|Corporation|Company|Co\.?$|Ltd|"
    r"Association|Assoc|Assn|Homebuilders|Home Builders|Realtors|Realty|Enterprises|"
    r"Solutions|Group|Holdings|Partners|Fund|Committee|Consulting|Consultants)\b", re.I)
_PAC_TOKENS = re.compile(r"\b(PAC|Political Action Committee)\b", re.I)
_PARTY_TOKENS = re.compile(r"\b(Republican Party|Democratic Party|Democrat Party|"
                           r"United Utah Party|Libertarian Party|\w+ Party)\b", re.I)


def _decap_word(w: str) -> str:
    """A fully-SHOUTED word (REALTORS, BERGESON) -> Title case; mixed case (MacKay,
    McGowan) and short tokens (UT, and) left alone."""
    if len(w) > 2 and w.isupper() and w.isalpha():
        return w.capitalize()
    return w


def tier1(name: str) -> str:
    """Deterministic normalization of a donor/vendor string. Verbatim in -> cleaned out.
    Never fabricates identity; `donor_raw` remains the source of truth."""
    if name is None:
        return ""
    s = name.strip()
    s = s.lstrip("*").strip()                       # org marker '*'
    s = re.sub(r"[.,;]+$", "", s).strip()           # trailing punctuation
    s = re.sub(r"\s+", " ", s)                       # collapse whitespace
    # Simple "Last, First" -> "First Last" (single comma, RHS 1-2 tokens, no joint 'and',
    # RHS does not already repeat the surname). Anything else is left as printed.
    m = re.match(r"^([A-Za-z''.\-]+),\s+([A-Za-z][A-Za-z''.\- ]*)$", s)
    if m:
        last, first = m.group(1), m.group(2).strip()
        first_toks = first.split()
        if " and " not in f" {first.lower()} " and len(first_toks) <= 2 \
                and first_toks[-1].lower() != last.lower():
            s = f"{first} {last}"
    return " ".join(_decap_word(w) for w in s.split())


# ------------------------------------------------------------- candidate name matching

def _name_tokens(name: str):
    """(first_tokens, last_token) from either 'Last, First' or 'First Last', lowercased."""
    s = name.strip().lstrip("*").strip()
    s = re.sub(r"[.,;]+$", "", s)
    if "," in s:
        last, _, first = s.partition(",")
        firsts = [t for t in re.split(r"[\s]+", first.strip()) if t]
        return [t.lower() for t in firsts], last.strip().lower()
    toks = [t for t in re.split(r"[\s]+", s) if t]
    if not toks:
        return [], ""
    return [t.lower() for t in toks[:-1]], toks[-1].lower()


def _first_match(a_firsts, b_firsts) -> bool:
    """Any first-name token in common (equal, or one a >=3-char prefix of the other —
    handles Jeff/Jeffrey)."""
    for a in a_firsts:
        for b in b_firsts:
            if a == b:
                return True
            if len(a) >= 3 and len(b) >= 3 and (a.startswith(b) or b.startswith(a)):
                return True
    return False


# ------------------------------------------------------------------ donor_type classifier

def classify_donor_type(donor_raw: str, candidate: str) -> str:
    raw = (donor_raw or "").strip()
    low = raw.lower()

    if not raw:
        return "unknown"
    # word-boundary required (Q3-2026): the bare substring matched surnames
    # containing "loan" — white_city's donor Yianni LOANnou was classified as
    # a loan (worked around there via donor_aliases; fixed structurally here)
    if re.search(r"\bloans?\b", low):
        return "loan"
    if "previous balance" in low or "carried forward" in low or "carryover" in low \
            or "carry-over" in low or "carry over" in low or "beginning balance" in low:
        return "carryover"
    if low.startswith("refund") or "refund from" in low:
        return "other"
    if "anonymous" in low or low == "cash":
        return "anonymous"
    if low.startswith("unitemized") or "aggregate" in low and "period" in low:
        return "aggregate-unitemized"
    if low in ("self", "myself", "self funding", "self-funding", "candidate"):
        return "candidate-self"

    # candidate-self vs family-of-candidate (owner-locked): compare surnames + first names.
    d_first, d_last = _name_tokens(raw)
    c_first, c_last = _name_tokens(candidate)
    if d_last and c_last and d_last == c_last:
        if _first_match(d_first, c_first):
            return "candidate-self"
        return "family-of-candidate"

    if _PAC_TOKENS.search(raw):
        return "pac"
    if _PARTY_TOKENS.search(raw):
        return "party"
    if _BUSINESS_TOKENS.search(raw) or raw.strip().startswith("*"):
        return "business"

    # A person-shaped name (comma form, or 2+ alpha tokens, incl. a joint household joined by
    # "&"/"and" like "Rob & Marianne Ludlow") -> individual; else unknown.
    core = [t for t in raw.replace("&", " ").split() if t.lower() != "and"]
    if "," in raw or (len(core) >= 2 and all(re.match(r"^[A-Za-z''.\-]+$", t) for t in core)):
        return "individual"
    return "unknown"


# ---------------------------------------------------------------------- alias file layer

ALIAS_HEADER = ["city", "donor_raw", "donor_normalized", "donor_type", "evidence", "added"]


def load_aliases(path: str):
    """Read donor_aliases.csv -> {donor_raw: (donor_normalized, donor_type)}. Missing file
    or header-only -> empty. Curated, human-reviewed; the ONLY place cross-spelling merges
    happen."""
    aliases = {}
    if not path or not os.path.exists(path):
        return aliases
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("donor_raw") or "").strip()
            if key:
                aliases[key] = (
                    (row.get("donor_normalized") or "").strip(),
                    (row.get("donor_type") or "").strip(),
                )
    return aliases


def normalize_contrib(row, candidate: str, aliases=None):
    """Fill donor_normalized + donor_type on a ContribRow in place. Alias overrides win."""
    aliases = aliases or {}
    raw = row.donor_raw
    if raw in aliases:
        norm, dtype = aliases[raw]
        row.donor_normalized = norm or tier1(raw)
        row.donor_type = dtype or classify_donor_type(raw, candidate)
    else:
        row.donor_normalized = tier1(raw)
        row.donor_type = classify_donor_type(raw, candidate)
    return row


def normalize_vendor(row):
    """Fill vendor_normalized on an ExpendRow via tier-1 (no alias layer for vendors in v1)."""
    row.vendor_normalized = tier1(row.vendor_raw)
    return row
