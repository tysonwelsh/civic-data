#!/usr/bin/env python3
"""build_finance.py — Town of Alta driver for the structured campaign-finance layer.

Vision-cache wave (2026-07-17; family `vision_cache`, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference implementation: midvale). Alta's 36
index filings split three ways:

  * 21 SCANNED money reports -> consumed from `vision/<sha1(index_path)[:8]>.json`
    (the read-tool transcription caches) via `vision_lib.build_result`.
  * 6 BORN-DIGITAL `format=text` money reports -> parsed HERE at build time with a small
    pdftotext grammar (`_parse_text_form`). This is where the town's substantive 2025
    money lives and it was correctly NOT vision-cached (real text layer): Roger Bourke's
    itemized $2,000 Abundance Political Consulting PAC contribution (2025-10-03) and John
    Byrne's $4,725.11 self-funded-then-refunded pair (2025-11-19). Dropping these would
    falsify the town's money picture, so they are captured as rows here.
      - Two form eras: the 2025 "CAMPAIGN FINANCIAL REPORT - 2025" form (cover lines
        1a/1b contributions, 2a/2b expenditures, Form A/B itemized sheets) and the older
        2021 "Campaign Financial Report" (>$25 / <=$25 tiers, no itemized sheets).
      - Byrne's final has NO cover text layer (scanned cover) — only two born-digital
        itemized lines; parsed headerless (3 cols = contribution, 4 cols incl. purpose =
        expenditure/refund). Cover totals stay blank -> reconcile UNKNOWN, money kept.
      - Moxley's final is born-digital but its field overlay is pdftotext MOJIBAKE
        (U+FFFD); it is a nil report per AVAILABILITY -> honest inventory-only row, no
        fabricated totals.
  * 8 declaration_of_candidacy filings -> OUT OF SCOPE (no C&E lines).
  * the 2021 "All campaign financial disclosures" combined bundle is a DUPLICATE of the
    four individual 2021 reports (each transcribed/parsed separately) -> inventory-only
    row with a dated no-parse note, never summed (the midvale duplicate-copy convention).

PER-CANDIDATE REGIME (`vision_lib.detect_regimes`): most Alta candidate-cycles are nil or
single-filing, but Schilling 2023 files 4 duplicate reports that each restate the same
lone $69.96 USPS expenditure -> detected cumulative (latest wins, never summed). Decisions
are printed below; correct a mis-shaped cycle via `cycle_overrides.csv`, never by editing
caches/CSVs.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv /
donor_aliases.csv / cycle_overrides.csv.

    python3 build_finance.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))

import csv  # noqa: E402

import driver  # noqa: E402
import vision_lib  # noqa: E402

VISION_DIR = HERE / "vision"
RAW_DIR = HERE / "raw"
FAMILY = "vision_cache"

# the 2021 combined-bundle duplicate — parsed nowhere (its four member reports are each in
# the index and transcribed/parsed on their own); kept as an inventory-only row.
BUNDLE_PATH = "raw/2021_all-campaign-financial-disclosures.pdf"


def _meta(ix):
    return dict(
        candidate=ix["candidate"].strip(),
        office=(ix.get("office") or "").strip(),
        seat="",                       # Alta is AT-LARGE (no districts / no district column)
        election_year=(ix.get("election_year") or "").strip(),
        filing_date=(ix.get("date") or "").strip(),
        reporting_period=(ix.get("reporting_period") or "").strip(),
        filing_type=(ix.get("filing_type") or "").strip(),
        source_filing=ix["path"],
        document_id=vision_lib.cache_key(ix["path"]),
        filing_regime="",              # Alta files election-cycle C&E only (no annual regime)
    )


# ------------------------------------------------------------ born-digital text parsing

_NUMLINE = re.compile(r"^\$?-?[\d,]+(?:\.\d+)?$")
_MONEYTOK = re.compile(r"\$-?[\d,]+(?:\.\d+)?")
_DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
_MONEYCOL = re.compile(r"\$?-?[\d,]+\.?\d*$")


def _num(s):
    s = s.strip()
    if not _NUMLINE.match(s):
        return None
    try:
        return float(s.replace("$", "").replace(",", ""))
    except ValueError:
        return None


def _block_value(lines, start_re, end_re):
    """The single numeric form-field value in a cover block (between a header anchor and
    its 'Form X total' / end anchor). Alta cover fills EITHER the aggregate OR the itemized
    line, so a block holds one value (equal zeros collapse to one). Also grabs a value glued
    onto the header line itself ('Expenditures ... $0')."""
    vals, inside = [], False
    for ln in lines:
        s = ln.strip()
        if not inside and re.search(start_re, s):
            inside = True
            for tok in _MONEYTOK.findall(s):            # value glued to the header line
                v = _num(tok)
                if v is not None:
                    vals.append(v)
            continue
        if inside and re.search(end_re, s):
            break
        if inside:
            v = _num(s)
            if v is not None:
                vals.append(v)
    if not vals:
        return None
    uniq = sorted({round(v, 2) for v in vals})
    if len(uniq) == 1:
        return vals[0]
    nz = [v for v in uniq if abs(v) > 0.005]
    return nz[0] if nz else uniq[-1]                    # prefer the filled (non-zero) line


def _inkind_col(lines, start_re, end_re):
    """Character column where the Form-A 'In-Kind (if applicable)' header begins (a value at
    or past it is an in-kind contribution, not cash), or None if the region has no such column."""
    inside = False
    for ln in lines:
        s = ln.strip()
        if not inside:
            if re.search(start_re, s):
                inside = True
            continue
        if end_re and re.search(end_re, s):
            break
        if "In-Kind" in ln:
            return ln.index("In-Kind")
    return None


def _itemized(lines, start_re, end_re, inkind_col=None):
    """Position-aware Form A/B row parse -> [(date, name, amount, purpose, in_kind)].
    Money tokens are located by column: on Form A a value at/after the 'In-Kind' header
    column is an in-kind contribution (Bourke 2025's $2,000 Abundance line sits there, with
    the 'Amount of Contribution' column blank). N/A / None placeholders skipped."""
    rows, inside = [], False
    for ln in lines:
        s = ln.strip()
        if not inside:
            if re.search(start_re, s):
                inside = True
            continue
        if end_re and re.search(end_re, s):
            break
        first = s.split(None, 1)
        if not first or not _DATE.match(first[0]):
            continue
        # money tokens to the RIGHT of the name band (col > 40 excludes the leading date)
        money = [(m.start(), m.group(0)) for m in re.finditer(r"\$?-?[\d,]+\.?\d*", ln)
                 if m.start() > 40 and any(ch.isdigit() for ch in m.group(0))
                 and _MONEYCOL.fullmatch(m.group(0).strip())]
        if not money:
            continue
        cash = [(c, t) for (c, t) in money if inkind_col is None or c < inkind_col - 4]
        inkind = [(c, t) for (c, t) in money if inkind_col is not None and c >= inkind_col - 4]
        col, tok = (cash[0] if cash else inkind[0])
        is_inkind = not cash and bool(inkind)
        name = ln[:col].strip()
        name = name[len(first[0]):].strip() if name.startswith(first[0]) else name
        if name.upper() in ("N/A", "NONE", ""):
            continue
        purpose = ln[col + len(tok):].strip()
        rows.append((first[0], name, tok.replace("$", "").replace(",", ""), purpose, is_inkind))
    return rows


def _parse_text_form(pdf_path):
    """pdftotext -layout -> a vision-cache-shaped dict, or None when the text is unusable
    (mojibake). Contributions/expenditures verbatim; cover totals where cleanly printed."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"],
                         capture_output=True, text=True).stdout
    if txt.count("�") >= 3:                        # garbled field overlay (Moxley)
        return None
    lines = txt.splitlines()
    era_a = "CAMPAIGN FINANCIAL REPORT - 2025" in txt
    era_b = "Total contributions of donors who gave more than $25" in txt
    out = dict(contributions=[], expenditures=[], total_contributions=None,
               total_expenditures=None, beginning_balance=None, ending_balance=None)
    if era_a:
        out["total_contributions"] = _block_value(lines, r"^Contributions\b", r"Form\s*.?A.?\s*total")
        out["total_expenditures"] = _block_value(lines, r"^Expenditures\b", r"Form\s*.?B.?\s*total")
        out["ending_balance"] = _block_value(lines, r"Form\s*.?B.?\s*total", r"^NOTE:")
        ik = _inkind_col(lines, r"ITEMIZED CONTRIBUTION REPORT", r"ITEMIZED EXPENDITURE REPORT")
        out["contributions"] = [dict(date=d, name=n, amount=a, in_kind=k) for (d, n, a, _p, k) in
                                _itemized(lines, r"ITEMIZED CONTRIBUTION REPORT",
                                          r"ITEMIZED EXPENDITURE REPORT", ik)]
        out["expenditures"] = [dict(date=d, recipient=n, amount=a, purpose=p) for (d, n, a, p, _k) in
                               _itemized(lines, r"ITEMIZED EXPENDITURE REPORT", None)]
    elif era_b:
        def above(label_re):
            for i, ln in enumerate(lines):
                if re.search(label_re, ln):
                    for j in range(i - 1, max(-1, i - 4), -1):
                        v = _num(lines[j].strip())
                        if v is not None:
                            return v
            return None
        c1 = above(r"Total contributions of donors who gave more than \$25")
        c2 = above(r"Aggregate total of contributions of \$25 or less")
        out["total_contributions"] = (round((c1 or 0) + (c2 or 0), 2)
                                      if (c1 is not None or c2 is not None) else None)
        out["total_expenditures"] = above(r"Total Campaign Expenses")
        out["ending_balance"] = above(r"Balance at the end")
    else:
        # headerless (Byrne final): bare itemized lines. 3 cols = contribution;
        # 4+ cols (trailing purpose) = expenditure/refund.
        for ln in lines:
            cols = [c for c in re.split(r"\s{2,}", ln.strip()) if c]
            if len(cols) < 3 or not _DATE.match(cols[0]):
                continue
            mi = next((i for i in range(len(cols) - 1, 0, -1)
                       if _MONEYCOL.fullmatch(cols[i].strip())), None)
            if mi is None:
                continue
            name = " ".join(cols[1:mi]).strip()
            amt = cols[mi].replace("$", "").replace(",", "")
            purpose = " ".join(cols[mi + 1:]).strip()
            (out["expenditures"].append(dict(date=cols[0], recipient=name, amount=amt, purpose=purpose))
             if purpose else
             out["contributions"].append(dict(date=cols[0], name=name, amount=amt)))
    return out


