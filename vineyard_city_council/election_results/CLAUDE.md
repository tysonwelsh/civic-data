# Vineyard (Utah) Municipal Election Results

Utah County (UGRC CountyID **25**) municipal election results, filtered to **Vineyard
City Mayor + City Council races only** and normalized for analysis. Covers the municipal
cycles **2019, 2021, 2023, 2025** (members seated 2020+). Vineyard is a small, fast-growing
Utah County city: **Mayor + at-large council** (no districts), 4-member council expanding
to a 5-member council (six-member-council form) effective Jan 2026.

> **Disambiguation:** Vineyard, **UTAH** (Utah County, on the former Geneva Steel site by
> Utah Lake). Not to be confused with Vineyard, neighboring Orem/Lindon precincts, or any
> "Vineyard" elsewhere. All contests here carry the literal name `Vineyard Mayor` /
> `Vineyard City Council`.

## TWO election methods — the central branch

Vineyard's results require handling **two completely different tabulation methods**:

| Cycle | Method | Why | Source of the numbers |
|---|---|---|---|
| **2019** | **Ranked-Choice Voting (RCV)** | Vineyard + Payson were Utah's first RCV-pilot cities | rcvis.com round tabulations |
| **2021** | **Ranked-Choice Voting (RCV)** | RCV pilot continued | rcvis.com round tabulations |
| **2023** | **Ranked-Choice Voting (RCV)** | RCV pilot continued | rcvis.com round tabulations |
| **2025** | **Plurality (vote-for-N) + Aug primary** | Vineyard voted **April 2025 to drop RCV** before the pilot sunset (Jan 1 2026) | Utah County / Enhanced Voting state portal JSON |

`election_type` encodes the branch: `municipal general (RCV)` vs `municipal general` /
`municipal primary` (plurality).

## How RCV (2019/2021/2023) is modeled

Vineyard ran **sequential multi-seat RCV**: a *separate single-winner tabulation per open
seat*, with each seat's winner removed from the ballot before the next seat is tabulated.
rcvis.com therefore hosts **one visualization per seat** (e.g. the 2019 "Seat 1" tabulation
elects Welsh from the full 7-candidate field; the "Seat 2" tabulation re-runs the remaining
6 and elects Flake).

We collapse each year's council contest into **ONE multi-winner `Vineyard City Council`
"At-Large" race** with N winners (mirrors the at-large model used for St. George), and model:

- **`vineyard_results_by_candidate.csv`** — one row per candidate. `votes` / `pct` / `rank`
  use the **full-field round-1 first-choice** totals (the count where the entire field is
  present — i.e. the first/full seat tabulation). `is_winner = Y` for every candidate who
  won a seat that cycle (so a 2-seat RCV council race has **two** `Y` rows).
  `final_round_votes` = the candidate's total in the round their seat was decided
  (final-round figure), blank for non-winners.
- **`vineyard_races.csv`** (one row per race) — for a multi-winner RCV council race the
  `winner` / `winner_votes` / `runner_up` / `margin_*` columns describe the
  **seat-deciding contest**: the *last open seat's final round* (winner vs the candidate
  eliminated/trailing in that final round). This keeps `winner_votes`, `runner_up_votes`,
  and `margin_*` internally consistent — all four are final-round figures from one
  tabulation. `winner_pct` = the seat-deciding winner's share of that final round's
  two-candidate split. `total_votes` = round-1 first-choice ballots cast (full field).
  - **"Margin" for an RCV race = the final-round margin of the seat-deciding contest**,
    not a first-choice margin. Documented here so the number is not misread.
- The **2021 Mayor** race was *also* RCV but **single-winner**: Julie Fullmer won outright
  on the **first count** (86.64% majority, no elimination rounds). Modeled as a normal
  single-winner race; `final_round_votes` = first-choice for the winner since round 1 = final.

