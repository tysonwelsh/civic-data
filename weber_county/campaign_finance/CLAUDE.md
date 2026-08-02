# campaign_finance/ — Weber County COUNTY-OFFICE campaign finance

**As-of 2026-08-01.** Additive module for `weber_county/`. Touches nothing else in the
entity: no db build, no federation, no edits outside this directory. Read
`RECON.md` (channels + method) and `AVAILABILITY.md` (coverage + gaps) before quoting
anything from here.

## What this is

**Campaign contribution & expenditure reports filed by candidates for WEBER COUNTY
elective office** — Commission Seats A/B/C, Clerk/Auditor, Sheriff, Attorney, Assessor,
Recorder/Surveyor, Treasurer — for the even-year cycles **2012 · 2014 · 2016 · 2018 · 2020
· 2022 · 2024 · 2026**. County candidates file with the **County Clerk/Auditor** under
**Utah Code 17-16-6.5**; the county publishes the filings itself. (Odd-year **municipal**
candidates file with each **city recorder** under 10-3-208 — those are not Weber County's
records and are not here.)

- **89 documents** retained verbatim (117.4 MB) from **4 channels**.
- **`filing_totals.csv` — 98 rows, one per county-office filing** (stated cover-page
  totals, built 2026-08-01; see "The money layer" below).
- **The BORN-DIGITAL itemized layer — 3 of 98 filings** (built 2026-08-02): **16
  contribution / 11 expenditure rows**, each side reconciling to the cent against the
  stated total, with per-row `geometry`. The other 95 filings itemize nothing here —
  93 handwritten scans + 2 stated reasons (§"The itemized layer" below).
- **`index.csv` — 197 rows**: 196 filings + 1 document-grain row. **114 of the filing rows
  are page ranges inside a consolidated PDF.**
- **98 county-office filings** by **32 distinct candidates**.
- **91 rows are school board** and **7 are `unclear`** — inventory of the county's own
  compilation documents, NOT a school-board dataset (`AVAILABILITY.md` §2).

## Layout

```
raw/archives/   6 consolidated per-cycle archive PDFs (2012,2016,2018,2020,2022,2024)
raw/y2026/      31 per-candidate 2026 PDFs from the live page
raw/wayback/    30 per-candidate PDFs recovered from the predecessor host (2012/2014/2016)
raw/state/      22 files from the Lt. Governor municipal tree (2010×7, 2012-primary×14,
                the 2022 aggregate) — the first two sets are the VERIFIED-NEGATIVE evidence
raw/*/_fetch_log.jsonl   provenance per fetch attempt: url, http_status, bytes, sha256,
                         content_disposition, retrieved_utc, and the PORTAL LABEL in `note`
text/           one sidecar per document, pages delimited by form feed (\f)
index.csv       ONE ROW PER FILING (see schema below)          [DERIVED — build_index.py]
filing_attribution.csv   CURATED — candidate/office/date read from each filing's own form
text_extraction.csv      MEASURED format/method per document   [DERIVED — backfill_text.py]
unrecovered.csv          33 filings the county once published and no longer exists anywhere
vision/<key>.json        CURATED — 98 stated-totals transcriptions (2026-08-01 tranche)
filing_totals.csv        DERIVED — 98 county-office filings   [build_finance.py]
contributions.csv        DERIVED — the BORN-DIGITAL itemized layer (16 rows)
expenditures.csv         DERIVED — ditto (11 rows)
batch/portal_manifest.json  portal-published labels, kept ONLY for comparison
batch/*.tsv     the fetch batches (url -> filename -> portal label)
fetch_cf.py · backfill_text.py · build_index.py · build_finance.py
RECON.md · AVAILABILITY.md · PRIVACY.md
```

## The money layer — stated cover-page TOTALS only (built 2026-08-01)

`filing_totals.csv` honors the `scripts/campaign_finance/SCHEMA.md` §4 column contract
(plus the optional trailing `filing_regime`), so it drops into the shared model
unchanged if a form family is ever registered. **`python3
scripts/campaign_finance/validate_finance.py weber_county/campaign_finance` → PASS
(0 fails, 25 warns; every warn is an out-of-scope school-board / `unclear` /
state-duplicate index row).**

