# utah_county / elections — the canonical Utah County canvass

**This is the county-level canonical source for Utah County elections, 2016–2026** —
the layer the held Utah County cities (lehi, provo, orem, vineyard) derive from. Built
2026-07-20 on the salt_lake_county/elections model. Source: **Utah County Clerk**
elections app <https://vote.utahcounty.gov/results/{year}> (files on its
`/cms/uploads/` CMS) + county-linked rcvis.com RCV tabulations. Everything acquired is
mirrored verbatim in `raw/` with byte-verified provenance in `sources.csv` (zero
unrecorded URLs).

## Files

- `utah_county_results_long.csv` — **canonical** tidy long, 198,459 rows: one row per
  precinct (or countywide where the county published no precinct grain) × contest ×
  candidate, every election 2016–2026 (municipal odd years AND even-year
  federal/state/county — the county's SOVCs carry them all). Column-compatible superset
  of the SLCo long (the 13 SLCo columns first, then `party`, `grain`
  (precinct|countywide), `extraction` (csv|xlsx|pdf_text|pdf_ocr|pdf_ocr+visual)).
  Verbatim layer — candidate names as printed (incl. "(WITHDREW)"/"(DISQUALIFIED)"),
  merged-precinct labels ("AF13 & AF14") kept, suppressed `-` cells emitted as
  `votes=''` + `suppressed=True`, never imputed. `COUNTY TOTALS` rollup rows are NOT
  precinct rows — they are captured as official totals and reconciled at build time.
- `election_results_by_contest.csv` — **derived** (`build_elections.py`), 1,044 rows /
  288 contests. Exactly the 14 columns the `gov.db` loader
  (`load_election_result()`) reads, in SLCo semantics, plus 3 ignored extras:
  `rcv`, `rcv_final_winner`, `official_total`. Scope: municipal **Council/Mayor**
  contests for EVERY Utah County municipality (`jurisdiction_slug` set for held cities
  lehi/provo/orem/vineyard; `''` for other municipalities) + **Utah County county
  offices** (`jurisdiction_slug='utah_county'`: County Commission Seats A–C, Clerk,
  Auditor, Clerk/Auditor, Attorney, Sheriff, Assessor, Recorder, Surveyor, Treasurer).
  `votes` = the county's official rollup total where one exists (`official_total=true`
  — includes suppressed cells), else the precinct sum. `rank_in_contest` is
  **plurality order — for `rcv=true` rows the RCV winner is `rcv_final_winner`, never
  the rank-1 candidate by first choices** (they differ, e.g. Payson 2023).
- `rcv/rcv_contests.csv` — the RCV registry: every RCV contest 2021–2023 (Utah County
  ran no RCV in 2019 or 2025), how the SOVC represents it (`rank_position_columns` |
  `absent`), the county-linked rcvis slugs, seat-ordered final winners, source +
  confidence. `rcv/rounds/*.json` = verbatim rcvis rawDataId blobs (provenance
  `rcv/rounds_sources.csv`), flattened to `rounds/*.csv`. Wayback captures of the
  county pages that linked the slugs are archived alongside.
- `build_elections.py` — regenerates long + by-contest + rounds CSVs from `raw/` (+
  `raw/text/` extractions). Idempotent; prints the full reconciliation every run.
- `sources.csv` — every acquired file: year, doc type, grain, used/parsed status, URL,
  bytes, sha256, notes (incl. the quarantined mislabeled upload).
- `VERIFICATION.md` — totals reconciliation (three independent layers), the OCR
  method + residuals, suppression + RCV ceilings, honest gaps, the Draper-straddle
  finding.

## Quirks to know before querying

- **Election-type vocabulary:** `municipal general`/`municipal primary` (odd years),
  `general`/`regular primary`/`presidential primary` (even years).
- **2021 general RCV:** the SOVC stores rank-POSITION contests ("Lehi City Council
  1st..9th Choice") — only "1st Choice" enters by-contest (first-choice tallies);
  ranks ≥2 live in the long file only.
- **2023 general:** the county's official summary EXCLUDES the 5 RCV cities entirely;
  their by-contest rows are rcvis-sourced (`source_file=rcvis.com/v/...`,
  `n_precincts=0`). No precinct grain exists for 2023 general at all (summary is
  contest-grain).
- **2019 general** precinct grain is OCR from the county's scan — reconciled 114/115
  per-candidate against the certified summary; by-contest uses the certified totals.
- **Suppression:** `-` cells stay suppressed; 2024 primary merges small precincts;
  2026 primary withholds 19 whole precincts ("Suppressed" pages); the mislabeled
  "2023 General SOVC" upload is actually the UNSUPPRESSED 2022 general — quarantined,
  never parsed.
- **Draper/Bluffdale:** despite the county-straddle relationships, Utah County runs no
  Draper or Bluffdale municipal contest in any year (verified 2016–2026); the
  `Draper_Reporting_2025` raw is an SLCo-generated Aspen Peaks School Board report
  (see VERIFICATION.md).
- **Pseudo-candidates:** `OVER VOTES`/`UNDER VOTES`/`Overvotes`/`Undervotes` rows are
  kept verbatim in the long file but excluded from by-contest ranking (exact-match
  guard — the SLCo METHOD_LABELS discipline).
- Precinct codes changed era: bare (`AF01`, to 2020) → 3-digit (`AF301`, 2022–24) →
  year-prefixed (`25AF01`, 2025+). Join precincts within an era only.

## How the cities relate

The audited per-city `election_results/<slug>_races.csv` files remain the
authoritative winner/margin layer (`election_race` in gov.db); this module is the
underlying county tally layer (`election_result`). Cross-checked 2026-07-20: 52/52
held-city winners agree (strict same-office-same-district). Re-pointing the four
cities' pipelines at this canonical is a separately-queued, byte-identity-gated
package — NOT done here.

## Refresh

New election: pull the new files from `vote.utahcounty.gov/results/<year>`, append to
`raw/` + `sources.csv` (byte-verified), extract text for PDFs into `raw/text/`
(`pdftotext -layout`), register in `PARSED_SOURCES`/`RECON_SUMMARIES`, harvest any new
RCV tabulations into `rcv/`, rerun `python3 build_elections.py`, and check the printed
reconciliation gates (COUNTY-TOTALS OVER must stay 0; summary recon diffs explained or
zero). Then rebuild gov.db centrally (outside this module).
