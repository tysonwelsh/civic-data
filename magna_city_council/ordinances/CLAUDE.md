# Magna — `ordinances/` (adopted ordinances & resolutions)

Additive dataset built by `/expand-city-sources` (source type 3), 2026-07-13. **Never
modifies** the existing `meeting_minutes/` layer; it only cross-references it. Canonical
gap/coverage prose is in `AVAILABILITY.md`; the machine-readable index is `index.csv`.

## Code host

**MunicipalCodeOnline** is Magna's codified-code vendor. Adopted-instrument PDFs live in a
public AWS S3 bucket (no auth, no browser UA needed):

```
https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/magna/
    ordinances/documents/    (ordinances; a few cross-filed resolutions)
    resolutions/documents/   (resolutions; a few cross-filed ordinances)
    plan/documents/          (General Plan + Water Element + adopting ord/res)
    fees/documents/          (fee schedules + one adopting resolution)
```

**Codification status: NOT-YET-FULLY-CODIFIED.** Magna became a CITY 2024-05-01 (HB35)
and elected its first executive Mayor in 2025 (seated ~Jan 2026); the post-cityhood
municipal-code rewrite (Title renumbering, the 2025-26 `YYYY-O-NN` / `RYYYY-NN` city-era
instruments) is **underway**. The host archive is real and current through **2026-06** but
will keep growing — re-harvest later to backfill new instruments.

## Build pipeline (all scripts live in THIS dir; unique `magna_ord_` prefix)

1. `magna_ord_parse_s3.py` — parses the four S3 `list-type=2` XML listings (saved in the
   session scratchpad as `magna_s3_<pref>.xml`) → dedupes by **ETag** (byte-identical
   re-uploads under different unix-ts filename prefixes) → `magna_ord_manifest.csv` +
   `magna_ord_batch.csv` (`url,name`). Skips 8 non-instruments (General Plan, Appendix,
   Active Transportation Plan, 4 fee schedules, the MIH packet) via `is_instrument()`.
2. `polite_fetch.py --batch magna_ord_batch.csv --out raw` — 241 raws +
   `raw/_fetch_log.jsonl` (sha256 provenance). All raws retained verbatim.
   ⚠ Two filenames contain commas; the CSV-quoted `name` reached disk wrapped in literal
   `"…"` quotes (so they ended in `"` and were skipped by the `.pdf` filter). They were
   renamed to strip the quotes and OCR'd — a `polite_fetch` batch-parsing quirk to watch
   for on any comma-bearing filename.
3. `magna_ord_extract.py` — text sidecars: `pdftotext -layout`; if < 200 chars,
   `tesseract` OCR (pages rendered with `pdftoppm` into the **session scratchpad**, not
   `/tmp`; Python subprocess timeouts, not shell `timeout`); `.docx` via `textutil`. Logs
   method/chars to `text/_extraction_log.csv`. 89 born-digital / 150 OCR.
4. `magna_ord_index.py` — builds `index.csv` (§9 contract) with motion linkage (below).

Idempotent end-to-end (re-fetch the S3 XML into the scratchpad first). See
`AVAILABILITY.md` for the exact commands.

## `index.csv` — SCHEMA_SPEC §9 ordinances contract + extras

Contract columns first (exact order): `ordinance_no, adoption_date, date, title,
source_url, retrieved_date, format, extraction_method, path, land_use, result,
matched_motion_date, matched_motion_no, match_confidence`. City extras follow:
`instrument_type` (ordinance|resolution), `canonical_no`, `dup_raw`, `source_last_modified`
(S3 upload date), `linkage_note`.

- **`ordinance_no` / number families** — from the MunicipalCodeOnline filename
  (authoritative), normalized by `canon()`. Handles the HB35 numbering drift:
  - township month-seq `YY-MM-NN` / `YYYY-MM-NN` — the middle segment IS the month
    (`17-01-01` = Jan 2017; `2024-01-01` = Jan 2024). Expanded to 4-digit year. **151 rows.**
  - city ordinance `YYYY-O-NN` (also 2-digit `22-O-01`; OCR `0`↔`O` tolerated). **42.**
  - city resolution `RYYYY-NN` (a trailing `A` re-issue letter strips to the base number
    for linkage; the `A` file is kept as a distinct row). **38.**
  - adopted code books → `TITLE-18` (subdivision) / `TITLE-19` (zoning), versioned. **7.**
  - un-numbered instrument (the Electronic Signatures Ordinance) → blank. **1.**
