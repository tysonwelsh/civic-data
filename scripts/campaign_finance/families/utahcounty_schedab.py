#!/usr/bin/env python3
"""utahcounty_schedab.py — Utah County's `FINANCIAL CAMPAIGN REPORT FOR COUNTY … CANDIDATES`
(Utah Code 17-16-6.5 / Utah County Code 2-5-2), BOTH printed variants.

EVIDENCE (utah_county/campaign_finance/CLAUDE.md, "The two form variants"):

  | variant | cycles | per-period cell | cumulative cell |
  |---|---|---|---|
  | **`legacy_colAB`** (135) | 2008–2018, some 2020/2026 | `Column A — Total this Period` | `Column B — Year-to-Date Total` |
  | **`modern_boxAF`** (130) | 2020+ (`v. 2.22` / `v. 4.20` / `v. 12.23`) | `Box B` / `Box D` | `Box C` / `Box E` |

  * "THE PROMOTION REGIME (read this before summing anything)" — "`stated_total_contributions` /
    `stated_total_expenditures` carry the **PER-PERIOD** figure … The **cumulative** figures are
    kept in `notes` as `ytd_contrib=` / `ytd_expend=` … and are **NEVER summed as increments**."
    So **Column A / Box B is the reconciliation anchor** and Column B / Box C is a cross-check.
  * "`legacy_colAB` prints lines 1–7 (1 contributions · 2 expenditures · 3 balance at beginning ·
    4 contributions · 5 subtotal · 6 expenditures · 7 balance at close). `modern_boxAF` prints
    A (balance at beginning) · B/C (contributions period/YTD) · D/E (expenditures period/YTD) ·
    F (subtotal before expenditures = A+B) · balance at close."
  * "a compound cell such as `94009.26 +Inkind 666.67` states two numbers and is not reduced to
    one" — the v.12.23 Box B/C cells print BOTH a cash and an in-kind figure. This parser does
    not reduce them either: it splits the cell on the form's OWN printed `+Inkind` marker, takes
    the CASH figure as the anchor (the itemized `Amount` column sums to it), and reports the
    in-kind figure separately. Nothing is added together.
  * "a **bare dash `-` is NOT a zero**" and the `-0-`/`Zero` whitelist — the shared ZERO-GLYPH
    RULING (GOTCHAS.md, owner 2026-08-02) via `common.parse_money_cell`. Utah County's OTHER two
    documented repairs (`(65.00)` -> −65.00 is handled; `2,250.-` -> 2250.00 is NOT) are
    deliberately not both here: a dash in the cents position is a malformed decimal and stays
    unparseable-blank, per the tranche rule that malformed decimals are never repaired.
  * "**Do not read `text/*.txt` as a transcript.** The sidecars are tesseract OCR of handwritten
    forms." — 245 of 263 filings are scans. THIS FAMILY IS FOR THE 18 MACHINE-READABLE FILINGS;
    everything else stays on the vision cache, and a filing whose cells will not parse cleanly
    yields blanks + reasons rather than digits.

SHAPES

  legacy_colAB                                      modern_boxAF (v. 12.23)
                        Column A      Column B           Balance at Beginning of Reporting Period
                     Total this      Year-to-Date        A 0
                       Period            Total           Contributions Received this Period | … Year to Date
  1 TOTAL CONTRIBUTIONS  $47,397.39                      B  168872.24 +Inkind 7670.68  | C  168872.24 +Inkind …
      RECEIVED                        $47,397.39         Expenditures Made this Period  | … Year to Date
  2 TOTAL EXPENDITURES   $42,192.78   $42,192.78         D  151411.54                   | E  …
  3 Balance at Beginning  $0                             F  (subtotal before expenditures)
  7 Balance at Close      $5,204.61
  SCHEDULE A  Date | Name of Contributor | Mailing Address & Zip | Amount
  SCHEDULE B  Date | Provider Vendor | Purpose | Amount
                                                    Contributor Name | Amount | INKIND   <- box form
                                                    Who Paid         | Total             <- box form

COLUMN A vs COLUMN B ARE READ POSITIONALLY. The two figures often land on DIFFERENT laid-out
lines (Ainge 2018 prints Column A on the label line and Column B on the next), so an ordinal
reader would take the Year-to-Date figure as the period total on exactly the filings where the
two differ — which is the whole point of the distinction. Each money token is assigned to the
`Column A` / `Column B` header whose x-position it is nearer, first token per column wins.

IN-KIND on the box form is also POSITIONAL: the ledger prints `Contributor Name | Amount |
INKIND`, and which column a lone figure sits in is the ONLY thing that marks it in-kind (Paxman
2026: Spencer Stokes 1,666.67 + Doug Ford 5,000 + All In For Utah PAC 1,004.01 = the printed
INKIND total 7,670.68, and every one of them is distinguishable from a cash row by x-position
alone). Rows are emitted with `in_kind=True`, so the county wires `reconcile_cash_only=True`.

PRIVACY: Schedule A prints `Mailing Address & Zip Code`; only `donor_city` / `donor_state` are
emitted (`common.split_city_state`) and the street portion is discarded.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_money_cell, money_cell_spans,
                    split_city_state, geom_text, page_line_index, parse_date, date_in_window)

# ------------------------------------------------------------------ legacy_colAB anchors
_HDR_A = re.compile(r"Column\s*A", re.I)
_HDR_B = re.compile(r"Column\s*B", re.I)
_L_CONTRIB = re.compile(r"TOTAL\s+CONTRIBUTIONS\s+RECEIVED", re.I)
_L_EXPEND = re.compile(r"TOTAL\s+EXPENDITURES\s+MADE", re.I)
_L_BEGIN = re.compile(r"Balance\s+at\s+Beginning\s+of\s+Reporting\s+Period", re.I)
_L_CLOSE = re.compile(r"Balance\s+at\s+Close\s+of\s+Reporting\s+Period", re.I)

# ------------------------------------------------------------------ modern_boxAF anchors
_BOX_BC = re.compile(r"Contributions\s+Received\s+this\s+Period", re.I)
_BOX_DE = re.compile(r"Expenditures\s+Made\s+this\s+Period", re.I)
_BOX_LETTER = re.compile(r"(?<![A-Za-z])([A-G])(?![A-Za-z])")
_INKIND_MARK = re.compile(r"\+\s*in\s*[- ]?\s*kind", re.I)

# ------------------------------------------------------------------------ schedules
# A schedule HEADING starts its own line — the phrase also appears inside the summary page's
# instruction "(Complete this page after filling out Schedule A and Schedule B)", which must
# never be read as a section start (it made both schedules resolve to the same line).
_SCHED_A = re.compile(r"^\s*(?:SCHEDULE\s*[\"“”']?A[\"“”']?\b"
                      r"|ITEMIZED\s+CONTRIBUTIONS\s+RECEIVED)", re.I)
_SCHED_B = re.compile(r"^\s*(?:SCHEDULE\s*[\"“”']?B[\"“”']?\b"
                      r"|ITEMIZED\s+EXPENDITURES\s+MADE)", re.I)
_SUMMARY = re.compile(r"SUMMARY\s+PAGE", re.I)
_TOTAL_LN = re.compile(r"^\s*(?:TOTAL|Subtotal)\b|Sum\s+of\s+subtotals|Total\s+Contributions\s+"
                       r"Received\s*\(|Total\s+Expenditures\s+Made\s*\(", re.I)
_COLHDR_C = re.compile(r"Contributor\s+Name|Name\s+of\s+Contributor", re.I)
_COLHDR_E = re.compile(r"Who\s+Paid|Provider\s+Vendor|Provider\s*/\s*Vendor", re.I)
_AMT_HDR = re.compile(r"\bAmount\b|\bTotal\b", re.I)
_INK_HDR = re.compile(r"\bIN\s*[- ]?\s*KIND\b", re.I)
_ADDR_HDR = re.compile(r"Mailing\s+Address|\bAddress\b", re.I)
_DATE_LEAD = re.compile(r"^\s*(\d{1,2}\s*[/\-]\s*\d{1,2}\s*[/\-]\s*\d{2,4})\b")


# A BARE INTEGER is a real amount in these ledgers — Paxman 2026 prints `Gary and Jeanette
# Herbert Foundation   500`, `Dean Judd   2000`, `Alta Bank   10`. The library deliberately does
# not treat a bare integer as money in general, so it is accepted HERE ONLY at or right of the
# ledger's own `Amount` column, which keeps a ZIP code or a street number in the address column
# from ever being read as a dollar figure.
_BARE_INT = re.compile(r"(?<![\d.,$])\d{1,7}(?![\d.,])")


def _num_tokens(ln, min_x):
    """[(start, end, value)] for money-shaped tokens plus bare integers at/after column `min_x`."""
    out = [(s, e, v) for s, e, v, _r in money_cell_spans(ln)]
    if min_x is not None:
        for m in _BARE_INT.finditer(ln):
            if m.start() < min_x:
                continue
            if any(s <= m.start() < e for s, e, _v in out):
                continue
            v, kind = parse_money_cell(m.group(0))
            if kind == "money":
                out.append((m.start(), m.end(), v))
    return sorted(out)


def _col_at(lines, i, span, rx):
    for j in range(i, min(i + span, len(lines))):
        m = rx.search(lines[j])
        if m:
            return j, m.start()
    return None, None


def _assign(tokens, cols):
    """tokens = [(start, end, value)]; cols = [(name, x)] -> {name: (value, start, end)}."""
    out = {}
    for s, e, v in tokens:
        centre = (s + e) // 2
        name = min(cols, key=lambda c: abs(c[1] - centre))[0]
        out.setdefault(name, (v, s, e))
    return out


def _split_compound(cell):
    """`168872.24 +Inkind 7670.68` -> (168872.24, 7670.68). The cell is split on the form's OWN
    printed `+Inkind` marker — the two figures are reported separately and NEVER added."""
    m = _INKIND_MARK.search(cell)
    if not m:
        v, kind = parse_money_cell(cell.strip())
        return (v if kind in ("money", "zero-glyph") else None), None
    left, right = cell[:m.start()], cell[m.end():]
    lv, lk = parse_money_cell(left.strip())
    rv, rk = parse_money_cell(right.strip())
    return (lv if lk in ("money", "zero-glyph") else None,
            rv if rk in ("money", "zero-glyph") else None)


# ------------------------------------------------------------------------- legacy mode

def _legacy(lines, notes):
    ja, xa = _col_at(lines, 0, len(lines), _HDR_A)
    jb, xb = _col_at(lines, 0, len(lines), _HDR_B)
    if xa is None or xb is None or xb <= xa:
        return None
    cols = [("A", xa), ("B", xb)]

    def _read(rx, start=0):
        for i in range(start, len(lines)):
            if not rx.search(lines[i]):
                continue
            toks = []
            for j in range(i, min(i + 3, len(lines))):
                for s, e, v, _raw in money_cell_spans(lines[j]):
                    if s >= xa - 12:
                        toks.append((s, e, v))
                if len(toks) >= 2:
                    break
            if toks:
                return _assign(toks, cols)
        return {}

    c = _read(_L_CONTRIB)
    e = _read(_L_EXPEND)
    beg = _read(_L_BEGIN)
    close = _read(_L_CLOSE)
    notes.append("variant=legacy_colAB; anchor = Column A (Total this Period); Column B "
                 "(Year-to-Date) is a CROSS-CHECK and is never summed as an increment")
    return dict(contrib=c.get("A", (None,))[0], contrib_ytd=c.get("B", (None,))[0],
                expend=e.get("A", (None,))[0], expend_ytd=e.get("B", (None,))[0],
                begin=beg.get("A", (None,))[0], close=close.get("A", (None,))[0],
                contrib_ik=None, expend_ik=None)


# --------------------------------------------------------------------------- box mode

def _boxes(lines, notes):
    def _pair(rx):
        for i, ln in enumerate(lines):
            if not rx.search(ln):
                continue
            for j in range(i + 1, min(i + 4, len(lines))):
                letters = [(m.group(1), m.start()) for m in _BOX_LETTER.finditer(lines[j])]
                if not letters:
                    continue
                out = {}
                for k, (name, x) in enumerate(letters):
                    nxt = letters[k + 1][1] if k + 1 < len(letters) else len(lines[j])
                    cash, ik = _split_compound(lines[j][x + 1:nxt])
                    if cash is None and ik is None:
                        for jj in range(j + 1, min(j + 3, len(lines))):
                            sp = money_cell_spans(lines[jj])
                            near = [t for t in sp if abs(t[0] - x) < 25]
                            if near:
                                cash = near[0][2]
                                break
                    out[name] = (cash, ik)
                return out
            return {}
        return {}

    bc, de = _pair(_BOX_BC), _pair(_BOX_DE)
    if not bc and not de:
        return None

    def _single(rx):
        for i, ln in enumerate(lines):
            if not rx.search(ln):
                continue
            for j in range(i, min(i + 4, len(lines))):
                m = _BOX_LETTER.search(lines[j])
                if m:
                    v, _ik = _split_compound(lines[j][m.end():])
                    if v is not None:
                        return v
                sp = money_cell_spans(lines[j])
                if sp:
                    return sp[0][2]
        return None

    notes.append("variant=modern_boxAF; anchor = Box B / Box D (this period); Box C / Box E "
                 "(Year to Date) are a CROSS-CHECK and are never summed as increments")
    b_cash, b_ik = bc.get("B", (None, None))
    c_cash, c_ik = bc.get("C", (None, None))
    d_cash, d_ik = de.get("D", (None, None))
    e_cash, e_ik = de.get("E", (None, None))
    if b_ik is not None:
        notes.append(f"Box B is a COMPOUND cell — cash {b_cash:,.2f} and in-kind {b_ik:,.2f} "
                     f"split on the form's own '+Inkind' marker; the two are never added")
    return dict(contrib=b_cash, contrib_ytd=c_cash, expend=d_cash, expend_ytd=e_cash,
                begin=_single(_L_BEGIN), close=_single(_L_CLOSE),
                contrib_ik=b_ik, expend_ik=d_ik)


# ------------------------------------------------------------------------ schedule rows

def _sections(lines):
    """([contribution ranges], [expenditure ranges]) as (start, stop) index pairs.

    Schedules REPEAT: Ainge 2018 prints `SCHEDULE A` three times and `SCHEDULE B` six times (one
    per continuation page), so a single contiguous block loses every page but the first. Each
    heading opens a range and the NEXT heading (of any kind, incl. the Summary Page) closes it."""
    marks = []
    for k, ln in enumerate(lines):
        if _SCHED_A.search(ln):
            marks.append((k, "a"))
        elif _SCHED_B.search(ln):
            marks.append((k, "b"))
        elif _SUMMARY.search(ln):
            marks.append((k, "end"))
    if not any(t in ("a", "b") for _k, t in marks):
        # the box form prints no SCHEDULE heading — its ledgers are identified by their own
        # column headers (`Who Paid | Total`, `Contributor Name | Amount | INKIND`)
        marks = []
        for k, ln in enumerate(lines):
            if _COLHDR_C.search(ln):
                marks.append((k, "a"))
            elif _COLHDR_E.search(ln):
                marks.append((k, "b"))
            elif _SUMMARY.search(ln):
                marks.append((k, "end"))
    n = len(lines)
    a_r, b_r = [], []
    for i, (k, kind) in enumerate(marks):
        if kind == "end":
            continue
        stop = marks[i + 1][0] if i + 1 < len(marks) else n
        (a_r if kind == "a" else b_r).append((k, stop))
    return a_r, b_r


_TOTAL_ROW = re.compile(r"^\s*TOTAL\b", re.I)


def _page_geometry(lines, start, stop, pl):
    """{page -> (amount_centre, inkind_centre)} for a ledger range.

    The box ledger's Amount / IN-KIND columns SHIFT between pages (Paxman 2026 right-aligns
    page 3 near column 55 and page 4 near column 43), so one global threshold misclassifies a
    whole page. Geometry is therefore taken PER PAGE from that page's own printed `TOTAL` row —
    which prints one figure per column — or, failing that, from a column header on that page.
    A page with neither has NO in-kind column of its own and its rows are cash."""
    geo = {}
    for k in range(start, stop):
        if k >= len(pl):
            break
        page = pl[k][0]
        if page in geo:
            continue
        ln = lines[k]
        if _TOTAL_ROW.match(ln):
            toks = [(s, e, v) for s, e, v, _r in money_cell_spans(ln)]
            if len(toks) >= 2:
                geo[page] = ((toks[-2][0] + toks[-2][1]) // 2, (toks[-1][0] + toks[-1][1]) // 2)
                continue
        ma, mi = _AMT_HDR.search(ln), _INK_HDR.search(ln)
        if ma and mi and mi.start() > ma.start():
            geo[page] = (ma.start(), mi.start())
    return geo


def _rows(lines, ranges, meta, is_contrib, pl, notes):
    out = []
    for start, stop in (ranges or []):
        out += _rows_one(lines, start, stop, meta, is_contrib, pl, notes)
    return out


def _printed_col_totals(lines, ranges):
    """(amount_total, inkind_total) from the ledger's own `TOTAL` row(s), or (None, None)."""
    a = i = None
    for start, stop in (ranges or []):
        for k in range(start, stop):
            if not _TOTAL_ROW.match(lines[k]):
                continue
            toks = [v for _s, _e, v, _r in money_cell_spans(lines[k])]
            if len(toks) >= 2:
                a, i = toks[-2], toks[-1]
            elif len(toks) == 1 and a is None:
                a = toks[0]
    return a, i


