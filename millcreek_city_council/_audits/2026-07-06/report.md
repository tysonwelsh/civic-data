# Audit — Millcreek City Council data repo (independent FINAL GATE)

**Audit date:** 2026-07-06 · **Method:** `/audit-city-data` methodology, run as the independent
Phase-6.3 final gate — adversarial, read-only except the doc-drift addendum noted below. Went
DEEPER than the Phase-5 `VERIFICATION.md` (larger ground-truth sample, corpus-wide collision/
undercapture screens, external election re-confirmation from a different source framing).
**Screeners/validators re-run:** `screen_corpus.py` (both corpora, per-year), `validate_city.py`,
`validate_votes.py` (via validate_city).

## SIGN-OFF: **READY — with one documented data-level finding (2017 roll-call undercapture)**

The repo is internally consistent, reconciles on every doubly-stored fact, and contains **no
fabrication**. One real, bounded, recoverable extraction gap was found (2017 named roll calls
recorded as tally-only) — it is a **safe-direction undercapture, not corruption or invention**, and
does not block sign-off. It is DOCUMENTED here (not silently fixed) as the top remediation item.
One trivial doc-drift (stale placeholder claim in VERIFICATION.md) was fixed via a dated addendum.

---

## 1. Statistical screen (both corpora, per-year)

Both corpora are OCR-heavy but statistically **uniform** — the systematic ~0.73 dict_ratio the
recon warned about is confirmed corpus-wide with **no garbled-year outlier** and **no PUA/mojibake/
stub/duplicate-body pathology**.

**Council (`meeting_minutes/minutes`, 372 files):** dict_ratio median 0.734 (per-year 0.706–0.758);
0 dict_ratio outliers, 0 weird_char outliers, 0 PUA_garbled, 0 mojibake, 0 stub, **0
duplicate_bodies**, 0 read_errors. Benign advisories only: 89/372 `ends_mid` (minutes sit at the
front of combined Agenda+Packet PDFs), 2 replacement_chars, 8 repeated_line, 2 split_word
(both benign — 2025 CRA/special packets).

**PC (`planning_commission/minutes`, 149 files):** dict_ratio median 0.734 (per-year 0.702–0.768);
0 dict_ratio outliers, 0 weird_char outliers, 0 PUA_garbled, 0 mojibake, 0 stub, **0
duplicate_bodies**, 0 read_errors. Benign only: 48/149 `ends_mid`, 1 replacement_char, 23
repeated_line, 2 split_word (both 2017).

Per-year dict medians decline monotonically ~0.77→0.70 (2017→2025) in BOTH bodies — a gradual
scan-quality trend, not a single bad year. No Ogden-style garbled-year hole.

## 2. Ground-truth (13 motion-level checks vs source — deeper than Phase-5's ~8)

All **PASS**, zero fabrication. Covers OCR-scanned, mayor-vote (max tally 5), CRA, tally-only,
named-2022+, contested, and PC — per the required strata.

