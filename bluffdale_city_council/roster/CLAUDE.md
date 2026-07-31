# roster/ — Bluffdale rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Bluffdale council + mayor seat
over time** as dated intervals with per-row provenance and confidence. Built 2026-07-12 on
the nephi at-large template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?*

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 15 tenures (13 high / 2 medium / 0 low) across 6 seats. |
| `district_versions.csv` | DEGENERATE (at-large → one row; the Utah-County sliver is unpopulated Camp Williams). |
| `roster_overrides.csv` | Hand-editable correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

## Seat model (verified in source)

**5 AT-LARGE council seats on staggered 4-year terms + a separately-elected Mayor.**
- `AL-A1..A3` — the **3-seat cohort A** (2015 / **2019** / **2023** cycles; winner counts
  confirm 3 every cycle back to 2007).
- `AL-B1..B2` — the **2-seat cohort B** (2017 / **2021** / **2025**).
- `MAYOR` — same cycle as cohort B.
Within-cohort seat numbers are a stable labelling of person-chains, not source-attested
(flagged in notes). **The Mayor does NOT vote in Council except to break a tie, but DOES
vote as Chair of the in-session RDA/LBA boards** → `non_voting_mayor=True`; Hall's
`body='Council'` role rows (2022-11-09..2025-05-14) are her mayoral **tie-breaks**, and
Timothy's role rows are RDA-only — neither is council membership.

## Oath dates (all minutes-documented — every post-floor transition is anchored)

- **2020-01-06** — "Council Members Elect; Traci Crockett, Jeff Gaston, Mark Hales, and
  Dave Kallas" ("four City Council Members sworn in at the same time").
- **2022-01-04** — Mayor-Elect Natalie Hall + Council Members Aston and Crockett
  (Hall's tribute: Timothy's "12 years of dedicated service" → mayor since Jan 2010).
- **2024-01-10** — Austin, Wilding, Lord.
- **2026-01-05** — Smith (legal name "David McKinley McLeod Smith"), Aston ("her third
  swearing in" — corroborating 2018/2022/2026), Hall.

## The two findings a user must know

1. **2019 winner-marking DEFECT in `election_results` — found by this roster build,
   PROVEN by the independent audit, FIXED at source 2026-07-12.** The 2019 cohort-A
   general was a **vote-for-3** (3 winners in 2007/2015/2023 too), but
   `clean_elections.py` carried `N_SEATS=2`, mis-flagging **Mark R. Hales (1,044, 3rd
   of 5) `is_winner=False`** despite his 2020-01-06 oath, exact 4-year service, and 2023
   re-run. `AUDIT.md` F1 proved it mathematically from the raw SOVC: **4,977 candidate
   votes against 2,154 ballots cast** — over the vote-for-2 ceiling in every precinct.
   Fix applied in the elections build (N_SEATS 2→3 + regenerate: Hales winner, runner-up
   Preece, last-winner margin 112), never in the roster (repo override doctrine).
2. **Crockett's 2019 win was a 2-year UNEXPIRED special** (her separate 1,140-v-907
   contest), forced by term arithmetic: her 2021 RCV win must be the full 2022-2025 term
   (service ends Jan 2026, no 2023 win). The seat was won in 2017 by **Alan Jackson**, who
   left at an **unrecoverable pre-floor date** (pre-2020 minutes not held; zero in-window
   votes). Jackson's tenure and any interim appointee are wholly pre-floor → **not
   rostered** (honest gap, documented — never guessed).

## Honest gaps / conventions

- **Pre-floor terms (`medium`)**: Aston's 2018-2021 term and Timothy's 2018-2022 term
  start at `2018-01-01` (cycle-inferred; the actual Jan-2018 oaths predate the minutes
  floor). Timothy's 2010-2017 mayoralty and Kallas' 2018-19 unexpired cohort-A seat
  (won uncontested 2017) are wholly pre-floor → not rostered.
- **`end_event=unknown`** for Kallas, Gaston, Crockett-2025, Timothy — each served the
  full term and simply was not a candidate in the next cycle; the end *date* is the
  successor's oath (precise), only the mechanism (retire vs decline) is unrecorded.
- **2021 = the RCV pilot**: stored election figures are FIRST-CHOICE totals; winners
  (Aston seat 1, Crockett seat 2, Hall) are the RCV final — cited as such.
- **OCR junk person rows** in cities.db (`kauas`, `crocket`, `wuding`, `astin`…) carry
  zero votes and are never mapped in `DB_KEY`.

## Queries

```bash
python3 roster/build_roster.py --demo   # (a) current roster, (b) as-of date
```
Federated into the repo-root `cities.db` as `term` / `district_version` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
