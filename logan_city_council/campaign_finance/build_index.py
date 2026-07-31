#!/usr/bin/env python3
"""Regenerate index.csv for Logan campaign-finance disclosures.

Reads batch/manifest.json (one entry per retrieved filing) + the files present on
disk, joins each filer to election_results/logan_results_by_candidate.csv by
normalized (name, year), and writes index.csv. Idempotent. Additive-only: never
touches election_results/ or any other dataset.

Usage:  python3 build_index.py
"""
import csv, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.dirname(HERE)
RETRIEVED = "2026-07-05"

# SCHEMA_SPEC §9 contract header, extras after
COLS = ["date", "candidate", "office", "election_year", "filing_type",
        "reporting_period", "title", "source_url", "retrieved_date", "format",
        "extraction_method", "path", "amended", "matched_election_candidate",
        "join_confidence"]


def norm(name):
    """UPPER, drop punctuation, drop lone middle initials and suffixes -> comparable key."""
    n = name.upper().strip()
    n = re.sub(r"\(NP\)", "", n)
    n = re.sub(r"[.,]", " ", n)
    n = re.sub(r"\b(JR|SR|II|III|IV)\b", "", n)
    toks = [t for t in n.split() if len(t) > 1]  # drop single-letter middle initials
    return " ".join(toks)


def firstlast(name):
    toks = norm(name).split()
    return (toks[0], toks[-1]) if len(toks) >= 2 else tuple(toks)


def load_election():
    path = os.path.join(CITY, "election_results", "logan_results_by_candidate.csv")
    by_year = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            by_year.setdefault(int(r["year"]), {})[norm(r["candidate"])] = r["candidate"]
    return by_year


def join(cand, year, elec):
    pool = elec.get(int(year), {})
    k = norm(cand)
    if k in pool:
        return pool[k], "exact"
    fl = firstlast(cand)
    for nk, orig in pool.items():
        t = nk.split()
        if len(t) >= 2 and (t[0], t[-1]) == fl:
            return orig, "firstlast"
    return "", "none"


def main():
    manifest = json.load(open(os.path.join(HERE, "batch", "manifest.json")))
    elec = load_election()
    rows = []
    for m in manifest:
        if not os.path.exists(os.path.join(HERE, m["path"])):
            continue  # skip anything whose raw file didn't download
        mc, conf = join(m["candidate"], m["election_year"], elec)
        rows.append({
            "date": m["date"], "candidate": m["candidate"], "office": m["office"],
            "election_year": m["election_year"], "filing_type": m["filing_type"],
            "title": m["title"], "source_url": m["source_url"], "retrieved_date": RETRIEVED,
            "format": m["format"], "extraction_method": m["extraction_method"],
            "path": m["path"], "reporting_period": m["report_period"], "amended": m["amended"],
            "matched_election_candidate": mc, "join_confidence": conf,
        })
    rows.sort(key=lambda x: (x["election_year"], x["date"], x["candidate"]))
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    matched = sum(1 for r in rows if r["join_confidence"] != "none")
    print(f"index.csv: {len(rows)} filings; {matched}/{len(rows)} joined to election_results")
    # per (year,candidate) join rate
    pairs = {(r["election_year"], r["candidate"]) for r in rows}
    pmatch = {(r["election_year"], r["candidate"]) for r in rows if r["join_confidence"] != "none"}
    print(f"distinct (year,candidate): {len(pmatch)}/{len(pairs)} matched")


if __name__ == "__main__":
    main()
