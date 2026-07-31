# Copperton — `ordinances/` (adopted ordinances & resolutions)

Additive dataset built by `/expand-city-sources` (source type 3), 2026-07-14. **Never
modifies** the existing `meeting_minutes/` layer; it only cross-references it. Canonical
gap/coverage prose is in `AVAILABILITY.md`; the machine-readable index is `index.csv`.

## Code host

**MunicipalCodeOnline** is the Town of Copperton's codified-code vendor
(`https://copperton.municipalcodeonline.com/`). Adopted-instrument PDFs live in a public
AWS S3 bucket (no auth, no browser UA needed for the listing/objects):

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/copperton/
```

**Unlike White City / Kearns (two subprefixes), Copperton scatters instruments across
SEVEN subprefixes** — all swept by the enumerator:
`ordinances/`, `resolutions/`, `orddoc/`, `fees/`, `landordinances/`, `policies/`, `plan/`.
(`ADC/` and `site/` hold only display PNGs/JPGs and the logo — excluded.)

**Codification status:** Copperton converted metro-township → **Town on 2024-05-01** and the
code host lags — the entire **2025 town-era resolution run `R2025-01…08` is cited in minutes
but not yet posted** (see `AVAILABILITY.md` gap 1). Re-harvest later to backfill.

## Build pipeline (all scripts live in THIS dir; unique `cop_ord_` prefix)

1. `cop_ord_enumerate.py` — lists the WHOLE `copperton/` S3 tree (`list-type=2`) once and
   classifies each object → `_s3_manifest.csv` (…,`in_scope`,`scope_reason`). In-scope =
   adopted ordinance/resolution INSTRUMENT PDFs; out = display images, the site logo, and
   non-instrument **plan / fee-schedule / policy-plan exhibits** (General Plan, Annexation
   Policy Plan, bare Fee Schedules — housing_plans/general-plan scope).
2. `cop_ord_build_batch.py` — in-scope manifest rows → `_fetch_batch.csv` (url,name).
   Saved names are collision-proof (`<subfolder>__<basename>` for the scattered folders) —
   Copperton reuses bare basenames across subfolders. The durable join is by **URL**, never
   the saved name.
3. `scripts/polite_fetch.py --batch _fetch_batch.csv --out raw` — 153 raws +
   `raw/_fetch_log.jsonl` (sha256 provenance). All raws retained verbatim (including
   byte-identical re-uploads; dedup happens later in the index).
4. `cop_ord_extract.py` — text sidecars: `pdftotext -layout`; if < 200 chars, tesseract OCR
   (pages rendered with `pdftoppm` into the **session scratchpad**, not `/tmp`; Python
   subprocess timeouts, not shell `timeout`). 83 born-digital / 70 OCR. Logs to
   `text/_extraction_log.csv`.
5. `cop_ord_index.py` — builds `index.csv` (§9 contract) with type-aware motion linkage.

Regenerate end-to-end: `python3 cop_ord_enumerate.py && python3 cop_ord_build_batch.py`,
fetch, `python3 cop_ord_extract.py && python3 cop_ord_index.py`. Idempotent.

## `index.csv` — SCHEMA_SPEC §9 ordinances contract + extras

Contract columns first (exact order): `ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence`. City extras follow:
`instrument_type` (ordinance|resolution), `canonical_no`, `dup_raw` (byte-identical
re-upload filenames retained on disk), `source_last_modified` (S3 upload date), `subfolder`
(which of the 7 prefixes), `linkage_note`.

- **`ordinance_no` / `canonical_no`** — from the MunicipalCodeOnline **original filename**
  (authoritative on the host), NOT the OCR header. Number grammars normalized in `canon()`:
  - township / early-town: `YY-MM-NN` and `YYYY-MM-NN` (`17-02-01` → `2017-02-01`).
  - **town-era ordinances: `YYYY-O-NN`** (`2025-O-01`, `2026-O-03`).
  - **town-era resolutions: `R-YYYY-NN`** (`R2026-02`).
  - The town-era **O-series is frequently mis-printed in minutes as a zero** (`2025-0-01`); a
    single `0` middle segment is normalized to `O` (a real month is never 0), so the OCR
    `0↔O` slip still links. Title 18/19 code books with no number → `TITLE-18`/`TITLE-19`.
- **`format`** ∈ `text` (born-digital) / `scanned` (OCR). 71 text / 58 scanned.
- **`result`** = the matched council motion's verbatim result (blank when unmatched); the
  motion outcome, never invented.
- **`land_use`** — coarse word-boundary keyword flag (zoning/subdivision/Title 18-19/setback/
  ADU/home-occupation/WUI/wildland/annex/engineering-standard/impact-fee/…). Advisory.

## Motion linkage (to `meeting_minutes/all_votes.csv`) — TYPE-AWARE

**Copperton runs PARALLEL ord/res numbering** (the magna lesson): the 2024-05-15 meeting
adopted BOTH `resolution 2024-05-01` (motion 3) AND `ordinance 2024-05-01` (motion 5), so an
ordinance PDF must match the *ordinance* motion. Candidates are filtered by instrument type
(honoring the ordinance/resolution word before the number, and the R-series = always a
resolution). Confidence:

- **high (17)** — the instrument number is cited in a recorded motion of the same type.
  `adoption_date` = the **motion date** (clean minutes) — it wins over the doc's own header
  when they disagree (some OCR/clerk headers carry a typo'd year; `linkage_note` flags it).
- **medium (22)** — no number in the motion, but subject-term overlap with a type-consistent
  motion. When the instrument carries its own header date the motion must fall **within 20
  days** of it (prevents an Aug fee ordinance linking to an Oct motion); else same-year ±2
  months. Year-only (O/R/Title) series need a stronger overlap. `adoption_date` prefers the
  doc's header date.
- **low (10)** — the header adoption date lands on a meeting whose only ord/res-type approving
  motion is unnumbered (date-only corroboration).
- **none (80)** — unmatched. Most Copperton motions read "to approve the ordinance/resolution"
  with no number, so a high `none` count is expected, not a miss.

**Adoption-date fallback (kearns lesson):** for an unmatched `std` number the fallback is the
**instrument number's own `YYYY-MM` (day placeholder `01`)** in preference to the S3 upload
date (flagged in `linkage_note`). O/R-series numbers carry no month, so those fall to the
header date, else the flagged upload date. **The mayor/chair VOTES in both eras (max roll = 5)**
— linkage never assumes the mayor is a non-voter.

## Caveats

- **Dedup:** 23 byte-identical S3 re-uploads collapse to one row each (both raws retained;
  alternate named in `dup_raw`). Distinct documents that share a number but differ in content
  (e.g. two different `Ordinance 2023-06-01.pdf`, or Title 18 base vs its Amendment) are
  **separate rows** — sha256 is the only dedup key, `canonical_no` is not.
- **Cross-entity decoy (shared-MSD hazard):** `raw/1597946761_Ordinance_20-08-01.pdf` is a
  **Kearns** ordinance mis-filed in Copperton's bucket — retained as raw, **excluded** from
  the index (`EXCLUDE_FILES`, with the caption evidence in-code). Only mis-file found in a
  full-caption sweep of all 153 sidecars.
- **Completeness gap** (12 cited-but-unposted numbers, incl. the whole 2025 `R2025-*` run) is
  real and documented in `AVAILABILITY.md` — not fabricated into rows.
- Derived working files (`_s3_manifest.csv`, `_fetch_batch.csv`) are regenerable and kept for
  provenance; `index.csv`, `raw/`, and `text/` are the durable artifacts.
