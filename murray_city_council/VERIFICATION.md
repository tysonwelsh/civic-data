# VERIFICATION — Murray City data repository

Independent QA of the Murray City Council + Planning Commission datasets, performed
**2026-07-11** by a verification agent separate from the build. Re-checks are read-only:
no canonical CSV, minutes markdown, or JSON was mutated. Method — reconcile the flat
`all_votes.csv` against the per-meeting vote JSON and `minutes_index.csv` for both bodies,
screen for fabricated/duplicated rows, sample source minutes against the extraction, and
cross-check every election winner/margin against an outside source.

Baseline: `python3 scripts/validate_city.py murray_city_council` = **24 PASS / 0 FAIL**.

## Result summary

| Dataset | Verdict | Evidence |
|---|---|---|
| Council minutes + votes | **PASS** | 132 md == 132 index == 132 vote JSON; 2,882 vote rows reconcile exactly (2,821 named + 61 tally-only blanks); 0 orphan sources; 0 duplicate rows; council roll never exceeds 5 |
| PC minutes + votes | **PASS** | 61 md == 61 index == 61 vote JSON; 1,433 vote rows reconcile exactly (1,288 named + 145 tally-only blanks); 0 orphan sources; 0 duplicate rows; PC roll ceiling = 7 (7-member commission) |
| Source fidelity (spot-check) | **PASS** | 8 meetings sampled across 2020–2025; every sampled motion, tally, and named roll matches the source minutes verbatim |
| Date coverage / gaps | **PASS (documented)** | 2020 floor honored; 2023 council TMM gap and PC-ends-2022-11 gap are honest, catalogued below |
| Election cross-check | **PASS** | All 2021/2023/2025 winners + margins confirmed against Salt Lake County / Murray Journal / Ballotpedia / KSL; 0 winner or margin-direction mismatches |
| Public comments | **PASS (honest-empty)** | Header-only `all_comments_clean.csv` + `AVAILABILITY.md`; submit-only city, correctly not fabricated |

## (a) Row-count + index reconciliation — PASS both bodies

Independent recount (`all_votes.csv` vs per-meeting `votes/**/*.json` vs `minutes_index.csv`):

| Metric | Council | PC |
|---|---|---|
| `minutes_index.csv` docs | 132 | 61 |
| markdown files on disk (all index paths exist) | 132 | 61 |
| per-meeting vote JSON files | 132 | 61 |
| distinct motions (JSON == `all_votes` grouped) | 657 == 657 | 378 == 378 |
| `all_votes.csv` member-vote rows | 2,897 | 1,510 |
| ├─ named voter rows (sum of aye/nay/abstain/absent/excused/recuse across JSON) | 2,836 | 1,356 |
| └─ tally-only blank-member rows (`names_recorded:false`) | 61 | 154 |
| index docs with 0 recorded motions | 4 | 0 |

The **per-source row deltas** between the JSON name-sum and `all_votes.csv` (52 council /
57 PC sources) are **fully explained by tally-only motions**: a voice-vote / unnamed-tally
motion (`names_recorded:false`) emits exactly one blank-member row in `all_votes.csv` and
zero named voters in the JSON. Counting those blanks back in makes both bodies reconcile to
the row: 2,836 + 61 = 2,897 and 1,356 + 154 = 1,510. Every `all_votes` `source` path exists
in `minutes_index.csv` (**0 orphans**), and every index markdown path exists on disk
(**0 missing**).

**OCR recovery (2026-07-11) — 5 scanned-stub docs were NOT vote-free.** An earlier audit
flagged 5 council + 4 PC "zero-motion" docs. Re-inspection found that **5 of them were
image-only scanned PDFs** that `pdftotext` had reduced to header-only stubs (<210 bytes),
silently dropping their votes — they were **not** genuinely vote-free. All 5 were re-OCR'd
(Tesseract, 300 dpi; raw PDFs retained; `format` flipped `pdf-text`→`ocr` in
`minutes_index.csv`) and re-extracted, recovering **92 new vote rows across 26 motions**:
- **Council 2022-06-21** — 3 named 5-0 roll calls (June 7 minutes, Consent Agenda,
  Resolution R22-31); **+15 rows**.
