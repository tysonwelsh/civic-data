# Bluffdale roster — independent adversarial audit

**Auditor:** independent QC pass (did NOT build the roster).
**Date:** 2026-07-12.
**Scope:** `roster/council_terms.csv` (15 tenures), `district_versions.csv` (1 row),
`roster_overrides.csv` (0 data rows), `build_roster.py`, `roster/CLAUDE.md`, ground-truthed
against `election_results/bluffdale_results_by_candidate.csv` + `bluffdale_races.csv` +
`raw/sovc/*.xlsx`, `meeting_minutes/minutes/**` (the four oath ceremonies quoted below),
and root `cities.db` (`role`/`vote`/`person`, `city='bluffdale'`).
**Method:** re-derived every tenure from primary sources; quoted the minutes; re-ran all
vote bounds (incl. per-tenure clamping) from `cities.db`; programmatic structural-invariant
checks; adversarially attacked the roster's two bold claims by attempting alternative
consistent histories; re-parsed the raw 2019 county SOVC workbook myself. Ran
`build_roster.py --check` — validators pass and both regenerated CSVs are **byte-identical**
to the pre-run copies (idempotent, no mutation).

**Verdict: the roster is CLEAN and its two bold claims are both TRUE — claim (a) is not
merely corroborated but arithmetically PROVEN from the county's own ballots-cast sheet
(the 2019 4-YEAR contest recorded more candidate votes than a vote-for-2 contest could
mathematically produce, in EVERY precinct).** No fabricated names, no phantom or dropped
tenures, no overlaps, correct 5+1 current roster, all 15 vote bounds re-derive exactly,
mayor rows correctly blank, confidence honestly calibrated. Findings are one elections-layer
scope note (the flagged 2019 defect is BROADER than the roster describes — good news for
the roster, more work for the queued elections review) plus two nit/minor label items.

| Check | Result |
|---|---|
| 1. Tenures re-derived from primary sources | **PASS** |
| 2. Vote bounds vs `cities.db` (clamped; mayor blank) | **PASS** (15/15 exact) |
| 3. Structural invariants (overlap/chain/sources/current 5+1) | **PASS** |
| 4a. Bold claim: 2019 vote-for-3 / Hales `is_winner` defect | **PASS — PROVEN** (F1 extends its scope) |
| 4b. Bold claim: Crockett 2019 = 2-yr unexpired special of Jackson's seat | **PASS — forced; no alternative history survives** |
| 5. 8th-voter sentinel + bidirectional election crosscheck | **PASS** (1 legitimate 6-voter roll, explained; see F2) |
| 6. Confidence calibration (13 high / 2 medium) | **PASS** |

---

## What ground-truthed CLEAN (verified against source)

- **All four oath ceremonies verify verbatim.**
  - `2020/2020-01-06/council_2020-01-06_702.md`: agenda item 2 — *"Council Members Elect;
    Traci Crockett, Jeff Gaston, Mark R. Hales, and Dave Kallas, administered by Judge Scott
    Mickelsen"*; present-list lists each as *"City Council Member-Elect"* (incl. *"Mark R.
    Hales, City Council Member-Elect"*); narrative — *"Mayor Timothy commented on the unique
    nature of having **four City Council Members sworn in at the same time**."*
  - `2022/2022-01-03/council_2022-01-04_1012.md`: *"Mayor Elect, Natalie Hall; Council
    Members Elect, Wendy Aston and Traci Crockett, Administered by Judge Scott Mickelsen"*;
    *"Judge Scott Mickelsen administered the Oath of Office to Council Members Wendy Aston and
    Traci Crockett. He then administered the Oath of Office to Mayor Elect Hall"*; and the
    Timothy tribute — *"Mayor Hall recognized Mayor Derk Timothy for his **12 years of
    dedicated service**"* (→ mayor since Jan 2010, matching his 2009/2013/2017 wins in the
    election file: 812, 1,245, unopposed 1,238).
  - `2024/2024-01-08/council_2024-01-10_1331.md`: *"Council Members Elect Steve Austin,
    Gregory Wilding and Alan Lord, Oath of Office administered by Judge Scott Mickelsen"* —
    **THREE** elected in the 2023 cohort-A cycle.
  - `2026/2026-01-05/council_2026-01-05_1745.md`: *"Judge Scott Mickelsen administered the
    Oath of Office for new Council Members **David McKinley McLeod Smith**, Wendy Watterson
    Aston and Natalie Caudell Hall"* — the Mackey-Smith legal-name claim is verbatim-correct;
    and Aston's remark — *"**This is her third swearing in**, but this is the first time with
    a choir"* — corroborating seatings 2018/2022/2026 exactly as the roster reads it.
