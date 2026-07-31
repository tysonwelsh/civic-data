# roster/ — Salt Lake City rolling council-roster (interval / slowly-changing-dimension layer)

A **DERIVED, regenerable** layer tracking **who holds each SLC City Council + Mayor seat over
time** as dated intervals, reconciled from multiple sources with **per-row provenance and
confidence**. Answers: *who was on the council on date X?*, *who is serving now?*, *who
represents this address on this date?* — none of which the flat CSVs can answer.

SLC is the repo's **largest / most complex** roster: **7 geographic council districts**
(D1..D7, **NO at-large/citywide council seats**) + a **separately-elected Mayor** who does
**NOT** vote on council motions; council votes exist **only 2021+** (LLM-extracted) while the
county election record runs **2007+** (the repo's longest); and the 7 districts were **redrawn
after the 2020 Census** (Resolution 9 of 2022). It is a district city like Provo
(`provo_city_council/roster/`) and reuses the same shared builder (`../../scripts/roster_lib.py`).

## Files

| File | Role |
|------|------|
| `build_roster.py` | Thin driver (SLC data + config). Regenerates all three CSVs idempotently. `--demo` prints the query patterns; `--check` runs validations + the precinct cross-check. |
| `council_terms.csv` | **Core table** — 52 tenures (incl. 6 VACANT) across 8 stable seats. |
| `district_versions.csv` | Boundary interval table — **REAL 7 districts × 2 plans** (the 2022 redistricting) + a Mayor/citywide row. |
| `district_precincts.csv` | **Versioned precinct → district composition** (plan-scoped; shares `plan_id`/dates with `district_versions`). 144 plan_2022 rows + **107 plan_2012 RECONSTRUCTED rows** (`medium`, 2026-07-19; 16 of D7's holes absent). |
| `roster_overrides.csv` | Hand-correction layer, applied **last**, wins ties. Currently **0 data rows**. |

**Never hand-edit the three generated CSVs** — regenerate with `python3 roster/build_roster.py`.
All corrections go in `roster_overrides.csv`.

## `council_terms.csv` schema
`city, body, seat_id, district, person_name, person_key, start_date, end_date, start_event,
end_event, election_year, first_vote, last_vote, sources, confidence, note`

- **`body`** ∈ {`Council`, `Mayor`}. **`seat_id`** — STABLE id (a redistricting redraws
  boundaries, it does NOT renumber seats): `D1..D7` + `MAYOR`.
- **`start_date` / `end_date`** — half-open `[start, end)`; `end_date` empty = currently serving;
  chained per seat (a tenure ends when the next on the same seat begins).
- **`start_event`** ∈ {elected, reelected, appointed, became-mayor, vacated}. **`end_event`** ∈
  {reelected, lost, did-not-run, resigned, became-mayor, elected, appointed, serving, filled}.
- **`first_vote`/`last_vote`** — first/last observed **Council-body** vote from `cities.db`
  (`role`, `city='slc'`, `body='Council'`), **clamped to each tenure's own `[start_date,
  end_date)` window**. Mayor rows are blank (the Mayor does not vote). A pre-2021 tenure whose
  only recorded votes fall in a LATER tenure is therefore **BLANK** (the clamp finds no vote
  inside its window); a pre-floor person who never voted is likewise blank.
- **`confidence`** — `high` = election result confirmed by minutes/votes, or a minutes-documented
  oath/appointment/resignation/the redistricting resolution · `medium` = an **election-anchored
  term that predates the 2021 vote-data floor** (flagged, no vote corroboration), a **gap-bounded
  vacancy/departure**, or a pre-2020-minutes-floor inferred date · `low` = unknown/not-acquired
  (none in `council_terms`; the `low` rows live in the district/precinct gap records).

**Counts: 52 tenures — 18 high / 34 medium / 0 low; 6 VACANT intervals.** 0 overlapping
tenures per seat. All shared-library validators pass (overlap, sources/confidence, seat_id,
the vacate-confidence invariant, and the un-recovered-minutes gap detector).

### The 8 seats and their stagger

| Cycle | Seats | Elected | Term starts |
|---|---|---|---|
| **ODD** | `D1`, `D3`, `D5`, `D7` | 2009 / 13 / 17 / 21 / 25 | Jan 2010 / 14 / 18 / 22 / 26 |
| **EVEN** | `D2`, `D4`, `D6`, `MAYOR` | 2007 / 11 / 15 / 19 / 23 | Jan 2008 / 12 / 16 / 20 / 24 |

Documented Jan first-meeting/swearing dates (= `cities.db` `role.first_seen`): **2020-01-07 ·
2022-01-04 · 2024-01-09 · 2026-01-13**. Pre-2020-floor term-starts use `YYYY-01-01` (inferred
from the stagger, flagged medium — same convention as Provo's 2017-cycle rows).

## Span covered, and how the pre-vote-floor era is handled

The roster runs **2008 → present** (the 2007 election onward). Two eras:

- **Documented era (2020-01 → present)** — every tenure is attested by 2020 minutes present-lists
  and/or the 2021+ vote record; all the appointment/vacancy detail lives here (mostly `high`).
- **Election-anchored era (2008 → 2019)** — built from the clean 2007–2017 county-file winners.
  These are **flagged `medium`**: the *win* is a documented fact, but there is **no vote
  corroboration** (votes are 2021+) and **continuous personal service is inferred from the
  election chain, not verifiable below the 2020 minutes floor** — every such row says so in its
  `note`. No fake `first_vote`/`last_vote` is invented for them. Where a mid-term departure IS
  publicly documented (Kitchen → Utah Senate 2019; Mendenhall D5 → Mayor 2020), it is modeled
  rather than glossed.

We did **not** fabricate deeper structure than the sources support: the 2019 winners are a
**broken-file gap** (below), and any un-documented pre-2020 mid-term substitution inside an
election-anchored interval is acknowledged as unobservable rather than guessed.

## The 4-layer reconciliation (in `build_roster.py`)

1. **Elections** — `election_results/slc_results_by_candidate.csv`, municipal **general** winners
   only (2007+). Each winner maps to a seat via `seat_for_contest` (District N → `D-N`; Mayor →
   `MAYOR`). UPPER-CASE names normalized; **LUKE/GARROTT disambiguation** keys Luke Garrott (D4)
   on surname `GARROTT` and Charlie Luke (D6) on first name `CHARLIE` (both unique) and never maps
   the bare token `LUKE`. The forward cross-check confirms every general winner maps to a tenure.
2. **Vote / attendance bounds** — `cities.db` `role` (`city='slc'`, `body='Council'`): sets
   `first_vote`/`last_vote`. **Mayor Mendenhall is correctly ABSENT** from this table — she does
   not vote on council motions. SLC's council also sits in-session as **RDA/CRA/LBA** (same people,
   different capacity); the roster is kept to `body=Council` + `Mayor` — no separate RDA tenures.
3. **Minutes events** — oath / appointment / resignation dates + the redistricting resolution, read
   from `meeting_minutes/minutes/**` (and `cities.db` `fts_minutes`) and encoded in `TENURES`.
4. **Overrides** — `roster_overrides.csv`, applied last, wins ties.

Then `end_date` is chained, the **VACANT-interval** rule runs, and the table is validated (a
failure aborts the write).

## The mid-term vacancies & appointments (SLC's distinctive surface — spot-checked)

SLC had an unusually busy 2020–2026 for mid-term turnover. Each is source-quoted:

- **D5 · Mendenhall → Mano (2020).** Mendenhall vacated D5 to become **Mayor** (present as *"Erin
  Mendenhall, Mayor"* by 2020-01-07). D5 filled by **appointment 2020-01-21**: minutes —
  *"Adopting a resolution appointing Darin Masao Mano as … District Five Councilmember. All Council
  Members were in favor."* → **VACANT D5 2020-01-07 → 2020-01-21 (`high` — both endpoints
  documented).** Mano then won the 2021 D5 general.
- **D2 · Johnston → Faris → Puy (2021).** Johnston (D2, conducting formal meetings through
  2021-04) **resigned** (last vote 2021-04-20). **Dennis Faris appointed** (present as a Council
  Member 2021-05-18), **ran the Nov-2021 D2 special and LOST**, served only the interim.
  → **VACANT D2 2021-04-20 → 2021-05-18 (`medium`, gap-bounded).**
- **D1 · Rogers → Petro (2021).** Rogers **resigned** (last vote 2021-09-21); by 2021-11-09 the
  Council was *"interview[ing] applicants for the vacant Council District One seat"* while
  **Victoria Petro-Eschler**, having just won the Nov-2021 D1 general, was **seated early
  (2021-11-16)** to fill the remainder. → **VACANT D1 2021-09-21 → 2021-11-16 (`medium`).**
- **D7 · Fowler → Young (2023).** Fowler **resigned** (farewell + last vote 2023-06-13); minutes
  2023-07-13 — *"Sarah Young was appointed as the new District 7 Council [member]."* Young then won
  the **Nov-2023 D7 special**. → **VACANT D7 2023-06-13 → 2023-07-18 (`medium`).**
- **D4 · Kitchen → Valdemoros (2019, pre-floor).** Kitchen left mid-term ~Jan 2019 on election to
  the **Utah State Senate**; Valdemoros was appointed (and also held the 2019 seat). Dates are
  below the 2020 minutes floor → **VACANT D4 2019-01-01 → 2020-01-07 (`medium`, approximate).**
- **D4 · Lopez Chavez → Napier-Pearce (2026).** Eva Lopez Chavez **resigned** (last vote
  2026-05-05; a documented *"District 4 Council vacancy process"* runs in minutes 2026-05-12/05-14;
  the 2026-05-12/05-19 sittings show only 6 members). **Jennifer Napier-Pearce appointed
  2026-06-09** (*"all CM's plus jennifer napier pearce"*). → **VACANT D4 2026-05-05 → 2026-06-09
  (`medium`).**

**Mayor is NOT a council voter (verified):** Mendenhall is absent from the `cities.db` council
`role` table and never appears in `all_votes.csv`'s member column — council votes are 7-member.
The roster's Mayor rows carry blank `first_vote`/`last_vote` accordingly.

## Known SOURCE DEFECTS (honest gaps, never fabricated around)

- **2019 general SOVC — FIXED 2026-07-19** (was: candidate names lost, only `Vote By Mail`/
  `Vote Centers`/`Early Voting` vote-method rows). The stale garbled slice was re-synced from
  the election archive's family-B re-parse; the election file now carries the real 2019
  winners (**Johnston D2 1,745 · Valdemoros D4 4,734 · Dugan D6 4,655 · Mendenhall Mayor
  26,762** — verified against the raw workbook's own `Total:` rows; see
  `../election_results/CLAUDE.md`). The affected tenures keep their minutes/vote anchoring
  and `medium` confidence UNCHANGED (terms are byte-identical to the pre-fix build; their
  `note` text still describes the defect as it stood when they were curated). The four H-C
  reverse-crosscheck exceptions were removed; the old `unmapped winner 2019 … VOTE BY MAIL`
  forward-check lines are gone. One NEW expected forward-check line: `winner not in roster:
  2019 D4 ANA VALDEMOROS` — a modeling artifact, not drift (her single D4 tenure is
  `start_event=appointed`: appointed to Kitchen's vacancy AND won the 2019 general; the
  forward check only matches elected-event tenures).
- **2021 D2 "Puy-not-Palmer" — FIXED 2026-07-19; it was never an RCV mislabel.** The
  "Palmer 363 / Puy 361 first-choice" ordering was a **partial-count artifact**: the county
  suppresses low-turnout precincts' vote-method rows (`****`) but prints each precinct's
  Total row, and the upstream normalizer dropped all Total rows. The certified first-choice
  totals are **PUY 1,084 / Palmer 751** — Puy is the plurality leader AND the seated member
  (2022-01-04+), so the election file's `is_winner` now agrees with the roster; the
  `unmapped winner 2021 Council 2 BILLY PALMER` line is gone and the Puy H-C exception was
  removed. (SLC 2021 was still an RCV-pilot election — the SOVC stores first-choice
  tallies — but all 2021/2023/2025 first-choice leaders match the seated members.) Puy's
  tenure `note`, originally written against the defective numbers, was REFRESHED 2026-07-19
  to the corrected tallies (PUY 1,084 42.53% / Palmer 751, margin 333 / 13.06% — verbatim
  from `../election_results/slc_races.csv`); only the note/text field changed, the
  interval/person/seat/confidence rows stay byte-identical.
- **Darin Mano stray 2026 vote.** `cities.db` shows a lone Mano vote-attribution on **2026-03-24**
  (one of two same-day meetings), *after* Carlsen was seated 2026-01-13 — a known **stray LLM
  vote-extraction artifact** (SLC council votes are LLM-extracted). It does **not** extend Mano's
  tenure; **no** post-2026-01-13 Mano tenure is created. (His `last_vote` **no longer shows it**:
  the per-tenure vote clamp bounds each tenure to its `[start_date, end_date)` window, and
  2026-03-24 falls outside his D5 term that ended 2026-01-13, so `last_vote`=2025-12-09.)
- **Victoria Petro name change.** Filed as *Petro-Eschler* (2021) and *Petro* (2025) — the **same
  person**; `cities.db` carries **two** name_keys (`victoriapetroeschler` + `victoriapetro`), both
  mapped to `victoria_petro`. Her true vote span is 2021-11-16 → 2026-06-09.

## `district_versions.csv` — REAL 7 districts + the 2022 redistricting

`city, district_id, plan_id, effective_start, effective_end, geometry_ref, adopted_by,
source_url, confidence, note`. Geometry is **not** stored inline — `geometry_ref` points at
`geo/slco_precincts_current.geojson`.

**SLC DID redistrict** after the 2020 Census: **Resolution 9 of 2022**, *"Redistricting City
Council District Boundaries,"* designating the seven lines from the 2020 Census (Exhibit A).
Adopted at the **2022-05-10** limited formal meeting, then **reconsidered and re-adopted 7-0 on
2022-05-17** to correct a single property inadvertently placed in **District Six** (moved to
**District Three**). First used for the **2023** (even D2/D4/D6) and **2025** (odd D1/D3/D5/D7)
elections. *(Note: SLC redistricts by **resolution**, not ordinance — unlike Provo's Ordinance
2022-13.)*

Versioning (15 rows):
- **`plan_2022`** (current) for D1–D7 — real geometry in `geo/slco_precincts_current.geojson`,
  `effective_start=2022-05-17`, open-ended, **high**.
- **`plan_2012`** (prior) for D1–D7 — RECONSTRUCTED 2026-07-19; **ALL districts' GEOMETRY confidence
  DOWNGRADED to `low` 2026-07-19** (was D1–D6 `medium` / D7 `low`): `geometry_ref=geo/council_districts_
  pre2022.geojson` (107/124 old codes). VALIDATION 2026-07-19: fetched SLC's authoritative GIS
  (Salt_Lake_City_Council_Districts + the legacy City_Council_Boundries) — BOTH are the CURRENT 2022 plan
  (IoU 0.995, 2022-era members); SLC publishes NO 2012-vintage layer. A fragmentation control PROVES the
  renumbering is CITY-WIDE, not just D7: the current-assignment dissolve = clean 1-piece districts, but
  this pre-2022 dissolve = **2–15-piece fragments (D6=15, D5=9, D4=7, D2=6)** EVEN for D1–D6 whose codes
  are all "present" → code-presence ≠ geometric fidelity; the county renumbered the SLC precinct codes
  (the millcreek defect) → geometry unreliable, `low` across all 7. The `district_precincts` precinct-CODE
  composition stays `medium` (a faithful SOVC record). In force for the 2007–2021 elections. See
  `scripts/roster_boundary_recon.md`.
- **`citywide`** row for `MAYOR` — whole-city extent, unaffected by redistricting, open-ended,
  high. (SLC has **no** at-large council seats, so there is no Citywide *council* row.)

## `district_precincts.csv` — versioned precinct → district composition

144 **`plan_2022`** rows from `geo/precinct_to_district.csv` + **107 `plan_2012` RECONSTRUCTED rows**
(`medium`, from `geo/precinct_to_district_pre2022.csv`; 17 renumbered/retired codes are honest holes,
absent — **16 of them in D7**, so D7 has only 6 plan_2012 rows; was 7 blank `low` GAP rows before
2026-07-19). Per-district plan_2012 counts: D1 13 · D2 9 · D3 22 · D4 15 · D5 21 · D6 21 · **D7 6**.

⚠️ **A place the shared library doesn't fit SLC cleanly:** the current SLC precinct→district map is
sourced from **two** equally-authoritative post-redistrict elections (2023 even + 2025 odd), but
`roster_lib.write_precincts()` can flag only **one** `source_year` as `high` (`precinct_hi_source`).
We set it to `2025`, so the **2023-sourced (even-district) rows read `medium`** — this is a
**library single-source-year limitation, NOT a data-quality distinction** (their `note` says so).
See "roster_lib fit notes" below.

### Precinct-map cross-check (`--check` / demo (e))

For each cycle+district with precinct data, the builder groups precinct votes by the
`district_precincts` (plan_2022) assignment and confirms the winner matches the roster:

| Cycle | Districts | Plan | Result |
|---|---|---|---|
| 2023 | D4, D7 | plan_2022 | **RECONCILES** (Lopez Chavez, Young) |
| 2025 | D1, D3, D5, D7 | plan_2022 | **RECONCILES** (Petro, Wharton, Carlsen, Young) |
| 2007–2021 | all | plan_2012 | **GAP at the runtime check** — old cycles can't be graded against the *current* plan_2022 map; the plan_2012 composition is now reconstructed (`medium`; D7 `low`), aggregate winner still matches |

All six `plan_2022` checks reconcile exactly (precinct-sum winner == citywide winner == roster
winner). **D2 and D6 are deliberately excluded from the automated string-match** (`crosscheck_
districts=("1","3","4","5","7")`) only because the election file spells them **`ALEJANDRO "ALE"
PUY`** and **`DAN DUGAN`** while the vote record / roster use `Alejandro Puy` / `Daniel Dugan` —
a nickname/abbreviation formatting mismatch, **not** a data discrepancy. Both are hand-verified to
reconcile: **2023 D2** — Puy ran **unopposed (100%)**; **2023 D6** — the precinct-sum leader
`DAN DUGAN` (3,967) is the seated `Daniel Dugan`.

## Honest gaps (recorded, not filled)

- **Prior (`plan_2012`) geometry + precinct composition** — **RECONSTRUCTED 2026-07-19** (was
  `low`/blank rows): `district_versions` carries `geometry_ref=geo/council_districts_pre2022.geojson`
  with **ALL 7 districts' geometry `low`** (DOWNGRADED 2026-07-19 from D1–D6 `medium`/D7 `low` after the
  fragmentation control proved city-wide precinct-code renumbering — see the `plan_2012` bullet above);
  `district_precincts` keeps 107 populated `medium` rows (the precinct-CODE composition is a faithful
  SOVC record, geometry-independent). **APPROXIMATE** — pre-2022 assignment over current-vintage shapes,
  renumbering-corrupted. No authoritative 2012 layer exists (both SLC-org council layers are the current
  2022 plan); firming up the geometry would need a 2020-vintage VistaBallotAreas snapshot with the retired
  codes (probed 2026-07-19; not an open endpoint). See `scripts/roster_boundary_recon.md`.
- **2019 general winners** — the SOVC slice was FIXED 2026-07-19 (real winner rows restored;
  see Known SOURCE DEFECTS above); the tenures deliberately keep their 2020-minutes/votes
  anchoring + `medium` confidence (the fix is election data, not new tenure evidence).
- **Election-anchored 2008–2019 terms (`medium`)** — win = fact, continuous service = inferred
  (pre-2020 minutes floor); no fake vote bounds.
- **Pre-floor vacancy dates** — the Kitchen→Valdemoros (2019) window is approximate (below the
  minutes floor); flagged medium.

## How to query
```bash
python3 roster/build_roster.py --demo    # (a) current (b) as-of (c) address→rep (d) redistricting (e) cross-check
python3 roster/build_roster.py --check   # validations + precinct cross-check
```
- **Current roster** — rows where `end_date` is empty and `end_event='serving'`.
- **As of a date** — `roster_as_of(date, body)`.
- **Address + date → representative** — `representatives_for_address(address, date)`: resolves an
  SLC address via `geo/address_to_district.py` (Census geocode → precinct point-in-polygon →
  `precinct_to_district.csv`) to **District N**, returns that district's rep on `date` + the Mayor.
  **SLC grid-intersection geo quirk:** SLC addresses are approximate grid intersections, not
  parcels; the geocoder still returns a point and point-in-polygon gives the precinct. It honors
  `district_versions`: a **pre-2022 date returns an honest GAP** — the shared query helper
  point-in-polygons only against the CURRENT precinct map, so it does not seat a district for a
  `plan_2012` date (never a fabricated district), which is exactly what demo (d) shows across the
  redistricting. *(The `plan_2012` boundary geometry itself is now RECONSTRUCTED on disk —
  `geo/council_districts_pre2022.geojson`, wired into `district_versions` (D1–D6 `medium`, D7 `low`)
  / `district_precincts` — but the address→rep helper is unchanged from the 5-city convention and
  still gaps on plan_old dates; a plan-aware point-in-polygon against the reconstructed layer is a
  possible follow-up.)*

## roster_lib fit notes (for hardening before the backlog cities)

Two spots where the shared library did not fit SLC cleanly (report, don't patch here — the lib is
off-limits from this driver):

1. **Two db name_keys → one person (name changes).** `load_vote_bounds` does `bounds[pk] = (fs,ls)`,
   so when several `cities.db` name_keys map to one `person_key` (Victoria **Petro-Eschler** +
   **Petro**), the last row **overwrites** rather than taking the **union** — a multi-name person's
   `first_vote`/`last_vote` can reflect only one of their db records. Suggest: aggregate
   `min(first_seen)`/`max(last_seen)` across all name_keys that share a `person_key`.
2. **Single `precinct_hi_source`.** A city whose current precinct map is validly sourced from
   **more than one** post-redistrict election (SLC: 2023 even + 2025 odd) can mark only one
   `source_year` `high`; the other reads `medium` despite equal authority. Suggest: allow
   `precinct_hi_source` to be a **set/tuple** of years.

(Also worth noting for the fleet: SLC exercises code paths Provo/Nephi/Vineyard did not — a
council→**mayor** move that vacates a district seat, an appointee who then **loses** the special
that fills their own seat (Faris), a **name-change** person, and a redistricting adopted by
**resolution**. All validated green.)
