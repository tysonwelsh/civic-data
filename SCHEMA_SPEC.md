# SCHEMA_SPEC — the civic-data city standard (normative)

This document defines the standard every `<city>_city_council/` repository in this
collection conforms to. Until 2026-07-02 the standard existed only by convention (the
SLC template plus the `build-city-data-repo` skill); this makes it explicit and
checkable. Check any city with:

```
python3 scripts/validate_city.py <city>_city_council/
```

Validation never mutates data. Principles that govern everything below:

1. **City-faithful values are never overwritten.** Normalized/derived fields live in
   columns or files *alongside* the verbatim source values.
2. **Honest gaps are data.** A missing meeting, an unnamed voter, an empty comments file
   are recorded as absences (`minutes_unrecovered.csv`, `names_recorded:false`,
   `AVAILABILITY.md`) — never filled in.
3. **Derived layers are regenerable and are never hand-edited** (`db/`, `weeks/`).

---

## 0. Entity model (2026-07-11) — cities, counties, regions, the state

The collection's unit is a **government entity**, not just a city. Every entity has a
stable **slug**, a **level** ∈ `{city, county, regional, state}`, and a **state**
(`ut` today — the model is multi-state ready). Cities remain the founding tier; counties,
regional bodies (MPOs/AOGs), and the state are added the same way.

- **Identity is flat; geography is data.** Each entity is a flat top-level folder
  (`<city>_city_council/`, `<county>_county/`, `<slug>_mpo/`, `ut_state/`) — a slug never
  encodes its parent. The hierarchy lives in `registry/relationships.csv` as a many-to-many
  graph (`within` / `member_of` / `overlaps` / `succeeds`), so an MPO can span several
  counties and a city can straddle two counties without a false single parent.
- **The registry is the single source of truth.** `registry/entities.csv` +
  `registry/relationships.csv`, loaded by `scripts/entities.py`. `scripts/cities.py` is now
  a back-compat shim exposing the `level=='city'` rows under the historical interface. The
  per-entity **`fed_index`** is the LOAD-BEARING federation offset (`fed_index * 10,000,000`);
  it is append-only, with non-overlapping bands reserved per level: **city 1–99** (16 used),
  **county 101–199**, **regional 201–299**, **state 301–999**.
- **Datasets are modules, not a fixed tree.** An entity carries only the modules that fit it
  (a county is not a big city). A county council, a city council, an MPO board, and the
  legislature are all *deliberative bodies*, so they all flow into the same relational vote
  spine (§5) and the federated DB — which is what makes cross-tier questions one query.
- **Value gate.** Acquire a module for an entity only where it is uniquely valuable and
  feasible; bulky GIS/parcel data is catalogued + linked + reduced to derived summaries,
  never mirrored. Honest gaps (principle 2) apply identically at every level.

The federated DB (`cities.db`; the `gov.db` rename is deferred) carries a leading `city`
column (the entity slug — city *or* county/regional/state) plus **`gov_level`** and
**`state`** on every core table, and the `entity` + `entity_relationship` registry tables.
See `cities_db_SCHEMA.md`.

---

## 1. Standard directory layout

