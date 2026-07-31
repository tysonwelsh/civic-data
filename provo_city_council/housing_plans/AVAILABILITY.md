# Provo housing_plans — availability & gap record

**As-of:** 2026-07-03 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (6 PDFs, ~29 MB in `raw/`)

### City of Provo (current CMS: CivicPlus CivicEngage at `www.provo.gov`, DocumentCenter file host)
Discovered by crawling `https://www.provo.gov/sitemap.xml` → General Plan page
`https://www.provo.gov/276/General-Plan-and-Citywide-Plans`. The MIH element is **not linked on that
page** (only the GP + citywide sub-plans are); it was found via web search and lives at a higher
DocumentCenter id.

- **General Plan 2023** — `DocumentCenter/View/919` — 108 pp, current adopted General Plan
  (supersedes the 2004 plan). HOUSING chapter at p.35; goals reference Appendix B for MIH.
- **General Plan Appendix B — Moderate-Income Housing Supply and Strategies 2022-2027** —
  `DocumentCenter/View/4020` — 22 pp, the statutory **MIH element** (Utah Code 10-9a-403 / HB 462):
  strategy-menu selection, AMI/affordability analysis, chosen strategies.

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`
HCD publishes **statewide compilation PDFs** of every municipality's filed MIH annual report (one PDF
per report year), not per-city files. Provo is included in each; page ranges bracketed by the next
jurisdiction header (Providence sorts immediately before Provo, Riverdale immediately after), and the
sidecars were grep-checked for zero Providence/Riverdale bleed:

- **2023 reports** compilation (`23reports.pdf`, 1109 pp) — Provo = pp. **577–586**.
- **2024 reports** compilation (`24reports.pdf`, 1030 pp) — Provo = pp. **556–563**.
- **2025 reports** compilation (`25reports.pdf`, 1303 pp) — Provo = pp. **704–715**.
- **SB 34 Municipal Progress Summaries 2019–2021** (`sb34.pdf`, 199 pp) — Provo = menu entry **#57**
  (PROVO, CITY; AOG/MPO: MAG; TOTAL MENU ITEMS: 23) — recorded as the `compliance_letter` proxy.

Provo-specific pages were extracted to `text/provo-<year>.txt`; the full compilations are retained
verbatim in `raw/`.

## What was NOT found / gaps

- **A standalone per-city annual-report PDF on the state site.** HCD only publishes the annual
  **statewide compilations** (`NNreports.pdf`) plus the SB 34 summary — there is no jobs.utah.gov page
  hosting an individual "Provo 2024 MIH report.pdf". The compilation IS the filed report of record;
  recorded as such. (Same structure verified for Lehi/St. George/West Jordan in this repo.)
- **A separate HCD "compliance letter" to Provo.** HCD does not publish per-city compliance letters;
  compliance is expressed through the SB 34 progress summary and the review embedded in each annual
  compilation. Recorded the SB 34 summary as the `compliance_letter` proxy.
- **Reporting years before 2023 as standalone compilations.** The `.../reporting/` index today links
  only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary. Earlier individual-year compilations are
  not linked (superseded); the SB 34 summary covers the 2019–2021 window. Not retrieved.
- **The newer `www.provo.org` site** (per recon, Provo runs both `provo.gov` and the newer
  `provo.org`) is **bot-gated**: `www.provo.org/sitemap.xml` → HTTP 403 to `polite_fetch.py`, and
  `www.provo.org/departments/community-development/planning` → 403 to WebFetch. The authoritative
  planning documents are on `www.provo.gov` (CivicEngage/DocumentCenter), which is reachable; the
  MIH element + GP were both retrieved there, so provo.org being closed to bots is not a data gap.
- **Standalone Housing chapter PDF** (`DocumentCenter/View/4007/4-General-Plan_Housing-2023`) exists
  but is a subset of the General Plan 2023 already retrieved — not separately stored (redundant).
- **No adopting resolution/ordinance PDF** for the MIH element was located on the GP page or
  DocumentCenter. The MIH element document itself is dated 2022-2027; council adoption is joinable via
  `meeting_minutes/all_votes.csv` if/when the ordinance number is confirmed (see dataset CLAUDE.md).

## Queries / URLs tried (audit trail)
- Sitemaps probed: `https://www.provo.org/sitemap.xml` (403), `https://www.provo.gov/sitemap.xml`
  (200, 115 KB) → grep for housing/planning/general-plan/moderate.
- City pages fetched: `https://www.provo.gov/276/General-Plan-and-Citywide-Plans` (live; 12
  DocumentCenter links). WebFetch `https://www.provo.org/departments/community-development/planning`
  (403).
- WebSearch: `Provo City "moderate income housing" plan element Appendix B general plan Utah
  10-9a-403` → located `DocumentCenter/View/4020` (MIH element) and `.../4007` (Housing chapter).
- State pages: `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (index) — confirmed
  23/24/25 `reports.pdf` + `sb34.pdf`. `--size-only` HEAD-probes before download (4.3/3.7/12.5/4.8 MB).
- Provo presence + no-bleed confirmed in each state compilation by page-range extraction + grep
  (Provo counts 11/13/27; Providence & Riverdale bleed = 0 in all three sidecars; SB34 entry #57).
