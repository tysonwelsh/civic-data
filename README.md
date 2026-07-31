# civic-data — Utah government records, from city councils to the State

A structured, quantifiable archive of Utah government records built for **housing,
growth, and development research** — so a question answered in one place can be asked
across every level of government, with honest coverage caveats respected. It spans
**42 registered entities in a 4-tier model**:

- **31 cities and towns** — council + planning-commission minutes, extracted roll-call
  votes, public comments, municipal election results, campaign finance, rolling council
  rosters, and address→district geography.
- **8 counties** — `salt_lake_county` (the reference implementation) plus a 2026-07-20
  value/effort-gated wave: `utah_county` (full), `weber_county` / `cache_county` /
  `summit_county` (mid — several with richer *named* roll calls than SLCo), the db-less
  `washington_county` (light) and `juab_county` (elections + projections), and
  `wasatch_county` (registered only, no build yet).
- **2 metropolitan planning organizations (MPOs)** — `wfrc_mpo` (Wasatch Front Regional
  Council) and `mag_mpo` (Mountainland Association of Governments): the regional bodies
  that program transportation dollars and publish long-range growth projections.
- **the State of Utah** (`ut_state`) — a land-use/housing legislation subset with named
  legislator roll calls, the Property Rights Ombudsman's advisory opinions, and the
  LUDMA statutes themselves.

Every entity is a flat unit in one **entity model** (normative spec:
[`SCHEMA_SPEC.md`](SCHEMA_SPEC.md)) with a `level` of city / county / regional / state,
federated into one database with a `gov_level` column. Geography — which city sits in
which county, which entities an MPO covers — lives in a relationship graph
(`registry/`), not the folder tree. The generated map is
[`registry/HIERARCHY.md`](registry/HIERARCHY.md).

**The non-city tiers are incorporated on their own terms.** An MPO is programmed
projects and projections, not roll calls; a db-less county is elections and searchable
text, with its vote layer honestly deferred. What each entity does and does not contain
is documented in its own `CLAUDE.md` — read it before analyzing that entity.

## gov.db — the federated database

**`gov.db`** (repo root) unions every built entity's standard tables with `city` +
`gov_level` columns, plus the cross-entity normalization, search, and roster layers. It
was **renamed from `cities.db` on 2026-07-20** as the repo outgrew cities; a `cities.db`
symlink remains for back-compat, and the builder is still
`python3 scripts/build_cities_db.py`. Read [`cities_db_SCHEMA.md`](cities_db_SCHEMA.md)
first.

Headline federated totals (measured, not estimated):

| Layer | city | county | regional | state | notes |
|---|---:|---:|---:|---:|---|
| **motions** | 49,172 | 24,346 | 958 | 1,208 | `motion` table |
| **member-votes** | 181,119 | 35,318 | 0 | 27,887 | `vote`; regional minutes are tally-only, so MPOs record no member-votes |
| **elections** | | | | | `election_race` 680 (authoritative winners/margins) + `election_result` 5,482 (SLCo SOVC tallies) |
| **regional projects** | | | 5,717 | | `regional_project` — WFRC + MAG programmed TIP/RTP projects |
| **projections** | 980 | | 9,832 | 140 | `projection` — county / annual city-area regional / state grains |
| **searchable minutes** | | | | | `fts_minutes` — 13,886 documents across 40 entities |

The State layer adds a **264-bill land-use/housing subset (2015–2026)** with 1,208 named
roll calls and 27,887 legislator votes (**a disjoint person population** — never
surname-joined to municipal officials), plus **309 Property Rights Ombudsman advisory
opinions** (307 with recovered text) and **218 LUDMA statute sections** as file corpora
under `ut_state/`.

The database is **DERIVED** — regenerated from the per-entity sources, never
hand-edited. Sandy's `legistar_*` extension tables are deliberately excluded (query them
in `sandy_city_council/db/sandy.db`).

## The 31 cities

