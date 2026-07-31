#!/usr/bin/env python3
"""build_finance.py — West Jordan driver for the structured campaign-finance layer (F2 + scanned).

Processes ALL non-statement (campaign C&E) filings in three GROUPS, then merges into the three
DERIVED CSVs. Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv /
donor_aliases.csv.

SCOPE — campaign C&E reports only (`filing_type in {interim, summary}`). The 53 `statement`
rows (annual financial / conflict-of-interest, Utah Code 10-3-1304 type) stay EXCLUDED.

Three groups (each its OWN driver.run so dedup/supersession is body-of-work-local):
  A. BORN-DIGITAL 43 — format=text EasyVote 2023+, family `easyvote_schedab` (text mode). This
     path is UNCHANGED from the original build and is ISOLATED in its own dedup group so its rows
     come out BYTE-IDENTICAL. (Isolation matters: several 2025 scanned filings share a candidate+
     cycle+period with a born-digital one — e.g. McConnehey's scanned "General Election Report -
     Amended" vs the born-digital "General Election Report" — and a COMBINED dedup would stamp a
     `superseded` note onto the born-digital filing, changing it. We keep born-digital canonical
     and instead mark the colliding SCANNED filing superseded, in group B below.)
  B. EASYVOTE SCANNED (2023/2025 image renders) — same `easyvote_schedab` family in OCR mode;
     WJ's scans OCR poorly (~2/30 reconcile), so nearly all escalate to the gated Claude-vision
     pass (`wj_vision_extract.py` -> vision/<doc8>.json, fed back via `rows_override_fn`). Cash-
     only reconciliation (EasyVote states totals EXCLUDING in-kind).
  C. CITY 2021 HANDWRITTEN — the West Jordan "Campaign Financial Disclosure Report" (numbered
     cover block + Attachment A/B). A distinct form the EasyVote parser cannot read, so it is
     transcribed 100% by vision. Each PDF BUNDLES 1+ full reports (interim + final); vision returns
     one entry per report and build sums the per-report stated totals (incremental periods, chained
     balances). Reconciliation is CASH-ONLY: line-4 "Total contributions" excludes in-kind (verified
     on Whitelock 2021 — her $1,750 in-kind Realtors PAC gift is not in her $1,250 line-4 total).

    python3 build_finance.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import driver  # noqa: E402
import common  # noqa: E402
from common import ContribRow, ExpendRow, parse_date  # noqa: E402

VISION_DIR = HERE / "vision"


# --------------------------------------------------------------------------- meta / helpers
def _did8(ix):
    """EasyVote -> trailing 8-hex of the filename (born-digital + scanned); city 2021 -> a stable
    sha1(path)[:8] (those filenames carry no document id). Matches wj_vision_extract._did8."""
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    m = re.search(r"([0-9A-F]{8})$", stem)
    if m:
        return m.group(1)
    return hashlib.sha1(ix["path"].encode("utf-8")).hexdigest()[:8]


def _meta(ix):
    dist = (ix.get("district") or "").strip()
    return dict(
        candidate=ix["candidate"], office=ix["office"],
        seat=(f"District {dist}" if dist and dist.isdigit() else dist),
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_did8(ix),
        reporting_period=ix.get("title", ""))


def _sidecar(ix):
    subdir = ix["path"].split("/")[1]
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{subdir}__{stem}.txt"


def _is_campaign(ix):
    return ix.get("filing_type", "").strip() in ("interim", "summary")


def _fmt(ix):
    return ix.get("format", "").strip().lower()


# ------------------------------------------------------------------------- vision overrides
def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_rows(d, meta):
    """Build ContribRow/ExpendRow lists from a cached vision transcription (shared by B and C)."""
    vm = meta["extract_method"].split("/")[0] + "/vision"

    def _date(s):
        return parse_date(str(s)) or "" if s not in (None, "", "null") else ""

    crows = []
    for i, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for i, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    return crows, erows


def _vision_result(ix, meta):
    """driver rows_override_fn: if a scanned filing has a cached vision transcription, build its
    rows from that (extract_method .../vision) INSTEAD of the OCR sidecar, reconciled by the same
    printed-total test. Returns None (-> OCR path) when no cache exists.

    TWO cache shapes, both reconciled CASH-ONLY (both forms state their contribution/expenditure
    TOTAL EXCLUDING in-kind — verified on Whitelock's 2021 form: line-4 'Total contributions' =
    $1,250 excludes her $1,750 in-kind Realtors PAC gift):
      * EasyVote (raw/easyvote/) — flat {contributions, expenditures, total_*}, one report.
      * City 2021 (raw/city/) — {reports:[…]}: each PDF BUNDLES 1+ full reports (an interim + a
        final, each a whole form). Rows are concatenated across reports and the stated totals are
        SUMMED in code (the form is incremental: each period excludes previously-reported activity,
        and consecutive reports' balances chain). The <=$50 aggregate (line 2) is UNITEMIZED — it
        is recorded in the note, never synthesized as a donor row. stated_contrib per report = line
        4 (Total contributions as of this report)."""
    cache = VISION_DIR / f"{meta['document_id']}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    is_city = meta["source_filing"].startswith("raw/city/")

    if "reports" in d:                                   # city multi-report bundle (future re-vision)
        reports = d.get("reports") or []
        crows, erows = [], []
        for rep in reports:
            cr, er = _vision_rows(rep, meta)
            crows.extend(cr)
            erows.extend(er)
        for i, r in enumerate(crows):
            r.line_no = f"v{i + 1}"
        for i, r in enumerate(erows):
            r.line_no = f"v{i + 1}"

        def _sum(field):
            vals = [_vmoney(rep.get(field)) for rep in reports]
            vals = [v for v in vals if v is not None]
            return round(sum(vals), 2) if vals else None

        agg = _sum("contributions_50_or_less")
        notes = "vision-transcribed(claude-sonnet-5)"
        if len(reports) > 1:
            notes += f"; bundle of {len(reports)} reports summed (incremental periods)"
        if agg:
            notes += f"; unitemized <=$50 aggregate stated ${agg:.2f} (not itemized on form)"
        return dict(contrib_rows=crows, expend_rows=erows,
                    stated_contrib=_sum("total_contributions"),
                    stated_expend=_sum("total_expenditures"),
                    stated_begin=None, stated_end=None, notes=notes)

    crows, erows = _vision_rows(d, meta)                  # flat single-report cache
    notes = ("vision-transcribed(claude-sonnet-5, recovered from first-pass)"
             if d.get("_recovered") else "vision-transcribed(claude-sonnet-5)")

    if is_city:
        # HONEST INCOMPLETENESS: the 2021 city PDFs BUNDLE multiple full reports (interim + final).
        # The recovered first-pass transcription captured only ONE report per bundle (the source
        # JSON was lost and API credit was exhausted before a multi-report re-transcription). Detect
        # the true report count from the OCR sidecar ("Balance carried forward from last report"
        # prints once per report); when the bundle holds more reports than were captured, the filing
        # is a KNOWN UNDERCOUNT -> flag every row needs_review and say so. Never presented as clean.
        try:
            n_reports = _sidecar(ix).read_text(errors="replace").count(
                "Balance carried forward from last report")
        except OSError:
            n_reports = 1
        if n_reports > 1:
            notes += (f"; PARTIAL: multi-report bundle ({n_reports} reports on form) — vision "
                      f"captured 1; UNDERCOUNT, multi-report re-transcription queued (TODO)")
            for r in crows + erows:
                r.needs_review = "1"

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_vmoney(d.get("total_contributions")),
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=_vmoney(d.get("beginning_balance")),
                stated_end=_vmoney(d.get("ending_balance")),
                notes=notes)


# --------------------------------------------------------------------------- amendment rule
_AMEND = re.compile(r"amend|amedned", re.I)


def _amend_fn(ix):
    return bool(_AMEND.search(ix.get("title", "") + " " + os.path.basename(ix.get("path", ""))))


# --------------------------------------------------------------------------------- the build
def _run_group(index_rows, in_scope_fn, is_scanned_fn, reconcile_cash_only):
    """One isolated driver.run over the given predicate; returns its result dict."""
    return driver.run(
        here=HERE, family_id="easyvote_schedab",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=is_scanned_fn,
        in_scope_fn=in_scope_fn,
        reconcile_cash_only=reconcile_cash_only,
        dedup_mode="incremental",
        amend_fn=_amend_fn,
        rows_override_fn=_vision_result)


def _write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(common.row_to_dict(r))


def main():
    index_rows = list(csv.DictReader(open(HERE / "index.csv", newline="", encoding="utf-8")))

    def group_a(ix):   # born-digital 43 — UNCHANGED, isolated
        return _is_campaign(ix) and _fmt(ix) == "text"

    def group_b(ix):   # EasyVote scanned 2023/2025
        return _is_campaign(ix) and _fmt(ix) == "scanned" and ix["path"].startswith("raw/easyvote/")

    def group_c(ix):   # city 2021 handwritten
        return _is_campaign(ix) and _fmt(ix) == "scanned" and ix["path"].startswith("raw/city/")

    print("=== GROUP A: born-digital EasyVote (text) — isolated, must stay byte-identical ===")
    res_a = _run_group(index_rows, group_a, is_scanned_fn=lambda ix: False,
                       reconcile_cash_only=True)
    print("\n=== GROUP B: EasyVote SCANNED (OCR + vision), cash-only ===")
    res_b = _run_group(index_rows, group_b, is_scanned_fn=lambda ix: True,
                       reconcile_cash_only=True)
    print("\n=== GROUP C: CITY 2021 handwritten (vision), cash-only (stated totals exclude in-kind) ===")
    res_c = _run_group(index_rows, group_c, is_scanned_fn=lambda ix: True,
                       reconcile_cash_only=True)

    # ---- cross-group supersession: a SCANNED filing sharing a born-digital filing's (candidate,
    # cycle, base-period) is subordinated to the born-digital canonical one (higher fidelity than
    # an OCR/vision scan) and marked superseded, so a cycle-total query does not double-count. The
    # born-digital note is NEVER touched (kept byte-identical); only the scanned side is annotated.
    bd_periods = {(ft.candidate, ft.election_year, driver._base_period(ft.reporting_period))
                  for ft in res_a["totals"]}
    n_cross = 0
    for ft in res_b["totals"]:
        key = (ft.candidate, ft.election_year, driver._base_period(ft.reporting_period))
        if key in bd_periods:
            msg = "superseded (born-digital filing covers same reporting period; born-digital canonical)"
            ft.notes = (ft.notes + "; " + msg) if ft.notes else msg
            n_cross += 1

    contrib = res_a["contrib"] + res_b["contrib"] + res_c["contrib"]
    expend = res_a["expend"] + res_b["expend"] + res_c["expend"]
    totals = res_a["totals"] + res_b["totals"] + res_c["totals"]

    # ---- EMPIRICAL per-candidate is_incremental (2026-07-20, the TODO follow-up):
    # the "True" the family stamps is the EasyVote Column-A form design, but several WJ
    # filers demonstrably fill Column A CYCLE-TO-DATE (re-listing prior schedules —
    # page-verified: Rulon Green 2023 General ColA=ColB=$2,605.82 re-lists the 28-Day;
    # Pack 2025 Post-Primary ColA $8,822.32 re-lists the primary; Whitelock 2025 28-Day
    # ColA equals its own full itemization incl. the re-listed primary rows; Whitelock
    # 2021 Final-Amended restates her earlier bundle). Run on the MERGED results (not
    # per-group) because a candidate's reports span born-digital + scanned groups (Pack).
    # Row-metadata only — filing_totals/cycle figures are untouched here; the three
    # page-proven cycle-figure corrections go through cycle_overrides.csv.
    print("\n=== EMPIRICAL is_incremental (per candidate-cycle, merged groups) ===")
    driver.derive_is_incremental(totals, contrib, expend)

    _write(HERE / "contributions.csv", common.CONTRIB_HEADER, contrib)
    _write(HERE / "expenditures.csv", common.EXPEND_HEADER, expend)
    _write(HERE / "filing_totals.csv", common.TOTALS_HEADER, totals)

    print(f"\n=== MERGED: contributions {len(contrib)} | expenditures {len(expend)} | "
          f"filing_totals {len(totals)} | cross-group superseded scanned: {n_cross} ===")


if __name__ == "__main__":
    main()
