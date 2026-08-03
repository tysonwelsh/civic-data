# campaign_finance/ — Cache County COUNTY-OFFICE candidate disclosures

Additive module for the `cache_county` entity. Acquired **2026-08-01**; the **vision
transcription pass** (office lines + the filings' own stated totals) ran **2026-08-01/02**.
Modifies nothing else. Completes **elections → officeholders → votes** at the county grain:
who funded the people whose roll-call votes live in `../legislative/` and `../land_use/`,
and whose wins are in `../elections/`.

**Read `AVAILABILITY.md` before quoting any number from here.** The headline caveats are
now: **itemized donor/vendor rows exist for the 2022+ BORN-DIGITAL subset only** (21 of 239
filings, 32 contribution + 111 expenditure rows, each side reconciled to the cent — the
handwritten Carr era has stated totals only), and **5 filings still have no established
office**.

## What this is

**495 filing PDFs** (198 MB) covering **10 even-year county cycles, 2008 → 2026**, split
across three ledgers, plus a transcription layer and a derived money layer:

```
index.csv       239 rows — county-office filings (the package deliverable)
excluded.csv    256 rows — acquired, then classified OUT of scope (237 school board,
                           14 Cache Water District Board, 2 municipal, 2 special district,
                           1 state legislature)
unrecovered.csv   2 rows — listed by the county, bytes gone everywhere (Craig Butters, 2008)
raw/<cycle>/    the filings verbatim; raw/_fetch_log.jsonl = one provenance row per URL
                (url, original_url, http_status, bytes, sha256, fetched_utc, listing page)
text/           one .txt sidecar per retained PDF (pdftotext -layout, or tesseract OCR)
vision/         171 CURATED vision transcriptions, one per DISTINCT document (schema
                cache_cf_totals_v1) — the cover page, the filing's own stated totals, and
                the office determination with a QUOTE of the page line it rests on
listing_labels.csv  the 2008/2010 ARCHIVED listing rows (name + the date the county printed
                    beside each link) — the only source of exact filing dates for those cycles
filing_totals.csv        DERIVED — one row per index.csv filing, SCHEMA.md §4 column contract
filing_stated_detail.csv DERIVED — module-local companion: every stated figure VERBATIM as
                         printed, BOTH the This-Period and the Year-to-Date column, the cover
                         fields, and the per-filing incremental/cumulative determination
contributions.csv / expenditures.csv   DERIVED — the BORN-DIGITAL itemized layer
                    (32 / 111 rows, 2022+ CFD only; SCHEMA.md §2/§3 + the trailing `geometry`)
build_index.py  regenerates index/excluded/unrecovered from raw/ + text/ + vision/
build_finance.py regenerates filing_totals + filing_stated_detail from index.csv + vision/ + text/
RECON.md        every channel probed, and how
AVAILABILITY.md the coverage matrix, the channel log, and the honest gaps
```

Governance note: Cache County changed form mid-window. **Board of Commissioners** through
the 2018 cycle; **County Council (7) + separately elected County Executive** seated
**January 2019**. Both eras' offices are in scope, so `office` carries `County Commission`
as a legal value even though no legible filing has yet resolved to it — every pre-2019
county-legislative filing that states an office writes some form of "County Council".

## Where it comes from (three channels — full log in `RECON.md`)

1. **The county elections site**, `cachecounty.gov/elections/financial-disclosures/` and its
   per-year pages — the primary channel (155 of the retained index rows).
2. **`disclosures.utah.gov`** Municipal → COUNTIES → CACHE — 46 index rows, including
   **the 2020 cycle, where the state holds 33 filings to the county's 17**. ⚠ The state
   files by the candidate's **town of residence**: Cache's 2018 county filers sit inside
   folders named *Logan*, *Providence*, *Hyde Park* … Never read a state folder name as a
   jurisdiction.
3. **The Wayback Machine** — 38 index rows: the whole **2008** and **2010** cycles (the
   `cachecounty.org` CMS is gone) plus the 2022 page as the county then published it, whose
   filer list is **not** the same as today's 2022 page.

`source_url` always records the **county's own** URL; `wayback_url` carries the archive
wrapper where one was used; `channel` says which of the three served the bytes.

## The vision transcription layer (`vision/*.json`)

The pre-2022 Cache instrument is a **printed Carr Printing 5-5-PG form completed in pen**,
and OCR recovers essentially none of the handwriting. Rendering each page and reading the
image natively is the only channel that can read it. **171 cache files** cover **213 of the
495 ledger rows** (one transcription per distinct document, applied to every byte-identical
copy of it).

- **Key convention:** `vision/<sha1(canonical_path)[:8]>.json`, written ONCE per distinct
  document (by sha256) under the **lexicographically first** of that document's index paths;
  `applies_to` names every ledger row the transcription covers. The 42 cross-channel
  byte-duplicates are therefore transcribed once and applied to both rows.
- **`office_determination`** carries `scope` (county | out_of_scope | undetermined),
  `office_std`, `seat`, a `confidence`, and **`evidence` — a verbatim QUOTE of the page line
  the determination rests on**. That quote is surfaced in `index.csv.office_evidence`.
- **`stated`** carries the filing's own printed totals in one of two shapes:
  `carr_three_column` (the Carr grid's Last | This | Cumulative columns, 147 filings) or
  `cfd_period_ytd` (the 2022+ Summary Page's lettered boxes A–F + Balance at Close, 91).
- Forms seen: `carr_5_5_pg` 122 · `cache_cfd` 42 · `other` 5 (a typed 2020 three-line
  variant, the county's online Jotform, the school-board-titled CFD) · `carr_school_board` 2.
- **DERIVED CSVs are regenerated from these caches — corrections go in `vision/<key>.json`,
  never in the CSVs.**

### Verification standard applied to this layer
Ten adopted transcriptions were re-rendered and re-read against the page image (all exact),
and every `carr_three_column` cache was screened for `last + this = cumulative`. **17 lines
violate that identity, and every one is the FILER's own arithmetic**, already documented
verbatim in that cache's `notes` — **no transcription defect was found.** Two bookkeeping
defects were repaired (`ac2b4174` carried an empty `sha256`; `ac2b4174` and `aeb8719a` each
named only one of their two byte-identical paths); **no transcribed value changed.**

⚠ **Resolution helps legibility; ARITHMETIC decides truth (Rhodes reversal, corrected
2026-08-02).** This note previously taught the OPPOSITE lesson and endorsed the wrong
digit: the Rhodes fax's open-top glyph is bistable at any dpi, a ≥600dpi sibling-copy
read 'settled' it as 4 — and the filing's own arithmetic disproves that (Form A sums to
exactly 1,694.09; the cover closes only under 1: 1,694.09+105.00=1,799.09=cumulative
expenses, balance 0). The published totals were corrected 4,799.09→1,799.09. Rule: on
any disputed glyph, close the document's own arithmetic FIRST; escalate resolution only
for cells no identity constrains.

## How a filing is classified (and why you can trust the label)

Portal labels, filenames and folder names are **never** the authority — a Cache filename is
just what a clerk typed ("A Geary finance campaign.pdf", "2025 Mark Hurd Financial
Docusign.pdf"). Every row is classified from the **document's own printed text or page image**:

- **`form_family`** comes from the printed statutory citation, which survives OCR far better
  than anything handwritten: `carr_county` (Utah Code **17-16-6.5** / Cache County Code 2.21,
  with a "Name of Office" line) · `carr_school_board` (the *separate* instrument citing
  **20A-11-1301..1305**) · `cache_cfd_combined` (the 2022+ "Financial Campaign Report **for
  County Offices and Local School Board Candidates**", which by design does not discriminate
  — only its Office field does) · `campaign_report_variant_unread` / `unclassified`.
- **`office`** is set only from real evidence, and `office_basis` always names it:

  | `office_basis` | rows | what established the office |
  |---|---:|---|
  | `vision_form_field` | 191 | the office line READ FROM THE PAGE IMAGE, quoted in `office_evidence` |
  | `form_field_typed` | 27 | a machine-readable typed Office field in the text sidecar |
  | `sibling_filing_same_cycle` | 7 | the same filer's own other filing that cycle (used only when that cycle yields exactly one office for them) |
  | `election_canvass_join` | 5 | a match against `../elections/cache_county_office_results_long.csv` |
  | `election_canvass_join (other cycle)` + `vision_no_office_printed` | 4 | the page's office line is BLANK; the office comes from the same filer's canvass row in an **adjacent** cycle — a weaker inference, and the basis string says so (David Erickson ×2, D. Chad Jensen ×2) |
  | `vision_no_office_printed` alone | 5 | the page was read and the office line is genuinely blank ⇒ `undetermined` |

- **`scope_status`** states how much is actually known — **read this column, not `office`**:

  | value | rows | meaning |
  |---|---:|---|
  | `county_confirmed` | **234** | an office is established by one of the bases above |
  | `undetermined` | **5** | the page image was read and the office line is blank; nothing else identifies it |

  The old `county_office_illegible` bucket (128 rows — "on the county instrument but the
  office line is unread") is now **EMPTY**: the vision pass read every one of those pages.
  The 5 remaining `undetermined` rows are `2020_st_Scan_3` (an orphan Form-B page),
  Allison Goulais 2024, Frank C. Stewart 2024, Jeff Ostermiller 2024, and Jeffrey
  Wallentine 2026 — in each case the filer left the Office box empty.
- **`candidate`** is cross-checked between the document's typed name and the clerk's own
  file label; on a surname disagreement the clerk label is kept as `candidate` (it is the
  stable ledger key) and **the document's own spelling is preserved in
  `filing_stated_detail.csv.candidate_stated`** — e.g. the ledger's *Devron Anderson* signs
  his 2024 filing *Devron Andersen* in all four hand-written instances.
- **`needs_review=1`** on the 5 rows that are not `county_confirmed`.

### What the vision pass re-classified OUT (11 rows)

The county instrument **false-positives** — a clerk hands the blank county form to a
municipal, school-board or special-district candidate — and only the office the filer WROTE
decides scope. Reading the pages moved 11 rows to `excluded.csv`, each carrying its quoted
page evidence in `exclusion_reason`: **School Board** 6 (K./Katherine Christiansen 2012 ×2,
Allen Grunig, Brian Chambers, Dennis Jeffrey Nielsen, Katie Chapman 2024) · **Municipal** 2
(Matt Funk 2012 — "Justice Court Judge") · **Special District** 2 (Bethany Nielson 2022) ·
**State Legislature** 1 (Greg Merrill 2018).

### The two known-suspect rows are ADJUDICATED

**Kevin Rhodes (2016)** and **Shannon Rhodes (2018)** were held at `county_office_illegible`
because *Rhodes* is also a Cache County **School Board** surname. Both pages were read:
each writes **"Cache County Council"** on its own Name-of-Office line (Kevin — district
"North", Democrat; Shannon — district "Northeast", Democratic). Both are now
`county_confirmed / County Council`, on page evidence, not on the instrument.

### The 2026 school-board suspicion is FALSIFIED
`AVAILABILITY.md` previously guessed that the 2026 column's `undetermined` rows — Chris
Daines, David Gillie, Jeffrey Wallentine — were the missing school-board filers. Their
pages say otherwise: **Chris Daines writes "County Attorney"**, **David Gillie writes
"Cache County Clerk"** (on both his April and June filings), and **N. George Daines writes
"Cache County Executive"**. Only Wallentine's office line is blank. If 2026 school-board
filers exist, they are not these.

## The money layer — what exists and what does not

**Each filing's own STATED TOTALS are transcribed. NO ITEMIZED ROWS ARE.**

- `filing_totals.csv` — 239 rows, the shared SCHEMA.md §4 column contract exactly.
  **210 rows carry a stated contributions figure, 212 a stated expenditures figure**,
  202 an ending balance, 83 a beginning balance. Extraction confidence: high 135 ·
  medium 103 · low 1. Only **1 row of 239 has no stated totals at all** (the orphan
  Form-B page).
- `filing_stated_detail.csv` — the module-local companion holding every figure **verbatim
  as printed**, both the This-Period and the Year-to-Date column, the cover fields
  (office_verbatim, party, residence city, report type, date signed, received stamp), and
  the per-filing `period_basis` / `is_incremental` determination. The shared §4 column list
  is fixed, so the verbatim + two-column detail cannot live in `filing_totals.csv`.
- `contributions.csv` / `expenditures.csv` — **the BORN-DIGITAL itemized layer** (built
  2026-08-02, TRANCHE 3 Phase A): **32 contribution + 111 expenditure rows over 21 filings**,
  all 2022+ CFD, parsed by the registered `cache_cfd` family from the born-digital text layer.
  **Every emitted side reconciles EXACTLY (±$0.01) to the stated total this module already
  published** — a side that does not reconcile emits **nothing** and says why in
  `filing_totals.notes` / `filing_stated_detail.notes`. No stated total was recomputed.
  Every row carries `geometry` (`p<page>:l<line>:c<col0>-<col1>`, SCHEMA.md §2a) pointing at
  the amount cell it was read from — 100% coverage. Parsing is keyed on **`sha256`**, so a
  cross-channel byte-duplicate is parsed once and applied to every index row sharing those
  bytes. Rows carry `donor_city` / `donor_state` only; the street portion of the free-typed
  address is discarded by `common.split_city_state` and never stored.
  **The handwritten Carr era (pre-2022) itemizes nothing** — that is NOT TRANSCRIBED, never
  "no donors", which is why those `reconciles_*` stay blank (unknown) and never `False`.
  To ask "who gave to X" outside the born-digital subset, open the raw PDF.

### `is_incremental` is a property OF EACH FILING here, not of the county
Cache's 2022+ form prints **both** a "This Period" and a "Year-to-Date" column, so whether a
report is incremental is fixed per filing and recorded in `filing_stated_detail.period_basis`:
`carr_cumulative_column` 147 (the Carr form's third column IS the whole-cycle-to-date figure
⇒ cumulative) · `period_equals_ytd` 58 (first/only report of the cycle — the two readings
coincide) · `period_and_ytd_differ` 24 (genuinely incremental) · `period_only` 3 ·
`ytd_only` 3 · `neither` 3. **Never sum across filings without reading this column.**

## Caveats / do-nots

- **Never sum rows without grouping on `sha256`.** 42 index rows are byte-identical copies
  served by a second channel (82 rows sit in a duplicate group; **197 distinct documents in
  239 rows**). They are kept because three publications of one filing are three real facts.
  Counting rows without grouping overstates filing volume by roughly a sixth.
- **The stated totals are NOT a fundraising ledger.** Summing them (deduped by sha256) gives
  ≈ **$346,104 contributions / $476,620 expenditures across 181 filings** — a *magnitude*,
  not a sanctioned total: filings within a cycle overlap (interim + final), the two form
  families count differently, and 29/27 rows carry no figure at all. There is no
  `cf_cycle`-equivalent here. **Do not publish a per-candidate total from this file.**
- **Nothing is computed for the filer.** Where a filer's own arithmetic disagrees with
  itself, both figures are retained verbatim and the disagreement is stated in `notes`
  (17 such lines across the Carr set; e.g. Shannon Rhodes 2018 writes 1,694.09 in the
  This column and 4,694.09 in the Cumulative box of the same line).
- **A printed word is not a number.** "None" / "-0-" become a decimal zero only when the
  word IS a stated zero; "NA"/"N/A" means *not applicable* and stays blank.
- **`date` is a filing date only where `date_precision='exact'`.** `date_source` tells you
  which: `archived_listing_row` and `filename` are the filer's own dates; **`cms_posting_date`
  is when the CMS posted the file, not when it was filed.** Cache **re-uploaded its entire
  2022 set on 2025-07-29** during a site migration, so those rows fall back to cycle-year and
  park 2025-07-29 in `listing_posted_date`.
- **`reporting_period` is inferred** from the filename/label or the month — a convenience
  label, not a value the form printed.
- **Odd-year pages are not odd-year filings.** The 7 filings on the county's **2025** page
  are **2026-cycle County Executive** C&E reports, indexed `election_year=2026`.
- **Annual conflict-of-interest statements (17-16a) are out of scope** and were not
  harvested; the county publishes them on separate pages.
- **School-board filings are retained but excluded**, not deleted — `excluded.csv` + `raw/`
  hold all 237 with full provenance, consistent with the owner's 2026-08-01 ruling that
  county school-board CF is ledgered and out of scope. Cache County School District is not
  a registered entity in this repo, so nothing consumes them today.

## Join to the rest of `cache_county`

- **To elections:** `index.csv.candidate` ↔ `../elections/cache_county_office_results_long.csv`
  `candidate`, on person + cycle. Canvass names are UPPER-CASE and carry a party prefix
  (`REP JOHN D. LUTHY`) or a write-in wrapper (`Write-In: MARC ENSIGN`) — strip both, then
  match on first-initial + surname. `build_index.py` already does this.
- **To votes:** from an elected filer, join `../db/cache_county.db` `person` → `vote`. Bear
  the entity's own caveat: named roll calls exist **2021+**; 2015–2020 is tally-only.
- **County Executive does not vote** (Council–Executive form) — a County Executive filer will
  have campaign finance but no `vote` rows, and that is correct, not a gap.

## The shared family — `cache_cfd`, REGISTERED and WIRED (2026-08-02)

The family this section used to describe as a need now exists:
`scripts/campaign_finance/families/cache_cfd.py`, registered in the shared registry and
unit-tested against this county's own sidecars (Hurd Apr-3 `397.76`/`613.88` dash style;
Hurd Jun-16 `316.72`/`508.83` whitespace style + the per-filing `period_basis`). Both driver
capabilities it needed shipped with it: the **" - " tokenizer** for free-typed one-liners
(`3/18/26 - Mark Hurd - 168 S 50 W Hyde Park, UT - $12.42`) and a **PER-FILING** regime read
off Box B vs Box C.

`build_finance.py` remains **module-local** — 201 of 239 filings are the handwritten Carr
form whose figures exist only as vision transcriptions, and `driver.run()` would rewrite all
three CSVs from one parse pass. It calls the family directly for the born-digital subset,
through the same shared normalization + reconciliation primitives the driver uses, so the
outputs stay inside the shared contract. The pre-2022 Carr era is handwriting — not
parseable by any text pipeline, which is exactly why the vision layer exists, and it is
**Phase B (vision) work**, not a gap this family can close.

**Measured, 2026-08-02:** 38 filings entered the born-digital pass; **7 contribution sides
and 19 expenditure sides reconciled exactly** and shipped (21 distinct filings carry rows).
Every other side emitted nothing with a stated reason — either the face itemizes nothing the
family reads cleanly (reconciliation UNKNOWN, never a fabricated mismatch) or the parsed rows
did not sum to the printed total, in which case they are **withheld**, not published.

## Rebuild

```
python3 build_index.py     # index/excluded/unrecovered  <- raw/ + text/ + vision/ + listing_labels.csv
python3 build_finance.py   # filing_totals + filing_stated_detail + the born-digital
                           # contributions/expenditures  <- index.csv + vision/ + text/
python3 ../../scripts/campaign_finance/validate_finance.py .   # PASS (0 fails, 0 warns)
```
Run in that order — `build_finance.py` reads `index.csv`. All five CSVs are **DERIVED —
regenerate, never hand-edit.** `raw/`, `text/`, `vision/`, `raw/_fetch_log.jsonl` and
`listing_labels.csv` are the canonical inputs.

**Federation:** cache_county CF is **document-tier in `gov.db`** — no `cf_*` rows are loaded
from here, and the entity carries a `cf-document-tier` caveat. That caveat's text was
corrected on 2026-08-02 to match this state and **takes effect only at the next
`scripts/build_cities_db.py` run, which the repo owner performs.**
