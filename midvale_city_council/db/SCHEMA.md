# Midvale City — `db/civic.db` schema

Normalized relational database over Midvale's civic vote data (Salt Lake County, Utah). It
lets you join **Planning & Zoning Commission ↔ City Council ↔ RDA ↔ MBA** votes by real
keys instead of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the
collection's db schema spec):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data*
   (each body keys only to itself), so it is reconstructed by record linkage in the separate
   `referral` table — every link is confidence-scored and overridable, and the genuine
   single-body majority is left **explicitly unlinked**.

Vendor: a **prose/PDF minutes portal** (Revize Document Center — no structured agenda/matter
IDs). Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council + in-session RDA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
`db/referrals_audit.csv` lists every referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 4 | Council, PlanningCommission, RDA, MBA |
| person | 33 | councilmembers + commissioners + movers/seconders (Erickson/Erikson merged 2026-07-31) |
| meeting | 287 | one row per (body, source minutes file) — incl. the 24 PMN-promoted docs (2026-07-16) |
| application | 487 | body-scoped land-use/policy projects |
| motion | 2,186 | council_vote 1,428 · pc_final_action 465 · pc_recommendation 204 · rda_vote 84 · mba_vote 5; `provenance` = `minutes` 2,007 / `pmn_minutes` 179 |
| vote | 5,752 | named member-vote rows (see reconciliation) |
| role | 31 | per person×body first/last vote + count |
| referral | 113 | reconstructed cross-body links: **42 high / 53 medium / 18 low** |

