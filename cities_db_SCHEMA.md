# cities.db — the federated cross-city database

`cities.db` (repo root, SQLite) unions the 16 per-city relational databases into one
queryable cross-city artifact, with the normalization layer (`motions_std.csv` × 32),
the `crosswalks/` tables, and a **caveat table** loaded alongside so cross-city
questions can be asked — and mis-comparisons can't happen silently.

> **DERIVED — never hand-edit.** Regenerate after ANY per-city db rebuild:
>
> ```
> python3 scripts/build_cities_db.py
> ```
>
> The build is stdlib-only, idempotent, deterministic; it reads whatever is on disk
> at run time and prints the full row-count reconciliation + join rates. The build
> timestamp is stored in the `build_info` table (`SELECT value FROM build_info WHERE
> key='built_at'`). This document's numbers are from the **2026-07-11T12:38:41-04:00**
> build (which federated the roster layer across all 16 cities and folded in the
> recovered-vote `provenance` integration — 661 PC/RDA/MBA motions);
> if in doubt, rebuild and trust the printed reconciliation over this snapshot.

## What's in it / what's not

**In:** the 8 standard tables from every city db (`body`, `person`, `meeting`,
`application`, `motion`, `vote`, `role`, `referral`) + `motion_std` (all 32
`motions_std.csv` files, joined to `motion`) + the three crosswalks + `caveat` +
`build_info` + 5 cross-city views + **the search layer** (since 2026-07-06,
REFACTOR_PLAN Phase 2, built by `scripts/build_search_layer.py` — invoked
automatically at the end of `build_cities_db.py`): `comment`, `cf_filing` /
`cf_contribution` / `cf_expenditure` / `cf_cycle` / `cf_candidate_person`,
`ordinance`, `document`, and four FTS5 full-text indexes (`fts_minutes`,
`fts_motion`, `fts_comment`, `fts_ordinance`). The full minutes text pushes the
file to ~330 MB — it is DERIVED and freely regenerable. Since 2026-07-11 it also
carries **the roster layer** (`term`, `district_version`, `district_precinct` +
views `v_council_current`, `v_term_provenance`), federated from all 16 cities'
`roster/` dirs — see the roster-layer section below.

**Not in (by design):**
- **sandy's `legistar_*` extension tables** (its full Legistar API harvest — 10
  bodies, 2,825 matters, 10,443 raw vote rows incl. `Nonvoting` and the Board of
  Adjustment). They are city-local extensions; query them in
  `sandy_city_council/db/sandy.db`.
- Election results — no db form yet; they live in each city's `election_results/`
  CSVs (schema drift across cities is a known hazard — REFACTOR_PLAN 5.3). The
  `caveat` table and `v_coverage` carry rows so coverage questions can't miss them.
- Per-city views (`v_referral_chain`, `v_project_timeline`, …) — use the per-city dbs
  for deep within-city work; cities.db has its own cross-city views.
- Transcript/housing-plan BODY text — the `document` table catalogs every artifact
  with `has_text`/`text_path`, but their text is not FTS-indexed yet. Packet staff
  reports ARE indexed since 2026-07-07: `fts_packet` covers the 3,446 stored
  born-digital packet sidecars (`scripts/extract_packet_text.py`; image-only and
  index-only packets are honestly excluded — see each city's
  `packets/text/_extraction_log.csv`).

## ID namespacing (how FKs stay valid)

Every per-city integer id — PK and FK alike — is shifted by a fixed per-city offset:

```
federated_id = source_id + fed_index * 10,000,000
```

