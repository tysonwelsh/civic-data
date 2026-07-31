#!/usr/bin/env python3
"""build_finance.py — Holladay City driver for the structured campaign-finance layer.

Vision-cache-consumed city (2026-07-17 cf-structuring wave; family `vision_cache`, shared
helpers `scripts/campaign_finance/vision_lib.py`). Holladay files Utah's "FINANCIAL
DECLARATION OF CANDIDATE" form (cover lines 1-4 = Form-A total / $50-or-less aggregate /
Form-B total / ending balance). Money is consumed from `vision/<sha1(index_path)[:8]>.json`
caches — pure sha1 keying (NEVER trailing-hex: `bradley-10282025.pdf` and
`fotheringham10282025.pdf` both end in hex "10282025" and would collide under the West
Jordan `_did8` shortcut; documented in CLAUDE.md).

36 caches feed this build:
  * 24 SCANNED in-scope C&E filings (2021 x5, 2023 x7, 2025 x12) — vision-transcribed
    (Read tool) in the two 2026-07-17 tranches.
  * 12 BORN-DIGITAL `format=text` C&E filings (2021 Brewer x2, 2025 Sundwall/Bilstad/Jones
    x8, Watts Oct-7, Wilson Final) — these carry a REAL text layer with REAL money (unlike
    midvale's junk-text templates), so they were transcribed from the authoritative
    born-digital `pdftotext -layout` at the 2026-07-17 cf-structuring step and cached too.
    Leaving them inventory-only would drop real money — the rollout forbids that.

Filings with NO cache flow through as honest inventory-only rows (unknown totals, dated
reason, low confidence):
  * the 4 below-2020-floor 2017 bonus scans (Petersen, Roach, Fotheringham-primary,
    Dahle-Aug) — kept IN as inventory (the midvale convention), never guessed.
The 12 Conflict-of-Interest (COI) ethics disclosures are OUT of scope (officeholder
disclosures, not C&E reports) — excluded by `in_scope_fn`, not campaign filings.

PER-CANDIDATE REGIME: Holladay 2025 council filers (Sundwall/Bilstad/Jones) file PER-PERIOD
reports (the balance chain proves it: each period's stated total is that period only, and a
year-end "Final" is itself just another period, NOT a cumulative summary), while some 2023
filers restate cumulative snapshots. A single city-wide dedup_mode would mis-mark someone,
so the regime is detected PER candidate-cycle (`vision_lib.detect_regimes`) and passed to the
driver as a callable; the decisions are PRINTED below — eyeball them, and correct a mis-shaped
cycle via `cycle_overrides.csv` (cycle_totals.py), never by editing caches or CSVs.

IN-KIND: the Holladay cover total (Form-A line 1) is CASH-ONLY — Gray 2023's $3,000 in-kind
(Russ Gray, Design Services) is excluded from her printed 9,297.00 cover (verified: cash-only
itemized 9,582 - 285 $50-or-less aggregate = 9,297 exactly). So `reconcile_cash_only=True`.

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
        filing_regime="",           # Holladay files election-cycle C&E only (no annual regime)
    )


def _in_scope(ix):
    # The 12 Conflict-of-Interest ethics disclosures are officeholder disclosures, NOT
    # campaign C&E reports — excluded from the money layer (documented in AVAILABILITY.md).
    return (ix.get("filing_type") or "").strip() != "coi_disclosure"


def _no_cache_note(ix):
    if ix.get("election_year") in ("2017",):
        return ("not transcribed (below-2020-floor 2017 bonus acquisition; scanned state "
                "declaration form — inventory-only, cf-structuring 2026-07-17)")
    return ("not transcribed (no vision cache; see AVAILABILITY.md — cf-structuring "
            "2026-07-17)")


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    # regime pre-pass: per-candidate-cycle incremental vs cumulative, from the caches
    # (COI rows are excluded so they never perturb a candidate-cycle's regime).
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
        in_scope_fn=_in_scope,             # exclude the 12 COI ethics disclosures
        reconcile_cash_only=True,          # Holladay cover total is CASH-ONLY (Gray in-kind excluded)
        dedup_mode=_mode_of,               # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
