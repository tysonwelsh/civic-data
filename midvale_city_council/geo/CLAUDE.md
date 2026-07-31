# Geo — Midvale address/point → council district

Maps a Midvale, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **Midvale's own OFFICIAL council-district FeatureServer**
(`City_Council_Districts_view`, hosted on Midvale's ArcGIS org) — the authoritative,
whole-city boundary layer. Modeled on `south_jordan_city_council/geo/` (same county, same
UGRC precinct source; Salt Lake County, **UGRC CountyID = 18**). **As-of: 2026-07-11.**

## Midvale council structure (important for interpretation)
Midvale uses a Utah **six-member council form: 5 district seats (Districts 1–5)** plus a
separately-elected **Mayor** (Dustin Gettel). There are **no at-large council seats** — the
Mayor is the only city-wide elected official. Every resident is represented by **two**
elected officials: their District councilmember and the city-wide Mayor.

This tool resolves only the **District seat (1–5)**. The Mayor is city-wide (no district)
and is not returned (the CLI prints a reminder). The mayor-vote nuance flagged in the city
`recon.md` (mayor votes only on ties / mayoral-power ordinances / city-manager hire-fire)
concerns vote extraction, not geography, and does not affect this tool.

Current district members (from the 2025-12-02 council-minutes header /
`midvale.utah.gov/government/city_council.php`; embedded in
`address_to_district.py::COUNCIL_MEMBERS`, update after each election):
District 1 = Bonnie Billings · District 2 = Paul Glover · District 3 = Heidi Robinson ·
District 4 = Bryant Brown · District 5 = Denece Mikolash. (Mayor, city-wide: Dustin Gettel.)

## Files
```
districts.geojson           Midvale's 5 official council-district polygons, true EPSG:4326
                            (field "District" = "1".."5"; from the official
                            City_Council_Districts_view FeatureServer, GEOMETRY ONLY)
precincts.geojson           38 Midvale (MID-prefixed) SLCo precincts, true EPSG:4326
precinct_to_district.csv    precinct -> district (1–5), centroid-in-district; 38 rows, 0 splits
address_to_district.py      CLI + importable module: address/point -> district 1-5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`
   (`District` = "1".."5"); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside Midvale → district
None. The address tool does **not** use `precinct_to_district.csv` — the official district
layer is authoritative and whole-city, so the lookup is a direct point-in-polygon against
the **district** outlines. The precinct table is a join aid for by-precinct election data.

## Data sources

### City council-district polygons (OFFICIAL, authoritative, PRIMARY source used)
Midvale's **own official ArcGIS FeatureServer**, `City_Council_Districts_view`, layer 0:
`https://services6.arcgis.com/8xmMYBLanDLIUCUt/arcgis/rest/services/City_Council_Districts_view/FeatureServer/0`
- Fetched via Query → geojson with `outSR=4326`:
  `…/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`
- **5 polygons**; source fields incl. `Counc_Dist` (= "1".."5"), `Name` (`District 1`…),
  `CITY`, and `F_Name`/`L_Name`. **⚠ The member-name fields are STALE** (District 5 is
  labeled "Dustin Gettel", now the Mayor) — we used **GEOMETRY / `Counc_Dist` ONLY** and
  took member names from the current roster (see `COUNCIL_MEMBERS`). Saved layer keeps only
  `District` (renamed from `Counc_Dist`), `Name`, `CITY`; no stale name fields retained.
- Endpoint responded 200 with valid GeoJSON on the first request; no precinct-derivation of
  current boundaries was needed. (Midvale open-data hub `data.json` lists the same "City
  Council Districts" dataset; the FeatureServer above is the direct source.)

### CRS note
The layer was queried with **`outSR=4326`** and verified to be true Utah lon/lat (Midvale
sits around −111.89, 40.61; all five district interior points resolve to their own
district). geopandas reads the file as EPSG:4326 and point-in-polygon against Census
lat/long works directly. If you refetch, keep `outSR=4326` and re-verify coords look like
Utah lon/lat.

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake County — Midvale
elections are county-run), filtered to the **38 `MID`-prefixed** Midvale precincts, fetched
with `outSR=4326`. Service (canonical, per gis.utah.gov):
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`
(1008 SLCo features statewide-county → filtered to the 38 MID-prefixed precincts that
intersect the district layer; sliver-overlaps <10% of precinct area dropped).

**Precinct→district method:** each precinct's representative interior point was tested for
containment in a district polygon (`method=centroid_in_district`), and cross-checked against
majority-area overlap. `district_area_frac` is the assigned-district share of the precinct's
**in-city** area (normalized so precincts straddling the city boundary are not spuriously
flagged) — **min 0.9914, so there are no split precincts** (`split=no` for all 38 rows).
Precinct→district counts: **D1=14, D2=7, D3=6, D4=6, D5=5** (38 total).

**Election cross-check (`election_xcheck` column):** each precinct's geometric assignment
was cross-checked against which "MIDVALE … DISTRICT N" contest it voted in the most recent
cycle (D1/2/3 → 2023, D4/5 → 2025) in
`election_results/midvale_results_by_precinct.csv`. **34 of 38 = `agree`; 0 mismatches.**
The 4 `no_recent_election` precincts (**MID035–MID038**) are cleanly inside one district by
geometry (in-city overlap 0.90–1.00) but produced no reported council-district tallies in
the recent cycle — an honest election-data gap, not a geometry problem. (The historical
election file also carries older numeric precinct IDs — 45xx — and 14 precincts that voted
different districts across cycles; those reflect **redistricting over time**, resolved here
by using the current polygons + the current election cycle.)

## Usage
```
python3 address_to_district.py "7505 S Holden St, Midvale, UT 84047"
python3 address_to_district.py --latlon "40.6111 -111.8885"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-11)
| Input | Result |
|---|---|
| 7505 S Holden St (Midvale City Hall) | District 5 (Denece Mikolash) |
| 451 S State St, Salt Lake City (control) | outside Midvale → None |
| D1–D5 interior rep-points (offline PIP) | each resolves to its own district |

All five district interior points (`geometry.representative_point()`) resolve to their own
district, confirming point-in-polygon for D1–D5.

## Caveats
- **The Mayor is city-wide** — no district mapping; never returned. (Six-member council
  form; the mayor-vote nuance in the city `recon.md` affects vote extraction, not this
  tool.) There are **no at-large council seats**.
- **The official layer's member-name attributes are STALE** — geometry/`Counc_Dist` is
  authoritative; names are hand-maintained in `COUNCIL_MEMBERS` and must be updated after
  each election.
- **Boundaries are Midvale only** — points outside the city return district None.
- **`--latlon` quoting:** because longitude is negative, argparse mis-parses two bare
  numbers; pass the pair as one quoted token (`--latlon "LAT -LON"`, comma also accepted).
- **CRS:** always refetch with `outSR=4326` and re-verify Utah lon/lat.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