| # | Motion | Stratum | Source says | CSV | Verdict |
|---|---|---|---|---|---|
| 1 | 2023-08-14 Council m2 | OCR-garbled text, mayor-vote, **contested** | "Catten voted no… DeSirant/Jackson/Uipi/Mayor Silvestrini voted yes" | 4-1, Catten=Nay, 5 named incl. Mayor | PASS |
| 2 | 2023-08-14 Council m1,m3-m5 | mayor-vote | all 5 (incl. Mayor) yes | 5-0, 5 named | PASS |
| 3 | 2020 Council (year) | **tally-only era** | 68× "All Council Members voted yes" (collective) | blank-member "Pass (unanimous)"; only 25 named rows (real exceptions) | PASS — no fabricated names |
| 4 | 2022-04-25 **CRA** (scanned) | CRA + tally-only | "All Board Members present voted yes" | tally-only; Board/Chair = same 5 | PASS |
| 5 | 2023-04-10 CRA m1 | **CRA named**, mayor | "Catten/DeSirant/Jackson/Uipi… and Chair Silvestrini voted yes" (5) | 5 Aye, cap 5, Chair→Silvestrini | PASS — Board/Chair→same people |
| 6 | 2024-03-25 Council (**scanned**) | OCR-scanned, mayor | 4-0 rolls (Catten/Jackson/Uipi/Mayor); DeSirant absent all day | matches; DeSirant never listed | PASS — absentee not invented |
| 7 | 2024-03-25 Council 3-0 sub-rolls | scanned | "Catten… Jackson… and Mayor Silvestrini voted yes" (3, Uipi out) | 3-0, correct 3 | PASS |
| 8 | 2026-05-20 **PC** m1 | PC named + referral | 8 commissioners (LaMar/Anderson/Burgess/Larsen/Reid/Richardson/Soule/Wright) yes | 8 Aye | PASS |
| 9 | 2026-05-20 PC referral text | referral linkage | "Council voted 5-0 on May 5 to recommend approval of the rezone" | present | PASS |
| 10 | 2019-02-20 **PC (ocr)** m7 | OCR PC, **contested** | "Mumford voted no. Claerhout, Stephens, Allen, LaMar voted yes" | 4:1, Mumford=Nay | PASS |
| 11 | 2019-02-20 PC m10/m11 | OCR PC, abstain | "Allen abstained and the other Commissioners voted yes" | Allen=Abstain | PASS |
| 12 | 2019-05-13 Council m1,m6-m8 | **pre-2022 named**, absentee, Marchant-era | "…Catten, and Mayor Silvestrini voted yes. Council Member Uipi was absent" | Jackson/Marchant/Silvestrini/Catten Aye; Uipi absent | PASS — Uipi not fabricated |
| 13 | Distinct voter names | roster | — | Council = exactly 7 real members; PC = 21, **0 not in roster** | PASS — no OCR-invented names |

**Mayor-vote structure verified:** max named council roll = 5 across all motions (0 over-5); the
Mayor appears in the roll ("…and Mayor Silvestrini voted yes"); CRA "Chair" maps to the Mayor.
**No fabrication in any stratum** — OCR garble ("Councn Member") resolved to the correct roster
surname; collective phrasing left tally-only; absentees never invented.

## 3. Derived-layer reconciliation (all tie out)

- **db votes = 6721** == named CSV rows (council 4245 + PC 2476). Exact, delta +0. By body:
  Council 3790 + CRA 455 + PC 2476 = 6721.
- **db motions = 3016** == motions_std rows (council 2257 + PC 759). By body: Council 2011 +
  CRA 246 + PC 759. CRA = **58 source files · 246 motions** (matches docs).
- **motions_std outcome coverage = 100%** both bodies (2257/2257 council, 759/759 PC).
- **weeks/ = 258 votes.csv (of 275 week dirs); summed vote rows = 5580** == council flat total
  (weeks are council-centric by design — `build_weeks.py` ingests only `meeting_minutes`; PC joins
  on its own date and is not in the weekly bundles). weeks mtime > canonical CSV mtime → **fresh**.
- **0 undocumented db drops** — db has no UNIQUE(meeting_id, motion_no); same-date work+regular
  documents are stored as separate meeting_ids/motions, so nothing is silently collapsed.
- **0 real duplicates** keyed on (source, motion_no, member) in both bodies. (A naive
  (date, body, motion_no) key produces one false-positive "double" on 2023-01-23 — that date has
  **two separate council docs**, a Special Work Meeting + a Regular Meeting, each with its own
  motion_no=1. Correct join key is (source, motion_no) or db motion_id.)
- **Referrals = 34** (10 high / 19 medium / 5 low). The **3 two-sided `case_no` bridges**
  (ZT-23-004, ZM-23-006, ZM-24-001) each trace to a real PC↔Council pair — all three case numbers
  appear in BOTH `meeting_minutes/all_votes.csv` AND `planning_commission/all_votes.csv`.

## 4. Structured-data invariants

