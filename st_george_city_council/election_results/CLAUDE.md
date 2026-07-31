# St. George (Utah) Municipal Election Results

Washington County (UGRC CountyID **27**) municipal election files, filtered to
**St. George City Mayor + City Council races only** and normalized for analysis.
Covers the municipal cycles **2019, 2021, 2023, 2025** (members seated 2020+).
Raw county files in `raw/` are the immutable source of truth and are never edited.

> **Disambiguation:** This is St. George, **UTAH**. NOT St. George, Louisiana
> (which has a district-based council). St. George UT is entirely **at-large**.

## Pipeline

```
raw/washco-*-results-export.csv (+ municipal-primary.csv)   county-wide precinct x candidate crosstabs (SOURCE OF TRUTH)
clean_elections.py                                           filter to St George mayor+council, normalize, rank, aggregate
  -> st_george_results_by_precinct.csv    filtered precinct x candidate (geographic analysis)
  -> st_george_results_by_candidate.csv   race x candidate: votes, pct, rank, is_winner
  -> st_george_races.csv                  ONE ROW PER RACE: winner, runner-up, margin, turnout
```

Regenerate: `python3 clean_elections.py`

## Sources used (all downloaded verbatim into `raw/`)

Washington County Clerk previous-election-results index:
`https://www.washco.utah.gov/departments/clerk/elections/previous-election-results/`
Files hosted on `outpost.washco.utah.gov`:

| Cycle | Raw file | Source URL |
|---|---|---|
| 2019 Nov general | `washco-2019-general-municipal-export.csv` | `.../elections/2019/11/2019-general-municipal-export.csv` |
| 2021 Aug primary | `washco-20210810-municipal-primary.csv` | `.../elections/2021/08/washco_elections_20210810_OFFICIAL_municipal-primary.csv` |
| 2021 Nov general | `washco-20211102-results-export.csv` | `.../elections/2021/11/washco-election-20211102-results-export.csv` |
| 2023 Sep primary | `washco-202309-results-export.csv` | `.../elections/2023/09/washco-election-202309-results-export.csv` |
| 2023 Nov general | `washco-20231121-results-export.csv` | `.../elections/2023/11/washco-election-20231121-results-export.csv` |
| 2025 Aug primary | `washco-20250812-results-export.csv` | `.../elections/2025/08/washco-election-20250812-results-export.csv` |
| 2025 Nov general | `washco-20251104-results-export.csv` | `.../elections/2025/11/washco-election-20251104-results-export.csv` |

Precinct-detail PDFs were also downloaded as a secondary reference / integrity
check (`raw/washco-*-results-precinct.pdf`, plus the 2021 Aug precinct summary).
The CSV exports already carry full precinct granularity, so the derived CSVs are
built from the CSV exports, not the PDFs. The Utah state portal
(`electionresults.utah.gov`, Enhanced Voting) was **not needed** — the county CSVs
are complete and authoritative for all four cycles.

## Raw file format

Each county CSV is a county-wide wide crosstab:
- row 0 = contest name, repeated once per candidate column (e.g. `St George City
  Council` appears in 4 adjacent columns when 4 candidates run).
- row 1 = party — all `NON` (municipal races are non-partisan).
- row 2 = candidate name (incl. pseudo-columns `OVER VOTES`, `UNDER VOTES`,
  `Withdrawn`, `Disqualified`, `Cancelled`, `Write-in`).
- rows 3.. = one row per precinct; cols are `COUNTY NUMBER, PRECINCT CODE,
  PRECINCT NAME, REGISTERED VOTERS TOTAL, BALLOTS CAST TOTAL, BALLOTS CAST BLANK`
  then one integer per candidate column. The final row (`PRECINCT CODE = ZZZ`,
  `PRECINCT NAME = COUNTY TOTALS`) is the certified grand total.

## Filtering + normalization

