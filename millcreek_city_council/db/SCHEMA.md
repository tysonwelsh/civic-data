# Millcreek City — `db/millcreek.db` schema

Normalized relational database over Millcreek's civic vote data (Salt Lake County, Utah).
It lets you join **Planning Commission ↔ City Council ↔ CRA** votes by real keys instead
of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's
`db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
   `build_db.py` therefore reports **0 applications spanning >1 body**.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *mostly absent from the source
   data* (each body keys chiefly to itself), so it is reconstructed by record linkage in the
   separate `referral` table — every link is confidence-scored and overridable, and the
   genuine single-body majority is left **explicitly unlinked**.

Vendor: a **prose/PDF minutes portal** (no structured agenda/matter IDs). Built from the two
canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council + CRA) and
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
| body | 3 | Council, PlanningCommission, CRA |
| person | 28 | councilmembers + mayor + commissioners + movers/seconders |
| meeting | 463 | one row per (body, source minutes file) |
| application | 884 | body-scoped land-use/policy projects |
| motion | 3,016 | Council 2,011 · PlanningCommission 759 · CRA 246 |
| vote | 6,721 | named member-vote rows (see reconciliation) |
| role | 35 | per person×body first/last vote + count |
| referral | 34 | reconstructed cross-body links (see below) |

Contested motions (any Nay/Abstain/Recuse): **132** (`v_contested`). Millcreek is a
high-consensus council but records roll calls richly (6,721 named vote rows), so the contested
signal is stronger here than in narrative-tally cities.

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Millcreek uses Aye/Nay/Abstain/
Absent on Council, Aye/Nay/Abstain/Recuse on the Planning Commission).
`outcome` ∈ Pass/Fail/Continued/Died. `stage` ∈ council_vote/cra_vote/rda_vote/mba_vote/
ha_vote/boa_action/other_action/pc_recommendation/pc_final_action (Millcreek uses
council_vote/cra_vote/pc_recommendation/pc_final_action). `PRAGMA foreign_keys=ON`; indexed on
`motion.application_id`, `vote.person_id`, `motion.meeting_id`, `application.body_id`,
`referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions (and substantive agency motions) get an `application`; budgets,
appointments, contracts, and procedural motions correctly get **no application** (2,107 motions,
NULL). Resolution tiers, strongest first:

| method | conf | count | meaning |
|---|---|---|---|
| `override` | high | 0 | a `db/overrides.csv` row forces `app_key` (none needed) |
| `case_no` | high | **262** | a Utah planning **case number** `<PREFIX>-<YY>-<NNN>` cited in the motion text (exact) |
| `name` | medium | 47 | a named development/rezone/annexation grouped by normalized name (heuristic) |
| `singleton` | high | 600 | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| (NULL) | — | 2,107 | non-land-use motion → no application |

**The planning `case number` is Millcreek's exact prose key.** The Planning Commission cites
`CU`/`ZM`/`ZT`/`SD`/`GP`/`EX`/`SV`/`PUD`/… case numbers (format `<PREFIX>-<YY>-<NNN>`, e.g.
`ZM-21-001`, `CU-17-004`) on most land-use motions; all motions sharing a case number group
into one application. A cited case number also makes a motion application-worthy even when its
native `motion_type` is `Other`/`Procedural`. The 3-part format never collides with the 2-part
`Ordinance/Resolution "YY-NN"` numbers Council cites.

## Cross-body `referral` layer — methodology & the key finding
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = the higher-authority side, Council > PlanningCommission > agency).
Signals: **case number** (exact) > **address** (shared full Utah grid pair / named-street
address) > **subject** (IDF-weighted title token agreement — symmetric Jaccard and asymmetric
name-anchored containment) > **code section** (specific shared subsection). **Temporal is a
gate, not a signal**: for a PC→Council pair the PC must precede the Council within ~400 days
(60-day forward slack); for CRA pairs (project-area/finance can precede or follow the land-use
action) it is symmetric. `db/referral_overrides.csv`
(`primary_application_id,related_application_id,action∈link/suppress,note`) forces or kills a
pair. Confidence: **high** = case-number match, or address+subject+temporal · **medium** =
strong subject+temporal · **low** = address-/gate-only (flag; do not quote).

