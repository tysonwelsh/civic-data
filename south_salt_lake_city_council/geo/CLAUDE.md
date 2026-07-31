# Geo — South Salt Lake address/point → council district

Maps a South Salt Lake, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **South Salt Lake's OWN official ArcGIS district polygons** ("South
Salt Lake City Council Districts") — the authoritative, whole-city boundary layer. Modeled
on `south_jordan_city_council/geo/` (same county; Salt Lake County, UGRC CountyID = 18).
**As-of: 2026-07-12.**

## South Salt Lake council structure (important for interpretation)

South Salt Lake uses a **SEVEN-member council form: 5 geographic districts (1–5) + 2
AT-LARGE seats**, plus a separately-elected executive **Mayor** (Cherie Wood, non-voting on
council). Every resident is represented by **four** elected officials: their **District**
councilmember **plus both At-Large** members **plus** the city-wide Mayor.

This tool resolves only the geographic **District seat (1–5)**. The **2 At-Large seats and
the Mayor are city-wide (no polygon)** — they are returned as context (`at_large`, `mayor`
fields; the CLI prints a reminder) but are **not** point-resolved.

Current district members (from the 2026-06-10 council-minutes header / `sslc.gov/160/City-Council`;
embedded in `address_to_district.py::COUNCIL_MEMBERS`, update after each election/appointment):
District 1 = **Joy Glad** · District 2 = **Corey Thomas** · District 3 = **Sharla Bynum**
(Council Chair) · District 4 = **Nick Mitchell** · District 5 = **Irvin Jones**. City-wide:
At-Large = **Ray deWolfe** & **Clarissa Williams**; Mayor = **Cherie Wood**.
(⚠ D1 Glad and D5 Jones are the 2026 *serving* members via mid-term appointment — the
*elected* 2023 winners were Huff (D1) and Sanchez (D5); see `../election_results/CLAUDE.md`.)

## Files
```
districts.geojson          South Salt Lake's 5 official council-district polygons, EPSG:4326
                           (field "CITY_COUNC" = 1..5, "LABEL" = "South Salt Lake Dist #N")
precincts.geojson          21 South Salt Lake (SSL-prefixed) SLCo precincts, EPSG:4326
precinct_to_district.csv   precinct -> district (1–5); 21 rows, from the district election
                           contests (method=district_election_contest), 0 splits
address_to_district.py     CLI + importable module: address/point -> district 1-5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`
   (`CITY_COUNC` = 1..5); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, at_large, mayor, lat,
lon}`; `district_for_address(address)` adds `matched_address`. Points outside South Salt
Lake → district None. The address tool does **not** use `precinct_to_district.csv` — the
official district layer is authoritative and whole-city, so the lookup is a direct
point-in-polygon against the **district** outlines. The precinct table is a join aid for
by-precinct election data.

## Data sources

### City council-district polygons (authoritative, PRIMARY source used)
South Salt Lake's **official ArcGIS FeatureServer**, layer **2**:
`https://services5.arcgis.com/3nLdZUaMqOeKxP26/arcgis/rest/services/Council_Districts/FeatureServer/2`
- Fetched via Query → geojson: `…/FeatureServer/2/query?where=1=1&outFields=*&f=geojson`
  (browser-UA; returned all **5** polygons, HTTP 200, 2026-07-12).
- Fields: **`CITY_COUNC`** (= 1..5, the district number) + `LABEL` ("South Salt Lake Dist
  #N"). **No member-name field** — member names live in the resolver's `COUNCIL_MEMBERS` /
  `AT_LARGE` / `MAYOR` maps.
- Source ArcGIS app `appid=94faefd2f4f34fb3ab067c2583ab61ec` → webmap
  `44d87811f82449c1830afc85a34fe8c8` (item "South Salt Lake City Council Districts").
- **CRS:** the geojson query returns true Utah lon/lat (WGS84); geopandas reads it as
  EPSG:4326 and point-in-polygon against Census lat/long works directly. Districts are
  post-2020-census; treat as **current** vintage (pre-2022 address→district questions may
  need older lines — not published by the city).

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — South Salt
Lake elections are county-run), filtered to the **21 `SSL`-prefixed** precincts, fetched
with `outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
(1,008 SLCo features → filtered to the 21 `SSL###`, incl. the `SSL901` mail/special
precinct).

**precinct → district method (`precinct_to_district.csv`):** built from the **district
(1–5) general-election contests** — each precinct is assigned the district whose ballot it
voted (most-recent general per district: D1/D4/D5 from 2023, D2/D3 from 2025). This is the
**election-authoritative** mapping the task specified. **Cross-checked geometrically**
against the official district polygons (each precinct's `representative_point()` tested for
containment): **all 21 precincts AGREE, 0 disagreements, 0 no-hits.** Counts: **D1=4, D2=4,
D3=6, D4=3, D5=4** (21 total). The two At-Large seats are citywide — no precinct→At-Large
mapping (every precinct votes both At-Large seats).

## Usage
```
python3 address_to_district.py "220 E Morris Ave, South Salt Lake, UT 84115"
python3 address_to_district.py --latlon "40.7089 -111.8883"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| 220 E Morris Ave (South Salt Lake City Hall) | **District 1 (Joy Glad)** + city-wide At-Large (deWolfe, Williams) + Mayor Wood |
| 451 S State St, Salt Lake City (control) | outside South Salt Lake → **None** |
| all 5 district interior rep-points (offline) | each resolves to **its own** district 1–5 |

## Caveats
- **The 2 At-Large members and the Mayor are city-wide** — no district mapping; returned as
  context only, never point-resolved. This is the key difference from South Jordan (which
  has no at-large seats).
- **Boundaries are South Salt Lake only** — points outside the city return district None.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare
  numbers; pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **Member names are hand-maintained** in `COUNCIL_MEMBERS` / `AT_LARGE` / `MAYOR` (the GIS
  layer has no member field); update after each election/appointment. Note the 2026
  serving-vs-elected D1/D5 appointment nuance above.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
