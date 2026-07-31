# mag_mpo / projections — sources & provenance

City-grain population and employment projections for the **Mountainland Association of
Governments (MAG)** region (Utah, Summit, Wasatch counties), federated into the repo's
9-column projection schema. Values are lifted **verbatim** from MAG's ArcGIS Hub feature
services; nothing is modeled, interpolated, summed, or fabricated. Nulls are preserved.

## Primary source

MAG ArcGIS Hub (`data.magutah.gov`, hosted org `services2.arcgis.com/EiGeaCDLpVDPqdJ5`):

- **Population Projections by City** — service `Population_Projections_by_City` (layer
  `CityPop`), FeatureServer/0. Service description (verbatim): *"These are the adopted MAG
  2023 RTP population projections by city for the years 2020, 2030, 2040, and 2050 for
  Summit County, Utah County, and Wasatch County, Utah."*
  <https://data.magutah.gov/datasets/mountainland::population-projections-by-city>
- **Employment Projections by City** — service `Employment_Projections_by_City` (layer
  `CityEmp`), FeatureServer/0.
  <https://data.magutah.gov/datasets/mountainland::employment-projections-by-city>

Both retrieved 2026-07-20 (raw JSON in `raw/`). 41 geographies each (38 municipalities +
3 "Unincorporated <County>").

## Schema mapping

| source field | CSV | notes |
|---|---|---|
| `City` | `geography` | verbatim |
| — | `geography_type` | `city_area` for municipalities; `unincorporated_area` for the 3 "Unincorporated …" rows |
| `Population_YYYY` / `Employment_YYYY` | `value` at `year`=YYYY | YYYY ∈ {2020,2030,2040,2050} |
| — | `metric` | `population` (pop service) / `jobs` (employment service) |
| — | `scenario` | `baseline` (single adopted forecast) |
| — | `vintage` | `MAG 2023 RTP (adopted 2023)` |

**328 rows** = 41 geographies × 4 years × 2 metrics. Metric split: population 164, jobs 164.
**8 null-value rows preserved** (blank `value`, never 0): employment for **Draper** (the
small Utah-County slice of Draper) and **Woodland Hills** is null in the source for all four
years.

## Vintage — the 2023 RTP SE forecast = Gardner Vintage 2022 control totals

These by-city figures are the **city aggregation of MAG's TAZ-level socioeconomic forecast**
(`TAZ_SE_RTP23`, annual 2019–2050) that underpins the adopted **2023 Regional Transportation
Plan**. The TAZ grain (1,330 zones for Utah County alone) is **too fine to federate** and is
catalogued instead in `../gis/index.csv` (MAG TAZ Population/Employment/Household Forecast) —
module-level reference only. Only the CITY grain is federated here.

### Sanity check vs the in-repo Gardner county totals (read-only)

Summing MAG's Utah-County geographies (26 city + unincorporated rows) and comparing to the
Gardner Institute Utah-County population already in `utah_county/projections/`:

| year | MAG city-sum | Gardner V2022 | Δ vs V2022 | Gardner V2025 | Δ vs V2025 |
|---|---|---|---|---|---|
| 2020 | 664,258 | 664,258 | **+0.0%** | — | — |
| 2030 | 853,713 | 853,711 | **+0.0%** (±2) | 882,276 | −3.2% |
| 2040 | 1,021,075 | 1,021,077 | **−0.0%** (±2) | 1,054,164 | −3.1% |
| 2050 | 1,185,677 | 1,185,679 | **−0.0%** (±2) | 1,254,910 | −5.5% |

**Finding (not a mismatch):** MAG's 2023 RTP city forecast is **control-totaled to Gardner
Vintage 2022** — the two agree to within ±2 persons (city-level rounding). It therefore runs
3–5.5% **below** the newer Gardner **Vintage 2025** (which revised Utah County up in Nov
2025, after the RTP was adopted). This is the expected relationship and confirms the vintage
label. When comparing MAG city projections to a county total, use **Gardner Vintage 2022**
for an apples-to-apples check; do not read the MAG numbers as reflecting the 2025 revision.
(This check is validation only — no summed county row was written to the CSV.)

## Honest gaps (what is NOT here)

- **No county or MAG-region total rows.** The by-city service publishes only individual
  cities + "Unincorporated <County>" — no published county/region rollup. County totals
  would require summing (fabrication) and are therefore **omitted**; for a county total use
  the Gardner rows in `utah_county/`, `summit_county/`, and (Wasatch has no in-repo county
  module) the MAG per-county TAZ services catalogued in `../gis/`.
- **No household grain federated.** MAG publishes households only at the TAZ grain
  (`Household_Projections_(…County)`), not by city — catalogued in `../gis/`, not federated.
- **Decadal snapshots only** (2020/2030/2040/2050) at the city grain; the annual series
  lives at the TAZ grain (not federated).
- **`population` = total resident population** at the city grain (the TAZ source field is
  household population `HHPOP`; the by-city service aggregates to total population and its
  Utah-County sum matches Gardner's *total* population, confirming it is total, not HH-only).

## Refresh

MAG re-publishes the by-city forecast with each RTP cycle. On the next RTP: re-pull both
FeatureServer/0 layers (`?where=1=1&outFields=*&returnGeometry=false&f=json`), refresh
`raw/`, append as a new `vintage`, and keep this vintage for comparison. Re-run the Gardner
sanity check against whichever Gardner vintage the new RTP control-totals to.
