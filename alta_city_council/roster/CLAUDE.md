# roster/ — Town of Alta rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Alta town-council + mayor seat
over time** as dated intervals with per-row provenance and confidence. Built on the
bluffdale/nephi at-large template (`update-council-roster` skill). Answers: *who was on the
council on date X?*, *who is serving now?*, *who represents this address on date D?* (Alta
is all at-large → the geographic answer degenerates to the townwide roster).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver over `../../scripts/roster_lib.py`; regenerates the CSVs idempotently. `--demo` prints query patterns; `--check` validates. |
| `council_terms.csv` | **Core table** — 13 tenures (8 high / 5 medium / 0 low) across 5 seats. |
| `district_versions.csv` | DEGENERATE (at-large town → one row; no wards, no address→district tool). |
| `roster_overrides.csv` | Hand-editable correction layer, applied last, wins ties (0 data rows). |

**Never hand-edit the generated CSVs** — edit `TENURES` in the driver or add an override,
then `python3 roster/build_roster.py`.

### Correction 2026-07-17 — the 2025 election was CANCELLED + CERTIFIED, not a county-file gap (11→13 tenures)

The 2025 Town of Alta election was **cancelled under Utah Code 20A-1-206** (Res **2025-R-26**,
adopted 2025-09-10, after candidate withdrawals) and the unopposed candidates **certified
elected** — **Roger Bourke** (Mayor, unopposed), **Carolyn Anctil** + **Craig Heimark** (the two
open at-large seats; John Byrne + Paul Moxley withdrew). Recovered 2026-07-17 into
`election_results/alta_races.csv` (year 2025, `cancelled_certification`; all vote/pct columns
blank — no votes cast). This **supersedes** the prior "county-file gap where the election
occurred" reading and **resolves** the prior "whether Bourke was re-elected in 2025 is
UNDETERMINED" note. Fixes:
- **Heimark (AL-1)** — evidence/mechanism corrected from "won a county-gap election / minutes-
  anchored" to **certified-elected via Res 2025-R-26** (start_event stays `elected`, ey 2025;
  structural row unchanged).
- **Anctil (AL-2)** and **Bourke (MAYOR)** — each **SPLIT** into a 2021 term and a **2025
  re-certified term** (`reelected`, ey 2025, seated 2026-01-14), the repo's consecutive-
  re-election pattern, now that the certification instrument is on disk (replaces the earlier
  single continuous tenure with the re-election "inferred from continued service").
Vote bounds re-clamped per term; Heimark's treasurer-era 2022-2023 stray votes stay clamped out
(his `first_vote` is 2026-01-14). Idempotent; district layer byte-unchanged; forward crosscheck
still 0-drift (`keep_election_row` is restricted to 2021/2023; no 2025 rows in `by_candidate`).

## Seat model (verified in source)

