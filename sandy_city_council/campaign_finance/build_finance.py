#!/usr/bin/env python3
"""build_finance.py — Sandy driver for the structured campaign-finance layer (F2, OCR mode).

Thin dispatcher: selects the `easyvote_schedab` family via the shared framework driver and
writes contributions.csv / expenditures.csv / filing_totals.csv from index.csv + text/*.txt.

Sandy is the **OCR twin** of West Jordan's born-digital F2 EasyVote work — the SAME "Report of
Contributions and Expenditures" form (Summary Page + Schedule A/B), but the portal only serves a
flattened, redacted PDF render, so every filing is `format=scanned` and read via tesseract OCR.
The family's OCR-tolerance mode (currency-glyph repair, date-sanity, reconcile against the
cleaner Summary Page total) is engaged automatically because `is_scanned_fn` returns True — no
separate parser, no fork.

SCOPE — every one of the 83 filings is an in-scope campaign C&E report (Sandy files no annual
financial / conflict-of-interest statements through EasyVote; its "Annual" reports ARE the
year-end C&E summaries, filing_type=summary). So there is nothing to exclude.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import driver  # noqa: E402
import vision_lib  # noqa: E402
import common  # noqa: E402
from common import ContribRow, ExpendRow, parse_date  # noqa: E402

VISION_DIR = HERE / "vision"


def _vmoney(x):
    """Parse a vision-transcribed amount string to float, or None (never guessed)."""
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: if a filing has a cached Claude-vision transcription, build its rows
    from that (extract_method .../vision) INSTEAD of the OCR sidecar, so the vision output is
    reconciled by the same printed-total test. Returns None for filings with no vision cache."""
    # cache filename = the repo-standard key sha1(index path)[:8] (2026-07-19
    # migration; document_id keeps the city's native doc id for provenance —
    # the two are now decoupled).
    cache = VISION_DIR / f"{vision_lib.cache_key(meta['source_filing'])}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    vm = meta["extract_method"].split("/")[0] + "/vision"

    def _date(s):
        return parse_date(str(s)) or "" if s not in (None, "", "null") else ""

    crows = []
    for i, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for i, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_vmoney(d.get("total_contributions")),
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=_vmoney(d.get("beginning_balance")),
                stated_end=_vmoney(d.get("ending_balance")),
                notes="vision-transcribed(claude-sonnet-5)")


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _office_seat(ix):
    """Sandy index office ∈ {Mayor, Council At-Large, Council District N} -> (office, seat)
    matching the born-digital WJ convention (office ∈ Mayor/Council; seat carries the seat)."""
    o = (ix.get("office") or "").strip()
    if o.lower().startswith("mayor"):
        return "Mayor", ""
    seat = re.sub(r"^Council\s*", "", o).strip()   # "District 2" / "At-Large"
    return "Council", seat


def _meta(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    m = re.search(r"([0-9A-F]{8})$", stem)
    did8 = m.group(1) if m else (ix.get("document_id", "")[:8])
    office, seat = _office_seat(ix)
    return dict(
        candidate=ix["candidate"], office=office, seat=seat,
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        # REGRESSION FIX (2026-07-20): the index column was renamed report_period ->
        # reporting_period after this build was written; the stale key read "" for every
        # filing, which collapsed each candidate-cycle into ONE dedup group (65 false
        # 'superseded by amendment/re-file' notes vs the 12 documented in CLAUDE.md) and
        # made cycle_totals take only the LAST filing's Column A (e.g. Stroud 2023 0/0
        # vs her printed YTD $970/$970). Read the current name, tolerate the old one.
        document_id=did8,
        reporting_period=ix.get("reporting_period", "") or ix.get("report_period", ""))


# amendment detection: the EasyVote checkbox OCRs unreliably, so key off the filer's own report
# label / filename — incl. the observed "amedned" tesseract typo — like WJ's amend_fn.
_AMEND = re.compile(r"amend|amedned", re.I)


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="easyvote_schedab",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: ix.get("format", "").strip().lower() == "scanned",
        in_scope_fn=lambda ix: True,        # all 83 are campaign C&E reports
        reconcile_cash_only=True,           # EasyVote states cash totals excluding in-kind
        dedup_mode="incremental",           # Column A is per-period; sum periods, amendment supersedes
        amend_fn=lambda ix: bool(_AMEND.search(
            ((ix.get("reporting_period", "") or ix.get("report_period", "")) + " "
             + ix.get("title", "") + " "
             + os.path.basename(ix.get("path", ""))))),
        rows_override_fn=_vision_result,     # vision re-transcription for OCR-unreconciled filings
        derive_incremental=True)             # EMPIRICAL per-candidate is_incremental (2026-07-20)
                                             # — replaces the per-city constant where row-overlap
                                             # evidence shows a filer is cumulative; no-evidence
                                             # candidates keep the constant (row-metadata only)
