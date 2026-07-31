#!/usr/bin/env python3
"""westvalley_form.py — F8 extractor: West Valley City "CAMPAIGN FINANCE STATEMENT" (Form A/B).

The self-hosted WVC statutory form (UCA 10-3-208). GENUINELY DISTINCT from every prior family —
none of the seven's `$`-anchored tokenizers work here — so it is its own module:

  * numbered COVER totals are the reconciliation anchor (there is NO per-section printed TOTAL
    line, unlike Lehi / Orem / Ogden):
      "1. Total contributions          $X"   (Form "A" total)
      "2. Total campaign expenses      $Y"   (Form "B" total)
      "3. Balance at the end of reporting period   $Z"
    The `$` is frequently ABSENT (a bare "3,204.87") and the filled value is usually wrapped in
    template underscores ("$ __128.44__"), so the value is read as the RIGHTMOST numeric token on
    the (underscore-stripped) label line.

  * ITEMIZED CONTRIBUTION REPORT (FORM "A"): Date Received | Name of Contributor |
    Mailing Address & Zip Code | Amount of Contribution.
  * ITEMIZED EXPENDITURE REPORT (FORM "B"): Date | Recipient (+ Purpose) | Mailing Address |
    Amount. The two itemized sections appear in EITHER order (some filers print Form B first),
    and each header REPEATS on every page of a multi-page schedule — so sections are recovered by
    walking the doc and tagging each line with the most recent header (not a single [start,end)).

  * Amounts are BARE decimals (NO '$'), sitting to the RIGHT of an address column that itself
    carries a 5-digit ZIP and a street number — so common.money_spans ($-anchored) finds nothing.
    An amount is read as the RIGHTMOST cents-bearing token `d.dd` (the two-cent decimal keeps it
    distinct from a bare integer zip/street number/year). Born-digital fillable PDFs come in TWO
    layouts — horizontal (whole row on the date line) and VERTICAL (date / name / address / amount
    each on its OWN line) — handled uniformly by collecting a row's fields from the date-anchor
    line THROUGH the following lines until the next date anchor. A token that will not parse
    cleanly leaves the amount BLANK + needs_review — never a guessed digit (SCHEMA.md).

  * IN-KIND and LOAN are marked INLINE in the donor name ("Jennifer Fresques (In-kind)",
    "Chris Bell (Loan)") — there is NO separate in-kind section/column, and the cover "Total
    contributions" INCLUDES in-kind (form text: "gift of cash or non-monetary items such as
    in-kind contributions"), so reconciliation sums ALL rows (driver reconcile_cash_only=False).

Two modes by meta["is_scanned"]:
  * born-digital (pdftotext -layout): the whitespace column grid is clean -> split each line on
    2+ spaces and collect a row's fields across the block (horizontal + vertical layouts).
  * scanned (tesseract): single-spaced -> each dated line is one row; rightmost cents token =
    amount; shared currency-repair whitelist applied. HANDWRITTEN filings whose OCR yields no
    dated/cents rows produce ZERO rows and flag honestly (the gated-vision candidates).

is_incremental = True (per-period): verified Jake Fitisemanu 2021 general interim $3,204.87 ->
final $1,026.19 — a cumulative final would be >= the general interim; it is smaller, so each
report covers only its own period. cycle_totals.py does the per-candidate summary-vs-summed-
interim rollup (and flags the mixed cases).
"""
from __future__ import annotations

import re

import common
from common import ContribRow, ExpendRow, parse_date, repair_money_line, date_in_window

_UND = re.compile(r"_+")
# a data row STARTS with a transaction date (M/D/Y, optional 2-or-4-digit year); a leading table
# border '|' / spaces tolerated.
# A '/' or '-' date (M/D or M/D/Y), OR a fully-dotted M.D.Y — the dotted form REQUIRES all three
# parts so a bare cents amount ("20.00") is NEVER misread as a date "20.00" (which would orphan a
# vertical-layout amount into its own empty row-block).
_DATE_LEAD = re.compile(r"^[\s|]*(\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?|\d{1,2}\.\d{1,2}\.\d{2,4})\b")
# a cents-bearing money body: "1,234.56" / "50.00" (2 decimals REQUIRED so a 5-digit zip can
# never be read as an amount). Not preceded/followed by another digit or a '.'.
_CENTS_FIND = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+)\.(\d{2})(?![\d])")
_CENTS_FULL = re.compile(r"^\(?\$?\s*(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})\)?$")
_NUM_ANY = re.compile(r"[\d,]+(?:\.\d{1,2})?")
_ZIP = re.compile(r"\b\d{5}\b")

_FORMA = re.compile(r"ITEMI.?.?ED\s+CONTRIB", re.I)
_FORMB = re.compile(r"ITEMI.?.?ED\s+E.?PEND", re.I)
_FOOTER = re.compile(r"additional space is needed", re.I)
_COLHDR = re.compile(r"Name of Contributor|Mailing Address|Amount of|Person or Organization|"
                     r"Purpose of Expenditure|As Well As|^\s*Received\b|^\s*Date\b|"
                     r"^\s*Expenditure\b|^\s*Contribution\b", re.I)
