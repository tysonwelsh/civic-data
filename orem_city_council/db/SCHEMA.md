# Orem City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **City Council ↔
Planning Commission ↔ Redevelopment Agency (RDA) ↔ Municipal Building Authority (MBA) ↔ Special
Service Lighting District (SSLD)** votes by real keys instead of fuzzy text matching. Built reproducibly
in **two stages**; the `db/tables/` CSVs are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Orem reality (why this is the prose-portal model, not Legistar's)
Orem's portal is **CivicClerk / Google-Drive PDF-prose** — there is **no Legistar API, no structured
agenda/matter key, and essentially no file/application number in the motion text**. So the project key
is **resolved from prose** by a tiered, auditable resolver — not read from a vendor field. Orem also
gives **no shared key across bodies**: the cross-body relationship is therefore **reconstructed**
(`referral`), never looked up — `build_db.py` reports **0 applications spanning >1 body**, by construction.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council "Stewart Retail Addition" and a PC "Stewart Retail Addition" are **distinct** application
   rows — never merged. `application` therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA / MBA / SSLD; `kind` ∈ council/agency/commission |
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
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` (**present in Orem:** Pass 1,052 · Fail 15)
- `motion.stage` ∈ `council_vote | rda_vote | mba_vote | ha_vote | boa_action | other_action |
  pc_recommendation | pc_final_action` (**stages present in Orem:** council_vote 550, pc_final_action
  390, pc_recommendation 111, rda_vote 15, mba_vote 1 — SSLD's 9 motions take `council_vote` by its
  `kind`)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused` (**present in Orem:** Aye 6,568 ·
  Nay 170 · Abstain 8 — Orem minutes record only Aye/Nay/Abstain in prose, no recuse/absent vote rows)

### Build totals (current — queried)
**5 bodies · 52 persons · 237 meetings · 296 applications · 1,067 motions · 6,746 votes · 58 roles · 29 referrals.**
Motions by body: **Council 541 · PlanningCommission 501 · RDA 15 · SSLD 9 · MBA 1.** Applications by
body: **PlanningCommission 216 · Council 72 · RDA 7 · MBA 1** (SSLD 0 — its motions are budget/minutes,
no land use). Votes by body: Council 3,602 · PC 2,997 · RDA 91 · SSLD 51 · MBA 5. PC stages: **111
recommendations** (100 Positive / 11 Negative — forwarded to Council) + **390 final/other actions**
(CUP/site-plan/plat finals the PC disposes itself, plus PC procedural motions — never reach Council).
Contested (any Nay/Abstain): Council 49 · PC 34. **0 people served on both the Council and the PC** in
this window (no commissioner was later elected to Council during 2020–2026). Coverage: Council
2020-01-14 → 2026-05-05; PC 2020-01-15 → 2026-05-06.

> **The five bodies.** `Council` is the elected body (mayor + 6, all at-large). `PlanningCommission` is
> the appointed technical land-use body (recommendations vs final actions). `RDA` (Redevelopment
> Agency) and `MBA` (Municipal Building Authority) are finance/development bodies that meet in-council.
> `SSLD` (Special Service Lighting District) is a small district that adopts an annual budget/minutes.

## Project resolution — TIERED + AUDITABLE (the within-body key)
Orem has no PL#/file number, so each **land-use/policy** motion's `application_id` is resolved in tiers;
`app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild. (Currently empty.)
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized name
   (e.g. *Stewart Retail Addition*, *Ken Garff Rezone*, *Whitestone Estates*). Heuristic — treat name
   groupings as provisional and correct via `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   acreage rezones/GPAs, **code/text amendments**, unnamed plats) becomes its **own** application:
   exact identity (one motion = one application). Code/text amendments are kept granular here so each
   links to its **specific** prior PC recommendation in the referral layer.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 42 · `singleton` 255**; **NULL/non-land-use 770.**
(Orem's land-use motions skew un-named — most rezones/plats cite an address rather than a project name —
so `singleton` dominates; this is exact identity, not weaker.)

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter, naming
a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA/MBA), and PC←agency — though in Orem every reconstructed link is **Council ← PlanningCommission**
(the classic PC→Council referral): the RDA/MBA applications carry **no shared addresses or distinctive
subjects** with the land-use corpus (0 of 8 have a grid address), so there are **0 agency referrals**
here. Grain = application↔application; motions/votes inherit the link through `v_referral_chain`.

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

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`166 n 400 w`) or named-street address.
  **Orem nuance:** many minutes give *approximate grid intersections* ("located generally at …"), i.e.
  whole street crossings, **not parcel addresses** — distinct matters can cluster at one crossing. So
  address **+ title agreement** → `high` (≈exact), but an **intersection match alone** (negligible
  subject overlap) → `low` (co-location only; review).
- **subject** — IDF-weighted title agreement, two measures: *symmetric* IDF Jaccard (≥0.30) carries the
  address-less **policy/code-amendment** referrals (Orem's PC↔Council code/General-Plan stream is large
  — Chapter 4 Housing, sign code 14-3-3, the PF zone, etc.); *asymmetric name-anchored containment*
  (≥0.50) catches a terse Council title wholly covered by a richer PC title. IDF down-weights the
  ubiquitous "amendment/code/general plan" boilerplate so distinctive **section numbers/names** dominate.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack); for agency pairs it would be
  **symmetric** (±400 days). A candidate failing the gate is rejected. (Observed `gap_days` here: −57 … 265.)
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. **1 row currently** (a `suppress`, see Tuning below).

