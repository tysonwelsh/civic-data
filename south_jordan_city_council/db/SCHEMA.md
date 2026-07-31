# South Jordan City — `db/south_jordan.db` schema

Normalized relational database over South Jordan's civic vote data (Salt Lake County, Utah).
It lets you join **Planning Commission ↔ City Council ↔ RDA / MBA** votes by real keys instead
of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's
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

Vendor: a **prose/PDF minutes portal** (no structured agenda/matter IDs). Built from the two
canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council + RDA + MBA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists every
referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 4 | Council, PlanningCommission, RDA, MBA |
| person | 19 | councilmembers + commissioners + movers/seconders |
| meeting | 384 | one row per (body, source minutes file) |
| application | 483 | body-scoped land-use/policy projects |
| motion | 1,759 | Council 1,007 · PlanningCommission 730 · RDA 21 · MBA 1 |
| vote | 1,110 | named member-vote rows (see reconciliation) |
| role | 24 | per person×body first/last vote + count |
| referral | 13 | reconstructed cross-body links (see below) |

Contested motions (any Nay/Abstain/Recuse): **32** (`v_contested`). South Jordan is a
high-consensus, narrative-tally council; most majorities pass with only movers/dissenters named.

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (SJ uses Aye/Nay/Absent/Abstain).
`outcome` ∈ Pass/Fail/Continued/Died. `stage` ∈ council_vote/rda_vote/mba_vote/ha_vote/
boa_action/other_action/pc_recommendation/pc_final_action. `PRAGMA foreign_keys=ON`; indexed on
`motion.application_id`, `vote.person_id`, `motion.meeting_id`, `application.body_id`,
`referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions (and substantive agency motions) get an `application`; budgets,
appointments, contracts, and procedural motions correctly get **no application** (1,268 motions,
NULL). Resolution tiers, strongest first:

| method | conf | count | meaning |
|---|---|---|---|
| `override` | high | 0 | a `db/overrides.csv` row forces `app_key` (none needed) |
| `pl_number` | high | **237** | a Utah planning **file number** `PL…` cited in the motion text (exact) |
| `name` | medium | 21 | a named development/rezone/annexation grouped by normalized name (heuristic) |
| `singleton` | high | 233 | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| (NULL) | — | 1,268 | non-land-use motion → no application |

**The `PL…` file number is South Jordan's one exact prose key.** The Planning Commission cites
`PLPP`/`PLPLA`/`PLCUP`/`PLSPR`/`PLZTA`/`PLZBA`/… numbers on ~1/3 of its motions; all motions
sharing a `PL…` number group into one application (e.g. a recommendation and a later PC final
action on the same case). A cited `PL…` also makes a motion application-worthy even when its
native `motion_type` is `Other`/`Procedural` (e.g. a plat approval labelled Procedural).

## Cross-body `referral` layer — methodology & the key finding
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = the higher-authority side, Council > PlanningCommission > agency).
Signals: **PL file number** (exact) > **address** (shared full Utah grid pair / named-street
address) > **subject** (IDF-weighted title token agreement — symmetric Jaccard and asymmetric
name-anchored containment) > **code section** (specific shared subsection). **Temporal is a
gate, not a signal**: for a PC→Council pair the PC must precede the Council within ~400 days
(60-day forward slack); for agency pairs it is symmetric. `db/referral_overrides.csv`
(`primary_application_id,related_application_id,action∈link/suppress,note`) forces or kills a
pair. Confidence: **high** = PL match, or address+subject+temporal · **medium** = strong
subject+temporal · **low** = address-/gate-only (flag; do not quote).

**Key structural finding — the PL bridge is one-sided (empty across bodies).** The Council's
minutes are terse and **ordinance-number-keyed** ("approve zoning Ordinance 2020-10-Z"): they
cite **0 `PL…` numbers** (232 non-council applications cite one; **0** council applications do;
**0** shared). So the strongest key cannot bridge PC→Council in the flat data, and cross-body
links fall to subject + address + temporal. This is a genuine data characteristic, reported on
every build, not a bug. (A `PL…` cross-body tier is nonetheless implemented and will fire
automatically if a future council motion ever carries one.)

**Result — 13 links: 1 high, 10 medium, 2 low.**
- **Council ← PlanningCommission: 9** (1 high, 6 medium, 2 low) — the classic referral,
  surfaced by `v_referral_chain`. Spot-checked correct: e.g. *Aubrey Cove Rezone 2021-08-Z*,
  *Annexation Policy Plan R2022-26*, *Streetscape Master Plan R2023-11*, and the *9828 S Temple*
  rezone/GPA cluster. Several mediums are carried by a shared resolution/ordinance number that
  both bodies happen to cite (surfaced through the subject signal).
- **Council ← RDA: 4** (medium) — project-area / development-agreement co-actions (e.g. RDA
  2023-04 ↔ Council R2023-34 redevelopment project-area designation).

**Tuning applied (precision over recall).** South Jordan minutes phrasing ("Council Member X
made a motion to approve … as stated") and the small, repeated **mover/seconder surnames** leak
as subject tokens and produced boilerplate fan-out (one tokenless RDA resolution matching
several unrelated zoning ordinances on "member"/"made"/a surname). Those tokens are added to the
IDF `STOP` set in this city's `build_referrals.py`, which removed the false fan-out (25 → 13
links) while leaving every content-bearing link intact. This is the spec's prescribed
"dump-mediums-weakest-first, eyeball, tune" step; the audit CSV records the final set.

## Bodies & voting notes
- **Form of government:** six-member council (Mayor + 5 district councilmembers). The **Mayor
  does not vote** on ordinary council motions — all normal tallies top out at 5.
- **Mayoral tie-break (2025-06-17):** the one time the Mayor voted. **Mayor Dawn R. Ramsey**
  cast a tie-breaking vote on motion 9 (Ordinance 2025-09, a code use-table amendment) — this is
  her single vote row in the data and her only `role` entry on the Council. It is a faithful
  minutes record, stored as an ordinary `vote` row (no special note field, unlike Park City).
- **RDA / MBA** convene *inside* council meetings (recess → agency board → reconvene); their
  open votes are tagged `body=RDA` (21 motions) / `body=MBA` (1 motion) in the council CSV.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **1,110 CSV named rows = 1,110 db vote rows**, **0 dropped, 0 documented overrides**. The build
  aborts (non-zero exit) if any row is dropped without a documented `db/overrides.csv` entry.
  South Jordan has no duplicate or unresolvable rows.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged. Of 184 Council applications, **13 link to
  another body; the rest are correctly UNLINKED** (they have no PC/agency counterpart, or the
  terse ordinance-keyed council text carries no linkable subject).
- **Narrative-tally city.** Many motions name only the mover and any dissenters, leaving the
  majority unnamed (`names_recorded` still 1 when any member row exists). Where a printed tally
  and a partial named roster disagree, the normalization layer keeps the string tally and blanks
  the counted one — never inferring unnamed Ayes. (The `normalize_motions.py` tally cross-check
  agrees on only ~23% of motions-with-both precisely because rosters are partial — expected, not
  an extraction error.)
- **Two documented source clerk errors** (minutes-layer, not corrected here): council
  **2025-08-19** and PC **2022-10-11** carry narrative motion text with embedded commentary /
  ambiguous roll calls (retained verbatim, CSV-quoted). They are audit signals for the minutes
  layer, not db defects; no override was required to build cleanly.
- Corrections go through the override CSVs (`db/overrides.csv`, `db/referral_overrides.csv`) +
  rebuild — never in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC/agency→Council link: both app keys, both project
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
