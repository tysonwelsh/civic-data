# Geo — Herriman address/point → council district

Maps a Herriman, Utah address (or lat/long) to its City Council **district (1–4)** by
point-in-polygon against **Herriman's OWN official city GIS district polygons**
("HerrimanDistricts", owner HCPublicWorks) — the authoritative, whole-city boundary layer.
Modeled on `south_jordan_city_council/geo/` (same county; UGRC precinct source).
**As-of: 2026-07-11.**

## Herriman council structure (important for interpretation)

Herriman uses a **Council–Mayor** form: **4 district council seats (Districts 1–4)** plus a
separately-elected **Mayor** (Lorin Palmer). There are **no at-large council seats** in the
modern (2020+) record — the Mayor is the only city-wide elected official, **presides** over
the council, and does **not** cast an ordinary roll-call vote (max council tally = 4). Every
resident is represented by **two** elected officials: their District councilmember and the
city-wide Mayor.

This tool resolves only the **District seat (1–4)**. The Mayor is city-wide (no district)
and is not returned (the CLI prints a reminder).

Current district members (from `herriman.gov/city-council` + the post-2025-election roster;
embedded in `address_to_district.py::COUNCIL_MEMBERS`, **update after each election**):
District 1 = **Jared Henderson** · District 2 = **Teddy Hodges** · District 3 = **Matt
Basham** · District 4 = **Terrah Anderson** (2025 special, 2-year term). Mayor (city-wide):
**Lorin Palmer**.

## Files
```
districts.geojson         Herriman's OFFICIAL 4 council-district polygons (EPSG:4326;
                          field "District" = 1..4, "Label" = "District N")
precincts.geojson         44 HER-prefixed SLCo precincts (UGRC VistaBallotAreas), EPSG:4326
precinct_to_district.csv  precinct -> district (1–4); 44 rows, 0 splits, 0 vote mismatches
address_to_district.py    CLI + importable module: address/point -> district 1-4
build_geo.py              reproducible builder (filters precincts, centroid-in-district,
                          QA cross-check); refetch commands documented in its header
_slco_precincts.geojson   intermediate: the full CountyID=18 VistaBallotAreas pull
                          (build_geo.py filters HER out of this)
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`
   (`District` = 1..4); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside Herriman → district
None. The address tool does **not** use `precinct_to_district.csv` — the official district
layer is authoritative and whole-city, so the lookup is a direct point-in-polygon against
the **district** outlines. The precinct table is a join aid for by-precinct election data.

## Data sources

### Council-district polygons (OFFICIAL, authoritative — PRIMARY source)
Herriman City's **own ArcGIS** (owner **HCPublicWorks**), FeatureLayer **HerrimanDistricts**
(item `f59497536e834761b5c376db68a47134`):
```
https://services2.arcgis.com/XBmqwOHlPh25M7aJ/arcgis/rest/services/HerrimanDistricts/FeatureServer/0
```
- Fetched via Query → geojson with `outSR=4326`
  (`.../0/query?where=1=1&outFields=*&outSR=4326&f=geojson`).
- **Exactly 4 polygons**; fields incl. `District` (integer 1–4) and `Label` ("District N").
  **No member-name field** — member names live in the resolver's `COUNCIL_MEMBERS` map.
- Used **directly** (no precinct-dissolve fallback was needed — the FeatureServer hunt
  succeeded immediately with the recon's endpoint).

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, internal **`CountyID = 18`** (Salt Lake County —
Herriman elections are county-run). **County-key reconciliation:** the task-level Salt Lake
FIPS is **49035**, but the UGRC VistaBallotAreas service keys county by an **internal id**,
which is **18** for Salt Lake — matched to the sibling `south_jordan`/`sandy` builds (a
`where=CountyID=49035` query returns nothing). Service:
```
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson
```
Returns **1,008** SLCo features statewide-county → filtered locally to the **44
`HER`-prefixed** Herriman precincts (`HER001`–`HER040` + special/mail `HER901`–`HER904`).

### City boundary (cross-reference, not shipped)
UGRC **Utah Municipal Boundaries** `NAME='HERRIMAN'`
(`services1.arcgis.com/99lidPhWCzftIe9K/.../UtahMunicipalBoundaries/FeatureServer/0`) —
used conceptually as a cross-check; the district layer already covers the whole city.

## Precinct → district method
Each precinct's representative interior point (`geometry.representative_point()`) is tested
for containment in a district polygon (`method=centroid_in_district`), QA'd by
largest-area-overlap fraction. **43/44 precincts** resolve cleanly to a district (all area
fractions > 0.99 → **no split precincts**). Counts: **D1=12, D2=9, D3=15, D4=8**.

**Cross-check against elections:** compared to which `DISTRICT-N` contest each precinct
actually voted in (2021+ `election_results/herriman_results_by_precinct.csv`) — **0
mismatches** across the 39 precincts with modern district votes. The geometric map agrees
with the ballots.

**HER904** is the lone precinct **outside every current district polygon** (a mail/special
sub-precinct); it cast ballots in the **District 1** contest, so it is assigned **D1** by
that electoral evidence (`method=electoral_only_outside_polygon`, `district_area_frac=0.0`).
`HER036–040` are newer precincts with no post-2021 district vote yet — mapped geometrically.

## Usage
```
python3 address_to_district.py "5355 W Herriman Main St, Herriman, UT 84096"
python3 address_to_district.py --latlon "40.5141 -112.0330"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-11)
| Input | Result |
|---|---|
| 5355 W Herriman Main St (City Hall) | **District 2 (Teddy Hodges)** |
| 451 S State St, Salt Lake City (control) | **outside Herriman → None** |
| D1 interior rep-point (offline) | District 1 (Jared Henderson) |
| D2 interior rep-point (offline) | District 2 (Teddy Hodges) |
| D3 interior rep-point (offline) | District 3 (Matt Basham) |
| D4 interior rep-point (offline) | District 4 (Terrah Anderson) |

All four district interior points resolve to their own district, confirming point-in-polygon
for D1–D4.

## Caveats / gaps
- **The Mayor is city-wide** — no district mapping; never returned. There are **no at-large
  council seats** in the modern record.
- **Boundaries are current / post-2020-census.** A **pre-2022** address near a moved district
  line may resolve to today's district, not the one in effect at an older election. The layer
  is authoritative for **present-day** lookups. (No prior-plan polygon set was published by
  the city; historical precinct→district for older cycles can be read from the by-precinct
  election contests instead.)
- **Member names are hand-maintained** in `COUNCIL_MEMBERS` (the GIS layer has no member
  field); update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
- **`--latlon` quoting:** longitude is negative → argparse mis-parses two bare numbers; pass
  the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **HER904** sits outside the official polygons (electoral-only assignment) — see above.
