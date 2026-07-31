# Audit report — Taylorsville City Council data repo

**Audit date:** 2026-07-06
**Method:** `/audit-city-data` run as the independent, adversarial **Phase-6 FINAL GATE**
(read-only except this report; deeper samples than the Phase-5 `VERIFICATION.md`).
**Auditor:** independent audit agent — did not build or verify the data previously.
**Scope:** `taylorsville_city_council/` only (cross-city files untouched).

## SIGN-OFF: READY (ship)

Every pillar holds: the statistical screen is clean per-year across the mid-2025 OCR seam;
15 hand-verified motions (incl. OCR, all 3 PC formats, tabular-contested, tally-only,
Chair-mapping) show **zero fabrication**; every doubly-stored fact reconciles exactly;
two election winners independently re-confirmed against outside sources (neither touched by
Phase 5); README/CLAUDE counts match the data; `validate_city.py` = 21 PASS / 1 WARN / 0 FAIL
(WARN = the intentionally-absent, honest-empty comments CSV). No data-level defect found. One
cosmetic normalization note (Excused->Absent) documented below; no fix required.

---

## 1. Statistical screen (per-year, both corpora)

`screen_corpus.py` on `meeting_minutes/minutes/` (150) and `planning_commission/minutes/` (91).

**Council** — 0 cid / 0 replacement-char / 0 PUA / 0 mojibake / 0 stub / 0 short / 0 duplicate-body /
0 long-token. dict_ratio median **0.736** (min 0.679, **0 outliers**); split_word/1k median 0.00
(max 1.44, 0 outliers); weird_char median 0.0004 (0 outliers). Advisory-only: 23 hyphen-break,
131 repeated-line (per-page headers), 89 ends-mid (attendee/footer) — all benign.

| year | files | med_dict | med_split | med_weird |
|---|---|---|---|---|
| 2020 | 23 | 0.739 | 0.000 | 0.000 |
| 2021 | 25 | 0.735 | 0.000 | 0.000 |
| 2022 | 25 | 0.750 | 0.000 | 0.000 |
| 2023 | 21 | 0.728 | 0.000 | 0.000 |
| 2024 | 23 | 0.753 | 0.000 | 0.000 |
| **2025** (OCR seam) | 22 | 0.730 | 0.000 | 0.000 |
| **2026** (OCR) | 11 | 0.726 | 0.000 | 0.000 |

**PC** — same clean profile. dict_ratio median **0.778** (min 0.611, **1 outlier**);
split_word/1k median 0.00 (max 2.87, 0 outliers); weird_char median 0.0002 (0 outliers).

| year | files | med_dict | med_split | med_weird |
|---|---|---|---|---|
| 2020 | 11 | 0.796 | 0.000 | 0.000 |
| 2021 | 12 | 0.808 | 0.000 | 0.000 |
| 2022 | 15 | 0.800 | 0.280 | 0.000 |
| 2023 | 15 | 0.782 | 0.280 | 0.000 |
| 2024 | 15 | 0.768 | 0.000 | 0.000 |
| **2025** (OCR seam) | 16 | 0.743 | 0.000 | 0.000 |
| **2026** (OCR) | 7 | 0.734 | 0.000 | 0.000 |

**OCR-seam verdict:** the 2025/2026 OCR years (24 council + 31 PC scanned) do **not** break
from their born-digital neighbors — dict_ratio stays inside the 0.72-0.81 corpus band, split-word
and weird-char stay at 0. No PUA / no font-cmap / no stub / no duplicate-body pathology anywhere.

**One outlier investigated -> benign:** `planning_commission/.../2025-08-26_planning-commission.md`
(dict 0.611). It is a **training-presentation** meeting (Utah Land Institute; rosters of visiting
commissions, guest attorney/planner names) — the low dict_ratio is proper-noun density, not
corruption. OCR is clean; source typos (`~`, `-Strategic`) preserved. No defect.

---

## 2. Ground truth — 15 motions hand-verified vs source (deeper than Phase 5)

Born-digital via `pdftotext -layout`; OCR via **visual Read of the scanned PDF pages**.
All samples new relative to Phase 5 except where noted. **Zero fabrication in every check.**

