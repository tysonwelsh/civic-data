# election_results — Sandy City municipal elections

Sandy City (Salt Lake County, Utah) municipal **general** election results, normalized
to the SLC-style schema. Three CSVs + a reproducible build script that derives from the
**county canonical** (`salt_lake_county/elections/`), plus the 2021 RCV-final PDFs in
`raw/`. **Do not rebuild unless a new cycle posts** (see "Rebuilding" below).

## Source

All results come from the **Salt Lake County Clerk** (Sandy elections are county-run, not
city-run). **The SOVC layer is now derived DIRECTLY from the county canonical held once at
the level where it originates** — no per-city raw SOVC copy is kept:

- **`salt_lake_county/elections/slco_municipal_results_long.csv`** — the canonical SL County
  Clerk SOVC (precinct × candidate × vote-method), filtered here to Sandy council/mayor
  general contests. Provides every per-precinct count.
- **`salt_lake_county/elections/election_results_by_contest.csv`** — the derived
  contest → office/district/seats map (jurisdiction-tagged `sandy`).

**Re-point 2026-07-19** (root TODO.md Phase-2 follow-up): this build previously parsed a
redundant local copy of the SOVC `.xlsx` exports under `raw/`. Those copies were retired
after `build_sandy_elections.py` was re-pointed at the county canonical and verified to
reproduce all three CSVs **byte-identically**. This became possible only because the county
canonical's 2026-07-19 suppression-recovery repaired the dropped un-suppressed per-precinct
2021 totals (the very gap that once forced Sandy to parse raw). The upstream provenance
(county-clerk site + `~/Desktop/slco-election-archive` mirror) lives in the county module's
`raw/SOURCES.md`.

**Non-SOVC source RETAINED in `raw/` (the county canonical does NOT carry it):** 2021 was
Sandy's RCV pilot; the county canvass holds only first-choice (round-1) counts. The official
RCV **final-round** winner/runner/margin come from the two PDFs below (hard-coded as the
`RCV2021` constants in the build):

| File in `raw/` | Use |
|---|---|
| `2021-general-election-ranked-choice-summary-report.pdf` | 2021 **RCV final-round** winners/margins |
| `2021-general-election-sandy-recount-results.pdf` | 2021 Sandy recount (see Recounts) |

## The three CSVs (do not edit by hand — regenerate)

- **`sandy_races.csv`** — one row per race. **14 races.** Cols include `n_seats`,
  `n_candidates`, `voting_method`, `total_first_choice_votes`, `winner`/`runner_up` with
  votes/pct, and `margin_votes`/`margin_pct`.
- **`sandy_results_by_candidate.csv`** — race × candidate (47 rows). `round1_votes`/
  `round1_pct`, `final_votes` (populated only for 2021 RCV), `rank`, `is_winner`.
- **`sandy_results_by_precinct.csv`** — precinct × candidate (2,811 rows), for geo
  analysis. Precinct IDs are `SAN###`. `suppressed=True` where the county redacted a small
  per-precinct/method count (`votes` blank). For 2021 (RCV) the per-precinct `note` reads
  `first-choice (round 1)` — only round-1 counts exist at precinct level.

## Council / mayor structure

Sandy is a **Council–Mayor** city. The legislative body is a **7-member council = 4
district seats (District 1–4) + 3 at-large seats**, plus a **separately-elected Mayor**
(the Mayor is executive and does **not** vote on the council). Terms are 4-year, staggered,
so each election cycle fills only part of the body. As the contests appear in the county
SOVC files:

| Year | Contests built | Note |
|---|---|---|
| 2019 | Council At-Large (**Vote for 2**) · District 2 · District 4 | 3 races; no mayor race |
| 2021 | Mayor · Council At-Large (Vote for 1) · District 1 · District 3 | 4 races; **RCV** |
| 2023 | Council At-Large (**Vote for 2**) · District 2 · District 4 | 3 races; no mayor race |
| 2025 | Mayor · Council At-Large (Vote for 1) · District 1 · District 3 | 4 races |

