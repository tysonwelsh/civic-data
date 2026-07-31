# campaign_finance/ — build method, linkage, caveats

Financial-disclosure filings for West Jordan municipal candidates (Mayor + Council),
completing the **elections → members → votes** chain. Additive dataset built by
`expand-city-sources` (Source 6). **As-of 2026-07-03.**

## Contents

- `raw/easyvote/` — 101 PDFs from West Jordan's EasyVote portal (2023–2026) + `_fetch_log.jsonl`.
- `raw/city/` — 34 PDFs from the city website disclosures page (2021 campaign finance +
  2021–23 annual disclosures + 2024/2026 conflict-of-interest) + `_fetch_log.jsonl`.
- `text/` — 135 text sidecars: `pdftotext -layout` for born-digital PDFs, `tesseract` OCR for
  scanned/handwritten forms. Filename = `<subdir>__<rawname>.txt`.
- `index.csv` — 135 rows, one per filing.
- `AVAILABILITY.md` — every source checked (with URLs), coverage, gaps, election-record flags.

## index.csv schema

Required cols: `date, candidate, office, election_year, filing_type, reporting_period, title,
source_url, retrieved_date, format, extraction_method, path` (`reporting_period` blank where
not recorded). Added alongside: `source`
(easyvote / city_website), `district`, `filer_type` (EasyVote: New Candidate / Unsuccessful
Candidate / Current Elected Official), `in_election_results` (yes / no / blank), `date_precision`
(day for EasyVote submit dates; month for city PDFs dated only by upload folder `YYYY/MM`).

- `office` ∈ Mayor / Council. `filing_type` ∈ interim / summary / statement (vocab also allows
  contribution / expenditure — not used; WJ files combined reports, not split ledgers).
  - **interim** = periodic campaign report (Primary, 28-Day, 7-Day, General Election Report).
  - **summary** = final/post-election campaign report (Post-General, Final, "Primary and General").
  - **statement** = elected-official annual financial disclosure or conflict-of-interest form
    (Utah Code 10-3-1304 type; not a campaign contribution/expenditure report).