```
<city>_city_council/
  README.md              front door: coverage table, structure, gaps, regeneration cmds
  CLAUDE.md              LLM analysis guidance: join keys, which artifact for which question
  recon.md               source/provenance map (which portal, what exists, what doesn't)
  VERIFICATION.md        independent QA record + audit/remediation addenda
  build_weeks.py         regenerates weeks/ (CITY + MEETING_WEEKDAY at top)

  meeting_minutes/       CORE (required)
    minutes/<YYYY>/<week-start>/<date>_<slug>.md    one markdown file per meeting
    minutes_index.csv    one row per minutes document (schema §3)
    minutes_unrecovered.csv   meetings known to exist whose minutes could not be recovered
    all_votes.csv        long-format member-vote rows (schema §2)
    extract_votes.py     the (city-specific) extractor that produced all_votes.csv
    roster.csv           voter roster for this dataset. Two conformant formats:
                         OBSERVED (member,first_seen,last_seen,n_votes — from the db
                         role table, one row per person across ALL bodies sourced
                         from meeting_minutes/, i.e. everything except
                         PlanningCommission — incl. separate-member bodies like
                         st_george's Arts Commission; the 13 pre-2026-07 cities,
                         added 2026-07-07) or CURATED (district,surname,full_name,
                         role,term_observed,notes — the three 2026-07-06 cities).
                         Observed rosters honestly omit people who never appear in a
                         named vote (non-voting mayors, tally-only cities). NOTE:
                         once roster.csv exists, each city's validate_votes.py
                         enforces voter-resolvable-to-roster as a HARD check.
    raw/                 retained source PDFs (required going forward; historic cities
                         may lack it — re-fetch via minutes_index.csv source_url)

  planning_commission/   PC minutes + votes; same schemas as meeting_minutes.
                         Every vote row body=PlanningCommission.
                         (sandy exception: PC votes come from the Legistar API; no
                         minutes/ or minutes_index.csv — documented in its CLAUDE.md)

  public_comments/       all_comments_clean.csv (may be honestly EMPTY) +
                         AVAILABILITY.md (the audit of what the city publishes) +
                         optionally minutes_speaker_log.csv (in-person speaker
                         record-notes — NOT public-submitted comments)

  election_results/      <city>_races.csv, <city>_results_by_candidate.csv,
                         <city>_results_by_precinct.csv (+ raw county files where kept)

  db/                    relational SQLite (civic.db; sandy.db/lehi.db/parkcity.db legacy
                         names) + SCHEMA.md + build_db.py + build_referrals.py +
                         tables/*.csv exports + overrides csvs (§5)

  geo/                   precinct boundaries + address_to_district.py

  roster/                DERIVED rolling council-roster — council_terms.csv (seat-tenure
                         intervals) + district_versions.csv + district_precincts.csv +
                         roster_overrides.csv + build_roster.py + CLAUDE.md

  weeks/                 DERIVED weekly bundles (§6) — regenerate, never hand-edit
```

**Roster layer** (`roster/`, all 16 cities as of 2026-07-11; DERIVED, regenerate with
`python3 roster/build_roster.py`, never hand-edit the generated CSVs — corrections go in
`roster_overrides.csv`). Tracks who holds each council + mayor seat over time as dated,
half-open `[start_date, end_date)` intervals with per-row `confidence` + `sources`. Files:
`council_terms.csv` (`city, body, seat_id, district, person_name, person_key, start_date,
end_date, start_event, end_event, election_year, first_vote, last_vote, sources,
confidence, note`; `person_name='VACANT'` = a chained mid-term gap; `end_date` empty =
serving), `district_versions.csv` + `district_precincts.csv` (redistricting-versioned
boundaries/precincts, prior plans kept as honest `confidence=low`/blank-geometry gaps),
`roster_overrides.csv` (hand-correction layer, applied last). Generated by a thin per-city
`build_roster.py` over the shared `scripts/roster_lib.py`; federated into `cities.db`
(`term`/`district_version`/`district_precinct` + views `v_council_current`/
`v_term_provenance` — see `cities_db_SCHEMA.md`). Each city's `roster/CLAUDE.md` is
authoritative.

**Expansion datasets** (additive; piloted in `lehi_city_council/`, in progress
elsewhere): `packets/`, `housing_plans/`, `ordinances/`, `pmn_backfill/`,
`transcripts/`, `campaign_finance/`. Each is self-contained: own `CLAUDE.md`,
`AVAILABILITY.md`, `index.csv`, retained `raw/` originals, and honest
`unrecovered.csv` where applicable. Their absence in a city is expected, not an error.

---

## 2. `all_votes.csv` — the 13-column vote schema

Long format: **one row per member-vote** (or one placeholder row per tally-only
motion). Applies to both `meeting_minutes/all_votes.csv` and
`planning_commission/all_votes.csv`.

Header, in order:

```
date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source
```

