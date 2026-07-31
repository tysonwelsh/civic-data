# roster/ — Vineyard rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each Vineyard City Council + Mayor
seat over time** as dated intervals, reconciled from multiple sources with **per-row
provenance and confidence**. Answers: *who was on the council on date X?*, *who is serving
now?*, *who represents this address on this date?* — none of which the flat CSVs can answer.

Vineyard is the **VACANCY / MID-TERM-APPOINTMENT validation city** for the roster schema.
Nephi (at-large) and Provo (district) both had the VACANT-interval code path but produced
**0 VACANT rows** in-window. Vineyard finally exercises it: **two councilmembers left
mid-term and were replaced by council appointment**, so the `person_name=VACANT` interval
**and** the `appointed` tenure both actually produce rows here. Like Nephi, Vineyard is
**AT-LARGE** (no geographic districts) — `district_versions` is one degenerate whole-city row.

## Files

| File | Role |
|------|------|
| `build_roster.py` | Reconciliation script (thin driver over `../../scripts/roster_lib.py`). Regenerates the two CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (**18 rows: 16 person-tenures + 2 VACANT intervals**). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for Vineyard** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit the two generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-cohort seat label. Vineyard = **Mayor + 4 at-large council seats
  (2020–2025), growing to Mayor + 5 from 2026** (Prop 10, 2024 ballot):
  - `AL-A1`, `AL-A2` — **Cohort A** (elected 2019 / 2023 / 2027; terms Jan-2020…, Jan-2024…).
  - `AL-B1`, `AL-B2` — **Cohort B** (elected 2017 / 2021 / 2025; terms Jan-2018…, Jan-2022…, Jan-2026…).
  - `AL-C` — the **NEW 5th seat** (Prop 10), first filled 2025; McCumber drew a **2-year term
    BY LOT** to stagger it onto the odd-year (Cohort-A / 2027) cycle.
  - `MAYOR` — single seat (elected 2017 / 2021 / 2025).
  Within-cohort seat **numbers** are a stable labelling of the person-chain; where two
  same-cohort newcomers arrive together the A1/A2 (and B1/B2, and Wood/Lauret) split is a
  **labelling choice** (flagged in `note`). The two vacancy chains **anchor one seat each**:
  `AL-A2` = Cameron→Nair, `AL-B2` = Rasmussen→Clawson.
- **`district`** = `At-Large` on every row (FK into `district_versions`; Vineyard has no
  geographic districts).
- **`person_key`** = `first_last`, disambiguating shared names. Vineyard has **two Jacobs** —
  `jacob_holdaway` (AL-A1, elected 2023) and `jacob_wood` (AL-B1, elected 2025): **different
  people, never merge** (they have distinct surnames, so no first-name key is used). The
  early councilmember surnamed **Welsh** (`cristy_welsh`, elected 2019) is kept full/distinct.
- **`start_date` / `end_date`** — half-open `[start, end)`. `end_date` empty = **currently
  serving**. Chained: a tenure ends when the next tenure on the same `seat_id` begins, or at a
  documented `vacate_date` (which then inserts a VACANT interval).
- **`start_event`** ∈ {elected, reelected, appointed, became-mayor, vacated (VACANT rows)}.
  **`end_event`** ∈ {reelected, lost, did-not-run, resigned, serving, filled (VACANT rows)}.
  `did-not-run` = a full-term member who was **not a candidate** in the next cycle (the end
  *date* is precise; only retire-vs-decline is unstated). `resigned` = a mid-term departure
  that created a declared council **vacancy** (see the two vacancy notes below).
- **`election_year`** — the cycle that seated the tenure (**blank for a pure appointment** —
  Clawson, Nair).