Contested motions (any Nay/Abstain/Recuse): **55** (`v_contested`). Midvale is a high-consensus
council, but — unlike the narrative-tally cities — it prints **named roll calls**, so majorities
are named too. `outcome`: Pass 2,176 / Fail 8 / **Died 2**. (Counts as of the 2026-07-31 debt
wave — the four phantom meetings removed, the two died-for-lack-of-a-second motions rescued
from a default `Pass`/`Fail`, and the Erickson/Erikson person split merged. Earlier figures in
this doc's history predate those repairs.)

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent (Midvale: Aye 4,869 · Absent 145 · Nay 70 ·
Abstain 1 · Recuse 1). `outcome` ∈ Pass/Fail. `stage` ∈ council_vote/rda_vote/
pc_recommendation/pc_final_action. `provenance` = `minutes` for every row (Midvale has no PMN
backfill layer). `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`, `vote.person_id`,
`motion.meeting_id`, `application.body_id`, `referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions (and substantive agency motions) get an `application`; budgets,
appointments, contracts, and procedural motions correctly get **no application** (1,665 motions,
NULL). Midvale's terse minutes cite **no planning file-number key** (unlike South Jordan's
`PL…`), so resolution falls to name-grouping and singleton identity:

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | **400** | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | **134** | a named development/rezone/annexation grouped by normalized name (heuristic) |
| (NULL) | — | 1,665 | non-land-use motion → no application |

## Cross-body `referral` layer — methodology
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = the higher-authority side, Council > PlanningCommission > RDA).
Signals: **address** (shared full Utah grid pair / named-street address) > **subject**
(IDF-weighted title-token agreement) > **code section**. **Temporal is a gate, not a signal**
(a PC→Council pair requires the PC to precede the Council within a bounded window).
`db/referral_overrides.csv` (`primary_application_id,related_application_id,action∈link/suppress,
note`) forces or kills a pair. Confidence: **high** = address+subject+temporal (**40**) ·
**medium** = strong subject+temporal (**44**) · **low** = address-/subject-only, flag, do not
quote (**15 address + 2 subject = 17**).

**No file-number bridge exists in Midvale's minutes** (it is ordinance/resolution-keyed, not
`PL…`-keyed), so every cross-body link falls to address + subject + temporal. This is a genuine
data characteristic, reported on every build, not a bug.

## Bodies & voting notes
- **Form of government:** six-member council (Mayor + 5 district councilmembers). The **Mayor
  votes ONLY to break a tie** — all normal tallies top out at 5.
- **Mayoral tie-break (2020-05-05):** the one time a Mayor voted. **Mayor Robert Hale** cast a
  tie-breaking Aye on motion 14 (a subdivision amendment) — his single `vote`/`role` row.
  ⚠ The source states the motion **passed 3-2** after his tie-break, but this OCR-era row's
  `result_raw` reads **"2-2 Fail"** (the pre-tie-break tally); the member rows are correct.
  A `db/vote_overrides.csv` correction is queued (`VERIFICATION.md` D2) — do not quote the
  `outcome`/`result_raw` for this one motion.
- **The Gettel council→mayor transition:** **Dustin Gettel** is a councilmember (D5) through
  2024-12-10, then becomes Mayor (appointed Jan 2025, elected Nov 2025); his 2020–2024 vote
  rows are legitimate councilmember votes. "Mayor Stevenson" (Marcus Stevenson) is the
  2022–2024 mayor and does not appear in the vote data (mayors don't vote except on ties).
- **RDA** convenes *inside* council meetings (recess → agency board → reconvene); its open
  votes are tagged `body=RDA` — 35 in-session motions in the audited CSV **plus 49 motions
  from standalone RDA board docs** PMN-promoted 2026-07-16 (`provenance=pmn_minutes`; 84
  total). **MBA** (Municipal Building Authority) is a standalone-doc body, 5 motions, all
  `pmn_minutes`.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **5,752 CSV named rows = 5,752 db vote rows**, exact **by body** (Council 3,777 · RDA 245 ·
  MBA 10 · PlanningCommission 1,720). (Council dropped 50 rows at the 2026-07-31 phantom-meeting
  removal; the same-day Erickson/Erikson merge re-keys 13 PC rows without changing any count.)
- **One documented same-day duplicate.** Council **2025-08-19** carries two indexed minutes
  docs (Regular + Truth-In-Taxation) that both print the same 5-0 consent roll call; the flat
  CSV holds both (10 rows), but the db's `UNIQUE(motion_id,person_id)` keeps each meeting's
  motion at a clean **5** votes (`motion_id 1122` = 5). **0** person appears twice within any
  motion. Logged in root `TODO.md`.
- **OCR-era person artifacts.** A handful of `person` rows are OCR name-garble from the
  2020–2021 scanned minutes (e.g. `Oustin Gettel`, `Paul Gettel`, `Hale called`) — ~0.4% of
  OCR-era rows; canonical names dominate. Fold-in is queued (`VERIFICATION.md` §e).
- The within-body core is exact; the `referral` layer is reconstructed inference — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged.
- **`db/person_aliases.csv` — the same-person override file (2026-07-31).**
  `raw_name,canonical_name,evidence`, the convention shared with the cache_county /
  utah_county / wfrc_mpo builders. It exists because the CITY sometimes misspells its own
  official: the born-digital 2022-08-10 / 09-14 / 09-28 PC minutes print `Candice Erickson`
  in the roll of members but `Commissioner Erikson` in the roll-call cells. The flat
  `all_votes.csv` keeps the verbatim spelling (cardinal rule 2); the merge is db-only.
  `db/build_db.py` applies it by wrapping the shared `db_build_lib.norm_person` — the one
  funnel every member/mover/seconder string passes through — so the shared library is
  untouched and the canonical DISPLAY name is set by decision, not by sort order. Every row
  must carry positive same-person evidence (one such official on the body; the variants never
  co-occur on a motion; the variant falls inside the canonical person's service).
- **`outcome='Died'` is a real, distinct value here** (2 motions): a motion that died for want
  of a second never reached a vote, so it is neither Pass nor Fail. Both carry
  `result_raw='Died (no second)'` and `names_recorded=0`. Do not fold them into `Fail`.
- Corrections go through the override CSVs (`db/person_aliases.csv`, `db/vote_overrides.csv`,
  `db/referral_overrides.csv`) + rebuild — never in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC/RDA→Council link: both app keys, both project
  names, both dates, method, confidence, shared address, subject score.
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
