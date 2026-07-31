# Sandy council-roster — adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did not build this layer)
**Scope:** `roster/council_terms.csv`, `district_versions.csv`, `district_precincts.csv`,
`roster_overrides.csv`, `CLAUDE.md`, derived sidecars — read against
`election_results/`, `meeting_minutes/minutes/**`, root `cities.db`, `db/sandy.db`.
**Method:** every tenure boundary, crossover, vacancy, redistricting fact, and vote-bound
cross-checked to a primary source. Read-only except this file.

**Verdict: the roster is structurally SOUND.** 22 tenures / 8 stable seats, zero overlaps,
every row sourced + confidence-graded, all 16 district+mayor winners map, all 6 at-large
winners map by cohort, redistricting exact, non-voting mayor honored, all vote-bounds
verbatim from `cities.db`. **No structural, chaining, or winner-mapping defect found.**
Two DOCUMENTATION-only inaccuracies in generated *note* prose (below) — neither touches a
tenure date, vote-bound field, geometry, or winner mapping.

---

## (A) CONFIRMED DEFECTS

### A1 — Appointment resolution mis-cited as "21-03"; signed resolution is **22-03** (MEDIUM, documentation)

The roster cites Scott Earl's D4 appointment as **Resolution 21-03** in two places:
- `council_terms.csv`, D4/Scott Earl row `sources`: *"motion to appoint him via Resolution 21-03"*
- `council_terms.csv`, D4/Zoltanski row note; `roster/CLAUDE.md` §"The D4 VACANT interval": *"(Resolution 21-03)"*

The primary source is internally contradictory, and the **authoritative artifact says 22-03**.
From `meeting_minutes/minutes/2022/2022-01-17/2022-01-18_city-council-meeting.md`:

```
2. 21-516 City council adopting a resolution appointing an interim replacement to fill
   the unexpired term of the vacated council district four seat
   Attachments: Resolution 22-03.pdf
                Resolution 22-03 Signed.pdf
   A motion was made by Ryan Mecham, seconded by Zach Robinson to amend
   Resolution 21-03, a resolution appointing Mr. Scott Earl ...
```

The **signed enacted document** is `Resolution 22-03 Signed.pdf`; "21-03" appears only in the
OCR'd motion prose. Sandy's entire 2022 resolution series is numbered `22-xx` (this same meeting
uses 22-04C; the Jan-4 meeting 22-01C/22-02C; the redistricting 22-24C). `db/sandy.db`
`legistar_matter` file `21-516` carries a null `enactment_number`, so it cannot disambiguate — the
signed attachment is the only authority. **"21-03" is an OCR/typo artifact of "22-03".**

**Fix:** in `build_roster.py`'s note strings (and `roster/CLAUDE.md`), cite **Resolution 22-03**
(the signed document), optionally noting the minutes prose OCR reads "21-03". The appointment date
(2022-01-18) and the 5–1 tally are correct and unaffected. (Cannot be fixed via
`roster_overrides.csv` — resolution number lives in descriptive prose, not a `TERM_COLUMNS` field.)

### A2 — "last recorded D4 vote is 2021-12-14" contradicts `cities.db`; it is **2021-12-07** (LOW, documentation)

The roster asserts a specific vote date in three note strings:
- `roster/CLAUDE.md`: *"Her last recorded D4 vote is 2021-12-14"* and *"Her true D4 service ended 2021-12-14."*
- `council_terms.csv` D4/Zoltanski row + Mayor/Zoltanski row: *"last true D4 vote 2021-12-14"* / *"a voting member, last D4 vote 2021-12-14"*

