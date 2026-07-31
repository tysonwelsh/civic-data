# Verification — South Jordan City Council data repo

**Verification date:** 2026-07-06
**Agent:** Independent Phase-5 verification (did not build the data; re-checked adversarially).
**External sources cross-checked:** utah.gov PMN certified-results files, South Jordan City
Board of Canvassers minutes, South Jordan Journal, Deseret News 2019 municipal results,
Salt Lake County / electionresults.utah.gov.
**Conformance:** `scripts/validate_city.py` → **19 PASS / 3 WARN / 0 FAIL**.

## Summary table

| Dataset | Status | Rows | Coverage | Notes |
|---|---|---|---|---|
| Council minutes | **PASS** | 243 md = 243 index; 244 raw PDF (1 documented mis-upload) | 2020-08 → 2026 | 2020 Jan–Jul gap logged honestly |
| Council votes | **PASS** | 1448 vote rows / 1029 motions | 2020–2026 | tie-break + 2 clerk errors faithful |
| PC minutes | **PASS** | 125 md = 125 index = 125 raw PDF | 2020 → 2026 | 3 un-minuted 2020 meetings logged |
| PC votes | **PASS** | 797 vote rows / 730 motions | 2020–2026 | names dissenters/absentees only (source style) |
| Elections | **PASS** | 41 race rows (30 general + 11 primary) | 2007–2025 | all sampled winners match outside sources |
| Public comments | **PASS** (honest empty) | 0 (AVAILABILITY.md) | n/a | submit-only, not published — documented |
| Geo (address→district) | **PASS** | 5 district polygons | current | tool + geojson present |
| db (south_jordan.db) | **PASS** | 1110 votes / 1759 motions | — | reconciles exactly to CSVs |
| weeks/ | **PASS** | 128 week bundles | 2020–2026 | fresh; sums to flat totals |

## Reconciliation (independently measured, not trusted from reports)

- **Council minutes:** 243 markdown = 243 `minutes_index.csv` rows. **244 raw PDFs**; exactly
  **1 orphan** (`civicplus_ADID-232.pdf`) — the **documented mis-upload**: CivicPlus ADID-232
  served the *Study* minutes in the *Regular* slot for 2021-10-19; the true regular minutes
  were recovered via PMN (`utah.gov/pmn/files/784439.pdf`) and the index title states this
  verbatim. Orphan retained in `raw/`, not indexed. **Reconciles.** Matches build claim
  (243 md / 244 raw / 1 mis-upload).
- **PC minutes:** 125 markdown = 125 index rows = 125 raw PDFs. **Reconciles** (claim: 125).
- **db vote rows:** measured 1110 = council 757 named + PC 353 named CSV rows; validator
  independently confirms db votes 1110 == CSV named 1110 (delta 0). **Reconciles** (claim: 1110).
- **weeks:** 128 week directories on disk. **Reconciles** (claim: 128). Validator confirms
  weekly votes sum 1448 == flat total and weeks/ not stale.
- No stub/header-only markdown (smallest council md ≈1191 B; no files < 400 B).

## No fabrication / no duplication

- **Zero true duplicate `(source, motion_no, member)` rows** in either body. (A naive
  `(date, motion_no, member)` key shows 50 council collisions — all false positives from
  same-date Study + Regular meetings legitimately reusing motion numbers; disjoint once
  keyed on source document.)
- **Unanimous narrative motions carry NO invented Aye names** (member/vote blank) —
  confirmed correct. 2020–2023 contested motions name only the dissenter (AYE=[]), which is
  the source's dissenter-only style, not a parse loss.
- **Off-roster names: 0** in both bodies (PC + council validators). Vote roster =
  Harris, Johnson, Shelton, Zander, McGuire, Marlor (+ Ramsey on the single flagged
  tie-break) — all real, election-confirmed members.

### Motion trace-checks (6 sampled, each traced to source text)

| # | Body | Motion | Source text confirmed |
|---|---|---|---|
| 1 | Council 2020-08-18 m1 | McGuire approve minutes | "McGuire made a motion to approve the July 24, 2020 Emergency City…" ✓ |
| 2 | Council 2025-06-17 m9 | Ord 2025-09 tie-break 3-2 | verbatim roll call incl. "Mayor Dawn R. Ramsey - Yes … passed with a vote of 3-2" ✓ |
| 3 | Council 2023-05-16 m3 | R2023-19 (2-3 Fail) | "Marlor motioned to approve Resolution R2023-19 …"; "2-3" present ✓ |
| 4 | PC 2022-10-11 m3 | 3-3 clerk-error item | "3-3, with no votes made by Commissioner Bevans, Chair Hollist, and…" ✓ |
| 5 | PC 2025-05-27 m8 | 6-1 Bevans No | "6-1 with Commissioner Bevans voting No." ✓ |
| 6 | PC 2020-11-10 m5 | 4-1 Catmull No | "4-1 Commissioner Catmull Voted No" ✓ |

## Tally-vs-result consistency

- **Mayoral tie-break 2025-06-17 (Ordinance 2025-09, 3-2) — STORED FAITHFULLY.** Source roll
  call: Shelton/Johnson Yes, Harris/McGuire No, Zander Absent, **Mayor Ramsey Yes** → the mayor
  broke a 2-2 council tie for a 3-2 pass. CSV records all six voters incl. `Dawn R. Ramsey | Aye`;
  flagged in the validation report as the single mayor-vote / 6th-voter event (Ramsey otherwise
  non-voting, as recon predicted).
- **Council clerk error 2025-08-19 m7 — RETAINED VERBATIM + FLAGGED.** `result` = "4-1 Pass"
  (city-verbatim) but only 3 Aye + 1 Nay named with 4 seated. Not silently corrected;
  surfaced in the validation report's tally-mismatch + roster-size sections.
