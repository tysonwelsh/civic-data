# Utah County / projections — sources & provenance

All values in `utah_county_projections.csv` are **extracted verbatim** from the
Kem C. Gardner Policy Institute's long-term state-and-county projection data workbooks
(the same statewide files Salt Lake County's projection layer uses — one workbook per
vintage covers every Utah county). Nothing here is modeled, interpolated, or fabricated.
Every row carries its exact `source_url` and `vintage`.

## Primary source — Kem C. Gardner Policy Institute (University of Utah)

The Gardner Institute produces the **official Utah long-term demographic and economic
projections**, funded by the Utah Legislature in collaboration with the Governor's Office
of Planning & Budget (GOPB), the Office of the Legislative Fiscal Analyst, and the state's
Associations of Governments. A new long-term ("Utah 2065"-style) vintage is released
roughly every four years; county-level detail is published as a single public Excel
workbook covering all 29 counties + the state. **There is no separate GOPB county
projection** — Gardner is the shared official set.

Two vintages are captured so the CSV spans real historical base years through the latest
40-year horizon, and so a user can see how the outlook shifted between releases. The two
vintages are kept **strictly separate** (never blended) — the same year appears under both
with different values.

### Vintage 2025 (release: November 2025) — CURRENT
- Landing page: <https://gardner.utah.edu/utah-demographics/population-projections/utah-2065-long-term-vintage-2025/>
- **Data workbook (Excel):** <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2025/11/Gardner-Policy-Institute-State-and-County-Projections-2025-2065-Data.xlsx>
- Report (PDF): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2025/11/LongTerm-Proj-Nov2025.pdf>
- **Horizon:** annual 2025 → 2065. Utah County rows in CSV: 5-year snapshots 2025–2065 (9 years).

### Vintage 2022 (release: January 2022) — PRIOR
- Long-term index: <https://gardner.utah.edu/demographics/population-projections/long-term/>
- **Data workbook (Excel):** <https://gardner.utah.edu/wp-content/uploads/Gardner-Policy-Institute-State-and-County-Projections-2020-2060-Data.xlsx>
- Report (PDF): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/LongTermProj-Jan2022.pdf>
- **Horizon:** the workbook carries base years **2010 & 2015** (historical) plus annual
  2020 → 2060 projections. CSV includes 2010/2015 (historical base) and 5-year snapshots
  to 2060 (11 years).

## Raw retention

Following the Salt Lake County precedent (bulk-data discipline), the full statewide
workbooks are **link-only, not re-hosted** — the same two Gardner files serve all seven
county projection layers in this repo. Byte-verification of the exact files used (MD5,
downloaded 2026-07-20 with a browser User-Agent):

| vintage | file | MD5 | size |
|---|---|---|---|
| 2025 | `Gardner-Policy-Institute-State-and-County-Projections-2025-2065-Data.xlsx` | `e088357b1460c7f1e25c6599254e671b` | 194,054 bytes |
| 2022 | `Gardner-Policy-Institute-State-and-County-Projections-2020-2060-Data.xlsx` | `8b5d2787e0469ae58bfacd00a38d19c1` | 232,141 bytes |

## What was extracted

The workbook's `Demographic Detail` sheet is one row per county × year. For Utah County we
pulled: **Population, Households, Persons Per Household, Household Population, Group Quarters
Population, Median Age**. The `Total Employment by County` sheet gave **Total Jobs**. All
years are dated **July 1**. Metric name mapping:

| workbook column | CSV `metric` |
|---|---|
| Population | `population` |
| Households | `households` |
| Persons Per Household | `persons_per_household` |
| Household Population | `household_population` |
| Group Quarters Population | `group_quarters_population` |
| Median Age | `median_age` |
| Total Jobs (employment sheet) | `jobs` |

The full annual series (every year, all 29 counties + state, plus births/deaths/net
migration/age bands) lives in the linked workbooks and is **not** re-hosted here — only the
Utah County 5-year snapshots are lifted into the CSV.

## Sanity check (against Gardner headline figures)

- **Vintage 2025 population:** 772,019 (2025) → 1,543,744 (2065), a 100.0% 40-year change.
- **Vintage 2025 jobs:** 471,008 (2025) → 752,908 (2065).
- **Vintage 2022 population:** 664,258 (2020) → 1,338,222 (2060).

These match the values in the respective Gardner workbooks cell-for-cell.

## GOPB

GOPB does **not** publish an independent numeric county population projection distinct from
Gardner's; it co-produces the Gardner set and runs the qualitative "Guiding Our Growth"
scenario-planning initiative (<https://gopb.utah.gov/guiding-our-growth/>), which is not a
county time series. Nothing distinct to add.

## Honest gaps (what is NOT here)

- **No housing-unit projection.** Gardner projects *households* (occupied units), not total
  *housing units*. `housing_units` is therefore absent — `households` is the closest
  published proxy. Do not treat households as a housing-unit (incl. vacancy) count.
- **County-level only — no sub-county / city / small-area rows.** The Gardner long-term set
  stops at the county. Small-area forecasts are produced by the relevant MPO/Association of
  Governments (WFRC/MAG for the Wasatch Front; Dixie MPO for Washington; Cache MPO). Not
  yet ingested — a future-work candidate for a sub-county tier.
- **Single baseline scenario.** The public county workbooks give one baseline projection (no
  published high/low migration variants at the county grain), so `scenario` is `baseline`
  for every row.
- **Vintages before 2022 not captured.** Earlier vintages (2017, 2015) exist but are
  superseded; only the two most recent long-term releases are included.

## Retrieval note

Gardner landing pages 403 to plain fetchers; retrieve with a browser User-Agent
(`curl -A "Mozilla/5.0" <url>`). The cloudfront `d36oiwf74r1rap.cloudfront.net` asset URLs
serve the Excel/PDF files directly.
