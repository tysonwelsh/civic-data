# Geo — Holladay address/point → council district

Maps a Holladay, Utah address (or lat/long) to its City Council **district (1–5)** by
point-in-polygon against **Holladay's OWN official district-polygon layer** — *"Holladay
City Council Districts, as amended 2022"* (ArcGIS Hub item
`d0cb510277ee4f0f989c9a5de4d0a6da`). Unlike Taylorsville/South Jordan (precinct-derived),
Holladay publishes real district polygons, so this resolves directly against the
authoritative outlines. **As-of: 2026-07-12.** Salt Lake County (UGRC CountyID = 18).

## Holladay council structure (important for interpretation)
Holladay uses a **Council–Manager** form: **5 district seats (Districts 1–5)** plus a
separately-elected **Mayor** (city-wide). There are **no at-large council seats** — the Mayor
is the only city-wide elected official. Every resident is represented by **two** officials:
their District councilmember and the city-wide Mayor. (Note: unlike an executive-mayor city,
the Holladay Mayor also **votes** on the council — that concerns vote extraction, not geo.)

This tool resolves only the **District seat (1–5)**; the Mayor is not returned (the CLI
prints a reminder).

Current district members, **seated Jan 2026** (from the district layer's `Representative`
field, corroborated by the 2026-02-05 council-minutes attendance block; embedded in
`address_to_district.py::COUNCIL_MEMBERS`, update after each election):
District 1 = **David Sundwall** · District 2 = **Matt Durham** · District 3 = **Natalie
Bradley** · District 4 = **Drew Quinn** · District 5 = **Emily Gray**. (Mayor, city-wide:
**Paul Fotheringham**.)

## Files
```
council_districts.geojson   Holladay's 5 official council-district polygons, true EPSG:4326
                            (property "District" = "1".."5"; also population + Representative;
                            from the "as amended 2022" layer)
precincts.geojson           30 Holladay (HOL0##) SLCo precincts, true EPSG:4326 (UGRC)
precinct_to_district.csv    precinct -> district (1–5), centroid-in-district; 30 rows, 0 splits
address_to_district.py      CLI + importable module: address/point -> district 1-5
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `council_districts.geojson`
   (`District` = "1".."5"); fully offline. `district_for_point(lon,lat)` →
   `{district, council_member, lat, lon}`; `district_for_address(address)` adds
   `matched_address`. Points outside Holladay → district None. The address tool does **not**
   use `precinct_to_district.csv` (the district layer is authoritative and whole-city).

## Data sources

### City council-district polygons (authoritative, PRIMARY source used)
Holladay's official **"Holladay City Council Districts"** ArcGIS Hub item
**`d0cb510277ee4f0f989c9a5de4d0a6da`** ("as amended 2022"). The item is a **Web Map** whose
single operational layer `Council_Districts_2022` embeds the 5 district polygons as a
**featureCollection** (resolved from the item's `/data` JSON — the org service list uses a
generic WFL name, so the Hub-item→data path is the reliable resolver, exactly as `recon.md`
warned). 5 polygons; fields `FID`, `population`, **`D_STRICT`** (= 1..5, written to property
`District`), `Representa` (current member → `Representative`), `Redistrict`.
- **CRS:** the embedded geometry is **Web Mercator (wkid 102100 / 3857)**; reprojected to
  **EPSG:4326** with the standard spherical-Mercator inverse. Verified Holladay bounds
  (lon −111.854…−111.786, lat 40.630…40.687). If refetched, re-reproject and re-verify.
- Hosting org (for reference / other layers like zoning, municipal boundary):
  `https://services6.arcgis.com/mGvwEqK9FI5j4ecF/arcgis/rest/services`.

### Precincts (informational + precinct→district join aid)
UGRC **VistaBallotAreas** FeatureServer, **CountyID = 18** (Salt Lake — Holladay elections
are county-run), filtered to the **30 `HOL0##`** precincts (`PrecinctID LIKE 'HOL%' AND
CountyID=18`; a `CountyID=14` "HOLD8" precinct in another county is excluded), fetched with
`outSR=4326`:
`https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/VistaBallotAreas/FeatureServer/0/query?where=CountyID%3D18%20AND%20PrecinctID%20LIKE%20%27HOL%25%27&outFields=PrecinctID,VistaID,CountyID,SubPrecinctID,AliasName,VersionNbr&outSR=4326&f=geojson`

