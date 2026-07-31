# Park City civic database — schema & data dictionary

`db/parkcity.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **Planning
Commission ↔ City Council ↔ RDA ↔ Housing Authority (HA)** votes by real keys instead of fuzzy text
matching. Built reproducibly in **two stages**; the `db/tables/` CSVs are exports of each table
(for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

> **Note — retrofitted model.** Park City's DB was originally built on an older *alias-merge* model
> (one `application` could span several bodies via a propagated `PL-####`, and a heuristic
> `project_timeline.csv` was the crosswalk). It has been **retrofitted to the unified body-scoped +
> referral model** shared across these city repos: applications are now **body-scoped** (a Council and
> a PC "Founder's Place" are distinct rows) and the cross-body tie lives **only** in the separate,
> scored `referral` table / `v_referral_chain`. The old `pl_number`/`alias` tiers and the
> `project_timeline.csv` crosswalk are superseded.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped).
   `build_db.py` reports **0 applications spanning >1 body**, by construction.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core. CivicClerk
   PDF-prose gives **no shared key across bodies**, so the real relationships ("the Council decided what
   the PC recommended"; "the Housing Authority adopted a mitigation plan for the development the
   Council approved") are **reconstructed** by record linkage, never looked up.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA / HA; `kind` ∈ council/commission/agency |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title (rich tokens for the referral layer) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized; `note` (nullable) preserves annotations — `'Mayor tie-break'` for the 2 mayoral tie-break votes (flat CSV value `"Nay (Mayor tie-break)"` is split into value+note), or `'override: …'` when a contradictory source pair was resolved via `db/vote_overrides.csv` |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died`
- `motion.stage` ∈ `council_vote | rda_vote | ha_vote | pc_recommendation | pc_final_action` (schema
  also allows `mba_vote | boa_action | other_action`; **stages present in Park City:** council_vote,
  rda_vote, ha_vote, pc_recommendation, pc_final_action)
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec)
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused` (+ nullable free-text `vote.note`)

### Vote-row integrity — `db/vote_overrides.csv` (2026-07-02)
The flat `all_votes.csv` is **verbatim/city-faithful**, so it carries (a) annotated values like
`"Nay (Mayor tie-break)"` and (b) **9 genuine clerk errors** where the source minutes list a member in
BOTH the AYES and the NAYS/ABSTAIN list of one motion (worst: 2022-10-06 motion 8, "5-2 Pass" on a
5-member council with Dickey and Toly in both lists; plus 7 partial abstentions of the form
"AYES: all five … ABSTAIN: Member X from the <date> minutes"). The old build silently dropped 11 such
rows on the `(motion_id, person_id)` UNIQUE constraint — including **both mayoral tie-breaks**. Now:
- Parenthetical annotations are split into a schema-legal `vote_value` + `note`
  (`"Nay (Mayor tie-break)"` → `Nay` + `'Mayor tie-break'`). Both tie-breaks (Beerman 2020-06-25,
  Worel 2024-08-22) are in the db.
- Contradictory `(motion, person)` pairs **must** have a row in **`db/vote_overrides.csv`**
  (`source_file,motion_no,member,date,claimed_values,resolution,reasoning`; `resolution` = a legal
  vote value, or `exclude` for unresolvable rows). Each resolution documents its reasoning (partial
  abstentions → `Abstain`; the 2022-10-06 full-roster-AYES template error → `Nay` per the deliberate
  NAYS line, true tally 3-2).
- Any conflict **not** covered by an override **fails the build loudly** (exit 1, every conflict
  printed); rows are never silently dropped. The build prints a reconciliation line
  (`named CSV rows = inserted + merged + excluded + unresolvable-person`) and fails on drift.

### Build totals (current — rebuilt 2026-07-02)
**4 bodies · 24 persons · 363 meetings · 676 applications · 2,159 motions · 7,980 votes · 46 roles.**
Motions by body: **Council 1,493 · PlanningCommission 602 · RDA 46 · HA 18.** Applications by body:
PlanningCommission 391 · Council 256 · RDA 16 · HA 13. PC stages: **156 recommendations** (153 Positive
/ 3 Negative) + **446 final actions** (CUP/design-review/steep-slope — never reach Council). Contested
(any Nay/Abstain/Recuse): Council 96 · PC 30 · RDA 1 · HA 1. **12 people served on more than one body**
(commissioners later elected — unified by name in `person`/`role`). Coverage 2020-01-08 → 2026-05-21.
(2026-07-02 rebuild: 10 spurious prose-artifact motions removed at extraction; 11 formerly-dropped
vote rows restored — see the vote-integrity section above. The 46th role is Beerman×Council, created
by his recovered 2020-06-25 tie-break vote.)

## Project resolution — TIERED + AUDITABLE (the within-body key)
CivicClerk exposes **no** structured agenda-item key, and the `PL-####` number appears in only ~2% of
motions, so each **land-use/policy** motion's `application_id` is resolved in tiers; `app_match_method`
+ `app_confidence` are stored on every motion (priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. Hand-edit to fix any mis-merge/split, then rebuild. (Currently empty.)
2. **`name`** (medium) — a genuine **named development/annexation/MPD/rezone** grouped by normalized
   name. The workhorse-but-heuristic tier; **treat name groupings as provisional** and correct via
   `overrides.csv`.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   rezones/GPAs, **code/text amendments**, unnamed actions) becomes its **own** application: exact
   identity (one motion = one application), `name` NULL. Kept granular so each links to its specific
   prior PC recommendation in the referral layer. Substantive (non-procedural) **agency** motions
   (RDA/HA) also get a singleton/named application, so an RDA loan or HA mitigation plan can be linked
   to the Council/PC action on the same site.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial; for
   agency bodies also meeting-date/canvass/consent) get **no** application — outside the land-use universe.

