# election_results — Cottonwood Heights City municipal elections

Cottonwood Heights City (**Salt Lake County**, Utah) municipal **general + primary**
election results, normalized to the SLC/Sandy/South-Jordan sibling schema. Three CSVs + a
reproducible build script (`clean_elections.py`) + the retained raw county source files
under `raw/`. **Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure — **4 districts + a VOTING mayor**

Cottonwood Heights (incorporated 2005) elects a **4-member council by DISTRICT
(Districts 1–4)** plus a **separately elected Mayor (citywide)** who **votes as a full
member of the council** (max council roll-call tally = **5**; this is the OPPOSITE of
Taylorsville / South Jordan, whose mayors do not vote). Non-partisan, 4-year staggered
terms, so each odd-year cycle fills only part of the body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 3 + District 4** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **Districts 1, 2** | (2007,) 2011, 2015, 2019, 2023 |

The Mayor is elected only on the **A** cycle. County contest labels drift across eras —
`COTTONWOOD HEIGHTS COUNCIL 3`, `…CITY CNCL 3`, `Cottonwood Hts Council 1` (2011),
`COT Council 1` (2019), and from 2021 `…COUNCIL DISTRICT N` — but all normalize to
**`Cottonwood Heights City Council District N`**, and the mayor to
**`Cottonwood Heights City Mayor`** (`contest_verbatim` preserves the raw label).

## What is EXCLUDED (not a city council/mayor seat)

`clean_elections.py::keep()` drops three neighbouring contests that share the "Cottonwood"
name but are **not** the city council:

- **Cottonwood Heights Parks & Recreation Service Area** trustee — a separate
  special-service district (`Park & Rec 2` 2017; `…SERVICE AREA DISTRICT 1/2 TRUSTEE`
  2021; `PARKS AND RECREATION TRUSTEE DISTRICT 1` 2025; `COT ParksRec 3` 2019).
- **Cottonwood Improvement Board** trustee — the water/sewer improvement district
  (`Cottonwood Improve Brd Trust-N/S` 2011; `COT Imprv` 2019).
- **COUNTY PROP #6 – ISLAND NO. 1** — a 2015 annexation ballot question, not a seat.

## Source

All results are **Salt Lake County Clerk** SOVC (Statement of Votes Cast) data, from the
local county mirror **`~/Desktop/slco-election-archive`** — not re-scraped. Three
provenance layers are retained under `raw/`:

1. **`raw/municipal_results_long_cottonwood_heights.csv`** — the repo-canonical SOVC
   normalization (`salt_lake_county/elections/slco_municipal_results_long.csv`) filtered
   to rows whose `contest` matches "COTTONWOOD HEIGHTS". Precinct- and vote-method-level,
   **zero suppression**, summing cleanly to contest totals. Consumed directly for
   **2009 / 2013 / 2015 / 2017 generals (+ their primaries), the 2023 general + primary,
   and the 2025 general**. (2021 is present here too but is re-parsed from raw — see below.)
2. **`raw/municipal_2011_general_cottonwood_heights.csv`** — the archive's own 2011
   normalization (`data/municipal/2011_municipal_general.csv`) filtered to CH. The 2011
   seats were labelled **`Cottonwood Hts Council 1/2`**, so a `%COTTONWOOD HEIGHTS%` filter
   on the main long file **misses them** ("Hts" ≠ "Heights"). Recovered here so the
   Cycle-B **2011 D1/D2** general is not a false gap.
3. **`raw/sovc/*.xlsx`** — the true county SOVC spreadsheets, re-parsed for the two
   contests the parsed layers don't deliver cleanly (see next).

## The gaps recovered from raw

| Contest | Why the parsed layer missed / broke it | Recovery |
|---|---|---|
| **2011 general** (D1/D2) | Labelled `Cottonwood Hts Council N` → **absent** from the `%COTTONWOOD HEIGHTS%` long-file slice. | Consumed the archive's own 2011 normalization (`raw/municipal_2011_general_cottonwood_heights.csv`). |
| **2019 general** (D1/D2) | Present in the raw file only under the sheet codes **`COT Council 1/2`** (a Family-A wide crosstab); the archive's `%COTTONWOOD%` normalizer never emitted them → **absent** from the long file. | Re-parsed `raw/sovc/2019-11-05-general-election-sovc.xlsx` for faithful district numbers, candidate names, precinct totals. |
| **2021 general** (Mayor/D3/D4) | Present in the long slice but **462/572 rows privacy-SUPPRESSED** at the In-Person / Vote-By-Mail method split, destroying precinct totals. | Re-parsed `raw/sovc/november-2-2021-general-election-statement-of-votes-cast.xlsx` (`Sheet8`=Mayor, `Sheet9`=D3, `Sheet10`=D4), whose per-precinct **`Total`** sub-rows are **not** suppressed. |

After recovery the final CSVs carry **zero suppressed cells**, and the build asserts **0
reconciliation mismatches** (every by-precinct sum equals its by-candidate total).

Recovered rows carry a provenance sentence in the races `note` column.

## No-primary / no-contest years (logged, not fabricated)

