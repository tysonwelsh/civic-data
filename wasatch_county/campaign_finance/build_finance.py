#!/usr/bin/env python3
"""Wasatch County campaign finance — module-local builder for the STATED-TOTALS layer.

DERIVED. Regenerate with:  python3 wasatch_county/campaign_finance/build_finance.py

Inputs (both curated / verbatim, never generated here):
  index.csv        one row per retained filing (built by build_index.py)
  vision/<key>.json  one curated cache per filing — the 2026-08-01 vision transcription of
                     the filing's COVER PAGE: office block, reporting-period boxes, and EVERY
                     stated total the sheet prints, each cell with its own confidence.
                     `<key>` = sha1(index.csv `path`)[:8] (the repo-wide convention,
                     scripts/campaign_finance/vision_lib.cache_key).

Outputs (SCHEMA.md column contract, headers exact):
  filing_totals.csv   one row per filing (111) — §4 + the optional trailing `filing_regime`
  contributions.csv   §2 (+ the optional trailing `geometry`) — the BORN-DIGITAL Table-A layer
  expenditures.csv    §3 (+ `geometry`) — the BORN-DIGITAL Table-B layer

Why a module-local builder: every `stated_*` figure here is a CURATED vision transcription, and
`driver.run()` would rewrite all three CSVs from one parse pass. `wasatch_disclosure_tableab` IS
now registered in the shared library, so this builder keeps the vision-based stated totals and
calls that family for the ITEMIZED layer of the Table A/B subset only.

THE ITEMIZED LAYER (TRANCHE 3 Phase A, 2026-08-02)
  * SUBSET SELECTION is `_meta.form_variant_vision == "wasatch_disclosure_tableab"` — the
    VISION-read variant, **never the statute header**: the 2024 vintage of this sheet still
    cites 17-16-6.5 (only 2026 cites 17-70-4), which mis-filed 6 rows until `build_index.py`
    was corrected on 2026-08-01. The two older sheets (carr_5_5_pg_4line, wasatch_fcr_3line)
    are cumulative three-column forms and are NOT this family.
  * Every emitted side is RECONCILIATION-GATED against the stated total this module already
    publishes; a side that does not reconcile emits NOTHING plus a reason. Stated totals are
    never recomputed from the itemization — the vision figure governs, and where the family
    reads a different cover figure the divergence is RECORDED, not resolved.
  * GARBLED COVERS STAY BLANK: the family refuses to turn `$ f -7 DD.oo` into a number, so
    those filings emit no row and say so. Their real figures live in `vision/`.
  * MULTI-REPORT PDFs: one published PDF may bind SEVERAL reports (Spencer Park's 2024-11 file
    holds two). The family reads ONE face per parse, so every report after the first is GATED
    OUT with a reason and flagged for Phase B — never merged into the first report's totals.

────────────────────────────────────────────────────────────────────────────────────────
THE TWO REGIMES (this is the whole point of the `filing_regime` column)

`cumulative` — the older county sheets (2010 + 2022 Carr 5-5-PG four-line; 2018 + 2020
  Wasatch three-line). Each prints THREE columns: TOTALS FROM LAST REPORT + TOTALS FOR THIS
  REPORT = CUMULATIVE REPORT. A candidate's cycle figure is the LATEST report, never a sum.
  `is_incremental` for any itemized rows built later = False.

`period`    — the newer CAMPAIGN FINANCIAL DISCLOSURE / Table A-B sheet (2024 + 2026). One
  TOTALS column, scoped to the report's own checked period ("Covering Sep 26 to Oct 24").
  A cycle figure is a SUM across periods. `is_incremental` = True.
  ⚠ Several filers restate cumulatively on this sheet anyway (Kaiserman 2024, Rowland 2026,
  Farrell 2026 all repeat their prior report's totals verbatim) — the per-filing `notes`
  say so. Read the notes before summing a candidate's period filings.

COLUMN SELECTION on the cumulative sheets (deterministic, documented, never a guess):
  1. use the CUMULATIVE column when it prints a figure;
  2. else, if the LAST REPORT column is blank / 0 / 'N/A' (i.e. nothing precedes this
     report), promote the THIS REPORT figure and say so in `notes`;
  3. else leave the stated total BLANK and record in `notes` which column the filer used.
On the four-line Carr sheet a contribution total is line 1 (>$50) + line 2 (aggregate <=$50),
summing ONLY the cells the filer actually printed (juab precedent). A cell that is not a
number ('N/A', a dash, an up-arrow 'see above' mark) is BLANK, never zero.

`stated_ending_balance` is carried VERBATIM (parentheses, stray '$', the Forsyth 2026
parenthetical prose) — it is not a computed field and SCHEMA.md does not constrain it.
`stated_total_contributions` / `stated_total_expenditures` are normalized to decimal strings
because the validator requires that; the verbatim string always remains in the cache.

itemized_* / reconciles_* / recon_delta_* / self_funded_amount stay BLANK on every filing the
itemized pass did not reach or could not reconcile — a blank reconciliation is "unknown", never
a fabricated match (SCHEMA.md §6), and an empty itemized side never means "no donors".
"""
import csv
import decimal
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
ENTITY = "wasatch_county"

