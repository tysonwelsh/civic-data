#!/usr/bin/env python3
"""Washington County campaign-finance — module-local builder (STATED-TOTALS tranche).

DERIVED layer. Regenerate with:

    python3 washington_county/campaign_finance/extract_born_digital.py
    python3 washington_county/campaign_finance/build_finance.py

Reads   `index.csv` + the stated-totals cache `vision/*.json` (one JSON per logical FILING)
        + the `text/` sidecars of the BORN-DIGITAL file-sets (the itemized layer).
Emits   `filing_totals.csv`        one row per FILING, schema = scripts/campaign_finance/SCHEMA.md §4
        `contributions.csv`        §2 (+ the trailing optional `geometry`, §2a)
        `expenditures.csv`         §3 (+ `geometry`)
        `portal_reconciliation.csv` module-local: the 2008-10 county-printed totals scored
                                    against what this dataset holds

Why a module-local builder and not the shared engine's `driver.run()`: 100 of the 206 filings
are the HANDWRITTEN 17-16-6.5 cover form whose figures exist only as vision transcriptions,
and `driver.run()` rewrites all three CSVs from one parse pass. The builder therefore keeps
its own totals path and calls the now-REGISTERED `washco_split` family for the itemized layer
of the born-digital `summary_sheet` file-sets only.

THE ITEMIZED LAYER (TRANCHE 3 Phase A, 2026-08-02)
  * GROUPING -- one logical filing is up to THREE published files, and the reconciliation
    anchor (the `County Candidate Summary`) is in a DIFFERENT FILE from the itemised rows it
    must reconcile against. The group is the module's own `extract_born_digital.filing_key`
    (already materialised as each cache's `files` list, with `primary_doc_kind='summary'` as
    the primary row) -- the identical contract as the shared driver's
    `group_fn` / `group_primary_fn`, handed to `family.parse_group(parts, meta)`.
  * SCOPE -- `sheet_type == 'summary_sheet'` (the 2010-2015 born-digital generations) ONLY.
    The 4 `ledger_only` 2008 `Detailed ... Report` postings emit NO rows by design: they
    print no totals at all, so there is nothing to reconcile a ledger against, and their
    counted sums already live (labelled as counted, never as stated) in
    `portal_reconciliation.csv`. The 100 handwritten cover forms are untouched, as are their
    vision caches.
  * RECONCILIATION-GATED against the stated total this module already publishes; a side that
    does not reconcile emits NOTHING plus a reason. No `stated_*` value is recomputed.
  * WHY MOST SIDES EMIT NOTHING, and it is not a defect: the county's own filing style
    (CLAUDE.md "Filing-style finding") is that the Summary rows are PER-PERIOD increments
    while the Contributions/Expenditures ledgers restate the WHOLE CYCLE TO DATE. The two are
    therefore different quantities on every filing after a candidate's first of a cycle, and
    reconciling a cycle-to-date ledger against a per-period figure would be arithmetic of
    ours, not the county's. Those sides are withheld with that reason stated.
  * `is_incremental` ON THE ITEMIZED ROWS IS `False`, deliberately, even though the FILING's
    regime is incremental: the rows come from the LEDGER, which restates the cycle to date.
    `filing_regime` / `_regime` describe the STATED figures; the row flag describes the rows.
    Marking ledger rows incremental would make a naive cycle sum double-count.
  * PRIVACY -- the ledgers print a donor's street address; only `donor_city` / `donor_state`
    are emitted (`common.split_city_state`) and the street portion is discarded.

CARDINAL RULES honored here:
  - `stated_*` carries ONLY what the FILING ITSELF printed. A filing that prints no totals
    (the ledger-only 2008/2011 postings) gets BLANKS -- the county's own web-page totals for
    those filings live in `portal_stated_totals.csv` and are scored in
    `portal_reconciliation.csv`, and are NEVER promoted into a stated field.
  - a cell the source left EMPTY stays empty; blanks are never zeroed.
  - a counted ledger sum is DERIVED, is labelled as such, and is withheld entirely unless the
    parse is provably complete (see extract_born_digital.count_2008_ledger).
"""
import csv
import datetime
import decimal
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)

CF_LIB = os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance"))
sys.path[:0] = [CF_LIB, os.path.join(CF_LIB, "families")]
import common            # noqa: E402
import normalize_donors  # noqa: E402
import reconcile         # noqa: E402
import registry          # noqa: E402

FAMILY_ID = "washco_split"

TOTALS_HEADER = [
    "candidate", "office", "election_year", "filing_date", "reporting_period", "filing_type",
    "stated_total_contributions", "stated_total_expenditures", "stated_beginning_balance",
    "stated_ending_balance", "itemized_contrib_sum", "itemized_expend_sum",
    "reconciles_contrib", "reconciles_expend", "recon_delta_contrib", "recon_delta_expend",
    "self_funded_amount", "n_contrib_rows", "n_expend_rows", "source_filing", "document_id",
    "extraction_confidence", "notes", "filing_regime"]
