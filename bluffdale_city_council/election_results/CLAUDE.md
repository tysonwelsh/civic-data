# election_results — Bluffdale City municipal elections

Bluffdale City (**Salt Lake County**, Utah) municipal **general + primary** election
results, normalized to the collection's 25-column race schema (header identical to
`south_jordan_city_council/election_results/*_races.csv`). Three CSVs + a reproducible
build script (`clean_elections.py`) + retained raw county sources under `raw/`.
**Do not edit the CSVs by hand — regenerate** (see "Rebuilding"). Coverage: **2007–2025**
(every odd-year municipal cycle).

## Council / mayor structure — MAYOR + 5 AT-LARGE (no districts)

Bluffdale is a **six-member mayor–council** city: a **Mayor** elected citywide + **5
Council Members, ALL at-large** (there are **no districts**). 4-year staggered, non-partisan
terms. Because the council seats are at-large and multi-seat, most council contests are
**vote-for-N** (top-N-elected). The Mayor **presides but does not vote** on ordinary
motions (see the repo `recon.md`); that concerns vote extraction, not elections.

| Cycle | Seats up | Years |
|---|---|---|
| **Mayor year** | **Mayor + 2 council seats** | 2009, 2013, 2017, 2021, 2025 |
| **Council-only year** | **3 council seats** | 2007, 2011, 2015, 2019, 2023 |

Plus mid-cycle **"2-YEAR" (unexpired-term) at-large vacancy** contests in **2017** (Kallas)
and **2019** (Crockett) — filled alongside the regular seats that year, keyed in the data as
`Bluffdale City Council At-Large (2-Year)`.

**Seat counts are DATA-VERIFIED, not assumed** — from the SOVC "Vote for N" headers, the
per-contest votes/ballots ratio, and external cross-checks (see the `N_SEATS` table in
`clean_elections.py`). Examples: 2021 council ratio ≈1.0 first-choice (RCV); 2023 ≈2.4
(vote-for-3 w/ undervoting); 2025 ≈1.8 (vote-for-2).

## The 25-column race schema + at-large multi-seat conventions

Columns (exact superset, matches the federated `cities.db` `election_race`):
`year, election_type, office, district, contest, contest_verbatim, n_seats, n_candidates,
voting_method, total_votes, total_first_choice_votes, winner, winner_votes, winner_pct,
runner_up, runner_up_votes, margin_votes, margin_pct, registered_voters, ballots_cast,
turnout_pct, uncontested, suppressed_precincts, note, source_file`.

Because council seats are **at-large / multi-winner**, the single-winner columns follow the
**Sandy at-large sibling** convention:
- **`winner`** = the single top vote-getter (rank 1). **`district`** = `At-Large`.
- **`runner_up`** = the **first loser** (rank `n_seats+1`); **`margin_votes`** =
  **last-winner (rank `n_seats`) − first-loser** — i.e. how close the **cutoff for the last
  seat** was, NOT winner−runnerup. (For single-seat contests this reduces to the usual
  winner−runnerup.)
- **`note`** carries the **full winning slate** (all `n_seats` winners w/ votes) for
  multi-seat generals, plus any RCV caveat and primary advancement rule.
- **`total_first_choice_votes`** = sum of all candidate votes (denominator for `winner_pct`);
  **`total_votes` is left blank** (mirrors Sandy — for a vote-for-N contest the candidate sum
  is not a ballot count). The **full winner list per contest lives in
  `..._results_by_candidate.csv`** where **`is_winner=True` flags the top `n_seats`** (so all
  seat winners are recoverable, not just rank 1).
- **Primaries:** `margin_votes` is measured at the **advancement cutoff** (top `2×seats`
  advance); the `note` says `top N advance` (or `all candidates advanced` when the field ≤
  the cutoff). `is_winner` is **False for all primary rows** (primaries elect no one).

## The three CSVs

