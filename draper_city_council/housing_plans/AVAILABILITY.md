# housing_plans — what exists, what doesn't (as-of 2026-07-13)

Source 2 of `expand-city-sources` for **Draper City**. What was checked, what was found,
and the honest gaps. Draper's MIH obligations: Utah Code **10-9a-403** (MIH element in the
General Plan, HB 462 2022) and **10-9a-408** (annual implementation reports to DWS HCD).

## What was checked

1. **City site** (`draperutah.gov`, custom Azure-edge CMS, browser UA): crawled
   `sitemap.xml` (nothing under `moderate|housing`), then the two master-plans pages
   (`/city-government/public-records-and-plans/master-plans/` and
   `/business-development/planning-and-development/master-plans/`), the public-records,
   plans-and-records, and planning-and-development pages. The live site posts exactly
   **two** relevant documents: the **General Plan** ("2019 General Plan", file
   `draper-city-general-plan-v2025.pdf`) and the **2025 MIH report**.
2. **Internet Archive Wayback** (CDX prefix scans of `draperutah.gov/DocumentCenter/`
   and `draperutah.gov/media/` filtered on housing/moderate/general-plan): recovered the
   **2020, 2022, 2023, 2024 annual reports**, all dead on the live site after the
   CivicPlus→custom-CMS migration. (Recovery detail per row in `index.csv` notes.)
3. **State repository** (Utah DWS HCD, `jobs.utah.gov/housing/affordable/moderate/reporting/`):
   the four statewide compilations, **copied sha256-verified from
   `bluffdale_city_council/housing_plans/raw/`** rather than re-downloaded (see CLAUDE.md).

## Draper presence in the state compilations — CONFIRMED every year

| State file | Reporting year | Draper present? | Physical pages | Bleed |
|---|---|---|---|---|
| `sb34.pdf` (SB 34 summaries 2019–2021) | 2019–2021 | YES — summary #15, 3 required items | 29 | none (2-up; Eagle Mountain starts p30) |
| `23reports.pdf` (1109 pp) | 2023 | YES | 139–155 | p139 head = ~4 lines Cottonwood Heights tail; p155 tail = Eagle Mountain header (this year's format has no per-city title pages; reports share pages) |
| `24reports.pdf` (1030 pp, 2-up) | 2024 | YES | 126–136 | none |
| `25reports.pdf` (1303 pp) | 2025 | YES | 175–195 | none |

The state publishes **compilations only, no per-city files** — Draper's excerpts are
extracted to `text/draper-{2023,2024,2025}.txt` + `text/draper-sb34-2019-2021.txt`.
Absence of a standalone per-city state file is expected, not a gap.

## What Draper publishes / what exists

- **General Plan** — adopted 2019-11-19 (Ord. #1412); the retained file is the current
  amended edition (Housing Element amendments Ord. #1561 2022-09-20 and Ord. #1623
  2024-09-17; Station Area Plans incorporated by Ords #1635/#1670/#1692; Water element
  #1694). LIVE.
- **MIH element** — **no standalone element PDF is published.** The element exists as
  (a) General Plan **Chapter 4 "Housing (2024)"** (current, as amended) + Appendix A
  (Sept 2022 MIH Study), and (b) the as-adopted 2022 package (signed Ord. #1561 + Study)
  preserved inside the 2022 annual report. Both indexed as `mih_element` excerpt rows.
- **Annual reports** — 2020, 2022, 2023, 2024 (all Wayback-recovered), 2025 (live).
  Draper posts each year's filing but the CMS keeps only the newest online.

## Honest gaps

- **2021 annual report: UNRECOVERED** (`unrecovered.csv`). A pre-migration link existed;
  the only Wayback captures of the replacing document are payload-truncated at 1 MiB and
  unreadable. The period is covered at summary level by Draper's sb34.pdf page.
- **No HCD compliance/notice-of-compliance letter** is posted anywhere on the city site
  or findable via Wayback (bluffdale, by contrast, posts one). Draper's compliance
  *status* is therefore not asserted here — the 2023 city filing itself says the
  Division "is reviewing the report". Absence of the letter is a publishing gap, not
  evidence either way.
- **Older General Plan editions** (v2022 `media/hsdmxc0k`, v2024 `media/x1wekkss`,
  ~47 MB each) survive only in Wayback; not retained (the amendments table in the
  current edition records what changed and when). Re-fetchable from the capture list if
  ever needed.
- A pre-migration **"Moderate Income Housing FAQ"** (DocumentCenter/View/14405, Wayback
  20240229015212) exists but is outside the §9 doc_type vocabulary; not retained.
