#!/usr/bin/env python3
"""build_finance.py — South Jordan driver for the structured campaign-finance layer.

South Jordan posts its campaign Contribution & Expenditure reports directly on sjc.utah.gov
(CivicPlus DocumentCenter), on a SOUTH-JORDAN-SPECIFIC "Campaign Financial Disclosure Report —
Report of Contributions and Expenditures, Section 1.12.050 of the South Jordan City Municipal
Code" form — a NEW family, `southjordan_form` (EasyVote-like Column A/B summary + Schedule A/B
itemization; see the family module for the structure). NOT the utah_standard_form, NOT EasyVote.

DEDUP — South Jordan is INCREMENTAL (`is_incremental=True`): Column A is "Total this Period" and
Schedule A/B itemize only that period (verified on Johnson 2023 5329), so a cycle total is the SUM
of the period reports' Column-A figures and the final report's Column B / Year-to-Date is the
cross-check. An amendment / re-file of the same period supersedes the original (marked in
filing_totals.notes, kept never dropped) — e.g. Hughes 2025 8609 "Amended Pre-General 28 Day".

SCOPE — the 3 flagged superseded 2023 uploads (ids 5135 / 5148 / 5149, `note`="superseded
upload") are re-uploads of a pre-general report already present under a live id; they are EXCLUDED
here so a cycle sum never double-counts them (never deleted from the acquisition index).

FORMAT REALITY (re-characterized per filing 2026-07-06, NOT trusting the index `format` labels):
only Johnson 2023 5329 renders its Schedule A/B itemization to `pdftotext` text (reconciles
$4,565 contributions / $5,213.02 expenditures). The 2025 fillable filings keep filled Summary
numbers recoverable but attach itemization as a scanned/re-encoded image `pdftotext` cannot read;
every other filing is a photographed/handwritten scan whose text sidecar is empty. Those reconcile
as totals-only / needs_review until Claude-vision transcribes their Schedule A/B via the
`cf-vision-transcribe` skill -> `vision/<sha1(path)[:8]>.json`, fed back through the SAME Column-A
reconciliation by the driver `rows_override_fn`. A figure that will not reconcile stays blank +
needs_review + low — never guessed.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import driver   # noqa: E402
import common   # noqa: E402
from common import ContribRow, ExpendRow, parse_date   # noqa: E402

VISION_DIR = HERE / "vision"


def _hash8(ix):
    """Stable vision-cache key: first 8 hex of sha1(index path). Vision transcriptions write
    vision/<hash8>.json; this build consumes them. (index.csv carries no sha256/document_id.)"""
    return hashlib.sha1(ix["path"].encode("utf-8")).hexdigest()[:8]


def _doc_id(ix):
    """City-stable filing id: the CivicPlus DocumentCenter View id from source_url, else the
    filename stem (2019 Wayback filings have no numeric id)."""
    m = re.search(r"/View/(\d+)", ix.get("source_url", "") or "")
    return m.group(1) if m else os.path.splitext(os.path.basename(ix["path"]))[0]


def _office_seat(ix):
    o = (ix.get("office") or "").strip()
    seat = (ix.get("district") or "").strip()
    if o.lower().startswith("mayor"):
        return "Mayor", ""
    return "Council", (f"District {seat}" if seat else "")


def _meta(ix):
    office, seat = _office_seat(ix)
    return dict(
        candidate=ix["candidate"], office=office, seat=seat,
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_doc_id(ix), reporting_period=ix.get("filing_period", ""))


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _superseded(ix):
    return ("superseded" in (ix.get("path", "") or "").lower()
            or "superseded upload" in (ix.get("note", "") or "").lower())


_AMEND = re.compile(r"amend|revis|updated", re.I)


def _is_amend(ix):
    return bool(_AMEND.search(ix.get("filing_period", "") + " " + ix.get("title", "")
                              + " " + os.path.basename(ix.get("path", ""))))


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME Column-A reconciliation as the text rows. total_contributions /
    total_expenditures in the cache are the Summary Page Column A "Total this Period" figures (the
    incremental anchor); *_ytd are the Column B cross-check. Returns None when no cache exists."""
    cache = VISION_DIR / f"{_hash8(ix)}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    vm = meta["extract_method"].split("/")[0] + "/vision"

    def _date(s):
        return (parse_date(str(s)) or "") if s not in (None, "", "null") else ""

    crows = []
    for i, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(),
            donor_city=(r.get("city") or "").strip(), donor_state=(r.get("state") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))),
            is_incremental="True", source_filing=meta["source_filing"],
            document_id=meta["document_id"], line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for i, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or r.get("payee") or r.get("name") or "").strip(),
            purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))),
            is_incremental="True", source_filing=meta["source_filing"],
            document_id=meta["document_id"], line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    notes = ["vision-transcribed(claude-code/read)"]

    def _basis(rows, colA, colB, side):
        """Pick the printed anchor the itemization actually reconciles to (both are the form's own
        figures): Column A 'Total this Period' (is_incremental=True) or, when the schedule listed
        the whole cycle, Column B 'Year-to-Date' (is_incremental=False). Neither -> default to
        Column A + flag (honest mismatch, e.g. an internally inconsistent source total). Never
        fabricates a figure; only chooses which stated total to reconcile the transcribed rows to."""
        s = round(sum(v for v in (_vmoney(r.amount) for r in rows) if v is not None), 2)
        if colA is not None and abs(s - colA) <= 0.01:
            return colA, "True", None
        if colB is not None and abs(s - colB) <= 0.01 and (colA is None or abs(colA - colB) > 0.01):
            return colB, "False", (f"{side} itemization reconciles to Column B Year-to-Date "
                                   f"${colB:,.2f} (cumulative snapshot; is_incremental=False)")
        return colA, "True", None

    stated_c, inc_c, note_c = _basis(crows, _vmoney(d.get("total_contributions")),
                                     _vmoney(d.get("total_contributions_ytd")), "contributions")
    stated_e, inc_e, note_e = _basis(erows, _vmoney(d.get("total_expenditures")),
                                     _vmoney(d.get("total_expenditures_ytd")), "expenditures")
    for r in crows:
        r.is_incremental = inc_c
    for r in erows:
        r.is_incremental = inc_e
    for lbl, key in (("YTD contributions", "total_contributions_ytd"),
                     ("YTD expenditures", "total_expenditures_ytd")):
        v = _vmoney(d.get(key))
        if v is not None:
            notes.append(f"{lbl} (Column B) stated ${v:,.2f}")
    notes += [n for n in (note_c, note_e) if n]
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_c, stated_expend=stated_e,
                stated_begin=None, stated_end=None, notes="; ".join(notes))


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="southjordan_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: ix.get("format", "").strip().lower() == "scanned",
        in_scope_fn=lambda ix: not _superseded(ix),   # drop the 3 superseded 2023 re-uploads
        reconcile_cash_only=False,   # in-kind folded into the printed Total Contributions -> sum all
        dedup_mode="incremental",    # Column A = this period; sum the cycle, amendment supersedes
        amend_fn=_is_amend,
        rows_override_fn=_vision_result)
