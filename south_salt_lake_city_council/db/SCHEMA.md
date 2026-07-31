# South Salt Lake City — `db/civic.db` schema

Normalized relational database over South Salt Lake's civic vote data (Salt Lake County,
Utah). It lets you join **Planning Commission ↔ City Council ↔ RDA** votes by real keys
instead of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the
collection's `db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
   `build_db.py` reports **0 applications spanning >1 body**.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The relationship "the Council decided
   what the Planning Commission first recommended" is *absent from the source data* (each
   body keys only to itself), so it is reconstructed by record linkage in the separate
   `referral` table — confidence-scored and overridable, with the genuine single-body
   majority left **explicitly unlinked**. **Since the 2026-07-16 ArchivedMinutes promotion
   the referral layer holds 43 links** (it was honestly EMPTY before — the coverage cliff
   removed the Council side; see below).

Source: **Utah Public Notice (PMN)** + the CivicPlus AgendaCenter `ArchivedMinutes`
recoveries promoted 2026-07-16 (prose/PDF minutes; no structured agenda / matter IDs).
Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council + RDA) and
`planning_commission/all_votes.csv` (PlanningCommission); the flat `provenance` column
(minutes | agendacenter_minutes) is carried into `motion.provenance`.

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists
every referral candidate with both titles, score, and day-gap for review.

## Current contents (as built 2026-07-16, post-ArchivedMinutes-promotion)
| table | rows | notes |
|---|---|---|
| body | 3 | Council, PlanningCommission, RDA |
| person | 27 | councilmembers + commissioners + movers/seconders |
| meeting | 192 | one row per (body, source minutes file) that carried ≥1 motion |
| application | 270 | body-scoped land-use/policy projects (8 `name`, 262 `singleton`; 696 non-land-use motions NULL) |
| motion | 966 | Council 555 · PlanningCommission 286 · RDA 125 (provenance: 374 `minutes`, 592 `agendacenter_minutes`) |
| vote | 6,253 | named member-vote rows (see reconciliation) |
| role | 37 | per person×body first/last vote + count |
| referral | 43 | reconstructed cross-body links (40 Council←RDA, 3 Council←PC; all `medium`) |

Contested motions (any Nay/Abstain/Recuse): **68** (`v_contested` — Council/RDA 56, PC 12).
SSL is a high-consensus council.

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent (SSL uses Aye/Nay/Absent/Abstain).
`outcome` ∈ Pass/Fail. `stage` ∈ council_vote/rda_vote/pc_recommendation/pc_final_action.
`PRAGMA foreign_keys=ON`; indexed on `motion.application_id`, `vote.person_id`,
`motion.meeting_id`, `application.body_id`, `referral.{primary,related}_application_id`.

Stage distribution (as built): `council_vote` 555 · `pc_final_action` 252 · `rda_vote` 125 ·
`pc_recommendation` 34.

## The `result_raw` string is SYNTHESIZED (SSL prints no result)
South Salt Lake's minutes print **no "motion passed" string** — only a per-member roll call.
So `result_raw` (and the flat CSV `result`) is the **synthesized tally `"<aye>-<nay>
Pass|Fail"`** derived from the actual roll (abstains/absents excluded from the aye/nay count;
e.g. a 5-Aye/0-Nay/1-Abstain roll → `"5-0 Pass"`). This is honest — it is *computed from* the
recorded votes, not invented. `validate_city.py`'s `f.tally` check confirms **676/676
(Council/RDA) and 285/285 (PC) synthesized tallies equal the counted member rows** (the
excluded motions are tally-only — no named roll printed).

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts and
procedural motions correctly get **no application** (696 motions, NULL). SSL's PMN minutes
carry **no Utah `PL…` planning file numbers** (unlike South Jordan) — items are titled in
prose — so land-use motions resolve as **`singleton`** (an unnamed land-use/policy motion →
its own application, exact identity, name unknown; 262) or **`name`** (a named
development/rezone grouped by normalized name; 8). There is no exact prose case key to bridge
bodies here.

