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
  contributions.csv    the BORN-DIGITAL itemized layer only (TRANCHE 3 Phase A) — see below
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
    meta = dict(candidate=cache.get("candidate_stated") or ix["candidate"],
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
    return rows, misses, contrib_rows, expend_rows, n_bd


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
    rows, misses, crows, erows, n_bd = build()
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
    print("contributions.csv  %3d rows  (the other %d filings are handwritten scans — "
          "NOT transcribed, never 'no donors')" % (len(crows), len(rows) - n_bd))
    print("expenditures.csv   %3d rows" % len(erows))
    if misses:
        print("MISSING vision cache for %d filings: %r" % (len(misses), misses))
    print("byte verification: %s (%d distinct files)" % (
        "OK — all sha256 match" if not bad else "FAILED %r" % bad, nfiles))
