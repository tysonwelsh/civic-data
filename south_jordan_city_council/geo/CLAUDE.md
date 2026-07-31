# Geo — South Jordan address/point → council district

Maps a South Jordan, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **South Jordan's own city GIS district polygons** ("Council
Districts 2020") — the authoritative, whole-city boundary layer. Ported from
`sandy_city_council/geo/` (same county, same UGRC precinct source; Salt Lake County,
UGRC CountyID = 18). **As-of: 2026-07-06.**

## South Jordan council structure (important for interpretation)
South Jordan uses a **six-member council form: 5 district seats (Districts 1–5)** plus a
separately-elected **Mayor** (Dawn R. Ramsey). There are **no at-large council seats** —
the Mayor is the only city-wide elected official. Every resident is represented by **two**
elected officials: their District councilmember and the city-wide Mayor.

This tool resolves only the **District seat (1–5)**. The Mayor is city-wide (no district)
and is not returned (the CLI prints a reminder). Note the mayor-vote nuance flagged in the
city `recon.md` (statutory six-member form vs. observed 5-0 tallies) — that concerns vote
extraction, not geography, and does not affect this tool.

Current district members (from the 2025-03-18 council-minutes header /
`sjc.utah.gov/241/City-Council`; embedded in `address_to_district.py::COUNCIL_MEMBERS`,
update after each election):
District 1 = Patrick Harris · District 2 = Kathie L. Johnson · District 3 = Don Shelton ·
District 4 = Tamara Zander · District 5 = Jason T. McGuire. (Mayor, city-wide: Dawn R. Ramsey.)

## Files
```
council_districts.geojson   South Jordan's 5 council-district polygons, true EPSG:4326
                            (field "District" = "1".."5"; from the city "Council Districts 2020" layer)
precincts.geojson           68 South Jordan (SJD-prefixed) SLCo precincts, true EPSG:4326
precinct_to_district.csv    precinct -> district (1–5), centroid-in-district; 68 rows, 0 splits
address_to_district.py      CLI + importable module: address/point -> district 1-5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `council_districts.geojson`
   (`District` = "1".."5"); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside South Jordan →
district None. The address tool does **not** use `precinct_to_district.csv` — the city
district layer is authoritative and whole-city, so the lookup is a direct point-in-polygon
against the **district** outlines. The precinct table is a join aid for future by-precinct
election data.

## Data sources

### City council-district polygons (authoritative, PRIMARY source used)
South Jordan's **own city GIS** ArcGIS Server, layer **2 = "Council Districts 2020"**:
`https://gis2.southjordanutah.gov/server/rest/services/Voting/Voting/MapServer/2`
- Fetched via Query → geojson with `outSR=4326`:
  `…/MapServer/2/query?where=1=1&outFields=*&outSR=4326&f=geojson`
- 5 polygons; fields incl. `OBJECTID`, **`District`** (= "1".."5"), `STATEFP20`=49,
  `COUNTYFP20`=035 (Salt Lake), `Acres`. **No member-name field** on the layer — member
  names are attached in the resolver's `COUNCIL_MEMBERS` map (see above).
- **The `recon.md`-flagged intermittent-DNS issue did NOT materialize** in this build —
  the `gis2.southjordanutah.gov` REST endpoint responded 200 with valid GeoJSON on the
  first request. The **PRIMARY** (direct city) layer was used; the ArcGIS Online mirror
  webmap `8747ca4ab86e4632a6966fd40cd2ed19` was **not needed** (documented fallback if the
  host flaps on a refetch).

### CRS note
The layer's native SR is **wkid 103170 / latestWkid 6625** (NAD83 Utah Central, ftUS).
The query was issued with **`outSR=4326`** and the result verified to be true Utah lon/lat
(bounds ≈ `[-112.095, 40.520, -111.895, 40.582]`, South Jordan is around −111.96, 40.55).
geopandas reads the file as EPSG:4326 and point-in-polygon against Census lat/long works
directly. If you refetch, keep `outSR=4326` and re-verify coords look like Utah lon/lat.

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — South
Jordan elections are county-run), filtered to the **68 `SJD`-prefixed** South Jordan
precincts, fetched with `outSR=4326`. Service (canonical, per gis.utah.gov):
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
(1008 SLCo features statewide-county → filtered to the 68 intersecting the district layer;
`query` endpoint returned intermittent 400 "Invalid URL"/"Bad Request" on 2–3 early calls
but succeeded on retry — the flakiness noted in `recon.md` is on the UGRC host, not just
the city host).

**Precinct→district method:** each South Jordan precinct's representative interior point
was tested for containment in a district polygon (`method=centroid_in_district`).
Cross-checked against majority-area overlap — **the two methods agree on all 68 precincts**,
and every precinct's largest-district area fraction is **> 0.97** (min 0.971), so there are
**no split precincts** (`split=no` for all rows). Precinct→district counts:
D1=14, D2=15, D3=12, D4=16, D5=11 (68 total). SJD901/902/903 (likely mail/special
precincts) resolve cleanly to D3/D4/D4 respectively.

## Usage
```
python3 address_to_district.py "1600 W Towne Center Dr, South Jordan, UT 84095"
python3 address_to_district.py --latlon "40.5622 -111.9297"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-06)
| Input | Result |
|---|---|
| 1600 W Towne Center Dr (City Hall) | District 2 (Kathie L. Johnson) |
| 4646 W Daybreak Pkwy | District 4 (Tamara Zander) |
| 2929 W 10400 S | District 2 (Kathie L. Johnson) |
| rep-point 40.545, −111.995 (offline) | District 4 (Tamara Zander) |
| 451 S State St, Salt Lake City (control) | outside South Jordan → None |

All five district interior points (`geometry.representative_point()`) resolve to their own
district, confirming point-in-polygon for D1–D5.

## Caveats
- **The Mayor is city-wide** — no district mapping; never returned. (Six-member council
  form; see the mayor-vote nuance in the city `recon.md`, which affects vote extraction,
  not this tool.) There are **no at-large council seats**.
- **Boundaries are South Jordan only** — points outside the city return district None.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare
  numbers; pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **CRS:** see the wkid 6625 → 4326 note above. Always refetch with `outSR=4326`.
- **Member names are hand-maintained** in `COUNCIL_MEMBERS` (the GIS layer has no member
  field); update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
  The Census geocoder fails to match some valid South Jordan addresses (e.g. newer
  Daybreak streets) — supply `--latlon` directly when that happens.
