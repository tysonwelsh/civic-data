# White City — adopted ordinances & resolutions: availability

**As-of:** 2026-07-13 · **Source type 3 (zoning/land-use ordinances)** of `/expand-city-sources`.

## What exists and where

White City's adopted **ordinances and resolutions are codified on MunicipalCodeOnline**
(the vendor host for the city's new municipal code), served from a public AWS S3 bucket:

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/whitecity/
    ordinances/documents/     31 objects
    resolutions/documents/   114 objects
    ADC/ fees/ plan/ site/   (code content, fee schedule, general plan — not harvested here)
```

Every object is a born-image or born-digital PDF of an adopted instrument. All **142**
in-scope objects were fetched verbatim into `raw/` (GET-only, ≥1 s/host throttle;
`raw/_fetch_log.jsonl` carries url/status/bytes/sha256). Enumeration is reproducible via
`wc_ord_enumerate.py` → `_s3_manifest.csv`.

## Coverage delivered

- **136 distinct adopted instruments** indexed — **28 ordinances + 108 resolutions**,
  adoption window **2017-01-05 → 2025-12-04**.
- **Format:** 99 scanned (image-only PDFs, OCR'd with tesseract) + 37 born-digital
  (`pdftotext -layout`). The MunicipalCodeOnline copies are **mostly scanned images**,
  even for recent years — text sidecars are labeled `ocr_tesseract` vs `pdftotext_layout`
  per row and in `text/_extraction_log.csv`.
- **Text sidecars** for all 142 raws in `text/` (feed `cities.db` `fts_ordinance`).
- **Motion linkage** to `meeting_minutes/all_votes.csv`: **95 high** (instrument number
  cited in a recorded council motion), **7 medium** (year + subject agreement; covers the
  `YYYY-O-NN` vs `YYYY-MM-NN` number drift, e.g. S3 `2025-O-02` = motion-cited
  `2025-02-02`, Title 8 Animals), **34 none** (procedural/appointment instruments and
  early-2017 organizational ordinances whose numbers are not cited by number in a motion).
- **Land-use / zoning subset:** 13 instruments flagged `land_use=yes` — incl. the
  **Title 18 Subdivision** + **Title 19 Zoning** ordinances, the 2023 **Ordinance 2023-O-01**
  wholesale Titles 18 & 19 rewrite, the 2017 land-use-plan adoption, **Ordinance 2025-O-04**
  (19.46.100 infrastructure), and the **2025-O-06 WUI** (wildland-urban-interface) ordinance.

## Honest gaps

1. **~68 instrument numbers cited in council minutes have NO posted PDF on the code host.**
   A per-number set-difference (minutes citations vs the S3 archive) finds them concentrated
   in:
   - **2026 (18 instruments):** the entire 2026 city-era resolution run (`2026-01-01` …
     `2026-05-01`) is cited in minutes but **not yet posted to MunicipalCodeOnline** — the
     code host **lags** the city's ~8-month post-HB35 municipal-code rewrite (2024–2026).
     This is the newest-record thinness the task anticipated. Re-harvest later to backfill.
   - **Scattered procedural resolutions 2018–2022 (~21):** payment-authorization and
     appointment resolutions (e.g. `2018-04-01/02/03`, `2020-10-01/02/03`, `2022-01-01/02/03`,
     `2022-04-01/02/03`) the clerk never uploaded to the code host.
   - **`2025-O-05`** is correctly absent: the council **voted to DENY** it (a Title 19 text
     amendment, 2025-07-10) — it was never adopted, so no adopted-instrument PDF exists.
   These are adopted-instrument texts we do not have; they are recorded here as a gap, never
   fabricated. (A handful of apparent misses — `2024-O-05/06`, `2025-O-01` — are only
   `O`-vs-`0` transcription variants and ARE indexed.)
2. **5 byte-identical re-uploads** on S3 collapse to one index row each; both raws are
   retained on disk and the alternate filename is named in the `dup_raw` column.
3. **1 cross-entity decoy retained-but-excluded:** `raw/1647891849_Ordinance_2021-10-01.pdf`
   is authored **"AN ORDINANCE OF THE COPPERTON METRO TOWNSHIP COUNCIL"** (an ADU/HB82
   ordinance) mis-filed into White City's bucket (the two townships share the Greater SL MSD
   admin). The raw is kept for provenance; it is **not** an index row. (Other docs merely
   *mention* Copperton in interlocal/boundary context and are legitimate White City rows.)
4. **OCR quality:** the oldest/poorest scans (esp. `Ordinance 17-02-01`, the 8 MB
   `2025-O-02` Title 8 Animals scan) carry expected OCR noise — source typos and layout
   artifacts are **preserved, not cleaned** (`screen_corpus.py` flags are advisory).

## Not harvested here (other datasets / out of scope)

- The **General Plan** and the two **Moderate-Income-Housing** PDFs that also sit in the
  `resolutions/` bucket belong to the `housing_plans/` dataset — left for that source type.
- The MunicipalCodeOnline `ADC/`, `fees/`, `plan/`, `site/` prefixes (current consolidated
  code, fee schedule) are not adopted-instrument PDFs and are not indexed here.
