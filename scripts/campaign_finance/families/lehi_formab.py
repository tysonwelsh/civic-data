#!/usr/bin/env python3
"""lehi_formab.py — F5 extractor: Lehi municipal campaign financial disclosures.

Two born-digital cover variants coexist; BOTH attach the same itemized Form A / Form B grid,
so itemization is parsed uniformly and only the totals block + cumulative/incremental flag
differ:

  * VARIANT 1 — "MUNICIPAL CAMPAIGN FINANCIAL DISCLOSURE" (2019/2021/2023 + some 2025).
    Numbered totals block: "1. Total Contributions (Form A total) $X", "3. Total Expenditures
    (Form B total) $Y", "Balance at the end of the reporting period $Z". Each report restates
    WHOLE-CYCLE-TO-DATE figures (verified: Condie 2021 Oct $9,675 -> Dec $9,835), so
    is_incremental = FALSE — later reports SUPERSEDE earlier snapshots (a cycle total is the
    latest report, NOT a sum).

  * VARIANT 2 — "CAMPAIGN FINANCIAL REPORT / for Reporting Period" (mostly 2025; some 2023
    covers). "Total Contributions for Reporting Period <num>" (often a BARE number, no '$') +
    "since last disclosure" language => PER-PERIOD, so is_incremental = TRUE (sum across the
    cycle chain, do not max). In-kind contributions are marked by an "In Kind" text token in
    the Amount column with the value in a right-hand In-Kind column; a "Carry-over from ..."
    row -> carryover.

Form A grid: Date Received / Name of Contributor / (mailing address, variant 1) / Amount
(+ In-Kind, variant 2).  Form B grid: Date / Payee / Purpose / Amount.

EMPTY Form A tables render header-only (e.g. "$0.00" filings) -> emit ZERO rows (never a
phantom row): a row is only emitted when the line carries a money token AND is not the section
TOTAL line.

Ligature/glyph dropout in pdftotext ("ITEMI ED CONTRIB TION", "(F  A  al)") is tolerated by
loose section headers.

SCANNED filings (is_scanned): OCR sidecars from the text-backfill. Following the Provo
scanned-handling floor, we read ONLY the stated totals (which survive OCR on this simple form)
and emit NO itemized rows; the filing is flagged low + needs_review. (Phase-3 scope is
born-digital; the 65 image-only Lehi filings are the honest deferred set.)
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, split_columns, parse_money, parse_date,
                    money_spans)

# ---- totals block: a $ or a bare decimal after the label -----------------------------------
_NUM = re.compile(r"\$?\s*(-?[\d,]+(?:\.\d{1,2})?)")


# instructional/boilerplate lines that mention a dollar figure but carry NO filed value
# ("...expenditures are $500 or less...", "Aggregate total ... under $500.00", the exemption
# note). They must not be mistaken for a stated total.
_INSTRUCTION = re.compile(r"\b(or less|or more|aggregate|unless|must file|can report|"
                          r"\$500 or)\b", re.I)


def _label_value(lines, label_re):
    """First filed numeric (with or without '$') on the first NON-instructional line matching
    label_re. Bare integers are accepted HERE only (whitelisted totals context) — the general
    tokenizer requires '$'. Returns None when the fill value is a blank template ('$ ____')."""
    for ln in lines:
        s = ln.strip()
        if label_re.search(s) and not _INSTRUCTION.search(s):
            nums = [n for n in _NUM.findall(s) if re.search(r"\d", n)]
            if nums:
                try:
                    return float(nums[-1].replace(",", ""))
                except ValueError:
                    return None
    return None


_TOTC = re.compile(r"\bTotal Contributions\b", re.I)
_TOTE = re.compile(r"\bTotal Expenditures\b", re.I)
_BAL = re.compile(r"\bBalance at the end\b", re.I)

_FORMA_HDR = re.compile(r"ITEMI.?ED\s+CONTRIB.?TION", re.I)
_FORMB_HDR = re.compile(r"ITEMI.?ED\s+E.?PENDIT.?RE", re.I)
_TOTC_LINE = re.compile(r"^\s*TOTAL\s+CONTRIBUTIONS\b", re.I)
_TOTE_LINE = re.compile(r"^\s*TOTAL\s+(CAMPAIGN|EXPENDITURES)\b", re.I)
_COLHDR = re.compile(r"Name of\s+Contributor|Amount of|Date\s+Received|Person/Organization|"
                     r"Purpose of Expenditure|Complete Mailing", re.I)

_INKIND = re.compile(r"\bin[\s\-]?kind\b", re.I)
_INKIND_TOK = re.compile(r"in[\s\-]?kind(\s*\(if applicable\))?", re.I)
_DATEISH = re.compile(r"^(N/?A|\d{1,2}[/\-]\d{1,2}([/\-]\d{2,4})?)")


def _incremental(text: str) -> bool:
    return ("for Reporting Period" in text) or ("since last disclosure" in text.lower())


def _parse_form_row(line, lineno, meta, is_contrib, incremental):
    if _COLHDR.search(line):
        return None
    # A real Form A/B data row STARTS with a date (or a date range, or N/A). Requiring this
    # excludes the form boilerplate that mentions dollar figures — "*If Candidate receives
    # $500 or more*", "If a candidate spent $500 or less...", "received $500.01 or more" —
    # which would otherwise be captured as phantom $500 rows.
    if not _DATEISH.match(line.strip()):
        return None
    sp = money_spans(line)
    if not sp:
        return None                      # no money -> not a data row (empty table stays empty)
    amount = sp[0][2]
    toks = split_columns(line)
    if not toks:
        return None
    # date: leading date-ish token, else blank (ranges / N/A do not resolve to one ISO date)
    first = toks[0].strip()
    iso = parse_date(first) or ""
    has_date_col = bool(parse_date(first) or _DATEISH.match(first))
    body = toks[1:] if has_date_col else toks
    # textual fields = non-money, non-"In Kind"-marker tokens
    text_fields = [t.strip() for t in body
                   if not money_spans(t) and not _INKIND_TOK.fullmatch(t.strip())]
    name = text_fields[0] if text_fields else ""
    address = text_fields[1] if (is_contrib and len(text_fields) > 1) else ""
    in_kind = bool(_INKIND.search(line))

    if is_contrib:
        district, city, state = _geo_from_address(address)
        return ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=iso,
            donor_raw=name, donor_city=city, donor_state=state, donor_district=district,
            amount=common.money_str(amount), in_kind=str(in_kind),
            is_incremental=str(incremental), source_filing=meta["source_filing"],
            document_id=meta["document_id"], line_no=str(lineno),
            extract_method=meta["extract_method"],
            needs_review="0" if (amount is not None and name) else "1")
    else:
        # purpose = the remaining text fields after the payee (variant 1 has a Purpose column)
        purpose = " ".join(text_fields[1:]).strip() if len(text_fields) > 1 else ""
        return ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=iso,
            vendor_raw=name, purpose=purpose, amount=common.money_str(amount),
            in_kind=str(in_kind), is_incremental=str(incremental),
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=str(lineno), extract_method=meta["extract_method"],
            needs_review="0" if amount is not None else "1")


_ST = re.compile(r"\b([A-Z]{2})\b")
_ZIP = re.compile(r"\b(\d{5})(?:-\d{4})?\b")


def _geo_from_address(addr):
    """Best-effort city/state from a Lehi mailing-address string ('2023 N 600 W, LEHI, UT,
    84043'). Conservative: only when a 2-letter state token is present. Never fabricates."""
    if not addr:
        return "", "", ""
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    state = ""
    city = ""
    for i, p in enumerate(parts):
        m = re.fullmatch(r"[A-Za-z]{2}", p)
        if m:
            state = p.upper()
            if i >= 1:
                city = parts[i - 1]
            break
    return "", city, state


def _sections(lines):
    a_hdr = b_hdr = None
    for i, ln in enumerate(lines):
        if a_hdr is None and _FORMA_HDR.search(ln):
            a_hdr = i
        elif b_hdr is None and _FORMB_HDR.search(ln):
            b_hdr = i
    return a_hdr, b_hdr


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    incremental = _incremental(text)
    meta = dict(meta)
    meta.setdefault("reporting_period", "")

    stated_contrib = _label_value(lines, _TOTC)
    stated_expend = _label_value(lines, _TOTE)
    stated_end = _label_value(lines, _BAL)
    notes = "cumulative(whole-cycle)" if not incremental else "incremental(per-period)"

    if meta.get("is_scanned"):
        return dict(contrib_rows=[], expend_rows=[],
                    stated_contrib=stated_contrib, stated_expend=stated_expend,
                    stated_begin=None, stated_end=stated_end,
                    incremental=incremental,
                    notes="scanned/OCR: stated totals only; itemization not machine-extractable")

    a_hdr, b_hdr = _sections(lines)
    contrib_rows, expend_rows = [], []

    if a_hdr is not None:
        end = b_hdr if (b_hdr is not None and b_hdr > a_hdr) else len(lines)
        for i in range(a_hdr + 1, end):
            if _TOTC_LINE.match(lines[i]) or _FORMB_HDR.search(lines[i]):
                break
            row = _parse_form_row(lines[i], i + 1, meta, True, incremental)
            if row:
                contrib_rows.append(row)

    if b_hdr is not None:
        for i in range(b_hdr + 1, len(lines)):
            if _TOTE_LINE.match(lines[i]):
                break
            row = _parse_form_row(lines[i], i + 1, meta, False, incremental)
            if row:
                expend_rows.append(row)

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=stated_end,
                incremental=incremental, notes=notes)