- Max named council roll = **5** (0 motions exceed the mayor-inclusive ceiling); PC ≤ 13.
- `validate_city.py` tally-vs-result: **922/922 council & 375/375 PC (100%)**.
- No member votes twice on one motion (0). No future dates. All index dates parse & fall in range.
- Named-council date range 2019-05-13 → 2026-06-08 (consistent with 2017/2018 being tally-only in
  the *extracted* data — but see Finding F-1).

## 5. Election spot-check (independent, outside sources)

- **Precinct sums reconcile exactly:** 17/17 contested races, precinct-summed votes ==
  race-row `total_votes`, **0 mismatches** (checked per year × election_type).
- **2021 D2 RCV (the divergence) — MATCH.** File: THOM DESIRANT winner, `ranked choice (RCV)`,
  first-choice margin **−26** (988 vs Clark 1014). Outside (SL Trib 2021 voter guide / KSL): Clark
  led first choice, then after Vice + Bagley-Gibson eliminations transfers moved to DeSirant, who
  won **51.7% vs 48.3%**. Winner + RCV divergence confirmed. *(The newspaper's election-night
  first-choice tallies — Clark 816 / DeSirant 728 — are smaller than the file's certified
  SLCo SOVC first-choice counts; expected press-vs-certified difference, not a defect.)*
- **2019 Mayor — MATCH.** File: JEFF SILVESTRINI 74.97% def. ANGEL VICE. Outside (Millcreek
  Journal / Deseret / KSL): Silvestrini def. Vice ~76.8%–23.2% election night. Winner + opponent +
  landslide margin confirmed. *(File uses certified SOVC totals — 10,855/3,625 — higher than the
  election-night press figures ~8,311/2,515; expected.)*
