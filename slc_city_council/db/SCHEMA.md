# Salt Lake City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **City Council ↔
Planning Commission ↔ Redevelopment Agency (RDA) ↔ Community Reinvestment Agency (CRA) ↔ Local Building
Authority (LBA)** votes by real keys instead of fuzzy text matching. Built reproducibly in **two
stages**; the `db/tables/` CSVs are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The SLC reality (why this is the prose-portal model, not Legistar's)
SLC's minutes are **PrimeGov / Laserfiche prose** (markdown) — there is **no Legistar API and no
structured agenda/matter key in the vote rows**, so the project key is **resolved from prose** by a
tiered, auditable resolver, not read from a vendor field. SLC also gives **no shared key across
bodies**, so the cross-body relationship is **reconstructed** (`referral`), never looked up.

### Two SLC-specific shapes the generic template is adapted to (in `db/build_db.py` only — the shared
### skill template in `~/.claude/skills/` is left pristine; both adaptations are read-time, no file is modified)
1. **Four bodies interleaved in one council vote stream.** Salt Lake City's Council, when it meets,
   adjourns/reconvenes *in the same session* as the **LBA, RDA, and CRA**. The
   **body per motion was recovered by walking the source markdown minutes**: each meeting's ALL-CAPS bold
   section headers (`LBA OPENING CEREMONY`, `REDEVELOPMENT AGENCY …`, `SALT LAKE CITY COUNCIL MEETING`,
   `…reconvene as the City Council`) delimit the body sections, and the *i*-th `Final Result` line maps
   to the *i*-th motion (294/302 files match exactly; the rest fall back to last-seen/title body).
2. **A rich land-use `motion_type` taxonomy.** SLC's PC tags every motion (`Planned Development`,
   `Conditional Use`, `Zoning Map Amendment`, `Zoning Text Amendment`, `Design Review`, `Master Plan
   Amendment`, `Subdivision/Plat`, `Street/Alley Closure`, `Special Exception`); Council/agencies phrase
   zoning as "Zoning Map Amendment", "Master Plan Amendment", etc. The build recognizes this taxonomy so
   the land-use universe (and the referral layer) isn't starved, and it guards pure-procedural motions
   (adjourn/reconvene transitions, closed-session, minutes approval) from ever becoming applications.

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped). A
   Council "Rio Grande" and a PC "Rio Grande" are **distinct** application rows — never merged.
   `build_db.py` reports **0 applications spanning >1 body**, by construction.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / Redevelopment Agency / Community Reinvestment Agency / Local Building Authority; `kind` ∈ council/commission/agency |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting (one body × one source file) | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path). One combined-session minutes file yields several `meeting` rows (one per body that voted in it) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title (rich tokens for the referral layer) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` (**present in SLC:** Pass 2,557 · Fail 25 —
  SLC result strings record disposition, not continuances). `outcome` reflects whether the
  **motion carried**, derived from the yes:no/yes-no tally (`outcome_of`, 2026-07-12) — a passed
  denial is `Pass`, a failed recommendation is `Fail`; the build FAILS on any tally↔outcome
  contradiction.
- `motion.stage` ∈ `council_vote | rda_vote | mba_vote | ha_vote | boa_action | other_action |
  pc_recommendation | pc_final_action` (**present in SLC:** council_vote 1,510 · pc_final_action 426 ·
  pc_recommendation 314 · rda_vote 293 (RDA 213 + CRA 80) · mba_vote 39 (the LBA — "Local Building
  Authority" maps to `mba_vote` via the template's building-authority rule))
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec).
  **Legacy/known-inconsistent:** keyword-derived from `result_raw`/`motion_text` *without* reliably
  composing with carriage, so it mislabels ~13 failed/tied PC recs (the same bug class fixed in
  `outcome_of`). Prefer `disposition`+`outcome` below; `recommendation` reconciliation is queued (TODO).
- `motion.disposition` ∈ `approve | deny | continue | table | procedural | NULL` (2026-07-12) — what the
  motion **PROPOSES** for the matter, a **separate axis from `outcome`** (did it carry). Deliberately NOT
  pre-composed: compose at query time — `disposition='approve' AND outcome='Pass'` ⇒ matter approved;
  `'approve' AND 'Fail'` ⇒ not approved; `'deny' AND 'Pass'` ⇒ denied. Read from verbatim `motion_text`;
  `disposition_method` ∈ `keyword | mixed | override | uncaptured | unclassified`, `disposition_confidence`
  ∈ `high | medium | low`. Corrections go in `db/disposition_overrides.csv`
  (`source_file,motion_no,disposition,note`). **Present in SLC:** approve 1,235 · procedural 1,004 ·
  continue 197 · NULL 73 · deny 51 · table 22. For PC recommendation motions the build cross-checks
  `compose(disposition,outcome)` against the legacy `recommendation` field (277/290 agree; the 13
  disagreements are legacy-field errors, not disposition errors).
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused`

