# roster/ — Emigration Canyon rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Emigration Canyon council + mayor
seat over time** as dated intervals with per-row provenance and confidence. Built on the
alta/nephi at-large + voting-mayor template (`update-council-roster` skill). Answers: *who was
on the council on date X?*, *who is serving now?*, *who represents this address on date D?*
(Emigration Canyon is all at-large → the geographic answer degenerates to the citywide roster).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently (byte-identical re-run). `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 18 tenures (9 high / 9 medium / 0 low), incl. 1 VACANT, across 6 seat_ids (AL-1..AL-5 + MAYOR). |
| `district_versions.csv` | DEGENERATE (all at-large → one row; no wards, no address→district tool). |
| `roster_overrides.csv` | Hand-editable correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

### Correction 2026-07-17 — the recovered 2019 election (16→18 tenures)

The **Nov-2019 general** (3-seat at-large: **Hawkes 300 / Brems 271 / Harris 241**,
canvass-confirmed by the 2019-11-19 Township Board of Canvassers) was recovered 2026-07-17 into
`election_results/emigration_canyon_races.csv` (it had been privacy-suppressed in the county
SOVC, so it is still ABSENT from `*_results_by_candidate.csv`). The roster's pre-recovery
"appointed" labels for these three are now corrected against the **2020-01-23 oath**: *"Nichole
Watt administered the Oath of Office to **re-elect** Council Members Jennifer Hawkes and David
Brems and **newly elected** Council Member Catherine Harris."*
- **Brems (AL-2)** and **Hawkes (AL-3)** are each **SPLIT**: the genuine pre-election appointed
  segment (2018-10-25 → 2020-01-23, `medium`) is retained, then a **2019-elected term**
  (`reelected`, election_year 2019, `high`) begins at the 2020-01-23 oath — a 2018 appointment
  FOLLOWED by a 2019 election, both true.
- **Harris (AL-4)** changes from `appointed`/blank-year/`medium` to **`elected`, election_year
  2019, `high`**: she *won* the seat the appointed Hook (2019-08..12) had briefly held; she was
  not herself appointed. Her start_date (2020-01-23) is unchanged, so the Hook→Harris chain is
  intact.
Vote bounds re-clamped (Brems/Hawkes's 2021/2023 named votes now land in their 2019 terms).
Idempotent; the AL-1 VACANT + all other rows byte-unchanged; forward crosscheck still 0-drift.

## Seat model — 5 at-large seats + a PEER-SELECTED MAYOR role-chain (verified in source)

One **5-member, ALL-AT-LARGE** council spanning a **form change** — **Metro Township**
(incorporated 2017-01-01) → **CITY** (H.B. 35, effective 2024-05-01) — the same body
throughout (vintage carried in each minutes doc's provenance). Seat numbers `AL-1..AL-5` are
**labels for the person-chains** (all at-large → within-body numbering is not source-attested;
flagged in notes).

**The MAYOR is peer-selected** — one of the five members, chosen by the council; **presides
AND votes** (the Millcreek pattern; max roll = 5), NOT an executive non-voter. So
**`non_voting_mayor=False`** → the MAYOR rows carry **real cities.db vote bounds** and the
mayor sits in `db_key`. Because the mayor is one of the five, **`MAYOR` is a ROLE OVERLAY**: a
separate role-chain that runs *alongside* the mayor's own at-large council seat, so the mayor
appears on **two** rows at once (e.g. Brems = AL-2 **and** MAYOR from 2026). This is the one
structural difference from Alta (where the Mayor is a genuinely separate elected 5th seat).

**MAYOR chain:** **Joe Smolka** (2017 → departed end of 2025) → **David Brems** (peer-selected
at the 2026-01-20 reorganization). Smolka presided every recovered meeting (township + city
eras) through 2025-12-15; Brems was sworn Mayor 2026-01-20 (already called "mayor-elect" in the
2025-12-15 minutes). Clean handoff on MAYOR (no meeting occurred in the interim); the mid-term
**vacancy was on Smolka's COUNCIL seat** (AL-1), filled by Griffith.

### The five at-large seat chains (from the meeting-by-meeting present blocks)

| Seat | Chain |
|------|-------|
| `AL-1` | **Smolka** (2017 → 2025-12-15) → **[VACANT]** → **Griffith** (appointed 2026-01-20) |
| `AL-2` | **Brems** (2018-10 → present; peer-selected **Mayor** 2026-01-20, keeps this seat) |
| `AL-3` | **Hawkes** (2018-10 → present; **Deputy Mayor** throughout) |
| `AL-4` | **Paine** (2018-10 → 2019-06) → **Hook** (2019-08 → 2019-12) → **Harris** (2020-01 → present) |
| `AL-5` | **Bowen** (2017 → 2021-12) → **Pinon** (appointed 2022-01 → present; **elected 2025**) |

Current council (5 seats): **Griffith, Brems, Hawkes, Harris, Pinon**; **Mayor = Brems**
(Deputy Mayor = Hawkes).

## The Jan-2026 reorganization (all documented at 2026-01-20)

- **Pinon** sworn to his **2025-elected** term; **Brems** sworn as (peer-selected) **Mayor**
  (*"administered the Oath of Office to Council Member Robert Pinon and Mayor David Brems"*).
- **Smolka departed MID-TERM** (last meeting 2025-12-15; *"Mid-Term Vacancy Public Notice –
  Council Member At-Large"* 2026-01-05). His **at-large seat (AL-1)** was advertised, applicants
  (Erickson, Griffith, Haskell) interviewed, and filled by **written-ballot appointment** of
  **Griffith** (*"the majority vote was for Nicholas Griffith … administered the Oath of Office
  to Nicholas Griffith"*). **Griffith did NOT win a 2025 election** (only Pinon's seat was on the
  2025 ballot). An explicit **`VACANT` interval [2025-12-16, 2026-01-20)** spans the empty seat.

## Confidence & honest gaps (recorded, not filled)

- **`high` (9 rows)** — election-anchored + minutes-seated: the **2019-elected terms** (Brems
  AL-2, Hawkes AL-3, Harris AL-4 — the 2020-01-23 oath + the recovered `_races.csv` 2019 row),
  the 2023 winners' current terms (Brems AL-2, Hawkes AL-3, Harris AL-4), Pinon's 2025 term
  (AL-5), Griffith's documented appointment (AL-1), Brems's documented mayor oath (MAYOR).
- **`medium` (9 rows)** — pre-floor and/or gap-bounded, honestly flagged:
  - **PMN purge (data floor 2017, recovered 2018-10).** Members serving at the first recovered
    meeting (2018-10-25) who are NOT on the 2016 initial slate (Staggers/Raile/Smolka/Bowen/
    Christensen) joined by appointment in the purged 2017–mid-2018 window → the **pre-election
    appointed segment** starts at **2018-10-25** (Brems, Hawkes, Paine). Brems & Hawkes then WON
    the 2019 general → a second, **high** 2019-elected term (above). **Smolka & Bowen** ARE 2016
    founders (+ 2017 re-election in-data) on the OTHER staggered cohort (not up in 2019) → start
    **2017-01-01**, continuous service across the **2019** + **2021** (no township council
    contest) cycles **inferred**.
  - **Appointment chains** (Hook 2019; Pinon 2022) — the appointment *events* are inferred from
    the present blocks (no 2021 election data; Hook was the brief pre-2019-election placeholder
    Harris then won at the ballot); the *service dates* are minutes-documented. Weakest-link →
    medium.
  - **VACANT AL-1 [2025-12-16, 2026-01-20)** — medium: the exact effective resignation date is
    unstated (Smolka last served 2025-12-15) and the window contains the 2026-01-01/2026-01-05
    notices logged as un-recovered, so the departing row carries `vacate_confidence=medium`.
- **No `low`/UNKNOWN rows** — every seat-date maps to a named person; the only VACANT is fully
  bounded. `end_event`: Smolka & Paine & Hook = `resigned` (mid-term departures; Smolka's
  triggered the Griffith appointment); Bowen = `unknown` (departed end 2021, mechanism unstated).

## Vote bounds — NARRATIVE-TALLY ceiling (a user must know)

Emigration Canyon council votes are **narrative-tally**: cities.db names only the five people
who ever cast a **recorded contested/dissent vote** (Brems, Smolka, Harris, Hawkes, Pinon — the
majority stays unnamed on unanimous motions). So **Bowen, Paine, Hook, Griffith carry blank
`first_vote`/`last_vote`** — a **source ceiling, not an extraction gap**. The **MAYOR rows DO
carry bounds** (Smolka 2021-08-24..2023-10-24) — confirming the mayor votes. Bounds are
**clamped to each tenure's own `[start,end)` window**, so Smolka's votes never smear onto
Griffith (AL-1) and Brems's 2021/2023 votes clamp to his pre-2024 AL-2 row (his 2024+ reelected
and MAYOR rows are honestly blank — no named votes cast after 2024).

## Queries

```bash
python3 roster/build_roster.py --demo    # (a) current  (b) as-of 2020-06-01  (c) as-of 2026-01-01 (mid-vacancy)
python3 roster/build_roster.py --check   # validations only
```
Not yet federated into repo-root `cities.db` (run `scripts/build_cities_db.py` to pick up this
`roster/` dir into `term` / `district_version` + `v_council_current`). **⚠ Do not run
`build_cities_db.py` as part of this build** (per the task's hard constraints).
