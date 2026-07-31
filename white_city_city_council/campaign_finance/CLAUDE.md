# campaign_finance — White City candidate campaign-finance disclosures

**ACQUISITION-ONLY layer** (source type 6 of `/expand-city-sources`). Raw filings retained
verbatim under `raw/` with a machine-readable `raw/_fetch_log.jsonl`; `index.csv` catalogs
every filing against the §9 contract. **No OCR/vision extraction and no dollar totals are
computed here** — `extraction_method` is `none (raw acquisition; OCR/vision deferred)` on every
row. Read `AVAILABILITY.md` for the coverage/threshold/discrepancy record.

## Scope & sources

Cycles **2023** (Metro Township Council At-Large) and **2025** (first city-era election: Mayor +
Council At-Large B + At-Large C). White City (~5,000 pop., Salt Lake County) is a **metro
township → city** (HB35, 2024-05-01); its elections are **administered by the SLCo Clerk**, but
municipal campaign-finance filings are hosted only by the **city itself** on its **Streamline**
site (`whitecity.utah.gov`, `source=city_website`):

- **`whitecity.utah.gov/elections`** — the **2025 campaign-finance money reports** (Utah Code
  10-3-208): 6 candidates × 3 reports (Oct 7 / Oct 28 / Dec 4 Final) = **18 PDFs**.
- **`whitecity.utah.gov/conflict-of-interest-disclosures`** — **10 conflict-of-interest ethics
  forms** (Utah Code 10-3-1301 / 67-16-1), captured as `filing_type=coi_disclosure` per the SKILL
  COI note. A *separate* statutory instrument — do NOT mix into money-report totals.

**The state `disclosures.utah.gov/Municipal` tree hosts NO White City filings in any year** (the
metro-township-origin entities — White City / Kearns / Magna / Copperton / Emigration — are
absent as a class); the **SLCo Clerk** page hosts county-office COIs only. **No pre-2024
(metro-township) campaign finance is published anywhere** (2023/2021/2019 are honest gaps —
confirmed against state, county, city, and Wayback). See `AVAILABILITY.md`.

## index.csv schema

