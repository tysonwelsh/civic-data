# SLC council-roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `roster/council_terms.csv` (52 tenures), `district_versions.csv` (15 rows),
`district_precincts.csv` (151 rows), against `election_results/`, `meeting_minutes/minutes/**`,
root `cities.db`, and `geo/`.
**Method:** READ-ONLY. Ran `build_roster.py --check`/`--demo` (idempotent — verified the
regenerated `council_terms.csv` was **byte-identical** to the pre-run copy, no mutation). Every
election winner, appointment, resignation, vacancy window, redistricting event, precinct
reconciliation, and vote-bound cross-checked at source with quotes below.

## Verdict

**The roster is remarkably clean. No fabrication, no overstated tenure, no mis-dated vacancy, no
overlap.** All 6 appointment/vacancy chains are documented at source; all election anchors match
the county file exactly; the two known source defects (2019 broken SOVC, 2021 D2 RCV mislabel) are
handled honestly; the redistricting is verbatim-verified; all 6 plan_2022 precinct checks
reconcile. Confidence is calibrated conservatively.

**One genuine data-field defect** exists (Petro `last_vote`), and it is the roster's own
**self-disclosed** builder library issue #1. **Both builder-flagged `roster_lib.py` issues are
REAL.** Everything else is honest-gap or minor-calibration.

---

## (A) CONFIRMED DEFECTS to fix

### A1 — DEFECT · Petro `last_vote` is wrong (2022-11-10; true value 2026-06-09)
**Rows:** both `D1 Victoria Petro` rows (`2021-11-16` and `2026-01-13`) carry
`first_vote=2021-11-16, last_vote=2022-11-10`.
**Evidence — `cities.db role` (body=Council), the SAME person under two name_keys:**
```
victoriapetroeschler   Council   first_seen 2021-11-16   last_seen 2022-11-10
victoriapetro          Council   first_seen 2022-05-03   last_seen 2026-06-09
```
The true person-level union is **first_vote=2021-11-16, last_vote=2026-06-09**. The CSV's
`last_vote=2022-11-10` reflects only the `petroeschler` name_key's bound — it understates her vote
span by ~3.5 years and reads as if she stopped voting in Nov 2022 (she voted continuously through
2026-06-09). `first_vote` is coincidentally correct (the earlier of the two).
**This is honestly flagged** in the row note ("union is 2021-11-16..2026-06-09"), so it is not
deceptive — but the *field value* is still wrong.
**Severity:** DEFECT (informational field only — does NOT touch tenure boundaries or confidence;
tenure dates are correct). **Fix:** library-level (see C1). No override needed once the lib is
patched; if a stopgap is wanted, a `roster_overrides.csv` row could set `last_vote=2026-06-09`.

*(No other defects found. The remaining items are calibration/honest-gap or nits.)*

---

## (B) Calibration / honest-gap items (verified correct or defensibly conservative)

### B1 — Confirmed HONEST: the 6 vacancy/appointment chains (all quoted at source)
| Chain | Departure (quote) | Successor (quote) | VACANT window | conf |
|---|---|---|---|---|
| **D5 Mendenhall→Mano** | `2020-01-07` present as *"Erin Mendenhall, Mayor"*; only 6 CMs on the D-roll, D5 empty | `2020-01-21` *"adopt Resolution 1 of 2020 appointing Darin Masao Mano as a new member … to fill the unexpired term of the vacated office representing District Five, which motion carried, all members voted aye."* | 2020-01-07→2020-01-21 | **high** ✓ (both endpoints documented) |
| **D2 Johnston→Faris** | last vote `2021-04-20` (`cities.db`) | `2021-05-18` present list: *"Amy Fowler, Ana Valdemoros, Chris Wharton, Daniel Dugan, Darin Mano, James Rogers, Dennis Faris"* (7) | 2021-04-20→2021-05-18 | medium ✓ |
| **D1 Rogers→Petro** | Rogers presided `2021-09-21` (last vote, `cities.db`) | `2021-11-09` WS: *"The Council will interview applicants for the vacant Council District One seat … unanimous selection to appoint Victoria Petro-Eschler"*; present as CM `2021-11-16` | 2021-09-21→2021-11-16 | medium ✓ |
| **D7 Fowler→Young** | Fowler present `2023-06-13` (last vote) | `2023-07-13` WS: *"Sarah Young was appointed as the new District 7 Council Member."* | 2023-06-13→2023-07-18 | medium ✓ |
| **D4 Kitchen→Valdemoros** | Kitchen→Utah Senate ~Jan 2019 (below 2020 minutes floor) | Valdemoros present as D4 `2020-01-07` (*"Analia Valdemoros"*) | 2019-01-01→2020-01-07 | medium ✓ (approx) |
| **D4 LopezChavez→Napier-Pearce** | last vote `2026-05-05`; `2026-05-14` WS *"an update regarding the District 4 Council vacancy process, including the timeline…"* | `2026-06-09` present: *"…Jennifer Napier-Pearce, Erika Carlsen…"* + *"all CM's plus jennifer napier pearce"* | 2026-05-05→2026-06-09 | medium ✓ |

