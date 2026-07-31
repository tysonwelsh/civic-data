# Salt Lake County — source reconnaissance (2026-07-11)

The first COUNTY-level entity in civic-data. Salt Lake County contains 7 of the repo's
cities (slc, sandy, west_jordan, west_valley, south_jordan, millcreek, taylorsville). This
maps the county's own growth/development records. Governance: **Council–Mayor form** —
a **9-member elected County Council** (legislative) + an **elected County Mayor** (executive).
FIPS 49035. Meets **Tuesdays**.

## Legislative — County Council (Legistar) ✅ primary source found

- **Platform: Legistar**, client `slco`. Web API: `https://webapi.legistar.com/v1/slco/`
  (live, no key). InSite: `https://slco.legistar.com/`. Minutes/agenda PDFs:
  `https://slco.legistar1.com/slco/meetings/<yr>/<mo>/<EventId>_M_..._Meeting_Minutes.pdf`.
- **Bodies (BodyId → meetings 2020+):** County Council **138** (261), Council Work Session
  **265** (98), Committee of the Whole **180** (55), Board of Equalization 276 (47, tax
  appeals — skip), Debt Review 263 (35), **Redevelopment Agency 257** (35), TRCC 252 (30),
  **Municipal Building Authority 258** (16), Council Executive Committee 251 (16),
  Redistricting 264 (12), Board of Canvassers 260 (11).
- **KEY FINDING — the Council is TALLY-PRIMARY.** Minutes record *"A motion was made by
  Council Member X, seconded by Y … the motion carried by a unanimous vote"* — mover +
  seconder named, individual members **not enumerated** (0 "NAY", "voting AYE" absent;
  "unanimous"/"motion carried" only). Named member votes appear **only when a division is
  called**, and those divided votes ARE the sparse Legistar `EventItemVote` records
  (probe: 3 of 84 passed items across 8 meetings carried member votes). So **the Legistar
  structured harvest is the COMPLETE record** — motion-level spine (title/mover/seconder/
  passed/matter) for every action + named votes for the few divided ones. **No minutes-prose
  vote parsing is needed or possible** (the minutes don't name members either). Tally-only is
  a true recording ceiling, not a gap (cf. nephi / west_jordan PC).
- **Harvest:** `db/harvest_legistar.py` → `db/staging/{bodies,persons,events,eventitems,
  votes}.csv`. Council + Work Session + Committee of the Whole = the **legislative** module;
  RDA + MBA = the **agencies** module (below).

## Land use — County Planning Commission (unincorporated) — PDF/PMN

- Land-use authority for **unincorporated** Salt Lake County (+ the metro townships). Agendas/
  minutes are **PDFs** on `saltlakecounty.gov` (`…/regional-development/…/salt-lake-county-
  planning-commission/agendas/<MMDDYYYY>.pdf`) and mirrored on **Utah Public Notice**
  (pmn.utah.gov, publicbody **712**). Meets ~monthly (Wednesdays, 8:30–10). NOTE: there are
  **two** county planning commissions (different geographic areas / commissioner residency).
  Approach: prose-parse the PDF minutes like the non-Legistar cities (TODO — Phase 3b).

## Agencies — RDA / MBA / Housing Authority

- **Redevelopment Agency of Salt Lake County** (Legistar body **257**, 35 mtgs 2020+;
  also PMN publicbody 1277) — harvested with the Council.
- **Municipal Building Authority** (Legistar body **258**, 16 mtgs; own page at
  `saltlakecounty.gov/council/agendas-minutes/municipal-building-authority/`) — harvested.
- **Housing Authority** — the *Housing Authority of the County of Salt Lake* ("Housing
  Connect") is a **separate legal entity** (PMN Housing Authority Board, publicbody 2535),
  NOT in the County Council Legistar. Records are on its own site + PMN. TODO — Phase 3b
  (lower priority; separate portal).

## Elections ✅ DONE (Phase 2)

Canonical county canvass at `elections/` (SLCo Clerk SOVC; `slco_municipal_results_long.csv`
+ derived `election_results_by_contest.csv`). In gov.db: `election_result` (county tallies)
+ `election_race` (city races). See `elections/CLAUDE.md`.

## Plans / projections / GIS — TODO (Phase 3b)

- **Plans:** county **General Plan** (+ the metro-township general plans) and the
  **Moderate-Income Housing** element/report (unincorporated) — `saltlakecounty.gov/
  regional-development/`. Text corpus + FTS.
- **Projections:** Kem C. Gardner Policy Institute / GOPB county population + household
  projections (small structured tables — high unique value). Source: gardner.utah.edu / GOPB.
- **GIS (catalog + link + derived only — never mirror):** parcels, zoning, address points,
  boundaries from the county + **UGRC / gis.utah.gov**. Store `index.csv` (layer/url/vintage/
  license) + small `derived/` summaries.

## Module status

| module | source | status |
|---|---|---|
| `elections/` | SLCo Clerk SOVC | ✅ done (Phase 2) |
| `legislative/` | Legistar (Council 138 + 265 + 180) | 🔨 harvesting → db + federate |
| `agencies/` | Legistar (RDA 257, MBA 258) + Housing Authority (PMN, separate) | 🔨 RDA/MBA harvested; HA TODO |
| `land_use/` | County PC minutes PDFs (saltlakecounty.gov + PMN 712) | ⬜ Phase 3b (prose parse) |
| `plans/` | county general plan + MIHP | ⬜ Phase 3b |
| `projections/` | Gardner / GOPB | ⬜ Phase 3b |
| `gis/` | UGRC + county (catalog+link+derived) | ⬜ Phase 3b |
