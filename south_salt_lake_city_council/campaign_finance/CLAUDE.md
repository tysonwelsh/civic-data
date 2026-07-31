# South Salt Lake — campaign_finance/ (build + linkage detail)

**ACQUISITION-ONLY** campaign-finance layer (source 6 of `/expand-city-sources`). Purely
additive; no existing dataset was modified. 68 filings retained verbatim under `raw/` with a
`_fetch_log.jsonl` (url, status, bytes, sha256, retrieved_utc). **No dollars extracted** —
`extraction_method='none (acquisition-only; …)'` on every row. Read `AVAILABILITY.md` first
for coverage, the search order, and the discrepancy flags.

## Where the filings live (two hosts, one pattern each)

- **City CivicPlus Archive Center** (2023 / 2025 / 2026-vacancy / COI). From
  `sslc.gov/469/Campaign-Finance-Statements` + `/559/Conflict-of-Interest-Disclosures`, each
  archive module is `Archive.aspx?AMID=<n>`; individual documents are
  **`Archive.aspx?ADID=<n>`** which 302-redirect to `/ArchiveCenter/ViewFile/Item/<n>`
  (`application/pdf`). Modules used: **AMID 61** (2025), **62** (2023), **64** (2026 council
  vacancies), **60** (COI). ⚠ The document rows render server-side but the links are `ADID=…`,
  not `DocumentCenter/View` — parse the `Archive.aspx?ADID=(\d+)".*?<span>(title)</span>` pairs
  from the saved listing HTML (kept in `raw/_listings/`).
- **State LG tree** `disclosures.utah.gov/Municipal` (2021 only — the city Archive Center
  begins at 2023). Chain: `/Municipal/salt lake` → `salt lake_2021` →
  `salt lake_2021_South Salt Lake City` (9 PDFs). Dir listings 403; files GET fine. Links carry
  Windows **backslash** paths → rewrite to `https://municipal.utah.gov/salt%20lake/2021/South%20Salt%20Lake%20City/<file>`
  (forward-slash + `%20`; a literal comma in `Surname, Given.pdf` is left unencoded but breaks a
  CSV `--batch` — those 9 were fetched one-per-call).

## Build (reproducible)

1. `python3 sslc_cf_fetch.py` — parses the four saved Archive-Center listings in
   `raw/_listings/` (+ the hardcoded 2021 state-file list), writes `_fetch_manifest.json`, and
   downloads every filing into `raw/` via `polite_fetch.py` (1 s/host, `--now` frozen). Re-run is
   idempotent (polite_fetch overwrites by name). NB the 9 state 2021 files are fetched
   individually (comma-in-URL vs `--batch`); the script auto-handles this.
2. Detect born-digital vs scanned: `pdftotext -layout` per file, `<120` real chars ⇒ `scanned`
   (written to `_textmeta.json`). 14 text / 54 scanned.
3. `python3 sslc_cf_index.py` — joins the manifest + textmeta + fetch-log sha256 and emits
   `index.csv` (§9 contract header + extension cols). The candidate→office/district/election-name
   map is the **verified election roster** (`election_results/*_by_candidate.csv`), hardcoded per
   `(cycle, surname)` — data-driven, not inferred.

Helper scripts (`sslc_cf_fetch.py`, `sslc_cf_index.py`) + build intermediates
(`_fetch_manifest.json`, `_textmeta.json`) live in this dir by design (dataset-local, unique
names). `raw/_listings/` retains the discovery HTML (Archive-Center modules + state/city pages)
as provenance.

## index.csv schema

SCHEMA_SPEC §9 contract prefix — `date, candidate, office, election_year, filing_type,
reporting_period, title, source_url, retrieved_date, format, extraction_method, path` — then
documented extension columns:
- `district` — 1–5, `At-Large`, `At-Large-2yr`, or blank (Mayor / COI-Mayor).
- `source` — `city_archive_center` | `state_lg_municipal_disclosures`.
- `adid` — the CivicPlus Archive document id (blank for state-tree files); keys the two distinct
  2023 "Final"-labelled filings per candidate so they never collapse.
- `is_incremental` — `no` for CF rows (a cumulative Year-to-Date column exists on the form; see
  the double-count note in `AVAILABILITY.md`); blank for COI.
