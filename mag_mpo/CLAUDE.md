# Mountainland Association of Governments — MPO (mag_mpo) — regional data repository

The repo's **second REGIONAL-tier entity** (`gov_level='regional'`, `level='regional'`,
fed_index **202**). Mountainland Association of Governments (MAG) is the Association of
Governments for **Utah, Summit, and Wasatch counties**; its federally-designated
**Metropolitan Planning Organization (MPO)** covers the **Provo–Orem urbanized area — Utah
County only**. Like WFRC this build is **DATA-FORWARD**: MAG's analytic value is its
**transportation project pipeline** and its **city-grain growth forecast**, NOT a per-member
vote record. Federated into repo-root `gov.db` (`cities.db`) as `gov_level='regional'` by
`scripts/build_cities_db.py` — regional bodies sit alongside cities/counties in the same
`motion`/`person`/`meeting` spine. Registry: `registry/entities.csv` (do NOT hand-edit).
Source map: `recon.md`. Read this file before analyzing MAG.

## The data layers (lead here) — what to reach for

- **`projects/` — the transportation project pipeline (571 rows).** Three program families:
  short-range **TIP** (UDOT ePM snapshot, 225 rows), adopted **2023 RTP** (highway/transit/
  active-transportation, 262 rows), and the **Wasatch Back RPO** 2023 plan (Summit+Wasatch
  rural, 84 rows). Canonical: `projects/projects.csv` (15-col cross-MPO schema, identical to
  WFRC). Federated as `cities.db` **`regional_project`** where `city='mag_mpo'`. **This is
  where funding / "what is programmed" / "where is the region investing" questions go.** Read
  `projects/SOURCES.md`: RTP vintage is recorded **per mode** (Highway = Amendment 3
  2025-12-11; Transit/Active = Amendment 1 2025-01-16 — never blended); points+lines are two
  geometries of ONE project, de-duped to one row per `project_id` (lines primary) so **cost is
  never double-counted**; TIP carries no county and RPO no cost/county (blank, never inferred).
- **`projections/` — the city-grain growth forecast (328 rows).** MAG's adopted **2023 RTP**
  socioeconomic forecast: **population** and **jobs** for 41 geographies (38 municipalities +
  3 unincorporated-county areas) × decadal 2020/2030/2040/2050. Canonical:
  `projections/mag_mpo_projections.csv` (9-col repo projection schema). Federated as `cities.db`
  **`projection`** where `city='mag_mpo'`. **This is where growth-assumption / demand questions
  go.** Caveats: control-totaled to **Gardner Vintage 2022** (matches ±2 persons; runs 3–5.5%
  BELOW the newer Gardner V2025 — expected, never blend with the V2025 rows in `utah_county/`);
  8 null jobs rows preserved (Draper + Woodland Hills, blank not 0); city grain only (the
  annual TAZ grain and households are TAZ-only → catalogued in `gis/`, not federated); no
  county/region rollup row (summing would fabricate — use the Gardner county modules).
- **`gis/` — the growth/development GIS catalog (20 layers, link-only).** Metadata + live
  ArcGIS REST endpoints, never mirrored (MAG hub `data.magutah.gov`, org
  `services2.arcgis.com/EiGeaCDLpVDPqdJ5`). Highest value: **`MAG Housing Unit Inventory`**
  (195,203 units, per-unit type + DUA), **`General Plan Land Use 2025`** (future land use +
  MaxDUA), **`Station Area Planning HB 462 Status`** (TOD housing mandate),
  **`MAG Wasatch Choice Vision Centers and Land Use`**, and the `TAZ_SE_RTP23` annual TAZ
  forecast behind the city projections. **This is where housing-supply / density / future-
  land-use questions go.** Per-county services (TAZ, geography, traffic) list the Utah-County
  endpoint + name the Summit/Wasatch analogs. Verify `?f=json`; catalog, don't mirror.
- **`legislative/` + `db/` — the adoption/certification record (635 motions).** The MPO Board
  + TAC decision log: TIP modifications, RTP amendments + air-quality conformity, corridor-
  preservation purchases, functional-classification submittals, funding awards. **This is where
  "what did the board adopt / certify / vote to approve" goes** — an adoption record, NOT a
  per-member vote analytic (see ceiling below).

## Which artifact for which question

- **Funding / what's programmed / project cost, mode, timing:** `projects/projects.csv` (fed
  `regional_project`, `city='mag_mpo'`). Filter `plan_kind` ∈ tip | rtp | rpo.
- **Growth assumptions / future population & jobs by city:** `projections/mag_mpo_projections.csv`
  (fed `projection`). Compare to Gardner **V2022**, not V2025.
