#!/usr/bin/env python3
"""build_finance.py — Logan driver for the structured campaign-finance layer.

Logan self-hosts its municipal campaign Contribution & Expenditure reports on the city
recorder's election page (Revize CMS; no EasyVote / third-party portal), on the SAME
statutory Utah "Financial Disclosure / Report of Contributions and Expenditures" form
(UCA 10-3-208) that Orem uses. So Logan REUSES the shared `utah_standard_form` family
UNCHANGED — the only difference is Logan's label wording, passed as `meta["form_opts"]`
overrides (no edit to the shared family; Nephi/Vineyard reuse it too).

WHAT DRIFTS ON LOGAN'S FORM (handled entirely via form_opts):
  * The numbered totals block, not any section TOTAL, is the reconciliation anchor. Logan's
    form prints NO per-section printed TOTAL line (unlike Orem's Cash/In-Kind/Cash-Exp
    subtotals); the itemized "Form A" / "Form B" pages carry the rows and the numbered block
    on the cover states the totals:
        2025 form:  1a Aggregate total of contributions under $500  (unitemized aggregate)
                    1b Itemized total of contributions $500 or more (= Form "A" total)
                    2a Aggregate total of campaign expenditures under $500
                    2b Itemized total of campaign expenditures      (= Form "B" total)
        2021 form:  1 Total aggregate amount of less than $500 (contrib+exp combined)
                    2 Itemized contributions of more than $500
                    3 Itemized expenditures of more than $500
    So l1←1b(itemized contrib), l2←1a(under-$500 aggregate), l3←2b/line3(itemized expend).
    stated_contrib = 1b + 1a (the family's headline fallback already sums l1+l2 — exactly the
    total-reported anchor). The under-$500 aggregate is recorded in the note, not synthesized
    as rows (Orem discipline).
  * The itemized-section headers are SENTINELED OFF (`(?!)`, never match) on purpose. Logan
    filings are ALL handwritten scans whose itemized amounts are written WITHOUT a `$` sign,
    so the shared money tokenizer (which — by anti-fabrication design — only accepts a
    `$`-anchored token, never a bare number) cannot read them from OCR. Detecting the section
    but reading zero rows would make the family coerce that section's total to $0 and FALSELY
    reconcile a real filing as nil. Suppressing section detection instead forces the correct
    headline-total anchor and 0 OCR rows -> the filing flags -> vision escalation supplies the
    rows. OCR mode therefore reconciles only genuine NIL filings + the rare clean cover-total;
    everything with real itemization is transcribed by the gated vision pass.

DEDUP — Logan is MIXED, empirically determined per candidate (do NOT assume one rule):
Logan filers are NOT internally consistent, so `is_incremental` is set PER CANDIDATE-CYCLE from
the transcribed row overlap between a candidate's consecutive reports (`_classify_modes`), not
as a city constant:
  * PREDOMINANT = INCREMENTAL (`is_incremental=True`) — 7 of the 9 traceable multi-report filers
    (Nafziger, Seamons, Dahle, Mark A. Anderson, Roesberry, Molitor, Dee Jones-2021) report ONLY
    that period's new, non-overlapping activity (consecutive-report row overlap = 0.00). This is
    the statutory design of the form (line 3 = "Balance at the end of THE REPORTING PERIOD"). For
    these, a cycle total is the SUM of the period reports.
  * EXCEPTION = CUMULATIVE (`is_incremental=False`) — exactly 2 filers, **Ernesto Lopez** and
    **Katie Lee-Koven**, re-list the ENTIRE cycle-to-date every period (overlap = 1.00; row counts
    grow 9->11->14->15 / 14->15->22->21). For these, a cycle total is the LATEST report, NOT a sum.
  * untraceable 2-report filers (a nil/near-nil post-primary "eliminated" second report) default
    to INCREMENTAL (statutory default; the empty second report adds ~nothing to a sum anyway).
Because no single global rule is correct, `dedup_mode=None` (the engine asserts NO uniform
supersession); the per-candidate `is_incremental` flag is the machine-readable signal a cycle-
total query must honor (sum where True, take-latest where False). See CLAUDE.md caveat.

Vision escalation (GATED): only scanned filings that still fail reconciliation after OCR are
escalated to Claude vision (`logan_vision_extract.py` -> `vision/<doc8>.json`), fed back through
the SAME reconciliation via the driver `rows_override_fn`. A figure that will not reconcile
stays blank + needs_review + low — never guessed.

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


def _classify_modes():
    """Empirically classify each (candidate, election_year) as cumulative ('False') or incremental
    ('True') from the OVERLAP of transcribed contribution rows between a candidate's consecutive
    reports. Cumulative filers re-list the whole cycle every period (overlap high); incremental
    filers list only that period's new activity (overlap ~0). Robust to a single stray back-dated
    row (uses set overlap, not min-date). Untraceable / single-traceable -> 'True' (statutory
    per-period default). Returns {(candidate, election_year): is_incremental_str}."""
    import csv as _csv
    import json as _json
    import statistics
    from collections import defaultdict

    def _sigs(doc8):
        c = VISION_DIR / f"{doc8}.json"
        if not c.exists():
            return []
        d = _json.loads(c.read_text())
        return [(str(r.get("date")), str(r.get("amount"))) for r in d.get("contributions", [])]

    filings = defaultdict(list)
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        for ix in _csv.DictReader(fh):
            filings[(ix["candidate"], ix["election_year"])].append((ix["date"], _did8(ix)))

    modes = {}
    for key, lst in filings.items():
        lst.sort()
        seqs = [_sigs(d) for _, d in lst]
        fracs = []
        for a, b in zip(seqs, seqs[1:]):
            if a:
                fracs.append(len(set(a) & set(b)) / len(set(a)))
        modes[key] = "False" if (fracs and statistics.median(fracs) >= 0.5) else "True"
    return modes


# ---- Logan label drift for the shared utah_standard_form family (NO family edit) ----
LOGAN_FORM_OPTS = dict(
    # itemized-section headers sentineled off: handwritten $-less rows are unreadable by OCR;
    # detecting a section but reading 0 rows would falsely coerce its total to $0. Vision reads
    # the rows instead. (Both 2021 "ITEMIZED REPORT OF CONTRIBUTIONS GREATER THAN $500" and 2025
    # "ITEMIZED CONTRIBUTION REPORT (Form A)" are covered by this deliberate suppression.)
    sec_cashc=r"(?!)",
    sec_inkind=r"(?!)",     # Logan has no in-kind SECTION (in-kind is a Form-A column)
    sec_cashe=r"(?!)",
    # numbered cover-block labels (the reconciliation anchor):
    l1=r"itemized (?:total of contributions|contributions of more than)",   # 1b / 2021 line 2
    l2=r"aggregate (?:total of contributions|amount of less than)",         # 1a / 2021 line 1
    l3=r"itemized (?:total of campaign expenditures|expenditures of more than)",  # 2b / 2021 line 3
)


def _did8(ix):
    """Stable 8-char filing id. Logan's index.csv has no sha256 column, so derive it
    deterministically from the dataset-relative path (unique across the 45 filings)."""
    return hashlib.sha1(ix["path"].encode("utf-8")).hexdigest()[:8]


def _office_seat(ix):
    """Logan is Mayor + 5 at-large council (no districts) -> (office, '')."""
    o = (ix.get("office") or "").strip()
    return ("Mayor" if o.lower().startswith("mayor") else "Council"), ""


def _meta(ix):
    office, seat = _office_seat(ix)
    return dict(
        candidate=ix["candidate"], office=office, seat=seat,
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_did8(ix), reporting_period=ix.get("report_period", ""),
        form_opts=LOGAN_FORM_OPTS)


def _sidecar(ix):
    # Logan text sidecars are nested by year: text/<year>/<stem>.txt
    p = Path(ix["path"])                      # raw/<year>/<stem>.pdf
    return HERE / "text" / p.parent.name / f"{p.stem}.txt"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME reconciliation as the OCR rows. Returns None for filings with no cache.

    Logan reconciliation anchor (computed HERE, not in the shared family):
      stated_contrib = (1a aggregate under $500) + (1b itemized $500+)   [= total contributions]
      stated_expend  = (2a aggregate under $500) + (2b itemized)         [= total expenditures]
    A grand-total the form prints explicitly, if vision captured one, wins over the a+b sum."""
    cache = VISION_DIR / f"{meta['document_id']}.json"
    if not cache.exists():
        return None
    d = json.loads(cache.read_text())
    vm = meta["extract_method"].split("/")[0] + "/vision"
    inc = MODES.get((meta["candidate"], meta["election_year"]), "True")  # empirical per-candidate

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
            in_kind=str(bool(r.get("in_kind"))), is_incremental=inc,
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
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental=inc,
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))

    def _combine(grand, a, b):
        """Return (stated_total_or_None, sign_normalized_bool). A grand total or a+b sum of the
        cover-block figures. A STATED grand total on this form is non-negative by definition, so a
        leading '-' (vision reading the form's dotted-leader line '......$ 1,664.81' as a minus
        sign) is normalized to its magnitude — this only touches a STATED TOTAL, never a row
        amount (a genuine per-row refund reversal keeps its sign). Documented in the note."""
        g = _vmoney(grand)
        if g is not None:
            return abs(g), (g < 0)
        va, vb = _vmoney(a), _vmoney(b)
        if va is None and vb is None:
            return None, False
        raw = round((va or 0.0) + (vb or 0.0), 2)
        return abs(raw), (raw < 0)

    stated_contrib, flip_c = _combine(d.get("total_contributions"),
                                      d.get("contributions_under_500"), d.get("contributions_itemized"))
    stated_expend, flip_e = _combine(d.get("total_expenditures"),
                                     d.get("expenditures_under_500"), d.get("expenditures_itemized"))
    notes = "vision-transcribed(claude-sonnet-5)"
    if flip_c or flip_e:
        notes += "; stated total sign normalized (dotted-leader artifact)"
    agg = _vmoney(d.get("contributions_under_500"))
    if agg:
        notes += f"; ≤$500 aggregate stated ${agg:.2f}"
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=None, notes=notes)


MODES = _classify_modes()  # {(candidate, election_year): is_incremental} — empirical, per candidate


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="utah_standard_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: True,       # all 45 Logan filings are handwritten scans
        in_scope_fn=lambda ix: True,         # all 45 are campaign C&E reports
        reconcile_cash_only=False,           # Logan states TOTAL contributions incl. in-kind column
        dedup_mode=None,                     # MIXED filers -> no uniform supersession; is_incremental is per-candidate
        amend_fn=lambda ix: (ix.get("amended", "").strip().lower() not in ("", "no", "false")),
        rows_override_fn=_vision_result)     # vision re-transcription for OCR-unreconciled filings
