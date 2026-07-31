# campaign_finance/ — Riverton City (ACQUISITION layer + STRUCTURED money layer)

> **2026-07-18 — STRUCTURED LAYER BUILT.** The `filing_totals.csv` / `contributions.csv` /
> `expenditures.csv` / `cycle_totals.csv` derived money layer now exists (`build_finance.py`,
> family `vision_cache`, shared `scripts/campaign_finance/vision_lib.py`). See the dated section
> at the bottom of this file for the build decisions. The text below is the original
> acquisition-layer doc.



Municipal candidate campaign-finance disclosures for Riverton City, completing the
**elections → members → votes** chain. **Acquisition-only:** raw PDFs retained with full
provenance; **no OCR/vision extraction and no dollar totals** — those are deferred
(`extraction_method='none (raw acquisition; OCR/vision deferred)'` on every row).

- **Built:** 2026-07-13 · **Cycles:** 2021 (D3/D4/Mayor), 2023 (D1/D2/D5), 2025 (D3/D4/Mayor).
- **60 filings, 171.9 MB, all under `raw/`** (verbatim; each with sha256 + status in
  `raw/_fetch_log.jsonl`). Fetched GET-only via `scripts/polite_fetch.py`.
- **Format split:** 30 born-digital `text` / 30 `scanned` (image-only).

## Sources (see AVAILABILITY.md for the full checklist)

1. **City recorder (Revize)** — `www.rivertonutah.gov/departments/recorder/elections/<slug>.pdf`,
   linked from `government/elections/archived-disclosures.php` (2023 year-end summaries +
   conflict forms) and `government/elections/candidates.php` (full 2025 packets). Canonical URLs
   are stable; the `?t=` query on the page links is only a cache-buster and was dropped.
   `source=city_recorder_page`.
2. **State — `disclosures.utah.gov/municipal` → `salt lake_2023_Riverton`** — the **2023-cycle
   interim reports** (10.24.23 / 11.14.23 / 12.21.23), which the city page does not publish. Served
   from `municipal.utah.gov/...` (Windows backslash paths → fetch with forward-slash + `%20`).
   `source=state_lg_municipal_disclosures`.
3. **Wayback (CDX)** was a **discovery index only** — it located filenames no longer linked on the
   live pages (2021 finance reports; 2023 declarations; the declared-but-unballoted filers). All
   Wayback captures were 302 Revize redirect stubs, so the PDFs were fetched from the **live**
   server, not the archive.

## index.csv schema

