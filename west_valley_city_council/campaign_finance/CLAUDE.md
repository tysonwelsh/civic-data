# West Valley City — campaign_finance

Municipal **candidate campaign-finance disclosures** for West Valley City (Salt Lake
County), odd-year cycles **2019 / 2021 / 2023 / 2025**. This is an **additive** dataset:
filings-as-documents + a filing-level `index.csv`, **plus a DERIVED structured
contribution/expenditure ledger** (`contributions.csv` / `expenditures.csv` /
`filing_totals.csv` / `cycle_totals.csv` — see "## Structured layer" below). The document
index still stops at the filing level; for donor/amount tables use the structured layer.

## Where the filings live (verified 2026-07-06)

West Valley City **self-hosts** its campaign-finance filings on the city website
(CivicPlus), in the **Archive Center**:

- Landing page: `https://www.wvc-ut.gov/2105/Campaign-Finance-Statements`
- Three Archive Center collections (the download engine), keyed by `AMID`:
  - `Archive.aspx?AMID=173` → **2025** cycle
  - `Archive.aspx?AMID=174` → **2023** cycle
  - `Archive.aspx?AMID=175` → **2021** cycle
  - (The page's nav labels the collections "2021 2023 2025" but the **AMID order is
    reversed** — verified by candidate roster + embedded filename timestamps. Trust the
    candidates, not the nav label order.)
- Each filing is `Archive.aspx?ADID=<n>` which 302-redirects to the PDF at
  `ArchiveCenter/ViewFile/Item/<n>`. `source_id` in `index.csv` is `ADID<n>`.
- WVC does **not** use EasyVote (all `*.easyvotecampaignfinance.com` subdomain guesses
  = NXDOMAIN; contrast West Jordan, which does). Not on `disclosures.utah.gov` either
  (that is the state candidate/PAC system; Utah municipal filings are with the city
  recorder per Utah Code 10-3-208).

**2019** is not in the Archive Center. One 2019 filing (Don Christensen's final,
`DocumentCenter/View/9949`) was recovered from the **Wayback Machine** (`id_` raw
variant); it is 404 on the live site. See `AVAILABILITY.md` and `unrecovered.csv`.

## Files

- `raw/` — every filing PDF, id-prefixed `<year>_<ADID|docid>_<slug>.pdf`. Retained
  verbatim. `raw/_fetch_log.jsonl` = one JSON line per fetch (url, status, sha256,
  bytes) — the provenance. 105 PDFs, ~93 MB.
- `text/` — one text sidecar per filing (Source-6 requirement). Born-digital →
  `pdftotext -layout`; scanned → Tesseract OCR @300 dpi (labeled `scanned` in
  `index.csv.format` / `extraction_method`).
- `index.csv` — filing-level index. One row per filing. §9 contract cols
  (`date, candidate, office, election_year, filing_type, reporting_period, title, source_url,
  retrieved_date, format, extraction_method, path`) plus:
  `district, filing_phase, source, source_id, in_election_results, election_winner,
  date_precision, pages, text_chars`.
- `text_extraction.csv` — per-file extraction audit (pages, char count, method).
- `AVAILABILITY.md` — every host/URL tried, per-year coverage, honest gaps.
- `unrecovered.csv` — 2019 filings proven referenced-but-unrecoverable.

## Column semantics

- `filing_type` ∈ `interim` | `summary` (the two that occur here) — `contribution` /
  `expenditure` are reserved for the future structured layer, not used at filing level.
  - `interim` = a periodic report (primary / post-primary / general 7-day reports).
  - `summary` = the candidate's **Final** campaign-finance statement.
  - `filing_phase` carries the finer native label (`primary`, `post-primary`,
    `general`, `final`, `declaration`).
- `date` — most filings carry **no explicit filing date** in the Archive Center title.
  Where a filename embedded the city's document-management timestamp (`_YYYYMMDD…`,
  some 2025 filings) `date_precision=day` (an **upload/scan** stamp, near but not
  identical to the statutory filing date); otherwise a **representative date by phase** is used
  (`date_precision=inferred`: primary→Aug 5, post-primary→Sep 15, general→Oct 27,
  final→Nov 30 of `election_year`). Never treat an `inferred` date as the true filing
  date; the year + phase are the reliable facts.
- `district` / `office` / `election_winner` are **join-derived** from
  `election_results/west_valley_results_by_candidate.csv` (general-election results). Blank
  district on a row usually means a **primary-only** candidate not present in
  `election_results` (see `in_election_results=no`).

## Join to election_results & flags

`in_election_results` marks whether the filer matched a general-election candidate.
`no` rows are almost all **primary-only / eliminated-in-primary / write-in** candidates —
`election_results/` is **general-only by design** (see its CLAUDE.md). These are flags,
not errors; `election_results/` was **not** edited. One notable gap the other direction:
a 2023 general **winner** (Will Whetstone, District 3) filed **no** campaign-finance
statement in the city archive — recorded in `AVAILABILITY.md`, not fabricated here.

