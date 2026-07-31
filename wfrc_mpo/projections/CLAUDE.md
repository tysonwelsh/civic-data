# wfrc_mpo / projections — WFRC small-area population/household/jobs forecast

The **Wasatch Front Regional Council** small-area socioeconomic forecast (Real Estate
Market Model, **RTP-2023 vintage**) at the **city-area** grain — the sub-county projection
layer Gardner's county series does not provide. Annual **2019-2050** population, households,
and jobs for every city-area in the six WFRC counties, plus a regional total.

## Files

- `wfrc_mpo_projections.csv` — **canonical.** Repo 9-col schema
  (`geography, geography_type, year, metric, value, scenario, source, source_url, vintage`),
  long-format, one row per geography × year × metric. 9,504 rows.
- `SOURCES.md` — provenance, the WFRC-region definition, the HHPOP nuance, the Gardner
  cross-check, and gaps. **Read before quoting.**
- `raw/` — the three City_Area attribute snapshots (316 rows each).
- `derived/taz_county_rollup.csv` — TAZ grain summed to county (all 29 counties, snapshot
  years, `in_wfrc_region` flag). The TAZ grain itself is too fine to federate.

## Grains & counts

- **9,504 rows** = (98 WFRC city-areas + 1 WFRC region) × 3 metrics × 32 years (2019-2050).
- `geography_type`: `city_area` (98 areas) and `region` (`WFRC region`).
- `metric`: `population`, `households`, `jobs`. `scenario='baseline'`, `vintage='RTP2023'`.

## Read-me-first caveats

1. **`population` is HOUSEHOLD population (HHPOP)** — excludes group quarters. Compare to
   Gardner `household_population`, not total population.
2. **`households` ≠ housing units** (occupied households; no vacancy/stock projection).
3. **WFRC region = 6 planning counties** (Box Elder, Davis, Morgan, Salt Lake, Tooele,
   Weber); the region row is the sum of the 98 federated city-areas. City-areas in other
   MPOs (Utah County = MAG, etc.) are deliberately excluded.
4. **RTP2023 tracks Gardner V2022, not V2025** (it predates V2025's downward revision). See
   SOURCES for the numbers — this is expected, not an anomaly.
5. **Refresh seam:** a DRAFT RTP2027 forecast exists (catalogued in `../gis/`), **not**
   merged here. Never blend vintages.

## Rebuild

Re-query the three `*_Projections_City_Area_RTP_2023` FeatureServers (org
`taguadKoI1XFwivx`) with `outFields=*&returnGeometry=false&f=json`, filter to the WFRC
city-areas (county membership from the TAZ layer's `CO_NAME`), emit per-year rows, and sum
for the region row. See `SOURCES.md` for the exact layer→metric map.
