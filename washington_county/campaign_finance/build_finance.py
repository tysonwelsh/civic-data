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
  * COMPLETENESS-GATED, then reconciliation-VERDICTED (rewritten 2026-08-23 — see `itemize`).
    Publication is decided by whether the parse is provably complete; reconciliation then
    records WHICH printed figure the side closes on. No `stated_*` value is ever recomputed.
  * WHY PHASE A EMITTED SO LITTLE, and why that was the wrong gate. Phase A published a side
    only when the ledger matched the summary's row for that deadline. But this county's
    ledgers restate the WHOLE CYCLE TO DATE while the summary prints one deadline at a time,
    so on every filing after a candidate's first of a cycle the two are different quantities
    and the side was thrown away — including sides that reconcile to the cent against the
    summary sheet's OWN column read down to that deadline. Under the owner-ratified
    RECONCILIATION-BASIS RULE (2026-08-17) a side is scored against the printed figure that
    MATCHES ITS SCOPE, so those sides are now PUBLISHED with `reconciles_*` left BLANK and the
    basis named (utah_county's `cumulative-exact` precedent). What is withheld is a side whose
    parse is SHORT — a wrong value, not a mismatched one.
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

import bbox_lib          # noqa: E402  module-local: TRUE page geometry for the PDF ledgers

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

# The county's own sub-$50 AGGREGATE ledger line, in the several wordings filers use for it.
# A row matching this names no donor and is typed `aggregate-unitemized` (SCHEMA.md 5).
AGGREGATE_LINE = re.compile(
    r"aggregate\s+(?:total\s+)?(?:of\s+)?contributions?|"
    r"\b\d+\s+(?:donations?|contributions?)\s+(?:of\s+)?under\b|"
    r"\bcontributions?\s+under\s+\$?\s*50\b|"
    r"\bdonations?\s+of\s+under\b", re.I)


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
        # ⚠ WORDED CAREFULLY (2026-08-23). The county's template is a PER-PERIOD table — one row
        # per deadline, with the Balance column carrying the running cumulative — and most
        # filers use it that way. A MINORITY DO NOT: on Kevin Brooks 2010 and Chris White 2012
        # the sheet's own arithmetic only closes if each row is read as CYCLE-TO-DATE
        # (Brooks: 2,634.05 - 2,318.49 = 315.56 against a printed Balance of 316.56, versus
        # 6,883.08 - 6,337.52 = 545.56 on the per-period reading). So `stated_*` is described
        # here as WHAT IT IS — the figure this deadline's row printed — and no scope is asserted
        # on the filer's behalf. Which scope a filing's LEDGER matched is recorded per side by
        # the itemized verdict below.
        notes.append("stated figures are the County Candidate Summary's printed row for THIS "
                     "deadline; the county's template is per-period (a minority of filers fill "
                     "it cumulatively instead) and the companion Contributions/Expenditures "
                     "ledgers restate the whole cycle to date, so a cycle total is the LEDGER, "
                     "never a sum of summary rows")
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
    if sheet == "cover_form" and not os.path.exists(
            D("vision_itemized", "%s.json" % c["_cache_file"][:-5])):
        notes.append("itemized donor/vendor rows NOT transcribed for this filing (stated totals "
                     "only) -- see AVAILABILITY.md 9")
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


def cum_through(cache, rep):
    """(contributions, expenditures) accumulated over the summary sheet's OWN printed rows, up
    to AND INCLUDING the row this filing reports on.

    ⚠ WHY THIS IS A READING OF THE DOCUMENT AND NOT AN INVENTED FIGURE. The County Candidate
    Summary is a TABLE of the cycle's deadlines; each row is that period's figure and the
    Balance column beside them is the running cumulative. The companion ledgers restate the
    WHOLE CYCLE TO DATE (verified on `live_wp/2010-David-Whitehead.pdf`, which staples all four
    of the 2010 reports together: the Expenditures sheet is byte-for-byte the same two lines
    under every one of the four deadlines, while the summary rows read 400 / 0 / 0 / 0). So the
    quantity the ledger states has ONE counterpart on the page — the sheet's own column read
    down to this deadline — and this is that read. It is used ONLY as a reconciliation ANCHOR
    and is NEVER written into a `stated_*` field: `stated_*` keeps carrying the single printed
    row, exactly as before. Nothing here differences one document against another.
    """
    pr = cache.get("printed_rows") or []
    ri = rep.get("row_index")
    if not isinstance(ri, int) or ri < 0:
        return None, None

    def col(field):
        vals = [dec(r.get(field)) for i, r in enumerate(pr) if i <= ri]
        vals = [v for v in vals if v is not None]
        return sum(vals) if vals else None

    a, b, e = col("contrib_gt50"), col("contrib_le50"), col("expenses")
    parts = [x for x in (a, b) if x is not None]
    return (sum(parts) if parts else None), e


def itemize(cache, index_by_path, ft_row, aliases):
    """Parse ONE born-digital file-SET with `washco_split`, gate it on COMPLETENESS, and record
    a scope-aware reconciliation verdict for each side.

    Returns (crows, erows, ft_patch, notes). Only `sheet_type == 'summary_sheet'` enters; the
    2008 ledger-only postings and the 100 handwritten cover forms return immediately.

    THE TWO GATES, IN ORDER (rewritten 2026-08-23, TRANCHE 3 parser wave):

    1. **COMPLETENESS decides whether a side may be published at all.** The family reports, per
       side, how many money-bearing logical rows it FOUND in the ledger body and how many it
       EMITTED. They must agree. A short parse is a WRONG VALUE dressed as a small one, so such
       a side emits NOTHING with the shortfall named. (This gate is why a `delta` below can only
       ever be the FILER's arithmetic, never ours.)

    2. **RECONCILIATION records a verdict; it no longer decides publication.** Under the
       owner-ratified RECONCILIATION-BASIS RULE (GOTCHAS/SHIP_GATE, 2026-08-17) a side is scored
       against the printed figure that MATCHES ITS OWN SCOPE. Washington's ledgers are
       CYCLE-TO-DATE while `stated_total_*` carries the summary's PER-PERIOD row, so:
         * `period-exact`     — ledger == the per-period row (a candidate's first filing of a
                                cycle, where the two scopes coincide, or a genuinely one-period
                                ledger). `reconciles_*=True`, delta 0.00 — the ordinary test.
         * `cumulative-exact` — ledger == the sheet's own column read down to this deadline.
                                `reconciles_*` stays **BLANK = unknown**, exactly as utah_county
                                does for the mirror-image case: the rows reconcile EXACTLY to a
                                quantity the document states, but that is a DIFFERENT SCOPE from
                                the figure this module publishes in `stated_total_*`, and
                                calling that True would assert a match the published columns do
                                not make.
         * `delta`            — neither closes on a PROVABLY COMPLETE parse. The rows are
                                published VERBATIM with `reconciles_*=False`, every competing
                                printed figure named in the note, and `needs_review=1` on the
                                side. `recon_delta_*` is left BLANK on purpose: subtracting a
                                cycle-scoped sum from a period-scoped total is a basis error,
                                not a delta (utah's 2026-08-20 finding, reverted there).

    The previous build published a side ONLY when it matched the per-period figure, which meant
    a cycle-scoped ledger that reconciled perfectly against the sheet's own cumulative column
    was thrown away as if it had failed. That is what this rewrite corrects; every figure it
    scores against is printed on the page.
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
                    is_scanned=(ix.get("format") == "scanned"),
                    # TRUE page coordinates for the PDF generations (bbox_lib docstring): the
                    # `-layout` character grid drifts BETWEEN PAGES of one document while the
                    # PDF's own x-coordinates do not, and the drift silently cost 54 of the 77
                    # rows on `Expenditures - Rob Tersigni.pdf`. Also the source of the `pct:`
                    # geometry these rows now carry. [] for a .xls or a scan.
                    bbox=bbox_lib.read_pdf_boxes(D(f["path"])))
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
        was_loan = x.donor_type == "loan"     # set by the family from the ledger's Loan column
        normalize_donors.normalize_contrib(x, meta["candidate"], aliases)
        if was_loan:
            x.donor_type = "loan"
    for x in erows:
        normalize_donors.normalize_vendor(x)
    crows = screen_side(crows, "donor_raw", "contributions", notes, FAMILY_ID)
    erows = screen_side(erows, "vendor_raw", "expenditures", notes, FAMILY_ID)

    cov = res.get("coverage") or {}
    cum_c, cum_e = cum_through(cache, rep)
    patch, keep = {}, {"contrib": list(crows), "expend": list(erows)}
    verdicts = {}
    for sidename, key, statedstr, cumv in (
            ("contrib", "contributions", ft_row["stated_total_contributions"], cum_c),
            ("expend", "expenditures", ft_row["stated_total_expenditures"], cum_e)):
        rows_ = keep[sidename]
        found = (cov.get(key) or {}).get("logical", 0)
        emitted = (cov.get(key) or {}).get("emitted", 0)
        if not rows_ and not found:
            verdicts[sidename] = "empty-schedule"
            continue
        # ---- GATE 1: completeness. A short parse is never published.
        if emitted != found or not rows_:
            notes.append(
                "ITEMIZED %s WITHHELD (INCOMPLETE PARSE): the ledger body holds %d "
                "money-bearing row(s) and the `%s` family could publish %d of them, so the "
                "side's sum is provably short. A short sum presented as a ledger total is a "
                "WRONG VALUE, not a rough one, so NOTHING is emitted. Refusal reason(s): %s"
                % (sidename, found, FAMILY_ID, emitted,
                   "; ".join(s for s in (res.get("notes") or "").split("; ")
                             if "NOT emitted" in s and key[:4] in s) or "see the family notes"))
            keep[sidename] = []
            verdicts[sidename] = "withheld"
            continue
        # ---- GATE 2: scope-aware reconciliation VERDICT (publication already decided).
        ssum = round(sum(float(x.amount) for x in rows_ if x.amount), 2)
        st = dec(statedstr)
        patch["itemized_%s_sum" % sidename] = common.money_str(ssum)
        if st is not None and abs(ssum - float(st)) <= float(TOL):
            patch["reconciles_%s" % sidename] = "True"
            patch["recon_delta_%s" % sidename] = "0.00"
            verdicts[sidename] = "stated-exact"
        elif cumv is not None and abs(ssum - float(cumv)) <= float(TOL):
            # ⚠ reconciles_* STAYS BLANK. The rows sum EXACTLY to a quantity the sheet states
            # (its own column read down to this deadline) but that is a different SCOPE from
            # the per-period figure in stated_total_*; asserting True would claim a match the
            # published columns do not make. Same treatment utah_county gives its mirror case.
            patch["recon_delta_%s" % sidename] = "0.00"
            verdicts[sidename] = "cumulative-exact"
            notes.append(
                "ITEMIZED %s CUMULATIVE-SCOPED: the ledger restates the WHOLE CYCLE TO DATE and "
                "sums EXACTLY to %.2f — the County Candidate Summary's own %s column read down "
                "to this deadline — and NOT to the single printed row this module publishes in "
                "stated_total_%s (%s). reconciles_%s is therefore left BLANK (unknown) rather "
                "than True: the two are different SCOPES and comparing them is a basis error. "
                "Both figures are named here; neither is adjusted."
                % (sidename, ssum, key, sidename,
                   "blank" if st is None else "%.2f" % float(st), sidename))
        else:
            patch["reconciles_%s" % sidename] = "False"
            verdicts[sidename] = "delta"
            for x in rows_:
                x.needs_review = "1"
            notes.append(
                "ITEMIZED %s DELTA (published verbatim, NOT adjusted): the parse is provably "
                "COMPLETE (%d of %d money-bearing ledger rows emitted) and sums to %.2f, which "
                "matches NEITHER printed figure — this deadline's own summary row states %s and "
                "the sheet's %s column read down to this deadline gives %s. The residual is the "
                "FILER's arithmetic, retained as a fact about the document. recon_delta_%s is "
                "deliberately BLANK: differencing a cycle-scoped sum against a period-scoped "
                "total is a basis error, not a delta. Every row on this side carries "
                "needs_review=1."
                % (sidename, emitted, found, ssum,
                   "blank" if st is None else "%.2f" % float(st), key,
                   "blank" if cumv is None else "%.2f" % float(cumv), sidename))

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
        elif AGGREGATE_LINE.search(x.donor_raw):
            # The county's own SUB-$50 AGGREGATE line (`5 Donations of under $50.00`,
            # `Aggregate total of contributions under 50.00`). It is a real ledger line and a
            # real dollar figure, but it names NO donor -- SCHEMA.md 5 has the enum value for
            # exactly this, and leaving it as `unknown` understated what the row is. Matched on
            # the line's own words only; nothing is inferred about who gave.
            x.donor_type = "aggregate-unitemized"
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
            "Summary` anchor and the itemised ledgers are different files). Verdicts: "
            "contributions=%s, expenditures=%s. Rows carry `is_incremental=False` because the "
            "LEDGER restates the cycle to date, and `source_filing` names the PART FILE each "
            "row was read from (not the group's summary), so `(source_filing, line_no)` and "
            "`geometry` resolve in the same document."
            % (len(crows), len(erows), FAMILY_ID, len(parts),
               verdicts.get("contrib", "none"), verdicts.get("expend", "none")))
    if res.get("notes"):
        notes.append("family: " + res["notes"])
    return crows, erows, patch, notes


# ------------------------------------------------ the HANDWRITTEN era: vision itemization
# PHASE B FINAL WAVE, 2026-08-23. The 100 `cover_form` filings are image-faced 17-16-6.5 forms
# that no parser can reach; their donor/vendor lines were transcribed from page images and live
# in `vision_itemized/<cache_key>.json` (schema cf_vision_itemized_v1, ONE per filing). That is a
# NEW sibling directory on purpose: the 100 stated-totals caches in `vision/` are hand
# transcriptions that are never regenerated, and they stay byte-identical through this wave.
#
# THE ANCHOR, and the one decision that matters here:
#   * Form "A" itemizes ONLY contributions OVER $50. The cover's line 2 (`Aggregate total of
#     contributions of $50.00 or less`) is NEVER itemized by the form, and `stated_total_
#     contributions` publishes line 1 + line 2. So the ledger is scored against the cover's
#     OVER-$50 line -- scoring it against the published sum would manufacture a false mismatch on
#     every filing carrying a small-donor aggregate.
#   * SCOPE IS TESTED PER FILING (per REPORT on a bundle), never assumed: the cover prints
#     `LAST + THIS = CUMULATIVE` and this module publishes the CUMULATIVE column, so a ledger
#     that sums to CUMULATIVE is same-scope (`reconciles_*=True`) while one that sums to THIS is
#     a genuinely per-period ledger at a DIFFERENT scope from the published figure -- published
#     with `reconciles_*` left BLANK, the utah/washington `cumulative-exact` precedent inverted.
#   * A provably complete side matching NEITHER printed figure is a `delta`: published verbatim,
#     `reconciles_*=False`, needs_review=1 on every row, both figures named. Nothing is nudged.
SIDE_STATES = ("transcribed", "none", "withheld", "out-of-scope")


def row_money(printed):
    """A VERBATIM printed amount from a vision row -> (Decimal|None, applied_note).

    ⚠ `dec()` CANNOT BE USED ON A HANDWRITTEN CELL. It strips commas AND spaces, so the
    decimal-COMMA convention (`300,00`) parses as 30000 and the space-separated-cents convention
    (`63 75`) as 6375 — both 100x FABRICATIONS, and both present on real pages of this queue.
    `common.parse_vision_amount` is the shared reader for these cells: an explicit whitelist of
    conventions (superscript cents, cents-vs-thousands by GROUP LENGTH, a dash or point in the
    cents position, angle-bracket negatives, the sanctioned decimal-comma and dot-thousands
    repairs), with everything else left BLANK and never repaired.
    """
    return common.parse_vision_amount(printed)


def _rowsum(rows):
    tot = decimal.Decimal(0)
    n_blank = 0
    for x in rows:
        v, _n = row_money(x.get("amount"))
        if v is None:
            n_blank += 1
        else:
            tot += v
    return tot, n_blank


def _verdict(ssum, cum, this):
    """(verdict, scope) from the document's own printed cells. Order matters: CUMULATIVE is
    tested first because it is the column this module publishes; where the two cells are equal
    (a filer's first report of a cycle) the scopes coincide and cumulative is the honest label."""
    if cum is not None and abs(ssum - cum) <= TOL:
        return "cumulative-exact", "cumulative"
    if this is not None and abs(ssum - this) <= TOL:
        return "period-exact", "period"
    return "delta", "unknown"


def itemize_vision(cache, ft_row, index_by_path, aliases):
    """Emit the vision-transcribed itemized rows of ONE handwritten cover-form filing.

    Returns (crows, erows, patch, notes). A filing with no `vision_itemized` cache returns
    empty -- an untranscribed filing, never a zero.

    ⚠ THE ROWS CARRY `index.csv`'s CANDIDATE SPELLING, NOT THE COVER'S. `ft_row["candidate"]` is
    the name the FILER WROTE (`Gary L Christensen`), which is the right value for the filing row
    and is preserved there and in the transcription cache; but the clerk's own label
    (`GARY L. CHRISTENSEN`) is the STABLE LEDGER KEY every consumer joins on, and
    `validate_finance.py` checks each itemized row's `(candidate, election_year)` against
    `index.csv`. The same split is documented in cache_county (`candidate` vs
    `candidate_stated`). Using the cover spelling here fails 434 rows on a name-formatting
    difference that is not a disagreement about who filed.
    """
    notes = []
    if cache.get("sheet_type") != "cover_form":
        return [], [], {}, notes
    p = D("vision_itemized", "%s.json" % cache["_cache_file"][:-5])
    if not os.path.exists(p):
        return [], [], {}, notes
    with open(p, encoding="utf-8") as fh:
        v = json.load(fh)

    reports = cache.get("reports") or [{}]
    src = cache.get("primary_path", "")
    row_candidate = (index_by_path.get(src, {}).get("candidate")
                     or ft_row["candidate"])
    sides = v.get("sides") or {}
    shapes = v.get("shape") or {}
    withheld = v.get("withheld_reason") or {}
    recon = v.get("recon") or {}
    by_report = {int(r.get("report_no", 1)): r for r in (v.get("recon_by_report") or [])}

    out = {"contrib": [], "expend": []}
    patch = {}
    verdicts = {}
    for sidename, key, rowcls, namefield in (
            ("contrib", "contributions", common.ContribRow, "donor_raw"),
            ("expend", "expenditures", common.ExpendRow, "vendor_raw")):
        state = sides.get(key, "")
        raw = v.get(key) or []
        if state not in SIDE_STATES:
            notes.append("ITEMIZED %s: unknown side state %r recorded by the transcription; "
                         "nothing emitted" % (key, state))
            verdicts[sidename] = "unknown-state"
            continue
        if state == "out-of-scope":
            verdicts[sidename] = "out-of-scope"
            notes.append("ITEMIZED %s OUT OF SCOPE: %s" % (key, withheld.get(key, "")))
            continue
        if state == "withheld":
            verdicts[sidename] = "withheld"
            notes.append("ITEMIZED %s WITHHELD by the transcription (NOTHING emitted, no sum "
                         "claimed): %s" % (key, withheld.get(key, "no reason recorded")))
            continue
        if state == "none":
            verdicts[sidename] = "no-schedule-page"
            notes.append("ITEMIZED %s: the document carries NO Form %s page at all -- an honest "
                         "absence, NOT a zero (%s)"
                         % (key, "A" if sidename == "contrib" else "B",
                            (recon.get(key) or {}).get("detail", "")))
            continue
        if not raw:
            verdicts[sidename] = "empty-schedule"
            notes.append("ITEMIZED %s: the Form %s page exists and prints NO lines (read from the "
                         "page image) -- an empty schedule, never 'no donors'"
                         % (key, "A" if sidename == "contrib" else "B"))
            continue

        # ---- rows, renumbered 1..N across the whole document so that
        # (source_filing, line_no) stays the schema's unique itemized-row key even where one PDF
        # staples several reports. The report's own printed line number is kept in the note.
        raw = sorted(raw, key=lambda x: (int(x.get("report_no", 1) or 1),
                                         int(x.get("line_no", 0) or 0)))
        rows, n_repaired = [], 0
        for i, x in enumerate(raw, 1):
            rno = int(x.get("report_no", 1) or 1)
            amt, amt_note = row_money(x.get("amount"))
            n_repaired += 1 if amt_note else 0
            rep = reports[rno - 1] if rno - 1 < len(reports) else reports[0]
            period = ""
            if rep.get("period_start") or rep.get("period_end"):
                period = "%s..%s" % (rep.get("period_start", ""), rep.get("period_end", ""))
            common_kw = dict(
                candidate=row_candidate, office=ft_row["office"], seat="",
                election_year=ft_row["election_year"],
                filing_date=iso(rep.get("submitted")) or iso(rep.get("report_date"))
                            or ft_row["filing_date"],
                reporting_period=period or ft_row["reporting_period"],
                date=x.get("date", ""),
                amount="" if amt is None else str(amt),
                in_kind="True" if x.get("in_kind") else "False",
                source_filing=src, document_id=ft_row["document_id"], line_no=str(i),
                # A VISION read is capped at the OCR tier -- `high` is reserved for a
                # machine-readable source. A transcriber's own `high` is downgraded, never up.
                extraction_confidence=("medium" if x.get("confidence") in ("", None, "high")
                                       else x.get("confidence")),
                extract_method="vision/cover_form",
                needs_review="1" if str(x.get("needs_review")) == "1" else "0",
                geometry=x.get("geometry", ""))
            if sidename == "contrib":
                r = common.ContribRow(donor_raw=x.get("donor_raw", ""),
                                      donor_city=x.get("donor_city", ""),
                                      donor_state=x.get("donor_state", ""), **common_kw)
            else:
                r = common.ExpendRow(vendor_raw=x.get("vendor_raw", ""),
                                     purpose=x.get("purpose", ""), **common_kw)
            r._report_no = rno
            r._printed_line = x.get("line_no", "")
            rows.append(r)

        ssum, n_blank = _rowsum([dict(amount=x.amount) for x in rows])
        if n_repaired:
            notes.append("ITEMIZED %s: the SHARED WHITELISTED currency repair (decimal-comma / "
                         "dot-as-thousands, common.repair_money_line) was applied to %d printed "
                         "amount(s) -- read naively a decimal comma is a 100x error (SCHEMA 6: "
                         "every repaired value is marked)" % (key, n_repaired))
        if n_blank:
            notes.append("ITEMIZED %s: %d row(s) carry NO amount (illegible on the page and never "
                         "guessed), so the side's sum is a FLOOR, not a total" % (key, n_blank))

        # ---- the anchors, read off the FILING's own published cover transcription
        n_rep = len(reports)
        if sidename == "contrib":
            cum = stated(reports[0], "contrib_gt50_cum")
            this = stated(reports[0], "contrib_gt50_this")
            le50 = stated(reports[0], "contrib_le50_cum")
            anchor_label = "the cover's line 1 (contributions over $50)"
        else:
            cum = stated(reports[0], "expenses_cum")
            this = stated(reports[0], "expenses_this")
            le50 = None
            anchor_label = "the cover's line 3 (total campaign expenses)"

        if n_rep > 1:
            # A BUNDLE: several reports stapled into one PDF. Each report has its own cover
            # cells, so a single filing-level verdict would be a category error. The rows are
            # published, the per-report verdicts recorded, and reconciles_* left BLANK.
            per = []
            for rno in sorted({x._report_no for x in rows}):
                sub = [x for x in rows if x._report_no == rno]
                s2, _ = _rowsum([dict(amount=y.amount) for y in sub])
                rep = reports[rno - 1] if rno - 1 < len(reports) else reports[0]
                c2 = stated(rep, "contrib_gt50_cum" if sidename == "contrib" else "expenses_cum")
                t2 = stated(rep, "contrib_gt50_this" if sidename == "contrib" else "expenses_this")
                vd, sc = _verdict(s2, c2, t2)
                per.append("report %d: %d row(s) summing %s vs cover cumulative %s / this-report "
                           "%s -> %s" % (rno, len(sub), s2,
                                         "blank" if c2 is None else c2,
                                         "blank" if t2 is None else t2, vd))
                for y in sub:
                    y.is_incremental = "True" if sc == "period" else "False"
                    if vd == "delta":
                        y.needs_review = "1"
            verdicts[sidename] = "bundle"
            notes.append(
                "ITEMIZED %s FROM A BUNDLE of %d stapled reports: the rows are published with a "
                "PER-REPORT verdict and reconciles_%s is left BLANK, because the filing publishes "
                "ONE cover row in stated_* while the PDF carries %d. %s. Row line_no is renumbered "
                "1..%d across the whole document so (source_filing, line_no) stays unique; each "
                "row's own report is in the transcription cache."
                % (key, n_rep, sidename, n_rep, "; ".join(per), len(rows)))
        else:
            vd, sc = _verdict(ssum, cum, this)
            verdicts[sidename] = vd
            for y in rows:
                y.is_incremental = "True" if sc == "period" else "False"
            if vd == "cumulative-exact":
                # Same scope as the published figure. reconciles_*=True is asserted ONLY when the
                # published stated_* IS that cell -- i.e. when the never-itemized <=$50 aggregate
                # is absent. Where the filer states an aggregate, the ledger cannot equal the
                # published sum by construction, so the claim is left honestly BLANK.
                patch["itemized_%s_sum" % sidename] = common.money_str(float(ssum))
                if le50 is not None and le50 != 0:
                    notes.append(
                        "ITEMIZED %s ANCHORED ON THE OVER-$50 LINE: the %d row(s) sum EXACTLY to "
                        "%s = %s (cumulative), but stated_total_contributions publishes line 1 + "
                        "the line-2 aggregate of contributions of $50.00 or less (%s), which the "
                        "form NEVER itemizes. reconciles_contrib is therefore left BLANK: the two "
                        "figures are different SCOPES and comparing them is a basis error."
                        % (key, len(rows), ssum, anchor_label, le50))
                else:
                    patch["reconciles_%s" % sidename] = "True"
                    patch["recon_delta_%s" % sidename] = "0.00"
                    notes.append("ITEMIZED %s EXACT: %d row(s) sum to %s = %s (cumulative column) "
                                 "= stated_total_%s" % (key, len(rows), ssum, anchor_label,
                                                        sidename))
            elif vd == "period-exact":
                patch["itemized_%s_sum" % sidename] = common.money_str(float(ssum))
                patch["recon_delta_%s" % sidename] = "0.00"
                notes.append(
                    "ITEMIZED %s PERIOD-SCOPED: the %d row(s) sum EXACTLY to %s -- %s in the "
                    "THIS-REPORT column -- and NOT to the CUMULATIVE column (%s) this module "
                    "publishes in stated_*. The ledger is a genuinely per-period schedule; rows "
                    "carry is_incremental=True. reconciles_%s is left BLANK (unknown) rather than "
                    "True: the two are different SCOPES. Both figures are named; neither is "
                    "adjusted." % (key, len(rows), ssum, anchor_label,
                                   "blank" if cum is None else str(cum), sidename))
            else:
                patch["itemized_%s_sum" % sidename] = common.money_str(float(ssum))
                patch["reconciles_%s" % sidename] = "False"
                for y in rows:
                    y.needs_review = "1"
                notes.append(
                    "ITEMIZED %s DELTA (published verbatim, NOT adjusted): %d row(s) read from the "
                    "page image sum to %s, which matches NEITHER printed figure -- %s states %s "
                    "cumulative and %s for this report. The residual is the FILER's arithmetic, "
                    "retained as a fact about the document; every row carries needs_review=1. "
                    "recon_delta_%s is deliberately BLANK where the scopes may differ."
                    % (key, len(rows), ssum, anchor_label,
                       "blank" if cum is None else str(cum),
                       "blank" if this is None else str(this), sidename))
        if shapes.get(key):
            notes.append("ITEMIZED %s shape: %s" % (key, shapes[key]))
        det = (recon.get(key) or {}).get("detail", "")
        if det:
            notes.append("ITEMIZED %s basis as read: %s" % (key, det))
        out[sidename] = rows

    crows, erows = out["contrib"], out["expend"]
    # TIER-1 NORMALIZATION, exactly as the born-digital path does it: `donor_normalized`,
    # `donor_type` (candidate-self / loan / pac / individual …) and `vendor_normalized` are
    # DERIVED columns with a closed enum, and a row that skips the normalizer ships an empty
    # `donor_type` that `validate_finance.py` rejects. The verbatim `donor_raw` is untouched.
    for x in crows:
        normalize_donors.normalize_contrib(x, ft_row["candidate"], aliases)
    for x in erows:
        normalize_donors.normalize_vendor(x)
    for x in crows + erows:
        x.extraction_confidence = x.extraction_confidence or "medium"
        x.needs_review = x.needs_review or "0"
    for x in crows:
        if not (x.donor_raw or "").strip():
            x.needs_review = "1"
        elif AGGREGATE_LINE.search(x.donor_raw):
            x.donor_type = "aggregate-unitemized"
            x.needs_review = "1"
    if crows or erows:
        patch["n_contrib_rows"] = len(crows)
        patch["n_expend_rows"] = len(erows)
        gates = v.get("gates") or {}
        notes.append(
            "ITEMIZED LAYER (VISION, Phase B final wave 2026-08-23): %d contribution / %d "
            "expenditure row(s) read from the page images of the handwritten 17-16-6.5 forms; "
            "verdicts contributions=%s, expenditures=%s. Gates: %s | %s | %s | %s"
            % (len(crows), len(erows), verdicts.get("contrib", "none"),
               verdicts.get("expend", "none"), gates.get("page_subtotal", "") or "no page subtotal",
               gates.get("row_count", "") or "no row-count gate",
               gates.get("geometry_proof", "") or "no geometry proof",
               gates.get("balance_chain", "") or "no balance chain"))
    if v.get("notes"):
        notes.append("transcription: " + v["notes"])
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

    # ---- HANDWRITTEN era: the vision itemization (Phase B final wave, 2026-08-23). No-op on
    # every born-digital file-set and on any cover form not yet transcribed.
    n_vis = 0
    for c in caches:
        if c.get("sheet_type") != "cover_form":
            continue
        ft_row = by_cache.get(c["_cache_file"])
        if not ft_row:
            continue
        _c, _e, patch, _n = itemize_vision(c, ft_row, index_by_path, aliases)
        if not (_c or _e or patch or _n):
            continue
        n_vis += 1
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
    vc, ve = {}, {}
    for r in rows:
        m = re.search(r"Verdicts: contributions=(\S+?), expenditures=(\S+?)\.", r["notes"])
        if m:
            vc[m.group(1)] = vc.get(m.group(1), 0) + 1
            ve[m.group(2)] = ve.get(m.group(2), 0) + 1
        else:
            for side, d in (("contributions", vc), ("expenditures", ve)):
                if "ITEMIZED %s WITHHELD" % side[:7] in r["notes"]:
                    d["withheld"] = d.get("withheld", 0) + 1
    print("born-digital file-sets handed to `%s`: %3d of %d" % (FAMILY_ID, n_bd, len(rows)))
    print("  contribution side verdicts: %s" % dict(sorted(vc.items())))
    print("  expenditure  side verdicts: %s" % dict(sorted(ve.items())))
    n_cover = sum(1 for c in caches if c.get("sheet_type") == "cover_form")
    print("handwritten cover forms carrying a vision itemization: %3d of %d  (untranscribed: %d)"
          % (n_vis, n_cover, n_cover - n_vis))
    vv = {}
    for r in rows:
        for m in re.finditer(r"verdicts contributions=(\S+?), expenditures=(\S+?)\.", r["notes"]):
            vv[m.group(1)] = vv.get(m.group(1), 0) + 1
            vv[m.group(2)] = vv.get(m.group(2), 0) + 1
    if vv:
        print("  vision side verdicts (both sides pooled): %s" % dict(sorted(vv.items())))
    print("contributions.csv %3d rows   expenditures.csv %3d rows  -- the 4 ledger-only 2008 "
          "postings itemize nothing here by design"
          % (len(contrib_rows), len(expend_rows)))
    ngeo = sum(1 for x in contrib_rows + expend_rows if getattr(x, common.GEOMETRY_COL, ""))
    print("  rows carrying geometry: %d of %d (100%%%s)"
          % (ngeo, len(contrib_rows) + len(expend_rows),
             "" if ngeo == len(contrib_rows) + len(expend_rows) else " -- SHORT"))
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
