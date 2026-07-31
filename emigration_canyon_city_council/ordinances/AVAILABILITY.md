# Emigration Canyon — adopted ordinances & resolutions: availability

**As-of:** 2026-07-14 · **Source type 3 (zoning/land-use ordinances)** of `/expand-city-sources`.

## What exists and where

Emigration Canyon's adopted **ordinances and resolutions are codified on
MunicipalCodeOnline** (its codified-code vendor), served from a public AWS S3 bucket.
**The working slug is `emigrationcanyon`** (the bare `emigration` slug is empty — both were
probed):

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/emigrationcanyon/
    ordinances/documents/    51 objects
    resolutions/documents/   49 objects
    orddoc/documents/        22 objects  (city-era 2025-O/2026-O signed PDFs + Ordinance Log.xlsx)
    policies/documents/       2 objects
    plan/ (4)  fees/ (11)  ADC/ site/    (general plan, fee schedule, consolidated code — other datasets)
```

All **124** in-scope objects were fetched verbatim into `raw/` (GET-only, ≥1 s/host
throttle; `raw/_fetch_log.jsonl` carries url/status/bytes/sha256 — all HTTP 200).
Enumeration is reproducible via `ec_ord_enumerate.py` → `_s3_manifest.csv`. Raw footprint
**155.9 MB**.

## Coverage delivered

- **98 distinct adopted instruments** indexed — **49 ordinances + 49 resolutions**,
  adoption window **2017-04 → 2026-05**.
- **Format:** **45 born-digital** (`pdftotext -layout`) + **53 scanned** (image-only PDFs,
  OCR'd with tesseract). Text sidecars for all 122 PDFs in `text/` (feed `cities.db`
  `fts_ordinance`); the 2 non-PDF raws (`Ordinance 20-11-01.docx`, `Ordinance Log.xlsx`)
  are retained but not sidecar'd.
- **Motion linkage** to `meeting_minutes/all_votes.csv`: **54 high** (instrument number
  cited in a recorded council motion), **2 medium** (year + subject agreement —
  `2025-O-02` engineering standards, `R2026-04` MSD-board alternate), **42 none** (mostly
  instruments pre-dating the recovered-minutes floor of **2018-10**, plus procedural
  resolutions referenced without a number). This is an INDEPENDENT cross-match, not a
  within-source derivation.
- **Adoption dates** for unmatched ordinances use the clerk's **`Ordinance Log.xlsx`
  "Date Signed"** (authoritative day-precision, ~22 rows incl. city-era `2025-O-01/08/12/13/14`);
  otherwise the number's encoded year-month, else the flagged S3 upload date.
- **Land-use / zoning subset:** **24** instruments flagged `land_use=yes` (advisory/coarse)
  — incl. the township **subdivision/zoning-code amendments** (`18-06-01/02/03`), the
  **iADU ordinance** `2021-09-01`, **floodplain** `2021-09-02`, the **WUI** ordinances
  (`2022-03-02`, `2025-O-13`), the **Night Lighting** ordinance `2023-06-01`, the city-era
  **Title 19 rewrite** (`2025-O-05/06/07`), and the **4180 Emigration Canyon Rd zoning-map
  change** `2025-O-09`.

## Honest gaps

1. **~15 instrument numbers cited in council minutes have NO posted PDF on the code host.**
   A per-number set-difference (minutes citations vs the S3 archive) finds them concentrated
   in tax-rate / budget / canvass / meeting-schedule resolutions the clerk never uploaded,
   plus the code-rewrite lag:
   - **Ordinances:** `2022-03-01` (the **General Plan adoption** ordinance — the plan itself
     lives under the host's `plan/` prefix, a `housing_plans/` concern), `2024-11-01`
     (2025 meeting-schedule ord — the log notes it was DocuSigned "will upload when
     received"), `2026-O-01` (2026 city-era, host lags).
   - **Resolutions:** `19-12-04`, `20-11-01`, `20-12-01`, `21-08-01`, `2023-04-01`,
     `2023-12-02`, `2023-12-03`, `2024-04-01`, `2024-11-01`, `R2025-07`, `R2025-12`,
     `R2025-13`.
   These are adopted-instrument texts we do not have; recorded here as a gap, never
   fabricated. Re-harvest later to backfill the 2025–2026 city-era lag.
   - *(Three apparent "misses" — `2025-0`, `2025-042`, `20254-11` — are OCR/typo citation
     variants in the minutes of instruments that ARE indexed under their correct numbers
     `2025-O-17`, `2025-O-04`, `2024-11-xx`; not real gaps.)*
2. **Cross-prefix / byte / format duplicates** collapse to one index row each (city-era
   `2025-O-NN` posted in both `ordinances/` and `orddoc/`; the `20-11-01` PDF+DOCX pair).
   Both raws are retained on disk; alternates are named in the `dup_raw` column.
3. **4 files retained but EXCLUDED from the index** (not adopted-instrument texts):
   `Ordinance Log.xlsx` (clerk catalog), the **Dominion Energy franchise agreement**
   (exhibit to Ord `19-05-02`), and the two **SLCo Hazard Mitigation Plan** volumes
   (`…Emigration Canyon Annex…`, `…MJHMP Volume1…` — exhibits to Res `R2026-02`).
4. **No cross-entity decoys.** The shared-MSD hazard (a Copperton ordinance was once found
   mis-filed in White City's bucket) did **not** recur — every instrument's authoring
   caption is an Emigration Canyon Metro Township / City instrument.
5. **OCR quality:** the scanned older instruments carry expected OCR noise; `screen_corpus.py`
   flagged only benign OCR/layout artifacts (0 dict-ratio outliers, 0 read errors). Source
   typos and layout artifacts are **preserved, not cleaned**.

## Not harvested here (other datasets / out of scope)

- The **General Plan** (`plan/` prefix) and the **fee schedules** (`fees/` prefix) on
  MunicipalCodeOnline are not adopted-ordinance texts — the general plan belongs to a
  `housing_plans/` dataset.
- The consolidated `ADC/` / `site/` code content is current-code, not adopted instruments.
