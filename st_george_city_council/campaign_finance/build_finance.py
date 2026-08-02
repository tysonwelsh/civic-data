#!/usr/bin/env python3
"""build_finance.py — St. George driver for the structured campaign-finance layer.

St. George is the HARDEST campaign-finance city: the City Recorder posts each filing deadline as
ONE scanned multi-candidate COMPILATION PDF (all candidates' "Campaign Finance Report" forms
back-to-back), OCR'd to a single text sidecar. There is NO page-range column, so this driver first
runs a CANDIDATE SEGMENTER that splits every text file into per-candidate sections on the
"CAMPAIGN FINANCE REPORT" / "Full Name of Candidate" header boundaries, then aligns each section to
an index.csv row by fuzzy candidate-name match (greedy, order-independent — 2021 page order does
NOT follow index order). Unaligned sections AND unmatched index rows BOTH land in `segments.csv`
(the audit surface): a donor list attributed to the WRONG candidate is worse than a gap.

Each aligned section is then fed (sliced text, not the whole file) to the `stgeorge_formab` family
via the driver's `rows_override_fn`, which also injects a gated Claude-vision transcription when the
OCR section will not reconcile. All scanned -> OCR mode + currency-repair + date-sanity. A figure
that will not reconcile stays blank + needs_review + low, NEVER guessed.

DEDUP — INCREMENTAL (verified: Jimmie Hughes 2023 Aug $17,203 -> Dec $5,000; periods do NOT
restate cumulatively), so a candidate's cycle total is the SUM of the deadline reports. Each filing
deadline gets a clean `reporting_period` label (below); the two Aug-2023 packets share one label so
the known duplicate re-post (2023_financialcampaigndisclosures duplicates 8 non-advancer reports
from 20230829) is superseded, not double-counted. Read `cycle_totals.csv` for a candidate total;
never sum filing_totals yourself.

Regenerate, never hand-edit the CSVs. Corrections -> finance_overrides.csv / donor_aliases.csv.

    python3 build_finance.py            # segment + parse + (use cached vision) + write CSVs
    python3 stgeorge_vision_extract.py  # THEN, for still-unreconciled sections: gated vision
    python3 build_finance.py            # re-run to fold the vision cache in
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "campaign_finance" / "families"))

import driver          # noqa: E402
import vision_lib      # noqa: E402
import common          # noqa: E402
import stgeorge_formab as family  # noqa: E402
from common import ContribRow, ExpendRow, parse_date  # noqa: E402

VISION_DIR = HERE / "vision"
SEGMENTS_CSV = HERE / "segments.csv"

# clean per-deadline reporting-period label — each filing deadline is a DISTINCT period, so an
# incremental cycle total sums them (verified: the amounts differ across deadlines, never restate).
# NB the two Aug-2023 packets are NOT duplicates (the index CLAUDE.md note is inaccurate): the
# undated `2023_financialcampaigndisclosures` holds the non-advancers' SEPARATE post-primary CLOSING
# reports (e.g. Mackey $200 closing vs his $4,970 Aug pre-primary) — a distinct, smaller period that
# must be summed, not superseded. Each file therefore gets its own label.
_PERIOD = {
    "wb20210803_campaignfinancialreports": "2021 pre-primary (Aug 3)",
    "wb20210909_campaignfinancialreports": "2021 post-primary (Sep 9)",
    "wb20211026_campaignfinancialdisclosures": "2021 pre-general (Oct 26)",
    "wb20211202_campaignfinancialdisclosures": "2021 year-end (Dec 2)",
    "20230829_campaignfinancedisclosures": "2023 pre-primary (Aug 29)",
    "2023_financialcampaigndisclosures": "2023 post-primary closing",   # non-advancers' closing reports
    "20231024_october242023financialdisclosures": "2023 pre-general (Oct 24)",
    "20231114_financialdisclosures": "2023 post-general (Nov 14)",
    "20231221_campaignfinancedisclosures": "2023 year-end (Dec 21)",
    "20250805_campaign_finance_reports": "2025 pre-primary (Aug 5)",
    "20250911_campaign_finance_reports": "2025 post-primary (Sep 11)",
    "20251007_campaign_finance_disclosures": "2025 pre-general (Oct 7)",
    "20251028_campaign_finance_disclosures": "2025 pre-general (Oct 28)",
    "20251204_campaign_finance_disclosures": "2025 year-end (Dec 4)",
    # State-channel AMENDMENTS (DEBT fix 2026-08-01): the word "amended" in the label is
    # load-bearing — driver._base_period strips it, grouping each with the original period
    # it restates, so incremental dedup marks the original 'superseded by amendment'.
    "municipal20240401_larkin_amended": "2023 pre-primary (Aug 29) amended",
    "municipal20240401_kemp_amended": "2023 pre-general (Oct 24) amended",
}

_COVER = re.compile(r"CA\w*PA\w*GN\s+FINAN\w+\s+REPORT", re.I)
_NAME = re.compile(r"Full\s*Name of Candidate\b(.*)", re.I)
_PAGE = re.compile(r"=====\s*PAGE\s*(\d+)")
_DATA_HDR = re.compile(r"(CONTRIBUTION|EXPENDITURE)\s+REPORT", re.I)   # a real Form-A/B section header
_MERGE_GAP = 8          # a cover header + its Full-Name line sit within this many lines -> one anchor


def _did8(path, candidate):
    """Stable per-filing id (path repeats across candidates, so key on both)."""
    return hashlib.sha1(f"{path}#{candidate}".encode("utf-8")).hexdigest()[:8]


def _stem(path):
    return Path(path).stem


def _norm_name(s):
    """Alpha tokens (>=2 chars, so a middle initial 'B'/'L' is dropped) upper-cased, for matching."""
    return [t for t in re.findall(r"[A-Za-z]{2,}", (s or "").upper())
            if t not in ("MR", "MRS", "MS", "DR", "JR", "SR")]


def _name_sim(a, b):
    """0..1 similarity of two candidate names. Rewards exact first/last-token agreement and overall
    token/character overlap; conservative so garbled OCR names fall through to the segment report."""
    ta, tb = _norm_name(a), _norm_name(b)
    if not ta or not tb:
        return 0.0
    sa, sb = set(ta), set(tb)
    overlap = len(sa & sb) / max(len(sa), len(sb))
    seq = difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    first_eq = ta[0] == tb[0]
    last_eq = ta[-1] == tb[-1]
    return round(0.45 * overlap + 0.25 * seq + 0.15 * first_eq + 0.15 * last_eq, 4)


def _segment_file(stem, text):
    """Split one compilation sidecar into candidate sections. Return list of dicts with
    start_line/end_line (0-based, [start,end)), page_first/page_last (PDF page numbers), ocr_name."""
    lines = text.splitlines()
    n = len(lines)
    # line -> current PDF page number
    page_at, cur = [0] * n, 0
    for i, l in enumerate(lines):
        m = _PAGE.search(l)
        if m:
            cur = int(m.group(1))
        page_at[i] = cur
    # anchor lines = cover header OR Full-Name line; merge a header+name pair (<= _MERGE_GAP apart)
    raw_anchors = sorted(i for i, l in enumerate(lines) if _COVER.search(l) or _NAME.search(l))
    anchors = []
    for i in raw_anchors:
        if anchors and i - anchors[-1] <= _MERGE_GAP:
            continue
        anchors.append(i)
    segs = []
    for j, a in enumerate(anchors):
        end = anchors[j + 1] if j + 1 < len(anchors) else n
        # extract the OCR name from any Full-Name line inside [a, end)
        name = ""
        for k in range(a, min(end, a + _MERGE_GAP + 2)):
            m = _NAME.search(lines[k])
            if m:
                name = re.sub(r"[_:.\\/|]+", " ", m.group(1)).strip()
                name = re.sub(r"\s{2,}", " ", name)
                break
        has_data = any(_DATA_HDR.search(lines[k]) for k in range(a, end))
        segs.append(dict(start_line=a, end_line=end, ocr_name=name, has_data=has_data,
                         page_first=page_at[a] or 1, page_last=page_at[end - 1] or page_at[a] or 1))
    return segs


def _align(segs, idx_rows):
    """ORDER-INDEPENDENT name alignment (2021 page order != index order). Three tiers, each more
    tentative than the last, so a mis-segmented donor list is flagged rather than silently forced:
      1. confident greedy name match (sim >= THRESH) -> high/medium/low by score;
      2. weak greedy on the leftovers (best remaining sim > 0) -> 'elimination' (garbled OCR names
         like 'Leavits'->LEAVITT still carry a usable relative signal within the reduced set);
      3. positional pairing of any still-equal free leftovers (segments in page order vs index rows
         in file order) -> 'elimination'.
    A tiny bonus prefers a DATA-bearing segment over a duplicate cover-only page for the same name.
    Returns seg_idx -> (index_row, sim, confidence); unmatched on either side go to the report."""
    THRESH = 0.34
    pairs = []
    for si, s in enumerate(segs):
        bonus = 0.03 if s["has_data"] else 0.0
        for ii, ix in enumerate(idx_rows):
            pairs.append((_name_sim(s["ocr_name"], ix["candidate"]) + bonus, si, ii))
    pairs.sort(reverse=True)
    seg_take, idx_take, out = {}, set(), {}
    for sim, si, ii in pairs:                                            # tier 1
        if si in seg_take or ii in idx_take or sim < THRESH:
            continue
        seg_take[si] = ii
        idx_take.add(ii)
        raw = _name_sim(segs[si]["ocr_name"], idx_rows[ii]["candidate"])
        out[si] = (idx_rows[ii], raw, "high" if raw >= 0.72 else "medium" if raw >= 0.5 else "low")
    remaining = [(sim, si, ii) for sim, si, ii in pairs
                 if si not in seg_take and ii not in idx_take and sim > 0]
    for sim, si, ii in remaining:                                       # tier 2: weak name signal
        if si in seg_take or ii in idx_take:
            continue
        seg_take[si] = ii
        idx_take.add(ii)
        out[si] = (idx_rows[ii], _name_sim(segs[si]["ocr_name"], idx_rows[ii]["candidate"]),
                   "elimination")
    free_s = sorted(i for i in range(len(segs)) if i not in seg_take)
    free_i = [i for i in range(len(idx_rows)) if i not in idx_take]     # tier 3: positional
    if free_s and len(free_s) == len(free_i):
        for si, ii in zip(free_s, free_i):
            out[si] = (idx_rows[ii], _name_sim(segs[si]["ocr_name"], idx_rows[ii]["candidate"]),
                       "elimination")
            seg_take[si] = ii
            idx_take.add(ii)
    return out, seg_take, idx_take


# --------------------------------------------------------------------------- segmentation pass
def build_segments():
    """Segment every text file, align to index rows, WRITE segments.csv, return a lookup
    (path, candidate) -> segment dict (with text slice + confidence)."""
    index_rows = list(csv.DictReader(open(HERE / "index.csv", newline="", encoding="utf-8")))
    by_path = {}
    for r in index_rows:
        by_path.setdefault(r["path"], []).append(r)

    lookup = {}
    report = []   # rows for segments.csv
    for path, idx_rows in by_path.items():
        stem = _stem(path)
        txt = (HERE / "text" / f"{stem}.txt")
        if not txt.exists():
            for ix in idx_rows:
                report.append(dict(file=stem, status="MISSING-TEXT", ocr_name="",
                                   matched_candidate=ix["candidate"], election_year=ix["election_year"],
                                   sim="", confidence="", page_range="", start_line="", end_line="",
                                   document_id=_did8(path, ix["candidate"])))
            continue
        text = txt.read_text(encoding="utf-8", errors="replace")
        segs = _segment_file(stem, text)
        out, seg_take, idx_take = _align(segs, idx_rows)
        lines = text.splitlines()
        for si, s in enumerate(segs):
            pr = f"p{s['page_first']:02d}-p{s['page_last']:02d}"
            if si in out:
                ix, sim, conf = out[si]
                did = _did8(path, ix["candidate"])
                lookup[(path, ix["candidate"])] = dict(
                    start_line=s["start_line"], end_line=s["end_line"],
                    text="\n".join(lines[s["start_line"]:s["end_line"]]),
                    page_first=s["page_first"], page_last=s["page_last"],
                    confidence=conf, sim=sim, document_id=did)
                report.append(dict(file=stem, status="aligned", ocr_name=s["ocr_name"],
                                   matched_candidate=ix["candidate"], election_year=ix["election_year"],
                                   sim=sim, confidence=conf, page_range=pr,
                                   start_line=s["start_line"], end_line=s["end_line"], document_id=did))
            else:
                report.append(dict(file=stem, status="unaligned-section", ocr_name=s["ocr_name"],
                                   matched_candidate="", election_year="", sim="", confidence="",
                                   page_range=pr, start_line=s["start_line"], end_line=s["end_line"],
                                   document_id=""))
        for ii, ix in enumerate(idx_rows):
            if ii not in idx_take:
                report.append(dict(file=stem, status="unmatched-index-row", ocr_name="",
                                   matched_candidate=ix["candidate"], election_year=ix["election_year"],
                                   sim="", confidence="", page_range="", start_line="", end_line="",
                                   document_id=_did8(path, ix["candidate"])))

    cols = ["file", "status", "matched_candidate", "election_year", "ocr_name", "sim",
            "confidence", "page_range", "start_line", "end_line", "document_id"]
    with open(SEGMENTS_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in sorted(report, key=lambda x: (x["file"], x["start_line"] if x["start_line"] != "" else 1e9)):
            w.writerow(r)
    _print_seg_report(report)
    return lookup


def _print_seg_report(report):
    from collections import Counter
    st = Counter(r["status"] for r in report)
    print("=== SEGMENTER ===")
    print(f"aligned={st['aligned']}  unaligned-section={st['unaligned-section']}  "
          f"unmatched-index-row={st['unmatched-index-row']}  missing-text={st['MISSING-TEXT']}")
    conf = Counter(r["confidence"] for r in report if r["status"] == "aligned")
    print(f"alignment confidence: high={conf['high']} medium={conf['medium']} low={conf['low']} "
          f"elimination={conf['elimination']}")
    flagged = [r for r in report if r["status"] != "aligned" or r["confidence"] in ("low", "elimination")]
    if flagged:
        print("flagged sections/rows (review in segments.csv):")
        for r in sorted(flagged, key=lambda x: x["file"]):
            print(f"    {r['file']:42s} {r['status']:20s} {r['page_range']:11s} "
                  f"ocr='{r['ocr_name'][:24]}' -> {r['matched_candidate']} [{r['confidence']}]")


# --------------------------------------------------------------------------- per-filing meta / parse
_SEGMENTS = {}    # populated by main()


def _office(ix):
    o = (ix.get("office") or "").strip()
    return "Mayor" if o.lower().startswith("mayor") else ("Council" if o.lower().startswith("council") else o)


def _filing_type(ix):
    """St. George reports are ALL per-period incremental (verified: a year-end 'summary' report is
    the CLOSING period's activity, e.g. Hughes Dec $5,000, NOT a cumulative restatement). So the
    index's `summary` label is mapped to `closing` here — deliberately OUTSIDE cycle_totals.py's
    SUMMARY_TYPES so the canonical cycle rollup SUMS every deadline (the correct incremental total)
    instead of treating the year-end as cumulative-to-date and dropping the interims."""
    return "closing" if (ix.get("filing_type", "") or "").strip().lower() == "summary" else "interim"


def _meta(ix):
    seg = _SEGMENTS.get((ix["path"], ix["candidate"]))
    return dict(
        candidate=ix["candidate"], office=_office(ix), seat="",     # St. George is all at-large
        election_year=ix["election_year"], filing_date=ix.get("date", ""),
        filing_type=_filing_type(ix), source_filing=ix["path"],
        document_id=(seg["document_id"] if seg else _did8(ix["path"], ix["candidate"])),
        reporting_period=_PERIOD.get(_stem(ix["path"]), ix.get("reporting_period", "")),
        line_base=(seg["start_line"] if seg else 0))


def _vmoney(x):
    if x in (None, "", "null"):
        return None
    return common.parse_money("$" + re.sub(r"[^\d.,-]", "", str(x)))


def _rows_override(ix, meta):
    """driver hook: (1) a cached Claude-vision transcription wins; else (2) slice this candidate's
    aligned segment and parse it with the stgeorge_formab family; unaligned index rows -> empty rows
    + honest note. The result flows through the SAME normalization + reconciliation as any family."""
    seg = _SEGMENTS.get((ix["path"], ix["candidate"]))
    # cache filename = the repo-standard key sha1(path + "|" + candidate)[:8]
    # (2026-07-19 migration from the legacy "#" separator; St. George PDFs are
    # multi-candidate compilations, so the candidate discriminator is required).
    # document_id keeps the legacy sha1(path#candidate) id for CSV/provenance stability.
    cache = VISION_DIR / f"{vision_lib.cache_key(ix['path'], ix['candidate'])}.json"
    if cache.exists():
        return _vision_result(cache, meta)
    if seg is None:
        return dict(contrib_rows=[], expend_rows=[], stated_contrib=None, stated_expend=None,
                    stated_begin=None, stated_end=None,
                    notes="no segment aligned (see segments.csv) — filing not machine-extracted")
    res = family.parse(seg["text"], meta)
    note = res.get("notes", "")
    if seg["confidence"] in ("low", "elimination"):
        note = (note + "; " if note else "") + f"segment match={seg['confidence']} (verify vs raw)"
    res["notes"] = note
    return res


def _vision_result(cache, meta):
    d = json.loads(cache.read_text())
    vm = meta["extract_method"].split("/")[0] + "/vision"

    def _date(s):
        return parse_date(str(s)) or "" if s not in (None, "", "null") else ""

    crows = []
    for i, r in enumerate(d.get("contributions", [])):
        amt = _vmoney(r.get("amount"))
        crows.append(ContribRow(
            candidate=meta["candidate"], office=meta["office"], seat="",
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            donor_raw=(r.get("name") or "").strip(), amount=common.money_str(amt),
            in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if (amt is not None and (r.get("name") or "").strip()) else "1"))
    erows = []
    for i, r in enumerate(d.get("expenditures", [])):
        amt = _vmoney(r.get("amount"))
        erows.append(ExpendRow(
            candidate=meta["candidate"], office=meta["office"], seat="",
            election_year=meta["election_year"], filing_date=meta["filing_date"],
            reporting_period=meta.get("reporting_period", ""), date=_date(r.get("date")),
            vendor_raw=(r.get("recipient") or "").strip(), purpose=(r.get("purpose") or "").strip(),
            amount=common.money_str(amt), in_kind=str(bool(r.get("in_kind"))), is_incremental="True",
            source_filing=meta["source_filing"], document_id=meta["document_id"],
            line_no=f"v{i + 1}", extract_method=vm,
            needs_review="0" if amt is not None else "1"))
    return dict(contrib_rows=crows, expend_rows=erows,
                stated_contrib=_vmoney(d.get("total_contributions")),
                stated_expend=_vmoney(d.get("total_expenditures")),
                stated_begin=_vmoney(d.get("previous_balance")),
                stated_end=_vmoney(d.get("ending_balance")),
                notes=d.get("transcribed_by", "vision-transcribed(claude-sonnet-5)"))


def main():
    global _SEGMENTS
    _SEGMENTS = build_segments()
    print()
    driver.run(
        here=HERE, family_id="stgeorge_formab",
        meta_fn=_meta, sidecar_fn=lambda ix: HERE / "text" / f"{_stem(ix['path'])}.txt",
        is_scanned_fn=lambda ix: True,           # every St. George filing is scanned
        reconcile_cash_only=False,               # itemized total INCLUDES in-kind
        dedup_mode="incremental",                # verified per-period; cycle total = sum of deadlines
        amend_fn=lambda ix: ix.get("filing_type") == "amended",   # 2 state-channel 2023 amendments (2026-08-01)
        rows_override_fn=_rows_override)


if __name__ == "__main__":
    main()
