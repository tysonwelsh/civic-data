# Taylorsville roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `taylorsville_city_council/roster/` (`council_terms.csv`, `district_versions.csv`,
`district_precincts.csv`, `roster_overrides.csv`) against source minutes, election results,
and root `cities.db`.
**Method:** READ-ONLY. Quoted every load-bearing claim back to source. Did NOT rebuild
(build_roster.py regenerates the CSVs — left untouched). Structural invariants checked with a
read-only pass over `council_terms.csv`.

## VERDICT: CLEAN — no confirmed defects.

35 tenures (15 high / 19 medium / **1 low**), 2 VACANT, 0 overlaps, 0 chain gaps, every row
sourced+confidence'd, one person_key per person (both crossovers clean). Every general
election winner (32 generals, 2007–2025) maps to a tenure. The distinctive surface — the
non-voting executive mayor, the in-window D3 vacancy chain, the below-floor D2 `low` VACANT,
the two crossovers, the 2022 redistricting — is faithfully and honestly modeled. Details below.

---

## (A) CONFIRMED DEFECTS
**None.** No fabricated names, no overstated confidence, no overlap/gap, no OCR-corrupted name.

---

## (B) Calibration / honest-gap items (accept-as-is; documented, not fixes)

### B1 — The `low` D2 [2018-01-01, 2020-01-08) VACANT is the CORRECT honest move (highest-scrutiny item — VERIFIED)
This is the fleet's first `low` row. It is right.

- **Overson genuinely vacated D2 to become Mayor.** She won D2 in 2011 (`KRISTIE S OVERSON`
  738, 59.9%) and 2015 (`KRISTIE STEADMAN OVERSON` 1009, 76.5%) — a 2016–2020 term — then won
  the 2017 Mayor race (`KRISTIE STEADMAN OVERSON` 5444, 57.2%, def. incumbent Mayor Larry
  Johnson) and was sworn Mayor ~Jan 2018, ~2 years early. All in `taylorsville_results_by_candidate.csv`.
- **The interim holder is genuinely undocumented.** The minutes floor is 2020-01-06 (first dir
  on disk); 2018–2019 minutes are not in the repo. No loaded source names the 2018–2020 D2
  seat-holder. The 2019 general elected **Cochran** (`CURT COCHRAN` 954, 60.6%) — the REGULAR
  B-cycle D2 election whose new term begins 2020-01-08, exactly where this window closes. So the
  ~2-week unexpired balance never needed a special; the appointee simply served to Jan 2020.
