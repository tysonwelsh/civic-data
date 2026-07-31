# election_results — Magna City municipal elections

Magna City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/South Jordan sibling schema. Three CSVs + a reproducible build script
(`clean_elections.py`) + the retained raw county source files under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure (form of government changed mid-record)

Magna was a Salt Lake County **metro township (seated 2017-01-01) → CITY (2024-05-01, Utah
H.B. 35)**. The council is elected by **5 single-member DISTRICTS (1–5)**. Key seam:

- **2017–2025 (metro township):** 5-member council, members styled **"Trustee,"** presiding
  via an **elected Chair** who is one of the five (**no separately-elected mayor**).
- **2025 cycle onward:** a separately-elected, citywide **executive Mayor** (Mick "Mickey"
  Sudbury — Magna's **first elected mayor**) plus the 5 district Council Members.

All contests are **plurality, single-member (vote-for-1), non-partisan** (`(NP)`/`(NON)` tags
stripped alongside the verbatim name). No RCV (that is Millcreek, not Magna).

### Term stagger (as the county SOVC files carry it)

| Cycle | Seats up | Years present in data |
|---|---|---|
| **Founding** | **All five (D1–D5)** | **2016** (Nov-2016 general seated the first council) |
| **A** | **Districts 2 & 4** (+ **Mayor** from 2025) | **2017, 2021, 2025** |
| **B** | **Districts 1, 3 & 5** | **2019** (2023 → see gap) |

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data, from the local
county mirror **`~/Desktop/slco-election-archive`** — not re-scraped. Two provenance layers
retained under `raw/`:

1. **`raw/municipal_results_long_magna.csv`** — the archive's canonical SOVC normalization
   (built by the archive's `scripts/normalize_sovc.py`; every row carries the true
   `source_file` + `sheet`), **filtered to the 7 genuine Magna council/mayor contests**
   (precinct + vote-method level). Consumed directly for **2017** (clean) and the **2025**
   general + primary (method `ALL`, clean).
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly by the build
   for the three cycles the parsed slice does not deliver cleanly (below).

## The three cycles recovered from raw

| Contest | Why the slice missed/broke it | Recovery |
|---|---|---|
| **2016 general** (D1–D5) | The **founding** election; **not in the parsed slice** at all. | Re-parsed `raw/sovc/2016-11-08-general-election-sovc.xlsx` (`MAGNA METRO TOWNSHIP CNCL #N` crosstab sheets; per-precinct `Total` rows). Extracted from the county-wide 2016 SOVC zip. |
| **2019 general** (D1/D3/D5) | Present only under the raw sheet code **`MAG Council N`** — a `%MAGNA CITY/METRO%` contest-string filter never matches it (**this is the D1/D3/D5 gap flagged in `recon.md`**). | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx`. All three **uncontested**. |
| **2021 general** (D2/D4) | Present but **14/30 rows privacy-SUPPRESSED** (`****`) at the In-Person/Vote-By-Mail method split, destroying precinct totals (the slice showed only Barney 112 / Hull 132). | Re-parsed `raw/sovc/2021-11-02-general-election-sovc.xlsx` (Sheet59/60), whose per-precinct `Total` sub-rows are **not** suppressed → full totals (Barney 347, Hull 283). |

After recovery **every by-precinct sum reconciles exactly** to its by-candidate total and the
final CSVs have **zero suppressed cells**.

## The three CSVs

- **`magna_races.csv`** — one row per race (**18 races: 15 general + 3 primary**), the
  **25-column** collection-standard header (mirrors South Jordan). `office`/`district`/`contest`
  (canonical) + `contest_verbatim` (the county's era-specific label — township vs city),
  `n_candidates`, `total_votes`, `winner`/`winner_votes`/`winner_pct`,
  `runner_up`/`runner_up_votes`, `margin_votes`/`margin_pct`,
  `registered_voters`/`ballots_cast`/`turnout_pct` (where the source carries them — 2016 & 2019
  & 2021 raw + 2025 provide reg/ballots; 2017 archive-slice leaves reg-only, turnout blank),
  `uncontested`, `suppressed_precincts` (`False` everywhere in final data), `note`,
  `source_file`. `total_first_choice_votes` is blank (all plurality).
- **`magna_results_by_candidate.csv`** — race × candidate (**41 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`magna_results_by_precinct.csv`** — precinct × candidate (**234 rows**). Precinct IDs are
  `MAG###` throughout (e.g. `MAG001`, `MAG901`).

## Winners (final canvass)

| Year | Race | Winner | Notes |
|---|---|---|---|
| 2016 | D1 | Steve Prokopis (829 v. York 604) | founding council |
| 2016 | D2 | Brint D. Peel (643 v. Elieson 608) | |
| 2016 | D3 | Dan W. Peay (740 v. **Gardner 735** — margin **5**) | razor-thin; verified precinct-by-precinct |
| 2016 | D4 | Trish Hull (631 v. Sudbury 496) | |
| 2016 | D5 | Eric Ferguson (662 v. Nosack 473) | |
| 2017 | D2 | Brint D. Peel (uncontested) | |
| 2017 | D4 | Trish Hull (uncontested) | |
| 2019 | D1 | Steve Prokopis (uncontested) | |
| 2019 | D3 | Dan W. Peay (uncontested) | |
| 2019 | D5 | Audrey Pierce (uncontested) | |
| 2021 | D2 | **Eric G. Barney** (347 v. Peel 190, Ramos 44) | unseats Peel |
| 2021 | D4 | Trish Hull (uncontested, 283) | |
| 2025 | Mayor | **Mickey M. Sudbury** (2260 v. Adriano 1196) | **first elected mayor** |
| 2025 | D2 | **Megan L. Olsen** (431 v. Barney 199) | unseats Barney |
| 2025 | D4 | **Terry George** (323 v. Hull 289) | unseats Hull; now Mayor Pro Tem |

2025 also had an **August primary** (D2, D4, Mayor) — top-two advanced; stored as
`election_type='municipal primary'`.

## External cross-check (2026-07-12)

- **2025 Mayor — Mickey Sudbury CONFIRMED** as Magna's first elected mayor by the West Valley
  City Journal ("Magna has the first elected mayor in its history", 2026-02-18), the Utah state
  elections portal, and the Salt Lake Tribune 2025 suburban-mayor coverage. Election-night news
  reported ~67.4% vs Adriano 32.6%; the CSV's **65.39%** (2260/3456) is the **final canvassed**
  SOVC share — the minor delta is the usual election-night-vs-final-canvass difference.
- **2025 D4 Terry George** (now **Mayor Pro Tem**) and **2025 D2 Megan Olsen** confirmed seated
  as council members on `magna.utah.gov/171/City-Council` — matching the CSV winners.

## Decoys EXCLUDED (never council/mayor seats)

`~95%` of "magna" rows in the county file are these — the build filters on the **exact** genuine
contest strings, never a bare `MAGNA` match:

- **Magna Water District** — `Magna Water Brd Trust` / `MAGNA WATER` / `MAGNA WATER DIST` /
  `MAGNA WATER BOARD OF TRUSTEES` / `MAGNA WATER DISTRICT BOARD OF TRUSTEES AT-LARGE` /
  `MAGNA WATER SPECIAL BOND ELECT` (a separate special district).
- **`MAGNA MSD`** (2015 MSD-formation ballot question).
- **`MAGNA METRO TOWNSHIP-CITY`** (2015 incorporation ballot question).

## Gaps / caveats

- **2023 general (D1/D3/D5) — ABSENT (honest gap).** The county SOVC archive carries **no
  Magna council district race for 2023** (only `MAGNA WATER DISTRICT`, a decoy). Utah **cancels
  uncontested municipal races**, so the Cycle-B incumbents (D1 Prokopis, D3, D5 Pierce) most
  likely drew no opponent and no contest was tabulated. **Recorded, not fabricated.** If a 2023
  Magna council sheet ever surfaces, add a raw parser call mirroring 2019.
- **D3 & D5 roster changes are NOT in the election data.** D3 Peay (won 2016 & 2019) → current
  D3 **Michael H. Jensen**, and D5 Ferguson (2016) → Pierce (2019), happened via mid-term
  appointment or the missing/cancelled 2023 cycle — a roster matter, not an election here.
- **Turnout** populated only where the source carries reg + ballots (2016/2019/2021/2025);
  2017 leaves `turnout_pct` blank. 2016 turnout is high (~76–80%) because it rode the **Nov-2016
  presidential general** ballot.
- **Name variants across years** are expected and retained verbatim (`ERIC G BARNEY` 2021 vs
  `ERIC GORDON BARNEY` 2025; `TRISH HULL` vs `TRISH A. HULL`). Normalize (case/suffix) before
  joining elections ↔ votes.
- Precinct geometry for joins: `../geo/precincts.geojson` (join `precinct` = `MAG###`).

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent. Re-run when a new cycle posts: add its SOVC to `raw/sovc/`, then either refresh the
archive slice (if the normalizer covers the new year cleanly) or add a raw parser call. Mind the
cycle — **A** = D2/D4/Mayor (2025, 2029…); **B** = D1/D3/D5 (2027, 2031…).


## 2026-07-17 — 2023 cancelled-certification rows (owner-approved convention, hand-edited)
Three rows were hand-appended to `magna_races.csv` for the **2023 election that was CANCELLED**
under **Utah Code § 20A-1-206**. Per Resolution 23-09-02 (adopted 2023-09-26; text at
`ordinances/text/Resolution_2023-09-02.txt`, verbatim in the 2023-09-26 minutes), only three
candidates filed for the three open township-council seats, so the Metro Township cancelled the
Nov-21-2023 election and **deemed the unopposed candidates elected effective 2024-01-01**:
**Steve Prokopis, Audrey Pierce, and Mick Sudbury**. District mapping (the resolution lists the
three names without districts): the 2023 seats were the odd D1/D3/D5 cycle — **Prokopis = D1**
and **Pierce = D5** (both incumbents from 2019), **Sudbury = D3** (the seat Peay vacated; the
roster lists Sudbury D3 — the roster's "APPOINTED" label should read elected-by-cancellation).

**Representation of a cancelled-certification row (owner convention — REPORT to orchestrator):**
the certified winner goes in `winner`; **every vote-count and percentage column is BLANK**
(no votes exist — never a fabricated tally, not even 0); `uncontested=True`; `n_seats=1`,
`n_candidates=1`, `voting_method=plurality` (structural, not tallies); and the `note` column
LEADS with the greppable marker `cancelled_certification (Utah Code 20A-1-206; Res 2023-09-02)`.
`source_file = Resolution_2023-09-02.txt`. Dated backup:
`_backups/2026-07-17-audited-election-rows/magna/`.
