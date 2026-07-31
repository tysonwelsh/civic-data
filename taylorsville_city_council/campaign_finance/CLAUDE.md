# campaign_finance — Taylorsville City candidate & elected-official campaign-finance disclosures

Additive expansion dataset (source type #6, `expand-city-sources`). Raw filings + provenance
`index.csv` + gap records, **plus the structured money layer** (`build_finance.py` →
`contributions.csv` / `expenditures.csv` / `filing_totals.csv`, family `taylorsville_form`).
Filings are **28 born-digital (`format=text`) + 43 scanned (`format=scanned`)**.

**COVERAGE (2026-07-19): 71 filings acquired; 70 STRUCTURED after the Overson dedup — 68
both-sides reconcile of 70, 2 honest flags (no false mismatches). One filing (Overson
doc8378) is a VERIFIED CONTENT DUPLICATE excluded from the structured build (see the dated
note); its raw PDF + vision cache are retained.** The 35 scanned annual statements
(2017–2025) were vision-transcribed this wave (cf-vision-transcribe, $0 API). See the dated
notes below.

**Reconcile-flag spot-check re-confirmed 2026-07-19 (TODO low-priority CF review-flags pass):**
the **2** residual non-reconciling `filing_totals` rows (2017 Burgess doc10669 — source left the
CONTRIBUTIONS cover total blank on a near-zero annual; 2022 Harker doc10615 — $200 totals-only,
Attachment A empty) and the lone `cycle_totals` `review_flag` (Larry Johnson 2021 D5, an
`override` = balance-chain-verified per-period `cycle_overrides` total) are all already
dispositioned above — honest source arithmetic / documented override, no pipeline defect. No
override added; `cycle_totals.csv` byte-identical after re-running `cycle_totals.py`.

## Structuring layer (the defining quirk — READ THIS)

Taylorsville hosts a **fillable PDF whose text layer is a static TEMPLATE — the real dollar
figures are HANDWRITTEN and rastered into the page image.** `pdftotext` recovers the boilerplate
cleanly but the numbers come back as garble ("23 a b. 3D", "c747.") or not at all. **So even the
"born-digital" filings mostly need VISION** — this is not an OCR problem, it is handwriting.

- **Text mode** (`taylorsville_form.parse`) reads ONLY filings whose totals auto-populate as
  cleanly-typed accounting cells (the newest 2025-26 template). In this corpus that is **3
  all-zeros annual statements** (2025 Harker doc10631, 2026 Barbieri doc11777, 2026 Knudsen
  doc11775 — reconcile clean) **+ 1 typed $200 expenditure total** (2026 Harker doc11783; its
  itemized row is field-glued, captured as totals-only, row left to vision). Every other filing
  returns **stated=None (awaiting vision)** — never a guessed/template-default zero.
- **Vision mode** — pages rendered + Read-transcribed (cf-vision-transcribe skill, Claude-Code
  allotment, $0 API) into `vision/<docid>.json`, fed through the driver's `rows_override_fn` and
  judged by the SAME printed-total reconciliation. `docid` = the CivicEngage document id.
- **2026-07-12 vision backfill of the 13 flagged filings: 35/36 structured filings now
  both-sides reconcile.** The 11 "awaiting vision" annuals were mostly handwritten
  accounting zeros (`-0-`/`Ø`); real money: Harker-2022 $200 to "Elect Aimee Winder Newton"
  (its Attachment A is empty despite the stated $200 — the one honest totals-only flag left),
  Harker-2026 $200 to Nicole McDermott, Cochran-2026 $657.03 self-funding. Johnson-2021's
  $4,256.01 expend gap was ONE cache digit (Winco "4299" → $42.99, check-style raised cents;
  fixed — now exact). **Barbieri doc10471 is a page-for-page duplicate scan of her annual
  doc10609** posted under a second label (both cached; both zero-dollar, harmless to sums —
  flagged here for any future content-level dedup).
- **2026-07-19 ANNUAL BACKFILL — the 35 remaining scanned annual statements (2017–2025)
  vision-transcribed** (cf-vision-transcribe, repo-standard `sha1(index_path)[:8]` cache
  keys; $0 API). Reconcile went **35→69 both-sides** (of 71); the 2 residual flags are
  HONEST, not mismatches: **2017 Burgess doc10669** (the source left the summary
  CONTRIBUTIONS total blank on a near-zero filing → `reconciles_contrib` blank/unknown) and
  **2022 Harker doc10615** (the pre-existing documented $200 totals-only, Attachment A
  empty). **Real money surfaced in several annuals** (all `filing_regime=annual` → NEVER in
  a race total): Overson 2025 **$11,500** (12 donors incl. SL Board of Realtors $5,000) /
  $665.20; Overson 2019 **$6,000** (Summit Life Plan $5,000 + Cowdell & Wooley $1,000);
  Overson 2020 $1,500; Burgess 2020 $500 (SL Board of Realtors) + $500 loan repayment;
  Cochran 2023 $800 self; Overson 2023 $155.60; Overson 2020 $88.80; Overson 2018 $75;
  Harker 2018 $50; Knudsen 2024 $5.00 account fee.
- **DUPLICATE SCAN — DISPOSITIONED (2026-07-19): Overson "2024" doc8378 ≡ "2025" doc10635
  are the BYTE-IDENTICAL PDF** (same md5 `6bad67e7bac1d15fe7551c8ff35e70d5`) — the city
  posted the 2025 Overson annual under BOTH the 2024 and 2025 labels, so the genuine 2024
  Overson annual (CY2023) is effectively UNPUBLISHED. Verified by md5 + the in-body reporting
  period (contribs 11/20/2024–2/24/2025, signed 2/25/25, "Received FEB 26 2025" → an
  unambiguously 2025 statement; the in-document year governs). **Disposition (Barbieri
  precedent, but ESCALATED because this dup is non-zero $11,500): the mislabeled 2024 row
  (doc8378) is marked `extraction_method=duplicate-excluded` in `index.csv` and dropped from
  the structured build by `build_finance.py`'s `_in_scope` gate** — so the identical
  $11,500 / $665.20 is counted ONCE (via the genuine 2025 row doc10635), not twice, in
  `filing_totals`. The raw PDF and its vision cache (`7eac6a20.json`) are RETAINED on disk
  (dedup = documented exclusion, never deletion); the validator emits one honest WARN
  ("index filing …doc8378… has no filing_totals row"). The genuine-2024-unpublished fact is
  logged in `unrecovered.csv` + `AVAILABILITY.md` gap #5. **Both were `annual` regime → NO
  race/cycle total was ever affected** (annuals never feed `cycle_totals`; `cycle_totals.csv`
  is byte-identical). Re-probed 2026-07-19: the live 2024 page (HTTP 200) still links
  "Overson, Kristie" → doc8378 — the distinct 2024 annual remains unposted.
  *(The zero-dollar Barbieri doc10471≡doc10609 dup was left in-scope as harmless — that
  precedent flags; this one is escalated to exclusion because the money is real.)*
- **RECEIVED-STAMP DATES (2026-07-19): 27 annual filings now carry the PDF "Received" stamp
  date** (`index.csv` `date_precision=received_stamp`, replacing the inferred `-03-01`).
  Skipped: 2021 Overson doc6220 (stamp conflicts with its own content — left inferred),
  the doc8378 dup, and the 2024/Knudsen forms that print no stamp.

## Two regimes — `filing_regime` (added to `filing_totals.csv`)

`filing_regime` ∈ {`annual`, `election_cycle`} is carried from `index.csv` onto every
`filing_totals` row (a TRAILING, optional column on the shared schema; single-regime cities omit
it — validate_finance accepts both). **`annual` (50) is a PARALLEL stream — mandatory March-1
statements, never summed into a race total.** **`election_cycle` (21, 2021 & 2023) is the ONLY
stream that feeds a cycle total.** Reports are per-period ("excluding those previously reported")
→ `is_incremental=True` → a cycle total **sums** a candidate's election_cycle reports.

> **Per-candidate `is_incremental` + a second cycle override (2026-07-20):** the build now runs the
> shared empirical derivation (`derive_incremental=True`, `driver.derive_is_incremental()` row-overlap
> method). **Two candidate-cycles are evidence-backed CUMULATIVE (`False`)**, both page-verified
> against the raw PDFs: **Anna Barbieri 2021** (her General Election Final Statement, signed 12/1/21,
> restates the whole campaign — Attachment A-1 single 6/15/21 self-contribution $2,115.65, Attachment
> B re-lists all 4 June–July expenditures summing exactly $2,115.65, balance $0.0; identical to her
> pre-general — cycle figure $2,115.65/$2,115.65 already correct, unchanged) and **Curt Cochran 2023**
> (his Gen Election Report, rec'd 11/14/2023, re-lists the 28-Day Report's two Attachment-B items
> verbatim — $50.00 filing fee + 9/9/2023 Lowe's $10.72 = $60.72 — with the SAME balance chain
> $800.00 → $739.28 both reports; a new period would have opened at $739.28 → $678.56; his Final shows
> no activity, begin=end $739.28). Cochran's sum-interim figure double-counted → **`cycle_overrides.csv`
> row 2: Curt Cochran 2023 = $0.00 raised / $60.72 spent** (basis=override). All other filers keep
> `True`; annual statements produced no pair evidence (each is its own period by construction).
> Restamp is row-metadata only (14 rows, `is_incremental` column alone); `filing_totals.csv`
> byte-identical; the **locked Johnson 2021 D5 override below is untouched** (verified byte-level).
> Validator PASS (1 expected WARN = the doc8378 duplicate exclusion).

> **cycle_totals.py RUN 2026-07-12** (`cycle_totals.csv`, 15 rows). The regime split falls out
> of the blank `election_year` on annual filings: rows with **blank election_year are the
> ANNUAL-statement stream grouped per candidate — NOT race totals**; only the 2021/2023 rows
> are race cycles. **Larry Johnson 2021 = 8,745.05 / 8,745.12 via `cycle_overrides.csv`**
> (balance-chain-verified pure per-period filer whose "final" is itself a period — the generic
> max(summary, summed-interims) rule under-counts by that final period; the override file is
> the documented correction mechanism, consumed by cycle_totals.py). Do not sum
> `filing_totals` by hand.

## What this is

Taylorsville City Code **2.36.040** (implementing Utah Code **10-3-208**) requires campaign-
finance disclosure, and the city **self-hosts** all filings on its CivicEngage site. There
are **two regimes, both "Report of Contributions & Expenditures" forms** — see the
`filing_regime` column:

- **`annual`** (50 filings, 2017–2026) — the *Annual Campaign Finance Statement for Elected
  Officials/Candidates*, **due March 1 every year from every sitting official**, election year
  or not. This is why the record is dense in off-years. (The lone 2022 "Campaign Financial
  Disclosure" grouped under Barbieri is one of these — face reads "MARCH 1, 2022", all-zeros.)
- **`election_cycle`** (21 filings) — candidate campaign disclosures filed during a race:
  Primary Initial / Pre-General (interim) + Final (summary). Present for **2021** & **2023**.

## Source & retrieval

- Home: `https://www.taylorsvilleut.gov/government/elections/financial-disclosures`
- Year subpages `.../financial-disclosures/<YYYY>-financial-disclosures` (2017–2025). Each
  page groups links under an "…Annual Financial Statements" header (annual regime) and, in
  election years, "Disclosures for <Candidate>" headers (election-cycle regime). The section
  header supplies the candidate for election-cycle filings; the link text ("Surname, First")
  supplies it for annual filings.
- Filing PDFs: `/home/showpublisheddocument/<docId>/<versionToken>`. **The site 403s bare
  bots** — every fetch used `scripts/../polite_fetch.py` with the browser UA and a Referer.
- Stored filenames: `<year>_<regime>_<First-Last>_<label-slug>_doc<docId>.pdf` — `docId` is
  the CivicEngage document id (unique; no collisions, unlike Wayback basenames).

## index.csv columns

§9 contract cols first (`date, candidate, office, election_year, filing_type, reporting_period,
title, source_url, retrieved_date, format, extraction_method, path`; `filing_type` ∈
interim|summary; `reporting_period` blank where not recorded; `path` dataset-relative incl.
`raw/`) **plus**: `district, filing_year, filing_regime` (annual|election_cycle),
`filing_phase` (annual|primary_initial|pre_general|final|first|second), `filing_label_verbatim`
(the city's exact link text), `docid`, `pages`, `date_precision` (`inferred` — see below),
`in_election_results` (yes/no), `election_winner` (True/False for election-cycle filings; blank
for annual), `source`.

- **`date` is INFERRED** (`date_precision=inferred`) from `filing_phase` + `filing_year`
  (annual→`-03-01`; primary→`-08-02`; pre_general→`-10-26`; final→`-12-02`;
  1st→`-08-15`; 2nd→`-10-25`). The true "Received" stamp is on each PDF's face and should be
  read during the OCR/structuring step to replace these with exact dates. **2026-07-19: 27
  annual filings now carry the read "Received" stamp (`date_precision=received_stamp`);** the
  election-cycle filings + a handful of stamp-less/duplicate annuals remain `inferred`.
- **`filing_type`/`filing_phase` are per-PDF** — this is the double-count-trap guard. Do NOT
  sum filings for a candidate/race total; run `scripts/campaign_finance/cycle_totals.py` in
  the structuring step (2021 Johnson/Knudsen each have 3 election-cycle filings, etc.).

## Join to election_results

100% candidate-join (71/71) via last name → office/district, with **Overson→Mayor** hard-
mapped (roster drift: she was D2 in 2011/2015 before becoming Mayor — see city `CLAUDE.md`).
Election-cycle `election_winner` was set from `election_results/taylorsville_races.csv`
winners by (office, district, year): **18 winner-filings + 3 by Larry Johnson** (2021 D5,
lost to Knudsen). No filing surfaced a race missing from the election dataset. **Nothing was
written back into `election_results/`.**

## Known gaps (also in `unrecovered.csv` / `AVAILABILITY.md`)

- **2019 election-cycle filings never posted** (only the 4 annual statements exist for 2019).
- **2025 election-cycle filings not yet posted** (only 2025/2026 annual statements) — likely a
  publishing lag; **re-probe on refresh**. **Re-probed 2026-07-19** (live page, HTTP 200): the
  2025 page still lists ONLY "Annual Financial Statements" — zero "Disclosures for <Candidate>"
  / Primary / Pre-General / Interim / Final sections. Gap PERSISTS; nothing new to ingest.
- Wayback holds only one pre-election 2025-08-12 snapshot; the filing PDFs were never archived,
  so neither gap is Wayback-recoverable.

## Rebuild / refresh

Re-harvest by fetching the year subpages, parsing the header→link groups (annual vs
"Disclosures for <Candidate>"), and re-running the index build. On refresh, especially
**re-check the 2025 page for newly-posted election-cycle campaign filings** and add any new
election year's subpage.
