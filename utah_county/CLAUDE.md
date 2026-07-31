# Utah County — county-level data repository

The repo's **second county entity** (after `salt_lake_county/`) and its first **3-member
Board of Commissioners** county. Utah County (FIPS 49049; **Board of Commissioners** form —
a 3-member elected Board that is simultaneously the legislative AND executive body, no
separate mayor/manager; meets **Wednesdays** — historically Tuesdays in the 2015–2019 era)
is Utah's second-largest county and contains four of the repo's cities (lehi, orem, provo,
vineyard). Federated into repo-root `gov.db` (`cities.db`) as `gov_level='county'`,
**fed_index 102** (offset band 101–199). Registry: `registry/entities.csv`. Source map:
`recon.md`. Counties are modeled as **modules**, not as big cities. Read each module's own
`CLAUDE.md`/`README.md` before analyzing it. Built 2026-07-20.

## Bodies in gov.db (4, three kinds) — totals: 546 meetings / 11,218 motions / 4,705 votes / 84 contested
<!-- Refreshed 2026-07-29 to the post-repair figures (the 2026-07-25 vote-layer repair recorded
     below had updated the narrative but not this header, which still read 532/10,089/2,765/43). -->


- **council** — **Board of Commissioners** (the voting body): 469 meetings, 9,890 motions
  (822 named-roll), 2,383 votes, 31 contested. + **Commission Work Session** (budget/work
  sessions, deliberative — mostly discussion): 26 meetings, 13 motions, 0 votes.
- **agency** — **Housing Authority of Utah County** (HAUC): 26 meetings, 113 motions, 0
  votes (tally-only — see below).
- **planning** — **Planning Commission** (unincorporated-area land use, recommends to the
  Board): 11 meetings, 73 motions (71 named-roll), 382 votes, 12 contested. HIGH-attribution.

