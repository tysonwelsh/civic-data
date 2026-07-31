#!/usr/bin/env python3
"""vision_lib.py — shared helpers for VISION-CACHE-consumed campaign-finance cities.

The 2026-07-17 wave established `vision/<sha1(index_path)[:8]>.json` caches (the
"midvale convention", schema per /cf-vision-transcribe) for 14 cities whose filings are
scans (or garbled fillable templates) with NO parseable text layer. This module is the
one shared implementation those cities' thin `build_finance.py` dispatchers use, so the
cache→rows mapping, verbatim-amount normalization, and the per-candidate regime
detection live in ONE place (the taylorsville `_vision_result` pattern, generalized).

Cache schema (values VERBATIM as printed — normalize here, never edit a cache):
    {contributions: [{date, name, amount, in_kind}],
     expenditures:  [{date, recipient|payee|name, purpose, amount, in_kind}],
     total_contributions, total_expenditures,
     beginning_balance?, ending_balance?, _meta{index_path, ...}}
  Multi-report bundles (one PDF stapling several reports) MAY instead carry
  `reports: [{reporting_period?, contributions, expenditures, total_*...}]` — see
  build_result(); each sub-report becomes its own logical filing ONLY if the city's
  build passes them separately; the default treats the bundle as one filing and
  concatenates, with the bundle noted (the conservative reading — never sum a bundle's
  cover totals across sub-reports without per-city evidence).

PER-CANDIDATE REGIME (`detect_regimes`): midvale proved a single city-wide
incremental/cumulative dedup mode is WRONG — within one city (even one year) some
filers file per-period reports (sum them) and others cumulative snapshots (latest
wins). Detection evidence, strongest first:
  1. row-subset: a later filing's itemized (date, name, amount) multiset CONTAINS an
     earlier filing's rows -> cumulative chain;
  2. restatement: a later filing prints the SAME stated totals with no (or fewer)
     itemized rows -> cumulative restatement (the Wayne Sharp 2021 shape);
  3. stated-sequence: effective totals (stated, else itemized sum) non-decreasing on
     BOTH sides across the date-ordered chain -> cumulative; a material decrease on
     either side -> incremental (per-period).
Undecidable (single filing / no usable totals) -> "incremental" (a group of one is
unaffected by either marking). The decisions are PRINTED by the build so a human can
eyeball them; `cycle_overrides.csv` (cycle_totals.py) remains the documented correction
path for a mis-shaped candidate-cycle.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import common
from common import ContribRow, ExpendRow


# ---------------------------------------------------------------- normalization

_MONEY_RE = re.compile(r"-?\(?\$?\s*-?[\d,]*\.?\d+\)?")


def vmoney(s):
    """Verbatim printed amount -> float, or None (illegible/blank stays None).
    Handles '$1,050.', '1050', '(50.00)' (negative), '- 25.00'. Never guesses."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip()
    if not t or t.lower() in ("null", "none", "n/a", "-", "--"):
        return None
    m = _MONEY_RE.search(t)
    if not m:
        return None
    tok = m.group(0)
    neg = "(" in tok or tok.lstrip().startswith("-")
    tok = tok.strip("()").replace("$", "").replace(",", "").replace(" ", "").lstrip("-")
    if tok in ("", "."):
        return None
    try:
        v = float(tok)
    except ValueError:
        return None
    return -v if neg else v


_MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}
_NUM_DATE_RE = re.compile(r"^\s*(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{2,4})\s*$")
_LONG_DATE_RE = re.compile(r"^\s*([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})\s*$")


def vdate(s):
    """Verbatim printed date -> ISO, or '' (ranges / illegible / blank stay blank).
    Tolerates dots, dashes, slashes, 2-digit years, 'October 7, 2025'."""
    if s in (None, "", "null"):
        return ""
    t = str(s).strip()
    m = _NUM_DATE_RE.match(t)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        if 1 <= mo <= 12 and 1 <= d <= 31 and 2000 <= y <= 2100:
            return f"{y:04d}-{mo:02d}-{d:02d}"
        return ""
    m = _LONG_DATE_RE.match(t)
    if m and m.group(1).lower() in _MONTHS:
        return f"{int(m.group(3)):04d}-{_MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return ""


# ---------------------------------------------------------------- cache access

