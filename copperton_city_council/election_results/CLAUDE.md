# election_results — Town of Copperton municipal elections

Town of Copperton (**Salt Lake County**, Utah, ~800 residents) municipal **general**
election results, normalized to the SLC/Sandy/Alta sibling schema. Three CSVs + a
reproducible build script (`clean_elections.py`) + the retained raw county-source slice
under `raw/`. **Do not edit the CSVs by hand — regenerate** (see "Rebuilding"). **As-of:
2026-07-12.**

## Council / mayor structure — AT-LARGE, form changed mid-record

Copperton incorporated as a **metro township** 2017-01-01 and converted to a **Town**
2024-05-01. Council seats are **AT-LARGE** (lettered A–E, but town-wide — **NOT districts**),
non-partisan, staggered 4-year terms:

| Cycle | Seats | Years |
|---|---|---|
| **A/B/C** | 3 at-large seats | 2019, **2023**, 2027 |
| **D/E** | 2 at-large seats | **2017**, **2021**, 2025 |

The **Mayor seat is new with the 2024 town conversion** and was first elected in **2025**
(Sean Clayton, unopposed). Under the town form the Mayor **votes** (max council roll = 5).
Because seats are at-large, every council row carries `district = At-Large`; join elections
↔ votes on **person + year** (no district).

## Source

All results derive from the **canonical Salt Lake County Clerk SOVC** long file —
`salt_lake_county/elections/slco_municipal_results_long.csv` — **not re-scraped**. The
Copperton slice (all **98** `%COPPERTON%` rows) is retained here at
**`raw/municipal_results_long_copperton.csv`** for provenance. `clean_elections.py` filters
that slice to the **genuine council contests only**, aggregates over the precinct×vote-method
long rows, and writes the three CSVs. Precinct is **`COP001`** (Copperton is a single-precinct
town); **no suppression** anywhere in the Copperton data.

## Genuine council contests vs decoys

**Kept (6 council races, 3 cycles):**

| Year | Verbatim contest | Seats | Outcome |
|---|---|---|---|
| 2017 | `COPPERTON MT CNCL @ LRG` | 2 (vote-for-2) | Pazell (111) & Severson (96) won; Baxter (90) lost |
| 2021 | `…COUNCIL AT-LARGE D` | 1 | David S Olsen (89), unopposed |
| 2021 | `…COUNCIL AT-LARGE E` | 1 | **Kevin Severson won as a QUALIFIED WRITE-IN (63) over Ronald Patrick (62) — by 1 vote** |
| 2023 | `…COUNCIL AT-LARGE A` | 1 | Kathleen Ray Bailey (118), unopposed |
| 2023 | `…COUNCIL AT-LARGE B` | 1 | Sean Clayton (98), unopposed |
| 2023 | `…COUNCIL AT-LARGE C` | 1 | Tessa Stitzer (143), unopposed |

**⚠ EXCLUDED decoys** (NOT the Township/Town council — `clean_elections.py` never lists them):
- `2015 COPPERTON METRO TOWNSHIP-CITY` — incorporation ballot question (township-vs-city)
- `2015 COPPERTON MSD` — municipal-services-district formation ballot question
- `2017 COPPERTON IMPROVEMENT DIST` — water/improvement-district board
- `2023 COPPERTON IMPROVEMENT DISTRICT BOARD OF TRUSTEES AT-LARGE` — improvement-district board

## The 2017 vote-for-2 inference (documented, not fabricated)

The county SOVC labeled the 2017 contest only `COPPERTON MT CNCL @ LRG` with a **blank
`vote_for`** — it does not state how many seats. It is modeled as **VOTE-FOR-2** because the
**February-2018 council roster** (Clayton Chair, Pazell Vice-Chair, Bailey Treasurer, Ron
Patrick, Kevin Severson) seats **both Pazell (111) and Severson (96)** from this contest but
**not JP Baxter (90, the first loser)** — i.e. the top **2** won. This is the founding **D/E**
cycle (2017 → 2021 → 2025). The inference lives in the race's `note`; the raw tallies are
untouched. If a primary source later pins a different seat count, re-model here.

## At-large multi-seat convention (matches alta/sandy/logan/nephi siblings)

For a vote-for-N at-large race (only 2017 here):
- `winner` = top vote-getter; `is_winner=True` for the top **`n_seats`** candidates.
- `runner_up` = **first loser** (highest-polling non-winner).
- `margin_votes` = **(last winning seat) − (first loser)** (2017: Severson 96 − Baxter 90 = 6).
- `note` names every seat filled and states the margin convention.

Single-seat contests use plain plurality; single-candidate contests are `uncontested=True`
(winner_pct = 100).