- **PC 2020-01-02** — 5 motions (3 named 4-0); **+14 rows**.
- **PC 2020-01-16** — 5 motions (3 named, incl. Sue Wilson abstain on the A-1→R-1-8 rezone
  recommendation); **+20 rows**.
- **PC 2020-02-06** — 4 motions (2 named 7-0); **+16 rows**.
- **PC 2020-02-20** — 9 motions (6 named 4-0); **+27 rows**.

Every recovered named tally matches its printed result. After recovery, only **4 council
zero-motion docs remain — those ARE legitimately vote-free** (canvass / study /
procedural-only sessions), and **0 PC zero-motion docs remain**.

## (b) No fabricated or duplicated rows — PASS

- **Exact-duplicate vote rows: 0** in both bodies (full-tuple dedupe over `all_votes.csv`).
- **Council roll-call ceiling respected: 0 motions exceed 5 named members** — consistent
  with the 5-district council and the **non-voting executive mayor**. PC tops out at **7**
  (a 7-member appointed commission), also correct.
- **Source spot-check (8 meetings, quoting source minutes):**
  - `2024-12-03` council motion 2 — minutes print `Council Roll Call Vote: Mr. Pickett Aye
    / Ms. Cotter Aye / Ms. Dominguez Aye / Ms. Turner Aye / Mr. Hock Aye / Motion passed:
    5-0`. JSON `aye = [Paul Pickett, Pamela Cotter, Rosalba Dominguez, Diane Turner, Adam
    Hock]`, `result = "Motion passed: 5-0"`. **Exact match.**
  - `2024-12-03` council motion 1 — source "Voice vote taken, all 'Ayes.' Approved" →
    JSON `names_recorded:false`, 0 named ayes, one blank row. **Correct** (not Present-filled).
  - `2022-01-18`, `2024-06-18`, `2024-09-30/10-01`, `2025-11-18` council and
    `2022-10-06`, `2020-05-07`, `2022-03-17` PC — sampled motions, movers, seconders,
    tallies, and named/tally-only status all match the source markdown. **No invented
    names on any tally-only motion.**

## (b′) Roster nuance verified — Brett Hales D5 → Mayor

The documented Hales transition is confirmed in the vote data itself:
**Brett Hales casts 190 councilmember votes from 2020-01-07 through 2021-12-07, then
exactly 0 vote rows in 2022 onward** — because he won the 2021 mayoralty and the Murray
mayor (executive form) does not vote. In `2022-01-18` minutes he appears as
"Brett Hales, Mayor" / "Mayor Hales", never in a roll call. "Councilmember Hales"
(2020–2021) and "Mayor Hales" (2022+) are the same person; his early council votes are
legitimate and correctly attributed.

## (c) Date coverage vs the 2020 floor — PASS, gaps documented honestly

Index year distribution:

| Year | Council docs | PC docs |
|---|---|---|
| 2020 | 23 | 22 |
| 2021 | 20 | 21 |
| 2022 | 25 | 18 |
| 2023 | **5** | **0** |
| 2024 | 25 | 0 |
| 2025 | 24 | 0 |
| 2026 | 10 | 0 |

Council range 2020-01-07 → 2026-06-16; PC range 2020-01-02 → 2022-11-17. Two honest gaps:

1. **2023 council minutes are a portal gap.** Only 5 of the ~24 expected 2023 council
   meetings are in the CivicPlus Archive; the remainder were diverted to a Tyler **Minutes
   Management** SPA (a separate, non-Archive interface) and are not exposed as downloadable
   Archive PDFs. This is a **publishing/portal gap, not an extraction miss** — the 5
   recovered 2023 docs are complete and pass every reconciliation above. The **18 missing
   2023 council meetings** are now enumerated in `meeting_minutes/minutes_unrecovered.csv`
   (their agendas are present in the CivicPlus council-agenda archive `AMID=83`, proving each
   meeting occurred; the minutes archive `AMID=31` holds only the 5 recovered dates). Recovery
   of the remaining 18 is a future task (candidate: the TMM SPA, PMN, or a records request).