def cache_key(index_path, sub=None):
    """THE repo-standard vision-cache key (normative since 2026-07-19, when the legacy
    doc-id keys — millcreek/taylorsville doc ids, west_valley ADIDs, ogden view-ids, orem
    sha256[:8], sandy trailing-filename-hex — were all migrated): the cache filename is
    `sha1(index.csv path)[:8].json`. A city where ONE PDF holds multiple logical filings
    passes the per-filing discriminator as `sub` -> `sha1(path + "|" + sub)[:8]`
    (st_george: sub=candidate; nephi keys `sha1(path + "|" + page_range)` with the pipe
    always present — its own build helper, keys unchanged). Trailing-filename-hex keys are
    BANNED (the holladay collision finding)."""
    key = index_path if not sub else f"{index_path}|{sub}"
    return hashlib.sha1(key.encode()).hexdigest()[:8]


def load_cache(vision_dir, index_path):
    p = Path(vision_dir) / f"{cache_key(index_path)}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


# ---------------------------------------------------------------- cache -> rows

def _rows_from(d, meta, extract_method, line_prefix="v"):
    crows = []
    for k, r in enumerate(d.get("contributions") or []):
        amt = vmoney(r.get("amount"))
        name = (r.get("name") or r.get("donor") or "").strip()
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=vdate(r.get("date")),
            donor_raw=name, amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))),
            is_incremental=meta.get("is_incremental", ""),
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"{line_prefix}{k + 1}", extract_method=extract_method,
            needs_review="0" if (amt is not None and name) else "1"))
    erows = []
    for k, r in enumerate(d.get("expenditures") or []):
        amt = vmoney(r.get("amount"))
        payee = (r.get("recipient") or r.get("payee") or r.get("name") or "").strip()
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat=meta.get("seat", ""),
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=vdate(r.get("date")),
            vendor_raw=payee, purpose=(r.get("purpose") or "").strip() if r.get("purpose") else "",
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))),
            is_incremental=meta.get("is_incremental", ""),
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"{line_prefix}{k + 1}", extract_method=extract_method,
            needs_review="0" if amt is not None else "1"))
    return crows, erows


_MODE_NOTES = {
    "vision": "vision-transcribed(read-tool)",
    "text": "text-transcribed(born-digital layer, not vision)",
}


def build_result(cache, meta, family_id, mode="vision"):
    """Cache dict -> the parse()-shaped result the driver reconciles. Handles both the
    single-report schema and a `reports:[...]` bundle (concatenated + noted; the bundle's
    top-level stated totals are used if present, else the LAST sub-report's — a bundle's
    sub-report covers must never be summed without per-city evidence).

    `mode` (2026-07-19) makes the per-row `extract_method` label TRUTHFUL for cities whose
    cache dir mixes provenance: "vision" (default — Read-tool page-image transcription) vs
    "text" (the cache was transcribed from the filing's born-digital text layer, e.g.
    pdftotext -layout; the murray/alta/herriman convention, now available to every city
    without reimplementing this function). Pass mode="text" ONLY where the cache's
    provenance is documented (its _meta transcription note / the city build's own record) —
    never inferred from the index `format` alone (riverton proved format=text can be a
    mislabeled handwritten scan). The label changes extract_method + the filing note only;
    parsing, normalization and reconciliation are identical."""
    vm = f"{family_id}/{mode}"
    notes = [_MODE_NOTES.get(mode, f"{mode}-transcribed")]
    if "reports" in cache and cache.get("reports"):
        reps = cache["reports"]
        crows, erows = [], []
        for j, rep in enumerate(reps):
            # RESTATEMENT sub-report: some filings staple a "Summary Column A / total
            # thru <prior deadline>" copy of the PRIOR report ahead of the filing's own
            # period (the Bryant Brown 2025-10-28 shape). Its rows duplicate a sibling
            # filing already in the index — including them double-counts. Detected from
            # the transcribed sub-report's OWN label (never guessed); excluded + noted.
            label = rep.get("reporting_period") or ""
            if j < len(reps) - 1 and re.search(r"(?i)column\s*a\b", label):
                notes.append(f"sub-report {j + 1} is a Column-A prior-period "
                             f"restatement ({label[:60]!r}) — rows excluded to avoid "
                             f"double-counting the prior filing")
                continue
            c, e = _rows_from(rep, meta, vm, line_prefix=f"r{j + 1}v")
            crows.extend(c)
            erows.extend(e)
        last = reps[-1]
        stated_c = vmoney(cache.get("total_contributions"))
        stated_e = vmoney(cache.get("total_expenditures"))
        if stated_c is None:
            stated_c = vmoney(last.get("total_contributions"))
        if stated_e is None:
            stated_e = vmoney(last.get("total_expenditures"))
        notes.append(f"multi-report bundle ({len(reps)} reports in one PDF; "
                     f"stated totals = bundle cover else last sub-report)")
        return dict(contrib_rows=crows, expend_rows=erows,
                    stated_contrib=stated_c, stated_expend=stated_e,
                    stated_begin=vmoney(cache.get("beginning_balance")),
                    stated_end=vmoney(cache.get("ending_balance")),
                    notes="; ".join(notes))
    crows, erows = _rows_from(cache, meta, vm)
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=vmoney(cache.get("total_contributions")),
                stated_expend=vmoney(cache.get("total_expenditures")),
                stated_begin=vmoney(cache.get("beginning_balance")),
                stated_end=vmoney(cache.get("ending_balance")),
                notes="; ".join(notes))


