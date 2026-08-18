#!/usr/bin/env python3
"""Weber County campaign finance — module-local STATED-TOTALS builder.

DERIVED layer.  Regenerate with:
    python3 weber_county/campaign_finance/build_finance.py

Inputs (both read-only here):
  index.csv            DERIVED by build_index.py — one row per FILING (196 filings +
                       1 document-grain row); this builder uses the 98 rows whose
                       office_scope == 'county'.
  vision/<key>.json    CURATED — one cache per county-office filing, written by the
                       2026-08-01 cf-vision-transcribe totals tranche.  Cache key is
                       sha1(index.csv `path` + "|" + "<page_start>-<page_end>")[:8]
                       (the repo-wide vision_lib convention plus the nephi/st_george
                       style per-filing discriminator, which Weber needs because one
                       archive PDF holds up to 50 filings).

Outputs (SCHEMA: scripts/campaign_finance/SCHEMA.md §2/§3/§4):
  filing_totals.csv    one row per COUNTY-OFFICE filing (98)
  contributions.csv    the itemized layer — TWO provenances, distinguishable by
                       `extract_method`: `weber_polimorphic/text` (born-digital, Phase A
                       2026-08-02) and `vision-itemized/…` (the scanned handwritten
                       Schedule A/B, Phase B 2026-08-14 — see `vision_itemize` below)
  expenditures.csv     ditto

Why a module-local builder and not the shared engine's `driver.run()`: `driver.run()`
writes all three CSVs from one parse pass, and 93 of Weber's 98 county-office filings
have no machine-readable itemization at all (handwritten Form A/B schedules behind a
vision-transcribed cover).  Their `filing_totals` rows come from `vision/<key>.json`
and are ground truth that must not move.  So the module keeps its own totals builder
and calls the REGISTERED FAMILY (`weber_polimorphic`) for the born-digital subset,
through the same shared normalization + reconciliation primitives the driver uses.
The COLUMN CONTRACT of SCHEMA.md is honored exactly (incl. the optional trailing
`geometry` column, §2a).

THE ITEMIZED LAYER (TRANCHE 3 Phase A, 2026-08-02) — 5 of 98 filings.
  Weber's 2026 cycle contains **5 born-digital Polimorphic e-filings**; every other
  county-office filing is a scan of a handwritten form.  Those 5 are parsed by the
  registered `weber_polimorphic` family from the RETAINED RAW PDF via
  `pdftotext -layout` (never the `text/` sidecars — `format` is `mixed` there, i.e.
  part native text and part tesseract OCR, and a figure must never come off an OCR
  layer).  Detection is by DOCUMENT CONTENT (the "Document generated with
  Polimorphic.com" footer + the "Total Contributions on This Report" summary line),
  never by filename or portal label — the module's own cardinal rule.

  Every emitted row is RECONCILIATION-GATED: a side ships only when its itemized rows
  sum EXACTLY (±$0.01) to the stated total already published in `filing_totals.csv`.
  A side that does not reconcile emits NOTHING and says why in `notes`.  The stated
  totals themselves are NEVER recomputed here — they are the vision/born-digital
  ground truth this build has always published.

  An empty itemized layer on the other 93 filings still means NOT TRANSCRIBED, never
  "no donors" — which is why their `reconciles_*` stay blank (unknown), never False.
"""
import csv
import decimal
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
ENTITY = "weber_county"

CF_LIB = os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance"))
sys.path[:0] = [CF_LIB, os.path.join(CF_LIB, "families")]
import common            # noqa: E402  shared row model + money/geometry primitives
import normalize_donors  # noqa: E402  tier-1 donor/vendor normalization + donor_type
import reconcile         # noqa: E402  the $0.01 printed-total test
import registry          # noqa: E402  form-family dispatch

FAMILY_ID = "weber_polimorphic"

# The two BORN-DIGITAL markers, read from the document itself (never a filename or a
# portal label — see CLAUDE.md "portal labels never set attribution"). A filing is
# handed to the family only when BOTH appear in `pdftotext -layout` of the RAW PDF.
BD_MARKERS = ("Document generated with Polimorphic.com",
              "Total Contributions on This Report")

CONF_RANK = {"high": 3, "medium": 2, "low": 1, "": 0}

CONTRIB_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period",
    "date", "donor_raw", "donor_normalized", "donor_type", "donor_city", "donor_state",
    "donor_district", "amount", "in_kind", "is_incremental", "source_filing",
    "document_id", "line_no", "extraction_confidence", "extract_method", "needs_review",
]
EXPEND_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period",
    "date", "vendor_raw", "vendor_normalized", "purpose", "amount", "in_kind",
    "is_incremental", "source_filing", "document_id", "line_no",
    "extraction_confidence", "extract_method", "needs_review",
]
TOTALS_HEADER = [
    "candidate", "office", "election_year", "filing_date", "reporting_period",
    "filing_type", "stated_total_contributions", "stated_total_expenditures",
    "stated_beginning_balance", "stated_ending_balance", "itemized_contrib_sum",
    "itemized_expend_sum", "reconciles_contrib", "reconciles_expend",
    "recon_delta_contrib", "recon_delta_expend", "self_funded_amount",
    "n_contrib_rows", "n_expend_rows", "source_filing", "document_id",
    "extraction_confidence", "notes", "filing_regime",
]

# report-type phrases that mark a FINAL (post-election / year-end) report.  Derived
# from the verbatim `report_type_stated`; the verbatim string is what goes into
# `reporting_period`, this is only a companion classification.
FINAL_MARKERS = ("final report", "january 4th", "january 5", "january 7th",
                 "december 5", "dec 3", "post- general", "post-general",
                 "30 days after")


def cache_key(path, page_start, page_end):
    return hashlib.sha1(("%s|%s-%s" % (path, page_start, page_end)).encode()).hexdigest()[:8]