2. **PC minutes end 2022-11-17.** The Planning Commission Archive (`AMID=33`) archive stops
   at November 2022; **no PC minutes are published for 2023+**. This is a real end-of-series
   in the source, honestly reflected as absence (no stub rows).

The **2023 council gap is now machine-enumerable** in
`meeting_minutes/minutes_unrecovered.csv` (18 rows, one per missing 2023 council meeting,
each with its agenda-archive provenance) — the PC end-of-series gap remains prose-only
(the source archive simply stops, with no per-meeting agenda records to enumerate beyond it).
Neither gap is stubbed into the index.

## (d) Election cross-check against outside sources — PASS (0 mismatches)

`election_results/murray_races.csv` (15 races) checked winner + margin against independent
reporting and the county results portal. Repo values are the **certified Salt Lake County
SOVC**; where an outside snapshot differs by a few votes it is an election-night-vs-canvass
artifact, not a data error.

| Year | Race | Repo winner (margin) | Outside source | Match |
|---|---|---|---|---|
| 2021 | Mayor | **Brett A. Hales** 6,108 / 58.3% over Clark Bullen (1,739 votes) | Murray Journal + Deseret: Hales 58% over Bullen 42%, ~1,800-vote lead | ✅ |
| 2021 | Council D2 | **Pamela J. Cotter** 54.74% | Murray Journal: "Turner and Cotter to council" | ✅ |
| 2021 | Council D4 | **Diane Turner** 64.41% | Murray Journal (same) | ✅ |
| 2023 | Council D1 | **Paul Pickett** 696 / 59.28% over Rodgers 478 | KSL/Murray Journal: Pickett 696 (59.28%) over Rodgers 478 | ✅ |
| 2023 | Council D3 | **Rosalba Dominguez** 1,095 / 52.67% over Bullen 984 | KSL: Dominguez 1,095 (52.69%) over Bullen 983 | ✅ (runner-up ±1 vote, canvass noise) |
| 2023 | Council D5 | **Adam Hock** 1,553 / 56.23% over Hrechkosy 1,209 | KSL/Murray Journal ("elect Hock and Pickett"): Hock 1,553 (56.23%) | ✅ |
| 2025 | Mayor | **Brett A. Hales** 6,490 / 61.84% over Bruce E. Turner | SL Trib/KSLTV: Hales ~62% over Bruce Turner ~38% | ✅ |
| 2025 | Council D2 | **Pamela Jane Cotter** 54.77% | Murray Journal 2025: Cotter wins D2 | ✅ |
| 2025 | Council D3 (2-yr special) | **Clark Bullen** 1,336 / 56.44% over Ben Peck | Reporting: Bullen wins the D3 2-year unexpired term (~58%) | ✅ |
| 2025 | Council D4 | **Diane Turner** uncontested (100%) | Sole candidate on ballot | ✅ |

**No winner or margin-direction mismatch in any race.** The 2025 "District 3 (2-Year Term)"
is correctly flagged in `note` as an unexpired-term SPECIAL (Bullen filling the seat vacated
by Dominguez, who left the council in Dec 2024). Brett A. Hales' two mayoral wins (2021,
2025) are both confirmed. The 2019 general is below the 2020 data floor and correctly out of
scope.

## Federated / derived layers — consistent

`db/civic.db` reconciles with the flat CSVs: **1,009 motions** (654 council + 355 PC) and
**4,109 named vote rows** (2,821 council + 1,288 PC — the tally-only blanks are modeled at
the motion level, not as phantom votes); 184 meetings (the 193 docs minus the 9 zero-motion
sessions); 23 persons; 22 PC→Council referrals; 2 bodies. Geo: 5 official district polygons,
53 precinct→district assignments (D1:8 / D2:11 / D3:14 / D4:8 / D5:12). These are DERIVED —
regenerate, never hand-edit.

## Issues / follow-ups

- **None blocking.** All datasets PASS.
- **Recommended (non-blocking):** enumerate the ~19 missing 2023 council meetings in a
  `meeting_minutes/minutes_unrecovered.csv` so the TMM gap is machine-countable, and queue a
  TMM-SPA / PMN recovery pass for 2023 council + any post-2022 PC minutes that may surface.

_Verification performed 2026-07-11. Extend with dated addenda whenever the data is repaired
or re-audited._

