#!/usr/bin/env python3
"""easyvote_schedab.py — F2 extractor: EasyVote "Report of Contributions and Expenditures".

The West Jordan (2023+, born-digital) and Sandy (OCR) EasyVote form. ONE parser, TWO modes,
selected per-filing by `meta["is_scanned"]` (the driver sets it; an explicit `meta["ocr"]`
overrides). Text mode is byte-for-byte the born-digital WJ behavior; OCR mode adds three
reversible, whitelisted tolerances for tesseract noise — nothing here ever guesses a figure:

  * currency-glyph repair (`_repair_money_line`): `§`->`$`; a lone `S` before a cents-bearing
    money body -> `$`; a money token whose FINAL comma is followed by exactly two digits and
    has no `.` -> that comma is a decimal point (`$104,18`->`$104.18`; `$2,500` stays thousands).
    All three are length-preserving (so x-positions still map) and can only restore a `$`-shaped
    token, never invent one. Rows whose amount came from a repaired token are marked
    `extract_method=...+repair`.
  * date-sanity (`_date_in_window`): a contribution/expenditure date outside
    [election_year-1-01-01 .. filing_date] (tesseract reads `2021` as `2012`) is BLANKED, the
    amount KEPT — never "fixed" to a guessed date.
  * reconciliation still runs against the Summary Page's stated total (which OCRs far better
    than the garbled per-page SUBTOTAL lines), so a filing whose itemized rows sum to the
    printed Summary figure earns `medium` confidence; a mismatch is flagged, never adjusted.

Layout (`pdftotext -layout`):
  * Summary Page — a two-column grid, Column A = "Total this Period", Column B =
    "Year-to-Date". Labels and their money sit on ADJACENT lines (the amount line follows the
    label line), so each stated total is read by finding the label then the next money-bearing
    line:
      "TOTAL CONTRIBUTIONS RECEIVED" (Col A / Col B)   -> stated_contrib (+ _ytd)
      "TOTAL IN-KIND CONTRIBUTIONS"                    -> in-kind contrib total (Col A)
      "TOTAL EXPENDITURES MADE"                        -> stated_expend (+ _ytd)
      "TOTAL IN-KIND EXPENDITURES"                     -> in-kind expend total (Col A)
      "Balance at Beginning of Reporting"              -> stated_begin
      "Balance at Close of Reporting Period"           -> stated_end
    These are PER-PERIOD (Column A) figures -> is_incremental = TRUE (sum the Column-A totals
    across a candidate's cycle chain; the final report's Column B is the YTD cross-check).

  * Schedule A — Itemized Contributions: Date Received / Name of Contributor / Amount / In-Kind.
    Cash amount and In-Kind value are two SEPARATE columns; a row is cash OR in-kind. The columns
    are located by the x-position of the two money tokens on the "SUBTOTAL FOR THIS PAGE" line;
    a row's money token is classed cash vs in-kind by which column it sits under. Rows itemize
    ONLY this period. Per-page SUBTOTAL + grand "TOTAL CONTRIBUTIONS RECEIVED (Sum of all
    subtotals...)" lines are section boundaries, not data rows.

  * Schedule B — Itemized Expenditures: Date / Recipient / Purpose / Amount / In-Kind. Same
    two-column money geometry.

In-kind rows carry in_kind=True with `amount` = the in-kind value; reconciliation of each side
sums the CASH rows only, matching the form's "TOTAL CONTRIBUTIONS/EXPENDITURES" (which exclude
in-kind — the form states them on a separate line). The driver reconciles cash vs cash.
"""
from __future__ import annotations

import re

import common
from common import ContribRow, ExpendRow, split_columns, parse_date, money_spans

_MONEY = re.compile(r"-?\$-?[\d,]+(?:\.\d{1,2})?")
_DATE = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4})")