def _rows_one(lines, start, stop, meta, is_contrib, pl, notes):
    if start is None:
        return []
    amt_x = ink_x = None
    has_addr = False
    for j in range(start, min(start + 5, stop)):
        if amt_x is None:
            m = _AMT_HDR.search(lines[j])
            if m:
                amt_x = m.start()
        if ink_x is None:
            m = _INK_HDR.search(lines[j])
            if m:
                ink_x = m.start()
        if _ADDR_HDR.search(lines[j]):
            has_addr = True
    geo = _page_geometry(lines, start, stop, pl) if ink_x is not None else {}
    out = []
    method = meta.get("extract_method", "utahcounty_schedab/text")
    for k in range(start + 1, stop):
        ln = lines[k]
        if not ln.strip() or _TOTAL_LN.search(ln) or _AMT_HDR.search(ln) or _INK_HDR.search(ln):
            continue
        min_x = None
        if amt_x is not None:
            min_x = amt_x - 12 if ink_x is None else min(amt_x, ink_x) - 12
        sp = _num_tokens(ln, min_x)
        if not sp:
            continue
        dm = _DATE_LEAD.match(ln)
        # IN-KIND is decided ONLY by x-position, against THIS PAGE's own column geometry — the
        # box ledger's lone figure carries no marker at all, and which column it sits in is the
        # only thing that distinguishes an in-kind contribution from a cash one.
        inkind = False
        s, e, v = sp[-1]
        page = pl[k][0] if k < len(pl) else 1
        if len(sp) > 1 and ink_x is not None:
            s, e, v = sp[0]                       # two figures printed -> Amount is the left one
        elif page in geo:
            ax, ix = geo[page]
            centre = (s + e) // 2
            inkind = abs(centre - ix) < abs(centre - ax)
        body = ln[dm.end():s] if dm else ln[:s]
        if len(re.findall(r"[A-Za-z]", body)) < 2:
            continue
        fields = [t for t in re.split(r"\s{2,}", body.strip()) if t.strip()]
        name = fields[0].strip() if fields else ""
        extra = " ".join(f.strip() for f in fields[1:]).strip()
        iso = parse_date(re.sub(r"\s+", "", dm.group(1))) if dm else ""
        if iso and not date_in_window(iso, meta):
            iso = ""
        lno = pl[k][1] if k < len(pl) else k + 1
        geo_s = geom_text(page, lno, s, e)
        if is_contrib:
            if has_addr:
                # Schedule A prints `Mailing Address & Zip Code`: city/state ONLY, street dropped.
                city, state = split_city_state(extra)
            else:
                # The BOX ledger has NO address column and splits the contributor's name across
                # two whitespace columns (`Spencer   Stokes`), so the trailing field belongs to
                # the NAME and there is no geography to read. Joined only when it carries no
                # digits — a street line always does, and a street is never written into
                # `donor_raw` (PRIVACY.md).
                city = state = ""
                if extra and not any(ch.isdigit() for ch in extra):
                    name = (name + " " + extra).strip()
                    extra = ""
            out.append(ContribRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso or "", donor_raw=name, donor_city=city, donor_state=state,
                amount=common.money_str(v), in_kind="True" if inkind else "False",
                is_incremental="True", source_filing=meta["source_filing"],
                document_id=meta.get("document_id", ""), line_no=str(k + 1),
                extract_method=method, needs_review="0" if name else "1", geometry=geo_s))
        else:
            out.append(ExpendRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso or "", vendor_raw=name, purpose=extra,
                amount=common.money_str(v), in_kind="True" if inkind else "False",
                is_incremental="True", source_filing=meta["source_filing"],
                document_id=meta.get("document_id", ""), line_no=str(k + 1),
                extract_method=method, needs_review="0" if name else "1", geometry=geo_s))
    return out


