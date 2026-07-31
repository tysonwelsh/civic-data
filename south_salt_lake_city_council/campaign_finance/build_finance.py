#!/usr/bin/env python3
"""build_finance.py — South Salt Lake City driver for the structured campaign-finance layer.

VISION-CACHE city (2026-07-17 CF-structuring wave; family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py`). SSL's 53 in-scope election-cycle C&E filings are
consumed from `vision/<sha1(index_path)[:8]>.json`:
  * 40 SCANNED filings (2021 x9 / 2023 x15 / 2025 x16) — transcribed in the 2026-07-17
    tranche pass (`format=scanned` -> medium confidence);
  * 13 BORN-DIGITAL TEXT filings (2023 x5 / 2025 x8) whose text layer is UNSTABLE for a
    deterministic grammar (handwritten summary pages, `SEE ATTACHED` scanned itemization,
    an AcroForm mayor filing, per-candidate custom spreadsheets) — Read-tool
    vision-transcribed 2026-07-17-CF-structuring into caches so their real money is NOT
    dropped (the alta precedent), `format=text` -> high confidence.

OUT OF SCOPE (excluded by in_scope_fn, no filing_totals row): the 8 FY2026 Conflict-of-
Interest disclosures (`filing_type=coi_disclosure`) and the 7 2026 council-vacancy
appointment filings (blank `election_year`) — neither is a campaign C&E report.

SSL FORM = INCREMENTAL Utah 10-3-208 form: Column A "Total this Period" + Column B
"Year to Date"; itemization is this-period only. Each cache stores Column A as
`total_*` (so the this-period itemized rows reconcile) and the balance chain. A cycle
total is therefore the SUM of Column A across a candidate's reports (= the final report's
printed Column B YTD). BUT some filers RESTATE cumulatively (Sanchez 2023: each report
re-lists all donors-to-date -> stated totals non-decreasing), so the regime is detected
PER candidate-cycle (`vision_lib.detect_regimes`, decisions printed) and passed to the
driver as a callable dedup_mode. The Dec year-end "summary"-typed reports are frequently
themselves per-period (often $0 this period) rather than cumulative-to-date, so the
generic cycle_totals summary-latest rule mis-reads several candidate-cycles -> corrected
with documented `cycle_overrides.csv` rows (each citing the printed final YTD as evidence;
the YTD-not-sum discipline). Regenerate, never hand-edit the CSVs.

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
        filing_regime="",           # SSL files election-cycle C&E only (no annual regime)
    )


def _in_scope(ix):
    # C&E disclosures only: drop the 8 FY2026 COI forms and the 7 2026 council-vacancy
    # appointment filings (blank election_year) — neither is a campaign C&E report.
    if (ix.get("filing_type") or "").strip() == "coi_disclosure":
        return False
    if not (ix.get("election_year") or "").strip():
        return False
    return True


def _no_cache_note(ix):
    # Every in-scope SSL filing has a vision cache; this is a defensive honest-gap note.
    return ("not transcribed (no vision cache found for an in-scope filing — regenerate "
            "vision/ per campaign_finance/CLAUDE.md 2026-07-17-CF-structuring)")


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    # regime pre-pass: per-candidate-cycle incremental vs cumulative, from the caches
    filings = []
    for ix in index_rows:
        if not _in_scope(ix):
            continue
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
        in_scope_fn=_in_scope,
        reconcile_cash_only=False,        # cover totals include in-kind at face value (verified: Karzen 2025)
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
