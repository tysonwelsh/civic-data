# Housing plans — availability & gap log

**As-of:** 2026-07-03 · **Source 2 of `expand-city-sources`** (moderate-income housing plans + annual reports + General Plan) · West Jordan City, Salt Lake County, Utah.

## What exists and was retrieved (11 docs)

### General Plan (city)
- **2023 General Plan** (current adopted) — `raw/city-2023-general-plan.pdf`, 125 pp, born-digital.
  Adopted by **Ordinance 23-10** (PC recommended 6-0 2023-02-07; council hearings 2023-03-08 &
  2023-06-14). Retained the **adoption ordinance** and the **Future Land Use Map** (60x36 poster,
  32 MB image-only) too.
- The **online codified General Plan** also lives on American Legal
  (`https://codelibrary.amlegal.com/codes/westjordanut/latest/westjordan_genplan/...`). That host is
  **403 bot-protected** (polite GET returns 403; SKILL-documented for amlegal) and is
  current-consolidated-text only — the adopted 2023 PDF above is the authoritative primary, so the
  amlegal copy is not separately archived.

### Moderate Income Housing element (city)
- **Ordinance 20-32** (2020-09-30) adopting the MIH plan into the General Plan —
  `raw/city-moderate-income-housing-plan.pdf` (the "Moderate Income Housing Plan" link on the city
  Affordable Housing page).
- **Current published MIH element** (uploaded 2026-04) —
  `raw/city-moderate-income-housing-plan-2026.pdf`. Narrative mirrors the 2020 element (same
  population/AMI figures); treated as the current published copy, not evidence of a re-adoption.

### MIH annual implementation reports
- **City-published, 2020 only:** the 2020 Utah MIH Reporting Form
  (`raw/city-moderate-income-housing-report.pdf`, reporting date 2020-11-18) + **Resolution 20-73**
  accepting it for state submittal (`raw/city-housing-report-resolution.pdf`).
- **State compilations (Utah DWS/HCD), 2023 / 2024 / 2025:** the annual reports are published as
  **statewide compilation PDFs**, not per-city files
  (`.../reporting/documents/{23,24,25}reports.pdf`). West Jordan's section was sliced from each and
  saved as a `text/westjordan-<year>.txt` sidecar. **West Jordan confirmed present in all three.**
  Page ranges (bracketed by the next jurisdiction; neighbor-bleed grep = 0 for each):
  - 2023 → pp. **1044–1059** of 1109 (prev West Haven; next West Point p.1060)
  - 2024 → pp. **968–989** of 1030 (prev West Haven; next West Point p.990)
  - 2025 → pp. **1224–1248** of 1303 (prev West Bountiful/West Haven; next West Point p.1249)
- **SB 34 progress summary** (`.../documents/sb34.pdf`): WJ = pp. **189–191** of 199 (prev
  Smithfield; next West Point p.192; bleed = 0). SB 34 (2019) strategy tracker showing
  2020 (required & submitted) / 2021 rows.

## Gaps / what was checked and NOT found

- **No standalone city-published MIH annual reports for 2021, 2022, 2023, 2024, 2025.** The city
  Affordable Housing page publishes only the **2020** report + resolution. West Jordan's post-2020
  annual implementation reporting is captured **only inside the state statewide compilations**
  (2023/2024/2025 above). This is the expected Utah pattern (municipalities file to HCD; HCD compiles),
  not a scraper miss. Earlier statewide compilations (e.g. `21reports.pdf`/`22reports.pdf`) were not
  pursued — the SKILL's verified-stable set is 23/24/25 + sb34, and the city's own 2020 form covers the
  earliest year.
- **No `compliance_letter`** (state notice of compliance / non-compliance to West Jordan) was located
  as a standalone public document. Compliance status is embedded within the state compilations
  (e.g. the 2024 compilation notes "West Jordan City did not meet benchmark guidelines for this
  strategy…" per-strategy). doc_type `compliance_letter` therefore has **0 rows**.
- **2012 General Plan** (superseded) exists at
  `.../wp-content/uploads/2021/09/APPROVED-2012-GENERAL-PLAN.pdf` but was **not archived** — scope is
  the *current* adopted plan (2023). Noted here for completeness.

## Discovery method
- Crawled `sitemap.xml` → `sitemap_index.xml` → `page-sitemap.xml` / `post-sitemap.xml` first (per
  SKILL: search-cached URLs go stale). City docs found via the **Affordable Housing** page
  (`/community-development/affordable-housing/`) and **Master Plans** page
  (`/community-development/master-plans/`). The current 2023 General Plan PDF (not linked as a PDF on
  those pages — the "General Plan" link points to amlegal) was located via targeted web search and
  confirmed on the city's own `wp-content/uploads/2023/08/` host.
- All fetches via `scripts/polite_fetch.py` (logged in `raw/_fetch_log.jsonl`), `--now 2026-07-03T00:00:00Z`.

## Extraction caveats
- **2023 General Plan** — the designed page layout causes `pdftotext` to insert letter-spacing inside
  many words ("We st Jo rd a n", "me d ia n a g e"). Text is legible and NOT hallucinated, but the
  screener flags low dict_ratio / split-word rate for this file. **Use `raw/city-2023-general-plan.pdf`
  for authoritative quoting.**
- **Future Land Use Map** — image-only (no text layer); read via the raw PDF / vision.
- `screen_corpus.py` on `text/`: no mojibake / stubs / duplicate bodies / read errors. `repeated_line`
  and `ends_mid` advisories are expected (form headers repeat; excerpts end mid-page).