### RCV winners per cycle (cross-checked — see below)
- **2019 Council** (2 seats, 7 candidates): **Cristy Welsh** (Seat 1, R6 majority) &
  **G. Tyce Flake** (Seat 2, R5). First-choice leaders: Welsh 347, Flake 277.
- **2021 Mayor**: **Julie Fullmer** (1,329 / 86.64%, R1 majority) over Marc Brimhall (132),
  Maria Guadalupe Cane (73).
- **2021 Council** (2 seats, 4 candidates): **Mardi Sifuentes** (Seat 1, R2) &
  **Amber Rasmussen** (Seat 2, R3).
- **2023 Council** (2 seats, 7 candidates): **Sara Cameron** (R1 majority, 907) &
  **Jacob Holdaway** (other seat, R6, 1,097).

## How plurality / vote-for-N (2025) is modeled — at-large

In 2025 Vineyard reverted to a normal plurality election. Council is **at-large,
vote-for-N**: all candidates run in one `Vineyard City Council` contest and the **top N
vote-getters win the N open seats**.

- **2025 General**: `Vineyard Mayor` (Vote for 1, single-winner) and `Vineyard City
  Council` (**Vote for 3** — 3 seats up; the new 5th seat staggered so one of the three is
  a 2-year term assigned by lot).
- **2025 Primary** (Aug 12 2025): **City Council only** (8 candidates → top 6 advance to the
  general). **No mayor primary** (only 2 mayoral candidates, so none was required).
- `district = At-Large` for council, empty for Mayor.
- In `vineyard_results_by_candidate.csv`, council `is_winner = Y` for `rank <= N`
  (general: N=3; primary: advancing top 2N=6). For Mayor, `is_winner = Y` for rank 1.
- `total_votes` for a vote-for-N council race is the **sum of all candidate votes**, larger
  than ballots cast because each voter may vote for up to N candidates. `pct` is therefore
  each candidate's **share of all council votes cast**, NOT turnout. Use the Mayor race for
  a turnout-like denominator.
- In `vineyard_races.csv` for a vote-for-N council field: `winner` = top vote-getter;
  `runner_up` = the candidate at **rank N+1** (first loser, just missed the last seat);
  `margin_*` = rank-N winner minus rank-(N+1) loser — the **seat-deciding margin**.

### 2025 winners (certified Nov 18 2025)
- **Mayor: Zack Stratton** (1,417 / 54.71%) over Mardi Sifuentes (1,173).
- **Council (Vote for 3): Parker McCumber** (1,460), **Jacob Wood** (1,389),
  **David Lauret** (1,348). Losers: Ezra Nair (1,002), Brett Clawson (998), Caden Rhoton (861).
  McCumber drew the **2-year term by lot** (staggering the new 5th seat). (Ezra Nair was
  later *appointed* Nov 2025 to fill Sara Cameron's vacated seat — an appointment, not an
  election, so not in this data.)

## Sources used (all mirrored verbatim into `raw/`)

**RCV detail (2019/2021/2023) — rcvis.com round-by-round tabulations:**

| File in raw/ | rcvis source | Covers |
|---|---|---|
| `rcvis_2019_seat1.html` | `rcvis.com/visualize=vineyard-seat-1-updated-2019-11-19_11-20-30json` | 2019 Council, full 7-candidate field, Welsh wins R6 |
| `rcvis_2019_seat2.html` | `rcvis.com/visualize=vineyard-seat-2-2019-11-19_11-20-30_summary_2json` | 2019 Council, Welsh removed, Flake wins R5 |
| `rcvis_2021_mayor.html` | `rcvis.com/v/21g_vi_m_u4` | 2021 Mayor, Fullmer R1 majority |
| `rcvis_2021_seat1_sifuentes.html` | `rcvis.com/v/21g_vi_cc_1_u4` | 2021 Council seat, Sifuentes wins R2 |
| `rcvis_2021_seat2_rasmussen.html` | `rcvis.com/v/21g_vi_cc_2_u2` | 2021 Council seat, Rasmussen wins R3 |
| `rcvis_2023_holdaway.html` | `rcvis.com/v/2023-vineyard-city-council-6` | 2023 Council, full field, Holdaway wins R6 |
| `rcvis_2023_cameron.html` | `rcvis.com/v/2023-vineyard-city-council-7` | 2023 Council, Cameron R1 majority |

