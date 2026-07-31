#!/usr/bin/env python3
"""build_finance.py — Taylorsville City driver for the structured campaign-finance layer.

Thin dispatcher: routes the `taylorsville_form` family through the shared framework driver and
writes contributions.csv / expenditures.csv / filing_totals.csv from index.csv (+ text/*.txt
sidecars for the born-digital filings, + vision/<sha1(index_path)[:8]>.json caches for transcribed ones — repo-standard key since the 2026-07-19 migration).

TAYLORSVILLE'S QUIRK (see families/taylorsville_form.py): the self-hosted fillable "Report of
Contributions & Expenditures" PDF has a TEMPLATE text layer with the real figures HANDWRITTEN /
rastered — so most filings (even the format=text "born-digital" ones) need VISION for numbers.
Text mode reads only the handful of newest forms whose totals auto-populate as cleanly-typed
accounting cells (the all-zeros annual statements); everything else returns stated=None and is
fed by a `vision/<sha1(index_path)[:8]>.json` cache via the driver's `rows_override_fn` (same reconcile test).

TWO REGIMES (`filing_regime`, from index.csv, carried to filing_totals.csv):
  * annual         — mandatory March-1 statements, EVERY sitting official, EVERY year (50).
                     A PARALLEL stream — NEVER summed into a race total.
  * election_cycle — during-a-race Primary/Pre-General/Final disclosures (21; 2021 & 2023).
                     ONLY these feed a cycle total. Reports are PER-PERIOD ("excluding those
                     previously reported") -> is_incremental=True -> a cycle total SUMS a
                     candidate's election_cycle reports.

  >>> cycle_totals.py MUST be run regime-aware (filter filing_regime=='election_cycle') so annual
  >>> statements never enter a race total. NOT run in this build (deferred, per the build plan).

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
    """Stable per-filing id = the CivicEngage document id (index.csv `docid`, unique)."""
    did = (ix.get("docid") or "").strip()
    return did or os.path.splitext(os.path.basename(ix["path"]))[0][:16]


def _meta(ix):
    dist = (ix.get("district") or "").strip()
    regime = ix.get("filing_regime", "")
    phase = ix.get("filing_phase", "")
    # reporting_period drives the driver's per-period dedup grouping. ANNUAL statements carry a
    # blank election_year, so every one of a candidate's annual filings would collide on
    # (candidate, "", "annual") and be falsely marked "superseded". Make each annual period
    # YEAR-distinct so annual statements never dedup against each other (each March-1 statement
    # is a standalone yearly filing, not an amendment of another year's).
    period = f"annual-{ix.get('filing_year', '')}-{_docid(ix)}" if regime == "annual" else phase
    return dict(
        candidate=ix["candidate"], office=(ix.get("office") or "Council").strip(),
        seat=(f"District {dist}" if dist.isdigit() else dist),
        election_year=ix.get("election_year", ""), filing_date=ix.get("date", ""),
        filing_type=ix.get("filing_type", ""), reporting_period=period,
        filing_regime=regime,
        source_filing=ix["path"], document_id=_docid(ix))


def _sidecar(ix):
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    return HERE / "text" / f"{stem}.txt"


def _is_scanned(ix):
    return ix.get("format", "").strip().lower() == "scanned"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    s = str(x).strip()
    # accounting-zero notations the forms print for $0 that vision transcribes verbatim:
    # "-0-", "-", "$-", "-0" -> 0.0 (a printed zero, not a fabricated one).
    if re.fullmatch(r"\$?\s*-\s*0?\s*-?\s*", s):
        return 0.0
    return common.parse_money("$" + re.sub(r"[^\d.,\-]", "", s))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME reconciliation as the text rows. Returns None for filings with no cache
    (they fall through to the text/*.txt sidecar parse). Cache schema (per cf-vision-transcribe):
      {contributions:[{date,name,amount,in_kind}],
       expenditures:[{date,recipient,purpose,amount,in_kind}],
       total_contributions, total_expenditures, ending_balance}
    Totals are the form's PRINTED cover totals transcribed verbatim (never summed by the model)."""
    # cache filename = the repo-standard key sha1(index path)[:8] (2026-07-19
    # migration; document_id keeps the city's native doc id for provenance —
    # the two are now decoupled).
    cache = VISION_DIR / f"{vision_lib.cache_key(meta['source_filing'])}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    vm = "taylorsville_form/vision"

    def _date(s):
        return (parse_date(str(s)) or "") if s not in (None, "", "null") else ""

    crows = []
    for k, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        name = (r.get("name") or r.get("donor") or "").strip()
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=name, amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and name) else "1"))
    erows = []
    for k, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        payee = (r.get("recipient") or r.get("payee") or r.get("name") or "").strip()
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=payee, purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{k + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_vmoney(d.get("total_contributions")),
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=_vmoney(d.get("beginning_balance")),
                stated_end=_vmoney(d.get("ending_balance")),
                notes="vision-transcribed(read-tool)")


def _in_scope(ix):
    """All 71 filings are C&E reports (both regimes ARE campaign finance) — the only
    out-of-scope rows are VERIFIED CONTENT DUPLICATES: a filing the city posted a second
    time under a different label/document id, byte-identical to the row that carries its
    genuine year. Excluding it keeps the identical money from being DOUBLE-COUNTED in the
    annual stream, while the raw PDF + its vision cache are retained on disk (dedup =
    documented exclusion, never deletion). Marked in index.csv via an
    `extraction_method` starting `duplicate-excluded` (same shape as the Barbieri
    doc10471 dup — see campaign_finance/CLAUDE.md). Currently: Overson doc8378
    (byte-identical to the genuine 2025 annual doc10635)."""
    return not (ix.get("extraction_method", "").strip().lower().startswith("duplicate-excluded"))


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="taylorsville_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=_is_scanned,
        in_scope_fn=_in_scope,
        reconcile_cash_only=False,          # section "TOTAL" includes in-kind at full value
        dedup_mode="incremental",           # per-period reports; SUM a candidate's election_cycle reports
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_vision_result,
        derive_incremental=True)            # empirical per-candidate is_incremental (2026-07-20):
                                            # row-metadata restamp only; annual filings carry blank
                                            # election_year + per-doc periods so only the
                                            # election_cycle stream can produce pair evidence;
                                            # cycle figures move ONLY via cycle_overrides.csv