- `format` ∈ text / scanned. `path` is dataset-relative including `raw/`.
- `election_year` = the municipal cycle a **campaign-finance** filing pertains to (2021/2023/2025);
  **blank for `statement` rows** (annual/COI filings aren't tied to one race).

## Retrieval (reproducible)

**EasyVote** (WJ instance, customer `96E8AE5D-966C-406F-AFD4-493B2A8BBF05`):
`GET https://ecf-api.easyvoteapp.com/filer/documentsearch/{customerId}` (JSON list of filers +
`documents[]`), then per document
`GET https://ecf-api.easyvoteapp.com/documents/{documentId}/viewfinalredactedpdf` (public redacted
PDF). Origin/Referer headers = `https://cityofwestjordanut.easyvotecampaignfinance.com`. The API
base and endpoints were reverse-engineered from the SPA's `main.5cb5b76dc155dd14.js`
(`API_BASE_URL`, `/documents/…/viewfinalredactedpdf`, `getHttpHeadersForAuthenticatedUserFromCookie`
distinguishes the 401 auth endpoints from the public one).

**City website:** direct `wp-content/uploads/YYYY/MM/*.pdf` links scraped from
`…/elections/conflict-of-interest-and-financial-disclosures/`, fetched via `polite_fetch.py`.
Saved filenames are prefixed with the upload `YYYYMM` to avoid basename collisions across periods.

All fetches: `polite_fetch.py`/urllib, GET-only, throttled, `--now 2026-07-03T00:00:00Z`.

## Linkage to election_results (the join)

Candidates join to `election_results/west_jordan_results_by_candidate.csv` by **normalized name ×
election cycle**. **Critical nuance:** EasyVote's `officename` is each filer's *current/latest*
seat, NOT the race a given document is about. So cycle/office are assigned by the document's
**year**, then the filer is matched against **that cycle's** `election_results` candidates —
e.g. Kayleen Whitelock's 2023 filings are her **Mayor** run (not At-Large), Rulon Green's 2023
filings are **District 1** (not At-Large), David Pack's 2023 filings are **District 4**.

Join quality: **2023 = 8/8** candidates matched; **2021 = 6/8** (2 primary-only); **2025 = 6/11**
(5 primary-only). `in_election_results=no` marks campaign-finance filers who ran only in a
**primary** and so are absent from the general-only `election_results` — see AVAILABILITY.md
"Flags". **`election_results/` was not modified** (additive-only rule).

## Caveats

- **2019 cycle: no online filings** (GRAMA-only; not in Wayback). Documented gap, not fabricated.
- **Redacted public copies**; ~half are scanned handwritten forms → OCR, expect word errors.
- **Kelvin Green 2023 Annual Financial Disclosure** exists in both sources (city + EasyVote);
  both rows kept with distinct provenance.
- **No dollar amounts** are in the index; the raw PDFs + `text/` sidecars hold them — and the
  additive **structured layer** (`contributions/expenditures/filing_totals.csv`, see "## Structured
  layer" below) now extracts them for the born-digital EasyVote filings, reconciled + flagged.

## Rebuild

Re-run EasyVote `documentsearch` + `viewfinalredactedpdf` and the city batch (URLs in
`raw/*/_fetch_log.jsonl`), re-extract (`pdftotext` / `tesseract`), then rebuild `index.csv`
with the year→cycle→election_results join above. Validate:
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py west_jordan_city_council/campaign_finance`

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-06

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`
(West Jordan 2023+ is the **F2 EasyVote** family — "Report of Contributions and Expenditures",
Summary Page + Schedule A/B). Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild:
`python3 build_finance.py` (idempotent). Gated vision escalation: `python3 wj_vision_extract.py`
(scanned filings only; caches to `vision/<doc8>.json`). Validate:
`python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS** (0 fails; the 53 WARNs
are the excluded `statement` filings, which by design carry no `filing_totals` row).

- **contributions.csv** 502 rows · **expenditures.csv** 760 rows · **filing_totals.csv** 82 rows
  (born-digital 43 → **+39 scanned** = 82 filings; the 43 born-digital rows are **byte-identical**
  to the 366/548/43 pre-backfill build — that path is isolated in its own dedup group and untouched).
- **SCOPE — campaign C&E reports (`filing_type ∈ {interim, summary}`).** **EXCLUDED: the 53
  `filing_type=statement` rows** (annual financial disclosure / conflict-of-interest, Utah Code
  10-3-1304 type — not contribution/expenditure reports). **Phase 4 (2026-07-06) added the 39
  `format=scanned` C&E filings** in two groups (below); the born-digital 43 (`format=text`) are
  unchanged.
  - **30 EasyVote SCANNED (2023/2025)** — same F2 form as the born-digital 43, but image renders.
    OCR reconciled only ~2/30 (WJ's scans OCR far worse than Sandy's), so all escalate to Claude
    **vision** (`easyvote_schedab/vision`); **30/30 reconcile** cash-only against the Summary Page
    total. 2 (McConnehey General, Sotelo General-7-Day) share a born-digital filing's period and are
    marked **superseded** (born-digital canonical) so cycle totals don't double-count.
  - **9 CITY 2021 handwritten** — the West Jordan "Campaign Financial Disclosure Report" (numbered
    cover lines 1-6 + Attachment A/B). This is a **distinct WJ form** the `easyvote_schedab` /
    `utah_standard_form` parsers can't read, so it is transcribed 100% by **vision** (fed through
    the shared driver `rows_override_fn`; no new family module warranted). Reconciled **cash-only**:
    line-4 "Total contributions" excludes in-kind (verified on Whitelock — her $1,750 in-kind
    Realtors PAC gift is NOT in her $1,250 line-4 total).
  - **2021 city bundles COMPLETE (2026-07-12).** The PARTIAL undercount era is over: all 9 bundles
    carry full multi-report `reports[]` caches (Read-tool re-transcription, `/cf-vision-transcribe`,
    $0 API; page-range partials preserved in `vision/_partials/`). Several bundle **three** reports
    (pre-primary + pre-general + final — Lamb, Whitelock Final-Amended, Green, Withers), and the
    Whitelock Primary-and-General bundle holds TWO (the earlier "SINGLE report" hand-verify note
    was wrong). Every merged cache cross-foots to the printed attachment totals; every balance
    chain verified. 3/9 reconcile clean; the 6 flags are **decomposed, page-verified filer
    artifacts** (Heath zeroed his own itemized self-loans on lines 2-4, +365.16; Smith put his
    in-kind total inside line 4 and omitted a $25 cash row, −466.19; Bloom −25 = a $50
    cover-vs-attachment inconsistency + a $25 self-loan excluded from her line 4; Withers +25/+6
    handwriting-era arithmetic, his filer-STRUCK $2,257.50 row excluded as the source's own
    deletion; Fields' final re-lists the interim's rows under a no-new-activity cover, +70/+25 —
    the Springer/Holz pattern). Whitelock's restated periods are NOT double-counted: cycle basis =
    her Final-Amended summary ($2,300.00 / $3,140.54). Notable corrected cycles: Lamb
    $6,577.00/$5,998.12; Green $26,713.35/$20,301.73 (line 4 INCLUDES in-kind + a $265 unitemized
    ≤$50 aggregate — the honest −$6,800.94 contrib delta is exactly in-kind + aggregate).
- **EasyVote is INCREMENTAL** (`is_incremental=True`): the Summary "Column A / Total this Period"
  and Schedule A/B are per-period, so a candidate's cycle total is the **sum** of the period
  reports' Column-A figures; the final report's Column B (Year-to-Date) is the cross-check.
  Verified sane where the period chain is complete (Bedore, Shelton, Jacob, Sheppard, Bennett,
  Wignall all match their YTD). Where ΣColumn-A < YTD (Chad Lamb, Dirk Burton), the YTD honestly
  reveals **missing earlier period reports** (a coverage gap, not a dedup error). Amendments /
  exact re-files of the same period **supersede** the original (8 `amendment` + 5 `superseded`
  notes); never summed twice.
- **Reconciliation (43):** **36 reconcile clean both sides**; 7 flagged (`reconciles_*=False`,
  rows `low`+`needs_review=1`) — all honest: multi-line **cell wraps** (an amount/recipient split
  across lines; small deltas) and **in-kind expenditures typed in the cash Amount column** rather
  than the In-Kind column (a genuine EasyVote source ambiguity — Bennett's $300; contrast
  Shelton's $1,200 which IS in the in-kind column). **Reconciliation is cash-only** because the
  form states TOTAL CONTRIBUTIONS/EXPENDITURES **excluding in-kind** (in-kind has its own stated
  line); in-kind rows carry `in_kind=True` + `amount`=the in-kind value and are excluded from the
  reconciliation sum. Multi-page Schedule A/B are handled (the grand-total line repeats per page;
  in-kind column position is learned **per page** from each SUBTOTAL).
- **donor_type distribution** (366): individual 244, loan 37 (candidate self-loans, repeated
  across the incremental period reports), pac 14, candidate-self 20, business 19, family-of-
  candidate 12, anonymous 6, unknown 14 (a few org abbreviations + one `3` mis-parse). Blank-donor
  rows → `unknown`+`needs_review=1`. `donor_aliases.csv` seeds 2 verified merges (Peterson
  Development Company / Corp / LLC). `finance_overrides.csv` header-only.

### Hand-verification (5 filings, line-by-line vs raw `text/` sidecars, 2026-07-05)
| filing | check | result |
|---|---|---|
| Bob Bedore 28-Day 2023 | 8 contribs Σ $3,370 = stated Column A; 8 expenditures Σ $2,098.39 = stated | ✓ MATCH |
| Kent Shelton Primary 2023 | cash contrib $2,145.04 = stated; Ed Brinton $1,200 in-kind (Sched A + B) correctly `in_kind`, excluded from cash; expend cash $1,860.45 = stated | ✓ MATCH |
| Zach Jacob 28-Day 2023 | 6-page Schedule B; contrib $9,032.05 = stated; expend $6,175.61 vs $6,243.47 (one wrapped row) | ◑ contrib MATCH, expend flagged |
| Jessica Wignall General 2025 | wrapped "$33.12 … forum" row recovered; contrib $8,766.67 = stated | ✓ contrib MATCH (expend 1 wrap flagged) |
| Rob Bennett 28-Day 2025 | contrib $26,011.51 = stated; a $300 in-kind expenditure typed in the cash column → cannot be told from cash → expend flagged +$300 | ◑ honest source-ambiguity flag |

### Hand-verification — 2021 city handwritten forms (4 filings, vision vs raw PDF page images, 2026-07-06)
| filing | check | result |
|---|---|---|
| Kayleen Whitelock Primary-and-General 2021 | ~~SINGLE report~~ **TWO reports** (Oct-26 general interim + Aug-2 primary interim — both now in the reports[] cache). Cover line-4 $1,250 = itemized cash; $1,750 in-kind correctly excluded. ~~Cover prints $2,637.99~~ **RETRACTED 2026-07-12: the cover prints $2,637.49** (400dpi glyph check + the typed Attachment B TOTAL corroborate) — this table's earlier ".99" claim was itself the misread; the vision cache was right | ✓ cache verified verbatim-correct both reports |
| Kelvin Green Final 2021 | captured Final report: line-3 $1,500.00, line-5 $5,718.86, line-6 $6,686.32 — all exact vs raw PDF (dated 2021/11/28) | ✓ captured report MATCH; **2-report bundle, earlier report uncaptured → PARTIAL** |
| Chad Lamb Final 2021 | captured report expend $379.27 = raw; the bundle's SECOND report (contrib ~$5,577 / expend $5,407.08) was NOT captured | ✗ **UNDERCOUNT** — clearest PARTIAL bundle; flagged needs_review |
| Pamela Bloom Final 2021 | captured Final: line-5 $(207.23), line-6 $25.62 exact; contribs Borgenicht $75 + Zitting-Goeckeritz $50 = $125 = line-4. `reconciles_contrib=False` (+$50) is a line3($75)-vs-itemized($125) anchor artifact, already `needs_review` via PARTIAL | ◑ data correct; anchor-artifact flag + 2-report bundle |

## Per-candidate `is_incremental` + cycle_overrides (2026-07-20)

- **`is_incremental` is now EMPIRICAL per candidate-cycle**, not the flat family constant:
  `build_finance.py` calls the shared `driver.derive_is_incremental()` (the vineyard/logan/nephi
  row-overlap method) over the MERGED three groups (a candidate's reports span born-digital +
  scanned groups — Pack). Six candidate-cycles are evidence-backed **cumulative** (`False`):
  Whitelock 2021 (restating Final-Amended bundle, adjudicated 2026-07-12), Whitelock 2025 +
  David Pack 2025 + Rulon Green 2023 + Rulon Green 2025 + Eric Hanna 2025 (later reports re-list
  earlier rows — all page-verified 2026-07-20). All other filers keep the form-correct `True`.
  Consequently the historical "born-digital 43 rows byte-identical" invariant is amended: those
  rows may now differ **in the `is_incremental` column only**; every other column is unchanged.
- **`cycle_overrides.csv` (3 rows, all page-verified):** Rulon Green 2023
  ($3,826.05→**$2,605.82** / $3,392.31→**$2,172.08**: his General Report's Column A = Column B =
  $2,605.82 re-lists the 28-Day rows; balance line 2,605.82−433.74 = 2,172.08 exact);
  David Pack 2025 ($7,322.32→**$8,822.32** / $10,022.32→**$11,522.32**: the Sep-10 Post-Primary
  Column A is cycle-to-date and the Sep-12 Amended isolates the period at $1,500 = the exact
  difference); Kayleen Whitelock 2025 ($4,300.00→**$4,150.00** / $6,839.23→**$6,263.12**: her
  28-Day re-lists both primary contributions and all 9 primary expenditures inside its own
  Column A; the Post-General adds one new $77.20 item). The 2021 adjudicated figures are
  untouched (cycle rows byte-identical through the change).
