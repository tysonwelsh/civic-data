# campaign_finance/ — Wasatch County county-office campaign finance

**As-of 2026-08-01.** The first dataset built for `wasatch_county`, which is otherwise a
**REGISTERED-ONLY** entity (registry row since 2026-07-20, carrying Park City's second
within-county edge; no db, no vote layer, no federation). Nothing here is in `gov.db`.

## What this is

**111 campaign-finance reports** filed by candidates for **Wasatch County COUNTY offices** —
County Council, Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer, Surveyor —
across the **2010, 2018, 2020, 2022, 2024 and 2026** cycles (61 distinct candidate-cycles).
Raw PDFs are retained verbatim in `raw/<year>/`; a text sidecar per filing is in
`text/<year>/`; one index row per filing is in `index.csv`.

**School board is out of scope** (32 filings identified and catalogued in `out_of_scope.csv`,
never fetched).

**A STATED-TOTALS layer exists as of 2026-08-01** — `filing_totals.csv`, 111 rows, built from
111 curated `vision/<key>.json` cover-page transcriptions. **Donor/vendor itemization is
BORN-DIGITAL ONLY and very thin — 8 expenditure rows over 2 filings, 0 contribution rows**
(TRANCHE 3 Phase A, 2026-08-02; see "The born-digital itemized layer"). See "The stated-totals
layer" below.

```
RECON.md              channels probed + every negative, with reasoning     ← read first
AVAILABILITY.md       coverage matrix, per-cycle sourcing, the gap ledger
index.csv             one row per retained filing (22 cols; schema below)
unrecovered.csv       5 known-missing 2024 general reports (dead everywhere)
out_of_scope.csv      32 school-board filings identified but not fetched
text_extraction.csv   per-file text-extraction manifest (format + method)
raw/<year>/           the filing PDFs + per-year _fetch_log.jsonl (url, bytes, sha256, utc)
raw/index_pages/      the 10 LISTING pages the map was read off (live + Wayback) + fetch log
text/<year>/          one .txt per PDF (pdftotext -layout, or 300dpi tesseract)
vision/<key>.json     CURATED — one cover-page transcription per filing (111). `<key>` =
                      sha1(index.csv `path`)[:8]. Schema below; corrections go HERE.
filing_totals.csv     DERIVED — one row per filing (111), SCHEMA.md §4 + `filing_regime`
contributions.csv     DERIVED — SCHEMA.md §2 (+ `geometry`); 0 rows — every parsed Table-A
                      section was field-shifted and withheld (see below)
expenditures.csv      DERIVED — SCHEMA.md §3 (+ `geometry`); 8 rows over 2 born-digital filings
build_finance.py      rebuild the three CSVs from index.csv + vision/    (idempotent)
refetch.py            verify every retained PDF against index.csv sha256 (currently 111/111)
extract_text.py       rebuild text/ + text_extraction.csv
build_index.py        rebuild index.csv / out_of_scope.csv / unrecovered.csv
```

## `index.csv` schema

