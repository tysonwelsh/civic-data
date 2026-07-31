# Orem roster — adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did not build this roster)
**Scope:** `roster/council_terms.csv` (18 rows), `district_versions.csv`, `roster_overrides.csv`,
`CLAUDE.md`, checked against `election_results/*_by_candidate.csv`,
`meeting_minutes/minutes/**`, and root `cities.db` (`city='orem'`).
**Method:** tried hardest to break the 0-VACANT claim, the voting-mayor claim, the
pre-floor `medium` calibration, the two-Davids split, confidence calibration, and the
structural invariants. READ-ONLY (only this file written; no CSV/lib edits, no rebuild).

## Verdict: CLEAN — 0 confirmed defects

Every checkable claim held against the sources. Details below.

---

## (A) CONFIRMED DEFECTS

**None.** Nothing in `council_terms.csv` is contradicted by the election files, the
minutes, or `cities.db`. No fix required.

---

## 1. The "0 VACANT" claim — tried hardest to break it. HOLDS.

`cities.db` shows exactly **14 distinct persons** with Orem Council-body votes, and every
one's first/last observed vote lands on a **clean January term boundary**:

| person | first_vote | last_vote | roster row(s) |
|---|---|---|---|
| Brent Sumner | 2020-01-14 | 2021-12-14 | AL-B1 (term ends Jan-2022) |
| Richard Brunst (Mayor) | 2020-01-14 | 2021-12-14 | MAYOR |
| Debby Lauret | 2020-01-14 | 2023-12-29 | AL-A3 |
| Terry Peterson | 2020-01-14 | 2023-12-29 | AL-A2 |
| David Spencer | 2020-01-14 | 2025-12-09 | AL-B2 ×2 |
| Tom Macdonald | 2020-01-14 | 2025-12-09 | AL-B3 ×2 |
| Jeff Lambson | 2020-01-14 | 2026-05-05 | AL-A1 ×2 (continuing) |
| David Young (Mayor) | 2022-01-04 | 2025-12-09 | MAYOR |
| LaNae Millett | 2022-01-04 | 2026-05-05 | AL-B1 ×2 (continuing) |
| Chris Killpack | 2024-01-09 | 2026-05-05 | AL-A3 |
| Jenn Gale | 2024-01-09 | 2026-05-05 | AL-A2 |
| Crystal Muhlestein | 2026-01-13 | 2026-05-05 | AL-B3 |
| Karen McCandless (Mayor) | 2026-01-13 | 2026-05-05 | MAYOR |
| Quinn Mecham | 2026-01-13 | 2026-05-05 | AL-B2 |

Every **start** is a January seating (2020-01-14 / 2022-01-04 / 2024-01-09 / 2026-01-13 —
all four exist as Council meetings in `cities.db`) and every **end** is the last meeting
before a January turnover (2021-12-14 / 2023-12-29 / 2025-12-09). **No person appears or
disappears off-boundary** → no mid-term appointee, no mid-term departure.

Minutes corroboration — full scan of `minutes/**` for `resign|vacan|appoint…council|sworn|
oath|fill the seat`: **every hit is a STAFF or board/commission item, not a councilmember**:
- *"resignation of Heather Schriever"* (a board member), *"resigning his position as a City
  Manager effective January 1, 2023"*, *"Jerry's resignation"* (2025-01-13, the City
  Manager), *"22 employees resigned"* (HR report), 2026-02-23 *"the commission had recently
  suffered three resignations"* (**Planning Commission**, not Council).