- **All 15 `first_vote`/`last_vote` values re-derive exactly** from `cities.db`
  (`body='Council'`, clamped to each tenure's `[start_date, end_date)`). Spot-verified the
  three hard seams: Aston t1/t2 split at 2022-01-04 → `2021-12-08 | 2022-01-12` ✓; Aston
  t2/t3 split at 2026-01-05 → `2025-11-18 | 2026-02-25` ✓; Crockett t2 last council vote
  `2025-10-08` ✓ (her true last observed vote 2025-12-10 is RDA — the row's note says
  exactly that). Hales' `first_vote=2020-02-12` is real (a **Nay**; his first Aye is
  2020-04-08 — the bound correctly takes the earlier). **All three MAYOR rows carry EMPTY
  bounds** per `non_voting_mayor=True` ✓.
- **The mayoral vote model verifies in `role`.** Timothy: **RDA-only** role rows,
  `2020-06-10..2021-12-08`, n=7 — exactly as the roster note states. Hall: `body='Council'`
  role row `2022-11-09..2025-05-14`, **n_votes=2** — the two documented recorded mayoral
  votes (see F2) — plus RDA/LBA Chair rows. Neither smears into a council tenure.
- **Election anchors: 100% match.** Every vote/pct/rank/margin quoted in `sources`/`note`
  checks against the candidate file: Kallas 1,120 r1 / Gaston 1,054 r2 / Hales 1,044 3rd-of-5
  (2019); Crockett 1,140 v. James 907 (2019 2-YEAR); Aston 833 + Crockett 1,098 first-choice
  and Hall 2,497 v. Roberts 806 (2021 RCV pilot); Austin 1,460 / Wilding 1,429 / Lord 1,397 /
  Hales 1,387 4th-of-6 (2023); Aston 1,959 r1 + Smith 1,860 r2 and Hall 1,993 v. Pavlakis
  1,927 = 50.84%, 66-vote margin (2025); Jackson 744 + Aston 708 (2017); Kallas 2017 2-YEAR
  uncontested 1,234; Timothy unopposed 1,238 (2017).
- **Bidirectional election crosscheck (ran it by hand).** Forward: all 12 `is_winner=Y`
  general winners 2019–2025 map to `elected`/`reelected` tenures (`--check` prints zero
  unmapped-winner warnings). Reverse: every elected tenure's `election_year` maps back to an
  `is_winner` general row **except the three documented exceptions** — Aston-2017 and
  Timothy-2017 (pre-floor cycles deliberately excluded by `keep_election_row`'s `year>=2019`,
  both honestly `medium`, rationale written into the config comment) and **Hales-2019 (the
  proven winner-marking defect, F1)**. No fabricated winners; the deliberately-NOT-rostered
  2017 wins (Kallas' 2-year special, Jackson's seat) are exactly the wholly-pre-floor set.
