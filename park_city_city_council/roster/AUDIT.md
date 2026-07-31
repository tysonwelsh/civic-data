# Park City roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this roster)
**Scope:** `roster/council_terms.csv` (19 rows), `roster_overrides.csv` (1 data row),
`district_versions.csv` (1 row), `build_roster.py`, `CLAUDE.md`, checked against
`election_results/park_city_results_by_candidate.csv`, `meeting_minutes/minutes/**`,
`meeting_minutes/minutes_unrecovered.csv`, and root `cities.db`.
**Method:** READ-ONLY. Did not run `build_roster.py` (would rewrite CSVs). Quotes below are
verbatim from the cited source files/db.

## Verdict: CLEAN — 0 confirmed defects.

Every high-risk claim was ground-truthed to source and holds. The two same-seat VACANT
intervals chain without overlap; the Worel vote-bound override is legitimately correct and
does **not** mask real council service; the non-voting-mayor invariant matches the db exactly.

---

## (A) CONFIRMED DEFECTS

**None.**

---

## 1. AL-A1 double-crossover chain — VERIFIED

Half-open `[start,end)` intervals on AL-A1 chain exactly, no overlap:

| person | start | end | events |
|--------|-------|-----|--------|
| Worel | 2020-01-09 | 2022-01-06 | elected / became-mayor |
| VACANT | 2022-01-06 | 2022-01-27 | vacated / filled |
| Dickey (appt) | 2022-01-27 | 2024-01-04 | appointed / reelected |
| Dickey (elected) | 2024-01-04 | 2026-01-05 | reelected / became-mayor |
| VACANT | 2026-01-05 | 2026-01-20 | vacated / filled |
| Miller (appt) | 2026-01-20 | — | appointed / serving |

**Crossover #1 (Worel → VACANT → Dickey), quotes verified:**
- `minutes/2022/2022-01-03/2022-01-06_city-council-meeting.md` ROLL CALL (l.23–30): heads
  the present list **"Mayor Nann Worel"** followed by exactly **4** councilmembers (Doilney,
  Gerber, Rubell, Toly) — AL-A1 empty at the 2022 term start.
- Same file, l.34: *"Mayor Worel announced 17 applications were received for the council seat
  vacated when she was elected mayor."* — matches the roster/vacate source verbatim.
- `2022-01-13_city-council-meeting.md` l.424 *"Appointment of New City Council Member to Fill
  the Seat Vacated by Nann [Worel]"*; l.559 *"Council Member Gerber moved to appoint Ryan
  Dickey … to fill the seat vacated by Mayor Worel."*
- `2022-01-27_city-council-meeting.md` l.18–22 *"SWEARING IN … Ryan … Dickey … Ryan Dickey
  was appointed by the Council at the last meeting to fill the remaining term."* cities.db
  role `first_seen 2022-01-27` matches.

**Crossover #2 (Dickey → VACANT → Miller), quotes verified:**
- `2026-01-08_city-council-meeting.md`: Dickey presides as Mayor; roll call shows Dickey +
  4 members (Ciraco, Parigian, Toly, Zegarra), Miller absent — AL-A1 empty at the 2026 term
  start. Corroborating swearing date at l.380 (public-comment prose): *"the new mayor being
  sworn in on Monday"* (2026-01-05 was a Monday); independently anchored by
  `election_results/CLAUDE.md` l.48: *"confirming Dickey as mayor (sworn Jan 5 2026)."*
- `2026-01-15_city-council-meeting.md` l.315 *"Appointment of New City Council Member to Fill
  the Seat Vacated by Ryan [Dickey]"*; l.342–351 a genuine **2-2 tie** (Toly & Zegarra for
  Miller; Ciraco & Parigian for Rubin) then *"Mayor Dickey broke the tie by voting for Molly
  Miller."* — the appointment selection, not a legislative roll-call.
- `2026-01-20_city-council-meeting.md` l.51–53 *"Swearing In of a Council Member … for a Term
  Expiring [Jan-2028] … Council Member-Elect Miller was sworn in."* cities.db role
  `first_seen 2026-01-20` matches.

**Miller "appointed-after-losing-the-primary" twist — VERIFIED:**
`park_city_results_by_candidate.csv`: `2025,municipal primary,Council,…,Molly Miller,432,8.71,
7,N`. She lost the 2025 council **primary** (rank7, is_winner=N), never reached the general,
and was appointed to Dickey's vacated cohort-A seat → serves to Jan-2028. `election_year`
correctly blank (pure appointee). Matches Lehi's Lockhart pattern.