# --------------------------------------------------------------------- OCR tolerance mode
# Each repair is reversible/whitelisted: it can only turn an OCR-mangled `$`-token back into a
# clean one, never fabricate a value out of non-money text. A repaired line is used CONSISTENTLY
# for both money spans AND the donor/vendor text slice within a row (so a length change from a
# dot-thousands fix never misaligns the name column) — the driver reconciles the result against
# the Summary Page total regardless.


# The currency-repair whitelist + date-sanity now live in common.py (shared with every OCR-mode
# family). These module-level aliases preserve easyvote's original call sites byte-for-byte.
_fix_dot_thousands = common.fix_dot_thousands
_repair_money_line = common.repair_money_line
_date_in_window = common.date_in_window


def _rep(line, ocr):
    """The working copy of a line: OCR-repaired when ocr, verbatim otherwise."""
    return _repair_money_line(line)[0] if ocr else line


def _money_after(lines, i0, label_re, max_ahead=6, ocr=False):
    """First money value on the label line or within max_ahead following lines. Returns
    (colA, colB) — colB is the second money token on that line if present, else None."""
    for i in range(i0, min(len(lines), i0 + max_ahead + 1)):
        ln = _repair_money_line(lines[i])[0] if ocr else lines[i]
        vals = [common.parse_money(m.group(0)) for m in _MONEY.finditer(ln)]
        vals = [v for v in vals if v is not None]
        if vals:
            return vals[0], (vals[1] if len(vals) > 1 else None)
    return None, None


def _find(lines, label_re):
    for i, ln in enumerate(lines):
        if label_re.search(ln):
            return i
    return None


_L_CONTRIB = re.compile(r"TOTAL CONTRIBUTIONS RECEIVED(?!\s*\(Sum)", re.I)
_L_INK_CONTRIB = re.compile(r"TOTAL IN-?KIND CONTRIBUTIONS", re.I)
_L_EXPEND = re.compile(r"TOTAL EXPENDITURES MADE", re.I)
_L_INK_EXPEND = re.compile(r"TOTAL IN-?KIND EXPENDITURES", re.I)
_L_BEGIN = re.compile(r"Balance at Beginning of Reporting", re.I)
_L_CLOSE = re.compile(r"Balance at Close of Reporting", re.I)

_SCHED_A = re.compile(r"Itemized Contributions Received", re.I)
_SCHED_B = re.compile(r"Itemized Expenditures", re.I)
_SUBTOTAL = re.compile(r"SUBTOTAL FOR THIS PAGE", re.I)
_GRAND_A = re.compile(r"TOTAL CONTRIBUTIONS RECEIVED \(Sum", re.I)
_GRAND_B = re.compile(r"TOTAL EXPENDITURES RECEIVED \(Sum", re.I)


def _stated_after_label(lines, label_re, ocr=False):
    i = _find(lines, label_re)
    if i is None:
        return None, None
    return _money_after(lines, i, label_re, ocr=ocr)


def _page_thresholds(lines, i0, i1, ocr=False):
    """A PER-PAGE Amount/In-Kind midpoint, learned from each page's own SUBTOTAL line (whose two
    money tokens anchor the two columns). Money-column indentation drifts page-to-page in
    multi-page schedules, so one global threshold mis-classes later pages. Returns thr(k) ->
    the midpoint for the row at line k (the next SUBTOTAL at/after k), or None = 'all cash'.

    PER-PAGE IN-KIND INFERENCE (the OCR-safe rule; also correct for born-digital WJ): a row is
    classed in-kind by x-position ONLY when that page's SUBTOTAL shows a NON-ZERO in-kind column
    (its 2nd money token). When the page's in-kind subtotal is $0.00 — the overwhelming Sandy case
    — every row on the page is cash regardless of where tesseract dropped the amount glyph, so no
    fragile position guess is made. Pages that DO carry in-kind (WJ's Shelton $1,200) keep the
    positional split, so this is behaviour-preserving for the born-digital corpus."""
    if ocr:
        # Under OCR the x-position of a lone amount glyph is unreliable, so NO positional in-kind
        # split is attempted — every row starts cash and in-kind is recovered ONLY by the arithmetic
        # per-page subtotal inference (`_infer_inkind_by_subtotal`), which the page's own printed
        # subtotal proves. This avoids the misclassification tesseract's drifting columns cause.
        return lambda k: None
    subs = []
    for k in range(i0 + 1, min(i1 + 1, len(lines))):
        if _SUBTOTAL.search(lines[k]):
            sp = money_spans(lines[k])
            if len(sp) >= 2:
                subs.append((k, (sp[0][0] + sp[1][0]) / 2.0, sp[1][2]))  # midpoint, in-kind subtotal
            else:
                subs.append((k, None, 0.0))

    def thr(k):
        pick = next(((mid, ink) for sk, mid, ink in subs if sk >= k),
                    (subs[-1][1], subs[-1][2]) if subs else (None, 0.0))
        mid, ink = pick
        return mid if (ink is not None and abs(ink) > 0.005) else None  # None => all-cash page
    return thr


