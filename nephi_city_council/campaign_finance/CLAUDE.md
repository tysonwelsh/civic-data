# Nephi City — campaign_finance (how to use this dataset)

Additive expansion dataset: **campaign-finance disclosures for Nephi municipal
candidates**, completing the **elections → members → votes** chain (who funded the people
casting the votes). Built by the `expand-city-sources` skill (source type 6). As of
**2026-07-05**. Read `AVAILABILITY.md` for coverage, hosts tried, and gap flags.

This directory is BOTH the filing-level document archive + index AND (as-of **2026-07-06**)
a **structured contribution / expenditure / filing-totals layer** — see "## Structured layer"
below. The raw PDF remains the authoritative record; the structured CSVs are DERIVED and every
figure is reconciled or honestly flagged, never asserted beyond what the form prints.

## Layout

```
raw/          27 retained scanned PDFs (cf_<viewid>_<slug>.pdf) + _fetch_log.jsonl (provenance)
text/         one OCR text sidecar per raw PDF (search aid only — noisy handwriting OCR)
index.csv     43 filing-level rows (some raw compilations split into per-candidate rows)
build_index.py  regenerates index.csv (idempotent); encodes the compilation page→candidate maps
AVAILABILITY.md hosts/URLs tried, per-cycle coverage, discrepancy flags
```

## index.csv columns

Required six: `date, title, source_url, retrieved_date, format, extraction_method`.
Plus: `candidate` (UPPER-CASE, matched to `election_results/nephi_results_by_candidate.csv`),
`office` (Council/Mayor), `election_year`, `filing_type` ∈ interim/summary,
`reporting_period`, `path` (`raw/…`), `candidate_match`, `date_precision`, `view_id`,
`page_range` (for rows split out of a multi-candidate compilation), `notes`.

- `format` = **scanned** for every row (all filings are scanned handwritten forms).
- `candidate_match`: `matched` (exact join to election_results) / `inferred` (attributed
  by elimination, name illegible) / `ocr_uncertain;not_in_election_results` (a name OCR
  read that is NOT in the elections roster — see flag) / `unreadable` (present but
  un-attributed).
- `date_precision`: `exact` (from a Canon scan CreationDate or a dated form) /
  `inferred` (election-cycle-anchored) / `batch_inferred` (from the reporting-round
  upload batch, anchored by a date-stamped file in the same batch).

## How to analyze

- **Filings by candidate/year:** filter `index.csv` on `candidate` + `election_year`.
  A candidate may have several rows in one year (2025 candidates filed up to 4 reporting
  rounds: pre-primary, two pre-general, final).
- **Join to the votes chain:** `candidate` is already in the election_results UPPER-CASE
  form → join on `(election_year, candidate)` to `nephi_results_by_candidate.csv`, then
  winners → `meeting_minutes/all_votes.csv` mover/seconder (at-large, join by person +
  year; no district key). **40/42** attributed rows join; **22/24** distinct
  `(year,candidate)` pairs (92%).
- **Multi-candidate compilations** (2019 has none; 2021 View 2118; 2023 Views 2706/2803)
  are split into per-candidate rows that share one `path` and carry a `page_range`. Open
  the raw scan at that page range for the actual form.

## Caveats (read before quoting anything)

1. **Handwritten scans.** The printed form template OCRs cleanly; **handwritten values
   (names, dollar amounts, dates) do not.** The `text/` sidecars are a search aid — the
   **raw PDF is authoritative**. Do not report a contribution/expenditure dollar figure
   from the OCR without eyeballing the scan.
2. **Worwood ambiguity — never merge.** SKIP F. WORWOOD (2021, 2025) ≠ TRAVIS L WORWOOD
   (2023). Distinguished by first token.
3. **2023 primary gap is a flag, not a fix.** View 2706 shows more 2023 filers than the
   elections dataset records (incl. OCR-read names not in the roster). `election_results`
   is left unchanged; the discrepancy is documented in `AVAILABILITY.md`. Do not "correct"
   election_results from finance filings.
4. **Conflict-of-interest / ethics disclosures are out of scope** and excluded (they live
   on the same DocumentCenter pages). See AVAILABILITY.md "Out of scope."
5. **Cardinal rule:** honest gaps are data. Un-attributed pages and non-joining names are
   recorded as such, never fabricated.

## Refresh

Re-fetch the three nav pages, diff `DocumentCenter/View/<id>` links against `index.csv`
`view_id`, fetch new ids via `polite_fetch.py`, OCR to `text/`, extend `build_index.py`,
re-run it, and re-validate. Newer cycles will add higher View ids under `/680/Disclosures`.

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-06

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`.
Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent).
Validate: `python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS** (0 fails).

