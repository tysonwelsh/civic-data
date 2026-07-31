#!/usr/bin/env python3
"""build_finance.py — Riverton City driver for the structured campaign-finance layer.

Family `vision_cache` (shared helpers `scripts/campaign_finance/vision_lib.py`), the
midvale reference pattern. Riverton's money reports are the Utah Code 10-3-208 city C&E
form: scanned/handwritten OR born-digital-but-degraded fillable templates whose text
layer is a spacey/garbled render. EVERY transcribed money filing is therefore consumed
from `vision/<sha1(index_path)[:8]>.json` (40 caches: 2021 x3, 2023 x9, 2025 x28 — see
CLAUDE.md), fed through the shared driver's normalization + reconciliation.

RIVERTON SPECIFICS (see CLAUDE.md / AVAILABILITY.md):
  * `reconcile_cash_only=True` — the printed cover TOTAL CONTRIBUTIONS excludes Schedule C
    in-kind (in-kind is a separate line; verified on Buroker primary: 19 cash rows =
    19,950 cover, 3,550 in-kind excluded). So the itemized reconciliation sum counts CASH
    rows only.
  * PER-PERIOD FILERS. The form's Summary Page carries Columns A..E, one period per column,
    Column E = Campaign Total. Every report records its OWN incremental column as its
    stated total, so a candidate's cycle = SUM of periods (Column E). The 2025 candidates'
    'Post-Election' report is itself a period (Column D), NOT a cumulative final -> its
    filing_type is 'summary' but the cycle total lives in cycle_overrides.csv (the midvale
    precedent). The 2023 candidates' 'financial-2024' year-end summaries ARE cumulative
    bundles (their cover = Column E), so the interim+summary overlap is deduped by
    detect_regimes + cycle_totals' max(summary, sum-interims) -- each period counts once.
  * OVERLAP / DOUBLE-COUNT (2023): each candidate's 3 state interims + 1 city year-end carry
    the same periods; the year-end cover = Column E = sum of the interims, so max() -> once.
  * PIERUCCI ACQUISITION GAP (AVAILABILITY #6): raw/2023_pierucci_state_10-24-23_redacted.pdf
    is the state's mis-publication of HAYMOND's 28-Day report; no cache was written (would
    fabricate Pierucci donors). It stays in scope as an honest inventory-only row.

EXCLUDED from the money layer (in_scope_fn, named reasons): declaration_of_candidacy (12) and
conflict_of_interest (6) are not C&E money reports; the McCay 'statement' (ed1bf236) is a
byte-identical duplicate upload of her 28-Day report (same sha256) -> counted once via the
28-Day filing.

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

# Money-report slot that is an honest acquisition gap (state mis-published Haymond's report
# under Pierucci's filename -> no cache; see AVAILABILITY.md flag #6).
PIERUCCI_GAP = "raw/2023_pierucci_state_10-24-23_redacted.pdf"
# byte-identical duplicate upload of the McCay 28-Day report (same sha256).
MCCAY_STATEMENT_DUP = "raw/2025_mccay_campaign-finance-statement-10-25.pdf"

# filing_types that are not C&E money reports (excluded from the structured layer).
NON_MONEY_TYPES = {"declaration_of_candidacy", "conflict_of_interest"}

# ---------------------------------------------------------------------------
# DOCUMENTED single-value transcription-artifact correction (owner-authorized
# 2026-07-18 CF adjudication; see finance_overrides.csv + CF CLAUDE.md).
# On raw/2025_buroker_general-election-report.pdf p.2 (Schedule A) the FILER wrote
# the loan as "$3,000,00" -- a comma where the decimal point belongs. The page's
# own "SUBTOTAL FOR THIS PAGE" and "TOTAL CONTRIBUTIONS RECEIVED" both print
# $4,000.00 = $1,000 Glen Roberts + $3,000 loan, proving the printed intent is
# $3,000.00 (re-rendered + verified 2026-07-18). The cache PRESERVES the filer's
# verbatim "3,000,00" (never edited); but vision_lib.vmoney strips the comma ->
# 300000.00, a 100x phantom in this filing's itemized_contrib_sum + self_funded.
# _adapt_cache maps that ONE cache value to the printed intent at build time
# (the bluffdale _adapt_cache precedent; shared scripts/ untouched). Cycle totals
# are UNAFFECTED (cycle_totals uses the printed cover/Column E $4,000, not the
# itemized sum). Keyed by the cache's _meta.index_path so it can never touch any
# other filing.
_TYPO_FIXES = {
    "raw/2025_buroker_general-election-report.pdf": [("3,000,00", "3000.00")],
}


def _adapt_cache(cache):
    """Return the cache with the ONE documented Buroker comma-for-decimal typo
    mapped to its printed intent. Returns a NEW dict (never mutates the cache
    file); a cache with no registered fix is returned unchanged. None -> None."""
    if cache is None:
        return None
    ip = (cache.get("_meta") or {}).get("index_path")
    fixes = _TYPO_FIXES.get(ip)
    if not fixes:
        return cache
    fixmap = dict(fixes)
    c = dict(cache)
    c["contributions"] = [
        ({**r, "amount": fixmap[str(r.get("amount")).strip()]}
         if str(r.get("amount")).strip() in fixmap else r)
        for r in (cache.get("contributions") or [])
    ]
    return c


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
        filing_regime="",           # Riverton files election-cycle C&E only (no annual regime)
    )


def _in_scope(ix):
    if (ix.get("filing_type") or "").strip() in NON_MONEY_TYPES:
        return False
    if ix["path"] == MCCAY_STATEMENT_DUP:
        return False
    return True


def _no_cache_note(ix):
    if ix["path"] == PIERUCCI_GAP:
        return ("not transcribed (ACQUISITION GAP -- the state file mis-publishes Spencer "
                "Haymond's 28-Day report under Pierucci's filename; AVAILABILITY.md #6). "
                "Pierucci's real 10-24-23 28-Day report was never acquired; his cycle total "
                "is carried by his year-end summary's Column-E cover. NOT vision-transcribed "
                "(would attribute Haymond's donors to Pierucci).")
    return "not transcribed (no vision cache; investigate)"


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
                            cache=_adapt_cache(vision_lib.load_cache(VISION_DIR, ix["path"]))))
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    def _mode_of(cand, year, members):  # driver callable dedup_mode
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental")
            == "incremental")
        cache = _adapt_cache(vision_lib.load_cache(VISION_DIR, ix["path"]))
        if cache is None:
            return vision_lib.empty_result(_no_cache_note(ix))
        # TRUTHFUL extract_method (2026-07-19): each riverton cache RECORDS its own
        # transcription provenance in `_meta.method` — "text-layer transcription ..."
        # (born-digital pdftotext read, 7 caches: pierucci x3, smith/mccay/buroker 28-day,
        # buroker post) vs "read-tool-vision ..." (page-image reads; incl. the format=text
        # MISLABELED handwritten 2021 scans). Label /text only on the recorded text-layer
        # prefix; the ambiguous "text/vision" (mccay post) and everything else stay
        # /vision (conservative). NEVER inferred from index.format (proven unreliable
        # here). Label-only — parsing/reconciliation identical.
        method = str((cache.get("_meta") or {}).get("method", ""))
        mode = "text" if method.startswith("text-layer transcription") else "vision"
        return vision_lib.build_result(cache, meta, FAMILY, mode=mode)

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=_in_scope,
        reconcile_cash_only=True,         # Riverton cover TOTAL excludes Schedule C in-kind
        dedup_mode=_mode_of,              # PER-CANDIDATE regime
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