- **Housing supply / density / future land use / TOD tracking:** the `gis/index.csv` catalog
  (Housing Unit Inventory, General Plan Land Use 2025, Station Area Planning HB462).
- **What the MPO decided / adopted + who moved/seconded:** `db/mag_mpo.db` (fed `motion` where
  `city='mag_mpo'`) — join `person` on mover/seconder; approve/deny mix via `disposition`
  (compose with `outcome`); failed/contested = `outcome='Fail'` (3 motions). **No `vote` rows.**
- **Thematic / keyword search** (TIP mods, RTP amendments, corridor preservation, conformity):
  `cities.db` `fts_minutes` filtered to `city='mag_mpo'`.
- **Who sits on the board / voting vs liaison:** `roster/seats.csv` (`entity_slug` joins repo
  members to their own rows).
- **NOT here:** per-member vote positions (ceiling); Summit/Wasatch bodies (see scope caveat).

## The MPO-is-Utah-County-only scope caveat (read before any cross-tier work)

MAG is governed by an **Executive Council** (the AOG's top board across all three counties;
noted, not built). Under it, the **MPO Board** is the Utah-County transportation policy body
(the "Regional Planning Committee" through ~2019, renamed **MPO Board** in 2020 — one body,
two names), advised by the staff-level **MPO Technical Advisory Committee (TAC)**. Board seats
are **ex-officio**: Utah-County city mayors + 3 Utah County commissioners + 2 state legislators
+ standing agency members (UDOT, UTA, Utah Division of Air Quality) vote; FHWA/FTA/Camp
Williams/TAC-Chair/Bluffdale sit as non-voting liaisons. Meets **monthly, ~2nd Thursday**.

> **SCOPE CAVEAT.** These records are the **Provo–Orem UZA MPO = Utah County only**. Repo
> members that DO sit here: `provo`, `orem`, `lehi`, `vineyard`, `utah_county`, plus county-
> straddling `draper` (voting) and `bluffdale` (non-voting liaison). **NEVER imply
> `summit_county` or `park_city` sit on the MPO Board** — they belong to MAG's separate
> **AOG / Wasatch Back RPO** side, not built here. The federated `caveat` table carries a row
> stating this. Most member cities (Alpine, American Fork, Eagle Mountain, Saratoga Springs,
> Springville, Payson, Lindon, Highland, Pleasant Grove, Spanish Fork, …) are **not repo
> entities** — their `entity_slug` is blank, never invented.

## The vote-recording ceiling — a SOURCE PROPERTY, not a gap (verified 2014-2026)

The MPO Board and TAC are **high-consensus, tally-only bodies**. Minutes name the **MOVER** and
**SECONDER** and record a **tally-only result** ("the motion passed all in favor") — **NO roll
call, NO per-member vote, usually not even a numeric count**, even on divided votes. Attendance
is a named ✓-table, but presence is not a vote. So:

- **The db `vote` table is HONESTLY EMPTY** and **`role` is empty** — an attribution ceiling
  exactly like alta / nephi voice votes / west_jordan PC. `names_recorded=0` on every motion.
  **Do NOT run per-member vote analytics on MAG.** Do not infer individual member positions.
- Motions carry **full-name mover/seconder person links** (`mover_person_id`/`seconder_person_id`,
  633/635 each), a **verbatim `result_raw`**, a derived **`outcome`** (**632 Pass / 3 Fail**),
  and a keyword **`disposition`** (approve/procedural/continue/deny; NULL = honestly
  unclassified, 58). **Contested signal**: `outcome='Fail'` (3 motions) is the only dissent the
  record exposes.
- Older-era (2014–2019) prose often names movers by **surname only** ("Mayor Acerson moved"),
  lifted to full names against that meeting's named attendance roster only when unambiguous
  (surnames collide — never guessed across meetings).

## Modules

