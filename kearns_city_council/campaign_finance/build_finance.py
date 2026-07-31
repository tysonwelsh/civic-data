#!/usr/bin/env python3
"""build_finance.py — Kearns (metro township → city) driver for the structured
campaign-finance layer.

Follows the 2026-07-17 vision-cache reference implementation (midvale; family
`vision_cache`, shared helpers `scripts/campaign_finance/vision_lib.py`). Kearns's
retrievable finance record is the pre-EasyVote metro-township era ONLY — 38 scanned,
redacted Salt Lake County Clerk candidate C&E disclosures, 2016–2021 (township-era CF
was acquired IN SCOPE for this full-history, data-floor-2017 entity: the 2016 founding
cycle and 2017 filers overlap the later roster and are retained as valid context per
campaign_finance/CLAUDE.md). Every one is an image scan whose `pdftotext` yields 0
chars, so ALL are consumed from `vision/<sha1(index_path)[:8]>.json` (transcribed via
the Read tool, $0 Anthropic API) and fed through the shared driver's normalization +
reconciliation. There are NO not-transcribed rows: every one of the 38 index rows has a
cache (the `empty_result` path below is a safety net only).

THE TWO LATER CYCLES ARE ACQUISITION GAPS, NOT ROWS. 2023 (still a metro township,
moved to the county's reCAPTCHA/auth-gated EasyVote SPA) and 2025 (first city era,
kearns.utah.gov Cloudflare-blocked; Longtin's two filings PROVEN to exist via a Wayback
landing page) yielded ZERO retrievable filings and therefore have NO index rows and NO
filing_totals rows. They live honestly in `unrecovered.csv` + AVAILABILITY.md, so cycle
coverage of this layer is 2016–2021 only — never read absence of 2023/2025 rows here as
"nobody filed."

PER-CANDIDATE REGIME (the midvale lesson): filers MIX styles, so the regime is detected
PER candidate-cycle (`vision_lib.detect_regimes`: row-subset ⊂ evidence, cover
restatement, stated-sequence monotonicity) and passed to the driver as a callable
dedup_mode. Kearns's township filings are tiny (many ≤$500 totals-only forms), so most
candidate-cycles are single-filing (default incremental — a group of one is unaffected).
The decisions are printed below — eyeball them; correct a mis-shaped cycle via
`cycle_overrides.csv` (cycle_totals.py), never by editing caches or CSVs.

IN-KIND: verified included in the printed cover TOTAL at face value (Perry 2016 June:
2500 + 150 + 100 + 130 in-kind = 2880 = printed total) → `reconcile_cash_only=False`,
like midvale. Filer/transcription mismatches (e.g. Richards 2019 interim expenditures)
stay flagged verbatim, never adjusted.

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
        seat="",                    # kearns index has no district column; office carries "Seat/District N"
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",           # township C&E only (no annual/COI regime in this layer)
    )


def _no_cache_note(ix):
    # Safety net only: every one of the 38 in-scope index rows HAS a vision cache
    # (verified). If a future refresh adds a row before its cache, this records the
    # honest reason rather than a silent drop.
    return ("not transcribed (no vision cache; scanned SLCo Clerk disclosure — queue a "
            "/cf-vision-transcribe pass, see campaign_finance/CLAUDE.md)")


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
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",  # all 38 scanned
        in_scope_fn=lambda ix: True,      # all 38 index rows are candidate C&E disclosures (no COI set)
        reconcile_cash_only=False,        # cover totals observed to include in-kind at face value (Perry 2016)
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
