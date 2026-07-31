# White City — `db/civic.db` schema

Normalized relational database over White City's civic vote data (Salt Lake County, Utah). It
lets you query motions, votes, members, and land-use applications by real keys instead of fuzzy
text. **Two layers, never conflated** (per `SCHEMA_SPEC.md §5`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use items) its project *application*, resolved **within each body**. `build_db.py` reports
   **0 applications spanning >1 body** by design.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The `referral` table links applications across
   bodies. **White City has only one body in the record (the Council), so `referral` is empty (0
   rows)** — there is no Planning Commission or agency minutes series to link to (the PC publishes
   no minutes; see `planning_commission/AVAILABILITY.md`). The layer exists and will populate
   automatically if a second body's votes are ever acquired.

Vendor: **Streamline CMS** prose/PDF minutes (no structured agenda/matter IDs). Built from the one
canonical flat CSV, which is never modified: `meeting_minutes/all_votes.csv` (Council only —
`planning_commission/all_votes.csv` is header-only).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (empty here; run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing.

> ⚠ **Running `db/build_db.py` drops and recreates all tables** (including any referral table).
> A read-only analysis should query `db/civic.db` directly and NOT run the build.

## Current contents (as built, 2026-07-12)

| table | rows | notes |
|---|---|---|
| body | 1 | Council |
| person | 10 | councilmembers + the voting Mayor + movers/seconders |
| meeting | 105 | one row per (body, source minutes file) that carries ≥1 motion (12 no-action sessions carry 0 motions and produce no meeting row) |
| application | 17 | body-scoped land-use/policy singletons |
| motion | 633 | all `body=Council`; outcome Pass 626 / Fail 7 |
| vote | 184 | named member-vote rows (see reconciliation) |
| role | 6 | per person×body first/last vote + count — only the 6 people who cast a NAMED vote |
| referral | 0 | single body — nothing to link (see above) |

Contested motions (any Nay/Abstain/Recuse): see `v_contested`. White City is a high-consensus,
largely narrative-tally council; **most majorities pass with only the mover/seconder and any
dissenter named** — 569 of 753 flat rows are tally-only placeholders (no member).

## Standard schema
```
body(body_id, name UNIQUE, kind∈council/agency/commission/committee/department)
person(person_id, full_name, name_key UNIQUE)          -- name_key = normalized full name for joins
meeting(meeting_id, body_id, meeting_date, title, source_file, UNIQUE(body_id,source_file))
application(application_id, app_key UNIQUE, body_id, name, rep_title)   -- the project/matter
motion(motion_id, meeting_id, body_id, motion_no, motion_text, motion_type, result_raw,
       outcome, stage, recommendation, application_id, app_match_method, app_confidence,
       mover_person_id, seconder_person_id, names_recorded, source_file, provenance)
vote(vote_id, motion_id, person_id, vote_value, UNIQUE(motion_id,person_id))
role(role_id, person_id, body_id, first_seen, last_seen, n_votes, UNIQUE(person_id,body_id))
referral(referral_id, primary_application_id, primary_body, related_application_id, related_body,
         match_method, confidence, shared_address, subject_score, primary_date, related_date,
         gap_days, note, UNIQUE(primary,related))   -- empty for White City
```
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused — **White City uses only Aye/Nay/
Abstain** (Aye 148, Nay 24, Abstain 12 = 184; a recording ceiling, §4 of the spec). `outcome` ∈
Pass/Fail/Continued/Died (White City: Pass/Fail). `provenance` = `minutes` for every row (no PMN
recovered votes). `PRAGMA foreign_keys=ON`.

## Within-body application resolution (`app_match_method` / `app_confidence`)

Only land-use / policy motions get an `application`; budgets, appointments, procedural motions get
none (NULL). White City minutes carry **no planning file-number key** (unlike South Jordan's `PL…`),
so land-use motions resolve as **singletons** (each its own application, exact identity, name from
the motion text):

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | 17 | an unnamed/uniquely-named land-use or policy motion → its own application |
| (NULL) | — | 616 | non-land-use motion → no application |

## Bodies & voting notes

- **Form of government changed mid-record** (see the repo `README.md`/`CLAUDE.md`): **White City
  Metro Township** (2017 → 2024-05-01) → **City** (Utah HB35 2024). Across both eras the voting
  body is **5 people and the Chair/Mayor VOTES** — `Allan Perry` (the elected Mayor from 2026) has
  30 `vote` rows; a full roll call tops out at **5**, never 6. This is the Millcreek model, not the
  non-voting-mayor form.
- **`role` has 6 rows, `person` has 10.** Only 6 people ever cast a *named* vote (Scott Little,
  Tyler Huish, Allan Perry, Greg Shelton, Linda Price, Neil Mahoney). The other 4 (Cutler,
  Dickerson, Flint, Cardenaz) appear only as movers/seconders in the pre-2026 narrative-tally era
  and honestly have no `role` row — a recording limit, not a data miss.
- **No agency/PC bodies** in the record — Council only.

## Honesty requirements

- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **184 CSV named rows = 184 db vote rows, 0 dropped, 0 overrides.** The build aborts (non-zero
  exit) if any row is dropped without a documented override.
- **Narrative-tally city.** Many motions name only mover + seconder (+ any dissenter), leaving the
  majority unnamed. The db never infers unnamed Ayes; a tally-only motion has a `motion` row and
  **0 `vote` rows**. Where a printed tally and a partial named roster disagree (a "unanimous" string
  with a named abstainer), the string is kept verbatim in `result_raw` and no Aye is fabricated —
  this is the `f.tally` validator WARN, by design.
- Corrections go through override CSVs + rebuild — never in-place edits to the flat CSV or the .db.

## Views to ship

- `v_project_timeline` — within-body project history (app_key → date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus council).
- `v_referral_chain` — cross-body links; **empty for White City** (single body).

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
