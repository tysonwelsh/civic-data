#!/usr/bin/env python3
"""build_finance.py — Midvale City driver for the structured campaign-finance layer.

REFERENCE IMPLEMENTATION for the vision-cache-consumed cities (2026-07-17 wave; family
`vision_cache`, shared helpers `scripts/campaign_finance/vision_lib.py`). Midvale's
filings are scans — or fillable Utah Code §10-3-208 templates whose "text" layer is
handwriting rendered as glyph junk (the taylorsville disease; verified on 3 samples) —
so EVERY transcribed filing is consumed from `vision/<sha1(index_path)[:8]>.json`
(40 caches: 2021 ×5, 2023 ×19, 2025 ×16), fed through the shared driver's normalization
+ reconciliation. Filings with NO cache (2017/2019 below-floor bonus acquisitions ×27,
plus 17 format=text rows whose text layer is junk — vision deferred, see AVAILABILITY)
flow through as honest inventory-only rows: unknown totals, a dated reason note, low
confidence — acquired ≠ transcribed, never guessed.

PER-CANDIDATE REGIME (the midvale lesson): filers MIX styles — most 2023 candidates
restate cumulative snapshots (Billings 81→88→90 rows; Feinberg totals grow; Sharp's
summary restates the interim's cover verbatim), while 2025 filers (and Hale 2021) file
per-period reports (Mikolash 2,610 → 1,125 → 400, disjoint). A single city-wide
dedup_mode would mis-mark someone, so this build detects the regime PER candidate-cycle
(`vision_lib.detect_regimes`: row-subset ⊂ evidence, cover-restatement, stated-sequence
monotonicity) and passes the decisions to the driver as a callable dedup_mode; the
decisions are printed below — eyeball them, and correct a mis-shaped cycle via
`cycle_overrides.csv` (cycle_totals.py), never by editing caches or CSVs.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv /
donor_aliases.csv / cycle_overrides.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import csv  # noqa: E402

import driver  # noqa: E402
import vision_lib  # noqa: E402

VISION_DIR = HERE / "vision"
FAMILY = "vision_cache"


def _meta(ix):
    return dict(
        candidate=ix["candidate"].strip(),
        office=(ix.get("office") or "").strip(),
        seat=(ix.get("district") or "").strip(),
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",           # midvale files election-cycle C&E only (no annual regime)
    )


def _no_cache_note(ix):
    if ix["path"].startswith("raw/state/"):
        return ("not transcribed (duplicate state-portal copy of the city-portal Dec "
                "summary, which IS transcribed — no money lost; Snow's state copy is "
                "his only Dec summary and IS cached)")
    if ix.get("election_year") in ("2017", "2019"):
        return ("not transcribed (below-2020-floor bonus acquisition; scanned/garbled "
                "template — vision deferred 2026-07-17)")
    return ("not transcribed (no vision cache; format=text but the text layer is "
            "template/scan junk — vision deferred 2026-07-17, see AVAILABILITY.md)")


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    # regime pre-pass: per-candidate-cycle incremental vs cumulative, from the caches
    filings = []
    for ix in index_rows:
        filings.append(dict(candidate=ix["candidate"].strip(),
                            election_year=(ix.get("election_year") or "").strip(),
                            filing_date=(ix.get("date") or "").strip(),
                            cache=vision_lib.load_cache(VISION_DIR, ix["path"])))
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    def _mode_of(cand, year, members):  # driver callable dedup_mode
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental")
            == "incremental")
        cache = vision_lib.load_cache(VISION_DIR, ix["path"])
        if cache is None:
            return vision_lib.empty_result(_no_cache_note(ix))
        return vision_lib.build_result(cache, meta, FAMILY)

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=lambda ix: True,      # all 84 index rows are C&E disclosures (no COI set)
        reconcile_cash_only=False,        # cover totals observed to include in-kind at face value
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
