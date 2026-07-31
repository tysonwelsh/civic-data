# Magna `ordinances/` — availability & coverage (as-of 2026-07-13)

Adopted ordinance + resolution instruments for **Magna** (metro township 2017-2024 →
city 2024, Salt Lake County). Built by `/expand-city-sources` source type 3. Additive:
does **not** modify any existing dataset; it cross-references
`meeting_minutes/all_votes.csv`.

## What exists — YIELDED

- **239 indexed instruments** (`index.csv`): **86 ordinances + 153 resolutions**,
  spanning **2017-01-01 → 2026-06-23** (adoption dates).
- **Source:** the **MunicipalCodeOnline public S3 bucket** — Magna's codified-code
  vendor. All raws no-auth GET from
  `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/magna/{ordinances,resolutions,plan,fees}/documents/`.
  The city's own CivicPlus site (`magna.utah.gov`) was **not** needed.
- **241 raw files retained** (`raw/`, 403 MB) + `raw/_fetch_log.jsonl` (sha256
  provenance). **241 text sidecars** (`text/`): **89 born-digital** (`pdftotext -layout`,
  incl. 1 `.docx` via `textutil`) + **150 OCR** (`tesseract`, 300-dpi render; most
  2017-2022 instruments are signed image scans). 0 files yielded no text.
- **Motion linkage** to `meeting_minutes/all_votes.csv`: **131 high** (instrument number
  cited in a recorded council/CRA motion — all 131 independently verified: the canonical
  number literally appears in the matched motion), **10 medium** (same-year subject
  match), **98 none** (unmatched — see below).
- **Land-use subset: 55** (49 ordinances + 6 resolutions) — rezones, Title 18
  (subdivision) / Title 19 (zoning) code books + amendments, planned-community zones,
  the 2021 General-Plan adoption, the 2025 Water Element, WUI code, landscaping/parking
  code. 20 are high-linked to a council vote.

## Number families & the form-of-government drift (handled)

Magna's instrument numbering **drifts across the HB35 seam** — `magna_ord_index.py`
`canon()` normalizes all of it:

| Family | Form | Era | Count |
|---|---|---|---|
| township month-seq | `YY-MM-NN` / `YYYY-MM-NN` (middle IS the month) | 2017 → 2024 | 151 |
| city ordinance O-series | `YYYY-O-NN` (also `22-O-01`; OCR `0`↔`O` drift) | 2022 → 2026 | 42 |
| city resolution R-series | `RYYYY-NN` (+ `A` re-issue suffixes) | 2025 → 2026 | 38 |
| adopted code books | `TITLE-18` / `TITLE-19` (versioned) | — | 7 |
| un-numbered | (blank) | — | 1 |

⚠ **Ordinances and resolutions were numbered in PARALLEL month-seq sequences** in the
township era — e.g. both `Ordinance 20-06-02` and `Resolution 20-06-02` exist and canon
to the same `2020-06-02`. They are **distinct instruments** kept as separate rows; motion
linkage is filtered by the ordinance/resolution word cited in the motion so an ordinance
never inherits a resolution's motion (and vice-versa). Ordinances went O-series in 2022
while resolutions kept month-seq through 2024, then switched to the R-series in 2025.

## What was NOT indexed (raws retained where fetched)

- **8 non-instrument files skipped at the manifest stage** (in `plan/`+`fees/`+the
  housing packet — NOT downloaded): the 2021 Magna General Plan + its Appendix, the Active
  Transportation Plan, four Consolidated Fee Schedules (2021/2022/2023/2025), and the
  "2019 Moderate Income Housing Submitted Packet." The General Plan + Water Element belong
  to `housing_plans/`; fee schedules aren't legislative instruments.
- **2 files fetched + retained but EXCLUDED from the index** (`is_excluded()`):
  - `Magna_R2026-13_SLCo_MultiJurisdictional_Hazard_Mitigation_Plan_UPDATED_2025.pdf` — the
    Salt Lake **County** hazard-plan volume bundled with the adopting resolution. The
    **adopting resolution `R2026-13` itself IS indexed.**
  - `05-10-22_Magna_Bird_Rides_Agreement-Final.pdf` — a scooter-contract exhibit (its
    `05-10-22` filename is a date, not an instrument number).
- **12 byte-identical re-uploads** (same S3 ETag under different unix-ts prefixes) were
  collapsed before fetch. Distinct-byte variants that share a number (signed vs unsigned
  scans, `A` re-issues, versioned Title code books, the Council-vs-CRA `R2026-01` pair)
  are **kept as separate rows** — honest distinct instruments, raws retained.

## Cross-entity (shared-MSD) screening — CLEAN

Magna, Kearns, White City, Copperton, and Emigration Canyon share **MSD** land-use staff,
and each city's MunicipalCodeOnline bucket can hold neighbors' mis-filed docs. **None found
here:** every filename is Magna-numbered, and sampled authoring captions read "…OF THE
MAGNA METRO TOWNSHIP COUNCIL" / "…OF THE MAGNA CITY COUNCIL." Instruments that *mention*
the MSD (they're MSD-serviced) are Magna-authored, not decoys.

## The `none` (98) — honest unmatched, not gaps

Most are routine resolutions (appointments, budgets, interlocal agreements, meeting
schedules) whose motions don't cite a number, plus township ordinances/resolutions
adopted before the on-disk recorded-minutes floor (**council votes begin 2018-07-17**;
2017 + Jan–Jun 2018 minutes are 404-unrecoverable on PMN — see the core
`minutes_unrecovered.csv`). For unmatched rows `adoption_date` prefers the document's own
header date, else the **instrument number's encoded `YYYY-MM` with a placeholder day
`-01`** (flagged in `linkage_note`; truer than the S3 upload date), else the upload date
(20 rows, all flagged).

## Corpus screen

`screen_corpus.py text` → 0 read errors; a handful of OCR outliers (1 dict_ratio,
4 split-word, 1 weird-char) on sparse/number-heavy signed scans (budget, appointment,
2017 township ordinances). Inspected: cosmetic OCR noise in number/date regions, faithful
body text — **not corruption**. OCR is preserved verbatim (source typos kept).

## Regenerate

```
# 1. re-fetch the four S3 XML listings into the session scratchpad as magna_s3_<pref>.xml:
#    curl 'https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/?list-type=2&prefix=magna/<pref>/'
python3 magna_ord_parse_s3.py            # -> magna_ord_manifest.csv + magna_ord_batch.csv
python3 <skill>/scripts/polite_fetch.py --batch magna_ord_batch.csv --out raw
python3 magna_ord_extract.py             # -> text/ sidecars + text/_extraction_log.csv
python3 magna_ord_index.py               # -> index.csv (§9 contract)
```
