# Town of Alta — `db/civic.db` schema

Normalized relational database over Alta's civic vote data (Salt Lake County, Utah; a ~380-
resident Little Cottonwood Canyon ski town). It lets you join **Planning Commission ↔ Town
Council** votes by real keys instead of fuzzy text. **Two layers, never conflated** (per
`SCHEMA_SPEC.md` and the collection's `db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use items) its project *application*, resolved **within each body**. A Council "Foo" and a
   PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data* (each
   body keys only to itself), so it is reconstructed by record linkage in the separate `referral`
   table — confidence-scored and overridable. **For Alta this table is empty (0 links) — an honest
   result, not a bug** (see below).

Vendor: **Utah Public Notice (PMN)** — a prose/PDF minutes portal (no structured agenda/matter
IDs). Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council) and `planning_commission/all_votes.csv`
(PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists any
candidate referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 2 | Council, PlanningCommission |
| person | 18 | 9 council voters + 6 PC commissioners/movers + **3 malformed mover-text rows** (see below) |
| meeting | 96 | Council 79 (meetings with ≥1 motion) + PlanningCommission 17 |
| application | 24 | body-scoped land-use/policy projects (Council 20 · PC 4) |
| motion | 527 | Council 480 · PlanningCommission 47 |
| vote | 726 | named member-vote rows (Council only; PC is 100% tally-only) |
| role | 9 | per person×body first/last vote + count (the 9 real council voters) |
| referral | 0 | reconstructed cross-body links — **none** (see §referral) |

Contested motions (any Nay/Abstain/Recuse): **13** (`v_contested`). Vote-value mix: **Aye 706 ·
Nay 16 · Abstain 4**. Alta is a very high-consensus council; most motions pass unanimously.

## THE MAYOR VOTES (Utah Town form — max roll = 5)
Alta's Mayor is an **ordinary voting member**, not a non-voting executive. A full council roll
call = **5** (Mayor + 4 at-large councilmembers). There is **no tie-break special-casing** — the
Mayor's vote is a plain `vote` row like any member's (contrast Park City / Riverton, where the
mayor votes only to break ties, and Taylorsville / South Jordan, where the mayor never votes).
`role` shows **Roger Bourke** as the top voter (156 votes; Mayor 2021→present; **Harris Sondak**
was Mayor in 2020, Bourke a councilmember then). Every real voter tops out at ≤5 on a roll call
(0 ceiling breaches).

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Alta uses **Aye/Nay/Abstain**).
`outcome` ∈ Pass/Fail/Continued/Died (Alta: **Pass 520 · Fail 7**). `stage` ∈
council_vote/pc_recommendation/pc_final_action/… (Alta: **council_vote 480 · pc_final_action 45 ·
pc_recommendation 2**). `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`,
`vote.person_id`, `motion.meeting_id`, `application.body_id`,
`referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, and
procedural motions correctly get **no application** (503 motions, NULL). Alta has no Utah `PL…`
planning file-number convention, so every application is a **`singleton`** (an unnamed land-use /
policy motion → its own application, exact identity, name unknown):

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | **24** | a land-use/policy motion → its own application (Council 20 · PC 4) |
| (NULL) | — | 503 | non-land-use motion → no application |

## Cross-body `referral` layer — **empty by design (0 links)**
`build_referrals.py` (shared `scripts/referrals_lib.py`) reconstructs application↔application
links between the two bodies using PL number (Alta has none) > address > IDF-weighted subject >
code section, temporal-gated. **For Alta it finds 0 links, which is correct:**
- The **PC is tiny** (17 meetings, 47 motions — mostly Alta Ski Area conditional-use permits and
  plat items) and produced no minutes at all in 2020–2021.
- Council motions are **resolution/ordinance-keyed** (`2022-R-18`, `2022-O-5`) with **no shared
  land-use case key** the PC also cites, so nothing bridges the two bodies in the flat data.
- `db/referral_overrides.csv` (`primary_application_id,related_application_id,action∈link/suppress,
  note`) can force or kill a pair if a genuine referral is later identified; none is warranted now.

This is an honest empty (a genuine data characteristic of a town this small), not a build
failure. The referral machinery is present and will fire automatically if a future PC
recommendation and a Council adoption ever share a linkable key.

## Bodies & voting notes
- **Form of government:** Utah **Town** form — **Mayor + 4 at-large councilmembers**, all seats
  at-large (no districts). **The Mayor votes** (max roll 5). Non-partisan, staggered 4-year terms.
- **Planning Commission** is the town's **Land Use Authority** + General Plan author; the Mayor
  sits **ex officio**. PC votes are 100% narrative "unanimous consent" → **tally-only** (0 named
  member rows; `vote` is Council-only). A blank PC roster is a source ceiling, not a loss.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote CSV row lands in `vote`:
  **726 CSV named rows = 726 db vote rows, 0 dropped, 0 overrides.** The build aborts (non-zero
  exit) if any row is dropped without a documented override.
- **The within-body core is exact; the `referral` layer is reconstructed inference** (here empty).
- **Tally-only majorities are honestly unnamed.** On a unanimous council motion with a
  `VOTE: All in favor` style, `member`/`vote` are blank (one placeholder motion) — no member is
  ever guessed. Named per-member rows appear on roll-call and in-favor/against motions.
- **3 malformed `person` rows** (`Contract. He`, `Council. Davis`, `Was`) are mover/seconder text
  artifacts from a few garbled minutes lines; each has **0 votes** and is mover/seconder on **1**
  motion, so they never enter a tally and do not affect the 726==726 reconciliation. Cosmetic;
  regenerate cleanly if the mover-name normalizer is tightened. See `VERIFICATION.md §8`.
- Corrections go through the override CSVs (`db/referral_overrides.csv`) + rebuild — never
  in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — reconstructed PC→Council links (currently returns 0 rows — see above).
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (**13** — the signal on a consensus council).

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
