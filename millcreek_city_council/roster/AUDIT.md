# Millcreek roster/ — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this layer)
**Scope:** `roster/` (council_terms.csv · district_versions.csv · district_precincts.csv ·
roster_overrides.csv · precinct_to_district.csv · build_roster.py) vs. the sources
(minutes markdown, `election_results/`, root `cities.db`).
**Method:** READ-ONLY. The generated CSVs were NOT rebuilt; every cross-check below was
replicated read-only against the source files, or verified by direct quotation of the
on-disk minutes. Constraint honored: no roster CSV, `roster_lib.py`, or geo file modified.

## Verdict

**CLEAN — 0 confirmed data defects.** Every load-bearing claim in `council_terms.csv`,
`district_versions.csv`, and `district_precincts.csv` reconciles to a quoted source. The
two hardest cases (the Nov-2025 council→mayor + VACANT succession, and the voting mayor)
are correct and are corroborated by evidence beyond what the builder cited. Findings below
are (B) calibration/honest-gap notes and (C) shared-library hardening recs only.

---

## A. CONFIRMED DEFECTS

**None.** No row requires a fix.

---

## Evidence log (what was verified)

### 1. Nov-2025 succession — council→mayor + VACANT (highest risk) — CONFIRMED
- **Silvestrini resigned:** `minutes 2025-10-13` line 393 — *"Mayor Silvestrini reported on
  his midterm vacancy and the process for finding a [successor]."* `minutes 2025-11-03`
  line 229 — he *"reflected on the weight of resigning after nine years of service."*
- **Res 25-38 appoints Jackson Mayor:** `minutes 2025-11-03` lines 286–290 — *"Discussion
  and Consideration of Resolution 25-38, Filling the Mid-Term Vacancy of the [Mayor] …
  Council Member Uipi moved to approve Resolution 25-38."*
- **Jackson sworn in as Mayor 2025-11-10:** `minutes 2025-11-10` lines 207–208 — *"Alex
  Wendt, the Deputy Recorder administered the Oath of Office to Mayor-Elect Cheri
  Jackson."*
- **D3 → Handy, Res 25-42, oath 2025-11-24:** `minutes 2025-11-24` lines 375–387 —
  *"Resolution 25-42, Filling the Mid-Term Vacancy of Council District 3 with Nicole Handy
  … The ballots unanimously reflected Nicole Handy as the winner … The City Recorder
  administered the oath of office to Nicole Handy."*
- **VACANT window [2025-11-10, 2025-11-24) is real — independently corroborated.** A meeting
  fell *inside* the window: `minutes 2025-11-18` (bucketed to the `2025-11-17` Monday
  folder). Mayor Jackson presides (line 49) and the roll call names only *"Catten … DeSirant
  … and Mayor Jackson"* (line 64) — **3 voters, D3 empty, no Handy, no Jackson-as-D3**. This
  is stronger than the builder's own note (which only argued the window contained no
  *un-recovered* minutes); the recovered meeting positively demonstrates the vacancy.
- **`roster_as_of('2025-11-17')`** (verified by hand against the half-open intervals):
  D1 Catten, D2 DeSirant, **D3 = VACANT**, D4 Uipi, **MAYOR = Jackson.** Matches the claim.
- **No D3/MAYOR overlap for Jackson:** D3 ends `2025-11-10` (exclusive); MAYOR starts
  `2025-11-10` (inclusive). Half-open → no overlap. ✓
- **Both appointees carry blank `election_year`** (Jackson MAYOR row 21; Handy D3 row 13) and
  there is **no 2025 mayoral or D3 race** in `millcreek_results_by_candidate.csv`. ✓
- **cities.db** person-level bounds: `nicolehandy` first_seen 2025-11-24 (matches appointment);
  `jeffsilvestrini` last_seen 2025-11-10 (matches resignation day). ✓

### 2. Founding council marked `high` (not medium) — CONFIRMED justified
- `minutes 2017-01-09` lines 24–28 list the seated officials verbatim: *"Jeff Silvestrini –
  Mayor / Silvia Catten – Council District 1 / Dwight Marchant – Council District 2 / Cheri
  Jackson – Council District 3 / Bev Uipi – Council District 4."*
- `minutes 2016-12-27` (City Council-Elect) lines 24–28 list the same five as
  *"…Council Elect – In Attendance."*
