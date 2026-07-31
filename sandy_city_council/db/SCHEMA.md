# Sandy City civic database — schema & data dictionary

`db/sandy.db` (SQLite) is the **canonical, queryable** form of Sandy's vote data — the same
normalized standard core as every other city in this collection (body / person / meeting /
application / motion / vote / role + the reconstructed `referral` layer and the four standard
views), **plus** a sandy-local `legistar_*` extension layer preserving the full Legistar
structured harvest. Built reproducibly in **two stages**; `db/tables/` CSVs are per-table
exports (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core + legistar_* extension layer
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer
                                #    (the byte-identical shared template used by 12 cities)
```

**History.** Until 2026-07-02 this db was a schema fork built ONLY from the Legistar API
staging CSVs (different meeting/application/motion columns, `Nonvoting` in the core vote
table, dropped CHECK constraints, 10 bodies, no `source_file`). REMEDIATION_PLAN.md 2.6
mapped it onto the standard schema — a query written for any other city's `civic.db` now
works here — with every Legistar-specific fact preserved in the extension layer below.
The pre-2.6 db and build scripts are in `_backups/2026-07-02/sandy_city_council/db/`.

## The Sandy reality (two sources, one standard core)

Sandy is the collection's **Legistar city**: alongside the published minutes there is a
structured API harvest (`db/staging/*.csv` — 10 bodies, 466 events, 2,825 matters, 10,457
event items, 10,443 raw vote rows). The two vote records disagree in coverage, so the core's
sourcing is an explicit, measured decision:

### Council votes: MINUTES-PRIMARY (decision 2026-07-02, re-examined post-PUA repair)

Measured comparison of the two council-vote records (2020-01 → 2026-06):

| measure | minutes `all_votes.csv` (post-repair) | Legistar staging (body 138) |
|---|---|---|
| raw rows | 3,975 (3,689 named member-votes) | 5,720 rows = **3,749 distinct votes** (consent fan-out duplicates the same VoteId onto every consent item; 536 distinct roll-call groups) |
| motions | 833 (incl. 286 tally-only/narrative rows) | ~536 roll-call groups |
| meeting dates with votes | **240** | 214 |
| dates only it covers | **33** | 7 — of which 3 are 2026-06-09/16/23 (minutes not yet published), 2 are minutes missing from the corpus (2023-10-17, 2023-11-07), 2 have minutes on disk but no extractable roll call (2022-07-19, 2023-10-24) |
| recorded Nays | **292** | 173 |

Legistar omits narrative voice votes and even whole contested roll calls — e.g. on
**2021-08-17** it carries neither the failed 2–5 tabling motion nor the contested 6–0–1
adoption of Resolution 21-31C, both printed in the minutes. The minutes CSV was also
verified 1.000 against retained raw PDFs (Phase 1.1). **Decision: council (and RDA) votes
come from `meeting_minutes/all_votes.csv`, like every other city; Legistar is the
enrichment layer** (matter keys, agenda numbers, action names, and the votes/bodies the
minutes don't carry — all preserved in `legistar_*`, nothing discarded).

### Planning Commission votes: LEGISTAR (their only source)

`planning_commission/all_votes.csv` is itself generated from `db/staging/` (body 140) by
`planning_commission/build_from_legistar.py` — Sandy publishes no PC minutes corpus. The
build replays that script's enumeration exactly, so all **554/554** PC motions map 1:1 to
their Legistar EventItem (title-verified) — `app_match_method='matter_id'`, exact.

## Two layers, never conflated

1. **STANDARD CORE (`build_db.py`) — EXACT**, from the two flat CSVs. Every vote ties to
   body/meeting/person; land-use/policy motions get a body-scoped `application_id`
   (0 applications span >1 body, by construction).
2. **LEGISTAR EXTENSION (`legistar_*` tables)** — the full structured harvest, cross-linked
   to the core where a mapping exists, never substituted for it.
3. **Cross-body `referral` (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE**
   (the shared generalized template, byte-identical to west_valley/lehi/provo/…).

## Core tables (standard semantics)

| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | `Council` / `PlanningCommission` / `RDA` (the CSV body codes); `kind` ∈ council/commission/agency. The 10 Legistar bodies live in `legistar_body` |
| `person` | one official | `person_id` PK; **`name_key` NOT NULL UNIQUE** | 25 officials from the CSVs (verified collision-free). Alias: Legistar "Kris Nicholl" = minutes "Kristin Coleman-Nicholl" (one person). Name-change caveat: Brooke Christensen and Brooke D'Sousa are recorded as two names in both sources and stay two `person` rows (name-keyed identity, as everywhere) |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | council/RDA `source_file` = the minutes `.md` path on disk; PC (no minutes retained) = the canonical Legistar event URL `https://webapi.legistar.com/v1/sandyutah/events/<EventId>` |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | matter-backed apps: `application_id` = Legistar MatterId, `app_key` = `<body>\|<MatterFile>`, `name` = MatterName, `rep_title` = the full matter title. Prose apps (unmatched land-use motions) use ids ≥ 1,000,001 and the template `<body>\|<name>` / singleton keys |
| `motion` | one motion | `motion_id` PK | `motion_type` (city-native, from the CSV), `result_raw` (verbatim CSV `result`), `outcome`/`stage`/`recommendation` CHECK-constrained, `names_recorded`, `source_file` = CSV `source`. Keyed off the CSVs on `(source, motion_no, date)` — date included because PC's `source` is one constant provenance string (SCHEMA_SPEC §2) |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | `vote_value` ∈ the standard §4 vocabulary (Aye/Nay/Abstain/Recuse/Absent/Excused). `Nonvoting` exists ONLY in `legistar_vote` (156 rows, PC nonvoting seats) — a documented Legistar-layer value, not a core one |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | derived observed span |

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` — present: **Pass 1,328 · Fail 52 · Died 7**
  (`Continued` allowed but absent — Sandy result strings never say tabled/continued; tabling
  shows up as its own motion).
- `motion.stage` — present: **`council_vote` 832 · `pc_final_action` 527 ·
  `pc_recommendation` 27 · `rda_vote` 1**. PC direction comes from the Legistar
  `EventItemActionName` of the mapped item ("recommended for approval/denial" vs
  "approved"/"adopted"): `recommendation` **Positive 25 / Negative 2**.
- `motion.app_match_method` ∈ `matter_id | name | singleton | override` — **`matter_id` is the
  sandy extension value** (an exact Legistar Matter key, stronger than the prose tiers; a
  query filtering on the standard three values behaves normally). Present: **matter_id 651 ·
  singleton 21 · name 1**; 714 motions correctly app-less (budgets, appointments, procedural).
- `vote.vote_value` — present: **Aye 6,624 · Absent 1,122 · Nay 329 · Recuse 16 · Excused 9 ·
  Abstain 9** (Excused/Recuse are PC-Legistar values; council minutes record Aye/Nay/Absent/Abstain).

### Build totals (current)
**3 bodies · 25 persons · 356 meetings (Council 240 · PC 115 · RDA 1) · 672 applications ·
1,387 motions (Council 832 · PC 554 · RDA 1) · 8,109 votes · 25 roles.** Contested (any
Nay/Abstain/Recuse): **Council 131 · PC 43.** Coverage 2020-01-07 → 2026-06-18.

### Reconciliation (printed on every build; validator check h.db)
**CSV named rows 8,120 (meeting_minutes 3,689 + planning_commission 4,431) = 8,109 `vote`
rows + 11 merged duplicate pairs**, every pair documented in `db/vote_overrides.csv`
(park_city schema: `source_file,motion_no,member,date,claimed_values,resolution,reasoning`):
- **8 identical pairs** — Legistar duplicated-roster-slot artifact (Ron Mortimer twice per
  roll, both Aye; PC 2022-06-02 m1–4 and 2022-06-16 m1–4). Merged.
- **2 conflicting pairs** — the same duplicated slot on PC 2022-05-05 m1–2 with **Aye +
  Absent**; resolved **Aye** (the in-sequence roster position holds the Yes; the agreeing
  Aye+Aye meetings prove the slot-duplication mechanism; documented judgment call — both raw
  rows preserved verbatim in `legistar_vote` and `db/staging/votes.csv`).
- **1 conflicting pair** — council 2021-08-17 m5 (failed 2–5 tabling motion): the minutes
  print Cyndi Sharkey on BOTH sides ("Cyndi Shakey" [sic] in the Yes list) while Alison
  Stroud appears in neither. Sharkey moved the motion; resolved **Aye**; the 5th Nay stays
  honestly unnamed. Legistar records no roll call for this motion at all.
The build FAILS LOUDLY on any duplicate pair not documented in `vote_overrides.csv`.

## Motion ↔ Legistar linkage (the enrichment cross-link)

**960/1,387 motions** link to their Legistar event item(s) (`legistar_event_item.motion_id`):
PC 554/554 exact (replayed enumeration); council via **roll-call signature matching** —
Legistar items sharing one VoteId set are one physical roll call (the consent-calendar roll
is duplicated onto every consent item), matched to minutes motions in tiers:
1. identical (Aye-set, Nay-set) member signatures on the same date;
2. identical Nay-set + printed-tally agreement (narrative votes name only dissenters);
2b. unique identical Aye-set + positive title-token overlap (minutes record dissent
   Legistar omits);
3. tally-only motions: tally agreement + unique positive title-token overlap.
Ties break by title-token overlap then minutes order; no candidate → no link. Values always
come from the CSVs — matching only drives matter/enrichment linkage. Unlinked council
motions are minutes-only records Legistar doesn't carry (the 33 minutes-only dates,
narrative votes, motions Legistar skipped).

A multi-matter roll call (consent) containing exactly **one** land-use matter resolves that
motion's application to it; rolls with 2+ land-use matters (e.g. twin annexations approved
in one motion) stay app-less on the standard side and fully queryable via
`legistar_event_item`.

## `legistar_*` extension layer (sandy-local; the full harvest, preserved)

| table | rows | carries |
|---|---|---|
| `legistar_body` | 10 | all Legistar bodies (Council 138, BoA 139, PC 140, + 7 committees/departments); `body_id` links the 2 that map to core bodies |
| `legistar_person` | 226 | every Legistar person; `person_id` links the 25 that map to core officials |
| `legistar_event` | 466 | every event with **`agenda_status` / `minutes_status`** (the old fork's meeting columns), time, location; `meeting_id` links unambiguous body+date matches |
| `legistar_matter` | 2,825 | every Matter with **`matter_type`, `status`, `intro_body`, `intro_date`**, agenda/passed dates, enactment number (the old fork's application columns); `application_id` links matters that became core applications |
| `legistar_event_item` | 10,457 | every agenda item with **`agenda_number`, `action_name`**, sequences, passed flag, matter fields, mover/seconder (the old fork's motion columns); `motion_id` links matched items |
| `legistar_vote` | 10,443 | every raw vote row (incl. the consent fan-out duplicates and the 156 **`Nonvoting`** rows) with `value_raw` + normalized `value_norm`; the Board of Adjustment's 136 rows live only here (BoA has no flat CSV) |

## `referral` — the reconstructed cross-body linkage

Built by the **shared generalized template** (byte-identical `build_referrals.py` across the
prose cities): `referral(primary_application_id, primary_body, related_application_id,
related_body, match_method ∈ address|subject|address+subject|override, confidence ∈
high|medium|low, shared_address, subject_score, primary_date, related_date, gap_days, note)`;
`UNIQUE(primary, related)`; overrides via `db/referral_overrides.csv`
(`primary_application_id,related_application_id,action,note`; the loader also accepts the
legacy sandy header). Signals: shared grid/named-street address; IDF-weighted de-boilerplated
title agreement (+ name-anchored containment); a directional temporal gate (PC precedes
Council, ~400 days). Audit: `db/referrals_audit.csv`.

### Current build
**145 council land-use/policy applications · 527 PC applications · 116 links
(53 high · 51 medium · 12 low)**, all Council ← PlanningCommission; by method:
address+subject 53 · subject 56 · address 7. **95 of 145 (65%)** council apps linked — the
rest are correctly UNLINKED (council-internal rules, honorary resolutions, council-initiated
policy with no prior PC hearing).

**Continuity vs the pre-2.6 layer** (124 links at raw-Legistar-matter grain, archived in
`_backups/2026-07-02/sandy_city_council/db/referrals_audit.csv`): **98/124 old pairs
reproduce exactly** (same MatterId pairs — matter-backed `application_id`s are MatterIds).
The 26 that don't: council matters whose only council action was a multi-land-use consent
roll (twin annexations), Legistar-only roll calls on the 4 dates outside the minutes corpus,
minutes/Legistar roll disagreements the matcher conservatively skips, and engine-template
scoring differences (the template rates address-only-without-subject links `low`, sandy's
old prototype rated them `high`). All the underlying matter relationships remain queryable
via `legistar_event_item` → `legistar_matter`. 18 new links come from the broader
minutes-side population (prose apps + the extended land-use pattern).

## Views (start here — standard shapes)
- **`v_referral_chain`** — every cross-body link: both `app_key`s/projects/dates, method,
  confidence, `shared_address`, `subject_score`, `gap_days`.
- **`v_project_timeline`** — within-body project history
  (`app_key → body/date/stage/outcome/recommendation/result_raw/dissenters`).
- **`v_member_record`** — per person×body vote tallies.
- **`v_contested`** — motions with any Nay/Abstain/Recuse (174: Council 131 · PC 43).

```sql
-- Trace a rezone across both bodies (PC hearing -> Council decision):
SELECT confidence, match_method, related_date AS pc_date, related_key AS pc_file,
       primary_date AS council_date, primary_key AS council_file, shared_address
FROM v_referral_chain WHERE confidence='high' ORDER BY primary_date;

-- Standard cross-city query (works unchanged on any city's db):
SELECT full_name, body, votes, nays FROM v_member_record ORDER BY nays DESC LIMIT 5;

-- Legistar enrichment join: a motion's agenda number, action name, and matter status:
SELECT mo.motion_id, m.meeting_date, lei.agenda_number, lei.action_name, lm.matter_file, lm.status
FROM motion mo JOIN meeting m ON m.meeting_id=mo.meeting_id
JOIN legistar_event_item lei ON lei.motion_id=mo.motion_id
LEFT JOIN legistar_matter lm ON lm.legistar_matter_id=lei.legistar_matter_id
WHERE mo.motion_id = ?;
```

## Known limitations (honest)
- The **referral layer is reconstructed inference**, not a looked-up key (Legistar gives no
  shared key across bodies: 0 shared MatterId/MatterFile, empty MatterRelations — verified).
  `high` ≈ exact; spot-check `medium` before quoting; `low` is flagged. Correct mistakes in
  `referral_overrides.csv` and rerun (idempotent).
- **Council motion ↔ Legistar item matching is conservative**: ~430 motions (mostly voice
  votes, tally-only motions, and the 33 minutes-only dates) have no Legistar link, and a few
  land-use matters decided on multi-land-use consent rolls or on the 4 non-corpus dates have
  no standard application. Their Legistar record is complete in the extension tables.
- **PC stage skew is source-faithful**: Legistar marks most PC actions "approved" (527
  `pc_final_action`) and only 27 "recommended…" — Sandy's clerk rarely uses the
  recommendation action label, so don't read `pc_recommendation` count as the true share of
  legislative items; the referral layer links regardless of stage.
- `person` identity is name-based (normalized full name), not a verified registry —
  Christensen/D'Sousa stay two rows; `role` is observed from votes, not a term roster.
- This DB covers votes; comments and elections remain in their CSVs (Sandy publishes no
  written public comments — `public_comments/AVAILABILITY.md`).

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
