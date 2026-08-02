# campaign_finance/ — Salt Lake County COUNTY-office campaign finance

Campaign Contribution & Expenditure (C&E) disclosures for **Salt Lake County elected COUNTY
offices** — Mayor, County Council (Districts 1–6 + At-Large A/B/C), Sheriff, District Attorney,
Clerk, Assessor, Recorder, Treasurer, Auditor, Surveyor. Built 2026-08-01 (county-acquisition
wave). Utah county candidates file with the **County Clerk**, not `disclosures.utah.gov`.

**This is the entity whose absence made the owner's "largest donor in a county race" query
fail.** That query is now answerable from `contributions.csv` (2024 + 2026 cycles, structured).

## What this is
Three acquisition eras (full recon in `RECON.md`, source log in `AVAILABILITY.md`):
- **(a) Legacy clerk PDFs, ~2006–2015** — `raw/clerk_legacy/` — 547 per-candidate report PDFs
  from `slco.org/clerk/financialDisclosurePDF/`. RAW + **stated totals for every filing**
  (vision, complete 2026-08-02); **no itemized layer**. `pdftotext` is useless for the figures
  here — see "Image-only text" under Honest gaps.
- **(b) County disclosure portal, ~2016–2021** — **NOT ACQUIRED (WAF-blocked).** See "Honest
  gaps" below. Recoverable only via browser automation or GRAMA.
- **(c) EasyVote portal, 2022–2026** — `raw/easyvote/` (442 redacted PDFs) + `raw/easyvote_api/`
  (the itemized JSON — the authoritative **structured** source). The **structured money layer**
  (`contributions.csv` / `expenditures.csv` / `filing_totals.csv`) is built from this JSON.