## Reproduce

Filings were fetched with the skill's `polite_fetch.py` (GET-only, browser UA, 3s
delay, logged). The build scripts used for discovery/index live in the session
scratchpad (not committed); `index.csv` + `raw/_fetch_log.jsonl` are the durable record.
Cardinal rule: **never fabricate** — honest gaps (2019, Whetstone) are recorded, not filled.

## Structured layer (`contributions.csv` / `expenditures.csv` / `filing_totals.csv` / `cycle_totals.csv`)

DERIVED, regenerable money layer built from the `text/` sidecars (and gated vision) by
`build_finance.py` (shared engine `../../scripts/campaign_finance/`). Additive; does not touch the
CORE index/documents. Contract: `../../scripts/campaign_finance/SCHEMA.md`. **Regenerate, never
hand-edit** — corrections go through `donor_aliases.csv` / `finance_overrides.csv` (both header-only).

- **Form family: `westvalley_form`** (NEW — `families/westvalley_form.py`, F8), NOT easyvote/utah_standard.
  WVC self-hosts a distinct "CAMPAIGN FINANCE STATEMENT" (Form A/B): numbered **cover totals** are the
  reconciliation anchor ("1. Total contributions $X", "2. Total campaign expenses $Y" — there is **no**
  per-section printed TOTAL line); the itemized `ITEMIZED CONTRIBUTION REPORT (FORM "A")` /
  `…EXPENDITURE REPORT (FORM "B")` sections carry **bare-decimal amounts (no `$`)** sitting to the right
  of an **address column with a 5-digit zip**, so no `$`-anchored family tokenizer works. In-kind/loan are
  **inline in the donor name** ("(In-kind)" / "(Loan)"); the cover "Total contributions" INCLUDES in-kind
  (`reconcile_cash_only=False`). Two born-digital layouts (horizontal + **vertical**, date/name/address/
  amount each on its own line) and a dateless "Previous balance" carryover row are all handled; sections
  can appear in **either order** and repeat per page. `is_incremental` default `True` (per-period): verified Jake
  Fitisemanu 2021 general interim $3,204.87 → final $1,026.19 (a cumulative final would be ≥ the general) —
  **since 2026-07-20 empirically restamped per candidate-cycle** (11 cumulative filers; see the dated section below).

### Counts / reconciliation (as-of 2026-07-12)
- **contributions.csv 887 rows · expenditures.csv 795 rows · filing_totals.csv 105 rows** (1/filing).
- **69 / 105 filings both-sides reconcile clean** (2026-07-12: the 4 OCR-floor Buhler/Amosa filings
  transcribed via the Read-tool method — Buhler primary exact 18,030.00/12,311.13, Amosa exact, Buhler
  general/final honest ±$25/$75 candidate-arithmetic flags after fixing a $9,900 PAI-Managers cache
  misread — plus LeFevre's 2 filings flipped by the shared driver's in-kind-convention fallback).
- **⚠ Buhler 2021 files CUMULATIVELY**: his general and final Form A photocopy the whole cycle's
  schedules, so his three filings' rows overlap — never sum his period filings; `cycle_totals.py`'s
  cumulative-restatement rule (2026-07-12) detects this and takes the summary (Mayor 2021 =
  $27,584.45 / $26,717.47, basis=summary, no flag).
- **extract_method** — contrib rows: text 208 · ocr 45 · **vision 281**. expend rows: text 150 · ocr 16 ·
  **vision 525**. (Most scanned itemization is handwritten and only recoverable by vision.)
- `donor_type`: individual 322 · unknown 72 · candidate-self 48 · loan 41 · business 26 ·
  family-of-candidate 11 · pac 6 · anonymous 4 · carryover 4. (blank donor → `unknown`+`needs_review`;
  the 7 blank-donor rows are all OCR-illegible scanned rows.) `donor_raw` is verbatim — OCR-mode scanned
  rows that reconciled can carry garbled names (honest; not vision-cleaned since only *flagged* scans were escalated).
- **cycle_totals.csv: 41 candidate-cycles, 1 review_flag** (Don Christensen 2023 — summary $12.9k vs summed
  interims $9.6k; per-period vs cumulative ambiguity, took the larger). **Read `cycle_totals.csv` for a
  candidate/race total — never sum `filing_totals`.** Top races: Karen Lang 2021 Mayor ~$19.1k spent,
  Tom Huynh 2021 Council ~$15.9k, Don Christensen 2023 Council At-Large ~$12.9k.
- **Dedup rule** (`dedup_mode="incremental"`): distinct period reports SUM across the cycle; a same-period
  amendment/re-file supersedes its original (kept + noted, never dropped). 2 supersessions: Geovani Salazar
  2025 primary re-file, Ryan Mahoney 2025 final. cycle_totals.py does the per-candidate summary-vs-interim rollup.

