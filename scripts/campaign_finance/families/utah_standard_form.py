#!/usr/bin/env python3
"""utah_standard_form.py — extractor for the SELF-HOSTED Utah municipal "Financial Disclosure /
Report of Contributions and Expenditures" form (UCA 10-3-208), the paper/PDF form a city posts
directly (no EasyVote / third-party portal).

This is the form Orem publishes on orem.gov, and — by design — the module GENERALIZES: Logan,
Nephi, and Vineyard file on the same or a near-identical statutory form, so they reuse this
family unchanged. Anything city-specific (label wording that drifts, an alternate header
variant) is passed as `meta["form_opts"]` overrides; the defaults below are the Utah-standard
wording, and NO city name / office logic lives here (candidate/office/year come from the
driver's meta, sourced from each city's index.csv).

Form structure (one page or several; `pdftotext -layout` concatenates pages and each section
header prints ONCE, itemization flowing continuously):

    FILING PERIOD: From <d> To <d>
    NAME OF CANDIDATE ...            NAME OF OFFICE ...
    1. Total contributions of donors more than $50.00 ....$ <L1>
    2. Aggregate total of contributions of $50.00 or less $ <L2>   (unitemized aggregate)
    3. Total campaign expenditures .......................$ <L3>
      -- Cash Contributions --      Date / Name of Donor / Amount            ... TOTAL $Cc
      -- In-Kind Contributions --   Date / Name of Donor / Estimated Amount  ... TOTAL $Ck
      -- Cash Expenditures --       Date / Recipient / Purpose / Amount      ... TOTAL $Ce
    (a 2025 Orem redesign folds the header into "Total Cash and In-Kind Contributions $..." /
     "Total Cash Expenditures $..." — handled as alternate headline labels.)

RECONCILIATION ANCHOR = the sections' own printed TOTAL lines (the "printed tally vs counted
rows" discipline), NOT the numbered headline block:
  * contributions side  -> sum of ALL contribution rows (cash + in-kind) vs (Cash-Contributions
    TOTAL + In-Kind TOTAL). The two section totals are the form's own printed subtotals; the
    numbered headline (line 1) folds in-kind into "more than $50" and splits out the ≤$50
    aggregate inconsistently between filers, so it is a FALLBACK only.
  * expenditures side   -> sum of expenditure rows vs Cash-Expenditures TOTAL (fallback line 3).
  The ≤$50 aggregate (line 2) is an UNITEMIZED stated figure — it is intentionally NOT emitted as
  a synthetic row (that would fabricate donor identities and break the itemized reconciliation);
  it is recorded in the filing note. Honest gaps are data.

OCR mode (`meta["is_scanned"]`): the shared common.py currency-repair whitelist + date-sanity
(`§`->`$`, thousands-comma-as-period, out-of-window date blanked/amount kept) is applied to each
line; a row whose amount came from a repaired token is marked `extract_method=...+repair`. A
figure that will not parse cleanly stays BLANK + needs_review — never a guessed digit. A scanned
filing whose garbled section headers/totals defeat this reconciles UNKNOWN/flagged and is the
honest candidate for the gated vision pass (driver `rows_override_fn`), never fabricated.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_date, money_spans, repair_money_line,
                    date_in_window)

# ------------------------------------------------------------------ default form vocabulary
_DEFAULTS = dict(
    sec_cashc=r"cash\s+contribution",
    sec_inkind=r"in[\s\-]?kind\s+contribution",
    sec_cashe=r"cash\s+expenditure",
    total=r"\b(?:SUB)?TOTAL\b",   # matches TOTAL, SUBTOTAL, and the "TOTAL" of GRAND TOTAL
    # numbered headline (fallback stated totals)
    l1=r"contributions of donors more than",
    l2=r"aggregate total of contributions",
    l3=r"total campaign expenditures",
    # 2025 redesigned headline
    cash_inkind=r"total cash and in.?kind contributions",
    cash_exp2=r"^total cash expenditures",
)

_SUBTOTAL = re.compile(r"\bSUBTOTAL\b", re.I)
_COLHDR = re.compile(r"name of (donor|recipient|contributor)|estimated amount|"
                     r"political purpose|^\s*date\b", re.I)
_MONTH = re.compile(r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*$", re.I)
# a leading transaction-date token to peel off the row's text (ISO, numeric, d-Mon, or a month
# word). Optional leading `|`/space is a scanned table-border artifact. ISO (YYYY-MM-DD) must come
# FIRST so a 4-digit year is not truncated to a 2-digit M/D by the later alternative.
_ISO = re.compile(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$")
_DATE_LEAD = re.compile(
    r"^[\s|]*("
    r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}"                  # 2023-01-12 (ISO)
    r"|\d{1,2}[/\-.]\d{1,2}(?:[/\-.]\d{2,4})?"        # 5/13/2023, 12-4-2021, 8/31, 6.30.23
    r"|\d{1,2}[\-\s][A-Za-z]{3,9}(?:[\-\s]\d{2,4})?"  # 30-May, 2 Apr 2018
    r")")


def _norm_date(dtok):
    """ISO YYYY-MM-DD (which parse_date doesn't cover) -> normalized; else the shared parse_date;
    else '' (never a guess)."""
    import datetime
    m = _ISO.match(dtok)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return ""
    return parse_date(dtok) or parse_date(dtok.replace(".", "/")) or ""


def _opts(meta):
    o = dict(_DEFAULTS)
    o.update(meta.get("form_opts") or {})
    return {k: re.compile(v, re.I) for k, v in o.items()}


_DOLLAR_SPACE = re.compile(r"\$\s+(?=[\d.])")


def _norm_line(line, ocr):
    """Working copy of a line. Collapse whitespace between a '$' and its digits — several Orem
    templates print `$        5,599.00` / `($   850.00)` (spreadsheet right-alignment), which the
    strict money regex (which needs `$` glued to the number) would otherwise miss ENTIRELY, losing
    the whole row. This only removes spacing inside an already-dollar-signed token; it never invents
    a value. OCR lines additionally get the shared currency-repair whitelist."""
    s = _DOLLAR_SPACE.sub("$", line)
    if ocr:
        s = repair_money_line(s)[0]
    return s


def _label_money(lines, label_re):
    """Rightmost clean money value on the first line matching label_re, else None. Used only for
    the fallback numbered-headline block (the section TOTALs are the primary anchor)."""
    for ln in lines:
        if label_re.search(ln):
            sp = money_spans(_norm_line(ln, True))
            if sp:
                return sp[-1][2]
    return None


def _peel_date(prefix):
    """Return (date_token, remainder). Peels a leading numeric/d-Mon date, or a leading MONTH
    word (Orem's 'JUNE'); otherwise no date. Conservative — never eats a donor's first name."""
    m = _DATE_LEAD.match(prefix)
    if m:
        return m.group(1).strip(), prefix[m.end():].strip()
    body = prefix.strip().lstrip("|").strip()
    first, _, rest = body.partition(" ")
    if _MONTH.match(first):
        rest = rest.strip()
        # also consume a trailing day and/or year so 'May 2025 Governing Group' -> donor 'Governing
        # Group' (not '2025'); 'July 8, 2025 ...' likewise. The month-word date won't resolve to an
        # ISO day, so `date` stays blank — but the donor column is no longer a stray year.
        m2 = re.match(r"^(\d{1,2},?\s+)?\d{4}\b|^\d{1,2}\b", rest)
        if m2:
            rest = rest[m2.end():].strip()
        return first, rest
    return "", body


def _sections(lines, o):
    """Ordered {kind: idx} of section-header lines (first occurrence of each kind wins; the form
    prints each header once and itemization flows continuously across page breaks).

    A real section header carries NO money and is NOT a "Total …" summary line — this excludes the
    2025 redesigned HEADLINE ('Total Cash and In-Kind Contributions $8,775.00', 'Total Cash
    Expenditures $7,088.48'), whose wording would otherwise be mistaken for the itemized-section
    headers and swallow the entire document into one section."""
    found = {}
    for i, ln in enumerate(lines):
        if o["total"].search(ln) or money_spans(_norm_line(ln, True)):
            continue
        for kind, rx in (("cashc", o["sec_cashc"]), ("inkind", o["sec_inkind"]),
                         ("cashe", o["sec_cashe"])):
            if kind not in found and rx.search(ln):
                found[kind] = i
    return found


def _section_rows(lines, start, end, o, meta, ocr, is_contrib):
    """Parse data rows in [start, end); return (rows, section_total). The section ends at its grand
    TOTAL line (SUBTOTAL lines are skipped but do not end it); that grand TOTAL is the
    reconciliation anchor and is never itself a data row, and trailing notes after it are ignored."""
    rows, sec_total = [], None
    for k in range(start, end):
        raw = lines[k]
        wln = _norm_line(raw, ocr)
        repaired = ocr and (repair_money_line(_DOLLAR_SPACE.sub("$", raw))[1])
        if o["total"].search(wln):
            sp = money_spans(wln)
            if _SUBTOTAL.search(wln):
                continue                        # page/column SUBTOTAL: skip, keep scanning
            if sp:
                sec_total = sp[-1][2]           # grand TOTAL: the reconciliation anchor
            break                               # section ends at its grand TOTAL (trailing
                                                # 'Amt Left over $110.13' / notes are not rows)
        if _COLHDR.search(wln):
            continue
        sp = money_spans(wln)
        if not sp:
            continue
        amount = sp[-1][2]                       # amount is the rightmost column
        if amount == 0.0:
            continue                             # skip $0.00 placeholder/template rows
        prefix = wln[:sp[-1][0]].rstrip()
        dtok, body = _peel_date(prefix)
        iso = _norm_date(dtok)
        if ocr and iso and not date_in_window(iso, meta):
            iso = ""                             # OCR misread the year -> blank, keep amount
        method = meta["extract_method"] + ("+repair" if repaired else "")
        if is_contrib:
            fields = [t for t in re.split(r"\s{2,}", body) if t.strip()]
            donor = fields[0].strip() if fields else ""
            rows.append(ContribRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                donor_raw=donor, amount=common.money_str(amount),
                in_kind="False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=str(k + 1), extract_method=method,
                needs_review="0" if donor else "1"))
        else:
            fields = [t for t in re.split(r"\s{2,}", body) if t.strip()]
            vendor = fields[0].strip() if fields else ""
            purpose = " ".join(f.strip() for f in fields[1:]).strip()
            rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                vendor_raw=vendor, purpose=purpose, amount=common.money_str(amount),
                in_kind="False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=str(k + 1), extract_method=method,
                needs_review="0" if vendor else "1"))
    return rows, sec_total


def parse(text: str, meta: dict) -> dict:
    o = _opts(meta)
    ocr = bool(meta.get("is_scanned"))
    lines = text.splitlines()
    n = len(lines)
    sec = _sections(lines, o)

    contrib_rows, inkind_rows, expend_rows = [], [], []
    cash_total = inkind_total = expend_total = None

    if "cashc" in sec:
        end = min([sec[k] for k in ("inkind", "cashe") if k in sec and sec[k] > sec["cashc"]]
                  + [n])
        contrib_rows, cash_total = _section_rows(lines, sec["cashc"] + 1, end, o, meta, ocr, True)
    if "inkind" in sec:
        end = min([sec[k] for k in ("cashe",) if k in sec and sec[k] > sec["inkind"]] + [n])
        inkind_rows, inkind_total = _section_rows(lines, sec["inkind"] + 1, end, o, meta, ocr, True)
        for r in inkind_rows:
            r.in_kind = "True"                   # this whole section is in-kind
    if "cashe" in sec:
        expend_rows, expend_total = _section_rows(lines, sec["cashe"] + 1, n, o, meta, ocr, False)

    # A section that IS present but whose TOTAL is an unreadable placeholder ("None" / "$ -") AND
    # produced ZERO data rows is a genuine NIL section (the form prints only dash placeholders when
    # a candidate reports nothing this period) -> total 0.0, so a nil filing reconciles True. Never
    # coerce when rows exist (that would falsely reconcile a real itemization against 0).
    if "cashc" in sec and cash_total is None and not contrib_rows:
        cash_total = 0.0
    if "inkind" in sec and inkind_total is None and not inkind_rows:
        inkind_total = 0.0
    if "cashe" in sec and expend_total is None and not expend_rows:
        expend_total = 0.0

    all_contrib = contrib_rows + inkind_rows

    # ---- stated (printed) totals: section TOTALs are the anchor; headline is the fallback ----
    if cash_total is not None or inkind_total is not None:
        stated_contrib = round((cash_total or 0.0) + (inkind_total or 0.0), 2)
    else:
        l1 = _label_money(lines, o["l1"]) or _label_money(lines, o["cash_inkind"])
        l2 = _label_money(lines, o["l2"])
        stated_contrib = None if l1 is None else round(l1 + (l2 or 0.0), 2)

    if expend_total is not None:
        stated_expend = expend_total
    else:
        stated_expend = _label_money(lines, o["l3"]) or _label_money(lines, o["cash_exp2"])

    # notes: record the unitemized ≤$50 aggregate + an in-kind cross-check (honest, non-blocking)
    notes = []
    l2 = _label_money(lines, o["l2"])
    if l2:
        notes.append(f"unitemized ≤$50 aggregate stated ${l2:.2f} (not itemized on form)")
    if inkind_total is not None:
        s = round(sum(float(r.amount) for r in inkind_rows if r.amount), 2)
        if abs(s - inkind_total) > 0.01:
            notes.append(f"in-kind itemized ${s:.2f} != stated ${inkind_total:.2f}")
    if not sec:
        notes.append("non-standard form (no Utah-standard sections found)")

    return dict(contrib_rows=all_contrib, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=None,
                notes="; ".join(notes))