def _infer_inkind_by_subtotal(rows, lines, i0, i1):
    """OCR per-page in-kind inference (the plan's remedy for the in-kind-in-cash-column ambiguity).

    Sandy's 2021 EasyVote form prints a SINGLE-token page SUBTOTAL (just the CASH total, no visible
    $0.00 in-kind column), yet a page may carry an in-kind row (e.g. `Reagan Outdoor Advertising
    $4,500.00` billboard) whose amount is EXCLUDED from that cash subtotal. Position can't tell them
    apart under OCR, but arithmetic can: on a page whose printed cash subtotal parses cleanly, if the
    extracted cash rows exceed the subtotal by EXACTLY one row's amount, that row is the in-kind one
    -> flip it to in_kind=True (dropping it from the cash reconciliation). Deterministic and proven
    by the page's own printed subtotal; when the excess matches no single row (garbled subtotal, or
    two in-kind rows) nothing is changed and the page is left to flag honestly. Never fabricates."""
    subs = []
    for k in range(i0 + 1, min(i1 + 1, len(lines))):
        if _SUBTOTAL.search(lines[k]):
            sp = money_spans(_repair_money_line(lines[k])[0])
            subs.append((k, sp[0][2] if sp else None))
    prev = i0
    for k, cash_sub in subs:
        page = [r for r in rows if prev < (int(r.line_no) - 1) <= k]
        prev = k
        if cash_sub is None:
            continue
        cash_rows = [r for r in page if r.in_kind != "True" and r.amount]
        s = round(sum(float(r.amount) for r in cash_rows), 2)
        excess = round(s - cash_sub, 2)
        if excess <= 0.01:
            continue
        cand = [r for r in cash_rows if abs(float(r.amount) - excess) <= 0.01]
        if len(cand) == 1:
            cand[0].in_kind = "True"
            if "+inkind" not in cand[0].extract_method:
                cand[0].extract_method += "+inkind"


def _classify(spans, threshold):
    """Given a row's money spans, return (amount, is_in_kind). Cash column = start < threshold;
    in-kind column = start >= threshold. Prefer a cash token; else the in-kind token."""
    if not spans:
        return None, False
    if threshold is None:
        return spans[0][2], False
    cash = [s for s in spans if s[0] < threshold]
    ink = [s for s in spans if s[0] >= threshold]
    if cash:
        return cash[0][2], False
    return ink[0][2], True


def _section(lines, start_re, end_res):
    """First `start_re` header to the LAST `end_re` grand-total line. EasyVote repeats both the
    per-page 'Schedule A/B' header AND the grand 'TOTAL ... (Sum of all subtotals...)' line on
    every page of a multi-page schedule, so the section must span to the LAST grand total, not
    the first (which would truncate a multi-page schedule to page 1)."""
    i0 = _find(lines, start_re)
    if i0 is None:
        return None, None
    i1 = None
    for j in range(i0 + 1, len(lines)):
        if any(r.search(lines[j]) for r in end_res):
            i1 = j
    return i0, (i1 if i1 is not None else len(lines))


