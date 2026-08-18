# juab_county/campaign_finance — how to use this module

**Built 2026-08-01; ITEMIZATION CLOSED 2026-08-14.** Juab **COUNTY-OFFICE** campaign financial
disclosures — Commission, Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder/Surveyor,
Treasurer. This is an **acquisition + document + stated-totals + FULLY ITEMIZED** module:
all 27 county-office filings carry donor/vendor rows or a reasoned no-schedule record. **Federated
into `gov.db` since 2026-08-01** — the `load_cf` loader now covers every entity with a
campaign_finance dataset (this module's filing_totals/contributions/expenditures rows carry
`city='juab_county'`); see the `cf-partial-structured` caveat row before querying.

**Read `AVAILABILITY.md` before quoting any number, and `RECON.md` before concluding anything is
missing.**

## The one thing to know

Juab county-office filings are **not on juabcounty.gov**. They are on the Lt. Governor's
`disclosures.utah.gov` system, in the tree labelled **"Municipal"**, in the **EVEN-year** folders,
sub-foldered by the candidate's **town of residence** — so a Juab County Sheriff filing sits at
`/Municipal/juab_2014_Mona/`. The label is not the jurisdiction. The only reliable discriminator
is the form header inside the PDF: **Utah Code 17-16-6.5** (county, Carr form 5-5-PG) vs
**20A-11-1301..1305** (school board, Carr 5-4 PG School). Every file is an image scan —
`pdftotext` returns 0 chars on all 82 — so this module is vision-transcribed.

### The itemization wave — CLOSED 2026-08-14 (TRANCHE 3 Phase B)

