# wfrc_mpo / projects — sources & provenance

`projects.csv` is ONE normalized attribute table of Wasatch Front Regional Council
transportation projects across **two program families**:

- **TIP** — the Transportation Improvement Program (the short-range, fiscally-constrained
  4-6 year list of programmed/funded projects), **8 vintages** 2020-2025 … 2027-2032.
- **RTP** — the long-range **2023-2050 Regional Transportation Plan** (the adopted
  30-year vision), roadway + transit + active-transportation projects.

**Attribute data only — no geometry is mirrored.** Every row's `source_url` is a live
ArcGIS REST query that returns that exact record (`?where=OBJECTID=<oid>&outFields=*&f=json`);
the geometry endpoints are catalogued in `../gis/index.csv`. Raw per-layer attribute
snapshots (returnGeometry=false) are in `raw/`.

## Publisher / org

All layers are WFRC ArcGIS Online org **`taguadKoI1XFwivx`** (`services1.arcgis.com`).
Service catalog (470 services, retrieved & byte-verified 2026-07-20):
<https://services1.arcgis.com/taguadKoI1XFwivx/ArcGIS/rest/services?f=json>
Human portal: <https://wfrc.org/maps-data/>.

## Column mapping (the shared 15-col schema — identical to the MAG module)

`entity,plan_kind,plan_vintage,project_id,name,mode,improvement_type,jurisdiction,county,phase_or_year,cost,status,description,source_layer,source_url`

### TIP rows (`plan_kind=tip`)
| out column | TIP source field (name varies by vintage — see below) |
|---|---|
| plan_vintage | service year span, e.g. `2026-2031` |
| project_id | `pin` (WFRC Project Identification Number); `OID<n>` fallback if pin null |
| name | `pin_desc` |
| mode | *(blank — TIP has no mode field)* |
| improvement_type | `proj_typ_nm` / `PROJ_TYP_N` (e.g. Roadway, Transit, Other) — **blank for the 2020-2025 vintage, which lacks the field** |
| jurisdiction | *(blank — TIP has no jurisdiction field)* |
| county | `cnty_name` |
| phase_or_year | `forecast_st_yr` / `FORECAST_S` (programmed forecast start year) |
| cost | `project_value` / `PROJECT_VA` — parsed to a number (strips `$`/commas) |
| status | `pin_stat_nm` / `PIN_STAT_N` (Scoping, Awarded, Under Construction, Close Out, …) |
| description | `public_desc` / `PUBLIC_DES` |

**TIP field-name drift across vintages (handled case-insensitively):** early vintages use
UPPERCASE truncated names (`PIN_DESC`, `PROJ_TYP_N`, `PIN_STAT_N`, `FORECAST_S`,
`PROJECT_VA`, `CNTY_NAME`, `PUBLIC_DES`); the 2026-2031 and 2027-2032 vintages use lowercase
full names (`pin_desc`, `proj_typ_nm`, …). The **2020-2025** vintage is the odd one: single
polyline layer, `PROJECT_VA` stored as a numeric Double, a `PROJ_LOC` location string
instead of `proj_typ`, and **no project-type field** (improvement_type left blank).

### RTP rows (`plan_kind=rtp`, `plan_vintage=RTP2023-2050`)
Sourced from the six explicitly-2023-named project layers (service descriptions confirm
"…in the Wasatch Front Regional Council 2023-2050 Regional Transportation Plan"):
| out column | RTP source field |
|---|---|
| project_id | `unique_id` (stable plan id, e.g. `W-B-2023-R-2`); `plan_id`/`OID<n>` fallback |
| name | `name` |
| mode | `mode` (Highway / Transit / Active Transportation) |
| improvement_type | `improvement_type` (New Construction, Widening, Operations, …) |
| jurisdiction | `jurisdiction` (mostly `WFRC`; some AT projects carry a city) |
| county | `county` |
| phase_or_year | `phase` (RTP build-phase band 1-4 → time bands to 2050) |
| cost | `cost` (base-year **2019 $**, unphased). *`cost_phased` (year-of-expenditure, inflated) is NOT carried — the shared schema has one cost column; query the endpoint for cost_phased.* |
| status | `status19vs23` — **the project's change status relative to the 2019 RTP** (New/Existing/Updated), NOT a delivery/construction status. Blank on the AT layers (no such field). |
| description | `description` |

## Layer inventory (all counts verified live 2026-07-20)

