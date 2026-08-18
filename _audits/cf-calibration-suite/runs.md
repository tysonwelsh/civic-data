# Calibration + pilot runs

## 2026-08-02 — model-tier experiment (Phase B wave 1), COORDINATOR JUDGMENT

Contenders: claude-opus-5 (runs-opus.md, pilot-opus/) vs claude-sonnet-5 (runs-sonnet.md,
pilot-sonnet/). Identical brief, identical 30-filing pilot_set.csv.

| dimension | opus | sonnet |
|---|---|---|
| calibration | 11 PASS / 1 HONEST FAIL (Rhodes, self-scored for ground-truth contamination; found the Read-downsampling root cause) / 1 specimen correctly DISPUTED | claims 14/14; Rhodes "pass" cache-cross-checked (contaminated under the stricter standard) and physically questionable given the downsampling finding |
| pilot coverage | 24/30 filings, 934 rows; 6 honestly unattempted (budget), with resumable page surveys | 30/30 filings, 786 rows |
| verification | 100% literal per-row crop-verify | SUBSTITUTED aggregate reconciliation for crop-verify (disclosed contract deviation) |
| reconciliation | 45/48 attempted sides exact; 3 deltas all proven filer arithmetic | 48/60 exact; 6 small deltas, some unchased |
| adjudicated digit conflict (Allen "Home Depot") | **13.85 — CORRECT** (page-5 subtotal 2,523.78 proves it arithmetically) | 3.85 — breaks the filer's own subtotal |
| shared discovery | BOTH independently found Kahler p3 "TOTAL: zero" → the wasatch cache + module were corrected (3rd read: coordinator) and the specimen now tests page coverage |
| cost | 391k tokens / 209 calls | 578k tokens / 296 calls |

**VERDICT: Opus for the handwritten bulk (wave B2).** Sonnet was not cheaper in tokens here,
deviated from the verification contract under volume pressure, and lost the only adjudicated
digit-level conflict. Sonnet remains plausible for clean-grid material, but that slice is
largely covered by the Phase-A parsers already.

**Method upgrades adopted for B2:** tight-crop escalation (GOTCHAS rule); page-SUBTOTAL
arithmetic as an additional per-page gate where the form prints one (the Allen adjudication
method); bbox precision gets its own render-back spot-check at scoring (both contenders'
boxes drifted); pct: geometry stored from the start.

## 2026-08-02 — WAVE B2 PRE-FLIGHT (production configuration, SLCo clerk-legacy itemization)

Configuration under test = the **production** configuration for wave B2: `claude-opus-5[1m]` via
the Read tool; `pdftoppm -jpeg -r 200` **full-page** first read; escalation = **TIGHT CELL CROP at
600–1200 dpi** (never a full-page dpi raise — GOTCHAS); sibling-copy check; **page-SUBTOTAL /
schedule-sum arithmetic gate** where the form prints one; zero-glyph ruling; whitelisted
decimal-comma repair only. Run by the B2 orchestrator before any bulk transcription.

**Disclosure of prior exposure (fairness caveat).** The orchestrator was briefed on
`runs-opus.md` and `manifest.csv` before running, so this is a **mechanism verification**, not a
blind test: it asks "does this configuration's escalation + gating machinery reach the right
answer", not "does it discover it unaided". Where the run *disagrees* with the recorded expected
value (specimen 1) the disagreement is carried with its own primary-source proof.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **RULE PASS / EXPECTED-VALUE DISPUTED** | 200 dpi full page → `1,694.09`. Escalated per the rule: 1200 dpi **tight cell crop** of both the December fax and the cleaner **October sibling** — glyph is genuinely bistable at true resolution. **The arithmetic gate settles it:** the filing's own Form "A" (p2, both copies) itemizes 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **1,694.09 exactly**; and 1,694.09 + line-2 105.00 = **1,799.09** = the printed line-3 expenses, giving the printed line-4 balance of **0**. Under `4,694.09` neither identity holds. → **digit = 1**, not 4 |
| 2 | `summit-reversed-columns` | **PASS** | contributions **503.00** (Current Report), expenditures **511.62**. 511.62 never emitted as a contribution total |
| 3 | `summit-zero-glyph` | **PASS** | Current-Report contribution/expenditure cells + the whole Campaign-balance row are slashed zeros → **0.00**, verbatim `Ø` kept (form prints "DO NOT DELETE ANY CELLS WITH $0.00") |
| 4 | `summit-genuine-blank` | **PASS** | contributions row and balance row genuinely EMPTY → **blank**, not 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54** |
| 5 | `wasatch-word-zero` | **PASS (incl. page coverage)** | rendered pp2–3. Table A TOTAL `zero` → **0.00**; **Table B's TOTAL row is on page 3** and also reads `zero` → **0.00**. A page-2-only pass would have missed a stated total |
| 6 | `wasatch-na-blank` | **PASS** | one handwritten `N/A` spans all three TOTALS cells → **all blank**, not zero |
| 7 | `weber-dash-nil` | **PASS** | line 4 Ending Balance is a bare `-` in all three columns → **blank** (line 2 likewise) |
| 8 | `slco-decimal-comma` | **PASS** | line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair; never 192000. (Col B `2510 ⁰⁰` = superscript cents) |
| 9 | `slco-superscript-cents` | **PASS** | `19 875 ⁸⁵` → **19875.85**; `19,435 ¹³` → **19435.13**. Confirmed by the page's own arithmetic: 2233.58 + 19875.85 = 22109.43 (line 5) and − 19435.13 = 2674.30 (line 7), both exact |
| 10 | `utah-checklist-decoy` | **PASS** | p5 is the county's staff-signed *Campaign Financial Disclosure Checklist* — it names every summary-page line label but carries **zero dollar figures**; rejected as a summary page |
| 11 | `washco-wrapped-ledger` | **PASS (negative control satisfied)** | **counted_sum = WITHHELD.** No total printed anywhere; cash and "Non Cash Expenditures" share one ledger with no separating subtotal; 5 rows wrap across lines; one row dated `Various`; one amount negative (`$-28.11`). Completeness not provable → no sum emitted |
| 12 | `utah-malformed-decimal` | **PASS** | `23,744,71` and `23.744.71` → **blank/unparseable**, not repaired, and `23,744` NOT lifted out. Well-formed neighbours kept (`23,744.71`, `32,744.71`); `N/A` cell blank |
| 13 | `utah-colAB-regime` | **PASS** | Column A "Total this Period" promoted (28,413.88 / 21,410.78); Column B "Year-to-Date Total" blank here, never summed as an increment; typed line-3 `0` → 0 |

