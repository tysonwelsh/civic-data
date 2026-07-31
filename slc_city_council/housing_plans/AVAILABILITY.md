# Salt Lake City housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (11 documents, ~90 MB in `raw/`)

### City of Salt Lake City (sites: `slc.gov` / `slcdocs.com`)
SLC is a large city with a dedicated housing function (Community & Neighborhoods → Housing Stability
Division / Housing & Neighborhood Development "HAND"). It publishes **standalone five-year housing
plans**, not a numbered general-plan housing chapter. Documents discovered via the Planning Division
citywide-plans page (`slc.gov/planning/general-plans/citywide-plans/`) and the Growing SLC page
(`slc.gov/can/growingSLC/`), then fetched from `slcdocs.com` / `slc.gov/hand/...` uploads.

- **Plan Salt Lake (adopted 2015-12-01)** — the adopted **citywide General Plan** (2040 vision;
  13 Guiding Principles incl. Housing). `doc_type=general_plan`.
- **Growing SLC: A Five-Year Housing Plan 2018-2022 (adopted 2017-12-12, Ord. 71 of 2017)** — the
  **standalone housing plan** for 2018-2022; SLC's first housing plan since the 2000 Community
  Housing Plan. Full version with attachments. `doc_type=mih_element`.
- **Ordinance No. 71 of 2017** — the signed adopting ordinance (image-only scan → OCR).
  `doc_type=mih_element`.
- **Housing SLC 2023-2027 (effective July 2023)** — the **CURRENT standalone five-year housing
  plan**, replacing Growing SLC; filed under Planning > General Plans > Housing (functions as SLC's
  HB462 moderate-income-housing element). `doc_type=mih_element`.
- **Thriving in Place: SLC's Anti-Displacement Strategy (adopted 2023-10-17)** — companion adopted
  housing-element strategy (PROTECT/PRESERVE/PRODUCE). `doc_type=mih_element`.
- **SLC 2021 Annual MIH Reporting Form** + **SLC 2021 MIH Plan-Report (narrative)** — city-published
  copies of SLC's 2021 annual MIH implementation report (Utah Code 10-9a-408).
  `doc_type=mih_annual_report`.

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes
**statewide compilation PDFs** (one per report year), not per-city files. Salt Lake City is present
in each — extracted as a page-range sidecar; full compilations retained verbatim in `raw/`:

- **2023 reports** compilation — SLC = PDF **fitz pp. 642-680** (Salt Lake County starts 681).
- **2024 reports** compilation — SLC = PDF **fitz pp. 605-631** (printed pp. ~1211-1263).
- **2025 reports** compilation — SLC = PDF **fitz pp. 765-784** (Salt Lake County starts 785).
- **SB 34 Municipal Progress Summaries 2019-2021** — SLC STRATEGIES block = PDF **fitz pp. 122-131**
  (`compliance_letter` proxy).

## What was NOT found / gaps (findings, not failures)

- **A moderate-income-housing chapter inside Plan Salt Lake.** SLC's general plan (Plan Salt Lake) is
  a short (50 pp.) vision/principles document; the MIH element is delivered as the **separate**
  Growing SLC / Housing SLC plans. This is a *structural* fact, not a gap — verified by reading Plan
  Salt Lake (housing is Guiding Principle, not a standalone statutory element) and by finding Housing
  SLC filed under Planning > General Plans > Housing.
- **A single HCD "compliance letter" to Salt Lake City.** HCD does not publish per-city compliance
  letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.
- **Standalone per-city annual-report PDFs on the state site.** HCD only publishes the annual
  statewide compilations (`NNreports.pdf`) + the SB 34 summary — no `jobs.utah.gov` page hosts an
  individual "Salt Lake City 2024 MIH report.pdf". The compilation IS the filed report of record.
- **City-published annual MIH reports for years other than 2021.** Only the 2021 forms are posted on
  the HAND uploads path that was discoverable; 2022-2025 city filings are captured via the HCD
  statewide compilations above (2023/2024/2025) rather than as separate city PDFs.
- **2019-2022 standalone state compilations.** The `.../reporting/` index today links only 23/24/25
  `reports.pdf` + the 2019-2021 SB 34 summary; earlier individual-year compilations are not linked
  (superseded). SB 34 (2019-2021) + the city 2021 report cover the earlier window.

## Notes / caveats
- **Growing SLC file naming:** the signed-ordinance PDF is named `...No17-2019.pdf` on the city
  server, but the document itself is **Ordinance No. 71 of 2017** (adopted 2017-12-12). Source
  filename preserved verbatim; index `title`/`notes` record the true ordinance number.
- **Compilation header bleed:** the state compilations interleave adjacent municipalities
  (Salt Lake County follows SLC alphabetically). Sidecars are convenience extracts by the recorded
  fitz page range; the full compilation in `raw/` is authoritative.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Discovery trail (audit)
- Pages fetched: `slc.gov/can/growingSLC/`, `slc.gov/planning/general-plans/citywide-plans/`
  (yielded Plan Salt Lake, Housing SLC 2023-2027, Thriving in Place URLs). `slc.gov/can/housingplan`
  and `slc.gov/housingstability/838-2/` returned 404 (stale slugs).
- WebSearch: "Growing SLC Five-Year Housing Plan PDF"; "Plan Salt Lake general plan 2015 PDF";
  "Thriving in Place anti-displacement plan adopted PDF".
- State: `jobs.utah.gov/housing/affordable/moderate/reporting/` (23/24/25 `reports.pdf` + `sb34.pdf`);
  SLC presence confirmed by page-level header search in every compilation before extraction.
