# housing_plans/ — Cottonwood Heights moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Cottonwood Heights' **General Plan** + its
**Moderate Income Housing (MIH) / "Affordable Housing" element** and adopting resolutions (Utah
Code 10-9a-403/408, HB 462 2022), the city's **annual implementation reports**, plus the **state
HCD annual reporting** record. Purely **additive** — no existing CH dataset was touched. As-of
2026-07-13.

## Layout
```
raw/    12 PDFs verbatim (+ _fetch_log.jsonl provenance)
        - 8 city docs (6 born-digital + 2 image-only signed/resolution scans)
        - 4 state HCD statewide compilations (sha256-copied from bluffdale, NOT re-downloaded)
text/   sidecars: 6 pdftotext city docs + 2 tesseract-OCR city scans
        + 4 state-compilation Cottonwood Heights excerpts
index.csv         §9 housing contract header (12 rows)
AVAILABILITY.md   what filed / not filed, how verified (READ THIS FIRST)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` | `mih_element` | `mih_annual_report` | (`compliance_letter` — none
  found for CH; see AVAILABILITY.md).
- `date` = adoption/resolution date (city docs) / filing-or-report year (state reports).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc city PDFs; for the state compilations it is CH's
  **physical page range within the compilation** (the raw file is the full statewide PDF).
- `repository` = "Cottonwood Heights (cottonwoodheights.utah.gov CivicEngage)" or "Utah DWS HCD
  (jobs.utah.gov)".

## Two source families
1. **City** (`cottonwoodheights.utah.gov`, Granicus/CivicPlus CivicEngage; `/home/
   showpublisheddocument/<id>/<token>`). The edge **403s bare UAs** — all fetches used
   `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py` (browser header set the
   recon documents). Discovered via `sitemap.xml` → the **Adopted & Special Plans** and **General
   Plan Update** community-development pages. CH's MIH element exists as a chain of "Affordable
   Housing Report" versions (2019 base → 2022 amendment → 2025 five-year update) plus its adopting
   **Resolutions 2023-02 and 2025-51** and the 2020/2021/2022 annual reports.
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. There is **no
   per-city file**; CH's excerpt lives inside each compilation. The four PDFs are byte-identical
   to bluffdale's copies (statewide docs) — **sha256-verified and copied in, not re-fetched**,
   with the true `jobs.utah.gov` provenance carried over. CH's page range was bracketed by the
   next alphabetical city (**Draper**) and extracted to `text/cottonwood_heights-<year>.txt`,
   grep-verified for zero neighbor bleed. Page-range table + per-year TOC quirks in AVAILABILITY.md.

## Key facts
- **CH is present and reporting in every state filing year checked** (RY 2023/2024/2025 + SB 34
  2019–2021). "Without a fixed guideway transit station."
- The city's MIH element is titled **"Affordable Housing Report"** (GSBS Consulting), not
  "Moderate Income Housing Element" — the `mih_element` docs use CH's verbatim titles.
- **Two city PDFs are image-only** (the signed Resolution 2023-02 scan, doc 6888; the Resolution
  2025-51 scan, doc 10101) → `format=scanned`, `extraction_method=tesseract OCR`. Every other
  raw file is born-digital text (`pdftotext -layout`).
- The **2025 five-year updated plan** was adopted by Resolution 2025-51 (1 July 2025) after a
  4 June 2025 PC hearing — doc 10101 is the resolution; the plan itself is annexed (not separately
  published at that doc id).

## Regenerating / extending
- City raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --name <name> <showpublisheddocument-url>` (needs the browser headers polite_fetch sends).
- Born-digital sidecars: `pdftotext -layout raw/<f>.pdf text/<f>.txt`.
- Scanned sidecars: `pdftoppm -r 200 -png` per page → `tesseract … stdout`.
- State excerpts: `pdftotext -layout -f <start> -l <end> raw/hcd-<n>reports.pdf text/cottonwood_heights-<year>.txt`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: an honest "no city-posted HCD compliance letter" and "state publishes only
  compilations, no per-city file" are the correct findings, not gaps to fill.
- Do not edit any existing CH dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals, and do not re-download the `hcd-*.pdf` compilations
  (byte-identical shared statewide PDFs, sha256-verified).
