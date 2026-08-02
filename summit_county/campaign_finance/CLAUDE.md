# campaign_finance/ — Summit County COUNTY-OFFICE candidate financial disclosures

Additive module, as-of **2026-08-01**. Does **not** modify any existing `summit_county/` dataset
and is **not** federated into `gov.db` (no build step touches the entity db). It completes the
**elections → officeholders → votes** chain for the county tier: who funded the candidates whose
County Council roll calls live in `../legislative/` and whose wins are certified in
`../elections/`.

**Money layer as of 2026-08-02: STATED TOTALS (all 131) + the BORN-DIGITAL ITEMIZED LAYER
(11 of 131).** All **131** cover pages were vision-transcribed (Read-tool method, `$0` API) and
`filing_totals.csv` carries each filing's own printed contribution / expenditure /
ending-balance figures. The **15 born-digital filings** were then parsed by the registered
`summit_form` family (TRANCHE 3 Phase A, 2026-08-02): **105 contribution + 386 expenditure rows
over 11 filings**, every emitted side reconciling to the cent against the published stated
total. **The 116 SCANS remain unitemized** — that is *not transcribed*, **never** *no donors*,
and their `reconciles_*` stay blank by design.

## What this is

**131 campaign financial reports** filed by Summit County **county-office** candidates for the
**2014, 2016, 2018, 2020, 2022, 2024, 2026** cycles — County Council (seats A–E, districts 4–5
from 2026), Attorney, Auditor, Clerk, Sheriff, Assessor, Recorder/Surveyor, Treasurer. 74 distinct
candidate-cycles. Each is the Summit County Clerk's **"CAMPAIGN FINANCIAL REPORT"** form under
**Utah Code 17-16-6.5** (cover box + `ITEMIZED CONTRIBUTION REPORT` + itemized expenditures).

**Coverage is complete against the source:** every one of the 56 county candidates on a Summit
ballot 2014–2026, and all 38 general-election winners 2014–2024, has ≥1 report here. That is a
**candidate-level** claim, not a candidate-CYCLE one: the county itself published nothing for
**Michael Howard's 2022 County Auditor run** — its Financial Reports page prints the verbatim
string `County Auditor: Michael Howard n/a n/a`, `n/a` in **both** the Pre-Election and
Post-Election columns (re-verified 2026-08-02 in the retained capture
`raw/index_pages/536_Financial-Reports_2026-08-01.html`). Nothing was withheld and nothing failed
to download — **no report exists**, and it is logged in `unrecovered.csv` + `listed_gaps.csv`, never
imputed as a zero. (Howard's own 2014 and 2018 filings are here, which is why he still satisfies
the candidate-level claim.) Coleen Reardon's 2022 row prints the same `n/a n/a` against her
Pre-/Post-Election cells, but she filed a Primary report, which is held.

School-board and municipal filings are **out of scope** — different statutes, different forms.
See `AVAILABILITY.md` → "Out of scope (with leads)".

## Layout

```
raw/2014/ 2016/ 2018/ 2020/ 2022/ 2024/ 2026/   the filing PDFs, named <docid>_<orig-slug>.pdf
raw/_fetch_log.jsonl        per-object provenance (url, http status, bytes, sha256, retrieved_utc)
raw/index_pages/            the listing pages this was built from (live capture + 5 Wayback
                            captures of the predecessor host) + their own _fetch_log.jsonl
text/                       one .txt sidecar per filing (pdftotext -layout, or tesseract)
index.csv                   DERIVED — one row per filing
unrecovered.csv             DERIVED — honest gaps (see below)
state_sweep.csv             the negative-result ledger for disclosures.utah.gov (34 folders)
listed_gaps.csv             CURATED — gaps that are stated on the page, not inferable from files
text_extraction.csv         which tool produced each sidecar (build input for extraction_method)
batch/manifest.json         the acquisition manifest (build input; candidate→url→file→sha256)
office_overrides.csv        CURATED — document_id,office,seat,evidence (read by build_index.py)
vision/<sha1(path)[:8]>.json  CURATED — the cover-page transcription of every filing (131)
filing_totals.csv           DERIVED — one row per filing, SCHEMA.md §4 contract
cover_totals.csv            DERIVED — module-local: ALL THREE cover columns, verbatim
contributions.csv           DERIVED — SCHEMA.md §2 + trailing `geometry`; born-digital only (105)
expenditures.csv            DERIVED — SCHEMA.md §3 + trailing `geometry`; born-digital only (386)
backfill_text.py            rebuilds text/ + text_extraction.csv
build_index.py              rebuilds index.csv + unrecovered.csv
build_finance.py            rebuilds filing_totals/cover_totals/contributions/expenditures
RECON.md                    the channel survey + the label traps (read this before re-probing)
AVAILABILITY.md             sources checked, coverage matrix, gap ledger
```

