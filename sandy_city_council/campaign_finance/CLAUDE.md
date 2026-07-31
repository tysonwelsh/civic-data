# campaign_finance — Sandy City candidate campaign-finance disclosures

Additive dataset completing the **elections → members → votes** chain for Sandy: *who
funded the people casting the council votes.* **83 filings, 7 filers, cycles 2021/2023/
2025**, all from Sandy's **EasyVote** portal. Read `AVAILABILITY.md` for the full
source-hunt (state, county, city, Wayback) and the honest 2019 gap. Additive only — this
directory never modifies `election_results/` or any other dataset.

## What this is

Every file under `raw/easyvote/` is a Sandy City **"Report of Contributions and
Expenditures"** (Ord. #05-18 / #18-09, UCA 10-3-208) — one form combining contributions +
expenditures per reporting period. These are the *campaign*-finance reports (not the
personal conflict-of-interest disclosures). All are **scanned images** (the portal only
serves a flattened, redacted rendering), so text is via **OCR** (`text/*.txt`).

## Layout

- `raw/easyvote/*.pdf` — the 83 filing PDFs, verbatim. Filename `YYYYMM_Lastname_<report>_<did8>.pdf`
  where `YYYYMM` = submission month (avoids cross-period collisions), `did8` = first 8 of the
  EasyVote documentId.
- `raw/easyvote/_api_documentsearch.json`, `_api_getwebsiteuser.json`, `_manifest.json` —
  verbatim API listing + per-doc harvest manifest (sha256, bytes, status).
- `raw/easyvote/_fetch_log.jsonl` — one JSONL line per download (url, status, bytes,
  sha256, content_type, retrieved_utc). Provenance.
- `raw/index_pages/` — the HTML of every portal/state/city/Wayback page consulted (the
  evidence behind `AVAILABILITY.md`), incl. `easyvote_main.js` (the app bundle the API was
  reverse-read from) and the empty-content `live_343…/live_2161…/wayback_338…` pages that
  prove the 2019/legacy gap.
- `text/*.txt` — OCR (tesseract) of each PDF, one file per PDF, page-break `\f`.
- `index.csv` — the machine-readable index (below).
- `build_index.py` — rebuilds `index.csv` from `_manifest.json`. Idempotent.

## How it was fetched (reproduce)

EasyVote is an Angular SPA backed by `https://ecf-api.easyvoteapp.com`. The public
endpoints and the two required headers (`Easy-Vote-Authenticated-User`,
`ZUMO-API-VERSION`) were read out of the app bundle; polite_fetch.py can't send custom
headers, so a small sibling harvester (`harvest_easyvote.py`, discipline mirrored:
browser UA, ≥1s throttle, verbatim bytes, sha256 + JSONL log) did the download; OCR via
`ocr_all.py` (pdftoppm + tesseract). Chain:
`getwebsiteuser/sandycityut` → CustomerId → `filer/documentsearch/{CustomerId}` (the 7
filers + 83 docs) → `documents/{id}/viewfinalredactedpdf` per doc. GET-only, public
records only.

## index.csv columns

`date` (filing/submission date, ISO) · `candidate` · `office` (normalized:
Mayor / Council At-Large / Council District N) · `election_year` · `filing_type`
(`interim` = 28/7-day-before periodic reports; `summary` = year-end **Annual** + post-
election **Final** reports) · `title` · `source_url` (the public portal page) ·
`retrieved_date` · `format` (`scanned`) · `extraction_method` (`ocr_tesseract`) · `path`
(dataset-relative, includes `raw/`) · `reporting_period` (the filer's own label for the
report) · `document_id` (EasyVote GUID) · `sha256` · `matched_election_candidate` ·
`join_confidence` · `provider`.

### `election_year` rule
`effective_year = (filing month ∈ {Jan,Feb}) ? filing_year−1 : filing_year`;
`election_year = effective_year if odd else effective_year−1`. Sandy municipal cycles are
the odd years. A January-filed **annual** report covers the prior calendar year, so it maps
to the seating cycle. Off-cycle annual reports by *sitting* officials fall in a cycle window
where they were **not on the ballot** — those correctly get `join_confidence=none`.

## Join to election_results (who funded the voters)

`build_index.py` left-joins each filing's `(candidate, election_year)` to
`../election_results/sandy_results_by_candidate.csv` (the full ballot universe, richer than
the winners-only `sandy_races.csv`). Names are normalized (upper-case, nickname/quotes/
apostrophes stripped, first+last tokens). `join_confidence`: `exact` (first+last match),
`medium` (unique last-name / first-initial match), `none`.