§9 campaign_finance contract prefix (exact, in order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method,path`
then White City extras (mirrors the Alta CF schema):
`source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256,notes`.

- `filing_type` ∈ `interim` (a "Report Prior to General Election" period report — Oct 7 / Oct 28),
  `summary` (the Dec-4 Final Report), `coi_disclosure` (conflict-of-interest ethics form).
- `format` ∈ `text` (born-digital, 13 files) / `scanned` (image, 15 files) — per §9 vocab.
- `date_precision`: `report_type_box` (money-report date read from the checked report box on the
  10-3-208 form), `candidate_filing_anchor` (2025 candidate COIs anchored to the June candidacy
  window — no printed date), `coi_annual_anchor` (annual officer COIs anchored to the Jan 1-31
  filing window — no printed date), `form_signature_date` (Shelton 1/29/2026, Huish 1/28/2026).
- `is_incremental=no` on ALL money reports — the 10-3-208 reports are **cumulative** cycle-to-date
  (confirmed for Flint); the **Dec-4 Final is the authoritative per-candidate total**, so
  **do NOT sum the three reports** (double-count trap). `is_incremental` is blank on COIs.
  **Caveat:** Cardenaz's Final is under-filled ($0); his real total is on his Oct-7 report — a
  per-candidate dollar total must go through `scripts/campaign_finance/cycle_totals.py`, never a
  row sum.
- `matched_election_candidate` = UPPER-CASE `white_city_races.csv` name; all 8 people
  (Perry/Flint/Price/Denning/Mahoney/Cardenaz from 2025; Shelton/Huish from 2023) are present in
  `election_results/`, so `join_confidence=high` throughout. Join elections ↔ finance on
  **person + year** (White City is all at-large; election names are UPPER-CASE).
- `sha256` from `raw/_fetch_log.jsonl` (keyed by `source_url`).

## Counts (as-of 2026-07-13)

**28 filings** — **18 campaign-finance money reports** (2025: 12 interim + 6 summary) +
**10 coi_disclosure** (4 candidate COIs 2025 + 6 annual officer COIs 2025/2026). By format:
13 text / 15 scanned. By source: 28 `city_website`. **2025 coverage is COMPLETE per the ballot
roster** (all 6 candidates × 3 reports); **2023 and earlier: honest gap (no filings published).**

## Key facts (see AVAILABILITY.md for the full record)

- **2025 candidates are SUBSTANTIVE filers, not threshold-exempt** — Cardenaz raised $1,050
  (incl. $400 from sitting councilmember Greg Shelton); Flint self-loaned $820; Denning
  self-funded ~$978 in printing. The small-entity "likely exempt" expectation was overturned.
- **2023 metro-township finance is entirely unpublished** — aligns with the known metro-township
  election-record gap (`election_results/CLAUDE.md`). This dataset adds no 2023 money data and
  surfaces/contradicts no election contest.
- **Water-district decoy excluded** — `wcwid.utah.gov` (White City Water Improvement District) is
  a separate special district; not ingested.
- **COI ≠ campaign finance** — the "Disclosure Statements" page holds ethics forms captured as
  `coi_disclosure`; keep them out of dollar totals.

## vision/ — pre-staged Read-tool transcriptions (2026-07-17, NO structured layer)

The **10 scanned 2025 money reports** were transcribed via `/cf-vision-transcribe` (Read-tool,
$0 API) into `vision/<sha1(index_path)[:8]>.json` — the midvale cache-key + schema convention
(`contributions[{date,name,amount,in_kind}]`, `expenditures[{date,recipient,purpose,amount,in_kind}]`,
printed cover totals, `_meta`). This is a **pre-staged input cache only** — there is still **NO
`build_finance.py` / no structured contributions/expenditures layer** (owner-gated). The 5 scanned
COIs are NOT transcribed (ethics forms, no financial line items). Amounts/totals are **verbatim as
printed** (commas/trailing periods preserved; illegible → null, never inferred). All 40 pages read
cleanly. Honest observations surfaced by the transcription:
- **Blank schedules over non-zero covers:** Mahoney final ($1,543.03), Cardenaz Oct-28 ($1,050/$859.78),
  and Price final ($695.82) print cover totals but leave Schedules A/B **itemization blank** — so the
  documented $400 Shelton→Cardenaz gift and Denning's "~$978 printing" are **NOT itemized on the filed
  pages** (Denning's only scanned report, Oct-7, prints all zeros). Contribution/expenditure arrays are
  empty where nothing is itemized — no fabrication.
- **Column-placement quirk:** several filers put cycle-to-date figures in the wrong report column
  (Cardenaz Oct-28 in "thru Oct 7"; Mahoney final carrying the Oct-7 total) — captured verbatim.

## Rebuild / refresh

`index.csv` is generated from the retained `raw/` PDFs + `raw/_fetch_log.jsonl`:
```
python3 build_wc_cf_index.py      # idempotent; asserts every path exists + has a sha256
```
To refresh when a new odd-year cycle posts: harvest the labeled anchors from
`whitecity.utah.gov/elections` (money reports) and `/conflict-of-interest-disclosures` (COIs),
fetch new PDFs through `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py`
(GET-only, logged, browser UA) into `raw/`, then extend the spec table in `build_wc_cf_index.py`
and re-run. A later extraction pass (OCR/vision → dollar totals via `cycle_totals.py`) is
deferred and OUT OF SCOPE for this acquisition layer.

## 2026-07-17 — STRUCTURED LAYER BUILT (family `vision_cache`)

`build_finance.py` (family **`vision_cache`**, shared helpers
`scripts/campaign_finance/vision_lib.py`; reference impl = midvale) now writes the four
DERIVED CSVs — `contributions.csv` (**48**) / `expenditures.csv` (**48**) /
`filing_totals.csv` (**18** — all 18 money reports; the 10 COIs excluded by `in_scope_fn`) /
`cycle_totals.csv` (**6** candidate-cycles) — all regenerable, never hand-edited. Corrections
go through `donor_aliases.csv` / `finance_overrides.csv` / `cycle_overrides.csv`.
`validate_finance.py` **PASS (0 fails, 10 warns** = the 10 out-of-scope COIs). `validate_city.py`
unchanged at **23 PASS / 3 WARN / 0 FAIL**. Backups: `_backups/2026-07-17-cf-structuring/white_city/`.

**`vision/` grew from 10 → 18 caches (all 2025).** The pre-stage (2026-07-13 note above) cached
only the 10 fully-SCANNED money reports. Structuring added **8 more** for the reports the
pre-stage skipped as `index.format=="text"`, because their schedules carry REAL, cleanly-legible
money the ROLLOUT's cardinal rule (alta precedent — "do NOT leave that money out") forbids
dropping:
- **7 born-digital text**, transcribed via `pdftotext -layout`: Flint ×3 (identical Schedule A,
  **$3,550** raised / $1,723.35→$2,627.08 spent — a cumulative filer), Cardenaz Oct-7 (**$1,050**
  incl. the **$400 Greg Shelton** gift; $859.78 spent), Cardenaz Dec-4 Final (under-filled),
  Denning Oct-28 (zeros), Denning Dec-4 Final (**$978.73** self-funded printing).
- **1 image-schedule** (Perry Oct-28): born-digital COVER but its Schedule pages are scans →
  read via **Read-tool page images** (per-period: $0 in / $10.00 Google Ads out).

**The "do not inject" landmine is honored, not violated.** The $400 Shelton gift and the $978
Denning printing are recorded ONLY on the filed pages that actually itemize them (Cardenaz Oct-7,
Denning Dec-4 Final) — never fabricated into a BLANK scanned schedule. The earlier acquisition-era
belief that they were "not itemized on any filed page" was scoped to the 10 SCANNED caches; the
born-digital TEXT reports do itemize them (verified against the PDFs + AVAILABILITY's own §
"Threshold-exemption / dollar reality"). Perry Oct-7 cache spot-checked against raw page images
(9 contributions $7,705.50 / 12 expenditures $7,633.57 — exact); 4 more filings cross-checked
cache↔CSV.

**Per-candidate regimes** (`vision_lib.detect_regimes`, printed by every build — the acquisition
note's "is_incremental=no on ALL" is a per-candidate matter, not a constant):
- **Cumulative** (latest report wins): **Flint** (restates identical Schedule A on all three;
  Final $3,550/$2,627.08), **Denning** (only the Final carries money; $978.73/$978.73).
- **Incremental / per-period** (sum the periods): **Perry**, **Price**, **Mahoney**, **Cardenaz**.
  Price/Mahoney land correct via the generic max(summary, sum-interim) rule (Oct-28 zeros).

**Two documented `cycle_overrides.csv` rows** (the generic dedup mis-shapes them):
- **Allan Perry 2025** → raised **7,730.50** / spent **7,706.47** = SUM of all 3 periods
  (7705.50+0+25.00 / 7633.57+10.00+62.90). His Dec-4 "summary"-typed Final is itself a period
  report, so the max() rule drops it (midvale Mikolash pattern).
- **Phillip Cardenaz 2025** → raised **1,050.00** / spent **1,763.51**. His Oct-28 (scanned)
  RESTATES the Oct-7 covers over blank schedules (sum-interim would double-count to $2,100) and
  his Dec-4 Final is under-filled ($0 stated). Real cycle: $1,050 (Oct-7, unchanged after) /
  $1,763.51 = Oct $859.78 + Dec printing $903.73 (his own Final Summary Campaign-Total Col D).

**THREE blank-schedule-over-nonzero-cover filings reconcile as totals-only UNKNOWN, by design**
(`reconciles_*` blank + `totals-only(no itemization)` note — never fabricated rows): **Mahoney
Final** ($1,543.03), **Cardenaz Oct-28** ($1,050/$859.78), **Price Final** ($695.82). Plus two
verbatim quirk flags kept unadjusted: **Cardenaz Final** `expend!=stated` (one $903.73 Edge
Printing row over a $0 stated total — internal filer inconsistency) and **Denning Final** expend
side totals-only ($978.73 self-funded printing itemized under Schedule **A** — a column-placement
quirk captured verbatim, flagged not moved).

**Two curated `donor_aliases.csv` rows** correct deterministic mis-fires: `Yianni Loannou`
(individual — the tier-1 classifier trips `loan` on the substring in the surname) and
`Ashtree Legal Services` (business — no `Services` business token). Self-funding is captured:
Perry candidate-self, Flint/Price/Mahoney `loan` (self-loans), Denning candidate-self ($978.73).