## `index.csv` — the columns that matter

Required §9 minimum (`date,title,source_url,retrieved_date,format,extraction_method`) plus:

| column | meaning |
|---|---|
| `date` / `date_basis` | **proxy only** — the PDF's own CreationDate, kept only when its year matches the cycle year (99 of 131; blank otherwise). `date_basis='pdf_creation_date (proxy)'`. The statutory due date is printed inside the form; read the raw PDF. |
| `candidate` | filer name in natural order. |
| `office` / `seat` | canonical office + seat (`A`–`E`, or `4`/`5` for the 2026 district naming). **Blank = unresolved, never guessed** (0 rows since the 2026-08-01 vision pass resolved Walter Brock). |
| `office_source` | how the office was established: `filing_text` (the filing's own "Office Filed For" line, the primary source) > `portal_listing` > `elections_join` (surname+year against `../elections/`) > `override:<evidence>` (2 — the Brock rows, from `office_overrides.csv`) > `unresolved` (0). |
| `election_year` | even-year county cycle. |
| `reporting_period` | `Pre-Election` / `Post-Election` / `Primary` / `Pre-Primary` / `Final` / `Withdrawn` / `Out at Convention` / `Out at Primary` / `Appointment Report`. |
| `filing_type` | `statement` (all). |
| `format` | `scanned` (116) / `text` (15) — measured from the **raster-image probe**, not the file extension and not "does it have a text layer" (69 scans carry a scanner-produced OCR layer). |
| `extraction_method` | `pdftotext -layout` (15 born-digital) / `embedded OCR text layer (pdftotext -layout)` (69 — the **clerk's scanner** OCR'd it, not this repo) / `tesseract OCR (pdftoppm 300dpi)` (47). |
| `text_quality` | `high` 89 / `medium` 22 / `low` 20 — does the **sidecar** contain the filer's surname AND ≥2 legible money tokens. `low` ⇒ **no machine-readable numbers in the text layer**. ⚠ This is a property of the OCR, **not of the document**: the 2026-08-01 vision pass read a legible cover box on 19 of the 20 `low` rows. For the money figures use `filing_totals.csv`; `text_quality` only tells you whether `text/` can be grepped. |
| `needs_review` | `1` (42) when `text_quality != high` or the office is unresolved. |
| `channel` | `county_live_page` (69) / `delisted_live_by_id` (62 — 2014/2016/2018 objects the listing dropped but the CMS still serves). |
| `listing_url` | the page (live or Wayback) the link was read from. |
| `matched_election_candidate` / `join_confidence` | join to `../elections/election_results_by_contest.csv` — `surname+year` (107) / `none` (24: primary- or convention-eliminated filers and the still-open 2026 cycle, who never reach a certified general contest). |
| `sha256` / `bytes` / `document_id` / `path` / `text_path` | integrity + addressing. `document_id` is the CivicPlus DocumentCenter id — stable, and the key to re-fetch. |

## `filing_totals.csv` + `cover_totals.csv` — the stated-totals layer (2026-08-01)

**Read this before quoting any dollar figure.**

### The column trap — the one thing this module exists to get right

Summit's cover box runs **`Current Report | Last Report | Cumulative Totals`** — the **REVERSE**
of the sheet the shared parsers assume (Millcreek prints `LAST | THIS | CUMULATIVE`). The 2024
sheet renames the middle column **`Previous Report`**; the ORDER never changes. A parser that
takes "the second-to-last money token" reads Summit's **Last Report** column and is silently
wrong. Measured proof, on `20765` (Langston 2022 Post-Election, born-digital): printed
contributions **$503.00**, printed expenditures **$511.62** — `millcreek_form` and `ogden_form`
both return **511.62 as "total contributions"** (RECON.md §4).

Because of that, **every one of the three cells is captured verbatim and labelled**:
- `vision/<sha1(path)[:8]>.json` holds the cover box cell-by-cell under its printed column name.
- `cover_totals.csv` republishes the same thing as a flat CSV (one row per cover row per filing,
  451 rows), with `col1/col2/col3_label` + `_verbatim` and the verbatim
  `candidate_as_printed` / `office_verbatim` / `party_verbatim` / `signature_date_as_printed`.
- `filing_totals.csv` carries the ONE promoted figure per side, with the promotion basis written
  into `notes`. **Any promotion can be audited against `cover_totals.csv` without reopening a PDF.**

**The column assignment was independently re-verified on 2026-08-02** by a session that
re-rendered and re-read the PDFs from scratch: **17 filings across all 7 cycles and all 5 form
variants, zero transpositions**, every verbatim cell matching the page and every promotion
following the rule below. The sample table, the three confirmed money-cell corrections, and the
one thing the audit *did* find (a systematically under-captured signature date, now repaired) are
recorded in AVAILABILITY.md → "Independent re-verification, 2026-08-02".

Verbatim-cell vocabulary (revised by the 2026-08-02 zero-glyph ruling): **`"Ø"` = the filer
wrote a slashed zero — promotes to 0.00**; **`""` = the cell was EMPTY on the form or held a
dash nil mark** — an honest blank, never a zero. **`ILLEGIBLE` (cache `null`) = a value is
present but could not be read** — never guessed (**5 cells**, listed under "Coverage + honest
gaps"). ⚠ The pre-ruling convention conflated Ø with `""`; the audited filings' caches now
carry `Ø` verbatim, but un-audited `""` cells in NON-promoted columns (Current/Last cells that
never feed a total) may still be either — only cells that affect promoted figures were
re-classified at the page.

### The promotion rule (deterministic, documented, never repairs a value)

Per cover row, in order:
1. **`cumulative`** when that cell holds a parseable amount.
2. **`current`** when the cumulative cell is empty or illegible.
3. **`current`/`previous`** when the cumulative cell parses to **zero** on a contributions or
   expenditures row whose Current or Previous cell is non-zero — the cumulative cell then
   contradicts its own row and is the fillable template's default `$ 0.00` (or Excel zero-dash)
   left in place. Proven on the file: Hanson's 2024 Pre-Election sheet (`24237`) prints `$0.00`
   cumulative against `640.86` current, and her Post-Election sheet (`24381`) carries `640.86`
   through **both** the Previous and Cumulative columns. Never applied to the balance row.
4. otherwise **blank** + a note. A blank stated total is an honest gap, never a zero.

On the pre-2022 sheet contributions are split across **two** printed lines (donors `>$50` and
donors `<=$50`); `stated_total_contributions` sums **only the lines actually printed** (the juab
precedent) and `notes` says so when one part was blank.

### Form variants (all three keep the same column order)

| variant | cycles | shape |
|---|---|---|
| `split50` | 2014–2018, and some 2022 filers | "CAMPAIGN FINANCIAL REPORTS (Utah Code 17-16-6.5)"; contributions split `>$50` / `<=$50` |
| `single_total` | 2018–2024 | "<YEAR> CAMPAIGN FINANCIAL REPORT"; one `Total contributions` row, address/phone block |
| `single_total_2024` | 2024 | boxed layout; middle column renamed **`Previous Report`** |
| `single_total_2026` | 2026 | adds a `Name of Office` box + City/State/Zip; county pre-redacts addresses |
| `narrative_letter` | 1 filing (`1273`, David Ure 2014 Post-Election) | **not the form at all** — a handwritten one-page letter with its own printed totals and NO column box |

The variants **overlap**: Martinez filed the old `split50` sheet in 2022 (`20638`) while everyone
else used the 2022 sheet. Never infer the variant from the cycle — read `form_variant`.

### Coverage + honest gaps in this layer

131 filings transcribed. **128** carry a stated contribution figure, **131** a stated expenditure
figure, **128** a stated ending balance. `extraction_confidence`: **high 116 / medium 15**.

- **ZERO-GLYPH RULING (owner, 2026-08-02).** A glyph that DENOTES the digit zero — a slashed
  zero `Ø`, `-0-`, or the written word "zero" — transcribes as **0** (it is the filer writing
  zero); a bare dash, `N/A`, or an empty cell stays BLANK. The coordinator re-rendered every
  blank-stated-cell filing at FULL page and classified each mark: **7 cells across 6 filings
  held deliberate slashed zeros and now carry 0.00** (Clyde 2020 ×2 + Francis 2020
  contributions; Francis 2020 + Olson 2022 + Siddoway 2022 + Poll 2024 balances — caches
  record the verbatim `Ø` with the audit note). Siddoway's own sheet even prints the county's
  instruction "DO NOT DELETE ANY CELLS WITH $0.00".
- **3 filings state no contribution total at all** — Rhonda Francis 2018 ×2 and Dallin
  Donaldson 2024 ×1: their contributions row is verified **genuinely empty on the form**
  (full-page re-read 2026-08-02; they filled only an expenditure cell). **Blank, not zero.**
  Welch 2024's balance row holds an untouched "Type text here" AcroForm placeholder — also a
  genuine blank.
- **5 individual cells are `ILLEGIBLE`** — struck-through or over-written figures. The two that
  matter: Murphy 2022 Pre-Election (`20640`) cumulative expenditure is genuinely ambiguous between
  `$3733.22` and `$3738.22` (his own Post-Election sheet, `20766`, prints `3733.22` in its Last
  Report column — recorded as evidence in the cache, **not** back-filled into `20640`); and
  Franchek/Frendelc 2022 (`20650`/`20751`) whose Current contributions cell is a struck-out figure.
- **Filer arithmetic is retained exactly as filed and is often wrong.** Documented per filing in
  `notes`: Howard's 2014 expenditures are printed **negative**; Adair's 2016 cumulative expenditure
  is printed negative; Ioannides' 2024 sheets carry three typography errors (`23,744,71` with a
  comma decimal, `23.744.71` with a period thousands separator, and a cumulative `32,744.71`
  against a current `23,744.71`); Welch 2024 states a balance that does not follow from his own
  rows; Forsling 2024 repeats the expenditure figure in the balance row.
- **6 rows have a blank `filing_date`** (125 of 131 carry one). `filing_date` in this layer is the
  **form's own printed signature date**, normalised to ISO; the `index.csv` `date` proxy (PDF
  CreationDate) is **never** substituted for it. ⚠ This was **51 blanks until 2026-08-02**: the
  original transcription rendered page 1 cropped to the top 80%, which cut the date line off most
  sheets. The 2026-08-02 verification pass re-read all 51 at full page, recovered **45**, and
  corrected one misread date (`23015` 4/10/24 → 4/18/24) — see AVAILABILITY.md → "Independent
  re-verification". The remaining 6 are genuine: `1273` (narrative letter, no date line), `8192` /
  `20752` / `20634` (line left empty), `8397` (filer wrote `12/8` with **no year** — verbatim in
  the cache, never completed), `20651` (illegible photocopy). Two retained oddities: `23014` is
  dated `2/5/2023`, before its own cycle, and `27204` wrote `June 7th 2026`.

