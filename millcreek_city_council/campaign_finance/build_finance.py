#!/usr/bin/env python3
"""build_finance.py — Millcreek City driver for the structured campaign-finance layer (F9).

Thin dispatcher: selects the `millcreek_form` family via the shared framework driver and writes
contributions.csv / expenditures.csv / filing_totals.csv from index.csv + text/*.txt.

Millcreek self-hosts its "FINANCIAL CAMPAIGN REPORT" (Form A/B) on the city CivicPlus
DocumentCenter (../CLAUDE.md / AVAILABILITY.md). The form's THREE-COLUMN cover box
(LAST + THIS = CUMULATIVE) and the mixed cumulative-vs-per-period cycle structure are handled in
the family; this driver only maps index.csv -> meta and feeds vision overrides.

FORMAT is re-characterized PER FILING, not trusted from index.csv `format` (the label proved
unreliable — 2023 are garbled OCR, some 2025 mixed, several "text" are actually scanned/
handwritten). `_is_scanned` treats a filing as OCR-mode when its index says scanned OR its text
sidecar is effectively empty (no recoverable text layer — the 2019 Wayback scans). In text mode
an amount must be a clean `$`-anchored token, so OCR $-mangling ($ -> S/§/9) yields a BLANK amount
+ needs_review rather than a guessed digit; those filings fail reconciliation and are the
gated-vision set (cf-vision-transcribe).

DEDUP — NOT applied here (dedup_mode=None). Millcreek is mixed: 2021 is a single cumulative bundle
(is_incremental=False, set in the family); 2023/2025 are per-period (is_incremental=True). The
per-candidate cycle rollup (cycle_totals.py) is a DEFERRED step — and note that Millcreek "summary"
(Dec) reports are themselves per-period (the cumulative figure lives in the cover box), so the
cycle logic must treat Millcreek as fully-incremental (sum all periods) OR read the last report's
cover CUMULATIVE column, NOT the default "summary = cumulative restatement" assumption. Do not run
cycle_totals until that is reconciled.

Vision escalation (GATED, Read-tool method): filings that fail reconciliation after text/OCR are
escalated to Claude vision, whose transcription is cached at `vision/<sha1(index_path)[:8]>.json` (repo-standard key since the 2026-07-19 migration) and fed back
through the SAME reconciliation via the driver `rows_override_fn`. A figure that will not reconcile
stays blank + needs_review + low — never guessed.

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
    """Stable per-filing id = the DocumentCenter id (index.csv `doc_id`, unique per PDF)."""
    did = (ix.get("doc_id") or "").strip()
    return did or os.path.splitext(os.path.basename(ix["path"]))[0][:16]


def _meta(ix):
    dist = (ix.get("district") or "").strip()
    return dict(
        candidate=ix["candidate"], office=(ix.get("office") or "Council").strip(),
        seat=(f"District {dist}" if dist.isdigit() else dist),
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_docid(ix), reporting_period=ix.get("filing_type", ""))


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _is_scanned(ix):
    """Re-characterize per filing (index `format` is unreliable): OCR mode when index says
    scanned OR the text sidecar has no usable text layer (< ~300 chars — the 2019 Wayback scans)."""
    if (ix.get("format", "").strip().lower() == "scanned"):
        return True
    sc = _sidecar(ix)
    try:
        return len(sc.read_text(encoding="utf-8", errors="replace").strip()) < 300
    except OSError:
        return True


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,\-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME reconciliation as the text/OCR rows. Returns None when no cache exists.

    Cache contract (schema identical to West Valley's; filename = the repo-standard
    vision/<sha1(index_path)[:8]>.json since 2026-07-19): =
      {"contributions":[{date,name,amount,in_kind}...],
       "expenditures":[{date,recipient,purpose,amount,in_kind}...],
       "total_contributions","total_expenditures","ending_balance"}
    Amounts verbatim strings; totals are the form's PRINTED cover totals (the model never sums).
    is_incremental mirrors the family: False for the 2021 cumulative bundle, else True."""
    # cache filename = the repo-standard key sha1(index path)[:8] (2026-07-19
    # migration; document_id keeps the city's native doc id for provenance —
    # the two are now decoupled).
    cache = VISION_DIR / f"{vision_lib.cache_key(meta['source_filing'])}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    vm = meta["extract_method"].split("/")[0] + "/vision"
    incr = "False" if str(meta.get("election_year", "")).strip() == "2021" else "True"

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
            in_kind=str(bool(r.get("in_kind"))), is_incremental=incr,
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
            vendor_raw=(r.get("recipient") or r.get("name") or "").strip(),
            purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental=incr,
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_vmoney(d.get("total_contributions")),
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=None, stated_end=_vmoney(d.get("ending_balance")),
                notes="vision-transcribed(read-tool)")


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="millcreek_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=_is_scanned,
        in_scope_fn=lambda ix: True,        # all 41 index rows are campaign C&E reports
        reconcile_cash_only=False,          # most covers count in-kind (Jackson/Clark/Gray); Vice +
                                            # DeSirant print CASH-ONLY covers — the driver's
                                            # alternate-convention fallback reconciles those with a note
        dedup_mode=None,                    # mixed cumulative(2021)/per-period; cycle rollup deferred
        rows_override_fn=_vision_result)    # vision re-transcription for unreconciled filings
