# salt_lake_county / projections — Salt Lake County population & housing projections

Small, high-value structured table of **long-term population, household, and employment
projections for Salt Lake County** from the **Kem C. Gardner Policy Institute** (University
of Utah) — Utah's official state-and-county projection series. Use this for growth/housing
demand context: how many people, households, and jobs the county is projected to hold
through 2065, and how the outlook shifted between the 2022 and 2025 vintages.

## Files

- `salt_lake_county_projections.csv` — **canonical.** Long-format, one row per
  geography × year × metric × vintage. Values lifted verbatim from the Gardner Excel
  workbooks (see `SOURCES.md`). Never hand-edit numbers; re-extract from the linked source.
- `SOURCES.md` — full provenance: exact source names, download URLs, vintages/release
  dates, the workbook-column → metric mapping, and honest gaps.

## CSV schema

| column | meaning |
|---|---|
| `geography` | `Salt Lake County` (only geography present) |
| `geography_type` | `county` |
| `year` | projection/estimate year (July-1 dated), 5-year snapshots |
| `metric` | `population`, `households`, `persons_per_household`, `household_population`, `group_quarters_population`, `median_age`, `jobs` |
| `value` | the figure (integer for counts; decimal for `persons_per_household`, `median_age`) |
| `scenario` | `baseline` (Gardner publishes one baseline at the county grain) |
| `source` | `Kem C. Gardner Policy Institute — Utah State and County Long-Term Projections` |
| `source_url` | exact Excel workbook URL the value came from |
| `vintage` | `Vintage 2025 (Nov 2025)` or `Vintage 2022 (Jan 2022)` |

## Coverage

- **Vintage 2025 (Nov 2025) — current:** 2025 → 2065 (5-year snapshots).
- **Vintage 2022 (Jan 2022) — prior:** historical base 2010 & 2015 + 2020 → 2060.
- 7 metrics per year. ~140 rows total.

## Caveats — read before quoting

1. **Projections are estimates, not counts.** Values past the release year are modeled
   forecasts; treat as scenario, not fact. Always state the `vintage` when citing.
2. **Two vintages coexist by design — filter to one.** The same year (e.g. 2030, 2050)
   appears under both vintages with *different* values (the 2025 vintage revised the
   county's near-term population **down** vs 2022 while pushing job growth **up**). For a
   single current view, filter `vintage LIKE 'Vintage 2025%'`. Never mix vintages in one
   trend line.
3. **`households` ≠ housing units.** Gardner projects occupied households, not total
   housing units; there is no vacancy/housing-stock projection here (honest gap).
4. **County grain only.** No city/sub-county rows — small-area forecasts come from WFRC
   (not yet ingested; see `SOURCES.md`).
5. **Verbatim source layer.** Follows the repo's cardinal rules: values are city/agency-
   faithful and never overwritten in place. Corrections, if ever needed, belong in a
   documented override, not an edit to the numbers.

## Refresh

Gardner issues a new long-term vintage roughly every 4 years. On the next release: grab the
new `...State-and-County-Projections-<yrs>-Data.xlsx`, extract the Salt Lake County rows
for the seven metrics (browser User-Agent needed — see `SOURCES.md`), append as a new
`vintage`, and keep prior vintages for comparison.
