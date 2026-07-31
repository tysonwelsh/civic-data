# VERIFICATION — Riverton City civic-data repo

Independent QA of the Riverton City Council + Planning Commission datasets, run 2026-07-12 by
a verification agent that did **not** build the data. Every check below reconciles the doubly
stored facts (flat CSV ↔ minutes_index ↔ per-meeting JSON ↔ `db/civic.db`), spot-checks source
markdown against extracted rows, and cross-checks the election winners/margins against outside
sources (news + county canvass). **Result: PASS on every built dataset, 0 FAIL.** No canonical
CSV or minutes file was mutated by this audit.

`scripts/validate_city.py riverton_city_council` = **23 PASS / 2 WARN / 0 FAIL**. The two WARNs
are expected and documented: (a) the optional docs this file completes (README/CLAUDE/
VERIFICATION), and (b) the one `Aye (Mayor tie-break)` vocabulary extension (see §3).

---

## 1. Council — PASS

| Check | Expected | Observed | Verdict |
|---|---|---|---|
| Meetings on disk == index | — | **128 md == 128 index rows**, all paths exist | ✅ |
| Meetings with votes == index dates | 128 | 128 (0 index dates missing from votes) | ✅ |
| Distinct motions | 851 | **851** | ✅ |
| Vote rows | 3,589 | **3,589** | ✅ |
| Named member rows | — | **3,457** | ✅ |
| Tally-only motions (blank member/vote placeholder) | 132 | **132** (851 − 719 named roll calls) | ✅ |
| Named roll-call motions | 719 | **719** | ✅ |
| Date coverage vs 2020 floor | 2020+ | **2020-02-18 → 2026-06-02** | ✅ |
| `validate_votes.py` | clean | clean (0 off-roster, 0 outcome/count inconsistencies) | ✅ |

The 132 tally-only Council motions are the honest source style (a printed tally with no per-name
roll call), **not** an extraction loss — consistent with SCHEMA_SPEC §4.

## 2. Planning Commission — PASS

| Check | Expected | Observed | Verdict |
|---|---|---|---|
| Meetings on disk == index | — | **119 md == 119 index rows**, all paths exist | ✅ |
| Distinct motions | 672 | **672** | ✅ |
| Vote rows | 1,296 | **1,296** | ✅ |
| Named member rows (divided votes fully attributed) | 127 motions | **127 named-divided motions**, **751 rows** | ✅ |
| Unanimous placeholders (honest unnamed) | 538 | **538** | ✅ |
| Died for lack of a second | 7 | **7** | ✅ |
| Tally-only total (538 + 7) | 545 | **545** | ✅ |
| Date coverage | 2020+ | **2020-01-23 → 2026-06-11** | ✅ |
| `validate_votes.py` | clean | clean | ✅ |

**One index meeting has no motions: `2020-06-09`.** Verified at source — the file
(`planning_commission/minutes/2020/2020-06-08/2020-06-09_planning-commission.md`, 36 lines) is a
**discussion/study meeting with no motions taken** (no "moved"/"seconded"/"vote"/"approve"
language). So 119 index meetings → 118 meetings-with-votes is a **truthful no-action meeting**,
not a dropped meeting. This is the documented PC WARN note.

The **538 unanimous unnamed placeholders** are Riverton's PC convention: the clerk prints a full
named roll call **only on divided votes**, and "unanimous consent" (no names) on unanimous ones.
Blank member lists on unanimous PC motions are the source style, never a parse miss.

## 3. Mayor tie-break — CONFIRMED against source

Riverton uses the **Park City model**: 5 district councilmembers vote; the separately-elected
**Mayor is NON-voting except to break a tie**. The single tie-break in the corpus is verified
verbatim against the source minutes.

**Source** — `meeting_minutes/minutes/2025/2025-12-15/2025-12-16_city-council.md`, motion 3
(Resolution No. 25-62, Removal of the Riverton City Skate Facility):

> "Mayor Staggs called for a roll-call vote. The vote was as follows: **Buroker-no, McCay-no,
> McDougal-yes, and Pierucci-yes. The motion ended in a tie, 2 to 2.**
> Mayor Staggs was called to vote to break the tie and **voted yes. The motion passed.**"

