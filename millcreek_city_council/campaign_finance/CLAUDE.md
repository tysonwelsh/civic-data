# campaign_finance — Millcreek City candidate campaign-finance disclosures

Raw municipal campaign-finance filing PDFs for Millcreek City candidates (Mayor +
Council Districts 1–4), completing the **elections → members → votes** chain. Built by the
`expand-city-sources` skill (source #6). Raw originals under `raw/` + a provenance
`index.csv`; the **structured contribution/expenditure layer is now BUILT** (partial — see
"Structured layer" below and the double-count trap).

## Structured layer (built 2026-07-06 — `millcreek_form` family, F9)

`build_finance.py` → `contributions.csv` / `expenditures.csv` / `filing_totals.csv` (DERIVED —
regenerate, never hand-edit; corrections go to `donor_aliases.csv` / `finance_overrides.csv`).
Parser = `scripts/campaign_finance/families/millcreek_form.py` (the Millcreek "FINANCIAL
CAMPAIGN REPORT" Form A/B; reuses West Valley's section/date helpers). Framework contract:
`scripts/campaign_finance/SCHEMA.md`.

**Two Millcreek-specific form facts the parser encodes:**
- **3-column cover box** `TOTALS FROM LAST + THIS = CUMULATIVE`. Reconciliation anchor = the
  **THIS** column for per-period reports (2019/2023/2025, `is_incremental=True`) but the
  **CUMULATIVE** column for **2021** (each 2021 PDF is one combined whole-cycle bundle,
  `is_incremental=False`).
- **Interior subtotal "TOTAL"/"Total" lines** inside Form A/B are dropped from row parsing (they
  would double the itemized sum).

**Format is re-characterized PER FILING, not from `index.csv` `format`** (that label is
unreliable: 2023 are garbled-OCR typed tables, some 2025 mixed, several "text" are actually
scanned/handwritten, and a bare-decimal born-digital variant exists — e.g. Vice-2019-1285,
DeSirant-2025-5898). In text mode an amount must be a clean `$`-token, so OCR `$`→`S`/`§`/`9`
mangling yields a BLANK amount + `needs_review` (never a guessed digit); such filings fail
reconciliation and are the **gated-vision set** (`cf-vision-transcribe`, Read-tool method →
`vision/<doc_id>.json`, consumed by `build_finance.py`'s `rows_override_fn`).

**Status (2026-07-12): 41 filings · 30 both-sides reconcile · 0 need vision · PASS validation.**
All 41 are extracted (31 text-parsed or vision-cached 2026-07-06; the 5 big-delta filings
1215/2676/2682/4097/5763 re-verified by full Read-tool re-transcription 2026-07-12 — zero missed
rows). **Millcreek filers MIX cover-total conventions**: Jackson/Clark/Gray covers include
in-kind; **Vice + DeSirant covers are CASH-ONLY** (their old deltas were exactly their in-kind
sums: 1,700.00 / 1,865.18 / 5,998.00 / 750.00) — handled by the shared driver's
alternate-convention reconcile fallback (fires only on an exact match; notes the convention in
`filing_totals.notes`). The remaining 11 flags are all documented source-side: **Gale 5762**
(form's own total 10¢ under its rows), **Springer 4040/4104 + Holz 4097** (amended/no-activity
periods that re-list prior rows under a THIS=$0/amended-to-0 cover), **Vice 2676 expend**
(+293.22 = 2× two positive credit rows the form nets but the build sums as magnitudes),
**Silvestrini 1221** (+$1.00), **Uipi 2677 / Williams 2681 / Gray 5766 / Holz 3931** (small
source arithmetic deltas). Never adjusted, never guessed.

**Reconcile-flag spot-check re-confirmed 2026-07-19 (TODO low-priority CF review-flags pass):**
re-walked all **11** non-reconciling `filing_totals` rows above + the lone remaining
`cycle_totals` `review_flag` (Keller 2019 D3, documented SPURIOUS below) — every one is an
already-documented category (honest source arithmetic / in-kind-excluded-from-cover cash-only
convention for Vice+DeSirant / amended-or-no-activity restatement). No new pipeline defect; no
override added; `cycle_totals.csv` byte-identical after re-running `cycle_totals.py`. The 9
CUMULATIVE-column `cycle_overrides` (table below) remain the sanctioned per-candidate totals.

**✅ `cycle_totals` RUN + RECONCILED (2026-07-19) — `cycle_totals.csv` + `cycle_overrides.csv`.**
Millcreek "summary" (Dec) reports are (for most filers) **per-period** — each report's stated
totals are THIS-period only and the running cycle total lives **only in the cover box
CUMULATIVE column** (`TOTALS FROM LAST + THIS = CUMULATIVE`). So `cycle_totals.py`'s generic
rule (`max(summary, summed-interims)`) systematically **under-counts** these filers: it drops
whichever period is smaller (usually the post-election summary), and for Uipi it split a
`max-mixed` pair taking raised from one side and spent from the other. The **authoritative
per-candidate total = the LAST report's cover CUMULATIVE column** — read directly from each
summary PDF and encoded in **`cycle_overrides.csv`** (9 candidate-cycles, each page-cited to its
summary doc-id):

| candidate | cycle | cover CUMULATIVE (raised/spent) | was computed | summary doc |
|---|---|---|---|---|
| Jeff Silvestrini | 2019 Mayor | 88369.40 / 64859.50 | 75414.82 / 56078.32 | 1284 |
| Angel Vice | 2019 Mayor | 8531.51 / 8659.86 | 8213.52 / 7345.75 | 1285 |
| Silvia Catten | 2019 D1 | 300.00 / 350.00 | 350.00 / 350.00 | 1282 |
| Cheri Jackson | 2019 D3 | 4341.21 / 3882.89 | 4341.21 / 3318.83 | 1274 |
| Cheri Jackson | 2023 D3 | 12003.14 / 5926.59 | 11994.56 / 5708.39 | 4095 |
| Thom DeSirant | 2025 D2 | 60711.13 / 35842.92 | 59816.13 / 30796.43 | 5898 |
| Angie Gray | 2025 D2 | 5801.28 / 5801.28 | 5741.09 / 5314.82 | 5895 |
| Bev Uipi | 2025 D4 | 16303.85 / 6746.62 | 15540.90 / 3766.69 | 5896 |
| Connor Jett Gale | 2025 D4 | 1745.52 / 1737.27 | 1745.52 / 1139.36 | 5897 |

**Verified CORRECT as-is (no override):**
- **Jemina A. Keller 2019 D3** (`basis=summary`, 4628.68/4628.68) — carries a `MIXED` review
  flag but it is **SPURIOUS**: her summary (doc 1272) is a *cumulative restatement* (re-lists
  the interim's rows: cover CUMULATIVE = 2761.79 LAST + 1866.89 THIS = **4628.68**), so the
  summary already IS the cycle total. The flag fires only because summed-interims (2761.79) ≠
  the (cumulative) summary — expected for a restating filer. Do not override.
- **David F. Holz 2023 D3** (`sum-interim`, 603.11/603.11) — summary (doc 4097) is a THIS=$0
  no-activity report (cover CUMULATIVE 603.11 = the two interims), so the interim sum IS the
  cycle. Correct.
- **Scott Springer 2023 D3** (50.00/50.00) — $0/amended summary; total activity was $50. Correct.
- **All eight 2021 rows** — each candidate filed ONE combined whole-cycle bundle
  (`n_filings=1`, cumulative); `basis=summary` is correct.

Regenerate after any `build_finance.py` run: `python3 ../../scripts/campaign_finance/cycle_totals.py
millcreek`. The 9 overrides show `basis=override`; the lone remaining non-override review flag is
Keller (documented-correct above). **Never sum `filing_type` dollar figures** — and note the
cover LAST column can EXCEED the recorded interim stated total (Silvestrini: 87387.11 vs 75414.82;
Catten's interim contributions were mis-recorded), so even summing all periods can be wrong — the
last report's certified CUMULATIVE column is the single sanctioned source.

## What's here

```
raw/live/       PDFs still served by the live CivicPlus DocumentCenter (2021,2023,2025)
raw/wayback/    PDFs recovered from the Internet Archive (2019 — 404 on live host)
  _fetch_log.jsonl in each   provenance for the bytes (url,final_url,status,bytes,sha256,…)
index.csv       one row per filing PDF (schema below)
AVAILABILITY.md what exists, what doesn't, how verified, the election-mismatch artifacts
unrecovered.csv machine-readable gap log (2016/2017 pre-online era; 2023 cancelled races; COI out-of-scope)
CLAUDE.md       this file
```

**Coverage: 41 filings · 4 cycles (2019, 2021, 2023, 2025) · ~46 MB.** No 2016/2017 online
(pre-online paper era — see AVAILABILITY.md). Millcreek has no pre-2016 record at all
(incorporated Dec 2016).

## index.csv schema

Required minimum (skill non-negotiable): `date, title, source_url, retrieved_date, format,
extraction_method`. Millcreek columns, in order:

`date` (filing date; `YYYY-12-31` for the 2021 combined bundles, see `date_precision`),
`candidate`, `office` (Mayor/Council), `election_year`
(cycle: 2019/2021/2023/2025), `filing_type` (**interim** = pre-election report / **summary**
= post-election or combined year-end report), `reporting_period` (§9 contract column; blank
where not recorded), `title`, `source_url` (the
`/DocumentCenter/View/<id>` we requested), `retrieved_date` (2026-07-06),
`format` (`text` = born-digital / `scanned`), `extraction_method` (`none (raw acquisition;
OCR/vision deferred)`), `path` (dataset-relative, includes `raw/`), `district` (1–4; blank
for Mayor), `source`
(`city_website` / `city_website_wayback`), `final_url` (resolved slug URL), `doc_id`
(DocumentCenter id), `date_precision` (`exact` / `year_only`), `in_election_results`
(yes/no — the join flag), `redacted` (city-redacted PII copy), `sha256`, `bytes`, `note`.

`filing_type` uses the interim/summary vocab from the skill (Millcreek filings are the
report kind, not itemized contribution/expenditure extracts). Assigned by date vs the
cycle's election day (pre = interim, post = summary); the 2021 combined single-PDF bundles
are `summary` with a note.

## How it was built (reproduce)

1. **Discovery.** Live `/547/Disclosures` + `/161/Elections` (via `sitemap.xml`) for the
   current cycle; **Wayback CDX** on `millcreek.us/161/Elections` (legacy domain) +
   `millcreekut.gov/161/Elections` for the prior cycles. Archived HTML was parsed for
   `DocumentCenter/View/<id>/<slug>` links; candidate/date read from the slug and the
   surrounding page text (2021/2023 were bare `<id>` links whose candidate came from the
   list context — mapped in the fetch driver).
2. **Fetch.** All bytes through `scripts/polite_fetch.py` (browser UA + `--referer`,
   `--now 2026-07-06`). ⚠ **CivicPlus quirk:** the live DocumentCenter needs a **GET with
   the `/<slug>` suffix**; a bare `/View/<id>` or any `HEAD` returns a 404 HTML stub. The
   2019 cycle is 404 on live and came from `…/web/<ts>id_/…` archived URLs (`WebFetch`
   can't reach archive.org).
3. **Index.** `format` set per file by a `pdftotext -l 3` character-count threshold
   (≥200 chars over the first 3 pages ⇒ born-digital `text`, else `scanned`). Files renamed
   to `raw/<route>/<YYYYMM>_<Candidate>_<docId>.pdf` (upload-month prefix per skill).
4. **Validate.** `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
   millcreek_city_council/campaign_finance` → PASS.

Discovery/driver scripts were run from the session scratchpad (not committed); the
`index.csv` + `raw/` + `_fetch_log.jsonl` are the durable, reproducible record.

## Linkage to election_results (the join)

Join **person + election_year + district** to
`election_results/millcreek_results_by_candidate.csv` (normalize case; election names are
UPPER-CASE with `(NON)`/`(NP)`). **20 of 22 candidate-cycles join exactly; 39/41 filings.**
The 2 non-joins are honest **appointment artifacts** (`in_election_results=no`):
- **Cheri Jackson 2025 (Mayor)** — appointed Nov 2025 to finish Silvestrini's term; no 2025
  mayoral race exists (she is in election_results as D3 winner 2016/2019/2023).
- **Nicole Handy 2025 (D3)** — appointed Nov 2025; **never elected** (absent from
  election_results entirely).
Inverse artifact: **2023 Mayor (Silvestrini) & D1 (Catten)** were **cancelled-uncontested**
→ no campaign → no CF filing (correctly absent, not a gap). See AVAILABILITY.md.

## ⚠ Double-count trap — READ BEFORE STRUCTURING (deferred layer)

Candidates file **several reports per cycle** (interim pre-election + a post-election
summary), and the **filing style varies by candidate**. Do NOT compute any per-candidate
or per-race dollar total by summing filings. When the structured layer is built:
- classify `filing_type` + a per-filing `is_incremental` **per PDF** (2019 = interim+summary;
  2023 = interim+interim+summary; 2025 = interim+interim+summary; **2021 = one combined
  bundle per candidate** — treat as a single cumulative total, do not also add phantom
  interims);
- sanity-check each candidate's latest summary vs summed interims — divergence ⇒ mixed/
  cumulative filer needing the max-with-cumulative-guard rule;
- compute totals only via `scripts/campaign_finance/cycle_totals.py` (→ `cycle_totals.csv`)
  and clear every `review_flag` before quoting any "most expensive race" figure.
Also: some 2025 filings are **city-redacted** (`redacted=yes`) — donor PII removed, so
itemized contributor extraction will be partial for those. Extraction: 31 born-digital
(pdftotext/pymupdf) + 10 scanned (2019 + Uipi-2021 → OCR/vision, e.g. `cf-vision-transcribe`).

## Do NOT

- Do not treat 2016/2017 absence as an extraction miss — it is a pre-online-era publishing
  gap (paper filings), logged in `unrecovered.csv`.
- Do not edit `election_results/` to "reconcile" the appointment/cancelled artifacts — they
  are correct as-is.
- Do not sum `filing_type` dollar figures across a candidate's filings (double-count trap).
