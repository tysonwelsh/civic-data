#!/usr/bin/env python3
"""common.py — shared tokenizers + row model for the structured campaign-finance layer.

Stdlib only. This module is form-family-agnostic: money/date parsing, OCR-safe currency
handling, whitespace-column splitting, and the dataclasses that back the three output CSVs
(contributions / expenditures / filing_totals).

Design rule (SCHEMA.md, cardinal rules): a figure that does not parse cleanly stays BLANK
(Python None) with needs_review=True — never a guessed digit. `parse_money` returns None on
anything it cannot read as an unambiguous decimal.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field, asdict, fields

# ----------------------------------------------------------------------------- money

# A money token in these forms always carries a '$'. We deliberately do NOT treat a bare
# integer as money (so a stray reporting-period digit like "1" or a district "4" is never
# mistaken for a dollar amount). A leading '-' (before or after the $) marks a reversal.
_MONEY_RE = re.compile(r"^-?\$-?[\d,]+(?:\.\d{1,2})?$")
# Same shape but findable anywhere in a line (for tokenizers that scan free text).
_MONEY_FIND = re.compile(r"-?\$-?[\d,]+(?:\.\d{1,2})?")


def clean_token(tok: str) -> str:
    """Strip the trailing-artifact punctuation Provo's Excel export leaves on totals
    (`$100.00)`  ,  `$3,298.92)` ) plus stray commas. Reversible/whitelisted only."""
    return tok.strip().rstrip(").,;")


def is_money(tok: str) -> bool:
    return bool(_MONEY_RE.match(clean_token(tok)))


def parse_money(tok):
    """Return a float dollar value, or None if the token is not clean, unambiguous money.

    Never guesses. `$1,690.70` -> 1690.7 ; `$500` -> 500.0 ; `-$39.85` -> -39.85 ;
    `$1,690.70)` -> 1690.7 (trailing paren stripped). Anything else -> None.
    """
    if tok is None:
        return None
    t = clean_token(tok)
    if not _MONEY_RE.match(t):
        return None
    neg = t.count("-") % 2 == 1  # handle -$x or $-x
    t = t.replace("-", "").replace("$", "").replace(",", "")
    if t == "":
        return None
    try:
        val = float(t)
    except ValueError:
        return None
    return -val if neg else val


def find_money(line: str):
    """All money tokens in a line, in order, as (raw_str, value) pairs (value may repeat)."""
    out = []
    for m in _MONEY_FIND.finditer(line):
        v = parse_money(m.group(0))
        if v is not None:
            out.append((m.group(0), v))
    return out


def money_spans(line: str):
    """All money tokens as (start, end, value) — position-aware, so a value glued to text
    by a single space ('...supplies. $108.19') is still found (split_columns would miss it)."""
    out = []
    for m in _MONEY_FIND.finditer(line):
        v = parse_money(m.group(0))
        if v is not None:
            out.append((m.start(), m.end(), v))
    return out


# ------------------------------------------------------------- OCR currency-repair whitelist
# Reversible, whitelisted repairs for tesseract-mangled money tokens. Each can only turn an
# OCR-garbled `$`-shaped token back into a clean one — it NEVER fabricates a value out of
# non-money text (SCHEMA.md: a figure that will not parse stays blank + needs_review, never a
# guessed digit). Shared by every OCR-mode family (easyvote_schedab, utah_standard_form, …); a
# row whose amount came from a repaired token is marked `extract_method=…+repair`.


def fix_dot_thousands(tok: str) -> str:
    """`$7.425.00` -> `$7425.00` and `$7.425` -> `$7425`: tesseract reads the thousands COMMA as a
    period, which the strict money regex would otherwise truncate to `$7.42`. Reverse it ONLY when
    every interior dot-group is exactly 3 digits (an unambiguous thousands grouping); a lone
    2-digit decimal (`$7.42`, `$0.50`) is never matched by the caller's regex, so cents are safe."""
    dollar = tok.startswith("$")
    body = tok[1:] if dollar else tok
    neg = body.startswith("-")
    body = body.lstrip("-")
    parts = body.split(".")
    if len(parts) < 2:
        return tok
    if all(len(p) == 3 for p in parts[1:]):                 # 7.425 / 1.234.567 -> all thousands
        newbody = "".join(parts)
    elif len(parts[-1]) == 2 and all(len(p) == 3 for p in parts[1:-1]):  # last group = cents
        newbody = "".join(parts[:-1]) + "." + parts[-1]
    else:
        return tok                                          # ambiguous -> leave verbatim
    return ("$" if dollar else "") + ("-" if neg else "") + newbody


