# campaign_finance — Kearns candidate campaign-finance disclosures

> **2026-07-18 — STRUCTURED LAYER BUILT (vision-cache reference implementation).** This is
> NO LONGER acquisition-only. `build_finance.py` (family **`vision_cache`**, shared helpers
> `scripts/campaign_finance/vision_lib.py` + `driver.py`) now writes the derived CSVs from
> the 38 vision caches — `contributions.csv` (61) / `expenditures.csv` (80) /
> `filing_totals.csv` (38, the FULL 2016–2021 inventory) / `cycle_totals.csv` (24
> candidate-cycles) — all regenerable, never hand-edited. `validate_finance.py` PASS (0/0);
> `scripts/validate_city.py kearns_city_council/` 0 FAIL. Key facts:
> - **Coverage is 2016–2021 ONLY.** 2023 (EasyVote auth-wall) + 2025 (city-site Cloudflare)
>   have NO index rows and therefore NO filing_totals rows — they are honest ACQUISITION GAPS
>   in `unrecovered.csv`/AVAILABILITY.md, never "nobody filed." Do not read their absence here
>   as zero activity.
> - **In-kind is included in the printed cover TOTAL at face value** (Perry 2016 June:
>   2500+150+100+130 in-kind = 2880 = printed) → `reconcile_cash_only=False` (midvale). 1
>   in-kind contribution row in the layer.
> - **Reconciliation:** 25/38 filings reconcile both sides against the printed covers; **12**
>   have a totals-only UNKNOWN side (≤$500 Summary-Page-only forms — the legal
>   non-itemization exemption; incl. Higginson's entirely-blank 2019 dissolution summary
>   `af72ce3e`, all-null by design); **1 genuine verbatim mismatch** — Richards 2019 interim
>   expenditures itemize to 1516.98 vs a printed 1511.75 (+5.23), flagged `needs_review`,
>   NEVER adjusted.
> - **Per-candidate regime** detected + printed by every build (`detect_regimes`): most
>   township cycles are single-filing; the multi-filing ones split cumulative-restatement
>   (Geertsen16/Welch16/Bush19/Peterson21/Gibson21/Snow21/RubyBrown19 — latest wins) vs
>   per-period (Perry16/Lefler16/Butterfield19/Schaeffer19/Higginson19/Richards19 — summed).
>   **Perry 2016 is the material case:** two interims (June 2880 / Nov 2850), incremental —
>   the Nov report's own Column B YTD prints 5730 = 2880+2850 and its beginning balance
>   (644.71) chains from June's close, so cycle raised = 5730 (the two $2500 Realtors gifts
>   carry distinct dates — not a double-count).
> - **One `cycle_overrides.csv` row (Butterfield 2019):** her Dec year-end 'summary' is itself
>   a period report carrying a genuine new $100 gift; default max(interim,summary) undercounts
>   to 196.90, but the Dec form's own Column B YTD prints 296.90 (raised) → override
>   296.90/296.90. NOTE the Dec expenditure Column-B YTD reads 295.90 (a verbatim $1 filer
>   arithmetic slip; the itemized period rows sum to 296.90 — flagged in the reason, not the
>   source). geertsen2019 (`3ec9a7d3`, join_confidence=low, no matching 2019 D3 contest) flows
>   through as a normal totals-only filing — the low join is NOT forced/reconciled.
> - Corrections route to `finance_overrides.csv` / `donor_aliases.csv` / `cycle_overrides.csv`
>   (none of the first two needed yet); backups in `_backups/2026-07-17-cf-structuring/kearns/`.

**ACQUISITION-ONLY layer** (source type 6 of `/expand-city-sources`). Raw filings retained
verbatim under `raw/` with a machine-readable `raw/_fetch_log.jsonl`; `index.csv` catalogs
every retrieved filing against the SCHEMA_SPEC.md §9 contract. `index.csv`
`extraction_method` remains `none (raw acquisition; OCR/vision deferred)` on every row (all
filings are scanned image PDFs) — the acquisition contract is unchanged. Read
`AVAILABILITY.md` for the full coverage/threshold/discrepancy record and `unrecovered.csv`
for the two blocked cycles.

## `vision/` — Read-tool transcription cache (2026-07-17, additive; NO structured layer)

