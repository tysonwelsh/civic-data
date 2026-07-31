# roster/ — Magna rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Magna council + mayor seat over
time** as dated intervals with per-row provenance and confidence. Built 2026-07-13 on the
herriman/midvale DISTRICT template + the white_city/copperton HB35-seam template
(`update-council-roster` skill). Answers: *who was on the council on date X?*, *who is serving
now?*, *who represents this address on date D?* — none of which the flat CSVs can answer.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — **19 tenures (12 high / 7 medium / 0 low) across 6 seats; 0 VACANT.** |
| `district_versions.csv` | Boundary interval table — **5 districts × 2 plans (10 rows)** (the 2022 redistricting). No citywide row (the exec-mayor office is 2026+, carried in `council_terms`). |
| `district_precincts.csv` | Versioned precinct→district composition — **14 `plan_2022` rows (6 high D2/D4, 8 medium D1/D3/D5) + 5 `plan_pre2022` gap rows**. |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. **0 data rows.** |
| `_precinct_to_district.csv` | Roster-layer **sidecar** over `geo/precinct_to_district.csv` — the 14 RESOLVED precincts, `source_year` preserved (2019/2025). See the library-fit note. A roster derived file, **not** a `geo/` edit. |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override, then
`python3 roster/build_roster.py`.

### Correction 2026-07-17 — the 2023 cycle was CERTIFIED, not cancelled/appointed (17→19 tenures)

