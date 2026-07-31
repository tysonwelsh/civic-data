# Emigration Canyon — `ordinances/` (adopted ordinances & resolutions)

Additive dataset built by `/expand-city-sources` (source type 3), 2026-07-14. **Never
modifies** the existing `meeting_minutes/` layer; it only cross-references it. Canonical
gap/coverage prose is in `AVAILABILITY.md`; the machine-readable index is `index.csv`.

## Code host

**MunicipalCodeOnline** is Emigration Canyon's codified-code vendor (same cluster as
white_city / kearns / magna / copperton). Adopted-instrument PDFs live in a public AWS S3
bucket. **The working slug is `emigrationcanyon`** — the bare `emigration` slug is EMPTY
(both were probed; `.../emigration/ordinances/` returns 0 keys).

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/emigrationcanyon/
    ordinances/documents/    51 objects (ordinances + resolutions, filed loosely)
    resolutions/documents/   49 objects (resolutions + a few ordinances)
    orddoc/documents/        22 objects (city-era 2025-O/2026-O SIGNED PDFs + Ordinance Log.xlsx)
    policies/documents/       2 objects (2 stray adopted instruments)
    plan/ fees/ ADC/ site/   (general plan, fee schedule, consolidated code — NOT harvested here)
```

- **`orddoc/` is EC-specific** (white_city has no such prefix): it holds the clean
  born-digital signed city-era ordinances (`2025-O-01` … `2026-O-04`) plus the clerk's
  **`Ordinance Log.xlsx`** (a per-year number → description → Passed Y/N → **Date Signed**
  spreadsheet — authoritative, used for adoption dates; see below).
- **Codification lag:** EC became a CITY 2024-05-01 (HB35) and is mid municipal-code
  rewrite. The archive is real but lags — several 2025–2026 resolutions cited in minutes
  are not yet posted (`AVAILABILITY.md` gap 1). Re-harvest later to backfill.

## Build pipeline (all scripts live in THIS dir; unique `ec_ord_` prefix)

1. `ec_ord_enumerate.py` — pages the S3 bucket (`list-type=2`) → `_s3_manifest.csv`
   (key, filename, size, last_modified) for the four adopted-instrument prefixes; also
   PROBEs `plan/` + `fees/` for the report.
2. `ec_ord_build_batch.py` — manifest → `_fetch_batch.csv` (url,localname). Fetches
   **EVERY** object; dedup/exclusion is an index-time decision, never a fetch-time drop.
3. `scripts/polite_fetch.py --batch _fetch_batch.csv --out raw` — 124 raws +
   `raw/_fetch_log.jsonl` (sha256 provenance). All raws retained verbatim (155.9 MB).
4. `ec_ord_extract.py` — text sidecars: `pdftotext -layout`; if < 200 chars, tesseract
   OCR (pages rendered with `pdftoppm` into the **session scratchpad**, not `/tmp`; Python
   subprocess timeouts, not shell `timeout`). `.docx`/`.xlsx` raws are retained but not
   sidecar'd (their PDF twin carries the text). Logs method/chars to
   `text/_extraction_log.csv`.
5. `ec_ord_index.py` — builds `index.csv` (§9 contract) with motion linkage (below).

Regenerate end-to-end: `python3 ec_ord_enumerate.py && python3 ec_ord_build_batch.py`,
fetch, `python3 ec_ord_extract.py && python3 ec_ord_index.py`. Idempotent.

## `index.csv` — SCHEMA_SPEC §9 ordinances contract + extras

Contract columns first (exact order): `ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence`. City extras follow:
`instrument_type` (ordinance|resolution), `canonical_no`, `dup_raw` (alternate
raw filenames collapsed into this row, `;`-joined), `source_last_modified` (S3 upload
date), `linkage_note`.

- **98 distinct instruments — 49 ordinances + 49 resolutions**, window **2017-04 → 2026-05**.
- **`ordinance_no` / `canonical_no`** — the **host-authoritative filename number** (NOT the
  OCR header). Three numbering eras, all normalized in `canonical_no`:
  - township `YY-MM-NN` (e.g. `18-06-02`)
  - transitional `YYYY-MM-NN` (e.g. `2022-01-01`)
  - city-era ordinances `YYYY-O-NN` (`2025-O-13`); city-era resolutions `RYYYY-NN`
    (`R2026-10`).
- **PARALLEL ord/res numbering (magna lesson):** an ordinance and a resolution can SHARE a
  number in the same period — `2023-06-01` and `2024-07-01` each exist as **both**. Rows are
  keyed on `(instrument_type, canonical_no)`, never number alone.
- **OCR 0↔O (city era):** council minutes write `2025-0-04` (digit zero) for instrument
  `2025-O-04` (letter O). The number normalizer folds `-0-`/`-O-` so the linkage matches.
- **`format`** ∈ `text` (45 born-digital `pdftotext_layout`) / `scanned` (53 OCR
  `ocr_tesseract`). The MunicipalCodeOnline copies are ~half image scans, even recent years.
- **`land_use`** — coarse, advisory keyword flag (24 rows) from the title, falling back to
  the body text only when the title is a bare instrument label. NOT a legal classification.
- **`result`** = the matched council motion's verbatim result string (blank when unmatched).

## Motion linkage (to `meeting_minutes/all_votes.csv`)

The instruments are published PDFs INDEPENDENT of the minutes, so a number match is a
genuine cross-match — **`within_source` is NOT used** (that value is reserved for
minutes-only derivations). Distribution: **54 high · 2 medium · 42 none.**

- **high (54)** — the instrument number is cited in a recorded council motion (same
  `instrument_type`). `adoption_date` = the **motion date** (clean born-digital minutes win).
- **medium (2)** — no number match, but same year + subject-term overlap with a motion of
  the same type (`2025-O-02` engineering standards; `R2026-04` alternate MSD-board rep).
- **none (42)** — unmatched. Most PRE-DATE the recovered-minutes floor (council minutes
  begin **2018-10**; everything 2017 → mid-2018 and other pre-floor meetings has no motion
  to match), or are procedural resolutions the minutes reference without a number.

**Adoption-date precedence** for non-high rows (kearns lesson — prefer the encoded
year-month over the S3 upload date):
1. **Ordinance Log `Date Signed`** (day-precision, authoritative, ORDINANCES only) —
   applied to ~22 rows incl. the city-era `2025-O-01/08/12/13/14`;
2. the instrument number's **encoded year-month** (`YYYY-MM` → `YYYY-MM-01`);
3. the **S3 upload date**, explicitly flagged in `linkage_note` (city-era `-O-`/`R`
   numbers encode no month).

**Mayor VOTES in both eras — max roll-call tally = 5** (Millcreek pattern; see the parent
CLAUDE.md). Linkage never assumes the mayor is a non-voter.

## Dedup & exclusions

- **Dedup:** cross-prefix re-uploads (a `2025-O-NN` in both `ordinances/` and `orddoc/`),
  byte-twins, and a `.docx`/`.pdf` pair (`20-11-01`) collapse to **one row per
  `(type, canonical_no)`** — the born-digital PDF wins as canonical; every alternate raw is
  named in `dup_raw` and **retained on disk**.
- **Retained-but-EXCLUDED from the index** (raw kept for provenance; not adopted-instrument
  texts): `Ordinance Log.xlsx` (the clerk catalog, used only for dates), the **Dominion
  Energy franchise agreement** (an exhibit to Ord `19-05-02`), and the two **SLCo Hazard
  Mitigation Plan** volumes (`…Annex…`, `…MJHMP Volume1…` — exhibits to Res `R2026-02`;
  belong to emergency-/general-planning, not the ordinance index).
- **Cross-entity decoys:** NONE found. Every instrument's authoring caption was checked;
  none is authored by white_city / kearns / magna / copperton (the shared-MSD hazard that
  mis-filed a Copperton ordinance in White City's bucket did not recur here).

Derived working files (`_s3_manifest.csv`, `_fetch_batch.csv`) are regenerable and kept for
provenance; `index.csv`, `raw/`, and `text/` are the durable artifacts.