_TOT_C = re.compile(r"Total\s+contributions", re.I)
_TOT_E = re.compile(r"Total\s+campaign\s+expenses", re.I)
_BAL = re.compile(r"Balance at the end", re.I)
_INKIND = re.compile(r"\bin[\s\-]?kind\b", re.I)
# a dateless carryover/previous-balance row (Scott Harmon 2025: "Previous balance ... 1829" folded
# into the cover total) — anchor it as a row so the printed figure is captured (date stays blank).
_CARRY = re.compile(r"previous balance|carr(?:y|ied)[\s-]?over|balance forward|carried forward",
                    re.I)


_LISTNUM = re.compile(r"^\s*\d+\.\s*")


def _label_total(lines, label_re):
    """RIGHTMOST numeric token on the first line matching label_re (underscores stripped first,
    and the leading list marker "1."/"2."/"3." REMOVED so a BLANK filled value never reads the
    list number as the total). Handles "$0", "$ __128.44__", and a bare "3,204.87". None when no
    digits remain (blank cover value -> unknown, never fabricated)."""
    for ln in lines:
        if label_re.search(ln):
            s = _LISTNUM.sub("", _UND.sub(" ", ln))
            vals = []
            for tok in _NUM_ANY.findall(s):
                try:
                    vals.append(float(tok.replace(",", "")))
                except ValueError:
                    pass
            if vals:
                return vals[-1]   # the filed value is rightmost ("1."/"2." list prefix is leftmost)
    return None


def _cents_num(tok):
    m = _CENTS_FULL.match(tok.strip())
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "") + "." + m.group(2))
    except ValueError:
        return None


# a money token WITHIN a field: a `$`-figure (optional space after $, optional cents — "$100",
# "$ 20", "$1,000.00") OR a bare cents number ("1,600.00", "50.00"). Single underscores between
# the address and the amount collapse to ONE space (not a 2+space column break), so the amount
# often lands glued onto the end of the address field — this finds it there.
_MONEY_IN_FIELD = re.compile(r"\$\s?-?[\d,]+(?:\.\d{2})?|(?<![\d.])[\d,]+\.\d{2}(?![\d])")
# a bare comma/plain integer amount ("1,600", "100") with NO $ and NO cents, as a standalone
# last field — accepted as a fallback but never a standalone 5-digit zip.
_BARE_INT = re.compile(r"\d{1,3}(?:,\d{3})+|\d{1,6}")


def _parse_money_tok(s):
    s = s.replace(" ", "")
    if not s.startswith("$"):
        s = "$" + s
    return common.parse_money(s)


def _find_amount(rest):
    """(amount, field_index) for a born-digital row's collected fields. Rightmost embedded
    `$`/cents money token wins; else a rightmost standalone bare integer (not a zip)."""
    for j in range(len(rest) - 1, -1, -1):
        ms = list(_MONEY_IN_FIELD.finditer(rest[j]))
        if ms:
            v = _parse_money_tok(ms[-1].group(0))
            if v is not None:
                return v, j
    for j in range(len(rest) - 1, -1, -1):
        t = rest[j].strip()
        if _BARE_INT.fullmatch(t) and not re.fullmatch(r"\d{5}", t):
            return float(t.replace(",", "")), j
    return None, None


def _peel_date(text, meta, ocr):
    """(iso_or_'', remainder). ISO blanked (amount kept) when OCR pushed the year out of window."""
    m = _DATE_LEAD.match(text.strip())
    if not m:
        return "", text.strip()
    iso = parse_date(m.group(1).replace(".", "/").replace("-", "/")) or ""
    if ocr and iso and not date_in_window(iso, meta):
        iso = ""
    return iso, text.strip()[m.end():].strip()


def _tag_sections(lines):
    """Walk the doc; return (contrib_lines, expend_lines) as [(lineno, rawline)]. Each Form A/B
    header (repeated per page) sets the current section; the 'additional space' footer ends it."""
    section = None
    contrib, expend = [], []
    for i, ln in enumerate(lines):
        if _FORMA.search(ln):
            section = "A"
            continue
        if _FORMB.search(ln):
            section = "B"
            continue
        if _FOOTER.search(ln):
            section = None
            continue
        if section == "A":
            contrib.append((i, ln))
        elif section == "B":
            expend.append((i, ln))
    return contrib, expend


def _mk_contrib(iso, name, in_kind, amount, meta, lineno):
    return ContribRow(
        candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
        election_year=meta["election_year"], filing_date=meta["filing_date"],
        reporting_period=meta.get("reporting_period", ""), date=iso,
        donor_raw=name, amount=common.money_str(amount), in_kind=str(in_kind),
        is_incremental="True", source_filing=meta["source_filing"],
        document_id=meta["document_id"], line_no=str(lineno), extract_method=meta["extract_method"],
        needs_review="0" if (amount is not None and name) else "1")


