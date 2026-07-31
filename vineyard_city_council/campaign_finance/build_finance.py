#!/usr/bin/env python3
"""build_finance.py — Vineyard driver for the structured campaign-finance layer.

Vineyard self-hosts its municipal campaign Contribution & Expenditure reports (legacy cycles
survive only in the Internet Archive), on the SAME statutory Utah municipal "Municipal Campaign
Financial Disclosure" form (UCA 10-3-208) that Orem/Logan/Nephi use. So Vineyard REUSES the shared
`utah_standard_form` family UNCHANGED — no edit to the shared family; label/layout drift is handled
via `meta["form_opts"]` overrides + a Vineyard-specific cover-total reader in this driver.

Vineyard is the MIXED case, like Orem: BOTH born-digital (`format=text`, pdftotext) AND scanned
(`format=scanned`, tesseract OCR / handwritten) filings, plus 4 archive-truncated (1-MiB Wayback
truncation) filings that cannot be read at all.

WHY THIS DRIVER DOES MORE THAN A THIN form_opts SWAP (the empirical Vineyard reality):
Vineyard's form is a FILLABLE PDF whose typed values render irregularly through pdftotext/OCR:
  * cover-block totals FLOAT — above, below, or inside the "$ ____" underscore field ("$ ___$3,848.00___",
    "5094.24" on the line ABOVE the label, "1451.50" on the line BELOW) — so the family's own numbered-
    headline fallback (which reads money ON the label line) cannot recover most of them; and
  * itemized amounts are often BARE numbers (no `$`, e.g. Welsh "250"/"500"/"1520") and/or in multi-line
    cells (donor name on a separate line from the amount), which the anti-fabrication `$`-anchored money
    tokenizer (correctly) will not read.
So a naive family parse would FALSE-NIL a real filing (section detected, 0 `$`-rows, no `$`-total ->
the family coerces the section total to $0 and "reconciles" a real filing as nil). This driver prevents
that and maximizes honest reconciliation with three moves, NONE of which touch the shared family:

  1. SCANNED path: family runs with sections SENTINELED OFF (Logan recipe) so a detected-but-unreadable
     section is never coerced to a false $0 nil. Content scanned filings therefore flag -> vision.
  2. BORN-DIGITAL path (`_borndigital`): the family runs with sections ON (Vineyard headers) to capture
     the clean `$`-anchored rows, and this driver OVERRIDES the stated totals with a ROBUST cover reader
     (`_robust_cover`) that follows the floating fillable-field value (above/below/inline). A born-digital
     filing whose rows are bare/multi-line reads 0 rows against a nonzero cover total -> it flags (NOT a
     false nil) -> vision. So born-digital reconciles DIRECTLY where its rows carry `$`; else it escalates.
  3. VISION path (`_vision_result`, GATED): any filing (born-digital OR scanned) that did not both-
     reconcile after the text/OCR pass is transcribed by `vineyard_vision_extract.py` (claude-sonnet-5,
     strict "transcribe exactly / never infer"), cached to `vision/<doc8>.json`, fed back through the SAME
     reconciliation via this `rows_override_fn`. A figure that will not reconcile stays blank +
     needs_review + low — never guessed.

TRUNCATED (4): the archive-truncated filings (extraction_method `unreadable:*`) are 1-MiB Wayback
truncations whose text sidecar is header-only. They emit an honest all-blank filing_totals row
(stated + itemized blank, needs_review, `low`, note) — never a fabricated figure. Vision is attempted
(pdftoppm on a truncated PDF usually renders nothing -> stays blank); if a legible total is recovered it
is used.

DEDUP — MIXED, empirically determined per candidate (like Logan/Nephi; do NOT assume one rule). Vineyard
files interim + summary per cycle and the summary is almost always NIL (nothing new after the election),
i.e. each report covers a DISCRETE period -> predominantly INCREMENTAL. `is_incremental` is set PER
(candidate, election_year) from the contribution-row overlap between consecutive reports
(`_classify_modes`); `dedup_mode=None` (no uniform supersession asserted). Note Vineyard cycles run
2015-2025 but only 2019/2021/2025 join elections; 2015/2017 are pre-floor (still structured; the pre-floor
status lives in index.csv `join_confidence=pre_floor`). 2023 is unrecoverable (0 filings).

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py            # (run vineyard_vision_extract.py between passes for escalation)
"""
from __future__ import annotations

