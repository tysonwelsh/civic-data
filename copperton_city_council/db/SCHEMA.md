# Town of Copperton — `db/civic.db` schema

Normalized relational database over Copperton's civic vote data (Salt Lake County, Utah). It lets
you join **Planning Commission ↔ Town Council** votes and member records by real keys instead of
fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's db schema
spec):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use items) its project *application*, resolved **within each body**. A Council "Foo" and a
   PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data* (each
   body keys chiefly to itself), so it is reconstructed by record linkage in the separate
   `referral` table — every link is confidence-scored and overridable, and the genuine single-body
   majority is left **explicitly unlinked**.

Vendor: a **prose/PDF minutes portal** (GoDaddy town site + Utah PMN; no structured
agenda/matter IDs). Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council) and `planning_commission/all_votes.csv`
(PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
`build_db.py` drops and recreates the whole DB, so **always re-run `build_referrals.py` after
it** (the `referral` table lives only in the second script). Every table is exported to
`db/tables/*.csv` for diffing; `db/referrals_audit.csv` lists every referral with both titles,
score, and day-gap for review.

## Current contents (as built)

| table | rows | notes |
|---|---|---|
| body | **2** | Council (`council`), PlanningCommission (`commission`) |
| person | **17** | councilmembers + planning commissioners + movers/seconders; the presiding Mayor/Chair IS a voter and appears in `vote` |
| meeting | **111** | one row per (body, source minutes file) that carried a motion — Council 94 · PC 17 |
| application | **30** | body-scoped land-use/policy projects (`name`-grouped 3 · `singleton` 27); most motions are non-land-use and get NO application |
| motion | **488** | Council **431** · PlanningCommission **57** |
| vote | **44** | named member-vote rows (see reconciliation) — Aye 26 · Nay 8 · Abstain 10 |
| role | **9** | per person×body first/last vote + count (Council 8 · PlanningCommission 1) |
| referral | **2** | reconstructed cross-body links, both **medium** confidence (see below) |

Data span **2018-07-18 → 2026-05-20**. Contested motions (any Nay/Abstain/Recuse): surfaced by
`v_contested`.

## Standard schema
```
body(body_id, name UNIQUE, kind∈council/agency/commission/committee/department)
person(person_id, full_name, name_key UNIQUE)          -- name_key = normalized for joins
meeting(meeting_id, body_id, meeting_date, title, source_file)
application(application_id, app_key UNIQUE, body_id, name, rep_title)   -- the project/matter
motion(motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
       outcome, stage, recommendation, application_id, app_match_method, app_confidence,
       mover_person_id, seconder_person_id, names_recorded, source_file, provenance)
vote(vote_id, motion_id, person_id, vote_value, UNIQUE(motion_id,person_id))
role(role_id, person_id, body_id, first_seen, last_seen, n_votes, UNIQUE(person_id,body_id))
referral(referral_id, primary_application_id, primary_body, related_application_id, related_body,
         match_method, confidence, shared_address, subject_score, primary_date, related_date,
         gap_days, note)
```
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent (Copperton's record uses **Aye/Nay/Abstain**).
`outcome` ∈ Pass/Fail/Continued/Died. `stage` ∈ council_vote/pc_recommendation/pc_final_action
(+ the collection's other agency stages, unused here — Copperton has no RDA/MBA). `PRAGMA
foreign_keys=ON`.

## Within-body application resolution (`app_match_method` / `app_confidence`)

Only land-use / substantive policy motions get an `application`; budgets, appointments,
contracts, minutes approvals, and procedural motions correctly get **no application** (458
motions, NULL). Copperton's land-use volume is tiny, so there is no case-number key at all:

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | **27** | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | **3** | a named policy item grouped by normalized name (heuristic) |
| (NULL) | — | **458** | non-land-use motion → no application |

There is **no `case_no` tier** — Copperton's clerk does not cite Utah planning case numbers (the
town processes almost no formal land-use cases), so applications are name/singleton only.

## Cross-body `referral` layer — methodology & finding

Reconstructed in `build_referrals.py` (grain: application↔application between the two bodies;
`primary_body` = Council, the higher-authority side). Signals: **address** (shared full Utah grid
pair) > **subject** (IDF-weighted title-token agreement) > **code section**. **Temporal is a
gate, not a signal**: a PC→Council pair requires the PC to precede the Council within ~400 days.
`db/referral_overrides.csv` (`primary_application_id,related_application_id,action∈link/suppress,
note`) forces or kills a pair. Confidence: **high** = address+subject+temporal · **medium** =
strong subject+temporal · **low** = gate-only (flag; do not quote).

**Result — 2 links, both `medium`, all Council ← PlanningCommission** (surfaced by
`v_referral_chain`). With no case-number bridge and a tiny land-use docket, every cross-body link
falls to subject + temporal; there are no high-confidence address rezone matches in this record.
The referral layer is **deliberately thin** — Copperton simply does not run the PC→Council rezone
pipeline that larger cities do. Respect the confidence column: **medium = spot-check, do not quote
as fact.**

## Bodies & voting notes

- **Form of government — the presiding officer VOTES (max tally 5, both eras).** Copperton was a
  **metro township 2017–2024** (5 at-large seats A–E, council-elected chair titled "Mayor/Chair")
  and a **Town from 2024-05-01** (separately-elected VOTING **Mayor Sean Clayton** + 4 Council
  Members). In **both** eras the presiding officer is counted in the roll call — so a full roll
  tops out at **5**, and Mayor/Chair Clayton **does appear in the `vote` table** (e.g. the
  2020-03-18 3-2 splits). This is the Millcreek pattern (mayor votes), the OPPOSITE of
  Taylorsville/South Jordan.
- **No RDA / MBA / agency bodies.** Copperton has only Council + Planning Commission.
- **Roster (join carefully across the 2024 town seam):** township-era Pazell, Patrick, Sorensen,
  Olsen, Severson → town-era Clayton (Mayor), Stitzer, Bailey, McCalmon, Pratt. **Sean Clayton**
  spans the whole record as Mayor/Chair. He is one `person`; a person-level join follows him
  across the seam by design.

## Honesty requirements

- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **44 CSV named rows = 44 db vote rows**, 0 dropped, 0 overrides. The build aborts (non-zero
  exit) if any row is dropped without a documented override. The many tally-only motions
  (unanimous, `names_recorded=0`) correctly contribute a `motion` row but **no `vote` rows** —
  that is the source format, not a drop.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged. Both Copperton referrals are `medium`.
- Corrections go through the override CSV (`db/referral_overrides.csv`) + rebuild — never in-place
  edits to the flat CSVs or the `.db`.

## Views to ship

- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names,
  both dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain, first/last vote).
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
