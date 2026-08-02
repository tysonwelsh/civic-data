#!/usr/bin/env python3
"""weber_polimorphic.py — Weber County's 2026 **Polimorphic e-filing** (born-digital).

EVIDENCE (weber_county/campaign_finance/):
  * `AVAILABILITY.md` §7 — "All five Polimorphic e-filings carry machine-readable itemized
    rows, and in three of them the itemized rows **reconcile exactly** to the stated cumulative
    total (Gary C New 13.72+931.39+55.08 = 1,000.19; Jon Beesley 7 rows = 1,120.00 and 2 rows =
    867.92; Michelle Tait 6+6 rows = 1,973.10 each side). A `weber_polimorphic` family would
    therefore land with a proven reconciliation on day one."
  * `CLAUDE.md` — "the other **5 are born-digital Polimorphic e-filings** whose totals were
    parsed straight from their machine-readable `text/` sidecars, no vision needed."
  * The three anchors verified at the source on 2026-08-02 (`pdftotext -layout` on
    `raw/y2026/2026_ugd_92078f_{863a82a7,916755f7,163de27d}.pdf`).

SHAPE — a two-column labelled key/value document ("Document generated with Polimorphic.com"),
NOT a ruled table. Each itemized entry is its own block:

    Itemized Contribution Report (#1)
        Date of Contribution                    January 01, 2026
        Name of Contributor                     Gary C. New
        Amount                                  13.72
        Donor's City                            Hooper, UT

    Itemized Expenditures Report (#1)
        Date of Expenditures                    January 01, 2026
        Person or Organization to whom the      Spaceship Inc
        expenditure was made                            <- the LABEL wraps; the value does not
        Recipient's Location                    Phoenix, AZ
        Amount                                  13.72
        Purpose of Expenditure                  Domain Name Registrations (Loan)

and the summary is a flat list of labelled lines:

    Total Contributions on Last Report      0
    Total Contributions on This Report      1000.19        <- the RECONCILIATION ANCHOR
    Cumulative Total Contributions          1000.19
    Total Campaign Expenditures on Last     0
    Report
    ...

Things this parser gets right, deliberately:
  * **Amounts are BARE decimals** (`13.72`, `1973.1`) — `common.parse_money` requires a `$` and
    would read nothing, so the shared `parse_money_cell` reader is used, with the ZERO-GLYPH
    RULING (GOTCHAS.md, owner 2026-08-02) applied to every cell: `Ø` / `-0-` / "zero" read as 0;
    a bare dash / `N/A` / an empty cell stays BLANK. A malformed decimal is NEVER repaired.
  * **A record may straddle a page break** (New's expenditure #3 does) — records are closed by
    the next record header or the summary block, not by a page.
  * **PRIVACY** — the form prints `Donor's City` / `Recipient's Location` as "City, ST" and never
    a donor street address, so `donor_city` / `donor_state` are all that is emitted. The FILER's
    own street address does appear on page 1 of some filings (Michelle Tait's does) and is never
    read by this parser.
  * **is_incremental / dedup regime are declared PER FILING.** The itemized rows reconcile to the
    "on This Report" line, not the cumulative one, so the e-filings are period-scoped
    (`is_incremental=True`, `dedup_mode="incremental"`) even though Weber's SCANNED cover forms
    are cumulative (`weber_county/campaign_finance/CLAUDE.md` "The five things to respect" #1).
    The cumulative figures are reported in `notes`, never as the anchor.

Geometry: every emitted row carries `geometry` = `p<page>:l<line>:c<col0>-<col1>` for the AMOUNT
token it was read from (SCHEMA.md §2a).
"""
from __future__ import annotations

import datetime
import re

import common
from common import (ContribRow, ExpendRow, parse_money_cell, split_city_state,
                    geom_text, page_line_index)

_C_HEAD = re.compile(r"Itemized\s+Contribution\s+Report\s*\(#\s*(\d+)\s*\)", re.I)
_E_HEAD = re.compile(r"Itemized\s+Expenditures?\s+Report\s*\(#\s*(\d+)\s*\)", re.I)

# summary lines (each label is followed, on the SAME line, by its value in the right column)
_SUM = {
    "contrib_last": re.compile(r"Total\s+Contributions\s+on\s+Last(\s+Report)?", re.I),
    "contrib_this": re.compile(r"Total\s+Contributions\s+on\s+This(\s+Report)?", re.I),
    "contrib_cum": re.compile(r"Cumulative\s+Total\s+Contributions", re.I),
    "expend_last": re.compile(r"Total\s+Campaign\s+Expenditures\s+on\s+Last", re.I),
    "expend_this": re.compile(r"Total\s+Campaign\s+Expenditures\s+on\s+This", re.I),
    "expend_cum": re.compile(r"Cumulative\s+Total\s+Expenditures", re.I),
    "bal_last": re.compile(r"Ending\s+Balance\s+on\s+Last", re.I),
    "bal_this": re.compile(r"Ending\s+Balance\s+on\s+This", re.I),
    "bal_cum": re.compile(r"Cumulative\s+Total\s+Balance", re.I),
}

# per-record field labels
_F_DATE_C = re.compile(r"Date\s+of\s+Contribution", re.I)
_F_DATE_E = re.compile(r"Date\s+of\s+Expenditures?", re.I)
_F_NAME_C = re.compile(r"Name\s+of\s+Contributor", re.I)
_F_NAME_E = re.compile(r"Person\s+or\s+Organization\s+to\s+whom(?:\s+the)?", re.I)
_F_AMOUNT = re.compile(r"^\s*Amount\b", re.I)
_F_CITY_C = re.compile(r"Donor'?s\s+City", re.I)
_F_CITY_E = re.compile(r"Recipient'?s\s+Location", re.I)
_F_PURPOSE = re.compile(r"Purpose\s+of\s+Expenditure", re.I)

_MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}
_LONG_DATE = re.compile(r"^([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})$")


def _long_date(tok):
    """`January 01, 2026` -> `2026-01-01`; anything else -> "" (never a guess)."""
    m = _LONG_DATE.match((tok or "").strip())
    if not m:
        return ""
    mon = _MONTHS.get(m.group(1).lower())
    if not mon:
        return ""
    try:
        return datetime.date(int(m.group(3)), mon, int(m.group(2))).isoformat()
    except ValueError:
        return ""


def _value_after(line, m):
    """The right-column value on a labelled line: everything after the label match, with the
    2+-space column gutter collapsed. A label with nothing to its right yields ""."""
    return re.sub(r"\s{2,}", " ", line[m.end():]).strip()


def _summary(lines):
    out = {}
    for ln in lines:
        for key, rx in _SUM.items():
            if key in out:
                continue
            m = rx.search(ln)
            if m:
                v, kind = parse_money_cell(_value_after(ln, m))
                out[key] = (v, kind)
    return {k: v for k, (v, kind) in out.items() if kind in ("money", "zero-glyph")}


def _records(lines, head_rx, stop_rxs):
    """Slice the sidecar into per-record (index, [(lineno, text), ...]) blocks."""
    recs, cur = [], None
    for k, ln in enumerate(lines):
        m = head_rx.search(ln)
        if m:
            cur = (int(m.group(1)), [])
            recs.append(cur)
            continue
        if cur is None:
            continue
        if any(rx.search(ln) for rx in stop_rxs):
            cur = None
            continue
        cur[1].append((k, ln))
    return recs


def _field(block, rx):
    for k, ln in block:
        m = rx.search(ln)
        if m:
            return k, ln, _value_after(ln, m)
    return None, None, ""


def _amount_of(block):
    """(value, kind, lineno, col_start, col_end) for the record's `Amount` line."""
    for k, ln in block:
        m = _F_AMOUNT.search(ln)
        if not m:
            continue
        raw = _value_after(ln, m)
        v, kind = parse_money_cell(raw)
        col0 = len(ln) - len(ln[m.end():].lstrip()) if raw else m.end()
        return v, kind, k, col0, col0 + len(raw)
    return None, "empty", None, None, None


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    pl = page_line_index(text)
    sm = _summary(lines)

    other_heads = [_C_HEAD, _E_HEAD] + list(_SUM.values())
    crecs = _records(lines, _C_HEAD, other_heads)
    erecs = _records(lines, _E_HEAD, other_heads)

    method = meta.get("extract_method", "weber_polimorphic/text")
    crows, erows, skipped = [], [], []

    for idx, block in crecs:
        _, _, dtok = _field(block, _F_DATE_C)
        _, _, name = _field(block, _F_NAME_C)
        _, _, loc = _field(block, _F_CITY_C)
        amt, kind, k, c0, c1 = _amount_of(block)
        if kind not in ("money", "zero-glyph"):
            skipped.append(f"contribution #{idx}: amount cell {kind} — row not emitted")
            continue
        city, state = split_city_state(loc)
        page, lno = pl[k] if k is not None and k < len(pl) else (1, (k or 0) + 1)
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta.get("office", ""),
            seat=meta.get("seat", ""), election_year=meta["election_year"],
            filing_date=meta.get("filing_date", ""),
            reporting_period=meta.get("reporting_period", ""),
            date=_long_date(dtok), donor_raw=name, donor_city=city, donor_state=state,
            amount=common.money_str(amt), in_kind="False", is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
            line_no=str(k + 1), extract_method=method,
            needs_review="0" if name else "1",
            geometry=geom_text(page, lno, c0, c1)))

    for idx, block in erecs:
        _, _, dtok = _field(block, _F_DATE_E)
        _, _, vendor = _field(block, _F_NAME_E)
        _, _, purpose = _field(block, _F_PURPOSE)
        amt, kind, k, c0, c1 = _amount_of(block)
        if kind not in ("money", "zero-glyph"):
            skipped.append(f"expenditure #{idx}: amount cell {kind} — row not emitted")
            continue
        page, lno = pl[k] if k is not None and k < len(pl) else (1, (k or 0) + 1)
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta.get("office", ""),
            seat=meta.get("seat", ""), election_year=meta["election_year"],
            filing_date=meta.get("filing_date", ""),
            reporting_period=meta.get("reporting_period", ""),
            date=_long_date(dtok), vendor_raw=vendor, purpose=purpose,
            amount=common.money_str(amt), in_kind="False", is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
            line_no=str(k + 1), extract_method=method,
            needs_review="0" if vendor else "1",
            geometry=geom_text(page, lno, c0, c1)))

    notes = ["polimorphic e-filing (born-digital); anchor = 'on This Report'"]
    for key, label in (("contrib_cum", "cumulative contributions"),
                       ("expend_cum", "cumulative expenditures")):
        if key in sm:
            notes.append(f"{label} stated ${sm[key]:,.2f} (NOT summed as an increment)")
    notes += skipped

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=sm.get("contrib_this"),
                stated_expend=sm.get("expend_this"),
                stated_begin=sm.get("bal_last"), stated_end=sm.get("bal_this"),
                stated_contrib_ytd=sm.get("contrib_cum"),
                stated_expend_ytd=sm.get("expend_cum"),
                is_incremental="True", dedup_mode="incremental",
                notes="; ".join(notes))
