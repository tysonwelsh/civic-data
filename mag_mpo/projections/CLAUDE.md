# mag_mpo / projections — MAG region city population & jobs projections

City-grain **population** and **jobs** projections for the MAG region (Utah, Summit, Wasatch
counties), from MAG's adopted **2023 RTP socioeconomic forecast**. Long format, repo-standard
9-col projection schema.

## Files

- `mag_mpo_projections.csv` — **canonical.** 328 rows = 41 geographies × 4 years
  (2020/2030/2040/2050) × 2 metrics (population, jobs). One row per
  geography × year × metric. Values verbatim from the MAG ArcGIS feature services.
- `SOURCES.md` — full provenance, schema mapping, the Gardner sanity check, honest gaps.
- `raw/` — verbatim ArcGIS JSON snapshots of the two by-city services (2026-07-20).

## Schema

`geography, geography_type, year, metric, value, scenario, source, source_url, vintage`
— `geography_type` is `city_area` (38 municipalities) or `unincorporated_area` (3);
`scenario`=`baseline`; `vintage`=`MAG 2023 RTP (adopted 2023)`.

## Caveats — read before quoting

1. **Vintage = MAG 2023 RTP, control-totaled to Gardner Vintage 2022.** MAG's Utah-County
   city-sum matches Gardner **V2022** to ±2 persons and runs 3–5.5% below Gardner **V2025**
   (the Nov-2025 revision came after the RTP). Compare to Gardner V2022 for consistency; see
   `SOURCES.md`. Never blend with the Gardner V2025 rows in `utah_county/`.
2. **8 null-value rows preserved** (Draper + Woodland Hills jobs, all years) — blank `value`,
   not 0.
3. **City grain only.** The annual TAZ grain (`TAZ_SE_RTP23`, 2019–2050) is too fine to
   federate — catalogued in `../gis/index.csv`, not here.
4. **No county/region rollup row** (source publishes none; summing would fabricate). Use
   Gardner county modules for county totals.
5. **Households not federated** (MAG publishes them only at TAZ grain — see `../gis/`).

## Refresh

Re-pull `Population_Projections_by_City` / `Employment_Projections_by_City` FeatureServer/0,
refresh `raw/`, append as a new `vintage`, re-run the Gardner sanity check. See `SOURCES.md`.
