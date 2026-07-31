# Copperton `ordinances/` — availability & gaps (as-of 2026-07-14)

Adopted **ordinance + resolution** instrument texts for the Town of Copperton, harvested
from the **MunicipalCodeOnline public S3 bucket** (`municipalcodeonline.com-new/copperton/`).
Additive dataset built by `/expand-city-sources` (source type 3). It **never modifies** the
existing `meeting_minutes/` layer; it only cross-references it.

## What exists (yielded)

- **129 distinct adopted instruments** (67 ordinances + 62 resolutions), **2017-01-05 →
  2026-06-17**, every year 2017–2026 represented.
- **153 raw PDFs retained** (199 MB) — 129 distinct + **23 byte-identical S3 re-uploads**
  (collapsed to one index row each; the alternate raw stays on disk, named in `dup_raw`) +
  **1 excluded cross-entity decoy** (below).
- **Text sidecars for all 153** (`text/<stem>.txt`): 83 born-digital (`pdftotext -layout`),
  70 tesseract-OCR (the town-era "SIGNED" copies and the Title 18/19 code are scans). Corpus
  screener: healthy real-word ratio (median 0.77), no cid/PUA/mojibake — advisory OCR noise
  only (split words / replacement chars in ~9 scanned resolutions), consistent with faithful
  scans, not hallucination.
- **24 land-use instruments** flagged (`land_use=yes`): the Title 18 Subdivision + Title 19
  Zoning codes (+ the 2024 & 2025 amendments), the 2021 ADU/accessory-use ords (HB82 series
  2021-10-01/-03), the 2024-12-01 setback / home-occupation ord, the 2025-O-07 Wildland-Urban-
  Interface ord, engineering-standards, and impact/subdivision-fee ordinances.

### The code host recovers instrument texts across the 2017-2018 minutes gap
The core `meeting_minutes/` layer has an honest **404 gap (2017-02 → 2018-06, PMN attachment
purge)**. The code host is INDEPENDENT of PMN and **still holds those instruments** — 25 rows
carry 2017 adoption dates and 11 carry 2018. So the ordinance archive is a partial *content*
recovery for the minutes-gap era even though the meeting minutes themselves remain lost.

## Motion linkage (to `meeting_minutes/all_votes.csv`)

Every indexed row is backed by an independently published PDF, so matches are genuine
cross-matches — **`within_source` is NOT used** here. Distribution:

| confidence | rows | meaning |
|---|---|---|
| **high**   | 17 | instrument number cited in a recorded motion of the SAME instrument type |
| **medium** | 22 | subject-term overlap with a type-consistent motion (≤20 days of the doc's own header date, else same-year ±2mo) |
| **low**    | 10 | header adoption date lands on a meeting whose only ord/res-type approving motion is unnumbered (date-only) |
| **none**   | 80 | unmatched — most motions say only "to approve the ordinance/resolution" with no number |

Copperton motions rarely print the instrument number (many read "to approve the resolution"),
so a high `none` count is expected and honest, not a linkage miss. `medium`/`low` are advisory
(spot-check before quoting); only `high` is an exact number cross-match.

## Gaps / what is NOT here

1. **12 instrument numbers are cited in council motions but NOT posted on the code host**
   (codification lags — same pattern as White City's 2026 run):
   - **The entire 2025 town-era resolution series `R2025-01 … R2025-08`** (appointments, the
     GSLM plan adoption, the FY2026 tentative budget, the county election contract) — cited at
     the 2025-01→05 meetings, none posted. The host's resolution folder jumps from 2023 docs
     straight to `R2026-01`.
   - `2024-05-02`, `2024-05-05` (two town-conversion resolutions), `2023-11-03` (the 2024
     tax-rate resolution), and `2019-09-03` (the code-enforcement ordinance — a draft copy IS
     retained as `…CO067-001 - Code Enforcement Ordinance FINAL (9-13-2019).pdf`, but under its
     drafting code, not the `19-09-03` number, so it does not number-match).

   These are **honest gaps recorded here, never fabricated into rows.** Re-harvest later to
   backfill the 2025 R-series once the host catches up.
2. **Non-instrument exhibits deliberately not fetched** (they belong to the housing_plans /
   general-plan scope, not the ordinance record): the 2020 **General Plan** draft + adopted
   PDFs, the **Annexation Policy Plan**, and two bare **Fee Schedule** attachment PDFs (the
   *adopting* fee ordinances/resolutions ARE indexed). Listed with `in_scope=no` in
   `_s3_manifest.csv`.
3. **Cross-entity decoy excluded (shared-MSD hazard, REAL for Copperton):**
   `raw/1597946761_Ordinance_20-08-01.pdf` is captioned **"AN ORDINANCE OF THE KEARNS METRO
   TOWNSHIP COUNCIL"** (conditional-use / Title 19 of the *Kearns* code) — a Kearns land-use
   ordinance mis-filed in Copperton's bucket, sharing the `20-08-01` number with Copperton's
   own fee-schedule ordinance (hence the slip). Raw retained, **excluded** from `index.csv`
   (`cop_ord_index.py EXCLUDE_FILES`). A full-caption sweep of all 153 sidecars found this as
   the **only** mis-file. (Reverse direction: a Copperton ADU ordinance was found mis-filed in
   *White City's* bucket and excluded there — cross-filing goes both ways among the MSD-staffed
   metro-township entities.)

## Source

`https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/copperton/` — public,
no-auth, GET-only S3 listing. Copperton spreads instruments across **seven** subprefixes
(not the two that White City/Kearns use): `ordinances/`, `resolutions/`, `orddoc/`, `fees/`,
`landordinances/`, `policies/`, `plan/` — all swept. See `CLAUDE.md` for the build pipeline.
