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


# --------------------------------------------------------------- the ZERO-GLYPH RULING
# GOTCHAS.md, owner 2026-08-02, repo-wide: a glyph that DENOTES the digit zero — a slashed
# zero `Ø`, the accounting `-0-`, or the written word "zero" — reads as **0**, with the
# verbatim glyph preserved by the caller. A bare dash, `N/A`, or an empty cell is a NIL MARK,
# not a numeral, and stays BLANK. Both sets are matched on the WHOLE cell only: a dash inside
# a name and the word "zero" inside prose are untouched.
_ZERO_GLYPHS = ("Ø", "∅", "0̸")        # Ø (O-slash), ∅ (empty set), 0+combining slash
_ZERO_WORD_RE = re.compile(r"^zero$", re.I)          # the ruling names ONLY "zero" — `None`,
#                                                      `NA` and a bare dash are nil marks, blank
_ZERO_DASH_RE = re.compile(r"^-\s*0\s*-$")            # -0-  /  - 0 -
_NIL_RE = re.compile(r"^(?:-{1,3}|–|—|n\s*/?\s*a|na|n\.a\.?|none)$", re.I)

# A strictly-formed decimal CELL: optional $ (with optional spaces), optional sign, an integer
# part that is either plain digits or CLEANLY comma-grouped (\d{1,3}(,\d{3})*), and at most one
# 1-2 digit decimal group. Deliberately REJECTS the malformed forms this corpus contains —
# summit's `23,744,71` (second comma group is 2 digits) and `23.744.71` (two dots) — which must
# stay unparseable-blank, never repaired (cardinal rule 1).
_CELL_NUM_RE = re.compile(
    r"^(?P<p1>\()?\s*(?P<sign1>-)?\s*\$?\s*(?P<p2>\()?\s*(?P<sign2>-)?\s*"
    r"(?P<int>\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.(?P<dec>\d{1,2}))?\s*(?P<p3>\))?$")


def parse_money_cell(tok):
    """Read ONE form cell -> (value_or_None, kind). The shared money reader for the county
    form families (2026-08-02); city families keep using `parse_money`/`find_money` unchanged.

    kind ∈:
      `money`        a clean decimal (value = float; parentheses ⇒ negative)
      `zero-glyph`   Ø / ∅ / -0- / the word "zero"|"none"  -> value 0.0  (ZERO-GLYPH RULING)
      `nil`          a bare dash / N/A / NA                 -> value None (a nil mark is not 0)
      `empty`        nothing printed                        -> value None
      `unparseable`  something IS printed and it is not clean money -> value None, NEVER repaired

    The caller keeps the verbatim token; this function never mutates or repairs one.
    """
    if tok is None:
        return None, "empty"
    t = str(tok).strip().strip("|").strip()
    if t == "":
        return None, "empty"
    if t in _ZERO_GLYPHS or _ZERO_WORD_RE.match(t) or _ZERO_DASH_RE.match(t):
        return 0.0, "zero-glyph"
    if _NIL_RE.match(t):
        return None, "nil"
    m = _CELL_NUM_RE.match(t)
    if not m:
        return None, "unparseable"
    body = m.group("int").replace(",", "")
    if m.group("dec"):
        body += "." + m.group("dec")
    try:
        v = float(body)
    except ValueError:
        return None, "unparseable"
    neg = bool(m.group("sign1")) != bool(m.group("sign2"))
    # accounting parentheses -> negative; the opening paren may sit before OR after the '$'
    # ("(65.00)", "$ (426.27)"), but an unbalanced paren is a broken cell, not a negative.
    opened, closed = bool(m.group("p1") or m.group("p2")), bool(m.group("p3"))
    if opened != closed:
        return None, "unparseable"
    if opened:
        neg = not neg
    return (-v if neg else v), "money"


# Money tokens as they appear INSIDE a laid-out row (not a whole cell): `$` optionally spaced
# away from the digits, or a bare decimal. Position-aware so a column-positional reader can
# match a token's x-span to a header's x-span.
# The lookarounds are load-bearing: without the trailing `(?![\d.,])` this regex would match
# `23,744` out of summit's MALFORMED `23,744,71` (Ioannides 2024, cents comma) and publish a
# repaired figure. A malformed decimal must yield NO token at all (cardinal rule 1).
_CELL_MONEY_FIND = re.compile(
    r"(?<![\d.,])(?:"
    r"\(?-?\$\s*-?\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?\)?"
    r"|\(?-?\$\s*-?\d+(?:\.\d{1,2})?\)?"
    r"|\(?-?\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?\)?"
    r"|\(?-?\d+\.\d{1,2}\)?"
    r")(?![\d,]|\.\d)")


