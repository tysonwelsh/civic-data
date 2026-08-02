#!/usr/bin/env python3
"""Summit County campaign-finance — module-local builder (STATED-TOTALS tranche).

DERIVED layer. Regenerate with:
    python3 summit_county/campaign_finance/build_finance.py

Reads   index.csv                (DERIVED by build_index.py — one row per filing)
        vision/<sha1(path)[:8]>.json  (CURATED — the vision transcription of each cover page)
        text/<file>.txt          the born-digital sidecars (15 filings) — the itemized layer
Writes  filing_totals.csv        one row per filing, SCHEMA.md §4 column contract
        contributions.csv        §2 contract — the BORN-DIGITAL itemized layer (below)
        expenditures.csv         §3 contract — ditto
        cover_totals.csv         module-local: ALL THREE cover columns, verbatim, per row

Why a module-local builder and not the shared engine
----------------------------------------------------
`summit_form` IS NOW REGISTERED (2026-08-02) in the shared registry — the family this
section used to describe as absent exists and is unit-tested against Langston 2022
(contributions 503.00 / expenditures 511.62, plus an explicit assertion that the documented
millcreek/ogden wrong answer, 511.62 read as the contribution total, is NOT produced).

The builder nonetheless stays MODULE-LOCAL: 116 of 131 filings are scans whose cover
figures exist only as vision transcriptions, and `driver.run()` would rewrite all three CSVs
from one parse pass. This builder keeps the vision-based promotion for `stated_*` and calls
the family for the ITEMIZED layer of the 15 born-digital filings only.

CROSS-VALIDATION, measured 2026-08-02: on all 15 born-digital filings the family's
independently-read cover figures equal this module's vision-promoted `stated_*` — with ONE
divergence, recorded in CLAUDE.md, on Betsy Wallace 23016's expenditure cell. No stated
value is taken from the family; the vision promotion remains authoritative.

THE COLUMN TRAP (the thing this module exists to get right)
-----------------------------------------------------------
Summit's cover box runs **Current Report | Last Report | Cumulative Totals** — the
REVERSE of the sheet the shared parsers assume (Millcreek prints LAST | THIS |
CUMULATIVE). The 2024 sheet renames the middle column "Previous Report"; the ORDER never
changes. The vision cache therefore stores all three cells verbatim AND labelled, and
this builder promotes one of them per the rule below. `cover_totals.csv` republishes all
three so every promotion is auditable without reopening the PDF.

PROMOTION RULE (documented, deterministic, and never silently repairing a value)
-------------------------------------------------------------------------------
Per cover row, in order:
  1. `cumulative`  when that cell holds a parseable amount        -> basis "cumulative"
  2. `current`     when cumulative is EMPTY or ILLEGIBLE          -> basis "current (cumulative cell <empty|illegible>)"
  3. `current`/`previous` when the cumulative cell parses to ZERO on a
     contributions/expenditures row whose Current or Previous cell is non-zero. The
     cumulative cell then contradicts its own row: it is the fillable template's default
     "$ 0.00" (or Excel zero-dash) left in place. Proven on the file: Hanson's 2024
     Pre-Election sheet (24237) prints $0.00 cumulative against 640.86 current, and her
     Post-Election sheet (24381) carries 640.86 through BOTH the Previous and Cumulative
     columns.  -> basis "current (cumulative prints zero against a non-zero row)"
     Never applied to the campaign-balance row, where a real zero is normal.
  4. otherwise blank + a note. A blank stated total is an honest gap, never a zero.
The verbatim cells always survive in cover_totals.csv and vision/*.json.

Contributions on the pre-2022 sheet are split across TWO printed lines (donors > $50 and
donors <= $50). `stated_total_contributions` is the sum of ONLY the lines that were
actually printed (the juab precedent); when one part is blank the notes say so.
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

CF_LIB = os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance"))
sys.path[:0] = [CF_LIB, os.path.join(CF_LIB, "families")]
import common            # noqa: E402  shared row model + money/geometry primitives
import normalize_donors  # noqa: E402  tier-1 donor/vendor normalization + donor_type
import reconcile         # noqa: E402  the $0.01 printed-total test
import registry          # noqa: E402  form-family dispatch

FAMILY_ID = "summit_form"

TOTALS_HEADER = [
    "candidate", "office", "election_year", "filing_date", "reporting_period",
    "filing_type", "stated_total_contributions", "stated_total_expenditures",
    "stated_beginning_balance", "stated_ending_balance", "itemized_contrib_sum",
    "itemized_expend_sum", "reconciles_contrib", "reconciles_expend",
    "recon_delta_contrib", "recon_delta_expend", "self_funded_amount",
    "n_contrib_rows", "n_expend_rows", "source_filing", "document_id",
    "extraction_confidence", "notes",
]
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

# Cells the filer used to mean "nothing here" rather than a number. A BARE dash is a
# handwritten nil mark -> blank. A dash carrying the form's own currency sign ("$   -") is the
# spreadsheet template's ACCOUNTING ZERO on the born-digital 2022/2024/2026 sheets -> 0.00.
NIL = {"", "n/a", "na", "-", "—", "–"}
ZERO_DASH = re.compile(r"^\$\s*[-—–]$")


def cache_key(index_path):
    """Repo-standard vision-cache key: sha1(index.csv path)[:8] (scripts/campaign_finance/
    vision_lib.cache_key). Kept as a local copy so this module imports nothing shared."""
    return hashlib.sha1(index_path.encode()).hexdigest()[:8]


def money(s):
    """Parse a cover cell to Decimal, or None when it is empty / illegible / unparseable.

    Conservative on purpose: only whitespace, a currency sign, thousands commas, accounting
    parentheses and a trailing "written dash" (the filers' shorthand for '.00') are removed.
    A cell whose decimal point itself is malformed (Ioannides 2024 wrote '23,744,71' and
    '23.744.71') returns None — it is reported as unparseable, never silently repaired.
    """
    if s is None:
        return None
    t = str(s).strip()
    if t.lower() in NIL:
        return None
    if ZERO_DASH.match(t):
        return decimal.Decimal(0)            # the template's accounting zero
    t = t.replace("$", "").replace("+", "").strip()
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1].strip()
    t = re.sub(r"[\s—–-]+$", "", t)          # trailing written dash
    if t.startswith("-"):
        neg, t = True, t[1:]
    t = t.strip()
    if not t:
        return None
    if not re.fullmatch(r"\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?", t):
        return None                                    # malformed separators -> honest None
    t = t.replace(",", "")
    try:
        v = decimal.Decimal(t)
    except decimal.InvalidOperation:
        return None
    return -v if neg else v


ZERO_GLYPHS = {"ø", "-0-", "zero"}   # owner ruling 2026-08-02: glyphs that DENOTE the digit 0
                                     # (a slashed zero is a written zero; a bare dash is not —
                                     # dashes/N-A stay in NIL as honest blanks)


def cell_state(raw):
    """(kind, value): 'empty' | 'illegible' | 'unparseable' | 'value'."""
    if raw is None:
        return "illegible", None
    if str(raw).strip().lower() in ZERO_GLYPHS:
        return "value", decimal.Decimal("0.00")
    if str(raw).strip().lower() in NIL or str(raw).strip() == "(no column)":
        return "empty", None
    v = money(raw)
    if v is None:
        return "unparseable", None
    return "value", v


def promote(cells, cols, is_balance_row):
    """Apply the documented promotion rule to one cover row.

    cells: the row dict from the cache; cols: the three column names in printed order.
    Returns (Decimal|None, basis_string).
    """
    cur_k, cur_v = cell_state(cells.get(cols[0]))
    prv_k, prv_v = cell_state(cells.get(cols[1]))
    cum_k, cum_v = cell_state(cells.get(cols[2]))

    if cum_k == "value":
        if (not is_balance_row and cum_v == 0
                and ((cur_k == "value" and cur_v != 0) or (prv_k == "value" and prv_v != 0))):
            if cur_k == "value" and cur_v != 0:
                return cur_v, "current (cumulative prints zero against a non-zero row)"
            return prv_v, "previous (cumulative prints zero against a non-zero row)"
        return cum_v, "cumulative"

    if cur_k == "value":
        return cur_v, "current (cumulative cell %s)" % cum_k
    if prv_k == "value":
        return prv_v, "previous (current and cumulative cells %s/%s)" % (cur_k, cum_k)
    return None, "none (no parseable cell in this row: %s/%s/%s)" % (cur_k, prv_k, cum_k)


MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def iso_date(s, year_hint):
    """Normalise the form's PRINTED signature date to ISO. Returns '' when it cannot be
    read cleanly — the index's pdf-CreationDate proxy is never substituted here."""
    if not s:
        return ""
    t = s.strip().replace(".", "")
    # ordinal suffixes as written by the filer ("June 7th 2026") -> "June 7 2026"
    t = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", t, flags=re.I)
    m = re.fullmatch(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})", t)
    if m:
        mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        yr += 2000 if yr < 100 else 0
        return "%04d-%02d-%02d" % (yr, mo, da)
    m = re.fullmatch(r"(\d{1,2})[\s\-]+([A-Za-z]{3,9})[\s\-,]+(\d{2,4})", t)
    if m:
        mo = MONTHS.get(m.group(2)[:3].lower())
        yr = int(m.group(3)) + (2000 if int(m.group(3)) < 100 else 0)
        if mo:
            return "%04d-%02d-%02d" % (yr, mo, int(m.group(1)))
    m = re.fullmatch(r"([A-Za-z]{3,9})[\s\-,]+(\d{1,2})[\s\-,]+(\d{2,4})", t)
    if m:
        mo = MONTHS.get(m.group(1)[:3].lower())
        yr = int(m.group(3)) + (2000 if int(m.group(3)) < 100 else 0)
        if mo:
            return "%04d-%02d-%02d" % (yr, mo, int(m.group(2)))
    return ""


