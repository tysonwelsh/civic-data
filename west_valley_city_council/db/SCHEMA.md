# West Valley City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ Redevelopment Agency (RDA) ↔ Municipal Building Authority (MBA)** votes by
real keys instead of fuzzy text matching. Built reproducibly in **two stages**; the `db/tables/` CSVs
are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The West Valley reality (why this is the prose-portal model, not Legistar's)
West Valley's portal is **Hyland OnBase born-digital text PDFs** — there is **no Legistar API and no
structured agenda/matter key**. The minutes *do* carry a **case number** in the motion text
(`Z-…`, `ZT-…`, `GPZ-…`, `PUD-…`, `C-…`, `SMI-…`, `SA-…`, `SV-…`), but the council and the PC use
**different case-number series for the same real-world project** (the PC recommends `PUD-6-2021`; the
Council adopts it as `GPZ-2-2022`), and there is **no shared key across bodies** (empirically verified:
`build_db.py` reports **0 applications spanning >1 body**, by construction). So the within-body project
key is **resolved from prose** by a tiered, auditable resolver, and the cross-body relationship is
**reconstructed** (`referral`), never looked up.

**Thin subject signal (like Logan).** WVC minutes describe land-use items almost entirely by **case
number + a few addresses**, rarely by a named development. So the prose resolver lands almost everything
in the `singleton` tier (one motion = one application, `name` NULL) — only **8** motions group by a real
project *name*. The practical consequence is **few automatic cross-body links**: the trustworthy ties
are hand-verified **exact-case-number overrides**, with the auto-linker contributing only flagged,
low-confidence co-occurrence. This is honest thinness, not a parser gap.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council item and a PC item are **distinct** application rows — never merged. `application`
   therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA / MBA; `kind` ∈ council/commission/agency |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (**NULL for singletons — the WVC norm**); `rep_title`=representative full motion title (carries the case number, the rich token for the referral layer) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` — **present in WVC:** Pass 2,482 · Continued 48 · Fail 18.
- `motion.stage` ∈ `council_vote | mba_vote | pc_recommendation | pc_final_action` (the schema also
  allows `rda_vote | ha_vote | boa_action | other_action`). **Stages present in WVC:** `council_vote`
  1,747 · `pc_final_action` 359 · `pc_recommendation` 247 · `rda_vote` 132 · `mba_vote` 63. Unlike
  Lehi's empty in-council RDA recesses, **West Valley holds separate RDA and MBA meetings**, so both
  `rda_vote` and `mba_vote` are real, populated stages here.
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the
  rec): **Positive 231 / Negative 16** (= the 247 `pc_recommendation` motions).
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`.
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused` — **present in WVC:** Aye 11,296 ·
  Nay 361 · Absent 334 · Recuse 62 · Abstain 2.

### Build totals (current)
**4 bodies · 28 persons · 679 meetings · 559 applications · 2,548 motions · 12,055 votes · 43 roles.**
Meetings by body: **Council 460 · PlanningCommission 134 · RDA 56 · MBA 29.** Motions by body:
**Council 1,747 · PlanningCommission 606 · RDA 132 · MBA 63.** Applications by body: **Council 399 ·
RDA 69 · PlanningCommission 63 · MBA 28.** PC stages: **247 recommendations** (231 Positive / 16
Negative — forwarded to Council) + **359 final actions** (CUP/site-plan/design — never reach Council).
Contested (any Nay/Abstain/Recuse): **Council 208 · PC 57 · RDA 10 · MBA 2.** Coverage 2020-01-07 →
2026-06-09.

**Person overlap is mostly the Council wearing other hats.** 10 people serve on >1 body, but 9 of those
are the **same councilmembers sitting as the RDA and MBA boards** (Council/RDA/MBA) — not separate
careers. Only **Cindy Wood** genuinely spans the *appointed* Planning Commission and the *elected*
Council (commissioner → District 4 councilmember), unified by name in `person`/`role`.

**Note on PC meeting count.** The DB holds **134** PlanningCommission meetings — those that recorded ≥1
motion. The PC subtree (`planning_commission/`) has **263** meeting files total (133 regular + 130
study); **128 discussion-only study meetings record no votes** and therefore produce no DB rows (study
sessions are deliberative; the action votes happen at the regular meeting two days later).

## Project resolution — TIERED + AUDITABLE (the within-body key)
WVC has no shared file number, so each **land-use/policy** motion's `application_id` is resolved in
tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment.
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized name.
   The heuristic workhorse elsewhere, but **near-vestigial in WVC (only 8 motions)** because the minutes
   describe items by case number, not project name.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (the WVC norm:
   case-numbered rezones/PUDs/site plans, code/text amendments) becomes its **own** application: exact
   identity (one motion = one application), `name` NULL. Kept granular so each links to its **specific**
   prior PC recommendation in the referral layer.
4. **(NULL)** — non-land-use motions (budget, appointments, RDA/MBA finance, contracts, procedural,
   ceremonial) get **no** application — correctly outside the land-use universe and outside referrals.

Current mix (all motions): **`singleton` 551 (high) · `name` 8 (medium) · NULL/non-land-use 1,989.**

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA/MBA), and PC←agency — though in West Valley every reconstructed link is **Council ←
PlanningCommission** (the classic PC→Council referral): the RDA's 69 and MBA's 28 applications are
finance/lease matters carrying no shared addresses/subjects with the land-use corpus, so there are
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
| `shared_address` | the matched grid pair / named-street address(es), `;`-joined (empty in WVC — see below) |
| `subject_score` | IDF-weighted title agreement (0–1; name-anchored containment folded in) |
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`. The table is body-agnostic (keyed on
`primary_body`/`related_body`, not a hard-coded council/pc pair).

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`2100 n 2300 w`) or named-street address.
  In WVC this signal is **almost silent**: the minutes give case numbers, not grid intersections, so
  only 1 application carries a parseable address and **0 referrals rest on address**.
