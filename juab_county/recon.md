# Juab County — recon / source map

**Built 2026-07-20 (CHEAP-MODULES-ONLY tier).** Juab County, Utah (FIPS **49023**,
UGRC CountyID **12**; registry `fed_index` **107**). Governance form: **3-member Board
of County Commissioners** (Seats A/B/C, partisan, staggered). County seat **Nephi**;
other municipalities **Mona** (city), **Levan**, **Rocky Ridge**, **Eureka**
(town/city). Rural, ~12k population.

This is a **thin county**: by owner decision it carries the **elections canonical
layer** + thin GIS/plan/code catalogs + this recon and the authoritative `CLAUDE.md`.
The legislative/minutes/land-use/ordinance/development modules were **deliberately NOT
built** (rationale below). `projections/` (Gardner Institute county series, 140 rows,
Vintage 2025 + Vintage 2022) was built by a parallel agent and is now on disk.

## What was built

```
juab_county/
  recon.md                       this file
  CLAUDE.md                      authoritative thin-county doc + which-artifact routing
  elections/                     CANONICAL Juab County canvass (2023-2026)
    juab_results_long.csv        tidy long: contest x candidate, Certified Total + Precinct rows
    election_results_by_contest.csv   DERIVED governance layer -> gov.db election_result
    harvest_ev.py / build_long.py / build_elections.py / build_sources.py
    sources.csv                  79 byte-verified raw-provenance rows (zero unrecorded)
    VERIFICATION.md              reconciliation + ceilings + the 2019/2021 gap
    raw/ev/     (71 files)       Channel C — Enhanced Voting JSON API
    raw/clerk/  (4 PDFs)         Channel A — Juab County Clerk canvass
    raw/ltgov/  (4 PDFs)         Channel B — Lt. Governor canvass certifications
  gis/index.csv                  thin CATALOG (link, never mirror) — UGRC SGID Juab layers (7)
  projections/                   Gardner Institute county series (140 rows; V2025 + V2022)
    juab_county_projections.csv  population/household/jobs, county grain; -> gov.db projection
```

## Elections — THREE official channels (all verified live 2026-07-20)

- **Channel A — Juab County Clerk canvass PDFs.** Index
  `https://juabcounty.gov/residents/election-information/election-results/`. The channel
  Nephi's 2023-primary adoption already used. Retained: 2023 Sept-5 primary
  (`.../2023/09/Official-Results-Prim-23.pdf`), 2023 Nov general
  (`.../2023/11/Gen-Election-Results-11-29.pdf`), 2024 June primary canvass
  (`.../2024/07/24P-Canvass-Rpt.pdf`), 2024 Nov post-canvass (`.../2024/11/24G-Post-Canvass-Rpt.pdf`).
- **Channel B — Lt. Governor per-county canvass certifications** on `vote.utah.gov`
  (standardized naming, archive floors at 2024). Retained: `2024/08/P24_Juab.pdf`,
  `2024/11/G24_Canvass_Juab.pdf`, `2025/08/P25_Canvass_Juab.pdf`,
  `2025/11/G25_Canvass_Juab.pdf`. (`sites/44/` path variants are 404; the flat
  `wp-content/uploads/<yyyy>/<mm>/` path is live.)
- **Channel C — Enhanced Voting JSON API (PRIMARY, precinct-level).**
  `https://electionresults.utah.gov/results/public/api/elections/juab-county-ut/<slug>/ballot-items`
  and `/ballot-items/<id>` (`breakdownResults` = per-precinct). Slug **`juab-county-ut`**
  (a newer slug `juabcountyutah` holds only the CD-2 recount). Election slugs harvested:
  `2023-Nov-General`, `primary06252024`, `general11052024`, `primary08122025`,
  `general11042025`, `Primary06232026`. Precinct set = Nephi #3-#7, Mona #1-2, Levan #1,
  Rocky Ridge #1, Eureka #1-6, Callao #1 (+ `:U` splits, CountyID-`12`-prefixed in 2025,
  + `Federal` overseas pseudo-precincts) — CountyID 12.

**Coverage:** 2023 (municipal primary + general), 2024 (primary + general — county
commission/assessor/recorder/treasurer, school boards, state/federal), 2025 (municipal
primary + general), 2026 (June primary — commission Seats A/B, sheriff, SBOE 14).
70 contests / 3,327 long rows; 37 governance contests / 123 by-contest rows across 9
jurisdictions (nephi, mona, levan, rocky_ridge, eureka, juab_county, juab_school,
tintic_school, utah_sboe). Reconciliation & ceilings: `elections/VERIFICATION.md`.

**CONFIRMED HONEST GAP — 2019 & 2021 municipal cycles: NO official canvass exists.**
The Clerk results page, the EV portal, and vote.utah.gov all floor at 2023/2024
(verified: pre-2023 EV slugs 404; the Clerk index links only 2023+). The county
canonical starts **2023**; no unofficial news numbers are ingested. Nephi's city module
keeps its own 2019/2021 unofficial rows with their existing caveat — not this layer's
scope.

## Legislative / minutes layer — DELIBERATELY DEFERRED (owner-gated)

Not built, by scope decision. Rationale: Juab County Commission records are **scanned,
sporadic, and agenda-heavy** — no Legistar/CivicClerk vote API, minutes are image PDFs
posted irregularly, and the recording ceiling is tally-only narrative. The
cost/coverage ratio fails the cheap-modules tier. No council/COW/agency/PC votes, no
adopted-ordinance linkage, and no development-applications pipeline were built. This is
a documented scope boundary, **not** a data gap to backfill silently; if commissioned
later, follow `build-county-data-repo` Phase 2 (prose-minutes path, not Legistar).

## Plans / code / GIS catalog pointers

- **General Plan 2023** and the **Juab County Code** are hosted on **CivicLinq**:
  `https://hosting.civiclinq.com/juabcounty/books/general-plan-2023/preface` and
  `https://hosting.civiclinq.com/juabcounty/books/county-code/preface`. Catalogued as
  links (not ingested — no `plans/` module in this tier).
- **GIS:** UGRC / Utah SGID CountyID-12 layers — `Parcels_Juab_LIR` (15,259 parcels,
  the housing base layer), `Parcels_Juab` geometry, plus statewide layers filtered to
  Juab (municipal/county boundaries, address points, housing unit inventory, census
  tracts). **No standalone Juab County ArcGIS hub was found** — everything is UGRC-hosted.
  Thin catalog in `gis/index.csv` (link, never mirror).

## Containment note

This build wrote ONLY `juab_county/` (elections/, gis/, recon.md, CLAUDE.md). It did not
touch `cities.db`, `scripts/`, `registry/`, city dirs, other counties, or the
parallel-agent-owned `juab_county/projections/`, and did not run
`scripts/build_cities_db.py`. Federation (registry `db_rel_path` + the county loaders
already generalized in `scripts/build_cities_db.py`) is a downstream integration step.
