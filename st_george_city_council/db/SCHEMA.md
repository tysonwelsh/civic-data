# St. George City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ RDA** votes by real keys instead of fuzzy text matching. Built
reproducibly in **two stages**; the `db/tables/` CSVs are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The St. George reality (why this is the prose-portal model, not Legistar's)
St. George publishes **PDF/prose minutes** (Revize 2022+ born-digital, Utah Public Notice backfill for
2020–21; the PC adds Revize 2024+ vs PMN 2020–23). There is **no Legistar API, no structured
agenda/matter key, and essentially no file/application number in the motion text** — PC motions often
only cite an agenda "Item 2A". So the project key is **resolved from prose** by a tiered, auditable
resolver — not read from a vendor field. St. George also gives **no shared key across bodies**:
`build_db.py` reports **0 applications spanning >1 body**, by construction (see below). The cross-body
relationship is therefore **reconstructed** (`referral`), never looked up.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council "Auburn Hills" and a PC "Auburn Hills" are **distinct** application rows — never merged.
   `application` therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA / ArtsCommission / Canvass; `kind` ∈ council/agency/commission/committee/department |
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
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` (**present in St. George:** Pass 2,767, Fail 12 —
  the source `result` strings encode continuances as motion text/type, not as an outcome word, so
  Continued/Died are 0 here)
- `motion.stage` ∈ `council_vote | rda_vote | pc_recommendation | pc_final_action | other_action`
  (the schema also allows `mba_vote | ha_vote | boa_action`; **stages present in St. George:**
  council_vote 1,767 · pc_recommendation 674 · pc_final_action 331 · rda_vote 3 · other_action 4)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused`

### Build totals (current)
**5 bodies · 63 persons · 394 meetings · 1,552 applications · 2,779 motions · 14,629 votes · 48 roles.**
Motions by body: **Council 1,765 · PlanningCommission 1,005 · ArtsCommission 4 · RDA 3 · Canvass 2.**
Applications by body: **Council 836 · PlanningCommission 713 · RDA 3.** PC stages: **674 recommendations**
(663 Positive / 11 Negative) + **331 final actions** (CUP/site-plan/hillside — never reach Council).
Contested (any Nay/Abstain/Recuse): **Council 85 · PC 88.** **4 people served on both the Council and
the PC** (commissioners later elected, or vice-versa — unified by name in `person`/`role`).
Coverage **2020-01-06 → 2026-06-09**. (The PC corpus has 1,006 motion blocks; one names-recorded-false
adjourn contributes no vote rows, so 1,005 PC motions land in the DB.)

## Project resolution — TIERED + AUDITABLE (the within-body key)
St. George has no PL#/file number, so each **land-use/policy** motion's `application_id` is resolved in
tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces it.
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized
   name (e.g. *Auburn Hills Phase 7B*, *Desert Playa*, *Knetta's Knoll*). The workhorse tier but
   heuristic — **treat name groupings as provisional** and correct via `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   acreage rezones/GPAs, code/text amendments, unnamed plats) becomes its **own** application (exact
   identity, one motion = one application), `name` NULL. PC motions that cite only "Item 2A" land here.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 232 · `singleton` 1,340**; **NULL/non-land-use 1,207.**
(St. George leans heavily on `singleton` because PC motion text usually names only an agenda item, not
the project; the rich project string lives in the Council twin and in `application.rep_title`.)

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA), and PC←agency — though in St. George every reconstructed link is **Council ← PlanningCommission**
(the classic PC→Council referral): the RDA's 3 applications share no addresses/subjects with the
land-use corpus, so there are **0 agency referrals** here. Grain = application↔application; motions/votes
inherit the link through `v_referral_chain`.

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
| `primary_date`, `related_date`, `gap_days` | the Council date, the PC date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`. (Body-agnostic columns —
`primary_application_id/primary_body/related_application_id/related_body` — replace any
`council_*/pc_*` legacy pair.)

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`1276 s black ridge`) or named-street
  address. **St. George nuance:** Council minutes are richly addressed (**198 of 836** Council
  land-use apps carry an address), but PC motions usually cite only "Item 2A" (**29 of 713** PC apps
  carry an address). So address evidence is mostly one-sided; a two-sided address match + title
  agreement → `high` (≈exact), but an **address match alone** (negligible subject overlap) → `low`
  (co-location only; review).
- **subject** — IDF-weighted title agreement, two measures: *symmetric* IDF Jaccard (≥0.30) and
  *asymmetric name-anchored containment* (≥0.50) for a terse title wholly covered by a richer one.
  IDF down-weights the ubiquitous "preliminary plat / hillside permit / conditional use / residential
  subdivision" boilerplate so distinctive project **names** dominate. This is the **workhorse** signal
  in St. George (the PC side rarely carries an address). A *specific* shared code section reinforces.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack); a candidate failing the gate is
  rejected (or kept at `low` only if its subject score ≥0.6). All `high`/`medium` gaps fall in the
  −54 … +389-day window; the few extreme gaps (e.g. −1,881) live only in `low` (same-name match in a
  different episode, flagged).
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent.

