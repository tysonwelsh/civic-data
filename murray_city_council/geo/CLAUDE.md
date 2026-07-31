# Geo — Murray address/point → council district

Maps a Murray, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **Murray's OWN city GIS district polygons** ("Murray City Council
Districts") — the authoritative, whole-city boundary layer. Ported from
`south_jordan_city_council/geo/` (same county, same UGRC precinct source; Salt Lake County,
UGRC internal CountyID = 18). **As-of: 2026-07-11.**

## Murray council structure (important for interpretation)
Murray uses a **council–mayor (executive-mayor / "strong mayor") form**: **5 district seats
(Districts 1–5)**, one member each, plus a separately-elected **executive Mayor** (Brett A.
Hales) who presides over the city but **not** the council and **casts no vote** (the council
elects its own Chair/Vice-Chair). There are **no at-large council seats** — the Mayor is the
only city-wide elected official.

This tool resolves only the **District seat (1–5)**. The Mayor is city-wide (no district) and
is not returned (the CLI prints a reminder). The mayor-non-voting nuance concerns vote
extraction, not geography, and does not affect this tool.

Current district members (Murray `recon.md` roster; embedded in
`address_to_district.py::COUNCIL_MEMBERS`, update after each election):
District 1 = Paul Pickett Acevedo · District 2 = Pam Cotter · District 3 = Clark Bullen ·
District 4 = Diane Turner · District 5 = Adam Hock. (Mayor, city-wide/executive: Brett A. Hales.)

## Files
```
districts.geojson            Murray's 5 official council-district polygons, EPSG:4326
                             (field "District" = "1".."5"; + Council_Member, Label). AUTHORITATIVE.
precincts.geojson            52 Murray (MUR-prefixed) SLCo precincts, EPSG:4326
                             (UGRC VistaBallotAreas, CountyID=18)
precinct_to_district.csv     precinct -> district (1–5), 53 rows; election-derived + cross-checked
                             against the official polygons (see below)
build_precinct_district_map.py   rebuilds precinct_to_district.csv (+ official cross-check)
address_to_district.py       CLI + importable module: address/point -> district 1-5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`
   (`District` = "1".."5"); fully offline.

`district_for_point(lon, lat)` returns `{district, council_member, lat, lon}`;
`district_for_address(address)` adds `matched_address`. Points outside Murray → district None.
The address tool resolves directly against the official **district** polygons;
`precinct_to_district.csv` is a join aid for by-precinct election data.

## Data sources

### City council-district polygons — OFFICIAL, PRIMARY source used
Murray runs its **own ArcGIS Online org** (`murraycity.maps.arcgis.com`, orgId
`RC4r7CDZgn3xGkO8`). The **"Council District Map"** web map
(`8e9e9092b4a64f4d96e5af5a9646c570`, and the **"Council District Lookup Tool"** app
`0ae69f81dec74844ad487ddd5ad60911`) references the district FeatureLayer:

