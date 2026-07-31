#!/usr/bin/env python3
"""build_finance.py — White City driver for the structured campaign-finance layer.

VISION-CACHE city (2026-07-17 wave; family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference impl = midvale). White City's ONLY
campaign-finance cycle is 2025 (its first city-era election under HB35): 6 candidates ×
3 reports = 18 Utah Code §10-3-208 C&E money reports, plus 10 conflict-of-interest ethics
forms (out of scope — a separate statutory instrument). All 18 money reports are consumed
from `vision/<sha1(index_path)[:8]>.json` caches, fed through the shared driver's
normalization + reconciliation.

CACHE PROVENANCE (18 caches, all 2025):
  * 10 pre-staged (2026-07-17 /cf-vision-transcribe) for the fully-SCANNED reports.
  * 8 added at STRUCTURING time (2026-07-17) for the reports the pre-stage skipped because
    index.format=="text": 7 are born-digital text transcribed via `pdftotext -layout`
    (Flint ×3 [cumulative], Cardenaz Oct-7 [the $1050 incl. the $400 Shelton gift],
    Cardenaz Dec-4 Final [under-filled], Denning Oct-28 [zeros], Denning Dec-4 Final
    [$978.73 self-funded printing, Schedule-A column quirk]); 1 (Perry Oct-28) has a
    born-digital COVER but IMAGE Schedule pages -> read via Read-tool page images.
    Rationale: those born-digital/imaged schedules carry REAL, cleanly-legible money
    (mayoral runner-up Flint's $3550; Cardenaz's $1050) that the ROLLOUT's cardinal rule
    (alta precedent: "do NOT leave that money out") forbids dropping. NO row is injected
    into a blank SCANNED schedule (the "do not inject" landmine is honored: the $400
    Shelton gift and the $978 Denning printing are recorded ONLY on the filed pages that
    actually itemize them — Cardenaz Oct-7, Denning Dec-4 — never fabricated into the
    blank-cover scanned filings).

PER-CANDIDATE REGIME (the midvale lesson): filers mix styles even within this one cycle —
Flint restates a cumulative snapshot on all three reports (latest wins); Perry files
disjoint PER-PERIOD reports (Oct-7 $7705.50 -> Oct-28 $10 -> Dec-4 $62.90; sum them);
Mahoney/Price/Cardenaz put real money on Oct-7, then Oct-28 zeros + a restated/under-filled
Final. `vision_lib.detect_regimes` decides per candidate-cycle (printed below — eyeball
them). Two candidate-cycles need documented `cycle_overrides.csv` rows (Perry: per-period
filer whose Dec Final is itself a period; Cardenaz: under-filled Final).

THREE blank-schedule-over-nonzero-cover SCANNED filings (Mahoney Final $1543.03, Cardenaz
Oct-28 $1050/$859.78, Price Final $695.82) reconcile as totals-only UNKNOWN by design —
never fabricated rows.

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

# Perry Oct-28: index.format=="text" (born-digital cover) but its Schedule pages are image
# scans -> vision-read, so it is treated as SCANNED for confidence tiering (medium, not high).
_IMAGE_SCHEDULE_TEXT = {"raw/2025_perry_cf_10-28.pdf"}


def _meta(ix):
    return dict(
        candidate=ix["candidate"].strip(),
        office=(ix.get("office") or "").strip(),
        seat="",                     # White City is ALL AT-LARGE (no district)
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",            # single regime — 2025 election-cycle C&E only
    )


def _in_scope(ix):
    # Money reports only; the 10 conflict-of-interest ethics forms are a separate statute.
    return (ix.get("filing_type") or "").strip() != "coi_disclosure"


def _is_scanned(ix):
    return (ix.get("format") or "") == "scanned" or ix["path"] in _IMAGE_SCHEDULE_TEXT


def _no_cache_note(ix):
    # Safety net only: every in-scope 2025 money report HAS a cache, so this is not reached
    # in a normal build. If a new cycle's reports arrive uncached, they flow through honest.
    return ("not transcribed (no vision cache; run /cf-vision-transcribe for this filing "
            "before structuring — see campaign_finance/CLAUDE.md)")


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = [r for r in csv.DictReader(fh) if _in_scope(r)]

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
        # TRUTHFUL extract_method (2026-07-19): the 7 born-digital reports transcribed via
        # pdftotext -layout (docstring item 2; each cache's _meta.transcription_note says
        # "born-digital text") are labeled `/text`, not `/vision`. Perry Oct-28
        # (_IMAGE_SCHEDULE_TEXT) stays `/vision` — its Schedule pages were Read-tool
        # page-image transcriptions despite index.format=="text".
        mode = ("text" if (ix.get("format") or "") == "text"
                and ix["path"] not in _IMAGE_SCHEDULE_TEXT else "vision")
        return vision_lib.build_result(cache, meta, FAMILY, mode=mode)

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=_is_scanned,
        in_scope_fn=_in_scope,
        reconcile_cash_only=False,     # no in-kind rows in any White City filing (Schedule C empty)
        dedup_mode=_mode_of,           # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
