# civic-data — how to answer questions with this repo

**44 registered Utah government entities in a 4-tier model** (41 built + the 3
**registered-only** reference entities `udot`/`uta`/`wasatch_county`) — **31 cities/towns**
(`<city>_city_council/`), **8 counties**, **2 metropolitan planning organizations
(MPOs)**, and **the State of Utah** — all under one **entity model** (SCHEMA_SPEC §0):
every government unit is a flat entity with a `level` (city / county / regional / state),
federated into **`gov.db`** with a `gov_level` column; geography lives in
`registry/relationships.csv`, not the folder tree. Non-city entities are incorporated **on
their own terms** — an MPO is programmed projects + projections, not roll calls; a
db-less county is elections + text corpora — so read each entity's own `CLAUDE.md` before
analyzing it. Generated hierarchy map: **`registry/HIERARCHY.md`** (never hand-edit).

- **Cities/towns (31)** — the original 16, joined 2026-07-08..12 by a 15-city SLCo wave
  (murray, herriman, draper, riverton, alta, midvale, cottonwood_heights, holladay,
  south_salt_lake, bluffdale + the **five metro-township-origin entities** white_city,
  kearns, magna, copperton, emigration_canyon — townships 2017-2024 → cities/town 2024
  under HB35; **data floor 2017**, their full history).