CF_LIB = os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance"))
sys.path[:0] = [CF_LIB, os.path.join(CF_LIB, "families")]
import common            # noqa: E402
import normalize_donors  # noqa: E402
import reconcile         # noqa: E402
import registry          # noqa: E402

FAMILY_ID = "wasatch_disclosure_tableab"
FAMILY_VARIANT = "wasatch_disclosure_tableab"   # the VISION-read variant, never the statute

TOTALS_HEADER = [
    "candidate", "office", "election_year", "filing_date", "reporting_period", "filing_type",
    "stated_total_contributions", "stated_total_expenditures", "stated_beginning_balance",
    "stated_ending_balance", "itemized_contrib_sum", "itemized_expend_sum",
    "reconciles_contrib", "reconciles_expend", "recon_delta_contrib", "recon_delta_expend",
    "self_funded_amount", "n_contrib_rows", "n_expend_rows", "source_filing", "document_id",
    "extraction_confidence", "notes", "filing_regime",
]
CONTRIB_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period", "date",
    "donor_raw", "donor_normalized", "donor_type", "donor_city", "donor_state", "donor_district",
    "amount", "in_kind", "is_incremental", "source_filing", "document_id", "line_no",
    "extraction_confidence", "extract_method", "needs_review",
]
EXPEND_HEADER = [
    "candidate", "office", "seat", "election_year", "filing_date", "reporting_period", "date",
    "vendor_raw", "vendor_normalized", "purpose", "amount", "in_kind", "is_incremental",
    "source_filing", "document_id", "line_no", "extraction_confidence", "extract_method",
    "needs_review",
]

CONTRIB_LINES = {"carr_5_5_pg_4line": ["contrib_gt50", "contrib_le50"],
                 "wasatch_fcr_3line": ["total_contributions"],
                 "wasatch_disclosure_tableab": ["total_contributions"]}
EXPEND_LINE = {"carr_5_5_pg_4line": "total_expenses",
               "wasatch_fcr_3line": "total_expenses",
               "wasatch_disclosure_tableab": "total_expenditures"}
CONF_RANK = {"high": 3, "medium": 2, "low": 1, "": 0}


