# Logan (Utah) Municipal Election Results

Logan City, **Cache County** (UGRC CountyID **3**), Utah. Mayor + 5-member Municipal
Council, filtered to **Logan races only** and normalized for analysis. Covers the
municipal cycles **2019, 2021, 2023, 2025** (primary + general). Raw files in `raw/`
are the immutable source of truth and are never edited.

> **Disambiguation:** This is **Logan**, the Cache County seat. NOT **North Logan**,
> a separate adjacent city whose contests ("North Logan City Council", "Mayor of North
> Logan") appear in the same county files and are **excluded** here. Some other Cache
> County municipalities (e.g. **Nibley**) used **ranked-choice voting (RCV)** in the state
> pilot — Logan did **not**, and **neither did North Logan** (plurality primaries
> 2021/2023/2025 — the earlier "North Logan RCV" note here was wrong; corrected 2026-08-01
> against the county canvass, see `cache_county/elections/CLAUDE.md`). Every Logan contest
> in this repo is **plurality**.

## Council structure — AT-LARGE, plurality, NO RCV

Logan elects the Mayor (single-winner, 4-yr term) and **5 council members entirely
AT-LARGE — there are NO districts** (in place since 1975). Council terms are 4 years,
**staggered**: **3 seats** are up in 2019 & 2023, **2 seats** in 2021 & 2025. The Mayor
is up in 2021 & 2025 (not 2019 or 2023). The official tallies label council contests
`Vote For N` (N = 3 or 2). Voting method is **plurality / vote-for-N at-large** — top N
vote-getters win; **no ranked-choice**.

### Multi-winner (at-large) modeling
- `district = At-Large` for council; empty for Mayor.
- A council race has **multiple winners**. In `logan_results_by_candidate.csv`,
  `is_winner = Y` for `rank <= N` (general) or `rank <= 2N` (primary = advanced to the
  general). Mayor: `is_winner = Y` for rank 1 (general) / rank <= 2 (primary).
- `total_first_choice_votes` is the **sum of all candidate votes**, inflated by
  vote-for-N (each voter may vote for up to N candidates). `pct` is therefore each
  candidate's **share of all council votes cast**, NOT turnout. Use the Mayor races or
  the raw files' ballots-cast figures for turnout.
- In `logan_races.csv` (one row per race): `winner` = top vote-getter; `runner_up` =
  the **first loser** (rank N+1 general / rank 2N+1 primary); `margin_votes`/`margin_pct`
  = rank-N minus rank-(N+1) = the **seat-deciding margin** (advancement-cutoff margin for
  primaries). For Mayor these are the usual 1st-vs-2nd values.

## Pipeline

```
raw/ (immutable sources, see table)  ->  clean_elections.py  ->
   logan_results_by_precinct.csv   filtered precinct x candidate (geographic)
   logan_results_by_candidate.csv  race x candidate: votes, pct, rank, is_winner
   logan_races.csv                 ONE ROW PER RACE: winner, runner-up, seat-deciding margin
```
Regenerate: `python3 clean_elections.py` (needs `pdftotext`; reads only `raw/`).

## Sources used (all downloaded verbatim into `raw/`)

**KEY FINDING — two different administrators across the window.** In **2019 and 2021,
Logan administered its OWN municipal election** (the City Clerk, not the county). Logan
is therefore **absent** from the Cache County 2021 result PDFs (`cache-2021-*.pdf`, kept
in `raw/` as evidence — they contain only the smaller Cache towns, never Logan). Starting
**2023, Cache County administers Logan's election** and Logan appears in the county
canvass. So:

| Cycle | Office(s) | Raw file(s) | Administrator / source |
|---|---|---|---|
| 2019 primary | Council (3 seats) | `logan-2019-primary-official.pdf` | **City of Logan** official PDF (`loganutah.org/.../OFFICIAL Council Primary August 13, 2019.pdf`) |
| 2019 general | Council (3 seats) | `logan-2019-general-official.pdf` | City of Logan official PDF |
| 2021 primary | Mayor | `logan-2021-primary-official.pdf` | City of Logan official PDF (`OFFICIAL Mayor Primary August 10, 2021.pdf`) |
| 2021 general | Mayor + Council (2 seats) | `logan-2021-general-official.pdf` | City of Logan official PDF (`OFFICIAL General November 2, 2021.pdf`) — both contests in one file |
| 2023 primary | Council (3 seats) | `cache-2023-primary-results.pdf` | **Cache County Clerk** OFFICIAL summary (`cachecounty.gov/.../2023-primary-results.html`, served as PDF) |
| 2023 general | Council (3 seats) | `cache-2023-nov-general-results.pdf` (totals) + `cache-2023-nov-general-details.pdf` (precinct) | **Cache County Clerk CERTIFIED canvass** (dated 12/01/2023) |
| 2025 primary | Mayor + Council (2 seats) | `ev-2025p-logan-mayor.json`, `ev-2025p-logan-council.json` | **Utah Enhanced Voting** JSON API |
| 2025 general | Mayor + Council (2 seats) | `ev-2025g-logan-mayor.json`, `ev-2025g-logan-council.json` | Utah Enhanced Voting JSON API |

Provenance extras in `raw/`: `ev-2023-nov-general-ballot-items.json`,
`ev-2025-primary-ballot-items.json`, `ev-2025-general-ballot-items.json` (the full
county contest lists from which the Logan ballot-item UUIDs were selected);
`ev-2023g-logan-council.json` (the Logan 2023 contest as the portal posted it — see the
2023 note below); and the two `cache-2021-municipal-*.pdf` files (evidence of Logan's
absence from the 2021 county canvass).

### Enhanced Voting (state portal) API — how to refetch
`electionresults.utah.gov` is an Angular SPA backed by a JSON API at
`https://electionresults.utah.gov/results/public/api`. Cache County's org slug is
**`cache-county-ut`** (an older slug `cachecountyutah` 404s on this API). Endpoints:
- election meta: `/elections/cache-county-ut/{election}` (e.g. `2023-Nov-General`,
  `primary08122025`, `general11042025`)
- all contests: `/elections/cache-county-ut/{election}/ballot-items` (returns each
  contest's id + summary)
- one contest w/ precinct breakdown: `/elections/.../ballot-items/{uuid}`
  (`summaryResults.ballotOptions[]` = candidates w/ `voteCount`; `breakdownResults[]` =
  per-precinct). Only **2023 and 2025** exist on the portal for Cache; 2019/2021 predate
  it (and were city-run anyway).

## 2023 ELECTION INTEGRITY EPISODE + RECOUNT (important)

Cache County's **2023** election was conducted under an **integrity investigation**: in
December 2023 the County Clerk (David Benson) and two other elections-office staff were
placed on **administrative leave** pending an elections-related investigation. The Logan
City Council race was **within the 0.25% recount threshold** — votes for **Joe Needham,
Katie Lee-Koven and Jeannie Simmonds** were separated by razor-thin margins; **Lee-Koven
requested a recount**. Logan (and Hyrum) held recounts/canvasses in mid-December 2023;
**the recount did NOT change the result.** Certified outcome (3 seats): **Mark A.
Anderson, Mike Johnson, Jeannie F. Simmonds** win; **Joe Needham is the first loser, the
seat decided by just 19 votes** (Simmonds 2,419 vs Needham 2,400; Lee-Koven 2,388 a
further 12 back).

This repo uses the **CERTIFIED county canvass figures** for 2023, not election-night
numbers. NOTE: the Enhanced Voting portal posting for the same 2023 contest
(`ev-2023g-logan-council.json`, flagged `isOfficialResults:false`) shows **higher,
unofficial** totals (Anderson 3,467 / Johnson 2,909 / Simmonds 2,427 / Needham 2,411 /
Lee-Koven 2,403 / Bennett 1,083; total 14,700) — those are **NOT** used. The certified
canvass PDF (`cache-2023-nov-general-results.pdf`, "OFFICIAL RESULTS") gives Anderson
3,449 / Johnson 2,892 / Simmonds 2,419 / Needham 2,400 / Lee-Koven 2,388 / Bennett 1,082
(total 14,630), which is what `logan_races.csv` / `logan_results_by_candidate.csv` carry.
2023 precinct rows come from the certified details canvass (`...details.pdf`, dated
12/01/2023) and **sum exactly** to those certified totals.

## Coverage (11 races)

| Year | Type | Office | Seats | Winners / advancers |
|---|---|---|---|---|
| 2019 | primary | Council | 3 (adv 6) | Anderson, Simmonds, Jensen, Heare, Garrity, Verdoes advance |
| 2019 | general | Council | 3 | **Anderson, Simmonds, Jensen** (Heare first loser, −408) |
| 2021 | primary | Mayor | 1 (adv 2) | Daines, Jones advance |
| 2021 | general | Mayor | 1 | **Holly H. Daines** (Jones, −1,615) |
| 2021 | general | Council | 2 | **Lopez, Amy Z. Anderson** (Garrity first loser, −504) |
| 2023 | primary | Council | 3 (adv 6) | Anderson, Johnson, Simmonds, Needham, Lee-Koven, Bennett advance |
| 2023 | general | Council | 3 | **Anderson, Johnson, Simmonds** (Needham first loser, **−19**; recount) |
| 2025 | primary | Mayor | 1 (adv 2) | Anderson, Nafziger advance |
| 2025 | primary | Council | 2 (adv 4) | Lopez, Lee-Koven, Dahle, Seamons advance |
| 2025 | general | Mayor | 1 | **Mark A. Anderson** (Nafziger, −1,299) |
| 2025 | general | Council | 2 | **Lopez, Lee-Koven** (Dahle first loser, −84) |

No mayoral race in 2019 or 2023 (Mayor is 4-yr, elected 2017/2021/2025). In 2021 there
was no council primary (only 3 candidates for 2 seats, below the threshold). Mark A.
Anderson was a council member 2018–2025, then **won the mayoralty in 2025** (succeeding
Holly Daines, who did not run); his vacated council seat was filled by appointment
(Melissa Dahle, the 2025 first-loser, now seated).

## Cross-check (external corroboration)

Winners independently confirmed against the Herald Journal (`hjnews.com`), Utah Public
Radio, Cache Valley Daily, KSL, the USU *Statesman*, and the city election page
(`loganutah.gov/government/mayor_s_office/election.php`):
- 2019 council: Mark Anderson, Jeannie Simmonds, Tom Jensen (3 seats). News reported
  election-night unofficials (Anderson 3,796 / Simmonds 3,173 / Jensen 2,522); this repo
  uses the city's **certified** PDF totals (3,837 / 3,221 / 2,546). Winners identical.
- 2021: Mayor Holly Daines re-elected; council Ernesto López & Amy Z. Anderson.
- 2023: Mark Anderson & Jeannie Simmonds re-elected, newcomer Mike Johnson; recount
  confirmed (sltrib, UPR, hjnews).
- 2025: Mayor Mark Anderson; council Ernesto López & Katie Lee-Koven (recon roster).

All per-race precinct rows **sum to the certified candidate totals** for 2019, 2021, and
2023 (verified in the build).

## Connecting to the rest of the repo

Elections are point-in-time events (odd-year Nov) — they do not belong in weekly
`../weeks/` bundles. They join to the rest of the repo via **person + year**: a race
winner becomes a councilmember whose roll-call votes live in `../meeting_minutes/`.
Candidate names vary in case between sources (2019/2021 city PDFs are **mixed-case**,
e.g. `Mark A. Anderson`; 2023/2025 county/portal sources are **UPPER-CASE**, e.g. `MARK
A. ANDERSON`) — normalize case before joining. Because Logan is **fully at-large**, there
is **no precinct→district mapping** (it is identity): every Logan precinct elects the
same citywide Mayor + council; the address tool degenerates to an **in/out-of-city-limits**
check.

## Gaps / caveats

- **2023 primary has no precinct breakdown** — the county summary PDF is contest-level
  only; the portal does not carry the 2023 primary. Race + candidate rows are complete;
  precinct rows for that one race are absent.
- **2025 precinct rows undercount the summary by a few votes** (e.g. general council
  Lopez precinct-sum 3,982 vs certified 3,985). The Enhanced Voting `breakdownResults`
  do not assign every ballot to a precinct (a small unassigned/canvass bucket). The
  **summary `voteTotal` is authoritative** and is what `races`/`by_candidate` use; the
  small precinct shortfall is a portal artifact, not a count change. (2025 portal results
  are also flagged `isOfficialResults:false` — they are the latest the state posts; no
  separate certified Cache PDF was published for 2025 at build time.)
- **Precinct naming differs by era/source** and is kept verbatim: 2019/2021 city PDFs use
  bare numbers (`1`..`33`, `33:5`, `Provisional`); the 2023 certified canvass uses
  `LOG##:I`; the 2025 portal uses `3LG##:I` (CountyID 3 + Logan). Not reconciled to a
  single key.
- 2019/2021 were **city-administered**; their precinct geometry/labels won't match the
  county's UGRC VistaBallotAreas exactly.

## Don't
- Don't edit the raw files in `raw/`.
- Don't treat `North Logan` / `Mayor of North Logan` / `North Logan City Council` as
  Logan, and don't pull any neighboring contest (RCV Nibley; plurality North Logan) — Logan is
  plurality.
- Don't use the unofficial Enhanced Voting 2023 numbers; the **certified county canvass**
  governs 2023 (recount episode).
- Don't read a council race as single-winner — **top N win** (vote-for-N at-large).
