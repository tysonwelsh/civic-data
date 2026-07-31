# Salt Lake County — county-level data repository

The first **county** entity in civic-data and the reference implementation for the
`build-county-data-repo` skill. Salt Lake County (FIPS 49035; **Council–Mayor** form:
9-member elected County Council + elected Mayor; meets **Tuesdays**) contains 7 of the
repo's cities (slc, sandy, west_jordan, west_valley, south_jordan, millcreek, taylorsville).
Federated into repo-root `gov.db` (`cities.db`) as `gov_level='county'`, offset band 101.
Registry: `registry/entities.csv`. Source map: `recon.md`. Counties are modeled as
**modules**, not as big cities. Its `elections/` module is **the canonical Salt Lake County
canvass** — not just for the 7 held cities but for **all 22 SLCo jurisdictions** it publishes
(see Elections below).

## Bodies in gov.db (7, three kinds) — totals: 4,853 motions / 8,142 votes / 176 contested

- **council** — County Council + **Committee of the Whole** (the heavy voting body) + Council
  Work Session: 4,064 motions, 6,197 votes.
- **agency** — Redevelopment Agency + Municipal Building Authority + **Housing Authority**
  (HACSL / Housing Connect): 483 motions, 1,929 votes.
- **planning** — Planning Commission + Mountainous Planning District PC: 306 motions, 16 votes.
  (Was 310 before 2026-07-31: the 2024-12-10 PC record was a **phantom** — the same
  2024-12-11 meeting posted twice on PMN, the draft copy dated off a clerk-typo header.
  See `land_use/CLAUDE.md`. Nothing is missing; no meeting was held 2024-12-10.)

## Modules

```
elections/     CANONICAL Salt Lake County Clerk SOVC (slco_municipal_results_long.csv,
               248,801 rows, 2007–2025 odd years, EVERY SLCo municipality) + derived
               election_results_by_contest.csv (2,172 rows, 22 jurisdictions tagged). The 7
               held cities' pipelines RE-POINT to it (see Elections below). gov.db:
               election_result (22 SLCo jurisdictions) + election_race.
legislative/   Council + Work Session + Committee of the Whole — minutes markdown (~396) +
               minutes_index.csv. Votes from the Legistar API (see below).
agencies/      RDA + MBA minutes (49). housing_authority/ — 68 board minutes (from
               housingconnect.org; PMN 2535 carries NO minutes) + all_votes.csv (NAMED board).
land_use/      County PC + Mountainous PD PC — 97 minutes markdown + all_votes.csv (16 named
               dissents) + motions_tally.csv (297 tally-only). Tally-primary body.
development/   applications.csv — the development pipeline: 261 land-use actions (rezones,
               planned developments, subdivisions, annexations, GP amendments) → motion/vote.
plans/         General Plan (West + Wasatch Canyons) + 6 township GP + Moderate-Income
               Housing (14 docs, searchable; large PDFs link-only).
projections/   Gardner Institute county population/household/jobs (140 rows, vintages 25+22).
gis/           CATALOG ONLY (link, never mirror) — 34 UGRC + county ArcGIS layers + derived.
packets/       310 agenda packets + 49 land-use staff reports (searchable) + 95 catalogued.
ordinances/    67 adopted ordinances (text + enacting-vote link; numbers honestly blank).
db/            harvest_legistar.py / harvest_ws.py (Legistar → staging/, staging_ws/),
               fetch_minutes.py, build_db.py (→ salt_lake_county.db, standard 8-table schema),
               ingest_pc_votes.py + ingest_ha_votes.py (prose vote layers), build_applications.py.
               DERIVED; rerun in that order, never hand-edit.
```

## How votes work here (IMPORTANT — differs from the prose cities)

The County Council + agencies are **Legistar** (`slco`, webapi.legistar.com/v1/slco); their
votes are structured `EventItemVote` records, NOT parsed from minutes. The Council **minutes
are tally-only** ("the motion carried by a unanimous vote") but Legistar's electronic-vote
records name each member's vote even on unanimous motions — so **the API gives fuller named
roll calls than the minutes**. The two **Planning Commissions** and the **Housing Authority**
are NOT in that Legistar; their votes are prose-extracted from minutes: the PCs are
tally-primary (only dissenters/abstainers named — 16 named rows / 310 motions), the Housing
Authority board is NAMED (327 motions / 1,695 votes, high-consensus). `names_recorded=0`
marks tally-only motions — an honest recording ceiling. Minutes markdown is kept regardless
as the searchable corpus (`fts_minutes`) and provenance.