**Score: 12 clean PASS + 1 rule-pass-with-disputed-expected-value. Negative controls (4, 6, 7,
11, 12) all held — nothing was "recovered". Pre-flight PASSED; bulk authorized.**

### The Rhodes finding — a specimen correction request, not a transcription

The suite's own README says a configuration that *recovers* a value on a negative control fails,
because eagerness is the screened mode. Specimen 1 turns out to be an instance of exactly that,
one level up: **escalation alone produced a `4` that the filing's own schedule disproves.** The
B2 method upgrade (page-subtotal / schedule-sum arithmetic as a gate on any escalated digit) is
what catches it. Evidence, all primary:

* `cache_county/campaign_finance/raw/2018/2018_cc_Shannon_Rhodes.pdf` p2 (and the December copy
  `…_final.pdf` p2 — the same seven rows) — Form "A" itemized: $100, $100, $100, $50, $202.50,
  $550, $591.59 → **1,694.09**.
* p1 line 2 = 105.00; line 3 (expenses) = 1,799.09; line 4 (balance) = 0.
  1,694.09 + 105.00 = 1,799.09 − 1,799.09 = 0. The page closes exactly on **1**.

**Requested (owner/coordinator decision, NOT actioned here):** correct
`manifest.csv:rhodes-4v1-fax` `expected_json.correct_digit` to `"1"` while keeping the escalation
RULE it tests, and add the arithmetic gate to what the specimen scores; re-read
`cache_county/campaign_finance/vision/00b019d3.json`, whose `contrib_over_50.cumulative`
(`4,694.09`) is the value that appears to be wrong — its `this` (`1,694.09`) already agrees with
the schedule. The cache_county CLAUDE.md "Render resolution matters" note would need the same
correction. **Nothing outside `salt_lake_county/campaign_finance/**` was modified by this wave**;
this is filed as a finding.

## 2026-08-02 — WAVE B2 **RESIDUE CONTINUATION** PRE-FLIGHT (same production configuration)

Configuration under test = unchanged from the wave-B2 production configuration: `claude-opus-5[1m]`
via the Read tool; `pdftoppm -jpeg -r 200` **full-page** first read, every page of the filing
rendered and classified; escalation = **TIGHT CELL CROP at 600–1200 dpi** (never a full-page dpi
raise); **the document's own ARITHMETIC — schedule sums, page subtotals, balance closure — outranks
any glyph re-read at any resolution** (GOTCHAS, Rhodes reversal); zero-glyph ruling; whitelisted
decimal-comma repair only; field-shift screen; withhold-rather-than-guess. Run by the residue
orchestrator before authorizing the 258-filing bulk.

