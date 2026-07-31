# Sandy housing_plans — availability & gap record

**As-of:** 2026-07-16 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.
**2026-07-16: PRIMARY_DOCS_PILOT class-3 expansion** — see "2026-07-16 expansion" section at the
bottom; it supersedes parts of the 2026-07-05 gap findings below (kept for the audit trail).

## What EXISTS and was retrieved (8 documents, ~27 MB in `raw/`)

### City of Sandy (site: `sandy.utah.gov` — CivicPlus; documents served as `content.civicplus.com/api/assets/<guid>`)
Discovered by crawling `https://sandy.utah.gov/sitemap.xml` → the General Plan / Long Range Planning pages, plus targeted search for the CivicPlus asset GUIDs (the `/798` page is JS-rendered and exposes no static document links).

- **Sandy City General Plan (comprehensive update, adopted 2025-01-07)** — the CURRENT adopted plan. Delivered as an **interactive ArcGIS web plan** ("Open Map"), **not a PDF**. Retained artifact = the `/798/Sandy-City-General-Plan` landing page HTML that hosts the map. Adoption date and "new Moderate Income Housing Element + five station area plans" confirmed by Sandy's 2025 state MIH report (see below).
- **General Plan Chapter 10 — Moderate Income Housing (MIH Element), Sept 2022** — the last **PDF-form** MIH element; adopted as part of the 2022 General Plan amendment (Ordinance 22-10).
- **Ordinance #23-01 (adopted 2023-01-31)** — amends the General Plan by adopting revisions to the **Implementation Plan** of the MIH Element (born-digital signed PDF).
- **2017 Biennial Moderate Income Housing Report** — Sandy's pre-HB462 biennial MIH review report (former 10-9a-403 regime), from the Long Range Planning page.

### State repository — Utah Dept. of Workforce Services, Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes **statewide compilation PDFs** (one per report year), not per-city files. Sandy is present in each:

- **2023 reports** compilation — Sandy = PDF pp. ~699–715.
- **2024 reports** compilation — Sandy = PDF pp. ~640–654.
- **2025 reports** compilation — Sandy = PDF pp. ~804–820.
- **SB 34 Municipal Progress Summaries 2019–2021** — Sandy = PDF pp. 134–135 (`compliance_letter` proxy).

Sandy pages were sidecar-extracted to `text/sandy-<year>-*.txt`; the full compilations are retained verbatim in `raw/`.

## What was NOT found / gaps (findings, not failures)

- **A standalone PDF of the current (2025) General Plan or its 2025 MIH Element.** The comprehensive General Plan adopted 2025-01-07 is **web-only** (ArcGIS interactive plan under `/798`); Sandy publishes no consolidated GP PDF and no chapter PDFs for the 2025 plan. Verified: crawled the sitemap; fetched `/798`, `/740/Plan`, `/797/Long-Range-Planning`, `/2297/General-Plan-Process`, `/2258/Sandys-General-Plan-Shaping-the-Future-T`, and the `.../community-development/planning/long-range-planning/sandy-city-general-plan` slug — all resolve to the same JS map-landing page with an "Open Map" ArcGIS link and no document assets. The **retrievable MIH element document of record is the Sept-2022 Chapter 10 PDF** (amended by Ord 23-01, 2023); the newer element lives only inside the interactive plan.
- **Per-city standalone annual-report PDFs on the state site.** HCD only publishes the annual statewide compilations (`NNreports.pdf`) + the SB 34 summary — there is no `jobs.utah.gov` page hosting an individual "Sandy 2024 MIH report.pdf". The compilation IS the filed report of record. Contact for filings: `mih@utah.gov`; Sandy filer Jake Warner (`jwarner@sandy.utah.gov`).
- **Reporting years 2019–2022 as standalone compilations.** The `.../reporting/` index today links only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary; earlier individual-year compilations are not linked (superseded). The 2017 Biennial Report (city copy) + SB 34 (2019–2021) cover the earlier window.
- **A separate HCD "compliance letter" to Sandy.** HCD does not publish per-city compliance letters; the SB 34 progress summary is recorded as the `compliance_letter` proxy.
- **The 2022 General Plan (Ordinance 22-10) as a full document.** Not published as a downloadable PDF; only its Chapter 10 (MIH) survives as an asset. Not retrieved (no PDF exists on the current site).

