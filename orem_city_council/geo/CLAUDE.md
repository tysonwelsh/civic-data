# geo/ — Orem, Utah

## TL;DR: there are NO council districts

Orem City Council is **entirely at-large**. The body is **Mayor + 6
councilmembers**, and **all seven are elected citywide** — there are **0 wards /
districts** (confirmed: orem.gov/citycouncil "all elected at large"; 2025 ballots
were citywide "Vote for N"). Council-Manager form of government, nonpartisan.

Because every in-city address is represented by the **same seven officials**, the
usual *address → council district* lookup is **degenerate / identity**. There is
nothing to map. The only geographically meaningful question is:

> **Is this address inside the Orem city limits?**

So `address_to_district.py` is really an **in-city-limits check**. If a point is
inside the city, it is represented by all 6 at-large councilmembers + the Mayor;
if it is outside, it has no Orem representation.

`precinct → district` mapping is therefore **N/A (degenerate)**: every Orem
precinct elects the same citywide slate, so a precinct→district table would be a
single constant. We do not build one and you should not fabricate one.

## Files

| File | What it is |
|---|---|
| `city_limits.geojson` | Orem **city-limits polygon** (1 MultiPolygon feature). The boundary the address tool tests against. |
| `precincts.geojson` | The **57** Orem voter precincts (`25OR01 … 25OR59`, gaps at `25OR55/56`). **Informational only** — for joining the by-precinct election data, NOT for district assignment. |
| `address_to_district.py` | Address (or lat/long) → **inside / outside** Orem city limits, plus the overlapping precinct for context. |

## Data sources

### City limits (`city_limits.geojson`)
- **Source:** UGRC SGID **Utah Municipal Boundaries** FeatureServer (the
  authoritative statewide municipal layer):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- **Query used:**
  `/query?where=NAME='OREM'&outFields=NAME,COUNTYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson`
- Returns **1** polygon: `NAME="Orem"`, `COUNTYNBR="25"` (**Utah County**),
  `FIPS="57300"`, `POPLASTCENSUS=98129`.
- Bounds ≈ lon `-111.74 … -111.66`, lat `40.25 … 40.33`.

### Precincts (`precincts.geojson`) — secondary
- **Source:** UGRC **VistaBallotAreas** FeatureServer (statewide voting precincts):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **Query used:** `?where=CountyID=25 AND PrecinctID LIKE '25OR%'&outFields=PrecinctID,VistaID,AliasName,CountyID&outSR=4326&f=geojson`
  (**Utah County is `CountyID = 25`** — there is no county-name field, use the
  numeric ID). Paginated `resultOffset` (transfer limit ~50/page) → **57**
  features. `PrecinctID == VistaID` (e.g. `25OR25`); `AliasName` is null for
  Orem precincts, so the tool reports `PrecinctID`.
- **Precinct-code namespace caveat:** this `25OR##` UGRC namespace differs from the
  Utah County SOVC election CSVs, which use `AF##`-style countywide precinct codes.
  Reconcile before joining election-by-precinct data to these polygons.

## CRS note (important)

All GeoJSON here is **EPSG:4326 (lon/lat)**. The UGRC features were requested
with **`outSR=4326`** and verified: sample coords look like Utah lon/lat
(≈ `-111.70, 40.26`), **NOT UTM meters** (the `slco-election-archive` GeoJSON was
mislabeled UTM-as-4326 and broke point-in-polygon — that trap is avoided here).
`address_to_district.py` still defensively `set_crs(4326)` if missing and
`to_crs("EPSG:4326")` before any point-in-polygon test.

## Using the tool

```bash
# Address (needs internet for the free Census geocoder)
python3 address_to_district.py "56 N State St, Orem, UT 84057"
#   -> INSIDE Orem city limits (precinct 25OR25)
#   -> represented by at-large (Mayor + 6 citywide councilmembers — no districts)

# lat/long (fully offline — no network needed)
python3 address_to_district.py --latlon 40.2969 -111.6946

# Batch: one address per line
python3 address_to_district.py --batch addresses.txt
```

As a module:
```python
from address_to_district import district_for_address, district_for_point
district_for_address("56 N State St, Orem, UT 84057")
# {"in_city": True, "district": None, "council": "at-large ...",
#  "precinct": "25OR25", "matched_address": "...", "lat":..., "lon":...}
```

The return dict keeps a `district` key (always `None`) for API parity with the
SLC tool, but **`in_city` is the field that matters**.

### Verified test points
| Input | Result |
|---|---|
| `56 N State St, Orem, UT 84057` (Orem City Center) | **INSIDE** (precinct `25OR25`) |
| `445 W Center St, Provo, UT 84601` (Provo City Hall) | **OUTSIDE** |
| `--latlon 40.2969 -111.6946` (offline, Orem center) | **INSIDE** (precinct `25OR30`) |
| `--latlon 40.2338 -111.6585` (offline, Provo) | **OUTSIDE** |

## Dependencies
`geopandas`, `shapely` (point-in-polygon); `curl` (Census geocoder). Geocoding
needs internet; `--latlon` lookups are fully offline.

## Don't
- **Don't fabricate a district map.** Orem has none — it is fully at-large.
- Don't treat `precincts.geojson` as a district layer — it is for joining
  election-by-precinct data only, and its `25OR##` codes still need reconciling
  with the SOVC `AF##` precinct namespace.
