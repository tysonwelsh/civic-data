# juab_county/campaign_finance — how to use this module

**Built 2026-08-01.** Juab **COUNTY-OFFICE** campaign financial disclosures — Commission,
Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder/Surveyor, Treasurer. This is an
**acquisition + document + stated-totals** module with a partial itemized layer. **Federated
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

### ZERO born-digital scope — re-verified 2026-08-02 (TRANCHE 3 Phase A)

The TRANCHE 3 Phase A sweep, which wired the six new county form families into every other
county's `campaign_finance/` module, **built nothing here, and that is the correct outcome.**
The claim above was re-measured at the source rather than inherited: `pdftotext -layout` was
run over **all 82 retained raws** and returned **0 non-whitespace characters in total** — not
"few", zero. There is therefore **no born-digital face for any text-layer form family to
parse**, no `text/` directory, and nothing for a reconciliation gate to test.

Consequences, recorded so a later session does not re-open the question:
- **No shared form family is registered or wired for Juab**, by determination, not omission.
  The Carr 5-5-PG handwritten sheet is Phase B (vision) territory — which is exactly what the
  existing `vision/transcripts.json` layer already is.
- **The existing itemized layer is untouched by this tranche**: `contributions.csv` (4 rows)
  and `expenditures.csv` (23 rows) remain the hand-verified **2020-only** vision transcription,
  byte for byte. Nothing was re-derived, re-sorted or re-normalized.
- An empty itemized layer for 2010/2014 still means *not transcribed*, **not** *no donors*.

## What exists

```
raw/                    82 retained PDFs, byte-verified (26 county-office files, 56 school board)
  juab_2008_School_Board/   34   school board (out of scope, indexed not transcribed)
  juab_2010_primary/        29   12 county-office + 17 school board, interleaved
  juab_2014_{Callao,Eureka,Levan,Mona,Nephi}/  17   12 county-office + 5 school board
  juab_2020_Primary/         2   2 multi-filing bundles: 3 county-office + 1 school board
vision/
  _download_log.json    CURATED — per-file source URL, sha256, byte size (the fetch record)
  transcripts.json      CURATED — hand-verified vision transcription of all 27 county filings
index.csv               DERIVED — 83 rows: one row PER COUNTY-OFFICE FILING (27; bundle
                        files repeat their path — st_george precedent, conformance fix
                        2026-08-01) + one row per school-board file (56): source_url,
                        retrieved_utc, sha256, tier, classification_basis
filing_totals.csv       DERIVED — one row per COUNTY-OFFICE filing (27)
contributions.csv       DERIVED — itemized Form A rows (4; 2020 only)
expenditures.csv        DERIVED — itemized Form B rows (23; 2020 only)
build_finance.py        the builder — idempotent, re-verifies every sha256
RECON.md                per-channel determination (5 channels, what each held)
AVAILABILITY.md         coverage, ceilings, the 2024 posting-practice gap, the GRAMA asks
```

**`index.csv`, `filing_totals.csv`, `contributions.csv`, `expenditures.csv` are DERIVED —
regenerate, never hand-edit:** `python3 juab_county/campaign_finance/build_finance.py`.
Corrections go in `vision/transcripts.json` (the transcription layer), with a note saying what
was re-read at the source. The column contract is `scripts/campaign_finance/SCHEMA.md` §2/§3/§4.

## Which artifact for which question

- **"Who ran for county office and what did they raise/spend?"** → `filing_totals.csv`. 27 rows,
  2010 / 2014 / 2020, all seven office classes. `office_verbatim` and `party_verbatim` are as
  written on the form (typos included: `Democrate`, `Commisoner`, `Rep.`); `office_std` is the
  normalized companion.
- **"Who donated / what did they buy?"** → `contributions.csv` / `expenditures.csv`, **2020
  only** (3 filings). For 2010 and 2014 the itemized pages are not yet transcribed:
  `filing_totals.itemized_transcribed = 0`, `reconciles_* = ''`. An empty itemized layer for
  those years means *not transcribed*, **not** *no donors*.
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
   to cumulative). Williams-2014 wrote `"$150.00 + SIGNS"` (numeric blank, verbatim string kept).
   Zirbes-2020 itemizes eight expenditures under a blank stated total. Anderson-2010 and
   Lofgran-2014 state balances that do not follow from their own lines. All stand as filed.
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
- **No `donor_aliases.csv` / `finance_overrides.csv`.** Nothing yet warrants either; create them
  (curated, human-confirmed) when a real merge or a source-verified correction appears.
- **No shared-lib form family.** `scripts/campaign_finance/families/` has no `carr_5_5_pg` parser
  and adding one means editing shared code. `build_finance.py` is module-local and honors the
  SCHEMA.md column contract so the CSVs drop in unchanged if a family is ever registered.