| directory | city | county | minutes portal | council meets |
|---|---|---|---|---|
| `slc_city_council/` | Salt Lake City | Salt Lake | PrimeGov (2021+), Laserfiche (2020) | Tue |
| `lehi_city_council/` | Lehi | Utah | Granicus | Tue |
| `logan_city_council/` | Logan | Cache | Revize | Tue |
| `nephi_city_council/` | Nephi | Juab | CivicPlus | Tue |
| `ogden_city_council/` | Ogden | Weber | CivicPlus | Tue |
| `orem_city_council/` | Orem | Utah | CivicClerk / gdrive | Tue |
| `park_city_city_council/` | Park City | Summit | CivicClerk | **Thu** |
| `provo_city_council/` | Provo | Utah | Hyland OnBase | Tue |
| `sandy_city_council/` | Sandy | Salt Lake | **Legistar (API)** | Tue |
| `st_george_city_council/` | St. George | Washington | Revize (+PMN) | **Thu** |
| `vineyard_city_council/` | Vineyard | Utah | CivicClerk | **Wed** |
| `west_jordan_city_council/` | West Jordan | Salt Lake | PrimeGov | Tue |
| `west_valley_city_council/` | West Valley City | Salt Lake | Hyland OnBase | Tue |
| `south_jordan_city_council/` | South Jordan | Salt Lake | CivicPlus | Tue |
| `millcreek_city_council/` | Millcreek | Salt Lake | CivicPlus AgendaCenter | **Mon** |
| `taylorsville_city_council/` | Taylorsville | Salt Lake | CivicEngage Central | **Wed** |
| `murray_city_council/` | Murray | Salt Lake | CivicPlus Archive | Tue |
| `herriman_city_council/` | Herriman | Salt Lake | PrimeGov | **Wed** |
| `draper_city_council/` | Draper | Salt Lake (+Utah) | Granicus | Tue |
| `riverton_city_council/` | Riverton | Salt Lake | PMN (+Granicus) | Tue |
| `alta_city_council/` | Alta (Town) | Salt Lake | PMN | **Wed** |
| `midvale_city_council/` | Midvale | Salt Lake | Revize | Tue |
| `cottonwood_heights_city_council/` | Cottonwood Heights | Salt Lake | CivicEngage + PMN | Tue |
| `holladay_city_council/` | Holladay | Salt Lake | PMN | **Thu** |
| `south_salt_lake_city_council/` | South Salt Lake | Salt Lake | PMN | **Wed** |
| `bluffdale_city_council/` | Bluffdale | Salt Lake (+Utah) | CivicPlus AgendaCenter | **Wed** |
| `white_city_city_council/` | White City | Salt Lake | Streamline + PMN | **Thu** |
| `kearns_city_council/` | Kearns | Salt Lake | PMN | **Mon** |
| `magna_city_council/` | Magna | Salt Lake | CivicPlus + PMN | Tue |
| `copperton_city_council/` | Copperton (Town) | Salt Lake | GoDaddy + PMN | **Wed** |
| `emigration_canyon_city_council/` | Emigration Canyon | Salt Lake | PMN | Tue (varies) |

City data floor is **2020** (SLC votes 2021+; elections 2019+), with documented
exceptions carrying their FULL history: **millcreek 2016** (incorporated 2016-12) and
the **five township-origin entities 2017** (white_city, kearns, magna, copperton,
emigration_canyon — metro townships incorporated 2017 → cities/town in 2024 under HB35;
several have genuine 2017–mid-2018 gaps where Utah Public Notice purged the file blobs).
Salt Lake City is the original template; the other thirty cities were built by the
`build-city-data-repo` skill, the counties by `build-county-data-repo`.

## The counties, MPOs & state

Each non-city entity lives in its own top-level directory and is documented by its own
`CLAUDE.md`. A one-line orientation:

- **`salt_lake_county/`** — the first county and reference build: County Council (9) +
  elected Mayor, agencies, PC votes/minutes, adopted ordinances, a development pipeline,
  the canonical SOVC election canvass, plans, projections, and a GIS catalog.
- **`utah_county/`** — Board of Commissioners (3), full tier; named roll calls exist
  2015–16 then an OCR tally-only era 2017+ (the inverse of most cities).
- **`weber_county/`** — Commissioners (3); named-primary minutes (99.6% named rolls
  2015+, depth to 2000) — richer than SLCo.
- **`cache_county/`** — County Council (7) + non-voting Executive; full named rolls
  2021+ born-digital (2015–20 scanned tally-only).
- **`summit_county/`** — County Council (6) + Manager; two planning commissions
  (Snyderville Basin + Eastern) and a 571-application development pipeline.
- **`washington_county/`** — Commissioners (3), db-less: canonical elections 2018–2025 +
  searchable minutes + plans/ordinances/GIS; vote layer and dev pipeline explicitly
  deferred.
- **`juab_county/`** — Commissioners (3), db-less and thin: canonical elections 2023–2026
  + projections + a GIS catalog.
- **`wasatch_county/`** — registered only; carries Park City's second county edge, no
  build yet.
