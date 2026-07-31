# Geo — West Jordan address/point → council district

Maps a West Jordan, Utah address (or lat/long) to its City Council **district (1–4)**,
using Salt Lake County precinct boundaries plus a precinct→district lookup derived
from West Jordan election data and cross-checked against the city's own GIS district
polygons. Ported from `slc_city_council/geo/` (and its sibling `west_valley_city_council/geo/`,
same county / CountyID=18).

## West Jordan council structure (important for interpretation)
West Jordan has a **7-member council: 4 district seats + 3 at-large seats**, plus a
separately elected **Mayor** (Dirk Burton). Every resident is represented by **five**
elected officials: their District councilmember, **all three** At-Large councilmembers,
and the Mayor.

This tool only resolves the **District seat (1–4)**. The three At-Large members and the
Mayor are **city-wide** — they have no precinct→district mapping and are not returned
(the CLI prints a reminder that they cover everyone).

## Files
```
precincts.geojson                 West Jordan precinct boundaries, true EPSG:4326 (95 WJD precincts)
council_districts.geojson         City's authoritative 4 council-district polygons (EPSG:4326)
build_precinct_district_map.py    -> precinct_to_district.csv  (regenerable lookup)
precinct_to_district.csv          precinct, district, source_year  (96 mapped precincts)
address_to_district.py            CLI + importable module: address/point -> district
```

## How it works (precinct-based; a council-boundary polygon is not required at runtime)
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → precinct** by point-in-polygon against `precincts.geojson`
   (`PrecinctID`, e.g. `WJD052`); fully offline.
3. **precinct → district** via `precinct_to_district.csv`.

The election `precinct` column == the GIS `PrecinctID` (e.g. `WJD050`), which is what
makes the join work. Resolving by **precinct** (the actual ballot-assignment unit) is more
correct than point-in-polygon against the district outlines, because a precinct that
slightly straddles a district boundary still votes in exactly one district.

## Data sources

### Precinct boundaries
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — West Jordan
elections are administered by SLCo). Reused from
`~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson`, filtered to the
**95 `WJD`-prefixed precincts** (86 numbered WJD001–086 + 9 mail/edge precincts WJD901–909).
- Service (to refetch fresh in true 4326):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,VersionNbr,EffectiveDate&outSR=4326&f=geojson`

### City council-district polygons (authoritative boundary + cross-check)
West Jordan publishes a clean 4-district FeatureServer (city ArcGIS org, owner
`patrick.london`):
`https://services1.arcgis.com/yznraL2FyB2Sm732/arcgis/rest/services/Council_Districts/FeatureServer/0`
→ saved as `council_districts.geojson` (DISTRICTID 1–4, NAME, REPNAME). This is the
authoritative district-boundary layer. It agreed with the **2023** election-derived map
on 77/89 shared precincts (86%) vs only 69% for 2019 → it reflects the **current**
(post-2022-redistricting) boundaries. (Its REPNAME values were slightly stale at fetch
time — McConnehey/Worthen/Jacob/Pack — but the polygons are current.)

### Election data (precinct→district source of truth)
`../election_results/west_jordan_results_by_precinct.csv` — the cleaned West-Jordan-only
precinct results (county-run elections, already filtered to WJ).
`build_precinct_district_map.py` reads it; rows carry explicit `office`/`district`
columns so the district filter is exact (`office==Council`, `district∈{1,2,3,4}`,
excluding Mayor and At-Large).

## Current map derivation (post-2022 redistricting)
Unlike West Valley (staggered), **West Jordan runs all four district seats in the same
odd-year cycle**, so a single general year gives the full map. The CURRENT map is the
**2023 general** — all four districts present, no precinct in two districts:
- District 1: 25 precincts · District 2: 21 · District 3: 23 · District 4: 23 (92 total)

Then **4 GIS-only precincts** (WJD083–086, which had no 2023 district-race rows) were
backfilled by assigning each precinct polygon to the city district polygon it most
overlaps (`source_year=gis`). → **96 precincts** total
(D1=25, D2=21, **D3=27**, D4=23).

The election-derived map is canonical for the lookup; the city polygons are the boundary
authority and reconciliation cross-check. 12 of the 89 shared precincts disagree between
the two (straddle precincts where most-overlap-area ≠ where the precinct's voters cast a
district ballot); the election (voter-assignment) value wins.

## Redistricting note (2019 → 2023)
The 2019 and 2023 maps differ substantially: **28 of 68 shared precincts were reassigned**
between cycles (post-2022-census redistricting). For a **historical** question (an address
under the pre-2022 boundaries), rebuild from that era's data:
```
python3 build_precinct_district_map.py --years 2019   # pre-redistricting map (68 precincts)
```

## Usage
```
python3 build_precinct_district_map.py                  # (re)build current lookup (2023)
python3 build_precinct_district_map.py --years 2019     # historical (pre-redistricting)
python3 build_precinct_district_map.py --from-gis       # alt: assign purely by city polygons
python3 address_to_district.py "8000 S Redwood Rd, West Jordan, UT 84088"
python3 address_to_district.py --latlon 40.60612 -111.93881    # offline
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified test addresses
| Address | Precinct | District |
|---|---|---|
| 8000 S Redwood Rd (City Hall) | WJD052 | 2 |
| 7251 Plaza Center Dr (Jordan Landing) | WJD009 | 1 |
| 9000 S 1300 W | WJD067 | 2 |
| 451 S State St, Salt Lake City (control) | — | outside WJ (None) |

City Hall offline check: `--latlon 40.60612 -111.93881` → WJD052 → District 2 (matches the
address path).

## Caveats
- **Coordinate-system gotcha (handled here):** the shared `slco-election-archive` GeoJSON
  carries coordinates in **EPSG:26912 (UTM 12N)** (≈ 424259, 4508665), not 4326 lon/lat.
  `precincts.geojson` here was read as 26912 and reprojected to **true** EPSG:4326 (CRS84),
  so its bounds are Utah lon/lat (≈ −112.0, 40.6) and point-in-polygon against Census
  lat/long works. If you ever refresh this file from the archive, redo that reprojection
  (or fetch fresh from UGRC with `outSR=4326` and verify the coords look like Utah lon/lat,
  not UTM meters).
- **CountyID = 18** is Salt Lake County in UGRC VistaBallotAreas — the key for the precinct
  query and the join to SLCo SOVC results.
- **At-large (3 seats) + Mayor are city-wide** — no precinct→district mapping; the tool
  never returns them. The CLI prints a reminder that every district resident also has 3
  at-large members and the Mayor.
- **Mail / edge precincts without (district) polygons:** the lookup has 96 precincts; the
  precinct layer has 95 polygons. A few `WJD90x` mail/provisional precincts appear in the
  election data but have **no polygon** (so no address resolves to them), and conversely
  WJD083–086 had polygons but no 2023 district-race rows (backfilled from GIS). A point in
  an unmapped precinct resolves to the precinct with District = None rather than guessing.
- **Redistricting:** `precinct_to_district.csv` is the CURRENT map (2023 general +
  post-2022 boundaries). Rebuild with `--years 2019` for the prior map.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
- Boundaries are West Jordan only; points outside West Jordan return district None.