There is **no RDA/CRA or MBA** — the 3-member Board acts directly; redevelopment in Utah
County is a municipal function (see `agencies/README.md`). No Mountainous Planning District
PC (that body is Salt Lake County's).

## How votes work here (IMPORTANT — this is a PROSE-EXTRACTION county, unlike SLCo Legistar)

Utah County has **NO Legistar/Granicus/CivicClerk vote API**. The Board runs a bespoke
Next.js portal (`commission.utahcounty.gov`) whose archive API yields only minutes PDFs —
**votes exist only in the minutes prose**. So every vote is extracted from minutes text, and
the recording ceiling **flips twice across the decade** (recon.md, confirmed by reading PDFs):

| Era | PDF kind (files) | Vote grammar | SOURCE ceiling | Motions / named (2026-07-25) |
|---|---|---|---|---|
| **2015–2017** | born-digital, 143/143 | *"…carried with the following vote: **AYE:** [full names] / **NAY:** [names]"* | **NAMED roll** | 1,140 / **1,031** |
| **2018** | mixed (27 BD / 18 OCR) | same `AYE: [names]` form | **NAMED roll** | 409 / **229** |
| **2019** | mostly OCR (9 BD / 42) | *"**VOTE: 3-0** / **AYE:** COMMISSIONER LEE / COMMISSIONER AINGE"* — ALL-CAPS, surname-only | **NAMED roll** | 1,132 / **266** |
| **2020–2024** | OCR | *"COMMISSIONER X: MOTION TO … / **AYE: ALL IN FAVOR** / PASSED: 2/0"* — tally-only, EXCEPT a parenthetical roll on some divided votes (`AYE: ALL IN FAVOR (COMMISSIONER LEE AND COMMISSIONER SAKIEVICH)`) | **TALLY-PRIMARY**, dissent nameable | 6,582 / **29** |
| **2025–2026** | OCR | *"Motion: Commissioner Gordon / … / Result: **passed 3/0**"* | **TALLY-ONLY** (genuine) | 1,955 / **71** |

⚠ **CORRECTED + REPAIRED 2026-07-25** (`_audits/2026-07-25/report.md` F3;
record: `db/REPAIR_2026-07-25.md`). The pre-audit table said "2017–2026 = scanned OCR,
TALLY-ONLY" and called it "a genuine recording ceiling, not an extraction gap." **That was
wrong in both directions**, and the gap has now been closed:

- **2015–2018 — pypdf text corruption (FIXED).** pypdf inserted stray mid-word spaces
  (`"carried with the f ollowing vote"`, `"mot ion"`) that broke the extractor's anchor. All
  **228 born-digital files were re-extracted with poppler** (`db/reextract_borndigital.py`),
  which drops the split-word rate from ~13 per 1,000 tokens to ~0. 2016-08-30 went from 5
  usable anchors to 17.
- **2019 — the ALL-CAPS roll (FIXED).** `VOTE: n-n` is now an anchor and
  `COMMISSIONER LEE` resolves through **this meeting's own attendance block**
  (`PRESENT: COMMISSIONER BILL LEE, CHAIR`), with a corpus-wide surname map as fallback for
  multi-part documents that begin mid-meeting. 2019-01-29 went from **0 motions to 14, 13 named**.
- **2020–2024 — partially recovered.** The parenthetical form is now parsed, including the
  trap where the clerk writes `AYE: THOSE OPPOSED (COMMISSIONER LEE)` — the direction is read
  from the PHRASE, never the `AYE:` prefix. 21 of 63 such blocks captured; the residual sit in
  OCR text too fragmented to pair reliably (honest, logged).

**Result: motions 10,089 → 11,218, member-vote rows 2,765 → 4,705, contested motions 31 → 84 —
and contested votes now span 2015–2026 instead of stopping at 2018.** The entity is no longer
blind to divided Board votes. Person identity is consolidated via `db/person_aliases.csv`
(15 name variants → 8 real commissioners, each entry carrying its non-co-occurrence evidence).

Most business is genuinely a **Consent Agenda** ("Approved on Consent"), honestly tally-only —
that part of the original note stands. `provenance`: `minutes` = born-digital primary,
`ocr_scan` = OCR'd scan.

- **Planning Commission** is the exception — **HIGH-attribution**: every Aye and Nay is named
  on each substantive motion (71 of 73 motions fully named; 382 vote rows). Vision-transcribed
  from signed PMN minutes.
- **Housing Authority (HAUC)** board is **tally-only with first-name mover/seconder**
  (*"April made a motion… Amelia seconded… passed unanimously"*) → `names_recorded=0`, no
  per-member rows. Resolutions numbered (`Resolution 2025-05-01`).
- **Contested** = a named Nay/Abstain/Recuse row (43: Board 31, PC 12). Tally-only motions
  cannot be contested-detected by roll — an honest ceiling, not consensus.

## Modules

```
db/            PROSE pipeline (all idempotent; rerun IN ORDER, never hand-edit):
               fetch_legislative.py (archive API → minutes md), fetch_agencies.py (HAUC),
               build_catalog.py (minutes_index), extract_votes.py (era-aware prose → staging/),
               build_db.py (staging → utah_county.db, standard 8-table schema),
               ingest_pc_votes.py (Planning Commission layer, APPENDED above the legislative
               motion-id ceiling — never renumbers 1..10016), build_applications.py
               (development pipeline → application table + motion links), link_ordinances.py
               (ordinance → enacting-motion linkage + regenerates ordinances/index.csv).
legislative/   Board of Commissioners + Commission Work Session — 495 minutes md 2015–2026
               (228 born-digital / 267 OCR) + minutes_index.csv.
agencies/      housing_authority/ — 26 HAUC board minutes 2023-12→2026-03 (born-digital,
               tally-only) + minutes_index.csv. No RDA/MBA (agencies/README.md).
land_use/      County Planning Commission — 11 vision-transcribed minutes 2025-01→2026-05 +
               all_votes.csv (382 named rows) + motions_tally.csv (73 motions) +
               minutes_index.csv (145-meeting ledger, md_path relative to utah_county/).
elections/     CANONICAL Utah County Clerk canvass 2016–2026 (utah_county_results_long.csv,
               198,459 rows) + election_results_by_contest.csv (1,044 rows / 288 contests) +
               rcv/. gov.db: election_result. See Elections below.
development/    applications.csv — 32 PC land-use actions 2025-2026 (rezone / GP-and-zone-map
               amendment / conditional-use / plat / UCLUO text amendment / ag-protection).
ordinances/    Codified code text corpus (land_use_ordinance / code_of_ordinances / policies)
               + adopted_ordinances.csv (322-row catalog) + index.csv (loader-facing).
plans/         General Plan — codified (current, in-force) + 2006 PDF snapshot (searchable text).
projections/   Kem C. Gardner county population/household/jobs (140 rows, Vintage 2025 + 2022).
gis/           CATALOG ONLY (link, never mirror) — 23 UGRC/SGID + county ArcGIS growth layers.
```

## Which artifact for which question

- **County vote record / contested actions:** `gov.db` `motion`/`vote` where
  `city='utah_county'`; `v_contested_all` (43); `v_member_record_all`. Respect the
  tally-only ceiling — `names_recorded=0` motions carry no per-member rows by design.
- **Development decisions + their votes:** `development_application` (join `motion_id` →
  motion/vote). 29 of 32 actions link to a PC motion; 3 continued items had no formal motion
  (blank motion_id — honest).
- **Adopted ordinances + who enacted them:** `ordinance` (`city='utah_county'`); 10 uniquely
  link to the enacting Board motion (`motion_resolution='unique'`). **The catalog is a FLOOR,
  not a register** — see Ordinances below. `fts_ordinance` searches the codified code text.
- **Thematic search of what was said:** `fts_minutes` (Board + Work Session + HAUC + PC +
  plans); filter `city='utah_county'`. Do NOT grep the minutes markdown directly.
- **Elections:** `election_result` (county-grain candidate tallies) / `election_race`
  (authoritative winners/margins) / `v_election_city`; canonical canvass in `elections/`. See
  Elections below.
- **Growth projections:** `projection` (filter ONE `vintage`). **GIS:** `gis_layer` (catalog —
  query the live ArcGIS endpoints; nothing mirrored).
- **What the zoning code / General Plan says:** grep `ordinances/text/land_use_ordinance.txt`
  (UCLUO, unincorporated only) and `plans/text/utah_county_general_plan_codified.txt`
  (current in-force plan; MIH is Chapter 4).
- **Cross-tier (county ↔ its 4 cities lehi/orem/provo/vineyard):** `entity_relationship`
  (`within`), then join city + county rows.

## Elections — the canonical county canvass (`elections/`)

`elections/utah_county_results_long.csv` is **the canonical Utah County Clerk SOVC**, tidy
long form, **198,459 rows, 2016–2026** — municipal odd years AND even-year
federal/state/county (the county's SOVCs carry them all), every Utah County municipality +
county offices. `build_elections.py` derives `election_results_by_contest.csv` (1,044 rows /
288 contests) → gov.db `election_result`. The four held cities' audited per-city
`<slug>_races.csv` remain the authoritative winner/margin layer (`election_race`);
re-pointing them at this canonical is a separately-queued package (NOT done here — 52/52
held-city winners cross-check agrees).

**RCV / rcvis discipline (read before quoting a winner):** `rank_in_contest` is **plurality
(first-choice) order** — for `rcv=true` rows the RCV winner is `rcv_final_winner`, NEVER the
rank-1 candidate (they differ, e.g. Payson 2023). 2021 general stores rank-POSITION contests
(only "1st Choice" enters by-contest); 2023 general's RCV cities are rcvis.com-sourced
(no county precinct grain for 2023 general exists). RCV ran only 2021–2023.

**Quarantined mislabeled upload (honest gap):** the county's "2023 General SOVC" file is
actually the **unsuppressed 2022 general** canvass — **quarantined, never parsed** (logged in
`sources.csv`/`VERIFICATION.md`). Other ceilings: suppressed `-` cells stay suppressed
(never imputed); precinct codes changed era (`AF01`→`AF301`→`25AF01` — join within an era);
Utah County runs no Draper/Bluffdale municipal contest despite the county straddles.

## Plans, projections, ordinances, gis — the routing caveats

- **Plans:** the **codified General Plan is CURRENT/in-force** (Ord. 2020-1110, amended
  through Ord. 2025-1064) — read `plans/text/utah_county_general_plan_codified.txt`; the
  2006 PDF (`utah_county_general_plan.txt`) is the historical adopted-record snapshot. MIH is
  **Chapter 4** of the current plan — there is **no standalone MIH document**. Unincorporated
  areas only. Document layer — not federated into gov.db motion/vote.
- **Ordinances — the 322-row FLOOR caveat:** `adopted_ordinances.csv` (322 rows, 303
  land-use, 1997→2026) is **reconstructed from the amendment-history citations printed inside
  the codified code** (the county publishes no standalone ordinance register). It is a
  **floor, not a complete register** — parcel-specific **rezones** (which change the zoning
  MAP, a GIS layer, not the code text), budget ordinances, and one-off resolutions are NOT
  captured; `title` is the amendment description, not the signed caption. **Enacting-vote
  linkage:** Utah's "YYYY-NN" ordinance numbers COLLIDE with the county's ubiquitous
  "Agreement No. YYYY-NNN" numbering, so a literal number match in motion text is a false
  positive — only a **strict 1:1 date match to an ordinance-adoption motion** is trusted (10
  links, all 2021–2026 named/OCR-clean adoptions; 2015+ era → ~7.5%, pre-2015 → nothing since
  the db floor is 2015). Non-unique/ambiguous rows stay honestly blank. `index.csv` is the
  federated artifact (carries the direct `utah_county.db` motion_id); `adopted_ordinances.csv`
  is the working catalog. Both regenerated by `db/link_ordinances.py` — never hand-edited.
- **Projections:** Gardner Institute, county grain only, 140 rows across **Vintage 2025**
  (current, 2025→2065) + **Vintage 2022** (prior). **Filter to ONE vintage before trending** —
  the same year appears under both with different values. `households` ≠ housing units.
- **GIS:** `gis/index.csv` is a **catalog of 23 live ArcGIS layers** (UGRC/SGID filtered to
  FIPS 49049 + county org) — never mirrored. Query the endpoints live. No county-wide open
  zoning / general-plan / subdivision / annexation feature service is published.
- **Development:** `development/applications.csv` (32 PC land-use actions, 2025-01→2026-05) —
  the PC *recommends* on rezones/GP/text amendments (the Board decides) but *approves/denies*
  conditional-use permits directly (`outcome` verbatim-ish). Built only from the 11
  vision-extracted PC minutes; the pre-2025 pipeline awaits the CMS backfill (below).

## Honest gaps (never fabricated)

- **`cms.utahcounty.gov` NXDOMAIN — the largest recoverable lead:** **46 Planning Commission
  meetings 2020–2024 (+ a few 2025)** are catalogued in the county CMS but its media host is
  offline (`minutes_status=catalogued_media_offline`; `cms_minutes_file` names the PDF).
  Backfillable when the host returns (queued in root TODO). 2015–2019 PC is PMN agenda-only.
- **Two 404'd Board minutes** (listed in the archive, PDF unpublished): **2021-06-02**,
  **2022-08-15**; plus a mislabeled archive row `2024/01.31.2023.pdf`. Genuine gaps.
- **HAUC pre-2023-12:** not published online (GRAMA-request backfillable).
- **Pre-2015 paper era:** the digital archive begins 2015 (the API lists placeholder years to
  1950 but nothing resolves before 2015) — paper-only, not queueable here.
- Work-session budget books are OCR'd but carry ~zero motions by nature (13 across 26 sessions).

## Rebuild (order matters — legislative ids must stay 1..10,016)

```
python3 utah_county/db/fetch_legislative.py     # archive API → minutes md (UC_Y0/UC_Y1 scope years)
python3 utah_county/db/fetch_agencies.py        # HAUC minutes md
python3 utah_county/db/build_catalog.py         # minutes_index.csv from on-disk front-matter
python3 utah_county/db/extract_votes.py         # era-aware prose → db/staging/
python3 utah_county/db/build_db.py              # staging → utah_county.db (fresh; legislative+agency)
python3 utah_county/db/ingest_pc_votes.py       # + Planning Commission (APPENDED above id 10,016)
python3 utah_county/db/build_applications.py     # development/applications.csv → application table + links
python3 utah_county/db/link_ordinances.py       # ordinance → motion linkage + regenerates ordinances/index.csv
python3 utah_county/elections/build_elections.py
python3 scripts/build_cities_db.py              # federate into gov.db (+ search layer) — run by the PARENT
```
`build_db.py` recreates the db fresh (legislative + agency only, 10,016 motions / 2,383
votes, ids 1..10,016); `ingest_pc_votes.py` only APPENDS the PC with higher ids (asserts the
legislative ceiling is unchanged), so ordinance/application motion links stay stable. Derived —
regenerate, never hand-edit.

## Gaps / follow-ons (root TODO.md "County content menu")

The cms.utahcounty.gov PC backfill (46 meetings) when the host returns; HAUC pre-2023 GRAMA
backfill; the 2 404'd Board dates; zoning-map rezone ordinances (from GIS + agenda, since they
don't surface in the code text); a signed adopted-ordinance register to upgrade the 322-row
floor; sub-county/MPO projections; county campaign finance; cross-tier analytical views. All
honest, tracked, never fabricated.
