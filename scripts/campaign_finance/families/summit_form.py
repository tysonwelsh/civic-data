#!/usr/bin/env python3
"""summit_form.py — Summit County Clerk's "CAMPAIGN FINANCIAL REPORT" (Utah Code 17-16-6.5).

THE ONE THING THIS FAMILY EXISTS TO GET RIGHT — THE REVERSED COLUMN ORDER.

EVIDENCE (summit_county/campaign_finance/):
  * `CLAUDE.md` "The column trap" — "Summit's cover box runs **`Current Report | Last Report |
    Cumulative Totals`** — the **REVERSE** of the sheet the shared parsers assume (Millcreek
    prints `LAST | THIS | CUMULATIVE`). The 2024 sheet renames the middle column
    **`Previous Report`**; the ORDER never changes. A parser that takes 'the second-to-last
    money token' reads Summit's **Last Report** column and is silently wrong."
  * `RECON.md` §4, measured on `text/20765_Langston-Post-Election-2022.txt` (born-digital;
    printed contributions **$503.00**, printed expenditures **$511.62**): `millcreek_form` and
    `ogden_form` both return **511.62 as "total contributions"**, and every other registered
    family returns None on one or both sides. The unit test asserts BOTH that 503.00/511.62 are
    produced AND that 511.62 is NOT produced as a contribution total.
  * `RECON.md` §4 reason 2 — "the itemization headers are `ITEMIZED CONTRIBUTION REPORT`, not
    `FORM \"A\"` — so section tagging finds nothing and the expenditure side comes back empty."

HOW THE COVER IS READ — by X-POSITION, never by ordinal. The three column headers give three
column territories (boundaries at the midpoints between header starts); every money token on the
row's value line is assigned to the territory containing its CENTRE. This is the only way to read
a row with a BLANK middle cell: Langston's `Campaign balance` row prints `$11.14 … $11.17` — two
tokens, three columns — and an ordinal reader puts $11.17 in `Last Report`. A column with no
money token is then sliced and classified (`empty` / `nil` / `unparseable`) for the notes only.

PROMOTION RULE (verbatim from `CLAUDE.md` "The promotion rule", applied per cover row):
  1. `cumulative` when that cell holds a parseable amount;
  2. `current` when the cumulative cell is empty or illegible;
  3. `current`/`previous` when the cumulative cell parses to ZERO on a contributions or
     expenditures row whose Current or Previous cell is non-zero (the fillable template's default
     `$ 0.00` left in place) — NEVER applied to the balance row;
  4. otherwise BLANK + a note. A blank stated total is an honest gap, never a zero.
On the pre-2022 `split50` sheet a contribution total is line 1 (`donors giving more than $50`) +
line 2 (`donors giving $50 or less`), summing ONLY the lines actually printed (the juab precedent).

MONEY: `common.parse_money_cell`, so the ZERO-GLYPH RULING (GOTCHAS.md, owner 2026-08-02) holds —
`Ø` / `-0-` / "zero" read as 0, a bare dash / `N/A` / an empty cell stays BLANK — and a MALFORMED
decimal is never repaired: Ioannides 2024 (`24231`) prints cumulative contributions `23,744,71`
(comma in the cents position), which stays unparseable so rule 2 promotes the Current column
`23,744.71` — the figure `AVAILABILITY.md` records for that filing.

ITEMIZATION + THE COMPLETENESS GATE. Sections are tagged on `ITEMIZED CONTRIBUTION REPORT` /
`ITEMIZED EXPENSE REPORT` (2024 prints them in title case). A data row is a leading date token +
a trailing money token; interior `Total …` lines are dropped. TWO gates, both mandatory:

  * **The printed TEMPLATE EXAMPLE rows are dropped, with a reason.** Summit's blank form prints
    a worked example in the first data row of each table — `8/25/10  Jon and Jane Doe  PO Box 128,
    Coalville, UT  84017  $435.00` and `8/25/10  Name of Business  Campaign signs and flyers
    $512.00` — and they survive into the text of essentially every filing (grep-verified across
    the corpus, OCR variants included). Detected by the placeholder name OR by a date outside the
    filing's plausible window (`common.date_in_window`); never by their amount. On Langston that
    is exactly the difference between a wrong ledger and an exact one: 938.00 − 435.00 = **503.00**
    and 1,023.62 − 512.00 = **511.62**, both matching the promoted cover figures to the cent.
  * **A section whose rows do not SUM to its own printed total emits NO ROWS + a reason.** The
    2014 sheets wrap a long contributor name across four laid-out lines, which drops the row's
    money from the row's line entirely; a silently short donor list is worse than none
    (`RECON.md` §4: "A silently-wrong total is worse than no total"). Set `EMIT_UNRECONCILED`
    only with a documented reason.

DEDUP: the cover box is `LAST + THIS = CUMULATIVE` and the promoted figure is the CUMULATIVE
column, so a candidate-cycle total is the LATEST non-superseded report — `dedup_mode="cumulative"`,
`is_incremental="False"`, declared PER FILING so it composes with a run-level mode.

PRIVACY: itemized rows carry `donor_city` / `donor_state` only (`common.split_city_state`); the
street/PO-box portion of a mailing address is discarded, never stored.
"""
from __future__ import annotations

