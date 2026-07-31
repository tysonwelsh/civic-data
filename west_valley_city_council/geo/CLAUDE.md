# Geo — West Valley City address/point → council district

Maps a West Valley City address (or lat/long) to its City Council **district (1–4)**,
using Salt Lake County precinct boundaries plus a precinct→district lookup derived
from West Valley election data. Ported from `slc_city_council/geo/`.

## West Valley City council structure (important for interpretation)
WVC has a **7-member council: 4 district seats + 2 at-large seats**, plus a separately
elected **Mayor**. Every resident is represented by **four** elected officials: their
District councilmember, **both** At-Large councilmembers, and the Mayor.

This tool only resolves the **District seat (1–4)**. The two At-Large members and the
Mayor are **city-wide** — they have no precinct→district mapping and are not returned
(the CLI prints a reminder that they cover everyone).

## Files
```
precincts.geojson                 West Valley City precinct boundaries, EPSG:4326 (71 WVC precincts)
build_precinct_district_map.py    -> precinct_to_district.csv  (regenerable lookup)
precinct_to_district.csv          precinct, district, source_year  (70 mapped precincts)
address_to_district.py            CLI + importable module: address/point -> district
```

## How it works (no council-boundary polygon file needed)
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → precinct** by point-in-polygon against `precincts.geojson`
   (`PrecinctID`, e.g. `WVC027`); fully offline.
3. **precinct → district** via `precinct_to_district.csv`.

The election `precinct` column == the GIS `PrecinctID` (e.g. `WVC003`), which is what
makes the join work. The district map is built from election data: each WVC council-
DISTRICT contest lists its precincts, so contest→precincts == district→precincts.

## Data sources
- **Precinct boundaries:** UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18**
  (Salt Lake County — WVC is administered by SLCo). Reused from
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson`, filtered to the
  71 `WVC`-prefixed precincts.
  - To refetch from scratch: the slco-archive `scripts/fetch_geometry.py` (CountyID=18),
    then filter `PrecinctID LIKE 'WVC%'`.
  - Service:
    `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,VersionNbr,EffectiveDate&outSR=4326&f=geojson`
- **Election data (precinct→district source of truth):**
  `~/Desktop/slco-election-archive/data/municipal_results_long.csv` — the shared SLCo
  archive (WVC elections are county-run). `build_precinct_district_map.py` reads it.

## Current map derivation (post-2022 redistricting)
WVC district seats are **staggered**: Districts **1 & 3** are on the ballot one odd-year
cycle, Districts **2 & 4** the next. The CURRENT map combines the two most recent generals:
- **2023:** District 1 (15 precincts), District 3 (14)
- **2025:** District 2 (19 precincts), District 4 (22)

→ **70 precincts** mapped, no overlap between districts. The contest filter excludes
Mayor, At-Large (city-wide), and school races, and requires the contest to start with
`WEST VALLEY` (so neighboring SLCo cities don't leak in).

## Usage
```
python3 build_precinct_district_map.py                       # (re)build the lookup (2023+2025)
python3 build_precinct_district_map.py --years 2021,2025     # historical / alt snapshot
python3 address_to_district.py "3600 S Constitution Blvd, West Valley City, UT 84119"
python3 address_to_district.py --latlon 40.6942 -111.9581    # offline
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified test addresses
| Address | Precinct | District |
|---|---|---|
| 3600 S Constitution Blvd (City Hall) | WVC027 | 2 |
| 3200 S Decker Lake Dr (Maverik Center) | WVC016 | 1 |
| 3600 S 5600 W (Granger area) | WVC020 | 4 |
| 451 S State St, Salt Lake City (control) | — | outside WVC (None) |

## Caveats
- **Coordinate-system gotcha (fixed here):** the source slco-archive geojson is written
  with coordinates in **EPSG:26912 (UTM 12N)** but mislabeled as EPSG:4326 (its
  `fetch_geometry.py` reprojects to a UTM working CRS before writing). `precincts.geojson`
  in this folder was re-set to 26912 then reprojected to **true** EPSG:4326, so
  point-in-polygon against Census lat/long works. If you ever refresh this file from the
  archive, redo that fix (or fetch fresh in real 4326).
- **Redistricting:** `precinct_to_district.csv` is the CURRENT map (2023+2025 generals,
  post-2022-census boundaries adopted March 2022, Municipal Code §2-3-103). For a
  historical question, rebuild with `--years YYYY,YYYY` from that era's election data.
  (Note older WVC contests use *seat numbers* like "Council #1"/"Coun 1" rather than
  district labels; the builder only counts explicit `DISTRICT N` contests for the current
  map.)
- **PRIOR (pre-2022) map — RECONSTRUCTED 2026-07-19** at `geo/council_districts_pre2022.geojson`
  + `geo/precinct_to_district_pre2022.csv` (via `scripts/build_prior_district_map.py --city
  west_valley_city_council --years 2019,2021` — the 2019 D1/D3 + 2021 D2/D4 district-contest
  precincts dissolved over current precinct shapes). **APPROXIMATE + UNRELIABLE:** old assignment
  over current-vintage precinct shapes; 64/74 old WVC codes carry geometry, 10 edge holes, WVC038 a
  resolved 2019-D1/2021-D2 conflict (→D2). **GEOMETRY confidence DOWNGRADED medium→`low` 2026-07-19**:
  WVC publishes NO combined council-district GIS (only a City Boundary + current per-district SLCo
  services), and a fragmentation control proved precinct-code renumbering beyond the known holes (the
  current-assignment dissolve makes clean 1–2-piece districts but this pre-2022 dissolve makes up to
  8-piece fragments on D2) — the millcreek defect. Wired into `roster/district_versions.csv` (`plan_pre2022`,
  geometry `low`); the `district_precincts` precinct-CODE composition stays `medium` (a faithful SOVC
  record). See `scripts/roster_boundary_recon.md`.
- **At-large + Mayor are city-wide** — no precinct→district mapping; the tool never
  returns them. (2025 cycle: an At-Large seat was reportedly decided by coin-toss/runoff;
  irrelevant to district geocoding.)
- **`WVC067`** has a GIS polygon but **no district** in the lookup (no district-race votes
  in 2023/2025 — likely a sliver/mail precinct). A point there resolves to the precinct
  but District = None.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
- Boundaries are WVC only; points outside West Valley City return district None.
- District-polygon FeatureServer at `gisportal.wvc-ut.gov` was **not** needed — precinct
  aggregation from election data (the SLC-matching primary method) produced a clean,
  non-overlapping 4-district map, so it was not pursued.
