# Provo City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **City Council ↔
Redevelopment Agency (RDA) ↔ Planning Commission** votes by real keys instead of fuzzy text matching.
Built reproducibly in **two stages**; the `db/tables/` CSVs are exports of each table (for
diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Provo reality (why this is the prose-portal model, not Legistar's)
Provo's council portal is **Hyland OnBase text PDFs** (`agendas.provo.gov`); the Planning Commission
publishes separately on **AgendaCenter** as **consolidated minutes** (the agenda packet with a
per-application *Report of Action* appended). There is **no Legistar API and no structured matter key
shared across bodies** (empirically verified: `build_db.py` reports **0 applications spanning >1 body**,
by construction). The council minutes carry a parenthetical file id (`(20-089)`) and ordinance/resolution
numbers, but the RDA and the Council reference the same project-area matter by **different instruments**
(an RDA `Resolution 2020-RDA-…` vs a Council `Ordinance/Resolution`), so the within-body project key is
**resolved from prose** and the cross-body relationship is **reconstructed** (`referral`), never looked up.

**Two source quirks shape this DB:**
- **Planning Commission data is 2025+ ONLY.** Provo began publishing consolidated PC minutes in 2025;
  for **2020–2024 the city published no PC minutes** (a documented **source gap**, not a parser gap —
  see `planning_commission/minutes_unrecovered.csv`). So the DB's PC slice is just **26 meetings,
  2025-02-26 → 2026-06-10.**
- **The cross-body link is RDA-side.** Because the PC record is so short and recent, every reconstructed
  referral here is **Council ← RDA** (the RDA/CRA project-area and tax-increment matters the Council
  ratifies) — there are currently **0 Council ← Planning Commission** links.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped). A
   Council item and an RDA item are **distinct** application rows — never merged. `application`
   therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA; `kind` ∈ council/commission/agency |
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
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` — **present in Provo:** Pass 1,127 · Fail 44 · Continued 5.
- `motion.stage` ∈ `council_vote | mba_vote | pc_recommendation | pc_final_action` (the schema also
  allows `rda_vote | ha_vote | boa_action | other_action`). **Stages present in Provo:** `council_vote`
  1,015 · `rda_vote` 59 · `pc_recommendation` 59 · `pc_final_action` 43. Provo's RDA meets separately
  (`rda_vote` populated); there is no MBA/LBA body here.
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the
  rec): **Positive 50 / Negative 9** (= the 59 `pc_recommendation` motions, all 2025+).
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`.
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused` — **present in Provo:** Aye 6,168 ·
  Nay 427 · Absent 321 · Abstain 4. (No Recuse/Excused in the corpus.)

### Build totals (current)
**3 bodies · 24 persons · 288 meetings · 425 applications · 1,176 motions · 6,920 votes · 38 roles.**
Meetings by body: **Council 223 · RDA 39 · PlanningCommission 26.** Motions by body: **Council 1,015 ·
PlanningCommission 102 · RDA 59.** Applications by body: **Council 366 · RDA 42 · PlanningCommission 17.**
PC stages: **59 recommendations** (50 Positive / 9 Negative — to the Municipal Council) + **43 final
actions** (Project Plan/CUP/etc.). Contested (any Nay/Abstain/Recuse): **Council 156 · PC 22 · RDA 4.**
Coverage 2020-01-07 → 2026-06-10 (Council/RDA); **PlanningCommission 2025-02-26 → 2026-06-10 only.**

**Person overlap is mostly the Council wearing the RDA hat.** 13 people serve on >1 body, but 12 are the
**same councilmembers sitting as the RDA board** (Council/RDA) — not separate careers. Only **Jeff
Whitlock** also appears on the Planning Commission (Council/PC/RDA), unified by name in `person`/`role`.

## Project resolution — TIERED + AUDITABLE (the within-body key)
Provo shares no matter key across bodies, so each **land-use/policy** motion's `application_id` is
resolved in tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces it.
2. **`name`** (medium) — a genuine **named development/project-area** grouped by normalized name
   (e.g. *The Mix*, *Freedom Plaza*, *Riverwoods* CRPA). Heuristic — treat as provisional.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   rezones/GPAs, ordinance text amendments) becomes its **own** application: exact identity, `name` NULL.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — correctly outside the land-use universe and outside referrals.

Current mix (all motions): **`singleton` 399 (high) · `name` 29 (medium) · NULL/non-land-use 748.**

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter, naming
a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA), and PC←agency — though in Provo every reconstructed link is **Council ← RDA**: the RDA's
project-area / tax-increment / interlocal resolutions that the Council ratifies by parallel ordinance.
There are **0 Council ← PC** links (the PC record is 2025+ only and its 2025–26 recommendations have not
yet produced a subject-matchable Council pair). Grain = application↔application; motions/votes inherit
the link through `v_referral_chain`.

### `referral` table columns
| column | notes |
|---|---|
| `referral_id` | PK |
| `primary_application_id` → `application` | the more-authoritative side (Council here) |
| `primary_body` | denormalized body name of the primary |
| `related_application_id` → `application` | the lower-authority origin (RDA here) |
| `related_body` | denormalized body name of the related |
| `match_method` | ∈ `address \| subject \| address+subject \| override` |
| `confidence` | ∈ `high \| medium \| low` |
| `shared_address` | the matched grid pair / named-street address(es), `;`-joined (empty for the RDA links — finance matters carry no address) |
| `subject_score` | IDF-weighted title agreement (0–1; name-anchored containment folded in) |
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`. The table is body-agnostic (keyed on
`primary_body`/`related_body`).

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** / named-street address. 114 Council and 12 PC
  applications carry addresses, but the RDA finance/project-area items do **not**, so **0 Provo referrals
  rest on address** — the Council↔RDA tie is carried entirely by subject.
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) and *asymmetric*
  name-anchored containment (≥0.50). IDF down-weights the heavy interlocal-agreement / tax-increment
  boilerplate so the **project-area name** (*The Mix*, *Freedom Plaza*, *Center Street*, *Riverwoods*,
  *City Center*) dominates. The boilerplate is exactly the failure mode audited below.
