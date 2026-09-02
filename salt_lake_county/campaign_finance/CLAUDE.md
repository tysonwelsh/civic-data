# campaign_finance/ — Salt Lake County COUNTY-office campaign finance

Campaign Contribution & Expenditure (C&E) disclosures for **Salt Lake County elected COUNTY
offices** — Mayor, County Council (Districts 1–6 + At-Large A/B/C), Sheriff, District Attorney,
Clerk, Assessor, Recorder, Treasurer, Auditor, Surveyor. Built 2026-08-01 (county-acquisition
wave). Utah county candidates file with the **County Clerk**, not `disclosures.utah.gov`.

**This is the entity whose absence made the owner's "largest donor in a county race" query
fail.** That query is now answerable from `contributions.csv` for **every document the county
holds** — 2006–2015 (vision), the **2015–2021 PAPER slice** (vision, closed 2026-08-23), and
the **whole EasyVote 2022–2026 era** (197 filings from the API + the 238-filing row-less
residue transcribed by wave W2, closed 2026-09-01). It is unanswerable only for the 251
GRAMA-only online reports of 2015–2021 — see "Honest gaps".

**State of the layer, 2026-09-01 (read this before saying "Salt Lake County is done").**
✅ closed: 2006–2015 itemization (496/496 filings with a Summary Page); the **2015–2021 paper
slice (130/130 filings, 6,028 rows, wave W1, 2026-08-23)**; the API-itemized EasyVote filings;
and the **EasyVote row-less residue (238/238 transcribed + 2 school-board out of scope,
18,240 rows + 141 new covers, wave W2, 2026-09-01)**. ❌ **unacquired — the county's ONLY
remaining gap:** the **251 online-filed 2015–2021 reports, GRAMA-only** (the county portal
application is dead).

## What this is
Three acquisition eras (full recon in `RECON.md`, source log in `AVAILABILITY.md`):
- **(a) Legacy clerk PDFs, ~2006–2015** — `raw/clerk_legacy/` — 547 per-candidate report PDFs
  from `slco.org/clerk/financialDisclosurePDF/`. RAW + **stated totals for every filing**
  (vision, complete 2026-08-02) + an **ITEMIZED donor/vendor layer, COMPLETE for every filing
  that has a Summary Page** — 496 of 496, closed 2026-08-03 (wave B2 + residue; see "The
  itemization tranche" below; run `python3 vision_coverage.py` for the
  live count, never quote it from memory). `pdftotext` is useless for the figures here — see
  "Image-only text" under Honest gaps.
- **(b) The 2015–2021 era — its PAPER slice is CLOSED; its ONLINE slice is GRAMA-only.**
  `raw/globalassets/` — **130 paper-filed county-office PDFs** from the clerk page's
  `globalassets` URL family (plain GET, zero overlap with `raw/clerk_legacy/`), harvested
  2026-08-20 and **FULLY TRANSCRIBED 2026-08-23 (wave W1): 717 pages, stated totals for all 125
  filings that have a Summary Page, and 6,028 itemized rows — 3,422 contributions + 2,606
  expenditures.** This is the ONLY slice that populates **`donor_occupation`** (its Schedule A
  pre-prints an Occupation/Employer column no other era has). See "The 2015–2021 paper slice"
  below. The other slice, **251 online-filed reports, is GRAMA-only**: the county disclosure
  portal's application is DEAD (not WAF-blocked — a real browser gets the same connection reset),
  and Wayback never crawled the report pages. Inventories in `_recon/2026-08-20-portal-probe/`.
- **(c) EasyVote portal, 2022–2026** — `raw/easyvote/` (442 redacted PDFs) + `raw/easyvote_api/`
  (the itemized JSON — the authoritative **structured** source for the filings it covers).
  **197 of the 442 documents are itemized by the API. The other 245 were NOT, and wave W2
  (closed 2026-09-01) transcribed them from the documents**: 240 filings in the derived queue
  (5 Fife-Jepperson filings sit outside it because the API does carry their school-board rows),
  238 transcribed, 2 ledgered out of scope. See "The EasyVote residue — wave W2" below.

## Layout
```
raw/clerk_legacy/    547 legacy PDFs + _fetch_log.jsonl (url, sha256, candidate, office, period)
raw/globalassets/    130 paper-filed 2015-2021 county PDFs + _fetch_log.jsonl (harvested
                     2026-08-20, transcribed 2026-08-23; characterisation in _audits/)
raw/easyvote/        442 county redacted PDFs (image-only) + _fetch_log.jsonl
raw/easyvote_api/    the 4 EasyVote API JSON responses (STRUCTURED SOURCE) + _fetch_log.jsonl
text/                text sidecars (<channel>__<name>.txt); born-digital layer only
vision/              VISION CACHES — **941 files, one per filing in the FOUR non-structured
                     eras** (clerk_legacy 547 + easyvote_2022 123 + globalassets 130 +
                     easyvote_2024_2026 141 — the W2 residue's 2024/2026 half; the residue's
                     97 filings from 2022 already had caches from the 2026-08-02 tranche),
                     keyed sha1(index.csv path)[:8]. Since wave B2 the clerk-legacy caches
                     ALSO carry their itemized Schedule A/B rows; since wave W1 (2026-08-23)
                     so do the 130 globalassets caches, which additionally carry
                     `totals_verbatim` where a coordinator adjudication applies; since wave W2
                     so do all 238 EasyVote-residue caches. See the tranche sections
index.csv            one row per acquired filing (both channels)
contributions.csv    DERIVED — 36,204 rows in FOUR appended blocks: EasyVote API (6,184),
                     clerk-legacy vision (14,746), the 2015-2021 paper slice (3,422), then the
                     wave-W2 EasyVote residue (11,852).
                     Carries TWO optional trailing columns: `geometry`, then `donor_occupation`
                     (SCHEMA §2c) — 12,517 rows carry one (W2 10,225 + paper slice 2,292)
expenditures.csv     DERIVED — 20,876 rows (3,757 API + 8,125 clerk-legacy + 2,606 paper +
                     6,388 wave-W2). ⚠ some filings print their expenditure amounts NEGATIVE
                     (Morris's ledger exports, Liewer 585D94D0, the legacy McAdams/Winder
                     rows); the sign is verbatim and reconciliation is on MAGNITUDE — take
                     abs() before summing this column
filing_totals.csv    DERIVED — 1,112 rows, one per filing: rows 1–171 are the structured
                     EasyVote-JSON 2024/2026 filings, 172–841 the 670 legacy + 2022 stated-totals
                     vision rows, 842–971 the 130 paper-slice rows, 972–1,112 the 141 wave-W2
                     EasyVote 2024/2026 covers (APPENDED, never interleaved). 26 of the vision
                     rows ALSO carry an API-supplied itemized half (2022 cycle) and 97 more
                     gained a VISION itemized half from wave W2.
donor_aliases.csv    CURATED (header-only seed)
finance_overrides.csv CURATED (header-only)
build_finance.py     builds the 3 structured CSVs from raw/easyvote_api/*.json, then APPENDS the
                     vision stated-totals rows (build_totals_tranche)
make_vision_caches.py materializes vision/*.json from the raw STATED-TOTALS transcription records
make_itemized_caches.py merges ITEMIZED Schedule A/B rows into those caches IN PLACE (wave B2) —
                     the one place the itemization stamp and the pixel->`pct:` geometry
                     conversion happen; never touches the stated-totals half
vision_coverage.py   prints MEASURED coverage of both tranches (quote it, never memory)
build_index.py       regenerates index.csv from the fetch logs (recomputes sha256/format from disk)
backfill_text.py     writes text/ sidecars + text_extraction.csv (pdftotext; --ocr legacy|all)
build_lib.py         shared helpers (office normalization, election-year proxy, donor strings)
RECON.md AVAILABILITY.md PRIVACY.md
```

## index.csv schema
`date, candidate, office, seat, election_year, filing_type, reporting_period, title,
source_url, retrieved_date, format, extraction_method, path, source, document_id, sha256,
filer_type, has_text, has_itemized`.
- `office` ∈ the 10 county offices (normalized from the raw labels — legacy parentheticals like
  "Council #5" / "Council At-Large C" and EasyVote "Salt Lake County …" strings); `seat` carries
  District N / At-Large X.
- `source` ∈ `clerk_legacy` | `easyvote` | `globalassets`. ⚠ `has_itemized` is an **acquisition-time** flag meaning
  "the EasyVote API returned itemized rows for this filing" **as computed at acquisition, under
  the buggy office gate** — it is NOT the test for "does this filing have itemized rows" (wave B2
  itemized the legacy era, and the 2026-08-20 gate repair admitted 33 more EasyVote filings). Use the filing's vision cache
  (`_meta.itemized`) or `source_filing` in `contributions.csv`/`expenditures.csv` instead.
- `election_year` is the **even-year proxy** (see caveats). `format` ∈ text | scanned, measured
  from the actual PDF font layer (never guessed by extension).