All **24** remaining filings (12 × 2010, 12 × 2014) were vision-itemized under the wave-B2
production contract, after a **13/13 pass** of the standing CF calibration suite
(`_audits/cf-calibration-suite/runs.md`, 2026-08-14). The module now holds **187 itemized rows**
(46 contributions + 141 expenditures). **34 of 48 sides reconcile EXACTLY** against a figure the
form itself prints; 3 carry a delta whose cause is named on the page; 9 sides have **no schedule
page at all** (honest non-existence). Only **$250.00** of stated money in the whole county lacks a
schedule to itemize (Robert Garrett 2014, whose Form A page is absent from the county's scan).
Read AVAILABILITY.md "The itemization wave" before quoting any of this — in particular the
**reconciliation-basis note**: `stated_total_contributions` is the form's line 1 + line 2, but
Form A itemizes only the over-$50 donors, so four filings show a `reconciles_contrib=False` that is
a BASIS DIFFERENCE, not a defect.

**Where the rows live.** Each filing has an itemized cache at `vision/<sha256-of-the-source-pdf>.json`
(written only by `make_itemized_caches.py`, from the wave's raw records at
`_backups/2026-08-14-tranche3-juab/records.json`). `applies_to` names every filing the document
carries; a filing is transcribed ONCE per sha256. `build_finance.py` merges those caches into the
derived CSVs and adds the trailing **`geometry`** column (`pct:x,y,w,h@p<page>`, SCHEMA.md §2a),
computed from the form's printed grid and verified by 600 dpi render-back. **Four honest states,
never conflated:** `sides.<side>="transcribed"` with rows = read; `"transcribed"` with ZERO rows =
the page exists and is BLANK (a real zero, 7 of them); `"none"` = no such page in the document
(9 sides); no cache at all = never attempted (**there are none**).

### ZERO born-digital scope — re-verified 2026-08-02 (TRANCHE 3 Phase A)

The TRANCHE 3 Phase A sweep, which wired the six new county form families into every other
county's `campaign_finance/` module, **built nothing here, and that is the correct outcome.**
The claim above was re-measured at the source rather than inherited: `pdftotext -layout` was
run over **all 82 retained raws** and returned **0 non-whitespace characters in total** — not
"few", zero. There is therefore **no born-digital face for any text-layer form family to
parse**, no `text/` directory, and nothing for a reconciliation gate to test.

Consequences, recorded so a later session does not re-open the question:
- **No shared form family is registered or wired for Juab**, by determination, not omission.
  The Carr 5-5-PG handwritten sheet is Phase B (vision) territory — and Phase B has now run.
- Phase A left the itemized layer at 2020 only; **Phase B (2026-08-14) closed 2010 and 2014**,
  so the "empty itemized layer means not transcribed" caveat no longer applies anywhere in this
  module. An empty side now means one of the two documented things (a blank page read, or no
  page at all) and the cache says which.

## What exists

```
raw/                    82 retained PDFs, byte-verified (26 county-office files, 56 school board)
  juab_2008_School_Board/   34   school board (out of scope, indexed not transcribed)
  juab_2010_primary/        29   12 county-office + 17 school board, interleaved
  juab_2014_{Callao,Eureka,Levan,Mona,Nephi}/  17   12 county-office + 5 school board
  juab_2020_Primary/         2   2 multi-filing bundles: 3 county-office + 1 school board
vision/
  _download_log.json    CURATED — per-file source URL, sha256, byte size (the fetch record)
  transcripts.json      CURATED — the COVER / stated-totals transcription of all 27 county
                        filings (+ the 2020 filings' inline itemized rows)
  <sha256>.json         CURATED — 24 ITEMIZED caches, one per 2010/2014 source PDF: Form A/B
                        rows with `pct:` geometry + `_meta.itemized` (sides, per-side
                        reconciliation, pages read, escalations, wave stamp)
index.csv               DERIVED — 83 rows: one row PER COUNTY-OFFICE FILING (27; bundle
                        files repeat their path — st_george precedent, conformance fix
                        2026-08-01) + one row per school-board file (56): source_url,
                        retrieved_utc, sha256, tier, classification_basis
filing_totals.csv       DERIVED — one row per COUNTY-OFFICE filing (27)
contributions.csv       DERIVED — itemized Form A rows (46), + trailing `geometry`
expenditures.csv        DERIVED — itemized Form B rows (141), + trailing `geometry`
build_finance.py        the builder — idempotent, re-verifies every sha256
make_itemized_caches.py the ONLY writer of vision/<sha256>.json; also the one place the
                        printed-grid -> `pct:` geometry conversion happens
RECON.md                per-channel determination (5 channels, what each held)
AVAILABILITY.md         coverage, ceilings, the 2024 posting-practice gap, the GRAMA asks
```

**`index.csv`, `filing_totals.csv`, `contributions.csv`, `expenditures.csv` are DERIVED —
regenerate, never hand-edit:** `python3 juab_county/campaign_finance/build_finance.py`.
Corrections to a COVER figure go in `vision/transcripts.json`; corrections to an ITEMIZED row go
in that filing's `vision/<sha256>.json` (or, better, in the wave records + a re-run of
`make_itemized_caches.py`) — either way with a note saying what was re-read at the source and
what decided it. The column contract is `scripts/campaign_finance/SCHEMA.md` §2/§2a/§3/§4.

**Rebuild:**
```
python3 juab_county/campaign_finance/make_itemized_caches.py     # only when records change
python3 juab_county/campaign_finance/build_finance.py
python3 scripts/campaign_finance/validate_finance.py juab_county/campaign_finance   # PASS
```

## Which artifact for which question

- **"Who ran for county office and what did they raise/spend?"** → `filing_totals.csv`. 27 rows,
  2010 / 2014 / 2020, all seven office classes. `office_verbatim` and `party_verbatim` are as
  written on the form (typos included: `Democrate`, `Commisoner`, `Rep.`); `office_std` is the
  normalized companion.
- **"Who donated / what did they buy?"** → `contributions.csv` / `expenditures.csv` — **all three
  cycles, 187 rows**. Each row's `geometry` resolves back to the box on the page it was read from
  (`scripts/campaign_finance/make_snippet.py`). Check the filing's `reconciles_*` and its `notes`
  before quoting a total, and read the reconciliation-basis note in AVAILABILITY.md: a
  `reconciles_contrib=False` on Sperry (2010/2014), Lofgran (2014) or Walker (2010) is the
  line-1-vs-lines-1+2 basis difference, not a defect.
- **"What source document is this?"** → `index.csv` — every row carries the published filename,
  the `municipal.utah.gov` URL, the UTC fetch timestamp and the sha256. `build_finance.py`
  re-hashes on every run and prints `byte verification: OK`.
