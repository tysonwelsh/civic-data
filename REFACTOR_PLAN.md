# REFACTOR_PLAN — LLM-retrieval refactor (approved 2026-07-06)

Owner-approved plan from the 2026-07-06 repo-wide evaluation (skills + storage structure,
four parallel survey agents: cross-city conformance, db retrievability, file-format deep
sample, tooling duplication). Goal: make the repo's growth/development data maximally
searchable by an LLM **through tools** (SQL, grep-able text), not by rereading files.

Verdict that drove this plan: the structured vote spine is strong — "all 2024 rezone
final actions across 16 cities with outcomes" is already one SQL query against
`cities.db` — but every text corpus (6,398 minutes markdown files, 17,943 public
comments, 4,115 ordinances) and two **already-structured** datasets (campaign finance:
12,841 contributions + 10,697 expenditures; the computed ordinance→motion linkage) live
outside any database, and there is **no full-text index anywhere**. The expansion
datasets' `index.csv` schemas are per-city ad hoc, and five shared scripts each hardcode
their own city list (three orderings; `refresh_status.py` still lists 13 cities — a live
bug that silently skips millcreek/south_jordan/taylorsville from refresh dashboards).

Work discipline (inherited from REMEDIATION_PLAN.md): back up every modified file to
`_backups/<date>/<relative path>` (no-clobber) before touching it; derived layers are
regenerated, never hand-edited; city-faithful values are never overwritten; every phase
ends with verification (validators + before/after counts) and a dated check-off here.

---

## Phase 1 — City registry + 16-city doc refresh (small; fixes a live bug)

- [x] 1.1 (2026-07-06) **`scripts/cities.py` single-source registry.** One ordered list of records
      `(slug, dir, db_path)` (+ room for weekday/vendor metadata later). Order is
      LOAD-BEARING: it must exactly preserve `build_cities_db.py`'s current `CITIES`
      tuple order (13 alphabetical + south_jordan/millcreek/taylorsville appended —
      offsets 14/15/16 are published namespacing). New cities are APPENDED only.
- [x] 1.2 (2026-07-06) **Refactor the five consumers to import it**: `build_cities_db.py`,
      `build_coverage.py`, `build_sources_index.py`, `normalize_motions.py`,
      `refresh_status.py`. The refresh_status change FIXES the missing-3-cities bug.
      Verify: rerun `refresh_status.py` (now 16 rows) and `build_coverage.py`
      (coverage.json unchanged except by-product ordering, byte-diff checked).
- [x] 1.3 (2026-07-06) **Doc refresh 13 → 16** in root `README.md`, `CLAUDE.md`, `SCHEMA_SPEC.md`
      (incl. §4 vote-value ceiling rows for millcreek/south_jordan/taylorsville,
      measured from the flat CSVs), `cities_db_SCHEMA.md` (city_index 1..16, current
      row counts from `build_info`), stale docstrings in `build_cities_db.py`, and the
      `refresh-city` skill's "13 cities" default-scope text. Add the 3 new cities'
      one-liner quirks to root CLAUDE.md.

## Phase 2 — Search layer in `cities.db` (the retrieval transformation)

New `scripts/build_search_layer.py`, invoked at the end of `build_cities_db.py` (so one
rebuild command still produces the whole federated db). All tables carry a leading
`city` column like the existing core. Additions:

- [x] 2.1 (2026-07-06) **`comment` table** — union of the 13 `public_comments/all_comments_clean.csv`
      (17,943 rows; honest-empty cities contribute 0 rows, recorded in `caveat`).
- [x] 2.2 (2026-07-06) **Campaign-finance tables** — `cf_filing` (filing_totals.csv), `cf_contribution`,
      `cf_expenditure`, `cf_cycle` (cycle_totals.csv) from the 15 structured cities.
      Include a `cf_candidate_person` crosswalk (name-key match to `person`, confidence
      column, never forced) so money joins to the vote record. Propagate the
      "NEVER sum filing_totals — use cf_cycle" rule into the table comments/SCHEMA doc
      and a `caveat` row.
- [x] 2.3 (2026-07-06) **`ordinance` table** — from the 16 `ordinances/index.csv` files via a tolerant
      column mapper (the per-city synonym drift is real: `land_use`/`land_use_category`/
      `land_use_type`/`zoning`, etc.). Carry the existing `matched_motion_date/no/
      match_confidence` linkage and resolve it to `motion_id` where the join lands
      (method + confidence columns; unmatched stays NULL, never forced).