## Structured layer — how it was built (READ THIS before quoting numbers)
`build_finance.py` reads the EasyVote **itemized advanced-search JSON** (`raw/easyvote_api/
advancedsearch_{contributions,distributions}.json`) — the genuinely-structured, per-transaction
source, the same data class as `disclosures.utah.gov` — filters to county offices, joins to
`documentsearch.json` for filer/filing metadata, and emits the three CSVs per
`scripts/campaign_finance/SCHEMA.md`. **The PDFs are NOT parsed for the money** (they are
image-only redacted scans); the API JSON is authoritative.

⚠️ **CORRECTED 2026-08-20 — the EasyVote office gate was dropping rows.** This section used to
read *"contributions.csv 4,956 · expenditures.csv 3,278 · filing_totals.csv 164 filings —
$1,905,741 raised / $1,633,769 spent across the 2024 + 2026 county cycles"*. `build_finance.py`
resolved office names ONLY through `raw/easyvote_api/offices.json`, which is a snapshot of
**currently-active** offices; **12 historical `OfficeGuid` values are absent from it**, so every
itemized row keyed to one failed the county-scope test and was dropped with no log line.
Repaired 2026-08-20: office resolution is now **row-level GUID first**, the filing's own metadata
only as a fallback, with the county-scope test applied to the RESOLVED name. GUID-first is
load-bearing — a filer's registered `officename` is their CURRENT registration and lies about
older documents (metadata-first would have pulled 73 school-board contributions into a county
dataset). Full record, proof obligations and before/after diff:
`_audits/2026-08-20-easyvote-office-gate/report.md`. **Zero rows lost; every `stated_*` value
byte-identical; all added rows are Salt Lake County county offices** (Clerk 1,006 C / 133 E ·
Sheriff 115/137 · Auditor 37/37 · Council D5 34/83 · D1 20/12 · At-Large B 4/39 · D3 4/30 ·
Council seat-blank 5/6 · Recorder 2/2 · Surveyor 1/0). **Never treat
`raw/easyvote_api/offices.json` as a complete historical office table.**

- **EasyVote API block: 6,184 contributions ($2,176,360.58) · 3,757 expenditures
  ($2,009,188.50) · 197 filings**, spanning **2022 (26 filings), 2024 (104) and 2026 (67)**.
  ⚠ Those are the API rows ONLY, and they are **rows 1–6,184 / 1–3,757** of the two CSVs; the
  vision-itemized clerk-legacy block is appended after them (whole-file totals: 20,930 / 11,882).
  Filter on `extract_method` (`easyvote_api/json` vs `vision-itemized/…`) before quoting an era.
- **donor_type** (API contrib rows): individual 5,491 · unknown 368 (359 are **blank-donor**
  aggregate/unnamed rows, `needs_review=1`) · candidate-self 141 · family-of-candidate 96 ·
  loan 88.
- **office** (API contrib rows): County Council 3,205 · Clerk 1,270 · Assessor 403 · Mayor 346 ·
  Treasurer 307 · Sheriff 215 · District Attorney 183 · Surveyor 180 · Auditor 71 · Recorder 4.
- **The 26 newly-admitted 2022 filings are an independent cross-validation of the vision method.**
  They already carried vision-transcribed cover totals and gained an itemized half from the API:
  **all 52 sides reconcile EXACTLY** (`recon_delta = 0.00`), including Chapman's $102,508.83 over
  556 rows. A page image read by vision and a born-digital feed agree to the cent. Nothing was
  nudged.

### Caveats — honest limits of the structured layer
1. **No stated (printed) totals ⇒ reconciliation UNKNOWN.** The API returns only itemized rows,
   not each filing's printed "Total Contributions/Expenditures" (those live in the image-only
   PDFs). So `filing_totals` carries `itemized_*` sums with **blank `stated_*` and blank
   `reconciles_*`** — the honest "unknown" state (SCHEMA §4/§6), never a fabricated mismatch. The
   integrity signal here is that the source IS the authoritative structured itemized data.
   `extraction_confidence='high'` reflects a structured (non-OCR) source, NOT a reconciled one.
2. **No in-kind flag in the API.** All itemized rows are plain Contributions/Expenditures, so
   `in_kind=False` on every row. In-kind items (if any) are folded into the itemized list without
   a marker — a source limitation, documented, not inferred.
3. **No donor address in the API** — `donor_city`/`donor_state`/`donor_district` are blank (see
   PRIVACY.md). Blank donor name ⇒ `donor_raw=''`, `donor_type=unknown`, `needs_review=1` (never
   a fabricated name/geography).
4. **`election_year` is an EVEN-year proxy** (`build_lib.election_year_from_date`): county offices
   elect in even years, so a report's cycle = its submission year rounded DOWN to even (odd-year
   filings are overwhelmingly dissolution/final/annual reports of the just-completed race). The
   **office/seat** is the reliable "county race" key, not the exact cycle.
5. **`is_incremental=True`** is set as the EasyVote family default (per-period reports). It was
   **not** empirically re-derived per candidate here (the WJ `derive_is_incremental` refinement is
   a follow-up). **Do NOT naively sum a candidate's `filing_totals` rows** for a cycle total — run
   `scripts/campaign_finance/cycle_totals.py` (dedup-aware) when a per-candidate-cycle rollup is
   needed. `cycle_totals.csv` is not built in this pass (see leads).
6. **ITEMIZED coverage is now EVERY ACQUIRED DOCUMENT.** ⚠️ CORRECTED TWICE. It first read
   *"the 2022 EasyVote docs store only the redacted PDF … so both remain totals-only"*
   (falsified 2026-08-20 by the office-gate repair: **26 of the 123 2022 documents ARE itemized
   from the API**), then *"the 197 API-itemized EasyVote filings PLUS a COMPLETE clerk-legacy
   layer — and NOTHING ELSE"* (falsified 2026-09-01 by waves W1 and W2). The state as of
   2026-09-01: clerk-legacy **496/496** filings with a Summary Page (closed 2026-08-03), the
   2015–2021 paper slice **130/130** (W1, closed 2026-08-23), the API-itemized **197**, and the
   EasyVote residue **238/238** (W2, closed 2026-09-01). Nothing acquired is un-itemized; the
   only gap left is the **251 GRAMA-only online reports** of 2015–2021, which the repo does not
   hold. `vision_coverage.py` prints the live state. **Never infer
   "no donors" from an absent row set** — check the filing's cache: an empty schedule the
   transcriber actually looked at is `sides:"transcribed"` with zero rows (a real zero), a
   schedule that does not exist is `"none"` (40 such sides — 8 of them with a non-zero stated
   total, tabled above as the documented gaps), an unfinished one would be `"withheld"` (**there
   are none left**), and a filing with no `_meta.itemized` block at all was never attempted
   (**there are none left in the queue**).
7. **`filing_totals.csv` mixes SEVERAL provenances now.** Rows 1–171 are EasyVote-JSON itemized
   filings (`extraction_confidence=high`, blank `stated_*`); rows 172–841 are the legacy + 2022
   vision rows, 842–971 the W1 paper slice, and 972–1,112 the W2 EasyVote 2024/2026 covers.
   The vision rows split again: a row from an itemization wave (B2 / W1 / W2) carries BOTH
   sides — the form's printed `stated_*` AND the vision-counted `itemized_*` with a real
   `reconciles_*` verdict — while a totals-only row still has blank
   `itemized_*`/`reconciles_*` (the honest unknown). **97 rows in the 172–841 block gained
   their itemized half in wave W2 and their `stated_*` did not move** (proved field-by-field
   2026-09-01). Filter on the `notes` wave markers (`wave B2`, `wave W1`, `wave W2`), or on
   which side is populated, before comparing.
   **Never sum the vision rows**: interims, year-ends, finals and amendments overlap by design,
   duplicate and mutually-inconsistent filings are common, and at least two filers put
   cumulative figures in Column A. Use `scripts/campaign_finance/cycle_totals.py`.
8. **A `reconciles_*` of `False` on a wave-B2 row is the FILER's arithmetic, not a defect.**
   The stated figure is the form's own printed total and is never recomputed; the itemized figure
   is what the page's lines actually say. Where they disagree the row keeps both and `notes`
   names the cause found on the page — a Schedule total that disagrees with the Summary Page, a
   page subtotal that disagrees with its own rows, in-kind items counted on one side only.

## The vision totals tranche (2026-08-01 → **COMPLETE 2026-08-02**) — stated totals for the two NON-STRUCTURED eras

The legacy clerk PDFs (~2006–2015) and the 2022 EasyVote cycle have **no machine-readable
STATED TOTALS** — the legacy scans' "text" layer is scanner OCR over HANDWRITING (worthless for
figures) and all 123 of the 2022 EasyVote PDFs are flattened images with zero text. Verified
2026-08-01: `pdftotext` returns nothing usable for either era, and the EasyVote
`documentsearch` JSON carries no total fields. **Vision is the only channel for the printed
totals.** (⚠️ narrowed 2026-08-20 — this used to say the two eras have "no machine-readable
money at all". For **26 of the 123 2022 filings** the *itemized* advanced-search JSON does carry
machine-readable rows; it just carries no printed totals. Those 26 rows now attach to the
vision row, which is why 26 vision rows have a populated itemized half.)

