# Ogden City — Election Results

Mayor + City Council races for **Ogden City, Utah only** (Weber County), municipal
**general** elections **2019, 2021, 2023, 2025** *and* the August **primaries**
**2021, 2023, 2025** (added 2026-07-31). **23 races (16 general + 7 primary), 60
candidate rows, 1,211 precinct rows** (precinct detail: generals 2023 + 2025,
primaries 2023 + 2025 — see below). Filter on `election_type` ∈ {`municipal general`,
`municipal primary`}.

Ogden has a 7-member council under a **strong-mayor** form: **4 district seats (1–4) +
3 at-large seats (A/B/C)**, each a **single-winner** contest, plus a separately-elected
**Mayor**. Non-partisan, odd years, November general (August primary when >2 candidates).
Terms are 4 years, staggered into two cycles:

| cycle | seats on the ballot | years |
|---|---|---|
| **A-cycle** | Mayor + At-Large **C** + Districts **2 & 4** | 2019, 2023 |
| **B-cycle** | At-Large **A & B** + Districts **1 & 3**     | 2021, 2025 |

Confirmed from the source files (not assumed). In 2025 the county labels the district
seats **"SEAT 1" / "SEAT 3"** rather than "DISTRICT 1/3"; both normalize to
`Ogden City Council District N` here.

## Source: Weber County Elections + Utah state portal

Primary source is **Weber County Elections** (`https://www.weberelections.gov/electionsresults`).
Born-digital (text-layer) canvass PDFs; parse with `pdftotext -layout`.

### Per-cycle source actually used
| year | election_type | source file in `raw/` | granularity |
|---|---|---|---|
| 2019 | general | `2019_general_results.pdf` (Ogden City summary page) | summary only |
| 2019 | **primary** | — **NO RAW HELD** (honest gap, see below) | — |
| 2021 | general | `2021_general_b.pdf` (Weber canvass summary) | summary only |
| 2021 | **primary** | `2021_general_results.pdf` — **misnamed; it IS the Aug 10 2021 primary** (GOTCHA 3) | summary only |
| 2023 | general | `state_api/items/2023-Nov-General__*.json` | summary **+ per-precinct** |
| 2023 | **primary** | `2023_primary_ogden_results.pdf` — **misnamed; it IS the per-precinct canvass** (GOTCHA 5) | per-precinct, **summed** to citywide |
| 2025 | general | `2025_general_precinct.pdf` (precinct canvass) + `2025_general_summary.pdf` (totals) | summary **+ per-precinct** |
| 2025 | **primary** | `state_api/items/primary08122025__OGDEN_CITY_*.json` (Seats A + B only) | summary **+ per-precinct** |

The build is **`build_ogden_elections.py`** (this folder). Reproducible:
`python3 build_ogden_elections.py` (needs `pdftotext` on PATH). Reads only Ogden City
contests, drops `Total Votes Cast` rows, writes the three CSVs.

**Why some cycles have fewer primary contests than general contests:** Utah holds a
municipal primary only for seats where **more than two** candidates file. Every seat
absent from a primary above drew ≤2 candidates in its general — verified against the
general rows' own `n_candidates` (2021 At-Large B & District 1 = 2 each; 2023 District 2
= unopposed; 2025 Districts 1 & 3 = 2 each) **and** against the source's own contest list
(the 2021 primary PDF and the 2025 `primary08122025_ballot-items.json` contain no such
Ogden contest). Nothing is inferred from absence alone.

### GOTCHA 1 — Weber County publishes NO 2023 general municipal PDF
The Weber results index for 2023 carries only a **County Bond** summary/precinct PDF and
the **August primary** municipal PDFs. For the **November general**, the page explicitly
says *"For municipal results visit the municipality's website."* There is **no Ogden 2023
general canvass PDF on the county site** to fetch. So 2023 is sourced from the **Utah state
portal** (`electionresults.utah.gov`, Enhanced Voting backend) JSON export that a prior run
captured into `raw/state_api/`. Those item JSONs carry the official summary **and** full
per-precinct breakdown (42 Ogden precincts) — richer than the 2019/2021 summary PDFs. The
2023 totals were cross-checked against Standard-Examiner (see below) and reconcile to the
state canvass.

### GOTCHA 2 — Wix host redirect (for any future re-fetch)
Weber's PDFs live at `weberelections.gov/_files/ugd/<bucket>_<hash>.pdf` and **301-redirect
cross-host** to `https://48b2f845-…filesusr.com/ugd/<bucket>_<hash>.pdf`. Filenames are
opaque hashes — derive year/type from the **index-page link text**, then `curl -L` (follow
the redirect). WebFetch returns the redirect instead of following it. Older files use a
different ugd bucket prefix (`7dc173` / `7e3a53` vs `92078f`).