- **PC clerk error 2022-10-11 (m3 "3-3…", m4 "4-0, no votes made by…") — RETAINED VERBATIM +
  FLAGGED.** Contradictory tally/name text preserved as the native `result` string; the PC
  validator flags the m4 named-nay-vs-tally mismatch. Not smoothed over.
- Sampled contested motions' named dissenters match the losing side of the tally where the
  source names them (2024-12-03 onward full roll calls sum exactly; earlier dissenter-only
  motions carry only the named No, by source design).

## Date coverage vs the 2020 floor

- **2020 Jan–Jul council gap is honestly logged**, not silently missing:
  `meeting_minutes/minutes_unrecovered.csv` records the Jan–Jul 2020 span (no portal retains
  pre-Aug-2020 SJ council minutes; CivicPlus starts 2021, Municode 2022, PMN 2020-08-04) plus
  the 2020-08-04 meeting (agenda/packet only, minutes never posted). Coverage begins 2020-08-18.
- **PC 2020:** three early-COVID electronic meetings (2020-04-14, 2020-04-28, 2020-08-11) noticed
  on PMN with no published minutes — logged in `planning_commission/minutes_unrecovered.csv`.

## External election cross-check (race-by-race)

| Race | File value | Outside source | Result |
|---|---|---|---|
| **2021 Mayor** (recovered) | Ramsey 11,951 / 91.64%; Fonua 1,090 | utah.gov PMN 784387 quotes "DAWN R RAMSEY 11,951 91.64% STONE FONUA 1,090 8.36%"; South Jordan Journal | **MATCH (exact)** |
| **2025 Council Dist 3** | Shelton 1,753 (50.65%) vs Lewis 1,708; margin 45; total 3,461 | SJC Board of Canvassers minutes + electionresults.utah.gov: Shelton 1,753 / Lewis 1,708 / 45-vote margin | **MATCH (exact)** |
| **2023 Council Dist 2** | Johnson 2,230 (61.7%) over Bevans 1,384 | South Jordan Journal ("Johnson returns … District 2") | **MATCH (winner)** |
| **2019 Council Dist 2** (recovered) | Marlor 1,161 (60.31%) over Quinn 764 | Deseret News 2019: Marlor def. Quinn | **MATCH (winner)**; counts differ (Deseret = election-night unofficial 861/548 vs file = final canvass) — expected, not a discrepancy |
| **2019 Dist 1 / Dist 4** (recovered) | Harris 1,501 unopposed; Zander 935 unopposed | Deseret News: Harris & Zander won unopposed | **MATCH (winners + unopposed status)** |

- **Roster consistency:** the members implied by the elections (Harris D1, Johnson/Marlor D2,
  Shelton D3, Zander D4, McGuire D5, Ramsey Mayor) match those casting votes in `all_votes.csv`
  after name normalization — including the Marlor→Johnson D2 handoff (Marlor votes 2020–2023,
  Johnson from 2024, matching the 2023 election).

## Conformance: validate_city.py — 19 PASS / 3 WARN / 0 FAIL

Every WARN maps to a documented quirk:

1. **`a.layout` — missing optional `all_comments_clean.csv`, `README.md`, `VERIFICATION.md`.**
   - `all_comments_clean.csv`: **legitimate** — comments are submit-only/not-published;
     `public_comments/AVAILABILITY.md` documents the exhaustive hunt and the honest empty verdict.
   - `VERIFICATION.md`: created by this run (resolves).
   - `README.md`: **genuinely absent** — see Gaps below.
2. **`f.tally[meeting_minutes]` 101/234 (43.2%).** Narrative-tally style: 2020–2023 minutes name
   only the dissenter (not the full Aye roster), so the *named* subset cannot sum to the printed
   tally; 2024+ full roll calls do match. The body's own `validate_votes.py` finds exactly **1**
   real tally mismatch (the documented 2025-08-19 clerk error). WARN is the documented source style.
3. **`f.tally[planning_commission]` 0/205 (0.0%).** PC never prints a full Aye/Nay roster — only
   absentees/dissenters — so 0% full-roster matches by design. PC `validate_votes.py` finds exactly
   **1** real mismatch (the documented 2022-10-11 clerk error). WARN is the documented source style.

Other validator checks all PASS: 13-column schema, vote vocabulary, index paths exist, source
refs resolve, motions_std contract (council 1029 / PC 730), db reconciliation (1110==1110),
weeks freshness + sum. `db/`, `geo/` (5 district polygons), db views
(`v_project_timeline`, `v_member_record`, `v_contested`, `v_referral_chain`) all present.

## Gaps & recommendations (documentation only — no data-integrity issues)

1. **`README.md` is absent** at repo root (validator WARN). Recommend adding the standard
   repo README.
2. **`meeting_minutes/CLAUDE.md` is absent** (planning_commission, election_results, geo each
   have one; db has SCHEMA.md). The council minutes dataset should carry its own CLAUDE.md
   documenting the narrative-tally style, the mayor-vote/tie-break rule, and the ADID-232
   mis-upload. Minor doc gap.
3. **PC `validate_votes.py` prints to stdout but does not write `votes/_validation_report.txt`**
   (the council script does). Cosmetic; the PC validator runs and is clean apart from the one
   documented clerk error. Recommend having it persist its report for parity.

None of the above affects data faithfulness. **All datasets verified PASS.** No fabrication,
no silent gaps, no unfaithful values found; the tie-break and both clerk errors are stored
verbatim and flagged; every sampled election winner matches an independent outside source.
