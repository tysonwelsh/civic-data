# Logan City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ Redevelopment Agency (RDA)** votes by real keys instead of fuzzy text
matching. Built reproducibly in **two stages**; the `db/tables/` CSVs are exports of each table
(for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Logan reality (why this is the prose-portal model, not Legistar's)
Logan's minutes are **PDF/prose** (the city publishes narrative minutes, ~40% of the Planning
Commission set as scanned **OCR**) — there is **no Legistar API, no structured agenda/matter key, and
no file/application number in the motion text**. So the project key is **resolved from prose** by a
tiered, auditable resolver — not read from a vendor field. Logan also gives **no shared key across
bodies** (verified: 0 shared addresses council↔non-council; `build_db.py` reports **0 applications
spanning >1 body**, by construction — see below). The cross-body relationship is therefore
**reconstructed** (`referral`), never looked up.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   A Council matter and a PC matter are **distinct** application rows — never merged. `application`
   therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA (Redevelopment Agency); `kind` ∈ council/agency/commission |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners + RDA board unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title (the text the referral layer tokenizes) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died`
- `motion.stage` ∈ `council_vote | rda_vote | pc_recommendation | pc_final_action` (the schema also
  allows `mba_vote | ha_vote | boa_action | other_action`; **stages present in Logan:** council_vote,
  rda_vote, pc_recommendation, pc_final_action)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused`

### Build totals (current)
**3 bodies · 24 persons · 306 meetings · 400 applications · 1,332 motions · 5,146 votes · 30 roles.**
Meetings by body: **Council 146 · PlanningCommission 129 · RDA 31.**
Motions by body: **Council 748 · PlanningCommission 549 · RDA 35.**
Applications by body: **PlanningCommission 314 · Council 51 · RDA 35.**
PC stages: **112 recommendations** (86 Positive / 26 Negative — forwarded to Council) + **437 final
actions** (design review / CUP / subdivision — never reach Council). Outcomes: Council 741 Pass / 4
Fail / 3 Died · PC 542 Pass / 7 Fail · RDA 35 Pass. Vote values: 4,891 Aye · 121 Nay · 7 Abstain ·
127 Absent. Contested (any Nay/Abstain/Recuse): **Council 28 · PC 62.** **6 people served on both the
Council and the RDA** (the RDA board *is* the City Council — unified by name in `person`/`role`); there
is **no Council↔PC person overlap** (commissioners are appointed, not elected). Coverage
**2020-01-07 → 2026-06-11.**

## Project resolution — TIERED + AUDITABLE (the within-body key)
Logan has no PL#/file number in the motion text, so each **land-use/policy** motion's `application_id`
is resolved in tiers; `app_match_method` + `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild.
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized name
   (e.g. *Spring View Estates Subdivision*, *Robinson Ranch Subdivision*, *West Airport Properties
   Annexation*). Heuristic — **treat name groupings as provisional** and correct via `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** becomes its
   **own** application: exact identity (one motion = one application, no cross-motion inference), `name` NULL.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial) get
   **no** application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 7 · `singleton` 393**; **NULL/non-land-use 932.**
All 7 `name`-tier applications are **Planning Commission** (where motion text carries the project
name); **all 51 Council land-use applications are `singleton`** — a direct consequence of Logan's
council minutes recording motions as bare action lines (*"adopt Ordinance 20-05 as presented"*) with
the project description living in the agenda title, which is not in the vote record. This is the key
fact behind the referral findings below.

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA), and PC←agency. Grain = application↔application; motions/votes inherit the link through
`v_referral_chain`.

