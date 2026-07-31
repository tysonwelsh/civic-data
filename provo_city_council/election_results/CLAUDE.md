# Provo Municipal Election Results

Utah County administers Provo's elections. This folder holds the county source files
(in `raw/`, never edited) filtered to **Provo Mayor + Provo Municipal Council races only**
and normalized for analysis. Covers the four odd-year cycles **2019, 2021, 2023, 2025**.

Provo Municipal Council = **5 districts + 2 citywide (at-large) seats**, 4-yr staggered terms:
- **Cycle A (2021, 2025):** Mayor, Citywide I, District 2, District 5
- **Cycle B (2019, 2023):** Citywide II, District 1, District 3, District 4 (no mayor)

## Pipeline

```
raw/*.csv  raw/*.pdf            Utah County SOURCE OF TRUTH (all cities/county)
clean_elections.py             filter to Provo council+mayor, unpivot crosstab, aggregate
  -> provo_results_by_precinct.csv  precinct x candidate (CSV cycles only: 2021, 2025)
  -> provo_results_by_candidate.csv race x candidate: votes, pct, rank, is_winner
  -> provo_races.csv                ONE ROW PER RACE: winner, runner-up, margin, turnout
```

Regenerate: `python3 clean_elections.py`. **Totals: 26 races, 69 candidate rows, 1,455 precinct rows.**

## Sources used (see `recon.md` §4; filenames re-scraped from `vote.utahcounty.gov/results/<year>`)

| Cycle | General (precinct?) | Primary | In `raw/` |
|---|---|---|---|
| 2019 | **PDF only** (citywide) | **PDF only** (citywide) | `2019_General_Results_PDF_*.pdf`, `2019_Primary_Results_PDF_*.pdf`, `19_G_Countywide_Precinct_Official_Suppressed_*.pdf` (22 MB precinct PDF — not parsed), `19_P_..._SOVC_*.CSV` |
| 2021 | **SOVC CSV** (precinct) | **SOVC CSV** (precinct) | `21_G_Countywide_SOVC_suppressed_*.csv`, `21_PP_..._SUPPRESSED_*.csv`, `2021_*_PDF_*.pdf` |
| 2023 | **PDF only** (citywide) | **PDF only** (citywide) | `2023_General_voting_results_*.pdf`, `2023_Primary_voting_results_*.pdf`, `23_P_SOV_Cs_suppressed_*.pdf` |
| 2025 | **SOVC CSV** (precinct) | **SOVC CSV** (precinct) | `SOVC_Simple_Redacted_*.csv`, `2025_Primary_SOVC_suppressed_*.csv`, `OFFICIAL_Countywide_Results_11_17_*.pdf` |