def money(s):
    """Parse a VERBATIM stated figure into a decimal, or None when it cannot be parsed
    WITHOUT guessing.  Never repairs a value; an unparseable cell stays None and the
    caller records why.

    Handled, because the source prints them: '$', thousands commas, a trailing bare
    '.', parentheses for negatives, a leading '-'.
    NOT handled on purpose: '-' alone (the filer's nil marker — a dash is not a
    transcribed zero), '' (blank cell), and figures with two decimal points
    ('13.742.18', a period written where a thousands comma belongs) — normalising
    those would be inventing the filer's intent.
    """
    if s is None:
        return None
    t = str(s).strip()
    if t in ("", "-", "--"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    if neg:
        t = t[1:-1]
    t = t.replace("$", "").replace(",", "").replace(" ", "").rstrip(".")
    if t.count(".") > 1:
        return None
    try:
        v = decimal.Decimal(t)
    except decimal.InvalidOperation:
        return None
    return -v if neg else v


def dec_str(v):
    return "" if v is None else str(v)


def load_index():
    with open(D("index.csv"), newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["office_scope"] == "county"]


def stated_contrib(cache):
    """Cumulative-column contributions.

    4-line form (2012/2014): line 1 (donors > $50) + line 2 (aggregate <= $50).  Sum
    only the cells the filer actually printed; if neither parses, the total is blank.
    3-line form (2016+): a single 'total contributions from all donors' line.
    """
    st = cache["stated"]
    if cache.get("form_variant", "4line") == "4line":
        parts = [money(st["contrib_gt50"]["cum"]), money(st["contrib_le50"]["cum"])]
        vals = [p for p in parts if p is not None]
        return (sum(vals) if vals else None,
                ["contrib_gt50", "contrib_le50"])
    return money(st["contrib_all"]["cum"]), ["contrib_all"]


def weakest(cache, fields):
    ranks = [CONF_RANK.get(cache["confidence"].get(f, ""), 0) for f in fields]
    if not ranks:
        return ""
    r = min(ranks)
    for k, v in CONF_RANK.items():
        if v == r:
            return k
    return ""


def filing_type(report_type):
    t = (report_type or "").lower()
    if not t:
        return ""
    return "final" if any(m in t for m in FINAL_MARKERS) else "interim"


def layout_text(path):
    """`pdftotext -layout` of a RETAINED RAW PDF. The born-digital subset is parsed from
    the PDF itself, never from `text/` (those sidecars are `format=mixed` — part native
    text, part tesseract OCR — and a dollar figure must never come off an OCR layer).
    Returns None when poppler is unavailable or the file will not render."""
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout


def is_born_digital(text):
    return bool(text) and all(m in text for m in BD_MARKERS)


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


# =====================================================================================
# THE VISION-ITEMIZED LAYER (TRANCHE 3 Phase B, 2026-08-14) — handwritten Schedule A/B
# =====================================================================================
# The born-digital path below answers "from whom" for the 2026 Polimorphic e-filings.  This
# one answers it for the SCANS: `vision/<key>.json` now carries populated `contributions` /
# `expenditures` lists written by `make_itemized_caches.py` from a transcriber's record, plus
# a `_meta.itemized` block holding the side states, the per-side reconciliation VERDICT and
# the printed ANCHOR that verdict was reached against.
#
# THE ONE THING THAT IS DIFFERENT ON WEBER'S FORM, and the reason this is not a copy of the
# SLCo path: **the cover is CUMULATIVE and some schedules are PERIOD-scoped.**  Weber's cover
# prints three columns (Totals From Last Report | Totals For This Report | Cumulative Report)
# and this module publishes the CUMULATIVE one as `stated_*`.  A filer who restates the whole
# cycle on Form A gives `this == cumulative`, and the schedule reconciles against the
# published figure directly.  A filer who itemizes only the reporting period gives a schedule
# that closes EXACTLY on the *This Report* column while the published cumulative figure
# carries prior periods that this schedule never itemized.  Comparing those two is a BASIS
# ERROR, not a defect, so:
#
#   * `recon.<side>.result = "exact"`        anchor == the published cumulative figure
#                                            -> `reconciles_*` is a real verdict.
#   * `recon.<side>.result = "period-exact"` anchor == the cover's *This Report* column.  Under
#                                            the OWNER-RATIFIED BASIS RULE (2026-08-17) a side
#                                            is reconciled against the printed cover figure
#                                            that MATCHES ITS OWN SCOPE, so once the build
#                                            VERIFIES the sum against the cache's own `this`
#                                            cell this IS a reconciliation: `reconciles_*` =
#                                            True and `recon_delta_*` is stated AGAINST THE
#                                            PERIOD ANCHOR, every row carries
#                                            `is_incremental=True`, and the note carries the
#                                            literal marker `ITEMIZED <side> PERIOD-SCOPED
#                                            (is_incremental=True)` that the shared validator's
#                                            check 6 requires as the declared exception.
#                                            `stated_*` stays the CUMULATIVE column and is
#                                            never recomputed and never differenced.  If the
#                                            build CANNOT verify the claim, both columns stay
#                                            BLANK (honest unknown) and the note says so.
#   * `recon.<side>.result = "delta"`        the rows and the printed anchor disagree — the
#                                            FILER's arithmetic, retained verbatim, never
#                                            adjusted: `reconciles_* = False` with the cause.
#
# Every verdict is RECOMPUTED here from the rows and cross-checked against the transcriber's
# recorded one; a disagreement is printed loudly at build time rather than resolved silently.
# `stated_*` is NEVER recomputed.  An empty side is not a zero: `sides.<side>` distinguishes
# `transcribed` (read, possibly to zero rows = a genuinely blank schedule page),
# `empty-schedule` (the page exists and is blank), `no-schedule-page` (the document has no
# such page — non-existence) and `withheld` (not finished; no rows, no sum claimed).

VISION_METHOD = "vision-itemized"

# SCHEMA.md §6 reserves `high` for a BORN-DIGITAL / structured source. A figure read off a
# rendered page image is the OCR tier however clean the scan and however certain the reader,
# so a vision row is CAPPED at `medium` here — at the build, not in the cache, so the
# transcriber's own per-row claim stays verbatim in `vision/<key>.json` and only the derived
# CSV is made conformant. A transcriber `low` is never raised.
VISION_CONF_CAP = {"high": "medium", "": "medium"}


def _vision_conf(v):
    return VISION_CONF_CAP.get((v or "").strip(), (v or "").strip())


def _vrow_money(v):
    """A verbatim transcribed amount -> Decimal, via the SAME whitelisted repair the totals
    half uses.  Unparseable stays None (blank + needs_review), never guessed."""
    return money(v)


_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_D_NUM = re.compile(r"^(\d{1,2})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{2}|\d{4})$")
_D_MON = re.compile(r"^(\d{1,2})\s*-\s*([A-Za-z]{3})[a-z]*\s*-\s*(\d{2}|\d{4})$")


def iso_date(v):
    """A VERBATIM date as the filer wrote it -> ISO `YYYY-MM-DD`, or ("", verbatim).

    SCHEMA.md §3: `date` is the ledger date normalized to ISO **where cleanly parseable**.
    Two shapes on these forms parse cleanly and unambiguously — `M/D/YY(YY)` (US order, which
    is what the printed column header calls for and what every four-digit-year row on this
    corpus confirms) and `D-Mon-YY`.  A TWO-DIGIT year is expanded 20YY: every Weber county
    filing in this corpus is 2006-2026, so no other century is in play, and the expansion is
    named in the filing's notes rather than done silently.

    Anything else — most importantly a date the filer wrote with NO YEAR at all (`15-Mar`) —
    returns BLANK plus the verbatim, and the caller sets `needs_review=1` and records the
    verbatim.  A year is NEVER filled in from the report date (wave contract), and an
    impossible day is never repaired into a possible one.
    """
    s = (v or "").strip()
    if not s:
        return "", ""
    m = _D_NUM.match(s)
    if m:
        mo, dy, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = _D_MON.match(s)
        if not m:
            return "", s
        dy, mo, yr = int(m.group(1)), _MONTHS.get(m.group(2).lower(), 0), int(m.group(3))
        if not mo:
            return "", s
    if yr < 100:
        yr += 2000
    if not (1 <= mo <= 12) or not (1 <= dy <= 31) or not (1990 <= yr <= 2030):
        return "", s
    return "%04d-%02d-%02d" % (yr, mo, dy), s


def vision_itemize(ix, cache, stated_c, stated_e, aliases):
    """(contrib_rows, expend_rows, ft_patch, notes, warnings) for ONE filing's vision cache.

    No-op (all empties) on a cache with no `_meta.itemized` block — i.e. a filing this wave
    has not transcribed, whose `reconciles_*` therefore stay blank/unknown, never False.
    """
    it = (cache.get("_meta") or {}).get("itemized") or {}
    if not it:
        return [], [], {}, [], []
    sides = it.get("sides") or {}
    recon = {k: ({"result": v} if isinstance(v, str) else (v or {}))
             for k, v in (it.get("recon") or {}).items()}
    notes, warn = [], []
    st = cache["stated"]
    method = VISION_METHOD + "/" + (it.get("wave") or "claude-opus-5")
    # `candidate` on a ROW is an IDENTITY, not a transcription: `validate_finance.py` requires
    # every contributions/expenditures row to join `(candidate, election_year)` back to
    # `index.csv`, and downstream `cf_candidate_person` joins on the same pair.  So the rows
    # carry the INDEX's candidate spelling.  The filer's own verbatim rendering of their name
    # (often all-caps — `JAMES HARRISON HARVEY` for index `James Harrison Harvey`) stays where
    # it is a transcribed FACT: `candidate_stated` in the cache, and the `candidate` column of
    # `filing_totals.csv` that the 2026-08-01 totals tranche published.  Using the stated form
    # on rows broke the index join for all 8 Harvey filings (found 2026-08-14, wave B2).
    meta = dict(candidate=ix["candidate"],
                office=cache.get("office_stated", ""), seat="",
                election_year=ix["election_cycle"],
                filing_date=ix["date"] or cache.get("filing_date_stated", ""),
                reporting_period=cache.get("report_type_stated", ""),
                source_filing=ix["path"], document_id=ix["document_id"],
                extract_method=method)

    crows, erows = [], []
    unparsed_dates = []          # verbatim dates that do NOT resolve to a calendar day

    def _date(row):
        iso, verb = iso_date(row.get("date", ""))
        if verb and not iso:
            unparsed_dates.append(verb)
        return iso

    for i, row in enumerate(cache.get("contributions") or [], 1):
        amt = _vrow_money(row.get("amount"))
        donor = (row.get("donor_raw") or "").strip()
        cr = common.ContribRow(
            **meta, date=_date(row), donor_raw=donor,
            donor_city=row.get("donor_city", ""), donor_state=row.get("donor_state", ""),
            donor_district="",
            amount=(common.money_str(amt) if amt is not None else ""),
            in_kind=("True" if row.get("in_kind") else "False"),
            is_incremental="", line_no=str(row.get("line_no", i)),
            extraction_confidence=_vision_conf(row.get("confidence")),
            needs_review=("1" if (amt is None or not donor or row.get("needs_review")
                                  or (row.get("date") and not iso_date(row.get("date"))[0]))
                          else "0"))
        setattr(cr, common.GEOMETRY_COL, row.get("geometry", ""))
        normalize_donors.normalize_contrib(cr, meta["candidate"], aliases)
        crows.append(cr)
    for i, row in enumerate(cache.get("expenditures") or [], 1):
        amt = _vrow_money(row.get("amount"))
        er = common.ExpendRow(
            **meta, date=_date(row),
            vendor_raw=(row.get("vendor_raw") or "").strip(),
            purpose=row.get("purpose", ""),
            amount=(common.money_str(amt) if amt is not None else ""),
            in_kind=("True" if row.get("in_kind") else "False"),
            is_incremental="", line_no=str(row.get("line_no", i)),
            extraction_confidence=_vision_conf(row.get("confidence")),
            needs_review=("1" if (amt is None or row.get("needs_review")
                                  or (row.get("date") and not iso_date(row.get("date"))[0]))
                          else "0"))
        setattr(er, common.GEOMETRY_COL, row.get("geometry", ""))
        normalize_donors.normalize_vendor(er)
        erows.append(er)

    # ---- THE SCHEDULE-A ANCHOR IS LINE 1, NOT THE PUBLISHED CONTRIBUTIONS TOTAL.
    # Weber's 4-line form (2012/2014 and the older state Schedule A/B family) prints, in
    # black-on-white on the schedule itself: "List all contributions of $50.00 or less as a
    # single aggregate figure."  So Form A / Schedule A itemizes ONLY line 1 (donors > $50),
    # while `stated_total_contributions` published by this module is line 1 + line 2 (the
    # <=$50 AGGREGATE, which the form never requires itemized).  The residual between the
    # transcribed rows and the published total is therefore exactly that aggregate — a
    # STRUCTURAL BASIS DIFFERENCE, not a missing row and not a filer error.  The 3-line form
    # (2016+) prints a single "total contributions from all donors" cell and has no separate
    # aggregate, so there the anchor and the published total are the same figure.
    patch = {}
    keep = {"contributions": crows, "expenditures": erows}
    _4line = cache.get("form_variant", "4line") == "4line"
    _c_anchor_cell = st["contrib_gt50"] if _4line else st["contrib_all"]
    _le50 = money(st["contrib_le50"]["cum"]) if _4line else None
    for side, rows, stated, anchor_cum, this_cell, basis_gap, gap_label, \
            sum_col, rec_col, dl_col, n_col in (
            ("contributions", crows, stated_c, money(_c_anchor_cell["cum"]),
             _c_anchor_cell["this"], _le50,
             "the cover's line-2 aggregate of contributions of $50.00 or less, which the "
             "form explicitly does NOT require itemized",
             "itemized_contrib_sum", "reconciles_contrib", "recon_delta_contrib",
             "n_contrib_rows"),
            ("expenditures", erows, stated_e, stated_e, st["expenditures"]["this"], None, "",
             "itemized_expend_sum", "reconciles_expend", "recon_delta_expend",
             "n_expend_rows")):
        state = sides.get(side, "")
        if state == "withheld":
            reason = (it.get("withheld_reason") or {}).get(side, "reason not recorded")
            notes.append("%s side WITHHELD (no rows emitted, no sum claimed): %s"
                         % (side, reason))
            keep[side] = []
            continue
        if state == "no-schedule-page":
            reason = (it.get("withheld_reason") or {}).get(side, "")
            notes.append("%s: the retained document contains NO schedule page for this side "
                         "— honest NON-EXISTENCE, not a zero and not an untranscribed page%s"
                         % (side, (": " + reason) if reason else ""))
            continue
        if state == "empty-schedule":
            notes.append("%s: the schedule page EXISTS and is BLANK (read, zero rows) — a "
                         "real absence of entries on this filing, not an untranscribed page. "
                         "No sum is claimed against the CUMULATIVE cover figure, which "
                         "carries prior periods this page does not itemize." % side)
            continue
        if state != "transcribed":
            notes.append("%s: side state %r is not a state this build knows — no "
                         "reconciliation claimed." % (side, state))
            continue
        patch[n_col] = str(len(rows))
        # `is_incremental` is STRUCTURAL per side and read off the reconciliation basis, not
        # assumed: a schedule that closes on the This-Report column itemizes ONE PERIOD
        # (incremental); a schedule that closes on the cumulative figure restates the whole
        # cycle (not incremental). Unknown basis stays blank.
        _inc = {"period-exact": "True", "exact": "False", "delta": "False"}.get(
            (recon.get(side) or {}).get("result", ""), "")
        for x in rows:
            x.is_incremental = _inc
        blanks = sum(1 for x in rows if not x.amount)
        if blanks:
            notes.append("%d %s row(s) have an ILLEGIBLE amount — left blank and EXCLUDED "
                         "from the itemized sum, so this side is a FLOOR" % (blanks, side))
        s = round(sum(float(x.amount) for x in rows if x.amount), 2)
        patch[sum_col] = common.money_str(s)
        # IN-KIND IS PER FILER, NOT A FORM PROPERTY (owner-ratified 2026-08-17, established on
        # the summit wave and confirmed on weber 2026-08-18 by Gochnour's 2016 Form A, whose
        # printed total EXCLUDES the in-kind rows it lists while every other weber filer read
        # so far INCLUDES them — the form's own instruction says to include, and filers do not
        # all obey it). So the arithmetic gate has to try BOTH conventions instead of assuming
        # one. `s` is every published row; `s_mon` is the monetary-only subtotal. The
        # monetary-only reading is a FALLBACK, tried only where the all-rows sum fails, and it
        # must still close EXACTLY — nothing is admitted that does not land on a printed
        # figure. `itemized_*_sum` keeps reporting every row that shipped; where the closure
        # was on the monetary subtotal the note names BOTH figures and the convention.
        # NB `in_kind` is already the CSV string form ("True"/"False") on these row objects.
        s_mon = round(sum(float(x.amount) for x in rows
                          if x.amount and str(x.in_kind) != "True"), 2)
        has_ik = abs(s_mon - s) > 0.005
        ik_note = ""
        said = (recon.get(side) or {}).get("result", "")
        detail = (recon.get(side) or {}).get("detail", "")
        anchor = (recon.get(side) or {}).get("anchor", "")
        if said == "period-exact":
            # BASIS DIFFERENCE, not a defect. Verify the claim against the cover's own
            # This-Report cell; publish the sum; leave the cumulative verdict UNKNOWN.
            per = money(this_cell)
            ok = per is not None and abs(s - float(per)) <= 0.01
            # ACCOUNTING PARENTHESES on the EXPENDITURE line are a per-filer presentation, not
            # a sign: Steven Van Wagoner writes every expenditure cell as `(32,960.17)` across
            # all four of his filings (AVAILABILITY §1b records the convention and
            # `filing_totals` stores the parsed SIGNED value verbatim). The schedule's rows are
            # positive outflows, so a magnitude comparison — and ONLY on the expenditures side,
            # and ONLY where the printed cell is negative while the rows are positive — is the
            # faithful test. The note says so wherever it is used; nothing is re-signed.
            paren_abs = False
            if (not ok and side == "expenditures" and per is not None and float(per) < 0
                    and s > 0 and abs(s - abs(float(per))) <= 0.01):
                ok, paren_abs = True, True
            s_used = s
            if not ok and has_ik and per is not None and abs(s_mon - float(per)) <= 0.01:
                ok, s_used = True, s_mon
                ik_note = (" THIS FILER EXCLUDES IN-KIND from the printed total: the closure "
                           "is on the MONETARY-ONLY subtotal %.2f; the in-kind rows are "
                           "published too and `%s` reports all rows (%.2f). In-kind treatment "
                           "is per FILER, not a form property — both conventions were tested "
                           "and only this one lands on a printed figure."
                           % (s_mon, sum_col, s))
            if not ok:
                warn.append("%s %s: transcriber claims period-exact but the rows (%.2f) do "
                            "not close on the cover's This-Report cell (%r)"
                            % (ix["path"], side, s, this_cell))
            if ok:
                # OWNER-RATIFIED BASIS RULE (2026-08-17): a side is reconciled against the
                # printed cover figure that MATCHES ITS OWN SCOPE — the This-Report column for
                # a period-scoped ledger, the Cumulative column for a cumulative one; a figure
                # is NEVER synthesized by differencing covers. This side closed on its own-
                # scope printed figure, so that IS a reconciliation and is published as one,
                # via the shared validator's DECLARED period-basis exception (check 6): every
                # row on the side carries is_incremental=True (set above) and the note carries
                # the literal marker below. `stated_*` remains the CUMULATIVE column and is
                # never recomputed — the delta published here is against the period anchor.
                patch[rec_col] = "True"
                patch[dl_col] = "%.2f" % round(s_used - (abs(float(per)) if paren_abs
                                                       else float(per)), 2)
                notes.append(
                    "ITEMIZED %s PERIOD-SCOPED (is_incremental=True): the schedule is "
                    "PERIOD-scoped behind a CUMULATIVE cover. Its %d rows close EXACTLY on "
                    "the cover's 'Totals For This Report' column (%s), which is the printed "
                    "figure MATCHING THIS LEDGER'S OWN SCOPE, so `reconciles_%s`/"
                    "`recon_delta_%s` are stated against THAT anchor. `stated_%s` is the "
                    "CUMULATIVE column and carries prior periods this schedule never "
                    "itemizes — it is a different figure by design and `%s` must never be "
                    "compared against it. No figure here is derived by differencing covers.%s"
                    % (side, len(rows), (anchor or ("%s" % this_cell)) + (
                           " — printed in ACCOUNTING PARENTHESES by this filer, so the rows "
                           "were closed against its MAGNITUDE; the signed value stays verbatim "
                           "in the cache and in stated_*" if paren_abs else ""),
                       "contrib" if side == "contributions" else "expend",
                       "contrib" if side == "contributions" else "expend",
                       "total_contributions" if side == "contributions"
                       else "total_expenditures",
                       sum_col, ((" " + detail) if detail else "") + ik_note))
            else:
                notes.append(
                    "%s: the transcriber recorded a PERIOD-scoped schedule behind a "
                    "CUMULATIVE cover, but its %d rows do NOT close on the cover's 'Totals "
                    "For This Report' column (%s) — ⚠ BUILD COULD NOT VERIFY THAT CLAIM, so "
                    "`reconciles_*`/`recon_delta_*` stay BLANK (honest unknown) while `%s` "
                    "reports what the page actually says.%s"
                    % (side, len(rows), anchor or ("%s" % this_cell), sum_col,
                       (" " + detail) if detail else ""))
            continue
        if anchor_cum is None:
            notes.append("%s: rows transcribed but the form states no CUMULATIVE anchor for "
                         "this side — reconciliation UNKNOWN, never assumed.%s"
                         % (side, (" " + detail) if detail else ""))
            continue
        # The VERDICT is always taken against the schedule's OWN printed anchor.
        delta = round(s - float(anchor_cum), 2)
        if abs(delta) > 0.01 and has_ik and abs(s_mon - float(anchor_cum)) <= 0.01:
            delta = round(s_mon - float(anchor_cum), 2)
            ik_note = (" THIS FILER EXCLUDES IN-KIND from the printed total: the closure is on "
                       "the MONETARY-ONLY subtotal %.2f; the in-kind rows are published too and "
                       "`%s` reports all rows (%.2f). In-kind treatment is per FILER, not a "
                       "form property — both conventions were tested and only this one lands "
                       "on a printed figure." % (s_mon, sum_col, s))
        mine = "exact" if abs(delta) <= 0.01 else "delta"
        if said and said != mine:
            warn.append("%s %s: transcriber said %r, arithmetic says %r against the schedule "
                        "anchor %s (delta %.2f)"
                        % (ix["path"], side, said, mine, dec_str(anchor_cum), delta))
        # Whether that verdict can be PUBLISHED in `reconciles_*` depends on whether the
        # anchor is the same figure as `stated_*`. Where the form carries a never-itemized
        # <=$50 aggregate, it is not, and a verdict against `stated_*` would be a basis error.
        gapped = basis_gap is not None and abs(float(basis_gap)) > 0.005
        if gapped:
            notes.append(
                "%s: the schedule itemizes ONLY the cover's line 1 (contributions above "
                "$50.00) and its %d rows close on that anchor to %.2f (printed %s, delta "
                "%.2f). `stated_total_contributions` published here is line 1 + line 2 and "
                "additionally carries %s (%s). That residual is STRUCTURAL — the form's own "
                "instruction — so `reconciles_contrib`/`recon_delta_contrib` stay BLANK "
                "rather than record a basis difference as a mismatch.%s"
                % (side, len(rows), s, dec_str(anchor_cum), delta, gap_label,
                   dec_str(basis_gap), (" " + detail) if detail else ""))
            if abs(delta) > 0.01:
                notes.append(
                    "⚠ %s ALSO does not close on its own line-1 anchor: delta %.2f. That part "
                    "is the FILER's arithmetic, retained verbatim, never adjusted%s"
                    % (side, delta, (". " + detail) if detail else ""))
            continue
        patch[dl_col] = "%.2f" % delta
        patch[rec_col] = "True" if abs(delta) <= 0.01 else "False"
        if abs(delta) > 0.01:
            notes.append(
                "%s RECONCILIATION DELTA %.2f (itemized %.2f vs the form's printed %s) — the "
                "FILER's own arithmetic, retained verbatim, NEVER adjusted%s%s"
                % (side, delta, s, dec_str(anchor_cum),
                   (". anchor: " + anchor) if anchor else "",
                   (". " + detail) if detail else ""))
        elif detail or ik_note:
            notes.append("%s reconciles EXACTLY to the printed total. %s%s"
                         % (side, detail, ik_note))

    keep_c, keep_e = keep["contributions"], keep["expenditures"]
    if keep_c:
        patch["self_funded_amount"] = common.money_str(round(sum(
            float(r.amount) for r in keep_c
            if r.donor_type in ("candidate-self", "loan") and r.amount), 2))
    if keep_c or keep_e:
        g = it.get("geometry") or {}
        if g.get("withdrawn"):
            notes.append(
                "ITEMIZED LAYER (VISION, %s): %d contribution / %d expenditure row(s) read off "
                "the rendered handwritten/typed Schedule A/B pages %s at 200 dpi full-page, "
                "with tight-crop escalation for disputed cells (%s escalation(s) on this "
                "filing). ⚠ GEOMETRY WITHDRAWN on this filing: the per-page frame it was "
                "measured from FAILED the 2026-08-17 render-back audit (the stored box did not "
                "reproduce the amount recorded for that row), so the `geometry` column is "
                "BLANK here rather than carrying a pointer that is wrong. The VALUES are "
                "unaffected — they remain gated by the figure this filing itself prints. "
                "Re-measurement is queued. Vision is capped at `medium` confidence "
                "(SCHEMA.md §6)."
                % (it.get("wave", ""), len(keep_c), len(keep_e), it.get("pages_read") or "",
                   it.get("escalations", 0)))
        else:
            notes.append(
                "ITEMIZED LAYER (VISION, %s): %d contribution / %d expenditure row(s) read off "
                "the rendered handwritten/typed Schedule A/B pages %s at 200 dpi full-page, with "
                "tight-crop escalation for disputed cells (%s escalation(s) on this filing). Every "
                "row carries a `pct:` geometry pointer at its amount cell (%s measured from the "
                "page's printed rules, %s hand-measured), and the pointer was verified by "
                "rendering it back off the page. Vision is capped at `medium` confidence "
                "(SCHEMA.md §6)."
                % (it.get("wave", ""), len(keep_c), len(keep_e), it.get("pages_read") or "",
                   it.get("escalations", 0), g.get("measured", 0), g.get("explicit", 0)))
    if unparsed_dates:
        notes.append(
            "DATES: %d row(s) carry a date this form prints WITHOUT A YEAR (or in a shape that "
            "does not resolve to a calendar day) — verbatim %s. Those rows' `date` is BLANK "
            "with `needs_review=1`: a year is NEVER filled in from the report date. Every "
            "other date is the filer's own, normalized to ISO; a two-digit year is expanded "
            "20YY (this corpus is 2006-2026 and no other century is in play)."
            % (len(unparsed_dates), ", ".join(sorted(set(unparsed_dates))[:8])))
    if it.get("notes"):
        notes.append("itemizer: " + str(it["notes"]))
    return keep_c, keep_e, patch, notes, warn


def itemize(ix, cache, stated_c, stated_e, aliases):
    """Parse ONE born-digital filing with the registered family and RECONCILIATION-GATE
    each side against the stated total this module already publishes.

    Returns (contrib_rows, expend_rows, ft_patch, notes) — ft_patch carries ONLY the
    reconciliation columns (itemized sums / reconciles / deltas / self_funded / row
    counts). `stated_*` is never recomputed: the published figure is the ground truth
    and the family's rows must agree with it or they do not ship.
    """
    notes = []
    text = layout_text(D(ix["path"]))
    if not is_born_digital(text):
        return [], [], {}, notes

    fam = registry.get(FAMILY_ID)
    # Row `candidate` is the INDEX spelling — see the identity note in the vision path above.
    # (A no-op for the born-digital 2026 e-filings, whose `candidate_stated` already matches
    # the index verbatim; made explicit so the two row paths cannot drift.)
    meta = dict(candidate=ix["candidate"],
                office=cache.get("office_stated", ""), seat="",
                election_year=ix["election_cycle"],
                filing_date=ix["date"] or cache.get("filing_date_stated", ""),
                reporting_period=cache.get("report_type_stated", ""),
                source_filing=ix["path"], document_id=ix["document_id"],
                extract_method=FAMILY_ID + "/text", is_scanned=False)
    res = fam.parse(text, meta)
    crows, erows = res["contrib_rows"], res["expend_rows"]
    for r in crows:
        normalize_donors.normalize_contrib(r, meta["candidate"], aliases)
    for r in erows:
        normalize_donors.normalize_vendor(r)

    crows = screen_side(crows, "donor_raw", "contributions", notes, FAMILY_ID)
    erows = screen_side(erows, "vendor_raw", "expenditures", notes, FAMILY_ID)

    # GATE 0 — the family's own anchor ("Total … on This Report") must agree with the
    # figure this module already publishes (the CUMULATIVE column). On a first/only
    # report of a cycle the two are the same number; where they diverge the module's
    # published value WINS and no row ships, because reconciling against a different
    # anchor would silently redefine what the published total means.
    out_c, out_e = list(crows), list(erows)
    for side, fam_val, mod_val, rows in (
            ("contributions", res.get("stated_contrib"), stated_c, out_c),
            ("expenditures", res.get("stated_expend"), stated_e, out_e)):
        if not rows:
            continue
        if mod_val is None or fam_val is None or abs(float(mod_val) - fam_val) > 0.005:
            notes.append(
                "ITEMIZED %s WITHHELD: the family's 'on This Report' anchor (%s) is not "
                "the CUMULATIVE figure this module publishes (%s); the published total "
                "governs, so no itemized row is emitted for that side."
                % (side, fam_val, mod_val))
            rows.clear()

    # GATE 1 — the printed-total test, $0.01 tolerance (SCHEMA.md §6).
    patch, keep_c, keep_e = {}, out_c, out_e
    for side, rows, stated, keep_name in (
            ("contrib", out_c, stated_c, "c"), ("expend", out_e, stated_e, "e")):
        if not rows:
            if stated is not None and abs(float(stated)) > 0.005:
                label = ("Itemized %s Report" %
                         ("Contribution" if side == "contrib" else "Expenditures"))
                if label not in text and ("Name of Contributor" in text
                                          if side == "contrib" else
                                          "Person or Organization" in text):
                    notes.append(
                        "%s: reconciliation UNKNOWN. The filing DOES print entry fields, "
                        "but Polimorphic omits the `%s (#n)` block header when a filing "
                        "has a single entry, and `%s` slices records on that header only "
                        "— so the family returns no row. FAMILY LIMITATION, documented "
                        "not patched (the shared engine is frozen this phase); the rows "
                        "are gated out rather than hand-built. Queued for Phase B."
                        % (side, label, FAMILY_ID))
                else:
                    notes.append(
                        "%s: stated total printed but the born-digital face itemizes "
                        "nothing that this family reads — reconciliation UNKNOWN, never "
                        "a fabricated mismatch." % side)
            continue
        s = round(sum(float(r.amount) for r in rows if r.amount), 2)
        rec, delta = reconcile.reconciles(s, None if stated is None else float(stated))
        if rec is not True:
            notes.append(
                "ITEMIZED %s WITHHELD: %d parsed row(s) sum to %.2f against a stated "
                "%s — the side does not reconcile, so NOTHING is emitted (SCHEMA.md §6)."
                % (side, len(rows), s, "blank total" if stated is None else "%.2f" % float(stated)))
            rows.clear()
            continue
        patch["itemized_%s_sum" % ("contrib" if keep_name == "c" else "expend")] = \
            common.money_str(s)
        patch["reconciles_%s" % side] = "True"
        patch["recon_delta_%s" % side] = "%.2f" % delta

    for r in keep_c:
        r.extraction_confidence = "high"
        r.needs_review = r.needs_review or "0"
    for r in keep_e:
        r.extraction_confidence = "high"
        r.needs_review = r.needs_review or "0"

    if keep_c or keep_e:
        patch["n_contrib_rows"] = str(len(keep_c))
        patch["n_expend_rows"] = str(len(keep_e))
        patch["self_funded_amount"] = common.money_str(round(sum(
            float(r.amount) for r in keep_c
            if r.donor_type in ("candidate-self", "loan") and r.amount), 2))
        notes.append("ITEMIZED LAYER: %d contribution / %d expenditure row(s) parsed by "
                     "the registered `%s` family from the RAW born-digital PDF "
                     "(pdftotext -layout), each side reconciled EXACTLY to the stated "
                     "total; per-row `geometry` records the amount cell read."
                     % (len(keep_c), len(keep_e), FAMILY_ID))
    if res.get("notes"):
        notes.append("family: " + res["notes"])
    return keep_c, keep_e, patch, notes


def build():
    rows = []
    misses = []
    contrib_rows, expend_rows = [], []
    aliases = normalize_donors.load_aliases(D("donor_aliases.csv"))
    n_bd = 0
    n_vis = 0
    warnings = []
    for r in load_index():
        key = cache_key(r["path"], r["page_start"], r["page_end"])
        cpath = D("vision", key + ".json")
        if not os.path.exists(cpath):
            misses.append((r["document_id"], key))
            continue
        cache = json.load(open(cpath))
        st = cache["stated"]

        contrib, cfields = stated_contrib(cache)
        expend = money(st["expenditures"]["cum"])
        begin = money(st["ending_balance"]["last"])
        end = money(st["ending_balance"]["cum"])

        notes = [cache.get("notes", "")]

        # filing date: index.csv is authoritative where it has one; where it is blank
        # and the tranche READ a date off the form face, use the read value and say so.
        fdate = r["date"]
        if not fdate and cache.get("filing_date_stated"):
            fdate = cache["filing_date_stated"]
            notes.append("filing_date read from the form face by the 2026-08-01 totals "
                         "tranche; index.csv/filing_attribution.csv carry a blank date "
                         "for this filing (needs_review=1 there).")

        # why a stated figure is blank, when the cache holds a non-empty verbatim
        for label, cell, val in (
            ("contributions", st.get("contrib_all", st.get("contrib_gt50"))["cum"], contrib),
            ("expenditures", st["expenditures"]["cum"], expend),
            ("ending balance", st["ending_balance"]["cum"], end),
        ):
            if val is None and str(cell).strip() not in ("", "-"):
                notes.append("stated %s left BLANK: the form's cumulative cell reads "
                             "%r, which is not a parseable amount and was NOT repaired."
                             % (label, cell))

        notes.append("REGIME: this form is CUMULATIVE (its third column is literally "
                     "'Cumulative Total'), so a candidate-cycle total is the LATEST "
                     "non-superseded report, never a sum of the filings.")
        notes.append("stated_* are the CUMULATIVE column; stated_beginning_balance is "
                     "the ending-balance figure in the 'Totals from Last Report' column.")
        # ---- BORN-DIGITAL itemized layer (TRANCHE 3 Phase A). No-op on the 93 scanned
        # filings: itemize() returns immediately when the raw PDF carries no Polimorphic
        # markers, so their rows/notes/reconciliation columns are byte-unchanged.
        crows, erows, patch, inotes = itemize(r, cache, contrib, expend, aliases)
        if crows or erows or patch or inotes:
            n_bd += 1
        # ---- VISION-ITEMIZED layer (TRANCHE 3 Phase B). No-op on a cache with no
        # `_meta.itemized` block. The two paths are MUTUALLY EXCLUSIVE by construction —
        # a Polimorphic e-filing is machine-readable and is never vision-itemized — and the
        # build asserts that rather than trusting it.
        vc, ve, vpatch, vnotes, vwarn = vision_itemize(r, cache, contrib, expend, aliases)
        if (vc or ve or vpatch) and (crows or erows or patch):
            raise SystemExit(
                "%s: BOTH the born-digital family and a vision cache produced an itemized "
                "layer for this filing. They are different readings of the same pages and "
                "must not be merged; resolve at the source before rebuilding." % r["path"])
        if vc or ve or vpatch or vnotes:
            n_vis += 1
            patch = dict(patch, **vpatch)
            crows, erows = crows + vc, erows + ve
            inotes = inotes + vnotes
            warnings.extend(vwarn)
        contrib_rows.extend(crows)
        expend_rows.extend(erows)
        notes.extend(inotes)

        if not patch:
            notes.append("itemized rows NOT transcribed (cover-page totals tranche) — "
                         "reconciles_* are blank/unknown, never False.")

        rows.append({
            "candidate": cache.get("candidate_stated") or r["candidate"],
            "office": cache.get("office_stated", ""),
            "election_year": r["election_cycle"],
            "filing_date": fdate,
            "reporting_period": cache.get("report_type_stated", ""),
            "filing_type": filing_type(cache.get("report_type_stated", "")),
            "stated_total_contributions": dec_str(contrib),
            "stated_total_expenditures": dec_str(expend),
            "stated_beginning_balance": dec_str(begin),
            "stated_ending_balance": dec_str(end),
            "itemized_contrib_sum": "",
            "itemized_expend_sum": "",
            "reconciles_contrib": "",
            "reconciles_expend": "",
            "recon_delta_contrib": "",
            "recon_delta_expend": "",
            "self_funded_amount": "",
            "n_contrib_rows": "0",
            "n_expend_rows": "0",
            "source_filing": r["path"],
            "document_id": r["document_id"],
            "extraction_confidence": weakest(cache, cfields + ["expenditures", "ending_balance"]),
            "notes": "  ".join(n for n in notes if n),
            "filing_regime": "cumulative",
        })
        rows[-1].update(patch)

    rows.sort(key=lambda x: (x["election_year"], x["office"], x["candidate"],
                             x["filing_date"], x["document_id"]))
    contrib_rows.sort(key=lambda r: (r.source_filing, int(r.line_no or 0)))
    expend_rows.sort(key=lambda r: (r.source_filing, int(r.line_no or 0)))
    write(D("filing_totals.csv"), TOTALS_HEADER, rows)
    write_rows(D("contributions.csv"), CONTRIB_HEADER,
               common.CONTRIB_HEADER_GEO, contrib_rows)
    write_rows(D("expenditures.csv"), EXPEND_HEADER,
               common.EXPEND_HEADER_GEO, expend_rows)
    return rows, misses, contrib_rows, expend_rows, n_bd, n_vis, warnings


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def write_rows(path, header, geo_header, rows):
    """Same trailing-optional-`geometry` contract as the shared driver (SCHEMA.md §2a):
    the column appears only when at least one row actually carries positional
    provenance, so a header-only file keeps its exact historical shape."""
    use = geo_header if any(getattr(r, common.GEOMETRY_COL, "") for r in rows) else header
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=use, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(common.row_to_dict(r))


def verify_bytes():
    """Re-hash every retained file referenced by a county filing row."""
    seen, bad = set(), []
    for r in load_index():
        if r["path"] in seen:
            continue
        seen.add(r["path"])
        p = D(r["path"])
        if not os.path.exists(p):
            bad.append((r["path"], "MISSING"))
            continue
        if hashlib.sha256(open(p, "rb").read()).hexdigest() != r["sha256"]:
            bad.append((r["path"], "SHA MISMATCH"))
    return len(seen), bad


if __name__ == "__main__":
    rows, misses, crows, erows, n_bd, n_vis, warnings = build()
    nfiles, bad = verify_bytes()
    by_cycle = {}
    for r in rows:
        by_cycle.setdefault(r["election_year"], []).append(r)
    print("filing_totals.csv  %3d county-office filings" % len(rows))
    for cyc in sorted(by_cycle):
        rr = by_cycle[cyc]
        nc = sum(1 for x in rr if x["stated_total_contributions"] != "")
        print("   %s  %2d filings   %2d with a stated contribution total" % (cyc, len(rr), nc))
    nrec_c = sum(1 for r in rows if r["reconciles_contrib"] == "True")
    nrec_e = sum(1 for r in rows if r["reconciles_expend"] == "True")
    print("born-digital filings handed to `%s`: %d of %d   "
          "(sides reconciling exactly: %d contrib / %d expend)"
          % (FAMILY_ID, n_bd, len(rows), nrec_c, nrec_e))
    nv_c = sum(1 for r in crows if r.extract_method.startswith(VISION_METHOD))
    nv_e = sum(1 for r in erows if r.extract_method.startswith(VISION_METHOD))
    print("vision-itemized filings (scanned Schedule A/B): %d of %d   "
          "(%d contribution / %d expenditure rows)" % (n_vis, len(rows), nv_c, nv_e))
    print("contributions.csv  %3d rows  (the other %d filings carry no itemized layer — "
          "NOT transcribed, never 'no donors')"
          % (len(crows), len(rows) - n_bd - n_vis))
    print("expenditures.csv   %3d rows" % len(erows))
    for w in warnings:
        print("WARN  verdict disagreement: %s" % w)
    if misses:
        print("MISSING vision cache for %d filings: %r" % (len(misses), misses))
    print("byte verification: %s (%d distinct files)" % (
        "OK — all sha256 match" if not bad else "FAILED %r" % bad, nfiles))
