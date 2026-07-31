# Geo — Magna City address/point → council district

Maps a Magna, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **precinct-derived** district polygons. Modeled on
`south_jordan_city_council/geo/` (same county; Salt Lake County, UGRC CountyID = 18).
**As-of: 2026-07-12.**

## Magna council structure (important for interpretation)
Magna is a Salt Lake County **metro township (seated 2017) → CITY (2024-05-01)**. The council
is elected by **5 single-member DISTRICTS (1–5)**. From the **2025** cycle there is also a
separately-elected, citywide **executive Mayor** (Mick "Mickey" Sudbury — presides, **does NOT
vote**; the metro-township era had **no** separate mayor — the council elected its own Chair).
There are **no at-large council seats**. This tool resolves only the **District seat (1–5)**;
the Mayor is city-wide and is not returned.

Current district members (from `magna.utah.gov/171/City-Council` + the 2026-05-26 minutes
header; embedded in `address_to_district.py::COUNCIL_MEMBERS`, update after each election):
D1 = **Steve Prokopis** · D2 = **Megan L. Olsen** · D3 = **Michael H. Jensen** ·
D4 = **Terry George** (Mayor Pro Tem) · D5 = **Audrey Pierce**. (Mayor, city-wide, non-voting:
Mick Sudbury.)

## Files
```
city_boundary.geojson       Magna City outline, EPSG:4326 (UGRC Municipalities NAME='Magna City')
precincts.geojson           18 Magna (MAG-prefixed) SLCo precincts, EPSG:4326 (UGRC VistaBallotAreas)
districts.geojson           5 precinct-DERIVED district polygons (field "District"="1".."5" +
                            n_precincts, source_year, confidence); MIXED-VINTAGE (see below)
precinct_to_district.csv    precinct -> district w/ source_year + confidence (18 rows)
build_districts.py          reproducible: precincts.geojson + election returns -> the 2 outputs
address_to_district.py      CLI + importable module: address/point -> district 1-5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`; fully offline.
   A point inside `city_boundary.geojson` but outside every district polygon returns
   district `None` with an **"in Magna, district unresolved"** note (never a guess); a point
   outside the city returns **"outside Magna."**

`district_for_point(lon, lat)` returns `{district, council_member, in_magna, note, lat, lon}`;
`district_for_address(address)` adds `matched_address`.

## ⚠ Districts are PRECINCT-DERIVED and MIXED-VINTAGE (Magna has no official district GIS layer)

There is **no** official Magna council-district FeatureServer (confirmed 2026-07-12 — the UGRC
Municipalities layer carries only the city outline; no county/city district layer exists). So
`districts.geojson` is **derived**: each SLCo VistaBallotAreas precinct (CountyID=18,
`PrecinctID='MAG###'`) is assigned to the district of the **most-recent tabulated council race
that contained it**, then precincts are dissolved by district.