- **contributions.csv** 50 rows · **expenditures.csv** 141 rows · **filing_totals.csv** 42 rows.
- **SCOPE — 42 of the 43 index rows are in-scope campaign C&E reports.** The one excluded row is
  the un-attributable 2023 compilation entry (candidate "(unidentified filers)", 3 forms with
  illegible handwritten names, `page_range 9-10,15-16,19-20`): attributing those dollars to a name
  we cannot read would fabricate identity, so it stays document-archive-only (honest gap, still in
  `index.csv`). `driver.run(in_scope_fn=…)` skips it → "out-of-scope skipped: 1".

### Form family — `utah_standard_form` REUSED (Orem's family, unchanged; Logan's recipe)
Nephi files the **same statutory Utah municipal "Campaign Financial Report" form (UCA 10-3-208)**
Orem/Logan use, so it **reuses `families/utah_standard_form.py` UNCHANGED** (no family edit; all 6
prior cities re-validate + re-build identically). Nephi is the **same class as Logan** — ALL
handwritten scans, no per-section printed TOTAL, totals stated only in a numbered COVER block — so
it copies Logan's `form_opts` recipe verbatim, in `build_finance.py`:
- **Section headers SENTINELED OFF** (`sec_cashc/inkind/cashe=(?!)`): the itemized "Form A/B"
  amounts are handwritten WITHOUT a `$`, so the anti-fabrication money tokenizer reads 0 rows from
  OCR; detecting a section but reading 0 `$`-rows would falsely coerce its total to $0 and
  reconcile a real filing as nil. Suppressing detection forces the cover-total anchor + vision rows.
- **Numbered COVER block = reconciliation anchor.** `l1←itemized contributions`, `l2←under-$500
  aggregate`, `l3←itemized expenditures`; `stated_contrib = l1+l2` (family headline fallback). The
  `l1/l2/l3` regexes cover BOTH Nephi form layouts: the older Carr-Printing form (2019/2021/2023:
  "Contributions received totaling $500 or LESS" / "total of all received from Form A" / "…from
  Form B") and the 2025 "Nephi City Campaign Financial Report" (1a/1b/2a/2b). The under-$500
  aggregate is recorded in the note, never synthesized as rows.

### Multi-candidate compilations (the Nephi-unique wrinkle vs Logan)
Nephi's 27 PDFs → 43 index rows because the **2021 (View 2118, 6 candidates) and 2023 (Views
2706/2803, 6+7) uploads pack several candidates' 2-page filings into ONE PDF**; `index.csv` splits
them into per-candidate rows sharing a `path` + carrying a `page_range` ("3-4", "9-10,15-16,…").
- `document_id = sha1(path|page_range)[:8]` — unique PER INDEX ROW, so compilation rows never
  collide (and the two Worwoods stay distinct; see below).
- `nephi_vision_extract.py` renders ONLY that candidate's page span (`pdftoppm -f/-l` per contiguous
  sub-range), so each candidate is transcribed in isolation. Hand-verified: page isolation correct
  (Parady 2118 p5-6, Cowan 2706 p11-12, Nielson 2118 p11-12, Miller 2803 p9-10 — each matches).
- **The validator was updated** (`validate_finance.py`) to key its per-filing row-count check on
  `document_id` (was `source_filing`) — necessary because a compilation shares one `source_filing`
  across several filings. In every single-PDF city `document_id` is 1:1 with `source_filing`, so
  this is **behavior-identical** there; **proven** — all 6 prior cities (provo/west_jordan/lehi/
  sandy/orem/logan) re-validate PASS and re-build with unchanged counts.
- **Worwood ambiguity preserved.** SKIP F. WORWOOD (2021, 2025) and TRAVIS L WORWOOD (2023) are
  DISTINCT people, kept apart by the `(candidate, election_year)` key — never merged.

### Modes — ~100% vision (all handwritten scans)
- **OCR-only reconciles 0/42** (expected — `$`-less handwriting). Vision is the primary itemization
  path.
- **Vision (GATED):** `nephi_vision_extract.py`, `pdftoppm -jpeg` @150 DPI into a WORKING DIR
  (`vision/_tmp`, never `/tmp`), model **`claude-sonnet-5`**, strict "transcribe EXACTLY / mark
  illegible null / never infer" prompt; cached to `vision/<doc8>.json`, fed back through the SAME
  reconciliation via the driver `rows_override_fn` (`extract_method=…/vision`). **42 of 42 in-scope
  filings vision-processed** (41 first run + 1 retried after a transient SSL EOF), **76 pages,
  ≈$1.21 total** (~258k input + ~29k output tokens, Sonnet list price). The same STATED-total
  sign-normalization hook Logan uses (dotted-leader "……$ 108.19" mis-read as a minus → magnitude)
  lives in `build_finance.py`, not the family.