**Precinct→district method:** each precinct's representative interior point tested for
containment in a district polygon (`method=centroid_in_district`), cross-checked against
majority-area overlap — **the two agree on all 30 precincts**, every precinct's largest
area-fraction is **> 0.95** (min 0.955), so **no split precincts** (`split=no` for all rows).
Counts: **D1=5, D2=5, D3=5, D4=5, D5=10** (30). D5 is larger because 2022 redistricting moved
several formerly-D1/D3/D4 precincts into it (see the cross-check below).

### Cross-check to the district ELECTION contests (redistricting-aware)
The polygon map was validated against which district each precinct actually **voted in**
(`../election_results/holladay_results_by_precinct.csv`). Using the **post-2022** contests
(the same boundary vintage as the layer):
- **2025 District 3** = {HOL013,014,015,016,024} — **exact match** to polygon D3. ✅
- **2023 District 4** = {HOL006,007,012,028,029} — **exact match** to polygon D4. ✅
- **2025 District 1** = {HOL008,009,010,027,**031**} vs polygon D1 {008,009,010,**025**,027}
  — matches on 4/5; the fifth is a **precinct-renumber seam** (see below). ✅ (modulo renumber)

Every apparent *disagreement* with a **pre-2022** election (HOL011/017/018/019/020/021/022,
and HOL025) is a genuine **2022 REDISTRICTING** change, not an error — e.g. HOL019/HOL021
were **D1** in 2021 and are **D5** in the 2022 lines; HOL017/HOL018 moved **D3→D5**;
HOL011/HOL020/HOL022 moved **D4→D5**. The polygon (current) is authoritative for present-day
districts; pre-2022 election precinct→district reflects the **old** lines.

## Known seams / caveats
- **Boundary vintage = "as amended 2022"** (post-2020-census). Address-history questions near
  a moved boundary before 2022 may mis-assign; the layer only encodes the current lines.
- **Precinct renumber (HOL025 ↔ HOL031).** The UGRC layer's **HOL025** is 98.7% inside the
  D1 polygon, but the Nov-2025 election's D1 precinct there is **HOL031** (≈263 voters) —
  which is **absent from the current UGRC layer** — while UGRC HOL025 cast only ~7 city-wide
  (mayor-only) votes in 2025. They are the same NW-D1 area under different vintage numbers.
  `precinct_to_district.csv` follows the **polygon** (HOL025→D1); the by-precinct election
  data carries its own authoritative `district` column, so election joins are unaffected.
- **Election precinct IDs not in the current layer:** older elections use county-wide numeric
  IDs (`4008`, `4020`…, 2007–2009) and, post-renumber, `HOL031`–`HOL035`. These are **not**
  in `precinct_to_district.csv` (which is the *current* 30-precinct map); join by-precinct
  election data via its own `district` column instead.
- **The Mayor is city-wide** — no district mapping; never returned. **No at-large seats.**
- **`--latlon` quoting:** longitude is negative → pass the pair as one quoted token
  (`--latlon "40.66 -111.82"`, comma also accepted).
- **Member names are hand-maintained** in `COUNCIL_MEMBERS` — update after each election.
- Geocoding needs internet (Census API, free, no key); `--latlon` lookups are offline.

## Usage
```
python3 address_to_district.py "4580 S 2300 E, Holladay, UT 84117"
python3 address_to_district.py --latlon "40.6592 -111.8210"     # quote the pair (negative LON)
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified tests (2026-07-12)
| Input | Result |
|---|---|
| 4580 S 2300 E (Holladay City Hall) | District 1 (David Sundwall) |
| 451 S State St, Salt Lake City (control) | outside Holladay → None |
| 5 district interior points (representative_point) | each resolves to its own D1–D5 |
