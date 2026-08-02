#!/usr/bin/env python3
"""build_index.py — regenerate index.csv for weber_county/campaign_finance.

Inputs (all in this directory; none are hand-edited outputs):
  raw/<channel>/_fetch_log.jsonl   provenance written by fetch_cf.py (url, sha256, bytes,
                                   retrieved_utc, and the PORTAL LABEL in `note`)
  text_extraction.csv              measured format/method per document (backfill_text.py)
  filing_attribution.csv           CURATED — candidate / office / date read from each
                                   filing's OWN printed form fields (OCR or a vision read
                                   of the rendered page), with the page range inside a
                                   consolidated PDF. This is the only place attribution
                                   lives; portal labels never set it.
  batch/portal_manifest.json       portal-published labels, kept for comparison only

Output: index.csv — ONE ROW PER FILING (page-ranged inside a compilation), plus one
document-grain row for any retained document that has no attributed filings.

Rebuild: python3 build_index.py
"""
from __future__ import annotations

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

CHANNEL_LABEL = {
    "archives": "weberelections.gov consolidated cycle archive",
    "y2026": "weberelections.gov 2026 per-candidate report",
    "wayback": "weberelections.com (predecessor host) via Internet Archive",
    "state": "disclosures.utah.gov / municipal.utah.gov (Lt. Governor municipal tree)",
}

FIELDS = [
    "date", "title", "source_url", "retrieved_date", "format", "extraction_method",
    "candidate", "candidate_key", "matched_election_candidate", "join_confidence",
    "office_stated", "office_scope", "election_cycle",
    "filing_grain", "page_start", "page_end", "pages_total",
    "channel", "portal_label", "path", "text_path", "document_id",
    "sha256", "bytes", "read_method", "needs_review", "notes",
    # TRAILING DERIVED ALIAS (2026-08-02): the shared campaign-finance contract
    # (scripts/campaign_finance/SCHEMA.md, validate_finance.py) keys itemized rows on an
    # index `election_year`; this module's own column is `election_cycle` (the even-year
    # cycle, with a January year-end report assigned to the PRIOR even year). The alias
    # carries the identical value so the two vocabularies cannot drift — `election_cycle`
    # remains the authoritative name here and is what the module's docs describe.
    "election_year",
]


def cand_key(name: str) -> str:
    """Deterministic first+last join key. Verbatim `candidate` is never overwritten."""
    import re
    n = re.sub(r'"[^"]*"', " ", name)                       # drop "Jim" style nicknames
    n = n.split(" - ")[0]                                   # drop " - Committee to Elect X"
    comma = "," in n
    n = re.sub(r"[^A-Za-z ,]", " ", n).upper()
    if comma:                       # election canvasses print "Harvey, Jim REP"
        last, _, first = n.partition(",")
        n = f"{first} {last}"
    n = n.replace(",", " ").split()
    # party markers and suffixes are not part of the person
    n = [t for t in n if t not in ("JR", "SR", "II", "III", "IV",
                                   "REP", "DEM", "UNA", "IND", "LIB", "CON", "NP", "UUP")]
    if len(n) < 2:
        return " ".join(n)
    return f"{n[0]} {n[-1]}"


def load_elections() -> dict:
    """candidate_key -> {year: name-as-published} from the sibling elections module
    (county contests only). Read-only; this module never writes there."""
    path = os.path.join(HERE, "..", "elections", "election_results_by_contest.csv")
    out: dict = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nm = r.get("candidate", "")
            if not nm or nm.lower().startswith("write-in"):
                continue
            k = cand_key(nm)
            if k:
                out.setdefault(k, {}).setdefault(r.get("year", ""), nm)
    return out


