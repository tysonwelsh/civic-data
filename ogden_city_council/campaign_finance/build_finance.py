#!/usr/bin/env python3
"""build_finance.py — Ogden driver for the structured campaign-finance layer.

Ogden self-hosts its campaign Contribution & Expenditure disclosures on the City Recorder's
Election-Information pages (no EasyVote / third-party portal). Each PDF is a single "Combined
Report of Contributions & Expenditures" packet that bundles a candidate's WHOLE cycle of
statutory reports, so it routes through the new `ogden_form` family (Attachment A contributions /
Attachment B expenditures, repeated per reporting period; in-kind is a per-row flag). See
`scripts/campaign_finance/families/ogden_form.py`.

Two modes, auto-selected per filing by `is_scanned_fn`:
  * 14 born-digital (`format=text`, `pdftotext -layout`)  -> text mode.
  * 24 scanned (`format=scanned`, tesseract OCR)           -> OCR mode (shared currency-repair
    whitelist; reconciled against the packet's printed attachment TOTALs).

DEDUP — one filing per candidate-cycle (the packet already aggregates the whole cycle: each
donation is itemized once across its reporting period), so is_incremental=False and NO cross-
filing supersession is needed (dedup_mode=None), exactly like Provo's whole-cycle summary.

Vision escalation (GATED, minimal): only SCANNED filings that still fail reconciliation after OCR
are escalated to Claude vision (`vision_extract.py` -> `vision/<sha1(index_path)[:8]>.json` (repo-standard key since the 2026-07-19 migration; formerly the DocumentCenter view id)), fed back through
the SAME reconciliation via the driver `rows_override_fn`. Born-digital filings are never
escalated. A figure that will not reconcile stays blank + needs_review + low — never guessed.

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
    """Stable per-filing id = the DocumentCenter View id (leading digits of the raw filename,
    e.g. raw/2019/31390_2019-Nadolski-Combined.pdf -> '31390'). Unique across the dataset."""
    base = os.path.basename(ix["path"])
    m = re.match(r"(\d+)", base)
    return m.group(1) if m else os.path.splitext(base)[0][:8]


def _meta(ix):
    office = (ix.get("office") or "").strip() or "Council"
    return dict(
        candidate=ix["candidate"], office=office, seat=(ix.get("district") or "").strip(),
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", "summary"), source_filing=ix["path"],
        document_id=_docid(ix), reporting_period="")


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    s = re.sub(r"[^\d.,\-]", "", str(x))
    # ledger shorthand "100.-" = 100.00 (Graf 2023 handwritten schedules) — deterministic
    # notation, not a guess; the cache keeps the verbatim string.
    s = re.sub(r"\.\-$", ".00", s)
    return common.parse_money("$" + s)


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
            reporting_period="", date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental="False",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for k, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period="", date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="False",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    # stated totals = SUM of the printed attachment TOTALs vision transcribed (the model returns
    # each verbatim; WE sum, never the model). Fall back to a scalar total_* if present. A side
    # with no readable printed total stays None (unknown) — never fabricated.
    def _sum_totals(list_key, scalar_key):
        vals = [_vmoney(x) for x in (d.get(list_key) or [])]
        vals = [v for v in vals if v is not None]
        if vals:
            return round(sum(vals), 2)
        return _vmoney(d.get(scalar_key))

    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_sum_totals("contribution_totals", "total_contributions"),
                stated_expend=_sum_totals("expenditure_totals", "total_expenditures"),
                stated_begin=None, stated_end=None,
                notes="vision-transcribed(claude-sonnet-5)")


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="ogden_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: ix.get("format", "").strip().lower() == "scanned",
        in_scope_fn=lambda ix: True,        # all 38 are campaign C&E combined reports
        reconcile_cash_only=False,          # in-kind is a per-row flag; printed TOTALs include it
        dedup_mode=None,                    # one whole-cycle packet per candidate-cycle
        rows_override_fn=_vision_result)     # vision re-transcription for OCR-unreconciled filings