def repair_money_line(line: str):
    """Return (repaired_line, changed). Whitelisted currency repair for OCR text only.
    `§`->`$`; a lone S/s before a cents-bearing money body -> `$`; the thousands-comma-read-as-
    period (`$7.425.00`->`$7425.00`); and the final-comma-as-decimal (`$104,18`->`$104.18`, a
    3-digit trailing group like `$2,500` is left as thousands)."""
    s = line.replace("§", "$")                                   # § is only ever a mis-scanned $
    # a lone S/s (optionally after a stray quote) immediately before a cents-bearing money body
    # -> $  ('s1,742.00' / 'S1,742.00' -> '$1,742.00'); won't touch 'S 450 E' (space, no cents)
    s = re.sub(r"(?<![A-Za-z0-9])['\"]?[Ss](?=\d[\d,]*[.,]\d{2}(?!\d))", "$", s)
    # dot-as-thousands: a $-token with an interior 3-digit dot-group ($7.425.00 / $7.425)
    s = re.sub(r"\$-?\d{1,3}(?:\.\d{3})+(?:\.\d{2})?",
               lambda m: fix_dot_thousands(m.group(0)), s)

    # final-comma-as-decimal: a $-token with no '.' whose LAST comma is followed by exactly two
    # digits ($104,18 -> $104.18); a 3-digit trailing group ($2,500) is left as thousands.
    def _fix(m):
        tok = m.group(0)
        if "." in tok:
            return tok
        return re.sub(r",(\d{2})$", r".\1", tok)

    s = re.sub(r"\$-?[\d,]+", _fix, s)
    return s, (s != line)


def date_in_window(iso: str, meta: dict) -> bool:
    """True if an ISO date falls in a filing's plausible window [election_year-1-01-01 .. filing
    date] (or election_year+1-12-31 when the filing date is unknown). OCR reads 2021 as 2012, so
    an out-of-window date is blanked (amount kept) by the caller, never re-guessed."""
    if not iso or len(iso) < 4 or not iso[:4].isdigit():
        return True
    ey = meta.get("election_year", "")
    if not str(ey).isdigit():
        return True
    ey = int(ey)
    fd = (meta.get("filing_date") or "").strip()
    upper = fd if (len(fd) >= 4 and fd[:4].isdigit()) else f"{ey + 1}-12-31"
    return f"{ey - 1}-01-01" <= iso <= upper


# ------------------------------------------------------------------------------ dates

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def parse_date(tok):
    """Normalize a Provo ledger date to ISO `YYYY-MM-DD`, or None if unparseable.

    Handles `18-Jan-2018`, `6/2/2025`, `06/01/23`, `9/5/2023`. Two-digit years map to
    2000-2069 / 1970-1999 the way `%y` does. Returns None (never a guess) on anything else.
    """
    if not tok:
        return None
    t = tok.strip()
    # d-Mon-YYYY or "d Mon YYYY" (e.g. 18-Jan-2018, 2-Apr-2018, 29 Jul 2021)
    m = re.match(r"^(\d{1,2})[-\s]([A-Za-z]{3})[-\s](\d{4})$", t)
    if m:
        d, mon, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        if mon in _MONTHS:
            try:
                return datetime.date(y, _MONTHS[mon], d).isoformat()
            except ValueError:
                return None
    # M/D/YYYY or M/D/YY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$", t)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(m.group(3)) == 2:
            y += 2000 if y < 70 else 1900
        try:
            return datetime.date(y, mo, d).isoformat()
        except ValueError:
            return None
    return None


