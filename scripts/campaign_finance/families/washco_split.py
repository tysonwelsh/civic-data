#!/usr/bin/env python3
"""washco_split.py — Washington County's BORN-DIGITAL generations: the 3-file split filing
(`County Candidate Summary` + `All Contributions for` + `All Expenditures for`), the 2014-15
`.xls` workbooks, and the 2008 `Detailed … Report` ledger pairs.

EVIDENCE (washington_county/campaign_finance/):
  * `CLAUDE.md` "The one form family, and why every era looks different":
      | **2010–2013** | **born-digital PDF**, split 3 ways per filing (`Summary` / `Contributions`
        / `Expenditures`) | **Yes** — real text layer, itemised ledgers with recipient, date,
        amount, in-kind flag, description |
      | **2014–2015** | **`.xls` workbooks**, same 3-way split | **Yes, best of all** — actual
        spreadsheet cells |
  * `CLAUDE.md` "**409 FILES, 206 FILINGS.** The county splits one logical filing across up to
    three published files, so file counts and filing counts are different quantities" — which is
    why this family needs the driver's `group_fn` hook: **the reconciliation anchor (the Summary)
    is in a DIFFERENT FILE from the itemised rows it must reconcile against.**
  * `CLAUDE.md` "But the data DOES reconcile — hand-verified 2026-08-01":
      - **Victor Iverson, Commission Seat B, 2014** — "Summary states `$630.00` contributions for
        the 4/4 deadline; ledger itemises Derek Brown `$130` + Spencer Stokes `$500`" → **$630 ✓**
      - **David Whitehead, Treasurer, 2010** — "Summary states `$400.00` expenditures at
        4/7/2010; ledger itemises Washington County filing fee `$375` + Washington County
        Republican Party convention table `$25`" → **$400 ✓**
    Both are unit-tested here against the county's own retained text sidecars.
  * `CLAUDE.md` "Filing-style finding": "in the 2014–15 generation the **Summary rows are
    PER-PERIOD increments** while the **Contributions/Expenditures ledgers restate the whole
    cycle to date** … A cycle total is therefore the **ledger**, not the sum of summary rows —
    the opposite of the naive reading. Encode as `is_incremental` per *sheet type*, not per city."
    Hence `dedup_mode`/`is_incremental` are declared PER FILING (the driver's 2026-08-02 hook):
    a `summary_sheet` filing is INCREMENTAL, a `cover_form` filing is CUMULATIVE.
  * `CLAUDE.md` Do-nots: "**Never treat a blank `stated_*` as `0`.**" and "Don't 'fix'
    `All Expeditures for` — that is the county's own spelling in its workbooks."

WHY THE LEDGERS ARE READ BY X-POSITION, NOT BY LAST-MONEY-TOKEN. The 2010-13 contribution ledger
prints `Name | Received | Amount | In Kind | Loan` and the 2008 report prints `Date: | Name of
Contributor: | Amount:` — in BOTH, more than one column can hold money, so a
last-money-token reader mis-columns. Every row is therefore split into COLUMN TERRITORIES taken
from that table's own printed header line, and each money token is required to fall wholly inside
exactly one territory.

THE COMPLETENESS GATE (the washington agent's rule). A ledger row is emitted ONLY when it is
provably complete: EVERY money token on the row (after wrapped continuation lines are joined)
lands wholly inside a single column, no column receives two tokens, and the Amount column
receives exactly one. Anything else emits NOTHING plus a reason. The rule earns its keep on Lin
Alder's 2008 report, whose wrapped aggregate row prints
`Various   Miscellaneous Donors $50.00   $700.00` / `Or less (18 donors)` — two money tokens in
one territory, so the row is refused rather than published with a guessed amount.

THE `.xls` READER reads REAL CELLS from the county's retained `text/` sidecars, which
`build_text.py` writes as `### SHEET: <name>  (RxC)` followed by TAB-separated cell rows.
Excel DATE SERIALS (`41733`) are converted with the 1899-12-30 epoch; a serial outside a sane
range stays blank. Geometry for a spreadsheet row is the real cell reference (`Sheet1!F5`).

MONEY: `common.parse_money_cell` throughout, so the ZERO-GLYPH RULING (GOTCHAS.md, owner
2026-08-02) applies — `Ø` / `-0-` / "zero" -> 0, a bare dash / `N/A` / an empty cell -> BLANK —
and nothing is repaired.

PRIVACY: the ledgers print a donor's street address on the line BELOW the name (xls) or in the
description column; only `donor_city` / `donor_state` are emitted, via
`common.split_city_state`. The street portion is discarded and never stored.
"""
from __future__ import annotations

import datetime
import re

import common
from common import (ContribRow, ExpendRow, parse_money_cell, money_cell_spans,
                    split_city_state, geom_text, geom_cell, page_line_index, parse_date)

_SHEET = re.compile(r"^###\s+SHEET:\s+(.*?)\s+\(\d+x\d+\)\s*$")
_H_SUMMARY = re.compile(r"County\s+Candidate\s+Summary", re.I)
# "All Expeditures for" is the county's own spelling in its workbooks — matched, never "fixed".
_H_CONTRIB = re.compile(r"All\s+Contributions?\s+for|Detailed\s+Contributions?\s+Report", re.I)
_H_EXPEND = re.compile(r"All\s+Expe(?:n)?ditures?\s+for|Detailed\s+Expe(?:n)?ditures?\s+Report",
                       re.I)

_SUM_HDRS = ("submitted", "date due", "contributions", "expenditures", "balance")
# These ledgers print a two-line column head — `Name` over `Address` — and the second line is
# NOT a donor. Held over as a pending name it prefixed the first donor of every 2012-generation
# ledger (`Address Darlo Esplin`), which is a wrong value in the published `donor_raw`.
_SUBHEADER = re.compile(r"address|name|recipient", re.I)
_LEDGER_HDR_C = re.compile(r"\bName\b.*\bAmount\b|\bDate:?\b.*\bName\s+of\s+Contributor", re.I)
_LEDGER_HDR_E = re.compile(r"\bRecipient\b.*\bAmount\b|\bDate:?\b.*\bName\b.*\bAmount", re.I)
_EXCEL_EPOCH = datetime.date(1899, 12, 30)


