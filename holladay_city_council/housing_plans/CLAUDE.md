# housing_plans/ — Holladay moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Holladay's **General Plan ("Holladay Horizons"
2025)** + its **Moderate Income Housing (MIH) element** and adopting resolution (Utah Code
10-9a-403/408, HB 462 2022), plus the **state HCD annual reporting** record. Purely
**additive** — no existing Holladay dataset was touched. As-of 2026-07-13.

## Layout
```
raw/    11 PDFs verbatim (10 born-digital text + 1 scanned) (+ _fetch_log.jsonl provenance)
text/   11 sidecars: 7 city docs + 4 state-compilation Holladay excerpts
index.csv         §9 housing contract header (11 rows)
AVAILABILITY.md   what filed / not filed, how verified (READ THIS FIRST)
CLAUDE.md         this file
build_index.py            regenerates index.csv (reproducible)
find_holladay_pages.py    helper: dump per-page headers of a compilation
find_city_boundary.py     helper: find physical pages containing a needle (city bracketing)
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` (3) | `mih_element` (3) | `mih_annual_report` (5). No
  `compliance_letter` — Holladay does not post a standalone HCD Notice-of-Compliance letter
  (honest absence, see AVAILABILITY.md).
- `date` = adoption date (city plan/resolution) / filing-or-report year (state reports).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc city PDFs; for the state compilations it is Holladay's
  **physical page range within the compilation** (the raw file is the full statewide PDF).
- `format=scanned` + `extraction_method=ocr` on Resolution 2025-02 only; all others
  `format=text` / `pdftotext -layout`.

## Two source families
1. **City** (`holladayut.gov`, **Revize** CMS; `Document Center/…` served from
   `cms3.revize.com/revize/cityofholladay/`, reachable via `holladayut.gov` 302). The MIH
   element exists in THREE captured forms:
   - **Appendix F of the 2025 General Plan Appendices** — the current in-plan MIH element.
   - **Chapter 5: Moderate Income Housing Plan** — the city's standalone MIH element (amended
     through March 2024), the doc the housing page links.
   - **Resolution No. 2025-02** (2025-03-20) — the signed resolution adopting the amended MIH
     Plan (Exhibit A). **Scanned/OCR.**
   Plus the historical **2019 Update Summary** (prior plan) and the **city-filed 2024 annual
   report**.
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. **No
   per-city file exists**; Holladay's excerpt lives inside each compilation. These 4 raws were
   **copied sha256-verified from `bluffdale_city_council/housing_plans/raw/`** (identical
   statewide files) — NOT re-downloaded; `index.csv`/`_fetch_log.jsonl` record the true
   `jobs.utah.gov` `source_url` and the original 2026-07-13 retrieval. Page ranges were bracketed
   by the next alphabetical city (**Hooper**) and extracted to `text/holladay-<year>.txt`,
   grep-verified for zero neighbor bleed. See AVAILABILITY.md for the page-range table and the
   per-year TOC-offset quirks (esp. 2024: TOC printed ≈ 2× physical → content-scanned).

## Key facts
- **Holladay is above the state MIH reporting threshold → present and reporting in every state
  filing year** (RY 2023/2024/2025 + SB 34 2019–2021).
- The current General Plan is **"Holladay Horizons" (2025 General Plan)**, adopted **Nov 2025**
  (per Holladay Journal; the plan text prints no exact adoption day — `date=2025-11`, honest
  precision noted). It **supersedes the 2016-2031 plan**. The MIH element is its **Appendix F**.
- The 2024 state-compilation excerpt is the state copy of the city-filed 2024 report; both
  retained deliberately (see AVAILABILITY.md "Provenance note").
- 10/11 PDFs are born-digital text; **Resolution 2025-02 is the only scan** (OCR sidecar).

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --batch <urls.csv>`.
- Sidecars: `pdftotext -layout raw/<f>.pdf text/<f>.txt`; state excerpts use `-f <start> -l <end>`
  (ranges from `find_city_boundary.py`); the scanned resolution used `pdftoppm -r 200 -png` →
  per-page `tesseract … --psm 6`.
- Rebuild index: `python3 build_index.py`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: "no standalone HCD compliance letter posted" and "state publishes only
  statewide compilations" are correct findings, not gaps to fill.
- Do not edit any existing Holladay dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals, and do not "correct" the benign Word non-breaking
  hyphens in the 2016-plan sidecar or the OCR artifacts in the resolution sidecar.
