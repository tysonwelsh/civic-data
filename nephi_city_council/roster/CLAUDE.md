# roster/ — Nephi rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer that tracks **who holds each city-council + mayor seat
over time** as dated intervals, reconciled from multiple sources with **per-row
provenance and confidence**. Answers: *who was on the council on date X?*, *who is
currently serving?*, *who represents this address on this date?* — none of which the flat
CSVs can answer (they have no seat/tenure model).

Prototype status: built and validated for **Nephi**; the schema is intended to generalize
to the other 15 cities (see "Federation & generalization" below).

## Files

| File | Role |
|------|------|
| `build_roster.py` | The reconciliation script. Regenerates the two CSVs idempotently. `--demo` prints the three query patterns; `--check` runs validations. |
| `council_terms.csv` | **Core table** — one row per seat-tenure (16 tenures for Nephi). |
| `district_versions.csv` | Boundary interval table. **DEGENERATE for Nephi** (at-large → one row). |
| `roster_overrides.csv` | Hand-editable correction layer (repo override convention). Applied **last**, wins ties. Currently 0 data rows. |

**Never hand-edit `council_terms.csv` / `district_versions.csv`** — they are regenerated
by `python3 roster/build_roster.py`. All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema

`city, body, seat_id, district, person_name, person_key, start_date, end_date,
start_event, end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}.
- **`seat_id`** — staggered-cohort seat label. Nephi = 5 at-large council seats on two
  4-year cycles + mayor:
  - `AL-A1..A3` — the **3-seat cohort** elected 2019 / 2023 (terms Jan-2020…, Jan-2024…).
  - `AL-B1..B2` — the **2-seat cohort** elected 2021 / 2025 (terms Jan-2022…, Jan-2026…).
  - `MAYOR` — single seat, same 2021 / 2025 cycle as cohort B.
  Within a cohort the number is a **stable labelling of the person-chain on that seat**.
  Where two same-cohort newcomers arrive together (Travis Worwood + Cowan, 2023) the
  A2/A3 split is a labelling choice, **not source-attested** — the person-tenures are
  exact; the seat *number* between them is arbitrary (flagged in `note`).
- **`district`** = `At-Large` on every row (FK into `district_versions`; Nephi has no
  geographic districts).
- **`person_key`** = `first_last`, and it **must disambiguate shared surnames**. Nephi has
  **two Worwoods** — `skip_worwood` (Skip F., cohort B, elected 2017 & 2021) and
  `travis_worwood` (Travis L., cohort A, elected 2023) — **different people, never merge**.
- **`start_date` / `end_date`** — half-open interval `[start, end)`. `end_date` **empty =
  currently serving**. A tenure's `end_date` is the `start_date` of the next tenure on the
  same `seat_id` (computed by chaining), or an explicit documented departure.
- **`start_event`** ∈ {elected, appointed, redistricted, became-mayor, reelected}.
  **`end_event`** ∈ {reelected, lost, resigned, term-limited, deceased, became-mayor,
  serving, unknown}. `unknown` is used honestly where the *departure mechanism* is
  genuinely unrecorded (see Kent Jones / Memmott below) — the interval END is still
  precise; only "retired vs declined to run" is unknown.
- **`election_year`** — the cycle that seated the tenure (blank for a pure appointment).
- **`first_vote` / `last_vote`** — the first/last **named member-vote** observed
  in `cities.db` (the `role` table), **clamped to each tenure's own `[start_date, end_date)`
  window**. Nephi is ~95% tally-only, so these are **sparse** — a term with no named vote in
  its window is BLANK; treat them as loose activity bounds within each tenure, not term boundaries.
- **`sources`** — semicolon list citing each contributing source
  (`election:YYYY …`, `appt:YYYY-MM-DD (minutes …)`, `votes:start..end`, `minutes:DATE …`,
  `override:…`). **Every row carries a non-empty `sources` and `confidence`.**
- **`confidence`** — `high` (anchored to an election result or a minutes-documented
  appointment/oath/departure) · `medium` (inferred from vote/attendance bounds only) ·
  `low` (guess/unknown — must be flagged, never silently filled).

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/nephi_results_by_candidate.csv`, municipal **general**
   winners only (the 2025 **primary** `is_winner` rows are *advancers*, not seats — dropped
   to avoid the documented duplicate). UPPER-CASE `(NP)`/middle-initial names normalized to
   canonical `First Last` (`JUSTIN D. SEELY`→`Justin Seely`; the two Worwoods kept apart).
   → `elected` tenures, confidence **high**. The script cross-checks that **every** general
   winner maps to a tenure (prints to stderr on drift).
2. **Vote / attendance bounds** — `cities.db` `role` table (`city='nephi'`, `body='Council'`):
   sets `first_vote`/`last_vote`, and is how **appointees** surface (a person in the vote
   record with no election win). ⚠️ This layer mislabels **Glade Nielson** as `body=Council`
   with 2 votes — those are his **mayoral tie-break** votes, not council membership; the
   minutes correct it (he was Mayor 2018–2022).
3. **Appointment / oath / became-mayor events** — read from `meeting_minutes/minutes/**`.
   Nephi records council-seat appointments and oaths **in narrative prose**, *not* as an
   `Appointment` `motion_type` (those rows are all staff hires), so these events are encoded
   as minutes-cited facts in `build_roster.py`'s `TENURES` table. They date mid-term
   arrivals precisely and upgrade medium→high.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties.

Then `end_date`/`end_event` are chained per seat and the table is **validated**: no two
tenures overlap on a `seat_id`; every row has `sources` + a valid `confidence`. A failure
aborts the write (never emits a broken table).

