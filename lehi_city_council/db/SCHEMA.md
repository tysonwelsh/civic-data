# Lehi City civic database — schema & data dictionary

`db/lehi.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ Local Building Authority (MBA)** votes by real keys instead of fuzzy text
matching. Built reproducibly in **two stages**; the `db/tables/` CSVs are exports of each table
(for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Lehi reality (why this is the prose-portal model, not Legistar's)
Lehi's portal is **Granicus ViewPublisher PDF-prose** — there is **no Legistar API, no structured
agenda/matter key, and essentially no file/application number in the motion text**. So the project key
is **resolved from prose** by a tiered, auditable resolver — not read from a vendor field. Crucially,
Lehi gives **no shared key across bodies** either (empirically verified: 0 shared file numbers;
`build_db.py` reports **0 applications spanning >1 body**, by construction — see below). The cross-body
relationship is therefore **reconstructed** (`referral`), never looked up.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council "Holbrook Farms" and a PC "Holbrook Farms" are **distinct** application rows — never
   merged. `application` therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / MBA (Local Building Authority) / PlanningCommission; `kind` ∈ council/agency/commission |
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
- `motion.outcome` ∈ `Pass | Fail | Continued | Died`
- `motion.stage` ∈ `council_vote | mba_vote | pc_recommendation | pc_final_action` (the schema also
  allows `rda_vote | ha_vote | boa_action | other_action`; **stages present in Lehi:** council_vote,
  mba_vote, pc_recommendation, pc_final_action — Lehi's in-council RDA recesses are empty, so no `rda_vote`)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused`

### Build totals (current)
**3 bodies · 27 persons · 281 meetings · 1,407 applications · 2,342 motions · 12,362 votes · 36 roles.**
(Rebuilt 2026-07-02 after the duplicate-Granicus-event dedup — see ../VERIFICATION.md addendum.)
Motions by body: **Council 1,245 · PlanningCommission 1,089 · MBA 8.** Applications by body:
PlanningCommission 862 · Council 540 · MBA 5. PC stages: **661 recommendations** (616 Positive / 45
Negative) + **428 final actions** (CUP/site-plan/design — never reach Council). Contested (any
Nay/Abstain/Recuse): Council 99 · PC 140. **8 people served on both the Council and the PC**
(commissioners later elected — unified by name in `person`/`role`). Coverage 2020-01-09 → 2026-05-28.

## Project resolution — TIERED + AUDITABLE (the within-body key)
Lehi has no PL#/file number, so each **land-use/policy** motion's `application_id` is resolved in
tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild.
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized
   name (e.g. *Holbrook Farms Plat H*, *Refractory Annexation*, *Jonsson Park Towns Zone Change*).
   This is the workhorse tier; the extractor is tuned to Lehi's title shapes but is heuristic —
   **treat name groupings as provisional** and correct via `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   acreage rezones/GPAs, **code/text amendments**, unnamed street vacations) becomes its **own**
   application: exact identity (one motion = one application, no cross-motion inference), `name` NULL.
   Code/text amendments are deliberately kept granular here so each links to its **specific** prior
   PC recommendation in the referral layer.
4. **(NULL)** — non-land-use motions (budget, appointments, employee policy, contracts, procedural,
   ceremonial) get **no** application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 798 · `singleton` 779**; **NULL/non-land-use 828.**

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA/MBA/HA where present), and PC←agency — though in Lehi every reconstructed link is **Council ←
PlanningCommission** (the classic PC→Council referral): MBA's 5 applications carry no shared
addresses/subjects with the land-use corpus, so there are **0 agency referrals** here. Grain =
application↔application; motions/votes inherit the link through `v_referral_chain`.

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
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`. (This **replaces** the old
`(council_application_id, pc_application_id)` columns — the table is now body-agnostic.)

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`2100 n 2300 w`) or named-street address.
  **Lehi nuance:** these are *approximate grid intersections* ("located at approximately …"), i.e.
  whole street crossings, **not parcel addresses** — one big master-planned site clusters many
  distinct matters at one crossing. So address **+ title agreement** → `high` (≈exact), but an
  **intersection match alone** (negligible subject overlap) → `low` (co-location only; review).