Current mix (motions with an application): **`singleton` 523 · `name` 232**; **NULL/non-land-use 1,404.**
(Park City minutes lean on terse ordinance-style titles, so the singleton tier dominates.)

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized**: it covers Council←PlanningCommission **and**
Council←RDA/HA **and** PC←HA. Grain = application↔application; motions/votes inherit the link through
`v_referral_chain`.

### `referral` table columns
| column | notes |
|---|---|
| `referral_id` | PK |
| `primary_application_id` → `application` | the more-authoritative side |
| `primary_body` | denormalized body name of the primary |
| `related_application_id` → `application` | the lower-authority origin/companion action |
| `related_body` | denormalized body name of the related |
| `match_method` | ∈ `address \| subject \| address+subject \| override` |
| `confidence` | ∈ `high \| medium \| low` |
| `shared_address` | the matched grid pair / named-street address(es), `;`-joined |
| `subject_score` | IDF-weighted title agreement (0–1; name-anchored containment folded in) |
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)` — each cross-body pair is emitted once, primary = the more authoritative side.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** or named-street address. (Park City titles
  carry fewer numeric grid pairs than valley cities; many links rest on subject.)
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) carries the address-less
  policy/code-amendment referrals; *asymmetric name-anchored containment* (≥0.50) catches a terse title
  wholly covered by a richer one. IDF down-weights ubiquitous "development/code/amendment" boilerplate
  so distinctive project **names** dominate. A *specific* shared code section reinforces.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council, ~400-day window, 60-day forward slack); for **agency** pairs it is
  **symmetric** (±400 days, since RDA/HA financing/mitigation can precede *or* follow the land-use
  action). A candidate failing the gate is rejected.
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills
  a pair; audited, idempotent.

### Confidence
- **high** — full-grid address **+ subject** + temporal (or an override).
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal.
- **low** — address co-location only, gate-uncertain, or a secondary origin — kept but **flagged**.

### Current build (Park City, rebuilt 2026-07-02)
**256 Council land-use/policy applications · 100 referral links** (**47 high · 30 medium · 23 low**). By
method: **address+subject 43 · subject 31 · address 22 · override 4.** By body-pair:
**Council ← PlanningCommission 95**, **Council ← HA 3** (high), **Council ← RDA 1** (high),
**PlanningCommission ← HA 1** (low). **84 of 256 (32%)** Council items
linked to ≥1 other body; the rest are correctly **UNLINKED**. Audit: `db/referrals_audit.csv`.

### Agency cross-body links are signal-limited → carried by overrides (honest)
The RDA/HA cross-body links are **signal-limited**: agency titles are boilerplate ("…affordable
housing mitigation plan…", "…restrictive covenant…") while the matching Council action is a terse
ordinance title ("Ordinance 2022-03…"), so the IDF subject signal rarely clears the bar and there are
few shared grid pairs. The reconstruction therefore finds only a thin agency layer on its own. The
**marquee development links are carried explicitly by `db/referral_overrides.csv`** (4 forced links,
all `match_method='override'`, confidence `high`):

| primary (Council) | related (agency) | development |
|---|---|---|
| 113 | 111 (HA) | **Founder's Place** — HA affordable-housing mitigation plan (the PC-5-0 → Council-fail case) |
| 143 | 120 (RDA) | **Sommet Blanc** — RDA affordable-housing mitigation (Empire Pass Pod B2 MPD) |
| 207 | 159 (HA) | **Studio Crossing** — HA housing mitigation plan (MPD, 3981 Kearns Blvd) |
| 70 | 151 (HA) | **Argent** (7677 Royal St) — HA restrictive-covenant affordability modifications |

> **Caveat — `referral_overrides.csv` is keyed by `application_id`**, which is assigned in build
> order and can shift when upstream motions change (the 2026-07-02 re-extraction shifted Studio
> Crossing from 209/160 to 207/159; the file was updated to match, verified by `app_key`). After any
> rebuild that changes motion counts, re-verify the override ids against `application.app_key`.

In total **5 referrals involve an agency body** (the 4 overrides above + 1 reconstructed `PC←HA` at
low confidence). These overrides are the honest way to assert relationships the prose signals can't
carry; edit `referral_overrides.csv` and rebuild to add/remove.

## Views (start here)
- **`v_referral_chain`** — every cross-body link: both `app_key`s, both project names, both dates,
  `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`. **Supersedes the old
  `project_timeline.csv` crosswalk.**
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

## Example queries
```sql
-- Trace the cross-body chain (PC recommendation / agency action -> Council decision):
SELECT confidence, match_method, primary_body, related_body,
       related_date, related_project, primary_date, primary_project, shared_address