def empty_result(note):
    """An honest inventory-only result for a filing with no cache and no parseable text
    (acquired, not transcribed) — flows into filing_totals as an unknown-totals row."""
    return dict(contrib_rows=[], expend_rows=[], stated_contrib=None,
                stated_expend=None, stated_begin=None, stated_end=None, notes=note)


# ---------------------------------------------------------------- regime detection

def _effective(side, cache):
    stated = vmoney(cache.get(f"total_{side}"))
    if stated is not None:
        return stated, "stated"
    rows = cache.get(side) or []
    vals = [vmoney(r.get("amount")) for r in rows]
    vals = [v for v in vals if v is not None]
    if rows:
        return round(sum(vals), 2), "itemized"
    return None, "none"


def _row_multiset(cache, side):
    key_name = "name" if side == "contributions" else None
    ms = Counter()
    for r in cache.get(side) or []:
        nm = (r.get("name") or r.get("donor") or "") if key_name else \
             (r.get("recipient") or r.get("payee") or r.get("name") or "")
        ms[(vdate(r.get("date")), " ".join(str(nm).split()).lower(), vmoney(r.get("amount")))] += 1
    return ms


def detect_regimes(filings, verbose=True):
    """filings: list of dicts {candidate, election_year, filing_date, cache} (cache may be
    None), one per in-scope filing. Returns {(candidate, election_year): "cumulative" |
    "incremental"} using the 3-tier evidence in the module docstring. Prints decisions."""
    groups = {}
    for f in filings:
        groups.setdefault((f["candidate"], f["election_year"]), []).append(f)
    out = {}
    for key, fs in sorted(groups.items()):
        fs = sorted(fs, key=lambda f: f["filing_date"])
        cached = [f for f in fs if f["cache"]]
        if len(cached) < 2:
            out[key] = "incremental"
            if verbose and len(fs) > 1:
                print(f"  regime {key[0]} {key[1]}: incremental (default — "
                      f"<2 transcribed filings)")
            continue
        reason = None
        # 1. row-subset evidence
        subset_votes = []
        for a, b in zip(cached, cached[1:]):
            for side in ("contributions", "expenditures"):
                ma, mb = _row_multiset(a["cache"], side), _row_multiset(b["cache"], side)
                if sum(ma.values()) >= 2 and sum(mb.values()) >= sum(ma.values()):
                    subset_votes.append(not (ma - mb))   # True iff a ⊆ b
        if subset_votes and all(subset_votes):
            # POSITIVE evidence only: a failed subset may just be transcription
            # variance between chunk agents (date-format drift), so it never proves
            # incremental — that falls to the stated-sequence test below.
            reason = "row-subset (later filings contain earlier rows)"
            out[key] = "cumulative"
        # 2/3. restatement / stated-sequence evidence. A cumulative verdict needs a real
        # CHAIN: at least one side with >=2 usable values AND the LAST cached filing
        # usable on some side — otherwise a blank/untranscribable trailing scan would be
        # crowned "the cycle-to-date total" (the Bryant Brown 2025 hazard) and a
        # supersession pass would zero the candidate out. Insufficient evidence defaults
        # incremental (summing never destroys transcribed money).
        if reason is None:
            monotone, chain = True, False
            for side in ("contributions", "expenditures"):
                vals = [_effective(side, f["cache"])[0] for f in cached]
                vals = [v for v in vals if v is not None]
                if len(vals) >= 2:
                    chain = True
                if any(b < a - 1.0 for a, b in zip(vals, vals[1:])):
                    monotone = False
            last_usable = any(_effective(side, cached[-1]["cache"])[0] is not None
                              for side in ("contributions", "expenditures"))
            if monotone and chain and last_usable:
                out[key], reason = "cumulative", \
                    "stated/itemized totals non-decreasing (restatement chain)"
            elif not monotone:
                out[key], reason = "incremental", \
                    "totals decrease across chain (per-period)"
            else:
                out[key], reason = "incremental", \
                    "insufficient chain evidence (default — summing is safe)"
        if verbose:
            print(f"  regime {key[0]} {key[1]}: {out[key]} — {reason}")
    return out