`fed_index` is the per-entity federation index from `registry/entities.csv` (loaded by
`scripts/entities.py`; `scripts/cities.py` is now a `level=='city'` shim over it). It is
append-only and **never renumbered**, with non-overlapping bands reserved per level so a
new tier never shifts published offsets — **city 1–99** (16 used), **county 101–199**,
**regional 201–299**, **state 301–999**. Cities: lehi=1, logan=2, nephi=3, ogden=4,
orem=5, park_city=6, provo=7, sandy=8, slc=9, st_george=10, vineyard=11, west_jordan=12,
west_valley=13, south_jordan=14, millcreek=15, taylorsville=16 (unchanged since the
city-only era). Counties/regions/state get vote-spine rows only once built (a per-entity db
exists); until then they are identity-only rows in the `entity` table.

- The largest source id repo-wide is ~1.0e6 (sandy's matter_id-derived
  `application_id`s), so offsets can never collide.
- All within-city FK relationships carry over unchanged and are declared +
  `PRAGMA foreign_key_check` verified at build (0 violations).
- Recover the source id with `id % 10000000`; recover the city with
  `id / 10000000` (or just use the `city` column, present on every table).
- Referrals are within-city only (no cross-city referrals exist or are implied).

## Schema

Every unioned table = the standard per-city schema (SCHEMA_SPEC.md §5) **+ a leading
`city` column** (now the general **entity slug** — a city today, or a county/regional/state
slug once those are built) **+ `gov_level`** (`city`\|`county`\|`regional`\|`state`) **+
`state`** (`ut`). Every row today is `gov_level='city'`, `state='ut'`; the columns exist so
county/regional/state rows federate into the same spine and cross-tier queries are one join
(SCHEMA_SPEC §0). Two registry tables accompany the union: **`entity`** (all 26 entities —
16 city, 7 county, 2 regional, 1 state — mirror of `registry/entities.csv`) and
**`entity_relationship`** (the 42-edge geography graph: `within`/`member_of`, with
`confidence`). Uniqueness is re-scoped per city where the per-city db had
a global UNIQUE: `body(city,name)`, `person(city,name_key)`,
`meeting(city,body_id,source_file)`, `application(city,app_key)`;
`vote(motion_id,person_id)` and `referral(primary_application_id,
related_application_id)` stay as-is (ids are already city-namespaced).

