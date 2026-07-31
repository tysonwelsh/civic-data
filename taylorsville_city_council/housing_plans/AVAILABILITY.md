# Taylorsville housing_plans — availability & gap record

**As-of:** 2026-07-06 · **Source 2 (moderate-income housing plans + General Plan + state
annual reports)** of `expand-city-sources`. Additive dataset — modifies no existing layer.

## What EXISTS and was retrieved (14 PDFs, ~172 MB in `raw/`)

### City of Taylorsville (CivicPlus / CivicEngage Central CMS — `www.taylorsvilleut.gov`)
The site **403s a bare bot UA** (recon risk); every fetch went through `polite_fetch.py`
(browser UA). Discovery via the CMS `sitemap.xml` → sitemap index → `sitemap-page-1.xml`
(160 page URLs), which listed a live standalone **`/government/general-plan`** page and a
**`/government/community-development/moderate-income-housing-plan`** page.

- **Taylorsville General Plan (updated 2025)** — published as **9 separate chapter PDFs**
  (`/home/showdocument/<id>`, wrapped on-page in a docaccess.com viewer), all born-digital
  text, PDFs exported Oct/Nov 2025. Dated **2025** by Chapter 3's own wording ("the updated
  2025 Taylorsville General Plan"):
  1 Introduction (11621), 2 Community Character (11623), 3 Land Use (11625),
  4 Mobility (**11619** — id out of numeric order), 5 Economic Prosperity (11627),
  6 Parks and Open Space (11629), 7 Neighborhoods (11631),
  **8 Moderate Income Housing (11633 — the MIH element)**, 9 Environmental Stewardship (11635).
- **General Plan Chapter 8 — Moderate Income Housing** is the **MIH element** required by
  **Utah Code 10-9a-403** (contains §8.4 State Moderate Income Housing Requirements +
  strategies). Retrieved as `doc_type=mih_element`, dated 2025 (PDF exported Nov 5 2025).
- **Standalone adopted MIH plan** — the community-development MIH page's "click the button
  above" link resolves (in static HTML, behind the JS docbox widget) to
  `Home/ShowDocument?id=3679`: **Ordinance No. 23-03**, *An Ordinance Approving an Amendment
  to Taylorsville General Plan Chapter 8 — Moderate Income Housing*, **PASSED Feb 1, 2023**
  (Planning Commission recommended **6-0** on Jan 24 2023). 70 pp, born-digital; bundles the
  adopting ordinance + the full Chapter 8 MIH text + strategies. Recorded as a second
  `mih_element` (the formally-adopted 2023 version; superseded in element form by the 2025
  General Plan Chapter 8). **Joins to `meeting_minutes/all_votes.csv` by 2023-02-01.**

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD
publishes **statewide compilation PDFs** of every municipality's filed MIH annual report
(one PDF per report year), **not** per-city files. Taylorsville is included in each; its
alphabetical block (**Syracuse → Taylorsville → Tooele**) was extracted to
`text/taylorsville-<year>.txt`. Page ranges bracketed by the next city's header:

| Report | PDF (pp) | Taylorsville pages | Boundary markers | Contamination check |
|---|---|---|---|---|
| 2023 | `23reports.pdf` (1109) | **895–911** | Syracuse ends p894; TVille header "Type of Jurisdiction" p895; Tooele County p912 | 34 TVille / 0 Syracuse / 0 Tooele |
| 2024 | `24reports.pdf` (1030) | **854–861** | Syracuse ends p853; "Taylorsville city / Who is filling out this report?" p854; Tooele city p862 | 14 / 0 / 0 |
| 2025 | `25reports.pdf` (1303) | **1033–1045** | Syracuse ends p1028; "Taylorsville city" p1033 (filed by Jim Spung); Tooele city p1046 | 30 / 0 / 0 |
| SB 34 | `sb34.pdf` (199) | **158–166** | SYRACUSE p157; TAYLORSVILLE CITY p158 (County: Salt Lake, AOG/MPO: WFRC); TOOELE CITY p167 | 69 / 0 / 0 |

Every sidecar is grep-clean of the two adjacent city names — no alphabetical bleed. Full
compilations retained verbatim in `raw/`.

## Known artifact (source, not extraction)
- **SB 34 pages 165–166** (Taylorsville's strategy matrix) render as image / broken-encoding
  **mojibake in the compilation PDF itself** (`screen_corpus.py` flagged the sb34 sidecar's
  `weird_char_ratio`). The substantive strategy narrative on **p158–164 extracts clean**;
  `raw/sb34.pdf` retains the pages as-published. Not a fetch/extraction defect.

## What was NOT found / gaps (expected, not scraper misses)
- **A standalone per-city Taylorsville state report PDF.** HCD only publishes the annual
  **statewide compilations** (`NNreports.pdf`) + the SB 34 summary; there is no jobs.utah.gov
  page hosting an individual "Taylorsville 2024 MIH report.pdf". The compilation IS the filed
  report of record. **Absence is expected, not a gap.**
- **Report years 2019–2022 as standalone compilations.** The `.../reporting/` index today
  links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary. The SB 34 summary covers
  the 2019–2021 window.
- **A separate HCD "compliance letter" to Taylorsville.** HCD publishes no per-city
  compliance letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.
- **A single consolidated General Plan PDF.** Taylorsville publishes the plan only as 9
  chapter PDFs; there is no one-file General Plan. All 9 chapters were retrieved.
- **An explicit General Plan adoption ordinance/date inside the document.** The chapters do
  not print an adoption resolution; dated **2025** by Chapter 3's own "updated 2025
  Taylorsville General Plan" wording + Oct/Nov 2025 PDF export dates. (Resolution #10-19 named
  in Chapter 1 is a 2010 Wasatch-Choice endorsement, unrelated to plan adoption.) The MIH
  element's adoption IS documented — Ordinance 23-03, Feb 1 2023 (the standalone doc).

## Queries / URLs tried (audit trail)
- `sitemap.xml` (200, sitemap index) → `sitemap-page-1.xml` (200, 160 `<loc>`s) → grepped for
  general-plan / housing / MIH / planning pages. Two direct hits used.
- `/government/general-plan` (200, 121 KB) → 9 `showdocument` chapter links (docaccess viewer).
- `/government/community-development/moderate-income-housing-plan` (200, 94 KB) → docbox widget;
  the button target `Home/ShowDocument?id=3679` (Ord 23-03) recovered from the static HTML.
- State files fetched by the stable generic pattern
  `jobs.utah.gov/housing/affordable/moderate/reporting/documents/{23,24,25}reports.pdf` + `sb34.pdf`.
- `screen_corpus.py text/` → clean (0 replacement-char / PUA / mojibake / stub / read-error);
  flagged only expected chaptered-PDF repeated footers, sb34 hyphen breaks, page-range
  mid-content ends, and the sb34 p165–166 source garble noted above.
