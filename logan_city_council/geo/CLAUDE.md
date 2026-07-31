# geo/ — Logan, Utah address → representation

## Governance model: ALL AT-LARGE (no districts)
Logan City (Cache County seat) is governed by a **Mayor + 5-member Municipal
Council**. All five council seats are elected **citywide / at-large** — they are
numbered for the ballot but are **NOT geographic districts**. There is no ward or
council-district map.

Consequence: the classic "address → council district" lookup is **degenerate**.
Every address inside the city is represented by the same six officials (Mayor +
all 5 at-large councilmembers); an address outside the city has no Logan
representation. So `address_to_district.py` reduces to an **in/out-of-city-limits**
point-in-polygon check. `district` is always `None`; `precinct` is returned only
as informational context (useful for joining by-precinct election results).

## Files
| File | What | Source |
|---|---|---|
| `city_boundary.geojson` | Logan city limits polygon | UGRC Utah Municipal Boundaries FeatureServer, `NAME='LOGAN'` |
| `precincts.geojson` | 25 Logan voter precincts (3LG01..3LG25) | UGRC VistaBallotAreas FeatureServer/0, `CountyID=3`, PrecinctID `3LG%`, dissolved to 1 polygon/precinct |
| `address_to_district.py` | address/latlon → inside Logan? + precinct | Census geocoder + local point-in-polygon |

## Sources (UGRC ArcGIS)
- **City boundary:** `services1.arcgis.com/99lidPhWCzftIe9K/.../UtahMunicipalBoundaries/FeatureServer/0`
  filtered `NAME='LOGAN'`, `outSR=4326`. Attributes confirm Logan: `COUNTYNBR='03'`
  (**Cache County**, UGRC CountyID 3), `FIPS=45860`, county seat. Centroid ≈
  (-111.84, 41.74), bounds ≈ lon[-111.90, -111.78], lat[41.68, 41.80] — the Logan
  polygon, as expected (~ -111.83, 41.74).
- **Precincts:** `services1.arcgis.com/99lidPhWCzftIe9K/.../VistaBallotAreas/FeatureServer/0`
  filtered `CountyID=3`. Cache County returns 124 ballot-area rows; the Logan-city
  subset is the **25** features whose `PrecinctID` starts with `3LG` (all carry
  `AliasName='Logan'`). The raw layer has multiple ballot-style rows per precinct
  (e.g. `3LG24:17C2`, `3LG24:CSD3`), dissolved here to one polygon per `PrecinctID`.
  Note: `AliasName='Logan'` also tags a few non-`3LG` canyon/rural areas and
  `North Logan` (`3NLG`) is a **separate city** — neither is included.

## CRS note (the gotcha that bit WVC)
UGRC has shipped VistaBallotAreas as **EPSG:26912 (UTM 12N) mislabeled as 4326**
in some fetches, which throws every point outside all polygons. This Cache County
fetch was **verified as TRUE 4326**: requested with `outSR=4326`, and the raw first
coordinate was `(-111.880, 41.677)` — Utah lon/lat, NOT UTM meters (which would be
~ (430000, 4615000)). **No reprojection was needed.** Both GeoJSONs are stored in
EPSG:4326. If you re-fetch and coords come back as large meter values, set CRS to
26912 then `.to_crs(4326)` before any point-in-polygon.

## Usage
```bash
# Address (needs internet for Census geocoder)
python3 address_to_district.py "290 N 100 W, Logan, UT 84321"
# Offline lat/long
python3 address_to_district.py --latlon 41.7370 -111.8338
# Batch (one address per line)
python3 address_to_district.py --batch addresses.txt
```
Returns inside/outside Logan city limits, the at-large council label, and the
overlapping precinct (informational; `district=None`).

### Verified tests
- `290 N 100 W, Logan, UT 84321` (Logan City Hall) → **INSIDE**, precinct `3LG12`.
- `--latlon 40.7608 -111.8910` (Salt Lake City) → **OUTSIDE** (no Logan rep).
- `2076 N 1200 E, North Logan, UT 84341` → **OUTSIDE** (North Logan is a separate city).

## Requirements
`geopandas`, `shapely` (Python); `curl` + internet for address geocoding (lat/long
lookups are fully offline).