def money(s):
    """Verbatim printed amount -> Decimal, or None when the cell is not a number.
    Handles '$1,050.00', '2,500', '-$2,137.36', '$-753.04', '(331.75)'. 'N/A', a dash and an
    empty cell all return None — a non-number is a BLANK, never a zero. EXCEPTION (owner
    ruling 2026-08-02): glyphs that DENOTE the digit zero — a slashed zero 'Ø', '-0-', or the
    written word 'zero' — parse as 0 (they are the filer writing zero, not a nil mark)."""
    if s is None:
        return None
    t = str(s).strip()
    if not t:
        return None
    if t.lower() in ("ø", "-0-", "zero"):
        return decimal.Decimal("0.00")
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    t = t.replace("$", "").replace(",", "").replace(" ", "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return None
    v = decimal.Decimal(t)
    return -v if neg else v


def is_nothing_before(cellval):
    """True when the LAST REPORT column carries nothing that precedes this report:
    blank, an explicit 'N/A', or zero."""
    t = (cellval or "").strip()
    if t == "" or t.upper() in ("N/A", "NA", "-", "--"):
        return True
    v = money(t)
    return v is not None and v == 0


def pick(stated, line, regime):
    """-> (Decimal|None, verbatim str, confidence, column_used)"""
    cells = stated.get(line)
    if not cells:
        return None, "", "", ""
    if regime == "period":
        c = cells["period"]
        return money(c["value"]), c["value"], c["confidence"], "period"
    cum, last, this = cells["cumulative"], cells["last_report"], cells["this_report"]
    if money(cum["value"]) is not None:
        return money(cum["value"]), cum["value"], cum["confidence"], "cumulative"
    if is_nothing_before(last["value"]) and money(this["value"]) is not None:
        return money(this["value"]), this["value"], this["confidence"], "this_report(promoted)"
    return None, cum["value"], "", "cumulative(blank)"


def side(stated, lines, regime):
    """Sum the printed cells of one side. Returns (total|None, confidence, columns_used)."""
    vals, confs, cols = [], [], []
    for ln in lines:
        v, _verb, conf, col = pick(stated, ln, regime)
        cols.append(col)
        if v is not None:
            vals.append(v)
            confs.append(conf)
    if not vals:
        return None, "", cols
    weakest = min(confs, key=lambda c: CONF_RANK.get(c, 0))
    return sum(vals), weakest, cols


def load():
    idx = list(csv.DictReader(open(D("index.csv"), newline="", encoding="utf-8")))
    out = []
    for r in idx:
        key = hashlib.sha1(r["path"].encode()).hexdigest()[:8]
        p = D("vision", key + ".json")
        if not os.path.exists(p):
            raise SystemExit("FAIL: no vision cache for %s (expected vision/%s.json)"
                             % (r["path"], key))
        out.append((r, key, json.load(open(p))))
    return out


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


_REPORT_TITLE = "CAMPAIGN FINANCIAL DISCLOSURE"


def itemize(r, key, variant, stated_c, stated_e, aliases):
    """Parse ONE born-digital Table A/B filing and RECONCILIATION-GATE each side against the
    stated total this module already publishes. Returns (crows, erows, ft_patch, notes)."""
    notes = []
    if variant != FAMILY_VARIANT:
        return [], [], {}, notes
    tp = D(r["text_path"]) if r.get("text_path") else ""
    if not tp or not os.path.exists(tp):
        return [], [], {}, notes
    text = open(tp, encoding="utf-8", errors="replace").read()

    n_reports = text.upper().count(_REPORT_TITLE)
    if n_reports > 1:
        notes.append("MULTI-REPORT PDF: this published file binds %d `%s` reports. The `%s` "
                     "family reads ONE face per parse, so only the FIRST report is read here "
                     "and reports 2..%d are GATED OUT — their figures and Table A/B rows are "
                     "NOT in this dataset and are NOT merged into the first report's totals. "
                     "Flagged for Phase B."
                     % (n_reports, _REPORT_TITLE.title(), FAMILY_ID, n_reports))

    fam = registry.get(FAMILY_ID)
    meta = dict(candidate=r["candidate"], office=r["office"], seat=r.get("seat", ""),
                election_year=r["election_year"], filing_date=r.get("date", ""),
                reporting_period=r.get("reporting_period", ""), source_filing=r["path"],
                document_id="wasatch-cf-" + key, extract_method=FAMILY_ID + "/text",
                is_scanned=False)
    res = fam.parse(text, meta)
    crows, erows = res["contrib_rows"], res["expend_rows"]
    for x in crows:
        normalize_donors.normalize_contrib(x, meta["candidate"], aliases)
    for x in erows:
        normalize_donors.normalize_vendor(x)

    # The family reads the cover INDEPENDENTLY of the vision transcription. The vision figure
    # governs; a disagreement is recorded, never resolved by taking the parser's number.
    for label, fam_val, mod_val in (("contributions", res.get("stated_contrib"), stated_c),
                                    ("expenditures", res.get("stated_expend"), stated_e)):
        fv = None if fam_val is None else round(float(fam_val), 2)
        mv = None if mod_val in (None, "") else round(float(mod_val), 2)
        if fv is not None and fv != mv:
            notes.append("COVER DIVERGENCE (%s): the `%s` family reads %s off the sheet where "
                         "the vision transcription published %s; the VISION figure governs and "
                         "nothing was changed." % (label, FAMILY_ID, fv, mv))
        elif fv is None and mv is not None:
            notes.append("The `%s` family could not read the %s cover cell (garbled or absent "
                         "on the text layer); the vision transcription's %s stands." 
                         % (FAMILY_ID, label, mv))

    crows = screen_side(crows, "donor_raw", "contributions", notes, FAMILY_ID)
    erows = screen_side(erows, "vendor_raw", "expenditures", notes, FAMILY_ID)
    for x in crows:
        if not (x.donor_raw or "").strip():
            x.needs_review = "1"          # blank name = the form printed none (honest)
    for x in erows:
        if not (x.vendor_raw or "").strip():
            x.needs_review = "1"

    patch, keep = {}, {"contrib": list(crows), "expend": list(erows)}
    for sidename, stated in (("contrib", stated_c), ("expend", stated_e)):
        rows_ = keep[sidename]
        if not rows_:
            continue
        ssum = round(sum(float(x.amount) for x in rows_ if x.amount), 2)
        st = None if stated in (None, "") else float(stated)
        rec, delta = reconcile.reconciles(ssum, st)
        if rec is not True:
            notes.append("ITEMIZED %s WITHHELD: %d parsed row(s) sum to %.2f against the "
                         "published stated %s — the side does not reconcile, so NOTHING is "
                         "emitted (SCHEMA.md §6)."
                         % (sidename, len(rows_), ssum,
                            "blank total" if st is None else "%.2f" % st))
            keep[sidename] = []
            continue
        patch["itemized_%s_sum" % sidename] = str(ssum)
        patch["reconciles_%s" % sidename] = "True"
        patch["recon_delta_%s" % sidename] = "%.2f" % delta

    crows, erows = keep["contrib"], keep["expend"]
    for x in crows + erows:
        x.extraction_confidence = "high"
        x.needs_review = x.needs_review or "0"
    if crows or erows:
        patch["n_contrib_rows"] = len(crows)
        patch["n_expend_rows"] = len(erows)
        patch["self_funded_amount"] = common.money_str(round(sum(
            float(x.amount) for x in crows
            if x.donor_type in ("candidate-self", "loan") and x.amount), 2))
        notes.append("ITEMIZED LAYER: %d Table-A / %d Table-B row(s) parsed by the registered "
                     "`%s` family from the born-digital text layer, each side reconciled "
                     "EXACTLY to the published stated total; per-row `geometry` records the "
                     "amount cell read." % (len(crows), len(erows), FAMILY_ID))
    if res.get("notes"):
        notes.append("family: " + res["notes"])
    return crows, erows, patch, notes


def build(rows):
    tot = []
    contrib_rows, expend_rows = [], []
    aliases = normalize_donors.load_aliases(D("donor_aliases.csv"))
    n_bd = 0
    for r, key, doc in rows:
        m, stated = doc["_meta"], doc["stated"]
        variant, regime = m["form_variant_vision"], m["filing_regime"]
        c_tot, c_conf, c_cols = side(stated, CONTRIB_LINES[variant], regime)
        e_tot, e_conf, e_cols = side(stated, [EXPEND_LINE[variant]], regime)
        bal = stated.get("balance_end", {})
        bal_v = bal.get("period", bal.get("cumulative", {})).get("value", "")
        if regime == "cumulative" and not bal_v:
            # honour the same promotion rule for the balance line
            b = stated.get("balance_end", {})
            if b and is_nothing_before(b["last_report"]["value"]):
                bal_v = b["this_report"]["value"]

        notes = []
        if regime == "cumulative":
            notes.append("CUMULATIVE-form filing: the sheet's three columns are LAST REPORT + "
                         "THIS REPORT = CUMULATIVE; a cycle total is the LATEST report, never a "
                         "sum. Stated totals here are the CUMULATIVE column.")
        else:
            notes.append("PERIOD-scoped filing: the sheet states one TOTALS column for the "
                         "checked reporting period only; a cycle total is a SUM across periods "
                         "(but see per-filing notes — some filers restate cumulatively).")
        if "this_report(promoted)" in c_cols + e_cols:
            notes.append("CUMULATIVE column blank and nothing precedes this report (LAST REPORT "
                         "blank/0/N-A), so the THIS REPORT figure is used; both columns are in "
                         "the vision cache verbatim.")
        if "cumulative(blank)" in c_cols + e_cols and c_tot is None and e_tot is None:
            notes.append("No stated total could be taken: the filer left the CUMULATIVE column "
                         "blank while printing figures elsewhere, or printed no figure at all. "
                         "Blank is honest — see the vision cache for what the face actually holds.")
        elif "cumulative(blank)" in c_cols + e_cols:
            notes.append("One side's CUMULATIVE cell is blank while the other prints a figure; "
                         "the blank side is left blank, not inferred.")
        if doc.get("notes"):
            notes.append(doc["notes"])
        # ---- BORN-DIGITAL Table A/B itemized layer (TRANCHE 3 Phase A). No-op on the two
        # older cumulative sheets: itemize() returns immediately unless the VISION-read
        # variant is the Table A/B one.
        _c, _e, patch, _n = itemize(r, key, variant, c_tot, e_tot, aliases)
        if variant == FAMILY_VARIANT:
            n_bd += 1
        contrib_rows.extend(_c)
        expend_rows.extend(_e)
        notes.extend(_n)
        if not patch:
            notes.append("Stated totals only — no itemized Table A/B row is published for this "
                         "filing, so reconciliation is UNKNOWN, not a match.")

        conf = min([c for c in (c_conf, e_conf) if c] or [""],
                   key=lambda c: CONF_RANK.get(c, 0))
        tot.append({
            "candidate": r["candidate"], "office": r["office"],
            "election_year": r["election_year"], "filing_date": r["date"],
            "reporting_period": r["reporting_period"], "filing_type": r["filing_type"],
            "stated_total_contributions": "" if c_tot is None else str(c_tot),
            "stated_total_expenditures": "" if e_tot is None else str(e_tot),
            "stated_beginning_balance": "",
            "stated_ending_balance": bal_v,
            "itemized_contrib_sum": "", "itemized_expend_sum": "",
            "reconciles_contrib": "", "reconciles_expend": "",
            "recon_delta_contrib": "", "recon_delta_expend": "",
            "self_funded_amount": "", "n_contrib_rows": 0, "n_expend_rows": 0,
            "source_filing": r["path"], "document_id": "wasatch-cf-" + key,
            "extraction_confidence": conf,
            "notes": " ".join(notes),
            "filing_regime": regime,
        })
        tot[-1].update(patch)
    tot.sort(key=lambda x: (x["election_year"], x["filing_date"], x["candidate"]))
    contrib_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    expend_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    return tot, contrib_rows, expend_rows, n_bd


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def write_rows(path, header, geo_header, rows):
    """Same trailing-optional-`geometry` contract as the shared driver (SCHEMA.md §2a)."""
    use = geo_header if any(getattr(x, common.GEOMETRY_COL, "") for x in rows) else header
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=use, extrasaction="ignore")
        w.writeheader()
        for x in rows:
            w.writerow(common.row_to_dict(x))