**Vacate-confidence invariant HOLDS:** the 5 gap-bounded departures are all `medium`; only the
fully-documented D5/Mano window is `high`. The gap-detector caught them — **no gap-bounded date is
mis-marked `high`.**

### B2 — Confirmed HONEST: known source defects
- **2019 broken SOVC** — election file yields only `Vote By Mail`/`Vote Centers` rows (candidate
  names lost). Winners (Johnston/Valdemoros/Dugan/Mendenhall) are anchored to the 2020-01-07
  present list + 2021 votes, flagged `medium` (Mayor `high` — see B4). `--check` prints the
  4 expected `unmapped winner 2019 … VOTE BY MAIL` warnings. **Not fabricated around.** ✓
- **2021 D2 RCV mislabel** — county file marks first-choice leader `BILLY PALMER (363)` winner;
  roster seats **Puy** (361 first-choice, won on later rounds). **Ground-truth: Puy was actually
  seated** — present list `2022-01-04`+ and `cities.db` `alejandropuy` Council `first_seen
  2022-01-04`. `--check` prints the expected `unmapped winner 2021 Council 2 BILLY PALMER`. ✓
- **Mano stray 2026-03-24 vote** — VERIFIED it is an extraction artifact: on `2026-03-24` the
  Council roll already carries a full 7 (Puy, Wharton, Dugan, **Carlsen**, Lopez Chavez, Young,
  Petro) and Mano is an **8th** voter — after his successor Carlsen was seated 2026-01-13. Mano's
  tenure correctly **ends 2026-01-13**; no post-seating tenure created. (His `last_vote` field
  retains the raw db bound 2026-03-24, honestly noted.) ✓
- **Petro name change** — one person, two `cities.db` name_keys (`victoriapetroeschler` +
  `victoriapetro`), both → `person_key=victoria_petro`. Confirmed in `role`. (Field consequence =
  defect A1.) ✓

### B3 — Confirmed HONEST: redistricting (Resolution 9 of 2022)
- `2022-05-10` limited formal: *"adopt Resolution 9 of 2022 Redistricting City Council District
  Boundaries, based on the 2020 Census results as shown on the attached map marked Exhibit A."*
- `2022-05-17` revised formal: *"…reconsider… correct the boundaries of Districts Three and Six to
  move a single property inadvertently placed in District Six into District Three."* (matches the
  roster's D6→D3 note exactly). `district_versions` `source_url` = attachment/20796 (Exhibit A
  Reconsideration Map for May 17) — that URL is present in the 2022-05-17 minutes. ✓
- `plan_2022` D1–D7 (`high`, real geometry) + `plan_2012` D1–D7 (`low`, blank `geometry_ref`,
  explicit acquisition GAP — county precincts renumbered, not reconstructable). **Not fabricated.** ✓

### B4 — Calibration NIT: 2019-anchored Mayor `high` vs council `medium`
Four rows share the broken-2019-SOVC anchor and 2020-01-07 documentation:
`Johnston/Valdemoros/Dugan = medium`, but `Mendenhall (Mayor) = high`. Defensible (the Mayor's
continuous presiding is documented in nearly every meeting, a stronger trail than a single roll
line), but Dugan's identical continuous 2021+ vote record arguably gives equal support. Mild
inconsistency, **not a defect** — err-conservative either way.

### B5 — Precinct cross-check: all 6 plan_2022 reconcile; pre-2022 honest gaps
`--check` output confirmed: **2023 D4** (Lopez Chavez 1900) · **2023 D7** (Young 4139) · **2025 D1**
(Petro 1594) · **2025 D3** (Wharton 3040) · **2025 D5** (Carlsen 4042) · **2025 D7** (Young 3650) —
precinct-sum winner == roster winner in every case. Pre-2022 rows all print `GAP (plan_2012 old
precinct numbering)`. **D2/D6 hand-verification confirmed** (excluded from the automated string
match only for name-format reasons):
- 2023 D2 precinct-sum: `ALEJANDRO "ALE" PUY = 2138` (unopposed 100%) = seated Alejandro Puy. ✓
- 2023 D6 precinct-sum: `DAN DUGAN = 3967` (leader; Semnani 3041, Alfandre 1707) = seated Daniel
  Dugan. ✓

### B6 — Address→rep demo works and honors versioning
`451 S State St` → District 4 via precinct `SLC054` → `2026-07-01`: **Jennifer Napier-Pearce (D4) +
Erin Mendenhall (MAYOR)** ✓ ; `2025-06-01`: Eva Lopez Chavez (D4) + Mendenhall ✓ ; `2021-06-01`
(pre-redistrict): **honest GAP** — *"plan_2012 boundaries not acquired — cannot resolve … without
fabricating."* ✓