### Do NOT sum, and other query rules

- **Never sum a candidate's filings.** Summit's reports are **cumulative snapshots** — a
  cycle total is the *latest* report's promoted figure, not a sum. (`cycle_totals.csv` is
  deliberately NOT built here; see "Not built".)
- **Two 2026 rows are the same document.** `26742` (Appointment Report) and `27210` (Primary) are
  the identical Malena Stevens sheet published twice. Do not double-count.
- Several 2014–2024 filers **re-filed their Pre-Election sheet unchanged** as the Post-Election
  report (Robinson, Wright, Jones, Olson, Francis, Armstrong, Larsen, Welch, Poll). Identical
  figures across two rows are the source's behaviour, not a duplication bug.

## Join to the rest of `summit_county/`

- **To elections:** `matched_election_candidate` → `../elections/election_results_by_contest.csv`
  on **person + year** (election names are UPPER-CASE with a party token — normalize).
- **To Council votes:** a winner's roll calls are in `../legislative/all_votes.csv` /
  `db/summit_county.db`. ⚠ Remember the entity ceiling: **Summit Council minutes are
  tally-primary** — only 23 of 1,831 Council motions carry named votes, and the Council coverage
  floor is **2023-01**. So a money↔vote analysis is only possible for the **2022 and 2024**
  cohorts, and mostly at the tally level. Don't promise per-member vote–donor correlation here.
