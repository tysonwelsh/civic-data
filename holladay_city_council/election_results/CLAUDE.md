# election_results — Holladay City municipal elections

Holladay City (**Salt Lake County**, Utah) municipal **general + primary** election results,
normalized to the SLC/South Jordan sibling schema. Three CSVs + a reproducible build script
(`clean_elections.py`). **Do not edit the CSVs by hand — regenerate** (see "Rebuilding").

## Council / mayor structure

Holladay is a **Council–Manager** city: a **5-member council elected by DISTRICT
(Districts 1–5)** plus a **Mayor elected at-large** (citywide). Non-partisan (`(NP)`).
4-year staggered terms, so each odd-year cycle fills only part of the body:

| Cycle | Seats up | Years |
|---|---|---|
| **A** | **Mayor + District 1 + District 3** | 2009, 2013, 2017, 2021, 2025 |
| **B** | **Districts 2, 4, 5** | 2007, 2011, 2015, 2019, 2023 |

The Mayor is elected only on the **A** cycle. (In **2007** the county labelled the B seats
`HOLLADAY CITY COUNCIL 2/4/5`; from 2009 the label drifted through `…COUNCIL DIST N`,
`…CITY CNCL DIST N`, `CITY OF HOLLADAY COUNCIL DISTRICT N` — all normalize to
`Holladay City Council District N`.) **Note:** this is the *opposite* stagger from South
Jordan (where D1 is a B-cycle seat) — in Holladay **D1 + D3 + Mayor** run together.

## Sources

**Primary — the repo-canonical county SOVC normalization**, not re-scraped:
`/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`,
filtered `contest LIKE '%HOLLADAY%'`. Precinct- and vote-method-level. Every year **except
2021** sums cleanly (zero suppression) to contest totals — consumed directly for
**2007, 2009, 2011, 2013, 2015, 2017** (+ their primaries) and the **2023 & 2025** generals
+ the **2025 mayoral primary**. (2025 rows carry a single pre-aggregated `ALL` method; all
earlier years are summed across the county's per-method rows — Absentee/Early/Polls/… — with
no aggregate row to double-count.)

**Raw re-parse** from the local Salt Lake County Clerk SOVC mirror
(`~/Desktop/slco-election-archive` — **not re-downloaded**) for the two contests the
canonical layer does not deliver cleanly:

| Contest | Why the canonical file missed / broke it | Recovery |
|---|---|---|
| **2019 general** (Dist 2/4/5) | **Absent** — the SLCo normalizer keyed the contest off the raw sheet name `HOL Council N`, so a `%HOLLADAY%` filter never matched (the shared gap flagged in `recon.md`). | Re-parsed `raw/historical-election-results/2019-11-05-general-election-sovc.xlsx` (sheets `HOL Council 2/4/5`; wide crosstab, per-candidate `Total Votes` columns). |
| **2021 general** (Mayor/D1/D3) | Present but privacy-**SUPPRESSED** (`****`) at the In-Person / Vote-By-Mail method split — 54 cells — which destroys precinct totals. | Re-parsed `raw/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx` (Sheets 16/17/18), whose per-precinct **`Total`** sub-rows are **not** suppressed. |

After recovery the final CSVs have **zero suppressed cells** and every by-precinct sum
reconciles exactly to its by-candidate total (the build asserts **0 mismatches**).

## Two honest no-contests (logged, not fabricated)

- **No 2019 primary.** The raw 2019 primary SOVC contains **no Holladay sheet** (verified) —
  each Cycle-B seat drew ≤2 candidates, so none triggered a primary.
- **2023 = District 4 only.** The 2023 general SOVC carries **only D4** (Quinn vs Tracy).
  The other two B-cycle seats, **D2 (Matt Durham)** and **D5 (Emily Gray)**, drew a single
  candidate each and were **UNCONTESTED** — Salt Lake County omits uncontested municipal
  seats from the ballot/SOVC, so there is no row to recover (both were declared elected to
  Jan-2028 terms; corroborated by the 2026-02-05 council roster). A true no-contest, not a
  data gap.

## The three CSVs

