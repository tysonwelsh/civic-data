# Cottonwood Heights City — `db/civic.db` schema

Normalized relational database over Cottonwood Heights' civic vote data (Salt Lake County,
Utah). It lets you join **Planning Commission ↔ City Council ↔ CDRA** votes by real keys instead
of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's
`db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use items) its project *application*, resolved **within each body**. A Council "Foo" and
   a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data* (each
   body keys only to itself), so it is reconstructed by record linkage in the separate `referral`
   table — every link is confidence-scored and overridable, and the genuine single-body majority
   is left **explicitly unlinked**. For Cottonwood Heights this layer is currently **empty** (see
   below) — an honest empty, not a build error.

Vendor: a **prose/PDF minutes portal** (Granicus / CivicEngage Central) with **no structured
agenda/matter IDs**, unioned with Utah Public Notice. Built from the two canonical flat CSVs,
which are never modified: `meeting_minutes/all_votes.csv` (Council + CDRA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 3 | **Council**, **CDRA**, **PlanningCommission** |
| person | 28 | councilmembers + 3 voting mayors + commissioners + movers/seconders |
| meeting | 269 | one row per (body, source minutes file) — Council 171 · CDRA 41 · PC 57 (a 0-motion minutes file creates no meeting row — the 21 admin-hearing docs are absent by design) |
| application | 132 | body-scoped land-use/policy projects — Council 42 · CDRA 58 · PC 32 |
| motion | 1,408 | **Council 1,075 · CDRA 70 · PlanningCommission 263** — `provenance` ∈ `minutes` (1,402 audited) / `pmn_minutes` (6 — the 2022-07-06 PC doc promoted 2026-07-16 from `pmn_backfill/`) |
| vote | 3,154 | named member-vote rows (see reconciliation) |
| role | 37 | per person×body first/last vote + count |
| referral | 0 | reconstructed cross-body links — **none cleared threshold** (see below) |

Contested motions (any Nay/Abstain/Absent): **64** (`v_contested`). Cottonwood Heights is a
high-consensus council but a **named-roll** one — unlike the narrative-tally cities, most
motions print a full member roll, so contested motions surface with every dissenter named.

## Standard schema
```
body(body_id, name UNIQUE, kind∈council/agency/commission/committee/department)
person(person_id, full_name, name_key UNIQUE)          -- name_key = normalized for joins
meeting(meeting_id, body_id, meeting_date, title, source_file, UNIQUE(body_id,source_file))
application(application_id, app_key UNIQUE, body_id, name, rep_title)   -- the project/matter
motion(motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
       outcome, stage, recommendation, application_id, app_match_method, app_confidence,
       mover_person_id, seconder_person_id, names_recorded, source_file,
       provenance)   -- 'minutes' = audited primary; 'pmn_minutes' = PMN-backfill promoted
vote(vote_id, motion_id, person_id, vote_value, UNIQUE(motion_id,person_id))
role(role_id, person_id, body_id, first_seen, last_seen, n_votes, UNIQUE(person_id,body_id))
referral(referral_id, primary_application_id, primary_body, related_application_id,
         related_body, match_method, confidence, shared_address, subject_score,
         primary_date, related_date, gap_days, note, UNIQUE(primary,related))
```
Enums (as observed here): `vote_value` ∈ **Aye 3,068 / Nay 54 / Abstain 26 / Absent 6**.
`outcome` ∈ **Pass 1,400 / Fail 4 / Died 4**. `stage` ∈ **council_vote 1,145** (Council + CDRA)
**/ pc_final_action 222 / pc_recommendation 41**. `PRAGMA foreign_keys=ON`; indexed on
`motion.application_id`, `vote.person_id`, `motion.meeting_id`, `application.body_id`,
`referral.{primary,related}_application_id`.

## Bodies & voting notes — the Mayor VOTES (max roll = 5)
- **Form of government:** a **four-district council + a separately-elected Mayor who is a full
  voting member**. Every normal council tally tops out at **5** (4 districts + Mayor), **never
  6** — the OPPOSITE of Taylorsville / South Jordan (mayor non-voting). The three mayors —
  **Michael Peterson**, **Mike Weichers**, **Gay Lynn Bennion** — each have a `role` row on the
  **Council** body and vote as ordinary members (533 vote rows). The build **swept for any
  >5-voter council motion and found none**; the ceiling holds.
- **CDRA (Community Development & Renewal Agency)** convenes *inside* council meetings (recess →
  agency board → reconvene); its open votes are the **`body='CDRA'`** rows (70 motions / 41
  meetings). Because the same people sit as the board, CDRA motions carry `stage='council_vote'`
  — filter on `body`, not `stage`, to isolate CDRA.
- **Mid-term appointment:** **Matt Holton**'s first Council vote is **2023-05-16**; **Douglas
  Petersen**'s last is **2023-04-04** (District 1 vacancy fill). Both are distinct `person`
  rows with their own `role` intervals — join by person, not by seat.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions (and substantive agency motions) get an `application`; budgets,
appointments, contracts, and procedural motions correctly get **no application** (1,274 motions,
NULL). Cottonwood Heights' minutes carry **no Utah `PL…` planning file numbers** (unlike South
Jordan), so resolution falls to:

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | 122 | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | 12 | a named development/rezone grouped by normalized name (heuristic) |
| (NULL) | — | 1,274 | non-land-use / procedural motion → no application |

## Cross-body `referral` layer — why it is empty (0 links)
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = higher authority, Council > PlanningCommission > CDRA). Signals:
address (shared grid pair / named-street) > subject (IDF-weighted title-token agreement) > code
section; temporal is a gate (PC must precede Council within a bounded window).

**Result — 0 links.** Cottonwood Heights' council minutes are terse and
**ordinance/resolution-number-keyed** ("APPROVE Ordinance 405 …"), and the PC recommendations
are keyed to their own project descriptions; the two sides share **no exact key** and, after the
precision-over-recall tuning the spec prescribes, no address/subject pair cleared the confidence
threshold. This is a **genuine data characteristic** (the same one-sided-bridge finding as South
Jordan), reported on every build — **not** a bug and **not** a claim that no PC→Council referral
ever happened. A `PL…`/number cross-tier is implemented and will fire automatically if a future
motion ever carries a shared key. Treat cross-body questions here via `v_project_timeline`
(within-body history) + manual date/subject inspection, not via `referral`.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **3,154 CSV named rows (2,633 Council/CDRA + 521 PC) = 3,154 db vote rows**, **0 dropped, 0
  overrides needed**. The build aborts if any row is dropped without a documented override. No
  duplicate or unresolvable rows exist (the 2026-05-19 phantom "Highland" was resolved at the
  extraction layer, so no duplicate reaches the db).
- **The within-body core is exact; the `referral` layer is reconstructed inference** — here it is
  empty, so all cross-body relationships are currently **explicitly unlinked**.
- **Named-roll city, faithful clerk errors retained.** Cottonwood Heights prints full rolls on
  most motions; the blank-member rows are unanimous-consent procedural motions (no roll printed).
  Three council `result_raw` strings disagree with their named rolls (2023-11-21 "4-to-1";
  2026-05-19 ×2 "4-to-2" with the phantom "Highland") — the **verbatim string is kept** and only
  the real members are stored. See `../VERIFICATION.md` §A3.
- Corrections go through override CSVs + rebuild — never in-place edits to the flat CSVs or the
  .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC/CDRA→Council link (currently empty).
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Absent (the signal; 64 motions).

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