## Elections — the canonical county canvass (`elections/`)

`elections/slco_municipal_results_long.csv` is **the canonical Salt Lake County Clerk SOVC**
(Statement of Votes Cast), tidy long form — one row per precinct × candidate × vote-method,
**248,801 rows, 2007–2025 odd years, every SLCo municipality** (not just the 7 held cities;
raw workbooks LINKED from `~/Desktop/slco-election-archive`, not re-hosted). Held once, at
the level where it originates, instead of divergent per-city copies. `build_elections.py`
derives `election_results_by_contest.csv` (2,172 rows, council/mayor contests only,
`jurisdiction_slug`-tagged for **22 jurisdictions**) → gov.db `election_result` — so
`election_result` is the county-grain candidate-tally source for **22 SLCo jurisdictions**,
alongside city-grain `election_race` (authoritative winners/margins).

**The 7 held cities' pipelines RE-POINT to this canonical (executed 2026-07-19), NOT the
old "cities filter their own copy" model:** slc, sandy, west_jordan, west_valley,
south_jordan, and taylorsville now derive their `election_results/<slug>_races.csv` DIRECTLY
from this file, **byte-identity-gated** (rebuilds reproduce the prior audited outputs
byte-for-byte); their redundant raw copies were deleted. **millcreek is a DOCUMENTED
EXCEPTION — do NOT re-point it:** this canonical is odd-years-only, and millcreek's founding
**2016 even-year election (10 races)** exists only in its own per-city slice, which is
retained as the sole holder. Ceilings: `rank_in_contest` is **plurality** order — for RCV
cities (millcreek 2021/2023; draper 2021 pilot) the RCV final differs, so take winners from
`election_race`. Honest gaps: the county published **no SOVC workbook for the 2021 municipal
primary** (only a contest-grain summary PDF) and cancelled/uncontested races leave no canvass
(Utah Code 20A-1-206). Module doc `elections/CLAUDE.md` is authoritative.

## Which artifact for which question

- **County vote record / contested actions:** `gov.db` `motion`/`vote` where
  `city='salt_lake_county'`; `v_contested_all` (176); `v_member_record_all`.
- **Development decisions + their votes:** `development_application` (join `motion_id`).
- **Adopted ordinances + who enacted them:** `ordinance` (join `motion_id`; `fts_ordinance` for text).
- **Thematic search of what was said:** `fts_minutes` (Council/COW/Work-Session/RDA/MBA/HA/PC +
  plans) and `fts_packet` (agendas + staff reports); filter `city='salt_lake_county'`.
- **Elections:** `election_result` (22 SLCo jurisdictions, county-grain tallies) / `election_race`
  (authoritative winners/margins) / `v_election_city`; canonical canvass in `elections/` — the
  7 held cities re-point to it (millcreek excepted). See Elections section above.
- **Growth projections:** `projection`. **GIS:** `gis_layer` (catalog — query the live ArcGIS
  endpoints; nothing mirrored).
- **Cross-tier (county ↔ its 7 cities):** `entity_relationship` (`within`), then join city + county rows.

## Rebuild

```
python3 salt_lake_county/db/harvest_legistar.py    # Council+RDA+MBA → db/staging/
python3 salt_lake_county/db/harvest_ws.py          # Work Session+COW → db/staging_ws/
python3 salt_lake_county/db/fetch_minutes.py       # minutes PDFs → markdown
python3 salt_lake_county/db/build_db.py            # staging(+_ws) → salt_lake_county.db
python3 salt_lake_county/db/ingest_pc_votes.py     # + Planning Commission layer
python3 salt_lake_county/db/ingest_ha_votes.py     # + Housing Authority layer
python3 salt_lake_county/db/build_applications.py  # development/applications.csv
python3 salt_lake_county/elections/build_elections.py
python3 scripts/build_cities_db.py                 # federate into gov.db (+ search layer)
```
Order matters (staging before staging_ws keeps Council motion_ids stable so the 67 ordinance
links never break — verify after any rebuild).

## Gaps / follow-ons (root TODO.md "County content menu")

RDA project-area financials; interlocal/development agreements; county campaign finance;
sub-county/WFRC projections + TAZ; cross-tier analytical views; one image-only HA minutes PDF
(2021-12-15, re-OCR pending); 2019 HA minutes (below the 2020 floor). All honest, tracked,
never fabricated.
