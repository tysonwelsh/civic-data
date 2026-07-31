# housing_plans/ — White City moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: White City's **General Plan** + its **Moderate
Income Housing (MIH) element/plan** and adopting ordinance (Utah Code 10-9a-403/408, HB 462 2022),
plus the **state HCD annual reporting** record. Purely **additive** — no existing White City
dataset was touched, and the parent `README.md`/`CLAUDE.md` are the orchestrator's to edit, not
this folder's. As-of 2026-07-13.

## Headline
White City is **NOT honest-empty and NOT below the reporting threshold.** It has a standalone
adopted MIH Plan (2022 FINAL, updated from a 2019 Housing Element / 2020 plan) and **files a
10-9a-408 report under its own name every state year checked** (SB34 2019–2021, RY 2023/2024/2025).
Long-range planning is **staffed by the Greater Salt Lake MSD**, so the plan/ordinance live on
`msd.utah.gov`, but the **entity of record in the state compilations is "White City"** — it is not
absorbed under an MSD umbrella entry. See `AVAILABILITY.md` (READ FIRST) for the per-year table.

## Layout
```
raw/    9 PDFs: 5 fetched here (GP + MIH plan + MIH ordinance + 2019 notice + retained timeline)
        + 4 sha256-verified COPIES of the shared statewide HCD compilations (+ _fetch_log.jsonl)
text/   8 sidecars: 4 city/MSD docs + 4 state-compilation White City excerpts
index.csv         §9 housing contract header (8 rows)
AVAILABILITY.md   per-year presence/absence + threshold/MSD-reporting status (READ THIS FIRST)
wc_hcd_pagerange.py   in-folder helper: locate White City's page range in an HCD compilation + extract sidecar
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` (1) | `mih_element` (3) | `mih_annual_report` (4). No `compliance_letter`
  (White City publishes none — honest absence).
- `date` = adoption date (city/MSD docs) / filing-or-report year (state reports).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc PDFs; for the state compilations it is White City's
  **physical (1-based) page range within the compilation** (the raw file is the full statewide PDF).
- `format`: `text` (born-digital) for 7 rows; `scanned` for the 2019 OCR'd hearing notice.

## Two source families
1. **City / MSD.** White City = tiny **Streamline** CMS (`whitecity.utah.gov`, Cloudfront `/files/<hash>/`;
   mirror `whitecity.specialdistrict.org`). MIH long-range planning is **GSL-MSD-staffed**, so the
   **standalone MIH Plan (View/673) + adopting ordinance (View/1200)** live on `msd.utah.gov`
   (CivicPlus DocumentCenter, discovered via `msd.utah.gov/446/Moderate-Income-Housing-Plan`), and
   the GP + 2019 hearing notice on the city Streamline site. The MIH element exists as **BOTH the GP
   Appendix C AND a standalone plan+ordinance** — not only buried in the 190-page GP.
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. No per-city file;
   White City's excerpt lives inside each compilation, bracketed by the next alphabetical city
   (**Woods Cross**) and extracted to `text/white_city-<year>.txt` (bleed-verified).

## Provenance of the state HCD compilations (do NOT re-download)
The 4 `hcd-*.pdf` in `raw/` are **byte-identical sha256-verified copies** of
`bluffdale_city_council/housing_plans/raw/{hcd-23reports,hcd-24reports,hcd-25reports,hcd-sb34}.pdf`
(these are shared statewide PDFs, one per state, not city-specific). sha256:
- `hcd-23reports.pdf` 8e59bb71…e8ac · `hcd-24reports.pdf` 53f4f9d9…e38f
- `hcd-25reports.pdf` 0b620618…bd6b01 · `hcd-sb34.pdf` 2712503323…e2e00
`raw/_fetch_log.jsonl` carries copy-provenance rows for these 4 with the **true**
`jobs.utah.gov/housing/affordable/moderate/reporting/documents/…` source URL and the original
retrieval timestamps from the bluffdale build (2026-07-13). The `index.csv` `source_url` is the
authoritative jobs.utah.gov URL, re-fetchable.

## Key facts
- White City **present + reporting in every state year** (SB34 2019–2021, RY 2023/2024/2025).
- Three MIH-element vintages: **2019** original Housing Element (hearing notice OCR'd) → **2020**
  plan (cited in RY2025) → **2022 FINAL** standalone MIH Plan (indexed; adopted via ord. 22-09-01).
- All city/MSD PDFs are born-digital text except the 1-page 2019 hearing notice (scanned → OCR).
- Township→city (HB 35, 2024-05-01) creates **no reporting gap**: SB34 files it as "White City,
  Metro Township"; RY2023–2025 as "White City".

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --name <f> <url>`.
- State excerpts: `python3 wc_hcd_pagerange.py raw/hcd-<yy>reports.pdf text/white_city-<year>.txt`
  (finds the page range by "white city" density; verify the auto range against the Woods Cross
  bracket — the 2023/2025 auto-heuristic under-shoots by a page, so the sidecars here were written
  with explicit `<start>..<end>` ranges; see AVAILABILITY.md for the exact spans).
- Sidecars for born-digital docs: `pdftotext -layout raw/<f>.pdf text/<f>.txt`.
- OCR (2019 notice): render page with pymupdf @300dpi → `tesseract <png> <out> --psm 4` (macOS has
  no `timeout` — do NOT wrap tesseract in a shell timeout).
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next `scripts/build_cities_db.py`
  run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: the standalone MIH Plan being MSD-hosted, and the reports being MSD-staffed but
  filed under White City's name, are the correct findings — not gaps to fill.
- Do not edit any existing White City dataset or the parent README/CLAUDE from this folder.
- Do not re-download the HCD compilations (copy from bluffdale); do not delete/normalize `raw/` originals.
