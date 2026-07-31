# salt_lake_county / projections — sources & provenance

All values in `salt_lake_county_projections.csv` are **extracted verbatim** from the
Kem C. Gardner Policy Institute's long-term state-and-county projection data workbooks.
Nothing here is modeled, interpolated, or fabricated. Every row carries its exact
`source_url` and `vintage`.

## Primary source — Kem C. Gardner Policy Institute (University of Utah)

The Gardner Institute produces the **official Utah long-term demographic and economic
projections**. The work is funded by the Utah Legislature and done in collaboration with
the Governor's Office of Planning & Budget (GOPB), the Office of the Legislative Fiscal
Analyst, and the state's Associations of Governments. A new long-term ("Utah 2065"-style)
vintage is released roughly every four years; county-level detail is published as a public
Excel workbook. **There is no separate GOPB county projection** — Gardner is the shared
official set (see "GOPB" below).

Two vintages are captured here so the CSV spans real historical base years through the
latest 40-year horizon, and so a user can see how the outlook shifted between releases.

### Vintage 2025 (release: November 2025) — CURRENT
- Landing page: <https://gardner.utah.edu/utah-demographics/population-projections/utah-2065-long-term-vintage-2025/>
- **Data workbook (Excel):** <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2025/11/Gardner-Policy-Institute-State-and-County-Projections-2025-2065-Data.xlsx>
- Report (PDF): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2025/11/LongTerm-Proj-Nov2025.pdf>
- Slides (PPTX): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2025/11/Gardner-Institute-Projections-Nov2025.pptx>
- Projections summary (PDF, Mar 2026): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/2026/03/ProjectionsSummary-Mar2026.pdf>
- **Horizon:** annual 2025 → 2065. Salt Lake County rows in CSV: 5-year snapshots 2025–2065.

### Vintage 2022 (release: January 2022) — PRIOR
- Long-term index: <https://gardner.utah.edu/demographics/population-projections/long-term/>
- **Data workbook (Excel):** <https://gardner.utah.edu/wp-content/uploads/Gardner-Policy-Institute-State-and-County-Projections-2020-2060-Data.xlsx>
- Report (PDF): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/LongTermProj-Jan2022.pdf>
- Salt Lake County fact sheet (PDF): <https://d36oiwf74r1rap.cloudfront.net/wp-content/uploads/Salt-Lake-Proj-Feb2022.pdf>
- **Horizon:** the workbook carries base years **2010 & 2015** (historical) plus annual
  2020 → 2060 projections. CSV includes 2010/2015 (historical base) and 5-year snapshots
  to 2060. These early years reflect the estimates embedded in the Vintage-2022 file, not
  a later revision.

## What was extracted

The Gardner workbook's `Demographic Detail` sheet is one row per county × year. For
Salt Lake County we pulled: **Population, Households, Persons Per Household (avg household
size), Household Population, Group Quarters Population, Median Age**. The
`Total Employment by County` sheet gave **Total Jobs**. All years are dated **July 1**
(workbook `File Layout` note). Metric name mapping:

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
migration/age bands) lives in the linked Excel workbooks and is **not** re-hosted here
(bulk-data discipline) — only the Salt Lake County 5-year snapshots are lifted into the CSV.

## GOPB (Governor's Office of Planning & Budget)

GOPB does **not** publish an independent numeric county population projection that differs
from Gardner's. It co-produces the Gardner set and runs a separate *scenario-planning*
initiative, "Guiding Our Growth" (<https://gopb.utah.gov/guiding-our-growth/>), which is
qualitative/survey-based future-visioning, not a county time series. Nothing distinct to
add to the CSV; noted for completeness.

## Honest gaps (what is NOT here)

- **No housing-unit projection.** Gardner projects *households* (occupied units), not total
  *housing units*. `housing_units` is therefore absent — `households` is the closest
  published proxy. Do not treat households as a housing-unit (incl. vacancy) count.
- **County-level only — no sub-county / city / small-area rows.** The Gardner long-term
  set stops at the county. Small-area (city, traffic-analysis-zone) projections for Salt
  Lake County are produced by the **Wasatch Front Regional Council (WFRC)** in the Real
  Estate Market Model / socioeconomic forecast (<https://wfrc.org/>, MAG mirror
  <https://magutah.gov/mag-population-projections/>). Not yet ingested — a future-work
  candidate for a sub-county tier.
- **Single baseline scenario.** The public county workbooks give one baseline projection
  (no published high/low migration variants at the county grain), so `scenario` is
  `baseline` for every row. Experimental/alternative Gardner runs exist only at the state
  level.
- **Vintages before 2022 not captured.** Earlier vintages (2017, 2015) exist but are
  superseded; only the two most recent long-term releases are included.
- The Feb-2022 Salt Lake County fact-sheet PDF is a graphic (non-extractable text); its
  numbers are the same as the Vintage-2022 workbook, which is the source used.

## Retrieval note

Gardner landing pages 403 to plain fetchers; retrieve with a browser User-Agent
(`curl -A "Mozilla/5.0" <url>`). The cloudfront `d36oiwf74r1rap.cloudfront.net` asset
URLs serve the Excel/PDF files directly.