def _xl_date(tok):
    """Excel serial -> ISO, or "" when the token is not a sane serial (never a guess)."""
    t = (tok or "").strip()
    if not re.fullmatch(r"\d{4,5}(?:\.\d+)?", t):
        return ""
    n = int(float(t))
    if not 20000 <= n <= 60000:              # 1954-10-… .. 2064-…; outside that it is not a date
        return ""
    return (_EXCEL_EPOCH + datetime.timedelta(days=n)).isoformat()


_DATE_TOK = re.compile(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}"
                       r"|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}"
                       r"|\b\d{4,5}\b")


def _date_in_col(ln, lo, hi):
    """The date token whose START lies in [lo, hi) — read WHOLE, never sliced. A column slice
    truncates `3/15/2010` to `3/15/20`, which `parse_date` then reads as 2020."""
    for m in _DATE_TOK.finditer(ln):
        if lo <= m.start() < hi:
            return m.group(0)
    return ln[lo:hi].strip()


def _date_any(tok):
    return parse_date((tok or "").strip()) or _xl_date(tok) or ""


# ------------------------------------------------------------------- part classification

def is_xls(text):
    return text.lstrip().startswith("### SHEET:")


def classify(part):
    """`summary` | `contributions` | `expenditures` | `mixed` | `unknown`, from the DOCUMENT — the
    county's filenames lie (`…Contributions - Greg Aldred.pdf` contains a Summary), so a
    `doc_kind` from `index.csv` is used only as a tiebreaker."""
    t = part.get("text", "")
    has_s, has_c, has_e = (bool(_H_SUMMARY.search(t)), bool(_H_CONTRIB.search(t)),
                           bool(_H_EXPEND.search(t)))
    if has_s and (has_c or has_e):
        return "mixed"
    if has_s:
        return "summary"
    if has_c and has_e:
        return "mixed"
    if has_c:
        return "contributions"
    if has_e:
        return "expenditures"
    return (part.get("ix") or {}).get("doc_kind", "") or "unknown"


# ------------------------------------------------------------------------ column model

def _territories(starts):
    """Header start columns -> [(lo, hi)] column territories.

    The boundary sits just BEFORE the next header's start, not at the midpoint between headers:
    these tables right-align their figures, so a value routinely begins well right of its own
    header and ends one or two characters short of the next one (`Amount` at column 40 holding
    `$375.00` at 43-50 with `In Kind` at 54). A midpoint boundary cuts exactly such a token in
    half and the completeness gate then refuses a perfectly legible row."""
    edges = [0]
    for b in starts[1:]:
        edges.append(max(edges[-1] + 1, b - 2))
    edges.append(10 ** 6)
    return list(zip(edges, edges[1:]))


_ADDR_HINT = re.compile(r"\b(?:P\.?O\.?\s*Box|St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|"
                        r"Ct|Cir|Circle|Way|Blvd|Hwy|Pkwy)\b", re.I)


def _looks_address(t):
    return bool(_ADDR_HINT.search(t)) or bool(re.search(r",\s*[A-Z]{2}\b", t))


def _assign_strict(ln, terr):
    """{column_index: (value, start, end)} plus an `ok` flag. A token must lie WHOLLY inside one
    territory and no territory may take two — that is the completeness test."""
    out, ok = {}, True
    for s, e, v, _raw in money_cell_spans(ln):
        hit = [i for i, (lo, hi) in enumerate(terr) if lo <= s and e <= hi]
        if len(hit) != 1:
            ok = False
            continue
        i = hit[0]
        if i in out:
            ok = False
            continue
        out[i] = (v, s, e)
    return out, ok


# --------------------------------------------------------------------- layout-PDF tables

def _pdf_header(lines, rx, labels):
    """(index, [(label, x)]) of the ledger's own header line."""
    for i, ln in enumerate(lines):
        if not rx.search(ln):
            continue
        hits = {}
        for lab in labels:
            m = re.search(r"\b" + lab.replace(" ", r"\s+") + r"\b", ln, re.I)
            if not m:
                continue
            # Two labels can match at the SAME x (`Name of Contributor:` matches both `Name` and
            # `Name of Contributor`), which would create an empty zero-width territory and lose
            # the column entirely. Keep the LONGEST label at each start.
            prev = hits.get(m.start())
            if prev is None or len(lab) > len(prev):
                hits[m.start()] = lab
        cols = sorted(((lab, x) for x, lab in hits.items()), key=lambda c: c[1])
        if len(cols) >= 2:
            return i, cols
    return None, []


