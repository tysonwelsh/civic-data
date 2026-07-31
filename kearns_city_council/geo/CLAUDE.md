# Geo — Kearns address/point → city council district

Maps a Kearns, Utah address (or lat/long) to its **City Council district** by
point-in-polygon against **precinct-derived** district polygons. Salt Lake County (UGRC
CountyNBR/CountyID = **18**). **As-of: 2026-07-12.**

## Kearns structure (important for interpretation)

Kearns has **two regimes** (hard seam Nov 2025):
- **Metro township (2017–2025):** 5 numbered council districts (1–5), no mayor. **No
  township-era district GIS is built here** — those seats are gone and the map was redrawn.
- **City (2025+, current):** a directly-elected **voting Mayor + 4 Council Members
  (Districts 1–4)**. ⚠ **The mayor VOTES** (Millcreek-style). This tool resolves the
  **city-era district seat only**; the Mayor (Jesse Valdez) is city-wide and not returned.

## The core limitation — D2/D4 exact, D1/D3 unsplit

There is **no official Kearns 4-district FeatureServer** (the only city district map is a
PDF on the Cloudflare-blocked election page). Districts are therefore **derived from the
2025 SOVC precinct→contest assignment** — but the **2025 ballot elected only Mayor + D2 +
D4**, so:

- **D2 and D4 precinct membership is authoritative** (`confidence=high`): the SOVC lists
  exactly which precincts voted in each contest.
- **D1 and D3 were NOT on the 2025 ballot** (their holders — Schaeffer & Butterfield — won
  township D1/D3 in 2023 and carried unexpired terms into the city seats; next elected
  ~2027). The 11 residual precincts are collectively **D1 ∪ D3**, but the SOVC **cannot
  split D1 from D3**. They are dissolved into one polygon labeled **`1/3`** — an honest gap,
  never fabricated. Resolving the split needs the city's official district map.

## Files
```
city_boundary.geojson      Kearns municipal outline (1 polygon), EPSG:4326
                           (UGRC Utah Municipal Boundaries NAME='KEARNS', CountyNBR=18; pop 36,723)
precincts.geojson          20 KRN SLCo precincts, EPSG:4326 (+ `district` field 2/4/"1/3")
districts.geojson          3 polygons — District 2, District 4, and "1/3" (D1-or-D3 residual);
                           fields: district, label, council_member, confidence, source
precinct_to_district.csv   precinct -> district (2/4/"1/3") + method + note; 20 rows
address_to_district.py     CLI + importable module: address/point -> district 2, 4, or "1/3"
build_geo.py               regenerates all of the above (idempotent; re-fetches the boundary)
```

## How it works
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → district** by point-in-polygon against `districts.geojson`; fully offline.
   Returns `2`, `4`, or `1/3` (undetermined). Points outside Kearns → district None.

`district_for_point(lon, lat)` → `{district, council_member, unsplit, mayor, lat, lon}`;
`district_for_address(address)` adds `matched_address`.

## Data sources & derivation
- **City boundary:** UGRC Utah Municipal Boundaries FeatureServer/0,
  `where=NAME='KEARNS'&outSR=4326` (CountyNBR 18; Polygon; POPLASTCENSUS 36,723).
- **Precincts:** UGRC **VistaBallotAreas** CountyID 18, the 20 `KRN`-prefixed precincts,
  taken from the local county mirror
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson` (same UGRC layer),
  reprojected to EPSG:4326. `KRN901` is a **0-registered-voter placeholder** precinct.
- **Districts:** dissolve of the precinct polygons by their 2025 SOVC district:
  - **D2** = KRN003, 005, 009, 016 (from `CITY OF KEARNS COUNCIL DISTRICT 2`)
  - **D4** = KRN008, 012, 013, 014, 015 (from `CITY OF KEARNS COUNCIL DISTRICT 4`)
  - **1/3** = the 11 residual KRN precincts (in the Mayor contest but neither D2 nor D4).
  The precinct union covers **99.8%** of the municipal boundary area; D2 and D4 dissolve to
  equal-area polygons, the residual to ~2× (consistent with two districts).

## Verified tests (2026-07-12)
| Input | Result |
|---|---|
| `5624 S Cougar Ln, Kearns` (Element Event Center area) | District 4 (Lorrin Colby Jr.) |
| rep-point 40.657, −111.994 (offline) | District 2 (Lyndsay Longtin) |
| rep-point 40.646, −112.001 (offline) | District 4 (Lorrin Colby Jr.) |
| rep-point 40.653, −112.013 (offline) | District 1-or-3 (undetermined; Schaeffer/Butterfield) |
| 40.7608, −111.8910 (SLC downtown, control) | outside Kearns → None |

Each district's interior representative point resolves to its own polygon.

## Caveats
- **`1/3` is undetermined by design** — do not present it as a single seat. It means "your
  representative is one of the two D1/D3 holders (Schaeffer, Butterfield), but the 2025 SOVC
  cannot say which." Resolve with the city's official district map when obtainable.
- **City-era only.** Township-era (2017–2025) 5-district geography is not modeled (redrawn).
- **The Mayor is city-wide and voting** — never returned as a district; every resident is
  also represented by Mayor Jesse Valdez.
- **Member names hand-maintained** in `address_to_district.py::COUNCIL_MEMBERS` (the derived
  layer has no member field); update after the ~2027 (D1/D3) and 2029 (Mayor/D2/D4) cycles.
- **`--latlon` quoting:** longitude is negative → pass the pair as one quoted token.
- Geocoding needs internet (Census API, free, no key); the Census geocoder misses some valid
  Kearns addresses (grid-style `4425 S 4800 W` did not match) — supply `--latlon` directly.
- Boundary is Kearns only; points outside return district None.

## Rebuild
```
cd geo && python3 build_geo.py     # re-fetches the UGRC boundary, rebuilds all 4 artifacts
```
Re-run after the **~2027 D1/D3 election** (which will finally reveal the D1-vs-D3 split — add
those precinct sets and replace the `1/3` polygon with real D1 and D3 polygons), or if the
city publishes an official 4-district GIS layer.