```
projects/      TIP/RTP/RPO project pipeline. projects.csv = 571 rows (tip 225 / rtp 262 /
               rpo 84), shared 15-col schema. raw/ = 9 ArcGIS JSON snapshots. SOURCES.md auth.
projections/   MAG 2023 RTP city-grain forecast. mag_mpo_projections.csv = 328 rows (41
               geographies × 2020/2030/2040/2050 × population/jobs). raw/ = 2 by-city
               snapshots. SOURCES.md authoritative (Gardner V2022 control-total finding).
gis/           CATALOG of 20 MAG-region growth/development ArcGIS layers (link, don't mirror).
               index.csv + SOURCES.md (Housing Unit Inventory, GP Land Use 2025, HB462, TAZ).
legislative/   MPO Board (101 minutes) + MPO TAC (50) = 151, 2014-01 → 2026-06. minutes/<year>/
               <date>_<bodyslug>.md (born-digital PDF -> flowed text + provenance front-matter,
               provenance=magutah_site). minutes_index.csv. raw_pdf/ retained (~30M).
roster/        seats.csv — MPO Board seat/office table (2025-11-13 composition, 38 rows) +
               CLAUDE.md. Ex-officio seat table, NOT a rolling council_terms layer.
plans/         the PUBLISHED-REPORT corpus (2026-07-20) — 16 MAG documents as a searchable
               text layer: TransPlan50 RTP 2023-2050 narrative + amendment process + AQ
               conformity determinations (2023 + Amend 1/2), TIP AQ conformity + Annual
               Obligated-Projects lists, CEDS 2024-2029, Wasatch Choice vision, transportation
               policy/procedures, UPWP FY2025, Wasatch County Transit Study (the RPO doc), and
               the TransPlan40/2040-MTP archives. This is the DATA-FORWARD build's published-
               report layer — the ADOPTION record (who moved/adopted what) stays in legislative/
               + db/; plans/ federates ONLY into the search layer (text_path is the searchable
               artifact). index.csv (doc_class,title,adopted_date,jurisdiction,path,text_path,
               format,source_url,retrieved_date,notes) + text/ + raw/ (all 16 retained) +
               SOURCES.md. Scope = Utah County MPO (+ 1 Wasatch Back RPO study); no single-city
               jurisdiction tags. plans/CLAUDE.md authoritative.
db/            fetch_minutes.py (site -> markdown + index), build_db.py (-> mag_mpo.db,
               STANDARD 8-table schema), SCHEMA.md. DERIVED — rerun, never hand-edit.
```

## The database (`db/mag_mpo.db`) — standard 8-table schema

Body / person / meeting / application / motion / vote / role / referral — the same tables
every per-city db carries (+ the `provenance` and `disposition` motion columns), so
`scripts/build_cities_db.py` federates it unchanged. Totals: **2 bodies** (MPO Board
`kind=council`, MPO TAC `kind=commission`), **151 meetings** (2014-01 → 2026-06), **635 motions**
(Board 418 / TAC 217), **169 persons**. `vote`, `role`, `application`, `referral` are **empty by
design** — no named votes (ceiling), no structured matter keys (the TIP/RTP project pipeline is
the `projects/` module), `referral` present-but-empty so the federator's loader does not
hard-fail. Gates all pass: `foreign_key_check` empty, `integrity_check` ok, rebuild idempotent,
zero orphan mover/meeting/body refs.

## Provenance & honest gaps

- **Primary source = `magutah_site`** (magutah.gov static file tree, born-digital PDFs, clean
  text, no OCR). Enumerated via the site's listing endpoint `/sitefiles/minutes-list/?dir=…`
  (the landing page is JS-rendered — see recon.md).
- **Recovery fallback = Utah Public Notice** (PMN body 8083 current / 1480 older) — documented,
  not harvested (the site is complete to 2014). A future PMN-recovered minute would carry
  `provenance='pmn_minutes'`/`'pmn_roa'`.
- **Archive floors:** MPO Board **2014** (continuous to 2026-06; no pre-2017 format break),
  MPO **TAC 2020** (no TAC minutes exist on the site before 2020 — an honest floor). Not every
  monthly meeting has posted minutes (cancellations + a few unposted dates); `minutes_index.csv`
  lists exactly what exists. Three site files were dropped with reason: 1 foreign-body doc (a
  Utah County Commission minutes mis-filed in the MPO folder) + 2 exact-duplicate texts.
- **Refresh seam:** re-pull the ArcGIS layers per each SOURCES.md; append a new RTP vintage as
  a new `plan_vintage`/`vintage`, never merged into the current one.

## Rebuild

```
python3 mag_mpo/db/fetch_minutes.py   # site -> legislative/minutes + raw_pdf + index
python3 mag_mpo/db/build_db.py        # index/minutes -> db/mag_mpo.db (idempotent)
# projects/ + projections/ refresh by re-querying the ArcGIS services (see each SOURCES.md)
python3 scripts/build_cities_db.py    # federation — run by the integrator, NOT here
```

## Follow-ons (queue in root TODO.md)

TAC pre-2020 has no posted minutes (honest floor); ~15 surname-only movers 2014-19 remain
honest partials; a rolling Chair/Vice-Chair succession layer; an Executive Council + Wasatch
Back RPO build (the AOG/Summit/Wasatch side, out of scope here); PMN cross-check of unposted
meeting dates.