def _text_result(ix, meta):
    """Born-digital text filing -> driver result dict (rows via the shared vision row-builder,
    honest extract_method + note)."""
    parsed = _parse_text_form(RAW_DIR / os.path.basename(ix["path"]))
    if parsed is None:
        return vision_lib.empty_result(
            "not itemized (born-digital text but pdftotext yields mojibake field overlay; "
            "nil report per AVAILABILITY — inventory-only, no totals fabricated 2026-07-17)")
    crows, erows = vision_lib._rows_from(parsed, meta, f"{FAMILY}/text")
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=vision_lib.vmoney(parsed.get("total_contributions")),
                stated_expend=vision_lib.vmoney(parsed.get("total_expenditures")),
                stated_begin=vision_lib.vmoney(parsed.get("beginning_balance")),
                stated_end=vision_lib.vmoney(parsed.get("ending_balance")),
                notes="born-digital text (pdftotext -layout parse)")


def main():
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        index_rows = list(csv.DictReader(fh))

    in_scope = lambda ix: (ix.get("filing_type") or "").strip() != "declaration_of_candidacy"

    # regime pre-pass: per-candidate-cycle incremental vs cumulative, from the caches
    filings = [dict(candidate=ix["candidate"].strip(),
                    election_year=(ix.get("election_year") or "").strip(),
                    filing_date=(ix.get("date") or "").strip(),
                    cache=vision_lib.load_cache(VISION_DIR, ix["path"]))
               for ix in index_rows if in_scope(ix)]
    print("per-candidate regime decisions (evidence-based; cycle_overrides.csv corrects):")
    modes = vision_lib.detect_regimes(filings)

    def _mode_of(cand, year, members):
        return modes.get((cand, year), "incremental")

    def _rows_override(ix, meta):
        meta["is_incremental"] = str(
            modes.get((meta["candidate"], meta["election_year"]), "incremental") == "incremental")
        if ix["path"] == BUNDLE_PATH:
            return vision_lib.empty_result(
                "not parsed (DUPLICATE combined bundle of the four individual 2021 reports, "
                "each transcribed/parsed separately — never summed; 2026-07-17)")
        cache = vision_lib.load_cache(VISION_DIR, ix["path"])
        if cache is not None:
            return vision_lib.build_result(cache, meta, FAMILY)
        return _text_result(ix, meta)

    driver.run(
        here=HERE, family_id=FAMILY,
        meta_fn=_meta,
        sidecar_fn=lambda ix: str(HERE / "text" / "_none_"),   # never reached: override always returns
        is_scanned_fn=lambda ix: (ix.get("format") or "") == "scanned",
        in_scope_fn=in_scope,
        reconcile_cash_only=False,      # Alta cover total is a single figure; no separate in-kind line
        dedup_mode=_mode_of,
        amend_fn=lambda ix: "amend" in (ix.get("title", "").lower()
                                        + os.path.basename(ix.get("path", "")).lower()),
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
