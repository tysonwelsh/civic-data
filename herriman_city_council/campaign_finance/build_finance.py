#!/usr/bin/env python3
"""build_finance.py — Herriman City driver for the structured campaign-finance layer.

Part of the 2026-07-17 vision-cache wave (reference impl: midvale; shared helpers
`scripts/campaign_finance/vision_lib.py`, family `vision_cache`). Herriman's corpus is a
50-row / 48-distinct-doc acquisition index across 2021/2023/2025 (Council D1-D4 + Mayor),
split 33 scanned + 17 born-digital text (SCHEMA_SPEC §9 index; see AVAILABILITY.md).

TWO consumption paths, both flowing through the SAME shared normalization + reconciliation:
  1. SCANNED (33) -> the vision caches `vision/<sha1(index_path)[:8]>.json` written by the
     three /cf-vision-transcribe tranches -> `vision_lib.build_result`.
  2. BORN-DIGITAL TEXT (17) -> `_stdform_parse()` below reads the Utah §10-3-208 "Municipal
     Elections Campaign Finance Report" Schedule A/B/C text layer (`pdftotext -layout`) into
     the SAME cache dict shape, then `_text_result` maps it through `vision_lib._rows_from`
     (extract_method `herriman_stdform/text`, NOT vision). RECONCILIATION IS THE INTEGRITY
     GATE: a parse that reconciles to the form's printed Schedule total earns `high`; a
     parse that does not is flagged `needs_review`/`low` and kept verbatim, never adjusted —
     so a mis-read cannot masquerade as clean truth. The ≤$50 unitemized aggregate becomes a
     blank-donor `needs_review` row (its stated amount, no fabricated identity). Ligature
     corruption in the born-digital layer ('ContribuƟons', 'Ma Basham') is normalized before
     parsing; names are carried verbatim otherwise.

Honest NOT-BUILT rows (`vision_lib.empty_result`, unknown totals + dated reason):
  * duplicate_of != '' (Grimm 5673/5719) — byte-identical re-uploads; superseded, never
    summed (the canonical 5785/5786 carry the money).
  * Grimm 5673/5719 duplicate re-uploads are the ONLY remaining not-built rows.
    (The 2 born-digital Basham filings whose §10-3-208 section headers did NOT render in the
    text layer — 5784 Aug-5, 5802 Pre-General — were VISION-transcribed 2026-07-19 into
    vision/73687d99.json + vision/c96909aa.json; they now route through the vision path,
    since _cache_for() checks the vision cache before the text parser. See AVAILABILITY.md.)

reconcile_cash_only=True: Herriman's printed "TOTAL CONTRIBUTIONS RECEIVED (Schedule A)"
counts CASH ONLY — Schedule C in-kind is a SEPARATE stated line (verified across 7 in-kind
caches: Anderson/Garcia/Smith/Palmer/Esselman/Bello/Hodges cover totals exclude in-kind).

Regime is PER candidate-cycle (`vision_lib.detect_regimes`, decisions printed — eyeball
them): Herriman's Schedule A/B are per-period, so most filers are incremental (sum periods);
a candidate who restates cumulatively is detected and marked cumulative. Correct a
mis-shaped cycle via `cycle_overrides.csv` (cycle_totals.py), NEVER by editing a cache/CSV.

Regenerate, never hand-edit the CSVs.  python3 build_finance.py
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import driver       # noqa: E402
import vision_lib   # noqa: E402

VISION_DIR = HERE / "vision"
RAW_DIR = HERE / "raw"
FAMILY = "vision_cache"


# ------------------------------------------------------------ born-digital §10-3-208 parser
# PROMOTION SURVEY VERDICT (2026-07-19): HERRIMAN-ONLY, promotion to families/ DECLINED.
# Anchor-grep found the §10-3-208 statutory phrases ("Itemized Contributions", "Sum of
# subtotals from all Schedule A", ...) in 9 other cities' born-digital filings (bluffdale
# 35, murray 30, SSL 9, white_city 7, ...), but a ground-truth run of THIS parser over 15
# sample filings from bluffdale/murray/SSL/white_city/EC reconciled 0 of 15 both sides
# (1 single-side match): each city renders the form with its own column geometry, total-
# line labels and row-wrap behavior, so the shared statutory language does NOT make a
# shared parseable layout. The parser stays city-local; other cities keep their audited
# vision/text caches.
def _norm_lig(s):
    """Normalize the born-digital font/ligature corruption (Ɵ->ti, ﬀ/ﬁ/ﬂ ligatures)."""
    for k, v in {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}.items():
        s = s.replace(k, v)
    return s.replace("Ɵ", "ti")


# a REAL amount is $-prefixed OR carries a decimal .dd; bare integers (street numbers, zips,
# phone fragments) are NOT money.
_AMT = re.compile(r"\$\s?-?[\d,]+(?:\.\d{1,2})?|(?<![\d.,])-?[\d,]*\.\d{1,2}")
# in-region label lines only (rows are already bounded to a schedule); narrow so a data row
# containing 'Candidate Apparel' etc. is NOT skipped.
_SKIP = re.compile(
    r"subtotal for this page|total contributions received|total expenditures made|"
    r"sum of subtotals|aggregate total of|subtotal of dona|^\s*\$?50\.00\s*\+?\s*$|"
    r"name of (contributor|recipient)|complete mailing|amount of\b|^\s*contribution\s*$|"
    r"date received|date of\b|political purpose|summary page|column [ab]\b|this period|"
    r"year-?\s*to|attach additional|of \$?50 or less", re.I)
_AGG = re.compile(r"aggregate total of|subtotal of dona", re.I)
_DATELEAD = re.compile(
    r"^[\s|]*(\d{1,2}[/\-.]\d{1,2}(?:[/\-.]\d{2,4})?|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s*\d{0,4})", re.I)


def _rightmost_money(line):
    best = None
    for m in _AMT.finditer(line):
        t = m.group(0).replace("$", "").replace(",", "").replace(" ", "")
        if t in ("", "-", "."):
            continue
        try:
            v = float(t)
        except ValueError:
            continue
        best = (v, m.start())
    return best


def _name_date(ln, upto):
    prefix = ln[:upto].rstrip()
    dm = _DATELEAD.match(prefix)
    date, body = "", prefix
    if dm:
        date, body = dm.group(1), prefix[dm.end():].strip()
    body = body.strip().lstrip("|").strip()
    return date, [t for t in re.split(r"\s{2,}", body) if t.strip()]


def _section_rows(lines, s, e, is_contrib):
    """A data row is (optional date)+name+rightmost amount. A long name+address wraps the
    amount to the next line -> pair the money-only line with the pending name row. The ≤$50
    aggregate -> a blank-name row (stated amount, no fabricated identity)."""
    rows, pending = [], None
    for k in range(s, e):
        ln = lines[k]
        if not ln.strip():
            continue
        if _AGG.search(ln):
            rm = _rightmost_money(ln)
            rows.append(dict(date="", name="", amount=(rm[0] if rm else None),
                             in_kind=False, agg=True))
            pending = None
            continue
        if _SKIP.search(ln):
            continue
        rm = _rightmost_money(ln)
        if not rm:
            date, fields = _name_date(ln, len(ln))
            name = fields[0].strip() if fields else ""
            if name:
                pending = (date, name, " ".join(fields[1:]).strip())
            continue
        val, st = rm
        if val == 0:
            continue
        date, fields = _name_date(ln, st)
        name = fields[0].strip() if fields else ""
        if not name:
            if pending is not None:          # wrapped amount -> attach to pending name row
                d, nm, pp = pending
                row = dict(date=d, amount=val, in_kind=False)
                if is_contrib:
                    row["name"] = nm
                else:
                    row["recipient"] = nm
                    row["purpose"] = pp
                rows.append(row)
                pending = None
            continue                          # else money-only total artifact
        purpose = " ".join(fields[1:]).strip() if (not is_contrib and len(fields) > 1) else ""
        row = dict(date=date, amount=val, in_kind=False)
        if is_contrib:
            row["name"] = name
        else:
            row["recipient"] = name
            row["purpose"] = purpose
        rows.append(row)
        pending = None
    return rows


def _stdform_parse(pdf_path):
    """Parse a born-digital §10-3-208 Schedule A/B/C form -> a vision-cache-shaped dict, or
    None when the section headers did not render (no reliable contrib/expend split)."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
                         capture_output=True, text=True).stdout
    lines = _norm_lig(txt).splitlines()
    n = len(lines)

    def find(pat, start=0, end=None):
        for i in range(start, end or n):
            if re.search(pat, lines[i], re.I):
                return i
        return None

    a0 = find(r"itemized contribu")
    b0 = find(r"itemized expenditure")
    c0 = None
    for i, ln in enumerate(lines):
        if re.search(r"in-?kind and other nonmonetary", ln, re.I) and not re.search(r"attach", ln, re.I):
            c0 = i
            break
    if a0 is None and b0 is None:
        return None                                  # headers unrendered -> defer

    a_end = b0 if b0 else (c0 if c0 else n)
    a_start = (a0 + 1) if a0 is not None else (0 if b0 is not None else None)
    contribs = _section_rows(lines, a_start, a_end, True) if a_start is not None else []
    b_end = c0 if c0 else n
    sp = find(r"summary page", b0 or 0)
    if sp and (not c0 or sp < c0):
        b_end = min(b_end, sp)
    expends = _section_rows(lines, (b0 + 1), b_end, False) if b0 is not None else []
    inkind = _section_rows(lines, (c0 + 1), n, True) if c0 is not None else []
    for r in inkind:
        r["in_kind"] = True
        r.pop("agg", None)
    contribs = contribs + inkind

    def anchor(pat):
        for ln in lines:
            if re.search(pat, ln, re.I):
                rm = _rightmost_money(ln)
                if rm:
                    return rm[0]
        return None

    def last_money(s, e):
        v = None
        for k in range(s, min(e, n)):
            if _SKIP.search(lines[k]) or _AGG.search(lines[k]):
                continue
            rm = _rightmost_money(lines[k])
            if rm and rm[0] != 0:
                v = rm[0]
        return v

    def first_not_none(*vals):
        for v in vals:
            if v is not None:
                return v          # explicit: a real $0.00 total is valid, not falsy-skipped
        return None

    stated_c = first_not_none(anchor(r"sum of subtotals from all schedule a"),
                              anchor(r"total contributions received"))
    if stated_c is None and any("name" in r for r in contribs) and b0 is not None:
        stated_c = last_money(a_start, b0)           # unlabeled Schedule A grand total fallback
    stated_e = first_not_none(anchor(r"sum of subtotals from all schedule b"),
                              anchor(r"total expenditures made"))
    return dict(contributions=contribs, expenditures=expends,
                total_contributions=stated_c, total_expenditures=stated_e)