**Result: 67 of 83 filings join `exact`; 12 of 18 distinct `(candidate, year)` pairs join.**
The 6 unjoined pairs are:
- **5 legitimate off-cycle annual reports** by sitting officials filing between their own
  elections (Stroud 2021 & 2025, D'Sousa 2023, Sharkey 2021, Zoltanski 2023) — the person
  wasn't on that cycle's ballot, so no join is correct.
- **1 election-record discrepancy — Parry Harrison 2025** — filed a full set of 2025
  District 3 *primary* campaign reports but is absent from `election_results` (which
  captures only the **general**). See `AVAILABILITY.md`. Flagged, not "fixed": additive
  dataset, `election_results` untouched.

## Caveats

- **Not the full candidate field.** EasyVote holds only the **7 filers who registered in
  it.** 2019 filings and several later winners/losers who never used the portal (Jim
  Edwards, Ryan Mecham, Zach Robinson, Marci Houseman, and all losing candidates) are
  **absent** — a source limitation, verified in `AVAILABILITY.md`, never fabricated.
- **Redacted at source.** Only the portal's `viewfinalredactedpdf` is public; donor detail
  is masked by Sandy before publication.
- **OCR, not born-digital.** `text/*.txt` is machine OCR of scanned images — expect
  transcription noise; the PDF is authoritative. Screen with
  `.claude/skills/audit-city-data/scripts/screen_corpus.py`.
- **Rebuild:** `python3 build_index.py` (index only). Re-harvesting PDFs requires the
  EasyVote API headers documented above.

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-05

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`.
Sandy is the **first OCR city** and the **OCR twin of West Jordan's born-digital F2 EasyVote**
work — the SAME "Report of Contributions and Expenditures" form (Summary Page + Schedule A/B),
but the portal serves flattened, redacted renders, so every filing is read via tesseract OCR.
Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent).
Validate: `python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS**.

- **contributions.csv** 1,261 rows · **expenditures.csv** 813 rows · **filing_totals.csv** 83 rows.
- **SCOPE — all 83 filings are in-scope campaign C&E reports.** Sandy files no annual-financial /
  conflict-of-interest statements through EasyVote; its "Annual" reports ARE the year-end C&E
  summaries (`filing_type=summary`). Nothing excluded.
- **EasyVote is INCREMENTAL** (`is_incremental=True`) exactly like WJ: the Summary "Column A /
  Total this Period" and Schedule A/B are per-period, so a candidate's cycle total is the **sum**
  of the period reports' Column-A figures; the final report's Column B (YTD) is the cross-check.

### OCR handling (`families/easyvote_schedab.py` — one parser, OCR mode auto-selected by `is_scanned`)
The born-digital WJ path is byte-for-byte unchanged (WJ still 366/548/43, PASS). OCR mode adds
only **reversible, whitelisted** tolerances — a figure that won't parse stays **blank + flagged,
never guessed**:
- **currency repair** (marked `extract_method=…+repair`): `§`→`$`; a lone `S`/`s`/`'s` before a
  cents body → `$`; the **thousands-comma-read-as-period** (`$7.425.00`→`$7,425.00`, the dominant
  Sandy OCR error) and the reverse comma-as-decimal (`$104,18`→`$104.18`).
- **date-sanity**: a contribution/expenditure date outside `[election_year−1 .. filing_date]`
  (tesseract reads `2021` as `2012`) is **BLANKED, amount KEPT** — never re-guessed.
- **per-page in-kind inference** (`…+inkind`): Sandy's 2021 form prints a single-token page
  SUBTOTAL (cash only); when a page's cash rows exceed that printed subtotal by exactly one row's
  amount, that row is the in-kind one (e.g. Nicholl's `Reagan Outdoor Advertising $4,500` billboard,
  ✔ in the In-Kind column) → flipped to `in_kind=True`, proven by the page's own subtotal.
- **vertical-layout recovery** (`…+vertical`): the 2025 form's expenditure pages OCR one field per
  line; those rows are re-assembled by scanning date→first money line.
- **Reconciliation is against the Summary-Page stated total** (which OCRs far better than the
  garbled per-page subtotals), cash-only (in-kind is a separate stated line), tolerance $0.01.

### Vision escalation (GATED — only the OCR-unreconciled filings)
OCR + repair reconciled **49 of 83** filings. The remaining **34** (garbled multi-row in-kind
campaigns; 40–224-donor filings whose odd-cent Stripe/ActBlue amounts accumulate OCR error;
one-field-per-line 2025 pages) were escalated to **Claude vision** (`vision_extract.py`, model
`claude-sonnet-5`, strict "transcribe exactly / never infer" prompt; transcriptions cached in
`vision/<doc8>.json`, fed back through the SAME reconciliation via the driver `rows_override_fn`,
`extract_method=…/vision`). **Cost ≈ $3 total** (34 filings, ~202 pages, ~430k input + ~180k
output tokens, synchronous list price; ~half that on the Batch API). Vision reconciled **32 of 34**.
- **Final: 81 of 83 filings reconcile both sides** (medium confidence — still a scanned source).
  The **2 honest residual flags** are both huge Monica Zoltanski filings: the 24-page 2021 Initial
  (contrib reconciles; vision still missed ~$3,005 of the 127 expenditures) and the superseded
  *original* of the amended July-15-2025 pair (its own stated totals differ from its itemization —
  which is why it was amended; the **amendment** `9E217718` reconciles perfectly). Both carry
  `needs_review=1` + `low` confidence; nothing fabricated.

### Dedup / amendments
Sandy labels an amendment DIFFERENTLY from its original (`Amend Aug 28 filing` vs `Primary Filing
Aug 29`), so the period-label grouping can't pair them; the driver now also pairs an orphan
amendment to the unique same-candidate+cycle non-amendment filing with **identical non-zero stated
totals** and marks it superseded (Nicholl 2021 `1`←`amedned`; Sharkey 2023 Aug/Oct pairs). 12
supersession/amendment notes; kept + flagged, never dropped. Cycle totals (a query) must exclude
`superseded…` rows — naive sums double-count the amended periods.

### donor_type distribution (1,261 rows)
individual 1,119 · candidate-self 62 · business 34 · family-of-candidate 14 · unknown 11 ·
loan 9 · pac 8 · anonymous 4. 76 in-kind contribution rows. **0 blank-donor rows.** 36 filings
carry self-funding. `donor_aliases.csv` + `finance_overrides.csv` are header-only seeds.

### Hand-verification (5 filings, line-by-line vs the rendered raw PDF images, 2026-07-05)
| filing | mode | check | result |
|---|---|---|---|
| Brooke Christensen — Oct-11 2021 | OCR+date-repair | Schedule-A grand total; 4 `09/28/2012`-type dates blanked (amount kept) | ✓ Σ contrib **$38,411.24 = stated**; 4 dates correctly blanked |
| Cyndi Sharkey — Primary Aug-8 2023 | OCR | 17 Schedule-A rows vs image | ✓ Σ **$7,425.00 = stated**, in-kind $0.00 |
| Kris Nicholl — report "1" 2021 | vision | `Reagan Outdoor Advertising $4,500` ✔ in In-Kind column; Cheryl Thackeray $10,000 cash | ✓ Reagan `in_kind=True`; cash Σ **$27,912.84 = stated** |
| Cyndi Sharkey — Mayor 28-day 2025 | vision | 4 in-kind rows incl. OCR-garbled `[511,200.00` | ✓ vision read **$11,800**; in-kind Σ **$21,847.84 = stated**; cash both sides reconcile |
| Monica Zoltanski — Initial 2021 | vision (flagged) | is the residual flag honest? | ✓ contrib reconciles; expend short (~$3,005 of 127 rows) → all rows `needs_review=1`+`low`, **not fabricated** |

## Regression fix + per-candidate regime pass (2026-07-20)

- **Stale-key regression FIXED:** the index column was renamed `report_period` →
  `reporting_period` after this build was written; the build kept reading the old key, so every
  filing carried a BLANK period and the incremental dedup collapsed each candidate-cycle into one
  group — **65 false "superseded by amendment/re-file" notes** (vs the 12 documented above) and
  cycle_totals reduced to the LAST filing per cycle (e.g. Stroud 2023 printed 0/0 against her
  YTD-proven $970/$970). `build_finance.py` now reads `reporting_period` (old key tolerated).
  The documented supersessions are restored exactly (Nicholl 2021 `1`←`amedned`; Sharkey 2023
  Aug/Oct pairs; 8 structural supersessions total).
- **`is_incremental`** now runs the shared empirical per-candidate derivation
  (`derive_incremental=True`); all evidence-backed Sandy filers are per-period — the family
  constant `True` stands for every row (0 restamps).
- **`cycle_overrides.csv` (9 rows)** carries the figures the generic rules cannot derive, each
  with its proof in the reason column: YTD-chain-exact per-period sums (Christensen 2021;
  Sharkey 2023; Nicholl 2021 — spent column B foots to the cent, raised-side B recorded as a
  filer anomaly), both-sides-equal closure proofs (Christensen 2025, Harrison 2025), the
  email-as-reporting_period label that falsely superseded two real periods (Christensen 2023,
  B-exact), the July-15 amendment that restates 104/104 + 26/26 rows but with different totals
  (Zoltanski 2025), the latest-summary rule taking a near-empty Annual over the real Dec-04
  post-general period (Sharkey 2025), and the officeholder-year chain (D'Sousa 2023). Remaining
  MIXED flag: Zoltanski 2021 (annual-disclosure attribution genuinely ambiguous — left flagged,
  not guessed).
