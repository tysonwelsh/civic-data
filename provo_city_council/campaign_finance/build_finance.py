#!/usr/bin/env python3
"""build_finance.py — Provo driver for the structured campaign-finance layer (F1).

Thin dispatcher: reads index.csv + text/*.txt, runs the Provo F1 parser
(scripts/campaign_finance/families/provo_form.py), applies deterministic donor/vendor
normalization + classification, reconciles every filing's itemized sums against its printed
totals, and writes the three DERIVED CSVs (contributions / expenditures / filing_totals).

Regenerate, never hand-edit the CSVs. Corrections go in finance_overrides.csv /
donor_aliases.csv (documented, verified vs the raw PDF), then re-run this.

    python3 build_finance.py           # rebuild the 3 CSVs, print the reconciliation table
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CF_LIB = REPO_ROOT / "scripts" / "campaign_finance"
sys.path.insert(0, str(CF_LIB))
sys.path.insert(0, str(CF_LIB / "families"))

import common                     # noqa: E402
import reconcile                  # noqa: E402
import normalize_donors           # noqa: E402
import registry                   # noqa: E402

FAMILY = "provo_form"
provo_form = registry.get(FAMILY)   # select this city's parser via the shared family registry
INDEX = HERE / "index.csv"
ALIASES = HERE / "donor_aliases.csv"
OVERRIDES = HERE / "finance_overrides.csv"


def _text_path(index_path: str) -> Path:
    """index.csv `path` is raw/<file>.pdf; its sidecar is text/<file>.txt."""
    base = os.path.basename(index_path)
    stem = os.path.splitext(base)[0]
    return HERE / "text" / f"{stem}.txt"


def _filing_conf(cc: str, ce: str) -> str:
    order = {"high": 3, "medium": 2, "low": 1, "": 0}
    present = [c for c in (cc, ce) if c]
    if not present:
        return "low"
    return min(present, key=lambda c: order.get(c, 0))


def _amt(s):
    """Parse a stored decimal amount string ('500.08', '-39.85') -> float, or None."""
    if s in ("", None):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _sum(rows):
    # No rows sums to $0.00 (a genuinely empty side, e.g. a $0 filing). Scanned filings,
    # where itemization is intentionally not attempted, are handled by the caller.
    vals = [v for v in (_amt(r.amount) for r in rows) if v is not None]
    return round(sum(vals), 2)


def main():
    aliases = normalize_donors.load_aliases(str(ALIASES))
    contrib_all, expend_all, totals_all = [], [], []
    recon_report = []

    with open(INDEX, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    for ix in rows:
        is_scanned = (ix.get("format", "").strip().lower() == "scanned")
        meta = {
            "candidate": ix["candidate"], "office": ix["office"], "seat": ix.get("seat", ""),
            "election_year": ix["election_year"], "filing_date": ix["date"],
            "filing_type": ix.get("filing_type", ""), "source_filing": ix["path"],
            "document_id": ix.get("document_id", ""),
            "extract_method": f"{FAMILY}/{'ocr' if is_scanned else 'text'}",
            "is_scanned": is_scanned,
        }
        tp = _text_path(ix["path"])
        if not tp.exists():
            recon_report.append((ix["candidate"], ix["election_year"], "MISSING-TEXT"))
            continue
        text = tp.read_text(encoding="utf-8", errors="replace")
        res = provo_form.parse(text, meta)

        crows, erows = res["contrib_rows"], res["expend_rows"]
        for r in crows:
            normalize_donors.normalize_contrib(r, meta["candidate"], aliases)
        for r in erows:
            normalize_donors.normalize_vendor(r)

        # ---- reconcile each side against the printed totals
        c_sum = _sum(crows)
        e_sum = _sum(erows)
        rec_c, delta_c = reconcile.reconciles(c_sum, res["stated_contrib"])
        rec_e, delta_e = reconcile.reconciles(e_sum, res["stated_expend"])
        conf_c = reconcile.side_confidence(not is_scanned, rec_c)
        conf_e = reconcile.side_confidence(not is_scanned, rec_e)

        for r in crows:
            r.extraction_confidence = conf_c
            if rec_c is not True:
                r.needs_review = "1"
        for r in erows:
            r.extraction_confidence = conf_e
            if rec_e is not True:
                r.needs_review = "1"

        self_funded = round(sum(
            _amt(r.amount) or 0.0 for r in crows
            if r.donor_type in ("candidate-self", "loan") and r.amount), 2)

        notes = res["notes"]
        flags = []
        if rec_c is False:
            flags.append("contrib!=stated")
        if rec_e is False:
            flags.append("expend!=stated")
        if flags:
            notes = (notes + "; " if notes else "") + " ".join(flags)

        ft = common.FilingTotals(
            candidate=meta["candidate"], office=meta["office"],
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period="", filing_type=meta["filing_type"],
            stated_total_contributions=common.money_str(res["stated_contrib"]),
            stated_total_expenditures=common.money_str(res["stated_expend"]),
            stated_beginning_balance=common.money_str(res["stated_begin"]),
            stated_ending_balance=common.money_str(res["stated_end"]),
            itemized_contrib_sum=("" if is_scanned and not crows else common.money_str(c_sum)),
            itemized_expend_sum=("" if is_scanned and not erows else common.money_str(e_sum)),
            reconciles_contrib=("" if rec_c is None else str(rec_c)),
            reconciles_expend=("" if rec_e is None else str(rec_e)),
            recon_delta_contrib=("" if delta_c is None else f"{delta_c:.2f}"),
            recon_delta_expend=("" if delta_e is None else f"{delta_e:.2f}"),
            self_funded_amount=common.money_str(self_funded),
            n_contrib_rows=str(len(crows)), n_expend_rows=str(len(erows)),
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            extraction_confidence=_filing_conf(conf_c, conf_e), notes=notes,
        )

        contrib_all.extend(crows)
        expend_all.extend(erows)
        totals_all.append(ft)
        recon_report.append((ix["candidate"], ix["election_year"],
                             ft.reconciles_contrib, ft.reconciles_expend,
                             ft.extraction_confidence))

    _write(HERE / "contributions.csv", common.CONTRIB_HEADER, contrib_all)
    _write(HERE / "expenditures.csv", common.EXPEND_HEADER, expend_all)
    _write(HERE / "filing_totals.csv", common.TOTALS_HEADER, totals_all)

    _print_report(recon_report, contrib_all, expend_all)


def _write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(common.row_to_dict(r))


def _print_report(rep, contrib_all, expend_all):
    clean = sum(1 for r in rep if len(r) == 5 and r[2] == "True" and r[3] == "True")
    flagged = [r for r in rep if not (len(r) == 5 and r[2] == "True" and r[3] == "True")]
    print(f"filings: {len(rep)}  |  both-sides reconcile: {clean}  |  flagged: {len(flagged)}")
    print(f"contribution rows: {len(contrib_all)}  |  expenditure rows: {len(expend_all)}")
    print("\nflagged / not-both-clean:")
    for r in flagged:
        print("  ", " | ".join(str(x) for x in r))


if __name__ == "__main__":
    main()