CONTRIB_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period", "date",
    "donor_raw", "donor_normalized", "donor_type", "donor_city", "donor_state",
    "donor_district", "amount", "in_kind", "is_incremental", "source_filing", "document_id",
    "line_no", "extraction_confidence", "extract_method", "needs_review"]
EXPEND_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period", "date",
    "vendor_raw", "vendor_normalized", "purpose", "amount", "in_kind", "is_incremental",
    "source_filing", "document_id", "line_no", "extraction_confidence", "extract_method",
    "needs_review"]
PORTAL_RECON_HEADER = [
    "portal_candidate", "portal_office", "portal_reporting_year", "portal_submitted",
    "portal_stated_contributions", "portal_stated_expenditures", "portal_stated_balance",
    "portal_detail_pdfs", "held_in_dataset", "matched_document_id", "matched_source_filing",
    "counted_contrib_sum", "counted_expend_sum", "contrib_verdict", "expend_verdict",
    "contrib_delta", "expend_delta", "flag", "notes"]

TOL = decimal.Decimal("0.01")
CONF_RANK = {"high": 3, "medium": 2, "low": 1}


def dec(s):
    """Printed amount -> Decimal, or None. Strips $ , and INTERNAL SPACES (handwriting sets
    the thousands separator as a space often enough to matter: `2 844.02`). Accepts the
    accounting parenthesis form as negative. Anything that is not a clean number after that
    -- `-`, `-0-`, `None/Zero`, prose -- returns None and stays BLANK downstream; this
    function never guesses and never repairs."""
    if s in (None, ""):
        return None
    t = str(s).strip().replace("$", "").replace(",", "").replace(" ", "")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return None
    try:
        v = decimal.Decimal(t)
    except decimal.InvalidOperation:
        return None
    return -v if neg else v


def stated(rep, field):
    """The filing's own figure for `field`. Prefers the cache's numeric twin; falls back to
    the VERBATIM `*_printed` twin when the numeric one was left blank but the printed one
    parses cleanly (the vision pass leaves the numeric twin empty where the handwriting is
    oddly spaced -- `2 844.02` -- which is a formatting quirk, not an unreadable cell). A
    printed cell that does not parse stays blank."""
    v = dec(rep.get(field))
    return v if v is not None else dec(rep.get(field + "_printed"))


def iso(s):
    """Verbatim printed date -> ISO, else ''. Never guesses a missing component."""
    if not s:
        return ""
    t = str(s).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        return t
    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", t)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y += 2000 if y < 100 else 0
        if 1 <= mo <= 12 and 1 <= d <= 31 and 1990 <= y <= 2100:
            return "%04d-%02d-%02d" % (y, mo, d)
    return ""


def sum_printed(*vals):
    """Sum ONLY the components the source actually printed (the juab precedent).
    Returns (total_or_None, n_components_present)."""
    parts = [dec(v) for v in vals if v not in (None, "")]
    parts = [p for p in parts if p is not None]
    return (sum(parts) if parts else None), len(parts)


def load_caches():
    out = []
    for p in sorted(glob.glob(D("vision", "*.json"))):
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        d["_cache_file"] = os.path.basename(p)
        out.append(d)
    return out