- Keep only contests whose name contains `St George` / `St. George` **and**
  excludes `Bond` (the 2023 `St George City Special Bond Election` is dropped —
  it's a ballot measure, not a council race). All other Washington County
  municipalities (Washington City, Hurricane, Ivins, Santa Clara, La Verkin,
  Toquerville, Springdale, Apple Valley, Hildale, Enterprise, Leeds, Rockville,
  Virgin, etc.) and county/state/SSD contests are excluded.
- Contest-name variants across years: `St George Mayor`, `St George City Mayor`,
  and `St George City Council`. Collapsed to canonical `St George Mayor` /
  `St George City Council`.
- Pseudo-candidates `OVER VOTES`, `UNDER VOTES`, `Withdrawn`, `Withdrew`,
  `Disqualified`, `Cancelled` are dropped (not real candidates). `Write-in` is
  kept where it appears as a named column.
- Race totals are taken from the certified `COUNTY TOTALS` (ZZZ) row; the
  per-precinct rows sum **exactly** to those totals (verified for all 11 races).

## AT-LARGE MODELING DECISION (important)

St. George elects every seat **citywide — no districts**. City Council does **not**
run as separate per-seat contests; it runs as a **single multi-winner field**:
all candidates appear in one `St George City Council` contest and the **top N
vote-getters win the N open seats** that cycle. The official county summary PDFs
label this `Vote For N` (confirmed: 2019 = 3, 2021 = 2, 2023 = 3, 2025 = 2).

Consequences for the schema:
- `district` column = `At-Large` for all council races (empty for Mayor, a
  conventional single-winner race).
- A council "race" has **multiple winners**. In `st_george_results_by_candidate.csv`,
  `is_winner = Y` for `rank <= N` (general) — i.e. every candidate who won a seat.
- `total_votes` for a council race is the **sum of all candidate votes**, which is
  larger than ballots cast because each voter may vote for up to N candidates
  (vote-for-N). `pct` is therefore each candidate's **share of all council votes
  cast**, the standard convention for multi-winner at-large fields. (Over/under
  votes are excluded from the denominator.)
- In `st_george_races.csv` (one row per race), for a multi-winner council field:
  `winner` = the top vote-getter; `runner_up` = the candidate at **rank N+1** (the
  first loser — the candidate who just missed the last seat); `margin_votes` /
  `margin_pct` = rank-N winner minus rank-(N+1) loser, i.e. the margin that
  **decided the final seat**. This is the analytically meaningful "closeness" of an
  at-large race. (For Mayor, runner-up/margin are the usual 1st-vs-2nd values.)

### Primaries
Municipal primaries (August/September, held when a contest has more candidates than
~2x the seats) narrow the field. The general winner-takes-top-N logic generalizes:
the **top 2N advance** to the general. In primary rows of
`st_george_results_by_candidate.csv`, `is_winner = Y` means **advanced to the
general** (`rank <= 2N`; mayor primary advances top 2). The primary `runner_up` /
`margin` in `st_george_races.csv` describe the **advancement cutoff** (rank 2N vs
2N+1), not a seat.

## Coverage (11 races)

| Year | Type | Office | Seats (Vote For) | Winners / advancers |
|---|---|---|---|---|
| 2019 | general | Council | 3 | Hughes, McArthur, Larkin |
| 2021 | primary | Mayor | 1 (adv 2) | Randall, Hughes advance |
| 2021 | primary | Council | 2 (adv 4) | Tanner, Curtis, Aldred, Larsen advance |
| 2021 | general | Mayor | 1 | **Michele Randall** |
| 2021 | general | Council | 2 | Larsen, Tanner |
| 2023 | primary | Council | 3 (adv 6) | Larkin, Hughes, Kemp, Smith, Bennett, McArthur advance |
| 2023 | general | Council | 3 | Kemp, Hughes, Larkin |
| 2025 | primary | Mayor | 1 (adv 2) | Randall, Hughes advance |
| 2025 | primary | Council | 2 (adv 4) | Tanner, Larsen, Leavitt, Aldred advance |
| 2025 | general | Mayor | 1 | **Jimmie Hughes** (beat incumbent Randall) |
| 2025 | general | Council | 2 | Larsen, Tanner |

No mayoral race in 2019 or 2023 (mayor is a 4-yr term elected 2021, 2025).

## Cross-check (external corroboration)

Winners independently confirmed against:
- **Official county summary PDF** (`pdftotext` of
  `washco-election-20251104-results-summary.pdf`): 2025 Mayor Hughes 12,334 /
  Randall 9,859; Council "Vote For 2" Larsen 12,013, Tanner 11,397 — matches the
  derived CSVs exactly.
- **St. George News** (`stgeorgeutah.com`): 2019 council "Vote For 3" won by
  Hughes, Larkin, McArthur.
- **Ballotpedia / KUER / St. George News** corroborate every winner and seat count
  for all four cycles (2019 Hughes/McArthur/Larkin; 2021 mayor Randall, council
  Larsen/Tanner; 2023 Kemp/Hughes/Larkin; 2025 mayor Hughes, council Larsen/Tanner).
- Recon facts: Randall mayor 2021–2025; Hughes won mayor Nov 2025; Larsen & Tanner
  re-elected 2025; Kemp & Larkin won council 2023. All consistent with the data.

**Vote-total note:** some news/secondary sources report slightly lower mayoral
totals (e.g. 2025 Hughes 10,287 / Randall 8,467; 2021 Randall 10,207 / Hughes
8,040) — these appear to be election-night / partial-canvass figures. This repo uses
the **certified county `COUNTY TOTALS`** (2025 Hughes 12,334 / Randall 9,859; 2021
Randall 11,614 / Hughes 9,434), independently verified against the official county
summary PDF via `pdftotext`. Certified county totals are authoritative; winner
identities and margins agree across all sources.

## Connecting to the rest of the repo

Elections are point-in-time events (odd-year Nov) — they do not belong in weekly
`../weeks/` bundles. They join to the rest of the repo via **person + year**: a race
winner becomes a councilmember whose roll-call votes live in
`../meeting_minutes/all_votes.csv`. Candidate names here are UPPER-CASE (e.g.
`DANNIELLE LARKIN`) vs mixed-case in votes data; normalize case before joining.
Because the city is **at-large**, there is no precinct->district mapping (it's
identity): every St. George precinct elects the same 6 citywide officials.

## Gaps / caveats

- None for the four target cycles — all obtained from authoritative county exports
  and reconcile to certified totals.
- 2019 has **no county summary PDF** posted (only the CSV export). Seat count (3)
  and winners confirmed via St. George News rather than a county summary PDF.
- Vote-for-N inflates council `total_votes`; see the at-large modeling note — `pct`
  is share-of-council-votes, not turnout. Use Mayor races or `BALLOTS CAST TOTAL`
  in the raw files for turnout.

## Don't
- Don't edit the raw `washco-*.csv` files.
- Don't treat `OVER VOTES`/`UNDER VOTES`/`Withdrawn` as candidates.
- Don't read a council race as single-winner — top N win (see at-large model).
- Don't match a neighboring Washington County city (Washington City, Hurricane,
  Santa Clara, Ivins, etc.) as St. George.
