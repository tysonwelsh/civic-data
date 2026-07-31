#!/usr/bin/env python3
"""build_finance.py — Orem driver for the structured campaign-finance layer.

Orem posts its campaign Contribution & Expenditure reports directly on orem.gov (no EasyVote /
third-party portal), on the SELF-HOSTED Utah municipal "Financial Disclosure / Report of
Contributions and Expenditures" form (UCA 10-3-208). That form is a NEW family,
`utah_standard_form`, built to GENERALIZE — Logan, Nephi, and Vineyard file the same/near-
identical statutory form and reuse the module unchanged (city label drift, if any, goes through
`meta["form_opts"]`; none is needed for Orem).

Two modes, auto-selected per filing by `is_scanned_fn`:
  * 41 born-digital (`format=text`, `pdftotext -layout`)  -> text mode.
  * 50 scanned/photographed (`format=scanned`, tesseract)  -> OCR mode (shared common.py
    currency-repair whitelist + date-sanity; reconciled against the form's printed section
    TOTALs).

DEDUP — Orem is INCREMENTAL (`is_incremental=True`): each report covers a DISCRETE, non-
overlapping reporting period (Primary May13–Aug29 / General Aug30–Oct24 / Final Oct25–Nov14),
and the per-period loan-to-campaign amounts differ each report (2,200 -> 3,300 -> 14,400), so a
cycle total is the SUM of the period reports, NOT the latest snapshot. An amendment / re-file of
the same period supersedes the original (marked in filing_totals.notes, kept never dropped).

SCOPE — all 91 filings are in-scope campaign C&E reports; Orem's personal conflict-of-interest
statements are a separate genre already EXCLUDED at harvest (AVAILABILITY.md), so nothing is
skipped here.

Vision escalation (GATED, minimal): only scanned filings that still fail reconciliation after OCR
+ repair are escalated to Claude vision (`vision_extract.py` -> `vision/<sha1(index_path)[:8]>.json` (repo-standard key since the 2026-07-19 migration; formerly sha256[:8])), fed back
through the SAME reconciliation via the driver `rows_override_fn`. A figure that will not
reconcile stays blank + needs_review + low — never guessed.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import driver  # noqa: E402
import vision_lib  # noqa: E402
import common  # noqa: E402
from common import ContribRow, ExpendRow, parse_date  # noqa: E402

VISION_DIR = HERE / "vision"


def _did8(ix):
    """Stable 8-char filing id: first 8 of the filing's sha256 (index.csv carries it)."""
    return (ix.get("sha256", "") or "")[:8] or os.path.splitext(os.path.basename(ix["path"]))[0][:8]


def _office_seat(ix):
    """Orem is all at-large, no districts. office ∈ {Mayor, Council At-Large} -> (office, seat)."""
    o = (ix.get("office") or "").strip()
    if o.lower().startswith("mayor"):
        return "Mayor", ""
    return "Council", re.sub(r"^Council\s*", "", o).strip()   # "At-Large"


def _meta(ix):
    office, seat = _office_seat(ix)
    return dict(
        candidate=ix["candidate"], office=office, seat=seat,
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        # REGRESSION FIX (2026-07-20, same defect as sandy): the index column was renamed
        # report_period -> reporting_period after this build was written; the stale key
        # read "" for every filing, collapsing each candidate-cycle into ONE dedup group
        # (63 false supersessions) so cycle_totals saw only the LAST filing per cycle.
        document_id=_did8(ix),
        reporting_period=ix.get("reporting_period", "") or ix.get("report_period", ""))


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME reconciliation as the OCR rows. Returns None for filings with no cache."""
    # cache filename = the repo-standard key sha1(index path)[:8] (2026-07-19
    # migration; document_id keeps the city's native doc id for provenance —
    # the two are now decoupled).
    cache = VISION_DIR / f"{vision_lib.cache_key(meta['source_filing'])}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
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
    # vision totals: contributions side = cash + in-kind section totals (the form's own anchor)
    tc, tk = _vmoney(d.get("total_contributions")), _vmoney(d.get("total_in_kind_contributions"))
    stated_contrib = None if (tc is None and tk is None) else round((tc or 0.0) + (tk or 0.0), 2)
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib,
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=None, stated_end=None,
                notes="vision-transcribed(claude-sonnet-5)")


_AMEND = re.compile(r"amend|updated|revis", re.I)


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="utah_standard_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: ix.get("format", "").strip().lower() == "scanned",
        in_scope_fn=lambda ix: True,        # all 91 are campaign C&E reports
        reconcile_cash_only=False,          # contributions reconcile against Cash TOTAL + In-Kind TOTAL
        dedup_mode="incremental",           # discrete per-period reports; sum the cycle, amendment supersedes
        amend_fn=lambda ix: bool(_AMEND.search(
            ((ix.get("reporting_period", "") or ix.get("report_period", "")) + " "
             + ix.get("title", "") + " "
             + os.path.basename(ix.get("path", ""))))),
        rows_override_fn=_vision_result,     # vision re-transcription for OCR-unreconciled filings
        derive_incremental=True)             # EMPIRICAL per-candidate is_incremental (2026-07-20)
                                             # — replaces the per-city constant where row-overlap
                                             # evidence shows a filer is cumulative; no-evidence
                                             # candidates keep the constant (row-metadata only)
