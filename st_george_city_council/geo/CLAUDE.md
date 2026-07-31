# geo/ — St. George, Utah

## TL;DR: there are NO council districts

St. George City Council is **entirely at-large**. The body is **Mayor + 5
councilmembers**, and **all six are elected citywide** — there are **0 wards /
districts**. (The district-based "5 districts + 2 at-large" structure that shows
up in web searches belongs to **St. George, *Louisiana***, a different city —
ignore it.)

Because every in-city address is represented by the **same six officials**, the
usual *address → council district* lookup is **degenerate / identity**. There is
nothing to map. The only geographically meaningful question is:

> **Is this address inside the St. George city limits?**

So `address_to_district.py` is really an **in-city-limits check**. If a point is
inside the city, it is represented by all 5 at-large councilmembers + the Mayor;
if it is outside, it has no St. George representation.

`precinct → district` mapping is therefore **N/A (degenerate)**: every St. George
precinct elects the same citywide slate, so a precinct→district table would be a
single constant. We do not build one and you should not fabricate one.

## Files

| File | What it is |
|---|---|
| `city_limits.geojson` | St. George **city-limits polygon** (1 feature). The boundary the address tool tests against. |
| `precincts.geojson` | The 79 voter precincts that overlap St. George (subset of Washington County). **Informational only** — used for joining the by-precinct election data, NOT for district assignment. |
| `address_to_district.py` | Address (or lat/long) → **inside / outside** St. George city limits, plus the overlapping precinct for context. |

## Data sources

### City limits (`city_limits.geojson`)
- **Source:** UGRC SGID **Utah Municipal Boundaries** FeatureServer (the
  authoritative statewide `Municipalities` layer):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- **Query used:**
  `/query?where=NAME='St. George'&outFields=NAME,COUNTYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson`
- Returns **1** polygon: `NAME="St. George"`, `COUNTYNBR="27"` (Washington
  County), `FIPS="65330"`, `POPLASTCENSUS=95342`.
- Bounds ≈ lon `-113.65 … -113.48`, lat `37.00 … 37.21`.

### Precincts (`precincts.geojson`) — secondary
- **Source:** UGRC **VistaBallotAreas** FeatureServer (statewide voting precincts):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **Query used:** `?where=CountyID=27&outFields=*&outSR=4326&f=geojson`
  (Washington County is **CountyID = 27** — there is no county-name field, use
  the numeric ID), then **clipped to features intersecting the St. George
  city-limits polygon** → 79 precincts (e.g. `STG:01 … STG:NN`, plus a few
  fringe `SC:` / `IVN:` precincts that straddle the boundary).
- Human-readable precinct label is `AliasName` (e.g. `STG:12`); `PrecinctID`
  is the UGRC code (e.g. `27STG`), `VistaID` is `PrecinctID:Alias`.

## CRS note (important)

All GeoJSON here is **EPSG:4326 (lon/lat)**. The UGRC features were requested
with **`outSR=4326`** and verified: sample coords look like Utah lon/lat
(≈ `-113.5, 37.1`), **NOT UTM meters** (the `slco-election-archive` GeoJSON was
mislabeled UTM-as-4326 and broke point-in-polygon — that trap is avoided here).
`address_to_district.py` still defensively `set_crs(4326)` if missing and
`to_crs("EPSG:4326")` before any point-in-polygon test.

## Using the tool

```bash
# Address (needs internet for the free Census geocoder)
python3 address_to_district.py "175 E 200 N, St. George, UT 84770"
#   -> INSIDE St. George city limits (precinct STG:54)
#   -> represented by at-large (Mayor + 5 citywide councilmembers — no districts)

# lat/long (fully offline — no network needed)
python3 address_to_district.py --latlon 37.1102 -113.5832

# Batch: one address per line
python3 address_to_district.py --batch addresses.txt
```

As a module:
```python
from address_to_district import district_for_address, district_for_point
district_for_address("175 E 200 N, St. George, UT 84770")
# {"in_city": True, "district": None, "council": "at-large ...",
#  "precinct": "STG:54", "matched_address": "...", "lat":..., "lon":...}
```

The return dict keeps a `district` key (always `None`) for API parity with the
SLC tool, but **`in_city` is the field that matters**.

### Verified test points
| Input | Result |
|---|---|
| `175 E 200 N, St. George, UT 84770` (City Hall) | **INSIDE** (precinct `STG:54`) |
| `147 N 870 W, Hurricane, UT 84737` (Hurricane City Hall) | **OUTSIDE** |
| `--latlon 37.0966 -113.5684` (offline) | **INSIDE** (precinct `STG:38`) |
| `--latlon 37.1750 -113.2900` (offline, near Hurricane) | **OUTSIDE** |

## Dependencies
`geopandas`, `shapely` (point-in-polygon); `curl` (Census geocoder). Geocoding
needs internet; `--latlon` lookups are fully offline.

## Don't
- **Don't fabricate a district map.** St. George has none. Any "St. George
  council district N" you see is St. George, Louisiana — wrong city.
- Don't treat `precincts.geojson` as a district layer — it is for joining
  election-by-precinct data only.