### Confidence
- **high** — full-grid address **+ title agreement** + temporal (clean rezones/plats/CUPs/site plans).
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal (code & General-Plan amendments).
- **low** — grid-intersection co-location only, or gate-uncertain — kept but **flagged**.

### Resolution (prevents false fan-out)
Per primary item the best origin in each related body wins; secondaries are kept only when
address+subject is high or a strong subject score sits within 80% of the best — which legitimately
preserves one **policy episode spanning several PC matters** (e.g. the Chapter 4 Housing General-Plan
update, heard by the PC in multiple sections, all feeding the Council ordinance).

### Current build (Orem) + tuning
**72 Council land-use/policy applications · 216 PC applications · 29 referral links**
(**10 high · 17 medium · 2 low**) — all **Council ← PlanningCommission**. By method:
**address+subject 10 · subject 17 · address 2.** **24 of 72 (33%)** Council items linked; the other
**48 are correctly UNLINKED**, dominated by (a) Council→PC *sequences* the directional gate rejects by
design — a Council rezone followed later by a PC plat/subdivision at the same site (e.g. Apple Bud,
Whitestone Estates), (b) items whose PC recommendation predates the 2020 data floor, and (c)
council-initiated/administrative actions with no PC origin.

**Tuning (precision over recall):** every `medium` link was dumped weakest-first from
`db/referrals_audit.csv` and eyeballed; the `high` and `low` links sanity-checked against `gap_days`.
**1 false positive suppressed** in `db/referral_overrides.csv`: a Council rezone at **519** S Geneva Rd
had been linked to a PC development-agreement amendment at **1981** S Geneva Rd — different parcels and
different actions, sharing only the arterial name. (That PC item correctly retains its true link to the
Council *deny the development agreement* motion at 1981 S Geneva, an exact address+subject `high`.) No
template thresholds were lowered. Audit trail: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
  (Orem's are all the PC→Council chain.)
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- 1. Trace a land-use matter PC -> Council (technical recommendation vs political decision):
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, shared_address
FROM v_referral_chain WHERE confidence='high' ORDER BY primary_date;

-- 2. Where the PC sent a NEGATIVE recommendation -> what the Council then did
--    (the technical-vs-political divergence; e.g. the Dunn Rezone the Council approved anyway):
SELECT pri.rep_title AS council_matter, p.meeting_date AS pc_date,
       c.meeting_date AS council_date, cm.outcome AS council_outcome
FROM referral r
JOIN motion pm ON pm.application_id=r.related_application_id AND pm.recommendation='Negative'
JOIN meeting p ON p.meeting_id=pm.meeting_id
JOIN application pri ON pri.application_id=r.primary_application_id
JOIN motion cm ON cm.application_id=pri.application_id
JOIN meeting c ON c.meeting_id=cm.meeting_id;

-- 3. A member's full record (which body, ayes/nays):
SELECT * FROM v_member_record WHERE full_name='Jeff Lambson';
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings (42 motions)
  are heuristic (the prose resolver) — exact only at the `singleton`/`override` tiers; correct
  mis-merges in `overrides.csv` and rebuild (idempotent).
- **The DB ingests the named roll-call subset of `all_votes.csv`.** Orem's PC subtree parsed **562
  motions across 114 meetings**, but only the **501** motions with a *recorded individual roll call*
  appear as rows in `planning_commission/all_votes.csv`; the **61 tally-only** PC motions
  (`names_recorded=false`, no per-member rows — mid-2025 summary minutes), the **11** PC meetings
  composed solely of them, and the 1 motion-less study session (2025-04-02) are therefore **not
  represented** in the DB (PC = 501 motions / 102 meetings here). The Council side has a named
  roll call on every motion, so it is fully represented (566 motions).
- **6 of the 114 PC minutes were OCR'd from image-only scans** (`format=ocr` in
  `planning_commission/minutes_index.csv`), slightly lower text fidelity — occasional garbled tokens
  in `rep_title` (e.g. "dény") flow through to the resolver but do not affect counts.
- The **`referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  `high` (address+subject) ≈ exact; `medium` (subject) is strong but **spot-check before quoting**;
  `low` is flagged. Correct mistakes in `referral_overrides.csv` and rerun.
- **Orem "addresses" are approximate grid intersections** ("located generally at 1230 W 2000 S"), not
  parcel addresses — so address co-location can cluster several distinct matters at one crossing. Real
  relatedness, kept and confidence-flagged, not a 1:1 parcel map.
- `person` identity is **name-based** (normalized full name), not a verified registry; `role` is
  *observed* from votes, not an authoritative term roster.
- Council→PC *sequences* (a rezone the Council passes first, the PC plats afterward) do **not** link —
  the referral gate is directional (PC must precede Council). The 48 unlinked Council items are largely
  this pattern plus pre-2020-floor PC origins — a feature, not a failure.
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