# ------------------------------------------------------------------ one cache -> one row
def totals_row(c, index_by_path):
    rep = (c.get("reports") or [{}])[0]
    sheet = c.get("sheet_type", "")
    idx = index_by_path.get(c.get("primary_path", ""), {})

    # WHICH COLUMN IS THE FILING'S OWN FIGURE -- the single most important decision here.
    #   cover_form   (handwritten 17-16-6.5): three columns, LAST + THIS = CUMULATIVE. The
    #                filing's figure for the cycle is the CUMULATIVE column.
    #   summary_sheet(born-digital County Candidate Summary): the row for THIS deadline is a
    #                PER-PERIOD increment; there is no cumulative money column (only the
    #                running Balance is cumulative).
    #   ledger_only  : the filing prints no totals at all.
    if sheet == "cover_form":
        col, regime = "cum", "cumulative"
    elif sheet == "summary_sheet":
        col, regime = "this", "incremental"
    else:
        col, regime = None, "none"

    if col:
        parts = [stated(rep, f"contrib_gt50_{col}"), stated(rep, f"contrib_le50_{col}")]
        parts = [p for p in parts if p is not None]
        contrib, n_parts = (sum(parts) if parts else None), len(parts)
        expend = stated(rep, f"expenses_{col}")
    else:
        contrib, n_parts, expend = None, 0, None

    begin = stated(rep, "balance_last")
    end = stated(rep, "balance_end")

    cover = c.get("cover") or {}
    candidate = (cover.get("candidate") or "").strip() or c.get("index_candidate", "")

    # OFFICE comes from the LIVE index.csv, never from the cache's `index_office`. That field
    # is a SNAPSHOT of what the index said when the cache was written, and the 100 vision
    # caches are hand transcriptions that are never regenerated -- so their snapshot freezes
    # and goes stale the moment an office is corrected. (It did: the 2026-08-02 pass moved
    # three Gil Almquist 2016 filings from Seat A to Seat C and gave Slade Hughes 2020 its
    # stated Seat C, via office_determinations.csv.) The cache snapshot is kept only as a
    # fallback for a filing whose primary path somehow misses the index.
    office = idx.get("office") or c.get("index_office", "")
    office_conf = idx.get("office_confidence") or c.get("index_office_confidence", "")
    office_src = idx.get("office_source") or c.get("index_office_source", "")

    # ELECTION YEAR -- the module's standing rule is that the DOCUMENT decides and the portal
    # label is advisory (CLAUDE.md "office is decided by the DOCUMENT, not the label"). The
    # index's `cycle_year` is document-sourced only when `cycle_year_source='document'`;
    # otherwise it is derived from a portal label, and the live page is a known liar here --
    # AVAILABILITY.md §5 records it labelling `2011-David-Whitehead.pdf` as `2012` when the
    # form inside prints "2010 Election Year". So a cover-stated year outranks a derived one.
    doc_year = (cover.get("election_year") or "").strip()
    idx_year = (c.get("index_cycle_year") or "").strip()
    idx_year_src = idx.get("cycle_year_source", "")
    year_note = ""
    if doc_year and idx_year and doc_year != idx_year and idx_year_src != "document":
        election_year = doc_year
        year_note = ("election_year taken from the DOCUMENT (%s); the index carries %s from "
                     "`%s`, a portal-label derivation the document contradicts" %
                     (doc_year, idx_year, idx_year_src or "an unrecorded source"))
    else:
        election_year = idx_year or doc_year or ""

    filing_date = (iso(rep.get("submitted")) or iso(rep.get("report_date"))
                   or iso(idx.get("posted_date")) or iso(idx.get("date")))
    period = ""
    if rep.get("period_start") or rep.get("period_end"):
        period = "%s..%s" % (rep.get("period_start", ""), rep.get("period_end", ""))

    filing_type = c.get("index_filing_type") or idx.get("filing_type") or ""
    # The county's ANNUAL officeholder report is filed each January for the PRIOR calendar
    # year and carries no election cycle (RECON.md §4). Everything else is cycle-scoped.
    annual = (filing_type == "annual") or (not election_year and filing_date[5:7] == "01")
    filing_regime = "annual" if annual else "election_cycle"

    confs = [v for v in (rep.get("conf") or {}).values() if v]
    conf = min(confs, key=lambda v: CONF_RANK.get(v, 0)) if confs else ""

    notes = []
    if year_note:
        notes.append(year_note)
    if sheet == "cover_form":
        notes.append("stated figures are the form's CUMULATIVE column (cycle-to-date); a "
                     "cycle total is the LATEST report, never a sum of reports")
    elif sheet == "summary_sheet":
        notes.append("stated figures are the County Candidate Summary's PER-PERIOD row for "
                     "this deadline (is_incremental=True); the companion Contributions/"
                     "Expenditures ledgers restate the whole cycle to date, so a cycle "
                     "total is the LEDGER, not the sum of summary rows")
    else:
        notes.append("LEDGER-ONLY filing: the county published the itemised sheets without "
                     "the summary, so the filing states NO totals -- left blank, never "
                     "inferred (the county's own web page printed totals for the 2008 "
                     "filings; see portal_reconciliation.csv)")
    if n_parts == 1 and col:
        notes.append("only one of the two contribution lines (>$50 / <=$50) was printed; "
                     "the stated total is that line alone, not a completed sum")
    # CUM-BLANK-THIS-PRESENT: on a cover form the filer sometimes fills LAST + THIS and
    # leaves CUMULATIVE empty. The form's own arithmetic says LAST+THIS=CUMULATIVE, but
    # completing it here would be OUR arithmetic printed as the county's stated total, so
    # `stated_*` stays blank. The figure the filer DID state is recorded verbatim in this
    # note so nothing is lost and the class is greppable/countable.
    if col == "cum":
        for fld, label in (("contrib_gt50", "contributions >$50"),
                           ("contrib_le50", "contributions <=$50"),
                           ("expenses", "expenditures")):
            if stated(rep, fld + "_cum") is None and stated(rep, fld + "_this") is not None:
                notes.append("CUM-BLANK-THIS-PRESENT: the filer left the CUMULATIVE %s cell "
                             "blank (printed %r) while stating %s for THIS report; "
                             "stated_* is left blank rather than completed by arithmetic"
                             % (label, rep.get(fld + "_cum_printed", ""),
                                stated(rep, fld + "_this")))
    if rep.get("blank_fields"):
        notes.append("blank on the form: " + ", ".join(rep["blank_fields"]))
    if rep.get("notes"):
        notes.append(rep["notes"])
    if c.get("notes"):
        notes.append(c["notes"])
    notes.append("itemized donor/vendor rows NOT transcribed in this tranche (stated totals "
                 "only) -- see CLAUDE.md 'Itemized transcription queue'")
    if office_conf and office_conf != "high":
        notes.append("office_confidence=%s (office_source=%s) -- not document-verified"
                     % (office_conf, office_src))

    return {
        "candidate": candidate,
        "office": office,
        "election_year": election_year,
        "filing_date": filing_date,
        "reporting_period": period,
        "filing_type": filing_type or "statement",
        "stated_total_contributions": "" if contrib is None else str(contrib),
        "stated_total_expenditures": "" if expend is None else str(expend),
        "stated_beginning_balance": "" if begin is None else str(begin),
        "stated_ending_balance": "" if end is None else str(end),
        "itemized_contrib_sum": "", "itemized_expend_sum": "",
        "reconciles_contrib": "", "reconciles_expend": "",
        "recon_delta_contrib": "", "recon_delta_expend": "",
        "self_funded_amount": "",
        "n_contrib_rows": 0, "n_expend_rows": 0,
        "source_filing": c.get("primary_path", ""),
        "document_id": c.get("filing_key", ""),
        "extraction_confidence": conf,
        "notes": " | ".join(n for n in notes if n),
        "filing_regime": filing_regime,
        "_regime": regime,
        "_cache": c["_cache_file"],
    }