def _pdf_rows(lines, hdr_i, cols, stop, meta, pl, kind, skipped, cov=None):
    """Ledger rows from a laid-out PDF table, with wrapped continuation lines joined into the
    NAME column and the strict completeness gate applied.

    `cov` (optional) accumulates the SIDE COVERAGE counters the module-local builder needs to
    tell FILER ARITHMETIC apart from PARSE LOSS: `logical` = money-bearing logical rows found in
    the table body, `emitted` = rows actually published. A side is provably complete only when
    the two agree; anything short is WITHHELD, never published as a short sum."""
    terr = _territories([c[1] for c in cols])
    names = [c[0].lower() for c in cols]
    idx = {n: i for i, n in enumerate(names)}
    rows = []
    pend = None            # [line_index, primary_line, wrapped_tail] awaiting its continuation
    for k in range(hdr_i + 1, stop):
        ln = lines[k]
        if not ln.strip():
            continue
        if not money_cell_spans(ln) and pend is not None:
            # A continuation line is either the tail of a wrapped NAME (`Washington County
            # Republican` / `Party`) or the donor's STREET ADDRESS printed under their name
            # (`3020 Sweetgum Cir, St George UT 84790`). They are told apart by digits: a street
            # line always carries a number, a wrapped name does not. The address is kept ONLY as
            # city/state — the street is discarded and never reaches `donor_raw` (PRIVACY.md).
            tail = ln.strip()
            if any(ch.isdigit() for ch in tail) or _looks_address(tail):
                pend[3] = (pend[3] + " " + tail).strip()
            else:
                pend[2] = (pend[2] + " " + tail).strip()
            continue
        if pend is not None:
            rows.append(pend)
            pend = None
        pend = [k, ln, "", ""]
    if pend is not None:
        rows.append(pend)

    out = []
    method = meta.get("extract_method", "washco_split/text")
    for k, ln, tail, addr in rows:
        cells, ok = _assign_strict(ln, terr)
        ai = idx.get("amount")
        if money_cell_spans(ln) and cov is not None:
            cov["logical"] = cov.get("logical", 0) + 1
        if ai is None or ai not in cells:
            # SILENT NO MORE (2026-08-23). A money-bearing row whose token misses the Amount
            # territory entirely is the LOAN / mis-columned case, and dropping it without a
            # word made a short ledger look like a complete one. Recorded so the side's
            # completeness gate can see it.
            if money_cell_spans(ln):
                skipped.append(f"line {k + 1}: {kind} row NOT emitted — the row's money "
                               f"token(s) fall outside the Amount column (a Loan/In-Kind-only "
                               f"or mis-columned line); nothing published")
            continue
        if not ok or len(cells) > 3:
            skipped.append(f"line {k + 1}: {kind} row NOT emitted — money tokens do not resolve "
                           f"to one column each (wrapped/aggregate row); nothing published")
            continue
        amount = cells[ai][0]
        lo, hi = terr[idx.get("name", 0)]
        name = re.sub(r"\s{2,}", " ", (ln[lo:hi] + " " + tail)).strip()
        if not name:
            skipped.append(f"line {k + 1}: {kind} row NOT emitted — no name printed in the "
                           f"name column")
            continue
        dtok = ""
        for key in ("received", "date", "date:"):
            if key in idx:
                dlo, dhi = terr[idx[key]]
                dtok = _date_in_col(ln, dlo, dhi)
                break
        rest = ""
        for key in ("description", "purpose", "loan"):
            if key in idx:
                rlo, rhi = terr[idx[key]]
                rest = (rest + " " + ln[rlo:rhi]).strip()
        in_kind = False
        if "in kind" in idx and idx["in kind"] in cells:
            in_kind = True
        page, lno = pl[k] if k < len(pl) else (1, k + 1)
        geo = geom_text(page, lno, cells[ai][1], cells[ai][2])
        iso = _date_any(dtok)
        if cov is not None:
            cov["emitted"] = cov.get("emitted", 0) + 1
        if kind == "contributions":
            # geography comes from the donor's own ADDRESS line, never from a status column
            city, state = split_city_state(addr) if addr else ("", "")
            out.append(ContribRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, donor_raw=name, donor_city=city, donor_state=state,
                amount=common.money_str(amount), in_kind="True" if in_kind else "False",
                is_incremental="", source_filing=meta["source_filing"],
                document_id=meta.get("document_id", ""), line_no=str(k + 1),
                extract_method=method, needs_review="0" if iso else "1", geometry=geo))
        else:
            out.append(ExpendRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, vendor_raw=name, purpose=re.sub(r"\s{2,}", " ", rest).strip(),
                amount=common.money_str(amount), in_kind="True" if in_kind else "False",
                is_incremental="", source_filing=meta["source_filing"],
                document_id=meta.get("document_id", ""), line_no=str(k + 1),
                extract_method=method, needs_review="0" if iso else "1", geometry=geo))
    return out


# -------------------------------------------------------- TRUE-COORDINATE ledger reader
# (2026-08-23) The `-layout` reader above pins its column territories to the CHARACTER-CELL
# geometry of the page the header is printed on, and that reconstruction is not stable across
# pages: `Expenditures - Rob Tersigni.pdf` puts the Amount column at character columns 40-47 on
# page 1 and 19-26 on page 2, so 54 of its 77 rows were dropped by the completeness gate. In
# the PDF's OWN coordinates there is no drift — that file's amounts right-align to x=305.0 on
# every page. So when the caller supplies `part['bbox']` (word boxes from
# `pdftotext -bbox-layout`, produced by the county module's `bbox_lib.py`) this reader is used
# instead: one header-derived column model, valid on every page, and `pct:` geometry measured
# from the document rather than inferred.

_MONEY_WORD = re.compile(r"^\(?-?\$?-?[\d,]+(?:\.\d{1,2})?\)?$")
# UNAMBIGUOUS data tokens, used only to locate the first data column's left edge. Deliberately
# narrower than `_MONEY_WORD`/`_DATE_TOK`: a bare 4-5 digit run is a house number or a ZIP in
# these ledgers' address lines (`2059 W Sunstar Cir … UT 84790`) as often as it is a figure, and
# letting one of those set the boundary would push the address INTO the date column.
_EDGE_TOK = re.compile(r"^\(?-?\$[\d,]+(?:\.\d{1,2})?\)?$"
                       # a slashed/dashed run of 3-4 numeric groups: a date, INCLUDING the
                       # filer's own malformed ones (`03/09/20/12`, Slade Hughes 2012). Those
                       # must still mark the date column's left edge, or the token drifts into
                       # the name and ships as part of the vendor's name.
                       r"|^\d{1,2}(?:[/-]\d{1,4}){2,3}$"
                       r"|^[\d,]+\.\d{2}$")