def dec(v):
    return "" if v is None else str(v)


def load():
    index = list(csv.DictReader(open(D("index.csv"), newline="", encoding="utf-8")))
    caches = {}
    for r in index:
        p = D("vision", cache_key(r["path"]) + ".json")
        if os.path.exists(p):
            caches[r["document_id"]] = json.load(open(p, encoding="utf-8"))
    return index, caches


# A street start INSIDE a donor name. Summit's ledger is fixed-column, but two 2022 donor
# names are long enough to run into the address column with a single space between them
# ("Women's Democratic Club of Utah PO Box 91184"), and `summit_form`'s whitespace split then
# carries the street into `donor_raw`. The engine is FROZEN this tranche, so the family is not
# patched; instead this module enforces its OWN privacy contract before publishing: the street
# portion is DISCARDED at the boundary marker, exactly the rule `cache_cfd` uses (a numeric
# token or `PO Box` marks the name/address boundary). Nothing is invented, no amount changes,
# and every affected row is named in `notes` + flagged `needs_review=1`.
_STREET_IN_NAME = re.compile(r"\s+(?:P\.?\s?O\.?\s+Box\b|\d+\s+\S)", re.I)


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


def privacy_guard(rows, notes):
    """Discard a street fragment that a family left inside `donor_raw`. Returns the count."""
    hit = 0
    for x in rows:
        m = _STREET_IN_NAME.search(x.donor_raw or "")
        if not m:
            continue
        kept = x.donor_raw[:m.start()].strip()
        if not kept:
            continue
        notes.append("PRIVACY GUARD: line %s — the `%s` family left a STREET fragment inside "
                     "donor_raw (the donor name overflows the fixed-width name column); the "
                     "street portion was discarded at the boundary marker and is not stored. "
                     "Donor kept as %r. FAMILY LIMITATION, documented not patched."
                     % (x.line_no, FAMILY_ID, kept))
        x.donor_raw = kept
        x.needs_review = "1"
        hit += 1
    return hit


