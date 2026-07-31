# campaign_finance — Town of Alta candidate campaign-finance disclosures

**ACQUISITION-ONLY layer** (source type 6 of `/expand-city-sources`). Raw filings retained
verbatim under `raw/` with a machine-readable `raw/_fetch_log.jsonl`; `index.csv` catalogs
every filing against the §9 contract. **No OCR/vision extraction and no dollar totals are
computed here** — `extraction_method` is `none (raw acquisition; OCR/vision deferred)` on every
row. Read `AVAILABILITY.md` for the coverage/threshold/discrepancy record.

## Scope & sources

Cycles **2021** (Mayor + Council At-Large), **2023** (Council At-Large), **2025** (Mayor +
Council At-Large). Town of Alta (~380 pop.) has its municipal elections **administered by the
Salt Lake County Clerk**; candidate filings are hosted in two places:

- **State `disclosures.utah.gov/Municipal` tree → `municipal.utah.gov` file host**
  (`source=state_lg_municipal_disclosures`): the **2021** folder `salt lake_2021_Town of Alta`
  (5 PDFs) and the **2023** folder `salt lake_2023_Alta` (3 year-end summaries). Directory
  *listing* on `municipal.utah.gov` is 403; individual files resolve — enumerated via the
  disclosures.utah.gov index page.
- **Town Juniper CMS GCS bucket** `storage.googleapis.com/juniper-media-library/130/…`
  (`source=town_website`): the **2023 town-side interim** "Financial Declarations" + candidate
  declarations (from `/conflict-of-interest-financial-disclosures/`), and the **entire 2025**
  money-report + declaration set (from `/elections-voting/`). The bucket is publicly enumerable
  via its S3-style XML endpoint (`?prefix=130/<YYYY>/<MM>/`) — the HTML pages render links
  client-side, so the XML listing is the reliable discovery route.

**2025 is hosted ONLY by the town** — the state 2025 entry just links back to
`townofalta.utah.gov`.

## index.csv schema