**Extracted `all_votes.csv` rows (2025-12-16, motion 3):**

| member | vote |
|---|---|
| Troy McDougal | Aye |
| Andy Pierucci | Aye |
| Tish Buroker | Nay |
| Tawnee McCay | Nay |
| **Trent Staggs** | **Aye (Mayor tie-break)** |

`result` = `Passed (Mayor tie-break)` (verbatim-style extension). **Exact match** to source:
2 Aye + 2 Nay among councilmembers, Mayor breaks yes. In `db/civic.db` the tie-break vote is
**normalized to `Trent Staggs | Aye`** (verbatim value preserved only in the flat CSV, per the
cardinal rules). Staggs appears in exactly **1** council vote row and **1** role entry — his sole
vote, as expected for a non-voting mayor. ✅

## 4. Roster additions (Stewart D1 / Wells D5) — CONFIRMED voting 2020–2023

The build corrected the extractor to add two 2020–2023 seat-holders the recon roster missed:

| Member | Seat | Roster tenure (`meeting_minutes/roster.csv`) | Vote rows |
|---|---|---|---|
| **Sheldon Stewart** | D1 (→ Pierucci 2023) | 2020-03-17 → 2022-12-13 | 319 |
| **Claude Wells** | D5 (→ Haymond 2024) | 2020-03-17 → 2023-12-06 | 413 |

Both confirmed **actively voting** at source. In
`meeting_minutes/minutes/2021/2021-12-13/2021-12-14_city-council.md` the Work-Session roll call
reads: *"the vote was as follows: **McCay-Yes, McDougal-Yes, Stewart-Yes, and Wells-Yes.** The
motion passed unanimously"* — matching the four named `Aye` rows in `all_votes.csv` for that
motion (Buroker was recorded absent that meeting). Stewart and Wells also mover/second numerous
2020–2022 motions. Their successors resolve cleanly: **Andy Pierucci** (D1) starts 2023-01-03;
**Spencer Haymond** (D5) starts 2024-01-02; and the 2025-elected **Alexander Johnson** (D3) +
**Shannon Smith** (D4) start 2026-01-20. ✅

## 5. db reconciliation — PASS (exact)

`db/civic.db`: **1,523 motions** (Council 851 + PlanningCommission 672), **4,208 votes**
(= 3,457 Council named + 751 PC named CSV rows), 27 persons, 246 meetings, 515 applications,
59 referrals (24 high / 23 medium / 12 low), 130 contested motions. Validator `h.db`:
**"reconciles exactly — CSV named rows 4208 vs db votes 4208 (delta +0)."** Weeks derived layer:
weekly vote sum **3,589 == flat total** (`i.weeks` PASS). ✅

## 6. Random meeting spot-checks (source markdown vs extracted rows)

Eight meetings drawn at random (seeded), both bodies, 2020–2025; each extracted motion/mover/
seconder/roll call cross-read against its source markdown. All matched.

- **Council 2021-12-14** — 7 motions / 25 rows. M1 roll call matches source verbatim
  (McCay/McDougal/Stewart/Wells all Aye; Buroker absent). M3 = Ordinance 21-32, M4 = **deny**
  Ordinance 21-33 Boyer Rezone (a denial recorded faithfully as its own motion). ✅
- **PC 2023-08-10** — 2 motions / 2 rows. M1 = McNeil Auto PLZ-23-8013 site-plan amendment,
  mover Cluff (acting chair, Gilchrist absent) / sec Park — matches source header; unanimous
  → tally-only (PC unnamed-majority convention). ✅
- Also verified without defect: Council 2020-09-01 (9 motions/41 rows), 2024-02-20 (4/16),
  2025-03-04 (10/46); PC 2020-07-09 (2/2), 2020-09-10 (4/8), 2025-10-09 (5/30). ✅

## 7. Election cross-check vs OUTSIDE sources — PASS

`election_results/riverton_races.csv` = 39 races (30 general + 9 primary), 2007–2025. Recent
cycles cross-checked against news + county canvass; all winners/margins agree.