- **Counties (8)** — `salt_lake_county` (the first, 2026-07-11, reference impl), joined
  2026-07-20 by the value/effort-gated wave: `utah_county` (FULL tier), `weber_county` /
  `cache_county` / `summit_county` (MID tier — weber+cache carry FULL NAMED legislative
  roll calls, richer than SLCo's minutes), `washington_county` (LIGHT+) and `juab_county`
  (CHEAP-ONLY) both **db-less but federated**, and `wasatch_county` (**registered-only** —
  carries Park City's second county edge; no build yet).
- **MPOs (2)** — `wfrc_mpo` (Wasatch Front Regional Council) and `mag_mpo` (Mountainland
  Association of Governments): `level='regional'`, **DATA-FORWARD** entities (programmed
  projects + city-area projections + regional GIS; council/board minutes are tally-only).
- **State (1)** — `ut_state`: a land-use/housing legislation subset + Ombudsman advisory
  opinions + LUDMA statutes + state-grain projections.

**`gov.db`** (repo root) is the federated database — the **cities.db → gov.db rename**
(2026-07-20); a `cities.db` symlink remains for back-compat and `scripts/build_cities_db.py`
is still the builder. Built for housing/growth/development research. Normative schema:
`SCHEMA_SPEC.md`. Human overview: `README.md`. Measured coverage: `coverage.json`.

**The entity list is `registry/entities.csv`** (loaded by `scripts/entities.py`;
`scripts/cities.py` is a back-compat `level=='city'` SHIM — never hand-edit it). To ADD an
entity, append to the registry + `registry/relationships.csv` and regenerate
`registry/HIERARCHY.md` — see `/build-city-data-repo` (city) or `/build-county-data-repo`
(county, reference impl `salt_lake_county/`).

**Work tracking (restructured 2026-07-31 — four files, four functions):**
- **`TODO.md`** — ONLY terminating work: [DEBT] (wrong/missing values, evidence-cited) +
  [GATED] (owner decisions) + the active PUBLISH GATE package. Check it when asked "what's
  next". Its open-box count is a true measure of work owed.
- **`LEADS.md`** — options, expansion menus, acquisition leads, WATCHES table. **File new
  leads/follow-ups HERE as one-line bullets (date + what was OBSERVED + evidence pointer),
  never in TODO.md.** An item enters TODO.md only as [DEBT] with a primary-source citation
  showing a wrong or missing value (≤3 promotions per session, each verified at the source
  first — backlog entries are hypotheses), or as [GATED] created by the owner. No umbrella
  items: one box, one terminating task, ≤15 lines.
- **`TODO_ARCHIVE.md`** — closed records, verbatim, under dated anchors. **Closing an item
  moves its full dated record there IN THE SAME SESSION**, leaving one changelog line in
  TODO.md. A closure that falsifies a claim in CLAUDE.md/README updates that claim in the
  same session.
- **`HANDOFF.md`** — the CURRENT session banner only (overwrite it; move the prior banner to
  TODO_ARCHIVE.md). Standing operational rules live in **`GOTCHAS.md`**; the publish
  readiness predicates in **`SHIP_GATE.md`**.

## Cardinal rules

1. **Never fabricate.** Blank `member`/`vote` = tally-only motion (source printed no
   names); `minutes_unrecovered.csv` = meeting exists, minutes don't; empty
   `all_comments_clean.csv` = city publishes none. **Honest gaps are data** — report
   them, never fill them.
2. **City-faithful values are never overwritten.** `result` and `motion_type` are
   verbatim/native; normalized fields live *alongside* (`motions_std.csv`,
   `crosswalks/` — see SCHEMA_SPEC.md §8). Corrections go through documented override
   files (`db/vote_overrides.csv`, `db/overrides.csv`, `db/referral_overrides.csv`),
   never in-place edits.
3. **Derived layers (`db/`, `weeks/`) are regenerated, never hand-edited.** Canonical
   truth is the flat CSVs + minutes markdown.

## Which artifact for which question

- **Aggregates / time series** (votes by member/type/year, comment volume, contested
  rate): the **flat CSVs** — `meeting_minutes/all_votes.csv`,
  `planning_commission/all_votes.csv`, `public_comments/all_comments_clean.csv`,
  `election_results/<city>_races.csv`.
- **Cross-body / project-level questions** (did the PC recommend against something the
  Council passed? one project's full timeline; a member's record across bodies): the
  **db** — `db/civic.db`, read `db/SCHEMA.md` first; start from views
  `v_referral_chain`, `v_project_timeline`, `v_member_record`, `v_contested`.
  Referral confidence: `high`≈exact, `medium` spot-check, `low` don't quote.
- **Meeting-level context** (what happened around this vote? what did the public say
  that week?): the **`weeks/<week-ending>/` bundle** — `summary.md` first, then
  `votes.csv` / `comments.csv`; minutes are linked from summary.md (canonical files in
  `meeting_minutes/minutes/`). `weeks/index.md` lists every week.
- **Approve/deny rates, per-member approval propensity, "PC said deny → Council approved"**
  (2026-07-12): the **`motion.disposition` derived column** (approve | deny | continue |
  table | procedural; NULL = honestly unclassified) alongside `motion.outcome` (did the
  motion CARRY). The two are ORTHOGONAL — compose at query time: `disposition='deny' AND
  outcome='Pass'` ⇒ the matter was denied. Ground-truth audited across all 31 cities
  (`_audits/2026-07-12-motion-classification/report.md`); corrections go in each city's
  `db/disposition_overrides.csv`. Disposition coverage beyond the cities: cache_county
  (2,949) and mag_mpo (577) are classified; salt_lake_county, summit_county, utah_county,
  weber_county, wfrc_mpo, and ut_state carry NULL on every motion (not yet computed —
  the db's `disposition-coverage` caveat rides every non-city motion_std row).
- **Thematic / keyword questions** ("every mention of accessory dwelling units",
  "density bonus discussions"): the **FTS5 layer in `gov.db`** — `fts_minutes`
  (full minutes text across cities + counties + MPOs, **14,696 docs** from 40 entities,
  incl. 823 recovered-PMN texts since 2026-07-31),
  `fts_motion`, `fts_comment`, `fts_ordinance`, `fts_packet`.
  Query with `MATCH`, filter by the stored `city`/`date` columns, use `snippet()` for
  passages, then open the `path` for full context. Do NOT grep thousands of files. For
  the STATE land-use text corpora — the **Ombudsman advisory opinions** (309 catalogued /
  307 with text, `ut_state/advisory_opinions/` + `index.csv`) and the **LUDMA statute
  sections** (218 sections, `ut_state/statutes/text/` + `index.csv`) — read the per-file
  text under `ut_state/`. **They ARE searchable** — `fts_minutes` carries 523 ut_state rows
  (305 advisory opinions + 218 statute sections; only the 2 image-only AOs #142/#145
  remain unindexed — no text exists), so a keyword sweep can start there; the per-file
  text remains the authority for full context.
- **Regional (MPO) funding / programmed projects** ("what's in the TIP", "which projects
  got RTP money", "transit vs road spend by area"): the **`regional_project` table** in
  `gov.db` — 5,717 rows (wfrc_mpo 5,146 across 8 TIP vintages + RTP-2050; mag_mpo 571
  TIP/RTP/RPO), the canonical form of each MPO's programmed-project layer. MPO council/
  board minutes are tally-only (no roll call), so the project + projection layers — not
  votes — are the analytic surface. **Project lifecycle across vintages** (slippage,
  cost drift, entry/exit; 2026-07-22 WFRC-native Phase 1): `project_vintage` (pin ×
  vintage, 3,453) + `project_history` (per-pin, 1,884) — `pin` = UDOT ePM PIN, the
  statewide join key; 4 caveat rows guard the semantics (left-censored window,
  statewide-2020 scope, cost = programmed snapshot not expenditure, pin-only coverage).
  `udot`/`uta` are REGISTERED-ONLY reference entities (fed 302/303).
- **Population/household/employment projections** ("Gardner projections for city X",
  "regional growth to 2050"): the **`projection` table** in `gov.db` — 10,952 rows across
  **3 grains**: county (980), **regional = annual city-area grain 2019–2050** (9,832,
  wfrc_mpo + mag_mpo), and state (140).
- **State legislation** ("how did legislator X vote on housing bills", "the 2023 ADU
  bill's roll call"): the **`ut_state` db** (federated into `gov.db` as `gov_level='state'`)
  — a **264-bill land-use/housing subset 2015–2026**, 1,208 named roll calls, 27,887 NAMED
  legislator votes via the public le.utah.gov channel. **State legislators are a DISJOINT
  person population** (222 persons; never auto-join to municipal officials by surname).
- **Public comments across cities**: `gov.db` `comment` table (+ `fts_comment`);
  the per-city CSVs remain canonical.
- **Campaign finance** (who funded whom; money vs votes): `gov.db` `cf_contribution`
  / `cf_expenditure` / `cf_cycle` / `cf_candidate_person` (joins donors to `person` →
  `vote`). **Never sum `cf_filing` dollar columns** — filings overlap (interim +
  summary); `cf_cycle` is the only sanctioned per-candidate total.
- **Adopted ordinances** (what did Ordinance X do; who voted for it): `gov.db`
  `ordinance` table — `motion_id` links to the enacting motion + roll call where the
  linkage is unique (`motion_resolution='unique'`; never quote ambiguous links).
- **What source material exists for a meeting**: `gov.db` `document` catalog
  (minutes, packets, ordinances, housing plans, transcripts, PMN recoveries, with
  `has_text`/`text_path` for what's directly readable).
- **Who represents an address**: `geo/address_to_district.py`.
- **Who served when / current council / address→rep over time** (rolling roster — the
  ALL 31 city/town entities, 641 federated seat-tenure rows — completed 2026-07-13,
  doc corrected 2026-07-31): the
  **`roster/` layer** — each city's `roster/council_terms.csv` (seat-tenure intervals,
  half-open `[start_date,end_date)`, per-row `confidence` + `sources`, `VACANT` gaps) +
  `district_versions.csv`/`district_precincts.csv` (redistricting-versioned boundaries,
  prior plans kept as honest `low`/blank-geometry gaps). Federated in `gov.db` as
  `term`/`district_version`/`district_precinct` + views `v_council_current` (serving
  now) and `v_term_provenance` (per-city confidence mix); a point-in-time roster is the
  half-open interval (`start_date<=:d AND (end_date='' OR end_date>:d)`). Each
  `roster/CLAUDE.md` is authoritative per city.
- **Elections in the db** (2026-07-11, expanded 2026-07-12): federated DB form in
  `gov.db` — `election_race` (audited 25-col races, **688 rows** + containing
  `county`; **authoritative** winners/margins; view `v_election_city`) and `election_result`
  (Salt Lake County Clerk SOVC candidate tallies, 2007–2025, **5,482 rows**, covering **22
  SLCo jurisdictions** after the 2026-07-12 normalizer fixes recovered the 2019/2011
  sheet-code eras and the Draper county-straddle precincts — canonical at
  `salt_lake_county/elections/`). County canvasses (washington 2018–2025, juab 2023–2026)
  are canonical in each county's `elections/`.
  The per-city `election_results/<city>_races.csv` remain the on-disk source. RCV cities
  (millcreek; draper 2021 pilot): `election_result.rank_in_contest` is plurality order, not
  the RCV final — take winners from `election_race`.
- **Member ↔ election margin**: join `election_results/<city>_races.csv` winners to
  votes on person + year + district (normalize names — election names are UPPER-CASE,
  some `(NP)` suffixes).

## Cross-city comparisons — the rules

- **Start with `gov.db`** (repo root; `cities.db` is a legacy symlink) for any
  cross-entity question: all built entities' standard tables unioned with `city` +
  `gov_level` columns — **motions 49,105 city / 27,271 county / 977 regional / 1,208 state**;
  **member-votes 180,980 city / 38,592 county / 0 regional / 27,887 state** (regional
  minutes are tally-only, so the MPOs contribute projects + projections, not votes) —
  `motion_std` (the normalization layer — **now covers the CITY + COUNTY + REGIONAL
  tiers, 77,353 rows joined to `motion` at 100%**: city 49,105 + county 27,271 +
  regional 977, closing TODO High-priority item (j) on 2026-07-29). **The two paths are
  built differently and that is a real distinction:** city rows are read from the on-disk
  `motions_std.csv` files; counties and MPOs publish no such file (no uniform flat-motion
  shape; mag_mpo has no flat motion CSV at all), so their rows are **COMPUTED AT
  FEDERATION** by `scripts/build_cities_db.py` (`compute_motion_std_noncity`) using the
  SAME classifier, imported from `normalize_motions.py` so the tiers can't drift.
  Consequences to respect: the non-city `motion_id` join rate is 100% **by construction**,
  not evidence of extraction quality; and the `dataset` column for that tier is
  **body-derived, not a directory** — `land_use` = the entity's planning commission(s),
  `legislative` = the governing body + work sessions + the agency boards it sits as.
  **Honest classification ceilings** (share of motions the source text leaves as
  `Other`/`low`, each carried as a `motion-std-classification-ceiling` caveat): weber
  8.6% · summit 18.9% · wfrc 26.2% · cache 27.7% · slco 35.6% · utah 42.0% · **mag 61.1%**
  (MPO motions are about programming and funding, not land-use matters — a real property,
  not an extraction failure). **`ut_state` has NO motion_std rows and that is the
  INTENDED state, not a gap** (owner ruling 2026-07-29): the municipal `motion_type_std`
  vocabulary does not describe legislative BILL-STAGE votes, and the problem is
  structural — ut_state has zero purpose-built tables in `gov.db` and its 264 bills sit in
  `application` (the municipal-development-application slot), where `wfrc_mpo` by contrast
  was incorporated on its own terms with four first-class tables. The state tier is to be
  reevaluated the same way — TODO **"STATE TIER — reevaluate how `ut_state` is integrated,
  ON ITS OWN TERMS (owner ruling 2026-07-29)"**; until then query ut_state's `motion`/`vote` rows directly.
  `v_coverage` now returns rows for the 7 normalized non-city entities, plus explicit
  `(no vote layer)` rows for the db-less-by-design washington_county / juab_county and a
  `(no motion_std layer)` row for ut_state. Also here: the crosswalks as
  tables, and a **`caveat` table** the views join against so mis-comparisons surface on
  every row. **The caveat table carries the data-forward framing for the non-city
  entities** — an MPO's empty vote layer and a db-less county's deferred vote/pipeline
  layers are honest properties, not gaps to fill. Views: `v_contested_all`,
  `v_member_record_all`, `v_landuse_outcomes`, `v_pc_divergence` (excludes low-confidence
  referrals by design; since 2026-07-12 also covers legislative `Other` items — historic
  districts, area/master plans), `v_coverage`. Read `gov_db_SCHEMA.md` first. DERIVED —
  regenerate with `python3 scripts/build_cities_db.py` after any per-entity db rebuild;
  sandy's `legistar_*` extension tables live only in its own `db/sandy.db`.
- **Never aggregate raw `result` or `motion_type` strings across cities.** Each city
  has its own labels (8–33 distinct result strings; Ogden files rezones under
  `Ordinance`, Lehi under `Land-Use/Zoning`, Sandy PC is one `Planning Item` blob).
  Use the normalization layer: `motions_std.csv` per city+dataset (joinable on
  `(source, motion_no)`; gives `motion_type_std`, `land_use_type`, `action_class`,
  `outcome`, tallies, `vote_mode`) and the repo-root `crosswalks/`
  (motion_type/body/vote_values) — both loaded into `gov.db`.
- **Respect vote-value ceilings** (SCHEMA_SPEC §4): Orem records Aye/Nay only; Nephi
  is ~80% tally-only; West Jordan PC names only dissenters/absentees. An absent
  Abstain/Recuse/Absent is a recording limit, not member behavior.
- **Respect coverage asymmetries**: comments substantive only in SLC + Park City
  (23 honest zeros, 6 slivers incl. millcreek's in-packets 27); elections 2019+ except
  SLC 2007+; SLC votes 2021+;
  Provo PC 2025+; Ogden RDA/MBA 2022–23 never acquired.
- **Recovered vs audited votes — the `provenance` column has TWO vocabularies by tier
  (corrected 2026-07-31).** CITY tier: `minutes` = audited primary (46,240 motions);
  recovered values (2,932 total) are `pmn_roa` 377 / `pmn_minutes` 1,193 (Utah Public
  Notice), `agendacenter_minutes` 592 (SSL CivicPlus ArchivedMinutes), `wayback_minutes`
  171 (holladay + cottonwood_heights), `citysite_minutes` 40 (west_jordan legacy host),
  `doccenter_draft` 525 + `packet_carve` 34 (ogden PC draft-sourced recovery, approval
  verified downstream). Filter city-tier audited-only with **`gov_level='city' AND
  provenance='minutes'`**. ⚠ NON-CITY tier: the same column holds EXTRACTOR names
  (tesseract, county_portal, legistar, poppler, citysite_ocr, le_utah_website,
  magutah_site …), and cache_county reuses the strings `citysite_minutes` (1,405) and
  `wayback_minutes` (201) with county-local meanings — a bare `provenance='minutes'`
  filter silently drops ~84% of county motions. Never apply the city-tier filter
  cross-tier; splitting recovery-channel from extractor into two columns is a queued
  candidate fix.
- Contested votes are the signal everywhere — `gov.db` `v_contested_all` now UNIONs
  **named** dissent (a Nay/Abstain/Recuse row) with **tally** dissent (a printed
  nay/other count with no roll call), splitting authoritative `tally_*` counts from
  attribution-only `named_*`; these councils are high-consensus (~4–16% contested).

## Per-city quirks (one-liners — details in each city's CLAUDE.md)

- **slc** — Council adjourns/reconvenes **in-session as RDA/CRA/LBA** (4 bodies in one
  minutes doc; `body` column walks section headers); votes 2021+ (2020 is OCR); council
  votes LLM-extracted, PC pure-regex; comments via Claude Vision (13,334); elections
  2007+; addresses are grid intersections, not parcels.
- **lehi** — Granicus; the **expand-city-sources pilot** (packets/housing_plans/
  ordinances/pmn_backfill/transcripts/campaign_finance); 8 Granicus double-event
  duplicate pairs repaired 2026-07-02.
- **logan** — council + RDA split from combined minutes; some tally-only blanks; PC has
  52 OCR files.
- **nephi** — **mostly tally-only** (only ~51 council motions name voters — source
  limit, not extraction); PC footer-bleed FIXED 2026-07-19 (FOOTER_RE strip; 2 motions
  cleaned); sparse CRA folds into council minutes as `body=CRA` (PMN body 5737
  harvested 2026-07-19 — complete within floor, one 2023-12-19 honest gap).
- **ogden** — separate RDA/MBA meetings via `body` column, but **2022 RDA/MBA and 2023
  MBA sets confirmed unavailable** (not on PMN); 7 of the 2023 RDA minutes recovered
  2026-07-06 into `pmn_backfill/` (promotion into the audited layer pending); 2022
  council minutes re-OCR'd + re-carved 2026-07-02; minutes come from year compilation
  PDFs.
- **orem** — **Aye/Nay only** (no absences/abstentions ever recorded); 68 OCR files;
  PC 2025-10-15 minutes unrecoverable (city mis-upload).
- **park_city** — meets **Thursday**; 2 mayoral tie-breaks stored as `vote.note`
  in parkcity.db (flat CSV value `"Nay (Mayor tie-break)"`); 9 contradictory source
  Aye+Nay pairs resolved via **`db/vote_overrides.csv`** (db build prints
  reconciliation); CivicClerk.
- **provo** — comments are letters extracted from agenda packets (81, page-walk
  classifier); PC dataset 2025+ only (source limit); OnBase portal.
- **sandy** — **the Legistar API city**: PC votes built from the API, not minutes
  (PC has no minutes files; PC `source` is not a file path); db is standard-schema
  since 2026-07-02 (2.6) — council votes minutes-primary like every city, full
  Legistar harvest preserved in `legistar_*` extension tables (incl. `Nonvoting` +
  Board of Adjustment), `app_match_method='matter_id'` extension; mayor doesn't
  vote; narrative tallies name only dissenters (majority honestly unnamed); 63
  PUA-garbled minutes decoded 2026-07-02.
- **st_george** — meets **Thursday**; 2020–21 minutes backfilled from PMN (Revize
  archive holds 2022+); one 2025-10-09 work meeting
  unrecoverable (city published the wrong file — logged); `result` strings contain
  embedded prose; heavy PMN supplementation (91 docs).
- **vineyard** — meets **Wednesday** (modal — schedule varies); many joint
  work-session docs; 29 raw agenda packets retained (2.5 GB); wrong/duplicate-doc
  defects repaired 2026-07-02.
- **west_jordan** — PrimeGov; **PC is tally-only + OCR-junky** (names only
  dissenters/absentees — zero named Ayes); council solid.
- **west_valley** — case-number city (items keyed `Z-`/`PUD-`/`GPZ-`…, not names —
  referral layer is deliberately thin, 11 hand-verified links); 3 motions where minutes
  printed "Unanimous" over a dissenting roll call (truthful roll call retained); no
  published comments; separate RDA + MBA meetings (real, populated).
- **south_jordan** — CivicPlus; mayor is uncounted in roll calls; PC names only
  dissenters/abstainers/absentees (no named Ayes); comments submit-only (honest zero);
  2020 minutes partly recovered via PMN (13 docs in `pmn_backfill/`, merge pending).
- **millcreek** — meets **Monday**; data floor **2016** (incorporated 2016-12 — full
  history, not a gap); **mayor VOTES** (5-member roll incl. mayor); 2017–2021 votes
  mostly tally-only by source (named roll calls start ~2022); has a CRA body; comments
  harvested from PC packets (in-packets layer BUILT 2026-07-19, 27 letters; retained-
  packet floor — see the millcreek comments caveat).
- **taylorsville** — meets **Wednesday**; CivicEngage Central; **mayor does NOT vote**
  (executive-mayor form; council elects its own Chair); RDA body; mid-2025+ minutes are
  RICOH scans (OCR — PMN born-digital upgrade queued); comments submit-only (honest
  zero); minutes markdown carries provenance headers (the newest-build convention).
- **murray** — 5 districts + non-voting exec mayor; the 2023 council-minutes loss and the
  post-2022-11 PC gap were **both closed 2026-07-16** (PMN promotion: all 18 missing 2023
  council + 59 PC minutes; PC now spans 2023-01→2026-05; only PC 2025-04-17/2025-07-17
  minute-less); voice votes tally-only; Hales D5→Mayor 2022 (roster seam).
- **herriman** — meets **Wednesday**; 4 districts + **VOTING mayor** (max roll 5);
  in-session CDRA/HCSEA/HCFSA agencies via the `body` column; PrimeGov.
- **draper** — **all at-large** (5 + non-voting mayor, 1 tie-break); **straddles Salt Lake
  + Utah counties** (SLCo administers its elections); 2021 was an RCV pilot (stored
  first-choice tallies — don't read winner_pct as a final margin); Granicus; the PC is
  the contested body (201 vs 15).
- **riverton** — 5 districts + tie-break-only mayor; **PC names members only on divided
  votes** (unanimous = tally-only, 555 rows); D3↔D4 renumbered at the 2022 redistricting
  — join on person, not district number.
- **alta** — **Town of Alta (~380 pop), sparse by design** (~12 meetings/yr); 4 at-large
  + **VOTING mayor** (max tally 5); PC 100% tally-only; minutes via PMN; exclude "Alta
  Canyon" rec-district decoys; 2021 election privacy-suppressed.
- **midvale** — 5 districts + tie-break-only mayor; in-session RDA; 2020-21 minutes are
  OCR (the "Gouncil" roll-dropout era — vote-layer repair queued in TODO); otherwise a
  high-attribution named-roll city; Gettel D5→Mayor 2025 (roster seam).
- **cottonwood_heights** — 4 districts + **VOTING mayor** (max 5); in-session CDRA;
  decayed portal backfilled from PMN; result strings are word-form prose ("Passed
  4-to-1" — deliberately unparsed by the tally regex; failed tallies print nays-first);
  clerk-error tallies retained verbatim.
- **holladay** — meets **Thursday**; 5 districts + **VOTING mayor** (rolls reach 6);
  in-session RDA + LBA; prose results (use `motions_std` for tallies); PC 2020 H1 +
  2021 H1 minutes recovered 2026-07-16 via Wayback (`provenance='wayback_minutes'`);
  2020 H2 / 2021 H2 / 2023 PC minutes remain genuine gaps (dead on every channel).
- **south_salt_lake** — the old "coverage cliff" is SUBSTANTIALLY CLOSED (2026-07-16):
  119 recorded minutes 2022–2026 (Council 75 / RDA 29 / PC 15) recovered from the
  CivicPlus ArchivedMinutes slot and promoted (`provenance='agendacenter_minutes'`);
  residual = 214 genuinely-unpublished dates, mostly council WORK meetings (COVERAGE.md
  has the precise ledger); 5 districts + 2 at-large + non-voting exec mayor (rolls of 7).
- **bluffdale** — 5 at-large; mayor tie-break-only in Council but **VOTES as Chair in
  in-session RDA/LBA** (rolls of 6 there); straddles SLCo + Utah Co (Camp Williams,
  unpopulated); 2021 RCV pilot; 2023-26 partial-OCR seam.
- **white_city** — meets **Thursday**; metro township 2017-2024 → **CITY 2024** (HB35);
  voting Chair/Mayor in both eras (max 5); **data floor 2017**; PC layer BUILT 2026-07-16
  from PMN body 5879 (22 minutes / 106 motions, MSD "Meeting Minute Summary" form,
  mover/seconder-only naming); three council vote-grammar eras (most rows tally-only).
- **kearns** — meets **Monday**; township → city seam 2024/2026 (city era: 4 districts +
  VOTING mayor); MSD-staffed PC (OAM case keys); narrative tallies name only dissenters;
  2017–mid-2018 PMN blobs purged (honest gap); floor **2017**; elections:
  `kearns_races.csv` is authoritative (parsed from raw SOVC).
- **magna** — **the presiding officer's vote FLIPS at the 2024 HB35 seam** (township
  Chair-titled-Mayor VOTED; the 2026+ elected exec mayor does NOT); 5 districts;
  in-recess CRA; floor **2017** (2017–mid-2018 PMN-purged); narrative-tally council
  with dissent-only naming (41/42 split votes carry named dissenters since the 2026-07-12
  T3.1(e) repair; 11 no-result-printed motions have NULL outcome).
- **copperton** — **~800-pop town, sparse by design**; township → TOWN 2024; voting
  Mayor/Chair both eras; meets **Wednesday**; floor **2017** (2017-02→2018-06 purge gap
  is GENUINE); PC cancels most meetings; almost entirely tally-only.
- **emigration_canyon** — ~1.6k pop; 5 at-large incl. **peer-selected VOTING mayor**
  (Millcreek pattern); minutes via PMN only (no city CMS); floor **2017** (recovered
  from 2018-10 — earlier PMN blobs purged); narrative-tally council; schedule varies
  (modal Tue). Its own CLAUDE.md predates the final build (says partial; the full
  db/weeks/geo/elections layers exist).

## Counties, MPOs & state quirks (one-liners — each entity's CLAUDE.md is authoritative)

- **salt_lake_county** — the first county + reference impl (2026-07-11); County Council
  (9) + elected Mayor; agencies + PC votes/minutes, adopted ordinances, dev pipeline, the
  canonical SOVC election canvass (federated `election_result`), plans, projections, GIS.
  County motions have NULL `disposition` (not yet computed).
- **utah_county** — Board of Commissioners (3); FULL tier, 4 bodies incl. PC + Housing
  Authority; the source names voters **2015–2019** and is tally-primary **2020+**, with
  dissent nameable throughout. The two extractor bugs found by the 2026-07-25 audit were
  **REPAIRED the same day** (motions 10,089→11,218, member-votes 2,765→4,705, contested
  31→84 with named divided votes in every year 2019–2026; record:
  `utah_county/db/REPAIR_2026-07-25.md`). Honest residual, caveat-carried in the db: 42 of
  63 2020–24 parenthetical roll blocks remain uncaptured (OCR-fragmented) and several
  2020+ persons are surname-only. Per-member analytics are fullest 2015–2019.
- **weber_county** — Board of Commissioners (3); MID tier but **NAMED-primary minutes**
  (99.6% named rolls 2015+, depth to 2000 — richer than SLCo); land_use is FTS-only (PC
  consolidation seam 2025-12-03, Ord 2025-27).
- **cache_county** — County Council (7) + non-voting elected Executive; MID tier; **full
  named rolls 2021+ born-digital** (2015–20 scanned tally-only); PC tally→named seam
  2024-11-07.
- **summit_county** — County Council (6) + Manager; MID tier, tally-primary (no API);
  **two planning commissions** for land use (Snyderville Basin + Eastern) + a 571-app dev
  pipeline; council coverage 2023+ born-digital (2015–22 scanned ledger).
- **washington_county** — Board of Commissioners (3); **LIGHT+ tier, db-less**: elections
  canonical 2018–2025 + minutes FTS corpora (78% OCR — 226/290, measured 2026-08-01) +
  plans/ordinances/gis; **vote layer
  + dev pipeline explicitly DEFERRED** (honest, not a gap).
- **juab_county** — Board of Commissioners (3); **CHEAP-ONLY tier, db-less, thin**:
  elections canonical 2023–2026 (3 official channels; 2019/2021 municipal = honest gap) +
  projections + a thin GIS catalog.
- **wasatch_county** — **registered-only** (2026-07-20); exists to carry Park City's
  second within-county edge; no build yet (backlog with the remaining 22 counties).
- **wfrc_mpo** (Wasatch Front Regional Council) — `level='regional'`, DATA-FORWARD:
  `regional_project` (8 TIP vintages + RTP-2050, 5,146 rows) + annual city-area
  projections 2019–2050 + Wasatch Choice GIS; **Council motions 2016+ are tally-only**
  (mover/seconder named, **dissent count-only — vote table empty by source**).
- **mag_mpo** (Mountainland Association of Governments) — AOG (Utah/Summit/Wasatch),
  Provo–Orem urbanized-area MPO; DATA-FORWARD: `regional_project` (TIP/RTP/RPO, 571) +
  city-grain projections + Housing Unit Inventory/Wasatch Choice GIS; MPO Board+TAC
  minutes 2014+ tally-only (no roll call ever); **the MPO Board is UTAH-COUNTY-only**
  (summit/park_city sit on the AOG/RPO side).
- **ut_state** — Legislature + executive agencies; a **264-bill land-use/housing subset
  2015–2026** (1,208 named roll calls, 27,887 NAMED legislator votes via public
  le.utah.gov); **legislators are a DISJOINT person population** (222 persons — never
  surname-join to municipal officials) + ~307 Ombudsman advisory opinions + LUDMA statutes.
  **2025 LUDMA RECODIFICATION**: 10-9a→**10-20**, 17-27a→**17-79** (older repo docs cite the
  pre-recodification numbering — that is historical fidelity, not an error).

## Tooling

- `python3 scripts/validate_entity.py <slug|dir>` — entity-aware conformance report
  (PASS/WARN/FAIL; delegates cities to `validate_city.py`, applies the right checks for
  county / regional / state / db-less entities; NOTE: city delegation regenerates two
  per-city validation artifacts — `votes/_validation_report.txt` + the votes-derived
  `meeting_minutes/roster.csv` — so expect mtime changes). `validate_city.py` remains
  the city-only validator it wraps.
- `python3 scripts/build_hierarchy.py` — regenerates `registry/HIERARCHY.md` from
  `entities.csv` + `relationships.csv` (never hand-edit the map).
- `python3 scripts/build_coverage.py` — regenerates `coverage.json` from the files.
- Per city: `python3 build_weeks.py` (weeks), `python3 db/build_db.py && python3
  db/build_referrals.py` (db) — idempotent.
- Skills: `/audit-city-data` (QC method), `/build-city-data-repo` (new city),
  `/build-county-data-repo` (new county — reference impl `salt_lake_county/`),
  `/expand-city-sources` (six new source types), `/check-slc-comments` (SLC refresh),
  `/fresh-instance` (hand off a long-context session to a new remote-controllable
  instance primed from HANDOFF.md).
- Backups of everything modified during remediation: `_backups/2026-07-02/`.