- **`wfrc_mpo/`** — Wasatch Front Regional Council; programmed projects (8 TIP vintages +
  RTP-2050) + annual city-area projections 2019–2050 + Wasatch Choice GIS. Council
  minutes are tally-only (dissent recorded as a count, no member-votes).
- **`mag_mpo/`** — Mountainland Association of Governments (Utah/Summit/Wasatch), the
  Provo–Orem MPO; TIP/RTP/RPO projects + city-grain projections + Housing Unit Inventory
  GIS. The MPO Board is Utah-County-only; Summit/Park City sit on the AOG/RPO side.
- **`ut_state/`** — the Legislature's land-use/housing bill subset with named legislator
  roll calls, the Property Rights Ombudsman's advisory opinions, and the LUDMA statutes
  (recodified in 2025: 10-9a→10-20, 17-27a→17-79).

## Standard per-city layout

```
<city>_city_council/
  meeting_minutes/       council minutes (markdown, one file per meeting) +
                         minutes_index.csv + all_votes.csv (roll-call votes) + roster
  planning_commission/   the appointed technical land-use body — same schemas,
                         body=PlanningCommission (recommendations vs final actions)
  public_comments/       all_comments_clean.csv (may be honestly EMPTY) + AVAILABILITY.md
  election_results/      <city>_races.csv + by-candidate + by-precinct
  db/                    relational SQLite (civic.db) + SCHEMA.md — the queryable form
  geo/                   address_to_district.py — any address → council district
  roster/                rolling council-roster: council_terms.csv (seat-tenure intervals)
                         + district_versions/district_precincts + CLAUDE.md
  weeks/                 DERIVED weekly bundles (summary.md + votes + comments; minutes linked)
  README.md / CLAUDE.md / recon.md / VERIFICATION.md / build_weeks.py
```

## What each dataset contains

- **`meeting_minutes/all_votes.csv`** — long format, one row per member-vote, 13
  standard columns (`date,year,title,body,motion_no,motion,motion_type,result,mover,
  seconder,member,vote,source`). `result` and `motion_type` are **city-faithful
  verbatim/native values** — the cross-city normalized layer lives alongside
  (see SCHEMA_SPEC.md §8). Tally-only motions (names not printed) appear with blank
  `member`/`vote` — nothing is ever guessed.
- **`planning_commission/`** — PC minutes + votes in the same schemas. The
  recommendation-vs-final-action distinction (PC recommends to Council vs PC decides
  CUP/site-plan itself) is encoded in the `result` strings; SLC additionally has an
  `action_class` column.