## Layout
```
raw/clerk_legacy/    547 legacy PDFs + _fetch_log.jsonl (url, sha256, candidate, office, period)
raw/easyvote/        442 county redacted PDFs (image-only) + _fetch_log.jsonl
raw/easyvote_api/    the 4 EasyVote API JSON responses (STRUCTURED SOURCE) + _fetch_log.jsonl
text/                text sidecars (<channel>__<name>.txt); born-digital layer only
vision/              VISION STATED-TOTALS CACHES — **670 files, one per filing in the two
                     non-structured eras (COMPLETE 2026-08-02)**, keyed sha1(index.csv path)[:8];
                     see "The vision totals tranche" below
index.csv            one row per acquired filing (both channels)
contributions.csv    DERIVED — itemized donations (EasyVote 2024+), per SCHEMA.md
expenditures.csv     DERIVED — itemized expenditures (EasyVote 2024+)
filing_totals.csv    DERIVED — one row per filing: the 164 EasyVote-JSON itemized filings FIRST,
                     then the 670 legacy + 2022 stated-totals rows (APPENDED, never interleaved)
donor_aliases.csv    CURATED (header-only seed)
finance_overrides.csv CURATED (header-only)
build_finance.py     builds the 3 structured CSVs from raw/easyvote_api/*.json, then APPENDS the
                     vision stated-totals rows (build_totals_tranche)
make_vision_caches.py materializes vision/*.json from the raw transcription records
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
- `source` ∈ `clerk_legacy` | `easyvote`. `has_itemized=yes` ⇒ the filing has structured rows in
  `contributions.csv`/`expenditures.csv` (EasyVote 2024+ only).
- `election_year` is the **even-year proxy** (see caveats). `format` ∈ text | scanned, measured
  from the actual PDF font layer (never guessed by extension).

## Structured layer — how it was built (READ THIS before quoting numbers)
`build_finance.py` reads the EasyVote **itemized advanced-search JSON** (`raw/easyvote_api/
advancedsearch_{contributions,distributions}.json`) — the genuinely-structured, per-transaction
source, the same data class as `disclosures.utah.gov` — filters to county offices, joins to
`documentsearch.json` for filer/filing metadata, and emits the three CSVs per
`scripts/campaign_finance/SCHEMA.md`. **The PDFs are NOT parsed for the money** (they are
image-only redacted scans); the API JSON is authoritative.

- **contributions.csv 4,956 · expenditures.csv 3,278 · filing_totals.csv 164 filings** —
  **$1,905,741 raised / $1,633,769 spent** across the **2024 + 2026** county cycles.
- **donor_type** (contrib): individual 4,371 · unknown 300 (294 are **blank-donor** aggregate/
  unnamed rows, `needs_review=1`) · candidate-self 117 · family-of-candidate 90 · loan 79.
- **office** (contrib rows): County Council 3,138 · Assessor 403 · Mayor 347 · Treasurer 307 ·
  Clerk 264 · District Attorney 183 · Surveyor 179 · Sheriff 100 · Auditor 34 · Recorder 2.

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
6. **ITEMIZED coverage is 2024 + 2026 only.** The 2022 county EasyVote docs store only the
   redacted PDF — the API returns no itemized rows for them. 2006–2015 (legacy) and 2016–2021
   (WAF gap) have no itemized layer either. Those two non-structured eras DO have
   **stated-totals** rows in `filing_totals.csv` for **all 670 filings** (vision-transcribed,
   complete 2026-08-02, see below); they are a different and weaker thing than the itemized
   layer and are labelled as such in `notes`. **Stated totals answer "how much"; only the
   2024/2026 itemized layer answers "from whom".**
7. **`filing_totals.csv` mixes two provenances.** Rows 1–164 are EasyVote-JSON itemized
   filings (`extraction_confidence=high`, blank `stated_*`); rows 165–834 are vision
   stated-totals rows (`extraction_confidence` ≤ `medium`, blank `itemized_*`). Filter on the
   `notes` marker `VISION-TRANSCRIBED` — or on which side is populated — before comparing.
   **Never sum the vision rows**: interims, year-ends, finals and amendments overlap by design,
   duplicate and mutually-inconsistent filings are common, and at least two filers put
   cumulative figures in Column A. Use `scripts/campaign_finance/cycle_totals.py`.

## The vision totals tranche (2026-08-01 → **COMPLETE 2026-08-02**) — stated totals for the two NON-STRUCTURED eras

The legacy clerk PDFs (~2006–2015) and the 2022 EasyVote cycle have **no machine-readable
money at all** — the legacy scans' "text" layer is scanner OCR over HANDWRITING (worthless for
figures) and all 123 of the 2022 EasyVote PDFs are flattened images with zero text. Verified
2026-08-01: `pdftotext` returns nothing usable for either era, and the EasyVote
`documentsearch` JSON carries no total fields. **Vision is the only channel.**

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

### The tranche is COMPLETE — how to redo or extend it
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
**The next tranche is ITEMIZATION** (Schedule A/B donor lines for these two eras), which drops
into the same caches — `contributions`/`expenditures` are already present and empty by design,
so no schema change is needed.
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
  byte-identical each time (`contributions.csv`, `expenditures.csv`, and rows 1–164 of
  `filing_totals.csv`) — the tranche is APPEND-only and any drift there means a bug.
- **Merge records with a dedupe pass before materializing.** Agents sometimes leave their own
  staging files beside the canonical `chunk_NN.json`; `make_vision_caches.py` hard-fails on a
  duplicate key, so collapse to one record per `index_path` first (canonical file wins).

## Honest gaps
- **2016–2021 (channel b) — the county disclosure portal is WAF-blocked** (BigIP: every scripted
  request 302-loops to `/Search/PublicSearch` or resets the connection, under any UA/TLS/cookie/
  delay). Wayback archived the folder/registration metadata but **not** the itemized `/Report/{id}`
  pages. This is a genuine ~3-cycle gap (2016/2018/2020). Recover via the `claude-in-chrome`
  browser skill against the live portal (a real browser session may pass the WAF; the `/Report/
  {id}` pattern + archived folder inventory make it turnkey) or a GRAMA request. See RECON.md.
- **Image-only text.** Every EasyVote redacted PDF and every legacy PDF is effectively
  image-only for VALUES: the 123 legacy PDFs that `index.csv` marks `format=text` carry a
  scanner-embedded OCR layer over **handwritten** 2006-era forms, so the pre-printed labels
  extract but the figures are garbage. Treat `format=text` in this dataset as "has a font
  layer", NOT as born-digital (the riverton precedent). Full text sidecars for the scans are
  still deferred; the tranche transcribed **stated totals only** (above).
- **Stated-totals coverage is now COMPLETE (670 of 670); ITEMIZATION is the remaining gap.**
  Every filing in both non-structured eras has a cache and a populated `filing_totals` row, but
  the Schedule A/B **donor and vendor lines for 2006–2015 and 2022 are still untranscribed** —
  so "who gave to whom" remains a 2024/2026-only question. The caches carry empty
  `contributions`/`expenditures` lists ready to receive them.
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
python3 build_finance.py     # structured CSVs from raw/easyvote_api/*.json + vision totals rows
python3 backfill_text.py --ocr legacy   # text/ sidecars (born-digital + legacy OCR)
python3 build_index.py       # index.csv from the fetch logs
python3 ../../scripts/campaign_finance/validate_finance.py .   # conformance
```
Re-fetch: EasyVote via the `ecf-api.easyvoteapp.com/advancedsearch/{contributions,distributions}/
D2EEAA9C-E9BF-4B77-AC5E-2A6F379D1775` recipe (browser UA required — 403 to Python-urllib);
legacy via the URLs in `raw/clerk_legacy/_fetch_log.jsonl`.

## OUT OF SCOPE (leads only — see AVAILABILITY.md)
- **Local school boards** (clerk `…/local-school-board/` + EasyVote) — a disjoint office set.
- **Metro Township Councils** — the clerk `…/metro-township-councils/` page has **297 redacted
  PDFs** (Millcreek/Magna/Kearns/Copperton/Brighton/Emigration/White City, mostly 2016) + 57
  EasyVote filings (2023/2026). May close the **kearns cf-blocked-cycles** caveat and enrich
  magna/white_city/copperton/emigration_canyon/millcreek city CF.
