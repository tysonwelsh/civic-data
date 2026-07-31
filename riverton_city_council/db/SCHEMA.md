# Riverton City — `db/civic.db` schema

Normalized relational database over Riverton's civic vote data (Salt Lake County, Utah). It lets
you join **Planning Commission ↔ City Council** votes by real keys instead of fuzzy text. **Two
layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's `db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use items) its project *application*, resolved **within each body**. A Council "Foo" and a
   PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data* (each
   body keys only to itself), so it is reconstructed by record linkage in the separate `referral`
   table — every link is confidence-scored and overridable, and the genuine single-body majority
   is left **explicitly unlinked**.

Vendor: a **prose/PDF minutes portal** (Granicus mirrored on Utah PMN; born-digital text — no
structured agenda/matter IDs). Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council) and `planning_commission/all_votes.csv`
(PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
`db/referrals_audit.csv` lists every referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 2 | Council, PlanningCommission |
| person | 27 | councilmembers + commissioners + movers/seconders (incl. Mayor Staggs, tie-break only) |
| meeting | 246 | one row per (body, source minutes file) — Council 128 + PC 118 |
| application | 515 | body-scoped land-use/policy projects |
| motion | 1,523 | **Council 851 · PlanningCommission 672** |
| vote | 4,208 | named member-vote rows (see reconciliation) |
| role | 27 | per person×body first/last vote + count |
| referral | 59 | reconstructed cross-body links — **24 high / 23 medium / 12 low** |

Contested motions (any Nay/Abstain/Recuse): **130** (`v_contested`). Riverton is a high-consensus
council; most majorities pass with a named roll call (Council) or an unnamed "unanimous consent"
tally (PC). `vote_value` distribution: **Aye 3,992 · Nay 193 · Abstain 10 · Recuse 9 · Absent 4**.

## Standard schema
```
body(body_id, name UNIQUE, kind∈council/commission)
person(person_id, full_name, name_key UNIQUE)          -- name_key = normalized for joins
meeting(meeting_id, body_id, meeting_date, title, source_file, UNIQUE(body_id,source_file))
application(application_id, app_key UNIQUE, body_id, name, rep_title)   -- the project/matter
motion(motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
       outcome, stage, recommendation, application_id, app_match_method, app_confidence,
       mover_person_id, seconder_person_id, names_recorded, source_file, provenance)
       -- provenance: 'minutes' = audited series; 'pmn_minutes' = the 7 meetings promoted
       -- from pmn_backfill/ 2026-07-16 (34 Council + 10 PC motions)
vote(vote_id, motion_id, person_id, vote_value, UNIQUE(motion_id,person_id))
role(role_id, person_id, body_id, first_seen, last_seen, n_votes, UNIQUE(person_id,body_id))
referral(referral_id, primary_application_id, primary_body, related_application_id,
         related_body, match_method, confidence, shared_address, subject_score,
         primary_date, related_date, gap_days, note, UNIQUE(primary,related))
```
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent (Riverton uses all five). `outcome` ∈
Pass/Fail/Continued/Died. `stage` ∈ council_vote/pc_recommendation/pc_final_action/other_action.
`PRAGMA foreign_keys=ON`; indexed on `motion.application_id`, `vote.person_id`,
`motion.meeting_id`, `application.body_id`, `referral.{primary,related}_application_id`.

## The Mayor and the one tie-break (normalization note)
**Form of government:** six-member council — five district councilmembers (D1–D5) + a
separately-elected **Mayor** who **does not vote on ordinary motions** (the **Park City model**);
all normal tallies top out at 5. The Mayor votes only to break a tie (or on manager
hiring/firing / mayoral-powers amendments).

**The single mayor-vote in the corpus: 2025-12-16, Resolution No. 25-62** (skate-facility
removal). The council split **2–2** (McDougal + Pierucci Aye, Buroker + McCay Nay) and **Mayor
Trent Staggs cast the tie-breaking Aye → passed.** In the flat `meeting_minutes/all_votes.csv`
this is stored **verbatim** as `result = "Passed (Mayor tie-break)"` with the vote value
`Aye (Mayor tie-break)`. **In this DB the tie-break vote is NORMALIZED to a plain `vote_value =
'Aye'`** (Trent Staggs → 1 vote row, 1 role entry) — the verbatim marked value lives only in the
flat CSV, per the collection's cardinal rule that city-faithful values are never overwritten and
normalized forms live alongside. This mirrors South Jordan's mayor-tie-break handling (a faithful
ordinary vote row); Park City itself keeps a `vote.note` — Riverton does not use a note field.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, and
procedural motions correctly get **no application** (NULL). Resolution tiers as built:

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | **360** | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | **198** | a named development/rezone/annexation grouped by normalized name (heuristic) |
| (NULL) | — | **965** | non-land-use motion → no application |

Riverton's minutes are **prose, not file-number keyed** — the PC cites application numbers
inline (`PLZ ##-####`) but the Council is ordinance/resolution-keyed, so there is no exact shared
prose key across bodies (the `singleton` tier gives each land-use motion an exact within-body
identity even where the project name is unstated).

## Cross-body `referral` layer — methodology
Reconstructed in `build_referrals.py` (grain: application↔application between the two bodies;
`primary_body` = the higher-authority side, Council > PlanningCommission). Signals: **address**
(shared Utah grid pair / named-street address) > **subject** (IDF-weighted title-token agreement —
symmetric Jaccard + asymmetric name-anchored containment). **Temporal is a gate, not a signal**:
a PC→Council pair requires the PC to precede the Council within the forward window.
`db/referral_overrides.csv` (`primary_application_id,related_application_id,action∈link/suppress,
note`) forces or kills a pair. Confidence: **high** ≈ address+subject+temporal · **medium** =
strong subject+temporal · **low** = address-/gate-only (flag; do not quote).

**Result — 59 links: 24 high / 23 medium / 12 low.** The Council's terse ordinance/resolution-
keyed minutes carry no exact PC file number, so every cross-body link falls to address + subject +
temporal — a genuine data characteristic reported on every build, not a bug. Review the full set
in `db/referrals_audit.csv`.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **4,208 CSV named rows = 4,208 db vote rows, 0 dropped** (validator `h.db`: delta +0). The build
  aborts if any row is dropped without a documented override.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged.
- **Tally-only / unnamed-majority style.** Council prints named roll calls on 719 of 851 motions
  (132 tally-only); PC names members **only on divided votes** (127), leaving unanimous majorities
  honestly unnamed (538 placeholders) + 7 died-for-lack-of-second. `names_recorded` is 1 when any
  member row exists; the normalization layer never infers unnamed Ayes.
- Corrections go through the override CSVs (`db/referral_overrides.csv`) + rebuild — never
  in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names,
  both dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus council;
  **130** motions).

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
