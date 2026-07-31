# Audit — South Jordan City Council data repo

**Audit date:** 2026-07-06
**Method:** `/audit-city-data` run as the **independent FINAL GATE** (Phase 6.3 of
`build-city-data-repo`). Adversarial, independent, larger ground-truth samples than the
Phase-5 `VERIFICATION.md`. Read-only on all built data (flat CSVs / minutes / votes JSON
never altered); only doc-drift in `.md` files was corrected.
**Verdict: READY — SIGN-OFF.** 0 data-integrity defects. 19 PASS / 3 WARN / 0 FAIL
conformance. Two trivial doc-drift fixes applied (below).

---

## 1. Statistical screen (`screen_corpus.py`) — both corpora, per-year

Both minutes corpora are **born-digital and clean**. No PUA/OCR/stub/duplicate-body
pathologies from the known-failure library appear.

**Council minutes** (`meeting_minutes/minutes`, 243 files):
| Detector | Result |
|---|---|
| cid_artifacts / PUA_garbled(>1%) / mojibake / long_tokens / stubs / short / duplicate_bodies | **0/243 each** |
| replacement_chars | 6/243 — all benign (Wingdings bullet glyph `U+F0A7`, isolated, <1%) |
| split_word_outlier | 2/243 — **false positives**: long `source_url` in provenance header (ADID URLs) |
| weird_char_outlier | 1/243 — benign bullet glyph |
| hyphen_breaks / repeated_line / ends_mid | advisory only (per-page headers, "South Jordan City Recorder" footer, section labels) |
| dict_ratio | median 0.808, min 0.726 — no outliers |

Per-year medians (dict / split / weird): 2020 .808/0/.001 · 2021 .817/.075/.001 ·
2022 .821/.070/0 · 2023 .815/0/.001 · 2024 .798/0/.001 · 2025 .780/.100/.001 ·
2026 .773/.080/.001. **No year breaks from its neighbors** — dict_ratio drifts down
gently 2024→2026 (longer, more procedural recent minutes), not a garbled year.

**PC minutes** (`planning_commission/minutes`, 125 files):
| Detector | Result |
|---|---|
| cid / PUA / mojibake / long_tokens / stubs / short / duplicate_bodies / replacement_chars | **0/125 each** |
| split_word_outlier | 0/125 |
| weird_char_outlier | 1/125 — benign bullet glyph (`U+F0A7`) |
| dict_ratio | median 0.815, min 0.701 — no outliers |

Per-year medians steady (2020 .825 → 2025 .838 → 2026 .834); no year breaks.

**Screen conclusion:** born-digital confirmed; every outlier investigated and benign.

## 2. Ground-truth sample — 10 motions across council + PC, traced to source text

| # | Body / date / motion | Type | Source confirmation | Result |
|---|---|---|---|---|
| 1 | Council 2025-06-17 m9 (Ord 2025-09) | **mayoral tie-break** | src ll.816-823: Shelton/Johnson **Yes**, Harris/McGuire **No**, Zander **Absent**, **Mayor Dawn R. Ramsey Yes**, "passed with a vote of 3-2" — CSV records all six incl. `Dawn R. Ramsey \| Aye`, `3-2 Pass` | **PASS (exact)** |
| 2 | Council 2025-08-19 m7 (table R2025-41) | **documented clerk error** | src roll call: Shelton/McGuire/Johnson Yes, Harris No, **plus a duplicate McGuire line** → "vote of 4-1". Extractor correctly **deduplicated** to 4 named rows (no Aye+Nay pair, no double-vote), preserved verbatim `4-1 Pass` | **PASS** |
| 3 | PC 2022-10-11 m3/m4 | **documented clerk error** | src l.1094 "Vote was 3-3, with no votes made by Commissioner Bevans, Chair Hollist, and…"; l.1127 "Roll Call vote was 4-0, no votes made by…" — both preserved **verbatim** as native `result` string, flagged by PC validator | **PASS** |
| 4 | Council 2020-08-18 m1 | minutes-approval, unanimous | McGuire moves to approve prior minutes; narrative-tally, no invented Aye names | **PASS** |
| 5 | Council/RDA 2023-07-18 m9 | **RDA**, unanimous | src ll.270-271 "…Council Member Zander seconded the motion. Roll Call vote was 5-0, unanimous in favor" — CSV `5-0 Pass`, member/vote blank (tally-only, no fabrication) | **PASS** |
| 6 | Council/MBA 2021-04-20 m9 | **MBA**, unanimous | src ll.171-172 (Combined CC/RDA/MBA section) "McGuire made a motion to approve Resolution R2021-13. …Zander seconded… vote was unanimous in favor" — CSV `Unanimous Pass`, MBA body | **PASS** |
| 7 | PC 2025-08-12 m4 (Bess Dental rezone) | **recommendation** | src "Vote was 4-0 unanimous in favor"; recommending-body language ("recommend the council approve the rezone"); Hollist Absent — CSV `4-0 unanimous in favor`, Harding mover, Gedge sec, Hollist Absent | **PASS** |
| 8 | PC 2025-05-27 m8 | contested 6-1 | src l.1083 "Vote was 6-1 with Commissioner Bevans voting No" — CSV verbatim, Bevans Nay, Hollist mover | **PASS (exact)** |
| 9 | PC 2020-11-10 m5 | contested 4-1 | src l.450 "Roll Call Vote was 4-1 Commissioner Catmull Voted No" — CSV verbatim, Catmull Nay | **PASS (exact)** |
| 10 | Council 2024-12-03 m3 (R2024-42) | contested full roll, **Fail** | src: Zander **Yes**, Shelton **Yes**, McGuire/Johnson/Harris **No**, "denied with a vote of 2-3" — CSV `2-3 Fail`, 2 Aye / 3 Nay all named | **PASS (exact)** |

