#!/usr/bin/env python3
"""build_finance.py — Magna City driver for the structured campaign-finance layer.

A clone of the midvale REFERENCE implementation (2026-07-17 vision-cache wave; family
`vision_cache`, shared helpers `scripts/campaign_finance/vision_lib.py`). Magna's filings
are Salt Lake County "_redacted" scans (township 2016-2021) and city-site scans/born-digital
handwriting templates (2025), so every TRANSCRIBED filing is consumed from
`vision/<sha1(index_path)[:8]>.json`. Everything else flows through as an honest
inventory-only row (unknown totals + a dated reason), because acquired != transcribed and we
never guess.

2026-07-19 — GENERAL-BUNDLE PER-CANDIDATE EXPANSION
---------------------------------------------------
The three 2025 city BUNDLE artifacts (one PDF = several candidates' 10-3-208 reports stapled
back-to-back) are transcribed to a single `reports:[...]` vision cache each (one sub-report
per candidate, verbatim covers + balance chain). Because one artifact = one acquisition-index
row but each report is a distinct candidate's FILING, this build EXPANDS every bundle row into
one synthetic per-candidate filing before it hits the shared engine: the expanded index (with
the real canonical candidate + office + the sub-report period) is written to the scratchpad and
handed to `driver.run(index_name=<abs path>)`, so the bundle's money reconciles + dedups
per-candidate exactly like a standalone filing. The acquisition `index.csv` keeps ONE artifact
row per bundle; the ONLY exception is a candidate whose filing exists solely inside a bundle
(Brooks Jones) — he gets a MEMBERSHIP row pointing at the same bundle path so his expanded
filing clears validate_finance's (candidate,election_year)-in-index gate, and `_expand`
de-dups same-path bundle rows so the bundle is still expanded exactly once. Only the derived
CSVs gain the per-candidate rows.
  * bundles = the 2 Oct general finalists' reports (v642 oct-07, v643 oct-28) + the
    primary-eliminated closing bundle (v644). Cache keys 489b0ca5 / 8586d25d / 0a3cfc7e.
  * `candidate_canonical`/`office` come from each sub-report (agent-mapped to the exact
    index.csv candidate string); a sub-report with a null canonical is SKIPPED + logged
    (never fabricated into a filing that would fail validate_finance). This guard still
    protects any FUTURE unmapped sub-report. Brooks Jones (2025 D4, primary-eliminated) WAS
    the null-canonical case: he filed no standalone PDF, so his v644 sub-report had no index
    candidate to map to. Resolved 2026-07-19 — a membership row for "Brooks Jones" was added
    to index.csv (same bundle artifact) and his cache canonical set to "Brooks Jones", so he
    now auto-structures from the cache ($958.44 self-funded, both sides reconcile) like every
    other bundle candidate.
  * document_id = sha1(bundle_path | canonical) — unique per candidate within the bundle.
  * These forms carry cumulative "Column A/C" summary columns; the caches transcribe the
    PRINTED cover verbatim (so Sudbury's oct-07 cover restates his primary Column-A total and
    Olsen's oct-28 Schedule A cumulatively restates the whole cycle) — those column quirks
    surface as honest reconcile FLAGS in filing_totals, never edits. The correct WHOLE-CYCLE
    raised/spent (which the generic dedup cannot derive from the mixed columns) is set from
    each candidate's own BALANCE CHAIN via `cycle_overrides.csv` (Adriano / Sudbury / Romero),
    with per-candidate evidence.

MAGNA FORM QUIRK vs midvale: the county/city C&E covers state TOTAL CONTRIBUTIONS/EXPENDITURES
**EXCLUDING in-kind** (in-kind is a separate "In-Kind and Other Nonmonetary" line), verified
on Romero (Becky Romero $680 in-kind → cash-sum $1,258.80 == cover) and Olsen (Cheryl Harding
$300 in-kind → cash-sum == cover ±$2). So this build reconciles CASH ROWS ONLY
(`reconcile_cash_only=True`), unlike midvale (False).

PER-CANDIDATE REGIME (`vision_lib.detect_regimes`, printed below — eyeball it) is applied
across the EXPANDED filing set, so a finalist's primary + oct-07 + oct-28 reports group as one
candidate-cycle.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv /
donor_aliases.csv / cycle_overrides.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import csv  # noqa: E402

import driver  # noqa: E402
import vision_lib  # noqa: E402

VISION_DIR = HERE / "vision"
FAMILY = "vision_cache"

_THRESHOLD_RE = re.compile(r"(?i)less than|more than|greater than|no more than|under \$|up to")


def _is_bundle(ix):
    return "bundle" in os.path.basename(ix.get("path", "")).lower()


def _bundle_reports(path):
    cache = vision_lib.load_cache(VISION_DIR, path)
    return (cache or {}).get("reports") or []


def _sub_report(ix):
    """For an expanded bundle sub-row, return its single-report cache dict (the matching
    sub-report of the bundle's reports[] cache); None if not found."""
    printed = ix.get("_bundle_printed")
    canon = ix.get("candidate", "").strip()
    for rep in _bundle_reports(ix["path"]):
        if (rep.get("candidate_canonical") or "").strip() == canon and \
                (rep.get("candidate") or "") == printed:
            return rep
    return None


def _filing_cache(ix):
    """The single-report cache dict backing THIS (possibly expanded) filing — a bundle
    sub-report for a bundle sub-row, else the row's own vision cache."""
    if ix.get("_bundle_printed"):
        return _sub_report(ix)
    return vision_lib.load_cache(VISION_DIR, ix["path"])


def _meta(ix):
    sub = ix.get("_bundle_printed") or None
    doc = vision_lib.cache_key(ix["path"], sub) if sub else vision_lib.cache_key(ix["path"])
    return dict(
        candidate=ix["candidate"].strip(),
        office=(ix.get("office") or "").strip(),
        seat="",  # magna index has no seat/district column — office carries "District N"
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=doc,
        filing_regime="",           # magna files election-cycle C&E only (no annual regime)
    )


def _no_cache_note(ix):
    y = (ix.get("election_year") or "").strip()
    fmt = (ix.get("format") or "").strip()
    base = os.path.basename(ix["path"]).lower()
    if "bundle" in base:
        return ("not transcribed (bundle sub-report cache missing — inventory-only; see "
                "AVAILABILITY.md)")
    if "white" in base and fmt == "text":
        return ("not transcribed (2025 single-candidate born-digital report; machine-readable "
                "cover = $20 contrib / $0 expend but not vision-transcribed this tranche — "
                "structuring follow-up, see AVAILABILITY.md)")
    if fmt == "text":
        return ("not transcribed (born-digital TEMPLATE text layer only — pdftotext yields "
                "handwriting-glyph junk, not machine-readable figures; real money present — "
                "vision deferred 2026-07-18 follow-up, see AVAILABILITY.md)")
    if y == "2016":
        return ("not transcribed (2016 founding-cycle township scan, below the 2017 data floor; "
                "not cached in the 2026-07-17 vision tranche — inventory-only)")
    if y in ("2017", "2019"):
        return ("not transcribed (2017/2019 township scan; deliberately not cached in the "
                "2026-07-17 vision tranche — inventory-only)")
    return "not transcribed (no vision cache — inventory-only; see AVAILABILITY.md)"


def _expand(index_rows):
    """Split every bundle row into one synthetic per-candidate row (canonical candidate +
    office + sub-report period), dropping the original bundle row. Non-bundle rows pass
    through unchanged. Returns (expanded_rows, skipped) where skipped = [(path, printed_name)]
    for null-canonical sub-reports (no acquisition-index row -> not structured)."""
    out, skipped = [], []
    for ix in index_rows:
        if not _is_bundle(ix):
            out.append(dict(ix))
            continue
        # A bundle PATH can carry TWO kinds of index row: the canonical ARTIFACT row (candidate
        # = a "...(bundle)" label) and a per-candidate MEMBERSHIP stub (a real candidate name,
        # e.g. "Brooks Jones"). The stub exists only so a candidate whose filing lives solely
        # inside the bundle clears validate_finance's (candidate,election_year)-in-index gate —
        # the gate other bundle candidates meet via their standalone primary rows. Only the
        # ARTIFACT row drives expansion; the stub is skipped (its candidate is already produced
        # from the bundle's reports[] cache). Keying expansion on the artifact row — not on
        # whichever same-path row appears first — keeps the expanded ordering (hence the
        # per-candidate regime + supersession marking) identical to the pre-stub build.
        if "bundle" not in ix.get("candidate", "").lower():
            continue
        base = os.path.basename(ix["path"]).lower()
        tag = ("general-oct07" if "oct07" in base else
               "general-oct28" if "oct28" in base else
               "primary-eliminated" if "primary-eliminated" in base else "bundle")
        for rep in _bundle_reports(ix["path"]):
            canon = (rep.get("candidate_canonical") or "").strip()
            printed = rep.get("candidate") or ""
            if not canon:
                skipped.append((ix["path"], printed))
                continue
            row = dict(ix)
            row["candidate"] = canon
            row["office"] = (rep.get("office") or ix.get("office") or "").strip()
            # A bundle-scoped period label. The scanned sub-reports often print NO period
            # (null), and the incremental supersession pass groups by (candidate, base_period)
            # — so two distinct bundle reports with a blank period would falsely collide and
            # one would supersede the other (dropping real money). A per-bundle tag keeps the
            # oct-07 vs oct-28 vs primary-eliminated periods distinct.
            row["reporting_period"] = (rep.get("reporting_period") or "").strip() or f"2025 {tag}"
            row["format"] = rep.get("format") or ix.get("format") or ""
            row["_bundle_printed"] = printed
            out.append(row)
    return out, skipped


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    expanded, skipped = _expand(index_rows)
    for path, printed in skipped:
        print(f"BUNDLE SUB-REPORT SKIPPED (null canonical — no acquisition-index row): "
              f"{printed!r} in {path} — transcribed verbatim in cache, NOT structured "
              f"(documented follow-up)")

    # write a TEMP expanded index (bundles split per candidate) the shared engine will read —
    # a portable temp file, NEVER the tracked dataset dir (the acquisition index.csv is
    # authoritative and untouched); cleaned up after the build.
    cols = []
    for r in expanded:
        for k in r:
            if k not in cols:
                cols.append(k)
    fd, expanded_index = tempfile.mkstemp(prefix="magna_cf_index_expanded_", suffix=".csv")
    os.close(fd)
    with open(expanded_index, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(expanded)

    # regime pre-pass over the EXPANDED filings (per-candidate incremental vs cumulative)
    filings = []
    for ix in expanded:
        if (ix.get("filing_type") or "").strip() == "coi_disclosure":
            continue  # COI packet is out of scope for the money layer
        filings.append(dict(candidate=ix["candidate"].strip(),
                            election_year=(ix.get("election_year") or "").strip(),
                            filing_date=(ix.get("date") or "").strip(),
                            cache=_filing_cache(ix)))
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    def _mode_of(cand, year, members):  # driver callable dedup_mode
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental")
            == "incremental")
        cache = _filing_cache(ix)
        if cache is None:
            return vision_lib.empty_result(_no_cache_note(ix))
        res = vision_lib.build_result(cache, meta, FAMILY)
        # A "Less than $1,000.00" (small-budget-certificate) cover is a THRESHOLD phrase, not a
        # dollar total. vmoney would coerce it to a number and assert money the form never
        # stated, so record that side as unknown (None) + a verbatim note. (Ramos 2021.)
        for side, key in (("stated_contrib", "total_contributions"),
                          ("stated_expend", "total_expenditures")):
            raw = str(cache.get(key) or "")
            if _THRESHOLD_RE.search(raw):
                res[side] = None
                extra = (f"{key} printed a threshold phrase ({raw!r}), not a dollar total "
                         f"— recorded as unknown")
                res["notes"] = (res.get("notes", "") + "; " + extra) if res.get("notes") else extra
        return res

    try:
        _run(expanded_index, _mode_of, _rows_override)
    finally:
        try:
            os.unlink(expanded_index)
        except OSError:
            pass


def _run(expanded_index, _mode_of, _rows_override):
    driver.run(
        here=HERE, family_id=FAMILY, index_name=str(expanded_index),
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),  # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=lambda ix: (ix.get("filing_type") or "").strip() != "coi_disclosure",
        reconcile_cash_only=True,          # magna covers state totals EXCLUDING in-kind (verified)
        dedup_mode=_mode_of,               # PER-CANDIDATE (see docstring)
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
