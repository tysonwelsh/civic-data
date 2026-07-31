#!/usr/bin/env python3
"""
Build Taylorsville City's geo layer: precinct_to_district.csv + council_districts.geojson.

Taylorsville has NO dedicated council-district GIS FeatureServer (recon.md §6). So the
5 district polygons are DERIVED from Salt Lake County precincts:

  1. precincts.geojson = UGRC VistaBallotAreas (CountyID=18) filtered to the 44 TAY
     precincts, EPSG:4326.
  2. precinct_to_district.csv = precinct -> district (1-5), taken from the district-
     contest precinct rows in the shared SL County election archive. Each council-
     district contest lists exactly the precincts that voted in it, so
     contest-precincts == district-precincts for that election's boundaries.
  3. council_districts.geojson = precincts dissolved (unioned) by district.

VINTAGE — CURRENT (post-2020-census redistricting) map. Taylorsville's district seats
are staggered across two odd-year cycles, so the current map is the union of the two most
recent generals under the redistricted lines:
    2023 general -> Districts 1, 2, 3   (contest label 'CITY OF TAYLORSVILLE COUNCIL DISTRICT N')
    2025 general -> Districts 4, 5       (contest label 'TAYLORSVILLE CITY COUNCIL DISTRICT N')
Together they cover all 44 TAY precincts with no overlap. (The 2021 D3/D4/D5 rows use the
PRE-redistricting lines — e.g. 2021 D3 = TAY035,037-044 vs 2023 D3 = TAY023-025,029,032-036,040
— and are intentionally NOT used for the current map. Run with --years 2017,2021 for the
prior-vintage map.)

Election data lives in the shared Salt Lake County archive because Taylorsville elections
are county-run. The election `precinct` column (e.g. TAY041) equals the UGRC `PrecinctID`,
which makes the join exact.

Usage:
    python3 build_precinct_district_map.py                 # current map (2023 D1-3 + 2025 D4-5)
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd

BASE = Path(__file__).resolve().parent
PRECINCTS = BASE / "precincts.geojson"
OUT_CSV = BASE / "precinct_to_district.csv"
OUT_DISTRICTS = BASE / "council_districts.geojson"
# Taylorsville results are filed under Salt Lake County; reuse the shared archive.
ELECTIONS = Path.home() / "Desktop" / "slco-election-archive" / "data" / "municipal_results_long.csv"


def tay_council_district(contest):
    """District number (as str) for a Taylorsville council-DISTRICT contest, else None.

    Excludes Mayor, the Taylorsville-Bennion Improvement District (a separate special
    district), and any non-Taylorsville contest. Requires an explicit DISTRICT number.
    """
    u = contest.strip().upper()
    if "TAYLORSVILLE" not in u:
        return None
    if "BENNION" in u or "IMPROVE" in u or "TRUSTEE" in u or "BOARD" in u or "DIVISION" in u:
        return None
    if not ("COUNCIL" in u or "CNCL" in u or "COUN" in u):
        return None
    if "MAYOR" in u:
        return None
    if "DIST" not in u and "DISTRICT" not in u:
        # Older 'COUNCIL 1' style labels are seat numbers on older boundaries; skip.
        return None
    nums = re.findall(r"\d+", u)
    return nums[-1] if nums else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2023,2025",
                    help="comma-separated general-election years to combine (default = current map)")
    ap.add_argument("--source", default=str(ELECTIONS))
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
            d = tay_council_district(r.get("contest", ""))
            if not d:
                continue
            p = r["precinct"].strip()
            if not p:
                continue
            if p in mapping and mapping[p][0] != d:
                conflicts.append((p, mapping[p][0], d))
            else:
                mapping.setdefault(p, (d, r["year"]))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year", "method"])
        for p in sorted(mapping):
            w.writerow([p, mapping[p][0], mapping[p][1], "district_contest_precinct_rows"])

    per = Counter(d for d, _ in mapping.values())
    print(f"Wrote {OUT_CSV.name}: {len(mapping)} precincts across districts {dict(sorted(per.items()))}")
    if conflicts:
        print(f"WARNING: {len(conflicts)} precinct/district conflicts:")
        for p, a, b in conflicts:
            print(f"  {p}: {a} vs {b}")

    # ---- Dissolve precincts -> district polygons ----
    gdf = gpd.read_file(PRECINCTS).to_crs("EPSG:4326")
    pid_col = "PrecinctID"
    gdf["district"] = gdf[pid_col].map({p: d for p, (d, _) in mapping.items()})
    unmapped = sorted(gdf.loc[gdf["district"].isna(), pid_col].tolist())
    if unmapped:
        print(f"WARNING: {len(unmapped)} precincts had no district: {unmapped}")
    dissolved = gdf.dropna(subset=["district"]).dissolve(by="district").reset_index()
    dissolved = dissolved[["district", "geometry"]].sort_values("district")
    dissolved.to_file(OUT_DISTRICTS, driver="GeoJSON")
    print(f"Wrote {OUT_DISTRICTS.name}: {len(dissolved)} district polygons "
          f"{sorted(dissolved['district'].tolist())}")


if __name__ == "__main__":
    main()