import csv as _csv
import hashlib
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance" / "families"))

import driver   # noqa: E402
import common   # noqa: E402
import registry  # noqa: E402
from common import ContribRow, ExpendRow, parse_date  # noqa: E402

VISION_DIR = HERE / "vision"

# ---- Vineyard form_opts for the shared utah_standard_form family (NO family edit) ----
# SCANNED path: sentinel the itemized-section headers OFF (Logan recipe) so a detected-but-
# unreadable OCR/handwritten section is never coerced to a false $0 nil. The numbered-cover
# labels below let the family's fallback recover a stated total when the OCR cover is legible;
# content scanned filings otherwise flag -> vision.
VINEYARD_SCANNED_OPTS = dict(
    sec_cashc=r"(?!)",
    sec_inkind=r"(?!)",
    sec_cashe=r"(?!)",
    # The numbered-headline fallback is sentineled OFF too: Vineyard's cover labels PRINT the
    # "$50.00" / "$500.00" statutory THRESHOLD, which the shared (threshold-blind) family fallback
    # would read as a fabricated stated total (e.g. $500+$500=$1,000) on a garbled OCR cover. So the
    # scanned path never trusts a family-read total; the stated total for a scanned filing comes ONLY
    # from its vision transcription (threshold-aware). A scanned filing with no legible vision total
    # is honestly left blank/unknown, never a threshold artifact.
    l1=r"(?!)", l2=r"(?!)", l3=r"(?!)",
    cash_inkind=r"(?!)", cash_exp2=r"(?!)",
)
# BORN-DIGITAL path: sections ON so the family captures the clean $-anchored rows. Vineyard's
# contribution section is headed either "Itemized Contribution Report (Form A)" or just the
# "Name of Contributor" column header; expenditure section "Itemized Expenditure Report" or
# "Name of Payee". No in-kind SECTION (in-kind is a donation-type column) -> sentineled off.
VINEYARD_BORN_OPTS = dict(
    sec_cashc=r"itemized contribution report|name of contributor",
    sec_inkind=r"(?!)",
    sec_cashe=r"itemized expenditure report|name of payee",
    # stated totals for born-digital come from _robust_cover (threshold-aware), so the family's own
    # numbered-headline fallback is unused here too -> sentineled off.
    l1=r"(?!)", l2=r"(?!)", l3=r"(?!)", cash_inkind=r"(?!)", cash_exp2=r"(?!)",
)


def _did8(ix):
    """Stable 8-char filing id from the dataset-relative path (unique across the 59 filings;
    Vineyard has no multi-candidate compilations)."""
    return hashlib.sha1(ix["path"].encode("utf-8")).hexdigest()[:8]


def _is_truncated(ix):
    return (ix.get("extraction_method") or "").startswith("unreadable")


def _office_seat(ix):
    """Vineyard is Mayor + at-large council (no districts) -> (office, '')."""
    o = (ix.get("office") or "").strip()
    return ("Mayor" if o.lower().startswith("mayor") else "Council"), ""


def _sidecar(ix):
    # Vineyard text sidecars are nested by cycle: text/<cycle>/<stem>.txt
    p = Path(ix["path"])                       # raw/<cycle>/<stem>.pdf
    return HERE / "text" / p.parent.name / f"{p.stem}.txt"


# ---------------------------------------------------------------- robust cover-total reader

def _tofloat(s):
    try:
        return float(s.replace(",", "").replace("$", ""))
    except (ValueError, AttributeError):
        return None


def _lone_num(line):
    """A line that is (essentially) just a number -> its value, else None. Strips the fillable-
    field underscores/whitespace. Used to follow a cover value that floated onto its own line."""
    s = (line or "").strip().strip("_").replace(" ", "").replace("_", "")
    m = re.fullmatch(r"\$?([\d,]+(?:\.\d{1,2})?)", s)
    return _tofloat(m.group(1)) if m else None


