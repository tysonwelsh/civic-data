# Kearns `ordinances/` — availability & gaps (as of 2026-07-13)

Adopted ordinance + resolution texts for the **City / Metro Township of Kearns**, source
type 3 of `/expand-city-sources`. Additive only — nothing in `meeting_minutes/` was
modified. Machine-readable index: `index.csv`; build detail: `CLAUDE.md`.

## What exists and was harvested

**Code host = MunicipalCodeOnline** (public AWS S3 bucket, no auth). The city's own site
(`kearns.utah.gov`) is Cloudflare-blocked, but the adopted-instrument archive lives in a
scriptable S3 bucket:

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/kearns/
    ordinances/documents/    (127 keys)
    resolutions/documents/   (116 keys)
    plan/documents/          (8 keys — General Plan + its adopting ord/res)
    fees/documents/          (2 keys — consolidated fee schedules)
```

- **227 raw instrument files retained** (`raw/`, 270 MB, `_fetch_log.jsonl` sha256
  provenance) after de-duplicating byte-identical re-uploads by S3 ETag (253 keys → 233
  unique; the 6 non-instrument General-Plan / fee-schedule PDFs in `plan/`+`fees/` were
  left for the housing_plans layer). Each raw got a `text/<stem>.txt` sidecar
  (`pdftotext -layout` born-digital; `tesseract` OCR for scans; `textutil` for .docx).
- **223 indexed instruments**: **94 ordinances + 129 resolutions**, adoption window
  **2017-02 → 2026-06** (data floor 2017 = incorporation edge, not a gap). **56 are
  land-use** (zoning, Titles 18/19, subdivision, WUI, overlay, density, plats, general
  plan, conditional use).
- **Formats:** 119 born-digital `text` / 104 `scanned` (OCR). The MunicipalCodeOnline
  copies are mostly scans of signed originals — OCR is faithful (source typos preserved,
  e.g. "RATIFVING WORK PERFORMED"); it is not cleaned.

## Motion linkage (to `meeting_minutes/all_votes.csv`)

Independently-published PDFs, so every match is a genuine cross-match (**`within_source`
is intentionally NOT used** — that value is reserved for minutes-only derivations).

| confidence | rows | meaning |
|---|---|---|
| high | 74 | instrument number cited in a recorded council motion (exact number+meeting) |
| medium | 7 | same-year + subject-term overlap (number not exactly in a motion) |
| none | 142 | unmatched — routine appointments/budgets/franchise items whose motions don't cite the number, or whose meeting minutes are in the purged 2017-2018 gap |

The high "none" share is honest: a large block of 2017-2018 instruments predate the
recorded-minutes floor on disk (the pre-~July-2018 township minutes are the known PMN
blob-purge gap — see `meeting_minutes/minutes_unrecovered.csv`), so no motion exists to
match them against.

## Gaps (honest — not fabricated into rows)

1. **26 minute-cited instruments have no posted PDF on the host** — concentrated in the
   **2025-2026 city era** (the code is *not yet fully re-codified* post-cityhood, same
   pattern as White City): ordinances `2025-O-06/08/09/11/12/13`, `2026-O-02/04`;
   resolutions `R2025-02/03/04/06/07/11`, `R2026-11/12/13`; plus a few township items
   (`2021-06-03`, `2022-12-05`, `2023-01-03`, `2023-11-03`, `2024-01-01`, `2024-05-04/05`,
   `2024-10-02`). Re-harvest later to backfill. `2025-O-17` (Water Element GP update) IS on
   the host but under the `plan/` prefix as the General-Plan document — it belongs to the
   `housing_plans/` layer, not here.
2. **Adoption-date precision for unmatched scans.** 78 unmatched rows have no parseable
   header date and no motion match; their `adoption_date` is derived from the **instrument
   number's encoded year+month** (`YYYY-MM-NN`) with a **placeholder day `-01`** — this is
   far truer than the S3 batch-upload date (the whole 2017-2018 back-catalog was uploaded
   to the host in 2019-2020). Every such row is flagged in `linkage_note`
   ("day placeholder 01"). 11 further rows (R-/O-series and un-numbered docs, which encode
   no month) fall back to the flagged S3 upload date. **Do not read the placeholder day as
   a real adoption day.**
3. **Non-instrument attachments / test uploads excluded from the index (raws retained):**
   the three bulky `R2025-10 Attachment A/B/C` files (the Salt Lake County
   Multi-Jurisdictional Hazard-Mitigation-Plan volumes appended to the adopting resolution
   — county documents, not Kearns instruments), and `Ord_COP Test.pdf` (a Kearns
   "ORDINANCE COP TEST" placeholder/draft upload with no real number). The adopting
   resolution itself (`Kearns R2025-10`) IS indexed.

## Shared-MSD hazard — screened clean

Kearns, White City, Magna, and Copperton share MSD planning staff, so a neighbor's
ordinance can land in the wrong bucket. Every indexed instrument's **authoring caption**
was checked ("AN ORDINANCE OF THE KEARNS …"); **no cross-entity (White City / Magna /
Copperton) instrument was found mis-filed** in Kearns's bucket. Files that merely *mention*
neighbors (interlocal agreements, mosquito-abatement appointments, the county hazard plan)
are Kearns-authored and retained.

## As-of / re-harvest

Harvested 2026-07-13. The city-era code is **not-yet-fully-codified**; re-run
`kearns_ord_parse_s3.py` → fetch → `kearns_ord_extract.py` → `kearns_ord_index.py` to pick
up newly-posted 2025-2026 instruments.
