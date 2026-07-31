#!/usr/bin/env python3
"""ogden_form.py — extractor for Ogden City's self-hosted "Combined Report of Contributions &
Expenditures" WHOLE-CYCLE packet (the form Ogden posts on its Recorder Election-Information
pages; UCA 10-3-208 lineage but a distinct layout from `utah_standard_form`).

WHY A NEW FAMILY (not utah_standard_form): each Ogden PDF is a single packet that bundles the
candidate's *entire cycle* of statutory reports (First / Second / Third / Final), so the same
section headers repeat several times in one file. The itemization is organized as:

    FINANCIAL DISCLOSURE REPORT            (cover — reset)
    SUMMARY                                (numbered box, lines 1–6 — reset region, NOT scanned)
    ITEMIZED REPORT OF CAMPAIGN CONTRIBUTIONS  [– ATTACHMENT A]   Date/Name/Address/Amount/Purpose
        ... rows ...                       TOTAL <amt>  |  TOTAL CONTRIBUTIONS ($ amt)
    ITEMIZED REPORT OF CAMPAIGN EXPENDITURES   [– ATTACHMENT B]   Date/Name/Address/Amount/Purpose
        ... rows ...                       TOTAL <amt>  |  TOTAL EXPENDITURES ($ amt)
    (repeated per reporting period; the whole packet = one whole-cycle filing)

vs utah_standard_form's Cash/In-Kind/Cash-Expenditure sections each printed ONCE. Ogden also
records IN-KIND as a per-row flag ("Yes" column, or purpose "In-Kind"), NOT a separate section,
and a candidate may file a supplementary "REPORT OF CONTRIBUTIONS $750.00 OR GREATER" whose rows
DUPLICATE the regular Attachment A — that supplementary block is skipped (never double-counted).

RECONCILIATION ANCHOR (the "printed tally vs counted rows" discipline): per side, the itemized
row sum vs the SUM of every attachment's own printed TOTAL line across the packet. Two column
layouts are handled (older "DATE RECEIVED / NAME / ADDRESS / AMOUNT / PURPOSE" and the 2023 wide
"Date / First / Last / Address / City / State / Zip / Amount / Purpose"); a money token is a
`$`/`($ …)`-signed figure OR a bare `.dd` decimal (so zip codes / street numbers / years are
never mistaken for amounts). The amount is the RIGHTMOST money token on the row.

OCR mode (`meta["is_scanned"]`): the shared common.py currency-repair whitelist is applied; a
figure that will not parse cleanly stays BLANK + needs_review (never a guessed digit). A scanned
packet whose garbled TOTALs defeat reconciliation is the honest candidate for the gated vision
pass (driver `rows_override_fn`) — never fabricated.

is_incremental=False: the packet already aggregates the whole cycle (each donation itemized once
across its reporting period), so it behaves like Provo's whole-cycle summary — one filing per
candidate-cycle, no cross-filing dedup needed.
"""
from __future__ import annotations

import re

import common
from common import ContribRow, ExpendRow, parse_date, repair_money_line

# ------------------------------------------------------------------ money tokenizing
# A money token: a $-signed figure (optionally wrapped `($ … )`, with a space after $), OR a bare
# decimal ending in exactly two places (`2265.00`, `93.81`). Bare integers, zip codes, street
# numbers, phone fragments and years (no `$`, no `.dd`) are deliberately NOT money.
_MONEY = re.compile(
    r"\(?\s*-?\$\s?-?[\d,]+(?:\.\d{1,2})?\s*\)?"          # $-prefixed / ($ 1,234.56)
    # bare decimal ending in .dd: either comma-grouped (2,268.62) OR at most 5 leading digits
    # (2265.00, 93.81). The 5-digit cap stops a zip code glued to an amount by layout collapse
    # ("UT 8410528.62" = zip 84105 + 28.62) from forming a bogus 7-digit mega-amount.
    r"|(?<![\d.,$/\-])-?(?:\d{1,3}(?:,\d{3})+|\d{1,5})\.\d{2}(?![\d])")

# A dollar figure inside a PURPOSE description ("Donation of $50 or less", "$750 or Greater") is
# NOT the row's amount — neutralize these threshold phrases before amount detection so the real
# amount column wins (positions preserved with equal-length blanks).
_THRESH = re.compile(r"\$?\s?\d[\d,]*(?:\.\d{2})?\s+or\s+(?:less|greater|more)", re.I)

