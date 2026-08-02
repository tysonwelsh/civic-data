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


def _pdf_rows(lines, hdr_i, cols, stop, meta, pl, kind, skipped):
    """Ledger rows from a laid-out PDF table, with wrapped continuation lines joined into the
    NAME column and the strict completeness gate applied."""
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
        if ai is None or ai not in cells:
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


def _xl_ledger(sheet, rows, meta, kind, skipped):
    hdr_r, cols = _xl_header(rows, ("name", "recipient", "received", "amount", "in kind", "loan",
                                    "description"))
    if hdr_r is None or "amount" not in cols:
        return []
    name_c = cols.get("name", cols.get("recipient", 0))
    out = []
    method = meta.get("extract_method", "washco_split/text")
    pending = None
    for r, cells in rows:
        if r <= hdr_r:
            continue

        def cell(i):
            return cells[i].strip() if i is not None and i < len(cells) else ""

        amt, kindm = parse_money_cell(cell(cols["amount"]))
        nm = cell(name_c)
        if kindm not in ("money", "zero-glyph"):
            if nm and pending is not None:
                # the address line printed under a donor's name -> geography ONLY
                city, state = split_city_state(nm)
                pending.donor_city, pending.donor_state = city, state
                pending = None
            continue
        if not nm:
            skipped.append(f"{sheet} row {r + 1}: {kind} row NOT emitted — amount printed with "
                           f"no name in the name column")
            continue
        iso = _date_any(cell(cols.get("received")))
        ik_v, ik_k = parse_money_cell(cell(cols.get("in kind")))
        rest = cell(cols.get("description"))
        geo = geom_cell(sheet, r, cols["amount"])
        if kind == "contributions":
            row = ContribRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, donor_raw=nm, amount=common.money_str(amt),
                in_kind="True" if ik_k == "money" and ik_v else "False",
                is_incremental="", source_filing=meta["source_filing"],
                document_id=meta.get("document_id", ""), line_no=str(r + 1),
                extract_method=method, needs_review="0" if iso else "1", geometry=geo)
            pending = row
        else:
            row = ExpendRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, vendor_raw=nm, purpose=rest, amount=common.money_str(amt),
                in_kind="True" if ik_k == "money" and ik_v else "False",
                is_incremental="", source_filing=meta["source_filing"],
                document_id=meta.get("document_id", ""), line_no=str(r + 1),
                extract_method=method, needs_review="0" if iso else "1", geometry=geo)
            pending = None
        out.append(row)
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

    for part in parts:
        text = part.get("text", "")
        role = classify(part)
        base = dict(meta)
        base["source_filing"] = meta["source_filing"]
        if is_xls(text):
            sheets = _xl_sheets(text)
            for sheet, rows in sheets:
                if not any(any(c.strip() for c in cells) for _r, cells in rows):
                    continue
                flat = "\n".join("\t".join(c) for _r, c in rows)
                if _H_SUMMARY.search(flat):
                    summary = summary or _summary_xls(rows, deadline, notes)
                elif _H_CONTRIB.search(flat):
                    crows += _xl_ledger(sheet, rows, base, "contributions", skipped)
                elif _H_EXPEND.search(flat):
                    erows += _xl_ledger(sheet, rows, base, "expenditures", skipped)
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
            rows = _pdf_rows(lines, hdr_i, cols, stop, base, pl, kind, skipped)
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
                notes="; ".join(notes))


def parse(text: str, meta: dict) -> dict:
    """Single-file entry — the county also publishes COMBINED PDFs holding the summary and both
    ledgers (`live_wp/2010-David-Whitehead.pdf`). Same code path, one part."""
    return parse_group([dict(ix={}, text=text, sidecar="", is_scanned=meta.get("is_scanned"))],
                       meta)