- **PC commissioners are appointed, not elected** — they file nothing and must never be joined to
  these rows.

## Caveats / do-nots

- **Cover-page totals ARE transcribed for all 131; donor itemization exists for the 15
  BORN-DIGITAL filings only.** Use `filing_totals.csv` / `cover_totals.csv` for any dollar
  figure — **never** the `text/` sidecars of a SCAN, which are OCR of handwriting and mis-anchor
  exactly the way the shared parsers do. On the 116 scans `contributions.csv` /
  `expenditures.csv` hold nothing and `reconciles_*` is blank **by design**.
- **Do not sum filings per candidate.** Reports are **cumulative snapshots**, so a cycle total is
  the *latest* report's promoted figure, never a sum.
- **Portal labels lie — three verified cases**, all corrected from the filing text and recorded in
  `RECON.md` §3: Dawn Mathiesen Langston 2022 renders under `County Auditor:` but filed for
  **County Clerk**; Michael Howard's 2018 row contains a stray anchor to **Margaret Olson's**
  Final report (dropped); Colin DeFord 2016 is listed surname-first without a comma.
- **Some forms carry no header at all.** Ari Ioannides' two 2024 sheets (`24231`, `24382`) have
  EMPTY `Full Name of Candidate` / `Office Filed For` / `Party` boxes, and Margaret Olson's 2026
  sheet (`27205`) has an empty `Name of Office` box. For those rows the candidate/office in
  `index.csv` come from the **county portal listing, not from the document** — the cache's
  `candidate_as_printed` / `office_verbatim` are blank and say so.
