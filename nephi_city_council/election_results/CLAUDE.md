# Nephi (Utah) Municipal Election Results

Nephi City, **Juab County** (UGRC CountyID **12**) municipal election results, filtered to
**Nephi City Mayor + City Council** and normalized for analysis. Target cycles
**2019, 2021, 2023, 2025**. Built from scratch — there is **no pre-existing Juab County
election archive**. Raw files in `raw/` are the immutable source of truth and are never edited.

> **Disambiguation:** Nephi, **Utah** (Juab County seat, pop. ~6,500). The City Council is
> elected entirely **AT-LARGE — no districts/wards** — and there is **no ranked-choice
> voting** (Nephi is not in Utah's RCV pilot; plain plurality / top-N).

## Council structure (at-large, staggered)

Mayor + **5 at-large council members**. The Mayor and **2 council seats** are elected on one
4-year cycle (**2021, 2025**); the **other 3 council seats** are on the offset 4-year cycle
(**2019, 2023**). So:

| Cycle | Mayor? | Council seats (Vote For) |
|---|---|---|
| 2019 | no  | **3** |
| 2021 | yes | **2** |
| 2023 | no  | **3** |
| 2025 | yes | **2** |

Seat counts confirmed: 2025 & 2025-primary = official `Vote for 2` label in the Enhanced
Voting JSON; 2019 = Deseret "(3 elected)"; 2021 = 2 winners seated; 2023 = `vote-for-3`
(official Sept-5-2023 primary had **9 candidates** → top-6 advanced to a 6-candidate general;
top-3 of the general = current seated members Worwood/Cowan/Parady).

## Pipeline

```
raw/ev-juab-*.json                 Enhanced Voting JSON API (2023 + 2025; SOURCE OF TRUTH)
raw/deseret-2019-*.html            archived 2019 unofficial canvass (city totals only)
raw/midutahradio-2021-*.html       archived 2021 unofficial canvass (city totals only)
build_nephi.py                     parse EV JSON -> rank, aggregate, precinct breakdown;
                                   writes races.csv in the SCHEMA_SPEC §9 25-col superset
build_nephi_manual.py              2019/2021 general + 2023 PRIMARY rows (not in the EV
                                   portal; hand-keyed from raw HTML / the official county PDF)
  -> nephi_races.csv               ONE ROW PER RACE: winner, runner-up, margin
  -> nephi_results_by_candidate.csv  race x candidate: round1/final votes, pct, rank, is_winner
  -> nephi_results_by_precinct.csv   per-precinct x candidate (2023 & 2025 only)
```
Regenerate: `python3 build_nephi.py`

## Sources

**Primary — Utah state Enhanced Voting portal (covers Juab County, 2023 onward):**
`https://electionresults.utah.gov/results/public/juab-county-ut/...`
The portal is a JS/Angular SPA; results come from its **JSON API** (not the rendered HTML),
fetched directly with curl. Endpoints used (host `electionresults.utah.gov` or
`app.enhancedvoting.com`, base `/results/public/api`):
- `/jurisdictions/juab-county-ut` — election list/slugs (`raw/ev-juab-county-ut-jurisdiction-elections.json`)
- `/elections/juab-county-ut/<slug>/ballot-items` — all contests + summary candidate totals
- `/elections/juab-county-ut/<slug>/ballot-items/<id>` — one contest **with per-precinct
  breakdown** (`breakdownResults`)

| Cycle | EV election slug | Raw file |
|---|---|---|
| 2023 Nov general | `2023-Nov-General` | `raw/ev-juab-2023-Nov-General-*.json` |
| 2025 Aug primary | `primary08122025`  | `raw/ev-juab-primary08122025-*.json` |
| 2025 Nov general | `general11042025`  | `raw/ev-juab-general11042025-*.json` |

The Enhanced Voting portal only carries Juab elections back to **2023** (verified: no
2019/2021 slugs exist; `general1105 2019` / `general11022021` etc. all 404). The Juab County
Clerk site (`juabcounty.gov/residents/election-information/election-results/`, archived as
`raw/juabcounty-election-results-index.html`) likewise only links results pages from 2023+.

**Official Juab County 2023 canvass PDFs** (the `ev-juab-2023-*.json` general data is pulled
from the undocumented state Enhanced Voting API, a live SPA with no durable per-file archive
URL — so these Clerk-published PDFs are the stable official-canvass equivalents/sources):
- 2023 Nov general: `https://juabcounty.gov/wp-content/uploads/2023/11/Gen-Election-Results-11-29.pdf`
  (content-verified 2026-07-19; equivalent to the EV general JSON already ingested).
- **2023 Sept-5 primary: `https://juabcounty.gov/wp-content/uploads/2023/09/Official-Results-Prim-23.pdf`**
  — this is the **SOURCE OF TRUTH for the 2023 council primary** (the EV portal carries only an
  empty `primary09052023_Demo` slug). Downloaded to `raw/juabcounty-2023-primary-official-results.pdf`
  and hand-keyed via `build_nephi_manual.py` (verified 2026-07-20). Official header: "Juab County,
  UT Summary Results — OFFICIAL RESULTS — Municipal Primary Election — September 5, 2023"; contest
  "Nephi City Council / Vote For 3", 9 candidates, printed Contest Totals 4,608 (named-candidate
  sum 4,214; the 394 difference = write-in/unallocated votes not itemized in the summary).

**2019 & 2021 (pre-portal) — secondary/unofficial sources, archived in `raw/`:**
- 2019: Deseret News statewide municipal tally
  (`raw/deseret-2019-utah-municipal-general-results.html`) — verbatim: *"Nephi CITY COUNCIL
  (3 elected): Justin D. Seely (inc.) 501, Larry O. Ostler (inc.) 500, Nathan H. Memmott
  (inc.) 495, Sarah Goode 139."* No mayor race in 2019.
- 2021: Mid-Utah Radio unofficial results
  (`raw/midutahradio-2021-municipal-election-results.html`) — verbatim: *"Nephi: Mayor
  Justin D. Seely 965, Glade R. Nielson 673; City Council Skip F. Worwood 1,162, Jeramie L.
  Callaway 834, J.D. Parady 708, L. Nyle Robinson 388."*

## AT-LARGE modeling (mirrors the St. George repo)

- `district` = `At-Large` for all council races; empty for Mayor (single-winner).
- A council "race" has **multiple winners**: in `nephi_results_by_candidate.csv`,
  `is_winner = True` for `rank <= n_seats` (the candidates who won a seat).
- `total_first_choice_votes` for a council race is the **sum of all candidate votes**, which
  exceeds ballots cast because each voter votes for up to N candidates. `round1_pct` /
  `final_pct` are therefore each candidate's **share of all council votes cast**, not turnout.
- In `nephi_races.csv` (one row per race): `winner` = top vote-getter; `runner_up` = the
  candidate at **rank n_seats+1** (first loser — just missed the last seat); `margin_votes` /
  `margin_pct` = rank-N winner minus rank-(N+1) loser — the margin that **decided the final
  seat** (the analytically meaningful closeness). For Mayor, these are the usual 1st-vs-2nd.
- **No RCV:** `voting_method` = `plurality` (mayor) / `plurality at-large (vote-for-N)`
  (council). `round1_votes == final_votes` everywhere (single-count plurality).

### Primary
Two council primaries are in the record. In primary rows, `is_winner = True` means **advanced
to the general** (top 2N), and `runner_up`/`margin` describe the advancement cutoff (rank 2N vs
2N+1), not a seat. No mayoral primary in either cycle (Seely unopposed).
- **2023 (Sept 5 2023)**: **9 candidates for 3 seats** → field 9 > 2N=6 triggered a primary; top
  **6** advanced (Worwood, Parady, Cowan, Ostler, Bradley, Miller — exactly the 2023 general
  field; the primary eliminated **Andersen, Ford, Goates**). OFFICIAL Juab County canvass (see
  Sources). margin = 168 (Miller 449 vs Andersen 281). NOTE the EV portal has only an empty
  `primary09052023_Demo` slug (0 votes) — the real numbers come from the county PDF, hand-keyed.
- **2025 (Aug 12 2025)**: 5 candidates for 2 seats; top 2N=4 advanced (Douglas, Callaway,
  Worwood, Miller; Jackson out). Enhanced Voting JSON.

## Coverage (8 races)

| Year | Type | Office | Seats | Winners / advancers | Source |
|---|---|---|---|---|---|
| 2019 | general | Council | 3 | **Seely, Ostler, Memmott** (Goode lost) | Deseret (unofficial) |
| 2021 | general | Mayor   | 1 | **Justin D. Seely** (def. Nielson) | Mid-Utah Radio (unofficial) |
| 2021 | general | Council | 2 | **Worwood, Callaway** (Parady, Robinson lost) | Mid-Utah Radio (unofficial) |
| 2023 | primary | Council | 3 | Worwood, Parady, Cowan, Ostler, Bradley, Miller advance (Andersen, Ford, Goates out) | **Juab County OFFICIAL PDF** |
| 2023 | general | Council | 3 | **T. Worwood, Cowan, Parady** (Ostler, Bradley, Miller lost) | Enhanced Voting |
| 2025 | primary | Council | 2 | Douglas, Callaway, Worwood, Miller advance (Jackson out) | Enhanced Voting |
| 2025 | general | Mayor   | 1 | **Justin D. Seely** (UNOPPOSED) | Enhanced Voting |
| 2025 | general | Council | 2 | **Douglas, Callaway** (Worwood, Miller lost) | Enhanced Voting |

The five seated council members trace cleanly across cycles: 2021 → Skip Worwood & Callaway;
2023 → Travis L. Worwood, Cowan, Parady; 2025 → Douglas (+ Callaway re-elected). (Two distinct
Worwoods: **Skip F.** elected 2021, **Travis L.** elected 2023.)

## Precinct data

Nephi has **5 precincts** (`Nephi #3`–`#7`; the Enhanced Voting 2025 data prefixes the
CountyID, `12Nephi #3`–`#7`). `nephi_results_by_precinct.csv` covers the **EV years only**
(2023 council; 2025 mayor, council, primary). Per-precinct sums reconcile **exactly** to the
contest totals (verified). **2019 & 2021 have no precinct breakdown** — the archived news
sources report city totals only.

## Gaps / caveats

- **2019 & 2021 figures are UNOFFICIAL** (election-night/canvass tallies from news outlets),
  not a certified county canvass — the Juab Clerk and the state portal do not publish results
  online for those years. Winner identities and seat counts are solid; exact vote totals carry
  the usual unofficial-tally caveat. No precinct breakdown for these two cycles.
- **2023 council vote totals** come from the official Enhanced Voting portal but were marked
  `isOfficialResults: false` (the portal snapshot is the canvass-period publication). Candidate
  order and the top-3 winners are confirmed; a later-certified PDF could differ by a vote or two.
- **2025 Mayor was uncontested** — Seely unopposed (1,298; `winner_pct` 100, no runner-up/margin).
- **2023 council primary (Sept 5 2023) — RECOVERED 2026-07-20.** Earlier builds wrongly recorded
  "no 2023 primary" (they assumed a 6-candidate field and saw only the empty EV `_Demo` slug).
  The OFFICIAL Juab County canvass PDF shows a real 9-candidate Vote-For-3 primary; it is now in
  the dataset (hand-keyed via `build_nephi_manual.py`; `raw/juabcounty-2023-primary-official-results.pdf`).
  `registered_voters`/`ballots_cast`/`turnout_pct` are left blank on this row: the PDF's stats
  block (5,877 reg / 2,471 cast / 42.05%) is **county-wide** (Nephi + Mona + Levan + Rocky Ridge +
  a Republican federal race), not Nephi-specific. Precinct breakdown is unavailable (summary PDF).
- Council `total_first_choice_votes` is vote-for-N inflated — `pct` is share-of-council-votes,
  not turnout. Use the Mayor race, or registered-voter/ballots-cast figures in the raw JSON
  (`totalVoters`, `ballotsCast`), for turnout.

## Connecting to the rest of the repo

Elections are point-in-time (odd-year Nov) — they don't belong in weekly bundles. They join
the rest of the repo by **person + year**: a race winner becomes a councilmember whose motions
appear in `../meeting_minutes/`. Candidate names here are UPPER-CASE
(e.g. `JERAMIE L. CALLAWAY`) vs mixed-case in minutes; normalize case (and reconcile the two
Worwoods) before joining. Because Nephi is **at-large**, there is no precinct→district map —
every precinct elects the same citywide officials (the geo tool reduces to in/out-of-city-limits).

## Don't
- Don't edit the `raw/` files.
- Don't read a council race as single-winner — top N win (see at-large model).
- Don't treat the 2019/2021 unofficial figures as certified.
- Don't match a neighboring Juab municipality (Mona, Levan, Eureka, Rocky Ridge) as Nephi —
  the Enhanced Voting ballot-items list mixes all of them in one election.
