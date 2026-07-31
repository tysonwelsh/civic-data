#!/usr/bin/env python3
"""build_finance.py — Bluffdale City driver for the structured campaign-finance layer.

Sibling of the midvale reference implementation (family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py` + `driver.py`). Bluffdale's municipal C&E
filings are scans or fillable Utah Code §10-3-208 templates transcribed to
`vision/<sha1(index_path)[:8]>.json` caches by /cf-vision-transcribe. This thin driver
feeds every cache through the shared normalization + reconciliation + per-candidate
regime detection.

TWO bluffdale-specific adaptations vs midvale (handled in _adapt_cache, city-local —
the shared scripts/ are read-only and unchanged):

1. CACHE SHAPE. Bluffdale's wave-2 caches nest the printed totals under
   `totals_printed:{total_contributions,total_expenditures[,total_in_kind]}` (the
   /cf-vision-transcribe wave-2 schema) rather than midvale's top-level
   `total_contributions`/`total_expenditures`. `_adapt_cache` hoists them so
   `vision_lib.build_result` + `detect_regimes` see the stated covers. Never edits a
   cache file.

2. THE PAVLAKIS 2025-10-07 BUNDLE (`a800473e.json`, `reports:[...]`). The one multi-report
   PDF staples an AMENDED re-file of the Pre-General report ahead of the ORIGINAL of the
   SAME period (identical $7,665.70 / $7,312.88 covers; the amendment only renames some
   anonymous donors to named ones). Concatenating both (vision_lib's default reports[]
   path — its Column-A restatement rule does NOT fire here, the labels are not "Column A")
   would double-count 21 contributions + 11 expenditures. `_adapt_cache` collapses the
   bundle to the AMENDED sub-report (it supersedes the original) as a single-report cache;
   the supersession is noted on the filing row. Verified: the amended report reconciles
   both sides exactly against its cover.

CANDIDATE-NAME CANONICALIZATION (`_CANON`). The acquisition index carries a few filer-name
spellings that split ONE person's cycle across two `candidate` values, all confirmed the
same person by `matched_election_candidate`: Eric/Erik Swanson, Greg/Gregory Wilding,
Steven/Steve Austin (2023); Allen/Albert Allen Larsen, Jeff/Jeffrey Steele (2025). Each is
folded to the OTHER spelling that already exists in index.csv for that (name, year), so the
validator's (candidate,election_year)∈index check still passes and cycle_totals groups the
person's filings as one cycle. index.csv itself is never edited.

THE 3 IN-FLOOR 2023 BORN-DIGITAL `text` FILINGS (Swanson 5969, Flynn 5971, Wilding 5996)
were transcribed from their clean pdftotext layer into caches (a720a221 / b9182572 /
ec057535) during this build: Swanson & Flynn are post-primary "no new activity" reports
($0 schedules; their primary money lives in their Aug caches); Wilding's Oct-24 Pre-General
carries REAL money ($5,100 cash + $20 in-kind / $3,046.38) and is part of his cumulative
chain. The 2017+2019 (49) below-floor filings stay honest inventory-only rows.

PER-CANDIDATE REGIME (the midvale lesson): filers mix styles. 2023 is dominated by
cumulative restatement chains (each report restates cycle-to-date; latest wins, earlier
superseded — e.g. Wilding 4,500→5,100→6,097.33→6,397.33), while 2025 is dominated by
per-period filers (Aug/Oct/Dec disjoint; sum them) whose Dec "summary"-typed filing is
itself a period report — corrected via documented `cycle_overrides.csv` rows (the midvale
precedent), never by editing caches or CSVs. `detect_regimes` prints its decisions — eyeball
them.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv /
donor_aliases.csv / cycle_overrides.csv.

    python3 build_finance.py
"""
from __future__ import annotations

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