| # | Motion | Stratum | Source vs data | Result |
|---|---|---|---|---|
| 1 | Council **2022-06-15 m3** | **tabular contested, max 5, Chair-map, Absent** | Source: "Chair Barbieri moved to deny Ord 22-07" -> Cochran Excused / Barbieri Yes / Harker **No** / Burgess Yes / Knudsen Yes -> "passed 3-1". CSV: 3-1 Pass, Harker Nay, `Chair Barbieri`->**Anna Barbieri**, Cochran non-voting, mayor absent, tally 5. | **PASS** |
| 2 | Council **2024-06-05 m2** | contested 4-1, 2nd Chair-map | Source: Res 24-12 -> Cochran/Burgess/Harker/Barbieri Yes, **Knudsen No** -> "4-1". `Chair Cochran`->**Curt Cochran**. Source quirks ("via text", "No audio available") faithfully carried. | **PASS** |
| 3 | Council **2025-06-18 m3** | **OCR, named 5-0, 3rd Chair-map** | Read scanned PDF pp.2-3: attendance/narrative/Mayor-Overson-report match markdown; Res 25-21 all 5 named. `Chair Harker`->**Meredith Harker**. Burgess-arrives-7:20 dynamics faithful (m1/m2 honest 4-0). | **PASS** |
| 4 | Council **2026-03-04 m3** | **OCR name-drop (documented)** | OCR markdown has all 5 incl. "Council Member Harker **'** Yes" (stray OCR apostrophe); the vote extractor missed that noise-token, so CSV m3 = 5-0 with **4** named. Tally faithful (5-0); the 4 present names correct; **Harker's real vote dropped, NOT invented**. Matches `CLAUDE.md` "printed 5-0, 4 named". | **PASS (documented)** |
| 5 | Council **2024-05-15 m1** | **FORM-C tally-only unanimous** | Source: "moved to transfer... seconded by Burgess **and passed unanimously**" — no roll-call block. CSV: `Unanimous Pass`, **0 named members**. No Present-fill, no invented ayes. | **PASS** |
| 6 | Chair->member mapping (aggregate) | Chair mapping | 4 distinct presiding chairs seen in checks 1-4 (Barbieri, Cochran, Harker, Knudsen) each map to the sitting councilmember; **Mayor Overson never in a vote row / never a chair**. | **PASS** |
| 7 | PC **2020-03-10 m4** | **PC named-inline (early)** | Source: "...Commissioner **Willardson - NO**. The motion passes 6 to 1." CSV: Positive recommendation 6-1, Willardson Nay, others Aye. | **PASS** |
| 8 | PC **2023-06-27 m3** | **PC named-inline (2023)** | Source: "Russell AYE, Wright AYE, **Wilkey NO, Quigley NO**, Wendel AYE, McElreath AYE, **Willardson NO**. passes 4 in favor, 3 in opposition." CSV: 4-3 Approved, exact. | **PASS** |
| 9 | PC **2025-07-22 m8** | **PC OCR + tabular + contested** | Read scanned PDF p.11: table "McElreath No / Quigley Yes / Wilkey No / Wright Yes / Chair Russell Yes / **Munoz Abstain** / Young No -> Failed 3-3." CSV exact. `Chair Russell`->Russell; PDF "Munoz" (tilde) -> OCR variants (`Munoz`/`Mufioz`) fuzzy-matched to Barbara Munoz. m9 (4-2) on same page also verified. | **PASS** |
| 10 | PC **2024-09-10 m1** | **PC narrative-tally (3rd format)** | Source: "Wendel moved to approve the minutes... seconded by Russell **and passed** [unanimously]" — no per-member block. CSV: `Pass (unanimous)`, 0 named. | **PASS** |
| 11 | PC **2024-09-10 m2** | **"No recorded vote" honesty** | Source: "Quigley moved to forward a negative recommendation... **The motion died for lack of a second**." CSV: `No recorded vote`, empty result/members — **not asserted as a pass**. | **PASS** |
| 12 | OCR faithfulness — council (2025-06-18) | hallucination screen | Scanned PDF text matches markdown incl. **preserved degradation** ("Ernest"->OCR "Emest", fuzzy-matched to Burgess). Implausibly-clean text would signal hallucination; not present. | **PASS** |
| 13 | OCR faithfulness — PC (2025-07-22) | hallucination screen | Scanned tabular roll calls (pp.10-11) reproduced verbatim in markdown; no invented rows. | **PASS** |
| 14 | Fabrication direction — whole corpus | invariant | Across all motions, **named voters never exceed the printed tally** except the single 2021-03-03 m2 deny-motion orientation artifact (named nays 3 defeated ayes 2; "3-2 Fail" — a labeling orientation, not an extra name). PC: 0 over, 0 under. | **PASS** |
| 15 | Unanimous-invention screen | invariant | 0 council/RDA motions carry a "unanimous" result string **and** a named member list; the 24 OCR council + 31 OCR PC files invented **0** names. | **PASS** |

