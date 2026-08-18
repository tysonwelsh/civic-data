#!/usr/bin/env python3
"""wasatch_disclosure_tableab.py — Wasatch County's 2024+ `CAMPAIGN FINANCIAL DISCLOSURE`
sheet (Table "A" / Table "B"), BORN-DIGITAL subset.

EVIDENCE (wasatch_county/campaign_finance/):
  * `CLAUDE.md` "THREE form variants" — `wasatch_disclosure_tableab` | cycles **2024, 2026** |
    49 filings | "`CAMPAIGN FINANCIAL DISCLOSURE` + Table A/B, **one TOTALS column** + a
    reporting-period checkbox list" | regime **period-scoped**. The two older variants
    (`carr_5_5_pg_4line` 2010/2022, `wasatch_fcr_3line` 2018/2020) are three-column CUMULATIVE
    sheets and are NOT this family.
  * `CLAUDE.md` #2 — "three filers say so in their own hand — … Forsyth 2026-06 prints
    *'(balance of $1,263.82 in campaign bank account from prior contributions previously
    reported)'*, and **Bonner's 2024 general covers 'Sep 26 to Oct 24' ($700 raised /
    $3,612.69 spent)**. So a cycle figure there is a **sum** across periods."
  * `CLAUDE.md` #4 — "Table A total, printed as the word *'zero'*, now yields
    `stated_total_contributions=0.00`" (Kahler 2026-03), which is the ZERO-GLYPH RULING.
  * The 2024 vintage of this sheet still cites **17-16-6.5** (only 2026 cites 17-70-4), so the
    statute header must NEVER be used to identify the variant — `build_index.py` was corrected
    on 2026-08-01 for exactly that (6 rows misfiled). This parser keys on the TITLE +
    the numbered `REPORTS … TOTALS` box, never on the statute line.

SHAPE

    REPORTS                                                     TOTALS
    1. Itemized total of all campaign contributions*
          (from Table "A" on page 2)                            $ 70.57
    2. Itemized total of all campaign expenditures*
          (from Table "B" on page 2)                            $1,062.84
    3. Balance at the end of the reporting period*
           (Difference between lines 1 & 2)                     $-992.27
    ...
    X General Report: Covering Sep 26 to Oct 24, 2024 – Filing Due date: October 29, 2024
                ITEMIZED CONTRIBUTION REPORT – TABLE "A"
    Date of  Name of Contributor        Amount   In-Kind / Tangible items (if applicable)
    ...                                          TOTAL: 0.00
                  ITEMIZED EXPENDITURE REPORT – TABLE "B"
    Date of      Person or Organization  Amount   Expenditure Purpose (optional)
    4/21/26      Sign A Rama             $1,000.22   Campaign Signs
    ...                                             TOTAL: $1,062.84

Deliberate decisions:
  * **The value cell may sit on the numbered line OR on its `(from Table …)` continuation** —
    both are searched, nearest-first, and the FIRST money-bearing line wins.
  * **The Amount column is read POSITIONALLY where the table header survives**, because Amount is
    NOT the last column: Table A prints `In-Kind / Tangible items` to its right and Table B prints
    `Expenditure Purpose` to its right, so a last-money-token reader would take an in-kind value
    as the cash amount. Where the header line is too degraded to locate `Amount`, the FIRST money
    token of the row is used (Amount precedes both trailing columns on every vintage) and the row
    says so via `needs_review`.
  * **The DATE GRAMMAR is explicit and enumerated** (extended 2026-08-14, tranche 3 Phase B).
    The date column is the FIRST field, so the leading-date match assigns every other column;
    Phase A knew only `M/D/YY(YY)` and three 2026 filers' own date styles therefore pushed the
    date into the NAME column (`donor_raw = "17 Jan 2026"`) with the amounts still summing
    exactly — the reconciliation-proof failure that the `wasatch-field-shift` calibration
    specimen exists to catch. `1.2.26` / `17 Jan 2026` / `5May26` / `Jan 17, 2026` are now
    matched, month names are ENUMERATED (never `[A-Za-z]{3,9}`, which would eat a blank-date
    row's vendor name), and a shape not listed stays UNMATCHED rather than guessed.
  * **The reporting period comes from the CHECKED box only** — `X` marks checked, `□` unchecked.
    A filing with no legible marker gets a BLANK period, never a guessed one (`CLAUDE.md`: 13
    filings mark none at all, 6 mark more than one — both are recorded as printed).
  * **A garbled scan yields NOTHING.** Bonner's 2024 general (`202411_746_…`) has a text layer,
    but its cover cells read `$ f -7 DD.oo` and `r Vbi&/"q`; the real $700.00 / $3,612.69 exist
    only in that filing's vision cache. This parser emits blank stated totals and a reason for
    exactly that filing — a garbled cell is never turned into a number.
  * **Zero-glyph** (GOTCHAS.md, owner 2026-08-02) via `common.parse_money_cell`: `zero` / `Ø` /
    `-0-` -> 0; a bare dash / `N/A` / an empty cell -> BLANK.
  * **PRIVACY** — Table A prints no donor address column at all on this sheet, so `donor_city` /
    `donor_state` are blank; nothing address-shaped is ever promoted into a row.

REGIME: period-scoped -> `is_incremental="True"`, `dedup_mode="incremental"`, declared PER FILING
(the driver's 2026-08-02 hook), because Wasatch's OTHER two variants on the same portal are
cumulative and a single run-level constant would mark one of them wrongly.
"""
from __future__ import annotations

