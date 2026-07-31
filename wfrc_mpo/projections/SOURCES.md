# wfrc_mpo / projections — sources & provenance

`wfrc_mpo_projections.csv` federates the **Wasatch Front Regional Council small-area
socioeconomic forecast** (Real Estate Market Model / RTP-2023 vintage) at the **city-area
grain** into the repo's 9-column projection schema, plus a derived **WFRC-region total**.
Values are lifted verbatim from WFRC's published ArcGIS layers — nothing modeled or
interpolated here beyond a documented sum.

## Primary source — WFRC RTP-2023 socioeconomic projections (ArcGIS)

WFRC org **`taguadKoI1XFwivx`** (`services1.arcgis.com`). Human portal:
<https://wfrc.org/maps-data/>. All values extracted 2026-07-20 (returnGeometry=false).

| metric | source FeatureServer (layer 0) |
|---|---|
| population | `Population_Projections_City_Area_RTP_2023` |
| households | `Household_Projections_City_Area_RTP_2023` |
| jobs | `All_Jobs_Projections_City_Area_RTP_2023` |

Each layer is one polygon per model **city-area** (316 total) with annual columns
`YEAR2019 … YEAR2050` (+ `CH19TO50` change field), `RELEASE`, `ModelArea`, and
`SECategory=HHPOP`. The full 316-row attribute snapshots are in `raw/`.

## What is federated (and what is not)

- **CITY-AREA grain, WFRC counties only.** The published layers span the whole statewide
  travel model (316 city-areas across 6 sub-models incl. Utah/Cache/Dixie/Iron/Summit).
  Only the **98 city-areas in the six WFRC planning counties** are federated
  (`geography_type=city_area`). WFRC region = **Box Elder, Davis, Morgan, Salt Lake,
  Tooele, Weber**. City-area→county membership was derived from the TAZ layer's `CO_NAME`
  (the city-area layer itself carries no county); only two city-areas are multi-county
  (Draper = Salt Lake+Utah, included as WFRC via its Salt Lake portion; Park City =
  Summit+Wasatch, excluded — non-WFRC).
  - City-areas outside the WFRC counties (Provo, Orem, Lehi = MAG/Utah County; Logan =
    Cache; St. George = Dixie; etc.) are **not** federated here — they belong to other MPOs
    (the sibling MAG module owns Utah County).
- **Regional total** (`geography='WFRC region', geography_type='region'`): the arithmetic
  **sum of the 98 federated WFRC city-areas**, per metric per year. Internally consistent
  with the city-area rows. (A TAZ-by-county sum over the same 6 counties gives 2050 pop
  2,669,075 vs the city-area regional sum 2,673,598 — the ~4,500 difference is Draper's
  Utah-County TAZs, which the city-area "Draper" polygon includes in full. Documented, not
  an error.)
- **All years 2019-2050** are federated (annual), `scenario='baseline'`, `vintage='RTP2023'`.

### NOT federated — kept as module raw/derived + catalog
- **TAZ grain** (`*_Projections_TAZ_RTP_2023`, 9,815 zones each) — too fine to federate.
  Endpoints catalogued in `../gis/index.csv`; a county rollup is in
  `derived/taz_county_rollup.csv` (all 29 counties, snapshot years 2019/2023/2028/2030/
  2040/2050, `in_wfrc_region` flag).
- **Job sub-sectors.** Only *total* jobs (`All_Jobs`) is federated as `metric=jobs`. WFRC
  also publishes Industrial / Office / Retail / Typical / NonTypical job layers at both
  `_City_Area_` and `_TAZ_` grains (same RTP2023 vintage) — query the org directly if a
  sector breakdown is needed.

## Population is HOUSEHOLD population (HHPOP)

`SECategory=HHPOP` — the city-area `population` metric is **household population** and
**excludes group-quarters** (dorms, prisons, etc.). This matters when comparing to Gardner
"total population." Households = **occupied households**, not total housing units (no
vacancy/housing-stock projection — honest gap).

## Cross-check vs the Gardner county projections (read-only sanity check)

WFRC RTP2023 sums for **Salt Lake County** city-areas vs the Kem C. Gardner Institute
county projections (`salt_lake_county/projections/`):

| year | WFRC RTP2023 (SL Co city-areas, HHPOP) | Gardner V2022 hhpop | Gardner V2025 hhpop |
|---|---|---|---|
| 2050 | 1,553,562 | 1,549,038 | 1,450,915 |

**WFRC RTP2023 tracks Gardner Vintage-2022 almost exactly (+0.3%)** — expected, because the
2023 RTP was calibrated to the then-current V2022 series. It runs ~7% ABOVE Gardner's
**Vintage-2025**, which revised the county's growth **down**. When comparing WFRC city-area
sums to a county number, use the **contemporaneous Gardner vintage (V2022)** and Gardner's
**household_population**, not V2025 total population. Trajectories are plausible and
internally consistent — no anomaly.

## Vintage / refresh seam

This is the **RTP2023** vintage. A DRAFT **RTP2027** cycle exists (`CITYAREA_RTP27_gdb`,
`COUNTY_RTP27_gdb`, base year 2023) — catalogued in `../gis/index.csv`, **NOT** merged here.
Vintages are never blended (cardinal rule). When RTP2027 is adopted, append it as a new
`vintage` value and keep RTP2023 for comparison.

## Honest gaps

- No housing-unit (vacancy-inclusive) projection — households is the closest proxy.
- No county-grain layer in the RTP2023 vintage (only City_Area + TAZ); the WFRC-region
  total is derived by summation, documented above. (The DRAFT RTP2027 set *does* add a
  clean `COUNTY_RTP27_gdb` grain — future use.)
- Job sub-sectors and the TAZ grain are not federated (catalog/derived only).
