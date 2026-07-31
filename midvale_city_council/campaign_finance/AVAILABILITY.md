# campaign_finance/ — availability & gap log

As-of **2026-07-13**. Additive **acquisition-only** dataset (source type 6, expand-city-sources).
No existing dataset was modified; no dollar amounts are extracted yet.

## What exists

- **City recorder page is the primary source and holds the full modern record.**
  `https://www.midvale.utah.gov/government/departments/recorder_s_office/campaign_financial_disclosures.php`
  (Revize CMS, one flat HTML page) links every posted municipal campaign-finance
  statement for **2017, 2019, 2021, 2023, 2025**. Files live in the Revize Document Center
  file tree under two folders:
  - `Document Center/.../Recorders Office/Campaign Financial Disclosures/<year>/…`
  - `Document Center/.../Recorders Office/Elections/2025/…` (the 2025 Oct-28 + Dec-4 reports
    are filed here, while the 2025 Oct-7 reports sit in the Campaign Financial Disclosures
    folder — split by upload batch, both are the same city page).
  - One 2023 Bart Benson December file sits at the flat `Document Center/` root (city
    mis-file); captured anyway.
  Paths carry spaces + a literal `&` — every URL is `%20`/`%26`-encoded (recon rule).
- **State: `disclosures.utah.gov` / `municipal.utah.gov` — a real SECOND source for 2023
  only.** The Lt. Governor's municipal-disclosures tree exposes
  `…/Municipal/salt lake_2023_Midvale/` (dir listing GETs 200; individual files GET fine).
  It holds **24 docs for 2023 — 4 of them NOT on the city page** (Bart Benson & Bonnie
  Billings "2023 Election Campaign Finance Statement"; Dustin Snow & Ben Umeadi "Final").
  Those 4 were fetched into `raw/state/` (`source=state_disclosures`). The **2019, 2021 and
  2025** state folders return *"…Midvale does not exist"* (verified 2026-07-13) — the state
  tree only backfilled the 2023 cycle for Midvale.
- **Salt Lake County Clerk** (`saltlakecounty.gov/clerk/elections/financial-disclosures/`):
  checked 2026-07-13 — hosts **county-office, metro-township and school-board** filings and,
  for *municipal* candidates, merely points to `disclosures.utah.gov` + the county easyvote
  portal (county filers). **No Midvale municipal filings** ("midvale" absent from the page).
  Midvale is a city (not a metro township) → its candidates file with the city recorder per
  Utah Code §10-3-208. Not a source.
- **Wayback / pre-2017:** the city page's own folder tree begins at **2017**; no earlier
  (2013/2015) campaign-finance folder or link surfaced. Utah municipal filings that old are
  typically paper at the recorder (GRAMA territory) — out of scope. No CMS-migration recovery
  was needed because the live city page already serves 2017→2025.

## Coverage — 84 filings, 5 cycles

| Cycle | Seats up | Filings | Candidates | text / scanned | Source |
|---|---|---|---|---|---|
| **2017** | Mayor + D4 + D5 | 16 | 11 | 10 / 6 | city page |
| **2019** | D1 + D2 + D3 | 11 | 7 | 0 / 11 | city page |
| **2021** | Mayor + D4 + D5 | 11 | 6 | 6 / 5 | city page |
| **2023** | D1 + D2 + D3 | 25 | 7 | 6 / 19 | city page (21) + state (4) |
| **2025** | Mayor + D4 + D5 | 21 | 7 | 5 / 16 | city page |

- **27 born-digital `text` / 57 `scanned`.** Format is per-file, determined by whether
  `pdftotext -layout` yields a real text layer. The 2019 cycle is 100% scanned; the modern
  cycles are mixed (candidates email in whatever they have — some are born-digital
  spreadsheet/state-form exports with donor rows and dollar amounts, most are printed-and-
  scanned signed statements). A few 2025 filings carry an **empty AcroForm shell over raster
  images** (a fillable template that was printed, filled, and re-scanned) — correctly
  `scanned` (0 extractable chars, no form-field values), not born-digital.
- **Every candidate in every in-scope GENERAL election (2017–2025) has ≥1 filing**, and every
  primary candidate the filings imply is already in `../election_results/midvale_races.csv`.

## Election-record cross-check — NO discrepancies found

Unlike some sibling cities (e.g. murray, whose filings proved an unlisted 2021 primary),
**Midvale's campaign-finance record surfaces no gap in the election dataset.** Verified
2026-07-13 (`index.csv` `matched_election_candidate` + a full set-difference against
`../election_results/midvale_results_by_candidate.csv`):