All **38 scanned filings are now transcribed** into `vision/<sha1(index.csv path)[:8]>.json`
via `/cf-vision-transcribe` (Read-tool native image reads on the Claude Code allotment —
**$0 Anthropic API**). Cache-key + JSON schema mirror the tranche-1 cities (midvale's
`vision/`): `{contributions[], expenditures[], total_contributions, total_expenditures,
total_contributions_ytd, total_expenditures_ytd, contributions_50_or_less,
beginning_balance, ending_balance, _meta{index_path,candidate,office,filing_type,
election_year,reporting_period,source_pdf,pages}}`. Amounts are **verbatim as printed**
(illegible → null, never inferred); 21 filings carried itemized contributor/expenditure
rows, the rest are summary-only (≤$500 forms). One filing (`af72ce3e`, Higginson 2019
year-end/dissolution) has an entirely blank Summary Page → all totals null (honest empty).
**These caches are a transcription artifact ONLY.** Kearns has **no `build_finance.py`** and
**no structured contributions/expenditures/filing_totals layer** — that build (and any dollar
rollup) is **owner-gated and deliberately NOT created here**. `index.csv` was NOT modified.
Per-filing transcription notes (dbl/trip filenames = single reports not duplicates;
verbatim source typos; a handful of low-confidence handwritten cents flagged in each
cache's `_notes`) live inside the individual JSON caches.

## Scope & the jurisdiction split (this is the whole story)

Kearns is a **metro township (2017–2025) → city (2024-05; first city election 2025-11-04)**,
elections administered by the **Salt Lake County Clerk**. Campaign-finance FILING jurisdiction
splits by era, and so does the *retrievability*:

- **Metro-township filings (2016–2021)** were filed with the **county** and are posted on the
  SLCo Clerk's **static** page → **38 PDFs retrieved** (`source=slco_clerk_static`).
- **2023 (still a metro township)** moved to the county's **EasyVote** portal (2022+), which
  is **reCAPTCHA/auth-gated** → **not retrievable** under polite GET rules (honest gap).
- **2025 (now a city)** files with the **city** recorder and is posted only on
  **kearns.utah.gov**, which is **Cloudflare-blocked** → **not retrievable** (honest gap;
  Longtin's two filings are *proven to exist* via a retained Wayback landing page).

Per the metro-township cluster lesson (White City build): these entities are **absent from
`disclosures.utah.gov/Municipal`**; the state's 2025 entry is a **link-farm** to the blocked
city pages. Do NOT expect Kearns on the state tree.

## What's in `raw/`

- **38 `*.pdf`** — SLCo Clerk redacted candidate campaign-finance disclosures, 2016–2021.
- **1 `*.html`** — `2025_longtin_cf_landing_wayback.html`, the archived Wayback capture of
  Lyndsay Longtin's 2025 city CF landing page. **Evidence that 2025 filings exist**, retained
  as provenance for the gap; it is **not a filing** and has **no `index.csv` row**.
- **`_fetch_log.jsonl`** — every fetch (url, status, bytes, sha256, retrieved_utc).

## index.csv schema

§9 campaign_finance contract prefix (exact, in order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method,path`
then Kearns extras (mirrors the White City / Alta CF schema):
`source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256,notes`.

- **`filing_type`** ∈ `interim` (June/July/Aug pre-primary, Oct pre-general, Nov general-election
  report) · `summary` (December year-end). 30 interim / 8 summary.
- **`office`** = `Metro Township Council Seat N` (2016/2017 township labels) or
  `… District N` (2019/2021 township labels) — matched to `election_results/` era labels.
- **`format`** = `scanned` on all 38 (every "_redacted" county PDF is an image; `pdftotext`
  yields 0 chars). No `text` rows.
- **`date`** = first-of-labeled-month; **`date_precision=county_page_month_label`** — the
  county page shows only a MONTH per link (no day); the year is fixed by the Kearns staggered
  cycle + the pre-2022 scope of the static page, cross-checked to `kearns_races.csv`. Not fabricated.
- **`is_incremental`** = BLANK (deferred) — do NOT sum a candidate's filings before the
  OCR/vision pass classifies cumulative-vs-incremental (double-count trap; the Dec `summary`
  is expected to be the cumulative cycle total). Any dollar total → `cycle_totals.py`, never a row sum.
- **`matched_election_candidate`** = UPPER-CASE `kearns_races.csv` name where the person is a
  certified winner/runner-up; **`join_confidence`**: `high` (roster winner/runner-up),
  `medium` (real candidate not in the general winner/runner columns — the 2016 Seat-3 primary
  field), `low` (the 2019 Geertsen filing that the certified record doesn't list — see below).
- **`sha256`** recomputed from disk by the build script.

## Discrepancy the finance data surfaces (FLAG — do NOT edit election_results/)

`christophergeertsen2019.pdf` is a **2019** Geertsen candidate finance filing, but the
certified **2019 District 3** contest is **Butterfield vs Ruby Brown only** (`kearns_races.csv`).
Geertsen ran in **2016 and 2023**, not 2019 — he likely declared for 2019 then withdrew.
Indexed `join_confidence=low` + note; flagged here, **not reconciled** into the election layer.

## Counts (as-of 2026-07-13)

**38 filings retrieved** — by year: **2016** 16 · **2017** 2 · **2019** 14 · **2021** 6.
All `format=scanned`, all `source=slco_clerk_static`. **2023** (5 candidates) and **2025**
(6 candidates; Longtin's 2 confirmed to exist) are honest gaps in `unrecovered.csv`.

## Join to other layers

Join finance ↔ council votes/elections on **person + year + seat/district** — normalize the
UPPER-CASE election names first (e.g. `PATRICK DANIEL SCHAEFFER`). Kearns township seats were
single-member (Seat/District N), so the join is unambiguous per cycle. Mind the **Nov-2025
seam**: 2016–2023 rows are township council; 2025 (unretrieved) would be city Mayor/D2/D4.

## Rebuild / refresh

`index.csv` is generated from the retained `raw/` PDFs + `raw/_fetch_log.jsonl`:
```
python3 build_kearns_cf_index.py      # idempotent; recomputes sha256 + format from disk
```
The SPEC table (year/seat/candidate/month/filing_type/match) is hard-coded from the SLCo
Clerk page's per-candidate grouping + month labels. To refresh:
- **2016–2021 (static county page):** re-harvest anchors from
  `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/`.
- **2023 (EasyVote):** requires reaching `saltlakecountyut.easyvotecampaignfinance.com`
  (`ecf-api.easyvoteapp.com`) past its reCAPTCHA/auth-gate — a browser/session fetch, not
  polite GET. Endpoints noted in `AVAILABILITY.md`.
- **2025 (city site):** requires a non-Cloudflare-blocked fetch of `kearns.utah.gov`
  (`/resource-center/page/disclosure-statements` index +
  `/township/page/campaign-finance-disclosure-<name>` pages → `/media/<id>` PDFs).
Fetch new PDFs through `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py`
(GET-only, logged) into `raw/`, extend the SPEC table, and re-run. A later dollar-extraction
pass (`/cf-vision-transcribe` → `cycle_totals.py`) is deferred and OUT OF SCOPE here.