## The three CSVs

- **`copperton_races.csv`** — one row per race (**6 races**, all general; Copperton has never
  triggered a primary). 25-col schema identical to the South Jordan sibling. `total_votes`
  blank / `total_first_choice_votes` = sum of contest candidate votes; `registered_voters`
  populated where the county carried it (2017=409, 2021=486, 2023=450); `ballots_cast` /
  `turnout_pct` left blank (the long file carries no clean per-contest ballots-cast figure —
  not fabricated). `suppressed_precincts=False` everywhere.
- **`copperton_results_by_candidate.csv`** — race × candidate (**9 rows**): `votes`, `pct`,
  `rank`, `is_winner`.
- **`copperton_results_by_precinct.csv`** — precinct × candidate (**9 rows**; single precinct
  `COP001`): `votes`, `suppressed` (all `False`).

## Name normalization

`norm_name()` normalizes each candidate name **alongside** the verbatim source (never
overwrites raw): collapses whitespace, strips the `(NP )` non-partisan tag, and strips the
`Qualified Write In` suffix (Kevin Severson, 2021 seat E). To join elections ↔ votes, further
strip case/suffixes — **election names are UPPER-CASE**; council `all_votes.csv` names are
mixed-case. Copperton is at-large → join key is **person + year** (no district).

## Verification / external cross-check (2026-07-12)

- **2025 first Mayor** — **Sean Clayton ran UNOPPOSED** and was **sworn in 2026-01-21**;
  corroborated by KSL and Deseret News 2025 municipal-candidate roundups and the town's own
  `meet-copperton-council` page. (No county tally exists — see gap below.)
- **2023 winners corroborated by the current roster**: Clayton (seat B) → elected first Mayor
  2025; Bailey (seat A) = current Council Member Kathleen Bailey; Stitzer (seat C) = current
  Mayor Pro Tempore Tessa Stitzer. All match `../recon.md`.
- **2017 winners corroborated**: Apollo Pazell + Kevin Severson both appear on the Feb-2018
  council roster (per PMN / Facebook township records); Pazell's win is independently noted in
  external bios.

## Gaps / caveats

1. **2019 council (A/B/C prior term) — ABSENT** from the county archive (the same 2019 drop
   seen for South Jordan / Millcreek / Taylorsville). Logged, not fabricated. Re-parse the raw
   2019 SOVC if it is ever needed.
2. **2025 Mayor + council D/E — NOT in the county data** at all. Copperton is **entirely
   absent** from the Nov-2025 SLCo SOVC (72-sheet official report) **and** the 2025 Cast-Vote-
   Record (both verified) — because **every Copperton 2025 seat was unopposed** (Clayton Mayor;
   McCalmon seat D; seat E → Pratt), so the county did not tabulate them. The election
   **occurred** (winners are known from the town) but **no county vote total exists** → these
   are documented as a gap, never fabricated into the CSVs.
3. **No primaries** — Copperton has never drawn enough candidates to trigger one.
4. **Turnout** (`ballots_cast`/`turnout_pct`) left blank — the county long file carries no
   clean per-contest ballots-cast figure for Copperton.
5. **Decoys excluded** — MSD, Improvement-District, and 2015 incorporation-question rows are
   NOT council contests (0 in the CSVs).

## Rebuilding

```
cd election_results && python3 clean_elections.py    # reads raw/, writes the 3 CSVs + prints a summary
```
Idempotent. Re-run when a new cycle posts to the county file: refresh
`raw/municipal_results_long_copperton.csv` from the county canonical
(`salt_lake_county/elections/slco_municipal_results_long.csv`, `%COPPERTON%`, keeping the
decoy exclusions), then rebuild. Add the **2025** Mayor/council cycle here once the county
posts Copperton (see gap 2).


## 2026-07-17 — 2019 general At-Large A/B/C appended (owner-approved, hand-edited)
Three rows hand-appended to `copperton_races.csv` from the 2026-07-16 SLCo SOVC re-parse
(`2019-11-05-general-election-sovc.xlsx`), following Copperton's lettered single-seat at-large
convention (A/B/C cycle; `total_first_choice_votes` column, `total_votes` blank):
- **Seat A** (contested) — Kathleen Ray Bailey 156 d. Cheryl Carrigan 64.
- **Seat B** (uncontested) — Sean Clayton 186 (later first Town Mayor 2025).
- **Seat C** (uncontested) — Tessa Stitzer 181.
All three were re-elected uncontested to the same seats in 2023. `registered_voters=426`
(township roll); `ballots_cast`/`turnout_pct` blank. Dated backup:
`_backups/2026-07-17-audited-election-rows/copperton/`. Kearns precedent; re-verified twice.
