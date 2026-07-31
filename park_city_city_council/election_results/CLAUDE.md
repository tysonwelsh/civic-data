# Park City, Utah — Election Results

Municipal **Mayor + City Council** results for **2019, 2021, 2023, 2025** (primary + general).
Built 2026-06-26 by `build_parkcity_elections.py` (re-run it to regenerate the three CSVs).

## KEY PREMISE — Park City SELF-ADMINISTERS its municipal elections
Unlike the other Utah cities in this archive, Park City's mayor/council results are **NOT
published by Summit County**. The Summit County Clerk explicitly defers: *"Municipal
election results are available by contacting the municipality that was responsible for
running their elections."* The city's elected body sits as the **Board of Canvassers** and
certifies results itself (the Summit County Clerk runs the mechanics / tabulation under
contract, which is why the precinct reports carry a "Summit County … OFFICIAL RESULTS"
banner, but the **certifying authority and publisher is Park City**).

**Authoritative source:** the city's own election page,
`https://www.parkcity.gov/government/elections/election_results.php`
(saved as `raw/parkcity_election_results_page_2026-06-26.html`), which embeds the official
results tables AND links the canvass / precinct PDFs. Cross-checked against
`electionresults.utah.gov` (Summit County context) and Park Record / KPCW / TownLift /
Ballotpedia for winner confirmation.

> Scraper note: `parkcity.org` 301-redirects to `parkcity.gov`; the `.gov` document links
> further 301 to `www.parkcity.gov` and **require URL-encoded spaces** (`%20`) or the fetch
> silently fails (HTTP 000). The CMS reuses generic filenames ("Canvass Resolution.pdf",
> "Votes by Precinct.pdf") across cycles, so the raw PDFs were renamed in `raw/` to match
> their **actual** certified content, verified by reading each PDF — do not trust the
> website's link labels.

## Council structure — AT-LARGE, vote-for-N, NO RCV
- All 5 council seats + the mayor are elected **citywide / at-large**. There are **no
  council districts** (so there is no precinct→district map; the geo tool degenerates to an
  address → in/out-of-city-limits check).
- **Staggered 4-year terms:** one cycle elects **Mayor + 2 council** (2021, 2025); the next
  elects **3 council** (2019, 2023).
- **Vote-for-N block plurality.** The top N vote-getters win the N open seats; **ALL N
  winners have `is_winner=Y`** in `results_by_candidate.csv`. Primaries advance the **top
  2N** to the general.
- **No Ranked Choice Voting** in any cycle here. Park City studied RCV and **punted in Sept
  2024** (awaiting a UVU study) — flag for future cycles, but `voting_method` = "no RCV"
  throughout.