_DATE_LEAD = re.compile(
    r"^[\s|]*("
    r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}"                       # 2023-01-12
    r"|\d{1,2}[/\-.]\d{1,2}(?:[/\-.]\d{2,4})?"             # 11/16/2023, 6-3-19
    r"|\d{1,2}[\-\s][A-Za-z]{3,9}'?\d{0,4}"                # 24 Aug'21, 6/27
    r")")


def _val(tok: str):
    """Dollar value of a money token, or None. `($ 1,234.56)` -> 1234.56 ; `-$39.85` -> -39.85."""
    t = re.sub(r"[^\d.,\-]", "", tok)
    neg = t.count("-") % 2 == 1
    t = t.replace("-", "").replace(",", "")
    if t.count(".") > 1 or t in ("", "."):
        return None
    try:
        return (-1 if neg else 1) * float(t)
    except ValueError:
        return None


def _money_tokens(line: str):
    """[(start, end, value)] for every money token in the line."""
    out = []
    for m in _MONEY.finditer(line):
        v = _val(m.group(0))
        if v is not None:
            out.append((m.start(), m.end(), v))
    return out


# ---------------------------------------------------------------- section / line classifiers
# A header starts an attachment section. Besides the statutory "ITEMIZED REPORT OF CAMPAIGN …"
# and bare "Attachment A/B", some candidates append an exported ledger headed simply "… |
# Itemized Contributions/Expenditures up to …" (Mata), so bare "itemized" also triggers; the
# summary box never uses that word (it says "the table in Attachment A"), so this stays safe.
_HDR_START = re.compile(r"\bitemized\b|^\s*attachment\s+[ab]\b|report\s+of\s+contributions", re.I)
# summary-box fallback anchors (born-digital only): lines 4 (total contributions) and 5 (total
# expenditures) of the numbered SUMMARY box — the form's own printed cycle totals, used only when
# a filing's itemization is an appended ledger with NO per-attachment TOTAL line (Mata/Gale).
_L4 = re.compile(r"total\s+contributions\s+as\s+of\s+this\s+report", re.I)
_L5 = re.compile(r"total\s+expenditures\s+made\s+or\s+obligations", re.I)
_L6 = re.compile(r"balance\s+at\s+the\s+end", re.I)
_RESET = re.compile(r"financial\s+disclosure|^\s*summary\b|candidate\s+information|"
                    r"report\s+verification|reporting\s*period|balance\s+carried|"
                    r"balance\s+at\s+the\s+end", re.I)
_TOTAL = re.compile(r"\btotal\b", re.I)
_GREATER = re.compile(r"750(\.00)?\s*or\s*greater|or\s+greater", re.I)
_COLHDR = re.compile(r"complete\s*address|date\s+received|first\s+name|last\s+name|"
                     r"political\s+purpose|name\s+of\s+(donor|recipient|contributor)|"
                     r"attach\s+additional", re.I)
_INKIND = re.compile(r"\bin[\s\-]?kind\b", re.I)
_ADDR_START = re.compile(r"^(p\.?\s?o\.?\s*box|\d)", re.I)


def _side(lines, i):
    """Classify the attachment header starting at line i: 'contrib' / 'expend' / 'skip'
    (a $750-or-greater supplementary report) — reading a 3-line window because the header often
    wraps ('ITEMIZED REPORT OF CAMPAIGN' \\n 'CONTRIBUTIONS – ATTACHMENT A')."""
    window = " ".join(lines[i:i + 3]).lower()
    if _GREATER.search(window):
        return "skip"
    if "expenditure" in window:
        return "expend"
    if "contribution" in window:
        return "contrib"
    # bare 'Attachment A'/'Attachment B' with the label on the SAME line
    m = re.search(r"attachment\s+([ab])\b", window)
    if m:
        return "contrib" if m.group(1) == "a" else "expend"
    return "contrib"


def _peel_date(prefix: str):
    m = _DATE_LEAD.match(prefix)
    if m:
        return _norm_date(m.group(1)), prefix[m.end():].strip(" |")
    return "", prefix.strip(" |")


def _norm_date(dtok: str):
    import datetime
    m = re.match(r"^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$", dtok)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            return ""
    return parse_date(dtok) or parse_date(dtok.replace(".", "/")) or ""


