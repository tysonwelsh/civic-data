# geo/ — Park City, Utah

## TL;DR: there are NO council districts

Park City Council is **entirely at-large**. The body is **Mayor + 5 council members**,
and **all five council seats are elected citywide — there are 0 wards / districts.**
Because every in-city address is represented by the **same six officials**, the usual
*address → council district* lookup is **degenerate / identity**. The only
geographically meaningful question is:

> **Is this address inside the Park City city limits?**

So `address_to_district.py` is really an **in-city-limits check**. Inside → represented
by all 5 at-large councilmembers + the Mayor; outside → no Park City representation.
This mirrors the Lehi / St. George / Vineyard at-large tools.

`precinct → district` mapping is therefore **N/A (degenerate)**: every Park City
precinct elects the same citywide slate. We do not build a precinct→district table and
you should not fabricate one.

## Files

| File | What it is |
|---|---|
| `city_boundary.geojson` | Park City **city-limits polygon** — **2 features** (see straddle note): the main Summit-County polygon + the small Wasatch-County piece. Together they are the full city limits the address tool tests against. |
| `precincts.geojson` | The **13** voter precincts (ballot areas) lying inside the Park City limits, a subset of Summit County's 82. **Informational only** — for joining by-precinct election data, NOT for district assignment. |
| `address_to_district.py` | Address (or lat/long) → **inside / outside** Park City limits, plus the overlapping precinct for context. |

## Data sources

### City limits (`city_boundary.geojson`)
- **Source:** UGRC SGID **Utah Municipal Boundaries** FeatureServer:
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- **Query used:**
  `/query?where=NAME='PARK CITY'&outFields=NAME,COUNTYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson`
- Returns **2** polygons, both `NAME="Park City"`, `FIPS="58070"`, `POPLASTCENSUS=8396`:
  one `COUNTYNBR="22"` (**Summit**, the main body) and one `COUNTYNBR="26"` (**Wasatch**,
  a small piece — see straddle note). **Both are kept** so the in/out test covers the
  entire city.
- Combined bounds ≈ lon `-111.559 … -111.436`, lat `40.599 … 40.703` (centered ≈
  `-111.50, 40.65` — verified the correct Park City polygon, not a look-alike).

### Summit / Wasatch straddle note
Park City is **administratively Summit County (CountyID 22)** — that is where its
elections are run and where its precincts live in UGRC VistaBallotAreas. But a small
slice of the city limits (Deer Valley South area) physically sits in **Wasatch County
(COUNTYNBR 26)**. The municipal-boundary layer splits the city into one polygon per
county; we keep **both** as the city limits. Tellingly, Summit County still administers
that slice as a Summit ballot area (`22DVS:30 "DEER VALLEY SOUTH WASATCH"`), so the
precinct layer remains entirely CountyID 22.

### Precincts (`precincts.geojson`) — secondary
- **Source:** UGRC **VistaBallotAreas** FeatureServer (statewide voting precincts):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **Query used:** `?where=CountyID=22&outFields=VistaID,PrecinctID,SubPrecinctID,AliasName,CountyID&outSR=4326&f=geojson`
  (**Summit County = CountyID 22** — there is no county-name field, use the numeric ID).
- That returns all **82** Summit ballot areas. Park City's precincts have **no single
  code prefix** (Park Meadows is `22PKMN/22PKMS`, Old Town `22OLDN/22OLDS`, Deer Valley
  `22DVN/22DVS`, plus `22PROS`, `22THAY`, `22SIDE`, `22QUAR`, `22FED:3`), so name/prefix
  filtering is unreliable. The **13 Park City precincts** were selected by **spatial
  intersection** with the city polygon (kept any ballot area ≥ ~99% inside):

  `22DVN:15` (Deer Valley North), `22DVS:25` (Deer Valley South),
  `22DVS:30` (Deer Valley South Wasatch), `22OLDN:15` (Old Town North),
  `22OLDS:25` (Old Town South), `22PKMN:15` (Park Meadows North),
  `22PKMS:25` (Park Meadows South), `22PROS:5` (Prospector),
  `22PROS:4` (Prospector 4), `22THAY:5` (Thaynes), `22SIDE:5` (Sidewinder),
  `22QUAR:5` (Quarry Mountain), `22FED:3` (Fed 3, a federal-land ballot area).

  The other 69 Summit ballot areas (Coalville, Kamas, Oakley, Henefer, Echo, Peoa,
  Promontory, Pinebrook, Summit Park, etc., plus rural sewer/school-district overlay
  sub-precincts) are outside the city and excluded.

## CRS note (important)

All GeoJSON here is **EPSG:4326 (lon/lat)** and **verified true 4326, not UTM**. The
UGRC features were requested with **`outSR=4326`**; sample precinct coords came back as
`(-111.49, 40.70)` and the city as `(-111.50, 40.65)` — Utah lon/lat, **NOT UTM 26912
meters**. This is the exact trap that bit the West Valley City build (UTM 26912
mislabeled as 4326 → every address fell outside all polygons). Here the coords are
genuinely 4326, so **no reprojection was needed**. `address_to_district.py` still
defensively `set_crs(4326)` if missing and `to_crs("EPSG:4326")` before any
point-in-polygon test. City and precinct bounds line up, confirming a shared CRS.

## Using the tool

```bash
# Address (needs internet for the free Census geocoder)
python3 address_to_district.py "445 Marsac Ave, Park City, UT 84060"
#   -> INSIDE Park City city limits (precinct 22DVS:25)
#   -> represented by at-large (Mayor + 5 citywide councilmembers — no districts)

# lat/long (fully offline — no network needed)
python3 address_to_district.py --latlon 40.6438 -111.4936

# Batch: one address per line
python3 address_to_district.py --batch addresses.txt
```

As a module:
```python
from address_to_district import district_for_address, district_for_point
district_for_address("445 Marsac Ave, Park City, UT 84060")
# {"in_city": True, "district": None, "council": "at-large ...",
#  "precinct": "22DVS:25", "matched_address": "...", "lat":..., "lon":...}
```

The return dict keeps a `district` key (always `None`) for API parity with the SLC /
Lehi / St. George tools, but **`in_city` is the field that matters**.

### Verified test points
| Input | Result |
|---|---|
| `445 Marsac Ave, Park City, UT 84060` (City Hall, Census geocode) | **INSIDE** (precinct `22DVS:25`) |
| `--latlon 40.6438 -111.4936` (offline, City Hall area) | **INSIDE** (precinct `22DVS:25`) |
| `451 S State St, Salt Lake City, UT 84111` (SLC City Hall) | **OUTSIDE** |
| `--latlon 40.5070 -111.4133` (offline, Heber City) | **OUTSIDE** |

(Precinct is informational only and does not affect the in/out answer.)

## Dependencies
`geopandas`, `shapely` (point-in-polygon); `curl` (Census geocoder). Geocoding needs
internet; `--latlon` lookups are fully offline.

## Don't
- **Don't fabricate a district map.** Park City has none — it is at-large.
- Don't treat `precincts.geojson` as a district layer — it is for joining
  election-by-precinct data only.
- Don't drop the Wasatch (`COUNTYNBR=26`) polygon from `city_boundary.geojson` — it is
  part of the real city limits even though Park City is administratively Summit.
- Don't filter precincts by a code prefix (there is no single Park City prefix) — select
  by spatial intersection with the city polygon, on `CountyID=22`.
