# Herriman City — `db/civic.db` schema

Normalized relational database over Herriman's civic vote data (Salt Lake County, Utah). It
lets you join **Planning Commission ↔ City Council ↔ in-session agencies (CDRA / HCSEA /
HCFSA)** votes by real keys instead of fuzzy text. **Two layers, never conflated** (per
`SCHEMA_SPEC.md` and the collection's `db_schema_spec.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting, person, and
   (for land-use items) its project *application*, resolved **within each body**. A Council
   "Foo" and a PC "Foo" are DISTINCT applications; nothing is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship "the Council
   decided what the Planning Commission first recommended" is *absent from the source data*
   (each body keys only to itself), so it is reconstructed by record linkage in the separate
   `referral` table — every link is confidence-scored and overridable.

Vendor: **PrimeGov** prose/PDF minutes (no structured agenda/matter IDs), plus a 2020 legacy
S3 backfill. Built from the two canonical flat CSVs, which are never modified:
`meeting_minutes/all_votes.csv` (Council + CDRA + HCSEA + HCFSA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv` lists
every referral with both titles, score, and day-gap for review.

## Current contents (as built)
| table | rows | notes |
|---|---|---|
| body | 5 | Council, CDRA, HCSEA, HCFSA (kind=council), PlanningCommission (kind=commission) |
| person | 22 | mayor + councilmembers + commissioners + movers/seconders |
| meeting | 288 | one row per (body, source minutes file) **that carries ≥1 motion** |
| application | 529 | body-scoped land-use/policy projects |
| motion | 1,970 | Council 1,091 · PlanningCommission 850 · CDRA 16 · HCFSA 9 · HCSEA 4 |
| vote | 6,180 | named member-vote rows (see reconciliation) |
| role | 38 | per person×body first/last vote + count |
| referral | 39 | reconstructed cross-body links (17 high / 18 medium / 4 low) |

Contested motions (any Nay/Abstain/Recuse): **88** (`v_contested`). Herriman is a
high-consensus council; vote values are Aye 5,406 · Absent 627 · Nay 132 · Abstain 1 · Excused 14.

**⚠ The MAYOR is a voting `person`.** Unlike Taylorsville/South Jordan (where the mayor is
excluded), Herriman's Mayor votes on ordinary motions — Mayors **David Watts** and **Lorin
Palmer** are in the `person` table with real `role` rows on the Council (167 and 478 votes).
A full Council roll = **5** (D1–D4 + Mayor). Lorin Palmer also has a **PlanningCommission**
role (2020–2021, pre-mayoralty) — one `person`, two `role` rows.

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent/Excused (Herriman uses Aye/Nay/Absent/
Excused; `Yes`/`No` in the source normalize to Aye/Nay). `outcome` ∈ Pass/Fail/Continued/
Died. `stage` ∈ council_vote (1,120 — all Council + agency bodies) / pc_final_action (529) /
pc_recommendation (321). `PRAGMA foreign_keys=ON`; indexed on `motion.application_id`,
`vote.person_id`, `motion.meeting_id`, `application.body_id`, `referral.{primary,related}_
application_id`.

## `body` — Council + three in-session agencies
Herriman's council recesses in-session to convene three district agencies, captured in the
same council minutes and tagged by `body` (all `kind=council`):
- **CDRA** — Community Development & Renewal Agency (16 motions)
- **HCSEA** — Herriman City Safety Enforcement Area (4 motions)
- **HCFSA** — Herriman City Fire Service Area (9 motions)
The same officials appear as "Trustee/Board Member". There are **no separate agency portal
files**; the in-meeting captures are the complete published record (not an acquisition gap).

## Within-body application resolution (`app_match_method` / `app_confidence`)
Only land-use / policy motions get an `application`; budgets, appointments, contracts, and
procedural motions correctly get **no application** (1,405 motions, NULL).

| method | conf | count | meaning |
|---|---|---|---|
| `singleton` | high | **399** | an unnamed land-use/policy motion → its own application (exact identity, name unknown) |
| `name` | medium | 166 | a named development/rezone/annexation grouped by normalized name (heuristic) |
| (NULL) | — | 1,405 | non-land-use motion → no application |

Herriman's PrimeGov minutes carry no structured planning file-number key in the vote prose
(unlike South Jordan's `PL…`), so there is no exact prose bridge — land-use grouping falls to
singleton identity + normalized name, and cross-body linkage to subject/address/temporal.

## Cross-body `referral` layer — methodology
Reconstructed in `build_referrals.py` (grain: application↔application between two different
bodies; `primary_body` = the higher-authority side, Council > PlanningCommission > agency).
Signals: **address** (shared full Utah grid pair / named-street address) > **subject**
(IDF-weighted title token agreement — symmetric Jaccard + asymmetric name-anchored
containment) > **code/instrument number** (specific shared ordinance/resolution number).
**Temporal is a gate, not a signal**: for a PC→Council pair the PC must precede the Council
within ~400 days. `db/referral_overrides.csv` (`primary_application_id,related_application_id,
action∈link/suppress,note`) forces or kills a pair. Confidence: **high** = address+subject+
temporal (or a shared instrument number) · **medium** = strong subject+temporal · **low** =
address-/gate-only (flag; do not quote).

**Result — 39 links, all Council ← PlanningCommission: 17 high · 18 medium · 4 low.** The
classic land-use referral (PC recommends a rezone/plat, Council adopts it) is surfaced by
`v_referral_chain`. Respect the confidence column: `high` ≈ exact, `medium` strong-but-spot-
check, `low` do-not-quote.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row lands in
  `vote`: **6,180 CSV named rows = 6,180 db vote rows, 0 dropped**. (Council-file 3,216 =
  Council 3,156 + CDRA 20 + HCFSA 30 + HCSEA 10; PC 2,964.) The build aborts on any undocumented
  drop. CDRA's 16 motions are 12 tally-only + 4 named rolls → 20 vote rows.
- **Meeting count (288) < minutes docs (312)**: 24 special/closed-session/adjournment-only
  docs carry no motion and correctly produce no `meeting` row. Not a defect.
- **The within-body core is exact; the `referral` layer is reconstructed inference** — `high`
  ≈ exact, `medium` spot-check, `low` flagged.
- **Tally-only majorities are honestly unnamed.** Short procedural motions print `all voted
  aye` (one placeholder CSV row, member blank → no `vote` rows); substantive motions carry a
  full named Mayor+member roll. A blank member on a procedural motion is a source style, not
  an extraction miss.
- **2020 `Lorin Powell` source typo** (4 PC rows) is retained verbatim in the source and maps
  to a `person` row as printed — it conflates Andy Powell + Lorin Palmer; never guess-merged.
- Corrections go through the override CSVs (`db/referral_overrides.csv`) + rebuild — never
  in-place edits to the flat CSVs or the .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC→Council link: both app keys, both project names,
  both dates, method, confidence, shared address, subject score.
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
