# South Jordan roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `roster/council_terms.csv`, `district_versions.csv`, `district_precincts.csv`,
`roster_overrides.csv`, `CLAUDE.md`, sidecars — verified against
`election_results/*_by_candidate.csv`, `meeting_minutes/minutes/**`, root `cities.db`
(`city='south_jordan'`), and the repo cardinal rules.
**Method:** READ-ONLY. No CSV/lib edits, no rebuild. Every finding below quotes its source.

## VERDICT: CLEAN — 0 confirmed defects.

30 tenures, 6 stable seats, 0 VACANT, 12 high / 18 medium / 0 low. All shared invariants
hold: no overlaps, no gaps, every row sourced + confidence-tagged, all 30 general winners
map 1:1, the non-voting-mayor invariant holds. The high-risk areas (the 18-row pre-floor
`medium` block and the 0-VACANT claim) were probed hardest and both survive.

---

## 1. The 18 pre-floor `medium` terms — HONEST (highest-risk area, ~60% of roster)

All 18 are correctly `medium` (none overstated `high`); the win is a SOVC fact and continuous
service is the INFERRED part. Vote bounds are empty where `cities.db` has no data; where present
they are the person's real later-era db bounds, explicitly flagged per row (the logged
vote-bound-clamp artifact — NOT fabrication). Spot-checks against
`south_jordan_results_by_candidate.csv`:

| Row | Roster claim | SOVC ground truth | ✓ |
|---|---|---|---|
| D1 Winger 2008–12 | 2007 D1 win 97.4% vs Write-in | `LEONA WINGER,1553,97.43,1,True` | ✓ |
| D2 Newton 2012–16 | 2011 D2 def. Johnson 51.9% | `CHUCK NEWTON,717,51.92`; `KATHIE JOHNSON,659,47.72` | ✓ |
| D3 Butters 2010–14 | 2009 D3 def. Ross 60.5%; lost 2013 to Shelton | `BRIAN C. BUTTERS,693,60.52`; `DON SHELTON,1218,66.92` (2013) | ✓ |
| D5 McGuire 2018–22 | 2017 D5 def. Kirkendoll 51.0% (+47) | `JASON T MCGUIRE,1163,51.03`; `SANDRA KAY KIRKENDOLL,1116` (Δ=47) | ✓ |
| MAYOR Alvord 2014–18 | 2013 def. incumbent Osborne 50.19% (Δ=100) | `DAVE ALVORD,5226,50.19`; `SCOTT L. OSBORNE,5126,49.23` (Δ=100) | ✓ |

(The remaining 13 medium rows were likewise cross-checked and all reconcile — Seethaler 2011
73.5%, Johnson 2007 50.7-49.1 & 2011 loss "Newton +58" = 717-659, Marlor 2015 66.8%, Harris
2015 66.2%, Shelton 2013 66.9% & 2017 61.5%, Zander 2015 60.9%, Taylor 2007 60.3%, Barnes 2011
57.6%, Short 2009 61.7% & 2013 loss, Rogers 2013 58.1%, Money 2009 54.6%, Ramsey 2017 55.7%.)

**Money→Osborne pre-floor succession — correctly FLAGGED, NOT fabricated.** There is exactly one
2009-cycle mayoral row (`W. Kent Money,2010-01-01,2014-01-01`); a `grep -i osborne council_terms.csv`
returns **no Osborne tenure**. Money's note reads: *"an intervening pre-floor Money->Osborne
mayoral succession (~2010-2013) is externally attested but its dates are entirely below the 2020
data floor and unreconstructable from loaded sources -> flagged, NOT modeled as a fabricated
Osborne tenure (repo cardinal rules)."* The internal evidence (2013 SOVC: Alvord *"def. incumbent
Osborne"*) is exactly what makes the gap visible, and the interval is left at the cycle boundary
rather than inventing an Osborne start date. This is the cardinal-rules-compliant choice. (See §B.)

---

## 2. Non-voting Mayor + the single tie-break — VERIFIED

`cities.db` `role`: `Dawn R. Ramsey | Council | first_seen=2025-06-17 | last_seen=2025-06-17 |
n_votes=1` — her **only** council-body vote. The motion (`meeting_date=2025-06-17`, motion_no 9,
Ordinance 2025-09) records her `vote_value=Aye`. Minutes
`2025/2025-06-16/2025-06-17_city-council-regular-meeting.md` (ll. 815–823), verbatim:

