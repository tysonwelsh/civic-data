#!/usr/bin/env python3
"""southjordan_form.py — extractor for South Jordan City's SELF-HOSTED
"CAMPAIGN FINANCIAL DISCLOSURE REPORT — Report of Contributions and Expenditures,
Section 1.12.050 of the South Jordan City Municipal Code" form.

This is a South-Jordan-SPECIFIC form (NOT the utah_standard_form and NOT EasyVote), but it
is structurally EasyVote-like: a Summary Page with two money columns —

    Covering Period <start> through <end>          Column A            Column B
                                                   Total this Period   Year-to-Date Total
    CONTRIBUTIONS RECEIVED
      (a) donors < $50 (money)                     <A>                 <B>
      (b) donors > $50 (money)                     <A>                 <B>
      (c) Total Contributions (Money) (a+b)        <A>                 <B>
      (d) in-kind < $50 in value                   <A>                 <B>
      (e) in-kind > $50 in value                   <A>                 <B>
      (f) Total contributions (in-kind) (d+e)      <A>                 <B>
      Total Contributions (Add line c and f above) <A>                 <B>
    EXPENDITURES MADE
      (g) Cash Expenditures                        <A>                 <B>
      (h) All other Expenditures                   <A>                 <B>
      Total Expenditures (Add line g and h above)  <A>                 <B>

    Schedule A — ITEMIZED CONTRIBUTIONS RECEIVED   Date | Name | Mailing Address | Amount
    Schedule B — ITEMIZED EXPENDITURES MADE        Date | Recipient | Purpose | Amount

INCREMENTAL (`is_incremental=True`): Column A is "Total this Period" and Schedule A/B itemize
only that period (verified on Johnson 2023 5329: Schedule A sums to $4,565 = Column A this-
period Total Contributions, NOT the $11,905 Year-to-Date; Schedule B sums to $5,213.02 = Column
A Cash Expenditures). So a cycle total is the SUM of the period reports' Column-A figures and the
final report's Column B / Year-to-Date is the cross-check (same discipline as EasyVote F2). The
RECONCILIATION ANCHOR is therefore Column A "Total this Period", and — because in-kind is folded
INTO the printed "Total Contributions (Add line c and f)" — the contributions side sums ALL rows
(cash + in-kind), NOT cash-only (`reconcile_cash_only=False`).

FORMAT REALITY (re-characterized per filing, 2026-07-06): the born-digital PDFs render their
Schedule A/B itemization to text ONLY for the 2023 print-flattened variant (Johnson 5329); the
2025 fillable variant keeps its filled Summary numbers in AcroForm fields (recovered by
`pdftotext -layout`) but attaches the itemization as a scanned/re-encoded image `pdftotext`
cannot read (garbled) — so those reconcile as totals-only until Claude-vision transcribes their
Schedule A/B (fed back through the driver `rows_override_fn`, judged by this same Column-A test).
A figure that will not parse cleanly stays BLANK + needs_review — never a guessed digit.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_date, money_spans, repair_money_line,
                    date_in_window)

# ---- Summary-page total labels (Column A = this period is the reconciliation anchor) ----
_LBL_CONTRIB = re.compile(r"total\s+contributions\s*\(add\s+line", re.I)
_LBL_EXPEND = re.compile(r"total\s+expenditures\s*\(add\s+line", re.I)

# A summary numeric token: bare or $-prefixed, must carry 2 decimals OR a $ (so a stray year or
# page number is never read as a dollar figure). Handles '$0.00', '150.00', '$12,615.00', '(150.00)'.
_SUMNUM = re.compile(r"\(?\$?\s*-?[\d,]*\d\.\d{2}\)?|\$-?[\d,]+")

# A leading transaction-date token (Schedule A/B row start): M/D/YY[YY], ISO, or d-Mon.
_DATE_LEAD = re.compile(
    r"^[\s|]*("
    r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}"                  # 2023-10-25 (ISO)
    r"|\d{1,2}[/\-.]\d{1,2}(?:[/\-.]\d{2,4})?"        # 10/25/23, 10-25-2023
    r"|\d{1,2}[\-\s][A-Za-z]{3,9}(?:[\-\s]\d{2,4})?"  # 25-Oct, 25 Oct 2023
    r")")
_ISO = re.compile(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$")
_DOLLAR_SPACE = re.compile(r"\$\s+(?=[\d.])")   # '$ 5,213.02' -> '$5,213.02' (Schedule B alignment)
_INKIND = re.compile(r"in[\s\-]?kind", re.I)


def _norm_line(line, ocr):
    s = _DOLLAR_SPACE.sub("$", line)
    if ocr:
        s = repair_money_line(s)[0]
    return s


def _norm_date(dtok, meta, ocr):
    import datetime
    m = _ISO.match(dtok)
    iso = ""
    if m:
        try:
            iso = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            iso = ""
    else:
        iso = parse_date(dtok) or parse_date(dtok.replace(".", "/")) or ""
    if ocr and iso and not date_in_window(iso, meta):
        iso = ""
    return iso


def _sumval(tok):
    """A summary/total numeric token -> float, or None. Strips ()/$/spaces; () => negative."""
    t = tok.strip()
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace("$", "").replace(",", "").replace(" ", "")
    if t in ("", "-"):
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _summary_totals(lines, label_re):
    """First (ColumnA, ColumnB) pair on / just after a summary total line, else (None, None).
    The label and its two numbers can share a line or the numbers fall on the next 1-2 lines."""
    for i, ln in enumerate(lines):
        if not label_re.search(ln):
            continue
        for j in range(i, min(i + 3, len(lines))):
            nums = [_sumval(m.group(0)) for m in _SUMNUM.finditer(_DOLLAR_SPACE.sub("$", lines[j]))]
            nums = [n for n in nums if n is not None]
            # the label line itself often carries trailing text; keep only from the label onward
            if j == i:
                after = lines[j][label_re.search(lines[j]).end():]
                nums = [n for n in (_sumval(m.group(0)) for m in _SUMNUM.finditer(
                    _DOLLAR_SPACE.sub("$", after))) if n is not None]
            if nums:
                a = nums[0]
                b = nums[1] if len(nums) > 1 else None
                return a, b
    return None, None


def _classify_lines(lines, ocr):
    """Tag each line ROW (date-led + trailing money) / TOTAL (only money, no other text) / OTHER."""
    tagged = []
    for k, raw in enumerate(lines):
        wln = _norm_line(raw, ocr)
        sp = money_spans(wln)
        if not sp:
            tagged.append(("OTHER", k, wln, None))
            continue
        dm = _DATE_LEAD.match(wln)
        # strip money + whitespace + table borders -> if nothing left it's a lone TOTAL line
        residue = wln
        for s, e, _ in sp:
            residue = residue[:s] + " " * (e - s) + residue[e:]
        residue = re.sub(r"[\s|$]+", "", residue)
        if dm:
            tagged.append(("ROW", k, wln, sp))
        elif residue == "":
            tagged.append(("TOTAL", k, wln, sp[-1][2]))
        else:
            tagged.append(("OTHER", k, wln, None))
    return tagged


_ADDR = re.compile(r",\s*[A-Z]{2}\s+\d{5}\b|^\d+\s+[NSEW]?\.?\s*[A-Za-z]")   # 'South Jordan, UT 84095' / '9444 S Tanya Ave'


def _mk_contrib(k, wln, sp, meta, ocr, repaired, lines):
    amount = sp[-1][2]
    prefix = wln[:sp[-1][0]]
    dm = _DATE_LEAD.match(wln)
    dtok = dm.group(1).strip() if dm else ""
    body = prefix[dm.end():] if dm else prefix
    fields = [t for t in re.split(r"\s{2,}", body.strip()) if t.strip()]
    donor = fields[0].strip() if fields else ""
    city = state = ""
    for fld in fields:
        m = re.search(r",?\s*([A-Za-z .]+),\s*([A-Z]{2})\s+\d{5}", fld)
        if m:
            city, state = m.group(1).strip(), m.group(2).strip()
            break
    # Multi-line contributor block: when the date-row's first column is an ADDRESS (the name sits
    # on the preceding line, as in Johnson 5329's $1500 self-contribution), recover the name from
    # the nearest preceding non-date, non-money line's first column. Never fabricates — the name is
    # printed, just on the line above; if none is found the address stays (flagged by review rules).
    if donor and _ADDR.search(donor):
        for j in range(k - 1, max(k - 4, -1), -1):
            prev = _DOLLAR_SPACE.sub("$", lines[j])
            if not prev.strip() or money_spans(prev) or _DATE_LEAD.match(prev):
                continue
            cand = [t for t in re.split(r"\s{2,}", prev.strip()) if t.strip()]
            if cand and not _ADDR.search(cand[0]) and re.search(r"[A-Za-z]{2}", cand[0]):
                donor = cand[0].strip()
            break
    method = meta["extract_method"] + ("+repair" if repaired else "")
    return ContribRow(
        candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
        election_year=meta["election_year"], filing_date=meta["filing_date"],
        reporting_period=meta.get("reporting_period", ""), date=_norm_date(dtok, meta, ocr),
        donor_raw=donor, donor_city=city, donor_state=state, amount=common.money_str(amount),
        in_kind="True" if _INKIND.search(wln) else "False", is_incremental="True",
        source_filing=meta["source_filing"], document_id=meta["document_id"],
        line_no=str(k + 1), extract_method=method, needs_review="0" if donor else "1")


def _mk_expend(k, wln, sp, meta, ocr, repaired):
    amount = sp[-1][2]
    prefix = wln[:sp[-1][0]]
    dm = _DATE_LEAD.match(wln)
    dtok = dm.group(1).strip() if dm else ""
    body = prefix[dm.end():] if dm else prefix
    fields = [t for t in re.split(r"\s{2,}", body.strip()) if t.strip()]
    vendor = fields[0].strip() if fields else ""
    purpose = " ".join(f.strip() for f in fields[1:]).strip()
    method = meta["extract_method"] + ("+repair" if repaired else "")
    return ExpendRow(
        candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
        election_year=meta["election_year"], filing_date=meta["filing_date"],
        reporting_period=meta.get("reporting_period", ""), date=_norm_date(dtok, meta, ocr),
        vendor_raw=vendor, purpose=purpose, amount=common.money_str(amount),
        in_kind="True" if _INKIND.search(wln) else "False", is_incremental="True",
        source_filing=meta["source_filing"], document_id=meta["document_id"],
        line_no=str(k + 1), extract_method=method, needs_review="0" if vendor else "1")


def parse(text: str, meta: dict) -> dict:
    ocr = bool(meta.get("is_scanned"))
    lines = text.splitlines()

    # --- Summary page Column A "Total this Period" (canonical reconciliation anchor) ---
    sumA_c, sumB_c = _summary_totals(lines, _LBL_CONTRIB)
    sumA_e, sumB_e = _summary_totals(lines, _LBL_EXPEND)

    # --- Schedule A/B itemization: contributions before the 1st schedule TOTAL, expenditures
    # after. Summary numeric lines (which look like TOTALs) are harmlessly ignored because a
    # schedule TOTAL is only accepted once its side already has ≥1 itemized ROW. ---
    tagged = _classify_lines(lines, ocr)
    crows, erows = [], []
    schedA_total = schedB_total = None
    phase = "A"
    for tag, k, wln, extra in tagged:
        repaired = ocr and repair_money_line(_DOLLAR_SPACE.sub("$", lines[k]))[1]
        if tag == "ROW":
            if extra[-1][2] == 0.0:
                continue  # skip $0.00 placeholder rows
            if phase == "A":
                crows.append(_mk_contrib(k, wln, extra, meta, ocr, repaired, lines))
            else:
                erows.append(_mk_expend(k, wln, extra, meta, ocr, repaired))
        elif tag == "TOTAL":
            if phase == "A" and crows:
                if schedA_total is None:
                    schedA_total = extra
                phase = "B"
            elif phase == "B" and erows:
                schedB_total = extra   # last non-placeholder TOTAL on the expenditure side wins

    stated_contrib = sumA_c if sumA_c is not None else schedA_total
    stated_expend = sumA_e if sumA_e is not None else schedB_total

    notes = []
    if sumB_c is not None:
        notes.append(f"YTD contributions (Column B) stated ${sumB_c:,.2f}")
    if sumB_e is not None:
        notes.append(f"YTD expenditures (Column B) stated ${sumB_e:,.2f}")
    if (stated_contrib is not None or stated_expend is not None) and not crows and not erows:
        notes.append("summary totals only; Schedule A/B itemization not text-extractable "
                     "(scanned attachment) — pending vision")

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=None,
                stated_contrib_ytd=sumB_c, stated_expend_ytd=sumB_e,
                notes="; ".join(notes))
