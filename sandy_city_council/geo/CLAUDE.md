# Geo — Sandy address/point → council district

Maps a Sandy, Utah address (or lat/long) to its City Council **district (1–4)** by
point-in-polygon against **Sandy's own city GIS district polygons** — the authoritative,
whole-city boundary layer. Ported from `slc_city_council/geo/` and its same-county sibling
`west_jordan_city_council/geo/` (Salt Lake County, UGRC CountyID = 18).

## Sandy council structure (important for interpretation)
Sandy has a **7-member council: 4 district seats + 3 at-large seats**, plus a separately
elected **Mayor** (Monica Zoltanski; Council–Mayor strong-mayor form — the Mayor does NOT
vote on the council). Every resident is represented by **five** elected officials: their
District councilmember, **all three** At-Large councilmembers, and the Mayor.

This tool resolves only the **District seat (1–4)**. The three At-Large members and the
Mayor are **city-wide** — they have no district and are not returned (the CLI prints a
reminder that they cover everyone).

Current district members (from the city GIS layer, matches the 2026-06-02 minutes):
District 1 = Brooke Christensen · District 2 = Alison Stroud · District 3 = Kris Nicholl ·
District 4 = Marci Houseman. (At-large: Aaron Dekeyzer, Brooke D'Sousa, Cyndi Sharkey/Chair.)

## Files
```
council_districts.geojson   Sandy's authoritative 4 council-district polygons, true EPSG:4326
precincts.geojson           110 Sandy (SAN-prefixed) SLCo precincts, true EPSG:4326 (informational)
address_to_district.py      CLI + importable module: address/point -> district 1-4
```
There is **no** `precinct_to_district.csv` — unlike the precinct-based WJ/WVC ports, Sandy's
city layer is authoritative and covers the whole city, so the lookup is a direct
point-in-polygon against the **district** outlines. `precincts.geojson` is kept only as a
join aid for future by-precinct election data (none exists yet at build time).

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `council_districts.geojson`
   (`Name` = "District 1".."District 4"); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside Sandy → district None.

## Data source

### City council-district polygons (authoritative)
Sandy's **own city GIS** MapServer:
`https://gis.sandy.utah.gov/arcgis/rest/services/Common/City_Council_Districts/MapServer`
- **Layer 0 = "Districts"** (polygon). Fields: `OBJECTID`, `City_Counc` (= "1".."4"),
  **`Name`** (= "District 1".."District 4"), `Council_Member`, `Link_to_Photo`, `Link_To_Bio`.
- Layer 1 = "At-large" (the at-large coverage area; not used here — it's city-wide).
- Exported via the Query endpoint:
  `…/City_Council_Districts/MapServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`
- It is a **MapServer** (not a FeatureServer) but exposes Query → geojson export works.

### CRS note (the gotcha) — SRID 102743 → 4326
The service's native spatial reference is **WKID 102743** (`latestWkid` 3566, a
Utah-specific NAD83 state-plane variant in **US survey feet**, falseX/falseY ≈ −1.2e8).
Raw geometry would come back as projected feet, NOT lon/lat. The query was issued with
**`outSR=4326`**, and the result was verified to be true Utah lon/lat: sample coord
`-111.911, 40.594`, full bounds ≈ `[-111.922, 40.528, -111.777, 40.618]` (Sandy is around
−111.88, 40.57). geopandas reads the file as EPSG:4326 and point-in-polygon against Census
lat/long works directly. If you refetch, keep `outSR=4326` and re-verify the coords look
like Utah lon/lat, not feet.

### Precincts (informational)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — Sandy
elections are county-run), filtered to the **110 `SAN`-prefixed** Sandy precincts, fetched
with `outSR=4326` (verified true lon/lat, bounds match the district layer). Service:
`https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,VersionNbr&outSR=4326&f=geojson`
Kept for joining future by-precinct election results (`election_results/sandy_results_by_precinct.csv`,
not present at build time); not used by the address tool.

## Usage
```
python3 address_to_district.py "10000 Centennial Pkwy, Sandy, UT 84070"
python3 address_to_district.py --latlon "40.5689 -111.8958"     # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests
| Input | Result |
|---|---|
| 10000 Centennial Pkwy (City Hall) | District 1 (Brooke Christensen) |
| 8200 S 1000 E | District 2 (Alison Stroud) |
| 9000 S 2000 E | District 3 (Kris Nicholl) |
| rep-point 40.55368, −111.82943 (offline) | District 4 (Marci Houseman) |
| 451 S State St, Salt Lake City (control) | outside Sandy → None |

All four district interior points (`geometry.representative_point()`) resolve to their own
district, confirming point-in-polygon for D1–D4.

## Caveats
- **At-large (3 seats) + Mayor are city-wide** — no district mapping; never returned. The
  Mayor is executive and does not vote on the council (Council–Mayor form).
- **Boundaries are Sandy only** — points outside the city return district None.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare
  numbers; pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **CRS:** see the SRID 102743 → 4326 note above. Always refetch with `outSR=4326`.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
- The Census geocoder fails to match some valid Sandy addresses (returns "no geocode
  match"); supply `--latlon` directly when that happens.