> Filename hashes are unguessable: always re-scrape the `/results/<year>` index and regex
> `/cms/uploads/[^"']+` (each link appears twice; strip the trailing `\` artifact).

Live source URLs (all 14 raw files re-verified 2026-07-19 — each returned HTTP 200 and was
confirmed **byte-identical (md5)** to the stored `raw/` copy, except `23_P_...` which is
content-verified as the 2023 Primary SOVC PDF; Utah County's `/cms/uploads/` CDN is stable):
- `https://vote.utahcounty.gov/cms/uploads/19_G_Countywide_Precinct_Official_Suppressed_c07b072cdf.pdf`
- `https://vote.utahcounty.gov/cms/uploads/19_P_19_Primary_SOVC_suppressed_93de48c7ac.CSV`
- `https://vote.utahcounty.gov/cms/uploads/2019_General_Results_PDF_a69d246ddc.pdf`
- `https://vote.utahcounty.gov/cms/uploads/2019_Primary_Results_PDF_dba3744ad0.pdf`
- `https://vote.utahcounty.gov/cms/uploads/2021_General_PDF_4d36475691.pdf`
- `https://vote.utahcounty.gov/cms/uploads/2021_Primary_PDF_e05a1d3833.pdf`
- `https://vote.utahcounty.gov/cms/uploads/2023_General_voting_results_be47c5636c.pdf`
- `https://vote.utahcounty.gov/cms/uploads/2023_Primary_voting_results_30a0ba993f.pdf`
- `https://vote.utahcounty.gov/cms/uploads/2025_Primary_SOVC_suppressed_4bc086dabf.csv`
- `https://vote.utahcounty.gov/cms/uploads/21_G_Countywide_SOVC_suppressed_1b85ad469d.csv`
- `https://vote.utahcounty.gov/cms/uploads/21_PP_2021_Primary_Statement_of_Votes_Cast_SUPPRESSED_bd47a35ddf.csv`
- `https://vote.utahcounty.gov/cms/uploads/23_P_SOV_Cs_suppressed_1907fb1cba.pdf`
- `https://vote.utahcounty.gov/cms/uploads/OFFICIAL_Countywide_Results_11_17_f09d22f26a.pdf`
- `https://vote.utahcounty.gov/cms/uploads/SOVC_Simple_Redacted_7a5eddcaf2.csv`

## The wide-crosstab unpivot (the tricky part)

Utah County SOVC CSVs are a **wide crosstab**: one row per precinct, and each *contest×candidate*
is its own column. A multi-row header spans those columns:
- **2-row header** (2021 general): row 0 = contest name (repeated across its candidate columns),
  row 1 = candidate name.
- **3-row header** (2021 primary, 2025 general+primary): row 0 = contest, row 1 = party (`NON`,
  non-partisan — ignored), row 2 = candidate.

`parse_sovc_csv()` reads the contest row + the **last** header row, keeps only columns whose
contest normalizes to a Provo Mayor/Council race, then sums each Provo precinct row (`PR##`,
or `25PR##` in 2025 — county-number prefix stripped) into both citywide totals and precinct rows.
- **Dropped pseudo-candidates:** `OVER VOTES`, `UNDER VOTES`, `VOTERS`, `BALLOTS CAST`, `Total`.
  **Kept:** `WRITE-IN` (real candidate; e.g. 2021 Citywide I had 703 write-ins).
- **Ballot measures excluded:** `Proposition #5 Provo` (RAP/PARC tax) is not a council/mayor race.
- Precinct rows filtered to `PR*` (Provo); look-alike cities (Orem, Lehi, Spanish Fork, Salem,
  Santaquin, etc.) excluded by the contest-name match `"provo" in contest`.

## 2023 PDF-only gap (and 2019)

- **2023 published NO general SOVC CSV — only a born-digital rollup PDF** (`2023_General_voting_results_*.pdf`).
  That PDF gives **citywide totals only**, so **2023 has NO precinct-level Provo data** in
  `provo_results_by_precinct.csv`. Same for the 2023 primary.
- **2019** likewise has no Provo SOVC CSV: the general/primary rollup PDFs are citywide. A 22 MB
  *precinct* PDF (`19_G_Countywide_Precinct_*.pdf`) exists but precinct crosstab extraction from it
  was out of scope (precinct detail required only for the 2021/2025 CSV cycles per the build spec).
  → **`provo_results_by_precinct.csv` contains 2021 + 2025 only.**
- The citywide totals for 2019 and 2023 (both primary + general) are hand-transcribed from those
  official PDFs into `PDF_CITYWIDE` in `clean_elections.py` (each value verified against the
  `pdftotext -layout` extraction).

## External cross-check (winners verified)

Cross-checked against Daily Herald (heraldextra.com), BYU Daily Universe, Salt Lake Tribune,
and provo.gov official results:
- **2025 Mayor:** **Marsha Judkins** defeated incumbent **Michelle Kaufusi** (≈8,703–8,280, ~422-vote
  margin) — confirmed upset, first west-side Provo mayor. Council winners **MacKay** (Citywide I),
  **Whitlock** (D2), **Whipple** (D5) — confirmed.
- **2023:** **Garrett** (Citywide II), **Christensen** (D1), **Bogdin** (D3), **Hoban** (D4, unopposed)
  — all confirmed and match the current provo.gov roster.
- **2021:** Kaufusi (Mayor, re-elected), MacKay (Citywide I), Handley (D2, unopposed), Whipple (D5).
- **2019:** Shipley (Citywide II), Fillmore (D1, unopposed), Ellsworth (D3), Hoban (D4).

> **Known 1-vote discrepancy:** the 2025 *suppressed/redacted* general SOVC CSV gives Kaufusi 8,280;
> some press/certified tallies show 8,281 (margin 423 vs 422). We keep the CSV value as the
> repo's source of truth; the difference is within the redaction/suppression of small precincts.

## Name-normalization notes (for joining elections ↔ votes ↔ comments)

Candidate names here are **UPPER-CASE** (`KATRICE MACKAY`, `TRAVIS HOBAN`); roster/votes data is
mixed-case (`Katrice MacKay`). Before joining on person+year+district, normalize: strip case,
any `(NP)`/`(NON)` suffix, and name-order/middle-initial variants (e.g. `MCKAY R. JENSEN`).
Note Provo has **two `JENSEN`s**: `MCKAY R. JENSEN` (2023 Citywide II runner-up) ≠ `STAN JENSEN`
(2023 D1 runner-up) — don't collapse them. `WRITE-IN` is an aggregate, not a person.

## Don't
- Don't edit `raw/`. Don't treat `Total`/`OVER VOTES`/`UNDER VOTES` as candidates.
- Don't match a neighboring Utah County city (Orem, Lehi, Spanish Fork, Salem, Santaquin) as Provo.
- Don't expect 2019/2023 precinct rows — those cycles are PDF-only (citywide).