def money_cell_spans(line: str):
    """All money-shaped tokens in a laid-out line as (start, end, value, raw).

    Accepts a space after `$` ("$   500.00" — the summit/wasatch fillable templates) and BARE
    decimals ("1973.1", "168872.24" — the polimorphic / Box A-F forms), which `money_spans`
    deliberately does not. Malformed tokens are dropped by `parse_money_cell`, never repaired.
    """
    out = []
    for m in _CELL_MONEY_FIND.finditer(line):
        raw = m.group(0)
        v, kind = parse_money_cell(raw)
        if kind == "money":
            out.append((m.start(), m.end(), v, raw))
    return out


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

# ------------------------------------------------------- PRIVACY: address -> city/state only
# SCHEMA.md §2 + every county PRIVACY.md: an itemized row may carry `donor_city` / `donor_state`
# and NEVER the street portion. `split_city_state` is the one shared implementation, so no family
# can accidentally promote a street line into a structured row. It only ever RETURNS a city and a
# state — the street tokens are discarded, not stored anywhere.

_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
    "VA", "WA", "WV", "WI", "WY", "DC", "PR", "VI", "GU", "AS", "MP",
}
# tokens that can only be part of a STREET / delivery line, never a city name
_STREET_LEAD = re.compile(r"^(?:\d+[a-z]{0,2}|[nsew]\.?|north|south|east|west|p\.?o\.?|box|"
                          r"#\S*|ste\.?|suite|apt\.?|unit|rr|hc)$", re.I)
_STREET_TYPE = re.compile(r"^(?:st|street|ave|avenue|rd|road|dr|drive|ln|lane|ct|court|cir|"
                          r"circle|way|blvd|boulevard|pkwy|parkway|hwy|highway|pl|place|ter|"
                          r"terrace|trl|trail|loop|bend|run|cv|cove|pt|point)\.?$", re.I)
_ZIP_TAIL = re.compile(r"[\s,]+\d{5}(?:-\d{4})?\.?$")


def split_city_state(addr):
    """`'168 S 50 W Hyde Park, UT 84318'` -> `('Hyde Park', 'UT')`. PRIVACY-SAFE: the street
    portion is dropped, never returned. Returns `('', '')` when no city can be read WITHOUT
    guessing — an honest blank, never a promoted street token.

    Deterministic order: strip a trailing ZIP, then a trailing 2-letter US state, then take the
    text after the LAST comma; if that is empty, fall back to the segment before it and strip a
    leading street run (numbers, directionals, PO Box, and everything through the last street-type
    word). A candidate city is rejected if it is empty, contains a digit, or runs past 4 tokens.
    """
    if not addr:
        return "", ""
    s = str(addr).strip().strip("|").strip()
    s = _ZIP_TAIL.sub("", s).strip().rstrip(",").strip()
    state = ""
    m = re.search(r"[,\s]+([A-Za-z]{2})\.?$", s)
    if m and m.group(1).upper() in _US_STATES:
        state = m.group(1).upper()
        s = s[:m.start()].strip().rstrip(",").strip()
    strip_street = True
    if "," in s:
        tail = s.rsplit(",", 1)[1].strip()
        head = s.rsplit(",", 1)[0].strip()
        # Text after the LAST comma is the city FIELD; do not street-strip it, or `St George`
        # loses its `St` to the street-type list and becomes `George`.
        cand, strip_street = (tail, False) if tail else (head, True)
    else:
        cand = s
    rest = cand.split()
    if strip_street:
        i = 0
        while i < len(rest) and _STREET_LEAD.match(rest[i]):
            i += 1
        rest = rest[i:]
        # if a street-type word appears, the city (if any) is whatever follows the LAST one
        last_type = max((j for j, t in enumerate(rest) if _STREET_TYPE.match(t)), default=None)
        if last_type is not None:
            rest = rest[last_type + 1:]
    city = " ".join(rest).strip(" ,.")
    if not city or any(ch.isdigit() for ch in city) or len(city.split()) > 4:
        return "", state
    return city, state