**Utah TOWN form: a VOTING Mayor + 4 AT-LARGE councilmembers** (no districts); a full roll
caps at **5** (Mayor + 4). **`non_voting_mayor=False`** → the MAYOR row carries **real vote
bounds** (Roger Bourke is cities.db's top Alta voter). Sparse by design (~12 meetings/yr).
- `AL-1`, `AL-2` — **cohort P** (elects 2021 / 2025).
- `AL-3`, `AL-4` — **cohort Q** (elects 2019 / 2023).
- `MAYOR` — Harris Sondak (2020–2021, pre-floor) → **Roger Bourke** (2022→).
Within-cohort seat numbers are a labelling of person-chains, **not** source-attested
(flagged in notes).

## Seating dates (documented)

- **2022-01-12** — 2021 winners Byrne (AL-1) + Anctil (AL-2) + Mayor Roger Bourke; Morgan
  named **Mayor Pro Tem** at this reorganization meeting.
- **2024-01-10** — 2023 winners Morgan (re-elected, AL-4) + Schilling (AL-3); present block.
- **2026-01-14** — the 2025 **cancelled-certification** winners take office: Heimark (AL-1, new),
  Anctil (AL-2, re-certified), and Mayor Bourke (re-certified) — Mayor Bourke referenced *"recent
  oath-of-office ceremonies for recently elected officials"*; Heimark *"welcomed … to the council
  following the transition from the treasurer position."*
Pre-2022 holders (Sondak, Curry, Davis, M. Bourke, Morgan-prefloor) predate these → pre-floor
`medium` (Alta `election_results` begins 2021, so they carry no in-data winner row).

## Two people/name hazards + the Heimark flag (a user must know)

1. **Two mayors, two Bourkes.** **Harris Sondak** was Mayor 2020–2021 (withdrew from the
   2021 race); **Roger Bourke** (a former Planning Commissioner) is Mayor 2022→. The
   2020–2021 councilmember **MARGARET Bourke** is a **different person** from Mayor **ROGER**
   Bourke → disambiguated ROGER vs MARGARET. **Join by full name.**
2. **Craig Heimark — TREASURER-then-COUNCILMEMBER (votes-pipeline FLAG).** Heimark was
   appointed **Town Treasurer (staff)** 2022-05-11 and served through 2025; he **won the 2025
   council election** and was seated **2026-01-14** (minutes: *"Heimark's election to the
   town council (from role as Treasurer)"*). His cities.db `craigheimark` role shows
   `first_seen 2022-04-13` with a handful of 2022–2023 "votes" (2022=1, 2023=3) — those are
   **treasurer-era procedural mover/seconder mentions MISATTRIBUTED as council votes**, not
   membership. The tenure-window clamp keeps them out (his rostered `first_vote` is
   2026-01-14). **FLAGGED as a votes-pipeline issue; not fixed from the roster.**

## Honest gaps / conventions

- **2021 tallies PRIVACY-SUPPRESSED** (Alta's ~380-person precinct is below the county
  privacy floor): the 2021 winners (Byrne + Anctil council; Roger Bourke mayor) are known
  from external cross-check + minutes; **numeric votes are blank, never fabricated**
  (`election_results/CLAUDE.md`). Their tenures are still `high` (minutes-anchored seatings).
- **2025 cycle was CANCELLED + CERTIFIED** (Utah Code 20A-1-206; Res 2025-R-26, adopted
  2025-09-10 — corrected 2026-07-17; NOT the earlier "county-file gap / the election occurred"
  reading): after candidate withdrawals the election was cancelled and the unopposed candidates
  deemed elected — **Bourke** (Mayor), **Anctil** + **Heimark** (the two open at-large seats;
  Byrne + Moxley withdrew). Recovered into `election_results/alta_races.csv` (year 2025,
  `cancelled_certification`; vote columns blank — no votes). All three seated **2026-01-14**.
  **Anctil (AL-2)** and **Bourke (MAYOR)** are now each **split** into a 2021 term + a 2025
  certified term (ey 2025); **Heimark (AL-1)** cites the certification (Res 2025-R-26). The
  `by_candidate.csv` still has no 2025 rows, so the forward crosscheck is unaffected.
- **Pre-floor holders (`medium`)**: Sondak (MAYOR), Curry (AL-2), M. Bourke (AL-1) start
  `2018-01-01` (2017 wins, cohort-inferred, term 2018-2022); Davis (AL-3) & Morgan-prefloor
  (AL-4) start `2020-01-01` (2019 wins, term 2020-2024, at the floor). Election years are
  inferred from the staggered cycle (not in the built 2021+ data) → honestly flagged, never
  asserted as fact.
- **`end_event`**: M. Bourke & Davis = `lost` (ran the next cycle and lost — M. Bourke 2021,
  Davis 2023); Curry & Byrne = `unknown` (did not return; mechanism unstated); Sondak =
  `unknown` (withdrew from the 2021 mayoral race).
- **Davis's stray vote**: cities.db shows a Sheridan Davis vote dated **2024-02-14**, AFTER
  Schilling was seated (2024-01-10, Davis not in that present block) — a post-seating
  misattribution → his AL-3 tenure ends 2024-01-10 and the clamp excludes the stray (his
  rostered `last_vote` is 2023-12-13). FLAGGED, not fixed from the roster.
- **Alta Canyon Rec decoys** are excluded from `election_results` (a different entity) and
  never enter this roster.

## Queries

```bash
python3 roster/build_roster.py --demo   # (a) current roster, (b) as-of 2023-06-01
```
Not yet federated into repo-root `cities.db` (run `scripts/build_cities_db.py` to pick up
this `roster/` dir into `term` / `district_version` + `v_council_current`).