def _wrapped_amount(lines, k, i1, ocr=False, look=2):
    """A date-bearing row whose amount wrapped to a FOLLOWING line: return that line's money
    spans if the next up-to-`look` non-blank lines is money-only (a lone $token, no date of its
    own). Conservative — only fires when the continuation line is unambiguously just an amount."""
    seen = 0
    for j in range(k + 1, min(i1, len(lines))):
        s = _rep(lines[j], ocr).strip()
        if not s:
            continue
        seen += 1
        if seen > look:
            return None
        if _DATE.match(s) or _SUBTOTAL.search(lines[j]):
            return None
        sp = money_spans(s)
        if sp and len(re.sub(r"[-$\d,.\s]", "", s)) == 0:  # line is money-only
            return sp
    return None


def _vertical_block(lines, k, i1, ocr, look=14):
    """OCR sometimes renders a schedule page VERTICALLY — each field on its own line:

        01/24/2025
        Landslide Political
        Professional Campaign Services:
        $1,000.00

    (the 2025 Sandy form's expenditure pages). The horizontal parser skips these (the amount is
    >2 lines below the date). This collects the non-blank lines after a date line UP TO the first
    money-bearing line — that money is the row's amount, the intervening text lines are the
    name/purpose fields. Stops (returns None) at the next date / subtotal / grand-total, so it
    never bleeds one row into the next. Returns (amount_value, [text fields]) or None."""
    parts = []
    seen = 0
    for j in range(k + 1, min(i1, len(lines))):
        raw = lines[j]
        s = _rep(raw, ocr).strip()
        if not s:
            continue
        seen += 1
        if seen > look:
            return None
        if _DATE.match(s) or _SUBTOTAL.search(raw) or _GRAND_A.search(raw) or _GRAND_B.search(raw):
            return None
        sp = money_spans(s)
        if sp:
            return sp[0][2], parts        # first money line closes the vertical row
        parts.append(s)
    return None