def load_fetch_logs() -> dict:
    out = {}
    raw = os.path.join(HERE, "raw")
    for ch in sorted(os.listdir(raw)):
        log = os.path.join(raw, ch, "_fetch_log.jsonl")
        if not os.path.exists(log):
            continue
        with open(log, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if not r.get("sha256"):
                    continue          # a failed attempt; the gap is logged, not indexed
                out[f"raw/{ch}/{r['out']}"] = r
    return out


def cycle_of(path: str, date: str) -> str:
    base = os.path.basename(path)
    for token in (base[:4], base.split("_")[0]):
        if token.isdigit() and len(token) == 4:
            return token
    if base.startswith("st2010"):
        return "2010"
    if base.startswith("st2012pri"):
        return "2012"
    if base.startswith("st2022"):
        return "2022"
    # wayback per-candidate: the cycle is the FILING's own year, and a January
    # year-end report belongs to the PRIOR even-year cycle.
    if date:
        y, m = int(date[:4]), int(date[5:7])
        return str(y - 1) if (y % 2 == 1 and m <= 3) else str(y)
    return ""


def main() -> int:
    fetch = load_fetch_logs()
    with open(os.path.join(HERE, "text_extraction.csv"), encoding="utf-8") as f:
        tx = {r["path"]: r for r in csv.DictReader(f)}
    with open(os.path.join(HERE, "filing_attribution.csv"), encoding="utf-8") as f:
        att = list(csv.DictReader(f))
    elect = load_elections()

    by_doc: dict[str, list] = {}
    for r in att:
        by_doc.setdefault(r["path"], []).append(r)

    rows = []
    for path in sorted(fetch):
        fr = fetch[path]
        ch = path.split("/")[1]
        t = tx.get(path, {})
        filings = sorted(by_doc.get(path, []), key=lambda r: int(r["page_start"]))
        common = dict(
            source_url=fr["url"],
            retrieved_date=fr["retrieved_utc"][:10],
            format=t.get("format", ""),
            extraction_method=t.get("method", ""),
            channel=CHANNEL_LABEL.get(ch, ch),
            portal_label=fr.get("note", ""),
            path=path,
            text_path=t.get("text_path", ""),
            sha256=fr["sha256"],
            bytes=fr["bytes"],
            pages_total=t.get("pages", ""),
        )
        if not filings:
            rows.append(dict(
                common, date="", title=f"{os.path.basename(path)} (document grain — "
                "filings not separately attributed)",
                candidate="", candidate_key="", matched_election_candidate="",
                join_confidence="", office_stated="", office_scope="", election_cycle="",
                filing_grain="document", page_start="", page_end=common["pages_total"],
                document_id=os.path.basename(path)[:-4], read_method="", needs_review="1",
                notes="no per-filing attribution rows exist for this document",
            ))
            continue
        grain = "filing-in-compilation" if len(filings) > 1 else "filing"
        for f_ in filings:
            cyc = cycle_of(path, f_["filing_date_stated"])
            cand = f_["candidate_stated"]
            off = f_["office_stated"]
            nr = "1" if (not cand or not off or f_["office_scope"] == "unclear"
                         or not f_["filing_date_stated"]) else "0"
            title = (f"{cand or '(candidate not read)'} — Weber County campaign financial "
                     f"report {cyc}" + (f" ({off})" if off else ""))
            key = cand_key(cand)
            hits = elect.get(key, {})
            if cyc in hits:
                matched, conf = hits[cyc], "exact"      # same person, same cycle year
            elif hits:
                matched, conf = hits[sorted(hits)[-1]], "person-only"   # other cycle
            else:
                matched, conf = "", "none"
            rows.append(dict(
                common, date=f_["filing_date_stated"], title=title,
                candidate=cand, candidate_key=key, matched_election_candidate=matched,
                join_confidence=conf,
                office_stated=off, office_scope=f_["office_scope"],
                election_cycle=cyc, filing_grain=grain,
                page_start=f_["page_start"], page_end=f_["page_end"],
                document_id=f"{os.path.basename(path)[:-4]}#p{f_['page_start']}"
                            if grain == "filing-in-compilation"
                            else os.path.basename(path)[:-4],
                read_method=f_["read_method"], needs_review=nr, notes=f_["notes"],
            ))

    for r in rows:
        r["election_year"] = r["election_cycle"]      # derived alias, never independent
    rows.sort(key=lambda r: (r["election_cycle"], r["path"],
                             int(r["page_start"] or 0)))
    with open(os.path.join(HERE, "index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"index.csv: {len(rows)} rows over {len(fetch)} retained documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
