# Juab County — county-level data repository (THIN county)

Juab County, Utah (FIPS **49023**, UGRC CountyID **12**; registry `fed_index` **107**,
offset band 101). Governance form: **3-member Board of County Commissioners** (Seats
A/B/C, partisan, staggered). County seat **Nephi**; other municipalities **Mona**
(city), **Levan** & **Rocky Ridge** (towns), **Eureka** (city). Rural (~12k pop).
Federates into repo-root `gov.db` (`cities.db`) as `gov_level='county'`. Source map:
`recon.md`. Built 2026-07-20 on the **CHEAP-MODULES-ONLY** tier — an intentionally thin
county: **elections canonical layer + catalogs only.**

Counties are modeled as **modules, not big cities** (SCHEMA_SPEC §0 entity model). Juab
holds one repo city, **Nephi** (`nephi_city_council/`) — a member whose city-side
election rows derive from the same canvass this module now holds canonically.

## What EXISTS

```
elections/   CANONICAL Juab County canvass, 2023-2026 (see below). The only substantive module.
gis/         index.csv — thin CATALOG (link, never mirror): UGRC SGID CountyID-12 parcels
             (Parcels_Juab_LIR, ~15,259) + boundaries + address points + housing unit inventory.
recon.md     source map (three election channels, the 2019/2021 gap, deferral rationale).
projections/ Kem C. Gardner Institute county projections — 140 rows (Vintage 2025 + Vintage
             2022), population/household/jobs, county grain. See "Projections" below.
```

## What was DELIBERATELY NOT built (owner-gated scope — documented, not a gap to backfill)

- **No legislative / minutes / votes layer.** County Commission records are scanned,
  sporadic, agenda-heavy, tally-only, with no vote API — the cost/coverage ratio fails
  the cheap tier. No `db/`, no Commission/agency/PC motions or votes, no `legislative/`,
  `land_use/`, `agencies/`.
- **No ordinances / development-applications / packets modules.**
- **No `plans/` ingest** — the General Plan 2023 + County Code live on **CivicLinq**
  (`hosting.civiclinq.com/juabcounty/books/general-plan-2023/preface`,
  `.../books/county-code/preface`) and are catalogued as links in `recon.md` only.

These are scope boundaries. If commissioned later, follow `build-county-data-repo`
(Phase 2 prose-minutes path — Juab is NOT a Legistar county).

## Elections — the canonical county canvass (`elections/`)

Three official channels (verified live 2026-07-20; full map in `recon.md`): **A** Juab
County Clerk canvass PDFs, **B** Lt. Governor per-county certifications (vote.utah.gov),
**C** Enhanced Voting JSON API (`juab-county-ut`, precinct-level — the PRIMARY source).

- **`juab_results_long.csv`** — canonical tidy long, 3,327 rows / 70 contests. Two row
  kinds per contest × candidate (column `vote_method`): **`Certified Total`**
  (precinct='', the EV/canvass certified figure — AUTHORITATIVE) and **`Precinct`**
  (per-precinct detail; EV publishes precinct TOTALS only — no vote-method split, the
  ceiling). Low-count precincts are **privacy-suppressed** by EV (`votes='' ,
  suppressed='True'`), so Certified Total ≥ Σ attributed precincts. Verbatim analysis
  layer — never hand-edit; regenerate `python3 elections/build_long.py`.
- **`election_results_by_contest.csv`** — DERIVED (`build_elections.py`), 123 rows / **37**
  GOVERNANCE contests (verified on disk), `jurisdiction_slug`-tagged across **9 jurisdictions**: municipal
  council/mayor (nephi, mona, levan, rocky_ridge, eureka) + county offices (juab_county:
  Commission Seat A/B/C, Sheriff, Assessor, Recorder/Surveyor, Treasurer) + school
  boards (juab_school, tintic_school, utah_sboe). Votes come from the `Certified Total`
  rows, so it **reconciles to the certified canvass** even under suppression. This is
  what loads into `gov.db` **`election_result`** (loader `load_election_result` in
  `scripts/build_cities_db.py`, already generalized — 14 columns, verified conforming).
  State/federal/judicial-retention/constitutional-amendment contests are kept in the
  long file **only** (not Juab local-governance jurisdictions).