import datetime
import re

import common
from common import (ContribRow, ExpendRow, parse_money_cell, money_cell_spans,
                    geom_text, page_line_index, parse_date)

_TITLE = re.compile(r"CAMPAIGN\s+FINANCIAL\s+DISCLOSURE", re.I)
_LINE1 = re.compile(r"^\s*1\.\s*Itemized\s+total\s+of\s+all\s+campaign\s+contributions", re.I)
_LINE2 = re.compile(r"^\s*2\.\s*Itemized\s+total\s+of\s+all\s+campaign\s+expenditures?", re.I)
_LINE3 = re.compile(r"^\s*3\.\s*Balance\s+at\s+the\s+end", re.I)

_TAB_A = re.compile(r"ITEMIZED\s+CONTRIBUTION\s+REPORT", re.I)
_TAB_B = re.compile(r"ITEMIZED\s+EXPENDITURES?\s+REPORT", re.I)
_TOTAL = re.compile(r"\bTOTAL\s*:?\s*(.*)$", re.I)
_AMT_HDR = re.compile(r"\bAmount\b", re.I)

# ---------------------------------------------------------------- THE DATE GRAMMAR (Phase B)
# The `Date of Donation` / `Date of expenditure` column is the FIRST field on this sheet, so the
# leading-date match is what assigns every other column. Phase A knew only `M/D/YY(YY)`, and three
# 2026 filers write dates their own way — so the date token stayed in the line body, became
# `fields[0]`, and landed in the NAME column while the real name slid one field right. The amounts
# still summed EXACTLY to the printed totals, so reconciliation could not see it, and all six
# affected sides were WITHHELD (wasatch CLAUDE.md "The born-digital itemized layer"; calibration
# specimen `wasatch-field-shift`).
#
# The three shapes, verified in the filings' own text layers (2026-08-14):
#   * `17 Jan 2026`, `5 Jan 2026`, `26 Feb 2026`   — Woodard 2026-03 (Tables A and B)
#   * `1.2.26`, `2.14.26`, `11 .7.25`              — Kellogg 2026-03 (dotted; note the stray space
#                                                     the text layer inserts before the first dot)
#   * `5May26`, `15Apr26`, `13May26`               — Vance 2026-06 (no separators at all)
# MONTH NAMES ARE ENUMERATED, never `[A-Za-z]{3,9}`: a bare alpha class would let a vendor row
# whose date cell is EMPTY ("May Company  $50.00") be eaten as a date, which is the same class of
# error this fix exists to remove. A shape not listed here is left UNMATCHED — the row then keeps
# its verbatim body and the field-shift screen still guards the side.
_MONTH_RX = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?"
             r"|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