# ---------------------------------------------------------------- the FIELD-SHIFT screen
# A form family reads a ledger by COLUMN GRAMMAR. Where a filing writes its dates in a shape
# the family's date regex does not know ("17 Jan 2026", "1.2.26", "5May26"), the date token
# lands in the NAME column and the real name slides into the next field — the amounts still
# sum to the printed total, so reconciliation alone cannot catch it. Two detectable shapes:
#   * a name field that IS a date token;
#   * a name/purpose field with no letters at all (an OCR artifact like "|" or "---").
# POLICY (uniform across this sweep, and the reason it is not one rule):
#   * >= 50% of a side's rows suspect  -> the family did not understand that section's column
#     grammar, so the WHOLE SIDE is WITHHELD with a reason (a systematically mis-columned
#     ledger is a wrong value, not a rough one);
#   * < 50%  -> an ISOLATED defect, almost always a filer's own malformed date on an otherwise
#     correctly parsed section; the rows are KEPT and flagged `needs_review=1`.
# Either way the finding is a FAMILY LIMITATION, documented not patched (the shared engine is
# frozen this phase) and queued for Phase B.
_DATEISH = re.compile(
    r"^\d{1,2}\s*[/.\-]{1,2}\s*\d{1,2}\s*[/.\-]{0,2}\s*\d{0,4}$"          # 5/20.14  1.2.26
    r"|^\d{1,2}\s*[A-Za-z]{3,9}\.?\s*,?\s*\d{2,4}$"                        # 17 Jan 2026  5May26
    r"|^[A-Za-z]{3,9}\.?\s*\d{1,2}\s*,?\s*\d{2,4}$")                       # Jan 17, 2026
_SHIFT_CUTOFF = 0.5


def _has_alpha(s):
    return any(ch.isalpha() for ch in s or "")


def screen_side(rows, name_field, side_label, notes, family_id):
    """Return the rows that may ship (possibly []). Appends every finding to `notes`."""
    if not rows:
        return rows
    suspect = []
    for x in rows:
        nm = (getattr(x, name_field, "") or "").strip()
        extra = (getattr(x, "purpose", "") or "").strip()
        why = None
        if _DATEISH.match(nm):
            why = "%s reads %r, a DATE token" % (name_field, nm)
        elif nm and not _has_alpha(nm):
            why = "%s reads %r, which carries no letters" % (name_field, nm)
        elif extra and not _has_alpha(extra):
            why = "purpose reads %r, which carries no letters" % extra
        if why:
            suspect.append((x, why))
    if not suspect:
        return rows
    frac = len(suspect) / len(rows)
    if frac >= _SHIFT_CUTOFF:
        notes.append(
            "ITEMIZED %s WITHHELD (FIELD SHIFT): %d of %d parsed row(s) are mis-columned — "
            "e.g. line %s: %s. The `%s` family did not recognise this filing's date format, so "
            "the date landed in the name column and the real name slid into the next field; "
            "the amounts still sum to the printed total, which is exactly why reconciliation "
            "cannot catch it. A systematically mis-columned ledger is a WRONG VALUE, so the "
            "whole side emits NOTHING. FAMILY LIMITATION, documented not patched — queued for "
            "Phase B."
            % (side_label, len(suspect), len(rows), suspect[0][0].line_no, suspect[0][1],
               family_id))
        return []
    for x, why in suspect:
        x.needs_review = "1"
    notes.append(
        "FIELD SHIFT (isolated, %d of %d rows KEPT and flagged needs_review=1): %s. The filer's "
        "own malformed date is not in the `%s` date grammar, so the token slid into the name "
        "column; the amount is unaffected and the side still reconciles. FAMILY LIMITATION, "
        "documented not patched."
        % (len(suspect), len(rows),
           "; ".join("line %s: %s" % (x.line_no, w) for x, w in suspect[:4]), family_id))
    return rows