### `referral` table columns
| column | notes |
|---|---|
| `referral_id` | PK |
| `primary_application_id` → `application` | the more-authoritative side |
| `primary_body` | denormalized body name of the primary |
| `related_application_id` → `application` | the lower-authority origin |
| `related_body` | denormalized body name of the related |
| `match_method` | ∈ `address \| subject \| address+subject \| override` |
| `confidence` | ∈ `high \| medium \| low` |
| `shared_address` | the matched grid pair / named-street address(es), `;`-joined |
| `subject_score` | IDF-weighted title agreement (0–1; name-anchored containment folded in) |
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`, or suppression rationale in the overrides CSV) |

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`2100 n 2300 w`) or named-street address.
  **Logan nuance:** these are *approximate grid intersections* ("located at approximately …"), i.e.
  whole street crossings, **not parcel addresses**. So address **+ title agreement** → `high`
  (≈exact), but an **intersection match alone** → `low` (co-location only; review). In Logan, only **1
  application carries a parseable address** and there are **0 shared addresses council↔non-council**, so
  the address signal is effectively inert here.
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) for address-less policy/code
  matters; *asymmetric name-anchored containment* (≥0.50) for a terse title covered by a richer one. IDF
  down-weights ubiquitous boilerplate so distinctive project **names** dominate. A *specific* shared code
  section reinforces.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack); for agency pairs it is **symmetric**
  (±400 days, since financing/project-area can precede or follow the land-use action).
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills a
  pair; audited, idempotent.

### Confidence
- **high** — full-grid address **+ title agreement** + temporal.
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal.
- **low** — grid-intersection co-location only, gate-uncertain, or a secondary origin — kept but **flagged**.

### Current build (Logan): 0 substantiated referrals — an honest data finding
**Logan's reconstructed referral layer is empty (0 links).** This is a deliberate, precision-first
outcome, not a build failure:
- The raw linker proposed **46 medium links, every one Council←RDA**, and **0 Council←PC** links.
- Eyeballing all 46 weakest-first showed **all 46 were boilerplate false positives**: each had the
  identical `subject_score` 0.388 and the *only* shared token was the generic word **"presented"**
  (council motions read *"adopt Ordinance NN-NN as presented"*; RDA motions read *"approve Resolution
  NN-NN RDA as presented"*). No shared project, address, or code section — pure boilerplate overlap.
- Because **48 of 51 Council applications carry only boilerplate tokens**, every such Council app
  matched *every* RDA resolution equally — a council×RDA false-positive cloud. The fix is at the
  source: the ubiquitous boilerplate word **"presented"** (plus "report"/"staff"/"findings") is now in
  the linker's STOP list, so these pairs share **no** scoreable token and **never form** — no overrides
  needed (`db/referral_overrides.csv` is empty).
- **No real cross-body link was suppressed:** PC→Council links never formed (Logan's council *and* many
  PC motion texts are bare procedural lines without project names — the one Council app with rich text,
  the Trapper Park / Phase 5 PDO, has a best PC subject score of only 0.043), and the address signal is
  inert (grid intersections, 0 council↔non-council shares).

The reconstruction stands on its own and is **honestly empty**: Logan's vote records do not carry
enough cross-body signal (no file number, bare council/RDA motion text, grid-intersection addresses) to
substantiate a single link without lowering thresholds (which would re-admit the boilerplate cloud) or
hand-authoring links from the underlying minutes. To add genuine links, populate
`db/referral_overrides.csv` with `link` rows after reading the relevant minutes, then rerun
`build_referrals.py`. Audit of the original proposals: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related (currently 0 rows for Logan).
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- A councilmember's full record (RDA board members appear under both Council and RDA):
SELECT full_name, body, votes, ayes, nays, abstain_recuse, first_vote, last_vote
FROM v_member_record WHERE full_name = 'Jeannie F. Simmonds';

-- Planning Commission recommendations the PC voted DOWN (negative rec forwarded to Council):
SELECT m.meeting_date, mo.outcome, mo.result_raw, mo.motion_text
FROM motion mo JOIN meeting m ON m.meeting_id = mo.meeting_id
WHERE mo.recommendation = 'Negative' ORDER BY m.meeting_date;

-- Walk a named PC project's timeline (recommendation vs. final action stages):
SELECT body, date, stage, outcome, recommendation, dissenters
FROM v_project_timeline WHERE project = 'Robinson Ranch Subdivision' ORDER BY date;
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings are
  heuristic (the prose resolver) — exact only at the `singleton`/`override` tiers; correct mis-merges
  in `overrides.csv` and rebuild (idempotent).
- **52 of the 130 Planning Commission minutes are scanned OCR**, so a fraction of PC motion/vote
  parsing is noisier than the digitally-published council set (mis-read names/tallies are possible).
- **Logan addresses are approximate grid intersections**, not parcels — so the address signal is
  co-location, not a 1:1 map; here it is effectively inert (only 1 app has a parseable address).
- The **`referral` layer is reconstructed inference** and is **honestly empty (0 links)**: Logan's
  council and RDA motion text is bare ("adopt Ordinance NN-NN as presented"), carrying no project
  identity, so no genuine cross-body link can be substantiated (the only candidates were boilerplate
  false positives, now eliminated at the source by stopwording — `referral_overrides.csv` is empty).
  This is a data-availability limit, not a modeling gap — add `link` rows after reading the minutes and rerun.
- `person` identity is **name-based** (normalized full name), not a verified registry; the 6
  Council↔RDA overlaps are by name match (the RDA board is the City Council). `role` is *observed* from
  votes, not an authoritative term roster.
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs).
</content>
</invoke>

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
