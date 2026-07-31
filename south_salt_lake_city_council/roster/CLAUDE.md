# roster/ — South Salt Lake rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each South Salt Lake council + mayor seat
over time** as dated intervals with per-row provenance and confidence. Built 2026-07-12 on the
west_jordan MIXED (districts + at-large + non-voting mayor) template (`update-council-roster`
skill). Answers *who was on the council on date X?*, *who is serving now?*, *who represents this
address on date D?* — none of which the flat CSVs can answer.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates + runs the precinct cross-check. |
| `council_terms.csv` | **Core table** — **27 tenures (24 high / 3 medium / 0 low)** across 8 stable seats, incl. **2 VACANT** (D1 + D5, early-2026). |
| `district_versions.csv` | 5 districts × 2 plans + At-Large citywide + Mayor citywide (12 rows). |
| `district_precincts.csv` | Versioned precinct→district composition (plan-scoped, **districts only**). 21 `plan_2022` rows (source_year 2023+2025, `high`) + 5 `plan_pre2022` gap rows (`low`). |
| `roster_overrides.csv` | Hand-correction layer, applied last, wins ties. **0 data rows.** |

**Never hand-edit the generated CSVs** — edit `TENURES`/the config in the driver or add an
override, then `python3 roster/build_roster.py`.

## Seat model

**Strong-mayor MIXED form: 5 geographic districts (D1–D5) + 2 city-wide AT-LARGE seats (AL1–AL2)
= 7 voting councilmembers + a NON-VOTING executive Mayor.** A full council/RDA roll caps at **7**.
The council elects its own Chair (currently **Sharla Bynum, D3**) to preside.

- `D1..D5` — geographic districts (elected on the 2019/2023 A-cycle for D1/D4/D5; the 2017/2021/2025
  B-cycle for D2/D3).
- `AL1`, `AL2` — **ANALYTICAL** at-large ids on offset 4-year cycles: **AL1** = the 2015/2019/2023
  cycle (Pinkney → deWolfe interim → deWolfe 2-yr special); **AL2** = the 2013/2017/2021/2025 cycle
  (deWolfe 2017 → Williams 2021/2025). The 2 at-large seats have no ballot seat number; the election
  cross-check keys on the LABEL `"At-Large"`, not the analytical id.
- `MAYOR` — separately-elected executive **Cherie Wood** (mayor since Jan-2010); does **NOT** vote →
  `non_voting_mayor=True` (empty vote bounds; cherie_wood absent from cities.db).

## ⚠ The coverage cliff governs confidence (read this before trusting a date)

SSL's recorded council minutes exist essentially **only for 2020 → early-2021**, plus **2025-03-12**
and **2026-06-10/17** — **253** council dates in `meeting_minutes/minutes_unrecovered.csv` are
agenda-only (an HONEST publication gap; see the city CLAUDE.md). So:

