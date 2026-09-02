#!/usr/bin/env python3
"""build_cities_db.py — build the federated cross-city database `cities.db`.

    python3 scripts/build_cities_db.py          # rebuild /…/civic-data/cities.db

cities.db is DERIVED and fully regenerable — never hand-edit it; rerun this
script after ANY per-city db rebuild (it reads whatever is on disk at build
time; the build timestamp is stored in `build_info` and printed).

What it does (stdlib only, idempotent, deterministic):

1. Unions the 8 STANDARD tables (body, person, meeting, application, motion,
   vote, role, referral) from the 16 per-city SQLite dbs, adding a `city`
   column (short slug) to every row.
   * ID NAMESPACING: every per-city integer id (PK and FK alike) is shifted by
     a fixed per-city offset = city_index * 10,000,000 (city_index = 1..16 in
     the scripts/cities.py registry order — the first 13 alphabetical by slug,
     later cities appended so published offsets never shift). The largest
     source id observed repo-wide is ~1.0e6 (sandy's matter_id-derived
     application_ids), so offsets can never collide; all within-city FK
     relationships remain valid unchanged. city = offset // 10,000,000.
   * park_city's `vote.note` extension column is carried through (NULL for
     every other city).
   * sandy's `legistar_*` extension tables (its full Legistar API harvest,
     incl. the `Nonvoting` value and the Board of Adjustment) are EXCLUDED by
     design — query them in `sandy_city_council/db/sandy.db`.
2. Loads every city's `motions_std.csv` files (the SCHEMA_SPEC §8 normalization
   layer) into `motion_std` (city + dataset + the 16 contract columns) and
   joins each row to its `motion` via (source, motion_no, meeting_date) —
   with a (source, motion_no) fallback where that pair is unique on both
   sides. sandy PC's constant provenance string makes (source, motion_no)
   degenerate there (SCHEMA_SPEC §2); the date-disambiguated key handles it.
   Join rates are printed and stored in `build_info`.
2b. COMPUTES `motion_std` for the COUNTY + REGIONAL tier (2026-07-29, TODO
   high (j)) — counties and MPOs publish no `motions_std.csv` and have no
   uniform flat-motion file shape (mag_mpo has no flat motion CSV at all), so
   their rows are derived here from the `motion`/`vote` rows already
   federated, REUSING the classifier and parsers imported from
   `scripts/normalize_motions.py` (never re-implemented, so the tiers cannot
   drift). motion_id is set by construction. The city file-based path above is
   untouched. See compute_motion_std_noncity().
   `ut_state` is EXCLUDED BY DESIGN — see EXCLUDED_FROM_MOTION_STD.
3. Loads the three `crosswalks/*.csv` files as tables
   (motion_type_crosswalk, body_crosswalk, vote_values).
4. Loads the `caveat` table (city, dataset, code, caveat) — the documented
   coverage/recording asymmetries from SCHEMA_SPEC.md / root README caveats /
   root CLAUDE.md quirk lines. Cross-city views LEFT JOIN these so a naive
   query surfaces the caveat text on every affected row (or, for
   v_pc_divergence, excludes non-quotable low-confidence links).
5. Creates the cross-city views: v_contested_all, v_member_record_all,
   v_landuse_outcomes, v_pc_divergence, v_coverage.
6. Prints (and asserts) the row-count reconciliation: for each federated
   table, the per-city row counts must sum EXACTLY to the federated total.

Read-only on every per-city file. Only writes <repo>/cities.db.
"""
import csv
import datetime
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# RENAMED 2026-07-20 (Phase 6): the federated db is gov.db — it spans cities,
# counties, MPOs, and the state, so the old name under-described it. A
# cities.db SYMLINK is maintained after every successful build for
# back-compat (all legacy readers keep working; SCHEMA_SPEC §0 naming).
OUT_DB = os.path.join(ROOT, "gov.db")
LEGACY_LINK = os.path.join(ROOT, "cities.db")
OFFSET_UNIT = 10_000_000

# The ordered city list lives in scripts/cities.py — the single registry every
# repo-wide script imports. Its order IS this build's id-offset order (index+1 =
# the offset multiplier); the append-only rule is documented there.
from entities import ENTITIES, RELATIONSHIPS

# Entities with a per-entity db are "built" and contribute vote-spine rows; today
# that is the 16 cities (fed_index 1..16 — the published offsets), and counties /
# regional bodies / the state as they come online. Order is fed_index order.
BUILT = sorted((e for e in ENTITIES if e.db_rel_path), key=lambda e: e.fed_index)

STD_TABLES = ["body", "person", "meeting", "application", "motion", "vote",
              "role", "referral"]

DDL = """
CREATE TABLE body (
    city        TEXT NOT NULL,   -- entity slug (a city OR a county/regional/state slug)
    gov_level   TEXT NOT NULL,   -- city | county | regional | state
    state       TEXT NOT NULL,   -- ut  (multi-state ready)
    body_id     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    kind        TEXT,
    UNIQUE(city, name)
);
CREATE TABLE person (
    city        TEXT NOT NULL,
    gov_level   TEXT NOT NULL,
    state       TEXT NOT NULL,
    person_id   INTEGER PRIMARY KEY,
    full_name   TEXT NOT NULL,
    name_key    TEXT NOT NULL,
    UNIQUE(city, name_key)
);
CREATE TABLE meeting (
    city         TEXT NOT NULL,
    gov_level    TEXT NOT NULL,
    state        TEXT NOT NULL,
    meeting_id   INTEGER PRIMARY KEY,
    body_id      INTEGER NOT NULL REFERENCES body(body_id),
    meeting_date TEXT NOT NULL,
    title        TEXT,
    source_file  TEXT NOT NULL,
    UNIQUE(city, body_id, source_file)
);
CREATE TABLE application (
    city           TEXT NOT NULL,
    gov_level      TEXT NOT NULL,
    state          TEXT NOT NULL,
    application_id INTEGER PRIMARY KEY,
    app_key        TEXT NOT NULL,
    body_id        INTEGER REFERENCES body(body_id),
    name           TEXT,
    rep_title      TEXT,
    UNIQUE(city, app_key)
);
CREATE TABLE motion (
    city              TEXT NOT NULL,
    gov_level         TEXT NOT NULL,
    state             TEXT NOT NULL,
    motion_id         INTEGER PRIMARY KEY,
    meeting_id        INTEGER NOT NULL REFERENCES meeting(meeting_id),
    body_id           INTEGER NOT NULL REFERENCES body(body_id),
    motion_no         INTEGER NOT NULL,
    motion_text       TEXT,
    motion_type       TEXT,
    result_raw        TEXT,
    outcome           TEXT,
    stage             TEXT,
    recommendation    TEXT,
    disposition       TEXT,
    disposition_method TEXT,
    disposition_confidence TEXT,
    application_id    INTEGER REFERENCES application(application_id),
    app_match_method  TEXT,
    app_confidence    TEXT,
    mover_person_id   INTEGER REFERENCES person(person_id),
    seconder_person_id INTEGER REFERENCES person(person_id),
    names_recorded    INTEGER,
    source_file       TEXT,
    provenance        TEXT
);
CREATE TABLE vote (
    city       TEXT NOT NULL,
    gov_level  TEXT NOT NULL,
    state      TEXT NOT NULL,
    vote_id    INTEGER PRIMARY KEY,
    motion_id  INTEGER NOT NULL REFERENCES motion(motion_id),
    person_id  INTEGER NOT NULL REFERENCES person(person_id),
    vote_value TEXT NOT NULL CHECK (vote_value IN
        ('Aye','Nay','Abstain','Recuse','Absent','Excused',
         'Yea')),  -- 'Yea' = the Legislature's verbatim affirmative (ut_state,
                   -- 2026-07-20 Phase 5); source-faithful values are never
                   -- rewritten, so the federated vocabulary extends instead.
    note       TEXT,           -- park_city extension; NULL elsewhere
    UNIQUE(motion_id, person_id)
);
CREATE TABLE role (
    city       TEXT NOT NULL,
    gov_level  TEXT NOT NULL,
    state      TEXT NOT NULL,
    role_id    INTEGER PRIMARY KEY,
    person_id  INTEGER NOT NULL REFERENCES person(person_id),
    body_id    INTEGER NOT NULL REFERENCES body(body_id),
    first_seen TEXT,
    last_seen  TEXT,
    n_votes    INTEGER,
    UNIQUE(person_id, body_id)
);
CREATE TABLE referral (
    city                    TEXT NOT NULL,
    gov_level               TEXT NOT NULL,
    state                   TEXT NOT NULL,
    referral_id             INTEGER PRIMARY KEY,
    primary_application_id  INTEGER NOT NULL REFERENCES application(application_id),
    primary_body            TEXT,
    related_application_id  INTEGER NOT NULL REFERENCES application(application_id),
    related_body            TEXT,
    match_method            TEXT,
    confidence              TEXT,
    shared_address          TEXT,
    subject_score           REAL,
    primary_date            TEXT,
    related_date            TEXT,
    gap_days                INTEGER,
    note                    TEXT,
    UNIQUE(primary_application_id, related_application_id)
);
CREATE TABLE motion_std (          -- SCHEMA_SPEC §8 normalization layer
    city                TEXT NOT NULL,
    -- CITY rows come from the on-disk motions_std.csv files (dataset = the
    -- directory they live in).  NON-CITY rows are COMPUTED AT FEDERATION from
    -- the loaded `motion` table (2026-07-29) — that tier publishes no
    -- motions_std.csv — and their dataset is BODY-DERIVED, not a directory
    -- path: 'land_use' = the entity's planning commission(s) (the county
    -- analogue of planning_commission) and 'legislative' = the governing body,
    -- its work sessions and the agency boards it sits as (the analogue of
    -- meeting_minutes, which likewise absorbs each city's RDA/MBA).
    -- ut_state contributes NO rows to this table by design — see
    -- EXCLUDED_FROM_MOTION_STD and the ut_state/motion-std-deferred caveat.
    dataset             TEXT NOT NULL CHECK (dataset IN
                            ('meeting_minutes','planning_commission',
                             'legislative','land_use')),
    source              TEXT NOT NULL,
    motion_no           INTEGER NOT NULL,
    date                TEXT NOT NULL,
    body                TEXT,
    motion_type_native  TEXT,
    motion_type_std     TEXT,
    land_use_type       TEXT,
    action_class        TEXT,
    outcome             TEXT,
    tally_aye           INTEGER,
    tally_nay           INTEGER,
    tally_other         INTEGER,
    vote_mode           TEXT,
    result_raw          TEXT,
    classify_method     TEXT,
    classify_confidence TEXT,
    motion_id           INTEGER REFERENCES motion(motion_id)  -- joined; NULL = unmatched
);
CREATE TABLE motion_type_crosswalk (
    city TEXT, native_label TEXT, motion_type_std TEXT, land_use_type TEXT
);
CREATE TABLE body_crosswalk (
    city TEXT, native_code TEXT, canonical_name TEXT, description TEXT
);
CREATE TABLE vote_values (
    city TEXT, value TEXT, recorded_meaning TEXT, notes TEXT
);
CREATE TABLE caveat (
    city    TEXT NOT NULL,   -- slug or '*' (applies to all cities)
    dataset TEXT NOT NULL,   -- meeting_minutes | planning_commission |
                             -- public_comments | election_results | '*'
    code    TEXT NOT NULL,   -- short machine key views join on
    caveat  TEXT NOT NULL
);
-- Elections DB form (2026-07-11, closes REFACTOR_PLAN 5.3).
-- election_race: city-grain race summaries — the uniform 25-col SCHEMA_SPEC §9
-- superset from every city's election_results/<slug>_races.csv, + entity key,
-- gov_level, state, and the containing county (from the relationship graph).
CREATE TABLE election_race (
    city                       TEXT NOT NULL,
    gov_level                  TEXT NOT NULL,
    state                      TEXT NOT NULL,
    county                     TEXT,          -- containing county slug (within edge)
    year                       INTEGER,
    election_type              TEXT,
    office                     TEXT,
    district                   TEXT,
    contest                    TEXT,
    contest_verbatim           TEXT,
    n_seats                    TEXT,
    n_candidates               TEXT,
    voting_method              TEXT,
    total_votes                TEXT,
    total_first_choice_votes   TEXT,
    winner                     TEXT,
    winner_votes               TEXT,
    winner_pct                 TEXT,
    runner_up                  TEXT,
    runner_up_votes            TEXT,
    margin_votes               TEXT,
    margin_pct                 TEXT,
    registered_voters          TEXT,
    ballots_cast               TEXT,
    turnout_pct                TEXT,
    uncontested                TEXT,
    suppressed_precincts       TEXT,
    note                       TEXT,
    source_file                TEXT
);
-- election_result: county-grain SOVC tallies (Salt Lake County today) — one row per
-- contest × candidate, votes summed across precinct + vote-method, from the canonical
-- county canvass (salt_lake_county/elections/). Municipal council/mayor contests only.
CREATE TABLE election_result (
    city              TEXT NOT NULL,   -- county entity slug (e.g. salt_lake_county)
    gov_level         TEXT NOT NULL,
    state             TEXT NOT NULL,
    year              INTEGER,
    election_type     TEXT,
    election_date     TEXT,            -- county-office rows only ('' on municipal rows)
    contest           TEXT,
    jurisdiction_slug TEXT,            -- held city the contest belongs to ('' = other)
    office            TEXT,
    district          TEXT,
    seats             TEXT,
    candidate         TEXT,
    party             TEXT,
    votes             INTEGER,         -- precinct-sum tally (understates under suppression)
    certified_votes   INTEGER,         -- workbook-certified total (county-office rows; NULL = municipal)
    votes_basis       TEXT,            -- exact | certified-over-suppressed | '' (municipal)
    rank_in_contest   INTEGER,         -- plurality rank; RCV finals differ (see caveat)
    n_precincts       INTEGER,
    suppressed        TEXT,
    source_file       TEXT
);
CREATE INDEX idx_erace_city   ON election_race(city);
CREATE INDEX idx_eresult_juris ON election_result(jurisdiction_slug, year);

-- County structured-data layers (2026-07-11, Salt Lake County build). Each loads
-- from a county module's derived CSV; tolerant of absence (other counties add later).
CREATE TABLE development_application (   -- the "development pipeline"
    city            TEXT NOT NULL,       -- county entity slug
    gov_level       TEXT NOT NULL,
    state           TEXT NOT NULL,
    date            TEXT,
    body            TEXT,
    dev_type        TEXT,                -- rezone | planned_development | subdivision_plat | ...
    title           TEXT,
    matter          TEXT,
    location        TEXT,
    outcome         TEXT,
    names_recorded  INTEGER,
    motion_id       INTEGER,             -- federated motion id (join to motion/vote)
    minutes_path    TEXT
);
CREATE TABLE projection (
    city          TEXT NOT NULL,
    gov_level     TEXT NOT NULL,
    state         TEXT NOT NULL,
    geography     TEXT,
    geography_type TEXT,
    year          INTEGER,
    metric        TEXT,
    value         TEXT,
    scenario      TEXT,
    source        TEXT,
    source_url    TEXT,
    vintage       TEXT
);
CREATE TABLE gis_layer (                 -- catalog only (link, never mirror)
    city            TEXT NOT NULL,
    gov_level       TEXT NOT NULL,
    state           TEXT NOT NULL,
    layer           TEXT,
    description     TEXT,
    publisher       TEXT,
    url             TEXT,
    api_endpoint    TEXT,
    format          TEXT,
    vintage         TEXT,
    license         TEXT,
    growth_relevance TEXT,
    notes           TEXT
);
CREATE TABLE regional_project (          -- MPO TIP/RTP/RPO adopted project tables
    city            TEXT NOT NULL,       -- entity slug (wfrc_mpo / mag_mpo)
    gov_level       TEXT NOT NULL,
    state           TEXT NOT NULL,
    plan_kind       TEXT,                -- tip | rtp | rpo
    plan_vintage    TEXT,                -- e.g. '2026-2031', 'RTP2023-2050'
    project_id      TEXT,
    name            TEXT,
    mode            TEXT,
    improvement_type TEXT,
    jurisdiction    TEXT,                -- verbatim; joins to member entities where named
    county          TEXT,
    phase_or_year   TEXT,
    cost            TEXT,                -- numeric where the source is numeric; blank never 0
    status          TEXT,
    description     TEXT,
    source_layer    TEXT,
    source_url      TEXT
);
CREATE TABLE project_vintage (           -- TIP project × vintage observations (derived,
    city            TEXT NOT NULL,       --   <entity>/projects/derived/project_vintage.csv;
    gov_level       TEXT NOT NULL,       --   wfrc_mpo 2026-07-22; mag_mpo when built)
    state           TEXT NOT NULL,
    plan_vintage    TEXT,                -- TIP vintage, e.g. '2026-2031'
    pin             TEXT,                -- UDOT ePM PIN (statewide join key); never blank here
    variant         TEXT,                -- '' normally; '1','2',.. for keep_both-override
                                         --   master-PIN sub-scopes (vintage_overrides.csv)
    name            TEXT,
    county          TEXT,
    in_wfrc_region  TEXT,                -- '1' | '0' | '' (Various/Statewide/unknown)
    forecast_start_year TEXT,
    cost            TEXT,                -- programmed project_value SNAPSHOT, not expenditure
    status          TEXT,
    funding_source_raw TEXT,
    description     TEXT,
    source_layer    TEXT
);
CREATE TABLE project_history (           -- per-PIN TIP lifecycle summary (derived)
    city            TEXT NOT NULL,
    gov_level       TEXT NOT NULL,
    state           TEXT NOT NULL,
    pin             TEXT,
    name_latest     TEXT,
    n_vintages      INTEGER,
    first_vintage   TEXT,
    last_vintage    TEXT,
    vintages        TEXT,                -- pipe-joined, chronological
    entered_tip     TEXT,                -- = first_vintage (left-censored at window start)
    left_censored   TEXT,                -- '1' if first seen in the 2020-2025 window-start vintage
    exited_tip      TEXT,                -- = last_vintage + 1 (the vintage AFTER the pin was
                                         --   last seen); blank if still programmed OR
                                         --   in_wfrc_region!='1'.
                                         -- NOT "first vintage it failed to reappear in" —
                                         -- 24 pins have NON-CONTIGUOUS runs (pin 11268 is in
                                         -- 2020-2025..2024-2029, ABSENT from 2025-2030, then
                                         -- back in 2026-2031) and the two readings differ
                                         -- there. The builder's definition is authoritative;
                                         -- see wfrc_mpo/projects/derived/SOURCES.md:82.
                                         -- (comment corrected 2026-07-26, audit D11)
    first_forecast_year TEXT,
    last_forecast_year  TEXT,
    slip_years      TEXT,                -- last - first forecast year (can be negative)
    first_cost      TEXT,
    last_cost       TEXT,
    cost_drift_pct  TEXT,
    last_status     TEXT,
    statuses        TEXT,                -- pipe-joined chronological distinct
    counties        TEXT,
    in_wfrc_region  TEXT,
    rtp_unique_id   TEXT,                -- exact-name 1:1 match to regional_project rtp row only
    rtp_match_confidence TEXT            -- 'exact_name' | ''
);

-- The entity registry (mirror of registry/entities.csv) + the geography graph
-- (registry/relationships.csv). ALL entities are listed (built or not); the
-- vote-spine rows above exist only for entities that have a per-entity db.
CREATE TABLE entity (
    slug        TEXT PRIMARY KEY,
    name        TEXT,
    level       TEXT NOT NULL,   -- city | county | regional | state
    state       TEXT NOT NULL,
    dir         TEXT,
    db_rel_path TEXT,            -- '' = not yet built (no vote-spine rows)
    fed_index   INTEGER NOT NULL,
    fips        TEXT,
    portal      TEXT,
    gov_form    TEXT,
    notes       TEXT
);
CREATE TABLE entity_relationship (
    entity_a   TEXT NOT NULL,    -- slug (endpoints validated in scripts/entities.py)
    relation   TEXT NOT NULL,    -- within | member_of | overlaps | succeeds
    entity_b   TEXT NOT NULL,
    confidence TEXT,
    note       TEXT
);
CREATE TABLE build_info (key TEXT PRIMARY KEY, value TEXT);

CREATE INDEX idx_motion_meeting  ON motion(meeting_id);
CREATE INDEX idx_motion_app      ON motion(application_id);
CREATE INDEX idx_motion_city     ON motion(city);
CREATE INDEX idx_vote_motion     ON vote(motion_id);
CREATE INDEX idx_vote_person     ON vote(person_id);
CREATE INDEX idx_std_city        ON motion_std(city, dataset);
CREATE INDEX idx_std_motion      ON motion_std(motion_id);
"""

