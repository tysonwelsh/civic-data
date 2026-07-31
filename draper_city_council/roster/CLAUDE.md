# roster/ — Draper rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Draper council + mayor seat
over time** as dated intervals with per-row provenance and confidence. Built on the
bluffdale/nephi at-large template (`update-council-roster` skill). Answers: *who was on
the council on date X?*, *who is serving now?*, *who represents this address on date D?*
(Draper is all at-large → the geographic answer degenerates to the citywide roster.)

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 16 tenures (13 high / 3 medium / 0 low) across 6 seats. |
| `district_versions.csv` | DEGENERATE (at-large → one row; Draper straddles Salt Lake + Utah counties, but SL County administers the whole election and there are no wards). |
| `roster_overrides.csv` | Hand-editable correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

## Seat model (verified in source)

**5 AT-LARGE council seats on staggered 4-year terms + a separately-elected, NON-VOTING
Mayor** (Utah council–mayor / executive-mayor form; a council roll caps at **5**).
- `AL-A1..A3` — **cohort A, 3 seats** (2015 / **2019** / **2023** cycles).
- `AL-B1..B2` — **cohort B, 2 seats** (2017 / **2021** / **2025**).
- `MAYOR` — Troy K. Walker, on the B calendar (won 2013/2017/2021/2025; mayor since Jan
  2014, after Darrell H. Smith 2010–2013).
Within-cohort seat numbers are a stable labelling of person-chains, **not** source-attested
(flagged in notes). **`non_voting_mayor=True`** → the three MAYOR rows carry **blank vote
bounds**; Walker's single cities.db council vote (2024-10-15, the Ordinance #1625
tie-break, a roll of 6) does not smear.

## Seating dates (first documented meeting of each term, present-block anchored)

- **2020-01-14** — 2019 winners Vawdrey / F. Lowry / Roberts (present block).
- **2022-01-11** — 2021: T. Lowery + Mayor Walker (present block).
- **2024-01-09** — 2023 winners F. Lowry / Roberts / **Bryn Heather Johnson**.
- **2026-01-06** — 2025: Dahlin (2-yr seat) + the canceled-race certifications T. Lowery /
  Green + Mayor Walker (first 2026 meeting; Walker absent, Johnson as Mayor Pro Tem).

## The three findings a user must know

1. **PUZZLE (a) — the "missing seats" are a CANCELED-UNCONTESTED race, NOT a council-size
   change (FLAG → election_results acquisition gap).** Recent county cycles look like only
   4 seats (3+1+3+1), but the council has **always been 5** (roll = 5 every meeting). The
   2025 **regular 2-seat 4-year Council race was CANCELED as uncontested** under Utah Code
   (one of three candidates withdrew, leaving two for two) and **Tasha Lowery + Mike Green
   were certified elected without appearing on the ballot** (Res #25-49; minutes 2025-09-16
   & 2025-10-07: *"canceling the race for the 4-year At-Large City Council seats and
   certifying Tasha Lowery and Mike Green as elected"*). Canceled races never enter the Salt
   Lake County SOVC, so that contest is **ABSENT from `election_results`** (the 2025 file
   carries only the `(2 YEAR TERM) (Vote for 1)` seat, Dahlin/Byington). **This is a
   documented election-data gap, FLAGGED here; not fixed from the roster** (repo doctrine).
2. **PUZZLE (b) — Mike Green's continuity is RESOLVED; his 2021 `is_winner=False` is
   CORRECT, not a defect.** Green won 2017 (B seat). 2021 was a **VOTE-FOR-1** for a single
   open B seat, which Tasha Lowery won (Green placed 3rd, 1,565). Green **retained his own
   B2 seat**, which was **not on the 2021 ballot** (the broken B-cohort stagger —
   `election_results/CLAUDE.md`: "2021 filled only 1 council seat"), served **continuously**
   2020-01-14..2025-12-16 (734 votes), and was **re-elected in 2025** via the same
   canceled-uncontested certification (Res #25-49). The precise mid-term event that took B2
   off the 2021 cycle is **not documented in the 2020+ window** → his B2 t1 is **`medium` +
   flagged**. The Aug-2022 "reappointing Mike Green" (Res #22-43) is the **Audit Committee**,
   not the council (a red herring). No win was fabricated.
3. **PUZZLE (c) — the 2025 by_candidate "duplication" is NOT a defect.** Dahlin appears in
   the 2025 primary (advancer) and general (winner); **Brad Byington's `is_winner=True` at
   32% is his PRIMARY-advancer flag** (the documented `is_winner`="rank ≤ 2N advances"
   convention), and `is_winner=False` in the general (lost 44.39%). Dahlin is the single
   2025 general winner.

## The A2 mid-term vacancy chain (fully documented)

**Cal Roberts** (won 2019 & 2023) **RESIGNED** late 2024 (last council vote 2024-11-12; the
2024-11-19 roll had only 4 voters). **Res #24-60** (minutes 2024-11-19) filled *"the vacancy
… created by the resignation of Cal Roberts"* by **appointing Marsha Vawdrey**, oath
administered the same night (first appointee vote 2024-12-03). **Dahlin** then won the 2025
**2-year unexpired** remainder (verbatim `(2 YEAR TERM)`), seated 2026-01-06.
Vawdrey's earlier **AL-A3** term (won 2015 & 2019) ended 2024-01-09 when Johnson was seated;
her cities.db vote **gap** (2023-12-06 → 2024-12-03) is exactly this out-then-appointed-back
signature (the tenure-window clamp splits her two seats correctly). The ~1-week Roberts
vacancy is chained to Vawdrey's same-night seating (no separate VACANT row; exact
resignation date undocumented, bounded 2024-11-12..2024-11-19).

## Honest gaps / conventions

- **Pre-floor terms (`medium`)**: T. Lowery (AL-B1) & Green (AL-B2) start `2018-01-01`
  (2017 wins, cycle-inferred; Jan-2018 seatings predate the 2020 floor); Mayor Walker's
  AL-MAYOR t1 starts `2018-01-01` (his 2017 term; mayor since 2014, wholly pre-floor before
  that). Vawdrey's 2015 term (2016-2020) is pre-floor and folded into her 2019-anchored
  AL-A3 row (noted, not double-rostered).
- **`end_event=unknown`**: Vawdrey-A3 (not a 2023 candidate) and Vawdrey-A2 (interim
  appointee superseded by the elected Dahlin) — the end *dates* are the documented successor
  seatings; only the mechanism (retire vs decline) is unstated.
- **2021 = the RCV pilot**: stored council figures are FIRST-CHOICE (T. Lowery's 3,105);
  the winner is the RCV final — cited as such.
- **`fred_lowry` ≠ `tasha_lowery`** — two members with near-identical surnames (Lowry vs
  Lowery); **resolve by full name, never surname**.
- **Reverse-crosscheck documented exceptions**: T. Lowery-2025 & Green-2025 are
  minutes-anchored (the canceled race left no `is_winner` row) — like the bluffdale Hales
  pattern. The forward crosscheck (`--check`) prints **zero** unmapped-winner warnings.

## Queries

```bash
python3 roster/build_roster.py --demo   # (a) current roster, (b) as-of 2025-06-01
```
Not yet federated into repo-root `cities.db` (run `scripts/build_cities_db.py` to pick up
this `roster/` dir into `term` / `district_version` + `v_council_current`).
