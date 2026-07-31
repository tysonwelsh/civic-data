# election_results — Murray City municipal elections

Murray City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/Sandy/south_jordan sibling schema. Three CSVs + a reproducible build
script (`clean_elections.py`) regenerates the 2021/2023/2025 cycles. Original data floor
**2020**; **six 2019/2021 rows were hand-appended 2026-07-17** from the SLCo SOVC re-parse
(owner-approved — the 2019 general D1/D3/D5, 2019 primary D1/D3, and the 2021 MAYOR primary;
see the dated note at the end of this file). Those recovered rows are NOT reproduced by
`clean_elections.py` and must be re-appended if the file is regenerated.

## Council / mayor structure

Murray is a **Council–Mayor** city: a **5-member council, each seat elected by
single-member DISTRICT (D1–D5)**, plus a **separately elected Mayor** (citywide; the mayor
is executive and does **not** vote on the council). 4-year staggered terms:

| Cycle | Seats up | In-scope years |
|---|---|---|
| **A** | **Mayor + District 2 + District 4** | 2021, 2025 |
| **B** | **Districts 1, 3, 5** | 2023 |

Mayor sits only on the **A** cycle → **no mayor race in 2023**. **2025 additionally held a
`District 3 (2-Year Term)` unexpired-term SPECIAL** (off the normal B-cycle — D3's regular
seat is a 2023/2027 seat; the 2-year special fills the balance of the term after mid-term
D3 churn). It is flagged in the `note` column and its canonical `contest` keeps the
`(2-Year Term)` marker so it never collides with a regular D3 race.

## Source (single canonical provenance)

All results are filtered from the **county-canonical** normalized Statement-of-Votes-Cast
(SOVC) long file — **not re-scraped**:

    /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv

**Filter:** rows whose `contest` contains `MURRAY` (case-insensitive), `year ∈ {2021,2023,
2025}`. Each source row is precinct- and vote-method-level and carries the true
`source_file` + `sheet`. No local `raw/` mirror is kept — the county repo is the source of
record. Rebuild: `python3 clean_elections.py [--report]` (idempotent).

### Two dedup / recovery decisions (both material)

1. **UPPER-CASE vs Mixed-Case "duplicate" labels are the GENERAL vs the PRIMARY** — not two
   copies of one race. In 2023 the file carries both `MURRAY CITY COUNCIL DISTRICT 1`
   (general, `…official-report-12-05-2023….xlsx`) and `Murray City Council District 1`
   (primary, `statementofvotescastrpt.xlsx`), with different candidate sets. Keying every
   race on **(year, election_type, canonical_contest)** keeps them distinct — no merge.

2. **The 2023 PRIMARY rows are triplicated** — the primary sheets export each
   `precinct × candidate` row **three times, verbatim** (a county-file artifact). Left
   un-deduped this triples the primary totals (D1 primary would read 1 584 instead of 528).
   The build **collapses rows identical across every field** before summing. This is safe
   against genuine **boundary-split precincts** (e.g. 2023 general `MUR047`, which straddles
   a district line and appears as two *differing* partial rows) — those differ in votes or
   `times_cast`, so they are **not** collapsed and still sum correctly. There are **no
   "Total"/"Cumulative" precinct rows** in the file (all precincts are `MUR###`), so the
   only double-count risk was the triplication.

3. **2021 general recovered from the raw SOVC workbook.** In the long file the 2021 general
   exists only at the In-Person / Vote-By-Mail method split, and the small In-Person cells
   are **privacy-suppressed** (`****`): D2 100 % suppressed, D4 20/36 rows, Mayor 152/208
   rows. Summing only the surviving cells would publish a gross undercount (Mayor Hales
   would read **983**, not the true **6 108**). The un-redacted per-precinct **`Total`**
   sub-rows live in the raw county SOVC workbook, already mirrored **locally** (not
   re-downloaded):
   `~/Desktop/slco-election-archive/raw/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx`
   (Sheet24 Mayor, Sheet25 D2, Sheet26 D4). The 2021 general is parsed from those `Total`
   rows — same county SOVC provenance chain, just the totals the method-split destroys.
   This is the identical method the sibling `south_jordan` build documents for its own 2021.
   After recovery, **no race carries `suppressed_precincts=True`** and every by-precinct sum
   reconciles exactly to its by-candidate total (verified: 0 mismatches).

## The three CSVs

- **`murray_races.csv`** — one row per race (**21 races: 13 general + 8 primary** after the
  2026-07-17 SOVC-reparse appends; was 15), the
  25-column SCHEMA_SPEC superset (identical header to `south_jordan_races.csv`), incl.
  `total_first_choice_votes` (blank — Murray is plurality, **no RCV**), `winner`/
  `winner_votes`/`winner_pct`, `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`
  (= winner − runner-up), `registered_voters`/`ballots_cast`/`turnout_pct` (populated for
  all in-scope races), `uncontested`, `suppressed_precincts` (**False everywhere** after
  recovery), and `note` (special-election + any suppression flags).