### GOTCHA 3 — `2021_general_results.pdf` is mislabeled (it's the PRIMARY)
The file named `2021_general_results.pdf` in `raw/` is actually the **2021 August primary**
(election date 08/10/2021, report run 08/27/2021, header "2021 Primary"). It only contains
the contests that had a primary (At-Large A, District 3 — the >2-candidate fields). The real
**2021 general** is `2021_general_b.pdf` (header "2021 General", 11/02/2021), which has all
four B-cycle Ogden contests. The build uses `2021_general_b.pdf` for the 2021 GENERAL and —
since 2026-07-31 — the mislabeled file for the 2021 **PRIMARY** (it is no longer ignored;
its race rows carry a `note` recording the misnaming). Its `STATISTICS` block is
**county-wide** (58,600 registered / 13,551 ballots for all of Weber County), NOT
Ogden-scoped, so `registered_voters` / `ballots_cast` / `turnout_pct` are left **blank** on
those two rows rather than attributing county figures to the city.

### GOTCHA 5 — the two 2023 "primary" files in `raw/` are swapped AND one is a different city
- `2023_primary_ogden_results.pdf` is **not** a summary — it is the **Ogden City
  *precinct-level* Official Canvass** for the Sep 5 2023 primary (41 pages, precincts
  `OGD01`–`OGD41`, no citywide summary page anywhere in it).
- `2023_primary_ogden_precinct.pdf` is **not** Ogden and **not** precinct-level — it is the
  **NORTH Ogden City** primary *summary*. It is **not used** (the look-alike exclusion rule).