`https://murraycemetery.org/web/rest/services/Public_Base_Layers/MapServer/7`
("**Murray City Council Districts**" — Murray's own GIS server; the `murraycemetery.org`
host is the city's ArcGIS Server, not a cemetery dataset). Fetched via Query → geojson with
`outSR=4326`:
`…/MapServer/7/query?where=1=1&outFields=*&outSR=4326&f=geojson`

- **5 polygons**; fields incl. `OBJECTID`, **`District`** (= "1".."5"), **`Council_Member`**,
  `Label` ("Council District N"), `Boundary_Approval_Date` = **2022-01-04** (post-2020-census
  redistricting). Bounds ≈ `[-111.932, 40.626, -111.834, 40.684]` — true Utah lon/lat.
- **NOTE the layer's `Council_Member` for D3 is slightly stale** — it reads "Scott Goodman"
  (the 2025 interim). **Clark Bullen** won the 2025 D3 2-year special and was sworn Jan 2026;
  the resolver's `COUNCIL_MEMBERS` map carries the corrected current roster.
- This is the **DOCUMENTED FALLBACK path avoided**: the boundary reference PDF
  (`https://www.murray.utah.gov/DocumentCenter/View/16904`, District_Council_Boundaries_2025)
  and precinct-aggregation were **NOT needed** — Murray's own FeatureServer was reachable and
  authoritative. If the `murraycemetery.org` host ever flaps, the PDF and the precinct-derived
  union (dissolve `precincts.geojson` by `precinct_to_district.csv`) are the fallbacks.

### CRS note
The layer's native SR is **wkid 102743 / latestWkid 3566** (NAD83 Utah Central, ftUS). The
query was issued with **`outSR=4326`** and the result verified to be true Utah lon/lat
(Murray sits around −111.89, 40.66). geopandas reads the file as EPSG:4326 and point-in-polygon
against Census lat/long works directly. If you refetch, keep `outSR=4326` and re-verify.

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, filtered to the **52 `MUR`-prefixed** Murray
precincts, fetched with `outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID=18 AND PrecinctID LIKE 'MUR%'&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`

**⚠ CountyID reconciliation (task 49035 vs UGRC internal 18).** The county's FIPS / standard
CountyID for Salt Lake is **49035**. But UGRC's **VistaBallotAreas** layer keys Salt Lake
County by an **internal `CountyID = 18`** — this is the value the sibling SLCo repos
(south_jordan, taylorsville, sandy) filter on, and it is what returns Salt Lake precincts.
Filtering `CountyID=49035` returns **nothing**. This build matches the sibling convention and
uses **`CountyID = 18`** (verified: returns the MUR precincts). The `49035` FIPS is the correct
key for other datasets (Census, the county elections archive), just **not** for this UGRC layer.

### Precinct → district method
`precinct_to_district.csv` is **election-derived**: each **`MURRAY CITY COUNCIL DISTRICT N`**
contest in the shared Salt Lake County SOVC archive
(`salt_lake_county/elections/slco_municipal_results_long.csv`) lists exactly the precincts
that voted in it, so contest-precincts == district-precincts for that election's boundaries.
The election `precinct` column (e.g. `MUR041`) equals the UGRC `PrecinctID`, so the join is
exact. **Vintage = CURRENT (post-2020-census)**: the current 5-district map is the union of the
two most-recent generals under the redistricted lines —
**2023** general → D1/D3/D5, **2025** general → D2/D4 (the D2/D4/Mayor cycle first ran under the
new lines in 2025). The 2025 **"DISTRICT 3 (2 YEAR TERM)"** special is excluded (D3 taken from
2023); as a built-in check, its 14 precincts are **identical** to 2023 D3. Rebuild with
`python3 build_precinct_district_map.py` (defaults to `--years 2023,2025`).

**Cross-check:** every mapped precinct's representative interior point was tested for
containment in the **official** district polygons (`districts.geojson`). The election-derived
assignment **AGREES with the official polygons on all 52 precincts that carry geometry** — 0
disagreements, 0 conflicts. Precinct→district counts: **D1=8, D2=11, D3=14, D4=8, D5=12** (53
total). The CSV records the official-centroid district + an `agrees` column per row.

## Usage
```
python3 address_to_district.py "5025 S State St, Murray, UT 84107"
python3 address_to_district.py --latlon "40.6669 -111.8880"    # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-11)
| Input | Result |
|---|---|
| 5025 S State St (Murray City Hall) | District 3 (Clark Bullen) |
| 5 district interior points (offline `representative_point()`) | each resolves to its own D1–D5 |
| 451 S State St, Salt Lake City (control) | outside Murray → None |

## Caveats / gaps
- **`districts.geojson` is Murray's OWN official layer** (not precinct-derived) — the
  authoritative whole-city boundary. Contrast Taylorsville (precinct-derived, no official layer).
- **`MUR053`** appears in the 2023 D3 election contest but has **no geometry in the current UGRC
  VistaBallotAreas layer** (52 features returned for 53 election precincts). It is mapped to D3 in
  `precinct_to_district.csv` with `agrees=no_geometry`. This does not affect the address tool
  (which uses the official district polygons, not precincts). Likely a merged/renumbered sub-
  precinct in the UGRC vintage.
- **D3 `Council_Member` on the source layer is stale** ("Scott Goodman", 2025 interim); the
  resolver carries the corrected **Clark Bullen**. Member names are hand-maintained in
  `COUNCIL_MEMBERS`; update after each election.
- **Vintage = post-2020-census (boundaries approved 2022-01-04).** An address near a moved
  boundary may mis-assign for **pre-2022** questions. For a prior-vintage precinct→district
  table rebuild with earlier `--years` (mind the 2019 general archive gap flagged in `recon.md`).
- **The Mayor is city-wide/executive** — no district mapping; never returned. No at-large seats.
- **`--latlon` quoting:** longitude is negative, so pass the pair as one quoted token
  (`--latlon "LAT -LON"`, comma also accepted).
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