- **`murray_results_by_candidate.csv`** — race × candidate (**47 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`murray_results_by_precinct.csv`** — precinct × candidate (**909 rows**), precinct IDs
  `MUR###`; `suppressed` column (all `False` in the final data).

## Name normalization

`norm_name()` normalizes each candidate **alongside** the verbatim value: collapses
whitespace, drops the leading `*` write-in mark, strips the `(NP)`/`(NON)` non-partisan
tag, and canonicalizes write-ins to `Write-in` / `Write-in (unresolved)`. Election names
are **UPPER-CASE**; to join elections ↔ council votes/roster, match on **person + year +
district** and normalize case/suffixes first.

## Winners (authoritative from this file) & the "Hales" cross-check

- **Mayor:** **BRETT A. HALES** won **2021** (6 108 vs Clark Bullen 4 369) and **2025**
  (6 490 vs Bruce E. Turner 4 005; also won the 2025 primary). No 2023 mayor race (B cycle).
- **Councilmember "Hales" vs Mayor Brett Hales — SAME PERSON.** The election record shows
  **Brett A. Hales** won **Murray City Council District 5** in **2011** and **2015**
  (general) — *below the 2020 floor, so those rows are not in these CSVs* — then moved up to
  **Mayor** in 2021 and 2025. There is **no separate sitting councilmember named Hales**;
  the roster's "Councilmember Hales" and "Mayor Brett Hales" are one individual who
  transitioned from the D5 council seat to the mayoralty. (Clark Bullen is the recurring
  foil — lost mayor to Hales in 2021, lost D3 in 2023, and finally won the **2025 D3 2-year
  special**.)
- In-scope district winners: **2021** D2 Pamela J. Cotter, D4 Diane Turner · **2023** D1
  Paul Pickett, D3 Rosalba Dominguez, D5 Adam Hock · **2025** D2 Pamela Jane Cotter,
  D4 Diane Turner (uncontested), D3-special Clark Bullen.

## Gaps / caveats

- **Below the 2020 floor:** the 2007–2017 Murray cycles exist in the county long file but
  remain out of scope. **The 2019 general (D1/D3/D5) + 2019 primary (D1/D3) ARE NOW INCLUDED**
  (hand-appended 2026-07-17 from the SOVC re-parse — see dated note). The Hales D5 council
  wins (2011/2015) still live only in the county file, not here.
- **2021 primaries (corrected 2026-07-17):** the **2021 MAYOR primary WAS held** (4 candidates —
  Hales 4,952 / Bullen 2,483 / Fitzgerald 413 / Teemsma 356; now added contest-grain from the
  election-night PDF). The **2021 D4 primary was NOT held** — three candidates filed but Galt
  withdrew pre-certification, leaving a field of 2 (straight to the general). No 2021 D2 primary
  (≤2 candidates). Likewise **no 2023 D5 primary** and **no 2025 D4 primary** (D4 2025 drew a
  single candidate → uncontested general, Diane Turner). This resolves the campaign-finance
  "2021 primary (Mayor ×4, D4 ×3)" review lead noted in the repo CLAUDE.md.
- **2021 method-level suppression** is fully resolved via the raw-workbook `Total` rows
  (above); if the county repo ever re-normalizes 2021 without suppression, the long-file
  path can replace the xlsx parse (delete the `SKIP` entry).
- `total_first_choice_votes` is blank everywhere — Murray did **not** join the 2021 RCV
  pilot; all races are plurality, vote-for-1.


## 2026-07-17 — SOVC-reparse rows appended (owner-approved, hand-edited)
Six rows were **hand-appended** to `murray_races.csv` from the 2026-07-16 SLCo raw-SOVC
re-parse (landed in `salt_lake_county/elections/`), the ONE sanctioned way audited election
files are edited (kearns precedent; dated backup in
`_backups/2026-07-17-audited-election-rows/murray/`):
- **2019 general** D1 (Kat Martinez d. Jake Pehrson 990-853), D3 (Rosalba Dominguez d. Adam
  Thompson 1050-883), D5 (Brett A. Hales UNOPPOSED 1445) — source `2019-11-05-general-election-sovc.xlsx`.
- **2019 primary** D1 (Martinez 647 / Pehrson 500 / Nicponski 321), D3 (Dominguez 565 /
  Thompson 449 / Brass 439) — source `2019-08-13-municipal-primary-sovc.xlsx`.
- **2021 MAYOR primary** (Hales 4,952 / Bullen 2,483 / Fitzgerald 413 / Teemsma 356) —
  **contest-grain** from the election-night report `2021-08-10-primary-election-results.pdf`
  (no precinct SOVC workbook exists for the 2021 primary); `registered_voters`/`ballots_cast`/
  `turnout_pct` are blank for that row by necessity.
- The 2019 district rows carry `registered_voters` (summed from the SOVC precinct rows,
  reproduces the sibling recovered-row method) but blank `ballots_cast`/`turnout_pct` (the
  method-split SOVC prints no clean contest total). All tallies re-verified twice vs the county
  layer. `clean_elections.py` will NOT regenerate these rows — re-append after any rebuild.
