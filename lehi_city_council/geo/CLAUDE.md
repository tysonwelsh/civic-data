# geo/ — Lehi, Utah

## TL;DR: there are NO council districts

Lehi City Council is **entirely at-large**. The body is **Mayor + 5 council members**
(UCA "six-member council" form). **All five council seats are elected citywide — there
are 0 wards / districts.** Ballot seats are *numbered* ("City Council 1st Seat", "2nd
Seat", ...) for sequencing, but those numbers are NOT geographic districts. The Mayor
presides and votes only to break a tie.

Because every in-city address is represented by the **same six officials**, the usual
*address → council district* lookup is **degenerate / identity**. There is nothing to
map. The only geographically meaningful question is:

> **Is this address inside the Lehi city limits?**

So `address_to_district.py` is really an **in-city-limits check**. If a point is inside
the city, it is represented by all 5 at-large councilmembers + the Mayor; if it is
outside, it has no Lehi representation. This mirrors the St. George and Vineyard
at-large tools.

`precinct → district` mapping is therefore **N/A (degenerate)**: every Lehi precinct
elects the same citywide slate, so a precinct→district table would be a single constant.
We do not build one and you should not fabricate one.

## Files

| File | What it is |
|---|---|
| `city_boundary.geojson` | Lehi **city-limits polygon** (1 feature). The boundary the address tool tests against. |
| `precincts.geojson` | The **55** voter precincts named for Lehi (`25LE01`–`25LE56`, subset of Utah County). **Informational only** — used for joining the by-precinct election data, NOT for district assignment. |
| `address_to_district.py` | Address (or lat/long) → **inside / outside** Lehi city limits, plus the overlapping precinct for context. |

## Data sources

### City limits (`city_boundary.geojson`)
- **Source:** UGRC SGID **Utah Municipal Boundaries** FeatureServer (the authoritative
  statewide municipalities layer):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- **Query used:**
  `/query?where=NAME='LEHI'&outFields=NAME,COUNTYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson`
- Returns **1** polygon: `NAME="Lehi"`, `COUNTYNBR="25"` (**Utah County**),
  `FIPS="44320"`, `POPLASTCENSUS=75907`.
- Bounds ≈ lon `-111.945 … -111.815`, lat `40.355 … 40.472`.

### Precincts (`precincts.geojson`) — secondary
- **Source:** UGRC **VistaBallotAreas** FeatureServer (statewide voting precincts):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **Query used:** `?where=CountyID=25 AND VistaID LIKE '25LE%'&outFields=VistaID,PrecinctID,SubPrecinctID,AliasName,CountyID&outSR=4326&f=geojson`
  (**Utah County = CountyID 25** — there is no county-name field, use the numeric ID).
- Returns **55** Lehi precincts: `25LE01` … `25LE56` (note: `25LE54` is absent in the
  current UGRC version — the live result is authoritative, 55 features, not a gap in this
  build). All 55 spatially intersect the Lehi city polygon (verified).
- **NAME-match note:** `AliasName` is empty (`None`) for Lehi's precincts, so name
  matching is impossible — the precinct code lives in `VistaID` / `PrecinctID`
  (e.g. `25LE33`). The `25LE` prefix (CountyID `25` + city code `LE`) is the key.

## CRS note (important)

All GeoJSON here is **EPSG:4326 (lon/lat)**. The UGRC features were requested with
**`outSR=4326`** and verified: sample coords look like Utah lon/lat
(city ≈ `-111.83, 40.42`; precincts ≈ `-111.84, 40.46`), **NOT UTM meters** (the
`slco-election-archive` GeoJSON was mislabeled UTM-as-4326 and broke point-in-polygon —
that trap is avoided here, and bit the WVC build). `address_to_district.py` still
defensively `set_crs(4326)` if missing and `to_crs("EPSG:4326")` before any
point-in-polygon test. City and precinct bounds line up exactly (both ≈ -111.945…-111.815
lon, 40.355…40.472 lat), confirming the two layers share the same CRS.

## Using the tool

```bash
# Address (needs internet for the free Census geocoder)
python3 address_to_district.py "153 N 100 E, Lehi, UT 84043"
#   -> INSIDE Lehi city limits (precinct 25LE42)
#   -> represented by at-large (Mayor + 5 citywide councilmembers — no districts)

# lat/long (fully offline — no network needed)
python3 address_to_district.py --latlon 40.3916 -111.8508

# Batch: one address per line
python3 address_to_district.py --batch addresses.txt
```

As a module:
```python
from address_to_district import district_for_address, district_for_point
district_for_address("153 N 100 E, Lehi, UT 84043")
# {"in_city": True, "district": None, "council": "at-large ...",
#  "precinct": "25LE42", "matched_address": "...", "lat":..., "lon":...}
```

The return dict keeps a `district` key (always `None`) for API parity with the SLC /
St. George / Vineyard tools, but **`in_city` is the field that matters**.

### Verified test points
| Input | Result |
|---|---|
| `153 N 100 E, Lehi, UT 84043` (City Hall, Census geocode) | **INSIDE** (precinct `25LE42`) |
| `--latlon 40.3916 -111.8508` (offline, City Hall area) | **INSIDE** (precinct `25LE33`) |
| `351 W Center St, Provo, UT 84601` (Provo City Hall) | **OUTSIDE** |
| `--latlon 40.2338 -111.6585` (offline, Provo) | **OUTSIDE** |

(The geocoded City Hall lands one precinct over from the hand-typed lat/lon — both inside
the city; precinct is informational only and does not affect the in/out answer.)

## Dependencies
`geopandas`, `shapely` (point-in-polygon); `curl` (Census geocoder). Geocoding needs
internet; `--latlon` lookups are fully offline.

## Don't
- **Don't fabricate a district map.** Lehi has none — it is at-large.
- Don't treat `precincts.geojson` as a district layer — it is for joining
  election-by-precinct data only.
- Don't filter the precinct layer by `AliasName` for Lehi (empty/unreliable) — use
  `CountyID=25 AND VistaID LIKE '25LE%'`. The city polygon filters fine by `NAME='LEHI'`.
