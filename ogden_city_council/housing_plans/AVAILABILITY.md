# Ogden housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

Ogden City (Weber County, ~87k pop.) is above the 10,000 threshold, so under Utah Code
§§ 10-9a-403 / 408 (as strengthened by HB 462, 2022) it MUST maintain a Moderate Income
Housing (MIH) element in its general plan and file annual MIH implementation reports with
the state. Both were located and retrieved.

## What EXISTS and was retrieved (6 documents, ~101 MB in `raw/`)

### City of Ogden (site: `www.ogdencity.gov` — CivicPlus; `.com` 301→`.gov`)
Discovered by crawling `https://www.ogdencity.gov/sitemap.xml` → Planning pages
(`/541/City-Plans`, `/2434/Housing-Element---Moderate-Income-Housin`,
`/2809/Plan-Ogden`), and by following the direct `DocumentCenter/View/24462` URL that
Ogden itself printed in its 2025 state MIH filing. Documents are served as
`www.ogdencity.gov/DocumentCenter/View/<id>/<slug>`.

- **Ogden City General Plan (August 2002; 2020 update; consolidated 847-page PDF)** —
  `general_plan`, `DocumentCenter/View/1031`. The current **adopted** plan of record.
- **General Plan Chapter 7 — Housing (amended 2022)** — `mih_element`,
  `DocumentCenter/View/24462`. Contains Ogden's **Moderate Income Housing element +
  Implementation Plan** (sec. G cites 10-9a-403(2)(b); strategies with "Actions Taken as
  of 2022" and 2022-2025 timelines including station area plans). This is the exact file
  Ogden cites in its state filings as its "general plan, moderate income housing element."

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD
publishes **statewide compilation PDFs** (one per report year), not per-city files. Ogden
is present in each; pages sidecar-extracted to `text/ogden-<year>-*.txt`, full
compilations retained verbatim in `raw/`:

- **2023 reports** compilation — Ogden = PDF pp. 486-498 (`mih_annual_report`).
- **2024 reports** compilation — Ogden = PDF pp. 461-470 (`mih_annual_report`).
- **2025 reports** compilation — Ogden = PDF pp. 586-597 (`mih_annual_report`).
- **SB 34 Municipal Progress Summaries 2019-2021** — Ogden = PDF pp. 93-94
  (`compliance_letter` proxy).

## Standalone vs. chapter (the key structural finding)

Ogden's MIH element is **a chapter of the general plan**, published as its own PDF
(`View/24462` = "7. Housing"), NOT a wholly separate stand-alone document. The full
consolidated General Plan (`View/1031`) is a different, larger PDF that embeds Housing as
Chapter 7. Both are retained. There is **no** separately-numbered "Moderate Income
Housing Plan" document distinct from the general plan Housing chapter.

## What was NOT found / gaps (findings, not failures)

- **The adopting ordinance/resolution for the MIH element (Ordinance 2023-8) as a public
  file.** In Ogden's 2025 state filing, the "Link to adoption resolution or ordinance"
  field is a **local network path** (`file:///X:/Planning/.../Pages from Ordinance 2023-8
  moderate income housing.pdf`), not a public URL — so it is not publicly retrievable. The
  MIH element PDF (`View/24462`) is the public artifact of record; the adopting ordinance
  text lives in Ogden's municipal code (American Legal `codelibrary.amlegal.com`), which
  is the scope of the separate `ordinances` source type, not this dataset.
- **Per-city standalone annual-report PDFs on the state site.** HCD publishes only the
  statewide `NNreports.pdf` compilations + the SB 34 summary — there is no
  `jobs.utah.gov` page hosting an individual "Ogden 2024 MIH report.pdf". The compilation
  IS the filed report of record; cite the Ogden page range. MIH filing contact:
  `mih@utah.gov`; Ogden filer Brandon Rypien (Senior Planner).
- **Reporting years 2019-2022 as standalone compilations.** The `.../reporting/` index
  today links only 23/24/25 `reports.pdf` + the 2019-2021 SB 34 summary; earlier
  individual-year compilations are not linked (superseded). The SB 34 summary covers the
  2019-2021 window.
- **A separate HCD "compliance letter" to Ogden.** HCD issues no per-city compliance
  letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.
- **The comprehensive "Plan Ogden" rewrite as an adopted plan.** `/2809/Plan-Ogden` is an
  **in-progress** citywide-vision / general-plan-update project (not yet adopted); it
  publishes no consolidated adopted PDF. The 2020-update General Plan remains the adopted
  plan. Not retrieved as an adopted document because none exists yet.

## Extraction notes

- Both city PDFs are **born-digital** (Housing element ~2,116 chars/pg; General Plan
  ~1,705 chars/pg — far above the "chars/page < 100 ⇒ OCR" gate) → full `pdftotext
  -layout` sidecars. No OCR was required for any document.
- State compilations → **Ogden page-range** sidecars only; full compilations kept in
  `raw/`. The **2023** compilation splits question/answer across pages (Ogden range opens
  mid-answer); the **2024** compilation is a **two-up merged** layout (two printed page
  numbers + a right-hand generic-instruction column per PDF page). Sidecars are
  convenience extracts — the page range in the full compilation is authoritative.
- `screen_corpus.py` on `text/`: **clean** — 0 cid-artifacts / PUA-garbled / mojibake /
  long-tokens; only advisory flags (repeated gov header/footer lines; page-range extracts
  ending mid-sentence; 1 stray replacement char in the 2.7 MB General Plan sidecar).
  dict_ratio median 0.76.

## Discovery / URLs tried (audit trail)

- Sitemap crawl: `https://www.ogdencity.gov/sitemap.xml` (175 KB) → Planning page slugs.
- City pages fetched: `/541/City-Plans` (yielded `View/1031` GP + `View/24462` chapter
  set), `/2434/Housing-Element---Moderate-Income-Housin` and `/2809/Plan-Ogden`
  (both JS-rendered CivicPlus pages exposing no static document links).
- Direct doc URLs from Ogden's own 2025 state filing: `DocumentCenter/View/24462`.
- State: `jobs.utah.gov/housing/affordable/moderate/reporting/documents/{23,24,25}reports.pdf`,
  `.../sb34.pdf`. Ogden presence + exact page range confirmed by page-level text search in
  every compilation before extraction (bracketed against North Ogden / South Ogden / Orem
  to avoid same-name bleed).
