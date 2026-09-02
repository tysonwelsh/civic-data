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

## 2026-08-18 — TRANCHE 3 PHASE B **UTAH COUNTY** PRE-FLIGHT (the largest remaining corpus)

**Why this run was mandatory** (wave brief §3a): no utah pre-flight had EVER been recorded — the
three utah-owned specimens had only ever been run by other counties' waves — **and the
configuration CHANGED on 2026-08-18**, which triggers the standing re-run rule on its own:

* `scripts/campaign_finance/make_snippet.py` — the `/Rotate` page-sizing defect and the
  oversized-mediabox blank-crop defect were both FIXED (weber close-out addendum §0).
* `scripts/campaign_finance/rowbands.py` + `fitgrid.py` — **NEWLY PROMOTED** to the shared path
  this session with the filed [DEBT] defects fixed (raw-frame coordinates, bar/baseline
  rejection, skew-robust angle search, column-restricted scan, data-band trimming; plus a
  fitgrid sub-multiple-pitch defect found while proving it). Evidence:
  `_backups/2026-08-18-utah-cf/workdir/ROWBANDS_PROMOTION.md`. The summit/weber backup copies
  are deliberately unchanged, so both closed waves stay reproducible against the tool they ran.

Configuration under test: `claude-fable-5` via the **Read tool** (Claude Code allotment, $0 API);
`pdftoppm -jpeg -r 200` **FULL-PAGE** first read, every page rendered and classified; escalation =
**TIGHT CELL CROP at 600–2000 dpi** only, never a full-page dpi raise; **the document's own
ARITHMETIC (schedule sums, page subtotals, cover balance closure) outranks any glyph re-read at
any resolution** (GOTCHAS, Rhodes reversal); zero-glyph ruling; whitelisted decimal-comma repair
only; malformed decimals unparseable-blank; field-shift screen; withhold-rather-than-guess;
mandatory `pct:` geometry per emitted row; PRIVACY city/state only.

**Disclosure of prior exposure (fairness caveat).** This agent read `README.md`, `manifest.csv`
and the earlier `runs.md` tables before running — the wave brief names them READ-FIRST material.
This is therefore a **mechanism verification**, not a blind discovery test. Every row states the
primary-source evidence that decided it, checkable independently of the expected value. All 13
specimens were re-rendered from the raw PDFs and read from scratch.

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS** (agrees with the corrected expected value) | 200 dpi full page, **zero escalations**. p2 Form "A" itemizes 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **1,694.09** exactly = the cover's line-1 THIS REPORT cell. LAST REPORT is blank, so cumulative must equal this report; 1,694.09 + line-2 105.00 = **1,799.09** = the printed line-3 cumulative expenses, giving the printed line-4 balance **0**. Under a leading `4` neither identity closes (4,799.09 ≠ 1,799.09; balance would be 2,894.99). → **correct_digit "1"**, closure **1799.09**. (Line 3 THIS REPORT is written `1,799.01` against cumulative `1,799.09` — a filer/fax slip, retained verbatim; it does not disturb the closure) |
| 2 | `summit-reversed-columns` | **PASS** | Header read off the page: Current Report \| Last Report \| Cumulative Totals. Contributions **503.00**, expenditures **511.62**; 511.62 never emitted as a contribution total. Last Report 0.00/0.00. Balance 11.14 current vs 11.17 cumulative — a filer inconsistency, kept verbatim, not reconciled |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway 20753: the Current-Report contribution and expenditure cells and **all three** Campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained. Last/Cumulative 825.33 read as digits. The form prints "DO NOT DELETE ANY CELLS WITH $0.00" |
| 4 | `summit-genuine-blank` | **PASS (negative control held)** | Francis 8196: the **entire** contributions row and the **entire** balance row are empty cells with no glyph → **blank**, never 0. Expenditures Current `$293 ⁵⁴/₁₀₀` → **293.54**, its Last/Cumulative cells also blank |
| 5 | `wasatch-word-zero` | **PASS (incl. page coverage)** | Kahler 2026-03, pp2–3 rendered. Table A's first Amount cell AND its TOTAL row both print `zero` → **0.00**; **Table B's TOTAL row sits on page 3** and also prints `zero` → **0.00**. A page-2-only pass loses a stated total — which is the coverage half of this specimen |
| 6 | `wasatch-na-blank` | **PASS (negative control held)** | Hewlett 2024-06: ONE handwritten `N/A` drawn across the TOTALS cells of lines 1–3 → **all blank**, never 0. Name of Office / District / Party boxes are genuinely empty as well |
| 7 | `weber-dash-nil` | **PASS (negative control held)** | Allred `wb20160824055025_CAllred_1.5.15.pdf` p1: line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 (the ≤$50 aggregate) likewise, and line 1/line 3 THIS REPORT are also `-` → blank. Real figures on the same page (4,067.20 in Last and Cumulative on lines 1 and 3) read normally, so the dash is a nil MARK, not illegibility |
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan p2 line 1 Col A verbatim `1920,00` → **1920.00** via the named whitelisted repair (never 192000, never 1920); Col B `2510 ᵒᵒ` superscript cents → 2510.00. The page proves it: line 3 2134.50 + line 4 1920.00 − line 6 4043.07 = **11.43** = the printed line 7, exactly. The filer's own line-5 subtotal `4,435.00` is WRONG (4,054.50 is the true sum) and is retained verbatim — the identity must be run PER LINE, never as "the page adds up". Line 4 also carries a struck-through value with `1920.00` written over it; the handwritten correction governs |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | Auger 6-19-06 p2: `19 875 ⁸⁵` → **19875.85**, `24,366 ⁶⁰` → 24366.60, `19,435 ¹³` → **19435.13**, `21,692 ³⁰` → 21692.30, `2233 ⁵⁸` → 2233.58, `22109 ⁴³` → 22109.43, `2674 ³⁰` → 2674.30. Both identities close exactly: 2233.58 + 19875.85 = 22109.43 and 22109.43 − 19435.13 = 2674.30 |
| 10 | `utah-checklist-decoy` | **PASS (and the control page re-proved)** | Located by CONTENT, not ordinal. `2022_Cox_Hyrum_5.9.2022_Redacted.pdf` **p5** is the Utah County Elections *Campaign Financial Disclosure Checklist* — it recites every Summary-Page line label ("Balance at Beginning of Reporting Period", "Contributions Received this Period / Year to Date", "Expenditures Made this Period / Year to Date", "Subtotal before Expenditures", "Balance at Close of Reporting Period") and carries **zero dollar figures**; two staff-reviewed copies on one sheet (blue 5/18/2022 + red 5/18/22). Rejected as a summary page. **Control:** `2022_Cox_Hyrum_4.1.2022_Redacted.pdf` **p5 IS a genuine Summary Page at the same ordinal** — A 0 · B 10,778.00 · C 10,778.00 · D 8705.50 · E 8705.50 · F 10,778.00 · close 2072.50, and F − D = 2072.50 exactly. Same ordinal, different page kind: that is the trap |
| 11 | `washco-wrapped-ledger` | **PASS (negative control held)** | **counted_sum = WITHHELD.** Both pages read: p1 "Detailed Expenditures Report" cash ledger, p2 "Non Cash Expenditures" — one continuous list with **no subtotal separating them and no grand total anywhere**. Five rows wrap across lines (Linden Alder "Adj Prior Reimb for / Premium Graphix"; "Reimbursement for / Mileage, Meals, / Supplies"; "Independent Publishing / Company" ×2; "Savage Esplin & / Radmall, PC"); one date is literally `Various`; one amount is negative (`$-28.11`). Completeness not provable against any printed figure → no sum claimed |
| 12 | `utah-malformed-decimal` | **PASS (negative control held)** | Ioannides summit 24231: contributions **Cumulative** `23,744,71` and expenditures **Current** `23.744.71` → **blank/unparseable**, not repaired, and `23,744` NOT lifted out of either. Well-formed neighbours kept (contributions Current `23,744.71`; expenditures Cumulative `32,744.71`); the `N/A` Previous-Report cell blank; typed `0` balances → 0. Candidate / Office / Party boxes genuinely EMPTY on this sheet |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich `2020_SakievichTom6.23.20_Redacted.pdf` **p6 of 6 — the Summary Page is the LAST page**, so page position is untrusted. Column A "Total this Period" promoted (**28,413.88** / **21,410.78**); Column B "Year-to-Date Total" **genuinely empty** → blank, never summed as an increment. Line 3 typed `0` → 0; lines 4/5 28,413.88, line 6 21,410.78, line 7 **7,003.10** closes exactly (28,413.88 − 21,410.78) |