- All five are the 2016 general winners in `millcreek_results_by_candidate.csv` (rows 2–10).
- `high` is correct: Millcreek's entire history is in-window (data floor 2016-12-28 =
  incorporation), so the founding council is **documented, not inferred** — the opposite of
  the older cities' pre-floor `medium` 2017-cycle terms. No fabrication.

### 3. Voting mayor — CONFIRMED (`non_voting_mayor=False` correct)
- `minutes 2023-12-11` lines 83–84 / 145–146 / 156–157 / 238–239 (four roll calls), each:
  *"Council Member DeSirant voted yes, Council Member Jackson voted yes, Council Member Uipi
  voted yes, **and Mayor Silvestrini voted yes.** The motion passed unanimously."* — the
  5-vote roll call topping out at the mayor.
- `minutes 2025-11-10` lines 165–167 shows the same 5-member pattern (Catten/DeSirant/
  Jackson/Uipi + Mayor Silvestrini) at the work meeting before the oath.
- **cities.db** `role` (body=Council): `jeffsilvestrini` = **615 votes**, `cherijackson` =
  799 — the mayor row carries real vote bounds. The `validate()` `non_voting_mayor` guard is
  correctly inert (only fires when the flag is True). MAYOR rows 18–21 carry
  first_vote/last_vote. ✓

### 4. Redistricting Ordinance 22-23 — CONFIRMED
- `minutes 2022-05-09` lines 396–397 + 415–419: *"Ordinance 22-23, Adjusting Council District
  Boundaries to Maintain Districts of Substantially Equal Population … Council Member Jackson
  moved to adopt … including map 5 as exhibit A. Council Member Uipi seconded … All Council
  Members voted yes. The motion passed unanimously."* — matches `adopted_by`, mover/second,
  and `map 5` exactly.
- `district_versions.csv`: `plan_2022` (high, real geometry) + `plan_2016` (low, **blank
  geometry_ref**, explicit "not published / not reconstructable from disk" note). The prior
  geometry is honestly recorded as an acquisition GAP, not fabricated. ✓

### 5. Precinct cross-check — CONFIRMED (incl. the RCV-divergence hiding)
Replicated read-only from `millcreek_results_by_precinct.csv` + `roster/precinct_to_district.csv`:
| Cycle | District | Plan | Result |
|---|---|---|---|
| 2023 | D3 | plan_2022 | **RECONCILES** (Jackson) |
| 2025 | D2 | plan_2022 | **RECONCILES** (DeSirant) |
| 2025 | D4 | plan_2022 | **RECONCILES** (Uipi) |
| 2016/2017/2019/2021 | D2/D3/D4 | plan_2016 | **GAP** (old composition not acquired) |

- The **2021 D2 RCV divergence is correctly hidden under the plan_2016 GAP.** The precinct
  first-choice winner is **JEREMIAH CLARK**, but the roster (final-round) winner is **Thom
  DeSirant** — if 2021 were graded on plan_2022 this would read as a false DISCREPANCY.
  Because 2021 falls under the plan_2016 GAP, it is reported as GAP, never as a discrepancy.
  Well designed.
- The roster-local `precinct_to_district.csv` was diffed against `geo/precinct_to_district.csv`:
  **51/51 precincts, 0 district mismatches** — a faithful copy plus a `source_year` column.
  D2/D3/D4 = `election-xcheck` (high), D1 = `gis-2022map` (medium; D1's only post-2022 race,
  2023, was cancelled-uncontested → no precinct-election corroboration). Confidences match
  `district_precincts.csv`.

### 6. Address→rep demo — CONFIRMED
- `geo/address_to_district.py` resolves **`3330 S 1300 E` → District 2 → Thom DeSirant**
  (executed read-only). On 2026-02-01 the roster returns DeSirant (D2, term from 2026-01-12)
  + Mayor Jackson; on 2021-06-01 `representatives_for_address` returns the plan_2016
  geographic **GAP** + Mayor Silvestrini (his 2020–2024 term). Honors `district_versions`. ✓

### 7. Structural invariants + election crosscheck — CONFIRMED
- **20 tenure rows / 5 stable seats / 1 VACANT** (D1×3, D2×4, D3×5 incl. VACANT, D4×4,
  MAYOR×4). Every row carries `sources` + `confidence`. **20 high / 0 medium / 0 low.**
- **No overlaps** on any seat_id; intervals are cleanly chained half-open per seat.
- **All 17 municipal-general winners map to a tenure** (2016×5, 2017×2, 2019×3, 2021×2,
  2023×3, 2025×2). The two appointments (Jackson MAYOR, Handy D3) correctly have blank
  election_year and are excluded from the winner-crosscheck by design.
