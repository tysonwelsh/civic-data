# election_results — Kearns municipal elections

Kearns (**Salt Lake County**, Utah) municipal **general** election results, normalized to
the SLC/South-Jordan sibling schema. Three CSVs + a reproducible build script
(`clean_elections.py`) that parses the retained **Salt Lake County Clerk SOVC** workbooks.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Two regimes (a hard structural seam at Nov 2025)

Kearns changed form of government between cycles — the election data straddles both:

| Era | Body | Seats on the ballot |
|---|---|---|
| **Metro township** (founding 2016 → 2023) | 5-member Township Council, **numbered single-member districts 1–5**, no mayor (council elected its own chair; MSD supplied executive services) | staggered — see below |
| **City** (incorporated 2024-05; first city election **2025-11-04**) | **directly-elected Mayor + 4 district Council Members**; ⚠ **the mayor VOTES** (Millcreek-style) | Mayor + District 2 + District 4 |

### Cycle / stagger
The founding **2016** general (even year, presidential turnout ~75%) elected **all five**
township seats at once, on split initial terms to establish the odd-year stagger:

| Cycle | Seats up | Years |
|---|---|---|
| **Even seats** | Township **D2 + D4** → City **D2 + D4** | 2016(short), 2017, 2021, **2025** |
| **Odd seats** | Township **D1 + D3 + D5** | 2016(short), 2019, 2023 |

So **2025 elected only Mayor + D2 + D4**. The two **odd-seat holdovers who won township
D1/D3 in 2023 (Schaeffer, Butterfield) carried their unexpired terms into the new City
D1/D3 seats** — which is why those two are sitting council members with **no 2025 race**.
City **D1 & D3 are next up ~2027** (not yet held → an honest coverage edge, not a gap).

**All 18 general races are single-seat, `plurality`, `Vote for 1`.** There are no at-large
multi-seat council contests and no RCV cycle (Kearns did not join the municipal RCV pilot).

## Source — parsed DIRECTLY from the raw county SOVC

Canonical source: **Salt Lake County Clerk SOVC**, taken from the local mirror
`~/Desktop/slco-election-archive/raw/` (not re-scraped). **The county's own normalized
long file** (`salt_lake_county/elections/slco_municipal_results_long.csv`) is **NOT reliable
for Kearns** and is deliberately bypassed here:

- **2019 is entirely absent** from the long file (the archive normalizer dropped the
  `KRN Council N` wide-crosstab sheets).
- **2025 is corrupted** — the long file's `SheetNN`→contest mapping drifted, merging foreign
  municipalities' candidates under "CITY OF KEARNS MAYOR" (e.g. Nordfelt/Roggenbuck, who are
  not Kearns candidates). The `sheet` labels are generic `SheetNN` for 2021/2023/2025.

`clean_elections.py` therefore parses each raw workbook by **sheet content**, handling the
three distinct SOVC layouts the county used over time:

| Format | Years | Workbook | Layout |
|---|---|---|---|
| **A** | 2016, 2017 | `…general…-statement-of-votes-cast.zip` (SLCo_16G / SOVC_17 xlsx) | one row per precinct×vote-type; candidate totals read off each precinct's `Type=Total` row |
| **B** | 2019 | `2019-11-05-general-election-sovc.xlsx` | wide crosstab, one sheet per district (`KRN Council N`); candidate total = the `Total Votes` column of each candidate's 4-col group |
| **C** | 2021, 2023, 2025 | `…2021…xlsx` · `…2023…5.22pm.xlsx` · `2025-general-election-statementofvotescastrpt.xlsx` | Clarity page-per-contest; per-precinct `Total` sub-row (2021/23) or direct precinct row (2025); grand total = `Electionwide - Total` |

**2021 privacy suppression:** the In-Person / Vote-By-Mail method split is `****`-redacted
in D2 & D4, but the per-precinct **`Total`** sub-rows and the `Electionwide - Total` are
**not** — so the parser recovers full contest and precinct totals (`suppressed_precincts`
is `False` in the final data; the method-level redaction never reaches the output grain).

## The three CSVs

- **`kearns_races.csv`** — one row per race (**18 generals: 1 mayor + 17 council**),
  the 25-column superset shared with South Jordan. `office`/`district`/`contest` (canonical)
  + `contest_verbatim`, `n_candidates`, `total_votes`, `winner`/`winner_votes`/`winner_pct`,
  `runner_up`/…, `margin_votes`/`margin_pct`, `registered_voters`/`ballots_cast`/`turnout_pct`
  (2019 has no ballots-cast column → blank; all others populated), `uncontested`,
  `suppressed_precincts` (`False` everywhere), `note`, `source_file`.