import re

import common
from common import (ContribRow, ExpendRow, parse_money_cell, money_cell_spans,
                    split_city_state, geom_text, page_line_index, date_in_window, parse_date)

# ---------------------------------------------------------------- cover box anchors
_HDR_CUR = re.compile(r"Current\s+Report", re.I)
_HDR_MID = re.compile(r"(?:Last|Previous)\s+Report", re.I)
# `Cumulative Totals` WRAPS on some vintages (Robinson 2022 prints `Cumulative` on the header
# line and `Totals` on the next), so the word `Cumulative` alone anchors the third column; the
# ordering check below is what actually establishes it is the third.
_HDR_CUM = re.compile(r"Cumulative(?:\s+Totals?)?", re.I)

_ROW_CONTRIB = re.compile(r"^\s*Total\s+contributions?\b", re.I)
_ROW_GT50 = re.compile(r"giving\s+more\s+than\s+\$?\s*50", re.I)
_ROW_LE50 = re.compile(r"giving\s+\$?\s*50\s+or\s+less", re.I)
_ROW_EXPEND = re.compile(r"^\s*Total\s+(?:amount\s+of\s+)?expenditures?\b", re.I)
_ROW_BALANCE = re.compile(r"^\s*Campaign\s+balance\b", re.I)

# ---------------------------------------------------------------- itemization anchors
_SEC_C = re.compile(r"ITEMIZED\s+CONTRIBUTION\s+REPORT", re.I)
_SEC_E = re.compile(r"ITEMIZED\s+(?:EXPENSE|EXPENDITURES?)\s+REPORT", re.I)
_TOTAL_LINE = re.compile(r"\bTOTAL\b", re.I)
_DATE_LEAD = re.compile(r"^\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b")

# The printed template EXAMPLE rows (quoted from the blank Summit form; see the docstring).
_TEMPLATE_NAMES = ("jon and jane doe", "name of business")

EMIT_UNRECONCILED = False   # see "the completeness gate" in the docstring


def _norm(s):
    return re.sub(r"[^a-z ]+", "", (s or "").lower()).strip()


def _cover_columns(lines):
    """(header_index, [(name, start_col), …]) for the 3-column cover header, or (None, [])."""
    for i, ln in enumerate(lines):
        mc, mm, mu = _HDR_CUR.search(ln), _HDR_MID.search(ln), _HDR_CUM.search(ln)
        if mc and mm and mu and mc.start() < mm.start() < mu.start():
            return i, [("current", mc.start()), ("middle", mm.start()), ("cumulative", mu.start())]
    return None, []