# --------------------------------------------------------------------------- row GEOMETRY
# A COMPACT, optional per-row provenance pointer for POSITIONAL sources (SCHEMA.md §2a,
# 2026-08-02). Two shapes, both plain ASCII and both re-derivable from the retained source:
#   `p<page>:l<line>:c<col0>-<col1>`  a laid-out text row (pdftotext -layout): 1-based page
#                                     (form feeds), 1-based line WITHIN the sidecar, and the
#                                     0-based character-column span the value occupies
#   `<Sheet>!<A1>`                    a spreadsheet cell reference (the .xls generation)
# Written into the TRAILING, optional `geometry` column, which appears in the output CSV only
# when at least one row carries a value -> every existing city file is byte-unchanged.


def geom_text(page, line_no, col_start=None, col_end=None):
    """Compact geometry for a laid-out text row. Blank args -> a shorter, still-valid pointer."""
    s = f"p{int(page)}:l{int(line_no)}"
    if col_start is not None and col_end is not None:
        s += f":c{int(col_start)}-{int(col_end)}"
    return s


def geom_cell(sheet, row, col):
    """Compact geometry for a spreadsheet cell: 0-based (row, col) -> `Sheet1!C7`."""
    col = int(col)
    letters = ""
    n = col + 1
    while n:
        n, r = divmod(n - 1, 26)
        letters = chr(65 + r) + letters
    return f"{sheet}!{letters}{int(row) + 1}"


def page_line_index(text):
    """Map each 0-based index of `text.splitlines()` -> (page_no, line_no), both 1-based, where a
    page break is a form feed (`\\f`, what `pdftotext` emits). Sidecars without form feeds are one
    page. Used by families to fill `geometry` without re-reading the PDF.

    ⚠ `str.splitlines()` SPLITS ON `\\f` as well as `\\n`, so the form feed never survives as a
    visible character and page number must be reconstructed here. The result is length-checked
    against `splitlines()`; on any mismatch (an exotic separator) it degrades to a single page
    rather than mis-attributing a row to the wrong page."""
    n = len(text.splitlines())
    pages = []
    page = 1
    for phys in text.split("\n"):
        for j, _seg in enumerate(phys.split("\f")):
            if j:
                page += 1
            pages.append(page)
    while len(pages) > n:                 # splitlines() drops a trailing "" after a final \n
        pages.pop()
    if len(pages) != n:
        pages = [1] * n
    return [(p, i + 1) for i, p in enumerate(pages)]


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
    # geometry — TRAILING, OPTIONAL, ADDITIVE (2026-08-02). Where the SOURCE is positional (a
    # column-aligned PDF ledger, a spreadsheet cell), the family records WHERE on the page this
    # row's value was read: `p2:l14:c46-55` or `Sheet1!F5` (see geom_text / geom_cell). The
    # driver emits this column ONLY when at least one row of the CSV carries a value, so every
    # existing (non-positional) city file keeps its exact historical header. Never a value —
    # a provenance pointer, so a mis-columned read is auditable without re-reading the PDF.
    geometry: str = ""


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
    geometry: str = ""        # see ContribRow.geometry — trailing, optional, emitted only if set


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


# The CANONICAL headers exclude the optional trailing `geometry` column, so they are byte-for-byte
# what every city has always written. `*_HEADER_GEO` is the same list + `geometry`; `driver._write`
# selects it only when a row actually carries geometry, and `validate_finance.py` accepts either.
# (Same trailing-optional-column contract as `filing_totals.filing_regime`.)
GEOMETRY_COL = "geometry"
CONTRIB_HEADER = [f.name for f in fields(ContribRow) if f.name != GEOMETRY_COL]
EXPEND_HEADER = [f.name for f in fields(ExpendRow) if f.name != GEOMETRY_COL]
TOTALS_HEADER = [f.name for f in fields(FilingTotals)]
CONTRIB_HEADER_GEO = CONTRIB_HEADER + [GEOMETRY_COL]
EXPEND_HEADER_GEO = EXPEND_HEADER + [GEOMETRY_COL]


def money_str(v):
    """Render a float dollar value as a 2-dp decimal string, or "" for None."""
    if v is None or v == "":
        return ""
    return f"{float(v):.2f}"


def row_to_dict(row):
    """Row -> dict for the CSV writers. The optional trailing `geometry` key is OMITTED when it
    is blank, so a caller writing the canonical (geometry-less) header — provo's inline writer,
    salt_lake_county's module-local writer, and the driver for every city — passes an exactly
    historical dict to `csv.DictWriter` and needs no change."""
    d = asdict(row)
    if GEOMETRY_COL in d and not d[GEOMETRY_COL]:
        del d[GEOMETRY_COL]
    return d
