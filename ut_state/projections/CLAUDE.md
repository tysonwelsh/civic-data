# ut_state / projections — Utah statewide population & housing projections

Small, high-value structured table of **long-term population, household, and employment
projections for the State of Utah** from the **Kem C. Gardner Policy Institute** — Utah's
official state-and-county projection series, read at STATE grain. Use for statewide
growth/housing-demand context and as the top-of-hierarchy denominator above the county
(`salt_lake_county/projections/`) and city tiers.

## Files

- `ut_state_projections.csv` — **canonical.** Long-format, one row per geography × year ×
  metric × vintage. Values lifted verbatim from the Gardner Excel workbooks (see
  `SOURCES.md`). Never hand-edit numbers; re-extract from the linked source.
- `SOURCES.md` — full provenance (URLs + MD5s), the workbook-column → metric mapping, the
  scenario finding, and honest gaps.

## CSV schema (repo 9-col projection schema)

`geography, geography_type, year, metric, value, scenario, source, source_url, vintage`

- `geography` = `State of Utah`; `geography_type` = `state`.
- `metric` ∈ {population, households, persons_per_household, household_population,
  group_quarters_population, median_age, jobs}.
- `scenario` = `baseline` (see caveat 2).
- `vintage` = `Vintage 2025 (Nov 2025)` or `Vintage 2022 (Jan 2022)`.

## Coverage

- **Vintage 2025 (current):** 2025 → 2065 (5-year snapshots).
- **Vintage 2022 (prior):** historical base 2010 & 2015 + 2020 → 2060.
- 7 metrics/year. **140 rows.**

## Caveats — read before quoting

1. **Projections are estimates, not counts.** Values past the release year are modeled;
   always state the `vintage` when citing.
2. **Single baseline scenario — no scenario variants in the source.** The public Gardner
   long-term workbook has NO scenario dimension at state grain (one series per year), so
   every row is `baseline`. High/low sensitivity numbers exist only as narrative in
   Gardner briefs, not as a machine-readable series — they were deliberately NOT
   fabricated into rows. Details in `SOURCES.md`.
3. **Two vintages coexist by design — filter to one.** The same year appears under both
   vintages with different values; never mix vintages in a trend line. For a current view,
   filter `vintage LIKE 'Vintage 2025%'`.
4. **`households` ≠ housing units** (occupied households only; no vacancy/stock — honest gap).
5. **Verbatim source layer.** Values are source-faithful and never overwritten in place;
   corrections belong in a documented override, not an edit to the numbers.

## Refresh

Gardner issues a new long-term vintage ~every 4 years. On the next release: grab the new
`...State-and-County-Projections-<yrs>-Data.xlsx`, extract the `Utah State` rows for the
seven metrics (browser User-Agent — see `SOURCES.md`), append as a new `vintage`, keep
prior vintages. If a future workbook adds explicit scenario columns at state grain, ingest
them with the variant name in `scenario`.
