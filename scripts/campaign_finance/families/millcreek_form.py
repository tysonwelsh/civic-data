#!/usr/bin/env python3
"""millcreek_form.py — F9 extractor: Millcreek City "FINANCIAL CAMPAIGN REPORT" (Form A/B).

The Millcreek statutory municipal C&E form (UCA 10-3-208), self-hosted on the city CivicPlus
DocumentCenter. Structurally a close cousin of West Valley's Form A/B but with two Millcreek-
specific twists that make it its own family:

  * THREE-COLUMN COVER BOX — every numbered cover line prints
        "TOTALS FROM LAST REPORT  +  TOTALS FROM THIS REPORT  =  CUMULATIVE REPORT"
    so a line carries up to THREE money tokens (LAST, THIS, CUMULATIVE). The reconciliation
    anchor therefore depends on WHAT the filing itemizes:
      - 2023 / 2025 / 2019 reports itemize ONLY the current period  -> anchor = THIS column
        (the second-to-last token) and is_incremental = True.
      - 2021 is a single COMBINED whole-cycle bundle per candidate (verified Bagley-Gibson:
        Form A lists a prior-period block summing to the LAST column $350 AND a this-period
        block summing to $121.60, together = the CUMULATIVE $471.60) -> anchor = CUMULATIVE
        (rightmost token) and is_incremental = False. (This is the double-count trap the city
        CLAUDE.md flags: 2021 must be treated as one cumulative report, never summed with
        phantom interims.)

  * PER-SECTION SUBTOTAL / TOTAL LINES — Form A/B print interior "TOTAL"/"Total" lines
    (a 2021 bundle prints one per sub-period; every filing prints a final section Total). These
    are NOT itemized rows and are dropped from row parsing (they would otherwise double the sum).
    The cover box, not these lines, is the reconciliation anchor.

Itemized layout (born-digital, pdftotext -layout — Millcreek rows are single-line/horizontal):
  * FORM "A": Date Received | Name of Contributor | Company | Amount
  * FORM "B": Date of Expenditure | Person/Org To Whom made | Purpose | Amount
Each data row carries its own `$`-amount at the right; the name/vendor is the first whitespace
column of the head, company/purpose the remainder. A leading dateless row (blank date cell) is
kept (anchored on its amount, date left blank) — unlike the date-anchored WVC collector.

Modes by meta["is_scanned"]:
  * text (born-digital): an amount is an unambiguous `$`-anchored token ONLY. The Millcreek OCR
    corpus mangles `$` -> `S`/`§`/`9`/`5`; in text mode we do NOT repair, so a mangled amount
    simply fails to parse and the row is emitted with a BLANK amount + needs_review (honest) —
    never a guessed digit. Such filings fail reconciliation and are the gated-vision set.
  * scanned (OCR / tesseract): shared currency-repair whitelist applied, then the rightmost
    cents token is accepted (WVC-style). Empty scans (2019 no-text-layer) yield ZERO rows and
    flag honestly at the OCR floor -> vision (cf-vision-transcribe).

Reconciliation, dedup, normalization all run in the shared driver — this module only parses.
"""
from __future__ import annotations

import re

import common
from common import ContribRow, ExpendRow, repair_money_line, split_columns
import westvalley_form as wv

# a cover-box money token that TOLERATES a space after the '$' ("$ 5,046.49", "$    60.19") and a
# parenthesized negative ("$ (426.27)") — the printed cover routinely spaces the fill value away
# from the '$', which common.find_money (no-space) would silently drop, losing the THIS column.
_COVER_MONEY = re.compile(r"\$\s*\(?\s*-?[\d,]+(?:\.\d{2})?\)?")

_TOTAL_LINE = re.compile(r"\bTOTALS?\b", re.I)
# a $-anchored money token (optional single space after $, optional cents): "$250.00", "$ 50.00",
# "$350". parse_money validates it; a mangled "§4,000.00"/"9100.00" carries no literal '$' and is
# rejected here (text mode) so it never becomes a guessed amount.
_DOLLAR = re.compile(r"-?\$-?\s?[\d,]+(?:\.\d{2})?")
# a bare cents token (OCR mode only, after repair): "50.00", "1,234.56" — two decimals required.
_CENTS = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})(?![\d])")