def _split_name_addr(prefix: str):
    """From the text before the amount (leading date already peeled), return the party name:
    everything up to where the mailing address begins (first token that starts a street number or
    'PO Box'). Works for both column layouts and joins the 2023 wide 'First  Last' pair."""
    cols = [c for c in re.split(r"\s{2,}", prefix.strip()) if c]
    name_cols = []
    for c in cols:
        if _ADDR_START.match(c.strip()):
            break
        name_cols.append(c.strip())
    name = " ".join(name_cols).strip(" ,|")
    # collapse a run of internal spaces the wide layout leaves between First and Last
    return re.sub(r"\s{2,}", " ", name)


def _summary_total(lines, label_re, ocr):
    """Sum the numbered SUMMARY-box value on every line matching label_re. These Adobe fillable
    forms print the field value ON the label line, or (when the text layer is corrupted) on the
    line just ABOVE or below it, so scan outward L, L-1, L+1, L-2, L+2 and take the nearest money.
    Used by the completeness guard, not primary reconciliation."""
    total = None
    for i, ln in enumerate(lines):
        if not label_re.search(ln):
            continue
        val = None
        for j in (i, i - 1, i + 1, i - 2, i + 2):
            if j < 0 or j >= len(lines):
                continue
            work = repair_money_line(lines[j])[0] if ocr else lines[j]
            toks = _money_tokens(work)
            if toks:
                val = toks[-1][2]
                break
        if val is not None:
            total = (total or 0.0) + val
    return None if total is None else round(total, 2)


def _summary_val(lines, label_re, ocr, same_line_first):
    """Sum the printed value on every summary-box line matching label_re across the packet. The
    money sits on the label line itself (line 4) or on the immediately-following numbered line
    (line 5's amount prints under the '5'); scan [L, L+1, L+2] but never cross into line 6
    (the ending balance)."""
    total = None
    for i, ln in enumerate(lines):
        if not label_re.search(ln):
            continue
        val = None
        scan = range(i, min(i + 3, len(lines)))
        for j in scan:
            if j != i and _L6.search(lines[j]):
                break
            work = repair_money_line(lines[j])[0] if ocr else lines[j]
            toks = _money_tokens(work)
            if toks:
                val = toks[-1][2]
                if same_line_first or j > i:
                    break
        if val is not None:
            total = (total or 0.0) + val
    return None if total is None else round(total, 2)


