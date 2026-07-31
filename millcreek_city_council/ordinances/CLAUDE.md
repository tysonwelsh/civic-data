# Millcreek — adopted zoning/land-use ordinances (`ordinances/`)

Expansion source #3 (`expand-city-sources` §3). An **additive** catalog of Millcreek's
**adopted ordinance texts** — especially zoning map/text amendments, rezones, and
development agreements — linked to the council votes that adopted them. Purely additive:
nothing in `meeting_minutes/`, `planning_commission/`, `db/`, etc. was modified.

## Source — municipalcodeonline.com S3 back-catalog (independent of the minutes)
Millcreek's codified-code host is **municipalcodeonline.com**, whose adopted-ordinance
PDFs live in a **publicly listable S3 bucket**:

```
bucket:  municipalcodeonline.com-new   (region us-west-2 — path-style only; the
         virtual-host name has dots and fails TLS)
list:    https://s3.us-west-2.amazonaws.com/municipalcodeonline.com-new/?list-type=2&prefix=millcreek/<sub>/
ordinance PDFs under:  millcreek/ordinances/documents/ , millcreek/orddoc/documents/ ,
                       millcreek/ordinances2/documents/ , millcreek/planzone/documents/ ,
                       millcreek/ordinances/pdf/
```
812 objects → **550 distinct adopted ordinances, 2016-01 → 2026** (`ORD YY-NN`). This is
a genuine second source for each ordinance NUMBER, independent of the council minutes.
`s3_sources.csv` is the manifest (ord_no → chosen S3 key/url/size/stored_locally); when
several files exist for one ordinance the smallest non-exhibit "signed" version is chosen.

Raw PDFs fetched with `scripts/polite_fetch.py` into `raw/<ord_no>.pdf` (525 files, 857 MB;
`raw/_fetch_log.jsonl` = url/status/bytes/sha256/retrieved_utc for every byte).

### Oversize index-only exception (25 ordinances)
25 ordinances whose only/best PDF is a **>8 MB exhibit bundle** (plats, corridor-study maps)
are catalogued **index-only** (`format=na`, `path` empty, `stored_locally=no` in
`s3_sources.csv`) with a live `source_url` — a documented, allowed exception to
"retain every raw original" (files are public + re-fetchable). Fetch on demand from
`source_url`; vision/OCR required to read them.

## Adoption dates — mostly OCR/text, NOT mass-vision
Contrary to the "handwritten date" expectation, the adoption date is usually **printed**
text — `PASSED AND APPROVED this Nth day of MONTH, YEAR` (signature page) or
`met in a regular session on MONTH D, YEAR to consider` (page-1 WHEREAS). The **day digit**
is sometimes handwritten/OCR-garbled, but **month + year print reliably**. Extraction ladder
(see `extract_ordinance.py`, cached to `date_extractions.csv` by `build_date_cache.py`):
1. `pdftotext -layout` whole doc → regex the adoption clause (284 born-digital text-layer PDFs).
2. Image-scan PDFs (no text layer) → **tesseract OCR** of page 1 + signature page, then whole
   doc for the residual (231 scanned).
3. **Vision (Read tool)** for **6** ordinances OCR couldn't date (17-07, 17-08, 17-11, 17-99,
   24-02, 26-46) — see `note` column.
`date_precision` ∈ `day` (522) / `month` (28 — day illegible/handwritten, month+year kept).
Never a fabricated day: a month-only reading stays month-granular.

## Linkage to votes (`index.csv`)
Join by **ordinance number cited in `../meeting_minutes/all_votes.csv` motion/title text**
(regex `Ordinance YY-NN`) — 443 of the 550 numbers appear in council motions.

`match_confidence`:
- **high (346)** — number cited in a council motion **AND** the PDF's own month+year
  (independent source) equals that motion's month → cross-source corroborated. The index
  `date` is then the authoritative council-action date (`matched_motion_date`).
- **medium (84)** — number cited in council motion(s) but the PDF month/year is not
  independently extractable (e.g. oversize index-only, or OCR gave no date), or the number is
  cited on >1 meeting date. `date` = the matched motion date; treat as number-only match.
- **none (120)** — no council motion cites the number (mostly 2016-18 procedural ordinances
  predating the named-vote seam, plus a few uncited rezones). `date` = the PDF's own adoption
  date (OCR/vision). No motion is forced.

`date` (the validator-required column) is a non-empty best-effort adoption date;
`adoption_date_source` ∈ `motion` / `pdf` records which source it came from.

**`land_use`** (`yes`=213 ≈39%) — keyword classification (rezone/zoning/subdivision/plat/
development agreement/overlay/annex/general plan/Title 19/ADU/impact fee…) over the title +
matched motion text. A screening flag, not a legal determination.

## Known limitations / findings
- **`citations_without_document.csv` (13)** — ordinance numbers cited in council motions with
  **no adopted PDF on the code host** (mostly recent 2025-26 not-yet-uploaded, a few older).
  Real gap in the host's catalog, not an extraction miss — do not fabricate a document row.
- **`17-99` is an APPARENT TEST/TEMPLATE document** on the code host (voters "John Doe /
  Jane Doe / Betsy Ross", a "(joke)" clause, a fictitious `U.C.A. 3.4.5`). Flagged in `note`;
  kept in the index for provenance but **not an authentic adopted ordinance** — exclude from
  analysis.
- **OCR garble** (same corpus caveat as the minutes) affects titles; 8/550 rows have an empty
  title where OCR failed the caption — the ord_no + matched motion still identify them.
- The mayor is a voting member (max council tally 5); linkage here is by number+date only and
  makes no per-member assumption.

## Rebuild (idempotent; additive)
```
python3 build_date_cache.py   # OCR/vision date+title extraction -> date_extractions.csv (slow; ~3 min)
python3 build_index.py        # join to all_votes.csv -> index.csv + citations_without_document.csv (fast)
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .   # PASS
```
`build_index.py` reads the cached `date_extractions.csv` (no re-OCR); rerun
`build_date_cache.py` only if `raw/` changes. Manual oversize/vision dates are encoded as
`SUPP` in `build_date_cache.py`.

as-of 2026-07-06.