### Confidence
- **high** — full address **+ title agreement** + temporal (clean addressed rezones/subdivisions), or a
  manual `override` link.
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal (named developments and
  policy/code amendments) — the bulk of St. George's links.
- **low** — address co-location only, gate-failing same-name match, or a secondary origin — kept but **flagged**.

### Resolution (prevents false fan-out)
Per Council item the best origin in each related body wins; secondaries are kept only when
address+subject is high or a strong subject score sits within 80% of the best — which legitimately
preserves one **development episode spanning several PC matters** (e.g. concept hillside permit + zone
change + preliminary plat, each its own PC action, for the same project — see Desert Playa, Knetta's Knoll).

### Current build (St. George)
**836 Council land-use/policy applications · 713 PC applications · 117 referral links**
(**15 high · 92 medium · 10 low**) — all **Council ← PlanningCommission**. By method:
**subject 97 · address+subject 12 · address 5 · override 3.** **108 of 836 (13%)** Council items are
linked to ≥1 PC matter; the other **728 are correctly UNLINKED** (non-land-use, PC origin pre-2020 data
floor, council-initiated code cleanups, PC final-action items that never reached Council, or
name-divergent matters). The **medium set was eyeballed weakest-first** and tuned via overrides
(**30 suppress + 3 link**), not by lowering template thresholds. Common false positives suppressed:
cross-phase Auburn Hills plats, short-term-rental "designated landmark" CUP boilerplate matching
different landmarks, and co-located-but-distinct Desert Canyons/Desert Reserve subdivisions. Audit:
`db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- 1) Trace land-use matters PC -> Council (technical recommendation vs political decision):
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, shared_address, gap_days
FROM v_referral_chain
ORDER BY confidence DESC, council_date;

-- 2) The full within-body life of one project (every stage/outcome/dissenters), e.g. Auburn Hills:
SELECT app_key, body, date, stage, outcome, recommendation, dissenters
FROM v_project_timeline
WHERE app_key LIKE '%auburn hills%'
ORDER BY date;

-- 3) A member's record (a commissioner-then-councilmember shows two rows, one per body):
SELECT * FROM v_member_record WHERE full_name = 'Nathan Fisher';
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings are
  heuristic (the prose resolver) — exact only at the `singleton`/`override` tiers; correct mis-merges
  in `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  `high` (address+subject / override) ≈ exact; `medium` (subject) is strong but **spot-check before
  quoting**; `low` is flagged. Correct mistakes in `referral_overrides.csv` and rerun.
- **PC minutes are two-vintage:** Revize 2024+ born-digital vs PMN 2020–23, with 2020–21 layout
  fragmentation (page-break-split roll calls, stale templates) — see `planning_commission/CLAUDE.md`.
  PC motion text usually names only an agenda "Item N", which is why most PC applications are
  `singleton`s and why the referral join leans on **subject** (IDF title) rather than address.
- **Addresses are mostly Council-side** and often **approximate grid intersections**, so address
  co-location can cluster several distinct matters at one crossing — kept (and confidence-flagged),
  not a 1:1 parcel map.
- `person` identity is **name-based** (normalized full name), not a verified registry; the 4
  Council↔PC overlaps are by name match. `role` is *observed* from votes, not an authoritative roster.
- Of the 11 PC **Negative** recommendations, **none link to a subsequently-passed Council item** — the
  classic "PC said no, Council approved anyway" divergence does not occur in the linked St. George set
  (negative recs were not forwarded to a Council approval, or their Council twin predates the floor).
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs).


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
