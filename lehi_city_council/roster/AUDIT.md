# Lehi roster — independent adversarial audit

**Date:** 2026-07-11
**Auditor:** independent (did NOT build this layer)
**Scope:** `lehi_city_council/roster/` (`council_terms.csv`, `district_versions.csv`,
`roster_overrides.csv`, `build_roster.py`, `CLAUDE.md`) ground-truthed against
`election_results/`, `meeting_minutes/minutes/**`, and root `cities.db`.
**Method:** read every cited minutes passage; re-ran the election crosscheck; queried
`cities.db` for vote bounds, mayor tie-breaks, and the appointment-day roll call; read the
`roster_as_of` boundary logic in `scripts/roster_lib.py`.

**Verdict: essentially CLEAN.** The high-risk vacancy/appointment chain, the non-voting-mayor
handling, the pre-floor `medium` inference, and the election mapping are all correct and
source-faithful. One genuine (minor) defect: an off-by-one at the vacate boundary. Two
hardening recommendations follow (non-voting-mayor DB_KEY footgun; vacate_date convention).
No fabrication found; every quoted source below was verified verbatim.

---

## (A) CONFIRMED DEFECTS

### DEFECT-1 (minor) — vacate boundary is off by one: roster_as_of returns VACANT on Albrecht's last day of actual service

**Row:** `AL-A1 / VACANT` (`start_date=2025-12-02`) and `AL-A1 / Paige Albrecht` 2nd tenure
(`end_date=2025-12-02`).

`roster_as_of` (scripts/roster_lib.py:499–507) is half-open `start <= date < end`:

```
if r["end_date"] and r["end_date"] <= date:   # end is EXCLUSIVE
    continue
```

Albrecht's 2nd tenure ends `2025-12-02` and the VACANT interval begins `2025-12-02`. So a
query **`roster_as_of('2025-12-02','Council')` returns the AL-A1 seat as VACANT** — excluding
Albrecht. But the 2025-12-02 minutes show her present and voting **twice** that day:

> `Members Present: … Paige Albrecht, Council Member` (2025-12-02 minutes, l.18)
> `Roll Call Vote: YES: Paige Albrecht, Chris Condie, Paul Hancock, Heather Newall,` (l.69, and again l.83)

So on the single day 2025-12-02 the roster contradicts its own source: it reports the seat
vacant while the member was seated and casting recorded votes. The biennial swap days
(e.g. Southwick `end 2024-01-09` / Stallings `start 2024-01-09`) do **not** have this problem
— there the boundary day legitimately belongs to the newcomer because the oath physically
transitions the seat that day. The VACANT case is different: `vacate_date` was set to
Albrecht's **last day of service** (a day she fully served), so using it as the *exclusive*
half-open end wrongly drops that day.