- **`sources.csv`** — 79 byte-verified provenance rows (one per retained raw; zero
  unrecorded; all URLs live-checked). Regenerate `python3 elections/build_sources.py`.
- **`VERIFICATION.md`** — reconciliation (internal + cross-source vs PDFs), ceilings,
  the 2019/2021 gap. Read it before quoting suppressed or even-year figures.

**Ceilings / gaps (honest, never filled):**
- **2019 & 2021 municipal cycles: NO official canvass exists anywhere** — Clerk page, EV
  portal, and vote.utah.gov all floor at 2023/2024. The canonical starts **2023**; no
  unofficial numbers are ingested. (Nephi's city module keeps its own 2019/2021
  *unofficial* news-archive rows — that caveat is the city's, not this canvass's.)
- **2023 Sept-5 municipal primary — Clerk PDF only** (EV `_Demo` slug is empty);
  contest-grain, no precinct; named sums below printed Contest Totals by the write-in
  remainder (recorded as-is).
- EV precinct **totals only** (no Election-Day/By-Mail/Early split). Precinct labels are
  verbatim and vary by vintage (2025 CountyID-prefixed `12Nephi #3`; `:U` splits;
  `Federal` overseas pseudo-precincts) — do not normalize; reconciliation is per-contest.

## Projections — Gardner Institute county series (`projections/`)

`juab_county_projections.csv` — the **Kem C. Gardner Policy Institute** Utah State-and-County
long-term projections (population / households / persons-per-household / household &
group-quarters population / median age / jobs), schema-identical to SLCo's, federates into
gov.db `projection` unchanged. **140 rows, two vintages:** **Vintage 2025 (Nov 2025)** 63 rows
2025→2065 + **Vintage 2022 (Jan 2022)** 77 rows (historical 2010/2015 + 2020→2060), 7 metrics ×
5-year snapshots, **county grain only** (no sub-county — MPO small-area not ingested). The two
vintages coexist by design — **filter to one `vintage` before trending**. `households` ≠ housing
units (honest gap). Verbatim source layer, never hand-edit. See `projections/CLAUDE.md` +
`SOURCES.md`.

## Which artifact for which question

- **Who won / margins / candidate tallies (all 5 Juab municipalities + county + school):**
  `gov.db` **`election_result`** (`city='juab_county'`), or on-disk
  `elections/election_results_by_contest.csv`. `rank_in_contest` = plurality order
  (Juab has no RCV). For **Nephi authoritative winners/margins** prefer
  `election_race` / `nephi_races.csv` (the audited city summary).
- **Precinct-level detail / turnout by precinct:** `elections/juab_results_long.csv`
  (`vote_method='Precinct'`), honoring `suppressed`.
- **Provenance / raw canvass:** `elections/sources.csv` → `raw/{ev,clerk,ltgov}/`.
- **Growth / population / household / jobs projections:** `gov.db` `projection`
  (`city='juab_county'`) or `projections/juab_county_projections.csv` — filter to one `vintage`.
- **Parcels / zoning / housing GIS (7 catalogued layers):** `gov.db` `gis_layer`
  (`city='juab_county'`) or `gis/index.csv` — query the live UGRC ArcGIS endpoints (nothing mirrored).
- **General Plan / County Code:** CivicLinq links in `recon.md` (not ingested).
- **County legislative votes / ordinances / development pipeline:** **not built** (see
  "DELIBERATELY NOT built" above) — do not imply coverage.
- **Cross-tier (county ↔ Nephi):** `entity_relationship` (`within`), then join the city
  + county rows.

## Rebuild (elections)

```
python3 juab_county/elections/harvest_ev.py       # Channel C EV API -> raw/ev/
python3 juab_county/elections/build_long.py        # raws (+ hand-keyed 2023 primary) -> long
python3 juab_county/elections/build_elections.py   # long -> election_results_by_contest.csv
python3 juab_county/elections/build_sources.py      # regenerate sources.csv
# federation is downstream: scripts/build_cities_db.py (NOT run by this thin build)
```
DERIVED layers are idempotent; the canonical long file + retained raws are the truth.