# ------------------------------------------------------------------- column tokenizing

def split_columns(line: str):
    """Split a `pdftotext -layout` row into fields on runs of 2+ spaces.

    Works for born-digital Provo forms whose columns are whitespace-aligned (even the
    'compressed' rows keep >=2 spaces between fields). NOT reliable on OCR single-spaced
    text — families must not lean on this for scanned corpora.
    """
    return [c for c in re.split(r"\s{2,}", line.strip()) if c != ""]


# -------------------------------------------------------------------------- row models

@dataclass
class ContribRow:
    candidate: str = ""
    office: str = ""
    seat: str = ""
    election_year: str = ""
    filing_date: str = ""
    reporting_period: str = ""
    date: str = ""            # contribution date — BLANK for Provo (form prints none)
    donor_raw: str = ""       # verbatim, incl. typos / trailing artifacts already stripped
    donor_normalized: str = ""
    donor_type: str = ""
    donor_city: str = ""
    donor_state: str = ""
    donor_district: str = ""
    amount: str = ""          # decimal string, or "" (blank) when not cleanly parsed
    in_kind: str = ""         # "True"/"False"
    is_incremental: str = ""  # per-city constant ("False" for Provo whole-cycle forms)
    source_filing: str = ""   # = index.csv path (raw/<file>.pdf)
    document_id: str = ""
    line_no: str = ""         # 1-based line in the text sidecar (stable within-filing key)
    extraction_confidence: str = ""  # high | medium | low
    extract_method: str = ""  # family id + text|ocr
    needs_review: str = "0"


@dataclass
class ExpendRow:
    candidate: str = ""
    office: str = ""
    seat: str = ""
    election_year: str = ""
    filing_date: str = ""
    reporting_period: str = ""
    date: str = ""            # ledger date, ISO (Provo prints real dates, can span years)
    vendor_raw: str = ""
    vendor_normalized: str = ""
    purpose: str = ""         # verbatim
    amount: str = ""
    in_kind: str = ""
    is_incremental: str = ""
    source_filing: str = ""
    document_id: str = ""
    line_no: str = ""
    extraction_confidence: str = ""
    extract_method: str = ""
    needs_review: str = "0"


@dataclass
class FilingTotals:
    candidate: str = ""
    office: str = ""
    election_year: str = ""
    filing_date: str = ""
    reporting_period: str = ""
    filing_type: str = ""
    stated_total_contributions: str = ""
    stated_total_expenditures: str = ""
    stated_beginning_balance: str = ""
    stated_ending_balance: str = ""
    itemized_contrib_sum: str = ""
    itemized_expend_sum: str = ""
    reconciles_contrib: str = ""     # True | False | "" (unknown/no stated total)
    reconciles_expend: str = ""
    recon_delta_contrib: str = ""
    recon_delta_expend: str = ""
    self_funded_amount: str = ""
    n_contrib_rows: str = ""
    n_expend_rows: str = ""
    source_filing: str = ""
    document_id: str = ""
    extraction_confidence: str = ""
    notes: str = ""
    # filing_regime — TRAILING, additive. Cities that record two campaign-finance regimes
    # (Taylorsville: `annual` mandatory March-1 statements vs `election_cycle` during-a-race
    # disclosures) set it so cycle_totals can sum ONLY the election_cycle stream (annual
    # statements are a parallel stream, never rolled into a race total). Single-regime cities
    # leave it "" -> their filing_totals is unchanged, and validate_finance accepts a
    # filing_totals header both WITH and WITHOUT this trailing column (no regression).
    filing_regime: str = ""


CONTRIB_HEADER = [f.name for f in fields(ContribRow)]
EXPEND_HEADER = [f.name for f in fields(ExpendRow)]
TOTALS_HEADER = [f.name for f in fields(FilingTotals)]


def money_str(v):
    """Render a float dollar value as a 2-dp decimal string, or "" for None."""
    if v is None or v == "":
        return ""
    return f"{float(v):.2f}"


def row_to_dict(row):
    return asdict(row)
