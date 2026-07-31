# campaign_finance/ — Bluffdale municipal candidate disclosures

Additive dataset (`expand-city-sources` Source 6), built 2026-07-12. **ACQUISITION LAYER**
(raw filings + provenance `index.csv` + election join; no structured dollar layer yet).
Completes the **elections → members → votes** chain: who funded the candidates whose
roll-call votes live in `../meeting_minutes/`.

## What this is

**106 filings** across **five cycles (2017 / 2019 / 2021 / 2023 / 2025)**, Mayor + 5 at-large
council candidates. **All self-hosted on the city website** (`source=city_website`, CivicPlus
DocumentCenter) — Bluffdale does not use `disclosures.utah.gov` or a county portal for
municipal filings. **50 born-digital `text` + 56 `scanned`** (OCR'd, labeled per file in
`extraction_method`). Filenames are `YYYYMM`-prefixed to prevent basename collisions across
filing periods; raw retained verbatim under `raw/` (+ `_fetch_log.jsonl` provenance).

## Filing-type / double-count trap

`filing_type` ∈ `interim` (78) / `summary` (28) is set **per PDF** — candidates file MULTIPLE
reports per cycle (interim pre-primary/pre-general + a year-end summary), so this is **NOT one
filing per candidate**. **Do NOT sum filings for a per-candidate or per-race dollar total** —
that awaits the structured layer + `scripts/campaign_finance/cycle_totals.py`. This layer is
documents + the election join only; it carries no dollar figures.

## Election join (the payoff)

Join by normalized name + `election_year` to
`../election_results/bluffdale_results_by_candidate.csv`. **100% join: all 106 filings map to
a candidate** (`in_election_results=yes`), **99 `high` / 7 `medium`** confidence
(`join_confidence`). `matched_election_candidate` carries the canonical UPPER-CASE election
name. Bluffdale is at-large, so `district` is blank on every row.

Cycles **2017 and 2019 predate the 2020 minutes floor** but are in scope — campaign-finance is
candidate-keyed and these filers seated council members serving in the 2020+ record (e.g.
Aston, Crockett, the 2020-01-06 oath cohort). From a winner here, their council votes are in
`../meeting_minutes/all_votes.csv` (join by person; the Mayor does not vote — see `../CLAUDE.md`).

## Schema

`index.csv` — §9 campaign-finance contract header (`date, candidate, office, election_year,
filing_type, reporting_period, title, source_url, retrieved_date, format, extraction_method,
path`) + city cols `district` (blank — at-large), `source`, `in_election_results`,
`matched_election_candidate`, `join_confidence`, `date_precision`, `docid`. `path` is
dataset-relative including `raw/`.

## `vision/` — scanned-filing transcriptions (2026-07-17, wave-2)

The **56 scanned filings** were transcribed to `vision/<sha1(index-path)[:8]>.json` via the
**Read-tool vision method** (`/cf-vision-transcribe`, $0 API / Claude Code allotment), EXCEPT the 2
pre-2020-floor 2017 filings (out of scope) → **54 caches** (0 bad JSON; 427 contribution + 335
expenditure rows; 4 honest-empty). Cache key + JSON schema match the **midvale** tranche-1 sibling
(`contributions`/`expenditures`/`totals_printed`, plus a `reports[]` variant for the one bundled
2025 PDF). Amounts verbatim; illegible → `null`, never inferred; filer arithmetic gaps preserved.
**These are PRE-STAGED inputs — NOT yet consumed:** Bluffdale has no `build_finance.py` yet (the
structured dollar layer is owner-gated / separately queued). Do NOT start the structured layer here.

## 2026-07-17 — STRUCTURED DOLLAR LAYER BUILT (vision-cache family)

`build_finance.py` (family **`vision_cache`**, shared `scripts/campaign_finance/vision_lib.py`
+ `driver.py`) now writes the four DERIVED, regenerable CSVs — `contributions.csv` (410) /
`expenditures.csv` (331) / `filing_totals.csv` (**106 rows = full inventory**: 57
vision-transcribed + **49 below-floor 2017/2019 inventory-only** rows with dated reasons) /
`cycle_totals.csv` (46 candidate-cycles). `validate_finance.py` **PASS (0/0)**;
`scripts/validate_city.py bluffdale_city_council/` **0 FAIL**. Regenerate, never hand-edit:
`python3 build_finance.py && python3 ../../scripts/campaign_finance/cycle_totals.py bluffdale`.