> Council Member Shelton - Yes / Council Member Johnson - Yes / Council Member Harris - No /
> Council Member McGuire - No / Council Member Zander - Absent / **Mayor Dawn R. Ramsey - Yes**
> … **The motion passed with a vote of 3-2.**

Members present split **2-2** (Shelton/Johnson Yes, Harris/McGuire No, Zander absent); Ramsey broke
it 3-2 on Ord. 2025-09 (drinking-water-protection-zone uses) — exactly as the roster states. **All
five MAYOR rows carry EMPTY `first_vote`/`last_vote`** (verified programmatically: Money, Alvord,
Ramsey×3 all `fv=[] lv=[]`), so `non_voting_mayor=True` + the `DB_KEY` exclusion prevent the lone
tie-break from smearing a span. PASS.

---

## 3. D2 Marlor → Johnson — CLEAN handoff, NOT a vacancy; Johnson is the returning 2008 member

- Marlor served the **full** 2020–2024 term: present + honored on 2023-12-05 (minutes
  `2023-12-05_city-council-regular-meeting.md` G.1: *"Proclamation in recognition of Bradley G.
  Marlor's Years of Service"*; a resident notes he *"did it for eight years"* = two full terms).
  His `cities.db` last NAMED vote 2023-03-07 is a dissent-only recording seam, not a departure.
- Johnson sworn 2024-01-02 (minutes `2024-01-02_city-council-regular-meeting.md` D.2: *"Oath of
  Office of City Council Member, Kathie L. Johnson"*); her tenure starts exactly where Marlor's ends
  (2024-01-02, **no overlap** — confirmed by the chain check).
- Same-person return: `kathie_johnson` holds D2 in **both** 2008–2012 (2007 win, lost to Newton
  2011) **and** 2024– (2023 win), with Newton (2012–16) + Marlor (2016–24) between — non-contiguous,
  so `start_event=elected` (not `reelected`). Correct.

Not a mid-term resignation → **no VACANT row**. PASS.

---

## 4. 0 VACANT — attempted to BREAK it, could not

Full-corpus sweep of `meeting_minutes/minutes/**` for
`resign|vacan|vacate|appoint…(fill|seat|council)|unexpired|step down|midterm` filtered to
council-seat context surfaced **zero** council-seat vacancies. Every hit is unrelated:
- Planning-Commission / board vacancies (e.g. 2022-01-04 study: *"Commissioner Sean Morrissey is
  stepping down"* — PC, not council);
- One-meeting **Mayor Pro Tempore** appointment, explicitly temporary (2022-10-18 study, l. 36:
  *"appoint Council Member Jason McGuire as Mayor **Pro Tempore for tonight's meetings** in the
  mayor's absence"*);
- committee/board seats (sewer district, treasurer procedures), and "vacant" **property/parcel**
  references.

The 7 distinct council voters in `cities.db` (Marlor, Ramsey[tie-break], Shelton, McGuire, Johnson,
Harris, Zander) all map to roster tenures with no unknown voter. Every seat transitions only at a
cycle boundary. **0 VACANT is honest.** PASS.

---

## 5. Redistricting — Ordinance 2022-13 VERIFIED

Minutes `2022/2022-06-06/2022-06-07_city-council-regular-meeting.md` (meeting_date 2022-06-07):
- Item H.1 *"Ordinance 2022-13, Amending Section 1.12.030: District Boundaries … set forth in the
  City Council District Boundary Map based on the 2020 census"*;
- l. 262: boundaries *"reflective … drawn based on the current census information … the 2020
  [decennial] census"*;
- ll. 324–326: *"Council Member Marlor motioned to approve Ordinance 2022-13 … Council Member Harris
  seconded … **Roll Call vote was 5-0, unanimous in favor.**"*

`district_versions.csv`: `plan_2022` (5 districts, `geometry_ref=geo/council_districts.geojson`,
`effective_start=2022-06-07`, open, **high**) + `plan_pre2022` (5 rows, **blank** `geometry_ref`,
`confidence=low`, note *"not reconstructable from data on disk. Acquisition gap, not a guess"*) +
a `citywide` MAYOR row. `district_precincts.csv`: 68 `plan_2022` rows (D1=14, D2=15, D3=12, D4=16,
D5=11 — verified) + 5 `plan_pre2022` gap rows. The gap is explicit, not fabricated. PASS.

---

## 6. Structural invariants + crosschecks — ALL PASS

- **No overlaps / no gaps:** per-seat chain check ran clean for all 6 seats (each `end_date` ==
  next `start_date`; earliest B-cycle 2008-01-01, A-cycle 2010-01-01). 0 overlaps.
- **Every row sourced + confidence-tagged:** 0 rows missing `sources` or `confidence`.
- **All 30 general winners map 1:1** to a tenure `election_year` (5 per seat × 6 seats = 30;
  10 cycles × 3 races = 30). 0 drift.
- **Sparse vote bounds are a recording limit, not a gap:** SJ names only dissenters, and Jan–Jul
  2020 lives in `pmn_backfill/` (`provenance='pmn_minutes'`; the 2020-01-07 anchor meeting is
  present on disk). First NAMED votes (Harris 2021-09-21, McGuire 2021-05-18) land mid-term — noted
  per row, consistent with `cities.db` `role` bounds (Zander/Shelton/Marlor first_seen 2020-09-15).
- **D5 name-format artifact benign:** ballot `JASON TIMOTHY MCGUIRE` (2025, 1,335) vs roster/vote
  `Jason McGuire` — a display mismatch (same pattern as SLC), correctly excluded from the automated
  string-match and hand-verified. Not a data discrepancy.

Sidecars (`_precinct_to_district.csv`, `_precinct_votes.csv`) and `roster_overrides.csv` (0 data
rows) are as documented.

---

## Findings summary

### (A) CONFIRMED DEFECTS — **none.**

### (B) Calibration / honest-gap items (correctly handled, no action required)
1. **Money 2010–2014 mayoral interval mildly overstates actual service.** Osborne (per the 2013
   SOVC) was the incumbent Money defeated-successor by 2013, so Money left before term-end; the row
   keeps `end_date=2014-01-01` (cycle boundary) because Osborne's real start is below the floor and
   unreconstructable. Flagged in the note; fabricating a date would violate the cardinal rules. This
   is the correct honest choice — the one place a reader should not read the interval as literal
   continuous service, and the note says so.
2. **Person-level vote-bound smear onto pre-floor / non-contiguous tenures** (e.g. Harris 2016 row
   `first_vote=2021-09-21`; Johnson 2008 row `first_vote=2024-01-16`). Real db bounds attached to an
   earlier term; authoritative interval is always `start_date`/`end_date`. Explicitly noted per row
   — the already-logged vote-bound-clamp item, not a new defect.
3. **2020-01-07 seating anchor** for the 2019-cycle B-seats is the first documented 2020 meeting
   (in `pmn_backfill/`, tally-only), corroborated by 2020-08+ audited minutes + the named-vote
   record — a defensible `high`. Honest seam, documented.

### (C) HARDENING recommendations
The precinct-crosscheck cluster, at-large hook, and vote-bound clamp are already logged; nothing
NEW rises to a required change. Two optional, cosmetic hardening notes only:
1. **MAYOR `district_versions` row** sets `source_url` to Ordinance 2022-13 and `geometry_ref` to
   the 5-district layer. The redistricting ordinance does not govern the mayor's citywide extent
   (the note clarifies this), but a future auditor grepping `source_url` could misread it as
   implying the mayor was redistricted. Optional: blank/repoint that one URL. Very low priority.
2. **Folder-vs-meeting-date seam (documentation only, NOT a roster issue):** minutes folders are
   named by the Monday week-bucket (e.g. `2025-06-16/`) while the file and `cities.db`
   `meeting_date` carry the true Tuesday meeting date (`2025-06-17`). The roster correctly uses the
   db/meeting date. A future auditor grepping folder names for an event date will be off by one —
   worth a one-line heads-up in a QC note. No roster change needed.

**Bottom line: the South Jordan roster is faithful to the sources. The 18-row pre-floor `medium`
block is honestly election-anchored with no fabricated tenures or bounds, and the 0-VACANT claim
holds against a full minutes sweep. Ship as-is.**

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
