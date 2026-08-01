# TODO_ARCHIVE — closed historical entries moved from TODO.md

This file holds fully-closed, purely-historical entries relocated from `TODO.md` on
2026-07-19 to keep the live queue readable. Nothing here is open work — open items,
partial (`- [~]`) items, honest gaps, and owner rulings all remain in `TODO.md`. Entries
still referenced by name from other docs (HANDOFF.md, NEXT_SESSION_PLAN.md) also kept a
short `- [x]` stub in `TODO.md` pointing here; SPLIT entries left their still-open
sub-items in `TODO.md` and moved only the bulk run-record here.

The verbatim pre-cleanup `TODO.md` is preserved at
`_backups/2026-07-19-todo-cleanup/TODO.md`. Entries below appear in their original
`TODO.md` order, grouped under their original section headers, verbatim.


## High priority

- [x] **Motion `disposition` derived column (approve | deny | continue | table |
      procedural)** — DONE FOR SLC 2026-07-12; **rollout to other 15 cities + county pending**
      (STATUS below). Surfaced 2026-07-11 during SLC PC analysis. The db records whether a
      motion *carried* (`motion.outcome` = Pass/Fail) and, for PC forwarded recs only, its
      direction (`motion.recommendation` = Positive/Negative — blank for all 426 PC final
      actions). But there is **no structured field for the project disposition** — whether a
      passing motion *approves or denies* the underlying matter. A "Reject the ordinance"
      motion that Passes = project DENIED with `outcome='Pass'`, and `motions_std.action_class`
      only encodes the stage (recommendation/final-action/procedural), not direction. So every
      analysis of "how often did they approve vs deny" currently falls back to fragile
      `motion_text LIKE 'approve%'/'deny%'` string-matching (which left ~30% of one
      commissioner's Nays unclassifiable). **Fix:** compute `disposition` ONCE from
      `motion_text` + `recommendation` + `outcome`, materialize it as a derived column on the
      `motion` table (a normalization layer alongside the verbatim core — Cardinal Rule 2, like
      `motions_std`), with a `disposition_method`/`confidence` provenance pair and an override
      file for hand-corrections. Small, well-scoped. Prototype/validate on SLC (rich land-use
      taxonomy, both PC stages present), then generalize into `build_db.py` /
      `normalize_motions.py` so every city+county gets it. Unlocks clean approve/deny rates,
      PC-recommendation-vs-Council-disposition divergence, and per-member approval propensity
      without prose heuristics.

      **✅ STATUS — SLC DONE (2026-07-12):** Added `disposition` + `disposition_method` +
      `disposition_confidence` columns to the `motion` table in `slc_city_council/db/build_db.py`
      via a new `disposition_of(motion_text)` classifier. Design choice (matches the two-axis
      lesson): `disposition` records the **PROPOSED action only** (approve/deny/continue/table/
      procedural), NOT pre-composed with `outcome` — compose at query time so the two orthogonal
      facts stay separable (`disposition='approve' AND outcome='Pass'` ⇒ approved; `'approve' AND
      'Fail'` ⇒ not approved; `'deny' AND 'Pass'` ⇒ denied). Override file
      `db/disposition_overrides.csv` (source_file,motion_no,disposition,note). Distribution:
      approve 1,235 · procedural 1,004 · continue 197 · NULL 73 (legislative-initiation / officer-
      election / appointment / uncaptured fragments — honestly unclassified) · deny 51 · table 22.
      QC'd land-use edge buckets (no real approve/deny leaked to NULL/procedural). Rebuilt db +
      referrals + federated `cities.db`; validate_city PASS (25/1 WARN/0 FAIL). The original
      question is now a direct query (SLC PC land-use: 476 approved · 40 denied · 13 approval-
      failed · 4 denial-failed) — no `motion_text LIKE` heuristic.
      **✅ ROLLOUT COMPLETE — ALL CITIES (2026-07-12, T1.1):** the "port to each clone" framing was
      STALE — the 2026-07-07 refactor means 26 of 31 cities share `scripts/db_build_lib.py`, so the
      port was ONE edit to the lib (disposition block + 3 DDL columns + override load + INSERT +
      guard + cross-check, mirroring SLC) plus agent-ports into the 5 documented forks (millcreek,
      park_city, sandy, south_jordan, taylorsville). `scripts/build_cities_db.py` now federates the
      3 columns (has_disp guard: county rows honestly NULL). Rebuilt via `rebuild_derived.py --all`:
- [x] **AUDIT the motion-classification layer — DONE 2026-07-12 (T1.3), comprehensive.**
      31 parallel per-city ground-truth agents, ~500 motions checked against source minutes +
      per-city convention analysis + exhaustive small-class sweeps. **Full report:
      `_audits/2026-07-12-motion-classification/report.md`** (+ findings_raw.md). Verdicts
      pre-fix: FAIL 6 / WARN 25 / PASS 0 — found ~55 wrong outcomes across 21 cities in 4 root
      causes (majority-first "failed N-M" tallies — provo 11!; ties→Pass — 12 rows; clock-times
      parsed as tallies — holladay 8; tally-less item-fate 'Denied' inversions) + systematic
      disposition gaps (continue recall broken in ~14 cities; "Table of Uses" noun traps in 6;
      'defer' traps in 5). **ALL classifier-fixable errors (~40) fixed the same day in v3**
      (word-priority carriage, tie⇒Fail, clock-strip, disposition-composed 'den', verb-anchored
      continue/table + guards + lexicon; sandy fork keeps PC tally-priority for its Legistar
      PassedFlag artifacts; provo's `was opposed` extractor cue motion-anchored + re-extracted).
      Verified: 37/37 + 45/45 unit cases, 26/26 audited-row battery, all 31 INTEGRITY OK, the
      new guard reports exactly the 38 audited word-over-tally rows with 0 unexplained
      violations federated; continue class 860→1,296, false tables purged 655→433, Died visible
      (51); v_pc_divergence 80 divergences. ~15 residual wrong rows are UPSTREAM extraction
      defects — queued in "T1.3 upstream extraction defects" below. ✅ The method is now FOLDED
      into `/audit-city-data` (2026-07-12): new checklist module §2d2 (per-city result-
      string conventions, exhaustive small-class sweeps, disposition strata, dissent-
      coverage + plausibility invariants, build cross-check verification, continue/table
      recall probes) + 8 new failure-library rows from the T3.1 repairs.
- [x] **ROOT-CAUSE: separate "did the motion carry" from "recommendation direction" at
      extraction** — DONE FOR SLC 2026-07-12; **rollout to the other 15 cities + county still
      pending** (see STATUS below). Surfaced 2026-07-11 on the Yalecrest–Laird Heights historic district
      (PC 2023-09-13). Two paired motions on one item — a *positive*-recommendation motion
      that **FAILED 4–5** and a *negative*-recommendation motion that **PASSED 5–4** — both
      land in the db as `motion.outcome='Pass'`. The named roll calls extracted fine; the
      defect is that the PC extractor folds **two orthogonal facts into the single `result`
      string**: (a) whether the motion *mechanically carried* and (b) the *recommendation
      direction* (Positive/Negative, itself computed from action×carriage). A "forward a
      NEGATIVE rec that PASSED" and a "forward a POSITIVE rec that FAILED" **both stringify to
      `"Negative recommendation N:N"`**, so `db/build_db.py`, which derives `outcome` by
      interpreting that string, cannot tell them apart and defaults to `Pass` — even though the
      minutes state "The motion failed with 4 yes and 5 no" and the yes:no tally (4:5 vs 5:4)
      is unambiguous.

      **✅ STATUS — SLC DONE (2026-07-12):** Rewrote **`outcome_of()` in
      `slc_city_council/db/build_db.py`** to read the yes:no (PC `N:N`) / yes-no (council/agency
      `N-N`) tally as the authoritative CARRIAGE signal — tally-first, *after* the
      Continued/Died deferral keywords, with the old disposition-word matching kept only as a
      fallback for ties / no-tally rows. Added the **HARD guard (sub-item 3)** to `build_db.py`'s
      integrity block: the build now FAILS if any motion's `outcome` contradicts its yes≠no
      tally. Rebuilt `db/civic.db` + `build_referrals.py` + federated `cities.db`; PC vote
      validator PASS, `validate_city.py` PASS, INTEGRITY OK, referral count stable (31).
      **Result:** exactly **21 PC outcomes corrected** (14 Pass→Fail failed recs/approvals, 7
      Fail→Pass passed denials), **0 council/agency rows changed** (their result strings already
      carry an explicit Pass/Fail word — verified), contested count unchanged (277), and
      Yalecrest is now right (positive-rec 4:5 → Fail, negative-rec 5:4 → Pass). **Scope note:**
      sub-item 1's explicit `carried` column was deliberately NOT added — the yes:no tally is
      already present on every motion and IS the authoritative carriage signal, so the db
      derives `outcome` from it directly and the flat-CSV schema stays stable; an explicit
      `carried` column remains OPTIONAL hardening if a future city's result strings ever omit
      the tally.
      **✅ ROLLOUT COMPLETE — ALL CITIES (2026-07-12, T1.1):** the "each city has its own clone"
      framing was STALE — 26 of 31 cities share `scripts/db_build_lib.py` (2026-07-07 refactor),
      whose `outcome_of` still had the identical bug; fixed tally-first there + in the 5 documented
      forks (millcreek, park_city, sandy, south_jordan, taylorsville — byte-identical old bodies),
      HARD tally↔outcome guard (with supermajority-keyword exemption) added everywhere. Measured
      baseline before the fix: **126 outcome/tally contradictions across 21 entities** (provo 31,
      sandy 24, logan 10, park_city 9, holladay 9, draper 7, …; SLC + county 0 = already fixed);
      after `rebuild_derived.py --all`: **0 across all 31 city dbs AND federated cities.db**, all
      cities validate, v_contested_all 3486, v_pc_divergence 1085 pairs / 85 divergences.
      Baseline + method recorded in NEXT_SESSION_PLAN.md. Do not close until the
      motion-classification AUDIT below passes (per that item's instruction).

      Fix at the most fundamental layer, root-first:
      1. **Extraction** (`planning_commission/extract_votes.py`, mirror in
         `meeting_minutes/extract_votes.py`): record a first-class boolean **`carried`** per
         motion, taken from the explicit outcome phrase the parser *already* reads to anchor
         motions ("the motion passed/failed/did not pass") and corroborated by the yes:no
         tally. Store it as its own column in the JSON + `all_votes.csv`; keep `result`
         verbatim/city-faithful (Cardinal Rule 2) but stop letting it be the sole carrier of
         carriage.
      2. **DB build** (`db/build_db.py`): the confirmed locus is **`outcome_of()` at
         `build_db.py:170`** — it keyword-matches disposition words in the `result` string
         (`fail`/`den`/`continu`/`tabl`/…) and **never reads the yes:no tally**, so any
         recommendation result lacking a failure keyword defaults to `Pass`
         (`"Negative recommendation 4:5"` → Pass, though 4:5 yes:no = failed). Set
         `motion.outcome` from the explicit `carried` flag + tally, NOT by re-parsing the
         `result`/recommendation string. The `disposition` column above then composes
         {proposed_action, carried} → approve/deny/continue deterministically, with no
         ambiguity left to resolve.
      **Measured blast radius (SLC PC, 2026-07-11):** NOT a one-off — **21 of 740 PC motions
      have a stored `outcome` that contradicts their own yes:no tally**, in BOTH directions:
      (a) ~7 *"N:0 Denied (Final Action)"* motions — a motion to DENY that CARRIED — wrongly
      flagged `Fail` because `"den"` matches (the motion passed; the *project* was denied —
      proving `carried` and `disposition` must be separate fields); (b) ~14 recommendation/
      approval motions with yes<no (e.g. `"Positive recommendation 0:1"`, `"Negative
      recommendation 4:5"`) wrongly `Pass` because no failure keyword is present. `outcome_of`
      is applied to **every body and is cloned across all 16 cities' + the county's
      `build_db.py`**, so the true repo-wide count is larger (council/agency result strings
      use dash tallies `N-N`, not caught by this colon-only scan — audit both). Fixing it
      flips 21 SLC PC outcomes alone; re-verify contested/divergence figures after.
      3. **Validation** (`planning_commission/validate_votes.py` + `scripts/validate_city.py`):
         add a HARD check that every motion's `carried` agrees with its yes:no tally (yes>no ⇒
         carried, barring a noted supermajority rule) and FLAG any single item whose paired
         motions both read as carried. This would have caught Yalecrest automatically. Backfill:
         re-extract + rebuild the db and diff — expect only genuinely-failed motions to flip
         `outcome` Pass→Fail.
- [x] **Extend the referral / divergence layer to `Other`-typed legislative items — DONE
      2026-07-12 (T1.4).** Admitted into the application universe via `LANDUSE_RE` in
      `scripts/db_build_lib.py` + the 6 forks: `historic district`, `landmark site`,
      `(small|station) area plan`, `master plan` (+ `(Local )?Historic District` in NAME_TYPE
      for named-app grouping). **"historic preservation" deliberately NOT admitted** — sampled
      corpus-wide, it matches HP-board APPOINTMENTS and proclamations, not designations (the
      procedural-Other guard the item required). Rebuilt all dbs + referrals + refederated:
      **+46 referral links across 11 cities** (slc 31→40, st_george +21, vineyard +4, wj +4…),
      federated v_pc_divergence 1085→1120 pairs / 80→83 real divergences, and **the flagship
      Yalecrest–Laird Heights chain is now queryable end-to-end** (PC 2023-09-13 negative rec
      [positive-rec motion Failed 4:5, negative-rec motion Passed 5:4 — both fixed by T1.1/T1.3]
      → Council Ord 09 of 2024 adopted → `diverged=1`). Spot-checks per the item's instruction:
      all 13 new SLC links reviewed — 4 FPs suppressed in `db/referral_overrides.csv` (the
      Princeton-vs-Laird district confusion, 2 documented boilerplate classes, generic
      design-review tokens) + SLC's `build_referrals.py` now passes
      `extra_stopwords=("design","review")` to kill that FP class at the root (69 generic PC
      design-review apps chain-linked otherwise); st_george's 21 sampled — all genuine
      (same-parcel zone/plat/hillside pairs; one renamed project correctly at low/flag-only).
      lehi -1 = re-scoring noise. Contested counts unchanged (3486).


## Known acquisition gaps (watch for sources appearing)

- [x] **Ogden separate 2022–2023 RDA & MBA minutes** — RESOLVED 2026-07-06 via `ogden_city_council/
      pmn_backfill/`: **7 of the 2023 RDA minutes recovered** from PMN (they existed after all — filed
      under Ogden's combined PMN body 6587, not the 6-month-capped RDA-321/MBA-322 pages). **2022 RDA/MBA
      and 2023 MBA confirmed NOT on PMN** (only budget/bond notices) — honest zeros, likely acted in-council.
      Recovered RDA minutes flagged for promotion into the audited `meeting_minutes/` layer.

## Extraction / data quality follow-ups

- [x] **Provo PC 2020-2024 ROA integration — DONE 2026-07-10.** The recovered per-item
      Reports of Action in `provo_city_council/pmn_backfill/` (2020-2024, the PC record the
      city never published as minutes) are now structured into `planning_commission/all_votes.csv`
      via new `extract_roa_votes.py` (reuses the audited `extract_votes.py` ROA parser). Added a
      **`provenance`** column (`minutes` vs `pmn_roa`) threaded through `all_votes.csv` →
      `db/civic.db` `motion.provenance` → `cities.db` (`motion.provenance` + `v_contested_all`).
      +381 PC motions / ~2,528 vote rows; PC now spans 2020-01-08→2026-06-24. Lit up the
      previously-empty Council←PC referral layer (0→150) and `v_pc_divergence` (0→88). validate_city
      provo 23 PASS / 0 FAIL. Backups in `_backups/2026-07-10-provo-pc/`.
- [x] **West Jordan PC 2021-04→2022-07 backfill — DONE 2026-07-10.** `planning_commission/extract_backfill_votes.py`
      reuses the audited WJ PC parser over the 28 recovered standalone PC minutes (2021-04-06→2022-07-05,
      pmn_backfill) and merges with `provenance` (`minutes` vs `pmn_minutes`). +44 named motions / 60
      dissent+absent rows (tally-only, no ayes — matches WJ convention); PC now 2021-04→2026-04. validate_city
      23 PASS / 0 FAIL. Backups in `_backups/2026-07-10-wj-pc/`.
- [x] **Shared `slco-election-archive` `normalize_sovc.py` bug — FIXED 2026-07-12 (T1.2).**
      Root-caused differently than filed: the 2011-general sheets were ALREADY parsed into the
      long file (an earlier archive re-run fixed that half), and the "missed 2019" was TWO
      stacked defects: (a) the archive parsed 2019 sheets with the wrong layout family —
      candidate names sit on the row ABOVE the sub-header, so Family A read the vote-METHOD
      labels ("Vote By Mail") as candidates — fixed with a new **`parse_family_b()`** in the
      archive normalizer (verified: SJD Council 2 → MARLOR 1161 / QUINN 764, EXACT match to
      SJ's audited races; all other years byte-stable); (b) downstream,
      `salt_lake_county/elections/build_elections.py` never matched the clerk's era variants —
      2019 3-letter sheet codes (`SJD`/`KRN`/`WVC`…), 2011 `Coun`/`CNCL`/`@ Lg`, abbreviated
      names (`S Salt Lake`, `CTTNWD HGHTS`) — fixed with per-city era-variant patterns, a
      normalization pre-pass, a special-district guard (TRUSTEE/IMPROVEMENT/WATER/… never a
      city office), and a kearns entry. County-grain coverage recovered: **2019 went 0 → 127
      rows; 2011 +120; 2017 +104**; refederated into `election_result`. Still-unparsed archive
      layouts (honest gaps, listed by the normalizer's own TODO output): 2019 municipal
      PRIMARY, 2018/2020 generals, 2002–2006 era.
- [x] **SLCo raw-SOVC re-parse — COMPLETED 2026-07-16 (landed just past midnight 07-17).**
      New `parse_family_d()` (numbered-sheet/ToC era) in the archive normalizer parses the
      2019 municipal primary (32 contests/3,103 rows) + 2018/2020 generals (66,587 + 84,062
      rows); 39/39 pre-existing file-groups byte-stable; 9/9 exact-match vs audited races
      (bluffdale/midvale/riverton/SSL — winners, votes, totals). County layer landed:
      `slco_municipal_results_long.csv` 245,719 rows, `election_results_by_contest.csv`
      +121 rows (all 2019 municipal primary, 15 cities), 0 changed/removed; elections
      CLAUDE.md + raw/SOURCES.md updated. Cycle dispositions: **CH-2019 D1 / holladay-2019
      D4+D5 / kearns-2019 D3 / murray-2019 D1+D3 / herriman-2019 D4 primaries RECOVERED**;
      EC/copperton 2019 generals were already recovered by T1.2 (those per-city "re-parse
      2019 SOVC" leads were stale — data is in the county layer, only the audited per-city
      rows remain); **murray + herriman 2021 MAYOR primaries recovered contest-grain** from
      the county's ONLY publication (election-night PDF, archived
      `slco-election-archive/raw/2021/2021-08-10-primary-election-results.pdf` — no 2021
      primary SOVC workbook exists); murray 2021 D4 primary never held (Galt pre-cert
      withdrawal, field of 2); **SSL 2021 mayoral primary NEVER EXISTED (RCV pilot — SSL
      election_results/CLAUDE.md "acquisition gap / almost certainly held" claim is wrong,
      doc fix needed)**; **magna 2023 D1/D3/D5 CANCELLED (Res 2023-09-02 under 20A-1-206,
      verbatim in 2023-09-26 minutes — Prokopis/Sudbury/Pierce deemed elected eff.
      2024-01-01; NOTE magna roster/council_terms.csv marks Sudbury D3 "APPOINTED" — should
      be elected-by-cancellation)**; **alta 2025 general CANCELLED (Res 2025-R-26, 2025-09-10
      minutes — Bourke/Anctil/Heimark deemed elected after Byrne + Moxley withdrew; absent
      from SOVC AND ballot-level CVR, county record correct)**. Proposed audited-layer rows
      for murray (2019 gen ×3 + 2019 prim ×2 + 2021 mayor prim), CH, holladay ×2,
      herriman ×2, copperton ×3, EC, kearns + the two cancelled-election certification
      entries are REPORTED, owner-gated, NOT applied (kearns precedent). Backups (verified
      intact): `_backups/2026-07-16-sovc-reparse/`. Residuals: 2021 primary precinct grain
      unpublished by county (ENR PDF is contest-grain, 6 contests, complete); 2020 primary +
      presidential primary (SpreadsheetML .xls, no municipal content); 2002–2006 era;
      1996–2001 PDFs; 2025 CVR loader. **Federation deliberately NOT run** (concurrent
      session) — the +121 rows reach `election_result` at the next `build_cities_db.py`.
      *(Landed: the 2026-07-17 vision-pass federation carried the +121; verified in
      `election_result`.)*

      **[x] Audited-layer SOVC-reparse rows APPLIED 2026-07-17** (owner-approved; kearns
      precedent; backups `_backups/2026-07-17-audited-election-rows/`). 21 rows across 9
      cities: murray (2019 gen D1/D3/D5 + 2019 prim D1/D3 + 2021 Mayor prim [ENR-PDF
      contest-grain]), CH (2019 prim D1), holladay (2019 prim D4/D5), herriman (2019 prim
      D4 + 2021 Mayor prim), copperton (2019 gen A/B/C), kearns (2019 prim D3),
      emigration_canyon (2019 gen At-Large 3-seat — module already existed, premise
      corrected; canvass-confirmed n_seats=3), magna (2023 D1/D3/D5 cancelled-cert), alta
      (2025 Mayor + Council cancelled-cert, Res 2025-R-26 instrument-verified). All
      25-col, byte-stable appends, validator 0-FAIL ×9, tallies re-verified twice against
      the county layer. Doc corrections riding along: murray "No 2021 primaries" (Mayor
      prim held / D4 never held — Galt pre-cert) → **CF 2021-primary lead RESOLVED**; CH
      "no 2019 primary" → **CF Petersen/Case/McHugh lead RESOLVED**; EC 2019 gap CLOSED.
      **Cancelled-certification convention CODIFIED in SCHEMA_SPEC** (races section,
      2026-07-17): winner recorded, all 11 vote/pct/turnout columns blank,
      `uncontested=True`, note leads with `cancelled_certification (Utah Code 20A-1-206;
      Res <no>)`. Residual: `results_by_candidate/by_precinct` sidecars not extended
      (candidate detail lives in race notes).

      **[x] EC elections generator PATCHED 2026-07-17** (the one hand-edit-in-a-derived-
      file violation, repaired same day): `build_emigration_elections.py` now regenerates
      the 2019 At-Large row itself — root cause was the `EMG At-Large` sheet-code name
      never registered in its GENUINE set (the long-file tallies were ALREADY
      un-suppressed by the 2026-07-12 normalizer fix); a dormant contest-file fallback is
      wired for re-suppression. by_candidate/by_precinct now also carry 2019; all other
      rows byte-identical; idempotent; 0 FAIL. Two better-sourced diffs vs the hand row
      (true sheet-era `contest_verbatim`; regenerated note). Backups
      `_backups/2026-07-17-ec-generator-patch/`.

      **[x] Roster corrections — cancelled-election certifications + EC 2019 recovery,
      2026-07-17.** magna Prokopis-D1/Pierce-D5/Sudbury-D3, emigration_canyon
      Brems-AL2/Hawkes-AL3/Harris-AL4, alta Heimark-AL1/Anctil-AL2/Bourke-MAYOR corrected
      in-driver from "appointed / held-over / county-gap / UNDETERMINED" to
      certified-/re-elected, citing the `*_races.csv` cancelled-certification rows +
      resolutions + oath minutes (alta's Bourke-2025 "re-elected? UNDETERMINED" standing
      question RESOLVED by Res 2025-R-26). Consecutive-term SPLITS per the holladay
      precedent (per-term vote clamping); EC's genuine 2018 appointed segments RETAINED
      as separate rows. Term counts: magna 17→19, EC 16→18, alta 11→13. Rebuilt,
      validated, idempotent, 0 election-crosscheck drift; backups
      `_backups/2026-07-17-roster-corrections/`. Federated 2026-07-17.
- [x] **West Jordan 2021 city campaign-finance forms: multi-report re-transcription.** ✅ **CLOSED
      2026-07-12** via `/cf-vision-transcribe` Read-tool agents ($0 API; page-range partials preserved in
      `vision/_partials/`). Queue was part-stale: 3 of 9 (Heath 49931082, Smith 3c4c23ca, Bloom b3345e08)
      already had `reports[]` caches. The 5 flat `_recovered` PARTIAL bundles (Lamb, Whitelock Final-Amended,
      Green, Withers, Fields) were fully re-transcribed — **several bundle THREE reports, not two** (Lamb/
      Whitelock-FA/Green/Withers: pre-primary + pre-general + final; every balance chain verified). Whitelock
      P+G (66bf742b) turned out to be a 2-report bundle too (the 07-06 "SINGLE report" hand-verify note was
      wrong) — upgraded to reports[] with its Aug-2 primary report. All merged caches cross-foot to the printed
      attachment totals exactly. Cycle impact: Lamb 379.27→**6,577.00/5,998.12**; Green 1,500→**26,713.35/
      20,301.73**; Whitelock cycle = the Final-Amended summary **2,300.00/3,140.54** (restated periods NOT
      double-counted — latest-summary basis). Verifier findings, all page-proven: Heath's +365.16 = he zeroed
      his own itemized self-loans on lines 2-4 (plus a real $2.00 misread, fixed); Smith's −466.19 = in-kind
      total inside line 4 + a $25 filer omission; Bloom's −25 = a $50 cover-vs-attachment inconsistency + a $25
      self-loan she excluded from line 4; **the "Whitelock $2,637.99" stated-total misread NEVER EXISTED — the
      07-06 hand-verification note was itself the misread (400dpi: the cover prints $2,637.49, and Attachment B's
      typed TOTAL corroborates)**. Withers' filer-struck $2,257.50 expenditure row excluded (the source's own
      deletion, documented). Fields' final re-lists the interim's rows under a no-new-activity cover (Springer
      pattern, honest flag). Group C: 3/9 reconcile clean; the 6 flags are all decomposed, page-verified filer
      artifacts. PASS validation; `contributions.csv` 601 / `expenditures.csv` 866 rows repo-wide for WJ.

## Expansion & routine operations

- [x] **Millcreek campaign-finance vision backfill (2026-07-06):** ✅ **CLOSED 2026-07-12.** The "28 still
      need vision" list below was STALE — all 28 caches were built and consumed the same evening (2026-07-06
      22:14/22:23; filing_totals already reflected them: 28/41 both-sides, not 10). This session re-verified the
      5 big-delta filings by full Read-tool re-transcription (1215, 2676, 2682, 4097, 5763): **zero missed rows**.
      Deltas explained at source: Vice/DeSirant cover totals are **CASH-ONLY** (in-kind excluded — 1,700.00 /
      1,865.18 / 5,998.00 / 750.00 exactly); 4097 = amended-to-zero re-list (the Springer 4040/4104 pattern,
      honest flag); 2676 expend 293.22 = 2× two positive credit rows the form nets but the build sums as
      magnitudes (honest flag); 1215 got one real fix (FundHero fee 37.28 not .26) + 3 donor-name spellings.
      `scripts/campaign_finance/driver.py` gained an **alternate-convention reconcile fallback** (cash-only vs
      incl-in-kind, fires only on an exact match, notes the convention per filing) since millcreek filers MIX
      conventions (Jackson/Clark/Gray covers include in-kind). Result: **30/41 both-sides reconcile** (1215 +
      5763 flipped fully; 2676/2682 contrib side now exact), PASS validation; remaining 11 flags all documented
      source-side. **`cycle_totals` still deferred** (per-period "summary" reports — see below). Original entry:
      structured layer BUILT — new `millcreek_form`
      family (F9; "FINANCIAL CAMPAIGN REPORT" Form A/B; 3-column LAST/THIS/CUMULATIVE cover box; 2021 =
      cumulative bundle `is_incremental=False`, else per-period `True`; interior subtotal lines dropped). 41 filings,
      **10 both-reconcile**, PASS validation; 6 born-digital 2025 + the 2023 D3 race (Jackson ×3 + Springer 3928,
      Read-tool vision). **28 filings STILL NEED VISION** (cf-vision-transcribe → `vision/<doc_id>.json`): all 2019
      (1215,1285,1216,1274,1221,1284,1218,1272,1219,1282 — 1285 is a bare-decimal born-digital, rest no-text-layer
      scans); all 2021 (2676,2677,2678,2679,2680,2681,2682,2683 — handwritten + the Bagley duplicate two-report
      bundle); Holz 2023 ×3 (3931,4039,4097 — city-redacted, contributions partial by design); 2025 messy
      (5766,5805,5761,5806,5763,5801,5898). **Do NOT re-vision Gale 5762** (real 10¢ source inconsistency, faithfully
      parsed) or **Springer 4040/4104** (honest $0 no-activity periods). **`cycle_totals` deferred** — Millcreek
      "summary" reports are per-period (cumulative lives in cover box), so treat as fully-incremental OR read the last
      report's cover CUMULATIVE column, NOT the default "summary=cumulative" rule, before running the rollup.
      Follow-up option: extend `millcreek_form` to parse the bare-decimal/vertical variant (1285, DeSirant 5898/5801)
      instead of vision. *(Framework: `validate_finance.py` reconcile check now rounds the delta to cents to match the
      driver + SCHEMA "≤$0.01" — fixes a float-boundary FAIL; no city regressed, re-verified WV+Provo PASS.)*
- [x] **Ogden campaign-finance vision backfill (2026-07-06):** ✅ **CLOSED 2026-07-12.** Choberka 17487 turned
      out already vision-cached (True/True since 07-06); the real queue was 5 filings / 142pp, transcribed via
      12 parallel Read-tool page-range agents ($0 API) → merged `vision/<docid>.json` (page-range partials
      preserved in `vision/_partials/`). **Castillo 31387**: the packet bundles ORIGINAL + AMENDED versions of
      four reports; the packet's own balance chain proves the amended set operative (Dec-5 fwd 22,482.48 = the
      amended chain's ending; the original chain's 19,625.27 is continued by nothing) — superseded originals
      excluded from the summed cache (fully documented in cache notes; rows preserved in _partials) →
      reconciles **0.00/0.00 both sides** at 50,701.56 / 32,991.11 (was −97,125.34/−63,324.53). **Andersen
      30766 + Myers 30779**: reconcile exactly. **Graf 30773**: honest flags — contrib +99.70 (overwritten
      Weil-row digit) + expend +0.06 (the source total's own 6¢ misprint); its handwritten ledger-dash amounts
      ("100.-" = 100.00) are normalized deterministically in `_vmoney` (cache stays verbatim). **Van Wagoner
      30783**: expend exact; contrib +2,530.00 = 1,530 in-kind excluded from printed schedule totals + a
      **$1,000 filer arithmetic error** on the Sept-25 schedule (rows verified against the page image: sum
      3,870 vs printed 2,870, error carried into the summary sheet) — kept verbatim, flagged. **25/38
      both-sides reconcile** (was 21); PASS validation; `cycle_totals.py ogden` regenerated (D4 2023 = a ~$60k
      race: Graf 30,581.72 vs Van Wagoner 30,086.50 raised). Remaining small-delta vision flags (Caldwell,
      Richey −65/−30, Blair-2023, nil-side Hyer) stay characterized honest flags — re-inspection is a lead, not
      a defect. Born-digital honest-flags (Gladwell garbled text layer, White/Knuth appended ledgers, Martinez
      re-filed duplicate reports, Nadolski incomplete report #3) are source-quality, not extraction bugs.
- [x] **West Valley City campaign-finance vision backfill (2026-07-06):** ✅ **CLOSED 2026-07-12** via
      `/cf-vision-transcribe` Read-tool agents ($0 API). ADID3518 already had a 07-06 cache (part-stale queue);
      its −$9,880 contrib gap was a **cache misread, now fixed**: PAI Managers LLC 6/28 is **$10,000.00** not
      $100.00 (filer writes big round amounts without decimals) + Mark Yates $15 not $10, leaving a verified
      **$25 candidate arithmetic error** (his general-period rows outgrow his cumulative cover by $25 — kept
      verbatim, flagged). ADID3520 (primary) + ADID3519 (general) transcribed fresh: 3520 reconciles EXACTLY
      (18,030.00/12,311.13); 3519's expend exact, contrib +$75 honest. ADID3558 (Amosa) reconciles exactly —
      the cover DOES print the expense total ($78.68); OCR had simply missed it. **Structural finding: Buhler
      files CUMULATIVELY** (the general/final Form A photocopies the whole cycle's schedules) — summing his
      period filings double-counts, so `cycle_totals.py` gained a cumulative-restatement rule (latest interim's
      stated raised == summary's ±$1 and spent ≤ summary's ⇒ basis=summary); Buhler 2021 Mayor = **$27,584.45 /
      $26,717.47**, no false MIXED flag. The same rule corrected a live south_jordan double-count (Noah Barrett
      2025: 680→340, his 7-day report restates the 28-day). Bonus: the driver's in-kind fallback flipped LeFevre's
      2 filings (her documented in-kind-excluded covers) → **WV now 69/105 both-sides reconcile** (was 65), PASS.
      Remaining flags are the documented candidate-arithmetic/OCR-floor set. cycle_totals review_flag: Don
      Christensen 2023 (summary vs summed-interims) still stands.
- [x] **Mandatory PMN cross-check in every refresh (owner-approved 2026-07-13) — BUILT,
      ROLLED OUT ALL 31 CITIES, FOLDED INTO /refresh-city, 2026-07-17.** The full 6-step
      plan executed in one session: (1) shared engine `scripts/pmn_crosscheck.py`
      (city-agnostic, read-only, report-only; per-city `pmn_backfill/pmn_bodies.csv` +
      `pmn_exceptions.csv` configs; flag classes missing_minutes/agenda_only_gap/
      count_mismatch/new_body/renamed_body; live body-list diff; 60-day pending-adoption
      window; per-body floors incl. township recovered-floors); (2) 3-city pilot
      (bluffdale false-positive test 68→0 noise + 3 GENUINE leads; murray recall test
      PASS; herriman metadata-noise test PASS); (3) configs seeded for all 31 (5 agents,
      zero-network transcription from each pmn_backfill's own docs — two prompt-recall
      errors corrected against docs, ogden's combined-body-6587 structure caught,
      millcreek's stale fetch_new council id 1031→5741 caught); full engine run all 31
      (640 first-run flags); EVERY flag verified by 7 verification agents (flag →
      recovery lead | exception row | hardening candidate; never ambiguous);
      (4) looped hardening: `scripts/pmn_crosscheck_HARDENING.md` — 3 pilot fixes +
      post-verification adjudication (APPLIED: attachment-filename-date rescue [17
      instances], postpone/attachment-cancellation detection, 8 non-meeting title
      families, the 'Minuteman' word-boundary bug, doc-extension gate; DEFERRED with
      reasons: notice-body cancel fetch, count_mismatch config [ogden's were GENUINE],
      repo_datasets widening); (5) folded into `/refresh-city` §1b as the mandatory
      post-probe step (review gate: NEVER auto-ingest); (6) dated flag archives under
      `_crosscheck/history/` accumulate per-city lag data — revisit the 60-day window
      after 2-3 cycles. **Steady state: 640 → 317 flags = the verified genuine-leads
      inventory** (park_city + sandy verified CLEAN supersets; SSL 122→1). Exception
      ledgers: ~215 verified rows across 29 cities.
- [x] **RECOVERY + EXTRACTION + CF WAVE — 2026-07-17 (same-day execution of the
      crosscheck's fetchable-now tier + queued extraction follow-ups + CF vision
      tranche 1; 11 agents, one boundary rebuild + federation).** Results:
      **48 meeting records promoted across 12 cities** (murray 20 [budget/CoW/specials
      incl. Carbon Free Power + 2 CoW motions], slc 4 [minutes-only, LLM vote extraction
      queued], CH 5 [+16 rows incl. the 2023-03-08 PC full roll], EC 3 [+8 rows, NEW
      4-1 Bowen dissent], magna 3 [honest 0-motion workshops], nephi 8 [+14], SJ-PC 1
      [+6], provo 1, WVC 1 [+2], ogden 9-sibling reverse-combined family [+44 rows
      incl. a NEW 5-1 Choberka dissent + the un-ingested 2025-01-07 meeting], lehi 2
      [pmn_backfill by consistency ruling], SSL 1 [the no-quorum PC record]).
      **7 leads correctly REJECTED** (agenda-only notices ×4, a court-reporter
      transcript mis-dated + mis-labeled [WVC 2022-01-28 retreat — transcripts/-layer
      candidate], duplicates). **Extraction fixes:** herriman PC T3.1(j) sync (verified
      no-op + a PC-grammar guard that PREVENTED a tally corruption; extractors now
      differ by 1 documented line — ratified); draper PC narrative-era recovery (+23
      rows/+32 named, contested 214→220, the hidden 4-1 Squire dissent captured); EC
      seconder regex (115 fills, byte-stable otherwise); SSL roster refresh (3
      historical corrections, current roster unchanged) + 2 documented Huff typo
      overrides (INERT — see mechanism follow-up below). **CF vision tranche 1
      (2025 cycle, 6 cities):** 92 caches / 1,209 contributions + 846 expenditures
      itemized, $0 API; structuring owner-gated (no build_finance.py exists in the 6).
      **Federation:** motions 52,510→52,567, votes 182,984→183,063, contested→3,689;
      all 3 new dissents verified queryable; 193/31 intact; ogden crosscheck 15→6
      (count_mismatches CLEARED — engine's backfill-folding confirmed); all 14 rebuilt
      cities validate clean. Backups: `_backups/2026-07-17-{pmn-leads-recovery,
      extraction-followups,ssl-bundle,cf-vision-t1}/`.
- [x] **CF-STRUCTURING PACKAGE — 2026-07-17/18 (owner-approved): the structured money
      layer for all 14 vision-cached wave cities (pilot midvale + 13-city fan-out +
      one federation).** Protocol held again: solo Fable pilot (allowed shared edits)
      → 13 city-local Opus agents (scripts/ read-only; one relaunch round after a
      2026-07-17 session-limit interruption killed all 13 pre-write — verified clean,
      relaunched with the dying agents' recon folded into the briefs) → cycle-totals
      byte-stability check → ONE `build_cities_db.py`. All 14 `validate_finance.py`
      PASS; all cities `validate_city.py` 0 FAIL.
      - **Shared additions (pilot, no-op proven):** `scripts/campaign_finance/
        vision_lib.py` (verbatim money/date normalization, `sha1(index_path)[:8]`
        cache keys, multi-report `reports[]` bundles with Column-A restatement
        exclusion, per-candidate `detect_regimes` with a chain-evidence gate — the
        "blank trailing scan crowned cycle total" hazard), `families/vision_cache.py`
        (F10), `driver.py` callable `dedup_mode`. taylorsville+west_jordan+millcreek
        rebuilt under the new code: 9/9 CSVs byte-identical. Rollout template:
        `scripts/campaign_finance/VISION_CITIES_ROLLOUT.md`.
      - **Federated result:** cf_filing 1,070→**1,843**, cf_contribution
        13,266→**18,834**, cf_expenditure 11,003→**14,959**, cf_cycle 463→**813**
        candidate-cycles across **29 cities**; 660 candidates, 211 person-matched;
        integrity ok / reconciliation exact / 193-31 intact. Override REASONS
        federate with the rows (self-documenting cycle totals).
      - **Headline catches (each documented in its city's CF CLAUDE/overrides):**
        holladay Fotheringham-Mayor 2025 — the generic summary rule was DROPPING his
        ~$17k final period (cycle now $49,825/$50,242.65, balance-chain-verified);
        SSL Pinkney $3,075→$29,665.90 (YTD-not-sum, 10 overrides); CH Weichers
        $33,700 (3 disjoint periods summed); white_city — the "Shelton $400/Denning
        $978 not itemized" wave-2 note was scanned-subset-scoped: the born-digital
        text filings DO itemize them (Flint mayoral runner-up $0→$3,550); murray
        Dominguez "2019 re-upload" cache note = FALSE ALARM (form header + received
        stamp prove 2023; ~$9.7k stays); riverton Buroker "$3,000,00" typo = 100×
        phantom (flagged verbatim, cycle unaffected via printed Column E); bluffdale
        Pavlakis bundle = amendment+original of the SAME period (collapsed, not
        summed) + a "superseded"-in-note string-match bug fixed; EC Bowen bundle
        re-visioned ($0→$55); alta Bourke $2,000 is IN-KIND per the raw form
        (Abundance conservatively `business`, flip to `pac` only on registration
        evidence); herriman ~$112k captured incl. a city-local §10-3-208 text parser.
      - **Regime/in-kind decisions are PER-CITY and evidence-cited** (printed by
        every build): cash-only covers in magna/holladay/murray/riverton/herriman;
        all-sum in midvale/kearns/CH; MIXED in bluffdale (driver fallback).
- [x] **WAVE-2 — 2026-07-17 (night): shared-lib add-member overrides + the 21-agent
      per-city wave (agenda-grade recovery / primary-docs residue / CF tranches 2+ /
      wave-1 extraction follow-ups) + single federation.** Protocol: Phase 0 solo
      shared-file work → 21 parallel per-city agents (2 Fable: cottonwood_heights,
      slc; 19 Opus), strictly city-disjoint, no shared-file edits, no mid-wave
      federation → ONE `build_cities_db.py` at the end. All 21 validated **0 FAIL**.
      - **Phase 0 (solo):** (1) vote_overrides **add-member** mechanism in
        `db_build_lib.py` + `validate_city.py` formula (see follow-up (a) above —
        SSL Huff rows now live; SCHEMA_SPEC invariant rewritten); (2) SSL
        `fetch_new.py` **no-quorum minutes detector** (header+title+no-meeting
        grammar, no vote lines; tested positive/negative).
      - **Recoveries (4 cities, +~104 motions):** west_jordan **27 of 28** 2020-01→
        2021-03 standalone PC meetings — NEW CHANNEL: legacy `assets.westjordan.
        utah.gov` PDFs mapped via the WordPress REST route `/wp-json/wjc/v1/
        data-meeting/<post_id>` (PrimeGov migration dropped pre-2022 PC; PMN
        agendas-only); **NEW provenance value `citysite_minutes`** (40 motions; root
        CLAUDE.md bullet updated); PC motions 203→287, +57 member rows (10 Nay/47
        Absent, ZERO named Ayes — ceiling preserved); the 28th + a council sibling =
        COVID cancellations (exceptions, not gaps). magna: **4 of 9** COVID-cluster
        council minutes (+16 motions; 2 found EMBEDDED in the next meeting's approval
        packet — page-range sidecars); 5 dead (audio survives). cottonwood_heights:
        **2024 PC hole CLOSED** — 20 docs (16 delisted-but-live CMS docs found via
        Wayback listing anchors, 1 wayback_minutes, 3 scattered 2022 incl. a NEW
        contested 2022-10-19 PC 5-to-1 Ebbeler Nay; 1 "PC" doc content-verified as a
        council work session), +79 rows; Dec-2022 council proven GRAMA-only. midvale:
        2023-01-11 PC from a Revize URL variant (+3 motions/+9 rows).
      - **CH extractor (bare-name rolls):** +130 named rows corpus-wide, 0
        motion-level changes; NEW dissent 2024-03-05 (Weichers No) — see (b) above.
      - **Dead-lead ledgering (12 cities, 0 recoverable — honest gaps):** vineyard 5,
        logan 16, taylorsville 12, st_george 14 (both implausible dates resolved:
        1 PMN metadata error, 1 Thanksgiving cancellation), alta 14, herriman 6
        (2 genuine 2023 special-district hearings), riverton 6 (+ "0 still-missing"
        claim corrected), bluffdale 2 (both APPROVED-but-unpublished, approval traced
        to consent items; claims corrected), white_city 4 (all FPs), copperton 6,
        kearns 1 (2025-01-13 skipped by the city's own approved series), EC 17.
        Per-city GRAMA drafts in each agent report / pmn_backfill notes.
      - **Primary-docs residue:** draper 243 CLOSED, murray 34 + SSL 72 + bluffdale
        60 targeted packets (see the primary-docs item above); riverton Timberline
        auth-wall dispositioned (5 sibling rows corrected — see that item).
      - **CF vision tranches 2+:** ~290 new caches across 14 cities ($0 API): the
        6 tranche-1 cities' 2021/2023 backlogs (CH 12, herriman 20, holladay 13,
        midvale 24, murray 36+Evans docx, riverton 17) + 8 NEW city layers (SSL 40,
        bluffdale 54, kearns 38, EC 29, alta 21, copperton 19, magna 13, white_city
        10). All midvale/WJ-convention `sha1(index_path)[:8]` keys; verbatim
        transcription, filer defects preserved. HEADLINE DEFECT (riverton): the state
        mis-published HAYMOND's 10-24-23 report under PIERUCCI's filename — would-be
        Pierucci cache DELETED (anti-fabrication), AVAILABILITY discrepancy #6,
        re-acquisition queued below. holladay "bradley" = tranche-1 misdiagnosis
        (see (e) above).
      - **Federation (one run):** motions 52,567→**52,667**, votes 183,063→**183,349**,
        contested 3,689→**3,700**, fts_packet 13,196→**13,603** (+407 = exactly the
        4 packet agents' sidecars); integrity ok / reconciliation exact /
        `v_council_current` 193/31; recovered-provenance motions now **2,287** incl.
        `citysite_minutes` 40; new dissents verified queryable (CH Weichers, CH
        Ebbeler, SSL Huff add-member rows); midvale motions_std backfilled (672=672)
        before federation; coverage.json regenerated. Backups:
        `_backups/2026-07-17-wave2/` (per city + scripts).
- [x] **Q3-2026 QUARTERLY REFRESH — 2026-07-19 (first full run of the routine; 23
      parallel city agents + one federation; every agent 0 FAIL).**
      **Probe:** 31/31 portals ok, 0 failures. **Crosscheck:** 75 flags across 15
      cities — ALL worked to zero through the review gate. **Ingested: ~62 minutes
      docs across 14 cities** → federated motions 52,667→**53,010** (+343), votes
      183,349→**185,111** (+1,762), contested 3,700→**3,726**; fts_minutes
      10,401→10,463; integrity ok / reconciliation exact / 193-31 intact;
      coverage.json + refresh_status.md regenerated.
      - **Notable ingests:** slc 16 docs (+444 rows: FY26-27 budget formal Ords
        27–40; RECOVERED the contested 6-1 Res 32 of 2021 COVID/mask extension,
        Rogers Nay, from a title-filter gap; PC 3:2 Definition-of-Family); orem 5
        OCR'd council (+288 rows, contested +3); park_city 4 council (+174);
        st_george 3+1 (+174); CH 3 flag-recoveries (incl. a full 2025-06-03 council
        mtg PMN mislabeled as a budget notice, +88 rows); west_valley 7; sandy 3
        (+139; PC drafts correctly deferred — 0 EventItemVote yet); nephi 3 (incl. a
        flag-recovery + NEW PC 4:1 Thomson dissent); ogden 3 (2 hand-OCR'd); logan
        1 (draft convention; NEW 5:1 Maughan dissent); lehi/millcreek/SJ/holladay/
        SSL/herriman/WJ singles. All backfill re-runs honored (WJ 117, ogden 197,
        herriman 272 recovered rows preserved).
      - **Defects found + FIXED (city-local):** slc scrape rebuild_index flipped
        pmn provenance→primegov (4 rows restored) + a ﬁ-ligature dropped
        Commissioner Rosenfield from ALL rolls (a 3:2 would have read 2:2); provo's
        hardcoded PC ROSTER silently dropped new commissioner Tosh Metzger's every
        vote (WATCH-CLASS: check rosters on each PC refresh); EC probe dedup
        (42/47 false "new" → 0, notice-disposition dedup + MM-DD-YY parsing); CH
        minutes_unrecovered.csv MISSING HEADER broke the engine's suppression
        (2 phantom flags); SJ "Farnworth" OCR-typo canon fold (+1 named abstain);
        WJ PC dual-meeting fixed-slug collision (worked around; permanent
        title-derived-slug fix queued); herriman `--build-md` proven DESTRUCTIVE
        (clobbered curated index — agent caught + fully reverted byte-identical).
      - **SHARED FIX (post-wave, solo): `scripts/refresh_lib.py`
        append_index_rows** now dedups WITHIN a batch (the st_george double-linked
        URL doubled every vote on 2026-06-18 — caught by the validator, fixed
        city-side, then root-caused here; unit-tested + idempotency-tested).
      - **New recovery leads — ALL WORKED 2026-07-19 (same-day agents + federated):**
        ✅ **slc 2022-08-29** = TWO genuine back-to-back sessions (6:05 pm
        Truth-in-Taxation hearing + 6:20 pm Budget Amendment No. 1 / Other Side
        Village) — BOTH ingested with disambiguated slugs (+6 motions/+42 rows,
        6/6 tallies match); the old PMN recovery file 913093 was MISLABELED (it is
        the budget session; born-digital copy supersedes); 3 Oath ceremonies + the
        Redistricting Commission ruled out-of-scope permanently.
        ✅ **ogden PC 2020-10-07 RECOVERED** (+16 motions/+119 named rows incl.
        both target items: Petition 2020-5 rec 8:0, open-space ord rec 9:0) — from
        a standalone born-digital DocumentCenter draft (View/14318), unamended
        approval verified at 2020-11-04 per the alta precedent. **🟢 MAJOR NEW
        LEAD: the whole ~60-row 2020–2023 ogden PC gap looks SYSTEMATICALLY
        recoverable** by the same channel (DocumentCenter View-ID probe +
        following-packet embedding; the 2020-11-04 minutes are already located
        inside View/14838) — queue as a dedicated backfill package.
        ❌ **lehi 0 of 3** — Granicus channel now definitively EXHAUSTED with
        evidence: 2021-08-10's Minutes link resolves to an EMPTY TEMPLATE stub
        (body never published); 2020-03-17 has no clip at all; PC 2025-10-02 is
        video-only (NoMinutes). All three reclassified GRAMA-only (approved
        records demonstrably exist — later consent items cite them); ledger rows
        carry the clip/doc evidence. fetch_new guard lead: detect the
        EmptyTemplate.php signature so hollow Minutes links flag in probes.
        ✅ Also closed this pass: the stale **taylorsville 15 OCR-upgrade** item
        (done 2026-07-12, never checked off — verified on disk incl. the recovered
        Cochran Aye; 7 drafts correctly sidecar-only by rule).
      - **Watches:** ⚠ **CivicPlus platform outage** — murray, sslc.gov, and both
        MSD hosts all HTTP-500 site-wide the same day (correlated; NOT rot; nothing
        marked dead; re-verify next cycle). Lehi council-minutes LAPSE still
        ongoing (~21 meetings since 2026-01-27, agendas only; PC unaffected; 3
        lapse regulars ledgered pending-publication). orem PC 2025-10-15 +
        st_george 2025-10-09 mis-uploads PERSIST (re-verified byte-identical wrong
        files). Holladay's 7 + others = normal 2-6wk minutes lag, re-probe next
        quarter. magna CRA pending items bumped (2025-11-18 draft's PMN notice now
        PURGED — our sidecar is the only surviving copy).
- [x] **HARDENING BUNDLE — 2026-07-19 (owner-authorized; executed solo/inline; ONE
      federation at the end — integrity ok / reconciliation exact / 193-31).**
      Closes Q3-entry follow-ups (b)(c)(d) + the CF-entry shared-lib-polish core.
      - **(a) pmn_crosscheck engine:** RE_CANCEL += reschedul; **notice-body/
        description cancellation check** (detail page fetched ONLY for would-be
        flags — polite; kills the 6-confirmation false-flag class); cross-body
        `(date, dataset-set)` dedup (the logan RDA class); nephi council body 1788
        `repo_datasets` widened to cover its PC cross-filing. 5-city regression all
        0 flags. Record: `scripts/pmn_crosscheck_HARDENING.md`.
      - **(b) refresh harness:** `refresh_status.py` now normalizes all probe-JSON
        shapes + labels print-only cities honestly — **the fix immediately
        recovered 2 missed white_city APPROVED council minutes** (+10 rows,
        ingested, 23/3/0) and identified bluffdale's 07-01 Minutes-slot doc as an
        agenda (pending window). CH `fetch_minutes` label matcher made
        fragmentation/entity-tolerant — **immediately surfaced + ingested 2 more
        docs** (2026-01-09 legislative breakfast [IN-scope by CH's own 2020
        precedent] + 2025-06-04 admin hearing, 5 rows). herriman gained a standard
        **read-only `--probe`** (live-tested; its `--build-md` now carries a
        DESTRUCTIVE warning). west_jordan PC slugs are now **title-derived**
        (unit-tested; the dual-meeting overwrite class is dead).
        `build_sources_index.py --verify-sample` per-city scoping ALREADY EXISTED
        (positional city args) — the sandy agent misread; closed as documentation.
        ⚠⚠ **INCIDENT (caught + fully repaired):** CH's `--fetch` full-acquisition
        path proved DESTRUCTIVE like herriman's — it dropped 3 council + 39 PC
        recovered index rows and resurrected the T3.1(h)-removed 2024-01-02
        duplicate; repaired via pre-fetch backup + reconstruction from the
        federated `document` table (all paths disk-verified), re-extracted,
        24/2/0. **CH + herriman are now BOTH confirmed destructive-refresh
        pipelines → append-only-ingest conversion is a queued item with doubled
        evidence** (do NOT run their full-build/--fetch paths as refresh steps).
      - **(c) referral overrides on stable keys:** `referrals_lib.load_overrides`
        accepts `primary_app_key`/`related_app_key` (resolved live; stale keys
        FAIL the build loudly); **all 111 override rows across 11 cities migrated**
        to app_keys; all 11 rebuilt **byte-equivalent** (links/override/high counts
        identical). The integer-id drift class (west_valley ×2) is dead.
      - **(d) CF shared-lib polish (core):** structured supersession markers
        (note-ENTRY startswith, both cycle_totals + driver — the bluffdale
        "keep-the-word-out" workaround is obsolete); donor classifier: `\bloans?\b`
        word-boundary + Consulting/Consultants business tokens. **29-city
        rebuild-diff proof:** 21 byte-identical; 8 intended firm→business
        reclassifications; **4 MATERIAL loan-surname fixes** (park_city's Loannides
        donors ×3 and st_george's "Sloan … Porter" $1,500 were counted as candidate
        LOANS — Beerman's self-funded −$500, Leavitt's −$1,500 now true);
        cycle_totals unchanged everywhere; provo's 42-row diff = formatting
        reconvergence to the federated state (strict-compare proven, zero data
        change).

## Infrastructure

- [x] **LLM-retrieval refactor — `REFACTOR_PLAN.md` — COMPLETE 2026-07-07.** All five
      phases executed + verified (16/16 cities 0 FAIL): city registry
      (scripts/cities.py), cities.db search layer (comment/cf_*/ordinance/document +
      five FTS5 indexes incl. fts_packet), §9 expansion contracts migrated + enforced
      (validate_dataset + validate_city + every index-writing builder), shared libs
      (weeks/referrals/db-build, all conversions byte-identical), rebuild_derived.py,
      consistency cleanups (rosters, honest-empty comments, 25-col election superset +
      slug filenames, 5,623 provenance headers, weeks slimmed 196→68 MB, 3,446 packet
      text sidecars), five skills updated + 70 stale doc listings fixed. Follow-up
      spun out below: CF vision cache-key standardization.
- [x] **Promote Ogden PMN-backfill RDA/MBA minutes — DONE 2026-07-10.**
      `meeting_minutes/extract_backfill_votes.py` reuses `find_motions()` over the 10 recovered
      minutes (forcing body from the pmn index) and merges with `provenance='pmn_minutes'`:
      RDA 111→147 (+36 motions, 2023 + 2024-04-23), MBA 18→23 (+5, 2020). validate 24 PASS / 0 FAIL;
      backups `_backups/2026-07-10-ogden-rda/`. (Original note retained for context.) NOTE: 2022
      RDA/MBA and 2023 MBA minutes are NOT on PMN (budget/hearing notices only) — honest
      gap, no source to recover from there.


## Three new cities (south_jordan / millcreek / taylorsville) — 2026-07-06 follow-ups

- [x] **South Jordan 2020-minutes backfill — DONE 2026-07-10.** `meeting_minutes/extract_backfill_votes.py`
      reuses `parse_meeting(load_lines())` over the 13 recovered council minutes (2020 Jan–Jul + 2023-01-24)
      and merges with `provenance='pmn_minutes'` (46 Council + 2 RDA motions, 2020-01-07→2023-01-24). SJ uses a
      **custom `db/build_db.py`** (not the shared lib) — patched it for the provenance column too. **Gotcha
      fixed:** a stray `db/civic.db` was hijacking SJ's glob-first db selection (canonical is `db/south_jordan.db`
      per `scripts/cities.py`); removed it. validate 23 PASS / 0 FAIL; backups `_backups/2026-07-10-sj-council/`.
      Still open: the recovered rows are provenance-tagged (not moved into the audited `minutes/` tree), so the
      2 `minutes_unrecovered.csv` rows are left as-is (they truthfully describe the audited layer).
- [x] **[high] Taylorsville 15 OCR-upgrade minutes — ALREADY DONE 2026-07-12; item was
      stale, verified + closed 2026-07-19.** `pmn_backfill/ocr_upgrade_candidates.csv`
      carries the full per-candidate disposition: **6 PROMOTED** (3 council + 3 PC,
      born-digital md swapped, scans retained, vote diffs clean — incl. the recovered
      Cochran Aye on 2025-01-22 m5, re-verified on disk 2026-07-19), **2 NO-OP** (repo
      docs already born-digital; the OCR docs those dates are separate RDA minutes not
      on PMN), **7 DRAFT — sidecar-only by rule** (the repo's scans are the APPROVED
      versions; draft text never replaces approved text). No further work exists.

---

# ═══ ARCHIVE ANCHOR 2026-07-31-RESTRUCTURE ═══

> The 2026-07-31 restructure (owner-approved) replaced TODO.md with a lean DEBT+GATED queue,
> moved options/watches/tails to LEADS.md, and cut HANDOFF.md to a single-session banner.
> Everything below is the VERBATIM pre-restructure content of the three replaced files, so
> every dated wave record, closure note, and named entry remains findable here by search.
> ⚠ Items open at restructure time appear below in their pre-restructure form too — the live
> queue is TODO.md; this snapshot is history. Line references in
> _audits/2026-07-31-publication-review/triage_full.md resolve against the TODO.md snapshot
> below (its line 1 = the snapshot's first line). Working copies also at
> _backups/2026-07-31-todo-restructure/ (gitignored, local only).

## 2026-07-31 snapshot — TODO.md (verbatim, pre-restructure)

# TODO — future work queue

## ⚠ HOW TO READ THIS FILE (triage taxonomy, added 2026-07-29)

**The open-checkbox count is NOT a measure of work owed.** On 2026-07-29 it read 55, but only
**~9 of those are actual correctness debt**. The rest are monitoring, menu options, and
decisions — all wearing the same `- [ ]`, which made the backlog look unbounded and made
"what's next" unanswerable. Every section header now carries its BUCKET. Use the bucket, not
the count.

| Bucket | ~n | Terminates? | How to treat it |
|---|---|---|---|
| **[DEBT]** correctness debt | 9 | **Yes** — bounded by the corpus | The only real queue. Burn down. |
| **[WATCH]** monitoring | 5 | No, by design | Ends only if a source appears. Not work owed. |
| **[OPTION]** scope choices | 15 | N/A | "We could add this." Not doing it is not a defect. |
| **[GATED]** owner decisions | 4 | When the owner decides | Do not start unprompted. |
| **[TAIL]** opportunistic residuals | 22 | Never fully | Fold into the quarterly refresh; don't queue. |

**Definition of done for the repo is a STATE, not an empty list:** (1) every entity passes
`validate_entity.py` including `--federation`; (2) every known ceiling is caveat-carried IN
THE DB so it surfaces at query time, not just in markdown; (3) no document asserts something
the db contradicts. Much of that is true as of 2026-07-29.

**⚠ A backlog entry is EVIDENCE, NOT FACT — verify before you rank.** The 2026-07-29 session
worked four items filed as "votes-pipeline extraction defects". **Only one was.** Two were the
SOURCE telling the truth and the extractor faithfully reproducing it (a clerk's stale
closed-session template; a county liaison sharing a councilmember's surname), and one had
already been fixed. Ranking work by reading this file reproduces this file's errors. When an
entry states a CAUSE ("an extraction artifact"), treat that as someone's hypothesis unless it
cites the primary document. Prefer entries that say what was OBSERVED over what was DIAGNOSED.

Durable to-do list for future sessions. When you complete an item, check it off with a
dated note. **Once a closed item is purely historical** — fully done, no open sub-items —
its bulk record moves to `TODO_ARCHIVE.md` (entries referenced by name from other docs,
e.g. HANDOFF.md / NEXT_SESSION_PLAN.md, leave a one-line `- [x]` stub here pointing to the
archive; SPLIT entries keep a stub PLUS their still-open sub-items). Open items, partials,
honest gaps, and owner rulings stay here in full. Add new items here rather than leaving
them only in agent reports. The 2026-07-19 archive move preserved the verbatim pre-cleanup
file at `_backups/2026-07-19-todo-cleanup/TODO.md`. Background: `REMEDIATION_PLAN.md` (the
2026-07-02 remediation, mostly complete) and `_audits/2026-07-02/report.md` (the audit that
drove it).

## High priority — [DEBT] + [OPTION] (MIXED — the only mixed section; check each item)

- [ ] **[DEBT] NON-CITY-TIER AUDIT FIXES (from `_audits/2026-07-25/report.md`, 2026-07-25).** The
      9-entity post-build audit found 4 entities with material extraction loss plus 6
      systemic federation/doc gaps. **All 9 pass `validate_entity.py` at 0 FAIL / 0 WARN —
      structural conformance was never the question.** Ranked, data loss first. Three of
      these are the repo's worst failure mode: **recoverable data documented as an honest
      source ceiling**, which stops anyone from looking again.
      **TIER 1 — data loss:**
      (a) **✅ DONE 2026-07-26 — cache_county OCR backfill.** All **160** text-empty
          documents OCR'd (tesseract 150dpi over re-fetched PDFs; ~2,000 pages, ~5h).
          **motions 1,812 → 3,495 · votes 11,788 → 13,200 · contested 182 → 206**; the
          2015-2020 era now yields **1,505 tally-only motions** (audit estimated ~1,400) and
          the 15 named-era files yielded **+813 named vote rows**. Four extractor bugs found
          en route: (i) `extract_votes.py` skipped on the `format` LABEL, so an OCR'd
          document's text was still never read — now routed on CONTENT; (ii) the born/tally
          discriminator keyed on the `Action:` line, which BOTH eras use, so the whole
          OCR'd era parsed as born-digital and yielded zero — now keyed on the named
          `Aye: N <names>` roll; (iii) the narrative seconder pattern admitted tokens ending
          in "." and so crossed the sentence boundary ("…approve the Permit Limits. Ward
          seconded" → a person named "Permit Limits. Ward"), minting **~430 phantom
          persons** — new `OCR_NAME` allows an initial but never a word+period, and
          `clean_name` strips leading role/agenda words; (iv) `--force` wrote SIBLING files
          rather than overwriting, leaving the placeholders in place — consolidated, with
          one document (2019-11-26a, 54pp) that had never got its own file OCR'd separately.
          **person 464 → 30** (9 new evidence-backed aliases). Surname-only movers in that
          era (White, Yeates, Potter, Robison, Merrill) are honest partials — the narrative
          prints no first name. The cache `caveat` row was REWRITTEN, since it still said the
          era "contributes ZERO motions".
          *(original)* **cache_county — 160 of 307 legislative minutes are text-empty placeholders**
          (145 = the whole 2015–2020 era; **15 sit inside the named-roll era 2021–2025 and
          are undocumented anywhere**). Cause: `cache_county/legislative/extract_votes.py:293`
          `if fmt=="scanned": continue`, while `extract_ocr()` at line 242 implements the
          tally grammar and is never reached. A re-fetched 2025-05-13 source carries a
          CONTESTED named roll (`Aye: 5 … Nay: 1 David Erickson`). Est. ≈1,400 tally motions
          + ≈200 motions / ≈1,300 named votes. **CLAUDE.md's "these are OCR (tesseract)" is
          false — no OCR ran.** Fix: run the documented `fetch_minutes.py --era scanned
          --ocr`, emit tally-only rows with blank member per the cardinal rule, rebuild.
      (b) **✅ LARGELY DONE 2026-07-25 — summit_county PC vote recovery.** Record:
          `summit_county/land_use/VERIFICATION.md` + `_audits/2026-07-25/remediation.md`.
          **The audit's premise was WRONG in an important way:** the `AYES:` blocks are
          inside **HTML comments the Granicus portal never renders** (545/545
          comment-enclosed, 0 rendered) — the converter stripped them correctly. Tested
          before acting: **520/520 hidden blocks agree exactly with the published tally**
          (real data), but **all 25 divided motions already name their dissenter in the
          rendered text**, so the hidden blocks add **0** dissent. **Owner ruling
          2026-07-25: published prose only — the 3,001 comment-hidden positions are NOT
          ingested.** Do not re-open this as a "gap" without a fresh ruling.
          What DID land, from published prose: `build_votes.py` v2→v3 recovered 4 unparsed
          divided-vote grammars (leading `Opposed were X, Y`; trailing `…objected.`/bare
          `…against.`; dotted-leader wraps; the 2020 two-column poll grid) + en-dash
          tallies. **Named rows 409→469, named-roll motions 256→270**; **15 motions whose
          `Pass` had been inherited from a neighbouring motion up to 10k chars away now
          carry an honest blank**, 1 flipped Pass→Fail, 52 tallies recovered, and 2
          impossible attributions removed (Nay rows against a `(7-0)` tally). Gates: 0
          named-votes-exceed-tally, 0 non-name-shaped members, FILES-WIN exact (469=469),
          links reproduce link-for-link, validate 10 PASS/0/0. All three ceiling docs
          corrected. **✅ RESIDUAL ALSO CLOSED same day — `build_votes.py` v4,
          marker-anchored segmentation.** v3 still found items by their "X made a motion"
          verb; v4 pairs motion verbs and printed outcomes **in document order**, so every
          printed outcome gets its own item and an item with no printed outcome keeps an
          honest blank. **Decisive gate: meetings where tallied motions == printed tally
          lines went 89% → 99% (AgendaCenter era 82% → 99%).** Motions **1,526 → 1,575**
          (+49 across 34 meetings, **all gains, 0 losses**), named vote rows **469 → 497**,
          db vote 578 → 606, contested 292 → 304. Four more source-fidelity bugs found and
          fixed while proving it: **tab-separated OCR files** (literal-space `made a motion`
          matched nothing — 2016-11-03 eastern went from **0 motions to 6**, the same
          whitespace lesson as utah_county); **U+2010 hyphens** in `(7‐0)` tallies invisible
          to an ASCII dash class; a **poll-grid name pattern** that swallowed 4 of 7 voters
          (`Kucera-Nay \n Commissioner Harte` read as one name); and **`which was` motion-text
          fragments 26 → 2**. Tally ORIENTATION now resolved from the named roll where one
          exists (prevailing-side-first failures like `MOTION FAILED (6-1)` over 1 Yea/6 Nay)
          while the verbatim tally string is kept as printed. Gates: 0 named>tally, 0
          non-name-shaped members, 0 member-twice, FK OK, FILES-WIN exact (497==497,
          1575==1575), **app/ordinance links reproduce link-for-link despite full PC
          renumbering** (they recompute from motion text, so renumbering is absorbed),
          validate 10 PASS/0/0. Motion-text fragments fully closed (`which was` 26→0 — the
          clerk also writes "seconded by X, THAT the Commission approves…", not only
          "to approve…"; plus 4 `All voted in approval` outcome sentences the action-picker
          was mistaking for motion substance). **Repo-wide sweep for the two GENERIC bug
          classes: summit-only in practice.** 36 of 41 entity trees show neither trigger;
          the U+2010-tally hits in herriman + park_city are FALSE POSITIVES (herriman's
          `(10‑1)`/`(6‑0)` are *state legislature committee* counts quoted in a bill report —
          council max roll is 6; park_city's `(5‐7 )` is list-item numbering), and the
          tab-separated files in midvale (×5) + wfrc (×1) all extract motions with 0 blank
          results. Record: `summit_county/land_use/VERIFICATION.md`.
      (c) **✅ DONE 2026-07-25 — utah_county vote-layer repair.** Record:
          `utah_county/db/REPAIR_2026-07-25.md`. **motions 10,089 → 11,218 · member-vote rows
          2,765 → 4,705 · named-roll motions 822 → 1,555 · contested 31 → 84, now spanning
          2015–2026 instead of stopping at 2018** — the entity is no longer blind to divided
          Board votes. (i) All 228 born-digital files re-extracted with **poppler** via new
          `db/reextract_borndigital.py` (split-word rate ~13/1k → ~0, better on 10/10;
          2016-08-30 anchors 5 → 17); handles the 30 multi-part meetings via the front-matter
          `source_url` order and refuses any >50% shrink. (ii) `VOTE: n-n` + bare
          `PASSED:/FAILED: n-m` added as anchors; ALL-CAPS `COMMISSIONER LEE` resolved through
          the meeting's own attendance block with a corpus-wide fallback; blank lines no longer
          end a vote block; the 2020-24 parenthetical form parsed **including the trap where
          `AYE: THOSE OPPOSED (COMMISSIONER LEE)` means a NAY** (direction read from the phrase,
          never the prefix). 2019-01-29 went 0 motions → 14 (13 named); 2019 overall 0 → 264
          named. A phantom-motion regression (+1,670) from the new anchor was caught and fixed
          by measuring adjacency in non-blank lines. (iii) **NOT a code defect** — the fetcher
          already parsed those filenames; the minutes were posted after the 2026-07-20 build.
          Re-running it recovered **15 meetings**; 3 (2021-06-02, 2022-08-15, 2024-01-31) 404
          today and stay documented gaps. Two defects the re-fetch exposed are now guarded:
          a meeting filed in **2029** (the county describes `07.16.2019….pdf` as "July 16,
          2029" — filename year now wins; 0 future-dated meetings) and a `pendingminutes.pdf`
          **placeholder** ingested as minutes (now logged unrecovered). **Audit D4 also closed:**
          `db/person_aliases.csv` consolidates 15 name variants → 8 real commissioners, each
          entry carrying a non-co-occurrence proof; the `Nathan Lee` row is a SOURCE misprint
          kept verbatim in the flat layer and resolved only in the person layer. Gates: 0
          votes>roster, 0 double-votes, 0 names_recorded mismatches, 0 future dates, FK 0,
          validate 10 PASS/0/0, 5 random named motions ground-truthed. **RESIDUAL (honest):**
          42 of 63 2020-24 parenthetical rolls uncaptured (OCR too fragmented to pair);
          surname-only `Sakievich`/`Gordon`/`Powers Gardner` (no attendance block in that era —
          first names not invented).
          *(original)* **utah_county — three compounding losses.** (i) **≥940 motions lost 2015–18** —
          pypdf inserts mid-word spaces that break the extractor's literal anchor
          (`"f ollowing"`, `"mot ion"`); on 2016-08-30 `pdftotext -layout` finds 17 anchors
          and the md holds 26 `AYE:` blocks, but the repo md has 5 and the db has 5 motions.
          The exact-anchor count EQUALS the db motion count each year — poppler extracts the
          same PDFs cleanly. (ii) **the entire 2019–2024 named era stored as tally-only** —
          `named`=0 for every year 2019–24 while `2019-01-29` reproduces
          `VOTE: 3-0 / AYE: COMMISSIONER LEE / …` and the db has 0 motions for that meeting;
          `NAME_LINE_RE` matches Title-Case only, 2019+ prints ALL-CAPS. ≈521 roll calls,
          ≈1,300 vote rows; **contested detection is blind after 2018** (3 Fail in 10,089).
          (iii) **20 meetings absent that the county API lists** (2025: 44 API rows vs 32
          repo dates) — fetcher filename-pattern blind spot; spot-checked URLs return 200.
      (d) **✅ DONE 2026-07-26 — weber_county OCR backfill.** New
          `db/ocr_empty_minutes.py` OCR'd all 21 Konica copier scans from the RETAINED raws
          (idempotent; born-digital untouched; `provenance=county_portal_ocr`).
          **motions 4,242 → 4,404 · votes 12,114 → 12,594 · motion_refs 1,102 → 1,148 ·
          adopted-instruments register 807 → 844 — exactly the 37 missing 2021 resolution
          numbers the audit predicted, including RESOLUTION 36-2021** from the very meeting
          (2021-09-21) the auditor had read visually to prove the loss.
          *(original)* **weber_county — 21 minutes docs are front-matter only** (~307 B; Konica copier
          scans, no text layer, no OCR fallback; 19×2021 + 2×2023). Source read visually
          holds 7 named roll calls incl. `RESOLUTION 36-2021`, and
          `ordinances/adopted_instruments.csv` is missing 37 of the 2021 resolution numbers.
          CLAUDE.md's "minutes_unrecovered.csv = none within floor" is false for these.
      **TIER 2 — fabrication / wrong derived facts:**
      (e) **✅ DONE 2026-07-29 — wfrc_mpo phantom persons. The briefed 12 were already gone;
          the INVERSE half of the same bug was still live and is now fixed.** The audit's 12
          (`Clinton City`, `Mark Shepherd No`, …) were removed 2026-07-26 — this item was
          simply never checked off. Re-deriving the bug class from scratch found the mirror
          image: `_NAMERUN` required every token to be followed by WHITESPACE, and `,` was
          not in the token class while `.` was. So a name closed by a period ran PAST the
          sentence (the known half), and a name closed by a **comma lost its last token** —
          *"seconded by Mayor Bob **Stevenson,** and the vote…"* → `Mayor Bob ` → a person
          called **`Bob`**. That minted **8 fabricated single-token persons** (`Bob`,
          `Carlton`, `Jeff`, `Joe`, `Mark`, `Monica`, `Rob`, `Shawn`), each splitting a real
          member. **`wfrc_mpo/CLAUDE.md` had been documenting these as "single-token honest
          partials" — a source ceiling that wasn't one, the repo's worst failure mode.**
          Fix (3 parts, each forced by a regression caught pre-rebuild): `_NAMERUN_C` (one
          optional final token closed by `, ; :`, used only behind an explicit cue); the bare
          `<run>seconded` alternative KEEPS the strict run (a tolerant run there fabricated a
          seconder named "Station Area Plan"); `ORG_TOK` for WFRC's appositive style
          (*"Mayor Tom Dolan, Chair of the Budget Committee, made a motion"* → returns ""
          honestly unattributed instead of minting "Budget"). **person 70 → 63 · role 144 →
          138 · motion 323 → 324 · vote 0 (ceiling intact) · 0 motions deleted.** The +1 is
          genuine, read in the primary minutes: 2024-03-28 *"Mayor Bob Dandoy, made a motion
          directing WFRC staff to update the RTP amendment process…"* — the comma had hidden
          it from the anchor. **`Rob Dahle` (Holladay's mayor) was absent from the entity
          entirely** and is now present. `validate_entity.py wfrc_mpo` 9 PASS / 0 WARN / 0 FAIL.
          **`Tami`/`Tamara Tran` RESOLVED as ONE person on positive evidence** (closing the
          audit's open collision question): WFRC's printed member table carries a single
          continuous **Kaysville Mayor** seat — Tamara through 2025-03, Tami from 2025-10, no
          gap, no second occupant — and `Tran` is the ONLY instance of that surname in the
          entire 2016–2026 corpus. Evidence in `person_aliases.csv` upgraded from name-shape
          (which the audit correctly called insufficient) to seat-continuity; no data change.
          **Honest residual:** `Froerer` stays a surname-only partial ("Commissioner Gage
          Froerer" appears only in attendance blocks, never as mover/seconder) — a real person
          recorded by surname, not a fabrication. Left unresolved rather than promoted.
      (e2) **[low, NEW 2026-07-29] wfrc_mpo — 4 appositive motions with no mover.**
          2017-03-23 Tom Dolan · 2020-08-27 Carlton Christensen · 2023-08-24 Mike Caldwell
          and Jeff Silvestrini. Each mover is unambiguous in the source and all 4 are
          recoverable with a backward appositive rule. **Pre-existing — they were missing
          before the (e) repair too, so this is a measured gap, not a regression.** Deliberately
          not attempted: two of three regex iterations during (e) produced non-obvious
          collateral damage, and a 5th dropped anchor (*"Commissioner moved to the next item"*)
          is NAVIGATION and must stay dropped. Only attempt with a same-session diff harness.
      (f) **✅ DONE 2026-07-26.** Both superseded postings dropped: 2022-10-25 "APPROVED"
          (superseded by "FINAL APPROVED") and 2024-11-26 "(approved)" (superseded by
          "amended-"). Each pair was ONE meeting published twice with identical motion
          counts — 2022-10-25 held 32 motions where the source has 16, and 2024-11-26 16
          where it has 8. Both dates now match the source exactly. The audit's warning held:
          of cache's 13 same-date document pairs only these 2 are duplicates; the rest are
          genuine council+workshop, regular+special and closed-declaration pairs (verified
          by comparing normalized bodies AND source URLs) — **do NOT dedup on date**.
          *(original)* **cache_county — 2 double-ingested documents** (2022-10-25, 2024-11-26) inflate
          24 motions / 168 votes / 4 contested; headline "182 contested" is really 178.
          **NOTE:** of the 7 duplicate meeting dates in the db these 2 are the only true
          dups — 2025-12-02 / 2026-05-26 / 2026-06-23 are `_council`+`_workshop` pairs with
          distinct source PDFs (verified), 2024-12-10 / 2025-11-18 are regular+special.
          Do NOT dedup on date.
      (g) **✅ DONE 2026-07-25 — summit_county spurious/duplicate motion rows.** The
          `'which was'` fragments (26) and the public-commenter sentence are gone via the
          v3/v4 extractor work. The "31 duplicated motion rows" claim was **~90% FALSE
          POSITIVE**: measuring repeated-long-line density per meeting, only **2015-01-08
          eastern** is a genuinely doubled document (68% repeated lines; page footers run
          2..22 twice) — fixed by `strip_duplicate_body()`, which fires on exactly 1 of 393
          files (8 motions → 4, matching the 4 outcome markers in the first copy). The other
          23 duplicate-bearing meetings sit at 0–5% and their repeats are REAL: 2017-06-27
          carries three separate minute approvals (Mar 28 / Apr 25 / May 9) that the clerk
          mislabelled "March 28" in all three headings — different seconders confirm.
          Source-faithful, correctly kept. **Do not "fix" these.**
      (h) **✅ DONE 2026-07-29 — and the real defect was ~10× the one filed.** The audit
          filed ORD 2021-22 as a date/typo problem. It wasn't: the register's
          `adoption_date=2021-12-14` was **correct all along** (the codified County Code
          prints `(Ord. 2021-22, 12-14-2021, eff. 1-1-2022)` at 15 places). The link was
          simply pointing at the wrong motion — 2021-10-12 item (c), whose Action line reads
          "approve Ordinance 2021-22" as a **clerk typo** for 2021-23; the true enacting roll
          call is 2021-12-14 item 10(a) (Erickson moved, Borup seconded, Aye 6 / Absent 1).
          **The far bigger finding: ALL 10 surviving cache ordinance links were DANGLING.**
          The 2026-07-26 OCR backfill inserted 1,505 motions from the 2015–2020 era AHEAD of
          the born-digital era, **renumbering `motion_id`** — and every hand-written id then
          pointed at an unrelated 2015–2017 motion. Verified in gov.db before the fix:
          ORD 2021-15 → *"approve the agenda as written"* · 2022-18 → *"adjourn from the
          Council meeting at"* · 2021-21 → *"deny the Little Bear Field Subdivision"* ·
          2022-30 → *"approve the request for tax relief filing"*. **All 10 were federated as
          `motion_resolution='unique'` — i.e. the repo's own rules said they were QUOTABLE.**
          Correct links before this pass: **0 of 10.**
          **Fix: the linkage is now DERIVED, not hand-written** —
          `cache_county/db/link_ordinances.py` (idempotent; the summit/utah idiom), 7 guards
          each drawn from a defect these minutes actually produce (canonical-document only,
          Ordinance-not-Resolution context, adoption verb, motion-carried incl. verbatim
          "Motion dies", **agenda-item heading outranks the number in the motion text**,
          register-date consistency, year consistency). Result **17 unique `high` links, every
          one read against the source**; 8 named-but-unlinkable rows carry a written reason
          (2022-01's only approve motion FAILED though the code source-notes it adopted;
          2021-09's roll call survives only as an attachment mis-dated to its 2022-11-22 host;
          2022-26/2022-34 have two competing adoption motions). Ords 2022-06/07/08/09/10 share
          one motion — a printed BUNDLED roll call, documented so it doesn't read as an error.
      (h2) **[HIGH, NEW 2026-07-29] GENERALIZABLE: any entity whose ordinance links were
          HAND-WRITTEN and whose db was later rebuilt has the same silent staleness.**
          `motion_id` is not stable across a re-extraction — cache proved it renumbers when
          rows are inserted into an earlier era. summit/utah have re-runnable linkers; **every
          other entity with an `ordinance.motion_id` needs checking**, and the durable fix is
          a derived linker per entity (never a hand-written id).
          **✅ MEASURED SAME DAY — the risk is NOT systemic. Do not panic-audit this.**
          Screened all **4,660 linked ordinances across 31 entities** in gov.db. The naive
          detector ("motion text doesn't name the ordinance") is **USELESS — ~30% false
          positive**: lehi reverses the number (`2020-05` ↔ *"Ordinance #05-2020"*, correct),
          orem and salt_lake_county carry `ordinance_no = NULL` so they can never match, and
          many correct links are titled motions that simply never print the number.
          The DIAGNOSTIC signature is narrower — linked to a **categorically unrelated
          procedural motion** (agenda/minutes/adjourn/recess/executive session with no
          "ordinance" in the text). That returns **just 5 candidates repo-wide**:
          nephi ×2 (`09-02-2025`, `01-20-2026` → consent-agenda motions), herriman ×1
          (`2022-36` → recess-to-convene), midvale ×1 (`2023-O-01` → Consent Agenda),
          weber_county ×1 (`2019-13` → adjourn).
          **⚠ CORRECTED SAME DAY — I predicted "several are probably CORRECT". ALL FIVE WERE
          WRONG (0/5).** Every one was the same defect family: **a procedural or consent motion
          absorbing an ordinance number it never enacted**, because a number read off an
          ALL-CAPS section header anchors to whichever motion follows it. So the narrow screen
          was **100% precise**, not noisy — and the "expect most to be correct" framing was the
          error, not the screen.
          **And the class was BIGGER than the 5 flagged rows** — it was suppressing correct
          links, not just creating wrong ones, which the screen could not see because a blanked
          link has no motion text to flag. Fixing the DERIVATION in each entity recovered:
          **weber_county 198 → 247 linked** (50 rows previously blanked as "ambiguous" — the
          spurious tie was always an adjourn motion; all 50 cite their own number verbatim),
          **midvale 113 → 127**, **nephi 96 → 95** (7 rows had pointed at a same-day RESOLUTION
          of the same number — Nephi numbers both by date; one dropped to an honest `none`),
          herriman exactly 1. **~64 links corrected from 5 flagged rows.**
          Fixes are all in the derivation, none hand-written: `PROCEDURAL_RE` guards
          (adjourn/recess/reconvene/approve-the-agenda) in herriman + weber; an enumerated
          `consent_match()` in herriman that links only on a unique code-citation or ≥2-token
          match; midvale `ORD_RE` now tolerates OCR `O`↔`0` in the year AND serial (`2O23-O-O1`)
          and requires an adopting verb reachable without crossing a sentence boundary; nephi
          pass-1 now iterates only adoption motions (the rule its own CLAUDE.md documented but
          the code applied in passes 2–3 only).
          **Standing lesson: a screen that flags WRONG values is blind to SUPPRESSED ones.**
          When a linkage bug is found, re-derive and diff the whole entity — don't just fix the
          flagged rows. cache remains the separate, worse case: hand-written ids plus a 1,505-row
          mid-era insertion that renumbered every one of them.
      (h3) **✅ DONE 2026-07-29 — and the root cause was a FETCHER bug, one level below the
          symptom.** `legislative/fetch_minutes.py` matched `source_url:\s*(\S+)` — and
          **`\S+` stops at the first SPACE**. Every Cache `source_url` contains spaces
          (`.../12-14-21 APPROVED sm.pdf`), so the stored URL was always truncated, the
          "same doc → overwrite in place" equality never held, and each re-fetch wrote a
          `_2.md` SECOND COPY. `extract_votes.py` then walked the DIRECTORY and extracted
          both. **Fix: extraction is now INDEX-DRIVEN** (`index_docs()`; the index resolves
          305/305 md_paths, the directory held 317) and the fetcher regex matches the whole
          line. Indexed-but-missing AND on-disk-but-unindexed are now PRINTED every run.
          **motions 3,495 → 3,388 (−107) · votes 13,200 → 12,560 (−640) · meetings 303 → 291
          · contested 206 → 193.** Proved by three independent checks: per-pair motion-for-
          motion twins; new `all_votes.csv` = old minus exactly the 644 rows sourced from the
          12 files; old-db-minus-unindexed == new-db row-for-row. Duplicate FILES deliberately
          LEFT in place (inert, invisible to index-driven consumers, honest fetch artefact, and
          deleting is irreversible without VCS). Doc correction: 9 pairs are byte-identical;
          3 differ only by the `snapshot_url` front-matter added to the indexed twin that day.
          **★ THE DERIVED LINKER PASSED ITS FIRST REAL TEST.** The rebuild shifted every 2021+
          `motion_id` by ~14 (1551→1537, 1790→1752…) — the exact renumbering that broke all 10
          hand-written links three days earlier. After re-running `link_ordinances.py`: **17
          linked before, 17 after**, all `high`, all re-derived onto the IDENTICAL physical
          motion (same date, text, source file), all still naming their own ordinance; the 8
          honestly-unlinkable stayed unlinkable. Hand-written ids would have broken a second
          time in three days. **Derive linkages; never hand-write a `motion_id`.**
      (h4) **✅ SWEPT CLEAN 2026-07-29 — the fetcher bug's symptom is cache-ONLY.** The `\S+`
          truncation is fetcher-shaped, so any entity with spaces in `source_url` whose fetcher
          was copied from this one could carry the same orphan duplicates. Swept **76 modules**
          (every `*/*/minutes_index.csv` with a `minutes/` dir, cities + counties): on-disk `.md`
          files absent from their module's index exist in **cache_county only**, and those 12 are
          the known, deliberately-retained duplicates. **No other entity is affected — do not
          re-audit this.** Cheap re-run: compare `basename` sets of `minutes/**/*.md` vs the
          `.md` paths named in that module's `minutes_index.csv`.
      *(original)* **cache_county: 12 un-indexed BYTE-IDENTICAL duplicate
          minutes markdown files** under `legislative/minutes/` (e.g. `2021-12-14_council.md`
          ≡ `2021-12-14_council_2.md`; 9 identical groups confirmed independently).
          `minutes_index.csv` lists one form, but **`extract_votes.py` walks the DIRECTORY**,
          so **107 motions / 640 votes in the db are exact duplicates** (~3% of motions, ~5%
          of votes). Residue of the F6 class the 2026-07-26 dedup closed for two other
          documents. NOT fixed — repairing it changes row counts, which the 2026-07-29 gate
          forbade. It also explains why ORD 2021-22 couldn't be re-pointed naively: the true
          enacting motion exists twice. Fix = index-driven (not directory-walk) extraction,
          then rebuild + re-federate; expect cache motions 3,495 → ~3,388.
      *(original)* **Ordinance links contradicted by primary documents** — cache ORD 2021-22's
          `high`-confidence link lands on a clerk typo (register `adoption_date` disagrees
          with the linked motion date and nothing flagged it) — **STILL OPEN (cache)**.
          **✅ summit DONE 2026-07-25**: Ord 1003 `2025-12-04` → **`2025-12-17`** (the old
          date appears in the text only as unrelated prose at line 209; the enactment clause
          reads "Enacted this 17th day of December, 2025" and motion 1633 is 2025-12-17);
          Ord 968 `2023-09-12` → **blank** (no source at all — signature block OCR-unreadable
          `Enacted this)" day of Guplumdpentoos,`, enacting motion 402 is 2023-09-20; blanked
          per the module's own 912/936 precedent rather than assert an unevidenced day).
          962/980 verified correct.
      **TIER 3 — garbling (bounded, source retained):** ✅ **wfrc DONE 2026-07-26** — 13
      `result_raw` values were stored one char short (all began `"ith "`) because an
      unanchored `it` alternative matched inside "W**it**h"; word-boundaried, **13 → 0**. And
      the Google-Docs/Skia exports wrap every word in U+202A-E/U+2066-9 marks: the parser
      stripped them but the MARKDOWN did not, so 7 files sat in `fts_minutes` with 14-19% of
      their characters unsearchable. `fetch_minutes.py` now strips at write time **as a
      SPACE, never as ""** — in these PDFs the marks ARE the word separators, and deleting
      them glued lines into "MayorDustinGettelmadeamotion…", costing 40 motions and 2 whole
      meetings before the gate caught it. ✅ **cache land_use DONE** — Chris Sands was
      dropped from 7 of 9 rolls on 2024-11-07: these are NUMBERED legal transcripts, so the
      line number fuses onto the last name ("…Nate Daugs, Chris Sands **13**") and the
      trailing `;` in the common "…Chris Sands; Nays: 0." form was also left attached. Both
      stripped; all 9 rolls now complete (named rows 930 → 939). ✅ **weber DONE** — the 9
      silently-dropped vote rows are now REPORTED on every build: `build_db.py` swallowed
      `sqlite3.IntegrityError` on `UNIQUE(motion_id,person_id)` and decremented the id, so
      they vanished with no trace (the Park City class). Each is a SOURCE clerk typo naming
      one commissioner twice on one roll; the flat CSV keeps them verbatim and the build now
      prints every collision (db 12,585 vs CSV 12,594 — expected and itemized).
      ✅ **summit packet sidecars DONE
      2026-07-25** — two font-cmap pathologies (PUA U+F0xx − 0xF000, plus a CID shift of
      −0x1D that stored "J-U-B SHALL RETAIN ALL COMMON LAW, STATUTORY" as
      `-\x108\x10%\x036+$//\x035(7$,1…`). `decode_cmap()` in `packets/build_packets.py`
      repairs both PER LINE and only when the shift raises that line's dictionary-word
      ratio, so it can never worsen a line; 58 of 118 sidecars repaired, >2%-control-char
      files 6 → 4 (residual is pure CAD coordinate text). ✅ **summit dev_type DONE** —
      104 rows reclassified (matched over the whole 2,500-char block, so project NAMES and
      public-comment text outranked the application: "Conditional Use Permit for a 'Vehicle
      control gate' … White Pine Ranches Subdivision" was typed `subdivision`); now read
      from the item TITLE, earliest-match wins. subdivision 212→147, plat_amendment 39→88,
      CUP 147→177; 8 random changes ground-truthed, 7 unambiguous + 1 genuinely dual.
      Still open: wfrc 13/53 minutes carry unstripped
      U+202C/D at 14–19% of chars + ~217 displaced first letters (the extractor documents a
      strip that never happens); wfrc 13 `result_raw` truncated one char (all begin `"ith "`
      — cardinal-rule-2 verbatim violation); cache land_use drops Chris Sands from 7 motions
      (trailing legal line-number fuses onto the name); weber 9 vote rows silently dropped
      CSV→db by `UNIQUE(motion_id,person_id)` (the Park City class — fail loudly instead);
      washington 1 file with shredded ALL-CAPS headings + 3 with ligature loss; summit 10 of
      118 packet sidecars font-cmap-garbled; mag drops printed divided tallies from
      `result_raw` (and 2 motions DO name a dissenter, which its absolute ceiling wording
      disallows).
      **SYSTEMIC (all verified against gov.db):**
      (i) **✅ DONE 2026-07-25 — caveat rows seeded for the whole non-city tier.** 7 of 9
          entities had none. Added to `scripts/build_cities_db.py`: summit ×2
          (`tally-only-partial`, `vote-ceiling`), utah/weber/cache/washington/juab ×1 each,
          ut_state ×2 (`disjoint-persons`, `vote-ceiling`) — each stating that entity's real
          ceiling (weber's 21 un-OCR'd scans, cache's 2015-2020 zero-motion era, utah's
          post-2018 dissent blindness, washington/juab's BY-DESIGN db-less deferrals,
          ut_state's disjoint legislator population + 264-bill subset). Verified the
          mechanism works: the exact row the audit flagged (`Clyde | Eastern Summit County
          PC | 38 nays`) now carries `record_caveats=tally-only-partial,vote-ceiling`.
      (j) **✅ DONE 2026-07-29 for the county + regional tiers; ut_state deliberately excluded.**
          `motion_std` **77,507 rows = city 49,172 + county 27,376 + regional 959**, 100%
          joined, 0 NULL `motion_id`. **Computed AT FEDERATION**, not from files — the tier
          has no uniform flat-motion shape (cache/summit `land_use`+`legislative/all_votes.csv`;
          utah/weber `db/staging/motions.csv`; wfrc `legislative/all_motions.csv`; SLCo
          Legistar-derived; **mag_mpo and ut_state have NO flat motion CSV at all**), so the
          city file-based contract could not cover it without inventing artifacts. New
          `compute_motion_std_noncity()` in `build_cities_db.py` **imports** `classify` /
          `action_class` / `parse_result` / `vote_mode` from `normalize_motions.py` so the two
          tiers can never drift; `ENTITY_MT` added there for non-city native labels (no city
          slug appears in it — city lookups provably unchanged). **The 31 cities' path was not
          touched: city motion_std byte-identical (sha1 `f0c6627…`), all 194 on-disk
          `motions_std.csv` byte-identical.** FK 0 / integrity ok / idempotent.
          **Two consequences to respect, both caveat-carried:** the non-city 100% join rate is
          **definitional, not a quality signal**; and `dataset` for that tier is **body-derived,
          not a directory** (`land_use` = the entity's PC(s), `legislative` = governing body +
          work sessions + agency boards).
          **Honest classification ceilings** (share left `Other`/`low` — findings about the
          SOURCES, not hidden failures; mag/cache/utah/weber publish an EMPTY native
          `motion_type` on 100% of rows, SLCo's are agenda-section headings, WFRC's are the
          motion verb): weber 8.6% · summit 18.9% · wfrc 26.2% · cache 27.7% · slco 35.6% ·
          utah 42.0% · **mag_mpo 61.1%** (MPO motions are about programming and funding, not
          land-use matters — a real property). 11 caveat rows added.
          `v_coverage` 68 → **82 rows**, covering all 7 normalized non-city entities plus
          explicit `(no vote layer)` rows for db-less-by-design washington/juab and a
          `(no motion_std layer)` row for ut_state.
          **ut_state EXCLUDED by owner ruling** (see the STATE TIER item above) — 0 motion_std
          rows, `EXCLUDED_FROM_MOTION_STD`, and `crosswalk_lookup('ut_state', …)` now
          hard-errors so nothing can quietly normalize it. A NULL-classification variant was
          built and then fully reverted. Caveat `ut_state / motion-std-deferred` records why.
          *(original)* **`motion_std` is empty for the whole non-city tier** (city 49,172/49,172; county
          0/24,346; regional 0/958; state 0/1,208) — root CLAUDE.md's "joined to `motion` at
          100%" is true only of cities. Consequence: **`v_coverage` returns 0 rows for all 9.**
      (j2) **[med, NEW 2026-07-29] weber (4) + summit (1) motions: `motion.outcome='Pass'`
          over a died-for-lack-of-a-second motion.** Surfaced by the (j) normalizer, which
          reads the text correctly as `outcome='died'` while the `motion`/`vote` layer says
          Pass. **Verified at source** (`weber_county/legislative/minutes/2018/2018-09-11_commission.md`
          :321-326): the minutes really do say *"Motion died for lack of a second"* — weber's
          extractor **merged the died motion with the SUBSTITUTE motion that followed and
          attached the substitute's roll call to it**. The normalizer is right; the extraction
          is wrong. Left untouched by the (j) work per cardinal rules 2/3 (a normalization
          layer must never repair the layer beneath it). Fix belongs in weber's + summit's
          own extractors, then re-federate.
      (k) **`coverage.json` covers only cities** (31 keys, `as_of` 2026-07-22; no counties /
          regional / state) though root CLAUDE.md presents it as the repo's measured coverage.
      (l) **✅ DONE 2026-07-26.** `has_text` and `fts_minutes` are now derived from the
          BODY, not from a file's existence: new `readable()` in `build_search_layer.py`
          rejects a front-matter-only stub or a "[SCANNED … DEFERRED]" placeholder, applied
          to the city minutes loader, the non-city minutes loader and the FTS indexer (which
          now PRINTS the exclusion count). Combined with the cache/weber OCR the stale rows
          went **195 → 7** (the 7 are genuinely-short real documents, e.g. cancellation
          notices), and `has_text` now reads cache 305/305 and weber 533/533 honestly rather
          than by assumption. Root docs updated to the live figure (13,886 / 40 entities).
          *(original)* **Searchable-coverage overstated twice**: docs say `fts_minutes` = 13,852, db has
          **13,896** (build_info agrees with the db); and **195 rows carry no usable text**
          (160 cache `[SCANNED]` stubs + 21 weber empties + 14) while `document.has_text`=1
          for all of them. Derive `has_text` from body length; exclude empty docs from FTS.
      (m) **✅ DONE 2026-07-26.** The path check now accepts every column spelling in use
          (`md_path`/`minutes_md`/`path`/`text_path`) AND resolves against the entity dir,
          the repo root and the MODULE dir — weber's 533 and mag's 151 documents had been
          silently validating NOTHING, and summit's module-relative `path` would have
          false-FAILed once the lookup was broadened. Added the three content gates the audit
          had to invent by hand: **placeholder/empty bodies**, **duplicate (date,body)
          documents**, and **future-dated meetings** (status-aware — a row explicitly marked
          `Scheduled` is a calendar entry, not a defect; utah_county has 5 such legitimately).
          They immediately earned their keep, surfacing weber's 21 empty scans and cache's
          141 placeholders as WARNs while the OCR was still running.
          *(original)* **`validate_entity.py` has a vacuous check** — it validates `md_path`, but weber
          and mag use `minutes_md`, so 533 + 151 paths are never checked. More broadly it
          caught NONE of (a)–(h) while reporting 0 FAIL / 0 WARN for all nine. Consider an
          empty-body / duplicate-(date,body) / text-presence check — the screener and the
          validator both currently miss zero-length markdown.
      **TIER 4 — doc drift:** ✅ **BATCH CLEARED 2026-07-26** — every item verified against
      the files before editing. Root `CLAUDE.md`: the ut_state advisory-opinion + statute
      corpora ARE federated (525 `fts_minutes` rows) though it said they were not; entity
      headline 42 → **44** (42 built + the 2 registered-only reference entities udot/uta);
      `fts_minutes` 13,852 → **13,886**. `ut_state/recon.md` "847 recorded roll calls" →
      **759** (of 1,137 rows; 378 are unrecorded voice votes). `weber_county/recon.md`
      motion_refs "1,679 / 1,096 / 582 / 1" → **1,148 / 749 / 399 / 0** (a figure that never
      matched the file, now refreshed post-OCR). `wfrc_mpo/CLAUDE.md` "all 53 docs" in FTS →
      **81** (53 minutes + 28 plans). `cache_county/CLAUDE.md` "312 minutes" → **305**, with
      the discrepancy explained (312 raw URLs; 4 lost, 2 superseded duplicates dropped, 1
      unparseable-date URL logged). `gov.db` `project_history.exited_tip` schema comment
      corrected — it is `last_vintage + 1`, NOT "first vintage the pin failed to reappear
      in"; the two differ for the 24 pins with non-contiguous runs (pin 11268 is absent from
      2025-2030 and back in 2026-2031). Also ✅ **utah_county's era ceiling CORRECTED 2026-07-25** in all
      three places (`utah_county/CLAUDE.md` era table rewritten from the derived per-year
      evidence; `recon.md` given a dated correction block preserving its recon record; root
      `CLAUDE.md:328` rewritten). True framing now documented: **named 2015–2019,
      tally-primary 2020+, dissent nameable throughout** — the losses are an extraction gap,
      not a ceiling. *(original)* utah_county's era ceiling is wrong in `utah_county/CLAUDE.md:37`,
      its `recon.md`, AND root `CLAUDE.md:328` (all say 2017+ is scanned-OCR tally-only;
      2017 is 100% born-digital, 49/50 files carry `AYE:` blocks, 499 total, and the db
      records 174 named motions in 2017). Correct framing: **named 2015–2019, tally-primary
      2020+, dissent nameable throughout.** Plus: root CLAUDE.md says ut_state's AO/statute
      corpora are "not federated into gov.db's fts tables" (525 rows ARE); root says 42
      registered entities, registry has 44; weber recon motion_refs 1,679 vs 1,102; cache
      312 vs 307 minutes + 1 unlogged URL; summit recon 195 vs 198 + an elections doc still
      saying the entity isn't registered; wfrc "all 53 docs" in FTS vs 81; ut_state "847
      recorded roll calls" vs 759; `project_history.exited_tip`'s schema comment disagrees
      with the builder for 24 non-contiguous pins.
      **TIER 5 — ✅ PROVENANCE POINTERS DONE 2026-07-29; raw retention is a PENDING OWNER
      DECISION.** Measured first: 305 legislative documents, **0 with a retained raw file**
      (`land_use/`, `plans/`, `ordinances/`, `elections/` all have `raw/`; `legislative/` does
      not). Probed all 305 live URLs — **280 return HTTP 200; exactly 25 return 404**, and the
      25 dead ones are precisely the wayback-recovered set (22 `wayback_minutes` + 3
      `wayback_ocr`), **0 of which carried a snapshot URL**. (The audit said 26; two superseded
      duplicate postings were dropped 2026-07-26.)
      **Snapshot URLs recovered 25/25** via the Wayback CDX API (serial, 1.5 s — polite), stored
      as ADDITIONS with `source_url` untouched, in three places: `legislative/minutes_index.csv`
      (new `snapshot_url` + `snapshot_timestamp`), each document's markdown front-matter, and
      the ledger `legislative/wayback_snapshots.csv`. Re-runnable:
      `python3 legislative/recover_snapshots.py`. Five verified by re-fetch (page counts match
      front-matter exactly; the one yielding 0 chars is the `wayback_ocr` scan, correct).
      **Every one of the 25 has at least one `200 application/pdf` capture; 10 have several** —
      no unrecoverable document, so no gap record was needed.
      **⏳ RAW RETENTION — DECIDE, don't drift:** these PDFs carry appended media packets, so
      the 280 live documents total **2.80 GB** (largest single file 47 MB) and the 25 dead ones
      **129 MB**. Options: (a) retain nothing — the provenance defect is closed either way now
      that pointers exist; (b) **retain only the 129 MB dead-URL slice** — the only
      IRREPLACEABLE bytes, recommended; (c) full 2.93 GB. Note (c) buys less than it looks:
      the planned GitHub publish **gitignores `*/raw/`**, so raw is local-only by design and
      helps only on-machine re-verification — which matters for exactly one question, *"did the
      OCR read this right?"*, answerable only from the image. cache is the repo's least-settled
      corpus (160 docs OCR'd 2026-07-26, 4 extractor bugs found), which is the case FOR (b).
      *(original)* cache_county retains **no `raw/`** for its legislative corpus
      and its 26 Wayback-recovered docs store the dead live URL with no snapshot URL — those
      documents have no reproducible provenance pointer today (one sampled URL 404s).
- [x] **Motion `disposition` derived column (approve | deny | continue | table |
      procedural)** — DONE for SLC and rolled out to all 31 cities (2026-07-12, T1.1/T1.3):
      the `disposition`/`disposition_method`/`disposition_confidence` normalization columns,
      materialized in `scripts/db_build_lib.py` + the 5 forks and federated in `cities.db`.
      Full record: TODO_ARCHIVE.md. Still open (retained below):
      all 31 validate, 40,090/45,728 federated city motions carry a disposition. **REMAINING:**
      salt_lake_county's own Legistar-based `build_db.py` (structurally different — motion text from
      EventItems) does not yet compute disposition; per-city ground-truthing belongs to the
      motion-classification AUDIT below (do not close this item until that passes).
      **↩ FOLLOW-UP the oracle surfaced — reconcile the legacy `recommendation` field:** the
      build's disposition∘outcome cross-check found **13 PC recommendation motions where the
      existing `recommendation` (Positive/Negative) is WRONG** — it keyword-matches direction from
      `result_raw`/`motion_text` WITHOUT reliably composing with carriage (same bug class as the
      old `outcome_of`), so it mislabels failed/tied recs (e.g. a "positive recommendation" that
      failed 0:1 stored as `Positive`; a "recommendation of denial" that passed 6:0 stored as
      `Positive`). Fix: derive `recommendation` for PC recs from `_compose_dir(disposition,
      outcome)` instead of `recommendation_of`'s keyword match — makes it correct by construction.
      Note this changes the "269 Positive / 45 Negative" counts and any `v_pc_divergence` figures,
      so re-verify downstream after. Currently reported non-fatally by the build.
- [x] **[box closed 2026-07-19 — the entry's own status already said "NOTHING REMAINS
      OPEN — T3.1 is 100% COMPLETE"; the checkbox had simply never been flipped]**
      **T1.3 upstream extraction defects (found by the 2026-07-12 motion-classification
      audit; per-city evidence in `_audits/2026-07-12-motion-classification/findings_raw.md`).**
      Corrupt result_raw / lost vote rows the classifier cannot repair — fix in each city's
      extractor + re-extract + rebuild. **STATUS 2026-07-12 (T3.1 execution, two sessions):
      (a)–(l) ALL DONE — 19 cities repaired, re-extracted, rebuilt, validated (alta,
      midvale, south_salt_lake, slc, copperton, cottonwood_heights, emigration_canyon,
      taylorsville, orem, vineyard, millcreek, west_jordan, holladay, magna, draper,
      herriman, riverton, white_city, st_george, kearns + the ogden lint). ALL original
      Tier-A five closed (riverton Hartley/Breinholt page-header-split votes recovered —
      both rolls now 7/7 matching printed 5-2/4-3; herriman form-feed satisfied;
      midvale/holladay dups resolved; alta line-wraps in (a)). **NOTHING REMAINS OPEN —
      sandy m80 closed 2026-07-12 (see (m)); T3.1 is 100% COMPLETE.** Known source-misprint residuals (advisory, faithful):
      riverton 2024-08-08 m4 / 2025-12-11 m1 (clerk tally arithmetic), herriman
      2021-09-08 m5 (nays-first "failed 3:2" — roll 2A/3N + Fail agree), riverton
      2021-10-14 m5 (4 named ayes vs printed 3-0), kearns/nephi/logan word-over-tally
      rows in the audited review population.** Ranked by blast radius:
      (a) **✅ alta 2021 narrative-grammar failures — DONE 2026-07-12.** Extractor rewritten
          (both body copies): vote-EVENT segment anchoring ("A [voice] vote … was taken",
          "called the question", qualified "VOTE on …:" labels, bounded ROLL-CALL label regex),
          quoted narrative name-lists ("voted/voting “Aye./Nay.”", "opposed"), CAPS "CALLED
          the Question on <target>" as its own motion row, 2021-07-14 Ayes/Nays column grid,
          "(No vote was taken)" → RECORDED (never fabricated APPROVED), word-priority outcome,
          seg cap 320→700, OCR `~` dash, `;` label variant. PLUS **per-file name resolution**:
          the 2020-21 councilmember Bourke is **MARGARET Bourke** (all her votes had been
          attributed to Roger Bourke; "Mayor Sondak" also resolved to Roger) — person layer
          corrected, 3 junk db persons ("Contract. He" etc.) removed via mover roster-guard +
          STOP additions. `db_build_lib.outcome_of`: exact-string `RECORDED (no vote line)` →
          outcome NULL (honestly unknown; aligns db with motions_std 'unknown'; string is
          alta-only — verified across cities.db, so the 6 forks need NO splice). Result:
          Fail 7→13 (every audit flip m58/66/73/99/119/65 landed + the 2 missing failures
          + a 3rd found at 2021-01-13, verified at source), contested 13→24, named motions
          168→177, +3 motion rows (CQ), 24 RECORDED rows now NULL outcome. Rebuilt +
          federated; validate_city 25 PASS / 0 WARN / 0 FAIL. Docs updated (alta CLAUDE.md ×2).
          Diff ground-truthed row-by-row vs source minutes (2020-03-11, 2021-01-13, 05-12,
          06-16, 06-30, 07-14, 09-08, 11-10, 12-08, 2023-12-13, 2024-01-10, 2025-12-09).
          *(original)* ~half of alta's true motion failures misrecorded (4 fabricated
          'APPROVED', 1 reverse 'FAILED (0-2)', 1 never-voted →Pass, 2 failed motions MISSING
          entirely); extends the logged alta line-wrap item.
      (b) **✅ slc PC missed-aye-blocks — DONE 2026-07-12.** Extractor fixes: unique
          FIRST-NAME resolution from attendance ("Commissioners Andra, Andres, ... voted
          'yes'" 2021 form + the 2023 clerk-garbled "Rich Anaya Brenda Scheer" lists);
          verbless quoted votes ("..., and Adrienne Bell, "yes"."); bare "The Chair voted
          Nay as a tie breaker" → this meeting's chair; phantom mid-roll "The motion
          passed." split MERGED back into its motion (with petition/new-matter +
          names-recorded guards; also fixed a latent aye=nay=abstain=recuse list-aliasing
          the merge would have mutated); scrivener contradictory all-nay roll vs "passed
          5-3" → honest tally-only 5:3 (zero-aye+carried is impossible); "All OTHER
          Commissioners voted yes" → present-minus-named. All 6 audited rows verified
          fixed at source + bonus recoveries (2021-10-27 m1-m3 full 8:0 rolls,
          2022-02-23 7:0+abstain, 2023-01-25 7:2, 2023-03-22 9:0): 15 motion-keys
          changed, +43 member rows, motions 777→776 (the phantom), validator 0 hard
          errors / 0 tally mismatches, validate_city 25 PASS / 1 WARN (documented) / 0
          FAIL, rebuilt + federated. Doc counts refreshed (776 motions / 5,376 rows /
          290 non-unanimous / 261 rec = 218P/43N / 308 final / 207 procedural — the old
          "740/5,333" was already stale pre-fix).
          *(original)* 6 rows (first-name lists, missing 'voted' verb, chair tie-break
          vote, mid-roll 'The motion passed.' split creating a phantom motion).
      (c) **✅ midvale 'Gouncil' OCR roll dropout — DONE 2026-07-12.** Council roles regex →
          `[CG]ounci[l!]` (tolerates Gouncil/Counci!/Gounci! — 138 OCR role tokens); names
          still captured as printed. Re-extract: **52 motions repaired, +66 vote rows, all
          additive** (0 removals) — the 4 lost NAMED NAYS landed exactly as audited
          (m533 3-1→3-2 +Brown Nay, m537 2-0→4-1 +Brown Nay, m569 3-1→3-2 +Glover Nay,
          m681 3-0→4-1 +Gettel Nay; 2022-05-03 spot-checked at source). v_contested now 52
          (per-city + federated agree). Rebuilt + validate_city 25 PASS / 0 WARN / 0 FAIL.
          NOTE: the Tier-A "2025-08-19 m1 duplicated roll-call motion" is STALE — verified 0
          duplicate (member,vote) rows anywhere in midvale (both CSVs + db); the two docs on
          that date (regular + truth-in-taxation) are cleanly separate meetings.
          *(original)* 45 vote lines across 41 files; 4 lost NAMED NAYS (m533/537/569/681
          Brown/Glover/Gettel) + tally undercounts; v_contested + margins misstated 2020-23.
      (d) **✅ south_salt_lake PC vote-block truncation — DONE 2026-07-12.** Three root causes
          fixed in the (shared council/PC) extractor: (1) FOOTER_RE missed the dash-less PC
          running footer ("South Salt Lake City Planning Commission [Regular ]Meeting <pg>")
          → footer broke rolls mid-block; (2) FOOTER_RE's bare `\d{1,3}` alternative had a
          `.*` tail — EVERY line starting with a number (all agenda headings + findings
          lists) was silently stripped, the true cause of the 83 'uncaptured' texts; (3) the
          blanks end-of-roll counter never reset on non-blank lines (footer-stripped gaps
          accumulated to 3). Plus `strip_embedded_drafts()`: the 2026-05-07 PC file embeds
          the DRAFT 2026-02-19/2026-03-05 minutes as approval attachments — parsing now cuts
          at an embedded full-minutes header with a mismatched date → the 8 duplicate motions
          (m8-15) are GONE. find_motion_text scan window 30→140 lines with a previous-motion
          boundary; ITEM_HEADING margin-anchored (≤4 spaces) so findings lists aren't
          headings. Result: 17 truncated tallies restored to full rolls (0 pass/fail flips),
          motions 238→230, uncaptured 63→11 (rest have no label/heading in source), council
          side text-enriched only (0 tally changes). Crosswalk rows added for the 2 newly-
          emitted labels (Budget Amendment, Public Hearing Action). Rebuilt; validate 23
          PASS / 2 WARN (documented extensions) / 0 FAIL. Residual (honest): a few ADJOURN
          rolls physically cut by appended STAFF REPORT attachments in the source PDFs.
          *(original)* ~20 sub-quorum '1-0/2-0/3-0' tallies (true 7-0) from page-break/
          watermark splits + 8 duplicate motions from DRAFT minutes embedded in the
          2026-05-07 PC file + 83 'uncaptured' motion_texts that exist in source.
      (e) **✅ magna — DONE 2026-07-12.** Council extractor rebuilt: (1) motion_text now
          spans the full anchor→result window (the old per-span collector missed the
          window's 2-line lookahead → ~338 texts truncated at the first wrap; 855 texts
          lengthened; **council disposition NULL 42%→10%**); (2) dissent grammar captured
          — "votING in opposition" (gerund), quoted per-member rolls ('X voting "Aye"'),
          "nay/NO vote(s) from X [and Y]", "being the/had the/casting a "No" vote", wrap
          across the result line — **split-tally motions with 0 named rows 41→1** (the 1:
          the vote word is physically missing in the source render), contested 26→45,
          named rows 72→144, +2 real tallies ("failed 2 to 3", "vote to be 3 to 2");
          (3) m632's 'Died (no second)' UNFABRICATED — DEATH regex no longer matches bare
          "no second" prose, the ♦♦♦ section divider is a hard scan boundary, and a NEW
          mover before any result ends the motion honestly as `result="No result
          recorded"` → NULL outcome (lib rule extended; 11 such rows, each a real
          seconded motion whose minutes print no result — the old code bound them to the
          NEXT item's result, a misattribution CASCADE verified at source on 2022-09-27
          m3/m4, 2020-01-28 m8/m9, 2024-06-25 m11/m12); (4) supermajority guard kept —
          2024-06-25 form-of-government now "3-2 Fail" (word looked up past the wrapped
          roll). Ceremonial crosswalk row added. Rebuilt + federated; validate_city 22
          PASS / 3 WARN (documented) / 0 FAIL; docs updated (magna CLAUDE.md ×2 + root
          quirk line).
          *(original)* ~338/899 texts end mid-phrase → the 42% NULL rate is an artifact;
          split-vote named dissenters uncaptured (33/41 tally motions have 0 vote rows);
          m632 fabricated 'Died (no second)'.
      (f) **✅ kearns — DONE 2026-07-12.** PC: the flattened Vote-text window is now cut at
          the next agenda item ("N)") / Motion block — m596/m598's "1-3" (bled from the
          NEXT item's "Phase 1-3 Ordinances" title) is gone; results now the clean
          "unanimous in favor Pass". PC dissent verb accepts "votED nay" — m610 = "3-1
          Pass (nay: Thomas)" with the named Nay row, + 2 bonus dissent captures
          (2020-01-13 Hatch, 2025-07-07 Thomas). Council: ROLLCALL_HDR also accepts
          "(carried|passed|failed) by the following vote:" — 5 full quoted 5-aye rolls
          recovered from the 2021-22 back-catalog (incl. m227's; +20 vote rows). Both
          validators PASS; rebuilt + federated; 24 PASS / 1 WARN / 0 FAIL.
          *(original)* m596/m598 next-item '1-3' bleed into PC results + incomplete
          named-roll harvest of the 2018-23 back-catalog (m227 full roll → 0 vote rows;
          m610 named Nay missing).
      (g) **✅ white_city Died class — DONE 2026-07-12.** Died-for-lack-of-second motions are
          now RECORDED as `Died (no second)` rows instead of skipped (the old code both
          dropped 7 entirely and let 6 slip through as bare 'Fail' via a [:om+30] slice
          that truncated the lack-phrase mid-match); LACK_SECOND tolerates "dies"/"the
          lack". **13 Died rows** — exactly the audit's 6+7; 0 bare-Fail died rows remain
          (the 1 Fail left is the genuine 2-3). m267 → its 3 named Nays captured (dissent
          LIST handler: "showing that Mayor Flint, Council Member Little, and Council
          Member Cardenaz, voted in opposition"); m569 → "4-1 Pass" + Huish Nay ("with 4
          in favor and 1 opposed" tally + "casting the opposing vote" verb) — both now in
          v_contested (37). Rebuilt + federated; 24 PASS / 1 WARN (pre-existing
          dissent-only tally style) / 0 FAIL.
          *(original)* extractor condenses 'died for lack of a second' to bare 'Fail'
          (6 rows should be Died) + 7 died motions never extracted + m267 3 named Nays
          stored tally-only + m569 4-1 contested vote stored bare 'Pass'.
      (h) **✅ duplicate documents — DONE 2026-07-12.** copperton: the "2025-07-02" PC doc is
          the DRAFT of 2025-05-13 (PMN label "May minutes.pdf", in-body date May 13) —
          removed from minutes_index.csv, markdown moved to _removed_duplicates/, raw
          retained, honest row added to minutes_unrecovered.csv; PC all_votes 57→51 rows
          (exactly the audit's prediction; deny-class ×2 inflation gone).
          cottonwood_heights: 2024-01-02 portal/PMN pair byte-identical past headers —
          PMN copy dropped (portal kept), stale votes/ JSON removed, 2024-01-02 rows 56→28.
          Both rebuilt + validate (24/1/0, 25/0/0 — WARNs pre-existing).
          *(original)* copperton PC 2025-07-02 = draft of 2025-05-13 (deny class ×2
          inflated); cottonwood_heights 2024-01-02 portal/PMN pair (8 motions double-counted).
      (i) **✅ st_george merged died-motion rows — DONE 2026-07-12.** _consume_motion_block's
          text loop no longer swallows sibling motions: a nested MOTION: header, a
          died-for-lack-of-second sentence, a withdrawal sentence, or a prose voice-vote
          outcome now ends the block — died/withdrawn/superseded motions are their own
          rows ("Died (no second)" → Died; "Withdrawn (no vote)" / "No vote recorded
          (superseded)" → NULL outcome via the shared-lib no-vote set). ALSO fixed the
          CSV writer's standard-violation: zero-member motions were dropped entirely
          ("tally-only -> none") so they never reached the db — they now emit the
          standard single placeholder row. Result: 13 recovered no-vote motions (3 Died
          incl. all of m178/316/1379's dates, 1 Withdrawn, 9 superseded restatements —
          e.g. the 2022-08-18 truth-in-taxation sequence is now 5 honest rows instead of
          one merged row wearing Larkin's text and the final 4-1); the voted siblings
          keep their correct own text+roll (2023-04-11 verified). m2457 REVIEWED, left
          as-is: a genuinely mixed-direction motion ("denial of the C-2 ... but approval
          of a PD-C") — the "Negative recommendation" label reflects the deny-C-2 head;
          no honest single reclassification exists. Rebuilt + federated; 26 PASS / 0
          WARN / 0 FAIL.
          *(original)* m178/316/1379 — died/withdrawn motions collapsed into voted
          siblings; Died invisible + m2457 reclassify.
      (j) **✅ draper + herriman — DONE 2026-07-12.**
          draper PC: NARR_VOTE tolerates the clerk's comma/typo forms ("Squire, voted,
          "Aye"" / "votes, "Nay"") + "voting N-M in favor" tallies + narrative recusals
          ("Ogden recused himself") + a vote-evidence flag so a moved-but-withdrawn item
          is "No vote (application withdrawn)" instead of a fabricated denial — m1267 now
          the true "3-2 Negative Recommendation" with all 5 names, m1007 honest, 3
          voice-only motions gained full named rolls, 3 recusals + 2 named-nay pairs
          (Hawker + Van Hoff) recovered; several results now carry the PRINTED "N-M in
          favor" tally (3-2/4-1 splits previously shown as 3-0/4-0 — hidden dissent).
          draper council: parse_grid PAGE-BREAK indent repair — post-footer grid rows
          gain a constant indent that shifted every X into Absent; an absent-majority
          grid (physically impossible) now re-buckets with indent-normalized X positions
          (kept only if it yields ayes) — 2025-01-07 Ord #1630 0-0→4-0 (Vawdrey absent),
          2025-05-06 1-0→4-0 (Green absent), both "passed unanimously" ✓. 25/0/0.
          herriman: inline narrative rolls ("Mayor Watts, ... voted aye, and ... voted
          nay") — m280-282 now carry the full 5-member 3:2 rolls (Ohrn+Henderson Nay);
          OUTCOME_RE crosses single line-wraps (21 truncated result strings healed,
          "The motion passed with the" → full sentence) with prose/page-number tail
          guards. Tier-A form-feed item SATISFIED: 647/648 named tallies reconcile; the
          1 residual "mismatch" is the source's nays-first "failed 3:2" convention
          (roll 2A/3N + Fail agree — cottonwood-style prevailing-side-first, honest).
          Both rebuilt + federated; 25/0/0 both.
          *(original)* draper 2024+ page-break-split grids (corrupt 0-0/1-0 tallies +
          phantom Absents; m1267 aye-sentence never parsed, m1007 misattached) — same
          class as herriman m280-282 narrative rolls + wrap-truncated result_raw.
      (k) **✅ emigration_canyon — DONE 2026-07-12.** Extractor: "recused
          himself/herself" added to both dissent regexes (→ Recuse bucket, new to this
          city — crosswalks/vote_values.csv row added); new ROLLCALL_RE for the inline
          full roll ("<Name> voting "Aye/Nay"" ×5, 2023-08-22); aye/recuse now emitted
          end-to-end (JSON → all_votes.csv → roster; validate_votes.py reconcile updated).
          m89 → Brems Recuse row; m182 → full 5-name roll (4 Aye + Harris Nay). Contested
          = 5 (doc's "3" corrected below). +4 rows net, validator PASS, rebuilt +
          federated, validate_city 22 PASS / 3 WARN (documented) / 0 FAIL.
          *(original)* m89 recusal + m182 full 5-name roll never extracted (the doc claim
          "3 contested council motions" is wrong — there are 5).
      (l) **✅ taylorsville no-vote rows — DONE 2026-07-12.** PC extractor now emits the
          block's explicit fate when there's no roll/tally/unanimity: m835 → "Withdrawn
          (no vote)" (outcome NULL via a fork outcome_of rule), m836/m842 → "Died (no
          second)" (→ Died), m887 → "Tabled (no quorum)" (→ Continued). m688/m770
          deliberately keep "No recorded vote" → Pass (verified at source: their votes
          live on the companion "motion stands"/amended rows — true passes, exactly the
          audit's no-blanket-map warning). m130 re-verified already-correct (v3); m131
          reviewed — Pass matches the amended motion's fate, left as-is. 26 PASS / 0 / 0.
          NOTE: fixed a live instance of the HANDOFF glob[0] landmine — a stray
          db/civic.db (created by a read-only sqlite3 query) had hijacked the fork's
          `glob("*.db")[0]` output path; removed, rebuilt into db/taylorsville.db.
          *(original)* extractor should emit Died/withdrawn for m835/836/842/887 + review
          m131 ('No recorded vote' defaults Pass; 2 such rows are genuine passes).
      (m) **single known-wrong rows — PARTIALLY DONE 2026-07-12** (all fixed upstream in
          each city's extractor, re-extracted, rebuilt, validated):
          ✅ orem m1057/m1060 — PC outcome window now cut at the next numbered agenda
             heading (the adjacent item's "the motion on the item failed" recap bled a
             Fail onto 4:0 true passes); exactly the 2 rows flipped to "4:0 Pass".
          ✅ vineyard m1336 — failed final actions now keep the carriage word
             ("2:1 Denied (Final Action) — motion failed"): a majority-of-body failure's
             2:1 tally no longer reads as Pass; db outcome now Fail.
          ✅ millcreek m2514 — "seiber"→"sieber" clerk-variant alias; the dropped aye had
             fabricated a 3:3 tie ("Negative recommendation 3:3" Fail) — now "Positive
             recommendation 4:3" Pass with Skye Sieber's Aye row (matches source verbatim).
          ✅ wj m412 — split_motions' 2500-char block cap no longer truncates mid-roll
             (cap extends past a "vote was recorded as follows" lead-in): m412 recovered
             all 7 rows incl. Green's Nay ("6-1 Pass"); bonus: 2021-07-28 m4 regained its
             "5-1 Pass" result string. Rebuilt; 23 PASS / 3 WARN / 0 FAIL.
          ✅ holladay m842 — "There was no second." followed by an explicit "The motion
             passed…" no longer marks Died (clerk-formality note on chair procedural
             motions; both extractor copies patched): calendar motion now "The motion
             passed unanimously." → Pass. ALSO (Tier-A): the "10 duplicated Layton rows"
             are TWO REAL PEOPLE (Chair Howard Layton + Commissioner Chris Layton, 2022)
             — rolls with a surname collision now keep the printed first name (Chris/
             Howard Layton rows; the audit's "dedup" framing would have erased real
             votes); AND a second 2024-04-02 PC duplicate-doc pair found + removed (PMN
             1162237 dropped, 1190589 kept; index+JSON cleaned). PC dup rows now 0;
             22 PASS / 3 WARN / 0 FAIL.
          ✅ ogden m370/m450 — verified their member rows were ALREADY correctly resolved
             via db/vote_overrides.csv (Nadolski→Nay 6-1; Choberka/White→Nay 5-2); the
             asked-for **impossible-tally LINT added to scripts/db_build_lib.py**
             (non-fatal: tally aye+nay > the motion's own vote rows, ≥5-row guard so
             dissent-only cities are exempt; fires on exactly m370/m450). Forks not
             spliced — the lint is diagnostic-only (note kept here per fork discipline).
          ✅ sandy m80 — DONE 2026-07-12. Council extractor: "There was a motion [to X]
             by A and seconded by B" is now an anchor (wrapped-clause tolerant,
             double-fire guarded); an unresolved motion superseded by a sub-motion (or
             hitting the length cap, now 40) is PARKED and reclaimed at "The vote was
             taken on the main motion"; "Yes:/No: Council Members A, B, and C." label
             LISTS split into names; the roll look-ahead also fires on bare "The motion
             failed:" + label lines. m80 → "3-4 Fail" with the full 7-name roll, the
             call-the-question its own "6-1 Pass" row, budget-option-#2 its own "3-4
             Fail" row — 18 motions repaired corpus-wide (+81 rows), incl. two hidden
             3-3 tie FAILS (2022-12-20 solid-waste, 2024-06-18) and the 2020-06-09 CQ
             sequence. Validator: 0 unexplained mismatches (was 5 vs stale motions_std),
             0 hard failures; 21 PASS / 3 WARN (documented Legistar extensions) / 0 FAIL.
      ✅ Also done 2026-07-12: **the T1.3 method is folded into `/audit-city-data`**
      (new §2d2 module + failure-library additions — see the skill).
      ✅ orem neutral-rec cases — DONE 2026-07-12: the PC extractor now marks a forward
      that the minutes explicitly send as neutral ("Forwarded a neutral recommendation" /
      "with no recommendation" / "lack of four positive or negative votes" — Orem's
      four-concurring-votes rule) with "(forwarded neutral — four-concurring-votes
      rule)", and `recommendation_of` in the shared lib maps the marker → NULL (verified
      orem-only across cities.db; forks unaffected). 5 rows corrected — the audited
      m921/m988/m1051 + two more the phrase found (2022-09-21 3:2, 2026-01-21 3:0 with
      Crismon abstaining), all source-verified; outcomes untouched (carriage stays
      separate from direction). 25 PASS / 1 WARN / 0 FAIL.
- [x] **Evaluate which additional primary documents should be stored as on-disk markdown
      text (general plans, plan amendments, council-member proposal memos, land-use staff
      reports, &c.) — surfaced 2026-07-14.** Motivation: analysis currently leans on the
      minutes' *paraphrase* of what a document did, and paraphrases can invert meaning. Live
      case (Sandy, 2026-07-14): a clerk's one-line minute — "the establishment of a minimum
      density in all land use designations" — dropped the governing verb from Sharkey's actual
      GP amendment ("**Eliminate** the establishment of a minimum density…"), producing a
      completely reversed reading that stood until the primary memo PDF was fetched live. Full
      write-up: `~/Desktop/sharkey-amendment-misread-incident.md`. **What to evaluate / scope:**
      (1) Which document classes are high-value-for-analysis but currently text-absent — general
      plans (incl. draft-era + section tables like Sandy GP T19–T41), plan *amendments* &
      council-member proposal memos, land-use staff reports (the "why" behind a rezone), and any
      others whose *content* (not just their existence) gets cited. Note adopted-ordinance text
      is ALREADY captured per-city (`ordinances/`) — this is about the proposal/plan layer.
      (2) The catalog largely already exists: each city's `packets/index.csv` indexes the
      attachments (Sandy alone: 6,446 matter attachments) with live `source_url` + `matter_id`,
      but stored **index-only** (`stored_locally=no`) because the *binaries* blew the disk
      ceiling (~14.9 GB for Sandy). **Key reframing:** the ceiling was a PDF-storage problem;
      *extracted text* is ~1–5% of PDF size, so a text-only corpus is cheap — fetch → extract →
      store text (+ retain `source_url`, discard binary) sidesteps the disk objection AND is
      rot-proof (index-only URLs will 404 over time). (3) Highest leverage = also **index the
      text in the FTS layer** (`fts_minutes`/`fts_ordinance` companions, e.g. `fts_packet`) and
      **link to the enacting/considering motion via `matter_id`**, so the PRIMARY text becomes
      the default hit for "what does it say" questions (today FTS returns the minutes' summary of
      the amendment, not the amendment) and is one join from the vote. That directly lowers the
      token cost of source-verification (a `snippet()` ≈100 tokens vs. rendering a PDF page
      ≈2,000). Fold the chosen scope into `expand-city-sources` (which already built `packets/`,
      `ordinances/`, `housing_plans/`). Caveats: some attachments are `.docx`/`.pptx` or scans
      (OCR floor); the CURRENT adopted general plans are sometimes web/ArcGIS products with no
      PDF (Sandy "Pace of Progress 2050" — landing-page HTML only), so their text needs scraping
      at reduced fidelity — flag as an honest gap where so. Overlaps the deferred raw-PDF
      backfill (§ Deferred) and the county "General Plan… (text corpus)" menu item below. Start
      by scoping a **targeted tier-1** cut (council-member amendments + land-use staff reports +
      GP text, one city — Sandy) before any repo-wide fetch.

      **📝 PILOT SPEC DRAFTED 2026-07-16 → `PRIMARY_DOCS_PILOT_SPEC.md`** (Sandy-only; six
      classes: staff reports, member memos/amendments, GP text incl. station-area plans, GP
      amendment exhibits, development agreements/MDAs, dated zoning-code snapshot). Recon
      facts baked in: all 6,446 Sandy attachments carry `matter_id` but one flat
      `packet_kind` → a title+`legistar_matter`-join classifier with precision/recall gates
      is the core design; 2025 GP is ArcGIS-web-only (reduced-fidelity honest gap); Sandy
      code host is Municode browser-only (acquisition risk — probe order in spec §7).
      **✅ PILOT EXECUTED + ACCEPTED same day (2026-07-16, owner-approved scope: classes
      1–5 + class-6 side-probe).** 889 attachments classified (precision gates 98–100%),
      767 text sidecars (25.2 MB ≈ 1.1% of the binary counterfactual), pre-2025 GP fully
      recovered via Wayback + the 2025 draft-of-record from Legistar (the consultant host
      is NXDOMAIN — rot-proofing validated; 26 attachment 404s already), class 6 = honest
      gap (MCO `book/*` auth-gated; rollout list re-scoped to Municode-native/AmLegal
      codifiers), `doc_class` federated into `document` + `fts_packet` (11,893→12,660),
      **Sharkey acceptance test PASSED end-to-end** (memo snippet with the "Eliminate"
      verb → 3–4 amendment FAIL roll → Ord 25-01 5–2 adoption). Full results in the spec
      STATUS block. **ROLLOUT DECIDED + PREPARED (owner, 2026-07-16):** Source 7 added to
      `/expand-city-sources` (six→seven; classifier gates + pipeline + acceptance test);
      `doc_class`/`fetch_status`/`sha256`/`text_path`/`text_chars` standardized in
      SCHEMA_SPEC §9 (with the sanctioned discard-binary exception); the
      `polite_fetch.py` header-row guard added (both known fetcher bugs now fixed);
      **execution work package for a FRESH session: `PRIMARY_DOCS_ROLLOUT.md`** (Phase-0
      read-only portal triage → owner sign-off on priorities → batched per-city agents →
      single federation). Still queued after rollout: the 96 sandy needs_ocr scans
      (+ whatever the rollout accumulates — one repo-wide vision pass), Sandy GP
      Section 8 records-request lead (jwarner@sandy.utah.gov).

      **✅ ROLLOUT EXECUTED 2026-07-16 — all 30 remaining cities dispositioned, federated,
      accepted.** Phase-0 read-only triage (5 parallel evidence agents) bucketed all 30;
      owner signed off on the order + scoped section-cuts to CH+magna. Results:
      - **Bucket A/A-lite (9 cities, classified):** draper 922 (sr 895/pa 18/da 9; 676
        text-linked, 243 classified-index-only follow-ups), riverton 530 (sr 522/da 8),
        logan 213 (sr 207/pa 6 — the ONE fetch job: 818 MB fetched→discarded, 2.7 MB text,
        48 ok/165 needs_ocr/0 404s), lehi 272 sr (2024–25 window), slc 11 (PC-2026 slice;
        council ruled not separable), alta 11, emigration_canyon 17 (sr 15/pa 2),
        copperton 6, kearns 10 (9 + 1 mis-shelved recall catch). All gates ≥95% (most
        100%); every validate_dataset PASS. No city has Sandy's matter metadata — all
        classifiers are title/token(+sidecar-head) based; classify-in-place dominated
        (7/9 cities' sidecars pre-existed).
      - **Bucket B section-cuts (owner-scoped to 2):** cottonwood_heights 17 sections
        (16 sr + 1 general_plan) from the 12 appendix-TOC packets, whole-class verified
        (the gate caught+fixed a nested-Attachment boundary bug); magna 204 MSD sections
        (PC 186/Council 18), 204/204 invariant-verified. Reconciled scheme:
        `packet_kind=packet_section`, sha256 blank on sections (binary provenance = parent),
        `extraction_method=section_split`, parent_path/case_key extras.
      - **B-no/C honest completions (19 cities):** dated "classes not separable / honest
        zero" records in every packets/AVAILABILITY.md; ogden + lehi stale "no text corpus"
        doc-drift fixed (real layers: 164 + 553 sidecars).
      - **Class-3 addenda:** west_valley Vision West 2035 GP completed (all 12 chapters,
        11 fetched); st_george GP web-plan got 8 text sidecars (was html-only).
      - **Federation:** one build_cities_db.py run — integrity ok, reconciliation exact;
        fts_packet 12,660→12,930; `document` carries 2,982 classified rows across 12
        cities (incl. sandy's 889); packet_section 221 exact. **All 11 per-city
        Sharkey-pattern FTS acceptance checks PASS** (doc_class-filtered snippet returns
        each doc's OWN text; e.g. draper's Ord #1625 ROW memo → the 3–2 mayoral
        tie-break; magna's CUP2022-000691 → contested PC vote, Cripps Nay).
      - **New follow-ups queued:** repo-wide needs_ocr vision pass (~96 sandy + 165
        logan + singles elsewhere) — **✅ DONE 2026-07-17, see block below**; draper's 243
        classified-index-only rows — **✅ DONE 2026-07-17 wave-2** (241 fetched-ok
        [2.74 GB → 204 MB text, §9 discard-binary], 2 needs_ocr [same image-only PDF
        ×2 — future vision candidates, re-fetch required], 0 404s, 0 doc_class
        corrections; 0 classified rows remain index-only);
        murray/bluffdale/SSL future targeted packet fetches — **✅ DONE 2026-07-17
        wave-2** (murray: all 34 2023 Council/CoW bundles; SSL: 72 contested/land-use
        packets via `?packet=true`; bluffdale: 60 contested/land-use packets; all
        text-extracted, binaries discarded per §9, doc_class honestly BLANK on
        bundles [no ≥95% section anchor]; remaining rows stay index-only with future
        candidates ledgered per city); CH water-element + magna
        2-OAM plan docs as housing_plans class-3 candidates; WVC 5 GP appendix plans.
      Backups: `_backups/2026-07-16-primary-docs-rollout/`. Full record:
      `PRIMARY_DOCS_ROLLOUT.md` (triage table + sign-off + this closeout).

      **[x] Salt Lake County packets §9 doc_class BACKFILL — 2026-07-17** (the optional
      taxonomy-symmetry cleanup, executed concurrent with the vision pass).
      staff_report 44 classified (precision 100% whole-class; recall 100% on-disk; 5
      general-gov false-positives of the harvest's `%annex%` filter correctly blanked —
      Clark Planetarium "Annex" budgets etc.; 1 `no_extractor` RTF-saved-as-.pdf, matter
      4700, upgradable). member_memo/plan_amendment/development_agreement honest empties
      (county GP exhibits live in `plans/`; sole MDA instrument is index-only). County
      classifier joins matter_id → county-db MOTION TEXT (no legistar_matter table
      exists, unlike Sandy). §9 validator inapplicable by design (county header predates
      the packets contract; zero NEW failures vs backup). 13 index-only content-family
      rows queued as future fetch-and-classify candidates. **`build_search_layer.py`
      county-packets loop EXTENDED 2026-07-17 to carry doc_class** (it predated the
      column); federated + verified same day (44 in `document`, 43 in `fts_packet`;
      county acceptance check passes — the matter-9505 rezone SR, a contested 8–1
      Council roll, returns its own text under the doc_class filter). Backups
      `_backups/2026-07-16-primary-docs-rollout/salt_lake_county/`.

      **✅ REPO-WIDE needs_ocr VISION PASS — COMPLETED + FEDERATED 2026-07-17.**
      Queue derived from disk (recap numbers corrected): sandy 96 / logan 165 /
      draper 3 / riverton 1 / alta 1 / emigration_canyon 1. The recap's
      "cottonwood_heights packet_section" did NOT exist — all 17 CH sections were
      already `ok`; lehi's 11 needs_ocr rows are UNCLASSIFIED (blank doc_class),
      out of scope by design. **261 rows flipped** to `fetch_status='ok'` +
      `extraction_method='claude_vision'` (per-file honest labeling; §9 vocabulary
      unchanged): sandy 96 docs / 980 pp and logan 157 unique docs (165 rows, 8
      dup-URL pairs) / 2,896 pp were re-fetched politely and **sha256-verified ==
      the recorded 2026-07-16 hashes (0 mismatches, 0 404s)**, rendered at 150 dpi,
      and Read-tool vision-transcribed (Claude Code allotment, $0 API — the
      cf-vision-transcribe method precedent); draper = 2 vision + 1 **reclassified
      `html tag-strip`** (a trailing-dot filename hid a born-digital Legistar
      coversheet mislabeled `format=scanned`; content extracted under draper's
      existing 893-row convention, `format` corrected to `html`); alta 1 (ScanSnap
      law-firm memo); EC 1 (9-pp signed ordinance + MSD staff report, 2 map
      exhibits honestly marked). VERBATIM discipline verified: 26 docs
      spot-checked against the rendered pages (source typos preserved — "Vice
      Chiar", "Fianl"; honest `[map/plat page N — no text]` / `[illegible]`
      markers; all 25 split-doc merge seams continuous, several mid-sentence);
      statistical screens clean (0 mojibake, 0 <200-char files, index `text_chars`
      == sidecar length for all 261 rows; logan's 46 repeated-block sidecars are
      GENUINE source repetition — workshop+action bundles — confirmed on the page
      images). Provenance: re-fetch + vision entries appended to each city's
      `text/_fetch_log.jsonl` (`binary_retained:false`); sha256 columns untouched.
      Federation (one run): integrity ok, reconciliation exact, **fts_packet
      12,930 → 13,196 (+266 = the exact expected row count)**; FTS acceptance PASS
      in all 5 cities (each formerly-needs_ocr doc returns its OWN text under its
      doc_class filter — e.g. sandy's "Vice Chiar" member_memo, EC's Camp
      Kostopulos rezone). Layer docs (packets/CLAUDE.md + AVAILABILITY.md, logan
      parent CLAUDE.md) updated with dated notes. **Honest residuals:** (a)
      riverton 2026-04-21 Timberline DA staff report STAYS needs_ocr — the stored
      4.6 KB "PDF" is a Granicus MediaManager LOGIN PAGE and the source_url still
      302s to the auth wall: an ACQUISITION gap, not an OCR gap (queued below);
      (b) lehi's 11 unclassified needs_ocr rows (in scope only if a future pass
      classifies them). Backups: `_backups/2026-07-16-needs-ocr-vision/`.
- [ ] **[OPTION] STATE TIER — reevaluate how `ut_state` is integrated, ON ITS OWN TERMS (owner
      ruling 2026-07-29). ⏸ ut_state work is PAUSED until this is done.** Owner: *"it seems
      like we are trying to impose a municipal framework on the state documents and that is
      not the way to go."* Correct — and the evidence is structural, not cosmetic:
      **(1) `ut_state` has ZERO purpose-built tables in `gov.db`.** Compare `wfrc_mpo`, the
          precedent this ruling invokes, which got FOUR (`regional_project`,
          `project_vintage`, `project_history`, `projection`) because an MPO's work product
          is programmed projects, not roll calls. The state was federated purely as
          `motion`/`vote`/`person`/`meeting` — i.e. entirely in the city vote-shape.
      **(2) A BILL is stored in the `application` table.** `ut_state/db/ut_state.db` holds
          the 264 bills as 264 `application` rows — the schema slot meant for a MUNICIPAL
          DEVELOPMENT APPLICATION (the land-use permit pipeline). A bill is not a
          development application. There is no `bill` table anywhere in the repo, though
          `ut_state/legislation/bills.csv` exists on disk.
      **(3) The municipal classification vocabulary does not describe legislative votes.**
          `motion_type_std` (Land-Use | Ordinance | Resolution | Budget | Appointment |
          Contract-Purchase | Ceremonial | …) partitions a council's genuinely mixed stream.
          The state corpus is a **land-use/housing subset BY CONSTRUCTION** (264 bills chosen
          for that reason), so any Land-Use share merely restates the selection criterion.
          What actually distinguishes one state vote from another is **chamber + stage**
          (2nd/3rd reading, concurrence, committee recommendation) — already carried by
          `motion_type` (`floor`/`committee`) and the 23 `body` values.
      **What is NOT wrong — do not overcorrect.** The ROLL-CALL layer is a genuine fit: a
      legislature really does take named roll calls, and the 27,887 NAMED legislator votes
      across 1,208 roll calls are the repo's most exact vote data (0 tally mismatches).
      `vote`/`person`/`role` should stay. The imposition is in the MATTER layer (bill-as-
      application) and the derived municipal classification, not in the votes.
      **What "on its own terms" would likely mean** (design, not yet decided): a first-class
      **`bill` spine** — bill number, session, title, sponsor(s), subject, status/disposition,
      the stage sequence a bill passes through, and the roll calls hanging off each stage;
      probably `bill_stage` and `bill_sponsor`. Then the natural state-tier questions become
      answerable — *did this bill die in committee or on the floor · who sponsored the ADU
      bills · how did a legislator's votes move across a bill's stages · which enacted bills
      preempted municipal land-use authority* — none of which the motion/vote shape answers
      today. Cross-tier value is the payoff: state preemption → the municipal decisions it
      constrains. Also fold in the LUDMA statutes (218 sections) + Ombudsman advisory
      opinions (307) as first-class, not just FTS text — and note the **2025 LUDMA
      recodification** (10-9a→10-20, 17-27a→17-79) is exactly the kind of fact a statute
      spine should carry.
      **Method:** re-run the `/build-county-data-repo`-style scout+tier discipline for a
      STATE entity — inventory the actual work product first, model to that, then federate;
      do not start from the city schema. Read `wfrc_mpo/CLAUDE.md` for how the MPO
      reevaluation was framed.
      **Interim state:** `motion_std` for the non-city tier (item (j)) deliberately leaves
      ut_state's classification columns NULL rather than fabricating municipal labels — see
      the `caveat` row. That is a holding position, not the answer.

- [ ] **[DEBT] [NEW 2026-07-29] Two extraction defects surfaced by the ordinance-link pass —
      both change motion/vote counts, so both were deliberately NOT fixed under that task's
      expected-rows-only gate.**
      (a) **weber_county — a real adopting motion + its roll call were never extracted.** The
          2019-07-30 minutes carry *"Commissioner Harvey moved to adopt Ordinance 2019-13
          amending the Weber County Zoning Map to overlay the Solar Overlay Zone… aye/aye/aye"*,
          but no `motion` row exists for it — the roll is interrupted by *"Commissioner Harvey
          amended his motion to include that"*, which defeats the extractor. This is why ORD
          2019-13 is now honestly `unlinked` rather than linked: there is nothing to link TO.
          Fix in `weber_county/db/extract_votes.py` (handle a mid-roll amendment), rebuild,
          re-run `build_adopted_instruments.py`, re-federate. Logged in
          `weber_county/ordinances/README.md`.
      (b) **midvale — mis-dated duplicate meetings from a Revize filename-parsing bug.**
          Filenames of the form `M DD YY` are parsed as `MM D YY`, so three meetings are held
          under a WRONG date while the PMN backfill later promoted the same meeting under its
          CORRECT date — leaving duplicate motions: **`2023-11-07` ≡ `2023-01-17`** (the
          document's own header reads "JANUARY 17, 2023"), **`2020-12-01` ≡ `2020-01-21`**,
          **`2022-11-08` ≡ `2022-01-18`**. Note the repo currently lists 2023-01-17 as a PMN
          *recovery* while ALSO holding the same meeting as an audited doc under a wrong date.
          **Same family as cache's h3 duplicates** (a fetch/parse artefact double-counting a
          meeting) — and the 2026-07-29 sweep for that class checked INDEX MEMBERSHIP, which
          cannot catch this one: both copies are legitimately indexed, just under different
          dates. A date-collision detector is the missing check. Tabulated in
          `midvale_city_council/ordinances/CLAUDE.md`.

- [ ] **[DEBT] [NEW 2026-07-29] Three follow-ups surfaced by the Tier-1 fabrication pass.**
      (a) **[med] emigration_canyon `parse_present()` counts ABSENT members as present.**
          The city-era two-column layout prints `Council Members Absent:` as an empty column
          HEADER before the present names, so genuine single-column absences (e.g. 2024-07-30
          "Council Member(s) Absent: Catherine Harris") are credited as attendance. Touches no
          votes and no tenure bounds, but it means `meeting_minutes/roster.csv` `n_meetings`
          currently reads "meetings whose roll LISTED them", not "meetings attended" — an
          honesty gap in the attendance layer. Fix needs the same two-column care as the
          2026-07-29 `trim_to_council_block()` guard.
      (b) **[low, cosmetic] `scripts/db_build_lib.py:38 kind_of()`** mints `kind='committee'`
          only for names containing "board", so alta's new `BudgetCommittee` body lands as
          `kind='council'` / `stage='council_vote'`. `body.name` is correct and authoritative;
          only the coarse classifier is imprecise. SHARED SCRIPT — serialize any fix.
      (c) **[med] gov.db was STALE by ~3,000 motions before the 2026-07-29 federation.** The
          2026-07-25/26 Tier-1 audit fixes (cache_county OCR backfill, weber OCR, utah_county
          vote repair) were built into each entity's own db but **never federated**. The
          2026-07-29 rebuild carried them in: **county motions 24,346 → 27,376 · county votes
          35,318 → 39,237 · regional motions 958 → 959.** Root `CLAUDE.md` still quotes the
          pre-federation figures in two places (the `gov.db` bullet and the cross-city rules
          bullet) — update them, and treat "entity db rebuilt but not federated" as a standing
          hazard: there is no gate that catches it. Candidate: a staleness check in
          `validate_entity.py` comparing per-entity counts against gov.db.

- [ ] **[DEBT] Riverton Timberline DA staff report re-acquisition (2026-07-17).** The one
      vision-pass residual: `packets/` row 2026-04-21 `Council_clip839_att10_26-06_
      Timberline_Development_Agreement_CC_Staff_Report.pdf` is an auth-wall HTML
      capture (Granicus MediaManager login), not a document; anonymous GET still
      redirects to login. Recovery paths: riverton's other Granicus/Legistar
      download hosts, the meeting's full packet PDF (the staff report may ride
      inside it), or a records request. Also correct the row's inaccurate
      `format=scanned` when resolved. Never fabricate; the row stays `needs_ocr`
      until the real document is acquired.
      **↩ WAVE-2 STATUS (2026-07-17 evening): both public probes DEAD — GRAMA is the
      only remaining channel.** (a) The Legistar S3 twin is a different id space
      (download-id 4040041 → AccessDenied); Legistar InSite is WAF-locked (19-byte
      "Invalid parameters!" stub), OData disabled. (b) The "full packet" is only the
      short agenda outline already stored (AgendaViewer 302s to it; PMN carries the
      same). DISCOVERY: the auth-wall is PER-OBJECT — 5 sibling attachments on
      2026-04-21 (att8–att12: Ord 26-06 cover + ordinance, this CC staff report,
      Res 26-15 + Drought Plan) were all mislabeled `scanned`/`needs_ocr` → all 5
      corrected to `fetch_status=error:auth_wall`, `format=na` (§9 escape vocab),
      documented in packets/AVAILABILITY.md. Drafted GRAMA (combined with riverton's
      6 dead minutes leads) in the wave-2 report. Re-probe only if InSite access is
      ever obtained.
- [ ] **[OPTION] Primary-document WATCH LIST — assess cost/benefit before admitting any class
      (2026-07-16).** Deferred document classes of potential interest are recorded in
      `PRIMARY_DOCS_PILOT_SPEC.md` **Appendix A** with per-class value hypotheses + cost
      notes: subdivision/design standards, fee schedules + impact-fee analyses, annexation
      policy plans (Lt. Gov centralized source), MIH annual reports, transportation/water/
      sewer master plans, RDA project-area plans, hearing-officer/BoA decisions, litigation
      settlements, budgets/ACFRs, applicant narratives, building permits (structured, county
      menu; Ivory-Boyer). Rule: a class is admitted only with a demonstrated question
      pattern + written cost/benefit (source, fetch cost, extraction fidelity, corpus size);
      otherwise it stays on the list. Revisit after the Sandy pilot ships.

## [OPTION] Multi-level entity tier — counties → regions → state (started 2026-07-11)

Generalizing the 16-city repo to a multi-level Utah government archive. Design + full plan
approved 2026-07-11 (`~/.claude/plans/clever-stirring-axolotl.md`). Model in SCHEMA_SPEC §0.

**DONE (backbone, verified):**
- [x] **Entity registry** — `registry/entities.csv` (26 entities: 16 city / 7 county /
      2 MPO / `ut_state`) + `registry/relationships.csv` (42 `within`/`member_of` edges,
      with `confidence`). Governance forms + FIPS recorded per county.
- [x] **`scripts/entities.py`** — single source of truth; reserved fed_index bands
      (city 1–99 / county 101–199 / regional 201–299 / state 301–999); fails loud on
      band overlap or dangling relationship. **`scripts/cities.py` is now a `level=='city'`
      shim** — proven byte-identical `CITIES`/`SLUGS`/`DIRS`; all consumers unchanged.
- [x] **Federated DB generalized** — `build_cities_db.py`: `gov_level`+`state` on all 8
      core tables, new `entity` + `entity_relationship` tables, build loop iterates the
      registry. Rebuilt + verified: every existing city value byte-preserved (golden
      checksum diff), 16/16 validate 0 FAIL, FK/integrity clean. (`cities.db`→`gov.db`
      rename DEFERRED to a doc/consumer sweep — `build_search_layer.py`/`roster_lib.py`
      hardcode the name.)

**NEXT (acquisition — one entity at a time, like the city builds):**
- [x] **Phase 2 — Salt Lake County elections promoted to canonical (DONE 2026-07-11).**
      `salt_lake_county/elections/` now holds the canonical county SOVC
      (`slco_municipal_results_long.csv`, 246k rows, 2007-2025, all SLCo municipalities)
      + derived `election_results_by_contest.csv` (`build_elections.py`; council/mayor,
      807 contest×candidate rows, jurisdiction-tagged) + CLAUDE.md/SOURCES provenance
      (raw xlsx LINKED to `~/Desktop/slco-election-archive`, not re-hosted).
      **Elections now have a DB form** (closes REFACTOR_PLAN §5.3): `election_race`
      (308 rows — all 16 cities' audited 25-col races + containing `county`,
      authoritative winners/margins) + `election_result` (807 — SLCo county tallies) +
      view `v_election_city` + 3 caveats. Verified: county derivation reproduces SLC's
      audited 2023 winners/votes EXACTLY; 8 core tables byte-preserved; FK/integrity clean.
      **Follow-up (deferred, not byte-risk-worth-it now):** mechanically re-point the 7
      cities' 3 build pipelines (SLC per-year filter / sandy-wj-wvc xlsx parsers /
      sj-millcreek-taylorsville long-slices) to derive DIRECTLY from the county canonical,
      byte-identical, then delete the redundant per-city raw copies (true dedup). Lineage
      is proven + documented; only the mechanical consolidation remains.
      **SLC slice DONE 2026-07-19:** `clean_elections.py` +
      `geo/build_precinct_district_map.py` re-pointed at the canonical; gate proven —
      slc_races.csv + slc_results_by_candidate.csv + precinct_to_district.csv
      byte-identical (slc_results_by_precinct.csv changed in exactly the 62 SLC rows of
      the county's lead-(v) `Cumulative` relabel, precinct-label-only, all votes=0); all
      18 per-year raw copies were first proven byte-identical slices of the canonical,
      then deleted (backups `_backups/2026-07-19-pv-tierb-low/lead-tu-slc/`);
      sources index slc branch now emits a canonical-pointer row.
      **sandy/wj/wvc + sj slices DONE 2026-07-19 (same wave):** all four re-pointed with
      the hard byte-identity gate passed on races + by_candidate + by_precinct; redundant
      raw xlsx/slice copies deleted (backups `_backups/2026-07-19-pv-tierb-low/lead-u-*`);
      note — the audited 25-col races files were never produced by the old on-disk
      scripts (narrower legacy schema + sandy's out-of-tree 2019 At-Large audit fix), so
      the builds were rewritten to consume the canonical AND reproduce the audited output
      exactly; sandy's non-SOVC RCV2021 final-round constants kept intact.
      **millcreek = DOCUMENTED EXCEPTION (2026-07-19, do NOT re-point):** the county
      canonical is odd-years-only — millcreek's founding 2016 election (10 races) exists
      ONLY in its per-city slice; re-pointing would silently drop it. Slice RETAINED as
      the sole 2016 holder (files proven untouched). Unblock = extend the archive to the
      2016 even-year SOVC first.
      **taylorsville = REAL FINDING (2026-07-19): a genuinely-missing 2019 D1 municipal
      primary** — the canonical carries it (Burgess 728 / Gehrke 371 / Quigley 229, from
      2019-08-13-municipal-primary-sovc.xlsx) but taylorsville's audited races + docs
      claim "no 2019 primary"; proven the SOLE re-point diff. Adoption + re-point queued
      this wave (after the 2019 pseudo-candidate canvass fix, which must land first).
      **✅ taylorsville DONE 2026-07-19 (adoption + re-point + slice deletion):** the 2019 D1
      primary was cell-verified against the raw workbook (per-precinct Total Votes TAY001
      149/89/6 … TAY008 178/91/46 → `Total:` 728/371/229 = 1,328; zero suppression, no
      method-label pseudo-candidates; top-2 Burgess/Gehrke = the D1 general's two candidates)
      and ADOPTED via the pipeline (it flows straight from the canonical's
      `TAYLORSVILLE CITY COUNCIL DISTRICT 1` primary contest). `clean_elections.py` re-pointed
      to `salt_lake_county/elections/slco_municipal_results_long.csv` (Cumulative + `TAY `
      sheet-code skips added; 2019/2021 generals still raw-parsed from the retained
      `raw/sovc/*.xlsx`). **Hard byte-identity gate PASSED:** races/by_candidate/by_precinct
      reproduced byte-for-byte vs the prior committed files, SOLE diff = the 1 primary race + 3
      candidate + 15 precinct rows in sort position (38→39 races, 90→93 cand, 1,353→1,368 prec).
      Redundant per-city slice `raw/municipal_results_long_taylorsville.csv` DELETED (backed
      up). Docs corrected (election_results/CLAUDE.md, root CLAUDE.md, README.md,
      VERIFICATION.md addendum, sources.csv canonical-pointer row). `validate_city.py` =
      25 PASS / 1 WARN (pre-existing i.weeks staleness, unrelated) / 0 FAIL. cities.db NOT
      rebuilt (federation deferred with the pending `build_cities_db.py` run above). Backups
      `_backups/2026-07-19-pv-tierb-low/taylorsville-elections/`.
      **2019 pseudo-candidate canvass fix LANDED 2026-07-19:** the sole affected contest
      archive-wide was the 2019 general `ALT Council` sheet (trailing CUMULATIVE header
      block → family-B rejection → family-A misparse of method sub-header labels as
      candidates); normalizer now exact-match rejects method/section labels at every
      candidate-detection site (`METHOD_LABELS`/`is_pseudo_candidate()`). Canonical −11
      pseudo rows +3 real (DAVIS 77/MORGAN 69/LENCHES-JHAMB 29, raw-cell-verified);
      by-contest 7→3; lead-(m)/(v) proofs re-ran clean; all six re-pointed cities
      byte-identical; non-re-pointed-city races sweep 0 hits (the class never leaked).
      Backups `_backups/2026-07-19-pv-tierb-low/pseudo-candidates/`. ~~**PENDING:** a
      `build_cities_db.py` re-federation (next run) to flush the 7 stale `ALT Council`
      pseudo rows from gov.db `election_result` (2019 is below alta's audited floor, so
      `election_race` is untouched).~~ **DONE 2026-07-20** (Phase-4 session step 0):
      re-federated clean (integrity ok / reconciliation exact / 193-31 / 54,029 / 189,261
      unchanged); `ALT Council` 2019 verified = exactly the 3 real candidates (Davis 77 /
      Morgan 69 / Lenches-Jhamb 29), pseudo rows gone; election_result 2,172.
- [~] **Phase 3 — Salt Lake County full build (template) — LARGELY DONE 2026-07-11.**
      Built + federated into gov.db (gov_level='county', offset 101; dir `salt_lake_county/`;
      authoritative doc `salt_lake_county/CLAUDE.md`): **legislative** (Council via Legistar
      `slco` — 2,912 motions / 3,659 named votes / 411 full roll calls; the Council is
      tally-primary in minutes but Legistar EventItemVote gives fuller named rolls; 253
      minutes md); **agencies** (RDA + MBA, 49 min); **land_use** (County PC + Mountainous PD
      PC, 97 min via PMN body 712 — searchable; PC vote extraction pending); **development**
      (146-action development-pipeline table → motion/vote); **plans** (14 docs: West/Wasatch
      GP + 6 township GP + MIH, searchable); **projections** (140 rows Gardner v2025+v2022);
      **gis** (34-layer UGRC/county catalog, link-not-mirror + tiny derived); **elections**
      (Phase 2). New gov.db tables `development_application`/`projection`/`gis_layer`;
      fts_minutes spans 413 county docs; v_contested_all shows 82 county contested;
      FK/integrity clean. **packets/staff reports DONE 2026-07-11** (310 agenda PDFs + 49
      land-use staff reports + 95 catalogued attachments; 358 in fts_packet — searchable).
      **ordinances DONE 2026-07-11** (67 adopted ordinances, text + enacting-vote link — 64
      high/3 med; ordinance_no honestly blank — Legistar only has unsigned drafts; 23
      land-use). **land_use PC votes DONE 2026-07-11** (tally-primary ceiling like WJ/SJ PC:
      2 PC bodies, 310 land-use motions, 16 named dissent/abstain rows, 297 tally-only —
      federated as a `planning` body). **Work-Session/COW backfill DONE 2026-07-11**
      (Committee of the Whole is a heavy voting body — +2,781 votes; +143 minutes).
      **Housing Authority DONE 2026-07-11** (HACSL/Housing Connect — minutes from
      housingconnect.org, NOT PMN 2535 which has none; 68 minutes + NAMED board: 327
      motions / 1,695 votes). **ALL 10 CORE-METHOD MODULES DONE.** County in gov.db:
      7 bodies, 4,857 motions, 8,142 votes, 176 contested, 67 vote-linked ordinances,
      261 development actions, ~1,049 searchable docs; 16 cities byte-identical; clean.
      **NEXT:** the **`build-county-data-repo` skill** (Phase 3c) generalizing this proven
      pipeline; refresh `salt_lake_county/CLAUDE.md` (stale re: PC/ws/HA); then the "County
      content menu" enrichments + Phase 4 (other 6 counties). Link fully to the 7 cities.
- [x] **Phase 4** — template the other 6 footprint counties (utah, weber, cache, summit,
      washington, juab), value/effort-gated. Cheap high-value modules (elections canvass,
      projections) can run even where cities are thin.
      **✅ EXECUTED + FEDERATED 2026-07-20 (owner-authorized package; 6-scout recon wave →
      posted gate → 18 build agents in 1 conflict-planned wave (5 Fable elections
      normalizers) → 5 closing agents → solo stage-C federation). All 30 agents 0 FAIL
      (1 transient API interruption + a 7-agent session-limit interruption, all resumed
      clean via transcript). FEDERATED: 36 built entities; county motions 24,346 / county
      votes 35,318 (utah 10,089/2,765 · weber 4,242/12,105 · summit 3,346/518 · cache
      1,812/11,788 + SLCo unchanged 4,857/8,142); election_result 5,482 across ALL 7
      counties; projection 980 (140×7); gis_layer 135; development_application 864
      (+summit 571, utah 32); fts_minutes 12,392; ordinance 7,542 (Weber's never-published
      807-instrument register reconstructed from minutes, 73% motion-linked). GATES: the
      31 cities byte-count-identical (49,172 motions / 181,119 votes / 680 races —
      purely additive), 193-31 intact, FK 0, integrity ok, reconciliation exact,
      coverage.json proven unchanged. Stage-C shared-script edits (backed up
      _backups/2026-07-20-phase4/stage-c/): _county_entities() db-gate dropped (db-less
      counties federate projections/gis), build_fts null-path guard (link-only plan rows,
      e.g. Cache's StoryMap-only 2023 GP), cache build_db.py standard referral table
      (empty by design). Registry: db_rel_path set for utah/weber/cache/summit; portal
      column filled for all 6.**
      **Headline findings:** cache + weber counties print FULL NAMED roll calls in
      minutes (richer than SLCo's tally-only; weber 99.6% named 2015+, depth to 2000;
      cache 97.5% named 2021+); utah county's era ceiling is INVERTED (named 2015-16,
      tally-only OCR 2017+); cache PC grammar seam 2024-11-07 (tally-only decade → full
      named rolls); weber Ord 2025-27 DISSOLVED the Ogden Valley + Western Weber PCs into
      one countywide PC eff. 2025-12-03 (Ogden Valley incorporation fallout — watch item
      + future city candidate); utah county's posted "2023 General SOVC" is actually the
      2022 SOVC UNSUPPRESSED (county publication error — quarantined, never parsed);
      utah county 2023 RCV contests are entirely absent from the SOVC (recovered from
      archived rcvis tabulations, first-choice never presented as the RCV result); cache
      vote_overrides recovered 5 buried dissents (contested 178→182); summit closer
      caught + fixed a fabricated cross-body identity (Council surname map merging
      like-surnamed PC commissioners).
      **QUEUED FOLLOW-UPS (Phase-4 wave):**
      (A) **Per-city election re-point package** (byte-identity-gated per the SLCo
      precedent; evidence already banked): park_city→summit (county canvass carries PC at
      precinct grain, 49/50 rows match), st_george→washington (13 raws byte-identical;
      11/11 audited races match), lehi/provo/orem/vineyard→utah (52/52 winners),
      logan→cache (2023+ ONLY — Logan self-administered 2019/2021, city PDFs sole
      primary, millcreek pattern), ogden→weber (EXCEPT 2023 — county published the 2023
      municipal general bond-only; Ogden 2023 stays city-side sole source).
      (B) utah_county PC minutes backfill: 46 meetings 2020–2024 catalogued in the
      county's new CMS with exact filenames but media host cms.utahcounty.gov is
      NXDOMAIN mid-migration — retry when wired, else Wayback.
      (C) OCR-gated depth backfills (pipelines ready): cache legislative 2015–2020
      (scanned tally-only) + 1995–2014 archive; weber legislative 2000–2014 (~690
      born-digital, same grammar — cheap); summit council pre-2023 (453 scanned dates,
      up to 180MB files); washington pre-2019 minutes (2005+).
      (D) Elections residue: cache 2024 canvass image-only (OCR/vision); cache 2006–2016
      GEMS + 2018 HTML unparsed extensions; weber GEMS SOVC precinct grids unparsed;
      washington 2019-08 municipal primary never published (GRAMA lead) + 2018-06
      scanned primary; summit 2022-primary scans + 2024-June-primary unpublished.
      (E) Smalls: logan CLAUDE.md "North Logan RCV" aside appears WRONG (cache canvass
      proof) — verify + correct city-side; SLCo HA minutes_index 69 rows vs 68 files;
      summit PMN-1503 gap recovery (Snyderville 2021 ×4, Eastern 2022 ×5) + 14
      image-only PC minutes OCR + pre-2024 DocumentCenter staff-report pass; cache PC
      14 minutes-less dates via PMN 1479; weber WWPC-2020 GRAMA; county motion
      disposition layer (all county motions NULL — extend classifier); weber planning
      FTS→votes promotion (only if Ogden Valley/W-Weber becomes a priority); summit
      HA/RDA build-later (HA minutes accumulating since 2025-08).
      (F) Refresh-harness hardening candidate: the PMN browser search is
      captcha/erroring but a JSON POST to /pmn/searchresult.html with X-CSRF-TOKEN works
      (washington build proved it) — fold into pmn_crosscheck/refresh tooling. Tier decisions, evidence-based: **utah = FULL** (4 covered cities;
      canonical clerk SOVC 2016–2026 at vote.utahcounty.gov incl. a Draper-straddle
      report; RCV via rcvis.com — SOVC is first-choice only; no Legistar, custom Next.js
      portals, PMN bodies 2731/1711; agencies + dev-pipeline are honest soft spots).
      **cache + weber = MID with a real legislative vote layer** (both counties' minutes
      are born-digital with FULL NAMED roll calls — cache council 7 members "Aye: 7
      <names>" 2011+, weber commission per-member aye/nay back to 2000 — richer than
      SLCo's tally-only minutes, no API needed); weber's 3 PCs = FTS-only first pass
      (Ogden Valley incorporation = watch item + future city candidate). **summit = MID
      with the land-use layer funded** (two PCs, Snyderville Basin development pressure,
      staff reports posted; tally-only prose — no Legistar; elections rich: DocumentCenter
      precinct+canvass PDFs 2004–2026; HA nascent 2025 + RDA thin = deferred). **washington
      = LIGHT+** (elections marquee: outpost.washco XLSX/CSV/PDF canvasses, county
      administers st_george's elections; vote layer explicitly deferred — scanned OCR
      minutes, 3-member board, no API; AmLegal code is 403 bot-walled). **juab =
      CHEAP-ONLY confirmed** (elections 2023–2025 official via 3 channels — juabcounty.gov
      wp-content + vote.utah.gov canvass certs (2024+) + EV JSON API precinct breakdowns;
      2019/2021 municipal = confirmed DEAD on all official channels, honest gap stands).
      Cross-cutting: Gardner "Utah 2065" statewide workbook (v2025+v2022) covers ALL
      counties in one download → single shared projections agent. Legislative/PC first-pass
      floor = 2015 (deeper availability recorded in each recon.md; backfill queueable).
      Per-city election re-points (ogden/logan/park_city/st_george/lehi/provo/orem/
      vineyard → county canonicals) NOT in this package — queue after canonicals land,
      byte-identity-gated per the SLCo precedent. Phase 3 residual DONE 2026-07-20:
      salt_lake_county/CLAUDE.md refreshed (elections-canonical role + verified counts;
      backup in _backups/2026-07-20-phase4/; flag: HA minutes_index.csv has 69 rows vs
      68 minutes files on disk — reconcile when the HA layer is next touched).
- [x] **Phase 5** — MPOs (WFRC/MAG board votes + RTP/TIP) and `ut_state` (legislature
      land-use bills+votes via LegiScan; Property-Rights-Ombudsman advisory opinions as an
      FTS corpus; statewide projections). Sources verified in the plan.
      **✅ EXECUTED + FEDERATED 2026-07-20 night (3 scouts → gate → 6 Opus builders →
      doc-finalization; 10 agents, 0 FAIL — 1 lost-completion-signal stall + 1 dead
      detached crawl, both recovered by coordinator process-level checks + resumes).**
      The repo's first REGIONAL and STATE tiers, incorporated ON THEIR OWN TERMS
      (owner directive; caveat-table rows + memory recorded): MPOs are DATA-FORWARD.
      FEDERATED (39 built entities; cities AND counties byte-stable again;
      integrity ok / FK 0 / 193-31 / reconciliation exact): **regional 958 motions
      (wfrc 323 across Council/TransCom/Budget/RGC 2016–2026; mag 635 MPO Board+TAC
      2014–2026) with vote tables EMPTY BY SOURCE (tally-only ceilings verified,
      caveat rows live); NEW `regional_project` table 5,717 rows (wfrc 5,146 — 8 TIP
      vintages 2020-2025→2027-2032 + RTP-2050; mag 571 TIP/RTP/RPO,
      geometry-variant-deduped); projection now 3-tier (county 980 / regional 9,832 —
      city-area grain ANNUAL 2019–2050, both MPO forecasts proven control-totaled to
      Gardner V2022 — / state 140); ut_state 1,208 roll calls / 27,887 NAMED
      legislator votes (264-bill land-use subset, 12 sessions 2015–2026, 0 tally
      mismatches, via the PUBLIC le.utah.gov channel — NO account created; LegiScan
      = documented owner-gated alternative); document +309 advisory_opinion (307
      fetched via Wayback CDX — both state hosts now Cloudflare-walled) +218 statute
      rows, FTS-live.** Stage-C schema work (backed up _backups/2026-07-20-phase5/):
      regional_project DDL+loader; non-city loader generalization (gov_level from
      registry); advisory-opinion/statute document+FTS wiring; build_fts binary-junk
      guard (.md/.txt only); federated vote CHECK extended with verbatim 'Yea' +
      aggregate views treat ('Aye','Yea') as affirmative (source values never
      rewritten). Roster/seat tables: wfrc 10 repo entities ex-officio, mag 9 —
      cross-entity person joins live. HEADLINE FINDINGS: the **2025 LUDMA
      RECODIFICATION** (10-9a→10-20, 17-27a→17-79; old chapters = repealed stubs;
      repo city/county docs cite the OLD numbering — doc-sweep candidate for Phase
      6); the shell-page HTML-comment vote trap caught (would have fabricated ~2,200
      fake legislator votes — stripped + real 2025/26 floor votes recovered by
      voteid crawl); Gardner publishes NO machine-readable state scenario variants
      (baseline-only, honest).
      **QUEUED FOLLOW-UPS (Phase-5 wave):** ut_state 2025/2026 committee-vote
      (mtgvotes) linkage residual + special-session sweep + legislator party/district
      backfill (roster pages or the gated API) + LegiScan account (owner call);
      advisory opinions #102/#206 (Wayback-dead) + #142/#145 image-only (OCR/vision);
      late-2025 year-sequential opinion series; WFRC historical seat-tenure roster
      (raw material = every meeting's member table); MAG ~15 surname-only 2014-19
      movers; RTP2027 refresh seam (both MPOs; drafts catalogued, never blended);
      wfrc 2016 .WMA audio unswept; mag TAC pre-2020 absent (honest). Gate:
      **both MPOs = DATA-FORWARD regional builds** (the structured layers are the value;
      votes are honest thin tally-only). wfrc: Council minutes born-digital (~30-40
      motions/yr, mover/seconder named, dissent COUNT-only — dissenters never named;
      site archive is durable, PMN 2262 rolls off) + the crown jewels: 8 TIP vintages +
      RTP-2050 project FeatureServers (pin/$/year/phase/jurisdiction) + RTP-2023
      City-Area & TAZ pop/HH/jobs projections ANNUAL 2019–2050 (CityArea keys straight
      to member entities) + Wasatch Choice layers; org services1.arcgis.com/taguadKoI1XFwivx
      (470 services). mag: MPO Board minutes 2014+ born-digital (tally-only, mover/
      seconder named; PMN 8083/1480 recovery; **MPO Board is Utah-County-only** — the
      summit/park_city member edges are AOG/RPO, never imply MPO votes) + ArcGIS Hub 34
      datasets (TIP FY26-30, 2023 RTP, TAZ 2015-2050, city pop/emp projections, Housing
      Unit Inventory, Wasatch Choice Vision). ut_state: 4 datasets — legislation
      (le.utah.gov for bill text/status + its PUBLIC per-bill vote pages for named rolls
      if reachable; LegiScan bulk is the documented alternative but needs an account =
      OWNER-GATED, no account creation by agents), advisory_opinions (~300 OPRO LUDMA
      opinions 2006+, Cloudflare-fronted + commerce mirror), projections (state rows of
      the in-repo Gardner workbook + state-grain scenario variants), statutes (LUDMA
      Title 10-9a/17-27a + §13-43 XML via the le.utah.gov developer API → FTS).
      Legislators = DISJOINT person population (no surname auto-merge with municipal
      people). Stage-C schema work (Fable/solo): generalize the county-gated
      projections/gis/development loaders to non-city levels; new `regional_project`
      federated table for TIP/RTP; advisory-opinion/statute document loading. Bill
      floor: 2015 General Session (captures HB35-era through HB462/SB174).
- [x] **Phase 6** — generalize skills (`refresh-city`/`audit-city-data`/`validate_city.py`
      entity-aware), the `cities.db`→`gov.db` rename + doc sweep, README/CLAUDE rewrite,
      generated hierarchy index; register `wasatch_county` to add Park City's 2nd `within`
      edge; backlog: all 29 counties + remaining cities (SL County cities next per owner).
      **✅ EXECUTED 2026-07-20 night (same session as Phases 4–5 — the full owner-authorized
      package is COMPLETE).** Delivered: **wasatch_county registered** (42 entities; Park
      City 2nd within edge + MAG AOG edge; registered-only, backlog build); **generated
      hierarchy index** (`scripts/build_hierarchy.py` → `registry/HIERARCHY.md`, regenerate
      after any registry change); **entity-aware validation** (`scripts/validate_entity.py`
      — dispatches cities to the untouched validate_city.py, module-aware checks for
      county/regional/state; all 11 non-city entities 0 FAIL on first full run — and the
      run CAUGHT a real defect: summit+mag legislative minutes_index used non-canonical
      path columns and were silently absent from FTS → tolerant shared-loader fix, 349
      minutes now federated); **skills entity-aware** (refresh-city + audit-city-data:
      additive non-city sections — county 3-channel elections checks, MPO
      append-never-blend vintage rule, ut_state session sweep + shell-trap warning,
      one-federation rule; zero city procedures invalidated); **THE RENAME, sequenced
      LAST**: gov.db is the federated database, cities.db = maintained back-compat SYMLINK
      (refreshed by every build; all gates verified THROUGH the symlink — 193-31 / four
      tiers stable / coverage.json byte-stable), builder remains build_cities_db.py;
      **root doc sweep** (README + CLAUDE.md rewritten for the 4-tier 42-entity reality,
      every number live-verified — files-win corrections: election_race 655→680,
      fts_minutes 13,852 across 40 entities; advisory/statute corpora accurately described
      as file corpora with CSV catalogs, not gov.db fts tables; backups
      _backups/2026-07-20-phase6/). Final federated state: gov.db = motions 49,172 city /
      24,346 county / 958 regional / 1,208 state; votes 181,119 / 35,318 / 0 (tally-only
      by source) / 27,887; election_race 680 + election_result 5,482; regional_project
      5,717; projection 10,952 (3 grains); FK 0 / integrity ok / reconciliation exact.
      Residual smalls: cosmetic `cities.db` strings in a few script comments (symlink
      keeps them true; sweep opportunistically); `cities_db_SCHEMA.md` keeps its filename
      (referenced widely — rename is optional future polish); v_pc_divergence /
      disposition / re-points for the new tiers stay queued in the Phase-4/5 follow-ups.
- [ ] **WFRC-NATIVE HOLISTIC PACKAGE (drafted 2026-07-20 late night at owner request —
      "include WFRC as though it were the starting place").** **PHASE 1 BUILT 2026-07-22**
      (owner go): the zero-acquisition derivation + registry + doc-corrections package —
      `wfrc_mpo/projects/derived/` project_vintage (3,453) + project_history (1,884; slip/
      cost-drift/entry/exit per PIN; all gates PASS, idempotent) via
      `build_project_history.py` + `vintage_overrides.csv` (2 adjudicated (pin,vintage)
      conflicts: 19561 merge_dup typo-dup, 21213 keep_both master-PIN sub-scopes →
      `variant` column + lifecycle-numerics guard); federated into gov.db (FK 0, integrity
      ok, +4 caveat rows; validate_entity wfrc_mpo 8P/0W/0F); `udot`/`uta` REGISTERED-ONLY
      (fed 302/303, member_of wfrc_mpo + within ut_state; build_hierarchy.py fixed to
      render state-agency leaves, not duplicate roots); §4.8 doc corrections applied +
      URL-verified (RTP amendments page EXISTS — 4 resolutions, capture queued Phase 2;
      obligation set 2023+2024 complete-as-published; CFA rename; PIN→STIP path in
      projects/SOURCES.md). NEXT: Phase 2 (plans capture + TIP-table funding parse) —
      see WFRC_NATIVE_SPEC.md §5. **RESEARCH PHASE DONE
      2026-07-22** — three-agent web sweep (institutional
      role / publication series / data-GIS-model surface) synthesized into
      **`WFRC_NATIVE_SPEC.md`** (repo root): own-terms assessment (5 native roles —
      allocator/certifier/forecaster/scorekeeper/advocate), tiered ingest/capture/
      catalog/defer verdicts, 5 new gov.db table designs (`project_vintage`+
      `project_history`, `project_funding`, `project_obligation`, `regional_grant`,
      `sap_certification`, `legislative_position`), phased build plan (P1 zero-
      acquisition derivation → P5 MAG parity). Key research deltas vs the 07-20 draft:
      RTP amendments page EXISTS (un-ledger the "no amendments log" gap); TIP table
      PDFs carry the funding-program+$ layer the ArcGIS attrs lack; NO public
      PIN-keyed obligation $ exists (obligation layer = 2023+2024 PDFs, honest
      ceiling); WFRC bill-tracker positions join to ut_state bills (new Workstream);
      15 SAP cert motions already extracted = cert-ledger spine. Implementation
      awaits owner go per phase. *(original draft below)* The
      corrective insight: the current wfrc_mpo build is what city-council methodology
      sees in an MPO; a WFRC-native model makes its ecosystem role first-class. Three
      workstreams, value-ordered: **(A) Project-lifecycle spine** — derive
      `project_history` keyed on `pin` (= UDOT ePM pin, a statewide join key) across the
      8 in-repo TIP vintages + RTP phases (+ ALOP obligations where parseable): entry /
      slippage / cost-drift / exit per project; funding-source breakdown (federal
      program / state / county sales tax / local match) where attributes carry it. ZERO
      new acquisition — pure derivation. **(B) Influence machinery** — SAP certification
      ledger (city × station area × cert date × WFRC motion × city plan doc; completes
      the HB462→WFRC→city-SAP→rezone chain); TLC grants table (city/year/$/funded study
      + downstream trace into city minutes/ordinances); Wasatch Choice centers × city
      rezone outcomes (derived spatial join, confidence-gated on motion geocoding —
      ledgered limits, never guessed); register `udot`/`uta` as registered-only entities
      for honest references + document the pin→STIP statewide expansion path. **(C)
      Deliberative record completed** — Council + RGC/Trans Com committee packets/full
      agendas (the "why" layer; committees are where recommendations form); ~~the
      published-reports corpus~~ **✅ DONE 2026-07-20 late night (ahead of the package):
      44 docs federated + FTS-live (wfrc 28 / mag 16 — adopted RTP narratives, TIP +
      Federal Obligation Reports, AQ conformity, CEDS, Wasatch Choice vision, TLC award
      rollups naming 16 repo cities [= Workstream B's grants-table raw material], HB462
      SAP progress reports; honest gaps ledgered in each plans/SOURCES.md: no per-study
      TLC PDFs (ArcGIS-map index), MAG RTP narrative UDOT-hosted, Wasatch Back legacy
      library dead, 4 Utah-Co SAP scopes Google-Drive-unverifiable)**; pre-2016 GRAMA
      depth ledgered low-value. Schema work (Fable/solo): `project_history` + possibly `regional_grant`
      federated tables. MAG inherits the template at smaller scale → this becomes the
      repo's REGIONAL-ENTITY METHOD (the salt_lake_county-analog for MPOs; future Dixie/
      Cache MPOs inherit). Effort: A cheap-moderate, B moderate, C familiar-pattern.
- [ ] **PHASES 4–6 PACKAGE — the three honest residuals (owner review 2026-07-20 late
      night; surfaced explicitly so the package close-out can't be misread as total):**
      (1) **The County content menu is STILL OPEN** — the Phase-4 fold-in completed only
      the salt_lake_county/CLAUDE.md refresh; the menu's enrichment modules (RDA
      project-area plans + tax-increment financials, interlocal & development agreements,
      Legistar matter catalog, county campaign finance, GP/small-area additions) were
      built for NO county (none crossed the scouts' cheap-bar during the wave). The
      menu block below (2026-07-11 brainstorm) remains the itemized list.
      (2) **✅ DONE 2026-07-25 — post-build audits for the 9 new entities.** Four-agent
      adversarial ground-truth pass over utah/weber/cache/summit/washington/juab counties +
      wfrc/mag/ut_state (+ wfrc's 2026-07-22 Phase-1 derived layer). Report:
      `_audits/2026-07-25/report.md`. Read-only; repo file count returned to baseline
      exactly. **Verdict: all 9 pass `validate_entity.py` at 0 FAIL / 0 WARN and 4 carry
      material extraction loss the gates cannot see** — in 3 cases recoverable data is
      documented as an honest source ceiling. Passed clean: ut_state's vote gates (shell
      trap uncontaminated, person populations provably disjoint, LUDMA numbering current),
      wfrc's Phase-1 derived layer (re-derived from source, 0 cell diffs / 22 columns),
      vintage separation, and the elections layer across the tier (utah_county's SOVC
      quarantine held at 0/198,459 rows). Fixes queued as their own item below.
      *(original)* ...are ALL audit-eligible per the repo's after-any-large-ingest
      convention (the builds carry their own gates + 0-mismatch reconciliations, but no
      independent adversarial ground-truth pass has run). **Ranked the most valuable next
      non-owner-gated work.**
      (3) **/build-county-data-repo skill lesson absorption** — the Phase-4 sharp edges
      (standard `referral` table REQUIRED in every entity db; non-city ordinances
      index.csv motion_id convention; link-only rows legitimate; md_path canonical in
      minutes_index; the PMN JSON-POST channel) live in HANDOFF gotchas but are NOT yet
      folded into the skill text — small doc task, do before the next county build.

**County content menu — datasets that raise LLM-analysis value (2026-07-11 brainstorm).
STATUS 2026-07-20: STILL OPEN — the Phase-4 package built none of these enrichments for
any county (only the county-standard packets/dev-pipeline landed where tiered in); this
block is the surviving Phase-3/4 residual (see the package-residuals item above).**
Prioritized into Phase 3a NOW (owner decision 2026-07-11): (1) **agenda packets / staff
reports** as searchable text (the "why" behind land-use decisions — Legistar attachments,
like Sandy's `packets/`); (2) a **structured development-applications table** (⭐ the
"development pipeline" — one row per rezone/subdivision/CUP: location, acreage,
from-zone→to-zone, units, applicant, PC rec → Council action → outcome; extends the
`application`/`motion`/`referral` spine); (3) **adopted land-use ordinances** (full text +
enacting-vote linkage). QUEUED follow-on county modules (add to the county standard as built):
- [ ] **RDA/CRA project-area plans + tax-increment financials** — text plans + structured $
      by project area × year (SLCo RDA = Legistar body 257; core growth mechanism).
- [ ] **Interlocal & development agreements** — county↔city coordination docs (service,
      revenue, annexation, negotiated project terms); text + light structure. Distinctively
      showcases the cross-tier entity model — rarely assembled anywhere.
- [ ] **Legislative matter catalog** — every ordinance/resolution/contract w/ status/subject
      (Legistar matters, like Sandy's `legistar_matter`) — a structured legislative index.
- [ ] **County campaign finance** — Council candidate contributions/expenditures → donors →
      votes (money-vs-land-use-votes); disclosures.utah.gov / county clerk.
- [ ] **Population/housing projections** — Gardner/GOPB by year × sub-county geography
      (structured; also a state-tier canonical source).
- [ ] **General Plan + metro-township general plans + small-area plans** (text corpus) +
      **Moderate-Income Housing** element/report.
- [ ] **CIP / impact-fee facilities plans** — the infrastructure-capacity pipeline
      (text + structured projects: location, cost, year, category).
- [ ] **Building permits / housing starts** — units permitted by year/area (hardest growth
      signal; needs a county data portal — feasibility TBD).
- [ ] **Cross-tier analytical views** — county PC/Council land-use actions ↔ member-city
      council actions on the same geography; RDA project areas overlapping cities.
- [ ] **County Council roster** — who-served-when (the roster layer, generalized to counties).
Applies to ALL counties, not just Salt Lake — fold each into the `build-county-data-repo`
skill (Phase 3c) as it's proven on SLCo.

**Watch:** on 2026-07-11 a 2026-07-10 city-data refresh (ogden/orem/provo/south_jordan/
vineyard/west_jordan) was found propagated into `cities.db` (rebuilt 07-11 13:24) but NOT
into `coverage.json` (frozen 07-07) — `build_coverage.py` was re-run 07-11 to true it up.
Lesson: after per-city refreshes, run the repo-level `build_coverage.py` too (rebuild_derived).

## [GATED] Deferred by owner decision

- [x] **Raw-PDF backfill (plan item 3.2) — RULED OUT OF SCOPE by owner 2026-07-19** for
      any file whose processed text version is already saved in the repo — which covers
      the entire item (the 11 cities discarded raws only *after* text extraction). No
      re-fetch will be done; the citation index (`sources.csv` per city, 96.8% direct
      URLs, all hosts live as of 2026-07-02) remains the recovery path, and the Wayback
      archiving pass (below, still owner-gated) is the rot-protection alternative.
      *(original, DEFERRED 2026-07-02 — disk space: re-fetch source PDFs into
      `<dataset>/raw/` for the 11 cities that discarded them. Note: www.ogdencity.gov
      404s non-browser user agents — use a browser UA.)*
- [ ] **Wayback Machine archiving pass.** Proposed alternative/complement to 3.2 with
      near-zero disk cost: politely submit every `sources.csv` URL (~6,700) to
      web.archive.org over several days; record the snapshot URL in a new column.
      Protects against portal rot and strengthens public citations. Owner interested,
      not yet approved — ask before running.

## [WATCH] Known acquisition gaps (watch for sources appearing)

- [ ] **Lehi council minutes publishing lapse** — Granicus lists 19 meetings after
      2026-01-27 with NO minutes posted (probed 2026-07-02; see refresh_status.md).
      City-side, not a scraper gap. If it persists another quarter, consider asking the
      recorder's office; PMN may also carry them.
- [x] **12 new documents available as of 2026-07-02 — ✅ CLOSED 2026-07-19 as SUBSUMED
      by the Q3-2026 quarterly refresh** (2026-07-19: 31/31 portals probed ok, ~62 docs
      ingested across 14 cities, all 75 crosscheck flags worked to zero — any doc a
      07-02 probe listed was re-surfaced and ingested/ledgered by the 07-19 run;
      spot-verified all six listed cities' minutes trees current through 2026, provo PC
      through 2026-07-06). *(original)* park_city 2, orem 2, sandy 3+1,
      west_valley 2, west_jordan 1, provo PC 1 (per refresh_probe.json). First real
      `fetch_new.py --fetch` run can ingest these; a good shakedown for the fetch path.
- [ ] **St George 2025-10-09 work-meeting minutes** — city published the wrong PDF on
      BOTH Revize and PMN (md5 = the 10-16 minutes). Meeting was real (agenda, packet,
      2 recordings exist). Options: watch for a corrected upload; transcribe the
      recordings; or email the city recorder. Logged in st_george
      meeting_minutes/minutes_unrecovered.csv.
- [ ] **Orem PC 2025-10-15 minutes** — same class: CivicClerk serves the 11-05 file
      under both events; real minutes not found anywhere. Logged in orem
      planning_commission/minutes_unrecovered.csv. Watch for republication.
- [x] **SLC 2020 Laserfiche minutes: no per-document URLs — ✅ CLOSED 2026-07-20 at the
      recoverable ceiling** (65/68 recorded; the 3 residual formal-session dates —
      2020-01-07/01-17/01-21 — are VERIFIED permanent no-PMN gaps, ledgered; PMN posted
      only those dates' work-session minutes, so this is the terminal honest state, not
      a pending task). *(original)* (session-based portal; the
      only minutes in the repo without direct citations). Possible fix: locate 2020
      council minutes on Utah PMN and record those URLs in the index.
      **DONE to the recoverable extent 2026-07-19 (pv-tierb-low):** the 65 recoverable
      PMN citations (from `slc_city_council/pmn_backfill/url_recovery_2020.csv`) were
      re-verified in-body (retained `pmn_backfill/raw/2020/<id>.pdf` → pdftotext: meeting
      date matches 65/65, "MINUTES OF THE SALT LAKE CITY COUNCIL …" title line present,
      session agrees, word-overlap ≥0.84 for 64/65; 2020-07-07 Formal is 0.51 because the
      repo slug holds a narrow "Delegating Bond Resolution Minutes" excerpt while PMN
      645597 is the comprehensive formal minutes of the SAME July-7-2020 formal session —
      ledgered in pmn_backfill/CLAUDE.md; + 3/3 live-URL liveness checks byte-identical to
      the retained raws) and PROMOTED into `meeting_minutes/minutes_index.csv` `source_url`
      (source stays `laserfiche`; OCR text unchanged — citation-provenance only).
      `sources.csv`/`SOURCES.md` regenerated (`build_sources_index.py slc`). validate_city
      24 PASS / 2 WARN (pre-existing) / 0 FAIL. **Box left open for the 3 permanent no-PMN
      gaps** — 2020-01-07 / 2020-01-17 / 2020-01-21 **Formal** meetings, for which PMN
      posted only the Work Session minutes (verified absent, not a search miss); these stay
      honestly URL-less. No further action possible unless SLC/PMN later posts them.
      Backups: `_backups/2026-07-19-pv-tierb-low/slc-laserfiche/`.
- [x] **Election URL provenance — ✅ DONE 2026-07-19 (fresh 31-city pass).** Every
      in-scope city's `unrecorded (<office>)` election rows resolved: **111 real URLs
      recorded** (each fetched + VERIFIED to serve the matching document — byte-identical
      md5 where the raw file is retained, else content-verified) and **66 upgraded to
      dated `verified-no-stable-archive (<office>, checked 2026-07-19)`** where no durable
      public archive exists. 0 in-scope election rows remain bare `unrecorded`; all 22
      touched cities validate 0 FAIL. Mechanism: verified URLs in each city's
      `election_results/CLAUDE.md` (doc_urls) + `scripts/build_sources_index.py`
      ELECTION_CFG `overrides`/fallbacks (new shared `SLCO_SOVC` map; the harvester now
      (a) emits a canonical-pointer row for the re-pointed **alta** so its retired-raw
      provenance is recorded not dropped, and (b) emits `verified-no-stable-archive` labels
      verbatim). Backups: `_backups/2026-07-19-pv-tierb-low/election-urls/`. Per office:
      - **Salt Lake County Clerk** (alta pointer + bluffdale/copperton/cottonwood_heights/
        draper/herriman/holladay/magna/midvale/millcreek/riverton/south_salt_lake/
        white_city): per-year SOVC `.xlsx`/`.zip` at `saltlakecounty.gov/globalassets/...`
        all **md5-byte-identical** to the retained raw copies (2011/2016/2019/2021/2025
        general + primaries); multi-year city long-slices point at the Clerk results page
        (canonical source). **~40 URLs.**
      - **Utah County Clerk** (provo 14, orem 9, lehi 5+3 index): `vote.utahcounty.gov/
        cms/uploads/…` md5-verified byte-identical. **31 URLs.**
      - **rcvis.com** (lehi 6, vineyard 7): `/v/<slug>` permalinks content-verified (winner
        final-round total identical to stored HTML; ambiguous Lehi/Vineyard update
        snapshots pinned by total). **13 URLs.**
      - **Washington County** (st_george): 10 `outpost.washco.utah.gov` files md5-verified;
        3 (2021 primary precinct-summary, 2023 primary export+precinct) → no-archive.
      - **Cache County** (logan): 5 stable `.html` result endpoints content-verified
        (Logan council present); logan-city-administered 2019/2021 PDFs → no-archive.
      - **Weber County** (ogden): 4 `weberelections.gov/_files/ugd/…` Wix assets
        md5-verified; remaining Weber PDFs (opaque Wix hashes) + 2020 + state_api → no-archive.
      - **Juab County** (nephi): 3 index/news overrides kept; the official 2023 Juab canvass
        PDFs (`juabcounty.gov/wp-content/…`) content-verified + recorded in CLAUDE.md; the
        state-portal `ev-*.json` → no-archive.
      - **Utah state Enhanced Voting portal** (`electionresults.utah.gov`, ev_*.json /
        state_api across lehi/vineyard/nephi/ogden/logan) → **verified-no-stable-archive**
        (dynamic SPA / undocumented unofficial live API; confirmed live 2026-07-19).
      - **Park City Recorder / Summit County** (park_city): 7 canvass/precinct PDFs →
        no-archive (Revize CMS reuses generic per-cycle filenames, overwritten each
        election; the `election_results.php` authoritative page recorded).
      - **NOT DONE (deferred, minor):** the six re-pointed SLCo cities (sandy, south_jordan,
        taylorsville, west_jordan, west_valley — slc already clean) still carry 33
        `unrecorded (…mirror)` rows on their **retained** raw SOVC copies; skipped per the
        pass scope (their provenance is the county canonical). Most share the new
        `SLCO_SOVC` filenames and could be recorded trivially by adding overrides
        (south_jordan needs 2007–2017 historical SOVC URLs; sandy needs its RCV
        summary/recount PDFs). Also murray/kearns/emigration_canyon read the canonical with
        no election `sources.csv` row at all (raw retired, not slc/alta-style pointered) —
        a separate small provenance-completeness gap.
        - **✅ DONE 2026-07-20 (P4 URL residue).** All 33 residual rows resolved + the
          three pointer-less cities closed; **0 `unrecorded` election rows remain across the
          9 touched cities; all 9 validate 0 FAIL.** Disk reality had moved on since the note:
          sandy/west_jordan/west_valley raws were further retired, so the true end-state is a
          mix of retained-raw per-file rows AND slc/alta-style canonical-pointer rows.
          Generalized `harvest_elections`: the hardcoded `city in ("slc","alta")` pointer
          branch became a per-city `ELECTION_CFG["canonical_pointer"]` flag (True = default
          county-long-file pointer; a dict overrides fields) that now also rides ALONGSIDE
          per-file rows when a city keeps raw. Records, all VERIFIED:
          - **sandy** — canonical pointer + its 2 RCV-pilot PDFs, whose URLs
            (`…/election-results/2021/2021-general-election-ranked-choice-summary-report.pdf`
            + `…-sandy-recount-results.pdf`) are **sha256-byte-identical** to the retained
            copies (live 200, county Clerk page links both).
          - **south_jordan** — canonical pointer + all 16 retained SOVC rows recorded via an
            extended shared `SLCO_SOVC` map; the 2007/2009×2/2013×2/2015-primary/2019-primary
            files sha256-match the county-mirror `download_log`, the 2015-general + 2017
            primary/general are served as `.zip` whose **inner xlsx is sha256-identical** to
            the retained copy, and 2023 general → the county's
            `statementofvotescastrpt-official-report-12-05-2023-5.22pm.xlsx`. All 10 new URLs
            live (HTTP 200/206) 2026-07-20.
          - **taylorsville** — canonical pointer + 2 retained SOVC (2019/2021, both in
            `SLCO_SOVC`).
          - **west_jordan / west_valley** — raw fully retired → canonical-pointer row only.
          - **murray / emigration_canyon** — canonical-pointer row added (were pointer-less).
          - **kearns** — Kearns-specific pointer (it parses the raw SLCo SOVC workbooks BY
            CONTENT because the county long file is corrupted for it; local_path →
            `salt_lake_county/elections/raw/SOURCES.md`, note preserved).
          Mechanism edits in `scripts/build_sources_index.py` (SLCO_SOVC extension +
          `canonical_pointer` config/emit); regenerated per-slug for the 9 cities.
          Backups: `_backups/2026-07-19-pv-tierb-low/p4-url-residue/`.

## [DEBT] Extraction / data quality follow-ups

- [x] **Alta council roll-call undercapture — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** Root cause = stray OCR glyphs between dash and wrapped vote token; 9 Ayes recovered on 9 unanimous motions (2 files beyond the audit list), 0 outcome changes; 3 garbled persons already dead via T3.1(a) guards (verified). (2026-07-12).** *(original)* When a member's When a member's
      `— yes` wraps to the next line, or a `;`-anchored / narrative `voted 'Aye'` form is used,
      the extractor drops that member (e.g. 2021-05-12; 2025-01-08 Byrne dropped, stored 4-0 vs
      true 5-0; 2025-12-09 stored 3-0 truly 5-0). It **never flips an outcome** (all such motions
      are unanimous) and **never fabricates** — an honest under-count that understates the derived
      N-0 tally. Fix: make the roll-row parser tolerant of line-wrapped / `;`-anchored / narrative
      vote tokens; re-extract, rebuild derived. Also **3 cosmetic garbled `db/person` rows**
      (`Contract. He` / `Council. Davis` / `Was`) from mover-text garble (0 votes each). Logged in
      `alta_city_council/_audits/audit_2026-07-12.md` + `VERIFICATION.md §8`.
- [ ] **Alta 2025 municipal election missing from the canonical SLCo file (2026-07-12)** though it
      occurred (**Heimark won a seat** per the 2026 council minutes). The Nov-2025 SLCo general SOVC
      carries no Alta contest yet (county-file acquisition lag, not a Town gap). Re-pull the raw
      2025 SOVC when available and add to `alta_city_council/election_results/alta_races.csv`
      (rebuild via `clean_elections.py`).
- [ ] **[roster] Historical council-district boundary acquisition (redistricting geometry gaps) — 5 of 9 DONE 2026-07-11.**
      The rolling-roster layer is BUILT + federated + independently audited for **all 16 cities** (370 term
      rows in `cities.db` `term`/`district_version`/`district_precinct` + `v_council_current`/
      `v_term_provenance`; per-city audits in `scripts/roster_HARDENING.md`). A read-only recoverability
      scout (`scripts/roster_boundary_recon.md`) found the prior maps largely repo-reconstructable, and
      **5 cities were reconstructed 2026-07-11** (owner-approved scope) — **west_jordan, taylorsville,
      south_jordan, sandy, millcreek** — by dissolving current-vintage precinct shapes by the pre-2022
      precinct→district assignment (`scripts/build_prior_district_map.py`): each now carries
      `geo/council_districts_pre2022.geojson` + a populated `district_precincts` prior composition at
      **`confidence=medium`** (approximate — old assignment over current shapes). district_precinct
      733→988; millcreek/sandy's factually-wrong "unrecoverable" notes corrected. **REMAINING (4, still
      documented GAPs):** **west_valley + slc** (repo-partial, ~13–14% renumbered-precinct holes — reconstruct
      approximate now or fetch the SL County 2020 VistaBallotAreas to firm up); **provo** (Utah County 2020
      precinct layer; D1/3/4 likely permanently unrecoverable — no pre-2022 SOVC) and **ogden** (Weber County
      historical precincts + a pre-2022 SOVC — none on disk) genuinely need an EXTERNAL FETCH. The roster
      hardening pass (vote-bound clamp + precinct-crosscheck robustness; 9 of 11 precinct sidecars retired)
      is COMPLETE — see `scripts/roster_HARDENING.md`.
- [x] **`v_contested_all` redefinition — DONE 2026-07-10; two follow-ups ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** (1) tally_other ruled BY DESIGN with 11-motion/9-city ground truth (encoding is NULL not 0; COALESCE already correct; semantics documented in normalize_motions + cities_db_SCHEMA). (2) per-city v_contested now mirrors the federated split tally/named column shape across all 31 dbs (+6 forks ported byte-check-first; counts proven identical).** Redefined
      contested as the UNION of *named* dissent (Nay/Abstain/Recuse row) OR *tally* dissent
      (`motion_std.tally_nay/tally_other`) and split the count columns into authoritative
      `tally_aye/tally_nay/tally_other` (+`vote_mode`) vs attribution-only
      `named_ayes/named_nays/…` (the old bare `ayes`/`nays` were vote-ROW counts that read as
      margins but undercount in dissent-only/tally-only cities). Strict superset (2362→2366,
      no city dropped). Follow-ups: (1) **`motion_std.tally_other` does not capture
      abstentions/recusals** — 331 motions have an Abstain/Recuse *row* but `tally_other=0`
      (source printed a bare "A:N" tally, abstention noted only in prose→row). Verify whether
      by-design (row is the authority for abstentions) or a tally_other completeness gap.
      (2) **Per-city `v_contested` (db_build_lib.py) still exposes only `result_raw`** — no
      split tally/named columns. Consider mirroring the cities.db shape for symmetry so a
      future reader gets the same self-explanatory margins per city.
- [x] **Full-name voter-resolution audit across ALL cities — COMPLETE 2026-07-19 (LM wave): remainder (a) taylorsville + west_valley gates, (b) st_george PC Anderson → attendance-based, (c) vineyard resolve_blackburn → attendance + honest abstention ALL done, every one byte-identical-proven (vineyard's second Blackburn is real — Spencer — but never co-occurs; st_george council Anderson = ex-PC chair, body move). DONE 2026-07-10; 4 extractors hardened.**
      Audited all 16 cities' `extract_votes.py` name resolution. **Finding: ZERO live wrong-merges** — every
      real shared-surname collision in the data today is already specially handled (attendance/first-name/year/
      role). All surname-only resolvers are LATENT risk (fragile mechanism, no colliding second person yet).
      **Hardened with the safe first-name gate (verified byte-identical output — pure no-op today):**
      west_jordan MM+PC, orem MM+PC. Gate recipe + the two gotchas (nicknames, shared first names like Orem's
      two Davids) in memory `prefer-full-name-vote-resolution`. **STILL TODO (latent, low priority):**
      (a) **taylorsville** MM+PC (`SURNAME_MAP` + difflib fuzzy) and **west_valley** MM+PC (`LASTNAME_TO_FULL`
      + prefix fuzzy) — apply the same gate. (b) **st_george PC** `normalize_pc_name` — bare "Anderson" in
      2024-2026 is resolved by a *year guess* but Austin (Chair) & Brandon both serve then; switch to
      attendance-based disambiguation (as lehi/nephi PC do) or abstain. (c) **vineyard PC** `resolve_blackburn`
      — bare "Blackburn" silently defaults to Tim; make it abstain when ambiguous. SAFE-by-design (leave):
      slc (LLM full names), nephi PC, lehi PC, logan MM, sandy PC (Legistar), provo PC (already fixed).
- Survey note: the OTHER recovered-but-unintegrated vote gaps found (Vineyard RDA, Orem RDA/MBA/BoA,
      South Jordan 2020 council, Ogden RDA/MBA) are ALREADY tracked in their own TODO items below.
- [x] **St George: two pre-existing extraction gaps — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** (a) gutter files: PC 2024-12-10 0→7 motions incl. the real 3:2 failed hillside rec, PC 2024-04-09 +5, council RDA +1; (b) the five 'joint' PC docs are council-side twins (correctly not double-captured); genuine recovery = council 2022-01-03 +2.** (found during the 3.5 fix, logged
      in its VERIFICATION.md): (a) 2024 meetings with line-number-gutter formatting
      extract 0 motions — including at least one real 3–2 failed vote; (b) joint
      PC/Council meetings' "Councilmember"-prefixed rolls uncaptured. Both need
      extractor work + regeneration.
- [x] **Ogden build_referrals surname-token weakness** — ✅ **DONE 2026-07-19 (PV Tier-B
      LOW wave).** Added an OGDEN-LOCAL two-layer guard in `ogden_city_council/db/build_referrals.py`
      (still a thin stub over `scripts/referrals_lib.py` — monkeypatches `IDF.score`/`contain`/
      `distinctive_shared` before calling `main`; no shared-lib edit, no global-tokenization
      change): (1) a CONTENT VETO — a subject link must share >=1 genuine content token, i.e.
      NOT motion/plan/CRA boilerplate (ADOPTED/ENTITLED/MEMBER/SECONDED/WAS/OGDEN/MASTER/AREA/
      COMMUNITY/REINVESTMENT...) and NOT a council/PC/RDA/MBA member name; (2) name-anchored
      containment must share >=2 distinctive NON-NAME tokens (kills lone shared-street co-location).
      WASHINGTON/WHITE deliberately kept OUT of the name set (place-name collisions) — Layer 2
      handles them. Diff: **referral table 13 → 6 links** (2 override-high + 4 real subject);
      the **7 dropped are ALL verified false positives** — the 2 live manifestations of the
      documented surname class (141←157 Ord 2024-12 code-amend vs RDA Ogden Bend; 243←239/241
      Ord 2026-7 clean-energy vs RDA ADJOURN, lone `lundell`) plus 110←89 (Continental vs Airport
      CRA), 136←111 (1450 vs 1781 Gibson — different parcels), 162←157 (Sewer vs Ogden Bend plans),
      162←200. All 5 hand-suppress rows now PROVABLY REDUNDANT (rebuild with them removed yields
      the identical 6 links) — kept as documentation; build handles them gracefully. Both override
      links (Franklin 60←435, Ogden Bend 594←157) still resolve correctly. validate_city.py = 23
      PASS/3 WARN(pre-existing)/0 FAIL. **FOLLOW-UPS: (a)** ✅ **PORTED into the shared lib
      2026-07-20 (PV Tier-B LOW, p4-referrals).** The guard now lives in `scripts/referrals_lib.py`
      as four opt-in params on `main()`/`IDF` — `member_names`, `template_stopwords`,
      `content_veto` (Layer 1), `name_anchor_min` (Layer 2, ogden passes 2) — ALL defaulting to a
      FAITHFUL NO-OP. `ogden_city_council/db/build_referrals.py` dropped its monkeypatches and now
      just calls `main(HERE, member_names=..., template_stopwords=..., content_veto=True,
      name_anchor_min=2)`. **Proof:** rebuilt all 31 entities' referral tables; ogden reproduces
      its exact 6-link state (2 override-high + 4 subject-medium, Franklin + Ogden Bend overrides
      bind, 5 suppress rows still handled gracefully, validate_city 23 PASS/3 WARN/0 FAIL), and
      **all 30 other cities are BYTE-IDENTICAL** to their pre-port referral tables (deterministic
      orig-rebuild baseline had zero pre-existing drift; post-port diff = 0 cities). No override
      reconciliation broke — no city hit the stale-app_key `sys.exit`. Backups in
      `_backups/2026-07-19-pv-tierb-low/p4-referrals/`. **STILL OPEN — enable the guard for cities
      beyond ogden:** the params are wired but ONLY ogden turns them on; enabling elsewhere needs
      PER-CITY evidence review (build the city's member-name + boilerplate sets, confirm the
      surname/template FP class actually manifests there, re-verify the referral delta is all true
      positives) — ogden's proven yield (13→6 links, 7 verified FPs dropped) is the motivation to
      pursue it. NOTE when any city (incl. re-enabling more of ogden's federated rows) changes:
      `cities.db` must be rebuilt via `scripts/build_cities_db.py` after — NOT done in this pass, so
      the federated Ogden referral rows remain stale until a federation rebuild window opens.
      **(b)** a WIDER, separate FP class remains
      unaddressed: two DIFFERENT named CRAs sharing the generic "Community Reinvestment Project Area"
      template, distinguished only by their project noun — needs project-noun-aware matching, not
      chased here.
- [x] **Nephi PC footer bleed** — page-footer text bleeds into extracted motion text
      (capture-window issue in nephi planning_commission/extract_votes.py). Cosmetic in
      CSV motion strings; logged 2026-07-02. **DONE 2026-07-19:** added `FOOTER_RE` +
      `strip_footers()` to `planning_commission/extract_votes.py` (removes the two-line
      running footer — lone page-number line + "Nephi City Planning Commission  <date>";
      all 176 footer lines verified preceded by a lone page-number line, so only footer
      text is removed, prose rejoined across the page break). Re-extracted --force: motion
      COUNT/votes/outcomes/tallies/mover/seconder/result ALL unchanged (373 rows, key
      tuples identical); exactly **2** motions cleaned (2024-01-10 #4 McDonald's site
      plan, #5 Cornerstone car wash) — the only two whose action prose actually straddled
      a page break. 0 residual footer signatures. Derived chain rebuilt (db/referrals/
      weeks/motions_std nephi); validate_city nephi = 26 PASS / 0 WARN / 0 FAIL. Backup:
      `_backups/2026-07-19-pv-tierb-low/nephi-footer/`.
- [x] **Vineyard minutes_speaker_log.csv** — ✅ **DONE 2026-07-19.** Re-ran the deterministic
      `extract_speaker_log.py` over the full current 172-file minutes corpus: **210 → 283
      rows**, 0 pre-existing rows changed (backup `_backups/2026-07-19-pv-tierb-low/
      vineyard-speaker/`). +76 across 18 dates (log was stale vs the whole corpus, not just
      Phase 1.3). Of the four Phase-1.3 recoveries: 2023-08-30 +4 (spot-verified verbatim);
      2020-06-24 genuine "hearing none" (0); PC 2023-06-21 out of scope (council-only
      extractor). 3 rows removed = the byte-identical 2024-04-10 dedup file's duplicates (no
      speaker lost). Validator 25 PASS / 1 WARN / 0 FAIL. RDA: audited-tree RDA-board minutes
      yield 0 speakers; the 20 new pmn_backfill RDA `.txt` are a separate non-audited corpus
      the extractor doesn't read — left alone. Full write-up in vineyard VERIFICATION.md
      (2026-07-19 addendum). **Residual follow-up below.**
- [x] **Vineyard speaker-log recall gap (compound-prefix + verb) — ✅ DONE 2026-07-20**
      (2026-07-19-pv-tierb-low package). NARROW fix in `public_comments/extract_speaker_log.py`:
      the Resident-anchored pattern now allows a compound title between "Resident" and the name —
      `^\s*Resident\s+(?:and\s+(?:[A-Z][a-zA-Z]+\s+){1,4})?NAME`. The optional middle **requires** a
      lowercase "and" + 1–4 Capitalized role words, so it fires only on a genuine "Resident and
      <role> <Name>" intro and cannot alter any bare-`Resident NAME` row. Because pattern 1 is
      Resident-anchored (no trailing-verb requirement), this captures the "explained" case WITHOUT
      touching the broad name-first verb allow-list — so the false-positive risk the original note
      flagged (Councilmember/Mayor/staff) is avoided by construction. Corpus-wide re-run (172 files)
      added **exactly 2 rows (283→285)**, both **manually verified genuine public-comment speakers at
      source**: 2020-09-23 Amber Rasmussen (item "2. PUBLIC COMMENTS") and 2023-01-11 Tyler Haroldsen
      ("4. PUBLIC COMMENTS", "living on Mill Road"). ZERO new false positives; `comm -23` confirms 0
      of the 283 baseline rows changed (purely additive). `topic_from` prefix-strip mirrored to
      "Resident [and]" only (role + full name retained in the paraphrase, matching the existing
      "Resident Dean Stonehocker → Dean Stonehocker …" convention). Not a vote artifact → no db/weeks
      rebuild; validate_city 25 PASS / 1 WARN / 0 FAIL. Docs: public_comments/CLAUDE.md updated;
      backups `_backups/2026-07-19-pv-tierb-low/p4-vineyard/public_comments/`.
- [ ] **[WATCH — permanent gap, not debt] SLC ~8 unrecoverable comment pages** (5 API content-filter blocks on 2020
      protest-era pages, 3 JSON edge cases) — documented in public_comments/CLAUDE.md.
      Retry occasionally with newer models; don't burn time on it.
- [ ] **[OPTION] Comments coverage — spoken-comment transcript layer for no-published-comment cities.**
      SCOPE UPDATED 2026-07-19: the "6 cities" count is stale (written 2026-07-02, 16-city
      era). Today **24 of 31 cities have zero rows in `public_comments/all_comments_clean.csv`**
      — only slc, lehi, park_city, west_jordan, st_george, provo, orem publish written comments.
      Every zero-row city is submit-only / honest-empty (residents comment in person or by
      unpublished email; the clerk paraphrases them in the minutes as a `minutes_speaker_log`,
      which is NOT a written-comment corpus). The spoken public-comment period still exists in
      each city's recordings, so a transcript pipeline (expand-city-sources source type 5) could
      build a speaker/comment layer. **Original 6** (the 16-city-era list): logan, nephi, ogden,
      sandy, vineyard, west_valley (logan/ogden/sandy/west_valley = captioned YouTube ASR;
      vineyard = COVID-era uploads only; nephi = video only from May 2026, 4 meetings).
      **+17 new-wave candidates**, grouped by transcript feasibility (per each city's
      `transcripts/AVAILABILITY.md`):
      • videos mapped WITH captions (YouTube ASR, directly fetchable): alta, cottonwood_heights,
        herriman, midvale, murray, south_salt_lake; partial-window only: holladay (YouTube
        2020–21; SuiteOne era is caption-less), kearns (city-era 2026+ YouTube only; deep PMN
        audio otherwise).
      • video exists but NO caption track → Whisper on video/Granicus audio: bluffdale
        (CivicClerk), draper (Granicus 0-caption; a 25-meeting 2026 third-party YouTube mirror
        carries ASR), riverton (Granicus 0-caption; exactly 1 captioned meeting).
      • audio-only, no meeting video anywhere → Whisper on PMN/Streamline MP3s (owner-gated,
        NOT run; wave-2 leads): copperton, emigration_canyon, magna, white_city, south_jordan,
        taylorsville.
      Exclusion: **millcreek** is NOT a transcript candidate — it publishes genuine written
      comments IN-PACKETS (PC agenda-packet appendices), already tracked by its own Provo-style
      harvest item below. Big job; owner decision.
- [x] **Millcreek F-1: re-extract 2017 council votes — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** parse_endash_votes recovered 362 named Ayes / 77 motions; non-2017 ordered-identical; doc framing corrected (2018–2021 is the genuine tally-only seam). (2026-07-06).** 70 unanimous 2017
      motions DO name voters in a tabular en-dash format (`Councilmember X – Aye`) the
      extractor doesn't parse → ~380 all-Aye rows recorded as tally-only (safe-direction
      undercapture, fully recoverable). Add the en-dash tabular grammar to the millcreek
      council extractor, regenerate, then **update the "2017 tally-only" doc framing**
      (CLAUDE.md + coverage caveat) from "city didn't name voters" to "recovered".
- [x] **Millcreek public comments: Provo-style IN-PACKETS harvest — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** layer BUILT (99 packets walked, 9 verbatim resident letters, 13 wrappers dropped); HONEST FLOOR — the unretained ?packet=true land-use packets with comment appendices are queued as follow-up (d) of the wave entry. (2026-07-06).** Resident
      letters are published inside PC agenda packets; a structured harvest (mirror Provo's
      page-walk classifier) is not yet built. Until then `all_comments_clean.csv` is empty
      by acquisition status, NOT because the city publishes none.
- [x] **Millcreek geo: source pre-2022 (2016) district boundaries — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** AUTHORITATIVE 2017-2022 layer found on the city's own ArcGIS org → plan_2016 medium→HIGH; the dissolve reconstruction proven materially wrong here (IoU ≤0.25, renumbered MIL codes) → validation lead (c) queued for the other reconstructed cities. (2026-07-06).** PARTIALLY
      ADDRESSED 2026-07-11: the roster now carries a RECONSTRUCTED `plan_2016` map
      (`geo/council_districts_pre2022.geojson`, dissolved from 2017+2019 precinct→district over
      current precinct shapes, `confidence=medium`, approximate) — pre-2022 address→district is now
      medium-approximate rather than blank/inaccurate. Still open: the AUTHORITATIVE 2016-incorporation
      boundary vintage (exact) is not sourced; fetch it (SL County GIS historical / incorporation
      exhibit) to promote from `medium`→`high`. See `scripts/roster_boundary_recon.md`.
- [x] **Millcreek + Taylorsville: PMN born-digital minutes upgrade — ✅ BOTH HALVES DONE.**
      **Taylorsville half CLOSED 2026-07-12** (6 born-digital promotions — see the Taylorsville
      expansion follow-ups item (a)). **Millcreek half DONE 2026-07-20 — VERIFIED NEGATIVE, 0
      upgrades available.** Enumerated all 106 council `format=scanned` + 36 PC `format=ocr`
      dates, mapped each to its PMN minutes attachment (cached notices HTML), fetched + measured
      every PMN PDF text layer (`pdffonts`/`pdftotext`; binaries §9-discarded). 142 date-probes:
      **92 scanned** (PMN copy also a scanned image), **38 now-404** (old 2017–18 PMN file ids
      purged/rotated off utah.gov/pmn), **10 no-PMN**, **2 "born-digital" that are cross-body
      false positives** — both (`1186547` CC 2024-01-09, `1122567` CRA 2024-02-26) are
      byte-equivalent to repo files that are ALREADY `format=text`, while the genuinely-scanned
      same-date repo files (the OTHER body) have only scanned PMN copies. Millcreek's city posts
      the SAME generation of each doc per body to both AgendaCenter and PMN, so no OCR-noise swap
      is possible (opposite of Taylorsville's RICOH-vs-born-digital case). Full per-date inventory:
      `millcreek_city_council/pmn_backfill/ocr_upgrade_probe.csv`; write-up in that folder's
      CLAUDE.md (2026-07-20 section). Backup `_backups/2026-07-19-pv-tierb-low/p4-millcreek/`.
- [ ] **Taylorsville geo: precinct-derived districts (2026-07-06).** No official council-
      district GIS layer exists; districts are derived from precinct × district-contest rows
      (post-2020 vintage), approximate near precinct edges. Source and swap in an official
      layer if one is ever published.
- [ ] **Taylorsville: 2 pending 2026 council meetings (2026-07-06).** 2026-06-17 minutes
      not-yet-posted; 2026-07-01 cancelled. Re-probe the portal when 06-17 posts and ingest.
- [x] **expand-city-sources for south_jordan / millcreek / taylorsville — ✅ CLOSED
      2026-07-19 as SUBSUMED**: all three cities were expanded in the later 2026-07
      waves (verified on disk: every expansion dataset dir present + populated — SJ
      packets 170 / ords 131, millcreek packets 553 / ords 551, taylorsville CF 72
      filings / ords 91; all three in the 29-city CF-structuring package + transcripts
      AVAILABILITY mapped). *(original, 2026-07-06)* Base builds are done; offer the
      6-source expansion for all three, one city at a time.

## [DEBT]+[WATCH] Minutes-promotion wave — COMPLETED 2026-07-16 (13 cities); new follow-ups

All 13 queued pmn_backfill/independent-source minutes promotions executed in one day
(3 batches of parallel per-city agents; single federation at the end). **Repo-wide
result: federated motions 50.6k → 52,510, votes ~175k → 182,984, contested 3,486 →
3,681, recovered-provenance motions now 2,189** (`pmn_minutes` 1,051 +
`agendacenter_minutes` 592 [SSL] + `wayback_minutes` 165 [holladay] + `pmn_roa` 381),
`foreign_key_check` 0 / `integrity_check` ok / search-layer reconciliation exact;
coverage.json regenerated (433 dataset entries); all 13 cities validate 0 FAIL.
Per-city dated DONE notes are on each city's expansion-follow-ups item; full agent
reports summarized there; backups in `_backups/2026-07-16-minutes-promotion/<city>/`.
Convention notes established this wave: promoted-doc weeks bundles show "Meetings: 0"
with votes present where docs live in pmn_backfill/ (midvale/magna/alta pattern); after
any `extract_votes.py` re-run, cities with an `extract_backfill_votes.py` MUST re-run it
(documented per city — herriman would silently drop 949 pmn rows otherwise).

**NEW follow-ups the wave surfaced (queued):**
- [x] **[med] herriman PC T3.1(j) sync — STALE: already synced 2026-07-17; LM-wave verification instead found+fixed 3 latent non-idempotency bugs in BOTH copies (mover-blanking healer, form-feed OUTCOME_RE, role-strip) → 6 PMN movers recovered, 949 pmn rows intact.** — the
      "one file, both datasets" copies have diverged (OUTCOME_RE wrap-healing, narrative
      rolls, result-cut missing on the PC side). Sync + re-extract PC + diff.
- [x] **[med, high yield] emigration_canyon PC seconder miss — STALE: fixed 2026-07-17 (124/141 filled, verified 2026-07-19 with throwaway old-regex proof); LM wave additionally recovered a whole dropped 2019-06-19 council motion via the same class (`second by` anchor), 296→297.** — the clerk's structured
      label is `2nd by:` (~129 occurrences / 51 docs) but the extractor parses only
      `Second(ed) by:`; 9 seconders captured today, a one-regex repair + re-extract fills
      ~120 (non-additive field changes — needs its own diffed pass).
- [x] **[med] draper PC narrative-era recovery pass — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** grammars were pre-applied 2026-07-17; LM wave source-verified all 9 named-row motions (Squire 4-1 confirmed), proved 2022+ byte-stability, and completed the deferred derived rebuild (h.db +32 delta → 0; contested 214→220).** — ~11 audited 2020-21 PC docs use
      "Commissioners X, Y voting in favor" + "This item passed with a N to M vote",
      currently tally-only; at least one REAL dissent invisible (2021-02-25 Squire 4-1).
      Corpus-affecting; own audited re-extraction diff.
- [x] **[med] fetch_new.py PMN-probe gaps — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** murray now probes PMN 735/983 (4 2026 PC dates re-probed: still agenda-only), white_city probes PC 5879; exception ledgers proven unnecessary (0-flag crosscheck runs); bonus: 7 stdout-only cities now write standard probe JSON.** (seed these into the
      PMN-crosscheck engine's pmn_bodies.csv when it's built): murray probes CivicPlus
      only (PC + 2023+ council live on PMN bodies 983/735; also re-probe the four 2026
      agenda-only PC dates); magna doesn't probe CRA body 6925; white_city doesn't probe
      PC body 5879. Also: magna/midvale/alta promoted dates live outside minutes_index —
      probes may re-flag them as "new" without an exception ledger.
- [x] **[med] SSL roster refresh — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** both fills were already rostered (source-verified); chair seam RESOLVED no-change (Bynum presided across the whole corpus); Huff overrides verified live; reconciliation exact.** (`update-council-roster`) — promoted minutes expose
      seams: 2023-10-25 D5 vacancy fill, 2025-01-22 at-large vacancy fill, January chair
      elections. Plus **[low]** two clerk-typo vote lines leaving Huff honestly
      unrecorded (2024-02-28 RDA m2 "Ye"; 2026-01-14 council m3 "Y/es") — documented
      `db/vote_overrides.csv` candidates; 2025-07-23 m3 printed an unfilled "Y/N" roll
      template (no vote record at source — honestly uncaptured).
- [x] **[low] "recommend"→Ceremonial classifier trap — DONE 2026-07-20.** Corpus
      characterization first: the shared classifier's **ceremonial RULE is NOT the
      culprit** — `\bcommendation\b` never matches "recommendation" (word boundary;
      verified `To recommend approval` → no match, `commendation for service` → match).
      The real defect is upstream: **62 `motions_std` rows carry `motion_type_std=Ceremonial`
      via CROSSWALK because the per-city EXTRACTORS emit native `motion_type='Ceremonial'`
      off the "commend"/"recommend" substring** (the trap white_city's extractor already
      guards locally). Enumerated all 62 (Ceremonial ∩ recommendation-grammar TEXT_REC_RX):
      murray 15, bluffdale 13, herriman 11, cottonwood_heights 7, kearns 6, midvale 5,
      nephi 3, vineyard 1, alta 1 — almost all PC "forward/recommend approval to City
      Council of [text amendment / rezone / code item]". **Fix:** a guard in `classify()`
      (`scripts/normalize_motions.py`) — when native maps to Ceremonial AND the text is
      a recommendation AND carries no genuine ceremonial signal (`CEREMONIAL_TEXT_RX`:
      proclamation/commendation/ceremonial/declaring-day), drop the bogus Ceremonial lock
      and reclassify by the substantive rules (accept only a HIGH-confidence type; else
      honest `Other` via new method `rule:rec-not-ceremonial`). None of the 62 fire a high
      substantive rule (plural "Text Amendments"/generic "Title 10" evade the land-use
      patterns by design — not touched, to preserve byte-stability), so all 62 →
      `Other`/low; `action_class` stays `recommendation` (unchanged on all 62). Verified
      each of the 62 against its text: every one is not-ceremonial. HARD GATE met:
      31-city regen diff = **exactly 62 rows changed, all Ceremonial→Other, 0
      action_class/land_use changes, everything else byte-identical**. (Follow-up idea,
      not done: enhance land-use rules to catch plural "Text Amendments"/"Chapter 17.x"
      so these PC land-use recommendations land in Land-Use instead of Other — deferred
      because it would ripple to non-Ceremonial rows.) Backups
      `_backups/2026-07-19-pv-tierb-low/p4-normalizer/`.
- [ ] **[low] herriman Appeal Authority body modeling** — 2 hearing docs catalogued in
      pmn_backfill (2025-02-20, 2026-06-09); no appeals body in the city model yet
      (same class as Orem BoA / CH Appeals Hearing Officer).
- [x] **[low] riverton audited "Substitute Motion … MOVED" review** (done 2026-07-19) —
      reviewed at source. The two real audited "made a substitute motion and MOVED"
      minutes are **2024-08-06** and **2020-05-19** (the TODO's "2024-04-16" was a
      misID — that meeting has no substitute; its motion 8 is a compound single
      McDougal motion, correctly extracted).
      • **2024-08-06 (Buroker case) — DEFECTIVE → FIXED.** Source: McDougal MOVED an
        original (create ordinance banning cargo containers, no second/no vote);
        Buroker "made a substitute motion and MOVED" to review Ord 18.225.020, McDougal
        SECONDED, roll call 5-0 pass. The substitute's "MOVED" is not adjacent to
        "Buroker", so the MOVED-anchor regex missed it and folded the substitute onto
        McDougal's superseded original → mover mis-credited to McDougal + conflated
        motion text. Fixed at the extractor (`extract_votes.py` new `SUBST_MOVED`
        re-anchor, guarded by a zero-width lookahead to fire ONLY when the substitute
        was SECONDED). Result: mover McDougal→Buroker, motion text = the substitute's
        text, superseded original correctly emits no row (superseded-without-vote).
        Only those 5 rows changed — full-corpus `all_votes.csv` diff byte-stable
        elsewhere (2020-05-19 / 2021-04-06 / pmn_backfill untouched).
      • **2020-05-19 — FAITHFUL, left untouched.** Stewart "made a Substitute Motion
        and MOVED" but it DIED for lack of a second; the 3-2 roll call belongs to
        Buroker's ORIGINAL Ord 20-13 motion (motion 7), already extracted correctly
        (mover Buroker, Aye={Buroker,McDougal,Wells}). The SUBST_MOVED lookahead
        deliberately skips DIED substitutes so this stays correct.
      Rebuilt db/build_db.py + build_referrals + build_weeks + normalize_motions
      riverton; validate_city.py = 23 PASS / 3 WARN (pre-existing documented
      extensions) / 0 FAIL. Backups: `_backups/2026-07-19-pv-tierb-low/p4-riverton/`.
- [x] **[low] riverton 2021-04-06 missing original motion — DONE 2026-07-20.** Res 21-26
      (RCV interlocal): Stewart's substitute (motion 4) captured correctly (Failed 2-3);
      McDougal's ORIGINAL motion, re-presented after the substitute failed and PASSED 4-1
      (Buroker/McCay/McDougal/Stewart Yes, Wells No), was MISSING because the parser takes
      only the FIRST roll call per MOVED-window and the re-presentation carries no MOVED
      anchor. **Method chosen: a tightly-scoped extractor recovery (`extract_votes.py` new
      `REPRESENT` rule), NOT a general window-split.** Rationale: a general second-rollcall
      split would ALSO fire on the 4 OTHER multi-rollcall MOVED-windows in the corpus
      (2020-05-05 McDougal Ord 20-12; 2021-06-01 Buroker Ord 21-14; 2023-01-17 Mayor Pro Tem
      nomination; 2024-06-04 Pierucci re-brought McCay's fee motion) — each a genuinely-missing
      SECOND motion but of a DIFFERENT trigger class (two-word first name / non-adjacent MOVED
      / nomination grammar), so a general split would recover 5 motions and violate the
      "byte-stable outside this recovery" requirement. The literal grammar "…original motion
      was presented before the council again" is UNIQUE to the 2021-04-06 file (verified across
      every council minutes file), so the rule fires ONLY here. It re-anchors the re-presentation
      as its own motion, reusing the superseded original's stashed mover/seconder/text
      (McDougal / Buroker / "approve Resolution No. 21-26 – …Interlocal Cooperation Agreement…
      Municipal Election") with the re-presentation's own roll call (4-1) + outcome (Passed).
      **New rows: motion 5 = McDougal original 21-26, Interlocal, Passed, Stewart/McCay/Buroker/
      McDougal Aye + Wells Nay (4-1)**; substitute stays motion 4 (byte-identical); Res 21-23 /
      21-24 / adjourn renumber 5→6, 6→7, 7→8 (faithful vote-sequence position). Verified vs
      minutes verbatim (mover line 379, seconder line 382, roll call lines 427-428). Diff proof
      (`comm -23`/`-13` sorted pre/post all_votes.csv): removed 15 lines, added 20 lines, **all
      on 2021-04-06, ZERO changed lines elsewhere** (net +5 rows). Rebuilt extract_votes +
      extract_backfill_votes + normalize_motions riverton + db/build_db + build_referrals +
      build_weeks; validate_city.py = 23 PASS / 3 WARN (pre-existing documented provenance +
      Mayor-tie-break extensions) / 0 FAIL; db reconciles 4375==4375, weeks sum 3756. Backups:
      `_backups/2026-07-19-pv-tierb-low/p4-riverton2/`.
      **↩ FOLLOW-UP: 4 sibling missing-motion gaps — ✅ ALL 4 RECOVERED 2026-07-19**
      (`_backups/2026-07-19-pv-tierb-low/p4-riverton3/`). Same "second motion in a
      MOVED-window is dropped" symptom, different (non-re-presentation) triggers, each fixed by
      a narrow per-trigger-class re-anchor in `meeting_minutes/extract_votes.py` (siblings of
      SUBST_MOVED/REPRESENT, all grep-verified to fire on exactly one meeting corpus-wide):
      · **2020-05-05 Ord 20-12 (5-0, m3)** — two-word first name "Council Member Troy McDougal
        MOVED" hid the anchor → **FULLNAME_MOVED** strips the given name onto the roster surname
        (case-explicit; a `(?!role-word)` guard stops the "Election of Mayor Pro Tem" header from
        being read as ROLE+firstname on the 4 Jan Mayor-Pro-Tem-election files). mover McDougal /
        sec Buroker.
      · **2021-06-01 Ord 21-14 (5-0, m4)** & **2024-06-04 Pierucci fee (4-1 pass, m8)** —
        non-adjacent "…and MOVED" ("Buroker supported this proposal and MOVED"; "Pierucci asked to
        bring back the original motion made by Councilmember McCay and MOVED") → **ANDMOVED**
        re-anchors the sentence-subject surname. A `(?<![Mm]otion)` lookbehind EXCLUDES the four
        sibling "…motion and MOVED" cases that are out of scope / handled elsewhere (2024-08-06 +
        2025-05-06 + 2020-05-19 substitute motions, 2023-12-06 "amended his motion") — all left
        byte-identical. mover Buroker/sec Stewart; mover Pierucci/sec Buroker.
      · **2023-01-17 Mayor Pro Tem election (5-0, m2)** — nomination grammar, no MOVED verb
        ("Councilmember Wells nominated Councilmember McDougal to be the Mayor Pro Tempore.
        Councilmember McCay seconded this nomination.") → dedicated **NOMINATE** emitter (keeps
        the Appointment motion_type; mover Wells / sec McCay).
      HARD GATE PASSED: CSV-aware pre/post diff of `all_votes.csv` shows changed rows on EXACTLY
      the 4 target dates (+20 vote rows = the 4 recovered rolls; every other changed row is
      faithful in-meeting motion_no renumbering, content byte-identical) and ZERO off-target
      change — the already-fixed 2024-08-06 / 2020-05-19 / 2021-04-06 rows are byte-identical.
      Ran extract_backfill_votes (pmn_minutes unchanged), rebuilt db/build_db + build_referrals
      (INTEGRITY OK; referrals 59→60) + build_weeks + `normalize_motions.py riverton` (890/682
      motions, outcome-coverage 100%). validate_city = 23 PASS / 3 WARN (pre-existing documented
      provenance + Mayor-tie-break extensions, no new WARN) / 0 FAIL; db reconciles 4395==4395,
      weeks sum 3776. Council motions 852→856 (+4); v_contested 135→136 (the 4-1 fee motion).

      ⚠ **INCIDENT (self-reported): `normalize_motions.py --help` triggered the all-31-city
      sweep** (`--help` is an unknown arg → bare-run codepath). It REWROTE every city's
      motions_std.csv, but the file is a deterministic/idempotent function of each city's
      (untouched) all_votes.csv + script-embedded crosswalks, so **content is byte-unchanged**
      for the 30 non-riverton cities — PROVEN: md5 of all 128 non-riverton motions_std.csv is
      identical before vs after an explicit clean re-run (only mtimes bumped, no all_votes.csv
      touched). No harm; noted per discipline.
- [x] **[low] cottonwood_heights pleading-line digit-bleed** — "Commissioner 7 Ebbeler
      seconded" leaves a seconder blank; candidate scrub in SECONDER_RE handling.
      **DONE 2026-07-20:** PMN/DOCX pleading-paper minutes carry a numbered left-margin
      gutter; once `load_text` collapses the page each line-start number lands mid-text and
      splits the seconder attribution ("seconded by Commissioner 40 Shelton"). Fixed in
      `ch_vote_lib.py::parse_meeting` — the SECONDER pass now runs on a bare-line-number
      scrub of `motion_text` (mirroring the scrub `parse_roll` already applies inside
      Vote-on-Motion blocks); the scrub feeds ONLY the name match, the stored motion prose
      stays un-scrubbed (no prose loss). MOTION_START/mover left on the un-scrubbed window
      on purpose (the gutter digit there guards against a spurious earlier "…Commission. <n>
      Commissioner X moved" boundary). Re-extracted: **PC +67 seconder rows recovered
      across 23 motions** (all blank→real roster name, 0 overwrites, all ground-truthed vs
      source "seconded by" context); **council 0 changes** (born-digital portal PDFs have no
      gutter). No lost/recovered vote rows (roll members were already digit-scrubbed), no
      motion/result/motion_type/tally/outcome changes; motions_std byte-identical.
      Derived chain rebuilt (build_db/build_referrals/build_weeks/normalize_motions);
      validate_city 24 PASS / 2 WARN (pre-existing provenance-col WARNs) / 0 FAIL. Backup:
      `_backups/2026-07-19-pv-tierb-low/p4-ch/`. NOTE: federated `cities.db` now stale for
      CH — regenerate with `scripts/build_cities_db.py` in the next federation pass (not run
      here per task scope).
- [x] **[low] herriman short-doc wrong-doc audit** — DONE 2026-07-20. Audited all **14**
      short zero-vote audited council-body docs (the complete current zero-vote set;
      earlier vote-affecting cases like 2021-10-13 already repaired). Dispositions:
      **(a) genuine short/no-vote = 13**, **(b) content-mismatch → real minutes recovered
      = 1 date (2022-02-09)**, **(c) truncation = 0** (live re-fetch confirmed every
      capture byte-faithful to source). Detail:
      • 3 lack-of-quorum certified minutes (2021-02-18, 2021-02-25, 2021-03-05 — adjourned
        for no quorum, genuine zero). • 5 agenda-half work/strategic docs whose meeting's
        votes ARE captured in the same-date sibling minutes doc (2021-04-14 wm1↔ccm 28v;
        2021-05-12 wm-p1↔wm-p2 19v; 2021-05-26 wm-p2↔wm-p1 19v; 2022-02-15 sp-p2↔sp-p1;
        2022-03-09 wm↔wm2 25v). • 3 discussion/notice agendas with no action items
        (2021-01-22 legislative-priorities w/ Sen. Fillmore; 2022-03-30 special
        discussion/OPMA-training; 2024-12-17 Notice of Quorum). • **2022-02-09**: the
        THREE stored docs (PrimeGov CompiledDocument "Minutes" templateIds 405/409/415)
        all return the AGENDA — the portal's Minutes slot was never populated (live
        re-fetch 2026-07-20 confirms agenda-only). The genuine RCCM minutes (approved
        2022-03-23, video exists) were on **PMN body 1155 file 828869** and were recovered
        → `pmn_backfill/{raw,text}/pmn_council_2022-02-09_828869.*` + index row →
        **+13 vote rows** (2 unanimous 5-0 roll calls incl. voting Mayor Palmer + 3
        tally-only), `provenance=pmn_minutes`. mm pmn_minutes 677→690; canonical 3645
        unchanged; diff-proven additions-only (0 rows lost). The 3 agenda docs are
        retained as-is (city-faithful portal artifacts, zero-vote, do not pollute the vote
        layer; two are the known PrimeGov double-event general-meeting duplicates).
        Derived rebuilt (normalize_motions herriman, build_db +0 delta, build_referrals,
        build_weeks); `validate_city.py herriman_city_council/` = 24 PASS / 2 WARN
        (documented `provenance` col) / 0 FAIL. Backups: `_backups/2026-07-19-pv-tierb-low/
        p4-herriman/`.
- [x] **[low] normalizer refinement lead (alta) — DONE 2026-07-20.** Emergency-proclamation
      resolutions were classified `Ceremonial` (the ceremonial rule's bare `\bproclamation\b`
      firing on "…extending the Emergency Proclamation…"), inconsistently with the SAME
      governance action classified `Resolution` in taylorsville/magna/riverton (whose minutes
      say "Declaration"/"Proclaimed" not "Proclamation"). Enumerated corpus-wide: the
      "emergency" & "proclamation" co-occurrence matches **17 rows — 16 currently Ceremonial
      (the defect) + 1 genuinely Procedural** (bluffdale 2020-04-22 m2, a consent-agenda
      removal step). **Fix:** two new HIGH rules `emergency-ord` / `emergency-res` placed
      BEFORE `ceremonial` (and AFTER the proc-* rules, so the Procedural consent-agenda step
      still wins) in `scripts/normalize_motions.py`: emergency proclamations/declarations are
      a substantive vehicle → `Ordinance` where the text names an ordinance (millcreek
      2023-05-08), else the modal `Resolution`. Result: all 16 → 15 Resolution + 1 Ordinance,
      consistent with the other ~20 emergency extensions repo-wide; also fixes two native
      mislabels the ceremonial rule had masked (millcreek 2020-09-14 native `Appointment`;
      park_city×2 / st_george native `Ceremonial`) by overriding to Resolution. Verified each
      of the 16 against its text. HARD GATE met: 31-city regen diff = **exactly 16 rows
      changed, all Ceremonial→Resolution/Ordinance, bluffdale m2 stayed Procedural
      (byte-identical), 0 action_class changes, everything else byte-identical.** Backups
      `_backups/2026-07-19-pv-tierb-low/p4-normalizer/`.
- [ ] **Watches:** magna 2025-11-18 CRA — re-check PMN for an APPROVED copy (current
      DRAFT rejected, sidecar); SSL 2025-02-12 RDA minutes unpublished (city filed
      council minutes in that slot); midvale 2023-01-17 RDA session minutes (held,
      unpublished) + whether a 2024-08-06 midvale council meeting occurred; SSL rejected
      dup 2023-09-21_pc AgendaCenter copy holds an ADJOURN motion the audited PMN copy
      lacks (optional swap).
- Notes: ~300 new murray PC motions postdate the motion-classification ground-truth
  audit (dispositions computed, unaudited); murray's 86-video caption-fetch item is now
  LOWER priority (minutes recovered); EC VERIFICATION.md carries pre-existing T3.1(k)
  staleness (flagged in its addendum); riverton/EC roster layers gain new vote evidence
  at re-federation (Stewart/Wells Jan–Feb 2020 corroborated).

## [TAIL] Expansion & routine operations — fold into the quarterly refresh, do NOT queue

- [x] **expand-city-sources rollout — ALL 13 CITIES EXPANDED (completed 2026-07-06).** Lehi, St. George,
      West Jordan, Provo, Sandy, Orem, Logan, Vineyard, Nephi, Park City, Ogden, SLC, West Valley — each has
      the six additive datasets (packets, housing_plans, ordinances, pmn_backfill, transcripts, campaign_finance),
      per-city `EXPAND_SOURCES_REPORT.md`, rebuilt `sources.csv`, and parent-doc sections. **One open item:**
      **SLC campaign_finance is a portal-blocked honest gap** — the JSON WebAPI was down (503 maintenance) during
      the run; API is reverse-engineered + a harvester is scaffolded → **re-run `slc_city_council/campaign_finance/`
      harvest when `dotnet.slcgov.com/Attorneys/CampaignFinance_Public/` is back up.** Method notes: each city = 6
      parallel agents + orchestrator consolidation; scratchpad hygiene = dataset-unique filenames (2 contamination
      incidents handled: nephi stray VTTs, park_city ran a leftover Vineyard harvest.py → Vineyard restored).
- [x] **Structured campaign-finance layer — ✅ BOX CLOSED 2026-07-20 as SUPERSEDED: the
      layer now covers 29 cities (CF-STRUCTURING PACKAGE 2026-07-18 + the 2026-07-19/20
      tranches); this entry's two live riders both landed 2026-07-20 — WJ-2021 handwritten
      backfill verified complete, and `is_incremental` re-derived per-candidate in the
      shared driver (WJ/sandy/orem + WVC/taylorsville audits, page-proven overrides).
      Remaining CF work lives in the owner-gated queue (below-floor tranches, hand-check)
      and per-city acquisition watches. Historical record follows.** *(original)*
      — 8 of 13 cities built (provo, west_jordan, lehi, sandy, orem, logan,
      nephi; **vineyard done 2026-07-06** — 108 contributions / 127 expenditures / 59 filings; reused
      `utah_standard_form` unchanged; 16 born-digital [8 direct + 8→vision for donor fidelity] + 39 scanned→vision +
      4 archive-truncated honest-blanks; 35/59 both-reconcile; all `is_incremental=True`; ~$1.88 vision).
      Canonical per-candidate rollup = `scripts/campaign_finance/cycle_totals.py` → `cycle_totals.csv` (**never sum
      `filing_totals`** — one row per filing). **ogden done 2026-07-06** — new `ogden_form` family (whole-cycle
      "Combined Report" packet; Attachment A/B; in-kind per-row flag; summary-box fallback + born-digital
      completeness guard for corrupted Adobe text layers); 1,073 contributions / 649 expenditures / 38 filings;
      21/38 both-reconcile; text 661 / OCR 218 / vision 194 rows; `is_incremental=False`; ~$1.7 vision (12 filings).
      ~~Remaining: WJ-2021 handwritten backfill.~~ **[VERIFIED DONE 2026-07-20]** — the backfill was in
      fact completed 2026-07-12 (all 9 city-2021 bundles carry full multi-report `reports[]` vision
      caches under the current `sha1(path)[:8]` keys; WJ campaign_finance/CLAUDE.md documents the
      per-filing adjudication) but this line was never checked off. Re-verified 2026-07-20: rebuild is
      fully idempotent (all 4 CSVs byte-identical), 110 contrib / 130 expend vision rows across the 8
      candidates, 3/9 both-reconcile + 6 decomposed page-verified filer artifacts, validator PASS,
      locked cycle figures intact (Lamb 6,577.00/5,998.12; Green 26,713.35/20,301.73; Whitelock
      2,300.00/3,140.54). ~~**Follow-up: `is_incremental` was set as a per-city constant but is
      per-candidate**~~ **[DONE 2026-07-20]** — empirical per-candidate derivation PORTED into the shared
      driver (`scripts/campaign_finance/driver.py: derive_is_incremental()`, the vineyard/logan/nephi
      row-overlap method run on parsed rows, live filings only, pooling both sides; opt-in
      `derive_incremental=True`). Wired: west_jordan (merged-groups call — 6 cumulative candidate-cycles
      restamped, incl. page-verified Rulon Green 2023 / Pack 2025 / Whitelock 2021+2025), sandy + orem
      (run-level). Row-metadata only — cycle figures move ONLY via documented `cycle_overrides.csv`
      (WJ 3 rows, all page-verified; each was a real double-count/undercount). **Collateral find, FIXED:
      sandy + orem builds read the stale `report_period` index key after the column was renamed
      `reporting_period` → every filing got a blank period, dedup collapsed each candidate-cycle to its
      last filing (sandy 65 false supersessions vs the 12 documented; orem 63; e.g. sandy Stroud 2023
      printed 0/0 vs her YTD-proven $970/$970). Keys fixed; sandy cycle_overrides.csv (9 rows) + orem
      cycle_overrides.csv (15 rows) added, every changed figure verified against filing evidence (YTD
      chains / printed FILING-PERIOD ranges / row-level restatement checks incl. a date-blind
      amount-containment audit — the Duerden date-drift trap); validators PASS; builds idempotent.
      ~~QUEUED follow-up: extend `derive_incremental=True` to the remaining constant-based cities —
      read-only preview found evidence-backed cumulative filers in **west_valley** (7: Buhler 2021, Wood
      2025, Curtis 2023, Christensen 2023, Fenn 2023, Jimenez-Vivanco 2023, Lang 2025) and
      **taylorsville** (Barbieri 2021); park_city/st_george showed none; provo/ogden constants are
      form-inherent (whole-cycle filings); lehi derives per filing from form language.~~
      **[DONE 2026-07-20]** — `derive_incremental=True` wired into west_valley + taylorsville.
      Driver-level derivation found MORE than the preview: **west_valley 11 cumulative candidate-cycles**
      (the 7 previewed + borderline-median Jones 2021, George JR 2025, Turcsanski 2025, Mahoney 2025) and
      **taylorsville 2** (Barbieri 2021 + Cochran 2023) — every flip audited row-level, the pivotal ones
      page-verified against raw PDFs; a date-blind amount-containment sweep (Duerden trap) found 0 missed
      cumulative filers among the non-flipped. **2 page-cited cycle_overrides written** (only figure
      changes): **west_valley Karen Lang 2025 Mayor $54.97/$54.97 → $10,244.85/$10,244.85** (cumulative
      post-primary + balance-carry general/final — the $54.97 "Total contributions" lines are the carried
      balance with Form A empty; final's Form B "Repay loan" $54.97 closes the chain to $0.00 exact) and
      **taylorsville Curt Cochran 2023 spent $121.44 → $60.72** (his Gen Election Report re-lists the
      28-Day's two items verbatim with the identical $800.00→$739.28 balance chain — a restatement, not a
      new period). All other flipped cycles' computed figures verified already-correct (incl. the
      adjudicated Buhler 2021 27,584.45/26,717.47 — untouched). Gates proven both cities: filing_totals
      byte-identical; contributions/expenditures changed in the `is_incremental` column ONLY (WV 515+417
      rows, TAY 2+12); cycle_totals byte-identical bar the 2 override rows; rebuilds idempotent;
      validate_finance PASS (WV 0/0; TAY 0 fails + the expected doc8378-dup WARN); taylorsville's locked
      Johnson 2021 D5 override (8,745.05/8,745.12) and regime-aware annual exclusion (49 filings) verified
      binding unchanged. Backups: `_backups/2026-07-19-pv-tierb-low/p4-cf2/`. Dated addenda in both
      cities' campaign_finance/CLAUDE.md. Remaining constant-based cities intentionally NOT wired
      (park_city/st_george no evidence; provo/ogden form-inherent; lehi per-filing) — the follow-up is CLOSED.
- [ ] **Park City expansion follow-ups (2026-07-05):** (a) **194 meeting videos but ZERO captions** (CivicClerk
      MP4 feed) — a Whisper transcript layer is the only path to text; 3 newest meetings (2026-06-04/11/25) have
      no published minutes yet, so video is their only record. (b) **[DONE 2026-07-20]** The two labels were
      ordinance NUMBERS, not dates: **2024-08** (Title 4A Special Events, adopted 2024-05-16) and **2026-08**
      (§2-3-11 Property Disposal, adopted 2026-05-07). Verified against the primary minutes: both are **genuinely
      consent-folded, NOT an extractor grammar gap** — each is an unnumbered line item under the meeting's
      `CONSENT AGENDA` header, adopted **en bloc** by the single "moved to approve the Consent Agenda" motion that
      is ALREADY in `meeting_minutes/all_votes.csv` (2024-05-16 m5, Parigian, 5-0 Pass; 2026-05-07 m4, Miller, 5-0
      Pass). No separable per-ordinance roll call exists, so `all_votes.csv` is unchanged (adding one would
      fabricate an itemized vote); extractor untouched, PC corpus byte-stable, 9 vote-overrides + 2 mayoral
      tie-breaks intact. Documented honestly: the two `ordinances/` `none`-tier rows stay `none` (match fields
      empty, never forced) but their `linkage_note` now cites the en-bloc consent motion instead of "no vote row";
      AVAILABILITY.md Gaps section annotated. `validate_city` 24 PASS / 2 (expected) WARN / 0 FAIL. Backups:
      `_backups/2026-07-19-pv-tierb-low/p4-parkcity/`. (c) Betsy Wallace filed a 2023 primary CF statement but is absent
      from `election_results` (withdrew).
- [ ] **Nephi expansion follow-ups (2026-07-05):** (a) **[DONE 2026-07-19] CRA body built.** PMN body 5737
      harvested in full (10 notices 2016–2023, `pmn_backfill/cra.json`; raw + fetch log retained). Finding:
      **0 new minutes within the 2020 floor** — the CRA is a sparse, in-session body already captured as
      `body=CRA` in `meeting_minutes/all_votes.csv` (1 motion, 2021-07-27). Modeled as a `body=` value inside
      `meeting_minutes` (slc/holladay/millcreek pattern), crosswalk row in `scripts/normalize_motions.py`
      BODY_CROSSWALK + `crosswalks/body_crosswalk.csv`. The one within-floor gap (2023-12-19, agenda-only,
      minutes 404 everywhere) is ledgered in `meeting_minutes/minutes_unrecovered.csv`. Pre-floor CRA
      (2016–2019) enumerated, not promoted (2017-12-19 minutes doc is a 404/purge; 2019 schedule doc retained
      raw). Derived chain rebuilt with **zero motion/vote delta** (1279 motions unchanged). Backups:
      `_backups/2026-07-19-pv-tierb-low/nephi-cra/`. (b) **[DONE 2026-07-20] 2023 municipal primary
      CONFIRMED + added.** A real **Sept-5-2023** Nephi City Council primary was held (9 candidates,
      Vote-For-3 → top-6 advanced); earlier builds wrongly said "no 2023 primary" (they assumed a
      6-candidate field and saw only the empty EV `primary09052023_Demo` slug). Recovered from the
      OFFICIAL Juab County Clerk canvass PDF (`Official-Results-Prim-23.pdf`; header "OFFICIAL RESULTS —
      Municipal Primary Election — September 5, 2023"), stored at
      `election_results/raw/juabcounty-2023-primary-official-results.pdf` and hand-keyed via
      `build_nephi_manual.py` (build_nephi.py races output also migrated to the SCHEMA_SPEC §9 25-col
      superset). Results: Worwood 733, Parady 672, Cowan 652, Ostler 583, Bradley 484, Miller 449
      (**advanced** — exactly the 2023 general field); Andersen 281, Ford 200, Goates 160 (eliminated).
      The CF-flagged OCR names "Vanessa Goode"/"Carolyn Louise" = GOATES/FORD. races 7→8; existing 7 rows
      byte-identical; validate_city 26 PASS / 0 FAIL. Docs updated (election_results CLAUDE +
      ELECTION_VERIFICATION, campaign_finance AVAILABILITY flag marked resolved). registered/ballots/turnout
      left blank on the primary row (the PDF stats are COUNTY-wide, not Nephi-only); no precinct breakdown
      (summary PDF). **cities.db `election_race` will pick this up on the next `build_cities_db.py` run
      (not run here per instructions).** (c) **[DONE 2026-07-20] 4 flagged land-use ordinances resolved
      2+2 via a vote-extractor fix.** Two were genuine extractor gaps, now recovered into `all_votes.csv`:
      **05-20-2025** (300 W rezone, `made THE motion` grammar gap — anchor widened to
      `made\s+(?:a|the)\s+motion`; recovered as a **4-0 named roll call**) and **06-20-2023** (temporary-
      ordinance rescission, mover surname OCR-mangled `Wowood`→Worwood alias). The systemic `made the motion`
      fix (2025 recorder style) recovered **+57 motions** corpus-wide (918→989 motions, 1090→1180 rows,
      46→51 named); plus mover aliases Pardy→Parady, Cown→Cowan, Ost.er→Ostler, first-name Jeramie→Callaway.
      **Additions-only proven** — exactly ONE pre-existing row changed (2023-09-19 CR-Circle-3 seconder
      ''→JD Parady, a real recovery: source reads "Councilor Pardy seconded"); everything else is net-new or
      in-meeting renumbering. The other two are honest, NOT extraction misses: **05-18-2021** (McPherson
      rezone) was **tabled by verbal consensus** — the minutes print no mover/seconder/vote; **07-12-2022**
      (§10.3.6 sign-permit) IS already in `all_votes.csv` — adopted **2022-07-19** (number-date≠meeting-date
      quirk), only the number-keyed `ordinances/index.csv` couldn't link it. ordinances none-tier 11→7
      (06-20-2023, 05-20-2025 + bonus 03-04-2025, 09-02-2025-B now linked). Derived chain rebuilt
      (db/build_db + build_referrals + build_weeks + normalize_motions nephi); validate_city 26 PASS / 0
      WARN / 0 FAIL; tally 51/51. Backups `_backups/2026-07-19-pv-tierb-low/p4-nephi/`. **cities.db needs a
      `build_cities_db.py` run to reflect the +57 motions (not run here).** (d) Full PMN body-1788 "Notice
      of Ordinance" harvest deferred (its search is JS/opaque; 5 corroborators retrieved so far).
- [ ] **Vineyard expansion follow-ups (2026-07-05):** (a) **[DONE 2026-07-10] Promote the net-new RDA
      minutes layer** — `meeting_minutes/extract_backfill_votes.py` reuses `process_file(default_body=RDA)`
      over the 43 recovered RDA minutes and merges with `provenance='pmn_minutes'` (deduped vs the 15
      council-embedded RDA dates + 2 no-vote files). RDA 15→147 motions (132 recovered, 2018-2024);
      validate_city 25 PASS / 0 FAIL; backups in `_backups/2026-07-10-vineyard-rda/`. **[DONE
      2026-07-19]** The 28 oversize-deferred RDA docs (actually 13–101 MB — embedded exhibits;
      minutes pages are born-digital text, no OCR) were re-fetched uncapped from PMN (all 28 still
      live, no purge): **20 verified net-new standalone RDA-board minutes promoted**
      (`provenance='pmn_minutes'`; 2021-01-13 … 2024-06-26) + **8 duplicate-not-promoted** (7 dates
      already audited-primary, 1 already recovered from another fileId). RDA 47→67 dates, 147→218
      motions (+71), 706→1058 member rows (+352); additions-only proven; validate_city 25 PASS / 1
      WARN (documented provenance col) / 0 FAIL; per-doc ledger `pmn_backfill/oversize_rda_ledger.csv`;
      backups `_backups/2026-07-19-pv-tierb-low/vineyard-rda/`. (b) **✅ Ord 2021-12 — RESOLVED
      2026-07-20** (2026-07-19-pv-tierb-low package). Diagnosis: the vote was **never missing** from
      `all_votes.csv` — it is 2021-09-08 #4 ("APPROVE ORDINANCE 2021-02", Carried unanimously:
      Fullmer/Earnest/Flake/Judd/Welsh all Aye). The 2021-09-08 council minutes DO record the adopting
      motion at business item **9.3**, whose agenda header reads "(Ordinance 2021-12)" (Chapter 2.30
      Commissions), corroborated by the signed PMN PDF "PASSED AND ADOPTED … SEPTEMBER 08, 2021". The
      clerk simply **mistyped the number** in the motion sentence as "2021-02". So this was NOT an
      extraction miss / grammar gap — the extractor was faithful (the verbatim motion text is retained
      untouched, cardinal rule 2). The failure was in the DERIVED `ordinances/index.csv` linkage: the
      typo made 2021-12 score `none` ("audit signal") AND falsely attached 2021-09-08 #4 to the real,
      distinct Ord 2021-02 (2021-02-10 item 9.1, ZTA 15.34.100 Parking). Fix: a documented
      `MOTION_ORD_OVERRIDE` in `ordinances/build_index.py` re-keys that one motion event to 2021-12 for
      **linkage only**. Result: 2021-12 → `high` matched to 2021-09-08 #4; 2021-02 → its correct sole
      match 2021-02-10 #4; `none`-tier count 1→0 (audit signal cleared). Isolated diff = exactly those
      2 rows; full index diff vs backup = those 2 + a pre-existing stale 2022-14 n_events 2→3 drift
      (from the recent RDA-layer growth adding an RDA-body "APPROVE ORDINANCE 2022-14" row — matched
      motion unchanged, harmless). No votes changed → no db/weeks rebuild; validate_city 25 PASS / 1
      WARN / 0 FAIL. Docs: ordinances/CLAUDE.md + AVAILABILITY.md updated; backups
      `_backups/2026-07-19-pv-tierb-low/p4-vineyard/ordinances/`. (Note: `ordinances/index.csv` change
      reaches cities.db `ordinance` table only on the next authorized `build_cities_db.py` run.)
      (c) **2023 campaign-finance cycle** unrecoverable
      (purged in CMS migration; Wayback caught only 404s) — re-fetch if the city ever re-posts; election
      winners are known. (d) 2025 general-election candidates filed no finance statements (city gap).
- [ ] **Logan expansion follow-ups (2026-07-05):** (a) **2023 campaign-finance cycle** (21 filings)
      provably unrecoverable online — Wayback captured only 302→CDN redirects whose targets 404;
      raw-PDF backfill if the city re-posts. (b) **3 adopted land-use ordinances missing from
      `all_votes.csv`** — Ord 22-13 (LDC Amendment), 23-15 (Tempki Subdivision Easement), 26-12
      (Data-Center Moratorium) — vote-extraction leads. **✅ (b) RESOLVED 2026-07-20**
      (`_backups/2026-07-19-pv-tierb-low/p4-logan/`). Per-ordinance verdicts:
      • **23-15 — GENUINE extractor miss → FIXED.** Adopting motion at 2023-05-02 (folder
        2023-05-01) reads `ACTION. Councilmember Simmonds seconded by Councilmember M. Anderson to
        adopt Ordinance 23-15 as presented. Motion carried by roll call vote.` (5 named Ayes) — the
        clerk dropped the leading "Motion by", so the `ANCHOR` ("Motion by") never fired. Added
        `ANCHOR3` to `meeting_minutes/extract_votes.py` (the `ACTION.`-led dropped-"Motion by" form,
        + a mover/seconder fallback). Recovered as **2023-05-02 m5, 5-0 Pass** (Simmonds / M.
        Anderson). The same corpus-wide grammar gap also recovered **4 more** genuinely-missed 5-0
        motions: 2023-05-02 m6 Res 23-13, and 2025-04-01 m4/m5/m6 Res 25-11/25-12/25-13. **+5 council
        motions (748→753), +25 rows (2,791→2,816).** Diff proof: 0 pre-existing
        `(source,date,body,motion_no,member,vote)` rows changed (recoveries append after existing
        motion_nos); the 2025-12-02 word-scramble form is deliberately excluded (see below).
      • **22-13 — NOT actually missing (false lead).** The vote is already in `all_votes.csv` at
        **2022-06-21 m7 "approve Resolution 22-13 as presented" 5-0 Pass (Land-Use/Zoning).** The
        minutes header is "Ordinance 22-13 – LDC Ch 17.53 Annexations" but the clerk wrote
        *Resolution* 22-13 in the motion sentence (city-faithful/verbatim — NOT overwritten, rule 2).
        The `ordinances/index.csv` false-negative (`audit_flag=adopted_no_vote_row`) is a linkage
        artifact: the number↔motion matcher keyed the "Resolution 22-13" string to the Fireworks
        **Resolution** 22-13 row and left **Ordinance** 22-13 unmatched. No extractor change; no
        synthesis. (The stale `none` flag for Ord 22-13/23-15 will clear on the next `ordinances/`
        rebuild — out of this task's rebuild scope.)
      • **26-12 — adopting meeting POSTDATES the repo minutes ceiling (honest gap, not synthesized).**
        Last in-repo council minutes = **2026-06-02**; the recorder "ordinance" PDF is in fact the
        **PMN special-meeting NOTICE posted 2026-07-01** (a temporary land-use regulation under UC
        10-20-504, which needs no PC recommendation). In-repo minutes carry only public COMMENT about
        data centers (2026-05-19, 2026-06-02), no adopting motion. Will be captured on the next
        `fetch_new.py` refresh.
      • **Newly surfaced (out of scope — separate extractor lead):** 2025-12-02 **Ord 25-21** adopting
        motion is a DIFFERENT defect — word-scrambled `ACTION. Motion Councilmember A. Anderson by
        Vice Chair Johnson seconded by to adopt Ordinance 25-21 … (4-0)` — still missing from
        `all_votes.csv`; `ANCHOR3` intentionally does not catch it (starts with "Motion").
        **✅ RESOLVED 2026-07-20** (`_backups/2026-07-19-pv-tierb-low/p4-logan2/`). Added a narrow
        **`ANCHOR4`** to `meeting_minutes/extract_votes.py`: `ACTION. Motion` that is NOT the normal
        `Motion by`/`Motion made by` opener (so it can't double-fire with `ANCHOR`) yet carries a
        `seconded by` clause on the same line. Corpus-wide it matches **exactly this one** motion
        (verified — no other genuinely-missed motions). Recovered as **2025-12-02 m4, Ordinance,
        4-0 Pass** (A. Anderson / Johnson / López / Simmonds all Aye — the printed `(4-0)` roll,
        `VACANT` correctly ignored). **ATTRIBUTION left BLANK (not guessed):** the scramble makes
        mover/seconder genuinely ambiguous — the position heuristic (mover listed first) points to
        mover A. Anderson, but the surviving preposition `…by Vice Chair Johnson` points to mover
        Johnson; the two readings conflict, so per the never-fabricate rule the existing
        mover/seconder resolvers correctly find no confident `by <mover> seconded by <seconder>`
        span and both fields stay empty. **+1 council motion (753→754), +4 rows (2,816→2,820).**
        Proofs: `comm -23` on sorted `all_votes.csv` pre/post — every changed line is dated
        2025-12-02 (0 other-meeting rows moved); within the meeting the only deltas are the 4 new
        Ord 25-21 rows plus the pure mechanical `motion_no` renumber of 25-22 (m4→m5) and 25-47
        (m5→m6), content otherwise byte-identical. Extractor idempotent (re-run → byte-identical
        CSV). Rebuilt db/build_db.py (motion 1340→1341, INTEGRITY OK) + build_referrals (0 links,
        OK) + build_weeks (149 bundles) + `normalize_motions.py logan` (789 mm motions, 100%
        outcome-coverage); validate_city.py logan_city_council/ **26 PASS / 0 WARN / 0 FAIL**.
      Rebuilt db/build_db.py + build_referrals (INTEGRITY OK), build_weeks, normalize_motions.py
      logan; validate_city.py logan_city_council/ **26 PASS / 0 WARN / 0 FAIL**. (c) 2021 Council winner **Ernesto López**
      published no campaign-finance statement (city gap; watch for republication).
- [ ] **Orem expansion follow-ups (2026-07-05):** (a) **Drive-archive packet backfill** — pre-CivicClerk
      2020–2021H1 agenda packets live only in Orem's Google Drive (folders `Agendas`=
      `1bYGd-3jyVsNPFpQfbQeipHqr8xzWcivm`, `Agendas-City Council`=`1jCLlNKyu1yGkYyefk0YM6cPG3_d90unz`);
      children load via authenticated `batchexecute` POST, so GET-only couldn't enumerate — needs a
      Drive API pass. (b) **[PARTIAL 2026-07-10] Promote recovered RDA + MBA minutes** —
      `meeting_minutes/extract_backfill_votes.py` reuses `extract_file` (forcing body from the pmn index,
      since standalone RDA/MBA files carry no in-council body marker) and merged the **5 parseable
      (chars>0) net-new RDA meetings** (RDA 15→30 motions, 2020–2026, provenance='pmn_minutes'); validate
      25 PASS / 0 FAIL; backups `_backups/2026-07-10-orem-rda/`. **✅ (i) OCR PASS DONE 2026-07-19**
      (`_backups/2026-07-19-pv-tierb-low/orem-ocr/`): tesseract 300 DPI over the 12 image-only `chars=0`
      scans (10 RDA/MBA + 2 council packets). In-body verified body+date on every doc (PMN labels lie):
      **corrected the `2026-06-10` MBA mislabel** — file 1454771 is the APPROVED scan of the **2025-06-10**
      MBA meeting (header/footer say June 10 2025, approved 2026-06-26, same notice 1003075 as the draft
      docx), folded as a duplicate of the 2025-06-10 row (`pmn_exceptions.csv` wrong_date). Promoted **7
      net-new RDA/MBA meetings / 17 motions** via `extract_backfill_votes.py` (RDA 2020-05-12, 2023-05-09,
      2023-06-13; MBA 2022-06-14, 2023-05-09, 2023-06-13, 2024-06-18) — all unanimous; total pmn_minutes
      RDA/MBA now 11 mtgs / 29 motions. RDA 2024-03-12 & 2024-05-14 (born-digital docx twin) were already
      audited council-embedded → auto-deduped, text retained for search only. Recovering 4 motions needed a
      **scoped OCR/phrasing tolerance** (`ev.extract_file(..., lenient=True)` — RDA/MBA `<Body> Minutes-date`
      footers injected mid name-list; "The vote was unanimous, motion passed"; "The motion <noise> passed");
      the default audited council pipeline is **byte-identical, diff-proven** (4037 rows unchanged). Validator
      25 PASS / 1 WARN (documented `provenance` col) / 0 FAIL; db reconciles +0; tally 637/637. The 2 council
      packet scans (2026-05-12/-05-26, header dates confirmed) are text-retained only, **NOT promoted**
      (council audited-layer backfill is out of this RDA/MBA scope). **STILL DEFERRED:** (ii) **3 Board
      of Adjustment (BoA) minutes** (OWNER-GATED) — text already present (2 born-digital docx + 1 born-digital
      pdf, all `chars>0`, no OCR needed); BoA is a body the schema/crosswalks/`kind_of` don't model yet; adding
      it needs body plumbing (body_crosswalk + normalize BODY_CROSSWALK + kind mapping) — do NOT ingest until
      owner-scoped. (c) **Orem 2019 + 2021 candidate campaign-finance filings** are a confirmed online gap
      (paper-only at the city recorder; not on orem.gov, Wayback, EasyVote, or state). (d) Re-crawl
      orem.gov WP ordinance posts (`O-YYYY-NNNN`) each refresh + upgrade `within_source` ordinance rows
      toward `medium` if PMN "Notice of Ordinance" docs surface as an independent corroborator.
- [ ] **Ogden campaign-finance follow-ups (2026-07-05):** (a) **2025 cycle not yet
      published** — `ogden_city_council/campaign_finance/` covers 2019/2021/2023 (38 filings,
      all 12 winners + 20/20 general candidates); the city had posted **no 2025 candidate
      financial reports** as of 2026-07-05 (no `2025-Elections` page exists; verified vs site
      nav, sitemap, the `/2971` sidebar, Wayback CDX, state site, EasyVote). Re-fetch once the
      city posts the 2025 cycle (winners Flor Lopez D1, Ken R. Richey D3, Alicia Washington
      At-Large A, Kevin Lundell At-Large B). (b) **Primary-eliminated filers flag** — 18 of 38
      filings are real primary candidates absent from `election_results` (general-only); Ogden
      ran primaries 2019/2021/2023 — a future `election_results` review lead (do not edit from
      the finance dataset). (c) **2013 & 2015 combined reports live but out of scope** (View
      17166–17171, 17369–17371) — available for a pre-2019 backfill if ever wanted.
- [ ] **Alta expansion follow-ups (2026-07-13).** Six-source run complete (all PASS; parent
      docs + sources.csv regenerated — 1,215 docs). A ~380-pop town that ran RICHER than recon
      predicted. Open items:
      (a) **✅ DONE 2026-07-16 (4/5 promoted; the 2023-11-28 PC DRAFT rejected on pdfinfo evidence — new honest unrecovered row; +4 contested incl. R-10 resort-tax FAILED 1-2; 2 audited-extractor defects fixed zero-regression). Was: [high] Promote `pmn_backfill/` (5 minutes)** — 3 council (2020-05-06, 2020-06-17
      born-digital; 2024-08-14 OCR, was misfiled under the PC body) + 2 PC (2023-11-28 draft,
      2024-04-24) — all label-mislabeled or cross-body-misfiled, invisible to the original
      label-based harvest. Re-extract votes, rebuild derived.
      (b) **[high] Election-record: the 2025 general is entirely absent from
      `election_results/alta_races.csv`** but fully documented in campaign_finance — re-pull the
      raw 2025 SLCo SOVC (exclude ALTA CANYON decoys) and add the race: Bourke re-elected Mayor,
      Anctil + Heimark to Council, Byrne + Moxley withdrew. (Also strengthens roster_HARDENING
      H-C/H-E canceled/absent-race exceptions.)
      (c) **[med] cf-vision-transcribe** the 36 CF filings (29 scanned) — small but complete
      2021/2023/2025; the 2025 $2,000 PAC contribution to the mayor is a notable data point.
      (d) **[low] Whisper leads**: 348 SoundCloud audio tracks back to 2013 + 172 captioned
      YouTube videos map in transcripts/; contested-motion Whisper candidates proposed.
      (e) **[low] Ordinance gaps**: pre-2021 ordinances (2020-O-1..O-3) unlocated; 4 `none`
      linkages. Note the digit-zero series form (`2024-0-4`) for any future extractor work.
- [ ] **Emigration Canyon expansion follow-ups (2026-07-14).** Six-source run complete (all PASS;
      parent CLAUDE + sources.csv regenerated — 899 docs). Open items:
      (a) **[med] Election-record: the finance record PROVES a 2019 council cycle existed**
      (Hawkes/Brems/Tippetts/Harris filed) — recon §6 + election_results say "no 2019 contest."
      Re-parse the raw 2019 SLCo SOVC. Roster fix: **Griffith was appointed, not elected**
      (not among the certified 2025 candidates).
      (b) **[med] cf-vision-transcribe** the 35 CF filings (29 scanned) + Whisper the 211 live
      PMN MP3s (audio is the only verbatim record; highest-value the 8 contested motions).
      (c) **✅ DONE 2026-07-16 (+2 tally-only motions, unrecovered 74→73; surfaced the corpus-wide '2nd by:' seconder miss — see wave section). Was: [low] Promote pmn_backfill (1 doc)**: the late-posted PC 2025-11-13 minutes (fills a
      PC unrecovered row). The 2 OCR-0-motion council scans (2024-02-22, 2025-01-28) have no
      born-digital twin anywhere — permanent OCR-only limit.
      (d) **[low, GENUINE GAP] 2017 (+scattered pre-2018-10) minutes/audio/packets purged** —
      re-confirmed 404; the MSD AgendaCenter is NOT a recovery avenue (it hosts the MSD Board of
      Trustees, not EC's own bodies — correct the recon's "secondary mirror" claim).
      (e) **[low] Build out the empty core scaffolds** — elections/geo/public_comments/db were
      never built for EC (the core CLAUDE notes this); the expansion layers are complete but the
      base repo is thinner than the other 13. A future core-completion pass.
- [ ] **Copperton expansion follow-ups (2026-07-14).** Six-source run complete (all PASS; parent
      docs + sources.csv regenerated — 746 docs). Open items:
      (a) **[low] pmn_backfill = complete superset (0 recoveries)** — the one lead is an
      OCR-upgrade: 2025-10-15 born-digital council draft (PMN 1353103) vs the repo's RICOH scan
      (cataloged, not swapped — it's the draft; approved stays the scan).
      (b) **[low, GENUINE GAP] 2017-02→2018-06 (29 mtgs) purged** (re-confirmed 404); the audio
      purge extends later (2018-07→11 have minutes but no audio).
      (c) **[med] cf-vision-transcribe** the 19 township CF filings (all scanned). Election flag:
      finance confirms the archive-missing **2019 A/B/C council cycle** existed (Bailey/Stitzer/
      Clayton filed) — re-parse raw 2019 SOVC. ~~Roster fix: Pratt was APPOINTED not elected~~ **REFUTED 2026-07-19 (H-C verification): Pratt was ELECTED UNOPPOSED** (2025-10-15 minutes: "Council Member Elect" after the cancelled unopposed election; the old claim over-inferred from a June certified-list snapshot; open owner Q on seat LETTERING — LM-wave lead (l)). *(original)*: **Pratt was APPOINTED not elected**
      (2025 Seat C had no declarations) — correct roster/CLAUDE framing.
      (d) **[low] Ordinance gaps**: the R2025-01…08 town-era resolution run not yet on
      MunicipalCodeOnline (codification lag) — re-probe. SKILL note: MCO buckets can scatter
      instruments across 7+ subprefixes (not just ordinances/+resolutions/) — list the whole
      `<city>/` prefix and key the index by URL, not filename.
- [ ] **Magna expansion follow-ups (2026-07-13).** Six-source run complete (all PASS; parent
      docs + sources.csv regenerated — 1,335 docs). Open items:
      (a) **✅ DONE 2026-07-16 (12/13; 2025-11-18 CRA DRAFT rejected — re-check PMN for approved copy; CRA 13→32 motions; +1 audited fix: 'passed BY A unanimous vote' grammar; referrals 1→3). Was: [med] Promote `pmn_backfill/` (13 docs)** — 5 missing council minutes + 8 CRA minutes
      (body 6925, more than triples the in-record CRA — the core had 5 CRA dates). Merge into
      meeting_minutes/ (body=CRA + Council), re-extract, rebuild derived.
      (b) **[med] cf-vision-transcribe** the 63 CF filings (56 scanned) + a Whisper pass on the
      370 live PMN MP3s (Magna's HIGHEST-value Whisper target repo-wide — no video transcript in
      any era; township narrative-tally minutes leave the majority unnamed).
      (c) **[med] Election double-gap: 2023 D1/D3/D5 missing from BOTH finance (EasyVote-blocked)
      AND `magna_races.csv`** — re-parse the raw 2023 SLCo SOVC (exclude Magna Water District
      decoys). Also the known 2016/2019 D1/D3/D5 gap.
      (d) **[low, GENUINE GAP] 2017-mid-2018 minutes/audio/packets purged** (blob purge, verified
      404 + no Wayback) — same as white_city/kearns.
      (e) **[low] SKILL BUG surfaced**: `polite_fetch.py --batch` mangles comma-bearing filenames
      (CSV quoting reaches disk → dodges the .pdf filter → silent drop; magna ordinances lost 2
      land-use ords until caught). Fix the fetcher to strip surrounding quotes / use proper CSV.
- [ ] **Kearns expansion follow-ups (2026-07-13).** Six-source run complete (all PASS; parent
      docs + sources.csv regenerated — 800 docs). Open items:
      (a) **✅ DONE 2026-07-16 (3/3; CRA body 0→9 motions; PC 2019-04-08 promoted + FALSE unrecovered row removed 24→23; +3 Council←CRA referrals; 11/11 ground-truthed). Was: [med] Promote `pmn_backfill/` (3 docs) — lights up the empty CRA body**: 2 CRA
      minutes (2025-07-14 + 2025-09-08, body 9273) into a new `body=CRA` layer + the bonus PC
      2019-04-08 (reconcile: it's currently a FALSE row in PC `minutes_unrecovered.csv` — remove
      it). Build CRA/PC vote extraction.
      (b) **[med] cf-vision-transcribe** the 38 township CF filings (all scanned); + a Whisper
      pass on the 218 live PMN MP3s (township 2019–2025 highest-value — narrative-tally minutes
      leave the majority unnamed, so audio is the only who-said-what record).
      (c) **[low, GENUINE GAP] 2017-01→2018-06 township minutes + audio (25 meetings) + 41
      pre-2018 PC packets are PMN blob-purged** (all objects 404, zero Wayback) — same purge as
      white_city 2017 / magna / copperton. Unrecoverable unless the city/MSD holds offline copies.
      (d) **[low] Blocked CF cycles**: 2023 (SLCo EasyVote SPA, auth-gated) + 2025 city-era (only
      on the Cloudflare-blocked city site — 11 filings PROVEN to exist via Wayback). Re-attempt
      if EasyVote exposes a GET path or the city site drops Cloudflare.
      (e) **[low] Ordinance re-harvest**: 26 minute-cited 2025-26 instruments not yet on
      MunicipalCodeOnline (post-cityhood codification lag) — re-probe as the code rewrite lands.
- [ ] **White City expansion follow-ups (2026-07-13).** Six-source run complete (all PASS; parent
      docs + sources.csv regenerated — 434 docs). Open items:
      (a) **✅ DONE 2026-07-16 (PC layer BUILT: 22 minutes / 106 motions, new extractor for the MSD Meeting-Minute-Summary form, 8-doc ground-truth + corpus-wide Vote:-line reconciliation; 5 council promoted +13 motions; 2017 purge gap absorbed into unrecovered ledger). Was: [HIGH] BUILD OUT the empty `planning_commission/` layer** — pmn_backfill found a
      previously-unknown PMN PC body **5879** with **22 net-new PC minutes (2019→2025)** (real
      motion grammar) + `packets/` has 7 PC packets. The core PC dataset is header-only and now
      KNOWN-INCOMPLETE. Promote the 22 recovered minutes into `planning_commission/`, build a PC
      extractor, rebuild derived, update CLAUDE.md ("PC honestly empty" → "PC recovered from PMN
      5879"). Also promote the 5 recovered council minutes (2019-11-14, 2022-03-03/08-18,
      2023-10-05/11-02).
      (b) **[low, GENUINE GAP] 2017 council year (18 meetings) lost to the pre-~2019 PMN blob
      purge** — notices prove the meetings but the minutes 404. Same purge as kearns/magna/
      copperton. Unrecoverable unless the city/MSD holds offline copies (GRAMA lead only).
      (c) **[med] cf-vision-transcribe** the 2025 CF (18 reports, 15 scanned) + Whisper the 13
      MP3s (esp. 2025 narrative-tally meetings where audio is the only who-said-what record).
      (d) **[low] Ordinance gaps**: ~68 minute-cited numbers not yet on MunicipalCodeOnline
      (mostly the not-yet-codified 2026 run — re-probe as the post-HB35 code rewrite completes).
      NOTE for the 4 remaining township cities: MunicipalCodeOnline S3 (ordinances), MSD-hosted
      housing plans, Streamline-only CF, and the pre-2019 PMN purge all recur — carry forward.
- [ ] **South Salt Lake expansion follow-ups (2026-07-13).** Six-source run complete (all PASS;
      parent docs + sources.csv regenerated — 1,103 docs). Open items:
      (a) **✅ DONE 2026-07-16 (119/130 promoted — C75/RDA29/PC15; 11 rejected for cause; motions 142→680 mm + 230→286 PC; contested 12→68; referrals 0→43; COVERAGE.md rewritten, residual = 214 dates; ~45 portal-label lies documented; provenance='agendacenter_minutes'). Was: [HIGH — biggest recovery of the wave] Promote `pmn_backfill/` (130 recorded minutes)
      + REWRITE COVERAGE.md.** The core "coverage cliff" narrative is substantially wrong: the
      core content-detected minutes on PMN ONLY, but the CivicPlus AgendaCenter hides recorded
      roll-call minutes in an `ArchivedMinutes` slot (via each Minutes doc's PreviousVersions
      page). 130 recorded minutes 2022–2026 recovered (Council 79 / RDA 30 / PC 21), incl. 9 that
      REFUTE "PC minutes begin 2023-01-19; 2020–2022 never published." Promote into
      meeting_minutes/ + planning_commission/, re-extract votes, rebuild derived, then REWRITE
      COVERAGE.md + the CLAUDE.md coverage-cliff section (residual is now 216 agenda-only dates,
      not 253+). This lights up the currently-thin 2022–2025 council vote layer + the empty
      referral layer. Cross-source lesson for the PMN-crosscheck TODO: for CivicPlus "minutes =
      packet" cities, the AgendaCenter ArchivedMinutes/PreviousVersions slot is a first-class
      recovery source alongside PMN.
      (b) **[med] Election-record: filings prove a 3-way 2021 mayoral primary** (Wood/Christensen/
      Siwik) absent from `election_results` — re-parse the raw 2021 SLCo primary SOVC. Also the
      known missing 2011/2019 SSL rows (state folders empty/redirect to a dead legacy site;
      Wayback recovery is future work).
      (c) **[med] cf-vision-transcribe** the 68 CF filings (54 scanned) + run cycle_totals.
      (d) **[med] Whisper the cliff-year videos** — 160 caption-bearing 2023–25 Council+PC videos
      already have ASR (transcripts/); Whisper only for higher name/number accuracy where the
      caption is the sole record.
      (e) **[low] Packets** — 429 index-only (3.37 GB); fetch specific ones on demand via
      `?packet=true`.
- [ ] **Holladay expansion follow-ups (2026-07-13).** Six-source run complete (all PASS; parent
      docs + sources.csv regenerated — 570 docs). Open items:
      (a) **✅ DONE 2026-07-16 (27/27; +165 PC motions / +15 contested; referrals 4→5; provenance='wayback_minutes'; 'Howard Lloyd' clerk conflation kept verbatim; NOTE the 35 residual gaps are 2020 H2 ×7 + 2021 H2 ×9 + 2023 ×19, not 'all 2023'). Was: [high] Promote `pmn_backfill/` (27 recovered PC minutes)** — all 2020 H1 + 2021 H1,
      recovered from the former cityofholladay.com WordPress site via Wayback (PMN/SuiteOne/Revize
      lack them). This DIRECTLY fills the documented PC PMN gap the core CLAUDE.md flagged
      (no 2020/2021/2023 PC minutes). Merge into planning_commission/, re-extract, rebuild derived;
      update the gap note. 35 still-missing stay honest (all 2023 unrecoverable anywhere).
      (b) **[med] cf-vision-transcribe** the 40 CF filings (39 scanned) — complete 2021/2023/2025.
      (c) **[med] Whisper the SuiteOne 2025-2026 meeting videos** (75, caption-less — the ONLY
      video record of the current era; 68 Council+PC). transcripts/ has the MP4 map.
      (d) **[low] Ordinance corroboration**: 102 within_source rows (motion-attested only — no
      independent PDF online for 2020–2024; American Legal bot-gated). Signed PDFs would upgrade
      them if the city ever posts a back-catalog. 2 medium rows carry documented clerk misprints.
      (e) **[low] Election leads (already known)**: 2019 general gap (D2/D4/D5) — re-parse raw
      2019 SOVC; CF corroborates the 2025 3-way mayoral primary (Wilson).
- [ ] **Cottonwood Heights expansion follow-ups (2026-07-13).** Six-source run complete (all
      PASS; parent docs + sources.csv regenerated — 1,051 docs). Open items:
      (a) **✅ DONE 2026-07-16 (16/16; the 15 admin hearings are genuine 0-motion officer-decision minutes; 2022-07-06 is a TWO-meeting combined PDF, +6 motions; 2023-03-01 clerk header-year typo retained verbatim). Was: [med] Promote `pmn_backfill/` (16 docs)** — 15 Administrative Hearings sessions
      2020–2023 (the PC dataset carries admin-hearing rows but only 2024+) + 1 PC work meeting
      (2022-07-06). Merge into the PC layer, re-extract, rebuild derived.
      (b) **[med] Election-record: filings prove a 2019 D1 primary** (Petersen, Case, McHugh)
      that `election_results/CLAUDE.md` explicitly says didn't happen, and McHugh is absent from
      `races.csv` — re-parse the raw 2019 SLCo primary SOVC (mirrors CH's already-documented
      2019 general recovery). Also confirm the 2023 D2 3rd primary candidate (Bracken).
      (c) **[med] cf-vision-transcribe** the 86 CF filings (55 scanned) — complete 2021/2023/2025.
      (d) **[low] NEW BODY — Architectural Review Commission (PMN body 2150, 13 in-window
      minutes 2020+)**: a live design-review land-use body the repo doesn't model at all;
      consider a dedicated dataset (also Appeals Hearing Officer 7091, 9 in-window dates).
      (e) **[low] Full transcript harvest** — 511 videos mapped, ASR on all (transcripts/).
      (f) **[low] Ordinance gaps**: Ord 392/455/456/457 (no citation, no PDF); Ord 304 pre-floor.
- [ ] **Midvale expansion follow-ups (2026-07-13).** Six-source run complete (all PASS; parent
      docs consolidated + sources.csv regenerated — 1,013 docs). Open items:
      (a) **✅ DONE 2026-07-16 (24/25; 1 genuine zero-motion retreat; RDA 35→84 motions + first MBA body; a PMN label lie date-corrected via DATE_OVERRIDES; +179 motions purely additive; referrals 102→114). Was: [high] Promote `pmn_backfill/` (14 dates / 25 docs)** — a REAL coverage hole in the
      audited layer, incl. a whole 2024 council cluster (Feb/May/Aug) + recurring 3rd-Tuesday
      January meetings + in-session RDA/MBA companions. Convert→extract votes→rebuild derived.
      Highest-value promotion in the wave so far (the city's own Revize portal had genuine gaps).
      (b) **[med] cf-vision-transcribe** the 84 CF filings (57 scanned) — deep 2017–2025 coverage.
      (c) **[med] Load ordinances `fts_ordinance`** on the next federated rebuild (263 rows /
      182 land-use, 107 high-linkage — a strong money-and-land-use layer).
      (d) **[low] Full transcript harvest** — 258 videos mapped, ASR on all; iterate yt-dlp
      `player_client` for the ~3 android_vr false-negatives.
      (e) **[low] Ordinance gaps**: 2 adopted-but-no-PDF (2023-O-12/O-13, within_source); 106
      year-only-dated rows (pre-2020 + blank-day templates); 25 consent-agenda `none` links.
      NOTE: two Midvale agents (pmn_backfill, ordinances) appended their own parent-doc sections
      mid-run despite the orchestrator-owns-parent-docs convention — consolidated into one
      Expansion block at closeout; reinforce the convention in future prompts (done from
      cottonwood_heights on).
- [ ] **Riverton expansion follow-ups (2026-07-13).** Six-source run complete (all PASS;
      parent docs + sources.csv regenerated — 3,497 docs). Open items:
      (a) **✅ DONE 2026-07-16 (7 promoted — the '4 early-2020 Word docs' claim was stale, there are 3; +44 motions / +4 contested; textutil conversion proven byte-identical; PC ceiling honored; fetch_new now chains the backfill merge). Was: [high] Promote `pmn_backfill/` (7 meetings)** — the 3 Granicus-only 2023 meetings
      (council 2023-09-05, 2023-11-07; PC 2023-11-09 — PMN never carried their minutes) + 4
      early-2020 council (Word-format `.doc/.docx`, before the audited series starts) + PC
      2026-06-25. Re-extract votes, rebuild derived.
      (b) **[med] cf-vision-transcribe** the 60 CF filings (30 scanned) — complete 2021/2023/2025.
      (c) **[low] Whisper**: 652 Granicus clips catalogued (transcripts/granicus_clips.csv);
      the 2025-12-16 mayoral tie-break meeting is the top candidate; whole in-scope window is
      caption-less (Utah Record mirror doesn't carry Riverton).
      (d) **[low] Ordinance linkage**: 93 within_source rows (2020–2022, before Riverton's PMN
      Notice-of-Adoption practice began in 2023) will stay uncorroborated unless signed PDFs
      surface elsewhere; the 4 `none` rode consent agendas.
      (e) **[low] Packets**: 301 oversize exhibits re-fetchable (dropped_oversize.csv); 83
      legistarweb 2020 exhibits are permanently 403 (content survives in stored agenda outlines).
- [ ] **Draper expansion follow-ups (2026-07-13).** Six-source run complete (all PASS;
      parent docs + sources.csv regenerated — 5,463 docs). Open items:
      (a) **✅ DONE 2026-07-16 (6/6; ords #1494/#1496/#1497 none→HIGH; 2024-03-14 stale row removed; 2023-10-15 proven a phantom (a Sunday) + fetch_new guard added; PC contested 206→214). Was: [high] Promote `pmn_backfill/` (6 meetings)** — 2021-07-20 council (heals the
      broken-stub gap AND resolves ordinances #1494/#1496/#1497 linkage), PC 2020-12-10 +
      2024-10-10 stubs, 3 August TnT specials (2022-08-24, 2024-08-14, 2025-08-13). With the
      promotion: fix the STALE PC minutes_unrecovered row (2024-03-14 — doc IS in the index)
      and review the phantom 2023-10-15 Granicus row (no such meeting doc anywhere; both
      sources hold 10-17).
      (b) **[med] cf-vision-transcribe the CF layer** — 125 filings, 116 scanned; Tyler
      EagleWeb copies are the cleanest set. 2011–2025 depth = good money-vs-votes runway.
      (c) **[med] Election-record notes**: 2019 primary scheduled-then-not-held (settles the
      recon caveat — record in election_results notes on next elections pass, not from CF);
      2025 canceled 4-yr race CF-corroborated (Green/Lowery filings + Turner withdrawal
      affidavit — strengthens the existing H-C/H-E TODO item on canceled-uncontested races).
      (d) **[low] Whisper candidates** (proposed only): 2024-10-15 tie-break meeting (clip
      1786), 2026-07-07 recap-only meeting (clip 2117), top v_contested PC dates — direct
      MP4 URLs in transcripts/granicus_clips.csv. 2020–25 is video-complete, caption-less.
      (e) **[low] Packet leads**: 373 oversize exhibits fetchable by URL
      (dropped_oversize.csv); 7 dead Legistar exhibit URLs; 2024-07-16 CRA has no packet at
      all; HPC/Tree/Arena packets exist on-portal but out of scope.
- [ ] **Herriman expansion follow-ups (2026-07-13).** Six-source run complete (all PASS;
      parent docs corrected + sources.csv regenerated). TWO REPO-CLAIM CORRECTIONS landed in
      README/CLAUDE: (i) the 2020 "COVID cancellations" were only half right — 9 proven
      cancellations + **12 real meetings recovered** into `pmn_backfill/`; (ii) **2024+
      standalone CDRA/HCSEA/HCFSA minutes are absent from the combined council docs** — all
      30 recovered. Open items:
      (a) **✅ DONE 2026-07-16 (66 promoted + 4 rejected for cause; agencies lit up CDRA 16→64 / HCSEA 4→39 / HCFSA 9→31; contested 48→54 C + 43→51 PC; referrals 39→51; ords 2021-17..21 all HIGH-linked to 2021-08-11 after the 2021-10-13 embedded-minutes wrong-doc repair; first Recuse row). Was: [high] Promote `pmn_backfill/` (70 docs)** into the audited layers — 20 council
      (full named roll calls!), 13 PC, 5 joint, 30 agency, 2 appeals — re-extract votes,
      rebuild derived; expect new 2020 + 2022 + 2024+ agency motions. The 2021-17/18/20
      ordinance noticed-vs-voted ambiguity resolves with the 2021-08-11 minutes.
      (b) **[med] Election-record lead: 2021 mayoral PRIMARY existed** (4 candidates' primary
      reports + posted sample ballot; Esselman + Grange eliminated) — absent from
      `election_results/` AND the county SOVC dataset. Review the 2021 SLCo primary SOVC.
      (c) **[med] Structure the CF dollar layer** (50 filings acquisition-only; 17 text / 33
      scanned → cf-vision-transcribe).
      (d) **[med] Bulk caption fetch** of the ~51 substantive no-minutes videos (~35 MB;
      map in `transcripts/index.csv`) — subset shrinks once (a) promotes recovered minutes.
      (e) **[low] Mirror the 1.7 GiB 2020 packet set** from the legacy `herriman-agendas`
      S3 bucket if 2020 preservation matters (legacy host, could retire any time; keys in
      `packets/index.csv`).
      (f) **[low] Ordinance leads**: 12 series holes 2020+ witnessed nowhere; 2026-14
      postdates the minutes layer; 10 documented Recorder/minutes typo-overrides in
      `ordinances/build_index.py` (verbatim retained) — spot-audit on next refresh.
- [ ] **Murray expansion follow-ups (2026-07-13).** Six-source `expand-city-sources` run
      complete (all 6 datasets validate PASS; parent docs + sources.csv regenerated). Open items:
      (a) **✅ DONE 2026-07-16 (18 council + 59 PC fully promoted; 2023-07-11 proven CANCELLED; council 657→755 motions incl. an 'All in favor N-0' blind-spot repair in audited 2024/2026 files; PC 378→678 + contested 15→27; ordinance none-links 18→0; validate 26/0/0). Was: [high] Promote `pmn_backfill/` into the audited layers** — the run recovered ALL
      18 missing 2023 council minutes (+ net-new 2023-08-21 joint special; 2023-07-11 proven
      cancelled) and 59 PC minutes 2023–2026 (PC gap closed end-to-end; only 2025-04-17 +
      2025-07-17 remain minute-less). Merge into `meeting_minutes/`/`planning_commission/`,
      drop the satisfied `minutes_unrecovered.csv` rows, re-run vote extraction + validate,
      rebuild derived, refresh the stale gap-framing in README/CLAUDE/VERIFICATION. Method
      precedent: ogden/vineyard/orem/SJ `extract_backfill_votes.py` (or full promotion since
      the docs are born-digital and identity-verified).
      (b) **[med] Bulk caption fetch of the 86 minutes-gap videos** (23× 2023 council, 63×
      2023+ PC; ~50 MB) — every Murray video has ASR captions; `transcripts/` has the map.
      (c) **[med] Election-record lead: 2021 municipal primary existed** (Mayor 4 candidates,
      D4 3) per campaign-finance filings + post-primary "eliminated" finals; `murray_races.csv`
      + docs say no 2021 primary. Review county SOVC/primary canvass; do NOT edit from CF.
      (d) **[med] Structure the campaign_finance dollar layer** (131 filings acquisition-only;
      39 born-digital direct, 92 scanned → cf-vision-transcribe).
      (e) **[low] Ordinance text gaps**: 2020→Apr-2021 adopted-ordinance texts unpublished
      anywhere (54 adopting motions); O22-02 attachment-less, O22-30/O23-14 series holes,
      O26-15 city mis-upload (byte-identical to O26-14) — watch for republication; 17 `none`
      linkages will resolve automatically when (a) promotes the 2023 minutes.
- [ ] **Taylorsville expansion follow-ups (2026-07-06).** Six-source `expand-city-sources`
      run complete (all PASS; `taylorsville_city_council/EXPAND_SOURCES_REPORT.md`). Open items:
      (a) **[high] ✅ DONE 2026-07-12 — PMN born-digital promotion.** All 15 candidates fetched
      (sha256-logged) + indexed in `pmn_backfill/`; per-row outcomes in
      `ocr_upgrade_candidates.csv`: **6 PROMOTED** (council 2024-12-04/2025-01-22/2025-05-07 +
      PC 2021-08-24/2021-09-14/2022-04-26 — born-digital md swapped in with promotion-provenance
      headers, `source=pmn`/`format=pdf-text`, city scans retained, PMN copies added to each
      dataset's raw/), **2 NO-OPs** (2021-06-02, 2022-01-05: PMN's file is the already-text
      council doc; the OCR docs those dates are the separate RDA Board minutes PMN lacks),
      **7 PC DRAFT sidecars** (repo's APPROVED scans stay canonical). Re-extraction diffed clean
      at (date, body, motion_no, member, vote) — one genuine recovery: **2025-01-22 council m5
      regained Cochran's Aye** (full 5-roll). validate PASS ×2; `rebuild_derived.py taylorsville`
      printed "Derived chain rebuilt". Backups `_backups/2026-07-12-t3.3/taylorsville/`. OCR
      residue now 21 council + 28 PC files. **Supersedes the generic "Millcreek + Taylorsville
      PMN born-digital upgrade" item above for the Taylorsville half.** (b) **[med] Consider merging
      the 2 recovered *Let's Talk Taylorsville* town halls** (2020-01-29, 2024-01-31 — real
      council-body meetings, non-standard, no roll-call votes) from `pmn_backfill/`. (c) **[med, MOSTLY DONE 2026-07-12]
      Structure the campaign_finance layer** — the layer EXISTS (`build_finance.py`, family
      `taylorsville_form`): **36 of 71 filings structured, 35/36 both-sides reconcile** after the
      2026-07-12 vision backfill of the 13 flagged filings (11 handwritten-zero annuals + Harker's
      two real $200 expenditures + the Johnson 6712 "4299"→$42.99 digit fix; Barbieri doc10471 =
      duplicate scan of doc10609, flagged in the CF CLAUDE.md). Two-regime split honored (annual
      blank-year rows never enter race totals); `cycle_totals.py` run (Johnson 2021 corrected to
      8,745.05/8,745.12 via the new documented `cycle_overrides.csv` mechanism — balance-chain
      verified). **STILL OPEN:** (i) the other **35 filings have no text sidecar and no vision
      cache** (build prints MISSING-TEXT; mostly 2017–2021 scanned annuals) — vision them for full
      coverage; (ii) replace inferred `date`s with the PDF "Received" stamps; (iii) **re-probe the
      2025 page** for not-yet-posted election-cycle filings (2019 cycle never posted — honest gap). (d) **[med]
      Real transcripts via OpenUtah/Whisper** — audio-only city, PR-only YouTube (1 ASR sample
      only); OpenUtah `taylorsville.openutah.org` (~8 transcribed, robots-limited) or Whisper
      over the city "Audio Recordings" archive (Whisper NOT run). (e) **[low] Packets are
      current-cycle-only** — no historical archive (2020–2026 packets unrecoverable, honest gap);
      Wayback captures of the 3 packet pages are the only, low-yield, partial-recovery lead.
      (f) **[low] Ordinance refresh + pre-2020 back-catalog** — re-crawl PMN body 720
      (`page=400`), diff vs `index.csv`; ~129-doc 2012–2019 back-catalog retrievable if the 2020
      floor is lowered.
- [x] **Structured campaign-finance layer (NEW, planned 2026-07-05) — ✅ BOX CLOSED
      2026-07-20 as SUPERSEDED/EXECUTED: the plan this entry proposed was approved and
      fully built out (29-city structured layer, cf_* tables federated in cities.db,
      vision pipeline, cycle_totals canonical rollup). Retained for the design/history
      record.** *(original)* Source 6 currently
      acquires filings as documents + a filing-level `index.csv`; the dollar amounts/donors/
      expenditures live ONLY as text in `campaign_finance/text/` (no structured table, not in db).
      Plan drafted (Fable agent) for `contributions.csv`/`expenditures.csv`/`filing_totals.csv`
      derived layers + folding into the skill's Source 6 + backfilling built cities. Owner to
      review the plan and decide parser architecture / db integration / prototype-first scope.
      Provo prototype (Phase 0 spec + Phase 1) in progress as of 2026-07-05.
      **Web-research finding (2026-07-05): NO centralized structured municipal campaign-finance
      database exists for Utah cities** — so this derived layer is genuinely novel, not a
      duplication. What's online is only document repositories / link directories:
      - `disclosures.utah.gov/Municipal/<county>_<year>` = the Lt. Governor's "municipal"
        section, but it is a **link directory pointing back OUT to each city's own site**
        (Provo→provo.gov, Orem→orem.org, Lehi→lehi-ut.gov), organized by county; hosts no
        filings/CSV/API. State's structured e-filing DB covers STATE offices only, not council.
      - County clerks post electronic copies (Utah law): Utah County
        (`vote.utahcounty.gov/financial-disclosures` — a Google Sheet roster + links),
        Salt Lake County (`saltlakecounty.gov/clerk/elections/financial-disclosures/`).
      - Third-party aggregators (FollowTheMoney, OpenSecrets) = STATE-level only, no municipal.
      - Even EasyVote (sandy, WJ 2023+) serves only redacted PDF renders publicly, not exports.
      **How the county/state resources ARE useful — for ACQUISITION gap-filling, not structuring:**
      because they aggregate links across cities + years, use them per-city to recover filings a
      city site dropped on CMS migration (esp. the **2019 cycles** absent for provo/sandy/WJ) and
      to cross-check alternate copies. An acquisition aid to fold into Source 6 / refresh-city, NOT
      a shortcut around parsing the PDFs.
- [ ] **[OPTION] Transcript backfill (deferred 2026-07-05).** Provo (740 videos mapped, 10 captions),
      West Jordan (647 mapped, 10), Orem (111 mapped, 10 captions), Lehi (0 captions — URL map
      only) have large un-fetched ASR caption backlogs. Owner set transcripts to SAMPLE-ONLY
      going forward; revisit full backfill later as its own task. Orem full backfill is pure
      yt-dlp (no Whisper) for the 98 `format=na` rows in `orem_city_council/transcripts/index.csv`;
      Whisper only for the 2020 video gap (Google Drive "Meeting Recordings"), the removed
      2025-04-22 video, and contested meetings with no YouTube video (see Orem AVAILABILITY.md).
- [x] **Lehi transcripts: fetch actual caption files — DONE 2026-07-20 (12/12 resolved:
      2 fetched, 10 ledgered as honest gap).** yt-dlp (2026.06.09) now installed. Recovered
      English auto-captions (`en-orig` VTT) for the two mapped meetings whose videos are still
      public on YouTube — 2026-05-26 City Council (`GMYzejWyA2U`) + 2026-05-28 Planning
      Commission (`ajch_vFR84k`) — stored `transcripts/raw/<date>.en-orig.vtt` + cleaned
      `transcripts/text/<date>.md` sidecars (ASR-header), index rows completed (`format=caption`),
      fetch-log provenance appended. PC row spot-checked against 2026-05-28 minutes/votes (Bishop
      13-lot subdivision @2424 W 900 N, Community Forestry, DADU — all match); council caption
      self-dates to "May 26, 2026" + budget/parks/transit topics match. The other **10 rows (all
      2025 meetings) are a genuine gap** — those videos are no longer public on YouTube (absent
      from both official channels' uploads + the City Council / Planning Commission playlists,
      which reach back only to Dec 2025; no hit on targeted yt-dlp YouTube search) and OpenUtah
      exposes no per-video id (transcript behind robots-disallowed `/api/`) — updated
      `unrecovered.csv` reasons + docs. validate_city.py 26/0/0. NOTE: transcripts feed the
      federated fts/document layers — cities.db rebuild deferred to a later batched run (NOT run
      here per task scope).
- [x] **Quarterly refresh routine — OPERATIONAL; first full run 2026-07-19 (Q3-2026).**
      See the dated **Q3-2026 QUARTERLY REFRESH entry** below for the complete run record
      (23 agents, ~62 docs ingested, all 75 crosscheck flags worked to zero, 7 city-local
      defects found+fixed, the shared refresh_lib dedup bug fixed). Next run: first week
      of October 2026. *(original)* — once fetch_new.py drivers land (plan 3.3): run
      `--probe` per city, then `--fetch` for cities with new meetings, rebuild derived
      layers, re-run validate_city.py, regenerate coverage.json / sources / cities.db.
      Consider a scheduled reminder.
- [x] **Mandatory PMN cross-check in every refresh (owner-approved 2026-07-13) — BUILT,
      ROLLED OUT ALL 31 CITIES, FOLDED INTO /refresh-city, 2026-07-17.** Shared engine
      `scripts/pmn_crosscheck.py` + per-city `pmn_bodies.csv`/`pmn_exceptions.csv` configs;
      steady state 317 verified genuine-lead flags; folded into `/refresh-city` §1b as the
      mandatory post-probe review gate (never auto-ingest). Full record: TODO_ARCHIVE.md.
      (Revisit the 60-day pending-adoption window after 2–3 refresh cycles.)
- [x] **RECOVERY + EXTRACTION + CF WAVE — 2026-07-17 (same-day execution of the
      crosscheck's fetchable-now tier + queued extraction follow-ups + CF vision
      tranche 1; 11 agents, one boundary rebuild + federation).** 48 meeting records
      promoted across 12 cities, 7 leads rejected, extraction fixes + CF vision tranche 1
      (92 caches); federated motions→52,567 / votes→183,063. Full record: TODO_ARCHIVE.md.
      **NEW FOLLOW-UPS from the wave — ALL WORKED IN WAVE-2 (2026-07-17 night; full
      record in the WAVE-2 entry below):**
      (a) ✅ **vote_overrides ADD-MEMBER mechanism — DONE (wave-2 Phase 0):** shared
      `db_build_lib.py` now ADDs a documented missing-member vote (override row whose
      member has NO CSV row); stale/ambiguous rows fail the build loudly;
      `validate_city.py` h.db formula counts add-rows at −1. Proven: old-vs-new
      validator diffed across all 31 cities — ONLY SSL's line changed (park_city +
      forks byte-identical); SSL rebuilt (+2 Huff Aye rows, "reconciles exactly"
      PASS); ogden conflict-path smoke test exact. SCHEMA_SPEC reconciliation
      invariant rewritten (two override kinds); SSL docs + override notes updated.
      (b) ✅ **CH bare-name-roll re-extraction — DONE:** PAIR_RE role token optional,
      triple-guarded (roster resolution + block anchor + ≥2-member blockless
      fallback); +71 council / +59 PC named rows, 0 motion-level changes; 2021-03-03
      roll now 7/7; NEW verified dissent 2024-03-05 m2 (4-to-1, Mayor Weichers No).
      (c) ✅ **SLC vote extraction — DONE** (direct Read of the 4 markdown docs, no
      API): +20 rows / 3 motions (Res 17/2021 Faris D2 appointment 6-0 + two 7-0 WS
      motions); 2 docs honestly zero-vote. SLC now emits the trailing `provenance`
      column (CSV + db) — the federated provenance filter is meaningful for SLC.
      (d) ~~OWNER scope decisions: murray CSCC series + Legislative Breakfast~~ —
      **RULED OUT OF SCOPE 2026-07-17** (7 dates ledgered in murray's
      pmn_exceptions.csv; PDFs retained in raw/ as catalogued out-of-scope material;
      murray residual → 1 flag);
      (e) ✅ **holladay "bradley-10282025" — MISDIAGNOSIS, corrected 2026-07-17:** the
      file IS genuinely Bradley (sha256 = fetch-log = index; the tranche-1 "Fotheringham
      content" claim came from a scratchpad render collision — both filenames end
      10282025). No index defect; date refined 10-27→10-24 (form's printed/received
      date) in index + buildindex driver; the filing was transcribed. Feeds the
      standing CF cache-key standardization item (trailing-hex keys collide).
      ✅ CH `duplicate_of` column ADDED (+ evidence-driven corrections: Prazen "final"
      = re-upload of his Oct-28 interim [genuine final NOT on file — gap]; Bracken +
      Daurelle filing-period fixes);
      (f) ✅ **murray Evans .docx — DONE** (no soffice: embedded PNGs extracted from
      the docx zip and vision-read; totals reconcile 1,028.15 / 1,377.42; index row
      honestly updated);
      (g) **CF tranches 2+ — 2021/2023 (+2025 where new) cycles DONE for ALL wave
      cities (wave-2):** CH/herriman/holladay/midvale/murray/riverton completed their
      2021+2023 backlogs; NEW vision layers established for SSL (40), bluffdale (54),
      alta (21), EC (29), kearns (38), copperton (19), white_city (10), magna (13).
      REMAINING at the time: the owner-gated per-city `build_finance.py` scaffolds —
      **✅ DONE 2026-07-18 (owner-approved): see the CF-STRUCTURING PACKAGE entry
      below.** Still open: the below-floor/pre-2020 vision tranches
      (murray 2017/2019 ×28, magna 2016–2019 ×43, alta/holladay 2017 handfuls,
      kearns 2023/2025 acquisition blocks [EasyVote auth / Cloudflare]).
- [x] **CF-STRUCTURING PACKAGE — 2026-07-17/18 (owner-approved): the structured money
      layer for all 14 vision-cached wave cities (pilot midvale + 13-city fan-out +
      one federation).** Federated cf_filing→1,843 / cf_contribution→18,834 /
      cf_expenditure→14,959 / cf_cycle→813 across 29 cities; all 14 validate_finance PASS.
      Full record: TODO_ARCHIVE.md.
      **NEW FOLLOW-UPS:**
      (a) ~~**OWNER ADJUDICATION QUEUE**~~ — **✅ RESOLVED 2026-07-18 (owner-authorized
          evidence pass; 5 city agents + registry check; all overrides evidence-cited;
          re-federated same day, 193/31 intact):**
          UNCHANGED-but-locked: midvale Fair $1,427.80/$1,427.80 (NOT a column swap —
          the raise-then-refund narrative, Summary Page proves orientation); herriman
          Grimm $2,525 (the $0 cover is the filer's error — both filings itemize the
          same $25+$2,500); riverton McCay Schedule-B (FILER sign convention, cache
          faithful); bluffdale Larsen $27,010.02 (restatement impossible: Oct-28 <
          Oct-7) + Robbins (gap is IN-SOURCE — her year-end never itemized the
          $5,619.41 pre-general block) + Hales (owner: closed as-is).
          CHANGED (documented overrides): herriman Smith 2021 Mayor
          $20,815.56→**$28,610.56/$28,635.96** and Palmer 2021 Mayor
          $20,617.18→**$32,038.06/$31,782.48** (loans proven REAL by balance
          arithmetic; the Dec "summary" was a dropped period — both confirmed by the
          filers' own YTD columns); holladay Tracy **$4,389.17/$3,924.19** (index
          dates were swapped vs the stamped forms; one $600 exact re-listing
          deduped), Watts 2025 Mayor **$65,135.33/$62,880.49** (only 2 true donor
          re-listings −$1,200; the material fix was a re-listed $13,045.37
          expenditure block — spent DOWN), Wilson 2025 Mayor
          **$38,914.37/$27,017.01** (his Final proven a genuine period — the $10,001
          8/1 self-loan, zero row overlap script-verified); bluffdale Hall spent
          $13,798.78→**$18,471.66** (Schedule-B parentheses were positive outflows —
          the form's own balance chain proves it; 33 cache rows corrected with
          `_correction` notes). riverton Buroker typo corrected at build via
          city-local `_adapt_cache` (intent $3,000.00 proven by the page's own
          $4,000 subtotal; cache stays verbatim; cycle unchanged). alta Abundance =
          **business CONFIRMED** by registry check (consulting firm, no Utah PAC
          registration; both alta docs' "PAC contribution" paraphrase corrected).
          **REMAINING OWNER QUESTIONS (new, surfaced by the pass):** (i) bluffdale
          Hall's Dec-04 "Final" ($4,251.59 exp) may ALSO be a real period like her
          five 2025 peers → spent would rise to ~$22,723 — approve or leave; (ii)
          approve the holladay Tracy index date/reporting_period label correction
          (the two interim files' labels are swapped vs the stamped forms).
          **New acquisition lead:** bluffdale Robbins' itemizing Oct-26 2021
          pre-general filing is absent from the index.
      (b) **Future vision tranches (typed money known present):** CH 21 (18×2021 +
          Hyland 2023 ×3); midvale 17 junk-text; herriman Basham 5784/5802 (~$7.5k);
          magna 2025 general bundles (per-candidate split; Adriano ≈$2,713) + White
          v571 + 2016–2019 scans; below-floor sets (floor-gated).
      (c) **Shared-lib polish candidates (from agent reports — do as one pass):**
          promote herriman's §10-3-208 Schedule-A/B/C parser into `families/` if
          other cities share the layout; distinguish extract_method text-vs-vision;
          fix the donor classifier "loan"-substring fragility (Loannou) + add
          business tokens (Consulting/Group); tighten cycle_totals basis labeling
          (max()-branch reported as `summary`); harden the note-string "superseded"
          match; wire `finance_overrides.csv` into the build (riverton documented a
          row the mechanism doesn't yet consume).
      (d) **Acquisition riders:** CH Prazen genuine Dec-4 final (recorder); riverton
          Pierucci 10-24-23 (state mis-publication); kearns 2023 (EasyVote) + 2025
          (Cloudflare — Longtin ×2 proven to exist); magna 2023 (EasyVote).
      (e) murray's CF-implied 2021 Mayor+D4 primary discrepancy flags are now
          money-backed — fold into the standing elections-review item.
- [ ] **[GATED] OWNER HAND-CHECK of the 2026-07-18 CF adjudications (when time permits).**
      The evidence pass corrected 6 cycle figures and locked 5 others via documented
      overrides; the owner wants to verify each against the raw filings by eye.
      Per-item: the adjudicated figure, what to look for, and the source PDF links.
      **CHANGED FIGURES (verify the override arithmetic):**
      - **Clint Smith, herriman Mayor 2021 → $28,610.56 / $28,635.96.** Check: the
        2nd $5,000 self-loan in the Oct filing is real (opening balance $1,283.39 +
        $10,000 loans − $11,185.60 spent = $97.79 close), and the Dec "Final" is its
        own period ($7,795 / $7,892.79) that must be ADDED.
        [Aug](https://web.archive.org/web/20210807175207id_/https://www.herriman.org/uploads/files/2097/Smith-Clint.pdf) ·
        [Oct](https://web.archive.org/web/20211115134358id_/https://www.herriman.org/uploads/files/2400/Clint-SmithMayor.pdf) ·
        [Dec Final](https://web.archive.org/web/20211211000711id_/https://www.herriman.org/uploads/files/2456/Clint-SmithMayor.pdf)
      - **Lorin Palmer, herriman Mayor 2021 → $32,038.06 / $31,782.48.** Check: the
        5 self-contributions carry distinct dates+amounts (7/16 $4,700, 7/30 $3,500,
        10/20 $5,000, 10/21 $2,000, 11/5 $10,800) and the Dec Final's Column-B YTD
        prints exactly $32,038.06 / $31,782.48.
        [Aug](https://web.archive.org/web/20210807175155id_/https://www.herriman.org/uploads/files/2096/Palmer-Lorin.pdf) ·
        [Oct](https://web.archive.org/web/20211115134359id_/https://www.herriman.org/uploads/files/2401/Lorin-PalmerMayor.pdf) ·
        [Dec Final](https://web.archive.org/web/20211211000754id_/https://www.herriman.org/uploads/files/2453/Lorin-PalmerMayor.pdf)
      - **Daren Watts, holladay Mayor 2025 → $65,135.33 / $62,880.49.** Check: the
        Oct-7 and Oct-28 filings BOTH itemize the same 10/1–10/6 expenditure block
        ($13,045.37: Google Ads, Roost ×2, Union Print ×2, Deseret News, Stripe, Sun
        Print — deduped); donor re-listings deduped are only Rosenberg 8/3 $200 and
        Bowler 10/23 $1,000; the other recurring donors gave on different dates.
        [Aug](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Financial%20disclosures/Watts.Aug2025.pdf?t=202508051318580) ·
        [Oct-7](https://www.holladayut.gov/Watts%20Financial%20Disclosure.pdf?t=202510081554090) ·
        [Oct-28](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Watts.Oct282025.pdf?t=202510281716360) ·
        [Dec Final](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Watts.FInal.pdf?t=202512041146180)
      - **Zac Wilson, holladay Mayor 2025 → $38,914.37 / $27,017.01.** Check: the
        Sept-11 Final's only contribution is the $10,001 self-loan dated 8/1 (absent
        from the Aug filing) and its expenses all date 7/31–9/1, after the Aug
        filing's last expense — zero overlap, so the two reports sum. (The Final's
        cover prints $10,000.10 — a transposition of the itemized $10,001.00.)
        [Aug](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Financial%20disclosures/Wilson.Aug.pdf?t=202508051719440) ·
        [Sept Final](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Wilson.Final.Sept2025.pdf?t=202509121428270)
      - **Natalie Hall, bluffdale Mayor 2025 → spent $18,471.66 (raised unchanged
        $22,135.67).** Check the sign fix: Schedule-B amounts print in parentheses
        but the cover arithmetic SUBTRACTS them as positive magnitudes ($2,324.30 +
        $21,035.67 − $16,135.22 = $7,224.75 ending on Oct-7; chains to Oct-28).
        ALSO the open question (i): is her Dec-04 Final ($4,251.59 exp) its own
        period like her five 2025 peers? If yes, spent rises to ~$22,723.
        [Oct-7](https://www.bluffdale.gov/DocumentCenter/View/9008/20251007-FINANCIAL-NATALIE-HALL-PDF) ·
        [Oct-28](https://www.bluffdale.gov/DocumentCenter/View/9049/20251028-FINANCIAL-NATALIE-HALL-PDF) ·
        [Dec-04 Final](https://www.bluffdale.gov/DocumentCenter/View/9103/20251204-FINANCIAL-NATALIE-HALL-PDF)
      - **Matthew Tracy, holladay 2023 → $4,389.17 / $3,924.19.** Check: the file
        labeled "7-day" is stamped NOV 14 (bal $230.83) and the unlabeled file is
        signed OCT 24 (bal $64.80) — the index labels are swapped (open question
        (ii): approve the index correction); the $600 McDonald web-page expense
        appears in both covers (deduped once).
        ["7-day" = Nov-14](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Financial%20disclosures/Tracy%20-%207%20day.pdf?t=202412191259420) ·
        [unlabeled = Oct-24](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Financial%20disclosures/Tracy.pdf?t=202412191300450) ·
        [Dec Final](https://www.holladayut.gov/Document%20Center/Departments/City%20Recorder/Elections/Financial%20disclosures/Tracy%20-%20Final.pdf?t=202412191314060)
      **LOCKED UNCHANGED (verify the reasoning):**
      - **David Fair, midvale Mayor 2025 = $1,427.80 / $1,427.80.** Check the
        raise-then-refund story: Oct-7 = 5 donors $550 in / $877.80 out (fee +
        signs); Oct-28 = $877.80 self-contribution in / "Return all donations" $550
        out; ends exactly $0.00.
        [Oct-7](https://www.midvale.utah.gov/Document%20Center/Government/Departments/Recorders%20Office/Campaign%20Financial%20Disclosures/2025/David%20Fair%20Oct%207th%20Report%20Redacted.pdf?t=202510062011250) ·
        [Oct-28](https://www.midvale.utah.gov/Document%20Center/Government/Departments/Recorders%20Office/Elections/2025/David%20Fair%20Financial%20Disclosure%20%28October%2028%2C%202025%29.pdf?t=202510281911580) ·
        [Dec-4](https://www.midvale.utah.gov/Document%20Center/Government/Departments/Recorders%20Office/Elections/2025/David%20Fair%20Financial%20Disclosure%20December%204%2C%202025%29.pdf?t=202512041909260)
      - **Rodman Grimm, herriman 2025 = $2,525 / $1,690.21.** Check: both filings
        itemize the same $25 (6/06) + $2,500 (7/29) self-contributions; the Sept
        Final's "-0-" cover is the filer's error. (Each filing exists twice on the
        city site — a documented duplicate pair.)
        [Aug interim](https://www.herriman.gov/uploads/files/5785/Grimm-Rodman-District-3-August-5-Report.pdf) ·
        [Sept Final](https://www.herriman.gov/uploads/files/5786/Grimm-Rodman-DIstrict-3-September-11-Report.pdf)
      - **Tawnee McCay, riverton (pre-primary Schedule-B signs).** Check: her first
        Schedule-B page types every amount negative yet subtotals them POSITIVE
        ($2,680.05) — filer convention, cache kept verbatim.
        [Pre-primary](https://www.rivertonutah.gov/departments/recorder/elections/tawnee-mccay-2025-primary-election-report.pdf)
      - **Tish Buroker, riverton (the "$3,000,00" typo).** Check: Schedule A prints
        $1,000 (Roberts) + "$3,000,00" (self-loan) with the page's own total
        $4,000.00 — intent $3,000.00, corrected at build only.
        [General report](https://www.rivertonutah.gov/departments/recorder/elections/tish-buroker-general-election-report-2025.pdf)
      - **Allen Larsen, bluffdale 2025 = $27,010.02.** Check: Oct-28 ($10,104.62) <
        Oct-7 ($12,685.40) — impossible as a restatement; recurring vendors carry
        different per-period amounts.
        [Aug](https://www.bluffdale.gov/DocumentCenter/View/8701/20250805-FINANCIAL-ALBERT-ALLEN-LARSEN-PDF) ·
        [Oct-7](https://www.bluffdale.gov/DocumentCenter/View/9004/20251007-FINANCIAL-ALLEN-LARSEN-PDF) ·
        [Oct-28](https://www.bluffdale.gov/DocumentCenter/View/9045/20251028-FINANCIAL-ALLEN-LARSEN-PDF) ·
        [Dec Final](https://www.bluffdale.gov/DocumentCenter/View/9099/20251204-FINANCIAL-ALBERT-ALLEN-LARSEN-PDF)
      - **Connie Robbins, bluffdale 2021 = $6,445.84 / $6,445.84 (covers).** Check:
        Schedule A hand-marked "none"; Summary splits expenditures $5,619.41 (thru
        Oct 25, itemized NOWHERE in this filing) + $826.43 (itemized) — the gap is
        the filing's own; her itemizing Oct-26 pre-general report is a new
        acquisition lead.
        [Year-end Final](https://www.bluffdale.gov/DocumentCenter/View/4471/Connie-Robbins-FINAL-Campaign-Financial-Report-2)
      - **Mark Hales, bluffdale 2023 = $2,000 / $910.61 (closed as-is).** The $2,000
        Realtors check: uncashed on the Oct-24 filing ($0 cover), cashed by Nov-14.
        [Aug](https://www.bluffdale.gov/DocumentCenter/View/5770/Campaign-Finance-Statement---Mark-Hales-08-29-2023-PDF) ·
        [Oct-24](https://www.bluffdale.gov/DocumentCenter/View/5994/Campaign-Finance-Statement---Mark-Hales---10-24-2023-PDF) ·
        [Nov-14](https://www.bluffdale.gov/DocumentCenter/View/6060/Campaign-Finance-Statement-Mark-Hales---11-14-2023--PDF)
      - **Roger Bourke, alta 2025 — the $2,000 Abundance line is IN-KIND from a
        consulting FIRM** (classified business; no Utah PAC registration found).
        Check: Form A puts the $2,000 in the In-Kind column.
        [Oct-3 report](https://storage.googleapis.com/juniper-media-library/130/2025/10/Bourke%20Campaign%20Finance%20Report%2010-3-2025.pdf) ·
        [firm site](https://abundancepolitical.com/)
      When done: check this item off with a dated note; any disagreement goes
      through the documented override files (cycle_overrides.csv /
      finance_overrides.csv), never in-place edits, then rebuild + re-federate.
- [x] **WAVE-2 — 2026-07-17 (night): shared-lib add-member overrides + the 21-agent
      per-city wave (agenda-grade recovery / primary-docs residue / CF tranches 2+ /
      wave-1 extraction follow-ups) + single federation.** 21 city-disjoint agents, all
      0 FAIL; federated motions→52,667 / votes→183,349 / contested→3,700; recovered-
      provenance motions 2,287 (incl. new `citysite_minutes`). Full record: TODO_ARCHIVE.md.
      **NEW FOLLOW-UPS from wave-2:**
      (a) **GRAMA queue (owner-gated outreach)** — ready-drafted requests per city for
          the genuinely-unpublished minutes: vineyard 2 (Nov-2025), logan 12,
          taylorsville 9, st_george 11, alta 14, herriman 2 (+ HCFSA 2023-08-23, the
          un-flagged same-day sibling — verify + ledger it when sending), riverton 6 +
          the Timberline/att8–12 packet objects, bluffdale 2, copperton 6, kearns 1
          (2025-01-13), EC 19, CH (Dec-2022 council ×2 + 8 purged PC/AH), midvale 3.
          Texts live in each wave-2 agent report + several pmn_backfill/ notes
          (bluffdale has a ready file: `pmn_backfill/GRAMA_request_draft.md`).
      (b) **pmn_crosscheck engine hardening (5 independent confirmations this wave):**
          (1) RE_CANCEL/RE_NOT_MEETING must scan the notice BODY text — cancellations
          are frequently body-prose-only (taylorsville/logan/midvale/WJ/riverton);
          (2) a `(date, repo_datasets)` dedup — RDA flags duplicating same-date
          council flags (logan); (3) the "Meeting Rescheduled" notice family
          (st_george ×5).
      (c) **Whisper/audio leads accumulated** (feeds the owner-gated Whisper program):
          st_george 2024-10-10 council (2 Revize MP3s); taylorsville PC ×3 (PMN
          .mp3-only); copperton ×3; magna 5 COVID council dates; alta 4 council dates;
          EC's existing candidates unchanged.
      (d) **riverton Pierucci re-acquisition** — obtain his genuine 10-24-23 28-day
          report (state mis-publication; index row pending owner annotation).
      (e) **CH Prazen genuine final CF report** — not on file (the posted "final" is
          an interim re-upload); recorder-request candidate.
      (f) **draper 2 needs_ocr staff reports** (same image-only 18.6 MB PDF ×2) →
          next repo-wide vision pass (binary discarded — RE-FETCH first).
      (g) **fetch_new hardening idea (CH pattern):** a Wayback-listing sweep for
          delisted-but-still-served-by-ID CMS docs — will recur.
      (h) **WJ PC roster regeneration** over the merged 2020+ span (optional —
          `first_seen` starts at the 2022 audited floor; pre-existing
          validate_votes out-of-range notes).
      (i) **Pending re-checks next refresh:** magna CRA 2026-05-12 + 2026-06-09
          (minutes pending) + 2025-11-18 still draft-only; st_george PC 2026-03-10;
          vineyard's 2 pending-adoption dates.
      (j) **magna lower-confidence flags not worked** (deliberate scope cut): council
          specials 2022-08-16 / 2024-06-18 / 2024-09-24 / 2025-09-09 + PC 2019-09-12 /
          2019-12-12 (PC is a documented complete superset).
- [x] **LARGE+MEDIUM EXECUTION WAVE — 2026-07-19 (owner-directed automode; 24 agents
      in 3 conflict-planned waves + ONE federation; every agent 0 FAIL).** Executed the
      entire non-owner-gated large/medium queue. Federated: motions 53,302→**53,871** /
      votes 185,316→**188,723** / contested 3,748→**3,844** / integrity ok / FK 0 /
      193-31 intact / reconciliation exact; coverage.json regenerated (433 entries).
      **Headline: the ogden 2020–2023 PC "~60-row gap" was 63 WHOLE MEETINGS** — all
      recovered (60 standalone DocumentCenter drafts + 2 packet-embedded + 1 bonus;
      2020-08-26 proven a BZA agenda, not PC), PC 445→988 motions / contested 54→149,
      100% approval-chain-verified, roster 16→19 (the Jan–Mar 2020 cohort), new
      documented `planning_commission/vote_corrections.csv` mechanism (6 rows, the
      failed-motion both-lists-"aye" reversal class), reusable discovery channel
      (CivicPlus site-search indexes DocumentCenter; 301-Location slug probe).
      Other completions, per item: **CH + herriman append-only-ingest conversions**
      (both destructive paths guarded behind --force-full-rebuild + auto-backup;
      idempotency/preservation proofs; herriman post_ingest auto-chains the 949-row
      backfill re-run; + 3 latent herriman extractor non-idempotency bugs fixed — 6 PMN
      movers recovered). **CF typed-money tranches all done** (CH 21 → 2021 layer lit up
      [Weichers $25.7k, Evans $18.3k]; midvale 17 → 6 page-proven cycle overrides
      [Gettel 2025 Mayor $32,297/$25,305]; herriman Basham ×2 [cycle → $7,824/$7,748];
      magna bundles expanded per-candidate [Sudbury $10,735/$9,735]; locked adjudicated
      figures verified unchanged everywhere). **CF shared-lib deferred polish** (truthful
      basis labels incl. `max-mixed`; finance_overrides wired fail-loud; §10-3-208
      promotion DECLINED on 0/15 ground-truth; extract_method labels; regime-aware
      cycle_totals [taylorsville 15→8]; **vision cache keys standardized** — 281 caches /
      7 cities migrated, byte-identical proofs, skill text shrunk). **draper PC
      narrative-era** verified pre-applied + derived rebuilt (h.db +32 delta closed;
      contested 214→220) + both needs_ocr staff reports vision-resolved. **st_george**
      gutter/joint extraction gaps fixed (+the real 3:2 failed hillside rec), PC
      Anderson attendance-based, ords 2026-051..056 HIGH, roster seam verified
      (council Anderson = ex-PC chair, body move). **alta** wrapped-glyph roll fix
      (+9 Ayes). **EC** `2nd by:` verified pre-applied + a dropped 2019-06-19 council
      motion recovered (`second by` anchor). **SSL** roster verified + chair seam
      resolved-no-change; Huff overrides verified. **millcreek** F-1 en-dash (+362
      named 2017 Ayes), in-packets comments layer BUILT (9 letters, honest floor),
      9 CUMULATIVE-column cycle overrides (Silvestrini 2019 $88,369/$64,860).
      **taylorsville** 35 annuals visioned (real money surfaced, regime-excluded),
      27 received-stamp dates. **Ordinance backfills** (e): slc 21 (not 22 — Ord 26
      pre-existed; 2026 now 1–40 complete), WJ 8 (26-29/30 = TABLED, honest), WVC 5
      (26-26/27 = DENIED), orem +5 (first medium tier via WP-post matcher), park_city
      2 = documented honest gap (archive unreachable). **Name gates** (taylorsville,
      WVC, st_george, vineyard) all byte-identical-proven; vineyard's second Blackburn
      (Spencer) real but never co-occurring. **Harness**: murray PMN 735/983 +
      white_city 5879 probes added; 7 stdout-only cities now emit probe JSON.
      **Geo**: WVC+SLC pre-2022 maps reconstructed (SLC D7 honest LOW); **millcreek
      2016 boundary AUTHORITATIVE** (city ArcGIS org layer, medium→HIGH) — and the
      dissolve reconstruction proven MATERIALLY WRONG there (IoU 0.00–0.25, renumbered
      precincts). **roster_lib H-A..H-H** closed (H-E deferred as elections-schema
      work; sidecars retired; sentinel live). **v_contested follow-ups**: tally_other
      ruled BY DESIGN (11-motion ground truth, semantics documented); per-city
      v_contested now mirrors the federated split-column shape across all 31 dbs
      (counts proven identical). Cross-agent incident root-caused: normalize_motions
      `write_crosswalks` regenerates crosswalk CSVs from IN-SCRIPT CONSTANTS — kearns
      CRA + EC Recuse rows added to the constants (curated crosswalk rows MUST go in
      the constants, never only the CSVs). Backups: `_backups/2026-07-19-lm-wave/`.
      **NEW FOLLOW-UPS — ALL (a)–(k) EXECUTED SAME DAY (2026-07-19, second automode
      wave: 10 agents, every one 0 FAIL; interrupted mid-run by a session usage limit,
      all 9 live agents resumed from transcript cleanly; re-federated after — integrity
      ok / 193-31 / reconciliation exact). Per-item outcomes are annotated inline
      below; NEW leads from this second wave are listed at the end of this entry.**
      (a) ✅ DONE — re-keyed to the TRUE pair (PC 2022-02-02 app 435 → Council 2022-08-09 app 60, Ords 2022-39/40; old keys had drifted onto an RDA adjourn + a WSU resolution); binds high/override, all other override rows verified holding; do-not-quote warning retired. **ogden Franklin Street referral override MIS-BOUND** (pre-existing; "high"
          link resolves to two unrelated 2024/2026 RDA motions; do-not-quote warning
          in ogden CLAUDE.md) — re-derive correct stable keys.
      (b) ✅ WS SIBLINGS DONE (both ingested, in-body + approval-chain verified, 0 motions each — honest; all_votes byte-identical). Pre-2020 drafts + Landmarks/BZA remain owner-gated. **ogden leads:** 2 sibling work-session docs on audited dates (2021-08-18,
          2021-12-15); pre-2020 PC drafts on DocumentCenter (data-floor extension,
          owner-gated); Landmarks/BZA minutes also live there if ever wanted.
      (c) ✅ DONE — the defect is SYSTEMIC: none of the 6 publishes a true pre-2022 layer; fragmentation-control proof (current-dissolve clean vs pre-2022 dissolve 3–15 fragments) ⇒ all 6 reconstructions downgraded to LOW with cited notes (kept as approximate artifacts; district_precincts CODE composition stays medium). True prior geometry for the 6 = same external-fetch gap tier as provo/ogden. **boundary-reconstruction validation lead:** millcreek proved current-shape
          dissolve can be actively wrong where precinct codes renumbered — probe each
          reconstructed city's OWN ArcGIS org for authoritative prior vintages
          (WJ/taylorsville/SJ/sandy/WVC/SLC), the millcreek channel.
      (d) ✅ DONE — 99/100 ?packet=true packets fetched (4.8 GB→text→§9 discard), comments 9→27 incl. the 2020 FormCenter web-form archive (refutes the 'submit-only/no archive' record); 180 audited exclusions; residual = OCR-unsignable letters, doc757, pre-2018. **millcreek comment-letter ceiling:** the big `?packet=true` land-use packets
          with standalone "Public Comments from Residents" appendices are unretained —
          live re-fetch would raise the 9-letter floor.
      (e) ✅ DONE — membership index row + canonical mapping + order-independent expansion dedup (White/Romero pattern); Jones $958.44/$958.44 True/True; Jones-only diff proven; overrides undrifted. **magna Brooks Jones** (2025 D4 primary-eliminated, $958.44, transcribed in
          vision/0a3cfc7e.json) needs an acquisition index.csv row to structure.
      (f) ✅ DONE — byte-identical md5 confirmed; in-body year proves the 2025 statement → '2024' label excluded via a new data-driven duplicate-excluded gate (raw+cache retained); genuine CY2023 annual ledgered unpublished (probe: still unposted); cycle_totals byte-identical. **taylorsville Overson annual dup:** doc8378 ≡ doc10635 byte-identical (2025
          annual posted under both year labels; genuine 2024 annual unpublished).
      (g) ✅ DONE — murray: Markham appointed BY LOT 2022-12-12 (oath same night), resigned ~2023-06-28 (became CED Director); Rodgers appointed BY COIN TOSS 2023-08-08; false 10-month VACANT replaced by the real 6-week one; both HIGH. SSL: Glad+Jones appointed+sworn 2026-02-25 (→HIGH); Huff resignation 2026-01-28 → documented D1 VACANT; Sanchez departure honestly bracketed medium. Sentinel ZERO both cities. **roster adjudications (H-B sentinel finds):** murray D1 2023 votes inside a
          rostered VACANT (roster predates the 07-16 recovery) + SSL jones/glad votes
          before their 2026-06-10 rostered appointments — minutes-grounded review.
      (h) ✅ DONE — all 17 dispositions = CITED EXCEPTIONS, rosters correct (copperton 2019 SOVC-drop + 2025 cancelled-unopposed; holladay/white_city uncontested-seat SOVC omissions; magna 2023 cancelled; riverton D3↔D4 renumber; sandy multi-winner At-Large; slc defective 2019 winner rows + 2021 D2 swap). Riverton+midvale precinct layers ENABLED (reconcile; pre-2022 honest gaps). REFUTED: the 'Pratt appointed' CF claim — he was ELECTED unopposed (2025-10-15 minutes). **H-C exception-candidate list** (copperton, holladay 2023, magna 2023,
          riverton renumbering, sandy at-large, slc 2019/Puy, white_city 2021) — each
          needs verification before an exception row is written; riverton+midvale
          precinct-layer enablement now unblocked (H-A).
      (i) ✅ DONE — defect reproduced (243 discard rows blanked), guard added + byte-identical no-op proven; caveat retired; script is draper-only (no clones). **draper `link_text_sidecars.py` hardening** — it blanks §9 columns on
          `stored=no` discard rows (documented do-not-run caveat in draper docs).
      (j) ✅ DONE — CONFIDENCE-GATED (only high/medium prior geometry resolves; per-district gating; provenance carried on hits; low/absent → honest explanatory gap). Today only millcreek qualifies — demo verified 3-way incl. a prior≠current divergence point. **plan-aware `representatives_for_address`** — pre-2022 dates could now
          resolve against the authoritative/reconstructed prior maps (shared-lib
          behavior change, all district cities).
      (k) ✅ RE-PROBED (8 channels; Revize ≠ CivicPlus so the site-search trick N/A) — signed PDFs still unpublished; RECOVERED the PMN Notice of Adopted Ordinances (1090107) independently corroborating both (number+date+title), archived un-indexed in ordinances/independent_notices/ (a summary notice is NOT the signed instrument — correctly not promoted). Rows stay within_source; re-try later. **park_city ords 2026-15/2026-18 signed PDFs** — re-try when the
          showpublisheddocument CMS route is reachable (promotion steps in its
          AVAILABILITY.md).
      **NEW LEADS from the follow-ups wave (2026-07-19, second automode wave):**
      (l) **[owner Q] copperton 2025 seat lettering** — the certified candidate list
          letters the 2025 cycle as seats C + D, but the roster models town-era
          cohorts A/B/C + D/E (Pratt on AL-E); the HB35 town-era re-lettering is
          unresolved (documented in copperton roster/CLAUDE.md).
      (m) ✅ FIXED 2026-07-19 (same day, own Fable agent; resumed once after a 529) —
          the defect had reached the AUDITED slc_races.csv. TWO root causes: 2019 =
          a stale pre-family-B raw slice (archive's own slice was already correct);
          2021 = a LIVE family-C bug (privacy-suppressed precincts' per-precinct
          Total rows skipped → 6/9 D2 precincts dropped → the Palmer/Puy swap).
          Fixed in the archive normalizer (suppression-recovery Total rows,
          structurally double-count-proof); propagated county+slc with surgical
          proofs (exactly 9 slc races changed: 2019 D2/D4/D6/Mayor = Johnston/
          Valdemoros/Dugan/Mendenhall; 2021 D2 = PUY 1,084/751 — he led round 1;
          the "won from behind" narrative was itself an artifact; D3 runner-up also
          corrected). 9/9 cross-city corroborations to the vote; alta's suppressed
          2021 tallies recovered. All 4 slc H-C exceptions removed (fail-loud fired
          as designed); federated. Follow-on leads → (s)(t)(u)(v) below.
          *(original)* **slc elections-layer defect lead** — the 2019 SOVC winner rows for
          D2/D4/D6/Mayor are header mis-parses ("Vote By Mail"/"Vote Centers" read
          as the winner) and the 2021 D2 rows list Palmer as winner over Puy
          (swapped). Rosters carry cited H-C exceptions; the fix belongs at the
          ELECTIONS layer (verify election_race vs the county canvass, repair the
          per-candidate rows).
      (n) ✅ FIXED 2026-07-19 (same day) — draper-pattern guard + no-op byte-proof +
          synthetic sandbox proof (the old script provably destroys the row). The
          30-city sweep found 6 MORE dormant same-class scripts → lead (p).
          *(original)* **EC `classify_attachments.py` latent reset** — same
          reset-derived-columns-each-run pattern as draper's fixed
          link_text_sidecars; dormant today (EC has 0 discard rows) — harden before
          EC ever gains §9 discard rows.
      (o) **six-city prior-geometry acquisition** — a 2019/2020-vintage SLCo
          VistaBallotAreas snapshot (not openly published) or georeferenced
          ordinance-map exhibits would lift the six LOW reconstructions; same tier
          as the provo/ogden external fetches.
      **POST-INGEST AUDITS — 2026-07-19 (same day, read-only agents; reports in
      `_audits/2026-07-19-postingest-{ogden,park_city}/report.md`):**
      • **ogden PC backfill: PASS (A−)** — transcription 0.999; all 6 vote_corrections
        + 8 tally-mismatch policies + approval chains verified clean. F1 (the one
        data defect: 2020-05-06 m9 "wit" typo → tally-only) **FIXED same day**
        (+9 named rows incl. Safsten's Nay, corpus byte-stable, tally 648/648) with
        the F2 doc drift; F3 → lead (q).
      • **park_city PC re-extraction: B+** — 22 new contested motions 0-fabrication;
        pre-2024 byte-identity held; BUT 1 dropped motion + 6 garbled results (one
        root cause: dotted page tokens severing outcome verbs, outside the fixer's
        11-meeting sample). **FIXED same day** (window-localized strip after a global
        clean_lines attempt was self-caught corrupting motion text; PC 872→873, the
        2024-11-13 Johnson/Sigg continuance recovered; 6 results healed; contested
        52 stable; overrides/tie-breaks/referrals hold; both docs' "0 mismatches"
        claim corrected). F7 → lead (r). Re-federated after all fixes: motions
        53,872 / votes 188,732 / contested 3,845 / integrity ok / 193-31.
      **FURTHER LEADS (p)–(v), from the audits + the (m)/(n) fixes:**
      (p) **batch-guard the 6 dormant reset-pattern classifiers** — alta, copperton,
          kearns, lehi, riverton `packets/classify_attachments.py` + salt_lake_county's
          (all currently 0 discard rows; sandy/logan's live discard rows confirmed
          SAFE). Mechanical, one small agent.
      (q) **ogden recovery-channel provenance tags** — the 63 recovered PC meetings
          carry provenance='minutes'; consider `doccenter_draft`/`packet_carve` values
          so draft-sourced recoveries are filterable (audit F3; design decision).
      (r) ~~**park_city pre-2024 PC count gaps** (5 dates, byte-identical to pre-fix,
          benign on inspection) — confirm in a future full-corpus pass (audit F7, low).~~
          DONE 2026-07-19: full-corpus confirmation pass over all 104 pre-2024 PC
          meetings (outcome-sentence vs emitted metric). ALL BENIGN — no missed
          extraction; every printed outcome captured. Excess MOTION: markers are
          adjournments / superseded-restated / procedural agenda-order motions with no
          printed outcome (honest drops). No fix, no rebuild; invariants unchanged
          (873/1086/52); validate_city 24 PASS / 2 WARN / 0 FAIL. Evidence:
          `_audits/2026-07-19-postingest-park_city/f7_followup.md`.
      (s) **slc roster note refresh** — Puy's tenure `note` still carries the
          historical 363/361 narrative verbatim (kept for byte-stability); refresh at
          the next roster update.
      (t) ✅ DONE 2026-07-19 (with the SLC pipeline re-point, same agent) — the
          re-pointed `clean_elections.py` now emits the county canonical's recovered
          2019 SLC municipal primary: **Mayor 8-way** (Mendenhall 9,046 / Escamilla
          8,015 advancing — externally corroborated outcome; Dabakis 7,531, Garbett
          6,238, Ibarra 3,046, Penfold 2,528, Huck 566, Goldberger 296) + **D6**
          (Luke 3,542 / Dugan 2,677 advancing; Martin 818). Diff proven surgical:
          57 prior races byte-identical in order, +2 race rows (+11 candidate,
          +1,058 precinct rows) at their sort position; tallies match
          election_results_by_contest.csv 11/11. slc_races.csv = 59 races.
          NOTE: gov.db `election_race` is +2 stale for slc until the next federation
          (not rebuilt in this wave by design).
          *(original)* **adopt the archive's recovered 2019 SLC municipal PRIMARY** (incl. the
          8-way Mayor primary) into `slc_city_council/election_results/` — adds races,
          out of the fix's byte-stable scope.
      (u) **other cities adopt the recovered 2021 tallies** — alta's suppressed-blank
          `winner_votes` can now fill; fold into the deferred "re-point the 7 city
          election pipelines at the county canonical" item.
      (v) ✅ FIXED 2026-07-19 (same day) — the family-C sheets' trailing all-zero
          `Cumulative` template sections now carry `precinct='Cumulative'` (the
          workbook's own rollup label; archive normalizer + README, county
          CLAUDE.md documented; `build_elections.py` excludes it from
          `n_precincts`). Diff proved surgical: 638 rows in the county canonical
          (2021 general 332 / 2023 general 306; +86 in the archive's even-year
          2022 file), ONLY the precinct field, all `votes=0`; row counts
          unchanged; `election_results_by_contest.csv` byte-identical; lead-(m)
          Total-recovery rows (3,090) byte-identical; 3 contests spot-checked
          against the raw workbooks. Backups:
          `_backups/2026-07-19-pv-tierb-low/lead-v/`.
          *(original)* **[low, cosmetic] family-C `Cumulative`-section 0-vote rows** misattributed
          to the last precinct (pre-existing; left for diff surgicality).
- [x] **Q3-2026 QUARTERLY REFRESH — 2026-07-19 (first full run of the routine; 23
      parallel city agents + one federation; every agent 0 FAIL).** 31/31 portals ok,
      75 crosscheck flags worked to zero, ~62 docs ingested across 14 cities (federated
      motions→53,010 / votes→185,111 / contested→3,726); 7 city-local defects + the
      refresh_lib dedup bug fixed. Full record: TODO_ARCHIVE.md.
      **FOLLOW-UPS (new, prioritized):**
      (a) ✅ 🔴 **HIGH — park_city PC parser gap — FIXED 2026-07-19 (same day, own
          agent + federated).** `folded_vote_window` grammar (+ outcome-only-block
          attach + inline-dissent capture with a new `names_mode` field;
          VOTE-marker-wins and no-fabrication guards). **PC 602→872 motions /
          790→1,085 rows / contested 30→52**; all 40 folded-era meetings reconcile
          0 mismatches (11-meeting verbatim audit sample); 6 pre-2024 mislabeled
          motions also recovered + a whitespace line-wrap bug found during the
          audit recovered 21 more; **pre-2024 corpus proven byte-identical
          (784/784 rows incl. motion_no)**. Referrals 101→113 (+12 Council←PC).
          The finding turned out BIGGER than flagged: dissent DID exist in the
          folded era (contested +22, e.g. 3-2 denials with named Nays) — the
          "all unanimous-consent" read was itself an artifact of the missing
          motions. Docs corrected (the understated PC note + stale city figures);
          Bill Johnson roster range extended to 2025-11-12 (source-verified).
          Residual: `validate_city` shows a NEW explained WARN (f.tally 86.4% —
          8 folded name-only-dissenter rows, the WJ/SJ partial-naming class);
          future enhancement lead: apply inline-dissent capture to CLASSIC VOTE
          windows too (a handful more named dissenters, each needs verification).
      (b) **Harness harmonization:** refresh_status.py can't parse the newer-wave
          cities' probe JSON shapes ("no probe" for ~8 cities despite OK probes)
          and 6 cities print-only (no probe json); herriman fetch_new needs a
          read-only --probe + append-only ingest (its --build-md is destructive —
          proven); build_sources_index.py --verify-sample needs a per-slug mode
          (global N stamps other cities); CH harvest_portal exact label=="minutes"
          match misses fragmented anchor labels (why its live-by-ID minutes hid).
      (c) **Crosscheck engine hardening (now 6+ confirmations):** cancel-detection
          must scan notice BODY and DESCRIPTION fields (title/filename-only today);
          (date, repo_datasets) dedup; "Meeting Rescheduled" family; nephi's
          council-body PC cross-filing (3rd instance) = the multi-dataset
          repo_datasets mapping.
      (d) **referral_overrides.csv unstable-key design** (west_valley: integer
          application_ids drift on every rebuild — re-keyed 507→512 this quarter,
          WILL drift again; re-key to stable case-numbers/app_keys; check other
          override-bearing cities).
      (e) **Ordinance backfills owed** (adopting motions already captured; the
          cross-reference layer lags): slc 22 (Ord 19-25 + 27-40 of 2026,
          JS-gated archive), west_jordan 8 (26-26..33), west_valley 5 (26-26..30),
          orem (re-derivation over the 5 new minutes), st_george (2026-051..056 +
          Title 10 codification), park_city 2 signed PDFs.
      (f) **st_george roster seam** — Mayor Hughes + new member Austin Anderson →
          run update-council-roster.
      (g) **SSL design question (owner):** vote-less work-meeting minutes ARE
          published to PMN but the residual ledgers them "minutes-not-posted" —
          distinguish the two states? build a vote-less WM minutes layer?
      (h) Smaller: draft-promotion watches (logan 2 PC drafts re-upload under same
          filename; sandy 2 council + 2 PC drafts pending; SSL AgendaCenter
          approved copies supersede later); copperton ordinance-roll enrichment
          lead (Ord 2024-12-01 4-0-1); SJ transcript-style-OCR motion-text
          hardening + doc-count drift; millcreek CRA 06-22 minutes unposted; EC PC
          2026-07-09 pending; ogden "AYE —" OCR anchor variant; provo/lehi packet
          window decisions.
- [x] **HARDENING BUNDLE — 2026-07-19 (owner-authorized; executed solo/inline; ONE
      federation at the end — integrity ok / reconciliation exact / 193-31).** Closed the
      Q3 follow-ups (b)(c)(d) + the CF shared-lib-polish core (pmn_crosscheck engine,
      refresh harness, referral overrides on stable keys, donor/loan classifier fixes).
      Full record: TODO_ARCHIVE.md.
      **STILL DEFERRED from the polish list (cosmetic/design, precise specs in the
      CF entry):** cycle_totals basis-label truthfulness (max()-branch reported as
      `summary`); wire `finance_overrides.csv` into the driver; §10-3-208 family
      promotion (survey whether any other city shares herriman's Schedule layout
      first); extract_method text-vs-vision label; the kearns/EC-style
      stdout-only probes writing standard JSON (5 cities).
- [~] **PMN-crosscheck RECOVERY LEADS — the verified inventory (2026-07-17; the
      crosscheck's standing output — work these as recovery passes; each city's
      pmn_backfill/CLAUDE.md verification section has the full per-flag detail).
      ⚡ UPDATE 2026-07-17 evening: the "REAL MINUTES ON PMN, fetchable now" tier is
      DONE (promoted — see the wave record above).
      ⚡⚡ WAVE-2 (2026-07-17 night): the AGENDA-GRADE tier is WORKED TO ZERO OPEN
      FLAGS across all 16 flagged cities (see the WAVE-2 entry below for the full
      record). Recoveries: **west_jordan 27 of 28** (legacy city-site channel —
      PC motions 203→287), **magna 4** COVID-cluster (2 embedded in next-meeting
      packets), **cottonwood_heights 20** (2024 PC hole CLOSED; delisted-but-live
      CMS docs via Wayback listing anchors), **midvale 1** (Revize URL variant).
      Everything else verified DEAD (held-but-unpublished → minutes_unrecovered
      ledgers, with drafted GRAMA texts per city) or FALSE-POSITIVE (cancellations /
      notice-date artifacts / wrong-body → pmn_exceptions ledgers). Coverage-claim
      contradictions CORRECTED in riverton + bluffdale + CH docs. What REMAINS below
      is only the owner scope decisions + the ingestion-side items (now done):
      - **REAL MINUTES ON PMN, fetchable now:** slc 3 (2021-05-13 special formal +
        2021-06-10/2023-05-25 work sessions); CH 5 (2023-03-08 PC full business mtg,
        2021/2022 admin hearings, 2022-01-25 retreat); magna 3 council specials
        (2022-11-29, 2023-02-23, 2023-03-23); EC 3 council (2021-01-28, 2021-02-25,
        2023-01-24); lehi 2 PC work sessions (2026-03-05, 2026-05-07); nephi ~7 council
        work sessions + CM 2025-10-21; murray ~19 (budget/CoW/specials incl. Carbon Free
        Power 2020-04-16 + the 2026-02-03 CoW-on-cancelled-council); south_jordan PC
        2024-05-14 FINAL; provo 2024-07-23 Library-Board joint; west_valley 2021-09-28 +
        2022-02-01; ogden's reverse-combined siblings (JWS net-new; 2 already in
        pmn_backfill pending promotion); SSL 2024-07-18 PC no-quorum minutes.
      - **AGENDA-GRADE coverage holes (recover from city CMS/GRAMA):** CH's 2024-02→10
        PC hole (10 mtgs) + Dec-2022 council [ESCALATED — contradicts its superset
        claim]; WJ's 28 standalone PC mtgs 2020-01→2021-03 [extends its known caveat];
        magna's Aug–Dec 2020 COVID council cluster (8) + CRA 2024-12-10/2026-05-12
        [never probed by fetch_new]; riverton 6 [contradicts "0 still-missing";
        Granicus path]; bluffdale 2022-08-16 + 2026-02-11 [contradicts "2024-26 fully
        in repo"]; taylorsville 12 PC/specials; st_george 14 (2 implausible dates need
        scrutiny); logan 16 (budget workshops/TnT); alta 14; midvale 9; vineyard 5;
        copperton 6; white_city 4; EC/herriman/others per their reports.
      - **SCOPE DECISIONS for the owner (still open):** lehi advisory-committee
        bodies; orem RDA/MBA/BoA promotion candidates (22 recovered docs, no repo
        layer). (murray CSCC was ruled out of scope 2026-07-17 — see the wave entry.)
      - **✅ INGESTION-SIDE fix — DONE 2026-07-17 (wave-2 Phase 0):** SSL
        `fetch_new.py` `is_minutes()` now accepts no-quorum minutes (minutes header +
        "Meeting Minutes" title + explicit no-meeting/no-quorum statement, no vote
        lines required); tested against the real 2024-07-18 record (detects), 3 real
        agenda packets + a quorum notice (reject), recorded minutes (still detect).
        SSL PC minutes_unrecovered.csv gained its **8** genuine 2022 agenda-only
        dates (4 of the 12 candidates were correctly EXCLUDED as non-meetings: 2
        hearing notices, 1 publish-date artifact, 1 cancelled); residual recounted
        214→221 across SSL's docs.
- [x] **Mandatory PMN cross-check in every refresh — ORIGINAL PLAN TEXT (superseded by
      the dated closeout above; retained for the design-constraints record).** Fold a
      PMN date-diff pass into `refresh-city` (and a shared script), motivated by the wave
      expansion's yield (murray: both known gaps closed from PMN; herriman: 12 "cancelled"
      2020 meetings were real + 2024+ agency minutes missing from combined docs; draper:
      3 TnT specials never on Granicus). DESIGN CONSTRAINTS (from the same wave's failure
      modes): (a) **flag-and-review output only, NEVER auto-ingest** — PMN carries drafts,
      mislabeled attachments, wrong event dates, body misfilings; candidates go to a
      per-city report for verification before any promotion; (b) **per-city exception
      ledger** (verified-mislabel/known-duplicate rows, seeded from each pmn_backfill/
      CLAUDE.md) so false positives don't resurface every quarter; (c) **periodic body-list
      re-crawl** per entity (bodies re-register — draper council 379→5555 — and new bodies
      appear; a frozen id map silently goes blind); (d) **one-directional diff** (PMN-has /
      repo-lacks) — PMN purges history (kearns/magna/copperton 2017–18), so PMN absence
      means nothing; (e) exact-date matching where the city's PMN event dates are reliable
      (draper), ±3–4d tolerance elsewhere; also scan attachment FILENAMES for "minutes"
      (labels under-count) and compare per-date doc COUNTS (catches multi-doc days);
      (f) **trailing exclusion window (~60 days)** — minutes attach to PMN notices only
      after ADOPTION (~2–6 wks post-meeting; same lifecycle as the portal), so recent
      meetings are agenda-only on both sources and would flag as pure pending-adoption
      noise without the window (observed: draper 2026-07-07, murray 2026 PC recents).
      PMN exposes no attachment-upload timestamps — per-city lag behavior accrues free
      from successive refresh probe logs; revisit the window size after 2–3 cycles.
      Cost: ~10–15 min/full refresh against the single politely-throttled utah.gov host.

      **IMPLEMENTATION PLAN (city-by-city, looped-hardening — the roster_lib pattern):**
      1. **Shared engine first**: `scripts/pmn_crosscheck.py` (city-agnostic, read-only
         vs the repo, report-only output). Inputs per city: `pmn_backfill/pmn_bodies.csv`
         (body_id, body_name, repo_dataset it maps to, date-match mode exact|±4d — NEW
         config file, seeded from each city's pmn_backfill/CLAUDE.md body discoveries)
         and `pmn_backfill/pmn_exceptions.csv` (verified mislabels / duplicate notices /
         known drafts, with a `verified_date` + one-line reason each). Output:
         `pmn_backfill/crosscheck_report.md` + machine-readable `crosscheck_flags.csv`
         (date, body, flag_class ∈ missing_minutes|agenda_only_gap|new_body|count_mismatch,
         evidence URL). The script ALSO diffs the live publicBodies list against
         pmn_bodies.csv and flags new/renamed body ids (constraint (c) built in, so a
         frozen map can't silently go blind).
      2. **Pilot on 3 behavior-diverse cities**: bluffdale (known superset ⇒ expect 0
         flags — the false-positive test), murray (rich recovery history ⇒ expect flags
         matching the known 2026 agenda-only recents — the recall test), herriman
         (body-misfiling + filename-vs-label quirks — the metadata-noise test). Iterate
         the engine until all 3 run clean against their known ground truth.
      3. **City-by-city rollout across all 31** (+ salt_lake_county later, entity-aware):
         one focused agent per city seeds pmn_bodies.csv + pmn_exceptions.csv, runs the
         check, verifies every flag at source (each verified flag either becomes a real
         recovery lead in TODO or an exception row — never left ambiguous). Cities from
         the 2026-07 expansion wave already have body ids + quirk notes in their
         pmn_backfill/CLAUDE.md — seeding is mostly transcription; the ORIGINAL 13
         expanded cities' pmn_backfill datasets predate some conventions — verify their
         body lists during rollout.
      4. **Looped hardening**: systemic findings go to `scripts/pmn_crosscheck_HARDENING.md`
         (the roster_HARDENING.md pattern) and harden the shared engine, not per-city
         forks; per-city facts stay in the config CSVs.
      5. **Fold into `/refresh-city`** as a mandatory post-probe step once the pilot is
         clean: refresh runs the check, surfaces crosscheck_report.md in its output, and
         a human/Claude review gate decides promotions (never auto-ingest, constraint (a)).
      6. **Cadence learning**: keep successive crosscheck_flags.csv files (dated) — 2–3
         refresh cycles of them measure each city's real PMN attachment lag for free;
         revisit the 60-day window per city after that.
- [ ] **[TAIL/routine] Re-run /audit-city-data periodically** (or after any large ingest) — the skill
      at .claude/skills/audit-city-data/ is the QC harness; write reports to _audits/.

## [GATED] Infrastructure

- [x] **`normalize_motions.py` CLI hardened to strict argparse — DONE 2026-07-20.** Five
      agents in a 24h window (see the 2026-07-19 self-reported `--help` incident under the
      minutes-promotion wave) accidentally triggered a full 31-city sweep by passing an
      unrecognized arg — the old `main()` filtered `--`-args out and defaulted `cities = args
      or CITIES`, so **any** unknown flag (`--help` included) silently swept every city.
      Converted to strict `argparse`: `--help` prints usage and exits 0; an unknown arg
      errors (exit 2, "unrecognized arguments"); a **bare invocation no longer sweeps** — it
      requires an explicit `--all` (which also regenerates `crosswalks/`), or one/more city
      slugs. Preserved exactly: `normalize_motions.py <city> [city …]` (single/multi-city, no
      crosswalk regen), `--report`, and the unknown-city error. Call sites: the only
      programmatic caller, `scripts/rebuild_derived.py`, passes a single slug (unaffected);
      every doc/refresh-harness reference that relied on the bare sweep was updated to `--all`
      — `SETUP.md`, `crosswalks/README.md`, `cities_db_SCHEMA.md`, `refresh_status.md`,
      `scripts/refresh_lib.py`, `scripts/refresh_status.py`, the 3 per-city `fetch_new.py`
      rebuild-hint prints (ssl/herriman/cottonwood_heights), and 22 per-city README/CLAUDE
      rebuild-step lines. Tested: `--help` exit 0, unknown arg exit 2, bad city exit 2, bare
      exit 2, `<city>` works, `--all` sweeps + regenerates crosswalks, `--all <city>` conflicts.

- [ ] **NO VERSION CONTROL — put the repo under git (decoupled from publishing)
      (raised 2026-07-29).** `/Users/tysonwelsh/civic-data` is not a git repository. A
      multi-GB, heavily-derived corpus with a 3,300-line change ledger is currently
      protected only by dated `_backups/` directories, a hand-kept TODO/HANDOFF narrative,
      and the "don't touch shared files while another instance is running" convention.
      **Concrete risks already recorded in this repo, not hypothetical:** (1) last-writer-wins
      clobbers between parallel Claude instances — `NEXT_SESSION_PLAN.md` names the exact
      shared-file set (`registry/*`, `gov.db`, `coverage.json`, `scripts/db_build_lib.py`,
      `scripts/build_cities_db.py`, `TODO.md`) and says "no git; last-writer-wins clobbers";
      (2) the 2026-07-19 `normalize_motions.py --help` incident, where five agents in 24h
      each silently swept all 31 cities — recovery there meant regeneration, not a revert;
      (3) no way to diff a derived-layer rebuild against its predecessor except the
      expected-rows-only discipline done by hand. The cardinal rules lean hard on
      "regenerate, never hand-edit" — git is what makes that claim auditable.
      **This is the URGENT half of the GitHub item below and does NOT require publishing
      anything**: `git init` + a PRIVATE remote is a separate, much smaller decision than a
      public repo linked from municipalsky.com. Do that first; the publish decision can wait
      indefinitely behind it.
      **Shape** (reuse the `.gitignore` already worked out below — raw PDFs/video under
      `*/raw/`, `_backups/`, both `.env` files, `.DS_Store`, `__pycache__`): the same ~800 MB
      text layer, private remote, no site integration, no README rewrite for a public
      audience. Verify no secrets in the tracked set before the first push (the .env files
      carry ANTHROPIC_API_KEY). Open sub-questions to settle at init time: whether the
      per-entity `.db` files and `gov.db` are tracked (binary, regenerated every build — a
      case for ignoring them and tracking only the CSVs/markdown they derive from) and
      whether `_backups/` pruning follows the first good commit.
      **Interim state 2026-07-29: owner took a manual local backup** — that covers the
      catastrophe case but not the diff/revert/attribution case, which is the one that
      actually bites during multi-agent waves.

- [ ] **Publish to GitHub as its own repo, linked from municipalsky.com** — plan agreed
      2026-07-02, execution deferred by owner ("not quite yet" — confirm before doing).
      **⚠ See the version-control item directly above — `git init` on a PRIVATE remote is
      the urgent, separable half; this item is only the PUBLIC/publishing decision.**
      The decided shape:
      - A **separate repo** under tysonwelsh (name TBD, e.g. `civic-data` or
        `municipalsky-civic-data`) — NOT inside the municipal-sky-site repo (that repo
        is only ~53 MB tracked; reasons: FTP publish flow would drag the data toward
        Bluehost, different change cadences would churn site history, and a standalone
        repo is a better citation identity).
      - Commit the text layer only (~800 MB: markdown, CSVs, JSON, dbs, weeks/,
        scripts, docs). `.gitignore`: raw PDFs/video under `*/raw/` (5.2 GB; 11 files
        exceed GitHub's 100 MB hard limit), `_backups/`, **both `.env` files (contain
        ANTHROPIC_API_KEY — verify no secrets in the tracked set before first push)**,
        `.DS_Store`, `__pycache__`. Keep raw *text* artifacts (e.g. provo packet_txt/).
      - `sources.csv` / `SOURCES.md` per city serve as the public references layer;
        raw PDFs stay local-only and re-fetchable.
      - Site integration afterward: a "Data" page on municipalsky.com linking the repo;
        optionally curated derived extracts copied into the site's `data/` at publish
        time — never the whole corpus.
      - After git init, `_backups/2026-07-02/` (192 MB) can eventually be pruned.
      Also unblocks Claude Code web sessions on this repo.
- [x] **cities.db / coverage.json / sources regeneration discipline** — DONE 2026-07-07
      (REFACTOR_PLAN 4.5): `python3 scripts/rebuild_derived.py <slug>|--all` is the
      one-command chain (db → referrals → weeks → motions_std → sources → validate →
      coverage → cities.db incl. the FTS search layer); refresh-city + remediate-city-data
      skills point at it.
- [x] **Standardize the CF vision cache-key convention — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** sha1(index path)[:8] normative (sub-filing pipe variant); 281 caches / 7 cities migrated with dry-run collision check; post-migration 21/21 CSVs byte-identical; SKILL.md defensive text shrunk.** (added 2026-07-07, REFACTOR_PLAN
      5.7 deferral): per-city `build_finance.py` drivers key `vision/*.json` caches
      differently (`sha1(index path)[:8]` vs `document_id`), forcing cf-vision-transcribe
      to re-learn it per city. Pick one convention in `scripts/campaign_finance/driver.py`,
      migrate/rename existing caches, verify every city's rebuild reproduces its CSVs
      byte-identically, then shrink the skill's defensive text.
- [x] **✅ DONE 2026-07-19 (LM wave): all 35 remaining filings visioned (queue was 35 not 47 — 12 pre-cached); regime-aware cycle_totals shipped in the shared lib (15→8 rows, annuals excluded, Johnson override intact). Taylorsville campaign-finance: finish the vision pass + regime-aware cycle_totals
      (2026-07-06).** Structured money layer built (`taylorsville_form` family; 3 CSVs;
      validate PASS 0 fails, 37 warns = filings still awaiting vision). This city's fillable
      PDFs have a TEMPLATE text layer with HANDWRITTEN figures, so MOST filings need Read-
      vision. Done this turn: 8 election-cycle 2021 filings (Johnson ×3, Knudsen ×3, Overson
      ×2 — the contested D5 race + Mayor) + 3 typed all-zeros annuals.
      **STILL NEEDS VISION — election-cycle first (13):** 2021 Barbieri pre_general(doc6920)+
      final(doc7001), 2021 Harker pre_general(doc6916)+final(doc7003); ALL 2023 (Barbieri /
      Cochran / Burgess × 1st+2nd+final = 9). **Annual (47):** all remaining (parallel stream;
      lower priority). 1 partial: 2026 Harker doc11783 has a typed $200 expenditure TOTAL but
      its itemized ROW is field-glued — vision it for the row. Method: `cf-vision-transcribe`
      skill (Read tool, $0 API), cache `vision/<docid>.json`, then rebuild + validate.
      **KNOWN FLAG (do not "fix"):** 2021 Johnson primary (doc6712) expend won't reconcile —
      the filer wrote a Winco item as "4299" with no decimal (≈$42.99); kept verbatim/flagged
      per anti-fabrication. A documented `finance_overrides.csv` row is the only sanctioned
      correction if ever desired.
      **THEN:** run `cycle_totals.py` REGIME-AWARE (filter `filing_regime=='election_cycle'`)
      so the 50 annual March-1 statements never enter a race total — cycle_totals.py needs a
      small change to read filing_regime (now a trailing col on filing_totals.csv). NOT run yet.

## Three new cities (south_jordan / millcreek / taylorsville) — 2026-07-06 follow-ups
Base builds + expansion + CF structuring all COMPLETE (16 cities; $0-API Read-vision). Deferred:
- [x] **[med] Taylorsville CF annual backfill + regime-aware cycle_totals — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** real money surfaced in ~10 annuals (Overson 2025 $11,500) — regime-excluded from race totals; 27 received-stamp dates; NEW dup found (Overson doc8378≡doc10635; genuine 2024 annual unpublished — follow-up (f)).** — 47 mandatory-annual March-1 statements acquired but itemization deferred (parallel stream, not race totals); election-cycle layer done (20/21 reconcile). Make `cycle_totals.py` filter to `filing_regime='election_cycle'`.
- [x] **[med] Millcreek IN-PACKETS comment harvest — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** see the main millcreek comments item above.** — PC agenda packets bundle verbatim resident letters (Provo pattern); packets/index pins them via `retained_raw_path` → build `public_comments/all_comments_clean.csv`.
- [x] **[med] Millcreek cycle_totals basis — ✅ **DONE 2026-07-19 (LM wave — full record in the LARGE+MEDIUM EXECUTION WAVE entry).** 9 CUMULATIVE-column cycle_overrides (Silvestrini 2019 $88,369/$64,860; 4 wrong non-flagged rows also caught; Keller/Holz verified correct).** — Millcreek Dec "summary" reports are per-period (cumulative only in the cover box), so the default summary=cumulative rule is wrong; treat as fully-incremental. 4 review-flags to check.
- [x] **[low] CF review-flags — ✅ DONE 2026-07-19 (pv-tierb-low wave).** Spot-checked every still-flagged reconcile gap in all three cities against the vision caches (row-sum vs the filer's printed cover total re-computed by hand); **all HONEST, no pipeline defect, no override written, all three `cycle_totals.csv` byte-identical after re-running `cycle_totals.py`.** Per-city dispositions written into each `campaign_finance/CLAUDE.md`. **south_jordan** (5 filing-level reconcile flags; cycle_totals has 0 cycle-level flags): all category-(a) honest filer arithmetic (cover total ≠ sum of own itemized rows) — Barrett 2025 Mayor doc8746 (live summary, expend Δ−3.53, the only one feeding a cycle total, kept city-faithful); the other 4 (Ramsey 8620 −2.00, Johnson 5063 −3155.29, Bevans 5061 −45.72, Lewis 8519 +10.00) sit on superseded/re-filed interims that build drops (n_live=1) → never enter a total. **millcreek** (11 filing flags + Keller 2019 D3 cycle flag): all already-documented (in-kind-excluded cash-only convention for Vice+DeSirant, amended/no-activity restatements, small source deltas; Keller flag is SPURIOUS — her summary is a cumulative restatement); the 9 CUMULATIVE-column cycle_overrides remain the sanctioned totals. **taylorsville** (2 filing flags + Johnson 2021 D5 cycle override): Burgess 2017 doc10669 (blank source contrib total) + Harker 2022 doc10615 ($200 totals-only, Attachment A empty) both honest; Johnson override balance-chain-verified. Backups: `_backups/2026-07-19-pv-tierb-low/cf-flags/`.
- [x] **[low] Millcreek 2017 canvass merge — ✅ DONE 2026-07-20 (pv-tierb-low wave).** The
      recovered PMN 2017-11-21 Board of Canvassers (general-election returns; seated D2 Marchant,
      D4 Uipi) was PROMOTED from `pmn_backfill/` into the audited `meeting_minutes/` layer:
      new markdown `minutes/2017/2017-11-21/...board-of-canvassers-general-election-returns.md`
      + `minutes_index.csv` row `source=pmn`/`source_url`=PMN file URL (the murray PMN-promotion
      convention). `extract_votes.py` (no `--force`, so the 2017 en-dash work is untouched)
      emits its **2 tally-only motions** (Other + Procedural/Administrative, both `Pass
      (unanimous)`, blank member/vote) — identical shape to the audited 2019-11-19 canvass.
      Identity cross-confirmed (2019-12-16 council minutes adopt these very "November 21, 2017"
      canvass minutes, Item 5.1). all_votes.csv delta = **exactly +2 rows, 0 removed**; 2017
      named-vote count byte-stable at 362. Derived chain rebuilt (normalize_motions/build_db/
      build_referrals/build_weeks — db INTEGRITY OK, motions 3035→3037); `validate_city.py`
      **26 PASS / 0 WARN / 0 FAIL**. The F-1 2017 en-dash re-extract was already completed
      2026-07-19 (see the Millcreek F-1 item). Backup `_backups/2026-07-19-pv-tierb-low/p4-millcreek/`.
- [x] **[low] Fold expand-city-sources vendor recipes into that skill's notes — ✅ DONE
      2026-07-19 (pv-tierb-low wave).** All 7 folded into `.claude/skills/expand-city-sources/SKILL.md`
      at the section an executing agent would look, verified against repo precedent; backup
      `_backups/2026-07-19-pv-tierb-low/skill-recipes/`. Landings: (1) **municipalcodeonline.com S3
      back-catalog** → §3 ordinances "Where" (path-style `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/<slug>/…`,
      dotted bucket breaks virtual-host TLS — keep path-style; verified `white_city/sources.csv` 136 docs)
      + bottom gotchas one-liner. (2) **@UtahRecord/OpenUtah mirror + audio-only §5 branch** → §5
      transcripts (mirror covers the YouTube→Swagit gap, robots-limited metadata-only; audio-only
      branch = mirror then owner-gated Whisper over PMN/Streamline MP3s; verified west_jordan
      transcripts/AVAILABILITY.md + taylorsville TODO). (3) **AgendaCenter `UpdateCategoryList` +
      ViewFile packet path** → §1 packets portal list (CivicPlus/CivicEngage AJAX per catID×year →
      `ViewFile/{Agenda,Minutes,ArchivedMinutes,AgendaPacket}/<id>`; verified SSL recon.md/packets/CLAUDE.md/sources.csv)
      + bottom one-liner. (4) **PMN-as-ordinance-archive when code host is 403** → §3 ordinances 403
      paragraph (harvest "Notice of Ordinance" PMN attachments as independent corroborator,
      within_source→medium upgrade; verified TODO body-1788/720 harvests). (5) **CivicEngage
      current-cycle-only packet pages** → §1 packets (no historical archive → Wayback lead; verified
      taylorsville TODO). (6) **mandatory-annual CF regime → `filing_regime` column** → §6 campaign
      finance (election_cycle vs mandatory_annual; cycle_totals.py filters to election_cycle; verified
      build_finance.py + filing_totals.csv trailing column). (7) **tesseract can't-read-/tmp +
      non-UTF8-stderr** → §4 EXTRACTION DISCIPLINE OCR bullet (OCR into scratchpad not /tmp; capture
      stderr with errors='replace'; from the Orem OCR pass) + bottom one-liner.

## [DONE 2026-07-12, T1.2] SLCo election normalizer drops county-straddling precinct labels (found 2026-07-11, Draper build)
**FIXED.** `PRECINCT_RE` in the archive normalizer now accepts optional leading county-ID
digits (`25DR01`); the dropped Utah-county Draper precincts flow into the canonical long file
(**Walker 5454 → 5910, exact match to Draper's audited races.csv**; +24 general +15 primary
rows — the 2025 PRIMARY had the same hole; all other years byte-stable). Also fixed the side
effect: all-`25DR` sheets used to fall through to the Family-A fallback and emit junk
`contest='Sheet2'` rows — that fallback is now blocked for generic `SheetNN` tabs, and the
Aspen Peaks school-board contest parses properly. Rebuilt long file + by_contest + refederated
`election_result`. Straddle audit: 25DR were the only foreign-ID-prefixed precincts in the
2025 SOVC (Draper is the only county-line-straddling SLCo city). Original finding below.
*(original)* The `slco_municipal_results_long.csv` normalizer's precinct regex silently DROPS
Utah-county-vintage `25DR0N` precinct labels, UNDERCOUNTING 2025 Draper council/mayor
races by ~600 votes.

## Draper verification follow-ups (found 2026-07-11, Draper VERIFICATION.md)
- [x] **[low] Draper 2025-08-26 Board of Canvassers extraction miss** — the meeting's named
  roll-call grid (Resolution #25-42, ceremonial primary canvass: Green/Johnson/T.Lowery/Vawdrey
  Yes, F. Lowry Absent) was NOT captured by `meeting_minutes/extract_votes.py` (non-standard
  canvassers header). 1 motion / 5 vote rows, no legislative impact. Patch the extractor to
  recognize the canvassers format, then re-extract + rebuild db/weeks. (VERIFICATION.md §7.)
  **DONE 2026-07-19:** root cause was the **"Board Member"** mover/seconder title (the GRID rows
  still print "Councilmember", so the grid parsed once the motion was detected) — added
  `Board\s*Member` to `NAME_PREFIX` + a guard skipping a "Board Member"-moved motion with no grid
  (the pro-forma tally-only adjournment). Re-extracted: diff **exactly +1 motion / +5 vote rows**
  on 2025-08-26 (Green/Johnson/T.Lowery/Vawdrey `Aye`, F. Lowry `Absent`, `4-0 Pass`), all 150
  other meetings byte-stable; rebuilt normalize_motions/db/referrals(5 medium, override still
  binds)/weeks. Backups `_backups/2026-07-19-pv-tierb-low/draper/`. (VERIFICATION.md addendum 2026-07-19.)
- [x] **[low] Draper 2021 election rows are RCV, labelled plurality** — 2021 was Draper's
  Ranked-Choice Voting pilot. `election_results/draper_races.csv` stores `voting_method=plurality`
  with FIRST-CHOICE tallies; the winner (Tasha Lowery, council) is correct but `winner_pct`
  (36.95%) is a first-choice share, not the RCV final. Annotate the 2021 rows' `voting_method`/
  `note` (mirror the Millcreek RCV caveat) so downstream can't read the pct as a final margin.
  (VERIFICATION.md §10.) **DONE 2026-07-19:** fixed at the SCRIPT layer (`clean_elections.py` —
  the CSV is script-generated) via an `RCV` set + `NOTE` entry; regenerated. Diff touches **only
  the 2021 council-general row**: `voting_method` plurality→`ranked choice (RCV)` + a `note`; winner/
  tallies/margins unchanged; by_candidate/by_precinct byte-stable. The 2021 mayor row (single
  candidate, uncontested) stays plurality. Docs updated (election_results/CLAUDE.md +RCV section,
  main CLAUDE.md, VERIFICATION.md addendum 2026-07-19).

## Riverton — 2 dropped roll-call votes from page-header split (found 2026-07-12 audit)
Riverton council `extract_votes.py` drops a member's vote when an injected running-header
line splits the member name from their vote value mid-roll-call: 2020-05-14 m1 (Kent
Hartley — Aye) and 2023-03-09 m2 (Keith Breinholt — Aye). Both motions still PASSED
(outcome unaffected); this is a member-attribution loss, not an outcome error. Same bug
CLASS as Herriman's form-feed roll-row split. Fix: make the roll-row parser tolerant of an
injected header/form-feed line between name and vote, re-extract (--force), rebuild derived.
Low severity (2 rows); audit verdict was SHIP.

## Midvale — 1 duplicated roll-call motion (found 2026-07-12 assembly)
Council 2025-08-19 m1 ("Approve the Consent Agenda", 5-0) captured the 5-member roll call
TWICE -> 10 rows for 5 people in meeting_minutes/all_votes.csv (outcome correct). db_build_lib
collapses the identical dupes so the db is right (5 votes), but the flat CSV has 5 spurious
duplicate rows. Fix: dedup identical (member,vote) within a motion in the Midvale extractor,
re-extract. Only 1 of 675 council motions affected. Also note: "Dustin Gettel" votes as a
COUNCILMEMBER 2022-2024 then became Mayor (roster council->mayor transition, like Herriman's
Hales) — not an over-count; "Mayor Stevenson" is the 2023-era mayor.

## Holladay — 10 duplicated PC roll-call rows (found 2026-07-12 closeout audit)
Holladay planning_commission/all_votes.csv has **10 duplicate (source,motion_no,member) rows**,
ALL member "Layton", across six 2022 PC meetings: files 870741 (m1-m4), 934075 (m1), 934073
(m1-m3), 934057 (m1), 934053 (m1). An early-2022 full-name PC roll printed Layton's name twice,
so the extractor emitted the row twice. Same CLASS as the Midvale dupe. db/civic.db is correct
(the vote (motion_id,person_id) UNIQUE collapses them -> 2,702 votes; CSV named rows 2,712),
outcomes unaffected. Fix: dedup identical (member,vote) within a motion in the Holladay PC
extractor (planning_commission/extract_votes.py), re-extract --force, rebuild db/weeks/motions_std,
re-federate cities.db. Low severity (10 of 610 PC rows); closeout verdict was SHIP.
Deferred second item: promote/recover the PC **2020/2021/2023** minutes (89 rows in
planning_commission/minutes_unrecovered.csv) — never posted to PMN body 389; would need the city
Revize Document Center / SuiteOne portal (recon.md §b). Honest upstream gap, not a scraper miss.

## Midvale — council two-column roll-call defect FIXED (2026-07-12)
The council extractor now handles the 2020-2023 two-column roll-call layout (recovered +33 named
motions / +187 vote rows; fixed the 2020-03-24 m7 and 2020-05-05 m14 [Mayor Hale tie-break]
outcome inversions). Remaining minor: the PC extractor's Erikson/Erickson name variant is
un-normalized (out of scope of the council fix); fold on next PC pass. The 2025-08-19 "dupe"
was a FALSE ALARM (two distinct same-day meetings), per audit — no action.

## Bluffdale — core build shipped 2026-07-12; follow-ups
Core build (minutes/votes/comments/elections/geo/db) verified + audited SHIP (23 PASS / 2 WARN / 0 FAIL; _audits/audit_2026-07-12.md). Deferred, non-blocking:
- **Expansion layers ✅ ALL SIX BUILT + FEDERATED 2026-07-13** (`expand-city-sources`, PASS each):
  packets (217 index-only full packets, 132 CC + 85 PC), housing_plans (11 docs incl. standalone MIH
  element Ord. 2022-15/2023-04), ordinances (150; 68 high / 75 within_source / 3 med / 4 none),
  pmn_backfill (entity 87 / council body 373; repo is a complete SUPERSET, 0 recovered), transcripts
  (CivicClerk video, 0 captions → 15 unrecovered; Whisper proposed), campaign_finance (106 filings
  2017-2025, 100% election-join — **ACQUISITION ONLY**, not in cities.db until a structured layer is
  built). Reusable skill notes banked: CivicEngage packets ride under the `Agenda` doc-type by
  "PACKET" title-keyword; CivicClerk transcript-discovery via the `/v1/Events` caption fields.
  **STILL OPEN follow-up:** structure the CF dollar layer (like the other CF cities); the 2 land-use
  `none` ordinances (2020-06 signs, 2023-29 Draper boundary) are extraction leads — their minutes
  motion omitted the ordinance number.
- **Rolling roster/ layer ✅ BUILT 2026-07-12** (`update-council-roster`; the first new-city-wave roster —
  17 cities now federated). 15 tenures (13 high / 2 medium / 0 low) across 6 seats: cohort A ×3
  (Kallas/Gaston/Hales 2020-01-06 → Austin/Wilding/Lord 2024-01-10), cohort B ×2 (Aston 2018→, the
  ex-Jackson seat: Crockett 2019-special → Crockett 2021 → Smith 2026-01-05), MAYOR (Timothy pre-floor →
  Hall 2022-01-04 →). All four oath ceremonies minutes-anchored; idempotent; `non_voting_mayor=True`
  (Hall's Council role rows are chair votes, not membership). **Independent adversarial audit PASSED
  every check** (`roster/AUDIT.md`) and PROVED a pre-existing elections defect from the raw SOVC: the
  **2019 4-YEAR contest was VOTE-FOR-3** (4,977 candidate votes vs 2,154 ballots — impossible under
  vote-for-2) — `clean_elections.py` N_SEATS corrected 2→3 + regenerated (**Mark Hales is_winner now
  True**; runner-up Preece; margin 112; federated `election_race` refreshed). Audit F2/F3 nits applied;
  3 systemic items logged to `scripts/roster_HARDENING.md` (E1 ballots-cast ceiling validator, C3
  reverse-crosscheck exceptions, S2 mayoral-participation allowlist). Jackson's pre-floor vacancy is a
  documented honest gap (pre-2020 minutes not held).
- **Referral layer spot-check + precision-tune** (db/civic.db): 269 links (189 high / 69 med / 11 low) is high vs peers (Taylorsville 28, South Jordan 13). Run the audit skill's 'dump-mediums-weakest-first, eyeball, tune' pass; treat medium/low as flag-only until then. build_db.py DROPS the referral table - do not rebuild casually.
- **LBA stage cross-tag (cosmetic):** the 22 LBA motions carry stage='mba_vote' in db (MBA bucket reused). body split Council/RDA/LBA is correct; optionally add an lba_vote stage in build_db.py. Filter LBA by body_id, not stage.

## [DONE 2026-07-12] Kearns 2017-2023 township COUNCIL minutes harvested from PMN body 5823
**Resolved.** Enumerated all 255 body-5823 notices; 111 township meetings carry a "Meeting Minutes"
attachment. **Harvested 85** (2018-07-09 → 2023; 84 `.pdf` + 1 `.docx` via `textutil`; OCR where
scanned) → council on disk now 117 files / 492 motions, range 2018-07-09 → 2026-05. `convert.py`
gained a `.docx` + `raw_stem` path; `extract_votes.py` gained a scoped `parse_rollcall` (some
2018-2023 minutes print full named roll calls → 32 named council vote rows, contested motions 1→5)
and the township roster now includes **Ruby Brown**. `minutes_unrecovered.csv` rewritten to 41
genuine rows and `SOURCES.md`/`README`/`CLAUDE`/`VERIFICATION` corrected. **Remaining honest gaps:**
25 township meetings 2017-01 → 2018-06 whose Meeting-Minutes attachment WAS published but whose PMN
file blob is **purged** (`file_id` < ~450000 → 404 at `/pmn/files/`; notice link stale; not on the
Internet Archive) — recover only if PMN restores those pre-mid-2018 blobs; 7 meetings that posted
only agenda + MP3 audio (never minuted); 9 recent not-yet-posted. One edge case logged: the
2022-11-14 notice has a date-named `11-14-22.pdf` mis-filed under category "Audio Recording" (not
"Meeting Minutes") — left unharvested per the strict category rule; verify + promote if it is in fact
minutes. NOTE the PC 2017-2018 gap is DIFFERENT and GENUINE (agenda+packet only). db/weeks
regeneration + cities.db refederation pending (orchestrator). Original finding below.

### (original finding) Kearns 2017-2023 township COUNCIL minutes are on PMN but NOT harvested (found 2026-07-12 audit) — FIX-FIRST
The build logged 111 council rows in `kearns_city_council/meeting_minutes/minutes_unrecovered.csv`
with a `reason` claiming the 2017-2023 metro-township council posted "only agendas + MP3 audio
(minutes genuinely absent)." **This is WRONG.** The 2026-07-12 verification/audit fetched 6 PMN
notices spread across 2017-2023 (2017-01-18, 2017-02-15, 2018-12-17, 2020-10-12, 2021-10-11,
2023-10-12) and **6/6 carry a written "Meeting Minutes" attachment** on PMN council body 5823
(`.docx` for 2017, `.pdf` after — e.g. 011817.docx, 021517.pdf, 12-17-18.pdf, 10-12-20.pdf,
10-11-21.pdf, 10-12-23.pdf). So ~102 township council meetings' minutes are **recoverable**, not
absent; the council record on disk currently begins 2024-01, losing 7 years of primary source.
`fetch_new.py` re-flags this backlog on every run. **FIX:** harvest all body-5823 notices 2017-2023
(notice ids are in the `source_url` column of `minutes_unrecovered.csv`) → pull each "Meeting Minutes"
file → add a **docx→text** path for the 2017-era `.docx` minutes (pdftotext won't read them) → carve
votes → rebuild `db/` + `weeks/` → then CORRECT `minutes_unrecovered.csv` (drop the recovered dates,
keep only genuine no-minutes meetings) and REGENERATE `SOURCES.md` (its "audio-only" note is now
falsified). Grade: council minutes dataset is C on completeness until done. NOTE the PC 2017-2018 gap
is DIFFERENT and GENUINE (2/2 sampled PC notices = agenda+packet only; approved PC minutes truly begin
2019-03) — do not "recover" those. See `kearns_city_council/_audits/audit_2026-07-12.md`.
Minor also-flagged: fold PC person `Thomes`(1)→`Thomas` (Gray Thomas); CRA in-recess body (PMN) not
acquired = 0 rows (acquire only if CRA analysis is wanted).

## Copperton — core build shipped + closeout-audited 2026-07-12; two nice-to-have follow-ups
Verification/audit SHIP (grades A/A-; `copperton_city_council/_audits/audit_2026-07-12.md`,
`VERIFICATION.md`). Unlike Kearns, the reported **2017-02→2018-06 council gap is GENUINE** — 40+ of
the referenced 2017-2018 PMN body-5831 attachment file-IDs return HTTP 404 (retention purge; audio
gone too) while 3 recovered controls (459667/459671/522659) return 200. Do NOT "recover" these.
Deferred (neither blocks anything):
- **(a) Enrich `meeting_minutes/minutes_unrecovered.csv` `candidates`** with the real purged PMN
  file-IDs surfaced this audit (e.g. 2017-02-15→315659.pdf, 2018-06-20→413287.pdf, …) instead of the
  current guessed filenames (`pmn:02-15-17.pdf`). Provenance polish only; the 404 verdict stands.
- **(b) Exhaustively enumerate PC body-1560 notices** to close the ~80 unsampled dates. `fetch_new.py`
  surfaces ~100 PC notice dates vs 18 indexed minutes; sampling (23/23) found them to be ~150-word
  CANCELLATION agendas / staff packets, NOT missed minutes (Copperton's PC cancels most meetings —
  thin-by-design). A full sweep would formally confirm 18 == all-held-meetings. No misses found.

## [RESOLVED 2026-07-12, T1.2] SLCo canonical election file "CORRUPTED for Kearns" (found 2026-07-12, township build)
**Re-diagnosed at source; both claims resolved differently than filed.** (1) 2019 Kearns was
NOT dropped — the rows existed under the sheet-code contest name `KRN Council N`, invisible to
a `%KEARNS%` filter, AND carried garbage candidates ("Vote By Mail") from the archive's wrong
layout family; both fixed (new `parse_family_b()` upstream + era-variant CITY_PATTERNS
downstream) — 2019 Kearns now federates correctly (**KRN Council 3: BUTTERFIELD 273 / BROWN
127 — EXACT match to kearns_races.csv**). (2) The 2025 "merged OTHER municipalities'
candidates" claim was a **FALSE ALARM**: CACHE DEXTER + CHRISTOPHER JAMES GEERTSEN are
legitimate Kearns 2025 mayoral PRIMARY candidates (raw primary workbook Sheet8 header lists
all four), correctly tagged `election_type='municipal primary'` — a query that didn't split
election_type read them as contamination. Verified 0 non-KRN precincts under any Kearns
contest. `("kearns", [r"KEARNS", r"\bKRN\b"])` is now IN CITY_PATTERNS (the district-body
guard keeps KEARNS IMPROVEMENT DISTRICT / Oquirrh Park out); Kearns federates 35 by_contest
rows. Original finding retained above for the record.

## New-city-wave rosters — 9 of 14 built + federated 2026-07-13; 5 residual
`update-council-roster` batch (parallel forks; several forks died on the 11:50pm session limit and
were re-run after reset). **BUILT + validated + idempotent + federated** (roster layer 17→26 cities,
term 385→542): **at-large** draper (16), alta (11); **district (tie-break/non-voting mayor)** murray
(24), riverton (17), midvale (19), south_salt_lake (24); **district (VOTING mayor — fleet's first)**
herriman (16), cottonwood_heights (15), holladay (15). bluffdale (15) done earlier. Each has a
`roster/CLAUDE.md`; systemic `roster_lib` findings consolidated in `scripts/roster_HARDENING.md`
(2026-07-13 entry: precinct `source_year` sidecar workaround, vote-outside-tenure-window sentinel,
reverse-crosscheck exception classes, estimated-switch-date confidence).
- **[✅ DONE 2026-07-13] 5 township→city HB35-seam rosters BUILT + federated** — white_city (20),
  copperton (18), kearns (19), magna (17), emigration_canyon (16). **Roster layer now 31/31 city-town
  entities** (term 632). Seam modeling: kearns 5→4 district restructure (township chair-Mayor Bush on
  D5 → abolished; city Mayor Valdez VOTES) — fixed a terminal-abolished-seat `end_date` bug via a
  documented `roster_overrides.csv` row (chain_end_dates blanks the last tenure; see roster_HARDENING
  H-F); magna presiding-officer VOTE-FLIP (township voting chair-hat on a district member → non-voting
  2026 exec Mayor Sudbury; `non_voting_mayor=True`, validate() enforces empty mayor bounds); emigration
  peer-selected voting mayor overlaid on the mayor's at-large seat. All validate + idempotent.
- **[med] murray/riverton/midvale precinct layer SKIPPED** (their `geo/precinct_to_district.csv` lacks
  `source_year`; rosters valid without it) — add the `_precinct_to_district.csv` sidecar (the
  herriman/CH/holladay pattern) to emit `district_precincts.csv` for these three.

## Votes-pipeline extraction defects flagged by the roster builds (2026-07-13)
Found while reconciling vote-bounds against tenures; queued for a `db/` extraction fix (NOT fixed
from the roster — cardinal rule).

**⚠ WORKED 2026-07-29 (4 parallel agents, all verified at source) — THE FRAMING OF THIS WHOLE
SECTION WAS WRONG. Only ONE of the three vote items was an extraction fault.** The section
header says "extraction defects"; in practice the vote-window sentinel fires for four different
causes and the heading pre-committed every entry to the wrong one. Two were the source telling
the truth and the extractor faithfully reproducing it — exactly the reading `roster_lib.py`'s
sentinel message discouraged. **`scripts/roster_lib.py:437` was reworded the same day** to
enumerate all four causes and require a primary-document check before anyone assumes extraction.
Lesson worth keeping: *a name outside its tenure window is a QUESTION, not a diagnosis.*

- **[x] ✅ NOT A DEFECT — Holladay `gibbons` ×4 (closed 2026-07-29).** All four rows are printed
  VERBATIM in the approved minutes, on the same boilerplate "move out of Closed Session" motion
  (2024-02-15 :729, -03-21 :483, -04-25 :690, -12-12 :342, under `minutes/2024/`). Cause is an
  upstream **clerk error** — the 2023 slate pasted forward in the closed-session template; the
  clerk DID update Gibbons→Gray on 2024-09-19/-10-03/-10-24 and throughout 2025, which is what
  makes the stale ones diagnosable. **Retained verbatim per cardinal rule 2.** `all_votes.csv`
  byte-identical (2,476 lines); the correct fix removed NOTHING. Also found: a 5th instance this
  entry missed (`seconder=Gibbons`, 2024-06-13) and a stale ATTENDANCE line on 2024-02-15.
  The "7th name over a roll-of-6" claim was wrong — no motion exceeds 6 named rows; 7 was a
  per-MEETING distinct-name count. Documented in `meeting_minutes/CLAUDE.md` ("Known SOURCE
  error") + `roster/CLAUDE.md` + `roster/build_roster.py`, so no future agent deletes real rows.
- **[x] ✅ FIXED — Alta, but it was a BODY mislabel, not a phantom name (2026-07-29).** Both
  flagged rows are real and printed. `meeting_minutes/extract_votes.py:698` stamped `body=BODY`
  (module constant `"Council"`) on every motion, but an Alta council-minutes PDF routinely
  minutes MORE THAN ONE MEETING: the **Budget Committee** (Mayor + 2 councilmembers + the staff
  **Treasurer**) meets immediately before Council under `CALL THE BUDGET COMMITTEE MEETING TO
  ORDER`. So Heimark's 2022-23 votes were genuine **Budget Committee** votes mislabeled Council —
  he was a real voting member of that body as Treasurer. Fix: `body_walk()` (the documented
  slc/holladay/herriman in-file body pattern); only an explicit header switches bodies.
  `all_votes.csv` 1,159 rows before AND after, **0 added / 0 removed, exactly 10 changed cells,
  all `body`**. Heimark's Council `role` now starts 2026-01-14, matching `council_terms.csv`.
  **Sheridan Davis 2024-02-14 is NOT pipeline noise** — verified against source PDF p.10: the
  APPROVED minutes print "Councilmember Davis – yes" though he left at the 2024-01-10 seating of
  Schilling, and the roll three paragraphs earlier names Schilling in that slot. A **clerk
  transposition in the primary document**; retained verbatim (substituting Schilling would be
  inference, not record — and `vote_overrides.csv` cannot express a wrong-PERSON correction).
- **[med] Draper `election_results` acquisition gap:** the 2025 regular 2-seat 4-year Council race was
  CANCELED-uncontested (Res #25-49; Tasha Lowery + Mike Green certified without a ballot) → absent from
  the Salt Lake County SOVC. Add these certifications so the winners aren't invisible to the crosschecks.
  *(Untouched 2026-07-29 — the only item in this section that is still open as written.)*
- **[x] ✅ FIXED — Emigration Canyon Gary Bowen (2026-07-29), though NOT via "agenda-text false
  positives".** He genuinely attends every city-era meeting as the **Salt Lake County Animal
  Services Representative**, printed under `Others Present:` — same name, different capacity;
  he even gives reports. Real cause: `meeting_minutes/extract_votes.py:168` took a fixed 500-char
  window after the `MEMBERS PRESENT` anchor and credited any roster surname in it, running
  through the `Staff Present:`/`Others Present:` sub-blocks — an **attendance-block over-reach**.
  Fix: `NONCOUNCIL_BLOCK_RE` + `trim_to_council_block()`, cutting at the first non-council label
  **only when a roster surname already precedes it** — load-bearing, because the township-era
  minutes are TWO-COLUMN and a blind cut would have deleted the entire council from ~30 docs
  (verified: 63 township-era files, 0 with an empty `present`). Bowen `last_seen` 2026-04-21 →
  **2021-12-14**, `n_meetings` 46 → **37**; 9 of 89 meetings changed, 9 names removed, 0 added,
  full council intact on every one. **Vote layer was never affected** — `all_votes.csv` MD5
  identical (`1e5a815…`); no Bowen row past 2021-12-14 in any capacity.

## 2026-07-31 snapshot — HANDOFF.md (verbatim, pre-restructure)

# HANDOFF — resume point (as of 2026-07-29, correctness + normalization pass)

> **⭐ LATEST (2026-07-29): a CORRECTNESS/NORMALIZATION pass, not an acquisition pass. No new
> entities. 8 work items closed, TODO.md restructured, gov.db re-federated 3×.**
>
> **LIVE DB STATE (verified post-federation, all gates green):** motions **49,172 city /
> 27,269 county / 959 regional / 1,208 state** · votes **181,119 / 38,597 / 0 / 27,887** ·
> **`motion_std` 77,400** (city 49,172 + county 27,269 + regional 959; ut_state deliberately 0)
> · ordinance **7,550 rows / 5,480 linked** · coverage.json **44 entities** (was 31) ·
> FK 0 · integrity ok · `validate_entity.py --federation` → **44/44 in step**.
>
> **NEW TOOL — run this before trusting any gov.db number:**
> `python3 scripts/validate_entity.py --federation` (exits 1 if any entity db is ahead of
> gov.db). Built because gov.db had silently sat **~3,000 motions stale** since 2026-07-26 —
> the 07-25/26 audit fixes were built into entity dbs and never federated, so every county
> query for three days was wrong. It compares row counts PLUS a content digest (catches a
> value-only repair). It fired correctly in production the same day.
>
> **WHAT CLOSED:** (1) TODO High-priority **(j)** `motion_std` for the non-city tier —
> **computed AT FEDERATION** (`compute_motion_std_noncity()` in build_cities_db.py, importing
> `classify` from normalize_motions.py so tiers can't drift); the tier has no uniform flat-motion
> shape and mag_mpo/ut_state have no motion CSV at all. City rows byte-identical (sha1
> `f0c6627…`). Honest classification ceilings per entity, caveat-carried: weber 8.6% → **mag_mpo
> 61.1%**. (2) **(k)** coverage.json now covers all 44 registry entities on their own terms
> (db-less counties get `(no vote layer)`, MPOs measured as projects/projections, registered-only
> as `built:false`); city section byte-identical. (3) **(h)** cache ordinance links — **all 10
> were dangling**, see below. (4) **(h3)** cache duplicate double-count. (5) TIER 5 cache
> provenance. (6) the federation-staleness gate. (7) `/build-county-data-repo` hardened
> (SKILL.md 177→388 lines + new `EXTRACTION_TRAPS.md`). (8) 5 suspect ordinance links → ~64
> corrected.
>
> **⭐ THE TWO FINDINGS THAT MATTER MOST TO A FUTURE SESSION:**
> 1. **`motion_id` IS NOT STABLE ACROSS RE-EXTRACTION — never hand-write one.** cache's
>    2026-07-26 OCR backfill inserted 1,505 motions into an EARLIER era, renumbering every id;
>    all 10 hand-written ordinance links slid onto unrelated motions (ORD 2022-18 →
>    *"adjourn from the Council meeting at"*) while still flagged `motion_resolution='unique'`,
>    i.e. **quotable**. Correct links before the repair: **0 of 10**. Now DERIVED
>    (`cache_county/db/link_ordinances.py`). It passed its first real test the same day: removing
>    107 duplicate motions shifted every 2021+ id by ~14 and **all 17 links re-derived onto the
>    identical physical motion**.
> 2. **A screen that flags WRONG values is blind to SUPPRESSED ones.** 5 links repo-wide showed
>    the "linked to a procedural motion" signature; **all 5 were wrong (0/5 — the prediction that
>    "most are probably correct" was the error, not the screen)**. But fixing the DERIVATION
>    recovered ~64 links total, because the same bug had been blanking correct links as
>    "ambiguous" where the spurious tie was always an adjourn motion (weber **198 → 247**).
>    When a linkage bug appears, **re-derive and diff the whole entity** — don't fix flagged rows.
>
> **TODO.md IS RESTRUCTURED — read its new preamble first.** Every section now carries a BUCKET:
> **[DEBT]** (~9, the only real queue) · **[WATCH]** (5, monitoring — ends only if a source
> appears) · **[OPTION]** (15, choices not debt) · **[GATED]** (4, owner decisions) ·
> **[TAIL]** (22, fold into the quarterly refresh). **The open-checkbox count is NOT work owed.**
> Definition of done is a STATE: every entity passes `validate_entity.py --federation`; every
> ceiling is caveat-carried IN THE DB; no doc asserts what the db contradicts.
>
> **⚠ RANKING LESSON (now in the TODO preamble + memory):** four items filed as "votes-pipeline
> extraction defects" were worked in parallel — **only ONE was.** Two were the SOURCE telling the
> truth, faithfully extracted (holladay: a clerk's stale closed-session template naming a departed
> member; emigration_canyon: a county Animal Services liaison sharing a councilmember's surname
> under `Others Present:`); one was already fixed. Meanwhile the LOWEST-ranked item ("a date typo
> on one ordinance") was the day's biggest find. **The backlog's priority ordering was unreliable
> in BOTH directions — spot-check one entry at its primary document before working a section.**
>
> **OPEN DECISIONS FOR THE OWNER:**
> - **`git init` (private remote) — the largest latent risk, still unaddressed.** A full day of
>   changes (two shared-script rewrites, four extractor fixes, new derived linkers, regenerated
>   coverage.json) was protected only by dated `_backups/` dirs. TODO Infrastructure has the
>   entry; it is DECOUPLED from the public-publish question.
> - ut_state is **PAUSED** pending the STATE TIER reevaluation (owner ruling 2026-07-29): its 264
>   BILLS sit in the `application` table and it has ZERO purpose-built tables, vs wfrc_mpo's four.
>   Its roll-call layer is a genuine fit and should stay — the imposition is in the MATTER layer.
>
> **NEXT (highest value first):** (a) the 2 extraction defects from the ordinance pass — weber's
> unextracted 2019-07-30 motion (mid-roll amendment defeats the extractor) and midvale's 3
> mis-dated duplicate meetings (Revize `M DD YY` parsed as `MM D YY`; NOT catchable by the
> index-membership sweep — needs a date-collision detector); (b) `git init`; (c) the [DEBT] bucket.
> **Do not start a new acquisition wave before (a).**

# HANDOFF — earlier resume point (as of 2026-07-21, post-package)

> **POST-PACKAGE ADDENDUM (2026-07-20 late night → 2026-07-21, same session):** (1) the
> **MPO published-reports corpus** was built + federated at owner request (44 docs
> FTS-live — wfrc 28 / mag 16; adopted RTP narratives, TIP + Federal Obligation Reports,
> conformity, CEDS, Wasatch Choice, TLC award rollups naming 16 repo cities; TODO's
> WFRC-native entry has the record). (2) The **WFRC-NATIVE HOLISTIC PACKAGE was drafted
> at owner request and AWAITS OWNER GO** (TODO entry: Workstream A project-lifecycle
> spine / B influence machinery / C deliberative record — C's reports piece done ahead).
> (3) The **three honest residuals** of Phases 4–6 are recorded as a TODO item (content
> menu still open; post-build audits of the 9 new entities = ranked next; county-skill
> lesson absorption). (4) Owner-facing analyses demonstrated from the new layers
> (read-only, nothing written): planning-assumptions-vs-behavior (Draper 17.5% rezone
> denial vs +102% assigned HH growth; South Jordan 4.9% vs +107%), TIP slippage across
> 8 vintages (25% of multi-vintage projects slip ≥1yr; I-15 1800 N $90M→$385.5M), and
> the 1300 East full-stack briefing (pin 15908: $3.9M→$15.7M, 4 vintages stalled in
> Scoping; corridor rezone denials 2021+2026 had NO effect on this grant but bear on
> the corridor's FUTURE transit-Core-Route funding — RTP2027 watch candidate, not yet
> queued).

> **⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ LATEST (2026-07-20 late night, same session): PHASE 6 IS EXECUTED —
> THE ENTIRE OWNER-AUTHORIZED PHASES-4–6 PACKAGE IS COMPLETE.** The repo is now a
> **4-tier, 42-entity system federated into `gov.db`** (the cities.db→gov.db RENAME is
> done, sequenced last as directed; cities.db = back-compat SYMLINK refreshed by every
> build — all gates verified through it). Phase-6 deliverables: wasatch_county
> registered (Park City's 2nd within edge live); `registry/HIERARCHY.md` generated
> (`scripts/build_hierarchy.py`); `scripts/validate_entity.py` (entity-aware, delegates
> cities to validate_city.py; first full run over all 11 non-city entities = 0 FAIL and
> it CAUGHT the summit/mag legislative-minutes FTS absence — fixed, +349 docs);
> refresh-city + audit-city-data skills made entity-aware (additive; no city procedure
> invalidated); root README/CLAUDE.md rewritten with every number live-verified
> (files-win fixes: election_race 655→680; fts_minutes 13,852/40 entities). FINAL STATE:
> motions 49,172 city / 24,346 county / 958 regional / 1,208 state · votes 181,119 /
> 35,318 / 0 (tally-only source ceiling) / 27,887 · election_race 680 + election_result
> 5,482 · regional_project 5,717 · projection 10,952 (3 grains) · FK 0 / integrity ok /
> 193-31 / reconciliation exact / coverage.json byte-stable. TODO's Phase-4/5/6 entries
> carry the full dated records + every queued follow-up (headline queue: the 8-city
> election re-point package (A), the county/state follow-up classes (B)–(F), Phase-5
> residuals, and the backlog: remaining 22 counties + SL-County-cities-next per owner).
> Backups: `_backups/2026-07-20-phase4|phase5|phase6/`. **WHAT REMAINS: the owner-gated
> queue (GRAMA, Whisper, GitHub publish→municipalsky.com, LegiScan account, scope
> decisions), external watches, routine maintenance (quarterly refresh early Oct 2026),
> and the queued follow-up packages — headed by TODO's "PHASES 4–6 PACKAGE — the three
> honest residuals" item: (1) the County content menu (still open, no county has the
> enrichment modules), (2) post-build AUDITS of all 9 new entities (ranked the most
> valuable next non-owner-gated work), (3) folding the Phase-4 sharp edges into the
> /build-county-data-repo skill before the next county build.**

> **Earlier (2026-07-20 night, same session): PHASE 5 IS EXECUTED +
> FEDERATED — the repo's first REGIONAL (wfrc_mpo, mag_mpo) and STATE (ut_state)
> tiers are live, incorporated ON THEIR OWN TERMS (owner directive: MPOs are
> data-forward, never vote-shaped city clones — caveat rows + a memory now encode
> this).** 39 built entities; cities AND counties byte-stable; integrity ok / FK 0 /
> 193-31 / reconciliation exact. New: **`regional_project` 5,717 rows** (wfrc 8 TIP
> vintages + RTP-2050; mag TIP/RTP/RPO), **projection 3-tier** (regional 9,832 rows
> at city-area grain ANNUAL 2019–2050 — both MPO forecasts proven control-totaled
> to Gardner V2022), **ut_state 1,208 roll calls / 27,887 NAMED legislator votes**
> (264 land-use bills, 2015–2026, 0 tally mismatches, public le.utah.gov channel —
> no accounts created; LegiScan = owner-gated alternative), **+309 advisory
> opinions + 218 LUDMA statute sections FTS-live** (fetched via Wayback CDX — the
> state hosts are Cloudflare-walled now). Headlines: the **2025 LUDMA
> recodification** (10-9a→10-20, 17-27a→17-79 — repo docs cite the OLD numbering;
> Phase-6 doc-sweep candidate); a shell-page HTML-comment trap that would have
> fabricated ~2,200 fake legislator votes was caught + the real 2025/26 floor votes
> recovered; federated vote vocabulary extended with verbatim 'Yea' (views treat
> Aye/Yea as affirmative — source values never rewritten). Follow-ups queued in
> TODO's Phase-5 entry. Backups: `_backups/2026-07-20-phase5/`. **NEXT: Phase 6**
> (entity-aware skills, hierarchy index, wasatch_county, README/CLAUDE rewrite,
> the cities.db→gov.db rename sequenced LAST).

> **Earlier (2026-07-20 afternoon→evening, fresh instance): ENTITY-TIER
> PHASE 4 IS EXECUTED + FEDERATED — all 6 footprint counties built value/effort-gated
> and live in cities.db.** Flow: pending ALT-pseudo federation flush (step 0) → 6-scout
> recon wave + SLCo CLAUDE.md refresh (Phase-3 residual) → posted tier gate (utah FULL /
> weber+cache+summit MID / washington LIGHT+ / juab CHEAP-ONLY) → 18 build agents, one
> conflict-planned wave (Opus default, **5 Fable elections normalizers** per the owner's
> agent policy) → 5 closing agents → solo stage-C (registry db_rel_path/portal fills; 3
> small shared-script edits, backed up; ONE federation). 30 agents, 0 FAIL; survived 1
> transient API error + a 7-agent session-limit interruption via transcript resumes.
> **Federated: 36 built entities · county motions 24,346 / votes 35,318 (utah
> 10,089/2,765 · weber 4,242/12,105 · summit 3,346/518 · cache 1,812/11,788 · SLCo
> unchanged) · election_result 5,482 across ALL 7 counties · projection 980 · gis_layer
> 135 · development_application 864 · ordinance 7,542 · fts_minutes 12,392 · the 31
> cities BYTE-COUNT-IDENTICAL (49,172/181,119/680) · 193-31 · FK 0 · integrity ok ·
> reconciliation exact · coverage.json proven unchanged.** Headlines: weber+cache
> minutes carry FULL NAMED rolls (99.6%/97.5% — richer than SLCo); weber's
> never-published 807-instrument adopted-ordinance register reconstructed from minutes
> (73% vote-linked); utah's posted "2023 SOVC" = the 2022 SOVC UNSUPPRESSED (county
> error, quarantined); utah 2023 RCV contests absent from SOVC → recovered from rcvis;
> cache overrides recovered 5 buried dissents (contested 178→182); weber Ord 2025-27
> dissolved OVPC+WWPC into one countywide PC (Ogden Valley incorporation fallout);
> summit closer killed a fabricated cross-body identity bug. **Re-point evidence banked
> for 8 cities** (park_city 49/50, st_george 11/11 + 13 byte-identical raws, utah-4
> 52/52, logan 2023+, ogden except-2023) — queued as follow-up (A) in TODO's Phase-4
> entry, with follow-ups (B)–(F) (CMS-migration PC backfill, OCR depth backfills,
> elections residue, smalls, the PMN JSON-POST harness lead). Backups:
> `_backups/2026-07-20-phase4/`. **NEXT: Phase 5 (WFRC/MAG MPOs + ut_state) and Phase 6
> (entity-aware skills, hierarchy index, wasatch_county, the cities.db→gov.db rename +
> doc sweep — rename sequenced LAST), both owner-authorized in the same 2026-07-20
> decision.**

> **Earlier (2026-07-19→20, fresh-instance session): the ENTIRE REMAINING
> NON-OWNER-GATED QUEUE IS EXECUTED + FEDERATED — leads (p)–(v), Tier-B, the standing
> low list, AND a full bonus wave of every actionable residual (≈30 agents across 6
> conflict-planned waves; 4 transient API interruptions, all resumed clean; one
> federation per package + a final one).** Federated: motions **54,029** / votes
> **189,261** / contested **3,853** / election_race **680** / integrity ok / FK 0 /
> 193-31 / reconciliation exact. Highlights: **nephi +57 council motions** (the 2025
> "made THE motion" grammar gap) + its **confirmed-real Sept-2023 primary** adopted
> from the official Juab canvass (races 7→8; "no 2023 primary" claims corrected);
> **the 7-city election-pipeline re-point EXECUTED** (slc/sandy/WJ/WVC/SJ/taylorsville
> derive from the county canonical, byte-identity-gated, redundant raws deleted;
> millcreek = documented exception — sole holder of its 2016 founding election;
> taylorsville's blocked gate exposed + adopted a genuinely-missing **2019 D1
> primary**); slc adopted the recovered **2019 municipal primary** (8-way Mayor);
> the 2019 **ALT-council pseudo-candidate residue** root-fixed at the archive
> normalizer (the dropped real candidates recovered: Davis 77/Morgan 69/Lenches 29);
> lead (v) Cumulative rows + lead (q) ogden `doccenter_draft`/`packet_carve`
> provenance tags landed; **riverton's missing-second-motion class fully closed**
> (6 motions across 3 surgical rules); **herriman 2022-02-09 real minutes recovered
> from PMN** (+13 rows; PrimeGov's minutes slot was never populated); CH +67
> seconders (pleading-gutter digit-bleed); logan +6 motions (2 grammar gaps);
> vineyard +20 oversize RDA meetings (+71 motions) + Ord 2021-12 = clerk-typo
> linkage fix; orem +7 RDA/MBA OCR meetings (a PMN date-mislabel caught); millcreek
> 2017 canvass promoted + born-digital upgrade proven a verified negative (142
> probes); park_city consent "gaps" verified honestly-unseparable; **CF**: WJ-2021
> backfill verified complete, `is_incremental` now empirically per-candidate in the
> shared driver (WVC Lang $54.97→**$10,244.85** page-proven; Cochran double-count;
> + a REAL sandy/orem stale-key regression fixed — 65/63 false supersessions), all
> locked figures byte-stable; election URL provenance = **0 unrecorded rows
> repo-wide** (111+10 byte-verified URLs; canonical-pointer rows for all
> canonical-derived cities); the 6 dormant reset-pattern classifiers batch-guarded;
> ogden referral guard PORTED to referrals_lib (opt-in params; 31-city byte-identity
> sweep 0 diffs); normalize_motions: 62 recommend-rows de-ceremonialized + 16
> emergency proclamations reclassified (78-row exact diff) + **strict CLI** (bare
> runs refuse; `--all` explicit — ends the accidental-sweep trap that fired 5×);
> nephi footer/CRA, slc Puy note, park_city F7 all-benign, CF review-flags all
> honest, vendor recipes folded into the skill. TODO: every executed item carries a
> dated check-off; stale boxes (T1.3, 12-docs, SJ/mill/tay expansions, CF umbrellas,
> SLC Laserfiche ceiling) closed with evidence. Backups:
> `_backups/2026-07-19-pv-tierb-low/`. **WHAT REMAINS IS *ONLY*: the owner-gated
> queue, external-event watches, and routine maintenance** (see "What remains").
> New open leads created this session (all small, non-blocking): referral-guard
> enable-elsewhere (per-city evidence review), the WJ/tay/SJ/sandy/WVC/SLC
> prior-geometry acquisition (lead (o), owner-gated), lehi 2024-25 caption recovery
> (Whisper-only — videos delisted), millcreek even-year SOVC acquisition to unblock
> its re-point exception.

> **Earlier (2026-07-19 late night): the LARGE+MEDIUM EXECUTION WAVE IS
> COMPLETE + FEDERATED — the entire non-owner-gated large/medium TODO queue,
> 24 agents in 3 conflict-planned waves, every agent 0 FAIL, ONE federation.**
> Federated: motions **53,871** / votes **188,723** / contested **3,844** /
> integrity ok / FK 0 / 193-31 / reconciliation exact; coverage regenerated.
> **Headline: ogden's "~60-row" 2020–2023 PC gap was 63 WHOLE MEETINGS — all
> recovered** (PC 445→988 motions, contested 54→149, 100% approval-chain-
> verified, 3 new 2020 commissioners rostered). Also landed: CH + herriman
> **append-only-ingest conversions** (destructive paths guarded — `--ingest` is
> now the refresh step for BOTH); all four **CF typed-money tranches** (CH 2021
> layer lit up; midvale Gettel 2025 Mayor → $32.3k; herriman Basham; magna
> bundles per-candidate) + the **CF shared-lib polish** (truthful basis labels,
> finance_overrides wired, regime-aware cycle_totals, **vision cache keys
> standardized** — 281 caches/7 cities, byte-proven) with every locked
> adjudicated figure verified unchanged; st_george gutter/joint gaps (+the real
> 3:2 failed hillside rec); millcreek F-1 (+362 named 2017 Ayes) + in-packets
> comments layer (9 letters, honest floor) + 9 CUMULATIVE-column cycle fixes
> (Silvestrini 2019 → $88.4k); alta +9 wrapped-glyph Ayes; EC dropped-motion
> recovery; ordinance backfills across slc/WJ/WVC/orem/park_city/st_george
> (WJ 26-29/30 = TABLED, WVC 26-26/27 = DENIED — honest); all four latent name
> gates byte-identical-proven; WVC+SLC pre-2022 maps reconstructed and
> **millcreek's 2016 boundary now AUTHORITATIVE (medium→HIGH — and the dissolve
> reconstruction proven materially WRONG there: validation lead queued for the
> other 6 cities)**; roster_lib H-A..H-H closed; per-city `v_contested` now
> mirrors the federated split-column shape in all 31 dbs. NEW follow-ups
> (a)–(k) queued in TODO's **LARGE+MEDIUM EXECUTION WAVE entry** (Franklin-St
> referral re-key, roster adjudications from the new sentinel, Brooks Jones
> index row, boundary-validation channel, etc.). Backups:
> `_backups/2026-07-19-lm-wave/`. **UPDATE (same day, second automode wave): the
> follow-ups (a)–(k) are ALL EXECUTED too** (10 agents, 0 FAIL; survived a
> mid-run session-limit interruption via transcript resume; re-federated clean —
> 53,871/188,723/3,844/193-31; millcreek comments 9→27; murray lot-draw + SSL
> oath seams fixed HIGH with sentinel zero; all 17 H-C drifts = cited exceptions;
> the 6-city prior-map downgrade to LOW; plan-aware address lookup live,
> confidence-gated). NEW leads (l)–(o) queued in the TODO wave entry (copperton
> seat-lettering owner Q; slc 2019/2021-D2 elections-defect; EC latent reset;
> six-city prior-geometry acquisition). What remains is now essentially the
> owner-gated queue + Tier-B smalls + leads (l)–(o). **SECOND UPDATE (same day):
> post-ingest AUDITS ran on the two big ingests — ogden PC backfill PASS (A−),
> park_city PC B+ — and both ranked fixes LANDED same day (ogden "wit" roll +9
> named rows; park_city dotted-page-token fix, PC 872→873 + 6 healed results).
> Lead (m) FIXED: the slc 2019 winner rows + 2021 D2 Puy/Palmer swap were real
> defects reaching the audited races file — root-caused (stale pre-family-B
> slice; live family-C suppression bug), fixed at the archive layer, 9 races
> corrected, all 4 H-C exceptions retired. Lead (n) FIXED (EC guard; 6 more
> dormant scripts found → new lead (p)). Re-federated: 53,872 / 188,732 / 3,845 /
> integrity ok / 193-31. Remaining leads now (l), (o)–(v).**

> **Earlier (2026-07-19 night): the HARDENING BUNDLE IS COMPLETE +
> FEDERATED** (TODO's dated HARDENING BUNDLE entry has the full record).
> Crosscheck engine: body/description cancel-detection + cross-body dedup +
> rescheduled family (5-city regression clean). Refresh harness: dashboard
> probe-shape normalization (immediately recovered 2 missed white_city
> meetings), CH tolerant label matcher (+2 docs), herriman read-only --probe,
> WJ title-derived slugs. ⚠ CH's --fetch proven DESTRUCTIVE (like herriman's
> --build-md) — incident caught + fully repaired; BOTH cities' append-only
> conversion queued with doubled evidence — never use their full-build paths as
> refresh steps. Referral overrides migrated to STABLE app_keys (111 rows / 11
> cities, byte-equivalent proof). CF polish core: structured supersession
> markers + donor-classifier fixes — 29-city proof found 4 MATERIAL corrections
> (Loannides/Sloan surnames counted as candidate LOANS; self-funded figures now
> true). Federated: integrity ok / 193-31. Session note: the 200-subagent cap
> was reached — next agent waves need /fresh-instance or a raised cap.

> **⭐⭐⭐⭐ LATEST (2026-07-19 evening): the POST-REFRESH RECOVERY PACKAGE IS
> COMPLETE + FEDERATED.** The 🔴 **park_city PC parser gap is FIXED** — PC
> **602→872 motions / contested 30→52** (the folded-outcome grammar; pre-2024
> proven byte-identical; the "all unanimous-consent" read was itself an artifact:
> real named dissent existed in the missing motions); referrals +12. **slc
> 2022-08-29** = two genuine back-to-back sessions, both ingested (+6 motions;
> the old PMN copy was mislabeled). **ogden PC 2020-10-07 RECOVERED** (+16
> motions/+119 rows) — and the method generalizes: 🟢 **the whole ~60-row
> 2020–2023 ogden PC gap looks systematically recoverable** (new backfill-package
> lead). **lehi 0/3** — Granicus definitively exhausted with evidence (empty
> template / no clip / video-only) → GRAMA-only. Stale taylorsville OCR-upgrade
> item verified done-since-07-12 and closed. Federated: motions **53,302** /
> votes **185,316** / contested **3,748** / 193-31 / integrity ok / reconciliation
> exact; coverage.json regenerated. NOTE: this session hit the 200-subagent cap —
> further agent waves need a fresh session (`/fresh-instance`) or a raised
> `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`. NEXT (owner-authorized, in progress):
> the **hardening bundle** (crosscheck engine, refresh harness, referral-override
> keys, CF shared-lib polish) — executed solo/inline.

> **Earlier (2026-07-19): the Q3-2026 QUARTERLY REFRESH IS COMPLETE — the
> routine's FIRST FULL RUN (23 parallel city agents + one federation; every agent
> 0 FAIL).** 31/31 probes ok; all **75 crosscheck flags worked to zero**; **~62
> minutes docs ingested across 14 cities** → motions **53,010** (+343) / votes
> **185,111** (+1,762) / contested **3,726** (+26); integrity ok / reconciliation
> exact / 193-31 intact; coverage.json + refresh_status.md regenerated. Headline
> recoveries: slc's contested 6-1 COVID/mask-extension vote (Res 32 of 2021,
> Rogers Nay) + the FY26-27 budget formal; CH's PMN-mislabeled full council
> meeting (+88 rows); 3 lehi Granicus gap-leads confirmed recoverable. Seven
> city-local defects found+fixed (slc provenance-flip + ligature-dropped
> commissioner; provo's roster-dropped NEW commissioner; EC probe dedup; CH
> ledger header; SJ OCR-typo; WJ slug collision; herriman destructive rebuild —
> caught + reverted) and the SHARED `refresh_lib` in-batch dedup bug fixed +
> unit-tested post-wave (the doubled-votes class). 🔴 NEW HIGH ITEM: **park_city
> PC parser gap — 34 meetings' tally-only motions absent since 2024-10-09**
> (own work package: parser fix + re-extraction + audit). ⚠ CivicPlus platform
> outage (murray/sslc/MSD 500s, correlated — re-verify, nothing marked dead);
> lehi council lapse ongoing (~21 meetings). Full record + follow-ups (a)–(h):
> TODO.md **Q3-2026 QUARTERLY REFRESH entry**. Backups:
> `_backups/2026-07-19-q3-refresh/`. Next run: first week of October 2026.

> **Earlier (2026-07-18): the CF-STRUCTURING PACKAGE IS COMPLETE + FEDERATED —
> the owner-approved structured money layer now covers all 14 vision-cached wave
> cities (29 cities total).** Solo Fable pilot (midvale; shared `vision_lib.py` +
> `families/vision_cache.py` F10 + callable `dedup_mode`, no-op proven byte-identical
> on 3 existing cities) → 13 city-local Opus agents (one full relaunch round after a
> session-limit interruption — all died pre-write, verified clean) → cycle-totals
> byte-stability check → ONE federation. **cf_cycle 463→813 candidate-cycles /
> cf_contribution 18,834 / cf_expenditure 14,959 / cf_filing 1,843 across 29
> cities; 660 candidates, 211 person-matched; integrity ok / reconciliation exact /
> 193-31 intact.** All 14 validate_finance PASS, all cities 0 FAIL. Headline
> catches: holladay Fotheringham's dropped $17k final period (Mayor cycle now
> $49.8k/$50.2k), SSL Pinkney $3,075→$29,666 (YTD-not-sum), white_city Flint
> $0→$3,550 (the "not itemized" note was scanned-subset-scoped), murray Dominguez
> "2019 re-upload" = false alarm, riverton Buroker 100×-typo phantom contained.
> Full record + the OWNER ADJUDICATION QUEUE (un-forced ambiguous cycles) + vision
> tranches + shared-lib polish pass: TODO.md **CF-STRUCTURING PACKAGE entry**.
> Backups: `_backups/2026-07-17-cf-structuring/`.

> **Earlier (2026-07-17, night): WAVE-2 IS COMPLETE + FEDERATED — the shared-lib
> add-member override mechanism + a 21-agent city-disjoint wave (agenda-grade
> recovery, primary-docs residue, CF tranches 2+, wave-1 extraction follow-ups).**
> Recoveries: **west_jordan 27 of 28** missing 2020-21 PC meetings (NEW legacy
> city-site channel + NEW `citysite_minutes` provenance; PC motions 203→287),
> **CH 2024 PC hole CLOSED** (20 docs; delisted-but-live CMS via Wayback anchors)
> + bare-name-roll extractor fix (+130 named rows, NEW Weichers 4-to-1 dissent),
> **magna 4** COVID-cluster minutes (2 embedded in next-meeting packets),
> **midvale 1**; everything else verified DEAD or FALSE-POSITIVE and ledgered
> (12 cities, drafted GRAMA texts per city). Primary-docs residue CLOSED (draper
> 243; murray/SSL/bluffdale targeted packets; riverton Timberline = per-object
> auth-wall, 5 sibling rows corrected to `error:auth_wall`). CF: ~290 new vision
> caches — the tranche-1 six completed 2021/2023 + 8 NEW city layers (SSL,
> bluffdale, kearns, EC, alta, copperton, white_city, magna); riverton found a
> STATE MIS-PUBLICATION (Haymond's report under Pierucci's filename — cache
> deleted, re-acquisition queued); holladay "bradley" defect was a tranche-1
> MISDIAGNOSIS (corrected). SLC's 4 promoted minutes extracted (+20 rows; SLC now
> emits `provenance`). Phase 0 shipped the **vote_overrides ADD-MEMBER mechanism**
> (SSL Huff rows live; validator formula updated; park_city semantics proven
> unchanged) + the SSL **no-quorum minutes detector**. Federation: motions
> **52,667** / votes **183,349** / contested **3,700** / fts_packet **13,603** /
> 193-31 intact / integrity ok / reconciliation exact; coverage.json regenerated.
> All 21 agents + federation verified; every city 0 FAIL. Full record: TODO.md
> **WAVE-2 entry** (with 10 new follow-up classes (a)–(j)). Backups:
> `_backups/2026-07-17-wave2/`.

Start-here doc for the next session. Overwritten per session; the exhaustive record is
`TODO.md`, and per-area detail lives in `scripts/roster_HARDENING.md`, `_audits/`, and each
dataset's/roster's own `CLAUDE.md`.

## Read these first, in order
1. `CLAUDE.md` (root) — accurate for the 31-city + Salt Lake County repo (the provenance
   bullet now lists `citysite_minutes` + notes SLC emits the column, 2026-07-17).
2. This file's **"What remains"** below — the prioritized queue.
3. `TODO.md` — the durable, itemized record; every closed item carries a dated note.

## Where things stand (what's DONE)
- **Wave-2 (2026-07-17 night)** — see banner. Agenda-grade crosscheck tier worked to
  zero open flags in all 16 flagged cities; primary-docs residue closed; CF vision now
  covers every wave city's acquired scanned filings (2020-floor scope); wave-1
  follow-ups (a)(b)(c)(e)(f) all closed; add-member overrides live in the shared lib.
- **Earlier 2026-07-17** — PMN-crosscheck engine built + run (all 31) + fetchable-now
  tier promoted (48 records, 12 cities); repo-wide needs_ocr vision pass (261 rows);
  SLCo SOVC re-parse follow-ons; CF tranche 1.
- **2026-07-16** — minutes-promotion wave (13 cities, 2,189 recovered motions);
  primary-docs pilot (Sandy) + 30-city rollout, fts_packet live.
- **2026-07-12/13/14** — T1.1–T1.4 + T3.1 correctness campaigns; disposition layer;
  all-31 rosters; Tier-A expansion wave.

## What remains — prioritized

**As of 2026-07-20 evening: Phase 4 is DONE (see the top banner). The current
authorized work package is Phases 5–6.** Everything else below is owner-gated, an
external-event watch, or routine maintenance.

> **⚡ OWNER DECISION 2026-07-20 (standing): entity-tier Phases 4–6 AUTHORIZED.**
> ~~Phase 4 = the other 6 footprint counties~~ **✅ DONE 2026-07-20** (TODO Phase-4
> entry = the full record; follow-ups (A)–(F) queued there, incl. the 8-city election
> re-point package with evidence banked). ~~**Phase 5 = MPOs (WFRC/MAG board votes +
> RTP/TIP) + `ut_state`**~~ **✅ DONE 2026-07-20 night** (TODO Phase-5 entry = the
> full record + queued follow-ups; owner framing "incorporate on their own terms"
> is encoded in caveat rows + memory). ~~**Phase 6 = entity-aware skills
> (refresh-city/audit-city-data/validate_city.py), the `cities.db`→`gov.db` rename +
> doc sweep (sequence LAST), README/CLAUDE rewrite, generated hierarchy index,
> `wasatch_county` registration (adds Park City's 2nd `within` edge).**~~ **✅ DONE
> 2026-07-20 late night — the WHOLE PACKAGE is complete** (TODO Phase-6 entry = the
> record). Phase 3
> residuals: SLCo CLAUDE.md refresh ✅ DONE 2026-07-20; the county content-menu
> enrichments remain queued (TODO). **Agent policy: Opus subagents by default; Fable
> only where advisable** (elections normalizers proved this policy out — all 5 were
> Fable; shared-lib/schema changes and the rename stay Fable). Standing discipline
> unchanged (conflict-planned waves, backups, one federation per package, cardinal
> rules, dated TODO check-offs). (Watches: alta 2025
SOVC county lag; st_george 2025-10-09 + orem PC 2025-10-15 republication; taylorsville
2026-06-17 minutes; magna CRA approved-copy; lehi council publishing lapse
(GRAMA-only); ogden/logan/orem CF cycle publications; SLC 8 comment pages "retry with
newer models". Maintenance: quarterly refresh (early Oct 2026); periodic
/audit-city-data — the post-4a ingests (nephi +57, vineyard RDA +71, herriman,
riverton) are audit-eligible when convenient.)

### Next-highest-leverage work packages
1. **GRAMA queue (owner-gated outreach)** — wave-2 verified ~110 genuinely-unpublished
   minutes across 13 cities, each with a ready-drafted request (TODO wave-2 follow-up
   (a); bluffdale has a ready file `pmn_backfill/GRAMA_request_draft.md`). This is now
   the ONLY channel for those records (every public channel exhausted + documented).
2. **pmn_crosscheck engine hardening** — 5 independent confirmations this wave:
   body-text cancellation scanning, (date, repo_datasets) dedup, the
   "Meeting Rescheduled" family (TODO wave-2 follow-up (b)). Small, well-evidenced.
3. ~~**Owner-gated CF structuring**~~ — **DONE 2026-07-18**, and the **adjudication
   queue is RESOLVED same day** (owner-authorized evidence pass, 11/11 items +
   the Abundance registry check; 6 cycle figures corrected with evidence-cited
   overrides — headline: herriman's 2021 mayoral race was UNDERCOUNTED ~$8–11k per
   candidate; holladay Watts's spend was double-counting a $13k re-listed block;
   bluffdale Hall's spend was sign-flipped — re-federated, TODO entry (a) has the
   full record). What remains from the package (updated 2026-07-19 LM wave): 2
   small owner questions (Hall Dec-04-is-a-period; Tracy index-label fix) and the
   acquisition riders (Prazen, Pierucci, Robbins Oct-26, kearns/magna gap cycles,
   + magna Brooks Jones index row). The shared-lib polish pass AND all four
   typed-money vision tranches are ✅ DONE 2026-07-19 (LM wave — §10-3-208
   promotion surveyed + declined 0/15; cache keys standardized).
4. **Whisper/audio program (owner-gated, scope decision pending)** — the audio-only
   lead list grew substantially: st_george 2024-10-10, taylorsville ×3, copperton ×3,
   magna ×5 (COVID cluster), alta ×4, + magna flagged earlier as highest-value
   (TODO wave-2 follow-up (c)).
5. **Owner scope decisions still open** — lehi advisory-committee bodies; orem
   RDA/MBA/BoA promotion candidates (22 recovered docs, no repo layer).

### Tier B — bounded per-city cleanups
Wave-2 residue: draper 2 needs_ocr staff reports (re-fetch + vision); WJ PC roster
regeneration over the merged 2020+ span (optional); magna lower-confidence flags
(4 council specials + 2 PC 2019); pending re-checks next refresh (magna CRA 2026
dates + 2025-11-18 draft watch, st_george PC 2026-03-10, vineyard's 2
pending-adoption dates). Pre-existing: roster_lib hardening (H-A…H-H);
murray/riverton/midvale precinct sidecars; nephi/logan/vineyard leads; pre-2022
district geometry external fetches; millcreek in-packets comments + F-1 2017
en-dash re-extract; taylorsville 15 OCR-upgrade minutes + CF annual backfill.

### Tier C — maintenance
Quarterly refresh routine (UNBLOCKED — crosscheck is folded into `/refresh-city` §1b);
periodic `/audit-city-data`; CF vision cache-key standardization (holladay's collision
finding strengthens the case: trailing-hex keys collide, pure `sha1(path)[:8]` is safe).

### Owner-gated — DO NOT start without explicit approval
GitHub publish (→ municipalsky.com); Wayback archiving pass (raw-PDF backfill: ruled
OUT of scope by owner 2026-07-19 — processed text is saved, no re-fetch);
entity-tier Phases 4/5/6 (other counties, MPOs + state, entity-aware skills +
`cities.db`→`gov.db` rename); the Salt Lake County content menu; Whisper transcript
program (see queue above); GRAMA outreach (drafts ready, sending is owner's call);
below-floor CF tranches (murray 2017/2019, magna 2016–2019, 2017 handfuls elsewhere).

## Operational gotchas (carry these forward)
- **Every BUILT entity db MUST carry the standard `referral` table** (empty is fine —
  create it in the entity's build_db.py; the federator hard-fails without it; the
  cache_county incident 2026-07-20).
- **Non-city ordinance federation reads `<entity>/ordinances/index.csv` with a DIRECT
  entity-db-local `motion_id` column** (loader applies the fed_index offset;
  matched_motion_date/no is the CITY convention only). Keep code-codification catalogs
  OUT of index.csv (Weber keeps them in `code_sources.csv`) or they federate as junk
  ordinance rows.
- **Link-only catalog rows (no on-disk artifact, e.g. a StoryMap-only general plan) are
  legitimate** — build_fts now guards null paths; don't "fix" them by fabricating a text
  sidecar.
- **The PMN browser search is captcha/erroring; the working path is a JSON POST to
  `/pmn/searchresult.html` with an `X-CSRF-TOKEN` header** (params JSON-stringified;
  paginate via startingRow; publicBodyName exact-match does NOT match "Planning
  Commission" — filter client-side). Proven in the washington build.
- **County-db projections/gis/development loaders no longer gate on db_rel_path**
  (db-less thin counties federate those modules); election_result never gated.
- **`normalize_motions.py` has a STRICT CLI since 2026-07-20**: `<city>` for one city,
  `--all` to sweep + regenerate crosswalks; bare runs and unknown args (incl. the old
  `--help` trap) now ERROR instead of silently sweeping all 31 cities.
- **`referrals_lib.py` carries the ogden FP guard as OPT-IN params** (member_names /
  template_stopwords / content_veto / name_anchor_min) — defaults are a proven no-op
  (31-city byte-identity sweep); only ogden enables it. Enabling elsewhere needs
  per-city evidence review (open TODO lead).
- **Curated crosswalk rows go in `scripts/normalize_motions.py` CONSTANTS, never only
  the CSVs** — `write_crosswalks` regenerates `crosswalks/*.csv` from the in-script
  tables on every normalize run and silently drops CSV-only rows (the kearns-CRA /
  EC-Recuse incident, root-fixed 2026-07-19).
- **CH + herriman refresh = `fetch_new.py --ingest` (append-only).** Their full-build
  paths (`--fetch` / `--build-md`) are DESTRUCTIVE and now refuse without
  `--force-full-rebuild` (+auto-backup). herriman's `post_ingest` auto-chains
  extract → extract_backfill_votes → validate.
- **draper `link_text_sidecars.py` is now discard-row-SAFE (fixed 2026-07-19,
  byte-identical no-op proven)** — the old do-not-rerun caveat is retired.
- **The LOW-confidence pre-2022 maps (WJ/tay/SJ/sandy/WVC/SLC) never resolve
  addresses** — the plan-aware lookup is confidence-gated (only high/medium prior
  geometry resolves; today = millcreek's authoritative layer).
- **ogden PC has a documented `planning_commission/vote_corrections.csv`** (post-parse,
  evidence-cited, snippet-anchored) for the failed-motion both-lists-"aye" clerk-typo
  class — corrections go there, never in the minutes markdown.
- **After any `extract_votes.py` re-run, cities with an `extract_backfill_votes.py` MUST
  re-run it** (herriman would silently drop 949 pmn rows; run order documented per city).
- **PMN/portal labels lie — verify from in-body content**: wave-2 additions — magna
  minutes EMBEDDED inside the next meeting's approval packet; a CH "PC" doc that is a
  council work session; a state CF PDF containing the WRONG CANDIDATE's report
  (riverton Pierucci/Haymond); cancellations announced only in notice BODY prose.
- **Delisted-but-live-by-ID CMS docs (CH pattern):** a city CMS can drop a doc from its
  listing while still serving it by ID — Wayback captures of the LISTING page recover
  the anchors. Candidate `fetch_new` hardening.
- **Auth-walls can be per-object, not per-meeting** (riverton Granicus MediaManager):
  siblings on the same agenda fetch fine; the walled rows use `fetch_status=error:auth_wall`.
- **CivicEngage is Akamai-403 to plain fetchers** — urllib + archive-browser UA works
  (taylorsville).
- **vote_overrides.csv now has TWO kinds** (SCHEMA_SPEC reconciliation invariant):
  conflict-resolution and ADD-MEMBER; stale rows FAIL the build loudly. h.db formula:
  `expected = db_votes + conflict_overrides − add_overrides`.
- **`sqlite3 <path>` CLI CREATES the file on open** — resolve a city's db via
  `registry/entities.csv` `db_rel_path`; delete any stray `.db` (the `glob("*.db")[0]`
  landmine).
- **cwd reverts when a compound `cd … && …` command fails** — prefer absolute paths.
- **Run repo-level builders with ABSOLUTE paths**; confirm success by "integrity_check:
  ok" + "Search layer done (reconciliation exact)" (federation) / "Derived chain rebuilt".
- **CSV builders that glob `votes/*.json` resurrect stale JSONs** — delete a doc's JSON
  after removing it from an index.
- **Re-extraction renumbers motion_ids** — diff at the
  `(source_file, date, body, motion_no, member, vote)` level.
- **Never hand-edit generated roster CSVs** — edit the driver's `TENURES` or
  `roster_overrides.csv`.
- **Never run `build_cities_db.py` while any city agent is live** — one federation at the
  end of a work package (wave-2's protocol; it held again, 21 agents).
- **Sanity-check `v_council_current` after federating** (193 seats / 31 entities as of
  2026-07-17).

## Standing constraints (cardinal rules)
Never fabricate (honest gaps are data; drafts stay sidecars; a cancelled meeting is an
EXCEPTION, never an unrecovered row — the white_city/vineyard precedent; a mislabeled
source document is never transcribed under its label — the riverton Pierucci precedent);
city-faithful values are never overwritten (fixes go in extractors or documented override
files — the add-member override is the sanctioned path for a garbled-value missing
member); derived layers (`db/`, `weeks/`, `roster/*.csv`, `cities.db`) are regenerated,
never hand-edited. A defect found in another layer while working is FLAGGED (report +
TODO), never fixed from the wrong layer.

## 2026-07-31 snapshot — NEXT_SESSION_PLAN.md (verbatim; superseded 2026-07-16, retired today)

# NEXT SESSION PLAN — prioritized execution of the TODO backlog

> **⚠️ SUPERSEDED 2026-07-16 — read `HANDOFF.md` for the current queue.** Tier 1 (1.1–1.4)
> and Tier 3.1/3.2/3.3 below are ALL DONE (dated notes in TODO.md); the 2026-07-16
> minutes-promotion wave (13 cities) is complete + federated. This file is retained as
> the 2026-07-12 planning record only.

Drawn up 2026-07-12 after a full review of `CLAUDE.md`, `README.md`, `TODO.md` (797 lines),
`registry/entities.csv`, `coverage.json`, and the actual state of the code the top TODO
items target. This file is the ordered work queue; `TODO.md` remains the exhaustive record.
Work items top-to-bottom; check off in the task list and cross off in `TODO.md` as each lands.

## Context that reshapes the TODO (read first)

- **The repo grew 16 → 28 registered city/town entities + Salt Lake County** (registry/entities.csv),
  almost all added 2026-07-08..12 (draper, riverton, alta, midvale, cottonwood_heights,
  holladay, south_salt_lake, bluffdale, white_city, kearns, murray, herriman).
- **`magna`, `copperton`, `emigration_canyon` dirs exist but are NOT in the registry** — that is
  the in-flight "5 townships" build (another Claude instance, 2026-07-12). **Do not touch those
  three dirs, `registry/*`, `cities.db`, `coverage.json`, `scripts/db_build_lib.py`,
  `scripts/build_cities_db.py`, or `TODO.md` until that instance confirms done** — shared-file
  collision risk (no git; last-writer-wins clobbers).
- **README.md and CLAUDE.md still say "16 cities"** — stale; fixed in Tier 2.
- Every "15 other cities" / "16 cities" count in the TODO is now ~27 cities + county.

## Tier 1 — correctness bugs corrupting analysis right now

### 1.1 Centralize the `outcome_of` tally fix + `disposition` column into the shared lib  ✅ DONE 2026-07-12
**Executed + verified same day.** Shared lib fixed (tally-first `outcome_of`, disposition block,
hard tally guard w/ supermajority exemption, non-fatal recommendation cross-check); the 5
documented forks (millcreek, park_city, sandy, south_jordan, taylorsville) ported by parallel
agents + independently re-verified; `build_cities_db.py` federates the 3 disposition columns
(has_disp guard). `rebuild_derived.py --all` clean: **126 → 0 contradictions** across all 31
city dbs and federated cities.db; 40,090/45,728 city motions carry disposition; v_contested_all
3486; v_pc_divergence 1085/85. TODO items 1 & 3 annotated (kept [~] pending the 1.3 audit).
Scoped remainders: salt_lake_county disposition (Legistar build), legacy `recommendation`
reconciliation (deliberately deferred, matching SLC).
Merges TODO High-priority items 1 (disposition rollout) + 3 (outcome_of tally fix) +
the recommendation-reconciliation follow-up. **Scope is now far smaller than the TODO says.**

- **Root fact (code-verified 2026-07-12):** the 2026-07-07 refactor consolidated db building —
  **28 of 29 cities import `scripts/db_build_lib.py`.** Its `outcome_of()` (line 127) STILL has
  the original bug: keyword-only (`"fail"/"den" → Fail`, else `Pass`), never reads the yes:no
  tally. So the bug that flipped 21 SLC PC votes is **live in all 27 lib-consuming cities**.
  SLC was fixed only in its own private `slc_city_council/db/build_db.py` (`outcome_of` line 171,
  `disposition_of` line 217); `salt_lake_county/db/build_db.py` has its own correct
  tally-aware `outcome_of(passed)` (Legistar boolean) — leave it.
- **The fix is a single-point edit:** port SLC's corrected `outcome_of` + `disposition_of` into
  `scripts/db_build_lib.py`; delete SLC's local overrides so there is ONE implementation for all
  28 lib-consumers. Also derive PC `recommendation` from `_compose_dir(disposition, outcome)`
  instead of the keyword matcher (fixes the 13 mis-derived PC recs).
- **Then:** extend `scripts/build_cities_db.py` to federate the 3 disposition columns
  (`disposition`/`disposition_method`/`disposition_confidence`) into the federated `motion` table
  (currently an explicit column list — SLC's new columns are NOT propagated yet).
- **Execution:**
  1. (read-only, safe anytime) baseline: per-city count of motions whose stored `outcome`
     contradicts their yes:no / yes-no tally — the expected flip set.
  2. Edit `scripts/db_build_lib.py`; keep the HARD guard (build FAILS if any `outcome`
     contradicts a yes≠no tally). Handle both `:` (PC) and `-` (council/agency) tallies.
  3. `python3 scripts/rebuild_derived.py --all` (db → referrals → weeks → motions_std →
     sources → validate → coverage → cities.db + FTS).
  4. Diff outcomes vs the baseline — expect ONLY tally-contradicting flips; re-verify each
     city's contested / approve-deny / `v_pc_divergence` figures.
  5. Spot-check native result-string conventions per city before trusting (tally-only
     ceilings; st_george prose-in-`result`; sandy Legistar PC; colon-vs-dash tallies).
- **On completion:** in `TODO.md` mark items 1 & 3 done (rewrite their "port to 15 clones"
  framing to "centralized in db_build_lib.py"); note recommendation counts changed.

### 1.2 Fix the shared SLCo election-normalizer bugs (external archive)  ✅ DONE 2026-07-12
**Executed + verified same day; root causes differed from the TODO claims.** Archive
(`normalize_sovc.py`): PRECINCT_RE widened for county-straddling precincts (Draper 2025
Walker 5454→5910, exact match to audited; primary had the same hole); new `parse_family_b()`
for the 2018–2019 layout (candidate names above the sub-header — Family A had been reading
vote-method labels as candidates); SheetNN Family-A fallback blocked. Repo
(`build_elections.py`): era-variant CITY_PATTERNS (2019 sheet codes, 2011 Coun/CNCL/@ Lg,
abbreviated names), special-district guard, kearns added. County grain recovered: 2019
0→127, 2011 +120, 2017 +104; SJD/KRN 2019 exact-match audited files; refederated.
Corrected two misdiagnoses in TODO (SJ-2011 already parsed; Kearns-2025 "contamination" =
legitimate primary candidates). Honest remainders: 2019 municipal primary + 2018/2020
generals + 2002–2006 era still unrecognized archive layouts.
`~/Desktop/slco-election-archive/scripts/normalize_sovc.py` — **actively corrupts election data
for every new SLCo city as it is added**, so urgent given the live expansion.
- (a) County-straddling precinct-label drop: the precinct regex silently drops
  `25DR0N`-style foreign-CountyID precincts → **Draper 2025 council/mayor undercounted ~600
  votes** in the canonical `slco_municipal_results_long.csv`. Widen the regex to accept
  `<foreignID>` prefixes; rebuild the long file + refederate `election_result`.
- (b) `SJD`/3-letter sheet-code skip + 2011-general skip: build a sheet-code→city table; stop
  skipping 2011-general sheets. (South Jordan worked around locally; upstream still wrong.)
- Audit other straddling entities for foreign-ID-prefixed precincts in 2025 (Draper is the only
  known SLCo city straddling a county line).

### 1.3 Cross-city motion-classification audit  ✅ DONE 2026-07-12 (comprehensive, per owner)
**31 parallel per-city ground-truth agents (~500 motions vs source minutes).** Pre-fix verdicts
FAIL 6 / WARN 25 / PASS 0: ~55 wrong outcomes in 4 root causes (majority-first "failed N-M"
tallies, ties→Pass, holladay clock-time regex hits, item-fate 'Denied' inversions) + broken
continue-class recall in 14 cities + Table/defer noun traps. **v3 classifier landed same day**
(word-priority carriage + tie⇒Fail + clock-strip + disposition-composed 'den'; verb-anchored
disposition patterns + guards; sandy PC exception; provo extractor cue fix + re-extract).
Verified 37/37 + 45/45 unit, 26/26 audited rows, 38 word-over-tally = the audited population,
0 unexplained federated violations; continue 860→1,296, tables 655→433, Died 51.
Report: `_audits/2026-07-12-motion-classification/report.md`. TODO items 1/2/3 closed;
~15 upstream extraction defects queued in TODO ("T1.3 upstream extraction defects" — folded
into T3.1's scope). Original scope below.
*(original)* Cross-city motion-classification audit (TODO item 2 — GATED on 1.1)
After 1.1 lands repo-wide: ground-truth a random `disposition`/`outcome` sample per city vs
source minutes (esp. non-`high` confidence, `mixed`, NULL/unclassified buckets); confirm the
tally↔outcome hard-check and disposition∘outcome-vs-`recommendation` cross-check pass (0
unexplained) in every city; verify native result-string conventions were actually handled;
re-verify contested/approve-deny/divergence aggregates + federated reconciliation. Fold findings
into `/audit-city-data`. Do NOT close items 1 & 3 until this passes.

### 1.4 Extend referral/divergence to `Other`-typed legislative items  ✅ DONE 2026-07-12
Admitted historic district / landmark site / (small|station) area plan / master plan into
LANDUSE_RE (lib + 6 forks) + Historic District into NAME_TYPE; "historic preservation"
deliberately excluded (matches board appointments). +46 links / 11 cities; Yalecrest–Laird
Heights diverged=1 federated; SLC spot-check suppressed 4 FPs + design/review stopwords;
st_george's +21 all genuine. Details in TODO item 4 (now [x]).
*(original)* (TODO item 4)
Admit legislative `Other` items (historic-district designations, some master-/small-area-plan
actions the PC forwards) into the application universe in `db/build_db.py`, guarding genuinely
procedural `Other` motions. Re-run `build_referrals.py`; subject-matched links — spot-check
before quoting. Pairs with the `disposition` column (makes "PC said deny → Council approved"
directly queryable). Surfaced by the real Yalecrest–Laird Heights PC→Council divergence.

## Tier 2 — cheap, high-leverage clarity

### 2.1 Refresh top-level docs to the real entity count  ✅ DONE 2026-07-12
README.md + CLAUDE.md rewritten 16→31 cities + county: new intro (15-city wave + the five
HB35 township-origin entities, 2017 floors), 31-row city table (county/portal/meeting-day
per city, agent-gathered from each city's CLAUDE.md), 15 new per-city quirk one-liners in
CLAUDE.md (voting-mayor forms, county straddles, coverage cliffs, OCR seams, township→city
seams), new `disposition` analysis guidance, elections-expansion note (655 races / 22 SLCo
jurisdictions), federated counts (~50.6k motions / 175k votes / ~10k FTS docs), honest
scoping of roster + expansion layers to the ORIGINAL 16 (new-city versions queued).
Comments caveat recounted (7 cities with comments / 24 zeros). EC's own stale CLAUDE.md
noted in its quirk line.
Rewrite `README.md` + `CLAUDE.md` + README coverage-caveat list from "16 cities" to the current
28 cities + Salt Lake County. Fold in the new-city quirks already captured in
`registry/entities.csv` notes (voting vs non-voting mayors; township-to-city white_city/kearns;
Draper/Bluffdale county-straddle; in-session RDA/LBA/CDRA bodies). Regenerate any generated
listings. Low effort, high value for every future session and for citation credibility.

## Tier 3 — well-scoped data completion (batchable; mostly $0-API Read-vision)

### 3.1 New-city extraction cleanups (same bug CLASS — header/line splits & dup rows; all outcome-safe)
- Riverton: 2 dropped roll-call votes from page-header split (2020-05-14 m1, 2023-03-09 m2).
- Herriman: form-feed roll-row split (same class).
- Midvale: 1 duplicated roll-call motion (2025-08-19 m1) — dedup identical (member,vote).
- Holladay: 10 duplicated PC roll-call rows (Layton, six 2022 meetings) — dedup + re-federate.
- Alta: ~6 line-wrapped / `;`-anchored / narrative roll-call undercaptures + 3 cosmetic garbled
  `db/person` rows.
Fix the roll-row parsers to tolerate injected header/form-feed lines + line-wraps + narrative
vote tokens; dedup identical (member,vote) within a motion; re-extract --force; rebuild derived.

### 3.2 Campaign-finance vision backfills (`cf-vision-transcribe`, $0 API)
millcreek (28 filings), ogden (6 scanned + 2025 cycle when posted), west_valley (4 scanned),
taylorsville (13 election-cycle + regime-aware cycle_totals), west_jordan 2021 multi-report
re-transcribe. Each: delete/rebuild the `vision/<id>.json` caches, rebuild + validate. Honor the
documented "do NOT re-vision" honest-flag rows.

### 3.3 OCR → born-digital PMN upgrades + new-city expansion/roster
Taylorsville 15 OCR-upgrade minutes (high); Millcreek/Taylorsville PMN born-digital swaps;
Bluffdale expansion layers + rolling roster; new-city rosters generally.

## Tier 4 — larger programs (owner-gated; not now)

- Entity-tier **Phase 4** (utah/weber/cache/summit/washington/juab counties), **Phase 5**
  (WFRC/MAG MPOs + `ut_state`), **Phase 6** (entity-aware skills, `cities.db`→`gov.db` rename +
  doc sweep, README/CLAUDE rewrite, hierarchy index). County content-menu enrichments.
- **GitHub publish** (owner deferred — confirm before doing), **Wayback archiving pass**
  (owner interested, not approved) — both await owner go. *(Raw-PDF backfill was RULED OUT
  OF SCOPE by owner 2026-07-19 — text versions are saved; sources.csv is the recovery path.)*
- CF vision cache-key standardization (REFACTOR 5.7 deferral).

## Items to retire / rewrite rather than execute
- Items 1 & 3 "port to 15 clones" scope → rewrite as the single shared-lib fix (see 1.1).
- "12 new documents available as of 2026-07-02" — likely absorbed by later refreshes; verify then close.
- README coverage-caveat list (8 honest-zero comment cities etc.) predates the 12 new cities.

## T1.1 verification baseline (captured 2026-07-12 11:06, read-only)

Expected flip-set = motions whose stored `motion.outcome` contradicts their authoritative
`motion_std` yes:no tally: `(outcome='Pass' AND tally_aye<tally_nay)` OR
`(outcome='Fail' AND tally_aye>tally_nay)`, excluding equal tallies. **126 contradictions
across 21 entities.** SLC=0 and salt_lake_county=0 (already correct) — validates the method.
After T1.1, re-run this query: nearly all 126 should flip to the correct outcome (a small
residue may be legitimate supermajority failures the fix must exempt, not miscodes).

  provo 31 · sandy 24 · logan 10 · park_city 9 · holladay 9 · draper 7 · lehi 5 · west_jordan 4 ·
  orem 4 · ogden 4 · st_george 3 · west_valley 2 · taylorsville 2 · south_jordan 2 · murray 2 ·
  millcreek 2 · kearns 2 · vineyard 1 · nephi 1 · herriman 1 · bluffdale 1

Query (re-run to verify): join `motion` m to `motion_std` s on `s.motion_id=m.motion_id AND
s.city=m.city`, `WHERE s.tally_aye IS NOT NULL AND s.tally_nay IS NOT NULL AND
s.tally_aye<>s.tally_nay AND ((m.outcome='Pass' AND s.tally_aye<s.tally_nay) OR
(m.outcome='Fail' AND s.tally_aye>s.tally_nay))`.

## Concurrency rule while the townships build is in flight
Only create NEW files (this plan) and internal task state. Do not edit any shared/derived file
until the townships instance confirms done: `cities.db`, `coverage.json`, `registry/*`,
`scripts/db_build_lib.py`, `scripts/build_cities_db.py`, `TODO.md`, README/CLAUDE.

## ARCHIVE ANCHOR 2026-08-01 — DEBT-clearance wave + solo pass (owner-approved 10 Opus agents + coordinator)

Closed 12 of the 14 post-restructure [DEBT] items; full per-agent records in the wave
transcript (journal wf_1fe6e521-df4) and commit history. Verdicts:
- **weber** died-motions ×4 FIXED at the extractor (+9 motions incl. 5 carried substitutes,
  4 died motions honestly vote-less; ordinances 2018-14/2018-23 re-pointed off died motions)
  + COLLATERAL: the 2020-06-23 Taylor Landing contested roll (2-1) was ORPHANED — attached
  to no motion at all — now recovered (+3 votes, contested 81→82).
- **ogden** died ×2 fixed (a Nay recovered, Died 0→2) + 7 primary races added (2021×2,
  2023×2, 2025×2, +1; from the on-disk canvasses).
- **midvale** died ×1 fixed; Erikson→Erickson merged at the person-resolution layer (13
  vote rows re-keyed, values identical, the Nay preserved); weeks Meetings:0 13→0.
- **emigration_canyon** parse_present fixed (attendance-only; vote layer proven
  byte-identical); VERIFICATION.md rewritten (11 numeric claims corrected).
- **south_salt_lake** 2021-primary premise FAILED — SSL 2021 was RCV (no primary exists);
  REAL defect fixed instead: 4 rows relabeled plurality→RCV with first-choice totals +
  caveat notes. Cross-entity RCV mislabel class filed as new [DEBT].
- **draper** 2025 canceled-uncontested race added (Res #25-49, convention row, no
  fabricated tallies); federated caveat text updated.
- **murray** 2021 Mayor primary corrected to the certified canvass (registered/ballots/
  turnout + source repointed); D4-primary premise FAILED (none should exist); unsourced
  "Galt withdrew" causal claim replaced with sourced text; 4 docs reconciled.
- **wfrc_mpo** 4 appositive motions added (corpus diff: +4/0/0) + a ride-along verbatim
  result fix ('the vote.' → the real sentence).
- **washington_county** ALL THREE premises FAILED — 290/290 minutes byte-identical; the
  filed garbling patterns don't exist as described; root CLAUDE.md 82%→78% OCR corrected.
- **bluffdale** referral ground-truth: high-tier precision FAR below quotable — 269→62
  links (-207; suppressions via the documented override ledger, now load-bearing);
  guard-params tested and rejected; recall unmeasured; extractor-window root cause filed
  as new [DEBT]; lehi census filed as a LEAD.
- **Coordinator solo:** logan "North Logan RCV" corrected (3 spots, dated); riverton 5
  auth-wall rows relabeled (now matching AVAILABILITY.md); SLCo HA "phantom row" premise
  FAILED (it is the honest-gap convention: image-only status + note); weeks_lib
  stem-parse + PMN-link fixes (bluffdale 136→0 and the 70-bundle residual class →0 across
  8 cities); db_build_lib kind_of 'committee' token (alta BudgetCommittee, blast radius
  alta-only, verified); holladay Layton closed as satisfied-by-G2-caveat.
Closing federation 2026-08-01T00:28:03: 44/44 auto-gate, integrity ok, reconciliation
exact; check_doc_numbers 13/13 after reconciliation; marquee 5/5; election_race 680→688.
