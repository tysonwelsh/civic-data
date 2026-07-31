# West Valley City roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `west_valley_city_council/roster/` reconciled against `election_results/`,
`meeting_minutes/minutes/**`, root `cities.db`, and the repo cardinal rules.
**Verdict:** **CLEAN.** No data defects. One documentation-only (LOW) prose imprecision
in provenance notes. All eight attack surfaces verified against source with quoted evidence.

READ-ONLY audit — no roster CSV / library / rebuild was touched.

---

## (A) CONFIRMED DEFECTS

**None.** Every tenure interval, confidence grade, vacancy chain, appointment, and the
voting-mayor / single-winner-at-large / RDA-exclusion modelling verified against source.

---

## (B) CALIBRATION / HONEST-GAP ITEMS

### B1 (LOW, documentation only) — 9 notes + CLAUDE.md cite an RDA date (`2026-06-09`) as the "cities.db person-level vote bound", but the Council-body last vote is `2026-05-26`
The `last_vote` **column** is correct in every row (Council-body max = `2026-05-26`; verified
`awk` over col 13 returns only `2021-12-14 / 2024-12-10 / 2026-05-26`, never `2026-06-09`).
But nine `note` strings — and the roster `CLAUDE.md` schema section — describe the bound as
`2026-06-09`, e.g. row 22 (Lang MAYOR):

> "votes:person-level 2020-01-07..**2026-06-09** (cities.db)"

`2026-06-09` is the **RDA** body's `last_seen`, not a Council vote. Confirmed in `cities.db`:

```
Council | Tom Huynh  | MAX(meeting_date) = 2026-05-26
RDA     | ...        | 2026-06-09
```

`role` for `city='west_valley', body='Council'` tops out at `2026-05-26` for every current
member. The DATA is right; only the prose over-reaches by quoting an across-body/RDA date on
a layer that is explicitly Council-scoped ("person-level bounds from cities.db … body='Council'").
**Fix:** in the affected note strings + CLAUDE.md, change `2026-06-09` → `2026-05-26` (the
Council-body max), or annotate that `2026-06-09` is the across-body max and not a Council poll.
Cosmetic — no query returns a wrong answer.

### B2 (honest gap, correctly recorded) — `plan_pre2022` geometry + precinct composition not on disk
`district_versions.csv` carries the pre-2022 lines as `confidence=low`, `geometry_ref` blank;
`district_precincts.csv` has 4 `plan_pre2022` GAP rows (blank `precinct_id`, `low`). The
`--check` cross-check correctly labels 2019 D1 / 2021 D4 as **GAP** (aggregate winner still
matches). Not reconstructable from disk — honest, not filled.

### B3 (honest calibration) — the 4 `medium` holdovers are honestly flagged, not overstated
Buhler (D2), Fitisemanu (D4), Nordfelt (AL2), Bigelow (MAYOR) all carry `start_event=in-office`,
**blank `election_year`**, `start_date=2020-01-07` (the data floor / first documented meeting) —
no fabricated seating date or phantom election. Their 2017-cycle origin is below the 2019
election-data floor; service is vote-documented from 2020-01-07. Correctly `medium`, not `high`.

### B4 (analytical construct, correctly disclosed) — AL1/AL2 seat ids
The county ballots label both at-large contests simply "At-Large" (no seat number); the roster's
AL1/AL2 are analytical ids. But because each is a single-winner Vote-for-1 contest on a distinct
cycle (AL1 = 2019/2023, AL2 = 2021/2025), `(year, "At-Large", person)` is unambiguous and the
mapping is a stable 1:1. Milder than West Jordan's grouped Vote-for-N. Correctly documented.

---

## (C) HARDENING RECOMMENDATIONS

- **B1 is the only actionable item** and it is a note-string/CLAUDE.md text fix (batch it with
  the fleet's existing "vote-bound clamp" note-hygiene backlog — the same person-level-bound
  prose issue was logged for Lang/Fitisemanu/Wood cross-tenure smear). No code change needed.