- **subject** — IDF-weighted title agreement, two measures: *symmetric* IDF Jaccard (≥0.30) carries
  the address-less **policy/code-amendment** referrals; *asymmetric name-anchored containment* (≥0.50)
  catches a terse council title wholly covered by a richer PC title. IDF down-weights the ubiquitous
  "development/code/amendment/subdivision" boilerplate so distinctive project **names** dominate. A
  *specific* shared code section (`05.030`, `37.080`; never a bare "Chapter 37") reinforces.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack); for agency pairs it would be
  **symmetric** (±400 days, since financing/project-area can precede or follow the land-use action).
  A candidate failing the gate is rejected.
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. (Currently empty for Lehi — the reconstruction stands on its own.)

### Confidence
- **high** — full-grid address **+ title agreement** + temporal (clean rezones/subdivisions/annexations).
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal (named items + policy/code amendments).
- **low** — grid-intersection co-location only, gate-uncertain, or a secondary origin — kept but **flagged**.

### Resolution (prevents false fan-out)
Per primary item the best origin in each related body wins; secondaries are kept only when
address+subject is high or a strong subject score sits within 80% of the best — which legitimately
preserves one **development episode spanning several PC matters** (e.g. concept → zone change →
preliminary → final, each its own PC recommendation, all at one crossing).

### Current build (Lehi)
**540 Council land-use/policy applications · 862 PC applications · 459 referral links**
(**273 high · 177 medium · 9 low**) — all **Council ← PlanningCommission**. By method:
**address+subject 273 · subject 179 · address 7.** **372 of 540 (68%)** Council items linked;
the other **168 are correctly UNLINKED**, dominated by items whose PC recommendation predates the 2020
data floor (heard by Council in early 2020 but recommended by the PC in 2019), plus council-initiated
code cleanups, annexation agreements following an earlier intent, and a few name-divergent items.
Medium links were eyeballed weakest-first; thresholds were tuned to that review. Audit:
`db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
  (Lehi's are all the PC→Council chain.)
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- Trace a land-use matter PC -> Council (technical recommendation vs political decision):
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, shared_address
FROM v_referral_chain WHERE confidence='high' ORDER BY primary_date;

-- Where the PC said NO but the Council approved anyway (the technical-vs-political divergence):
SELECT pri.rep_title, p.meeting_date AS pc_date, c.meeting_date AS council_date
FROM referral r
JOIN motion pm ON pm.application_id=r.related_application_id AND pm.recommendation='Negative'
JOIN meeting p ON p.meeting_id=pm.meeting_id
JOIN application pri ON pri.application_id=r.primary_application_id
JOIN motion cm ON cm.application_id=pri.application_id AND cm.outcome='Pass'
JOIN meeting c ON c.meeting_id=cm.meeting_id;

-- A commissioner-then-councilmember's full record across both bodies:
SELECT * FROM v_member_record WHERE full_name='Michelle Stallings';
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings are
  heuristic (the prose resolver) — exact only at the `singleton`/`override` tiers; correct mis-merges
  in `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  `high` (address+subject) ≈ exact; `medium` (subject) is strong but **spot-check before quoting**;
  `low` is flagged. Correct mistakes in `referral_overrides.csv` and rerun.
- Lehi addresses are **approximate grid intersections**, so address co-location can cluster several
  distinct matters at one crossing — real relatedness, kept (and confidence-flagged), not a 1:1 map.
- `person` identity is **name-based** (normalized full name), not a verified registry; the 8
  Council↔PC overlaps are by name match. `role` is *observed* from votes, not an authoritative term roster.
- Council-*initiated* policy (Council starts a code amendment the PC hears afterward, or the PC origin
  predates the 2020 floor) will not link — by design. The 174 unlinked Council items are a feature, not a failure.
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs).
</content>
</invoke>

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