Key build decisions (all evidence-based; see `build_finance.py` docstring):

- **Cache shape differs from midvale.** Bluffdale wave-2 caches nest printed totals under
  `totals_printed:{...}` (no top-level totals, no `_meta`). `_adapt_cache` (city-local — the
  shared `scripts/` are read-only and unchanged) hoists them so build_result + regime
  detection see the covers. Caches are never edited.
- **3 in-floor 2023 born-digital `text` filings transcribed** from their clean pdftotext
  layer into new caches (`vision/a720a221` Erik Swanson 5969, `b9182572` Ulises Flynn 5971,
  `ec057535` Gregory Wilding 5996). Swanson & Flynn Oct-05 are post-primary **$0** "no new
  activity" reports (their primary money is in their Aug caches); **Wilding's Oct-24
  Pre-General carries real money** ($5,100 cash + $20 in-kind Bart Barton / $3,046.38) and is
  part of his cumulative chain. Vision cache count is now **57** (54 wave-2 + these 3).
- **The Pavlakis 2025 `reports[]` bundle** (`a800473e`) staples an AMENDED re-file of the
  Pre-General report ahead of the ORIGINAL of the SAME period (identical $7,665.70/$7,312.88
  covers; the amendment only renamed anonymous donors). `_adapt_cache` collapses it to the
  **amended** sub-report (kept + noted; original excluded) — the filing now shows 21 contrib
  rows (not 42) and reconciles both sides exactly. Bundle handled at build, cache untouched.
- **In-kind convention is MIXED** across filers (Pavlakis's cover INCLUDES in-kind at face
  value; Wilding/others EXCLUDE it). `reconcile_cash_only=False` (midvale default); the
  cash-only filers reconcile via the driver's alt-convention fallback (noted per row).
