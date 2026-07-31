# SLC Municipal Election Results

Salt Lake County Clerk canvass (2007–2025), filtered to **Salt Lake City Council and
Mayoral races only** and normalized for analysis. **Source of truth is the COUNTY
CANONICAL** — `../../salt_lake_county/elections/slco_municipal_results_long.csv`
(read-only input here; its provenance is that folder's CLAUDE.md + raw/SOURCES.md).

## Pipeline (re-pointed 2026-07-19 — the "re-point the 7 city election pipelines" item, SLC slice)

```
../../salt_lake_county/elections/
    slco_municipal_results_long.csv      county canonical SOVC, tidy long form (SOURCE OF TRUTH)
clean_elections.py                       filter to SLC council+mayor, normalize, aggregate
  -> slc_results_by_precinct.csv         filtered precinct x candidate (geographic analysis)
  -> slc_results_by_candidate.csv        race x candidate: votes, pct, rank, is_winner
  -> slc_races.csv                       ONE ROW PER RACE: winner, runner-up, margin, turnout
```

Regenerate: `python3 clean_elections.py` (add `--report` for closest-races summary).
`slc_races.csv` is written in the repo-wide 25-col superset header (SCHEMA_SPEC §9);
the columns this pipeline cannot derive from the county long file stay blank
(honest gaps, never inferred).

**History:** this folder used to hold redundant per-year raw copies
(`{year}_municipal_{primary|general}.csv`, 18 files, 2007–2025). Before deletion each
was proven **byte-identical** to the canonical filtered by (year, election_type) —
except 62 SLC-relevant rows of the county's later lead-(v) relabel, where zero-vote
report-template rows now carry `precinct='Cumulative'` (the workbook's own rollup
label, never a precinct) instead of a misattributed real precinct. The re-pointed
rebuild reproduced `slc_races.csv` and `slc_results_by_candidate.csv` **byte-identical**
(gate proof, pre-scope-extension); `slc_results_by_precinct.csv` changed in exactly
those 62 precinct-label-only, `votes=0` rows. Deleted raw copies are backed up in
`_backups/2026-07-19-pv-tierb-low/lead-tu-slc/`. The canonical covers the full 2007+
range, so **no race lost its derivation** (there is no pre-2019 split — all 59 races,
2007–2025, derive from the one canonical file). `../geo/build_precinct_district_map.py`
was re-pointed the same way (output byte-identical).

## 2019 municipal PRIMARY adopted (2026-07-19, TODO lead (t))

The county canonical carries the recovered **2019 municipal primary** (upstream
`parse_family_d()` re-parse, verified against 9 audited per-city races — see the county
elections CLAUDE.md). The re-pointed pipeline now emits SLC's two 2019 primary races
(`election_type='municipal primary'`, same derivation rules as every other race):

- **Salt Lake City Mayor** (the 8-way primary): ERIN MENDENHALL 9,046 (24.27%) /
  LUZ ESCAMILLA 8,015 (21.51%) / JIM DABAKIS 7,531 / DAVID GARBETT 6,238 /
  DAVID IBARRA 3,046 / STAN PENFOLD 2,528 / RAINER HUCK 566 / RICHARD N GOLDBERGER 296
  — total 37,266. Matches the known outcome: Mendenhall + Escamilla advanced to the
  general (which Mendenhall won 26,762–19,393).
- **Salt Lake City Council District 6**: CHARLIE LUKE 3,542 / DAN DUGAN 2,677 /
  JT MARTIN 818 — total 7,037. Luke + Dugan advanced; Dugan won the general 4,655–4,473.

These are the only SLC-proper contests in the county's 2019 primary canvass (no
D2/D4 primary rows — see root TODO.md's separate lead about the scheduled-then-not-held
2019 primaries). **Primary `winner` = plurality leader; in a two-advance municipal
primary read ranks 1–2 as the advancers, not rank 1 as an office winner.** Diff proof:
all 57 prior races byte-identical and in order; exactly 2 race rows (+11 candidate
rows, +1,058 precinct rows) inserted at their (year, election_type, contest) sort
position.

## 2026-07-19 defect + fix (2019 garbled winners; 2021 suppressed-precinct undercounts)

Two source defects found during roster H-C verification, both fixed at the RIGHT layer
(the upstream `~/Desktop/slco-election-archive` normalizer / its per-year slices — never
by hand-editing outputs); backups in `_backups/2026-07-19-slc-elections-fix/`:

1. **2019 general was a STALE, garbled slice.** `2019_municipal_general.csv` predated the
   archive's 2026-07-12 `parse_family_b()` fix, so the ballot-METHOD sub-headers ("Vote By
   Mail"/"Vote Centers"/"Early Voting") had been parsed as the *candidates* — the D2/D4/D6/
   Mayor winner rows literally read "Vote By Mail". Re-synced from the fixed archive slice.
   True 2019 winners (verified against the raw workbook's own `Total:` rows AND the seated
   roster/minutes): **D2 ANDREW JOHNSTON 1,745** (Benally 1,075) · **D4 ANA VALDEMOROS
   4,734** (Rodgers 866) · **D6 DAN DUGAN 4,655** (Luke 4,473 — margin 1.99%) · **Mayor
   ERIN MENDENHALL 26,762** (Escamilla 19,393).
2. **2021 privacy-suppressed precincts' votes were dropped** (the county prints `****` on
   low-turnout precincts' method rows but DOES print each precinct's Total row; the
   upstream family-C parser skipped all Total rows). All five 2021 SLC contests were
   partial sums; in **D2 it swapped the winner** ("Palmer 363 / Puy 361"). Certified
   first-choice totals (= the workbook's `Electionwide - Total` rows): **D2 ALEJANDRO
   PUY 1,084 / Palmer 751** (Puy is the plurality leader AND the seated member,
   2022-01-04+); D1 Petro-Eschler 1,612 / Perez 1,440; D3 Wharton 3,750 (runner-up is
   McDonough 1,231, not Berg); D5 Mano 2,902; D7 Fowler 3,798. The normalizer now emits
   `vote_method='Total'` recovery rows exactly where every method row was suppressed.

**2021 RCV caveat:** SLC's 2021 general was an RCV-pilot election (see `roster/CLAUDE.md`);
the SOVC stores **first-choice tallies**, so 2021 `winner_pct`/`margin_pct` are
first-choice shares, not final-round margins. Every 2021 first-choice leader matches the
RCV winner / seated member, so `winner` is correct as stored.

Diff surface of the fix: 9 `slc_races.csv` rows (the four 2019 + five 2021 rows above);
sidecars changed only in 2019/2021-general rows; all other years/races byte-identical.
*(The per-year raw slices this fix re-synced were retired later the same day by the
pipeline re-point above; the 2019 municipal primary follow-up lead was adopted the same
day — see the sections above.)*

## Filtering + normalization (the tricky part)

Contest names are wildly inconsistent across years and must be matched carefully:
- `SALT LAKE CITY COUNCIL DISTRICT 1` (2021+), `... CNCL DIST 1` (2017 general),
  `... COUNCIL DIST 1` (2009–15), `... COUNCIL #4` (2007), `Salt Lake City Council 2`
  (2011, mixed case), `SLC Council 6` / `SLC Mayor` (2019, abbreviated).
- Must match SLC **proper** — startswith `SALT LAKE CITY` or `SLC ` — and **exclude
  SOUTH SALT LAKE / SSL** and Salt Lake County. `normalize_contest()` handles all of it,
  collapsing to canonical `Salt Lake City Mayor` / `Salt Lake City Council District N`.
- Non-candidate `Total` rows are dropped; `WRITE-IN` variants are kept as candidates.

## Coverage

- **Mayor:** 2007, 2011, 2015, 2019, 2023 (4-yr terms) + primaries (incl. the 8-way
  2019 primary, adopted 2026-07-19).
- **Council districts staggered:** odd (1,3,5,7) in 2009/13/17/21/25; even (2,4,6) in
  2007/11/15/19/23. Occasional special elections add an off-cycle district (e.g. D2 in 2021).
- **59 races total** after filtering (57 + the two 2019 primary races adopted
  2026-07-19). `slc_races.csv` = 59 data rows; `slc_results_by_candidate.csv` = 200;
  `slc_results_by_precinct.csv` = 28,680.

## Connecting to the rest of the repo

Elections are point-in-time events (November, odd years) — they do NOT belong in the
weekly `../weeks/` bundles. They connect via **person + year + district**: a race
**winner** becomes a councilmember whose roll-call votes live in
`../meeting_minutes/all_votes.csv` and whose constituents' comments are in
`../public_comments/`. That lets you ask, e.g., "did a member's votes / constituent
sentiment track their election margin?"

**Join caveat:** candidate names here are upper-case and may carry a `(NP)`
(non-partisan) suffix and maiden/married variants — e.g. `VICTORIA PETRO-ESCHLER (NP )`
(2021) vs `VICTORIA PETRO` (2025) vs `Victoria Petro` in the votes data. Normalize names
(strip case, `(NP)`, suffixes) before joining.

## Don't
- Don't edit the county canonical (`salt_lake_county/elections/` — read-only input;
  corrections go through the upstream archive normalizer, see that folder's CLAUDE.md).
- Don't treat `Total` rows as candidates, or match `SOUTH SALT LAKE`/`SSL` as SLC.
- Don't treat `precinct='Cumulative'` as a precinct (workbook rollup label, always 0 votes).
- Don't read a primary race's `winner` as an office winner (top-2 advance).