- The only council-scoped "appoint" lines are **Mayor Pro Tem designations** (*"appoint
  Member Jeff Lambson as Mayor Pro Tem"* 2022-12; *"appoint Council Member LaNae Millett as
  Mayor Pro Tem"* 2022-06) — a presiding role, **not a seat change**. The roster correctly
  does **not** treat these as tenures. No defect.

**0 VACANT is an honest structural fact, confirmed.**

## 2. Voting mayor — VERIFIED (`non_voting_mayor=False` correct).

`build_roster.py:258` sets `non_voting_mayor=False` with the comment "OREM'S MAYOR IS A FULL
VOTING MEMBER." Confirmed at source — the mayor is named **inside** the roll-call vote lists:

- **Brunst**, 2020-01-14: *"Those voting aye: **Richard F. Brunst**, Jeff Lambson, Debby
  Lauret, Tom Macdonald, Terry Peterson, David Spencer, and Brent Sumner."* Present-list
  header: *"CONDUCTING Mayor Richard F. Brunst … ELECTED OFFICIALS Jeff Lambson, Debby
  Lauret, Tom Macdonald, Terry Peterson, David Spencer, and Brent Sumner"* (Mayor + 6 = 7).
- **Young**, 2022-10-11: *"Those voting aye: **David A. Young**, David Spencer, Debby Lauret,
  Tom Macdonald, Jeff Lambson…"* Conducting 2022-01-11: *"CONDUCTING Mayor David A. Young."*
- **McCandless**, 2026-01-27: *"Those voting yes: **Karen McCandless**, Chris Killpack,
  Crystal Muhlestein, Jeff Lambson, Jenn Gale, LaNae Millett…"* Conducting 2026-01-13:
  *"CONDUCTING Mayor Karen McCandless."* (Note: 2026 minutes say "voting yes" not "aye" —
  same roll-call semantics.)

All three MAYOR rows carry real vote bounds matching `cities.db` exactly (Brunst
2020-01-14…2021-12-14, Young 2022-01-04…2025-12-09, McCandless 2026-01-13…2026-05-05).

**Mayoral chain Brunst → Young → McCandless** confirmed with transition dates and the
**2026 mayor is KAREN McCandless** (not David): election SOVC row *"2025 municipal general
Mayor KAREN MCCANDLESS 9574 51.39 rank1 Y"* over *"DAVE YOUNG 9056"*; roster note documents
this corrected a brief "David" error. Young 2021 (9,647 / 59.06% over Jim Evans) verified.

## 3. Pre-floor `medium` terms — correctly flagged, NOT fabricated.

Exactly **4 medium rows** = Sumner (AL-B1), Spencer (AL-B2 t1), Macdonald (AL-B3 t1), Brunst
(MAYOR) — the four 2017-cycle holders already seated at the 2020-01-14 floor. Confirmed:
- The 2020-01-14 present list shows all four already seated (*"ELECTED OFFICIALS Jeff
  Lambson, Debby Lauret, Tom Macdonald, Terry Peterson, David Spencer, and Brent Sumner"* +
  Mayor Brunst) — and this is exactly the 3 Class-A 2019 winners + 3 Class-B 2017 holders +
  Mayor, so the class stagger is internally consistent.
- **No fabricated `election:2017` citation** anywhere in the `sources` column (0 matches;
  parsed with proper CSV). The string `election:2017` appears **only in the `note` column
  as the disclaimer** *"no fabricated 'election:2017'"* on those 4 rows. Sources instead
  cite observed votes + the 2020 present-list + non-candidacy/re-election in 2021. Correct.

## 4. The two Davids — kept distinct. CORRECT.

`cities.db` has `David Spencer` (person 50000012, council) and `David Young` (50000013,
mayor) as separate persons; roster keys them `david_spencer` (AL-B2) and `david_young`
(MAYOR). Never merged. The shared first name `DAVID` is never used as a key.

## 5. Confidence calibration — clean.

14 high / 4 medium / 0 low. **No pre-floor `high`** (all four rows with `start_date <
2020-01-01` are `medium`). No `high` row is inferential — every high row has an election
result + a minutes present-list + a `cities.db` bound. Calibration is honest.

## 6. Structural invariants — all pass.

- **No overlapping tenures** within any `seat_id` (half-open `[start,end)` chains verified
  programmatically across all 7 seats).
- **Every row** carries non-empty `sources` and `confidence` (0 missing).
- **Election crosscheck clean:** all **14 municipal-general winners** (2019/2021/2023/2025
  Council + 2021/2025 Mayor, excluding WRITE-IN) map to an `elected`/`reelected` tenure with
  matching `election_year` + surname — **0 unmapped**. All cited ranks/vote counts match the
  election CSV (e.g. Millett 2025 rank3 9,077 over Spencer 8,789 = 288-vote final-seat margin).
- **Within-class seat numbers** (A2/A3 Peterson/Lauret→Gale/Killpack; B2/B3 Spencer/Macdonald
  →Mecham/Muhlestein; and B1 Sumner→Millett) are explicitly flagged as a labelling choice
  in each `note` — the person-tenures are exact; the number between paired arrivals is not
  source-attested. Honestly disclosed.
- **Current roster** (2026-01-13 present list) = McCandless (Mayor) + Killpack, Muhlestein,
  Lambson, Gale, Millett, Mecham — exactly the 6 `serving` council rows + serving mayor.

---

## (B) Calibration / honest-gap items (NOT defects — documented tradeoffs)

1. **Person-level vote bounds overspill the pre-floor term rows.** On a multi-term holder's
   *first* row the `first_vote`/`last_vote` are the **person-level** span, so e.g. Spencer's
   AL-B2 term-1 row (`2018-01-01…2022-01-04`) carries `last_vote=2025-12-09` — four years
   past that term's `end_date`. This is disclosed in `CLAUDE.md` ("both rows share the
   person-level span … an accepted disclosure limit"). Correct as documented; a consumer
   must read `start_date`/`end_date` (not `last_vote`) for the tenure window.

2. **Pre-floor term-start `2018-01-01` is inferred from the stagger**, not source-attested
   (the 2017 election + Jan-2018 seating predate both the 2019 election-data floor and the
   2020-01-14 minutes floor). Honestly flagged `medium`; `roster_overrides.csv` is the
   documented path if an exact 2018 seating date surfaces.

## (C) Hardening recommendations for `roster_lib` / skill

1. **Scope the "no shared surname in-window" claim to Council+Mayor.** `CLAUDE.md` states
   *"All Orem surnames are distinct in-window — no shared surname, so no first-name
   disambiguation is needed."* That is true **only within the roster's Council+Mayor scope**.
   `cities.db` contains a **`Ross Spencer` (person 50000046), a Planning Commissioner**
   (177 PC votes, 2020-01-15…2022-01-19) sharing the `Spencer` surname with council member
   `David Spencer`. **No actual risk today** — `person_key` is `first_last` (`david_spencer`
   vs `ross_spencer`), so the key already disambiguates, and the PC is out of roster scope.
   But the prose reasoning ("keyed by their distinct surnames") is what's imprecise: the
   *keys* are safe because they are first+last, not because surnames are globally unique.
   Recommend: reword the CLAUDE.md to say surnames are distinct *among Council+Mayor holders*
   and that safety comes from the `first_last` key, so a future PC-commissioner-to-council
   promotion (or a federation join that mixes bodies) doesn't inherit a false premise.

2. **(Minor) Assert the vote-bound/seating-date invariant in `--check`.** The strongest
   evidence for 0-VACANT is that all 14 vote bounds hit the four January boundaries. If not
   already validated, add a check that every `elected`/`reelected` `start_date` equals an
   existing Council meeting date and that no person's `cities.db` first/last vote falls
   strictly between boundaries — so a future off-cycle appointee (the Vineyard path) would
   trip the validator instead of silently producing a clean-looking chain.

Otherwise: **none.** The Orem roster is well-sourced, well-calibrated, and internally
consistent. The 0-VACANT and voting-mayor claims are correct and defensible against the
sources.

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
