# Emigration Canyon — `db/civic.db` schema

Normalized relational database over Emigration Canyon's civic vote data (Salt Lake County,
Utah). It lets you join **Planning Commission ↔ City/Township Council** votes by real keys
instead of fuzzy text. **Two layers, never conflated** (per `../SCHEMA_SPEC.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its `application`, resolved **within each body**. A Council item and a
   PC item are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data*
   (each body keys only to itself), so it is reconstructed by record linkage in the separate
   `referral` table — confidence-scored and overridable.

Vendor: **Utah Public Notice (PMN)** prose/PDF minutes (no structured agenda/matter IDs).
Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council — Metro Township 2018–2024 + City 2024+) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists every
candidate referral with both titles, score, and day-gap for review.

## Current contents (as built, 2026-07-12)
| table | rows | notes |
|---|---|---|
| body | 2 | Council, PlanningCommission (no RDA/CRA — this body has none) |
| person | 15 | named movers / seconders / dissenters only (narrative-tally → few names) |
| meeting | 128 | one row per (body, source minutes file) **that recorded ≥1 motion** (see note) |
| application | 14 | body-scoped land-use / policy items (land-use singletons) |
| motion | 427 | **Council 288 · PlanningCommission 139** |
| vote | 6 | named member-vote rows (the entire attributed-dissent record) |
| role | 4 | per person×body first/last vote + count |
| referral | 0 | reconstructed cross-body links — **none found** (see below) |

**Meeting count (128) vs docs on disk (145).** The `meeting` table is motion-driven: **17**
indexed minutes docs recorded **no formal motion** (work/emergency sessions, a Board of
Canvassers meeting, cancelled-substance meetings, and the 2 zero-motion OCR docs — see
`../VERIFICATION.md §3f`) and therefore create no `meeting` row. The canonical
`minutes_index.csv` still holds **all 145** (86 council + 59 PC). This is a derived-layer
characteristic, not data loss.

**Contested motions (any Nay/Abstain):** 6 total — **3 Council** (2021-08-24 Smolka abstain,
2021-12-14 Harris abstain, 2023-10-24 Smolka Nay — all 4-1) + **3 PC** (2019-11-14 & 2022-11-17
Harpst abstain, 2026-06-11 Wallace Nay). Emigration Canyon is a high-consensus, narrative-tally
body; most motions pass with only the mover/seconder named and the majority honestly unnamed.

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Emigration records Nay/Abstain on
named dissent; unanimous majorities are unnamed). `outcome` ∈ Pass/Fail/Continued/Died.
`stage` ∈ council_vote/pc_recommendation/pc_final_action/other_action. `PRAGMA
foreign_keys=ON`; indexed on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, `referral.{primary,related}_application_id`.

## The peer-selected VOTING mayor (denominator note)
Emigration Canyon's Mayor is **selected by the council from its own five members** and
**PRESIDES AND VOTES** — the **Millcreek pattern**, max full-council tally **= 5 including the
mayor** (NOT the Taylorsville/South-Jordan executive-mayor form where the mayor is uncounted).
The presiding mayor changes by era — **Joe Smolka** (Metro Township, 2018–2024) → **David
Brems** (City, 2024+) — and is detected per document from the "Council Members Present" block,
not hard-coded. Both mayors appear in the vote record as full members (e.g. Smolka's 2023-10-24
Nay in a 4-1). `person` therefore contains no separate non-voting executive.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, and
procedural motions correctly get **no application** (NULL). Emigration Canyon's PMN minutes
carry **no Utah `PL…`/`OAM…` file number on the Council side** and only sporadic case numbers on
the PC side, so most land-use items resolve as **singletons** (an unnamed land-use/policy motion
→ its own application; exact identity, name unknown). **14 applications** total.

## Cross-body `referral` layer — the key finding: EMPTY (0 links)
`build_referrals.py` reconstructs application↔application links between the two bodies
(`primary_body` = higher authority: Council > PlanningCommission), using PL/case number (exact)
> address > IDF-weighted subject > code section, gated by temporal order (PC precedes Council).
**It found 0 qualifying links.** This is a genuine data characteristic, not a bug:

- The Council minutes are **terse and ordinance/resolution-number-keyed** ("approve Resolution
  2023-10-02", "Ordinance 2025-O-09") and cite **no** PC case/`OAM…` numbers, so the strongest
  bridge cannot fire.
- The record volume is tiny (a ~1,600-person canyon), land-use items are few, and the surviving
  subject+temporal signals did not clear the precision threshold for any pair.
- The genuine single-body majority is therefore left **explicitly unlinked** — the honest
  result. `db/referral_overrides.csv` (`primary_application_id,related_application_id,action∈
  link/suppress,note`) can force a hand-verified link if one is later identified; none was.

`db/referrals_audit.csv` records the (empty) candidate set for review.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **6 CSV named rows == 6 db votes, 0 dropped, 0 overrides.** The build aborts if any row is
  dropped without a documented `db/overrides.csv` entry.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — here it
  is empty, which is the faithful answer for this record.
- **Narrative-tally body.** Many motions name only the mover/seconder, leaving the majority
  unnamed (`names_recorded` reflects whether any member row exists). Never infer unnamed Ayes.
- `result_raw`/`motion_type` are **city-verbatim**; normalized fields live alongside
  (`motions_std.csv`, repo-root `crosswalks/`). Corrections go through the override CSVs +
  rebuild — never in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link (currently empty).
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome).
- `v_member_record` — per person×body vote tallies (first/last vote, counts).
- `v_contested` — motions with any Nay/Abstain (the signal on a high-consensus council).

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