- **Candidate-name canonicalization** (`_CANON` in build_finance.py; index.csv NOT edited):
  a few filers split one cycle across two `candidate` spellings, all confirmed same person by
  `matched_election_candidate` — Eric/**Erik Swanson**, Greg/**Gregory Wilding**,
  Steven/**Steve Austin** (2023); Allen/**Albert Allen Larsen**, Jeff/**Jeffrey Steele**
  (2025). Each folded to the OTHER spelling that already exists in index (validator's
  (candidate,year)∈index still holds) so cycle_totals groups the person once.
- **Per-candidate regimes** (`detect_regimes`, printed every build): 2023 is dominated by
  **cumulative** restatement chains (latest wins; e.g. Wilding 4,500→5,100→6,097.33→6,397.33,
  earlier superseded), 2025 by **per-period** filers (Aug/Oct-07/Oct-28/Dec disjoint — SUM).
- **7 `cycle_overrides.csv` rows** (the midvale precedent — a per-period filer whose Dec
  "Final"-typed report is itself a disjoint PERIOD report, which the summary-vs-interims rule
  drops): Alan Lord, Steve Austin (2023); Albert Allen Larsen, Mackey Smith, Jeffrey Steele,
  Wendy Aston, Connie Pavlakis (2025) → cycle = sum of ALL filings. Reasons carry the
  per-filing arithmetic.
- **Reconciliation:** 49/57 transcribed filings reconcile both sides; **8 carry verbatim
  filer/transcription mismatches, flagged `needs_review`, NEVER adjusted** — Blain Dietrich
  2021 (expend +$6, source arithmetic; spot-checked vs the raw PDF images), Connie Robbins 2
  2021 (contrib totals-only + Column-A expend un-itemized in-source — see 2026-07-18 note),
  Mark Hales 2023 Aug (expend −$10.52) & Oct-24 (a verbatim "Uncashed check of $2000" donor
  over a $0 cover), Larsen Oct-07 (−$10.10, a named flag), Steele Oct-07 (−$0.03), Aston
  Oct-07 (−$0.02), Pavlakis Oct-28 (−$9.90). (Was 9 before 2026-07-18: Natalie Hall 2025
  Oct-07 cleared when the expenditure-sign mis-read was corrected — see the dated note below.)

### 2026-07-18 — owner-authorized evidence-pass adjudication (`cf-adjudication`)
Re-visioned the four flagged filings via the Read-tool ($0 API); documented overrides only on
unambiguous evidence; source values never altered. Old caches/CSVs backed up in
`_backups/2026-07-18-cf-adjudication/bluffdale/`.

- **Natalie Hall 2025 — RESOLVED (sign mis-read corrected).** Oct-07 (`9008`) and Oct-28
  (`9049`) Schedule-B line items were transcribed verbatim WITH the form's outflow
  parentheses, which the parser read as NEGATIVE. Re-rendered both cover sheets: the form's
  own running-balance arithmetic proves expenditures are POSITIVE magnitudes SUBTRACTED
  (Oct-07: $2,324.30 begin + $21,035.67 contrib = $23,359.97 subtotal − **$16,135.22 exp** =
  $7,224.75 end; Oct-28: $7,224.75 + $1,100.00 = $8,324.75 − **$2,336.44 exp** = $5,988.31,
  chaining off Oct-07's ending balance). Caches corrected (parentheses removed, magnitudes
  unchanged; Oct-28's sign-flipped printed total `(2,336.44)`→`2,336.44`); both filings now
  reconcile both sides (Δ 0.00), flag cleared. **Cycle spent corrected $13,798.78 → $18,471.66**
  (= $16,135.22 + $2,336.44 summed interims); raised unchanged at **$22,135.67**. cycle_totals
  still notes MIXED (summary $4,252 vs summed interims $18,472 — takes larger); the Dec-04
  "Final" ($4,251.59 exp, $0 contrib) is treated as a summary and dropped, NOT added as a
  disjoint period — residual open question whether Hall (like the other 2025 per-period filers)
  warrants a Dec-04-is-a-period override; left unoverridden pending owner call.
- **Connie Robbins 2 2021 (`4471`) — CONFIRMED FAITHFUL (gap is in-source, candidate-side).**
  Re-visioned all 5 pages: Schedule A (contributions) is hand-marked "none" and its total boxes
  are blank though the Summary Page reports a $6,445.84 lump; the Summary Page splits
  expenditures into Column A (thru Oct 25) **$5,619.41** and Column B (thru Dec 2) **$826.43** =
  Column C total **$6,445.84**, but only the Column-B period is itemized on Schedule B (Rate Now
  $187.77 + Repay Walt Hall $300 + Repay Julie Lambert $200 + Repay Connie & Lamont Robbins Loan
  $138.66 = $826.43). The $5,619.41 pre-general expenditures are itemized nowhere in this
  year-end final report (no Column-A Schedule B attached; the itemizing pre-general filing is not
  in our index). Nothing to recover — the cache already holds the only 4 rows that exist; covers
  stand ($6,445.84/$6,445.84). The `expend!=stated` (Δ −$5,619.41) flag faithfully reflects the
  filing's own incompleteness; do NOT "fix" it.
- **Albert Allen Larsen 2025 — APPROVED unchanged (additive, override stands).** Sanity-checked
  Oct-07 (`9004`, $12,685.40) vs Oct-28 (`9045`, $10,104.62): a cumulative restatement is
  impossible because the later total is SMALLER; recurring vendors carry different per-period
  amounts (Robocent $9,189.30 vs $6,910; Proximity $326.64 vs $486.18; Canvassing $1,325 vs
  $750) and Oct-28 adds fresh vendors (Web Partner, Slick Texts). Disjoint per-period
  self-loans, raised==spent each period. Cycle $27,010.02 (= 3,470 + 12,685.40 + 10,104.62 +
  750) confirmed. The pre-existing Oct-07 −$10.10 itemization flag is untouched (verbatim).
- **Mark Hales 2023 — CLOSED AS-IS (owner decision, 2026-07-18).** The $2,000 Salt Lake Board
  of Realtors check appears Oct-24 ("uncashed", $0 cover) then Nov-14 ($2,000, cashed) — one
  donation across two reports. Cycle stays as published: **$2,000 raised / $910.61 spent**, the
  conservative computed value, NOT overridden. Owner-decision to close; do not re-open absent
  new source evidence.

## Caveats / do-nots

- **No dollar amounts in `index.csv`** — the raw PDFs + the `vision/` caches (scanned filings) hold
  them; the structured `contributions.csv`/`expenditures.csv`/`cycle_totals.csv` layer is a separate
  planned step (see repo `TODO.md`).
- **Do not sum `filing_type` dollars** across a candidate's filings (double-count trap).
- Additive only — never edit `../election_results/`; a filing that surfaces an election-record
  gap is FLAGGED (see `AVAILABILITY.md`), not reconciled from here.
