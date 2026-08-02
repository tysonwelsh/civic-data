#!/usr/bin/env python3
"""cache_cfd.py — Cache County's 2022+ born-digital `Financial Campaign Report for County
Offices and Local School Board Candidates` (the "CFD" instrument).

EVIDENCE (cache_county/campaign_finance/):
  * `CLAUDE.md` "Shared-script need (described, not built)" — "Registering `cache_cfd` would be
    worthwhile **only for the 2022+ born-digital subset**, and needs two genuinely new driver
    capabilities: itemized rows are **free-typed one-liners**
    (`3/18/26 - Mark Hurd - 168 S 50 W Hyde Park, UT - $12.42`), not a ruled table, so the
    tokenizer must split on ` - ` rather than columns; and `is_incremental` must be settable
    **per filing** rather than per city. The pre-2022 Carr era is handwriting — not parseable by
    any text pipeline, which is exactly why the vision layer exists."
  * `CLAUDE.md` "`is_incremental` is a property OF EACH FILING here, not of the county" —
    "Cache's 2022+ form prints **both** a 'This Period' and a 'Year-to-Date' column, so whether a
    report is incremental is fixed per filing": `period_and_ytd_differ` 24 (genuinely
    incremental) · `period_equals_ytd` 58 · `ytd_only` 3 · `period_only` 3 · `neither` 3.
  * `CLAUDE.md` "A printed word is not a number" — "'None' / '-0-' become a decimal zero only
    when the word IS a stated zero; 'NA'/'N/A' means *not applicable* and stays blank."
  * Anchors read at the source 2026-08-02: `text/2026_cc_2026_Financial_Disclosure_Apr_3_Mark_
    Hurd.txt` (the dash-tokenized style) and `…_June16_Mark_Hurd.txt` (the whitespace style).

SHAPE

    Schedule A - Itemized Contributions Received
    Date       Name of Contributor        Address and Zip Code        Amount
    3/18/26 - Mark Hurd - 168 S 50 W Hyde Park, UT - $12.42      <- style 1: " - " tokens
    April 8 Mark Hurd 168 S 50 W HP UT 59.74                     <- style 2: free whitespace
                                        Total Contributions Received $ 316.72
    Schedule B - Itemized Expenditures Made
    3/25/26 - Amazon - Health Days Parade - $41.12
                                        Total Expenditures Made $ 508.83
    Summary Page
     Balance at Beginning of Reporting Period
     A     238.77
    Contributions Received This Period        Contributions Received Year-to-Date
    B  316.72                                 C  491.73
    Expenditures Made This Period             Expenditures Made Year-to-Date
    D  508.83                                 E  1122.71
     Subtotal Before Expenditures (Box A + Box B)      F  555.49
    Balance at Close of Reporting Period (Box F - Box D)     46.66

THE TWO CAPABILITIES THIS FAMILY NEEDS, AND HOW THEY ARE USED
  1. **Per-FILING `is_incremental`** — read off Box B vs Box C. A This-Period box printed at all
     ⇒ the itemization is period-scoped ⇒ `is_incremental="True"` + `dedup_mode="incremental"`,
     and Box B / Box D are the reconciliation anchors. A filing that prints ONLY the Year-to-Date
     boxes ⇒ `"False"` + `"cumulative"` (the latest report is the cycle total). Neither is assumed
     county-wide, because Cache demonstrably files both ways in the same cycle.
  2. **The " - " tokenizer** — the ledger is free text typed into one cell, not columns. Rows are
     split on ` - ` (and on `word- ` — filers omit the leading space: `Amazon- 100 pk balloons-
     $8.57`); FIRST token = date, LAST = amount, middle = name (+ address) or vendor (+ purpose).

PRIVACY — the binding constraint here. The tokenized address is `168 S 50 W Hyde Park, UT`, i.e.
a STREET ADDRESS. Only `donor_city` / `donor_state` are ever emitted (`common.split_city_state`);
the street portion is discarded and NEVER written to `donor_raw` or anywhere else. In the
whitespace style, where name and address are not delimited, a row is emitted ONLY when a street
start (a numeric token, or `PO Box`) marks the boundary; if it cannot be found the row is
**skipped with a reason** rather than published with the street inside the donor name.

MONEY — `common.parse_money_cell`, so the ZERO-GLYPH RULING (GOTCHAS.md, owner 2026-08-02)
applies: `Ø` / `-0-` / "zero" -> 0; a bare dash / `N/A` / `None` / an empty cell -> BLANK. Nothing
is repaired: the Apr-3 filing prints `Subtotal for this page $$397.76` (a doubled `$`), which is
not a clean cell and is left alone — the parser reads the `Total … $ $397.76` line's own token.

Geometry: `p<page>:l<line>:c<col0>-<col1>` on the AMOUNT token of every row and on each summary
box cell's source line (SCHEMA.md §2a).
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_money_cell, money_cell_spans,
                    split_city_state, geom_text, page_line_index, parse_date, date_in_window)

_SCHED_A = re.compile(r"Schedule\s*A\s*[-–—]\s*Itemized\s+Contributions", re.I)
_SCHED_B = re.compile(r"Schedule\s*B\s*[-–—]\s*Itemized\s+Expenditures", re.I)
_SUMMARY = re.compile(r"^\s*Summary\s+Page\s*$", re.I)
_TOT_C = re.compile(r"Total\s+Contributions\s+Received", re.I)
_TOT_E = re.compile(r"Total\s+Expenditures\s+Made", re.I)
_SUBTOTAL = re.compile(r"Subtotal\s+for\s+this\s+page", re.I)
_HDR_ROW = re.compile(r"Name\s+of\s+Contributor|Provider\s*/\s*Vendor|Attach\s+additional", re.I)
_NOISE = re.compile(r"Candidate\s+Financial\s+Disclosure|Name\s+of\s+Candidate|Date\s+of\s+Report"
                    r"|Sum\s+of\s+all\s+Schedule", re.I)

# Box labels on the Summary Page. The letter sits on its own (shared) line and the figure on the
# next, so B/C and D/E are read POSITIONALLY — the letter's column picks its own figure.
_BOX_BC = re.compile(r"Contributions\s+Received\s+This\s+Period", re.I)
_BOX_DE = re.compile(r"Expenditures\s+Made\s+This\s+Period", re.I)
_BOX_A = re.compile(r"Balance\s+at\s+Beginning\s+of\s+Reporting\s+Period", re.I)
_BOX_CLOSE = re.compile(r"Balance\s+at\s+Close\s+of\s+Reporting\s+Period", re.I)
_LETTERS = re.compile(r"(?<![A-Za-z])([A-F])(?![A-Za-z])")

# " - " tokenizer: a dash with whitespace on BOTH sides, or a dash glued to the previous word and
# followed by whitespace (`Amazon- 100 pk`). A hyphenated name (`Smith-Jones`) has no trailing
# whitespace and is never split.
_DASH_SPLIT = re.compile(r"\s+[-–—]\s+|(?<=\w)[-–—]\s+")
_STREET_START = re.compile(r"^(?:\d+[A-Za-z]{0,2}|P\.?O\.?|PO)$", re.I)

# A TRAILING bare integer is a real amount in these free-typed cells (`May 3 Mark Hurd 168 S 50 W
# HP UT 150`, `April 9 cache GOP convention table 50`) even though the library deliberately does
# not treat a bare integer as money anywhere a stray page number could be mistaken for one. It is
# accepted ONLY at the very end of a row, and NEVER when it is a 5-digit ZIP sitting behind a
# state abbreviation — which is what an amount-less address row ends with.
_TRAIL_NUM = re.compile(r"(?<![\d.,])(\$?\s*\d{1,7}(?:\.\d{1,2})?)\s*$")
_ZIP_TAIL = re.compile(r"\b[A-Z]{2},?\s+\d{5}(?:-\d{4})?\s*$")


def _amount_span(txt):
    """(start, end, value) of the row's AMOUNT, or None. A `$`/decimal token wins; otherwise a
    trailing bare integer is accepted under the guards above."""
    sp = money_cell_spans(txt)
    if sp:
        s, e, v, _raw = sp[-1]
        return s, e, v
    if _ZIP_TAIL.search(txt):
        return None
    m = _TRAIL_NUM.search(txt)
    if m:
        v, kind = parse_money_cell(m.group(1))
        if kind == "money":
            return m.start(1), m.end(1), v
    return None


def _sections(lines):
    """(a_start, a_stop, b_start, b_stop, summary_start) — indices into `lines`."""
    a = b = s = None
    for k, ln in enumerate(lines):
        if a is None and _SCHED_A.search(ln):
            a = k
        elif b is None and _SCHED_B.search(ln):
            b = k
        elif s is None and _SUMMARY.search(ln):
            s = k
    n = len(lines)
    a_stop = b if (a is not None and b is not None and b > a) else (s if s is not None else n)
    b_stop = s if (b is not None and s is not None and s > b) else n
    return a, a_stop, b, b_stop, s


def _join_wrapped(lines, start, stop):
    """Yield (first_line_index, joined_text) for ledger rows, joining a line that carries no
    trailing amount to the next (the June-16 filing wraps a long purpose:
    `April 8 Sam's Club Peanut M&Ms/Granola` + `Bars/Cheese Its / bottled water 59.74`)."""
    buf, buf_k = "", None
    for k in range(start, stop):
        ln = lines[k]
        if not ln.strip() or _HDR_ROW.search(ln) or _NOISE.search(ln) \
                or _TOT_C.search(ln) or _TOT_E.search(ln) or _SUBTOTAL.search(ln):
            if buf:
                yield buf_k, buf
                buf, buf_k = "", None
            continue
        # A line whose ONLY content is money is a stray page/section subtotal (the form prints
        # `Subtotal for this page $613.88` with the figure repeated on its own line under the
        # candidate's name). Joining it to a buffered name manufactures a $613.88 "payment to
        # Mark Hurd" that is really the schedule total — so it ends the buffer instead.
        if not re.sub(r"[\s$]+", "", re.sub(r"[\d.,]+", "", ln)) and _amount_span(ln.strip()):
            buf, buf_k = "", None
            continue
        cand = (buf + " " + ln.strip()).strip() if buf else ln.strip()
        if buf_k is None:
            buf_k = k
        if _amount_span(cand):
            yield buf_k, cand
            buf, buf_k = "", None
        else:
            buf = cand
            if len(buf) > 400:                      # runaway join -> give up honestly
                yield buf_k, buf
                buf, buf_k = "", None
    if buf:
        yield buf_k, buf


def _tokens(txt):
    """Free-typed row -> (date_token, middle_parts, amount, span) or None. Style 1 (" - ") is
    tried first; style 2 falls back to leading-date + trailing-amount with the middle as one
    string."""
    got = _amount_span(txt)
    if not got:
        return None
    s, e, amount = got
    head = txt[:s].strip()
    if len(re.findall(r"[A-Za-z]", head)) < 2:
        return None            # a bare figure on its own line is a subtotal, not a ledger row
    parts = [p.strip() for p in _DASH_SPLIT.split(txt) if p.strip()]
    if len(parts) >= 3 and parse_money_cell(parts[-1])[1] == "money":
        return parts[0], parts[1:-1], amount, (s, e), "dash"
    dm = re.match(r"^([A-Za-z]{3,9}\.?\s+\d{1,2}(?:,?\s+\d{4})?|\d{1,2}[/\-]\d{1,2}"
                  r"(?:[/\-]\d{2,4})?)\s+(.*)$", head)
    if dm:
        return dm.group(1), [dm.group(2).strip()], amount, (s, e), "whitespace"
    return "", [head], amount, (s, e), "whitespace"


def _split_name_address(blob):
    """('Mark Hurd', '168 S 50 W HP UT') or (None, None) when the boundary is not provable.
    NEVER returns the street inside the name — that is the PRIVACY guarantee."""
    toks = blob.split()
    for i, t in enumerate(toks):
        if i and _STREET_START.match(t.strip(",")):
            return " ".join(toks[:i]).strip(" ,"), " ".join(toks[i:])
    return None, None


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    pl = page_line_index(text)
    notes = []
    a, a_stop, b, b_stop, s = _sections(lines)
    if a is None and b is None:
        return dict(contrib_rows=[], expend_rows=[], stated_contrib=None, stated_expend=None,
                    stated_begin=None, stated_end=None,
                    notes="no Schedule A/B header — not the born-digital cache_cfd instrument "
                          "(the pre-2022 Carr sheet is handwriting; read its vision cache)")

    # ---------------------------------------------------------------- Summary Page boxes
    def _pair(rx):
        """A This-Period / Year-to-Date box pair, matched by the LETTER column on the line
        carrying the letters and the figure directly beneath it."""
        for i, ln in enumerate(lines):
            if not rx.search(ln):
                continue
            for j in range(i + 1, min(i + 3, len(lines))):
                letters = [(m.group(1), m.start()) for m in _LETTERS.finditer(lines[j])]
                if not letters:
                    continue
                figs = []
                for jj in range(j, min(j + 3, len(lines))):
                    figs = money_cell_spans(lines[jj])
                    if figs:
                        break
                out = {}
                for name, col in letters:
                    if not figs:
                        break
                    best = min(figs, key=lambda t: abs(t[0] - col))
                    out[name] = (best[2], jj, best[0], best[1])
                return out
            return {}
        return {}

    def _single(rx):
        for i, ln in enumerate(lines):
            if not rx.search(ln):
                continue
            for j in range(i, min(i + 4, len(lines))):
                figs = money_cell_spans(lines[j])
                if figs:
                    return figs[0][2], j, figs[0][0], figs[0][1]
        return None, None, None, None

    bc, de = _pair(_BOX_BC), _pair(_BOX_DE)
    box_b = bc.get("B", (None,))[0]
    box_c = bc.get("C", (None,))[0]
    box_d = de.get("D", (None,))[0]
    box_e = de.get("E", (None,))[0]
    box_a, _ja, _ca0, _ca1 = _single(_BOX_A)
    box_close, _jc, _cc0, _cc1 = _single(_BOX_CLOSE)

    def _printed_total(rx, start, stop):
        for k in range(start or 0, stop or len(lines)):
            if rx.search(lines[k]):
                figs = money_cell_spans(lines[k])
                if figs:
                    return figs[-1][2]
                for j in range(k + 1, min(k + 3, len(lines))):
                    figs = money_cell_spans(lines[j])
                    if figs:
                        return figs[-1][2]
        return None

    sched_a_total = _printed_total(_TOT_C, a, a_stop) if a is not None else None
    sched_b_total = _printed_total(_TOT_E, b, b_stop) if b is not None else None

    stated_contrib = box_b if box_b is not None else (
        sched_a_total if sched_a_total is not None else box_c)
    stated_expend = box_d if box_d is not None else (
        sched_b_total if sched_b_total is not None else box_e)

    # ------------------------------------------------- PER-FILING regime (the cache capability)
    if box_b is not None or box_d is not None:
        incremental, regime = "True", "incremental"
        if box_c is not None and box_b is not None:
            basis = ("period_and_ytd_differ" if abs(box_c - box_b) > 0.005
                     else "period_equals_ytd")
        else:
            basis = "period_only"
    elif box_c is not None or box_e is not None:
        incremental, regime, basis = "False", "cumulative", "ytd_only"
    else:
        incremental, regime, basis = "", "", "neither"
    notes.append(f"period_basis={basis or 'neither'}"
                 + (f"; is_incremental={incremental}" if incremental else
                    " (no This-Period or Year-to-Date box printed — regime NOT asserted)"))
    if box_c is not None:
        notes.append(f"contributions Year-to-Date (Box C) stated ${box_c:,.2f} — never summed "
                     f"as an increment")
    if box_e is not None:
        notes.append(f"expenditures Year-to-Date (Box E) stated ${box_e:,.2f} — never summed "
                     f"as an increment")

    # ------------------------------------------------------------------------ ledger rows
    method = meta.get("extract_method", "cache_cfd/text")
    crows, erows, skipped = [], [], []

    if a is not None:
        for k, txt in _join_wrapped(lines, a + 1, a_stop):
            tk = _tokens(txt)
            if tk is None:
                continue
            dtok, mids, amount, span, style = tk
            blob = " ".join(mids).strip()
            if style == "dash" and len(mids) >= 2:
                name, addr = mids[0], " ".join(mids[1:])
            else:
                name, addr = _split_name_address(blob)
                if name is None:
                    skipped.append(f"line {k + 1}: contribution row NOT emitted — the donor name "
                                   f"and street address are not separable in this free-typed row, "
                                   f"and a street address is never published (PRIVACY.md)")
                    continue
            city, state = split_city_state(addr)
            iso = parse_date(dtok) or ""
            if iso and not date_in_window(iso, meta):
                skipped.append(f"line {k + 1}: contribution date {dtok!r} reads {iso} — outside "
                               f"the filing's plausible window; date left BLANK, amount kept")
                iso = ""
            page, lno = pl[k] if k < len(pl) else (1, k + 1)
            crows.append(ContribRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, donor_raw=name, donor_city=city, donor_state=state,
                amount=common.money_str(amount), in_kind="False", is_incremental=incremental,
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(k + 1), extract_method=f"{method}/{style}",
                needs_review="0" if (name and iso) else "1",
                geometry=geom_text(page, lno, span[0], span[1])))

    if b is not None:
        for k, txt in _join_wrapped(lines, b + 1, b_stop):
            tk = _tokens(txt)
            if tk is None:
                continue
            dtok, mids, amount, span, style = tk
            if style == "dash" and len(mids) >= 2:
                vendor, purpose = mids[0], " ".join(mids[1:])
            else:
                vendor, purpose = " ".join(mids).strip(), ""
            iso = parse_date(dtok) or ""
            if iso and not date_in_window(iso, meta):
                skipped.append(f"line {k + 1}: expenditure date {dtok!r} reads {iso} — outside "
                               f"the filing's plausible window; date left BLANK, amount kept")
                iso = ""
            page, lno = pl[k] if k < len(pl) else (1, k + 1)
            erows.append(ExpendRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, vendor_raw=vendor, purpose=purpose,
                amount=common.money_str(amount), in_kind="False", is_incremental=incremental,
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(k + 1), extract_method=f"{method}/{style}",
                needs_review="0" if (vendor and iso and style == "dash") else "1",
                geometry=geom_text(page, lno, span[0], span[1])))

    notes += skipped
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=box_a, stated_end=box_close,
                stated_contrib_ytd=box_c, stated_expend_ytd=box_e,
                is_incremental=incremental or None, dedup_mode=regime or None,
                notes="; ".join(notes))
