# update-council-roster — detection queries

Copy-paste probes for step 2 of `SKILL.md`. Each is a **FLAG generator** — a hit is a
candidate to investigate at source, never an auto-edit. Set `:city` to the slug
(`slc`, `provo`, `nephi`, `vineyard`, …). Run from the repo root against `cities.db`.

**Name-key vs person-key — read this first.** `cities.db` stores a compact `person.name_key`
(`alejandropuy`, `victoriapetro`) while the roster's `term.person_key` is a `first_last` slug
(`alejandro_puy`). The driver's `cfg.db_key` dict bridges them, and a name-change person maps
**two** `name_key`s to **one** `person_key` (SLC `victoriapetroeschler` + `victoriapetro` →
`victoria_petro`). So a raw `name_key NOT IN (SELECT person_key …)` join will over-report — use
it as a first pass, then resolve each hit **through the driver's `db_key` map** before deciding
it's genuinely unrostered. An unresolved `name_key` is either a real new person (appointee) or a
normalization miss to add to `db_key`.

---

## 1. Unrostered voter (mid-term appointee OR name-normalization miss)

Council voters in the vote record whose `name_key` isn't obviously on the roster. Investigate
each: is it a **new person appointed mid-term**, or the **same person under a new/variant name**
(cross-check `person` for a near-duplicate, then extend `db_key`)?

```sql
SELECT p.name_key, r.first_seen, r.last_seen
FROM role r
JOIN person p ON p.person_id = r.person_id AND p.city = r.city
JOIN body   b ON b.body_id   = r.body_id
WHERE r.city = :city AND b.name = 'Council'
ORDER BY r.last_seen DESC;
```

Then eyeball each `name_key` against the current roster (through `db_key`):

```bash
python3 <city>_city_council/roster/build_roster.py --demo   # prints the current roster
```

Signature of an **appointee**: an off-cycle `first_seen` landing right after a predecessor's
last vote (Vineyard `clawson` first_seen 2024-11-20). Signature of a **name change**: two
`name_key`s whose vote spans are contiguous/overlapping for what is clearly one person — search
`person` for the near-duplicate:

```sql
SELECT name_key, full_name FROM person WHERE city = :city ORDER BY name_key;
```

## 2. Disappeared member (candidate resignation / departure)

A still-serving roster member whose last observed council vote predates the latest council
meeting by more than one normal cadence → FLAG an `end_date` to confirm from the minutes
(farewell / vacancy declaration).

```sql
-- latest Council meeting on record for the city:
SELECT MAX(m.meeting_date)
FROM meeting m JOIN body b ON b.body_id = m.body_id
WHERE m.city = :city AND b.name = 'Council';

-- per-person last observed Council vote (compare each currently-serving member to the above):
SELECT p.name_key, MAX(m.meeting_date) AS last_vote
FROM vote v
JOIN motion  mo ON mo.motion_id = v.motion_id
JOIN meeting m  ON m.meeting_id  = mo.meeting_id
JOIN body    b  ON b.body_id     = mo.body_id
JOIN person  p  ON p.person_id   = v.person_id AND p.city = v.city
WHERE v.city = :city AND b.name = 'Council'
GROUP BY p.name_key
ORDER BY last_vote DESC;
```

(For tally-only cities — Nephi ~95% unnamed, West Jordan PC — the vote record is sparse; a low
`last_vote` there is expected, not a departure. Lean on minutes present-lists instead.)

## 3. Roll-size / 8th-voter sentinel (extraction artifact — do NOT extend a tenure)

A meeting-date whose distinct council voters **exceed the seat count** flags an artifact: a
mayor tie-break counted as a member, a Board-of-Canvassers session (the mayor sits as an extra
voter), or an LLM stray vote (SLC Mano 2026-03-24). FLAG and log; never let it seat or extend a
tenure. Set the threshold to the city's council size (SLC = 7; Provo = 7; Nephi = 5; Vineyard =
5).

```sql
SELECT m.meeting_date, COUNT(DISTINCT v.person_id) AS voters
FROM vote v
JOIN motion  mo ON mo.motion_id = v.motion_id
JOIN meeting m  ON m.meeting_id  = mo.meeting_id
JOIN body    b  ON b.body_id     = mo.body_id
WHERE v.city = :city AND b.name = 'Council'
GROUP BY m.meeting_date
HAVING voters > 7            -- set to the city's council seat count
ORDER BY voters DESC;
```

Distinguish **recurring benign** hits (Board of Canvassers, a voting-mayor city like Millcreek
or Vineyard where the mayor legitimately votes, documented tie-breaks) from a **stray**
one-off artifact. Only the latter is a defect; recurring structural ones are known and belong in
the city's notes, not the roster.

## 4. Bidirectional election crosscheck

The builder already forward-checks "every general winner → a tenure" (`election_crosscheck`,
prints to stderr on `--check`). Add the **reverse** by hand: every `elected`/`reelected` tenure
with a non-blank `election_year` must map back to an `is_winner` general row. The only
sanctioned exception: **pre-floor / election-anchored** terms (predating the vote-data or
minutes floor) carry no in-data winner row and MUST be `confidence=medium`.

```sql
-- roster's election-anchored tenures:
SELECT seat_id, person_name, person_key, election_year, start_event, confidence
FROM term
WHERE city = :city AND start_event IN ('elected','reelected') AND election_year <> ''
ORDER BY election_year, seat_id;
```

Compare against the winners file — municipal **general** rows only (drop primary "advancer"
rows, which some cities mark `is_winner`):

```bash
# winners in the election file (UPPER-CASE names; watch (NP) suffixes + nicknames):
awk -F, 'NR==1 || tolower($0) ~ /true|yes|,1,/' \
  <city>_city_council/election_results/<city>_results_by_candidate.csv
```

Any `elected` tenure with an `election_year` at/after the election floor that has **no** winner
row is a candidate fabricated/mis-yeared tenure → verify at source. Any winner with **no**
tenure is the §1/new-winner case. Known-expected mismatches (broken SOVC, RCV first-choice
mislabels) are documented in the city's `roster/CLAUDE.md` — check there before treating one as
a defect (e.g. SLC's 4×2019 "VOTE BY MAIL" + 2021 D2 "BILLY PALMER" are EXPECTED).

## 5. Redistricting check (district cities)

New redistricting resolution/ordinance in fresh minutes → a new `district_versions` plan (+
`district_precincts` composition). Confirm the current federated state and whether geometry is
on disk:

```sql
SELECT district_id, plan_id, effective_start, effective_end, geometry_ref, confidence, note
FROM district_version
WHERE city = :city
ORDER BY plan_id, district_id;
```

Real geometry on disk (a geojson under `<city>/geo/`) → `high`; prior/unacquired boundaries →
explicit gap row (blank `geometry_ref`, `confidence=low`). Then reconcile precinct composition
against the latest election with `python3 roster/build_roster.py --check` (runs
`precinct_crosscheck`).

---

## After applying confirmed changes

```bash
python3 <city>_city_council/roster/build_roster.py    # regenerate (validators re-gate)
python3 scripts/build_cities_db.py                    # re-federate term/district_version/district_precinct + v_council_current
```

Verify the federation picked up the change:

```sql
SELECT city, confidence, COUNT(*) FROM term WHERE city = :city GROUP BY confidence;   -- honesty read
SELECT * FROM v_council_current WHERE city = :city;                                   -- current seat-holders
```
