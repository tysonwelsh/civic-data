#!/usr/bin/env python3
"""build_finance.py — West Valley City driver for the structured campaign-finance layer (F8).

Thin dispatcher: selects the new `westvalley_form` family via the shared framework driver and
writes contributions.csv / expenditures.csv / filing_totals.csv from index.csv + text/*.txt.

WVC self-hosts its "CAMPAIGN FINANCE STATEMENT" (Form A/B) on the city CivicPlus Archive Center
(no EasyVote / third-party portal — verified in ../CLAUDE.md). Two modes, auto-selected per
filing by `is_scanned_fn`:
  * 42 born-digital (`format=text`, pdftotext -layout)      -> text mode.
  * 63 scanned (`format=scanned`, tesseract OCR @300dpi)     -> OCR mode (shared currency-repair
    whitelist; reconciled against the cover-page printed totals). Handwritten scans that yield no
    dated rows flag honestly at the OCR floor and are the gated-vision candidates.

SCOPE — all 105 index rows are campaign C&E statements (interim + summary); all in scope.

DEDUP — is_incremental=True (per-period; each report covers only its own period, verified Jake
Fitisemanu 2021 general $3,204.87 -> final $1,026.19). A candidate's summary/final and interims
are rolled up per-candidate by cycle_totals.py (which flags the mixed cases); a same-period
amendment/re-file supersedes its original (dedup_mode="incremental").

Vision escalation (GATED, minimal): only SCANNED filings that still fail reconciliation after OCR
are escalated to Claude vision (`vision_extract.py` -> `vision/<sha1(index_path)[:8]>.json` (repo-standard key since the 2026-07-19 migration; formerly <ADID>.json)), fed back through the
SAME reconciliation via the driver `rows_override_fn`. Born-digital filings are never escalated. A
figure that will not reconcile stays blank + needs_review + low — never guessed.

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


def _docid(ix):
    """Stable per-filing id = the Archive Center ADID (index.csv source_id, e.g. 'ADID3496').
    The 2019 Wayback filing uses its DocumentCenter id ('DocumentCenter9949')."""
    sid = (ix.get("source_id") or "").strip()
    return sid or os.path.splitext(os.path.basename(ix["path"]))[0][:12]


def _meta(ix):
    dist = (ix.get("district") or "").strip()
    return dict(
        candidate=ix["candidate"], office=(ix.get("office") or "Council").strip(),
        seat=(f"District {dist}" if dist.isdigit() else dist),
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_docid(ix), reporting_period=ix.get("filing_phase", ""))


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _is_scanned(ix):
    return ix.get("format", "").strip().lower() == "scanned"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,\-]", "", str(x)))


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
    for k, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for k, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    # stated totals = the cover-page printed totals vision transcribed verbatim (a scalar each;
    # a side with no readable printed total stays None). We never let the model sum.
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_vmoney(d.get("total_contributions")),
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=None, stated_end=_vmoney(d.get("ending_balance")),
                notes="vision-transcribed(claude-sonnet-5)")


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="westvalley_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=_is_scanned,
        in_scope_fn=lambda ix: True,        # all 105 are campaign C&E statements
        reconcile_cash_only=False,          # cover "Total contributions" INCLUDES in-kind
        dedup_mode="incremental",           # per-period; amendment/re-file supersedes same period
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_vision_result,     # vision re-transcription for OCR-unreconciled filings
        derive_incremental=True)             # empirical per-candidate is_incremental (2026-07-20):
                                             # row-metadata restamp only; cycle figures move ONLY
                                             # via documented cycle_overrides.csv rows
