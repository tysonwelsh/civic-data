# election_results — Draper City municipal elections

Draper City municipal **general + primary** election results, normalized to the
SLC/South Jordan/St. George sibling schema. Three CSVs + a reproducible build script
(`clean_elections.py`) + the retained raw county sources under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure — ALL AT-LARGE

Draper is a **council–mayor** city: a **separately-elected Mayor** (citywide,
executive, **non-voting** on the council) + **5 Council Members ALL elected
AT-LARGE — there are NO districts**. 4-year staggered non-partisan terms. City
Council runs as a **single multi-winner "vote-for-N" field**: the top **N**
vote-getters win the **N** open seats that cycle. So a council "race" has **multiple
winners** (`is_winner = rank ≤ N`). This models exactly like the St. George at-large
build; the schema is the 25-column SLC/South Jordan superset.

Two staggered cycles (2 years apart):

| Cycle | Council seats (N) | Years | Mayor? |
|---|---|---|---|
| **A** | **3** | 2007, 2011, 2015, 2019, 2023 | no |
| **B** | **2**, then disrupted → **1** | 2009, 2013, 2017, **2021 (1)**, **2025 (1, 2-yr)** | yes (2009, 2013, 2017, 2021, 2025) |

The Cycle-B stagger was broken by mid-term vacancies: 2021 filled only **1** council
seat and **2025 filled a single 2-year *unexpired* (short) term** (verbatim label
`… (2 YEAR TERM)`; flagged in the `note` column). The Mayor is elected on the B
calendar every 4 years.

### How `n_seats` was determined (cross-confirmed, never guessed)

`vote-for` is printed in the source only for **2021 (1) / 2023 (3) / 2025 (1)**. For
2007–2019 the SOVC carries no "Vote For" string, so `n_seats` is **derived and
internally verified** by the primary→general **"top 2N advance"** candidate counts:

| Year | Primary cands | → General cands | ⇒ 2N | ⇒ N (seats) |
|---|---|---|---|---|
| 2007 | 13 | 6 | 6 | **3** |
| 2009 | 6 | 4 | 4 | **2** |
| 2013 | 7 | 4 | 4 | **2** |
| 2017 | 6 | 4 | 4 | **2** |
| 2011 / 2015 / 2019 | (no primary — field ≤ 2N) | — | — | **3** (Cycle A) |

2011/2015/2019 had no primary (candidates ≤ 2N=6), so their seat count comes from the
stable 4-year re-election chain anchored by 2023's authoritative `vote-for=3` (Cycle A
= 3 seats): the same three winners recur (2007↔2011 Summerhays/Walker/Colbert;
2015 Vawdrey/Weeks/Summerhays; 2019 Vawdrey/Lowry/Roberts; 2023 Lowry/Roberts/Johnson).

## Administering county — Salt Lake County runs the WHOLE election

Draper physically straddles **Salt Lake County (FIPS 49035)** and **Utah County
(49049)**, but under Utah law the county holding the greater share of registered
voters administers the entire city election. For Draper that is **Salt Lake County**:
the SL County SOVC is the **whole-city total**, and **Utah County reports NO Draper
mayor/council race** (the only Utah-County-administered Draper item ever found is a
**2011 bond** — a special-district measure, **excluded** here). So there is **no
Utah-County election gap** for Draper city races; the two-county wrinkle matters only
for bonds/special districts and GIS precincts (see `../geo/`).

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data from the
local county mirror **`~/Desktop/slco-election-archive`** — not re-scraped. Two
provenance layers retained under `raw/`:

1. **`raw/municipal_results_long_draper.csv`** — the archive's canonical SOVC
   normalization, filtered to Draper (every row carries the true `source_file` +
   `sheet`). Precinct- and vote-method-level. Consumed directly for **2007, 2009,
   2011, 2013, 2015, 2017, 2023** (+ their primaries) — all clean, **zero
   suppression**; votes summed across vote methods; per-precinct sums reconcile
   **exactly** to candidate totals (build asserts **0 mismatches**), and 2023
   reconciles to the raw Electionwide-Total (16,480).
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly by the
   build for the **three cases the parsed slice does not deliver correctly** (below).

## The three raw recoveries / fixes