- **No name was fabricated.** `person_name=VACANT`, `confidence=low`, and the note explicitly
  says the seat was NOT literally empty ("honest gap, not a literally-empty seat … the appointee
  is not named in the loaded sources"). The distinction between "holder unknown" (this row) and
  "documented-empty" (the D3 VACANT, `high`) is carried by the confidence column, exactly as the
  fleet convention intends.

**Is `low` VACANT the right representation, or should it be a `low` UNKNOWN-holder row?** VACANT
is correct given the constraints. There is no `UNKNOWN` sentinel in the fleet schema, and the
note removes the only ambiguity VACANT could introduce (it states a holder existed). Minting a
new sentinel for one below-floor row would be a schema divergence with no analytic payoff. The
representation is honest and self-describing. **Accept as-is.**

### B2 — D3 `end_event='resigned'`: the documented mechanism is a MOVE-OUT, not a resignation letter
`council_terms.csv` row 17 (Christopherson, D3 2020-01-08→2020-08-20) sets `end_event=resigned`.
The vacancy itself is airtight, but the *documented* trigger is relocation, not a filed
resignation:

> "In closing, the Mayor expressed her very best wishes to Vice Chair Christopherson as he and
> his family **began their new adventure outside Taylorsville**." — 2020-08-19 minutes

That is a residency-loss vacancy (a councilmember must reside in-district). The word "resign"
appears nowhere for Christopherson in the loaded 2020 minutes (the only "resignation" hit is
2020-09-02 line 161, an unrelated *committee-chair* resignation by a different person). The
downstream facts the roster relies on are all confirmed:
- last day served / last vote **2020-08-19** (`cities.db` Council bound 2020-01-08..2020-08-19 ✓);
- 2020-09-02 minutes ×2: "The District No. 3 council seat was temporarily vacant" ✓;
- Ordinance 20-17 fills "the District No. 3 **vacancy**" on 2020-09-30 ✓.

**Assessment:** calibration only, NOT a defect — the interval, dates, and VACANT chain are all
correct. `end_event=resigned` is a defensible shorthand for "vacated the seat"; `vacated` /
`moved-out` would be marginally more source-faithful. No change required; logged for the
fleet's `end_event` vocabulary review.

### B3 — Pre-floor `medium` terms: spot-checked, none overstated
Sampled 5 of the 19; each is win=fact / service=inferred, honestly flagged, no fabricated
citation, correctly `medium` (not `high`):
- **Catlin D1 2008–2012** — 2007 D1 winner (955, 65.1% def. Gidney) ✓; note "Not a 2011 D1
  candidate → Burgess won" matches the data (2011 D1 = Burgess vs Grossman) ✓.
- **Pratt D2 2008–2012** — 2007 D2 winner (97.7%) ✓; "LOST to Overson 2011" matches ✓.
- **Rechtenbach D3 2012–2014, `ran-for-mayor-lost`** — 2011 D3 winner ✓; ran Mayor 2013 and lost
  (2013 Mayor = Johnson def. Rechtenbach 53.5%) ✓. The existence of a **2013 D3 special**
  (Christopherson 98.98% in an A-cycle year) independently corroborates that Rechtenbach vacated
  D3 — the election data itself proves the seat came open off-cycle. ✓
- **Barbour D4 2010–2014** — 2009 D4 winner (66.4%) ✓.
- **L. Johnson D5 2010–2014, `became-mayor`** — 2009 D5 winner (57.7%) ✓; won Mayor 2013 ✓.

The `first_vote`/`last_vote` "smear" (pre-floor rows inheriting a person's later documented-era
db bounds, e.g. Burgess's 2012 D1 row showing `first_vote=2020-01-08`) is per-row disclosed and
the authoritative interval is always `start_date`/`end_date`. Correct handling.

---

## Positive confirmations (each quoted to source)

**1. Non-voting executive mayor — CONFIRMED.**
- `cities.db`: the Council body's distinct voters are exactly the 7 district members (Barbieri,
  Knudsen, Christopherson, Cochran, Armstrong, Burgess, Harker). **Overson and Larry Johnson are
  absent from the `person` table entirely.**
- 2020-06-17 Ordinance 20-14 deny motion, contested 4-1 — the roll names exactly 5
  councilmembers, mayor absent: "Councilmember Armstrong Yes / Councilmember Burgess Yes / Chair
  Harker No / Vice Chair Christopherson Yes / Councilmember Cochran Yes … The motion passed 4-1".
- 2020-09-30 appointment vote passed **4-0** with only 4 members voting (D3 vacant, mayor
  non-voting) — 5 seats − 1 vacancy = 4, mayor never counted. Internally consistent.
- All 6 MAYOR-body rows carry empty `first_vote`/`last_vote`. ✓

**2. D3 resignation→appointment chain — CONFIRMED (quotes exact).**
- "Councilmember Armstrong moved to approve Ordinance 20-17, appointing Anna Barbieri to
  represent District No. 3 on the City Council; and to swear her in on October 7, 2020" (2020-09-30) ✓
- "Ms. Barbieri had become a member of the city council immediately upon approval of Ordinance
  20-17" (2020-09-30) ✓
- VACANT D3 [2020-08-20, 2020-09-30) is `high` and begins the day AFTER Christopherson's last
  served day (2020-08-19) ✓. `roster_as_of('2020-08-19')` resolves to Christopherson (his
  interval end is 2020-08-20, half-open) ✓. First named Barbieri Council vote 2020-10-07 (db) ✓.

**3. Two crossovers — CONFIRMED.**
- Larry Johnson: D5 [2010-01-01,2014-01-01) → MAYOR [2014-01-01,2018-01-01) — adjacent, no
  overlap; also the 2021 D5 loser; one `larry_johnson` key. Council rows blank (pre-floor, no
  in-window votes; absent from db). ✓
- Kristie Overson: D2 [2012],[2016-01-01,2018-01-01) → MAYOR [2018-01-01,…) — no overlap; one
  `kristie_overson` key spanning both bodies; MAYOR rows empty. ✓

**4. Redistricting Resolution 22-11 — CONFIRMED (quotes exact).**
- "Councilmember Harker moved to approve Resolution 22-11 as presented. The motion was seconded
  by Councilmember Burgess." → "Councilmember Cochran No / Chair Barbieri Yes / Councilmember
  Harker Yes / Councilmember Burgess Yes / Councilmember Knudsen Yes — The motion passed 4-1"
  (2022-05-04). Motion Harker / second Burgess / Cochran No / 4-1 all match `district_versions.csv`. ✓
- "60,448 residents" quote matches ✓. `plan_2022` (2022-05-04, high) + `plan_pre2022` (GAP,
  blank geometry, low) modeling is correct; 44 plan_2022 precinct rows + 5 plan_pre2022 GAP rows. ✓
- "Chair Barbieri" presiding independently re-confirms "Chair = one of the five members."

**5. Structural invariants — ALL PASS.**
0 overlapping tenures per seat; every `end_date` chains exactly to the next same-seat
`start_date` (0 gaps); every row has non-empty `sources` and `confidence`; no person_name maps
to >1 key and no key maps to >1 name; counts 15 high / 19 medium / 1 low match the CLAUDE.md
ledger.

**6. OCR seam did not corrupt any name.**
The 2026-01-07 seating is post mid-2025 RICOH-OCR seam. Names render clean: "Administration of
Oath of Office to Mayor Overson and Council Members Harker [and Knudsen]" and "Knudsen had been
elected to serve as Chair while Council Member Cochran was elected as Vice[-Chair]" — Overson /
Harker / Knudsen / Cochran / Barbieri / Burgess all spelled correctly. The 2024-01-03 quote is
likewise exact: "Council members Barbieri, Burgess, and Cochran had all been reelected in the
November 2023 general election. The oath of office was administered to all three."

---

## (C) HARDENING recommendations
**None actionable at the row level.** Two items for the fleet backlog (already-logged classes;
no per-city change here):
- The `end_event` vocabulary could distinguish `vacated-moved-out` from `resigned` (B2) — a
  cosmetic labeling nicety, not a data issue.
- The `low` VACANT convention (B1) works but leans entirely on the note to signal "holder
  unknown ≠ empty seat." If more `low` holder-unknown rows accrue across the fleet, a dedicated
  `person_name` sentinel (e.g. `UNKNOWN-HOLDER`) vs `VACANT` would make the distinction
  machine-legible without reading the note. Log as a fleet-schema consideration, not a fix.

The roster is accurate, honest about its gaps, and faithful to every source I checked.

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