**10/10 PASS. Zero fabricated Aye names** — unanimous narrative motions carry blank
member/vote (source printed no roster); dissenter-only motions name only the No. The
tie-break and both clerk errors are stored verbatim and flagged, not smoothed.

## 3. Derived-layer reconciliation

| Invariant | Expected | Measured | Status |
|---|---|---|---|
| db vote rows == named CSV rows | 1110 | council 757 + PC 353 = 1110 == db 1110 | **delta 0** |
| db motion rows == CSV motions | 1759 | council 1029 + PC 730 = 1759 == db 1759 | **exact** |
| motions_std outcome coverage (council) | 100% | 1029/1029 | **100%** |
| motions_std outcome coverage (PC) | 100% | 730/730 | **100%** |
| weeks vote sum == council flat total | 1448 | 128 weeks summing 1448 (Council 1418 + RDA 29 + MBA 1) | **exact** |
| weeks freshness | not stale | validator PASS (weeks not older than CSVs) | **fresh** |
| db-dropped rows explained by overrides | 0 dropped | delta 0 → nothing dropped; `db/overrides.csv` + `db/referral_overrides.csv` both header-only (0 rows) by design | **clean** |

**Note (design, not a defect):** `build_weeks.py` buckets only `meeting_minutes/all_votes.csv`
(council + its in-session RDA/MBA), so weeks total = council flat total 1448; PC's 797
rows are intentionally not in the weekly grid (PC is not on the council weekly join).
This matches the build spec and the stated acceptance value.

**Referrals (13 total: 1 high, 10 medium, 2 low):** high + medium spot-checked to real
PC→Council pairs —
- **HIGH #11** (address+subject, 9816/9822/9828 S Temple Dr): PC 2025-08-12 "Bess Dental
  Office Rezone" → Council 2025-09-02 rezone of the same three parcels. **Real.**
- **MEDIUM #4** (Aubrey Cove Rezone, Ord 2021-08-Z): PC 2021-08-24 → Council 2021-09-07.
  **Real.**
- Other medium links (South Jordan Annexation, Streetscape Master Plan) carry
  subject_score 1.0 on matching project names. The 2 **low** links are left unquoted by
  design.

## 4. Election spot-check (independent, races NOT in Phase 5)

| Race | File value | Outside source | Result |
|---|---|---|---|
| **2017 Mayor** | Ramsey 6,454 (55.68%) def. Woolley 5,137 | South Jordan Journal / SL Tribune: "Dawn Ramsey led Mark Woolley 55-45%… replace one-term incumbent David Alvord"; primary Ramsey 39 / Woolley 34 / Cunningham 27 (matches our primary precinct rows) | **MATCH (winner + margin %)** |
| **2013 Mayor** | Alvord 5,226 def. Osborne 5,126 (final canvass) | KSL: Alvord edged incumbent Osborne by a razor-thin margin (election-night unofficial 4,691 / 4,672) | **MATCH (winner)**; count differs = final canvass vs election-night unofficial (provisional/absentee still uncounted on election night) — expected, same pattern as Phase-5 2019 |

