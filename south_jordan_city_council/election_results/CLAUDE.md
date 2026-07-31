# election_results — South Jordan City municipal elections

South Jordan City (**Salt Lake County**, Utah) municipal **general + primary** election
results, normalized to the SLC/Sandy sibling schema. Three CSVs + a reproducible build
script (`clean_elections.py`) + the retained raw county source files under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure

South Jordan is a **Council–Mayor** city: a **5-member council elected by DISTRICT
(Districts 1–5)** plus a **separately elected Mayor** (citywide). 4-year staggered terms,
so each odd-year cycle fills only part of the body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 3 + District 5** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **Districts 1, 2, 4** | 2007, 2011, 2015, 2019, 2023 |

The Mayor is elected only on the **A** cycle (no mayor race in a B year). Every general
cycle 2007→2025 therefore has exactly **3** South Jordan races. (In **2007** the county
labelled the seats `SOUTH JORDAN CITY COUNCIL 1/2/4`; from 2009 on the label became
`…COUNCIL DISTRICT N`. Both normalize to `South Jordan City Council District N`.)

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data. Two
provenance layers:

1. **The county canonical long file** — `salt_lake_county/elections/slco_municipal_results_long.csv`
   (the county-clerk SOVC held once at the level where it originates). `clean_elections.py`
   reads it **directly** and filters to South Jordan council/mayor contests. Precinct- and
   vote-method-level. Consumed for **2007, 2009, 2013, 2015, 2017** (+ their primaries), the
   **2011 primary**, and the **2023 & 2025** generals — all with **zero suppression**,
   summing cleanly to contest totals. **(Re-point 2026-07-19:** the old redundant per-city
   copy `raw/municipal_results_long_south_jordan.csv` was retired after verifying the
   re-pointed build reproduces all three CSVs **byte-identically**; the `precinct='Cumulative'`
   workbook-rollup rows the county canonical now labels are excluded — never a precinct — and
   the **2011 general** the canonical now carries under `South Jordan City Coun N` is skipped
   in the long-file read because the raw parser below already recovers it.)
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly by the
   build for the **three contests the long file does not deliver cleanly** (see below).

## The three gaps recovered from raw

| Contest | Why the archive parse missed / broke it | Recovery |
|---|---|---|
| **2011 general** (Dist 1/2/4) | **Absent** from the parsed layer — the archive's normalizer skipped South Jordan's 2011-general sheets entirely. | Re-parsed `raw/sovc/2011-11-08-municipal-general-sovc.xlsx` (`South Jordan City Coun N` sheets; per-precinct `Total` sub-rows). |
| **2019 general** (Dist 1/2/4) | Present only under the raw **sheet code `SJD Council N`** — the normalizer keyed the contest name off the sheet name, so a `%SOUTH JORDAN%` filter never matched it. **This is the gap flagged in `recon.md`.** | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx` (`SJD Council N` sheets; Family-A wide crosstab) for faithful district numbers, candidate names, precinct totals. |
| **2021 general** (Mayor/D3/D5) | Present but **198/246 rows privacy-suppressed** at the In-Person/Vote-By-Mail method split, destroying the precinct totals. | Re-parsed `raw/sovc/2021-11-02-general-election-sovc.xlsx` (Sheets 39/40/41), whose per-precinct **`Total`** sub-rows are **not** suppressed. |

After recovery the final CSVs have **zero suppressed cells** and every by-precinct sum
reconciles exactly to its by-candidate total (the build asserts 0 mismatches).

**2019 municipal PRIMARY:** the raw 2019 primary SOVC contains **no South Jordan sheet**
(verified) → South Jordan held **no 2019 primary** (each Cycle-B district drew ≤2
candidates, so none was triggered). Logged, not fabricated.

## The three CSVs

- **`south_jordan_races.csv`** — one row per race (**41 races: 30 general + 11 primary**).
  Columns: `office`/`district`/`contest` (canonical) + `contest_verbatim`, `n_candidates`,
  `total_votes`, `winner`/`winner_votes`/`winner_pct`, `runner_up`/`runner_up_votes`,
  `margin_votes`/`margin_pct`, `registered_voters`/`ballots_cast`/`turnout_pct` (where the
  source carries them — 2011/2019 raw + 2021/2023/2025 provide reg/ballots; older archive
  years often don't → blank), `uncontested`, `suppressed_precincts` (`False` everywhere in
  the final data), `source_file`.
- **`south_jordan_results_by_candidate.csv`** — race × candidate (**111 rows**): `votes`,
  `pct`, `rank`, `is_winner`.
- **`south_jordan_results_by_precinct.csv`** — precinct × candidate (**2,062 rows**).
  Precinct IDs are `SJD###` for 2011→2025; older county-wide numeric IDs (`3513`, `3425CA`)
  for 2007–2009. `suppressed=True` marks a redacted county cell (none survive in the final
  data).

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source value (never
overwrites raw): collapses whitespace, strips the `(NP)` / `(NON)` non-partisan tag, drops
the leading `*` registered-write-in mark, and canonicalizes write-ins to `Write-in` /
`Write-in (unresolved)`. To join elections ↔ votes, further strip case/suffixes as the
playbook describes (council `all_votes.csv` names are mixed-case).

## Verification / cross-checks

- **All six current officeholders match `recon.md`**: Mayor **Dawn Ramsey** (won 2017,
  2021, 2025), D1 **Patrick Harris** (2015/2019/2023), D2 **Kathie L. Johnson** (2023),
  D3 **Don Shelton** (2013/2017/2021/2025), D4 **Tamara Zander** (2015/2019/2023), D5
  **Jason McGuire** (2017/2021/2025).
- **2013 Mayor** (external): Dave Alvord defeated incumbent Scott Osborne — confirmed. The
  CSV margin (**100**, Alvord 5226 vs Osborne 5126) is the **final canvassed** SOVC figure;
  news reported a 19-vote election-night margin before absentee/provisional canvass.
- Notable close races: **2025 D3** Shelton +45, **2017 D5** McGuire +47, **2007 D2**
  Johnson +24, **2011 D2** Newton +58 (unseating Johnson).

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent. Re-run only when a **new cycle** posts to the county site: add its SOVC to the
county archive so `salt_lake_county/elections/slco_municipal_results_long.csv` picks it up,
then either (a) rely on the direct long-file read if the canonical covers the new year
cleanly, or (b) add its raw SOVC to `raw/sovc/` + a raw parser call in `clean_elections.py`
(mirror the 2021/2023/2025 handling) for any contest the long file suppresses or mislabels.
Mind whether the cycle is A (Mayor+D3+D5) or B (D1/D2/D4).

## Gaps / caveats

- **No 2019 primary** for South Jordan (see above) — a true no-contest, not a data gap.
- Turnout is populated only where the source carries registered-voter / ballots-cast counts
  (2011, 2019, 2021, 2023, 2025); older archive-slice years leave `turnout_pct` blank.
- **Vote-for-1 everywhere** — South Jordan elects each council seat by single-member
  district, so (unlike Sandy/St. George) there are no at-large / vote-for-N races and no
  RCV cycle (South Jordan did **not** join the 2021 municipal RCV pilot; 2021 was
  plurality).
- Precinct geometry for joins: `~/Desktop/slco-election-archive/geo/` (join `PrecinctID`);
  the city's own council-district layer is the preferred geo source (see `../geo/`).