def _after_last_dollar(line):
    """The number immediately following the LAST '$' on the line (the fillable field's '$'), or
    None. This skips any '$50.00' / '$500.00' threshold printed INSIDE the label text (those are
    left of the field's '$'), and returns the typed value where it rendered inline."""
    idx = line.rfind("$")
    if idx < 0:
        return None
    tail = line[idx + 1:]
    m = re.match(r"[\s_]*([\d,]+(?:\.\d{1,2})?)", tail)
    return _tofloat(m.group(1)) if m else None


_THRESH1 = re.compile(r"\$?\s*(?:50|500)(?:\.00)?\s+or\s+(?:more|less)", re.I)
_THRESH2 = re.compile(r"(more than|under|totaling)\s*\$?\s*(?:50|500)(?:\.00)?", re.I)


def _strip_threshold(s):
    """Remove the printed '$50.00' / '$500.00' THRESHOLD from a cover label so it is never mistaken
    for the candidate's typed field value ('more than $50.00' / 'under $500.00' / '$500.00 or more')."""
    return _THRESH2.sub(lambda m: m.group(1) + " ", _THRESH1.sub(" ", s))


def _value_near(lines, i):
    """Cover value for the label on line i: inline after the field '$', else a lone number that
    floated onto the adjacent line (above first, then below). The printed $50/$500 threshold is
    stripped first so it is never read as the value."""
    v = _after_last_dollar(_strip_threshold(lines[i]))
    if v is not None:
        return v
    for j in (i - 1, i + 1):
        if 0 <= j < len(lines):
            lv = _lone_num(lines[j])
            if lv is not None:
                return lv
    return None


_C_GT = re.compile(r"contributions of (?:donors who gave )?more than|itemized total of contributions", re.I)
_C_LE = re.compile(r"contributions of \$?50(?:\.00)? or less|aggregate total of contributions under", re.I)
_C_TOT = re.compile(r"total contributions \(form", re.I)                 # 2019 explicit total line
_E_OLD = re.compile(r"total campaign expens", re.I)                      # 2015/2019 "Total Campaign expenses"
_E_ITEM = re.compile(r"itemized total of campaign expenditures", re.I)   # 2021/2025 2b
_E_AGG = re.compile(r"aggregate total of campaign expenditures under", re.I)  # 2021/2025 2a
_BAL = re.compile(r"balance at the end", re.I)


def _first(lines, rx):
    for i, ln in enumerate(lines):
        if rx.search(ln):
            return _value_near(lines, i)
    return None


def _robust_cover(text):
    """Read the stated (candidate-printed) totals from Vineyard's numbered COVER block, following
    the fillable value wherever it rendered (inline / above / below). Returns
    (stated_contrib, stated_expend, ending_balance, le_agg, e_agg) — floats or None. Covers all
    three Vineyard layouts (2015, 2019, 2021/2025).

    RECONCILIATION ANCHOR = the ITEMIZED (Form-A / Form-B) total the listed rows sum to:
      * 2019 form   -> line 3 "Total Contributions (Form A total)" (= c_tot);
      * 2015 form   -> line 1 "Total Contributions ... more than $50.00 (Form A total)" (= c_gt);
      * 2021/2025   -> line 1b "Itemized total of contributions" (= c_gt).
    The ≤$50 / ≤$500 UNITEMIZED aggregate (c_le / e_agg) is NOT added to the stated total (that would
    break the itemized reconciliation) — it is returned for the filing note, the Orem/Nephi discipline.
    None where blank/'n/a' — never a fabricated figure."""
    lines = text.splitlines()
    c_tot, c_gt, c_le = _first(lines, _C_TOT), _first(lines, _C_GT), _first(lines, _C_LE)
    stated_c = c_tot if c_tot is not None else c_gt

    e_old, e_item, e_agg = _first(lines, _E_OLD), _first(lines, _E_ITEM), _first(lines, _E_AGG)
    stated_e = e_old if e_old is not None else e_item

    return stated_c, stated_e, _first(lines, _BAL), c_le, e_agg


# ------------------------------------------------------------------ born-digital direct parse

_INKIND = re.compile(r"in[\s\-]?kind", re.I)


