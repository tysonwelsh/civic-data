# Nephi housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`. Nephi City, Juab County (~6,500; small rural county seat).

## Headline finding

- **MIH is a CHAPTER, not a standalone plan.** Nephi's moderate-income housing element lives **inside the General Plan** as **Element 6: Housing** (2023 General Plan, PDF pp. 56-65). There is **no** separate MIH plan/element PDF and no separate MIH report.
- **Nephi is EXEMPT from Utah's state MIH annual-report regime**, and is **absent from every state compilation** (verified — see below). This is a valid finding, not an acquisition failure.

## What EXISTS and was retrieved (5 PDFs, ~33 MB in `raw/`)

### City of Nephi (site `www.nephi.utah.gov` — CivicPlus; documents served from `/DocumentCenter/View/<id>`)
Discovered by crawling `https://www.nephi.utah.gov/sitemap.xml` -> the planning pages, chiefly **`/168/City-Code-Planning-Documents`**, which exposes static `DocumentCenter/View/...` links (unlike many CivicPlus sites, Nephi's planning-documents page lists real hrefs).

- **Nephi City General Plan 2023** (`raw/nephi-general-plan-2023.pdf`, 89 pp., born-digital text) — the adopted General Plan of record. Full sidecar `text/nephi-general-plan-2023.txt`.
  - **Element 6: Housing** (PDF pp. 56-65) is Nephi's **MIH element** — focused sidecar `text/nephi-general-plan-2023-ch6-housing.txt`. Contains: rental-affordability-gap tables keyed to 80/50/30% AMHI (ACS 2010 & 2019); **Goal 6.2** using the statute's own words — a *"reasonable opportunity for a variety of housing, including moderate-income housing"* (Utah Code 10-9a-403); and Housing implementation steps a-e (ADUs in residential zones, adopt a mixed-density residential zone, housing rehab info, senior/affordable-housing grants). It reads as a **general housing element**, not the formal HB462 *menu-of-strategies* MIH element that specified municipalities must file — consistent with Nephi's exemption.

### State repository — Utah DWS / Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes **statewide compilation PDFs** (one per report year), not per-city files. All four current documents were downloaded and **full-text searched for Nephi**; retained in `raw/` as evidence of the negative check:

- `raw/23reports.pdf` (2023, 1109 pp.) — **zero** `Nephi`.
- `raw/24reports.pdf` (2024, 1030 pp.) — **zero** `Nephi`.
- `raw/25reports.pdf` (2025, 1303 pp.) — **zero** `Nephi`.
- `raw/sb34.pdf` (SB 34 Municipal Progress Summaries 2019-2021, 199 pp.) — **zero** `Nephi`.

## Why Nephi is absent (verified exemption)

State MIH reporting under Utah Code §10-9a-408 applies only to a **"specified municipality"** — per HCD's own reporting page, **"all cities over 10,000 population; cities over 5,000 in counties with at least 40,000 in population."** Nephi (~6,500) is **over 5,000 but Juab County (~11,800) is far under 40,000**, and Nephi is not over 10,000 — so Nephi qualifies under **neither** threshold and is **not** a specified municipality. It therefore has **no state annual-report obligation** and does not appear in any compilation. (All municipalities with a general plan still include an MIH *element* in that plan — which Nephi does, as Element 6 above.)

Corroboration inside the compilations: **no Juab County city** (Nephi, Mona, Levan) files; the only `JUAB` reference in the whole SB 34 file is **Santaquin** (county listed `UTAH/JUAB`, MAG region), a comparison city, not Nephi. Sandy — a comparable specified municipality — appears ~30 times in each file, confirming the text layer is searchable and Nephi's zero-count is real, not an extraction artifact.

## What was NOT found / gaps (findings, not failures)

- **A standalone Moderate Income Housing plan/element/report for Nephi.** None exists — MIH is Element 6 of the General Plan. Verified: crawled the sitemap; fetched the planning pages (`/168`, `/271` Planning Commission, `/521`/`/588`/`/705` Planning-and-Zoning, `/622`, `/631` Zoning-and-Maps); the only housing/general-plan document link anywhere is the 2023 General Plan itself.
- **Any Nephi filing in the state HCD compilations (2023/2024/2025) or SB 34 summary.** Nephi is exempt (above) and absent from all four.
- **An HCD per-city "compliance letter."** HCD publishes none for any city; the SB 34 progress summary is the closest proxy (and Nephi is absent from it too).
- **An explicit adoption ordinance/resolution number or date inside the General Plan PDF.** The document is titled "General Plan 2023" and carries no embedded adoption instrument; `date` is recorded as the title year `2023`. (An adoption vote may exist in `meeting_minutes/` — not cross-referenced here.)
- **A pre-2023 / prior Nephi General Plan.** The DocumentCenter surfaces only the 2023 plan; no earlier plan is published on the current site.

## Discovery / audit trail (URLs tried)

- Sitemap: `https://www.nephi.utah.gov/sitemap.xml` (200, 55 KB) -> planning page slugs.
- City pages fetched: `/168/City-Code-Planning-Documents` (source of the GP link), `/271`, `/521`, `/588`, `/705`, `/622`, `/631`, `/DocumentCenter`.
- Document retrieved: `DocumentCenter/View/2451/Nephi-City-General-Plan-2023-PDF`.
- State: `jobs.utah.gov/housing/affordable/moderate/reporting/` + `documents/{23reports,24reports,25reports,sb34}.pdf`; each full-text searched for `Nephi` (word-boundary) before concluding absence.
- Statute/threshold confirmation: HCD reporting page + Utah Code §10-9a-403/408 ("specified municipality" population/county thresholds).

Byte-level provenance for every retrieval: `raw/_fetch_log.jsonl`.
