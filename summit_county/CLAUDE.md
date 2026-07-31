# summit_county — how to answer questions with this entity

**Summit County, Utah** (FIPS **49043**; seat **Coalville**) — a `gov_level='county'` entity
(**fed_index 105**) federated into the repo-root `gov.db`/`cities.db`. Built 2026-07-20 as the
**MID-tier county** on the `build-county-data-repo` model (reference impl: `salt_lake_county/`).
Counties are modeled as **modules**, not big cities — only the datasets that fit. This file is
authoritative for the whole entity; each module's own `CLAUDE.md` is authoritative for that
module — read it before analyzing that module.

**Governance — Council–Manager form.** A **6-member elected County Council** (the legislative
body; at-large, staggered 4-year terms) + an **appointed County Manager** (executive). The
Council meets **Wednesdays, weekly** (Coalville). Current members (2023–2026 window; the
extracted roster): Roger Armstrong, Christopher (Chris) Robinson, Canice Harte, Tonja B Hanson,
Malena Stevens, Megan McKenna (Stephanie Poll appears in an earlier seam). The Council also
convenes **in-session** as the Board of Equalization, the SBSRD/rec-district board, etc. — those
convening motions stay `body='County Council'` (verbatim in the motion text). Land use is
**unincorporated-area** and runs through **two Planning Commissions** (below).

**Contains one repo city, `park_city` (separately owned — DO NOT touch from here).** The county
canvass does carry Park City's contests at precinct grain; see elections routing below.

## Cardinal rules (repo-wide — apply identically here)

1. **Never fabricate.** Blank `member`/`vote` on a motion = the source printed a tally only
   (a recording ceiling, not a gap). Meetings whose minutes don't exist are logged, never
   invented. Honest gaps are data.
2. **City/source-faithful values are never overwritten.** `result_raw` (the verbatim tally)
   and native strings stay verbatim; normalized/derived fields live alongside.
3. **Derived layers are regenerated, never hand-edited** — `db/summit_county.db`, the staging
   dirs, `all_votes.csv`/`motions_tally.csv`, `development/applications.csv`. Canonical truth =
   the flat CSVs + minutes markdown + raw PDFs.

## The recording ceilings (read before quoting any vote)

- **County Council — tally-primary, NO-API ceiling (final, cannot be lifted).** Summit runs on
  **Granicus MinutesViewer** (born-digital HTML), **NOT Legistar** — there is no structured
  vote API. Every Council motion names the **mover + seconder** and prints a **tally**
  (`"all voted in favor, (5-0)"`), but names individual members **only when a division is
  called**. So unanimous motions are `names_recorded=0`, blank member/vote (the majority); named
  `vote` rows exist only for the **23 divided Council motions** (of 1,831). Contrast `salt_lake_county`,
  whose Legistar API is richer than its tally-only minutes — Summit has no such recovery path.