### Build totals (current — queried)
**5 bodies · 70 persons · 494 meetings · 893 applications · 2,582 motions · 18,157 votes · 77 roles.**
Motions by body: **Council 1,510 · PlanningCommission 740 · Redevelopment Agency 213 · Community
Reinvestment Agency 80 · Local Building Authority 39.** Applications by body: **PlanningCommission 501 ·
Council 275 · Redevelopment Agency 76 · Community Reinvestment Agency 37 · Local Building Authority 4.**
PC stages: **314 recommendations** (269 Positive / 45 Negative) + **426 final actions** (CUP / design
review / planned development — never reach Council). Contested (any Nay/Abstain/Recuse): **PC 274 ·
Council 70 · RDA 7 · CRA 4.** **1 person** served on both the Council and the PC (unified by name in
`person`/`role`). Coverage **2020-01-08 → 2026-06-10** (PC from 2020; council/agency votes 2021+).

## Project resolution — TIERED + AUDITABLE (the within-body key)
SLC vote rows carry no usable file/petition number, so each **land-use/policy** motion's
`application_id` is resolved in tiers; `app_match_method` + `app_confidence` are stored on every motion:
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces it.
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized name.
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (the common
   case in SLC, where titles are address-keyed: *"Rezone at approximately 536 South 200 West"*) becomes
   its **own** application: exact identity (one motion = one application), `name` NULL.
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, ceremonial, procedural) get **no**
   application — correctly outside the land-use universe and outside referrals.

Current mix (motions with an application): **`name` 30 · `singleton` 872**; **NULL/non-land-use 1,680.**
SLC titles are overwhelmingly address-keyed rather than named, so **singletons dominate** — and a single
real matter often appears as **several** council singletons (a "close public hearing / defer" motion and
a later "adopt Ordinance N" motion are separate singleton applications). This is why the council linked %
below is lower than a named-development city's: the referral layer ties the PC origin to the best-matching
council application, not to every motion of the episode.

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter, naming
a `primary_body` (the more authoritative side: **Council > Planning Commission > agency**) and a
`related_body`. The model is **generalized** — it covers Council←PlanningCommission, Council←agency
(RDA/CRA/LBA), and PC←agency. Grain = application↔application; motions/votes inherit the link through
`v_referral_chain`.

### `referral` table columns
| column | notes |
|---|---|
| `referral_id` | PK |
| `primary_application_id` → `application` | the more-authoritative side (Council, here) |
| `primary_body` | denormalized body name of the primary |
| `related_application_id` → `application` | the lower-authority origin (PC / agency) |
| `related_body` | denormalized body name of the related |
| `match_method` | ∈ `address \| subject \| address+subject \| override` |
| `confidence` | ∈ `high \| medium \| low` |
| `shared_address` | the matched grid pair / named-street address(es), `;`-joined |
| `subject_score` | IDF-weighted title agreement (0–1; name-anchored containment folded in) |
| `primary_date`, `related_date`, `gap_days` | the decision date, the origin date, and their gap |
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** (`536 s 200 w`) or named-street address.
  **SLC nuance:** these are *approximate grid intersections* ("at approximately …"), i.e. whole street
  crossings, **not parcel addresses** — so address **+ title agreement** → `high` (≈exact), but an
  **intersection match alone** (negligible subject overlap) → `low` (co-location only; review).
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) carries the address-less
  **policy/code-amendment** referrals; *asymmetric name-anchored containment* (≥0.50) catches a terse
  council title wholly covered by a richer PC title. IDF down-weights ubiquitous "amendment / zoning /
  ordinance" boilerplate. A *specific* shared code section reinforces.
- **temporal** — a **gate**, not a stored signal. For a PC→Council pair it is **directional** (the PC
  must precede the Council within ~400 days, 60-day forward slack); for agency pairs it is **symmetric**
  (±400 days, since financing/project-area can precede or follow the land-use action).
- **override** — `db/referral_overrides.csv`
  (`primary_application_id,related_application_id,action,note`; action ∈ link/suppress) forces or kills a
  pair; audited, idempotent.

### Confidence
- **high** — full-grid address **+ title agreement** + temporal (clean rezones / map amendments).
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal (named items + text amendments).
- **low** — grid-intersection co-location only, gate-uncertain, or a secondary origin — kept but **flagged**.

