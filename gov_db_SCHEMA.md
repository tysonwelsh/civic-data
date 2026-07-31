# gov.db — the federated 4-tier database

**The queryable form of the whole repository**: every built entity's standard tables
unioned with `city` + `gov_level` + `state` columns, plus the normalization, search,
roster, elections, campaign-finance, regional-project, and projection layers, and a
`caveat` table the analysis views join so measurement ceilings surface at query time.

Renamed from `cities.db` on 2026-07-20 (a `cities.db` symlink remains; the builder is
still `python3 scripts/build_cities_db.py`). **DERIVED — regenerated, never hand-edited.**
Counts below are from the build of **2026-07-31T17:00:54** and are reprinted by every
build; re-verify any number against the live db (`build_info` table) or with
`python3 scripts/check_doc_numbers.py`. Query read-only:
`sqlite3 "file:gov.db?mode=ro"`.

## What's in it / what's not

IN: 41 built entities' vote spine (**motion 78,548** — city 49,105 / county 27,262 /
regional 973 / state 1,208; **vote 247,455** member-vote rows — city 180,979 / county
38,589 / regional 0 (tally-only by source) / state 27,887), the normalization layer
(**motion_std 77,340**), elections (**election_race 680** audited races +
**election_result 5,482** SLCo SOVC tallies), campaign finance (**cf_contribution
19,685** / cf_expenditure 15,750 / cf_filing 1,889 / **cf_cycle 805** — the only
sanctioned per-candidate totals), comments (**14,202**), ordinances (**7,550**, 5,480
motion-linked), the document catalog (**54,702**), rosters (**term 641**), regional
projects (**regional_project 5,717** + project_vintage 3,453 + project_history 1,884),
projections (**10,952**), development pipeline (869), GIS catalog (173), and the FTS5
search layer.

NOT in it: raw source binaries (local-only; re-fetch via `document.source_url` — 99.98%
populated), sandy's `legistar_*` extension tables (query `sandy_city_council/db/sandy.db`),
and the per-entity flat CSVs, which remain the canonical on-disk sources.

⚠ **`document.path` resolves only in a full local build** (34% of rows point into the
gitignored `raw/` tree). In a cloned repo use `text_path` (99.96% resolvable) to read and
`source_url` to re-fetch.

## ID namespacing

Every entity's integer ids are offset by a per-entity `fed_index` band at federation
(`registry/entities.csv`), so FKs stay valid repo-wide and `(city, *_id)` is unique.
**Never hand-write a `motion_id`** — ids renumber on re-extraction; derive links
(the cache_county lesson, 2026-07-29).

## Tables (row counts as of 2026-07-31)

**Vote spine** (all carry `city, gov_level, state`):

| table | rows | key columns |
|---|---:|---|
| `entity` | 44 | slug, name, level, dir, db_rel_path, fed_index, portal, gov_form |
| `entity_relationship` | 81 | entity_a, relation, entity_b (the geography graph) |
| `body` | 154 | name, kind (council / PlanningCommission / RDA / …) |
| `person` | 1,664 | full_name, name_key — ⚠ state legislators are a DISJOINT population |
| `meeting` | 12,574 | body_id, meeting_date, title, source_file |
| `motion` | 78,548 | motion_text, motion_type + result_raw (VERBATIM), outcome, stage, recommendation, disposition (+method/confidence), application_id, mover/seconder, names_recorded, source_file, provenance |
| `vote` | 247,455 | motion_id, person_id, vote_value (verbatim vocabulary — see `vote_values`), note |
| `application` | 20,533 | app_key, name, rep_title — ⚠ includes ut_state's 264 bills (app_key `bill:…`) pending the state-tier reintegration; filter `gov_level` |
| `referral` | 1,836 | reconstructed PC→Council links, confidence-scored; `low` = don't quote |
| `role` | 2,195 | person × body service spans derived from votes |

**Normalization**: `motion_std` 77,340 (city rows read from each city's
`motions_std.csv`; county/regional rows COMPUTED AT FEDERATION with the same classifier —
their 100% join rate is definitional, and `dataset` there is body-derived:
`land_use` = planning commission(s), `legislative` = everything else). Plus
`motion_type_crosswalk` 411 / `body_crosswalk` 43 / `vote_values` 83. ut_state has NO
motion_std rows BY DESIGN (see its `motion-std-deferred` caveat).

**Elections**: `election_race` 680 (25-col audited winners/margins — authoritative;
RCV cities: take winners here, not from tallies) · `election_result` 5,482 (SLCo SOVC
candidate×contest tallies 2007–2025; `rank_in_contest` is plurality order).

**Campaign finance**: `cf_filing` 1,889 → `cf_contribution` 19,685 / `cf_expenditure`
15,750 → `cf_cycle` 805 (the ONLY sanctioned per-candidate totals — filings overlap) ·
`cf_candidate_person` 659 (212 person-matched). Structured rows carry donor
city/state only — never street addresses. Coverage: 29 of 31 cities (see the
`cf-coverage` caveat; slc portal-blocked, draper unstructured).