_DATE_LEAD = re.compile(
    r"^\s*("
    r"\d{1,2}\s*[/\-]\s*\d{1,2}\s*[/\-]\s*\d{2,4}"        # 5/20/26   5-20-2026   (Phase A shape)
    r"|\d{1,2}\s*\.\s*\d{1,2}\s*\.\s*\d{2,4}"              # 1.2.26    11 .7.25
    r"|\d{1,2}\s*" + _MONTH_RX + r"\.?\s*,?\s*\d{2,4}"     # 17 Jan 2026   5May26
    r"|" + _MONTH_RX + r"\.?\s*\d{1,2}\s*,?\s*\d{2,4}"     # Jan 17, 2026  Jan. 17 26
    r")(?=\s|$)", re.I)

_MONTH_NUM = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def _iso_date(tok):
    """A Table A/B date cell -> ISO `YYYY-MM-DD`, or "" when it is not cleanly parseable.

    NEVER a guess: a two-digit year maps the way `%y` does (00-69 -> 2000s), an impossible
    calendar date returns "" and the verbatim stays in the row's own line. `common.parse_date`
    is tried FIRST so the shapes the shared helper already owns keep their shared behaviour;
    only the three wasatch-local shapes are added here, inside this family, so no other county's
    parse can move."""
    if not tok:
        return ""
    t = " ".join(str(tok).split())
    iso = parse_date(t)
    if iso:
        return iso
    m = re.fullmatch(r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{2,4})", t)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.fullmatch(r"(\d{1,2})\s*(" + _MONTH_RX + r")\.?\s*,?\s*(\d{2,4})", t, re.I)
        if m:
            d, mo, y = int(m.group(1)), _MONTH_NUM[m.group(2)[:3].lower()], int(m.group(3))
        else:
            m = re.fullmatch(r"(" + _MONTH_RX + r")\.?\s*(\d{1,2})\s*,?\s*(\d{2,4})", t, re.I)
            if not m:
                return ""
            mo, d, y = _MONTH_NUM[m.group(1)[:3].lower()], int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000 if y < 70 else 1900
    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        return ""
# a marked report-period box: `X`, `x`, or a filled bullet at the head of a `… Report:` line.
_CHECKED = re.compile(r"^\s*(?:X|x|☑|☒|■|●)\s+(.*Report.*)$")
_UNCHECKED = re.compile(r"^\s*(?:□|☐|\[\s*\]|o|O)\s")


_LABEL_TEXT = re.compile(
    r"^\s*\d\.\s*(?:Itemized\s+total\s+of\s+all\s+campaign\s+(?:contributions?|expenditures?)"
    r"|Balance\s+at\s+the\s+end\s+of\s+the\s+reporting\s+period)\*?"
    r"|\(?\s*from\s+Table\s*[\"“”']?\s*[AB]\s*[\"“”']?\s*on\s+page\s*\d*\s*\)?"
    r"|\(?\s*Difference\s+between\s+lines?\s*1\s*&\s*2\s*\)?", re.I)
_STOP = re.compile(r"^\s*\d\.\s|\(initial\)|ITEMIZED\s+(?:CONTRIBUTION|EXPENDITURE)", re.I)


def _cell_region(ln):
    """The line with its PRINTED label/continuation text removed — what is left is the filer's
    own TOTALS cell (plus, on a bad scan, scanner noise)."""
    return _LABEL_TEXT.sub(" ", ln)


def _box_value(lines, i):
    """The TOTALS cell for a numbered REPORTS line -> (value, kind, line_index, span).

    STRICT, because a garbled scan is the failure mode this form actually has. A cell is accepted
    ONLY when its region (the line minus the form's own printed label / `(from Table "A" on page
    2)` continuation) contains EXACTLY ONE money token and NOTHING else alphanumeric. Bob Adams'
    2024-06 filing renders `(from Table "A" on page 2) ) i} O < 2.2 4` — one money-shaped token
    (`2.2`) surrounded by scanner noise; a first-token reader publishes `$2.20` as his contribution
    total. It is rejected here as `garbled` and the figure stays blank."""
    for j in range(i, min(i + 4, len(lines))):
        if j > i and _STOP.match(lines[j]):
            break
        region = _cell_region(lines[j])
        if not region.strip():
            continue
        sp = money_cell_spans(region)
        residue = region
        for s, e, _v, _r in sp:
            residue = residue[:s] + " " * (e - s) + residue[e:]
        clean = not re.search(r"[A-Za-z0-9]", residue)
        if len(sp) == 1 and clean:
            s, e, v, _raw = sp[0]
            return v, "money", j, (s, e)
        if sp and not clean:
            return None, "garbled", None, None
        if len(sp) > 1:
            return None, "ambiguous (more than one figure in the cell)", None, None
        if not clean:
            v, kind = parse_money_cell(region.strip())
            if kind in ("money", "zero-glyph", "nil"):
                return v, kind, j, None
            return None, "garbled", None, None
    return None, "empty", None, None


