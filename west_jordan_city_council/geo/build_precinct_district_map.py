#!/usr/bin/env python3
"""
Build precinct_to_district.csv — the lookup that powers address->district for
West Jordan's 4 council DISTRICTS (the 3 at-large seats + Mayor represent the
whole city, so they have no precinct->district mapping).

Two sources of truth, reconciled here:

1. ELECTION DATA (primary, SLC-matching method).  Each West Jordan council-
   DISTRICT contest lists the precincts that voted in it, so the set of precincts
   in a contest == the precincts in that district *for that election's boundaries*.
   Unlike West Valley, West Jordan runs ALL FOUR district seats in the SAME odd-year
   cycle, so one general year gives the full map.  The 2023 general is the CURRENT
   (post-2022-redistricting) map; 2019 is the pre-redistricting map (28 of 68 shared
   precincts were reassigned between the two -- see --years to rebuild a historical
   map).  The election `precinct` column (e.g. WJD050) equals the GIS `PrecinctID`,
   which is what makes the join work.  West Jordan elections are administered by Salt
   Lake County, but the cleaned WJ-only results live in this repo's election_results/.

2. CITY GIS DISTRICT POLYGONS (authoritative cross-check).  West Jordan publishes a
   clean 4-district FeatureServer (Council_Districts, city ArcGIS org owner
   `patrick.london`).  Saved here as council_districts.geojson.  With --from-gis the
   builder assigns each precinct polygon to the district polygon it most overlaps,
   which fills in precincts that had no district-race rows (e.g. mail precincts) and
   confirms the election-derived assignments.

Output columns: precinct, district, source_year
Run again with different --years to build a historical map.

Usage:
    python3 build_precinct_district_map.py                  # current map from 2023 election
    python3 build_precinct_district_map.py --years 2019     # pre-redistricting map
    python3 build_precinct_district_map.py --from-gis       # assign via city district polygons
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "precinct_to_district.csv"
# Cleaned West-Jordan-only precinct results (county-run elections, filtered to WJ).
ELECTIONS = BASE.parent / "election_results" / "west_jordan_results_by_precinct.csv"
PRECINCTS_GEOJSON = BASE / "precincts.geojson"
DISTRICTS_GEOJSON = BASE / "council_districts.geojson"


def wj_council_district(row):
    """Return the council DISTRICT number ('1'-'4') for a WJ council-district row, else None.

    The cleaned WJ results carry explicit office/district columns, so this is exact:
    keep office == 'Council' with district in 1-4. Deliberately excludes Mayor and
    At-Large (city-wide, no precinct->district). Falls back to parsing the contest
    string if the structured columns are absent.
    """
    office = (row.get("office") or "").strip().lower()
    district = (row.get("district") or "").strip()
    if office == "council" and district in {"1", "2", "3", "4"}:
        return district
    # Fallback: parse the contest text.
    contest = (row.get("contest") or "").upper()
    if not contest.startswith("WEST JORDAN"):
        return None
    if "COUNCIL" not in contest:
        return None
    if "MAYOR" in contest or "AT-LARGE" in contest or "AT LARGE" in contest:
        return None
    m = re.search(r"DISTRICT\s+(\d)", contest)
    return m.group(1) if m and m.group(1) in {"1", "2", "3", "4"} else None


def build_from_elections(years):
    mapping = {}        # precinct -> (district, source_year)
    conflicts = []
    if not ELECTIONS.exists():
        raise SystemExit(f"Election source not found: {ELECTIONS}")
    with open(ELECTIONS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("year") or "").strip() not in years:
                continue
            d = wj_council_district(r)
            if not d:
                continue
            p = (r.get("precinct") or "").strip()
            if not p:
                continue
            if p in mapping and mapping[p][0] != d:
                conflicts.append((p, mapping[p][0], d))
            else:
                mapping.setdefault(p, (d, r["year"]))
    return mapping, conflicts


def build_from_gis():
    """Assign each precinct polygon to the city council-district polygon it most overlaps."""
    import geopandas as gpd
    prec = gpd.read_file(PRECINCTS_GEOJSON).to_crs(26912)   # meters for overlap area
    dist = gpd.read_file(DISTRICTS_GEOJSON).to_crs(26912)
    mapping = {}
    for _, p in prec.iterrows():
        best_d, best_area = None, 0.0
        for _, d in dist.iterrows():
            try:
                inter = p.geometry.intersection(d.geometry).area
            except Exception:
                inter = 0.0
            if inter > best_area:
                best_area, best_d = inter, str(d["DISTRICTID"])
        if best_d and best_area > 0:
            mapping[str(p["PrecinctID"])] = (best_d, "gis")
    return mapping, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2023",
                    help="comma-separated general-election year(s) (default 2023 = current map; 2019 = pre-redistricting)")
    ap.add_argument("--from-gis", action="store_true",
                    help="assign precincts by overlap with the city Council_Districts polygons instead of election data")
    args = ap.parse_args()

    if args.from_gis:
        mapping, conflicts = build_from_gis()
        label = "city GIS polygon overlap"
    else:
        years = {y.strip() for y in args.years.split(",")}
        mapping, conflicts = build_from_elections(years)
        label = f"election years {sorted(years)}"

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year"])
        for p in sorted(mapping):
            w.writerow([p, mapping[p][0], mapping[p][1]])

    per = Counter(d for d, _ in mapping.values())
    print(f"Wrote {OUT.name} ({label}): {len(mapping)} precincts across districts {dict(sorted(per.items()))}")
    if conflicts:
        print(f"WARNING: {len(conflicts)} precinct/district conflicts (precinct in 2+ districts):")
        for p, a, b in conflicts[:10]:
            print(f"  {p}: {a} vs {b}")


if __name__ == "__main__":
    main()
