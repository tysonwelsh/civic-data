# Weber County — county-level data repository

The repo's **second COUNTY entity** (after `salt_lake_county/`) and the first county built
from **prose minutes with NAMED roll-call votes** rather than a Legistar API. Weber County
(FIPS **49057**; `gov_level='county'`, **fed_index 103**, offset band 101–199) governs by a
**3-member Board of County Commissioners** (a Council-of-Commissioners form — NOT
Council–Mayor; no separately-elected executive). It **contains the repo's
`ogden_city_council`**. The Commission meets **Tuesdays, 10:00 a.m.**, Weber Center, Ogden.
Federated into repo-root `gov.db` (`cities.db`). Registry: `registry/entities.csv`
(+ `registry/relationships.csv`: `ogden within weber_county`, `weber_county within
ut_state`, `weber_county member_of wfrc_mpo`). Source map: `recon.md`. Counties are modeled
as **modules**, not big cities — only the modules that fit are built. Each module's own
`README.md`/`CLAUDE.md` is authoritative for that module.

## Governance & the voting body

- **Board of County Commissioners — 3 members, all voting**; one is **Chair**, one **Vice
  Chair** (elected internally each January). Current board (2023– ): **Gage Froerer**
  (Chair), **James "Jim" H. Harvey** (Vice Chair), **Sharon Bolos**. Prior-era
  commissioners appear across 2015–2022 (Ebert, Gibson, Jenkins, Bell) and are captured
  data-first from the roll calls. There is **no county council and no elected mayor** — the
  Commission is both legislative and executive; agencies (RDA, etc.) convene in-session as
  the same Commission. County Clerk/Auditor (Ricky Hatch) takes the minutes.

## Bodies in the db — totals: 4,404 motions / 12,585 votes / 7 persons (2015-01-06 .. 2026-04-14)

- **Board of Commissioners** — the regular meeting body: **4,404 motions / 12,585 votes**,
  **99.6% named** (4,387/4,404 carry a named roll call). Outcomes: 4,225 Pass, 2 Fail, 15
  no-result-printed (`outcome=''`). **76 contested** motions (≥1 Nay/Abstain/Recuse).
- **Board of Commissioners Work Session** — 3 posted work sessions in the floor (2016-07-06,
  2016-07-13, 2018-10-10), all discussion-only (**0 motions**); kept as a distinct body so
  the meeting-type distinction is preserved. Detection is **title-block-only** (regular
  meetings routinely *mention* "work session" in discussion prose — do not re-flag on that).

## The vote-recording CEILING — NAMED roll call, even on unanimous motions