- **Planning Commissions — mover/seconder + divided-named ceiling.** Both PCs name the
  mover + seconder on every motion; **unanimous motions are tally-only**; **divided motions name
  voters** (modern Granicus era = full roll; older AgendaCenter era = dissenters/abstainers
  only; abstentions named in both eras). `motions_tally.csv`'s `(N-M)` tally is the
  authoritative count; the **496** named rows are attribution (on a few large rolls tally >
  named — honest). **⚠ Revised 2026-07-25:** much of what this bullet previously called a
  ceiling was an extractor gap. `build_votes.py` **v4** now pairs motion verbs and printed
  outcomes in document order rather than hunting outward from the verb: **motions 1,526 →
  1,571, named rows 409 → 496**, every printed tally line now has exactly one motion
  carrying it in **99% of meetings (was 89%; the AgendaCenter era went 82% → 99%)**, and
  motions no longer inherit a neighbour's outcome. The Granicus HTML's unrendered
  `<!-- AYES: -->` block is **deliberately not ingested** (owner ruling; unpublished, and
  adds no dissent). Full record: `land_use/VERIFICATION.md`. PC commissioner names are recorded **as printed** (often surname-only) — they are a
  **separate roster** and are **NOT merged** into the like-surnamed Council members (a PC
  "Harte"/"Stevens"/"Hanson" ≠ Council Canice Harte / Malena Stevens / Tonja Hanson; the db keeps
  them as distinct `person` rows — cardinal rule, don't fabricate cross-body identity).
- **The 2024-05-15 portal-migration seam.** The county froze its CivicPlus **AgendaCenter** for
  new postings on 2024-05-15 and moved to a new "Meetings and Minutes" page (the **Granicus**
  front-end). Pre-2023 Council minutes on AgendaCenter are **image-only scanned PDFs** (a
  different, OCR-gated era); Granicus HTML is clean. This seam also splits the PC minutes source.

## Module map + which-artifact routing

| module | what it is | routing |
|---|---|---|
| `legislative/` | County Council minutes (Granicus, 2023-01→present), 198 mtgs, 1,831 motions | meeting context, Council votes |
| `land_use/` | the **two PCs** (Snyderville Basin PC + Eastern Summit County PC), 393 minutes, 1,571 motions, 496 named rows, 2015→2026 | PC votes/recommendations, minutes corpus |
| `development/` | the **development pipeline** — `applications.csv`, 576 land-use application rows | one row per PC application item; growth/housing research |
| `ordinances/` | adopted-ordinance catalog, `index.csv` (11 rows incl. **both development codes**) | what an ordinance did; enacting-motion link |
| `elections/` | the **canonical county canvass, 2006–2026** | authoritative winners/margins/precinct grain |
| `plans/` | General Plans (Basin 2015, Eastern 2023) + the MIH plans; searchable text | growth vision, HB462 MIH obligations |
| `projections/` | Gardner Institute pop/household/jobs, **Vintage 2025 + Vintage 2022** | growth-demand context (filter to ONE vintage) |
| `gis/` | 15-layer **catalog** (link, never mirror) of parcel/zoning/address REST endpoints | live geospatial layers |
| `packets/` | 122 agenda-packet / staff-report docs + 118 text sidecars (SCHEMA_SPEC §9 `doc_class`) | primary-document text |
| `agencies/` | **deferral ledger only** (README.md) — RDA + Housing Authority | see honest gaps |

- **Aggregates / time series** (votes by member/type/year, PC recommendation rates): the flat
  CSVs — `legislative/all_votes.csv`, `land_use/all_votes.csv` + `land_use/motions_tally.csv`
  (the tally is authoritative; named rows are the contested signal).
- **Cross-body / project questions, or a motion's full context**: `db/summit_county.db`
  (standard 8-table schema). Bodies: `County Council` (council), `Snyderville Basin Planning
  Commission` + `Eastern Summit County Planning Commission` (planning). Council motion_ids
  **1–1820** are stable; PC motion_ids **1821–3346** append above them.
- **Approve/deny vs carried**: PC `motion.outcome` = did the motion CARRY (`Pass` 1369 / `Fail`
  24 / blank 133 = no result printed); the application-level disposition
  (`applications.csv.pc_recommendation` = approve/deny/continue) is ORTHOGONAL — compose at
  query time. (County-motion disposition is not yet computed; NULL like SLCo.)
- **Development pipeline** (did the PC approve project X; one matter's action): `development/
  applications.csv` → federated `development_application`; `motion_id` joins to the PC motion +
  its named roll where the link is unique (70 of 224 outcome rows — see below).
- **Ordinances** (what Ordinance X did; who enacted it): `ordinances/index.csv` — `motion_id`
  links to the enacting Council motion + roll call where uniquely resolvable
  (`match_confidence='high'`; 4 of 11 — the 2023+ discrete ordinances).
- **Elections** (winners, margins, precinct grain): `elections/election_results_by_contest.csv`
  (certified layer → `election_result`) + `elections/summit_results_long.csv` (109,201
  precinct-grain rows). **Canonical for Summit 2006–2026.** No RCV in any Summit contest. Read
  `elections/VERIFICATION.md` before quoting anything unusual.
- **Thematic / keyword** (ADUs, density, MIH): the FTS layer in `cities.db` (`fts_minutes`
  covers Summit Council + both PCs; `fts_ordinance`, `fts_packet`).

## Development-pipeline & ordinance linkage (closing-pass, 2026-07-20)

- **Applications → PC motions.** `db/link_applications.py` loads all **571** `applications.csv`
  rows into the db `application` table and resolves each outcome-bearing row to its unique
  enacting PC motion, restricted to the same (body, date) and scored on shared
  parcel/project/location token + a distinctive **project-NAME** phrase. **70 of 224** rows
  (31%) link uniquely (`app_confidence` high|medium; `app_match_method`
  project_name/parcel/location/…); the rest stay blank because Summit PC minutes identify the
  item by parcel # but the motion by project name, and multiple items per meeting make most
  links ambiguous — **never forced**.
- **Ordinances → Council motions.** `db/link_ordinances.py` fills `ordinances/index.csv`
  `motion_id`/`match_confidence` only where exactly one Council motion cites the ordinance
  number in an ordinance context ("adopt Ordinance No. 962 …"). **4 of 11** link (**962, 968,
  980, 1003** — every discrete ordinance adopted within the 2023+ Granicus Council era);
  839/912/936/950/951 pre-date the Council coverage floor, and the two continuously-amended
  **development codes** (Title 10 Basin, Title 11 Eastern) have no single enacting motion —
  all correctly blank.

## Honest gaps (never fabricate to fill these)

- **Pre-2023 Council era (scanned).** `legislative/minutes_unrecovered.csv` (460 rows) logs
  **453 dates 2015-03-25→2022-12-30** as `status=scanned-image` (image-only AgendaCenter PDFs,
  OCR-gated — 2015 has a rough OCR layer) + **7 Granicus uploaded-PDF** special sessions. The
  built Council db is the **contiguous-weekly Granicus era only (2023-01→present)**; Jan–Mar
  2015 and earlier are unposted (availability floor). **PMN body 1330** is the born-digital
  OCR-upgrade channel (queued follow-on).
- **PC portal gaps.** **Snyderville 2021 (4 of ~20)** and **Eastern 2022 (5 of ~17)** are
  genuine AgendaCenter/Granicus seam gaps; **14 image-only PC minutes** are
  `minutes_exist_text_unrecovered` (meeting recorded, text unrecovered). **PMN body 1503**
  ("Summit County Community Development") is the recovery channel (its search backend errored at
  build — logged). The 14 unrecovered are excluded from the db meeting set (logged in
  `land_use/minutes_index.csv`).
- **Elections.** Honest gaps: 2004 (scan), 2006 primary (county mis-link serves the 2010 file),
  2019 primary (dead links), **2022 primary (all docs scanned, OCR queued)**, **2024 June
  regular primary (unpublished on every county channel)**, and the 2005–2017 odd-year municipal
  self-administration era (except 2011/2015). Suppressed low-turnout precinct cells (2024+) carry
  `votes=''`, `suppressed=True` — never imputed.
- **Agencies deferred.** `agencies/` is a **ledger only** — the **RDA** (PMN body 1277; a single
  Silver Creek project area, thin) and the **Housing Authority** (**formed 2025**, essentially no
  history yet) are documented in `agencies/README.md`, not built.
- **Projections** are county-grain only (no sub-county); `households` ≠ housing units.
- **GIS** is a catalog, not mirrored bulk geodata.

## Park City & elections cross-reference

Park City self-administers its municipal elections, but the county tabulates under contract and
the county canvass **contains PC contests at precinct grain (11 PC precincts), 2011–2025**.
Cross-checked against the audited `park_city_city_council/election_results/` layer: **49/50
candidate rows 2019–2025 match exactly** (the 50th is a `Withdrawn` 0-vote ballot line the city
layer omits). The per-city re-point to this canonical is queued separately and byte-identity
gated — **do NOT touch the park_city layer from here.**

## Plans / MIH note (growth-relevant)

Summit plans unincorporated land as **two districts, each with its own General Plan AND
Development Code** (Basin = Title 10, 20% inclusionary set-aside; Eastern = Title 11). The
**HB462 (2022) Moderate-Income-Housing trail**: Basin Ord 950 + Eastern Ord 951 (2022) →
amendments 962 (2023) → 968 (2023) → 980 (2024). Note the honest finding that **Utah DWS found
the 2023 MIH report NON-COMPLIANT** (`plans/mih_udws_noncompliance_notice_2023`). A
comprehensive Basin GP update is in progress, **not adopted** — the 2015 Basin GP still governs.
Projection note: Summit's outlook was **lowered between vintages** (Vintage 2022 ran 2020
population 42,394 → 59,603 by 2060; Vintage 2025 runs 43,374 → 56,650 by 2065) — filter to one
vintage before trending.

## Provenance conventions

- Every built motion carries `provenance='minutes'` (all audited-primary; Summit has no recovered
  channels yet). The tally is the authoritative count; named rows are attribution.
- Name canonicalization: the Council roster is unified via a surname map (Chris/Christopher
  Robinson; Tonja/Tonja B Hanson) shared by `legislative/extract_votes.py` + `db/build_db.py`;
  **PC names are exempt** from that map (separate roster, kept verbatim — see the ceiling).
- Elections/plans/projections/gis values are verbatim source layers; corrections go through
  documented overrides, never in-place edits.

## Build / regenerate order (all idempotent — never hand-edit outputs)

```
cd land_use     && python3 build_votes.py          # minutes md → all_votes.csv + motions_tally.csv
cd legislative  && python3 extract_votes.py        # Granicus HTML → db/staging/ (Council)
cd development  && python3 build_applications.py   # PC minutes → applications.csv   ⚠ see below
python3 db/build_staging_pc.py      # land_use CSVs → db/staging_pc/ (PC → staging shape)
python3 db/build_db.py              # db/staging/ (Council) + db/staging_pc/ (PC) → summit_county.db
python3 db/link_applications.py     # applications.csv → application table + motion.application_id + motion_id col
python3 db/link_ordinances.py       # ordinances/index.csv motion_id/match_confidence (unique only)
# elections: cd elections && python3 build_elections.py   (gates must PASS)
# then federate: python3 ../scripts/build_cities_db.py
```

⚠ **`build_applications.py` MUST be followed by `link_applications.py`.** The builder
rewrites `development/applications.csv` **without** the trailing `motion_id` column, which
`link_applications.py` appends. Running the builder alone silently drops every
application→motion link from the CSV (the db keeps them until the next `build_db.py`).
Both are individually idempotent; only the ORDER is load-bearing (noted 2026-07-25).

Council motion_ids (1–1820) are **stable** across rebuilds (staging read first, deterministic
sort); PC appends above. `db/build_db.py` reads `db/staging/` first, then the optional
`db/staging_pc/` last — the designed append path. FK/integrity gates print on every db build.

## Federated totals (in `summit_county.db`; verified 2026-07-25 after the PC vote-recovery pass)

body 3 · person 104 · meeting 577 · application 576 · motion **3402** (Council 1831 / PC 1571) · vote 605 (Council 109 / PC 496) · role 71 · named-roll motions 304 ·
motion.application_id linked 67. `foreign_key_check` OK, `integrity_check` ok, idempotent.
