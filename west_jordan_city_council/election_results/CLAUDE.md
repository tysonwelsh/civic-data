# West Jordan City — Election Results

Mayor + City Council races for **West Jordan City, Utah only**, municipal general
elections **2019, 2021, 2023, 2025** (the odd-year cycles seating members who serve
2020 onward). **13 races, 37 candidate rows, 1,978 precinct rows.**

West Jordan has a 7-member council: **4 district seats (1–4) + 3 at-large seats**, plus a
separately-elected **Mayor** (strong-mayor form, adopted at the 2019 election). Terms are
4 years, staggered. The stagger as it actually appears in the Salt Lake County SOVC files:

| cycle | contests on the ballot |
|---|---|
| **2019** | Mayor + Council **At-Large (1 seat, Vote for 1)** + Districts 1, 2, 3, 4 |
| **2021** | Council **At-Large (Vote for 3)** only |
| **2023** | Mayor + Districts 1, 2, 3, 4 |
| **2025** | Council **At-Large (Vote for 3)** only |

So in the modern era the **three at-large seats are filled together in one Vote-for-3
race in the "B" cycle (2021, 2025)** — the top-3 vote-getters win all three seats — while
**Mayor + the four district seats are the "A" cycle (2019, 2023)**.

**Note on the 2019 At-Large contest (flagged, not guessed):** 2019 was West Jordan's
*first* election under its new strong-mayor form of government (SL Tribune / West Jordan
Journal, Nov 2019). In 2019 the SOVC shows a **single** West Jordan At-Large council
contest (Vote for 1), won by Kelvin Green — not the grouped Vote-for-3 field seen in
2021/2025. This data records exactly what the county SOVC contains (one single-seat 2019
At-Large race); the shift to a single grouped Vote-for-3 at-large field appears from 2021
onward. This is documented from the source rather than reconciled to a theory of the
stagger.

## How this was built

