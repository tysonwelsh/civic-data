#!/usr/bin/env python3
"""
Build precinct_to_district.csv — the lookup that powers address->district for
West Valley City's 4 council DISTRICTS (the 2 at-large seats represent the whole
city, so they have no precinct->district mapping).

Source of truth is the election data: each WVC council-DISTRICT contest lists the
precincts that voted in it, so the set of precincts in a contest == the precincts
in that district *for that election's boundaries*. WVC district seats are staggered
(Districts 1 & 3 in one odd cycle, Districts 2 & 4 in the next), so for the CURRENT
(post-2022-redistricting) map we combine the two most recent generals:
2023 (Districts 1 & 3) + 2025 (Districts 2 & 4).

The election data lives in the shared Salt Lake County archive
(~/Desktop/slco-election-archive/data/municipal_results_long.csv) because WVC
elections are administered by Salt Lake County. The election `precinct` column
(e.g. WVC003) equals the GIS `PrecinctID`, which is what makes the join work.

Output columns: precinct, district, source_year
Run again with different --years to build a historical map.

Usage:
    python3 build_precinct_district_map.py                 # current map (2023+2025)
    python3 build_precinct_district_map.py --years 2021,2025
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "precinct_to_district.csv"
# WVC results are filed under Salt Lake County; reuse the shared archive.
# NOTE: the slco-election-archive intentionally still lives at ~/Desktop/ (verified
# present 2026-07-02); update this path if that archive is ever relocated.
ELECTIONS = Path.home() / "Desktop" / "slco-election-archive" / "data" / "municipal_results_long.csv"


def wvc_council_district(contest):
    """Return the council DISTRICT number for a WVC council-district contest, else None.

    Matches only 'West Valley City Council District N' style contests; deliberately
    excludes Mayor, At-Large (city-wide, no precinct->district), and school races, and
    excludes neighboring cities (must start with WEST VALLEY).
    """
    u = contest.strip().upper()
    if not u.startswith("WEST VALLEY"):
        return None
    if not ("COUNCIL" in u or "CNCL" in u or "COUN" in u):
        return None
    if "MAYOR" in u or "SCHOOL" in u:
        return None
    # At-large / city-wide seats have no district number.
    if "AT-LARGE" in u or "AT LARGE" in u or "AT LRG" in u or "@ LRG" in u or "@ LG" in u:
        return None
    if "DIST" not in u and "DISTRICT" not in u:
        # Older labels like 'WEST VALLEY CITY COUNCIL #1' / 'COUN 1' are seat numbers,
        # not the current district map; skip them for the current map.
        return None
    nums = re.findall(r"\d+", u)
    return nums[-1] if nums else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2023,2025",
                    help="comma-separated general-election years to combine (default = current map)")
    ap.add_argument("--source", default=str(ELECTIONS),
                    help="path to the long municipal results CSV")
    args = ap.parse_args()
    years = {y.strip() for y in args.years.split(",")}
    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"Election source not found: {src}")

    mapping = {}        # precinct -> (district, source_year)
    conflicts = []
    with open(src, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("year") not in years:
                continue
            d = wvc_council_district(r.get("contest", ""))
            if not d:
                continue
            p = r["precinct"].strip()
            if not p:
                continue
            if p in mapping and mapping[p][0] != d:
                conflicts.append((p, mapping[p][0], d))
            else:
                mapping.setdefault(p, (d, r["year"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year"])
        for p in sorted(mapping):
            w.writerow([p, mapping[p][0], mapping[p][1]])

    per = Counter(d for d, _ in mapping.values())
    print(f"Wrote {OUT.name}: {len(mapping)} precincts across districts {dict(sorted(per.items()))}")
    if conflicts:
        print(f"WARNING: {len(conflicts)} precinct/district conflicts (precinct in 2+ districts):")
        for p, a, b in conflicts[:10]:
            print(f"  {p}: {a} vs {b}")


if __name__ == "__main__":
    main()
