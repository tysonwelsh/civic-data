# Geo — Taylorsville address/point → council district

Maps a Taylorsville, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **precinct-derived** district polygons. **As-of: 2026-07-06.**

## No official district layer — polygons are PRECINCT-DERIVED
Taylorsville publishes **no council-district GIS FeatureServer** (recon.md §6 — the one
Taylorsville ArcGIS item found is a retail/demographic map, not districts; the legal lines
live only textually in municipal code 13.04.100). So the 5 district polygons in
`council_districts.geojson` were **derived**, not downloaded:

1. Take Salt Lake County precincts (**UGRC VistaBallotAreas, CountyID=18**), filtered to
   the **44 `TAY`-prefixed** Taylorsville precincts → `precincts.geojson`.
2. Assign each precinct to a district using the **district-contest precinct rows** in the
   shared SL County election archive: each `… COUNCIL DISTRICT N` contest lists exactly the
   precincts that voted in it, so contest-precincts == district-precincts.
3. **Dissolve** (union) the precincts by district → the 5 district polygons.

These follow **precinct lines**, which approximate but do not exactly equal the legal
district boundaries. Treat near-boundary results as approximate. This is a best-effort
derived layer, **not an authoritative city layer** (contrast South Jordan / Sandy, which
had their own "Council Districts 2020" GIS).

## Redistricting vintage — CURRENT (post-2020-census) map
Taylorsville was **redistricted after the 2020 census** (5 districts, "0% deviation";
city news `/Home/Components/News/News/496/`). District seats are staggered across two
odd-year cycles, so the current map is the **union of the two most recent generals under
the redistricted lines**:

| Cycle | Districts | Contest label style |
|---|---|---|
| **2023** general | **1, 2, 3** | `CITY OF TAYLORSVILLE COUNCIL DISTRICT N` |
| **2025** general | **4, 5** | `TAYLORSVILLE CITY COUNCIL DISTRICT N` |

Together they cover all 44 TAY precincts with **no overlap and no conflicts**. The
**2021** D3/D4/D5 rows use the **pre-redistricting** lines (e.g. 2021 D3 = TAY035,037–044
vs 2023 D3 = TAY023–025,029,032–036,040) and are deliberately **not** used here. For the
prior-vintage map, rebuild with `build_precinct_district_map.py --years 2017,2021` (note
2021 lacks a redistricted-era D1/D2, and 2019 for D1/2/3 is an archive gap — recon.md §5).

## Council structure (important for interpretation)
Taylorsville uses a **council–mayor (executive-mayor) form**: **5 district seats
(Districts 1–5)**, one member each, plus a separately-elected **executive Mayor** (Kristie
Steadman Overson) who does **not** vote on ordinary council motions and has **no district**.
There are **no at-large council seats**. This tool resolves only the **District seat
(1–5)**; the Mayor is city-wide and is not returned (the CLI prints a reminder). The
mayor-non-voting nuance concerns vote extraction, not geography.

Current district members (2025-09-03 council-minutes header /
`taylorsvilleut.gov/government/elected-officials/council`; embedded in
`address_to_district.py::COUNCIL_MEMBERS`, update after each election):
District 1 = Ernest (Ernie) Glen Burgess · District 2 = Curt Cochran ·
District 3 = Anna Barbieri · District 4 = Meredith Harker (Council Chair) ·
District 5 = Bob Knudsen (Vice Chair). (Mayor, city-wide/executive: Kristie Steadman Overson.)

## Files
```
precincts.geojson            44 TAY-prefixed SLCo precincts (UGRC VistaBallotAreas,
                             CountyID=18), true EPSG:4326 (fields PrecinctID, VistaID, CountyID)
precinct_to_district.csv     precinct -> district (1–5); 44 rows; columns
                             precinct,district,source_year,method (no splits, no conflicts)
council_districts.geojson    5 district polygons dissolved from precincts, EPSG:4326
                             (field "district" = "1".."5") — PRECINCT-DERIVED, not official
build_precinct_district_map.py   rebuilds precinct_to_district.csv + council_districts.geojson
address_to_district.py       CLI + importable module: address/point -> district 1-5
```

Precinct→district counts: **D1=7, D2=6, D3=10, D4=7, D5=14** (44 total, 0 splits).

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `council_districts.geojson`
   (`district` = "1".."5"); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside Taylorsville →
district None. The address tool resolves directly against the dissolved **district**
polygons; `precinct_to_district.csv` is a join aid for by-precinct election data.

## Data sources
### Precincts (PRIMARY input to the derivation)
UGRC **VistaBallotAreas** FeatureServer, **CountyID=18** (Salt Lake County — Taylorsville
elections are county-run), the **44 `TAY`** precincts, fetched with `outSR=4326` (browser
UA; the city CMS 403s bots but the UGRC ArcGIS host does not):
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18 AND PrecinctID LIKE 'TAY%'&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
Returned true Utah lon/lat (bounds ≈ `[-111.992, 40.630, -111.908, 40.686]`) — no CRS
fix needed. (The identical 44 TAY features also sit in the shared archive
`~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson`, but that copy is
EPSG:26912 tagged as such — reproject before use; the fresh UGRC fetch avoided that.)

### Precinct → district assignment (the derivation key)
Shared SL County election archive
`~/Desktop/slco-election-archive/data/municipal_results_long.csv`, filtered to Taylorsville
council-**district** contests for **2023 + 2025** (see vintage table above). The election
`precinct` column (e.g. `TAY041`) equals the UGRC `PrecinctID`, so the join is **exact**.
All 44 precincts mapped; **0 unmapped, 0 conflicts, 0 splits** (each precinct appears in
exactly one district contest).

### CRS note
`precincts.geojson` and `council_districts.geojson` are true **EPSG:4326**. If you refetch
precincts, keep `outSR=4326` and verify coords look like Utah lon/lat (≈ −111.94, 40.66),
not UTM meters.

## Usage
```
python3 address_to_district.py "2600 W Taylorsville Blvd, Taylorsville, UT 84129"
python3 address_to_district.py --latlon "40.6677 -111.9388"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-06)
| Input | Result |
|---|---|
| 2600 W Taylorsville Blvd (City Hall) | District 5 (Bob Knudsen) |
| 5407 S Redwood Rd | District 3 (Anna Barbieri) |
| 451 S State St, Salt Lake City (control) | outside Taylorsville → None |

All five district interior points (`geometry.representative_point()`) resolve to their own
district, confirming point-in-polygon for D1–D5.

## Caveats
- **Precinct-derived, not official** — polygons follow precinct lines (an approximation of
  the legal 13.04.100 boundaries). Near-boundary addresses may be off by a precinct edge.
- **Current-vintage only** — reflects the post-2020-census (2023/2025) lines. For pre-2022
  questions, rebuild with earlier `--years` (and mind the 2019 archive gap / 2021 D3 special).
- **The Mayor is city-wide/executive** — no district mapping; never returned. No at-large seats.
- **Boundaries are Taylorsville only** — points outside the city return district None.
- **`--latlon` quoting:** longitude is negative, so pass the pair as one quoted token
  (`--latlon "LAT -LON"`, comma also accepted).
- **Member names are hand-maintained** in `COUNCIL_MEMBERS`; update after each election.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