## Candidate documents CHECKED and EXCLUDED (verified NOT Sandy)
Utah Public Notice (`utah.gov/pmn/files/…`) MIH PDFs surfaced by search were opened and identified as **other cities'** filings, so excluded: `532759.pdf` = Holladay; `1022981.pdf` = Plain City; `1395429.pdf` = Murray; `1166659.pdf` = a generic MIH slide deck. The classic `sandy.utah.gov/home/showdocument?id=…` DocumentCenter links now 302-redirect to `/home` (dead after the CivicPlus migration).

## Queries / URLs tried (audit trail)
- Sitemap crawl: `https://sandy.utah.gov/sitemap.xml` → planning/GP page slugs.
- City pages fetched: `/798` (= `/sandys-general-plan` = the community-development GP slug), `/740/Plan`, `/797/Long-Range-Planning`, `/2297/General-Plan-Process`, `/2258/Sandys-General-Plan-Shaping-the-Future-T`, `DocumentCenter`.
- WebSearch: "Sandy City Utah General Plan adopted PDF"; "Sandy … moderate income housing element 10-9a-403 adopted"; "Sandy … chapter 10 general plan"; "Sandy … General Plan 2025 MIH element station area plan".
- State pages: `jobs.utah.gov/housing/affordable/moderate/reporting/` (23/24/25 `reports.pdf` + `sb34.pdf`); Sandy presence confirmed by page-level text search in every compilation before extraction.

---

## 2026-07-16 expansion (PRIMARY_DOCS_PILOT class 3 — general-plan text corpus)

### What was ADDED (28 index rows; ~150 MB raw, ~4.5 MB text sidecars)

**Pre-2025 chaptered General Plan — the full surviving chapter set (was: only Ch.10).**
The city REMOVED the chapter list from `/798` after the 2025-01-07 adoption (the live page now
shows only the "Open Map" link). The list was recovered from the **Wayback 2024-04-20 capture of
`/798`**, whose embedded widget JSON names all chapter assets (`manualContentItemIds` under the
"General Plan Chapters" LINK_LIST widget). All assets still resolve on `content.civicplus.com`
(fetched + verified in-body 2026-07-16): Ch.1 Introduction (undated), Ch.2 Goals & Policies
(1997/rev.2017), Ch.3 Growth/Land Use/Community Identity (1980), Ch.4 Commercial & Industrial
(1979), Ch.5 Transportation (=2009 Master Transportation Plan Update), Ch.6 Community Facilities
(1980), Ch.7 Housing Element (2013/rev.2022), Ch.8 Parks/Rec/Trails (2005 update), Ch.9
Environmental Hazards (1992), Index of Appendices (undated). Chapters 3/6/9 required a cmap-shift
decode (see CLAUDE.md). Also captured: the **Ord 22-10 Exhibit A** council form of the 2022
Housing Element revision (Legistar) and the **MIH Element amended 1.31.23** (the "Link to Plan"
in Sandy's 2023 state filing).

**Pace of Progress: Sandy City General Plan 2050 (adopted 2025-01-07) — the narrative text, at
document fidelity.** The earlier "no PDF exists" finding was TOO STRONG: no *consolidated/official
site* PDF exists, but (a) the adopting **Ord 25-01's Exhibit A adopts "the draft dated 10/21/2024"**
(full document then at `sandypaceofprogress.org`) as amended by Exhibit B, and (b) the council
packets carry the draft sections as attachments. Captured: Sections 1–7, Appendix A (**all five
Station Area Plans**: Historic Sandy, Expo Center, Sandy Civic Center, Crescent View, South Jordan
FrontRunner (Sandy portion)), Appendix B (six NAC plans), the staff memo "Accessing the General
Plan draft documents", and the **city-published adopted-form "Section 2 | Livability.pdf"** — the
CivicPlus asset Sandy's own 2025 state MIH filing gives as the link to the current MIH element.
Section 7's pages **T19–T41 are the land-use designation/mix dashboard tables** (verified in the
extracted text; T42+ = goals/objectives). Also captured: the standalone **Stadium Village Master
Plan (2019)** from the Long Range Planning page (new doc_type `small_area_plan`).

