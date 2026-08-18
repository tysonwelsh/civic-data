#!/usr/bin/env python3
"""make_itemized_caches.py — merge WAVE transcription records into the per-filing vision caches.

TRANCHE 3 PHASE B (2026-08-14). The analogue of `salt_lake_county/campaign_finance/
make_itemized_caches.py`, written for Wasatch's three form variants.

    python3 wasatch_county/campaign_finance/make_itemized_caches.py <records_dir>
    python3 wasatch_county/campaign_finance/make_itemized_caches.py <records_dir> --dry-run

WHAT IT DOES
  Reads every `<records_dir>/chunk_*.json` (a JSON list of per-filing transcription records, one
  object per filing, schema in `_backups/2026-08-14-tranche3-phaseb/wasatch/AGENT_BRIEF.md` §6),
  SCREENS each record against the gates below, and writes the surviving rows INTO that filing's
  existing `vision/<key>.json` as top-level `contributions` / `expenditures` lists plus a
  `_meta.itemized` block. **It never touches the stated-totals half of a cache**, and it is
  idempotent: re-running replaces the itemized block and nothing else.
  Files whose basename starts with `_` are skipped (retired in-progress saves, the SLCo
  convention).

THE SCREEN — every gate is applied HERE, by this module, not trusted from the record
  1. `key == sha1(index_path)[:8]` and the path is a real `index.csv` row. Hard fail otherwise.
  2. Every amount parses to a decimal; a row with a blank amount is kept but excluded from the
     sum, and the side is marked a FLOOR.
  3. **RECONCILIATION IS RECOMPUTED HERE**, against the anchors THIS module derives from the
     face — never the anchor the record claims. `anchors()` returns every figure the sheet
     legitimately prints (see its docstring: cover line 1 on the Carr sheet, the CUMULATIVE and
     the THIS REPORT columns on both cumulative sheets, the single TOTALS column on the 2024+
     sheet), and each is tried against BOTH the all-rows sum and the cash-only sum, because
     **in-kind treatment is per FILER, not per form**. The first exact closure wins and names
     itself. If none closes, the delta is measured against the PRIMARY anchor and the
     transcriber's own account of the cause is appended verbatim. A side with no figure at all
     on the face gets `unknown` — never a fabricated match.
     ⚠ `filing_totals.reconciles_*` / `recon_delta_*` are separately computed against the
     PUBLISHED `stated_total_*` (`csv_reconciles` / `csv_delta`), because that is what those
     columns mean and the shared validator checks it. A side can therefore close exactly on
     line 1 and still read `False` in the CSV, with the cause named in `recon.<side>.detail`.
  4. **FIELD-SHIFT SCREEN** (the `wasatch-field-shift` calibration specimen, which came from this
     county): a name cell that IS a date token, or that carries no letters at all, is suspect;
     >=50% suspect rows WITHHOLDS the whole side. Sum-level agreement is never accepted as proof
     of correct columns.
  5. **PRIVACY**: `donor_city` must not look like a street or a box number. A violation is
     stripped to blank and counted — street addresses never reach a derived CSV.
  6. Dates are ISO or blank. Anything else is blanked and flagged.

GEOMETRY — `pct:x,y,w,h@p<page>` (SCHEMA §2a), resolution-independent, resolvable by
`scripts/campaign_finance/make_snippet.py`.
  * **Born-digital rows** (the `wasatch_disclosure_tableab` text-layer parse in
    `build_finance.py`) get EXACT boxes from `pdftotext -bbox-layout`, which costs nothing on a
    machine-readable page. `bbox_pct()` here is the shared implementation.
  * **Vision rows** get an ESTIMATED band from the form's own fixed row pitch (`ROW_BANDS`
    below, measured off the rendered pages of each variant). A ruled ledger has a constant
    pitch, so the band lands on the row; it is a POINTER, never a value, and every such row is
    stamped `geometry_fit: "estimated"` so no consumer mistakes it for a measured box.
"""
from __future__ import annotations

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

