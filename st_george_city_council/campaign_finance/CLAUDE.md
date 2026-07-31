# campaign_finance/ — build method, linkage, caveats

Municipal **campaign-finance disclosures** for St. George, Utah candidates (Mayor +
City Council, all at-large), completing the elections→members→votes chain. Additive
dataset built by `expand-city-sources` Source 6. **As-of 2026-07-02.**

## What's here

- `raw/` — 14 disclosure **packet PDFs** verbatim (+ `_fetch_log.jsonl` provenance:
  url, status, bytes, sha256, retrieved_utc). 10 live from `sgcityutah.gov`, 4 recovered
  from the Internet Archive (2021, old `sgcity.org` domain).
- `text/` — one **OCR sidecar per packet** (`tesseract --psm6 @200dpi`). Machine OCR of
  scanned forms — **expect errors; not authoritative for amounts.**
- `index.csv` — **104 rows**, one per (candidate, packet).
- `build_index.py` — regenerates `index.csv` from the packet→candidate mapping (the
  mapping is hard-coded there, derived from the OCR "Full Name of Candidate" fields).
- `AVAILABILITY.md` — per-source what-exists / what-doesn't + the 2019 gap.

## Source & coverage

| Cycle | Packets | Rows | Source | Office coverage |
|---|---|---|---|---|
| 2021 | 4 | 35 | Wayback (`www.sgcity.org`, migrated) | Mayor + Council |
| 2023 | 5 | 37 | live `sgcityutah.gov` | Council (no mayor race) |
| 2025 | 5 | 32 | live `sgcityutah.gov` | Mayor + Council |
| **2019** | **0** | **0** | — | **GAP — not archived anywhere (see AVAILABILITY.md)** |

Each raw PDF is a **combined packet**: all candidates who filed by one deadline, each as
an individual state "Campaign Finance Report" form, scanned into one file. We split each
packet into one index row per candidate (same `path` repeated), so the data joins by
person.

## index.csv columns

Required six first: `date, title, source_url, retrieved_date, format, extraction_method`
(here reordered to lead with `date,candidate,office,election_year,filing_type,reporting_period,title,...`).
Plus:
- `candidate` — canonical spelling **verbatim from `../election_results`** (UPPER-CASE),
  so a direct equ(year, candidate) join works.
- `office` ∈ `Mayor` / `Council`.
- `election_year` — the municipal cycle (2021/2023/2025).
- `filing_type` ∈ `interim` (periodic report filed while campaigning: pre-primary /
  pre-general) / `summary` (final closing report: year-end December for general
  finalists, or the post-primary closing report of eliminated primary candidates).
  *(The state form itself bundles summary + Form A contributions + Form B expenditures,
  so the `contribution`/`expenditure` filing_types are not used — every packet is a
  periodic/summary report carrying both.)*
- `reporting_period` — the `MM/DD/YY..MM/DD/YY` window when OCR captured it (2023 files).
- `source_url` — where the bytes were fetched (live city URL, or the
  `web.archive.org/web/<ts>id_/...` URL for 2021).
- `path` — dataset-relative incl. `raw/`.
- `candidate_match` ∈ `direct` (clean OCR name→roster match) / `inferred` (OCR-mangled
  name assigned by set-elimination within the packet against the known cycle roster —
  14 rows).
- `date_precision` ∈ `exact` (filing date from filename/period) / `inferred` (the one
  undated 2023 non-advancer re-post, dated to the 2023-08-29 pre-primary deadline).
- `source_archive` ∈ `city_live` / `wayback`.
- `original_url` — pre-migration `sgcity.org` URL for the Wayback rows.

## Join to the rest of the repo (elections → members → votes)

`index.csv.candidate` == `../election_results/st_george_results_by_candidate.csv.candidate`
for the same `year`/`election_year` — an **exact string match** (both UPPER-CASE).
**Verified: all 40 distinct (year, candidate) pairs join with zero unmatched.** From there,
race winners → councilmembers → roll-call votes in `../meeting_minutes/all_votes.csv`
(names there are mixed-case — normalize case, as noted in the election_results CLAUDE).