| table | grain | notes |
|---|---|---|
| `body` | city × governing body | `kind` ∈ council/commission/agency |
| `person` | city × official | name-based identity **within one city only** — the same human in two cities would be two rows (none known) |
| `meeting` | one meeting | `meeting_date`, `title`, `source_file` provenance |
| `application` | one project/matter within one body | body-scoped, per SCHEMA_SPEC |
| `motion` | one motion | standard columns incl. `outcome` (Pass/Fail/Continued/Died), `stage`, `recommendation`, `app_match_method`/`app_confidence`, and **`provenance`**. Values: `minutes` = audited primary layer; `pmn_*` = recovered from Utah Public Notice (query recovered with `provenance LIKE 'pmn_%'`) — `pmn_roa` (Provo PC 2020-2024 Reports of Action) and `pmn_minutes` (recovered standalone minutes: West Jordan PC 2021-22, Vineyard RDA 2018-24, Orem RDA 2020-26, South Jordan council 2020, Ogden RDA/MBA 2020-24). Non-PMN recovery channels also carry distinct values (so audited-only is `provenance='minutes'`, NOT `LIKE 'pmn_%'`): `agendacenter_minutes`, `wayback_minutes`, `citysite_minutes`, and — Ogden PC 2020–2023 gap recovery (2026-07-19) — `doccenter_draft` (standalone CivicPlus DocumentCenter unofficial-draft minutes, 525 motions) / `packet_carve` (following-meeting agenda-packet carves, 34). Also surfaced on `v_contested_all`. |
| `vote` | one member-vote | `vote_value` CHECK ∈ Aye/Nay/Abstain/Recuse/Absent/Excused; **`note`** = park_city's extension (2 `'Mayor tie-break'` + 9 `'override: …'` rows; NULL for all other cities) |
| `role` | person × body observed span | |
| `referral` | reconstructed cross-body link (within city) | `confidence` ∈ high/medium/low — **low = flagged, do not quote** |
| `motion_std` | one motion (normalization layer) | `city`, `dataset` + the 16 SCHEMA_SPEC §8 contract columns + **`motion_id`** (the resolved join to `motion`). **Since 2026-07-29 it covers the CITY + COUNTY + REGIONAL tiers** (77,507 = city 49,172 + county 27,376 + regional 959). Two build paths: **city** rows are READ from the on-disk `motions_std.csv` files (`dataset` ∈ meeting_minutes \| planning_commission = the directory); **county + MPO** rows are **COMPUTED AT FEDERATION** from `motion`/`vote` (that tier publishes no `motions_std.csv`) with the SAME classifier, imported from `scripts/normalize_motions.py` — see `compute_motion_std_noncity()`. For that tier `dataset` ∈ legislative \| land_use is **body-derived, not a path** (`land_use` = the entity's planning commission(s); `legislative` = governing body + work sessions + agency boards), and `motion_id` is set **by construction** so its 100% join rate is definitional, not a quality signal. **`ut_state` contributes NO rows BY DESIGN** (owner ruling 2026-07-29) — the municipal `motion_type_std` vocabulary does not describe legislative bill-stage votes, and the state tier is to be reintegrated on its own terms (TODO "STATE TIER — reevaluate how `ut_state` is integrated, ON ITS OWN TERMS (owner ruling 2026-07-29)"); query its `motion`/`vote` rows directly meanwhile. Per-entity confidence mixes: `build_info` key `motion_std_computed:<slug>`; honest ceilings: `caveat` codes `motion-std-computed-tier` / `motion-std-classification-ceiling` / `motion-std-deferred`. |
| `motion_type_crosswalk` | 241 rows | from `crosswalks/motion_type_crosswalk.csv` |
| `body_crosswalk` | 29 rows | from `crosswalks/body_crosswalk.csv` (canonical body names; **known gap: no rows yet for logan/provo/vineyard** — REFACTOR_PLAN 4.6) |
| `vote_values` | 50 rows | from `crosswalks/vote_values.csv` (per-city recording ceilings) |
| `caveat` | city × dataset × code | the documented coverage/recording asymmetries (below) |
| `election_race` | city × race | **elections DB form (2026-07-11)** — every city's audited `election_results/<slug>_races.csv` (the uniform 25-col §9 superset) + entity key + containing `county`. **Authoritative winners/margins.** Closes REFACTOR_PLAN §5.3. View: `v_election_city` |
| `election_result` | county × contest × candidate | Salt Lake County Clerk SOVC candidate tallies (council/mayor, 7 held cities) from `salt_lake_county/elections/`. `rank_in_contest` = plurality order (RCV finals differ — use `election_race`) |
| `build_info` | key/value | `built_at`, per-table row counts, per-file join rates, `search:*` keys |

### Search layer (2026-07-06, `scripts/build_search_layer.py`)

| table | grain | notes |
|---|---|---|
| `comment` | one public comment | union of every `public_comments/all_comments_clean.csv`, verbatim columns (14,175 rows: slc 13,334, park_city 459, five slivers) |
| `cf_filing` | **one filing** | union of `campaign_finance/filing_totals.csv`. ⚠️ **NEVER sum dollar columns across filings** (interim+summary double-counts) — use `cf_cycle` |
| `cf_contribution` | one contribution | 12,841 rows; `amount` verbatim + `amount_num` REAL parsed alongside |
| `cf_expenditure` | one expenditure | 10,697 rows; same amount convention |
| `cf_cycle` | candidate × cycle | the deduped rollup (`cycle_totals.csv`) — the ONLY sanctioned per-candidate total |
| `cf_candidate_person` | city × candidate | → `person_id` by exact name-key match only (110/377 matched — candidates who never held a seat stay NULL, never forced) |
| `ordinance` | one adopted ordinance | 4,115 rows from the per-city `ordinances/index.csv` via a synonym map (pre-Phase-3 column drift); `matched_motion_*` linkage resolved to `motion_id` where unique (3,402 resolved, 293 ambiguous — never forced; `motion_resolution` records which) |
| `document` | one source artifact | 27,442 rows across minutes / packets / ordinances / housing plans / transcripts / pmn_backfill; `has_text`/`text_path` = what an LLM can read directly; `meeting_id` set where the artifact IS a db meeting's minutes (5,268/6,466 — the rest have no motions, hence no `meeting` row) |
| `fts_minutes` | FTS5 | full text of all 6,466 minutes markdown files; `city`/`dataset`/`date`/`path` stored for filtering |
| `fts_motion` | FTS5 | external-content index over `motion.motion_text` (join back via `rowid = motion_id`) |
| `fts_comment` | FTS5 | external-content index over `comment` subject/topic/text (`rowid = comment_id`) |
| `fts_ordinance` | FTS5 | ordinance titles + text sidecars (sidecar text deduped per source file) |
| `fts_packet` | FTS5 | 3,446 stored packet text sidecars (staff reports/agendas; `packet_kind` stored for filtering) |

### Roster layer (2026-07-11, `scripts/roster_lib.py` + `<city>/roster/*.csv`)

The **rolling council-roster** — who holds each council + mayor seat over time, as
dated intervals with per-row provenance/confidence — federated from every city that
HAS a `roster/` dir: **all 16 cities** as of 2026-07-11 (each built, then
independently audited — see `scripts/roster_HARDENING.md`). Each per-city roster is
generated by a thin `roster/build_roster.py` driver over the shared
`scripts/roster_lib.py`; the loader unions the CSVs verbatim (the `city` column is
already in each CSV). All-TEXT, **no FK** — roster `person_key` is a `first_last`
slug, not the offset-namespaced `person.name_key`, so there is no clean join key
(match on `person_name` / `election_year` when tying to `vote`).

| table | grain | notes |
|---|---|---|
| `term` | one seat-tenure | 370 rows across 16 cities (slc 52 is the largest; taylorsville 35; range 16–52). Confidence mix **255 high / 114 medium / 1 low**; **23 `VACANT` intervals** (chained mid-term gaps, `person_name='VACANT'`). Cols: `city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event, end_event, election_year, first_vote, last_vote, sources, confidence, note`. Half-open interval `[start_date, end_date)`; **`end_date` empty = currently serving**. `confidence` ∈ high/medium/low (`high` = election result confirmed by minutes/votes or a minutes-documented event; `medium` = election-anchored but below a vote/minutes floor, or a gap-bounded date; `low` = holder unknown/not-acquired). `sources` cites each layer (election / minutes / votes / override). `first_vote`/`last_vote` are the earliest/latest observed Council-body vote **clamped to each tenure's own window** (blank if none, e.g. a non-voting mayor or a pre-floor tenure). |
| `district_version` | district × plan | 105 rows across 16 cities. The 7 at-large / single-district cities (lehi, logan, nephi, orem, park_city, st_george, vineyard) carry one degenerate `plan_id='current'`; the 9 real-district cities carry `plan_2022` + a prior plan + Citywide/Mayor rows. A redistricting is two `plan_id`s: the old plan carries a closed `effective_end`, the new plan is open-ended. `geometry_ref` is a path pointer (geometry not stored inline); an **unacquired prior plan** is an honest `confidence=low` row with blank `geometry_ref` (9 such gap rows — millcreek `plan_2016`, ogden/provo/slc `plan_2012`, sandy/south_jordan/taylorsville/west_jordan/west_valley `plan_pre2022`). |
| `district_precinct` | precinct × plan | 733 rows across the **9 district cities** (millcreek, ogden, provo, sandy, slc, south_jordan, taylorsville, west_jordan, west_valley). Versioned precinct→district composition sharing `plan_id`/dates with `district_version`; prior-plan gap rows have blank `precinct_id` + `confidence=low`. |
| `v_council_current` | view | **current seat-holders across all rostered cities** = `term` rows where `end_date IS NULL OR end_date=''` (107 rows). Includes the mayor. |
| `v_term_provenance` | view | per `(city, confidence)` tenure counts — a quick read on how much of each roster is election/minutes-anchored (high) vs pre-floor-inferred (medium). |

**The parameterized AS-OF pattern** (point-in-time roster on any date `:d`) — the view
above only answers "now"; for a historical roster use the half-open interval directly:

```sql
SELECT seat_id, person_name, body, start_event, confidence
FROM term
WHERE city = :city
  AND start_date <= :d
  AND (end_date = '' OR end_date > :d)
ORDER BY seat_id;
-- e.g. :city='provo', :d='2025-06-01' → D5 = Rachel Whipple (her 2022–2026 term).
```

Adding a new city: create `<city>_city_council/roster/build_roster.py` with a
`RosterConfig` + curated `TENURES` importing `roster_lib` (an at-large city omits
`redistrict`/`precinct_*`; a district city supplies them). The next
`build_cities_db.py` run federates it automatically — no change here needed.

## motion_std ↔ motion join — rate 100.00%

Join key: **(source, motion_no, meeting_date)** — motion-side date via
`meeting.meeting_date`. Fallback to (source, motion_no) where unique on both sides
(never needed in the current build). The date disambiguation exists because **sandy
PC's `source` is a constant Legistar-staging string**, making (source, motion_no)
degenerate there (SCHEMA_SPEC §2, documented).

All 32 files joined at **100.0%** — 29,483 / 29,483 rows matched to 29,483 distinct
motions (1:1, no fan-in). Per-file rates are stored in `build_info`
(`key LIKE 'join_rate:%'`).

## Row-count reconciliation (2026-07-11 build — reprinted and asserted every build)

One row per city (registry order), one column per federated table:

| city | body | person | meeting | application | motion | vote | role | referral |
|---|---|---|---|---|---|---|---|---|
| lehi | 3 | 27 | 281 | 1,407 | 2,342 | 12,362 | 36 | 459 |
| logan | 3 | 24 | 306 | 400 | 1,332 | 5,146 | 30 | 0 |
| nephi | 3 | 24 | 258 | 225 | 1,249 | 259 | 20 | 18 |
| ogden | 4 | 28 | 326 | 368 | 1,964 | 5,890 | 51 | 10 |
| orem | 5 | 52 | 242 | 303 | 1,082 | 6,844 | 65 | 30 |
| park_city | 4 | 24 | 363 | 676 | 2,159 | 7,980 | 46 | 100 |
| provo | 3 | 67 | 380 | 546 | 1,557 | 9,450 | 79 | 163 |
| sandy | 3 | 25 | 356 | 672 | 1,387 | 8,109 | 25 | 116 |
| slc | 5 | 71 | 494 | 893 | 2,582 | 18,169 | 78 | 31 |
| st_george | 5 | 63 | 393 | 1,545 | 2,765 | 14,565 | 48 | 117 |
| vineyard | 3 | 37 | 270 | 241 | 1,549 | 7,488 | 47 | 8 |
| west_jordan | 4 | 26 | 280 | 312 | 1,207 | 7,071 | 52 | 29 |
| west_valley | 4 | 28 | 679 | 559 | 2,548 | 12,055 | 43 | 31 |
| south_jordan | 4 | 19 | 398 | 487 | 1,807 | 1,110 | 24 | 13 |
| millcreek | 3 | 28 | 463 | 884 | 3,016 | 6,721 | 35 | 34 |
| taylorsville | 3 | 18 | 235 | 190 | 937 | 3,076 | 24 | 28 |
| **sum** | **59** | **561** | **5,724** | **9,708** | **29,483** | **126,295** | **703** | **1,187** |

The build FAILS (exit 1) if any per-city copy ≠ its source count or any federated
total ≠ the sum. `motion_std` = 29,483 = the motion total (every motion normalized).

## The `caveat` table (35 rows) — what it protects against

Columns: `city` (slug or `'*'`), `dataset` (`meeting_minutes` /
`planning_commission` / `public_comments` / `election_results` / `'*'`), `code`
(short machine key the views join on), `caveat` (the full text). Sourced from
SCHEMA_SPEC.md §4, root README "Coverage caveats", root CLAUDE.md quirk lines, and
`crosswalks/README.md`; the authoritative list is embedded in
`scripts/build_cities_db.py` (`CAVEATS`).

| code | city/dataset | one-line gist |
|---|---|---|
| `tally-only` | nephi mm | ~80% of votes carry no member name — per-member/dissent analysis limited to the named subset |
| `tally-only-partial` | logan mm, west_valley mm | substantial no-name vote shares |
| `dissent-only` | sandy mm, provo mm, west_jordan PC | minutes name only dissenters/absentees — counted Ayes < stated tallies by design (WJ PC: zero named Ayes) |
| `vote-ceiling` | orem \*, vineyard \* | orem records Aye/Nay only; vineyard never records Abstain — absences are recording limits, not behavior |
| `tie-break-note` | park_city mm | 2 mayoral tie-break Nays + 9 override resolutions carry `vote.note` |
| `coverage-floor` | slc mm (2021+), provo PC (2025+) | dataset starts later than the 2020 repo floor |
| `coverage-note` | st_george mm | 2020–21 are PMN backfill; one 2025-10-09 meeting unrecoverable |
| `body-gap` | ogden mm, sandy mm | ogden 2022–23 RDA/MBA sets never acquired; sandy publishes no separate RDA minutes (1 RDA vote row is all there is) |
| `outcome-unknown` | ogden mm | 126 `Recorded` motions = honest outcome unknowns |
| `landuse-undercount` | ogden mm | 428 council ordinance adoptions whose land-use subject was never captured — ogden council Land-Use share is an undercount |
| `no-hearing-motions` | st_george \* | open/close-hearing motions not captured (0% Public-Hearing vs vineyard 27%) |
| `text-quality` | nephi PC | truncated motion text + footer bleed → honest Other/low classifications |
| `degenerate-source-key` | sandy PC | Legistar-API source; (source, motion_no) degenerate, date needed |
| `comments-two-cities` | \* public_comments | comments substantive only in slc (13,334) + park_city (459); 8 honest zeros, 5 slivers, millcreek pending (in-packets) — in cities.db (`comment` + `fts_comment`) since 2026-07-06 |
| `elections-2019-floor` | \* election_results | elections 2019–2025 except slc 2007+ — NOT in cities.db |

## Views — caveat-aware by construction

Every cross-city view either **carries the relevant caveat codes on every row**
(LEFT JOIN-style correlated lookup, so a naive `SELECT *` sees them) or **excludes
non-quotable rows by design**:

- **`v_contested_all`** — every motion whose recorded outcome was **not
  unanimous**: contested = a dissent was *named* (Nay/Abstain/Recuse row) **OR**
  the printed *tally* shows nay/other (motion_std). This union catches both named
  dissent and tally-only dissent (a bare "5:2" with no roll call); neither alone
  is complete. Columns: city, body, date, `motion_type_std`/`land_use_type`,
  verbatim text/result, `vote_mode`, and two families of counts —
  **`tally_aye`/`tally_nay`/`tally_other`** (authoritative margins from motion_std,
  falling back to named counts only where no std tally exists — **use these**) and
  **`named_ayes`/`named_nays`/`named_abstains`/`named_recuses`** (who was actually
  named; attribution only, and they UNDERCOUNT in dissent-only/tally-only cities —
  e.g. provo work sessions record only dissenters, so `named_ayes=0` while
  `tally_aye=5`). **`dissent_caveats`** carries the tally-only/dissent-only/
  vote-ceiling codes so every skewed row is impossible to miss.
  **`tally_other` semantics (audited at source 2026-07-19 — BY DESIGN):**
  `motion_std.tally_*` mirror only PRINTED tallies; when a source prints a bare
  "A:N" and records an abstention/recusal only in prose/roll/table-mark, its
  `tally_other` is NULL (never 0) and the vote ROW is the authority — the view's
  `COALESCE(tally_other, named-count)` then supplies the abstain/recuse count
  from the named rows, so such motions are NOT undercounted. A source that
  prints a third number ("6-1-1") or an "N recused" phrase does get a real
  `tally_other`. Ground-truthed across 9 cities (see
  `scripts/normalize_motions.py` header + TODO "v_contested_all redefinition"
  follow-up (1)).
  **Per-city parity (2026-07-19):** each city's own `db/civic.db` `v_contested`
  now mirrors this column shape (split `tally_*` vs `named_*`, `motion_type_std`,
  `land_use_type`, `vote_mode`, `provenance`), backed by a per-db `motion_std`
  table — but its MEMBERSHIP stays named-dissent-only; the tally-dissent UNION
  remains unique to this federated view.
- **`v_member_record_all`** — per (city, member, body): vote counts by value,
  `nay_pct_of_aye_nay`, and **`record_caveats`**. Orem's zero absences and sandy/
  provo/WJ-PC's inflated nay-shares (unnamed Aye majorities) are flagged per row.
- **`v_landuse_outcomes`** — motion_std-based: city × dataset × year ×
  `land_use_type` × `action_class` × `outcome` with counts and
  **`landuse_caveats`** (ogden's undercount, coverage floors, outcome unknowns).
- **`v_pc_divergence`** — PC recommendation vs linked council outcome through the
  reconstructed `referral` layer. **Excludes `confidence='low'` links by design**
  (repo rule: low = flagged, do not quote — the rows stay in `referral`).
  `council_outcome` is the latest council-stage motion on the linked application;
  `diverged=1` = PC said Negative but council passed (or Positive/failed).
  Referral density varies hugely by city (lehi 435 links, ogden 1) — that is
  linkage coverage, **not** divergence behavior; never compare divergence *rates*
  across cities without noting link counts.
- **`v_coverage`** — the caveat-aware coverage matrix: one row per city × vote
  dataset (motions, passes, unknowns, date span, **full caveat text**), plus
  caveat-only rows for `public_comments` / `election_results` so datasets outside
  cities.db surface in any coverage scan. 37 rows.

## Example queries (the marquee questions)

**Cross-city land-use approval rates** (final actions only — recommendations are a
different act; caveat flag shows where the denominator is skewed):

```sql
SELECT city,
       SUM(n_motions) AS landuse_final_actions,
       ROUND(100.0 * SUM(CASE WHEN outcome='pass' THEN n_motions ELSE 0 END)
             / SUM(n_motions), 1) AS pass_pct,
       MAX(landuse_caveats IS NOT NULL) AS has_caveats
FROM v_landuse_outcomes
WHERE action_class = 'final-action' AND outcome IN ('pass','fail')
GROUP BY city ORDER BY pass_pct;
-- 2026-07-02: provo 95.2% … vineyard/ogden/nephi 100.0%; lehi has the volume (945).
```

**Dissent rates by city** (council-side; caveats column shows which cities can't be
compared naively):

```sql
WITH c AS (SELECT city, COUNT(*) n FROM v_contested_all
           WHERE body != 'PlanningCommission' GROUP BY city),
     t AS (SELECT m.city, COUNT(*) n FROM motion m
           JOIN body b ON b.body_id = m.body_id
           WHERE b.name != 'PlanningCommission' GROUP BY m.city)
SELECT t.city, t.n AS motions, COALESCE(c.n,0) AS contested,
       ROUND(100.0*COALESCE(c.n,0)/t.n, 1) AS contested_pct,
       (SELECT GROUP_CONCAT(code,',') FROM caveat cv
         WHERE (cv.city=t.city OR cv.city='*')
           AND cv.dataset IN ('meeting_minutes','*')
           AND code IN ('tally-only','tally-only-partial','dissent-only','vote-ceiling'))
       AS caveats
FROM t LEFT JOIN c ON c.city = t.city ORDER BY contested_pct DESC;
-- 2026-07-02: west_jordan 17.1% … nephi 2.4% (tally-only — dissent mostly invisible).
```

**Technical-vs-political divergence** (where did the elected body override the
appointed body?):

```sql
SELECT city, COUNT(*) AS links,
       SUM(pc_recommendation='Negative') AS pc_negative,
       SUM(diverged) AS diverged
FROM v_pc_divergence GROUP BY city ORDER BY links DESC;

SELECT city, confidence, pc_date, pc_recommendation,
       council_date, council_outcome, council_item
FROM v_pc_divergence WHERE diverged = 1 ORDER BY city, council_date;
-- 2026-07-02: 703 quotable links; lehi dominates (435 links, 38 divergences —
-- mostly council passing GP amendments/rezones the PC recommended against).
```

**Thematic full-text search** (what used to require rereading 6,400 files):

```sql
SELECT city, COUNT(*) AS mentions
FROM fts_minutes WHERE fts_minutes MATCH '"accessory dwelling"'
GROUP BY city ORDER BY mentions DESC;
-- 2026-07-06: slc 107, millcreek 93, provo 74, park_city 55 … all 16 cities, instant.
-- snippet(fts_minutes, 0, '>>', '<<', '…', 12) pulls the matching passage;
-- the `path` column opens the full minutes file.
```

**Adopted ordinance → enacting motion → roll-call votes** (who voted against enacted
land-use law):

```sql
SELECT o.city, o.ordinance_no, o.title, p.full_name, v.vote_value
FROM ordinance o
JOIN motion m ON m.motion_id = o.motion_id
JOIN vote v   ON v.motion_id = m.motion_id
JOIN person p ON p.person_id = v.person_id
WHERE o.land_use != '' AND v.vote_value = 'Nay';
-- only rows with motion_resolution='unique' carry a motion_id — never forced.
```

**Money vs. land-use votes** (the elections→finance→votes chain):

```sql
SELECT cc.city, cc.candidate, SUM(cc.amount_num) AS amt,
       (SELECT COUNT(*) FROM vote v
         JOIN motion_std ms ON ms.motion_id = v.motion_id
        WHERE v.person_id = cp.person_id
          AND ms.motion_type_std = 'Land-Use' AND v.vote_value='Aye') AS landuse_ayes
FROM cf_contribution cc
JOIN cf_candidate_person cp
  ON cp.city = cc.city AND cp.candidate = cc.candidate AND cp.person_id IS NOT NULL
WHERE cc.donor_type = 'business'          -- or filter donor_raw by keyword
GROUP BY cc.city, cc.candidate;
-- per-candidate/race TOTALS must come from cf_cycle, never cf_filing sums.
```

## Regeneration & trust chain

```
per-city:  python3 db/build_db.py && python3 db/build_referrals.py   (each city)
           python3 scripts/normalize_motions.py --all                 (motions_std; --all sweeps all cities)
federated: python3 scripts/build_cities_db.py                         (this db —
           automatically runs scripts/build_search_layer.py at the end; the
           search layer alone can be refreshed with
           python3 scripts/build_search_layer.py)
```

cities.db is the **last** link: rebuild it whenever anything upstream changes. It
never feeds back into any canonical file (read-only on all per-city data). The build
prints — and asserts — the reconciliation table and join rates above; a silent
mismatch is impossible.