def itemize(r, stated_c, stated_e, aliases):
    """Parse ONE born-digital filing with the registered `summit_form` family and
    RECONCILIATION-GATE each side against the stated total this module already publishes
    (the vision-promoted cover figure).

    Returns (contrib_rows, expend_rows, ft_patch, notes). The family applies its OWN
    completeness gate first (`EMIT_UNRECONCILED=False`): the printed template example rows
    are dropped, and a section whose rows do not sum to its own printed total emits NOTHING
    with a reason — that is where the wrapped-2014 contributor names and the Harte-2026
    period-scoped-ledger-under-a-cumulative-cover class are refused. This function is the
    SECOND gate: even a family-approved section must sum to the figure THIS module
    publishes, or it does not ship.
    """
    notes = []
    tp = D(r["text_path"]) if r.get("text_path") else ""
    if r.get("format") != "text" or not tp or not os.path.exists(tp):
        return [], [], {}, notes
    text = open(tp, encoding="utf-8", errors="replace").read()

    fam = registry.get(FAMILY_ID)
    meta = dict(candidate=r["candidate"], office=r["office"], seat=r.get("seat", ""),
                election_year=r["election_year"], filing_date=r.get("date", ""),
                reporting_period=r.get("reporting_period", ""), source_filing=r["path"],
                document_id=r["document_id"], extract_method=FAMILY_ID + "/text",
                is_scanned=False)
    res = fam.parse(text, meta)
    crows, erows = res["contrib_rows"], res["expend_rows"]
    privacy_guard(crows, notes)          # BEFORE normalization, so the alias/type layer
    crows = screen_side(crows, "donor_raw", "contributions", notes, FAMILY_ID)
    erows = screen_side(erows, "vendor_raw", "expenditures", notes, FAMILY_ID)
    for x in crows:
        normalize_donors.normalize_contrib(x, meta["candidate"], aliases)
    for x in erows:
        normalize_donors.normalize_vendor(x)

    # The family reads the cover INDEPENDENTLY of the vision transcription. Where the two
    # disagree, the vision promotion governs and the divergence is recorded — a figure is
    # never taken from the parser over the transcription.
    for side, fam_val, mod_val in (("contributions", res.get("stated_contrib"), stated_c),
                                   ("expenditures", res.get("stated_expend"), stated_e)):
        fv = None if fam_val is None else round(float(fam_val), 2)
        mv = None if mod_val is None else round(float(mod_val), 2)
        if fv != mv:
            notes.append("COVER DIVERGENCE (%s): the `%s` family reads %s off the sheet "
                         "where the vision promotion published %s; the vision figure "
                         "governs and no figure was changed"
                         % (side, FAMILY_ID, fv, mv))

    patch, keep = {}, {"contrib": list(crows), "expend": list(erows)}
    for side, stated in (("contrib", stated_c), ("expend", stated_e)):
        rows_ = keep[side]
        if not rows_:
            continue
        ssum = round(sum(float(x.amount) for x in rows_ if x.amount), 2)
        rec, delta = reconcile.reconciles(ssum, None if stated is None else float(stated))
        if rec is not True:
            notes.append("ITEMIZED %s WITHHELD: %d parsed row(s) sum to %.2f against the "
                         "published stated %s — the side does not reconcile, so NOTHING is "
                         "emitted (SCHEMA.md §6)"
                         % (side, len(rows_), ssum,
                            "blank total" if stated is None else "%.2f" % float(stated)))
            keep[side] = []
            continue
        patch["itemized_%s_sum" % side] = str(ssum)
        patch["reconciles_%s" % side] = "True"
        patch["recon_delta_%s" % side] = "%.2f" % delta

    crows, erows = keep["contrib"], keep["expend"]
    for x in crows + erows:
        x.extraction_confidence = "high"
        x.needs_review = x.needs_review or "0"   # guard/shift flags already set stay set
    if crows or erows:
        patch["n_contrib_rows"] = str(len(crows))
        patch["n_expend_rows"] = str(len(erows))
        patch["self_funded_amount"] = common.money_str(round(sum(
            float(x.amount) for x in crows
            if x.donor_type in ("candidate-self", "loan") and x.amount), 2))
        notes.append("ITEMIZED LAYER: %d contribution / %d expenditure row(s) parsed by the "
                     "registered `%s` family from the born-digital text layer, each side "
                     "reconciled EXACTLY to the published stated total; per-row `geometry` "
                     "records the amount cell read"
                     % (len(crows), len(erows), FAMILY_ID))
    if res.get("notes"):
        notes.append("family: " + res["notes"])
    return crows, erows, patch, notes