FROM v_referral_chain ORDER BY confidence DESC, primary_date;

-- Founder's Place across every body (the marquee PC-yes / Council-fail / HA-mitigation case):
SELECT b.name AS body, m.meeting_date, p.full_name, v.vote_value
FROM application a JOIN motion mo ON mo.application_id=a.application_id
  JOIN meeting m ON m.meeting_id=mo.meeting_id JOIN body b ON b.body_id=mo.body_id
  JOIN vote v ON v.motion_id=mo.motion_id JOIN person p ON p.person_id=v.person_id
WHERE a.app_key LIKE '%founder%' ORDER BY m.meeting_date;

-- A commissioner's full record across bodies:
SELECT * FROM v_member_record WHERE full_name='Jeremy Rubell';
```

## Known limitations (honest)
- The **within-body core** is exact. `name`-tier groupings are heuristic (the prose resolver) — exact
  only at `singleton`/`override`; correct mis-merges in `overrides.csv` and rebuild (idempotent).
- The **`referral` layer is reconstructed inference**, not a looked-up key. `high` (address+subject /
  override) ≈ exact; `medium` (subject) is strong but **spot-check before quoting**; `low` is flagged.
- **Agency (RDA/HA) links are signal-limited** — boilerplate agency titles vs terse ordinance titles —
  so the headline development links are asserted via `db/referral_overrides.csv`, not discovered. The
  reconstructed agency layer is intentionally thin.
- This DB was **retrofitted** from the older alias-merge model; the legacy `pl_number`/`alias` tiers and
  `planning_commission/project_timeline.csv` are superseded by the body-scoped core + `v_referral_chain`.
- `person` identity is **name-based**, not a verified registry; the 12 multi-body overlaps are by name.
  `role` is *observed* from votes, not an authoritative term roster.
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