- Both winners independently re-confirmed against outside reporting; the 2021 first-choice
  breakdown here comes from the SL Trib voter guide (a different framing than Phase-5's citations).

## 6. Doc-drift sweep

- **No `{{...}}` placeholders remain** in `CLAUDE.md`, `README.md`, or any subfolder CLAUDE.md —
  the Phase-6 placeholder fill is complete.
- Doc counts reconcile to data: 372 council md (314 Council + 58 CRA), 2257 council motions,
  5580 council vote rows (4245 named); 149 PC md, 759 motions, 2840 rows (2476 named); db
  3016/6721; 34 referrals; 22 races; 275 week bundles; 51 precincts. All verified.
- **FIXED (trivial drift):** `VERIFICATION.md` (written 17:57, before `CLAUDE.md`/`README.md` were
  filled at 18:08/18:09) still claimed those files were unfilled "`{{CITY}}` templating"
  placeholders and that the validate WARN covered README/VERIFICATION. Both are stale — README/
  CLAUDE are filled and the current single WARN is only the IN-PACKETS comments CSV. Corrected via a
  dated addendum appended to `VERIFICATION.md` (respecting that file's dated-addendum convention).

## 7. Conformance

`python3 scripts/validate_city.py millcreek_city_council` → **21 PASS / 1 WARN / 0 FAIL.**
The single WARN = missing optional `public_comments/all_comments_clean.csv` → documented
IN-PACKETS state (`public_comments/AVAILABILITY.md`), not a defect.

---

## Findings (ranked)

### F-1 (DATA — moderate; DOCUMENTED, do not silently fix) — 2017 named roll calls extracted as tally-only

**What:** In **2017 only**, 70 unanimous council motions record individual voters in a tabular
en-dash format —
> `Motion passed unanimously by roll call vote with members voting as follows:`
> `Councilmember Uipi – Aye`  /  `Councilmember Catten – Aye`  /  `Mayor Silvestrini – Aye` …

but `meeting_minutes/extract_votes.py` only handles (a) collective "All Council Members voted yes"
and (b) prose "Councilmember X voted yes". The en-dash list matches the `UNANIMOUS`
("passed unanimously") pattern and falls through to **tally-only (blank member)**. Result: 2017 has
**0 named vote rows** in `all_votes.csv` despite the source naming voters on 70 motions
(~380 individual member-vote lines).

**Scope (measured):** 24 files, 70 "voting-as-follows" blocks, 380 en-dash member lines — **all in
council files, all Aye** (0 Nay/Absent/Abstain). Confined to 2017: 2018–2021 have 0 such blocks and
0 en-dash lines (their tally-only status is genuine source behavior — the doc claim holds for those
years; the 2019–2021 named rows come from the prose format, which the extractor *does* capture).

**Impact / severity:** Moderate but bounded and **safe-direction**:
- **No fabrication** — the downgrade is conservative (named→tally-only), never inventing votes.
- **Motion-level correctness intact** — all 70 are genuinely unanimous, so outcome, tally (`Pass
  (unanimous)`), and the contested signal are all correct.
- **Recoverable loss** — ~380 named Aye rows for 2017 are present in the source but absent from the
  extract; member-level analysis for 2017 is currently impossible. Recovering them would also raise
  low pre-2022 per-member counts (e.g. Marchant, who served in 2017).
- **Doc claim needs correction** — `CLAUDE.md` §2, `README.md`, and `VERIFICATION.md` describe
  "2017–2021 tally-only **by source**" and cite "2017 [0/174]" as a *source property*. For 2017
  this is inaccurate: the source **does** name voters; it is an **extraction-format gap**, not a
  source-format change. (The 2022 named-vote "seam" is really ~mid-2017 + 2022 in two different
  formats.)

**Recommended remediation (separate, user-approved pass — NOT done here):** extend
`extract_votes.py` with an en-dash roll-call pattern (`(Councilmember|Mayor) <Name> – (Aye|Nay|
Absent|Abstain)` under a "voting as follows" block), re-extract 2017, rebuild motions_std → db →
weeks, then correct the "[0/174]"/"by source" wording in CLAUDE/README/VERIFICATION to reflect that
2017 names voters in a tabular format.

### F-2 (DOC — trivial; FIXED) — stale placeholder claim in VERIFICATION.md
`VERIFICATION.md` claimed README/CLAUDE were unfilled `{{CITY}}` placeholders. They are filled.
Corrected via dated addendum (see §6).

---

## Grade table

| Dataset | Grade | Basis |
|---|---|---|
| meeting_minutes — minutes (text corpus) | **A** | Faithful OCR; uniform stats; garble contained; no fabrication |
| meeting_minutes — votes (extraction) | **B** | Clean, reconciled, zero fabrication — but F-1: 2017 named rolls (~380 rows) undercaptured as tally-only |
| CRA (within meeting_minutes) | **A** | Board/Chair→same 5 verified; cap 5; tally-only handled correctly |
| planning_commission — minutes + votes | **A** | Faithful; named commissioner rolls verified incl. OCR contested; 21/21 roster; referral language present |
| election_results | **A** | Precinct sums reconcile 17/17; 2 winners re-confirmed outside; RCV/appointment/cancelled findings hold |
| db (millcreek.db) | **A** | Exact reconciliation (6721/3016); no silent drops; referrals + case_no bridges verified real |
| weeks/ | **A** | Fresh; sum 5580 == council flat total (council-centric by design) |
| geo | **B** | Present + documented 2022-vintage boundary caveat (not independently re-tested this pass) |
| public_comments | **PARTIAL (by design)** | IN-PACKETS, documented pending harvest — not honest-empty, not a defect |

## Audit blind spots (completeness critic)

- **geo** address→district tool was not exercised against ground-truth addresses this pass (relied
  on Phase-5 + documented 2022-vintage caveat).
- **public_comments** IN-PACKETS claim was accepted from AVAILABILITY.md; the packet PDFs were not
  page-walked to independently confirm verbatim comments exist (Phase-5 verdict trusted).
- Ground-truth sampled 2016/2019/2020/2022/2023/2024/2026 across both bodies; **2018, 2021, 2025**
  had no fresh motion-level source diff this pass (their stats are clean and in-family).
- Election external check covered 2 of 22 races (2019 Mayor, 2021 D2); the 2023 cancelled-
  uncontested and 2025 appointment findings were reconciled internally + against Phase-5, not
  re-searched here.
- F-1's exact recoverable row count (~380) is a source-line estimate, not a re-run of a fixed
  extractor.
