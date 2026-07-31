# Vineyard City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ RDA** votes by real keys instead of fuzzy text matching. Built reproducibly
in **two stages**; the `db/tables/` CSVs are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Vineyard reality (a small consensus town)
Vineyard is a young, fast-growing but **small, high-consensus** council: contested votes are rare and
the minutes are largely **ALL-CAPS roll-call prose** with terse, boilerplate motion titles. The portal
(CivicClerk) gives **no structured agenda/matter key and no shared key across bodies**, so the project
key is **resolved from prose** and the cross-body relationship is **reconstructed**. Two consequences
to set expectations honestly (both visible in the totals below):
- The ALL-CAPS, name-poor titles defeat the named-project extractor, so almost every application is a
  **singleton** (one motion = one application) rather than a multi-motion **name** group.
- Few projects surface in both bodies with enough shared text to link, so the reconstructed
  **`referral` layer is small** (9 links) — an honest reflection of the corpus, not a bug.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council and a PC matter are **distinct** application rows — never merged. `build_db.py` reports
   **0 applications spanning >1 body**, by construction.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA; `kind` ∈ council/commission/agency |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died`
- `motion.stage` ∈ `council_vote | rda_vote | pc_recommendation | pc_final_action` (the schema also
  allows `mba_vote | ha_vote | boa_action | other_action`; **stages present in Vineyard:** council_vote,
  rda_vote, pc_recommendation, pc_final_action)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused`

### Build totals (current)
**3 bodies · 37 persons · 231 meetings · 129 applications · 1,395 motions · 6,745 votes · 43 roles.**
Motions by body: **Council 1,018 · PlanningCommission 362 · RDA 15.** Applications by body:
PlanningCommission 78 · Council 37 · RDA 14. PC stages: **56 recommendations** (55 Positive / 1
Negative) + **306 final actions** (never reach Council). Contested (any Nay/Abstain/Recuse): Council 49
· PC 5 · RDA 1. **6 people served on more than one body** (unified by name in `person`/`role`).
Coverage 2020-01-08 → 2026-06-09.

## Project resolution — TIERED + AUDITABLE (the within-body key)
Vineyard has no file number, so each **land-use/policy** motion's `application_id` is resolved in
tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild. (Currently none.)
2. **`name`** (medium) — a genuine **named development/rezone** grouped by normalized name. Heuristic;
   correct via `overrides.csv`. **In Vineyard this tier barely fires** — the ALL-CAPS, boilerplate
   titles rarely expose a clean project name.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** becomes its
   **own** application: exact identity (one motion = one application), `name` NULL. Substantive
   (non-procedural) **RDA** motions also get an application so an RDA action can link to a Council/PC
   action on the same site.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — outside the land-use universe and outside referrals.

Current mix (motions with an application): **`singleton` 127 · `name` 2**; **NULL/non-land-use 1,266.**
The overwhelming singleton share is the direct, honest consequence of the ALL-CAPS minutes: identity is
exact (each motion = one application) but cross-motion *name grouping* is mostly unavailable.

## `referral` — the reconstructed, GENERALIZED cross-body linkage
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency/RDA**)
and a `related_body`. The model is **generalized** — it covers Council←PlanningCommission,
Council←RDA, and PC←RDA — though in Vineyard every reconstructed link is **Council ←
PlanningCommission** (RDA's applications share no linkable text with the land-use corpus, so there are
**0 agency referrals**). Grain = application↔application; motions/votes inherit the link through
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
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** or named-street address. As in other Utah
  minutes these are *approximate grid intersections*, so address **alone** is co-location (low);
  reserve high for address **+** subject.
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) carries address-less
  policy/code-amendment referrals; *asymmetric name-anchored containment* (≥0.50) catches a terse title
  wholly covered by a richer one. IDF down-weights boilerplate so distinctive **names** dominate.
- **temporal** — a **gate**, not a stored signal. PC→Council pairs are **directional** (PC must precede
  Council, ~400-day window, 60-day forward slack); agency pairs would be **symmetric** (±400 days). A
  candidate failing the gate is rejected.
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. (Currently empty.)

### Confidence
- **high** — full-grid address **+ subject** + temporal (or an override). · **medium** — strong IDF
  subject + temporal. · **low** — address co-location only / gate-uncertain / secondary — flagged.

### Current build (Vineyard)
**37 Council land-use/policy applications · 78 PC applications · 9 referral links** — **all 9 medium,
all `match_method='subject'`, all Council ← PlanningCommission.** **7 of 37 (19%)** Council items
linked; the rest are correctly **UNLINKED** (no shared-text PC origin in the corpus, or origin predates
the 2020 floor). The small count is honest: a small, consensus council with name-poor minutes yields
few confidently linkable cross-body episodes. Audit: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link: both `app_key`s, both project names, both dates,
  `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- Every reconstructed PC -> Council link (all medium/subject here):
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, subject_score
FROM v_referral_chain ORDER BY primary_date;

-- Within-body timeline for a single matter:
SELECT body, date, stage, outcome, recommendation, dissenters
FROM v_project_timeline WHERE app_key = (SELECT app_key FROM application LIMIT 1);

-- A member's full record across bodies:
SELECT * FROM v_member_record ORDER BY votes DESC LIMIT 10;
```

## Known limitations (honest)
- The **within-body core** is exact. Because the ALL-CAPS minutes seldom expose a project name, almost
  everything is a `singleton` (exact identity, no cross-motion grouping) and the `name` tier is tiny
  (2 motions). Add groupings via `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference** and **small** (9 links, all medium) — a faithful
  reflection of a small, name-poor corpus, not a failure. Spot-check before quoting; correct via
  `referral_overrides.csv`.
- RDA cross-body links: RDA carries 14 applications but shares no linkable address/subject text with the
  Council/PC land-use corpus, so there are **0 agency referrals**.
- `person` identity is **name-based**, not a verified registry; the 6 multi-body overlaps are by name.
  `role` is *observed* from votes, not an authoritative term roster.
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
