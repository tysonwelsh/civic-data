# Geo — White City address/point → council representation (ALL AT-LARGE)

Maps a White City, Utah address (or lat/long) to its City Council representation by
point-in-polygon against **White City's municipal boundary**. White City has **NO council
districts** — the whole city elects **one at-large body** (a directly-elected Mayor + 4
at-large council seats A–D since the 2024 HB35 city conversion; before that, a 5-member
all-at-large metro-township council whose Chair held the "Mayor" title and voted as a
member). So there is no sub-city district geography: the answer for **every** resident is
**At-Large** (in White City) or **None** (outside). Modeled on
`south_jordan_city_council/geo/` (same county; Salt Lake County, UGRC CountyID = 18).
**As-of: 2026-07-12.**

## White City structure (important for interpretation)
Every White City resident is represented by the **same** at-large body — there is no
per-address district. Current representatives (from `whitecity.utah.gov/city-council` +
the 2026 minutes headers; embedded in `address_to_district.py::AT_LARGE_REPRESENTATIVES`,
update after each election):

- **Mayor Allan Perry** (voting; elected 2025) · **Seat A** Greg Shelton (2023) ·
  **Seat B** Linda Price (2025) · **Seat C** Neil Mahoney, Mayor Pro-Tem (2025) ·
  **Seat D** Tyler Huish (2023).

(Metro-township era 2017–2024: a 5-member all-at-large council; Chair **Paulina Flint**
carried the "Mayor" title and voted as a member. The mayor **votes** in both eras.)

## Files
```
city_boundary.geojson       White City municipal boundary, 1 polygon, true EPSG:4326
                            (UGRC UtahMunicipalBoundaries, NAME='WHITE CITY', COUNTYNBR=18)
precincts.geojson           6 White City (WHT-prefixed) SLCo precincts, true EPSG:4326
precinct_to_district.csv    every WHT precinct -> "At-Large" (there are no districts)
address_to_district.py      CLI + importable module: address/point -> in White City + At-Large
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → representation** by point-in-polygon against `city_boundary.geojson`:
   inside → `district="At-Large"` + the full representative list; outside → `None`.
   Fully offline for `--latlon`.

`district_for_point(lon, lat)` returns `{district, in_white_city, representatives, lat,
lon}`; `district_for_address` adds `matched_address`. There is **no** district split —
`precinct_to_district.csv` maps all six precincts to `At-Large` (a join aid for
by-precinct election data, not used by the address tool).

## Data sources

### Municipal boundary (authoritative, PRIMARY)
UGRC **Utah Municipal Boundaries** FeatureServer (canonical per gis.utah.gov), White City
now an incorporated city (2024):
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME='WHITE CITY'&outFields=*&outSR=4326&f=geojson`
- **1 polygon**; fields incl. `NAME`="White City", `COUNTYNBR`="18" (Salt Lake),
  `SHORTDESC`="WHITE CITY", `FIPS`="84050". Bounds ≈ `[-111.872, 40.556, -111.853, 40.582]`
  (a small footprint SE of Sandy). Fetched with browser UA + `outSR=4326`.

### Precincts (informational + precinct→"district" join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18**, filtered to the White City
precincts:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18 AND PrecinctID LIKE 'WHT%'&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
- **6 precincts: WHT001–WHT006.** All six representative-points fall inside the municipal
  boundary (verified). **The election data (2019–2025) used WHT001–WHT004**; WHT005/WHT006
  are a later precinct split of the same footprint — all six map to the same At-Large body.

### CRS note
Both layers fetched with **`outSR=4326`** and verified to be true Utah lon/lat
(≈ −111.86, 40.567). geopandas reads the files as EPSG:4326 and point-in-polygon against
Census lat/long works directly. If you refetch, keep `outSR=4326` and re-verify.

## Usage
```
python3 address_to_district.py "999 E Galena Dr, Sandy, UT 84094"
python3 address_to_district.py --latlon "40.5688 -111.8615"     # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| 999 E Galena Dr, Sandy UT 84094 (WC meeting venue) | White City → At-Large (Mayor Perry + Seats A–D) |
| interior rep-point 40.5688, −111.8615 (offline) | White City → At-Large |
| 40.759, −111.888 (451 S State St, SLC — control) | outside White City → None |

## Caveats
- **No council districts — all At-Large.** The whole city elects one Mayor + 4 at-large
  seats; there is no per-address district to return. This is by design (not a missing
  layer). The **mayor votes** on every roll call in both the township and city eras.
- **⚠ Address caveat:** the meeting venue **999 E Galena Dr** and the city admin mailing
  address **860 W Levoy Dr, Taylorsville** are shared-services artifacts (the water-district
  building and the Greater SL MSD office) — not governance/geography facts. The mapping
  above is by boundary polygon only.
- **Boundaries are White City only** — points outside return `None`.
- **`--latlon` quoting:** longitude is negative; pass the pair as one quoted token
  (`--latlon "LAT -LON"`, comma also accepted).
- **Member names are hand-maintained** in `AT_LARGE_REPRESENTATIVES` (the GIS layer has no
  member field); update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
  White City is small (~5,000 people) — the Census geocoder may miss some addresses; pass
  `--latlon` directly when that happens.
- **Do NOT confuse with the White City Water Improvement District** (a separate special
  district with its own elected board) — this tool is the city/township council only.