## Cross-body `referral` layer — methodology & the finding
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = higher authority, Council > PlanningCommission > agency). Signals:
address (shared Utah grid pair / named-street address) > subject (IDF-weighted title token
agreement) > code section; **temporal is a gate** (a PC→Council pair needs the PC to precede
the Council within ~400 days). `db/referral_overrides.csv` forces/kills a pair. Confidence:
**high** = address+subject+temporal · **medium** = strong subject+temporal · **low** =
address-/gate-only.

**Finding (updated 2026-07-16) — the layer was EMPTY (0 links) before the ArchivedMinutes
promotion, honestly: the coverage cliff removed the Council side of nearly every PC/RDA
pipeline.** The promotion restored the 2022-09→2026 council record and re-running
`build_referrals.py` surfaced **43 links** exactly as the pre-promotion finding predicted:
**40 Council←RDA** (budget/property resolutions heard by both boards) and **3
Council←PlanningCommission**, all `medium` (subject+temporal — SSL still has no exact prose
key, so no `high` links are possible without an address match). The PC side remains thin
because 2020–2021 PC minutes were never published and PC recommendations are sparse
(34 `pc_recommendation` motions). `db/referrals_audit.csv` lists every scored candidate.

## Bodies & voting notes
- **Form of government:** **strong-mayor (council–mayor).** A **7-member council** (5
  districts + 2 At-Large) legislates; the separately-elected **executive Mayor does NOT vote**.
  Every normal Council/RDA roll tops out at **7**; the build asserts **0 mayor-in-roll rows and
  0 motions with >7 voters** (Mayor Cherie Wood appears in the minutes only as a *presenter*,
  never in a tally, and is absent from `person`).
- **RDA** convenes as a separate PMN body (1296) the same Wednesday; the RDA board **is** the
  seven councilmembers (Mayor = non-voting Executive Director). RDA open votes are tagged
  `body=RDA` (125 motions) in the council CSV. 19 RDA dates remain agenda-only/no-action
  (honest source limit).
- **Planning Commission** (body 1297, Thursday) uses its own commissioner roster and a
  distinct `Commissioner <Name> – Aye;` vote grammar; up to 8 seats.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **6,253 CSV named rows = 6,253 db vote rows**, delta 0, 0 dropped, 0 overrides. (The 5 CSV
  rows with a blank member — tally-only motions, `names_recorded=0` — are correctly NOT
  `vote` rows: 6,258 total CSV rows − 5 blank = 6,253.) `validate_city.py`
  `h.db` confirms the exact reconciliation.
- **Synthesized `result` is derived, never invented** (see above). A blank member on a
  tally-only procedural motion is honest source style, not an extraction miss.
- **A faithful source typo is retained, not merged:** the PC roster carries both
  `Oliva Spencer` and `Olivia Spencer` (the clerk mis-typed one meeting) as a near-duplicate
  `person`; it is left verbatim rather than silently collapsed.
- Corrections go through the override CSVs (`db/referral_overrides.csv`, and a
  `db/overrides.csv` if ever needed) + rebuild — never in-place edits to the flat CSVs or the
  .db.
- **`db/vote_overrides.csv` (added 2026-07-17)** — documents the two clerk-typo vote lines
  that leave Huff honestly unrecorded in the flat CSVs (2024-02-28 RDA m2 `Huff: Ye`;
  2026-01-14 Council m3 `Huff: Y/es` — both unambiguous typos for `Yes`), with
  verbatim-source citations. ✅ **APPLIED since 2026-07-17 (same day):** the shared
  `scripts/db_build_lib.py` gained an **add-member** override kind (SCHEMA_SPEC §
  reconciliation invariant) — an override row whose member has NO CSV row for the motion
  ADDS the corrected vote to the db (`+2 added by override (missing-member)` in the build's
  reconciliation line); the flat `all_votes.csv` stays verbatim-faithful (no Huff row —
  the source value is garbled). `validate_city.py`'s `h.db` formula now counts add-member
  rows at −1 (`expected = db_votes + conflict_overrides − add_overrides`) and SSL
  **reconciles exactly** (the former standing `delta -2` WARN is resolved). Stale override
  rows (member already recorded, unknown motion, unconsumed `exclude`) fail the build loudly.

## Views to ship
- `v_referral_chain` — every reconstructed PC/agency→Council link (43 rows).
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (68 — the signal on a consensus council).

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
