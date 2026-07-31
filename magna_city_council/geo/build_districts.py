#!/usr/bin/env python3
"""Derive Magna City council-district polygons from precinct geometry + election returns.

Magna has **NO official council-district GIS layer** (no FeatureServer; confirmed 2026-07-12).
The 5 single-member districts (D1-D5) are therefore DERIVED here by assigning each Salt Lake
County **VistaBallotAreas** precinct (CountyID=18, PrecinctID 'MAG###') to the district of the
**most-recent tabulated council race that contained it**, then dissolving precincts by district.

## The redistricting seam (why this is a documented, mixed-vintage derivation)

A **precinct/boundary change happened between the 2021 and 2025 cycles** (the 2020-census
rebalance around Magna's 2024 cityhood). Evidence from the county SOVC precinct rows:

  * 2021 D2 = {MAG001, MAG003, MAG004}  ->  2025 D2 = {MAG002, MAG003, MAG004}
  * 2021 D4 = {MAG009, MAG016}          ->  2025 D4 = {MAG012, MAG013, MAG016}
    (MAG012 was D5 in 2019; MAG013 was D1 in 2019 -> both moved INTO D4 by 2025.)

Because the 2025 election only ran **D2, D4 and Mayor**, the **current** precinct membership of
**D1/D3/D5 is NOT election-derivable under the new lines** (their last tabulated race was 2019,
under the pre-2022 lines; the 2023 D1/D3/D5 cycle was cancelled/uncontested -- see
election_results/CLAUDE.md). So this map is honestly **mixed-vintage**:

  * D2, D4  -> **2025 general**  (current lines; confidence HIGH)
  * D1, D3, D5 -> **2019 general** (PRE-2022 lines; confidence MEDIUM -- may be stale)
  * 4 precincts UNRESOLVED (confidence NONE): they left their former district in the 2022 change
    and never appeared in a later district race, or postdate every election:
      - MAG001 (D2 through 2021, dropped by 2025), MAG009 (D4 through 2021, dropped by 2025),
      - MAG008 (only ever in the citywide Mayor race), MAG017 (new precinct, eff 2025-12-17).

Newest-wins resolves every overlap (2025 beats 2019), so no precinct is double-assigned. The 4
unresolved precincts are LEFT OUT of the district polygons (honest holes) -- address_to_district
reports them as "in Magna, district unresolved," never a guess.

Reproducible:  python3 build_districts.py     (reads precincts.geojson, writes the 2 outputs)
"""
import csv, json
from pathlib import Path
import geopandas as gpd

BASE = Path(__file__).resolve().parent

# ---- election-derived precinct -> district assignment (newest tabulated race wins) ----
# (precinct, district, source_year, source_contest, confidence, note)
ASSIGN = [
    # HIGH -- 2025 general (current lines)
    ("MAG002", "2", 2025, "Magna City Council District 2", "high", ""),
    ("MAG003", "2", 2025, "Magna City Council District 2", "high", ""),
    ("MAG004", "2", 2025, "Magna City Council District 2", "high", ""),
    ("MAG012", "4", 2025, "Magna City Council District 4", "high", "moved D5->D4 in 2022 redistrict"),
    ("MAG013", "4", 2025, "Magna City Council District 4", "high", "moved D1->D4 in 2022 redistrict"),
    ("MAG016", "4", 2025, "Magna City Council District 4", "high", ""),
    # MEDIUM -- 2019 general (PRE-2022 lines; D1/D3/D5 not re-run under current lines)
    ("MAG010", "1", 2019, "Magna City Council District 1", "medium", "pre-2022 lines"),
    ("MAG011", "1", 2019, "Magna City Council District 1", "medium", "pre-2022 lines"),
    ("MAG901", "1", 2019, "Magna City Council District 1", "medium", "pre-2022 lines; mail/special precinct"),
    ("MAG005", "3", 2019, "Magna City Council District 3", "medium", "pre-2022 lines"),
    ("MAG006", "3", 2019, "Magna City Council District 3", "medium", "pre-2022 lines"),
    ("MAG007", "3", 2019, "Magna City Council District 3", "medium", "pre-2022 lines"),
    ("MAG014", "5", 2019, "Magna City Council District 5", "medium", "pre-2022 lines"),
    ("MAG015", "5", 2019, "Magna City Council District 5", "medium", "pre-2022 lines"),
    # NONE -- unresolved under current lines (honest gap)
    ("MAG001", "", None, "", "none", "D2 through 2021, dropped by 2025 -> current district unknown"),
    ("MAG009", "", None, "", "none", "D4 through 2021, dropped by 2025 -> current district unknown"),
    ("MAG008", "", None, "", "none", "only ever in the citywide Mayor race -> district unknown"),
    ("MAG017", "", None, "", "none", "new precinct (eff 2025-12-17); postdates every election"),
]

# ---- write precinct_to_district.csv ------------------------------------------------
with open(BASE / "precinct_to_district.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["precinct", "district", "source_year", "source_contest", "confidence", "note"])
    for prec, dist, yr, contest, conf, note in ASSIGN:
        w.writerow([prec, dist, yr if yr else "", contest, conf, note])

amap = {p: d for p, d, *_ in ASSIGN}

# ---- dissolve assigned precincts -> district polygons ------------------------------
gdf = gpd.read_file(BASE / "precincts.geojson").to_crs("EPSG:4326")
gdf["District"] = gdf["PrecinctID"].map(amap)
assigned = gdf[gdf["District"].astype(bool) & (gdf["District"] != "")].copy()
diss = assigned.dissolve(by="District", as_index=False)[["District", "geometry"]]
diss = diss.sort_values("District").reset_index(drop=True)
# precinct-count + vintage per district for provenance in the layer
prov = {}
for prec, dist, yr, *_ in ASSIGN:
    if dist:
        prov.setdefault(dist, {"n": 0, "years": set()})
        prov[dist]["n"] += 1
        prov[dist]["years"].add(yr)
diss["n_precincts"] = diss["District"].map(lambda d: prov[d]["n"])
diss["source_year"] = diss["District"].map(lambda d: ";".join(str(y) for y in sorted(prov[d]["years"])))
diss["confidence"] = diss["District"].map(lambda d: "high" if prov[d]["years"] == {2025} else "medium")
diss.to_file(BASE / "districts.geojson", driver="GeoJSON")

print("wrote precinct_to_district.csv (18 precincts) and districts.geojson (5 districts)")
for _, r in diss.iterrows():
    print(f"  D{r['District']}: {r['n_precincts']} precincts  vintage {r['source_year']}  conf {r['confidence']}")
unresolved = [p for p, d, *_ in ASSIGN if not d]
print("  UNRESOLVED (excluded from polygons):", ", ".join(unresolved))