- `date_precision` — `label_inferred` / `label_year`. **The `date` is anchored to the report
  LABEL / statutory deadline, NOT a signature date read from the PDF** (most are scanned). Verified
  anchors: 2025 "Post Election Filing" = Dec-4 post-general (from Wood's born-digital checkbox);
  2023 period order from born-digital transaction windows (≤Oct 22 / Oct 23–Nov 8 / Nov 15+).
- `in_election_results` — `yes` / `no` / `n/a` (COI): does this person appear in the SSL
  election roster.
- `matched_election_candidate` — UPPER-CASE election-roster name; `join_confidence` — `exact` |
  `normalized` (Nicholas↔Nick, LeAnne↔LEANNE, Ray deWolfe↔G. RAY DEWOLFE) | `person_only` (Jones,
  2026 vacancy) | `none` (2026 vacancy applicants not in the roster) | `n/a` (COI).
- `sha256` — mirrors `raw/_fetch_log.jsonl`.

## filing_type classification

`interim` (2025 pre-general reports + 2023 election-period report) / `summary` (year-end /
post-general finals, single-file 2021 state filings, 2026 vacancy filings) / `coi_disclosure`
(the 8 FY2026 elected-officer conflict-of-interest forms — **excluded from any money total**).
Filing-type is best-effort from the city's verbatim archive LABEL (preserved in
`reporting_period` + `title`); the exact statutory report type per scanned file is a
deferred-extraction question.

## Linkage to the rest of the repo

Join `matched_election_candidate` → `election_results/south_salt_lake_races.csv` /
`_results_by_candidate.csv` on person + `election_year` + `district` (normalize case; mind the
`At-Large-2yr` special and the D1/D5 **elected-vs-serving appointment** nuance in the city
`CLAUDE.md` — the 2026-vacancy filings are the appointive side of that seam). From there,
person → `db/civic.db` votes completes the elections→money→members→votes chain. **Coverage is
COMPLETE for every 2021/2023/2025 ballot candidate** (see the AVAILABILITY table).

## `vision/` — Read-tool transcription cache (2026-07-17; NO structured build yet)

The 40 **scanned** 2021/2023/2025 ballot-candidate filings were transcribed via
**`/cf-vision-transcribe`** (Read-tool method — **$0 API**, billed to the Claude Code
allotment, NOT `vision_extract.py`/the Anthropic API) into `vision/<hash>.json`. This is the
transcription cache ONLY — **the structured build is owner-gated and was NOT run**; this repo
still has **no `build_finance.py`, no `filing_totals.csv`, no dollar rollup**. The caches sit
ready for a future owner-approved build.

**Cache-key convention (established consistent with the tranche-1 cities — midvale's
`vision/` setup):**
- **Filename** = `sha1(<index.csv `path` value>)[:8].json` — e.g. `raw/2021_state_wood-cherie.pdf`
  → `sha1(...)[:8]`. (Midvale/West Jordan/Ogden convention; a future SSL `build_finance.py`
  must reproduce THIS to consume the cache.)
- **Body schema (midvale byte-for-byte):**
  `{"contributions":[{date,name,amount,in_kind}], "expenditures":[{date,recipient,purpose,amount,in_kind}],
  "total_contributions","total_expenditures","contributions_50_or_less","beginning_balance",
  "ending_balance","_meta":{index_path,candidate,office,filing_type,election_year,source_pdf,pages}}`.
  Amounts/dates are **strings verbatim as printed**; printed cover TOTALS are transcribed, never
  computed; illegible → `null` (a flagged gap, never inferred); source typos preserved.
- **Scope:** the 40 scanned filings for **2023 (15) / 2021 (9) / 2025 (16)** — every scanned
  ballot-candidate filing in the three election cycles. The **8 COI** forms and the **7 2026
  council-vacancy** filings were NOT transcribed (out of the election-cycle money scope; COI are
  not campaign filings). The 14 born-digital `text` filings need no vision cache.
- **Common source quirk (per the transcription pass):** SSL/state forms have **no
  "contributions of $50 or less" aggregate line** → `contributions_50_or_less` is `null`
  throughout. Several filers list the **cumulative Year-to-Date** itemization on every report
  (so per-report "Total this Period" ≠ the transcribed line-sum) and a few forms carry
  struck-through/handwritten-corrected totals — each cache preserves the printed figure with the
  reconciling judgment noted; a future build must apply the YTD-not-sum discipline (see the
  double-count trap in `AVAILABILITY.md`).

The **RESOLVED 2021 flag stands** (`AVAILABILITY.md` flag 1/2): the Wood/Christensen/Siwik
3-way was the 2021 **RCV general**, not a missing primary — do not "re-find" a 2021 primary.

## 2026-07-17 — STRUCTURED LAYER BUILT (family `vision_cache`)

`build_finance.py` (family **`vision_cache`**, shared helpers
`scripts/campaign_finance/vision_lib.py`) now writes the derived CSVs — regenerable,
never hand-edited. Query `cycle_totals.csv` for any per-candidate/race total; never sum
`filing_totals` yourself.
- **contributions.csv (839) / expenditures.csv (510) / filing_totals.csv (53) /
  cycle_totals.csv (24)** + `donor_aliases.csv` (1) + `finance_overrides.csv` (header) +
  `cycle_overrides.csv` (10). `validate_finance.py` **PASS (0 fails)**;
  `scripts/validate_city.py` **0 FAIL**.