## The key transitions (spot-checked against source minutes)

- **Justin Seely: council → mayor.** Won a **council** seat 2019 (AL-A1); elected **Mayor**
  2021. Minutes 2022-01-04: *"the vacant city council seat that Mayor Seely vacated because
  of being elected Mayor."* → his AL-A1 tenure ends `became-mayor`; a `MAYOR` tenure begins.
- **The Seely vacancy → JD Parady (appointed).** Minutes 2022-01-18: *"JOHN D. PARADY
  APPOINTED TO THE CITY COUNCIL"* — unanimous written ballot (Callaway, Memmott, Ostler,
  Worwood all wrote "JD Parady"), oath administered. → `appointed` tenure on AL-A1, filling
  a ~2-week vacancy (2022-01-04…2022-01-18). Parady then **won** AL-A1 outright in 2023.
- **Two distinct Worwoods.** Same minutes: *"Travis Worwood as Nephi City Treasurer"*
  resigned that staff role Jan 2022; **Skip F. Worwood** is the councilmember sworn 2022-01-04.
  Travis L. Worwood later won **council** in 2023. Different first names, roles, cohorts,
  election years → two people, `skip_worwood` ≠ `travis_worwood`.

## Honest gaps (recorded, not filled)

- **Tally-only sparsity.** Only ~46 of 918 council motions name voters, so the layer-2
  vote bounds are thin — the roster leans on **elections + minutes appointments**, not the
  vote record. `first_vote`/`last_vote` are loose, per-tenure-clamped bounds (blank where a
  tenure's window holds no named vote).
- **Pre-2020-floor terms (confidence `medium`).** Skip Worwood, Kent Jones, and Glade
  Nielson (mayor) were already seated at the 2020 minutes floor; the election data only
  starts 2019. Their 2017 election / 2018 term-start is **inferred from the 4-year
  staggered cycle**, flagged `medium`, and noted — not asserted as fact.
- **`end_event=unknown` for Kent Jones & Nathan Memmott.** Both served full terms and were
  **not candidates** in the next cycle (2021, 2023 respectively) — i.e. did not seek
  re-election — but the minutes don't state *why* they left (retire vs decline), so the
  departure mechanism is honestly `unknown` (the end *date* is precise).
- **Within-cohort seat numbers.** AL-A2 vs AL-A3 for the 2023 pair (Travis Worwood / Cowan)
  is a labelling choice, not source-attested.
- **No unidentified appointees.** Every mid-term arrival in Nephi's window resolved to a
  named person from the minutes — so there is **no** `UNKNOWN`/`low` row here. (Had the
  Seely-vacancy appointee been undeterminable, the seat-gap would be recorded explicitly as
  `person_name=UNKNOWN, confidence=low, note=…` rather than guessed.)

## How to query

```bash
python3 roster/build_roster.py --demo     # regenerate + print (a) current, (b) as-of, (c) address+date
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a past date** — `roster_as_of(date, body)` in `build_roster.py`: tenures with
  `start_date <= date < end_date`.
- **Address + date → representative** — `representatives_for_address(address, date)`: joins
  through `district_versions` (address → district) then `council_terms` (district+date →
  sitting members). For Nephi this **correctly reduces to At-Large → all sitting members**
  on that date (it works, just degenerate).

## `district_versions.csv` — DEGENERATE for Nephi

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Geometry is **not** stored inline — `geometry_ref` is a path
pointer (`geo/city_boundary.geojson`, the existing city-limits artifact).

Nephi's council is elected **entirely AT-LARGE — no wards/districts, no RCV** — so this
table holds exactly **one** row (`district_id=At-Large`, whole city, `plan_id=current`,
open-ended). **District-versioning is a scaffold here.** The real exercise — a sub-district
address→representative join across a boundary change — **must be validated on a
district-based city** (West Jordan, Ogden, or Provo) as a follow-up; Nephi cannot exercise
it (there are no districts to version, and no redistricting event).

## Federation & generalization (NOT implemented yet)

To federate into the root `cities.db` later (do **not** do this now — it would require
touching the shared build):
- Add a **`term`** table = `council_terms` unioned across cities (add `city`, keep
  `seat_id`/`person_key`/interval/provenance columns), and a **`district_version`** table =
  `district_versions` unioned.
- Add a view **`v_council_current`** = terms where `end_date IS NULL AND end_event='serving'`,
  and **`v_council_asof(:date)`** logic mirroring `roster_as_of`.
- Join `term.person_key` to the existing `person`/`vote` tables (via a per-city key map like
  the one in `build_roster.py`) to wire member records to tenures.

**What the district-based cities will exercise that Nephi could not:**
- Multiple concurrent `district_versions` rows and a **real redistricting event** (a
  `district_version` with a closed `effective_end` succeeded by a new `plan_id`) — testing
  the `start_event=redistricted` path and the boundary-change join.
- A **non-degenerate** address→district→representative join (one district, one rep) using
  `geo/address_to_district.py`, instead of At-Large → everyone.
- Ward/seat identity that is genuinely source-attested (district number = seat), removing
  the within-cohort labelling ambiguity Nephi has.
- Larger councils, term-limit regimes, and by-district appointment-to-vacancy processes.
Nephi validated the harder-to-see half: **multi-source tenure reconciliation with honest
provenance/confidence, shared-surname disambiguation, an appointed→elected transition, a
council→mayor transition, and pre-floor inference** — all of which the district cities also
need. The at-large geometry join is the main untested surface.