Her **last recorded (named) vote is 2021-12-07**, per the roster's own cited source. `cities.db`
`vote`→`meeting` for Monica Zoltanski jumps `2021-12-07` → `2023-12-06` (a Mayor-era canvass); the
flat `meeting_minutes/all_votes.csv` agrees (last member-row date 2021-12-07). On **2021-12-14** she
*was present and seconded the sole motion* ("A motion was made by Brooke Christensen, seconded by
Monica Zoltanski …") and gave her District 4 farewell — but that motion was a **unanimous voice vote
with no named members** (`all_votes.csv` 2021-12-14 motion 1: `member=''`, `result="Unanimous
(voice)"`), so she cast **no recorded named vote** that day.

So 2021-12-14 was Zoltanski's **last meeting served** as D4 member, not her last *recorded vote*. The
note conflates the two.

**Fix:** reword to "last recorded named vote 2021-12-07; last meeting served as D4 member 2021-12-14
(seconded the sole motion — a unanimous voice vote; gave her D4 farewell)." The D4 tenure end
(2022-01-03) and the structured `first_vote`/`last_vote` fields (2020-01-07 / 2025-11-18, verbatim
from `cities.db`) are correct and unaffected.

---

## (B) Calibration / honest-gap items — CONFIRMED CORRECT (no action)

- **Zoltanski D4→Mayor crossover — clean.** D4 2020–21 voting member (2020-01-07 masthead "Monica
  Zoltanski, District 4"); won 2021 Mayor RCV 8620–8599 over Bennett (election file); sworn
  2022-01-03 (2022-01-04 minutes "swearing in ceremony yesterday", Mayor's Report). D4 ends
  2022-01-03, Mayor begins 2022-01-03 — **half-open, zero overlap** (verified programmatically).
- **D4 VACANT window 2022-01-03 → 2022-01-18 — real & documented.** 2022-01-04 masthead prints
  **"Seat Vacant, District 4"**; the meeting notes the vacancy notice with interviews "January 18,
  2022." Appointment confirmed at 2022-01-18: verbal vote **5–1 for Scott Earl over Pat Casaday**
  (Stroud/Robinson/D'Sousa/Houseman/Sharkey → Earl; **Mecham → Casaday**) — matches roster exactly.
- **Prior mayor Kurt Bradburn — confirmed.** 2020-01-07 masthead "Administration: Mayor Kurt
  Bradburn"; not among the 8 candidates in the 2021 Mayor race (election file) → `did-not-run`. No
  `cities.db` role row (0 council votes) → non-voting, bounds empty. Correct.
- **Two return members — confirmed.** 2026-01-06 minutes: *"new and returning Council Members Kris
  Nicholl, District 3 and Brooke Christensen, District 1"*; Christensen "excited to return to the
  Council and represent District 1." Intervening holders Mecham (D1) and Robinson (D3) both present
  in the 2022-01-18 and 2024-01-09 mastheads. Non-contiguous D1/D3 chains verified — no overlap,
  no spurious VACANT. Kris Nicholl ≡ Kristin Coleman-Nicholl (one `person_key`) — correct.
- **Redistricting — exact.** 2022-05-03 minutes: motion Scott Earl / second Brooke D'Sousa to adopt
  **Resolution #22-24C … selecting Alternative Map 4-1b**, **Yes: 7** (Stroud, Robinson, Houseman,
  Sharkey, Mecham, D'Sousa, Earl) = unanimous 7-0. `plan_2022` real geometry (high) + `plan_pre2022`
  explicit acquisition GAP (blank geometry, low) — honest, not fabricated.
- **Vote-bound smears — all verbatim from `cities.db` `role`, correctly flagged informational.**
  Zoltanski last_seen 2025-11-18 (canvass smear), Christensen/Coleman-Nicholl 2020-01-07..2026-06-02
  (2022–25 off-council gap), Robinson/Houseman shared AL↔D bounds — every value matches the `role`
  table; tenure dates come from elections+minutes, not these fields. (Sub-claim A2 above is the one
  prose slip inside this otherwise-correct treatment.)
- **Non-voting mayor — honored.** All MAYOR rows have empty `first_vote`/`last_vote`; Bradburn absent
  from `role`; Zoltanski's only Mayor-era `role` activity is 3 canvass actions, correctly excluded
  from the mayoralty bounds.
- **Pre-floor `medium` rows (4)** — Christensen (D1), Coleman-Nicholl (D3), Robinson (AL-C), Bradburn
  (MAYOR): term-start 2018-01-01 inferred from the B-cycle stagger, honestly graded `medium`, no
  fabricated citation (each cites the documented 2020–21 membership + notes the pre-floor inference).
- **At-large multi-winner limitation — benign & correctly worked around.** The lib's
  contest→seat forward check cannot map Vote-for-2/1 at-large winners to a specific AL seat; the
  6 "unmapped contest … At-Large" lines are expected informational output, and the driver's cohort
  cross-check maps all 6 winners (2019 Sharkey+Houseman, 2021 D'Sousa, 2023 Sharkey+DeKeyzer, 2025
  D'Sousa). Confirmed a limitation, not a missed winner.
- **Within-council moves** Robinson AL-C→D3 (2021) and Houseman AL-B→D4 (2023) — both confirmed in
  the 2022-01-18 / 2024-01-09 mastheads. Precinct composition 110 plan_2022 (D1 25 / D2 30 / D3 31 /
  D4 24) + 4 gap rows — matches `CLAUDE.md`.
- **Structural invariants** — 22 rows, 18 high / 4 medium / 0 low, 0 overlaps, every seat chains
  end==next-start, every seat exactly one open row, every row has sources+confidence. All pass.

---

## (C) HARDENING recommendations

The precinct point-in-polygon cross-check cluster, the at-large candidate→seat hook, and the
vote-bound-smear clamp are already logged in `roster/CLAUDE.md`. NEW item:

- **Generated note prose is un-correctable via `roster_overrides.csv`.** Both defects above (A1, A2)
  live in hard-coded note strings emitted by `build_roster.py`, not in `TERM_COLUMNS` data fields, so
  the documented override mechanism cannot reach them — a fix requires editing the driver source. If
  note text is expected to carry load-bearing provenance (resolution numbers, "last vote" dates),
  consider (a) sourcing those specific tokens from data (e.g. the signed-attachment resolution number
  from `db/sandy.db`/packets; the last vote date from `cities.db`) rather than hand-authored prose, or
  (b) adding a note-override column so hand corrections don't require a code edit. Otherwise no new
  hardening needed — the layer is clean.

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
