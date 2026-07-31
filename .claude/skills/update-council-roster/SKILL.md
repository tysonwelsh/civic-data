---
name: update-council-roster
description: Keep a city's rolling council-roster layer (`<city>_city_council/roster/`) current after a refresh — regenerate + validate, DETECT candidate roster changes (new election winners, mid-term appointees, resignations, redistrictings) as review FLAGS, apply only human/Claude-confirmed ones to the driver's TENURES or roster_overrides.csv, and re-federate into cities.db. Use after a city refresh lands new minutes/elections/votes, or when the user says "update/refresh the council roster", "who's on the council changed", "add the new member", "a councilmember resigned/was appointed", or "the districts were redrawn".
---

# Update the council roster

Maintains the **rolling council-roster** layer for one `<city>_city_council/roster/` — the
interval / slowly-changing-dimension table of **who holds each council + mayor seat over
time**, with per-row provenance + confidence. Runs **AFTER** a city's normal `refresh-city`
pass (new minutes/elections/votes already ingested and the derived chain rebuilt). Four
rosters exist as worked examples — **nephi** (at-large), **provo** (district + redistricting),
**vineyard** (mid-term VACANT/appointment), **slc** (largest; name-change person; 6
vacancies). Read the target city's `roster/CLAUDE.md` first; it is authoritative for that
city's seats, cohorts, and quirks.

The mechanics live in `scripts/roster_lib.py` (read its module docstring + the `RosterConfig`
schema + the VALIDATORS). Each `roster/build_roster.py` is a thin driver supplying a config +
the hand-curated `TENURES` list. **You edit the driver's curated data, never the generated
CSVs.** The hardening history is `scripts/roster_HARDENING.md` — the guardrails below encode
its lessons.

## Cardinal philosophy: DETECT-AND-FLAG, never silently guess

Every signal below is a **FLAG for confirmation**, not an auto-edit. Surface the candidate
change with its evidence, investigate the minutes, then apply only what a source documents.
An unknown seat-holder/date/boundary becomes an **explicit gap** (`confidence=low` +
`UNKNOWN`/`VACANT` + a note), never a guess (civic-data CLAUDE.md cardinal rules: NEVER
fabricate; honest gaps are data; corrections go through override files; derived layers
regenerate). Copy-paste detection queries are in `reference.md` (same dir).

## Procedure

### 1. Regenerate + validate (the tripwire)

`python3 <city>_city_council/roster/build_roster.py --check`. The hardened validators
(`roster_lib.validate`) must pass: **no overlapping tenures** on a seat, **every row has
`sources` + a valid `confidence` + a known `seat_id`**, the **vacate-confidence invariant** (a
tenure that vacates mid-term may not be more confident than its own `vacate_confidence`), and
the **gap-detector** (a `high` VACANT interval whose window contains an un-recovered minutes
date FAILS). A failure is a **signal, not a nuisance** — it usually means a new event needs
modeling. Note the idempotency check the audits use: a clean re-run leaves
`council_terms.csv` **byte-identical**; a diff means new data moved something — investigate why.

### 2. Detect new signals (each a FLAG for review)

Run the `reference.md` queries against the refreshed data. For each hit, investigate the
minutes before touching anything.

- **New election winner** — an `is_winner` general-election row (`election_results/<city>_
  results_by_candidate.csv`) with no matching `elected`/`reelected` tenure. → Propose a new
  `elected` tenure: **start = the January swearing-in** (the documented first-meeting/oath
  date, e.g. Provo `2024-01-09`; NOT Jan-01), and **close the predecessor** on the same seat.
  Confidence `high` (election-anchored + minutes-seated).
- **Unrostered voter** — a `person` casting a `body='Council'` vote in `cities.db` who is NOT
  on the current roster. → FLAG as **either** a mid-term **appointee** **or** a
  **name-normalization miss** (the shared-surname / name-change class — e.g. SLC's
  Petro-Eschler→Petro carrying two `name_key`s → one `person_key`). **Cross-check `person` /
  `name_key`** first; if it's a real new person, **investigate the minutes for an
  appointment** — never auto-add. An off-cycle `first_vote` right after a predecessor's last
  vote is the appointment signature (Vineyard Clawson 2024-11-20).
- **Disappeared member** — a rostered, still-serving member whose **last observed vote** is now
  well before the latest meeting. → FLAG a candidate `end_date` (resignation / did-not-run /
  declined) for confirmation from the minutes (farewell, vacancy declaration). The end *date*
  can be precise even when the *mechanism* (retire vs decline) is unstated → `end_event=unknown`
  is honest.
- **New appointment / resignation in fresh minutes** → model with the **VACANT convention**:
  predecessor ends at the documented `vacate_date`, an explicit `person_name=VACANT` interval
  spans until the successor's seating, then the `appointed` tenure begins. If the exact dates
  fall in an **un-recovered minutes gap**, set `vacate_confidence=medium` — the gap-detector
  will enforce it (this is the Vineyard Cameron→Nair lesson).
