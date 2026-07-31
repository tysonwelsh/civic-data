#!/usr/bin/env python3
"""taylorsville_form.py — extractor for Taylorsville City's self-hosted "Report of
Contributions & Expenditures" (UCA 10-3-208 / Taylorsville City Code 2.36.040).

THE DEFINING QUIRK (verified 2026-07-06): Taylorsville hosts a FILLABLE PDF whose text layer is
a static TEMPLATE — the numbered summary block, the ATTACHMENT/ITEMIZED section headers, and the
"TOTAL $..." lines all print, but the ACTUAL FIGURES ARE HANDWRITTEN and rastered into the page
image. `pdftotext -layout` therefore recovers the boilerplate cleanly while the real dollar
values come back as OCR garble ("23 a b. 3D", "1043.", "c747.") or not at all. So EVEN THE
"BORN-DIGITAL" (format=text) FILINGS NEED VISION for their numbers — with a small exception:

  * A handful of the NEWEST fillable forms (2025-2026 template) auto-populate their totals as
    typed accounting cells ("$   -" for zero, "$0.00", or a real typed "$200.00"). Where EVERY
    inspected total line on a filing is a cleanly-typed cell (no handwriting garble anywhere),
    this family reads those typed printed totals in TEXT mode. In the current corpus that clean
    set is the three all-zeros annual statements (2026 Knudsen, 2026 Barbieri, 2025 Harker); one
    more (2026 Harker) prints a typed $200 expenditure total but its itemized row is field-glued
    concatenated text, so it is left to vision. Everything else is handwritten -> deferred.

Anti-fabrication: a filing whose totals are handwritten/garbled/blank returns stated=None (both
sides UNKNOWN) and zero rows — an honest "awaiting vision" state, NEVER a guessed or template-
default zero. The vision re-transcription (build_finance.py `rows_override_fn`, cache
`vision/<docid>.json`) supplies the real rows and is judged by the SAME printed-total reconcile.

TWO REGIMES (recorded on `filing_regime`, sourced from index.csv, carried through build_finance):
  * annual         — the mandatory March-1 "Annual Campaign Finance Statement" every sitting
                     official files every year (50 filings). A PARALLEL stream — NEVER summed
                     into a race/cycle total.
  * election_cycle — the during-a-race Primary/Pre-General/Final disclosures (21 filings, 2021 &
                     2023). ONLY these feed cycle_totals; each report is PER-PERIOD ("excluding
                     those previously reported") -> is_incremental=True -> a cycle total SUMS a
                     candidate's election-cycle reports (dedup via cycle_totals.py; not run here).

parse(text, meta) -> the standard family dict (contrib_rows, expend_rows, stated_*, notes).
"""
from __future__ import annotations

import re

import common
from common import ContribRow, ExpendRow

# The numbered summary lines whose right-hand value cell we inspect, plus the section "TOTAL"
# lines. The value is always the far-right cell; labels contain "$50"/"$500" thresholds which we
# never confuse for a value because we only classify the tail to the RIGHT of the matched label.
_L_CONTRIB = re.compile(r"total contributions as of this report", re.I)
_L_EXPEND = re.compile(r"total expenditures\s+or obligations|total expenditures\s+made", re.I)
# The SECTION total lines print "TOTAL" in ALL CAPS ("TOTAL $0.00"); the numbered summary labels
# use sentence-case "Total contributions ...". Match ONLY the all-caps section total (no re.I) so
# a summary label is never mistaken for a total line.
_L_TOTAL = re.compile(r"\bTOTAL\b")
_COLGAP = re.compile(r"\s{6,}")   # the form's label->value column gap (>=6 spaces)


def _value_cell(line: str) -> str:
    """The form is laid out `<label>   <gap>   <value>`; the value sits to the RIGHT of the first
    wide (>=6-space) column gap. Return that right-hand value cell verbatim ("" if none). This
    isolates the value from the label so a threshold like "$50" inside a label is never read as a
    value, and an accounting-zero "$      -" (wide internal gap) is preserved whole. Leading
    indentation is stripped first so an indented "   TOTAL $ -" splits after the label, not before."""
    s = line.lstrip()
    m = _COLGAP.search(s)
    return s[m.end():].strip() if m else ""


