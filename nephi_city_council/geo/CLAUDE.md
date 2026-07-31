# geo/ — Nephi, Utah

## TL;DR: there are NO council districts

Nephi City Council is **entirely at-large**. The body is **Mayor + 5 councilmembers**, all
elected **citywide** (standard small-Utah-city form; confirmed at-large by the Nov 2025
ballot wording "2 seats at large"). **There are 0 wards / districts.**

Because every in-city address is represented by the **same six officials**, the usual
*address → council district* lookup is **degenerate / identity**. There is nothing to map.
The only geographically meaningful question is:

> **Is this address inside the Nephi city limits?**

So `address_to_district.py` is really an **in-city-limits check**. If a point is inside the
city, it is represented by all 5 at-large councilmembers + the Mayor; if it is outside, it
has no Nephi representation.

`precinct → district` mapping is therefore **N/A (degenerate)**: every Nephi precinct elects
the same citywide slate, so a precinct→district table would be a single constant. We do not
build one and you should not fabricate one.

## Files

| File | What it is |
|---|---|
| `city_boundary.geojson` | Nephi **city-limits polygon** (1 feature). The boundary the address tool tests against. |
| `precincts.geojson` | The **5** in-city voter ballot areas that overlap Nephi (`12NE3:I`, `12NE4:I`, `12NE5:I`, `12NE6:I`, `12NE7`, subset of Juab County). **Informational only** — used for joining by-precinct election data, NOT for district assignment. |
| `address_to_district.py` | Address (or lat/long) → **inside / outside** Nephi city limits, plus the overlapping precinct for context. |

## Data sources

### City limits (`city_boundary.geojson`)
- **Source:** UGRC SGID **Utah Municipal Boundaries** FeatureServer (authoritative statewide
  municipalities layer):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- **Query used:** `/query?where=NAME='NEPHI'&outFields=NAME,COUNTYNBR,FIPS,POPLASTCENSUS&outSR=4326&f=geojson`
- Returns **exactly 1** polygon: `NAME="Nephi"`, `COUNTYNBR="12"` (**Juab County**),
  `FIPS="54220"`, `POPLASTCENSUS=6443`. (`NAME='NEPHI'` matches case-insensitively and
  uniquely — no neighboring-city look-alikes returned.)
- Bounds ≈ lon `-111.865 … -111.800`, lat `39.661 … 39.734`.

### Precincts (`precincts.geojson`) — secondary
- **Source:** UGRC **VistaBallotAreas** FeatureServer (statewide voting precincts):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **Query used:** `?where=CountyID=12&outFields=*&outSR=4326&f=geojson`
  (**Juab County = CountyID 12** — there is no county-name field, use the numeric ID).
  Juab returns **30** ballot-area features.
- **Selection by spatial intersect** against the Nephi city polygon (AliasName is blank
  `" "` for every Juab precinct → name matching is impossible), keeping features with
  **>50%** of their area inside the city → **5** precincts: `12NE3:I`, `12NE4:I`, `12NE5:I`,
  `12NE6:I`, `12NE7` (each ~99.9% inside).
- **Naming:** `12` = CountyID (Juab), `NE` = Nephi, `#` = precinct number; the `:I` suffix =
  the **In-city / incorporated** sub-area, `:U…` = the unincorporated remainder (outside the
  city). Precincts `12NE1` and `12NE2` are far-west **rural** Nephi-named precincts
  (centroids ≈ -112.4 / -112.7 lon) that lie **outside** the city limits and so are excluded.
  The `:U` (unincorporated) portions of NE3–NE6 are likewise outside the city and excluded.

## CRS note (important)

All GeoJSON here is **EPSG:4326 (lon/lat)**. The UGRC features were requested with
**`outSR=4326`** and verified: sample coords look like Utah lon/lat (≈ `-111.83, 39.71`),
**NOT UTM(26912) meters** (the WVC / `slco-election-archive` GeoJSON was mislabeled
UTM-as-4326 and broke point-in-polygon — that trap is avoided here). `address_to_district.py`
still defensively `set_crs(4326)` if missing and `to_crs("EPSG:4326")` before any
point-in-polygon test.

## Using the tool

```bash
# Address (needs internet for the free Census geocoder)
python3 address_to_district.py "21 E 100 N, Nephi, UT 84648"
#   -> INSIDE Nephi city limits (precinct 12NE4:I)
#   -> represented by at-large (Mayor + 5 citywide councilmembers — no districts)

# lat/long (fully offline — no network needed)
python3 address_to_district.py --latlon 39.7106 -111.8345

# Batch: one address per line
python3 address_to_district.py --batch addresses.txt
```

As a module:
```python
from address_to_district import district_for_address, district_for_point
district_for_address("21 E 100 N, Nephi, UT 84648")
# {"in_city": True, "district": None, "council": "at-large ...",
#  "precinct": "12NE4:I", "matched_address": "...", "lat":..., "lon":...}
```

The return dict keeps a `district` key (always `None`) for API parity with the SLC /
St. George tools, but **`in_city` is the field that matters**.

### Verified test points
| Input | Result |
|---|---|
| `21 E 100 N, Nephi, UT 84648` (City Hall) | **INSIDE** (precinct `12NE4:I`) |
| `--latlon 39.7106 -111.8345` (offline, City Hall area) | **INSIDE** (precinct `12NE4:I`) |
| `445 W Center St, Provo, UT 84601` (Provo City Hall) | **OUTSIDE** |
| `--latlon 40.7608 -111.8910` (offline, SLC) | **OUTSIDE** |

## Dependencies
`geopandas`, `shapely` (point-in-polygon); `curl` (Census geocoder). Geocoding needs
internet; `--latlon` lookups are fully offline.

## Don't
- **Don't fabricate a district map.** Nephi has none — it is at-large.
- Don't treat `precincts.geojson` as a district layer — it is for joining
  election-by-precinct data only.
- Don't include `12NE1`/`12NE2` or the `:U` sub-areas as Nephi precincts — they are the
  rural / unincorporated parts of Juab County outside the city limits.