- Otherwise **none.** The build already worked around the two logged library gaps (`source_year`
  column + blank-vote guard) with the standard derived sidecars, exactly as five prior cities did.

---

## Evidence log (per task item)

### 1. VOTING mayor — CONFIRMED (highest-scrutiny, inverted from last 2 cities)
The WVC mayor is polled on **routine legislation**, not just tie-breaks:
- **2022-03-15, Ordinance 22-10** (the redistricting), full 7-member roll:
  `Fitisemanu Yes / Whetstone Yes / Harmon Yes / Huynh Yes / Christensen Yes / Nordfelt Yes /
  **Mayor Lang Yes** / Unanimous.`
- **2020-01-13/14** routine roll: `Fitisemanu Yes / Lang Yes / Buhler Yes / Christensen Yes /
  Nordfelt Yes / **Mayor Bigelow Yes** / Unanimous.` (Bigelow votes too.)
- `cities.db`: both mayors are Council voters — `Ron Bigelow` (Council, 2020-01-07..2021-12-14,
  422 votes) and `Karen Lang` (Council, 2020-01-07..2026-05-26, 1185 votes).
- **Max distinct voters per Council motion = 7** (1,079 motions at exactly 7); the mayor is the
  7th. No roll exceeds 7. `non_voting_mayor=False` is correct; MAYOR rows legitimately carry bounds.
- **No cross-tenure smear in the DATES:** Lang D3 `[2020-01-07, 2022-01-04)` and MAYOR
  `[2022-01-04, 2026-01-13)` / `[2026-01-13, )` do not overlap. The person-level vote bounds
  (identical on both) are documented per row as informational (see B1).

### 2. Single-winner at-large — CONFIRMED
`west_valley_results_by_candidate.csv` shows exactly **one** "At-Large" Vote-for-1 winner per
cycle: 2019 **DON CHRISTENSEN** (56.66%), 2021 **LARS NORDFELT** (59.59%), 2023 **DON
CHRISTENSEN** (58.41%), 2025 **LARS NORDFELT** (54.82%). → AL1 = 2019/2023 (Christensen), AL2 =
2021/2025 (Nordfelt). Cycle assignment correct; no district winner mis-filed as at-large or vice
versa. Four at-large winners across four cycles map onto the two AL seats.

### 3. Vacancy chains — CONFIRMED
- **D3:** Lang won Mayor 2021 → vacated D3. Minutes 2022-01-18: *"a midterm vacancy has occurred
  in District 3 with the election of Karen Lang as Mayor … the office of Councilmember District 3
  unfilled with a remaining term of two years."* **Resolution 22-11** appointed Whetstone; the
  final passing roll was **6-0** (`Fitisemanu Yes / Harmon Yes / Huynh Yes / Christensen Yes /
  Nordfelt Yes / Mayor Lang Yes / Unanimous`) — Whetstone then moved to adjourn (seated that
  night). VACANT **[2022-01-04, 2022-01-18)**, `high`, no overlap. (Rolls in this window show 6
  voters, no D3 — consistent with the vacancy.)
- **D4:** Minutes 2025-01-28: *"This vacancy was created when Jake Fitisemanu was elected to State
  House District 30 in the 2024 General Election. The vacancy, governed by Utah State Code
  20A-1-510, lasts until the end of the year."* Fitisemanu's last Council vote = **2024-12-10**
  (cities.db). **Resolution 25-11** appointed Wood, **6-0**, and *"Nichole Camac, City Recorder,
  perform[ed] the oath of office … Councilmember Wood joined the Council on the dais."* VACANT
  **[2024-12-11, 2025-01-28)** — begins the day AFTER last service — `high`, closes exactly at
  Wood's appointment. No overlap.
- Both successors then won outright (Whetstone 2023 seated 2024-01-02; Wood 2025 seated
  2026-01-13); appointed tenures end where the elected term begins.