- **No CH primary** exists in **2011, 2015, 2021, 2025** — each district/mayor field
  drew ≤ 2 candidates (or, for a 3-way, none crossed the primary trigger), so no primary
  was held. Primaries: **2009 (D3), 2013 (D3, Mayor), 2017 (D3, D4), 2019 (D1), 2023 (D2)**.
- **CORRECTION (2026-07-17):** a **2019 D1 primary DID occur** (3-way: Case 578 / Petersen 511 /
  McHugh 189) — recovered by the SLCo SOVC re-parse and hand-appended to
  `cottonwood_heights_races.csv` (see dated note). The earlier "no CH sheet in the 2019 primary
  SOVC" finding was a gap in the county slice, now resolved. This closes the campaign-finance
  reconciliation flag in the repo CLAUDE.md (Petersen/Case/McHugh filings). Deborah Case *led*
  the primary but Douglas Petersen won the November general (1057-965).

## The three CSVs

- **`cottonwood_heights_races.csv`** — one row per race (**29: 23 general + 6 primary** after
  the 2026-07-17 SOVC-reparse append of the 2019 D1 primary; was 28),
  the **25-column** collection superset (header identical to `south_jordan_races.csv`,
  incl. the RCV-only `total_first_choice_votes` — blank here, all plurality — and a free
  `note`). `registered_voters`/`ballots_cast`/`turnout_pct` populated where the source
  carries them (2019 raw + 2021/2023/2025); older archive-slice years leave turnout blank.
- **`cottonwood_heights_results_by_candidate.csv`** — race × candidate (**80 rows**).
- **`cottonwood_heights_results_by_precinct.csv`** — precinct × candidate (**1,176 rows**);
  precinct IDs are `COT###`. `suppressed=False` everywhere in the final data.

## Coverage & winners (2009–2025, every odd year)

Full Cycle A + B coverage. Mayors: **Cullimore** (2009, 2013), **Mike Peterson** (2017),
**Mike Weichers** (2021), **Gay Lynn Bennion** (2025). Current district holders:
**D1 Matt Holton** (2023), **D2 Suzanne Hyland** (2023), **D3 Shawn Newell** (2021, 2025),
**D4 Ellen Birrell** (2021, 2025).

## Verification / external cross-check

- **2025 Mayor** (external, KSLTV / SL Trib / electionresults.utah.gov): **Gay Lynn
  Bennion defeated incumbent Mike Weichers ~56–44%** — matches the CSV (Bennion 6,180 /
  57.52% vs Weichers 4,565; pct denominators include write-ins). Weichers "mayor since
  2022" confirms his **2021** win in the data.
- **Roster join** matches `recon.md` and the live Elected Officials page: Holton D1 (2023),
  Hyland D2 (2023), Newell D3 (2021→2025), Birrell D4 (2021→2025), Bennion Mayor (2025).
- Notable close races: **2009 D3** Omer +5 (549–544), **2015 D2** Bracken +65, **2019 D1**
  Petersen +92, **2021 Mayor** Weichers +509 (5-way), **2023 D2** Hyland +67.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent; re-run when a new cycle posts (add its SOVC to `raw/`, then extend the loader —
mirror the 2021/2023/2025 handling; mind whether the cycle is A (Mayor+D3+D4) or B (D1/D2)).

## Gaps / caveats

- **2007 D1/D2 is PRE-FLOOR and NOT included.** The archive's `2007-11-06-…-sovc.xls`
  carries sheets `COTTONWOOD CITY COUNCIL 1/2` (Cottonwood Heights' first Cycle-B election
  after 2005 incorporation), but the label reads "COTTONWOOD CITY" (not "…HEIGHTS") and the
  file is legacy `.xls`. The stated coverage floor is **2009**; 2007 is documented here as a
  recoverable pre-floor backfill, not fabricated in.
- **Vote-for-1 / plurality everywhere** — single-member districts + citywide mayor; no
  at-large / vote-for-N and no RCV cycle (`total_first_choice_votes` blank; CH did not join
  the 2021 municipal RCV pilot).
- Precinct geometry for joins: see `../geo/` (`COT###` precincts, UGRC CountyID 18).


## 2026-07-17 — 2019 D1 primary appended (owner-approved, hand-edited)
The **2019 D1 municipal primary** (Deborah Case 578 / Douglas Petersen 511 / Christopher
McHugh 189) was **hand-appended** to `cottonwood_heights_races.csv` from the 2026-07-16 SLCo
SOVC re-parse (`2019-08-13-municipal-primary-sovc.xlsx`), correcting the prior "no 2019 CH
primary" claim above and closing the repo CLAUDE.md campaign-finance reconciliation flag.
`registered_voters` summed from the SOVC precinct rows; `ballots_cast`/`turnout_pct` blank.
Dated backup: `_backups/2026-07-17-audited-election-rows/cottonwood_heights/`. Only the
race-summary row was added — `results_by_candidate`/`by_precinct` were not extended (the
candidate detail is in the race `note`). Kearns precedent; re-verified twice vs the county layer.