# minority spelling -> the spelling that already exists in index.csv for that (name, year);
# both map to one matched_election_candidate (see docstring). Keyed (raw_candidate, year).
_CANON = {
    ("Eric Swanson", "2023"): "Erik Swanson",
    ("Greg Wilding", "2023"): "Gregory Wilding",
    ("Steven Austin", "2023"): "Steve Austin",
    ("ALLEN LARSEN", "2025"): "ALBERT ALLEN LARSEN",
    ("JEFF STEELE", "2025"): "JEFFREY STEELE",
}

# NB: keep the word "supersed" OUT of this note — cycle_totals.py drops any filing whose
# notes contain "supersed", and this bundle filing (the amended Pre-General) must stay LIVE.
_PAVLAKIS_NOTE = ("multi-report bundle: kept the AMENDED Pre-General re-file, dropped the "
                  "original same-period copy in the same PDF (identical covers; the amendment "
                  "only renamed anonymous donors) to avoid double-count")


def _canon(cand, year):
    return _CANON.get((cand, year), cand)


def _adapt_cache(cache):
    """Return a NEW single-report, midvale-shape dict (top-level total_contributions/
    total_expenditures) from a bluffdale cache. Handles the Pavlakis reports[] bundle by
    keeping the amended sub-report. Never mutates the cache file. (cache is None -> None.)"""
    if cache is None:
        return None
    if "reports" in cache and cache.get("reports"):
        reps = cache["reports"]
        amended = [r for r in reps if "amend" in (r.get("label", "") or "").lower()]
        chosen = amended[0] if amended else reps[-1]
        tp = chosen.get("totals_printed") or {}
        return dict(contributions=chosen.get("contributions") or [],
                    expenditures=chosen.get("expenditures") or [],
                    total_contributions=tp.get("total_contributions"),
                    total_expenditures=tp.get("total_expenditures"))
    tp = cache.get("totals_printed") or {}
    c = dict(cache)
    c["total_contributions"] = tp.get("total_contributions")
    c["total_expenditures"] = tp.get("total_expenditures")
    return c


def _meta(ix):
    return dict(
        candidate=_canon(ix["candidate"].strip(), (ix.get("election_year") or "").strip()),
        office=(ix.get("office") or "").strip(),
        seat=(ix.get("district") or "").strip(),           # bluffdale is at-large -> blank
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=(ix.get("docid") or vision_lib.cache_key(ix["path"])).strip(),
        filing_regime="",           # bluffdale files election-cycle C&E only (no annual regime)
    )


def _no_cache_note(ix):
    if (ix.get("election_year") or "") in ("2017", "2019"):
        return ("not transcribed (below-2020-floor bonus acquisition; candidate-keyed "
                "coverage retained as inventory-only — vision deferred, see AVAILABILITY.md)")
    return "not transcribed (no vision cache — see AVAILABILITY.md)"


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    # regime pre-pass: per-candidate-cycle incremental vs cumulative, from the ADAPTED caches
    filings = []
    for ix in index_rows:
        year = (ix.get("election_year") or "").strip()
        filings.append(dict(candidate=_canon(ix["candidate"].strip(), year),
                            election_year=year,
                            filing_date=(ix.get("date") or "").strip(),
                            cache=_adapt_cache(vision_lib.load_cache(VISION_DIR, ix["path"]))))
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    def _mode_of(cand, year, members):  # driver callable dedup_mode
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental")
            == "incremental")
        raw = vision_lib.load_cache(VISION_DIR, ix["path"])
        if raw is None:
            return vision_lib.empty_result(_no_cache_note(ix))
        res = vision_lib.build_result(_adapt_cache(raw), meta, FAMILY)
        if "reports" in raw and raw.get("reports"):
            res["notes"] = (res.get("notes", "") + "; " + _PAVLAKIS_NOTE).lstrip("; ")
        return res

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=lambda ix: True,      # all 106 index rows are C&E disclosures (no COI set)
        reconcile_cash_only=False,        # covers observed to include in-kind at face value
                                          # (Pavlakis); the cash-only filers (Wilding, etc.)
                                          # reconcile via the driver's alt-convention fallback
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + (ix.get("reporting_period", "") or "").lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