- **`first_vote` / `last_vote`** — each row's first/last observed **council-body** member
  vote in `cities.db` (`role`/`vote`, `city='vineyard'`), **clamped to that tenure's own
  `[start_date, end_date)` window** (so Fullmer's two `MAYOR` terms carry per-term bounds, not
  one spanning span). Vineyard has **full named roll calls**, so these are rich and reliable —
  they set the vote bounds AND surface the two appointees (a person voting with no election win:
  Clawson from 2024-11-20, Nair from 2026-01-14). **Vineyard's Mayor VOTES**, so the `MAYOR` rows
  also carry vote bounds (Fullmer's 973 council-body votes split across her two terms; Stratton 2
  — see below), unlike Nephi/Provo where the mayor is absent from the vote table.
- **`sources`** — semicolon list (`election:YYYY …`, `appt:DATE (minutes …)`, `votes:…`,
  `minutes:DATE …`). **Every row carries a non-empty `sources` + `confidence`.**
- **`confidence`** — `high` (election result or minutes-documented appointment/oath/vacancy)
  · `medium` (pre-floor 2017-cycle term, term-start inferred; or a vacancy window bounded by
  documented service across an un-recovered minutes gap) · `low` (unknown — **none here**).

Counts: **18 rows — 13 high / 5 medium / 0 low; 2 VACANT intervals.** 0 overlapping tenures
per seat. The 5 `medium` rows: the 3 pre-floor 2017-cycle holders (Earnest AL-B1, Judd
AL-B2, Fullmer's first Mayor term) + the AL-A2 Cameron departure and its VACANT interval
(down-ranked 2026-07-11 after the roster audit — the Cameron→Nair resignation/appointment
dates fall in an un-recovered Nov/Dec-2025 minutes gap, so they are `medium` on the dates;
Nair's `appointed` row stays `high`, anchored to his 2026-01-14 seating). `roster_lib` now
auto-fails a `high` VACANT interval whose window overlaps `minutes_unrecovered.csv`.

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/vineyard_results_by_candidate.csv`, municipal **general**
   winners only (`keep_election_row` drops the 2025 **primary** advancer rows so Nair/Rhoton/
   Clawson are not mis-counted as winners). Both the RCV years (2019/2021/2023) and the 2025
   plurality vote-for-3 are handled — each `is_winner=Y` general row maps to a seat via
   office=body (at-large). UPPER-CASE names normalized (`G. TYCE FLAKE`→`tyce_flake`). The
   script cross-checks that **every** general winner maps to an `elected`/`reelected` tenure
   (prints to stderr on drift — currently clean).
2. **Vote / attendance bounds** — `cities.db` `role`/`vote` (`city='vineyard'`,
   `body='Council'`): sets `first_vote`/`last_vote` and is how the **two appointees** surface
   (Clawson first_seen 2024-11-20, Nair first_seen 2026-01-14 — both with no election win).
   The bound `rasmussen … last 2024-09/10 → clawson first 2024-11-20` is exactly the off-cycle
   arrival that flags a mid-term appointment.
3. **Appointment / oath / vacancy events** — read from `meeting_minutes/minutes/**` and encoded
   in the `TENURES` table (Vineyard records these in narrative prose, not as a machine motion
   type). These date the mid-term arrivals and the Jan-2026 turnover precisely.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties.

Then `end_date` is chained per seat, the **VACANT-interval** rule runs, and the table is
validated (no overlaps; sources+confidence present). A failure aborts the write.

## The VACANT / mid-term-appointment path — the point of this city (spot-checked)

Two councilmembers left mid-term and were replaced by **council appointment**, producing the
first real `person_name=VACANT` rows in the roster schema:

- **AL-B2 — Rasmussen → [VACANT] → Clawson (fully on-disk).** Amber Rasmussen (elected 2021)
  is present and voting through **2024-10-09**; by the **2024-11-13** meeting she is absent
  from the present-list and a resident *"thanked councilmember Rasmussen for her service"* — a
  documented farewell. The **2024-11-20 special session** agenda item 2.1 is *"Vineyard City
  Council Vacancy"*: the council interviewed 20 applicants and *"voted by means of a secret
  ballot. The voting results were: three (3) votes for **Brett Clawson (winner)** and two (2)
  votes for Kimberly Olsen … Ms. Spencer **swore in Brett Clawson** as the new councilmember."*
  → Rasmussen ends `resigned` at the vacate date (**2024-11-13**, the documented first-absent
  meeting), an explicit **VACANT** interval spans 2024-11-13…2024-11-20, then Clawson's
  **`appointed`** tenure begins. The 2024-12-11 present-list confirms the swap
  (Cameron/**Clawson**/Holdaway/Sifuentes). *(The word "resign" isn't printed in the recovered
  minutes — a mid-term **Vacancy** was formally declared and filled, so `resigned` is the
  standard inferred mechanism; the exact letter/date is flagged as not-on-disk.)* Clawson then
  **ran** for a full term in the **2025 general and LOST** (rank5 of 6) → `end_event=lost`;
  term expired Jan-2026. **Appointed → contested → lost** — the appointee did not retain the seat.

- **AL-A2 — Cameron → [VACANT] → Nair (appointment date in a minutes GAP).** Sara Cameron
  (elected 2023) serves through her last documented meeting **2025-10-22**, then resigned
  mid-term; **Ezra Nair was appointed** to fill her seat (~Nov 2025; confirmed by
  `election_results/CLAUDE.md`'s cross-check and the `vineyardutah.gov` council page). The
  resignation/appointment minutes are in an **un-recovered gap** — no Nov-2025 council minutes
  were recovered and **2025-12-10 is unrecoverable** (`meeting_minutes/minutes_unrecovered.csv`).
  So the **VACANT** interval is **documented-service-bounded** (Cameron's last service
  2025-10-22 → Nair's first documented seating 2026-01-14), Cameron ends `resigned`, and Nair's
  **`appointed`** tenure starts at his first on-disk seating (2026-01-14 — the ~Nov-2025 oath
  date is **not fabricated**). The 2026-01-14 present-list confirms *"Councilmember Ezra Nair"*
  seated while Cameron appears only in "Others Speaking" (a resident).

## Other key transitions (spot-checked)

- **Fullmer = MAYOR, confirmed (not double-counted as a council voter).** Julie Fullmer heads
  the 2020-01-08 present-list as *"Mayor Julie Fullmer"* and chairs the RDA as *"Chair
  Fullmer"* — she is the **Mayor**, in the `MAYOR` seat, **not** a council seat (elected Mayor
  2017 pre-floor, re-elected 2021 at 86.64%). Vineyard's mayor **votes**, so her 973
  council-body votes are legitimate mayoral roll-call participation, attached to the `MAYOR`
  rows (not a council tenure). She did not run in 2025 → the 2025 mayoral race was for the
  **open seat** she vacated.
- **Stratton anomaly resolved.** `cities.db` lists **Zack Stratton with 2 Council-body votes on
  2026-02-03 only**. Those are his **mayoral** roll-call participation on that special session
  (*"MAYOR STRATTON AND COUNCILMEMBERS NAIR, LAURET … VOTED"*) — **not** a separate council
  tenure. Stratton is the **Mayor** (elected 2025, def. Sifuentes 1417–1173); the 2 votes are
  recorded on his `MAYOR` row's `last_vote`, and no council seat is invented for him.
- **Jan-2026 wholesale turnover (4 new faces at once).** The 2026-01-14 present-list is **Mayor
  Zack Stratton + Councilmembers McCumber, Wood, Holdaway, Lauret, Nair** (Mayor + 5, the Prop-10
  expansion). New that day: **Stratton** (Mayor, replacing Fullmer), **Wood** and **Lauret** (4-yr
  Cohort-B, replacing Sifuentes and the Clawson-held B2 seat), **McCumber** (the new 2-yr AL-C
  seat). Holdaway continues; Nair was appointed just before. Cameron and Clawson now appear as
  residents in "Others Speaking".

## Honest gaps (recorded, not filled)

- **Exact Rasmussen resignation date** — the recovered minutes declare a "Vacancy" + farewell
  but do not print the resignation letter/date; `vacate_date` uses the documented first-absent
  meeting (2024-11-13) as the departure bound. Mechanism inferred as `resigned` (flagged).
- **Cameron→Nair appointment date** — in an **un-recovered Nov/Dec-2025 minutes gap**; the
  VACANT window and Nair's start are **documented-service-bounded** (`medium` on the dates,
  `high` on the fact of resignation+appointment). Drop the exact dates into
  `roster_overrides.csv` if those minutes surface.
- **Pre-floor 2017-cycle terms (`medium`).** Earnest (AL-B1), Judd (AL-B2) and Fullmer's first
  Mayor term were seated at the 2020 floor; their 2017 election / 2018-01 term-start is inferred
  from the Cohort-B / mayoral 4-year stagger, not asserted as fact.
- **Within-cohort seat numbers.** A1/A2 (Welsh/Flake→Holdaway/Cameron), B1/B2 (Earnest/Judd→
  Sifuentes/Rasmussen; Wood/Lauret in 2026) are labelling choices where same-cohort members
  arrived together — the **person-tenures are exact**; the seat *number* between paired arrivals
  is not source-attested (the two vacancy chains anchor `AL-A2` and `AL-B2`).
- **No unidentified appointee.** Both mid-term arrivals resolved to named persons from the
  minutes → **no `UNKNOWN`/`low` rows**. (Had an appointee been undeterminable, the seat-gap
  would be recorded as `person_name=UNKNOWN, confidence=low` rather than guessed.)

## `district_versions.csv` — DEGENERATE for Vineyard (at-large)

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Vineyard's council + mayor are elected **entirely AT-LARGE — no
wards/districts** — so this table holds exactly **one** row (`district_id=At-Large`, whole city,
open-ended). `geometry_ref` = `geo/city_limits.geojson` (the existing city-limits polygon).
**Note:** Vineyard's city LIMITS change over time by **annexation** (fast-growth city); the row
points at the **current** limits, and prior annexation-versioned boundaries are **not on disk
and not fabricated**. The sub-district address→representative join is validated on Provo (a real
district city); here it correctly degenerates to whole-city → all sitting members + mayor.

## How to query

```bash
python3 roster/build_roster.py --demo   # (a) current  (b) as-of a VACANT window  (b') as-of appointed  (c) address→rep
python3 roster/build_roster.py --check  # regenerate + validations only
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'` (Mayor + 5).
- **As of a past date** — `roster_as_of(date, body)`: e.g. **2024-11-17** shows the AL-B2
  **VACANT** interval; **2025-03-01** shows **Clawson appointed** and seated.
- **Address + date → representative** — `representatives_for_address(address, date)`: for
  Vineyard this **correctly reduces to At-Large → all sitting members + mayor** on that date
  (degenerate, like Nephi). On a date inside the VACANT window it honestly returns the `VACANT`
  placeholder alongside the sitting members.

## What Vineyard validated that Nephi/Provo could not

The **mid-term VACANT interval + `appointed` tenure actually producing rows** — the one surface
both prototypes left untested (both had the code path but 0 vacancies in-window). Vineyard adds:
two real council-appointment chains (one fully on-disk with an exact appointment date + secret
ballot, one bounded across a minutes gap), an **appointed→ran→lost** trajectory (Clawson), a
**council-member-runs-for-mayor-and-loses** departure (Sifuentes), a **new seat added by
ballot proposition** mid-schema (AL-C, 2-year-by-lot stagger), and a **voting mayor** whose
bounds land on the `MAYOR` rows. It shares the harder-to-see half with both — multi-source
tenure reconciliation with honest provenance/confidence, shared-name disambiguation (two
Jacobs), and pre-floor inference. **Federation into the root `cities.db` is NOT done here** (it
would require touching the shared build) — see the Nephi/Provo roster CLAUDE.md federation notes.