- **13 born-digital `format=text` filings vision-transcribed** (they had NO cache before —
  the earlier note "The 14 born-digital text filings need no vision cache" is SUPERSEDED).
  Their text layers are UNSTABLE for a deterministic grammar (handwritten summary pages —
  Williams 305 / Mitchell / Campos 320; `SEE ATTACHED` scanned itemization — Karzen; an
  AcroForm mayor filing — Wood 314; per-candidate custom spreadsheets — Mitchell), and some
  money lives on attached image pages, so they were **Read-tool vision-transcribed** into
  `vision/<hash>.json` (now **53 caches** = 40 scanned + 13 text) rather than parsed from
  `pdftotext` — the alta precedent ("parse them or vision them; do NOT leave money out").
- **OUT OF SCOPE (excluded by `in_scope_fn`, no filing_totals row, WARN-only):** the 8
  FY2026 COI disclosures + the 7 2026 council-vacancy appointment filings (blank
  `election_year`). 53 of the 68 index rows are in-scope C&E filings.
- **REGIME = the SSL Utah 10-3-208 form is INCREMENTAL** (Column A "Total this Period" +
  Column B "Year to Date"; itemization is this-period). Each cache stores **Column A** as
  `total_*` (so the this-period rows reconcile) + the balance chain; a cycle total is the
  **sum of Column A** = the final report's printed **Column B YTD**. Regime is detected PER
  candidate-cycle (`detect_regimes`, decisions printed): **Sanchez 2023 / deWolfe 2025 /
  Potter 2023 = cumulative-restatement** (each report re-lists YTD → non-decreasing → latest
  wins; deWolfe is a "cumulative-YTD-on-every-report" filer); **all others incremental**.
- **YTD-not-sum discipline → 10 `cycle_overrides.csv` rows.** SSL's Dec year-end reports are
  `filing_type=summary` but are **per-period** (often $0 this period), so the generic
  `cycle_totals` "latest-summary-is-cumulative" rule mis-reads every incremental multi-filer
  (e.g. Pinkney would read $3,075 not $29,665.90). Each override cites the printed final
  **Column B YTD** (Pinkney $29,665.90/$28,376.63; Wood $35,915.11/$34,050.26; Karzen
  $14,969.48; Mitchell $4,940/$4,696.55) or the Σ-Column-A incremental total (Huff, Mila,
  Campos 2023, Bynum/Hampton 2025). **Campos 2025** override: `adid311` cover is STALE
  CARRYOVER of `adid304`, so summing covers double-counts — cycle = $6,750/$7,240.71 (the
  −$490.71 ending balance on `adid320` confirms).
- **Reconciliation:** 44/53 both-sides reconcile; 9 carry verbatim filer inconsistencies
  (flagged `needs_review`, NEVER adjusted): the 2021 Bynum/Siwik/Thomas/Wood
  struck-through/handwritten-corrected covers; **Campos 2025 `adid311` stale carryover**
  (cover $6,750/$7,175.78 vs itemized $0/$64.93 → `totals-only`); **Pinkney 2023 `adid336`**
  (cover $3,075/$4,531.55 vs itemized $2,325/$5,281.55 — both sides off by exactly $750);
  **Mitchell 2023 `adid340`** (cover expend $1,703.08 vs itemized $1,703.83, Δ+$0.75).
  `reconcile_cash_only=False` — cover totals include in-kind at face value (verified Karzen
  2025: $70 Poliengine/Strategic-Vision in-kind is inside the $5,802.69/$8,949.98 covers).
- **donor_aliases.csv (1):** `Nick Mitchell` → `candidate-self` (the candidate self-seed
  $800; shared normalizer misread `Nick`≠`Nicholas`).
- Backup of pre-existing modified files: `_backups/2026-07-17-cf-structuring/south_salt_lake/`
  (CLAUDE.md, AVAILABILITY.md, index.csv — index.csv unchanged; the derived CSVs +
  `build_finance.py` + the 13 text caches are greenfield).

## Caveats

- Acquisition layer: **no dollar figures** — do not quote totals from this dataset; run the
  deferred (owner-gated) build + `cycle_totals.py` pass first (the 40 scanned election filings
  now have `vision/` transcription caches; 14/68 are born-digital text).
- Dates are label/deadline-inferred (`date_precision`), not document-read.
- 2019 / 2011 filings did not surface (state shells empty / dead legacy `sslc.com` redirect —
  flag 3 in AVAILABILITY); this aligns with, and does not close, the known 2019/2011
  election-record gap. `election_results/` was NOT edited.
