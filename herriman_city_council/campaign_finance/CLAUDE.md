# campaign_finance/ — Herriman municipal campaign-finance disclosures (ACQUISITION layer)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 6). **Acquisition-only:
no dollar amounts extracted** — raw filings + provenance index. Cycles in scope: **2021,
2023, 2025** (Herriman's D1–D4 staggered cycles + Mayor; 2025 D4 was a 2-year special).

## What's here

- `raw/` — 50 filing PDFs (57 MB) named `<docid>_<original-basename>.pdf`, plus
  `raw/_fetch_log.jsonl` (url, status, sha256, bytes, retrieved_utc for every fetch).
- `index.csv` — one row per published filing URL, SCHEMA_SPEC §9 contract header
  (`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,
  retrieved_date,format,extraction_method,path`) + extras
  (`district,source,original_url,docid,date_precision,duplicate_of,
  matched_election_candidate,join_confidence`).
- `AVAILABILITY.md` — per-cycle coverage, honest empties, and the **flagged 2021-primary
  election-record discrepancy**.

## Sources & the two-domain seam

- **2025 (live):** `https://www.herriman.gov/elections` (Lunasoft CMS; City Recorder's
  page; browser UA — the site 403s bare bots). `source=city_website`,
  `source_url=https://www.herriman.gov/uploads/files/<docid>/<name>.pdf`.
- **2021 + 2023 (Wayback-only):** the page is rewritten each cycle and the old
  `herriman.org` docids **404 on the live host**. Recovered from Internet Archive
  captures of `herriman.org/elections.php` (key captures: 2021-08-11 primary-era,
  2021-12-11 post-general, 2024-07-15 full-2023). `source=wayback_herriman_org`;
  `source_url` is the exact `https://web.archive.org/web/<ts>id_/…` URL fetched
  (matches `_fetch_log.jsonl`), `original_url` the herriman.org address.

## Semantics / gotchas

- **`filing_type`**: `interim` = pre-primary, October-7/October-24 class, and 7-day
  pre-general reports; `summary` = the final report (30 days after the general, or —
  for a candidate eliminated at the primary — 30 days after the primary: Grimm 2025).
  **Never sum dollar figures across a candidate's filings** once extraction happens —
  reports within a cycle overlap (the repo-wide cf double-count trap).
- **`date`** is the filing date **as best known**; `date_precision` qualifies it:
  `exact_received` / `exact_signature` / `exact_stamp` (read from the PDF),
  `from_filename` (city filename, e.g. Hodges "DEC3rd"), `est_report_class` (the
  statutory due date printed on the form — most scanned filings), `est_capture_bound`
  (filed on/before that Wayback capture date — Ohrn 2429 only).
- **`duplicate_of`**: the city published each of Grimm's two 2025 filings under two
  URLs; the later-labeled docids (5785 = Aug 5 report, 5786 = Sep 11 report) are
  canonical and 5673/5719 point at them. **Filter `duplicate_of=''` for a
  distinct-document cut (48 docs)** — critical once dollars are extracted.
- **`format`**: `text` (17) = born-digital, `pdftotext -layout` works; `scanned` (33) =
  image PDFs needing OCR/vision (Henderson's 2023 three have an embedded low-quality
  OCR layer — still classified `scanned`; don't trust that layer for amounts).
- **Election join**: `matched_election_candidate` is the UPPER-CASE name in
  `../election_results/herriman_results_by_candidate.csv` (year-specific: `TEDDY
  HODGES` 2021 vs `TEDDY M HODGES` 2025). `join_confidence=none` on Esselman/Grange —
  they exist only in the (missing-from-election-data) 2021 mayoral primary; that's the
  flagged discrepancy, not a bad join.
- The elections page also hosts Declarations of Candidacy and Conflict-of-Interest
  disclosures (2025) — **not** campaign finance, deliberately not indexed here.

## Rebuild / extend

Next cycle (2027): the live `herriman.gov/elections` page will be rewritten — harvest it
before it turns over, or rely on Wayback again. Fetch with
`.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw` (browser UA
built-in; web.archive.org needs 20–45 s backoff between requests). The dollar-extraction
step (contributions.csv / expenditures.csv / cycle_totals.csv, Lehi/Logan pattern) is
future work — see repo `TODO.md` conventions and `/cf-vision-transcribe` for the
scanned-majority corpus.

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 1, 2025 cycle) — vision/ caches written

Transcribed **all 13** scanned 2025-cycle C&E filings via `/cf-vision-transcribe` (Read-tool
vision, **$0 Anthropic API**). `vision/*.json` = 41 contributions + 66 expenditures itemized.

- **Cache contract (provisional-standard, no build yet):** WJ `_did8` filenames
  (`sha1(index_path)[:8].json`) + WJ vision schema (contributions/expenditures + verbatim cover
  totals + balances); each cache carries a `_meta` block for lossless re-keying. Herriman forms
  have **no "$50 or less" aggregate line** → `contributions_50_or_less` null throughout.
- **STRUCTURING PENDING:** no `build_finance.py` yet — additive caches only; structuring build
  (CSVs + `cycle_totals`) is owner-gated later-tranche work, not scaffolded here.
- **Duplicate scans (already flagged in index via `duplicate_of`):** 5673→5785 (Grimm Aug-5
  primary) and 5719→5786 (Grimm Sept-11 primary-eliminated summary) are byte-identical re-uploads.
  Caches exist for BOTH members of each pair (identical financial content, distinct `_meta`);
  a build must dedup via the index `duplicate_of` column.
- **NEEDS_REVIEW — Grimm 2025 filer-error contradiction:** the Summary Page prints TOTAL
  CONTRIBUTIONS = `$0`/`"-0-"` while Schedule A itemizes $2,525 ($25 + $2,500 self-transfer;
  filer appears to have booked the $2,500 as beginning balance). Itemized rows preserved verbatim
  in all four Grimm caches; **cover-total field choice differs between the two report periods**
  (Aug-5 cache used Schedule A total "2525.00"; Sept-11 cache used Summary "-0-") — must be
  adjudicated when a herriman `build_finance.py` is created.
- Other verbatim-preserved defects: Palmer summary Column A vs B close-balance clerk mismatch
  (15,755.08 vs .98 — Column A retained); Palmer in-kind lines sum 3516 vs printed 3510.00;
  Brady interim `08efdd70` has no summary page (balances null); date typos "11/31/25",
  "11/5/2125" kept. Brady year-end `c019992c` is a YTD-only snapshot (empty itemized arrays,
  totals from Column B).
- Backup: `_backups/2026-07-17-cf-vision-t1/herriman/` (greenfield — nothing pre-existed).

## 2026-07-17 (wave-2) — CF VISION TRANSCRIPTION tranches 2 & 3 (2023, then 2021) — vision/ caches written

Transcribed **all 20 remaining scanned filings** via `/cf-vision-transcribe` (Read-tool vision,
**$0 Anthropic API**): **8 in the 2023 cycle** + **12 in the 2021 cycle**. With the tranche-1
2025 set, **all 33 scanned C&E filings across all three cycles (2021/2023/2025) are now cached**
(17 text filings need no vision). Same cache contract: `vision/<sha1(index_path)[:8]>.json`,
herriman schema (contributions/expenditures + verbatim cover totals + balances + `_meta`),
`contributions_50_or_less` null throughout (Herriman forms have no "$50 or less" aggregate line).
- **STILL NO `build_finance.py`** — additive caches only; the structuring build (CSVs +
  `cycle_totals`) remains owner-gated later work. Nothing else in the dataset was touched.
- **No duplicate/do-not-re-vision filings in 2023 or 2021** — every scanned row has
  `duplicate_of=''` (the byte-identical dup pairs were the 2025 Grimm 5673/5719, already cached).
- **Verbatim-preserved filer defects** (recorded, NOT corrected — see each cache `_meta.notes`):
  candidate-made non-standard tables with no date/purpose columns (Clint Smith 2021 both filings →
  null dates/purposes; Chris Roberts 2023 spreadsheet); Summary Column-A vs Schedule-A / Column-B
  contradictions (Jared Henderson 2023 interim "900" vs 2,496.12; Steven Shields 2023 zero-activity
  with YTD 3,110/2,767.53; Ohrn/Hodges 2021 zero-period summaries with YTD carryover); clerk
  one-digit slips (Palmer 2021 summary 11,420.88 vs .98; Bello interim 1,556..12 doubled decimal);
  itemized-vs-total arithmetic gaps left uncorrected (Palmer 2021 interim rows sum 7,893 vs printed
  7,885); blank/omitted cover totals (Aly Escobar 2021 interim total_expenditures null — Summary
  line blank); date typos kept ("06/2621", "Nov 26 20211", year-less handwritten dates); in-kind
  Schedule-C rows with no printed amount → amount null, in_kind true.
- Backup: `_backups/2026-07-17-wave2/herriman/campaign_finance/` (pre-existing 13 caches + index
  snapshotted before the run).

## 2026-07-17 — STRUCTURED LAYER BUILT (`build_finance.py`, CF-structuring wave)

`build_finance.py` (family **`vision_cache`**, shared `scripts/campaign_finance/vision_lib.py`)
now writes the derived CSVs — **`contributions.csv` (338) / `expenditures.csv` (265) /
`filing_totals.csv` (50 = the full index inventory) / `cycle_totals.csv` (18 candidate-cycles)**
— all regenerable, never hand-edited. **`validate_finance.py` PASS (0/0)**;
`validate_city.py herriman_city_council/` **0 FAIL** (24 PASS / 2 pre-existing WARN).

**TWO consumption paths, both through the shared normalization + reconciliation:**
- **Scanned (33)** → the vision caches → `vision_lib.build_result`.
- **Born-digital text (17)** → a §10-3-208 **Schedule A/B/C text parser** in `build_finance.py`
  (`_stdform_parse`, `pdftotext -layout`; extract_method `herriman_stdform/text`, NOT vision).
  **RECONCILIATION IS THE INTEGRITY GATE** — a parse that matches the form's printed Schedule
  total earns `high`; one that does not is flagged `needs_review`/`low`, kept verbatim, never
  adjusted. Amounts are distinguished from street-numbers/zips by the `$`-or-decimal rule;
  long name+address rows that wrap the amount to the next line are re-paired; the ≤$50
  unitemized aggregate becomes a **blank-donor `needs_review` row** (stated amount, no
  fabricated identity); ligatures ('ContribuƟons', 'Ma Basham') normalized before parsing.
  **13 of 17 reconcile both sides; 2 more one side; Palmer 5768 is Schedule-A-only (no
  cover/Schedule-B in the published PDF → contributions captured, stated blank).**
- **`reconcile_cash_only=True`** — Herriman's printed "TOTAL CONTRIBUTIONS RECEIVED (Schedule
  A)" counts CASH ONLY; Schedule C in-kind is a separate stated line (verified across 7 in-kind
  caches: Anderson/Garcia/Smith/Palmer/Esselman/Bello/Hodges).