WAVE = "itemized-vision(claude-opus-5; 2026-08-14 tranche 3 Phase B wasatch wave)"

# ---------------------------------------------------------------- estimated row bands
# (x, y0, w, pitch) in PERCENT of the rendered page, measured off the 200 dpi renders of each
# variant. `y0` is the TOP of the first data row under the column header; `pitch` is the ruled
# line spacing. Band height = pitch, so consecutive rows tile the ledger without gaps.
# `B@p3` = the case where the expenditure table CONTINUES onto a following page and its rows
# start near the top margin.
ROW_BANDS = {
    ("carr_5_5_pg_4line", "A"):      (6.0, 9.30, 88.0, 2.27),
    ("carr_5_5_pg_4line", "B"):      (6.0, 7.90, 88.0, 2.28),
    ("wasatch_fcr_3line", "A"):      (10.0, 19.00, 80.0, 2.05),
    ("wasatch_fcr_3line", "B"):      (10.0, 15.50, 80.0, 2.10),
    ("wasatch_disclosure_tableab", "A"): (5.0, 18.50, 90.0, 2.45),
    ("wasatch_disclosure_tableab", "B"): (5.0, 61.50, 90.0, 2.45),
}
CONTINUATION_BAND = 3.00   # y0 when a table continues onto a later page


def row_band(variant, side, page, row_i, first_page):
    """Estimated `pct:` band for a vision-transcribed ledger row. `side` is 'A' or 'B'."""
    key = (variant, side)
    if key not in ROW_BANDS:
        return ""
    x, y0, w, pitch = ROW_BANDS[key]
    if first_page is not None and page > first_page:
        y0 = CONTINUATION_BAND
    y = y0 + pitch * int(row_i)
    if y > 97.0:
        y = 97.0
    return "pct:%.2f,%.2f,%.2f,%.2f@p%d" % (x, y, w, min(pitch, 100.0 - y), int(page))


# ---------------------------------------------------------------- exact boxes, born-digital
_WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">'
                   r'(.*?)</word>', re.S)
_LINE = re.compile(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">'
                   r'(.*?)</line>', re.S)
_PAGE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', re.S)
_bbox_cache = {}


def _norm(s):
    return re.sub(r"[^0-9a-z]", "", s.lower())


