# housing_plans/ — Murray City (build notes)

Moderate-income housing (MIH) plans + General Plan dataset, built 2026-07-13 by the
`/expand-city-sources` skill (source type 2). §9 contract `index.csv`
(`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`);
raw originals verbatim under `raw/` (+ `_fetch_log.jsonl` for the city fetches), text
sidecars under `text/`. 9 index rows: 2 `general_plan`, 2 `mih_element`,
4 `mih_annual_report` (2023/2024/2025 + SB 34 2019–2021), 0 `compliance_letter`
(honestly absent — see AVAILABILITY.md).

## The Murray shape of the MIH story

- **General Plan 2017** (adopted **2017-03-07**, replacing the 2003 plan) is current.
  Its **Chapter 9** is the MIH element.
- **HB 462 (2022)** forced a Chapter 9 rewrite: the new **Chapter 9 — Moderate Income
  Housing Element** (View/13361, source docx dated 2022-07-21) was adopted by
  **Ordinance 22-29 on 2022-09-20** (Kat Martinez, Council Chair — the same D1
  councilmember in `roster/`; she resigned that December). View/13361 is the exact
  "Link to Plan" URL Murray filed with the state in its 2023 annual report.
- Annual **10-9a-408 implementation reports** exist only in the state's compilation
  PDFs (the city links none, despite its Housing Resources page saying it posts them).
  Murray filed **every year checked**: 2019–2021 (per SB 34 summary), 2023, 2024, 2025
  (in the compilations; filed by Planning Division Manager Zachary Smallwood).

## Acquisition + provenance

- **City documents** (General Plan, Future Land Use Map, Chapter 9, Ordinance 22-29):
  fetched 2026-07-13 from `murray.utah.gov/DocumentCenter/View/<id>` via
  `polite_fetch.py` (browser UA, Referer = the Housing Resources page) — see
  `raw/_fetch_log.jsonl`. Discovery was CMS-navigation (Departments → Community &
  Economic Development → General Plan `/162/` + Housing Resources `/979/`), not search
  URLs; the sitemap.xml is thin (282 URLs) and lists neither page.
- **State compilations** (`hcd-23reports.pdf`, `hcd-24reports.pdf`, `hcd-25reports.pdf`,
  `hcd-sb34.pdf`): **local copies from `bluffdale_city_council/housing_plans/raw/`**
  (identical bytes — sha256 verified against bluffdale's `_fetch_log.jsonl`; original
  polite fetch from `jobs.utah.gov` on 2026-07-12), to avoid re-downloading ~25 MB of
  identical statewide PDFs. `source_url` in index.csv is the true jobs.utah.gov origin;
  `retrieved_date=2026-07-12` is the original fetch date. These files are NOT in this
  dataset's `_fetch_log.jsonl` (that log covers only the four Murray fetches).

## Extraction notes / caveats

- All city PDFs are born-digital **except Ordinance 22-29** (View/17009), a scan —
  its sidecar is **tesseract OCR** (pdftoppm 300 dpi): expect word errors (e.g. the
  signature block OCRs "Kat Martinez" imperfectly). Never quote the OCR text verbatim
  without checking the raw PDF.
- The Future Land Use Map sidecar carries legend/label text only; the map content is
  graphical — use the raw PDF (vision) for spatial questions.
- **Compilation page ranges are physical (1-based PDF) pages**; the 2023 TOC's printed
  numbers are physical−1. Murray brackets: Millcreek before, Nibley after, all years.
  - **2023** (pp 430–440): Murray starts/ends **mid-page**. `text/murray-2023.txt` is
    mechanically trimmed to the Murray section (from the `Murray`/`Type of
    Jurisdiction` header to just before Nibley's) — a boundary trim, no content edits.
  - **2024** (pp 414–422): p422 is a **shared boundary page** (Murray tail + `Nibley
    city` header in parallel columns); `text/murray-2024.txt` keeps it verbatim, so
    the last page carries Nibley-header bleed. The 2024 form layout is two-column and
    `pdftotext -layout` interleaves columns — read for content, not layout fidelity.
  - **2025** (pp 522–533) and **SB 34** (pp 84–85): clean page boundaries, no bleed.
- The 2023 state filing cites the ordinance at DocumentCenter id **13351**; the city's
  Housing Resources page now serves the same ordinance at **17009** (CivicPlus re-upload)
  — same document, different id. Both facts are recorded; the retained copy is 17009.
- `screen_corpus.py` (2026-07-13): 8/8 files clean — no garbling/stubs/dict outliers;
  advisory flags (repeated page-footer lines, hyphen line-breaks in the designed 2017
  plan, mid-sentence-looking tails at page footers) all investigated benign.

## Linkage

- Ordinance 22-29's adoption (2022-09-20, a Tuesday council date) should appear in
  `meeting_minutes/all_votes.csv`; the PC's favorable recommendation preceded it (per
  the ordinance recitals). No formal linkage columns in this dataset (that's
  `ordinances/`); dates + ordinance number are in the index for joining.
- Annual-report years join to the housing/land-use motions of the same year; the 2023
  report narrates specific council actions (e.g. 2023-06-27 text amendments).