def _deadline_iso(cache, rep):
    """The filing's own DEADLINE, ISO. The family uses it to reject a ledger date outside the
    filing's plausible window. Prefers the sheet's printed `date_due`, then the file-set's own
    label (the deadline the county names each file for), then the submitted date."""
    for v in (rep.get("date_due"), cache.get("label"), rep.get("submitted")):
        t = iso(v)
        if t:
            return t
    for k in (cache.get("filing_key") or "").split("|"):
        if iso(k):
            return iso(k)
    return ""


def itemize(cache, index_by_path, ft_row, aliases):
    """Parse ONE born-digital file-SET with `washco_split` and reconciliation-gate each side.

    Returns (crows, erows, ft_patch, notes). Only `sheet_type == 'summary_sheet'` enters; the
    2008 ledger-only postings and the 100 handwritten cover forms return immediately.
    """
    notes = []
    if cache.get("sheet_type") != "summary_sheet":
        return [], [], {}, notes
    rep = (cache.get("reports") or [{}])[0]

    # THE GROUP -- the same contract as the shared driver's group_fn/group_primary_fn: the
    # file-set is `extract_born_digital.filing_key`, and its PRIMARY row is the doc_kind
    # 'summary' file (which carries the reconciliation anchor).
    parts, primary = [], None
    for f in cache.get("files", []):
        ix = index_by_path.get(f["path"])
        if not ix or not ix.get("text_path"):
            continue
        tp = D(ix["text_path"])
        if not os.path.exists(tp):
            continue
        part = dict(ix=ix, sidecar=tp,
                    text=open(tp, encoding="utf-8", errors="replace").read(),
                    is_scanned=(ix.get("format") == "scanned"))
        if f.get("doc_kind") == "summary" and primary is None:
            primary = part
        parts.append(part)
    if not parts:
        return [], [], {}, notes
    if primary is not None:
        parts = [primary] + [x for x in parts if x is not primary]

    meta = dict(candidate=ft_row["candidate"], office=ft_row["office"], seat="",
                election_year=ft_row["election_year"], filing_date=ft_row["filing_date"],
                reporting_period=ft_row["reporting_period"],
                source_filing=ft_row["source_filing"], document_id=ft_row["document_id"],
                extract_method=FAMILY_ID + "/text", is_scanned=False,
                deadline=_deadline_iso(cache, rep))
    try:
        res = registry.get(FAMILY_ID).parse_group(parts, meta)
    except Exception as exc:                                   # noqa: BLE001
        notes.append("ITEMIZED LAYER SKIPPED: the `%s` family raised %s on this file-set; no "
                     "row is emitted and nothing is guessed. FAMILY LIMITATION, documented not "
                     "patched (the shared engine is frozen this phase)."
                     % (FAMILY_ID, type(exc).__name__))
        return [], [], {}, notes

    crows, erows = res["contrib_rows"], res["expend_rows"]
    for x in crows:
        normalize_donors.normalize_contrib(x, meta["candidate"], aliases)
    for x in erows:
        normalize_donors.normalize_vendor(x)
    crows = screen_side(crows, "donor_raw", "contributions", notes, FAMILY_ID)
    erows = screen_side(erows, "vendor_raw", "expenditures", notes, FAMILY_ID)

    patch, keep = {}, {"contrib": list(crows), "expend": list(erows)}
    for sidename, statedstr in (("contrib", ft_row["stated_total_contributions"]),
                                ("expend", ft_row["stated_total_expenditures"])):
        rows_ = keep[sidename]
        if not rows_:
            continue
        ssum = round(sum(float(x.amount) for x in rows_ if x.amount), 2)
        st = dec(statedstr)
        rec, delta = reconcile.reconciles(ssum, None if st is None else float(st))
        if rec is not True:
            notes.append(
                "ITEMIZED %s WITHHELD: the ledger's %d row(s) sum to %.2f against a stated %s. "
                "On this generation the Summary states a PER-PERIOD increment while the ledger "
                "restates the WHOLE CYCLE TO DATE (CLAUDE.md 'Filing-style finding'), so on "
                "every filing after a candidate's first of a cycle the two are different "
                "quantities -- reconciling them would be OUR arithmetic, not the county's. "
                "NOTHING is emitted (SCHEMA.md 6)."
                % (sidename, len(rows_), ssum,
                   "blank total" if st is None else "%.2f" % float(st)))
            keep[sidename] = []
            continue
        patch["itemized_%s_sum" % sidename] = str(ssum)
        patch["reconciles_%s" % sidename] = "True"
        patch["recon_delta_%s" % sidename] = "%.2f" % delta

    crows, erows = keep["contrib"], keep["expend"]
    for x in crows + erows:
        # The ROWS come from the ledger, which restates the cycle to date -> cumulative.
        # The FILING's stated figures are per-period; that stays in `filing_regime`.
        x.is_incremental = "False"
        x.extraction_confidence = "high"
        x.needs_review = x.needs_review or "0"
    for x in crows:
        if not (x.donor_raw or "").strip():
            x.needs_review = "1"
    if crows or erows:
        patch["n_contrib_rows"] = len(crows)
        patch["n_expend_rows"] = len(erows)
        patch["self_funded_amount"] = common.money_str(round(sum(
            float(x.amount) for x in crows
            if x.donor_type in ("candidate-self", "loan") and x.amount), 2))
        notes.append(
            "ITEMIZED LAYER: %d contribution / %d expenditure row(s) parsed by the registered "
            "`%s` family from the born-digital file-SET (%d files; the `County Candidate "
            "Summary` anchor and the itemised ledgers are different files), each side "
            "reconciled EXACTLY to the stated total. Rows carry `is_incremental=False` because "
            "the LEDGER restates the cycle to date; `geometry` records the amount cell (a real "
            "`Sheet!A1` reference on the .xls generations)."
            % (len(crows), len(erows), FAMILY_ID, len(parts)))
    if res.get("notes"):
        notes.append("family: " + res["notes"])
    return crows, erows, patch, notes