def _boundaries(cols):
    """Column territories from the header starts: midpoints between consecutive headers."""
    starts = [c[1] for c in cols]
    edges = [0]
    for a, b in zip(starts, starts[1:]):
        edges.append((a + b) // 2)
    edges.append(10 ** 6)
    return edges


def _pure_money_line(ln):
    """True when the line's ONLY content is money tokens (the cover value lines are printed on
    their own line on most Summit vintages). `giving more than $50` is NOT pure money."""
    sp = money_cell_spans(ln)
    if not sp:
        return False
    residue = ln
    for s, e, _v, _r in sp:
        residue = residue[:s] + " " * (e - s) + residue[e:]
    return re.sub(r"[\s$|]+", "", residue) == ""


def _row_cells(lines, i, cols, edges):
    """Read one cover row anchored at label line `i` -> (value_line_index, {col: (value, kind)}).

    The filled value sits EITHER on the label line itself (the 2026 vintage prints
    `Total Contributions   $  1,000.00   $  109.63   $  1,109.63`) or on a nearby line of its own
    (2014-2024 print the numbers on the line ABOVE or BELOW the label). Money tokens are assigned
    by CENTRE position; a column with no token is sliced and classified for the note."""
    cand = None
    lab_end = _label_end(lines[i])
    # The label line is its own value line ONLY when it carries content AT OR BEYOND the Current
    # column (the 2024/2026 vintages print `Total Contributions   $ 1,000.00   $ 109.63   $ …`).
    # The test is on CONTENT, not on a money token, because a cover cell is often a bare `0`
    # (Ioannides' `Campaign Balance   0   0`) which is deliberately not a money token elsewhere in
    # the library. Without the POSITION test, the split50 label `giving more than $50` would read
    # its own printed threshold as the Current cell.
    tail = lines[i][lab_end:]
    if tail.strip():
        first = lab_end + (len(tail) - len(tail.lstrip()))
        if first >= cols[0][1] - 10:
            cand = i
    if cand is None:
        for j in (i - 1, i + 1, i + 2, i - 2, i + 3):
            if 0 <= j < len(lines) and _pure_money_line(lines[j]):
                cand = j
                break
    if cand is None:
        return None, {}
    ln = lines[cand]
    cells = {}
    for s, e, v, raw in money_cell_spans(ln):
        if cand == i and s < lab_end:
            continue                       # a threshold printed inside the label is not a cell
        centre = (s + e) // 2
        for k, (name, _st) in enumerate(cols):
            if edges[k] <= centre < edges[k + 1]:
                if name not in cells:
                    cells[name] = (v, "money", s, e)
                break
    for k, (name, _st) in enumerate(cols):
        if name in cells:
            continue
        lo, hi = edges[k], min(edges[k + 1], len(ln))
        if cand == i:
            lo = max(lo, lab_end)
        raw = ln[lo:hi] if lo < len(ln) and lo < hi else ""
        v, kind = parse_money_cell(raw.strip())
        cells[name] = (v, kind, None, None)
    return cand, cells


def _label_end(ln):
    """Character column at which a cover label's WORDS stop — the leading alpha run only, so a
    figure printed to its right is never absorbed into the label and the label's own text is
    never sliced into the `current` cell. A line with no leading alpha run returns 0."""
    m = re.match(r"\s*[A-Za-z]+(?: [A-Za-z]+)*", ln)
    return m.end() if m and m.group().strip() else 0


def _promote(cells, is_balance):
    """The documented promotion rule -> (value_or_None, basis_note)."""
    cum = cells.get("cumulative", (None, "empty"))
    cur = cells.get("current", (None, "empty"))
    mid = cells.get("middle", (None, "empty"))
    cum_v, cum_k = cum[0], cum[1]
    cur_v, cur_k = cur[0], cur[1]
    mid_v, mid_k = mid[0], mid[1]
    if cum_k in ("money", "zero-glyph") and cum_v is not None:
        if (not is_balance) and abs(cum_v) < 0.005:
            other = cur_v if (cur_k in ("money", "zero-glyph") and cur_v) else (
                mid_v if (mid_k in ("money", "zero-glyph") and mid_v) else None)
            if other:
                which = "current" if (cur_k in ("money", "zero-glyph") and cur_v) else "previous"
                return other, (f"promoted {which} (cumulative cell prints 0.00 against a "
                               f"non-zero {which} — template default)")
        return cum_v, "promoted cumulative"
    if cur_k in ("money", "zero-glyph") and cur_v is not None:
        return cur_v, f"promoted current (cumulative cell {cum_k})"
    return None, f"no promotable figure (current={cur_k}, cumulative={cum_k})"


# ---------------------------------------------------------------------- itemization

def _sections(lines):
    """(contrib_lines, expend_lines) as [(index, line)], tagged on the printed section headers."""
    c, e, mode = [], [], None
    for k, ln in enumerate(lines):
        if _SEC_C.search(ln):
            mode = "c"
            continue
        if _SEC_E.search(ln):
            mode = "e"
            continue
        (c if mode == "c" else e if mode == "e" else []).append((k, ln))
    return c, e


def _row_parts(ln):
    """(date_token, body_before_amount, amount, span) or None.

    A ledger row is a TRAILING money token with at least one alphabetic field to its left. The
    leading date is OPTIONAL: Langston's 7/7/22 $50.00 row has its date pushed onto the next
    laid-out line, and requiring a date silently dropped it (453.00 instead of the printed
    503.00). A dateless row keeps `date` blank rather than borrowing a neighbour's."""
    sp = money_cell_spans(ln)
    if not sp:
        return None
    s, e, v, _raw = sp[-1]
    dm = _DATE_LEAD.match(ln)
    body = ln[dm.end():s] if dm else ln[:s]
    if not re.search(r"[A-Za-z]{2}", body):
        return None
    return (dm.group(1) if dm else ""), body, v, (s, e)


def _is_template(name, extra, iso, meta):
    """Detect the form's own printed EXAMPLE row — by the PLACEHOLDER TEXT only.

    An earlier draft also treated an out-of-window date as a template marker. That was WRONG and
    is deliberately not here: on Martinez 2014 (`1064`) it dropped 90+ genuine donor and vendor
    rows whose only fault was a filing date this parser does not know precisely. A template row is
    identified by what the blank form prints, never by a date heuristic — and any example row that
    slipped through would break the completeness gate rather than be published."""
    if _norm(name) in _TEMPLATE_NAMES or _norm(extra).startswith("campaign signs and fly"):
        return "printed template example row"
    return ""


def _build(section, meta, is_contrib, pl):
    rows, dropped = [], []
    method = meta.get("extract_method", "summit_form/text")
    for k, ln in section:
        if _TOTAL_LINE.search(ln):
            continue
        parts = _row_parts(ln)
        if parts is None:
            continue
        dtok, body, amount, (s, e) = parts
        fields = [t for t in re.split(r"\s{2,}", body.strip()) if t.strip()]
        name = fields[0].strip() if fields else ""
        extra = " ".join(f.strip() for f in fields[1:]).strip()
        iso = parse_date(dtok) or ""
        why = _is_template(name, extra, iso, meta)
        if why:
            dropped.append(f"line {k + 1} dropped: {why} ({name or extra})".strip())
            continue
        page, lno = pl[k] if k < len(pl) else (1, k + 1)
        geo = geom_text(page, lno, s, e)
        if is_contrib:
            city, state = split_city_state(" ".join(fields[1:]))
            rows.append(ContribRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, donor_raw=name, donor_city=city, donor_state=state,
                amount=common.money_str(amount), in_kind="False", is_incremental="False",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(k + 1), extract_method=method,
                needs_review="0" if name else "1", geometry=geo))
        else:
            rows.append(ExpendRow(
                candidate=meta["candidate"], office=meta.get("office", ""),
                seat=meta.get("seat", ""), election_year=meta["election_year"],
                filing_date=meta.get("filing_date", ""),
                reporting_period=meta.get("reporting_period", ""),
                date=iso, vendor_raw=name, purpose=extra,
                amount=common.money_str(amount), in_kind="False", is_incremental="False",
                source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
                line_no=str(k + 1), extract_method=method,
                needs_review="0" if name else "1", geometry=geo))
    return rows, dropped