Unlike the tally-only county councils (incl. Salt Lake, whose named votes come from
Legistar), **Weber's minutes name every commissioner's individual vote on every recorded
motion** — the `motion`/`vote` layer is NAMED-primary straight from the minutes prose
(`db/extract_votes.py`). `result_raw` is the **verbatim roll-call line** ("Chair Froerer –
aye; Commissioner Harvey – aye; Commissioner Bolos – aye"); `outcome` (Pass/Fail) is derived
from the aye/nay tally (there is no separate "carried 3-0" result string). Two roll-call
grammars are handled: (a) the modern single semicolon-separated dash-joined line, and (b) an
EARLY-ERA (mostly 2015–2017) `Roll Call Vote:` header + one dot-leader member line each.
**`names_recorded=0` = an honest recording ceiling** (source printed no roll call) — **15
motions (0.35%)**: a lost-for-lack-of-second motion, a recess motion, a source-malformed
roll, and stacked organizational motions sharing one roll call. Never fabricated.

- **Data floor 2015-01-01.** The county's own born-digital archive reaches back to **2000**
  (~690 additional meetings, same named grammar) — a high-value backfill logged in `recon.md`,
  **not harvested in this build** (per-year counts recorded there).
- **Provenance** `county_portal` on every meeting/motion. Minutes markdown carries
  front-matter (`source_url`, `source_pdf`, `source_index`); a UNION of two portal indexes
  (`commission_meetings.php` + `commission_minutes_archive.php`) is merged in
  `db/fetch_minutes.py` because neither index alone is complete.

### The Froerer alias (person-unification normalization)

"Freorer" is a **clerk typo for Chair Gage Froerer** in the roll-call lines of three Jan-2023
meetings (`2023-01-10`, `2023-01-17`, `2023-01-24`). The verbatim value is **retained
untouched in `db/staging/votes.csv`** (city-faithful); it is merged onto the canonical
person **only at name-key resolution** in `db/build_db.py` (`PERSON_ALIASES = {"freorer":
"froerer"}` — the sanctioned normalization layer, SCHEMA_SPEC §8). Result: 7 persons (not 8),
23 votes reattributed to Gage Froerer (2,639 total). Add future verbatim misspellings there,
not by editing staging.

## Modules

```
legislative/  Commission minutes markdown (533 docs, 2015+) + minutes_index.csv (UNION of
              two portal indexes). minutes_unrecovered.csv = none within floor — TRUE again
              as of 2026-07-26: 21 docs had been front-matter-only Konica copier scans with
              no OCR fallback (see the repair note below).
db/           extract_votes.py (prose → staging/), build_db.py (→ weber_county.db, the
              STANDARD 8-table schema; federates unchanged). DERIVED — rerun in that order.
              staging/motion_refs.csv = 1,148 motion-anchored instrument refs (feeds ordinances/).
              ocr_empty_minutes.py = the 2026-07-26 image-only-scan OCR backfill.
land_use/     County planning corpus — FTS-ONLY (166 minutes, 4 bodies). NO vote layer (by
              scope). See the consolidation seam below.
ordinances/   The adopted-instruments register (NEW) + adopted-code catalog + land-use case keys.
elections/    CANONICAL Weber County Clerk canvass, 2006–2026 (weber_results_long.csv). Ogden
              re-points to it (queued, separate). gov.db: election_result + election_race.
plans/        Ogden Valley + Western Weber General Plans (MIH lives inside them) — text sidecars.
projections/  Kem C. Gardner population/household/jobs (140 rows, vintages 2022 + 2025).
gis/          CATALOG ONLY (link, never mirror) — 8 UGRC/county ArcGIS layers (LIR parcels base).
```

## Which artifact for which question

- **County vote record / contested actions / a commissioner's record:** `gov.db`
  `motion`/`vote` where `city='weber_county'`; `v_contested_all` (76 contested),
  `v_member_record_all`. NAMED roll call on 99.6% of motions.
- **Adopted ordinances + who enacted them:** the **`ordinances/` register** — the
  adopted-ordinance / resolution table Weber never published, derived from the named-roll
  minutes (`ordinances/build_adopted_instruments.py`). `adopted_instruments.csv` is the full
  working register (**844 rows — 277 ordinances + 567 resolutions**, one per distinct
  instrument, each citing its minutes). `index.csv` is the **ordinance-class subset (277
  rows)** in the federation loader's schema (direct county-db `motion_id`) → `cities.db`
  `ordinance` **with enacting-vote linkage**: **247/277 (89.2%)** carry a unique link; **30
  ambiguous/unlinked** (same-date/same-stage ties, or an ordinance number matched from a
  nearby header) are honestly `unlinked` (blank motion_id, `prior_readings` recorded).
  ⚠ **Was 198/277 before 2026-07-29**: procedural motions (adjourn / recess / reconvene)
  were competing as "adopting" motions, because a number read off an ALL-CAPS section
  header anchors to whichever motion follows it. Excluding them recovered 50 correct links
  and turned **ordinance 2019-13** from a WRONG link (it pointed at "moved to adjourn the
  public meeting and reconvene the public hearing") into an honest `unlinked` — its real
  adopting motion is in the 2019-07-30 minutes but was never extracted (an `extract_votes.py`
  gap, logged in `ordinances/README.md`). Resolutions
  stay register-only. `code_sources.csv` = the dual-codification code catalog (Municode +
  Municipal Code Online); `case_keys.csv` = 169 PC/BOA land-use case keys (a DIFFERENT
  numbering from Commission ordinances — join is a future task).
- **Thematic / keyword search:** `fts_minutes` (Commission minutes + the land_use planning
  corpus + plans), filter `city='weber_county'`.
- **Land-use decisions (Planning Commissions / BOA):** **FTS ONLY** — read the minutes.
  There is **NO vote/`all_votes.csv`/development-pipeline layer** for land use (owner-gated
  scope, not a data gap — the votes were never extracted). See the seam below.
- **Elections:** `election_result` / `election_race` / `v_election_city`; canonical canvass
  in `elections/` (see below).
- **Growth projections:** `projection` (filter ONE vintage before trending). **GIS:**
  `gis_layer` (catalog — query the live ArcGIS endpoints; nothing mirrored; LIR parcels =
  the housing/growth base for **unincorporated** Weber).
- **Cross-tier (Weber ↔ Ogden):** `entity_relationship` (`within`), then join the Ogden city
  rows to the county rows.

## Land-use — the 2025 planning-commission consolidation seam

Historically two area commissions + a countywide appeal authority; **`land_use/` ingests all
four as searchable text** (166 minutes, floor 2020):

- **Weber County PC** (consolidated, `weber_county_pc`) — created by **Weber County
  Ordinance 2025-27** (final reading 2025-11-18), which dissolved the two area PCs
  **effective 2025-12-03**; corpus 2025-12-09 → 2026-05-05 (8 minutes). This is the LIVE
  body going forward.
- **Ogden Valley PC** + **Western Weber PC** — the former eastern/western area commissions,
  now **closed historical series** (OVPC 2020-04-07..2025-12-02, 77; WWPC 2021-02-09..2025-11-18, 69).
- **Board of Adjustment** (appeal authority, sparse by nature) — 2022-04-28..2025-10-23, 12.

**WATCH ITEM — Ogden Valley incorporation.** The 2024 ballot incorporated **Ogden Valley
City** (council elected 2025; `ogdenvalley.gov`), which removed jurisdiction from the OVPC
and triggered the consolidation. New Ogden-Valley-area land use now splits: unincorporated
pockets → the consolidated county PC; the incorporated city → its own municipality (a
potential FUTURE `build-city-data-repo` target, not part of this county). Use the GIS
Municipal Boundaries layer to separate newly-incorporated land over time.

## Elections — the canonical Weber County canvass (`elections/`)

`elections/weber_results_long.csv` is **the canonical Weber County Clerk canvass** (tidy long
form, 13 columns matching the SLCo file; 11,416 rows, **2006–2026**): every odd-year
municipal canvass 2007–2025 (all contests + districts) plus even-year county-office contests
and countywide measures. `build_elections.py` derives `election_results_by_contest.csv`
(1,080 rows / 327 contests) → gov.db `election_result`. **Ogden, the repo-held Weber city,
draws from this same county canvass** — the byte-identity-gated Ogden re-point is **queued
and separate** (do NOT touch `ogden_city_council/election_results/` from here).

Honest gaps: **the 2023 municipal general is a county-publication gap** — the county
published only a **bond-only** canvass and referred voters to the municipalities, so
**Ogden's 2023 council races exist only city-side** (`ogden_city_council`), not in this
county canvass. Also missing county-side: 2009 (entire cycle), 2013 primary, 2019 primary;
no precinct grain before 2018 / for 2019g / 2021. Suppressed cells (<15-voter precincts)
stay suppressed (`suppressed=True, votes=''`). Module `elections/CLAUDE.md` is authoritative.

## 2026-07-26 repairs (audit F4 / F13 — `_audits/2026-07-25/report.md`)

- **21 image-only scans OCR'd.** They were Konica-Minolta copier scans with no text layer
  and the build had no OCR fallback, so each markdown was ~307 bytes of front matter and
  contributed nothing (19×2021, 2×2023). New `db/ocr_empty_minutes.py` renders the RETAINED
  raws and OCRs them (idempotent; born-digital rows untouched; `provenance` restamped
  `county_portal_ocr`). **motions 4,242 → 4,404 · votes 12,114 → 12,594 (CSV rows; the db
  holds 12,585 — see the documented expected 9-row difference below) · motion_refs
  1,102 → 1,148 · adopted-instruments register 807 → 844 — exactly the 37 missing 2021
  resolution numbers the audit predicted, including RESOLUTION 36-2021** (2021-09-21, the
  meeting the auditor had read visually to prove the loss).
- **Silent vote drops made LOUD.** `build_db.py` swallowed `sqlite3.IntegrityError` on
  `UNIQUE(motion_id, person_id)` and decremented the id, so 9 rows vanished between the flat
  CSV and the db with no trace (the Park City class). Each is a SOURCE clerk typo naming one
  commissioner twice on one roll ("Commissioner Harvey – aye; Commissioner Froerer – aye;
  Chair Froerer – aye"). The CSV keeps them verbatim; the build now prints every collision.
  db vote = 12,585 vs CSV 12,594 — the 9-row difference is expected and itemized on build.

## Honest gaps (not fabricated)

- **Land-use votes are out of scope** (FTS-only), not missing. 15 Commission motions are
  `names_recorded=0` (genuine recording ceilings). Joint **Weber+Davis** boundary meetings
  (2020-10-14, 2023-08-01) print both boards' roll calls — visiting Davis commissioners
  (Kamalu/Stevenson) are excluded via the extractor's `VISITING` set and never become Weber
  persons; "Elliott" is left ambiguous (cast no Weber vote).
- **WWPC has no 2020 minutes** (portal begins 2021-02-09; GRAMA-only). Agenda-only dates
  (OVPC ~29 / WWPC ~43 / BOA ~28) are logged, not ingested (no deliberative record). Three
  portal source mis-links are recorded in `land_use/gaps.csv` (mislinked copies dropped).
- **2000–2014 Commission history** is a logged future backfill (~690 meetings), not a gap.
- **MIH** — Weber publishes no standalone Moderate-Income Housing plan; MIH lives as chapters
  inside the two General Plans (search the `plans/text/` sidecars).

## Rebuild (order matters; DERIVED — never hand-edit outputs)

```
python3 weber_county/db/extract_votes.py                     # minutes markdown → db/staging/
python3 weber_county/db/build_db.py                          # staging → weber_county.db (+ Froerer alias)
python3 weber_county/ordinances/build_adopted_instruments.py # register + ordinances/index.csv (needs the db)
python3 weber_county/elections/build_elections.py            # canvass → election_results_by_contest.csv
python3 scripts/build_cities_db.py                           # federate into gov.db (+ search layer)
```

## Gaps / follow-ons (root TODO "County content menu")

Land-use vote layer promotion (4 bodies) + case-key↔ordinance linkage; the 2000–2014
Commission backfill; the Ogden elections re-point; RDA/interlocal agreements; county campaign
finance; the Ogden Valley City build watch. All honest, tracked, never fabricated.
