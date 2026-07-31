# campaign_finance/ — Midvale City municipal campaign-finance disclosures

**ACQUISITION-ONLY layer** (built 2026-07-13 by the expand-city-sources skill, source
type 6): every campaign-finance statement Midvale City publishes for its municipal
candidates, as raw originals + a §9-contract index. **No dollar amounts are extracted
yet** — the structured contributions/expenditures pass (`cf-vision-transcribe` →
`build_finance.py`) is a later step. **57 of 84 filings are scanned.**

```
raw/                  80 city-page originals (all PDF), never modified
raw/_fetch_log.jsonl  bytes-level provenance (url, status, sha256) per city fetch
raw/state/            4 state-site (disclosures.utah.gov) originals — 2023 net-new only
raw/state/_fetch_log.jsonl   provenance for the state fetches
index.csv             one row per filing — SCHEMA_SPEC §9 campaign_finance contract header + extras
AVAILABILITY.md       what exists / what doesn't / election cross-check (read before quoting)
mv_cf_build.py        reproducible harvest+index builder (session helper, kept in-dataset)
mv_cf_filings.tsv     intermediate parsed metadata (regenerable by mv_cf_build.py)
```

## Coverage — 84 filings, 5 cycles

| Cycle | Seats up | Filings | Candidates | Source |
|---|---|---|---|---|
| 2017 | Mayor + D4 + D5 | 16 | 11 | city page |
| 2019 | D1 + D2 + D3 | 11 | 7  | city page |
| 2021 | Mayor + D4 + D5 | 11 | 6  | city page |
| 2023 | D1 + D2 + D3 | 25 | 7  | city page (21) + **state disclosures (4)** |
| 2025 | Mayor + D4 + D5 | 21 | 7  | city page |

Authoritative source: the city recorder's
`campaign_financial_disclosures.php` (Revize Document Center). The state
`disclosures.utah.gov` / `municipal.utah.gov` tree is a **second source for 2023 only** (its
2019/2021/2025 Midvale folders return "does not exist"); the Salt Lake County Clerk hosts no
Midvale municipal filings (all verified 2026-07-13 — see AVAILABILITY.md).

## index.csv — the §9 contract + extras

Contract columns first (`date, candidate, office, election_year, filing_type,
reporting_period, title, source_url, retrieved_date, format, extraction_method, path`), then
Midvale extras: `district`, `source` (`city_cf_page` | `state_disclosures`),
`in_election_results` (`yes` for all 84), `matched_election_candidate` (the UPPER-CASE name
in `../election_results/midvale_results_by_candidate.csv`), `join_confidence` (`exact`),
`date_precision`, `filing_label_verbatim` (the raw page/anchor label), `pages`, `note`.

- **`candidate`** is the canonical election-roster name (title-cased from
  `matched_election_candidate`) so a person is one value across their filings; the messy
  page label is preserved verbatim in **`filing_label_verbatim`**.
- **`office`/`district`** come from the election roster for that `(candidate, election_year)`
  — never guessed. Mayor rows have blank district.