Because the Ogden PDF has no citywide page, the 2023 primary race/candidate totals are
**summed over its 41 precinct pages**. That sum is verified against the PDF's own printed
per-page `Total Votes Cast` lines and the build **aborts** on any disagreement (Mayor
10,347 · At-Large C 9,729 · District 4 4,126 — all three agree exactly). `registered_voters`
/ `ballots_cast` are likewise summed, per contest, over only the precincts that actually
carried that contest (District 4 = 11 precincts, so its turnout is the district's, not the
city's). The 2023 primary reports 41 precincts where the 2023 general reports 42 — the
general splits out the sub-precinct `29OG41:U`, the primary does not.

### GOTCHA 4 — suppressed precincts (voter-privacy)
Very small precincts have their votes **withheld** in the precinct-level reports for voter
privacy. In the 2025 precinct PDF, precinct **`29OG31`** (5 ballots cast) is marked
`Suppressed` with blank candidate cells; the state JSON likewise returns `null` counts for
`29OG31` and `29OG41:U`. Their votes **are** included in the official **summary** total, so
the per-precinct sum is short by exactly the suppressed total (2025 Seat A: precinct-sum
11366 vs canvass 11371 = the 5 withheld 29OG31 ballots). For this reason the 2025 **race /
candidate totals are taken from the official summary PDF** (`2025_general_summary.pdf`,
which matches the state portal exactly), while the **precinct rows come from the precinct
PDF**. Suppressed precincts appear in `ogden_results_by_precinct.csv` as rows with
`votes` blank and `suppressed=True` so the canvass↔precinct reconciliation is auditable.

## Contest normalization
- Canonical labels: `Ogden City Mayor`, `Ogden City Council District N` (N=1–4),
  `Ogden City Council At-Large Seat X` (X=A/B/C).
- Source contest strings vary by year: `Ogden City Council - At Large Seat C` (2019),
  `OGDEN CITY COUNCIL - AT LARGE A` / `- DISTRICT 3` (2021), `OGDEN CITY COUNCIL
  AT-LARGE SEAT C` / `DISTRICT 4` (2023 state), `OGDEN CITY COUNCIL AT-LARGE SEAT A` /
  `SEAT 1` (2025). All map to the canonical labels above.
- **Look-alike exclusion:** only `OGDEN CITY` contests are taken. The same county files
  contain **NORTH OGDEN**, **SOUTH OGDEN**, and **OGDEN VALLEY** city contests — all
  excluded.
- Precinct IDs normalized to UGRC form **`29OG##`** (the 2023 state portal uses `OGD##`;
  the 2025 PDF already uses `29OG##`). Sub-precinct suffix `:U` preserved (`29OG41:U`).
- Unopposed seats (one candidate) are kept as a race with `winner_pct=100`, blank
  runner-up. District 2 (Richard Hyer) was unopposed in both 2019 and 2023.

## Parsing note (contest-boundary detection)
Every contest header line in these Electionware PDFs is immediately followed by a
`Vote For N` line, but the **2025 summary PDF has NO "Total Votes Cast" closer** between
contests (the 2019/2021 summaries do). Both the summary and precinct parsers therefore
treat the `Vote For` lookahead as the contest boundary — without this, the last Ogden
contest on a page slurped every following (non-Ogden) candidate row. Fixed and verified.

## External cross-check (winners) — CONFIRMED, not fabricated
- **2025** (Standard-Examiner, "Washington, Lundell, Lopez earn seats… Richey retains
  seat," 2025-11-06): Alicia Washington (At-Large A, 6,439 / 56.63%), Kevin Lundell
  (At-Large B, 6,879 / 60.24%), Flor Lopez (Dist 1, 1,108 / 60.12%), Ken Richey (Dist 3,
  1,795 / 52.15%). **All match the CSVs exactly.**
- **2023** (Standard-Examiner / KUER, Nov 2023): Ben Nadolski (Mayor, def. Taylor Knuth),
  Shaun Myers (At-Large C, def. J. Levi Andersen), Dave Graf (Dist 4, def. Steven Van
  Wagoner), Richard Hyer (Dist 2, unopposed). Winners match; the official state-portal
  vote totals (Nadolski 6,418) are slightly higher than the day-after newspaper count
  (~6,258) because Utah is largely vote-by-mail and the canvass kept counting — the CSV
  uses the **official canvass** totals.
- 2025 race totals additionally cross-checked PDF↔state portal in the build (all 4 OK).

## Primaries (added 2026-07-31)

Seven primary races: **2021** (At-Large A, District 3), **2023** (Mayor, At-Large C,
District 4), **2025** (At-Large A, At-Large B). Conventions, matching the audited peer
shape (murray / holladay):

- `election_type = "municipal primary"`, `voting_method = "plurality"`, `n_seats = 1`.
- **`winner` / `runner_up` on a primary row are the top two vote-getters — the two who
  ADVANCE, not an office-winner.** `is_winner=True` on rank 1 in
  `ogden_results_by_candidate.csv` means "led the primary", nothing more. Take office
  winners from the `municipal general` rows only.
- The ten 25-col superset extras are filled **only where the source supports them**;
  `contest_verbatim` carries the canvass's own contest header line. The 16 pre-existing
  **general** rows were left byte-identical (their extras stay blank — back-filling them is
  a separate, reviewable change; `build_records(..., keep_verbatim=True)` is the hook).
- The build runs a **primary→general advancement cross-check** and prints it per contest.

### The 2023 At-Large C advancement discrepancy (real, annotated, NOT explained)
The 2023 At-Large C primary's top two were **SHAUN MYERS (4,426)** and **LARA GALE
(2,556)**; the November general's field was **MYERS vs J. LEVI ANDERSEN** (3rd in the
primary, 1,595). Both rows are exactly as canvassed and both reconcile to their sources.
**No source held in this repo states why Gale was not on the general ballot**, so the
primary race row carries a `note` recording the discrepancy and nothing more — no
withdrawal, disqualification, or other cause is asserted. The other six primaries'
top-two match their general's field exactly.

## Gaps / not obtained
- **No 2019 PRIMARY canvass is held** — nothing in `raw/` covers an August 2019 Weber
  County municipal primary, and whether Ogden even required one is **unverified**: the 2019
  general carried 2 mayoral candidates and 3 unopposed council seats, which is consistent
  both with "no primary was needed" and with "a primary narrowed a >2-candidate mayoral
  field to 2". Ledgered, never synthesized. Closing it means fetching the 2019 primary
  canvass from Weber County (see GOTCHA 2 for the Wix redirect recipe).
- **No per-precinct detail for 2019 or 2021** (general **or** primary) — Weber published
  only city/county **summary** PDFs for those cycles. Race and candidate rows are complete;
  `ogden_results_by_precinct.csv` covers **2023 + 2025** (both general and primary).
- `raw/2020_*` and `2025_primary_ogvalley_*` files are unrelated to Ogden City council
  cycles (2020 is not a municipal year; Ogden Valley ≠ Ogden City) — not used. Likewise
  `2023_primary_ogden_precinct.pdf`, which is North Ogden (GOTCHA 5).

## Files
- `ogden_races.csv` — one row per race, **25-col audited superset**; 23 rows (16 general +
  7 primary). Key on `(year, election_type, contest)`.
- `ogden_results_by_candidate.csv` — race × candidate (votes, pct, rank, is_winner); 60 rows.
- `ogden_results_by_precinct.csv` — `29OG##` × candidate (2023 + 2025, general **and**
  primary), with `suppressed`; 1,211 rows.
- `build_ogden_elections.py` — regenerates all three from `raw/`.

**Reconciliation (re-verified 2026-07-31, all 23 races):** every race's `total_votes`
equals the sum of its `ogden_results_by_candidate.csv` rows; every precinct-bearing race's
precinct sum equals its total **except** where voter-privacy suppression withholds counts —
the two 2025 primary races are short by exactly 11 each (`29OG31` + `29OG41:U`, the same
pair as the 2025 general; GOTCHA 4), and those precincts appear as blank-vote
`suppressed=True` rows so the shortfall is auditable rather than silent.