def build(index, caches):
    totals, cover = [], []
    contrib_rows, expend_rows = [], []
    aliases = normalize_donors.load_aliases(D("donor_aliases.csv"))
    n_bd = 0
    for r in index:
        did = r["document_id"]
        c = caches.get(did)
        if not c:
            totals.append({k: "" for k in TOTALS_HEADER} | {
                "candidate": r["candidate"], "office": r["office"],
                "election_year": r["election_year"], "reporting_period": r["reporting_period"],
                "filing_type": "statement", "n_contrib_rows": "0", "n_expend_rows": "0",
                "source_filing": r["path"], "document_id": did,
                "notes": "no vision cache for this filing — stated totals NOT transcribed",
            })
            continue

        cv = c["cover"]
        cols = cv["column_order"]
        rows = cv["rows"]
        variant = c["form_variant"]
        notes = []

        # ---- contributions: one printed line (2018+) or two split lines (pre-2022 sheet)
        if variant == "split50":
            parts, bases = [], []
            for nm, lbl in (("contrib_gt50", ">$50"), ("contrib_le50", "<=$50")):
                v, b = promote(rows[nm], cols, False)
                bases.append("%s=%s" % (lbl, b))
                if v is not None:
                    parts.append(v)
                else:
                    notes.append("contribution line %s printed no readable figure — "
                                 "NOT treated as zero" % lbl)
            contrib = sum(parts) if parts else None
            contrib_basis = "sum of the printed split lines [%s]" % "; ".join(bases)
        else:
            contrib, contrib_basis = promote(rows["contrib_total"], cols, False)

        expend, expend_basis = promote(rows["total_expenditures"], cols, False)
        balance, balance_basis = promote(rows["campaign_balance"], cols, True)

        notes.insert(0, "form_variant=%s; column order %s" % (variant, " | ".join(cols)))
        notes.append("promotion: contributions[%s]; expenditures[%s]; ending_balance[%s]"
                     % (contrib_basis, expend_basis, balance_basis))
        # ---- BORN-DIGITAL itemized layer (TRANCHE 3 Phase A). No-op on the 116 scans:
        # itemize() returns immediately unless index.format == 'text'.
        _c, _e, patch, _n = itemize(r, contrib, expend, aliases)
        if r.get("format") == "text":
            n_bd += 1
        contrib_rows.extend(_c)
        expend_rows.extend(_e)
        notes.extend(_n)
        if not patch:
            notes.append("stated totals only — itemized donor/expenditure layer NOT "
                         "transcribed (reconciliation columns intentionally blank)")
        if c["notes"]:
            notes.append(c["notes"])

        totals.append({
            "candidate": r["candidate"],
            "office": r["office"],
            "election_year": r["election_year"],
            "filing_date": iso_date(cv["signature_date_as_printed"], r["election_year"]),
            "reporting_period": r["reporting_period"],
            "filing_type": "statement",
            "stated_total_contributions": dec(contrib),
            "stated_total_expenditures": dec(expend),
            "stated_beginning_balance": "",
            "stated_ending_balance": dec(balance),
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
            "document_id": did,
            "extraction_confidence": c["field_confidence"]["stated_totals"],
            "notes": " | ".join(n for n in notes if n),
        })
        totals[-1].update(patch)

        for nm, cells in rows.items():
            cover.append({
                "document_id": did, "source_filing": r["path"],
                "candidate": r["candidate"], "office": r["office"],
                "election_year": r["election_year"], "reporting_period": r["reporting_period"],
                "form_variant": variant, "cover_row": nm,
                "col1_label": cols[0], "col1_verbatim": _vb(cells.get(cols[0])),
                "col2_label": cols[1], "col2_verbatim": _vb(cells.get(cols[1])),
                "col3_label": cols[2], "col3_verbatim": _vb(cells.get(cols[2])),
                "candidate_as_printed": cv["candidate_as_printed"],
                "office_verbatim": cv["office_verbatim"],
                "party_verbatim": cv["party_verbatim"],
                "signature_date_as_printed": cv["signature_date_as_printed"],
                "transcribed_by": c["transcribed_by"],
            })

    totals.sort(key=lambda x: (x["election_year"], x["office"], x["candidate"],
                               x["reporting_period"], x["document_id"]))
    cover.sort(key=lambda x: (x["election_year"], int(x["document_id"]), x["cover_row"]))
    contrib_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    expend_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    return totals, cover, contrib_rows, expend_rows, n_bd


