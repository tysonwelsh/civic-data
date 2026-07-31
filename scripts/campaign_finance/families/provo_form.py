#!/usr/bin/env python3
"""provo_form.py — F1 extractor: Provo self-hosted "Campaign Finance Disclosure Form".

One PDF per candidate per cycle = a whole-cycle summary (is_incremental = False). Layout
(born-digital, `pdftotext -layout`):

  * a per-reporting-period PIVOT: Starting/Ending Date, Starting Amount, Donations,
    "Expendatures" (sic), Difference, Ending Amount, periods 1..N + a Total column;
  * a "Summary of Donations" itemization: Donor / District / City / State / per-period /
    Total. Donations carry NO individual dates (contributions.date stays BLANK for Provo).
    The Total column is sometimes rounded to whole dollars ($10.73 -> "$11"), so the donor
    amount is taken as the SUM OF THE PER-PERIOD columns (exact cents), not the Total token.
    Trailing ')' artifacts on totals ($100.00)) are stripped.
  * a "List of Expenses" ledger: Date / Vendor / Purpose / Amount / In-kind Amount, with
    REAL dates that can span prior years (officeholder accounts). Amount = the FIRST money
    token after the purpose (Amount column); a second money token equal to it marks a true
    in-kind item; an unequal trailing money token is the form's reporting-period artifact
    ($2.00 on period-2 rows) and is ignored.

Non-donor rows in the donor table are typed by the classifier: "Previous balance from 2018
Campaign" -> carryover ; "Refund from ..." -> other.

SCANNED filings (format=scanned): OCR tears the tables into vertical token streams that
cannot be re-columned without guessing. We therefore extract ONLY the period-pivot stated
totals (which survive OCR) and emit NO itemized rows — the filing is flagged needs_review.
This is the honest floor for the 4 Provo scans; a vision pass is a later, owner-gated phase.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, split_columns, is_money, parse_money,
                    parse_date, find_money, clean_token)

_STATE_RE = re.compile(r"^([A-Za-z]{2}|Utah)$")
_DISTRICT_RE = re.compile(r"^\d{1,2}$")


def _pivot_total(lines, label_re):
    """Last money token on the first pivot row whose stripped text starts with label_re."""
    for ln in lines:
        s = ln.strip()
        if label_re.match(s):
            mons = find_money(s)
            if mons:
                return mons[-1][1]
    return None


def _pivot_first(lines, label_re):
    for ln in lines:
        s = ln.strip()
        if label_re.match(s):
            mons = find_money(s)
            if mons:
                return mons[0][1]
    return None


def _geo_from(tokens):
    """Split leading non-money tokens into (district, city, state). Column order is
    District | City | State."""
    toks = [t for t in tokens if re.search(r"[A-Za-z0-9]", t)]  # drop stray ',' / ')' fragments
    district = city = state = ""
    if toks and _STATE_RE.match(toks[-1]):
        state = toks.pop()
    if toks and _DISTRICT_RE.match(toks[0]):
        district = toks.pop(0)
    city = " ".join(toks).strip()
    return district, city, state


def _known_cities(donor_lines):
    """Cities observed in CLEARLY-named rows (donor token contains a comma). Used to detect
    blank-donor-name rows, where pdftotext left only District/City/State + amounts."""
    cities = set()
    for _lineno, line in donor_lines:
        toks = split_columns(line)
        if toks and "," in toks[0] and not is_money(toks[0]):
            _d, c, _s = _geo_from([t for t in toks[1:] if not is_money(t)])
            if c:
                cities.add(c)
    return cities


def _parse_donor_line(line, lineno, meta, known_cities):
    toks = split_columns(line)
    if not toks or is_money(toks[0]):
        return None
    money_toks = [t for t in toks if is_money(t)]
    if not money_toks:
        return None
    vals = [parse_money(t) for t in money_toks]
    # amount = sum of per-period columns (drop the rounded Total column) — see module docstring
    amount = round(sum(vals[:-1]), 2) if len(vals) >= 2 else vals[0]

    first = clean_token(toks[0]).rstrip(",").strip()
    # Blank-donor-name row: the leftmost token is really a district / state / known city,
    # i.e. the source printed no name. Record donor_raw="" (honest) + needs_review; never
    # promote a geography token to a donor identity.
    name_blank = (first == "" or _DISTRICT_RE.match(first) or _STATE_RE.match(first)
                  or first in known_cities)
    if name_blank:
        donor_raw = ""
        geo = [t for t in toks if not is_money(t)]
    else:
        donor_raw = first
        geo = [t for t in toks[1:] if not is_money(t)]
    district, city, state = _geo_from(geo)

    return ContribRow(
        candidate=meta["candidate"], office=meta["office"], seat=meta["seat"],
        election_year=meta["election_year"], filing_date=meta["filing_date"],
        reporting_period="", date="",  # Provo prints no per-donation date
        donor_raw=donor_raw, donor_city=city, donor_state=state, donor_district=district,
        amount=common.money_str(amount), in_kind="False", is_incremental="False",
        source_filing=meta["source_filing"], document_id=meta["document_id"],
        line_no=str(lineno), extract_method=meta["extract_method"],
        needs_review="1" if (amount is None or name_blank) else "0",
    )


def _parse_expense_line(line, lineno, meta):
    toks = split_columns(line)
    if not toks:
        return None
    iso = parse_date(toks[0])
    if iso is None:
        return None  # not a ledger transaction row (blank / wrapped-purpose continuation)
    # Locate money by POSITION so a value glued to the purpose by a single space
    # ('...supplies. $108.19', Rachel Whipple 2021) is still captured.
    spans = common.money_spans(line)
    if not spans:
        vendor = toks[1] if len(toks) > 1 else ""
        purpose = " ".join(toks[2:]) if len(toks) > 2 else ""
        return ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta["seat"],
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period="", date=iso, vendor_raw=vendor, purpose=purpose,
            amount="", in_kind="False", is_incremental="False",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=str(lineno), extract_method=meta["extract_method"], needs_review="1")
    amount = spans[0][2]  # first (leftmost) money = the Amount column
    head = line[:spans[0][0]]  # date + vendor + purpose, before the amount
    htoks = split_columns(head)
    vendor = htoks[1] if len(htoks) > 1 else ""
    purpose = " ".join(htoks[2:]) if len(htoks) > 2 else ""
    # in-kind: a second money token EQUAL to the amount (Provo records in-kind at full value);
    # an unequal trailing money token is the reporting-period artifact and is not in-kind.
    trailing = [v for (_s, _e, v) in spans[1:]]
    in_kind = any(abs(v - amount) < 0.005 for v in trailing)
    return ExpendRow(
        candidate=meta["candidate"], office=meta["office"], seat=meta["seat"],
        election_year=meta["election_year"], filing_date=meta["filing_date"],
        reporting_period="", date=iso, vendor_raw=vendor, purpose=purpose,
        amount=common.money_str(amount), in_kind=str(bool(in_kind)),
        is_incremental="False", source_filing=meta["source_filing"],
        document_id=meta["document_id"], line_no=str(lineno),
        extract_method=meta["extract_method"],
        needs_review="0" if amount is not None else "1")


def parse(text: str, meta: dict) -> dict:
    """Parse one Provo filing. meta carries the index-derived fields (candidate/office/seat/
    election_year/filing_date/filing_type/source_filing/document_id/extract_method) plus
    `is_scanned` (bool). Returns dict: contrib_rows, expend_rows, stated_contrib,
    stated_expend, stated_begin, stated_end, notes."""
    lines = text.splitlines()

    # NB: Provo's 2023 born-digital cycle drops the "ti" ligature in pdftotext output
    # ("Donations" -> "Dona ons", "Starting" -> "Star ng"), so labels tolerate an optional
    # "ti" / whitespace at that position.
    stated_contrib = _pivot_total(lines, re.compile(r"^Dona(?:ti)?\s*ons\b"))
    if stated_contrib is None:
        stated_contrib = _pivot_total(lines, re.compile(r"^Total of Dona(?:ti)?\s*ons\b"))
    stated_expend = _pivot_total(lines, re.compile(r"^Expend(?:atures|itures)\b"))
    if stated_expend is None:
        # Some filings omit the top period-pivot entirely (e.g. Tom Fifita 2025); the
        # "Total of Purchases" grand-total row survives and gives the expenditure total.
        stated_expend = _pivot_total(lines, re.compile(r"^Total of Purchases\b"))
    stated_begin = _pivot_first(lines, re.compile(r"^Star(?:ti)?\s*ng Amount\b"))
    stated_end = _pivot_total(lines, re.compile(r"^Ending Amount\b"))

    contrib_rows, expend_rows = [], []
    notes = ""

    if meta.get("is_scanned"):
        notes = ("scanned/OCR: period-pivot stated totals only; itemized rows not "
                 "machine-extractable (OCR columns torn) — see raw PDF")
        return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                    stated_contrib=stated_contrib, stated_expend=stated_expend,
                    stated_begin=stated_begin, stated_end=stated_end, notes=notes)

    # ---- donor itemization: between the "Donor ... Total" header and "Summary of Expenses"
    donor_hdr = donor_end = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if donor_hdr is None and s.startswith("Donor") and "Total" in s:
            donor_hdr = i
        elif donor_hdr is not None and re.match(r"^Summary of Expense", s):
            donor_end = i
            break
    if donor_hdr is not None:
        end = donor_end if donor_end is not None else len(lines)
        donor_lines = [(i + 1, lines[i]) for i in range(donor_hdr + 1, end)]
        known_cities = _known_cities(donor_lines)
        for lineno, line in donor_lines:
            row = _parse_donor_line(line, lineno, meta, known_cities)
            if row:
                contrib_rows.append(row)

    # ---- expenditure ledger: after the "Date ... Vendor ... Purpose ... Amount" header
    ledger_hdr = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("Date") and "Vendor" in s and "Purpose" in s and "Amount" in s:
            ledger_hdr = i
            break
    if ledger_hdr is not None:
        for i in range(ledger_hdr + 1, len(lines)):
            row = _parse_expense_line(lines[i], i + 1, meta)
            if row:
                expend_rows.append(row)

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=stated_begin, stated_end=stated_end, notes=notes)
