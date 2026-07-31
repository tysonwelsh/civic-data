# Washington County — source reconnaissance (2026-07-20)

Washington County, Utah (FIPS **49053**; registry `fed_index` 106) — the repo's second
COUNTY entity and the first **3-member Commission / LIGHT+ tier** build. Contains the repo's
city `st_george_city_council` (plus Hurricane, Ivins, Santa Clara, Washington City, etc., not
in the repo). Governance: **Board of County Commissioners** — 3 elected commissioners:
**Adam Snow (Chair), Gil Almquist, Victor Iverson** (as scouted 2026-07-20). Seat of
government: St. George. This maps the county's growth/development records: searchable minutes
corpora (Commission + Planning Commission), plans, an ordinance catalog, and a GIS catalog.
Elections and projections are built by parallel agents (`elections/`, `projections/`).

## SCOPE DECISION — owner-gated LIGHT+ tier (documented honest deferrals)

Two datasets that a full county build carries are **deliberately NOT built** this pass, for
documented structural reasons — these are honest deferrals, not gaps to be filled:

1. **NO vote layer.** The Board is **3 commissioners**; there is **no Legistar / electronic
   voting API** (unlike Salt Lake County). Minutes are **scanned OCR image PDFs** (KONICA
   MINOLTA scanner output — zero text layer). Votes appear only as narrative motion prose
   ("Commissioner X moved, Commissioner Y seconded; motion passed") inside OCR text — no
   structured roll call, no reliable machine-extractable tally. Extracting a vote layer from
   3-member narrative OCR would be low-value and error-prone. The **minutes corpus itself**
   (searchable, provenance-flagged) is the vote-record artifact; motion prose is discoverable
   via FTS.
2. **NO development-applications pipeline.** **No planning-application log exists.** The county
   `planning-applications/` page publishes only **blank forms/checklists** (CUP, variance,
   zone-change, subdivision, planned-development). Building permits are accepted **only through
   an online permitting system**, and applicants get a **private per-application status link**
   — there is no public case list (no case numbers, applicants, or statuses). Nothing to
   ingest.

**Excluded bodies** (out of scope, noted for completeness): **Board of Equalization** (19
minutes in the archive — tax-appeal body, skip, cf. SLCo) and the **RAP tax advisory board**
(Recreation/Arts/Parks, 8 minutes — separate advisory body). The **Washington County Water
Conservancy District** is a separate special district — excluded per instructions. **Vision
Dixie** belongs to the **Dixie MPO** (a separate entity) — referenced here, not ingested.

## Legislative — Board of County Commissioners ✅ built

- **No vendor CMS.** County-hosted WordPress portal. Meetings landing:
  `https://www.washco.utah.gov/meetings/`. Bi-weekly-ish, **4:00 pm**, Commission Chambers,
  111 East Tabernacle, St. George.
- **Minutes archive = a date-query form, NOT a browsable index.**
  `GET /forms/commission/minutes/?m=MM&y=YYYY` returns that month's minutes list (the raw
  page is JS-lean; the server renders a `<div class="Notifications">` result list). Files
  live at **`/forms/pdf/minutes/{year}/M {YYYY-MM-DD}[ SUFFIX].pdf`**. Suffixes seen:
  (plain regular), ` SPEC` (special), ` W` (work session), ` PLAN` (Planning Commission —
  see land_use), ` BOE` (Board of Equalization), ` RAP`. Agendas parallel at
  `/forms/commission/agendas/?m=..` → `/forms/pdf/agendas/{year}/A {date}[ SUFFIX].pdf`
  (agenda suffixes add `HEAR`, `WORK`). **Archive depth: the form exposes 2005–2026**;
  this build floors at **2019-01-01** to bound OCR cost (deeper years available on the same
  pattern for a future pass).
- **KEY FINDING — scanned OCR, no API.** Minutes PDFs are scanner images
  (`Creator: C368 WashCo Comm`, `Producer: KONICA MINOLTA bizhub`), **0 text-layer chars**.
  OCR'd here with **tesseract 5** (200 dpi, `--psm 1`). 215 of 230 legislative docs required
  OCR; 15 were born-digital.