So each filing's **cover page + Summary Page** is transcribed by Read-tool vision (Claude Code
allotment, **$0 API**) into `vision/<sha1(index.csv path)[:8]>.json` — the repo-standard cache
key (`scripts/campaign_finance/vision_lib.cache_key`). **Totals only this tranche; the itemized
Schedule A/B lines are NOT transcribed.**

**The form is one form, 2006 → 2022.** Page 1 = cover (candidate / Office Sought / District /
the checked "Type of Report" box / amendment flag / signature date); page 2 = "Summary Page"
with Column A "Total this Period" and Column B "Sum Total to Date" (later "Aggregate Total"),
lines 1–7. That stability is what makes one transcription contract cover both eras.

### Cache schema (a SUPERSET of the standard vision cache, so a later itemization tranche can
fill `contributions`/`expenditures` in place without a schema change)
```jsonc
{ "contributions": [], "expenditures": [],          // empty — itemization deferred
  "total_contributions": "...", "total_expenditures": "...",   // Summary Page line 1 / line 2, Column A
  "beginning_balance": "...",   "ending_balance": "...",       // line 3 / line 7
  "aggregate": { "total_contributions_to_date", "total_expenditures_to_date", "line5_subtotal" },
  "cover": { "candidate","party","office_sought","district_number","report_type",
             "is_amendment","amendment_of","report_date","form_year" },
  "confidence": { "<field>": "high|medium|low" },   // per field, only where a value was read
  "_meta": { "index_path","era","tranche","candidate","office","election_year","source_pdf",
             "pages_read","render","summary_page_found","transcription_method",
             "transcribed_by","transcribed_date","notes" } }
```
- `"transcribed_by"` names the WAVE: `"vision-transcribed(claude-opus-5; 2026-08-01 totals
  tranche)"` for the first 114, `"vision-transcribed(claude-opus-5; 2026-08-02 totals tranche,
  continuation)"` for the remaining 556.
- **Every value is VERBATIM as printed** (`"$1,735.79"`, `"7,500.00"`, `"($11,592.46)"`).
- **THREE distinct states, and they mean different things** — a **string** = printed;
  **`""`** = the field exists and the filer left it BLANK; **`null`** = printed but
  **ILLEGIBLE**, or the field does not exist in that document. `null` never becomes `0`.
- Nothing is computed in the cache or the build: Line 7 is never derived from Lines 5−6,
  Column B is never filled from Column A, and no total is ever summed by us.

### How it reaches `filing_totals.csv`
`build_finance.py::build_totals_tranche()` emits ONE row per legacy / 2022 filing and
**APPENDS** them after the EasyVote-JSON rows. Rules:
- `stated_total_contributions` / `_expenditures` = Summary Page **Column A** lines 1 / 2;
  `stated_beginning_balance` / `_ending_balance` = lines 3 / 7. Column B is preserved
  verbatim in `notes` (there is no schema column for a to-date figure).
- `itemized_*`, `reconciles_*`, `recon_delta_*` stay **BLANK** — there is no itemized side to
  reconcile against this tranche. That is the honest unknown, never a fabricated mismatch.
  `n_contrib_rows` / `n_expend_rows` are `0`.
- `reporting_period` = the **form's own checked report-type label**, which OUTRANKS the clerk
  listing-page label (GOTCHAS: portal/listing labels lie — and they demonstrably do here, see
  below); the listing label is kept in `notes` whenever the two disagree. `filing_type` is the
  derived class (`interim` / `year-end` / `final` / `summary`; `''` when no box is checked)
  that `cycle_totals.py` reads.
- `election_year` and `filing_date` are filled from the form **ONLY where index.csv is blank**
  — an acquisition-time value is never overwritten (27 and 22 fills respectively).
- `office` is taken from the form's own "Office Sought" only where the clerk listing label did
  not already normalize to one of the 10 county offices.
- `document_id` = index.csv's id where it exists (EasyVote GUID), else the vision cache key —
  the legacy channel has no id of its own, so the cache key IS the stable per-filing id.
- **Currency repair**: handwritten forms sometimes use a decimal COMMA (`"1920,00"`). Read
  naively that is a 100× fabrication, so figures pass through the SHARED whitelisted repair
  (`common.repair_money_line`) before parsing; a 3-digit trailing group (`"2,500"`) is still
  thousands, and anything it cannot make unambiguous stays blank. Repaired values are named in
  the row's `notes` (2 so far).
- `extraction_confidence` is **capped at `medium`** — SCHEMA §6 reserves `high` for a
  born-digital/structured source, and a page image read by vision is the OCR tier. An
  illegible stated total, or a transcriber `low` flag, drops the filing to `low`.

### Coverage of this tranche — **COMPLETE 2026-08-02** (regenerate with `python3 vision_coverage.py`)
| era | filings | stated totals transcribed | no Summary Page in the doc | not yet transcribed |
|---|---|---|---|---|
| clerk_legacy ~2006–2015 | 547 | **496** | 51 | **0** |
| EasyVote 2022 cycle | 123 | **122** | 1 | **0** |
| **total** | **670** | **618** | **52** | **0** |

The tranche ran in two waves — 114 filings on 2026-08-01, the remaining **556 on 2026-08-02**
(18 disjoint chunks of ~32). `_meta.transcribed_by` records which wave produced each cache;
`make_vision_caches.py --transcribed-by/--transcribed-date` is how a wave stamps itself.
**Every filing in both non-structured eras now has a vision cache — the queue is empty.**

- **Text-parsed: ZERO.** Both eras are image-only (measured, see above) — every figure here is
  vision-read. The **52** "no Summary Page" filings are honest non-existence, not extraction
  failure, and they are a richer set than the first wave suggested: the single-page
  **"Dissolution of a Candidate Campaign" notice** (the bulk), the one-page **"Small Budget
  Campaign Certificate"** (SLCo Ord. 2.72A.204.5 — a filer under the threshold certifies instead
  of reporting; no dollar figures exist on it at all), printed **email threads** asking the clerk
  to close an account, plain letters, cover-sheet-only scans, and **six structurally damaged or
  blank PDFs** (below). Their totals are `null` by non-existence.
- **Illegible/absent stated fields: 216** across the 670 caches — **208 are fields that do not
  exist** on those 52 documents, and exactly **8 are true illegibility** on a real Summary Page:
  `jhatch_sept152006.pdf` (all four — Schedule A sheets were scanned on top of the summary
  table), `sharmsen_10_FinalDis_CntyCncl1.pdf` (lines 2 and 7, a degraded fax with a black smear,
  re-rendered at 600 dpi and cell-cropped before being left null), `ltopham_jan3107report.pdf`
  line 1 Column A, and `Sherrie-Swensen__56E26BA7.pdf` line 3. **2,440** fields carry a printed
  value; **24** were left blank by the filer.
- Filing-level confidence: **610 `medium`, 8 `low`**, 52 blank (no Summary Page to grade) —
  vision is capped at `medium`. Per-FIELD transcriber confidence: high 5,132 / medium 374 / low 33.
- `filing_type` derived from the form's own checked box: **interim 371 · year-end 167 · final 84**;
  48 filings check **no box at all** (honest `''`, never guessed).
- Money observed across the 618 (period Column-A figures; **NEVER sum these across filings** —
  interims, summaries and amendments overlap by design): **$9,636,827.12** contributions /
  **$8,993,843.15** expenditures.

**Six source files are damaged or blank at the file level** (all re-verified against
`index.csv` sha256 — our copies are intact, the defect is upstream at `slco.org`):
`jauger_61906amendment.pdf` and `20_june_cannon_russ06.pdf` (broken xref; **re-fetched
2026-08-02 and byte-identical to the stored copy**, so re-acquisition is exhausted),
`nhendricks_sept152006.pdf` and `jhatch_sept152006.pdf` (broken xref, Summary Page absent or
overprinted), `lreberg_sept152006.pdf` (page 1's lower two-thirds destroyed by an expenditure
listing printed over it), and **`dwilde_apr52006.pdf` — a completely blank 4-page scan**
(pixel range 251–255 on every page, nothing recoverable even contrast-stretched). The Wilde
April-2006 report is the one filing that would benefit from a fresh clerk request.

### What the transcription found (source properties, not defects)
1. **The clerk reused the 2020 form template through the 2022 cycle** — most 2022 EasyVote
   filings are titled "**2020** Financial Disclosure Report". `cover.form_year` records the
   printed title verbatim; it is NOT the cycle. Some 2022 filings do use a "2022" title, so
   both appear in the same cycle.
2. **Listing labels disagree with the forms, repeatedly** — e.g. a filing listed
   "Sept 10, 22 Amend" whose form checks *September 15* and marks itself NOT an amendment; two
   listed "June report" whose forms check *April 5*. The form wins; the label is kept in notes.
3. **Amended/overlapping filings are common and mutually inconsistent.** One 2022 sheriff filer
   has five April-5/September-15 reports printing materially different Column-A totals
   ($68,605.79 vs $38,236.42 vs $31,019.37 for overlapping periods). All are kept verbatim.
   **This is exactly why `filing_totals` must never be summed** — run `cycle_totals.py`.
4. **Internal inconsistencies are retained, never reconciled** — a form whose Line 2
   ("$23,40") disagrees with its own Line 6 ("$422.35", with the Line-2 figure struck through);
   a Line 7 struck out and rewritten in the margin; a negative closing balance printed in
   accounting parentheses; Column B smaller than Column A.
