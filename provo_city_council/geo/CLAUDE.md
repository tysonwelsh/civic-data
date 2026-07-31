# Geo — Provo address/point → Municipal Council district

Maps a Provo, Utah address (or lat/long) to its Provo **Municipal Council district (1–5)**.

Provo Municipal Council = **7 members**: Districts 1–5 (geographic) + **2 citywide seats**
(Citywide I & II) + a separately elected **Mayor**. The two citywide councilmembers and the
Mayor represent the whole city, so this tool returns only the geographic **District 1–5**.

## Files
```
precincts.geojson              Provo precinct polygons (PRECINCT, COUNCIL_DISTRICT, POLLING_PLACE), WGS84
build_precinct_district_map.py -> precinct_to_district.csv (regenerable lookup)
precinct_to_district.csv        precinct, district, source_year (67 Provo precincts, Districts 1–5)
address_to_district.py          CLI + importable module: address/point -> district
```

## How it works (no separate council-boundary file needed)
1. **address → lat/long** via the free U.S. Census geocoder (needs internet).
2. **lat/long → precinct** by point-in-polygon against `precincts.geojson` (`PRECINCT`,
   e.g. `25PR04`); fully offline.
3. **precinct → district** via `precinct_to_district.csv`.

## Usage
```
python3 build_precinct_district_map.py                       # (re)build the lookup
python3 address_to_district.py "445 W Center St, Provo, UT 84601"
python3 address_to_district.py --latlon 40.2338 -111.6585    # offline
python3 address_to_district.py --batch addresses.txt
```
As a module: `from address_to_district import district_for_address, district_for_point`.

Tested OK:
- `445 W Center St, Provo, UT 84601` (Provo City Center) → 25PR54 → **District 5**
- `1700 N 900 E, Provo, UT 84604` (BYU area) → 25PR31 → **District 1**
- `1200 Towne Centre Blvd, Provo` (south Provo mall) → 25PR60 → **District 3**
- Offline `--latlon 40.2338 -111.6585` → 25PR46 → District 5; an out-of-city point → None.

## Data provenance

### Precinct geometry — Provo City GIS, not raw UGRC Vista
`precincts.geojson` is pulled from **Provo City's own GIS** "Precinct Boundary" layer:
`https://gispublicweb.provo.org/ArcGIS/rest/services/Council/Council_Districts/FeatureServer/1`
(68 polygons; `outSR=4326`). That layer is preferable to the statewide UGRC Vista layer here
because **it already carries `COUNCIL_DISTRICT` per precinct** AND it includes Provo precincts
(`25PR02`, `25PR03`, `25NE13`) that are **missing from UGRC Vista**, so it gives full District-1
coverage that Vista alone would not.

For reference, the UGRC source (used elsewhere in this repo / the playbook):
- **VistaBallotAreas FeatureServer**, `CountyID=25` (Utah County):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
  → 533 ballot areas countywide; Provo precincts are the `25PR##` PrecinctIDs (64 of them).
- **CRS lesson (from the West Valley build):** always request `outSR=4326` and verify the
  coordinates look like Utah lon/lat (≈ **-111.66, 40.31**), not UTM meters. Both the Provo
  layer and Vista were fetched with `outSR=4326`; `precincts.geojson` bounds are
  `[-111.74, 40.19, -111.54, 40.33]` — confirmed true WGS84, not EPSG:26912.

### Precinct-naming reconciliation
- Election CSV (`election_results/provo_results_by_precinct.csv`) uses **`PR##`** (e.g. `PR04`).
- Provo GIS and UGRC Vista use **`25PR##`** (CountyID 25 + `PR##`, e.g. `25PR04`).
- They reconcile by stripping the `25` prefix. The lookup CSV and `precincts.geojson` both key
  on the canonical **`25PR##`** `PRECINCT` value, so the join is internally consistent; the
  `build` script strips `25` only to cross-check the election file.
- One election row was literally `PR04 & 25PR02` (a combined reporting unit) — corroborating
  that election `PR##` == GIS `25PR##`.

### Which district came from which source (`source_year`)
| District | Precincts | source_year | Basis |
|---|---|---|---|
| 1 | 19 | `gis-2023map` | City GIS only — **no precinct-level election data exists** (odd-year-B seat: 2019/2023, no precinct CSV published for 2023). |
| 2 | 14 | `2025` | City GIS, **cross-validated** against 2025 municipal-general precinct results (match; GIS adds one newer precinct `25PR66`). |
| 3 | 11 | `gis-2023map` | City GIS only — no precinct election data. |
| 4 | 13 | `gis-2023map` | City GIS only — no precinct election data. |
| 5 | 10 | `2025` | City GIS, **cross-validated** against 2025 results — **exact match** (10/10 precincts). |

Provo **redistricted** between the 2021 and 2025 cycles (precinct numbering changed: ~45
reporting precincts in 2021 vs ~65 in 2025). The map here is the **CURRENT** post-redistricting
map (the city's published 2023-cycle districts; cf. Provo City Code **§2.01.050** / §2.50.060).
Election data only ever contains **District 2, District 5, Citywide I, and Mayor** contests
(2021 & 2025 — the odd-year-A stagger), which is why Districts 1/3/4 rely on the city GIS map.

## Caveats
- **Districts 1, 3, 4 have no precinct-level election corroboration.** They are taken from
  Provo City's authoritative published GIS map (the current 2023-cycle districts). Districts 2
  & 5 are additionally confirmed against the 2025 precinct results. No precinct→district
  assignment was fabricated — every row traces to the city GIS layer.
- **Redistricting:** the lookup is the current map. For a 2021-era question, the old precinct
  numbering (and the §2.01.050 numeric precinct codes like 301/302) would apply; rebuild from
  era-appropriate data. 2023/2019 districts never had precinct CSVs, so a true historical D1/3/4
  map isn't reconstructable from election data alone.
- **§2.01.050** lists districts by an **older numeric precinct scheme** (301, 302, … / D1=301–319,
  D2=315–364, D3=326–367, D4=320–346, citywide=all). Those codes do **not** match the current
  `25PR##` Vista/GIS codes — they predate the latest redistrict — so we use the city GIS layer,
  which is in the current `25PR##` scheme, instead.
- **Mail / combined precincts:** the GIS layer has one polygon (`25NE10`) with no council
  district (excluded from the CSV). Any precinct without a polygon can't be resolved from a point.
- Geocoding needs internet (Census API, free, no key); `--latlon` lookups are fully offline.
- Boundaries cover only Provo; points outside Provo return district `None`.
- **Citywide I/II councilmembers and the Mayor are citywide** and are intentionally not returned.
```

> CountyID=25 = Utah County (UGRC standard county number). outSR=4326 everywhere. Join key = `25PR##`.
