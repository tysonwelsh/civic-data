# campaign_finance — South Jordan City

Municipal candidate **campaign-finance disclosure reports** (Mayor + 5 district council
seats), retrieved from the City Recorder's Elections publications. Added by the
`expand-city-sources` skill (source type #6).

**Structured extraction layer — IN PROGRESS (started 2026-07-06).** `build_finance.py` +
family `scripts/campaign_finance/families/southjordan_form.py` now emit
`contributions.csv` / `expenditures.csv` / `filing_totals.csv` (regenerable; never hand-edit).
The SJ form is a South-Jordan-specific "Campaign Financial Disclosure Report — Section 1.12.050"
(EasyVote-like Column A "this period" / Column B "year-to-date" summary + Schedule A/B
itemization); **is_incremental** anchors on Column A. **9 of 43 in-scope filings extracted so
far** (Johnson 2023 5329 from born-digital text; the 2025 Mayor race Ramsey+Barrett ×3 + McGuire
8747 + Hughes 8749 via Read-vision). The remaining **34 scanned filings still need vision**
(`vision/<sha1(index-path)[:8]>.json`, fed through `rows_override_fn`) — do NOT quote a
candidate's dollar total until its filings are extracted. **`cycle_totals.csv` is NOT built yet**
(deferred until all vision is done; see the double-count trap below). The 3 superseded 2023
uploads (5135/5148/5149) are EXCLUDED from the structured layer by `build_finance.py`.

Per-filing basis quirk: some post-general reports itemize the WHOLE CYCLE (reconcile to Column B,
`is_incremental=False`, e.g. McGuire 8747) rather than just the period — `build_finance.py`
detects this by which printed total the transcribed rows reconcile to and records it in
`filing_totals.notes`. Two source-arithmetic inconsistencies are honestly flagged (Ramsey 8620
expend Δ−2.00, Barrett 8746 expend Δ−3.53) — kept verbatim, not adjusted.

## Reconcile-flag spot-check — DISPOSITIONED 2026-07-19 (all HONEST source arithmetic)

The structured layer is now fully extracted (43/43 filings) and `cycle_totals.csv` IS built
(18 candidate-cycles; **0 cycle-level `review_flag` rows** — the `max(summary, summed-interims)`
rule never fires a MIXED flag here because `build_finance.py` marks every amended/re-filed
interim `superseded` so each candidate-cycle has exactly **one live filing**, `n_live=1`). The
**5 `filing_totals` rows that do not both-sides reconcile were spot-checked against their vision
caches** (row-sum vs the filer's printed cover total re-computed by hand); **all 5 are category
(a) honest source arithmetic — the filer's own cover total ≠ the sum of their own itemized line
items — NOT an extraction miss** (every itemized row + the cover total were transcribed
faithfully). Figures kept city-faithful; **no override written; `cycle_totals.csv` unchanged.**

| filing | side | cover total | itemized rows | Δ | disposition |
|---|---|---|---|---|---|
| **Barrett 2025 Mayor, doc8746** (LIVE summary) | expend | 227.18 | 223.65 (5 rows) | −3.53 | filer arithmetic; the ONLY flagged filing that feeds a cycle total (Barrett 2025 Mayor spent = the city-faithful 227.18) |
| Ramsey 2025 Mayor, doc8620 (superseded interim) | expend | 9,870.59 | 9,868.59 (12 rows) | −2.00 | filer arithmetic; superseded by clean summary doc8748 → excluded from cycle total |
| Johnson 2023 D2, doc5063 (superseded interim) | expend | 6,237.17 | 3,081.88 (6 rows) | −3,155.29 | filer's original PreGen cover overstated its own rows; she re-filed the same period as doc5329 (reconciles clean) and the cycle uses clean summary doc5328 → superseded, excluded |
| Bevans 2023 D2, doc5061 (superseded interim) | contrib | 7,045.72 | 7,000.00 (15 rows) | −45.72 | filer arithmetic; re-filed as doc5330 (clean); cycle uses summary doc5340 → excluded |
| Lewis 2025 D3, doc8519 (superseded interim) | expend | 17,469.89 | 17,479.89 (30 rows) | +10.00 | filer arithmetic; re-filed as doc8605 (clean) + summary doc8743 (clean) → superseded, excluded |

Net: **4 of 5 sit on superseded interims that `build_finance.py` drops** (never enter any cycle
total); **only Barrett doc8746 carries its $3.53 city-faithful gap** into the Barrett 2025 Mayor
row. No pipeline defect; nothing to correct. (Supersedes the stale "9 of 43 extracted /
`cycle_totals.csv` NOT built" wording above — that intro predates the completed vision pass.)

## What's here

```
raw/city/        filings still served by the live CivicPlus DocumentCenter (2021,2023,2025)
raw/wayback/     2019 filings recovered from the Internet Archive (live URLs 404)
raw/discovery/   archived-HTML captures used to discover the id->candidate->report mapping
raw/*/_fetch_log.jsonl   byte-level provenance (url, status, bytes, sha256, retrieved_utc)
index.csv        one row per filing PDF (46 rows)
AVAILABILITY.md  where the filings live, what was searched, honest gaps
```

## index.csv columns

§9 contract: `date, candidate, office, election_year, filing_type, reporting_period,
title, source_url, retrieved_date, format, extraction_method, path`. Source-specific
added alongside: `source, district, in_election_results, date_precision, note`.

- **`filing_type`** ∈ `interim` (any Pre-General report) / `summary` (Post-General, i.e.
  the post-election final; and the 2019 combined pre+post PDFs). Set **per PDF**, not per
  candidate — candidates file several reports per cycle (see the double-count note below).
- **`reporting_period`** — the city's **verbatim** label (`Pre-General 28 Day Report`,
  `Pre-General 7 Day Report`, `Post-General 30 Day Report`, `Pre-General Financial
  Disclosure`, `Post-General Financial Disclosure`, the 2019 combined label). Kept
  alongside the normalized `filing_type`.
- **`format`** — `scanned` (42/46; photographed/handwritten state forms) or `text` (4 with a
  real PDF text layer). `extraction_method` is `none (raw acquisition; OCR/vision deferred)`
  for all rows — nothing has been extracted yet.
- **`source`** — `city_website` (live DocumentCenter) or `city_website_wayback` (2019, bytes
  from the Internet Archive; `source_url` still records the original city URL).
- **`date` / `date_precision`** — estimated by report class (`est_report_class`): pre-general
  `<year>-10-15`, post-general `<year>-12-01`. Exact filing dates are inside the scanned
  forms; capture them during OCR and add alongside (never overwrite).

## Retrieval method (reproducible)

All fetches via `scripts/polite_fetch.py` (browser UA, ≥1s/host, logged). Discovery chain:
1. **2025** — parse the *Financial Disclosure Reports* column of the per-candidate tables on
   the live `/230/Elections` page → `DocumentCenter/View/<id>` PDFs.
2. **2021 & 2023** — the live page overwrites each cycle, so the id→candidate→report mapping
   was recovered from **Wayback** captures of `/230/Elections` (2022-03 for 2021; 2023-12 +
   2024-06 for 2023), then the PDFs fetched from the **still-live** DocumentCenter.
3. **2019** — old WordPress `/elections/` page (Wayback 2019–2020); combined
   pre+post PDFs under `/wp-content/uploads/2019/10/…`, fetched from the Archive
   (`web/<ts>id_/<url>`) because the live URLs 404. Wayback filenames prefixed `201910_`.

Re-run for a new cycle: parse the current `/230/Elections` finance column, fetch the new
`DocumentCenter/View/<id>` PDFs into `raw/city/`, append to `index.csv`.

## Linkage to the rest of the repo

- **Elections:** every filer joins to `election_results/south_jordan_races.csv` on
  candidate + election_year + district (100% this dataset). Election names are UPPER-CASE
  with occasional middle names — normalize before joining (e.g. `Jason Timothy McGuire` ↔
  `JASON TIMOTHY MCGUIRE`; `Dawn R. Ramsey` ↔ `DAWN R RAMSEY`).
- **Members/votes:** via the elected candidates, this completes the
  elections → members → votes chain (who funded the people casting the council votes).

## CRITICAL — double-count trap (read before ANY dollar aggregation)

Candidates file **multiple reports per cycle** (2025: a 28-day + 7-day pre-general + a
30-day post-general each; 2023: two pre-general + one post-general). Whether a report is
**cumulative** (restates cycle-to-date) or **incremental** is **not yet known** — it lives
in the scanned line items. **Do NOT sum `filing_type`/filings into a per-candidate cycle
total** until the structured step classifies `is_incremental` per filing and applies
`scripts/campaign_finance/cycle_totals.py`. Also: **3 flagged superseded 2023 uploads**
(ids 5135/5148/5149, `note` says so) are re-uploads of the same pre-general report — never
count them as additional filings.

## Deferred (structured step)

OCR/vision the 42 scanned PDFs (this repo's default is the `/cf-vision-transcribe` skill,
billed to the plan), extract contributions/expenditures, classify incremental vs cumulative
per filing, build `cycle_totals.csv` with the shared dedup, and reconcile. Until then, quote
only *counts of filings* and *who filed*, never dollar totals.