**Three PC formats all confirmed against source:** narrative-tally (#10) - named-inline (#7,#8) -
tabular (#9). **Tabular-contested council roll (#1)** and **tally-only unanimous (#5, #10)** confirmed.

---

## 3. Derived-layer reconciliation (all counted twice)

| Fact | Expected | Measured | Delta |
|---|---|---|---|
| db `vote` == named CSV rows | 3,076 | 3,076 (council 2,315 + PC 761) | **0** |
| Vote values | Aye 2,863 - Nay 81 - Absent 94 - Abstain 35 - Recuse 3 | identical | **0** |
| db motions | 937 (Council 605 + RDA 8 + PC 324) | 937 | **0** |
| Duplicate (motion,person) | 0 | 0 | — |
| Orphan FKs (vote->motion, vote->person) | 0 | 0, 0 | — |
| Undocumented db drops (CSV-db) | 0 | 0 | — |
| Mayor in `person` table | absent | absent (`%verson%`/`%Mayor%` -> empty) | — |
| motions_std outcome — council | 88.7% (544/613; 69 unknown) | 88.7%; **all 69 unknown have blank `result_raw`** (0 non-blank) | source-blank, not parser miss |
| motions_std outcome — PC | 99.1% (321/324) | 99.1% | ok |
| weeks vote sum == flat total | 2,457 | 2,457 (141 votes.csv files, 144 week dirs) | **0** |
| weeks staleness | not stale | weeks mtime > canonical CSV mtime | fresh |
| referral links | 28 (7 high / 15 med / 6 low) | 28 (7 / 15 / 6) | ok |
| v_contested | 73 | 73 | ok |
| CSV invariants | no future/bad dates, no member voting twice | 0 / 0 / 0 both corpora | ok |

The 69 council `outcome=unknown` motions were independently confirmed truly source-blank
(procedural/administrative items the minutes printed no disposition for) — an honest source limit.

---

## 4. Election spot-check (independent, outside sources — both new vs Phase 5)

| Race | File | Outside source | Result |
|---|---|---|---|
| **2023 D1 Council** | Burgess 1,070 (64.73%) def. Sanok 583 | Salt Lake County / KSL municipal results (web) | **EXACT MATCH** |
| **2025 D4 Council** | Harker 1,140 (56.02%) def. Munoz 895 | Taylorsville Journal ("Harker earned a lopsided win... third four-year term") | **MATCH** (winner + decisive margin) |

- **Precinct sums reconcile exactly:** 2021 D5 by-precinct {Knudsen 914, Johnson 825} ==
  by-candidate {914, 825} == races winner/runner-up (914/825). **MATCH.**
- **2019 gap RECOVERED:** all three re-parsed races present — D1 Burgess 1,044, D2 Cochran 954,
  D3 Christopherson 1,197.
- **2021 D3 special flag present:** `note` field documents "special / unexpired-term election
  ... Christopherson vacated — Barbieri won this balance, then the full D3 term in 2023",
  `uncontested=True`. Correctly out-of-cycle.
- 38 races total, 2007-2025.

---

## 5. Doc-drift sweep

- **README.md counts all match measured data:** 150/91 minutes (== index), 126+24 / 60+31
  pdf-text/ocr, 613 (605+8) / 324 motions, 2,457 (2,315 named) / 961 (761 named) rows,
  937 db motions, 3,076 votes, 28 referrals (7/15/6), 38 races, 44 precincts, 144 week bundles,
  motions_std council 613 / PC 324. **No drift.**
- **CLAUDE.md (root + subfolders) match** (150, 613, 2,457, 2,315 named, 24 OCR; PC 91, 324,
  761 named, 31 OCR, 12 commissioners; 58+81+185=324; 112+212 named/tally-only).
- **PC CLAUDE `motions_std` note already corrected** to "BUILT, 324 rows" (Phase-5 flagged it
  stale; it is now fixed) — no action needed.
- **No `{{...}}` placeholders** anywhere in the repo.
- **Unrecovered log accurate:** council holds exactly the 2 honest 2026 gaps (2026-06-17 minutes
  not-yet-posted; 2026-07-01 CANCELLED, docId 12089 = cancellation notice); PC 0. Never stubbed.

No trivial doc-drift required fixing (README/VERIFICATION now present; counts already reconcile).

---

## 6. Conformance

`python3 scripts/validate_city.py taylorsville_city_council/` -> **21 PASS / 1 WARN / 0 FAIL.**
- Only WARN: `missing optional public_comments/all_comments_clean.csv` — the documented
  honest-empty (SUBMIT-ONLY) quirk. README.md and VERIFICATION.md now both present.
- f.tally council 462/471 (98.1%) - PC 112/112 (100%); g.std council 613 / PC 324 conform;
  h.db reconciles exactly (3,076 == 3,076, 937 motions); i.weeks not stale, sum 2,457 == flat.

---

## 7. Minor observation (no fix required)

**Source "Excused" is normalized to `Absent`.** Where the minutes print a member as "Excused"
(e.g. 2022-06-15 Councilmember Cochran), the extracted `vote` field records `Absent` — 0
"Excused" strings survive in either CSV, and the db `vote` table uses none of its allowed
`Excused` enum value (all no-shows -> `Absent`). This is a **deliberate, non-fabricating
normalization** (the member cast no vote; the verbatim source is retained in `raw/`), consistent
with the already-normalized `vote` field (source "Yes"/"No" -> Aye/Nay). It flattens the
Excused<->Absent distinction the source draws; harmless for tallies (both excluded from N-M) and
not a defect. Optional: a one-line note in `meeting_minutes/CLAUDE.md` could record the mapping.

---

## 8. Grade table

| Dataset | Grade | Basis |
|---|---|---|
| Council + RDA minutes | **A** | screen clean per-year incl. OCR seam; OCR faithful vs scan; source typos preserved |
| Council + RDA votes | **A** | 15-motion ground truth zero-fabrication; tabular/FORM-C/Chair-map/RDA all faithful; documented OCR name-drops bounded |
| PC minutes | **A** | screen clean; 1 outlier benign (training mtg); OCR faithful |
| PC votes | **A** | all 3 formats verified; tabular-contested + narrative-tally + "No recorded vote" honest |
| Relational db | **A** | reconciles exactly (3,076/937); 0 drops/orphans/dupes; mayor absent |
| Elections | **A** | 2 new outside-source confirmations exact; precinct sums reconcile; 2019 recovered; 2021 D3 special flagged |
| Geo | **B** | precinct-derived, post-2020 vintage (documented); point-in-polygon offline OK |
| Public comments | **A (honest-empty)** | SUBMIT-ONLY verdict documented; deliberately no CSV |
| Weeks (derived) | **A** | sum 2,457 == flat, not stale |

---

## 9. Audit blind spots (completeness critic)

- **Address-geocode mode** of `geo/address_to_district.py` not exercised (needs network; the
  offline `--latlon` point-in-polygon path is the verified one — an env limit, not a data claim).
- **Referral confidence tiers** confirmed by count (7/15/6) and view (v_contested=73) but the
  individual 28 links were not each re-traced to source (Phase-5 spot-checked; the audit relied on
  count reconciliation + the one-sided-case-number caveat already documented).
- **Ground-truth years sampled:** council 2022/2024/2025/2026; PC 2020/2023/2024/2025. Council
  2020/2021/2023 and PC 2021/2022/2026 individual motions were screened statistically but not
  hand-diffed to source (screen was clean for those years).
- **Comment corpus** has no text to screen (honest-empty by design) — nothing to sample.