# ---------------------------------------------------------------------------
# CAVEATS — documented coverage/recording asymmetries. Sources: SCHEMA_SPEC.md
# §4 (vote-value ceilings), root README.md "Coverage caveats", root CLAUDE.md
# per-city quirk lines, coverage.json, crosswalks/README.md. city='*' /
# dataset='*' = applies everywhere. Views join on `code`.
# ---------------------------------------------------------------------------
CAVEATS = [
    # --- WFRC project-lifecycle layer (derived 2026-07-22, WFRC-native Phase 1)
    ("wfrc_mpo", "project_history", "tip-window",
     "TIP lifecycle is observed only within the 8 retained vintages "
     "2020-2025..2027-2032. entered_tip is LEFT-CENSORED at the window start "
     "(left_censored='1' rows may have entered earlier); last_vintage = "
     "2027-2032 means still programmed, not completed."),
    ("wfrc_mpo", "project_history", "statewide-2020",
     "The 2020-2025 TIP vintage is STATEWIDE-inclusive. Rows with "
     "in_wfrc_region!='1' carry no exit semantics — exited_tip is blank by "
     "construction (a statewide project vanishing from later WFRC-only "
     "vintages is a scope change, not a project exit)."),
    ("wfrc_mpo", "project_vintage", "cost-snapshot",
     "cost is the programmed project_value snapshot per vintage, NOT "
     "expenditure or obligation. RTP costs (different basis, base-year $) are "
     "not in this table. Obligated dollars exist only in the Federal "
     "Obligation Report documents (FFY 2023-2024 — complete as published)."),
    ("wfrc_mpo", "project_history", "pin-only",
     "Lifecycle derivation covers PIN-carrying rows only; pin-null TIP rows "
     "(OID-fallback in regional_project) are excluded and counted in the "
     "build report. TIP<->RTP linkage is exact-name 1:1 only "
     "(rtp_match_confidence='exact_name'); unlinked is the honest default."),
    # --- regional (MPO) entities are DATA-FORWARD, not vote-forward (2026-07-20)
    ("wfrc_mpo", "*", "regional-model-note",
     "WFRC is a data-forward regional entity: its analytic center is "
     "regional_project (TIP funded projects across 8 vintages + RTP-2050) and "
     "projection (city-area pop/HH/jobs, annual 2019-2050), NOT the vote spine. "
     "Council/committee minutes are tally-only by source (mover/seconder named; "
     "dissent is COUNT-only, dissenters never named; vote table empty by "
     "construction). The motion layer is an adoption/certification record — "
     "never use it for per-member vote analytics."),
    ("mag_mpo", "*", "regional-model-note",
     "MAG is a data-forward regional entity: analytic center = regional_project "
     "(TIP/RTP/RPO) + projection (city grain) + the Housing Unit Inventory / "
     "Wasatch Choice GIS catalog, NOT the vote spine. MPO Board/TAC minutes are "
     "tally-only (mover/seconder named; no roll-call table ever — vote table "
     "empty by construction). Divided votes are RARE (5 Fail in 12 years) and "
     "where one occurs the clerk sometimes prints the count and even dissenter "
     "names IN THE RESULT SENTENCE — preserved verbatim in result_raw (G8a "
     "2026-07-31), not parsed to vote rows. The MPO Board is UTAH-COUNTY-only: "
     "summit_county/park_city belong to MAG's AOG/RPO side and never vote on "
     "the MPO Board."),
    # --- named-vote / dissent recording limits (affect contested/member views)
    ("nephi", "meeting_minutes", "tally-only",
     "Nephi votes are mostly tally-only (~80% of rows carry no member name; only "
     "~51 council motions name voters). Per-member and dissent analysis is limited "
     "to the small named subset — dissent on unnamed motions is invisible here."),
    ("orem", "*", "vote-ceiling",
     "Orem records Aye/Nay only (council; PC adds Abstain) — absences and recusals "
     "are never in the minutes. Orem's 'perfect attendance' is a recording artifact."),
    ("west_jordan", "planning_commission", "dissent-only",
     "West Jordan PC names only dissenters/absentees — zero named Ayes. Counted "
     "member rows understate participation; use stated tallies (motion_std tally_*)."),
    ("sandy", "meeting_minutes", "dissent-only",
     "Sandy narrative tallies name only dissenters (the assenting majority is "
     "honestly unnamed on many motions); counted Ayes < stated tally by design."),
    ("provo", "meeting_minutes", "dissent-only",
     "Provo minutes frequently name only dissenters/absentees (tally cross-check "
     "90.4%); counted Ayes < stated tally by design."),
    ("south_jordan", "meeting_minutes", "dissent-only",
     "South Jordan narrative tallies name only dissenters/absentees; the assenting "
     "majority is honestly unnamed (0 named-Aye by design on unanimous motions) — "
     "counted Ayes < stated tally. Full tabular roll calls appear only 2024-12+."),
    ("south_jordan", "meeting_minutes", "mayor-vote",
     "South Jordan's Mayor is non-voting on ordinary council motions (max tally 5, "
     "the 5 district members only) EXCEPT one recorded statutory tie-break "
     "(2025-06-17, Ordinance 2025-09, 3-2) — the sole 6th-voter event, stored "
     "faithfully as Dawn R. Ramsey | Aye. Do not treat Ramsey as a routine voter."),
    ("south_jordan", "meeting_minutes", "body-note",
     "South Jordan's RDA + MBA are IN-MEETING bodies (the council recesses and "
     "convenes them in-session); body ∈ {Council 1007, RDA 21, MBA 1}. No separate "
     "RDA/MBA minutes exist to acquire — the in-meeting captures are complete."),
    ("south_jordan", "planning_commission", "dissent-only",
     "South Jordan PC names only dissenters/abstainers/absentees — ZERO named Ayes "
     "anywhere in the PC record (the west_jordan-PC pattern). A per-member rate over "
     "SJ PC rows measures dissent visibility, not voting behavior; use stated "
     "tallies (motion_std tally_*). (Re-filed from meeting_minutes 2026-07-31 — the "
     "mis-filed dataset key left v_member_record_all PC rows uncaveated.)"),
    ("millcreek", "meeting_minutes", "mayor-vote",
     "Millcreek's Mayor VOTES on ordinary council motions (max council tally 5, "
     "unlike most cities where the mayor is non-voting) — Ayes/Nays can include the "
     "mayor. Do not assume a 5-vote body is mayor-excluded here."),
    ("millcreek", "meeting_minutes", "tally-only-partial",
     "Millcreek named roll-call is reliable only ~2022+; 2017-2021 minutes are "
     "largely tally-only (no member names). 2017 specifically is an extraction-format "
     "gap (tabular en-dash roll calls the extractor didn't parse — ~380 all-Aye rows "
     "recorded as tally-only; safe-direction undercapture, recoverable — TODO F-1). "
     "Pre-2022 per-member/dissent analysis is limited."),
    ("millcreek", "meeting_minutes", "body-note",
     "Millcreek's CRA (Community Reinvestment Agency) is an IN-MEETING body (the "
     "council convenes it in-session); CRA 'Board Member'/'Chair' synonyms resolve to "
     "the same council people. No separate CRA minutes to acquire."),
    ("millcreek", "election_results", "election-format-note",
     "Millcreek elections use Ranked-Choice Voting (2021, 2023); 2025 mayor was "
     "appointed (not elected) and 2023 had a cancelled-uncontested race. RCV/appointed/"
     "cancelled outcomes are election-only properties — margins are not standard "
     "plurality margins."),
    ("taylorsville", "meeting_minutes", "mayor-nonvote",
     "Taylorsville's Mayor is an executive and NON-voting (max council tally 5); the "
     "presiding Chair is one of the 5 council members (rotates), not a 6th voter."),
    ("taylorsville", "meeting_minutes", "body-note",
     "Taylorsville's RDA (Redevelopment Agency) is an IN-RECORD body (convened within "
     "the council record); no separate RDA minutes to acquire."),
    ("taylorsville", "planning_commission", "vote-format-note",
     "Taylorsville PC votes appear in 3 distinct minute formats across the record "
     "(format normalized on extraction). Mid-2025+ minutes are RICOH OCR scans "
     "(text-layer quality lower)."),
    ("taylorsville", "meeting_minutes", "ocr-note",
     "Taylorsville recent minutes (mid-2025+) are RICOH OCR scans rather than "
     "born-digital text — OCR-noise possible; PMN clean-text upgrade is a pending "
     "follow-up."),
    ("taylorsville", "*", "geo-precinct-derived",
     "Taylorsville has no official council-district GIS layer; address→district is "
     "DERIVED from precinct × district-contest rows (post-2020 vintage). Boundary "
     "assignments near precinct edges are approximate."),
    ("logan", "meeting_minutes", "tally-only-partial",
     "Logan has a substantial tally-only (no-name) vote share from narrative minutes."),
    ("west_valley", "meeting_minutes", "tally-only-partial",
     "West Valley has 524 tally-only voice votes beside 1,223 named roll-calls."),
    ("vineyard", "*", "vote-ceiling",
     "Vineyard never records Abstain (any dataset); absence of abstentions is a "
     "recording limit, not behavior."),
    ("park_city", "meeting_minutes", "tie-break-note",
     "Park City's 2 mayoral tie-break Nays carry vote.note='Mayor tie-break'; 9 "
     "contradictory source Aye+Nay pairs were resolved via db/vote_overrides.csv "
     "(note LIKE 'override:%')."),
    # --- coverage floors / gaps
    ("slc", "meeting_minutes", "coverage-floor",
     "SLC votes are 2021+ only (2020 minutes are OCR; not vote-extracted)."),
    ("provo", "planning_commission", "coverage-floor",
     "Provo PC dataset is 2025+ only (source limit)."),
    ("st_george", "meeting_minutes", "coverage-note",
     "St George 2020-21 minutes are PMN backfill (Revize archive holds 2022+); one "
     "2025-10-09 work meeting unrecoverable (city published the wrong file)."),
    ("ogden", "meeting_minutes", "body-gap",
     "Ogden's separate 2022 and 2023 RDA/MBA meeting sets were never acquired "
     "(~20-25 RDA + ~5-8 MBA meetings missing per year). Ogden RDA coverage = 2021 "
     "in-meeting transitions + 2024-26 separate meetings."),
    ("sandy", "meeting_minutes", "body-gap",
     "Sandy publishes no separate RDA minutes (its RDA acts in closed session inside "
     "council meetings) — 1 RDA vote row is genuinely all there is."),
    # --- county vote-recording ceilings (2026-07-25 audit, _audits/2026-07-25/) ---
    # These are the mechanism that stops cross-entity mis-comparison for the non-city
    # tier: without them v_member_record_all / v_contested_all return county rows with
    # an EMPTY record_caveats column, so a "who dissents most" query ranks a tally-only
    # county's few named dissenters against cities with full rolls.
    ("summit_county", "*", "tally-only-partial",
     "Summit County is TALLY-PRIMARY. Council motions name mover+seconder and print a "
     "tally; individual members are named only when a division is called (23 of 1,831 "
     "council motions). Both Planning Commissions name voters on divided motions only "
     "(282 of 1,571). Unanimous motions are tally-only BY SOURCE — a blank member/vote "
     "is the recording ceiling, not a gap. Never read named rows as a full roll."),
    ("summit_county", "*", "vote-ceiling",
     "Summit County motions carry NULL disposition (see the disposition-coverage "
     "caveat — the classifier runs for the 31 cities plus cache_county and mag_mpo "
     "only) and the pre-2023 Council era is scanned/unbuilt (460 dates ledgered in "
     "legislative/minutes_unrecovered.csv). Council coverage starts 2023-01."),
    ("utah_county", "*", "vote-ceiling",
     "Utah County's source names full rolls 2015-2019 and is TALLY-PRIMARY 2020+ "
     "(mover/seconder + tally; members named mainly when a vote divides — dissent "
     "nameable throughout). The two extractor bugs found by the 2026-07-25 audit were "
     "REPAIRED the same day (motions 10,089->11,218, member-votes 2,765->4,705, "
     "contested 31->84, named divided votes in every year 2019-2026 — record: "
     "utah_county/db/REPAIR_2026-07-25.md). Honest residual ceiling: 42 of 63 "
     "2020-2024 parenthetical roll blocks remain uncaptured (OCR-fragmented) and "
     "several 2020+ persons are surname-only. Per-member analytics are fullest "
     "2015-2019; post-2019 named rows skew toward divided votes."),
    ("weber_county", "*", "tally-only-partial",
     "Weber County prints NAMED roll calls on ~99.6% of motions 2015+ (richer than most "
     "counties). The 21 formerly image-only copier-scan minutes documents were OCR'd "
     "and ingested 2026-07-26, closing the 2021/2023 scan gaps — rows sourced from "
     "them carry OCR-era text quality (provenance-filterable)."),
    ("cache_county", "*", "tally-only-partial",
     "Cache County splits at 2021. 2021+ is born-digital with FULL named rolls (every "
     "member's Aye/Nay on every motion). 2015-2020 was OCR'd 2026-07-26 and now contributes "
     "1,505 TALLY-ONLY motions: mover, seconder and a numeric tally are named, individual "
     "members are NOT (a source recording ceiling, names_recorded=0, blank member/vote). So "
     "per-member analytics are valid 2021+ ONLY; a 2015-2026 member time series will "
     "silently understate the early years. Movers/seconders in that era are often "
     "SURNAME-ONLY (White, Yeates, Potter, Robison, Merrill) because the narrative prose "
     "gives no first name — not merged with any 2021+ person without evidence."),
    ("washington_county", "*", "vote-ceiling",
     "Washington County is DB-LESS BY DESIGN (LIGHT+ tier): the vote layer and the "
     "development pipeline are explicitly DEFERRED, not missing. Its canonical layers are "
     "elections (2018-2025) + the minutes FTS corpora + plans/ordinances/gis. Absence of "
     "motions/votes for this county is an honest property, not a coverage gap."),
    ("juab_county", "*", "vote-ceiling",
     "Juab County is DB-LESS BY DESIGN (CHEAP-ONLY tier): no legislative/land_use/plans "
     "modules were built, so it contributes elections + projections + a GIS catalog only "
     "(hence 0 rows in fts_minutes and document). Its 2019/2021 municipal election cycles "
     "are an HONEST GAP — dead on all three official channels, never inferred."),
    ("ut_state", "*", "disjoint-persons",
     "State legislators are a DISJOINT person population (222 persons). NEVER join them "
     "to municipal officials by surname — verified 0 cross-level vote rows and 0 name_key "
     "collisions. Legislative roll calls are FULL NAMED votes (27,887), which makes this "
     "the one tier where per-member analytics are exact; do not blend those rates with "
     "municipal tally-only bodies."),
    ("ut_state", "*", "vote-ceiling",
     "The ut_state layer is a 264-bill LAND-USE/HOUSING SUBSET of 2015-2026, not the full "
     "Legislature. 378 motions are voice votes with names_recorded=0. Bill selection is a "
     "title-based classifier, so recall is a ceiling, not a census."),
    # --- non-city motion_std: computed at federation (2026-07-29, TODO high (j))
    # Before this date motion_std was EMPTY for the whole non-city tier, so
    # v_coverage returned 0 rows for all 9 non-city entities and no normalized
    # cross-TIER comparison was possible. These rows are now computed here (see
    # compute_motion_std_noncity) rather than from a motions_std.csv — the tier
    # has no uniform flat-motion file shape. The caveat each entity carries is
    # the honest CLASSIFICATION CEILING: what share of its motions the source
    # text leaves genuinely unclassifiable (Other / confidence='low').
    # Scoped by DATASET, not by city: 'legislative'/'land_use' are exactly the
    # non-city motion_std datasets, so a ('*', <that dataset>) row attaches to
    # every non-city motion_std row and to no city row.
] + [
    ("*", _ds, "motion-std-computed-tier",
     "motion_std rows for the county and regional (MPO) tier are COMPUTED AT "
     "FEDERATION (2026-07-29) from the `motion` table, not read from a "
     "motions_std.csv — that tier publishes no such file (and mag_mpo has no flat "
     "motion CSV at all). Same classifier as the 31 cities (imported from "
     "scripts/normalize_motions.py), so the columns mean the same thing; motion_id "
     "is set by construction, so the non-city join rate is 100% BY DEFINITION and "
     "is NOT evidence of extraction quality. `dataset` here is BODY-DERIVED, not a "
     "directory: land_use = the entity's planning commission(s), legislative = the "
     "governing body + work sessions + the agency boards it sits as. Per-entity "
     "confidence mixes: build_info key motion_std_computed:<slug>. THE STATE TIER "
     "IS NOT IN THIS LAYER — ut_state motion_std is intentionally empty (see the "
     "ut_state/motion-std-deferred caveat).")
    for _ds in ("legislative", "land_use")
] + [
    ("salt_lake_county", "*", "motion-std-classification-ceiling",
     "Salt Lake County's Legistar native motion_type is an AGENDA-SECTION heading "
     "('Discussion Items', 'Tax Letters', 'Consent Item'), not a subject type, so "
     "classification runs on the item title alone: 35.6% of motions land on "
     "Other/low (honest no-signal, e.g. 'To approve application #31089 as "
     "presented'). Land-Use share is therefore a FLOOR, not a census."),
    ("utah_county", "*", "motion-std-classification-ceiling",
     "Utah County publishes an EMPTY native motion_type on 100% of motions, so "
     "every classification comes from the motion text alone; 42.0% land on "
     "Other/low. Its motion text is also frequently truncated mid-phrase ('...as "
     "specified in Regular Agenda Item No. 3'), which is where much of that share "
     "comes from. Read alongside this entity's vote-ceiling caveat."),
    ("weber_county", "*", "motion-std-classification-ceiling",
     "Weber County publishes an EMPTY native motion_type on 100% of motions, but "
     "its minutes carry full narrative motion sentences, so classification is the "
     "richest in the non-city tier: only 8.6% Other/low."),
    ("cache_county", "*", "motion-std-classification-ceiling",
     "Cache County publishes an EMPTY native motion_type on 100% of motions and "
     "its motion text is a short verb phrase ('approve the agenda as written'), "
     "often truncated; 27.7% land on Other/low."),
    ("summit_county", "*", "motion-std-classification-ceiling",
     "Summit County's native motion_type is a real 8-value vocabulary, so 66.6% of "
     "motions classify high-confidence; 18.9% are Other/low. Its 'Board of "
     "Equalization' label (property-tax valuation appeals) maps to NO "
     "motion_type_std bucket by design — those motions classify from text only."),
    ("wfrc_mpo", "*", "motion-std-classification-ceiling",
     "WFRC's native motion_type is the motion VERB ('Approval', 'Adoption', "
     "'Endorsement') — it says what was done, never to what — so classification "
     "runs on text alone; 26.2% land on Other/low. NOTE the tier framing: an MPO's "
     "analytic surface is regional_project + projection, not motions; its Council "
     "minutes are tally-only (vote table empty by source), so vote_mode here is "
     "'unanimous-declared'/'unknown' on essentially every row."),
    ("mag_mpo", "*", "motion-std-classification-ceiling",
     "MAG publishes an EMPTY native motion_type on 100% of motions and its board "
     "motions are about programming and funding requests rather than land-use "
     "matters, so 61.1% land on Other/low — the highest honest no-signal share in "
     "the tier, and a real property of MPO business, not an extraction failure. "
     "Same tier framing as WFRC: projects + projections are the analytic surface."),
    ("ut_state", "*", "motion-std-deferred",
     "ut_state has NO motion_std rows AT ALL, and that is the INTENDED STATE, not "
     "a gap (owner ruling 2026-07-29, when the county+MPO tier got this layer). "
     "The municipal motion_type_std vocabulary (Land-Use | Ordinance | Resolution "
     "| Budget | Appointment | Contract-Purchase | …) does not describe "
     "LEGISLATIVE BILL VOTES: the unit here is a bill STAGE (committee report, "
     "2nd/3rd reading, concurrence), not a motion on a matter, so action_class "
     "(recommendation | final-action | procedural) has no legislative meaning "
     "either; motion_text is the bill SHORT TITLE on only ~41% of rows and a stage "
     "fragment ('House/ circled', 'House/ floor amendment') on the rest; and the "
     "corpus is a 264-bill LAND-USE/HOUSING SUBSET BY CONSTRUCTION, so any "
     "Land-Use share computed over it would measure the acquisition filter, not "
     "the Legislature. The problem is STRUCTURAL, not just classification: "
     "ut_state has zero purpose-built tables in gov.db and its 264 BILLS sit in "
     "`application`, the slot meant for municipal development applications — "
     "compare wfrc_mpo, which was incorporated on its own terms with four "
     "first-class tables (regional_project, project_vintage, project_history, "
     "projection). The state tier is to be reevaluated and reintegrated the same "
     "way. Tracking: TODO 'STATE TIER — reevaluate how `ut_state` is integrated, "
     "ON ITS OWN TERMS (owner ruling 2026-07-29)'. Until then use the ut_state "
     "`motion`/`vote` rows "
     "directly — 1,208 named roll calls and 27,887 NAMED legislator votes, the "
     "most exact vote layer in the repo — and never blend them with municipal "
     "tally-only bodies (see the disjoint-persons and vote-ceiling caveats)."),
    # --- normalization-layer caveats (affect motion_std-based views)
    ("ogden", "meeting_minutes", "outcome-unknown",
     "126 ogden council motions have outcome=unknown ('Recorded' — OCR-garbled "
     "narrative outcomes; honest unknowns). Only city below 97% outcome coverage."),
    ("ogden", "meeting_minutes", "landuse-undercount",
     "428 ogden council ordinance-adoption motions read only 'ORDINANCE WAS PASSED "
     "AND ADOPTED AS ORDINANCE 20xx-N' — the land-use subject lives in un-captured "
     "agenda headings, so ogden council Land-Use share (1.3%) is an undercount; "
     "ogden PC (36.7%) is representative."),
    ("st_george", "*", "no-hearing-motions",
     "St George's extractor captured no open/close-public-hearing motions (0.0% "
     "Public-Hearing) — a recording difference vs vineyard/slc/ogden, where every "
     "hearing motion is its own vote row."),
    ("nephi", "planning_commission", "text-quality",
     "Nephi PC motion text is frequently truncated mid-word and has footer bleed "
     "(known extractor limitation) — 13.5% honest Other/low classifications."),
    ("sandy", "planning_commission", "degenerate-source-key",
     "Sandy PC votes come from the Legistar API, not minutes: `source` is a constant "
     "staging string, so (source, motion_no) is degenerate — motion identity needs "
     "(source, motion_no, date). Items are titles, not motion phrasing."),
    # --- 2026-07-31 back-fill: the 15-city SLCo wave + lehi carried ZERO caveat
    # rows (the table was maintained for the original 16 + counties/MPOs and never
    # extended), so v_member_record_all ranked tally-only/dissent-only cities with
    # an EMPTY caveat column (e.g. magna dissent-only rows read as 73% nay rates).
    # Sources: each city's CLAUDE.md + root CLAUDE.md quirk lines; several spot-
    # verified against gov.db by _audits/2026-07-31-publication-review/.
    ("alta", "*", "tally-only-partial",
     "Town of Alta (~380 pop) is SPARSE BY DESIGN (~12 meetings/yr): 4 at-large + "
     "VOTING mayor (max tally 5). The PC is 100% tally-only and council naming is "
     "irregular — per-member analytics rest on a small named subset."),
    ("alta", "election_results", "election-format-note",
     "Alta's 2021 municipal results were privacy-suppressed by the county, and the "
     "2025 municipal election was CANCELLED under Utah Code 20A-1-206 "
     "(uncontested) — absence of 2025 contest rows is the election not happening, "
     "not a gap."),
    ("emigration_canyon", "meeting_minutes", "tally-only-partial",
     "Emigration Canyon (~1.6k pop) is a narrative-tally council: most motions "
     "print a tally without member names (mover/seconder named). 5 at-large incl. "
     "a peer-selected VOTING mayor (max roll 5). Data floor 2017; PMN purged the "
     "earliest blobs (recovered floor 2018-10)."),
    ("copperton", "*", "tally-only-partial",
     "Copperton (~800-pop town) is SPARSE BY DESIGN; township->TOWN 2024 with a "
     "voting Mayor/Chair in both eras. Votes are almost entirely tally-only; the "
     "PC cancels most meetings. Floor 2017 with a GENUINE 2017-02..2018-06 PMN "
     "purge gap."),
    ("kearns", "meeting_minutes", "dissent-only",
     "Kearns narrative tallies name only dissenters — the assenting majority is "
     "honestly unnamed; counted Ayes < stated tallies. Township->city seam "
     "2024/2026 (city era: 4 districts + VOTING mayor). Floor 2017; 2017-mid-2018 "
     "PMN blobs purged (honest gap)."),
    ("magna", "meeting_minutes", "dissent-only",
     "Magna is a narrative-tally council with DISSENT-ONLY naming (split votes "
     "carry named dissenters; unanimous motions are tally-only) — a per-member "
     "rate over magna rows measures dissent visibility, not behavior. ⚠ The "
     "presiding officer's vote FLIPS at the 2024 HB35 seam: the township "
     "Chair-titled-Mayor VOTED; the 2026+ elected executive mayor does NOT. 11 "
     "no-result-printed motions carry NULL outcome. Floor 2017 (early PMN purge)."),
    ("white_city", "meeting_minutes", "tally-only-partial",
     "White City council minutes span three vote-grammar eras; most rows are "
     "tally-only. Voting Chair/Mayor in both township and city eras (max 5). "
     "Data floor 2017 (full history for a 2017-incorporated entity)."),
    ("white_city", "planning_commission", "tally-only",
     "White City PC minutes (MSD 'Meeting Minute Summary' form, PMN body 5879) "
     "name mover/seconder only — no per-member rolls exist in the source."),
    ("cottonwood_heights", "meeting_minutes", "vote-format-note",
     "Cottonwood Heights results are word-form prose ('Passed 4-to-1'; failed "
     "tallies print nays-first) deliberately unparsed by the tally regex — use "
     "motions_std for tallies; clerk-error tallies are retained verbatim. 4 "
     "districts + VOTING mayor (max 5); in-session CDRA."),
    ("midvale", "meeting_minutes", "ocr-note",
     "Midvale 2020-21 minutes are OCR (the 'Gouncil' roll-dropout era) — some "
     "roll calls degraded; otherwise a high-attribution named-roll city. 5 "
     "districts + tie-break-only mayor; in-session RDA."),
    ("riverton", "planning_commission", "tally-only-partial",
     "Riverton PC names members ONLY on divided votes — unanimous motions are "
     "tally-only (hundreds of rows). Named PC rows therefore skew heavily toward "
     "contested items. Council: 5 districts + tie-break-only mayor; D3<->D4 were "
     "renumbered at the 2022 redistricting — join on person, not district number."),
    ("bluffdale", "meeting_minutes", "mayor-vote",
     "Bluffdale's mayor is tie-break-only in Council but VOTES as Chair in the "
     "in-session RDA/LBA (rolls of 6 there). 5 at-large. 2023-26 minutes carry a "
     "partial-OCR seam."),
    ("bluffdale", "election_results", "election-format-note",
     "Bluffdale 2021 was an RCV pilot (stored first-choice tallies — winner_pct "
     "is not a final-round margin). The city straddles Salt Lake + Utah counties "
     "(the Utah Co. part is unpopulated Camp Williams)."),
    ("draper", "election_results", "election-format-note",
     "Draper is all-at-large (5 + non-voting mayor, 1 tie-break) and straddles "
     "Salt Lake + Utah counties (SLCo administers its elections). 2021 was an RCV "
     "pilot — stored first-choice tallies; don't read winner_pct as a final "
     "margin. The 2025 4-year 2-seat council race was CANCELED as uncontested "
     "(Res #25-49; Lowery + Green seated without a vote) — its election_race row "
     "carries the canceled-uncontested convention with NO vote totals (added "
     "2026-08-01; the SOVC never printed the contest)."),
    ("herriman", "meeting_minutes", "mayor-vote",
     "Herriman: 4 districts + VOTING mayor (max roll 5); in-session "
     "CDRA/HCSEA/HCFSA agency bodies appear via the body column."),
    ("holladay", "meeting_minutes", "vote-format-note",
     "Holladay results are prose (use motions_std for tallies). 5 districts + "
     "VOTING mayor (rolls reach 6); in-session RDA + LBA."),
    ("holladay", "planning_commission", "person-ambiguity",
     "A bare-surname person 'Layton' exists (2020-2022 votes) that CANNOT be "
     "disambiguated between TWO Laytons serving simultaneously — Chair Howard "
     "Layton and Commissioner Chris Layton, both real, both printed in e.g. the "
     "2022-05-16 minutes. Surname-only source rows; never merge without evidence."),
    ("holladay", "planning_commission", "coverage-note",
     "Holladay PC 2020 H1 + 2021 H1 minutes are Wayback-recovered "
     "(provenance='wayback_minutes'); 2020 H2 / 2021 H2 / 2023 PC minutes are "
     "GENUINE gaps (dead on every channel; ledgered in minutes_unrecovered.csv)."),
    ("murray", "meeting_minutes", "tally-only-partial",
     "Murray voice votes are tally-only. 5 districts + non-voting executive "
     "mayor. The 2023 council-minutes loss and the post-2022-11 PC gap were "
     "CLOSED 2026-07-16 via PMN promotion (provenance-filterable); only PC "
     "2025-04-17 / 2025-07-17 remain minute-less."),
    ("lehi", "meeting_minutes", "coverage-note",
     "Lehi's council minutes publishing LAPSED after 2026-01-27 (~19-21 Granicus "
     "meetings with no minutes; every public channel exhausted — GRAMA is the "
     "only remaining path). Post-Jan-2026 lehi council coverage is "
     "agenda/video-only, an external publishing gap, not an extraction one."),
    ("south_salt_lake", "meeting_minutes", "coverage-note",
     "SSL: 119 recorded minutes 2022-2026 were recovered 2026-07-16 from the "
     "CivicPlus ArchivedMinutes slot (provenance='agendacenter_minutes'); the "
     "residual ~214 genuinely-unpublished dates are mostly council WORK meetings "
     "(precise ledger in COVERAGE.md). 5 districts + 2 at-large + non-voting "
     "executive mayor (rolls of 7)."),
    # --- disposition coverage (2026-07-31): the derived disposition column is
    # computed for the 31 cities + cache_county + mag_mpo ONLY. Attached to the
    # non-city motion_std datasets so any tier-wide disposition query surfaces it.
] + [
    ("*", _ds, "disposition-coverage",
     "The derived `disposition` column is computed for all 31 cities plus "
     "cache_county and mag_mpo ONLY; salt_lake_county, summit_county, "
     "utah_county, weber_county, wfrc_mpo (and ut_state) carry NULL on every "
     "motion. A disposition-filtered query across the non-city tier returns "
     "cache+mag rows alone — the other entities' NULLs mean not-yet-computed, "
     "NOT honestly-unclassifiable (that state is disposition IS NULL in cities).")
    for _ds in ("legislative", "land_use")
] + [
    # --- campaign finance coverage (2026-07-31): previously the cf_* tables had
    # ZERO caveat rows, so the two absent cities were invisible to any money query.
    # (county caveats rewritten 2026-08-02 after the vision-totals tranche: every county's
    # stated-totals layer now federates into cf_filing; itemized + cf_cycle remain limited.)
    ("*", "campaign_finance", "cf-coverage",
     "The campaign-finance layer spans TWO tiers. Cities: structured dollar layer in 29 of "
     "31 (slc ABSENT — portal blocked; draper acquired-but-unstructured — see their rows). "
     "Counties (added 2026-08-01, vision-totals tranche completed 2026-08-02): all 8 "
     "county datasets federate their per-filing STATED TOTALS into cf_filing (salt_lake "
     "971 · utah 265 · cache 239 · washington 206 · summit 131 · wasatch 111 · weber 98 · "
     "juab 27 rows). ITEMIZED donor/vendor rows (cf_contribution/cf_expenditure) exist for "
     "the county tier from salt_lake_county's EasyVote 2022/2024/2026 API data, its "
     "clerk-legacy era, its **2015-2021 PAPER slice (closed 2026-08-23, 130/130 filings, "
     "6,028 rows — the only slice populating `donor_occupation`)**, juab's 3 "
     "transcribed 2020 filings, and — since the 2026-08-02 born-digital sweep — "
     "reconciliation-gated parser rows in weber/cache/summit/wasatch/utah/washington "
     "(geometry-anchored; the scanned remainder is NOT itemized). washington's "
     "machine-readable era was RE-PARSED AND CLOSED 2026-08-23: 3,256 rows over 101 of its "
     "102 born-digital filings, superseding the 489-row 2026-08-02 slice — see its "
     "cf-itemized-machine-readable row — while its 100 handwritten cover forms stay a "
     "vision queue. An empty itemized layer means NOT TRANSCRIBED, never "
     "'no donors'. CYCLE ROLLUPS NOW EXIST FOR BOTH TIERS (2026-08-23): cf_cycle is "
     "CITY-ONLY (805 rows / 29 cities) and cf_cycle_county is the COUNTY tier (968 "
     "candidate-cycles over all 8 counties, 618 publishing a figure and 350 honest GAP "
     "rows) — DIFFERENT MEASUREMENTS, see the cf-cycle-tiers row before comparing them, and "
     "v_cf_cycle_all if you want both in one query. NEVER sum cf_filing dollar columns; for "
     "county money read each county's cf-* caveat row + campaign_finance/AVAILABILITY.md "
     "first."),
    ("*", "campaign_finance", "cf-cycle-tiers",
     "TWO CYCLE TABLES, TWO DIFFERENT MEASUREMENTS — do not rank one against the other "
     "without reading both. cf_cycle is CITY-ONLY: max(latest summary, summed interims) of "
     "stated totals, with NO carryover concept, no governing-filing provenance and no gap "
     "rows; its `basis` column (summary | sum-interim | single | max-mixed | override) is "
     "the whole story. cf_cycle_county is the COUNTY tier, derived per candidate-cycle from "
     "THAT CYCLE'S OWN PRINTED ARITHMETIC: it carries `regime` (per-period | cumulative | "
     "*-single | undetermined), a SEPARATED `carryover_opening` that is never folded into "
     "the raised figure, `is_floor`=1 where the published number is a provable LOWER BOUND "
     "rather than a total, `chain_closes` (the balance-chain proof), `governing_filings` "
     "(every figure is reproducible from exactly those filings), and GAP ROWS with a "
     "`gap_reason` where the filings establish no total. A blank raised_gross is a GAP, "
     "never zero. The view v_cf_cycle_all unions the two deliberately and carries this "
     "caveat on every row; it EXCLUDES gap rows (a gap is not a total), so ask coverage "
     "questions of cf_cycle_county itself. ⚠ NEVER SUM A RESTATING LEDGER OR A CUMULATIVE "
     "SNAPSHOT: for a cumulative-regime cycle the county figure is the LATEST governing "
     "report, never a sum of the candidate's filings — summing summit's David R. Brickey "
     "2014 gives 32,400.00 where the truth is 16,800.00."),
    ("*", "campaign_finance", "cf-cycle-county-method",
     "cf_cycle_county METHOD AND ITS HONEST CEILINGS (COUNTY_CYCLE_REDUCER_SPEC.md, built "
     "2026-08-23). Stated totals from cf_filing are PRIMARY — the filer's own printed "
     "figures, complete for all 8 counties back to 2006. The BALANCE CHAIN is the resolver: "
     "filings link when one's beginning balance equals the previous one's ending balance, "
     "and a cycle earns tier A only when BB(first) + ΣC − ΣE = EB(last) closes within $0.51. "
     "That proof resolves markerless amendments with no heuristic (SLCo Rosie Rivera 2022: "
     "nine filings, five labelled 'April 5' with mutually inconsistent totals, chain to "
     "142,340.79). Regime is decided PER CANDIDATE-CYCLE from its own arithmetic; each "
     "county's documented form prior is a TIE-BREAK ONLY and can only ever confirm, never "
     "decide — so washington's per-period template does not stop a cumulative-filling filer "
     "being classified cumulative, and SLCo's per-period prior does not stop DeBry 2022. "
     "Tiers: A 102 (chain closes, every filing placed) · A-superseded 57 (chain resolved "
     "orphan amendments, all named in excluded_filings) · B 281 (cumulative — the latest "
     "non-superseded report, per each county's own rule) · C 178 (arithmetically coherent "
     "but unproved; mostly is_floor) · GAP 350. 618 of 968 candidate-cycles publish a "
     "figure. 200 published rows carry is_floor=1 — A LOWER BOUND, NEVER A TOTAL. "
     "raised_net_of_carryover is BLANK for every cumulative cycle by owner ruling "
     "(2026-08-23): the opening-balance column's semantics is not stable across filings "
     "(weber Froerer 2022's cumulative contributions cell equals BB + this-period, while his "
     "2018 final carries a last-report CONTRIBUTIONS figure beside a BALANCE opening), so "
     "one blanket subtraction would be wrong on one of them. Carryover is real and large: "
     "159 published cycles open with a non-zero balance totalling ~$1.70M (SLCo Winder "
     "Newton 2022 opens at 215,160.87 having raised 61,084.62). Balance-chain closure over "
     "multi-filing cycles: utah 67% · salt_lake 50% · cache 20% · weber 13% · washington 9% "
     "· summit/wasatch 0% (they print NO beginning balance at all — 0 of 131 and 0 of 111 — "
     "so no chain is constructible and their cycles rest on the cumulative rule). The "
     "itemized cross-check is ADVISORY and NEVER gates or corrects a stated total; where "
     "only some governing filings are itemized the check declares itself not-comparable. "
     "Empty itemized anywhere in the county tier means NOT TRANSCRIBED, never 'no donors'. "
     "DERIVED — regenerate with `python3 scripts/campaign_finance/cycle_totals_county.py "
     "--all`; corrections go in <county>/campaign_finance/cycle_overrides_county.csv, never "
     "as edits to the CSV."),
    ("salt_lake_county", "campaign_finance", "cf-county-eras",
     "SLCo county-office CF has three source eras. Since 2026-09-01 EVERY DOCUMENT THE "
     "COUNTY HOLDS IS ITEMIZED — the remaining gap is ACQUISITION (251 online-filed "
     "2015–2021 reports, GRAMA-only), not transcription. "
     "(1) Legacy clerk PDFs ~2006–2015: 547 filings, stated totals for all 547 (496 with a "
     "Summary Page, 51 without) and ITEMIZATION CLOSED 2026-08-03 — 496/496, 22,871 rows; "
     "the only gaps inside it are 8 sides across 5 filings that state a non-zero total but "
     "filed no schedule page (~$121k contributions / ~$120k expenditures). "
     "(2) The 2015–2021 era, in two slices with two different fates. Its PAPER slice is "
     "ACQUIRED AND FULLY TRANSCRIBED — harvested 2026-08-20 from the clerk page's "
     "globalassets URL family and closed 2026-08-23 by wave W1: **130 of 130 filings, 717 "
     "pages, 6,028 rows (3,422 contributions + 2,606 expenditures)**, every row "
     "geometry-anchored except 284 whose pointers were deliberately WITHDRAWN (values intact; "
     "a rotated attachment whose row grid could not be independently confirmed — the "
     "calibration suite's 'frame corrected OR geometry withheld' rule). 244 sides transcribed, "
     "16 `none`, **ZERO withheld, ZERO amounts blank for illegibility**; 212 of 226 sides that "
     "have a printed anchor reconcile EXACTLY, 14 carry a delta traced to a named page of the "
     "filer's own arithmetic. Period figures observed: $2,163,611.66 in / $1,726,036.30 out — "
     "**NEVER sum these across filings** (interims, year-ends and amendments overlap by "
     "design). This slice is the ONLY place `donor_occupation` is populated (2,292 of 3,422 "
     "contribution rows): its Schedule A pre-prints an Occupation/Employer column no other "
     "era has, captured verbatim under the 2026-08-20 owner decision. ⚠ TWO SEMANTIC TRAPS "
     "CARRIED PER ROW IN NOTES: (i) a **SCHEDULE-SCOPE SPLIT** on 5 filings, where the "
     "schedule's printed total and the Summary figure measure DIFFERENT THINGS (in-kind "
     "included vs excluded, or cumulative vs per-period) — those rows publish BOTH figures "
     "with `reconciles_*` deliberately BLANK, because comparing figures of different scope is "
     "a basis error, not a delta; and (ii) at least one filer (DeBry) puts the CUMULATIVE in "
     "Summary Column A with the period figure only at lines 4/6, so his `stated_*` are not "
     "comparable to other filers'. **The scope test must be run PER PAGE** — the same filer "
     "flips convention between his original and his amendment. "
     "The other slice, **251 online-filed reports, remains GRAMA-ONLY** because the county "
     "disclosure portal APPLICATION IS DEAD (re-probed 2026-08-20: not WAF-blocked — a real "
     "browser gets the same connection reset; last Wayback 200 was 2026-01-15; the report "
     "route is /Search/PublicSearch/Report/{id}, never crawled). The two slices are "
     "COMPLEMENTARY: 34 of the 54 portal filers have no clerk-page PDF at all, so this "
     "transcription does NOT make the GRAMA unnecessary. "
     "⚠ ONE DUPLICATE PAIR: `2020_…_burdick-fin-report-3.pdf` is a SECOND SCAN of the "
     "Schedule B sheet inside `…amendment-burdick-fin-report-9-15-20_redacted.pdf` (identical "
     "rows, identical printed grand total 9,533.28, identical stray pencil line; the PDFs are "
     "sha256-DISTINCT because the embedded rasters differ by one pixel row). Both are "
     "published as their own filings — **summing the pair double-counts $9,533.28**. "
     "(3) EasyVote 2022–2026 — CLOSED 2026-09-01 by wave W2. 442 documents: 197 itemized "
     "from the API (2022 26 · 2024 104 · 2026 67) after the 2026-08-20 office-gate repair, "
     "and THE ROW-LESS RESIDUE IS NOW TRANSCRIBED. The queue was DERIVED, not counted — "
     "every EasyVote filing whose document_id has no rows in the advanced-search API: 240 "
     "filings = 238 transcribed + 2 ledgered OUT OF SCOPE (Fife-Jepperson AE07FEF8 / "
     "D20522DA, whose Office Sought line reads 'Salt Lake School Board' — verified at the "
     "cover 2026-09-01; her 2026 filing B5AB014E is correctly IN scope because its Office "
     "Sought reads 'Salt Lake County Council District 2'. Classify by OFFICE SOUGHT, never by "
     "the top-row Office, which carries the filer's current seat). Wave W2 delivered "
     "18,240 rows (11,852 contributions + 6,388 expenditures), 100% pct:-geometry-anchored, "
     "and 141 previously-missing covers, so filing_totals went 971 -> 1,112 and every "
     "EasyVote document now has both halves it can have. Per SIDE over 240 filings (480 "
     "sides): 359 exact · 33 delta-with-cause traced to a named page · 82 `none` (no such "
     "schedule page) · 2 unknown (no anchor exists in the document) · 4 out-of-scope. "
     "ZERO sides withheld. 78 contribution amounts are blank BY SOURCE, not by omission: 77 "
     "on Wilson-Jennifer B5D1F91C, whose county bar spans the Amount column on pp.3 and 6 "
     "(the filing's C side is a documented FLOOR — 114,980.00 readable against a stated "
     "161,699.85), and 1 on Wilson CE8EF5B5 where the filer printed no amount. "
     "Provenance: rows carry extract_method 'vision-itemized/W2 EasyVote residue "
     "(2026-08-24; kimi-k3)' — this is the FIRST non-Claude transcription in gov.db; 658 of "
     "the 18,240 rows were finished by a claude-opus-5 resumption of three killed chunks and "
     "say so in the same string. The wave was verified before federation (gates re-run, "
     "byte-identical rebuild, frozen pre-wave blocks proved unchanged, four filings "
     "re-read at the page). "
     "⚠ donor_occupation IS NO LONGER PAPER-SLICE-ONLY: the EasyVote forms and filer "
     "attachments print an Occupation/Employer column too, so 10,225 of the W2 rows carry "
     "one (repo total 12,517). Blank still means the form has no such field, the filer left "
     "it empty, or it was redacted — the row note says which. "
     "⚠ SOME EXPENDITURE AMOUNTS ARE NEGATIVE AS PRINTED (Morris-Rachelle's bank/ledger "
     "exports; Liewer 585D94D0): the sign is kept verbatim per filing, reconciliation is on "
     "MAGNITUDE, and `itemized_expend_sum` is published positive. A consumer summing "
     "cf_expenditure.amount for this county must take the absolute value — the same "
     "convention already present in the clerk-legacy McAdams/Winder rows. "
     "So donor-level questions are answerable for 2006–2015, for the 2015–2021 PAPER slice, "
     "and for the WHOLE EasyVote 2022–2026 era; they remain UNANSWERABLE only for the 251 "
     "GRAMA-only online reports of 2015–2021, which are now the county's ONLY acquisition "
     "gap. A query spanning eras still measures PUBLICATION, not fundraising. Semantic traps "
     "carried per-row in notes: at least two filers (DeBry, Gill 2007) put CUMULATIVE figures "
     "in the per-period column; 48 legacy filings check no report-type box (filing_type "
     "honestly blank); 16 decimal-comma currency repairs are named in notes. Donor geography "
     "in the EasyVote era is redacted AT SOURCE (a county black bar over the address cell "
     "takes city/state/ZIP with it) — blank donor_city/donor_state there is redaction, not "
     "filer silence."),
    ("utah_county", "campaign_finance", "cf-totals-tier",
     "265 filing_totals rows 2008–2026 (all covers vision-read; regime PER-PERIOD — "
     "cumulative YTD columns kept in notes, NEVER summed as increments; a candidate-cycle "
     "total is the sum of the per-period rows, cross-checked against the last report's ytd_*) "
     "— BUT an AMENDMENT RESTATES ITS ORIGINAL'S PERIOD rather than adding one, so filter on "
     "the amendment= marker in notes before summing: Buhman 2014 files an original and its "
     "amendment inside ONE PDF, both stating 15,209.58, and summing them double-counts the "
     "candidate. 7 offices honestly unresolved; 62 filing_date blanks; 89 school-board filings "
     "ledgered out of scope; 3 channel errors documented (wrong year ×2; one filing "
     "mis-attributed by the county API; one clerk name-drift Bird→Baird) — join on "
     "source_filing, NEVER on the channel's candidate label. ITEMIZED LAYER IS COMPLETE FOR "
     "THE SCANNED CORPUS: 245 of 245 handwritten filings vision-transcribed in wave B2 "
     "(2026-08-18/20; queue closed 2026-08-20) plus the 2 born-digital filings of 2026-08-02 "
     "— 2,884 contribution + 3,629 expenditure rows over 247 reports, 100% "
     "pct:-geometry-anchored, every frame proved by rendering it back off the page. "
     "extraction_confidence is medium/low ONLY, never high on a scan. AN EMPTY ITEMIZED SIDE "
     "IS NOT 'NO DONORS': 90 sides are empty-schedule (the page exists, the filer entered "
     "nothing) and 15 are no-schedule-page (the document has no such page) — DIFFERENT FACTS. "
     "ZERO sides withheld. RECONCILIATION: 342 of 389 transcribed sides close EXACTLY on the "
     "promoted per-period cell; 34 are FILER-ARITHMETIC deltas retained verbatim (a "
     "reconciles_*=False is the FILER's arithmetic, never a transcription-defect claim, and "
     "each carries a traced explanation in notes); 11 sides are cumulative-exact — the "
     "schedule restates the WHOLE CYCLE and sums exactly to the cover's CUMULATIVE cell, so "
     "reconciles_* is left BLANK (unknown), not True, because that is a DIFFERENT SCOPE from "
     "the figure this module publishes and comparing them is a basis error. recon_delta_* is "
     "likewise blank unless the transcriber recorded it: it is NOT derivable as (itemized − "
     "stated), because a delta side's anchor need not share the promoted cell's scope (Ewell "
     "2024 — cumulative schedule, Box D prints 0, derivation gives 2,729.23 where the page "
     "shows 119.27). needs_review rides 1,394 rows but is dominated by BLANK FILER DATES "
     "(1,292); only 102 rows are flagged for a reading concern. Donor city/state only, never "
     "street addresses."),
    ("weber_county", "campaign_finance", "cf-totals-tier",
    "98 filing_totals rows 2012–2026, regime CUMULATIVE (cycle figure = latest "
    "non-superseded report, never a sum; two superseding re-files flagged in notes; "
    "officeholder carryover inflates cumulative totals — Harvey 2024 opens from his 2020 "
    "closing). 33 county-published interim filings (2018/2020) are LOST everywhere — "
    "those cycles carry FINAL-report figures only, no within-cycle timing. ITEMIZED LAYER "
    "IS COMPLETE: 98 of 98 filings (1,360 contribution + 1,256 expenditure rows) — 5 "
    "born-digital parsed by `weber_polimorphic` (2026-08-02, single-entry family fix "
    "2026-08-14) plus all 93 handwritten scans vision-transcribed in wave B2 "
    "(2026-08-14/17/18; queue closed 2026-08-18). 100% pct:-geometry-anchored (2,616 of "
    "2,616 rows), every re-measured frame proved by rendering it back off the page; the 18 "
    "geometry withdrawals of 2026-08-17 are RESOLVED and none stands. Filter by "
    "extract_method before comparing eras (`weber_polimorphic/text` high vs "
    "`vision-itemized` medium). 134 of 149 transcribed sides reconcile EXACTLY to a figure "
    "the filing itself prints; 15 are filer-arithmetic deltas retained verbatim — a "
    "reconciles_*=False is the FILER's arithmetic, never a transcription-defect claim. 26 "
    "sides are honest empty-schedule (page exists, filer entered nothing) and 11 are "
    "no-schedule-page (the document has no such page) — DIFFERENT facts, and neither is "
    "'no donors'. ZERO sides withheld. RECONCILIATION-BASIS RULE (owner-ratified "
    "2026-08-17): a side reconciles against the printed cover figure matching ITS OWN "
    "SCOPE — This-Report for a period ledger, Cumulative for a cumulative one; no figure "
    "is EVER derived by differencing covers. 71 sides publish on the PERIOD basis with "
    "is_incremental=True (601 contribution + 432 expenditure rows), so on those rows "
    "itemized_*_sum is ONE REPORTING PERIOD and sits far below stated_total_* BY DESIGN — "
    "the notes name both figures and comparing them is a basis error. One period claim "
    "stays an honest UNKNOWN (Harvey 2024: Form A prints 24,300.00 but the cover's line-1 "
    "This-Report cell is blank, unresolvable between 24,300 and 24,000) — reconciles_contrib "
    "blank, never asserted. IN-KIND IS PER FILER, NOT A FORM PROPERTY: the form says to "
    "include it and most filers do, but Gochnour 2016 EXCLUDES it (7 monetary rows = the "
    "printed 3,500.00; in-kind-inclusive 8,153.00 matches nothing printed), so "
    "build_finance.py tests both conventions and names the one that closed — on that filing "
    "itemized_contrib_sum reports all published rows (6,826.00) while the reconciliation is "
    "against 3,500.00. Zero-glyph ruling (owner 2026-08-02): a glyph DENOTING zero "
    "transcribes as 0; a bare dash is a NIL MARK and stays blank (weber's 10 dash balances "
    "are the calibration suite's own negative control). Two cover figures were CORRECTED "
    "from primary evidence (Combe 2012 line 1 + balance; the Gibson 2026 SWAPPED cover pair "
    "76c91f61/8a163a02) — see AVAILABILITY.md §9b. filing_regime CUMULATIVE is carried in "
    "the module docs."),
    ("cache_county", "campaign_finance", "cf-totals-tier",
     "239 filing_totals rows 2008–2026 (vision pass closed the handwriting floor: 234 "
     "county_confirmed offices, 5 blank ON THE FILING; 210/212 stated figures). "
     "ITEMIZED LAYER IS COMPLETE FOR EVERY DOCUMENT THE COUNTY HOLDS (queue closed "
     "2026-08-24): 176 of 176 un-itemized DISTINCT DOCUMENTS transcribed from page images, on "
     "top of the 21 born-digital filings parsed 2026-08-02 — 756 contribution + 1,466 "
     "expenditure rows over 179 filings, 100% pct:-geometry-anchored, ZERO sides withheld. "
     "The queue was derived at the DOCUMENT grain, not the row grain: 239 index rows are 197 "
     "distinct sha256, so ONE transcription is applied to every index row sharing those bytes "
     "and a naive row count over-counts by the duplicate factor. "
     "is_incremental varies PER FILING and is decided from WHICH printed cell the rows equal "
     "(filing_regime is NULL in db — regime lives in the module docs). "
     "⚠ THREE THINGS AN EMPTY ITEMIZED SIDE CAN MEAN, never 'no donors': the schedule page "
     "exists and is blank or struck out (an honest zero), the PDF has NO schedule page at all "
     "(33 sides — several filings are a cover-only one-page scan), or the filer states a "
     "figure his own schedule never itemizes. "
     "Of 352 sides: 282 EXACT against a printed figure, 26 filer-arithmetic DELTAS published "
     "verbatim with reconciles_*=False and needs_review=1 on every row, 44 UNKNOWN where the "
     "document prints no anchor of any scope (a bare dash or a blank cell is BLANK, never 0). "
     "⚠ TWO DUPLICATE CLASSES, and sha256 only sees the first: 42 index rows are byte-identical "
     "cross-channel copies, AND 26 filings are the SAME REPORT RE-SCANNED with different bytes "
     "(flagged CONTENT-DUPLICATE in notes). Count each report ONCE on both."),
    ("summit_county", "campaign_finance", "cf-totals-tier",
     "131 filing_totals rows 2014–2026 (every ballot candidate covered; regime CUMULATIVE; "
     "the form's Current|Last|Cumulative column order is REVERSED vs the parsed cities' "
     "sheet — anti-transposition audit recorded in AVAILABILITY.md, 17 samples exact). "
     "ITEMIZED LAYER IS COMPLETE: 131 of 131 filings — 11 born-digital parsed by "
     "summit_form (105+386 rows) plus 116 of 116 scans vision-transcribed (1,193+1,407 "
     "rows, 100% pct:-geometry-anchored; queue closed 2026-08-17). Filter by "
     "extract_method before comparing eras (`summit_form/text` high vs "
     "`vision-itemized/summit-scan` medium). A reconciles_* of False on a vision row is "
     "the FILER's arithmetic, not a defect (32 side-flags). RECONCILIATION-BASIS RULE "
     "(owner-ratified 2026-08-17): a side reconciles against the printed cover figure "
     "matching ITS OWN SCOPE — Current Report for a period ledger, Cumulative for a "
     "cumulative one; no figure is EVER derived by differencing covers. 16 sides (81 "
     "rows) are published on the PERIOD basis with is_incremental=True, so on those rows "
     "itemized_*_sum is ONE REPORTING PERIOD and sits far below stated_total_* BY DESIGN "
     "— the notes name both figures. 5 sides remain withheld (1250 amount column off the "
     "scan; 1268 contrib and 4278 expend where neither printed figure closes; 12943 "
     "contrib and 12944 expend blank pages with no gate) — never 'no donors'. "
     "filing_regime NULL in db (module docs carry it). Reports are CUMULATIVE snapshots "
     "— never sum a candidate's filings. Zero-glyph ruling (owner 2026-08-02): "
     "slashed-zero marks transcribe as 0.00 (7 cells across 6 filings promoted, verbatim "
     "Ø kept in the caches); dashes/N-A/empty stay blank."),
    ("washington_county", "campaign_finance", "cf-totals-tier",
     "206 filing_totals rows 2006–2025 at the LOGICAL-FILING grain (one filing spans up to "
     "3 files: Summary+Contributions+Expenditures — 409 files behind 206 filings). 195 "
     "stated totals; wrapped/'Various'-dated ledgers are WITHHELD from counted sums unless "
     "provably complete. ⚠ THE LEDGERS RESTATE THE WHOLE CYCLE TO DATE while the summary "
     "prints ONE DEADLINE PER ROW, so cf_contribution/cf_expenditure rows carry "
     "is_incremental=False and A CYCLE TOTAL IS THE LATEST FILING'S LEDGER, NEVER A SUM OF "
     "ROWS: the 1,518+1,738 published rows restate only 676 distinct donations and 758 "
     "distinct payments. One portal-anchor disagreement kept verbatim (Gardner Dec-2012); "
     "113 index rows carry medium/low office confidence (not individually document-verified)."),
    ("washington_county", "campaign_finance", "cf-itemized-vision-era",
     "THE HANDWRITTEN ERA IS CLOSED TOO (vision wave 2026-08-24): all 100 image-faced "
     "17-16-6.5 cover forms transcribed from page images — 530 contribution + 778 expenditure "
     "rows, 100% pct:-geometry-anchored, ZERO sides withheld, 0 amounts blank for illegibility. "
     "Of 200 sides: 173 EXACT against a printed figure, 12 filer-arithmetic DELTAS published "
     "verbatim (reconciles_*=False, needs_review=1 on the side), 15 UNKNOWN where the form "
     "prints no anchor of any scope, and 1 document carries NO Form A page at all. "
     "⚠ SCOPE IS PER FILING HERE, NOT PER COUNTY: 127 sides sum to the cover's CUMULATIVE "
     "column (is_incremental=False) and 64 to its THIS-REPORT column (is_incremental=True) — "
     "the latter is a DIFFERENT SCOPE from the cumulative figure this module publishes in "
     "stated_*, so those sides leave reconciles_* BLANK and that is not a failure. "
     "⚠ FORM 'A' ITEMIZES ONLY CONTRIBUTIONS OVER $50; the cover's line-2 aggregate of $50-and-"
     "under is NEVER itemized, so the rows are scored against LINE 1, not against "
     "stated_total_contributions (which publishes line 1 + line 2). "
     "19 PDFs staple SEVERAL reports; their rows carry the report they belong to, line_no is "
     "renumbered across the document to keep (source_filing, line_no) unique, and the filing "
     "leaves reconciles_* blank with a per-report verdict in notes. "
     "Also corrected in the same wave: 36 index.csv candidate names that were tesseract noise "
     "are now the name read off the page (candidate_determinations.csv, evidence quoted)."),
    ("washington_county", "campaign_finance", "cf-itemized-machine-readable",
     "ITEMIZED COVERAGE IS THE MACHINE-READABLE ERA ONLY, and it is CLOSED there "
     "(parser tranche 2026-08-23). Queue derived from index.csv: of 409 files / 206 "
     "filings, 106 filings (309 files) are machine-readable — 102 born-digital "
     "Summary+ledger sets of the 2010–2015 generations plus 4 ledger-only 2008 postings — "
     "and 100 filings are image-faced handwritten cover forms (95 index format='scanned' "
     "PLUS 5 whose index format says 'text' because a stamped transmittal note carries the "
     "only text layer). ALL 102 sets were parsed: 1,518 contribution + 1,738 expenditure "
     "rows over 101 filings, cycles 2010/2012/2014, 34 filers, 9 offices, 100% "
     "geometry-anchored (2,659 real .xls cell refs + 597 pct: boxes measured from "
     "`pdftotext -bbox-layout` word coordinates). 204 sides: 57 sum EXACTLY to the figure "
     "in stated_total_* (reconciles_*=True); 63 are CUMULATIVE-SCOPED — they sum exactly "
     "to the summary sheet's own column read down to that deadline, a DIFFERENT SCOPE from "
     "the single printed row this module publishes, so reconciles_* is honestly BLANK "
     "(utah_county's cumulative-exact precedent; treating blank as failure is a basis "
     "error); 42 are filer-arithmetic DELTAS published verbatim with reconciles_*=False, "
     "recon_delta_* deliberately blank and needs_review=1 on every row; 41 are honest "
     "empty schedules; 1 side is WITHHELD (Cory Pulsipher 2010-04-06 contributions — the "
     "county's export prints '$5,00.00', which is never repaired, so the parse is provably "
     "short). NOT itemized and NOT attempted here: the 100 handwritten cover-form filings "
     "(2006 + 2016–2025) — a future vision wave, ledgered in AVAILABILITY.md — and the 4 "
     "2008 ledger-only postings, whose column header prints once and re-lays out per page "
     "with no total to prove completeness against. Empty itemized = NOT TRANSCRIBED, never "
     "'no donors'."),
    ("juab_county", "campaign_finance", "cf-partial-structured",
     "27 filing_totals rows (2010/2014/2020 only — the county stopped uploading to the "
     "state system after 2020 and adopted a local disclosure ordinance only 2024-10; "
     "2012/2016/2018/2022/2024/2026 are publication gaps, GRAMA lead filed). "
     "ITEMIZATION IS COMPLETE as of 2026-08-14: all 27 filings carry Form A/B donor "
     "and vendor rows (187: 46 contributions + 141 expenditures), vision-transcribed "
     "from image-only scans (zero born-digital text in this county) with pct: geometry "
     "per row. 34 of 48 sides reconcile EXACTLY to a figure the form prints; 3 carry a "
     "filer-arithmetic delta named on the page (Carlton-2010 ±0.10 both sides, "
     "Lofgran-2014 +50.00, Painter-2014 −1,025.57 = a prior report the state never "
     "uploaded); 9 sides have NO schedule page in the document — 8 of them all-zero "
     "filings, the ninth Garrett-2014's absent Form A ($250.00 stated, unitemizable). "
     "An empty itemized side is now one of TWO documented facts, never 'no donors': a "
     "blank page that was read (7 real zeros) or a page that does not exist. WARNING: "
     "stated_total_contributions is the form's line 1 (>$50, itemized) PLUS line 2 "
     "(<=$50 aggregate, never itemized), so reconciles_contrib=False on Sperry-2010, "
     "Sperry-2014, Lofgran-2014 and Walker-2010 is a BASIS difference, not a defect — "
     "see the filing's notes. Never sum filing_totals across a candidate's filings; "
     "these forms are cumulative."),
    ("wasatch_county", "campaign_finance", "cf-totals-tier",
     "111 filing_totals rows 2010–2026 + 851 ITEMIZED rows (346 contributions / 505 "
     "expenditures over 73 filings; tranche 3 Phase B 2026-08-14 — all 111 filings have "
     "an itemized layer and 0 sides are WITHHELD). THREE form variants with a clean "
     "2022→2024 cycle-boundary seam: the two older sheets are CUMULATIVE (2020's "
     "three-reports-per-candidate: take December, never sum), the 2024+ sheet is "
     "period-scoped — but three filers restate cumulatively on it anyway (flagged in "
     "notes; regime is per CANDIDATE, not per form). RECONCILIATION IS ANCHOR-DEPENDENT: "
     "reconciles_* is measured against the PUBLISHED stated total, and False there is "
     "usually NOT a missing donor — Carr-sheet contributions gate on cover LINE 1 "
     "(line 2 is an unitemized <=$50 aggregate with no donor rows by form design), a "
     "cumulative-sheet schedule may gate on the THIS REPORT column, and in-kind "
     "exclusion is per FILER; the real anchor and cause are in "
     "vision/<key>.json._meta.itemized.recon. 168 sides exact, 20 carry a verbatim "
     "filer delta (Koson 2010 wrote the contributor COUNT in a dollar cell). 38 filings "
     "publish no row and that is THREE facts: 26 blank-but-present schedule pages (real "
     "zeros), 9 cover-only PDFs with no schedule page at all (non-existence, not zero), "
     "3 mixed. 5 of 12 2024 general reports unrecoverable on any channel; county "
     "publication begins 2018."),
    ("slc", "campaign_finance", "cf-honest-zero",
     "Salt Lake City's CF layer holds ONLY the 2003 cycle (10 Wayback-recovered Recorder "
     "filings — structured 2026-08-02, extended 2026-08-14 when the IA interstitial "
     "cleared the 2 blocked filings: 248 contributions + 176 expenditures, all sides "
     "reconciled or honestly unknown, geometry-anchored; Dale_Lambert is the one "
     "permanent 2003 gap). Everything after 2003 is "
     "absent: 2005–2017 was published in a POST-only app never archived (GRAMA-"
     "recoverable — the city's DB is provably alive), and the 2019+ JSON portal "
     "(dotnet.slcgov.com) has been down/blocked "
     "since acquisition (2026-07). Any cross-city money-vs-votes design that "
     "assumes SLC coverage will silently return nothing. Re-harvest is a WATCH "
     "in LEADS.md."),
    ("draper", "campaign_finance", "cf-unstructured",
     "Draper's campaign finance is ACQUIRED but UNSTRUCTURED: filings (mostly "
     "scanned) sit in campaign_finance/raw/ + index.csv with no "
     "contributions/expenditures/cycle layer, so draper is absent from cf_cycle. "
     "Structuring is queued in LEADS.md."),
    ("kearns", "campaign_finance", "cf-blocked-cycles",
     "Kearns 2023 (EasyVote auth-gated) and 2025 city-era (Cloudflare-blocked; "
     "filings proven to exist) CF cycles are acquisition-blocked — kearns money "
     "totals cover the acquired cycles only."),
    ("slc", "planning_commission", "dual-direction-recommendation",
     "One 2025-05-28 PC motion recommends APPROVAL for one right-of-way segment "
     "and DENIAL for another in a single motion; the stored recommendation "
     "('Negative') follows the clerk's own result label ('Negative recommendation "
     "7:2') while disposition reads the motion's leading approve verb — the one "
     "adjudicated, documented disagreement left by the 2026-08-01 "
     "recommendation-oracle pass (56 contradictions -> this 1). Dual-direction "
     "motions carry both directions verbatim in motion_text; read it."),
    # --- datasets that exist outside cities.db but shape cross-city claims
    ("*", "public_comments", "comments-two-cities",
     "Public comments are substantive in only 2 of 31 cities: SLC (13,334) and Park "
     "City (459). Slivers: st_george 136, orem 95, provo 81, lehi 42, west_jordan 28, "
     "millcreek 27 (in-packets harvest). The other 24 cities are honest zeros or "
     "submit-only records, documented per city in public_comments/AVAILABILITY.md. "
     "Never compare 'public engagement' across cities on this data. (Comments ARE "
     "federated — `comment` table + `fts_comment`; the per-city public_comments/ "
     "CSVs remain canonical.)"),
    ("millcreek", "public_comments", "comments-in-packets",
     "Millcreek publishes resident comments inside PC agenda packets (Provo-style "
     "IN-PACKETS); the structured harvest was BUILT 2026-07-19 — all_comments_clean.csv "
     "carries the verbatim resident letters (source='agenda_packet'). HONEST FLOOR: "
     "only letters bundled in RETAINED packets are captured; unretained "
     "?packet=true land-use packets with comment appendices are unharvested (LEADS.md)."),
    ("taylorsville", "public_comments", "comments-honest-zero",
     "Taylorsville publishes no separate public-comment record — its empty "
     "all_comments_clean.csv is an honest zero, not a gap."),
    ("*", "election_results", "elections-2019-floor",
     "Election results cover 2019-2025 everywhere except SLC (2007-2025). "
     "Longitudinal election analysis deeper than 2019 is SLC-only. "
     "(Elections ARE federated — `election_race` is the audited winners/margins "
     "layer, `election_result` the SLCo SOVC tallies; the per-city "
     "election_results/ CSVs remain the on-disk source.)"),
]


