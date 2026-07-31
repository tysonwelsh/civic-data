#!/usr/bin/env python3
"""build_finance.py — Emigration Canyon driver for the structured campaign-finance layer.

Vision-cache-consumed build (family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference impl = midvale). Emigration Canyon is a
Salt Lake County metro township (2017–2024) → CITY (2024, HB35), full-history entity: the
township-era filings (2016 founding cohort + 2017 @LRG + 2019 cycle) are IN SCOPE alongside
the 2025 city-primary reports. All 30 in-scope Contribution & Expenditure filings are consumed
from `vision/<sha1(index_path)[:8]>.json`:
  - 29 scanned SLCo/city forms transcribed via /cf-vision-transcribe (Read-tool, $0 API);
  - 1 born-digital-TEXT filing (Pinon 2025) transcribed from its pdftotext layer into the same
    cache schema (fbe3c5ba.json) — format=text so it earns HIGH confidence on reconcile.

THE RECORD IS DOMINATED BY $50 FILING-FEE-ONLY, SELF-FUNDED FILINGS (and outright zero-activity
reports) — that is the honest shape of a ~1,600-pop canyon, not a build failure. Only ~15
itemized contributions + ~15 expenditures exist across all 30. Source quirks are preserved
VERBATIM, never corrected: Brems 2016 prints a $662.11 cover over items summing to $562.11 (a
$100 filer arithmetic error — flagged, not adjusted); 2019 Harris/Hawkes carry negative (−$50)
ending balances; 2019 Tippets Dec is a cover-page-only PDF (all nulls). The Bowen 2016 November
PDF is a TWO-REPORT bundle (June 21 + November 1 stapled) — re-visioned into the reports[]
schema so the June sub-report's $55 is not lost.

The 5 conflict-of-interest (10-3-1301/1313) forms are OUT OF SCOPE (not C&E reports; no dollars).

PER-CANDIDATE REGIME: `vision_lib.detect_regimes` decides cumulative vs incremental per
candidate-cycle from the caches; the decisions are PRINTED — eyeball them. Correct a mis-shaped
cycle via `cycle_overrides.csv` (cycle_totals.py), never by editing caches or CSVs. Regenerate,
never hand-edit the CSVs.

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
        seat="",                       # Emigration seats are ALL at-large (no district key)
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",             # election-cycle C&E only (COI is excluded, not a 2nd regime)
    )


def _in_scope(ix):
    # Exclude the 5 conflict-of-interest disclosures (10-3-1301/1313) — not C&E reports, no
    # dollar figures. Everything else (26 township 2016/2017/2019 + 4 city 2025) is a genuine
    # Report of Contributions & Expenditures. Township-era 2016 stays in: this is a
    # full-history entity (data floor 2017, but the 2016 founding cohort is retained context).
    return (ix.get("filing_type") or "").strip() != "coi_disclosure"


def _no_cache_note(ix):
    # Defensive only: every in-scope filing currently HAS a cache (29 scanned + Bowen bundle +
    # Pinon born-digital text). If a future refresh adds an untranscribed filing this fires.
    yr = ix.get("election_year") or ""
    if yr == "2023":
        return ("not transcribed (2023 metro-township cycle is EasyVote-portal-blocked — "
                "HTTP-500/auth-gated; acquisition gap, see unrecovered.csv)")
    return ("not transcribed (no vision cache; queue /cf-vision-transcribe — "
            "see AVAILABILITY.md, 2026-07-17)")


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = [ix for ix in csv.DictReader(fh) if _in_scope(ix)]

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
        # TRUTHFUL extract_method (2026-07-19): the ONE born-digital money report was
        # transcribed from its text layer, not page images — its cache _meta records
        # "Transcribed ... from the BORN-DIGITAL TEXT layer (pdftotext -layout, not a
        # scan)". Label it /text; every other cache is a Read-tool vision transcription.
        mode = ("text" if ix["path"] == "raw/city_electioninfo_robert-pinon.pdf"
                else "vision")
        return vision_lib.build_result(cache, meta, FAMILY, mode=mode)

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=_in_scope,            # exclude the 5 COI disclosures
        reconcile_cash_only=False,        # no in-kind rows anywhere; cover-total convention moot
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