- [x] 2.4 (2026-07-06) **`document` catalog table** — one row per source artifact across minutes,
      packets, ordinances, housing_plans, transcripts, pmn_backfill:
      `(city, doc_type, date, body, title, path, format, has_text, source_url)`.
      Soft-link to `meeting_id` by (city, body, date) where a meeting exists.
- [x] 2.5 (2026-07-06) **FTS5 external-content tables**: `fts_minutes` (the minutes markdown corpora,
      keyed to `document`/`meeting`), `fts_motion` (motion_text), `fts_comment`,
      `fts_ordinance` (ordinance text sidecars where they exist). Porter tokenizer.
- [x] 2.6 (2026-07-06) **Update `cities_db_SCHEMA.md`** with the new tables + example queries
      (thematic FTS search; ordinance→motion→vote; contributions vs land-use votes).
      Verification: row-count reconciliation vs source CSVs per city; the three example
      queries must return sane results; `build_cities_db.py` end-to-end rerun is
      idempotent.

## Phase 3 — Expansion `index.csv` schema contracts + migration

- [x] 3.1 (2026-07-06) **Write the per-source-type column contracts** into SCHEMA_SPEC (landed as §9):
      exact required header for `packets/`, `ordinances/`, `campaign_finance/`,
      `pmn_backfill/`, `transcripts/` (housing_plans' 11-col header is the model and
      is already ~uniform). Canonical names decided once (e.g. packets meeting key,
      ordinance `land_use_type`, CF match columns). Extra city-specific columns remain
      allowed AFTER the contract columns.
- [x] 3.2 (2026-07-06) **Migrate all 16 cities' index.csv files** to the contracts (column renames /
      reorders only — values untouched; originals backed up). Rebuild the Phase-2
      loaders' synonym maps down to the contract. DONE: 75 migrated + 21 already
      conformant, per-column value identity asserted; 5 CF index-writer/reader scripts
      updated (lehi/logan/orem/park_city build_index.py + orem build_finance.py; lehi
      builder reproduces the migrated file byte-for-byte); 17 doc files' column
      references updated; sources.csv regenerated ×16 (fixes millcreek packets paths
      that the old retained_raw_path name hid from the sources index). NOTE for 5.7:
      some dataset CLAUDE.md files still print full pre-migration header LISTINGS
      (e.g. lehi packets) — true them up in the Phase-5 doc sweep.
- [x] 3.3 (2026-07-06) **Enforce**: `expand-city-sources/scripts/validate_dataset.py` checks exact
      contract headers (96/96 datasets PASS; also fixed its path resolution to accept
      city-root-relative paths); skill rule 2 rewritten to cite §9. `validate_city.py`
      gains the same checks in Phase 4.4 as planned.

## Phase 4 — Tooling consolidation + validator extension

- [x] 4.1 **`scripts/weeks_lib.py`** — lift the ~180 shared lines of `build_weeks.py`;
      per-city file becomes a config stub (CITY, MEETING_WEEKDAY + call). slc's fork
      gets its extra behavior as hooks or stays documented-divergent.
      *(Done 2026-07-07: 15 cities → 15-line stubs over `weeks_lib.build(city_dir,
      city_name, meeting_weekday, index_council_label)`; only observed deltas
      parameterized (provo/st_george index-heading label "City Council"). Every
      converted city's regenerated `weeks/` verified byte-identical (per-file md5
      manifests + stdout, no exclusions). slc stays documented-divergent (header
      comment only, body untouched). Old copies: `_backups/2026-07-06-refactor/`.)*
- [x] 4.2 **`scripts/referrals_lib.py`** — 13 copies are byte-identical today; lift
      verbatim, stub the callers, reconcile the 3 forks explicitly.
      *(Done 2026-07-07: 328-line lib = the shared 286-line copy verbatim,
      parameterized by exactly the observed fork deltas — `case_no_re`,
      `case_no_method_label` ('pl_number' south_jordan / 'case_no' millcreek+
      taylorsville), `case_no_report_label`, `extra_stopwords`; defaults (None) =
      the 13-city behavior. 13 cities → one byte-identical 13-line stub; 3 forks →
      25–31-line stubs keeping their explanatory comments. All 16 verified: referral
      table dump + sqlite_master schema + referrals_audit.csv + tables/referral.csv
      + stdout byte-identical to pre-conversion state, no exclusions; cwd=db/ and
      absolute-path invocations both checked. Old copies:
      `_backups/2026-07-06-refactor/`.)*