5. **A mislabeled document was caught**: one legacy filing indexed under *Deanna L. Taylor* is
   in fact **Diane Turner's** dissolution. Transcribed from the form and flagged, per the
   riverton-Pierucci precedent (never transcribe a document under a label it contradicts).
   Likewise `richardson_05finalreport.pdf`, whose FINAL REPORT box is *not* checked (the
   January-31 year-end box is) — the filename is not the report type.
6. **The 2008-era form has TWO office boxes** (a top-row "Office" and a separate "Office
   Sought"); where "Office Sought" was blank the top-row value is recorded as `office_sought`
   and the substitution is stated in that filing's note.
7. **Clerk-side corrections appear on the page**: one filing (`10168c6b`) is a web-printed
   slco.org variant whose two printed Column-B `$0.00` cells were struck through by hand and
   replaced with `$17,951.97` / `$15,079.26`, initialled 1/29/07 — the handwritten values are
   the ones transcribed, with the strike recorded.
8. **Many filers write cents as a raised superscript over a rule** (`19875` ⁸⁵). Those are
   transcribed with a decimal point and the convention is noted per filing; where a superscript
   runs off the cell edge the value is kept partial at `low` confidence rather than completed.

Wave 2 (the 556) confirmed all of the above at scale and added:

9. **The listing label lies at a MEASURABLE rate, and always in the same direction** — the clerk
   listing calls a filing "Final"/"Summary"/"Dissolution"/"Amend" where the form checks only
   Year-End, or checks no amendment box at all. Dozens of cases across every chunk. `filing_type`
   comes from the form; the listing label is kept in `notes`. **A `_final`/`_dissolution`
   filename is not evidence of a final report.**
10. **48 filings check NO "Type of Report" box at all** — several of them amendments that carry
    only the "Yes, this is an amendment" tick, with the period identifiable solely from
    `amendment_of`. `filing_type` is honestly `''`; do not infer a period from the filename.
11. **Two more form VARIANTS exist beside the standard report**: the **"Small Budget Campaign
    Certificate"** (a one-page under-threshold certification with no figures) and a **"Summary
    Page — Other Campaign Accounts"** page whose Column B header is "Year to Date". Two filings
    carry the *Other Accounts* page INSTEAD of the standard Summary Page; where that happened the
    figures were either left `null` (`bf8a4533`) or recorded with the substitution stated loudly
    in `notes` (`ee4789b4`). They are not interchangeable tables.
12. **Column A does not always mean "this period."** At least two filers (DeBry 2022, Gill
    2007) put the PRIOR CUMULATIVE total in Column A lines 1–2 while the real period figures sit
    in lines 4/6. Their `stated_total_*` are therefore not comparable to other filers' — a
    per-filer semantic, recorded verbatim and flagged, never normalized.
13. **Column B is unreliable across the corpus** — routinely `$0.00` against a five-figure
    Column A, sometimes smaller than Column A, sometimes not advancing between filings, and in
    one case identical for contributions and expenditures ($488,558.50 both sides). Kept
    verbatim; treat the aggregate column as filer-asserted, not as a computed running total.
14. **Filer arithmetic breaks on the page often enough to be a property, not an anomaly** —
    Line 7 ≠ Line 5 − Line 6 by cents to hundreds of dollars, Line 5 ≠ Lines 3 + 4, Line 2
    disagreeing with Line 6. Roughly two dozen instances, each retained verbatim with the
    discrepancy named in `notes`. **Nothing was ever reconciled or recomputed.**
15. **Pages are frequently out of order or bundled** — the Summary Page turns up on PDF page 3,
    4, or 8; reports arrive stapled to bank statements (17 pages of them in one case),
    QuickBooks exports, or a dissolution notice. Renders beyond page 2 were used wherever
    page 2 was not the Summary Page.
16. **More mislabels caught, per the riverton-Pierucci precedent** — a filing whose filename says
    "12Mayor" is in fact **James M. Winder, Sheriff**; one indexed *Robert L. Warnick* is signed
    **Robert W. Warnick**; two manifest `election_year`s (2020, 2030) are filename mis-parses of
    2006 and 2013 forms. Transcribed from the form, flagged in `notes`.
17. **Filer date typos survive verbatim**: amendment-of dates printed `2222-03-31` and
    `2222-04-04`, a Summary Page self-dated "Sept 15 2015" on a 2014 filing, a report signed
    "11-28-08" that checks October 28. Never silently corrected.
18. **Duplicate filings exist that are not amendments** — page-for-page identical pairs with
    different md5s, and "amendments" whose Summary Page is byte-identical to the original
    (propagated errors included). Another reason `filing_totals` must never be summed.

## The ITEMIZATION tranche — wave B2 (2026-08-02) — WHO gave, and to whom

The totals tranche answers *how much*. This one answers **from whom** for the clerk-legacy era,
and it is the first structured donor layer that has ever existed for these filings — the
transactions live only as handwriting on a 2006-era scan.

**Scope: clerk-legacy filings that HAVE a Summary Page.** A document with no Summary Page has no
Schedule A/B either (dissolution notices, Small Budget Campaign Certificates, letters, the six
damaged/blank PDFs — 51 of them), so they are out of scope by non-existence, not skipped. The
2022 EasyVote cycle is **not** in this tranche. ⚠️ **CORRECTED 2026-08-20** — the reason given
here used to be *"its PDFs are flattened redacted images and its schedules are redacted"*. The
PDFs are flattened images, but **the schedules are NOT redacted**: the county's black bar covers
only the donor ADDRESS column, never a name, date or amount, which is why the 2026-08-20 residue
audit classified **zero** sides as withheld and found **89 of the 97 row-less 2022 filings carry
readable itemized detail**. The 2022 cycle is simply UNTRANSCRIBED — see "The EasyVote row-less
residue" below. Coverage is measured, never recalled: `python3 vision_coverage.py`.

### Coverage — the queue is CLOSED. MEASURED 2026-08-03 (`python3 vision_coverage.py`)
| | |
|---|---|
| clerk-legacy filings **with** a Summary Page (the queue) | **496** |
| **itemized** (214 wave-B2 + 24 promoted pilot + 256 residue + 2 residue-close) | **496** |
| **still queued** | **0** |
| clerk-legacy filings with **no** Summary Page (out of scope by non-existence) | 51 |

**Rows: 14,746 contributions + 8,125 expenditures = 22,871.** 9,709 (42.5%) carry `verified=1`
(re-read in a tight higher-dpi band and identical); 22,748 rows `medium` confidence, 123 `low`
(vision is capped at `medium` per SCHEMA §6); **21 amounts blank for illegibility** across 22,871;
1,758 rows carry `needs_review=1`, overwhelmingly dates the form prints **without a year**.

**Reconciliation, per SIDE:** contributions 427 exact · 39 delta-with-cause · 204 unknown;
expenditures 428 exact · 41 delta-with-cause · 201 unknown. **Zero sides withheld** — the last two
(below) were finished 2026-08-03, so no side in the corpus is abandoned mid-read. "Unknown" means
the form states no total for that side, or the side is `none`; it is never a fabricated mismatch.
**All 80 deltas are traced to the filing itself** and named in the row's `notes` (a Schedule total
disagreeing with the Summary Page, a page subtotal disagreeing with its own rows, in-kind counted
on one side only, or Schedule pages physically missing from the county's scan, where the side is
labelled a FLOOR).

**44 filings are real zeros** (both schedules present and blank) and **40 sides are `none`** (no
such schedule page exists in the document). 819 tight-crop escalations were used, and a
page-subtotal gate is recorded on 472 of 496 filings.

### The last two sides — closed 2026-08-03 (wave "B2 residue close")
Wave B2 left exactly two CONTRIBUTION sides `withheld`, both for agent capacity and neither for
illegibility: `simgill_oct312006.pdf` and `McAdams_B_12_Oct_Mayor_Redacted.pdf`, whose Schedule A
in each case is a typed LANDSCAPE spreadsheet attachment (p7–p15 and p4–p18). Both are now
transcribed — **985 rows** — and both closed on a gate the withholding agent had not found:

* **Neither attachment prints per-page subtotals**, and on both filings the county's own
  Schedule A form says "See Attachment" with its SUBTOTAL/TOTAL cells blank. The usable gate is
  the **attachment's own printed grand total on its last page**.
* `McAdams`: 631 rows sum to **$258,816.71 exactly** = the export's printed grand total (foot of
  p18) = the Summary Page figure. `result=exact`.
* `simgill`: 354 rows sum to **65,294.91 exactly** = the attachment's printed grand total (foot of
  p15), against a Summary Page stating **65,294.94**. The residual **$0.03 is the filer's own
  arithmetic between his attachment and his summary**, not a misread digit — both figures are
  retained verbatim and the side is `delta`. The predecessor's `withheld_reason` had asserted that
  "the only gate available for that side is the Summary Page figure"; that was wrong, and the
  attachment total is what localises the three cents.