**A precinct/boundary change happened between the 2021 and 2025 cycles** (the 2020-census
rebalance around Magna's 2024 cityhood), proven by the county SOVC precinct rows:
- 2021 D2 `{MAG001, MAG003, MAG004}` → 2025 D2 `{MAG002, MAG003, MAG004}`
- 2021 D4 `{MAG009, MAG016}` → 2025 D4 `{MAG012, MAG013, MAG016}` (MAG012 was D5 in 2019;
  MAG013 was D1 in 2019 — both moved **into** D4).

The 2025 election ran only **D2, D4 and Mayor**, so the **current** precinct membership of
**D1/D3/D5 is not election-derivable under the new lines** (their last tabulated race was 2019,
under pre-2022 lines; the 2023 D1/D3/D5 cycle was cancelled/uncontested — see
`../election_results/CLAUDE.md`). The map is therefore honestly mixed-vintage:

| District | Precincts | Vintage | Confidence |
|---|---|---|---|
| **D2** | MAG002, 003, 004 | **2025 general** (current lines) | **high** |
| **D4** | MAG012, 013, 016 | **2025 general** (current lines) | **high** |
| **D1** | MAG010, 011, 901 | 2019 general (**pre-2022 lines**) | medium |
| **D3** | MAG005, 006, 007 | 2019 general (**pre-2022 lines**) | medium |
| **D5** | MAG014, 015 | 2019 general (**pre-2022 lines**) | medium |

Newest-wins resolves every overlap (2025 beats 2019), so **no precinct is double-assigned**.
The address tool tags D1/D3/D5 hits with a "district lines PRE-2022 (medium confidence)" note.

### 4 UNRESOLVED precincts (honest holes — excluded from the polygons)
- **MAG001** — D2 through 2021, dropped by 2025 → current district unknown (now some of D1/D3/D5).
- **MAG009** — D4 through 2021, dropped by 2025 → current district unknown.
- **MAG008** — only ever in the citywide Mayor race → district unknown.
- **MAG017** — new precinct (eff 2025-12-17); postdates every election → district unknown.

A point in one of these returns district `None` + "in Magna, district unresolved," never a
guess. **To fully resolve them**, an official Magna 2022-redistricting map (county Clerk / MSD),
or the next tabulated D1/D3/D5 race (2027) under current lines, is required. Logged, not
fabricated.

## Data sources
- **City boundary** — UGRC **Municipalities** FeatureServer, `NAME='Magna City'`,
  `COUNTYNBR='18'` (Salt Lake): `…/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME='Magna City'&outSR=4326&f=geojson`. **The name is `'Magna City'`, not `'MAGNA'`** (the recon's `NAME='MAGNA'` returns 0 features).
- **Precincts** — UGRC **VistaBallotAreas** FeatureServer, `CountyID=18 AND PrecinctID LIKE 'MAG%'`,
  `outSR=4326` → 18 features (MAG001–017 + MAG901, all EffectiveDate 2025-12-17 = current version).
- **District assignment** — from `../election_results/magna_results_by_precinct.csv`
  (2025 D2/D4; 2019 D1/D3/D5), encoded in `build_districts.py::ASSIGN`.
- **CRS** — all layers fetched with `outSR=4326` and verified as true Utah lon/lat (Magna bbox
  ≈ `[-112.26, 40.68, -112.06, 40.81]`). geopandas reads them as EPSG:4326; point-in-polygon
  against Census lat/long works directly. If you refetch, keep `outSR=4326`.

## Usage
```
python3 address_to_district.py "8952 W Magna Main St, Magna, UT 84044"
python3 address_to_district.py --latlon "40.709 -112.101"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.
Rebuild the derived layers: `python3 build_districts.py` (idempotent; reads `precincts.geojson`).

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| 8952 W Magna Main St (Webster Center / city hall) | District 2 (Megan L. Olsen) — high-confidence 2025 precinct |
| D1/D3/D5 interior points (offline) | resolve to their own district (with pre-2022 note) |
| D2/D4 interior points (offline) | resolve to their own district (high confidence) |
| MAG017 / MAG008 interior point | in Magna, district unresolved (honest) |
| 451 S State St, Salt Lake City (control) | outside Magna → None |

## Caveats
- **The Mayor is city-wide** (non-voting, executive form) — no district mapping; never returned.
- **Mixed-vintage, precinct-derived districts** — D2/D4 current (2025), D1/D3/D5 pre-2022 (2019);
  4 precincts unresolved. Treat D1/D3/D5 boundaries as **medium confidence** near edges; do not
  quote them for tight boundary-edge questions. Rebuild when an official district map or a
  post-2022 D1/D3/D5 election appears.
- **Member names are hand-maintained** in `COUNCIL_MEMBERS` (no member field on any GIS layer);
  update after each election.
- **`--latlon` quoting:** longitude is negative, so pass the pair as one quoted token
  (`--latlon "LAT -LON"`; comma also accepted).
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline. The
  Census geocoder may miss some valid Magna addresses — supply `--latlon` directly when it does.