def _cover_tokens(lines, label_re):
    """Money values on a cover line: search the label line + next 2 lines for the FIRST line
    carrying money (the filled value often wraps onto the "2)" continuation line) and return
    its money tokens in printed order [LAST, THIS, CUMULATIVE]."""
    for i, ln in enumerate(lines):
        if label_re.search(ln):
            for j in range(i, min(i + 3, len(lines))):
                vals = _cover_vals(lines[j])
                if vals:
                    return vals
            return []
    return []


def _cover_vals(line):
    """Money values on one cover line, in printed order, tolerating '$ '-spacing + parenthesized
    negatives. A bare '$' / '$.' with no digits (blank fill) is skipped, never fabricated."""
    out = []
    for m in _COVER_MONEY.finditer(line):
        s = m.group(0)
        neg = "(" in s
        body = re.sub(r"[^\d.]", "", s)
        if body in ("", "."):
            continue
        try:
            v = float(body)
        except ValueError:
            continue
        out.append(-v if neg else v)
    return out


def _stated(tokens, cumulative):
    """THIS-report anchor (second-to-last token) for per-period filings; CUMULATIVE (rightmost)
    for the 2021 whole-cycle bundle. None when the cover value was unreadable."""
    if not tokens:
        return None
    if cumulative:
        return tokens[-1]
    return tokens[-2] if len(tokens) >= 2 else tokens[-1]


def _amount(line, ocr):
    """(value_or_None, head_before_amount_or_None). Rightmost $-token (both modes); rightmost
    repaired cents token (OCR mode only)."""
    work = repair_money_line(line)[0] if ocr else line
    ms = [m for m in _DOLLAR.finditer(work)
          if common.parse_money(m.group(0).replace(" ", "")) is not None]
    if ms:
        m = ms[-1]
        return common.parse_money(m.group(0).replace(" ", "")), work[:m.start()]
    if ocr:
        cs = list(_CENTS.finditer(work))
        if cs:
            m = cs[-1]
            return float(m.group(1).replace(",", "") + "." + m.group(2)), work[:m.start()]
    return None, None


def _rows(section_lines, meta, is_contrib, ocr, incremental):
    rows = []
    for lineno, ln in section_lines:
        if _TOTAL_LINE.search(ln):
            continue                                   # interior subtotal / section Total line
        amount, head = _amount(ln, ocr)
        if amount is None and head is None:
            continue                                   # no amount token -> not a data row
        iso, rest = wv._peel_date(head, meta, ocr)
        fields = split_columns(rest)
        name = fields[0].strip() if fields else ""
        extra = " ".join(f.strip() for f in fields[1:]).strip()
        if not name and amount is None:
            continue
        if is_contrib:
            rows.append(ContribRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                donor_raw=name, amount=common.money_str(amount), in_kind="False",
                is_incremental=incremental, source_filing=meta["source_filing"],
                document_id=meta["document_id"], line_no=str(lineno + 1),
                extract_method=meta["extract_method"],
                needs_review="0" if (amount is not None and name) else "1"))
        else:
            rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                vendor_raw=name, purpose=extra, amount=common.money_str(amount), in_kind="False",
                is_incremental=incremental, source_filing=meta["source_filing"],
                document_id=meta["document_id"], line_no=str(lineno + 1),
                extract_method=meta["extract_method"],
                needs_review="0" if (amount is not None and name) else "1"))
    return rows


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    ocr = bool(meta.get("is_scanned"))
    cumulative = str(meta.get("election_year", "")).strip() == "2021"
    incremental = "False" if cumulative else "True"

    c_tokens = _cover_tokens(lines, wv._TOT_C)
    e_tokens = _cover_tokens(lines, wv._TOT_E)
    b_tokens = _cover_tokens(lines, wv._BAL)
    stated_contrib = _stated(c_tokens, cumulative)
    stated_expend = _stated(e_tokens, cumulative)
    stated_end = _stated(b_tokens, cumulative)

    contrib_lines, expend_lines = wv._tag_sections(lines)
    contrib_rows = _rows(contrib_lines, meta, True, ocr, incremental)
    expend_rows = _rows(expend_lines, meta, False, ocr, incremental)

    notes = ("cumulative whole-cycle bundle (2021)" if cumulative
             else "incremental(per-period); cover THIS-report anchor")
    if ocr and not contrib_rows and not expend_rows:
        notes += "; scanned: no rows recovered (no text layer / OCR floor)"

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=stated_end, notes=notes)
