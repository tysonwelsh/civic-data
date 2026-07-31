#!/usr/bin/env python3
"""
Build Murray City's precinct_to_district.csv from Salt Lake County SOVC precinct rows,
and cross-check it against the OFFICIAL Murray council-district polygons (districts.geojson).

Murray HAS its own authoritative council-district GIS layer (Murray City ArcGIS org ->
"Murray City Council Districts", saved as districts.geojson). So unlike Taylorsville, the
district polygons are NOT precinct-derived. This script only builds the precinct->district
join table (a lookup aid for by-precinct election data) and verifies it agrees with the
official polygons.

precinct_to_district.csv is DERIVED from the district-contest precinct rows in the shared
Salt Lake County election archive: each "MURRAY CITY COUNCIL DISTRICT N" contest lists
exactly the precincts that voted in it, so contest-precincts == district-precincts for that
election's boundaries.

VINTAGE -- CURRENT (post-2020-census redistricting, boundaries approved 2022-01-04). Murray's
5 district seats are staggered across two odd-year cycles, so the current map is the union of
the two most recent generals under the redistricted lines:
    2023 general -> Districts 1, 3, 5   (D1/D3/D5 cycle: 2023/2027)
    2025 general -> Districts 2, 4      (D2/D4/Mayor cycle: 2021/2025/2029)
The 2025 "DISTRICT 3 (2 YEAR TERM)" special is EXCLUDED (D3 already taken from 2023; the two
sets are the identical 14 precincts, a built-in consistency check).

Usage:
    python3 build_precinct_district_map.py            # current map (2023 D1/3/5 + 2025 D2/4)
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

import geopandas as gpd

BASE = Path(__file__).resolve().parent
PRECINCTS = BASE / "precincts.geojson"
DISTRICTS = BASE / "districts.geojson"
OUT_CSV = BASE / "precinct_to_district.csv"
ELECTIONS = (Path(__file__).resolve().parents[2]
             / "salt_lake_county" / "elections" / "slco_municipal_results_long.csv")


def murray_council_district(contest):
    """District number (str) for a Murray council-DISTRICT contest, else None.

    Requires an explicit DISTRICT number. Excludes Mayor and the 2-YEAR-TERM special
    (handled by year selection, but guarded here too).
    """
    u = contest.strip().upper()
    if "MURRAY" not in u:
        return None
    if not ("COUNCIL" in u or "CNCL" in u):
        return None
    if "MAYOR" in u:
        return None
    if "DIST" not in u:  # matches DIST and DISTRICT; older "COUNCIL 1" seat labels are skipped
        return None
    if "2 YEAR" in u or "2YEAR" in u or "SPECIAL" in u:
        return None
    nums = re.findall(r"\d+", u)
    return nums[-1] if nums else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2023,2025",
                    help="comma-separated general years to combine (default = current map)")
    ap.add_argument("--source", default=str(ELECTIONS))
    args = ap.parse_args()
    years = {y.strip() for y in args.years.split(",")}
    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"Election source not found: {src}")

    mapping = {}       # precinct -> (district, source_year)
    conflicts = []
    with open(src, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("year") not in years:
                continue
            d = murray_council_district(r.get("contest", ""))
            if not d:
                continue
            p = (r.get("precinct") or "").strip()
            if not p:
                continue
            if p in mapping and mapping[p][0] != d:
                conflicts.append((p, mapping[p][0], d))
            else:
                mapping.setdefault(p, (d, r["year"]))

    # ---- Cross-check against the OFFICIAL district polygons (centroid-in-district) ----
    prec = gpd.read_file(PRECINCTS).to_crs("EPSG:4326")
    dist = gpd.read_file(DISTRICTS).to_crs("EPSG:4326")
    reps = prec.copy()
    reps["geometry"] = reps.geometry.representative_point()
    joined = gpd.sjoin(reps, dist[["District", "geometry"]], how="left", predicate="within")
    centroid_dist = dict(zip(joined["PrecinctID"], joined["District"].astype("string")))

    disagree = []
    for p, (d, _) in sorted(mapping.items()):
        cd = centroid_dist.get(p)
        if cd is not None and str(cd) != str(d):
            disagree.append((p, d, cd))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year", "method",
                    "official_centroid_district", "agrees"])
        for p in sorted(mapping):
            d, yr = mapping[p]
            cd = centroid_dist.get(p)
            cds = "" if cd is None else str(cd)
            agrees = "no_geometry" if cd is None else ("yes" if str(cd) == str(d) else "NO")
            w.writerow([p, d, yr, "district_contest_precinct_rows", cds, agrees])

    per = Counter(d for d, _ in mapping.values())
    print(f"Wrote {OUT_CSV.name}: {len(mapping)} precincts across districts {dict(sorted(per.items()))}")
    no_geom = [p for p in mapping if centroid_dist.get(p) is None]
    if no_geom:
        print(f"  {len(no_geom)} election precinct(s) with NO UGRC geometry: {sorted(no_geom)}")
    if disagree:
        print(f"  WARNING: {len(disagree)} election-vs-official disagreements:")
        for p, d, cd in disagree:
            print(f"    {p}: election D{d} vs official-centroid D{cd}")
    else:
        print("  election-derived map AGREES with official polygons on every precinct that has geometry")
    if conflicts:
        print(f"  WARNING: {len(conflicts)} precinct/district conflicts in election data:")
        for p, a, b in conflicts:
            print(f"    {p}: {a} vs {b}")


if __name__ == "__main__":
    main()
