# ut_state / projections — sources & provenance

All values in `ut_state_projections.csv` are **extracted verbatim** from the Kem C.
Gardner Policy Institute's long-term **State**-and-county projection workbooks — the same
files already in the repo at `salt_lake_county/projections/`, read at their **state
("Utah State") grain** instead of the county grain. Nothing here is modeled, interpolated,
or fabricated. Every row carries its exact `source_url` and `vintage`.

## Primary source — Kem C. Gardner Policy Institute (University of Utah)

The Gardner Institute produces the **official Utah long-term demographic and economic
projections**, funded by the Utah Legislature with GOPB, the Legislative Fiscal Analyst,
and the state Associations of Governments. A new long-term ("Utah 2065"-style) vintage is
released roughly every four years as a public Excel workbook covering the **State of Utah
plus all 29 counties**. Two vintages are captured here so the CSV spans real historical
base years through the latest 40-year horizon and shows how the outlook shifted between
releases.

### Vintage 2025 (release: November 2025) — CURRENT
- Landing page: <https://gardner.utah.edu/utah-demographics/population-projections/utah-2065-long-term-vintage-2025/>
- **Data workbook (Excel):** <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2025/11/Gardner-Policy-Institute-State-and-County-Projections-2025-2065-Data.xlsx>
  (byte-verified 2026-07-20: 194,054 bytes, MD5 `e088357b1460c7f1e25c6599254e671b`)
- **Horizon:** annual 2025 → 2065. State-of-Utah rows in CSV: 5-year snapshots 2025–2065.

### Vintage 2022 (release: January 2022) — PRIOR
- Long-term index: <https://gardner.utah.edu/demographics/population-projections/long-term/>
- **Data workbook (Excel):** <https://gardner.utah.edu/wp-content/uploads/Gardner-Policy-Institute-State-and-County-Projections-2020-2060-Data.xlsx>
  (byte-verified 2026-07-20: 232,141 bytes, MD5 `8b5d2787e0469ae58bfacd00a38d19c1`)
- **Horizon:** base years **2010 & 2015** (historical) + annual 2020 → 2060 projections.
  CSV includes 2010/2015 (historical base) and 5-year snapshots to 2060.

These are the identical files documented in `salt_lake_county/projections/SOURCES.md`
(reused per instruction — not re-derived).

## What was extracted

The workbook's **`Demographic Detail`** sheet is one row per geography × year; the
**`Total Employment by County`** sheet gives Total Jobs. For geography **`Utah State`**
the seven metrics pulled are:

| workbook column | CSV `metric` |
|---|---|
| Population | `population` |
| Households | `households` |
| Persons Per Household | `persons_per_household` |
| Household Population | `household_population` |
| Group Quarters Population | `group_quarters_population` |
| Median Age | `median_age` |
| Total Jobs (employment sheet) | `jobs` |

All years are dated **July 1** (workbook `File Layout` note). `geography` = `State of Utah`,
`geography_type` = `state`. Counts are integers; `persons_per_household` and `median_age`
are decimals. **140 rows** (Vintage 2025: 9 years × 7 = 63; Vintage 2022: 11 years × 7 = 77).
Cross-check: Vintage-2025 2065 population = **5,550,525**, matching Gardner's public
"5.6 million by 2065" headline.

The full annual series (every year, births/deaths/net migration/age bands, all 29 counties
+ state) lives in the linked workbooks and is **not** re-hosted here (bulk-data discipline).

## Scenario column — honest finding (single baseline)

The task anticipated published **scenario variants** at the state grain. **These public
State-and-County long-term workbooks do not contain them.** The `Demographic Detail` sheet
is **one row per geography × year — there is no scenario dimension**; `Utah State` has a
single series, exactly as the counties do. Gardner's high/low sensitivity figures (e.g.
"if net migration ceased, the 2065 population would be ~4 million") appear only as
**narrative statements in companion briefs/PPTX**, not as a machine-readable time series in
this or any downloadable long-term workbook found here. Per the repo's cardinal rule
(never fabricate), **`scenario` is `baseline` for every row**; no high/low/alternative rows
were invented. If Gardner later publishes an explicit multi-scenario state workbook, add
those rows with the variant name in `scenario`.

## GOPB

GOPB does not publish an independent numeric state projection distinct from Gardner's; it
co-produces the Gardner set and runs the qualitative "Guiding Our Growth"
(<https://gopb.utah.gov/guiding-our-growth/>) scenario-visioning effort — not a numeric
time series. Nothing distinct to add.

## Honest gaps (what is NOT here)

- **Single baseline scenario** (see above) — the honest headline gap.
- **No housing-unit projection.** Gardner projects *households* (occupied units), not total
  housing units; `households` is the closest published proxy. No vacancy/stock figure.
- **State grain only.** Sub-state / MPO / county detail is available (county grain is in
  `salt_lake_county/projections/`; small-area is WFRC's Real Estate Market Model, not yet
  ingested).
- **Vintages before 2022 not captured** (2017, 2015 superseded).

## Retrieval note

Gardner landing pages 403 to plain fetchers; the cloudfront `d36oiwf74r1rap.cloudfront.net`
asset URLs serve the Excel files directly (`curl -A "Mozilla/5.0"`). Extraction:
`openpyxl` over the `Demographic Detail` + `Total Employment by County` sheets, filtering
`Geography == "Utah State"`.