**Disclosure of prior exposure (fairness caveat).** This orchestrator read `manifest.csv`,
`README.md` and the earlier `runs.md` tables before running. Like the 18:26 run this is therefore a
**mechanism verification** — "does the gating machinery reach the right answer" — not a blind
discovery test. Every row below states the primary-source evidence that decided it, so each verdict
is checkable independently of the expected value.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS (agrees with the CORRECTED expected value)** | 200 dpi full page, **no escalation used or needed**. Decided purely by the document: p2 Form "A" itemizes 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **1,694.09 exactly**; cover line 1 (this report **and** cumulative) is that same figure; 1,694.09 + line-2 105.00 = **1,799.09** = the printed cumulative line-3 expenses, giving the printed line-4 balance **0**. Under a leading `4` neither identity closes. → **correct_digit = "1"**, closure figure **1,799.09** |
| 2 | `summit-reversed-columns` | **PASS** | Columns read Current \| Last \| Cumulative. Contributions **503.00**, expenditures **511.62**; 511.62 never emitted as a contribution total. (Cumulative 503.00/511.62; balance 11.14 current vs 11.17 cumulative — a filer inconsistency, kept verbatim, not reconciled) |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway's Current-Report contribution and expenditure cells and **all three** Campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained. Form prints "DO NOT DELETE ANY CELLS WITH $0.00". Last/Cumulative 825.33 read as digits, not zeros |
| 4 | `summit-genuine-blank` | **PASS (negative control held)** | Francis: the entire contributions row and the entire balance row are **empty cells, no glyph** → **blank**, not 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54** |
| 5 | `wasatch-word-zero` | **PASS (incl. page coverage)** | pp2–3 rendered. Table A TOTAL `zero` → **0.00** (and the first Amount cell also reads `zero`); **Table B's TOTAL row sits on page 3** and reads `zero` → **0.00**. A page-2-only pass loses a stated total |
| 6 | `wasatch-na-blank` | **PASS (negative control held)** | Hewlett: one handwritten `N/A` written across all three TOTALS cells (lines 1–3) → **all blank**, never 0 |
| 7 | `weber-dash-nil` | **PASS (negative control held)** | Allred 2014: line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 likewise. Real figures on the same page (4,067.20 ×4) read normally, so this is a nil MARK, not illegibility |
| 8 | `slco-decimal-comma` | **PASS, and closed by arithmetic** | K. Morgan p2 line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair (never 192000, never 1920). Col B `2510 ⁰⁰` = superscript cents. **The page proves it:** line 3 2134.50 + 1920.00 − line 6 4043.07 = **11.43** = the printed line 7, exactly. (The filer's own line-5 subtotal `4,435.00` is wrong — 4054.50 is the true sum — and is retained verbatim, never corrected) |
| 9 | `slco-superscript-cents` | **PASS, and closed by arithmetic** | Auger p2: `19 875 ⁸⁵` → **19875.85**, `19,435 ¹³` → **19435.13**, `2233 ⁵⁸` → 2233.58, `22109 ⁴³` → 22109.43, `2674 ³⁰` → 2674.30. Both identities close exactly: 2233.58 + 19875.85 = 22109.43 and 22109.43 − 19435.13 = 2674.30. Col B `24,366 ⁶⁰` / `21,692 ³⁰` same convention |
| 10 | `utah-checklist-decoy` | **PASS** | Cox p5 is the Utah County Elections *Campaign Financial Disclosure Checklist* — it names every Summary-Page line label ("Balance at Beginning of Reporting Period", "Subtotal before Expenditures", …) and carries **zero dollar figures**; two staff-signed copies on one sheet. Rejected as a summary page |
| 11 | `washco-wrapped-ledger` | **PASS (negative control held)** | **counted_sum = WITHHELD.** Both pages rendered: p1 cash ledger, p2 "Non Cash Expenditures" — one continuous list with **no subtotal separating them and no grand total anywhere**; 5 rows wrap across lines; one date is literally `Various`; one amount is negative (`$-28.11`). Completeness not provable against any printed figure → no sum claimed |
| 12 | `utah-malformed-decimal` | **PASS (negative control held)** | Ioannides: `23,744,71` (cumulative contributions) and `23.744.71` (current expenditures) → **blank/unparseable**, not repaired, and `23,744` NOT lifted out of either. Well-formed neighbours kept (`23,744.71`, `32,744.71`); `N/A` cell blank; typed `0` balances → 0 |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich p6 (Summary Page is the LAST page — page position untrusted): Column A "Total this Period" promoted (**28,413.88** / **21,410.78**); Column B "Year-to-Date Total" genuinely empty → blank, never summed as an increment. Line 3 typed `0` → 0; line 7 7,003.10 closes exactly (28,413.88 − 21,410.78) even though the filer left lines 4 and 6 blank |

**Score: 13 / 13 PASS.** All five negative controls (4, 6, 7, 11, 12) held — nothing was
"recovered", no sum was claimed where completeness was unprovable, no malformed decimal was
repaired. Specimen 1 now **agrees** with the manifest's corrected answer and was reached the way the
corrected specimen demands: by the document's own arithmetic, with **zero glyph escalations**.
Specimens 8, 9 and 13 independently reproduced the same pattern — a page identity closing to the
cent is what confirms a doubtful digit, and specimen 8 additionally shows the identity surviving a
filer arithmetic error on a *different* line (line 5), which is why the gate must be run per
identity and not as a single "the page adds up" check.

**Pre-flight PASSED; bulk transcription of the 258-filing residue authorized** under the unchanged
per-row contract (`_backups/2026-08-02-tranche3/slco-b2/AGENT_BRIEF.md`).

## 2026-08-14 — SUMMIT COUNTY (Tranche 3 Phase B) BULK-ITEMIZATION PRE-FLIGHT

Configuration under test: `claude-opus-5[1m]` via the Read tool (Claude Code allotment, $0 API);
`pdftoppm -jpeg -r 200` **FULL-PAGE** first read of every page of the filing; escalation = **TIGHT
CELL CROP at 600–1200 dpi**, never a full-page dpi raise; **the document's own ARITHMETIC —
schedule sums, page subtotals, cover closure — outranks any glyph re-read at any resolution**;
zero-glyph ruling (Ø / -0- / "zero" → 0 verbatim-preserved, bare dash / N/A / empty → blank);
whitelisted decimal-comma repair only, malformed decimals unparseable-blank; field-shift screen;
withhold-rather-than-guess. Run by the summit wave agent before opening the 116-scan queue.

**Disclosure of prior exposure (fairness caveat).** This agent read `manifest.csv`, `README.md`
and the earlier `runs.md` tables before running, per its brief. This is therefore a **mechanism
verification**, not a blind discovery test. Every row states the primary-source evidence that
decided it, checkable independently of the expected value. All 13 specimens were re-rendered from
the raw PDFs and re-read from scratch.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS (corrected expected value)** | 200 dpi full page, **zero escalations**. p2 Form "A" itemizes 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **1,694.09**; the cover's "THIS REPORT" line 1 is that same figure with a blank LAST-REPORT column, so cumulative must equal it; 1,694.09 + line-2 105.00 = **1,799.09** = printed cumulative line-3 expenses → line-4 balance **0**. Under a leading `4` no identity closes. → **correct_digit "1"**, closure 1,799.09. (The fax also prints line-3 "this report" as `1,799.01` against cumulative `1,799.09` — a fax/filer artifact; the closure resolves on 1,799.09) |
| 2 | `summit-reversed-columns` | **PASS** | Header reads Current Report \| Last Report \| Cumulative Totals. Contributions **503.00**, expenditures **511.62**; 511.62 never emitted as a contribution total. Balance 11.14 current vs 11.17 cumulative — filer inconsistency, kept verbatim |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway 20753: Current-Report contribution + expenditure cells and **all three** Campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained. Last/Cumulative 825.33 read as digits. Form prints "DO NOT DELETE ANY CELLS WITH $0.00" |
| 4 | `summit-genuine-blank` | **PASS (negative control held)** | Francis 8196: the whole contributions row and the whole balance row are **empty cells, no glyph** → **blank**, not 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54** |
| 5 | `wasatch-word-zero` | **PASS (incl. page coverage)** | pp2–3 rendered. Table A first Amount cell and its TOTAL both read `zero` → **0.00**; **Table B's TOTAL row sits on page 3** and reads `zero` → **0.00**. A page-2-only pass loses a stated total |
| 6 | `wasatch-na-blank` | **PASS (negative control held)** | Hewlett 202406: one handwritten `N/A` drawn across all three TOTALS cells (lines 1–3) → **all blank**, never 0. Office/District/Party boxes also genuinely empty |
| 7 | `weber-dash-nil` | **PASS (negative control held)** | Allred `wb20160824055025_CAllred_1.5.15`: line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 likewise. Real figures on the same page (4,067.20 ×4) read normally, so the dash is a nil MARK, not illegibility |
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan p2 line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair (never 192000, never 1920). Col B `2510 ⁰⁰` superscript cents. The page proves it: line 3 2134.50 + line 4 1920.00 = 4054.50; − line 6 4043.07 = **11.43** = printed line 7 exactly. The filer's own line-5 subtotal `4,435.00` is WRONG and is retained verbatim, never corrected — the identity must be run per-line, not as "the page adds up" |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | Auger p2: `19 875 ⁸⁵` → 19875.85, `19,435 ¹³` → 19435.13, `2233 ⁵⁸` → 2233.58, `22109 ⁴³` → 22109.43, `2674 ³⁰` → 2674.30. Both identities close: 2233.58 + 19875.85 = 22109.43 and 22109.43 − 19435.13 = 2674.30. Col B `24,366 ⁶⁰` / `21,692 ³⁰` same convention |
| 10 | `utah-checklist-decoy` | **PASS** | Cox `2022_Cox_Hyrum_5.9.2022_Redacted.pdf` p5 is the Utah County Elections *Campaign Financial Disclosure Checklist* — it recites every Summary-Page line label ("Balance at Beginning of Reporting Period", "Subtotal before Expenditures", …) and carries **zero dollar figures**; two staff-signed copies on one sheet (5/18/2022 blue + red). Rejected as a summary page |
| 11 | `washco-wrapped-ledger` | **PASS (negative control held)** | **counted_sum = WITHHELD.** Both pages read: p1 "Detailed Expenditures Report" cash ledger, p2 "Non Cash Expenditures" — one continuous list, **no subtotal separating them and no grand total anywhere**; rows wrap across lines (Linden Alder "Adj Prior Reimb for / Premium Graphix"; "Independent Publishing / Company"), one date is literally `Various`, one amount is negative (`$-28.11`). Completeness unprovable against any printed figure → no sum claimed |
| 12 | `utah-malformed-decimal` | **PASS (negative control held)** | Ioannides summit 24231: `23,744,71` (cumulative contributions) and `23.744.71` (current expenditures) → **blank/unparseable**, not repaired, and `23,744` NOT lifted out of either. Well-formed neighbours kept (current contrib `23,744.71`; cumulative expend `32,744.71`); `N/A` cell blank; typed `0` balances → 0. Header boxes (name/office/party) genuinely EMPTY on this sheet |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich `2020_Sakievich_06.29.30_Revised_Redacted_Redacted.pdf` **p6 of 6 — the Summary Page is the LAST page** (page position untrusted; p2/p4 of the sibling file are Schedules A/B and one sibling even binds a 2018 Schedule B). Column A "Total this Period" promoted (**28,413.88** / **21,410.78**); Column B "Year-to-Date Total" genuinely empty → blank, never summed as an increment. Line 3 typed `0` → 0; line 7 **7,003.10** closes exactly (28,413.88 − 21,410.78) even though the filer left lines 4 and 6 blank |

**Score: 13 / 13 PASS.** All five negative controls (4, 6, 7, 11, 12) held — nothing was
"recovered", no sum was claimed where completeness was unprovable, no malformed decimal was
repaired. Specimen 1 was reached the way the corrected specimen demands: by the document's own
arithmetic, with **zero glyph escalations**. Specimens 8, 9 and 13 independently reproduced the
same pattern, and 8 again demonstrates the identity surviving a filer arithmetic error on a
*different* line.

**Incidental finding (filed as a lead, nothing modified outside summit):** `2020_SakievichTom6.23.20_Redacted.pdf`
p6 is a **2018 Utah County Schedule B** bound into a 2020 filing — the same multi-report-PDF class
as the Park 2024-11 residual in the LEADS enriched spec. Utah County's index may carry one row for
a PDF holding two reports.

**Pre-flight PASSED; bulk itemization of the summit 116-scan queue authorized** under the per-row
contract in `salt_lake_county/campaign_finance/CLAUDE.md` §"The per-row contract".

## 2026-08-14 — WAVE B2 **WEBER COUNTY** PRE-FLIGHT (Tranche 3 Phase B)

Configuration under test: `claude-opus-5[1m]` via the Read tool; `pdftoppm -jpeg -r 200`
**full-page** first read (every page of a filing rendered and classified); escalation =
**TIGHT CELL CROP at 600–1200 dpi**, never a full-page dpi raise; **the document's own
ARITHMETIC (schedule sums, page subtotals, balance closure) outranks any glyph re-read at any
resolution** (GOTCHAS, Rhodes reversal); zero-glyph ruling; whitelisted decimal-comma repair
only; field-shift screen; withhold-rather-than-guess. Run by the weber_county B2 wave agent
before authorizing bulk transcription of weber's 93 handwritten county-office filings.

**Disclosure of prior exposure (fairness caveat).** This agent read `manifest.csv`, `README.md`
and the earlier `runs.md` tables before running (they are named READ-FIRST material in the wave
brief). This is therefore a **mechanism verification**, not a blind discovery test; every row
states the primary-source evidence that decided it so each verdict is checkable independently
of the expected value.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS (corrected expected value, reached by arithmetic)** | 200 dpi full page, **zero escalations**. p2 Form "A": 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **1,694.09** exactly = cover line-1 *This Report*. Line 1 cumulative + line 2 (105.00) = **1,799.09** = printed line-3 cumulative expenses ⇒ printed line-4 balance **0**. Under a leading `4` neither identity closes (4,799.09 ≠ 1,799.09; balance would be 2,899.99). → **correct_digit "1"**, closure **1799.09** |
| 2 | `summit-reversed-columns` | **PASS** | Header order read as printed: Current \| Last \| Cumulative. Contributions **503.00**, expenditures **511.62**; 511.62 never emitted as a contribution total. Balance 11.14 current vs 11.17 cumulative = filer inconsistency, kept verbatim |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway: Current-column contributions + expenditures and **all three** Campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained (form prints "DO NOT DELETE ANY CELLS WITH $0.00"). Last/Cumulative 825.33 read as digits |
| 4 | `summit-genuine-blank` | **PASS (negative control held)** | Francis: contributions row and balance row are **empty cells, no glyph** → **blank**, not 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54** |
| 5 | `wasatch-word-zero` | **PASS (incl. page coverage)** | pp2–3 rendered. Table A first Amount cell and TOTAL both read `zero` → **0.00**; **Table B's TOTAL row sits on page 3** and also reads `zero` → **0.00**. A page-2-only pass loses a stated total |
| 6 | `wasatch-na-blank` | **PASS (negative control held)** | Hewlett: one handwritten `N/A` written across all three TOTALS cells (lines 1–3) → **all blank**, never 0 |
| 7 | `weber-dash-nil` | **PASS (negative control held)** | Allred 2014 (`wb20160824055025_CAllred_1.5.15.pdf` p1): line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 likewise; line 1/3 *This Report* also `-` → blank. Real figures on the same page (4,067.20 ×4) read normally, so the dash is a nil MARK, not illegibility |
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan p2 line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair (never 192000). Col B `2510 ⁰⁰` = superscript cents. The page proves it: line 3 2134.50 + line 4 1920.00 − line 6 4043.07 = **11.43** = printed line 7 exactly. The filer's own line-5 subtotal `4,435.00` is WRONG (4,054.50 is the true sum) and is retained verbatim |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | Auger p2: `19 875 ⁸⁵` → **19875.85**, `19,435 ¹³` → **19435.13**, `2233 ⁵⁸` → 2233.58, `22109 ⁴³` → 22109.43, `2674 ³⁰` → 2674.30. Both identities close: 2233.58 + 19875.85 = 22109.43; 22109.43 − 19435.13 = 2674.30 |
| 10 | `utah-checklist-decoy` | **PASS** | Located by CONTENT, not page number: `2022_Cox_Hyrum_5.9.2022_Redacted.pdf` p5 is the Elections Division *Campaign Financial Disclosure Checklist* — it names every Summary-Page line label and carries **zero dollar figures**; two staff-signed copies on one sheet; rejected. Control: `2022_Cox_Hyrum_4.1.2022_Redacted.pdf` p5 IS a genuine Summary Page (10,778.00 / 8,705.50 / 2,072.50) — same page ordinal, different page kind, which is the trap |
| 11 | `washco-wrapped-ledger` | **PASS (negative control held)** | **counted_sum = WITHHELD.** Both pages read: p1 cash ledger, p2 "Non Cash Expenditures" — one continuous list, **no subtotal separating them, no grand total anywhere**; 5 rows wrap across lines; one date is literally `Various`; one amount is negative (`$-28.11`). Completeness not provable against any printed figure → no sum claimed |
| 12 | `utah-malformed-decimal` | **PASS (negative control held)** | Ioannides: `23,744,71` (cumulative contributions) and `23.744.71` (current expenditures) → **blank/unparseable**, not repaired, and `23,744` NOT lifted out. Well-formed neighbours kept (`23,744.71`, `32,744.71`); `N/A` cell blank; typed `0` balances → 0 |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich p6 (Summary Page is the LAST page): Column A "Total this Period" promoted (**28,413.88** / **21,410.78**); Column B "Year-to-Date Total" genuinely empty → blank, never summed as an increment. Line 3 typed `0` → 0; line 7 **7,003.10** closes exactly (28,413.88 − 21,410.78) even though the filer left lines 4 and 6 blank |

**Score: 13 / 13 PASS.** All five negative controls (4, 6, 7, 11, 12) held — nothing was
"recovered", no sum claimed where completeness was unprovable, no malformed decimal repaired.
Specimen 1 was decided with **zero glyph escalations**, purely by the document's arithmetic.
Specimen 7 is weber's own trap and confirms the module's 10 dash balances correctly stay blank.

**Pre-flight PASSED; bulk transcription of weber_county's 93 handwritten county-office filings
authorized** under the unchanged per-row B2 contract (arithmetic-first gates, mandatory `pct:`
geometry anchors, per-filing cache checkpointing, transcribe-once-per-sha256).

## 2026-08-14 — TRANCHE 3 PHASE B, **JUAB WAVE** PRE-FLIGHT (B2 production configuration)

Configuration under test: `claude-opus-5[1m]` via the **Read tool** (Claude Code allotment, $0 API);
`pdftoppm -jpeg -r 200` **FULL-PAGE** first read, every page of a filing rendered and classified;
escalation = **TIGHT CELL CROP at 600–1200 dpi** only, never a full-page dpi raise; **the
document's own ARITHMETIC (schedule sums, page subtotals, cover balance closure) outranks any
glyph re-read at any resolution**; zero-glyph ruling; whitelisted decimal-comma repair only;
field-shift screen; withhold-rather-than-guess; mandatory `pct:` geometry per emitted row.
Run by the juab_county wave agent before opening its 24-filing itemization queue.

**Disclosure of prior exposure (fairness caveat).** This agent read `README.md`, `manifest.csv`
and the earlier `runs.md` tables before running — so, like the two runs above, this is a
**mechanism verification**, not a blind discovery test. Every row states the primary-source
evidence that decided it, checkable independently of the expected value.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS** (agrees with the corrected expected value) | 200 dpi full page; **zero escalations**. p2 Form "A" = 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **1,694.09**; cover line 1 "this report" prints that same figure; 1,694.09 + line-2 105.00 = **1,799.09** = the printed cumulative line-3 expenses, leaving the printed line-4 balance **0**. Under a leading `4` neither identity closes. → `correct_digit="1"`, closure **1799.09**. (Line 3 "this report" is written `1,799.01` against a cumulative `1,799.09` — a filer slip, retained verbatim, and it does not disturb the closure) |
| 2 | `summit-reversed-columns` | **PASS** | Header read off the page: Current \| Last \| Cumulative. Contributions **503.00**, expenditures **511.62**; 511.62 never emitted as a contribution total. Balance 11.14 current vs 11.17 cumulative — filer inconsistency, kept verbatim |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway: Current-Report contributions + expenditures and **all three** Campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained. Last/Cumulative 825.33 read as digits |
| 4 | `summit-genuine-blank` | **PASS** (negative control held) | Francis: entire contributions row and entire balance row are **empty cells, no glyph** → **blank**, never 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54** |
| 5 | `wasatch-word-zero` | **PASS** (incl. page coverage) | pp2–3 both rendered. Table A first Amount cell and TOTAL both read `zero` → **0.00**; **Table B's TOTAL row sits on page 3** and reads `zero` → **0.00**. A page-2-only pass loses a stated total |
| 6 | `wasatch-na-blank` | **PASS** (negative control held) | Hewlett: one handwritten `N/A` drawn across the TOTALS cells of lines 1–3 → **all blank**, never 0 |
| 7 | `weber-dash-nil` | **PASS** (negative control held) | Allred 2014 (`wb20160824055025_CAllred_1.5.15.pdf`): line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 likewise. Real figures on the same page (4,067.20 ×4) read normally ⇒ nil MARK, not illegibility |
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan p2 line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair (never 192000, never 1920); Col B `2510 ⁰⁰` superscript cents → 2510.00. The page proves it: line 3 2134.50 + line 4 1920.00 − line 6 4043.07 = **11.43** = the printed line 7 exactly. The filer's own line-5 subtotal `4,435.00` is wrong (true sum 4054.50) and is retained verbatim |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | `jauger_sept152006.pdf` p2: `35,786 ¹²`→35786.12, `5999 ⁸⁰`→5999.80, `27,692 ¹⁰`→27692.10, `2674 ³⁰`→2674.30, `11,419 ⁵²`→11419.52, `14,093 ⁸²`→14093.82, `8094 ⁰²`→8094.02. Both identities close: 2674.30 + 11419.52 = 14093.82 and 14093.82 − 5999.80 = 8094.02. Cross-filing check: that line-7 8094.02 is exactly the Oct-30 report's line-3 opening balance |
| 10 | `utah-checklist-decoy` | **PASS** | `2022_Rampton_Russ_5.6.2022_Redacted.pdf` p5 is the Elections Division's *Campaign Financial Disclosure Checklist* — it names every Summary-Page line label ("Balance at Beginning of Reporting Period", "Subtotal before Expenditures", …), carries **zero dollar figures**, and holds two staff-signed review passes (5/18/2022). Rejected as a summary page |
| 11 | `washco-wrapped-ledger` | **PASS** (negative control held) | **counted_sum = WITHHELD.** Both pages read: p1 cash ledger, p2 "Non Cash Expenditures" — one continuous list, **no subtotal separating them and no grand total anywhere**; ≥5 rows wrap across lines; one date is literally `Various`; one amount is negative (`$-28.11`). Completeness unprovable against any printed figure → no sum claimed |
| 12 | `utah-malformed-decimal` | **PASS** (negative control held) | Ioannides (summit 24231): cumulative contributions `23,744,71` and current expenditures `23.744.71` → **blank/unparseable**, not repaired, and `23,744` NOT lifted out of either. Well-formed neighbours kept (23,744.71 / 32,744.71); `N/A` cell blank; typed `0` balances → 0 |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich (2020 6.23.20 filing), Summary Page is the **LAST** page (p6 of 6 — page position untrusted): Column A "Total this Period" promoted (**28,413.88** / **21,410.78**); Column B "Year-to-Date Total" genuinely empty → blank, never summed as an increment. Line 3 typed `0`; line 7 7,003.10 closes exactly |

**Score: 13 / 13 PASS.** All five negative controls (4, 6, 7, 11, 12) held — nothing was
"recovered", no sum was claimed where completeness was unprovable, no malformed decimal was
repaired. Specimen 1 was reached with **zero glyph escalations**, purely by the page's own
identities; 8, 9 and 13 reproduced the same pattern independently.

**Directly load-bearing for the juab corpus:** specimen 1 is the SAME FORM juab files on — the
Carr Printing 5-5-PG statewide county sheet (Utah Code 17-16-6.5), whose cover carries
`TOTALS FROM LAST REPORT + TOTALS FOR THIS REPORT = CUMULATIVE REPORT` and whose Form "A"/"B"
sums are the reconciliation gate. Specimen 2 is its variant-order twin and is why each juab
filing's column order is confirmed from the page header, never from the family default.

**Pre-flight PASSED; bulk itemization of the juab 2010/2014 queue (24 filings) authorized.**

## 2026-08-14 — TRANCHE 3 PHASE B **WASATCH WAVE** PRE-FLIGHT (production configuration)

Configuration under test: `claude-opus-5[1m]` via the **Read tool** (Claude Code allotment, $0 API);
`pdftoppm -jpeg -r 200` **full-page** first read, every page of a filing rendered and classified;
escalation = **TIGHT CELL CROP at 600–1200 dpi** (never a full-page dpi raise); **the document's own
ARITHMETIC outranks any glyph re-read at any resolution** (GOTCHAS, Rhodes reversal); zero-glyph
ruling; whitelisted decimal-comma repair only; malformed decimals unparseable-blank; field-shift
screen with withhold-the-side; PRIVACY city/state only. Run by the wasatch wave agent before
opening the 111-filing itemization bulk.

**Disclosure of prior exposure.** This agent read `README.md`, `manifest.csv` and the earlier
`runs.md` tables before running (the brief requires it), so this is a **mechanism verification**,
not a blind discovery test. Each row states the primary-source evidence that decided it.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS** | 200 dpi full page, **zero escalations**. p2 Form "A": 100+100+100+50+202.50+550+591.59 = **1,694.09** exactly; cover line 1 THIS REPORT prints that same figure while the CUMULATIVE cell's lead glyph is bistable. 1,694.09 + line-2 105.00 = **1,799.09** = the printed cumulative line-3 expenses, giving the printed line-4 balance **0**. Under a leading `4` neither identity closes → **correct_digit "1"**, closure **1799.09**. (Line 3 THIS REPORT is printed `1,799.01` against cumulative `1,799.09` — a filer/scan inconsistency retained verbatim, not reconciled) |
| 2 | `summit-reversed-columns` | **PASS** | Header order Current \| Last \| Cumulative. Contributions **503.00**, expenditures **511.62**; 511.62 never emitted as a contribution total. Balance 11.14 current vs 11.17 cumulative kept verbatim |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway: Current-column contributions + expenditures and **all three** Campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained; Last/Cumulative 825.33 read as digits. Form prints "DO NOT DELETE ANY CELLS WITH $0.00" |
| 4 | `summit-genuine-blank` | **PASS (negative control held)** | Francis: the whole contributions row and the whole balance row are **empty cells, no glyph** → blank, not 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54** |
| 5 | `wasatch-word-zero` | **PASS (incl. page coverage)** | pp2–3 rendered. Table A first Amount cell and TOTAL both print `zero` → **0.00**; **Table B's TOTAL row sits on page 3** and prints `zero` → **0.00**. A page-2-only pass loses a stated total |
| 6 | `wasatch-na-blank` | **PASS (negative control held)** | Hewlett 2024-06: ONE handwritten `N/A` drawn across the TOTALS cells of lines 1–3 → **all blank**, never 0 |
| 7 | `weber-dash-nil` | **PASS (negative control held)** | Allred 2014-10-27: line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 likewise. Lines 1 and 3 (4,067.20 ×2 each) read normally, so the dash is a nil MARK, not illegibility |
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan p2 line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair (never 192000, never 1920); Col B `2510 ᵒᵒ` superscript → 2510.00. Page identity: line 3 2134.50 + line 4 1920.00 − line 6 4043.07 = **11.43** = printed line 7, exactly. The filer's own line-5 subtotal `4,435.00` is wrong (4,054.50 is the sum) and is retained verbatim |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | Auger 6-19-06 (`20_june_auger_janice06.pdf` p2): `19 875 ⁸⁵` → **19875.85**, `24,366 ⁶⁰` → 24366.60, `19,435 ¹³` → 19435.13, `21,692 ³⁰` → 21692.30, `2233 ⁵⁸` → 2233.58, `22109 ⁴³` → 22109.43, `2674 ³⁰` → 2674.30. Both identities close: 2233.58+19875.85 = 22109.43 and 22109.43−19435.13 = 2674.30 |
| 10 | `utah-checklist-decoy` | **PASS** | Cox 4/1/2022 **p7** is the *Campaign Financial Disclosure Checklist* — it names every Summary-Page line label ("Balance at Beginning of Period", "Subtotal before Expenditures", …), carries **zero dollar figures**, and holds two staff-signed copies on one sheet. Rejected as a summary page; the real Summary Page (p5, boxes A–F, 10,778.00 / 8705.50 / 2072.50) was read separately and is unaffected |
| 11 | `washco-wrapped-ledger` | **PASS (negative control held)** | **counted_sum = WITHHELD.** Both pages rendered: p1 cash ledger, p2 "Non Cash Expenditures" — one continuous list, **no subtotal separating them and no grand total anywhere**; rows wrap across lines; one date is literally `Various`; one amount is `$-28.11`. Completeness not provable against any printed figure → no sum claimed |
| 12 | `utah-malformed-decimal` | **PASS (negative control held)** | Ioannides 2024 pre-election: contributions Cumulative `23,744,71` and expenditures Current `23.744.71` → **blank/unparseable**, not repaired, and `23,744` NOT lifted out of either. Well-formed neighbours kept (`23,744.71` current contributions, `32,744.71` cumulative expenditures); `N/A` cell blank; typed `0` balances → 0 |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich 6/23/2020 revised, **p6 of 6 — the Summary Page is the LAST page**, so page position is untrusted. Column A "Total this Period" promoted (**28,413.88** / **21,410.78**); Column B "Year-to-Date Total" **genuinely empty** → blank, never summed as an increment. Line 3 typed `0`; line 7 7,003.10 closes exactly even though the filer left lines 4 and 6 blank |

**Score: 13 / 13 PASS.** All five negative controls (4, 6, 7, 11, 12) held. Zero glyph escalations were
needed — every doubtful figure was settled by a printed identity on its own page. Specimen 10 required
locating the checklist page by content (it is p7 here, not p5 as in the SLCo run) — a live
demonstration of the specimen's own lesson that page POSITION is untrustworthy.

**Pre-flight PASSED; bulk itemization of the 111-filing wasatch_county corpus authorized** under the
per-row contract of `_backups/2026-08-02-tranche3/slco-b2/AGENT_BRIEF.md`.
