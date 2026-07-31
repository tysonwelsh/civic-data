# Nephi City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ Community Reinvestment Agency (CRA)** actions by real keys instead of
fuzzy text matching. Built reproducibly in **two stages**; the `db/tables/` CSVs are exports of each
table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Nephi reality (small rural, NARRATIVE-dominant, prose portal)
Nephi (Juab County seat, ~6,500) publishes minutes through **CivicPlus as PDF/prose** — there is **no
Legistar API, no structured agenda/matter key, and no file/application number in the motion text**. So
the project key is **resolved from prose** by a tiered, auditable resolver — not read from a vendor
field. Nephi gives **no shared key across bodies** either (`build_db.py` reports **0 applications
spanning >1 body**, by construction). The cross-body relationship is therefore **reconstructed**
(`referral`), never looked up.

**Narrative-vote caveat (important, honest).** Nephi records most actions as narrative tallies
("motion passed unanimously"), naming a mover/seconder but **not** the individual voters. Only **58 of
1,249 motions** name per-member votes (Council 46 · PlanningCommission 12 · CRA 0); the other **1,191
are tally-only** (`names_recorded=0`). The `vote` table therefore holds just **259 member-vote rows**.
This is a real property of the source, not a parsing gap — it limits *within-body per-member* analysis
(use `mover`/`seconder` + `result_raw`/`outcome` for those motions) but does **not** affect the
referral layer, which matches on motion **title text**, not on who voted.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every motion ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped). A
   Council "Bryce's Landing" and a PC "Bryce's Landing" are **distinct** application rows — never
   merged. `application` therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / CRA (Community Reinvestment Agency); `kind` ∈ council/agency/commission |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title (rich tokens for the referral layer) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized. Sparse in Nephi (narrative voting — see caveat) |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) — only people who appear in recorded votes |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` (**present in Nephi:** Pass 1,252 · Fail 1)
- `motion.stage` ∈ `council_vote | rda_vote | pc_recommendation | pc_final_action` (the schema also
  allows `mba_vote | ha_vote | boa_action | other_action`; **stages present in Nephi:** council_vote
  917 · pc_final_action 236 · pc_recommendation 95 · rda_vote 1 (the single 2021 CRA action))
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the
  rec; **93 Positive / 2 Negative**, the other 236 PC motions are final actions with no rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused` (**present:** Aye 199 · Nay 36
  · Absent 21 · Abstain 2 · Recuse 1)

### Build totals (current)
**3 bodies · 24 persons · 258 meetings · 225 applications · 1,249 motions · 259 votes · 20 roles · 18
referrals.** Motions by body: **Council 917 · PlanningCommission 331 · CRA 1.** Applications by body:
**Council 120 · PlanningCommission 104 · CRA 1.** PC stages: **95 recommendations** (93 Positive / 2
Negative — forwarded to Council) + **236 final actions** (CUP/site-plan/concept — never reach
Council). Contested (any Nay/Abstain/Recuse, only visible on named motions): **Council 22 · PC 11.**
**0 people served on both Council and the PC** in the recorded-vote window (roles: Council 11 · PC 9).
Coverage 2020-01-07 → 2026-06-09 (PC 2020-01-08 → 2026-02-11).

> Note on PC subtree vs DB: the `planning_commission/` subtree documents **70 recovered meetings** and
> a **13-commissioner roster** (from attendee headers). The DB shows **63 PC meetings** (only the ones
> that produced at least one motion) and **9 PC roles** (only commissioners who appear in a *named*
> vote — the narrative majority leaves most commissioners off per-member rows). Both are honest; they
> count different things.