(rcvis also exposes mirror slugs `2023-vineyard-city-council-20` / `-21` for the same two
2023 seats — identical numbers, ±a handful of votes from canvass updates.)

**2025 official results — Utah County via the Utah state Enhanced Voting portal
(`electionresults.utah.gov`, locality `utah-county-ut`):** an Angular app whose JSON API
base is `https://electionresults.utah.gov/results/public/api`. Contest list:
`…/elections/utah-county-ut/<electionSlug>/ballot-items`; per-contest detail (carries
citywide `summaryResults` **and** per-precinct `breakdownResults`):
`…/ballot-items/<ballotItemId>`.

| File in raw/ | Election slug | Covers |
|---|---|---|
| `ev_2025_general_ballot-items.json` | `general11042025` | full 2025 general contest list (72 items) |
| `ev_2025_general_mayor_detail.json` | `general11042025` | Vineyard Mayor + 8-precinct breakdown |
| `ev_2025_general_council_detail.json` | `general11042025` | Vineyard Council (Vote for 3) + 8-precinct breakdown |
| `ev_2025_primary_ballot-items.json` | `primary08122025` | full 2025 primary contest list |
| `ev_2025_primary_council_detail.json` | `primary08122025` | Vineyard Council primary + 8-precinct breakdown |

The portal flags `isOfficialResults:false` with `asOf 2025-11-20` (post-canvass snapshot);
the City certified these same totals on Nov 18 2025, and they match the certified figures
reported by the Daily Herald. **Note: this Enhanced Voting portal only hosts 2025** —
querying it for 2019/2021/2023 slugs returns 404 (those predate the state's migration to
Enhanced Voting), which is why the RCV years are sourced from rcvis.com.

## Pipeline

```
raw/rcvis_*.html         RCV round tabulations (2019/21/23)  -- transcribed into clean_elections.py
raw/ev_*.json            Enhanced Voting JSON (2025 general + primary, incl. precinct breakdowns)
clean_elections.py       branch on method, normalize, rank, aggregate
  -> vineyard_races.csv                ONE ROW PER RACE: winner, runner-up, seat-deciding margin
  -> vineyard_results_by_candidate.csv race x candidate: first-choice votes, pct, rank, is_winner, final_round_votes
  -> vineyard_results_by_precinct.csv  precinct x candidate (2025 only — see precinct note)
```

Regenerate: `python3 clean_elections.py`  (→ 7 races, 37 candidate rows, 128 precinct rows).

The RCV-year numbers are **transcribed constants** in `clean_elections.py` (rcvis serves
its data as an escaped/JSON-parsed blob, not a flat table), each annotated with its source
file; the 2025 numbers are read **directly** from the `ev_*.json` files.

## Precinct data

