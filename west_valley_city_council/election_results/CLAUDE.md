# West Valley City — Election Results

Mayor + City Council races for **West Valley City, Utah only**, municipal general
elections **2019, 2021, 2023, 2025** (the odd-year cycles seating members who serve
2020 onward). 14 races, 34 candidate rows, 1,479 precinct rows.

WVC has a 7-member council: **4 district seats (1–4) + 2 at-large seats**, plus a
separately-elected **Mayor**. Terms are 4 years, staggered:
- **2019** cycle: At-Large, District 1, District 3 (members seated Jan 2020).
- **2021** cycle: Mayor, At-Large, District 2, District 4.
- **2023** cycle: At-Large, District 1, District 3.
- **2025** cycle: Mayor, At-Large, District 2, District 4.

(The District-1/3 + one At-Large group and the Mayor + District-2/4 + other At-Large
group alternate every two years; next WVC election 2027 = At-Large, D1, D3.)

## How this was built

**Re-pointed 2026-07-19 (root TODO.md Phase-2 follow-up): derives DIRECTLY from the county
canonical — no per-city raw SOVC copy.** The build reads
`salt_lake_county/elections/slco_municipal_results_long.csv` (precinct × candidate ×
vote-method) filtered to the West Valley `WVC*`/"WEST VALLEY" general contests, and
`election_results_by_contest.csv` for the contest → office/district map.

Originally this city parsed a redundant local copy of the raw SOVC `.xlsx` exports because
the archive's derived long file *had dropped the un-suppressed per-precinct 2021 totals*.
That gap was **repaired in the county canonical's 2026-07-19 suppression-recovery**, so the
build was re-pointed and the four local `raw/*.xlsx` copies retired after verifying the
re-pointed build reproduces all three CSVs **byte-identically** (races + by_candidate +
by_precinct). The upstream provenance (county-clerk site + `~/Desktop/slco-election-archive`
mirror; the four cycles are `2019/2021/2023/2025` general) lives in the county module's
`raw/SOURCES.md`.

Per-precinct total rule reproduced from the canonical: use the `Total` vote_method row where
present (the family-C recovery emits a `Total` only where every method split was
privacy-suppressed); otherwise sum the non-`Total` method rows (2019/2025 single `ALL`; 2023
`In-Person` + `Vote by Mail`). Every per-precinct sum reconciles to the contest total.

Build script: **`build_wvc_elections.py`** (in this folder). Reproducible:
`python3 build_wvc_elections.py`. Only municipal **general** elections are output (the
seat-deciding contests); primaries exist in the canonical but are not emitted here.

## The `SheetNN` placeholder issue — RESOLVED

The recon flagged that 2021/2023/2025 WVC contests appear under `SheetNN` placeholder
tab names. That is true of the **Excel sheet TAB names** (the county's SOVC export
tabs each worksheet as `Sheet51`, `Sheet52`, …). But the **real contest title is
written in cell A2 (row index 1) of each sheet** (e.g. `WEST VALLEY CITY COUNCIL
DISTRICT 2 (Vote for 1)`). So the remapping was resolved by reading that in-cell
title, then cross-checking the candidate roster, the WVC precincts, and the known
winners. Confirmed mapping:

| year | sheet TAB | in-cell A2 title → canonical contest |
|---|---|---|
| 2021 | Sheet51 | WEST VALLEY CITY MAYOR → West Valley City Mayor |
| 2021 | Sheet52 | WEST VALLEY CITY COUNCIL AT-LARGE → ...Council At-Large |
| 2021 | Sheet53 | WEST VALLEY CITY COUNCIL DISTRICT 2 → ...Council District 2 |
| 2021 | Sheet54 | WEST VALLEY CITY COUNCIL DISTRICT 4 → ...Council District 4 |
| 2023 | Sheet52 | WEST VALLEY CITY COUNCIL AT-LARGE → ...Council At-Large |
| 2023 | Sheet53 | WEST VALLEY CITY COUNCIL DISTRICT 1 → ...Council District 1 |
| 2023 | Sheet54 | WEST VALLEY CITY COUNCIL DISTRICT 3 → ...Council District 3 |
| 2025 | Sheet57 | WEST VALLEY CITY MAYOR → West Valley City Mayor |
| 2025 | Sheet59 | WEST VALLEY CITY COUNCIL AT-LARGE → ...Council At-Large |
| 2025 | Sheet60 | WEST VALLEY CITY COUNCIL DISTRICT 2 → ...Council District 2 |
| 2025 | Sheet61 | WEST VALLEY CITY COUNCIL DISTRICT 4 → ...Council District 4 |

(2019 uses descriptive tab names — `WVC At-Large`, `WVC Council 1`, `WVC Council 3` —
not SheetNN, and a different wide crosstab layout, handled separately by the parser.)

Note: the archive's pre-derived `data/sovc_long.csv` / `municipal_results_long.csv`
already carried correct contest **names** for 2021/2023/2025 (a prior pass had read
A2), but it had **dropped the per-precinct totals**: 2021's method-level rows were
privacy-suppressed (`****`) and the normalizer kept only those, discarding the
un-suppressed per-precinct `Total` rows. Parsing the raw spreadsheets directly recovers
the full, un-suppressed per-precinct candidate counts. Every per-precinct sum here
reconciles exactly to the official `County - Total` grand total.

## Two raw layouts

- **2019** (`...historical-election-results...`): wide crosstab. Candidate names in
  row 2; each candidate has Vote Centers / Vote By Mail / Early Voting / **Total Votes**
  columns; one row per precinct. Parser reads each candidate's `Total Votes` column.