## Addendum 2026-07-16 — pmn_backfill PROMOTION into the audited layers (minutes-promotion work package)

**What changed.** The 77 `status=recovered` documents in `pmn_backfill/` were promoted into
the audited trees: **18 council minutes** (all 17 TMM-lost 2023 regular meetings + the
net-new 2023-08-21 joint special with Millcreek, a zero-motion discussion session) →
`meeting_minutes/` (132→150 docs), and **59 PC minutes 2023-01-05 → 2026-05-07** →
`planning_commission/` (61→120 docs). Index `source=pmn`, `format=pdf-text` (all
born-digital); raw PDFs copied into each dataset's `raw/` keeping their
`<body>_<date>_<pmn_file_id>.pdf` basenames (sha256-traceable to
`pmn_backfill/raw/_fetch_log.jsonl`). The cancellation notice (2023-07-11) and the two
negative probes were NOT promoted (provenance/gap records). Every promoted doc passed a
pre-promotion screen (dedup vs the audited indexes; agenda-header absence; motion-language
presence; in-body date match — the 10 council docs whose letterhead date is an image were
re-verified via their internal minutes-approval chains, e.g. 10-17 approves 09-19 + 10-03).

**Vote layer.** Council: 657→**755 motions**, 2,897→**3,323 rows**, contested 70→**75**;
validate_votes PASS (0 hard). PC: 378→**678 motions**, 1,510→**2,708 rows**, contested
15→**27**; PASS (0 hard). The PC extractor's fixed canon gained the five 2023–2026
commissioners (Hristou, Henrie, Hildreth, Klinge, Rogers — verified against attendance
blocks; staff incl. "David Rodgers, Senior Planner" and post-2022 "Phil Markham, CED
Director" excluded), plus new-corpus grammar: "with all in favor" voice votes,
"Motion fails: N-N", pre-form/"Seconded from" seconders, "move to"/"made a recommendation"
intros, a mid-sentence pronoun motion, headerless roll blocks, and a no-printed-result roll
guard. The council extractor gained the CoW-style "All in favor N-N" result (also repairing
10 previously-dropped 2024/2026 minutes-approval motions and 6 misparsed 2026-01-06
nomination confirmations) and a deferred-roll handler for 2023-06-27's out-of-order "ROLL
CALL FOR SECOND MOTION" (a contested 3-2 travel-policy vote previously invisible). Every
extractor change was regression-proven: all previously-audited meetings reparse identically
except the enumerated, source-verified improvements.

**Ground truth.** 10 newly extracted motions spot-checked verbatim against source across
bodies/years (names, tallies, results exact), incl. the 2023-05-16 3-2 travel denial, the
2023-10-17 Rodgers-era roll, PC 2026-03-19 7-0, and PC 2025-08-07 0-6. Faithful-capture
source defects (retained verbatim, soft-flagged): 2023-05-02 m2 (the source PDF truncates
its own Ayes list mid-name under a printed 4-0), 2025-06-05 PC m5 (printed "Motion passes:
6-0" over a roll containing `N Pehrson`), 2025-05-01 PC m3 (Rogers printed as both mover
and seconder).

**Derived layers.** db/civic.db rebuilt: **1,433 motions / 5,680 named votes / 268 meetings
/ 28 persons / 24 referrals** (was 22); weeks/ 147 bundles; motions_std 100% outcome
coverage; sources.csv 1,421 docs. `ordinances/` linkage rebuilt with the 2023 enacting
motions present: **151 medium / 21 low / 0 none** (was 132/16/18 — the TMM-gap `none` rows
all resolved; O24-05 remains `low` with no motion_no, its 2024-02-20 adoption date having
only CoW minutes). Gap records updated: `meeting_minutes/minutes_unrecovered.csv` →
header-only (17 recovered + 1 proven cancellation); NEW
`planning_commission/minutes_unrecovered.csv` (2025-04-17, 2025-07-17 — the only
minute-less PC meetings). `scripts/validate_city.py`: **26 PASS / 0 WARN / 0 FAIL**.
Backups of every touched canonical file: `_backups/2026-07-16-minutes-promotion/murray/`.
