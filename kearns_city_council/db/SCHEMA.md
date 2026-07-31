# Kearns City — `db/civic.db` schema

Normalized relational database over Kearns's civic vote data (Salt Lake County,
Utah). It lets you join **Planning Commission ↔ City Council** votes by real keys
instead of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person,
   and (for land-use items) its project *application*, resolved **within each body**.
   A Council item and a PC item are DISTINCT applications; nothing is merged across
   bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** "The Council decided what the
   Planning Commission first recommended" is absent from the source data (each body
   keys only to itself), so it is reconstructed by record linkage in the `referral`
   table — every link is confidence-scored and overridable.

Vendor: **Utah PMN** prose/PDF minutes (no structured agenda/matter IDs). Built from
the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council) and `planning_commission/all_votes.csv`
(PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv`
lists every referral with both titles, score, and day-gap for review.

## Current contents (as built, 2026-07-12)

| table | rows | notes |
|---|---|---|
| body | 2 | Council, PlanningCommission |
| person | 16 | councilmembers + commissioners + movers/seconders |
| meeting | 74 | Council 31 · PlanningCommission 43 (one Council file = Board of Canvassers, 0 motions, no meeting row) |
| application | 53 | body-scoped land-use/policy projects |
| motion | 375 | Council 178 · PlanningCommission 197 |
| vote | 5 | named member-vote rows (narrative-tally city — see below) |
| role | 4 | per person×body first/last vote + count (only for named voters) |
| referral | 2 | reconstructed cross-body links (both `medium`) |

Contested motions (any Nay/Abstain/Recuse): **5** (`v_contested`) — Kearns is a
high-consensus, narrative-tally council. The one contested Council motion is the
`2026-05-11` Colby abstain (R2026-12, 4-0).

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Kearns records only
**Abstain** as a named non-aye — the tally style names no individual ayes/nays).
`outcome` ∈ Pass/Fail/Continued/Died. `stage` ∈ council_vote/rda_vote/mba_vote/
ha_vote/boa_action/other_action/pc_recommendation/pc_final_action. `PRAGMA
foreign_keys=ON`; indexed on the usual FK columns.

## Bodies & voting notes

- **Two governing regimes (hard seam at the 2024-05 city conversion / Nov-2025 first
  city election).** Township era (2017-2025): 5-member council, elected Chair styled
  "Mayor," no separate executive. City era (Jan 2026 →): **the elected Mayor VOTES**
  — city-era full rolls tally 5-0 with only 4 councilmembers, so the 5th is the
  mayor's (max roll = 5, mayor included). See root `CLAUDE.md` §1.
- **Narrative-tally.** Motions name only mover + seconder (+ any dissenter/abstainer);
  the majority is honestly unnamed. So `vote` holds just **5** named rows — this is
  a source property, not record loss. `names_recorded` = 1 when any member row exists.
- **CRA** (Community Reinvestment Agency) convenes in-recess but its own PMN body was
  not acquired → **0 rows / not modeled** (honest gap; would be `body=CRA`, agency).

## Within-body application resolution

Only land-use / policy motions get an `application` (53); budgets, appointments,
contracts, and procedural motions correctly get none. The Planning Commission cites
**`OAM<YYYY>-<NNNNNN>`** file numbers on its land-use items — Kearns's one exact prose
key — and motions sharing an `OAM…` number group into one application. Non-land-use
motions resolve to NULL.

## Cross-body `referral` layer — methodology & finding

Reconstructed in `build_referrals.py` (grain: application↔application between two
different bodies; `primary_body` = higher authority, Council > PlanningCommission).
Signals: **OAM file number** (exact) > **address** > **subject** (IDF-weighted title
token agreement) > **code section**; **temporal is a gate** (PC must precede Council
within ~400 days). `db/referral_overrides.csv` forces/kills a pair. Confidence:
**high** = OAM/address+subject+temporal · **medium** = strong subject+temporal ·
**low** = gate-only (flag; do not quote).

**Result — 2 links, both `medium`** (Council ← PlanningCommission). Kearns's Council
minutes are ordinance/resolution-keyed and cite few OAM numbers, so the strongest key
rarely bridges the two bodies in the flat data and links fall to subject + date. This
is a genuine data characteristic (a small city with a young council record), reported
on every build, not a bug. Respect the confidence column; the genuine single-body
majority is left **explicitly unlinked**.

## Honesty requirements

- **Vote reconciliation is exact and fail-loud.** 5 named CSV rows = 5 db `vote` rows,
  0 dropped, 0 orphan FKs.
- **The within-body core is exact; the `referral` layer is reconstructed inference.**
- **Narrative-tally city** — never infer unnamed ayes.
- Corrections go through the override CSVs (`db/referral_overrides.csv`) + rebuild —
  never in-place edits to the flat CSVs or the `.db`.
- **⚠ Completeness caveat:** the Council record on disk begins 2024-01; the 2017-2023
  township minutes are recoverable on PMN but not yet harvested (see
  `_audits/audit_2026-07-12.md`). The db reflects only what is on disk.

## Views to ship

- `v_referral_chain` — every reconstructed PC→Council link: both app keys, names,
  dates, method, confidence.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome).
- `v_member_record` — per person×body vote tallies (first/last vote, counts).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus
  council).

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
