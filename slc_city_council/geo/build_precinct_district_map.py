#!/usr/bin/env python3
"""
Build precinct_to_district.csv — the lookup that powers address->district.

Source of truth is the election data: each SLC council-district contest lists the
precincts that voted in it, so the set of precincts in a contest == the precincts
in that district *for that election's boundaries*. Council districts are staggered
(odd 1/3/5/7 vs even 2/4/6), so for the CURRENT (post-2022-redistricting) map we
combine the two most recent generals: 2023 (even) + 2025 (odd).

Output columns: precinct, district, source_year
Run again with different --years to build a historical map.

Usage:
    python3 build_precinct_district_map.py                 # current map (2023+2025)
    python3 build_precinct_district_map.py --years 2013    # a historical snapshot
"""

import argparse
import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
# Re-pointed 2026-07-19: reads the COUNTY CANONICAL canvass directly (the folder's
# redundant per-year {year}_municipal_general.csv raw copies were deleted after the
# election pipeline re-point — see election_results/CLAUDE.md). Output proven
# byte-identical across the re-point. precinct='Cumulative' is the workbook's own
# zero-vote rollup label, never a precinct (county elections CLAUDE.md) — skipped.
CANONICAL = (BASE.parent.parent / "salt_lake_county" / "elections"
             / "slco_municipal_results_long.csv")
OUT = BASE / "precinct_to_district.csv"


def slc_council_district(contest):
    """Return the council district number for an SLC council contest, else None."""
    u = contest.strip().upper()
    if not (u.startswith("SALT LAKE CITY") or u.startswith("SLC ")):
        return None
    if "SCHOOL" in u or "MAYOR" in u or not ("COUNCIL" in u or "CNCL" in u):
        return None
    nums = re.findall(r"\d+", u)
    return nums[-1] if nums else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2023,2025",
                    help="comma-separated general-election years to combine (default current map)")
    args = ap.parse_args()
    years = [y.strip() for y in args.years.split(",")]

    by_year = {y: [] for y in years}
    with open(CANONICAL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("election_type", "").strip() == "municipal general"
                    and r.get("year", "").strip() in by_year):
                by_year[r.get("year", "").strip()].append(r)

    mapping = {}        # precinct -> (district, source_year)
    conflicts = []
    for y in years:
        if not by_year[y]:
            print(f"  (skipping {y}: no municipal-general rows in the county canonical)")
            continue
        for r in by_year[y]:
            d = slc_council_district(r.get("contest", ""))
            if not d:
                continue
            p = r["precinct"].strip()
            if p == "Cumulative":       # workbook rollup label, not a precinct
                continue
            if p in mapping and mapping[p][0] != d:
                conflicts.append((p, mapping[p][0], d))
            else:
                mapping.setdefault(p, (d, y))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year"])
        for p in sorted(mapping):
            w.writerow([p, mapping[p][0], mapping[p][1]])

    from collections import Counter
    per = Counter(d for d, _ in mapping.values())
    print(f"Wrote {OUT.name}: {len(mapping)} precincts across districts {dict(sorted(per.items()))}")
    if conflicts:
        print(f"WARNING: {len(conflicts)} precinct/district conflicts (precinct in 2+ districts):")
        for p, a, b in conflicts[:10]:
            print(f"  {p}: {a} vs {b}")


if __name__ == "__main__":
    main()
