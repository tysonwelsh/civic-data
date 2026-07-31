# VERIFICATION — Cottonwood Heights City Council data repository

Independent QA of the built repo, performed 2026-07-12 (combined verification / documentation /
audit closeout). Method: reconcile every doubly-stored fact, ground-truth random meetings against
source text, verify the structural ceilings, and cross-check election winners against an outside
source. **No canonical CSV, minutes file, or extractor was modified.** Companion graded audit:
`_audits/audit_2026-07-12.md`.

`scripts/validate_city.py cottonwood_heights_city_council` = **24 PASS / 0 FAIL** (the WARNs it
emitted were the missing README/CLAUDE/SCHEMA docs, now written).

---

## Part A — per-dataset verdicts

| Dataset | Verdict | Evidence |
|---|---|---|
| Council + CDRA minutes | ✅ PASS | 181 md == 181 `minutes_index.csv` rows; 180 pdf-text + 1 docx-text; 0 read errors; screener 0 outliers |
| Council + CDRA votes | ✅ PASS | 3,237 rows / 1,145 motions; 2,658 named; max roll = 5 (0 motions >5); validate_votes reconciles bar 3 documented clerk errors |
| PC minutes | ✅ PASS | 62 md == 62 index rows; 61 pdf-text + 1 docx-text; screener 0 outliers |
| PC votes | ✅ PASS | 688 rows / 257 motions; 513 named; named-inline rolls verified |
| db (`db/civic.db`) | ✅ PASS | 3,171 db votes == 3,171 named CSV rows (0 drops); 1,410 motions == distinct (source,motion_no) |
| public_comments | ✅ PASS (honest-empty) | header-only CSV by design; AVAILABILITY.md documents SUBMIT-ONLY |
| election_results | ✅ PASS | 28 races 2009–2025; winners match outside sources (§A5) |
| geo | ✅ PASS | official 4-district polygons; `--latlon` City-Hall point → District 3 |
| weeks/ | ✅ PASS | 163 bundles; summed vote rows 3,237 == council flat total; minutes LINKED (0 copied minutes/ dirs) |

### A1 — three-way reconciliation (all_votes ↔ minutes_index ↔ votes JSON), both bodies
- **Council:** `all_votes.csv` = 3,237 rows across 1,145 distinct `(date, motion_no)`; every
  vote row's `source` file resolves to a `minutes_index.csv` path; per-meeting JSON exists under
  `votes/<year>/` for every voting meeting; `votes/_validation_report.txt` present.