- **The county pre-redacts the 2022 and 2026 filings** (black-marker addresses/phones on the
  published PDFs) — inconsistently: Harte's, Keyes' and Robinson's 2022 Pre-Election copies are
  redacted while their Post-Election copies are not. That is the publisher's behaviour, retained.
- **`format` is not `has a text layer`.** 69 scans arrive pre-OCR'd by the county's scanner. The
  index distinguishes that from born-digital and from this repo's own tesseract pass.
- **`date` is a proxy.** Never present it as the statutory filing date.
- **Seat letters are not stable across time.** Summit used Council **seats A–E** through 2024 and
  **districts 4/5** in the 2026 cycle. Join on person, not seat.
- **This module is not in `gov.db`.** Nothing here federates; no `build_cities_db.py` run is
  implied by rebuilding it.

## Not built (deliberate)

- **No donor/expenditure itemization for the 116 SCANS.** Their `ITEMIZED CONTRIBUTION REPORT`
  and itemized expense pages are untranscribed — a much larger vision job (most run 3 pages of
  handwriting), and Phase B work. Until it runs, those filings carry no itemized row and no
  `reconciles_*` value may be asserted for them. The 15 born-digital filings ARE itemized (see
  the section below).
- **No `cycle_totals.csv`.** The shared `scripts/campaign_finance/cycle_totals.py` dedup contract
  assumes an itemized layer and a per-candidate incremental/cumulative determination. Summit is
  uniformly cumulative and the rollup is a one-line query over `filing_totals.csv` (latest report
  per candidate × cycle) — a derived file would only add a contract this data does not need yet.
- **No `donor_aliases.csv` / `finance_overrides.csv`.** Nothing yet warrants either; the
  corrections that were needed went in `office_overrides.csv` (the index's own sanctioned path).
- **No `gov.db` federation.** The repo's `cf_*` tables are city-scoped. Nothing here federates.

## The BORN-DIGITAL itemized layer (built 2026-08-02, TRANCHE 3 Phase A)

`contributions.csv` (105 rows) / `expenditures.csv` (386 rows) cover **11 of the 15
born-digital filings**, parsed by the now-REGISTERED `summit_form` family. Measured:

| | count |
|---|---:|
| born-digital filings handed to the family | **15 of 131** |
| contribution sides reconciling exactly → shipped | **4** |
| expenditure sides reconciling exactly → shipped | **11** |
| rows emitted | **105 contributions · 386 expenditures** |
| rows carrying `geometry` | **491 of 491 (100%)** |
| rows flagged `needs_review=1` | 6 (2 privacy-guarded names + 4 field shifts, below) |

**TWO gates, both mandatory.** The family drops the printed TEMPLATE EXAMPLE rows (`Jon and
Jane Doe` / `Name of Business` — on Langston that is exactly the 938.00 − 435.00 = 503.00
difference) and refuses any section whose rows do not sum to its own printed total
(`EMIT_UNRECONCILED=False`). This module then applies a SECOND gate: a family-approved section
must also sum to the figure THIS module publishes, or it does not ship. Nothing was withheld by
the second gate — the two agree on every filing.

**What the gates refused, and why (each named in `filing_totals.notes`):**
- **Canice Harte 2026 (27200)** — the contribution ledger is **PERIOD-scoped** (rows sum to
  **1,000.00**, the *Current* column) under a **CUMULATIVE** cover (**1,109.63**). Publishing
  those rows against a cycle total would state an incoherent pair, so the side is **WITHHELD**
  with both figures named. The expenditure side of the same filing reconciles and ships.
- **The wrapped-2014 sections** (Shumway, Howard, Coleman, Williams, both Martinez filings,
  Ioannides 2024) — a long contributor name wraps across up to four laid-out lines, which drops
  the row's money off the row's line; the section is short and is refused rather than published
  as complete. A silently-short donor list is worse than none (`RECON.md` §4).

**Two module-local guards on the family's output** (the shared engine is FROZEN this tranche,
so neither is a patch — both are documented in `filing_totals.notes` per row):
- **PRIVACY GUARD** — two 2022 donor names are long enough to run into the fixed-width address
  column with a single space, so the family carried a street into `donor_raw`
  (`Women's Democratic Club of Utah PO Box 91184`). The street portion is **discarded** at the
  boundary marker (a numeric token or `PO Box` — the same rule `cache_cfd` uses) and never
  stored; the row is flagged `needs_review=1`. Rows carry `donor_city` / `donor_state` only.
