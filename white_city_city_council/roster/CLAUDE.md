# roster/ — White City rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each White City council + mayor seat
over time** as dated intervals with per-row provenance and confidence. Built 2026-07-13 on
the bluffdale AT-LARGE template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?*

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 20 rows (18 tenures + 2 VACANT) across 5 seats: 15 high / 5 medium / 0 low. |
| `district_versions.csv` | DEGENERATE (all AT-LARGE → one row). |
| `roster_overrides.csv` | Hand-editable correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

## Seat model — 5 AT-LARGE positions the whole time (max roll = 5)

White City was a **Metro Township 2017 → CITY (HB35) effective 2024-05-01**; the first
directly-elected executive Mayor (Allan Perry) + council were seated **2026-01-08**. Five
voting positions throughout. **The presiding officer VOTES in BOTH eras** (the Millcreek
pattern — `non_voting_mayor=False`, kept in `DB_KEY`), NOT the Taylorsville non-voting form.

Two staggered cohorts:
- **Cohort A** (3 seats, elected 2019 / 2023): `MAYOR` (Flint), `AL-A2` (Perry→Huish),
  `AL-A3` (Cutler→Little→Shelton).
- **Cohort B** (2 seats, 2017 / 2021 / 2025 cycle): `AL-B1` (Price), `AL-B2`
  (Dickerson→Cardenaz→Mahoney).

**`seat_id MAYOR` = the presiding-officer chain.** Township era = the peer-selected voting
**Chair** (courtesy-titled "Mayor" per S.B.175, `body=Council`): **Paulina Flint**. City era
= the directly-elected executive **Mayor** (`body=Mayor`): **Allan Perry** (2026). Flint ran
for the executive mayoralty in 2025 and **lost** to Perry, so the presiding seat passes
Flint → Perry cleanly. (Perry also separately held council seat `AL-A2`, 2020-2024 — the same
person, two eras; his 2020-2024 term carries no named vote, honest to the tally-only source.)

Within-cohort seat numbers (A2 vs A3) are a **stable labelling of person-chains**, not
source-attested where two newcomers co-arrive (Huish + Shelton, 2023) — flagged in notes.

## ⚠ The ballot-structure seam (numbered vs grouped) — the load-bearing finding

The metro-township **2019 & 2023** council races were **GROUPED "At-Large" vote-for-3** (4–5
candidates, top 3 win — like bluffdale). The city's **2025** races were **NUMBERED,
single-seat LETTERED contests** (Mayor / At-Large **B** / At-Large **C**). A single city
cannot be both grouped and numbered under `roster_lib`'s one `winners_have_district` flag, so
this driver reconciles the **bluffdale way** (`winners_have_district=False`, chained by
**person**, not by ballot letter). The lettered city seats map onto the cohort chains:
city **B** = `AL-B1` (Price), city **C** = `AL-B2` (Mahoney); city **A/D** (up 2027) =
`AL-A2`/`AL-A3` (Huish, Shelton). Reported to `scripts/roster_HARDENING.md`.

## Oath / transition dates (all minutes-documented)

- **2020-01-02** — oath to re-elected Flint & Perry + newly elected **Scott Little** (2019
  grouped vote-for-3: Little 622 / Perry 589 / Flint 559; Cutler 532 lost).
- **2021-08-05** — **Cardenaz APPOINTED** (Resolution 2021-08-01) to fill Dickerson's seat.
- **2022-01-06** — oath to re-elected Price + newly elected Cardenaz (2021 uncontested).
- **2023-01-05** — **Shelton APPOINTED** (Resolution 23-01-02) to fill Little's seat.
- **2024-01-04** — oath to re-elected Flint & Shelton + newly elected **Huish** (2023 grouped
  vote-for-3: Flint 579 / Shelton 558 / Huish 448).
- **2026-01-08** — oath to **Mayor Allan Perry** (first executive mayor) + Price (At-Large B) +
  **Mahoney** (At-Large C).

## Two documented mid-term vacancies (VACANT-interval convention)

1. **Dickerson (AL-B2) RESIGNED 2021-07-08** ("effective immediately") → VACANT →
   **Cardenaz appointed 2021-08-05**. He was present & voting by 2021-09-02, then won the
   uncontested 2021 general.
2. **Little (AL-A3) DIED Nov 2022** (car accident; last present 2022-10-13, vacancy noticed
   2022-12-01) → VACANT → **Shelton appointed 2023-01-05**, then elected 2023.

## Honest gaps / conventions

- **Pre-2019 layer (`medium`)** — the initial 5-member council (Dickerson, Flint, Price,
  Cutler, Perry; present 2018-01-04) was elected in the **Nov-2016 even-year general**, which
  is NOT in the odd-year election archive (there is genuinely **no 2017 White City contest**).
  Their 2017 term-start = the incorporation floor; the founding election is pre-data → medium.
- **2021 cohort-B general absent from the county SOVC** (uncontested seats carry no tally
  sheet). Price/Cardenaz seatings are anchored to the **2022-01-06 oath** instead → honest
  gap on the tally, not fabricated. The REVERSE crosscheck (H-C, 2026-07-19) flags these two
  2021 elected/reelected tenures for that reason; they are silenced by 2 cited
  `reverse_crosscheck_exceptions` in the driver, so the crosscheck ends clean.
- **Tally-only sparsity** — most motions print no roll; named-vote bounds are thin (Flint 1,
  Cardenaz 1, Perry's 2020-2024 council term 0). `first_vote`/`last_vote` are loose in-window
  activity bounds, not term boundaries. Dickerson & Cutler cast zero named votes → absent
  from `cities.db`, never mapped in `DB_KEY` (the source, not a gap).
- **`end_event=unknown`** for Perry's 2019 council seat — he served the full term and simply
  did not run for council in 2023 (later won Mayor 2025); the end *date* is precise, only the
  mechanism is unrecorded.

## Queries

```bash
python3 roster/build_roster.py --demo   # (a) current roster, (b) as-of date
```
Federated into the repo-root `cities.db` as `term` / `district_version` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
