#!/usr/bin/env python3
"""build_finance.py — Nephi driver for the structured campaign-finance layer.

Nephi self-hosts its municipal campaign Contribution & Expenditure reports on the city
DocumentCenter (CivicPlus), on the SAME statutory Utah municipal "Campaign Financial Report"
form (UCA 10-3-208) that Orem/Logan use. So Nephi REUSES the shared `utah_standard_form`
family UNCHANGED — the only difference is Nephi's label wording, passed as
`meta["form_opts"]` overrides (no edit to the shared family). Nephi is the same class as
Logan: ALL handwritten scans, no per-section printed TOTAL line, totals stated only in a
numbered COVER block. It therefore copies Logan's recipe verbatim:
  * section headers SENTINELED OFF (`(?!)`) so a detected-but-$-less section is never coerced
    to a false $0 nil; and
  * the numbered COVER block is the reconciliation anchor (l1←itemized contrib, l2←under-$500
    aggregate, l3←itemized expend; stated_contrib = l1+l2 via the family's headline fallback).

TWO form layouts (both covered by the form_opts labels below):
  * Older "Carr Printing" form (2019/2021/2023):
        1. Contributions received totaling $500 or LESS ............ $   (l2, under-$500 agg)
        2. Enter the total of all received from Form A ............. $   (l1, itemized contrib)
        3. Expenditures totaling $500 or LESS ..................... $   (expend under-$500)
        4. Enter the total of all expenditures from Form B ........ $   (l3, itemized expend)
        5. Balance at the end of the reporting period ............ $
  * 2025 "Nephi City Campaign Financial Report" form:
        1a Aggregate total of contributions under $500.00 ......... $   (l2)
        1b Itemized total of contributions totaling $500.00+ ...... $   (l1)
        2a Aggregate total of campaign expenditures under $500.00 . $
        2b Itemized total of campaign expenditures ............... $   (l3)

MULTI-CANDIDATE COMPILATIONS: the 2021 (View 2118) and 2023 (Views 2706/2803) uploads pack
several candidates' 2-page filings into ONE PDF; index.csv splits them into per-candidate rows
sharing one `path` + carrying a `page_range`. The vision extractor renders ONLY that candidate's
page span (nephi_vision_extract.py); document_id is keyed on (path,page_range) so compilation
rows never collide. The one un-attributable row (candidate "(unidentified filers)", 3 forms with
illegible handwritten names) is OUT OF SCOPE for the money layer — attributing those dollars to a
name we cannot read would fabricate identity; it stays an honest document-archive-only gap.

WORWOOD AMBIGUITY: SKIP F. WORWOOD (2021, 2025) and TRAVIS L WORWOOD (2023) are DISTINCT people
kept apart by the (candidate, election_year) key — never merged.

DEDUP — Nephi is MIXED, empirically determined per candidate (do NOT assume one rule), exactly
like Logan: `is_incremental` is set PER (candidate, election_year) from the vision-transcribed
contribution-row overlap between a candidate's consecutive reports (`_classify_modes`). Filers who
re-list the whole cycle every round (overlap high) -> cumulative (`False`, cycle total = latest);
filers who report only new activity (overlap ~0) -> incremental (`True`, cycle total = sum). Single-
report (candidate,year) pairs default to incremental. `dedup_mode=None` (no uniform supersession).

Vision escalation (GATED): all Nephi filings are handwritten scans whose itemized amounts are
written WITHOUT a `$` sign, so OCR reconciles ~0 -> nephi_vision_extract.py transcribes each
in-scope filing (per page_range) to vision/<doc8>.json, fed back through the SAME reconciliation
via the driver `rows_override_fn`. A figure that will not reconcile stays blank + needs_review +
low — never guessed.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import hashlib
import json
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
UNIDENTIFIED = "(unidentified filers)"   # the one un-attributable compilation row — out of scope


# ---- Nephi label drift for the shared utah_standard_form family (NO family edit) ----
# Same recipe as Logan: itemized-section headers sentineled off (handwritten $-less rows are
# unreadable by OCR; detecting a section but reading 0 rows would falsely coerce its total to $0
# and reconcile a real filing as nil). Vision reads the rows. The numbered cover block is the
# reconciliation anchor. The l1/l2/l3 labels cover BOTH Nephi form layouts (2025 1a/1b/2a/2b AND
# the older Carr-printing lines 1-4).
NEPHI_FORM_OPTS = dict(
    sec_cashc=r"(?!)",
    sec_inkind=r"(?!)",     # Nephi has no in-kind SECTION (in-kind is a Form-A column)
    sec_cashe=r"(?!)",
    # itemized contributions (2025 "1b Itemized total of contributions" / older "total of all
    # received from Form A"):
    l1=r"itemized total of contributions|total of all received from form",
    # under-$500 aggregate (2025 "1a Aggregate total of contributions under" / older
    # "Contributions received totaling $500 or less"):
    l2=r"aggregate total of contributions|contributions received totaling",
    # itemized expenditures (2025 "2b Itemized total of campaign expenditures" / older "total of
    # all expenditures from Form B"):
    l3=r"itemized total of campaign expenditures|total of all expenditures from form",
)


def _did8(ix):
    """Stable 8-char filing id, unique PER INDEX ROW. Nephi's index.csv has no sha256 column and
    multi-candidate compilations SHARE a `path`, so derive the id from (path, page_range): each
    candidate row within a compilation carries a distinct page_range, and single-filing paths are
    already unique. Distinguishes the two Worwoods (different paths / page_ranges)."""
    return hashlib.sha1(f"{ix['path']}|{ix.get('page_range', '')}".encode("utf-8")).hexdigest()[:8]


def _in_scope(ix):
    """Every retained filing is an in-scope campaign C&E report EXCEPT the single un-attributable
    compilation row (3 forms with illegible handwritten candidate names) — its dollars cannot be
    tied to a candidate without fabricating identity, so it is document-archive-only (honest gap)."""
    return (ix.get("candidate") or "").strip() != UNIDENTIFIED


def _classify_modes():
    """Empirically classify each (candidate, election_year) as cumulative ('False') or incremental
    ('True') from the OVERLAP of vision-transcribed contribution rows between a candidate's
    consecutive reports. Cumulative filers re-list the whole cycle every round (overlap high);
    incremental filers list only that round's new activity (overlap ~0). Single-report pairs ->
    'True' (statutory per-period default). Returns {(candidate, election_year): is_incremental_str}.
    (Identical method to Logan's — Nephi filers are likewise not internally consistent.)"""
    import csv as _csv
    import statistics
    from collections import defaultdict

    def _sigs(doc8):
        c = VISION_DIR / f"{doc8}.json"
        if not c.exists():
            return []
        d = json.loads(c.read_text())
        return [(str(r.get("date")), str(r.get("amount"))) for r in d.get("contributions", [])]

    filings = defaultdict(list)
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        for ix in _csv.DictReader(fh):
            if not _in_scope(ix):
                continue
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


def _office_seat(ix):
    """Nephi is Mayor + 5 at-large council (no districts) -> (office, '')."""
    o = (ix.get("office") or "").strip()
    return ("Mayor" if o.lower().startswith("mayor") else "Council"), ""


def _meta(ix):
    office, seat = _office_seat(ix)
    return dict(
        candidate=ix["candidate"], office=office, seat=seat,
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_did8(ix), reporting_period=ix.get("reporting_period", ""),
        form_opts=NEPHI_FORM_OPTS)


def _sidecar(ix):
    # Nephi text sidecars are flat: text/<stem>.txt (one per raw PDF; compilations share it).
    return HERE / "text" / f"{Path(ix['path']).stem}.txt"


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result(ix, meta):
    """driver rows_override_fn: build rows from a cached Claude-vision transcription when present,
    fed through the SAME reconciliation as the OCR rows. Returns None for filings with no cache.

    Nephi reconciliation anchor (computed HERE, not in the shared family):
      stated_contrib = (under-$500 aggregate) + (itemized $500+)   [= total contributions]
      stated_expend  = (under-$500 aggregate) + (itemized)         [= total expenditures]
    A grand total the form prints explicitly, if vision captured one, wins over the a+b sum."""
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
        cover-block figures. A STATED grand total is non-negative by definition, so a leading '-'
        (vision reading the form's dotted-leader '......$ 108.19' as a minus) is normalized to its
        magnitude — STATED TOTAL only, never a row amount. Documented in the note."""
        g = _vmoney(grand)
        if g is not None:
            return abs(g), (g < 0)
        va, vb = _vmoney(a), _vmoney(b)
        if va is None and vb is None:
            return None, False
        raw = round((va or 0.0) + (vb or 0.0), 2)
        return abs(raw), (raw < 0)

    stated_contrib, flip_c = _combine(d.get("total_contributions"),
                                      d.get("contributions_under_500"),
                                      d.get("contributions_itemized"))
    stated_expend, flip_e = _combine(d.get("total_expenditures"),
                                     d.get("expenditures_under_500"),
                                     d.get("expenditures_itemized"))
    notes = "vision-transcribed(claude-sonnet-5)"
    if flip_c or flip_e:
        notes += "; stated total sign normalized (dotted-leader artifact)"
    agg = _vmoney(d.get("contributions_under_500"))
    if agg:
        notes += f"; <=$500 aggregate stated ${agg:.2f}"
    end_bal = _vmoney(d.get("ending_balance"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=(abs(end_bal) if end_bal is not None else None),
                notes=notes)


MODES = _classify_modes()  # {(candidate, election_year): is_incremental} — empirical, per candidate


if __name__ == "__main__":
    driver.run(
        here=HERE, family_id="utah_standard_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=lambda ix: True,       # all Nephi filings are handwritten scans
        in_scope_fn=_in_scope,               # exclude the un-attributable compilation row
        reconcile_cash_only=False,           # Nephi states TOTAL contributions incl. in-kind column
        dedup_mode=None,                     # MIXED filers -> is_incremental is per-candidate
        amend_fn=lambda ix: (ix.get("amended", "").strip().lower() not in ("", "no", "false")),
        rows_override_fn=_vision_result)     # vision re-transcription for OCR-unreconciled filings
