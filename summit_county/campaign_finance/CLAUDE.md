# campaign_finance/ — Summit County COUNTY-OFFICE candidate financial disclosures

Additive module, as-of **2026-08-01**. Does **not** modify any existing `summit_county/` dataset
and is **not** federated into `gov.db` (no build step touches the entity db). It completes the
**elections → officeholders → votes** chain for the county tier: who funded the candidates whose
County Council roll calls live in `../legislative/` and whose wins are certified in
`../elections/`.

**Money layer as of 2026-08-17 (post-ruling): STATED TOTALS (all 131) + a BORN-DIGITAL itemized layer
(11 filings) + a COMPLETE VISION itemized layer over the SCANS (116 of 116 — QUEUE CLOSED).** All **131** cover
pages were vision-transcribed (Read-tool method, `$0` API) and `filing_totals.csv` carries each
filing's own printed contribution / expenditure / ending-balance figures. The **15 born-digital
filings** were then parsed by the registered `summit_form` family (TRANCHE 3 Phase A,
2026-08-02): **105 contribution + 386 expenditure rows over 11 filings**, every emitted side
reconciling to the cent. TRANCHE 3 **Phase B** opened the 116 SCANS (2026-08-14) and **closed the queue on 2026-08-17**:
all **116** are itemized by Read-tool vision — **1,193 contribution + 1,407 expenditure rows**
(after the 2026-08-17 **reconciliation-basis ruling** published 16 previously-withheld PERIOD-scoped
sides), 100% carrying `pct:` geometry, **181 of 212 published sides reconciling EXACTLY**. So **131 of
131 Summit filings now carry an itemized layer**. The queue is DERIVED, never hand-kept, and it
is now empty: `python3 _backups/2026-08-14-tranche3/summit-b/wave_stats.py --residue` prints
nothing. ⚠ An empty itemized layer no longer exists on any filing except where a side is honestly
`none` (no such page), blank, or one of the **5 sides still WITHHELD** after the 2026-08-17
reconciliation-basis ruling — see the caveats.

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
vision/<sha1(path)[:8]>.json  CURATED — the cover-page transcription of every filing (131);
                            since 2026-08-14 the itemized SCAN rows live in the SAME caches
make_itemized_caches.py     the ONLY writer of the caches' itemized half (never touches the cover)
filing_totals.csv           DERIVED — one row per filing, SCHEMA.md §4 contract
cover_totals.csv            DERIVED — module-local: ALL THREE cover columns, verbatim
contributions.csv           DERIVED — SCHEMA.md §2 + trailing `geometry`; born-digital 105 + vision 1,193
expenditures.csv            DERIVED — SCHEMA.md §3 + trailing `geometry`; born-digital 386 + vision 1,407
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

- **Cover-page totals ARE transcribed for all 131, and donor itemization now covers all 131**
  (15 born-digital + **116 of 116 SCANS**, queue closed 2026-08-17). Use `filing_totals.csv` /
  `cover_totals.csv` for any dollar figure — **never** the `text/` sidecars of a SCAN, which are
  OCR of handwriting and mis-anchor exactly the way the shared parsers do. Where a filing still
  holds no itemized row, read the reason off `_meta_itemized.sides`: `none` = the document has no
  such schedule page, `transcribed` with zero rows = the page exists and is BLANK (a real zero),
  `withheld` = read but not published (rows parked in `_meta_itemized.withheld_rows`). ⚠ Since the
  2026-08-17 ruling a cache side may read `withheld` while the module PUBLISHES its parked rows on
  the PERIOD basis — the cache records what the transcriber decided at the page, `build_finance.py`
  decides publication. `filing_totals.notes` is authoritative for what shipped. None of these
  states is "no donors".
- **Filter the itemized layer by `extract_method` before comparing eras.** `summit_form/text` =
  the born-digital parser (`extraction_confidence=high`); `vision-itemized/summit-scan` = the
  Phase-B vision rows (capped at `medium`, SCHEMA §6). The two are read by different channels
  under different gates.
- **A `reconciles_*` of `False` on a VISION row is the FILER's arithmetic, not a defect** (the
  SLCo wave-B2 semantics, and the deliberate difference from the born-digital path, where a
  parser that disagrees with the page emits nothing). The stated figure is the form's own
  printed total and is never recomputed; the cause is named in `notes`. **32 side-flags read
  `False`** — 29 with a `delta` verdict and 3 whose ledger closes on the page exactly but differs
  from the module's stated total for a STRUCTURAL reason (the `split50` `<=$50` aggregate) or
  because in-kind money the filer counted inside his own total is excluded from
  `itemized_contrib_sum`. Full ledger: AVAILABILITY.md → "The SCAN itemization wave — QUEUE
  CLOSED 2026-08-17".
- **⚠ THE RECONCILIATION-BASIS RULE (owner-ratified 2026-08-17) — read this before reading any
  `reconciles_*` column.** A side is reconciled against the printed cover figure that MATCHES ITS
  OWN SCOPE: the **CURRENT REPORT** cell for a PERIOD-scoped ledger, the **CUMULATIVE** cell for a
  cumulative one. No figure is ever synthesized by differencing covers, and a side that closes
  against NEITHER printed figure stays withheld. `stated_total_*` is UNCHANGED — always the
  cumulative cover figure. The ruling published **16 of the 21 previously-withheld sides**
  (81 rows: 1264, 1265, 1268-expend, 1274, 4278-contrib, 11861, 12943-expend, 24384, 24390, 27451),
  each with **`is_incremental=True`** on every row and a `notes` line that opens
  `ITEMIZED <side> PERIOD-SCOPED (is_incremental=True)`, names the period figure AND the cumulative
  one, and states that the sum is one reporting period and **NOT a cycle total**. ⚠ On those rows
  `reconciles_*`/`recon_delta_*` are stated against the PERIOD figure, so `itemized_*_sum` is
  deliberately far below `stated_total_*` — that is the design, not a defect. The shared
  `validate_finance.py` check 6 was amended the same day to admit that DECLARED basis (and only a
  declared one). Full ledger: AVAILABILITY.md → "THE RECONCILIATION-BASIS RULING".