- **Built:** 230 minutes markdown 2019-01-08 → 2026-07-07 (`legislative/minutes/<year>/`) +
  `legislative/minutes_index.csv`. Bodies: 166 regular Commission, 60 special, 4 work session.
  **No vote extraction** (see scope decision).
- **PMN mirror:** Utah Public Notice **public body 700** = "County Commission of Washington
  County" (mirrors recent notices + minutes + MP3 audio; the sitemap page shows only the most
  recent handful, so the **county archive is the deep source**). YouTube: `@washcoutah`.

## Land use — Washington County Planning Commission ✅ built

- Land-use authority for **unincorporated** Washington County. Meets **Tuesdays 1:30 pm**.
- **Two source channels:**
  1. **County archive** — the same date-query form; PC minutes carry the ` PLAN` suffix
     (`/forms/pdf/minutes/{year}/M {date} PLAN.pdf`). Distribution: 2019:7, 2020:12, 2021:10,
     2022:6, 2023:8, then **drops off** (2024:0, 2025:1, 2026:1).
  2. **PMN public body `701`** = the Washington County **Land Use Authority** (discovered
     2026-07-20; entity "Washington County"; distinct from SLCo PC which is PMN 712). This IS
     the Planning Commission — PMN names the body "Land Use Authority" while its notices are
     titled "Planning Commission Agenda/Meeting". Minutes are attached as `YYMMDD PC
     Minutes.pdf`. This is where **2024-10 → 2026 PC minutes live** now that the county archive
     stopped posting ` PLAN` files. **Harvested 2026-07-20** via the PMN JSON search API (see
     `land_use/SOURCES.md` for the CSRF/JSON mechanism).
- **Built:** **60 PC minutes** markdown 2019-02-12 → 2026-06-09 (`land_use/minutes/<year>/`) +
  `land_use/minutes_index.csv` — 45 from the county archive (2019–2023) + **15 recovered from
  PMN 701** (2024-10 → 2026, all born-digital, `provenance: pmn_minutes`). Extraction: **49
  born-digital / 11 OCR**. **No vote extraction.**
- **Honest gap ledger (`land_use/gaps.csv`):** PMN 701 shows 28 PC meeting dates in 2024–2025;
  13 carry minutes, **15 are agenda/audio-only** (no minutes published anywhere) — including
  every 2024 Jan–Sep meeting (PMN minutes uploads begin 2024-10-08).

## Plans ✅ built (high FTS value — all born-digital)

`plans/` — 24 index rows, raw PDFs retained (<50MB) + text sidecars:
- **Countywide General Plan** (`washco-general-plan.pdf`, 406 pp; Public Lands element adopted
  2010-11-16, later element amendments ~2012).
- **Attainable Housing Plan** (2021; the county **MIH-equivalent**, Utah Code 17-27a-408),
  amended June 2025 by **Ord. 2025-1295-O** (see ordinances).
- **Transportation Master Plan** (2024, 63 MB → **link-only** per >50MB rule; text extracted)
  + Southern Utah Regional Trail Standards (2024).
- **13 community general plans** (2010–2011 series: Winchester Hills, Dammeron Valley, Diamond
  Valley, Veyo, Gunlock, Kolob, Pintura, Pine Valley, New Harmony, Central/Dixie Deer,
  Cliffdwellers/Sky Ranch, Brookside, East Enterprise) + 2 legacy 1990s community plans.
- **3 overlay-zone documents** (Pine Valley, Scenic Byway, New Harmony overlays).
- **Resource Management Plan** (2017, state-mandated) and **Water Use & Preservation Element**
  — published **interactive-only** (ArcGIS/outpost apps); **no downloadable PDF located** →
  catalog-link rows, text not extractable (honest gap).

## Ordinances ✅ cataloged (with the documented American Legal wall)