- **Zero orphan filers** — all 84 filings map to a candidate listed in the election results.
- The only election candidate **without** a filing is **Andrea B. Person (2017 Mayor
  primary, 4th of 6)** — a candidate-side publishing gap (the city posted nothing for her),
  not an election-record error. All other 2017 mayoral / D4 primary filers (Jankovich,
  Hansen, Millerberg, Johnson, Stoddard) are explained by the 2017 primaries already in the
  election data; the 2019 D2 primary (Chamberlain's Aug-6 + Sept-12 filings) is likewise
  already recorded.

*(No edit was made to `election_results/` — this is an acquisition layer.)*

## Roster context worth knowing (from `../CLAUDE.md`)

- **Gettel council→mayor.** Dustin Gettel filed as a **D5 council** candidate in **2017 and
  2021**, then as a **Mayor** candidate in **2025** (won, 60.89%). His filings straddle the
  council→mayor transition — join on person + year, not a fixed office.
- **Stevenson resigned.** Marcus Stevenson (2021 Mayor winner) filed the 2021 mayoral
  reports here, then **resigned**; Gettel was appointed mayor (sworn 2025-01-03) and won 2025;
  Denece Mikolash (2025 D5 filer) took Gettel's vacated D5 seat. Mid-term **appointments do
  not trigger campaign-finance filings**, so there is correctly no interim-appointment filing
  for Gettel-as-appointee or Mikolash-as-appointee — only their **2025 candidate** filings.

## The double-count trap (do not sum filings)

Candidates file **several statements per cycle** — pre-primary / pre-general interims plus a
year-end or "Final" summary — so there is **not one filing per candidate**. The 2023 state
"Final" / "Election Campaign Finance Statement" docs likely **overlap** the city page's
December filing for the same candidate (flagged per-row in `note`). Any per-candidate or
per-race dollar total must use the repo's dedup rules
(`scripts/campaign_finance/cycle_totals.py`) once amounts are transcribed — **never** sum
rows of this index.

## Known limits / honest gaps

- **No dollar extraction yet** (bluffdale/murray-style acquisition layer). 57/84 filings are
  scanned → a future structured pass needs OCR/vision (`cf-vision-transcribe`).
- **`filing_type` blank on 14 rows** — the 2017 bare-name and 2019 "Campaign Finance
  Statement" labels state no reporting period on the page; classified honestly as blank
  rather than guessed. `date` for those falls back to the cycle anchor `<year>-11-01` with
  `date_precision=cycle_inferred`.
- **Andrew Person 2017 / any withdrawn candidate:** no filing posted → honest empty.
- **Duplicate upload:** the 2019 Sophia Hawes-Tingey "Campaign Finance Statement" is posted
  twice (a `(1)` copy) — both retained, flagged in `note`.
- **Re-saved doc:** Heidi Robinson 2023 November is served as `*.pdf.docx.pdf` (a docx
  re-export) — flagged.
- **Redacted 2025 Oct-7 reports:** the city posts `_Redacted` versions (donor detail
  redacted) — flagged in `note`; these are the record the city publishes.

## How verified / method

- All bytes fetched GET-only via `scripts/polite_fetch.py` (browser UA, throttled, retried);
  url/status/bytes/sha256 logged per attempt in `raw/_fetch_log.jsonl` (city, 80) and
  `raw/state/_fetch_log.jsonl` (state, 4).
- Candidate→office/district mapping and the `in_election_results` join are derived from
  `../election_results/midvale_results_by_candidate.csv` (never fabricated); `join_confidence`
  is `exact` for all 84 (every filer matched a listed candidate).
- Rebuild: `python3 mv_cf_build.py parse` (re-harvest the saved page → metadata + fetch
  batch) then `python3 mv_cf_build.py index` (format-probe every PDF, write `index.csv`); the
  4 state rows are appended by the documented state-folder step. Validate with
  `.claude/skills/expand-city-sources/scripts/validate_dataset.py`.

## 2026-07-17 — structured-layer availability notes
- **17 `format=text` rows have junk text layers** (fillable-template glyph noise or
  scan-junk, verified on samples: Umeadi Final, Billings Election-CF-Statement, Snow
  post-general) — they are NOT parseable born-digital text and are NOT yet
  vision-transcribed; `filing_totals.csv` carries them as honest unknown-totals rows.
  Future vision tranche candidates (2021 ×6, 2023 ×6, 2025 ×5).
  **✅ DONE 2026-07-19** — all 17 transcribed (typed-money vision tranche; see the
  CLAUDE.md 2026-07-19 note). Nuance: the four 2021 Gettel/Stevenson filings turned out
  to be fully born-digital (transcribed from `pdftotext`), not junk; the rest were
  image-rendered. `vision/` now 57; only the 27 below-2020-floor 2017/2019 filings
  remain inventory-only.
- The 27 below-2020-floor 2017/2019 filings are inventory-only (acquired, not
  transcribed) — same status as murray/magna's below-floor tranches.
- Structured dollar queries go through `cycle_totals.csv` (per-candidate regime dedup +
  5 documented `cycle_overrides.csv` corrections), never by summing `filing_totals.csv`.
