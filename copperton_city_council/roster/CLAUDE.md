# roster/ — Town of Copperton rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Copperton council + mayor seat
over time** as dated intervals with per-row provenance and confidence. Built 2026-07-13 on
the bluffdale AT-LARGE template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?*

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 18 rows (17 tenures + 1 VACANT) across 5 seats: 13 high / 5 medium / 0 low. |
| `district_versions.csv` | DEGENERATE (all AT-LARGE → one row; single precinct COP001). |
| `roster_overrides.csv` | Hand-editable correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

## Seat model — 5 AT-LARGE positions the whole time (max roll = 5)

~800-pop town, **sparse by design** (~11-12 mtgs/yr) and almost entirely narrative-tally.
Metro Township **2017 → TOWN (HB35) effective 2024-05-01**; the first directly-elected Town
Mayor (Sean Clayton) was seated **2026-01-21**. Five voting positions throughout. **The
presiding officer VOTES in BOTH eras** — the Chair is titled "Mayor" (S.B.175) and appears in
the roll (`non_voting_mayor=False`, kept in `DB_KEY`): verified 2018-07-18 ("Mayor Clayton
voting Aye" as the 5th roll) and 2020-03-18 ("Mayor Clayton voted Nay" in a 3-2 split).

Five AT-LARGE seats (lettered A-E, **town-wide — NOT districts**), two cohorts:
- **Cohort A/B/C** (3 seats, 2019 / 2023): `AL-A` (Bailey), `MAYOR` (=former At-Large B,
  Clayton), `AL-C` (Patrick→Stitzer).
- **Cohort D/E** (2 seats, 2017 / 2021 / 2025): `AL-D` (Pazell→Olsen→McCalmon), `AL-E`
  (Severson→Pratt).

**`seat_id MAYOR` = the presiding-officer chain (the former township At-Large B seat).**
**Sean Clayton carries it continuously**: `body=Council` (peer-selected Chair/"Mayor", VOTES)
through 2025, then `body=Mayor` (directly-elected Town Mayor) from 2026-01-21. Because the
**same person** carries the role across the seam, the chain closes with no absorbed/orphan
seat. The presiding officer is **peer-selected** from the council in the township era (no
separately-elected mayor); the 2024 town conversion made the mayoralty a directly-elected
office ("the mayor's seat would become an elected office going forward" — 2024-01-17 minutes).

## Oath / transition dates (all minutes-documented)

- **2019-11-19** — canvass names the 2019 A/B/C winners verbatim: **At-Large A Bailey /
  At-Large B Clayton / At-Large C Stitzer** (terms commence Jan 1).
- **2020-11-18** — **Olsen APPOINTED** to fill Pazell's seat (from applicants Green & Olsen).
- **2022-01-19** — oath to **Olsen** (elected 2021 seat D); Clayton elected Mayor, Stitzer
  Deputy Mayor.
- **2024-01-17** — oath to re-elected Clayton, Stitzer, Bailey (2023 A/B/C, all unopposed).
- **2026-01-21** — oath to **Mayor Clayton** (first Town Mayor) + **McCalmon** (seat D) +
  **Pratt** (seat E).

## One documented mid-term vacancy (VACANT-interval convention)

**Pazell (AL-D) RESIGNED** (announced 2020-10-21, moved away; last present/vote 2020-09-16)
→ VACANT → **Olsen appointed 2020-11-18** (first vote 2020-12-16), then elected 2021.
(Patrick→Stitzer on AL-C chains directly — Patrick's final meeting 2019-12-18, Stitzer seated
2020-01-01 — no vacancy.)

## Honest gaps / conventions

- **2017-02 → 2018-06 PMN purge** — a GENUINE retention purge (files 404); earliest recovered
  minutes **2018-07-18**. The founding council's exact seating is in this gap → the initial
  A/B/C tenures start at the incorporation floor (2017-01-01, `medium`) and the D/E tenures at
  the 2017-election → Jan-2018 seating (`medium`); the pre-seating founding year is not
  rostered (honest gap), never fabricated.
- **2019 A/B/C general absent from the county SOVC** (same 2019 drop as South Jordan /
  Millcreek / Taylorsville) — BUT the **2019-11-19 minutes canvass** names all three winners,
  so those seatings are `high` (minutes-anchored), not a gap.
- **2025 Town Mayor + seats D/E were UNOPPOSED and NOT tabulated by the county** — Clayton,
  McCalmon, Pratt are anchored to the **2026-01-21 oath** (`high` on the seating); the tally
  is an honest gap. Corroborated 2026-07-19: the Town Clerk's **Certified List of Candidates
  (published 2025-06-09)** lists Mayor Clayton + At-Large Seat D McCalmon (both unopposed) and the
  **2025-10-15 minutes** name **Pratt "Council Member Elect"** who "begins service in January
  following a **canceled election in which all candidates had run unopposed**" (Utah Code
  20A-1-206). So Pratt was **ELECTED unopposed, not appointed** — this supersedes the
  finance/COI layer's "Pratt was appointed" inference (that read the June certified-list snapshot,
  which showed the open non-mayor seats as **C** ["No Candidate Declarations" at that date] + D,
  before Pratt's later unopposed filing closed the seat). ⚠ **NEEDS-OWNER (orthogonal to the
  roster's reverse-crosscheck, which keys on `body`):** the certified list letters the 2025 cycle
  as seats **C + D**, whereas this roster models the town-era cohorts as **A/B/C (2023) + D/E
  (2025)** and places Pratt on **AL-E** (succeeding Severson). The person-chains are consistent,
  but the town-era HB35 seat-**lettering** (does Pratt hold C or E? did the 4-council-seat town
  re-letter the township A–E seats?) is unresolved and left for owner adjudication — not
  restructured here.
- **H-C reverse-crosscheck documented exceptions (2026-07-19)** — the 6 `elected`/`became-mayor`
  tenures with no by_candidate winner row (2019 A/B/C absent-from-SOVC; 2025 canceled-unopposed)
  are curated, cited exceptions in `build_roster.py` (`reverse_crosscheck_exceptions`); the
  crosscheck ends clean.
- **Kevin Severson won seat E in 2021 as a qualified WRITE-IN by 1 vote** over Ron Patrick
  (63-62) — recorded in the sources.
- **Tally-only sparsity** — 3-8 named votes per member over years; `first_vote`/`last_vote`
  are loose in-window activity bounds, not term boundaries. McCalmon casts no named vote yet →
  absent from `cities.db`, never mapped in `DB_KEY` (the source, not a gap).
- **`end_event=unknown`** for Patrick (seat C), Olsen (seat D), Severson (seat E) — each
  simply did not continue at the next cycle; the end *date* is precise, the mechanism unstated.

## Queries

```bash
python3 roster/build_roster.py --demo   # (a) current roster, (b) as-of date
```
Federated into the repo-root `cities.db` as `term` / `district_version` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