- **"Is anything missing?"** → `AVAILABILITY.md`. 2012/2016/2018/2022/2024/2026 have **zero**
  county-office filings on any public channel.

## Cardinal-rule specifics for this module

1. **Blank is data.** A blank amount means the filer left the line blank or the handwriting is
   unreadable — never a zero. `0` appears only where the filer wrote a zero. Two Kenison 2020
   expenditure amounts are blank because they could not be read; they were not guessed.
2. **Filer errors are retained verbatim, never corrected.** Anderson-2014 and Garrett-2014 put
   every figure in the "totals from last report" column (kept in `stated_prior`, never promoted
   to cumulative — and their schedules reconcile exactly against those figures). Williams-2014
   wrote `"$150.00 + SIGNS"` (numeric blank, verbatim string kept — the itemized layer now
   accounts for both halves). Zirbes-2020 itemizes eight expenditures under a blank stated total.
   Anderson-2010 and Lofgran-2014 state balances that do not follow from their own lines.
   Walker-2010 wrote his Form B total on the aggregate-contributions line. All stand as filed.
2a. **An unreadable cell is resolved by the page's ARITHMETIC or not at all.** Walker-2010's
   cumulative >$50 cell was blank until 2026-08-14, when line 1's own LAST + THIS = CUMULATIVE
   identity and the single Form A row both gave 125.00. Corrections of this kind go in
   `vision/transcripts.json` with the proof written into the row's note — never by re-reading a
   glyph at higher resolution (GOTCHAS, the Rhodes reversal).
3. **State filenames lie.** `janice bowers 6-3-10.pdf` is signed *Janice J. Boswell*;
   `Helen_Miwall_10-28-10.pdf` and `Helen_Wall_10-28-10.pdf` are the same document. Names in the
   derived CSVs come from the form face, not the filename.
4. **Never surname-join across tiers.** Several surnames recur across county, school-board and
   municipal filings (Kenison, Carlton, Olsen, Hanks, Wall, Painter, Anderson). Kathleen Kenison
   (2010 Clerk/Auditor) and Marvin Garr Kenison (2020 Commissioner) are different people, both in
   this dataset. Resolve on full name.
5. **School-board filings are OUT OF SCOPE and untranscribed.** They are acquired only because
   the state folders interleave them with county filings. Juab and Tintic School Districts are
   separate taxing entities. The 2008 folder's 34 files are classified from the folder label plus
   one sampled form header — `index.csv.classification_basis` says so per row.
6. **`PRIVACY.md`:** campaign_finance text is never redacted. Candidate street addresses and
   phone numbers printed on the form face are deliberately **not** carried into the derived CSVs
   (only `residence_city`); the `raw/` scans are unaltered.

## Not built (deliberate)

- ~~No `gov.db` federation~~ — **SUPERSEDED 2026-08-01**: the owner authorized the county CF
  tier and `load_cf` was extended to every entity with a campaign_finance dataset; this
  module's rows federate (db-less entities federate datasets without a vote-spine db, the
  washington/juab elections precedent).
- **No `cycle_totals.csv`.** With one report per candidate per cycle a cycle total is a trivial
  query over `filing_totals.csv`; a derived file would only add a dedup contract this data does
  not need. (Cumulative-vs-incremental: these forms are **cumulative** — the third column is
  literally "CUMULATIVE REPORT" — verified on Painter-2014 where 1025.57 + 1647.51 = 2673.08.)
- **No `donor_aliases.csv` / `finance_overrides.csv`.** Still nothing warrants either after the
  itemization wave: the 46 contribution rows carry **29 distinct donor strings** and exactly ONE
  cross-spelling merge is even arguable — "Juab County Democratic Comm." / "Juab Democratic Party"
  (×2) / "Juab County Democratic Party", four rows in which four filers spell the same county
  party committee three ways. That is a legitimate alias row the day someone needs the rollup, and
  it is the only one in the corpus. Create them (curated,
  human-confirmed) when a real merge or a source-verified correction appears.
- **No shared-lib form family.** `scripts/campaign_finance/families/` has no `carr_5_5_pg` parser
  and adding one means editing shared code. `build_finance.py` is module-local and honors the
  SCHEMA.md column contract so the CSVs drop in unchanged if a family is ever registered.
