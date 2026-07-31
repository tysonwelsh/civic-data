# Geo — Town of Copperton boundary + address→representation (AT-LARGE)

Copperton (**Salt Lake County**, Utah, ~800 residents) is an **AT-LARGE town — there are NO
council districts**. So there is no address→district map to build: the only geographic
question is binary, **is a point inside the Town of Copperton or not**. This layer answers
that by point-in-polygon against the town boundary. Modeled on `alta_city_council/geo/` (the
sibling at-large SLCo town) and `south_jordan_city_council/geo/` (tooling shape). **As-of:
2026-07-12.**

## Copperton council structure (important for interpretation)

Copperton converted from a **metro township** (2017-01-01) to a **Town** (2024-05-01). The
current form is a separately-elected **Mayor** (voting) + a **4-member Town Council, ALL
elected AT-LARGE** (seats lettered A–E historically, but town-wide — not districts).
Non-partisan, staggered 4-year terms (A/B/C cycle = 2019/2023/2027; D/E cycle =
2017/2021/2025). Every resident is represented by the whole at-large body + the town-wide
Mayor. There are **no sub-district geometries to derive** — a town this small is a single
ballot precinct.

Current town-wide officials (2026, from `copperton.utah.gov/meet-copperton-council` + the
2025 minutes + Jan-2026 swearing-in; embedded in `address_to_district.py::COUNCIL_AT_LARGE`,
update after each election): **Mayor Sean Clayton** (voting) · **Mayor Pro Tem Tessa Stitzer**
· Kathleen Bailey · Linda McCalmon · Jonathan Pratt.

## Files
```
city_boundary.geojson    ONE Town-of-Copperton polygon, true EPSG:4326
                         (UGRC UtahMunicipalBoundaries, NAME='Copperton', COUNTYNBR '18')
precincts.geojson        the single Copperton precinct polygon (SLCo VistaBallotAreas COP001)
precinct_to_district.csv COP001 -> At-Large (single-precinct, at-large town)
address_to_district.py   CLI + importable module: address/point -> "At-Large" (in town) or None
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → in Copperton?** by point-in-polygon against `city_boundary.geojson`; fully
   offline. Inside → `district = "At-Large"`; outside → `district = None`.

`district_for_point(lon, lat)` returns `{district, in_copperton, council, lat, lon}`;
`district_for_address(address)` adds `matched_address`. There are no districts, so the return
is always **"At-Large"** (in town) or **None** (outside).

## Data sources

### Town boundary (PRIMARY)
UGRC **UtahMunicipalBoundaries** FeatureServer/0, `NAME='Copperton'`, `COUNTYNBR='18'`
(Salt Lake), fetched with `outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME='Copperton'&outFields=*&outSR=4326&f=geojson`
- **1 polygon**; props `NAME=Copperton`, `COUNTYNBR=18`, `FIPS=15720`. Bounds
  ≈ `[-112.106, 40.562, -112.079, 40.571]` (verified Utah lon/lat — Copperton sits ≈
  −112.099, 40.567, SW Salt Lake County by Bingham Canyon / Kennecott). ~2 km across, correct
  for an ~800-person town.

### Precinct (informational + join aid)
UGRC **VistaBallotAreas** FeatureServer/0, `CountyID=18 AND PrecinctID LIKE 'COP%'`, fetched
with `outSR=4326`. Returns **one** feature, **`PrecinctID = COP001`** — coextensive with the
town boundary (same bounds). This is the precinct ID under which Salt Lake County reports all
Copperton SOVC results (see `../election_results/`), so it is the join key for by-precinct
election data. `precinct_to_district.csv` maps `COP001 -> At-Large`.

### CRS note
Both layers were fetched with **`outSR=4326`** and verified to be true Utah lon/lat.
geopandas reads them as EPSG:4326 and point-in-polygon against Census lat/long works directly.
If you refetch, keep `outSR=4326` and re-verify coords look like Utah lon/lat.

## Usage
```
python3 address_to_district.py "8725 Hillcrest St, Copperton, UT 84006"
python3 address_to_district.py --latlon "40.5668 -112.0987"   # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| interior rep-point `40.5668, −112.0987` (offline) | Town of Copperton → At-Large |
| `40.7590, −111.8880` (Salt Lake City, control) | outside the Town of Copperton → None |
| `40.5622, −111.9297` (South Jordan City Hall, control) | outside the Town of Copperton → None |

## Caveats
- **AT-LARGE town — no districts, ever.** The tool returns `"At-Large"` or `None`; it never
  returns a sub-district. Do not add district geometry — the town is a single precinct.
- **Boundaries are Copperton only** — points outside the town return `None`.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare numbers;
  pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **Member names are hand-maintained** in `COUNCIL_AT_LARGE` (the GIS layer has no member
  field); update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline. The
  Census geocoder may not match every Copperton address — supply `--latlon` directly if so.
