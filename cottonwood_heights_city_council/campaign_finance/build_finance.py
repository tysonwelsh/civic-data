#!/usr/bin/env python3
"""build_finance.py — Cottonwood Heights City driver for the structured campaign-finance layer.

Vision-cache-consumed city (2026-07-17 wave; family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference implementation = midvale). Cottonwood
Heights' filings are Utah Code §10-3-208 municipal C&E forms: the 2025 city filings and the
2021/2023 state scans are consumed from `vision/<sha1(index_path)[:8]>.json` (30 caches:
2021 ×7, 2023 ×5, 2025 ×18), fed through the shared driver's normalization + reconciliation.

Filings with NO cache flow through as honest inventory-only rows (unknown totals, dated
reason, low confidence — acquired != transcribed, never guessed). Three honest reasons:
  * 2017/2019 below-2020-floor BONUS acquisitions (16 rows) — inventory-only by the midvale
    convention (kept in scope, never transcribed).
  * 2021/2023 `format=text` filings whose COVER totals are handwritten/garbled in the text
    layer (Schwartz, Wiechers/Weichers, Kim, Evans, Hanson, Newell, Rawlings, McShaffrey,
    Walker, Hallbeck, Birrell-final, Hyland) — their typed itemized tables carry real money;
    a vision tranche is the honest follow-up (see AVAILABILITY.md), NOT dropped-as-zero.
    The three CLEAN typed reports the owner flagged (Cottam, Holton, Kraan) ARE vision-cached.
  * 2025 `statement` (initial financial disclosure) + `conflict_of_interest` — NOT C&E
    reports (no contributions/expenditures); EXCLUDED by in_scope_fn, not inventory rows.

STRUCTURAL NOTES (Cottonwood Heights):
  * 4-district council + a VOTING Mayor — the Mayor is a candidate/person like any member.
  * DUPLICATE (`index.csv` `duplicate_of`): Prazen 2025 "final-dec-4" (`df89b7c3`) is a
    byte-distinct re-upload of his Oct-28 interim (`4779b80c`) — page-identical scan, same
    totals. Honored here: the dup row carries a `superseded (duplicate re-upload…)` note so
    it never sums, and Prazen's cycle total is fixed to his Oct-28 interim via
    `cycle_overrides.csv` (his GENUINE Dec-4 final is an acquisition gap — not on file).
  * PER-CANDIDATE REGIME (the midvale lesson): `vision_lib.detect_regimes` classifies each
    candidate-cycle cumulative vs incremental from the caches; decisions PRINTED below —
    eyeball them. CH 2025 filers restate cumulative snapshots (Bennion 86->100->106);
    correct a mis-shaped cycle via `cycle_overrides.csv`, never by editing caches/CSVs.

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
        filing_regime="",           # CH files election-cycle C&E only (no annual regime)
    )


def _in_scope(ix):
    """C&E reports only. Exclude the 2025 candidacy-era financial disclosure STATEMENTS and
    all conflict-of-interest forms (no contributions/expenditures — not C&E). The 2017/2019/
    2023 `statement`-typed rows ARE pre-primary C&E reports (Bracken 2023 is even cached) and
    stay in scope."""
    ft = (ix.get("filing_type") or "").strip()
    if ft == "conflict_of_interest":
        return False
    if ft == "statement" and (ix.get("election_year") or "").strip() == "2025":
        return False
    return True


def _no_cache_note(ix):
    yr = (ix.get("election_year") or "").strip()
    if yr in ("2017", "2019"):
        return ("not transcribed (below-2020-floor bonus acquisition; scan/handwritten §10-3-208 "
                "template — inventory-only, vision deferred 2026-07-18)")
    return ("not transcribed (format=text but cover totals are handwritten/garbled in the text "
            "layer; typed itemization carries real money — vision-tranche follow-up deferred "
            "2026-07-18, see AVAILABILITY.md)")


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
        res = vision_lib.build_result(cache, meta, FAMILY)
        dup = (ix.get("duplicate_of") or "").strip()
        if dup:
            # Honor index.csv duplicate_of: a byte-distinct re-upload of an earlier filing
            # (Prazen 2025 dec-4 == his oct-28 interim scan). Keep the transcribed rows for
            # the inventory, but flag SUPERSEDED so it never enters a cycle sum; the genuine
            # later report is an acquisition gap (documented in cycle_overrides.csv).
            note = (f"superseded (duplicate re-upload of {dup}; identical scan/totals — the "
                    f"genuine later report is not on file, an acquisition gap)")
            res["notes"] = (res.get("notes", "") + "; " + note) if res.get("notes") else note
        return res

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=_in_scope,
        reconcile_cash_only=False,        # CH cover TOTAL includes in-kind at face value (see AVAILABILITY)
        dedup_mode=_mode_of,              # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()
                                        + (ix.get("reporting_period", "") or "").lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