Coverage vs roster: every 2021/2023/2025 candidate in `election_results` has ≥1 filing.
Only the six **2019** council candidates have none (the 2019 gap).

## How it was built

1. Discovered links on the two live city pages (election_information.php +
   campaign_financials...php) via `polite_fetch.py` + link scrape. Resolved the Revize
   root-relative quirk by probing (`https://sgcityutah.gov/<file>.pdf` → 200).
2. Wayback CDX (`web.archive.org/cdx/search/cdx`) on the old `sgcity.org` domain to
   recover the 2021 packets (`web/<ts>id_/<pdf>`); confirmed 2019 absent by exhaustive
   CDX (queries logged in AVAILABILITY.md). `polite_fetch.py` for all fetches (WebFetch
   can't reach web.archive.org).
3. OCR every packet: `pdftoppm -r 200 -png` → `tesseract --psm 6` → `text/<name>.txt`.
   The embedded PDF text layer was low-quality; fresh 200-dpi tesseract was materially
   cleaner (e.g. "Full Name of Candidate Michele Randall").
4. Parsed the "Full Name of Candidate" / "Candidate for Office Of" fields to enumerate
   each packet's candidates; mapped to canonical roster names (14 OCR-mangled names
   assigned by set-elimination — flagged `inferred`).
5. `build_index.py` emits `index.csv`. Screened `text/` with `screen_corpus.py`.

Regenerate index: `python3 build_index.py` (idempotent; edit the `PACKETS` table there
to add/fix mappings).

## Caveats

- **Amounts are NOT in `index.csv`** and OCR amounts in `text/` are error-prone — always
  read the raw scanned PDF for actual contribution/expenditure figures.
- `filing_type` is inferred from filing timing, not a field on the form.
- 2021-12-02 year-end packet is missing Larsen's report (only 5 of 6 finalists present) —
  recorded as-found, not back-filled.
- The undated `2023financialcampaigndisclosures.pdf` duplicates the 8 non-advancer
  reports also present in the dated 2023-08-29 packet; both are indexed as distinct
  published files (`date_precision=inferred` on the undated one).
- Officeholder **Conflict-of-Interest** statements (2025/2026) exist on the same city
  page but are a different document class and are **excluded** here (see AVAILABILITY.md).
- **Correction (structured layer, 2026-07-06):** the undated `2023financialcampaigndisclosures.pdf`
  is NOT a duplicate of the 8 non-advancer reports in the 2023-08-29 packet — it holds those
  candidates' **separate post-primary CLOSING reports** (different, smaller amounts, e.g. Mackey
  $200 closing vs his $4,970 Aug pre-primary). It is a distinct filing period, summed (not
  superseded) in the money layer below.

## Structured layer (`contributions.csv` / `expenditures.csv` / `filing_totals.csv`) — 2026-07-06

Derived, regenerable money layer over the 104 filings. Contract: `scripts/campaign_finance/SCHEMA.md`.
St. George is the **compilation-PDF** city — one scanned PDF per deadline holds many candidates'
"Campaign Finance Report" forms back-to-back with **no page-range column**, so `build_finance.py`
runs a **candidate segmenter** first, then parses each candidate's slice with the
`stgeorge_formab` family, escalating unreconciled OCR to gated Claude vision. **Regenerate, never
hand-edit** (`python3 build_finance.py`); corrections go to `finance_overrides.csv` /
`donor_aliases.csv` (header-only so far). `segments.csv` is the regenerable segment→candidate map.

- **Form family:** `stgeorge_formab` (new). Two itemized tables — Form "A" (contributions,
  in-kind is a *description column*, not a section) + Form "B" (expenditures, **purpose printed
  AFTER the amount**). Two vintages: 2023/2025 `$`-amounts + cover "Itemized total …"; 2021
  (Wayback) **bare amounts + a mailing-address column + no Form-B purpose** and a "CAMPAIGN
  FINANCIAL REPORT" header. Reconciliation anchor = the per-table "Total … for reporting period"
  footer (cover line is the fallback); the itemized total **includes** in-kind, so all rows are
  summed (`reconcile_cash_only=False`).
