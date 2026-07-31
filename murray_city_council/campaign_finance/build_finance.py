#!/usr/bin/env python3
"""build_finance.py — Murray City driver for the structured campaign-finance layer.

Vision-cache wave (2026-07-17; family `vision_cache`, shared `scripts/campaign_finance/
vision_lib.py`). Murray's filings come in TWO transcribable forms, both consumed here:

  1. SCANNED filings (image PDFs / an image-based .docx) -> `vision/<sha1(path)[:8]>.json`
     (63 caches: 2025 ×27, 2023 ×16, 2021 ×20; incl. the Evans docx `577872d2`), read via
     `/cf-vision-transcribe`. Consumed by `vision_lib.build_result` (extract_method /vision).
  2. BORN-DIGITAL `format=text` filings -> `text_cache/<sha1(path)[:8]>.json` (30 in-scope
     2021/2023/2025 filings). UNLIKE midvale, Murray's text layer carries REAL money
     (Ben Peck 2025 Pre-Primary = $5,700 / $4,002.81 verified), so those are parsed from the
     authoritative born-digital text (pdftotext / openpyxl) — NOT left out — and consumed by
     `murray_text.build_text_result` (extract_method /text, so they read born-digital).

Filings with NO cache flow through as honest inventory-only rows (unknown totals, dated
reason, low confidence): the 2017 (16) + 2019 (21) BELOW-2020-FLOOR cycles (midvale
convention — acquired ≠ transcribed, kept as inventory). The Jim Brass 2023 Candidacy
Withdrawal Affidavit (docid 14399) is a NON-finance instrument and is excluded in-scope.

REGIME: single campaign-finance regime — every Murray filing is an ELECTION-CYCLE C&E
report (interim / summary; report types are Pre-Primary / Pre-General / Year-end /
Post-Primary). Murray publishes NO mandatory annual financial statement in this dataset
(its Utah-Code conflict-of-interest statements live on the separate /2123 page, out of
scope), so `filing_regime` is "" for all and there is no annual-vs-election split.
Per-CANDIDATE cumulative-vs-incremental dedup is detected from the caches
(`vision_lib.detect_regimes`; decisions printed — eyeball them) and corrected only via
documented `cycle_overrides.csv` (cycle_totals.py).

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
sys.path.insert(0, str(HERE))

import csv  # noqa: E402

import driver  # noqa: E402
import vision_lib  # noqa: E402
import murray_text  # noqa: E402

VISION_DIR = HERE / "vision"
TEXT_DIR = HERE / "text_cache"
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
        filing_regime="",          # single regime: all filings are election-cycle C&E reports
    )


def _cache_for(ix):
    """Return ('vision', cache) | ('text', cache) | (None, None) for a filing. A scanned
    filing keys into vision/; a born-digital format=text filing keys into text_cache/."""
    vc = vision_lib.load_cache(VISION_DIR, ix["path"])
    if vc is not None:
        return "vision", vc
    tc = murray_text.load_text_cache(TEXT_DIR, ix["path"])
    if tc is not None:
        return "text", tc
    return None, None


def _no_cache_note(ix):
    yr = (ix.get("election_year") or "").strip()
    if yr in ("2017", "2019"):
        return ("not transcribed (below-2020-floor bonus acquisition; inventory-only per "
                "the midvale convention — 2026-07-17)")
    return ("not transcribed (no vision/text cache; unexpected — see AVAILABILITY.md, "
            "2026-07-17)")


def _in_scope(ix):
    # Exclude the Jim Brass 2023 Candidacy Withdrawal Affidavit (docid 14399, blank
    # filing_type) — it is NOT a C&E finance statement (his Final report 14400 IS in scope).
    if (ix.get("docid") or "").strip() == "14399":
        return False
    return True


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    # regime pre-pass: per-candidate-cycle incremental vs cumulative, from BOTH cache kinds
    filings = []
    for ix in index_rows:
        if not _in_scope(ix):
            continue
        _, cache = _cache_for(ix)
        filings.append(dict(candidate=ix["candidate"].strip(),
                            election_year=(ix.get("election_year") or "").strip(),
                            filing_date=(ix.get("date") or "").strip(),
                            cache=cache))
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    def _mode_of(cand, year, members):  # driver callable dedup_mode
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental")
            == "incremental")
        kind, cache = _cache_for(ix)
        if kind == "vision":
            return vision_lib.build_result(cache, meta, FAMILY)
        if kind == "text":
            return murray_text.build_text_result(cache, meta, FAMILY)
        return vision_lib.empty_result(_no_cache_note(ix))

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=_in_scope,
        reconcile_cash_only=True,          # cover "Total Contributions (Schedule A)" EXCLUDES
                                           # Schedule C in-kind (separate schedule/total)
        dedup_mode=_mode_of,               # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()
                                        + (ix.get("note", "") or "").lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
