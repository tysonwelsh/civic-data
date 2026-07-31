# Orem housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (14 documents / 15 raw files, ~51 MB in `raw/`)

### City of Orem (site: `orem.gov` — WordPress; documents served from `orem.gov/wp-content/uploads/...`)
Discovered by crawling `https://orem.gov/sitemap.xml` → the WordPress sub-sitemap `wp-sitemap-posts-page-1.xml`, which exposed the relevant pages `/generalplan/`, `/longrangeplanning/`, `/housing/`, `/planning/`. PDF links were harvested from the `/generalplan/` and `/longrangeplanning/` page HTML (all under `/wp-content/uploads/2024/12/` and `/2025/...`).

- **Orem General Plan (2023 Update)** — the CURRENT adopted General Plan. **The MIH element required by Utah Code § 10-9a-403 is Chapter 4 (Housing)** — sec. 4.4 *Median-Income Housing Study* and **sec. 4.4.2 *Moderate Income Housing***. Orem publishes **no separate stand-alone "MIH element" PDF**: the element IS Chapter 4. On **2023-01-09** the City Council amended the General Plan (Resolution **R-2023-0004**) to adopt its MIH strategies. Born-digital, full `pdftotext -layout` sidecar.
- **Orem Moderate-Income Housing Study (Sept 2018)** — the housing-needs study underlying the element (Ch. 4 references it). Born-digital.
- **orem.gov/housing landing page** — living city page documenting the MIH strategies + reporting; confirms the 2023-01-09 5-strategy amendment and the 2023-08-01 report filing. Retained as HTML.
- **FrontRunner Station Area Plan (SAP) + adopting/compliance resolutions (2025)** — HB 462 (2022) requires station area plans around fixed-guideway transit as a MIH/land-use tool. Retrieved: the **SAP Report (Exhibit A, 2025-12-08)** (born-digital); **Resolution R-2025-0021** adopting it; and four **HB 462 determination-of-impracticability** artifacts for the UVX (Utah Valley Express) stations — **R-2025-0023 (Main Street)**, **R-2025-0024 (University Place)**, **R-2025-0025 (Lakeview)**, plus the **MAG SAP Policy Committee certification** of those findings (signed 2025-12 + a Nov-2025 MAG certification page). The resolutions are **signed/scanned** → OCR'd (tesseract, labeled).

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes **statewide compilation PDFs** (one per report year), **not per-city files**. Orem is present in each:

- **2023 reports** compilation — Orem = printed pp **498–508** (PDF pp 499–509); bracketed by Ogden (ends 497) and Park City (509 per the ToC on PDF p4).
- **2024 reports** compilation — Orem report starts **PDF p471** ("Orem city / Grant Allen"), ends before Park City at PDF p481; printed pp 940–959 (2-up layout).
- **2025 reports** compilation — Orem = **PDF pp 598–610** ("Orem city / Grant Allen grallen@orem.gov"), between Ogden (p586) and Park City (p611).
- **SB 34 Municipal Progress Summaries 2019–2021** — Orem = **PDF pp 95–96** (header `OREM, CITY`; County UTAH; AOG/MPO MAG; Required Items 4 / Menu 6; Major Transit Investment Corridor YES) — the `compliance_letter` proxy.

Orem pages were sidecar-extracted to `text/orem-<year>-*.txt`; the full compilations are retained verbatim in `raw/`.

## What was NOT found / gaps (findings, not failures)

- **A stand-alone Moderate Income Housing *element* PDF.** None exists — the element is **Chapter 4 of the General Plan** (verified in the born-digital text: sec. 4.4.2 Moderate Income Housing). This is expected, not a gap.
- **Resolution R-2023-0004 (the 2023 MIH-strategy adopting resolution).** Referenced *inside* Orem's 2023 state report at `http://orem.org/wp-content/uploads/2023/02/R-2023-0004.pdf`, but that URL is **dead (404)** after the CMS migration — Orem's old `/uploads/2023/02/...` tree did not survive the move to the current `/uploads/2024/12/` structure. Probed the redirect target `orem.gov/.../2023/02/R-2023-0004.pdf` and the plausible current paths `/2024/12/`, `/2023/01/`, `/2025/01/` — all 404. The strategies it adopted are captured in General Plan Ch. 4 and narrated in the annual reports; the resolution PDF itself is not retrievable from the public site as of 2026-07-05.
- **Per-city stand-alone annual-report PDFs on the state site.** HCD publishes only the annual statewide compilations (`NNreports.pdf`) + the SB 34 summary — there is no `jobs.utah.gov` page hosting an individual "Orem <year> MIH report.pdf". The compilation IS the filed report of record. Orem filer: **Grant Allen, Senior Planner (grallen@orem.gov)**.
- **Reporting years 2019–2022 as stand-alone compilations.** The `.../reporting/` index today links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary; earlier individual-year compilations are not linked (superseded). SB 34 (2019–2021) covers the earlier window.
- **A separate HCD "compliance letter" to Orem.** HCD does not publish per-city compliance letters; the SB 34 progress summary (and the MAG SAP certification for the 2025 station-area findings) are recorded as `compliance_letter` proxies.

## Candidate documents CHECKED and EXCLUDED / not retained
- **`Orem-Frontrunner-Station-SAP-Supporting-Documentation.pdf`** (linked on `/longrangeplanning/`, `/wp-content/uploads/2025/11/…`) — **160 MB** of SAP technical/appendix supporting material (public-input, exhibits). Fetched and **discarded as oversize + tangential** to the MIH record (the SAP Report itself, Exhibit A, is retained). Recorded here rather than kept in `raw/`.
- Neighbourhood/corridor sub-plans on the `/generalplan/` page (State Street Corridor Master Plan, Geneva Road/GRAP, Aspen-Timpview, etc.) are land-use sub-area plans, **not** MIH documents — out of scope for this dataset, not retrieved.

## Queries / URLs tried (audit trail)
- Sitemap crawl: `https://orem.gov/sitemap.xml` (WordPress index) → `wp-sitemap-posts-page-1.xml` → `/generalplan/`, `/longrangeplanning/`, `/housing/`, `/planning/`.
- City PDFs from `orem.gov/wp-content/uploads/2024/12/` and `/2025/11|12/` (General Plan, MIH Study, FrontRunner SAP + resolutions).
- Dead-URL probes for R-2023-0004 (see gap above).
- State: `jobs.utah.gov/housing/affordable/moderate/reporting/documents/{23,24,25}reports.pdf` + `sb34.pdf`; Orem presence confirmed by locating each city's report-start header ("Orem city / Who is filling out this report?") and the ToC before extracting the page range.