- **2025 (plurality): full precinct granularity** — Vineyard has **8 precincts**:
  `25VI01`–`25VI08` (Enhanced Voting `breakdownResults`; precinct code = CountyID `25` +
  `VI` + ##). All three 2025 contests carry all 8 precincts; they sum to the citywide
  totals. These are the only rows in `vineyard_results_by_precinct.csv`.
- **2019/2021/2023 (RCV): CITYWIDE ONLY.** rcvis publishes round tabulations at the
  contest level, not per precinct, so the RCV years have **no precinct breakdown** here.
  (Utah County's per-precinct SOVC for those years was not surfaced as a downloadable file
  during the build — see Gaps.) This is expected for RCV pilot results.

## Cross-check (external corroboration)

Winners independently confirmed against multiple outside sources — no fabrication:
- **Daily Herald (heraldextra.com)** "Making it official: 2025 Municipal election results
  certified" — confirms 2025 Mayor **Stratton**, Council **Lauret / Wood / McCumber**, and
  that McCumber drew the 2-year term by lot.
- **Ballotpedia** `City_elections_in_Vineyard,_Utah_(2019)` — confirms 2019 was RCV, two
  at-large seats, 7 candidates, winners **Welsh** and **Flake** (Flake R5, Welsh R6).
- **rcvis.com** round tabulations — the primary numeric source for every RCV winner/round.
- **City council page** (`vineyardutah.gov`) and recon — confirm current officeholders:
  Stratton (Mayor 2026–29), Lauret & Wood (2026–29), McCumber (2026–27), Holdaway (2024–27),
  and that Sara Cameron (2023 winner) resigned and Ezra Nair was appointed to replace her.
- **2021 Mayor (Julie Fullmer)** — winner confirmed; she was the incumbent re-elected, and
  the 2025 mayoral race was for the open seat she vacated.

**2021 Mayor vote-total discrepancy (flagged):** one web summary reported the 2021 Mayor
totals as Fullmer **597** / Brimhall 57 / Cane 38; the authoritative rcvis tabulation
(`21g_vi_m_u4`, mirrored as `raw/rcvis_2021_mayor.html`) gives Fullmer **1,329** / Brimhall
**132** / Cane **73** (total 1,534). The larger figures are the correct ones — they are
consistent with the 2021 *council*-race turnout (~1,499 first-choice ballots that same
cycle); the smaller figures are not. This repo uses the rcvis tabulation (1,329/132/73).

## Gaps / caveats

- **No downloadable Utah County certified SOVC CSV/PDF for the RCV years (2019/2021/2023)
  was located** during the build. The state Enhanced Voting portal only hosts 2025; the
  older RCV results are taken from rcvis.com (the official RCV visualization vendor used by
  Utah County) and corroborated against Ballotpedia / Daily Herald. If a certified
  Utah County SOVC for those years surfaces later, drop it in `raw/` and reconcile.
- **2023 (and 2019/2021) precinct breakdown is unavailable** (RCV results are citywide on
  rcvis) — `vineyard_results_by_precinct.csv` therefore contains **2025 only**. This is a
  known limitation of RCV-pilot reporting, not an error.
- The Enhanced Voting 2025 numbers are the **canvass snapshot** (`isOfficialResults:false`,
  asOf 2025-11-20) but match the City's Nov 18 certification and press reporting; treat as
  certified.
- RCV "margin" is the seat-deciding **final-round** margin, not a first-choice margin — by
  design (see the RCV modeling section). Don't read it as a plurality margin.
- Vote-for-N inflates 2025 council `total_votes`; `pct` is share-of-council-votes, not
  turnout. Use the Mayor race for turnout.

## Connecting to the rest of the repo

Elections are point-in-time odd-November events (not weekly `../weeks/` material). They join
the rest of the repo via **person + year**: a race winner becomes a councilmember whose
roll-call votes live in `../meeting_minutes/all_votes.csv`. Candidate names here are
UPPER-CASE (e.g. `DAVID LAURET`) vs mixed-case in votes data — normalize case before
joining. Because Vineyard is **at-large**, there is no precinct→district mapping (it's
identity): every Vineyard precinct (`25VI01`–`25VI08`) elects the same citywide officials.

## Don't
- Don't read an RCV council race as single-winner — two seats are up each cycle; both
  winners are flagged `is_winner=Y` in the candidate CSV.
- Don't read the RCV `margin` as a first-choice/plurality margin — it's the seat-deciding
  final round.
- Don't treat 2025 council `total_votes` as turnout (vote-for-3 inflation).
- Don't use the erroneous 597/57/38 figures for 2021 Mayor — use rcvis 1,329/132/73.
- Don't expect precinct rows for the RCV years — citywide only.