def _col_model(spans):
    """[(label, x0, x1)] sorted by x -> (labels, boundaries). A token belongs to the column
    whose interval contains its CENTRE; boundaries sit midway between adjacent header spans.
    These tables print headers LEFT-aligned and figures RIGHT-aligned, so a value routinely
    starts right of its own header and ends short of the next one — a midpoint boundary is the
    only rule that gets both ends right."""
    spans = sorted(spans, key=lambda s: s[1])
    bounds = []
    for a, b in zip(spans, spans[1:]):
        bounds.append((a[2] + b[1]) / 2.0)
    return [s[0] for s in spans], bounds


def _col_of(x_centre, bounds):
    i = 0
    while i < len(bounds) and x_centre > bounds[i]:
        i += 1
    return i


def _find_header(pages, labels):
    """(page_index, line_index, [(label, x0, x1)]) of the ledger's own printed header."""
    want = [l.lower() for l in labels]
    for pi, page in enumerate(pages):
        for li, ln in enumerate(page["lines"]):
            toks = [(w[2].lower().strip(":"), w[0], w[1]) for w in ln["words"]]
            found = {}
            for j, (t, x0, x1) in enumerate(toks):
                for lab in want:
                    lw = lab.split()
                    if [t] == lw[:1] and len(lw) == 1:
                        found.setdefault(lab, (x0, x1))
                    elif len(lw) > 1 and [z[0] for z in toks[j:j + len(lw)]] == lw:
                        found.setdefault(lab, (x0, toks[j + len(lw) - 1][2]))
            if "amount" in found and len(found) >= 2:
                return pi, li, [(k, v[0], v[1]) for k, v in found.items()]
    return None, None, []


def _pct(page, x0, y0, x1, y1):
    w, h = page["width"] or 612.0, page["height"] or 792.0
    return "pct:%.2f,%.2f,%.2f,%.2f" % (100.0 * x0 / w, 100.0 * y0 / h,
                                        100.0 * (x1 - x0) / w, 100.0 * (y1 - y0) / h)


def _flat_lines(pages):
    return [(pi, li, " ".join(w[2] for w in ln["words"]))
            for pi, page in enumerate(pages) for li, ln in enumerate(page["lines"])]


def _bbox_window(pages, rx):
    """(start, end) flat-line indices of the ONE section `rx` names, or None.

    Deliberately refuses a document that prints the section header more than once — the
    `live_wp` annual re-posts staple four successive reports into one PDF, and picking "the
    first" of those would publish an early report's ledger under a later deadline. Those files
    keep the `-layout` reader's existing behaviour, unchanged.
    """
    flat = _flat_lines(pages)
    hits = [i for i, (_p, _l, t) in enumerate(flat) if rx.search(t)]
    if len(hits) != 1:
        return None
    start = hits[0]
    end = len(flat)
    for other in (_H_CONTRIB, _H_EXPEND, _H_SUMMARY):
        if other is rx:
            continue
        for i, (_p, _l, t) in enumerate(flat):
            if i > start and other.search(t):
                end = min(end, i)
                break
    return start, end


