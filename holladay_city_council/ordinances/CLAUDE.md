# ordinances/ — Holladay adopted ordinances (build notes)

Additive dataset (`expand-city-sources` **Source 3**), built **2026-07-13**. Maps each
adopted **Ordinance YYYY-NN → adoption date → subject → the council motion that passed
it**, so a vote in `../meeting_minutes/all_votes.csv` links to what the ordinance did.
**123 distinct ordinances, 2020-01 → 2026-06.** Regenerate:
`python3 holladay_ord_ocr.py && python3 build_index.py` (idempotent; `build_index.py`
does no network).

## Code host — recorded, NOT mirrored

Holladay's codified code is **American Legal Publishing**
(`https://codelibrary.amlegal.com/codes/holladayut`) — **403 bot-gated, current
consolidated text only**, so per the skill rule it is recorded here and **not scraped**.
The code is current through **Ordinance 2026-06 (passed 2026-05-21)**.

## Three evidence roles (READ THIS)

Holladay is the skill's **"no online ordinance archive"** case, so the **minutes are the
backbone** and independent PDFs upgrade rows where they exist:

1. **Council/RDA/LBA minutes backbone** (`../meeting_minutes/all_votes.csv`, READ-ONLY) —
   **118 ordinance numbers** cited in adopting motions (2020-2026). Numbers are the
   modern `YYYY-NN` form throughout; parsed from `motion`+`result`, normalized to
   zero-padded `YYYY-NN` (source strings preserved in `result`/`title`). One motion per
   number chosen as the adopter (result mentions adopt/approve/pass; latest date).
2. **Recorder-certified adopted-ordinance PDFs** (independent full text) — **21 PDFs**
   from the live Revize **Document Center** (`holladayut.gov/Document Center/Ordinances/`
   + `.../Departments/City Recorder/2026 Ord Adopt/`), linked off the Recorder's
   current-year-only "Adopted Ordinances" page. Stored `raw/docs/<num>__<origname>.pdf`.
   **15 are wet-signature scans → tesseract OCR @300dpi** (`--psm 6`); 6 are born-digital
   → `pdftotext -layout`. Text sidecars in `text/<stem>.txt`, method per row in
   `text/_extraction_log.csv`. OCR noise preserved (`20"` for `20th`).
3. **PMN (body 388) + Wayback** — checked, **yielded no independent adopted-ordinance
   archive** (PMN attaches minutes + staff-report/draft handouts, not certified
   summaries; Wayback holds only current-year snapshots). Discovery artifacts retained:
   `raw/pmn/council_notices_list.html` (cumulative 884-notice list), the 2 ordinance
   notices, `raw/_wb_*` , `raw/_adopted_ordinances_page.html`. See `AVAILABILITY.md`.

## Linkage rubric (`match_confidence`)

- **high** (14) — an independent Recorder PDF exists AND a council motion cites the same
  number, with no number/date conflict.
- **medium** (2) — independent PDF + subject agreement but a wrinkle: **2025-02** (posting
  certificate misprints the number as "2025-03"; header is `ORDINANCE NO. 2025-02`,
  stormwater — city clerical error, verbatim) and **2025-15** (posted as clean 13.84 code
  text with no printed ordinance number; number from the page label). See `linkage_note`.
- **within_source** (102) — witnessed ONLY by the citing motion (no independent doc):
  **high by construction, NOT corroborated.** `format=na`, `path` blank, `source_url` =
  the minutes PDF (`minutes_source`).
- **none** (5) — independent PDF, no matching motion: 2025-06 and 2026-03/04/05/06 (2026
  items post-date the available minutes). Adoption date from each PDF's "PASSED AND
  APPROVED" clause.

**Never forced** — an ordinance number with no independent PDF stays `within_source`; a
PDF with no motion stays `none`.

## adoption_date provenance (`subject_source` + `linkage_note`)

`adoption_date` = the matched adopting-motion date (the vote that adopted it) for every
row with a motion; for the 5 `none` rows it comes from the PDF "PASSED AND APPROVED"
clause (noted in `linkage_note`). `subject_source` ∈ `recorder-pdf` (title from the
Recorder page label / certified PDF) | `motion` (title is the verbatim motion text, for
`within_source` rows).

## Schema

`index.csv` — SCHEMA_SPEC §9 ordinances contract header
(`ordinance_no,adoption_date,date,title,source_url,retrieved_date,format,
extraction_method,path,land_use,result,matched_motion_date,matched_motion_no,
match_confidence`) + extras `subject,subject_source,minutes_source,linkage_note`.
`format` ∈ `text` (born-digital PDF) / `scanned` (OCR) / `na` (within_source, no doc).
`result` is the matched motion's **verbatim** result string (Holladay results are prose,
not tallies). `land_use` = yes/no (rezone/overlay/Title-13/vacation/historic/stormwater/
lighting/WUI = yes). `path` is dataset-relative including `raw/`.

## Rebuild / validate

```
python3 holladay_ord_ocr.py     # (re)extract text sidecars (OCR + born-digital)
python3 build_index.py          # rebuild index.csv from PDFs + motion backbone
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```

Feeds `cities.db` `fts_ordinance` (via the sidecars) + the `ordinance`/`document` catalog
on the next `scripts/build_cities_db.py` run (orchestrator-run; not run here).