- **New redistricting** — a resolution/ordinance redrawing districts in fresh minutes. → Add a
  `district_versions` plan (real geometry if the geojson is on disk → `high`; else an
  **explicit gap** row: blank `geometry_ref`, `confidence=low`, note "not acquired"). For a
  district city, also update `district_precincts` (plan-scoped). Prior boundaries not on disk
  are a gap, never reconstructed.
- **8th-voter / roll-size sentinel** — a date whose recorded council-vote count **exceeds the
  seat count**. → An extraction artifact (a mayor tie-break counted as a member, or an LLM
  stray vote like SLC's Mano 2026-03-24). **FLAG it; do NOT let it extend a tenure.** Log it as
  a votes-pipeline issue.
- **Bidirectional election crosscheck** — every `elected`/`reelected` tenure with an
  `election_year` should map back to an `is_winner` general row (the reverse of the builder's
  built-in forward check). The documented exception: **pre-floor / election-anchored terms**
  (predating the vote-data or minutes floor) legitimately carry no in-data winner row and must
  be `confidence=medium`.

### 3. Apply confirmed changes (curated data, never generated CSVs)

- A **new fact the reconciliation can derive** (an election winner + its swearing-in, an
  appointment quoted in minutes) → add/extend the `dict(...)` in the driver's `TENURES` list,
  with a cited `sources` string and `confidence`. Match the existing entries' shape (see any
  `roster/build_roster.py`).
- A **correction or a fact reconciliation can't derive** (an exact date recovered from
  late-posted minutes, an adjudicated source conflict) → add a row to
  `roster/roster_overrides.csv`, keyed `(seat_id, person_key, start_date)`; it is applied last
  and wins ties. Always fill `reason`.
- Then re-run `python3 roster/build_roster.py` (regenerates the CSVs; validators re-gate), and
  **re-federate**: `python3 scripts/build_cities_db.py` (picks up any city with a `roster/` dir
  into `term` / `district_version` / `district_precinct` + `v_council_current`). Confirm
  integrity — the build prints roster row counts per city.

### 4. Confidence discipline

- **`high`** — anchored to an **election result** OR a **minutes-documented**
  oath/appointment/resignation/redistricting (both endpoints of a VACANT window documented).
- **`medium`** — a pre-floor / election-anchored term (win is fact, continuous service
  inferred), or a **gap-bounded** vacancy/departure (dates bounded by documented service across
  an un-recovered gap).
- **`low` / `UNKNOWN` / `VACANT`** — a genuine gap: an undeterminable appointee or an
  unacquired boundary. Flag it; never fill it.

**Cite every row's `sources`** (`election:YYYY …`, `minutes:DATE …`, `appt:DATE …`,
`votes:start..end`, `override:…`). Weakest-link rule: a row that bundles a documented start
with an inferred end reads at the weaker confidence (the Vineyard F1/F2 finding).

### 5. When to (re)run the independent audit

A **materially-changed** roster (a new vacancy chain, a redistricting, a name-change person, a
seat added/removed) earns a fresh `roster/AUDIT.md` — the adversarial ground-truth pass that a
**separate** agent runs (it did NOT build the roster): re-derive every changed tenure from
source, quote the minutes, re-run vote-bounds from `cities.db`, run the structural invariants,
and grade calibration. The existing `vineyard_city_council/roster/AUDIT.md` and
`slc_city_council/roster/AUDIT.md` are the template + voice. Systemic findings get logged to
`scripts/roster_HARDENING.md` and, where general, harden `roster_lib.py` for the whole fleet.

## Rules

- **DETECT-AND-FLAG.** Surface candidates with evidence; apply only source-confirmed changes.
- **Never fabricate** a name, date, or boundary — an unknown is an explicit gap, not a guess.
- **Never hand-edit** `council_terms.csv` / `district_versions.csv` / `district_precincts.csv`
  — edit `TENURES` or `roster_overrides.csv` and regenerate.
- **Do not edit `scripts/roster_lib.py` from a city driver** — library-fit problems get
  reported to `roster_HARDENING.md`, not patched per-city.
- A validation FAILURE is information. Read it, model the missing event, don't suppress it.

## Hardening backlog (open items from `scripts/roster_HARDENING.md` — future work)

- **C2 — multi-source-year precinct calibration.** `precinct_hi_source` accepts only ONE
  `high` source-year, so a city whose current precinct map is validly sourced from **more than
  one** post-redistrict election (SLC: 2023 even + 2025 odd) reads ~57% of `plan_2022` rows as
  `medium` despite equal authority. Cosmetic (each row's note says so). Fix: accept a SET of
  years.
- **Fold the detection checks into `roster_lib` as build-time guards.** The **bidirectional
  election crosscheck** (§2) and the **8th-voter / roll-size sentinel** currently live in this
  skill (and `reference.md`); promoting them into `roster_lib.validate()` would make them
  fail-loud on every build for every city (the name-change union guard from C1 is already in).