**Score: 13 / 13 PASS.** All five negative controls (4, 6, 7, 11, 12) held — nothing was
"recovered", no sum was claimed where completeness was unprovable, no malformed decimal was
repaired. Specimen 1 was decided with **zero glyph escalations**, purely by the document's own
identities; 8, 9, 10-control and 13 independently reproduced the same pattern, and 8 again shows
the identity surviving a filer arithmetic error on a *different* line of the same page.

**Directly load-bearing for the utah corpus.** Specimen 13 is utah's own `legacy_colAB` regime and
confirms the INVERTED anchor this wave must respect: Column A (per-period) is promoted, Column B
(cumulative) is never summed as an increment. Specimen 10 is utah's own page-selection decoy and
was run BOTH ways — the checklist rejected, the same-ordinal genuine Summary Page accepted — which
is the discipline the 245-filing queue needs on every filing. Specimen 12 is utah-registered and
holds the line against repairing a malformed decimal.

**Pre-flight PASSED; bulk itemization of the utah_county queue authorized** under the unchanged
per-row B2 contract (`utah_county/campaign_finance/WAVE_BRIEF_PHASEB.md` §4), with utah's
per-period basis rule and per-filer in-kind testing per §2.

### 2026-08-18 — SUITE GROWTH (same session, after the utah pre-flight passed)

The utah wave brief §3a instructed the pre-flight to **grow the suite** with the candidates the
weber/summit waves produced. Seven specimens added, taking the suite from 13 to **21**. Each is
ground-truthed and carries its evidence citation; the four with a `must_not_produce` or
`detect` clause are negative controls.

| new specimen | class | ground-truthed how |
|---|---|---|
| `summit-specimen-row` | non-transaction row | page read 2026-08-18: Langston p3's first ledger line is the blank form's printed example (`Jon and Jane Doe`, `PO Box 128 Coalville`, **$435.00**, dated **8/25/10 on a 2022 form**), highlighted yellow by the filer. The nine real rows sum to **exactly 503.00** = the cover's Current Report contributions; including the specimen gives 938.00. The arithmetic is the proof, not the highlight |
| `utah-underline-band-offset` | GEOMETRY pointer | Graves 2014 p3: on the utah underline form the writing sits **above** its rule, so row N = [rule N−1, rule N] and row 1 is extrapolated one pitch up. Two-crop proof at 500 dpi: row-1 box rendered **745.00**, row-4 box rendered **180.75**; a naive band list points row 1 at 300.00 |
| `utah-template-vintage-year` | provenance token | three 2018 filings are filed on a blank headed *"2016 County & Local School Board Candidates"*. The printed year is the TEMPLATE VINTAGE. Negative control against reclassifying the cycle or reporting a bound-in prior report |
| `weber-wrong-column-pointer` | GEOMETRY pointer | the 4 records the 2026-08-17 weber audit withdrew: `cell` held the NAME column, so every amount summed exactly while every pointer aimed at the donor name. Only a render-back catches it |
| `weber-swapped-cover-pair` | cross-filing | Gibson 2026 (`76c91f61`/`8a163a02`): two internally-consistent covers under swapped keys. No single-page gate can see it; the Last-Report-vs-prior-Cumulative chain can |
| `weber-rtl-rows` | GEOMETRY pointer | weber's reverse-rotated landscape sheets: rows advance along x **descending**, so an ascending band list reverses the ledger while the sum still closes |
| `summit-swapped-pages` | page selection | summit 1059 / 23013 / 24377 bind the EXPENSE schedule on p2 and CONTRIBUTIONS on p3 |

**Why this matters beyond bookkeeping:** the original thirteen almost all ask *"is this cell's
value right?"*. Three of the seven additions ask **"is the POINTER right?"** — cases where every
value is correct and every side reconciles to the cent while the stored geometry still aims at
the wrong cell. No arithmetic gate can see any of them, which is exactly why the two-crop
render-back proof is a mandatory gate and not a nicety. A fresh capability the suite gained
today: it can now fail a configuration that gets every number right.

**These seven were NOT run as part of the 13/13 pre-flight above** — they were authored from it.
The next wave to run the suite runs 21.

### 2026-08-19 — TARGETED RE-VERIFICATION after a mid-wave `rowbands.py` change

The suite's rule is that a changed configuration must re-earn its bulk rights. A utah chunk
agent found that the promoted `rowbands.py` scanned VERTICAL (column) rules at a fixed 0.60
coverage while the horizontal scan had a relaxing ladder — so a filer's boxed LANDSCAPE
attachment ledger returned **28 row rules and ZERO column rules**. The vertical scan is now
adaptive (0.60 → 0.18, strict first, stop at the first threshold yielding a real column
structure).

**Scope of the re-verification, stated honestly:** `rowbands.py` is a MEASURING instrument — it
never reads a value — so the 18 value-reading specimens are untouched by this change and were
NOT re-run. What this change can affect is GEOMETRY, i.e. the three specimens added on
2026-08-18. Those were re-checked directly:

| check | result |
|---|---|
| `weber-wrong-column-pointer` — the audited box `pct:85.23,16.62,10.66,3.17@p2` | **PRESERVED EXACTLY.** Column bands still 4.72 / 12.87 / 43.17 / **85.24 / 95.90** at the STRICT 0.60 threshold |
| `utah-underline-band-offset` — Graves 2014 p3 | **UNCHANGED**: 16 data bands, and the underline form still correctly returns **no** vertical rules |
| the failure that prompted the change (Anderson 2010 attachment p4) | **RECOVERED**: 0 → **8** column rules at 0.45 |

**A failed first attempt is recorded because it is the lesson.** My first fix gave the vertical
axis the same PITCH-REGULARITY scoring the horizontal axis uses. That **regressed the proven
weber case**, replacing its correct column bands with a run of text stems 0.6 pct apart —
because table COLUMNS are unequal widths by design, so "most regular spacing" actively prefers
junk. Strict-wins-then-relax is what preserves them. The dead end is documented in the tool so
it is not retried.

**No bulk-transcription authorization is claimed or changed by this note** — the 13/13 pre-flight
above stands, and this records a measuring-tool change and exactly what was re-proved.

### 2026-08-19 — SECOND targeted re-verification after a `rowbands.py` change

A utah chunk agent reported that a printed rule **crossed by heavy ink** was being misfiled as a
BAR — four times in one chunk — so the row grid silently lost a line and every band below it
shifted. On one page the missing rule decided **row 1 itself** (candidate frames rendered `22.17`
vs `2500.00`). Fix: a run's thickness is now the **median across its own columns**, not its
maximum, because a printed rule stays thin along most of its length even where ink crosses it.