## Project resolution — TIERED + AUDITABLE (the within-body key)
Nephi has no PL#/file number, so each **land-use/policy** motion's `application_id` is resolved in
tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild. *(Currently none for Nephi.)*
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized name
   (e.g. *North Ridge Estates*, *Bryce's Landing*, *Reed Ridge*, *222 Business Park*). Heuristic —
   **treat name groupings as provisional** and correct via `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   acreage rezones/GPAs, code/text amendments, unnamed plats) becomes its **own** application: exact
   identity (one motion = one application), `name` NULL. Kept granular so each links to its **specific**
   prior PC recommendation in the referral layer.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 78 · `singleton` 164**; **NULL/non-land-use 1,011.**

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency/CRA**)
and a `related_body`. The model is **generalized** — it covers Council←PlanningCommission,
Council←CRA, and PC←CRA — though in Nephi every reconstructed link is **Council ← PlanningCommission**
(the classic PC→Council referral): the single CRA application carries no shared address/subject with
the land-use corpus, so there are **0 agency referrals** here. Grain = application↔application;
motions/votes inherit the link through `v_referral_chain`.

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

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`100 n 200 w`) or named-street address.
  **Nephi nuance:** these are *approximate grid intersections* (whole street crossings, **not parcel
  addresses**); and Nephi minutes are address-poor — only **1 Council + 3 PC** applications carry any
  parsable address and **0 are shared council↔non-council**, so in practice **no Nephi link uses
  address** (all 18 are subject-based).
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) carries address-less
  policy/code referrals; *asymmetric name-anchored containment* (≥0.50) catches a terse Council title
  wholly covered by a richer PC title. IDF down-weights ubiquitous "plat/subdivision/rezone"
  boilerplate so distinctive project **names** dominate.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within 400 days, 60-day forward slack); for CRA pairs it would be
  **symmetric** (±400 days). A candidate failing the gate is rejected. Nephi link gaps run **6–328
  days** (mean ≈ 64).
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. **Nephi has 2 `suppress` rows** (two clear false positives killed —
  see tuning below).

### Confidence
- **high** — full-grid address **+ title agreement** + temporal. *(None in Nephi — address-poor source.)*
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal. **All 18 Nephi links.**
- **low** — grid-intersection co-location only / gate-uncertain / secondary — kept but **flagged**. *(None in Nephi.)*

### Current build (Nephi) — and the honest tuning
**120 Council land-use/policy applications · 104 PC applications · 18 referral links** — all **medium**,
all **subject**, all **Council ← PlanningCommission**. **11 of 120 (9%)** Council items linked; the
other **109 are correctly UNLINKED** (small city: most council motions are budget/appointments/
procedural with no land-use counterpart, plus a few PC origins predating the 2020 floor or
council-initiated items). All `medium` links were dumped weakest-first from `db/referrals_audit.csv`
and eyeballed. Two false positives were **suppressed** via `db/referral_overrides.csv`:
- Council *Development Agreement with **Wright Direction LLC*** vs PC *rezone by **Mt. Peak Development
  LLC*** — different developers, matched only on generic tokens.
- Council *North Ridge Estates Phase C* rezone vs PC *Loveless Estates Vicinity Plan* — different
  developments, matched on generic `zone`/`PUD` tokens.

No obvious *misses* were found (a token scan turned up no unlinked cross-body pair sharing a
distinctive project name within the temporal gate). Template thresholds were **not** lowered. Audit:
`db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`,
  `gap_days`. (Nephi's are all the PC→Council chain.)
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies (sparse — narrative voting). · **`v_contested`**
  — motions with any Nay/Abstain/Recuse.

```sql
-- Trace a land-use matter PC -> Council (technical recommendation vs political decision):
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, gap_days, subject_score
FROM v_referral_chain ORDER BY primary_date;

-- The Planning Commission's recommendation mix (Positive vs Negative) and final actions:
SELECT stage, recommendation, COUNT(*) AS motions
FROM motion mo JOIN body b USING(body_id)
WHERE b.name='PlanningCommission' GROUP BY stage, recommendation ORDER BY stage;

-- Contested council motions (the named-dissent signal) with the dissenters:
SELECT m.meeting_date, mo.motion_text,
       group_concat(p.full_name || ' (' || v.vote_value || ')', '; ') AS dissent
FROM motion mo JOIN meeting m ON m.meeting_id=mo.meeting_id JOIN body b ON b.body_id=mo.body_id
JOIN vote v ON v.motion_id=mo.motion_id AND v.vote_value IN ('Nay','Abstain','Recuse')
JOIN person p ON p.person_id=v.person_id
WHERE b.name='Council' GROUP BY mo.motion_id ORDER BY m.meeting_date;
```

## Known limitations (honest)
- **Narrative voting dominates.** Only 58 of 1,249 motions name per-member votes; the `vote` table
  (259 rows) and the `role`/`v_member_record` tables are correspondingly sparse. For the 1,191
  tally-only motions use `mover`/`seconder` + `result_raw`/`outcome`. This is the source's nature, not
  a gap.
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings are
  heuristic (the prose resolver) — exact only at the `singleton`/`override` tiers; correct mis-merges
  in `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  All Nephi links are `medium` (subject-only, the source is address-poor) — **strong but spot-check
  before quoting**. Correct mistakes in `referral_overrides.csv` and rerun.
- **Small city → few referrals (18) is expected and honest**, not a coverage failure. Most council
  business has no land-use counterpart; 9% of council apps linking is the real shape of a town this
  size.
- Nephi addresses are **approximate grid intersections** when present at all, and are too sparse here
  to drive any link.
- `person` identity is **name-based** (normalized full name), not a verified registry; `role` is
  *observed* from recorded votes, not an authoritative term roster (so it undercounts commissioners
  given narrative voting). Two distinct **Worwood**s exist on the council — kept separate by full name.
- This DB covers **votes/motions**; it does not model public comments or elections (those remain in
  their CSVs).

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
