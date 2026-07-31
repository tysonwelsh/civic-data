# utah_county / elections — verification report (built 2026-07-20)

Everything below is printed by `python3 build_elections.py` at every rebuild — this file
records the shipped state and the reasoning behind each residual.

## What was built from what

| year | election | source (raw/) | grain | long rows | suppressed rows |
|---|---|---|---|---|---|
| 2016 | general | GEMS canvass summary PDF | countywide only | 117 | 0 |
| 2016 | regular primary | GEMS canvass summary PDF | countywide only | 36 | 0 |
| 2017 | municipal general | EVS official summary PDF | countywide only | 127 | 0 |
| 2017 | municipal primary (Lehi only) | EVS official summary PDF | countywide only | 12 | 0 |
| 2018 | general | SOVC xlsx workbook | precinct | 29,050 | 2,321 |
| 2018 | regular primary | SOVC xlsx workbook | precinct | 3,705 | 434 |
| 2019 | municipal primary | SOVC wide CSV | precinct | 1,644 | 90 |
| 2019 | municipal general | scanned SOVC PDF (OCR) + certified summary | precinct + countywide totals | 1,446 | 0 |
| 2020 | presidential primary | SOVC wide CSV | precinct | 7,333 | 1,240 |
| 2020 | regular primary | SOVC wide CSV | precinct | 3,494 | 78 |
| 2020 | general | SOVC wide CSV | precinct | 25,247 | 1,036 |
| 2021 | municipal primary | SOVC wide CSV | precinct | 1,888 | 304 |
| 2021 | municipal general | SOVC wide CSV (incl. RCV rank columns) | precinct | 6,418 | 1,625 |
| 2022 | regular primary | Electionware official summary PDF | countywide only | 35 | 0 |
| 2022 | general | SOVC wide CSV (official suppressed) | precinct | 22,495 | 7,811 |
| 2023 | municipal primary | born-digital precinct-summary PDF | precinct | 1,791 | 0 |
| 2023 | municipal general | Electionware official summary PDF | countywide only | 107 | 0 |
| 2024 | presidential primary | SOVC wide CSV | precinct | 2,100 | 1,625 |
| 2024 | regular primary | SOVC wide CSV (merged small precincts) | precinct | 6,735 | 0 |
| 2024 | general | SOVC wide CSV | precinct | 61,269 | 7,448 |
| 2025 | municipal primary | SOVC wide CSV | precinct | 3,823 | 0 |
| 2025 | municipal general | SOVC wide CSV ("Simple Redacted") | precinct | 10,618 | 5,072 |
| 2026 | regular primary | born-digital precinct-summary PDF | precinct | 8,969 | 0 (19 whole precincts withheld) |

Long file total: **198,459 rows** (`utah_county_results_long.csv`).
By-contest: **1,044 contest×candidate rows / 288 contests** (`election_results_by_contest.csv`).

## Reconciliation — three independent layers

1. **Precinct sums vs the county's own COUNTY TOTALS rollup rows** (present in every
   SOVC CSV and the 2018 workbooks' `County - Total` rows):
   **exact = 1,266 candidate-cells, under = 549, OVER = 0.**
   Every "under" is the suppressed remainder — the rollup includes the `-`-suppressed
   cells, the precinct sum cannot. Zero overs = no double-counting anywhere.
   The by-contest layer therefore uses the official rollup (`official_total=true`)
   wherever it exists, so suppression never undercounts the derived totals.
2. **Per-candidate totals vs the county's countywide summary PDFs** (independent
   documents, full coverage — not samples):
   - 2018 general 130/130 exact; 2018 primary 26/26.
   - 2019 primary 90/90; 2019 general 114/115 (see OCR section for the 1).
   - 2020 general 143/143; regular primary 26/26; presidential primary 23/23.
   - 2021 general 84/84 (non-RCV contests).
   - 2021 primary: the only summary the county published is in-body
     **"UNOFFICIAL RESULTS"** (generated 8/16/2021, pre-canvass). 73 of 76 candidates run
     LOW vs the certified SOVC, 3 exact, none high — the expected direction, so the SOVC
     is confirmed as the later, official record.
   - 2023 primary 57/57; 2024 general 121/121; 2025 general 168/168; 2025 primary 179/179.
   - "Missing" buckets in the build printout are the summaries' certified write-in
     itemizations (`Write-In: <name>`, `Write-In Totals`, `Not Assigned`) which have no
     SOVC counterpart — the SOVC is the canonical layer; the summaries stay in raw/.