def bbox_lines(pdf_path):
    """{page_no: [(normalized_row_text, x%, y%, w%, h%)]} from `pdftotext -bbox-layout`.

    Free, exact geometry for a born-digital page. Returns {} when poppler cannot read the file
    (a scan) rather than raising — the caller then falls back to an estimated band.

    ⚠ `-bbox-layout` emits one `<line>` PER TABLE CELL, so a ledger row arrives as four or five
    separate elements ("17jan2026", "jonwoodard", "60000", "loan"). Matching a whole ledger row
    against those fragments fails on every row, so this function CLUSTERS the fragments back
    into rows by vertical overlap and unions their boxes — which is also exactly the band a
    `geometry` pointer should describe."""
    if pdf_path in _bbox_cache:
        return _bbox_cache[pdf_path]
    out = {}
    try:
        xml = subprocess.run(["pdftotext", "-bbox-layout", pdf_path, "-"],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        _bbox_cache[pdf_path] = out
        return out
    for pno, m in enumerate(_PAGE.finditer(xml), 1):
        pw, ph = float(m.group(1)), float(m.group(2))
        cells = []
        for lm in _LINE.finditer(m.group(3)):
            x0, y0, x1, y1 = (float(lm.group(i)) for i in range(1, 5))
            words = [w.group(5) for w in _WORD.finditer(lm.group(5))]
            txt = _norm(" ".join(words))
            if txt:
                cells.append((y0, y1, x0, x1, txt))
        cells.sort()
        rows, cur = [], []
        for c in cells:
            if cur:
                cy0 = min(z[0] for z in cur)
                cy1 = max(z[1] for z in cur)
                overlap = min(cy1, c[1]) - max(cy0, c[0])
                if overlap <= 0.45 * min(cy1 - cy0, c[1] - c[0]):
                    rows.append(cur)
                    cur = []
            cur.append(c)
        if cur:
            rows.append(cur)
        band = []
        for grp in rows:
            y0 = min(z[0] for z in grp)
            y1 = max(z[1] for z in grp)
            x0 = min(z[2] for z in grp)
            x1 = max(z[3] for z in grp)
            txt = "".join(z[4] for z in sorted(grp, key=lambda z: z[2]))
            band.append((txt, 100.0 * x0 / pw, 100.0 * y0 / ph,
                         100.0 * (x1 - x0) / pw, 100.0 * (y1 - y0) / ph))
        out[pno] = band
    _bbox_cache[pdf_path] = out
    return out


def bbox_pct(pdf_path, page, line_text):
    """Exact `pct:` box for the laid-out text line `line_text` on `page`, or "" if not matched.

    Matching is on the line's alphanumeric content, so the layout engine's spacing choices do
    not matter. A near-miss is NOT accepted — a wrong pointer is worse than none."""
    pages = bbox_lines(pdf_path)
    want = _norm(line_text)
    if not want or page not in pages:
        return ""
    best, score, hits = None, 0.0, 0
    for txt, x, y, w, h in pages[page]:
        if txt == want:
            best, score, hits = (x, y, w, h), 1.0, 1
            break
        if want in txt or txt in want:
            r = min(len(want), len(txt)) / max(len(want), len(txt))
            if r > score:
                best, score = (x, y, w, h), r
            if r >= 0.75:
                hits += 1
    if best is None or score < 0.75 or hits > 1:
        return ""   # unmatched, or AMBIGUOUS — a wrong pointer is worse than none
    return "pct:%.2f,%.2f,%.2f,%.2f@p%d" % (best[0], best[1], best[2], best[3], int(page))


# ---------------------------------------------------------------- the screen
_DATEISH = re.compile(
    r"^\d{1,2}\s*[/.\-]{1,2}\s*\d{1,2}\s*[/.\-]{0,2}\s*\d{0,4}$"
    r"|^\d{1,2}\s*[A-Za-z]{3,9}\.?\s*,?\s*\d{2,4}$"
    r"|^[A-Za-z]{3,9}\.?\s*\d{1,2}\s*,?\s*\d{2,4}$")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_STREETY = re.compile(r"\d|\bP\.?O\.?\b|\bBox\b|\bSte\b|\bApt\b|\b(St|Ave|Rd|Dr|Ln|Blvd|Cir|Way|"
                      r"Ct|Hwy|Pkwy)\b\.?$", re.I)
SHIFT_CUTOFF = 0.5
_STATE_NAMES = {
    "UTAH": "UT", "ARIZONA": "AZ", "CALIFORNIA": "CA", "COLORADO": "CO", "IDAHO": "ID",
    "MARYLAND": "MD", "NEVADA": "NV", "NEW JERSEY": "NJ", "NEW YORK": "NY", "TEXAS": "TX",
    "WYOMING": "WY", "MONTANA": "MT", "OREGON": "OR", "WASHINGTON": "WA", "FLORIDA": "FL",
    "ILLINOIS": "IL", "VIRGINIA": "VA", "MASSACHUSETTS": "MA", "PENNSYLVANIA": "PA",
}


def money(s):
    t = (s or "").strip().replace("$", "").replace(",", "")
    if not t:
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    if not re.fullmatch(r"-?\d+(\.\d+)?", t):
        return None
    v = decimal.Decimal(t)
    return -v if neg else v


def _screen_side(rows, name_field, findings):
    """-> (kept_rows, suspect_fraction). Applies the field-shift + privacy + date screens."""
    if not rows:
        return rows, 0.0
    suspect = 0
    for r in rows:
        nm = (r.get(name_field) or "").strip()
        if _DATEISH.match(nm) or (nm and not any(c.isalpha() for c in nm)):
            suspect += 1
            findings.append("FIELD SHIFT suspect: %s=%r on line %s" % (name_field, nm,
                                                                      r.get("line_no")))
        d = (r.get("date") or "").strip()
        if d and not _ISO.match(d):
            findings.append("non-ISO date %r blanked on line %s" % (d, r.get("line_no")))
            r["date"] = ""
            r["needs_review"] = 1
        city = (r.get("donor_city") or "").strip()
        if city and _STREETY.search(city):
            findings.append("PRIVACY: donor_city %r looks like a street/box - blanked" % city)
            r["donor_city"] = ""
        # `donor_state` is a two-letter USPS code repo-wide. Filers write "Utah", "UT", "Ut";
        # normalizing the CASE/SPELLING of a state name is not changing a value, and anything
        # that is not a state at all ("United States") is blanked rather than guessed.
        st = (r.get("donor_state") or "").strip()
        if st:
            up = st.upper().replace(".", "")
            if up in _STATE_NAMES:
                r["donor_state"] = _STATE_NAMES[up]
            elif len(up) == 2 and up.isalpha():
                r["donor_state"] = up
            else:
                findings.append("donor_state %r is not a US state code - blanked" % st)
                r["donor_state"] = ""
    return rows, suspect / len(rows)


def load_index():
    idx = {}
    for r in csv.DictReader(open(D("index.csv"), newline="", encoding="utf-8")):
        idx[r["path"]] = r
    return idx


def load_totals():
    tot = {}
    for r in csv.DictReader(open(D("filing_totals.csv"), newline="", encoding="utf-8")):
        tot[r["source_filing"]] = r
    return tot


CUM_LINE = {("carr_5_5_pg_4line", "contributions"): "contrib_gt50",
            ("carr_5_5_pg_4line", "expenditures"): "total_expenses",
            ("wasatch_fcr_3line", "contributions"): "total_contributions",
            ("wasatch_fcr_3line", "expenditures"): "total_expenses"}


def anchors(variant, side, cache, totals_row):
    """Every figure on the face this side could legitimately close against, in priority order.

    Returns `[(value, label), ...]`. **Three real properties of these forms make a single anchor
    wrong**, and each was found in the documents, not assumed:

    * `carr_5_5_pg_4line` CONTRIBUTIONS — the published total is cover line 1 + line 2, and
      **line 2 is an unitemized AGGREGATE of contributions of $50 or less**. Form A itemizes
      line 1 only, so line 1 is the anchor.
    * The two CUMULATIVE variants print three columns, and **several filers itemize only the
      current period on the schedule while the cover states the CUMULATIVE figure** (found across
      the 2020 cycle: the residual then equals the TOTALS-FROM-LAST-REPORT cell exactly). So the
      THIS REPORT column is a legitimate second anchor, and closing on it is a real closure, not
      a coincidence — it is checked only after the cumulative column fails.
    * The `wasatch_disclosure_tableab` sheet has one TOTALS column and one anchor.
    """
    out = []
    line = CUM_LINE.get((variant, side))
    if line:
        cells = cache["stated"].get(line) or {}
        label1 = ("cover line 1 (>$50, from form A)" if line == "contrib_gt50"
                  else "the cover's own %s line" % line.replace("_", " "))
        for col, human in (("cumulative", "CUMULATIVE column"),
                           ("this_report", "TOTALS FOR THIS REPORT column")):
            v = money((cells.get(col) or {}).get("value"))
            if v is not None:
                out.append((v, "%s, %s" % (label1, human)))
    col = "stated_total_contributions" if side == "contributions" else "stated_total_expenditures"
    pub = money(totals_row.get(col))
    if pub is not None and all(pub != v for v, _l in out):
        out.append((pub, "published stated total"))
    return out or [(None, "nothing stated on the face")]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        raise SystemExit("usage: make_itemized_caches.py <records_dir> [--dry-run]")
    rec_dir = args[0]
    idx, totals = load_index(), load_totals()

    records = []
    for fn in sorted(os.listdir(rec_dir)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        blob = json.load(open(os.path.join(rec_dir, fn), encoding="utf-8"))
        for rec in blob:
            records.append((fn, rec))

    n_ok = n_rows_c = n_rows_e = 0
    n_exact = n_delta = n_withheld = n_unknown = 0
    report = []
    for fn, rec in records:
        path = rec["index_path"]
        key = hashlib.sha1(path.encode()).hexdigest()[:8]
        if key != rec["key"]:
            raise SystemExit("FAIL %s: key %s != sha1(%s)[:8]=%s" % (fn, rec["key"], path, key))
        if path not in idx:
            raise SystemExit("FAIL %s: %s is not an index.csv row" % (fn, path))
        cache_path = D("vision", key + ".json")
        cache = json.load(open(cache_path, encoding="utf-8"))
        variant = cache["_meta"]["form_variant_vision"]
        pdf = D(path)

        findings = []
        crows = rec.get("contributions") or []
        erows = rec.get("expenditures") or []
        crows, cfrac = _screen_side(crows, "donor_raw", findings)
        erows, efrac = _screen_side(erows, "vendor_raw", findings)

        sides = dict(rec.get("sides") or {})
        withheld = dict(rec.get("withheld_reason") or {})
        if cfrac >= SHIFT_CUTOFF and crows:
            sides["contributions"] = "withheld"
            withheld["contributions"] = ("FIELD SHIFT: %d%% of parsed rows are mis-columned; a "
                                         "systematically mis-columned ledger is a wrong value, "
                                         "so the whole side emits nothing" % round(100 * cfrac))
            crows = []
        if efrac >= SHIFT_CUTOFF and erows:
            sides["expenditures"] = "withheld"
            withheld["expenditures"] = ("FIELD SHIFT: %d%% of parsed rows are mis-columned; the "
                                        "whole side emits nothing" % round(100 * efrac))
            erows = []
        if sides.get("contributions") == "withheld":
            crows = []
        if sides.get("expenditures") == "withheld":
            erows = []

        recon = {}
        for side, rows, band_side in (("contributions", crows, "A"),
                                      ("expenditures", erows, "B")):
            cand = anchors(variant, side, cache, totals.get(path, {}))
            st, label = cand[0]
            if sides.get(side) == "withheld":
                recon[side] = dict(stated="" if st is None else str(st), itemized="",
                                   result="withheld", anchor=label,
                                   detail=withheld.get(side, "withheld"))
                n_withheld += 1
                continue
            if sides.get(side) == "none":
                recon[side] = dict(stated="" if st is None else str(st), itemized="",
                                   result="unknown", anchor=label,
                                   detail=(rec.get("withheld_reason") or {}).get(
                                       side, "the document has no such schedule page"))
                n_unknown += 1
                continue
            # in-kind rows are summed separately: at least one filer excluded them from his own
            # printed total, and a side that closes only without them is a REAL closure.
            cash = sum((money(r.get("amount")) or 0) for r in rows if not r.get("in_kind"))
            ink = sum((money(r.get("amount")) or 0) for r in rows if r.get("in_kind"))
            allsum = cash + ink
            blanks = sum(1 for r in rows if money(r.get("amount")) is None)
            # Try every legitimate anchor on the face, and — because in-kind treatment is
            # PER FILER on these sheets, not per form (Armer 2020 excludes her in-kind rows from
            # her own totals, Lee 2020 includes hers and still closes) — try each anchor against
            # BOTH the all-rows sum and the cash-only sum. The first exact closure wins and names
            # itself; if none closes, the delta is measured against the PRIMARY anchor.
            hit = None
            for v, lab in cand:
                if v is None:
                    continue
                if abs(allsum - v) <= decimal.Decimal("0.01"):
                    hit = (v, lab, allsum, False)
                    break
                if ink and abs(cash - v) <= decimal.Decimal("0.01"):
                    hit = (v, lab, cash, True)
                    break
            if hit:
                v, lab, used, cash_only = hit
                st, label = v, lab
                res = "exact"
                item = "%.2f" % used
                det = "exact (%.2f = %s, %s)" % (used, v, lab)
                if cash_only:
                    det += ("; the %d IN-KIND row(s) totalling %.2f are EXCLUDED from the "
                            "filer's own printed total and are published alongside it with "
                            "in_kind=true" % (sum(1 for r in rows if r.get("in_kind")), ink))
                if lab.endswith("THIS REPORT column"):
                    det += (". The schedule is PERIOD-SCOPED while the cover states the "
                            "CUMULATIVE figure - a real property of this three-column sheet, not "
                            "a missing row; the residual against the cumulative cell is the "
                            "TOTALS FROM LAST REPORT column")
                n_exact += 1
            elif st is None:
                res, det = "unknown", ("no stated figure on the face, so the %d transcribed "
                                       "row(s) summing to %.2f cannot be reconciled - unknown, "
                                       "never a fabricated match" % (len(rows), allsum))
                n_unknown += 1
                item = "%.2f" % allsum
            else:
                res = "delta"
                det = ("delta %.2f - %d row(s) sum to %.2f against %s, which prints %s. Both "
                       "figures retained verbatim; no row was adjusted and the stated total was "
                       "not recomputed." % (allsum - st, len(rows), allsum, label, st))
                n_delta += 1
                item = "%.2f" % allsum
            if blanks:
                det += (" %d row(s) carry an ILLEGIBLE amount and are excluded from the sum, so "
                        "this side is a FLOOR." % blanks)
            # Keep the TRANSCRIBER's own account of a side that does not close. This module's
            # recomputation is the gate; the person who read the page is the one who can say WHY
            # (a filer who totalled gross-of-fees, a carry-in from a prior report, an unrecorded
            # line). Losing that explanation would turn a diagnosed delta back into a bare number.
            claim = ((rec.get("recon") or {}).get(side) or {}).get("detail", "")
            if res != "exact" and claim:
                det += " || TRANSCRIBER'S ACCOUNT: " + claim
            # ---- what the CSV columns mean vs what the SIDE was gated against.
            # `reconciles_contrib` / `recon_delta_contrib` in `filing_totals.csv` are defined
            # against the PUBLISHED `stated_total_*`. On the Carr sheet that published figure is
            # line 1 + line 2, and **line 2 is an unitemized <=$50 AGGREGATE with no donor rows
            # BY FORM DESIGN** — so a side that closes perfectly on line 1 still cannot equal the
            # published total, and claiming `True` there would be a false match (and fails the
            # shared validator, correctly). Both facts are carried: the side's own gate in
            # `result`, and the CSV verdict here.
            pub = money((totals.get(path, {}) or {}).get(
                "stated_total_contributions" if side == "contributions"
                else "stated_total_expenditures"))
            csv_sum = decimal.Decimal(item) if item else None
            if pub is None or csv_sum is None:
                csv_rec, csv_delta = "", ""
            elif abs(csv_sum - pub) <= decimal.Decimal("0.01"):
                csv_rec, csv_delta = "True", "%.2f" % (csv_sum - pub)
            else:
                csv_rec, csv_delta = "False", "%.2f" % (csv_sum - pub)
            if csv_rec == "False" and res == "exact":
                why = ("the published figure adds cover line 2 - the AGGREGATE of contributions "
                       "of $50 or less, which this form deliberately does not itemize"
                       if "line 1" in label else
                       "the published figure is the CUMULATIVE column while this schedule is "
                       "period-scoped, so the difference is the TOTALS FROM LAST REPORT cell"
                       if "THIS REPORT" in label else
                       "the filer excluded his own in-kind rows from the printed total")
                det += (" NOTE: against the PUBLISHED stated total of %s this reads as a %.2f "
                        "difference, because %s. The itemized side is COMPLETE against the "
                        "figure it closes on; the difference is not a missing row."
                        % (pub, csv_sum - pub, why))
            recon[side] = dict(stated="" if st is None else str(st), itemized=item,
                               result=res, anchor=label, detail=det,
                               published_stated="" if pub is None else str(pub),
                               csv_reconciles=csv_rec, csv_delta=csv_delta)

        # geometry
        geo_exact = geo_est = 0
        first_A = min((int(r["page"]) for r in crows), default=None)
        first_B = min((int(r["page"]) for r in erows), default=None)
        name_key = {"A": "donor_raw", "B": "vendor_raw"}
        for rows, band_side, first in ((crows, "A", first_A), (erows, "B", first_B)):
            for r in rows:
                # A born-digital page gives the row's EXACT box for free. Anchor on the row's own
                # content (name + amount together) so a short amount cannot match the wrong row.
                probe = " ".join(x for x in ((r.get(name_key[band_side]) or ""),
                                             (r.get("amount") or "")) if x)
                g = bbox_pct(pdf, int(r["page"]), probe) if probe else ""
                if g:
                    r["geometry"] = g
                    r["geometry_fit"] = "bbox"
                    geo_exact += 1
                else:
                    r["geometry"] = row_band(variant, band_side, int(r["page"]),
                                             int(r.get("row_i", 0)), first)
                    r["geometry_fit"] = "estimated"
                    geo_est += 1

        cache["contributions"] = crows
        cache["expenditures"] = erows
        cache["_meta"]["itemized"] = {
            "wave": WAVE,
            "transcribed_date": "2026-08-14",
            "record_file": fn,
            "variant": variant,
            "pages_read": rec.get("pages_read", []),
            "itemized_pages_A": rec.get("itemized_pages_A", ""),
            "itemized_pages_B": rec.get("itemized_pages_B", ""),
            "sides": sides,
            "withheld_reason": withheld,
            "recon": recon,
            "page_subtotal_gates": rec.get("page_subtotal_gates", ""),
            "escalations": rec.get("escalations", 0),
            "escalation_note": rec.get("escalation_note", ""),
            "n_contrib_rows": len(crows),
            "n_expend_rows": len(erows),
            "geometry": {"bbox_exact": geo_exact, "estimated_band": geo_est,
                         "provenance": ("bbox = pdftotext -bbox-layout on a born-digital page; "
                                        "estimated = the form's own fixed ruled-row pitch. A "
                                        "band is a POINTER to the row, never a value.")},
            "screen_findings": findings,
            "notes": rec.get("notes", ""),
        }
        if not dry:
            with open(cache_path, "w", encoding="utf-8") as fh:
                json.dump(cache, fh, indent=1, ensure_ascii=False)
                fh.write("\n")
        n_ok += 1
        n_rows_c += len(crows)
        n_rows_e += len(erows)
        report.append((path, len(crows), len(erows),
                       recon.get("contributions", {}).get("result", ""),
                       recon.get("expenditures", {}).get("result", "")))

    print("%s%d filing caches updated  (%d contribution rows / %d expenditure rows)"
          % ("DRY RUN: " if dry else "", n_ok, n_rows_c, n_rows_e))
    print("  sides: exact %d  delta %d  withheld %d  unknown %d"
          % (n_exact, n_delta, n_withheld, n_unknown))
    for p, c, e, rc, re_ in report:
        if rc in ("delta", "withheld") or re_ in ("delta", "withheld"):
            print("   !! %-58s C=%-3d(%s) E=%-3d(%s)" % (p, c, rc, e, re_))


if __name__ == "__main__":
    main()