SCHEMA_SPEC §9 `campaign_finance` contract header first (exact order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method,path`
then city-specific extras: `district,source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256`.

- **`filing_type`** — `interim` (pre-election reports incl. all 2023 state interims + 2025
  primary/28-day/general), `summary` (cumulative finals: 2021 single reports, 2023 year-end
  "financial-2024", 2025 post-election), `statement` (McCay Oct-2025 statement; possible 28-day
  duplicate), `conflict_of_interest` (candidate COI in a campaign packet),
  `declaration_of_candidacy` (candidacy declaration — captured for roster/discrepancy provenance,
  not a money report).
- **`date` + `date_precision`** — best filing-date estimate, precision flagged honestly:
  `filename_filing_date` (2023 state interims, exact), `form_sworn_date` (declarations read via
  vision for office/district only), `upload_timestamp` (2025 reports — Revize `?t=` publish date),
  `statutory_year_end_deadline` (2023 city summaries), `cycle_anchor_general_election_day` (2021),
  `candidate_filing_period_anchor` (2023 declarations). NO internal report dates were read
  (acquisition-only) except the three declarations vision-classified for office/district.
- **`matched_election_candidate` / `join_confidence`** — the UPPER-CASE `election_results/riverton_races.csv`
  winner/runner-up name for that person (`high`), or blank + `none` when the person is not in the
  races file (Almond, Scott, Renlund — see discrepancy flags).

## Linkage / analysis rules

- **Join to elections/members on PERSON, not district number** — Riverton **renumbered D3↔D4 at the
  2022 redistricting** (Ord. 22-07), and both McCay (Council D3, 2021) and Buroker (Council D4,
  2017/2021) ran for **Mayor** in 2025. Names are normalized: election_results are UPPER-CASE;
  Rustin Lance appears as "RUSTY LANCE", Alexander Johnson as "ALEXANDER A. JOHNSON".
- **DOUBLE-COUNT TRAP** — candidates file several reports per cycle (2023: 3 interims + 1 year-end;
  2025: 4-report series). Do NOT sum a candidate's filings for a cycle total — interims are
  cumulative-to-date and the summary is the cumulative final. Use
  `scripts/campaign_finance/cycle_totals.py` at extraction time.
- **Discrepancy flags** (documented in AVAILABILITY.md, NOT applied to `election_results/`):
  David Almond (declared 2023 Council D5, withdrew), John Scott (2025 Mayor, un-named 3rd primary
  candidate), Matt Renlund (declared 2025 Council D4, withdrew) — each filed a declaration but no
  finance report and is absent from the county SOVC race file.

## Regenerating / extending

- Re-fetch: `polite_fetch.py --batch <list> --out raw` (canonical city URLs; state URLs
  forward-slash + `%20`-encoded). Retain `raw/_fetch_log.jsonl`.
- Validate: `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
  riverton_city_council/campaign_finance` — must PASS.
- This layer feeds `cities.db` `document`/`cf_*` on the next `build_cities_db.py` (run by the
  orchestrator, not here). Extraction to `filing_totals.csv`/`cycle_totals.csv` is future work.

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 1, 2025 cycle) — vision/ caches written

Transcribed **all 8** scanned 2025-cycle C&E filings via `/cf-vision-transcribe` (Read-tool
vision, **$0 Anthropic API**). `vision/*.json` = 83 contributions + 104 expenditures.

- **Cache contract:** pure `sha1(index_path)[:8].json` + WJ vision schema + `_meta` block.
  **STRUCTURING PENDING** (no `build_finance.py` yet — additive caches only, owner-gated later work).
- **Riverton form quirks:** itemizes **only contributions exceeding $50** — there is **no "$50 or
  less" aggregate line** (a separate "$500 or less" small-campaign box was blank on all), so
  `contributions_50_or_less` is null throughout. **No date/purpose columns** on Schedule A/B →
  dates/purposes null by design. **Separate Schedule C in-kind** recorded as `in_kind:true`
  contribution rows and is **NOT part of the cover contribution total** (tracked separately).
- **Column structure (build caution):** summary pages carry Column A (prior 28-day report) + Column
  B (this general-election period); **this-period Column B** values were used. The larger cumulative
  schedule-footer totals (e.g. Smith prints $17,663.81 contrib / $12,317.35 exp) are campaign-to-date,
  NOT the period figures — do not read them as the report total.
- **Verbatim flags (unreconciled, filer-side):** Lance `c498ac4b` summary columns filled
  inconsistently ($575 exp under the wrong column; `ending_balance` blank→null); Johnson `016a3822`
  balance off by ~$78; Buroker (`8ddf6029`/`cdaabfda`) beginning-balance $5,000 off-by; McCay
  expenditure sign flip page1/page2; typo "3,000,00" preserved.
- Backup: `_backups/2026-07-17-cf-vision-t1/riverton/` (greenfield — nothing pre-existed).

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 2, 2023 then 2021 cycles) — vision/ caches written

Transcribed the **2023 (17 filings) then 2021 (1 filing)** scanned money reports via `/cf-vision-transcribe`
(Read-tool vision, **$0 Anthropic API**), fanned out across 9 `general-purpose` chunk agents (≤~15
page-images each, disjoint filings). **17 new `vision/*.json` caches** written (same pure
`sha1(index_path)[:8].json` key + WJ schema + `_meta` block as tranche 1); total cache count now **25**
(8 from tranche 1 + 17). The **4 `declaration_of_candidacy` scans** (Pierucci/Almond/Gatti/McDougal) were
**correctly SKIPPED** — they carry no contribution/expenditure data (already vision-classified for
office/district only). STRUCTURING still PENDING (no `build_finance.py`; additive caches only, owner-gated).

- **The 2023 "financial-2024" summaries are 3-report BUNDLES.** Each candidate's year-end `summary` PDF
  (15–16pp) staples a 28-Day + General-Election + Post-General report into one file. Each cache holds all
  itemized rows across the bundle; cover totals come from the final summary's **Column E "Campaign Total"**
  where the filer printed it (Gatti $4,253.02/$4,253.02; McDougal $2,000/$2,669.04; Winters
  $4,350.00/$4,358.00) — and are **null** where the filer left Column E BLANK (**Haymond** — never summed
  by us, per anti-fabrication). The corresponding 2023 `interim` caches (state-published, but the FORM is
  the Riverton CITY C&E form, not the Lt.-Gov form) carry the same three periods separately — so
  **interim + summary OVERLAP by design** (the documented double-count trap; dedupe at structuring time).
- **2021 McCay** (`8a4744cb`) bundles the Dec-2 final (no activity) + Oct-26 pre-general (the itemized
  report); cover totals from the printed Campaign Total ($100 contrib / $147.77 exp).
- **Riverton form quirks re-confirmed:** no date column, no expenditure purpose column → dates/purposes
  null (EXCEPT Gatti's Schedule B, which uniquely prints per-line dates+purposes — captured); itemizes
  only contributions >$50 so `contributions_50_or_less` null throughout; Schedule C in-kind as
  `in_kind:true`, excluded from the cover contribution total.
- **Verbatim/unreconciled filer flags** (transcribed as printed, NOT corrected): Haymond struck-through
  Lowes 125.6→80.05; Gatti interim summary vs Schedule-B $3 expenditure mismatch (1937.90 vs 1934.90);
  Winters Column-E $4,358 vs schedule-subtotal $4,350.11 and 1,937.40/1,937.26 carryover ambiguity;
  McDougal beginning_balance 928.30 re-entered every period; several low-confidence handwritten donor
  names (e.g. Winters "Mezzohambardo Janef", "Rachel Hooley/Healey").
- **⚠ DATA DEFECT found — see AVAILABILITY.md flag #6:** the state file
  `2023_pierucci_state_10-24-23_redacted.pdf` actually contains **Haymond's** 28-day report (line-identical
  to `2023_haymond_state_10-24-23`). No Pierucci cache was written for it (would fabricate Pierucci
  donors); Pierucci's real 10-24-23 28-Day interim is an honest acquisition gap (his 11-14/12-21 interims
  + year-end summary ARE held).
- Backup: greenfield (17 new caches — nothing pre-existed; the 8 tranche-1 caches were untouched).

## 2026-07-18 — STRUCTURED LAYER BUILT (`build_finance.py`, family `vision_cache`)

The derived money layer now exists — `contributions.csv` (303) / `expenditures.csv` (308) /
`filing_totals.csv` (**41 rows** = 40 vision/text-transcribed money reports + 1 honest
inventory-only gap) / `cycle_totals.csv` (**14 candidate-cycles**) — all regenerable
(`python3 build_finance.py`; then `python3 scripts/campaign_finance/cycle_totals.py riverton`),
never hand-edited. `validate_finance.py` PASS (0 fails; 19 warns = the excluded non-money rows).
`scripts/validate_city.py riverton_city_council/` = 23 PASS / 0 FAIL. Read `cycle_totals.csv`
for any candidate/race total — **never sum `filing_totals`**.

**15 new caches written this session (cache count now 40).** Riverton's landmine: the
born-digital `format=text` money reports are NOT clean text — they are degraded fillable-form
renders (space-separated digits, multi-column BALANCE SUMMARY) or, for 2021 and several 2025
reports, **handwritten scans mislabeled `format=text`** (the pdftotext layer is junk). They
carry REAL money, so they were transcribed (read-tool vision / text-layer reading), NOT dropped
as inventory and NOT parsed with a fragile regex grammar. New caches: 2021 Buroker/Staggs
(handwritten); Pierucci 11-14 / 12-21 / financial-2024 (born-digital text); 2025 Johnson-28day/
post, Park-28day, Lance-28day, Smith-28day/post, McCay-28day/post, Buroker-28day/post.

Key build decisions (all evidence-based):
- **`reconcile_cash_only=True`** — the Riverton C&E cover TOTAL excludes Schedule C in-kind
  (verified: Buroker primary 19 cash rows = 19,950 cover, 3,550 in-kind excluded). In-kind rows
  (13) carry `in_kind=True` and are NOT summed into the contribution reconciliation.
- **PER-PERIOD form (Summary Page columns A..E; Column E = Campaign Total).** Every report
  records its OWN incremental column as its stated total; a candidate's cycle = the sum of
  periods = Column E. `detect_regimes` marks every candidate "incremental".
- **2025 Post-Election reports are themselves a period** (Column D), not a cumulative final —
  their `filing_type` is `summary` but the generic summary-vs-interims rule undercounts, so the
  cycle total is carried in **`cycle_overrides.csv`** = the filer's own printed Column E:
  **McCay 2025 30,690.55 / 26,419.77; Smith 2025 19,183.81 / 18,933.34; Buroker 2025 32,350.00 /
  26,932.59** (each verified = the sum of that candidate's 3-4 period reports). Johnson/Lance/Park
  2025 needed NO override (their post-election period is $0 or they filed none — `cycle_totals`
  computes them correctly as `sum-interim`).
- **2023 interim+summary OVERLAP (the double-count trap) is deduped, NOT summed.** Each 2023
  candidate filed 3 state interims (this-period) + 1 city `financial-2024` year-end bundle whose
  cover = Column E = the sum of the same 3 periods. `cycle_totals` takes `max(summary,
  sum-interims)` so **each period counts once** (Gatti 4,253.02 etc.). No override needed.
- **Pierucci 2023 acquisition gap (AVAILABILITY #6) is represented as one inventory-only
  `filing_totals` row** (blank totals, dated reason) for `raw/2023_pierucci_state_10-24-23_
  redacted.pdf` — NO cache (would attribute Haymond's donors to Pierucci). His cycle total
  (**5,540 / 2,817.78**) is carried by his year-end summary's printed Column E; his summary's
  expenditure side reconciles FALSE (itemized 150 vs cover 2,817.78) because the 28-Day schedule
  detail is in the gap — an honest consequence, flagged `needs_review`, never adjusted.
- **Exclusions (19 rows, named in `in_scope_fn`):** 12 `declaration_of_candidacy` + 6
  `conflict_of_interest` (not money reports) + the McCay `statement` (`ed1bf236`, a byte-identical
  duplicate of her 28-Day report — same sha256 — counted once via the 28-Day filing).

Reconciliation: 26/41 filings reconcile both sides; 15 carry verbatim mismatches (never adjusted):
cent discrepancies (Haymond/Winters/Smith-general), the documented Gatti summary-vs-schedule gap,
Staggs 2021 totals-only (he reported lump totals, itemized nothing), and two pre-existing tranche-1
cache quirks worth knowing:
- **McCay 2025 primary (`f233622b`):** the filer wrote the FIRST Schedule-B page's amounts with
  **minus signs** (−53.31 …) but totaled them as positive; the cache preserved the negatives
  verbatim, so itemized expend nets to 5,026.66 vs the cover 10,386.76 (= 2,680.05 + 7,706.71).
  An honest filer sign-quirk, flagged; her cycle spend is correct via the Column-E override.
- **Buroker 2025 general (`cdaabfda`):** the filer wrote the loan as **"$3,000,00"** (comma for
  the decimal); `vmoney` strips commas → **300,000** — a 100× phantom in that filing's
  `itemized_contrib_sum` and `self_funded_amount`. Kept VERBATIM + flagged `needs_review` (the
  cardinal rule: mismatches are flagged, never corrected); documented in `finance_overrides.csv`.
  Buroker's cycle total is UNAFFECTED (`cycle_totals` uses the printed cover 4,000 / Column E, not
  the itemized sum). If policy later allows, correct via `finance_overrides` once that mechanism is
  wired, or fix the cache to 3000.00 (the value the filer's own $4,000 subtotal proves).

Backups: `_backups/2026-07-17-cf-structuring/riverton/` (pre-edit CLAUDE.md + AVAILABILITY.md).

## 2026-07-18 — CF EVIDENCE-PASS ADJUDICATION (owner-authorized) — 2 tranche-1 quirks resolved

Re-rendered both flagged filings from the raw PDFs (`/cf-vision-transcribe` Read-tool re-read).
Backups of every file touched: `_backups/2026-07-18-cf-adjudication/riverton/`.

- **Item 1 — McCay 2025 primary (`f233622b`), Schedule-B negatives: FILER SIGN-QUIRK, cache
  faithful, NO change.** The re-render is unambiguous: on the FIRST Schedule-B page (period
  1/1/2025 THRU 5/15/2025) the **filer hand-typed every amount with a leading minus sign**
  (`-53.31, -192.34, … -31.63`) yet totaled them as positive absolute values ("SUBTOTAL FOR THIS
  PAGE $2,680.05" = the sum of the magnitudes). The SECOND page is positive (subtotal $7,706.71;
  cumulative TOTAL 1/1 THRU 8/5 = $10,386.76 = 2,680.05 + 7,706.71). The cache preserved exactly
  what the filer printed — this is a **filer** convention (outflows written negative), NOT a
  transcription misread, so the negatives stay VERBATIM. Consequence: this filing's
  `itemized_expend_sum` nets to **5,026.66** vs the cover **10,386.76** (expend-side reconciles
  FALSE, `needs_review`, flagged, never adjusted). Cycle spend is correct via the Column-E override
  (26,419.77). **NOTE CLOSED** — no cache edit, itemization fidelity is faithful.
- **Item 2 — Buroker 2025 general (`cdaabfda`), "$3,000,00" loan: TRANSCRIPTION-STRIPPING ARTIFACT,
  now CORRECTED at build.** Re-render confirms the **filer wrote "$3,000,00"** (a comma where the
  decimal belongs) for "Loan from Tish Buroker"; the page's own "SUBTOTAL FOR THIS PAGE" and "TOTAL
  CONTRIBUTIONS RECEIVED" both print **$4,000.00 = $1,000 Glen Roberts + $3,000 loan**, so the
  printed intent is unambiguously **$3,000.00**. The cache **keeps the filer's verbatim "3,000,00"**
  (filer wrote the typo — cache untouched); `vision_lib.vmoney` strips the comma → 300000.00, a 100×
  phantom. Added a city-local **`_adapt_cache`** in `build_finance.py` (the bluffdale precedent;
  shared `scripts/` untouched) that maps this ONE `_meta.index_path`-keyed value 300000.00→3000.00
  at build time. **Before → after:** filing_totals `itemized_contrib_sum` 301000.00→**4000.00**,
  `self_funded_amount` 300000.00→**3000.00**, contrib row v2 300000.00→**3000.00** (`needs_review`
  1→0), the filing now reconciles both sides (confidence low→medium). `finance_overrides.csv` reason
  updated to "APPLIED via _adapt_cache". **Cycle total UNCHANGED** (32,350.00 / 26,932.59 —
  override uses printed Column E, not the itemized sum).

Rebuilt `build_finance.py` + `cycle_totals.py riverton` (never `--all`). `validate_finance.py`
**PASS (0 fails, 19 warns** — the non-money exclusions); `scripts/validate_city.py riverton_city_council/`
**23 PASS / 0 FAIL**. Residual ambiguity: none for either item — both are settled by the filers'
own printed subtotals on the re-rendered pages.