* A second, INDEPENDENT gate was used on McAdams: each page's data-row count was measured by
  rule-detection (`_backups/2026-08-02-tranche3/slco-b2/rowbands.py`, calibrated against ten
  hand-counted pages) and matched the transcription on **15 of 15 pages**. A row-count gate
  catches a dropped or duplicated line that a sum can hide.
* The predecessor's estimate of "~387 rows" for simgill (from counting text runs in the amount
  column) **overcounted**: the true grid is 41 rows/page × 8 + 26 = 354.

### Documented gaps in the itemized layer — 8 sides, 5 filings
These are sides where the filing STATES a non-zero total but **contains no schedule page at all**
(`sides.<side>="none"`), so there is nothing to transcribe. Honest non-existence, never a zero:
**$121,789.32 contributions + $120,455.49 expenditures**. Four of the eight are exactly reproduced
by an itemized SIBLING filing for the same period, so the donor/vendor detail does exist in the
corpus — the other four are not reproduced by any sibling.

| filing | side | stated | sibling covers it? |
|---|---|---|---|
| `Romero_R_12_Final_Amended_Mayor_Redacted.pdf` | expenditures | $64,174.00 | YES — `Romero_R_12_Final_Mayor_Redacted.pdf`, 99 rows, exact |
| `Romero_R_12_Final_Amended_Mayor_Redacted.pdf` | contributions | $23,055.00 | YES — same sibling, 48 rows, exact |
| `Romero_R_12_April_Interim_Amend_Mayor_Redacted.pdf` | contributions | $45,042.12 | YES — `…_April_Interim_Mayor_Redacted.pdf`, 125 rows, exact |
| `BrunerM2014AprilAmendment.pdf` | expenditures | $1,284.49 | YES — `BrunerM_2014_April.pdf`, 8 rows, exact |
| `08_rhoriuchi_september152008.pdf` | expenditures | $54,843.80 | no (sibling amend sums 54,843.81 — 1¢ off) |
| `08_rhoriuchi_september152008.pdf` | contributions | $52,100.00 | no (sibling amend sums 42,100.00 — $10,000 short) |
| `Romero_R_12_April_Interim_Amend_Mayor_Redacted.pdf` | expenditures | $50,828.01 | no (sibling sums 50,171.61) |
| `rcannon_apr52006.pdf` | expenditures | $153.20 | no — the only other Cannon scan is one of the six DAMAGED PDFs |

The **six damaged/blank source PDFs** are a separate, earlier gap and are NOT itemization gaps:
five of them (`jauger_61906amendment`, `20_june_cannon_russ06`, `nhendricks_sept152006`,
`lreberg_sept152006`, `dwilde_apr52006`) have no Summary Page and so were never in this queue;
the sixth, `jhatch_sept152006.pdf`, IS in the queue and WAS itemized (29 + 11 rows) despite its
four illegible stated totals. See "Honest gaps" below.

### Where the rows live
Each filing's rows go into its EXISTING `vision/<key>.json` — the `contributions` /
`expenditures` lists that the totals tranche deliberately shipped empty — plus a
`_meta.itemized` block recording sides, reconciliation, page-subtotal gates, escalations and the
wave stamp. `make_itemized_caches.py` is the only writer; it never touches the stated-totals
half, and it is idempotent. `build_finance.py` then emits the rows into `contributions.csv` /
`expenditures.csv` **appended after** the EasyVote-JSON block (which stays byte-identical) and
fills each filing's `itemized_*` / `reconciles_*` / `recon_delta_*`.

### The per-row contract (why these rows can be trusted, and exactly how far)
* **Full-page first read at 200 dpi**, every page of the filing rendered and classified — a
  schedule total has turned up on page 3, 4 and 8, and a previous wave lost a total by stopping
  at the page it expected.
* **Escalation is a TIGHT CELL CROP at 600–1200 dpi, never a bigger full page.** The Read tool
  downsamples to ~2000 px, so a "600 dpi" full-page render is ~185 effective dpi and reproduces
  the misread it was meant to settle (GOTCHAS, proven 2026-08-02).
* **The page-SUBTOTAL gate.** Where a page prints `SUBTOTAL FOR THIS PAGE`, the rows transcribed
  from that page must sum to it, and a page that will not gate is reported with BOTH figures
  named rather than nudged into agreement. This gate is what settles ambiguous digits: it caught
  a `597.36`-vs-`897.36` on Olds 2008 and it is the method that adjudicated the pilot's Allen
  "Home Depot" digit.
* **Filing-level reconciliation** against the stated total already in `filing_totals.csv`.
  `stated_*` is the form's printed figure and is NEVER recomputed; the vision figure governs
  what the lines say; a residual delta is the filer's arithmetic, retained verbatim and named.
* **Field-shift screen** before each side is finalized — amounts can sum EXACTLY while the name
  and date columns are systematically wrong (the `wasatch-field-shift` specimen), so sum-level
  agreement is never accepted as proof of correct columns. A side whose columns cannot be
  assigned is WITHHELD, not guessed.
* **Dates are strict.** A range, two dates in one cell, a missing year, or an impossible day is
  BLANK + `needs_review=1` with the verbatim in the row note — a year is never filled in from
  the report date. A well-formed filer TYPO is the opposite case and is kept verbatim.
* **Zero-glyph ruling, decimal-comma repair, superscript cents** exactly as the totals tranche
  (GOTCHAS + the two calibration specimens); a malformed decimal is unparseable-blank, never
  repaired, and never has a clean prefix lifted out of it.
* **Privacy: `donor_city` / `donor_state` only.** Street addresses and PO boxes are discarded at
  read time and never written anywhere. A county-redacted address block is honestly blank, and
  the note distinguishes *redacted* from *left empty by the filer* — different facts.
* **`geometry`** is `pct:x,y,w,h@p<page>` (SCHEMA §2a) — percentages of the page, resolution-
  independent, resolvable to a cropped snippet by `scripts/campaign_finance/make_snippet.py`. It
  is a provenance pointer, never a value.

### Honest states — four different things, never conflated
| state | means |
|---|---|
| `sides.<side> = "transcribed"` + rows | the lines were read |
| `sides.<side> = "transcribed"` + ZERO rows | the schedule page exists and is **BLANK** — a real zero |
| `sides.<side> = "none"` | the document has no such schedule — non-existence, not zero |
| `sides.<side> = "withheld"` + `withheld_reason` | could not be finished or columns could not be assigned — **no rows, no sum claimed** |
| no `_meta.itemized` at all | the filing is still QUEUED — never attempted |

### The 24 promoted pilot filings
The opus pilot (`_audits/cf-calibration-suite/pilot-opus/`) transcribed 24 filings under the same
gates before B2 began; they were promoted rather than redone, stamped
`_meta.itemized.wave = "opus pilot … PROMOTED into wave B2"`. Three carry deltas the pilot
proved to be filer arithmetic (Allen +89.00, Jensen +600.00, McAdams −0.02). Their geometry is a
**pilot ESTIMATE converted to `pct:`**: render-back spot-checks found portrait boxes row-exact
(3 of 3 sampled) but one rotated page (`08_jwinder_jan31.pdf` p3) off by eight row-pitches, and
55 rows of `20_june_auger_janice06.pdf` overflow their frame and are marked `geometry_fit:
"clamped"`. Treat a promoted row's box as a page/section pointer; wave-B2 rows carry
transcriber-emitted `pct:` boxes.

### How to REBUILD or EXTEND the itemization tranche (the queue is enumerable at any moment)
**The clerk-legacy queue is CLOSED — `wave_stats.py --residue` prints nothing.** This section is
now a rebuild/extension recipe, not a resume recipe. ⚠️ The extension targets, restated
2026-08-20 (this line used to name "the 2022 EasyVote cycle and the 2016–2021 WAF era"):
~~**(1) the 245 row-less EasyVote filings**~~ — **DONE 2026-09-01, wave W2** (238 transcribed
+ 2 school-board out of scope; 18,240 rows + 141 covers; working set
`_backups/2026-08-24-slco-w2/`, close-out `_backups/2026-09-01-w2-closeout/`; the sizing plan it
worked from is `_audits/2026-08-20-easyvote-residue/classification.csv`);
~~**(2) the 130 paper-filed 2015–2021 PDFs**~~ — **DONE 2026-08-23, wave W1** (see
AVAILABILITY.md; its working set at `_backups/2026-08-23-slco-w1p2/` was the model W2 followed,
being the SLCo wave that transcribed stated totals and itemization in ONE pass);
**(3) the 251 GRAMA-only online reports — THE ONLY TARGET LEFT**, once obtained. It has an
inventory in `_recon/2026-08-20-portal-probe/`.

Wave B2's working set is preserved at `_backups/2026-08-02-tranche3/slco-b2/`:
`queue.csv` (the 472 filings the wave opened with), `chunks/chunk_NN.csv` (disjoint assignments),
`records/chunk_NN.json` (the raw transcription records — **one record per filing; each declares
its own `wave`, so the stamp is reproducible from the records and not from a CLI flag**),
`AGENT_BRIEF.md` (**the per-row contract verbatim — hand this to any agent that continues the
work**), `screen_records.py` (the QA screen that gates a record before it is materialized),
`checkpoint.py` (the append-only invariant guard), `wave_stats.py` (the measured numbers this doc
quotes), `rowbands.py` (rule-detection row banding for landscape spreadsheet attachments — gives
a per-page ROW-COUNT gate and exact `pct:` geometry) and `assemble_residue.py` (how the final two
sides were built). `records/_superseded_*.json` files are retired in-progress saves kept as
provenance; a leading `_` makes both the screen and the materializer skip them.