| Contest | Why the slice is wrong / missing | Recovery |
|---|---|---|
| **2019 general** (Council, 3 seats) | **0 rows in the long file — the KNOWN 2019 GAP.** The archive normalizer keyed the contest off the raw sheet name `DRP Council`, so a `%DRAPER%` filter never matched it. | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx` (sheet `DRP Council`, Family-A wide crosstab). Winners **Vawdrey, Lowry, Roberts** — externally confirmed (Draper Journal: Vawdrey ~22%, Roberts ~19%; both match). |
| **2021 general** (Mayor + Council) | **280/350 rows privacy-SUPPRESSED** at the In-Person/Vote-By-Mail method split, destroying the totals. | Re-parsed `raw/sovc/2021-11-02-general-election-sovc.xlsx` (Sheet11 Mayor / Sheet12 Council); the per-precinct **`Total`** sub-rows are un-suppressed and reconcile to the Electionwide-Total (Mayor Walker **5,360**; council Lowery **3,105**). |
| **2025 general + primary** (Mayor + Council) | The slice **silently DROPPED the new 2025-vintage precincts labelled `25DR0N`** (the normalizer's precinct regex didn't match the year prefix), undercounting every 2025 race by ~600 votes (e.g. Mayor 5,454 vs certified 5,910). | Re-parsed both raw SOVC files (`2025-11-04-…` general, `2025-08-12-…` primary); totals now reconcile to the certified Electionwide-Totals (Mayor Walker **5,910**, Rutherford 2,259; council Dahlin **4,518**, Byington 3,606). Winners externally confirmed (Draper Journal). |

**No 2019 municipal PRIMARY** for Draper (verified: no Draper sheet in the 2019 primary
SOVC — 5 candidates for 3 seats, below the 2N=6 primary trigger). A true no-contest,
not a data gap.

## The three CSVs

- **`draper_races.csv`** — one row per race (**23 races: 15 general + 8 primary**),
  **exact 25-column** SLC/South Jordan superset schema. Multi-winner convention (Council):
  `winner` = top vote-getter; `runner_up` = the candidate at **rank N+1** (first loser —
  the seat-deciding boundary); `margin_votes`/`margin_pct` = rank-N vs rank-(N+1) (the
  margin that decided the **last seat**). `n_seats` populated for every race;
  `total_first_choice_votes` blank (the SOVC prints no separate first-choice column).
  `voting_method` is `plurality` for every race **except the 2021 council general**, which
  is `ranked choice (RCV)` — Draper ran Utah's **2021 RCV pilot** (see below). `note` carries
  the 2025 "2-year unexpired/short term" flag and the 2021 RCV first-choice caveat.
  `district = At-Large` (Council) / `""` (Mayor).
- **`draper_results_by_candidate.csv`** — race × candidate (**119 rows**): `votes`,
  `pct` (share of all votes cast in the field — vote-for-N inflates the denominator),
  `rank`, `is_winner` (`True` = won a seat in a general / **advanced** to the general
  in a primary, i.e. `rank ≤ 2N`).
- **`draper_results_by_precinct.csv`** — precinct × candidate (**3,401 rows**),
  vote-methods summed. Precinct IDs are `DRP###`/`DR##` (and the **2025 `25DR0N`**
  vintage). `suppressed=False` everywhere (all suppression recovered).

## Ranked-choice voting — the 2021 pilot

Draper joined **Utah's municipal RCV pilot in 2021**, so the **2021 council general**
(7 candidates, `DRAPER CITY COUNCIL AT-LARGE (Vote for 1)`) was decided by
**instant-runoff, not plurality**. The Salt Lake County SOVC carries only **first-choice**
tallies (the round-by-round tabulation is published separately), so `winner_votes`/
`winner_pct` (**Tasha Lowery, 3,105 / 36.95%**) are a **first-choice share, NOT the RCV
final margin**. The first-choice leader (Lowery) **also won the final round**, so the
`winner` is correct — take the winner from the row, don't quote `winner_pct` as a final
margin. Mirroring the **Millcreek convention**, this race row is stamped
`voting_method='ranked choice (RCV)'` and a `note` records the caveat; the first-choice
tallies are **retained verbatim** (never overwritten). The **2021 mayor** race had a
single candidate (uncontested, 100% — no ranking occurred) and is left `plurality`.
Set by `clean_elections.py` (the `RCV` set + `NOTE`) — regenerate, never hand-edit the CSV.
*(Annotation added 2026-07-19; before that the 2021 council row was labelled `plurality`.)*

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source
(never overwrites raw): collapses whitespace, strips the `(NP)`/`(NON)` non-partisan
tag + leading `*` write-in mark, canonicalizes write-ins. Note **`T. Lowery` (Tasha
Lowery)** ≠ **`F. Lowry` (Fred Lowry)** — two different members with near-identical
surnames; **resolve elections↔votes by full name**, never surname. Election names are
UPPER-CASE; council `all_votes.csv` names are mixed-case — normalize case to join.

## Verification / external cross-check

- **2019 (recovered gap):** Vawdrey/Lowry/Roberts win 3 seats — **confirmed** by the
  Draper Journal (Vawdrey ~22% ≙ CSV 21.81%; Roberts ~19% ≙ 19.36%).
- **2023:** Lowry/Roberts/Johnson — confirmed (KSL/Draper Journal); CSV totals equal the
  raw certified Electionwide-Total (Lowry 4,443 / Roberts 4,377 / Johnson 3,429). News
  election-night figures (3,914/3,845/2,990) are pre-canvass; CSV uses **final canvass**.
- **2025:** Mayor **Troy Walker** re-elected (4th term); **Kathryn Dahlin** wins the new
  2-year council seat (succeeding Marsha Vawdrey) — confirmed (Draper Journal). CSV uses
  the certified SL-County Electionwide-Total (Walker 5,910; Dahlin 4,518), marginally
  above the Journal's earlier-canvass figures (5,885 / 4,499).
- **Mayor history:** Darrell H. Smith (2009) → **Troy K. Walker (2013, 2017, 2021,
  2025)** — consistent with recon and news.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent (asserts 0 precinct-sum mismatches). Re-run when a new cycle posts: add its
SOVC to `raw/sovc/` and either refresh the slice (if the archive normalizer covers it
cleanly) or add a raw parser call. **Watch the `25DR0N`-style precinct renaming** — the
archive normalizer drops precincts it doesn't recognize; always reconcile the new year's
race total to its raw **Electionwide-Total** row.

## Gaps / caveats

- **No 2019 primary** and **no 2011/2015 primary** (fields ≤ 2N) — true no-contests.
- Turnout is populated only where the source carries ballots-cast (**2021, 2023, 2025**);
  older archive years carry registered voters but no ballots-cast → `turnout_pct` blank.
- **Vote-for-N inflates council `total_votes`** (each voter casts up to N votes); `pct`
  is share-of-field, not turnout. Use Mayor races or `ballots_cast` for turnout.
- The **2011 "Utah County Draper Bond"** is intentionally **excluded** (a bond measure,
  not a council/mayor race; the sole Utah-County-administered Draper item).