_GEO_RE = re.compile(r"p(\d+):l\d+:c(\d+)-(\d+)")


def _calibrate_inkind(rows, printed_ink):
    """Prove the in-kind column from the ledger's OWN printed IN-KIND total.

    The box ledger right-aligns its figures and the alignment SHIFTS between pages, so no single
    x-threshold classifies the whole section (Paxman 2026: page 3's cash rows end at columns
    49-55, page 4's cash rows at 38-40 and its three in-kind rows at 47-49). Instead, each page's
    candidate thresholds are enumerated from its own token positions and a combination is sought
    that reproduces the PRINTED in-kind total exactly. The answer is adopted only when it is
    EXACT and UNIQUE; otherwise the split is refused (the caller reports every row as cash and
    flags it). Nothing is inferred that the source's own arithmetic does not confirm.

    Returns the set of `id(row)` to mark in-kind, or None."""
    per_page = {}
    for r in rows:
        m = _GEO_RE.match(r.geometry or "")
        if not m or not r.amount:
            return None
        per_page.setdefault(int(m.group(1)), []).append((int(m.group(3)), r))
    if not per_page:
        return None
    options = {}
    for pg, items in per_page.items():
        ends = sorted({e for e, _r in items})
        seen, opts = set(), []
        for t in ends + [max(ends) + 1]:
            sel = frozenset(id(r) for e, r in items if e >= t)
            if sel in seen:
                continue
            seen.add(sel)
            opts.append((round(sum(float(r.amount) for e, r in items if id(r) in sel), 2), sel))
        options[pg] = opts
    states = {0.0: [frozenset()]}
    for pg in sorted(options):
        nxt = {}
        for tot, sels in states.items():
            for amt, sel in options[pg]:
                key = round(tot + amt, 2)
                if key > printed_ink + 0.01:
                    continue
                nxt.setdefault(key, [])
                for prev in sels:
                    if len(nxt[key]) < 3:
                        nxt[key].append(prev | sel)
        states = nxt
    hits = [s for t, sels in states.items() if abs(t - printed_ink) <= 0.01 for s in sels]
    uniq = {frozenset(h) for h in hits}
    return set(next(iter(uniq))) if len(uniq) == 1 else None


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    pl = page_line_index(text)
    notes = []

    tot = _boxes(lines, notes)
    if tot is None:
        tot = _legacy(lines, notes)
    if tot is None:
        return dict(contrib_rows=[], expend_rows=[], stated_contrib=None, stated_expend=None,
                    stated_begin=None, stated_end=None,
                    notes="neither a Column A/B summary page nor a Box A-F ladder is legible — "
                          "nothing read (this is the OCR floor; use the filing's vision cache)")

    a_r, b_r = _sections(lines)
    crows = _rows(lines, a_r, meta, True, pl, notes)
    erows = _rows(lines, b_r, meta, False, pl, notes)

    # VERIFY the positional in-kind split against the ledger's OWN printed column totals. If it
    # does not reproduce them to the cent, the split is not proven and every row is reported as
    # cash with a loud note, rather than published as a classification the source does not carry.
    pa, pi = _printed_col_totals(lines, a_r)
    if pi is not None:
        got = round(sum(float(r.amount) for r in crows if r.amount and r.in_kind == "True"), 2)
        cash = round(sum(float(r.amount) for r in crows if r.amount and r.in_kind != "True"), 2)
        if abs(got - pi) > 0.01:
            solved = _calibrate_inkind(crows, pi)
            if solved is not None:
                for r in crows:
                    r.in_kind = "True" if id(r) in solved else "False"
                got = round(sum(float(r.amount) for r in crows
                                if r.amount and r.in_kind == "True"), 2)
                cash = round(sum(float(r.amount) for r in crows
                                 if r.amount and r.in_kind != "True"), 2)
                notes.append("in-kind column CALIBRATED per page against the ledger's own "
                             "printed IN-KIND total (exact + unique solution)")
        if abs(got - pi) <= 0.01 and (pa is None or abs(cash - pa) <= 0.01):
            notes.append(f"in-kind split VERIFIED against the ledger's printed column totals "
                         f"(cash {cash:,.2f} / in-kind {got:,.2f})")
        else:
            for r in crows:
                r.in_kind = "False"
                r.needs_review = "1"
            notes.append(f"in-kind split NOT proven (positional read gives {got:,.2f} against a "
                         f"printed IN-KIND total of {pi:,.2f}) -- every row reported as cash and "
                         f"flagged; the in-kind column is not asserted")

    for key, label in (("contrib_ytd", "contributions Year-to-Date"),
                       ("expend_ytd", "expenditures Year-to-Date")):
        if tot.get(key) is not None:
            notes.append(f"{label} stated ${tot[key]:,.2f} — NEVER summed as an increment")
    if tot.get("contrib_ik") is not None:
        notes.append(f"in-kind contributions stated ${tot['contrib_ik']:,.2f} (separate figure)")

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=tot["contrib"], stated_expend=tot["expend"],
                stated_begin=tot["begin"], stated_end=tot["close"],
                stated_contrib_ytd=tot.get("contrib_ytd"),
                stated_expend_ytd=tot.get("expend_ytd"),
                is_incremental="True", dedup_mode="incremental",
                notes="; ".join(notes))