The Nov-2023 township election was **cancelled under Utah Code 20A-1-206** and the three
unopposed candidates **certified elected** (Res 2023-09-02, adopted 2023-09-26, verbatim in
the minutes; `election_results/magna_races.csv` year=2023, `cancelled_certification`, no votes
cast). The roster previously mis-modeled this three ways, now fixed:
- **Sudbury (D3)** was `appointed`/blank-year → now **`elected`, election_year 2023**: he was
  the sole declared D3 candidate deemed elected (D3 opened by Peay's retirement), NOT appointed.
- **Prokopis (D1)** and **Pierce (D5)** carried a single 2020– tenure that claimed the 2023
  cycle "was NOT held (cancelled at cityhood)" — the mechanism was wrong. Each is now **SPLIT**
  into a 2020→2024 term (elected 2019) and a **2024→ term (re-certified, election_year 2023)**,
  the repo's consecutive-re-election pattern (cf. holladay Durham/Quinn). They held over without
  a new oath; both 2024 terms organized at the 2024-01-09 reorg.
Vote bounds re-clamped per term (Prokopis/Pierce's 2020-2023 vs 2024+ votes now split cleanly).
Idempotent; district layers byte-unchanged; forward crosscheck still 0-drift (the 2023 rows are
in `_races.csv`, not `_results_by_candidate.csv`, so they are not forward-checked — by design).
The REVERSE crosscheck (H-C, 2026-07-19) flags the 2023 D1/D3/D5 elected/reelected tenures for
that same reason; they are silenced by 3 cited `reverse_crosscheck_exceptions` in the driver
(cancelled-certified under 20A-1-206, Res 2023-09-02 — no by_candidate tally rows can exist), so
the crosscheck ends clean.

## ⚠ The load-bearing fact: the presiding officer's VOTE FLIPS at the 2024 HB35 seam

Magna was a Salt Lake County **metro township (2017) → CITY effective 2024-05-01 (Utah H.B.
35)**. The presiding officer changed KIND across the seam, and **so did whether they vote**:

- **Township era (2017–2025):** a 5-member **DISTRICT** council with **no separately-elected
  mayor**. The council elects one of its five as **Chair, titled "Mayor" (S.B.175)**, and
  **that Chair VOTES** as one of the five. The "Mayor" title is a **rotating ceremonial hat on
  a sitting district member** — Dan Peay (D3) through 2023, then Eric Barney (D2) 2024–2025 —
  **not a distinct seat**. Verified: Peay casts Nay/Aye rolls 2020–2023; Barney casts 7 Council
  Ayes in 2024.
- **City era (2026+):** the first **directly-elected executive Mayor, Mick Sudbury**, presides
  but **does NOT vote** (verified: cities.db shows **ZERO** Council votes for Sudbury after his
  2026-01-13 seating; 2026 tallies are 4-0 excluding the Mayor). This mayoralty is a genuinely
  **NEW office** created at the 2024-05-01 conversion.
- **Max council roll = 5 in BOTH eras.**

### How the flip is modeled (the core decision)

**`seat_id MAYOR` is reserved for the directly-elected EXECUTIVE mayoralty, which exists ONLY
from 2026** (one tenure: Sudbury, `body='Mayor'`). The township-era voting Chairs are **NOT**
placed on the MAYOR seat — they are modeled on their **DISTRICT seats** (Peay = D3, Barney = D2,
`body='Council'`), where their real votes already live. Consequences:

- **`non_voting_mayor=True`.** The only `body='Mayor'` tenure (Sudbury 2026+) is non-voting;
  `roster_lib.validate()` **ENFORCES** that its `first_vote`/`last_vote` are EMPTY — a
  fail-loud tripwire if the vote extractor ever mis-attributes a mayoral vote to him. Verified
  clean (Sudbury casts 0 Council votes in 2026).
- **The township voting Chairs keep REAL vote bounds.** Because Peay/Barney are `body='Council'`
  district members, the `non_voting_mayor` flag never touches them (it only empties
  `body='Mayor'` rows). Their votes clamp normally: **Peay D3** `2020-07-14..2023-04-25`,
  **Barney D2** `2022-01-11..2025-06-10` (including his 2024–2025 Chair-"Mayor"-hat votes).
- **Mick Sudbury is one biography across the seam.** `D3 Sudbury` (`body='Council'`, appointed
  2024) carries **real** bounds `2024-06-25..2025-06-10`; `MAYOR Sudbury` (`body='Mayor'`, 2026+)
  carries **EMPTY** bounds. Same `person_key`, per-tenure clamp — the seats don't overlap.

This **inverts** the white_city/copperton pattern (there the AT-LARGE chair's own seat *became*
the MAYOR chain and `non_voting_mayor=False`, because THOSE exec mayors also vote). Here the
DISTRICT structure makes the township chair a district member, and the exec mayor is
non-voting, so **True** is both correct and a stronger guard.

**Config tradeoff (flagged for `scripts/roster_HARDENING.md`):** `non_voting_mayor` is a single
per-city flag, so a *single* MAYOR-seat chain cannot carry a voting township-chair era AND a
non-voting exec-mayor era. The clean general fix is a **per-TENURE voting flag**. For Magna the
district-seat split above avoids the need entirely (the township chair genuinely IS a district
member), so no lib change was made — do NOT implement it per-city.

## Seat model & cohorts (verified in source)

**5 single-member DISTRICT seats (D1–D5) + the 2026+ exec MAYOR.** Founding stagger from the
Nov-2016 metro-township election (terms commence Jan):

| Cohort | Seats | Elected | Seated |
|---|---|---|---|
| **A** | D1, D3, D5 | 2016 / 2019 / ~~2023~~ / 2027 | Jan 2017 / **2020-01-14** / — |
| **B** | D2, D4 | 2016 / 2017 / 2021 / 2025 | Jan 2017 / Jan 2018 / **2022-01-11** / **2026-01-13** |
| **MAYOR** | MAYOR | 2025 (first ever) | **2026-01-13** |

`seat_id` is stable (the 2022 redistricting redrew boundaries, not seat numbers). Documented
seatings in the loaded window: **2018-07-17** (earliest recovered), **2020-01-14**,
**2022-01-11**, the **2024-01-09** reorg, **2026-01-13** (city seating).

## The chains a user must know

1. **D3 — Peay → Sudbury → Jensen (the presiding-officer thread).** **Dan Peay** (D3 + township
   Chair-"Mayor") RETIRED end of 2023 (documented last meeting **2023-12-12**: *"congratulating
   Mayor Peay on his retirement"*). **Mick Sudbury** was **certified elected** to the open D3
   seat at the **cancelled Nov-2023 election** (sole declared candidate, deemed elected under
   Utah Code 20A-1-206 / Res 2023-09-02) and **took office at the 2024-01-09 reorg** (present +
   acting from the opening roll; named *"District 3: Mick Sudbury"* in Res. 2024-01-01; the same
   meeting elected Barney the new Chair-"Mayor") — NOT an appointment. Sudbury then **won the
   2025 exec-Mayor race** and vacated D3 → **Michael Jensen** was **appointed** to the D3
   mid-term vacancy and sworn in **2026-01-13** (*"a District 3 council seat had become vacant
   because the District 3 council member had been elected mayor"* → selected from 4 applicants).
   No VACANT interval: each successor is seated at the very next meeting.
2. **D2 — Peel → Barney → Olsen.** Peel (founding + 2017) LOST D2 to **Eric Barney** (2021);
   Barney was the township Chair-"Mayor" 2024–2025 and then LOST D2 to **Megan Olsen** (2025).
3. **D4 — Hull → George.** Trish Hull (founding + 2017 + 2021) LOST D4 to **Terry George**
   (2025, after advancing through the primary).
4. **D1 / D5 — re-certified incumbents (two terms each).** **Steve Prokopis (D1)** and **Audrey
   Pierce (D5)** were elected 2019, then **RE-CERTIFIED for the 2024 term** at the **cancelled
   Nov-2023 election** — the 2023 D1/D3/D5 cycle **was resolved by certification** under Utah
   Code 20A-1-206 (Res 2023-09-02; deemed elected eff. 2024-01-01), **not** "cancelled at
   cityhood." Each is modeled as **two consecutive tenures** (2020→2024 elected 2019; 2024→
   re-certified 2023). They held over without a new oath (present at the 2024-01-09 reorg and the
   2026-01-13 city seating). The first CITY election (2025) ran only D2/D4/Mayor; D1/D3/D5 are
   next up in **2027**. Pierce also served as township **Mayor Pro Tempore** 2024–2025 (an
   acting/alternate role, not a Mayor tenure).

## Confidence model / honest gaps

- **Pre-floor founding terms (`medium`, 7 rows).** Magna's council record begins **2018-07-17**
  (the 2017 → mid-2018 minutes are a **genuine PMN retention purge**), so the **2016-founding**
  and the **2017 D2/D4 re-election** terms (Jan-2017 / Jan-2018 starts) predate the minutes
  floor: the win is in the election file, continuous service from the term start is inferred →
  `medium`. All 2019/2021/2024/2025 seatings are minutes-documented → `high`.
- **Sparse / dissent-only naming.** Magna is a narrative-tally council that names only
  dissenters (source limit). `first_vote`/`last_vote` are loose in-window activity bounds, **not**
  term boundaries — e.g. Peel's single named vote (2020-02-11) reflects the naming style, not a
  short tenure (he served D2 continuously to 2022, present in 24 of the 2021 minutes). **Eric
  Ferguson** (D5 founding), **Megan Olsen** and **Terry George** (2026 newcomers) cast **no
  named vote** and are absent from cities.db → blank bounds (the source, not a gap); they are not
  in `DB_KEY`.
- **No `low` rows in `council_terms`; 0 VACANT** — every successor is seated at the next meeting.

## The 2022 redistricting (`plan_pre2022` → `plan_2022`)

**Resolution 22-04-01, *"ADOPTING A NEW MAGNA METRO TOWNSHIP COUNCIL DISTRICT MAP"* (Map 9),
adopted 2022-04-26** on a 3-1 roll (Hull mover / Prokopis second; **VOTING Chair Peay Aye**;
Pierce Nay) — the 2020-census reapportionment that *"keeps all the Council Members in their
districts."* `district_versions` versions D1–D5 into `plan_2022` (current, `high`) and
`plan_pre2022` (founding, gap `low` — boundaries **not acquired**, never reconstructed).

### ⚠ Mixed-vintage geo + library-fit note (for `scripts/roster_HARDENING.md`)

Magna has **NO official district GIS layer** — `geo/districts.geojson` is **precinct-derived and
MIXED-VINTAGE**: D2/D4 precincts are on the **2025 (current) lines** (`high`), but **D1/D3/D5**
are still derived from the **2019 (pre-2022) returns** (`medium`) because the 2023 D1/D3/D5 cycle
was cancelled and 2025 ran only D2/D4. The driver reproduces this honestly via
`precinct_hi_source="2025"` (2025→high, 2019→medium). The canonical `geo/precinct_to_district.csv`
**has** a `source_year` column (unlike Herriman/Midvale), but it also carries **4 `confidence=none`
blank-district rows** (MAG001/008/009/017 — precincts whose current district is unknown) that
`roster_lib.write_precincts()` would render as invalid `"District "` rows. Worked around with the
roster-layer sidecar `_precinct_to_district.csv` (the 14 resolved precincts only, `source_year`
preserved). The 4 unresolved precincts are an **honest gap** documented here + in `geo/CLAUDE.md`,
never guessed. `roster_lib` and `geo/` were **not** edited.

### Precinct cross-check (`--check` / demo (e))

Groups the by-precinct council votes by the `district_precincts` (`plan_2022`) assignment and
confirms the precinct-sum winner matches the roster. **2025 D2 (Olsen) and D4 (George) RECONCILE**;
all pre-2022 cycles (2016/2017/2021) fall under `plan_pre2022` (old numbering) → honest GAPs.
D1/D3/D5 have no current-line by-precinct data (last tabulated 2019) → excluded from the
cross-check (`crosscheck_districts=("2","4")`).

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of 2024-06-01 (township voting Chair) (c) address→reps (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into the repo-root `cities.db` as `term` / `district_version` / `district_precinct` rows
(`v_council_current`, `v_term_provenance`) by `scripts/build_cities_db.py`.
