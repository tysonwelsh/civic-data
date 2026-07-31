# Magna City — `db/civic.db` schema

Normalized relational database over Magna's civic vote data (Salt Lake County, Utah).
It lets you join **Planning Commission ↔ City Council ↔ CRA** votes by real keys instead of
fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data*
   (each body keys only to itself), so it is reconstructed by record linkage in the separate
   `referral` table — every link is confidence-scored and overridable, and the genuine
   single-body majority is left **explicitly unlinked**.

Vendor: **CivicPlus AgendaCenter** (`magna.utah.gov`, 2022+) + **Utah PMN** (body 5803 council
2018–2021, body 1559 PC) — prose/PDF minutes, no structured matter IDs. Built from the two
canonical flat CSVs, which are never modified: `meeting_minutes/all_votes.csv` (Council + CRA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists every
referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 3 | **CRA**, Council, PlanningCommission |
| person | 24 | councilmembers + commissioners + movers/seconders |
| meeting | 248 | one row per (body, source doc) — Council/CRA (incl. 12 PMN-promoted) + 80 PC |
| application | 223 | body-scoped land-use / policy projects |
| motion | 1,286 | Council 940 (908 `minutes` + 32 `pmn_minutes`) · **CRA 32 (13 + 19)** · PlanningCommission 314 |
| vote | 175 | named member-vote rows (see reconciliation) |
| role | 16 | per person×body first/last vote + count |
| referral | 3 | reconstructed cross-body links, **all `medium`** (see below) |

(Counts as-rebuilt 2026-07-16 after the pmn_backfill promotion; the 2026-07-12 T3.1(e)
re-extraction had already grown the named layer beyond this file's original figures.)

Contested motions (any Nay/Abstain/Recuse): **64** (`v_contested`). Magna is a high-consensus,
narrative-tally council; most majorities pass with only movers/dissenters named — hence just 175
named vote rows over 1,286 motions.

## Standard schema
```
body(body_id, name UNIQUE, kind∈council/agency/commission/committee/department)
person(person_id, full_name, name_key UNIQUE)          -- name_key = normalized for joins
meeting(meeting_id, body_id, meeting_date, title, source_file, UNIQUE(body_id,source_file))
application(application_id, app_key UNIQUE, body_id, name, rep_title)   -- the project/matter
motion(motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
       outcome, stage, recommendation, application_id, app_match_method, app_confidence,
       mover_person_id, seconder_person_id, names_recorded, source_file, provenance)
vote(vote_id, motion_id, person_id, vote_value, UNIQUE(motion_id,person_id))
role(role_id, person_id, body_id, first_seen, last_seen, n_votes, UNIQUE(person_id,body_id))
referral(referral_id, primary_application_id, primary_body, related_application_id,
         related_body, match_method, confidence, shared_address, subject_score,
         primary_date, related_date, gap_days, note, UNIQUE(primary,related))
```
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Magna records Aye/Nay/Abstain/Absent;
source "EXCUSED" is normalized to `Absent`). `outcome` ∈ Pass/Fail/Continued/Died. `stage` ∈
council_vote/rda_vote/mba_vote/ha_vote/boa_action/other_action/pc_recommendation/pc_final_action
(Magna's CRA motions use `stage=rda_vote`). `provenance` ∈ `minutes` (audited docs) /
`pmn_minutes` (the 12 PMN-recovered docs promoted 2026-07-16 from `pmn_backfill/` — 51 motions;
filter `provenance='minutes'` for a clean audited-only cut). `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`,
`vote.person_id`, `motion.meeting_id`.

## Bodies & the form-of-government seam (the Magna-specific fact)
- **Three bodies:** `Council`, `PlanningCommission`, and **`CRA`** (Community Reinvestment Agency —
  Magna's RDA-equivalent). The CRA convenes *inside* council meetings (recess → agency board →
  reconvene); its **13** open votes are tagged `body=CRA` in the council CSV and appear as
  "Board Member <Name>". There is no separate CRA portal.
- **Presiding officer's vote flips at 2025→2026.** Magna was a metro township (2017) that became a
  city 2024-05-01; through 2025 the council elected its own **Chair, titled "Mayor"** (Peay, then
  Barney) who **is one of the five and VOTES**; from 2026 the directly-elected executive **Mayor
  Sudbury presides but does NOT vote**. **Max council roll = 5 in both eras.** `Mick Sudbury` is a
  single `person` with **voting rows through 2025** (as the D3 councilmember) and **none after** he
  becomes Mayor — a person-level query spans the seam by design. There is no separate "Mayor"
  person row for the non-voting era (he simply stops appearing in `vote`).

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, and
procedural motions correctly get **no application** (NULL). Land-use motions are grouped by the
PC's cited **`REZ####-######` case number** where present (exact) or as singletons otherwise; the
Council side is ordinance/resolution-keyed and cites no `REZ` numbers.

## Cross-body `referral` layer — methodology & the key finding
Reconstructed in `build_referrals.py` (grain: application↔application between two different bodies;
`primary_body` = higher authority, Council > PlanningCommission > CRA). Signals, strongest first:
**case number** (exact) > **address** (shared Utah grid / named street) > **subject** (IDF-weighted
title-token agreement) > **code section**. **Temporal is a gate, not a signal** (a PC→Council pair
requires the PC to precede the Council within ~400 days). `db/referral_overrides.csv`
(`primary_application_id,related_application_id,action∈link/suppress,note`) forces or kills a pair.
Confidence: **high** = case-number match, or address+subject+temporal · **medium** = strong
subject+temporal · **low** = address-/gate-only (flag; do not quote).

**Key structural finding — the case-number bridge is one-sided.** The PC keys land-use items by
`REZ####-######`; the **Council/CRA minutes are ordinance/resolution-keyed and cite 0 PC case
numbers**, so the strongest key cannot bridge PC→Council in the flat data, and every cross-body
link falls to subject + address + temporal. This is a genuine data characteristic, reported on
every build. **Result — 3 links, all `medium`** (as-rebuilt 2026-07-16: 2 Council←PC ordinance
chains surfaced by the promoted 2024-02-27 ADU / 2024-11-26 glass-requirements minutes + 1
same-night Council←CRA Broadway pair). They surface through `v_referral_chain`; treat
`medium` as strong-but-spot-check, and note that the vast majority of PC recommendations are
correctly **unlinked** (terse ordinance-keyed council text carries no linkable key).

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **175 CSV named rows (156 Council/CRA + 19 PC) = 175 db vote rows**, **0 dropped, 0 orphan FKs,
  0 unresolved voters, 0 duplicate member-on-a-motion.** The build aborts if any row would be
  dropped without a documented `db/overrides.csv` entry.
- **Narrative-tally city.** Most motions name only the mover, seconder, and any
  dissenters/absentees, leaving the majority unnamed (`names_recorded` is 1 whenever any member
  row exists). Where a printed tally and a partial named roster disagree, the normalization layer
  keeps the string tally and never infers unnamed Ayes.
- **The within-body core is EXACT; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged.
- Corrections go through the override CSVs + rebuild — never in-place edits to the flat CSVs or the
  `.db`.

## Views to ship
- `v_referral_chain` — every reconstructed PC/CRA→Council link: both app keys, both project names,
  both dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote);
  read Mick Sudbury's row with the seam in mind (councilmember votes only, none as Mayor).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus council; 28).

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