- **`date`** is the filing's reporting-period date where the page states one, else a cycle
  anchor. **`date_precision`** says which: `page_stated` (an explicit M/D/YYYY or "Month D,
  YYYY" on the page, 45 rows), `label_month` ("Month YYYY" → first of month, 18 rows),
  `cycle_inferred` (`<year>-11-01`; the label gave no period, 17 rows).
- **`filing_type`**: `interim` = a dated pre-primary/pre-general periodic statement (47);
  `summary` = a December / "Final" / "year-end" / candidacy statement (23); **blank** = the
  page label stated no period (14 — mostly 2017 bare-name + 2019 "Campaign Finance
  Statement"). Classified from the page label only (acquisition layer) — not by opening PDFs.
- **`format`**: `text` (27, born-digital text layer) vs `scanned` (57, image PDF incl.
  empty-AcroForm-over-raster 2025 filings). Determined by a real `pdftotext -layout` yield;
  `extraction_method` records that no text was extracted (deferred).

## THE DOUBLE-COUNT TRAP (do not sum filings)

Candidates file several statements per cycle (pre-primary, pre-general, year-end/Final).
The **4 state `source=state_disclosures` 2023 rows likely OVERLAP** the city page's December
filing for the same candidate (Benson, Billings, Snow, Umeadi) — retained for completeness,
flagged in `note`, **not** deduped. Any per-candidate / per-race total must run the repo's
`scripts/campaign_finance/cycle_totals.py` dedup once amounts are transcribed — never sum
this index or a future `filing_totals`.

## Flags worth knowing (details in AVAILABILITY.md)

- **No election-record discrepancy.** Every filing matches a listed election candidate and
  every implied primary is already in `midvale_races.csv`. The only election candidate with
  no filing is **Andrea B. Person (2017 Mayor primary)** — a candidate-side empty, not an
  election error. (Contrast murray, whose filings exposed an unlisted 2021 primary.)
- **Gettel council→mayor / Stevenson resigned.** Gettel filed as D5 council (2017, 2021) then
  Mayor (2025); Stevenson filed the 2021 mayoral reports then resigned (Gettel appointed, won
  2025; Mikolash took D5). Appointments file no campaign finance — join on person + year.
- **2025 Oct-7 reports are city-posted `_Redacted` versions**; the 2019 Sophia Hawes-Tingey
  statement is a **duplicate upload**; Heidi Robinson 2023 Nov is a `*.pdf.docx.pdf` re-save
  — all flagged in `note`.

## Rebuild / extend

1. Re-fetch the city page and re-parse: `python3 mv_cf_build.py parse` (writes
   `mv_cf_filings.tsv` + a fetch batch; the saved page is re-downloaded via `polite_fetch.py`).
2. Fetch new filings into `raw/` (`polite_fetch.py --batch`, browser UA, URL-encode `%20`/`%26`).
3. `python3 mv_cf_build.py index` — format-probes every PDF and writes `index.csv`.
4. For a new cycle, also check `disclosures.utah.gov/Municipal/salt lake_<year>_Midvale/`
   for state-only net-new files (append with `source=state_disclosures`).
5. Validate:
   `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py <this dir>` (PASS).

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 1, 2025 cycle) — vision/ caches written

Transcribed **all 16** scanned 2025-cycle C&E filings via `/cf-vision-transcribe` (Read-tool
vision, **$0 Anthropic API**). `vision/*.json` = 240 contributions + 94 expenditures (15
single-report + 1 multi-report).

- **Cache contract:** pure `sha1(index_path)[:8].json` + WJ vision schema + `_meta` block.
  **STRUCTURING PENDING** (no `build_finance.py` yet — additive caches only, owner-gated later work).
- **Midvale form quirks (captured honestly):** **no date column** on Schedule A/B → every row
  `date` is null (honest gap, not omitted); **no purpose column** → expenditure `purpose` null,
  payee verbatim in `recipient`. Schedule A splits **Part I (>$50, itemized)** / **Part II ($50 or
  less, ALSO itemized by name)**; the Part II subtotal is in `contributions_50_or_less` AND the
  sub-$50 donors are in `contributions[]` — a build must NOT double-count the aggregate against the
  itemized rows.
- **Bryant Brown — dedup needed:** two interim filings — `4188750d` (Oct-7 report) and `c47ca64d`
  (Oct-28, transcribed as **`reports[]` multi-report** because its Summary Page carries fully-filled
  Column A thru-Oct-7 AND Column B thru-Oct-28). The multi-report's Report-A duplicates the standalone
  Oct-7 filing — watch for double-count.
- **DOUBLE-COUNT TRAP:** interim vs Dec-4 Final (Column C) filings are cumulative — never sum a
  candidate's filings; use the final/summary. Several Schedule-B **subtotal-vs-TOTAL gaps** (cumulative
  TOTAL EXPENDITURES > this-page subtotal — Steverson, Boyer) retained verbatim, unreconciled.
- Name variants preserved (Brandee/Brandy Boyer; Gettel/Gettle) and negative ending balances
  (Mikolash -67.42; Boyer/Steverson chains) copied verbatim.