def _text_result(cache, meta):
    """Text-parsed cache dict -> the driver's parse-shaped result (honest extract_method)."""
    crows, erows = vision_lib._rows_from(cache, meta, "herriman_stdform/text")
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=vision_lib.vmoney(cache.get("total_contributions")),
                stated_expend=vision_lib.vmoney(cache.get("total_expenditures")),
                stated_begin=None, stated_end=None,
                notes="born-digital §10-3-208 Schedule A/B/C text parsed (pdftotext -layout)")


# ---------------------------------------------------------------------------- driver wiring
def _meta(ix):
    return dict(
        candidate=ix["candidate"].strip(),
        office=(ix.get("office") or "").strip(),
        seat=(ix.get("district") or "").strip(),
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",           # Herriman files election-cycle C&E only (no annual regime)
    )


def _cache_for(ix):
    """The cache dict driving this filing: vision cache (scanned) else born-digital text
    parse. Duplicate re-uploads carry NO cache (superseded). Returns (cache, kind)."""
    if (ix.get("duplicate_of") or "").strip():
        return None, "duplicate"
    vc = vision_lib.load_cache(VISION_DIR, ix["path"])
    if vc is not None:
        return vc, "vision"
    if (ix.get("format") or "").strip() == "text":
        parsed = _stdform_parse(RAW_DIR / os.path.basename(ix["path"]))
        if parsed is not None:
            return parsed, "text"
        return None, "text-unrendered"
    return None, "none"