def _row_party_purpose(line, sp_amount):
    """Text between the date and the amount token: for Schedule A -> donor; for Schedule B ->
    (recipient, purpose) split on 2+ spaces."""
    head = line[:sp_amount[0]]
    m = _DATE.match(head.strip())
    if m:
        head = head.strip()[m.end():]
    fields = [f for f in re.split(r"\s{2,}", head.strip()) if f]
    return fields


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    meta = dict(meta)
    meta.setdefault("reporting_period", "")
    ocr = bool(meta.get("ocr", meta.get("is_scanned", False)))
    base_method = meta["extract_method"]

    def _method(repaired):
        return base_method + "+repair" if (ocr and repaired) else base_method

    def _date_for(raw):
        """ISO date, blanked (kept-amount) when OCR pushed it outside the filing window."""
        iso = parse_date(raw) or ""
        if ocr and iso and not _date_in_window(iso, meta):
            return ""
        return iso

    stated_contrib, contrib_ytd = _stated_after_label(lines, _L_CONTRIB, ocr)
    stated_expend, expend_ytd = _stated_after_label(lines, _L_EXPEND, ocr)
    ink_contrib, _ = _stated_after_label(lines, _L_INK_CONTRIB, ocr)
    ink_expend, _ = _stated_after_label(lines, _L_INK_EXPEND, ocr)
    stated_begin, _ = _stated_after_label(lines, _L_BEGIN, ocr)
    stated_end, _ = _stated_after_label(lines, _L_CLOSE, ocr)

    # ---- Schedule A (contributions) : from its header to its grand-total line
    contrib_rows = []
    a0, a1 = _section(lines, _SCHED_A, [_GRAND_A])
    if a0 is not None:
        thr_fn = _page_thresholds(lines, a0, a1, ocr)
        for k in range(a0 + 1, a1):
            ln = lines[k]
            if _SUBTOTAL.search(ln) or _GRAND_A.search(ln):
                continue
            m = _DATE.match(ln.strip())
            if not m:
                continue
            wln = _rep(ln, ocr)               # OCR-repaired working copy (used for spans + text)
            repaired = wln != ln
            extra = ""
            sp = money_spans(wln)
            if sp:                            # horizontal row (money on the date line)
                amount, in_kind = _classify(sp, thr_fn(k))
                fields = _row_party_purpose(wln, sp[0])
            elif (w := _wrapped_amount(lines, k, a1, ocr)):  # amount wrapped to a following line
                amount, in_kind = w[0][2], False
                fields = [f for f in re.split(r"\s{2,}", _DATE.sub("", wln.strip()).strip()) if f]
            elif ocr and (v := _vertical_block(lines, k, a1, ocr)):  # one-field-per-line page
                amount, in_kind, fields, extra = v[0], False, v[1], "+vertical"
            else:
                continue
            # donor = first NON-numeric field: a malformed source date ("05/27/22023" — an extra
            # digit) leaves a stray digit fragment as fields[0]; the real name is the next field.
            donor = next((f.strip() for f in fields if not f.strip().isdigit()),
                         fields[0].strip() if fields else "")
            contrib_rows.append(ContribRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""),
                date=_date_for(m.group(1)), donor_raw=donor,
                amount=common.money_str(amount), in_kind=str(in_kind), is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=str(k + 1), extract_method=_method(repaired) + extra,
                needs_review="0" if (amount is not None and donor) else "1"))
        if ocr:
            _infer_inkind_by_subtotal(contrib_rows, lines, a0, a1)

    # ---- Schedule B (expenditures)
    expend_rows = []
    b0, b1 = _section(lines, _SCHED_B, [_GRAND_B])
    if b0 is not None:
        thr_fn = _page_thresholds(lines, b0, b1, ocr)
        for k in range(b0 + 1, b1):
            ln = lines[k]
            if _SUBTOTAL.search(ln) or _GRAND_B.search(ln):
                continue
            m = _DATE.match(ln.strip())
            if not m:
                continue
            wln = _rep(ln, ocr)
            repaired = wln != ln
            extra = ""
            thr = thr_fn(k)
            sp = money_spans(wln)
            if sp:                            # horizontal row (money on the date line)
                amount, in_kind = _classify(sp, thr)
                cash_sp = [s for s in sp if thr is None or s[0] < thr]
                anchor = cash_sp[0] if cash_sp else sp[0]
                fields = _row_party_purpose(wln, anchor)
            elif (w := _wrapped_amount(lines, k, b1, ocr)):  # amount wrapped to a following line
                amount, in_kind = w[0][2], False
                fields = [f for f in re.split(r"\s{2,}", _DATE.sub("", wln.strip()).strip()) if f]
            elif ocr and (v := _vertical_block(lines, k, b1, ocr)):  # one-field-per-line page
                amount, in_kind, fields, extra = v[0], False, v[1], "+vertical"
            else:
                continue
            vendor = fields[0].strip() if fields else ""
            purpose = " ".join(fields[1:]).strip() if len(fields) > 1 else ""
            expend_rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""),
                date=_date_for(m.group(1)), vendor_raw=vendor, purpose=purpose,
                amount=common.money_str(amount), in_kind=str(in_kind), is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=str(k + 1), extract_method=_method(repaired) + extra,
                needs_review="0" if amount is not None else "1"))
        if ocr:
            _infer_inkind_by_subtotal(expend_rows, lines, b0, b1)

    notes = "incremental(Column A per-period)"
    if contrib_ytd is not None:
        notes += f"; ytd_contrib={common.money_str(contrib_ytd)}"
    if expend_ytd is not None:
        notes += f"; ytd_expend={common.money_str(expend_ytd)}"

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=stated_begin, stated_end=stated_end,
                contrib_ytd=contrib_ytd, expend_ytd=expend_ytd,
                ink_contrib=ink_contrib, ink_expend=ink_expend,
                incremental=True, notes=notes)