- Backup: `_backups/2026-07-17-cf-vision-t1/midvale/` (greenfield — nothing pre-existed).

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 2, 2023 + 2021 cycles) — vision/ caches written
Transcribed **all 24** remaining scanned filings via `/cf-vision-transcribe` (Read-tool vision,
**$0 Anthropic API**) — **19 of the 2023 cycle + 5 of the 2021 cycle**. `vision/*.json` now
totals **40** (16 from tranche 1 + 24). Same cache contract (`sha1(index_path)[:8].json`, WJ
vision schema + `_meta`). **STRUCTURING STILL PENDING** (no `build_finance.py` — additive caches
only, owner-gated). 366 contributions + 281 expenditures; all single-report (no bundles this
tranche).
- **Form-era difference (captured honestly):** the **2023-cycle** forms DO carry filled **Date
  + Purpose** columns (unlike the 2025 forms) → `date`/`purpose` populated, not nulled. No Part
  II ($50-or-less) aggregate and no beginning-balance line on most → those `null`. The 2021
  forms vary (some have the Part I/Part II split — Robert Hale — others don't).
- **DOUBLE-COUNT TRAP unchanged:** interim vs Dec Final are cumulative — never sum a candidate's
  filings; several candidates' itemized rows don't reconcile to the printed cover TOTAL (Feinberg,
  Robinson, Snow, Billings) — printed totals kept verbatim, itemized rows NOT adjusted.
- **Same-campaign disagreements kept verbatim, NOT reconciled:** Heidi Robinson's two interim
  filings (`15727d1f`, `5ea536d2` — the latter is the `*.pdf.docx.pdf` re-save) disagree on a few
  amounts (Michalik 25 vs 75; three expenditure cents) — both preserved. Low-confidence handwritten
  donor names flagged for human spot-check (e.g. `5ea536d2` row 9, `42cac402` "Malak <surname>").
  Dustin Snow's state "Final" (`bb6c3d34`) is actually the Midvale POST-GENERAL form, transcribed
  under its true index_path `raw/state/2023_state_Dustin-Snow_Final.pdf`.
- Backup: greenfield (all 24 caches new; nothing pre-existed to overwrite).

## 2026-07-17 — STRUCTURED LAYER BUILT (the vision-cache reference implementation)
`build_finance.py` (family **`vision_cache`**, shared helpers
`scripts/campaign_finance/vision_lib.py`) now writes the four derived CSVs —
`contributions.csv` (587) / `expenditures.csv` (368) / `filing_totals.csv` (84 rows =
the FULL inventory: 40 vision-transcribed + 44 honest not-transcribed rows with dated
reasons) / `cycle_totals.csv` (38 candidate-cycles) — all regenerable, never hand-edited.
`validate_finance.py` PASS (0/0). Key decisions, all evidence-based:
- **The "cumulative — never sum" guidance above is REFINED, not repealed:** regimes are
  PER CANDIDATE (`vision_lib.detect_regimes`, decisions printed by every build): most
  2023 filers file cumulative restatement chains (latest wins; earlier snapshots marked
  superseded), while the 2025 filers + Hale 2021 file per-period reports (sum them).
  Query `cycle_totals.csv` — it encodes the dedup; never sum `filing_totals` naively.
- **Five per-period filers' Dec "summary"-typed filings are themselves period reports**
  (the millcreek precedent) — corrected via documented `cycle_overrides.csv` rows
  (Mikolash, Steverson, Boyer, Lilbok, Hale-2021; basis=`override`, reason carried).
  David B. Fair 2025 was left as computed + MIXED-flagged pending owner adjudication —
  **ADJUDICATED 2026-07-18, see the dated note below** (basis now `override`, figures
  unchanged at 1,427.80/1,427.80).
- **Bryant Brown 2025-10-28 is a two-report bundle** whose first sub-report is a
  "Summary Column A" RESTATEMENT of his 10-07 filing — rows excluded by
  `vision_lib.build_result`'s label-based restatement rule (noted on the row); both his
  filings now reconcile exactly.
- **Reconciliation:** 22/40 transcribed filings reconcile both sides against printed
  covers; 15 carry verbatim filer/transcription mismatches (flagged `needs_review`,
  never adjusted); the `raw/state/` Dec copies of Umeadi/Billings/Benson are duplicate
  state-portal copies of transcribed city summaries (noted; no money lost).
- **17 format=text rows are NOT transcribed** — their "text" layers are template/scan
  junk (verified on samples); queued as a vision follow-up in AVAILABILITY.md. The 27
  below-floor 2017/2019 filings remain inventory-only.

## 2026-07-18 — DAVID B. FAIR 2025 MAYOR — MIRROR-SWAP ADJUDICATED (owner-authorized)
The one MIXED-flagged residual from the structured build. Re-rendered both interim
filings (Read-tool page renders of `raw/2025_10_David-Fair.pdf` + `raw/2025_11_David-Fair.pdf`).
**Verdict: UNAMBIGUOUS — the columns are NOT swapped; both filings are correctly oriented
per their own Schedule A/B headers.** The build-time "mirror-swap" (Oct-7 = 550/877.80 vs
Oct-28 = 877.80/550, the same two numbers on opposite sides) is a **real-world coincidence
of the actual campaign narrative, not a transcription error:**
- **Oct-7** (box "Prior to General Election October 7, 2025", signed 10-3-25): Schedule A
  *Itemized Monetary Contributions Received* lists 5 named DONORS — Norman Stevens/Phil
  Mecham/Maurine Helm 100 ea, Mary Ellen Reid 200 (Part I=500), Mary Owens 50 (Part II) =
  **550 raised**; Schedule B *Itemized Expenditures* = Midvale City filing fee 50 + Signs on
  the cheap 827.80 = **877.80 spent**; close −327.80.
- **Oct-28** (box "October 28, 2025", signed 10-28-25): Schedule A = **David Fair 877.80**
  (self-contribution); Schedule B = **"Return all donations" 550.00** (refund of the Oct-7
  donations); its Summary Page carries the decisive proof — **Col A (thru Oct-7)=550/877.80
  AND Col B (thru Oct-28)=877.80/550**, running the balance −327.80 → **0.00**. Donors on the
  contribution side, vendors/refunds on the expenditure side, in BOTH filings.
- **Cycle total = the filer's own stated per-period gross sums**, unchanged at **$1,427.80
  raised / $1,427.80 spent** (550+877.80+0 / 877.80+550+0; Dec-4 Final is a 0/0 period).
  Documented in `cycle_overrides.csv` (basis=`override`) so the number is locked and the
  MIXED flag cleared — no caches touched (they were already correctly oriented). Backup:
  `_backups/2026-07-18-cf-adjudication/midvale/`. `validate_finance` PASS (0/0),
  `validate_city midvale` 0 FAIL.

## 2026-07-19 — TYPED-MONEY VISION TRANCHE (the 17 above-floor `format=text` filings)
Transcribed the **17 remaining `format=text` filings above the 2020 floor** (2021 ×6, 2023 ×6,
2025 ×5 — the set AVAILABILITY.md flagged as "junk text layer / vision deferred"), via
`/cf-vision-transcribe` (Read-tool + `pdftotext`, **$0 Anthropic API**). `vision/*.json` is now
**57** (was 40). Rebuilt `build_finance.py` + `cycle_totals.py midvale`; `validate_finance` **PASS (0/0)**.
- **The "17 junk-text" label was only partly right:** the four 2021 Gettel/Stevenson filings are
  fully **born-digital** (clean, complete `pdftotext -layout` incl. the appended itemized donor
  lists) and were transcribed from text; the rest (fillable-template rasters / scans) were
  rendered (`pdftoppm -r 150`) and read as images. Bryant S. Brown 2021 ×2 = legitimate
  **zero-activity** ("no contributions/expenditures") reports (0/0).
- **Derived CSV growth:** `contributions.csv` 587→**918**, `expenditures.csv` 368→**526**;
  `filing_totals.csv` inventory-only ("not transcribed") rows 44→**27**; both-sides-reconcile
  22→**33** (recC 30→45, recE 25→38).
- **State-portal Dec copies are NOT double-counted** (verified): Umeadi state `Final` = a NIL
  report (0/0); Billings state `Election-CF-Statement` (9,725.29/6,296.27) and Benson state copy
  (0/2,376.68) are cumulative restatements SUPERSEDED by each candidate's later city Dec summary —
  the cycle totals are unchanged (Billings 9,893.29/6,626.38; Umeadi 376.04/376.04; Benson
  0/2,376.68). Snow's city Dec summary (2023_18) filled a real gap (his cycle 0→**1,361.64/1,361.64**);
  Glover's Dec summary populated **0/643.73**.
- **6 `cycle_overrides.csv` changes** (all page-proven, `basis=override`), because the newly
  itemized reports exposed **per-period Midvale filers** whose Dec "summary" is itself a period
  report (the millcreek pattern; same as the pre-existing Hale-2021/Mikolash/Steverson set):
  - NEW: **Dustin Gettel 2021** 13,883.29/**11,534.61** (mixed-scope Final: cumulative contributions,
    period-only expenditures → Column C is authoritative); **Marcus Stevenson 2021**
    11,273.65/11,067.03 (Column C; disjoint periods); **Dustin Gettel 2025 Mayor**
    32,297.13/25,304.99 (Column D; the Dec-4 is a period); **Bryant Brown 2025** 2,332.00/**2,364.00**
    (the filer's own Column-D campaign total — summing the reports' itemized expenditures over-counts,
    the max()-rule under-counts).
  - UPDATED (prior overrides went stale when this wave added a period): **Rainer Lilbok 2025**
    23.56/3.56 → **212.25/192.25** (+Oct-7 188.69/188.69); **Brandee Boyer 2025** 994.94/1,017.46
    → **1,327.27/1,327.27** (+Oct-28 332.33/309.81).
- **LOCKED figure held:** **David B. Fair 2025 = $1,427.80 / $1,427.80** — untouched (no Fair filing
  in this tranche; his adjudicated override is unchanged and did not drift).
- **Honest verbatim mismatches retained, NOT adjusted:** Stevenson 2021 ×2 Schedule-B
  subtotal-vs-TOTAL gaps (−314.74 / −291.21); Snow 2023 contributions cover 1,361.64 vs itemized
  1,126.64 (−235.00); Boyer 2025 sub-$50 un-itemized spend gap (−9.81); Billings/Glover blank-cover
  totals-only (reconcile=unknown, not a fabricated mismatch). Brown's messy negative balances copied verbatim.
- Backups: `_backups/2026-07-19-lm-wave/midvale-cf/` (pre-change CSVs + `vision-before/` 40 caches +
  `after/` post-change CSVs). Vision caches were additive (17 net-new; none overwritten).
