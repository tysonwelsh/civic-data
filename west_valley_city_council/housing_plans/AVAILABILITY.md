# West Valley City housing_plans — availability & gap record

**As-of:** 2026-07-06 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

West Valley City (~140k, Salt Lake County — Utah's 2nd-largest city) is well over the 10,000
threshold, so it **must** adopt an MIH element and file annual MIH implementation reports
(Utah Code 10-9a-403 / 10-9a-408; HB 462, 2022). Both are present and retrieved.

## Standalone plan vs. General Plan chapter — RESOLVED

**MIH is a STANDALONE plan published as an appendix to the General Plan** (and there is *also* a
Housing chapter inside the GP). The GP's own Housing chapter (Ch 7) states verbatim:
> "the City's Moderate Income Housing Plan required by the State is included as an appendix to
> this General Plan."

So there are two distinct housing artifacts, both captured:
- **Chapter 7 – Housing** — the GP's housing element chapter (web page, older 2011-2014-vintage data).
- **2025 Moderate Income Housing Plan** — the statutory MIH element, a separate 22-page PDF appendix
  (the element of record; `mih_element`).

## What EXISTS and was retrieved (7 documents, ~26 MB in `raw/`)

### City of West Valley City (site: `www.wvc-ut.gov` — CivicPlus; PDFs served from `/DocumentCenter/View/<id>/…`)
Discovered by crawling `https://www.wvc-ut.gov/sitemap.xml` (663 URLs) → the General Plan pages
(`/450` landing + web chapters `/2166`–`/2182`), then extracting `DocumentCenter/View` links from the
GP landing page.

- **General Plan — landing / components page** (`/450`). The adopted GP is delivered as **web chapters
  + appendix PDFs**; **no consolidated GP PDF is published** ("Contact our office for a PDF General
  Plan"). Retained artifact = the landing HTML. `general_plan`.
- **General Plan — all 12 chapters** ("Vision West 2035 General Plan"). Ch 1 Introduction (`/2166`),
  2 Administration (`/2170`), 3 Land Use (`/2171`), 4 Economic Development (`/2172`), 5 Urban Design
  (`/2173`), 6 Existing Neighborhoods (`/2174`), 7 Housing (`/2176`), 8 Community Facilities (`/2177`),
  9 Parks/Rec/Culture (`/2180`), 10 Transportation (`/2178`), 12 Definitions (`/2182`) are **web-page
  chapters** (html-strip sidecars); **11 Implementation** is the one **born-digital PDF chapter**
  (`DocumentCenter/View/23727`, 16 pp, pdftotext -layout). All `general_plan`.
  **Class-3 addendum, 2026-07-16 (primary-documents rollout):** the original 2026-07-06 build extracted
  only Ch 7 Housing + the landing; the other 11 chapters were fetched/extracted in this pass, closing
  the current-GP text-layer gap. Chapters were discovered from the `/450` landing HTML component link
  set (verified against the site) — no guessed IDs; all 11 fetched 200 (`raw/_fetch_log.jsonl`).
- **2025 Moderate Income Housing Plan** (`DocumentCenter/View/23733`). Standalone 22-page born-digital
  PDF appendix — the **MIH element of record**. `mih_element`.

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes
**statewide compilation PDFs** (one per report year), not per-city files. West Valley City is present
in each. Its report sorts **after West Point and before White City** (see disambiguation below):

- **2023 reports** compilation — WVC = PDF pp. ~1067–1089.
- **2024 reports** compilation — WVC = PDF pp. ~999–1015.
- **2025 reports** compilation — WVC = PDF pp. ~1261–1279.
- **SB 34 Municipal Progress Summaries 2019–2021** — WVC = PDF pp. 193–196 (`compliance_letter` proxy).

WVC pages were sidecar-extracted to `text/west-valley-city-<year>.txt`; the full compilations are
retained verbatim in `raw/`.

## The West Valley / West Jordan / West Point disambiguation (how the range was verified)

The compilations are alphabetical, and "West …" cities cluster: **West Bountiful → West Haven →
West Jordan → West Point → West Valley → White City**. West Valley is the LAST West-city and
immediately precedes **White City**. Boundaries were pinned per year by counting per-page mentions of
each jurisdiction (fitz) and locating the White City report start (which caps WVC):

- 2023: West Point content ends ~p.1065, White City report title at p.1089 → **WVC pp.1067–1089**.
- 2024: West Point ends ~p.997, White City starts p.1015 → **WVC pp.999–1015**.
- 2025: West Point ends ~p.1259, White City starts p.1279 → **WVC pp.1261–1279**.
- SB 34: WVC pages carry the explicit header "WEST VALLEY CITY, CITY" → **pp.193–196**.

Each extracted sidecar was re-checked: it contains "West Valley" (12–18 hits) and **zero** "West
Point" / "West Jordan" / "White City" bleed. `screen_corpus.py`: 0 cid/replacement/PUA/mojibake
across all 7 text files; the only advisory flags are repeated gov-form header lines (state templates)
and ends-mid-sentence (page-range/HTML extracts). dict_ratio median 0.77.

## What was NOT found / gaps (findings, not failures)

- **A consolidated PDF of the full adopted General Plan.** The GP is web-chapter-delivered; the /450
  page explicitly directs "Contact our office for a PDF General Plan" and "…for a PDF General Plan
  Map". Every chapter is now captured individually (11 web pages + the Implementation PDF), but there
  is still no single-file GP PDF and no GP Map PDF online. Verified by crawling the sitemap and reading
  the /450 landing HTML link set.
- **The 5 non-MIH GP appendix PLANS are catalogued but not ingested** (out of scope for this
  housing/GP-text dataset): Active Transportation Plan (`DocumentCenter/View/23729`), Major Street Plan
  (`/2181`, a web page), Fairbourne Station Vision (`/23730`), Station Area Plans (`/23734`), Water Use
  & Preservation (`/30211`). They exist and are fetchable; they are separate appendix documents, not GP
  chapters. The MIH Plan appendix (`/23733`) IS ingested (as `mih_element`).
- **The adopting resolution/ordinance for the 2025 MIH Plan as a public document.** The 2025 state
  report supplies the adoption-resolution and MIH-element links only as `wvcity-my.sharepoint.com`
  **personal** OneDrive URLs (auth-gated; not public records fetchable via polite GET). The MIH PDF
  itself carries no embedded ordinance/resolution number. Not retrieved (not publicly hosted).
- **Per-city standalone annual-report PDFs on the state site.** HCD only publishes the annual
  statewide compilations (`NNreports.pdf`) + the SB 34 summary — there is no `jobs.utah.gov` page
  hosting an individual "West Valley 2024 MIH report.pdf". The compilation IS the filed report of
  record.
- **Reporting years 2019–2022 as standalone compilations.** The `.../reporting/` index today links
  only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary; earlier individual-year compilations are
  not linked (superseded). SB 34 covers the 2019–2021 window.
- **A separate HCD "compliance letter" to West Valley City.** HCD does not publish per-city compliance
  letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.

## Vintage note (do not misread the General Plan as brand-new)

The **appendix documents are labeled "2025 General Plan – …"** and the MIH Plan is the 2025 element,
but the GP's core chapters (e.g. Chapter 7 Housing, with 2011–2014 home-price tables) are older, and a
**comprehensive General Plan update is in progress** — the 2025 state report projects the update to
start in the second half of 2025 and complete in **2027**. Treat the 2025 MIH Plan as the current
statutory element and the web chapters as the incumbent (pre-comprehensive-update) plan text.

## Queries / URLs tried (audit trail)

- Sitemap crawl: `https://www.wvc-ut.gov/sitemap.xml` (663 URLs) → GP pages `/450`, `/2166`–`/2182`;
  `/1631/Affordable-Housing`, `/271/Planning-Zoning`, `/485/Community-Development`.
- DocumentCenter links harvested from GP pages: MIH Plan (23733), Implementation (23727), Active
  Transportation (23729), Fairbourne Station Vision (23730), Station Area Plans (23734), Water Use &
  Preservation (30211), Water Conscious Development Guide (30213). Only the MIH Plan (the statutory
  element) was ingested; the others are non-MIH GP appendices out of scope for this dataset.
- State: `jobs.utah.gov/housing/affordable/moderate/reporting/` → `23reports.pdf`, `24reports.pdf`,
  `25reports.pdf`, `sb34.pdf`. WVC presence + page range confirmed by per-page jurisdiction-mention
  counting before extraction.