- **Segmenter:** anchors on the `CAMPAIGN FINAN(CE|CIAL) REPORT` / `Full Name of Candidate`
  headers (page order does NOT follow index order in 2021 → **order-independent** greedy
  name-match, then weak-name + positional elimination for garbled OCR names). Result:
  **104/104 index rows aligned, 0 unmatched, 2 unaligned sections** (both are Michelle Tanner's
  genuinely duplicated 2021 cover pages — no donor data). Match confidence: 79 high / 8 medium /
  1 low / **16 elimination** (garbled 2021 + 2025 names — listed in `segments.csv`, all
  hand-checkable via `page_range`).
- **Dedup / cycle totals:** **INCREMENTAL** per candidate (verified: Hughes 2023 Aug $17,203 →
  Dec $5,000 — periods do not restate), so a cycle total = **sum of the deadline reports**. Each
  file carries a clean `reporting_period` label; the index's `summary` filing_type is mapped to
  `closing` in the money layer so `cycle_totals.py` (which treats SUMMARY_TYPES as cumulative)
  correctly SUMS St. George's incremental year-end reports instead of dropping the interims.
  `cycle_totals.csv` = **40 candidate-cycles, 0 review flags** — **read it for any candidate/race
  total; never sum `filing_totals` yourself.**
- **Rows:** contributions **1,354**, expenditures **1,103**, filing_totals **104**.
  `donor_type`: individual 1109 · business 80 · candidate-self 69 · unknown 43 ·
  **family-of-candidate 32** · loan 11 · anonymous 5 · pac 2 · party 2 · carryover 1.
  extract_method: vision 937 · ocr 413 · ocr+repair 4 (contributions).
- **Reconciliation:** **83/104 filings reconcile both sides** (tolerance $0.01). The **21 flagged**
  were all vision-processed yet still won't reconcile — genuine source/OCR ambiguities (a garbled
  printed figure, a nil filing, or a cover total that itself disagrees with the itemization); their
  rows stay **blank/needs_review=1/low, never guessed**. `validate_finance.py` → **PASS (0/0)**.
- **Vision (gated):** `stgeorge_vision_extract.py` (St.George-unique: renders only the candidate's
  **page range** from `segments.csv` via `pdftoppm -jpeg`, `claude-sonnet-5`, "transcribe exactly,
  mark illegible null, never infer"), fed back through the same reconciliation via the driver
  `rows_override_fn`. This run: **71 filings, 821,890 in / 165,538 out tokens, ≈ $4.95** (list
  price). Cache in `vision/*.json`; re-run `build_finance.py` to fold in.
- **The "everything in-kind" candidate:** Aros Mackey (2023) marks nearly every donation "In-kind"
  in the description column — recorded **verbatim** (`in_kind=True`, 19/21 rows); the two rows he
  described as "Loan" are correctly `in_kind=False`. Classify cautiously downstream.

### Hand-verification (5 filings vs the raw scans, 2026-07-06)
1. **Steve Kemp 2023 (VISION, 20230829 p16-19)** — 37 contrib / 24 expend reconcile; "Loan From
   Steve Kemp $10,000" → `loan`, "Kenny and Kasi Miller $100" match raw p17. ✓
2. **Dannielle Larkin 2023 (VISION, 20230829 p19-24)** — 86 donors = **$24,690** stated;
   "Dale Larkin $200" → **family-of-candidate** (shares the Larkin surname), matches raw p20-21. ✓
3. **Aros Mackey 2023 (all-in-kind, VISION)** — 19/21 rows `in_kind=True` per the printed flag;
   "Adaptive Ops … Loan" rows correctly cash. ✓
4. **Gregg McArthur 2023 (OCR, non-vision)** — Form-B purpose captured after the amount
   ("Design to Print $605 Signs & Brochures"); OCR typo "Marekting" preserved verbatim. ✓
5. **Segmenter attribution (dense 14-candidate 20230829 compilation)** — Kemp∩Larkin donor
   overlaps ("Brad Bonham" etc.) are **genuine shared donors** confirmed in raw p17 AND p21, NOT
   leakage; each candidate-unique donor ("Loan From Steve Kemp", "Dale Larkin") lands only under
   the correct candidate. Attribution correct across the packed compilation. ✓