The Mayor sits on the odd "B" cycle (**2021 / 2025**) — there is no Sandy mayor race in 2019
or 2023. The 3 at-large seats are staggered **2+1**: **two** seats fill together in the
**2019 / 2023** cycle (Vote-for-2) and **one** seat fills alone in the **2021 / 2025** cycle
(Vote-for-1). For a multi-seat At-Large race, `sandy_races.csv` lists the **top vote-getter**
as `winner` and the **first loser** as `runner_up` (margin = last-winner − first-loser);
**all** winners are flagged `is_winner=True` in `sandy_results_by_candidate.csv` — that file
is authoritative for the full winner set. Verified winners: **2019 At-Large = Sharkey +
Houseman** (Edwards, Theodore lost); **2023 At-Large = Sharkey + DeKeyzer** (Bennett,
Christensen lost).

## Ranked-choice voting — 2021 ONLY

Sandy ran **all four 2021 city races as ranked-choice voting (RCV)** under Utah's municipal
RCV pilot. Sandy **reverted to plurality** in 2023 and 2025 (the pilot was not renewed).
Handling in the build:

- The county canonical's 2021 rows hold only **round-1 (first-choice)** counts (the RCV
  canvass reports first-choice at precinct grain) — these populate `round1_votes` and the
  per-precinct rows.
- The official **RCV final-round** winner, runner-up, margin, and per-candidate
  `final_votes` come from the county's *Official Final Ranked Choice Results* summary report
  (`raw/2021-general-election-ranked-choice-summary-report.pdf`); these final-round numbers
  are hard-coded in `RCV2021` in `build_sandy_elections.py` and match the separately
  published Sandy recount. Eliminated candidates carry their last-active-round total so the
  final-standing ranking is faithful.
- So for 2021: `voting_method=RCV`, `round1_*` = first-choice, race-level
  winner/runner_up/margin + `final_votes` = RCV final round. For 2019/2023/2025:
  `voting_method=plurality`, `final_votes` blank.

## Contest normalization

`canon()` in the build script maps every contest to a canonical name:
`Sandy City Mayor`, `Sandy City Council At-Large`, `Sandy City Council District {1..4}`,
with `office` = `Mayor`/`Council` and `district` = `''`/`At-Large`/`1..4`. Candidate names
are normalized (whitespace collapsed, `(NP)` non-partisan tag stripped, write-ins mapped to
`Write-in` / `Write-in (unresolved)`). Unresolved write-ins with 0 votes are excluded from
`n_candidates` but kept as `rank` rows in `by_candidate`.

## Recounts

Two Sandy recounts exist in the county source; both are documented, not separately merged
into the CSVs (the CSV winners already reflect the certified/final outcome):

- **2017 Sandy Council District 3 recount** — `2017-05-17 Salt Lake Council 5 & Sandy
  Council 3 Recount` (SOVC zip + PDF). Lives in `~/Desktop/slco-election-archive/raw/
  historical-election-results/`; **not** in this repo's `raw/` because 2017 is outside the
  built cycles (build window = 2019/2021/2023/2025).
- **2021 General Sandy recount** — `raw/2021-general-election-sandy-recount-results.pdf`
  (the tight 2021 RCV mayor / at-large contests). Its final figures agree with the RCV
  summary report used for the `final_votes` in `sandy_races.csv`.

## Rebuilding

```
cd election_results && python3 build_sandy_elections.py   # reads the county canonical, writes the 3 CSVs
```
The build reads `salt_lake_county/elections/` directly (no local SOVC copy). Only re-run
after a **new Sandy cycle** has been ingested into the county canonical (`build_elections.py`
there) — the new cycle is then picked up automatically for plurality contests; if it is RCV,
add the final-round `RCV2021`-style constants from that cycle's summary-report PDF (retained
in `raw/`). Do **not** edit the CSVs by hand.

## Gaps / caveats

- **2019 municipal primary** Sandy results are unparsed upstream (a "Family-B"
  numbered-sheet layout in the SLCo archive, raw-only). Only **general** elections are built
  here; primaries are out of scope.
- 2023 At-Large is the only Vote-for-2 race — keep the `n_seats=2` semantics in mind for any
  "winner" logic.
- Precinct geometry for joins lives in `~/Desktop/slco-election-archive/geo/
  slco_precincts_current.gpkg` (join field `PrecinctID`).
