# Geo — Bluffdale address/point → in-city? (AT-LARGE, two-county)

Bluffdale is an **AT-LARGE** city: a Mayor + **5 Council Members, ALL elected at-large**
(**no districts**). So there is **no council-district polygon layer and no
"which-district?" question** — every Bluffdale address is represented by the **same** six
officials. The only geographic question is **inside/outside the city**, which
`address_to_district.py` answers by point-in-polygon against the **municipal boundary**.
Bluffdale also **straddles two counties** (Salt Lake — populated; Utah — Camp Williams /
unpopulated). **As-of: 2026-07-12.**

## Bluffdale council structure (important for interpretation)
Six-member mayor–council form: **Mayor (citywide, presides, does NOT vote on ordinary
motions)** + **5 at-large Council Members**. There are **no districts and no ward seats** —
every resident is represented by all six. `address_to_district.py` therefore returns a
citywide roster (not a district), with `district = "At-Large"` for any in-city point and
`None` outside.

Current roster (2025 winners + continuing 2023 winners; embedded in
`address_to_district.py`, update after each election):
Mayor **Natalie Hall** · at-large: **Wendy Aston, Mackey Smith** (2026–2029) · **Steve
Austin, Alan Lord, Greg Wilding** (2024–2027). (Mackey Smith replaced Traci Crockett Jan 2026.)

## Files
```
city_boundary.geojson       Bluffdale municipal boundary, true EPSG:4326 — 2 polygons
                            (the Salt Lake + Utah county slices; unioned at load time).
                            From UGRC UtahMunicipalBoundaries, NAME='BLUFFDALE'.
precincts.geojson           15 Bluffdale voting precincts, true EPSG:4326: 13 Salt Lake
                            (BLF001–BLF013) + 2 Utah County (25BL01 main, 25NW04 sliver).
                            From UGRC VistaBallotAreas, CountyID 18 + 25, clipped to the city.
precinct_to_district.csv    every precinct -> At-Large (there are no districts); carries
                            county / CountyID / intersect_frac (join aid for by-precinct data)
address_to_district.py      CLI + importable module: address/point -> in-Bluffdale? + roster
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → in-city?** by point-in-polygon against the unioned `city_boundary.geojson`
   (fully offline). In-city → `{in_bluffdale: True, district: "At-Large", mayor, council_at_large}`;
   outside → `in_bluffdale: False`.

`district_for_point(lon, lat)` is offline; `district_for_address(address)` adds
`matched_address`. `precinct_to_district.csv` is a by-precinct election-join aid — the
address tool does not need it (there are no districts to look up).

## Data sources

### City boundary (authoritative; the layer the tool resolves against)
UGRC **Utah Municipal Boundaries** FeatureServer, `NAME='BLUFFDALE'`, fetched with
`outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME='BLUFFDALE'&outFields=*&outSR=4326&f=geojson`
Returns **2 polygons** (the Salt Lake and Utah county slices of the city) — the resolver
**unions** them so a point in either county's slice tests as in-city. City bbox ≈
`[-111.992, 40.420, -111.899, 40.502]`.

### Precincts (informational + by-precinct join aid), TWO counties
UGRC **VistaBallotAreas** FeatureServer, queried by **envelope over the city bbox** for
**CountyID = 18 (Salt Lake)** and **CountyID = 25 (Utah)**, then clipped to precincts whose
area overlaps the boundary (`intersect_frac > 0.02`), `outSR=4326`:
`…/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&geometry=<bbox>&geometryType=esriGeometryEnvelope&spatialRel=esriSpatialRelIntersects&outFields=PrecinctID,VistaID,CountyID,AliasName,SubPrecinctID,VersionNbr&outSR=4326&f=geojson`
- **13 Salt Lake precincts** `BLF001–BLF013` (all ≥98% inside; these carry Bluffdale's
  voters and match the SOVC precinct IDs used in `election_results/`).
- **2 Utah County precincts**: **`25BL01`** (98.6% inside — the Utah-county Bluffdale slice)
  and **`25NW04`** (a 2.7% sliver — Camp Williams edge). Per `recon.md` the Utah-county
  extent is essentially **unpopulated** (Camp Williams), so these carry ~no voters; they are
  retained to represent the full municipal footprint honestly. Salt Lake County administers
  all Bluffdale elections.

### CRS note
Both layers were requested with **`outSR=4326`** and verified as true Utah lon/lat (Bluffdale
≈ −111.94, 40.49). geopandas reads the files as EPSG:4326 and point-in-polygon against Census
lat/long works directly. If you refetch, keep `outSR=4326` and re-verify coords.

## Usage
```
python3 address_to_district.py "2222 W 14400 S, Bluffdale, UT 84065"
python3 address_to_district.py --latlon "40.4890 -111.9390"   # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| 2222 W 14400 S (Bluffdale City Hall), geocoded | **in Bluffdale** → At-Large (Mayor Hall + 5 at-large) |
| `--latlon 40.4890 -111.9390` (City Hall, offline) | **in Bluffdale** → At-Large |
| `--latlon 40.7608 -111.8910` (SLC control) | **outside** Bluffdale |
| 451 S State St, Salt Lake City (control) | **outside** Bluffdale |

## Caveats
- **At-large city — no districts.** `district` is always `"At-Large"` in-city (or `None`
  outside); there is no ward/district geometry. Every address maps to the same Mayor + 5
  at-large Council Members.
- **The Mayor presides but does NOT vote** on ordinary motions (six-member form) — a
  vote-extraction nuance, not a geography one; the roster is returned for completeness.
- **Two counties:** the boundary spans Salt Lake + Utah counties; the resolver unions both
  slices. The Utah-county portion is Camp Williams / unpopulated.
- **Boundaries are Bluffdale only** — points outside return `in_bluffdale: False`.
- **`--latlon` quoting:** longitude is negative, so pass the pair as one quoted token
  (`--latlon "LAT -LON"`, comma also accepted).
- **Member names are hand-maintained** in `address_to_district.py` (the boundary layer has no
  member field); update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