def main():
    rows = load()
    tot, crows, erows, n_bd = build(rows)
    write(D("filing_totals.csv"), TOTALS_HEADER, tot)
    write_rows(D("contributions.csv"), CONTRIB_HEADER, common.CONTRIB_HEADER_GEO, crows)
    write_rows(D("expenditures.csv"), EXPEND_HEADER, common.EXPEND_HEADER_GEO, erows)

    import collections
    by_reg = collections.Counter(t["filing_regime"] for t in tot)
    blank_c = sum(1 for t in tot if t["stated_total_contributions"] == "")
    blank_e = sum(1 for t in tot if t["stated_total_expenditures"] == "")
    conf = collections.Counter(t["extraction_confidence"] for t in tot)
    print("filing_totals.csv  %d filings  (%s)" % (
        len(tot), ", ".join("%s=%d" % kv for kv in sorted(by_reg.items()))))
    print("  stated contributions blank: %d   stated expenditures blank: %d" % (blank_c, blank_e))
    print("  extraction_confidence: %s" % dict(sorted(conf.items())))
    nrc = sum(1 for t in tot if t["reconciles_contrib"] == "True")
    nre = sum(1 for t in tot if t["reconciles_expend"] == "True")
    print("born-digital Table A/B filings handed to `%s`: %d of %d  (sides reconciling "
          "exactly: %d contrib / %d expend)" % (FAMILY_ID, n_bd, len(tot), nrc, nre))
    print("contributions.csv  %3d rows   expenditures.csv %3d rows  — the two older cumulative "
          "sheets itemize nothing (NOT transcribed, never 'no donors')" % (len(crows), len(erows)))


if __name__ == "__main__":
    main()
