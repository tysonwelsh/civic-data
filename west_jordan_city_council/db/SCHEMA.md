# West Jordan City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **City Council
↔ Redevelopment Agency (RDA) ↔ Municipal Building Authority (MBA) ↔ Planning Commission** votes by
real keys instead of fuzzy text matching. Built reproducibly in **two stages**; the `db/tables/`
CSVs are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The West Jordan reality (why this is the prose-portal model, not Legistar's)
West Jordan's portal is **PrimeGov PDF/prose** — there is **no Legistar API, no structured
agenda/matter key, and essentially no file/application number in the motion text**. So the project key
is **resolved from prose** by a tiered, auditable resolver — not read from a vendor field. West Jordan
also gives **no shared key across bodies**: `build_db.py` reports **0 applications spanning >1 body**,
by construction (see below). The cross-body relationship is therefore **reconstructed** (`referral`),
never looked up.

The Council, RDA, and MBA share membership entirely — the City Council sits **as** the Redevelopment
Agency and the Municipal Building Authority — but they are modeled as **distinct bodies** (separate
agendas, separate motions) and so are kept as separate `body` rows.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every recorded vote ties to body/meeting/person, and
   every land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council "Copper Meadows" and a PC "Copper Meadows" are **distinct** application rows — never
   merged. `application` therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / RDA / MBA / PlanningCommission; `kind` ∈ council/agency/commission |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title (rich tokens for the referral layer) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` (**present in WJ:** Pass 1,148 · Fail 15)
- `motion.stage` ∈ `council_vote | rda_vote | mba_vote | pc_recommendation | pc_final_action` (the
  schema also allows `ha_vote | boa_action | other_action`; **stages present in WJ:** council_vote 835,
  rda_vote 88, mba_vote 37, pc_recommendation 74, pc_final_action 129)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused` (**present in WJ:** Aye, Nay,
  Abstain, Absent — note **no PC Aye rows exist**, see Known limitations)

### Build totals (current)
**4 bodies · 25 persons · 267 meetings · 293 applications · 1,163 motions · 7,011 votes · 50 roles ·
21 referrals.** Coverage: Council **2020-01-08 → 2026-05-12**; Planning Commission (in DB)
**2022-07-19 → 2026-04-21**.

Motions by body: **Council 835 · RDA 88 · MBA 37 · PlanningCommission 203.** Applications by body:
**Council 160 · PlanningCommission 97 · RDA 30 · MBA 6.** Votes by body: **Council 5,829 · RDA 616 ·
PlanningCommission 307 · MBA 259.** PC stages: **74 recommendations** (68 Positive / 6 Negative,
forwarded to Council) + **129 final actions** (site plan/CUP/preliminary plat — never reach Council).
Contested (any Nay/Abstain/Recuse): **Council 148 · PC 25.** Exactly **1 person served on both the
Council and the PC** — **Kent Shelton** (PC commissioner 2022–2023, then elected to Council 2024+),
unified by name in `person`/`role`. (The Council/RDA/MBA roles overlap completely by design — the
council sits as both agencies.)

## Project resolution — TIERED + AUDITABLE (the within-body key)
West Jordan has no PL#/file number, so each **land-use/policy** motion's `application_id` is resolved
in tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild. (Currently none.)
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized
   name (e.g. *Copper Meadows Rezone*, *Wood Ranch Rezone*, *Prattplex Rezone*). This is the
   heuristic tier — **treat name groupings as provisional** and correct via `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   acreage rezones/GPAs, **code/text amendments**, unnamed street vacations) becomes its **own**
   application: exact identity (one motion = one application, no cross-motion inference), `name` NULL.
   Code/text amendments are deliberately kept granular here so each links to its **specific** prior
   PC recommendation in the referral layer.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 45 (medium) · `singleton` 272 (high)**;
**NULL/non-land-use 858.** (Agency bodies are inherently development/finance, so substantive RDA/MBA
motions also receive an application — see `application_worthy` in `build_db.py`.)

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA/MBA), and PC←agency — though in West Jordan every reconstructed link is **Council ←
PlanningCommission** (the classic PC→Council referral): the RDA/MBA's 36 applications carry no shared
addresses (0 of 36 cite a grid pair) and no shared subjects with the land-use corpus, so there are
**0 agency referrals** here. Grain = application↔application; motions/votes inherit the link through
`v_referral_chain`.

### `referral` table columns
| column | notes |
|---|---|
| `referral_id` | PK |
| `primary_application_id` → `application` | the more-authoritative side (Council here) |
| `primary_body` | denormalized body name of the primary |
| `related_application_id` → `application` | the lower-authority origin (PC here) |
| `related_body` | denormalized body name of the related |
| `match_method` | ∈ `address \| subject \| address+subject \| override` |
| `confidence` | ∈ `high \| medium \| low` |
| `shared_address` | the matched grid pair / named-street address(es), `;`-joined |
| `subject_score` | IDF-weighted title agreement (0–1; name-anchored containment folded in) |
| `primary_date`, `related_date`, `gap_days` | the Council decision date, the PC origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`5891 w 7000 s`) or named-street address
  (`1986 w gardner`). **WJ nuance:** these are *approximate grid intersections / block addresses*,
  i.e. whole street crossings, **not parcel addresses** — so address **+ title agreement** → `high`
  (≈exact), but an **intersection match alone** (negligible subject overlap) → `low` (co-location
  only; review).
- **subject** — IDF-weighted title agreement, two measures: *symmetric* IDF Jaccard (≥0.30) carries
  the address-less **policy/code-amendment** referrals; *asymmetric name-anchored containment* (≥0.50)
  catches a terse council title wholly covered by a richer PC title. IDF down-weights the ubiquitous
  "rezone/amendment/subdivision" boilerplate so distinctive project **names** dominate. A *specific*
  shared code section (`13-5B-8`; never a bare "Title 13") reinforces.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack); for agency pairs it would be
  **symmetric** (±400 days, since financing/project-area can precede or follow the land-use action).
  A candidate failing the gate is rejected. WJ's linked `gap_days` run **−7 → 112** (avg ≈ 39) — PC
  rec a few weeks to a few months before the Council decision, as expected.
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. (Currently empty — the reconstruction stands on its own; the medium
  links were reviewed weakest-first and all proved to be true positives, so none were suppressed.)

### Confidence
- **high** — full-grid address **+ title agreement** + temporal (clean rezones/subdivisions).
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal (named items + code amendments).
- **low** — grid-intersection / block-address co-location only, gate-uncertain, or a secondary origin
  — kept but **flagged**.

### Resolution (prevents false fan-out)
Per Council item the best PC origin in each related body wins; secondaries are kept only when
address+subject is high or a strong subject score sits within 80% of the best.

### Current build (West Jordan)
**160 Council land-use/policy applications · 97 PC applications · 21 referral links**
(**8 high · 9 medium · 4 low**) — all **Council ← PlanningCommission**. By method:
**address+subject 8 · subject 9 · address 4.** **20 of 160 (12%)** Council items linked; the other
**140 are correctly UNLINKED**. The low link rate is honest and expected: the PC corpus in the DB is
small (97 applications) because West Jordan's PC minutes are **tally-only** and the per-body vote CSV
emits **only named rows** — so a PC recommendation that drew no named dissent/absentee never reaches
the DB and cannot anchor a referral (see Known limitations). Most unlinked Council items are
annexation-petition acceptances, council-initiated code cleanups, or rezones whose PC recommendation
predates the in-DB PC floor (2022-07). Medium links were eyeballed weakest-first; thresholds were not
lowered. Audit: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
  (WJ's are all the PC→Council chain.)
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- 1. Trace a land-use matter PC -> Council (technical recommendation vs political decision):
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, shared_address, gap_days
FROM v_referral_chain ORDER BY confidence DESC, council_date;

-- 2. The high-confidence (address+subject) referrals only, newest first:
SELECT primary_date AS council_date, related_date AS pc_date, gap_days,
       shared_address, subject_score, primary_key, related_key
FROM v_referral_chain WHERE confidence='high' ORDER BY council_date DESC;

-- 3. Kent Shelton's full record across both bodies he served (PC then Council):
SELECT * FROM v_member_record WHERE full_name='Kent Shelton';
```

## Known limitations (honest)
- **West Jordan PC minutes are 100% tally-only.** The minutes print a tally ("passed 6-0 in favor")
  and **never name the affirmative majority**; only the **dissent/abstain/recuse side and named
  absentees** are recorded. So **no PC `Aye` rows exist** in the DB — the 307 PC votes are
  **42 Nay · 3 Abstain · 262 Absent**. Within-body PC vote counts therefore reflect *recorded dissent
  + attendance only*, not full roll calls — this is correct and honest, not a parsing gap.
- **The DB covers a subset of PC motions by construction.** `planning_commission/all_votes.csv` emits
  **only named-member rows**, so a PC motion that named nobody (full attendance, unanimous, no
  dissent) produces no CSV row and is **absent from the DB**. The DB holds the **203** PC motions that
  name ≥1 member across **49** meetings; the **fuller PC subtree** (`planning_commission/votes/*.json`
  + minutes) has **84 meetings / 384 motions** (see `planning_commission/votes/_validation_report.txt`).
  This also depresses referral recall (the 12% linked figure is a floor, not a ceiling).
- **36 of 84 PC minutes are OCR'd scans** (`format=ocr` in `planning_commission/minutes_index.csv`,
  2024-02 → 2025-07). OCR parse quality was validated on par with born-digital (0 tally mismatches),
  but treat OCR-era titles with slightly more caution.
