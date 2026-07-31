# election_results — Riverton City municipal elections

Riverton City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/Sandy/South-Jordan sibling schema. Three CSVs + a reproducible build
script (`clean_elections.py`) + the retained raw county source files under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure

Riverton is a **six-member council form**: a **5-member council elected by DISTRICT
(Districts 1–5)** plus a **separately elected Mayor** (citywide; the Mayor chairs the council
and votes only to break a tie — see the city `recon.md`). There are **no at-large council
seats**. 4-year staggered non-partisan terms, so each odd-year cycle fills only part of the
body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 3 + District 4** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **Districts 1, 2, 5** | 2007, 2011, 2015, 2019, 2023 |

The Mayor is elected only on the **A** cycle (no mayor race in a B year). Note Riverton's
B-cycle seats are **1 / 2 / 5** and A-cycle **3 / 4 + Mayor** — unlike sibling South Jordan
(B = 1/2/4, A = 3/5+Mayor). Riverton's council was **numbered `#1/#2/#5`** at-large in 2007,
became **`DIST 3/DIST 4`** from 2009, and **`DISTRICT N`** from ~2015/2021; all normalize to
`Riverton City Council District N`.

## ⚠ D3 ↔ D4 NUMBERING CAVEAT (read before joining people to districts across 2022)

**Election labels here are VERBATIM from the county SOVC and are kept as-is.** But the
District-3 / District-4 seat *numbers* are **not stable across the 2022 redistricting**
(Ordinance No. 22-07):

- The **authoritative election record** shows **Tawnee McCay winning "District 3"** (2017 &
  2021) and **Tish Buroker winning "District 4"** (2017 & 2021).
- This is **OPPOSITE** to `recon.md` and the **current** city GIS labels, which describe
  McCay as the D4 member and Buroker as the D3 member (Buroker → Mayor 2026; her seat →
  Alexander **Johnson (D3)**; McCay's seat → Shannon **Smith (D4)**).
- **Independent corroboration in the GIS:** the retained **pre-2022** district layer
  (`../geo/districts_pre2022.geojson`, the 2019 lines) labels **D3 = Tawnee McCay, D4 = Tish
  Buroker** — matching the election record — while the **current 2022** layer
  (`../geo/districts.geojson`) labels **D3 = Johnson, D4 = Smith**. The seat geography +
  number were therefore **renumbered (D3 ↔ D4) at the 2022 redraw**.

**Consequence:** do **not** assume the D3/D4 number is the same person's seat before and
after 2022. Person↔district joins that cross the 2022 boundary (e.g. tying a 2017/2021
"District N" winner to a post-2022 "District N" seat, roster, or GIS polygon) must join on
**person identity**, not on the bare district number. Within a single era the numbers are
consistent; only the D3↔D4 pair flips across 2022. (D1/D2/D5 are unaffected.)

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data. Two
provenance layers are retained under `raw/`:

1. **`raw/riverton_slco_results_long.csv`** — a verbatim filter (`contest LIKE
   '%RIVERTON%'`) of the collection-canonical
   `salt_lake_county/elections/slco_municipal_results_long.csv` (the county SOVC normalized
   to one row per year/contest/precinct/candidate/vote-method). Consumed directly for
   **2007, 2009, 2011, 2013, 2015, 2017, 2023, 2025** (generals + the primaries the county
   published), summed across vote-method rows to the precinct × candidate level.
2. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed directly by the build
   for the **two years the canonical slice does not deliver cleanly** (see below).

## The two years recovered from raw SOVC

| Year | Why the canonical slice missed / broke it | Recovery |
|---|---|---|
| **2019 general + primary** (Cycle B: D1/D2/D5) | **Absent** from the canonical slice: the county keyed the contest off the worksheet name and Riverton's 2019 sheets are named **`RIV Council 1/2/5`** (no `RIVERTON` string), so a `%RIVERTON%` filter never matched them (same failure mode as sibling South Jordan's `SJD Council N`). **This is the gap flagged in `recon.md`.** Its winners are the **2020–2023 voting bench** (in scope for the 2020-floor minutes record). | `parse_2019()` re-parses `raw/sovc/2019-11-05-general-election-sovc.xlsx` + `2019-08-13-municipal-primary-sovc.xlsx` (Family-A wide crosstab; the per-candidate `Total Votes` column is the precinct count). |
| **2021 general** (Cycle A: D3/D4/Mayor) | Present in the slice but **privacy-SUPPRESSED**: the county split every precinct cell at the In-Person / Vote-By-Mail method line (`****`), which collapsed the candidate totals — **District 3 winner Tawnee McCay read 0 votes / all-`****`** in the suppressed slice. | `parse_2021()` **skips 2021 in `load_slice()`** and re-parses `raw/sovc/november-2-2021-general-election-statement-of-votes-cast.xlsx` (precinct-block layout), reading each precinct's **unsuppressed `Total` sub-row** — only the method split was ever hidden. |