- **`kearns_results_by_candidate.csv`** — race × candidate (**31 rows**): `votes`, `pct`,
  `rank` (by raw votes), `is_winner`.
- **`kearns_results_by_precinct.csv`** — precinct × candidate (**164 rows**). Precinct IDs
  are `KRN###`. `suppressed=True` would mark a redacted county cell (none survive).

## Name / winner conventions

- Candidate names are the verbatim UPPER-CASE SOVC spelling with the `(NP)`/`(NON)`
  non-partisan tag and the `Qualified Write In` suffix stripped; generic scattered write-ins
  canonicalize to **`Write-in`**.
- **`Write-in` is never marked `is_winner`** — the aggregate is not a single person. In
  **2017 D4** the aggregate write-in (43) outpolled the lone named candidate **Tina Snow
  (15)**; Snow is recorded as the certified winner (see that row's `note`; `margin_votes`
  is negative there by construction).
- To join elections ↔ council votes: match on **person + year + district**; election names
  are UPPER-CASE — normalize case/suffixes first (the roster/minutes use mixed case).

## Verification / cross-checks

- **All five current officials trace to this data**: Mayor **Jesse Valdez** (2025, 57.6% —
  first Hispanic mayor in Utah), **Lyndsay Longtin** (D2, 2025), **Lorrin Colby Jr.** (D4,
  2025), **Patrick Schaeffer** (won township D1 2023 → City D1 holdover), **Chrystal
  Butterfield** (won township D3 2023 → City D3 holdover).
- **2023 D1 — certified-vs-election-night flip (validates using the certified SOVC):**
  election-night press (KSL) reported **Valdez ahead 191–184**; the **official Dec-5-2023
  canvassed SOVC has Schaeffer winning 212–209** (mail ballots counted after election night
  flipped it). Schaeffer's sitting D1/D3 seat confirms the certified result; Valdez then won
  the 2025 mayoralty. This repo uses the **certified** figures throughout.
- Closest races: **2023 D1** Schaeffer +3, **2021 D2** Peterson +4 (two qualified write-ins),
  **2019 D1** Schaeffer +7.

## Rebuilding

```
cd election_results && python3 clean_elections.py   # reads the archive raw/, writes the 3 CSVs
```
Idempotent (verified byte-identical on re-run). Re-run when a new cycle posts: add its SOVC
to `~/Desktop/slco-election-archive/raw/` and, if the county workbook uses a new layout, add
a parser call (mirror the Format-C 2025 handling). Mind the cycle: **2027 = City D1 + D3**
(Mayor/D2/D4 are on the 2029 cycle).

## Gaps / caveats

- **Generals only.** Municipal primaries (e.g. the Aug-2025 four-way mayoral primary that
  narrowed to Valdez vs Snow) are **not** ingested — the general is the seat-determining
  contest. Noted, not fabricated.
- **City D1 & D3 have no election yet** (first up ~2027) — the 2025 ballot carried only
  Mayor/D2/D4. This also limits the geo district derivation (see `../geo/CLAUDE.md`): the
  2025 SOVC authoritatively assigns **D2 & D4** precincts but does **not** reveal the D1/D3
  split.
- **Pre-2016 is out of scope / non-existent.** The 2015 ballot held only the incorporation
  question + the MSD service-district question (both **decoys**, excluded); Kearns had no
  council before the 2016 founding election. Other excluded Kearns-named decoys: **Oquirrh
  Park Board of Trustees** (recreation district), **Kearns Improvement District** (water),
  **Kearns MSD**.
- Turnout uses `ballots_cast / registered_voters`; 2019's SOVC omits a ballots-cast column
  → `turnout_pct` blank that year only.
- Precinct geometry for joins: `~/Desktop/slco-election-archive/geo/` (join `PrecinctID`);
  city-era council-district polygons derived in `../geo/`.


## 2026-07-17 — 2019 D3 primary appended (owner-approved, hand-edited)
The **2019 D3 primary** (Chrystal Butterfield 191 / Ruby Brown 103 / Christopher J Geertsen 67)
was hand-appended to `kearns_races.csv` from the 2026-07-16 SLCo SOVC re-parse
(`2019-08-13-municipal-primary-sovc.xlsx`). The 2019 D3 general was already present.
`registered_voters` summed from SOVC precinct rows; `ballots_cast`/`turnout_pct` blank.
Dated backup: `_backups/2026-07-17-audited-election-rows/kearns/`. Kearns precedent (same city
that established the convention); re-verified twice vs the county layer.
