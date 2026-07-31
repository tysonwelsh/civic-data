# summit_county/plans — how to use this module

The **governing planning documents** for unincorporated Summit County's **two planning
districts** (Snyderville Basin + Eastern Summit County) and its statutory
**Moderate-Income-Housing (MIH)** plans, as a **searchable plain-text corpus** for
growth / housing / development questions. Self-contained: raw PDFs, extracted/OCR'd text,
a manifest. Nothing here feeds gov.db/cities.db — it is a document layer.

## Layout

- `raw/<stem>.pdf` — source PDF (all <=50 MB, all retained).
- `text/<stem>.txt` — extracted text of **every** document (10/10). Born-digital via
  `pypdf`; the scanned MIH ordinances via **tesseract OCR**. **This is the searchable
  layer — read/grep these.**
- `index.csv` — the manifest. Columns:
  `doc_type,title,adopted_date,jurisdiction,path,text_path,format,source_url,notes`.
- `SOURCES.md` — provenance, OCR method, and honest gaps.

## Which document for which question

- **Basin growth vision / land use (west, around Park City):**
  `snyderville_basin_general_plan_2015` (adopted Ord 839). Note the Basin's **20%
  inclusionary-zoning** affordable set-aside (implemented in Title 10, see `ordinances/`).
- **East Side growth vision (Coalville/Kamas/Oakley/Henefer/Francis surrounds):**
  `eastern_summit_county_general_plan_2023`.
- **Moderate-income / affordable housing obligations & strategies (HB462, 2022):**
  `snyderville_basin_mih_plan_ord950_2022` (Basin), `eastern_summit_mih_plan_ord951_2022`
  (East Side), then the amendments `mih_plan_amended_ord962_2023`, `mih_plan_ord968_2023`,
  `mih_plan_ord980_2024` (most recent).
- **Annual MIH reporting / state compliance:** `mih_plan_updates_2023`,
  `mih_notice_of_compliance_2022`, and `mih_udws_noncompliance_notice_2023` (Utah DWS found
  the 2023 report NON-COMPLIANT — an honest finding).

## Two planning districts (read this first)

Summit County plans unincorporated land as **two districts, each with its own General Plan
AND its own Development Code** (Basin = Title 10; Eastern = Title 11 — both in the
`ordinances/` module). A **joint GP committee (2024)** is harmonizing them; a comprehensive
Basin GP update is **in progress, not adopted** — the 2015 Basin GP still governs.

## Cardinal rules (inherited from repo root)

- **Never fabricate.** `index.csv` lists only documents actually retrieved with a live
  `source_url`. Missing/undrafted plans (the un-adopted Basin GP update; small-area plans)
  are **honest gaps** in `SOURCES.md`, not invented rows.
- **OCR uncertainty is disclosed, not hidden.** Several MIH ordinance adoption dates are
  OCR-inferred (only Ord 951's 2022-09-19 is clean) — noted per-row; the PDF is canonical.
- **Text is derived; PDFs/URLs are canonical.** Regenerate born-digital text with `pypdf`;
  the scans need tesseract OCR (`pdftoppm -r 300` → `tesseract --psm 1`). See SOURCES.md.

## Cross-module note

The MIH ordinances here (950/951/962/968/980) and the GP-adopting Ord 839 are also listed
in `summit_county/ordinances/index.csv` (with blank `path`, pointing back to this module)
so the adopted-ordinance catalog stays complete without duplicating bytes.