- **temporal** — a **gate**, not a stored signal. For an **agency↔Council** pair (RDA here) the gate is
  **symmetric** (±~400 days): RDA financing / project-area designation can precede *or* follow the
  Council instrument.
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. In Provo it carries **8 suppress rows** that kill project-area boilerplate
  false positives (below); no forced links were needed.

### Confidence
- **high** — address + subject + temporal. **0 in Provo** (RDA finance items carry no address).
- **medium** — strong IDF subject + temporal (the Provo tier: matched project-area names). **All 12
  Provo links are medium.**
- **low** — co-location only / gate-uncertain / secondary — kept but flagged. **0 in Provo.**

### Resolution (prevents false fan-out)
Per primary item the best origin in each related body wins; secondaries are kept only when a strong
subject score sits within 80% of the best.

### Current build (Provo)
**366 Council land-use/policy applications · 42 RDA applications · 12 referral links** (**all 12
medium**, all `subject`) — all **Council ← RDA**. Only **12 of 366 (3%)** Council items link — the rest
are correctly UNLINKED (most council land-use is rezones/ordinances with no RDA counterpart). The
surviving links are project-area matches where both sides name the same CRA/CDPA (*The Mix*, *Freedom
Plaza*, *Center Street*, *Riverwoods*, *City Center*, the SR-75/Springville street vacation, the West/
Southwest Provo commercial JDA).

**Medium links were eyeballed weakest-first and the boilerplate false positives suppressed** (precision
over recall, recorded in `db/referral_overrides.csv`):
- A **Riverwoods** RDA resolution (app 68) had fanned out to the *Provo Medical School*, *The Mix*, and
  *Center Street* Council items — all distinct project areas matched only on interlocal-agreement
  boilerplate — while its true *Riverwoods* counterpart (app 70) remained. The three wrong pairs were
  suppressed; suppressing them also let the correct **The Mix** RDA origin (app 32) surface for the Mix
  Council resolution (app 31).
- A truncated 2026 RDA resolution (app 408) had fanned out to **four** different rezone ordinances on
  generic vocabulary; all four were suppressed. A second truncated 2026 RDA resolution (app 406)
  similarly over-matched a generic MDR rezone (suppressed) while its plausible same-day *2230 North
  Station Area* pairing was kept.

`INTEGRITY: OK`. Audit: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
  (Provo's are all the Council←RDA chain.)
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- Trace the Council <- RDA referrals (project-area matters the Council ratifies):
SELECT confidence, match_method, related_date AS rda_date, related_project,
       primary_date AS council_date, primary_project, subject_score
FROM v_referral_chain ORDER BY subject_score DESC;

-- A project area's full history across the RDA and the Council:
SELECT body, date, stage, outcome, dissenters, result_raw
FROM v_project_timeline WHERE app_key LIKE '%mix%' OR project LIKE '%Mix%' ORDER BY date;

-- Jeff Whitlock's record across every body he served (Council, RDA, and the Planning Commission):
SELECT * FROM v_member_record WHERE full_name='Jeff Whitlock' ORDER BY body;
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings (29 motions)
  are heuristic; exact only at `singleton`/`override`. Correct mis-merges in `overrides.csv` and rebuild.
- **Planning Commission coverage is 2025+ only** — a documented city source gap for 2020–2024
  (`planning_commission/minutes_unrecovered.csv`), not a parser limitation. Any PC-based cross-body
  analysis is therefore confined to 2025–2026.
- The **`referral` layer is reconstructed inference**, not a looked-up key. All 12 Provo links are
  **medium** (subject-only, no address) — **strong but spot-check before quoting.** The dominant failure
  mode is **project-area boilerplate** (near-identical interlocal-agreement language across different
  CRAs); the audited suppressions remove the clear cases, but truncated 2024/2026 consolidated-minutes
  titles can still under-specify. Correct mistakes in `referral_overrides.csv` and rerun.
- **Few cross-body links by design.** Only 3% of Council items link, and all to the RDA — there is no
  PC→Council chain yet because the PC record starts in 2025. Unlinked Council items are the expected
  majority.
- **Person overlap is mostly hats, not careers.** 12 of the 13 multi-body people are the Council sitting
  as the RDA board; only Jeff Whitlock also served on the PC. `person` identity is name-based; `role` is
  *observed* from votes, not an authoritative term roster.
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs).
</content>


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