def _mk_expend(iso, vendor, purpose, in_kind, amount, meta, lineno):
    return ExpendRow(
        candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
        election_year=meta["election_year"], filing_date=meta["filing_date"],
        reporting_period=meta.get("reporting_period", ""), date=iso,
        vendor_raw=vendor, purpose=purpose, amount=common.money_str(amount),
        in_kind=str(in_kind), is_incremental="True", source_filing=meta["source_filing"],
        document_id=meta["document_id"], line_no=str(lineno), extract_method=meta["extract_method"],
        needs_review="0" if (amount is not None and vendor) else "1")


def _rows_digital(section_lines, meta, is_contrib):
    """Block-based: a row spans its date-anchor line THROUGH the following lines up to the next
    date anchor. Each line is 2+space column-split; the row's fields are collected across the
    block, so horizontal (all on the date line) and vertical (one field per line) both work."""
    blocks, cur = [], None
    for lineno, ln in section_lines:
        s = _UND.sub(" ", ln)
        if _COLHDR.search(s):
            cur = None                       # repeated page header ends the previous block
            continue
        fields = [f.strip() for f in re.split(r"\s{2,}", s) if f.strip()]
        if _DATE_LEAD.match(s.strip()) or (_CARRY.search(s) and _find_amount(fields)[0] is not None):
            cur = {"lineno": lineno + 1, "fields": list(fields)}
            blocks.append(cur)
        elif cur is not None and fields:
            cur["fields"].extend(fields)

    rows = []
    for b in blocks:
        fields = b["fields"]
        # peel the date off field[0]; KEEP its remainder — when the date and the name share a
        # field ("9/5/2023 UA Local 140" | "$500"), the name lives here, not in a later field.
        iso, head_rest = _peel_date(fields[0], meta, False)
        rest = ([head_rest] if head_rest else []) + fields[1:]
        amount, amt_i = _find_amount(rest)
        text_fields = []
        for k, f in enumerate(rest):
            f2 = _MONEY_IN_FIELD.sub("", f).strip() if k == amt_i else f
            if f2:
                text_fields.append(f2)
        in_kind = bool(_INKIND.search(" ".join(fields)))
        if not text_fields and amount is None:
            continue                          # empty template row (date only)
        if is_contrib:
            name = text_fields[0] if text_fields else ""
            rows.append(_mk_contrib(iso, name, in_kind, amount, meta, b["lineno"]))
        else:
            vendor = text_fields[0] if text_fields else ""
            addr_i = next((k for k in range(len(text_fields) - 1, 0, -1)
                           if _ZIP.search(text_fields[k])), None)
            purpose = " ".join(f for k, f in enumerate(text_fields)
                               if k not in (0, addr_i)).strip()
            rows.append(_mk_expend(iso, vendor, purpose, in_kind, amount, meta, b["lineno"]))
    return rows


def _split_name_addr_ocr(head):
    """OCR single-spaced 'Name 4882 Street, City ST 84125' -> (name, address): the name is the
    run BEFORE the first digit (a street number / PO box number). Conservative; never fabricates."""
    m = re.search(r"\d", head)
    if not m:
        return head.strip(" ,-"), ""
    return head[:m.start()].strip(" ,-"), head[m.start():].strip()


def _rows_scanned(section_lines, meta, is_contrib):
    """Line-based: each dated line is one row; rightmost cents token = amount."""
    rows = []
    for lineno, ln in section_lines:
        work = repair_money_line(_UND.sub(" ", ln))[0]
        s = work.strip()
        if not _DATE_LEAD.match(s):
            continue
        cents = list(_CENTS_FIND.finditer(s))
        if cents:
            mm = cents[-1]
            amount = float(mm.group(1).replace(",", "") + "." + mm.group(2))
            head = s[:mm.start()]
        else:
            amount, head = None, s
        iso, rest = _peel_date(head, meta, True)
        in_kind = bool(_INKIND.search(ln))
        method = meta["extract_method"] + ("+repair" if repair_money_line(_UND.sub(" ", ln))[1] else "")
        name, addr = _split_name_addr_ocr(rest)
        if is_contrib:
            r = _mk_contrib(iso, name, in_kind, amount, meta, lineno + 1)
        else:
            r = _mk_expend(iso, name, "", in_kind, amount, meta, lineno + 1)
        r.extract_method = method
        rows.append(r)
    return rows


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    ocr = bool(meta.get("is_scanned"))
    meta = dict(meta)
    meta.setdefault("reporting_period", "")

    stated_contrib = _label_total(lines, _TOT_C)
    stated_expend = _label_total(lines, _TOT_E)
    stated_end = _label_total(lines, _BAL)

    contrib_lines, expend_lines = _tag_sections(lines)
    fn = _rows_scanned if ocr else _rows_digital
    contrib_rows = fn(contrib_lines, meta, True)
    expend_rows = fn(expend_lines, meta, False)

    notes = "incremental(per-period); cover-total anchor"
    if ocr and not contrib_rows and not expend_rows:
        notes += "; scanned: no dated rows recovered (handwriting/OCR floor)"

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=stated_end,
                incremental=True, notes=notes)
