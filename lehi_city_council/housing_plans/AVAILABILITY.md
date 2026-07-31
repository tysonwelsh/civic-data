# Lehi housing_plans — availability & gap record

**As-of:** 2026-07-02 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (9 PDFs, ~35 MB in `raw/`)

### City of Lehi (current site: `lehi-ut.gov` — migrated off WordPress to a new CMS with `/media/<hash>/` paths)
Discovered via the current General Plan page: `https://www.lehi-ut.gov/departments/planning-zoning/general-plan/`
(the older `wp-content/uploads/...` URLs returned by web search now **404** — the site migrated; all live docs are under `/media/`).

- **General Plan — Final Document (2022)** — 136 pp, current adopted General Plan.
- **General Plan — Land Use Map** — adopted 2011-10-25, last amended 2022-01-25.
- **General Plan — Max Density Map** — supplementary land-use map (graphic; no text layer).
- **Moderate Income Housing Element** — current MIH element; originally adopted 2017-12-12, goals/strategies/timeline **updated 2024-05-28** (HB 462 compliance).
- **Ordinance adopting the MIH Element (05/28/24)** — signed adopting ordinance (scanned image).

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`
HCD publishes **statewide compilation PDFs** of every municipality's filed MIH annual report (one PDF per report year), not per-city files. Lehi is included in each:

- **2023 reports** compilation — Lehi = pp. 341–352.
- **2024 reports** compilation — Lehi = pp. 328–341.
- **2025 reports** compilation — Lehi = pp. 430–441.
- **SB 34 Municipal Progress Summaries 2019–2021** — Lehi = entry #35 (compliance/progress summary).

Lehi-specific pages were extracted to `text/lehi-<year>-mih-annual-report.txt` for convenience; the full compilations are retained verbatim in `raw/`.

## What was NOT found / gaps

- **Per-city standalone annual-report PDFs on the state site.** HCD only publishes the annual **statewide compilations** (`NNreports.pdf`) plus the SB 34 summary — there is no jobs.utah.gov page hosting an individual "Lehi 2024 MIH report.pdf". The compilation IS the filed report of record; recorded as such.
  - Checked: `https://jobs.utah.gov/housing/affordable/moderate/index.html`, `.../reporting/` — only the compilation PDFs and a fillable form link (`feedback.utah.gov`) are exposed. Contact for filings: `mih@utah.gov`.
- **Reporting years 2019–2022 as standalone compilations.** The `.../reporting/` index today links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary. Earlier individual-year compilations are not linked (superseded); the SB 34 summary covers the 2019–2021 window. Not retrieved (not published on the current index).
- **A separate "compliance letter" to Lehi.** HCD does not publish per-city compliance letters; compliance is expressed through the SB 34 progress summary and the review notes embedded in each annual compilation. Recorded the SB 34 summary as the `compliance_letter` proxy.
- **General Plan appendices / draft written document (161 MB) and appendices (20.7 MB)** referenced on `engagelehi.org/general-plan-update` are **pre-adoption drafts**; the adopted 2022 Final Document supersedes them. Deferred (drafts, not the adopted record). The adopted Final Document + Land Use Map + Max Density Map are retained.

## Queries / URLs tried (audit trail)
- WebSearch: "Lehi Utah General Plan adopted PDF community development"; "Lehi City moderate income housing plan element Utah 10-9a-403"; "Lehi City moderate income housing plan resolution 2022 2023 HB 462 strategies adopted"; "lehi-ut.gov general plan document media planning".
- Sitemap crawl: `https://www.lehi-ut.gov/sitemap.xml` → found current planning path `/departments/planning-zoning/general-plan/` (old `/government/public-meetings/planning/general-plan/` = 404).
- City pages fetched: `/departments/planning-zoning/general-plan/` (live, 8 PDF links), `/departments/planning-zoning/area-plans/`, `engagelehi.org/general-plan-update`, `engagelehi.org/moderate-income-housing-goals-update`.
- State pages fetched: `jobs.utah.gov/housing/affordable/moderate/index.html`, `.../reporting/`.
- Probes confirmed content-type `application/pdf` for all four state files before download.