### Gated vision (`vision_extract.py` → `vision/<ADID>.json`, `claude-sonnet-5`)
Only SCANNED filings that fail OCR reconciliation are escalated (born-digital never). Pages rendered
`pdftoppm -jpeg` 150dpi; strict "transcribe exactly, mark illegible null, do NOT infer/sum"; the model
returns each cover total verbatim and **build_finance uses them** (never the model sums). Fed back through
the SAME reconciliation via the driver `rows_override_fn`, so vision earns confidence only if it reconciles.
**55 filings vision-transcribed 2026-07-06, ~$2.67 (Sonnet list price).** The **4 remaining OCR-floor
filings** (Buhler 2021 ×3, Amosa 2025) were transcribed **2026-07-12 via the Read-tool method**
(`/cf-vision-transcribe`, $0 API) — see the counts section above and the dated TODO closure note.

### Hand-verified against raw PDFs (5, 2026-07-06)
| filing | mode | check |
|---|---|---|
| Darrell Curtis 2021 general (Council) | vision (typed scan) | Form A: Betti Curtis $600.00 + Self-Darrell Curtis $2,507.30 = cover $3,107.30 — **exact** match to page image ✓ |
| Darrell Curtis 2023 primary (Council) | vision (**handwritten**) | Form A "6-5-23 Self $1,000.00" transcribed exactly; $25 WVC filing + $480.72 phone = $505.72, balance $499.28 ✓ |
| Jake Fitisemanu 2021 general (Council) | born-digital (vertical layout) | 27 contrib rows recovered after the date-separator fix; reconciles to cover $3,204.87 / $2,678.68 ✓ |
| Marni LeFevre 2023 post-primary (Council D1) | born-digital | 20 contrib rows exact-match to raw; itemized $8,172 vs cover $7,472 (+$700) = the two **in-kind** rows ($200+$500) she excluded from her cover total — genuine, honestly flagged ✓ |
| Arnold Jones 2021 primary (Mayor) | born-digital | 1 contrib $127.98 vs cover $128.44 (−$0.46); 6 expend $134.96 vs cover $127.46 (+$7.50) — candidate arithmetic, honestly flagged ✓ |

### Per-candidate `is_incremental` + cycle_overrides (2026-07-20)

- **`is_incremental` is now EMPIRICAL per candidate-cycle** (`derive_incremental=True` → the shared
  `driver.derive_is_incremental()` row-overlap method), superseding this family's flat `True`. **11
  candidate-cycles are evidence-backed CUMULATIVE (`False`)** — later reports re-list earlier rows:
  Steve Buhler 2021 (the already-adjudicated ⚠ case above — flip matches, cycle figure untouched),
  Arnold Jones 2021, Darrell Curtis 2023, Don Christensen 2023, James (Jack) Fenn 2023, Jesus
  Jimenez-Vivanco 2023, Cindy Wood 2025, Danny George JR 2025, Justin Turcsanski 2025, Karen Lang
  2025, Ryan Mahoney 2025. All 11 audited row-level (restatement + stated-total chains; Wood's
  general page-verified — its attached report prints "TOTAL CAMPAIGN CONTRIBUTIONS 9,345.96 /
  EXPENSES 9,151.72", exactly the cycle row). A **date-blind amount-containment sweep** (the sandy
  Duerden trap) over all non-flipped cycles found **0** missed cumulative filers. Restamp is
  row-metadata ONLY: 515 contrib + 417 expend rows changed in the `is_incremental` column alone;
  `filing_totals.csv` byte-identical; `cycle_totals.csv` byte-identical bar the one override below.
- **`cycle_overrides.csv` (1 row, page-verified): Karen Lang 2025 Mayor = $10,244.85 / $10,244.85**
  (was $54.97/$54.97 — the generic rule took her balance-carry final as the cycle). Proof from all
  4 raw PDFs: the Post-Primary (10/6/2025) is cumulative — cover $10,244.85 / $10,189.88 / balance
  $54.97, Form A re-lists all 7 primary rows + 3 new, sums exact; the General (rec'd 10/21) and
  Final (rec'd 11/24) print $54.97 on the "Total contributions" line with **Form A empty** — that
  is the CARRIED BALANCE, not new money; the Final's Form B itemizes one new item (11/15/2025
  "Repay loan" Karen Lang $54.97) closing the chain to line-3 $0.00 exactly. Spent = 10,189.88 +
  54.97 = 10,244.85. This retires her 2025 row's prior understated figure; her 2021 Mayor cycle
  ($19.1k) is separate and untouched.
- Unchanged-but-now-honest: Cindy Wood 2025's final prints 0/0 with a $194.24 balance left
  undisposed on paper — source's own record, cycle stays at the printed 9,345.96/9,151.72.

### Rebuild
`python3 build_finance.py` (idempotent; reads `index.csv` + `text/` + any `vision/*.json`), then
`python3 ../../scripts/campaign_finance/cycle_totals.py west_valley` (consumes
`cycle_overrides.csv`). Validate:
`python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS (0 fails, 0 warns)**. Vision
backfill: `python3 vision_extract.py [--max-pages N] [<ADID>…]`.