- **No unrostered voter; no OCR ghost mapped.** The `cities.db` council voter set is exactly
  the 10 mapped `DB_KEY` people (9 members + Hall's 2 mayoral votes). Every junk/surname-only
  person row (`astin`, `auston`, `crocket`, `hales`, `councu`, …) carries **0 votes** — the
  roster CLAUDE.md's claim verified. Alan Jackson appears **nowhere** in `role`/`vote`, and a
  grep of all 2020+ minutes finds "Jackson" only as a Percy Jackson musical and a construction
  company — his pre-floor departure is a genuine gap, correctly not rostered.
- **Structural invariants — all PASS (programmatic):** 15 rows; 13 high / 2 medium / 0 low;
  0 rows missing `sources`/`confidence`; 0 overlapping tenures; every seat chains half-open
  with **end_date = successor start** (2024-01-10 ×3, 2022-01-04 ×3, 2026-01-05 ×3); current
  roster = **exactly 5 serving Council + 1 serving Mayor** (Austin, Wilding, Lord, Aston,
  Smith + Hall). Idempotency: `--check` re-run leaves both CSVs **byte-identical**.
- **Federation verified:** root `cities.db` carries 15 bluffdale `term` rows + 1
  `district_version`; `v_council_current` returns the correct six.
- **`district_versions.csv`** — correctly degenerate (one At-Large row);
  `geo/city_boundary.geojson` exists on disk; the Camp-Williams two-county caveat and the
  `effective_start = data floor` convention are honest.

---

## The two bold claims, attacked

### Claim (a) — 2019 was VOTE-FOR-3 and Hales' `is_winner=False` is a defect — **TRUE, and now PROVEN, not just argued**

The roster's evidence (3 winners in 2007/2011/2015/2023; four Members-Elect sworn
2020-01-06; Hales' exact 4-year vote record 2020-02-12..2023-12-14, 352 council votes; his
2023 re-run) all verified. I then went one layer deeper than the builder did — into
`raw/sovc/2019-11-05-general-election-sovc.xlsx` — and found a **decisive arithmetic proof**:

