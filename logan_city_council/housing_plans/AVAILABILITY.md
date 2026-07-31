# Logan housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.
City: **Logan, Cache County, Utah** (USU college town). Site `loganutah.gov` (Revize CMS; file CDN `cms9files.revize.com/loganut/`).

## What EXISTS and was retrieved (7 PDFs, ~97 MB in `raw/`)

### City of Logan — Community Development (Revize CMS)
Discovered from the live Community-Development **Projects & Plans** page
`https://www.loganutah.gov/government/departments/community_development/projects_and_plans.php`.
All city docs are hosted on the Revize CDN `cms9files.revize.com/loganut/departments/comdev/...`.

- **Logan 2045 General Plan (ADOPTED)** — 155 pp, current adopted General Plan (file timestamp 2026-05-18). Born-digital. **Contains the statutorily-required Moderate Income Housing element** as a section of its "Housing and Neighborhoods" chapter (p.45).
- **Moderate Income Housing Plan (2022) — Resolution No. 22-46** — 123 pp, the standalone adopted MIH element, adopted 2022-11-15 (Utah Code 10-9a-403/408 as revised by HB 462 2022). Born-digital.
- **Biennial Moderate-Income Housing Report (2018)** — 21 pp, the City's own pre-HB462 biennial MIH element review filing on the State of Utah reporting form. Born-digital.

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`.
HCD publishes **statewide compilation PDFs** of every municipality's filed MIH annual report (one PDF per report year), **not** per-city files. Logan is included in each:

- **2023 reports** compilation (1109 pp) — Logan = **PDF pp. 367–372**.
- **2024 reports** compilation (1030 pp) — Logan = **PDF pp. 354–366**.
- **2025 reports** compilation (1303 pp) — Logan = **PDF pp. 456–467**.
- **SB 34 Municipal Progress Summaries** (199 pp, 2019–2021 window) — Logan = **PDF p. 73** (single page).

Logan-specific pages were extracted to `text/logan-<year>-mih-annual-report.txt` (and `text/logan-sb34-progress-summary.txt`); the full compilations are retained verbatim in `raw/`.

## Page-range brackets (audit trail — how each Logan range was verified)
Compilations are ordered by municipality; the range was bracketed by the neighboring cities to
guard against alphabetization bleed. **`North Logan city` is a separate municipality** and was
excluded in every file.

- **2023** — Logan report begins at the form header on PDF idx 366 (page 367); Magna begins at PDF idx 372 (page 373). Range 367–372. Verified 0 "Magna"/"Lindon" strings in the sidecar.
- **2024** — `Logan city` header at PDF idx 353 (page 354); `Magna city` at PDF idx 366 (page 367). Range 354–366. Sidecar 0 Magna/Lindon.
- **2025** — `Logan city` header at PDF idx 455 (page 456); `Magna city` at PDF idx 467 (page 468). Range 456–467. `North Logan city` is at PDF idx 545 (page 546) — not included. Sidecar 0 Magna/Lindon.
- **SB 34** — `LOGAN, CITY` block at PDF idx 72 (page 73); `MAGNA, METRO TOWNSHIP` at PDF idx 73 (page 74). Single page. Sidecar 0 Magna.

## Is the MIH plan standalone or a General-Plan chapter?
**Both forms exist, and both were retrieved.** Logan maintains a **standalone** Moderate Income
Housing Plan (2022, Resolution 22-46, `doc_type=mih_element`), AND the current **Logan 2045
General Plan (2026)** incorporates a Moderate Income Housing **element/section** within its
"Housing and Neighborhoods" chapter that references and builds on the 2022 MIHP. This matches
Utah Code 10-9a-403, which requires the MIH plan to be an *element of the general plan*.

## What was NOT found / gaps (honest gaps are data)

- **`https://www.loganutah.gov/sitemap.xml` — 404.** The prescribed sitemap crawl returned HTTP 404
  (both `.gov` and legacy `.org` redirect to the same 404). Discovery instead proceeded from the live
  Community-Development Projects & Plans page (found via web search + direct navigation). Recorded, not faked.
- **Per-city standalone annual-report PDFs on the state site.** HCD only publishes the annual
  **statewide compilations** (`NNreports.pdf`) plus the SB 34 summary — there is no jobs.utah.gov page
  hosting an individual "Logan 2024 MIH report.pdf". The compilation IS the filed report of record.
  This is EXPECTED, not a gap.
- **Reporting years 2019–2022 as standalone state compilations.** The `.../reporting/` index today
  links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary. Earlier individual-year
  compilations are not linked (superseded); the SB 34 summary covers the 2019–2021 window, and Logan's
  own 2018 biennial filing (retrieved from the city) covers the prior period. Not retrieved (not on the current index).
- **A separate HCD "compliance letter" to Logan.** HCD does not publish per-city compliance letters;
  compliance is expressed through the SB 34 progress summary (retrieved as the `compliance_letter` proxy)
  and the review embedded in each annual compilation.
- **Prior General Plan (LoganGenPlan v20).** The superseded prior General Plan is still live on the CDN
  (`.../document_center/Planning Zoning/LoganGenPlan v20 low for web.pdf`, 25.8 MB; and a high-res
  `.../departments/comdev/LoganGenPlan v20 high.pdf`, 68.9 MB). **Not retrieved** — superseded by the
  adopted 2026 Logan 2045 General Plan, which is the plan of record. Both probed 200/application-pdf;
  logged here for future backfill if the historical plan is ever needed.

## Queries / URLs tried (audit trail)
- Probe: `https://www.loganutah.gov/sitemap.xml` → 404; `https://www.loganutah.org/sitemap.xml` → 404 (redirects to .gov 404).
- WebSearch: "Logan Utah city General Plan moderate income housing element loganutah.gov community development".
- City pages fetched: `.../community_development/projects_and_plans.php` (live — GP 2026, MIHP 2022, 2018 biennial links),
  `.../community_development/planning_and_zoning/documents.php` (older v20 GP + downtown plans).
- City page 404 (old path): `https://www.loganutah.gov/151/Community-Development`.
- State pages: `jobs.utah.gov/housing/affordable/moderate/reporting/` and `.../index.html`.
- Probes confirmed `content-type: application/pdf` (HTTP 200) for all seven downloaded files and the two
  un-retrieved v20 GP files before any decision.
- Full byte-level provenance for every download: `raw/_fetch_log.jsonl` (url, status, bytes, sha256, content_type, final_url, retrieved_utc).
