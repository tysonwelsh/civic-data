# Ogden City civic database — schema & data dictionary

`db/civic.db` (SQLite) is the **canonical, queryable** form of this repo's vote data — a normalized
relational model (PKs, FKs, typed/constrained columns, provenance) that lets you join **City Council
↔ Planning Commission ↔ Redevelopment Agency (RDA) ↔ Municipal Building Authority (MBA)** votes by
real keys instead of fuzzy text matching. Built reproducibly in **two stages**; the `db/tables/` CSVs
are exports of each table (for diffing/portability).

```
python3 db/build_db.py          # 1. the EXACT within-body core
python3 db/build_referrals.py   # 2. the reconstructed, scored cross-body referral layer (run AFTER)
```

## The Ogden reality (why this is the prose-portal model, not Legistar's)
Ogden publishes **PDF/prose minutes** (text PDFs; many OCR'd) — there is **no Legistar API, no
structured agenda/matter key**, and the petition/ordinance number is only *sometimes* restated in the
motion text that gets recorded into a roll-call. So the project key is **resolved from prose** by a
tiered, auditable resolver — not read from a vendor field. Ogden also shares **no key across bodies**;
`build_db.py` reports **0 applications spanning >1 body**, by construction (see below). The cross-body
relationship is therefore **reconstructed** (`referral`), never looked up.

**The dominant Ogden characteristic (mitigated 2026-07-02, plan item 3.5):** Council vote motions
are **terse and ordinance-number-based** ("ORDINANCE WAS PASSED AND ADOPTED AS OGDEN CITY ORDINANCE
2022-46 … UPON THE FOLLOWING ROLL CALL VOTE") — the substantive subject historically lived only in
the staff report / agenda. The extractor now appends the item's **verbatim** printed long-title /
agenda heading (`[ENTITLED: "…"]` / `[AGENDA ITEM: "…"]`, 500 motions; see
meeting_minutes/CLAUDE.md), so **117** Council motions resolve a land-use application (was 20), vs
**131** at the Planning Commission. Referrals grew 1 → 4 accordingly (all hand-verified).

## Two layers, never conflated
1. **Within-body core (`build_db.py`) — EXACT.** Every vote ties to body/meeting/person, and every
   land-use/policy motion gets an `application_id` resolved **within its own body** (body-scoped). A
   Council "171 Franklin" and a PC "171 Franklin" are **distinct** application rows — never merged.
   `application` therefore spans exactly one body, always.
2. **Cross-body referral (`build_referrals.py`) — RECONSTRUCTED + SCORED + OVERRIDABLE.** The only
   probabilistic part; kept in a separate table so it can never contaminate the exact core.

## Core tables (exact — from `build_db.py`)
| table | grain | key | notes |
|---|---|---|---|
| `body` | one governing body | `body_id` PK; `name` UNIQUE | Council / PlanningCommission / RDA / MBA; `kind` ∈ council/commission/agency |
| `person` | one official | `person_id` PK; `name_key` UNIQUE | councilmembers + commissioners unified by normalized full name |
| `meeting` | one meeting | `meeting_id` PK; `(body_id, source_file)` UNIQUE | FK→body; carries `source_file` provenance (the markdown path) |
| `application` | one project/matter **within one body** | `application_id` PK; `app_key` UNIQUE; `body_id` FK | `app_key` is body-scoped: `<body>\|<normname>` (named) or `<body>\|s\|<src>\|<mno>` (singleton). `name`=clean project name (NULL for singletons); `rep_title`=representative full motion title (rich tokens for the referral layer) |
| `motion` | one motion (agenda action) | `motion_id` PK | FK→meeting, body, application, person(mover/seconder); `outcome`/`stage`/`recommendation` constrained; `app_match_method`+`app_confidence` record how the project was resolved; `names_recorded` ∈ 0/1 |
| `vote` | one member-vote | `vote_id` PK; `(motion_id, person_id)` UNIQUE | FK→motion, person; `vote_value` normalized |
| `role` | person×body service | `(person_id, body_id)` UNIQUE | DERIVED observed span (first/last vote, n_votes) |

`PRAGMA foreign_keys=ON`; indexes on `motion.application_id`, `vote.person_id`, `motion.meeting_id`,
`application.body_id`, and (referral layer) `referral.primary_application_id`,
`referral.related_application_id`.

### Enumerations (CHECK-constrained)
- `motion.outcome` ∈ `Pass | Fail | Continued | Died` — **present in Ogden:** Pass 1,907 · Fail 16
  (the 1,882 previously printed here was stale — the pre-enrichment db already held 1,907).
- `motion.stage` ∈ `council_vote | rda_vote | mba_vote | pc_recommendation | pc_final_action`
  (the schema also allows `ha_vote | boa_action | other_action`; none occur in Ogden). The PC stage
  is assigned by a keyword test (`recommend`/`forward` ⇒ `pc_recommendation`), so it differs slightly
  from the PC extractor's subject-matter taxonomy in `planning_commission/CLAUDE.md` — see limitations.
- `motion.recommendation` ∈ `Positive | Negative | NULL` (Planning Commission only — direction of the rec).
- `motion.app_match_method` ∈ `name | singleton | override | NULL`; `app_confidence` ∈ `high | medium | low | NULL`.
- `vote.vote_value` ∈ `Aye | Nay | Abstain | Recuse | Absent | Excused`.

### Build totals (current — queried; rebuilt 2026-07-02 after the 2022 minutes re-carve/re-OCR and the 3.5 subject enrichment)
**4 bodies · 28 persons · 316 meetings · 340 applications · 1,923 motions · 5,758 votes · 48 roles · 4 referrals.** (2026-07-02 subject enrichment: applications 259 → 340 — Council 19→117 as adoption motions' subjects became visible, while RDA 93→80 / MBA 16→12 because agency budget/procedural resolutions, previously subject-less and counted as substantive, are now correctly excluded by the AGENCY_PROCEDURAL filter; referrals 1 → 4.)
Coverage **2020-01-07 → 2026-05-20**.

| body | kind | meetings | motions | votes | applications | contested* |
|---|---|---|---|---|---|---|
| Council | council | 213 | 1,377 | 3,812 | 117 | 78 |
| PlanningCommission | commission | 65 | 417 | 1,660 | 131 | 54 |
| RDA | agency | 32 | 111 | 258 | 80 | 7 |
| MBA | agency | 6 | 18 | 28 | 12 | 0 |

\* contested = motions drawing ≥1 Nay/Abstain/Recuse. **Stages:** council_vote 1,377 · pc_recommendation
163 · pc_final_action 254 · rda_vote 111 · mba_vote 18. **PC recommendation direction:** Positive 161 ·
Negative 2. **Vote values:** Aye 5,404 · Nay 238 · Absent 108 · Recuse 6 · Abstain 2. **Persons:** 28
distinct — **13 serve on more than one body**, but these are the **councilmembers who also sit as the
RDA / MBA boards** (7 Council+RDA, 5 Council+MBA+RDA, 1 Council+MBA+PC+RDA); **exactly 1 person served
on both the Council and the Planning Commission**; the other 15 persons are PC-only commissioners
(16 distinct commissioners total).

## Project resolution — TIERED + AUDITABLE (the within-body key)
Ogden's recorded motion text rarely carries a usable file number, so each **land-use/policy** motion's
`application_id` is resolved in tiers; `app_match_method` + `app_confidence` are stored on every motion
(priority high→low):
1. **`override`** (high) — a row in `db/overrides.csv` (`source_file,motion_no,app_key`) forces the
   assignment. (Currently empty — the within-body resolver stands on its own.)
2. **`name`** (medium) — a genuine **named development/annexation/rezone** grouped by normalized name.
   Heuristic; treat name groupings as provisional and correct via `overrides.csv`. **(18 motions)** —
   small here because even enriched motions seldom restate a project *name* (long titles describe
   the action, not a marketing name).
3. **`singleton`** (high) — a land-use/policy motion with **no extractable project name** (generic
   acreage rezones/GPAs, code/text amendments, unnamed street vacations) becomes its **own**
   application: exact identity (one motion = one application). **(326 motions / 326 applications;
   grew from 252 when the 2026-07-02 subject enrichment made adoption motions' subjects visible.)**
4. **(NULL)** — non-land-use motions (budget, appointments, contracts, procedural, ceremonial, and the
   remaining subject-less roll-calls) get **no** application — correctly outside the land-use
   universe and outside referrals. **(1,579 motions.)**

## `referral` — the reconstructed, GENERALIZED cross-body linkage (the design point)
A **referral** links two applications **in two different bodies** for the same real-world matter,
naming a `primary_body` (the more authoritative side: **Council > Planning Commission > agency
(RDA/MBA)**) and a `related_body`. The model is **generalized** — it covers Council←PlanningCommission,
Council←agency (RDA/MBA), and PC←agency. Grain = application↔application; motions/votes inherit the
link through `v_referral_chain`.

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
| `note` | override rationale (when `match_method='override'`) |

`UNIQUE(primary_application_id, related_application_id)`.

### Signals (recorded per link in `match_method` + `confidence`)
- **address** — both cite the SAME full Utah **grid pair** or named-street address. **Ogden nuance:**
  these are *approximate grid intersections / named-street crossings* ("located generally at …"), i.e.
  whole crossings, **not parcel addresses**. So address **+ title agreement** → `high`; an
  **intersection match alone** (negligible subject overlap) → `low` (co-location only; review).
- **subject** — IDF-weighted title agreement: *symmetric* IDF Jaccard (≥0.30) carries address-less
  policy/code referrals; *asymmetric name-anchored containment* (≥0.50) catches a terse title covered
  by a richer one. IDF down-weights ubiquitous boilerplate; a *specific* shared code section reinforces.
- **temporal** — a **gate**, not a stored signal. PC→Council is **directional** (PC must precede
  Council within ~400 days, 60-day forward slack); agency pairs are **symmetric** (±400 days, since
  financing/project-area can precede or follow the land-use action).
- **override** — `db/referral_overrides.csv` (`primary_application_id,related_application_id,action,
  note`; action ∈ link/suppress) forces or kills a pair; audited, idempotent.

### Confidence
- **high** — full-grid address + title agreement + temporal, **or** a vetted `override` link.
- **medium** — strong IDF subject (symmetric or name-anchored) + temporal.
- **low** — grid-intersection co-location only, gate-uncertain, or a secondary origin — kept but **flagged**.

### Current build (Ogden) — honest and tuned for precision
**4 referral links: 1 `high` + 3 `medium`** — the **171 Franklin Street vacation/rezone (2022)**
Council←PC `override` (PC rec 2022-02-02 → Council action 2022-08-09), plus 3 subject-matched
links enabled by the 2026-07-02 enrichment, all hand-verified: **Adams Community Reinvestment
Project Area** tax-increment interlocal (Council←RDA twin resolutions, 2025-05-13), the **2023
Housing Element / moderate-income housing** General Plan amendment (Council 2023-02-07 ← PC rec
2022-12-07), and the **Ogden Bend master plan** (PC←RDA, 2024). **3 of 117 (2%)** Council
land-use applications are linked; the rest are correctly **UNLINKED**. 4 false-positive pairs
are suppressed in `referral_overrides.csv` (surname-token class: the matcher counted shared
mover/seconder surnames as subject signal — a known build_referrals weakness; a principled fix
is to strip roster surnames from subject tokens and stop treating agency adjourn motions as
applications). (Before the 2026-07-02 2022 minutes re-carve there was also a `low` Council←RDA
address co-location link; it sat on 2022 motions the re-carve proved were mis-tagged Council
motions, so it correctly disappeared.)

**Why so few (this is honest, not a bug):** Ogden's recorded Council motions are terse ordinance-
adoption roll-calls that omit the subject (only 19 carry resolvable land-use prose), so they share
almost no distinctive address/subject tokens with the descriptive PC/RDA motions — there is simply
little to link on. The reconstruction is therefore tuned for **precision over recall**.

**Tuning performed (`db/referral_overrides.csv`):** the medium tier is dumped weakest-first into
`db/referrals_audit.csv` and eyeballed. The only medium candidates have been **procedural-boilerplate
false positives** — instrument adoptions matching purely on the shared "ON A MOTION BY … was
ADOPTED / ordered posted as required by law upon the following roll call vote" phrasing (different
instruments, no shared subject) — all **suppressed** (currently 1: Council ord 2025-22 vs RDA Res
2024-8; the original four Council-2022-46-vs-RDA pairs vanished when the 2026-07-02 re-carve removed
the mis-tagged 2022 RDA motions). The one obvious **miss** — the PC's 171 Franklin recommendation,
which the template missed because the matching Council motion is a terse agenda-ordering line — is
force-added as a `link`. No template thresholds were lowered. Audit: `db/referrals_audit.csv`;
overrides: `db/referral_overrides.csv` (1 suppress + 1 link). **NB overrides pin `application_id`s,
which shift if the underlying vote CSVs change — re-bind them after any re-extraction (done
2026-07-02).**

### Resolution (prevents false fan-out)
Per primary item the best origin in each related body wins; secondaries are kept only when
address+subject is high or a strong subject score sits within 80% of the best.

## Views (start here)
- **`v_referral_chain`** — every cross-body link, surfaced primary↔related: both `app_key`s, both
  project names, both dates, `match_method`, `confidence`, `shared_address`, `subject_score`, `gap_days`.
- **`v_project_timeline`** — within-body project history (`app_key → body/date/stage/outcome/recommendation/dissenters`).
- **`v_member_record`** — per person×body vote tallies. · **`v_contested`** — motions with any Nay/Abstain/Recuse.

```sql
-- 1. The reconstructed cross-body chain (PC recommendation -> Council action):
SELECT confidence, match_method, primary_body, related_body,
       related_date, primary_date, gap_days, shared_address, subject_score
FROM v_referral_chain ORDER BY confidence DESC, primary_date;

-- 2. Planning Commission recommendation activity (direction of every land-use rec forwarded to Council):
SELECT recommendation, outcome, COUNT(*) AS n
FROM motion m JOIN body b USING(body_id)
WHERE b.name='PlanningCommission' AND stage='pc_recommendation'
GROUP BY recommendation, outcome ORDER BY n DESC;

-- 3. "Follow the money": every RDA land-use/finance motion and its named dissenters:
SELECT m.meeting_date, mo.outcome, substr(mo.motion_text,1,80) AS motion,
       (SELECT group_concat(p.full_name,'; ') FROM vote v JOIN person p USING(person_id)
          WHERE v.motion_id=mo.motion_id AND v.vote_value IN ('Nay','Abstain','Recuse')) AS dissenters
FROM motion mo JOIN body b USING(body_id) JOIN meeting m USING(meeting_id)
WHERE b.name='RDA' ORDER BY m.meeting_date;
```

## Known limitations (honest)
- **The within-body core is exact**; `name`-tier groupings (18) are heuristic — exact only at the
  `singleton`/`override` tiers. Correct any mis-merge in `overrides.csv` and rebuild (idempotent).
- **Council land-use was undercounted by the source's phrasing until 2026-07-02.** Ogden's recorded
  Council roll-calls are terse ordinance-adoption motions that omit the subject; the extractor now
  appends each item's verbatim printed long-title/heading, so 117 Council applications resolve
  (was ~20) and referrals stand at 4. Motions whose printed text truly carries no subject anywhere
  in the minutes remain honestly app-less.
- **PC minutes coverage / fidelity.** Of 72 PC minutes, **49 are OCR'd** (2024–2026 uppercase
  roll-calls; stray-space names normalized by the PC parser). **2020–2023 PC coverage is sparse** —
  Ogden did **not** maintain a standalone Planning-Commission minutes archive those years; minutes were
  embedded in the next meeting packet, so fewer PC meetings (65 in the DB) are recoverable for the early
  span than the per-year cadence would imply.
- **2022–2023 RDA/MBA undercounted (0 motions those years)** — the separate 2022 and 2023 RDA/MBA
  meeting sets were not acquired (2023: DocCenter 29548/29549; a 2022 set is referenced in the council
  minutes but was likewise never harvested; ~20–25 RDA + ~5–8 MBA meetings missing per year). So the
  RDA/MBA motion counts (111/18) cover 2021 in-meeting transitions + 2024–26 only.
- **Addresses are approximate grid intersections / street crossings**, not parcels — address co-location
  can cluster distinct matters at one crossing (kept, confidence-flagged, not a 1:1 map).
- **The `referral` layer is reconstructed inference**, not a looked-up key — partial and probabilistic.
  `high` (address+subject, or vetted override) ≈ exact; `low` is flagged. Correct mistakes in
  `referral_overrides.csv` and rerun.
- **The DB `stage` for PC motions is keyword-derived** (`recommend`/`forward` ⇒ `pc_recommendation`),
  so its 163/254 recommendation/final split differs from the PC extractor's subject-matter taxonomy
  (`planning_commission/CLAUDE.md`, which also carves out a `procedural` class). Use the PC extractor's
  classification for taxonomy questions; the DB stage for cross-body joins.
- **`person` identity is name-based** (normalized full name), not a verified registry; the 13 multi-body
  persons are councilmembers wearing RDA/MBA/PC hats (the 7-member board sits as RDA & MBA). `role` is
  *observed* from votes, not an authoritative term roster.
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