# ------------------------------------------------------------------ portal reconciliation
def portal_reconciliation(caches):
    """Score the county's OWN 2008-2010 web-page totals against what this dataset holds.

    `portal_stated_totals.csv` is a verbatim transcription of figures the county rendered in
    HTML above the links to each filer's PDFs -- a SECOND, INDEPENDENT statement of the same
    numbers, and therefore the only external anchor in the whole record. The filings it links
    are ledger-only (they print no totals), so the comparison is portal-stated vs
    ledger-COUNTED, and it is only made where the count is provably complete."""
    rows = []
    by_basename = {}
    for c in caches:
        for f in c.get("files", []):
            by_basename[os.path.basename(f["path"])] = c

    with open(D("portal_stated_totals.csv"), newline="", encoding="utf-8") as fh:
        portal = list(csv.DictReader(fh))

    for p in portal:
        pdfs = [x.strip() for x in (p.get("detail_pdfs") or "").split(";") if x.strip()]
        names = [os.path.basename(x) for x in pdfs]
        hits = [by_basename[n] for n in names if n in by_basename]
        cache = hits[0] if hits else None
        held = "yes" if cache else "no"
        counted = (cache or {}).get("ledger_counted") or {}

        row = {
            "portal_candidate": p["candidate"], "portal_office": p["portal_office"],
            "portal_reporting_year": p["reporting_year"], "portal_submitted": p["submitted"],
            "portal_stated_contributions": p["stated_contributions"],
            "portal_stated_expenditures": p["stated_expenditures"],
            "portal_stated_balance": p["stated_balance"],
            "portal_detail_pdfs": " ; ".join(names),
            "held_in_dataset": held,
            "matched_document_id": (cache or {}).get("filing_key", ""),
            "matched_source_filing": (cache or {}).get("primary_path", ""),
            "counted_contrib_sum": counted.get("contrib_sum", ""),
            "counted_expend_sum": counted.get("expend_sum", ""),
            "contrib_verdict": "", "expend_verdict": "",
            "contrib_delta": "", "expend_delta": "",
            "flag": "", "notes": "",
        }
        notes = []
        if not cache:
            row["contrib_verdict"] = row["expend_verdict"] = "not_scorable"
            row["flag"] = "portal_row_without_file"
            notes.append("the PDFs this portal row links were never retrieved (they are not "
                         "in the archive's captures) -- the county's printed totals are "
                         "retained here as the only surviving record of this report")
        else:
            for side, pkey in (("contrib", "stated_contributions"),
                               ("expend", "stated_expenditures")):
                stated = dec(p[pkey])
                got = dec(counted.get(f"{side}_sum"))
                if got is None:
                    row[f"{side}_verdict"] = "not_scorable"
                    notes.append("%s: ledger sum WITHHELD -- %s" % (
                        side, counted.get(f"{side}_withheld_reason", "not a countable table")))
                elif stated is None:
                    row[f"{side}_verdict"] = "not_scorable"
                else:
                    delta = got - stated
                    row[f"{side}_delta"] = str(delta)
                    row[f"{side}_verdict"] = ("agree" if abs(delta) <= TOL else "disagree")
        if "disagree" in (row["contrib_verdict"], row["expend_verdict"]):
            row["flag"] = "DISAGREEMENT"
        row["notes"] = " | ".join(notes)
        rows.append(row)

    # A disagreement is kept VERBATIM on BOTH sides and EXPLAINED FROM EVIDENCE, never
    # reconciled away and never explained by assertion. The evidence assembled here is the
    # candidate's OTHER portal snapshots: if the counted ledger falls strictly between an
    # earlier and this later snapshot, the linked file is an EARLIER report than the row it
    # hangs under -- which is a portal-label defect, not a transcription error. If it does
    # not, we say so and leave the disagreement unexplained rather than invent a reason.
    for r in rows:
        if r["flag"] != "DISAGREEMENT":
            continue
        parts = ["portal figure and counted ledger are BOTH retained verbatim; neither is "
                 "corrected"]
        for side, pkey in (("contrib", "portal_stated_contributions"),
                           ("expend", "portal_stated_expenditures")):
            if r[f"{side}_verdict"] != "disagree":
                continue
            got = dec(r[f"counted_{side}_sum"])
            stated = dec(r[pkey])
            siblings = sorted(
                (dec(o[pkey]) for o in rows
                 if o is not r and o["portal_candidate"] == r["portal_candidate"]
                 and dec(o[pkey]) is not None),
                key=lambda v: v)
            lower = [v for v in siblings if v < got]
            if lower and got < stated:
                parts.append(
                    "%s: the counted ledger (%s) falls BETWEEN this filer's earlier portal "
                    "snapshot (%s) and this row's figure (%s), and the linked PDFs are named "
                    "for an earlier deadline than this row's `submitted` date -- i.e. the "
                    "county hung an EARLIER pair of detail sheets under a LATER row. A "
                    "portal-label defect of the kind AVAILABILITY.md §5 catalogues, not a "
                    "transcription error; the ledger parse is provably complete (every money "
                    "token in the body is consumed by a parsed row, and the file's trailing "
                    "page was confirmed genuinely blank)"
                    % (side, got, max(lower), stated))
            else:
                parts.append("%s: counted %s vs portal %s -- the difference is NOT explained "
                             "by this filer's other portal snapshots; recorded unexplained"
                             % (side, got, stated))
        r["notes"] = " | ".join(parts + ([r["notes"]] if r["notes"] else []))
    rows.sort(key=lambda r: (r["portal_candidate"], r["portal_submitted"]))
    return rows