def log(msg=""):
    print(msg, flush=True)


def copy_standard_tables(out, src, slug, offset, gov_level, state):
    """Copy the 8 standard tables from one entity db, offsetting all ids and
    stamping the federation key (entity slug + gov_level + state). `slug` fills
    the historical `city` column (now the general entity key)."""
    counts = {}
    pfx = (slug, gov_level, state)

    def off(v):
        return None if v is None else v + offset

    cur = src.execute("SELECT body_id, name, kind FROM body ORDER BY body_id")
    rows = [pfx + (off(a), b, c) for a, b, c in cur]
    out.executemany("INSERT INTO body VALUES (?,?,?,?,?,?)", rows)
    counts["body"] = len(rows)

    cur = src.execute("SELECT person_id, full_name, name_key FROM person ORDER BY person_id")
    rows = [pfx + (off(a), b, c) for a, b, c in cur]
    out.executemany("INSERT INTO person VALUES (?,?,?,?,?,?)", rows)
    counts["person"] = len(rows)

    cur = src.execute("SELECT meeting_id, body_id, meeting_date, title, source_file "
                      "FROM meeting ORDER BY meeting_id")
    rows = [pfx + (off(a), off(b), c, d, e) for a, b, c, d, e in cur]
    out.executemany("INSERT INTO meeting VALUES (?,?,?,?,?,?,?,?)", rows)
    counts["meeting"] = len(rows)

    cur = src.execute("SELECT application_id, app_key, body_id, name, rep_title "
                      "FROM application ORDER BY application_id")
    rows = [pfx + (off(a), b, off(c), d, e) for a, b, c, d, e in cur]
    out.executemany("INSERT INTO application VALUES (?,?,?,?,?,?,?,?)", rows)
    counts["application"] = len(rows)

    # provenance exists once a city's db is rebuilt post-2026-07-10; older dbs
    # predate it — default those rows to 'minutes' (same tolerance as vote.note).
    has_prov = any(r[1] == "provenance" for r in src.execute("PRAGMA table_info(motion)"))
    prov_col = "provenance" if has_prov else "'minutes'"
    # disposition columns exist once a city's db is rebuilt post-2026-07-12 (T1.1);
    # older/custom dbs (e.g. the county) may lack them — default those rows to NULL.
    has_disp = any(r[1] == "disposition" for r in src.execute("PRAGMA table_info(motion)"))
    disp_cols = ("disposition, disposition_method, disposition_confidence"
                 if has_disp else "NULL, NULL, NULL")
    cur = src.execute(
        "SELECT motion_id, meeting_id, body_id, motion_no, motion_text, motion_type,"
        " result_raw, outcome, stage, recommendation, " + disp_cols + ", application_id,"
        " app_match_method, app_confidence, mover_person_id, seconder_person_id,"
        " names_recorded, source_file, " + prov_col + " FROM motion ORDER BY motion_id")
    rows = [pfx + (off(r[0]), off(r[1]), off(r[2]), r[3], r[4], r[5], r[6], r[7],
             r[8], r[9], r[10], r[11], r[12], off(r[13]), r[14], r[15], off(r[16]),
             off(r[17]), r[18], r[19], r[20]) for r in cur]
    out.executemany("INSERT INTO motion VALUES (" + ",".join(["?"] * 24) + ")", rows)
    counts["motion"] = len(rows)

    # vote.note exists only in park_city's db
    has_note = any(r[1] == "note" for r in src.execute("PRAGMA table_info(vote)"))
    sel = ("SELECT vote_id, motion_id, person_id, vote_value, note FROM vote"
           if has_note else
           "SELECT vote_id, motion_id, person_id, vote_value, NULL FROM vote")
    cur = src.execute(sel + " ORDER BY vote_id")
    rows = [pfx + (off(a), off(b), off(c), d, e) for a, b, c, d, e in cur]
    out.executemany("INSERT INTO vote VALUES (?,?,?,?,?,?,?,?)", rows)
    counts["vote"] = len(rows)

    cur = src.execute("SELECT role_id, person_id, body_id, first_seen, last_seen,"
                      " n_votes FROM role ORDER BY role_id")
    rows = [pfx + (off(a), off(b), off(c), d, e, f) for a, b, c, d, e, f in cur]
    out.executemany("INSERT INTO role VALUES (?,?,?,?,?,?,?,?,?)", rows)
    counts["role"] = len(rows)

    cur = src.execute(
        "SELECT referral_id, primary_application_id, primary_body,"
        " related_application_id, related_body, match_method, confidence,"
        " shared_address, subject_score, primary_date, related_date, gap_days,"
        " note FROM referral ORDER BY referral_id")
    rows = [pfx + (off(r[0]), off(r[1]), r[2], off(r[3]), r[4], r[5], r[6], r[7],
             r[8], r[9], r[10], r[11], r[12]) for r in cur]
    out.executemany("INSERT INTO referral VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    counts["referral"] = len(rows)

    return counts


def load_motion_std(out, slug, city_dir):
    """Load the city's (up to) two motions_std.csv files and join to motion.

    Join key: (source, motion_no, date) against motion.source_file +
    motion.motion_no + meeting.meeting_date; falls back to (source, motion_no)
    where that pair is unique on both sides (it is everywhere except sandy PC,
    whose constant Legistar-staging `source` string makes the pair degenerate
    — SCHEMA_SPEC §2 — which is exactly why the date key is primary).
    """
    # motion-side lookups (already offset ids, so query cities.db itself)
    key3, key2 = {}, {}
    for mid, src_file, mno, mdate in out.execute(
            "SELECT m.motion_id, m.source_file, m.motion_no, mt.meeting_date "
            "FROM motion m JOIN meeting mt ON mt.meeting_id = m.meeting_id "
            "WHERE m.city = ?", (slug,)):
        key3[(src_file, mno, mdate)] = mid
        key2.setdefault((src_file, mno), []).append(mid)

    stats = {}
    for dataset in ("meeting_minutes", "planning_commission"):
        path = os.path.join(ROOT, city_dir, dataset, "motions_std.csv")
        if not os.path.exists(path):
            continue
        n = matched = 0
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                n += 1
                mno = int(r["motion_no"])
                k3 = (r["source"], mno, r["date"])
                mid = key3.get(k3)
                if mid is None:  # date-mismatch fallback: unique (source, motion_no)
                    cands = key2.get((r["source"], mno), [])
                    if len(cands) == 1:
                        mid = cands[0]
                if mid is not None:
                    matched += 1
                rows.append((
                    slug, dataset, r["source"], mno, r["date"], r["body"],
                    r["motion_type_native"], r["motion_type_std"],
                    r["land_use_type"], r["action_class"], r["outcome"],
                    int(r["tally_aye"]) if r["tally_aye"] else None,
                    int(r["tally_nay"]) if r["tally_nay"] else None,
                    int(r["tally_other"]) if r["tally_other"] else None,
                    r["vote_mode"], r["result_raw"], r["classify_method"],
                    r["classify_confidence"], mid))
        out.executemany(
            "INSERT INTO motion_std VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows)
        stats[dataset] = (n, matched)
    return stats


# ---------------------------------------------------------------------------
# NON-CITY motion_std — computed at federation (2026-07-29, TODO high (j))
# ---------------------------------------------------------------------------
# The 31 cities keep their file-based path exactly as it was: normalize_motions.py
# writes <city>/<dataset>/motions_std.csv and load_motion_std() reads it.  The
# county / MPO tier has NO uniform flat-motion file shape (cache+summit carry
# land_use/+legislative/all_votes.csv, utah+weber only db/staging/motions.csv,
# wfrc legislative/all_motions.csv, salt_lake_county land_use only — and mag_mpo has
# NO flat motion CSV at all: its motions exist only in its entity db).  Rather than
# invent per-entity artifacts, this tier's motion_std rows are
# computed HERE, from the `motion`/`vote`/`meeting`/`body` rows already federated,
# REUSING scripts/normalize_motions.py's classifier and parsers — imported, never
# re-implemented, so the two tiers can never drift.  Consequences:
#   * motion_id is set by construction -> the non-city join rate is 100% exactly.
#   * classification degrades HONESTLY: where the motion text carries no subject
#     signal the row is Other / classify_confidence='low' (rule:no-signal), the
#     same output the city path emits.  That is a finding about the source, not a
#     failure — most of this tier publishes an empty or non-subject motion_type
#     (see normalize_motions.ENTITY_MT).
#   * NOTHING on disk is written or read for this tier; re-running is idempotent.
import normalize_motions as _nm          # scripts/ is on sys.path (same dir)

# 'Yea' is the Legislature's verbatim affirmative (SCHEMA §DDL vote_value CHECK).
# Extend the imported set at the CALL SITE rather than mutating the shared module,
# so the city path's counting vocabulary is provably untouched.
_AYE_VALUES = _nm.AYE_VOTE_VALUES | {"Yea"}

# Entities EXCLUDED from this layer — their motion_std stays EMPTY on purpose.
# ut_state (owner ruling, 2026-07-29): its "motions" are BILL-STAGE VOTES
# (committee report, 2nd/3rd reading, concurrence), not motions on a matter, and
# the municipal motion_type_std vocabulary (Land-Use | Ordinance | Resolution |
# Budget | Appointment | …) does not describe them. The state tier is to be
# reevaluated and reintegrated ON ITS OWN TERMS — the way wfrc_mpo was, with
# first-class tables — rather than having the municipal frame fitted to it. See
# TODO "STATE TIER — reevaluate how `ut_state` is integrated, ON ITS OWN TERMS (owner ruling 2026-07-29)". Its 1,208 motions having no motion_std row is the INTENDED
# state, not a gap; the ut_state/motion-std-deferred caveat says so on the record.
EXCLUDED_FROM_MOTION_STD = {"ut_state"}

# body-name -> dataset.  The only split that matters analytically is the
# land-use body vs everything else (mirrors the city meeting_minutes /
# planning_commission split, which likewise folds RDA/MBA into meeting_minutes).
def _noncity_dataset(slug, body_name):
    if "planning commission" in body_name.lower() or body_name == "PlanningCommission":
        return "land_use"
    return "legislative"


def compute_motion_std_noncity(out, slug):
    """Compute + insert motion_std rows for one non-city entity.

    Mirrors normalize_motions.process() step for step — parse_result() on the
    verbatim result string, the counted-member-rows tally fallback (guarded by
    outcome consistency exactly as the city path guards it), the '+text-died'
    and members-majority outcome fallbacks, classify(), action_class(),
    vote_mode() — but sources its rows from the federated tables instead of a
    CSV.  Returns (n_rows, n_low_confidence, Counter(classify_confidence)).
    """
    votes = {}
    for mid, vv in out.execute(
            "SELECT motion_id, vote_value FROM vote WHERE city = ?", (slug,)):
        votes.setdefault(mid, {})
        votes[mid][vv] = votes[mid].get(vv, 0) + 1

    rows = []
    conf_dist = {}
    std_dist = {}
    for (mid, body_name, mdate, src_file, mno, native, text, result) in out.execute(
            "SELECT m.motion_id, b.name, mt.meeting_date, m.source_file, m.motion_no,"
            "       m.motion_type, m.motion_text, m.result_raw "
            "FROM motion m JOIN body b ON b.body_id = m.body_id "
            "JOIN meeting mt ON mt.meeting_id = m.meeting_id "
            "WHERE m.city = ? ORDER BY m.motion_id", (slug,)):
        text = text or ""
        result = result or ""
        dataset = _noncity_dataset(slug, body_name)

        outcome, aye, nay, other, mode_hint, _rule = _nm.parse_result(result)
        if outcome == "unknown" and re.search(
                r"motion died|died for lack of a second|for lack of a second",
                text, re.I):
            outcome = "died"

        vc = votes.get(mid, {})
        names = bool(vc)
        c_aye = sum(vc.get(v, 0) for v in _AYE_VALUES)
        c_nay = sum(vc.get(v, 0) for v in _nm.NAY_VOTE_VALUES)
        c_oth = sum(vc.get(v, 0) for v in _nm.OTHER_VOTE_VALUES)
        # tallies: the printed string wins; else count named member rows, but
        # only when they are CONSISTENT with the stated outcome (a partial
        # roster — dissent-only naming — must stay blank, never be inferred).
        if aye is None and names:
            consistent = (outcome == "pass" and c_aye > c_nay) or \
                         (outcome == "fail" and c_nay >= c_aye) or \
                         outcome == "unknown"
            if consistent:
                aye, nay = c_aye, c_nay
                other = c_oth if c_oth else None
        if outcome == "unknown" and names and (c_aye or c_nay):
            outcome = "pass" if c_aye > c_nay else ("fail" if c_nay > c_aye else "unknown")

        std, sub, method, conf = _nm.classify(slug, native or "", text)
        # action_class()'s statutory PC-advisory default keys on the city dataset
        # name; a county planning commission is advisory to the county legislative
        # body under the same LUDMA article, so pass the city-equivalent token.
        ac = _nm.action_class(
            slug,
            "planning_commission" if dataset == "land_use" else "meeting_minutes",
            "", result, text, std, sub)
        conf_dist[conf] = conf_dist.get(conf, 0) + 1
        std_dist[std] = std_dist.get(std, 0) + 1

        rows.append((slug, dataset, src_file or "", mno, mdate, body_name,
                     native, std, sub, ac, outcome, aye, nay, other,
                     _nm.vote_mode(names, mode_hint, aye is not None),
                     result, method, conf, mid))

    out.executemany(
        "INSERT INTO motion_std VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows), conf_dist, std_dist


def load_crosswalks(out):
    for fname, table, ncol in (
            ("motion_type_crosswalk.csv", "motion_type_crosswalk", 4),
            ("body_crosswalk.csv", "body_crosswalk", 4),
            ("vote_values.csv", "vote_values", 4)):
        path = os.path.join(ROOT, "crosswalks", fname)
        with open(path, newline="", encoding="utf-8") as f:
            rdr = csv.reader(f)
            next(rdr)  # header
            rows = [row[:ncol] + [None] * (ncol - len(row)) for row in rdr]
        out.executemany(
            "INSERT INTO %s VALUES (%s)" % (table, ",".join("?" * ncol)), rows)
        log("  %-22s %4d rows  (crosswalks/%s)" % (table, len(rows), fname))


VIEWS = """
-- Datasets are derived from body: PlanningCommission rows came from
-- planning_commission/, everything else from meeting_minutes/.

-- v_contested_all — every motion whose recorded outcome was NOT unanimous,
-- across all cities. Contested = a dissent was NAMED (Nay/Abstain/Recuse row)
-- OR the printed TALLY shows nay/other (motion_std). The union catches BOTH
-- named dissent AND tally-only dissent (a bare "5:2" with no roll call) —
-- neither alone is complete (a nay can live in the tally but not the roll call,
-- or in the roll call but not a "Unanimous"-printed tally).
--   MARGINS: use tally_aye/tally_nay/tally_other — authoritative, from motion_std,
--   falling back to the named counts only where no std tally exists. vote_mode
--   (roll-call / tally / dissent-only) says how the source recorded it.
--   ATTRIBUTION ONLY: named_ayes/named_nays/named_abstains/named_recuses are who
--   was actually NAMED. They UNDERCOUNT in dissent-only/tally-only cities — e.g.
--   provo work sessions record only dissenters, so named_ayes=0 while tally_aye=5.
--   Never read named_* as the margin; dissent_caveats flags every such row.
CREATE VIEW v_contested_all AS
SELECT
    m.city,
    b.name                       AS body,
    mt.meeting_date              AS date,
    m.motion_id,
    m.motion_no,
    ms.motion_type_std,
    ms.land_use_type,
    m.motion_type                AS motion_type_native,
    m.motion_text,
    m.result_raw,
    m.outcome,
    m.provenance,
    ms.vote_mode,
    COALESCE(ms.tally_aye,   SUM(v.vote_value IN ('Aye','Yea')))         AS tally_aye,
    COALESCE(ms.tally_nay,   SUM(v.vote_value = 'Nay'))                  AS tally_nay,
    COALESCE(ms.tally_other, SUM(v.vote_value IN ('Abstain','Recuse'))) AS tally_other,
    SUM(v.vote_value IN ('Aye','Yea')) AS named_ayes,
    SUM(v.vote_value = 'Nay')     AS named_nays,
    SUM(v.vote_value = 'Abstain') AS named_abstains,
    SUM(v.vote_value = 'Recuse')  AS named_recuses,
    (SELECT GROUP_CONCAT(c.code, ',') FROM caveat c
      WHERE (c.city = m.city OR c.city = '*')
        AND (c.dataset = '*' OR c.dataset =
             CASE WHEN b.name = 'PlanningCommission'
                  THEN 'planning_commission' ELSE 'meeting_minutes' END)
        AND c.code IN ('tally-only','tally-only-partial','dissent-only',
                       'vote-ceiling','tie-break-note'))
                                  AS dissent_caveats
FROM motion m
JOIN meeting mt ON mt.meeting_id = m.meeting_id
JOIN body b     ON b.body_id = m.body_id
JOIN vote v     ON v.motion_id = m.motion_id
LEFT JOIN motion_std ms ON ms.motion_id = m.motion_id
GROUP BY m.motion_id
HAVING SUM(v.vote_value IN ('Nay','Abstain','Recuse')) > 0
    OR MAX(COALESCE(ms.tally_nay,   0)) > 0
    OR MAX(COALESCE(ms.tally_other, 0)) > 0;

-- v_member_record_all — per (city, member, body) voting record. Same
-- recording-limit caveats apply (orem: no absences ever; nephi: tiny named
-- subset; sandy/provo: majority often unnamed; WJ PC: dissenters only).
CREATE VIEW v_member_record_all AS
SELECT
    v.city,
    p.full_name,
    b.name                        AS body,
    COUNT(*)                      AS n_votes,
    SUM(v.vote_value IN ('Aye','Yea')) AS ayes,
    SUM(v.vote_value = 'Nay')     AS nays,
    SUM(v.vote_value = 'Abstain') AS abstains,
    SUM(v.vote_value = 'Recuse')  AS recuses,
    SUM(v.vote_value = 'Absent')  AS absents,
    SUM(v.vote_value = 'Excused') AS excuseds,
    ROUND(100.0 * SUM(v.vote_value = 'Nay')
          / MAX(1, SUM(v.vote_value IN ('Aye','Yea','Nay'))), 1)
                                  AS nay_pct_of_aye_nay,
    (SELECT GROUP_CONCAT(c.code, ',') FROM caveat c
      WHERE (c.city = v.city OR c.city = '*')
        AND (c.dataset = '*' OR c.dataset =
             CASE WHEN b.name = 'PlanningCommission'
                  THEN 'planning_commission' ELSE 'meeting_minutes' END)
        AND c.code IN ('tally-only','tally-only-partial','dissent-only',
                       'vote-ceiling'))
                                  AS record_caveats
FROM vote v
JOIN person p ON p.person_id = v.person_id
JOIN motion m ON m.motion_id = v.motion_id
JOIN body b   ON b.body_id = m.body_id
GROUP BY v.city, v.person_id, m.body_id;

-- v_landuse_outcomes — motion_std-based: land_use_type × outcome × city ×
-- year × dataset, with the caveats that shape land-use comparability
-- (ogden's 428-subject undercount; provo PC 2025+ floor; slc 2021+ floor).
CREATE VIEW v_landuse_outcomes AS
SELECT
    s.city,
    s.dataset,
    CAST(substr(s.date, 1, 4) AS INTEGER) AS year,
    s.land_use_type,
    s.action_class,
    s.outcome,
    COUNT(*) AS n_motions,
    (SELECT GROUP_CONCAT(c.code, ',') FROM caveat c
      WHERE (c.city = s.city OR c.city = '*')
        AND (c.dataset = s.dataset OR c.dataset = '*')
        AND c.code IN ('landuse-undercount','coverage-floor','outcome-unknown',
                       'no-hearing-motions','text-quality'))
                                  AS landuse_caveats
FROM motion_std s
WHERE s.motion_type_std = 'Land-Use'
GROUP BY s.city, s.dataset, year, s.land_use_type, s.action_class, s.outcome;

-- v_pc_divergence — PC recommendation vs the linked council outcome, via the
-- reconstructed referral layer. EXCLUDES confidence='low' links BY DESIGN
-- (repo rule: low = flagged, do not quote); the underlying rows remain in
-- `referral` if you need them. council_outcome is the LATEST council-stage
-- motion on the linked council application. diverged=1 when the PC said
-- Negative but council passed, or Positive but council failed.
CREATE VIEW v_pc_divergence AS
WITH pc_rec AS (
    SELECT m.application_id,
           MAX(mt.meeting_date)  AS pc_date,
           GROUP_CONCAT(DISTINCT m.recommendation) AS pc_recommendation
    FROM motion m JOIN meeting mt ON mt.meeting_id = m.meeting_id
    WHERE m.stage = 'pc_recommendation'
    GROUP BY m.application_id
),
council_last AS (
    SELECT m.application_id, m.outcome, mt.meeting_date,
           ROW_NUMBER() OVER (PARTITION BY m.application_id
                              ORDER BY mt.meeting_date DESC, m.motion_id DESC) AS rn
    FROM motion m JOIN meeting mt ON mt.meeting_id = m.meeting_id
    WHERE m.stage NOT IN ('pc_recommendation', 'pc_final_action')
)
SELECT
    r.city,
    r.confidence,
    r.match_method,
    pr.pc_date,
    pr.pc_recommendation,
    cl.meeting_date AS council_date,
    cl.outcome      AS council_outcome,
    CASE WHEN (pr.pc_recommendation = 'Negative' AND cl.outcome = 'Pass')
           OR (pr.pc_recommendation = 'Positive' AND cl.outcome = 'Fail')
         THEN 1 ELSE 0 END AS diverged,
    pa.rep_title AS pc_item,
    ca.rep_title AS council_item,
    r.primary_application_id,
    r.related_application_id
FROM referral r
JOIN pc_rec pr       ON pr.application_id = r.related_application_id
JOIN council_last cl ON cl.application_id = r.primary_application_id AND cl.rn = 1
JOIN application pa  ON pa.application_id = r.related_application_id
JOIN application ca  ON ca.application_id = r.primary_application_id
WHERE r.related_body = 'PlanningCommission'
  AND r.confidence IN ('high', 'medium');

-- v_coverage — the caveat-aware coverage matrix. One row per city × dataset
-- present in motion_std (all vote datasets), plus caveat-only rows for the
-- datasets that live OUTSIDE cities.db (public_comments, election_results),
-- so a coverage question can't silently miss them.
CREATE VIEW v_coverage AS
SELECT
    s.city, s.dataset,
    COUNT(*)                                  AS motions,
    SUM(s.outcome = 'pass')                   AS passed,
    SUM(s.outcome = 'unknown')                AS outcome_unknown,
    MIN(s.date)                               AS first_date,
    MAX(s.date)                               AS last_date,
    (SELECT GROUP_CONCAT(c.code || ': ' || c.caveat, ' | ') FROM caveat c
      WHERE (c.city = s.city OR c.city = '*')
        AND (c.dataset = s.dataset OR c.dataset = '*')) AS caveats
FROM motion_std s
GROUP BY s.city, s.dataset
UNION ALL
SELECT c.city, c.dataset, NULL, NULL, NULL, NULL, NULL,
       GROUP_CONCAT(c.code || ': ' || c.caveat, ' | ')
FROM caveat c
WHERE c.dataset IN ('public_comments', 'election_results')
GROUP BY c.city, c.dataset
UNION ALL
-- ...and the non-city entities with NO motion_std rows, so they can't silently
-- vanish from a coverage question now that every other entity has them. The
-- dataset label distinguishes the TWO honest reasons:
--   '(no vote layer)'       — the entity contributes no motions at all:
--                             washington_county (LIGHT+) and juab_county
--                             (CHEAP-ONLY) are DB-LESS BY DESIGN, vote layer
--                             explicitly DEFERRED, not missing.
--   '(no motion_std layer)' — the entity HAS motions and votes but is not in the
--                             normalization layer: ut_state, whose bill-stage
--                             votes the municipal vocabulary does not describe
--                             (see its motion-std-deferred caveat).
-- Restricted to entities that carry a caveat SAYING SO — a registered-only entity
-- with no documented deferral (wasatch_county, udot, uta) is a registry fact,
-- not a coverage row.
SELECT e.slug,
       CASE WHEN EXISTS (SELECT 1 FROM motion m WHERE m.city = e.slug)
            THEN '(no motion_std layer)' ELSE '(no vote layer)' END,
       NULL, NULL, NULL, NULL, NULL,
       (SELECT GROUP_CONCAT(c.code || ': ' || c.caveat, ' | ')
          FROM caveat c WHERE c.city = e.slug)
FROM entity e
WHERE e.level <> 'city'
  AND NOT EXISTS (SELECT 1 FROM motion_std s WHERE s.city = e.slug)
  AND EXISTS (SELECT 1 FROM caveat c WHERE c.city = e.slug);

-- v_election_city — each city's audited council/mayor races with the containing
-- county attached (the city↔county elections tier in one place). Winners/margins
-- are the per-city audited values; join election_result on (county=r.county,
-- jurisdiction_slug=r.city, year, office) for the underlying candidate tallies.
CREATE VIEW v_election_city AS
SELECT r.city, r.county, r.year, r.election_type, r.office, r.district,
       r.winner, r.winner_votes, r.runner_up, r.runner_up_votes,
       r.margin_votes, r.margin_pct, r.uncontested, r.turnout_pct, r.source_file
FROM election_race r;
"""


ELECTION_CAVEATS = [
    ("*", "election_results", "elections-coverage",
     "Elections cover municipal general + primary races; 2019+ for most cities, "
     "SLC 2007+ (SCHEMA_SPEC §9). election_race = per-city audited winners/margins "
     "(the authoritative layer); election_result = county SOVC candidate tallies."),
    ("salt_lake_county", "election_results", "county-canvass",
     "election_result holds Salt Lake County Clerk SOVC tallies (council/mayor, the 7 "
     "held cities) derived from salt_lake_county/elections/slco_municipal_results_long.csv "
     "(precinct×candidate, summed here). rank_in_contest is PLURALITY order; for the "
     "audited winner/margin use election_race (v_election_city)."),
    ("millcreek", "election_results", "rcv",
     "Millcreek uses Ranked-Choice Voting (2021, 2023) — election_result rank_in_contest "
     "(first-choice plurality) is NOT the RCV final winner; 2025 mayor was appointed. Use "
     "election_race for authoritative outcomes."),
    ("salt_lake_county", "election_results", "county-office-suppression",
     "County-office rows (even-year, 2002–2026): 185 candidate columns in the 2024/2026 "
     "workbooks carry **** privacy-suppressed precinct sub-rows, so `votes` (precinct sum) "
     "understates. Use `certified_votes` (the workbook's own certified figure; "
     "votes_basis='certified-over-suppressed' marks these rows)."),
    ("salt_lake_county", "election_results", "county-primary-nominees",
     "County-office `primary` rows in election_race are party NOMINATION results — the "
     "winner is the nominee, not an officeholder. Each such row's note says so; join "
     "year+office to the general row for the seat outcome."),
    ("salt_lake_county", "election_results", "county-writein-bucket",
     "2 county_races rows carry AUDIT FLAG in note (2006 Surveyor, 2016 Council D2): the "
     "runner-up is the canvass's aggregate write-in bucket, so margin_* is not a "
     "two-candidate margin."),
    ("salt_lake_county", "election_results", "county-2004-source-discrepancy",
     "2004 'Salt Lake City School District 2': the county's own precinct rows sum to "
     "1,937/1,934 but its legend and certification PDF certify 1,939/1,938. Source-internal "
     "contradiction kept verbatim (allowlisted in the county normalizer's gate)."),
]

ERACE_COLS = [
    "year", "election_type", "office", "district", "contest", "contest_verbatim",
    "n_seats", "n_candidates", "voting_method", "total_votes",
    "total_first_choice_votes", "winner", "winner_votes", "winner_pct", "runner_up",
    "runner_up_votes", "margin_votes", "margin_pct", "registered_voters",
    "ballots_cast", "turnout_pct", "uncontested", "suppressed_precincts", "note",
    "source_file"]


def load_election_race(out):
    """Audited race summaries (the uniform 25-col §9 superset), stamped with entity
    key + containing county. Two grains: every city's election_results/<slug>_races.csv,
    and — since 2026-08-01 (county-acquisition package) — every county's
    elections/county_races.csv (county-office races; `county` = the entity itself)."""
    within = {r.a: r.b for r in RELATIONSHIPS if r.relation == "within"}
    n = 0
    for e in (x for x in ENTITIES if x.level == "city"):
        path = os.path.join(ROOT, e.dir, "election_results", "%s_races.csv" % e.slug)
        if not os.path.exists(path):
            continue
        county = within.get(e.slug, "")
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out.execute(
                    "INSERT INTO election_race VALUES (%s)" % ",".join(["?"] * 29),
                    [e.slug, "city", e.state, county] + [r.get(c, "") for c in ERACE_COLS])
                n += 1
    for e in (x for x in ENTITIES if x.level == "county"):
        path = os.path.join(ROOT, e.dir, "elections", "county_races.csv")
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                out.execute(
                    "INSERT INTO election_race VALUES (%s)" % ",".join(["?"] * 29),
                    [e.slug, "county", e.state, e.slug] + [r.get(c, "") for c in ERACE_COLS])
                n += 1
    return n


def load_election_result(out):
    """County-grain SOVC tallies from each built county's elections module.
    Two files per county: election_results_by_contest.csv (municipal, odd-year)
    and — since 2026-08-01 — county_results_by_contest.csv (county-office,
    even-year; carries election_date/certified_votes/votes_basis, '' / NULL on
    municipal rows). Contest×candidate, jurisdiction-tagged."""
    def _int(v):
        return int(v) if v not in (None, "") else None
    n = 0
    for e in (x for x in ENTITIES if x.level == "county"):
        for fname in ("election_results_by_contest.csv",
                      "county_results_by_contest.csv"):
            path = os.path.join(ROOT, e.dir, "elections", fname)
            if not os.path.exists(path):
                continue
            with open(path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    out.execute(
                        "INSERT INTO election_result VALUES (%s)" % ",".join(["?"] * 20),
                        [e.slug, "county", e.state, int(r["year"]),
                         r["election_type"], r.get("election_date", ""),
                         r["contest"], r["jurisdiction_slug"], r["office"],
                         r["district"], r["seats"], r["candidate"], r["party"],
                         int(r["votes"]), _int(r.get("certified_votes")),
                         r.get("votes_basis", ""), int(r["rank_in_contest"]),
                         int(r["n_precincts"]), r["suppressed"], r["source_file"]])
                    n += 1
    return n


def _county_entities():
    # All NON-CITY entities, built-db or not: thin counties (washington, juab —
    # 2026-07-20 Phase 4) carry projections/gis without a vote-spine db, and the
    # Phase-5 regional/state tiers (wfrc_mpo/mag_mpo/ut_state) carry projections/
    # gis/projects modules too. Each loader already skips missing files via
    # read_csv_rows, so no db gate is needed; gov_level comes from e.level.
    return [e for e in ENTITIES if e.level != "city"]


def load_regional_projects(out):
    cols = ["plan_kind", "plan_vintage", "project_id", "name", "mode",
            "improvement_type", "jurisdiction", "county", "phase_or_year",
            "cost", "status", "description", "source_layer", "source_url"]
    n = 0
    for e in _county_entities():
        for r in read_csv_rows(os.path.join(ROOT, e.dir, "projects", "projects.csv")):
            out.execute("INSERT INTO regional_project VALUES (%s)" % ",".join(["?"] * 17),
                        [e.slug, e.level, e.state] + [r.get(c) for c in cols])
            n += 1
    return n


def load_project_vintages(out):
    cols = ["plan_vintage", "pin", "variant", "name", "county", "in_wfrc_region",
            "forecast_start_year", "cost", "status", "funding_source_raw",
            "description", "source_layer"]
    n = 0
    for e in _county_entities():
        path = os.path.join(ROOT, e.dir, "projects", "derived", "project_vintage.csv")
        for r in read_csv_rows(path):
            out.execute("INSERT INTO project_vintage VALUES (%s)" % ",".join(["?"] * 15),
                        [e.slug, e.level, e.state] + [r.get(c) for c in cols])
            n += 1
    return n


def load_project_histories(out):
    cols = ["pin", "name_latest", "n_vintages", "first_vintage", "last_vintage",
            "vintages", "entered_tip", "left_censored", "exited_tip",
            "first_forecast_year", "last_forecast_year", "slip_years",
            "first_cost", "last_cost", "cost_drift_pct", "last_status",
            "statuses", "counties", "in_wfrc_region", "rtp_unique_id",
            "rtp_match_confidence"]
    n = 0
    for e in _county_entities():
        path = os.path.join(ROOT, e.dir, "projects", "derived", "project_history.csv")
        for r in read_csv_rows(path):
            out.execute("INSERT INTO project_history VALUES (%s)" % ",".join(["?"] * 24),
                        [e.slug, e.level, e.state] + [r.get(c) for c in cols])
            n += 1
    return n


def load_development_applications(out):
    import glob
    n = 0
    for e in _county_entities():
        off = e.fed_index * OFFSET_UNIT
        path = os.path.join(ROOT, e.dir, "development", "applications.csv")
        for r in read_csv_rows(path):
            mid = r.get("motion_id")
            fed_mid = int(mid) + off if mid and str(mid).strip().isdigit() else None
            out.execute("INSERT INTO development_application VALUES (%s)" % ",".join(["?"] * 13),
                        [e.slug, e.level, e.state, r.get("date"), r.get("body"),
                         r.get("dev_type"), r.get("title"), r.get("matter"),
                         r.get("location"), r.get("outcome"),
                         int(r["names_recorded"]) if r.get("names_recorded", "").strip().isdigit() else None,
                         fed_mid, r.get("minutes_path")])
            n += 1
    return n


def load_projections(out):
    import glob
    cols = ["geography", "geography_type", "year", "metric", "value", "scenario",
            "source", "source_url", "vintage"]
    n = 0
    for e in _county_entities():
        for path in sorted(glob.glob(os.path.join(ROOT, e.dir, "projections", "*.csv"))):
            for r in read_csv_rows(path):
                if "year" not in r or "metric" not in r:
                    continue
                yr = r.get("year", "")
                out.execute("INSERT INTO projection VALUES (%s)" % ",".join(["?"] * 12),
                            [e.slug, e.level, e.state] +
                            [(int(yr) if str(yr).strip().isdigit() else None) if c == "year"
                             else r.get(c) for c in cols])
                n += 1
    return n


def load_gis_layers(out):
    cols = ["layer", "description", "publisher", "url", "api_endpoint", "format",
            "vintage", "license", "growth_relevance", "notes"]
    n = 0
    for e in _county_entities():
        for r in read_csv_rows(os.path.join(ROOT, e.dir, "gis", "index.csv")):
            out.execute("INSERT INTO gis_layer VALUES (%s)" % ",".join(["?"] * 13),
                        [e.slug, e.level, e.state] + [r.get(c) for c in cols])
            n += 1
    return n


def read_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


LOCK_PATH = os.path.join(ROOT, "gov.db.lock")
TMP_DB = OUT_DB + ".tmp"


def main():
    """G7 hardening (2026-07-31): exclusive lockfile + atomic tmp-then-replace
    build + the federation-staleness gate auto-run at the end. A mid-build crash
    leaves the previous gov.db intact, and the GOTCHAS no-concurrent-federation
    rule is enforced in code, not prose."""
    try:
        lock_fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(lock_fd, ("%d\n" % os.getpid()).encode())
    except FileExistsError:
        log("FATAL: %s exists — another federation appears to be running (or a "
            "prior one crashed; verify no build is live, then remove the "
            "lockfile)." % LOCK_PATH)
        sys.exit(1)
    try:
        _build_locked()
    finally:
        os.close(lock_fd)
        if os.path.exists(LOCK_PATH):
            os.unlink(LOCK_PATH)


def _build_locked():
    if os.path.exists(TMP_DB):
        os.remove(TMP_DB)
    out = sqlite3.connect(TMP_DB)
    out.execute("PRAGMA foreign_keys = ON")
    out.executescript(DDL)

    log("Building %s" % OUT_DB)
    log("")

    # 1. union the standard tables ------------------------------------------
    per_city = {}        # slug -> {table: n}
    src_counts = {}      # slug -> {table: n in source db}
    for e in BUILT:
        db_path = os.path.join(ROOT, e.dir, e.db_rel_path)
        if not os.path.exists(db_path):
            log("FATAL: missing %s" % db_path)
            sys.exit(1)
        src = sqlite3.connect("file:%s?mode=ro" % db_path, uri=True)
        offset = e.fed_index * OFFSET_UNIT
        per_city[e.slug] = copy_standard_tables(out, src, e.slug, offset,
                                                e.level, e.state)
        src_counts[e.slug] = {
            t: src.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
            for t in STD_TABLES}
        src.close()

    # 2. reconciliation: copied == source, and federated total == sum --------
    log("Row-count reconciliation (per-city source counts must sum exactly):")
    hdr = "%-12s" % "table" + "".join("%8s" % e.slug[:7] for e in BUILT) \
          + "%9s %9s %5s" % ("sum", "cities.db", "ok")
    log(hdr)
    ok_all = True
    for t in STD_TABLES:
        total_src = 0
        cells = []
        for e in BUILT:
            slug = e.slug
            n = src_counts[slug][t]
            if n != per_city[slug][t]:
                log("FATAL: %s/%s copied %d != source %d"
                    % (slug, t, per_city[slug][t], n))
                sys.exit(1)
            total_src += n
            cells.append("%8d" % n)
        fed = out.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        ok = fed == total_src
        ok_all = ok_all and ok
        log("%-12s%s%9d %9d %5s" % (t, "".join(cells), total_src, fed,
                                    "OK" if ok else "FAIL"))
    if not ok_all:
        log("FATAL: reconciliation failed")
        sys.exit(1)
    log("")

    # 3. motion_std ----------------------------------------------------------
    log("motion_std load + join to motion (key: source, motion_no, meeting_date):")
    join_report = []
    tot_n = tot_m = 0
    for e in BUILT:
        slug, city_dir = e.slug, e.dir
        stats = load_motion_std(out, slug, city_dir)
        for ds, (n, matched) in sorted(stats.items()):
            tot_n += n
            tot_m += matched
            rate = 100.0 * matched / n if n else 100.0
            join_report.append((slug, ds, n, matched, rate))
            log("  %-12s %-20s %5d rows, %5d joined  (%.1f%%)"
                % (slug, ds, n, matched, rate))
    log("  %-12s %-20s %5d rows, %5d joined  (%.2f%%)  TOTAL (city, file-based)"
        % ("ALL", "", tot_n, tot_m, 100.0 * tot_m / tot_n))

    # 3b. non-city motion_std — COMPUTED here (no motions_std.csv exists for the
    # county / MPO / state tier); classifier imported from normalize_motions.py.
    log("")
    log("motion_std COMPUTED for the non-city tier (from `motion`; classifier "
        "imported\n  from scripts/normalize_motions.py — city rows above are "
        "untouched):")
    nc_n = 0
    nc_report = []
    for e in BUILT:
        if e.level == "city":
            continue
        if e.slug in EXCLUDED_FROM_MOTION_STD:
            log("  %-18s %-9s %6s  EXCLUDED BY DESIGN — motion_std intentionally "
                "empty;\n  %-28s see the %s/motion-std-deferred caveat"
                % (e.slug, e.level, "-", "", e.slug))
            continue
        n, conf_dist, std_dist = compute_motion_std_noncity(out, e.slug)
        nc_n += n
        low = conf_dist.get("low", 0)
        nc_report.append((e.slug, e.level, n, conf_dist, std_dist))
        log("  %-18s %-9s %6d rows  conf high %5d / medium %5d / low %5d "
            "(%.1f%% honest Other-low)"
            % (e.slug, e.level, n, conf_dist.get("high", 0),
               conf_dist.get("medium", 0), low, 100.0 * low / n if n else 0.0))
    log("  %-18s %-9s %6d rows, %6d joined (100.00%%) TOTAL (non-city, computed)"
        % ("ALL", "", nc_n, nc_n))

    n_motion = out.execute("SELECT COUNT(*) FROM motion").fetchone()[0]
    log("  motion_std rows: %d (city %d file-based + non-city %d computed); "
        "motion rows: %d;\n  distinct motion_ids joined: %d"
        % (tot_n + nc_n, tot_n, nc_n, n_motion,
           out.execute("SELECT COUNT(DISTINCT motion_id) FROM motion_std "
                       "WHERE motion_id IS NOT NULL").fetchone()[0]))
    log("")

    # 4. crosswalks + caveats ------------------------------------------------
    log("Crosswalk + caveat tables:")
    load_crosswalks(out)
    out.executemany("INSERT INTO caveat VALUES (?,?,?,?)", CAVEATS)
    log("  %-22s %4d rows  (embedded in this script; sourced from"
        % ("caveat", len(CAVEATS)))
    log("  %26sSCHEMA_SPEC.md / root README+CLAUDE.md / coverage.json)" % "")
    log("")

    # 4b. entity registry + geography graph (registry/*.csv via entities.py) ---
    out.executemany(
        "INSERT INTO entity VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(e.slug, e.name, e.level, e.state, e.dir, e.db_rel_path, e.fed_index,
          e.fips, e.portal, e.gov_form, e.notes) for e in ENTITIES])
    out.executemany(
        "INSERT INTO entity_relationship VALUES (?,?,?,?,?)",
        [(r.a, r.relation, r.b, r.confidence, r.note) for r in RELATIONSHIPS])
    log("Entity registry: %d entities (%d built), %d relationships"
        % (len(ENTITIES), len(BUILT), len(RELATIONSHIPS)))

    # 4c. elections DB form (city races + county SOVC tallies) ----------------
    n_race = load_election_race(out)
    n_result = load_election_result(out)
    out.executemany("INSERT INTO caveat VALUES (?,?,?,?)", ELECTION_CAVEATS)
    log("Elections: election_race %d city races, election_result %d county tallies"
        % (n_race, n_result))

    # 4d. non-city structured layers (development pipeline / projections / gis
    # catalog / MPO project tables) -------------------------------------------
    n_app = load_development_applications(out)
    n_proj = load_projections(out)
    n_gis = load_gis_layers(out)
    n_rproj = load_regional_projects(out)
    n_pv = load_project_vintages(out)
    n_ph = load_project_histories(out)
    log("Non-city layers: development_application %d, projection %d, gis_layer %d, "
        "regional_project %d, project_vintage %d, project_history %d"
        % (n_app, n_proj, n_gis, n_rproj, n_pv, n_ph))
    log("")

    # 5. views ----------------------------------------------------------------
    out.executescript(VIEWS)
    log("Views: v_contested_all, v_member_record_all, v_landuse_outcomes,")
    log("       v_pc_divergence, v_coverage")

    # 6. build info ------------------------------------------------------------
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    info = [("built_at", now),
            ("script", "scripts/build_cities_db.py"),
            ("note", "DERIVED database — regenerate after any per-city db "
                     "rebuild; never hand-edit"),
            ("motion_std_rows", str(tot_n)),
            ("motion_std_rows_scope", "city, file-based (motions_std.csv); the "
                                      "non-city tier is counted separately below"),
            ("motion_std_joined", str(tot_m)),
            ("motion_std_join_rate_pct", "%.2f" % (100.0 * tot_m / tot_n)),
            ("motion_std_noncity_rows", str(nc_n)),
            ("motion_std_noncity_scope", "county/regional/state, COMPUTED at "
                                         "federation from `motion` (2026-07-29); "
                                         "motion_id set by construction, join 100%"),
            ("motion_std_total_rows", str(tot_n + nc_n))]
    for slug, ds, n, matched, rate in join_report:
        info.append(("join_rate:%s:%s" % (slug, ds),
                     "%d/%d (%.1f%%)" % (matched, n, rate)))
    for slug, lvl, n, conf_dist, std_dist in nc_report:
        info.append(("motion_std_computed:%s" % slug,
                     "%d rows (%s); conf high=%d medium=%d low=%d; Other=%d (%.1f%%)"
                     % (n, lvl, conf_dist.get("high", 0),
                        conf_dist.get("medium", 0), conf_dist.get("low", 0),
                        std_dist.get("Other", 0),
                        100.0 * std_dist.get("Other", 0) / n if n else 0.0)))
    for slug in sorted(EXCLUDED_FROM_MOTION_STD):
        info.append(("motion_std_computed:%s" % slug,
                     "EXCLUDED BY DESIGN — motion_std intentionally empty pending "
                     "TODO 'STATE TIER — reevaluate how `ut_state` is integrated, "
                     "ON ITS OWN TERMS (owner ruling 2026-07-29)'; see the "
                     "%s/motion-std-deferred caveat"
                     % slug))
    for t in STD_TABLES:
        info.append(("rows:%s" % t,
                     str(out.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0])))
    out.executemany("INSERT INTO build_info VALUES (?,?)", info)

    out.commit()
    # integrity
    fk = out.execute("PRAGMA foreign_key_check").fetchall()
    ic = out.execute("PRAGMA integrity_check").fetchone()[0]
    log("")
    log("foreign_key_check: %s; integrity_check: %s"
        % ("0 violations" if not fk else "%d VIOLATIONS" % len(fk), ic))
    if fk or ic != "ok":
        sys.exit(1)
    out.close()
    # atomic promote: only a fully-built, integrity-checked db replaces gov.db
    os.replace(TMP_DB, OUT_DB)
    log("Done: %s (built %s)" % (OUT_DB, now))

    # Phase-2 search layer (REFACTOR_PLAN.md): comment/cf_*/ordinance/document
    # tables + FTS5 indexes. Separate module, same one-command rebuild.
    import build_search_layer
    build_search_layer.main()

    # back-compat: keep cities.db as a symlink to gov.db (Phase 6 rename).
    # An existing regular file (the pre-rename db) is replaced by the link.
    if os.path.islink(LEGACY_LINK) or os.path.exists(LEGACY_LINK):
        os.remove(LEGACY_LINK)
    os.symlink(os.path.basename(OUT_DB), LEGACY_LINK)
    log("Legacy alias: cities.db -> gov.db (symlink refreshed)")

    # G7 (2026-07-31): every build ends with the federation-staleness gate, so
    # "gov.db matches every entity db" is proven on every run instead of only
    # when a human remembers (the 3,000-motion silent-staleness incident).
    import subprocess
    gate = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "validate_entity.py"),
         "--federation"], capture_output=True, text=True)
    tail = "\n".join((gate.stdout or gate.stderr or "").strip().splitlines()[-2:])
    log(tail)
    if gate.returncode != 0:
        log("FATAL: federation-staleness gate FAILED immediately after build.")
        sys.exit(gate.returncode)


if __name__ == "__main__":
    main()
