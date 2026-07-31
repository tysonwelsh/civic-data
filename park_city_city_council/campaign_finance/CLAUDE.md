# campaign_finance/ — Park City municipal candidate financial disclosures

Additive dataset built by the `expand-city-sources` skill (**Source 6**), as-of
**2026-07-05**. Does **not** modify any existing dataset. Completes the **elections →
members → votes** chain: who funded the candidates whose roll-call votes live in
`../meeting_minutes/` and `../planning_commission/`, and whose wins are in
`../election_results/`.

## What this is
**126 municipal campaign financial disclosures** filed by Park City **Mayor + City
Council** candidates for the **2017, 2019, 2021, 2023, 2025** cycles (primary, general,
and final/year-end reports, incl. candidate-filed amendments), plus **10
conflict-of-interest officeholder statements** (2025–2026) — **136 PDFs total**. Each is
the Utah "Municipal Campaign Financial Statement" (combined contributions + expenditures
on one form). Raw PDFs retained verbatim in `raw/<year>/`; per-subdir `_fetch_log.jsonl`
carries provenance (url, http status, bytes, sha256, retrieved_utc).

**Scope note:** Park City council is **5 at-large seats + Mayor, NO districts** — so there
is no district column; `office` is `Mayor` or `Council`. This is a *filing-level* index
(documents + provenance), **not** a structured contribution/expenditure table — that is a
separate planned layer.

## Where the data comes from (see `AVAILABILITY.md` for the full source log)
Park City **runs its own municipal elections** and **self-hosts every filing** on its
CivicPlus site. The state site (`disclosures.utah.gov`) does not carry them; EasyVote is
not used; no Wayback recovery was needed. Single source page:
`https://www.parkcity.gov/government/elections/campaign_disclosures.php`
→ document-tree PDFs under `…/Documents/Government/Elections/Campaign Disclosures/<cycle>/`.
Spaces must be `%20`-encoded (CMS quirk). These are plain paths, **not**
`showpublisheddocument/<id>` deep links.

## Layout
```
raw/
  2017/ 2019/ 2021/ 2023/ 2025/   campaign filing PDFs, each dir with _fetch_log.jsonl
  2025/ 2026/                     also hold the *_coi_* conflict-of-interest PDFs
     filenames: <year>_<period>_<orig-stem>  (period ∈ primary/general/final/coi)
  index_pages/                    the disclosures INDEX + results HTML (discovery source)
text/<year>/<same-stem>.txt       ONE text sidecar per filing (Source-6 requirement)
index.csv                         one row per filing (schema below)
batch/manifest.json               href→url→file manifest + the one 404/recovery note (build input)
build_index.py                    regenerates index.csv from manifest + files + text sidecars
extract_text.py                   (re)builds the text/ sidecars: pdftotext -layout, OCR fallback
AVAILABILITY.md                   every host tried, per-cycle coverage, honest gaps
```

## `index.csv` schema
Required minimum columns (`date,title,source_url,retrieved_date,format,extraction_method`)
plus source-specific columns:

