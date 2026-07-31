# Taylorsville City — `db/taylorsville.db` schema

Normalized relational database over Taylorsville's civic vote data (Salt Lake County, Utah).
It lets you join **Planning Commission ↔ City Council ↔ RDA** votes by real keys instead of
fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the collection's
`db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
   `build_db.py` therefore reports **0 applications spanning >1 body**.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data*
   (each body keys chiefly to itself), so it is reconstructed by record linkage in the separate
   `referral` table — every link is confidence-scored and overridable, and the genuine
   single-body majority is left **explicitly unlinked**.

Vendor: a **prose/PDF minutes portal** (no structured agenda/matter IDs). Built from the two
canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council + RDA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
`build_db.py` drops and recreates the whole DB, so **always re-run `build_referrals.py` after
it** (the `referral` table lives only in the second script). Every table is exported to
`db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists every referral with both titles,
score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 3 | Council, PlanningCommission, RDA |
| person | 18 | 7 councilmembers + 11 planning commissioners (Anna Barbieri sits on both) + movers/seconders; the non-voting mayor never appears as a voter |
| meeting | 235 | one row per (body, source minutes file) |
| application | 190 | body-scoped land-use/policy projects (Council 54 · PlanningCommission 132 · RDA 4) |
| motion | 937 | Council 605 · PlanningCommission 324 · RDA 8 |
| vote | 3,076 | named member-vote rows (see reconciliation) — Aye 2,863 · Nay 81 · Absent 94 · Abstain 35 · Recuse 3 |
| role | 24 | per person×body first/last vote + count (Council 7 · PlanningCommission 11 · RDA 6) |
| referral | 28 | reconstructed cross-body links (see below) |