- [x] 4.3 (2026-07-07) **db-build core library** (`scripts/db_build_lib.py`). Done: the lib
      is the 397-line fail-loud variant (the 347↔397 delta was ONLY the
      vote_overrides.csv reconciliation block, so all 10 template cities now get the
      fail-loud behavior — the six 347-line cities previously still had the silent
      INSERT OR IGNORE path). 10 cities converted to a 15-line stub (lehi, logan,
      nephi, orem, vineyard, west_valley, ogden, provo, st_george, west_jordan);
      each verified: old-script rebuild dump + tables/*.csv manifest vs stub rebuild —
      **10/10 byte-identical** (also proves none of the 6 had latent silently-dropped
      vote conflicts). The 6 real forks (slc, sandy, park_city, south_jordan,
      millcreek, taylorsville) stay forked with a DOCUMENTED FORK header pointing at
      the lib ("fix the lib first, port by diffing"). Referral layers restored after
      each rebuild; originals in `_backups/2026-07-06-refactor/`.
- [x] 4.4 (2026-07-07) **Extend `validate_city.py`**: added k.expansion (§9 contract
      header per present expansion dataset) and l.crosswalks (every observed body
      code / vote value / motion_type has a city or '*' crosswalk row; body+vote =
      FAIL, motion_type = WARN). All 16 cities pass 0 FAIL. Repo-level doc-staleness
      checking deferred to the 5.7 doc sweep (per-city validator is the wrong home).
- [x] 4.5 (2026-07-07) **`scripts/rebuild_derived.py`** — one command per city (db →
      referrals → weeks → motions_std → sources → validate) + repo level (coverage →
      cities.db incl. search layer), fail-loud. Tested end-to-end on nephi.
      refresh-city §4 + remediate-city-data step 5 now point at it.
- [x] 4.6 (2026-07-07) **body_crosswalk logan/provo/vineyard** — added at the
      authoritative source (the BODY_CROSSWALK table embedded in
      scripts/normalize_motions.py, which regenerates the CSV verbatim — editing the
      CSV alone would be clobbered); the three cities' body codes were technically
      wildcard-covered, so the rows document each city's actual RDA convening mode.
      The new l.crosswalks validator check is wildcard-aware.

## Phase 5 — Consistency cleanups + skill updates

- [x] 5.1 (2026-07-07) **Roster**: 13 older cities now have an OBSERVED
      `meeting_minutes/roster.csv` (member,first_seen,last_seen,n_votes — from the db
      role table, one row per person across all meeting_minutes-sourced bodies).
      This ACTIVATED the dormant off-roster-voter HARD check in every city's
      validate_votes.py (first run caught that st_george's roster must include its
      separate-member Arts Commission — fixed); all 16 validate 0 FAIL.
- [x] 5.2 (2026-07-07) **Honest-empty comments, one representation**: header-only 14-col
      `all_comments_clean.csv` written for millcreek / south_jordan / taylorsville.
- [x] 5.3 (2026-07-07) **Election schema superset + naming one-offs** — DONE: all 16
      `<slug>_races.csv` migrated to the 25-col superset (per-column value identity
      asserted; total_votes vs total_first_choice_votes kept semantically distinct,
      blanks never inferred; contract now in SCHEMA_SPEC §9 + enforced by
      validate_city check m.elections); 12 election files renamed to slug-consistent
      names (parkcity_/stgeorge_/wjordan_/wvc_ retired) with 29 doc/script references
      updated (park_city + st_george CF builders re-run and verified); park_city
      minutes_skipped.csv → minutes_unrecovered.csv; ogden comments-dropped file →
      standard name (+2 docs); lehi EXPAND_SOURCES_PILOT_REPORT.md →
      EXPAND_SOURCES_REPORT.md (+root README).
- [x] 5.4 (2026-07-07) **Provenance headers in minutes markdown** — DONE via the new
      permanent `scripts/add_minutes_headers.py` (idempotent; additive-only invariant
      asserted per file): 5,623 headers added across 14 cities (vineyard/taylorsville
      + parts of south_jordan/west_valley already had them — the newer-build
      convention, now universal). Pre-change corpus tarball:
      `_backups/2026-07-06-refactor/minutes_pre_headers_2026-07-07.tar.gz` (47 MB).
      refresh-city step 3 now runs the script after every fetch. Screener stable.
- [x] 5.5 (2026-07-07) **Slim `weeks/`** — DONE: weeks_lib.py (+ slc's fork) now LINK
      minutes from summary.md via relative paths instead of copying; all 16
      regenerated; weeks/ footprint 196 MB → 68 MB; validators pass; SCHEMA_SPEC §6 +
      root docs updated.
- [x] 5.6 (2026-07-07) **Packet text sidecars** — DONE via the new permanent
      `scripts/extract_packet_text.py` (idempotent, honest `_extraction_log.csv` per
      city): 3,446 sidecars extracted (38 MB text; 109 image-only + 2 errors logged,
      no sidecar faked), after normalizing 771 repo-relative `path` values
      (lehi/ogden packets + 6 cities' pmn_backfill) that had hidden files from every
      resolver. New `fts_packet` FTS5 table in cities.db (build_search_layer) — "what
      did staff say about X" is now a query. Also swept ALL index-writing scripts:
      11 more builders emitted pre-contract headers and were fixed + rerun-verified
      byte-identical (agent report; slc's build_url_recovery.py writes a provenance
      sidecar, not index.csv — left as-is).
- [x] 5.7 (2026-07-07) **Skill updates + doc sweep** — DONE.
      Skills: expand-city-sources (mandatory packet/ordinance text sidecars via
      scripts/extract_packet_text.py, dataset-relative path rule, new db-load step 10);
      build-city-data-repo (Phase 4 rewritten for the shared libs + stubs, registry
      append in scripts/cities.py, embedded-crosswalk editing, add_minutes_headers,
      one honest-empty comments form, 25-col election superset + slug filenames,
      rebuild_derived.py); refresh-city (add_minutes_headers + extract_packet_text
      after fetch; rebuild_derived already pointed); audit-city-data (search-layer
      reconciliation, weeks-copies-as-staleness-signal, doc city-count checks,
      crosswalk coverage, NEW §e2: expansion datasets + CF structured layer in
      scope); cf-vision-transcribe (cache-key standardization deferral note → new
      TODO.md item). Doc sweep (agent-verified): 70 stale schema listings fixed
      across 67 per-city dataset docs, zero remaining out-of-order index.csv
      enumerations repo-wide; all 67 backed up.
- [x] 5.8 (2026-07-07) **Hygiene** — DONE: 63 __pycache__ dirs + 36 .DS_Store removed;
      EXPAND_SOURCES_PROMPT.txt retired to _backups; _comment_qc/ relocated to
      `_audits/comment_qc/` (reference in the 2026-07-02 audit report updated);
      root `.gitignore` created per the decided GitHub shape (raw/, _backups/, .env,
      OS noise).

## Sequencing + status

1 → 2 are this session's targets (1 is small and fixes a live bug; 2 is the vision).
3 → 4 → 5 follow; 4.3 depends on 2, 3.3 depends on 3.1–3.2, 5.6 feeds a follow-on FTS
table. Each completed item gets a dated check-off here and, where user-visible, a
TODO.md note.

---

## COMPLETE (2026-07-07)

All five phases executed and verified. End state: 16/16 cities validate 0 FAIL
(26 checks each, incl. the new k.expansion / l.crosswalks / m.elections and the
newly-activated off-roster-voter hard check); cities.db (373 MB, derived) carries
the full search layer — comment / cf_* / ordinance / document + five FTS5 indexes
(minutes 6,466 files, motions, comments, ordinances, packets 3,446 sidecars);
one-command rebuild via scripts/rebuild_derived.py; every original under
_backups/2026-07-06-refactor/ (incl. the pre-header minutes tarball and the
migration/conversion scripts). Deferred follow-ups live in TODO.md (CF vision
cache-key standardization; the packet OCR/image-only backlog stays honest in each
city's packets/text/_extraction_log.csv).
