# housing_plans — Orem City General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-05.**

## What this is

Orem's land-use / housing planning record, from two repositories:
1. **City of Orem** (WordPress site `orem.gov`, documents at `orem.gov/wp-content/uploads/`) — the
   current adopted **General Plan (2023 Update)** whose **Chapter 4 (Housing) IS the Moderate Income
   Housing element**, the **2018 Moderate-Income Housing Study** behind it, the MIH/reporting landing
   page, and Orem's **2025 FrontRunner Station Area Plan** with its adopting resolution and the HB 462
   **determinations of impracticability** for the UVX transit stations.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Orem files with the state, as published in HCD's statewide compilations (2023 / 2024 / 2025), plus
   the SB 34 2019–2021 progress summary.

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies (from a statutory menu) giving a "reasonable opportunity" for
  households at **≤ 80% of county AMI** to live in the city. **Orem's element is General Plan Chapter 4
  (Housing), sec. 4.4.2.**
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD. HCD reviews (does not audit) the self-reported data.
- **HB 462 (2022)** strengthened these and, for cities with fixed-guideway transit, requires
  **Station Area Plans** (Utah Code § 10-21-203) or, where infeasible, a **resolution of
  impracticability**. Orem sits on FrontRunner + UVX (Utah Valley Express BRT); its 2025 record
  includes a FrontRunner SAP plus impracticability determinations for the Main Street, University
  Place, and Lakeview UVX stations.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — the **Orem General Plan (2023 Update)** (born-digital PDF, 93 pp). Its MIH element
  is Chapter 4.
- **mih_element** — the 2018 **Moderate-Income Housing Study**, the `orem.gov/housing` landing page,
  the **FrontRunner SAP Report** (Exhibit A, 2025-12-08), and **Resolution R-2025-0021** adopting it.
- **mih_annual_report** — HCD statewide compilations for report years **2023 / 2024 / 2025** (Orem's
  filing is a page-range within each — see below).
- **compliance_letter** — HCD **SB 34 Progress Summaries 2019–2021** (Orem = PDF pp. 95–96), the **MAG
  SAP Policy Committee certification** of Orem's impracticability findings, and the three UVX
  **determination-of-impracticability** resolutions (**R-2025-0023 / -0024 / -0025**). HCD issues no
  per-city compliance letter; these are the closest published artifacts.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- City site is **WordPress**: `orem.gov/sitemap.xml` is an index → `wp-sitemap-posts-page-1.xml` lists
  the pages; documents live under `orem.gov/wp-content/uploads/<YYYY>/<MM>/`. The **old
  `orem.org/wp-content/uploads/2023/02/…` upload tree is dead** after the CMS migration (see
  `AVAILABILITY.md`: R-2023-0004 is unrecoverable).
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- **Born-digital** city PDFs (General Plan, MIH Study, FrontRunner SAP Report) and all state
  compilations → full / page-range `pdftotext -layout` sidecars in `text/`.
- **Scanned** signed resolutions (R-2025-0021 / -0023 / -0024 / -0025, the MAG certification, the
  signed impracticability certification) → **OCR** via `tesseract` 5.5 (`pdftoppm -r 300` per page),
  sidecars named `*.ocr.txt` and `extraction_method=ocr-tesseract` in `index.csv`.
- State compilations → **Orem page-range** sidecars only (`text/orem-<year>-mih-annual-report.txt`,
  `text/orem-sb34-2019-2021-progress.txt`); full compilations retained verbatim in `raw/`.
- `screen_corpus.py` on `text/` → **clean**: 0 cid / 0 PUA-garbled / 0 mojibake; dict_ratio median
  0.76. Advisory flags only (repeated gov header/footer lines; page-range extracts end mid-sentence;
  the short OCR resolutions show a higher split-word rate — normal for OCR of signed forms).

## Caveats

- **The MIH element is not a stand-alone document.** It is **Chapter 4 of the General Plan** (sec.
  4.4.2). Cite the General Plan PDF / its sidecar, not a separate element file.
- **State "annual report" = statewide compilation**, not a stand-alone Orem PDF. Cite the page range;
  the full compilation is authoritative.
- **2023 compilation boundary bleed:** Ogden's feedback paragraph bleeds into the top of Orem's first
  page in `text/orem-2023-mih-annual-report.txt` (alphabetization/boundary bleed). Orem's own content
  begins a few lines down (the General Plan / R-2023-0004 references).
- **R-2023-0004** (the resolution that adopted the MIH strategies, 2023-01-09) is referenced but its
  PDF is **dead post-migration** — a recorded gap, not fabricated.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- **General Plan 2023 amendment (Council 2023-01-09, R-2023-0004)**, **FrontRunner SAP adoption
  (R-2025-0021)** and the **impracticability resolutions (R-2025-0023/-0024/-0025)** are joinable to
  `meeting_minutes/all_votes.csv` and `planning_commission/` by date.
- Orem's state filer of record is **Grant Allen, Senior Planner (grallen@orem.gov)**.