After recovery the final CSVs have **zero suppressed cells** and every by-precinct sum
reconciles exactly to its by-candidate total (the build asserts **0 mismatches**). Recovered
2021 totals: **McCay (D3) = 863, Buroker (D4) = 1160, Staggs (Mayor) = 4973** (all three
uncontested; registered-voter / ballots-cast / turnout preserved).

**2019 municipal PRIMARY:** the raw 2019 primary SOVC carries Riverton **D2 and D5** (3–4
candidates each) but **no D1 sheet** → D1 drew ≤2 candidates (Sheldon B. Stewart effectively
unopposed), so no D1 primary was triggered. Logged, not fabricated.

## The three CSVs

- **`riverton_races.csv`** — one row per race (**39 races: 30 general + 9 primary**).
  Columns: `office`/`district`/`contest` (canonical) + `contest_verbatim`, `n_candidates`,
  `total_votes`, `winner`/`winner_votes`/`winner_pct`, `runner_up`/`runner_up_votes`,
  `margin_votes`/`margin_pct`, `registered_voters`/`ballots_cast`/`turnout_pct` (where the
  source carries them — 2021/2023/2025 provide ballots-cast → turnout; other years leave
  `turnout_pct` blank), `uncontested`, `suppressed_precincts` (**`False` everywhere in the
  final data**), `source_file`.
- **`riverton_results_by_candidate.csv`** — race × candidate (**105 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`riverton_results_by_precinct.csv`** — precinct × candidate (**1,174 rows**). Precinct
  IDs are `RIV###` for the recent county-run cycles; `suppressed=True` would mark a redacted
  county cell (**none survive in the final data**).

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source value (never
overwrites raw): collapses whitespace, strips the `(NP)` / `(NON)` non-partisan tag, drops
the leading `*` registered-write-in mark, canonicalizes write-ins. To join elections ↔ votes,
further strip case/suffixes — election names are **UPPER-CASE**, council `all_votes.csv`
names are mixed-case. **Normalize on person identity, and mind the D3↔D4 renumbering above.**

## Verification / cross-checks

- **2020–2023 bench recovered from the 2019 general** (Cycle B): D1 **Sheldon B. Stewart**
  (unopposed, 498), D2 **Troy D. McDougal** (1174 vs Halvorsen 658), D5 **Claude Wells**
  (846 vs Winters 685). McDougal + Haymond (2023) are on the current council.
- **2021 recovered** (Cycle A, all uncontested): McCay (D3) 863, Buroker (D4) 1160, Staggs
  (Mayor) 4973 — matches the county Electionwide-Total rows (D3 1012 ballots / 5033
  registered → 20.11% turnout, etc.).
- **2025** (Cycle A): Mayor **Tish Buroker** def. Tawnee McCay (7687 vs 3284); D3 **Alexander
  A. Johnson** def. Rusty Lance; D4 **Shannon Smith** def. Darren J. Park — the current
  seating, consistent with `recon.md` (and the D3↔D4 caveat: 2025 labels are the *current*
  numbering).

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent (asserts 0 precinct↔candidate mismatches, 0 suppressed contests). Re-run only when
a **new cycle** posts to the county site: add its SOVC to `raw/sovc/`, then either refresh the
canonical slice (`raw/riverton_slco_results_long.csv`) if the county publishes it under a
clean `%RIVERTON%` label, or add a raw-parser call (mirror `parse_2019` / `parse_2021`). Mind
whether the cycle is A (Mayor+D3+D4) or B (D1/D2/D5).

## Gaps / caveats

- **D3↔D4 renumbered at the 2022 redistricting** — see the caveat above; the single most
  important join hazard in this dataset.
- **No 2019 primary** for D1 (Stewart unopposed) — a true no-contest, not a data gap.
- Turnout is populated only where the source carries ballots-cast counts (2021/2023/2025);
  earlier years leave `turnout_pct` blank.
- **Vote-for-1 everywhere** — each council seat is a single-member district; no at-large /
  vote-for-N races and no RCV cycle (Riverton did **not** join the 2021 municipal RCV pilot;
  2021 was plurality — and uncontested).
- Precinct geometry for joins: `../geo/precincts.geojson` (join `PrecinctID` = `RIV###`) +
  `../geo/precinct_to_district.csv`; the city's own council-district layer is the preferred
  geo source (see `../geo/`).