def _borndigital(text, meta):
    """Direct parse of a born-digital filing: the shared family (sections ON) captures the clean
    $-anchored itemized rows; this driver overrides the stated totals with the robust cover read
    (the family's own headline fallback cannot follow Vineyard's floating fillable-field values).

    A born-digital filing whose amounts are bare/multi-line reads 0 rows against a nonzero cover
    total -> it flags (needs_review) and is escalated to vision — it is NEVER coerced to a false
    nil. In-kind rows are flagged from the row's own 'In-Kind' donation-type cell."""
    family = registry.get("utah_standard_form")
    m2 = dict(meta)
    m2["form_opts"] = VINEYARD_BORN_OPTS
    m2["is_scanned"] = False
    res = family.parse(text, m2)
    stated_c, stated_e, bal, le_agg, e_agg = _robust_cover(text)
    res["stated_contrib"] = stated_c
    res["stated_expend"] = stated_e
    res["stated_end"] = bal
    lines = text.splitlines()
    for r in res["contrib_rows"]:
        try:
            ln = int(r.line_no) - 1
        except (ValueError, TypeError):
            continue
        ctx = " ".join(lines[max(0, ln - 1):ln + 2])
        if _INKIND.search(ctx):
            r.in_kind = "True"
    # Build the note fresh (DISCARD the shared family's note): with sections sometimes undetected on
    # Vineyard's fillable form the family emits a misleading "non-standard form" / threshold-derived
    # "≤$50 aggregate" line; the robust cover read above is authoritative for born-digital.
    bits = ["born-digital direct (fillable-PDF: totals read from cover block)"]
    if le_agg:
        bits.append(f"unitemized ≤$50 aggregate stated ${le_agg:.2f} (not itemized on form)")
    if e_agg:
        bits.append(f"unitemized ≤$500 expenditure aggregate stated ${e_agg:.2f}")
    res["notes"] = "; ".join(bits)
    return res


# ------------------------------------------------------------------------- vision path

def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _vision_result_for(meta, d):
    """Build a parsed-result dict from a cached Claude-vision transcription (Logan/Nephi shape)."""
    vm = meta["extract_method"].split("/")[0] + "/vision"
    inc = MODES.get((meta["candidate"], meta["election_year"]), "True")

    def _date(s):
        return parse_date(str(s)) or "" if s not in (None, "", "null") else ""

    crows = []
    for i, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental=inc,
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for i, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental=inc,
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))

    def _anchor(itemized, grand, under):
        """Reconciliation anchor = the ITEMIZED (Form A/B) total the listed rows sum to; fall back
        to an explicit grand total, then to an aggregate-only figure (which flags totals-only when
        it has 0 rows). The ≤$50/$500 UNITEMIZED aggregate is NOT added in (that would break the
        itemized reconciliation — Orem/Nephi discipline; it is noted). A stated total is non-negative,
        so a leading '-' (dotted-leader-as-minus artifact) is normalized to magnitude."""
        for v in (_vmoney(itemized), _vmoney(grand), _vmoney(under)):
            if v is not None:
                return abs(v), (v < 0)
        return None, False

    stated_contrib, flip_c = _anchor(d.get("contributions_itemized"),
                                     d.get("total_contributions"), d.get("contributions_under_500"))
    stated_expend, flip_e = _anchor(d.get("expenditures_itemized"),
                                    d.get("total_expenditures"), d.get("expenditures_under_500"))
    notes = "vision-transcribed(claude-sonnet-5)"
    if flip_c or flip_e:
        notes += "; stated total sign normalized (dotted-leader artifact)"
    for lbl, key in (("contribution", "contributions_under_500"),
                     ("expenditure", "expenditures_under_500")):
        agg = _vmoney(d.get(key))
        if agg:
            notes += f"; ≤$500 {lbl} aggregate stated ${agg:.2f} (exemption; not itemized on form)"
    end_bal = _vmoney(d.get("ending_balance"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=stated_contrib, stated_expend=stated_expend,
                stated_begin=None, stated_end=(abs(end_bal) if end_bal is not None else None),
                notes=notes)


def _rows_override(ix, meta):
    """driver rows_override_fn. Priority: vision cache (any filing that was escalated) ->
    truncated honest-blank -> born-digital direct parse -> None (scanned family/OCR pass)."""
    cache = VISION_DIR / f"{meta['document_id']}.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        if any(d.get(k) not in (None, "", "null") for k in (
                "contributions", "expenditures", "contributions_itemized", "total_contributions",
                "expenditures_itemized", "total_expenditures", "contributions_under_500",
                "expenditures_under_500", "ending_balance")):
            return _vision_result_for(meta, d)
    if _is_truncated(ix):
        return dict(contrib_rows=[], expend_rows=[], stated_contrib=None, stated_expend=None,
                    stated_begin=None, stated_end=None,
                    notes="archive-truncated (1-MiB Wayback truncation) — unreadable; honest blank")
    if (ix.get("format") or "") == "text":
        sc = _sidecar(ix)
        if not sc.exists():
            return None
        res = _borndigital(sc.read_text(encoding="utf-8", errors="replace"), meta)
        inc = MODES.get((meta["candidate"], meta["election_year"]), "True")
        for r in res["contrib_rows"] + res["expend_rows"]:
            r.is_incremental = inc                # empirical per-candidate (family default was "True")
        return res
    return None       # scanned, no vision yet -> driver reads OCR sidecar via the family