| column | semantics |
|---|---|
| `date` | meeting date, ISO `YYYY-MM-DD` (source clerk-typo dates are resolved and documented in the city's VERIFICATION.md, never silently altered) |
| `year` | integer, must equal `date`'s year |
| `title` | meeting title as published |
| `body` | short body code: `Council`, `PlanningCommission`, `RDA`, `CRA`, `LBA`, `MBA`, `HA`, `SSLD`, … (city-native code set; cross-city canonical names come from the `crosswalks/body_crosswalk.csv` layer, §8) |
| `motion_no` | 1-based motion sequence **within the source document** — `(source, motion_no)` is the motion key |
| `motion` | verbatim (lightly whitespace-normalized) motion text |
| `motion_type` | **city-native** category from that city's fixed taxonomy (~12 categories, labels vary by city — e.g. `Procedural/Administrative`, `Land-Use/Zoning`). NEVER compare raw across cities; use `motions_std.csv` (§8) |
| `result` | **verbatim** outcome string as printed (`4-0 Pass`, `Carried unanimously`, `Voice Pass`, `Died (no second)`, embedded prose…). 8–33 distinct strings per city; no controlled vocabulary by design — the parsed form lives in `motions_std.csv` (§8) |
| `mover`, `seconder` | member names as printed (may be blank) |
| `member` | the voting member's name. **Blank = tally-only motion** (names not printed in source); paired with blank `vote` |
| `vote` | one of the controlled vocabulary (§4), or blank on tally-only rows |
| `source` | path to the source minutes document, relative to the **city root** (`meeting_minutes/minutes/...`) or to the **dataset dir** (`minutes/...`) — both occur; join key with `motion_no` |

Documented extensions (allowed, flagged by the validator as WARN):
- **slc `planning_commission/all_votes.csv`** carries two extra columns
  (`action_class`, `names_recorded`) and a different column order; all 13 standard
  columns are present.
- **park_city** flat value `"Nay (Mayor tie-break)"` (2 rows) — split into
  `Nay` + `note='Mayor tie-break'` in its db.
- **sandy PC** `source` is not a file path (`db/staging (Legistar EventItemVote, body 140)`)
  and is constant across all rows — so `(source, motion_no)` is **degenerate** there;
  motion identity in sandy PC requires `(source, motion_no, date)`.
- **`provenance`** — a 14th trailing column on the `all_votes.csv` files that received
  votes recovered from independent sources: `minutes` (audited primary layer) vs the
  recovered values `pmn_roa` / `pmn_minutes` (Utah Public Notice) and the non-PMN
  channels `agendacenter_minutes` / `wayback_minutes` / `citysite_minutes` /
  `doccenter_draft` / `packet_carve` (the last two = ogden PC 2020–2023 gap recovery,
  2026-07-19: standalone CivicPlus DocumentCenter draft minutes vs following-meeting
  agenda-packet carves). Present ONLY where recovered rows exist (e.g. `meeting_minutes/`
  in ogden/orem/south_jordan/vineyard and `planning_commission/` in
  ogden/provo/west_jordan); absent — not blank — elsewhere. Threaded
  through to db `motion.provenance` (§5) and `cities.db`.

**Tally-only rows.** When minutes record only a tally ("passed 5-0") with no names, the
motion appears as a single row with `member` and `vote` blank. No member is ever
guessed. Cities with substantial tally-only shares: nephi (most rows), logan, ogden,
west_valley, sandy (narrative tallies name only dissenters), west_jordan PC.

---

## 3. `minutes_index.csv`

One row per minutes document actually on disk. Header, in order:

```
date,year,title,slug,path,source,source_url,format
```

| column | semantics |
|---|---|
| `date` | meeting date, ISO |
| `year` | = date's year |
| `title` | published meeting title |
| `slug` | filename-safe meeting identifier |
| `path` | path to the markdown/text file, relative to the city root or the dataset dir (both occur); must exist |
| `source` | portal identifier (`primegov`, `laserfiche`, `granicus`, `civicclerk`, `civicplus`, `legistar`, `revize`, `onbase`, `gdrive`, `slcdocs`, `pmn`, …) |
| `source_url` | re-fetchable URL of the original document (provenance of record where `raw/` is absent) |
| `format` | how the text was obtained: `text`/`md` (born-digital), `ocr`, `pdf`, `pdf-text`, `compilation`, … (city-documented values) |

Documented extensions: extra trailing columns are allowed and validator-WARNed
(`from_compilation` in ogden, `packet_url` in provo/west_jordan). SLC's pre-retrofit
extras are frozen in `minutes_index_legacy.csv`.

Meetings that exist but whose minutes could not be recovered go in
`minutes_unrecovered.csv` — never as stub or wrong-document rows in the index.

---

## 4. Vote-value vocabulary

```
Aye | Nay | Abstain | Recuse | Absent | Excused
```

plus **blank** on tally-only rows (§2). Anything else is a defect — except the two
documented extensions in §2 (park_city tie-break annotation; sandy's Legistar-layer
`Nonvoting`, which appears only in its db's `legistar_vote` extension table, §5).

**Per-city ceilings — what each city's source actually records** (measured 2026-07-02;
the three 2026-07-06 cities measured at build time; comparisons must respect these —
an absent value is a *recording* limit, not behavior):

| city | council values observed | PC values observed | ceiling notes |
|---|---|---|---|
| slc | Aye, Nay, Abstain, Absent | Aye, Nay, Abstain, Recuse | no Excused |
| lehi | Aye, Nay, Abstain, Absent | + Recuse | |
| logan | Aye, Nay, Abstain, Absent | Aye, Nay, Abstain | + tally-only blanks |
| nephi | Aye, Nay, Abstain, Recuse, Absent | Aye, Nay, Abstain, Absent | **mostly tally-only** (~80% blank) |
| ogden | Aye, Nay, Abstain, Recuse, Absent | Aye, Nay, Recuse | |
| orem | **Aye, Nay only** | + Abstain | absences/recusals never recorded |
| park_city | all 5 + `Nay (Mayor tie-break)` ×2 | Aye, Nay, Abstain | |
| provo | Aye, Nay, Abstain, Absent | Aye, Nay, Absent | |
| sandy | Aye, Nay, Abstain, Absent | + Recuse, Excused (Legistar) | narrative tallies name only dissenters |
| st_george | all 5 | all 5 | |
| vineyard | Aye, Nay, Recuse, Absent | + (no Abstain anywhere) | |
| west_jordan | all 5 | **Nay, Abstain, Absent only** — PC is tally-only; Ayes never named | |
| west_valley | Aye, Nay, Recuse, Absent | + Abstain | no Excused |
| south_jordan | Aye, Nay, Absent | **Nay, Abstain, Absent only** — PC Ayes never named | mayor uncounted |
| millcreek | Aye, Nay, Abstain, Absent | Aye, Nay, Abstain, Recuse | mayor VOTES (5-member roll); 2017–2021 mostly tally-only (measured 2026-07-06) |
| taylorsville | Aye, Nay, Absent | all 5 minus Excused | mayor does not vote (measured 2026-07-06) |

---

## 5. The relational database (`db/`)

`db/civic.db` (SQLite; legacy filenames `sandy.db`, `lehi.db`, `parkcity.db`) is the
canonical queryable form, built in two idempotent stages —
`python3 db/build_db.py` (exact within-body core) then `python3 db/build_referrals.py`
(reconstructed cross-body referral layer). Each city's `db/SCHEMA.md` is authoritative
for that city; the shared model (mirroring the template, e.g.
`west_valley_city_council/db/SCHEMA.md`):

**Core tables (exact):**

| table | grain | key |
|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE; `kind` ∈ council/commission/agency |
| `person` | one official | `person_id` PK; `name_key` UNIQUE (normalized full name) |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE |
| `application` | one project/matter **within one body** | `application_id` PK; body-scoped `app_key` UNIQUE — 0 applications span >1 body by design |
| `motion` | one motion | `motion_id` PK; FKs to meeting/body/application/mover/seconder; `outcome`/`stage`/`recommendation` CHECK-constrained; `app_match_method` ∈ name/singleton/override (+ sandy's exact `matter_id`) + `app_confidence`; `provenance` ∈ minutes / pmn_roa / pmn_minutes / agendacenter_minutes / wayback_minutes / citysite_minutes / doccenter_draft / packet_carve (recovered-vote origin, §2) |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE; `vote_value` ∈ the §4 vocabulary |
| `role` | person×body service | derived observed span |

**Referral layer (reconstructed, scored, overridable — never conflated with the core):**
`referral` links applications across bodies (`match_method` ∈
address/subject/address+subject/override; `confidence` ∈ high/medium/low; `high`≈exact,
`medium` spot-check before quoting, `low` flagged — do not quote). Corrections via
`db/overrides.csv` / `db/referral_overrides.csv`, then rebuild. Views:
`v_referral_chain`, `v_project_timeline`, `v_member_record`, `v_contested`.

**City extensions:**
- **park_city**: `vote.note` (nullable text) — carries `'Mayor tie-break'` for the 2
  mayoral tie-breaks and `'override: …'` for the 9 contradictory source Aye+Nay pairs
  resolved via `db/vote_overrides.csv`
  (`source_file,motion_no,member,date,claimed_values,resolution,reasoning`). Every
  build prints the reconciliation (CSV rows = db rows + merged overrides).
- **sandy** (conformant since 2026-07-02, plan item 2.6 — the former schema fork is in
  `_backups/2026-07-02/sandy_city_council/db/`): standard core built from the two flat
  CSVs like every city (council minutes-primary — the measured decision and numbers are
  in its `db/SCHEMA.md`; PC votes are Legistar-sourced, their only source). Extensions:
  `app_match_method` adds the value **`matter_id`** (exact Legistar Matter key, used for
  651 motions); the full Legistar API harvest is preserved in **`legistar_*` extension
  tables** (`legistar_body`/`person`/`event`/`matter`/`event_item`/`vote` — 10 bodies,
  2,825 matters, all 10,443 raw vote rows incl. the `Nonvoting` value and the Board of
  Adjustment, cross-linked to the core, never conflated with it). PC `meeting.source_file`
  is the canonical Legistar event URL (no PC minutes exist on disk); its `vote_overrides.csv`
  documents 11 duplicate CSV pairs (8 identical + 3 conflicting, resolved explicitly).

**Reconciliation invariant** (checked by the validator, all cities): named vote rows
in the two flat CSVs = db `vote` rows + documented `vote_overrides.csv` merges
− documented **add-member** override rows. `vote_overrides.csv` rows come in two kinds
(shared `db_build_lib.py`, 2026-07-17): **conflict-resolution** (the member has 2+
contradictory CSV rows — the resolution collapses them to one db vote; the park_city
pattern) and **add-member** (the source printed a garbled/unparseable value the audited
extractor honestly left unrecorded, so the member has NO CSV row — the documented
resolution ADDS the corrected vote to the db only; the flat CSV stays verbatim-faithful;
the SSL Huff `Ye`/`Y/es` pattern). A row that is neither (member already has one clean
recorded value, unknown motion key, or an unconsumed `exclude`) FAILS the build loudly —
stale overrides are never silently ignored.

---

## 6. `weeks/` — derived weekly bundles

`build_weeks.py` buckets every record onto the city's weekly grid: the council
**MEETING_WEEKDAY that ends each council week** (Tue for most cities; park_city and
st_george = Thursday; vineyard = Wednesday — set at the top of each city's script).

```
weeks/
  index.md                every week with counts
  <week-ending-date>/
    summary.md            the narrative entry point (surfaces contested votes; LINKS
                          the week's minutes files via relative paths — minutes are
                          no longer copied into the bundle as of 2026-07-07)
    votes.csv             that week's vote rows (same schema as all_votes.csv)
    comments.csv          that week's public comments (only where a comments corpus exists)
```

Invariants: sum of `weeks/*/votes.csv` rows = council `all_votes.csv` rows; sum of
`weeks/*/comments.csv` rows = `all_comments_clean.csv` rows. weeks/ must be rebuilt
after any change to the canonical CSVs (staleness is a validator check). Never
hand-edit; safe to delete and regenerate.

---

## 7. Provenance requirements

- Every `minutes_index.csv` row carries `source` + `source_url` (known historic gap:
  68 SLC 2020 Laserfiche rows — per-document provenance in `index_laserfiche.csv`).
- **Going forward, every fetch retains the original under `<dataset>/raw/`**
  (REMEDIATION_PLAN.md 3.2). Historic cities that discarded raw minutes PDFs rely on
  `source_url` liveness; backfill is opportunistic.
- Expansion datasets always retain `raw/` plus machine-readable `index.csv` and record
  failures in `unrecovered.csv`.
- Extraction method is documented per dataset in that dataset's `CLAUDE.md`; per-file
  format lives in `minutes_index.csv format`.

---

## 8. NORMALIZATION CONTRACT (cross-city comparability layer)

The following is the normative spec for the normalization layer (REMEDIATION_PLAN.md
2.2–2.4), being implemented concurrently. Validators must tolerate the absence of
these files until that work lands; once present they are checked against this contract
exactly.

- Per city+dataset file `<city>_city_council/<meeting_minutes|planning_commission>/motions_std.csv`, one row per motion, joinable to all_votes.csv on (source, motion_no).
- Columns: source, motion_no, date, body, motion_type_native (verbatim), motion_type_std, land_use_type, action_class, outcome, tally_aye, tally_nay, tally_other, vote_mode, result_raw (verbatim), classify_method, classify_confidence.
- motion_type_std enum: Land-Use | Ordinance | Resolution | Budget | Appointment | Contract-Purchase | Grant-Funding | Interlocal | Ceremonial | Procedural-Administrative | Public-Hearing | Legislative-Intent | Other.
- land_use_type (only when motion_type_std=Land-Use, else blank): Rezone | Text-Amendment | General-Plan-Amendment | Subdivision-Plat | Conditional-Use | Site-Plan-Design-Review | Vacation | Annexation | Variance-Exception | Development-Agreement | Other-Land-Use.
- action_class enum: recommendation | final-action | procedural.
- outcome enum: pass | fail | died | withdrawn | unknown. vote_mode enum: roll-call | voice | unanimous-declared | tally-only | unknown. tally_* integers or blank — parsed only, never inferred beyond the result string + counted member rows.
- classify_method: rule:<id> | crosswalk | manual. classify_confidence: high | medium | low. Unclassifiable → Other + low, never guessed.
- Crosswalk files at repo root crosswalks/: motion_type_crosswalk.csv (city, native_label, motion_type_std), body_crosswalk.csv (city, native_code, canonical_name, description), vote_values.csv (city, value, recorded_meaning, notes/ceilings).

---

## 9. EXPANSION-DATASET INDEX CONTRACTS (2026-07-06, REFACTOR_PLAN Phase 3)

Every expansion dataset's `index.csv` MUST begin with its exact contract header
below, in order. City-specific extra columns are allowed ONLY AFTER the contract
columns (original values preserved verbatim). Blank values are allowed everywhere —
a required column with a blank value means "not recorded", never invented. All 16
cities were migrated to these contracts on 2026-07-06 (renames/reorders/blank-adds
only; originals in `_backups/2026-07-06-refactor/`).

```
packets/          date,title,body,meeting_type,packet_kind,source_url,retrieved_date,
                  format,extraction_method,path
housing_plans/    date,title,doc_type,source_url,retrieved_date,format,
                  extraction_method,path,pages,repository,notes
ordinances/       ordinance_no,adoption_date,date,title,source_url,retrieved_date,
                  format,extraction_method,path,land_use,result,matched_motion_date,
                  matched_motion_no,match_confidence
pmn_backfill/     date,year,title,slug,body,path,source,source_url,notice_url,
                  pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method
transcripts/      date,title,body,video_url,video_id,caption_type,source_url,
                  retrieved_date,format,extraction_method,path
campaign_finance/ date,candidate,office,election_year,filing_type,reporting_period,
                  title,source_url,retrieved_date,format,extraction_method,path
```

Canonical names retired these synonyms (never reintroduce them):
`packet_kind` ← doc_type; `path` ← retained_raw_path; `land_use` ← zoning;
`result` ← motion_result, matched_motion_result; `pmn_file_id` ← file_id, fid;
`pmn_body_id` ← pmn_body; `reporting_period` ← report_period, filing_period.
Election-match columns (`matched_election_candidate`+`join_confidence`,
`candidate_match`, `in_election_results`, `matched_to_results`) carry different
SEMANTICS per city (name vs status vs boolean) and deliberately remain extras —
do not merge them by rename; unifying them requires a value-level re-derivation.

Enforced by `expand-city-sources/scripts/validate_dataset.py` (exact contract
prefix) — run it after touching any expansion `index.csv`.

**Primary-document text-layer columns (2026-07-16, Sandy pilot — standardized
optional TRAILING extensions on `packets/index.csv`):** `doc_class` (controlled
vocabulary: `staff_report` | `member_memo` | `general_plan` | `plan_amendment` |
`development_agreement` | `code_snapshot`; blank = honestly unclassified),
`fetch_status` (CLOSED vocabulary — `ok` | `404`/other HTTP codes | `needs_ocr` |
`oversize` | `no_extractor` | `error:<kind>`; never invent new values), `sha256` (of
the fetched binary, retained after the binary is discarded), `text_path`
(dataset-relative sidecar; when present and the file exists it is the searchable
artifact — the federated search layer prefers it over the stem-named `text/`
convention), `text_chars`. These are the ONE sanctioned case where a raw binary is
fetched, hashed, extracted, and DISCARDED (text-only corpus; public + re-fetchable
via `source_url`; the fetch log is provenance). Normative method + acceptance test:
repo-root `PRIMARY_DOCS_PILOT_SPEC.md`; reference impl `sandy_city_council/packets/`.
Federated as `document.doc_class` + `fts_packet.doc_class`. `extraction_method` on
these rows is honest per-file: `pdftotext`-family for born-digital, `claude_vision`
for vision-transcribed scans (the needs_ocr→ok upgrade path), `section_split` for
section rows (below).

**Section-cut rows (2026-07-16 rollout — for stored monolithic packets whose
sections are separable at high confidence):** additive rows with
`packet_kind=packet_section`, one per cut section of a parent `full_packet`. The
parent row is never mutated. Section rows: `doc_class` per section,
`extraction_method=section_split` (a deterministic line-slice of the parent's
pdftotext sidecar), `text_path` under `text/sections/`, **`sha256` BLANK** (sha256
means binary hash; byte provenance lives on the parent row / fetch log),
`stored_locally=no` (describes the binary), plus city extras AFTER the contract +
pilot columns: `parent_path` (the parent's raw path) and a section identifier
(`appendix_no` / `section_seq`) + `case_key` where the portal has case numbers.
Cutting requires an explicit machine-readable anchor (a TOC manifest or a rigid
per-section template) and a boundary-verification gate — "not separable" is the
honest default (record it in AVAILABILITY.md). Reference impls:
`cottonwood_heights_city_council/packets/` (appendix-TOC) and
`magna_city_council/packets/` (MSD template anchors).

**`election_results/<slug>_races.csv`** (25-col superset, adopted 2026-07-07 —
migrated from three incompatible variants; blank = the county didn't publish it,
never inferred; `total_votes` and `total_first_choice_votes` are SEMANTICALLY
DISTINCT — RCV races carry first-choice only):

```
year,election_type,office,district,contest,contest_verbatim,n_seats,n_candidates,
voting_method,total_votes,total_first_choice_votes,winner,winner_votes,winner_pct,
runner_up,runner_up_votes,margin_votes,margin_pct,registered_voters,ballots_cast,
turnout_pct,uncontested,suppressed_precincts,note,source_file
```

Filenames are slug-consistent (`<slug>_races.csv` / `<slug>_results_by_candidate.csv`
/ `<slug>_results_by_precinct.csv`) — the squashed prefixes (`parkcity_`, `stgeorge_`,
`wjordan_`, `wvc_`) were retired 2026-07-07.

**Cancelled-election certifications (convention adopted 2026-07-17; Utah Code
20A-1-206 lets a municipality cancel an election whose declared candidates don't
exceed the open seats and certify them elected):** such certifications get a races
row so member↔election joins keep working — the certified name in `winner`,
`uncontested=True`, structural columns populated (`n_seats`/`n_candidates`/
`voting_method`), **ALL eleven vote/pct/turnout columns BLANK** (no votes exist —
never fabricate, not even 0), and the `note` column LEADING with the greppable marker
`cancelled_certification (Utah Code 20A-1-206; Res <no>)`; `source_file` points at
the on-disk cancellation instrument (resolution text / minutes). Multi-seat at-large
cancellations put the first certified name in `winner` and every deemed-elected name
in the note. Precedents: magna 2023 D1/D3/D5 (Res 2023-09-02), alta 2025 Mayor+Council
(Res 2025-R-26).

## 10. Conformance checking

`scripts/validate_city.py` implements this spec: layout presence, header conformance,
vote vocabulary, index path existence + date plausibility, source-path existence,
tally-vs-member-row consistency rate, `motions_std.csv` contract conformance (when
present), db reconciliation (honoring `db/vote_overrides.csv`), and weeks/ freshness +
row-sum invariants. Exit code reflects FAILs only; WARNs document known quirks and
soft drift. `scripts/build_coverage.py` regenerates the machine-readable
`coverage.json` manifest from the actual files (never from docs).