| column | meaning |
|---|---|
| `date` | filing-period proxy `YYYY-01-01` (the CivicPlus paths carry no statutory due date; use `reporting_period` + `election_year` for the real period). **Approximate.** |
| `candidate` | filer name recovered from the filename (qualifier words stripped). |
| `office` | `Mayor` / `Council`, from filename tokens and/or the election-results join. |
| `election_year` | 2017 / 2019 / 2021 / 2023 / 2025 (for COI rows = the statement year). |
| `filing_type` | `interim` (before-primary / before-general report), `summary` (final/year-end report), or `conflict_of_interest` (the 10 officeholder COI statements — a documented extension of the interim/summary/contribution/expenditure vocab; these are not campaign-finance reports). |
| `reporting_period` | `Primary` / `General` / `Final` / `Conflict of Interest`. |
| `title` | human label incl. cycle + period + `[amended]`. |
| `source_url` | the **live** parkcity.gov PDF URL (`%20`-encoded). |
| `retrieved_date` | (§9 contract column; blank where not recorded) |
| `format` | `text` (born-digital, real text layer) / `scanned` (image-only, OCR'd). Set from the measured sidecar length + extractor. |
| `extraction_method` | `pdftotext -layout` or `tesseract OCR (pdftoppm 300dpi, psm6)`. |
| `path` | repo-relative path to the retained PDF. |
| `matched_election_candidate` | canonical `../election_results/` name this filer joins to (blank if none). |
| `join_confidence` | `exact` (first+last + same year in election_results), `firstlast` (person in elections, different/primary-only year), `coi-officeholder` (COI filer matched to an elections name), `none` (no election row — chiefly 2017, which predates the election dataset). |
| `amended` | `yes` for candidate-filed amendments/revisions. |

## Join to election_results
Filers are joined to `../election_results/park_city_results_by_candidate.csv` on normalized
first+last name + year. See `AVAILABILITY.md` for the join rate and the two flagged
discrepancies (2017 filings predate the election dataset; a few primary-eliminated filers
match at the primary level only). **The election dataset was not modified** — gaps are
flagged here, per the repo's cardinal rules.

## Regenerating
```
python3 extract_text.py     # rebuilds text/ sidecars from raw PDFs (slow: OCRs scans)
python3 build_index.py      # rebuilds index.csv from batch/manifest.json + files + sidecars
python3 /Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
Fetching is **not** re-run by these; raw originals are retained. To re-acquire, replay
the `url` fields of `batch/manifest.json` through the skill's polite fetcher
`/Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts/polite_fetch.py`
(GET-only, browser UA, ≥1.2 s delay).

**OCR env caveat (learned the hard way):** on this machine tesseract 5.5 / leptonica 1.85
fails to read pdftoppm's PNG/TIFF output, and fails on **absolute** image paths when
anaconda is on `PATH` ("Leptonica … failed to open locally"). The working recipe, encoded
in `extract_text.py`: `pdftoppm -jpeg`, then run tesseract **from the image directory with a
relative filename**. Foreground only — the sandboxed background shell can't read the temp
images.

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-06

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`.
Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent).
Validate: `python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS** (10 warns =
the 10 excluded COI statements, which correctly have no filing_totals row).

- **contributions.csv** 3,656 rows · **expenditures.csv** 3,063 rows · **filing_totals.csv** 126 rows.
- **cycle_totals.csv** 47 candidate-cycles (0 review_flags) — the canonical per-candidate×cycle
  rollup (`python3 ../../scripts/campaign_finance/cycle_totals.py park_city`). **Always read this
  for a candidate/race total; never sum filing_totals** (Park City reports are cumulative — see Dedup).
- **SCOPE — the 126 campaign C&E filings only.** Park City's **10 conflict-of-interest officeholder
  statements** (`filing_type=conflict_of_interest`, 2025–2026) are a SEPARATE statutory genre and are
  **EXCLUDED** here (`in_scope_fn` in `build_finance.py`), exactly as Orem excludes its COI statements.

### Form family — `parkcity_form` (NEW; Park City's form genuinely differs)
Park City self-hosts a **Park-City-specific "Campaign Financial Report"** (UCA 10-3-208 + PCMC 3-3)
that is **structurally distinct from the Orem-style `utah_standard_form`**, so it is a NEW family
`families/parkcity_form.py` (registered in `families/registry.py`; NOT a reuse). Why it differs:
- **Two itemized sections — Form "A" (contributions) + Form "B" (expenditures)** — NOT the Orem
  trio of Cash-Contributions / In-Kind / Cash-Expenditures sections. **In-kind is INLINE** ("(in
  kind)" in the donor name or "In Kind" in the amount column), never its own section/total, and its
  value **IS included in the Form-A total** (so contributions reconcile ALL rows, `reconcile_cash_only=False`).
- **Columns DRIFT by cycle**: 2017 = `Date | First | Last | Addr | City | State | Zip | Type | Amount |
  running-total` (a SECOND money column) with QuickBooks P&L expenditures; 2019/2023/2025 =
  `Date | Name | Address | Amount` (2023 prints the amount BARE, no `$`); 2021 = `Date | First | Last |
  Mailing address | Gross`.
- **The printed TOTAL anchor also drifts**: cover block "1. Total amount from donors giving more than
  $50.00 … (Form A total)" + inline "+ $x VIK" (2017/2019) → "1b. Itemized total of contributions
  totaling $500 or more" (2023/2025); ~half the sidecars drop the cover page, so the family also
  anchors on the in-table "Total Contributions"/"Total Expenditures" line. Values are read past the
  leading item-number and the `$50/$500` label thresholds.
The family handles: the running-total 2nd money column (take amount, not cumulative), bare amounts,
amounts glued to a payment annotation ("59.41 in kind"), wrapped multi-line rows (address overflow),
zip-vs-amount disambiguation, and QuickBooks P&L expenditures (left UNPARSED → honest flag, like
Orem's McKell). NO city name/office logic lives in the family — candidate/office/year come from `index.csv`.

### Modes — born-digital + OCR + gated vision
- **82 born-digital** (`format=text`) → text mode: **27 both-sides reconcile** (`high`); side-level
  **contrib 40, expend 43** of 82 reconcile. The residual is HONEST, not extraction failure: Park
  City forms frequently **don't foot** (candidate arithmetic, e.g. Jack Rubin 2025: cover says
  $46,075, itemized cash sums $43,075 — a $3,000 source discrepancy kept verbatim), plus **19
  OCR-garbled `text`-classified cover pages** with no readable printed total (honest unknown), and
  the **2017 QuickBooks-P&L cohort**.
- **44 scanned** (`format=scanned`) → OCR mode, then **gated vision** for the 43 that failed OCR
  reconciliation: **`parkcity_vision_extract.py`** (model `claude-sonnet-5`, strict "transcribe
  exactly / never infer" prompt; cached in `vision/<doc8>.json`; fed back through the SAME
  reconciliation via the driver `rows_override_fn`; `extract_method=parkcity_form/vision`). **All 43
  flagged scanned filings were vision-transcribed** (two runs; **~$2.6 total**, ~249k input + 126k
  output tokens, synchronous list price). **Vision reconciled 19 filings both-sides and improved ≥1
  side on 40**; `<doc8>` = sha1(dataset-relative path)[:8] (index.csv has no sha256).
- **Final: 47 of 126 both-sides reconcile** (born-digital 27, scanned/vision 20); **side-level
  contrib 66, expend 76** of 126. **79 flagged/partial** (48 of them reconcile ONE side): ≈41
  born-digital source-non-foot/layout, 21 scanned/vision residual, 16 no-anchor garbled covers, 1
  QuickBooks P&L. All carry `needs_review=1` + `low` — nothing fabricated.

### Dedup — CUMULATIVE (`driver.run(dedup_mode="cumulative")`)
Empirically determined: each Park City report **restates the whole cycle-to-date** (a General report
contains the cycle's April–October donations; the Final restates everything), so a candidate's cycle
total is the **LATEST (non-superseded) report per candidate+cycle, NOT a sum** (contrast Orem =
incremental). `cycle_totals.py` picks the summary/Final (or max interim) per candidate — 47 cycles,
0 review-flags. ~9 PDFs stack two full reports; ~90 others repeat the Form-A/B page-header on long
tables (handled). An amendment (`amended=yes`/`title` revis) supersedes its snapshot, kept + flagged.

### donor_type distribution (3,656 contribution rows)
individual 3,252 · unknown 160 (incl. **68 blank-donor** → `unknown`+`needs_review`; rest are
single-token/parenthetical joint names the conservative classifier won't force) · candidate-self 99 ·
business 61 · **family-of-candidate 50** (same-surname relatives) · loan 18 · anonymous 10 · pac 4 ·
party 2. **404 in-kind** contribution rows; **50 filings carry self-funding**. `donor_aliases.csv` +
`finance_overrides.csv` header-only (no curated overrides needed yet).

### Hand-verification (5 filings vs the raw source, 2026-07-06)
| filing | mode | check | result |
|---|---|---|---|
| Deanna Rhodes — General 2019 | born-digital | 8 contrib + 9 expend vs printed | ✓ contrib Σ **$1,225 = stated**; expend **$1,616.99 = stated** |
| David A. Dobkin — Primary 2021 | born-digital | 18 contrib rows vs raw sidecar, line-by-line | ✓ names/dates/amounts match exactly (David Dobkin $5,001 self, Aaron Ingram $100…); Σ **$30,278.14 = stated**; expend **$24,524.39** |
| Bob Sertner — Primary 2023 | born-digital | 63 contrib + 37 expend | ✓ Σ contrib **$31,540 = stated**; expend **$25,660.76 = stated** |
| Becca Gerber — Final 2019 | vision | 30 contrib vs rendered raw PDF page | ✓ every row matches (Tommy Tanzer $100, Sue & Dick Roth $2,000, Park City Board of Realtors $500…); Σ **$5,070 = printed total** |
| Ed Parigian — Final 2019 | vision | cover + Form A/B vs rendered raw PDF | ✓ cover confirms Form-A **$2,300**, Form-B **$2,725** (both = our sums); "Ed Parigian (loan) $500" correctly `donor_type=loan` |

### Notes for future maintenance
- Re-run vision idempotently with `python3 parkcity_vision_extract.py` (skips cached). A figure that
  won't reconcile stays blank + `needs_review` + `low` — never guessed.
- The **QuickBooks P&L** expenditure exports (some 2017 filers) and **stacked two-report PDFs** are
  the two structural cases left honestly flagged; a dedicated path could recover them if ever needed.
