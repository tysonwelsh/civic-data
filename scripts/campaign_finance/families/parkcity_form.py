#!/usr/bin/env python3
"""parkcity_form.py — extractor for PARK CITY's self-hosted municipal "Campaign Financial
Report" form (UCA 10-3-208 + Park City Municipal Code 3-3), the paper/PDF form Park City posts
directly on its Revize `/Documents/.../Campaign Disclosures/` tree (no EasyVote / state portal).

WHY A NEW FAMILY (not `utah_standard_form`): Park City's form is structurally distinct from the
Orem-style Utah standard form. It has TWO itemized sections — **Form "A" (contributions)** and
**Form "B" (expenditures)** — NOT the Orem trio of Cash-Contributions / In-Kind / Cash-
Expenditures sections, and in-kind is recorded INLINE ("(in kind)" in the donor name or "In Kind"
in the amount column), never as its own section with its own TOTAL. The itemized columns also
differ and DRIFT across cycles:
  * 2017: Date | First | Last | Address | City | State | Zip | Type | Amount | *running-total*
    (a SECOND money column per row — the cumulative), expenditures as a QuickBooks P&L export.
  * 2019/2023/2025: Date | Name of Contributor | Mailing Address & Zip | Amount   (one column;
    2023 prints the amount BARE, no `$`).
  * 2021: Date | First | Last | Mailing address | Gross                          (one column).
And the printed reconciliation TOTAL lives in a COVER headline block whose wording itself drifted:
  * 2017/2019: "1. Total amount from donors giving more than $50.00  $<A>  (Form 'A' total)" —
    with a possible inline "+ $<vik> VIK" (value-in-kind, EXCLUDED from the cash total).
  * 2023/2025: "1b. Itemized total of contributions totaling $500.00 or more  $<A>"; the ≤$500
    aggregate is line 1a.
  * expenditures: "3. Total campaign expenditures" / "3b. Itemized total of campaign expenditures".
Only ~half the filings retain that cover page in the sidecar; the rest carry an in-table
"Total Contributions" / "Total Expenditures" line, which we anchor on as a fallback.

RECONCILIATION ANCHOR = the form's own printed Form-A / Form-B totals (the "printed tally vs
counted rows" discipline). Contributions reconcile CASH rows only (in-kind is a separate inline
line EXCLUDED from the Form-A cash total, exactly the EasyVote cash-only rule) — the driver is
called with reconcile_cash_only=True. The ≤$50/≤$500 unitemized aggregate is NOT emitted as a
synthetic row (that would fabricate donor identities); it is recorded in the filing note.

OCR mode (`meta["is_scanned"]`): shared common.py currency-repair whitelist + `$`-spacing
normalizer + date-sanity. A scanned filing whose garbled columns/totals defeat this reconciles
UNKNOWN/flagged and is the honest candidate for the gated vision pass (driver `rows_override_fn`),
NEVER fabricated. A figure that will not parse cleanly stays BLANK + needs_review — never guessed.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_date, repair_money_line, date_in_window)

# --------------------------------------------------------------------- numeric tokenizing
# Park City prints amounts either $-signed ("$ 250.00", "$46,075.00") or BARE ("16,400", "200").
# money_spans() (common.py) only finds $-signed tokens, so we add a bare-number scanner used only
# where a column is known to be the amount column. A bare integer is NOT treated as money by the
# generic tokenizers (so a zip/street number is safe); this scanner is applied deliberately.
_NUM = re.compile(r"-?\$?\s?-?[\d,]+(?:\.\d{1,2})?")
_DOLLAR_SPACE = re.compile(r"\$\s+(?=[\d.])")
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_DATE_LEAD = re.compile(
    r"^[\s|]*("
    r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}"                  # 2023-01-12 (ISO)
    r"|\d{1,2}[/\-.]\d{1,2}(?:[/\-.]\d{2,4})?"        # 5/13/2023, 10.24.23, 8/31
    r"|\d{1,2}[\-\s]" + _MON + r"(?:[\-\s]\d{2,4})?"  # 30-May, 2 Apr 2018, 17-Oct
    r"|" + _MON + r"\.?\s+\d{1,2}(?:,?\s*\d{2,4})?"   # Oct 23, 2025 / October 26 (month-first)
    r")", re.I)
_ISO = re.compile(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$")
_MONTHNUM = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def _num(tok):
    """Parse a $-signed OR bare numeric token to float, else None. Never guesses."""
    if tok is None:
        return None
    t = tok.strip().replace(" ", "")
    if not re.fullmatch(r"-?\$?-?[\d,]+(?:\.\d{1,2})?", t):
        return None
    neg = t.count("-") % 2 == 1
    t = t.replace("-", "").replace("$", "").replace(",", "")
    if t == "" or t == ".":
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _num_spans(line):
    """All numeric tokens (money or bare) as (start, end, value), in order."""
    out = []
    for m in _NUM.finditer(line):
        v = _num(m.group(0))
        if v is not None:
            out.append((m.start(), m.end(), v))
    return out


_DOLLAR_TOKEN = re.compile(r"\$\s*\d[\d,.\s]*\d")


def _norm(line, ocr):
    s = _DOLLAR_SPACE.sub("$", line)
    # collapse stray spaces INSIDE a $-signed number only ("$1 ,087.61" / "$231 .27" — a
    # pdftotext/OCR artifact). Bounded to $-tokens so a bare "84060  10,000" (zip vs amount) is
    # never merged. This never invents a value; it only re-joins a split money token.
    s = _DOLLAR_TOKEN.sub(lambda m: re.sub(r"\s+", "", m.group(0)), s)
    if ocr:
        s = repair_money_line(s)[0]
    return s


def _norm_date(dtok):
    import datetime
    m = _ISO.match(dtok)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return ""
    # month-first "Oct 23, 2025" / "October 26 2025"
    m = re.match(r"^(" + _MON + r")\.?\s+(\d{1,2})(?:,?\s*(\d{2,4}))?$", dtok, re.I)
    if m and m.group(3):
        mon = _MONTHNUM.get(m.group(1)[:3].lower())
        y = int(m.group(3))
        y += 2000 if y < 70 else (1900 if y < 100 else 0)
        try:
            return datetime.date(y, mon, int(m.group(2))).isoformat()
        except (ValueError, TypeError):
            return ""
    return parse_date(dtok) or parse_date(dtok.replace(".", "/").replace("-", "/")) or ""


# ---------------------------------------------------------------- stated (printed) totals
_THRESH = {50.0, 500.0}   # the "$50.00" / "$500.00" thresholds baked into the label wording
_MONEY_ONLY = re.compile(r"\$-?\s?[\d,]+(?:\.\d{1,2})?")


def _values(line, money_only=False):
    """Numeric values on a line, thresholds ($50/$500) dropped. money_only=True restricts to
    $-signed tokens (used on cover lines whose label carries a bare threshold like 'more than 50').
    """
    src = _MONEY_ONLY.finditer(line) if money_only else _NUM.finditer(line)
    vals = []
    for m in src:
        v = _num(m.group(0))
        if v is not None and v not in _THRESH:
            vals.append(v)
    return vals


_ITEMNO = re.compile(r"^\s*\d{1,2}[a-z]?[.)]\s")


def _norm_total(ln):
    """Normalize a cover/total line before value extraction: collapse '$   53,125' right-alignment
    and '$1 ,087.61' artifacts, and STRIP the leading numbered-item marker ('1.', '1b.', '3a.')
    so the item number is never mistaken for the answer value."""
    s = _DOLLAR_SPACE.sub("$", ln)
    s = _DOLLAR_TOKEN.sub(lambda m: re.sub(r"\s+", "", m.group(0)), s)
    return _ITEMNO.sub(" ", s)


def _find_total(lines, patterns, first=False):
    """First line matching any pattern -> its chosen value (first or last non-threshold numeric),
    else None. `first` picks the leftmost value (the 2017 '$39,100 + $8573 VIK' cash-first case).
    The $-signed value wins over a bare number when both are present (the label carries a bare
    '$50'/'$500' threshold that is dropped; the answer is $-signed after normalization, except the
    2023 bare-value forms where only a bare number remains)."""
    for pat in patterns:
        rx = re.compile(pat, re.I)
        for ln in lines:
            if rx.search(ln):
                s = _norm_total(ln)
                vals = _values(s, money_only=True) or _values(s, money_only=False)
                if vals:
                    return vals[0] if first else vals[-1]
    return None


# contributions cash TOTAL (Form A). 2017/2019 label is "more than $50" (VIK may follow → take
# the FIRST value = cash); 2023/2025 is "itemized total of contributions" (take the printed value);
# in-table fallback "Total Contributions"; last-ditch the ≤ aggregate (1a) when 1b was left blank.
def _stated_contrib(lines):
    v = _find_total(lines, [r"more than \$?\s?50\b.*"], first=True)
    if v is not None:
        return v
    for pat in (r"itemized total of contributions",
                r"total\s+contrib\w*",
                r"aggregate total of contributions under"):
        v = _find_total(lines, [pat])
        if v is not None:
            return v
    return None


def _stated_expend(lines):
    for pat in (r"itemized total of campaign expenditures",
                r"total campaign expenditures",
                r"total\s+expend\w*",
                r"aggregate total of campaign expenditures under"):
        v = _find_total(lines, [pat])
        if v is not None:
            return v
    return None


# ------------------------------------------------------------------------- section finding
_A_HDR = re.compile(r"itemized contribution|name of contributor|name and address of contributor",
                    re.I)
_B_HDR = re.compile(r"itemized expenditure|person or organization|to whom expenditure|"
                    r"expenditure was made", re.I)
_COLHDR = re.compile(r"name of contributor|mailing address|amount of contribution|name and address|"
                     r"person or organization|to whom|political purpose|^\s*date\b|gross\b|"
                     r"first\s+last|expenditure was made|reporting period", re.I)
_TOTAL_LINE = re.compile(r"\b(sub\s?total|total\s+contrib\w*|total\s+expend\w*|total under|"
                         r"net income|total expense)\b", re.I)
_AGG_DONOR = re.compile(r"under\s*\$?\s*5?0{1,2}|aggregate|unitemized", re.I)
_INKIND = re.compile(r"in[\s\-]?kind|\bvik\b", re.I)


def _find_section(lines, hdr_re, after=-1):
    for i, ln in enumerate(lines):
        if i > after and hdr_re.search(ln):
            return i
    return None


def _running_mode(lines, a0, a1, ocr):
    """2017 prints a per-row running-total as a SECOND money column. Detect it: a majority of the
    contribution data rows carry >=2 $-signed tokens -> the amount is the second-to-last, not last."""
    two = one = 0
    for k in range(a0, a1):
        wln = _norm(lines[k], ocr)
        if _TOTAL_LINE.search(wln) or _COLHDR.search(wln):
            continue
        sp = [m for m in _MONEY_ONLY.finditer(wln)]
        if not _DATE_LEAD.match(wln):
            continue
        if len(sp) >= 2:
            two += 1
        elif len(sp) == 1:
            one += 1
    return two > (one + two) / 2 and two >= 3


def _peel_date(prefix):
    m = _DATE_LEAD.match(prefix)
    if m:
        return m.group(1).strip(), prefix[m.end():].strip()
    return "", prefix.strip().lstrip("|").strip()


def _amount(wln, running):
    """(amount_value_or_None, amount_start_index). money tokens win; a bare trailing column is the
    fallback. In running-total mode the amount is the second-to-last money token (last = cumulative).
    """
    sp = [(m.start(), m.end(), _num(m.group(0))) for m in _MONEY_ONLY.finditer(wln)]
    sp = [t for t in sp if t[2] is not None]
    if sp:
        idx = -2 if (running and len(sp) >= 2) else -1
        return sp[idx][2], sp[idx][0]
    # bare fallback: the RIGHTMOST clean numeric column, skipping a trailing method annotation
    # ('978.04  in kind', '100  cash', '250  check'). A column may GLUE the amount to a KNOWN
    # annotation in one whitespace field ('59.41 in kind') -> peel a leading number ONLY when the
    # rest of that field is a recognized payment/in-kind annotation (never from an address field).
    fields = [f for f in re.split(r"\s{2,}", wln.rstrip()) if f != ""]
    for f in reversed(fields):
        f = f.strip()
        v = _num(f)
        if v is None:
            m = re.match(r"^(\$?-?[\d,]+(?:\.\d{1,2})?)\s+"
                         r"(in[\s\-]?kind|cash|check|paypal|venmo|credit|debit|card|zelle)\b",
                         f, re.I)
            v = _num(m.group(1)) if m else None
        if v is not None:
            start = wln.rstrip().rfind(f)
            return v, start
    return None, len(wln)


def _donor_name(body):
    """Donor from the columns before the amount. Joins a split First|Last (older forms) when the
    2nd column is a lone surname-shaped token and the 1st has no digits; else takes the 1st column
    (already-combined 'First Last' / org name). Strips an inline '(in kind)' marker."""
    body = re.sub(r"\(?\s*in[\s\-]?kind\s*\)?", "", body, flags=re.I).strip()
    fields = [f for f in re.split(r"\s{2,}", body) if f.strip()]
    if not fields:
        return ""
    donor = fields[0].strip()
    if len(fields) >= 2 and not re.search(r"\d", donor) \
            and re.fullmatch(r"[A-Za-z][A-Za-z.'’&\-]{0,19}", fields[1].strip()):
        donor = (donor + " " + fields[1].strip()).strip()
    return donor.rstrip(",")


def _merge_wraps(lines, start, end, ocr):
    """Reassemble wrapped rows: a date-led line whose amount overflowed onto the NEXT (non-date,
    non-total) line (a long mailing address pushes the amount down). Returns [(line_no, text)].
    An amount-less date-led line whose successor is ALSO date-led (e.g. an in-kind row) is left
    intact — never merged."""
    out = []
    k = start
    while k < end:
        wln = _norm(lines[k], ocr)
        if (_DATE_LEAD.match(wln) and _amount(wln, False)[0] is None
                and not _TOTAL_LINE.search(wln) and not _COLHDR.search(wln)
                and k + 1 < end):
            nxt = _norm(lines[k + 1], ocr)
            if (nxt.strip() and not _DATE_LEAD.match(nxt) and not _TOTAL_LINE.search(nxt)
                    and not _COLHDR.search(nxt) and _amount(nxt, False)[0] is not None):
                out.append((k, wln + "   " + nxt.strip()))
                k += 2
                continue
        out.append((k, wln))
        k += 1
    return out


def _parse_rows(lines, start, end, meta, ocr, is_contrib, running=False):
    rows = []
    method = meta["extract_method"]
    for k, wln in _merge_wraps(lines, start, end, ocr):
        if _TOTAL_LINE.search(wln) or _COLHDR.search(wln):
            continue
        dtok, _ = _peel_date(wln)
        if not dtok:
            continue                                  # data rows are date-led; skip prose/labels
        amt, astart = _amount(wln, running)
        if amt is None or amt == 0.0:
            # an in-kind row often prints "In Kind" instead of a dollar amount -> keep it, blank amt
            if is_contrib and _INKIND.search(wln):
                amt = None
            else:
                continue
        repaired = ocr and repair_money_line(_DOLLAR_SPACE.sub("$", lines[k]))[1]
        mtd = method + ("+repair" if repaired else "")
        _, body = _peel_date(wln[:astart])
        iso = _norm_date(dtok)
        if ocr and iso and not date_in_window(iso, meta):
            iso = ""
        inkind = bool(_INKIND.search(wln))
        if is_contrib:
            donor = _donor_name(body)
            if _AGG_DONOR.search(body) or donor.lower().startswith("under"):
                continue                              # ≤$50/≤$500 aggregate line: not an itemized donor
            rows.append(ContribRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                donor_raw=donor, amount=common.money_str(amt),
                in_kind="True" if inkind else "False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=str(k + 1), extract_method=mtd,
                needs_review="0" if (donor and amt is not None) else "1"))
        else:
            fields = [f for f in re.split(r"\s{2,}", body) if f.strip()]
            vendor = fields[0].strip() if fields else ""
            purpose = " ".join(f.strip() for f in fields[1:]).strip()
            rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=iso,
                vendor_raw=vendor, purpose=purpose, amount=common.money_str(amt),
                in_kind="True" if inkind else "False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=str(k + 1), extract_method=mtd,
                needs_review="0" if (vendor and amt is not None) else "1"))
    return rows


_PL = re.compile(r"profit\s*&?\s*(and\s+)?loss", re.I)


def parse(text: str, meta: dict) -> dict:
    ocr = bool(meta.get("is_scanned"))
    lines = text.splitlines()
    n = len(lines)

    stated_contrib = _stated_contrib(lines)
    stated_expend = _stated_expend(lines)

    # Section geometry. The Form-B (expenditures) header is the reliable divider; the Form-A
    # (contributions) header is OFTEN absent (the table just opens with a 'Date First Last ...'
    # column header), so contributions default to everything before Form B (the cover block +
    # column headers are dropped by _parse_rows' date-led filter). A 2017-era QuickBooks
    # 'Profit & Loss' export stands in for Form B on some filings — its rows do NOT map to the
    # form's Recipient/Purpose/Amount columns, so we do NOT parse them (honest flag), and it also
    # bounds the contributions region so P&L lines never leak in as donations.
    a_start = _find_section(lines, _A_HDR)
    b_start = _find_section(lines, _B_HDR, after=(a_start if a_start is not None else -1))
    pl_start = next((i for i, ln in enumerate(lines) if _PL.search(ln)), None)

    contrib_start = (a_start + 1) if a_start is not None else 0
    contrib_end = min(x for x in (b_start, pl_start, n) if x is not None and x > contrib_start)

    contrib_rows, expend_rows = [], []
    if contrib_end > contrib_start:
        running = _running_mode(lines, contrib_start, contrib_end, ocr)
        contrib_rows = _parse_rows(lines, contrib_start, contrib_end, meta, ocr, True, running)
    # A QuickBooks 'Profit & Loss' export (some 2017 filers) stands in for Form B — its
    # Type/Date/Name/Amount/Balance columns do NOT map to the form's Recipient/Purpose/Amount, and
    # its running Balance column would be summed as bogus expenditures. Leave the expenditure side
    # UNPARSED (stated total kept -> reconciles UNKNOWN, an honest flag), never fabricate rows.
    if b_start is not None and pl_start is None:
        e_running = _running_mode(lines, b_start + 1, n, ocr)   # QB Amount+Balance two-column guard
        expend_rows = _parse_rows(lines, b_start + 1, n, meta, ocr, False, e_running)

    notes = []
    agg = _find_total(lines, [r"\$?\s?50\.00 or less", r"aggregate total of contributions under",
                              r"cash contributions \(\$?\s?50", r"total under"])
    if agg:
        notes.append(f"unitemized ≤$50/$500 aggregate stated ${agg:.2f} (not itemized)")
    vik = None
    for ln in lines:
        if re.search(r"more than \$?\s?50", ln, re.I) and _INKIND.search(ln):
            vv = _values(ln, money_only=True)
            if len(vv) >= 2:
                vik = vv[-1]
    if vik:
        notes.append(f"in-kind (VIK) stated ${vik:.2f} (excluded from Form-A cash total)")
    if pl_start is not None:
        notes.append("expenditures are a QuickBooks Profit&Loss export (not mapped to Form B)")
    if a_start is None and b_start is None and pl_start is None:
        notes.append("non-standard form (no Form A/B sections found)")

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=None,
                notes="; ".join(notes))
