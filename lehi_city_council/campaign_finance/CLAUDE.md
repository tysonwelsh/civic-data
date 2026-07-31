# campaign_finance/ — Lehi municipal candidate financial disclosures

Additive dataset built by the `expand-city-sources` skill (**Source 6**), as-of **2026-07-02**.
Does **not** modify any existing dataset. Completes the **elections → members → votes** chain:
who funded the candidates whose roll-call votes live in `../meeting_minutes/` and
`../planning_commission/`, and whose wins are in `../election_results/`.

## What this is
**134 municipal campaign financial statements** filed by Lehi **Mayor + City Council**
candidates for the **2019, 2021, 2023, 2025** cycles. Each is the Lehi/Utah "Municipal Campaign
Financial Disclosure" form (combined contributions = Form A, expenditures = Form B, and end
balance). Raw PDFs retained verbatim in `raw/<year>/`; provenance in the per-subdir
`_fetch_log.jsonl` (url, http status, bytes, sha256, retrieved_utc).

## Where the data comes from (see `AVAILABILITY.md` for the full source log)
Lehi runs its **own** municipal disclosure — the state site (`disclosures.utah.gov`) only
**redirects** to the city page. Filings live on the **city recorder's elections page**:
- **2025** — live current page `lehi-ut.gov/government/elections/financial-disclosures/`
  (`/media/<hash>/` PDFs). Downloaded directly.
- **2019 / 2021 / 2023** — the **legacy** page
  `…/campaign-finance-disclosures/` (`/wp-content/uploads/<YYYY>/<MM>/` PDFs) now **404s** on the
  live site (CMS migration). Recovered from the **Wayback Machine** (post-general snapshots of
  the legacy index page → original PDF bytes at their archived capture, via
  `web.archive.org/web/<ts>id_/<original-url>`).

## Layout
```
raw/
  2019/ 2021/ 2023/ 2025/   the filing PDFs (+ one .jpg scan), each with _fetch_log.jsonl
     names are <YYYYMM>_<orig-filename> (wp-content) or <mediahash>_<orig-filename> (2025)
  index_pages/              the disclosure INDEX HTML pages (live 2025 + 4 Wayback snapshots)
raw/_fetch_log.jsonl        provenance for the top-level 2025 index fetch
index.csv                   one row per filing (see schema below)
unrecovered.csv             12 known-missing 2023 report PDFs (never archived + 404 live)
build_index.py              regenerates index.csv from batch/manifest.json + files on disk
batch/manifest.json         the candidate→url→file manifest (build input; provenance of link lists)
AVAILABILITY.md             sources checked, what each had/didn't, gaps
```

## `index.csv` schema
Required minimum columns (`date,title,source_url,retrieved_date,format,extraction_method`)
plus source-specific columns:

| column | meaning |
|---|---|
| `date` | filing-period proxy. For 2019/21/23 = `YYYY-MM-01` from the `/wp-content/uploads/YYYY/MM/` path (the month the report was posted/filed). For 2025 (hashed `/media/` URLs carry no date) = the election year `2025`. **Approximate**, not the exact statutory due date printed inside the form. |
| `candidate` | filer name as published (mixed case). |
| `office` | `Mayor` / `Council`. Assigned by cycle (2019 & 2023 had **no** mayor race → all Council; 2021 & 2025 mayor filers = Johnson/Riddle, Albrecht/Binns/Condie/Tautuaa) and confirmed against `election_results` where the candidate appears there. |
| `election_year` | 2019 / 2021 / 2023 / 2025. |
| `filing_type` | `statement` (all — these are full financial statements, not separate contribution/expenditure schedules). |
| `reporting_period` | e.g. "Before Primary (Aug)", "Before General (Oct)", "Final/Post-election (Dec)", or the 2025 page label. |
| `title` | human label incl. the report period. |
| `source_url` | the **original** lehi-ut.gov URL (not the Wayback wrapper). |
| `retrieved_date` | (§9 contract column; blank where not recorded) |
| `format` | `text` (**69** born-digital, real text layer) / `scanned` (**65** image-only — 64 OCR'd PDFs + 1 `.jpg`). Set from the measured text layer (see "## Text sidecars" — the original build guessed by file extension and mislabeled 64 image-only PDFs as `text`). |
| `extraction_method` | `pdftotext -layout` (69) / `tesseract OCR (pdftoppm 300dpi)` (64) / `tesseract OCR (image)` (1). `text/` sidecars now EXIST (backfilled 2026-07-05) and the structured layer transcribes amounts from them — see "## Structured layer". |
| `path` | repo-relative path to the retained PDF. |
| `matched_election_candidate` | canonical `election_results` name this filer joins to (blank if none). |
| `join_confidence` | `exact` (normalized name match, 118) / `firstlast` (first+last match, middle initial differs, 6) / `none` (10 — 2019 primary-eliminated filers not in `election_results`). |
| `amended` | `yes` for the 5 candidate-filed amendments/revisions. |

## Join to `election_results/`
Filings join to `../election_results/lehi_results_by_candidate.csv` by **person + year**
(Lehi council is at-large — no district key). Names are normalized (upper-case, punctuation
stripped, `III/Jr` dropped) with a first+last fallback for middle-initial differences
(e.g. filing "Mark Johnson" ↔ results "MARK I. JOHNSON"). **All 12 general-election winners**
(2019 Albrecht/Southwick/Koivisto; 2021 Johnson[M] + Condie/Hancock; 2023 Stallings/Albrecht/
Newall; 2025 Binns[M] + Harrison/Freeman) **have ≥1 filing.** The 10 `none` rows are the 2019
"eliminated at primary" filers (see cross-dataset note below). From there, a winner's
council roll-call votes are in `../meeting_minutes/all_votes.csv` (join by person; case-fold —
finance is mixed case, minutes say "Councilor <Lastname>").

## Caveats / do-nots
- **Dates are period proxies, not exact due dates** — derived from the upload-path month
  (2019/21/23) or set to the election year (2025). The exact statutory due date is printed
  inside each PDF; read the raw file if you need it.
- **Amounts:** the raw index transcribes none — but the additive **structured layer**
  (`contributions/expenditures/filing_totals.csv`, see "## Structured layer" below) now does,
  for the born-digital filings, with per-filing reconciliation + honest confidence flags. Quote
  the structured layer only with its `reconciles_*` / `needs_review` caveats; otherwise open the
  raw PDF. (Lehi Free Press published 2019 & 2025 totals externally.)
- **12 missing 2023 reports** (`unrecovered.csv`) — never archived by Wayback, 404 live. No
  candidate is fully missing; every 2023 filer and all 3 winners have ≥1 recovered report.
- **2025 `Stephen Su'a-Filo`**: the live page's Su'a-Filo links point to E. LaRell Stephens'
  PDFs (a city page error) — there is **no distinct Su'a-Filo PDF**, so he has no row here.
- **2019 primary discrepancy (NOT fixed here):** the legacy page's "Eliminated at the Primary"
  list shows 8 extra 2019 council filers ⇒ Lehi **did** hold a 2019 primary, contradicting
  `election_results/CLAUDE.md` ("no primary"). Flagged in `AVAILABILITY.md` for a future
  `election_results` review; this additive dataset does not alter `election_results`.
- **Utah law context:** municipal candidates file under **Utah Code 10-3-208** and **Lehi City
  Code Title 1, Ch. 9 (§1-9-4)** — statements due 28 days before the primary and the general
  (plus post-election). Enforcement/hosting is the **city recorder's**, which is why the state
  and county sites don't hold Lehi's candidate PDFs.

## Rebuild
`python3 build_index.py` (reads `batch/manifest.json` + the files present in `raw/`; skips any
manifest entry whose file didn't download). Re-fetch raw via
`.claude/skills/expand-city-sources/scripts/polite_fetch.py --batch batch/<year>.tsv --out raw/<year> --now 2026-07-02T00:00:00Z`.

## Text sidecars (`text/`) — Source-6 backfill (2026-07-05)

This dataset originally shipped **zero** `text/` sidecars (a Source-6 conformance gap). They
were backfilled by **`backfill_text.py`**: `pdftotext -layout` for the born-digital PDFs,
`pdftoppm 300dpi + tesseract` for the image-only ones. **The original index mislabeled format
by file EXTENSION** — it called all 133 PDFs born-digital `text`; measuring the actual text
layer shows **69 are truly born-digital (text) and 65 are image-only scans** (64 OCR'd PDFs +
1 `.jpg`). `build_index.py` now reads `text_extraction.csv` (the backfill manifest) to set
`format`/`extraction_method` honestly per file; `validate_dataset.py` still **PASS**. Rebuild:
`python3 backfill_text.py && python3 build_index.py`.

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-05

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`
(Lehi is the **F5** family — "Municipal Campaign Financial Disclosure" + Form A/B). Contract:
`scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent; reads
`index.csv` + `text/*.txt`, writes the 3 CSVs). Validate:
`python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS**.

- **contributions.csv** 422 rows · **expenditures.csv** 300 rows · **filing_totals.csv** 134 rows.
- **Lehi is CUMULATIVE, not incremental** (`is_incremental=False`): each report restates
  whole-cycle-to-date Form-A/Form-B totals (verified Condie 2021 Oct $9,675 → Dec $9,835). A
  candidate+cycle's total is the **latest** (non-superseded) report, NOT a sum — 80 earlier
  snapshots are noted `superseded (cumulative snapshot)`; the 1 `amended=yes` original that
  survives grouping is noted `amendment`. **Do not sum a candidate's Lehi reports.**
- **Reconciliation (born-digital 69):** 8 reconcile clean both sides; **48 are template forms
  whose stated totals are blank in `pdftotext`** (fillable-AcroForm values that don't render, or
  the "1a/1b/2a/2b aggregate/itemized" 2023 variant left blank) — their itemized rows ARE
  extracted but the filing is **unverifiable** (`reconciles_*` blank, rows `needs_review=1`,
  `low`); 4 genuine mismatches (wrapped table cells / a `$13.750.55` pdftotext comma→period
  glitch). The **65 image-only scans** follow the Provo floor: **stated totals only from OCR,
  ZERO itemized rows**, flagged `low`. **~93% of contribution rows carry `needs_review=1`** —
  that is the honest signal that most Lehi filings could not be reconciled, not that extraction
  failed. Prefer rows on filings with `reconciles_contrib=True`.
- **Three born-digital form variants coexist** (the plan expected one clean form): (1) classic
  "MUNICIPAL CAMPAIGN FINANCIAL DISCLOSURE" numbered totals (cumulative, no in-kind column);
  (2) 2025 "CAMPAIGN FINANCIAL REPORT … for Reporting Period" (`In Kind` text-marked donations;
  "Total … for Reporting Period" is CASH, in-kind stated apart → reconcile cash-only);
  (3) 2023 "1a/1b aggregate/itemized total" template (blank fill-lines). Form A/B itemization is
  parsed uniformly across all three. Empty Form A tables emit ZERO rows (no phantom rows); form
  boilerplate that mentions "$500 or more/less" is excluded (rows must start with a date/N/A).
- **donor_type distribution** (422): individual 324, unknown 32 (21 blank-donor wrapped-cell
  rows + single-token names/orgs), business 25, candidate-self 20, family-of-candidate 10, pac 6,
  anonymous 4, carryover 1. Blank-donor rows → `donor_raw=''` + `unknown` + `needs_review=1`
  (never a promoted address). `donor_aliases.csv` seeds 3 verified merges (Utah Central Assoc.
  of Realtors / UCAR; The Governing Group PAC). `finance_overrides.csv` header-only.

### Hand-verification (5 filings, line-by-line vs `raw/*.pdf`, 2026-07-05)
| filing | check | result |
|---|---|---|
| Cody Black Before General 2019 (amended) | Form A self $2,224.85; Form B 10 rows Σ $2,224.85 = stated | ✓ MATCH |
| Cody Black Before Primary 2019 | $0 contrib; 5 expenditures Σ $1,123.67 = stated | ✓ MATCH |
| Paige Albrecht 28-day-general 2025 | cash contrib $4,550 = stated; 2 Governing Group PAC in-kind ($3,408.45 + $2,000) correctly `in_kind`, EXCLUDED from cash; Form B $5,894.65 = stated | ✓ MATCH |
| Chris Condie Before General 2021 | stated $9,675/$8,927.47 but the born-digital copy has an EMPTY Form A/B → 0 itemized rows | ✓ honest totals-only floor |
| Katie Koivisto Before General 2019 | Form A cells wrap across 3 lines (date below the amount); $1,200 in-kind "Copy That" + $200 not fully recovered → flagged | ✓ honest (documented wrapped-cell limit) |