**Key structural finding — the case-number bridge is thin but genuinely two-sided.** Unlike
South Jordan (whose PC `PL…` numbers never appear in the terse, ordinance-keyed council text,
so the strongest key can't bridge), Millcreek's Council occasionally cites the PC case number
verbatim: **233 non-council applications cite a case number, 6 council applications do, and 3
are shared council↔PC** → 3 exact `case_no` cross-body links. The rest of the cross-body links
fall to subject + address + temporal.

**Result — 34 links: 10 high, 19 medium, 5 low.**
- **Council ← PlanningCommission: 21** — the classic referral, surfaced by `v_referral_chain`.
  Spot-checked correct: e.g. the *4277 S 500 E* rezone (Ordinance 19-31 ↔ ZM-19-001), the
  *857 E 4315 S* rezone (Ordinance 20-57 ↔ ZM-20-010), the *4080/4090 S Highland Dr* mixed-use
  master development agreement, and station-area plans (Murray North, Meadowbrook).
- **Council ← CRA: 13** — project-area plan/budget, participation-agreement, and inter-fund-loan
  co-actions where the Council ordinance and the CRA resolution are adopted the same night
  (gap=0), e.g. Woodland Avenue / Olympus Hills / Canyon Rim Commons Community Reinvestment
  Project Area plans, and the Opus Green development agreement.

**Tuning applied (precision over recall).** Millcreek minutes name movers/seconders and members
richly ("Council Member Bev Uipi made a motion…"), so those names leak as subject tokens; every
Millcreek council/PC member + mover/second surname and first name is added to the IDF `STOP`
set in this city's `build_referrals.py`. Three `PlanningCommission ← CRA` candidates were false
(a consent-agenda "items 2.2–2.4" blob, a procedural "go back into the public meeting", and a
meeting-minutes-approval match) and are **suppressed via `db/referral_overrides.csv`** (37 → 34
links). This is the spec's prescribed "dump-mediums-weakest-first, eyeball, tune" step; the
audit CSV records the final set.

## Bodies & voting notes
- **Form of government:** Millcreek is a five-member council (Mayor + 4 district
  councilmembers). **Unlike most cities in this collection, the Mayor VOTES on ordinary
  council motions** — a full council roll call therefore tops out at **5** (4 districts +
  mayor), not 4. Treat a 5-vote tally as complete.
- **CRA (Community Reinvestment Agency):** the Council convenes as the Millcreek Community
  Reinvestment Agency board (Utah 17C) — project-area plans/budgets, participation agreements,
  and inter-fund loans. Its open votes are tagged `body=CRA` (246 motions) in the council CSV
  and carry `stage=cra_vote`.
- **Roster drift (join carefully across years):** District 2 **Dwight Marchant → Thom DeSirant**
  (Jan 2022); **Cheri Jackson** moved from **District 3 → Mayor** (Nov 2025) and **Nicole Handy**
  took District 3 (Nov 2025). Mayor **Jeff Silvestrini** served through Nov 2025.
- **Elections use Ranked-Choice Voting (RCV) in 2021 & 2023.** This is an *election* property
  (recorded in `election_results/…` as `voting_method`), NOT a motion-vote property — it does
  **not** affect the `vote_value` crosswalk or any tally in this db. Noted here only so the
  election↔member join isn't misread.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **6,721 CSV named rows = 6,721 db vote rows**, **0 dropped, 0 documented overrides**. The build
  aborts (non-zero exit) if any row is dropped without a documented `db/overrides.csv` entry.
  Millcreek has no duplicate or unresolvable rows.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged. Of 254 Council applications, **28 link to
  another body; the rest are correctly UNLINKED** (no PC/CRA counterpart, or terse
  ordinance-keyed council text with no linkable subject).
- Corrections go through the override CSVs (`db/overrides.csv`, `db/referral_overrides.csv`) +
  rebuild — never in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC/CRA→Council link: both app keys, both project
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
