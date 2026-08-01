# Wasatch Front Regional Council (wfrc_mpo) — regional/MPO data repository

The repo's **first REGIONAL-tier entity** (`gov_level='regional'`, `level='regional'`,
fed_index **201**). WFRC is the federally-designated **Metropolitan Planning Organization**
for the greater Salt Lake–Ogden area (**Salt Lake, Davis, Weber, Morgan** counties + the
urbanized part of **Box Elder**, plus **Tooele** in the planning region). It is a
**transportation & regional-growth planning body, not a general-purpose government** — no
land use, ordinances, elections, or taxes. So this repo is **DATA-FORWARD**: WFRC's analytic
value is its **project pipeline** (what the region is funding and where) and its **small-area
growth forecast** (the region's own pop/household/jobs assumptions), NOT a per-member vote
record. Federated into repo-root `gov.db` (`cities.db`) as `gov_level='regional'`. Registry:
`registry/entities.csv` (do NOT hand-edit). Source map: `recon.md`. Read this file before
analyzing WFRC.

## The data layers (lead here) — what to reach for

WFRC's decisions are downstream of two numeric layers; start with those, not the minutes.

- **`projects/` — the transportation project pipeline (5,146 rows).** The short-range **TIP**
  (Transportation Improvement Program, **8 vintages** 2020-2025 … 2027-2032, 3,699 rows) +
  the adopted long-range **2023-2050 RTP** (roadway/transit/active-transportation, 1,447
  rows). Canonical: `projects/projects.csv` (15-col cross-MPO schema, identical to MAG so the
  two federate cleanly). Federated as `cities.db` **`regional_project`** where
  `city='wfrc_mpo'`. **This is where funding / "what is programmed" / "where is the region
  investing" questions go.** Read `projects/SOURCES.md` before quoting a field — `plan_kind`
  changes what columns MEAN (TIP `phase_or_year` = calendar year, `cost` = programmed value,
  `status` = delivery status; RTP `phase_or_year` = phase band 1-4, `cost` = base-2019 $,
  `status` = `status19vs23` change-vs-2019, NOT construction status). The 2020-2025 TIP is
  statewide-inclusive — filter by `county` for WFRC-only. Vintages are NEVER blended.
- **`projections/` — the small-area growth forecast (9,504 rows).** WFRC's Real Estate Market
  Model (**RTP-2023 vintage**), annual **2019-2050** population/households/jobs for 98 WFRC
  city-areas + a WFRC-region total. Canonical: `projections/wfrc_mpo_projections.csv` (9-col
  repo projection schema). Federated as `cities.db` **`projection`** where `city='wfrc_mpo'`.
  **This is where growth-assumption / demand questions go** — the sub-county grain Gardner's
  county series does not provide. Caveats: `population` is **HOUSEHOLD population (HHPOP)**
  (excludes group quarters — compare to Gardner `household_population`, not total);
  `households` ≠ housing units; RTP2023 tracks **Gardner V2022**, ~7% above the downward
  V2025 revision (expected, not an anomaly). The finer TAZ grain is not federated (catalog +
  `derived/taz_county_rollup.csv` only).
- **`gis/` — the Wasatch Choice growth/vision GIS catalog (18 layers, link-only).** Metadata +
  live ArcGIS REST endpoints, never mirrored (WFRC org `taguadKoI1XFwivx`,
  `services1.arcgis.com`). **This is where "where is growth planned to concentrate" /
  future-land-use / equity-overlay questions go** — `WCV_All_Centers_2023` (center density
  targets), `Generalized_Future_Land_Use_(2025)` (cross-jurisdiction MaxDUA),
  `BIG5_Housing_Jobs_Within_Centers`, `Equity_Focus_Areas_2023`. Verify `?f=json` before
  quoting; catalog, don't mirror.
- **`legislative/` + `db/` — the adoption/certification record (328 motions).** The Council's
  decision log: RTP & TIP amendments adopted, member-city **Station Area Plan certifications**,
  the WFRC budget. **This is where "what did the board adopt / certify / vote to approve" goes**
  — an adoption record, NOT a per-member vote analytic (see ceiling below).

## Which artifact for which question

- **Funding / what's programmed / where the region is investing / project cost & timing:**
  `projects/projects.csv` (fed `regional_project`, `city='wfrc_mpo'`). Read `plan_kind` first.
- **Growth assumptions / future population, households, jobs by area or region:**
  `projections/wfrc_mpo_projections.csv` (fed `projection`). HHPOP, not total pop.
- **Where growth is planned to concentrate / future land use / centers / equity overlays:**
  the `gis/index.csv` catalog (live ArcGIS endpoints).
- **What WFRC adopted / certified / voted on (RTP & TIP amendments, SAP certifications,
  budget) + who moved/seconded it:** `db/wfrc_mpo.db` (fed `motion` where `city='wfrc_mpo'`) —
  filter `body`, read `result_raw`/`outcome`, mover/seconder via `mover_person_id`/
  `seconder_person_id`. **There are NO `vote` rows** (ceiling below).
- **Thematic / keyword search of the discussion** (Wasatch Choice, a corridor, a city's SAP):
  `cities.db` `fts_minutes` filtered to `city='wfrc_mpo'` (81 rows = 53 minutes + 28 plans) — do NOT grep.
- **Who sits on the Council / which repo entities are represented:** `roster/council_seats.csv`.
- **Cross-tier (WFRC ↔ its member cities/counties):** `registry/relationships.csv`
  `member_of wfrc_mpo` edges, then join the member-entity rows.

## The vote-recording ceiling — a SOURCE PROPERTY, not a gap (verified 2016-2026)

WFRC minutes name the **MOVER** and **SECONDER** of every action and print a **narrative
tally** ("passed unanimously" / "the affirmative vote was unanimous" / "there were two
dissenting votes; however the affirmative vote was the majority and the amendment was
approved"). **Dissent is COUNT-ONLY — dissenters are never named; there is no roll call.**
This is how a high-consensus ex-officio regional board records itself — the same shape as
nephi / west_jordan PC. Consequences, honest and by construction:

- **`vote` is EMPTY** and every `motion.names_recorded=0`. Individual member vote positions do
  not exist in the source. **Do NOT run per-member vote analytics on WFRC** — the federated
  `caveat` table carries a row that surfaces this on every mis-comparison.
- Individual attribution is **mover/seconder only** (`motion.mover_person_id` /
  `seconder_person_id`; the `role` table's `n_votes` counts named **mover+seconder actions**,
  NOT roll-call votes).
- `result_raw` is the **verbatim** tally clause; `outcome` = Pass/Fail/Unknown derived from it
  (**313 Pass / 15 Unknown / 0 Fail** — a near-total-consensus body).

## Modules

```
projects/      TIP + RTP transportation project pipeline. projects.csv = 5,146 rows
               (TIP 3,699 across 8 vintages + RTP2023-2050 1,447). Attribute-only — geometry
               stays live at the ArcGIS endpoint; raw/ = per-layer JSON. SOURCES.md is
               authoritative on per-vintage field drift. derived/ = the TIP project-LIFECYCLE
               layer (2026-07-22): project_vintage (pin × vintage, 3,453) + project_history
               (per-pin entry/exit/slip/cost-drift, 1,884), fed into gov.db; read
               derived/SOURCES.md before quoting exited_tip/cost_drift_pct (statewide-2020
               scope guard, left-censoring, master-PIN variants via vintage_overrides.csv).
projections/   WFRC small-area RTP-2023 forecast. wfrc_mpo_projections.csv = 9,504 rows
               (98 city-areas + WFRC region × pop/HH/jobs × annual 2019-2050). raw/ = 3
               City_Area snapshots; derived/taz_county_rollup.csv. SOURCES.md authoritative.
gis/           CATALOG of 18 Wasatch Choice growth/vision/land-use ArcGIS layers (link, don't
               mirror). index.csv + SOURCES.md.
legislative/   53 Council minutes (markdown + provenance front-matter), 2016-01-28 →
               2026-05-28, ~5 mtgs/yr. minutes_index.csv (md_path). all_motions.csv = 328
               motions (mover/seconder full-name-resolved, verbatim result, outcome, body ∈
               {Council, Regional Growth Committee, Transportation Coordinating Committee,
               WFRC Budget Committee}). meetings_source.tsv = curated URL manifest. raw/
               retained (gitignored, ~11M).
roster/        council_seats.csv — the WFRC Council seat table (office→person→repo entity→
               voting). SEAT-STRUCTURE snapshot, not a tenure history. roster/CLAUDE.md auth.
plans/         the PUBLISHED-REPORT corpus (2026-07-20) — 28 WFRC/Wasatch Choice documents
               as a searchable text layer: adopted RTP 2023-2050, TIP 2026-2031 + Federal
               Obligation Reports + AQ conformity memos, CEDS 2023-2028/2018-2023, Wasatch
               Choice vision brochure, TLC report card + 2020-2026 award rollups, HB462 SAP
               progress reports, and land-use design guidance. This is the DATA-FORWARD build's
               published-report layer — the ADOPTION record (who moved/adopted what) stays in
               legislative/ + db/; plans/ federates ONLY into the search layer (text_path is the
               searchable artifact). index.csv (doc_class,title,adopted_date,jurisdiction,path,
               text_path,format,source_url,retrieved_date,notes) + text/ + raw/ (2 link-only
               >50MB) + SOURCES.md. TLC award rollups name repo member-cities that received
               land-use/SAP study co-funding (see plans/SOURCES.md); plans/CLAUDE.md authoritative.
db/            fetch_minutes.py (URLs→markdown) → extract_motions.py (prose→all_motions.csv)
               → build_db.py (→ wfrc_mpo.db, STANDARD 8-table schema; 53 meetings, 63 persons,
               328 motions, vote=0). DERIVED; rerun in that order, never hand-edit.
```

## Governance (context for the motion layer)

A nominally **27-member Council (21 voting by charter + 6 non-voting appointments)**, seats
held **ex officio** by member-jurisdiction mayors/commissioners + the UDOT Executive Director +
UTA trustees; the 6 non-voting appointments are ULCT, UAC, Envision Utah, one Senator, one
Representative, GOPB. Chair 2025-26 = South Jordan Mayor **Dawn Ramsey**; Vice Chair = Davis
County Commissioner Bob Stevenson. `roster/council_seats.csv` enumerates the **current member
table as 28 seats (22 voting + 6 non-voting)** — anchored on **2026-01-22**, with UDOT/UTA
carried from the clean **2025-10-23** table (the 2026 born-digital PDF garbles those columns,
`confidence=medium`); the extra voting row is a second UTA trustee the member table lists.
Standing committees — **Regional Growth Committee (RGC)**, **Transportation Coordinating
Committee (Trans Com)**, **WFRC Budget Committee** — meet separately but their actions are
**taken by the full Council in-session** and recorded in the ONE Council minutes doc; the
`motion.body` column walks those section headers (the SLC in-session pattern). Non-repo
jurisdictions (Davis/Weber/Box Elder/Morgan/Tooele counties + their cities, UDOT, UTA, the
Legislature) sit on the Council too and are flagged **external** — never invented as repo
entities. Repo-entity seats: **slc** (Mendenhall), **south_jordan** (Ramsey, Chair), **sandy**
(Zoltanski), **west_jordan** (Burton), **taylorsville** (Overson), **herriman** (Palmer),
**ogden** (Nadolski), **salt_lake_county** (Wilson + Winder Newton), **draper** (Walker,
non-voting ULCT), plus **millcreek** (Silvestrini) in the 2025 roster.

## Provenance & honest gaps

- Minutes fetched from the **live** wfrc.utah.gov file tree (paths discovered via old-site
  Wayback CDX). Born-digital text (`pdftotext`; one 2016 .docx via `textutil`).
- `provenance`: **312 `minutes`** (FINAL/APPROVED) + **11 `minutes_draft`** — the two
  draft-only meetings **2023-01-26** and **2026-05-28** (no FINAL published; filterable).
- **Floor = 2016** (no WFRC Council minutes online before 2016-01-28 — honest floor, not a
  gap). 2016 also had .WMA audio, not ingested.
- **Name partials**: later minutes reference members by surname/first-name only; canonicalized
  to the fullest corpus name ONLY when unambiguous (surnames collide — never guessed). The
  canonical authority is the MOVER/SECONDER corpus, not the attendance tables, so exactly
  **one** honest single-token partial survives: **`Froerer`** — the minutes name him
  "Commissioner Gage Froerer" only in member/attendance blocks, never as a mover or
  seconder, so the surname is not promoted. He is a real person recorded by surname, not a
  fabrication. (The eight FIRST-name-only rows that used to sit here — `Bob`, `Jeff`, … —
  were an extractor truncation, removed 2026-07-29; see below.)
- **⚠ Person-layer repair 2026-07-26 (audit F5).** `clean_name()` stripped punctuation
  BEFORE testing a token, so a name ran past the sentence boundary and **12 non-existent
  people** sat in the federated `person` table — `Mark Shepherd No`, `Bob Stevenson This`,
  `Carmen Freeman Amendment`, `Joy Petro With`, and `Clinton City` (a jurisdiction, from
  "Mayor Brandon Stanger **of Clinton City** made a motion"). Fixed: stop at sentence
  punctuation, a jurisdiction stop-list, and a name run that may span "of <City>" so the
  title-led name is captured. A capture with NO office title but a jurisdiction word now
  returns "" — honestly unattributed rather than a place recorded as a member.
  `db/person_aliases.csv` additionally merges 5 evidence-backed spelling variants
  (`Bob Stevension`, `JoAnne Seghini`, `Tamara Tran`/`Tran`, `Mark Shephard`), each with a
  non-co-occurrence proof. **person 86 → 70; motions unchanged at 323.**
- **⚠ Person-layer repair 2026-07-29 (audit F5, second half — the OPPOSITE truncation).**
  The 2026-07-26 pass stopped the name run running PAST the sentence; it did not fix the
  run stopping SHORT. The run required whitespace after every token and `,` is not in the
  token class, so **a name closed by a comma lost its last token**: *"seconded by Mayor Bob
  Stevenson, and the vote…"* captured only `Mayor Bob ` and minted a person called **`Bob`**
  — likewise `Carlton`, `Jeff`, `Joe`, `Mark`, `Monica`, `Rob`, `Shawn`, all splitting real
  members already in the table, and **`Rob Dahle` (Holladay) was absent from the entity
  entirely**. These were the "single-token honest partials" the bullet above claims — they
  were an EXTRACTOR artifact, not a source limit. Fixed with a comma-tolerant run
  (`_NAMERUN_C`) used ONLY where an explicit cue proves the run is a name ("seconded by",
  "motion was made by", or the motion verb). The bare `<run>seconded` alternative keeps the
  STRICT run: there a trailing comma means the preceding text is a clause, and the tolerant
  form made an earlier position win, recording *"…certify the Farmington FrontRunner Station
  Area Plan, seconded by Mayor Troy Walker"* as a seconder named **"Station Area Plan"**.
  Also added `ORG_TOK` (committee/council/board/…) alongside `JURISDICTION_TOK`: WFRC uses
  appositives — *"Mayor Tom Dolan, Chair of the Budget Committee, made a motion"* — and the
  run cannot cross the lowercase "of the", so the leftmost run it can match is
  `Budget Committee,`; that now returns "" (motion skipped, honestly unattributed) instead
  of minting a person called **"Budget"**. **person 70 → 63** (8 truncation artifacts
  removed, `Rob Dahle` gained); **motions 323 → 324** — the one gain is a REAL motion the
  comma had hidden from the anchor entirely (2024-03-28 *"Mayor Bob Dandoy, made a motion
  directing WFRC staff to update the RTP amendment process…"*, seconded by Mayor Brandon
  Stanger, passed unanimously). 11 mover/seconder values completed to the full name printed
  verbatim in the source; **0 motions lost, `vote` still 0, outcomes 309 Pass / 15 Unknown /
  0 Fail.** The `Tami`/`Tamara Tran` pair the 2026-07-25 audit refused to rule out as a
  genuine 2-person collision is now **positively resolved as ONE person**: WFRC's own
  printed member table carries a single continuous seat (Kaysville Mayor) named
  `Tamara Tran` 2024-01→2025-03 and `Tami Tran` 2025-10→2026-05, and `Tran` is the only
  occurrence of that surname in the whole 2016-2026 corpus (evidence recorded in
  `db/person_aliases.csv`).
- **✅ CLOSED 2026-07-31 — the 4 APPOSITIVE motions are now extracted (`motion` 324 → 328).**
  The gap the 2026-07-29 pass measured and deferred: the name run cannot cross a lowercase
  connector ("of the") or a mid-run comma, so where WFRC writes the mover as
  `<Titled Name>, <appositive>, made a motion` the leftmost run the anchor could reach was
  the appositive itself, and the ORG/jurisdiction guard correctly returned "" rather than
  invent a member — dropping the whole motion. Recovered, each verified verbatim against the
  source: **2017-03-23** *"Mayor Tom Dolan, Chair of the Budget Committee, made a motion"*
  (WFRC Budget Committee, sec. Ben McAdams); **2020-08-27** *"Carlton Christensen, UTA Board
  Trustee, …"* (Council, sec. Dirk Burton); **2023-08-24** *"Mayor Mike Caldwell, Ogden City,
  …"* and *"Mayor Jeff Silvestrini, Millcreek City, …"* (both RGC, Station Area Plan
  certifications). Outcomes 309 Pass → **313 Pass / 15 Unknown / 0 Fail**; `vote` still **0**
  and `names_recorded` still **0** — the ceiling is untouched, these are adoption records.
  **How the fix avoids the collateral damage the original entry warned about:** `ANCHOR` is
  **UNCHANGED**. It doubles as the window-boundary list (`end = movers[i+1].start()`), so
  widening it would silently re-cut every motion window in the corpus. Instead
  `recover_appositive()` runs ONLY in the branch where the primary run already yielded no
  mover, under three guards — active (`n1`) form only; a structural test that we are still
  inside one sentence mid-appositive; and **attestation**, the recovered name must already be
  a mover/seconder elsewhere in the corpus (a two-pass build), so an uncorroborated name is
  dropped, never recorded. Consequences proved by full-corpus diff: **4 added, 0 removed, 0
  changed**, and **person stayed 63 — nobody was invented**. The 5th dropped anchor,
  *"With no further business, the Commissioner moved to the next item"*, is navigation and
  **correctly STAYS dropped** (the text behind it ends in the lowercase "business", so no
  name run exists to recover).
- **Verbatim fix riding along (2026-07-31).** The `the (?:affirmative )?vot(e|ing)…`
  result-clause alternative is tried before the generic ones, so on 2023-08-24 the PRECEDING
  sentence *"Mayor Dandoy, as Mayor of Roy City, abstained from the vote."* beat the real
  clause and stored `result_raw="the vote."` / `outcome=Unknown` for a motion the source says
  was *"approved unanimously with one abstention."* Now `(?<!from )`-guarded — a recusal
  clause is not a result clause. Lookbehind only: **all 168 genuine "the vote/voting was
  unanimous" captures are unchanged** (proved by the same diff).
- **Known residual (not a defect):** the two 2023-08-24 SAP motions carry a **blank
  seconder**. Their seconders are appositives too (*"Commissioner Jim Harvey, Weber County,
  seconded"* / *"Salt Lake County Councilmember Aimee Winder Newton, seconded"*), and the
  bare `<run>seconded` alternative deliberately keeps the STRICT (comma-intolerant) run —
  loosening it is what once recorded a seconder named *"Station Area Plan"* (see the
  2026-07-29 note). Blank is the honest value; a mover-side recovery does not license a
  seconder-side one.
- **⚠ Verbatim + corpus repair 2026-07-26 (audit F10/F11).** 13 `result_raw` values were
  stored one character short (all began `"ith "`) because an unanchored `it` alternative
  matched inside "W**it**h" — a cardinal-rule-2 violation, now word-boundaried (**13 → 0**).
  And the Google-Docs/Skia exports wrap every word in U+202A-E/U+2066-9 marks: the parser
  stripped them but the **markdown did not**, so 7 files sat in `fts_minutes` with 14-19%
  of their characters unsearchable. `fetch_minutes.py` now strips at write time —
  **as a SPACE, never as ""**: in these PDFs the marks ARE the word separators, and
  deleting them glued lines into "MayorDustinGettelmadeamotion…", costing 40 motions and
  2 whole meetings before it was caught.
- **No historical seat-tenure roster** (only the current seat structure) — documented future
  item; the raw material is every meeting's printed member table.
- **DRAFT RTP2027** (next cycle, `CITYAREA_RTP27_gdb`/`COUNTY_RTP27_gdb`/preferred-scenario
  layers) is the refresh seam — catalogued in `gis/`, **NOT** ingested into projects/
  projections. Never blend vintages. The 2027-cycle vision is being branded **"Wasatch
  Choice for 2054"**.
- **Source-drift recorded as-is (not guessed):** TLC program partner listings differ across
  WFRC's own materials (FY25 funding packet says Salt Lake County; the current TLC page says
  GOPB), and WFRC's WFEDD/EDA designation year appears as both **2013** (history page) and
  **Aug 2014** (WFEDD program sheet). Both recorded, neither resolved.

## Rebuild

```
python3 wfrc_mpo/db/fetch_minutes.py      # meetings_source.tsv -> minutes markdown + index
python3 wfrc_mpo/db/extract_motions.py    # minutes -> legislative/all_motions.csv
python3 wfrc_mpo/db/build_db.py           # -> db/wfrc_mpo.db (standard 8-table schema)
# projects/ + projections/ refresh by re-querying the ArcGIS services (see each SOURCES.md)
python3 scripts/build_cities_db.py        # federate into gov.db (run by the integrator, NOT here)
```
Gates: FK check 0, integrity ok, idempotent (verified). `vote`=0 and `names_recorded=0` are
CORRECT (the ceiling), not a build defect.
