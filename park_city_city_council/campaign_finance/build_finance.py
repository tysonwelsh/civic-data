#!/usr/bin/env python3
"""build_finance.py — Park City driver for the structured campaign-finance layer.

Park City self-hosts its candidate "Campaign Financial Report" (UCA 10-3-208 + PCMC 3-3) on its
Revize `/Documents/.../Campaign Disclosures/` tree — no EasyVote / state portal. The form is a
Park-City-specific two-section variant (Form "A" contributions + Form "B" expenditures, in-kind
inline), structurally distinct from the Orem-style utah_standard_form, so it uses the NEW family
`families/parkcity_form.py` (see that module's header for the full rationale + column drift).

SCOPE — the **126 campaign C&E filings** only. Park City's **10 conflict-of-interest officeholder
statements** (filing_type=conflict_of_interest, 2025-2026) are a SEPARATE statutory genre and are
EXCLUDED here (in_scope_fn), exactly as Orem excludes its COI statements. See CLAUDE.md.

Two modes, auto-selected per filing by `is_scanned_fn`:
  * 82 born-digital (`format=text`, `pdftotext -layout`)  -> text mode.
  * 44 scanned (`format=scanned`, tesseract)              -> OCR mode (shared currency-repair +
    `$`-spacing normalizer + date-sanity; reconciled against the form's printed Form-A/B totals).

Contributions reconcile CASH rows only (in-kind is a separate inline line EXCLUDED from the Form-A
cash total) -> reconcile_cash_only=True.

DEDUP — Park City is CUMULATIVE (`is_incremental` carried False on rows via the family? no —
see below): each report restates the whole cycle-to-date (a General report contains the cycle's
April-October contributions; the Final restates everything), so a candidate's cycle total is the
LATEST (non-superseded) report per candidate+cycle, NOT a sum (contrast Orem = incremental). The
authoritative rollup is `scripts/campaign_finance/cycle_totals.py`, which additionally re-derives
the style per candidate. driver.run(dedup_mode="cumulative"); an amendment supersedes its snapshot.

Vision escalation (GATED, scanned-only): scanned filings that still fail reconciliation after OCR +
repair are escalated to Claude vision (`parkcity_vision_extract.py` -> `vision/<doc8>.json`), fed
back through the SAME reconciliation via the driver `rows_override_fn`. A figure that will not
reconcile stays blank + needs_review + low — never guessed.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py
"""
from __future__ import annotations

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


def _did8(ix):
    """Stable 8-char filing id: sha1 of the dataset-relative path (index.csv carries no sha256)."""
    return hashlib.sha1(ix["path"].encode("utf-8")).hexdigest()[:8]


def _office(ix):
    o = (ix.get("office") or "").strip()
    if o.lower().startswith("mayor"):
        return "Mayor"
    if o.lower().startswith("council"):
        return "Council"
    return o          # blank (4 filings with no office token) — kept verbatim, never invented


def _meta(ix):
    return dict(
        candidate=ix["candidate"], office=_office(ix), seat="",     # Park City is all at-large
        election_year=ix["election_year"], filing_date=ix.get("date", ""),
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_did8(ix), reporting_period=ix.get("report_period", ""))


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / ix["election_year"] / f"{stem}.txt"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME reconciliation as the OCR rows. Returns None when there is no cache."""
    cache = VISION_DIR / f"{meta['document_id']}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    vm = meta["extract_method"].split("/")[0] + "/vision"

    def _date(s):
        return parse_date(str(s)) or "" if s not in (None, "", "null") else ""

    crows = []
    for i, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        ink = bool(r.get("in_kind"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat="",
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(ink), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for i, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat="",
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    # vision total: Form-A CASH total only (in-kind excluded, matching the printed reconciliation)
    tc = _vmoney(d.get("total_contributions"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=tc, stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=None, stated_end=None,
                notes="vision-transcribed(claude-sonnet-5)")


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="parkcity_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: ix.get("format", "").strip().lower() == "scanned",
        in_scope_fn=lambda ix: ix.get("filing_type", "") != "conflict_of_interest",
        reconcile_cash_only=False,          # Form-A total INCLUDES itemized in-kind (valued inline)
        dedup_mode="cumulative",            # each report restates cycle-to-date; latest = cycle total
        amend_fn=lambda ix: ix.get("amended", "").strip().lower() == "yes"
        or bool(re.search(r"amend|revis|updated", ix.get("title", ""), re.I)),
        rows_override_fn=_vision_result)     # vision re-transcription for OCR-unreconciled filings