- **No standalone PC meetings exist in 2020–2021** — only **4 joint City Council + PC work sessions**
  (2020-09-29, 2021-03-31, 2021-08-31, 2022-08-30), which are discussion-only (0 PC motions). The
  earliest PC votes in the DB are **2022-07-19**.
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings are
  heuristic (the prose resolver) — exact only at the `singleton`/`override` tiers; correct mis-merges
  in `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  `high` (address+subject) ≈ exact; `medium` (subject) is strong but **spot-check before quoting**;
  `low` is flagged. Correct mistakes in `referral_overrides.csv` and rerun.
- WJ addresses are **approximate grid intersections / block addresses**, so address co-location can
  cluster several distinct matters at one crossing — real relatedness, kept (and confidence-flagged),
  not a 1:1 parcel map.
- `person` identity is **name-based** (normalized full name), not a verified registry; `role` is
  *observed from recorded votes*, not an authoritative term roster. (E.g. roster.csv lists Pamela Bloom
  as an early PC member, but she cast no recorded PC dissent/absence, so she carries no PC `role` here.)
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs).
</content>
</invoke>


## Vote-conflict overrides — `db/vote_overrides.csv` (2026-07-02, plan item 3.1)

The flat `all_votes.csv` files are city-faithful/verbatim: where the source minutes list
a member under BOTH the AYES and NAYS/ABSTAIN/ABSENT labels (clerk duplication in the
source), the CSV carries two contradictory rows for one (motion, person). `build_db.py`
previously collapsed these via `INSERT OR IGNORE` (keeping whichever row came first —
arbitrary). It now requires a documented resolution in **`db/vote_overrides.csv`**
(`source_file,motion_no,member,date,claimed_values,resolution,reasoning`; resolution is
a legal vote value or `exclude`) and FAILS THE BUILD on any conflict not covered — rows
are never silently dropped. Identical duplicate rows still merge silently. Every build
prints the reconciliation (named CSV rows = inserted + merged + excluded + unresolvable).
The flat CSV keeps both verbatim rows; only the db's single-vote grain uses the
resolution. (Pattern shared with `park_city_city_council/db/`.)

### `v_contested` column shape (2026-07-19 — mirrors cities.db `v_contested_all`)

Membership is UNCHANGED (a motion with any **named** Nay/Abstain/Recuse row), but the view
now exposes the split count families plus the normalization fields, backed by a per-db
**`motion_std`** table (this city's `motions_std.csv` files loaded + joined to `motion`):

- **`tally_aye` / `tally_nay` / `tally_other`** — AUTHORITATIVE margins from `motion_std`
  (printed tallies), falling back to the named counts only where no std tally exists.
  `tally_other` is NULL-encoded upstream (a bare "A:N" source prints no third number — the
  vote ROW is the authority for abstentions), so the fallback supplies the named
  abstain/recuse count. **Use these for margins.**
- **`named_ayes` / `named_nays` / `named_abstains` / `named_recuses`** — who was actually
  NAMED; attribution only (they undercount under dissent-only/tally-only recording).
- **`motion_type_std`**, **`land_use_type`**, **`vote_mode`**, **`motion_no`**,
  **`provenance`** (NULL in dbs whose motion table doesn't carry the column).