**Documents & text**: `document` 54,686 (doc_type × dataset catalog with
has_text/text_path) · `ordinance` 7,550 (`motion_resolution='unique'` rows carry a
quotable enacting-motion link; 321 ambiguous — never forced) · `comment` 14,202
(published comment layers are email/phone-redacted per PRIVACY.md).

**Rosters**: `term` 641 (seat-tenure intervals, half-open `[start,end)`, per-row
confidence/sources, VACANT gaps) · `district_version` 205 · `district_precinct` 1,490.
Point-in-time roster: `start_date<=:d AND (end_date='' OR end_date>:d)`.

**Regional/data-forward layers** (the MPO analytic surface — NOT votes):
`regional_project` 5,717 (wfrc 8 TIP vintages + RTP-2050 = 5,146; mag TIP/RTP/RPO 571) ·
`project_vintage` 3,453 + `project_history` 1,884 (lifecycle across vintages, keyed on
UDOT ePM `pin`; 4 caveat rows guard the semantics) · `projection` 10,952 (county 980 /
regional city-area annual 2019–2050 9,832 / state 140) · `development_application` 869 ·
`gis_layer` 173 (with per-layer license).

**Apparatus**: `caveat` 91 (see below) · `build_info` 100 (built_at, per-layer counts,
join rates — the numeric source of truth).

## Search layer (FTS5)

`fts_minutes` 14,696 docs (40 entities — incl. 823 recovered-PMN texts and 523 ut_state
rows: 305 advisory opinions + 218 LUDMA statute sections) · `fts_motion` · `fts_comment` ·
`fts_ordinance` 7,550 · `fts_packet` 13,725. Query with `MATCH`, filter the stored
`city`/`date` columns, pull passages with `snippet()`.

⚠ **Path columns are ENTITY-relative, with a tier-dependent prefix.** To open a result's
file from the repo root:

```sql
SELECT CASE WHEN gov_level='city' THEN city || '_city_council/' ELSE city || '/' END || path
-- (fts_minutes carries no gov_level column: derive via JOIN entity e ON e.slug = city,
--  using e.level='city'; document.text_path follows the same convention)
```