**How the numbers were obtained.** OCR is never trusted for a figure on these forms.
Each filing's **summary page was rendered inside its own PDF** (`pdftoppm -r 200`, page
picked from `filing_attribution.csv`) and **read visually** — 93 of 98 filings. The
other **5 are born-digital Polimorphic e-filings** whose totals were parsed straight
from their machine-readable `text/` sidecars, no vision needed. Each
`vision/<key>.json` carries the verbatim last/this/**cumulative** cells, **per-field
confidence**, the report-type box the filer checked, and
`"transcribed_by": "vision-transcribed(claude-opus-5; 2026-08-01 totals tranche)"`.
Cache key = `sha1(index.csv path + "|" + "<page_start>-<page_end>")[:8]` — the
repo-wide `vision_lib` convention with the per-filing discriminator Weber needs,
because one archive PDF holds up to 50 filings.

**The five things to respect before quoting a number:**

1. **The forms are CUMULATIVE** (`filing_regime=cumulative`; the third column is
   literally "Cumulative Totals"). A candidate-cycle total is the **latest
   non-superseded** report — **never** a sum of that candidate's filings.
2. **`stated_*` is the CUMULATIVE column**; `stated_beginning_balance` is the
   ending-balance figure in the "Totals from Last Report" column.
3. **Officeholder accounts carry across cycles.** Harvey's 2024 final states $77,060.05
   cumulative but opens from his 2020 closing figures; "raised in cycle N" must subtract
   the opening column.
4. **An empty itemized layer means NOT TRANSCRIBED, not "no donors"** — which is why
   `reconciles_*` is blank (unknown) and never `False` on the 95 filings with no rows.
   **3 filings DO carry itemized rows** (2026 born-digital) and those, and only those,
   have `reconciles_*=True` with a non-zero `n_contrib_rows`/`n_expend_rows`.
5. **A dash is not a zero, and an unreadable digit is not a value.** 10 rows have a
   blank `stated_ending_balance` because the filer wrote `-`; 1 has a blank
   `stated_total_expenditures` because the printed figure is `13.742.18`; Corey Combe's
   2012 balance is blank because the handwriting reads as either 4,287.87 or 4,957.87
   and did not resolve at 900 dpi. **None was repaired.**

Filer errors, amendments, sign conventions and the county's own redactions are all
recorded per row in `filing_totals.notes` (carried through from the cache). Corrections
go in `vision/<key>.json` with a note saying what was re-read at the source — never in
the derived CSVs.

**Per-cycle dollars, the finals-only bias, and the proposed coordinator caveat are in
`AVAILABILITY.md` §1b.**

## The itemized layer — born-digital only (built 2026-08-02, TRANCHE 3 Phase A)

`contributions.csv` (16 rows) / `expenditures.csv` (11 rows) hold the **2026 Polimorphic
e-filings** and nothing else. Wired to the registered `weber_polimorphic` family through
the shared normalization + reconciliation primitives; `AVAILABILITY.md` §7a has the
measured table and every gated-out reason. The five rules that govern it:

1. **Reconciliation-gated.** A side ships only when its rows sum EXACTLY (±$0.01) to the
   stated total this module already publishes. A side that does not reconcile emits
   **nothing** plus a reason in `filing_totals.notes`. The vision/born-digital stated
   totals are ground truth and are **never recomputed** by the family.
2. **The anchor must agree.** The family's anchor is the form's *"Total … on This
   Report"* line; this module publishes the **cumulative** column. On these filings the
   two are the same figure — where they would diverge, the published total governs and
   no row ships.
3. **Parsed from the RAW PDF** (`pdftotext -layout`), never from `text/` (those sidecars
   are `format=mixed` — part native text, part tesseract OCR). Born-digital detection is
   by **document content** (the Polimorphic footer + the summary line), never by filename
   or portal label — the same rule as attribution, below.
4. **`geometry` on every row** (`p<page>:l<line>:c<col0>-<col1>`, SCHEMA.md §2a): the
   amount cell each figure was read from. 100% coverage on the emitted rows.
5. **Two born-digital filings emit nothing and say why** — Arbon (filer answered "No" to
   both disclosure questions yet states 879.97 on both sides: an internal source
   inconsistency, recorded not resolved) and Allred (Polimorphic omits the `Itemized
   Contribution Report (#n)` header for a single-entry filing and the family slices on
   that header — a **family limitation documented, not patched**; the engine is frozen
   this phase). Both are queued for Phase B.

## The one rule that matters here: portal labels never set attribution

**Every filing's candidate, office and date come from the document's own printed form
fields** — read by OCR where the field was typed, and by a **vision read of the rendered
page** where it was handwritten (`read_method` records which, per row). The portals'
labels are retained separately (`index.csv.portal_label`, `batch/portal_manifest.json`) so
a disagreement is visible, but they never populate `candidate` / `office_stated`.

This is not pedantry. The live 2026 page renders its report links **column-wise**, so a
link cannot be attributed to a candidate by position in the page at all (RECON.md §3). And
scope depends on attribution: the county's archive PDFs mix **county** and **school
board** filings in one file under one shared form, and the only thing separating them is
the office each filer wrote on their own cover page.

## `index.csv` schema

Required six first (`date,title,source_url,retrieved_date,format,extraction_method`), then:

| column | meaning |
|---|---|
| `date` | the filing date **printed/signed on the form**. Blank where the filer left it blank — never inferred from a filename or a portal label. |
| `candidate` | **verbatim as written on the form**, including nicknames, committee names and the filer's own spelling. Never normalized in place. |
| `candidate_key` | deterministic FIRST+LAST join key (nicknames in quotes dropped, `- Committee to Elect X` dropped, party markers and Jr/Sr/II–IV stripped, `Last, First` reordered). Derived, alongside — not a replacement. |
| `matched_election_candidate`, `join_confidence` | join to `../elections/election_results_by_contest.csv`. `exact` = same person key **and** same cycle year (76 county rows); `person-only` = same person, a different cycle (7); `none` = no match (15). **`none` is not "did not run"** — it is mostly nickname variance (the forms say *James H. "Jim" Harvey*, the canvass says *Harvey, Jim*) or an unopposed/convention-stage candidate the canvass never lists. |
| `office_stated` | **verbatim** office line. Kept with the filer's own errors (`Commisioner`, `HOME OFFICE`, a campaign name instead of an office, or blank). |
| `office_scope` | `county` (98) / `school_board` (91) / `unclear` (7). Derived from `office_stated` only. |
| `election_year` | **trailing derived ALIAS of `election_cycle`** (identical value), because the shared campaign-finance contract keys itemized rows on `election_year`. `election_cycle` remains the authoritative name here. |
| `election_cycle` | even-year cycle. A January year-end report is assigned to the **prior** even year (a 2015-01-05 report is the 2014 cycle). |
| `filing_grain` | `filing` (a standalone PDF) / `filing-in-compilation` (a page range inside a consolidated PDF, 114 rows) / `document` (1 row — the state's re-saved 2022 duplicate, see below). |
| `page_start`,`page_end`,`pages_total` | the filing's page range inside `path`. For a compilation the boundaries are the **printed** `CAMPAIGN FINANCIAL REPORT: <year>` cover headers — machine-printed, so the splits are reliable even where the handwriting is not. |
| `channel` | which of the 4 channels served the bytes. |
| `portal_label` | what the portal called it. **Comparison only.** |
| `sha256`,`bytes` | of the retained file, from the fetch log. |
| `read_method` | `ocr` / `ocr (born-digital)` / `vision (rendered cover page)` / `vision (rendered page 1)`. |
| `needs_review` | `1` when the office, the candidate or the date could not be read, or the scope is `unclear` (34 rows overall, 24 of them county). This was the `cf-vision-transcribe` queue; the 2026-08-01 tranche read a filing date off the form face for **23 of those 24** and an office for 2 of the 3 blanks, but **`filing_attribution.csv` was deliberately NOT rewritten** — the recovered values live in `vision/<key>.json` (`filing_date_stated`) and in `filing_totals.filing_date`. Promoting them into the CURATED attribution layer is a coordinator decision. |

## Caveats / do-nots

- **Dollar amounts are STATED COVER-PAGE TOTALS on 95 of 98 filings**
  (`filing_totals.csv`, built 2026-08-01 — see "The money layer" above and
  `AVAILABILITY.md` §7). For those, **there are no itemized donor or vendor rows**: the
  Form A/B schedules behind the covers are handwritten. For "who gave what" there, open
  the raw PDF at the row's page range. The **3 born-digital filings with itemized rows**
  are the exception — see below.
- **Never sum the 2022 filings twice.** The county and the state publish the *same*
  52-page 2022 compilation as two differently-saved files. Both are retained; the filings
  are attributed once, to the county copy. The state copy is the single
  `filing_grain=document` row.
- **`format` is measured, not guessed** (`text_extraction.csv`): **175 rows `scanned`, 22
  `mixed`, 0 fully born-digital.** `mixed` means a compilation that binds a few
  born-digital filings among scans — those documents were OCR'd **only on the pages the
  text layer left blank**, so a `mixed` sidecar is part native text and part OCR.
- **The `text/` sidecars carry the PRINTED form, not the filled-in values.** They are
  reliable for "which form, whose office, which cycle, is this a Form A or Form B page"
  and unreliable for names and numbers in handwriting. Search them; do not quote figures
  from them.
- **A zero in the coverage matrix is usually the election calendar**, not a gap —
  county offices are four-year terms on alternating even years. The genuine losses are
  ledgered in `unrecovered.csv` (33 filings, all 2018/2020 interim reports).
- **The 2026 cycle is live and incomplete** — 5 candidates were still *"Awaiting final
  report"* on the page, and no 2026 consolidated archive exists yet.
- **School-board and conflict-of-interest material is out of scope**; the school-board
  rows present are inventory of county compilation documents. Do not treat them as
  coverage.

## Rebuild

```
python3 fetch_cf.py --batch batch/<name>.tsv --out raw/<channel> \
        --referer https://www.weberelections.gov/financialdisclosures [--use-curl]
python3 backfill_text.py          # measures format, writes text/ + text_extraction.csv
python3 build_index.py            # index.csv from the fetch logs + attribution + text
python3 build_finance.py          # index.csv + vision/*.json -> filing_totals.csv, and the
                                  # `weber_polimorphic` family over the born-digital raws ->
                                  # contributions/expenditures; re-verifies every sha256
                                  # (needs poppler's pdftotext on PATH)
python3 ../../scripts/campaign_finance/validate_finance.py .   # expect PASS
```
`build_index.py` is idempotent and reads only files in this directory (plus a **read-only**
look at `../elections/election_results_by_contest.csv` for the join). New documents need a
row in `filing_attribution.csv` — read from the document — or they surface as a loud
`filing_grain=document`, `needs_review=1` row.