### The ArcGIS web product — probed, REDUCED FIDELITY (honest limit)

The `/798` "Open Map" target is `sandycity.maps.arcgis.com` Instant App (sidebar template)
`975e67ed4298468b8a698d49e8ec2e1c`, titled **"Sandy Future Land Use Map"** (created 2025-09-10).
Polite GET probes of the public REST endpoints (item + `/data` for app and its web map
`828d8e3e483943c58d7f599cf16d54fe`, created 2025-02-19) show: the app serves ONLY the future-land-use
web map (layers: Current Zoning, Road Network, Neighborhood Transition Corridors, Station Areas,
Municipal Boundary, Sandy_Future_Land_Use with 10 designation labels). **No plan narrative is
served by any public ArcGIS text endpoint**: a public search of the whole `IGYUtIzoA63tzE48` org
(352 items) finds no StoryMap/Hub/Experience for "Pace of Progress"/"Livability"/"2050". The four
`arcgis-*.json` rows are flagged REDUCED-FIDELITY in index notes. NOT capturable as text: the map
geometry/interaction itself. (No auth/bot barriers were encountered or bypassed; all endpoints
public.)

### Remaining honest gaps (evidence attached)

- **GP 2050 Section 8 (Resiliency & Sustainability + the implementation-strategies chapter).**
  The 2024-10-03 staff memo confirms the draft = 8 sections + 2 appendices at
  `sandypaceofprogress.org`; that domain is **dead (NXDOMAIN, 2026-07-16)** and Wayback holds only
  Jan–May 2023 engagement-phase captures (no PDFs; CDX filter `.*pdf.*` = 0 rows). Section 8 was
  never attached standalone to any Legistar matter (packets index searched: matters 6018, 6045,
  6055, 6080, 6085–6094, 6098, 6107, 6126, 6140). Its content is witnessed only indirectly: the
  Dekeyzer (§4+8) and D'Sousa (§7–8) amendment PDFs (packet attachments; exhibits inside signed
  Ord 25-01, which scan as images there). Candidate future source: a records request to Long Range
  Planning (jwarner@sandy.utah.gov).
- **Adopted-form PDFs for sections other than Section 2.** Only "Section 2 | Livability.pdf"
  was found published post-adoption (because the state MIH filing links it). The adopted text of
  the rest = the 10/21/24 draft + Ord 25-01 Exhibit B amendments (both on disk, composable).
- **Pre-2025 GP appendices A–N**: the Index of Appendices is posted; the appendices themselves
  were "available upon request" only — never published (per the archived GP page text).
- **One Wayback-era asset lost:** the 2020-10-27 snapshot's single manual chapter asset
  `1db66b41-cda3-47f5-919b-21f89a95ccb4` now returns 404 from content.civicplus.com (identity
  unknown; the 2024 snapshot's full chapter list supersedes that page state).
- **PMN**: `pmn_backfill/` holds only minutes for Sandy — no plan PDFs there (checked 2026-07-16).

### Fetch discipline

All 28 fetches via `polite_fetch.py` (browser UA, ≥1.0 s/host, logged to `raw/_fetch_log.jsonl`
with sha256 — rows stamped `2026-07-16T00:00:00Z`). Sources: `content.civicplus.com/api/assets/`
(8 chapter + 3 other assets), `sandyutah.legistar1.com/sandyutah/attachments/` (12),
`sandycity.maps.arcgis.com/sharing/rest/` (4 JSON). Every PDF verified in-body against its index
claim (title + date) before indexing.
