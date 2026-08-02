#!/usr/bin/env python3
"""driver.py — shared build engine for the structured campaign-finance layer.

A city's build_finance.py calls `run()` with the form-family id + a few small callbacks that
map its own index.csv columns to the framework's meta. The engine: parses each filing via the
registered family, applies deterministic donor/vendor normalization, reconciles each side's
itemized sum against the form's printed total, writes the three DERIVED CSVs, and prints the
reconciliation report. Regenerate, never hand-edit the CSVs.

Reconciliation nuances handled here (beyond the Provo prototype's inline driver):
  * `reconcile_cash_only` — EasyVote states TOTAL CONTRIBUTIONS / EXPENDITURES EXCLUDING
    in-kind (in-kind is a separate line), so the itemized reconciliation sum counts CASH rows
    only. Lehi/Provo include in-kind at full value in the printed total -> sum all rows.
  * totals-only filings — a side with a positive stated total but ZERO itemized rows (Lehi's
    under-$500 exemption: the candidate may report totals without itemizing) reconciles as
    UNKNOWN (blank) + a note, NOT a false mismatch. A $0 side with no rows reconciles True.

finance_overrides.csv — WIRED (2026-07-19; the vote_overrides discipline):
  The per-city `campaign_finance/finance_overrides.csv` is the documented row-level
  correction mechanism. Columns:
      source_filing, line_no, csv, field, old_value, new_value, reason, added [, mode]
  * `mode` is a TRAILING, optional column: `apply` = the driver applies the correction at
    build time; anything else (blank / absent column) = a DOCUMENTATION-ONLY record (the
    historical contract — e.g. nephi's "Documented only" row and riverton's _adapt_cache
    record are documentation records and stay unapplied). Only `mode=apply` rows change
    output.
  * `csv` ∈ contributions | expenditures | filing_totals (".csv" suffix accepted).
    Row-level targets match on (source_filing, line_no) and any source-derived field of
    the row model; they are applied AFTER normalization and BEFORE reconciliation, so a
    corrected amount flows into itemized sums / self_funded / the printed-total test.
    `extraction_confidence`/`needs_review` are pipeline-computed and may NOT be overridden.
    filing_totals targets match on source_filing alone and are applied after the row is
    built — reconciliation fields are NOT recomputed there (figure corrections belong at
    the itemized-row level).
  * STALE rows FAIL THE BUILD LOUDLY (SystemExit): unknown csv/field, no (or ambiguous)
    matching row, or a current value that no longer equals `old_value`. Every applied
    override is printed. old_value/new_value compare against the value as it appears in
    the output CSV (auditable against the published file).
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

CF_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(CF_LIB))
sys.path.insert(0, str(CF_LIB / "families"))

import common          # noqa: E402
import reconcile       # noqa: E402
import normalize_donors  # noqa: E402
import registry        # noqa: E402


def _amt(s):
    if s in ("", None):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _cash_sum(rows):
    vals = [_amt(r.amount) for r in rows if r.in_kind != "True"]
    vals = [v for v in vals if v is not None]
    return round(sum(vals), 2) if vals else 0.0


def _all_sum(rows):
    vals = [_amt(r.amount) for r in rows]
    vals = [v for v in vals if v is not None]
    return round(sum(vals), 2) if vals else 0.0


def _filing_conf(cc, ce):
    order = {"high": 3, "medium": 2, "low": 1, "": 0}
    present = [c for c in (cc, ce) if c]
    return min(present, key=lambda c: order.get(c, 0)) if present else "low"


def _reconcile_side(rows, stated, is_text, reconcile_cash_only):
    """Return (itemized_sum_or_None, reconciles_bool_or_None, delta_or_None, confidence, note)."""
    summ = (_cash_sum if reconcile_cash_only else _all_sum)
    if not rows:
        if stated is not None and abs(stated) > 0.005:
            # source printed a total but itemized nothing (legal under-$500 exemption) —
            # cannot verify; leave reconciliation UNKNOWN, do not fabricate a mismatch.
            return None, None, None, "low", "totals-only(no itemization)"
        # $0 (or unknown) side with no rows -> trivially reconciles if stated known
        rec, delta = reconcile.reconciles(0.0, stated)
        conf = reconcile.side_confidence(is_text, rec)
        return (0.0 if stated is not None else None), rec, delta, conf, ""
    s = summ(rows)
    rec, delta = reconcile.reconciles(s, stated)
    if rec is False:
        # Filers are not uniform about whether the printed cover total includes in-kind
        # (Millcreek: Jackson/Clark/Gray include it, Vice/DeSirant print cash-only covers).
        # If the flag-selected sum fails but the OTHER convention matches the printed total,
        # the itemization is verified complete — reconcile under that convention and say so.
        alt = (_all_sum if reconcile_cash_only else _cash_sum)(rows)
        if alt != s:
            arec, adelta = reconcile.reconciles(alt, stated)
            if arec:
                note = ("reconciles including in-kind (cover total counts in-kind)"
                        if reconcile_cash_only else
                        "reconciles cash-only (cover total excludes in-kind)")
                return alt, True, adelta, reconcile.side_confidence(is_text, True), note
    conf = reconcile.side_confidence(is_text, rec)
    return s, rec, delta, conf, ""


import re


def _base_period(label):
    """Period label with amendment/revision words + separators stripped, for grouping an
    amendment with the original it supersedes."""
    s = re.sub(r"\b(amended|amendment|revised|revision)\b", "", label or "", flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _mark_supersessions(pairs, dedup_mode, amend_fn, per_filing_mode=None):
    """pairs = list of (FilingTotals, index_row). Append supersession/amendment notes so a
    cycle total is computable without double-counting (kept + flagged, never dropped).

      * incremental (WJ EasyVote): distinct period reports are SUMMED across the cycle; an
        amendment (or an exact re-file) of the SAME period supersedes the original -> the
        original is noted 'superseded by amendment'. Amendments are noted 'amendment'.
      * cumulative (Lehi Form A/B): each report restates cycle-to-date, so the LATEST report
        per candidate+cycle IS the cycle total and every earlier snapshot is noted 'superseded
        (cumulative snapshot)'.
      * CALLABLE (2026-07-17, the vision-cache cities): `dedup_mode(candidate,
        election_year, members)` -> "cumulative" | "incremental" PER candidate-cycle —
        midvale proved both regimes coexist within one city (2023 filers restate
        cumulative snapshots; 2025 filers file per-period), so a single city-wide string
        marks someone's filings wrongly. The callable's decision group is applied with
        exactly the string modes' logic. String modes are unchanged.
      * PER-FILING (2026-08-02, the county families): `per_filing_mode` = {source_filing ->
        "cumulative"|"incremental"} lets a FAMILY declare the regime it READ OFF EACH FILING
        (cache's 2022+ Summary Page prints both a "This Period" and a "Year-to-Date" column, so
        the regime is a property of the sheet in hand; wasatch's regime varies per candidate on
        one published sheet). A per-filing verdict WINS over the string/callable mode; filings
        with no verdict fall back to it exactly as before. Composition is by PARTITION, then the
        unchanged string logic on each partition — which is the same thing the callable path
        already did, so a city that declares no per-filing regime is bit-identical.
    """
    from collections import defaultdict

    if callable(dedup_mode) or per_filing_mode:
        groups = defaultdict(list)
        for ft, ix in pairs:
            groups[(ft.candidate, ft.election_year)].append((ft, ix))
        cum_pairs, inc_pairs, unmoded = [], [], []
        for (cand, year), members in groups.items():
            grp_mode = (dedup_mode(cand, year, members) if callable(dedup_mode)
                        else dedup_mode)
            for ft, ix in members:
                mode = (per_filing_mode or {}).get(ft.source_filing) or grp_mode
                if mode == "cumulative":
                    cum_pairs.append((ft, ix))
                elif mode:
                    inc_pairs.append((ft, ix))   # historical rule: any other mode = incremental
                else:
                    unmoded.append((ft, ix))     # no regime known at all -> unmarked (honest)
        if cum_pairs:
            _mark_supersessions(cum_pairs, "cumulative", amend_fn)
        if inc_pairs:
            _mark_supersessions(inc_pairs, "incremental", amend_fn)
        return

    def add_note(ft, msg):
        ft.notes = (ft.notes + "; " + msg) if ft.notes else msg

    if dedup_mode == "cumulative":
        groups = defaultdict(list)
        for ft, ix in pairs:
            groups[(ft.candidate, ft.election_year)].append((ft, ix))
        for key, members in groups.items():
            members.sort(key=lambda p: (p[0].filing_date, amend_fn(p[1])))
            for ft, ix in members[:-1]:
                add_note(ft, "superseded (cumulative snapshot; cycle total = latest report)")
            if amend_fn(members[-1][1]):
                add_note(members[-1][0], "amendment")
    elif dedup_mode == "incremental":
        groups = defaultdict(list)
        for ft, ix in pairs:
            groups[(ft.candidate, ft.election_year, _base_period(ft.reporting_period))].append((ft, ix))
        orphan_amends = []
        for key, members in groups.items():
            if len(members) == 1:
                if amend_fn(members[0][1]):
                    orphan_amends.append(members[0])   # amendment with no same-period original yet
                continue
            # amendment(s) present -> they win; originals of the same period are superseded
            members.sort(key=lambda p: (amend_fn(p[1]), p[0].filing_date))
            winner = members[-1]
            for ft, ix in members[:-1]:
                add_note(ft, "superseded by amendment/re-file (same reporting period)")
            if amend_fn(winner[1]):
                add_note(winner[0], "amendment")

        # Fallback: some cities (Sandy) label an amendment DIFFERENTLY from its original
        # ("Amend Aug 28 filing" vs the original "Primary Filing Aug 29"), so the period grouping
        # above can't pair them. Match such an orphan amendment to the UNIQUE same-candidate+cycle
        # NON-amendment filing carrying identical stated totals (both sides, non-zero) and supersede
        # that one — otherwise a naive cycle sum double-counts the amended period. Never matches an
        # all-zero/blank filing (guarded), and only when the match is unique.
        by_cy = defaultdict(list)
        for ft, ix in pairs:
            by_cy[(ft.candidate, ft.election_year)].append((ft, ix))

        def _tot(ft):
            return (ft.stated_total_contributions, ft.stated_total_expenditures)

        for ft, ix in orphan_amends:
            nonzero = any(v not in ("", "0.00") for v in _tot(ft))
            matches = [o for (o, oix) in by_cy[(ft.candidate, ft.election_year)]
                       if o is not ft and not amend_fn(oix)
                       and not any(s.strip().lower().startswith("superseded")
                                   for s in (o.notes or "").split(";"))
                       and _tot(o) == _tot(ft)] if nonzero else []
            if len(matches) == 1:
                add_note(matches[0], "superseded by amendment (matched by identical stated totals)")
                add_note(ft, "amendment")
            else:
                add_note(ft, "amendment (no original recovered)")


def _is_superseded_note(notes):
    """Structural supersession test (same rule as cycle_totals.py): a note ENTRY that
    begins with 'superseded', never an anywhere-substring match."""
    return any(seg.strip().lower().startswith("superseded")
               for seg in (notes or "").split(";"))


def derive_is_incremental(totals, contrib_rows, expend_rows, verbose=True):
    """EMPIRICAL per-candidate `is_incremental` (2026-07-20) — the vineyard/logan/nephi
    row-overlap method, shared so the CONSTANT-BASED cities stop stamping a per-city
    constant on filers it is demonstrably wrong for (the TODO follow-up: is_incremental
    is per-CANDIDATE, not per-city).

    Method (ported from vineyard/logan/nephi `_classify_modes`, generalized to run on the
    driver's PARSED rows instead of per-city cache re-reads, and to pool BOTH sides):
      * group the built FilingTotals per (candidate, election_year); LIVE filings only
        (structurally-superseded ones excluded — an amendment restating its original's
        period must not read as fake cumulative evidence);
      * per consecutive pair of live filings (filing_date order), overlap fraction
        |sig(a) & sig(b)| / |sig(a)| of the (date, amount) row signatures, contributions
        AND expenditures pooled (a cumulative filer re-lists prior rows -> ~1.0; an
        incremental filer lists only new activity -> ~0.0);
      * median >= 0.5 -> the filer is CUMULATIVE ('False'); any other evidence ->
        INCREMENTAL ('True'); NO pair evidence -> rows keep the family/city constant.
    Decisions restamp `is_incremental` on ALL of that candidate-cycle's rows (the flag
    describes the filer's regime). This touches ONLY the row-metadata column: stated
    totals, reconciliation, notes and filing_totals.csv are untouched, so cycle_totals
    (which never reads is_incremental) stays byte-identical — figure corrections still go
    through the documented override files, never through this derivation.
    Returns {(candidate, election_year): "True"|"False"} for evidence-backed cycles."""
    import statistics
    from collections import defaultdict

    by_filing_c, by_filing_e = defaultdict(list), defaultdict(list)
    for r in contrib_rows:
        by_filing_c[r.source_filing].append((r.date, r.amount))
    for r in expend_rows:
        by_filing_e[r.source_filing].append((r.date, r.amount))

    groups = defaultdict(list)
    for ft in totals:
        if not _is_superseded_note(ft.notes):
            groups[(ft.candidate, ft.election_year)].append(ft)

    decisions = {}
    for key, fts in sorted(groups.items()):
        fts.sort(key=lambda f: (f.filing_date, f.source_filing))
        if len(fts) < 2:
            continue
        fracs = []
        for side in (by_filing_c, by_filing_e):
            seqs = [side.get(f.source_filing, []) for f in fts]
            fracs += [len(set(a) & set(b)) / len(set(a))
                      for a, b in zip(seqs, seqs[1:]) if a]
        if not fracs:
            if verbose:
                print(f"  is_incremental[empirical] {key[0]} {key[1]}: no row evidence "
                      f"({len(fts)} live filings) — city constant kept")
            continue
        decisions[key] = "False" if statistics.median(fracs) >= 0.5 else "True"
        if verbose and decisions[key] == "False":
            print(f"  is_incremental[empirical] {key[0]} {key[1]}: False (CUMULATIVE — "
                  f"later reports re-list earlier rows; overlaps "
                  f"{[round(x, 2) for x in fracs]} over {len(fts)} live filings)")

    n_flip = 0
    for r in list(contrib_rows) + list(expend_rows):
        dec = decisions.get((r.candidate, r.election_year))
        if dec is not None and r.is_incremental != dec:
            r.is_incremental = dec
            n_flip += 1
    if verbose:
        n_cum = sum(1 for v in decisions.values() if v == "False")
        print(f"  is_incremental[empirical]: {len(decisions)} candidate-cycles with "
              f"evidence, {n_cum} cumulative, {n_flip} row(s) restamped")
    return decisions


def _fail(msg):
    """Loud, build-stopping failure (the vote_overrides discipline: a stale/unmatched
    override is a data-integrity event, never silently skipped)."""
    raise SystemExit(f"FINANCE-OVERRIDES FATAL: {msg}")


_OV_UNTOUCHABLE = {"extraction_confidence", "needs_review"}


def _load_finance_overrides(path):
    """Read finance_overrides.csv -> (apply_rows, n_documentation_rows). apply_rows are
    (file_line_no, normalized_dict) for rows with mode=apply; every other row (incl. all
    rows of a file without the trailing `mode` column) is a documentation-only record."""
    p = Path(path)
    if not p.exists():
        return [], 0
    with open(p, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    apply_rows, n_doc = [], 0
    for k, r in enumerate(rows, 2):          # header = file line 1
        if (r.get("mode") or "").strip().lower() != "apply":
            n_doc += 1
            continue
        tgt = (r.get("csv") or "").strip().lower()
        if tgt.endswith(".csv"):
            tgt = tgt[:-4]
        if tgt not in ("contributions", "expenditures", "filing_totals"):
            _fail(f"{p.name} line {k}: unknown csv target {r.get('csv')!r}")
        field = (r.get("field") or "").strip()
        if not field:
            _fail(f"{p.name} line {k}: blank field")
        if field in _OV_UNTOUCHABLE:
            _fail(f"{p.name} line {k}: field {field!r} is pipeline-computed and cannot "
                  f"be overridden")
        apply_rows.append((k, dict(r, csv=tgt, field=field)))
    return apply_rows, n_doc


def _apply_row_overrides(overrides, applied, meta, crows, erows, fname):
    """Apply mode=apply contribution/expenditure overrides for THIS filing (matched on
    source_filing + line_no). Runs after normalization, before reconciliation. Stale ->
    _fail. Prints every application."""
    for k, ov in overrides:
        if ov["csv"] == "filing_totals" or ov["source_filing"] != meta["source_filing"]:
            continue
        rows = crows if ov["csv"] == "contributions" else erows
        hits = [r for r in rows if r.line_no == ov["line_no"]]
        if not hits:
            _fail(f"{fname} line {k}: no {ov['csv']} row with source_filing="
                  f"{ov['source_filing']!r} line_no={ov['line_no']!r} (stale override)")
        if len(hits) > 1:
            _fail(f"{fname} line {k}: {len(hits)} rows match line_no={ov['line_no']!r} "
                  f"(ambiguous override)")
        row = hits[0]
        if not hasattr(row, ov["field"]):
            _fail(f"{fname} line {k}: {ov['csv']} has no field {ov['field']!r}")
        cur = getattr(row, ov["field"])
        if cur != (ov.get("old_value") or ""):
            _fail(f"{fname} line {k}: stale override — current {ov['field']}="
                  f"{cur!r} != old_value={ov.get('old_value')!r}")
        setattr(row, ov["field"], ov.get("new_value") or "")
        applied.add(k)
        print(f"OVERRIDE APPLIED [{fname}:{k}] {ov['csv']} {ov['source_filing']} "
              f"line {ov['line_no']}: {ov['field']} {cur!r} -> {ov.get('new_value')!r} "
              f"({(ov.get('reason') or '')[:80]})")


def _apply_ft_overrides(overrides, applied, ft, fname):
    """Apply mode=apply filing_totals overrides for THIS filing (matched on
    source_filing). Reconciliation fields are not recomputed here (documented)."""
    for k, ov in overrides:
        if ov["csv"] != "filing_totals" or ov["source_filing"] != ft.source_filing:
            continue
        if not hasattr(ft, ov["field"]):
            _fail(f"{fname} line {k}: filing_totals has no field {ov['field']!r}")
        cur = getattr(ft, ov["field"])
        if cur != (ov.get("old_value") or ""):
            _fail(f"{fname} line {k}: stale override — current {ov['field']}="
                  f"{cur!r} != old_value={ov.get('old_value')!r}")
        setattr(ft, ov["field"], ov.get("new_value") or "")
        applied.add(k)
        print(f"OVERRIDE APPLIED [{fname}:{k}] filing_totals {ov['source_filing']}: "
              f"{ov['field']} {cur!r} -> {ov.get('new_value')!r} "
              f"({(ov.get('reason') or '')[:80]})")


def _group_index(index_rows, in_scope_fn, group_fn):
    """Group in-scope index rows into FILINGS. Without `group_fn` (every city) each row is its
    own filing and the iteration order is unchanged. With `group_fn(ix) -> key`, rows sharing a
    key become ONE filing, in first-appearance order; a falsy key means "this row stands alone".
    Returns (units, n_skipped) where a unit is a list of index rows."""
    units, by_key, skipped = [], {}, 0
    for ix in index_rows:
        if not in_scope_fn(ix):
            skipped += 1
            continue
        key = group_fn(ix) if group_fn else None
        if not key:
            units.append([ix])
            continue
        if key in by_key:
            by_key[key].append(ix)
        else:
            by_key[key] = [ix]
            units.append(by_key[key])
    return units, skipped


def run(*, here, family_id, index_name="index.csv", aliases_name="donor_aliases.csv",
        meta_fn, sidecar_fn, is_scanned_fn, in_scope_fn=lambda ix: True,
        reconcile_cash_only=False, dedup_mode=None, amend_fn=lambda ix: False,
        rows_override_fn=None, derive_incremental=False,
        group_fn=None, group_primary_fn=None):
    """rows_override_fn(ix, meta) -> a parsed-result dict (same shape a family's parse() returns:
    contrib_rows/expend_rows/stated_*), or None. When it returns a dict, that result is used INSTEAD
    of parsing the OCR/text sidecar — the general hook a city uses to feed a VISION re-transcription
    of a filing that OCR could not reconcile. The overridden rows still flow through the SAME
    normalization + reconciliation + dedup below, so vision output is judged by the identical
    printed-total test. Default None keeps every existing city unchanged.

    MULTI-FILE FILINGS (2026-08-02) — `group_fn(ix) -> key`. Washington County publishes ONE
    logical filing as up to THREE files (a `County Candidate Summary` carrying the reconciliation
    anchor, plus separate `Contributions` and `Expenditures` ledgers), so the printed total and
    the itemized rows it must reconcile against live in DIFFERENT files. When `group_fn` is given,
    index rows sharing a key are parsed as ONE filing: `meta` comes from the PRIMARY row
    (`group_primary_fn(rows) -> ix`, default the first row of the group), and the family is called
    as `family.parse_group(parts, meta)` where each part is
        {"ix": <index row>, "sidecar": <path>, "text": <str>, "is_scanned": <bool>}
    (only parts whose sidecar exists are passed; the group reports MISSING-TEXT only when NONE
    does). A family without `parse_group` falls back to `parse()` on the parts' texts joined by
    form feeds. `group_fn=None` is the default and every existing city takes the identical
    one-row-per-filing path.

    PER-FILING REGIME (2026-08-02) — a family's result dict may carry:
      * `is_incremental`: "True"/"False" -> restamped on that filing's rows (the row-metadata
        column only). Cache's 2022+ Summary Page prints BOTH a This-Period and a Year-to-Date
        column, so the regime is legible per filing rather than assumed per city.
      * `dedup_mode`: "cumulative"|"incremental" -> that filing's supersession regime, which WINS
        over the run-level string/callable `dedup_mode` for that filing only (see
        `_mark_supersessions`). Families that return neither key change nothing.
    """
    here = Path(here)
    family = registry.get(family_id)
    aliases = normalize_donors.load_aliases(str(here / aliases_name))
    ov_name = "finance_overrides.csv"
    ov_rows, ov_docs = _load_finance_overrides(here / ov_name)
    ov_applied = set()

    with open(here / index_name, newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    contrib_all, expend_all, totals_all, report = [], [], [], []
    ft_pairs = []
    per_filing_mode = {}
    units, skipped = _group_index(index_rows, in_scope_fn, group_fn)
    for unit in units:
        ix = (group_primary_fn(unit) if (group_primary_fn and len(unit) > 1) else unit[0])
        is_scanned = is_scanned_fn(ix)
        meta = meta_fn(ix)
        meta["is_scanned"] = is_scanned
        meta.setdefault("extract_method",
                        f"{family_id}/{'ocr' if is_scanned else 'text'}")
        res = rows_override_fn(ix, meta) if rows_override_fn else None
        if res is None and len(unit) > 1:
            parts = []
            for part_ix in unit:
                sc = sidecar_fn(part_ix)
                if not Path(sc).exists():
                    continue
                parts.append(dict(ix=part_ix, sidecar=str(sc),
                                  text=Path(sc).read_text(encoding="utf-8", errors="replace"),
                                  is_scanned=is_scanned_fn(part_ix)))
            if not parts:
                report.append((meta["candidate"], meta["election_year"], "MISSING-TEXT", "", ""))
                continue
            if hasattr(family, "parse_group"):
                res = family.parse_group(parts, meta)
            else:
                res = family.parse("\n\f".join(p["text"] for p in parts), meta)
        if res is None:
            sc = sidecar_fn(ix)
            if not Path(sc).exists():
                report.append((meta["candidate"], meta["election_year"], "MISSING-TEXT", "", ""))
                continue
            text = Path(sc).read_text(encoding="utf-8", errors="replace")
            res = family.parse(text, meta)

        crows, erows = res["contrib_rows"], res["expend_rows"]
        # PER-FILING regime, when the family read one off this filing's own face.
        if res.get("is_incremental") in ("True", "False"):
            for r in list(crows) + list(erows):
                r.is_incremental = res["is_incremental"]
        if res.get("dedup_mode") in ("cumulative", "incremental"):
            per_filing_mode[meta["source_filing"]] = res["dedup_mode"]
        for r in crows:
            normalize_donors.normalize_contrib(r, meta["candidate"], aliases)
        for r in erows:
            normalize_donors.normalize_vendor(r)

        if ov_rows:
            # documented mode=apply corrections: after normalization, before
            # reconciliation, so a corrected amount flows into the printed-total test.
            _apply_row_overrides(ov_rows, ov_applied, meta, crows, erows, ov_name)

        is_text = not is_scanned
        c_sum, rec_c, delta_c, conf_c, note_c = _reconcile_side(
            crows, res.get("stated_contrib"), is_text, reconcile_cash_only)
        e_sum, rec_e, delta_e, conf_e, note_e = _reconcile_side(
            erows, res.get("stated_expend"), is_text, reconcile_cash_only)

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

        flags = []
        if rec_c is False:
            flags.append("contrib!=stated")
        if rec_e is False:
            flags.append("expend!=stated")
        note_bits = [res.get("notes", ""), note_c, note_e] + flags
        notes = "; ".join(b for b in note_bits if b)

        ft = common.FilingTotals(
            candidate=meta["candidate"], office=meta["office"],
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""),
            filing_type=meta.get("filing_type", ""),
            stated_total_contributions=common.money_str(res.get("stated_contrib")),
            stated_total_expenditures=common.money_str(res.get("stated_expend")),
            stated_beginning_balance=common.money_str(res.get("stated_begin")),
            stated_ending_balance=common.money_str(res.get("stated_end")),
            itemized_contrib_sum=("" if c_sum is None else common.money_str(c_sum)),
            itemized_expend_sum=("" if e_sum is None else common.money_str(e_sum)),
            reconciles_contrib=("" if rec_c is None else str(rec_c)),
            reconciles_expend=("" if rec_e is None else str(rec_e)),
            recon_delta_contrib=("" if delta_c is None else f"{delta_c:.2f}"),
            recon_delta_expend=("" if delta_e is None else f"{delta_e:.2f}"),
            self_funded_amount=common.money_str(self_funded),
            n_contrib_rows=str(len(crows)), n_expend_rows=str(len(erows)),
            source_filing=meta["source_filing"], document_id=meta.get("document_id", ""),
            extraction_confidence=_filing_conf(conf_c, conf_e), notes=notes,
            filing_regime=meta.get("filing_regime", ""))

        if ov_rows:
            _apply_ft_overrides(ov_rows, ov_applied, ft, ov_name)

        contrib_all.extend(crows)
        expend_all.extend(erows)
        totals_all.append(ft)
        ft_pairs.append((ft, ix))
        report.append((meta["candidate"], meta["election_year"],
                       ft.reconciles_contrib, ft.reconciles_expend, ft.extraction_confidence))

    unconsumed = [k for k, _ in ov_rows if k not in ov_applied]
    if unconsumed:
        _fail(f"{ov_name} line(s) {unconsumed}: mode=apply override(s) matched NO parsed "
              f"filing (source_filing not in the index / out of scope / not built) — "
              f"stale overrides fail the build")
    if ov_rows or ov_docs:
        print(f"finance_overrides: {len(ov_rows)} applied (mode=apply), "
              f"{ov_docs} documentation-only row(s) (not applied)")

    if dedup_mode or per_filing_mode:
        _mark_supersessions(ft_pairs, dedup_mode, amend_fn, per_filing_mode or None)

    if derive_incremental:
        # AFTER dedup so structurally-superseded filings never feed false cumulative
        # evidence. Row-metadata only; never changes totals/notes/reconciliation.
        derive_is_incremental(totals_all, contrib_all, expend_all)

    _write(here / "contributions.csv", common.CONTRIB_HEADER, contrib_all,
           common.CONTRIB_HEADER_GEO)
    _write(here / "expenditures.csv", common.EXPEND_HEADER, expend_all,
           common.EXPEND_HEADER_GEO)
    _write(here / "filing_totals.csv", common.TOTALS_HEADER, totals_all)
    _print_report(report, contrib_all, expend_all, skipped)
    return dict(contrib=contrib_all, expend=expend_all, totals=totals_all, report=report)


def _write(path, header, rows, geo_header=None):
    """Write the DERIVED CSV. `geo_header` (= header + the trailing optional `geometry` column)
    is used ONLY when at least one row actually carries geometry — so a family that records no
    positional provenance writes the exact historical header, byte for byte. Same
    trailing-optional-column contract as `filing_totals.filing_regime`; `validate_finance.py`
    accepts both shapes."""
    use = header
    if geo_header and any(getattr(r, common.GEOMETRY_COL, "") for r in rows):
        use = geo_header
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=use, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(common.row_to_dict(r))


def _print_report(rep, contrib_all, expend_all, skipped):
    clean = sum(1 for r in rep if len(r) == 5 and r[2] == "True" and r[3] == "True")
    flagged = [r for r in rep if not (len(r) == 5 and r[2] == "True" and r[3] == "True")]
    print(f"filings parsed: {len(rep)}  |  both-sides reconcile: {clean}  |  "
          f"flagged/partial: {len(flagged)}  |  out-of-scope skipped: {skipped}")
    print(f"contribution rows: {len(contrib_all)}  |  expenditure rows: {len(expend_all)}")
    print("\nflagged / not-both-clean:")
    for r in flagged:
        print("   ", " | ".join(str(x) for x in r))
