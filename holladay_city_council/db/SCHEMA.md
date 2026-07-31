# Holladay City — `db/civic.db` schema

Normalized relational database over Holladay's civic vote data (Salt Lake County, Utah). It lets
you join **Planning Commission ↔ City Council ↔ RDA ↔ LBA** votes by real keys instead of fuzzy
text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's db schema spec):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use / policy items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data* (each
   body keys only to itself), so it is reconstructed by record linkage in the separate `referral`
   table — every link is confidence-scored and overridable, and the genuine single-body majority
   is left **explicitly unlinked**.

Vendor: **Utah Public Notice** born-digital minutes (no structured agenda/matter IDs). Built from
the two canonical flat CSVs, which are never modified: `meeting_minutes/all_votes.csv` (Council +
in-session RDA + LBA) and `planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing; `db/referrals_audit.csv` lists every
referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 4 | Council · PlanningCommission · RDA · LBA |
| person | 26 | councilmembers (incl. voting Mayor) + commissioners + movers/seconders |
| meeting | 194 | one row per (body, source minutes file): Council 140 · RDA 9 · LBA 1 · PC 44 |
| application | 125 | body-scoped land-use/policy projects: Council 35 · PC 68 · RDA 19 · LBA 3 |
| motion | **869** | Council 678 · PlanningCommission 167 · RDA 21 · LBA 3 |
| vote | **2,702** | named member-vote rows (see reconciliation) |
| role | 37 | per person×body first/last vote + count |
| referral | 4 | reconstructed Council←PC links (all medium; see below) |

Motion outcomes (`outcome`): **Pass 856 · Fail 7 · Continued 5 · Died 1**. `names_recorded`:
496 motions name ≥1 voter · 373 are tally-only (unanimous-consent / procedural). Contested motions
(any Nay/Abstain/Recuse): **17** (`v_contested`) — Holladay is a high-consensus council.

## The MAYOR VOTES — max council roll = 6
Holladay's **Council–Manager** form seats **five district councilmembers + a voting Mayor** (the
City Manager is the appointed executive). So a full Council roll tops out at **6**, not 5, and the
Mayor **is** in `person` with `vote`/`role` rows (**Dahle** 2020–2025, **Fotheringham** 2026 —
365 mayor vote-rows total). The **RDA/LBA** convene in-recess (same members act as Board Members /
Chair); the **PlanningCommission** is a 7-member body with no mayor (roll ≤ 7). Contrast South
Jordan / Taylorsville, whose mayors do not vote.

## Standard schema
```
body(body_id, name UNIQUE, kind∈council/agency/commission/committee/department)
person(person_id, full_name, name_key UNIQUE)          -- name_key = normalized for joins
meeting(meeting_id, body_id, meeting_date, title, source_file, UNIQUE(body_id,source_file))
application(application_id, app_key UNIQUE, body_id, name, rep_title)   -- the project/matter
motion(motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
       outcome, stage, recommendation, application_id, app_match_method, app_confidence,
       mover_person_id, seconder_person_id, names_recorded, source_file)
vote(vote_id, motion_id, person_id, vote_value, UNIQUE(motion_id,person_id))
role(role_id, person_id, body_id, first_seen, last_seen, n_votes, UNIQUE(person_id,body_id))
referral(referral_id, primary_application_id, primary_body, related_application_id,
         related_body, match_method, confidence, shared_address, subject_score,
         primary_date, related_date, gap_days, note, UNIQUE(primary,related))
```
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Holladay uses Aye/Nay/Abstain/Recuse
— the source's printed `Yes/No` council tokens are normalized to Aye/Nay upstream). `outcome` ∈
Pass/Fail/Continued/Died. `stage` ∈ council_vote/rda_vote/lba_vote/pc_recommendation/
pc_final_action/other_action. `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`,
`vote.person_id`, `motion.meeting_id`, `application.body_id`, `referral.{primary,related}_application_id`.

## Vote reconciliation — fail-loud, one documented delta
The two `all_votes.csv` carry **2,712 named member rows**; the db holds **2,702 votes**. The
**+10 delta is fully explained**: the `vote(motion_id,person_id)` UNIQUE collapses **10 duplicate
`(source,motion_no,member)` rows**, all in the **PC**, all member **Layton**, across six 2022 PC
meetings (files 870741 ×4, 934075, 934073 ×3, 934057, 934053). These are a source/build recording
artifact (a name printed twice in an early-2022 full-name PC roll), not a db defect — the db's
collapse is the correct de-duplicated count. A dedup follow-up (rewrite the affected PC rows) is
queued in the repo-root `TODO.md`. The build never silently drops any *other* rows.

## Within-body application resolution
Only land-use / policy motions (and substantive agency motions) get an `application`; budgets,
appointments, contracts, and procedural motions correctly get **none**. Holladay's Council minutes
are **ordinance/resolution-number-keyed** ("ADOPT Ordinance 2024-16 …"); the PC groups its
recommendations/final actions by normalized project name + address. There is **no shared case
number** across bodies (see referral note).

## Cross-body `referral` layer — methodology & finding
Reconstructed in `build_referrals.py` (grain: application↔application between two different bodies;
`primary_body` = higher authority, Council > PlanningCommission > agency). Signals: shared
address > subject (IDF-weighted title-token agreement) > code section. **Temporal is a gate, not a
signal** (a PC→Council pair requires the PC to precede the Council within a bounded window).
`db/referral_overrides.csv` forces or kills a pair. Confidence: **high** = address+subject+temporal
(or an exact shared key) · **medium** = strong subject+temporal · **low** = gate-only (flag; don't
quote).

**Key structural finding — Holladay Council text is ordinance-keyed and cites 0 PC case numbers**,
so the strongest key cannot bridge PC→Council; cross-body links fall to subject + address +
temporal. **Result — 4 links, all `medium`, all Council←PlanningCommission** (surfaced by
`v_referral_chain`):
- Ord. **2022-15** (multi-family in the ORD Zone) ← PC positive recommendation 2022-05-17.
- Ord. **2024-07** (C-2 building heights) ← PC Ault mixed-use CLUP 2024-05-07.
- Ord. **2024-16** (short-term rentals as a conditional use in the PO Zone) ← PC **CONTINUE**
  2024-07-16, **and** ← the PC **NEGATIVE recommendation** 2024-08-20 (6-1, Berndt dissenting;
  subject score 1.0). The Council's motion to **APPROVE** Ord. 2024-16 then **FAILED 5-0** on
  2024-10-24 (`outcome=Fail`) — i.e. the Council **concurred** with the PC's recommended denial.
  This traced STR chain (PC continue → PC negative rec → Council fails-to-approve) is exactly the
  cross-body timeline the layer exists to surface; read the motion `outcome`, not just the "APPROVE"
  motion_text, before characterizing who prevailed.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names, both
  dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote).
  Mind the **Jan-2026 roster turnover** when reading a member's span.
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus council).

## Honesty requirements
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged. Holladay's 4 referrals are all `medium`.
- **Narrative-tally / tally-only motions** name only mover + seconder (+ any dissenters) or nobody
  (unanimous consent); the majority is honestly unnamed. Never infer unnamed Ayes.
- **Vote values are normalized, `result` is verbatim.** The db's `vote_value` is the controlled
  token; `result_raw` preserves the city's prose result string.
- Corrections go through the override CSVs + rebuild — never in-place edits to the flat CSVs or the
  `.db`.

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
