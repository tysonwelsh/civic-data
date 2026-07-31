# summit_county / plans — sources & provenance

The **governing planning documents** for unincorporated Summit County (two planning
districts) and its statutory **Moderate-Income-Housing (MIH)** plans, as a searchable
plain-text corpus for growth / housing / development questions. Self-contained: raw PDFs,
extracted/OCR'd text, and a manifest. Nothing here feeds gov.db/cities.db.

Built 2026-07-20. Every row verified live against its `source_url` on that date.

## Publisher

All documents come from **Summit County's CivicPlus DocumentCenter**
(`summitcountyutah.gov/DocumentCenter/View/<id>/...`), except the UDWS non-compliance
notice, which the county also hosts there. Landing pages:
- General Plans: <https://www.summitcountyutah.gov/2475/General-Plans>
- Snyderville Basin GP update: <https://www.summitcountyutah.gov/2517/Snyderville-Basin-General-Plan-Updates>
- Eastern GP update: <https://www.summitcountyutah.gov/2516/Eastern-Summit-County-General-Plan-Updat>
- Moderate-Income Housing Plans: <https://www.summitcountyutah.gov/2470/Moderate-Income-Housing-Plans>

## Two planning districts (important context)

Summit County plans its unincorporated land as **two separate districts, each with its own
General Plan and its own Development Code**:
- **Snyderville Basin** (west, around Park City) — Basin GP + Title 10 code; uses
  **inclusionary zoning (20% affordable set-aside)**.
- **Eastern Summit County** (east, around Coalville/Kamas/Oakley/Henefer/Francis) —
  Eastern GP + Title 11 code.
A **joint General Plan committee (2024)** is harmonizing the two; a comprehensive Basin GP
update is in progress but **not yet adopted** (only visioning/engagement summaries exist).

## Retrieval & text method

- PDFs fetched with `curl -L` from the DocumentCenter `View/<id>` URLs; all are **<50 MB**
  so every raw PDF is retained (largest is the Basin GP at 14.2 MB).
- **Born-digital** docs (both General Plans, the 2022 Notice of Compliance, the UDWS
  non-compliance notice) → text via `pypdf`.
- The **MIH ordinance/plan scans** (Ord 950, 951, 962, 968, 980, and the 2023 updates
  packet) are **image-only scanned signed ordinances** — `pypdf` returned ~0 chars, so
  they were **OCR'd with tesseract 5.5** (`pdftoppm -r 300` → `tesseract --psm 1`). The
  text is good but carries normal OCR noise; **the PDF is canonical**.

Regenerate born-digital text:

    python3 -c "from pypdf import PdfReader; \
    open('text/<stem>.txt','w').write('\n'.join((p.extract_text() or '') \
    for p in PdfReader('raw/<stem>.pdf').pages))"

## doc_type vocabulary

`general_plan`, `moderate_income_housing`, `moderate_income_housing_report`.
(Open set — extend if new types are added.)

## HONEST GAPS

- **MIH ordinance adoption dates are partly OCR-inferred.** The scanned signature blocks
  read cleanly only for **Ord 951** (Enacted 2022-09-19). For **Ord 950** the day is
  OCR-garbled (Sept 2022; recorded as the companion date 2022-09-19 with a note); **968**
  the day is uncertain (Sept 2023); dates for **962/980** were read from the body. All are
  noted per-row; verify against the county's signed register before quoting a precise day.
- **Basin GP comprehensive update — not adopted.** Only engagement/visioning material
  exists (e.g. Basin Engagement Summary, DocumentCenter/View/24741). Not ingested as a plan
  (it is not an adopted plan). The 2015 Basin GP remains the governing document.
- **The MIH plan CONTENT lives inside the adopting ordinances** (950/951 etc.) — there is
  no standalone "MIH plan" PDF separate from the ordinance. Those ordinances are also
  cross-listed in the `ordinances/` module (path blank there, pointing back here).
- **Small-area / community plans** (neighborhood studies, corridor plans) are a logged
  follow-up, not yet ingested.
- The **2023 MIH report was found NON-COMPLIANT by Utah DWS** (see
  `mih_udws_noncompliance_notice_2023`) — recorded as an honest compliance finding, not a
  plan.
