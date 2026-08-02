#!/usr/bin/env python3
"""vision_coverage.py — print the CURRENT coverage of the vision stated-totals tranche.

Read-only. Run it after adding caches so the counts quoted in CLAUDE.md / AVAILABILITY.md can
be refreshed from the files rather than remembered (the repo rule: measured coverage, not
recalled coverage).

    python3 vision_coverage.py
"""
import csv
import glob
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STATED = ("total_contributions", "total_expenditures", "beginning_balance", "ending_balance")


def main():
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        idx = list(csv.DictReader(fh))
    era_of = {}
    for r in idx:
        if r["source"] == "clerk_legacy":
            era_of[r["path"]] = "clerk_legacy"
        elif r["source"] == "easyvote" and r["election_year"] == "2022":
            era_of[r["path"]] = "easyvote_2022"
    totals = Counter(era_of.values())

    caches = {}
    for f in glob.glob(os.path.join(HERE, "vision", "*.json")):
        d = json.load(open(f))
        caches[d["_meta"]["index_path"]] = d

    done = Counter()
    nosum = Counter()
    val = blank = illegible = 0
    conf = Counter()
    for p, d in caches.items():
        era = d["_meta"].get("era") or era_of.get(p, "?")
        if d["_meta"].get("summary_page_found"):
            done[era] += 1
        else:
            nosum[era] += 1
        for f in STATED:
            v = d.get(f)
            if v is None:
                illegible += 1
            elif v == "":
                blank += 1
            else:
                val += 1
        for k, v in (d.get("confidence") or {}).items():
            conf[v] += 1

    print(f"{'era':<16} {'filings':>8} {'transcribed':>12} {'no-summary':>11} {'remaining':>10}")
    for era in ("clerk_legacy", "easyvote_2022"):
        t, dn, ns = totals[era], done[era], nosum[era]
        print(f"{era:<16} {t:>8} {dn:>12} {ns:>11} {t - dn - ns:>10}")
    T, D, N = sum(totals.values()), sum(done.values()), sum(nosum.values())
    print(f"{'TOTAL':<16} {T:>8} {D:>12} {N:>11} {T - D - N:>10}")
    print(f"\ncaches: {len(caches)}   stated fields: value={val} blank-on-form={blank} "
          f"ILLEGIBLE/absent={illegible}")
    print("per-field transcriber confidence:", dict(conf))

    ftp = os.path.join(HERE, "filing_totals.csv")
    if os.path.exists(ftp):
        with open(ftp, newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if "VISION-TRANSCRIBED" in r["notes"]]
        print(f"\nfiling_totals tranche rows: {len(rows)}")
        print("  filing-level confidence:", dict(Counter(r["extraction_confidence"] for r in rows)))
        print("  filing_type:", dict(Counter(r["filing_type"] for r in rows)))
        c = sum(float(r["stated_total_contributions"]) for r in rows if r["stated_total_contributions"])
        e = sum(float(r["stated_total_expenditures"]) for r in rows if r["stated_total_expenditures"])
        print(f"  stated period figures observed (NEVER a cycle total — filings overlap): "
              f"${c:,.2f} contributions / ${e:,.2f} expenditures")


if __name__ == "__main__":
    main()