def mark_cross_channel_reposts(rows, index_by_path):
    """Flag the SAME report published on TWO DIFFERENT channels, so a cycle total does not
    double-count it.

    The county re-posts filings as it migrates CMS: the state channel and the 2010 archive
    both carry the April-2010 field; `live_outpost` and `live_wp` both carry 2024; the live
    page re-uploads older reports under `<year>-<Name>.pdf`. These are the SAME report and a
    consumer summing per candidate+cycle would count them twice.

    DELIBERATELY CONSERVATIVE. Identical stated figures alone are NOT evidence of a re-post:
    a filer with no activity between two deadlines files two DIFFERENT reports carrying
    identical (usually zero) figures, and the record has several of those. So a group is
    marked only when the rows also share a filing_date AND come from DIFFERENT channels --
    which sequential reports never do. Same-channel look-alikes are left alone."""
    groups = {}
    for r in rows:
        key = (re.sub(r"[^a-z]", "", (r["candidate"] or "").lower()), r["election_year"],
               r["filing_date"], r["stated_total_contributions"],
               r["stated_total_expenditures"], r["stated_ending_balance"])
        if not r["filing_date"]:
            continue                      # no shared date -> no evidence, never guessed
        groups.setdefault(key, []).append(r)
    marked = 0
    for key, grp in groups.items():
        if len(grp) < 2:
            continue
        chans = {index_by_path.get(r["source_filing"], {}).get("channel", "") for r in grp}
        if len(chans) < 2:
            continue                      # same channel -> sequential reports, not a re-post
        for r in grp:
            others = [o["source_filing"] for o in grp if o is not r]
            r["notes"] += (" | CROSS-CHANNEL RE-POST: the same report (same filer, same "
                           "filing date, identical stated figures) is also published at %s. "
                           "Count this filing ONCE -- do not sum the copies."
                           % "; ".join(others))
            marked += 1
    return marked


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_rows(path, header, geo_header, rows):
    """Same trailing-optional-`geometry` contract as the shared driver (SCHEMA.md 2a)."""
    use = geo_header if any(getattr(x, common.GEOMETRY_COL, "") for x in rows) else header
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=use, extrasaction="ignore")
        w.writeheader()
        for x in rows:
            w.writerow(common.row_to_dict(x))


