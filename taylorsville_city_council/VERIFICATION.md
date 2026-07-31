# Verification — Taylorsville City Council data repo

**Verification date:** 2026-07-06
**Verifier:** independent Phase-5 agent (did NOT build the data; adversarial re-check, read-only except this file)
**Sources cross-checked:** source minutes PDFs/markdown, `db/taylorsville.db`, the flat CSVs,
Salt Lake County SOVC files, and OUTSIDE election sources (Taylorsville City Journal, Salt Lake
Tribune, the city's own certified 2019 results doc, city council/mayor pages).

## Summary table

| Dataset | Status | Rows | Coverage | Notes |
|---|---|---|---|---|
| Council minutes (`meeting_minutes/`) | **PASS** | 150 md == 150 index | 2020-01-08 → 2026-06-03 | 24 OCR files clean; 2 honestly unrecovered (2026-06-17 not-yet-posted, 2026-07-01 CANCELLED) |
| Council votes (`all_votes.csv`) | **PASS** | 2,457 rows / 2,315 named / 613 motions (605 Council + 8 RDA) | 2020–2026 | max tally 5 (Council & RDA); Mayor never votes; named roll calls printed in source (not Present-filled) |
| Planning Commission (`planning_commission/`) | **PASS** | 91 md == 91 index; 961 rows / 761 named / 324 motions | 2020–2026 | 31 OCR files clean; 3 vote formats all parse; 5 "No recorded vote" honest |
| Relational db (`db/taylorsville.db`) | **PASS** | 3,076 votes == named CSV rows; 937 motions | 2020–2026 | 0 dropped, 0 duplicate (motion,person); mayor absent from `person`; referral 7 high/15 med/6 low |
| Elections (`taylorsville_races.csv`) | **PASS** | 2007–2025 | 2019 gap RECOVERED | 2017 Mayor + 3×2019 + 2021 D3/D5 confirmed against outside sources |
| Geo (`address_to_district.py`) | **PASS** | 44 precincts → Districts 1–5 | current boundaries | point-in-polygon verified; address-geocode mode needs network (env limitation, not a data defect) |
| Public comments | **PASS (honest-empty)** | 0 | n/a | `AVAILABILITY.md` (145 lines) documents SUBMIT-ONLY verdict; no `all_comments_clean.csv` by design |
| Weeks (derived) | **PASS** | 144 week dirs | — | regenerates clean; spot-check 2021-03-03 = 17 rows both canonical & week bundle |

**Overall: 8/8 datasets PASS.** No fabrication found. All discrepancies are documented, source-faithful, and non-fabricating.

---

## Reconciliation (independently measured)

- **Council minutes:** 150 markdown files == 150 `minutes_index.csv` rows. Raw = 163 PDFs; 163 − 12 agendas − 1 cancellation = 150 minutes. `minutes_unrecovered.csv` holds exactly the 2 honest gaps (2026-06-17 minutes not yet posted; 2026-07-01 meeting CANCELLED — docId 12089 is the cancellation notice, not minutes). ✓
- **PC minutes:** 91 markdown == 91 index. ✓
- **db votes == named CSV:** db `vote` = **3,076**; council named rows **2,315** + PC named rows **761** = **3,076** (delta 0). By value: Aye 2,863 · Nay 81 · Absent 94 · Abstain 35 · Recuse 3 (matches SCHEMA.md). ✓
- **0 duplicate** (motion_id, person_id) rows in db. ✓
- **Max council tally = 5, max RDA = 5, max PC = 8** (7 members + alternate). A naive (date, motion_no) group hit 10 only because Council & RDA reuse motion numbers on the same date; regrouped by (date, body, motion_no) the ceiling is 5. ✓
- **Weeks = 144 dirs**; validator confirms weekly votes sum 2,457 == flat total and weeks are not stale. ✓
- **validate_city.py: 21 PASS / 1 WARN / 0 FAIL** (WARN justified below).

---

## Motion traces (sampled against source minutes)

1. **Council contested + Chair mapping — 2021-03-03 m2/m4** (`.../2021-03-03_city-council.md`). Source prints a per-member roll call: m2 "moved to deny Resolution 21-09" → Burgess No, Barbieri No, **Chair Cochran** No, Armstrong Yes, Harker Yes → "**The motion failed 3-2**". CSV: 2 Aye / 3 Nay, result `3-2 Fail`. m4 "moved to approve" → 3 Yes / 2 No → "**passed 3-2**", CSV `3-2 Pass`. **Outcome orientation correct** (validator: 0 outcome-vs-count inconsistencies). **`Chair Cochran` is attributed to councilmember Curt Cochran** — not a separate person. ✓
2. **RDA named roll call — 2021-06-02 m1** (`.../2021-06-02_city-council.md`). Source prints "Councilmember Barbieri Yes … Armstrong Yes … **The motion passed 5-0**" with each member listed. CSV `5-0 Pass`, 5 named Ayes. Confirms named-unanimous motions are backed by a **printed** per-member roll call, NOT attendance-fill. ✓
3. **PC tabular contested (2025 format) + 2nd Chair mapping — 2025-01-14 m3** (`.../2025-01-14_planning-commission.md`). Source tabular: "Commissioner Willardson: No / Russell: Aye / McElreath: Aye / Wright: Aye / **Chair Wilkey**: Aye / Wendel: Aye" → File #3S124 final action. CSV `6-1 Approved (Final Action)`, Willardson→Nay, **Chair Wilkey→Cindy Wilkey** Aye. ✓
4. **PC named-inline (2023 format) — 2023-02-28 m4** (`.../2023-02-28_planning-commission.md`). Source: "VOTE: Young – AYE, **Wilkey – NAY**, Wright – AYE, Willardson – AYE, Russell – AYE, Quigley – AYE. Motion passes 5 to 1." CSV `Positive recommendation 5-1`, Wilkey→Nay. ✓
5. **PC narrative-tally unanimous (2021 format) — 2022-04-26 m1/m3** stay tally-only: `Pass (unanimous)`, EMPTY member lists (no invented Ayes). ✓
6. **OCR-file name spot-check — 2022-04-26 m2** (OCR file). Source roll call printed "6 in favor, 1 in opposition" but the OCR dropped Commissioner **Wendel's** vote token ("Commissioner Wendel," with no AYE/YES after). CSV honestly recorded the 5 legible Ayes + Quigley Nay = `5-1 Approved (Final Action)` — **Wendel's vote was NOT invented**; matches the documented named-vs-printed discrepancy. ✓

**Unanimous-invention screen:** 0 council/RDA motions carry a "unanimous" result string while also listing named members. Corpus screener: **0 outliers** on both minutes corpora (dict/split-word/weird-char), including all OCR files. **The 24 OCR council files invented no names.**

---

## Mayor-non-voting & roster

- **Mayor Kristie Overson appears in 0 vote rows** (CSV) and is **absent from the db `person` table** (queried `%verson%`/`%Mayor%` → empty). ✓
- **`Chair <Name>` always maps to a sitting councilmember** (verified Chair Cochran→Cochran, Chair Wilkey→Wilkey), never a separate person.
- **Roster of 7 confirmed:** current 5 — Burgess (D1), Cochran (D2), Barbieri (D3), Harker (D4), Knudsen (D5) — plus former **Dan Armstrong** and **Brad Christopherson**. Per-year roster shows Christopherson voting in 2020 (66 rows) and Armstrong through 2021 (71 rows); Knudsen appears from 2022. **The 2 former members really vote in 2020–21.** Barbieri appears 2020 (14 rows) → full 2021, consistent with the documented D3 vacancy chain (Christopherson vacated → Barbieri appointed, then won the 2021 D3 special). ✓

---

## Three PC vote formats & the 5 "No recorded vote" motions

- **Narrative-tally (2021)**, **named-inline (2023)**, **tabular (2025)** each spot-checked to source and parse correctly (traces 3–5 above).
- **5 "No recorded vote" motions** (2021-07-27 m3, 2023-05-09 m3, 2024-07-09 m5, 2024-09-10 m2, 2025-06-10 m2) all carry empty result/member fields — moved but not voted (superseded or tabled for lack of quorum). **None asserted as a pass.** ✓

---

## External election cross-check (race-by-race)

| Race | File says | Outside source | Result |
|---|---|---|---|
| **2017 Mayor** | Overson 5,444 (57.2%) def. Larry Johnson 4,073 (42.8%), margin 14.4 pt | Taylorsville City Journal ("Councilwoman Overson defeats incumbent…"); Salt Lake Tribune (Johnson losing 58-42) | **MATCH** — incumbent Johnson unseated, ~14 pt |
| **2019 D1** (recovered) | Burgess 1,044 (63.62%) def. Gehrke 597 | City certified results doc id=3764; Deseret News 2019 tallies | **MATCH** (exact) |
| **2019 D2** (recovered) | Cochran 954 (60.61%) def. McElreath 620 | same | **MATCH** (exact) |
| **2019 D3** (recovered) | Christopherson 1,197 (100%, unopposed) | same | **MATCH** (exact) |
| **2021 D3 special** | Barbieri 1,119 (100%, unopposed) | Taylorsville City Journal ("None of the three… face opponents") | **MATCH** (winner/uncontested); election-night count 1,115 vs certified 1,119 |
| **2021 D5** | Knudsen 914 (52.56%) def. Larry Johnson 825 | SL Tribune 2021 voter guide; Taylorsville City Journal | **MATCH** (winner); election-night 911 vs 820, certified 914 vs 825 |

- The tiny 2021 vote deltas (3–5 votes) are **election-night unofficial vs certified-canvass** counts — the file uses the certified SOVC; winners, margins, and the uncontested/contested structure all match.
- **2019 gap flagged in recon is RECOVERED** (D1/D2/D3 re-parsed from the raw 2019 SOVC). **2021 D3 correctly labeled a special/unexpired-term** race in the `note` column.
- **Roster implied by elections == vote-casters** after name normalization (Burgess D1, Cochran D2, Barbieri D3, Harker D4, Knudsen D5; former Armstrong/Christopherson in the earlier record).

---

## validate_city.py — counts & WARN justification

`python3 scripts/validate_city.py taylorsville_city_council` → **21 PASS / 1 WARN / 0 FAIL.**
- `f.tally[meeting_minutes]` 462/471 (98.1%) & `f.tally[planning_commission]` 112/112 (100%).
- `g.std` both bodies conform (council 613, PC 324). `h.db` reconciles exactly (3,076 == 3,076).
- **The single WARN** = `a.layout: missing optional public_comments/all_comments_clean.csv, README.md, VERIFICATION.md`, each a documented quirk:
  - `all_comments_clean.csv` — intentionally absent (comments honest-empty; `AVAILABILITY.md` documents SUBMIT-ONLY). ✓
  - `README.md` — Phase-6 TODO (not yet written). ✓
  - `VERIFICATION.md` — this file (now created). ✓

**Council `motions_std` 88.7% (544/613) known outcome verified as a SOURCE blank, not a parser miss:** all **69** `outcome=unknown` council motions have **blank `result_raw`** (0 non-blank among them) — the source minutes printed no outcome for those motions (procedural/administrative items with no recorded disposition). This is an honest source limitation, correctly carried as `unknown`. ✓

---

## Discrepancies found (all documented & source-faithful — none are fabrication)

1. **10 named-count vs printed-tally mismatches** (validator, hand-review list): e.g. 2020-05-06 m3/m4/m6 (printed 4-0, 3 names survived), 2021-06-16 m4/m5, 2021-11-17 m2, 2024-08-21 m2, 2025-01-22 m5, 2026-03-04 m3 (printed 5-0, 4 named), plus 2021-03-03 m2 (correctly a 3-2 by orientation). All are OCR-dropped names or source typos where the extractor kept the legible names and never invented the missing one. Documented; not corrected in place (spec-compliant).
2. **PC named-vs-printed drops** (documented in `planning_commission/CLAUDE.md`): 2021-11-09 m3 (5-1 vs printed 6-1, source clerk omission), 2022-04-26 m2, 2024-10-22 m1 (header-less OCR), 2026-01-27 m1. All faithful to source.
3. **Address-geocode mode of `address_to_district.py` returns "no match"** in this sandbox (no network geocoder). The point-in-polygon path (`--latlon`) works correctly and names the current member — this is an environment limitation, not a data defect.

---

## Gaps & recommendations

- **README.md** not yet written — Phase-6 TODO (the only real omission; already noted in-repo).
- **`planning_commission/motions_std.csv` exists** (324 rows) despite the PC CLAUDE.md listing it as a TODO — the CLAUDE.md note is stale and can be updated; the crosswalk registration should be confirmed when `scripts/build_cities_db.py` next runs.
- Comments are legitimately empty (SUBMIT-ONLY) — no action.
- No fabrication, no silent truncation, no duplicate rows found anywhere. The build is honest.

**Verdict: repository PASSES independent verification.** Recommended next step: write `README.md`, then run `/audit-city-data` as the final Phase-6 gate.

---

## Addendum 2026-07-19 — elections re-point + 2019 D1 primary adoption

- **Re-pointed `election_results/clean_elections.py` to the Salt Lake County canonical**
  (`salt_lake_county/elections/slco_municipal_results_long.csv`) as the long-file source,
  retiring the redundant per-city slice `raw/municipal_results_long_taylorsville.csv`
  (backed up, then deleted). The 2019 & 2021 generals are still re-parsed from the retained
  `raw/sovc/*.xlsx`. **Hard byte-identity gate PASSED:** the re-pointed build reproduces
  `taylorsville_races.csv` / `taylorsville_results_by_candidate.csv` /
  `taylorsville_results_by_precinct.csv` **byte-for-byte** against the prior committed files,
  with the SOLE diff being the newly-adopted primary below (all 38 prior races / 90 candidate
  / 1,353 precinct rows unchanged).
- **Adopted a real, previously-missing contest: the 2019 District 1 municipal primary.**
  District 1 drew 3 candidates, triggering a primary the prior docs wrongly denied ("no 2019
  primary"). The canonical carries it, and it is **cell-verified against the raw workbook**
  `2019-08-13-municipal-primary-sovc.xlsx` (sheet `25`): per-precinct Total Votes TAY001
  149/89/6, TAY002 167/63/10, TAY004 114/64/32, TAY007 120/64/135, TAY008 178/91/46, summing
  to the workbook's own `Total:` row **Burgess 728 / Gehrke 371 / Quigley 229** (grand total
  1,328). No suppression, no method-label pseudo-candidates. **Cross-corroboration:** the
  primary's top-2 (Burgess, Gehrke) are exactly the two candidates on the 2019 D1 general
  ballot. Race count now **39 (32 general + 7 primary)**; by_candidate **93**; by_precinct
  **1,368**. Backups: `_backups/2026-07-19-pv-tierb-low/taylorsville-elections/`.