- **`format`** ∈ `text` (born-digital pdf/docx) / `scanned` (OCR). 89 / 150.
- **`result`** = the matched council/CRA motion's **verbatim** result string (blank when
  unmatched); never invented.
- **`land_use`** — coarse word-boundary keyword flag (zoning/subdivision/rezone/plat/
  setback/density/annex/Title 18-19/19.xx/planned-community/P-C/WUI/wildland/ADU/floodplain/
  overlay/landscap/hardscape/conditional-use/water-element). Advisory, not legal. **55 yes.**

## Motion linkage (to `meeting_minutes/all_votes.csv`)

Independently-published PDFs → genuine cross-matches, so **`within_source` is intentionally
UNUSED** (it is reserved for minutes-only derivations). Confidence:

- **high (131)** — the instrument number is cited in a recorded motion (exact `canon`
  match, ordinance/resolution hint honored). All 131 verified: the canonical number
  literally appears in the matched motion. `adoption_date` = the **motion date** (wins over
  a scanned header date if they disagree; `linkage_note` flags the conflict). Council
  motions cite the FULL 4-digit-year township number and the exact city-era number
  (`2018-09-01`, `2023-O-05`, `R2026-28`), incl. the OCR `2025-0-01`→`2025-O-01` drift.
- **medium (10)** — no exact number match, but same-year (±2 months when the number encodes
  a month) + ≥2 shared subject terms. `adoption_date` prefers the header date.
- **none (98)** — unmatched. Routine appointments/budgets/interlocals whose motions cite no
  number, plus pre-2018-07-17 instruments that predate the on-disk minutes floor.
  `adoption_date` = header date, else the **number's encoded `YYYY-MM` + placeholder day
  `-01`** (truer than the S3 upload date), else (R-/O-series/un-numbered) the flagged
  upload date (20 rows).

⚠ **PARALLEL township numbering** — ordinances and resolutions share the `YY-MM-NN`
sequence (`Ordinance 20-06-02` AND `Resolution 20-06-02` both exist → same `canon`). The
linkage filters candidate motions by the ordinance/resolution word cited in the motion, so
an ordinance never inherits a resolution-hinted motion (this was a real bug caught in QA:
`Ordinance 20-06-02` had wrongly grabbed a "Resolution 20-06-02" motion; now honest `none`).

⚠ **Presiding-officer VOTE FLIP at the 2024/2026 HB35 seam** — the township Chair-"Mayor"
VOTED (e.g. AYE Mayor Barney, `4-0`), but the 2026+ elected Mayor Sudbury does NOT
(`4-0`/`5-0` excludes him). Max council roll = 5 in BOTH eras. Linkage only reads motion
text, so it is agnostic to the mayor's voting status.

## Caveats

- **Dedup:** byte-identical S3 re-uploads (same ETag) collapse before fetch (12); distinct-
  byte copies that share a number (signed vs unsigned scans, `A` re-issues, versioned Title
  books, the Council-vs-CRA `R2026-01` pair) are kept as **separate rows** (raws retained).
- **Excluded from the index, raws retained** (`is_excluded()`): the SLCo
  MultiJurisdictional Hazard Mitigation Plan volume bundled with `R2026-13` (a **county**
  document — the adopting resolution `R2026-13` IS indexed), and the `05-10-22` Bird scooter
  agreement (a contract exhibit, not an instrument).
- **Shared-MSD hazard screened clean** — all filenames Magna-numbered; sampled captions read
  "…OF THE MAGNA … COUNCIL." No Kearns/White City/Copperton/Emigration instrument mis-filed.
- **OCR is faithful** — source typos preserved (a bad scan reading implausibly clean is the
  hallucination signal). `screen_corpus.py` outliers are sparse/number-heavy signed scans,
  not corruption.
- Derived working files (`magna_ord_manifest.csv`, `magna_ord_batch.csv`, `*.log`) are
  regenerable and kept for provenance; `index.csv`, `raw/`, and `text/` are the durable
  artifacts.