**Fix (pick one, then document it as the standard):**
- Set `vacate_date` = *day after* the last recorded service (`2025-12-03`) so the last served
  day stays inside the member's tenure; the VACANT interval then spans `[2025-12-03,
  2025-12-22)`. This keeps the "last-recorded-service" anchor and removes the off-by-one; OR
- Adopt the **first-absent** convention explicitly (`vacate_date=2025-12-16`, the first
  documented-vacant meeting) — no recorded-service day is ever mislabeled vacant, at the cost
  of carrying Albrecht through the (already-flagged) unknown-resignation-date bracket.

Either is defensible; the current choice is the only one that produces a source-contradicting
day. This is the concrete manifestation of the still-unsettled convention flagged in the build
(see Hardening-2). Severity minor: it mis-answers exactly one boundary day and the underlying
resignation-date uncertainty is honestly documented — but a roster whose one job is
"who held the seat on date X" should not answer VACANT on a day the member voted.

---

## (B) CALIBRATION / HONEST-GAP ITEMS (all correct — no action needed)

### The VACANT / appointment chain — VERIFIED, high is justified
Every link is in **recovered** minutes (no `meeting_minutes/minutes_unrecovered.csv` exists;
the only `minutes_unrecovered.csv` is in `planning_commission/` and lists no council dates
relevant here — confirmed on disk). Quoted verbatim:

- **Vacancy procedure, 2025-12-16** (l.502–505):
  > `Consideration of Resolution #2025-95 adopting procedures governing the appointment,
  > interview, and voting process for filling the current vacancy in the Lehi City Council.`
  > `The Council discussed procedures to fill the vacancy due to the resignation of Paige
  > Albrecht.`
  Present list that day is **4** members (Condie, Hancock, Newall, Stallings + Mayor Johnson,
  l.17–21); `Mayor Johnson … noted that all four Councilmembers were present` (l.35).
- **Appointment, 2025-12-22** (l.354–358, 361–362):
  > `Chris Condie moved to approve Resolution #2025-103 appointing Emily Lockhart to the Lehi
  > City Council. Paul Hancock seconded the motion.`
  > `Roll Call Vote: YES: Paige Al[b]recht, Chris Condie, Paul Hancock, Heather Newall,
  > Michelle Stallings. The motion passed unanimously.`
  > `The Oath of Office was administered to Emily Lockhart after the adjournment.`

**The "Voting Member for the Vacancy" claim is TRUE, not fabricated** (I specifically tried to
break this). The roster note says Lockhart's first db vote is 2026-01-06 because the 12-22
appointment vote "was cast by Albrecht as the retained 'Voting Member for the Vacancy'." The
2025-12-22 minutes header carries exactly that line: `Voting Member for the Vacancy: Paige
Albrecht` (l.24), and Albrecht appears in the Resolution #2025-103 roll call (l.357). Lockhart
was sworn **after adjournment**, so she cast no vote that day. `cities.db` confirms Lockhart's
first **Council-body** vote is 2026-01-06 (her 254 PlanningCommission votes 2024-01-11…
2025-11-13 are correctly excluded from `first_vote` — the body filter works). `first_vote=
2026-01-06` is **correct**.

- The **Lockhart twist** is real: 2025 general council `EMILY LOCKHART … rank 3 … is_winner=
  False` (loser); she is a pure appointee (`election_year` blank) to Albrecht's *different*
  cohort-A seat. `keep_election_row` correctly drops her 2025-**primary** advancer row.
- Minor imprecision (not a defect): the note says Albrecht's "last recorded vote is
  2025-12-02." The **minutes** actually record an Albrecht vote on 2025-12-22 (as the vacancy
  proxy); `cities.db` misses it only because the source typo `Paige Alrecht` isn't in the
  extractor's normalized-variant list. Doesn't change the vacate decision (the 12-22 vote was
  in the special proxy capacity, not as the seated member) — flagged for the record.

### Non-voting mayor — VERIFIED
`cities.db` shows Mayor **Mark Johnson** with exactly **4** votes on the Council body —
`2022-06-14 Aye, 2023-04-11 Aye, 2024-03-26 Nay, 2025-12-16 Aye` — all tie-breaks (matches
`meeting_minutes/CLAUDE.md` and the roster note; the 2025-12-16 one is the l.496–499 `2–2 …
Mayor Johnson voted YES. The motion carried 3-2`). Zero regular council votes. **Binns** has
0 db votes. All three `MAYOR` rows carry **empty** `first_vote`/`last_vote` — correct; the
tie-breaks are documented in the note, not smeared into the bounds. (See Hardening-1 for the
mechanism concern.)

### Pre-floor `medium` terms — VERIFIED and honestly flagged
Condie (AL-B1 #1), Hancock (AL-B2 #1), Johnson (MAYOR #1) are `medium`, term-start
`2018-01-01` inferred from the 2017-cycle stagger, and **none cites a fabricated `election:
2017`** — sources are the 2020 present-list + the 2022 oath only. Corroborated by the
**2020-01-14** swearing-in naming only the three 2019 winners:
> `2. Swearing In Ceremony for City Council Members` / `Councilors Southwick, Albrecht, and
> Koivisto were sworn in.` (2020-01-14, l.40–41)
Condie, Hancock, and Mayor Johnson head the same present-list (l.17–21) but were **not** sworn
that day → continuing incumbents, exactly as claimed. The **2022-01-04** (`Swearing In Ceremony
for Mayor Johnson, Councilor Condie and Councilor Hancock.`, l.33) and **2024-01-09**
(`Swearing-In Ceremony for Councilors Paige Albrecht, Heather Newall, and Michelle Stallings`,
l.35) ceremonies verify verbatim.

### Confidence calibration — CLEAN
14 high / 3 medium / 0 low (counts match). **No pre-floor `high`.** No `high` row is actually
inferential (each cites an election result or a minutes-documented oath/appointment/vacancy).
The 3 `medium` rows are exactly the inferential ones. `vacate_confidence` invariant holds (the
VACANT row is `high` and its window contains no un-recovered minutes).

### Structural invariants — CLEAN
Per-seat chains are gap-free and non-overlapping (AL-A1 Albrecht→Albrecht→VACANT→Lockhart;
AL-A2/A3/B1/B2/MAYOR each chain cleanly). 17 rows = 16 person-tenures + 1 VACANT. Every row
has non-empty `sources` + `confidence`. VACANT uses `person_key=vacant` (no fabricated name).
`person_key` on surname distinguishes the two shared first names (Paul **Hancock** vs Paul
**Binns** → `paul_hancock`/`paul_binns`). The A2/A3 and B1/B2 within-cohort seat numbers are
explicitly flagged as labelling choices in the notes.

### Election crosscheck — CLEAN
Every general winner maps to a tenure: 2019 Albrecht/Southwick/Koivisto; 2021 Johnson(M)/
Condie/Hancock; 2023 Stallings/Albrecht/Newall; 2025 Binns(M)/Harrison/Freeman. No fabricated
winners. 2023 & 2025 **primary** advancers (Kunze/Roberts/Glade; Lockhart/Peterson) are
correctly NOT counted as seat winners. Departures verify against the CSV: Condie ran for
**mayor** 2025 (primary rank3, `is_winner=False`) → `did-not-run` for council; Hancock ran for
council re-election and **lost** the 2025 primary (rank5, `is_winner=False`) → `lost`.
2026-01-06 present list confirms the current roster (`Paul Binns, Mayor; Rachel Freeman; James
Harrison; Emily Lockhart; Heather Newall; Michelle Stallings`).

### Source-data observation (NOT a roster defect)
2025-12-16 minutes l.90–91 contain stale boilerplate — `all Councilmembers were present.
Councilor Albrecht led the Pledge of Allegiance` — although the authoritative present list
(l.17–21) and every roll call that day show only 4 members and no Albrecht. The roster
correctly used the 4-member present list. Noted so a future re-reader isn't misled by the
source's own copy-paste artifact.

---

## (C) HARDENING RECOMMENDATIONS for `roster_lib` / the skill

### Hardening-1 — YES, the non-voting-mayor DB_KEY omission is a footgun; make it a first-class config flag
The mayor is kept out of vote-bound population by **omitting `mark_johnson` from the driver's
`DB_KEY` map** — an implicit, undocumented convention with no validator behind it. Failure mode:
if a future maintainer regenerates, adds the new mayor (Binns), or copies this driver to another
non-voting-mayor city and *doesn't remember* to omit the mayor, the mayor's tie-break votes are
silently folded into `first_vote`/`last_vote`, smearing a bogus person-level span across the
MAYOR tenures — wrong data, no error raised. Most Utah cities in this repo have a
non-voting/tie-break-only mayor (Nephi, Provo, SLC, Taylorsville, South Jordan, …), so this is a
recurring shape, not a Lehi one-off.

**Recommendation:** add a declarative `non_voting_mayor: bool` (or `tiebreak_only_bodies` /
per-seat `role='Mayor'` handling) to the `roster_lib` config that, when set: (a) auto-excludes
MAYOR-body rows from `first_vote`/`last_vote` population regardless of DB_KEY, (b) optionally
auto-summarizes the tie-break vote dates into the MAYOR-row note, and (c) is asserted by a
validator (`MAYOR row has non-empty vote bounds while non_voting_mayor=True` → FAIL). That turns
today's "remember to leave a name out of a dict" into a checked, self-documenting declaration.

### Hardening-2 — settle the `vacate_date` convention in `roster_lib` (last-service vs first-absent) and fix the half-open boundary
DEFECT-1 is the concrete cost of leaving this unsettled. The build uses **last-recorded-vote**
as `vacate_date` and feeds it straight into the **exclusive** half-open end, which drops the
member's last served day. Recommendation: standardize on **"last day of recorded service, with
the VACANT interval beginning the following day"** — i.e., when `vacate_date` is derived from a
last-service signal, `chain_end_dates` should set the predecessor's `end_date` to
`vacate_date + 1 day` (or equivalently start VACANT the day after), so `roster_as_of` never
reports vacant on a day the member is recorded serving. Document the chosen rule in
`roster_lib` and add a validator: `no VACANT interval starts on a date on which the predecessor
has a recorded vote/presence`. (If the project prefers **first-absent** semantics instead,
encode that explicitly and drop the "last-recorded-vote" language from the notes — but pick one
and enforce it, because the two conventions disagree by up to the full bracket window.)

### Hardening-3 (nit) — extractor variant list
Add `Alrecht → Albrecht` to the minutes extractor's OCR/typo normalization
(`meeting_minutes/CLAUDE.md` already maps `Albreht`). It's why `cities.db` misses Albrecht's
2025-12-22 proxy vote. Out of scope for the roster layer, but it's the reason the roster's
"last recorded vote 2025-12-02" phrasing is db-true but minutes-imprecise.

---

## Bottom line
No fabrication, no misattributed seat, no overstated confidence, correct VACANT placement, and
the appointed-after-losing / mayor-proxy-voter twists are all real and source-backed. The lone
substantive fix is the one-day vacate boundary off-by-one (DEFECT-1), which doubles as the
worked example for settling the `vacate_date` convention (Hardening-2). The non-voting-mayor
handling is correct today but rests on an implicit omission that should become a checked config
flag (Hardening-1).

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
