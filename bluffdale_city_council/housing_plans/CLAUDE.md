# housing_plans/ — Bluffdale moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Bluffdale's **General Plan** + its **Moderate
Income Housing (MIH) element** and adopting ordinances (Utah Code 10-9a-403/408, HB 462 2022),
plus the **state HCD annual reporting** record. Purely **additive** — no existing Bluffdale
dataset was touched. As-of 2026-07-12.

## Layout
```
raw/    11 born-digital PDFs verbatim (+ _fetch_log.jsonl provenance)
text/   pdftotext -layout sidecars: 7 city docs + 4 state-compilation Bluffdale excerpts
index.csv         §9 housing contract header (12 rows)
AVAILABILITY.md   what filed / not filed, how verified (READ THIS FIRST)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` | `mih_element` | `mih_annual_report` | `compliance_letter`.
- `date` = adoption date (city docs) / filing-or-report year (state reports / compliance letter).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc city PDFs; for the state compilations it is Bluffdale's
  **physical page range within the compilation** (the raw file is the full statewide PDF).
- `repository` = "Bluffdale (bluffdale.gov DocumentCenter)" or "Utah DWS HCD (jobs.utah.gov)".

## Two source families
1. **City** (`bluffdale.gov`, CivicPlus/CivicEngage; `/DocumentCenter/View/<id>`). Discovered via
   `sitemap.xml` → the `/878/Moderate-Income-Housing`, `/218/Master-Plans`, `/268/Planning`
   pages. The MIH element exists as **BOTH a standalone element PDF AND its adopting ordinances**
   (2022-15 on 2022-09-14; amended by 2023-04 on 2023-01-25), not only as a General Plan chapter.
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. There is **no
   per-city file**; Bluffdale's excerpt lives inside each compilation. Page ranges were bracketed
   by the next alphabetical city (**Bountiful**) and extracted to `text/bluffdale-<year>.txt`,
   grep-verified for zero neighbor-city bleed. See AVAILABILITY.md for the page-range table.

## Key facts
- Bluffdale is **present and compliant in every state filing year** checked (RY 2023/2024/2025 +
  SB 34 2019–2021). No fixed-guideway transit station → 3 MIH strategies accepted.
- All 11 PDFs are **born-digital text** (`pdftotext -layout`, `format=text`) — the Bluffdale
  council-minutes OCR seam does NOT apply here.
- The 2024 state-compilation excerpt is the state copy of the city-filed 2024 report (View/6981);
  both retained deliberately (see AVAILABILITY.md "Provenance note").

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --batch <urls.csv>`.
- Sidecars: `pdftotext -layout raw/<f>.pdf text/<f>.txt`; state excerpts use `-f <start> -l <end>`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: an honest "state publishes only compilations, no per-city file" is the
  correct finding, not a gap to fill.
- Do not edit any existing Bluffdale dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals.
