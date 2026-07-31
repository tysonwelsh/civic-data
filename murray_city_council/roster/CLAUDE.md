# roster/ — Murray rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Murray council + mayor seat over
time** as dated intervals with per-row provenance and confidence. Built 2026-07-12 on the
west_jordan district template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?*

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — 24 tenures (16 high / 8 medium / 0 low) across 6 seats, incl. **4 VACANT** intervals. |
| `district_versions.csv` | 5 districts × 2 plans (the 2022 redistricting) + a Mayor citywide row. |
| `district_precincts.csv` | Versioned precinct→district composition (plan_2022 from `geo/precinct_to_district.csv`, source_year 2023; plan_pre2022 = honest GAP rows). |
| `roster_overrides.csv` | Hand-correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

## Seat model (verified in source)

**Council–mayor (executive-mayor) form: 5 DISTRICT council seats (D1–D5, no at-large) + a
separately-elected executive Mayor who does NOT vote** (`non_voting_mayor=True` → MAYOR rows
carry EMPTY vote bounds; a full council roll tops out at 5). Staggered 4-year cycles:

| Cohort | Seats | Elected | Seated |
|---|---|---|---|
| **A** | D1, D3, D5 | 2019 / 2023 | Jan 2020 / 2024 |
| **B** | D2, D4 | 2021 / 2025 | Jan 2022 / 2026 |
| **Mayor** | MAYOR | 2021 / 2025 | Jan 2022 / 2026 |

Seating dates (first documented January council meeting = first cities.db vote): **2020-01-07,
2022-01-04, 2024-01-02, 2026-01-06**. Murray's own election data floor is **2021** — the
2019-cohort seatings at the 2020 minutes floor are **pre-floor** (their win is not in the
loaded election file) → `confidence=medium`, no fabricated election row.

## Current roster (as of the 2026-01-06 seating)

| Seat | Member | Since | Elected | Conf |
|---|---|---|---|---|
| D1 | Paul Pickett | 2024-01-02 | 2023 | high |
| D2 | Pamela Cotter (Council Chair) | 2026-01-06 | 2025 | high |
| D3 | Clark Bullen | 2026-01-06 | 2025 (2-yr special) | high |
| D4 | Diane Turner | 2026-01-06 | 2025 (uncontested) | high |
| D5 | Adam Hock (Vice-Chair) | 2024-01-02 | 2023 | high |
| MAYOR | Brett Hales (non-voting) | 2026-01-06 | 2025 | high |

Matches the 2026-01-06 attendee header verbatim.

## The distinctive surface (spot-checked against source minutes)

- **Brett Hales: D5 councilmember → Mayor.** Won D5 in 2019 (pre-floor); cast 190 D5 votes
  2020-01-07..2021-12-07; won the **2021 mayoralty** and took office 2022-01-04, vacating D5.
  His unexpired D5 term (to Jan 2024) was filled by the **interim Garry Hrechkosy** (appointed
  at the 2022-01-31 special meeting, *"resolution appointing Mr. Hrechkosy as Interim Murray
  City Council Member"*; header-attested "District #5"). Then Adam Hock (elected 2023).
- **The D1 post-Martinez churn — now FULLY DOCUMENTED (the 2023 minutes gap is closed).**
  **Kat Martinez** (D1, pre-floor 2019 win) **resigned** — *"due to Councilmember Kat Martinez
  resigning from her position … while she was presiding as Council Chair"* (2022-12-06; last
  vote 2022-11-01) → **VACANT** → **Philip Markham** (interim, **appointed + sworn in at the
  documented 2022-12-12 special meeting** — *"a resolution appointing Philip Markham as Interim
  Murray City Council Member for Council District 1, pursuant to Section 20A-1-510 … to serve
  until January 2, 2024"*, chosen by lot after a 2-2 tie; his name *"was drawn"*; he then
  **resigned mid-2023 to become the city's CED Director** — last D1 vote 2023-06-27, seat
  recorded *"(Vacant), District #1"* at the 2023-07-18 and 2023-08-01 meetings) → **VACANT
  [2023-06-28, 2023-08-08)** → **David Rodgers** (interim, **appointed + sworn in at the
  documented 2023-08-08 special "District #1 Interviews"** — chosen over Roberto Paul Pickett by
  **coin toss** after two 2-2 ties, *"Coin Toss: Heads – David Rodgers"*, resolution per
  20A-1-510 to serve until Jan 2, 2024; first vote 2023-08-22) → **Paul Pickett** (elected 2023,
  seated 2024-01-02). **Both appointees now carry HIGH-confidence, exact appointment/swearing
  dates** — the 2026-07-16 recovery of all 18 missing 2023 council minutes surfaced both
  appointment instruments AND both members' full 2023 vote spans (Markham voted at 12 D1
  meetings 2023-01-10..06-27; Rodgers at 7, 2023-08-22..12-06), replacing the old gap-bounded
  medium chain (which wrongly showed a single long VACANT 2023-01-17..2023-11-14). *(Internal
  check: Rodgers, Bullen, and Hrechkosy were the defeated 2023 challengers — Rodgers lost D1 to
  Pickett, Bullen lost D3 to Dominguez, Hrechkosy lost D5 to Hock — consistent with local
  figures who were then appointed/re-ran.)*