⚠ **Re-materializing the whole records directory is safe ONLY because each record carries its own
`wave`.** An earlier re-run of `make_itemized_caches.py` without that field silently re-stamped
256 residue-wave caches with the default wave string. If you add records, set `wave` on them.
```
python3 _backups/2026-08-02-tranche3/slco-b2/screen_records.py            # must PASS first
python3 make_itemized_caches.py _backups/2026-08-02-tranche3/slco-b2/records
python3 build_finance.py
python3 _backups/2026-08-02-tranche3/slco-b2/checkpoint.py                # append-only held?
python3 ../../scripts/campaign_finance/validate_finance.py .
python3 vision_coverage.py                                               # what remains
```
The remaining queue is DERIVED, never a hand-kept list: it is every clerk-legacy cache with
`summary_page_found` and no `_meta.itemized` block (`wave_stats.py --residue` prints it). So a
resumed wave cannot double-transcribe a filing, and an interrupted one loses nothing that was
saved. **Materialize + rebuild + checkpoint after EVERY chunk** — the checkpoint asserts the
EasyVote 2024/2026 block is byte-identical and that no already-itemized filing ever shrinks.

### The stated-totals tranche is COMPLETE — how to redo it
All 670 caches exist. To rebuild from the preserved raw transcription records
(`_backups/2026-08-01-county-acquisition/salt_lake_county-cf-vision/records/` — the 18 wave-2
chunk files plus `_all_records_merged.json`):
```
python3 make_vision_caches.py <dir of raw transcription records> \
    --transcribed-by "vision-transcribed(claude-opus-5; 2026-08-02 totals tranche, continuation)" \
    --transcribed-date 2026-08-02
python3 build_finance.py                                           # rebuild (additive)
python3 ../../scripts/campaign_finance/validate_finance.py .
```
(That tranche's successor, ITEMIZATION, is the wave-B2 section above; it drops into the same
caches, which is why they shipped with empty `contributions`/`expenditures` lists.)
A transcription record is `{key, index_path, pages_read, summary_page_found, cover{}, totals{},
confidence{}, notes}` — the `key` MUST equal `sha1(index_path)[:8]` (make_vision_caches hard-fails
otherwise; a record's `index_path` must come from index.csv, **never retyped from memory** — that
mistake was made and caught by exactly this check during the first pass).

Page renders are disposable and regenerate in ~1 min for the whole corpus:
`pdftoppm -jpeg -r 150 -f 1 -l 2 <raw pdf> <workdir>/<key>` — pages **1 and 2** are enough for
~98% of filings (cover + Summary Page); render further pages only when page 2 is not the
Summary Page. Watch the zero-padding: poppler emits `<key>-1.jpg` for a <10-page PDF and
`<key>-01.jpg` for a longer one. `python3 vision_coverage.py` prints exactly which filings
remain. Chunk ~30–45 filings per transcription agent (page images are context-heavy) and give
each agent DISJOINT filings.

**Method notes from the 556-filing wave (worth reusing for the itemization tranche):**
- **Render at `-r 110`, escalate per-cell.** 110 dpi keeps ~32 filings inside one agent's
  context; the reliable move for a doubtful figure is re-rendering that ONE page at 250–600 dpi
  (and cropping with `-x/-y`) rather than raising the base resolution. Agents did this on
  roughly one filing in four, and it is what kept true illegibility down to 8 fields in 2,680.
- **Have each agent re-save its whole record file every ~8 filings.** The first attempt at this
  wave was killed mid-flight and lost 6 agents' work; with incremental saves a kill costs at
  most 8 filings. Page renders are disposable, transcriptions are not.
- **Materialize + rebuild after every chunk** and assert the 2024/2026 structured block is
  byte-identical each time (`contributions.csv`, `expenditures.csv`, and rows 1–171 of
  `filing_totals.csv`) — the tranche is APPEND-only and any drift there means a bug.
- **Merge records with a dedupe pass before materializing.** Agents sometimes leave their own
  staging files beside the canonical `chunk_NN.json`; `make_vision_caches.py` hard-fails on a
  duplicate key, so collapse to one record per `index_path` first (canonical file wins).

## The 2015–2021 PAPER slice — wave W1, QUEUE CLOSED 2026-08-23

**130 of 130 filings · 717 pages · 6,028 rows (3,422 C + 2,606 E) · 0 withheld · 0 amounts blank
for illegibility.** Measured coverage, reconciliation, money, geometry and the ten source
properties this slice established are in `AVAILABILITY.md` §"The 2015–2021 PAPER slice" — read
there, and regenerate counts with `python3 vision_coverage.py`, never from memory.

The three things a reader of THIS file most needs:

### 1. `donor_occupation` starts here (⚠ no longer ONLY here — corrected 2026-09-01)

The county's 2015–2021 Schedule A pre-prints an **Occupation/Employer** column that the
~2006–2015 clerk-legacy form does not have. Captured verbatim under the owner decision of
2026-08-20 as a trailing-optional column (SCHEMA §2c) on `contributions.csv` and
`gov.db.cf_contribution`. **2,292 of this slice's 3,422 rows carry one.** Within this slice a
blank is one of **three** facts — no such column, filer left it empty, or redacted at source —
and each row's note says which. Three filings split the cell into two attachment columns; both
halves are composed with `" / "` (484 rows).

⚠ **This section used to say the paper slice was the ONLY source of the column. Wave W2
falsified that on 2026-09-01**: the EasyVote county grid prints Occupation/Employer too, and
most filer attachments carry Organization + Title, so **10,225 W2 rows populate it** and the
module total is **12,517**. NULL elsewhere in the repo still means *the form has no such
field*, never "no occupation".

### 2. The reconciliation SCOPE TEST must be run PER PAGE

Six filings print a schedule total and a Summary figure that **measure different things** — in
one direction (the schedule includes in-kind rows the Summary excludes) and in the other (the
schedule's `TOTAL (Sum of subtotals from all pages)` cell holds the CYCLE-CUMULATIVE figure while
`SUBTOTAL FOR THIS PAGE` holds the period one). On some filings **Summary Column A is ALSO
cumulative**, with the true period figure only at lines 4/6. **The same filer flips convention
between his original and his amendment**, so the test is per PAGE, not per filer or per filing.

Those 5 filings ship with `reconciles_*` and `recon_delta_*` deliberately **BLANK** under the
`SCHEDULE-SCOPE SPLIT` marker in `notes`, both printed figures published verbatim — comparing
figures of different scope is a basis error, not a delta. This is the same answer utah's
`cumulative-exact` sides get, and it required **no weakening of `validate_finance.py`**.
`build_finance.py::apply_itemized` implements it with two tests (the record anchored on a
different FIGURE; the record anchored on a different LINE) and deliberately lets a same-scope
filer disagreement fall through to a real published delta. Gating naively would have fabricated
**>$180,000** of deltas across six filings.

### 3. Two corrections to the 2026-08-20 harvest report

