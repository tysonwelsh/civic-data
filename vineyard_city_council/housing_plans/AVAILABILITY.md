# Vineyard housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (7 documents, ~156 MB in `raw/`)

### City of Vineyard (site: `vineyardutah.gov` — Revize CMS; documents served from `cms3.revize.com/revize/vineyard/…` and, for the codified plan, `municipalcodeonline.com` S3)
Discovery: crawled `https://www.vineyardutah.gov/sitemap.xml` (a legacy `.php`/Revize sitemap that still enumerates the `Departmnts/Planning/…` document tree), then fetched the live Planning page `https://www.vineyardutah.gov/government/planning.php` and the Community Development page for the document links.

- **Vineyard City General Plan (General Plan Update, May 2019)** — the adopted General Plan the city's Planning page links (151-page born-digital PDF, ~70 MB). **The Moderate Income Housing element is a CHAPTER inside it** (printed pp. 98-107), not a standalone document. The living/codified plan is also published as an online book at `vineyard.municipalcodeonline.com/book?type=plan` (a JS app with no static/PDF snapshot).
- **Future Land Use Map** — the General Plan's statutory land-use map (single-page vector PDF, ~68 MB; densities directly bear on housing capacity). Linked from the same Planning page.
- **Ordinance 2022-17 (adopted 2022-09-14)** — General Plan amendment updating the **Moderate Income Housing element to align with Utah Code 10-9a-403** (post-HB 462): goals, strategies, and an action plan with timeframes. **This is the current MIH element of record.** Planning Commission hearing 2022-09-07; Council adoption 2022-09-14 (Mayor Julie Fullmer).

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes **statewide compilation PDFs** (one per report year), not per-city files. Vineyard is present in each:

- **2023 reports** compilation — Vineyard = PDF pp. 968-978.
- **2024 reports** compilation — Vineyard = PDF pp. 907-915 (2-up merged layout).
- **2025 reports** compilation — Vineyard = PDF pp. 1122-1132.
- **SB 34 Municipal Progress Summaries 2019-2021** — Vineyard = PDF pp. 176-177 (`compliance_letter` proxy).

Vineyard pages were sidecar-extracted to `text/vineyard-<year>-*.txt`; the full compilations are retained verbatim in `raw/`.

## Is MIH standalone or a General Plan chapter?

**A General Plan element/chapter, not a standalone plan.** It first appears as the "Moderate Income Housing" chapter of the 2019 General Plan Update (printed pp. 98-107), then was updated in place by a General Plan amendment, **Ordinance 2022-17 (2022-09-14)**, to satisfy Utah Code 10-9a-403 after HB 462. Vineyard publishes no separate "Moderate Income Housing Plan" PDF; Ord 2022-17 is the closest thing to a standalone MIH-element document and is recorded as `mih_element`.

## What was NOT found / gaps (findings, not failures)

- **A standalone Moderate Income Housing Plan PDF.** Does not exist — the MIH element lives inside the General Plan (2019 chapter, amended by Ord 2022-17). Verified: sitemap document tree, Planning page, Community Development page, and web search surface only the GP PDF, the online codified plan, and Ord 2022-17.
- **A published FrontRunner Station Area Plan (SAP).** Vineyard's 2024 and 2025 state MIH reports describe a Station Area Plan for the FrontRunner-station / Utah City (Downtown Vineyard) area as **in progress** ("Completion of the SAP is expected …"; consultant Avenue Consultants awarded Sept 2023). No adopted SAP document was published on the city site as of 2026-07-05 — recorded as a forward gap, not retrieved.
- **A PDF snapshot of the online codified General Plan.** `vineyard.municipalcodeonline.com/book?type=plan` is a JS single-page app; it renders no static HTML or consolidated PDF to retain. The retained plan artifacts are the 2019 GP PDF + the Ord 2022-17 amendment.
- **Per-city standalone annual-report PDFs on the state site.** HCD publishes only the annual statewide compilations (`NNreports.pdf`) + the SB 34 summary. The compilation IS Vineyard's filed report of record. Filings contact: `mih@utah.gov`.
- **Reporting years 2019-2022 as standalone compilations.** The `.../reporting/` index today links only 23/24/25 `reports.pdf` + the 2019-2021 SB 34 summary; earlier individual-year compilations are not linked. SB 34 (2019-2021) covers the earlier window.
- **A separate HCD "compliance letter" to Vineyard.** HCD does not publish per-city compliance letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.

## Boundary / bleed notes for the state compilations
The HCD compilations concatenate one shared MIH-report form per jurisdiction, so at a city's last page adjacent-jurisdiction narrative can bleed onto the same physical page. For **2023 reports**, the trailing page (PDF p.979) began a rural-county narrative ("rural residents … roadway projects") and was **trimmed** from Vineyard's sidecar. **2024 reports** uses a 2-up merged layout (printed page numbers 1812-1829 across Vineyard's range). Treat every `text/vineyard-*-mih-annual-report.txt` as a **page-range convenience extract**; the full compilation in `raw/` is authoritative.

## Queries / URLs tried (audit trail)
- Sitemap crawl: `https://www.vineyardutah.gov/sitemap.xml` → `Departmnts/Planning/Vineyard General Plan.pdf`, `Departmnts/Planning/Future Land Use Map.pdf`.
- City pages fetched: `/government/planning.php` (GP PDF, Future Land Use Map, online codified plan link), `/government/community_development.php`.
- Online codified plan probed: `vineyard.municipalcodeonline.com/book?type=plan` (JS app, no snapshot).
- Ordinance located via web search hit `municipalcodeonline.com-new/vineyard/plan/pdf/Ord_2022-17.pdf`; verified as the MIH-element GP amendment.
- WebSearch: "Vineyard Utah General Plan adopted moderate income housing element PDF"; "Vineyard City Utah General Plan 2023 2024 adopted moderate income housing element".
- State pages: `jobs.utah.gov/housing/affordable/moderate/reporting/` (23/24/25 `reports.pdf` + `sb34.pdf`); Vineyard presence confirmed by page-level text search in every compilation before extraction.
