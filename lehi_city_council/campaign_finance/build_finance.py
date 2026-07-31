#!/usr/bin/env python3
"""build_finance.py — Lehi driver for the structured campaign-finance layer (F5).

Thin dispatcher: selects the `lehi_formab` family via the shared framework driver and writes
contributions.csv / expenditures.csv / filing_totals.csv from index.csv + text/*.txt.

Regenerate, never hand-edit the CSVs. Corrections go in finance_overrides.csv /
donor_aliases.csv (documented, verified vs the raw PDF), then re-run this.

    python3 build_finance.py

PREREQUISITE: text/ sidecars must exist — run `python3 backfill_text.py` first (born-digital
-> pdftotext, image-only -> tesseract) and regenerate index.csv via `python3 build_index.py`
so `format`/`extraction_method` are honest per file.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import driver  # noqa: E402


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _meta(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return dict(
        candidate=ix["candidate"], office=ix["office"], seat="",  # Lehi is at-large
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=stem, reporting_period=ix.get("report_period", ""))


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="lehi_formab",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: ix.get("format", "").strip().lower() == "scanned",
        reconcile_cash_only=True,   # Lehi "Total Contributions" is CASH; in-kind stated apart
                                    # (variant 1 has no in-kind, so cash-only == all there)
        dedup_mode="cumulative",    # each report restates cycle-to-date; latest = cycle total
        amend_fn=lambda ix: ix.get("amended", "").strip().lower() == "yes")
