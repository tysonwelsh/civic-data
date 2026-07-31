#!/usr/bin/env python3
"""stgeorge_formab.py — extractor for ST. GEORGE's self-hosted municipal "Campaign Finance
Report" (UCA 10-3-208), the scanned state-style form the City Recorder posts as multi-candidate
COMPILATION packets. This family parses ONE candidate's section (already sliced out of the
compilation by the city driver's segmenter — see st_george_city_council/campaign_finance/
build_finance.py); it never sees the whole file.

WHY A NEW FAMILY (not utah_standard_form, not parkcity_form):
  * NOT utah_standard_form — St. George has no Cash-Contributions / In-Kind / Cash-Expenditures
    section trio. It has exactly TWO itemized tables: Form "A" (ITEMIZED CONTRIBUTION REPORT) and
    Form "B" (ITEMIZED EXPENDITURE REPORT). In-kind is a DESCRIPTION column inside Form A, never a
    section with its own TOTAL.
  * NOT parkcity_form — St. George's Form B prints the PURPOSE column AFTER the amount
    (Date | Payee | Amount | Purpose), whereas Park City / the layout parkcity_form assumes puts
    purpose (if any) before the amount. St. George also has two form vintages whose column order
    differs (see below), and the reconciliation anchor wording differs.

FORM VINTAGES (both handled by the same mode-machine; page order can even swap A/B):
  2023 / 2025 ("CAMPAIGN FINANCE REPORT"):
     cover: "Itemized total of contributions totaling $500 or more  $<C>"
            "Itemized total of expenditures  totaling $500 or more  $<E>"
            "Balance at the end of the reporting period:            $<bal>"
     Form A: Date Received | Name of Contributor | Amount ($-signed) | In-Kind Description
     Form B: Date | Payee | Amount ($-signed) | Purpose(optional)
  2021 ("CAMPAIGN FINANCIAL REPORT", Wayback):
     cover: "Total Contributions of all donors  $<C>" / "Total campaign expenses  $<E>" /
            "Balance at the end of the reporting period  $<bal>"
     Form A: Date | Name of Contributor | Mailing Address & Zip | Amount (BARE, no $)
     Form B: Date | Payee | Mailing Address & Zip | Amount (BARE, no $)   (no purpose column)
  Both vintages footer each table with "Total contributions/expenditures for reporting period $<t>"
  — that per-table footer is the PRIMARY reconciliation anchor; the cover line is the fallback.

RECONCILIATION ANCHOR = the form's own printed Form-A / Form-B "Total … for reporting period"
(the "printed tally vs counted rows" discipline). The itemized total INCLUDES in-kind (the cover
"Itemized total of contributions" and the Form-A footer both sum every row, in-kind included), so
the driver reconciles ALL rows (reconcile_cash_only=False). A figure that will not parse cleanly
stays BLANK + needs_review — never a guessed digit.

OCR MODE (every St. George filing is scanned): shared common.py currency-repair whitelist
(`$104,18`->`$104.18`, `§`->`$`, thousands-comma-as-period) + date-sanity (out-of-window year
blanked, amount kept). One candidate (Aros Mackey) marks nearly every cash donation "In-kind" in
the description column — the printed flag is recorded VERBATIM (in_kind=True) and left for review,
never re-interpreted. A section whose garbled totals defeat OCR reconciles UNKNOWN/flagged and is
the honest candidate for the gated vision pass (driver rows_override_fn), never fabricated.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_date, repair_money_line, date_in_window)

# ------------------------------------------------------------------- section / anchor vocabulary
# Match ONLY the real Form-A / Form-B section-header lines ("ITEMIZED CONTRIBUTION REPORT (Form
# "A")"). Deliberately NOT a loose "form a" — that matches the substring "form"+"a" inside a
# donor/vendor word ("Large format" -> "forma") and would flip the section machine mid-table; and
# NOT the cover's "(Form 'A' total from other side of sheet)". "CONTRIBUTION/EXPENDITURE REPORT" is
# unique to the two section headers.
_A_HDR = re.compile(r"CONTRIBUTION\s+REPORT", re.I)
_B_HDR = re.compile(r"EXPENDITURE\s+REPORT", re.I)
_COLHDR = re.compile(r"name of contrib\w*|mailing address|amount of contrib\w*|in.?kind description|"
                     r"person or organization|expenditure was made|amount of expend\w*|"
                     r"^\s*date\b|received\b|purpose\b", re.I)
# per-table printed footer (PRIMARY reconciliation anchor)
_TOT_C = re.compile(r"total\s+contrib\w*\s+for\s+report\w*\s+period", re.I)
_TOT_E = re.compile(r"total\s+expend\w*\s+for\s+report\w*\s+period", re.I)
_TOTAL_ANY = re.compile(r"\btotal\b.*\bfor\s+report", re.I)
# cover fallbacks
_COV_C = re.compile(r"itemized total of contrib\w*|total contrib\w* of all donors", re.I)
_COV_E = re.compile(r"itemized total of expend\w*|total campaign expens\w*", re.I)
_COV_BAL = re.compile(r"balance at the end of the report\w* period", re.I)
_INKIND = re.compile(r"in[\s\-]?kind", re.I)

_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_DATE_LEAD = re.compile(
    r"^[\s|)>._]*("
    r"\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}"              # 08/01/23, 06.1.23, 8.20.23, 6/7/2023
    r"|\d{1,2}[/\-.]\d{1,2}(?![/\-.\d])"              # 8/31, 6.30 (no year)
    r"|\d{1,2}[\-\s]" + _MON + r"(?:[\-\s]\d{2,4})?"  # 30-May, 2 Apr 2018
    r"|" + _MON + r"\.?\s*[/]{0,2}\s*\d{2,4}"         # AUG//2023, June//2023, July/2023 (month-word)
    r")", re.I)
_ISO = re.compile(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$")

# amount token: $-signed (money_spans covers it) OR a BARE number carrying 2 decimals (2021 forms).
# A bare 2-decimal requirement means a street number / 5-digit ZIP integer is NEVER read as money.
_BARE_DEC = re.compile(r"(?<![\d.])\d[\d,]*\.\d{2}(?!\d)")
_MONEY_TOK = re.compile(r"\$\s?-?[\d,]+(?:\.\d{1,2})?|(?<![\d.$])\d[\d,]*\.\d{2}(?!\d)")
_DOLLAR_SPACE = re.compile(r"\$\s+(?=[\d.])")
_NUM_SPACE = re.compile(r"(?<=\d)\s+(?=[\d,]*\.\d{2}\b)")   # "7 856.54" -> "7856.54" (join split total)


def _norm(line, ocr):
    s = _DOLLAR_SPACE.sub("$", line)
    if ocr:
        s = repair_money_line(s)[0]
    return s


def _amount_tokens(wln):
    """(start, end, value) for every $-signed or bare-2dp numeric token, in order. Never guesses."""
    out = []
    for m in _MONEY_TOK.finditer(wln):
        v = common.parse_money(m.group(0)) if "$" in m.group(0) else _bare(m.group(0))
        if v is not None:
            out.append((m.start(), m.end(), v))
    return out


def _bare(tok):
    t = tok.strip().replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def _norm_date(dtok):
    import datetime
    m = _ISO.match(dtok)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return ""
    return parse_date(dtok) or parse_date(dtok.replace(".", "/").replace("-", "/")) or ""


def _peel_date(prefix):
    m = _DATE_LEAD.match(prefix)
    if m:
        return m.group(1).strip(), prefix[m.end():].strip()
    return "", prefix.strip()


def _total_value(ln):
    """The rightmost $-signed value on a footer/cover total line (space-joined splits re-joined),
    or None. The '$500' threshold baked into the cover wording is dropped."""
    s = _NUM_SPACE.sub("", _DOLLAR_SPACE.sub("$", ln))
    s = repair_money_line(s)[0]
    vals = []
    for m in re.finditer(r"\$\s?-?[\d,]+(?:\.\d{1,2})?", s):
        v = common.parse_money(m.group(0))
        if v is not None and v != 500.0:
            vals.append(v)
    return vals[-1] if vals else None


def _first_total(lines, rx):
    for ln in lines:
        if rx.search(ln):
            v = _total_value(ln)
            if v is not None:
                return v
    return None


def parse(text: str, meta: dict) -> dict:
    ocr = bool(meta.get("is_scanned", True))
    lines = text.splitlines()
    method = meta["extract_method"]

    contrib_rows, expend_rows = [], []
    stated_contrib = stated_expend = None
    mode = None                       # 'c' (Form A), 'e' (Form B), or None (cover/preamble)

    for k, raw in enumerate(lines):
        wln = _norm(raw, ocr)

        # --- section headers switch the mode machine (page order may swap A/B) ---
        is_a = bool(_A_HDR.search(raw))
        is_b = bool(_B_HDR.search(raw))
        if is_a and not is_b:
            mode = "c"
            continue
        if is_b and not is_a:
            mode = "e"
            continue

        # --- per-table printed footer = the reconciliation anchor (also closes the table) ---
        if _TOT_C.search(wln):
            v = _total_value(wln)
            if v is not None and stated_contrib is None:
                stated_contrib = v
            mode = None
            continue
        if _TOT_E.search(wln):
            v = _total_value(wln)
            if v is not None and stated_expend is None:
                stated_expend = v
            mode = None
            continue

        if mode is None:
            continue
        if _COLHDR.search(wln):
            continue

        dtok, body_after_date = _peel_date(wln)
        if not dtok:
            continue                                   # data rows are date-led
        toks = _amount_tokens(wln)
        # amount = the FIRST money/bare-2dp token AFTER the date (2023 rows may carry a second
        # money value inside an in-kind description, e.g. "... $891.00 website-in kind $297/mo").
        date_end = _DATE_LEAD.match(wln).end()
        toks = [t for t in toks if t[0] >= date_end]
        if not toks:
            continue
        astart, aend, amount = toks[0]
        if amount == 0.0:
            continue                                   # $0 placeholder/garble -> skip
        repaired = ocr and repair_money_line(_DOLLAR_SPACE.sub("$", raw))[1]
        mtd = method + ("+repair" if repaired else "")
        iso = _norm_date(dtok)
        if ocr and iso and not date_in_window(iso, meta):
            iso = ""                                   # OCR misread the year -> blank, keep amount

        before = wln[date_end:astart].strip()          # donor/vendor (+ address in 2021)
        after = wln[aend:].strip()                     # in-kind desc (A) / purpose (B)
        inkind = bool(_INKIND.search(after) or _INKIND.search(wln))

        if mode == "c":
            fields = [f for f in re.split(r"\s{2,}", before) if f.strip()]
            donor = fields[0].strip().rstrip(",") if fields else ""
            contrib_rows.append(ContribRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                donor_raw=donor, amount=common.money_str(amount),
                in_kind="True" if inkind else "False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(meta.get("line_base", 0) + k + 1), extract_method=mtd,
                needs_review="0" if donor else "1"))
        else:
            fields = [f for f in re.split(r"\s{2,}", before) if f.strip()]
            vendor = fields[0].strip().rstrip(",") if fields else ""
            purpose = after                            # St. George prints purpose AFTER the amount
            expend_rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                vendor_raw=vendor, purpose=purpose, amount=common.money_str(amount),
                in_kind="True" if inkind else "False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(meta.get("line_base", 0) + k + 1), extract_method=mtd,
                needs_review="0" if vendor else "1"))

    # cover fallbacks when a Form footer was garbled/absent
    if stated_contrib is None:
        stated_contrib = _first_total(lines, _COV_C)
    if stated_expend is None:
        stated_expend = _first_total(lines, _COV_E)
    stated_end = _first_total(lines, _COV_BAL)

    notes = []
    if not contrib_rows and not expend_rows:
        notes.append("no itemized rows parsed in segment")
    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=stated_end,
                notes="; ".join(notes))