Data span **2020-01-08 → 2026-06-03**. Contested motions (any Nay/Abstain/Recuse): **73**
(`v_contested`).

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Taylorsville uses Aye/Nay/Absent on
Council; Aye/Nay/Abstain/Recuse/Absent on the Planning Commission). `outcome` ∈
Pass/Fail/Continued/Died. `stage` ∈ council_vote/rda_vote/cra_vote/mba_vote/ha_vote/boa_action/
other_action/pc_recommendation/pc_final_action (Taylorsville uses council_vote/rda_vote/
pc_recommendation/pc_final_action). `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`,
`vote.person_id`, `motion.meeting_id`, `application.body_id`,
`referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions (and substantive agency motions) get an `application`; budgets,
appointments, contracts, and procedural motions correctly get **no application** (727 motions,
NULL). Resolution tiers, strongest first:

| method | conf | count | meaning |
|---|---|---|---|
| `override` | high | 0 | a `db/overrides.csv` row forces `app_key` (none needed) |
| `case_no` | high | **124** | a Utah planning **case number** `<SEQ><LETTER><YY>` cited in the motion text (exact) |
| `name` | medium | 7 | a named development/rezone/annexation grouped by normalized name (heuristic) |
| `singleton` | high | 79 | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| (NULL) | — | 727 | non-land-use motion → no application |

**The planning `case number` is Taylorsville's exact prose key — but only on the Planning
Commission side.** Taylorsville files land-use cases as `<SEQ><LETTER><YY>`: a 1–3 digit
sequence, a type letter, and a 2-digit year — `Z`=rezone / zone-text, `S`=subdivision,
`C`=conditional-use, `G`=general-plan, `P`=permitted-use (two-letter `SI`/`GP` variants also
occur), e.g. `15Z19`, `12S19`, `29C20`, `2SI24`. The PC cites these on most land-use motions
(as "File #15Z19"); all motions sharing a case number group into one application, and a cited
case number makes a motion application-worthy even when its native `motion_type` is
`Procedural`/`Other`. The embedded 2-digit year keeps it from colliding with Council's
`Ordinance/Resolution "YY-NN"` numbers.

## Cross-body `referral` layer — methodology & the key finding
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = the higher-authority side, Council > PlanningCommission > agency).
Signals: **case number** (exact) > **address** (shared full Utah grid pair / named-street
address) > **subject** (IDF-weighted title token agreement — symmetric Jaccard and asymmetric
name-anchored containment) > **code section** (specific shared subsection). **Temporal is a
gate, not a signal**: for a PC→Council pair the PC must precede the Council within ~400 days
(60-day forward slack); for RDA pairs (project-area/finance can precede or follow the land-use
action) it is symmetric. `db/referral_overrides.csv`
(`primary_application_id,related_application_id,action∈link/suppress,note`) forces or kills a
pair. Confidence: **high** = address+subject+temporal · **medium** = strong subject+temporal ·
**low** = address-/gate-only (flag; do not quote).

**Key structural finding — the case-number bridge does NOT cross bodies here.** Unlike Millcreek
(whose Council occasionally cites the PC case number verbatim), Taylorsville's Council/RDA
minutes are strictly ordinance/resolution-number-keyed and cite **0** planning case numbers
(104 non-council applications cite one; 0 council applications do; 0 shared). So — exactly like
South Jordan's one-sided `PL…` bridge — the strongest key cannot link PC→Council, and every
cross-body link falls to **address + subject + temporal**.

**Result — 28 links: 7 high, 15 medium, 6 low, all Council ← PlanningCommission**
(surfaced by `v_referral_chain`). The **high** links are address+subject rezone matches
(the Council ordinance approving a Zoning Map Amendment ↔ the PC's positive recommendation at
the same grid address, e.g. *5439 S 1300 W* Ord. 22-10, *1274 W Marinwood* Ord. 23-05,
*5418 S 1900 W* Ord. 26-01). The **medium** links carry the address-less policy referrals —
Zoning **Text Amendments** and **General Plan Amendments** where a rezone ordinance ↔ PC text/GP
recommendation share subject tokens within the temporal gate. The **low** links are
address-only co-locations at one site (e.g. three 2021 *3879 W 5400 S* / "West Point" ordinances
tied to a single PC approval — a genuine one-episode cluster kept per the spec).

**Tuning applied (precision over recall).** Every Taylorsville council/PC member + mayor +
mover/second surname and first name is added to the IDF `STOP` set in this city's
`build_referrals.py` so those names don't leak as subject tokens. One false
`Council ← RDA` candidate — a Council *"adjourn and convene the RDA / closed session"* motion
matching an RDA *"adjourn to the noticed closed session"* motion on procedural boilerplate
(2021-06-02) — is **suppressed via `db/referral_overrides.csv`** (29 → 28 links). This is the
spec's prescribed "dump-mediums-weakest-first, eyeball, tune" step; the audit CSV records the
final set.

## Bodies & voting notes
- **Form of government:** Taylorsville is a five-member council + a separately-elected mayor.
  **The Mayor does NOT vote** on council motions — a full council roll call therefore tops out
  at **5** (the presiding Chair rotates among the five councilmembers and is one of the five
  voters). Treat a 5-vote tally as complete; there is no sixth (mayoral) vote. Mayor **Kristie
  Overson** never appears in the `vote` table.
- **RDA (Redevelopment Agency):** the Council convenes as the Taylorsville Redevelopment Agency
  board (in-meeting recess). Its open votes are tagged `body=RDA` (8 motions) in the council CSV
  and carry `stage=rda_vote`.
- **Roster (join carefully across years):** current councilmembers **Ernest Burgess, Curt
  Cochran, Anna Barbieri, Meredith Harker, Bob Knudsen**; former members **Dan Armstrong** and
  **Brad Christopherson** appear in the earlier record. **Anna Barbieri** sits on **both** bodies
  in the data (Planning Commissioner early on, then Councilmember) — she is a single `person`
  with two `role` rows, so a person-level join spans both bodies by design.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **3,076 CSV named rows = 3,076 db vote rows**, **0 dropped, 0 documented overrides**. The build
  aborts (non-zero exit) if any row is dropped without a documented `db/overrides.csv` entry.
  Taylorsville has no duplicate or unresolvable rows.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high` ≈
  exact, `medium` strong-but-spot-check, `low` flagged. Of 54 Council applications, **27 link to
  the Planning Commission; the rest are correctly UNLINKED** (no PC counterpart, or terse
  ordinance-keyed council text with no linkable subject/address).
- Corrections go through the override CSVs (`db/overrides.csv`, `db/referral_overrides.csv`) +
  rebuild — never in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names,
  both dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a high-consensus council).
</content>

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