| column | meaning |
|---|---|
| `date` | filing-period **proxy** (`YYYY-MM-DD`). Exact where the source states it (2010, the 2024 state copy); otherwise the first of the statutory reporting month. **Not** the signature date — that is inside the PDF. |
| `candidate` | filer name as published by the county. |
| `office`, `seat` | assigned from **the county's own candidate listing for that cycle** (`raw/index_pages/`), because the PDF's *Name of Office* field is usually handwritten. Where the listing was silent, from the form field itself. |
| `election_year` | 2010 / 2018 / 2020 / 2022 / 2024 / 2026. |
| `filing_type` | `statement` (all — these are full reports, not separate schedules). |
| `reporting_period` | the statutory filing point as published (e.g. `June 2020 (7 days before Primary)`, `General 2022`, `March 2026 (Partisan Convention Report, due 3/31)`). |
| `source_url` | the **government's own** URL (county origin, or `municipal.utah.gov` for the state copies). |
| `archive_url` | populated **only** for the 7 filings recovered via the Internet Archive; blank means origin-fetched. |
| `form_family` | **the vision-read variant** (coordinator fix 2026-08-01 — `build_index.py` now sources this column from each filing's `vision/<key>.json._meta.form_variant_vision`, retiring the statute-header classifier that misfiled 6 rows): `wasatch_disclosure_tableab` (49) / `wasatch_fcr_3line` (45) / `carr_5_5_pg_4line` (17). Agrees with `filing_totals.filing_regime` by construction. |
| `format` | `text` (71 born-digital / AcroForm) / `scanned` (40 image-only). Measured from the actual text layer, not the extension. |
| `extraction_method` | `pdftotext -layout` or `tesseract OCR (pdftoppm 300dpi, psm 6)`. |
| `path`, `text_path` | repo-relative PDF + sidecar. |
| `pages`, `bytes`, `sha256` | integrity triple; `refetch.py` checks the digest. |
| `channel` | `origin` (104) / `wayback` (6) / `wayback_latest` (1). |
| `needs_review` | `1` on every row. This predates the stated-totals layer and now means only *"itemized rows not transcribed / nothing reconciled"* — the **cover-page stated totals HAVE been transcribed** (see `filing_totals.csv`). |
| `notes` | per-row caveats (5 rows): the Farrell double-checkbox, the state-site copy, the untimestamped Adams recovery, the two undetectable form families. |

## The three things to get right before querying this

1. **THREE form variants, and the seam is the 2022→2024 CYCLE BOUNDARY — not mid-2024.**
   Every one of the 111 covers was read by vision on 2026-08-01, and the split is clean:

   | variant (`form_variant_vision`) | cycles | n | shape | regime |
   |---|---|---:|---|---|
   | `carr_5_5_pg_4line` | 2010, 2022 | 17 | Carr `FINANCIAL CAMPAIGN REPORT` + Form A/B, **4 lines** (>$50, ≤$50 aggregate, expenses, balance) × 3 columns; statute **17-16-6.5** | cumulative |
   | `wasatch_fcr_3line` | 2018, 2020 | 45 | Wasatch's own typed `FINANCIAL CAMPAIGN REPORT`, **3 lines** × 3 columns; statute misprinted **17-15-6.5** | cumulative |
   | `wasatch_disclosure_tableab` | 2024, 2026 | 49 | `CAMPAIGN FINANCIAL DISCLOSURE` + Table A/B, **one TOTALS column** + a reporting-period checkbox list | period-scoped |

   **The earlier "2024 is mixed (4 old / 16 new)" reading is FALSIFIED by the documents.** All
   21 of the 2024 filings are on the new Table A/B sheet. The mislabel has a cause worth
   knowing: **the 2024 vintage of the NEW sheet still cites Utah Code 17-16-6.5** (only from
   2026 does it cite 17-70-4 for anonymous-donation disposition), so a statute-header classifier
   reads it as the old county form. That classifier misfiled 6 rows (`202403_state_Adams`,
   `202406_BobAdams`, `202406_JamiSmithHewlett`, `202406_ToddGriffin` labelled old-but-new;
   `202406_ToriBroughton` blank-but-new; `2020_OctJGranger` blank-but-three-line) — **FIXED
   2026-08-01**: `build_index.py` now takes `form_family` from each filing's vision cache
   (`form_variant_vision`, the page-read evidence), so `index.csv`, `filing_totals.filing_regime`
   and the caches agree by construction.
2. **The variants mean different things by "a report", so a cycle total is a different
   computation on each.** The two older sheets are **cumulative** — a three-column
   `TOTALS FROM LAST REPORT + TOTALS FOR THIS REPORT = CUMULATIVE REPORT` box — so a candidate's
   cycle figure is the **latest** report and summing their filings double-counts (ground truth:
   Granger 2022-11-01, $0 / $0 / $450 expenses / −$450). The new sheet is **period-scoped**;
   three filers say so in their own hand — Woodard 2026-06 annotates lines 1 and 2 *"since last
   report"*, Forsyth 2026-06 prints *"(balance of $1,263.82 in campaign bank account from prior
   contributions previously reported)"*, and Bonner's 2024 general covers *"Sep 26 to Oct 24"*
   ($700 raised / $3,612.69 spent). So a cycle figure there is a **sum** across periods —
   **except** where a filer restates cumulatively anyway (Kaiserman 2024 June and general both
   print 653.00/653.00/0; Rowland 2026 and Farrell 2026 both repeat their March totals in June).
   Those are called out in each row's `notes`; read them before summing.
   **2020 is the trap year**: 3 reports per candidate, all cumulative — take December, do not
   add June + October + December.
3. **The stated totals are transcribed; the donor rows almost entirely are not.**
   `filing_totals.csv` carries what each cover PRINTS. Only **2 of 111 filings** carry any
   itemized row (8 expenditures, Murphy 2026-03 and Forsyth 2026-06); `reconciles_*` is blank
   on the other 109 — **unknown, not a match**. To quote a donor, open the PDF.

## The born-digital itemized layer (TRANCHE 3 Phase A, 2026-08-02) — and why it is 8 rows

The registered `wasatch_disclosure_tableab` family was wired into `build_finance.py` for the
**49 Table A/B filings**, selected on the VISION-read `_meta.form_variant_vision` — **never the
statute header**, which is the exact mistake that mis-filed 6 rows until 2026-08-01 (the 2024
vintage of the NEW sheet still cites 17-16-6.5).

| | count |
|---|---:|
| Table A/B filings handed to the family | **49 of 111** |
| contribution sides shipped | **0** |
| expenditure sides shipped | **2** (Michael Murphy 2026-03 · Lauren Forsyth 2026-06) |
| rows emitted | **0 contributions · 8 expenditures** (100% carry `geometry`) |

**Why so little, stated honestly:**

- **Most Table A/B covers have no readable ledger on their text layer at all.** The family
  refuses to turn a garbled cell into a number — Bonner's 2024 general prints `$ f -7 DD.oo`
  and `r Vbi&/"q` where $700.00 / $3,612.69 belong — so those filings emit nothing and their
  real figures stay where they are, in `vision/`.
- **FIELD SHIFT — the finding of this pass.** On Woodard 2026-03, Kellogg 2026-03 and Vance
  2026-06 the family put the **date token in the NAME column** and slid the real name into the
  next field (`donor_raw = "17 Jan 2026"`, `"1.2.26"`, `"5May26"`), because those filers write
  dates in formats its grammar does not know. **The amounts still summed EXACTLY to the printed
  totals**, so reconciliation could not catch it — which is precisely why this module screens
  every parsed side for mis-columned rows before publishing. Where **≥50% of a side's rows are
  shifted the whole side is WITHHELD** (a systematically mis-columned ledger is a wrong value,
  not a rough one); an isolated shift would be kept and flagged. Here every affected section was
  100% shifted, so all 3 contribution sides and 3 expenditure sides were withheld.
  **FAMILY LIMITATION, documented not patched** — the shared engine is frozen this phase, and a
  date-grammar extension is queued for Phase B. Each withheld side names itself in
  `filing_totals.notes`.
- **Rowland 2026-06's Table B is OCR noise** (`| es | |`, `a es es eee`) from which the family
  produced one letterless row that happened to equal the stated total. Withheld by the same
  screen.
- **MULTI-REPORT PDF:** `raw/2024/202411_732_s-park-general.pdf` binds **two** CAMPAIGN
  FINANCIAL DISCLOSURE reports in one file. The family reads ONE face per parse, so the second
  report is **gated out with a reason** and flagged for Phase B — never merged into the first
  report's totals.
- **Cover divergences are recorded, never resolved.** Where the family reads a different cover
  figure than the vision transcription (e.g. Bob Adams 2024-03: family 252.68 vs published
  9,832.68), the **vision figure governs** and the disagreement is written into `notes`.
- **0 of 111 `stated_*` values changed** in this pass.

## The stated-totals layer

`filing_totals.csv` (111 rows) is DERIVED — **regenerate, never hand-edit**:
`python3 wasatch_county/campaign_finance/build_finance.py`. Corrections go in the
`vision/<key>.json` cache, with a note saying what was re-read at the source.

- **`filing_regime`** (the optional trailing SCHEMA.md column) is `cumulative` (62) or
  `period` (49), taken from the variant. It is the semantics an itemized tranche would carry as
  `is_incremental`: **cumulative ⇒ `is_incremental=False`** (latest report wins),
  **period ⇒ `is_incremental=True`** (sum across periods).
- **Column selection on the cumulative sheets** is deterministic and documented in
  `build_finance.py`: use the CUMULATIVE column when it prints a figure; else, if the LAST
  REPORT column is blank/0/`N/A` (nothing precedes this report), promote THIS REPORT and say so
  in `notes`; else leave the total BLANK. All three columns stay verbatim in the cache.
- On the four-line Carr sheet a contribution total is **line 1 (>$50) + line 2 (≤$50
  aggregate)**, summing only the cells the filer actually printed (the juab precedent).
- **`stated_ending_balance` is VERBATIM** — parentheses (`(331.75)`), a stray `$-`, even
  Forsyth's parenthetical prose. `stated_total_contributions`/`_expenditures` are normalized to
  decimals only because the validator requires it.
- **`extraction_confidence`**: 103 `high`, 6 `medium`, 2 blank (nothing stated to read). Per-cell
  confidence lives in the cache, so a single shaky digit does not downgrade a whole filing
  silently.

### `vision/<key>.json` schema

```
_meta   index_path, cache_key, election_year, reporting_period_index,
        form_family_index (what index.csv says) vs form_variant_vision (what the page IS),
        form_statute_verbatim, filing_regime, is_incremental, tranche, source,
        pages_read, text_layer_corroborated_lines, transcribed_by, transcribed_utc
cover   candidate/office/district/party/residence_city/addressee/signature_date, each
        {value, confidence}; `signed`; `report_periods_checked` — verbatim box labels, where
        `null` = the variant prints NO period selector (2010/2022 Carr) and `[]` = a selector
        is present and nothing is marked; `convention_date_verbatim`
stated  per printed line -> per COLUMN cell {value, confidence}.
        cumulative variants: last_report / this_report / cumulative
          carr_5_5_pg_4line: contrib_gt50, contrib_le50, total_expenses, balance_end
          wasatch_fcr_3line: total_contributions, total_expenses, balance_end
        period variant: a single `period` cell
          wasatch_disclosure_tableab: total_contributions, total_expenditures, balance_end
itemized_transcribed  false everywhere (this tranche)
notes   per-filing verbatim observations
```
`value` is the string **as printed** (`"N/A"`, `"(331.75)"`, `"250."`); `""` = the cell is blank
on the face. `confidence` is per cell: `high` / `medium` / `""` (blank cell).
`text_layer_corroborated_lines` lists the lines whose transcribed figure also appears verbatim
in the born-digital `text/` sidecar — an independent, automatic cross-check (it is empty for the
scans and for handwriting, which is expected, not a defect).

### Still not built

`contributions.csv` / `expenditures.csv` rows, `cycle_totals.csv`, `donor_aliases.csv`,
`finance_overrides.csv`, and any `gov.db` federation. A shared form-family module for either
Wasatch sheet is still absent from `scripts/campaign_finance/families/` — both sheets were
tested against `millcreek_form` and `utah_standard_form` and returned 0 rows and no totals —
and adding one means editing shared code, which is outside this module's write scope.

## Provenance notes worth carrying

- **104 of 111 filings came from the government's own origin host.** The DNN host
  `wasatch.utah.gov` still serves its `Portals/` PDFs even though its pages now redirect to the
  CivicPlus site — so 2018/2020/2022/2024-June are origin-fetched, not archive-recovered. Only
  the 2024 general reports (retired Jadu CMS) required Wayback.
- **The county's own 2018/2020 form misprints its statute as `17-15-6.5`** (correct: 17-16-6.5).
  Retained verbatim — a source typo is data, not an error to fix.
- **A portal label can contradict the filing.** `S. Farrell Elimination Report` (2026-06) has
  BOTH the *Partisan Convention* and the *Withdrawal/Elimination* boxes checked on the form.
  Recorded as published + flagged in `notes`; not silently resolved.
- **The Farrell double-checkbox is not unique — "select only one" is widely ignored.** Of the
  **94 filings whose sheet even has a reporting-period selector** (the 17 Carr-form filings of
  2010 and 2022 print none at all), **6 mark more than one box** — Kaiserman 2024-06
  convention+primary, Park 2024-06 convention+primary, Bonner 2024-11 Sept-30+general,
  Kaiserman 2024-11 convention+general, Park 2024-11 Sept-30+general+year-end, Farrell 2026-06
  convention+elimination — and **13 mark none at all** (2018 Sweat; 2020 Griffin ×2; 2024 Gibbs,
  Adams-June, Hewlett ×2, Murray-general, Nelson, Bercuson-general; 2026 Granger-March,
  Murphy-March, Kahler-March). All are verbatim in
  `vision/<key>.json.cover.report_periods_checked`, where **`null` = the form prints no selector**
  and **`[]` = a selector is present and nothing is marked** — and each is flagged in the
  filing's `notes`. `index.csv.reporting_period` remains the county's published filing point.
- **Two filings' checked box contradicts the filing point index.csv assigns them:** Xela Thomas
  2020-06 checks *30 Days after withdraw or elimination* on a report published at the June
  pre-primary point, and Karl McMillan 2026-03 checks *Candidate Withdrawal/Disqualification/
  Elimination* on one published at the March partisan-convention point. Both kept as published
  and noted.
- **School-board and county candidates file the same form, to the same clerk, in the same
  folder.** Only the statutory citation (17-16-6.5 vs 20A-11-1301) or the *Name of Office* field
  separates them. That is how `out_of_scope.csv` was built, and it is why
  `disclosures.utah.gov/Municipal/wasatch_2012 Primary` — which looks like six county filings —
  is a county-office **zero**.
- **Privacy** follows the repo policy (root `PRIVACY.md`): `raw/` and `text/` are **verbatim
  reproductions of government-published documents and are not redacted**, including donor
  addresses printed on the face of a filing. Should a structured layer ever be built here, its
  rows must carry **donor city/state only**, never street addresses.

## Cardinal-rule specifics for the totals layer

1. **Blank is data, and it is never a zero — EXCEPT a glyph that denotes zero (owner ruling
   2026-08-02).** A slashed zero `Ø`, `-0-`, or the written word "zero" IS the filer writing
   the digit 0 and promotes to 0.00 (verbatim glyph kept in the cache): **Kahler 2026-03**'s
   Table A total, printed as the word *"zero"*, now yields `stated_total_contributions=0.00`
   (CORRECTED 2026-08-02: Table B CONTINUES to page 3, whose TOTAL row also prints 'zero' — found independently by both pilot contenders + the coordinator's page read; stated_total_expenditures=0.00 too. Only the balance stays blank — nothing states it). Everything else stands: 3
   filings state no contribution total and 3 no expenditure total, each with its reason in
   `notes` — **Hewlett 2024-06** writes `N/A` in all three cells; **Woodard 2026-06** puts a
   dash in the expenditure cell; **Jenkins 2020-06** and **Farrell 2020-06** fill only some
   lines. A non-zero-denoting non-number (`N/A`, a bare dash, an up-arrow *see-above* mark)
   is BLANK.
2. **Filer errors stand as filed.** Farrell 2020-12 prints a cumulative contribution total of
   3332.96 against 3337.96 on his own expense and balance lines; Wade 2018 prints a positive
   balance against zero contributions and $1,004.74 of expenses; Sweat 2022 prints the same
   $650.08 negative in June and positive in November; Granger 2020-06 states a NEGATIVE expense
   (−246.08); Adams 2024-11 prints a $135.55 balance against zero-and-zero; Rowland 2026-03
   prints a positive balance where the arithmetic is negative. None were corrected.
3. **Strikeouts are transcribed to the value that survives, and the fact is noted** —
   Yergensen 2010 (over a struck 535.36), Titcomb 2018 and Hewlett 2024-11 (a struck figure
   replaced with a circled 0), Farrell 2020-10 (party written over a struck "Republict").
4. **Two filings are published unsigned/undated** — McDonald 2010 (no signature) and
   Crittenden 2020-12 (neither signature nor date). Recorded in `cover.signed`.
5. **Never surname-join.** Several filers recur across cycles and offices, and two 2024 filers
   share a first name with a different 2020 filer. Resolve on full name (repo-wide rule); note
   also that `index.csv.candidate` is the county's published spelling while
   `vision.cover.candidate_verbatim` is the form face — they differ (e.g. "Joey D. Granger" vs
   "Joey Diane Granger", "Jami Smith Hewlett" vs "Jami Hewlett").
6. **`PRIVACY.md`:** campaign-finance text is never redacted, but the derived CSVs carry no
   street addresses or phone numbers — only `residence_city` in the cache. The `raw/` scans are
   unaltered.

## Joins (what is and is not possible today)

There is **no `wasatch_county` election-results layer, no roster, and no db** — the entity is
registered-only. Within this module, join on `candidate` + `election_year` (+ `office`/`seat`).
Cross-entity, the useful edge is **Park City**, which straddles Summit and Wasatch; Park City's
canvass is run by **Summit** (`summit_county/elections/`), so nothing here joins to it directly.
Note also that several filers recur across cycles and offices (Granger 2020/2022/2026;
Rigby 2018-declaration/2022/2026; Sweat 2010/2018/2022; Crittenden 2018/2020/2024;
Rowland 2022/2026) — resolve people by **full name**, not surname (repo-wide rule).

## Refresh

The 2026 cycle is **open**: general reports are due **2026-10-28** and finals **2026-12-03**.
Re-run after December 2026 against `wasatchcounty.gov/elections`, then
`python3 extract_text.py && python3 build_index.py && python3 refetch.py`.

New filings need a **vision cover transcription** before they appear in `filing_totals.csv` —
`build_finance.py` HARD-FAILS on any `index.csv` row without a `vision/<sha1(path)[:8]>.json`
cache (silence is not an option here). Transcribe with `/cf-vision-transcribe` (Read-tool
method, $0 API), then `python3 build_finance.py && python3
scripts/campaign_finance/validate_finance.py wasatch_county/campaign_finance`.