**Re-pointed 2026-07-19 (root TODO.md Phase-2 follow-up): derives DIRECTLY from the county
canonical — no per-city raw SOVC copy.** The build reads
`salt_lake_county/elections/slco_municipal_results_long.csv` (precinct × candidate ×
vote-method) filtered to the West Jordan `WJD*`/"WEST JORDAN" general contests, and
`election_results_by_contest.csv` for the contest → office/district/**seats** map.

Originally this city parsed a redundant local copy of the raw SOVC `.xlsx` exports because
the archive's derived long file *dropped the un-suppressed per-precinct 2021 totals*. That
gap was **repaired in the county canonical's 2026-07-19 suppression-recovery**, so the
build was re-pointed and the four local `raw/*.xlsx` copies retired after verifying the
re-pointed build reproduces all three CSVs **byte-identically** (races + by_candidate +
by_precinct). The upstream provenance (county-clerk site + `~/Desktop/slco-election-archive`
mirror; the four cycles are `2019/2021/2023/2025` general) lives in the county module's
`raw/SOURCES.md`.

Per-precinct total rule reproduced from the canonical: use the `Total` vote_method row where
present (the family-C recovery emits a `Total` only where every method split was
privacy-suppressed); otherwise sum the non-`Total` method rows (2019/2025 single `ALL`; 2023
`In-Person` + `Vote by Mail`). Every per-precinct sum reconciles to the contest total.

Build script: **`build_wjordan_elections.py`** (in this folder). Reproducible:
`python3 build_wjordan_elections.py`. Only municipal **general** elections are output (the
seat-deciding contests); primaries exist in the canonical but are not emitted here.

## Contest mapping (`SheetNN` placeholder issue — RESOLVED)

As in the West Valley build, the 2021/2023/2025 county SOVC exports name every worksheet
`SheetNN` (`Sheet50`, `Sheet58`, …). The **real contest title is written in cell A2 (row
index 1)** of each sheet (e.g. `CITY OF WEST JORDAN COUNCIL DISTRICT 2 (Vote for 1)`). The
2019 file instead uses descriptive tab names (`WJD Mayor`, `WJD At-Large`, `WJD Council 1`)
and carries the title in **cell A1**. Mapping was resolved by reading those in-cell titles,
then cross-checking the candidate roster, the `WJD*` precincts, and the known winners.
Confirmed mapping:

| year | sheet TAB | in-cell title → canonical contest |
|---|---|---|
| 2019 | `WJD Mayor`     | WEST JORDAN CITY MAYOR → West Jordan City Mayor |
| 2019 | `WJD At-Large`  | WEST JORDAN CITY COUNCIL AT LARGE (Vote for 1) → ...Council At-Large |
| 2019 | `WJD Council 1` | WEST JORDAN CITY COUNCIL DISTRICT 1 → ...Council District 1 |
| 2019 | `WJD Council 2` | WEST JORDAN CITY COUNCIL DISTRICT 2 → ...Council District 2 |
| 2019 | `WJD Council 3` | WEST JORDAN CITY COUNCIL DISTRICT 3 → ...Council District 3 |
| 2019 | `WJD Council 4` | WEST JORDAN CITY COUNCIL DISTRICT 4 → ...Council District 4 |
| 2021 | `Sheet50` | CITY OF WEST JORDAN COUNCIL AT-LARGE (Vote for 3) → ...Council At-Large |
| 2023 | `Sheet47` | CITY OF WEST JORDAN MAYOR → West Jordan City Mayor |
| 2023 | `Sheet48` | CITY OF WEST JORDAN COUNCIL DISTRICT 1 → ...Council District 1 |
| 2023 | `Sheet49` | CITY OF WEST JORDAN COUNCIL DISTRICT 2 → ...Council District 2 |
| 2023 | `Sheet50` | CITY OF WEST JORDAN COUNCIL DISTRICT 3 → ...Council District 3 |
| 2023 | `Sheet51` | CITY OF WEST JORDAN COUNCIL DISTRICT 4 → ...Council District 4 |
| 2025 | `Sheet58` | WEST JORDAN CITY COUNCIL AT-LARGE (Vote for 3) → ...Council At-Large |

**Look-alike exclusion:** only `WJD*`-prefixed / "WEST JORDAN" contests were taken.
The same files contain `SJD*` **SOUTH JORDAN** contests ("CITY OF SOUTH JORDAN …") and
West Valley City contests — both excluded despite the shared "JORDAN" substring.

## Three raw layouts

- **2019** (`...historical-election-results...`): wide crosstab. Candidate names in row 2
  (index 1); each candidate block has Vote Centers / Vote By Mail / Early Voting / **Total
  Votes** columns; one row per precinct (`WJDnnn` in col 0). The parser reads each
  candidate's `Total Votes` column.
- **2021 / 2023** (Clarity/Dominion SOVC export): one value column per candidate; the
  count sits in the candidate's header column index. Each precinct is a block of
  `In Person` / `Vote By Mail` rows plus a per-precinct **`Total`** row — the parser reads
  the `Total` row. There is a second redundant "Precinct" column (and 2023 adds
  Undervotes/Overvotes columns) plus an interleaved percent column after each candidate;
  these are skipped by the non-candidate filter. `County - Total` = grand total.
- **2025**: the method breakout is collapsed, so the `WJDnnn` row itself holds the precinct
  totals — the parser reads candidate counts directly from that row.

## Privacy suppression — recovered

2021's **method-level** per-precinct rows (`In Person` / `Vote By Mail`) are privacy-
suppressed as `****` ("Insufficient Turnout to Protect Voter Privacy"). The archive's
derived `sovc_long.csv` kept only those rows for 2021 and discarded the un-suppressed
per-precinct `Total` rows. **Parsing the raw spreadsheet directly recovers the full
un-suppressed per-precinct candidate counts** from the `Total` rows. **Every per-precinct
sum reconciles exactly to the official `County - Total` grand total — 0 mismatches, 0
suppressed rows across all 13 contests** (verified programmatically).

## Vote-for-N at-large modeling

The 2021 and 2025 At-Large races elect **3 seats** in one field (`Vote for 3`); the top-3
vote-getters win. In `west_jordan_results_by_candidate.csv`, `is_winner=True` for `rank<=3`
(three winners per race). In `west_jordan_races.csv`, the multi-winner race row records the
**seat-deciding boundary**: `winner` = the lowest winning seat (rank 3), `runner_up` =
the first loser (rank 4), and `margin` = the rank-3-vs-rank-4 gap (the seat that actually
flipped). `total_votes` is inflated by Vote-for-3, so `pct` is each candidate's share of
all council votes cast, **not** turnout. Mayor and the district seats stay single-winner
(`n_seats=1`, `is_winner=True` for rank 1 only). 2019's At-Large was single-seat (Vote
for 1), so it is modeled `n_seats=1`.

## Name normalization

Candidate names in the files are UPPER-CASE with a `(NP )` non-partisan suffix and
write-in tags. `norm_name` collapses whitespace, strips `(NP)`, lowercases `WRITE-IN` →
`Write-in`, maps `Qualified Write In` → `(Write-in)` and `Unresolved Write-In` →
`Write-in (unresolved)`. Names are otherwise kept verbatim from the ballot
(e.g. `CHRISTOPHER M MCCONNEHEY` 2019 vs `CHRIS MCCONNEHEY` 2025 — same person across
years; not merged, since the CSVs key on year × contest). `n_candidates` counts real
ballot lines; a 0-vote `Write-in (unresolved)` aggregate bucket is excluded from the count
(it still appears as a 0-vote row for completeness).

## Winners (all verified against external sources)

| year | contest | winner(s) | win/seat % | runner-up / first loser | margin |
|---|---|---|---|---|---|
| 2019 | Mayor | Dirk Burton | 52.13% | Jim Riding | 589 |
| 2019 | At-Large (1 seat) | Kelvin Green | 46.77% | Mikey Smith | 1,893 |
| 2019 | District 1 | Christopher M McConnehey | 50.68% | Marilyn Richards | 54 |
| 2019 | District 2 | Melissa Worthen | 81.92% | John Price | 2,458 |
| 2019 | District 3 | Zach Jacob | 57.47% | Amy L Martz | 355 |
| 2019 | District 4 | David Pack | 57.19% | Pamela Berry | 470 |
| 2021 | At-Large (3 seats) | Kayleen Whitelock, Kelvin Green, Pamela Bloom | seat3 19.70% | Chad Lamb (4th) | 326 (seat 3) |
| 2023 | Mayor | Dirk Burton | 60.47% | Kayleen Whitelock | 3,025 |
| 2023 | District 1 | Chad Lamb | 64.54% | Rulon Green | 1,089 |
| 2023 | District 2 | Bob Bedore | 54.17% | Gary Leany | 312 |
| 2023 | District 3 | Zach Jacob | 65.81% | Sterling Morris | 919 |
| 2023 | District 4 | Kent Shelton | 57.19% | David F. Pack | 555 |
| 2025 | At-Large (3 seats) | Kayleen Whitelock, Annette Harris, Jessica Wignall | seat3 16.65% | Sergio Sotelo (4th) | 79 (seat 3) |

External cross-check sources:
- **2025 At-Large:** West Jordan City newsroom ("Your Vote, Your Council: West Jordan's
  At-Large Winners," Dec 2025) and Hoodline confirm **Annette Harris, Kayleen Whitelock,
  Jessica Wignall** as the three winners — exactly the top-3 here. Sotelo finished 4th by
  79 votes (the seat-3 margin in this data).
- **2023:** KSL municipal-results roundup and SL Tribune confirm Burton (Mayor), Lamb (D1),
  Bedore (D2), Jacob (D3), Shelton (D4) as winners. (KSL's election-night totals are lower
  than this data because this is the **certified canvass** SOVC, not the election-night
  count; winners and order match.)
- **2021 At-Large:** West Jordan Journal ("At-large council seats filled with two incumbents,
  one newcomer") confirms Whitelock + Green (incumbents) and Bloom (newcomer) won, with
  **Bloom outpacing Chad Lamb by 326 votes** for the final seat — matches the seat-3 margin
  here exactly.
- **2019:** SL Tribune ("incumbent West Jordan…", Nov 2019) and West Jordan Journal confirm
  **Dirk Burton** beat incumbent **Jim Riding** for Mayor (first strong-mayor election), and
  **Kelvin Green** won the At-Large seat (~47%, Smith 2nd) — both match this data.

The current council (per recon §2, June 2026) is fully consistent: Mayor Burton, D1 Lamb,
D2 Bedore, D3 Jacob, D4 Shelton, At-Large Harris + Whitelock + Wignall (all seated by the
2025 grouped at-large race; Whitelock also won at-large in 2021).

## Unresolved / caveats

- **None unresolved.** All 13 contests are confidently mapped and winner-verified.
- The 2019 At-Large single-seat vs the later grouped Vote-for-3 at-large field is a genuine
  structural feature of the source (the 2019 strong-mayor transition), documented above —
  not a parsing artifact.
- Per-precinct `votes` are blank with `suppressed=True` only where genuinely unavailable;
  in practice **0 precinct rows are suppressed** (the raw `Total`/precinct rows are not
  privacy-redacted), and every precinct sum reconciles to the County-Total.
- Precincts use the `WJDnnn` code, which equals the GIS `PrecinctID` join key in
  `~/Desktop/slco-election-archive/geo/` (UGRC VistaBallotAreas, CountyID 18) for geo
  analysis. (The archive GeoJSON has the documented EPSG:26912-tagged-as-4326 CRS bug —
  reproject before point-in-polygon; see lessons_learned.)

## Schema

- `west_jordan_races.csv` — one row per race:
  `year, election_type, office, district, contest, n_seats, n_candidates, total_votes,
  winner, winner_votes, winner_pct, runner_up, runner_up_votes, margin_votes, margin_pct`
  (`district` = district number for district seats, `At-Large` for at-large, blank for
  Mayor; `n_seats` = seats elected in the contest, 3 for the grouped at-large races).
- `west_jordan_results_by_candidate.csv` — race × candidate:
  `year, election_type, office, district, contest, candidate, votes, pct, rank, is_winner`
  (`is_winner=True` for `rank <= n_seats`).
- `west_jordan_results_by_precinct.csv` — precinct × candidate (geo):
  `year, election_type, office, district, contest, precinct, candidate, votes, suppressed`