### B7 — Mayor is NOT a council voter (verified)
Erin Mendenhall does **not** appear anywhere in `cities.db role` for `body='Council'`; Mano's
appointment resolution passed with all members voting aye but Mendenhall is absent. Council rolls
are 7-member (e.g., 2021-05-18, 2021-11-16, 2023-06-13, 2026-06-09 present lists each list 7). Mayor
rows carry blank `first_vote`/`last_vote`. ✓

### B8 — Election anchors: 100% match
Every general winner 2007–2025 in `council_terms` matches `slc_results_by_candidate.csv` (spot-checks
incl. 2009 D7 Simonsen 50.03% 13-vote margin, 2013 D3 Penfold 76.69%, 2015 D4 Kitchen 51.77%, 2017
D1 Rogers 100%). Forward cross-check reports only the 5 EXPECTED unmapped-winner warnings (4×2019
VOTE BY MAIL + 2021 D2 PALMER). LUKE/GARROTT disambiguation correct. ✓

### B9 — Structural invariants (programmatic)
52 rows · **18 high / 34 medium / 0 low** · 6 VACANT · **0 overlaps · 0 chain-gaps** (every seat
chains contiguously, VACANTs filling departures) · every row has non-empty `sources`+`confidence` ·
no pre-2020 tenure marked `high` · all 8 current serving rows `high` · shared surnames distinct
(person_keys unique). ✓

### B10 — Minor nits
- **Quote paraphrase.** The Mano row `sources`/CLAUDE.md render *"All Council Members were in
  favor,"* but the minutes read *"which motion carried, all members voted aye."* Faithful, but not
  verbatim — prefer the exact string.
- **Faris `high` on a present-list, not an appointment resolution.** No Faris appointment-resolution
  quote (unlike Mano's Res. 1 of 2020); `high` rests on documented present + continuous 2021-05-18+
  votes. Defensible, slightly generous.
- **Young VACANT window (2023-06-13→2023-07-18)** uses her first-vote 2023-07-18 as the seating
  date though she was appointed 2023-07-13 — overstates the vacancy by 5 days. Conservative.
- **Mayor term-start convention.** Mayor 2024 term starts `2024-01-01` while council uses the
  first-meeting `2024-01-09`. Harmless (Mayor doesn't vote), but inconsistent.

---

## (C) HARDENING recommendations for `scripts/roster_lib.py` + the maintenance skill

### C1 — `load_vote_bounds` must UNION across name_keys sharing a person_key — **REAL, confirm fix**
Builder-flagged issue #1 is **confirmed real** and is the direct cause of defect A1. The library
does `bounds[pk] = (fs, ls)` per db name_key, so when a name-change person (Petro-Eschler → Petro)
carries two name_keys mapping to one `person_key`, the last write **overwrites** instead of taking
the union. **Fix:** aggregate `first_vote = min(first_seen)`, `last_vote = max(last_seen)` over all
name_keys that resolve to the same `person_key`, e.g. keep a running min/max instead of assignment.
This is the only change that corrects A1 at the source. Impact today: Petro only, but any future
name change (marriage, legal change) re-triggers it.

### C2 — `precinct_hi_source` should accept a SET/TUPLE of years — **REAL, cosmetic**
Builder-flagged issue #2 is **confirmed real**: SLC's current precinct map is validly sourced from
**two** equally-authoritative post-redistrict generals (2023 even + 2025 odd + the 2023 D7 special),
but the lib can mark only one `source_year` `high`. Measured effect: **62 rows `high` (2025) / 82
rows `medium` (2023)** — 57% of plan_2022 rows read `medium` despite equal authority (incl. odd-D7,
tagged from its 2023 special). Purely a confidence-label artifact (each row's `note` says so); no
data-quality difference. **Fix:** let `precinct_hi_source` be a set of years, mark a row `high` if
its `source_year ∈ the set`.

### C3 — Maintenance-skill checks to add
1. **Name-change detector:** when >1 `cities.db` name_key maps to one `person_key`, assert the
   emitted `first_vote`/`last_vote` equals the union — would have caught A1 automatically.
2. **8th-voter / roll-size sentinel:** flag any council meeting whose vote roll exceeds the seated
   count (would have surfaced the Mano 2026-03-24 artifact as a db issue to log, not silently rely
   on a hand-note).
3. Keep the current `--check` invariants (overlap, sources/confidence, vacate-confidence, gap
   detector) — all passed here and all earned their keep.

---

## Bottom line
No blockers. One self-disclosed data-field defect (A1, Petro `last_vote`), fixable only in
`roster_lib.py` (C1). Both builder-flagged library issues are real (C1 substantive, C2 cosmetic).
Everything else — 6 vacancy chains, both source defects, redistricting, precinct reconciliations,
Mayor-absence, Mano stray, election anchors, structural invariants — ground-truthed and **honest**.

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