- **⚠ 5 sides across 5 filings remain WITHHELD** and must never be read as "no donors":
  **1250 Trussell 2014 contributions** (the Amount column is not on the scan — a landscape sheet
  fed through the scanner in portrait, cropping the right ~23% of the page, so the columns could
  not be assigned); **1268 Yost 2014 contributions** (cover Current 1,700+75 vs the schedule's own
  1,700/25 boxes — the filer's own two figures disagree and neither closes); **4278 Adair 2016
  expenditures** (+0.30 against the printed period box); **12943 Stevens 2020 contributions** (the
  page is blank and prints a $0 PERIOD total — nothing parked, so nothing to publish); **12944
  Francis 2020 expenditures** (blank page and an EMPTY Current Report cell — no printed period
  figure to gate against). The Phase-A born-digital **Harte 2026 (27200)** contribution side is
  also still refused, by the born-digital path's own stricter gate.
- **⚠ In-kind treatment is PER-FILER, not a form property, and the period-basis promotion TESTS
  BOTH conventions** (monetary-only, and monetary-plus-in-kind), recording which one closed in
  `notes` — 13 sides closed monetary-only, 3 monetary + in-kind (1264 both sides, 4278
  contributions). On an in-kind-inclusive side `itemized_*_sum` INCLUDES the in-kind money (that is
  what closes to the cent); everywhere else it is monetary-only. On the 2024 McKenna pair in-kind is a
  separate schedule and the cover is monetary-only; on 4020, 4278, 8191, 1268, 11110, 20758 and
  24234/24708 the filer counts in-kind INSIDE the contribution schedule's printed total and inside
  the cover figure. `itemized_contrib_sum` is monetary-only either way, so on the second class it
  sits under the stated total by exactly the in-kind amount. Settle it per filing from the page's
  own arithmetic; never assume it from the cycle or the form family.
- **Read `_meta_itemized.sides`, not `recon.result`, to decide what a side is.** Records use two
  vocabularies for a withheld or `none` side's `recon.result` (`withheld`/`none` on some, `unknown`
  on others — the AGENT_BRIEF shape documents only `exact|delta|unknown`). The side state governs.
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

- **(CLOSED 2026-08-17) Donor/expenditure itemization of the 116 SCANS.** Formerly the open item
  here; the queue is now empty and 131 of 131 filings carry an itemized layer. The working set,
  the per-row contract and the wave kit remain in `_backups/2026-08-14-tranche3/summit-b/`
  (`AGENT_BRIEF.md` is still the binding per-row contract for any future re-read).
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

## The SCAN itemized layer (TRANCHE 3 Phase B) — 116 of 116, QUEUE CLOSED 2026-08-17

Read `AVAILABILITY.md` → "The SCAN itemization wave — QUEUE CLOSED 2026-08-17" for the measured
table, the state audit that re-screened the paused wave's staged work, the full delta ledger, the
21 withheld sides and the source properties this wave established. The short version:

* **1,193 contribution + 1,407 expenditure rows** over **116** filings (2014 29 · 2016 10 ·
  2018 16 · 2020 12 · 2022 19 · 2024 19 · 2026 11), **$376,669.21 monetary contributions +
  $38,073.76 in-kind / $404,977.69 spent** (incl. the 2026-08-17 period-basis promotion: 23 + 58
  rows, $10,112.61 monetary + $18,064.43 in-kind / $26,229.77 spent). All 2,600 rows carry `pct:`
  **geometry** — 1,607
  MEASURED from the page's own printed rules by `rowbands.py` (deskewed projection, threshold
  chosen by grid REGULARITY, padded by the scan's skew drift), 912 from a validated DECLARED
  frame where the rules were too faint or contaminated. A row's box resolves to a crop with
  `scripts/campaign_finance/make_snippet.py` and the crop reproduces donor + amount.
* **181 of 212 published sides reconcile EXACTLY** (165 transcribed + the 16 period-promoted);
  29 carry a delta traced on the page and 2 have no printed figure to gate against; **5 sides
  remain withheld**; 15 are `none` (no such page in the document). **216 tight-crop escalations**
  at 600–2000 dpi (plus 1 on 2026-08-17 for the Wolbach re-read); a page-gate record exists for
  all 116.
* **The blank form's PRINTED SPECIMEN ROWS are not transactions** (`Jon and Jane Doe` $435.00 /
  `Name of Business` $512.00) and the printed total closing only without them is the proof — one
  filer highlighted them in yellow, another struck them through in pen, and a third copy dates
  the specimen `8/25/10` on a 2014 form.
* **Page position is not a classifier**: on 1059, 23013 and 24377 the EXPENSE page is page 2 and
  the CONTRIBUTION page is page 3.
* **On the pre-2022 sheet the ledger itemizes only the `>$50` donors.** Where a filer used the
  `<=$50` box, the rows reproduce the `>$50` box to the cent and the residual is exactly that
  aggregate — structural, not a missing row.

Rebuild path for this layer:
```
python3 make_itemized_caches.py ../../_backups/2026-08-14-tranche3/summit-b/records
python3 build_finance.py
python3 ../../_backups/2026-08-14-tranche3/summit-b/checkpoint.py     # append-only invariants
python3 ../../scripts/campaign_finance/validate_finance.py .          # -> PASS
```

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
