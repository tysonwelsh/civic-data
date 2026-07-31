# geo/ — Vineyard, Utah

## TL;DR: there are NO council districts

Vineyard City Council is **entirely at-large**. The body is **Mayor + 5
councilmembers** (UCA "six-member council" form, adopted by Nov 2024 Proposition 10,
effective Jan 2026; the Mayor chairs meetings and votes). **All six are elected
citywide — there are 0 wards / districts.**

Because every in-city address is represented by the **same six officials**, the usual
*address → council district* lookup is **degenerate / identity**. There is nothing to
map. The only geographically meaningful question is:

> **Is this address inside the Vineyard city limits?**

So `address_to_district.py` is really an **in-city-limits check**. If a point is inside
the city, it is represented by all 5 at-large councilmembers + the Mayor; if it is
outside, it has no Vineyard representation.

`precinct → district` mapping is therefore **N/A (degenerate)**: every Vineyard precinct
elects the same citywide slate, so a precinct→district table would be a single constant.
We do not build one and you should not fabricate one.

## Files

| File | What it is |
|---|---|
| `city_limits.geojson` | Vineyard **city-limits polygon** (1 feature). The boundary the address tool tests against. |
| `precincts.geojson` | The **9** voter precincts that overlap Vineyard (`25VI01`–`25VI09`, subset of Utah County). **Informational only** — used for joining the by-precinct election data, NOT for district assignment. |
| `address_to_district.py` | Address (or lat/long) → **inside / outside** Vineyard city limits, plus the overlapping precinct for context. |

## Data sources

### City limits (`city_limits.geojson`)
- **Source:** UGRC SGID **Utah Municipal Boundaries** FeatureServer (the authoritative
  statewide municipalities layer):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- **NAME-match-fails note (important):** `AliasName` is empty for Vineyard and a plain
  `NAME='Vineyard'` filter is unreliable here, so the polygon was fetched **by FIPS**:
  `/query?where=FIPS=80420&outFields=NAME,COUNTYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson`
- Returns **1** polygon: `NAME="Vineyard"`, `COUNTYNBR="25"` (Utah County),
  `FIPS="80420"`, `POPLASTCENSUS=12543`.
- Bounds ≈ lon `-111.772 … -111.733`, lat `40.278 … 40.333`.

### Precincts (`precincts.geojson`) — secondary
- **Source:** UGRC **VistaBallotAreas** FeatureServer (statewide voting precincts):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **Query used:** `?where=CountyID=25&outFields=*&outSR=4326&f=geojson`
  (**Utah County = CountyID 25** — there is no county-name field, use the numeric ID),
  then **clipped to features whose area meaningfully intersects the Vineyard city-limits
  polygon** → **9** precincts: `25VI01` … `25VI09`.
- **NAME-match fails here too:** `AliasName` is empty for Vineyard's precincts, so name
  matching is impossible — the precincts were selected by **spatial intersect** against
  the city polygon (not by name). The precinct code lives in `VistaID` / `PrecinctID`
  (e.g. `25VI07`); `AliasName` is `None`.
- Recon expected `25VI01`–`08`; the live spatial intersect returns **9** (`25VI09`
  present). The spatial result is authoritative.

## CRS note (important)

All GeoJSON here is **EPSG:4326 (lon/lat)**. The UGRC features were requested with
**`outSR=4326`** and verified: sample coords look like Utah lon/lat (≈ `-111.75, 40.30`),
**NOT UTM meters** (the `slco-election-archive` GeoJSON was mislabeled UTM-as-4326 and
broke point-in-polygon — that trap is avoided here). `address_to_district.py` still
defensively `set_crs(4326)` if missing and `to_crs("EPSG:4326")` before any
point-in-polygon test.

## Using the tool

```bash
# Address (needs internet for the free Census geocoder)
python3 address_to_district.py "125 S Main St, Vineyard, UT 84059"
#   -> INSIDE Vineyard city limits (precinct 25VI07)
#   -> represented by at-large (Mayor + 5 citywide councilmembers — no districts)

# lat/long (fully offline — no network needed)
python3 address_to_district.py --latlon 40.3035 -111.7545

# Batch: one address per line
python3 address_to_district.py --batch addresses.txt
```

As a module:
```python
from address_to_district import district_for_address, district_for_point
district_for_address("125 S Main St, Vineyard, UT 84059")
# {"in_city": True, "district": None, "council": "at-large ...",
#  "precinct": "25VI07", "matched_address": "...", "lat":..., "lon":...}
```

The return dict keeps a `district` key (always `None`) for API parity with the SLC /
St. George tools, but **`in_city` is the field that matters**.

### Verified test points
| Input | Result |
|---|---|
| `125 S Main St, Vineyard, UT 84059` (City Hall) | **INSIDE** (precinct `25VI07`) |
| `56 N State St, Orem, UT 84057` (Orem City Hall) | **OUTSIDE** |
| `--latlon 40.3035 -111.7545` (offline, City Hall area) | **INSIDE** (precinct `25VI08`) |
| `--latlon 40.2969 -111.6946` (offline, Orem) | **OUTSIDE** |

## Dependencies
`geopandas`, `shapely` (point-in-polygon); `curl` (Census geocoder). Geocoding needs
internet; `--latlon` lookups are fully offline.

## Don't
- **Don't fabricate a district map.** Vineyard has none — it is at-large.
- Don't treat `precincts.geojson` as a district layer — it is for joining
  election-by-precinct data only.
- Don't filter UGRC layers by `NAME`/`AliasName` for Vineyard (both empty/unreliable) —
  use FIPS=80420 for the city polygon and CountyID=25 + spatial intersect for precincts.