- **Marchant → DeSirant (D2, Jan 2022)** transition present and dated to the 2022-01-10
  oath.
- **Named-roll-call seam** (2017–2021 tally-only): founders' `first_vote` = 2019-05-13 (Uipi
  2020-02-24), DeSirant 2022-07-26 — all match cities.db `role.first_seen` exactly, i.e. the
  seam is a recording limit, not a term start and not a gap. `dwightmarchant` = 14 votes
  (matches the "only 14 named votes" note).

---

## B. Calibration / honest-gap items (no fix required)

1. **`plan_2022` effective date is the adoption date, not the stated effective date.**
   `district_versions.csv` uses `effective_start = 2022-05-09` (ordinance adoption), but the
   `2022-05-09` minutes record staff saying the map *"would go into effect the following
   day"* (i.e. 2022-05-10). One-day nuance with **zero query impact** (the 2021 election used
   the old lines; 2023+ use the new lines; no query resolves against 2022-05-09/10). Optional:
   add a one-line note that adoption date is used as the switch.

2. **Intra-day handoff on 2025-11-10 (day-granularity convention).** Because intervals are
   half-open at day granularity, `roster_as_of('2025-11-10')` returns MAYOR=Jackson and
   D3=VACANT for the *whole* day — yet the `2025-11-10` work meeting held that morning (before
   the oath) has Silvestrini voting *as Mayor* and Jackson voting *as Council Member D3*
   (lines 165–167). This is the standard SCD convention (a mid-day swearing-in resolves to the
   successor); it is not an error, but the succession note could acknowledge the intra-day
   limit for anyone reconciling the 2025-11-10 roll call against the roster.

3. **Person-level vote bounds blend Jackson's D3 + Mayor spans** (all her rows read
   2019-05-13..2026-05-26). Already disclosed in the row note and CLAUDE.md — flagged here only
   for completeness.

4. **Correctly-recorded honest gaps:** `plan_2016` geometry + composition (unpublished; county
   kept MIL### numbering, so not reconstructable), D1 plan_2022 composition (`medium`, GIS-only),
   and the 2017–2021 named-vote seam. All recorded as low/blank/medium with notes — none filled.

---

## C. HARDENING recommendations (shared `roster_lib.py`, not Millcreek data)

**Verdict on the `source_year` question (posed by the builder):**
The **roster-local adapter copy is the CORRECT choice, not a workaround** — keep it.
`source_year` here is not a mechanical column: it encodes a real provenance/confidence
judgment (`election-xcheck` for the D2/D3/D4 compositions cross-validated by a post-2022
contested general vs `gis-2022map` for D1, whose only post-2022 race was cancelled). The
city `geo/precinct_to_district.csv` legitimately lacks it because it is a pure GIS
centroid product; materializing the column in a roster-scoped copy (geo/ untouched,
assignments verified identical) is the right separation. `roster_lib` should therefore
**not** silently default a missing `source_year` — doing so would erase the high/medium
distinction and *over-claim* confidence. Two hardening items remain:

1. **Fail-safe the required column (low).** `roster_lib.write_precincts` line 437 does
   `src = r["source_year"]`, a raw `KeyError` if a future city forgets the column. Change to
   `r.get("source_year")` with an explicit fallback → `confidence='medium'` + a
   `"source_year absent"` note, so an omission fails **safe (medium)** rather than crashing —
   and never silently upgrades to `high`.

2. **Dead per-precinct mismatch check (low, latent).** `roster_lib.precinct_crosscheck`
   line 627 gates the per-precinct exact-assignment mismatch detector on
   `r["year"] == rd.precinct_hi_source`. Millcreek sets `precinct_hi_source="election-xcheck"`
   (a source token, consumed at line 438), whereas `r["year"]` is a calendar year, so **this
   branch never fires** — the cross-check validates only the *aggregate* district winner, not
   individual precinct assignments. `precinct_hi_source` is overloaded (a *year* in the lib
   default `"2025"` at line 101; a *token* in Millcreek's driver). For Millcreek this yields
   no wrong output (assignments == geo/, aggregate winners reconcile), but the
   "cross-validated → high" label rests on a coarser check than the note implies. Recommend
   splitting into two config fields — a source-token for the confidence label and a separate
   key for the per-precinct crosscheck — so the finer validator actually runs fleet-wide.

Neither item changes any Millcreek value; both harden the shared library against a future
city.

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