- **`bluffdale_races.csv`** — one row per race (**25 races: 17 general + 8 primary**).
- **`bluffdale_results_by_candidate.csv`** — race × candidate (**124 rows**): `votes`, `pct`,
  `rank`, `is_winner` (top `n_seats` for generals).
- **`bluffdale_results_by_precinct.csv`** — precinct × candidate (**977 rows**). Precinct IDs
  are county SOVC codes: `3801–3806` (2007–2015), `BLF001…BLF013` (2017–2025). `suppressed`
  marks a redacted county cell (none survive after the 2021 raw re-parse).

## Sources & the two recoveries (all Salt Lake County Clerk SOVC)

**Salt Lake County administers and reports ALL Bluffdale results.** Bluffdale's Utah-County
portion is Camp Williams / undeveloped and **essentially unpopulated**, so — unlike Draper —
there is **no separate Utah-County Bluffdale race**; the SLCo SOVC is the complete record.
(No Utah-County SOVC was available on disk to re-scan; the two-county close-out rests on the
established Camp Williams / unpopulated finding in `recon.md` + the geo layer, which shows the
Utah-county slice as precinct `25BL01` + a `25NW04` sliver.)

1. **`raw/municipal_results_long_bluffdale.csv`** — the collection-wide canonical SOVC
   normalization filtered to Bluffdale (2,572 rows). Consumed for **2007, 2009, 2011, 2013,
   2015, 2017, 2023, 2025** (generals + primaries). Method rows are summed per candidate; the
   **2023 primary rows are TRIPLICATED** (each (precinct,candidate) repeated 3× identically)
   and de-duplicated on read.

2. **`raw/sovc/*.xlsx`** — true county SOVC workbooks, re-parsed directly for the two things
   the canonical layer does not deliver:

   | Contest | Why | Recovery |
   |---|---|---|
   | **2019 general + primary** (4-YEAR = **3 seats** — corrected from 2 on 2026-07-12, see below; 2-YEAR = 1 seat) | **ABSENT** from the canonical long file (0 Bluffdale rows — the normalizer keyed the contest off the sheet name `BLF Council …`, so a `%BLUFFDALE%` filter never matched). **This is the recon-flagged 2019 gap.** | Re-parsed `2019-11-05-general-election-sovc.xlsx` (`BLF Council - 4 yr` / `- 2 yr`) and `2019-08-13-municipal-primary-sovc.xlsx` (sheets `2`/`3`). Recovers a **genuine 2019 primary** (it DID occur, both contests). |
   | **2021 general** (Mayor + Council) | Present in the long file but with **method-split privacy suppression**. | Re-parsed `november-2-2021-general-election-...xlsx` (Sheet4 Mayor, Sheet5 Council) from the per-precinct **Total** rows (not suppressed) → clean, higher totals than the suppressed slice. |

**⭐ 2021 was the Utah RCV pilot.** The 2021 council at-large contest was **2-seat
ranked-choice** (`voting_method=RCV`); the stored candidate figures are **FIRST-CHOICE
totals** only. The two RCV winners were **Wendy Aston (seat 1)** and **Traci Crockett
(seat 2)** — recorded in the `note`. (First-choice order alone shows Crockett ahead of Aston;
the sequential-RCV rounds awarded seat 1 to Aston. Take 2021 council winners from the note /
external canvass, not from raw first-choice rank.) 2023 and 2025 held primaries → **not RCV**
(plurality). **2021 Mayor** was 2-candidate (RCV first round decisive).

**EXCLUDED:** `BLUFFDALE CITY PROPOSITION #13` (2023) — a ballot **proposition**, not a
council/mayor candidate race; logged here, not fabricated into the candidate schema.

## Name normalization

`norm_name()` normalizes each candidate name alongside the verbatim value (never overwrites):
collapses whitespace, strips the `(NP)`/`(NON)`/`(NP )` non-partisan tag, canonicalizes
write-ins to `Write-in` / `Write-in (unresolved)`. Election names are **UPPER-CASE**; to join
elections ↔ votes, further strip case/suffixes (council minutes names are mixed-case).