def _gate(rows, stated, current, side, notes):
    """Completeness gate. Rows survive ONLY when they sum to the figure the driver will
    reconcile them against — the PROMOTED (cumulative-first) cover total.

    Two distinct honest failures are told apart, because the follow-up differs:
      * Σrows == the CURRENT column but != the promoted CUMULATIVE — the ledger is period-scoped
        under a cycle-to-date cover (Harte 2026: 2 rows = $1,000.00 Current vs $1,109.63
        Cumulative). The rows are complete FOR THE PERIOD, but publishing them against a cycle
        total would state an incoherent pair, so they are withheld and the note names both
        figures. This is the documented follow-up for a period-grain itemized tranche.
      * Σrows != anything printed — the itemization is genuinely short (the 2014 sheets wrap a
        contributor name across four laid-out lines, taking the row's money off its own line).
        `RECON.md` §4: "A silently-wrong total is worse than no total."
    """
    if not rows:
        return []
    total = round(sum(float(r.amount) for r in rows if r.amount), 2)
    if stated is not None and abs(total - stated) <= 0.01:
        return rows
    if current is not None and abs(total - current) <= 0.01:
        notes.append(f"{side}: {len(rows)} row(s) NOT emitted — the ledger is PERIOD-scoped "
                     f"(Sum rows {total:.2f} = the Current column) under a CUMULATIVE cover "
                     f"({'blank' if stated is None else format(stated, '.2f')}) -- publishing "
                     f"them against a cycle total would state an incoherent pair")
        return rows if EMIT_UNRECONCILED else []
    notes.append(f"{side}: {len(rows)} row(s) NOT emitted — Sum rows {total:.2f} matches no "
                 f"printed figure (cover {'blank' if stated is None else format(stated, '.2f')})"
                 f" -- itemization incomplete, a short ledger is not published as complete")
    return rows if EMIT_UNRECONCILED else []


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()
    pl = page_line_index(text)
    notes = []

    hdr, cols = _cover_columns(lines)
    stated_contrib = stated_expend = stated_end = None
    cur_contrib = cur_expend = None
    if hdr is None:
        notes.append("cover box NOT found (no 'Current Report | Last/Previous Report | "
                     "Cumulative' header) — no stated totals read")
    else:
        edges = _boundaries(cols)
        notes.append(f"cover columns: {'|'.join(n for n, _ in cols)} "
                     f"(Summit order is Current FIRST — never the millcreek LAST|THIS|CUM)")

        def _read(rx, is_balance=False, start=hdr):
            for i in range(start, len(lines)):
                if rx.search(lines[i]):
                    _vi, cells = _row_cells(lines, i, cols, edges)
                    if cells:
                        return _promote(cells, is_balance), cells
            return (None, "row label not printed"), {}

        def _cur(cells):
            v = cells.get("current")
            return v[0] if v and v[1] in ("money", "zero-glyph") else None

        (c_direct, c_note), c_cells = _read(_ROW_CONTRIB)
        if c_cells:
            stated_contrib, cur_contrib = c_direct, _cur(c_cells)
            notes.append(f"contributions: {c_note}")
        else:
            (gt, gt_note), gt_cells = _read(_ROW_GT50)
            (le, le_note), le_cells = _read(_ROW_LE50)
            parts = [v for v in (gt, le) if v is not None]
            if parts:
                stated_contrib = round(sum(parts), 2)
                cur_parts = [v for v in (_cur(gt_cells), _cur(le_cells)) if v is not None]
                cur_contrib = round(sum(cur_parts), 2) if cur_parts else None
                notes.append(f"contributions = split50 line1+line2, summing only the printed "
                             f"lines ({gt_note} / {le_note})")
            else:
                notes.append("contributions: no cover row found")
        (e_val, e_note), e_cells = _read(_ROW_EXPEND)
        stated_expend, cur_expend = e_val, _cur(e_cells)
        notes.append(f"expenditures: {e_note}")
        (b_val, b_note), _b_cells = _read(_ROW_BALANCE, is_balance=True)
        stated_end = b_val
        notes.append(f"balance: {b_note}")

    csec, esec = _sections(lines)
    if not csec and not esec:
        notes.append("no ITEMIZED section header found — itemization not attempted")
    crows, cdrop = _build(csec, meta, True, pl)
    erows, edrop = _build(esec, meta, False, pl)
    notes += cdrop + edrop
    crows = _gate(crows, stated_contrib, cur_contrib, "contributions", notes)
    erows = _gate(erows, stated_expend, cur_expend, "expenditures", notes)

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=stated_end,
                is_incremental="False", dedup_mode="cumulative",
                notes="; ".join(notes))
