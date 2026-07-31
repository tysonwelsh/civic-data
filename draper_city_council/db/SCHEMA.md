# Draper City — `db/civic.db` schema

Normalized relational database over Draper's civic vote data (Draper straddles Salt Lake +
Utah counties, Utah). It lets you join **Planning Commission ↔ City Council** votes by real
keys instead of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md` and the
collection's `db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and (for
   land-use items) its project *application*, resolved **within each body**. A Council "Foo" and a
   PC "Foo" are DISTINCT applications; nothing is merged across bodies here. `build_db.py` reports
   **0 applications spanning >1 body**.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council decided
   what the Planning Commission first recommended" is *absent from the source data* (each body keys
   only to itself), so it is reconstructed by record linkage in the separate `referral` table — every
   link is confidence-scored and overridable, and the genuine single-body majority is left
   **explicitly unlinked**.

Vendor: **Granicus MinutesViewer** — a prose/PDF minutes portal (no structured agenda/matter IDs).
Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council) and `planning_commission/all_votes.csv` (PlanningCommission).

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
| body | 2 | Council, PlanningCommission |
| person | 28 | councilmembers + commissioners + movers/seconders + **Mayor Troy K. Walker** (tie-break only) |
| meeting | 294 | one row per (body, source minutes file) — 151 Council + 143 PC |
| application | 632 | body-scoped land-use/policy projects — 95 Council + 537 PC |
| motion | 1,793 | Council 882 · PlanningCommission 911 (679 final actions + 232 recommendations) |
| vote | 7,801 | named member-vote rows (see reconciliation) |
| role | 24 | per person×body first/last vote + count |
| referral | 5 | reconstructed cross-body links (all `medium`; see below) |

`vote_value` distribution: **Aye 6,685 · Absent 770 · Recuse 180 · Nay 90 · Abstain 76**.
Contested motions (any Nay/Abstain/Recuse): **229** (`v_contested`) — **15 Council + 214 PC**. Draper
Council is high-consensus; the **Planning Commission is where the real contest is** (heavy land-use
docket).

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent (Draper uses all five; the PC "Not-Participating"
grid maps to `Recuse`). `outcome` ∈ Pass/Fail/Died (Pass 1,786 · Fail 4 · Died 3). `stage` ∈
`council_vote` (882) / `pc_final_action` (679) / `pc_recommendation` (232). `provenance` ∈
`minutes` (1,769 — audited Granicus docs) / `pmn_minutes` (24 — the 6 meetings PMN-recovered and
promoted 2026-07-16: council 2021-07-20 + 3 Truth-in-Taxation specials, PC 2020-12-10 +
2024-10-10). `PRAGMA
foreign_keys=ON`; indexed on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, `referral.{primary,related}_application_id`.

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, ceremonial and
procedural motions correctly get **no application** (1,132 motions, NULL). Resolution tiers:

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | **560** | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | **101** | a named development/rezone/subdivision grouped by normalized name (heuristic) |
| (NULL) | — | 1,132 | non-land-use motion → no application |

**Note on PC case numbers.** The Planning Commission cites land-use case numbers `YYYY-NNNN-TYPE`
(`USE`/`SUB`/`MA`/`VAR`/`SP`; **184 distinct** in the motion text) — a potentially exact within-body
key. This build resolves applications by `singleton`/`name` rather than by the case number; a
case-number tier is a natural future upgrade (it would tighten PC application grouping and could seed
an exact cross-body bridge if a Council motion ever cited one).

## Cross-body `referral` layer — methodology & the key finding
Reconstructed in `build_referrals.py` (grain: application↔application between the two bodies;
`primary_body` = the higher-authority side, Council > PlanningCommission). Signals: **address** (shared
full grid pair / named-street address) > **subject** (IDF-weighted title token agreement) > **code
section**. **Temporal is a gate, not a signal**: for a PC→Council pair the PC must precede the Council
within ~400 days. `db/referral_overrides.csv` (`primary_application_id,related_application_id,
action∈link/suppress,note`) forces or kills a pair. Confidence: **high** ≈ exact / address+subject+
temporal · **medium** = strong subject+temporal · **low** = gate-only (flag; don't quote).

**Result — 5 links, all `medium`, all Council ← PlanningCommission** (`match_method = subject`). The
Council's minutes are terse and **ordinance/resolution-number-keyed** and cite **0** PC case numbers,
so the strongest key can't bridge PC→Council in the flat data; cross-body links fall to subject +
temporal (address where present). This is a genuine data characteristic reported on every build, not a
bug. Respect the confidence column — spot-check each `medium` before quoting; there are **no `high`
links**, so treat every cross-body claim as reconstructed inference, not source fact. Of 93 Council
applications, **5 link to the PC; the rest are correctly UNLINKED** (no PC counterpart, or the terse
ordinance-keyed council text carries no linkable subject).

## Bodies & voting notes
- **Form of government:** **5 AT-LARGE councilmembers + a separately-elected NON-voting Mayor** —
  **no districts**. All normal council tallies top out at **5**.
- **Mayoral tie-break (2024-10-15):** the one time the Mayor voted. **Mayor Troy K. Walker** cast a
  tie-breaking `Aye` on motion 3 (Ordinance #1625, `3-2 Pass`) when the five members split 2-2 with
  one recusal. It is his single `vote` row and his only `role` entry, stored as an ordinary `Aye` (no
  special note field, unlike Park City).
- **No RDA/MBA in the db.** Draper's Council + PC are the only bodies here (unlike South Jordan's
  4-body model). A CRA recess appears inside some council minutes but is tagged `body=Council`.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in `vote`:
  **7,801 named CSV rows == 7,801 db vote rows** (3,719 Council + 4,082 PC), **0 dropped, 0 documented
  overrides**. The build aborts if any row is dropped without a documented override.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — all 5 links are
  `medium`, none `high`; spot-check before quoting.
- **Narrative/tally-only motions.** Some 2020–2021 council motions and many procedural motions record
  only mover/seconder + a printed tally, leaving members unnamed (`names_recorded=0`); a blank member
  list is a source style, never an extraction miss, and unnamed Ayes are never inferred.
- **One known extraction miss (not a db defect):** the 2025-08-26 Board of Canvassers meeting
  (Resolution #25-42) has a named grid the extractor skipped — 1 ceremonial motion, no legislative
  impact, logged in `TODO.md` / `VERIFICATION.md` §7. It is upstream of the db (absent from the flat
  CSV), so the db reconciliation is still exact against the CSV.
- Corrections go through override CSVs (`db/referral_overrides.csv`) + rebuild — never in-place edits
  to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names, both
  dates, method, confidence, shared address, subject score.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse, first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (229: 15 Council + 214 PC).

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