- **PC:** `all_votes.csv` = 688 rows / 257 motions; 62 index docs; JSON present per meeting.
- **db reconciliation (exact):** db `vote` = **3,171** = 2,658 named council rows + 513 named PC
  rows — **0 dropped, 0 overrides**. db `motion` = **1,410** = distinct `(source_file,
  motion_no)` (Council 1,083 + CDRA 70 + PC 257). db `meeting` = 269 (Council 172 + CDRA 41 + PC
  56). **weeks/** summed vote rows = **3,237** = the council `all_votes.csv` total; **0**
  `weeks/*/minutes/` directories (bundles LINK the canonical minutes via relative path in
  `summary.md`, not copy).

### A2 — mayor-votes max-5 ceiling + Holton appointment timing
- **Ceiling holds.** Named-member count per council motion is **{3: 21, 4: 170, 5: 378}** — the
  maximum is **5** (4 districts + Mayor); **0 motions have >5 named members**. Confirmed against a
  real full roll (2023-08-15, Resolution 2023-44): *"Council Member Holton-Aye; Council Member
  Bracken-Aye; Council Member Newell-Aye; Council Member Birrell-Aye; Mayor Weichers-Aye. The
  motion passed unanimously."* — the Mayor is the 5th voter. Mayors appear as voting members in
  **533** rows (Peterson 168 + Weichers 310 + Bennion 55).
- **Holton appointment timing confirmed.** In the vote record **Matt Holton's first vote is
  2023-05-16** and **Douglas Petersen's last vote is 2023-04-04** — the District 1 vacancy fill.
  Corroborated externally: the *Cottonwood Heights Journal* reported "Matthew Holton sworn-in as
  new Cottonwood Heights City councilmember" (2023-06-01); Holton then won the Nov 2023 D1 general
  (§A5). The April→May handoff is a genuine roster seam, not missing data.

### A3 — the three faithful source clerk errors (spot-checked at source)
1. **2023-11-21, Ordinance 405** — source minutes (line 658–659): *"Vote on Motion: Council
   Member Holton-Aye, Council Member Newell-Aye, Council Member Birrell-Nay, and Mayor Pro Temp
   Bracken-Aye. The motion passed 4-to-1."* Only **4 members** are named (3 Aye + 1 Nay) yet the
   clerk wrote "4-to-1" (a 5-vote tally). The extractor recorded the 4 real votes; the verbatim
   `result` "passed 4-to-1" is retained. **Faithful.**
2–3. **2026-05-19, Ordinance 464 (m2 TABLE + m3 APPROVE)** — source (line 2150–2152): *"Vote on
   Motion: Council Member Birrell-Yes; Council Member Newell-No; Council Member Hyland-No;
   **Council Member Highland-No**; Council Member Holton-No; Mayor Bennion-Yes. The motion failed
   4-to-2."* The clerk **duplicated "Hyland" as a phantom "Highland,"** producing 6 named voters.
   `all_votes.csv` records exactly the **5 real members** (Birrell-Aye, Bennion-Aye, Newell-Nay,
   Hyland-Nay, Holton-Nay) — **the phantom was dropped, roll stays ≤5** — while the verbatim
   "failed 4-to-2" is retained. **Faithful; ceiling preserved.**

### A4 — random ground-truth (6 unflagged meetings, both bodies, incl. CDRA + PMN-backfill)
Every sampled motion matched its source minutes verbatim (names, Aye/Nay, result):
- **2020-10-20** (council, CDRA-tagged) — CDRA in-session block; "Board Member Bracken moved…"
  motions tagged `body=CDRA`; matches.
- **2021-03-02** (council, **PMN-backfilled**, `source=pmn`, `utah.gov/pmn/files/715045.pdf`) —
  source shows "Adjourn to CDRA Meeting… Chairman Mike Peterson, Board Member…" in-session CDRA;
  extraction matches.
- **2023-08-15** (council, **.docx-sourced**) — full 5-member rolls + a CDRA block; the .docx
  converted cleanly; Resolutions 2023-44/45 unanimous 5-member rolls match.
- **2024-09-10** (council, contested) — source: "…Mayor Weichers-Nay. The motion failed by a
  vote of 4-to-1." matches recorded Failed 4-to-1.
- **2024-01-02** (council, contested Res 2024-03) — recorded m4 Failed 3-to-2 / m5 Passed 4-to-1
  matches validate_votes cross-check.
- **2022-08-03** (PC, contested) — named-inline roll "Commissioner Steinman-Aye; Anderson-Aye;
  Chappell-Aye…" matches.

### A5 — election winners vs OUTSIDE sources (browser-UA / web)
| Race | Repo (`cottonwood_heights_races.csv`) | Outside source | Match |
|---|---|---|---|
| 2025 Mayor | **GAY LYNN BENNION** 6,180 (57.52%) def. Mike Weichers 4,565 | KSL/Utah News Dispatch: Bennion def. Weichers **56–44**, Weichers conceded | ✅ (Weichers→Bennion turnover) |
| 2023 D1 | **MATT HOLTON** 1,175 (56.52%) def. Jen Cottam 904 | *Cottonwood Heights Journal* / SLCo canvass: Holton 1,175 (56.52%) | ✅ exact |
| 2023 D2 | **SUZANNE HYLAND** 964 (51.80%) def. Sharon Daurelle 897 | *CH Journal*: Hyland 964 (51.80%) | ✅ exact |
| 2021 Mayor | **MIKE WEICHERS** 3,526 (38.11%) | Ballotpedia / KSL: Weichers elected mayor 2021 | ✅ |
| 2021 D3/D4 | Newell (D3) / Birrell (D4) | seated 2022; match the vote record roster | ✅ |

Recoveries verified present and note-flagged: **2011** & **2019** district generals (SOVC sheets
keyed `Cottonwood Hts Council N` / `COT Council N`) and the **2021** de-suppressed general.
Minor observation (not a defect): rcvis.com lists a 2025 CH mayor RCV visualization, but the SOVC
records `plurality` and Bennion won a first-choice majority (57.52%), so the winner is unambiguous
either way.

---

## Overall — SHIP
Every built dataset PASSes independently; all doubly-stored facts reconcile exactly; the
mayor-votes max-5 ceiling and the Holton appointment timing are confirmed; election winners match
outside sources. The only source anomalies (3 clerk-error tallies) are correctly retained
verbatim per the cardinal rules. No blocking issues.

### Addenda
_Extend this section with a dated note whenever the data is repaired or re-audited._

#### 2026-07-16 — pmn_backfill promotion into planning_commission/ (16 docs)
The 16 docs recovered by the 2026-07-13 PMN all-body sweep (`pmn_backfill/`) were promoted
into the audited PC layer: **15 Administrative Hearing sessions 2020-03-11 → 2023-03-01**
(PMN body 3287; extends the existing `slug=administrative-hearing` convention backward — the
dataset previously held only 2021-10-06 + 2024+) and the **2022-07-06 PC doc** (PMN body
2148 — ONE combined PDF holding the 5:00 pm Work Meeting and the 6:00 pm Business Meeting,
"Approved: August 3, 2022"). Verification performed:
- **Date/body verified in-body for all 16** (labels not trusted). One header anomaly: the
  2023-03-01 doc's in-body header prints "Wednesday, March 1, **2022**" — a clerk year typo;
  the footer ("APPROVED Cottonwood Heights Administrative Hearing – 03/01/23"), the
  CUP-23-xxx case numbers, and the weekday check (2023-03-01 is the Wednesday; 2022-03-01
  was a Tuesday) prove 2023-03-01. Text retained verbatim.
- **Draft screen: none are drafts.** 11 carry explicit approval evidence (10 "Approved"
  filenames — several also with in-body "Approved: <date>" stamps — plus 2021-03-17, plain
  filename but in-body stamp "Approved: March 23, 2021"); the remaining 5 (2020-03-11,
  2021-04-07, 2021-12-15, 2022-02-09, 2022-05-18) show no draft/pending markings anywhere
  and are the city's official PMN-published record — promoted with that caveat noted.
- **Dedup: 0 collisions** — no (date, slug) overlaps with the existing 78-doc index
  (2022-07-06 had no PC doc of any kind; the 2021-10-06 admin hearing already in the audited
  layer was correctly NOT in the recover set); raw PDFs copied sha256-verified; md bodies
  byte-identical to the pdftotext sidecars.
- **Extraction: +6 motions / +12 vote rows, all from 2022-07-06**, tagged
  **`provenance=pmn_minutes`** (documented trailing 14th column in
  `planning_commission/all_votes.csv`, flowing into `db/civic.db` `motion.provenance`).
  The 15 admin hearings are legitimate 0-motion officer-decision minutes (the hearing
  officer "moves to APPROVE/CONTINUE" with no roll call or printed result — matching the
  audited 2021-10-06/2024+ convention).
- **Additive-only diff proven** at (source, date, body, motion_no, member, vote): 688 → 700
  rows, 0 removed, 0 changed. Council dataset untouched (13-col, byte-identical
  motions_std). db reconciles exactly (3,154 named CSV rows == 3,154 db votes; 1,408
  motions); contested count unchanged (64); referral layer unchanged (0 links, honest
  empty). `validate_city.py`: 25 PASS / 1 WARN (the documented provenance extension) /
  0 FAIL.
- **Ground-truth spot-checks**: all 6 new motions of 2022-07-06 verified verbatim vs source
  (movers/seconders/results; m2 & m3 named 4-0 rolls: Anderson, Mills, Ebbeler, Allen —
  match); 3 admin-hearing sessions (2020-06-17, 2022-10-12, 2023-03-01) verified as
  0-motion with correct dates/officer. Known minor extraction limit: the m2 seconder is
  blank because a pleading-line-number bleed splits "Commissioner 7 Ebbeler seconded" —
  the motion text retains the bleed verbatim (consistent with the audited corpus's
  handling; source says Ebbeler seconded).