`ordinances/` — codified county code on **American Legal**
(`codelibrary.amlegal.com/codes/washingtoncout`), numbering **YYYY-NNNN-O**, **current
through Ord. 2026-1318-O**. Land-use titles: **Title 10 Zoning Regulations**, **Title 11
Subdivision Regulations** (structure confirmed via search — e.g. §10-29-4).
- **American Legal is HTTP 403 to every automated fetcher** (curl AND WebFetch) — bot-blocked,
  known from the st_george build. Cataloged as **metadata only**; text NOT scraped around the
  block (repo rule). Recorded in `ordinances/gaps.csv`.
- **County publishes NO browsable ordinance archive** (the `/forms/commission/` form exposes
  684 RESOLUTIONS 2019–2026 but zero ordinances). Individual ordinance PDFs surface only as
  scattered `wp-content/uploads/comdev-ordinance-*.pdf` links on topic pages.
- **Recovered free text:** **Ord. 2025-1295-O** (June-2025 MIH amendment, scanned → OCR'd).
  Adopted-ordinance **numbers** are otherwise discoverable in the OCR'd legislative minutes
  corpus (FTS). 4 index rows + 2 gap rows.

## GIS ✅ cataloged (link, never mirror)

`gis/` — the county runs a **live ArcGIS Server** at
`https://agisprodvm.washco.utah.gov/arcgis/rest/services` with **91 services**. `index.csv`
= 24 curated growth/development-relevant layers (Parcels, ParcelOwners, Assessor,
Developed_Parcels, Zoning, GeneralPlan, Subdivisions, Boundaries, Greenbelt, Hazards/WUI/
Wildfire, hillside slope, Elections precincts, RMP, plus the 1953–2026 aerial/Pictometry
imagery time-series) + UGRC/SGID statewide entries (Washington County Parcels LIR, municipal
boundaries, ACS housing). `derived/washco_arcgis_full_service_list.csv` = the full 91-service
reference. Interactive front-ends: `outpost.washco.utah.gov/apps/community-development/
interactive-map/` and zoning-info map PDFs. Catalog only — query the REST endpoints; nothing
mirrored.

## Elections / projections — ✅ built (parallel agents, now on disk)

- **`elections/`** — canonical Washington County Clerk canvass: `washco_results_long.csv`
  (117,920 rows, 15 elections, 2018–2025, precinct grain, `vote_method='Total'`) + derived
  `election_results_by_contest.csv` (435 rows / 110 contest-instances / 7 municipal elections
  2019–2025; st_george 63 rows; other WashCo municipalities `jurisdiction_slug=''`) →
  gov.db `election_result`. 55 byte-verified sources. Honest gaps: **2019-08 municipal primary
  held but never published** (GRAMA / city-recorder-minutes lead), 2018-06 scanned-only, 2022-06
  recount-only, **2026-06 precinct report REDACTED** (CVR not used to reconstruct). St George
  city layer shares the same clerk files (13 byte-identical); city re-point queued, not executed.
  See `elections/CLAUDE.md` + `VERIFICATION.md`.
- **`projections/`** — Gardner Institute county projections, 140 rows (Vintage 2025: 63,
  2025→2065; Vintage 2022: 77, 2010→2060), 7 metrics, county grain. See `projections/CLAUDE.md`.

## Honest gaps / follow-ons

- **PC minutes 2024–2025**: ✅ RESOLVED 2026-07-20 — recovered from **PMN body 701** (15 docs,
  2024-10 → 2026). Residual: 15 agenda/audio-only PC dates with no published minutes on any
  channel (logged in `land_use/gaps.csv`), incl. all 2024 Jan–Sep meetings.
- **Ordinance full text**: American Legal 403 wall (metadata cataloged; recover via manual
  browser or Community Development Dept).
- **Pre-2019 minutes**: available on the same county pattern back to 2005 (floored for OCR
  cost).
- **RMP + Water Use Element**: interactive-only, no extractable text.
- **Transportation Master Plan**: 63MB, link-only (text extracted).