* **The "split filing" is a DUPLICATE SCAN.** `_audits/2026-08-20-globalassets-harvest/report.md`
  §3 records `2020_…_burdick-fin-report-3.pdf` as a bare Schedule B whose other half is
  `…amendment-burdick-fin-report-9-15-20_redacted.pdf`, "paired on the 9-15-20 report date".
  Verified at the page: the sibling is a **complete 4-page report on its own**, and the bare sheet
  is a **second scan of that same Schedule B** — identical rows, dates, amounts, printed grand
  total 9,533.28 and the identical stray diagonal pencil line, differing only by one pixel row in
  the embedded raster (which is why the harvest's sha256 check called all 130 distinct).
  **Summing the pair double-counts $9,533.28.** Generalises: in a scanned corpus, `sha256`-distinct
  is not document-distinct.
* **One privacy flag names the wrong document.** `characterisation.csv` puts "UNREDACTED
  contributor address cell" on `2015_…_jim_bradley2015ye.pdf`, whose cell holds only a workplace
  descriptor; the genuine unredacted residential address is on
  `2015_…_jim-bradley-amendment---redacted.pdf`, despite its `_redacted` filename.

⚠ **And one finding the harvest could not have seen:** `2020_…_staggs-mayor_redacted.pdf` — the
corpus's one born-digital document — has a **COSMETIC redaction**: black bars drawn over an intact
text layer, 40,598 extractable characters and **156 ZIP-shaped tokens against exactly 156
contribution rows**. Nothing was extracted and no address token from it exists anywhere in this
repo. It is a defect in the COUNTY'S publication, raised for owner decision at
`_backups/2026-08-23-slco-w1p2/OWNER_DECISION_PRIVACY.md`.

## The EasyVote residue — wave W2, QUEUE CLOSED 2026-09-01

**245 of the 442 EasyVote documents carried no itemized rows.** The repo could not previously say
whether that meant "no itemizable activity" or "the detail is in the document, untranscribed".
It was overwhelmingly the latter, and it is now transcribed. Audit that sized it:
`_audits/2026-08-20-easyvote-residue/README.md` +
`classification.csv` (one row per filing, classified per SIDE). **240 of the 245 were read — all
1,719 pages, rendered and looked at.** (The 5 not in the cohort are Fife-Jepperson filings whose
covers read *Salt Lake School Board* while `index.csv` labels them County Council — out of county
scope, flagged in `index.csv`, not relabelled, per the riverton-Pierucci precedent.)

### What W2 delivered (measured 2026-09-01; regenerate with `python3 vision_coverage.py`)

The queue was **DERIVED, never hand-kept**: every EasyVote filing whose `document_id` has no
rows in the advanced-search API (ungated, so a school-board filing whose rows exist but fail
the county-office gate is excluded here too). That is **240 filings = 238 transcribed + 2
ledgered OUT OF SCOPE** (`FIFE-JEPPERSON-CHARLOTTE__AE07FEF8` / `__D20522DA`, whose **Office
Sought** line reads "Salt Lake School Board" — re-verified at the cover 2026-09-01). ⚠ The
classification field is **Office Sought**, not the top-row **Office**: her 2026 filing
`__B5AB014E` has Office = "Salt Lake City School Board District 2" (her sitting seat) but
Office Sought = "**Salt Lake County Council District 2**", and it is correctly IN scope.

| | |
|---|---:|
| filings in the derived queue | **240** |
| transcribed | **238** |
| out of scope (school board) | **2** |
| remaining | **0** |
| rows published | **18,240** (11,852 C + 6,388 E) |
| geometry (`pct:`) | **100%** |
| new covers read (`filing_totals` 971 → 1,112) | **141** |
| filings whose 2022 cover already existed and gained an itemized half | **97** |

**Per SIDE (240 × 2 = 480): 359 exact · 33 delta-with-cause (traced to a named page) ·
82 `none` (no such schedule page) · 2 unknown (no anchor exists in the document) ·
4 out-of-scope. ZERO withheld.** 234 of the 238 have a Summary Page; 4 do not (a Small Budget
Campaign Certificate, a dissolution notice, and two cover-only documents).

**78 contribution amounts are blank BY SOURCE, never by omission**: 77 on
`Wilson-Jennifer__B5D1F91C.pdf`, whose county redaction bar spans the **Amount** column on
pp.3 and 6 (verified at the page 2026-09-01 — the bar runs Address→Amount inclusive while
Date, Name, Employer and Occupation survive), so that side is a documented **FLOOR**:
$114,980.00 readable against a stated $161,699.85; and 1 on `Wilson-Jennifer__CE8EF5B5.pdf`
where the filer printed no amount for Loralee Rees. **This is the only place in the SLCo
corpus where the county's bar takes a MONEY column** — everywhere else it takes only address.

**Provenance.** W2 is the **first non-Claude transcription federated into `gov.db`**. Rows carry
`extract_method = 'vision-itemized/W2 EasyVote residue (2026-08-24; kimi-k3)'`; 658 of the
18,240 say `; chunk resumed 2026-08-24 by claude-opus-5` (three chunks whose agents died on a
provider 403). Cover rows carry the tranche stamp `ReadMediaFile vision (Kimi K3); 2026-08-24
wave W2 (EasyVote residue)`. The wave was **verified before federation** by an independent
Claude session (2026-09-01): all module gates re-run, byte-identical rebuild, the pre-wave
frozen blocks proved unchanged field-by-field, and four filings across the ledger tiers re-read
at the page. Working set + close-out: `_backups/2026-08-24-slco-w2/`,
`_backups/2026-09-01-w2-closeout/`.

⚠ **`donor_occupation` is NO LONGER paper-slice-only.** The EasyVote county grid prints an
Occupation/Employer column and most filer attachments carry Organization+Title, so **10,225 of
the W2 rows populate it** (module total 12,517). Composition order is
`occupation / employer`, verbatim.

⚠ **Some W2 expenditure amounts are NEGATIVE as printed** — Morris-Rachelle's five bank/ledger
exports and Liewer `585D94D0` print every debit with a minus sign. The sign is kept **verbatim**
per the never-correct-the-filer rule; reconciliation is on **MAGNITUDE**, and
`filing_totals.itemized_expend_sum` is published POSITIVE. A consumer summing
`expenditures.amount` for this module must take `abs()`. The convention is not new — the
clerk-legacy McAdams/Winder rows already did this.

### What the audit found before the wave (kept — it is the record of the corpus)

| cycle | audited | `has-attachment-detail` | `empty-schedule` | `no-schedule-page` | `withheld` | `undetermined` |
|---|---:|---:|---:|---:|---:|---:|
| 2022 | 97 | **89** | 4 | 4 | 0 | 0 |
| 2024 | 91 | **76** | 2 | 13 | 0 | 0 |
| 2026 | 52 | **32** | 2 | 18 | 0 | 0 |
| **all** | **240** | **197** | **8** | **35** | **0** | **0** |

**The recoverable class: 197 filings, ~18,433 lines over 980 pages** (11,972 C + 6,461 E; 2022
8,820 · 2024 8,142 · 2026 1,471). ⚠ **That row total is an ESTIMATE, and must always be quoted
as one.** Its basis: **14,397 rows counted line by line** + **1,489 numbered by the filer's own
spreadsheet** (~86% real counts) + **2,547 `approx`** — dense uniform grids measured on sampled
pages and extrapolated at a fixed row pitch. `classification.csv`'s `c_count_basis` /
`e_count_basis` name the basis per side. Concentration is extreme: the largest 10 filings hold
roughly a third of the rows, and the 60 largest would recover well over half.

**143 of the 240 have NO `filing_totals` row at all** — all 91 audited 2024 filings and all 52
from 2026. No itemized rows, no stated totals, no vision cache: they exist only as a PDF plus an
`index.csv` row. The 2022 cohort by contrast has complete stated totals from the 2026-08-02
tranche. **A wave here owes stated totals for those 143 as well as itemization.**

**What a wave must know before it starts** (each measured, not assumed):
- **Detail sits in THREE structural places, not one.** 62% of has-detail sides are typed or
  handwritten **directly onto the county's own Schedule A/B grid**; a second group is a filer
  attachment behind a blank county stub ("See Schedule A attached"); and a third has **no county
  schedule page at all** — the filer's own sheet simply IS the schedule. **A wave keyed on
  finding a "See Attached" stub will silently miss the third class** (well over a thousand rows).
- **Attachment layouts are filer-stable across cycles** — 63 distinct filer slugs collapse to 19
  field-set families once column order and synonyms are normalized, and four families cover 110
  of the 138 attachment sides. Per-filer calibration transfers.
- **Geometry anchoring outlook is good:** 185 of 197 have printed gridlines; 178 print their own
  SUBTOTAL/TOTAL line (a real page- or side-level gate on top of the Summary figure). **19
  filings have no printed gate at all** (~4,290 rows; `subtotals=0` in the CSV) — for those a
  row-count gate (rule-detection banding) is the second independent check. 28 of 197 are
  handwritten; the rest are typed or printed.
- **Reconcile against the SUMMARY figure, not the schedule's grand total.** A recurring class —
  roughly a quarter of has-detail filings — has the schedule's printed grand total sitting below
  Summary line 1/2, and the cause is uniform and benign: **the page subtotals exclude In-Kind
  rows the schedule nonetheless lists.** Reconciling against the schedule total will manufacture
  false deltas on dozens of filings. Name the class `schedule-total-vs-summary-gap`.
- **Two mechanical traps:** rotated attachments stored 90° inside the PDF (Harrison E5C37303
  pp.8–14, Morris) must be rotated before rendering; and one attachment (Liewer p9, a bank
  export) **runs off the bottom of the page mid-row** — 26 visible debits sum to $8,142.97
  against a stated $8,316.61, so $173.64 of lines never printed. That is a real ceiling, not a
  zero.
- **Donor geography will NOT survive.** The county's black bar covers the itemized rows' address
  column on **157 of the 197**; on the county grid a single "Complete Mailing Address" cell holds
  city, state and ZIP, so all of it goes, and on attachments with separate columns one wide bar
  routinely spans all four. **Exactly 3 filings preserve any geography** (`Robinson-Zach__7022E201`
  ZIP, `Robinson-Zach__C4162BAF` street-only redaction, `Pinkney-Natalie__07C097D5` state/ZIP/
  country). A row's note must say **redacted at source**, never "left blank by the filer" —
  different facts. The bar never covers a donor name, date or amount, which is why **nothing is
  `withheld`**. Occupation/Employer almost always survives.
- **`doc_kind`:** 237 standard reports, 3 one-page Small Budget Campaign Certificates. **There
  are NO one-page dissolution notices in this cohort** — every document titled
  "Dissolution"/"Final" is the full standard form with that box checked. That is the opposite of
  the clerk-legacy era, where the standalone notice is the bulk of the no-Summary-Page class.

**Three sides contradict their own stated total; all three were re-read at the page.** Two are
genuine gaps: `Snelgrove-Richard__CE0A4B74` (2024 Recorder, Final/Dissolution — $3,261.09
expenditures stated, the 2-page filing has **no Schedule B page**, and being the final report no
sibling can cover it) and `Ahn-Danielle__23F2E34E` (2022 District Attorney — $11,868.21 stated,
Schedule B present and wholly blank; the sibling `__43FA92A0` itemizes ~30 rows totalling
$11,008.96, the clerk-legacy `Romero` partial-sibling pattern). The third,
`Creno-Tracey__E28B702C`, is **NOT a gap but a basis inversion** — the filer put the
cycle-cumulative figure in lines 1/2 and the period figure in lines 4/6, the same per-filer
semantic already documented for DeBry 2022 and Gill 2007 (finding 12 above). Period activity is
$0 in / $1,500 out and is fully itemized.

**The audit also re-read the 2022 stated totals blind and compared them to the caches: 191
comparable sides, ZERO disagreements.** The 2026-08-02 vision tranche's Column-A figures hold.

**Other things the audit established about the corpus** (source properties, worth carrying):
`index.csv` form-year is not the cycle **at scale** (~25 filings across 2022/2024/2026 print a
"2020 Financial Disclosure Report" cover; one 2026 filing uses the 2019 form — already known for
2022, it runs through 2024 and 2026 too); and **the 2026 form family is not one form** —
"Financial Disclosure Report **For an Open Campaign Account**" and "…**For a Candidate**" are both
live in that cycle, with different Type-of-Report option sets and different Column-B semantics.

## Honest gaps
- **2015–2021 — NOT ACQUIRED, and it is TWO gaps with two different routes.** ⚠️ CORRECTED
  2026-08-20; this bullet used to read *"the county disclosure portal is WAF-blocked (BigIP: every
  scripted request 302-loops … under any UA/TLS/cookie/delay) … Recover via the `claude-in-chrome`
  browser skill against the live portal (a real browser session may pass the WAF; the
  `/Report/{id}` pattern + archived folder inventory make it turnkey)."* **Wrong twice.** The
  application behind the load balancer is **DEAD, not defended** — the LB discriminates by PATH
  (every app-pool path RSTs at a flat ~0.23 s; every other path gets a clean catch-all 302), real
  Chrome over CDP gets `ERR_CONNECTION_RESET`, an unrelated source IP gets `read ECONNRESET`, and
  Wayback's last HTTP-200 capture is **2026-01-15**. And the report route is
  **`/Search/PublicSearch/Report/{id}` (ids 1069–2104)**, not `/Report/{id}` — the old 404 was on
  a non-route and was never evidence about the reports. What is actually true:
  - ✅ **The 130 paper-filed county-office PDFs are ACQUIRED AND TRANSCRIBED** — harvested
    2026-08-20 from `saltlakecounty.gov/globalassets/…/financial_disclosure/…` and CLOSED
    2026-08-23 by wave W1 (130/130 filings, 717 pages, 6,028 rows, 0 withheld). Full record:
    "The 2015–2021 PAPER slice" in `AVAILABILITY.md`. All three phase-1 shape warnings proved
    real and are now handled: the **Occupation/Employer** column has a home (`donor_occupation`,
    SCHEMA §2c, owner decision 2026-08-20); **folder-year labels lie** (two 2018 documents sit in
    `2016_disclosures/september/`, confirmed at the form); and **page 1 is not always a cover**
    (three documents bundle another document in front, one of them behind a near-blank ghost
    page). ⚠ The fourth warning — "a filing can be split across several PDFs" — **was WRONG**:
    the one cited case is a DUPLICATE SCAN, not a split (see the corrections below).
  - **251 online-filed reports exist only in the dead portal, were never archived, and are
    GRAMA-only.** Inventory with the Wayback folder URL proving each filing exists:
    `portal_online_reports_inventory.csv`. Ask for the export, not for 251 printouts.
  - **The two slices are COMPLEMENTARY** — 34 of the 54 portal filers have no clerk-page PDF at
    all, while the filers with rich PDF sets have zero online reports. Harvesting the 130 does
    **not** make the GRAMA unnecessary. Evidence: `_recon/2026-08-20-portal-probe/NOTES.md`.
