#!/usr/bin/env python3
"""build_finance.py — Town of Copperton driver for the structured campaign-finance layer.

Vision-cache-consumed city (2026-07-17 wave; family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference impl = midvale). Copperton is a tiny
~800-pop metro-township→town; its campaign-finance record is **19 scanned SLCo-Clerk
candidate disclosures 2016–2021** (township era; below the repo's 2017 floor for the 5
founding-2016 filings, but the founders overlap the later roster so they are IN as full
history — the midvale below-floor-inventory convention does not apply because these DO
have caches). Every one of the 19 scanned filings is consumed from
`vision/<sha1(index_path)[:8]>.json` (Read-tool transcription, $0 API), fed through the
shared driver's normalization + reconciliation. The **6 COI rows are OUT OF SCOPE**
(conflict-of-interest statements, Utah Code 10-3-1301 — no dollar figures) and are
excluded by `in_scope_fn`; the 5 born-digital `format=text` rows are all COIs (verified —
no campaign-finance text filing exists), so no text sidecar is ever parsed.

TINY-TOWN SHAPE (honest, not a build failure): most filings are $50 filing-fee-only or
$0-activity summary pages. The only substantive itemizations are **Ron Patrick 2016**
($381.97, 4 contrib / 2 expend incl. a Vista Print sign order) and **Kathleen Bailey 2019
Oct** ($428.40, 1 contrib / 7 expend). Expect a high totals-only / zero count and a
low both-sides-reconcile rate — that is the true shape of the record.

VERBATIM QUIRKS captured, never corrected: Baxter-2016 struck-through ending balance =
null; Severson-2021 Dec blank this-period totals = null; Column-B YTD figures were
deliberately NOT captured in the caches (per-period Column A only).

PER-CANDIDATE REGIME: detected per candidate-cycle (`vision_lib.detect_regimes`) and
passed to the driver as a callable dedup_mode. Copperton has no cumulative restatement
chains (the two multi-filing candidates — Bailey 2019, Stitzer 2019 — file disjoint
per-period reports, so all cycles resolve to `incremental`). Decisions are printed —
eyeball them; correct a mis-shaped cycle via `cycle_overrides.csv` (cycle_totals.py),
never by editing caches or CSVs.

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


def _in_scope(ix):
    # COI (conflict-of-interest) statements carry no dollar figures — out of scope (6 rows).
    return (ix.get("filing_type") or "").strip() != "coi_disclosure"


def _meta(ix):
    return dict(
        candidate=ix["candidate"].strip(),
        office=(ix.get("office") or "").strip(),
        seat="",                       # Copperton seats are AT-LARGE — no district key
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",              # single regime: election-cycle C&E only (COIs excluded)
    )


def _no_cache_note(ix):
    # Never reached for in-scope rows: all 19 scanned CF filings HAVE a vision cache
    # (verified). Kept honest in case a future acquisition adds an un-transcribed filing.
    return ("not transcribed (no vision cache; acquisition-only — vision deferred, "
            "see AVAILABILITY.md)")


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
        in_scope_fn=_in_scope,            # exclude the 6 COI rows (no dollars)
        reconcile_cash_only=False,        # no in-kind rows anywhere in Copperton (moot); cover totals as-is
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