**Precinct-sum reconciliation** (filtered by `election_type`): 2017 Mayor general
precinct rows sum to Ramsey **6,454** / Woolley **5,137** — exactly the race-file
`winner_votes`/`runner_up_votes`. 2013 Mayor general sums to Alvord **5,226** / Osborne
**5,126** (+ a handful of expected write-ins). **Precinct rows reconcile to race totals.**
(Naive whole-file sums must be split by `election_type`; primary+general share office
labels.)

## 5. Doc-drift sweep — found & fixed

| Drift | Where | Action |
|---|---|---|
| **VERIFICATION.md "40 race rows"** — actual is **41** (30 general + 11 primary) | `VERIFICATION.md` l.18 | **FIXED** → "41 race rows (30 general + 11 primary)" |
| **Root `CLAUDE.md` shipped with 5 unfilled template placeholders** — `{{CITY}}`×3, `{{COUNTY}}`, `{{WEEKDAY}}`, `{{WEEKDAY_NAME}}` (build never substituted them) | `CLAUDE.md` ll.1,3,13,17,37 | **FIXED** → "South Jordan", "Salt Lake" County, "Tuesday" (MEETING_WEEKDAY=1, confirmed: 2025-06-17 is a Tuesday) |

All other doc counts already correct and match measured data — README: 243 council / 125
PC minutes, 730 PC motions / 797 rows / 353 named, **41 races (30+11)**, 111 candidate
rows, 2,062 precinct rows, 128 weeks, motions_std 1,029/730, 244 raw vs 243 indexed. The
remaining `{{…}}` hits in `db/*.py` are Python regex quantifiers (`{2,5}`), not
placeholders.

## 6. Conformance — `validate_city.py`

**19 PASS / 3 WARN / 0 FAIL.** All three WARN are documented source quirks, not defects:
- `a.layout` missing `all_comments_clean.csv` — comments are submit-only/unpublished
  (`public_comments/AVAILABILITY.md`), an honest empty.
- `f.tally[meeting_minutes]` 101/234 — 2020-2023 narrative style names only the dissenter,
  so the named subset can't sum to the printed tally; body's `validate_votes.py` finds
  exactly **1** real mismatch (the documented 2025-08-19 clerk error).
- `f.tally[planning_commission]` 0/205 — PC never prints a full Aye/Nay roster (dissenter/
  absentee only); `validate_votes.py` finds exactly **1** real mismatch (documented
  2022-10-11 clerk error).

## 7. Grades (city × dataset)

| Dataset | Grade | Basis |
|---|---|---|
| Council minutes | **A** | born-digital, screener-clean all years, faithful transcription |
| Council votes | **A** | 6/6 sampled council motions exact; tie-break + clerk error verbatim; 0 fabricated names |
| PC minutes | **A** | born-digital, screener-clean |
| PC votes | **A** | 4/4 sampled PC motions exact; clerk error + dissenter-only style preserved |
| Elections | **A** | 2 new outside-source winner matches; precinct sums reconcile to race totals |
| db | **A** | reconciles exactly (delta 0); motions_std 100%; referrals high/medium trace real |
| weeks/ | **A** | fresh, sums to council flat total |
| Public comments | **B (honest empty)** | AVAILABILITY.md documents exhaustive hunt; not gradeable as content |
| Geo | **B (present, not exercised)** | 5 district polygons + tool present (validator); not functionally driven this pass — see blind spots |

## 8. Completeness critic — this audit's blind spots

- **Geo tool** presence-verified only (5 polygons + `address_to_district.py`); not
  functionally run against known addresses this pass.
- **Public comments** honest-empty accepted from `AVAILABILITY.md`; not independently
  re-hunted on the portal.
- **Raw-PDF token diff:** born-digital faithfulness established via the statistical
  screener + line-level source greps on 10 motions, not a full `pdftotext -layout`
  token-diff of a random raw PDF (Phase 5 similarly relied on trace-checks; screener
  medians make wholesale text loss unlikely).
- **2026 motions** were screened corpus-wide but not individually ground-truthed (sample
  spans 2020-2025); the 2 **low**-confidence referrals were not traced (by design).

---

### SIGN-OFF

**READY.** The South Jordan repo passes the independent final gate: born-digital minutes
clean across every year in both bodies, 10/10 ground-truth motions faithful with zero
fabricated names, the mayoral tie-break and both clerk errors stored verbatim and flagged,
derived layers reconcile exactly (db delta 0, motions_std 100%, weeks fresh), referrals
trace to real PC→Council pairs, and two new outside-source election winners match with
precinct sums reconciling. Only two trivial doc-drift items were found and fixed
(VERIFICATION 40→41; root CLAUDE.md template placeholders). No data-level defects.
Build Phase 6.3 complete.
