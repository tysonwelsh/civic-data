# Geo — Emigration Canyon address/point -> in-city? (AT-LARGE, no districts)

Emigration Canyon (Salt Lake County) elects its **5-member council entirely AT-LARGE**
(no wards/districts); the council selects one of the five as Mayor, who presides and
**votes**. There is therefore **no district to resolve** — this tool answers the only
meaningful geographic question: **is an address inside Emigration Canyon?** — by
point-in-polygon against the UGRC municipal boundary. Inside -> `"At-Large"`; outside ->
None. Modeled on `south_jordan_city_council/geo/` (same county; UGRC CountyID = 18).
**As-of: 2026-07-12.**

Emigration Canyon was a **Metro Township (2017-2024)** and is a **CITY since 2024-05-01**
(H.B. 35) — the same at-large body throughout; the boundary/point test is unaffected.

## Files
```
city_boundary.geojson       single Emigration Canyon polygon, true EPSG:4326
                            (UGRC UtahMunicipalBoundaries; NAME='Emigration Canyon',
                             COUNTYNBR=18, ENTITYNBR=3901, pop 1466)
precincts.geojson           the ONE Emigration ballot precinct, EMG001 (EPSG:4326)
precinct_to_district.csv    EMG001 -> At-Large (single precinct; there are no districts)
address_to_district.py      CLI + importable module: address/point -> in-city? -> At-Large
```

## How it works
1. **address -> lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long -> in-city** by point-in-polygon against `city_boundary.geojson`; fully
   offline. Inside -> `district="At-Large"`, `in_city=True`, and the 5 at-large council
   members are returned; outside -> `district=None`, `in_city=False`.

`district_for_point(lon, lat)` -> `{district, in_city, council, lat, lon}`;
`district_for_address(address)` adds `matched_address`.

## Data sources
### City boundary (authoritative, PRIMARY)
UGRC **Utah Municipal Boundaries** FeatureServer/0, `NAME='Emigration Canyon'`
(`COUNTYNBR='18'` = Salt Lake), fetched as GeoJSON with `outSR=4326`:
```
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME%3D%27Emigration%20Canyon%27&outFields=NAME,COUNTYNBR,ENTITYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson
```
One **single Polygon**, 273 vertices, bbox lon `[-111.810, -111.689]` lat `[40.745, 40.835]`
— the long, narrow canyon corridor east of Salt Lake City. NOTE: a `UPPER(NAME) LIKE '%…%'`
query returned HTTP 400 on this service; the **exact-match `NAME='Emigration Canyon'`** form
works — use it on refetch. Use a browser UA.

### Precinct (single; informational + join aid)
UGRC **VistaBallotAreas** FeatureServer/0, `CountyID=18`, filtered to the **one** Emigration
precinct **EMG001** (1008 SLCo features statewide-county -> 1 Emigration). Its extent matches
the boundary bbox. This is the same `EMG001` that carries every Emigration row in the SOVC
(`election_results/`), so the precinct table joins by-precinct election data straight to the
at-large body.

## Usage
```
python3 address_to_district.py "5025 E Emigration Canyon Rd, Salt Lake City, UT 84108"
python3 address_to_district.py --latlon "40.7700 -111.7600"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| representative interior point (40.790, -111.733), offline | in Emigration Canyon -> At-Large |
| mid-canyon 40.77, -111.76 (offline) | in Emigration Canyon -> At-Large (5 members returned) |
| SLC City Hall 40.755, -111.888 (control, west of the canyon mouth) | outside -> None |
| Provo 40.234, -111.659 (far control) | outside -> None |

## Caveats
- **No districts, no separately-elected mayor.** All 5 seats are at-large; the Mayor is one
  of the five (council-selected) and is included in the returned `council` list. `"At-Large"`
  is a sentinel for "inside the single city-wide body," not a district id.
- **Boundaries are Emigration Canyon only** — points outside return None.
- **Council names are hand-maintained** in `address_to_district.py::COUNCIL` (the GIS layer
  has no member field); update after each election (elections are at-large, so there is no
  per-district field to maintain).
- **`--latlon` quoting:** longitude is negative, so pass the pair as one quoted token
  (`--latlon "LAT -LON"`; comma also accepted).
- Geocoding needs internet (Census API, free, no key); `--latlon` lookups are offline.
- **CRS:** the boundary was fetched with `outSR=4326` and verified to be true Utah lon/lat
  (≈ -111.7, 40.79). Keep `outSR=4326` on any refetch.