## The 2025 mayoral recount (decided by 7 votes)
The Nov 4 2025 mayor's race was the closest in the dataset: **Ryan Dickey 1,706 (50.10%) vs
Jack Rubin 1,699 (49.90%) — a 7-vote margin (0.21%).** Park City certified the general
canvass Nov 18 2025 (Resolution 25-2025). The losing candidate **Rubin requested a recount
on Nov 20**; the Summit County Clerk conducted it and the Board of Canvassers **certified
the recount Nov 24 2025 (Resolution 27-2025) with the identical 1,706–1,699 result**,
confirming Dickey as mayor (sworn Jan 5 2026). The CSVs carry the **certified canvass /
recount** numbers (they match). Raw: `raw/2025_general_canvass.pdf` and
`raw/2025_general_recount_canvass.pdf`. (Same cycle: Tana Toly and Diego Zegarra won the two
council seats; Zegarra is Park City's first Latino councilor.)

## Files
| File | Rows | Notes |
|---|---|---|
| `park_city_races.csv` | 11 | one row per contest (year × primary/general × office) |
| `park_city_results_by_candidate.csv` | 56 | every candidate, ranked, `is_winner` |
| `park_city_results_by_precinct.csv` | 308 | per-candidate per-precinct, where the canvass provides a clean table |
| `raw/*.pdf` (7) + `*.html` | — | certified canvass / precinct PDFs + saved results page |

### `park_city_races.csv` columns
`year, election_type, office, district, contest, n_seats, n_candidates, voting_method,
total_first_choice_votes, winner, winner_votes, winner_pct, runner_up, runner_up_votes,
margin_votes, margin_pct`
- `district` = `At-Large` for council, blank for mayor.
- `n_seats` = seats the office fills that cycle (mayor 1; council 2 or 3). Primaries share
  the office's seat count; `voting_method` records the "top 2N advance" cut.
- `total_first_choice_votes` = total votes cast in the contest (= sum of candidate votes).
  For vote-for-N council this is **inflated by N** (each voter casts up to N votes).
- `winner` = top vote-getter; `winner_pct` = winner's share of `total_first_choice_votes`.
- `runner_up` = the **first non-winner** (the highest-ranked candidate who did NOT
  win/advance, i.e. rank N+1 in a general, rank 2N+1 in a primary).
- `margin_votes` / `margin_pct` = the **seat-deciding (or advancement) boundary**: the last
  winner's votes minus the first loser's votes — NOT winner-minus-runner_up. (E.g. 2023
  general council margin 74 = Ciraco 1,158 − Sertner 1,084, the 3rd-vs-4th seat boundary.)

### pct semantics (IMPORTANT)
For council vote-for-N, `pct` is **share of total council votes cast in the contest, NOT
voter turnout** — the denominator is inflated because each voter casts up to N votes. Mayor
`pct` is a true two-way share. Turnout figures live in the canvass PDFs (e.g. 2025 general
63.28%, 5,431 active registered, 3,437 ballots), not in these CSVs.

## Precinct coverage & codes
`results_by_precinct.csv` covers the cycles with a **clean per-candidate precinct table**:
**2021 primary** (mayor+council), **2021 general** (mayor+council), **2023 general**
(council), **2025 general** (mayor+council). Precinct codes are reproduced verbatim from
each source PDF. The 2021/2023 Electionware reports use short codes (`Dvn1:1`, `Pkmn35:1`,
…); the 2025 report uses **CountyID-prefixed** codes (`22DVN:15`, `22PKMN:15`, …) — same
physical precincts, renamed between cycles. `22DVS:30` (4–9 voters) is **Suppressed** for
privacy in the 2025 source and is omitted.

**Reconciliation:** every 2021 and 2023 precinct-sum matches the certified candidate total
exactly. **2025** precinct sums run a few votes below the certified canvass (Rubin −4, Toly
−3, Rubell −3, Zegarra −1; Dickey exact) because **late-cured / provisional ballots are not
assigned to a precinct** — the CSVs use the certified canvass totals in
`races`/`by_candidate` and the precinct-tabulated figures in `by_precinct`. This is expected
and not an error.

## Gaps / caveats
- **2019 (primary + general): no precinct data, and no canvass PDF.** The city's CMS only
  surfaces the 2019 results as the embedded HTML table (which this build uses); the old
  `showpublisheddocument` deep links 404. Candidate totals are confirmed by KPCW / Deseret /
  Ballotpedia, but a born-digital 2019 canvass PDF could not be retrieved. Numbers traced to
  `raw/parkcity_election_results_page_2026-06-26.html`.
- **2023 primary: no per-candidate precinct data.** The canvass PDF's "Precinct Table
  Report" page is image/garbled for the candidate columns (only registered/cast/turnout per
  precinct survive extraction). Contest totals ARE certified text (used in
  races/by_candidate); per-precinct candidate votes are not recoverable. Raw:
  `raw/2023_primary_canvass.pdf`.
- **2025 primary: canvass PDF is image-only** (no text layer except the Docusign envelope
  ID), so those numbers are traced to the city's embedded HTML results table, not the PDF
  text. No precinct breakdown exists for the 2025 primary. Raw: `raw/2025_primary_canvass.pdf`.
- **Withdrawals:** Thomas C. Purcell appeared on the 2021 general council ballot but
  withdrew (0 votes) — excluded as a non-competing candidate. John "J.K." Kenworthy advanced
  from the 2025 council primary (4th) but withdrew before the general, leaving only 3
  candidates for 2 seats.
- **Ballot measures excluded:** the 2023 general Recreation Bond (No 1,439 / Yes 1,165) and
  2019 Open Space Bond (For 3,315 / Against 931) are recorded here for reference only and
  are NOT in the candidate CSVs (this archive tracks mayor/council races).

## Provenance summary (every number traces to a raw file)
| Cycle | Candidate totals source | Precinct source |
|---|---|---|
| 2019 P+G | results page HTML | — (none) |
| 2021 primary | `2021_primary_votes_by_precinct.pdf` (Totals) | same PDF |
| 2021 general | `2021_general_votes_by_precinct.pdf` (Totals) | same PDF |
| 2023 primary | `2023_primary_canvass.pdf` (canvass text) | — (image-garbled) |
| 2023 general | `2023_general_election_reports.pdf` (canvass text) | same PDF |
| 2025 primary | results page HTML (canvass PDF image-only) | — (none) |
| 2025 general | `2025_general_canvass.pdf` + `..._recount_canvass.pdf` | `2025_general_canvass.pdf` |