Re-verified (measuring tool only — the 18 value-reading specimens are untouched by it):

| check | result |
|---|---|
| weber's audited box `pct:85.23,16.62,10.66,3.17@p2` (`weber-wrong-column-pointer`) | **PRESERVED EXACTLY** — band 3 y=16.62 h=3.18; column bands 4.72 / 12.87 / 43.17 / **85.24 / 95.90** |
| `utah-underline-band-offset` (Graves p3) | unchanged — 17 rules, **16** data bands, no v-rules |
| weber typed boxed grid (55 real rules) | unchanged — **55** data bands, no over-rejection |
| utah typed born-digital | unchanged — **16** data bands |
| the reported failure (Tracy p4, rule returned in `bars_pct` at y≈22.96) | **RECOVERED** — 16 rules / 15 data bands, 1 bar |

No bulk-transcription authorization is claimed or changed by this note.

### 2026-08-20 — THIRD targeted re-verification after a `rowbands.py` change (DEFECT 7 + 2 siblings)

Closing the TODO [DEBT] "**`rowbands.py` DEFECT 7 — it can silently MISS a grid's TOP rule**".
Reproduced first: `utah_county/.../2026_Taylor_Fox_Redacted.pdf` p3 returned **15 rules for a
15-row grid** and **1 of 5** column rules, exactly as filed. Root cause measured at the page —
a faded photocopy's top rule is split into two runs by the absolute threshold and each half
then fails the `fill ≥ 0.80` gate; the column rules **shear** 3.2 pct top-to-bottom, which a
rigid deskew cannot straighten. Fix: background-normalised dark-run mask (union with the old
mask, more-regular-grid-wins, ties to raw), per-band column scan on projection failure,
off-grid (footer/header-box) rule exclusion, an ink-probed grid self-audit, `--expect-rows`
assert and a four-state `geometry_status` with CLI exit 2 on the two bad states.
Full report: `_audits/cf-calibration-suite/ROWBANDS_DEFECT7_FIX_2026-08-20.md`.

Measuring tool only — the 18 value-reading specimens are untouched by it and were not re-run.
The three GEOMETRY specimens plus the promotion's own proofs were re-checked directly:

| check | result |
|---|---|
| `weber-wrong-column-pointer` — weber `741f163c` p2 | **BYTE-IDENTICAL** — 27 rules, 25 data bands, column bands 4.72 / 12.87 / 43.17 / **85.24 / 95.90**; `fitgrid` pitch still **3.1013** |
| `utah-underline-band-offset` — Graves 2014 p3 | **BYTE-IDENTICAL** — 17 rules, **16** data bands, still correctly **no** vertical rules |
| the promotion's two-crop specimen — Balderree 4.2.22 p3 `--col 74,90` | **BYTE-IDENTICAL** — 15 data bands, band 1 `23.32/3.68`, band 15 `74.32/3.89` |
| defect-3 typed-sheet control — `2018_TAinge.pdf` p3 | **UNCHANGED** — 16 data bands |
| the reproducer — Taylor Fox p3 | **RECOVERED** — **16** rules (top at **16.25** vs the wave's crop-proved 16.30), **5** column rules, 15 data bands; two-crop proof renders row 1 = `901.50 Elections Division` |

**Broad regression run (new — the suite had no page-level geometry harness before).** Sample =
pages the CLOSED waves actually measured, taken from the `geometry` column of each county's
`contributions.csv`/`expenditures.csv`: 1,186 distinct `(filing, page)` pairs enumerated, **30
per county drawn at seed 20260820 = 180 pages / 1,942 wave-proven row boxes** across utah,
weber, summit, wasatch, juab and salt_lake. Both versions run at 200 dpi; harness + both raw
output sets archived at `_backups/2026-08-20-rowbands-defect7/regression/`.

| | before | after |
|---|---|---|
| crashes | 0/180 | **0/180** |
| pages byte-identical (h + v + data bands) | — | **138/180** |
| wave-proven boxes contained in a detected band | 1,048/1,942 | **1,072/1,942** |
| …matched within 0.5 pct of the stored `y` | 871 | **892** |
| pages returning <3 rules | 18 | 17 — all now `no-reliable-geometry`, exit 2 |

No county lost containment (juab 143→143 · summit 213→213 · weber 126→126 · utah 260→261 ·
wasatch 130→139 · salt_lake 176→190). All 3 pages the diff flagged as regression candidates
were opened at the page and are improvements or honest degradations — details in the report.

No bulk-transcription authorization is claimed or changed by this note.

## 2026-08-23 — SALT LAKE COUNTY **WAVE W1 PHASE 2** PRE-FLIGHT (the 2015–2021 paper slice) — **21/21**

**Why this run was mandatory.** Two reasons, either sufficient. (1) The standing rule fires on a
configuration change and the configuration changed on **2026-08-20**: `make_snippet.py` (the
`/Rotate` page-sizing fix + the oversized-mediabox blank-crop fix) and `rowbands.py` (DEFECT-7 —
background-normalised dark-run mask, per-band column scan, off-grid rule exclusion,
`--expect-rows`, four-state `geometry_status` with exit 2). (2) This is the **first run of the
full 21**. The seven specimens added on 2026-08-18 were *authored from* the utah pre-flight, not
run by it, and `README.md` records that "the next wave to run the suite runs 21."

**Configuration under test:** `claude-opus-5` via the **Read tool** (Claude Code allotment, $0
API — the Anthropic API was never called). `pdftoppm -jpeg -r 200` **FULL-PAGE** first read,
every cited page rendered and classified; escalation = **TIGHT CELL CROP at 500–1200 dpi** only,
never a full-page dpi raise; **the document's own ARITHMETIC outranks any glyph re-read at any
resolution**; zero-glyph ruling; whitelisted decimal-comma repair only; malformed decimals
unparseable-blank; field-shift screen; withhold-rather-than-guess; mandatory `pct:` geometry per
emitted row, proved by render-back; PRIVACY city/state only.

**Why opus, not fable.** The target corpus is the SAME clerk form family, the same county and the
same handwriting era as the clerk-legacy tranche, whose 670 caches are stamped
`vision-transcribed(claude-opus-5; …)`. The proven configuration for THIS corpus is the one that
read it before.

**Fan-out:** three concurrent specimen agents (7 / 7 / 7), one configuration, plus the
coordinator's own ground-truthing of a corpus page.

**Disclosure of prior exposure (fairness caveat).** All three agents read `README.md`,
`manifest.csv` (including `expected_json`) and the earlier `runs.md` tables first — the brief
names them READ-FIRST material. This is a **mechanism verification, not a blind discovery test**.
Every row states the primary-source evidence that decided it, checkable independently of the
expected value; every specimen was re-rendered from the raw PDFs and read from scratch.

### Part A — specimens 1–7 (value reading, three negative controls)

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS — decided by arithmetic, ZERO escalations on the disputed digit** | p2 Form "A" itemizes 100 + 100 + 100 + 50 + 202.50 + 550 + 591.59 = **exactly 1,694.09**, so line 1 must lead with **1**; 1,694.09 + 105.00 = **1,799.09** = the printed cumulative expenses, leaving the printed balance **0**. Under a leading 4 neither identity closes (4,799.09 ≠ 1,799.09; balance 3,000.00 against a printed 0). **A third independent identity found this run:** p3 Form "B"'s 14 rows sum to exactly 1,799.09 — and its row-2 tens digit was *itself* bistable (46 vs 48) at a 1200 dpi tight crop; the sum, not the crop, fixed it at 48.24. The cleaner October sibling was rendered and **deliberately not used as a settlement** — that is the founding correlated-error failure |
| 2 | `summit-reversed-columns` | **PASS** | Headers read off the page first: `Current Report │ Last Report │ Cumulative Totals`. Contributions **503.00**, expenditures **511.62**. **511.62 was never emitted as a contribution total.** The 11.14-vs-11.17 balance disagreement is the filer's, retained verbatim |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway 20753 p1: Current-Report contributions and expenditures and **all three** campaign-balance cells are slashed zeros → **0.00**, verbatim `Ø` retained; Last/Cumulative 825.33 read as digits. Independent on-page check: 825.33 − 825.33 = 0, so the row denotes zero however the glyph is read |
| 4 | `summit-genuine-blank` **(NEG)** | **PASS — control held** | Francis 8196: the **entire** contributions row and the **entire** balance row are empty ruled cells — no Ø, no dash, no digit → **blank**. Expenditures `$293 ⁵⁴⁄₁₀₀` → 293.54. **0 / 0.00 was explicitly not produced** |
| 5 | `wasatch-word-zero` | **PASS incl. page coverage** | Kahler 2026-03 pp 2 AND 3. Table A's first Amount cell and its TOTAL row print `zero`; **Table B's TOTAL row falls on p3** and also prints `zero` → both **0.00**, verbatim kept. Independently checkable without images: `pdftotext -layout` emits exactly three `zero` tokens at those cells. A page-2-only pass loses a stated total |
| 6 | `wasatch-na-blank` **(NEG)** | **PASS — control held** | Hewlett 2024-06: **ONE handwritten `N/A` drawn diagonally across the TOTALS column** spanning lines 1–3 → all three **blank**. No number of any kind produced |
| 7 | `weber-dash-nil` **(NEG)** | **PASS — control held** | Allred 1.5.15 p1: line 4 Ending Balance is a bare `-` in all three columns → **blank**; line 2 likewise. **The eagerness trap is live on this page** — 4,067.20 − 4,067.20 = 0, so a configuration that "computes" the balance writes 0.00. It did not. The dash is a mark, not illegibility: real digits render cleanly in the adjacent cells |

### Part B — specimens 8–14 (currency, page selection, completeness, field shift)

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan, Summary Page located by CONTENT. Line 1 Col A `1920,00` → **1920.00** via the named whitelisted repair; **192000 not produced, a bare 1920 not produced.** The page's PER-LINE identity closes exactly: 2134.50 + 1920.00 − 4043.07 = **11.43** = printed line 7 (under 192000: 190,091.43). A 600 dpi crop shows line 4 carries a struck-through `4,435` with `1920,00` written beside it and line 5 still holds the stale figure — **the filer's own line-5 subtotal is WRONG and is retained verbatim**. The identity is run per line, never as "the page adds up" |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | Auger 6-19-06 p2: `19 875 ⁸⁵` → 19875.85, `19,435 ¹³` → 19435.13, etc. Both printed identities close: 2233.58 + 19875.85 = 22109.43 and 22109.43 − 19435.13 = 2674.30. **The discriminating evidence is the CARRY**: 58¢ + 85¢ = 143¢ forces line 5's integer part to 22109, whereas dropping the superscripts gives 22108 ≠ printed |
| 10 | `utah-checklist-decoy` | **PASS, run BOTH ways** | DECOY `5.9.2022` p5 = the Elections *Campaign Financial Disclosure Checklist*: recites every Summary-Page label, carries **zero dollar figures**, two staff-reviewed copies on one sheet → **REJECTED**. CONTROL `4.1.2022` p5 = a **genuine** Summary Page at the same ordinal → A 0 · B 10,778.00 · C 10,778.00 · D 8705.50 · E 8705.50 · F 10,778.00 · close **2072.50**, with F−D exact and Schedule A's 12 rows summing to 10,778.00. **`must_not_assume` held explicitly:** the checklist-binding 5.9 filing DOES have a real Summary Page, at **p4**, and 4.1 ALSO binds a checklist, at **p7**. Cross-filing chain closes independently: 4.1's close 2072.50 = 5.9's box A |
| 11 | `washco-wrapped-ledger` **(NEG)** | **PASS — control held** | **`counted_sum = WITHHELD`; no sum computed or claimed.** Both pages read: cash ledger then "Non Cash Expenditures", **no subtotal separating them and no grand total anywhere**, and no cover against which completeness could be gated. Five wrapped rows found; one date is literally `Various`; one amount is negative (`$-28.11`); date/vendor/amount tokens collide with no separating space. Two different bases in one undifferentiated list |
| 12 | `utah-malformed-decimal` **(NEG)** | **PASS — control held** | Ioannides: `23,744,71` (final separator a comma) and `23.744.71` (two dots) → **blank/unparseable**, not repaired, and **`23,744` not lifted out of either**. Mechanically consistent with the whitelist: both repairs are anchored on a `$`-prefixed OCR token and these are filer-typed born-digital cells. **Well-formed neighbours on the same page read normally** (23,744.71 and 32,744.71), which is what proves discrimination rather than blindness; the 32/23 transposition is the filer's and is retained |
| 13 | `utah-colAB-regime` | **PASS** | Sakievich: the Summary Page is **p6 of 6 — the LAST page**, found by content. Column A "Total this Period" promoted (28,413.88 / 21,410.78); Column B "Year-to-Date Total" **genuinely empty → blank, never summed as an increment**. Line 7 closes exactly. Independent corroboration: the rotated-landscape Schedule B's own printed footer reads `$ 21,410.78`, identical to Column A line 2 — so A is the figure the schedules tie to |
| 14 | `wasatch-field-shift` | **PASS (field-level screen, not a sum)** | Woodard / Kellogg / Vance 2026 Table A. **`donor_raw` was never a date token** — "17 Jan 2026", "1.2.26", "5May26" were not produced as names. All three sides close to their printed TOTALs and their cover lines, and **0 of 7 Table-A rows and 0 of 18 Table-B rows are shifted**. Kellogg's single Table-A row is a NARRATIVE, not a person — *"Self-Funded. Not accepting campaign contributions."* — kept verbatim and flagged as an aggregate declaration rather than an itemized donor |

### Part C — specimens 15–21 (POINTER correctness, cross-document, page selection)

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 15 | `summit-specimen-row` | **PASS** | Langston p3's first ledger line is the blank form's printed example (`Jon and Jane Doe`, PO Box 128 Coalville, **$435.00**, dated **8/25/10 on a 2022 form**), highlighted yellow. **Dropped on the arithmetic, not the highlight:** the nine real rows sum to **exactly 503.00** = the cover's Current Report contributions; including it gives **938.00**, which was not produced. Page-coverage half also held — p4/p6 are **headerless continuation grids with zero data rows**, read as empty overflow sheets, not as missing schedules |
| 16 | `utah-underline-band-offset` | **PASS** | `rowbands.py` Graves p3: **17 h-rules, 16 data bands, `v_rules_pct` = []** (correctly no verticals on an underline form), `geometry_status: ok`. `fitgrid`: pitch **4.0500**, explains 17/17, resid 0.0097. Two-crop proof at 500 dpi: row-1 box → **`745.00`**, row-4 box → **`180.75`**. **The naive band-1 box was rendered separately and LABELLED A COUNTERFACTUAL** — it shows `300.00`, the one-row-early failure. Page closes: 745.00+300.00+1500.00+180.75 = **2,725.75** = the printed subtotal and total |
| 17 | `utah-template-vintage-year` **(NEG)** | **PASS — control held** | All three filings carry the printed imprint *"2016 County & Local School Board Candidates"* (Durfey's stock even says "County Commission" on a **Sheriff's** filing — the stock's OFFICE label is template too). **Decisive census: every `2016` token in all three OCR sidecars is inside that printed string — 7/7, 5/5, 10/10** — not one 2016 date, amount or report reference exists. Against it: Schedule A dates Mar–Apr 2018, "Date of Report" June 19 2018, a clerk stamp `'18 MAY 1`. → `election_year` **2018**, `bound_in_prior_report` **false**. Cycle not reclassified |
| 18 | `weber-wrong-column-pointer` | **PASS — detected** | `741f163c` p2: **27 rules, 25 data bands**, column bands **4.72 / 12.87 / 43.17 / 85.24 / 95.90**, `fitgrid` pitch **3.1013** — byte-identical to the 2026-08-20 record. Render-back of the audited box shows **`$53,000.00`**, the AMOUNT cell. The counterfactual at the same y over the name band renders **`James Ebert`** — **and the page's six rows total 66,500.00 either way, so no sum can see it.** The four withdrawn keys now carry re-measured amount-column frames; spot-proved on `611f381e` (stored box → `$130.00`; the old address-column band at the same row renders a full street address — the privacy-relevant mis-aim) |
| 19 | `weber-swapped-cover-pair` | **PASS — detected, and the specimen's shorthand REFINED** | Both raw sha256s re-verified against `index.csv` (bytes did not move). **Honest refinement: the cover chain ALONE does not break under the swap — it merely PERMUTES** (both covers self-close and 42,670.65 → 66,670.65 → 88,220.65 → 92,389.26 still forms, just bound to the wrong `document_id`s). What fires is the chain **plus each document's own schedule anchor**: `fd9d0787` p2 prints *"Total Contributions (to line 1 of report): 21,550.00"* against a swapped 4,168.61, and vice versa. A third independent detector: schedule DATE WINDOWS — one runs 6/12–**7/17/2026**, which cannot sit inside a June-16 primary report. **Incidental finding, flagged not fixed:** `32f407e4` is a *real* chain break and a self-close failure (24,000.00 + 20,550.00 ≠ 88,152.04), its Last column holding the prior filing's *This* values — but its own schedule anchor matches its cover, so the gate cleanly separates **filer error** from **transcriber swap** |
| 20 | `weber-rtl-rows` | **PASS** | Hansen/Thompson 2014 reverse-rotated landscape sheets. `rowbands.py` returns h-rules that are the COLUMN grid and 27 v-rules at ~2.98 pct pitch that are the ROW grid — `axis: "x"`, descending. **Order proved by render-back, not by sum:** Hansen row 1 → **`552.22`**, row 2 → **`170.00`** (sum 722.22 = the printed Total, which is exactly the check that cannot see order). **Ascending counterfactual rendered explicitly:** band 1 becomes an **empty cell at the unused far end of the grid** — the ledger reversed |
| 21 | `summit-swapped-pages` | **PASS** | Each page classified from its **own printed header**, never by ordinal: 1059 / 23013 / 24377 all put *Itemized Expense Report* on p2 and *Itemized Contribution Report* on p3. Bonus internal checks: Ames's three expense rows total **579.46** = his single Personal Contribution, a self-funded campaign whose two sides cross-check; and 1059 p3's four sub-$50 rows total **91.80** = its printed "Total for $50 or less", leaving **4,934.10** = the printed "Total for over $50" exactly |

**Score: 21 / 21 PASS.** All **eight** negative controls / `must_not_produce` / `detect` clauses
answered explicitly and held: 4, 6, 7, 11, 12 and 17 recovered nothing; 15's 938.00 and 16's
row-1-at-300.00 were produced only as *labelled counterfactuals*; 18 and 19 were both detected,
19 without relying on single-page arithmetic. Specimen 1 was decided with **zero escalations on
the disputed digit**. Every geometry claim rests on a render-back; every value claim on a printed
anchor on the document's own page.

### Did the 2026-08-20 tooling changes preserve the audited geometry?

**Yes on both standing anchors.** `weber 741f163c` p2 → 27 rules / 25 data bands / columns
**4.72 / 12.87 / 43.17 / 85.24 / 95.90** / pitch **3.1013**, and the stored
`pct:85.23,16.62,10.66,3.17@p2` still lands on `$53,000.00`. `utah Graves` p3 → 17 rules /
**16** data bands / still correctly **no** verticals / pitch **4.0500** at residual 0.0097, both
proof crops rendering their recorded values. The `make_snippet.py` rotation and
oversized-mediabox fixes are load-bearing here and behaved: every crop taken on a **rotated
landscape** sheet (specimen 20, and the corrected weber frames in 18) rendered a populated cell
rather than a blank or a clipped `$`.

One measurement moved, and it is an improvement inside tolerance. `weber 4acceac4` p2 — measured
2026-08-18, never in a `runs.md` table — now reads **5.30 / 13.21 / 42.72 / 83.81 / 94.13**
against the record's 5.26 / 13.19 / 42.69 / 83.78 / 94.10: a uniform +0.03/+0.04 pct, ~0.7 px at
200 dpi, well inside a printed rule's own 2–4 px thickness. And where that record had to
**interpolate** a missed row rule at 74.50 on the constant pitch, the current detector **finds it
directly at 74.49** (27 v-rules where the wave saw 26), independently validating the
interpolation to 0.01 pct. Nothing regressed; the drift is sub-pixel and the recovery is real.

### Two housekeeping corrections made from this run

* **`manifest.csv` — `rhodes-4v1-fax` `source_ref` now carries PATHS + sha256.** It previously
  read only *"campaign_finance raw: Shannon Rhodes December-2018 fax … CLEANER SIBLING: her
  October copy"*, with no path. Given no path, the pre-flight brief's author resolved "Rhodes" to
  the unrelated **2014 Teri B. Rhodes school-board covers** — single-page filings with no Form A,
  no four-figure amount and no bistable glyph, on which the specimen is untestable. The agent
  caught it by content and located the real documents. The specimen's expected value is
  unchanged; only the citation was strengthened.
* **`weber-swapped-cover-pair`'s `how` clause is shorthand.** As run, the cover chain permutes
  rather than breaks; the detector that actually fires is the chain **plus** each document's own
  printed schedule anchor (and, independently, its schedule date window). Recorded here rather
  than rewritten into `expected_json`, because `detect: true` — the property the specimen tests —
  held.

**Pre-flight PASSED; bulk transcription of the salt_lake_county 2015–2021 paper queue AUTHORIZED**
under the per-row contract at `_backups/2026-08-23-slco-w1p2/AGENT_BRIEF.md`, with the three
corpus-specific traps that brief carries (`schedule-total-vs-summary-gap`; the three structural
shapes; `Occupation/Employer` capture) and the reconciliation-basis rule of 2026-08-17.

### 2026-08-23 — POST-WAVE NOTE: what the SLCo W1 corpus produced for the suite

The 21/21 pre-flight above authorized the wave; the wave then ran 130 filings / 717 pages and
**produced five new specimen candidates**, ground-truthed at the page with citations, drafted at
`_backups/2026-08-23-slco-w1p2/SPECIMEN_CANDIDATES.md` and **awaiting promotion into
`manifest.csv`** (not added here unilaterally — the suite's own rule is that a specimen carries an
expected value and an evidence citation, and these want an owner's eye on the three-way set).

| candidate | class | why it is worth a row |
|---|---|---|
| `slco-schedule-scope-split` | reconciliation basis, **negative control** | Snelgrove Apr-2016: the schedule's printed total (3,161.02, in-kind INCLUDED) and Summary line 2 (501.02, in-kind EXCLUDED) measure different things. Expected: `reconciles_expend` BLANK. **`must_not_produce`: `False` with a +2,660.00 delta.** Fires at the BUILD, not the transcriber — no arithmetic gate can see it |
| `slco-cumulative-in-the-grand-total-slot` | reconciliation basis, **inverted** | DeBry 2015 YE: the `TOTAL (Sum of subtotals from all pages)` cell holds the CYCLE-CUMULATIVE figure (= Column B) while `SUBTOTAL FOR THIS PAGE` holds the PERIOD one (= Column A). Four independent sightings across the wave; **the same filer flips convention between his original and his amendment**, which is why the test is per PAGE |
| `slco-same-scope-filer-disagreement` | reconciliation basis, **positive control** | Evershed 2018 YE: 20 rows = attachment total = county stub total = Summary line 6, while line 2 prints $14.05 less. Expected: a REAL published delta. **Discriminates the two above** — a configuration that blanks this one has over-applied the mechanism |
| `slco-decimal-point-omitted` | arithmetic-outranks-glyph, currency | Goodfellow line 7 written `173634`; the same page proves 1736.34 three ways. Expected 1736.34 with the verbatim retained; **must not produce 173634.00 (a 100x error) and must not BLANK a value the page proves.** Sibling of utah's Smith-2014 `$3446` |
| `slco-rotated-attachment-band-drift` | GEOMETRY, **negative control** | McAdams Nov-2016 pp.4-9: every value correct and both sides reconciling to the cent while the stored `pct:` boxes drift ~1-2 row bands; `rowbands.py` returns one fewer band than ink rows on five of six pages. Expected: **withheld** (the suite's own "frame corrected OR geometry withheld") |

**The three-way set is the point.** Two of them require a BLANKED verdict and the third requires a
PUBLISHED delta, so they cannot be satisfied by a single rule about non-summary anchors — which is
exactly the failure the wave's build made, four times, before arriving at a two-test discriminator
(*did the record anchor on a different FIGURE?* / *on a different LINE?*). Graded singly, any one
of them is passable by a configuration that gets the other two wrong. **They should be added and
run together.**

Two further notes for whoever promotes them:

* **`utah-malformed-decimal` has a latent conflict with the shared parser.** Measured 2026-08-23:
  `common.repair_money_line('23.744.71') -> 23744.71` and `('23,744,71') -> 23744.71`, against the
  specimen's expected `""`. Nothing published is wrong today (a repo-wide cache scan found zero
  summit/utah caches holding such a string — their transcribers blanked them at the page), so the
  guard currently lives in transcriber judgement rather than in code. Filed in LEADS.md with the
  reproducing command; the fix worth considering is making the repair **opt-in per form family**.
* **No configuration change was made after the pre-flight**, so the 21/21 authorization stands
  unmodified for this wave. The build-side reconciliation-basis logic changed four times during
  the wave, but that is a BUILD rule about which printed figure to compare against — it reads no
  pixels and is outside the suite's scope.

## 2026-08-23 — PHASE B FINAL WAVE, **WASHINGTON COUNTY** PRE-FLIGHT (the 100 handwritten cover forms) — **21/21 PASS**

Run before any page of the washington vision queue was transcribed. Configuration under test:
**`claude-opus-5` reading page images with the Read tool, no Anthropic API, $0 credit** —
full-page first read at `pdftoppm -jpeg -r 200`, escalation ONLY as tight cell crops at
500–1200 dpi, arithmetic closure outranking glyph reading, the zero-glyph ruling, and the
whitelisted decimal-comma repair only. Two agents, specimens 1–11 and 12–21, each re-rendering
every page from the raw PDFs and required to state the primary-source evidence it personally
observed (prior exposure to expected answers makes this a MECHANISM verification, not a blind
test — a copied answer scores FAIL).

**Result: 21 of 21 PASS. All 18 negative-control / `must_not_produce` / `detect` /
`must_not_assume` clauses held**, including every case whose correct answer is a BLANK, a DROP
or a WITHHELD sum.

Findings worth carrying (each verified at the page, not asserted):

* **#1 `rhodes-4v1-fax` was decided by arithmetic with the sibling copy NEVER RENDERED**, and a
  *third* independent identity was reproduced this run: Form "B"'s 14 rows sum to exactly
  1,799.09, and that closure — not the crop — fixes two of its own bistable cells. One of them
  (`$4?.24` → 48.24) **stayed bistable at 900 dpi**. The specimen's own lesson, reproduced.
* **#5 `wasatch-word-zero` refined:** the Kahler cover's TOTALS boxes are *genuinely empty* —
  the three `zero` tokens live only on the schedule TOTAL rows (pp. 2–3). A cover-anchored
  stated-totals pass returns blank on a filing whose stated totals are 0.00.
* **#12 `utah-malformed-decimal` — the LEADS repro command is WRONG and the conflict is
  narrower than filed.** `common.repair_money_line` is `$`-ANCHORED: `('23.744.71')` and
  `('23,744,71')` both return UNCHANGED with `changed=False`; only the `$`-prefixed forms
  repair. So the latent conflict **cannot fire on the Ioannides page as printed**.
* **#16 / #18 / #20** — the three geometry specimens were re-measured and reproduce the stored
  records to sub-pixel (`fitgrid` pitch 4.0500 / 3.1013; Hansen's column rules within
  +0.03 pct), and each was proved by a render-back plus an explicitly labelled counterfactual.
* **#19 `weber-swapped-cover-pair` sharpened:** the cover chain does **not break** under the
  swap — it *permutes* (both covers self-close). What fires is each document's own printed
  schedule anchor, corroborated by the schedule DATE WINDOW. The gate cleanly separates a
  FILER ERROR (anchor matches its own cover) from a TRANSCRIBER SWAP (anchor disagrees).

Manifest imprecision found (the page governs; **five specimens still carry no path/sha**):
`slco-superscript-cents` (two different documents used across prior runs — pin
`salt_lake_county/campaign_finance/raw/clerk_legacy/20_june_auger_janice06.pdf` p2),
`weber-dash-nil`, `utah-colAB-regime` and `utah-template-vintage-year` (two DIFFERENT Sakievich
filings sit in adjacent rows), and `washco-wrapped-ledger` (the directory holds a Contributions
*and* an Expenditures Lin Alder PDF; the specimen is the **Expenditures** one). Also:
`utah-colAB-regime`'s prior-run Schedule-B corroboration **is not reproducible in that file**
and should be dropped or re-cited; `utah-template-vintage-year`'s imprint string is **not
uniform** across its three filings (Durfey's stock reads "County Commission & Local School Board
Candidate"), so a literal grep for the other two's string scores a false 0/10.

New specimen candidates proposed (not yet promoted): `wasatch-cover-blank-schedule-total`,
`summit-uncloseable-cover` (Langston 20765 — no identity closes and none should be repaired),
`slco-struck-and-rewritten-cell`, `mixed-currency-conventions-in-one-row`,
`page-local-mixed-cent-convention`, `rotated-crop-reading-discipline` (a correct pointer misread
because the crop was judged unrotated), `filer-error-vs-transcriber-swap` as a positive control,
`intra-chain redaction asymmetry`, and `near-homograph-sibling-filename`.

## 2026-08-24 — SALT LAKE COUNTY **WAVE W2** PRE-FLIGHT (the EasyVote row-less residue) — **21/21**

**Why this run was mandatory.** A new MODEL TIER earns no bulk-transcription rights without the
suite (README protocol): wave W2 is run by **Kimi K3**, and every prior run on this instrument
was a Claude tier. The target corpus is the SLCo EasyVote 2022/2024/2026 row-less residue (197
has-detail filings, ~18,433 estimated lines; plus 143 missing covers) per
`salt_lake_county/campaign_finance/W2_HANDOFF.md`.

**Configuration under test:** `Kimi K3` via the **ReadMediaFile** tool (no external vision API).
`pdftoppm -jpeg -r 200` **FULL-PAGE** first read, every page classified by its own printed
header; escalation = **TIGHT CELL CROP at 500–1200 dpi** only; **the document's own ARITHMETIC
outranks any glyph re-read at any resolution**; zero-glyph ruling; whitelisted decimal-comma
repair only; malformed decimals unparseable-blank; field-shift screen; withhold-rather-than-guess;
geometry claims only with a render-back proof. Fan-out: three concurrent specimen agents
(7/7/7), one configuration; coordinator brief at `_backups/2026-08-24-slco-w2/CALIBRATION_BRIEF.md`.
Same fairness disclosure as prior runs: agents read README/manifest/runs first (mechanism
verification), but every value was re-read from fresh renders of the raw PDFs.

### Part A — specimens 1–7 (value reading, three negative controls)

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 1 | `rhodes-4v1-fax` | **PASS — arithmetic, ZERO escalations on the disputed digit** | Form A's seven rows sum exactly **1,694.09**; the cover closes only under a leading **1** (1,694.09+105.00=**1,799.09**=printed cumulative, balance 0; under 4: 4,799.09≠1,799.09). The cleaner October sibling was **not rendered and not used** — correlated-error settlement avoided by construction |
| 2 | `summit-reversed-columns` | **PASS** | Headers read off the page first (Current│Last│Cumulative): contributions **503.00**, expenditures **511.62**; 511.62 never emitted as contributions. Filer's 11.14-vs-11.17 balance disagreement retained verbatim |
| 3 | `summit-zero-glyph` | **PASS** | Siddoway: Current contributions/expenditures and all three balance cells slashed zeros → **0.00**, verbatim `Ø` kept; 825.33−825.33=0 corroborates on-page |
| 4 | `summit-genuine-blank` **(NEG)** | **PASS — control held** | Francis: entire contributions row and balance row are empty ruled cells → **blank**; expenditures 293.54 (superscript). **0/0.00 explicitly not produced** |
| 5 | `wasatch-word-zero` | **PASS incl. page coverage** | Kahler pp 2 AND 3 both read: Table A total `zero` and Table B total ON P3 `zero` → both **0.00**; a p2-only pass loses a stated total |
| 6 | `wasatch-na-blank` **(NEG)** | **PASS — control held** | Hewlett: one diagonal `N/A` across the TOTALS column spanning lines 1–3 → all three **blank**; no number of any kind produced |
| 7 | `weber-dash-nil` **(NEG)** | **PASS — control held** | Allred 1.5.15: bare `-` in all three columns of lines 2 and 4 → **blank**. The eagerness trap is live (4,067.20−4,067.20=0) and the computed 0.00 was deliberately NOT emitted |

### Part B — specimens 8–14 (currency, page selection, completeness, field shift)

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 8 | `slco-decimal-comma` | **PASS, closed by arithmetic** | K. Morgan: Line 1 Col A `1920,00` → **1920.00** via the NAMED whitelisted repair; **192000 not produced**. Typed Schedule A attachment sums exactly 1920.00 and prints its own `$1,920.00`; chain closes 2134.50+1920.00=4054.50=4043.07+11.43. Filer slip found and retained verbatim: his printed Line 5 reads `4,435.00` against his own closed chain (4054.50) |
| 9 | `slco-superscript-cents` | **PASS, closed by arithmetic** | Auger: `19875`⁸⁵ → **19875.85**, `19,435`¹³ → 19435.13 etc. The CARRY is decisive: 2233.58+19875.85=22109.43 requires the cents carry (58+85=143); typed schedules print TOTAL $19,875.85 / $19,435.13, matching to the cent |
| 10 | `utah-checklist-decoy` | **PASS, run BOTH ways** | May-Cox p5 = clerk checklist, recites every label, **zero dollar figures** → REJECTED by content; April-Cox p5 at the SAME ordinal is a GENUINE Summary Page (A 0 · B 10,778.00 · D 8,705.50 · close **2,072.50**, schedule sums match). May's own real Summary Page found at p4 by its printed header (its A = April's close, cross-filing chain ✓); April binds its checklist at p7 (the OTHER revision). `must_not_assume` held explicitly |
| 11 | `washco-wrapped-ledger` **(NEG)** | **PASS — control held** | **`counted_sum = WITHHELD`, no sum computed.** Money tokens inside wrapped NAME text (`Miscellaneous Donors $50.00 / Or less (18 donors)`), the amount flipping sides of the wrap pair, one aggregate row SPLIT ACROSS A PAGE BOUNDARY, `Various` dates, and no printed total anywhere — completeness not provable |
| 12 | `utah-malformed-decimal` **(NEG)** | **PASS — control held** | Ioannides 24231: `23,744,71` and `23.744.71` → **BLANK, unparseable, verbatim kept**; no silent repair and **no clean prefix lifted** even though the page offers hints (schedule totals print 23,744.71). Confirms in vivo the latent `repair_money_line` conflict filed 2026-08-23 — the guard lives in transcriber judgement, not code |
| 13 | `utah-colAB-regime` | **PASS** | Graves 2014: Column A promoted (2,725.75/2,725.75), Column B (4,656.61) kept cumulative, never summed as increments; chain and both schedule sums close exactly. **Honest deviation: the manifest's "Summary Page is the LAST page" did not hold for this filing (it is p2 of 4)** — content classification covered it; manifest wording may overfit |
| 14 | `wasatch-field-shift` | **PASS (field-level screen)** | Woodard/Kellogg/Vance: no date token (`17 Jan 2026`, `1.2.26`, `5May26`) ever landed in `donor_raw`, on pages where the amounts sum exactly EITHER WAY. Kellogg's narrative aggregate row kept verbatim and flagged |

### Part C — specimens 15–21 (POINTER correctness, cross-document, page selection)

| # | specimen | result | what this configuration produced |
|---|---|---|---|
| 15 | `summit-specimen-row` | **PASS** | Langston p3 row 1 (Jon and Jane Doe **$435.00**, dated 8/25/10 on a 2022 form) **DROPPED on arithmetic, not the highlight**: nine real rows sum exactly **503.00** = cover; **938.00 never produced**. Blank interleaved pages (p2/p4/p6) read as empty, not missing schedules. p5's expense ledger carries its own specimen row; ten real rows sum exactly 511.62 |
| 16 | `utah-underline-band-offset` | **PASS** | Graves p3 two-crop proof at 500 dpi: stored row-1 box renders **`745.00`**, row-4 renders **`180.75`**; page closes 2,725.75 = printed subtotal AND total. The naive one-row-early box rendered as a **labelled counterfactual** (shows `300.00` — the exact failure screened) |
| 17 | `utah-template-vintage-year` **(NEG)** | **PASS — control held** | All three 2018 filings print a `2016` stock imprint; **every `2016` token in the OCR sidecars sits inside that printed string (7/7, 5/5, 10/10)** against June-2018 signatures and an `'18 MAY 1` clerk stamp → `election_year` **2018**, `bound_in_prior_report` **false** |
| 18 | `weber-wrong-column-pointer` **(detect)** | **PASS — detected** | Render-back of the re-measured stored box (Ebert p2 row 1) renders **`$130.00`** (the amount cell); the counterfactual over the name-column band at the same row renders the donor NAME. Six rows total 6,230.00 either way — no sum can see it |
| 19 | `weber-swapped-cover-pair` **(detect)** | **PASS — detected without single-page arithmetic** | Both covers self-close AND are signed the same day (chain permutes, does not break); what fires is the chain **plus each document's own printed Form A anchor** (21,550.00 vs 4,168.61, each matching its own cover) and independently the schedule DATE WINDOW (6/12–7/17/2026 cannot sit inside the June-16 primary report). Matches the 2026-08-23 refinement of the specimen's `how` shorthand |
| 20 | `weber-rtl-rows` | **PASS** | Hansen 2014 reverse-rotated sheet: `axis: x`, bands **descending**, proved by render-back (row 1 → **`552.22`**, row 2 → **`170.00`**, sum 722.22 = printed Total — the check that cannot see order). Ascending counterfactual rendered: band 1 is an **empty cell at the unused far end** |
| 21 | `summit-swapped-pages` | **PASS** | 1059/23013/24377 each classified from their own printed header: EXPENSE on p2, CONTRIBUTION on p3. Bonus checks reproduced (Ames 579.46 self-fund cross-check; 1059 sub-$50 rows 91.80 = printed, leaving 4,934.10 exactly) |

**Score: 21 / 21 PASS.** All eight negative-control / `must_not_produce` / `detect` clauses
answered explicitly and held; specimen 1 decided with zero escalations on the disputed digit;
every geometry claim rests on a render-back with the counterfactual rendered and labelled.

**Pre-flight PASSED; bulk transcription of the SLCo EasyVote residue queue AUTHORIZED** under
the per-row contract at `_backups/2026-08-24-slco-w2/AGENT_BRIEF.md`.

**Configuration note for future runs.** Two agents independently confirmed the 2026-08-23
latent-conflict note: `common.repair_money_line` would emit 23744.71 for Ioannides' malformed
cells; the passing behavior lives in transcriber judgement, not code. And specimen 13's
manifest wording ("the Summary Page is the LAST page") overfits — Graves 2014 binds it at p2;
content classification is the rule that must hold.

## 2026-08-23 — PHASE B FINAL WAVE, **CACHE COUNTY** PRE-FLIGHT (the 176-document handwritten queue) — **21/21 PASS**

Run fresh for cache, before any page of its queue was transcribed, in the same configuration
(`claude-opus-5` + Read tool, no API; full-page first read at `-r 200`; escalation only as tight
cell crops at 500–1200 dpi; arithmetic outranks glyph; zero-glyph ruling; whitelisted
decimal-comma repair only). Two agents, specimens 1–11 and 12–21.

**Result: 21 of 21 PASS. Every negative-control / `must_not_produce` / `detect` / `acceptable` /
`must_not_assume` clause held; zero values were "recovered" on any control.**

Cache is the **home county of specimen #1**, so that one was run with deliberate discipline:

* **#1 `rhodes-4v1-fax` was decided by ARITHMETIC ALONE and the sibling copy was NEVER OPENED.**
  Three independent identities close on `1`: Form A's 7 rows sum to exactly **1,694.09**;
  1,694.09 + 105.00 = **1,799.09** = the printed cumulative line 3 with a printed balance of 0
  (under a leading `4` the balance would have to be 3,000.00 against a printed 0); and Form B's
  14 rows sum to **1,799.09**. The one 900 dpi crop taken is recorded as **legibility only, of
  zero evidential weight**.
* **A NEW property of that specimen was found: Form B carries TWO simultaneously bistable 6/8
  cells** (rows 2 and 10). Four readings are individually legible and **exactly one closes**
  (48.24 and 69.74 → 1,799.09; the others give 1,797.09 / 1,817.09 / 1,819.09). The run's own
  first full-page read guessed 46.24 and 89.74 and **the sum corrected both** — a system, not a
  cell, and no single-cell escalation can pass it.

Other findings worth carrying:

* **#5 `wasatch-word-zero`** — the Kahler cover's TOTALS cells are **empty**, so the filing's only
  stated totals are the two word-`zero` schedule TOTALs on pp. 2–3; the document carries the
  blank-stays-blank rule and the zero-glyph rule **at once, on different pages**.
* **#7 `weber-dash-nil`** — the eagerness trap is live: lines 1 and 3 both print 4,067.20, so a
  computing configuration writes an Ending Balance of 0.00. It did not; the dash stayed blank.
* **#8 / #9** — both slco currency specimens were closed by the page's OWN per-line identity, and
  #9's discriminating evidence is the **CARRY** (2233 + 19875 = 22108, but the page prints 22109,
  which exists only if 58¢ + 85¢ carried — the page proves the raised digits are cents).
* **#10 `utah-checklist-decoy` — `must_not_assume` answered in BOTH directions**: the
  checklist-binding filing *does* have a real Summary Page (p4), and the control filing *also*
  binds a checklist (p7).
* **#18 / #20** — the two geometry specimens were proved by **render-back plus an explicitly
  labelled counterfactual**, and #18 reproduced the privacy-relevant mis-aim (the withdrawn
  address-column band renders a donor's street address).
* **#19** — confirmed again that under a cover swap the chain **permutes** rather than breaking;
  what fires is each document's own schedule anchor plus its schedule DATE WINDOW.

Manifest imprecision found (the page governs — these are citation defects, not verdict defects):
`utah-malformed-decimal`'s `entity` column says **utah_county but the document is a SUMMIT
filing** (Ioannides 24231, p1) and carries no path; `utah-colAB-regime` carries no path AND the
2026-08-23 run's locator prose is **wrong** (it records a 6-page Sakievich with the Summary at p6
and figures 28,413.88 / 21,410.78 — but `2018_COMA.Sakievich.pdf` is **8 pages** with its Summary
at **p8** reading 10,421.17 / 9,464.37, and those other figures live in the **2020** filings);
`slco-superscript-cents` and `slco-decimal-comma` both cite `CLAUDE.md` line numbers that have
drifted (the currency-repair section is at :261–262 and the superscript rule at :343–345), and
specimen 9 has a **silent near-miss** — `jauger_61906amendment.pdf` is a different document whose
p2 renders blank; `wasatch-word-zero` and `summit-reversed-columns` each have a near-name decoy in
their own directory; `wasatch-na-blank`'s "N/A in all three cells" is really **one** N/A drawn
across the column; `summit-specimen-row` under-describes itself — the SAME filing carries a
**second** printed template row on its EXPENSE schedule (p5, `Name of Business … $512.00`), also
droppable by arithmetic (ten real rows = 511.62); and weber `741f163c`'s recorded band count
(25 data bands) is really **24** though every load-bearing measurement reproduces exactly.

New specimen candidates proposed (not promoted): `rhodes-two-unknown-simultaneous-close`,
`utah-mixed-form-vintage-in-one-filing` (one filing binding TWO template vintages — cover stock
and schedule stock disagree), **`zero-glyph-in-a-DIGIT-POSITION`** (`956.8Ø` — the ruling is
written for whole cells; a configuration can be wrong in two opposite directions here),
`colAB-first-report-B-equals-A` (YTD legitimately equals period, so A+B double-counts exactly and
no per-column sanity check can see it), `specimen-row-on-BOTH-sides`,
`utah-clerk-name-imprint-vintage` (the officeholder name on the stock is a template token),
and `fraction-over-100 cents` (`$293 ⁵⁴⁄₁₀₀`).