- **Final: 20 of 42 reconcile BOTH sides.** The **22 honest residual flags** (all `low` +
  `needs_review`, nothing guessed) break down as:
  - **17 with an "unknown" (blank) contribution side** — the filer stated only an under-$500
    aggregate (a single handwritten figure) with NO Form-A itemization, so the itemized side cannot
    be reconciled and the aggregate is recorded in `filing_totals.notes` (the totals-only /
    non-fabrication discipline), or reported nothing.
  - **12 with an expenditure mismatch** — mostly tiny candidate arithmetic / handwriting cents
    (Callaway 2025 ×3 at −$0.33/−0.34/−0.39; Worwood −$0.20; Carolyn −$5; Tate −$10), plus **2
    genuine large source discrepancies** kept verbatim: **SHARI COWAN 2023 interim** (her cover 2b
    states $1,112.50 but her own Form-B itemizes $3,932.50 — three $1,102 Nephi Times News ads +
    others; +$2,820 delta is HER error, transcribed exactly) and **NATHAN MEMMOTT 2019** (+$500).
  All raw-PDF-authoritative.

### Dedup — MIXED, per-candidate (empirically determined, like Logan)
`is_incremental` is set PER `(candidate, election_year)` from consecutive-report contribution-row
overlap (`_classify_modes`), NOT a city constant. **Predominant = INCREMENTAL** (`True`, 22 of 24
traceable pairs — each round reports only new activity; a cycle total is the SUM). **Exception =
CUMULATIVE** (`False`, exactly **BART STANLEY MILLER 2023 and 2025** — he re-lists the whole cycle
every round; e.g. 2025 he filed $508.41 identically 3×; a cycle total is the LATEST report, NOT a
sum). `dedup_mode=None` (no uniform supersession asserted); a cross-cycle total MUST honor per-
filing `is_incremental`.

### donor_type distribution (50 contribution rows)
individual 23 · candidate-self 23 · family-of-candidate 2 · business 1 · unknown 1. **1 in-kind**
row. **0 blank-donor rows** (every transcribed row carries a name). Rural, low-money city — heavy
self-funding (23 candidate-self) is expected. `donor_aliases.csv` carries **1 curated override**
(FlexSim Software Products → business; the conservative tier-1 classifier missed the company because
"Software"/"Products" aren't business tokens — evidenced vs the Nielson 2021 raw PDF).
`finance_overrides.csv` carries **1 documentary row** (Shari Cowan Jeff & Patty Banks contribution
is in-kind "Door hangers" on the form but vision read `in_kind=False`; documented, not auto-applied
— the row reconciles and the raw PDF is authoritative).

### Hand-verification (5 filings, line-by-line vs raw PDFs, 2026-07-06 — all vision)
| filing | check | result |
|---|---|---|
| Bart Stanley Miller — 2023 Final (2803 p9-10), CUMULATIVE | 7 contrib + 6 expend | ✓ exact; Σcontrib **$1,684.65 = 1b**, Σexpend **$1,684.65 = 2b**; 5 candidate-self + Hap/Bonnie White individual; both reconcile |
| Shari Cowan — 2023 interim (2706 p11-12), FLAGGED | 1 contrib + 6 expend | ✓ page isolation correct; expend transcribed EXACTLY (3× Nephi Times News $1,102 + others = $3,932.50); flag = HER cover 2b $1,112.50 ≠ her own itemized → honest source discrepancy, not an extraction error. Minor: Banks in-kind "Door hangers" not flagged (finance_overrides) |
| J.D. Parady — 2021 interim (2118 p5-6) | 4 contrib + 8 expend | ✓ exact; contrib **$480 = line 1 aggregate**, expend Σ **$1,570.61 = line 4** (Form B); both reconcile |
| Glade R. Nielson — 2021 interim (2118 p11-12) | 2 contrib + 6 expend | ✓ exact; contrib **$1,500 = line 2** (FlexSim $1,000 + AES $500), expend Σ **$1,943.98 = line 4**; both reconcile; FlexSim→business via alias |
| Justin D. Seely — 2019 Final (cf_1202, single PDF) | 0 contrib + 4 expend | ✓ exact; 4 expenditures Σ **$820.20 = line 4** (The Times News ×2, Juab High School, Livingston Photography); expend reconciles |

### Rebuild / correct
`python3 build_finance.py` (idempotent; re-reads `vision/*.json`, never re-calls the API for a
cached filing). Re-run vision for one filing: delete its `vision/<doc8>.json` and run
`python3 nephi_vision_extract.py [<doc8> …]`. Corrections → `finance_overrides.csv` /
`donor_aliases.csv` (never hand-edit the derived CSVs).