def _classify_cell(cell: str):
    """Classify a value cell. Returns (kind, value):
      ('empty', None)  — blank AcroForm cell (filer entered nothing)
      ('zero',  0.0)   — the accounting-zero the fillable template renders for $0 ("$   -" / "-")
      ('money', float) — a cleanly-typed dollar cell ("$0.00", "$200.00", "$ 1,234.56")
      ('dirty', None)  — a non-empty cell that is NOT clean typed money = handwriting/OCR garble
                         (e.g. "c747.", "23 a b. 3D", a bare "786.12" with no $) -> defer to vision
    """
    s = cell.strip()
    if s == "":
        return ("empty", None)
    # accounting-zero: an optional $ then a lone dash (Excel/AcroForm renders $0 as "-")
    if re.fullmatch(r"\$?\s*-\s*", s):
        return ("zero", 0.0)
    # cleanly-typed money: optional $, digits/commas, optional 2-dp cents, nothing else
    m = re.fullmatch(r"\$?\s*([\d,]+(?:\.\d{2})?)", s)
    if m:
        v = common.parse_money("$" + m.group(1))
        return ("money", v) if v is not None else ("dirty", None)
    return ("dirty", None)


def parse(text: str, meta: dict) -> dict:
    lines = text.splitlines()

    # Collect the classified value cell for each inspected line, in document order.
    total_cells = []          # section "TOTAL $x" cells, in order (1st ~ contributions, last ~ expend)
    l4_cell = None            # summary line 4 (total contributions) — fallback
    l5_cell = None            # summary line 5 (total expenditures) — fallback
    any_dirty = False

    for ln in lines:
        for lab, sink in ((_L_CONTRIB, "l4"), (_L_EXPEND, "l5")):
            if lab.search(ln):
                kind, val = _classify_cell(_value_cell(ln))
                if kind == "dirty":
                    any_dirty = True
                if sink == "l4":
                    l4_cell = (kind, val)
                else:
                    l5_cell = (kind, val)
        if _L_TOTAL.search(ln):                # all-caps section-total line ("TOTAL $x")
            kind, val = _classify_cell(_value_cell(ln))
            if kind == "dirty":
                any_dirty = True
            if kind in ("zero", "money"):
                total_cells.append(val)

    # A filing is TEXT-parseable only when NOTHING on it is dirty (no handwriting/garble). Any
    # dirty cell => the real numbers are handwritten => stated UNKNOWN, awaiting vision.
    if any_dirty:
        return dict(contrib_rows=[], expend_rows=[], stated_contrib=None,
                    stated_expend=None, stated_begin=None, stated_end=None,
                    notes="handwritten/garbled totals — awaiting vision")

    # No dirty cells. Derive stated_contrib / stated_expend from the section TOTALs (1st = the
    # ITEMIZED CONTRIBUTIONS total; last = the expenditures total), falling back to the numbered
    # summary lines. A side we still cannot read cleanly stays None (never fabricate a zero).
    def _cell_val(cell):
        return cell[1] if (cell and cell[0] in ("zero", "money")) else None

    stated_contrib = total_cells[0] if total_cells else _cell_val(l4_cell)
    stated_expend = total_cells[-1] if len(total_cells) >= 2 else (
        total_cells[0] if (len(total_cells) == 1 and l4_cell is None) else _cell_val(l5_cell))
    # when exactly one TOTAL cell was found, it is the contributions total; use l5 for expend
    if len(total_cells) == 1:
        stated_contrib = total_cells[0]
        stated_expend = _cell_val(l5_cell)

    notes = ""
    if stated_contrib is None and stated_expend is None:
        notes = "no readable typed totals — awaiting vision"
    elif stated_contrib is None or stated_expend is None:
        notes = "one side typed, other blank — partial (awaiting vision)"

    # TEXT mode never itemizes rows: in this corpus every cleanly-typed filing is all-zeros (no
    # rows), and the one typed non-zero form (2026 Harker $200) has a field-glued concatenated
    # itemized line that cannot be split deterministically -> it stays totals-only here and is
    # captured by vision. So we emit stated totals + zero rows; the driver reconciles all-zeros
    # (0 == 0) as clean, and a typed-total-with-no-rows as honest "totals-only(no itemization)".
    return dict(contrib_rows=[], expend_rows=[], stated_contrib=stated_contrib,
                stated_expend=stated_expend, stated_begin=None, stated_end=None, notes=notes)