- **FIELD-SHIFT FLAG** — where a filer typed a **malformed date** (`5/20.14`, `4/2//14`) the
  family's date regex misses it, the token slides into `vendor_raw` and the real vendor slides
  into `purpose`. The AMOUNT is unaffected (the side still reconciles), so the 4 affected rows
  are kept and flagged `needs_review=1` rather than dropped.

**One COVER DIVERGENCE, recorded not resolved.** On **Betsy Wallace 23016** the family reads
**no promotable expenditure figure** where the vision promotion published **734.21** — and the
family's own expenditure ledger sums to exactly 734.21, corroborating the vision figure. The
vision promotion governs (a figure is never taken from the parser over the transcription); the
family's inability to promote that cell is a FAMILY LIMITATION and is why those 3 rows are not
published. Documented, not patched.

## Shared-script need — SATISFIED (the family is registered; the builder stays module-local)

The **new form family** described here now exists: `scripts/campaign_finance/families/summit_form.py`
(county tier, Utah Code 17-16-6.5), registered and unit-tested on Langston 2022. It could not
reuse an existing one:
`millcreek_form` and `ogden_form` both return **$511.62 as "total contributions"** on a Summit
filing whose printed contribution total is **$503.00** — they read the wrong cover column. The
family would need (a) cover anchors `Total contributions` / `Total expenditures` / `Campaign
balance`, (b) the **`Current | Last | Cumulative`** column order (Millcreek's is
`Last | This | Cumulative` — reversed), (c) section tagging on `ITEMIZED CONTRIBUTION REPORT` /
the itemized expenditure header instead of `FORM "A"/"B"`, and (d) `dedup_mode="cumulative"`.
Evidence table: `RECON.md` §4. **The 2026-08-01 vision pass supersedes that need for the COVER
TOTALS** — `build_finance.py` stays module-local and reads the curated `vision/` caches for every
`stated_*` figure. The family is the home of the *itemized* tranche only, and 2026-08-02 wired it
for the born-digital subset.

## Rebuild

```
python3 summit_county/campaign_finance/backfill_text.py   # text/ + text_extraction.csv (slow: OCR)
python3 summit_county/campaign_finance/build_index.py     # index.csv + unrecovered.csv
python3 summit_county/campaign_finance/build_finance.py   # filing_totals + cover_totals + the born-digital
                                                          # contributions/expenditures
python3 scripts/campaign_finance/validate_finance.py summit_county/campaign_finance   # -> PASS
```
`build_finance.py` is offline, idempotent, and reads ONLY `index.csv` + `vision/*.json` + the
born-digital `text/*.txt` sidecars (the itemized layer).
**Corrections to a transcribed figure go in the filing's `vision/<key>.json`** (with a note saying
what was re-read at the source), never in the derived CSVs. The cache key is the repo-standard
`sha1(index.csv path)[:8]` (`scripts/campaign_finance/vision_lib.cache_key`).

All four builders are idempotent and offline. Re-acquisition is manifest-driven:
`batch/manifest.json` holds every `document_id` + `source_url` + `sha256`, so a refresh is a
re-fetch of those ids plus a re-parse of `raw/index_pages/` for new rows. `index.csv` /
`unrecovered.csv` / `text_extraction.csv` / `filing_totals.csv` / `cover_totals.csv` /
`contributions.csv` / `expenditures.csv` are **DERIVED — never hand-edit them**; corrections go in
`batch/manifest.json` (with a `notes` field citing the evidence), `listed_gaps.csv`,
`office_overrides.csv` (`document_id,office,seat,evidence` — read by `build_index.py`), or the
per-filing `vision/<key>.json`.