def _table_total(lines, start, stop):
    """`TOTAL: <cell>` inside a table section -> (value, kind, verbatim)."""
    for j in range(start, stop):
        m = _TOTAL.search(lines[j])
        if m:
            raw = m.group(1).strip()
            v, kind = parse_money_cell(raw)
            return v, kind, raw
    return None, "empty", ""


def _amount_col(lines, start, stop):
    """Character column of the `Amount` header inside a table section, or None."""
    for j in range(start, min(start + 6, stop)):
        m = _AMT_HDR.search(lines[j])
        if m:
            return m.start()
    return None


def _pick_amount(ln, amt_col):
    """(value, span, positional_bool). Positional where the Amount header was located — Amount is
    NOT the rightmost column on this sheet, so a last-token reader takes In-Kind / Purpose money."""
    sp = money_cell_spans(ln)
    if not sp:
        return None, None, False
    if amt_col is not None:
        best = min(sp, key=lambda t: abs((t[0] + t[1]) // 2 - amt_col))
        return best[2], (best[0], best[1]), True
    s, e, v, _raw = sp[0]
    return v, (s, e), False


def _rows(lines, start, stop, meta, is_contrib, pl):
    amt_col = _amount_col(lines, start, stop)
    out = []
    method = meta.get("extract_method", "wasatch_disclosure_tableab/text")
    for k in range(start, stop):
        ln = lines[k]
        if _TOTAL.search(ln) or _AMT_HDR.search(ln):
            continue
        amount, span, positional = _pick_amount(ln, amt_col)
        if amount is None:
            continue
        dm = _DATE_LEAD.match(ln)
        body = ln[dm.end():span[0]] if dm else ln[:span[0]]
        if not re.search(r"[A-Za-z]{2}", body) and not dm:
            continue
        fields = [t for t in re.split(r"\s{2,}", body.strip()) if t.strip()]
        name = fields[0].strip() if fields else ""
        extra = " ".join(f.strip() for f in fields[1:]).strip()
        tail = ln[span[1]:].strip()
        page, lno = pl[k] if k < len(pl) else (1, k + 1)
        geo = geom_text(page, lno, span[0], span[1])
        iso = _iso_date(dm.group(1)) if dm else ""
        review = "0" if (name and positional) else "1"
        if is_contrib:
            out.append(ContribRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso or "", donor_raw=name, amount=common.money_str(amount),
                in_kind="True" if tail else "False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(k + 1), extract_method=method, needs_review=review, geometry=geo))
        else:
            out.append(ExpendRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso or "", vendor_raw=name, purpose=(extra + " " + tail).strip(),
                amount=common.money_str(amount), in_kind="False", is_incremental="True",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(k + 1), extract_method=method, needs_review=review, geometry=geo))
    return out


def _periods(lines):
    """Verbatim labels of the CHECKED report-period boxes, in printed order."""
    out = []
    for ln in lines:
        if _UNCHECKED.match(ln):
            continue
        m = _CHECKED.match(ln)
        if m and "Report" in m.group(1):
            out.append(re.sub(r"\s{2,}", " ", m.group(1)).strip())
    return out


def _gate(rows, stated, side, notes):
    """Rows survive only when they SUM to the figure the driver reconciles them against."""
    if not rows:
        return []
    total = round(sum(float(r.amount) for r in rows if r.amount), 2)
    if stated is not None and abs(total - stated) <= 0.01:
        return rows
    notes.append(f"{side}: {len(rows)} row(s) NOT emitted -- Sum rows {total:.2f} != stated "
                 f"{'blank' if stated is None else format(stated, '.2f')}; an unproven ledger is "
                 f"not published")
    return []


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    pl = page_line_index(text)
    notes = []

    def _find(rx):
        for i, ln in enumerate(lines):
            if rx.match(ln):
                return i
        return None

    # Identify the variant by the NUMBERED REPORTS box, not by the printed title and NEVER by the
    # statute line: several sidecars lose the title to a DocuSign envelope banner (Forsyth 2026-06)
    # while the box survives, and the 2024 vintage of THIS sheet still cites 17-16-6.5 — the exact
    # mistake that misfiled 6 rows in `build_index.py` before 2026-08-01.
    n_title = sum(1 for ln in lines if _TITLE.search(ln))
    if _find(_LINE1) is None and _find(_LINE2) is None and not n_title:
        return dict(contrib_rows=[], expend_rows=[], stated_contrib=None, stated_expend=None,
                    stated_begin=None, stated_end=None,
                    notes="not a CAMPAIGN FINANCIAL DISCLOSURE (Table A/B) sheet — nothing read")
    if n_title > 1:
        notes.append(f"{n_title} report faces in this PDF; the FIRST is parsed (a multi-report "
                     f"bundle needs one index row per report)")

    vals = {}
    for key, rx in (("c", _LINE1), ("e", _LINE2), ("b", _LINE3)):
        i = _find(rx)
        if i is None:
            notes.append(f"line {'1' if key == 'c' else '2' if key == 'e' else '3'} not printed")
            vals[key] = None
            continue
        v, kind, _j, _sp = _box_value(lines, i)
        vals[key] = v if kind in ("money", "zero-glyph") else None
        if kind not in ("money", "zero-glyph"):
            notes.append(f"line {'1' if key == 'c' else '2' if key == 'e' else '3'} cell is "
                         f"{kind} -- left BLANK, never repaired")

    ia = _find(_TAB_A) if _find(_TAB_A) is not None else None
    ia = next((i for i, ln in enumerate(lines) if _TAB_A.search(ln)), None)
    ib = next((i for i, ln in enumerate(lines) if _TAB_B.search(ln)), None)
    a_stop = ib if (ia is not None and ib is not None and ib > ia) else len(lines)
    b_stop = len(lines)

    ta = tb = None
    if ia is not None:
        ta_v, ta_k, ta_raw = _table_total(lines, ia, a_stop)
        if ta_k in ("money", "zero-glyph"):
            ta = ta_v
            if ta_k == "zero-glyph":
                notes.append(f'Table "A" TOTAL printed as {ta_raw!r} -> 0.00 (ZERO-GLYPH RULING)')
    if ib is not None:
        tb_v, tb_k, tb_raw = _table_total(lines, ib, b_stop)
        if tb_k in ("money", "zero-glyph"):
            tb = tb_v
            if tb_k == "zero-glyph":
                notes.append(f'Table "B" TOTAL printed as {tb_raw!r} -> 0.00 (ZERO-GLYPH RULING)')

    stated_contrib = vals["c"] if vals["c"] is not None else ta
    stated_expend = vals["e"] if vals["e"] is not None else tb
    if vals["c"] is None and ta is not None:
        notes.append('contributions promoted from the Table "A" TOTAL (line 1 cell blank)')
    if vals["e"] is None and tb is not None:
        notes.append('expenditures promoted from the Table "B" TOTAL (line 2 cell blank)')

    crows = _rows(lines, ia + 1, a_stop, meta, True, pl) if ia is not None else []
    erows = _rows(lines, ib + 1, b_stop, meta, False, pl) if ib is not None else []
    crows = _gate(crows, stated_contrib, "contributions", notes)
    erows = _gate(erows, stated_expend, "expenditures", notes)

    periods = _periods(lines)
    if periods:
        notes.append("period box(es) checked: " + " | ".join(periods[:4]))
    else:
        notes.append("no report-period box legibly marked -- period left blank, never guessed")

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=vals["b"],
                is_incremental="True", dedup_mode="incremental",
                notes="; ".join(notes))