3. **Winner agreement with the audited per-city layer** (lehi / provo / orem / vineyard
   `election_results/<slug>_races.csv`, strict same-office-same-district join):
   **52/52 rank-1-or-RCV-final winners agree.** (Read-only cross-check; the city files
   were not touched.)

Also: per-page block self-checks on the precinct-summary PDFs (sum of parsed candidate
lines vs the printed `Total Votes Cast` / `Contest Totals`): 2023 primary and 2026
primary pass **100%** of blocks; 2019 OCR flags exactly 2 blocks, both explained below.

## The 2019 general — OCR method and its residuals

The county's only precinct-grain 2019 general source is a 22.5 MB **scan** (256 of the
report's 261 pages; report pages 17/34/137/213/214 are absent from the published PDF,
and 4 born-digital replacement pages sit where scan pages were damaged — the absent
pages are each the continuation side of a replaced page, and every affected city
reconciles exactly, so no votes are lost to them). Method: pdftoppm 300 dpi →
tesseract psm 4 → the same block parser as the born-digital precinct PDFs, plus:

- systematic character repairs verified against the certified summary
  (`$`→`S`, `S$`→`S`, `!`→`I` in names; 2-letter-prefix `O`→`0` repair in precinct
  codes; 3 page-order-derived precinct-label patches, e.g. `PROO`→`PR09`);
- **one visually-verified value patch** (`OCR_PATCHES_2019G`): tesseract dropped the
  `DAVID SHIPLEY 58` line on report page 189 (PR33) — re-rendered the raw PDF page and
  read it directly (SHIPLEY 58 / MOSS 47 / Total 105); the patched row carries
  `extraction=pdf_ocr+visual`.

Result: **114 of 115 candidates reconcile exactly** with the certified countywide
summary. The single residual — OREM COUNCIL / LAMBSON, precinct-sum 7,996 vs summary
7,995 — is a **source-internal inconsistency**, not an extraction error: on the
`OR47 & OR47S` page both the born-digital text layer and the OCR agree the printed
candidate values sum to 976 while the page's own printed `Total Votes Cast` says 975.
The long file keeps the printed per-precinct values verbatim; the by-contest layer uses
the certified summary totals for all of 2019 general (`official_total=true`).

## Suppression — preserved, never imputed

- `-` cells (2018–2025 SOVCs) → `votes=''`, `suppressed=True` in the long file;
  by-contest `suppressed=true` only where no official rollup covers the contest.
- 2024 regular primary suppresses by **merging small precincts** (`AF301 & FED301`) —
  merged labels kept verbatim; 2019 general has 4 merged precinct pages likewise.
- 2026 primary withholds **19 whole precincts** (printed as `<precinct> Suppressed`) —
  no rows exist for them; the ledger is printed at build time and recorded here:
  25CH08, 25LE08, 25LE44, 25NE09, 25NW05, 25NW10, 25NW11, 25NW12, 25NW13, 25NW18,
  25NW24, 25OR54, 25PR01, 25SE04, 25SE06, 25SE15, 25SL02, 25SW01, 25SW08.
- **Quarantined file:** `raw/2023_General_SOVC_6c3a0e6491.csv` was linked by the county
  as "2023 General SOVC" but is in-body the **2022 general SOVC with all 7,884
  suppressed cells unredacted** (a county publication error; the only differences from
  the official 22_G file are the filled dashes + precinct-code zero-padding). It is
  retained verbatim for the acquisition record and **never parsed** — the canvass keeps
  the official suppressed file's dashes.

## RCV — the discipline

SOVC first-choice order is **never** presented as an RCV result: RCV rows carry
`rcv=true` + `rcv_final_winner` (from `rcv/rcv_contests.csv`); rank-position contests
beyond "1st Choice" never enter the by-contest layer.

