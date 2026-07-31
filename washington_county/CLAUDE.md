# Washington County — county-level data repository (LIGHT+ tier)

The repo's **second COUNTY entity** and the first **3-member Commission / LIGHT+ tier** build
(2026-07-20). Washington County, Utah (FIPS **49053**; registry `fed_index` 106; governance:
**Board of County Commissioners** — 3 elected commissioners, meets ~bi-weekly **Tuesdays 4pm**
in St. George). Contains the repo's city `st_george_city_council`. Registry:
`registry/entities.csv`. Source map + the scope-decision rationale: **`recon.md`** (read it).
Counties are modeled as **modules**, only the ones that fit; this is a **light** county — a
searchable minutes corpus + plans + ordinance catalog + GIS catalog, **no vote layer and no
development pipeline** (see below).

## What this build IS and IS NOT (owner-gated scope — honest deferrals)

- **NO vote layer.** 3-member board; **no electronic-vote API** (not a Legistar county); minutes
  are **scanned OCR image PDFs** with only narrative motion prose. A structured vote/motion
  layer is a documented deferral, not a gap. The **minutes corpus is the vote-record artifact**
  — find motions via full-text search of the OCR.
- **NO development-applications pipeline.** **No public application log exists** — the county
  publishes only blank forms; permits run through an online system with private status links.
  Documented deferral.
- **Excluded:** Board of Equalization (tax appeals) and RAP (Recreation/Arts/Parks) minutes;
  the Water Conservancy District (separate special district); Vision Dixie (Dixie MPO entity).

## Bodies & corpora