- **subject** — IDF-weighted title agreement. The WVC weakness: a case-numbered title strips to a bare
  body-type token (e.g. `PUD`), so two unrelated PUDs can score 1.0 on the collapsed token. These are
  the noise links, kept only at **low** confidence (or suppressed — see below).
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack). A candidate failing the gate is
  rejected (or demoted to low when the gate is ambiguous).
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent. **In WVC this is the backbone:** all 11 high-confidence links are
  hand-verified **exact shared case numbers** (the Council `GPZ/Z/SA/PUD` action ← the PC `PUD/SMI/GPZ`
  recommendation), plus suppress rows that kill the `PUD`-token subject noise.

### Confidence
- **high** — an exact-case-number `override` (WVC has no full address+subject pairs).
- **medium** — strong IDF subject + temporal. **0 in WVC** after audit (the only auto-medium candidates
  were `PUD`-token false positives, suppressed).
- **low** — collapsed-token co-occurrence, gate-uncertain, or a secondary origin — kept but **flagged;
  do not quote without checking**.

### Resolution (prevents false fan-out)
Per primary item the best origin in each related body wins; secondaries are kept only when a strong
subject score sits within 80% of the best.

### Current build (West Valley)
**399 Council land-use/policy applications · 63 PC applications · 31 referral links** (**11 high · 0
medium · 20 low**) — all **Council ← PlanningCommission**. By method: **override 11 · subject 20.**
Only **11 of 399 (2%)** Council items link to another body — the rest are **correctly UNLINKED**, which
is the honest reality of a case-number-only corpus with a tiny named-project surface and a PC vote
record (134 meetings) that lags the council's. The 11 high links are exact-case-number overrides; the
20 low links are flagged `PUD`-token co-occurrence (large/negative `gap_days`, `subject_score`≈1.0 on a
bare token), kept for transparency, not for citation. The 4 auto-`medium` candidates (PC `PUD-1-2021`
spuriously matched to four different Council PUDs that each already carry their correct override link)
were reviewed weakest-first and **suppressed** in `db/referral_overrides.csv` (precision over recall).
`INTEGRITY: OK`. Audit: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names (NULL in WVC — join `application.rep_title` for the case number), both dates,
  `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`. (WVC's are all the
  PC→Council chain.)
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- Trace the hand-verified PC -> Council referrals (case numbers live in rep_title, not name):
SELECT r.confidence, r.related_date AS pc_date, rel.rep_title AS pc_item,
       r.primary_date AS council_date, pri.rep_title AS council_item, r.note
FROM referral r
JOIN application rel ON rel.application_id=r.related_application_id
JOIN application pri ON pri.application_id=r.primary_application_id
WHERE r.confidence='high' ORDER BY r.primary_date;

-- One PUD's full history, PC -> Council (case numbers live in motion_text, not the view's result_raw):
SELECT t.body, t.date, t.stage, t.outcome, t.recommendation, t.dissenters
FROM v_project_timeline t JOIN motion m ON m.motion_id=t.motion_id
WHERE m.motion_text LIKE '%PUD-2-2021%' ORDER BY t.date;

-- Cindy Wood's record across every body she served (PC commissioner -> Council, also RDA/MBA):
SELECT * FROM v_member_record WHERE full_name='Cindy Wood' ORDER BY body;
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. Because WVC items are case-numbered,
  the resolver lands almost everything in `singleton` (exact identity) — the heuristic `name` tier is
  near-empty (8 motions), so there is little `name`-grouping risk here. Correct any mis-merge in
  `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference**, not a looked-up key, and in WVC it is
  **deliberately thin**: `high` = exact-case-number overrides (≈exact); there are **no medium** links;
  `low` is `PUD`-token co-occurrence kept only as a flag. Correct mistakes in `referral_overrides.csv`
  and rerun.
- **Few cross-body links by design.** Only 2% of Council items link — the corpus describes items by case
  number, the two bodies use different series, and the PC vote record is sparse (128 study meetings carry
  no votes). Unlinked Council items are the expected majority, not a failure.
- **Person overlap is mostly hats, not careers.** 9 of the 10 multi-body people are the Council sitting
  as the RDA/MBA boards (same individuals). Only Cindy Wood spans the appointed PC and the elected
  Council. `person` identity is name-based (normalized full name), not a verified registry; `role` is
  *observed* from votes, not an authoritative term roster.
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs;
  note WVC publishes no genuine written public comments — see `public_comments/AVAILABILITY.md`).
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