- **Every tenure is anchored to an in-file ELECTION WIN** (2007–2025; winners cross-checked in
  `VERIFICATION.md`) → the term-**holder** is `high`. Where a term's **END** or an **appointee's
  START** genuinely falls in an un-recovered window, the row reads `medium` with an explicit note
  (weakest-link rule). **The gap has SHRUNK — the 2026 spring council minutes are now on disk**
  (2026-01-14…2026-07-08 recovered), so the D1/D5 2026 seam is fully DOCUMENTED (see the 2026-07-19
  maintenance note). The **3 remaining medium rows** are: **Sanchez-D5-2023** (elected tenure — no
  resignation instrument on disk; departure bracketed 2025-12-10 last substantive vote / 2026-01-14
  last roll appearance .. 2026-01-28 documented vacant), **Pinkney-AL1-2023** (resignation date
  still inferred, bounded before the documented 2025-01-22 deWolfe fill), and the **D5 VACANT**
  (inherits Sanchez's medium vacate boundary). Huff-D1-2023, Glad-D1, Jones-D5, and deWolfe-AL1 are
  now all **HIGH** (documented resignation/appointment/oath instruments).
- **No oath ceremonies are on disk** (SSL's January organizational minutes are all in the gap). Term
  starts use the **statutory first-Monday-in-January commencement (UCA 10-3-205)**, labelled as such
  — the election win, not a claimed ceremony, is the anchor. `first_vote`/`last_vote` are thin and
  clamped per tenure; a 2024-cycle member's first observed vote is 2025-03-12 because that's when the
  record resumes, not when service began.
- **The D1 + D5 early-2026 VACANT intervals are now DATABLE and asserted** (the 2026 spring
  minutes closed the gap): **D1 VACANT [2026-01-29, 2026-02-25)** (Huff resigned 2026-01-28 →
  Glad sworn 2026-02-25) and **D5 VACANT [2026-01-28, 2026-02-25)** (Sanchez off the roll by
  2026-01-28 → Jones sworn 2026-02-25). Both close at the documented 2026-02-25 appointment
  meeting. (Superseded the pre-recovery model that dated Glad/Jones at their first vote 2026-06-10
  with no VACANT — that was correct only while the 2026 minutes were absent.)

## The distinctive surface (spot-checked against source)

- **NON-VOTING exec Mayor Cherie Wood** — appears in 0 vote rows (only presents items); verified 0
  council rolls exceed 7 voters. Mayor rows carry empty bounds; cherie_wood is not in DB_KEY.
- **D3 NAME CHANGE** — Sharla **Beverly** (elected 2013/2017) → Sharla **Bynum** (2021/2025), one
  person (the current Chair). `BEVERLY` and `BYNUM` both map to `sharla_bynum`.
- **ONE PERSON, TWO AT-LARGE SEATS (non-contiguous)** — Ray deWolfe: AL2 2018–2022 (elected 2017,
  lost 2021 to Williams), off council 2022–2025, then appointed to AL1 (Pinkney's seat) Jan-2025 and
  won the 2025 At-Large **2-year special**. One `ray_dewolfe` key; vote bounds clamped per tenure.
- **The 2025 At-Large 2-YEAR special** — Natalie Pinkney (AL1, elected 2019 + 2023) left mid-term for
  the Salt Lake **COUNTY** council (took county office Jan-2025); deWolfe filled the interim, then won
  the off-cycle `district='At-Large-2yr'` contest that fills Pinkney's unexpired 2023 term to Jan-2028.
- **D5 Irvin Jones returns by appointment** — Jones won D5 back in 2011 (pre-floor); the 2026 D5
  appointee is the same person.

## The current roster (as-of 2026-06-10 — matches the documented roll)

| Seat | Member | Since | Basis | Conf |
|---|---|---|---|---|
| D1 | Joy Glad | 2026-02-25 | appointed + sworn (mid-term, documented) | high |
| D2 | Corey Thomas | 2026-01-05 | elected 2025 (unopposed) | high |
| D3 | Sharla Bynum (Chair) | 2026-01-05 | elected 2025 | high |
| D4 | Nick Mitchell | 2024-01-01 | elected 2023 | high |
| D5 | Irvin Jones | 2026-02-25 | appointed + sworn (mid-term, documented) | high |
| AL1 | Ray deWolfe | 2026-01-05 | elected 2025 (At-Large 2-yr special) | high |
| AL2 | Clarissa Williams | 2026-01-05 | elected 2025 (unopposed) | high |
| MAYOR | Cherie Wood | 2026-01-05 | elected 2025 (non-voting) | high |

Matches the city CLAUDE.md's documented 2026 seven (Glad, Thomas, Bynum, Mitchell, Jones, Williams,
deWolfe) + Mayor Wood.

## `district_versions` / `district_precincts` — the redistricting is INFERRED (honest)

SSL publishes its **own** authoritative 5-district ArcGIS layer (`geo/districts.geojson`, current
vintage) — `plan_2022` rows are `high`. But SSL's **redistricting adoption resolution falls in the
coverage-cliff gap** (no 2022–2024 minutes on disk), so `plan_switch` is the **nominal statewide
post-2020-census cycle boundary (2022-01-01)**, labelled inferred — not a locally-documented date.
The **pre-2022 boundaries are NOT acquired** (SSL keeps only its current layer) → `plan_pre2022` is
an honest GAP (blank geometry, `low`), never reconstructed. The precinct cross-check RECONCILES for
2023/2025 (Huff/Mitchell/Sanchez/Thomas/Bynum) and reports the pre-2022 cycles as honest GAPs.

## Honest gaps (recorded, not filled)

- **The 3 remaining `medium` rows** (above) — Sanchez-D5-2023 (no resignation instrument on disk),
  Pinkney-AL1-2023 (resignation date still inferred), and the D5 VACANT; dated at the nearest
  documented meeting, flagged, never guessed. (Down from 6: the 2026 spring-minutes recovery
  upgraded Huff/Glad/Jones to high; deWolfe was upgraded 2026-07-17.)
- **No oath dates** — term starts are the statutory UCA 10-3-205 first-Monday-January (SSL's January
  organizational minutes are all in the gap).
- **Pre-2022 district geometry + precinct composition** — not acquired (`low`), never reconstructed.
- **Pre-2017 wins not rostered** — wholly pre-floor; `keep_election_row` filters `year>=2017` (the
  earliest cycle that seats a tenure still active at the 2020 floor).

## Queries

```bash
python3 roster/build_roster.py --demo    # (a) current roster (b) as-of 2020-10-01
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
Federated into repo-root `cities.db` as `term` / `district_version` / `district_precinct` rows by
`scripts/build_cities_db.py` (run by the orchestrator, not here).

## Maintenance notes
- **2026-07-19 — D1/D5 2026 seam ANCHORED to recovered minutes (vote-window-sentinel follow-up).**
  The H-B `vote_window_sentinel` flagged Glad + Jones casting Council votes (×6 each, 2026-03-11..
  05-27) BEFORE their rostered 2026-06-10 appointments. The 2026 spring council minutes are now on
  disk (2026-01-14…2026-07-08), so the seam is fully DOCUMENTED and the gap-dated placeholders were
  corrected:
  - **Glad D1 + Jones D5: MEDIUM/2026-06-10 → HIGH/2026-02-25.** The 2026-02-25 regular minutes
    record the appointing resolutions (*"… for the Remaining Term of Office Commencing February 25,
    2026, and Concluding January 3, 2028"*; Glad unanimous for D1, Jones 3-2 over Darlene McDonald
    then 5-0 for D5) followed by a **Swearing-In Ceremony** (*"City Recorder, Ariel Andrus,
    administered the Oath of Office to Joy Glad … and to Irvin Jones …"*). First observed votes
    2026-03-11 (post-oath).
  - **Huff D1 elected-2023: MEDIUM → HIGH, end 2026-06-10 → 2026-01-29.** She *"announced her
    resignation from the District 1 City Council seat"* at the DOCUMENTED 2026-01-28 meeting (present
    + voting that night; last vote 2026-01-28) → **D1 VACANT [2026-01-29, 2026-02-25)**. The lone
    un-recovered date in that window (2026-02-11 **WORK** meeting) is acknowledged via
    `vacate_unrecovered_ack` — the 2026-02-11 REGULAR minutes are on disk and show D1 vacant, and
    both bracket dates are attested.
  - **Sanchez D5 elected-2023: stays MEDIUM, end 2026-06-10 → 2026-01-28.** No resignation
    instrument on disk (last substantive vote 2025-12-10, absent on the 2026-01-14 roll, seat
    documented vacant by 2026-01-28) → **D5 VACANT [2026-01-28, 2026-02-25)**, medium (exact
    departure unstated).
  Sentinel now CLEAN for Glad/Jones; validation PASS (27 tenures, 24 high / 3 medium; 2 VACANT);
  `validate_city.py` 0 FAIL. Backup `_backups/2026-07-19-lm-wave-followups/south_salt_lake/`.
- **2026-07-19 — LM-wave verification pass (roster + Huff overrides).** Re-ran the roster
  build/validate against the current corpus; the 2026-07-17 seams (D5 Sanchez appointed
  2023-10-25; AL1 deWolfe appointed/sworn 2025-01-22) are intact and validation is **PASS**
  (25 tenures, 20 high / 5 medium; no overlaps; gap/vacate/non-voting-mayor guards clear).
  Two follow-ups this pass:
  - **January CHAIR-election seam — INVESTIGATED, confirmed NO CHANGE (upgrades the prior
    2026-07-17 "HELD").** Swept the PRESIDING officer of every documented council RC/SM
    2020-07 → 2026-06 (incl. the recovered January organizational minutes 2024-01-10 /
    2025-01-08 / 2026-01-14): **Sharla Bynum has presided as Council Chair across the ENTIRE
    documented corpus** — no chair ever changes hands, and the January officer elections are
    by acclamation (honestly uncaptured, not a motion). The chair-as-a-note-on-Bynum-D3 model
    is therefore complete and correct; **no rostered change applied** (Chair is a role note,
    not a separate seat). This closes the third seam positively rather than leaving it held.
  - **`last_vote` refreshed 2026-06-17 → 2026-07-08** for the seven currently-serving
    tenures — a legitimate data-driven regeneration (a real 2026-07-08 Council RC meeting was
    ingested after 2026-07-17; confirmed in `meeting_minutes/minutes_index.csv`), not a seam.
    Idempotent otherwise (only the vote-bound field moved). The Glad-D1 / Jones-D5 2026
    appointments remain gap-dated `medium` (no on-disk appointment instrument yet).
- **2026-07-17 — roster refresh from the newly promoted 2022–2026 minutes** (the 2026-07-16
  ArchivedMinutes promotion quintupled the corpus). Now **25 tenures (20 high / 5 medium)**,
  up from 24 (18 high / 6 medium). Two mid-term seams that were gap-inferred are now anchored
  to DOCUMENTED instruments recovered in the promoted minutes:
  - **AL1 deWolfe interim: MEDIUM → HIGH, start 2025-03-12 → 2025-01-22.** The 2025-01-22
    regular council minutes record the 5-1 selection, the appointing Resolution (UCA
    10-3-507), and City Recorder Ariel Andrus **swearing deWolfe in** — refuting the old
    "appointment resolution is in the coverage gap" note. Pinkney's AL1 end auto-moves to the
    documented 2025-01-22 fill (still `medium` — her exact resignation date is unstated but
    now bounded to before that).
  - **D5 Sanchez: new HIGH appointed tenure 2023-10-25 → 2024-01-01.** The 2023-10-25 council
    minutes record "Selection to Fill Vacant Council District 5 Seat" — Sanchez the sole
    applicant, appointed to fill Siwik's mid-term vacancy, then won the concurrent Nov-2023
    general for the full term (his elected tenure follows, still `medium` for its gap-inferred
    end). **Siwik D5 end_event `did-not-run` → `resigned`** (he vacated before 2023-10-25; the
    handoff is dated at the documented fill, no fabricated VACANT). Validation PASS, no
    overlaps, 2023 D5 still RECONCILES.
  - **HELD (flag, not applied):** January **Chair elections** — the Chair is tracked only as a
    note on Bynum (D3), not a rostered seat, and SSL's officer elections are largely by
    acclamation (honestly uncaptured); no structural roster change. The Glad-D1 / Jones-D5
    2026 appointments remain gap-dated `medium` (no on-disk appointment instrument recovered —
    those 2026 January/appointment minutes are still absent).
