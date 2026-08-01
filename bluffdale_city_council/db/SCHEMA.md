# Bluffdale City — `db/civic.db` schema

Normalized relational database over Bluffdale's civic vote data (Salt Lake
County, Utah — with an unpopulated Utah-County / Camp Williams slice). It lets you
join **Planning Commission ↔ City Council ↔ in-session RDA / LBA** votes by real
keys instead of fuzzy text. **Two layers, never conflated** (per `SCHEMA_SPEC.md`):

1. **Within-body core — EXACT.** Every motion/vote ties to its body, meeting,
   person, and (for land-use items) its project *application*, resolved **within
   each body**. A Council "Foo" and a PC "Foo" are DISTINCT applications; nothing
   is merged across bodies here.
2. **Cross-body linkage — RECONSTRUCTED + SCORED.** The real-world relationship
   "the Council decided what the Planning Commission first recommended" is
   *absent from the source data* (each body keys only to itself), so it is
   reconstructed by record linkage in the separate `referral` table — every link
   is confidence-scored and overridable.

Vendor: **CivicPlus/CivicEngage AgendaCenter** — a prose/PDF minutes portal (no
structured agenda/matter IDs). Built from the two canonical flat CSVs, which are
never modified: `meeting_minutes/all_votes.csv` (Council + RDA + LBA) and
`planning_commission/all_votes.csv` (PlanningCommission).

Rebuild (idempotent — drop+recreate; same inputs → same DB):
```
python3 db/build_db.py          # within-body exact core
python3 db/build_referrals.py   # cross-body referral layer (run AFTER build_db.py)
```
Every table is exported to `db/tables/*.csv` for diffing. `db/referrals_audit.csv`
lists every referral with both titles, score, and day-gap for review.
**⚠ Do not run `build_db.py` casually during analysis — it drops + rebuilds the
`referral` table.** Read the .db, don't rebuild it, unless you mean to.

## Current contents (as built, 2026-07-12)
| table | rows | notes |
|---|---|---|
| body | 4 | Council, PlanningCommission, RDA (agency), LBA (agency) |
| person | 56 | councilmembers + commissioners + movers/seconders |
| meeting | 295 | one row per (body, source minutes file) |
| application | 530 | body-scoped land-use/policy projects |
| motion | 1,279 | Council 872 · PlanningCommission 308 · RDA 77 · LBA 22 |
| vote | 3,793 | named member-vote rows (see reconciliation) |
| role | 41 | per person×body first/last vote + count |
| referral | 62 | reconstructed cross-body links (18 high / 41 med / 3 low) — **precision-audited + tuned 2026-07-31**, down from an untuned 269; see `db/CLAUDE.md` |

Contested motions (any Nay/Abstain/Recuse): **99** (`v_contested`). Bluffdale is a
high-consensus, mixed named/narrative-tally council; many majorities pass with
only the mover/seconder + any dissenters named.

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
Enums: `vote_value` ∈ Aye/Nay/Abstain/Recuse/Absent. `outcome` ∈
Pass/Fail/Continued/Died. `stage` ∈ `council_vote` (872) / `pc_final_action` (182)
/ `pc_recommendation` (126) / `rda_vote` (77) / `mba_vote` (22). `PRAGMA
foreign_keys=ON`.

## Bodies & voting notes
- **Form of government:** Mayor + **5 at-large** council members (no districts).
  The **Mayor does NOT vote** on ordinary Council motions — normal Council tallies
  top out at **5**.
- **2 mayoral tie-breaks / recorded Council votes** — the only times the Mayor
  votes in the pure `Council` body: **2022-11-09** motion 4 (Mayor Hall breaks a
  2-2 tie → 3-2) and **2025-05-14** motion 4 (Mayor Hall → 4-2). Both are faithful
  minutes records, stored as ordinary `vote` rows (no special note field).
- **RDA / LBA convene in-session** inside council meetings (adjourn → agency board
  → reconvene). Their open votes are tagged `body=RDA` (77 motions) / `body=LBA`
  (22 motions) in the council CSV, and in these boards **the Mayor votes as
  Chair** — a named RDA/LBA roll caps at **6** and legitimately includes the Mayor.
- **⚠ Stage sub-label cross-tag:** the LBA (Local Building Authority) motions carry
  `stage='mba_vote'` (the schema's Municipal-Building-Authority stage bucket,
  reused for the LBA). The **`body` split (Council / RDA / LBA) is correct**; only
  the `stage` string reuses the MBA label. Filter LBA by `body_id`, not by stage.

## Honesty requirements
- **Vote reconciliation is exact and fail-loud.** Every named member-vote row
  lands in `vote`: **3,793 CSV named rows = 3,793 db vote rows** (2,538 council +
  1,255 PC), **0 dropped, 0 overrides**. The tally-only placeholder rows (blank
  member) in the flat CSVs correctly do NOT become `vote` rows.
- **`provenance` is `minutes` for all 1,279 motions** — this is a core build with
  **no PMN-recovered rows** (nothing to filter; no `pmn_*` provenance exists).
- **The within-body core is exact; the `referral` layer is reconstructed
  inference** — `high` ≈ exact, `medium` strong-but-spot-check, `low` flagged/do
  not quote. **The layer was ground-truthed link-by-link on 2026-07-31 and tuned
  via `db/referral_overrides.csv` (365 evidence-cited `suppress` rows): 269 links
  → 62, and every surviving link was verified against the source minutes.** The
  pre-audit set was 9.5% precise in the `high` tier (171 of 189 links were
  meeting-notice boilerplate joined on CITY HALL's own address). Read
  `db/CLAUDE.md` before quoting or re-tuning this layer.
- **Narrative-tally motions** name only the mover + any dissenters, leaving the
  majority unnamed; the extractor never infers unnamed Ayes. Corrections go
  through override CSVs + rebuild — never in-place edits to the flat CSVs or .db.

## Views to ship
- `v_referral_chain` — every reconstructed PC/agency→Council link: both app keys,
  both project names, both dates, method, confidence.
- `v_project_timeline` — within-body project history (app_key → body/date/stage/
  outcome/dissenters).
- `v_member_record` — per person×body vote tallies (ayes/nays/abstain-recuse,
  first/last vote).
- `v_contested` — motions with any Nay/Abstain/Recuse (the signal on a
  high-consensus council; 99 motions).

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