| plan_vintage | service(s) | rows |
|---|---|---|
| tip 2020-2025 | `TIP20202025_gdb` L0 (lines) | 995 |
| tip 2021-2026 | `TIP20212026_gdb` L0 (lines) | 362 |
| tip 2022-2027 | `TIP20222027_gdb` L0/L1 (lines+points) | 261 |
| tip 2023-2028 | `TIP_2023_2028_gdb` L0/L1 | 298 |
| tip 2024-2029 | `TIP_2024_2029_gdb` L0/L1 | 342 |
| tip 2025-2030 | `TIP_2025_2030_gdb` L0/L1 | 387 |
| tip 2026-2031 | `TIP_2026_2031_gdb` L0/L1 | 340 |
| tip 2027-2032 | `TIP_2027_2032` L0/L1 | 714 |
| rtp RTP2023-2050 | roadway lines(394)+points(91), transit lines(69)+points(33), AT lines(731)+points(129) | 1,447 |
| **total** | | **5,146** |

TIP projects appear as separate **lines** (corridor) and **points** (spot) features within a
vintage — both are distinct projects (no double-count); `source_layer` records which.

## Honest notes & gaps

- **The 2020-2025 TIP is broader than the WFRC region.** Its counties include Utah,
  Washington, Cache, etc. — it is effectively a statewide/STIP-inclusive snapshot. Later
  vintages are WFRC-region-focused (Salt Lake, Davis, Weber, Box Elder, Tooele, Morgan,
  plus `Various`/`Statewide`). Rows are kept verbatim; filter by `county` if you need
  WFRC-only.
- **cost is blank, never 0, for 83 rows** where the source value was empty / non-numeric /
  literally 0 (`blank never 0` rule). 5,063 of 5,146 rows carry a numeric cost.
- **RTP `cost` is base-2019 $; `phase_or_year` is a phase band, not a calendar year.** For
  TIP, `phase_or_year` IS a calendar year (the programmed forecast start year). The two
  program families use the column differently by design — read with `plan_kind`.
- **RTP vintages are NOT blended.** Only the adopted **2023-2050** RTP is ingested. A
  parallel thinner-schema family (`Roadway_Line_Projects`, `Transit_Line_Projects`,
  `Active_Transportation_Lines`/`_Point_Projects`) exists with different field names
  (`ProjectID/Project/ProjType/Lanes2019/Lanes2050/Cost2019`) and blank service
  descriptions — an unlabeled/earlier representation. It was **NOT ingested** to avoid
  blending an unverified vintage; catalogued here for reference only.
- **RTP2027 is a DRAFT next cycle** (`CITYAREA_RTP27_gdb`, `COUNTY_RTP27_gdb`,
  `RTP2027_PreferredScenario_*`). NOT ingested — it is the **refresh seam**, catalogued in
  `../gis/index.csv`. When RTP2027 is adopted, add it as `plan_vintage=RTP2027-…`, never
  merged into the RTP2023 rows.
- MAG (Mountainland AG, Utah County) runs a parallel `MAG_Roadway_lines_gdb` /
  `MAG_Transit_lines_gdb` set in this same WFRC org — those belong to the sibling MAG
  module, not here.

## PIN → statewide expansion path (documented 2026-07-22)

The TIP layers are extracted from **UDOT's ePM**, and `pin` (the WFRC/UDOT Project
Identification Number) is the **UDOT ePM PIN — the statewide join key**. What this does and
does NOT buy:

- **Statewide PIN-keyed project data** lives at UDOT's **UPlan open-data hub**
  (<https://data-uplan.opendata.arcgis.com>) — the "ePM All Projects" layer, refreshed
  daily. A `pin` here joins WFRC's programmed projects to the statewide project universe.
- **Legacy `maps.udot.utah.gov` EPM REST endpoints are UNSTABLE** (404s observed
  2026-07-22). **Always re-resolve service ids from the Hub item pages; never hard-code**
  the old REST URLs.
- **NO public PIN-keyed obligation/expenditure dataset exists.** UDOT's TIGS layer is
  project-lifecycle status only (no expenditure fields); Transparent Utah is keyed by state
  finance codes, not PIN. **Obligation dollars come only from WFRC's Federal Obligation
  Report PDFs** (`../plans/`, FFY2023 + FFY2024) — by construction, not a gap to close by
  joining PIN.
- A derived per-project lifecycle layer is intended to live in **`derived/`** (built by
  `build_project_history.py`, being added in parallel) — reference it there once present.

## Refresh

Re-run `raw/`-regeneration by re-querying each service `…/FeatureServer/<id>/query?where=1=1&
outFields=*&returnGeometry=false&f=json` (page at 2000). When a new TIP vintage service
appears (e.g. `TIP_2028_2033`), add it to the vintage map; when RTP2027 is adopted, ingest
it as a new `plan_vintage`.