| Cycle | Race | CSV (winner / margin) | Outside source | Verdict |
|---|---|---|---|---|
| **2025** | Mayor | **Tish Buroker 7,687 (70.07%)** def. Tawnee McCay 3,284 | ABC4 / SL Tribune: Buroker ~69–70% over McCay (election-night partial); certified totals higher, same margin | ✅ |
| 2025 | Council D3 | Alexander A. Johnson 1,546 def. Rusty Lance 702 | ABC4 "both council races decided by large margins" | ✅ |
| 2025 | Council D4 | Shannon Smith 1,987 def. Darren J. Park 812 | ABC4 (same) | ✅ |
| **2023** | Council D2 | **Troy McDougal 945** def. David Gatti 902 | KSL / SLCo canvass: McDougal 945 / Gatti 902 | ✅ exact |
| 2023 | Council D5 | Spencer Haymond 1,142 def. Steven Winters 676 | KSL / SLCo canvass: 1,142 / 676 | ✅ exact |
| 2023 | Council D1 | Andy Pierucci 416 (uncontested) | SLCo canvass: Pierucci 416, unopposed | ✅ |
| **2021** | Council D3 | **Tawnee McCay 863** (uncontested, RECOVERED) | Official Riverton certified results (Nov 16 2021): Mayor Staggs, **Council D3 Tawnee McCay**, Council D4 Tish Buroker | ✅ |
| 2021 | Council D4 | Tish Buroker 1,160 (uncontested) | same certified list (D4 Buroker) | ✅ |
| 2021 | Mayor | Trent Staggs 4,973 (uncontested) | same certified list (Mayor Staggs) | ✅ |

**Staggs → Buroker mayoral transition confirmed.** Trent Staggs (councilmember 2013, Mayor
2017 & re-elected 2021) left the mayoralty mid-term to join the federal administration; the 2025
race to replace him was Buroker vs McCay, won by **Buroker**, who took office Jan 2026 (KSL/
Deseret/ABC4). Matches the roster (Staggs 2020–2025 councilmember-then-mayor line; Buroker →
Mayor Jan 2026).

**2021 privacy-suppression recovery verified.** The county long-file suppressed 2021 at the
In-Person/Vote-By-Mail method split (`****`), which read **McCay D3 = 0 votes**. The build's
`parse_2021()` re-parses the raw SOVC's unsuppressed `Total` sub-row → **McCay 863**, matching
the official certified list above. Final CSVs carry **0 suppressed cells** and every by-precinct
sum reconciles to its by-candidate total.

### ⚠ D3 ↔ D4 numbering caveat (carried forward, not a defect)

The **election record labels McCay = D3 and Buroker = D4** (2017 & 2021) — the **opposite** of
`recon.md` and current city GIS, which describe McCay as D4 and Buroker as D3. This is the
**2022 redistricting renumber (Ordinance 22-07)**: the retained **pre-2022** GIS layer
(`geo/districts_pre2022.geojson`, 2019 lines) independently labels **D3 = McCay, D4 = Buroker** —
corroborating the election record — while the **current** layer labels D3 = Johnson, D4 = Smith.
Verbatim election labels are kept as-is; **person↔district joins that cross 2022 must join on
person identity, not the bare district number** (D1/D2/D5 unaffected). Fully documented in
`election_results/CLAUDE.md`. This is a truthful join hazard, correctly surfaced. ✅

---

## Summary

| Dataset | Verdict |
|---|---|
| Council votes (128 mtg / 851 motions / 3,589 rows) | ✅ PASS |
| PC votes (119 mtg / 672 motions / 1,296 rows) | ✅ PASS |
| Mayor tie-break (2025-12-16, Staggs) | ✅ CONFIRMED at source |
| Roster adds (Stewart D1, Wells D5, 2020–2023) | ✅ CONFIRMED voting |
| db/civic.db reconciliation | ✅ PASS (exact, delta 0) |
| Elections (2021 / 2023 / 2025 winners + margins) | ✅ PASS vs outside sources |
| D3↔D4 numbering caveat | ✅ documented (not a defect) |
| Gaps | Only honest: 2020-06-09 PC no-action meeting; comments submit-only (header-only CSV) |

No fabricated data found. No canonical file modified.
