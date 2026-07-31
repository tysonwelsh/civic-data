#!/usr/bin/env python3
"""
Build precinct_to_district.csv — the lookup that powers address->district for Provo.

Two sources of truth, reconciled:

1. The authoritative CURRENT precinct->district assignment is published by Provo City
   itself in its GIS "Precinct Boundary" layer (Council/Council_Districts/FeatureServer/1),
   which carries both a PRECINCT code (e.g. 25PR04) and a COUNCIL_DISTRICT (1-5). This is
   the post-redistricting map current as of the 2023 cycle (cf. Provo City Code 2.01.050).
   geo/precincts.geojson is fetched straight from that layer, so the district is already on
   each polygon. This covers ALL FIVE districts.

2. The precinct-level ELECTION data (election_results/provo_results_by_precinct.csv) only
   contains the District 2, District 5, and Citywide I + Mayor contests, for 2021 and 2025
   (the odd-year-A cycle). Districts 1/3/4 (odd-year-B: 2019/2023) have NO precinct CSV
   published, so they cannot be derived from election data. We USE the 2025 District 2 and
   District 5 precinct lists to CROSS-VALIDATE the city GIS map (they match), and record
   2025 as the source_year for those two districts. Districts 1/3/4 are recorded with
   source_year = "gis-2023map" (the city's current published map; ordinance/2.01.050).

Provo precinct codes:
  - Election CSV uses `PR##` (e.g. PR04). The Provo GIS / UGRC Vista layers use `25PR##`
    (CountyID 25 + PR##). They reconcile by stripping the `25` prefix. We store the canonical
    `25PR##` code (what's on the geometry) and the join works because precincts.geojson and
    this CSV both key on PRECINCT == 25PR##.

Output columns: precinct, district, source_year

Usage:
    python3 build_precinct_district_map.py        # build current map from precincts.geojson
"""

import csv
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
PRECINCTS = BASE / "precincts.geojson"
ELECTIONS = BASE.parent / "election_results" / "provo_results_by_precinct.csv"
OUT = BASE / "precinct_to_district.csv"

# Districts corroborated by 2025 precinct-level election data; the rest come from the
# city's current GIS map (the 2023-cycle redistricted boundaries, per Provo City Code).
ELECTION_VALIDATED = {"2", "5"}
GIS_SOURCE = "gis-2023map"
ELECTION_YEAR = "2025"


def election_precincts_by_district():
    """{district: set(PR## codes)} from the 2025 municipal general (D2 & D5 only)."""
    out = defaultdict(set)
    if not ELECTIONS.exists():
        return out
    for r in csv.DictReader(open(ELECTIONS, newline="", encoding="utf-8")):
        if (r["year"] == ELECTION_YEAR and r["office"] == "Council"
                and r["election_type"] == "municipal general"
                and r["district"] in ELECTION_VALIDATED):
            out[r["district"]].add(r["precinct"].strip())
    return out


def main():
    import geopandas as gpd
    gdf = gpd.read_file(PRECINCTS)

    # Build {25PR## -> district} from the authoritative city GIS layer.
    gis = {}
    for _, row in gdf.iterrows():
        prec = str(row["PRECINCT"]).strip()
        d = row["COUNCIL_DISTRICT"]
        if d is None or (isinstance(d, float) and d != d):  # NaN -> not in any Provo district
            continue
        gis[prec] = str(int(float(d)))

    # Cross-validate D2/D5 against 2025 election precinct lists (PR## == 25PR## sans prefix).
    elec = election_precincts_by_district()
    for d, ps in elec.items():
        gis_set = {p[2:] for p, gd in gis.items() if gd == d and p.startswith("25")}
        only_elec = ps - gis_set
        only_gis = gis_set - ps
        if only_elec or only_gis:
            print(f"  NOTE D{d}: election-only {sorted(only_elec)} | gis-only {sorted(only_gis)}")
        else:
            print(f"  validated D{d}: {len(ps)} precincts match 2025 election exactly")

    rows = []
    for prec in sorted(gis):
        d = gis[prec]
        src = ELECTION_YEAR if d in ELECTION_VALIDATED else GIS_SOURCE
        rows.append((prec, d, src))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year"])
        w.writerows(rows)

    per = defaultdict(int)
    for _, d, _ in rows:
        per[d] += 1
    print(f"\nWrote {OUT.name}: {len(rows)} precincts -> districts {dict(sorted(per.items()))}")


if __name__ == "__main__":
    main()
