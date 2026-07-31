# housing_plans/ — South Salt Lake moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: South Salt Lake's **General Plan 2040** + its
**Moderate Income Housing (MIH) element** (a General Plan chapter + two standalone MIH Plan
PDFs, 2016 and 2023), plus the **state HCD annual reporting** record (Utah Code 10-9a-403/408,
HB 462 2022). Purely **additive** — no existing SSL dataset was touched. As-of 2026-07-13.

## Layout
```
raw/    8 born-digital PDFs verbatim (+ _fetch_log.jsonl provenance)
text/   pdftotext -layout sidecars: 4 city docs + 4 state-compilation SSL excerpts
index.csv         §9 housing contract header (8 rows)
AVAILABILITY.md   what filed / not filed, how verified (READ THIS FIRST)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` | `mih_element` | `mih_annual_report` | `compliance_letter`.
  (`compliance_letter` has **0 rows** — SSL posts no HCD compliance letter; see AVAILABILITY.md.)
- `date` = adoption date (city docs) / filing-or-report year (state reports).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc city PDFs; for the state compilations it is SSL's
  **physical page range within the compilation** (the raw file is the full statewide PDF).
- `repository` = "South Salt Lake (sslc.gov DocumentCenter)" or "Utah DWS HCD (jobs.utah.gov)".

## Two source families
1. **City** (`sslc.gov`, CivicPlus / CivicEngage Central; `/DocumentCenter/View/<id>`).
   Discovered via `sitemap.xml` → the `/519/Housing-Resources` page (holds the General Plan
   2040, the 2016 MIH Plan, the 2023 MIH Plan & Needs Assessment). The `/522/Moderate-Income-
   Housing` page is **narrative only, no doc links** — SSL's MIH element is a **chapter of the
   General Plan** (Implementation Strategy, cites 10-9a-403) plus **two standalone MIH Plan
   PDFs**: the 2016 adopted plan (`View/456`) and the 2023 updated plan/needs assessment
   (`View/1996`). The GP Appendix (`View/312`) was surfaced from the state report's "Link to
   Plan" field.
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. **No
   per-city file exists**; SSL's excerpt lives inside each compilation. These four PDFs were
   **copied sha256-verified from `bluffdale_city_council/housing_plans/raw/`** (identical bytes;
   one statewide download serves every city) — NOT re-downloaded. `index.csv` records the true
   `jobs.utah.gov` `source_url` + original 2026-07-12 `retrieved_date`. SSL page ranges were
   bracketed by the alphabetical neighbors **South Ogden** / **South Weber** and extracted to
   `text/south_salt_lake-<year>.txt`, grep-verified for zero neighbor bleed. See AVAILABILITY.md
   for the page-range table + per-year TOC quirks.

## Key facts
- **South Salt Lake is present in every state filing year** checked (RY 2023/2024/2025 + the
  SB 34 2019–2021 summary) — expected; at ~26k pop. SSL is well above the reporting threshold.
- The MIH element is a **General Plan chapter**, and SSL also maintains a **standalone MIH
  Plan** (adopted 2016-08-11; updated 2023 by James Wood). The 2023 doc is mislabeled on the
  city site as a "Housing Needs Assessment" but is titled "Moderate Income Housing Plan and
  Needs Assessment" — it is the operative current MIH element analysis.
- All 8 PDFs are **born-digital text** (`pdftotext -layout`, `format=text`) — SSL's council-
  minutes coverage cliff / OCR concerns do NOT apply here. The GP Appendix sidecar carries
  benign decorative-glyph control chars from its custom design fonts (narrative + tables are
  clean; see AVAILABILITY.md).

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --batch <urls.csv>`.
- Sidecars: `pdftotext -layout raw/<f>.pdf text/<f>.txt`; state excerpts use `-f <start> -l <end>`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: an honest "SSL posts no compliance letter; the state publishes only
  compilations" is the correct finding, not a gap to fill.
- Do not edit any existing SSL dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals.