- **legislative/** — **Board of County Commissioners**: **230 minutes** markdown
  2019-01-08 → 2026-07-07 + `minutes_index.csv`. 166 regular / 60 special / 4 work session.
  **215 OCR / 15 born-digital (~93% OCR).** Source: county-hosted PDFs
  (`/forms/pdf/minutes/{year}/`, `provenance: citysite_minutes`); PMN mirror = public body 700.
- **land_use/** — **Planning Commission** (unincorporated county land use; Tuesdays 1:30pm):
  **60 minutes** markdown 2019-02-12 → 2026-06-09 + `minutes_index.csv` + `gaps.csv`. **49
  born-digital / 11 OCR.** Sources: county archive (` PLAN` suffix, 2019–2023, `provenance:
  citysite_minutes`) + **PMN public body 701** = the "Land Use Authority" (= the PC; 15 docs
  2024-10 → 2026, `provenance: pmn_minutes`). `gaps.csv` logs 15 agenda/audio-only PC dates
  with no published minutes (incl. all 2024 Jan–Sep). See `land_use/SOURCES.md`.
- **plans/** — 24 index rows (all **born-digital**): countywide **General Plan** (2010, 406pp),
  **Attainable Housing Plan** (2021, the MIH-equivalent; amended by Ord. 2025-1295-O), 13
  community general plans + 2 legacy, 3 overlay zones, Transportation Master Plan (63MB →
  link-only), Trail Standards; RMP + Water Use Element are interactive-only (catalog-link).
  `raw/` + `text/` + `index.csv`.
- **ordinances/** — CATALOG: codified county code on **American Legal** (numbering YYYY-NNNN-O,
  current through 2026-1318-O; **Title 10 Zoning / Title 11 Subdivision**). American Legal is
  **HTTP 403 bot-blocked** → metadata only, text not scraped (`gaps.csv`). County has **no
  ordinance browse archive**. Recovered free text: **Ord. 2025-1295-O** (2025 MIH amendment,
  OCR). `index.csv` + `gaps.csv` + `raw/` + `text/`.
- **gis/** — CATALOG ONLY (link, never mirror): 24 curated growth-relevant layers from the
  county's live **ArcGIS Server** (`agisprodvm.washco.utah.gov/arcgis/rest/services`, 91
  services) + UGRC/SGID entries. `index.csv` + `derived/washco_arcgis_full_service_list.csv`.
- **elections/** — **the canonical Washington County Clerk canvass** (the marquee module).
  `washco_results_long.csv` = tidy long, one row per precinct × candidate-column,
  **117,920 rows, 15 elections, 2018–2025** (municipal odd years 2019/2021/2023/2025
  primary+general; even-year generals 2018–2024; the 2020/2023-09/2024 primaries).
  `vote_method='Total'` throughout (the CSV era publishes no method grain); zero cells are
  real (the crosstab prints every precinct under every contest — row-presence is NOT
  jurisdiction-membership). Derived `election_results_by_contest.csv` = **435 rows / 110
  contest-instances / 7 municipal elections 2019–2025**, municipal council/mayor only (the
  SLCo contract), `jurisdiction_slug='st_george'` on the held city's **63 rows**; every other
  Washington County municipality rides along with the documented `jurisdiction_slug=''`
  ("other" — the contest string names the city) → loads gov.db `election_result` via the
  already-generalized loader. The county administers **St. George's** municipal elections; the
  audited `st_george_city_council/election_results/` layer derives from the *same* clerk files
  (13 shared files byte-identical); the city-pipeline re-point is queued + byte-identity-gated,
  **not yet executed**. `sources.csv` = 55 byte-verified provenance rows. **Format-era map**
  (VERIFICATION.md §5): CSV crosstabs E1/E2 (generals), P/SOVC (partisan primaries), 2018-11
  XLSX. **Honest gaps (never filled):** the **2019-08 municipal primary was HELD (six cities
  incl. St George) but never published as a file** — no Wayback capture; recovery lead =
  **GRAMA to the county clerk / city-recorder canvass minutes**; the 2018-06 primary is
  scanned-image PDF only (OCR queued); 2022-06 posted only the House-72 recount; **pre-2018**
  is below the index floor. **2026-06 primary — redaction discipline:** official summary PDF
  exists but the county **REDACTED the precinct report** and posted no export; precinct grain is
  NOT loaded and the public CVR was **deliberately NOT used to reconstruct redacted tallies**
  (suppressed stays suppressed). Module doc `elections/CLAUDE.md` + `VERIFICATION.md` authoritative.
- **projections/** — Kem C. Gardner Policy Institute county population/household/employment
  projections (Utah's official state-and-county series), schema-identical to SLCo's.
  `washington_county_projections.csv` = **140 rows, two vintages** — **Vintage 2025 (Nov 2025)**
  63 rows 2025→2065 + **Vintage 2022 (Jan 2022)** 77 rows (historical 2010/2015 + 2020→2060),
  7 metrics × 5-year snapshots, county grain only. Two vintages coexist by design — **filter to
  one** before trending. Verbatim source layer; `households` ≠ housing units (honest gap).
  Federates into gov.db `projection` unchanged. See `projections/CLAUDE.md` + `SOURCES.md`.

## Recording ceiling (cardinal rules)

Commission + PC minutes are **scanned images OCR'd with tesseract 5** — every OCR'd markdown
carries `ocr: true` in front-matter and a verify-against-source note; **verify names/numbers/
motions against `source_url` before quoting.** Born-digital docs carry `ocr: false`. No vote
tallies are extracted (see scope). Honest gaps are recorded in `recon.md` and
`ordinances/gaps.csv` — never fabricated.

## Which artifact for which question

- **What was discussed / decided at a Commission or PC meeting; motion prose; ordinance
  adoptions:** the **minutes corpora** — `legislative/minutes/` and `land_use/minutes/`
  (full-text search; open the `source_url` PDF to confirm anything OCR'd).
- **Long-range policy / land-use designations / housing strategy:** `plans/` text sidecars
  (General Plan, Attainable Housing Plan, community plans, overlays).
- **What the zoning/subdivision ordinance says:** `ordinances/index.csv` points to the
  American Legal code (Titles 10/11 — text 403-blocked; use a browser) + recovered PDFs.
- **Spatial / parcels / zoning / growth geography:** `gis/index.csv` → query the live ArcGIS
  REST endpoints (nothing mirrored).
- **Who won / margins / any Washington County municipal or county/state/federal tally:**
  gov.db `election_result` (municipal council/mayor, `city='washington_county'`) or on-disk
  `elections/election_results_by_contest.csv`; **St George authoritative winners/margins** →
  the audited `st_george_races.csv` / `election_race`. County/state/federal contests + precinct
  grain live ONLY in `elections/washco_results_long.csv` (not the by-contest file, by design).
  `rank_in_contest` = plurality order within a multi-winner at-large field — the "runner-up" is
  the first candidate BELOW the seat cut, not rank 2 (no RCV anywhere in this county).
- **Growth / population / household / jobs projections:** `projections/` (gov.db `projection`) —
  filter to one `vintage`.

## Provenance conventions (SLCo model)

Every minutes markdown carries source provenance in front-matter (recovered-vs-primary is a
first-class fact here as everywhere in the repo):
- **`citysite_minutes`** — county-hosted archive PDFs (`/forms/pdf/minutes/{year}/`); all 230
  legislative docs + the 45 county-archive PC docs (2019–2023).
- **`pmn_minutes`** — Utah Public Notice recoveries: **PMN body 701 = "Land Use Authority"**
  (= the Planning Commission) supplied the **15** PC minutes 2024-10 → 2026 after the county
  archive stopped posting ` PLAN` files. PMN body 700 = the County Commission mirror (deep
  source remains the county archive).
- **`ocr: true|false`** front-matter flag — 215/230 legislative + 11/60 PC docs are scanned
  images OCR'd with tesseract 5; born-digital docs carry `ocr: false`. **Verify names /
  numbers / motions against `source_url` before quoting anything OCR'd.**
- Elections + projections carry their own byte-verified `sources.csv` / `SOURCES.md`.

## Rebuild notes

Minutes were fetched from the county date-query archive
(`/forms/commission/{minutes,agendas}/?m=MM&y=YYYY`), OCR'd where scanned, and written with
provenance front-matter. This is a light build: there is **no per-county `db/`** and **no
federation step run by this build** — federation into `cities.db` (FTS corpora, plans,
ordinances, gis) is a separate integration step (do NOT run `scripts/build_cities_db.py` as
part of this module work). Derived layers are regenerated, never hand-edited.
