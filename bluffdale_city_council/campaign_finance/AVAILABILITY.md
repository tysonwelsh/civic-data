# campaign_finance/ — availability & gap log

As-of 2026-07-12. Additive; no existing dataset modified.

## What exists
- **City website (CivicPlus DocumentCenter)** — Bluffdale self-hosts all municipal
  candidate campaign-finance filings here (`source=city_website`). This is the authoritative
  source; the state site (`disclosures.utah.gov`) and Salt Lake County do not carry Bluffdale
  municipal filings.

## Coverage
- **106 filings across 5 cycles**: 2017 (19), 2019 (30), 2021 (6), 2023 (27), 2025 (24).
- **50 born-digital `text` + 56 `scanned`** (OCR'd).
- **100% election join** — every filing maps to a candidate in
  `../election_results/bluffdale_results_by_candidate.csv` (99 `high` / 7 `medium`).

## How verified / method
- Filings fetched GET-only via `scripts/polite_fetch.py` (browser UA, throttled); sha256 +
  status logged to `raw/_fetch_log.jsonl`. Filenames `YYYYMM`-prefixed to avoid
  cross-period basename collisions.
- The 2021 cycle's six "…-Report" filings were renamed to the clean index names on
  2026-07-13 (a mid-build rename that was interrupted by a session limit; reconciled — index
  paths and disk files now match exactly).

## Vision transcription of scanned filings (`vision/`, 2026-07-17, wave-2)
The **56 scanned filings** were transcribed to structured JSON via the **Read-tool vision method**
(`/cf-vision-transcribe`, $0 API — runs on the Claude Code allotment, NOT the Anthropic API), EXCEPT
the **2 pre-2020-floor 2017 filings** (out of task scope) → **54 caches** written to `vision/`.
- **Cache-key convention** matches Bluffdale's tranche-1 sibling **midvale**: filename =
  `sha1(index-path)[:8].json`; body = `{"contributions":[{date,name,amount,in_kind}],
  "expenditures":[{date,recipient,purpose,amount,in_kind}], "totals_printed":{...}}`, one
  multi-report `reports[]` file (the 2025 Pavlakis Pre-General PDF bundled two copies of the same
  report). Priority order transcribed: 2023 (24) → 2021 (6) → 2025 (24).
- **Totals: 54 caches, 0 bad JSON, 427 contribution rows + 335 expenditure rows, 4 honest-empty
  (no-activity) filings.** All amounts verbatim as printed; illegible glyphs/blank donor names set
  to `null`, NEVER inferred (e.g. Blain Dietrich 2021 blank contributor → null; Mark Hales 2023 "?"
  amount → null). Handwritten-digit ambiguities resolved only where cover-total arithmetic pins them
  and documented as such. Several filer arithmetic gaps (schedule-vs-cover mismatches) were preserved
  verbatim, not reconciled — see the per-cache values.
- **These caches are PRE-STAGED, not yet consumed.** Bluffdale has **no `build_finance.py`** (this is
  still an acquisition-only layer); the structured dollar layer is owner-gated / separately queued.
  When that build lands it will read these `vision/<hash>.json` via its `rows_override_fn` (midvale
  convention). No structured CSV was built in this pass, and no do-NOT-re-vision flags existed (fresh).

## 2026-07-17 — STRUCTURED DOLLAR LAYER (build_finance.py, family vision_cache)
The pre-staged `vision/` caches are now CONSUMED into the four derived CSVs
(`contributions.csv` 410 / `expenditures.csv` 331 / `filing_totals.csv` 106 / `cycle_totals.csv`
46). `validate_finance.py` PASS (0/0); `validate_city.py` 0 FAIL. See `CLAUDE.md` (dated
section) for the full decision log. Highlights relevant to availability/coverage:
- **Full inventory preserved:** all 106 index filings are in `filing_totals.csv` — 57
  vision-transcribed + **49 honest inventory-only rows** (the below-2020-floor 2017 ×19 + 2019
  ×30 filings; unknown totals, dated reason, low confidence). No filing is silently dropped.
- **3 in-floor 2023 born-digital `text` filings** (Swanson 5969, Flynn 5971, Wilding 5996) were
  transcribed from their clean pdftotext layer into new caches → **57 caches total** (up from
  54). Swanson/Flynn Oct-05 are $0 no-activity post-primary reports; **Wilding Oct-24 carries
  real money** ($5,100/$3,046.38) and was NOT left out.
- **Pavlakis 2025 `reports[]` bundle** collapsed to its AMENDED sub-report at build (no
  double-count; reconciles). The other 53 caches consume unchanged.
- **9 verbatim reconcile flags** (filer arithmetic / transcription gaps) preserved, never
  corrected; the named-filer flags Ostler, Mackey Smith, Allen Larsen, Blain Dietrich behave as
  expected (Larsen −$10.10 expend; Dietrich +$6 expend, spot-checked vs raw PDF).
- **Follow-ups (not fixed):** re-vision **Natalie Hall 2025 Oct-07/Oct-28** (parenthesized/
  negative expenditure sign inconsistency in the scanned caches); **Mark Hales 2023** uncashed→
  cashed $2,000 check spanning two reports; **Connie Robbins 2 2021** contribution itemization
  gap. Cycle totals for these use stated covers and are flagged.

## Gaps / honest limits
- **No dollar extraction yet** — acquisition layer only; the structured contribution/
  expenditure/cycle-total layer is a separate planned step (repo `TODO.md`). The `vision/` caches
  above are the pre-computed transcription inputs for that step.
- **2021 has only 6 filings** vs 19–30 in other cycles — the 2021 RCV-pilot cycle; verify
  against the candidate slate whether any filer's report is missing from the city site
  (a possible city-publishing gap) before quoting 2021 coverage as complete.
- Any filing that implies an election contest the `election_results` docs don't list is a
  FLAGGED discrepancy for an elections review — this dataset does not edit `election_results/`.