Indexing rules (G5, 2026-07-31): recovered `pmn_minutes` texts ARE indexed (823), except
112 skipped as same-(city,date,body) duplicates of already-indexed promoted minutes;
statutes use a 40-char floor (short sections are real law) while other docs keep the
200-char stub guard; the only remaining unindexed ut_state items are the 2 image-only
advisory opinions (#142/#145 — no text exists).

## The `caveat` table (91 rows) — what it protects against

`(city, dataset, code, caveat)`; `'*'` = applies across that axis. Every measurement
ceiling — tally-only and dissent-only recording, vote-vocabulary limits, coverage floors,
classification ceilings, disposition/cf coverage, the disjoint state-person population —
carried IN the db so the views can attach it to result rows. All 41 built entities carry
at least one row (back-filled 2026-07-31). `v_coverage` prints the full text per entity.

## Views — caveat-aware by construction

- **`v_contested_all`** — every non-unanimous motion: contested = a *named*
  Nay/Abstain/Recuse row OR a printed tally showing nay/other. Two count families:
  `tally_*` (authoritative margins — use these) vs `named_*` (attribution only;
  UNDERCOUNT in dissent-only/tally-only cities). `tally_other` is NULL (never 0) when no
  third number was printed — the COALESCE against named rows keeps abstain/recuse counts
  honest (ground-truthed across 9 cities). `dissent_caveats` carries the applicable
  caveat codes on every row.
- **`v_member_record_all`** — per (city, member, body): counts by vote value,
  `nay_pct_of_aye_nay`, and `record_caveats` (a `dissent-only` city's 100%-nay
  commissioner is flagged on the row).
- **`v_landuse_outcomes`** — city × dataset × year × land_use_type × action_class ×
  outcome, with `landuse_caveats`.
- **`v_pc_divergence`** — PC recommendation vs linked council outcome through the
  reconstructed `referral` layer; excludes `confidence='low'` links BY DESIGN. Link
  density varies hugely by city (lehi ~450, ogden ~6) — that is linkage coverage, not
  behavior; never compare divergence *rates* without noting link counts. County tier has
  no referral layer yet (city-only view in practice).
- **`v_coverage`** — the caveat-aware coverage matrix (city × dataset + caveat-only rows,
  full caveat text; includes the honest `(no vote layer)` / `(no motion_std layer)` rows
  for db-less counties and ut_state).
- **`v_council_current`** — who serves now (193 seats / 31 entities); from `term`.
- **`v_term_provenance`** — per-city roster confidence mix.
- **`v_election_city`** — per-city audited race view over `election_race`.

## Example queries

**Thematic full-text sweep** (counts are matching DOCUMENTS — one row per minutes file —
not occurrences; a meeting mentioning ADUs ten times counts once):

```sql
SELECT city, COUNT(*) AS docs
FROM fts_minutes WHERE fts_minutes MATCH '"accessory dwelling"'
GROUP BY city ORDER BY docs DESC;
-- snippet(fts_minutes, 0, '>>', '<<', '…', 12) pulls the passage;
-- open the file via the tier-dependent path prefix documented above.
```

**Dissent rates by city** (the caveats column shows which cities can't be compared
naively — nephi's low rate is a recording ceiling, not consensus):

```sql
WITH c AS (SELECT city, COUNT(*) n FROM v_contested_all
           WHERE body != 'PlanningCommission' GROUP BY city),
     t AS (SELECT m.city, COUNT(*) n FROM motion m
           JOIN body b ON b.body_id = m.body_id
           WHERE b.name != 'PlanningCommission' AND m.gov_level='city' GROUP BY m.city)
SELECT t.city, t.n AS motions, COALESCE(c.n,0) AS contested,
       ROUND(100.0*COALESCE(c.n,0)/t.n, 1) AS contested_pct,
       (SELECT GROUP_CONCAT(code,',') FROM caveat cv
         WHERE (cv.city=t.city OR cv.city='*')
           AND cv.dataset IN ('meeting_minutes','*')
           AND code IN ('tally-only','tally-only-partial','dissent-only','vote-ceiling'))
       AS caveats
FROM t LEFT JOIN c ON c.city = t.city ORDER BY contested_pct DESC;
```

**Cross-city land-use approval rates** (final actions only):

```sql
SELECT city,
       SUM(n_motions) AS landuse_final_actions,
       ROUND(100.0 * SUM(CASE WHEN outcome='pass' THEN n_motions ELSE 0 END)
             / SUM(n_motions), 1) AS pass_pct,
       MAX(landuse_caveats IS NOT NULL) AS has_caveats
FROM v_landuse_outcomes
WHERE action_class = 'final-action' AND outcome IN ('pass','fail')
GROUP BY city ORDER BY pass_pct;
```

**Technical-vs-political divergence** (elected body overriding the appointed body):

```sql
SELECT city, confidence, pc_date, pc_recommendation,
       council_date, council_outcome, council_item
FROM v_pc_divergence WHERE diverged = 1 ORDER BY city, council_date;
```

**Adopted ordinance → enacting motion → roll call** (who voted against enacted land-use
law; only `motion_resolution='unique'` rows carry a motion_id — never forced):

```sql
SELECT o.city, o.ordinance_no, o.title, p.full_name, v.vote_value
FROM ordinance o
JOIN motion m ON m.motion_id = o.motion_id
JOIN vote v   ON v.motion_id = m.motion_id
JOIN person p ON p.person_id = v.person_id
WHERE o.land_use != '' AND v.vote_value = 'Nay';
```

**Money vs. land-use votes** (⚠ note the filter: `donor_type='business'` covers only
~700 of 19,685 contribution rows (~3.5% — the distribution is individual 15,999 /
candidate-self 902 / unknown 770 / business 697 / family 510 / loan 356 / anonymous 260 /
pac 166); state your donor-type scope when quoting):

```sql
SELECT cc.city, cc.candidate, SUM(cc.amount_num) AS amt,
       (SELECT COUNT(*) FROM vote v
         JOIN motion_std ms ON ms.motion_id = v.motion_id
        WHERE v.person_id = cp.person_id
          AND ms.motion_type_std = 'Land-Use' AND v.vote_value='Aye') AS landuse_ayes
FROM cf_contribution cc
JOIN cf_candidate_person cp
  ON cp.city = cc.city AND cp.candidate = cc.candidate AND cp.person_id IS NOT NULL
WHERE cc.donor_type = 'business'
GROUP BY cc.city, cc.candidate;
-- per-candidate/race TOTALS must come from cf_cycle, never cf_filing sums.
```

**Projections + regional projects** (the data-forward tiers):

```sql
SELECT geography, year, metric, value FROM projection
WHERE city='wfrc_mpo' AND geography LIKE 'Draper%' AND metric='households'
ORDER BY year;   -- annual city-area grain 2019–2050

SELECT plan_vintage, name, cost, status FROM regional_project
WHERE pin IS NOT NULL AND name LIKE '%1300 East%' ORDER BY plan_vintage;
```

## Regeneration & trust chain

```
per-city:  python3 db/build_db.py && python3 db/build_referrals.py   (each city)
           python3 scripts/normalize_motions.py <city>|--all          (motions_std)
non-city:  python3 <entity>/db/build_db.py                            (per entity)
federated: python3 scripts/build_cities_db.py                         (this db; chains
           scripts/build_search_layer.py; refreshes the cities.db symlink)
verify:    python3 scripts/validate_entity.py --federation            (staleness gate:
           counts + content digest per entity — run before trusting any number here)
           python3 scripts/check_doc_numbers.py                       (docs-vs-db drift)
post-step: python3 scripts/redact_comments.py                         (after any
           comment-layer rebuild — PRIVACY.md policy)
```

gov.db is the **last** link: rebuild it whenever anything upstream changes; it never
feeds back into any canonical file. The build prints — and asserts — reconciliation and
join rates; a silent mismatch is impossible.