**4 honest not-built inventory rows (unknown totals + dated reason, no silent drops):**
- **Grimm 5673 / 5719** — byte-identical duplicate re-uploads → **superseded** (canonical
  5785/5786 carry the money; `duplicate_of` honored). NEVER summed.
- **Basham 5784 (Aug-5) / 5802 (Pre-General)** — born-digital but the §10-3-208 section headers
  did NOT render in `pdftotext` (no reliable contrib/expend split) → **deferred to a vision
  tranche** (AVAILABILITY.md). Real money (~$5.8k + ~$1.7k) — Basham 2025's cycle total is a
  documented lower bound until they are visioned.

**Per-candidate REGIME (`vision_lib.detect_regimes`, decisions printed + eyeballed):** most
filers are per-period (incremental). One correction: **Lorin Palmer 2025** was auto-marked
cumulative from a monotone stated sequence, but its 3 filings' donor rosters are MUTUALLY
DISJOINT → forced `incremental` in `build_finance.py` (documented). **`cycle_overrides.csv`**
corrects two per-period filers whose Dec "summary" is itself a period report:
- **Teddy Hodges 2025** → raised 14350 / spent **13555.01** (expenditures disjoint across
  periods; cycle_totals' max() undercounted spend at 9585.93).
- **Lorin Palmer 2025** → raised **5541.02** / spent 12138.39 (**spent is a LOWER BOUND** — the
  Oct-7 5768 filing's expenditures are unrecovered).

**Verbatim filer/transcription discrepancies preserved, NEVER adjusted (flagged
`needs_review`):** the **Grimm 2025 $0-vs-$2525 contradiction** (5786 Summary prints "-0-" over
a $2,525 Schedule A — adjudication is the owner's, no override); Palmer 2021 interim rows sum
$7,893 vs printed $7,885; Esselman 2021 $8,897.43 vs $8,892.43; assorted one-cent slips
(Smith/Brady). **Two MIXED cycle review-flags left un-overridden per the "never sum what you
cannot honestly sum" rule: Clint Smith 2021 & Lorin Palmer 2021 (Mayor)** — per-period donor
lists but repeated self-loans/a repeat donor make a confident cycle sum impossible; the
`sum-interim` figure is flagged for human adjudication (a real follow-up).

**Query `cycle_totals.csv` for any candidate/race total — it encodes the dedup; never sum
`filing_totals` naively.** Regenerate: `python3 campaign_finance/build_finance.py` then
`python3 scripts/campaign_finance/cycle_totals.py herriman`. Backup of the docs modified this
run: `_backups/2026-07-17-cf-structuring/herriman/`.

## 2026-07-18 — CF EVIDENCE-PASS ADJUDICATION (owner-authorized) — 3 flags resolved

Backup: `_backups/2026-07-18-cf-adjudication/herriman/`. Two `cycle_overrides.csv` rows added;
`cycle_totals.csv` regenerated; `validate_finance.py` PASS (0/0), `validate_city.py herriman_city_council/`
24 PASS / 2 WARN / **0 FAIL**. No source value was altered (caches/CSVs untouched).

- **Grimm 2025 Council — $0-vs-$2,525 contradiction → CLOSED, no figure change.** Both the
  Aug-5 (5785) and Sep-11 (5786) filings itemize the SAME two self-contributions ($25 on 6/6 +
  $2,500 on 7/29 = **$2,525**, Schedule A page total $2,525.00). Only 5786's *Summary-page* cover
  line prints "-0-" (a second Schedule A page is marked "No Contributions"). Itemization sums to
  $2,525 on BOTH filings → the "-0-" cover is unambiguous **filer error** (he booked the $2,500
  self-transfer as beginning balance and zeroed the period cover). Published cycle total already
  reflects the truth: raised **$2,525.00** / spent **$1,690.21** (build's reconciliation fallback
  used the itemized $2,525 when the cover stated 0). **Unchanged.**
- **Clint Smith 2021 Mayor — self-loan NOT double-counted; but sum-interim was an UNDERCOUNT →
  OVERRIDE.** The repeated "Clint Smith Loan" $5,000 in the Aug (2097) and Oct (2400) filings is
  TWO separate real infusions, not one restated: Oct spent $11,185.60 against a $1,283.39 opening
  balance, and `1283.39 + 10000 − 11185.60 = 97.79` (= stated close) proves the 2nd $5,000 was real
  cash → no deduction. Separately, the Dec-2 (2456) "summary" is itself a period report ($7,795 /
  $7,892.79), so `cycle_totals` max(summary, sum-interims) DROPPED the Dec period (same defect
  already overridden for Hodges/Palmer 2025). Corrected to the 3-period sum: raised **$28,610.56**
  (10815.56+10000+7795) / spent **$28,635.96** (9557.57+11185.60+7892.79); filer's own final-report
  YTD (28,610.96/28,610.96) confirms within documented clerk slips. **Was $20,815.56/$20,743.17.**
- **Lorin Palmer 2021 Mayor — self-contributions all DISTINCT; sum-interim was an UNDERCOUNT →
  OVERRIDE.** The "Lorin & Christi Palmer" self-contributions carry distinct dates AND amounts in
  every filing (7/16 $4,700 + 7/30 $3,500 Aug; 10/20 $5,000 + 10/21 $2,000 Oct; 11/5 $10,800 Dec) —
  no repeated date+amount → genuine separate infusions, no deduction. Same Dec-summary-is-a-period
  defect. Corrected to the 3-period sum: raised **$32,038.06** / spent **$31,782.48**, which EXACTLY
  equal the filer's own final-report YTD (2453 Col B). (Oct itemized rows sum $7,893 vs printed cover
  $7,885 — the city-verbatim $7,885 is used, matching the YTD.) **Was $20,617.18/$20,162.86.**

The two prior "MIXED" review-flags (Smith/Palmer 2021) are now documented `override` rows, not open
flags. The paragraph above (pre-2026-07-18) describing them as "left un-overridden" is superseded.

## 2026-07-19 — BASHAM ×2 TYPED-MONEY VISION TRANCHE (CF-STRUCTURING PACKAGE) — the 2 deferred filings built

The last 2 not-built dollar rows (the born-digital Basham 5784/5802 whose §10-3-208 section
headers never rendered in `pdftotext -layout`, deferred 2026-07-17) are now **vision-transcribed**
(Read-tool, **$0 Anthropic API**) into `vision/73687d99.json` (5784) + `vision/c96909aa.json`
(5802) and built. Backup: `_backups/2026-07-19-lm-wave/herriman-cf/`. **`validate_finance.py`
PASS (0/0)**; `validate_city.py herriman_city_council/` **0 FAIL** (23 PASS / 3 WARN — all WARNs
pre-existing/unrelated: the 2 `provenance` extension cols + a `weeks/` staleness from the
concurrent votes work, NOT campaign_finance). Counts: contributions **338→352** (+14), expenditures
**265→298** (+33), filing_totals **50** (unchanged inventory), cycle_totals **18**. The ONLY
remaining not-built rows are now the Grimm 5673/5719 byte-identical duplicate re-uploads (superseded).

- **Matt Basham 5784 (2025 Pre-Primary, Aug-5, `73687d99`):** 5 cash contributions
  reconcile to the cover **$5,799.00** (incl. two candidate self-loans `Matt Basham (LOAN)`
  $999 + $1,000 → self_funded $1,999.00); 7 Schedule-C in-kind rows appended `in_kind=true`
  (Governing Group ×6 + Cinnamen LLC; excluded from the cash cover under `reconcile_cash_only`).
  30 expenditures, cover **$4,850.83**. **VERBATIM FILER SLIP, NOT CORRECTED:** the 30 itemized
  expenditure amounts sum **$4,850.76** (page-2 rows sum $3,522.54 vs the page's own printed
  subtotal $3,522.61 — a $0.07 arithmetic error; all page-2 amounts + the refund `($8.59)` and
  the date typo `07/18/2028` verified at 400 dpi) → **expenditure side flagged `low`/`needs_review`,
  `recon_delta_expend=-0.07`**, kept verbatim.
- **Matt Basham 5802 (2025 Pre-General 7-day, Oct-27, `c96909aa`):** Schedule A empty (0 cash,
  reconciles at $0.00); 3 expenditures reconcile to **$1,693.78** (verbatim recipient typo
  "Sun Lighographing" on 10/06 retained); 2 Schedule-C in-kind ($2,500 Salt Lake Board of
  Realtors / $60 Sam Winkler). Filer's Column-B YTD is internally inconsistent (line-2 YTD
  expend 7,739.31 vs line-6 subtract 7,736.31, a $3.00 YTD-column slip) — the Column-A
  this-period basis is unaffected and is what is recorded.
- **CYCLE-TOTAL CHANGE — Matt Basham 2025 Council: raised `$2,025.00`→`$7,824.00`, spent
  `$1,194.70`→`$7,748.34`** (`cycle_overrides.csv`, basis `override`). Was a lower bound built
  from only the Oct-7 5772 + Final 5880; now the full 4-filing incremental (per-period, disjoint
  expenditure dates) chain. Raised = 5799.00+2025.00+0+0 = 7824.00 (matches 5802 Summary Col-B
  YTD 7,824.00); spent = 4850.83+1194.70+1693.78+9.03 = 7748.34 (the 3-interim sum 7,739.31
  matches 5802 Col-B YTD 7,739.31; +9.03 recovers the Nov-7 Final period the `max(summary,
  sum-interims)` dedup would otherwise drop — same structural defect adjudicated for
  Hodges/Palmer/Smith).
- **LOCKED FIGURES VERIFIED UNCHANGED** (no drift): Clint Smith 2021 Mayor **$28,610.56 /
  $28,635.96**; Lorin Palmer 2021 Mayor **$32,038.06 / $31,782.48**; Lorin Palmer 2025 Mayor
  **$5,541.02 / $12,138.39**; Grimm 2025 raised **$2,525.00**. All still `override`/as-built.

Regenerate: `python3 campaign_finance/build_finance.py` then
`python3 scripts/campaign_finance/cycle_totals.py herriman`.
