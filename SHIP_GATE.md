# SHIP GATE — the state that means "ready to publish"

Readiness is a STATE, not an empty TODO list. The repo is publishable when the three predicates
below hold. **Policy: an open [DEBT] item blocks publish only if it makes a published value
WRONG; incompleteness ships with its caveat row.** (Honest gaps are data — cardinal rule 1.)

## Predicate 1 — federation integrity (runnable)

```
python3 scripts/validate_entity.py --federation   # must exit 0, 44/44 in step
sqlite3 "file:gov.db?mode=ro" "PRAGMA integrity_check;"    # ok
sqlite3 "file:gov.db?mode=ro" "PRAGMA foreign_key_check;"  # no rows
```

## Predicate 2 — every known ceiling is caveat-carried IN THE DB

Every measurement ceiling asserted in a per-entity CLAUDE.md / COVERAGE.md (tally-only eras,
dissent-only naming, vote-vocabulary limits, absent layers, classification ceilings) has a
matching row in gov.db `caveat` on the CORRECT (city, dataset), and no caveat row asserts
something the data contradicts. Spot-check the known hazards:

```
-- zero-caveat entities (should return no BUILT city with a documented ceiling):
SELECT e.city FROM entity e LEFT JOIN caveat c USING(city) WHERE c.city IS NULL;
-- dissent-only/tally-only cities must be flagged where the votes actually are:
SELECT city, body, COUNT(*) n, SUM(vote='Aye') ayes FROM vote v JOIN motion m USING(motion_id)
  GROUP BY 1,2 HAVING n>30 AND ayes=0;   -- every row needs a caveat on that dataset
```

## Predicate 3 — no document asserts what the db contradicts

The number-bearing claims in README.md and CLAUDE.md (headline table, per-entity quirk counts,
coverage statements) re-verified against gov.db at the current build. Generate headline counts
from `build_info` rather than hand-transcribing wherever possible. A closure that falsifies a
doc claim updates the doc in the same session — this predicate is maintained, not re-earned.

## Publication mechanics (one-time, tracked as TODO.md PUBLISH GATE G1–G9)

git init private with corrected .gitignore → LICENSE/CITATION/METHODS/PRIVACY → doc pass →
search-layer fixes → consumer packaging (quickstart, gov.db.gz release asset, data
dictionary) → build hardening → the three wrong-value data fixes → declare against this file
→ publish (repo + release + Zenodo DOI + municipalsky.com link).

## Status

| date | P1 | P2 | P3 | note |
|---|---|---|---|---|
| 2026-07-31 (review) | PASS (44/44, ok, 0) | FAIL — 16 zero-caveat entities; 2 falsified caveats (utah_county, weber); 1 mis-filed (south_jordan); 1 stale (millcreek) | FAIL — README/CLAUDE.md county counts, disposition claim, cities_db_SCHEMA.md, entity counts | caveat fix in progress (G2); doc pass queued (G4) |
| 2026-07-31 (post-G2) | PASS (44/44, ok, 0; build 14:30:48) | PASS — caveat 63→88; 0 built entities uncaveated; both falsified rows rewritten; SJ PC + magna dissent-only rows verified surfacing in v_member_record_all | FAIL — G4 doc pass pending | G1 (git) + G3–G8 remain |