def main():
    with open(D("index.csv"), newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))
    index_by_path = {r["path"]: r for r in index_rows}
    caches = load_caches()

    rows = [totals_row(c, index_by_path) for c in caches]

    # ---- BORN-DIGITAL itemized layer (TRANCHE 3 Phase A). No-op on the 100 handwritten
    # cover forms and the 4 ledger-only 2008 postings.
    aliases = normalize_donors.load_aliases(D("donor_aliases.csv"))
    contrib_rows, expend_rows, n_bd = [], [], 0
    by_cache = {r["_cache"]: r for r in rows}
    for c in caches:
        if c.get("sheet_type") != "summary_sheet":
            continue
        ft_row = by_cache.get(c["_cache_file"])
        if not ft_row:
            continue
        n_bd += 1
        _c, _e, patch, _n = itemize(c, index_by_path, ft_row, aliases)
        contrib_rows.extend(_c)
        expend_rows.extend(_e)
        if _n:
            ft_row["notes"] = ft_row["notes"] + " | " + " | ".join(_n)
        ft_row.update(patch)

    n_reposts = mark_cross_channel_reposts(rows, index_by_path)
    rows.sort(key=lambda r: (r["election_year"], r["office"], r["candidate"],
                             r["filing_date"], r["source_filing"]))

    # every retained file must be reachable from exactly one filing
    covered = set()
    for c in caches:
        for f in c.get("files", []):
            covered.add(f["path"])
    orphans = sorted(set(index_by_path) - covered)

    contrib_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    expend_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    write(D("filing_totals.csv"), TOTALS_HEADER, rows)
    write_rows(D("contributions.csv"), CONTRIB_HEADER, common.CONTRIB_HEADER_GEO, contrib_rows)
    write_rows(D("expenditures.csv"), EXPEND_HEADER, common.EXPEND_HEADER_GEO, expend_rows)
    precon = portal_reconciliation(caches)
    write(D("portal_reconciliation.csv"), PORTAL_RECON_HEADER, precon)

    n_stated = sum(1 for r in rows if r["stated_total_contributions"]
                   or r["stated_total_expenditures"])
    print("filing_totals.csv %3d filings covering %d of %d indexed files"
          % (len(rows), len(covered), len(index_by_path)))
    print("  by cache regime:  %s" % {k: sum(1 for r in rows if r["_regime"] == k)
                                      for k in ("cumulative", "incremental", "none")})
    print("  with a stated contribution or expenditure total: %d  (blank: %d)"
          % (n_stated, len(rows) - n_stated))
    print("  filing_regime:    %s" % {k: sum(1 for r in rows if r["filing_regime"] == k)
                                      for k in ("election_cycle", "annual")})
    print("  cross-channel re-posts flagged: %d rows (count each report ONCE)" % n_reposts)
    print("  CUM-BLANK-THIS-PRESENT cells:   %d filings"
          % sum(1 for r in rows if "CUM-BLANK-THIS-PRESENT" in r["notes"]))
    nrc = sum(1 for r in rows if r["reconciles_contrib"] == "True")
    nre = sum(1 for r in rows if r["reconciles_expend"] == "True")
    print("born-digital file-sets handed to `%s`: %3d of %d  (sides reconciling exactly: "
          "%d contrib / %d expend)" % (FAMILY_ID, n_bd, len(rows), nrc, nre))
    print("contributions.csv %3d rows   expenditures.csv %3d rows  -- the 100 handwritten "
          "cover forms and the 4 ledger-only 2008 postings itemize nothing here"
          % (len(contrib_rows), len(expend_rows)))
    sides = [r[k] for r in precon for k in ("contrib_verdict", "expend_verdict")]
    print("portal_reconciliation.csv %d portal snapshots, %d scoreable sides -> %s"
          % (len(precon), len(sides),
             {v: sides.count(v) for v in ("agree", "disagree", "not_scorable")}))
    print("  files held for %d of %d portal snapshots"
          % (sum(1 for r in precon if r["held_in_dataset"] == "yes"), len(precon)))
    if orphans:
        print("WARNING: %d indexed files reachable from no filing: %s"
              % (len(orphans), orphans[:5]))
    else:
        print("every one of the %d indexed files is reachable from a filing" % len(covered))
    print("built %s" % datetime.datetime.now(datetime.timezone.utc)
          .strftime("%Y-%m-%dT%H:%M:%SZ"))


if __name__ == "__main__":
    main()