def _vb(v):
    """Verbatim cell for the CSV: '' = empty cell on the form, 'ILLEGIBLE' = present but
    unreadable (cache null). The two are different facts and are kept apart."""
    return "ILLEGIBLE" if v is None else v


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


if __name__ == "__main__":
    index, caches = load()
    totals, cover, crows, erows, n_bd = build(index, caches)
    write(D("filing_totals.csv"), TOTALS_HEADER, totals)
    write_rows(D("contributions.csv"), CONTRIB_HEADER, common.CONTRIB_HEADER_GEO, crows)
    write_rows(D("expenditures.csv"), EXPEND_HEADER, common.EXPEND_HEADER_GEO, erows)
    write(D("cover_totals.csv"), list(cover[0].keys()), cover)

    got_c = sum(1 for t in totals if t["stated_total_contributions"] != "")
    got_e = sum(1 for t in totals if t["stated_total_expenditures"] != "")
    got_b = sum(1 for t in totals if t["stated_ending_balance"] != "")
    print("index.csv          %3d filings" % len(index))
    print("vision/            %3d cover-page transcriptions" % len(caches))
    print("filing_totals.csv  %3d rows  (contributions %d, expenditures %d, ending balance %d "
          "with a stated figure)" % (len(totals), got_c, got_e, got_b))
    print("cover_totals.csv   %3d rows  (all three columns, verbatim)" % len(cover))
    nrc = sum(1 for t in totals if t["reconciles_contrib"] == "True")
    nre = sum(1 for t in totals if t["reconciles_expend"] == "True")
    print("born-digital filings handed to `%s`: %3d of %d  (sides reconciling exactly: "
          "%d contrib / %d expend)" % (FAMILY_ID, n_bd, len(totals), nrc, nre))
    print("contributions.csv  %3d rows   expenditures.csv %3d rows  — the 116 scans itemize "
          "nothing (NOT transcribed, never 'no donors')" % (len(crows), len(erows)))