### Current build (SLC)
**275 Council land-use/policy applications · 501 PC applications · 117 agency applications · 31 referral
links** (**11 high · 15 medium · 5 low**). By body-pair: **Council ← PlanningCommission 28 · Council ←
Community Reinvestment Agency 2 · Council ← Redevelopment Agency 1.** By method: **address+subject 11 ·
subject 15 · address 5.** **31 of 275 (11%)** Council items linked; the rest are correctly **UNLINKED**
(council-initiated code cleanups, episodes whose PC recommendation predates the data floor, the many
duplicate council singletons of an already-linked matter, and address-less items). The 3 agency links
are the **HTRZ / Sugar House Streetcar interlocal agreements** the Council adopts that the RDA/CRA also
acted on. `high` `gap_days` span 78–356 (mean ≈159), all directionally PC-before-Council. **6 false
positives were reviewed weakest-first and suppressed** in `db/referral_overrides.csv` (two cross-project
HTRZ / consent-agenda agency matches; an ADU text-amendment vs a single ADU conditional-use; a
Subdivision-Code vs Zoning-amendment pair; a Design-Review-Standards vs a single design-review approval).
Audit: `db/referrals_audit.csv`.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- 1. Trace land-use matters PC -> Council (technical recommendation vs political decision), best first:
SELECT confidence, match_method, related_date AS pc_date, related_project,
       primary_date AS council_date, primary_project, shared_address, subject_score
FROM v_referral_chain
WHERE related_body = 'PlanningCommission'
ORDER BY confidence DESC, subject_score DESC;

-- 2. Where the PC recommended DENIAL but the Council still acted on the same matter:
SELECT pri.rep_title AS council_item, p.meeting_date AS pc_date, c.meeting_date AS council_date
FROM referral r
JOIN motion pm ON pm.application_id = r.related_application_id AND pm.recommendation = 'Negative'
JOIN meeting p ON p.meeting_id = pm.meeting_id
JOIN application pri ON pri.application_id = r.primary_application_id
JOIN motion cm ON cm.application_id = pri.application_id
JOIN meeting c ON c.meeting_id = cm.meeting_id
WHERE r.related_body = 'PlanningCommission';

-- 3. Motions split across the four interleaved council-session bodies (how many of each, by year):
SELECT strftime('%Y', m.meeting_date) AS yr, b.name AS body, COUNT(*) AS motions
FROM motion mo JOIN meeting m ON m.meeting_id = mo.meeting_id JOIN body b ON b.body_id = mo.body_id
WHERE b.kind = 'agency'
GROUP BY yr, body ORDER BY yr, body;
```

## Known limitations (honest)
- The **within-body core** (`application`/`motion`/`vote`) is exact. `name`-tier groupings are heuristic;
  exact only at the `singleton`/`override` tiers. SLC is **singleton-dominated** (address-keyed titles),
  so one real matter can appear as several council singleton applications — correct mis-splits in
  `db/overrides.csv` and rebuild (idempotent).
- **Body recovery for the council stream is reconstructed**, not a clerk-recorded field: body was
  derived by walking the **markdown** section headers /
  `Final Result` order (see top). Since the 2026-07-02 retrofit that derivation is materialized as the
  council CSV's `body` column (short codes Council/RDA/CRA/LBA; the build maps them back to full body
  names and keeps the walk as fallback). 294/302 files align exactly; 8 (mostly pure-agency) fall back to
  last-seen/title and may misattribute a stray procedural motion. The land-use Council↔PC payoff is
  unaffected (those items sit squarely in clearly-marked council sections).
- The **`referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  `high` (address+subject) ≈ exact; `medium` (subject) is strong but **spot-check before quoting**; `low`
  is flagged. Correct mistakes in `db/referral_overrides.csv` and rerun.
- SLC addresses are **approximate grid intersections**, so address co-location can cluster several
  distinct matters at one crossing — real relatedness, kept (and confidence-flagged), not a 1:1 map.
- **Extraction provenance differs by body** (be aware when judging precision): the **PC** vote extractor
  is **pure-regex** (`planning_commission/extract_votes.py`, deterministic) over minutes sourced from a
  **mix of slcdocs and Laserfiche**; the **council** votes were **LLM-batch-extracted** in the prior
  build. The DB consumes both CSVs as given (`all_votes.csv` is immutable input).
- `person` identity is **name-based** (normalized full name), not a verified registry; the single
  Council↔PC overlap is by name match. `role` is *observed* from votes, not an authoritative term roster.
- This DB covers **votes**; it does not model public comments or elections (those remain in their CSVs).
</content>


## Vote-conflict overrides — `db/vote_overrides.csv` (2026-07-02, plan item 3.1)

The flat `all_votes.csv` files are city-faithful/verbatim: where the source minutes list
a member under BOTH the AYES and NAYS/ABSTAIN/ABSENT labels (clerk duplication in the
source), the CSV carries two contradictory rows for one (motion, person). `build_db.py`
previously collapsed these via `INSERT OR IGNORE` (keeping whichever row came first —
arbitrary). It now requires a documented resolution in **`db/vote_overrides.csv`**
(`source_file,motion_no,member,date,claimed_values,resolution,reasoning`; resolution is
a legal vote value or `exclude`) and FAILS THE BUILD on any conflict not covered — rows
are never silently dropped. Identical duplicate rows still merge silently. Every build
prints the reconciliation (named CSV rows = inserted + merged + excluded + unresolvable).
The flat CSV keeps both verbatim rows; only the db's single-vote grain uses the
resolution. (Pattern shared with `park_city_city_council/db/`.)

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