def _bbox_rows(pages, meta, kind, skipped, cov, labels, window=None):
    """Ledger rows read from TRUE page coordinates, with `pct:` geometry."""
    flat = _flat_lines(pages)
    lo, hi = window if window else (0, len(flat))
    keep = {(p, l) for i, (p, l, _t) in enumerate(flat) if lo <= i < hi}
    pages = [{"width": pg["width"], "height": pg["height"],
              "lines": [ln if (pi, li) in keep else {"y0": ln["y0"], "y1": ln["y1"], "words": []}
                        for li, ln in enumerate(pg["lines"])]}
             for pi, pg in enumerate(pages)]
    hp, hl, spans = _find_header(pages, labels)
    if hp is None:
        return []
    names, bounds = _col_model(spans)
    ix = {n: i for i, n in enumerate(names)}
    ai = ix.get("amount")
    name_i = ix.get("name", ix.get("recipient", 0))
    date_i = ix.get("received", ix.get("date"))
    loan_i = ix.get("loan")
    ink_i = ix.get("in kind")
    desc_i = ix.get("description")
    method = meta.get("extract_method", "washco_split/text")
    out = []
    pending_name = ""            # a text-only line held until the next money line decides it
    last = None                  # the last emitted row (for a trailing address / wrapped tail)

    def cols_of(line, bnds):
        buckets = {}
        for x0, x1, t in line["words"]:
            buckets.setdefault(_col_of((x0 + x1) / 2.0, bnds), []).append((x0, x1, t))
        return buckets

    # ⚠ THE NAME COLUMN'S RIGHT EDGE IS SET BY THE DATA, NOT BY THE HEADER MIDPOINT.
    # `Recipient` is a short header (x 56-98) over long values (`Southern Utah Office Supply`
    # runs to x=183), while the next header `Received` starts at x=208 — so the midpoint at
    # x=153 cut the vendor's own name in half and pushed `Supply` into the date column.
    # Money and date tokens ARE unambiguous, so the first data column's true left edge is the
    # leftmost of those; everything left of it is name. Measured from this document's own
    # tokens, never assumed.
    if bounds:
        per_col = {}
        for page in pages:
            for line in page["lines"]:
                for i, ws in cols_of(line, bounds).items():
                    if i < 1:
                        continue
                    for x0, _x1, t in ws:
                        if _EDGE_TOK.match(t):
                            per_col.setdefault(i, []).append(x0)
        # ⚠ MEDIAN PER COLUMN, NOT THE MINIMUM. One outlier is enough to ruin a minimum, and
        # this corpus has one: the county's own sub-$50 AGGREGATE line prints its figure INSIDE
        # the donor name (`Aggregate total under $50.00 contribution`), so a `$50.00` token
        # lands at x=181.8 in a table whose dates all start at x=265.1. Taking the minimum
        # moved the name column's right edge left of the addresses and truncated them
        # (`292 E Joshua, Washington,` lost its `UT 84780`). These tables align a column's
        # values to the same x on every row, so the median IS the column's true left edge.
        if per_col:
            meds = []
            for xs in per_col.values():
                xs.sort()
                meds.append(xs[len(xs) // 2])
            b0 = min(meds) - 1.0
            if len(bounds) >= 2:
                b0 = min(b0, bounds[1] - 1.0)
            bounds = [b0] + bounds[1:]

    for pi, page in enumerate(pages):
        for li, line in enumerate(page["lines"]):
            if pi < hp or (pi == hp and li <= hl):
                continue
            buckets = cols_of(line, bounds)
            amt_toks = [w for w in buckets.get(ai, []) if _MONEY_WORD.match(w[2])]
            money_here = bool(amt_toks) or any(
                _MONEY_WORD.match(w[2]) and re.search(r"\d", w[2])
                for c in (loan_i, ink_i) if c is not None for w in buckets.get(c, []))
            text_of = lambda c: " ".join(w[2] for w in buckets.get(c, [])).strip()
            nm_here = text_of(name_i)
            if not money_here:
                if not nm_here or _SUBHEADER.fullmatch(nm_here):
                    continue          # the table's own `Address` sub-header line, never a name
                # ⚠ A HELD-OVER LINE CARRYING DIGITS IS A STREET ADDRESS, always. `_looks_address`
                # alone is not enough — `460 N 2460 W, Hurricane UT 84737` matches none of its
                # street-word hints and has no comma before the state — and treating such a line
                # as a wrapped NAME appends it to `donor_raw`, which is both a wrong value and a
                # PRIVACY breach (PRIVACY.md: city/state only, the street is discarded). A
                # wrapped personal/business name never carries a street number, so the digit
                # test is the safe side of the ambiguity. (Same rule the `-layout` reader has
                # always used; it was missing here and leaked 57 rows before this fix.)
                if last is not None and (_looks_address(nm_here)
                                         or any(ch.isdigit() for ch in nm_here)):
                    city, state = split_city_state(nm_here)
                    if hasattr(last, "donor_city"):
                        last.donor_city, last.donor_state = city, state
                    continue
                # no digits and not address-shaped: EITHER this record's name printed above its
                # figures, OR the wrapped tail of the row just emitted. The next money line
                # decides which.
                pending_name = (pending_name + " " + nm_here).strip()
                continue
            cov["logical"] = cov.get("logical", 0) + 1
            addr = ""
            if _looks_address(nm_here) and pending_name:
                nm, addr = pending_name, nm_here      # name-above-address layout
            elif nm_here:
                if pending_name and last is not None:
                    attr = "donor_raw" if hasattr(last, "donor_raw") else "vendor_raw"
                    setattr(last, attr, (getattr(last, attr) + " " + pending_name).strip())
                nm = nm_here
            else:
                # name above, and the filer printed NO address line — the held-over line is
                # the donor's name (`Bob and Bev Sands` / `Gil Almquist`, Aldred 2012).
                nm = pending_name
            pending_name = ""
            if not amt_toks:
                # Money printed only in In Kind / Loan. Both are REAL ledger lines the form puts
                # in their own column, and dropping them is what made several sides read short
                # (Kevin Brooks 2010: J Ryan Lee's three IN-KIND entries — $400.00 / $100.92 /
                # $243.13, right-aligned to x=454 under `In Kind`, against cash amounts
                # right-aligned to x=395 under `Amount`). Each column's figures right-align a
                # few points before the NEXT header's start, so the two are unambiguous.
                iktoks = [w for w in buckets.get(ink_i, []) if _MONEY_WORD.match(w[2])
                          and re.search(r"\d", w[2])] if ink_i is not None else []
                ltoks = [w for w in buckets.get(loan_i, []) if _MONEY_WORD.match(w[2])
                         and re.search(r"\d", w[2])] if loan_i is not None else []
                if len(iktoks) == 1 and not ltoks and nm:
                    amt_toks, is_loan, forced_ik = iktoks, False, True
                elif kind == "contributions" and len(ltoks) == 1 and not iktoks and nm:
                    amt_toks, is_loan, forced_ik = ltoks, True, False
                else:
                    skipped.append(
                        "p%d y%.0f: %s row NOT emitted — money printed outside the Amount "
                        "column and not a single clean In-Kind / Loan figure; nothing published"
                        % (pi + 1, line["y0"], kind))
                    continue
            else:
                is_loan = forced_ik = False
            if len(amt_toks) != 1:
                skipped.append("p%d y%.0f: %s row NOT emitted — %d money tokens land in the "
                               "Amount column; nothing published"
                               % (pi + 1, line["y0"], kind, len(amt_toks)))
                continue
            if not nm:
                skipped.append("p%d y%.0f: %s row NOT emitted — an amount with no name in the "
                               "name column" % (pi + 1, line["y0"], kind))
                continue
            val, mk = parse_money_cell(amt_toks[0][2])
            if mk not in ("money", "zero-glyph"):
                skipped.append("p%d y%.0f: %s row NOT emitted — the Amount cell reads %r, which "
                               "is not clean money and is never repaired"
                               % (pi + 1, line["y0"], kind, amt_toks[0][2]))
                continue
            geo = _pct(page, amt_toks[0][0], line["y0"], amt_toks[0][1], line["y1"]) \
                + "@p%d" % (pi + 1)
            # the FIRST DATE-SHAPED token in the date column — never simply the first word:
            # a long vendor name can still spill one token into this territory.
            iso = ""
            for _x0, _x1, t in (buckets.get(date_i, []) if date_i is not None else []):
                iso = _date_any(t)
                if iso:
                    break
            in_kind = forced_ik
            if not in_kind and ink_i is not None:
                ik = text_of(ink_i)
                v, k = parse_money_cell(ik)
                in_kind = (k == "money" and bool(v)) or ik.strip().upper() in ("YES", "Y")
            cov["emitted"] = cov.get("emitted", 0) + 1
            common_kw = dict(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, amount=common.money_str(val),
                in_kind="True" if in_kind else "False", is_incremental="",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(_line_no(pages, pi, li)), extract_method=method,
                needs_review="0" if iso else "1", geometry=geo)
            if kind == "contributions":
                city, state = split_city_state(addr) if addr else ("", "")
                row = ContribRow(donor_raw=nm, donor_city=city, donor_state=state, **common_kw)
                if is_loan:
                    row.donor_type = "loan"
            else:
                row = ExpendRow(vendor_raw=nm, purpose=text_of(desc_i) if desc_i is not None
                                else "", **common_kw)
            out.append(row)
            last = row
    if pending_name and last is not None:
        nmattr = "donor_raw" if hasattr(last, "donor_raw") else "vendor_raw"
        setattr(last, nmattr, (getattr(last, nmattr) + " " + pending_name).strip())
    return out


def _line_no(pages, pi, li):
    """1-based line ordinal across the whole document — the stable `(source_filing, line_no)`
    half of SCHEMA.md's itemized-row key when rows are read from coordinates rather than from
    the `-layout` sidecar's own lines."""
    n = 0
    for j, page in enumerate(pages):
        if j == pi:
            return n + li + 1
        n += len(page["lines"])
    return n + li + 1


# ------------------------------------------------------------------------- xls tables

def _xl_sheets(text):
    """[(sheet_name, [(row_index, [cells])])] from a `### SHEET:` sidecar."""
    out, cur = [], None
    r = 0
    for ln in text.splitlines():
        m = _SHEET.match(ln)
        if m:
            cur = (m.group(1), [])
            out.append(cur)
            r = 0
            continue
        if cur is None:
            continue
        cur[1].append((r, ln.split("\t")))
        r += 1
    return out


def _xl_header(rows, keys):
    """(row_index, {key: column_index}) for the first row naming >=2 of `keys`."""
    for r, cells in rows:
        found = {}
        for c, cell in enumerate(cells):
            t = cell.strip().lower()
            for k in keys:
                if t == k or t.startswith(k):
                    found.setdefault(k, c)
        if len(found) >= 2:
            return r, found
    return None, {}


def _xl_ledger(sheet, rows, meta, kind, skipped, cov=None):
    """Ledger rows from a `.xls` workbook sidecar (real cells).

    TWO STACKING LAYOUTS live in this corpus and they are read from the page, not assumed
    (2026-08-23):

      * 2014-15 — NAME INLINE with the figures, the donor's street address on the row BELOW
        (`Brian Filter | 41722 | 200` then `1724 S Rockcress Dr, St George, UT 84790`);
      * 2012    — NAME ABOVE, the address sharing the figures' row
        (`Bob Holt` then `Po Box 998, Enterprise, UT 84725 | 40991 | 100`).

    Reading the second as if it were the first put the ADDRESS in `donor_raw` — a wrong value
    and a PRIVACY breach at once. The two are told apart by whether the figure row's own name
    cell reads as an address, and the held-over line is only ever used as a NAME.

    In-Kind and Loan figures are real ledger lines the form puts in their own columns; a row
    whose Amount cell is empty but whose In Kind / Loan cell carries one clean figure is
    emitted from that column (`in_kind=True` / `donor_type='loan'`), never moved into Amount.
    """
    # ⚠ `date` is in this key list because the workbooks' EXPENDITURE sheets head their date
    # column `Date`, not `Received` (`4 4 2014 Expenditures - Brock Belnap.xls`:
    # `Recipient | Date | Amount | In Kind | Description`). Without it the column was never
    # located and 1,174 workbook expenditure rows shipped with a BLANK date while the cell
    # beside them held a perfectly good Excel serial.
    hdr_r, cols = _xl_header(rows, ("name", "recipient", "received", "date", "amount", "in kind",
                                    "loan", "description"))
    if hdr_r is None or "amount" not in cols:
        return []
    name_c = cols.get("name", cols.get("recipient", 0))
    out = []
    method = meta.get("extract_method", "washco_split/text")
    last = None
    pending_name = ""
    for r, cells in rows:
        if r <= hdr_r:
            continue

        def cell(i):
            return cells[i].strip() if i is not None and i < len(cells) else ""

        nm_here = cell(name_c)
        amt, kindm = parse_money_cell(cell(cols["amount"]))
        ik_v, ik_k = parse_money_cell(cell(cols.get("in kind")))
        ln_v, ln_k = parse_money_cell(cell(cols.get("loan")))
        money_here = (kindm in ("money", "zero-glyph") or ik_k == "money" or ln_k == "money"
                      or kindm == "unparseable")
        if not money_here:
            if not nm_here or _SUBHEADER.fullmatch(nm_here):
                continue              # the table's own `Address` sub-header line, never a name
            if last is not None and (_looks_address(nm_here)
                                     or any(ch.isdigit() for ch in nm_here)):
                # a held-over line carrying digits is the donor's STREET ADDRESS — kept as
                # city/state only, never appended to `donor_raw` (see the bbox reader's note)
                city, state = split_city_state(nm_here)
                if hasattr(last, "donor_city"):
                    last.donor_city, last.donor_state = city, state
                continue
            pending_name = (pending_name + " " + nm_here).strip()
            continue
        if cov is not None:
            cov["logical"] = cov.get("logical", 0) + 1
        addr = ""
        if _looks_address(nm_here) and pending_name:
            nm, addr = pending_name, nm_here
        elif nm_here:
            if pending_name and last is not None:
                attr = "donor_raw" if hasattr(last, "donor_raw") else "vendor_raw"
                setattr(last, attr, (getattr(last, attr) + " " + pending_name).strip())
            nm = nm_here
        else:
            nm = pending_name
        pending_name = ""
        is_loan = False
        in_kind = ik_k == "money" and bool(ik_v)
        geo_col = cols["amount"]
        if kindm not in ("money", "zero-glyph"):
            if kindm == "unparseable":
                skipped.append(f"{sheet} row {r + 1}: {kind} row NOT emitted — the Amount cell "
                               f"reads {cell(cols['amount'])!r}, which is not clean money and is "
                               f"never repaired; nothing published")
                continue
            if ik_k == "money" and ln_k != "money":
                amt, in_kind, geo_col = ik_v, True, cols["in kind"]
            elif ln_k == "money" and ik_k != "money" and kind == "contributions":
                amt, is_loan, geo_col = ln_v, True, cols["loan"]
            else:
                skipped.append(f"{sheet} row {r + 1}: {kind} row NOT emitted — money printed "
                               f"outside the Amount column and not a single clean In-Kind / "
                               f"Loan figure; nothing published")
                continue
        if not nm:
            skipped.append(f"{sheet} row {r + 1}: {kind} row NOT emitted — amount printed with "
                           f"no name in the name column")
            continue
        if cov is not None:
            cov["emitted"] = cov.get("emitted", 0) + 1
        iso = _date_any(cell(cols.get("received"))) or _date_any(cell(cols.get("date")))
        rest = cell(cols.get("description"))
        geo = geom_cell(sheet, r, geo_col)
        base_kw = dict(
            candidate=meta["candidate"], office=meta.get("office", ""),
            seat=meta.get("seat", ""), election_year=meta["election_year"],
            filing_date=meta.get("filing_date", ""),
            reporting_period=meta.get("reporting_period", ""),
            date=iso, amount=common.money_str(amt),
            in_kind="True" if in_kind else "False", is_incremental="",
            source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
            line_no=str(r + 1), extract_method=method,
            needs_review="0" if iso else "1", geometry=geo)
        if kind == "contributions":
            city, state = split_city_state(addr) if addr else ("", "")
            row = ContribRow(donor_raw=nm, donor_city=city, donor_state=state, **base_kw)
            if is_loan:
                row.donor_type = "loan"
        else:
            row = ExpendRow(vendor_raw=nm, purpose=rest, **base_kw)
        out.append(row)
        last = row
    if pending_name and last is not None:
        attr = "donor_raw" if hasattr(last, "donor_raw") else "vendor_raw"
        setattr(last, attr, (getattr(last, attr) + " " + pending_name).strip())
    return out


# ------------------------------------------------------------------------- the SUMMARY

def _summary_xls(rows, deadline, notes):
    hdr_r, cols = _xl_header(rows, _SUM_HDRS)
    if hdr_r is None or "contributions" not in cols:
        return None
    starts = sorted(cols.values())
    span = {}
    for key, c in cols.items():
        nxt = next((x for x in starts if x > c), 10 ** 6)
        span[key] = (c, nxt)
    best = None
    for r, cells in rows:
        if r <= hdr_r:
            continue

        def cell(i):
            return cells[i].strip() if i < len(cells) else ""

        due = _date_any(cell(cols.get("date due", 0)))
        sub = _date_any(cell(cols.get("submitted", 0)))
        vals = {}
        for key in ("contributions", "expenditures", "balance"):
            if key not in span:
                continue
            lo, hi = span[key]
            parts = []
            for c in range(lo, min(hi, len(cells))):
                v, k = parse_money_cell(cells[c].strip())
                if k in ("money", "zero-glyph"):
                    parts.append(v)
            vals[key] = round(sum(parts), 2) if parts else None
        if all(v is None for v in vals.values()):
            continue
        row = dict(due=due, submitted=sub, **vals)
        if deadline and due and due == deadline:
            notes.append(f"summary row selected by matching the filing's deadline {deadline}")
            return row
        best = row
    if best is not None:
        notes.append("summary row = the LAST printed row carrying a figure (no deadline supplied "
                     "to match on)")
    return best


def _summary_pdf(lines, deadline, notes):
    hdr_i, cols = _pdf_header(lines, re.compile(r"Contributions", re.I),
                              ["Submitted", "Date Due", "Contributions", "Expenditures",
                               "Balance"])
    if hdr_i is None or len(cols) < 3:
        return None
    terr = _territories([c[1] for c in cols])
    idx = {c[0].lower(): i for i, c in enumerate(cols)}
    best = None
    for k in range(hdr_i + 1, len(lines)):
        ln = lines[k]
        cells, _ok = _assign_strict(ln, terr)
        if not cells:
            continue
        due = ""
        if "date due" in idx:
            lo, hi = terr[idx["date due"]]
            due = _date_any(ln[lo:hi].strip())
        sub = ""
        if "submitted" in idx:
            lo, hi = terr[idx["submitted"]]
            sub = _date_any(ln[lo:hi].strip())
        row = dict(due=due, submitted=sub,
                   contributions=cells.get(idx.get("contributions"), (None,))[0],
                   expenditures=cells.get(idx.get("expenditures"), (None,))[0],
                   balance=cells.get(idx.get("balance"), (None,))[0])
        if deadline and due and due == deadline:
            notes.append(f"summary row selected by matching the filing's deadline {deadline}")
            return row
        best = row
    if best is not None:
        notes.append("summary row = the LAST printed row carrying a figure (no deadline supplied "
                     "to match on)")
    return best


# ------------------------------------------------------------------------------- entry

def parse_group(parts, meta) -> dict:
    """The driver's multi-FILE hook: `parts` are the Summary + Contributions + Expenditures files
    of ONE logical filing (or a single combined file). Their roles are read from each DOCUMENT,
    never from its filename."""
    notes, skipped = [], []
    crows, erows = [], []
    summary = None
    deadline = (meta.get("deadline") or "").strip()
    # SIDE COVERAGE (2026-08-23): money-bearing logical rows FOUND vs rows EMITTED, per side.
    # The module-local builder uses it as a completeness gate — a side whose parse is short is
    # WITHHELD rather than published as a short sum, so a delta can only ever mean the FILER's
    # own arithmetic, never ours.
    cov = {"contributions": {"logical": 0, "emitted": 0},
           "expenditures": {"logical": 0, "emitted": 0}}

    for part in parts:
        text = part.get("text", "")
        role = classify(part)
        base = dict(meta)
        # ⚠ STAMP THE ROW'S OWN PART FILE (2026-08-23 — the documented multi-file emission bug,
        # SCHEMA.md 2a caveat 1). One washington filing is up to THREE published files, and a
        # row's `line_no` / `geometry` are measured inside the file it was READ from, not inside
        # the group's primary (the Summary). Stamping the primary made `(source_filing, line_no)`
        # — the schema's itemized-row key — point at the wrong document, which `make_snippet.py`
        # then had to repair downstream by span-content search. Fixed AT EMISSION here.
        base["source_filing"] = ((part.get("ix") or {}).get("path")
                                 or meta.get("source_filing", ""))
        if is_xls(text):
            sheets = _xl_sheets(text)
            for sheet, rows in sheets:
                if not any(any(c.strip() for c in cells) for _r, cells in rows):
                    continue
                flat = "\n".join("\t".join(c) for _r, c in rows)
                if _H_SUMMARY.search(flat):
                    summary = summary or _summary_xls(rows, deadline, notes)
                elif _H_CONTRIB.search(flat):
                    crows += _xl_ledger(sheet, rows, base, "contributions", skipped,
                                        cov["contributions"])
                elif _H_EXPEND.search(flat):
                    erows += _xl_ledger(sheet, rows, base, "expenditures", skipped,
                                        cov["expenditures"])
            continue

        lines = text.splitlines()
        pl = page_line_index(text)
        if role in ("summary", "mixed") or _H_SUMMARY.search(text):
            summary = summary or _summary_pdf(lines, deadline, notes)
        for rx, kind, labels in (
                (_H_CONTRIB, "contributions", ["Name", "Received", "Amount", "In Kind", "Loan",
                                               "Date", "Name of Contributor"]),
                (_H_EXPEND, "expenditures", ["Recipient", "Received", "Amount", "In Kind",
                                             "Description", "Date", "Name"])):
            m = rx.search(text)
            if not m:
                continue
            start = text[:m.start()].count("\n")
            hdr_i, cols = _pdf_header(lines[start:start + 12],
                                      re.compile(r"Amount", re.I), labels)
            if hdr_i is None:
                continue
            hdr_i += start
            stop = len(lines)
            for other in (_H_CONTRIB, _H_EXPEND, _H_SUMMARY):
                if other is rx:
                    continue
                mo = other.search(text[m.end():])
                if mo:
                    stop = min(stop, text[:m.end() + mo.start()].count("\n"))
            if re.search(r"Detailed\s+\w+\s+Report", text, re.I):
                # The 2008 `Detailed … Report` prints its column header ONCE and then re-lays the
                # table out differently on every following page, and the filing prints no totals
                # at all (`CLAUDE.md`: `ledger_only`, 4 filings, "the filing prints no totals").
                # There is therefore nothing to prove completeness against and no stable column
                # geometry — so NO rows are emitted. `portal_stated_totals.csv` holds the county's
                # own printed 2008 figures; that is the source for this era.
                skipped.append(f"{kind}: NO rows emitted from the 2008 'Detailed … Report' — its "
                               f"column header is printed once and the layout shifts per page, "
                               f"and the filing prints no total to prove completeness against")
                continue
            # TRUE-COORDINATE path first (see `_bbox_rows`): it is the same table read from the
            # PDF's own word boxes, so a multi-page ledger keeps ONE column model and every row
            # carries `pct:` geometry. The `-layout` reader stays as the fallback for a part
            # whose caller supplied no boxes.
            bb = part.get("bbox")
            rows = None
            if bb:
                win = _bbox_window(bb, rx)
                if win:
                    probe = {"logical": 0, "emitted": 0}
                    rows = _bbox_rows(bb, base, kind, skipped, probe, labels, win)
                    if rows:
                        cov[kind]["logical"] += probe["logical"]
                        cov[kind]["emitted"] += probe["emitted"]
                        notes.append("%s read from TRUE PDF coordinates (`pdftotext -bbox-"
                                     "layout`): one header-derived column model across all "
                                     "pages, `pct:` geometry per row" % kind)
            if not rows:
                rows = _pdf_rows(lines, hdr_i, cols, stop, base, pl, kind, skipped, cov[kind])
            (crows if kind == "contributions" else erows).extend(rows)

    stated_c = summary.get("contributions") if summary else None
    stated_e = summary.get("expenditures") if summary else None
    stated_b = summary.get("balance") if summary else None
    if summary is None:
        notes.append("LEDGER-ONLY filing — the file set prints no totals sheet; stated totals "
                     "stay BLANK (blank is never 0 here)")

    # Per-FILING regime (CLAUDE.md "Filing-style finding"): a summary_sheet filing's summary rows
    # are PER-PERIOD increments while its companion ledgers restate the cycle to date, so the
    # ledger — not the sum of summary rows — is the cycle total.
    if summary is not None:
        regime, inc = "incremental", "True"
        notes.append("sheet_type=summary_sheet: the summary row is a PER-PERIOD increment; the "
                     "companion ledgers restate the cycle to date — never sum the summary rows")
    else:
        regime, inc = None, None
    for r in crows + erows:
        if inc:
            r.is_incremental = inc
    notes += skipped

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_c, stated_expend=stated_e,
                stated_begin=None, stated_end=stated_b,
                is_incremental=inc, dedup_mode=regime,
                coverage=cov, summary_row=summary,
                notes="; ".join(notes))


def parse(text: str, meta: dict) -> dict:
    """Single-file entry — the county also publishes COMBINED PDFs holding the summary and both
    ledgers (`live_wp/2010-David-Whitehead.pdf`). Same code path, one part."""
    return parse_group([dict(ix={}, text=text, sidecar="", is_scanned=meta.get("is_scanned"))],
                       meta)