### 4. Karen Lang — one person, D3→Mayor — CONFIRMED
`cities.db` has a single `Karen Lang` person (`person_id=130000014`, `name_key=karenlang`)
spanning both bodies; her Council votes run 2020-01-07..2026-05-26 continuously. D3 and MAYOR
intervals do not overlap (see #1). She is the only two-seat person.

### 5. The 4 `medium` holdovers — CONFIRMED honestly flagged
See B3. Exactly Bigelow MAYOR / Nordfelt AL2 / Buhler D2 / Fitisemanu D4; `start_event=in-office`,
blank `election_year`, no fabricated seating. Not overstated to `high`.

### 6. RDA / MBA did not leak — CONFIRMED
`council_terms.csv` bodies = **19 Council + 3 Mayor** only; seat_ids = D1–D4, AL1–AL2, MAYOR.
`grep -i "RDA|MBA|Redevelopment|Building Authority"` over the file returns **nothing**. cities.db
shows the same people carry RDA (132) and MBA (63) roles, but `load_vote_bounds` reads only
`body='Council'`, so no RDA/MBA seat was created.

### 7. Redistricting Ord 22-10 — CONFIRMED
Minutes 2022-03-15: *"ORDINANCE 22-10: AMEND TITLE 2, CHAPTER 3 … MAKING ADJUSTMENTS IN THE WEST
VALLEY CITY COUNCIL DISTRICT BOUNDARIES,"* 2020 Census, each district within 1% of ideal, motion
Harmon "Option 1" / second Huynh, roll **7-0 including Mayor Lang**. `plan_2022` real (high),
`plan_pre2022` GAP (low/blank). Precinct cross-check: **D1 (2023, TOM HUYNH) and D4 (2025, CINDY
WOOD)** auto-reconcile (names match exactly). **D2 and D3 excluded** because the by-precinct
ballot spells the winners **`SCOTT L. HARMON`** (2025 D2) and **`WILL WHETSTONE`** (2023 D3) vs
roster `Scott Harmon` / `William Whetstone` — verified a name-FORMAT difference, not a data
mismatch (same precinct-sum leaders are the seated members). Exclusions are legitimate, hide no
real discrepancy. Zero suppressed cells in the by-precinct data (defensive sidecar drops nothing).

### 8. Structural invariants + winner mapping — CONFIRMED
22 tenures, **18 high / 4 medium / 2 VACANT**. Per-seat chaining verified programmatically:
**every seat's intervals are contiguous half-open with no gap and no overlap.** All **14** general
winners (2019/2021/2023/2025 × their contests) map to a tenure with matching `election_year`.
Current roster (D1 Huynh / D2 Harmon / D3 Whetstone / D4 Wood / AL1 Christensen / AL2 Nordfelt /
MAYOR Lang) matches the **2026-01-13** present list verbatim:

> Karen Lang, Mayor / Lars Nordfelt, At-Large / Don Christensen, At-Large / Tom Huynh, District 1 /
> Scott Harmon, District 2 / William Whetstone, District 3 / Cindy Wood, District 4

No OCR / name corruption in any person field.

---
## RESOLUTION ADDENDUM — 2026-07-11 (post-audit): vote-bound smear FIXED fleet-wide
Any observation in this audit describing a `first_vote`/`last_vote` **person-level smear** (a
councilmember→mayor person's mayor-era vote appearing on a council tenure, or a re-elected
member's whole-career span repeated on each term row) is **RESOLVED**. `scripts/roster_lib.py`
now CLAMPS `first_vote`/`last_vote` to each tenure's own `[start_date, end_date)` window
(`load_vote_dates()` + `clamp_vote_bounds()`), so each tenure carries only its own window's votes
(blank if none). The per-city de-smear overrides (Park City Worel, St George Randall) are retired —
the clamp reproduces their corrected values structurally. See `scripts/roster_HARDENING.md`
(hardening item #2). This addendum records the resolution; the dated findings above are unchanged.