- **2021 / 2023 / 2025** (modern Clarity/Dominion SOVC export): one value column per
  candidate (the count sits in the same column index as the candidate's header name).
  - 2021 & 2023: each precinct is a block of `In Person` / `Vote By Mail` rows plus a
    per-precinct **`Total`** row — the parser reads the `Total` row.
  - 2025: the method breakout is collapsed, so the `WVCnnn` row itself holds the
    precinct totals — the parser reads candidate counts directly from that row.

## Name normalization

Candidate names in the files are UPPER-CASE with a `(NP )` non-partisan suffix and
write-in tags. Normalization (`norm_name` in the build script): collapse whitespace,
strip `(NP)`, convert `Qualified Write In` → `(Write-in)`, and `Unresolved Write-In`
→ `Write-in (unresolved)`. Names are otherwise kept verbatim from the ballot
(e.g. `SCOTT HARMON` in 2021 vs `SCOTT L. HARMON` in 2025 — same person, different
ballot rendering across years; not merged, since the CSVs key on year × contest).

`n_candidates` counts real ballot lines; the `Unresolved Write-In` aggregate bucket is
excluded from the count when it has 0 votes (it appears as a 0-vote candidate row in
`results_by_candidate` for completeness but is not a real contestant).

## Winners (all verified against external sources)

| year | contest | winner | win% | runner-up | margin |
|---|---|---|---|---|---|
| 2019 | Council At-Large | Don Christensen | 56.66% | Darrell R Curtis | 1,315 |
| 2019 | Council District 1 | Tom Huynh | 65.64% | Christiana Tavo | 507 |
| 2019 | Council District 3 | Karen Lang | 70.32% | Kaletta L. Lynch | 1,072 |
| 2021 | Mayor | Karen Lang | 58.54% | Steve Buhler | 1,933 |
| 2021 | Council At-Large | Lars Nordfelt | 59.59% | Jim Vesock | 2,696 |
| 2021 | Council District 2 | Scott Harmon | 59.39% | Chris Bell | 636 |
| 2021 | Council District 4 | Jake Fitisemanu Jr | 53.45% | Darrell R. Curtis | 227 |
| 2023 | Council At-Large | Don Christensen | 58.41% | Sophia Hawes-Tingey | 1,931 |
| 2023 | Council District 1 | Tom Huynh | 54.52% | Marni Lefevre | 188 |
| 2023 | Council District 3 | Will Whetstone | 56.57% | Heidi Roggenbuck | 358 |
| 2025 | Mayor | Karen Lang | 75.40% | June Freeman Hesleph | 5,974 |
| 2025 | Council At-Large | Lars Nordfelt | 54.82% | Heidi Roggenbuck | 1,281 |
| 2025 | Council District 2 | Scott L. Harmon | 61.53% | Danny George Jr | 825 |
| 2025 | Council District 4 | Cindy Wood | 63.51% | Amitonu Wesley Amosa | 949 |

External cross-check sources:
- **2025**: ABC4 + Salt Lake Tribune + WVC certified results — winners and exact vote
  counts (Lang 8,866 / Hesleph 2,892; Nordfelt 6,333 / Roggenbuck 5,052) match this data
  precisely. (Ryan Mahoney was a qualified write-in, 167 votes; no At-Large coin-toss
  runoff occurred — Nordfelt won outright by 1,281 votes.)
- **2023**: West Valley Journal ("Incumbents rule West Valley City Council election")
  and electionresults.utah.gov — Christensen ~55%, Huynh 55%/45%, Whetstone 57%/43% all
  consistent with this data.
- **2021**: Salt Lake Tribune / Deseret News — Lang ~58.5% Mayor, Nordfelt 59% At-Large,
  Harmon (D2), Fitisemanu (D4) all match.
- **2019**: West Valley Journal ("Reelected West Valley City Council members begin new
  terms," sworn in Jan 7 2020) confirms Huynh, Lang (D3), Christensen (At-Large) as the
  three 2019 winners.

The current council (per recon §2, June 2026) is fully consistent with these results:
Mayor Lang, At-Large Nordfelt + Christensen, D1 Huynh, D2 Harmon, D3 Whetstone,
D4 Wood. (Christensen holds the At-Large seat last won in 2023; Nordfelt the At-Large
seat won in 2021 and again 2025.)

## Unresolved / caveats

- **None unresolved.** All 14 contests are confidently mapped and winner-verified.
- The `2025-11-04` general spreadsheet copied here is the canvassed official report
  dated 2025-11-18 (filename in the archive was `2025-general-election-statementof
  votescastrpt.xlsx`; a separate `final_official_statementofvotescastrpt_20250826.xlsx`
  in the archive is the **2024** general, not 2025, and was NOT used).
- Per-precinct `votes` are blank with `suppressed=True` only where a value was genuinely
  unavailable; in practice every WVC precinct total is present (0 suppressed rows) because
  the raw `Total` rows are not privacy-redacted.
- Precincts use the `WVCnnn` code, which equals the GIS `PrecinctID` join key in
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.gpkg` (for geo analysis).
- Look-alike exclusion: only `WVC*`-prefixed / "WEST VALLEY CITY" contests were taken.
  Neighboring West Jordan (`WJD`) and West Haven were excluded.

## Schema

- `west_valley_races.csv` — one row per race:
  `year, election_type, office, district, contest, n_candidates, total_votes, winner,
  winner_votes, winner_pct, runner_up, runner_up_votes, margin_votes, margin_pct`
- `west_valley_results_by_candidate.csv` — race × candidate:
  `year, election_type, office, district, contest, candidate, votes, pct, rank, is_winner`
- `west_valley_results_by_precinct.csv` — precinct × candidate (geo):
  `year, election_type, office, district, contest, precinct, candidate, votes, suppressed`