- **2021 general (6 RCV cities, 13 contests):** the SOVC prints rank-POSITION columns
  ("Lehi City Council 1st..9th Choice") — frequency of each rank per candidate, not
  rounds. First-choice contests enter by-contest; finals come from the 15 recoverable
  county-linked rcvis.com tabulations (slugs from the county's own 2021RankedResults.asp,
  Wayback 2021-11-23, archived at `rcv/2021RankedResults_wayback_20211123.html`) plus
  the county's certified 2021 summary PDF, which prints final-round blocks for Elk Ridge
  Council, Genola Mayor and Lehi Mayor. **Ceiling:** 4 of the 19 county-linked rcvis
  pages are dead (404, no Wayback capture): Elk Ridge Council seats 1–2, Genola Mayor,
  Lehi Mayor — all four have county-PDF finals and/or trivial fields (Elk Ridge Council
  was 2 candidates for 2 seats), so every 2021 winner is sourced; the missing artifacts
  are those four round-by-round tables only.
- **2023 general (5 RCV cities) + 2023 Lehi RCV primary:** entirely ABSENT from the
  county SOVC/summary. First-choice tallies + finals recovered from rcvis (the primary
  slug is county-page-linked, Wayback 2024-05-30 archived at
  `rcv/results2023_wayback_20240530.html`). Two upload generations exist (preliminary
  + higher-count certified re-uploads); **winners identical in both**; the registry pins
  the certified seat-1 tabulations and documents which seats have only the
  preliminary-era tables. Multi-seat races were run as sequential single-seat
  tabulations — seat order proven by the candidate-count ladder.
- **2025:** no RCV anywhere (plain plurality contests; Utah's pilot ended).
- Vineyard 2021 note: qualified write-in KRISTAL C. PRICE is named in the rcvis
  tabulation but appears only as `WRITE-IN:` in the SOVC rank columns.

Round-by-round tables: `rcv/rounds/*.json` (verbatim rcvis rawDataId blobs; provenance
`rcv/rounds_sources.csv`) + flattened `rcv/rounds/*.csv`.

## Honest gaps (not recoverable from the county's publications)

- **No precinct grain exists** for: 2016 general/primary, 2017 general/primary,
  2022 regular primary, 2023 municipal general (countywide contest grain only).
- **2019 general:** report pages 17/34/137/213/214 absent from the published scan
  (no votes lost — see above); precinct grain for the 5 RCV-era… n/a (2019 pre-RCV).
- **2021 municipal primary:** the county never published an official summary — only the
  unofficial 8/16 interim report; the SOVC CSV is the official record.
- **2016:** the county's summary lists only County Commission Seat C among county
  offices (unopposed offices not printed); the 1-page Fairfield special bond PDF is a
  textless scan (cataloged, outside council/mayor/county-office scope).
- **2025 Public CVR** (ballot-level) retained but not loaded (future loader, as SLCo).
- **2026 general** not yet held; 2026 primary is loaded.
- 2023 primary PDF carries the "suppressed" filename but shows no visible suppression
  markers (no dashes, no merged labels) — any suppression was applied upstream by
  omission; nothing to preserve beyond what is printed.

## The Draper county-straddle finding

`raw/Draper_Reporting_2025_8_26_795def9e21.pdf` is a **Salt Lake County**-generated
UNOFFICIAL report (header "Salt Lake County, Utah", 8/25/2025) covering SLCo's three
Draper precincts (25DR01–03) voting in **Aspen Peaks School Board 4** — the school
district extends into SLCo Draper while Utah County administers the contest;
Utah County posted SLCo's component for canvass completeness. It is NOT a Draper
municipal race and is not loaded (unofficial + other-county grain + school-board scope,
which the by-contest layer excludes by the district-body guard). Consistent with
`registry/relationships.csv`: no Utah-County-run Draper or Bluffdale municipal contest
exists in any year (verified against every contest list 2016–2026).

## Loader conformance

`scripts/build_cities_db.py::load_election_result()` (read-only inspection) reads
`<county>/elections/election_results_by_contest.csv` by column name — the 14 columns it
uses are emitted with SLCo-identical names/types; the extra columns (`rcv`,
`rcv_final_winner`, `official_total`) are ignored by the loader. No loader change
needed. `utah_county` is already registered (fed_index 102), so the next
`build_cities_db.py` run (NOT run by this build, per containment) will pick the file up.