**Both VACANT windows are `high` (no un-recovered minutes):**
`minutes_unrecovered.csv` contains **nothing** in either window (its nearest entries are
2021-12-15 — before Worel's last vote — and 2026-06-04+ future agenda-only meetings). Each
window is bracketed by two recovered meetings (last council vote → documented-vacant meeting).

**Council/Mayor tenures do NOT overlap; MAYOR rows empty:**
Worel and Dickey each have Council rows carrying council vote bounds and MAYOR rows with
empty `first_vote`/`last_vote` (council_terms rows 19–20). No date overlap between any
councilmember tenure and the same person's mayoral tenure.

## 2. The Worel override — VERIFIED CORRECT (not masking service)

This was the KEY question. cities.db `role` for `nannworel`, body=Council, has
`last_seen = 2024-08-22`. Ground-truth of that row:

```
2024-08-22 | Nann Worel | Nay | note='Mayor tie-break' | Council | Res 16-2024
```

Her true last council-**member** vote is **2021-12-16** (Aye/Nay roll calls on Ords 2021-49…
2021-52 etc.; on 2021-12-09 she was Absent). Between 2021-12-16 and the 2024-08-22 tie-break
she cast **zero** council-member votes (she was Mayor from 2022-01-06). Therefore correcting
`last_vote` to 2021-12-16 removes a genuine tie-break smear (the Ogden-Nadolski defect class)
and does **NOT** hide any real service. `roster_overrides.csv` applied: council_terms row 2
shows `first_vote=2020-01-09, last_vote=2021-12-16` (override leaves first_vote blank →
computed floor preserved). Override is legitimate and correctly applied.

## 3. Non-voting mayor — VERIFIED

`SELECT COUNT(*) FROM vote WHERE city='park_city' AND note='Mayor tie-break'` → **2**, and
they are exactly:
- **Beerman 2020-06-25** (Ord 2020-31), `Nay`, 'Mayor tie-break' — his ONLY cities.db Council
  row (role n_votes=1).
- **Worel 2024-08-22** (Res 16-2024), `Nay`, 'Mayor tie-break'.

Dickey's 2026-01-15 tie-break (appointing Miller) is correctly **absent** from cities.db (it
was an appointment selection, not a legislative roll-call). All three MAYOR rows carry empty
vote bounds; `andy_beerman` is omitted from DB_KEY. The other 8 non-empty vote notes in
cities.db are all `db/vote_overrides.csv` clerk-error fixes (Abstain+Aye / Aye+Nay), not
tie-breaks — consistent with the Dickey note's caveat about the 2022-06/2022-10 override rows.

## 4. Pre-floor `medium` rows — HONESTLY FLAGGED

Joyce (AL-B1), Henney (AL-B2), Beerman (Mayor): all `confidence=medium`, seated at the
2020-01-09 data floor, 2017 election / 2018-01-01 term-start explicitly labeled *inferred from
the 4-year stagger*. The 2017 cycle genuinely predates the election CSV (which starts 2019),
so no fabricated 2017/2018 citation exists — `sources` cite only observed 2020 service +
the 2021 election outcome (Joyce not a candidate; Henney lost rank3; Beerman lost to Worel).
Clean.

## 5. Structural invariants + election crosscheck — VERIFIED

- **All general winners map** to an elected/reelected/became-mayor tenure: 2019 Council
  (Worel/Gerber/Doilney), 2021 Mayor (Worel) + Council (Toly/Rubell), 2023 Council
  (Dickey/Parigian/Ciraco), 2025 Mayor (Dickey) + Council (Toly/Zegarra). No drift.
- **Primary advancers correctly dropped** (`keep_election_row = "general" only`). Two traps
  handled: Parigian's 2019 **primary** is_winner=Y (general N) does NOT create a phantom
  2019 tenure; Miller's 2025 primary is_winner=Y does NOT seat her by election.
- **No overlapping tenures** on any seat, including the heavily-reused AL-A1.
- **Every row** carries non-empty `sources` + `confidence`.

---

## (B) Calibration / honest-gap items (not defects)

1. **2026-01-05 swearing source is commenter prose.** The `high` "sworn on Monday" evidence
   for Dickey's mayoral start lives in a **public comment** quoted at l.380 of the 2026-01-08
   minutes, not a clerk/roll-call line. It is independently corroborated by
   `election_results/CLAUDE.md` ("sworn Jan 5 2026"), so the date is sound and `high` is
   defensible — but the `vacate_source` phrasing "minutes:2026-01-08 states…" would read more
   precisely as "minutes:2026-01-08 (public comment) + election_results/CLAUDE.md." Cosmetic.
2. **Person-vs-tenure vote-bound disclosure.** Two-tenure holders share person-level bounds on
   both rows (Toly's two AL-B1 rows and Dickey's two AL-A1 rows both show the full
   person-level span, e.g. Dickey 2022-01-27..2025-12-18). This is the documented fleet-wide
   disclosure (CLAUDE.md §first_vote/last_vote); the authoritative interval is `start`/`end`.
   Not a defect.
3. **Within-cohort A2/A3 and pre-floor B1/B2 seat numbers are labelling choices** (flagged in
   `note`). Person-tenures are exact; the seat *number* between paired same-cohort arrivals is
   not source-attested. Honestly disclosed.

## (C) Hardening recommendations

1. (Optional, cosmetic) Tighten the 2026-01-05 `vacate_source` string to note the "sworn on
   Monday" quote is public-comment prose and that the primary date anchor is
   `election_results/CLAUDE.md`. No data change.

Otherwise: **none.** The roster is internally consistent, every row is source-anchored, the
two same-seat VACANT intervals chain cleanly, and the marquee Worel override is correct rather
than concealing. Ship as-is.

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