## Verification / external cross-check (2026-07-12)

External cross-check (KSL/Deseret/Salt Lake Tribune/Ballotpedia + the city's roster) **passes
with exact vote matches**:
- **Mayor Natalie Hall** — won **2021** (2,497 vs John Roberts 806, 75.6%) and **2025** (1,993
  vs **Connie Pavlakis** 1,927, margin 66) — 2025 figures match SLTrib/KSL **exactly**.
- **2025 council** (2 seats) — **Wendy Aston 1,959 + Mackey Smith 1,860** win; Steele 1,738,
  Larsen 1,651 — matches news **exactly**.
- **2023 council** (3 seats) — **Steve Austin, Gregory Wilding, Alan Lord** win; **Mark Hales
  first loser by 10 votes** (1,397 vs 1,387). Matches the city roster (Austin/Lord/Wilding,
  2024–2027 terms).
- **2021 council** (2-seat RCV) — **Aston + Crockett** win (SLTrib: "Aston … first seat,
  Crockett … second"). Resolves the roster question (Aston served 2022–2025 via the 2021 win).
- **⚠ 2019 4-YEAR contest was VOTE-FOR-3, not 2 — corrected 2026-07-12** (roster
  `AUDIT.md` F1): the raw SOVC records **4,977 candidate votes against 2,154 ballots
  cast** — impossible under vote-for-2 (cap 4,308), over the ceiling in **every**
  precinct — and the 2020-01-06 oath minutes seat Kallas, Gaston AND **Mark Hales** as
  Council Members-Elect (cohort A elects 3 in 2007/2015/2023 as well). `N_SEATS` fixed
  2→3 in `clean_elections.py` + regenerated: Hales `is_winner=True`, runner-up
  **Preece**, last-winner margin **112** (Hales 1,044 over Preece 932; the old "margin
  10 Kallas/Gaston over Hales" reading was an artifact of the wrong seat count).
- Notable squeakers: **2017 margin 4** (Jackson/Aston over Robbins), **2011 margin 8**
  (Pehrson/Kartchner/Nielsen over Briggs).

## Rebuilding

```
cd election_results && python3 clean_elections.py            # reads raw/, writes the 3 CSVs
                       python3 clean_elections.py --report    # + per-race summary
```
Idempotent. Re-run when a new cycle posts: add its SOVC to `raw/` (refresh the Bluffdale
slice from the canonical long file, or drop the raw xlsx in `raw/sovc/`), set the seat count
in `N_SEATS`, and mind whether it is a Mayor year (Mayor+2) or council-only year (3 seats),
plus any 2-year vacancy contest.

## Gaps / caveats

- **2019 recovered** from raw (was a canonical-file gap) — now complete (general + primary,
  4-YEAR and 2-YEAR contests).
- **2021 council is RCV first-choice only** — winners are the two RCV winners (Aston,
  Crockett), NOT a first-choice top-2 read; see the `note`.
- **`total_votes` is blank; use `total_first_choice_votes`** as the vote-sum / pct
  denominator (at-large multi-seat convention, per Sandy).
- **`margin_votes` is the last-seat cutoff margin** (last-winner − first-loser), not
  winner−runnerup. For the full winning slate use the `note` or `is_winner` in
  `..._results_by_candidate.csv`.
- **Two-county:** SLCo administers/reports everything; the Utah-county portion (Camp Williams)
  is unpopulated — no Utah-County Bluffdale race exists. No Utah-County SOVC was on disk to
  re-scan (reasoned close-out, per `recon.md` + geo).
- **Turnout** is populated only where the source carries registered-voter / ballots-cast
  counts (2021, 2023, 2025); older years leave `turnout_pct` blank. `registered_voters` is
  present for most council-contest years (SOVC precinct reg totals).