- **`holladay_races.csv`** — one row per race (**34 races: 28 general + 6 primary**), the
  **25-column** SLC/South Jordan superset (`year, election_type, office, district, contest,
  contest_verbatim, n_seats, n_candidates, voting_method, total_votes,
  total_first_choice_votes, winner, winner_votes, winner_pct, runner_up, runner_up_votes,
  margin_votes, margin_pct, registered_voters, ballots_cast, turnout_pct, uncontested,
  suppressed_precincts, note, source_file`). `total_first_choice_votes` is blank (Holladay
  is **plurality**, not RCV — verified from the 2021 SOVC's single-count layout). `winner`
  is the top vote-getter; for a **primary** row that is the leading advancer, not an
  office-winner. `suppressed_precincts` is `False` on every final row.
- **`holladay_results_by_candidate.csv`** — race × candidate (**84 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`holladay_results_by_precinct.csv`** — precinct × candidate (**960 rows**), `suppressed`
  `False` everywhere. Precinct IDs are county-wide numeric (`4008`, `4020`…) for 2007–2009
  and `HOL###` from 2011 onward.

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source (never
overwrites raw): collapses whitespace, strips the `(NP)`/`(NP )` non-partisan tag, drops the
leading `*` write-in mark, canonicalizes write-ins (`Unresolved Write-In` → `Write-in
(unresolved)`, `WRITE-IN` → `Write-in`). To join elections ↔ minutes votes, further strip
case/suffixes — the council `all_votes.csv` names are mixed-case (e.g. election
`PAUL S FOTHERINGHAM` ↔ minutes `Fotheringham`).

## Verification / external cross-checks

- **Roster continuity → recon.** Mayor chain **Webb (2009) → Dahle (2013 by 88, 2017 & 2021
  unopposed) → Fotheringham (2025)**; D1 **Petersen (2009/13/17) → Brewer (2021) → Sundwall
  (2025)**; D3 **Pignanelli (2009/13) → Fotheringham (2017/21) → Bradley (2025)**; D4
  **Quinn (2019, 2023)**; D2 **Durham (2019)**; D5 **Gibbons (2019)**. Matches `recon.md`'s
  current + prior rosters (Dahle→Fotheringham, Brewer→Sundwall, Fotheringham→Bradley).
- **2013 Mayor** (external): Rob Dahle defeated D. Blaine Anderson by **88 votes** — the CSV
  margin is **88** (Dahle 2476 vs Anderson 2388). Confirmed against news reporting. Note the
  **primary** the same year was *led* by Anderson (1212) over Dahle (1110) before Dahle took
  the general.
- **2025 Mayor** (external, SL Tribune): Fotheringham def. Watts ~**57%/43%** — CSV head-to-
  head 5601 vs 4219 = **57.0%/43.0%** (the 57.04% `winner_pct` counts write-ins in the
  denominator). D1 Sundwall vs Bilstad and D3 Bradley vs Jones confirmed.
- **Closest races:** 2013 Mayor +88 (0.50%), 2009 D3 Pignanelli +48, 2011 D5 Palmer +37,
  2011 D4 Gunn +59, 2021 D1 Brewer +63.

## Rebuilding

```
cd election_results && python3 clean_elections.py            # writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent. Re-run when a **new cycle** posts: refresh the canonical
`slco_municipal_results_long.csv` (or add a raw parser call mirroring 2019/2021). Mind the
cycle — **A** = Mayor+D1+D3, **B** = D2/D4/D5.

## Gaps / caveats

- **Turnout** is populated only where the source carries times-cast counts (**2021, 2023,
  2025**); older canonical-slice years leave `turnout_pct`/`ballots_cast` blank (2009 also
  lacks registered-voter figures). Registered-voter totals are present 2007/2011/2013/2015/
  2017 and the raw-recovered 2019/2021.
- **Vote-for-1 everywhere** — single-member districts + at-large mayor; no at-large/vote-for-N
  and **no RCV** (Holladay did not join the 2021 municipal RCV pilot; 2021 was plurality).
- **Primary `winner` semantics:** the top primary vote-getter, who advanced — not an
  office-holder (see 2013 Mayor).


## 2026-07-17 — 2019 D4 + D5 primaries appended (owner-approved, hand-edited)
Two rows hand-appended to `holladay_races.csv` from the 2026-07-16 SLCo SOVC re-parse
(`2019-08-13-municipal-primary-sovc.xlsx`):
- **2019 primary D4** — Drew B. Quinn 997 / B. Peter Monson 231 / Aspen Perry 175.
- **2019 primary D5** — Lori A. Khodadad 595 / Daniel Bay Gibbons 382 / Chad B Iverson 234
  (Khodadad led the primary but Gibbons won the general).
The 2019 D4/D5 GENERAL rows were already present; these add the missing primaries.
`registered_voters` summed from SOVC precinct rows; `ballots_cast`/`turnout_pct` blank.
Dated backup: `_backups/2026-07-17-audited-election-rows/holladay/`. Kearns precedent;
tallies re-verified twice vs the county layer.
