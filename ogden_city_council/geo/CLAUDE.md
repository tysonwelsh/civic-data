# Geo — Ogden address/point → council district

Maps an Ogden, Utah (Weber County) address (or lat/long) to its City Council
**district (1–4)**, using **Ogden City's own GIS precinct layer** and its authoritative
`MUNIWARD` (= council district) field. Ported from `slc_city_council/geo/` and
`west_jordan_city_council/geo/` (same approach).

## Ogden council structure (important for interpretation)
Ogden has a **7-member council: 4 DISTRICT seats (Districts 1–4) + 3 AT-LARGE seats
(Seats A, B, C)**, plus a separately elected **Mayor** (strong-mayor; the Mayor does NOT
vote on council legislation). Every resident is represented by **five** elected officials:
their District councilmember, **all three** At-Large councilmembers, and the Mayor.

This tool only resolves the **District seat (1–4)**. The three At-Large members and the
Mayor are **city-wide** — they have no precinct→district mapping and are not returned (the
CLI prints a reminder that they cover everyone).

## Files
```
precincts.geojson                 Ogden city precinct boundaries, EPSG:4326 (41 OGD precincts)
council_districts.geojson         4 council-district polygons (dissolved from precincts by MUNIWARD), EPSG:4326
precinct_to_district.csv          precinct, district, source_year  (41 precincts, == MUNIWARD)
address_to_district.py            CLI + importable module: address/point -> district
precincts_ugrc.geojson            INFORMATIONAL: UGRC VistaBallotAreas CountyID=29 (Weber), 200 features
```

## How it works (precinct-based)
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → precinct** by point-in-polygon against `precincts.geojson`
   (`PRECINCT`, e.g. `OGD21`); fully offline.
3. **precinct → district** via `precinct_to_district.csv` (the `MUNIWARD` field).

Resolving by **precinct** (the actual ballot-assignment unit, carrying its own MUNIWARD)
is the authoritative path. `council_districts.geojson` is the dissolved district outline
for mapping/cross-check; it was built by dissolving the precincts on MUNIWARD, so it
agrees with the precinct lookup by construction.

## Data source — Ogden City GIS (authoritative, PREFERRED per recon)
**`Public/Ogden_Voting_Precincts` FeatureServer/0** on the Ogden City ArcGIS server:
`https://arcgis.ogdencity.com/arcgis/rest/services/Public/Ogden_Voting_Precincts/FeatureServer/0`

- **41 Ogden city precincts**, `PRECINCT` = `OGD01`…`OGD41`.
- Field **`MUNIWARD` (SmallInteger) = the council district** (1, 2, 3, 4). This is the
  precinct→district authority for the address tool.
- Other fields: `CONSOL_PRE` (all null in this layer), `POLLING_PL`, `ADDRESS`.
- Distinct MUNIWARD = {1,2,3,4} → confirms 4 districts.
- **Precinct counts per district (live layer, 2026-06):** District 1 = 10, District 2 = 9,
  District 3 = 11, District 4 = 11 (= 41). (Recon noted 11/8/10/12 from an earlier read;
  the live FeatureServer is the authority — minor count drift, total 41 either way.)

Refetch / regenerate:
```
curl -s "https://arcgis.ogdencity.com/arcgis/rest/services/Public/Ogden_Voting_Precincts/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson" -o precincts_raw.geojson
# then: read with geopandas, write precincts.geojson, derive precinct_to_district.csv from
# MUNIWARD, and dissolve(by=MUNIWARD) -> council_districts.geojson.
```

## CRS note (the playbook gotcha — verified clean here)
- The Ogden layer's **native** spatial reference is **WKID 102742 / 3560** (NAD83 Utah
  State Plane North, US-feet) — a projected CRS, NOT lon/lat. **Always request
  `outSR=4326`.** With `outSR=4326` the returned coords are correct Utah lon/lat
  (≈ −111.97, 41.22; city bounds [−112.026, 41.160] → [−111.920, 41.286]) — verified, NOT
  meters/feet. No reprojection needed after a 4326 query.
- The **UGRC VistaBallotAreas** CountyID=29 layer (`precincts_ugrc.geojson`,
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`)
  is kept **informational only**. Queried with `outSR=4326` it also returned correct Utah
  lon/lat here (the playbook-flagged 26912-mislabeled-as-4326 problem did NOT manifest on
  this `outSR=4326` query — but still verify coords look like Utah lon/lat before any use).
  It returned **200 features** for CountyID=29 (recon's earlier read saw 153; UGRC updated),
  of which **42** are `29OG`-prefixed (Ogden city). It carries `PrecinctID` only — **no
  MUNIWARD / district field** — so it can't assign districts on its own and is not used by
  the tool. Reconcile naming if ever joined: UGRC `29OG##` (CountyID prefix) ↔ city `OGD##`.

## Duplicate / sub-precinct handling
The recon-flagged **duplicate `29CN05`** and **sub-precinct suffixes** (`:X`,`:H`,…) are in
the **statewide UGRC layer**, not in this city layer. The Ogden City
`Ogden_Voting_Precincts` layer is clean: **41 distinct `PRECINCT` values, no duplicates, no
suffixes** (verified — `Counter` over PRECINCT has no value > 1). Nothing to dedupe for the
district tool; the dedup caveat applies only if you ever build from `precincts_ugrc.geojson`.

## Usage
```
python3 address_to_district.py "2549 Washington Blvd, Ogden, UT 84401"
python3 address_to_district.py --latlon 41.2230 -111.9706     # offline
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

### Verified test addresses
| Address | Precinct | District |
|---|---|---|
| 2549 Washington Blvd (Ogden Municipal Building) | OGD21 | 1 |
| 3848 Harrison Blvd (Weber State area) | OGD36 | 4 |
| 1140 28th St | OGD28 | 4 |
| 451 S State St, Salt Lake City (out-of-city control) | — | outside Ogden (None) |

Offline check: `--latlon 41.2230 -111.9706` → OGD21 → District 1 (matches the
Municipal-Building address path). All 4 districts round-trip via precinct centroids
(OGD15→D1, OGD01→D2, OGD10→D3, OGD24→D4).

## Caveats
- **At-large (Seats A/B/C, 3 seats) + the Mayor are city-wide** — no precinct→district
  mapping; the tool never returns them. The Mayor (strong-mayor form) does not vote on
  council legislation.
- **Native CRS is 3560 (State Plane ft)** — always query `outSR=4326`; verify coords look
  like Utah lon/lat, not projected, before point-in-polygon.
- Boundaries are **Ogden city only**; points outside Ogden return district None.
- Geocoding requires internet (Census API, free, no key); `--latlon` lookups are offline.
  The Census geocoder occasionally returns "no match" for some valid Ogden addresses
  (e.g. odd unit/format); supply `--latlon` directly when that happens.
- The map is **current** (Ogden City GIS as of 2026-06). `source_year` in
  `precinct_to_district.csv` is tagged `2025`; re-query the FeatureServer to refresh after
  any city reprecincting/redistricting.
```