- **The D3 Dominguez → Goodman → Bullen chain.** **Rosalba Dominguez** (D3, pre-floor 2019 win;
  re-elected 2023) **left mid-term Dec 2024** (last vote 2024-12-03; departure date not
  separately documented → medium) → **VACANT** → **Scott Goodman** (appointed; header-attested
  "District #3" across 2025) → **Clark Bullen** (won the **2025 "District 3 (2-Year Term)"
  unexpired-term special**, seated 2026-01-06).
- **Blair Camp → Hales (Mayor).** Blair Camp held the mayoralty at the 2020 floor (pre-floor
  2017 win → medium, EMPTY vote bounds); not a candidate 2021 → Hales seated 2022-01-04.

## The 2022 redistricting

Murray redrew its 5 districts after the 2020 Census — the official district layer
(`geo/districts.geojson`) carries `Boundary_Approval_Date = 2022-01-04`, and the 2022-01-04
council minutes consider *"an ordinance adjusting the Murray City Municipal Council District
Boundaries."* **The district NUMBERS were unchanged.** `district_versions` versions the
current plan (`plan_2022`, high, real geometry) against `plan_pre2022` (pre-2020-census
boundaries **not acquired → honest GAP**, blank geometry, low). The precinct cross-check
(`--check`) **RECONCILES** every current-plan cycle (2023 D1/D3/D5, 2025 D2/D3/D4); 2021 is a
GAP against the old plan (expected).

## Honest gaps (recorded, not filled)

- **The 2023 council-minutes coverage gap is CLOSED** (recovered/promoted 2026-07-16; all 18
  formerly-lost 2023 meetings are now on disk, source=pmn, and `minutes_unrecovered.csv` is
  header-only). D1's 2023 appointee chain (Markham, Rodgers) is now anchored to DOCUMENTED
  appointment + swearing-in special meetings (2022-12-12, 2023-08-08) → **high**, no longer
  gap-bounded. (Superseded the pre-recovery medium/gap-bounded representation on 2026-07-19.)
- **Pre-floor seatings (medium)** — Martinez (D1), Cox (D2), Dominguez-t1 (D3), Turner-t1
  (D4), Hales-D5, Camp (Mayor) all held their seats at the 2020 floor via a pre-2021 election
  below the loaded election floor. Service is vote-documented; the term origin is inferred → medium.
- **plan_pre2022 geometry / precinct composition** — not acquired (blank/low GAP).
- **Executive Mayor never votes** — MAYOR `first_vote`/`last_vote` are empty by design.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2023-07-25 (D1 vacant: Markham→CED, pre-Rodgers)
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into the repo-root `cities.db` as `term` / `district_version` / `district_precinct`
rows (`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