- The sheet `BLF Council - 4 yr` prints **no "Vote for N" header** (just *"BLUFFDALE CITY
  COUNCIL AT LARGE 4 YEAR"*) — so the elections dataset's `n_seats=2` was **hand-set** in
  `clean_elections.py`'s `N_SEATS` table, not source-printed.
- The workbook's own **`Registered Voters` sheet gives Bluffdale 2019 ballots cast = 2,154**
  (382+304+238+452+9+341+428). The 4-YEAR contest recorded **4,977 candidate votes**. A
  vote-for-2 contest caps at 2 × 2,154 = **4,308 < 4,977 — mathematically impossible.**
- It is impossible **in every single precinct**: BLF001 889 votes vs ceiling 764; BLF002
  710 vs 608; BLF003 521 vs 476; BLF004 1,065 vs 904; BLF005 22 vs 18; BLF006 789 vs 682;
  BLF007 981 vs 856. The votes/ballots ratio (2.31 citywide, ~2.4 per precinct) is the
  fingerprint of **vote-for-3 with undervoting** — matching 2023's measured vote-for-3 ratio
  (7,623/3,156 = 2.42) almost exactly.
- Independent corroboration: the 2019 **general had 5 candidates**. A 2-seat primary advances
  4 — five in the general is impossible under `n_seats=2`; under vote-for-3, six advance
  (top-6 includes Jon R. Hansen, 353, who evidently did not appear on the general ballot) and
  five is unremarkable.

**Attempted alternative history** — Hales sworn 2020-01-06 as an appointee to some vacancy
rather than a winner — fails: the agenda, present-list, and narrative all print him
*"Council Member-Elect"*, the ballot arithmetic requires a third 4-YEAR winner, and without
a third 2019 win the 2023 cycle could not have had three expiring seats to elect
Austin/Wilding/Lord to. No consistent alternative exists. See **F1** for the finding this
produces (the defect's blast radius in the elections dataset is wider than the roster's
description).

### Claim (b) — Crockett's 2019 win = 2-year unexpired special of Alan Jackson's 2017 seat — **TRUE (forced; no alternative survives)**

- The contest is **definitionally 2-year** (SOVC sheet *"BLF Council - 2 yr"*, title
  *"…AT LARGE 2 YEAR"*): term Jan-2020 → Jan-2022. A 2-year term seated Jan-2020 can only be
  the **unexpired remainder of a 4-year seat won in 2017** (a 2015-won seat expires Jan-2020
  and cannot leave a remainder; the 2017 2-YEAR Kallas special's seat also expires Jan-2020).
- 2017 elected exactly two cohort-B members: **Jackson (744) and Aston (708)**. Aston's
  continuous service is triple-attested — present as a sitting member at the 2020-01-06 oath,
  voting 2020-04-08..2021-12-08, and her own 2026 *"this is her third swearing in"* (=
  2018/2022/2026). So the vacated seat **must be Jackson's**. Jackson has zero votes, zero
  role rows, and zero minutes presence post-floor.
- The forward arithmetic also checks: Crockett's 2021 RCV win must be the **full 2022-2025
  term** — her service ends at the 2026-01-05 oath (last council vote 2025-10-08, last RDA
  2025-12-10) and she was **not** a 2023 candidate — so her 2019 win cannot have been a
  4-year term. **Attempted alternative** (Aston vacated; Aston reappointed to Jackson's seat;
  the special was a 6th seat) each contradict a primary source (Aston's 2020 present-list
  seat, both 2017 wins, the 5-member roll cap and the exactly-5 2020 roster:
  Kallas/Gaston/Hales/Crockett/Aston). The chain is forced. The un-rostered Jackson departure
  date is an honest pre-floor gap, correctly documented and never guessed.

---

## FINDINGS

### F1 — The 2019 election_results defect is BROADER than the roster flags — **SCOPE NOTE for the queued elections review (roster itself unaffected)**

The roster flags only *"Mark R. Hales … is mis-flagged `is_winner=False`"*. The proof above
shows the root cause is **`n_seats=2` hand-set in `clean_elections.py` `N_SEATS`** for the
2019 4-YEAR contest, which poisons every derived field, not just `is_winner`:

- `bluffdale_races.csv` 2019 general: `n_seats=2`; `runner_up=MARK R. HALES` (he was the
  **last winner**, so runner_up should be Preece 932); `margin_votes=10` (last-seat cutoff
  should be 1,044−932 = **112**); the `note` slate omits Hales.
- `bluffdale_races.csv` 2019 primary: `note="top 4 advance"` (should be top 6 — and 5
  candidates reached the general, already contradicting a 2-seat read).
- `election_results/CLAUDE.md` **contradicts itself**: its cycle table says council-only
  years (incl. 2019) elect **3 seats**, while its verification section repeats the wrong
  *"2019 4-yr margin 10 (Kallas/Gaston over Hales)"*.
- The defect is federated into `cities.db` `election_race`/`election_result` for the 2019
  Bluffdale 4-YEAR contest.

The roster row for Hales is UNAFFECTED (minutes-anchored `high`, correct) and the roster
rightly never edits the elections dataset. **Action:** the queued `election_results` review
should fix `N_SEATS[2019 …]=3` and regenerate (races + by_candidate + by_precinct +
re-federate), not just flip one `is_winner` bit. The **ballots-cast ceiling test**
(Σ candidate votes ≤ n_seats × ballots cast, citywide and per-precinct) should go into the
elections validator — it catches this class automatically.

### F2 — "TIE-BREAKS" slightly over-describes Hall's 2025-05-14 council vote — **NIT (wording; inference unaffected)**

The roster note (and `build_roster.py` docstring + `roster/CLAUDE.md`) call both of Hall's
`body='Council'` rows *"her mayoral TIE-BREAKS."* Ground truth: **2022-11-09** is a genuine
tie-break (roll: Kallas/Gaston Aye, Crockett/Hales Nay = 2-2; Hall Aye → *"The motion passed
3-to-2"*). But **2025-05-14** (appoint Bruce Kartchner as City Manager) was **already
passing 3-2** before her vote — the minutes print a full 6-name roll ending *"…Council
Member Aston-Yes, **Mayor Hall-Yes**. The motion passed 4-to-2."* That is a **recorded
mayoral vote in a non-tie**, exactly why the city CLAUDE.md hedges *"tie-break/recorded
event."* The roster's material inference — mayoral participation, NOT council membership —
holds identically either way. Recommended: align the note's wording with the city
CLAUDE.md's ("tie-break/recorded mayoral vote").

### F3 — Aston's 2022 tenure `start_event='elected'` should be `reelected` — **MINOR (labeling inconsistency, no functional impact)**

Aston was a sitting incumbent re-elected in 2021, exactly like Crockett — whose 2022 row
says `start_event=reelected` — and like Aston's own 2026 row (`reelected`). The 2022 Aston
row alone says `elected`. No downstream effect (the config's `elected_events` tuple includes
both, so all crosschecks behave identically), but the inconsistency would mislead a consumer
counting `reelected` events. Fix in the driver's `TENURES` (one word) and regenerate.

*(No other findings. Specifically hunted for and did NOT find: vote-bound smears, an
8th-voter extraction artifact — the corpus' one 6-voter roll is faithful to the minutes, see
F2 — phantom tenures for Hall/Timothy council rows, an unrostered appointee, a disappeared
member (all four serving members' last votes are at/near the 2026-06-24 corpus edge; Lord's
2026-06-10 is one missed meeting, not a departure signal), or a mis-chained seam.)*

---

## Confidence-calibration summary

| Row(s) | Current | Should be | Why |
|---|---|---|---|
| Aston 2018-01-01 (AL-B1 t1) | medium | medium (OK) | pre-floor start, cycle-inferred; win is fact; honestly the weakest-link grade |
| Timothy 2018-01-01 (MAYOR t1) | medium | medium (OK) | same pre-floor class; "12 years" tribute is corroboration, not an oath record |
| Hales 2020-01-06 (AL-A3) | high | high (OK) | minutes-anchored oath (quoted verbatim ×3 in the file) + 352 votes over exactly the term + the ballots-cast proof; the conflicting `is_winner` bit is the *elections file's* defect, not doubt about the tenure |
| All other 12 `high` rows | high | high (OK) | each anchored to an in-data election win AND a quoted oath ceremony |

No `high` row is inference-only; no `medium` row is strong enough to promote (both hinge on
pre-floor start dates no on-disk source attests). The `end_event=unknown` convention
(Kallas, Gaston, Crockett-t2, Timothy) is correctly honest — the end *dates* are the
documented successor oaths; only retire-vs-decline is unstated.

---

## Hardening notes (for `scripts/roster_HARDENING.md`)

1. **Ballots-cast ceiling validator (elections layer, would have caught F1's root cause
   automatically).** For every multi-seat race: FAIL if Σ candidate votes > n_seats ×
   ballots_cast (citywide and per-precinct, where the SOVC carries a ballots sheet — the
   2019 workbook does). `n_seats` values in `N_SEATS` tables are curated, not source-printed;
   this is the cheap arithmetic that audits them.
2. **Hales-class documented exception for the reverse crosscheck.** Bluffdale adds a new
   fleet pattern: a **minutes-anchored tenure contradicted by an in-data `is_winner=False`
   row** (the forward check is silent — he's not a marked winner — and the reverse check
   flags him). When the bidirectional crosscheck is promoted into `roster_lib.validate()`
   (existing backlog item), it needs a per-city documented-exceptions list (like SLC's
   expected `unmapped winner` warnings) so a known upstream defect doesn't force either a
   fake winner bit or a suppressed check.
3. **Roll-size sentinel needs a "recorded mayoral participation" allowlist.** Unlike SLC's
   Mano 2026-03-24 (a genuine extraction artifact), Bluffdale's one over-size council roll
   (2025-05-14, 6 voters) is **faithful to the minutes** ("Mayor Hall-Yes"). The sentinel,
   when promoted into the lib, should distinguish minutes-verbatim mayoral votes from
   artifacts rather than assuming every over-roll is a pipeline bug.

---

*END OF AUDIT — 2026-07-12. Read-only pass: no roster CSV, driver, `roster_lib.py`, or
elections file was modified (the `--check` rebuild was verified byte-identical). Recommended
fixes: F1 via the queued `election_results` review (N_SEATS + regenerate + re-federate);
F2/F3 via one-word edits to the driver's `TENURES`/notes + regenerate, per cardinal rule 2.*
