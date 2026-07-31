# Geo — Draper address/point → in-city + at-large representation

Draper elects **ALL AT-LARGE** — a separately-elected **Mayor** (city-wide, executive,
**non-voting**) + **5 Council Members elected AT-LARGE**, with **NO council districts**.
So there is **no district polygon to build and no address→district lookup**: every Draper
resident is represented by **the same 5 at-large Council Members + the Mayor**. The only
geographic question is **in Draper or not**, and Draper **straddles two counties** (Salt
Lake FIPS 49035 + Utah FIPS 49049), so the city limit itself crosses the county line.
Ported from the St. George / South Jordan sibling mechanics and adapted to the at-large,
two-county model. **As-of: 2026-07-11.**

## Files
```
city_boundary.geojson      the Draper city limit — 2 polygons (the Salt Lake-county part,
                           COUNTYNBR=18, + the Utah-county part, COUNTYNBR=25), true EPSG:4326
precincts.geojson          33 Draper voting precincts, true EPSG:4326 (two-county UNION):
                           30 Salt Lake (DRP###) + 3 Utah (25DR0N); fields precinct/county/CountyID
precinct_to_district.csv   every precinct -> "At-Large" (Draper has no districts); 33 rows
address_to_district.py     CLI + importable module: address/point -> in-Draper? + at-large body
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → in/out** by point-in-polygon against **`city_boundary.geojson`** (both
   county parts); when inside it reports the **At-Large** seat basis (all 5 Council
   Members + the Mayor) and a best-effort **precinct** (informational only — at-large, so
   the precinct carries no seat). Fully offline for `--latlon`.

`district_for_point(lon, lat)` returns
`{in_draper, seat_basis:"At-Large", council_members:[…5…], mayor, precinct, county, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Outside the city → `in_draper=False`.

## The at-large model (why there are no districts)
Draper's five Council seats are **all elected city-wide** (every election contest is
labelled `DRAPER CITY COUNCIL AT LARGE` — no district numbers ever; see
`../election_results/`). The Mayor is likewise city-wide. There is therefore **one
representation for the whole city**: `precinct_to_district.csv` maps **every** precinct to
`At-Large`, and the resolver never returns a district number. Current officials (hand-
maintained in `address_to_district.py`, update after each election): Mayor **Troy K.
Walker**; Council **Mike Green, Bryn Heather Johnson, Tasha Lowery, Fred Lowry, Kathryn
Dahlin** (Dahlin new 2025, succeeded Marsha Vawdrey). **T. Lowery (Tasha) ≠ F. Lowry
(Fred)** — two different members, near-identical surnames.

## Data sources

### City boundary (authoritative)
UGRC **Utah Municipal Boundaries** FeatureServer, `NAME='DRAPER'`, fetched with `outSR=4326`
(browser UA):
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME='DRAPER'&outFields=*&outSR=4326&f=geojson`
Returns **2 features** — the layer stores Draper as two polygons split on the county line:
**COUNTYNBR=18 (Salt Lake)** + **COUNTYNBR=25 (Utah)**. Both retained in
`city_boundary.geojson` (with a `county` field); the resolver tests containment against
either part, so a Traverse-Mountain / SunCrest (Utah-county) address correctly reads as
in-Draper.

### Precincts — TWO-COUNTY UNION (the core GIS caveat)
Draper's voting precincts span both counties, so the precinct layer **unions UGRC
`VistaBallotAreas` CountyID 18 (Salt Lake) + CountyID 25 (Utah)** — a single-county pull
would miss the Utah-county (Traverse Mountain / SunCrest) precincts.

- **Salt Lake side (30 precincts, `DRP###`):** taken from the local county mirror
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson` (UGRC
  VistaBallotAreas CountyID=18; native **EPSG:26912** → reprojected to 4326), filtered to
  the `DR`/`DRP`-prefixed Draper precincts (DRP001–029 + the mail/special **DRP901**).
- **Utah side (3 precincts, `25DR0N`):** pulled live from UGRC VistaBallotAreas
  **CountyID=25** (533 Utah-county features), filtered to the **`25DR`** (= Draper) prefix →
  **25DR01, 25DR02, 25DR03**. All three verified to intersect the Draper Utah-county
  boundary polygon. VistaBallotAreas carries only `PrecinctID/VistaID/CountyID` (no city
  name), so the `25DR` prefix (UGRC's Utah-county Draper code) is the filter; spatial
  intersection with the boundary corroborates it.
  Service:
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=25&outFields=PrecinctID,VistaID,CountyID,VersionNbr&outSR=4326&f=geojson`

### CountyID / prefix reconciliation (ties the geo to the elections)
UGRC's internal **CountyID 18 = Salt Lake, 25 = Utah** (FIPS 49035 / 49049). The Utah-side
precinct code **`25DR0N`** is exactly the precinct label that appears in the **2025 election
SOVC** — and which the county's own election normalizer **dropped** (it didn't recognize the
`25` year/county prefix), undercounting the 2025 Draper races until re-parsed from raw (see
`../election_results/CLAUDE.md`). The 2023 SOVC labelled the same Utah-side precincts
`DR301/DR302` (an older vintage); the current UGRC layer uses `25DR01/02/03`.

## Usage
```
python3 address_to_district.py "1020 E Pioneer Rd, Draper, UT 84020"
python3 address_to_district.py --latlon "40.5247 -111.8638"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-11)
| Input | Result |
|---|---|
| **1020 E Pioneer Rd** (Draper City Hall) | **IN Draper** — Salt Lake County, precinct DRP011, At-Large + Mayor Walker |
| **40.4757, −111.8300** (SunCrest / Traverse Mtn, offline) | **IN Draper** — **Utah County, precinct 25DR02** (two-county union works) |
| 451 S State St, Salt Lake City (control) | **OUTSIDE** Draper city limits |
| 40.2338, −111.6585 (Provo, control) | **OUTSIDE** Draper city limits |

## Caveats
- **NO districts / all at-large** — the resolver never returns a district; it returns the
  whole 5-member at-large body + the city-wide Mayor. `precinct_to_district.csv` is a
  degenerate map (every precinct → `At-Large`), kept for schema parity and as a by-precinct
  election-join aid — the `precinct` field joins `../election_results/*_by_precinct.csv`.
- **Two counties** — the city limit and precinct layer both cross the SL/Utah county line;
  always union CountyID **18 + 25** for precincts.
- **CRS:** the SL precincts are native EPSG:26912; reprojected to 4326 on load. If you
  refetch UGRC layers, keep `outSR=4326`.
- **Member names are hand-maintained** in `address_to_district.py::COUNCIL_AT_LARGE`/`MAYOR`
  (the GIS layers carry no member field); update after each election.
- Geocoding needs internet (Census API, free, no key); `--latlon` lookups are offline. The
  Census geocoder misses some newer Draper addresses — pass `--latlon` directly when so.
