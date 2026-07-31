# Murray City — `db/civic.db` schema

Normalized relational database over Murray City's civic vote data (Salt Lake County, Utah).
It lets you join **Planning Commission ↔ City Council** votes by real keys instead of fuzzy
text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's
`db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
   `build_db.py` therefore reports **0 applications spanning >1 body**.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data*
   (each body keys only to itself), so it is reconstructed by record linkage in the separate
   `referral` table — every link is confidence-scored and overridable, and the genuine
   single-body majority is left **explicitly unlinked**.

Vendor: the **CivicPlus Archive** prose/PDF minutes portal (Council `Archive.aspx?AMID=31`,
Planning Commission `AMID=33`) — **no structured agenda/matter IDs, and no Utah `PL…` file
number anywhere in the prose** (unlike South Jordan's PC). Built from the two canonical flat
CSVs, which are never modified: `meeting_minutes/all_votes.csv` (Council) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists every
referral with both titles, score, and day-gap for review. Corrections go through
`db/vote_overrides.csv` / `db/referral_overrides.csv` + rebuild — never in-place edits.

## Current contents (as built — regenerate after any flat-CSV change)
| table | rows | notes |
|---|---|---|
| body | 2 | Council, PlanningCommission (Murray has **no** RDA/MBA) |
| person | 23 | councilmembers + commissioners + movers/seconders |
| meeting | 184 | one row per (body, source minutes file) |
| application | 256 | body-scoped land-use/policy projects — Council 21 · PlanningCommission 235 |
| motion | 1,009 | Council 654 · PlanningCommission 355 |
| vote | 4,109 | named member-vote rows — Aye 3,940 · Nay 90 · Excused 39 · Abstain 33 · Absent 7 |
| role | 23 | per person×body first/last vote + count |
| referral | 22 | reconstructed cross-body links (see below) |

Contested motions (any Nay/Abstain/Recuse): **84** (`v_contested`). Murray is a high-consensus
council; most majorities pass unanimously with the full roll call named (Murray records
per-name roll calls, unlike South Jordan's dissenter-only narrative tally).

> These counts are a point-in-time snapshot of the on-disk `.db`; `build_db.py` regenerates
> them from the flat CSVs (which now include the 5 OCR-recovered 2020/2022 minutes — the
> next rebuild will lift the motion/vote totals accordingly).

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Murray uses all but Recuse).
`outcome` ∈ Pass/Fail/Continued/Died. `stage` ∈ council_vote/rda_vote/mba_vote/ha_vote/
boa_action/other_action/pc_recommendation/pc_final_action (only `council_vote` /
`pc_recommendation` / `pc_final_action` / `*_action` occur here). `motion.provenance`
defaults `'minutes'` (all Murray motions are audited primary minutes; no PMN-recovered
rows). `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`, `vote.person_id`,
`motion.meeting_id`, `application.body_id`, `referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, and
procedural motions correctly get **no application** (745 motions, NULL). Resolution tiers:

| method | conf | count | meaning |
|---|---|---|---|
| `override` | high | 0 | a `db/overrides.csv` row forces `app_key` (none needed) |
| `singleton` | high | **212** | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | 52 | a named development/rezone grouped by normalized name (heuristic) |
| (NULL) | — | 745 | non-land-use motion → no application |

**Murray prints no exact prose key** (no `PL…` file number, no ordinance number in the roll
call), so — unlike South Jordan's `pl_number` PC key — every land-use application is resolved
by `singleton` identity or by normalized `name`. 264 motions carry an application (212+52);
235 of the 256 applications are PC-side (the Commission is the land-use workhorse; the Council
side is 21, mostly rezone/GPA final actions).

## Cross-body `referral` layer — methodology
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = the higher-authority side, Council > PlanningCommission). Signals:
**address** (shared full Utah grid pair / named-street address) > **subject** (IDF-weighted
title token agreement — symmetric Jaccard and asymmetric name-anchored containment) > **code
section**. **Temporal is a gate, not a signal**: for a PC→Council pair the PC must precede the
Council within ~400 days. `db/referral_overrides.csv`
(`primary_application_id,related_application_id,action∈link/suppress,note`) forces or kills a
pair. Confidence: **high** = address+subject+temporal · **medium** = strong subject+temporal ·
**low** = address-/gate-only (flag; do not quote).

**As with South Jordan, no exact key bridges the bodies** — Murray's Council minutes carry no
`PL…`/ordinance number the PC also cites — so cross-body links rest on subject + address +
temporal agreement, reported on every build, not a bug.

**Result — 22 links, all Council ← PlanningCommission: 15 high (`address+subject`), 7 medium
(`subject`).** The classic referral chain (PC recommendation → Council decision), surfaced by
`v_referral_chain`; the 15 high links share both a street address and subject tokens across the
PC→Council gap. Respect the confidence column: `high` ≈ exact, `medium` spot-check before
quoting, `low` flagged. Of Murray's 21 Council applications, those that link have a PC
counterpart; the rest are correctly UNLINKED (Council-originated items, or terse text with no
linkable subject).

## Bodies & voting notes
- **Form of government:** council–mayor (executive-mayor) form. **Five district councilmembers
  (D1–D5, no at-large) legislate; the separately-elected Mayor is the executive and casts NO
  council vote** — every ordinary Council tally tops out at **5**. The Mayor is excluded from
  the voting roster (only the five district surnames map to a Council vote).
- **Brett Hales** was **District-5 councilmember (2020–2021)** — a real, distinct voter — then
  **won the 2021 mayoralty (office 2022+)** and casts 0 council votes thereafter. "Councilmember
  Hales" and "Mayor Hales" are the same person; his 2020–2021 rows are legitimate.
- **Planning Commission** is a separate 7-member appointed body; its roll calls top out at **7**
  (a 7-named PC motion is correct, not an over-count). Council meets Tuesday; PC meets Thursday.
- **No in-meeting agency bodies.** Murray has no RDA/MBA votes in the minutes — `body` is only
  ever `Council` or `PlanningCommission`.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row in the flat CSVs
  lands in `vote`; the build aborts (non-zero exit) if any row is dropped without a documented
  `db/vote_overrides.csv` entry (`vote_overrides.csv` is currently empty — no reconciliation
  needed).
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged.
- **Tally-only voice votes are unnamed by design.** A "voice vote taken, all Ayes" motion
  records mover + seconder + tally, not each Aye (`names_recorded=0`, no `vote` rows). A blank
  member list on a passed motion is a source style, not a missing extraction.
- Corrections go through the override CSVs (`db/vote_overrides.csv`, `db/referral_overrides.csv`)
  + rebuild — never in-place edits to the flat CSVs or the `.db`.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names,
  both dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus council).

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