- **Image-only text.** Every EasyVote redacted PDF and every legacy PDF is effectively
  image-only for VALUES: the 123 legacy PDFs that `index.csv` marks `format=text` carry a
  scanner-embedded OCR layer over **handwritten** 2006-era forms, so the pre-printed labels
  extract but the figures are garbage. Treat `format=text` in this dataset as "has a font
  layer", NOT as born-digital (the riverton precedent). Full text sidecars for the scans are
  still deferred; the tranche transcribed **stated totals only** (above).
- **ALL THREE ERAS ARE CLOSED (2026-09-01).** Stated-totals coverage is COMPLETE for every era
  that has a Summary Page, and ITEMIZATION is COMPLETE for the clerk-legacy era (496/496 filings
  with a Summary Page, 2026-08-03), the 2015–2021 paper slice (130/130, wave W1, 2026-08-23) and
  the EasyVote era (197 from the API + 238/238 of the row-less residue, wave W2, 2026-09-01) —
  every such filing carries real Schedule A/B lines or an explicit, reasoned `none`/zero.
  The residual honest gaps INSIDE the layer are the 8 clerk-legacy `none` sides tabled above
  ($121,789.32 contributions + $120,455.49 expenditures stated but no schedule page filed, 4 of
  the 8 reproduced by an itemized sibling), the 82 EasyVote `none` sides, and the
  **Wilson `B5D1F91C` redaction floor** (77 amounts blacked out at source).
  ⚠️ CORRECTED THREE TIMES. It once read *"The 2022 EasyVote cycle and the 2016–2021 WAF gap
  have no itemized layer at all"* (falsified 2026-08-20 by the office-gate repair), then
  *"unanswerable for 2016–2021"* (falsified 2026-08-23 by wave W1), then *"only partly
  answerable for 2022–2026 — 245 EasyVote filings are still row-less"* (falsified 2026-09-01 by
  wave W2). So "who gave to whom" is now answerable for **every document the county holds**; it
  is unanswerable ONLY for the **251 GRAMA-only online reports** of 2015–2021.
- **52 filings have no Summary Page and therefore no totals** — dissolution notices, Small Budget
  Campaign Certificates, letters/emails, cover-only scans, and six damaged/blank PDFs. Honest
  non-existence, carried as `null`, never zero.
- **Six source files are damaged or blank at the file level, upstream at `slco.org`** —
  `jauger_61906amendment.pdf`, `20_june_cannon_russ06.pdf`, `nhendricks_sept152006.pdf`,
  `jhatch_sept152006.pdf`, `lreberg_sept152006.pdf`, and the wholly blank `dwilde_apr52006.pdf`.
  All six were verified byte-intact against `index.csv` sha256, and the two xref-broken 2006
  files were **re-fetched 2026-08-02 and came back byte-identical** — re-acquisition from
  `slco.org` is exhausted. A GRAMA request to the Clerk is the only remaining route.

## Rebuild
```
python3 make_vision_caches.py  _backups/2026-08-24-slco-w2/records  # W2 covers (skips
                             #   itemization-only records; their caches already exist)
python3 make_itemized_caches.py _backups/…/records   # (only when new itemized records exist)
python3 build_finance.py     # structured CSVs from raw/easyvote_api/*.json + ALL vision tranches
python3 backfill_text.py --ocr legacy   # text/ sidecars (born-digital + legacy OCR)
python3 build_index.py       # index.csv from the fetch logs
python3 vision_coverage.py   # MEASURED coverage of every tranche incl. the W2 section
python3 ../../scripts/campaign_finance/validate_finance.py .   # conformance
```
`build_finance.py` is **deterministic** — a rebuild off unchanged caches reproduces
`contributions.csv` / `expenditures.csv` / `filing_totals.csv` **byte-for-byte** (verified
2026-09-01). After any rebuild, re-run the county cycle reducer
(`python3 ../../scripts/campaign_finance/cycle_totals_county.py salt_lake_county`) and then
`python3 ../../scripts/build_cities_db.py` — **adding filings without re-running the reducer
leaves the documented cycle counts stale** (standing rule, 2026-08-24).
⚠ `cycle_totals_county.py` has NO `--help`: a bare or unrecognized-flag run REGENERATES ALL
EIGHT COUNTIES. That is deterministic and safe, but do not expect usage text.
Re-fetch: EasyVote via the `ecf-api.easyvoteapp.com/advancedsearch/{contributions,distributions}/
D2EEAA9C-E9BF-4B77-AC5E-2A6F379D1775` recipe (browser UA required — 403 to Python-urllib);
legacy via the URLs in `raw/clerk_legacy/_fetch_log.jsonl`.

## OUT OF SCOPE (leads only — see AVAILABILITY.md)
- **Local school boards** (clerk `…/local-school-board/` + EasyVote) — a disjoint office set.
- **Metro Township Councils** — the clerk `…/metro-township-councils/` page has **297 redacted
  PDFs** (Millcreek/Magna/Kearns/Copperton/Brighton/Emigration/White City, mostly 2016) + 57
  EasyVote filings (2023/2026). May close the **kearns cf-blocked-cycles** caveat and enrich
  magna/white_city/copperton/emigration_canyon/millcreek city CF.