def parse(text: str, meta: dict) -> dict:
    ocr = bool(meta.get("is_scanned"))
    lines = text.splitlines()
    n = len(lines)
    method = meta["extract_method"]

    contrib_rows, expend_rows = [], []
    stated_c = stated_e = None            # sum of attachment TOTAL lines (None until one is read)
    c_section_seen = e_section_seen = False
    state = "limbo"                        # limbo | contrib | expend | skip

    def add_stated(which, v):
        nonlocal stated_c, stated_e
        if which == "contrib":
            stated_c = (stated_c or 0.0) + v
        else:
            stated_e = (stated_e or 0.0) + v

    i = 0
    while i < n:
        raw = lines[i]
        work = repair_money_line(raw)[0] if ocr else raw
        work = _THRESH.sub(lambda m: " " * len(m.group(0)), work)  # blank purpose-embedded $ phrases
        low = work.lower()

        # section header?
        if _HDR_START.search(work):
            s = _side(lines, i)
            state = s
            if s == "contrib":
                c_section_seen = True
            elif s == "expend":
                e_section_seen = True
            i += 1
            continue
        # a reset line drops us out of any section (summary box, cover, verification)
        if _RESET.search(work):
            state = "limbo"
            i += 1
            continue

        if state in ("limbo", "skip"):
            i += 1
            continue

        toks = _money_tokens(work)
        # TOTAL line: closes the section; its rightmost money is the section's printed subtotal
        if _TOTAL.search(work):
            if toks:
                add_stated(state, toks[-1][2])
            state = "limbo"
            i += 1
            continue
        if _COLHDR.search(work) or not toks:
            i += 1
            continue

        # ---- a data row ----
        s_amt, e_amt, amount = toks[-1]
        if amount == 0.0:
            i += 1
            continue
        prefix = work[:s_amt]
        tail = work[e_amt:]
        dtok, body = _peel_date(prefix)
        in_kind = bool(_INKIND.search(work) or re.search(r"(?<![A-Za-z])Yes(?![A-Za-z])", tail))
        line_no = str(i + 1)
        if state == "contrib":
            donor = _split_name_addr(body)
            contrib_rows.append(ContribRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=dtok,
                donor_raw=donor, amount=common.money_str(amount),
                in_kind=str(in_kind), is_incremental="False",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=line_no, extract_method=method,
                needs_review="0" if donor else "1"))
        else:
            vendor = _split_name_addr(body)
            purpose = re.sub(r"^[\s)]*(Yes\b)?", "", tail).strip(" ,|")
            expend_rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
                election_year=meta["election_year"], filing_date=meta["filing_date"],
                reporting_period=meta.get("reporting_period", ""), date=dtok,
                vendor_raw=vendor, purpose=purpose, amount=common.money_str(amount),
                in_kind=str(in_kind), is_incremental="False",
                source_filing=meta["source_filing"], document_id=meta["document_id"],
                line_no=line_no, extract_method=method,
                needs_review="0" if vendor else "1"))
        i += 1

    # A side whose section IS present but printed no readable TOTAL and produced 0 rows is a
    # genuine NIL side (candidate reported nothing) -> 0.0 so it reconciles True. Never coerce a
    # populated side (that would falsely reconcile real rows against 0).
    if c_section_seen and stated_c is None and not contrib_rows:
        stated_c = 0.0
    if e_section_seen and stated_e is None and not expend_rows:
        stated_e = 0.0

    # Summary-box fallback (BORN-DIGITAL only — the summary is reliable there; OCR garble would
    # inject a wrong stated total, so scanned filings with no attachment TOTAL stay unknown and go
    # to the gated vision pass). Used when a side has itemized rows but no printed attachment TOTAL
    # (an appended ledger, e.g. Mata's spreadsheet / Gale's blank expenditure TOTAL): the form's own
    # printed line-4 (contributions) / line-5 (expenditures), summed across the packet's summary
    # boxes, is the reconciliation anchor.
    if not ocr:
        if stated_c is None and contrib_rows:
            v = _summary_val(lines, _L4, ocr, same_line_first=True)
            if v is not None:
                stated_c = v
        if stated_e is None and expend_rows:
            v = _summary_val(lines, _L5, ocr, same_line_first=False)
            if v is not None:
                stated_e = v

    notes = []
    # COMPLETENESS GUARD (born-digital only): the numbered SUMMARY box (line 4 = total
    # contributions, line 5 = total expenditures, one per reporting period) is the form's own
    # printed CYCLE total. When it MATERIALLY exceeds the sum of captured attachment TOTALs, an
    # entire report's itemization failed to extract (a corrupted Adobe text layer — the amounts
    # render as lone 's'/garbage), so the filing would otherwise FALSELY reconcile on a subset.
    # Adopt the summary figure as the stated total (the honest cycle total) so reconciliation fails
    # and the filing is flagged incomplete — never a silent undercount. Threshold (> $1,000 AND
    # > 50% over the captured total) tolerates a legitimately-unitemized ≤$50 aggregate.
    if not ocr:
        s4 = _summary_total(lines, _L4, ocr)
        s5 = _summary_total(lines, _L5, ocr)
        if s4 is not None and s4 > (stated_c or 0.0) + 1000 and s4 > (stated_c or 0.0) * 1.5:
            notes.append(f"incomplete extraction: summary states ${s4:,.2f} contributions but only "
                         f"${(stated_c or 0.0):,.2f} itemizable (corrupted text layer)")
            stated_c = s4
        if s5 is not None and s5 > (stated_e or 0.0) + 1000 and s5 > (stated_e or 0.0) * 1.5:
            notes.append(f"incomplete extraction: summary states ${s5:,.2f} expenditures but only "
                         f"${(stated_e or 0.0):,.2f} itemizable (corrupted text layer)")
            stated_e = s5
    if not (c_section_seen or e_section_seen):
        notes.append("no Ogden Attachment A/B sections found")

    return dict(contrib_rows=contrib_rows, expend_rows=expend_rows,
                stated_contrib=(None if stated_c is None else round(stated_c, 2)),
                stated_expend=(None if stated_e is None else round(stated_e, 2)),
                stated_begin=None, stated_end=None,
                notes="; ".join(notes))
