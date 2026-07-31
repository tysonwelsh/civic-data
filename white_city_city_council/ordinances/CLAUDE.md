# White City — `ordinances/` (adopted ordinances & resolutions)

Additive dataset built by `/expand-city-sources` (source type 3), 2026-07-13. **Never
modifies** the existing `meeting_minutes/` layer; it only cross-references it. Canonical
gap/coverage prose is in `AVAILABILITY.md`; the machine-readable index is `index.csv`.

## Code host

**MunicipalCodeOnline** is White City's codified-code vendor. Adopted-instrument PDFs live
in a public AWS S3 bucket (browser UA not even required for the S3 listing/objects):

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/whitecity/
    ordinances/documents/    (ordinances + a few misfiled resolutions/code titles)
    resolutions/documents/   (resolutions + misfiled MIH/general-plan docs)
```

**Codification status:** White City became a CITY on 2024-05-01 (HB35) and is ~8 months
into a full municipal-code rewrite (2024–2026). The adopted-instrument archive on the code
host is real but **lags** — its newest posted document is Dec 2025; the entire **2026**
city-era resolution run is cited in minutes but **not yet on the host** (see
`AVAILABILITY.md` gap 1). So the code is **not-yet-fully-codified**; re-harvest later to
backfill 2026+.

## Build pipeline (all scripts live in THIS dir; unique `wc_ord_` prefix)

1. `wc_ord_enumerate.py` — pages the S3 bucket (`list-type=2`) → `_s3_manifest.csv`
   (key, filename, size, last_modified) for the `ordinances/` + `resolutions/` prefixes.
2. `wc_ord_build_batch.py` — manifest → `_fetch_batch.csv`, excluding out-of-scope files
   (Copperton decoy by name; the two Moderate-Income-Housing PDFs → `housing_plans/`).
3. `scripts/polite_fetch.py --batch _fetch_batch.csv --out raw` — 142 raws +
   `raw/_fetch_log.jsonl` (sha256 provenance). All raws retained verbatim.
4. `wc_ord_extract.py` — text sidecars: `pdftotext -layout`; if < 200 chars, tesseract OCR
   (pages rendered with `pdftoppm` into the **session scratchpad**, not `/tmp`; Python
   subprocess timeouts, not shell `timeout`). Logs method/chars to `text/_extraction_log.csv`.
5. `wc_ord_index.py` — builds `index.csv` (§9 contract) with motion linkage (below).

Regenerate end-to-end: `python3 wc_ord_enumerate.py && python3 wc_ord_build_batch.py`,
fetch, `python3 wc_ord_extract.py && python3 wc_ord_index.py`. Idempotent.

## `index.csv` — SCHEMA_SPEC §9 ordinances contract + extras

Contract columns first (exact order): `ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence`. City extras follow:
`instrument_type` (ordinance|resolution), `canonical_no`, `dup_raw` (byte-identical
re-upload filename retained on disk), `source_last_modified` (S3 upload date),
`linkage_note`.

- **`ordinance_no`** — taken from the **MunicipalCodeOnline filename** (authoritative on the
  host), NOT the OCR header (OCR headers carry noise and clerk typos). Formats across eras:
  township `YY-MM-NN` (e.g. `17-02-01`) and `YYYY-MM-NN`; city-era ordinances `YYYY-O-NN`
  (`2024-O-01`). All normalized to a 4-digit-year canonical in `canonical_no`.
- **`format`** ∈ `text` (born-digital) / `scanned` (image-only → OCR). 99 scanned, 37 text.
- **`result`** = the **matched council motion's verbatim result** string (blank when
  unmatched); it is the motion outcome, never an invented value.
- **`land_use`** — coarse word-boundary keyword flag (zoning/subdivision/rezone/land-use/
  general-plan/plat/setback/density/annex/title 18-19/19.46/WUI/wildland/ADU/floodplain/
  zone). Advisory, not a legal classification.

## Motion linkage (to `meeting_minutes/all_votes.csv`)

Instruments carry independently-published PDFs, so matches are genuine cross-matches
(**`within_source` is NOT used** — that value is reserved for minutes-only derivations,
which this dataset is not). Confidence:

- **high (95)** — the instrument number is cited in a recorded motion. `adoption_date` =
  the **motion date** (clean born-digital minutes) — it wins over the instrument's own
  header when they disagree, because some OCR/clerk headers carry a typo'd year (e.g. Res
  `23-06-02` printed "DATE: June 22, **2022**" for the 2023-06-22 meeting; `linkage_note`
  flags such conflicts).
- **medium (7)** — no exact number match, but same-year (± 2 months when the number encodes
  a month) + subject-term overlap. Handles the `YYYY-O-NN` vs `YYYY-MM-NN` drift
  (S3 `2025-O-02` ↔ motion-cited `2025-02-02`). `adoption_date` prefers the instrument's
  own header date here (the motion is only a subject guess).
- **none (34)** — unmatched. `adoption_date` = the instrument's own header date, else a
  **flagged S3 upload date** (`linkage_note: date=upload_date...`). A broad body-date scan
  is deliberately avoided (it grabs term-expiry/effective dates, not adoption).

`matched_motion_date` + `matched_motion_no` point back to the `all_votes.csv` motion.
**Mayor/Chair votes in both eras — max roll-call tally = 5** (see the parent city CLAUDE.md);
linkage does not assume the mayor is a non-voter.

## Caveats

- **Dedup:** 5 byte-identical S3 re-uploads collapse to one row each (both raws retained;
  alternate named in `dup_raw`). Distinct documents that share a base number but differ
  (e.g. `Ordinance 18-01-01` vs `Ordinance 18-01-01 Policy #2`) are **separate rows**.
- **Copperton decoy:** `raw/1647891849_Ordinance_2021-10-01.pdf` is a Copperton-authored
  ordinance mis-filed in White City's bucket — retained as raw, **excluded** from the index
  (`wc_ord_index.py EXCLUDE_FILES`).
- **Completeness gap** (68 cited-but-unposted instruments, incl. all of 2026) is real and
  documented in `AVAILABILITY.md` — not fabricated into rows.
- Derived working files (`_s3_manifest.csv`, `_fetch_batch.csv`) are regenerable and kept
  for provenance; `index.csv`, `raw/`, and `text/` are the durable artifacts.