§9 campaign_finance contract prefix (exact, in order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method,path`
then Alta extras: `source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256,notes`.

- `filing_type` ∈ `summary` (single-cycle / year-end / final), `interim` (a period slice),
  `declaration_of_candidacy` (candidacy provenance, not a money report).
- `format` ∈ `text` (born-digital, 7 files) / `scanned` (image, 29 files) — per §9 vocab.
- `date_precision` documents anchored dates: `form_signature_date`, `reporting_period_end`,
  `report_date`, `candidate_filing_period_anchor` (declarations dated to the June filing window),
  `cycle_anchor_general_election_day` (the 2021 combined bundle).
- `is_incremental=yes` = discrete period slice (addable across periods); `no` = cumulative /
  final / single-cycle (do not add to the interims); blank = declaration.
- `matched_election_candidate` = UPPER-CASE `alta_races.csv` name; `join_confidence`:
  `high` (2021/2023 ballot candidates), `none` (2021 combined bundle, and **all 2025 rows** —
  the 2025 cycle is not yet in `election_results/alta_races.csv`; see AVAILABILITY FLAG 1).
- `sha256` from `raw/_fetch_log.jsonl`. Join candidates to `election_results/` on **person +
  year** (Alta is at-large; election names are UPPER-CASE; mind the two Bourkes — **Margaret**
  Bourke ran Council 2021, **Roger** Bourke is Mayor).

## Counts (as-of 2026-07-13)

**36 filings** — 2021: 5 · 2023: 15 · 2025: 16. By type: 13 summary, 15 interim, 8
declaration_of_candidacy. By source: 28 town_website, 8 state. Coverage is **COMPLETE per the
ballot roster** in every in-scope cycle (see AVAILABILITY table).

## Key facts (see AVAILABILITY.md for the full record)

- **2021/2023 are essentially nil** (small-town threshold exemption) — the lone substantive 2021
  filer is **John Byrne** ($5,000 raised); Schilling 2023 spent $69.96; everything else $0.
- **2025 is the substantive cycle** — Roger Bourke (Mayor) took an itemized **$2,000 PAC
  contribution**; withdrawn candidate John Byrne raised **$4,725** and refunded it all.
- **2025 discrepancy FLAG:** this dataset establishes the 2025 roster (Bourke Mayor; Anctil +
  Heimark Council; Byrne + Moxley withdrew) that `election_results/alta_races.csv` is still
  missing. **Do not edit the elections layer** — reconcile when the county posts 2025 SOVC.
- The **2021 "All campaign financial disclosures.pdf"** is a combined DUPLICATE bundle of the
  four individual reports; the un-redacted twin of Anctil's 2025 10-07 report was deliberately
  **not** downloaded (PII). Conflict-of-interest ethics statements are OUT OF SCOPE.

## `vision/` — Read-tool transcription cache (2026-07-17, wave2; $0 API)

Added by `/cf-vision-transcribe` (Read-tool method, billed to the Claude Code allotment, **no
Anthropic API**). **21 scanned MONEY reports** transcribed → `vision/<sha1(index_path)[:8]>.json`,
matching the tranche-1 convention (reference: `midvale_city_council/campaign_finance/vision/`).
The 8 scanned `declaration_of_candidacy` filings are NOT vision-transcribed (they carry no
contribution/expenditure lines); the 7 born-digital `format=text` reports don't need vision
(pdftotext-readable).

- **Cache key:** `sha1(index.csv `path` value, e.g. "raw/2023_morgan_finance-disclosure.pdf")[:8].json`.
- **Schema (per file):** `contributions[]` `{date,name,amount,in_kind}`, `expenditures[]`
  `{date,recipient,purpose,amount,in_kind}`, plus verbatim printed cover fields
  `total_contributions / total_expenditures / contributions_50_or_less / beginning_balance /
  ending_balance`, and a `_meta` block (`index_path,candidate,office,filing_type,reporting_period,
  election_year,source_pdf,pages,transcription_method`). Amounts are strings, **verbatim as
  printed** — no totals were computed; illegible → null.
- **STILL ACQUISITION-ONLY / owner-gated: no structured layer was built.** There is no
  `build_finance.py` here and `index.csv` `extraction_method` stays `none` — the caches are a
  forward-investment so a later structured build (or the owner) can consume them without paying
  for vision. Nothing here is summed or federated.
- **Substantive figures captured:** 2021 **Byrne** $5,000.00 self-funded contribution + 3
  expenditures ($239.89 total); 2023 **Schilling** the lone $69.96 USPS postage expenditure
  (present on 3 of his 4 duplicate/cumulative filings — do NOT sum). Everything else nil ($0).
  Alta's form has **no $50-or-less line and no beginning-balance line** (both `""` by design);
  line 1a (≤$25 aggregate) → `contributions_50_or_less`, line "balance at end" → `ending_balance`.
- **NOT in the vision cache (by design — they are `format=text`, pdftotext-readable):** 2025
  **Bourke** $2,000 Abundance Political Consulting PAC contribution (9/1/25) lives in
  `raw/2025_bourke_cf-report_10-03.pdf`; 2025 **Byrne** $4,725 raised-then-refunded is in his
  born-digital final. The scanned 2025 Bourke 10-28 "financial-determination" (`8a7b0789.json`)
  is a later interim that prints 0 and does NOT restate the PAC line — transcribed as printed.
- **PII:** the 2025 Anctil 10-07 vision cache (`74b0da4c.json`) transcribes the **redacted**
  public copy only; the blacked-out street address is null, never reconstructed.

## 2026-07-17 — STRUCTURED LAYER BUILT (vision-cache wave; family `vision_cache`)

`build_finance.py` (family **`vision_cache`**, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference impl: midvale) now writes the four
derived CSVs — **`contributions.csv` (3 rows) / `expenditures.csv` (7) / `filing_totals.csv`
(28 = the full in-scope inventory) / `cycle_totals.csv` (13 candidate-cycles)** — all
regenerable, never hand-edited. `validate_finance.py` **PASS (0 FAIL / 8 WARN**, the 8 WARNs
are the out-of-scope `declaration_of_candidacy` filings, correctly excluded).
`scripts/validate_city.py alta_city_council/` unchanged (24 PASS / 0 FAIL).

**How the 36 index rows flow (no silent drops):**
- **21 scanned money reports** → consumed from the `vision/*.json` caches via
  `vision_lib.build_result`.
- **6 born-digital `format=text` money reports** → parsed at build time by
  `_parse_text_form` (pdftotext -layout + a small two-era grammar). This is where the
  town's substantive 2025 money lives and it was correctly NOT vision-cached.
- **1 combined bundle** (`2021_all-campaign-financial-disclosures.pdf`) → inventory-only
  row (DUPLICATE of the four individual 2021 reports, each parsed separately; never summed).
- **8 `declaration_of_candidacy`** → OUT OF SCOPE (`in_scope_fn`; no C&E lines).

**Substantive money — all captured and PROVEN in the CSVs:**
- **2025 Roger Bourke (Mayor) — $2,000 Abundance Political Consulting** (2025-10-03,
  born-digital text). The raw Form A puts the $2,000 in the **In-Kind column** (the "Amount
  of Contribution" column is blank), so the row is `in_kind=True`; the cover 1b=$2,000
  includes it → **reconciles, `high` confidence**. Reclassified `individual`→**`business`**
  via `donor_aliases.csv` (it is an organization, not a natural person; the repo paraphrases
  it as a "PAC contribution" but the filing establishes only that the donor is an org, so the
  conservative org type is used — see the alias's `evidence`).
  ✅ **Registry check (2026-07-18):** Abundance Political Consulting is a private political
  consulting FIRM (commercial site abundancepolitical.com); no PAC registration surfaced on
  disclosures.utah.gov, and the contribution itself is in-kind services — consistent with a
  firm, not a committee. `business` is the evidenced classification, not just the
  conservative one. Flip to `pac` only if a Utah PAC/PIC registration is ever produced.
- **2025 John Byrne (Mayor, withdrew) — $4,725.11 self-funded then fully refunded**
  (2025-11-19 final, born-digital but with a scanned cover, so text has only the two itemized
  lines): 1 `candidate-self` contribution ($4,725.11) + 1 expenditure ($4,725.11 "Return of
  unused contribution"). No printed cover in the text layer → reconciliation UNKNOWN (blank),
  rows `low`/`needs_review` — honest, money kept.
- **2021 John Byrne — $5,000 self-funded** (`candidate-self`) + $239.89 in 3 expenditures
  (vision cache; reconciles both sides).
- **2023 Dan Schilling — the lone $69.96 USPS expenditure**. It appears on **3 of his 4
  duplicate filings**; regime detection classifies Schilling 2023 **cumulative** (restatement
  chain), so 3 filings are marked superseded and `cycle_totals` counts **$69.96 once**
  (n_live=1 of 4). Never summed.

**Per-candidate regimes** (`vision_lib.detect_regimes`, printed every build): Schilling /
Morgan / Davis 2023 and Anctil / Heimark 2025 are **cumulative** (nil/de-minimis restatement
chains → latest wins). **Bourke 2025 is incremental** (default, <2 caches). His near-empty
11-17 "final" would mask the 10-03 $2,000 under a naive "summary wins" rule, but
`cycle_totals` takes `max(summary, summed-interims)` and recovers **$2,000** — so **no
`cycle_overrides.csv` row was needed** (never override a cycle you can honestly compute).

**Curated files:** `donor_aliases.csv` — 1 row (Abundance → business).
`finance_overrides.csv` — header-only (no row-level corrections needed; every arithmetic
mismatch is a reconcile flag, and there are **zero** contrib!=stated / expend!=stated flags).
`cycle_overrides.csv` — not created (none warranted). **Moxley 2025 final** is born-digital
but its field overlay is pdftotext **mojibake** (U+FFFD ×11) → honest **inventory-only** nil
row (no fabricated totals). Backups: `_backups/2026-07-17-cf-structuring/alta/`.

**Read `cycle_totals.csv` for any per-candidate/per-race total — never sum `filing_totals`.**
Regenerate: `python3 build_finance.py` then
`python3 scripts/campaign_finance/cycle_totals.py alta`.

## Rebuild / refresh

Filings are static public PDFs. To refresh: re-enumerate the state folders
(`disclosures.utah.gov/Municipal/salt lake_<year>_Alta`) and the town GCS prefixes
(`storage.googleapis.com/juniper-media-library?prefix=130/<YYYY>/<MM>/`), fetch new PDFs through
`scripts/polite_fetch.py` (GET-only, logged) into `raw/`, and append to `index.csv`. A later
extraction pass (OCR/vision → `text/` sidecars + dollar totals via
`scripts/campaign_finance/cycle_totals.py`) is deferred and OUT OF SCOPE for this acquisition layer.
</content>