- **`public_comments/all_comments_clean.csv`** — cleaned public-submitted comments
  where the city publishes them (see caveats — most don't).
- **`election_results/`** — county canvass results filtered to that city's council +
  mayor races (`races` / `by_candidate` / `by_precinct`), verified against retained
  canvass sources.
- **`db/civic.db`** — normalized SQLite joining all bodies' votes by real keys, plus a
  **reconstructed, confidence-scored** PC→Council referral layer (`v_referral_chain`).
  Read the city's `db/SCHEMA.md` first; `high` links ≈ exact, `low` = flagged, don't quote.

## Join keys

- **By week**: everything buckets to the council week ending on the city's meeting
  weekday (Tue for most; several bodies meet Thu/Wed/Mon) — the `weeks/` bundles are that
  join, materialized.
- **By motion**: `(source, motion_no)` identifies a motion within an entity; joins
  `all_votes.csv` ↔ `motions_std.csv` (normalization layer) ↔ db `motion` provenance.
- **By person**: election winners ↔ vote records join on **person + year + district**
  (normalize names first — election names are upper-case, some with `(NP)` suffixes).
  State legislators are a separate person population — do not surname-join them to
  municipal officials.
- **By geography**: `geo/address_to_district.py` ties an address to a district, hence
  to its member, votes, and election margin.
- **Cross-body (within an entity)**: the db's `referral` layer — reconstructed and
  scored, never a looked-up key.

## Coverage caveats — read before comparing entities

These asymmetries are properties of what governments *record and publish*, not of
behavior. Comparisons that ignore them will mislead. **Honest gaps are data** — they are
reported, never filled.

- **Public comments are substantive in only 2 of 31 cities**: SLC (13,334, 2020–2026,
  one of the few Utah cities publishing written comments) and Park City (459). Five have
  small slivers (St George 136, Orem 95, Provo 81, Lehi 42, West Jordan 28). **The other
  24 are honest zeros or pending harvests** documented in each city's
  `public_comments/AVAILABILITY.md`. Do not compare "public engagement" across cities on
  this data.
- **Vote-attribution ceilings differ everywhere.** Nephi is ~80% tally-only; Orem
  records Aye/Nay only (no absences/abstentions); West Jordan's PC names only dissenters;
  Utah County names rolls only 2015–16; the MPOs and several db-less counties record no
  member-votes at all. An absent Recuse/Abstain/Absent is a recording limit, not member
  behavior. See SCHEMA_SPEC.md §4 for the measured per-city table.
- **`result` and `motion_type` have no cross-entity vocabulary** (8–33 distinct result
  strings per city; each entity's motion_type labels differ). Never aggregate the raw
  strings across entities — use the normalization layer (`motions_std.csv` +
  `crosswalks/`, SCHEMA_SPEC.md §8).
- **Elections: 2019–2025 for most cities; SLC 2007–2025**; county canvasses run their own
  spans (washington 2018–2025, juab 2023–2026). Longitudinal analysis deeper than 2019 is
  SLC-only.
- **Recovered vs audited rows** carry a `provenance` column so recovered minutes (Utah
  Public Notice, Wayback, CivicPlus archives, draft-carves) are always filterable apart
  from audited primary sources.
- Smaller seams (SLC votes 2021+, St George 2020–21 PMN backfill, Provo PC 2025+, the
  township 2017–mid-2018 purge gaps, county born-digital seams) are logged per entity in
  its `CLAUDE.md` and `minutes_unrecovered.csv`.

## Expansion datasets

The `expand-city-sources` skill added seven additive source types, piloted in
**`lehi_city_council/`** and rolled out to the original 16 cities: `packets/` (agenda
packets + staff reports), `housing_plans/` (moderate-income housing + general plan),
`ordinances/` (zoning/land-use ordinance index), `pmn_backfill/` (Utah Public Notice
cross-check + recovered meetings), `transcripts/` (meeting-video transcripts),
`campaign_finance/` (candidate disclosures joined to election results — a structured
dollar layer in 15 cities), and a primary-document text layer. Each is self-contained
with its own `CLAUDE.md`, `AVAILABILITY.md`, `index.csv`, retained `raw/`, and honest
`unrecovered.csv`. The 2026-07 city wave and the counties are queued for expansion (see
`TODO.md`).

## Repo-level tooling & records

- **[`SCHEMA_SPEC.md`](SCHEMA_SPEC.md)** — the normative standard (schemas,
  vocabularies, normalization contract).
- **[`CLAUDE.md`](CLAUDE.md)** — analysis guidance: which artifact answers which
  question, cardinal rules, per-entity quirks.
- **`registry/entities.csv`** + **`registry/relationships.csv`** — the entity list and
  geography graph every repo-wide script reads (via `scripts/entities.py`;
  `scripts/cities.py` is a `level=='city'` back-compat shim). Regenerate the map with
  `python3 scripts/build_hierarchy.py` → `registry/HIERARCHY.md`.
- **`scripts/validate_entity.py <slug|dir>`** — entity-aware conformance checker
  (delegates cities to `scripts/validate_city.py`; validation, never mutation).
- **`scripts/build_coverage.py`** → **`coverage.json`** — measured per-entity × dataset
  manifest (records, date ranges, method, caveats).
- **`scripts/build_cities_db.py`** → **`gov.db`** — rebuilds the federated database.
- **`TODO.md`** / **`LEADS.md`** / **`HANDOFF.md`** — the work queue ([DEBT] + [GATED]
  only), the options/leads menu + watches, and the current-session handoff banner; standing
  rules in `GOTCHAS.md`, publish criteria in `SHIP_GATE.md`, closed records in
  `TODO_ARCHIVE.md`.
- **`_audits/`** — repo-wide extraction & consistency audits; **`_backups/`** —
  pre-modification originals of every file touched during remediation.

## License & citation

**Code** (scripts, extractors, builders): [MIT](LICENSE). **Derived data layers**
(schemas, normalized/extracted records, crosswalks, referral chains, rosters):
[CC-BY-4.0](DATA-LICENSE.md) — the underlying Utah public records are not subject to this
project's copyright, and third-party plans/GIS layers retain their own terms (see
DATA-LICENSE.md). Cite via [`CITATION.cff`](CITATION.cff). How each layer was built and
audited: [`METHODS.md`](METHODS.md). Personal-information policy (what is redacted and
what ships verbatim, with a correction/takedown contact): [`PRIVACY.md`](PRIVACY.md).
