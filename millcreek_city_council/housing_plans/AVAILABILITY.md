# Millcreek housing_plans — availability & gap record

**As-of:** 2026-07-06 · **Source 2 (moderate-income housing plans + General Plan + state annual reports)** of `expand-city-sources`.

Millcreek incorporated Dec 2016, so its entire land-use/housing record is recent (General Plan first adopted Feb 2019; MIH strategies folded in 2022) — a short history is legitimate, not a gap.

## What EXISTS and was retrieved (7 documents, ~91 MB in `raw/`)

### City of Millcreek (site: `millcreekut.gov` — CivicPlus/CivicEngage; documents served from `/DocumentCenter/View/<id>`)
Discovered by crawling `https://www.millcreekut.gov/sitemap.xml` and navigating the **Planning & Zoning page `/151`** (the `/568/Plans-and-Policies` and `/600/Affordable-Housing` pages carry only HR policies / program contacts, NOT the plan documents).

- **Millcreek Together General Plan** (`general_plan`) — `DocumentCenter/View/3193`, 140 pp. Originally adopted **Feb 2019**; URL-slug-labeled **"Sep 2022"**. **The Moderate Income Housing element is embedded in this plan** (MIH strategies/implementations folded into **Chapter 4** + a housing appendix) — Millcreek publishes **no separate standalone MIH-element PDF**. Cover text reads **"Amended December 12, 2026"** (a source date anomaly — future-dated, likely a typo/placeholder) and the body references 2023 station-area plans, so `View/3193` serves the **living/current GP**, not a frozen 2022 snapshot.
- **Ordinance 22-44** (`mih_element`) — adopted **Sept 26, 2022**; 53 pp. "AN ORDINANCE AMENDING THE MODERATE INCOME HOUSING ELEMENT OF THE GENERAL PLAN TO INCLUDE MIH STRATEGIES AND AN IMPLEMENTATION PLAN pursuant to Utah Code 10-9a-403." Body + adopted strategies/implementation exhibit — **Millcreek's MIH element of record.** Retrieved from Utah Public Notice (`utah.gov/pmn/files/893155.pdf`); born-digital text layer. Millcreek qualifies for the 6+-strategy tier (within 1/2 mi of two fixed-guideway transit stations). Joins to `meeting_minutes/all_votes.csv` on 2022-09-26.
- **Millcreek Housing Report — August 2024** (`mih_annual_report`, city copy) — `DocumentCenter/View/4489`, 47 pp. The city's own copy of its annual MIH implementation report (10-9a-408).

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes **statewide compilation PDFs** (one per report year), not per-city files. Millcreek is present in each:

- **2023 reports** compilation — Millcreek = PDF pp. **413–429**.
- **2024 reports** compilation — Millcreek = PDF pp. **399–413**.
- **2025 reports** compilation — Millcreek = PDF pp. **507–521** (clean single-column `Millcreek city` header).
- **SB 34 Municipal Progress Summaries 2019–2021** — Millcreek = PDF pp. **81–82** (`compliance_letter` proxy).

Millcreek page-ranges were sidecar-extracted to `text/millcreek-<year>-*.txt`; the full compilations are retained verbatim in `raw/`.

### Page-range CONTAMINATION check (grep of adjacent-city names in each Millcreek sidecar)
The task's "2024 compilation packs blocks" warning is real. Per-sidecar mentions:
- **2023** — Millcreek 46, **Murray 16**, South Salt Lake 2 → merged/2-up layout bleeds adjacent **Murray** column text into the range. Cite the page range, not the sidecar as Millcreek-exclusive.
- **2024** — Millcreek 129, **Murray 22**, Salt Lake County 1, South Salt Lake 3 → same 2-up bleed (heaviest).
- **2025** — Millcreek 49, Murray **1**, South Salt Lake 1 → **clean** (single-column headers). Confirms the 507–521 range.
- **SB 34** — Millcreek 24, **zero** other cities → clean (bracketed by Midway p80 / Morgan County p83).
- Some **South Salt Lake** mentions are GENUINE (Millcreek's Meadowbrook / Millcreek-TRAX **joint station-area plans** with South Salt Lake), not contamination.

## What was NOT found / gaps (findings, not failures)

- **A standalone Moderate Income Housing element/plan PDF.** Millcreek does not publish one — the MIH element lives inside the General Plan (Chapter 4 + appendix) and its adopting instrument is **Ordinance 22-44** (retained). The `mih_element` document of record is therefore the ordinance, not a separate plan file.
- **Per-city standalone annual-report PDFs on the state site.** HCD only publishes the annual statewide compilations (`NNreports.pdf`) + the SB 34 summary; there is no `jobs.utah.gov` page hosting an individual "Millcreek 2024 MIH report.pdf". The compilation page-range IS the filed report of record; the city's own Aug-2024 Housing Report is the city-side copy.
- **Reporting years 2019–2022 as standalone compilations.** The `.../reporting/` index today links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary; earlier individual-year compilations are not linked (superseded). SB 34 (2019–2021) covers the earlier window.
- **A separate HCD "compliance letter" to Millcreek.** HCD issues no per-city compliance letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.

## Candidate document CHECKED and EXCLUDED
- **Ordinance 24-48** (`utah.gov/pmn/files/1180769.pdf`) surfaced in search but was opened and identified as a **rezone** (C-2/zc → C-2 at ~877 E 4500 S et al., adopted 2024-10-14) — a zoning/land-use ordinance, NOT a housing-plan document. Belongs to the (future) `ordinances/` dataset (source 3), so it was fetched, inspected, and removed from `raw/`. Its fetch remains logged in `raw/_fetch_log.jsonl` for provenance.

## Queries / URLs tried (audit trail)
- Sitemap crawl: `https://www.millcreekut.gov/sitemap.xml` → planning/housing page slugs.
- City pages fetched: `/151/Planning-Zoning` (yielded the General Plan link `DocumentCenter/View/3193`), `/568/Plans-and-Policies` (HR only), `/600/Affordable-Housing` (program contacts only).
- WebSearch: "Millcreek City Utah adopted General Plan moderate income housing element PDF"; "Millcreek … Moderate Income Housing Plan 2023 general plan appendix adopted ordinance 22-44"; "Millcreek … DocumentCenter General Plan chapter 4 housing".
- State pages: `jobs.utah.gov/housing/affordable/moderate/reporting/` (23/24/25 `reports.pdf` + `sb34.pdf`); Millcreek presence + page range confirmed by page-level header search in every compilation before extraction.

## Extraction QA
`screen_corpus.py` on `text/` (7 files) → **clean**: 0 cid-artifacts / replacement-chars / PUA-garbled / mojibake / long-tokens / dict-ratio outliers. dict_ratio median 0.75. Only advisory flags (repeated state-form question/header lines; hyphen line-breaks in the GP; page-range extracts end mid-sentence). Unlike the city's OCR-garbled *minutes* corpus, these housing PDFs are born-digital and extract cleanly.
