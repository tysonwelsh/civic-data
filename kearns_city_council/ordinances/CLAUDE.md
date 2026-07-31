# Kearns — `ordinances/` (adopted ordinances & resolutions)

Additive dataset built by `/expand-city-sources` (source type 3), 2026-07-13. **Never
modifies** the existing `meeting_minutes/` layer; it only cross-references it. Canonical
gap/coverage prose is in `AVAILABILITY.md`; the machine-readable index is `index.csv`.

## Code host

**MunicipalCodeOnline** is Kearns's codified-code vendor. Adopted-instrument PDFs live in a
public AWS S3 bucket (no auth, browser UA not required — the city's own
`kearns.utah.gov` is Cloudflare-blocked and was NOT used):

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/kearns/
    ordinances/documents/    (ordinances + a few cross-filed resolutions/code titles)
    resolutions/documents/   (resolutions + a few cross-filed ordinances)
    plan/documents/          (General Plan + its adopting ord/res — GP itself -> housing_plans)
    fees/documents/          (fee schedules — not indexed here)
```

**Codification status: NOT-YET-FULLY-CODIFIED.** Kearns incorporated as a CITY (2024-05,
first city officials seated Jan 2026) and the post-cityhood municipal-code rewrite is
underway; the host archive is real but **lags** — 26 minute-cited 2025-2026 city-era
instruments are not yet posted (`AVAILABILITY.md` gap 1). Re-harvest later to backfill.

## Build pipeline (all scripts live in THIS dir; unique `kearns_ord_` prefix)

1. `kearns_ord_parse_s3.py` — parses the four S3 `list-type=2` XML listings (saved in the
   session scratchpad) → dedupes by **ETag** (byte-identical re-uploads under different
   unix-ts filename prefixes) → `kearns_ord_manifest.csv` + `kearns_ord_batch.csv`
   (`url,name`), guaranteeing unique local names (collisions get a `__<etag6>` suffix).
   Skips the 6 General-Plan / fee-schedule PDFs in `plan/`+`fees/`.
2. `scripts/polite_fetch.py --batch kearns_ord_batch.csv --out raw` — 227 raws +
   `raw/_fetch_log.jsonl` (sha256 provenance). All raws retained verbatim.
3. `kearns_ord_extract.py` — text sidecars: `pdftotext -layout`; if < 200 chars,
   `tesseract` OCR (pages rendered with `pdftoppm` into the **session scratchpad**, not
   `/tmp`; Python subprocess timeouts, not shell `timeout`); `.docx` via `textutil`. Logs
   method/chars to `text/_extraction_log.csv`.
4. `kearns_ord_index.py` — builds `index.csv` (§9 contract) with motion linkage (below).

Regenerate end-to-end (re-fetch the S3 XML into the scratchpad first):
`python3 kearns_ord_parse_s3.py && … fetch … && python3 kearns_ord_extract.py &&
python3 kearns_ord_index.py`. Idempotent.

## `index.csv` — SCHEMA_SPEC §9 ordinances contract + extras

Contract columns first (exact order): `ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence`. City extras follow:
`instrument_type` (ordinance|resolution), `canonical_no`, `dup_raw` (byte-identical
re-upload filename retained on disk), `source_last_modified` (S3 upload date),
`linkage_note`.

- **`ordinance_no` / number families** — taken from the **MunicipalCodeOnline filename**
  (authoritative on the host), normalized by `canon()`. THREE families, all handled:
  - township 3-part `YY-MM-NN` / `YYYY-MM-NN` — the middle segment IS the month
    (e.g. `17-02-01` = Feb 2017; `2024-05-01` = May 2024). Expanded to 4-digit year.
  - city ordinance `YYYY-O-NN` (e.g. `2025-O-08`) — OCR `0`↔`O` drift tolerated.
  - city resolution `RYYYY-NN` (e.g. `R2026-12`).
  Un-numbered instruments (PC Rules of Order, a code-section correction, an interlocal
  agreement) keep `ordinance_no` blank; the two adopted code books get `TITLE-18`/`TITLE-19`.
- **`format`** ∈ `text` (born-digital pdf/docx) / `scanned` (image-only → OCR). 119 / 104.
- **`result`** = the matched council motion's **verbatim** result string (blank when
  unmatched); never an invented value.
- **`land_use`** — coarse word-boundary keyword flag (zoning/subdivision/rezone/land-use/
  general-plan/plat/setback/density/annex/Title 18-19/19.4x-19.50/WUI/wildland/ADU/
  floodplain/overlay/landscap/conditional-use). Advisory, not a legal classification. 56 yes.

## Motion linkage (to `meeting_minutes/all_votes.csv`)

Independently-published PDFs → genuine cross-matches, so **`within_source` is intentionally
UNUSED** (it is reserved for minutes-only derivations). Confidence:

- **high (74)** — the instrument number is cited in a recorded motion (exact `canon` match
  on number). `adoption_date` = the **motion date** (born-digital minutes) — it wins over a
  scanned header date when they disagree (`linkage_note` flags the conflict). The minutes
  cite the FULL 3-part township number and the exact city-era number, so most matches are
  exact — the feared `R2026-NN` vs `YYYY-O-NN` drift is handled in `canon()` (R-series vs
  O-series vs month-seq), including the OCR `2025-0-04`→`2025-O-04` zero/O confusion.
- **medium (7)** — no exact number match, but same-year (±2 months when the number encodes
  a month) + ≥2 shared subject terms. `adoption_date` prefers the instrument's header date.
- **none (142)** — unmatched. Mostly routine appointments/budgets/franchise items whose
  motions don't cite a number, plus 2017-2018 instruments that predate the recorded-minutes
  floor on disk (PMN blob-purge gap). `adoption_date` = header date, else the **number's
  encoded year-month with a placeholder day `-01`** (flagged in `linkage_note`; truer than
  the 2019-2020 batch S3-upload date), else (R-/O-series/un-numbered) the flagged upload date.

`matched_motion_date` + `matched_motion_no` point back to the `all_votes.csv` motion.
**⚠ The Mayor VOTES in the city era (max roll tally = 5, incl. Mayor Valdez); the township
Chair also voted** — linkage never assumes the mayor is a non-voter.

## Caveats

- **Dedup:** byte-identical S3 re-uploads (same ETag) collapse to one manifest entry;
  distinct-byte copies that share a base number (e.g. a signed vs unsigned scan) are kept
  as **separate rows** (raws retained). **3 instruments exist as both `.pdf` and `.docx`**
  (`18-10-01`, `19-10-03`, `R2026-03`) — two rows, one shared text sidecar.
- **Excluded from the index, raws retained** (`EXCLUDE_FILES`): the three
  `R2025-10 Attachment A/B/C` files (Salt Lake County hazard-plan volumes appended to the
  resolution — county docs, not Kearns instruments) and `Ord_COP Test.pdf` (a Kearns
  "ORDINANCE COP TEST" placeholder upload with no real number). The adopting resolution
  `R2025-10` itself IS indexed.
- **Shared-MSD hazard screened clean:** authoring captions all read "…OF THE KEARNS…"; no
  White City / Magna / Copperton instrument is mis-filed in Kearns's bucket. Files that
  merely mention neighbors are Kearns-authored.
- **OCR is faithful** — source typos preserved (a bad scan that reads implausibly clean is
  the hallucination signal, not the reverse). `screen_corpus.py` outliers are number-heavy
  budget/franchise scans, not corruption.
- Derived working files (`kearns_ord_manifest.csv`, `kearns_ord_batch.csv`, `*.log`) are
  regenerable and kept for provenance; `index.csv`, `raw/`, and `text/` are the durable
  artifacts.