def _meta(ix):
    office, seat = _office_seat(ix)
    return dict(
        candidate=ix["candidate"], office=office, seat=seat,
        election_year=ix["election_year"], filing_date=ix["date"],
        filing_type=ix.get("filing_type", ""), source_filing=ix["path"],
        document_id=_did8(ix), reporting_period=ix.get("filing_type", ""),
        form_opts=VINEYARD_SCANNED_OPTS)


# ---------------------------------------------------------------------- empirical dedup

def _sig_for(ix):
    """Contribution (date, amount) signatures for a filing, from the vision cache if present,
    else a born-digital direct parse, else [] (scanned-no-vision / truncated)."""
    doc8 = _did8(ix)
    cache = VISION_DIR / f"{doc8}.json"
    if cache.exists():
        d = json.loads(cache.read_text())
        return [(str(r.get("date")), str(r.get("amount"))) for r in d.get("contributions", [])]
    if (ix.get("format") or "") == "text" and not _is_truncated(ix):
        sc = _sidecar(ix)
        if sc.exists():
            m = _meta(ix)
            m["extract_method"] = "utah_standard_form/text"
            res = _borndigital(sc.read_text(encoding="utf-8", errors="replace"), m)
            return [(r.date, r.amount) for r in res["contrib_rows"]]
    return []


def _classify_modes():
    """Per-(candidate, election_year) is_incremental from consecutive-report contribution-row
    overlap (cumulative filers re-list the whole cycle -> high overlap; incremental filers list
    only new activity -> ~0). Single-report pairs default to incremental."""
    filings = defaultdict(list)
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        for ix in _csv.DictReader(fh):
            filings[(ix["candidate"], ix["election_year"])].append((ix["date"], ix))
    modes = {}
    for key, lst in filings.items():
        lst.sort(key=lambda t: t[0])
        seqs = [_sig_for(ix) for _, ix in lst]
        fracs = [len(set(a) & set(b)) / len(set(a)) for a, b in zip(seqs, seqs[1:]) if a]
        modes[key] = "False" if (fracs and statistics.median(fracs) >= 0.5) else "True"
    return modes


MODES = _classify_modes()   # {(candidate, election_year): is_incremental} — empirical, per candidate


if __name__ == "__main__":
    def _is_scanned(ix):
        # A vision-sourced filing is judged like a scan (medium ceiling); born-digital direct = text (high).
        return (ix.get("format") == "scanned") or _is_truncated(ix) \
            or (VISION_DIR / f"{_did8(ix)}.json").exists()

    driver.run(
        here=HERE, family_id="utah_standard_form",
        meta_fn=_meta, sidecar_fn=_sidecar,
        is_scanned_fn=_is_scanned,
        in_scope_fn=lambda ix: True,          # all 59 are in-scope campaign C&E reports
        reconcile_cash_only=False,            # Vineyard states TOTAL contributions incl. in-kind
        dedup_mode=None,                      # MIXED filers -> is_incremental is per-candidate
        amend_fn=lambda ix: False,            # no amendment labels in the Vineyard set
        rows_override_fn=_rows_override)