def _no_cache_note(ix, kind):
    if kind == "duplicate":
        return (f"not built (byte-identical duplicate re-upload; superseded — canonical "
                f"docid {ix['duplicate_of']} carries the money; do not sum — 2026-07-17)")
    if kind == "text-unrendered":
        return ("not built (born-digital §10-3-208 text layer present but Schedule A/B "
                "section headers did not render in pdftotext -> no reliable contrib/expend "
                "split; deferred to a vision tranche 2026-07-17, see AVAILABILITY.md)")
    return "not built (no vision cache and no parseable text layer — 2026-07-17)"


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    caches = {ix["path"]: _cache_for(ix) for ix in index_rows}

    # regime pre-pass: per-candidate-cycle incremental vs cumulative (duplicates excluded)
    filings = [dict(candidate=ix["candidate"].strip(),
                    election_year=(ix.get("election_year") or "").strip(),
                    filing_date=(ix.get("date") or "").strip(),
                    cache=caches[ix["path"]][0]) for ix in index_rows]
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    # Evidence-based regime correction (rollout step 4 — eyeball the decisions): the detector
    # marked Lorin Palmer 2025 'cumulative' from a monotone STATED sequence (406→1625→3510),
    # but the three filings' itemized donor rosters are MUTUALLY DISJOINT — a per-period chain
    # whose period totals merely grew. Force incremental so filing_totals does not mislabel the
    # Oct-28 interim as a superseded cumulative snapshot. (The cycle number itself is set by
    # cycle_overrides.csv, since the Dec-4 'summary' is ALSO a period report.)
    modes[("Lorin Palmer", "2025")] = "incremental"
    print("  regime CORRECTION Lorin Palmer 2025: -> incremental (itemized donor rosters "
          "mutually disjoint across all 3 filings; per-period, not cumulative)")

    def _mode_of(cand, year, members):
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental") == "incremental")
        cache, kind = caches[ix["path"]]
        if cache is None:
            return vision_lib.empty_result(_no_cache_note(ix, kind))
        if kind == "text":
            return _text_result(cache, meta)
        return vision_lib.build_result(cache, meta, FAMILY)

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),   # never reached (override returns)
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=lambda ix: True,           # all 50 index rows are C&E disclosures (no COI set)
        reconcile_cash_only=True,              # cover TOTAL counts cash only; in-kind separate
        dedup_mode=_mode_of,                   # PER-CANDIDATE
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
