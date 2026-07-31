# South Jordan housing_plans — availability & gap record

**As-of:** 2026-07-06 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (6 PDFs, ~40 MB in `raw/`)

### City of South Jordan (CivicPlus / CivicEngage CMS — `www.sjc.utah.gov`)
Discovered via the **Planning & Zoning** page (sitemap crawl → `/334/Planning-Zoning`, section
**"General Plan & Supporting Documents"**). Note: `sitemap.xml` does **not** list a standalone
General Plan page; the General Plan + MIH plan are `DocumentCenter/View/<id>` links inside the
Planning-Zoning page body, so the sitemap crawl had to descend to `/334`.

- **South Jordan City General Plan** (`DocumentCenter/View/812`) — 95 pp, born-digital text,
  current adopted plan ("Plan Together, Grow Together"; replaces the 2010 plan). PDF
  CreationDate 2020-01-31, re-saved 2025-10-13. No single adoption date/resolution is printed
  in the document itself — dated **2020** by PDF creation + the "since the 2010 plan" framing.
- **Moderate Income Housing Plan and Housing Study** (`DocumentCenter/View/8116`), published as
  **General Plan Appendix A** — 41 pp, born-digital text. Zions Public Finance "Housing Report"
  dated **December 2024**, labeled "(2025)" on the city page, PDF created 2025-03-05. Contains
  the MIH **Goals & Strategies element** required by **Utah Code 10-9a-403(2)(b)(iii)** (the
  "Appendix A: MIH Strategies" menu, doc p.28) plus the AFFH / demographics / housing-supply /
  permits study behind it. This is the city's current **MIH element**.

Other General Plan appendices on the same page (B Transportation Master Plan 2025, C Public
Outreach 2018, D Existing Conditions 2018, E Large Maps 2020, Sub-Areas Plan, TRAX/FrontRunner
Station Area Plans) are supporting land-use studies, **not** the housing element — not retrieved
(out of scope for this source; the adopted General Plan + its MIH Appendix A are the record).

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`
HCD publishes **statewide compilation PDFs** of every municipality's filed MIH annual report
(one PDF per report year), **not** per-city files. South Jordan is included in each; its
alphabetical block was extracted to `text/south_jordan-<year>.txt`:

- **2023 reports** compilation — South Jordan = PDF pp. **757–770** (South Ogden begins on 770).
- **2024 reports** compilation — South Jordan = PDF pp. **692–717** (South Ogden begins on 717).
  *(The 2024 compilation packs city blocks tightly; an initial pp.692–737 bracket wrongly
  swept in South Ogden + South Salt Lake and was corrected to 692–717.)*
- **2025 reports** compilation — South Jordan = PDF pp. **868–886** (South Ogden begins on 886).
- **SB 34 Municipal Progress Summaries 2019–2021** — South Jordan = **entry #69** (AOG/MPO WFRC),
  PDF pp. **141–142** (South Ogden begins on 143).

Boundary pages of each range may share a few lines with the neighboring city's report — this is
the compilation's own packed layout and is noted in each sidecar's header. Full compilations are
retained verbatim in `raw/`.

## What was NOT found / gaps (expected, not scraper misses)

- **A standalone per-city South Jordan state report PDF.** HCD only publishes the annual
  **statewide compilations** (`NNreports.pdf`) + the SB 34 summary — there is no jobs.utah.gov
  page hosting an individual "South Jordan 2024 MIH report.pdf". The compilation IS the filed
  report of record. **This absence is expected, not a gap.**
- **Reporting years 2019–2022 as standalone compilations.** The `.../reporting/` index today
  links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary. Earlier individual-year
  compilations are superseded / not linked; the SB 34 summary covers the 2019–2021 window.
- **A separate HCD "compliance letter" to South Jordan.** HCD does not publish per-city
  compliance letters; compliance is expressed through the SB 34 progress summary + the review
  notes embedded in each annual compilation. The SB 34 summary is recorded as the
  `compliance_letter` proxy.
- **An explicit General Plan adoption date/resolution in the document.** None is printed; dated
  2020 by PDF metadata + internal framing. If a precise adoption resolution is needed, cross-ref
  `meeting_minutes/all_votes.csv` for a General Plan adoption/amendment motion.

## Queries / URLs tried (audit trail)
- Sitemap crawl: `https://www.sjc.utah.gov/sitemap.xml` (200, 70 KB) → planning-adjacent pages
  (`/334/Planning-Zoning`, `/526/City-Wide-Master-Plans`, `/509/Redevelopment-Agency-Housing-Programs`,
  `/347/Community-Development-Block-Grant`). No standalone General Plan page in the sitemap.
- Page fetched: `/334/Planning-Zoning` → "General Plan & Supporting Documents" section with the
  `DocumentCenter/View/812` (General Plan) + `View/8116` (Appendix A — MIH Plan & Housing Study)
  links. `/526/City-Wide-Master-Plans` links out to the Municode code book (`southjordan.municipalcodeonline.com`), not the General Plan.
- Probes confirmed `content-type: application/pdf` for both city docs and HEAD-sized the four
  state files (23=4.27 MB, 24=3.73 MB, 25=12.46 MB, sb34=4.78 MB) before download.
- `screen_corpus.py text/` → clean (0 replacement-char / PUA / mojibake / stub; flagged only the
  expected repeated footers, justified-text hyphen breaks, and page-range mid-content ends).
