# housing_plans — availability & verification (Riverton City)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing + general plan). **Additive dataset** — nothing in any existing Riverton dataset was
modified.

## What was checked

Two source families, per the skill:

1. **City** (`rivertonutah.gov`, **Revize** CMS). Discovered by crawling
   `https://www.rivertonutah.gov/sitemap.xml` (929 URLs; NOT stale search-result URLs), then
   navigating the **Planning** landing (`/planning/index.php`) and **Planning → Maps**
   (`/planning/maps.php`). Housing/general-plan documents are static files under
   `/departments/planning/documents/…` (Revize serves them via `cms8.revize.com/rivertonut/…`).
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. Annual reports are
   **statewide compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`), plus the
   `sb34.pdf` SB 34 Municipal Progress Summaries (2019–2021).

## What was retrieved (8 index rows, 8 raw PDFs)

### City documents (4 PDFs)
- **General Plan / Land Use Map** — single-page large-format Land Use Element map
  (`general-plan.pdf`, 1 pp). Printed "AMENDED AUGUST 18, 2020", "Revision 3-8-22". The city
  publishes its General Plan **as this land-use map** (the Maps page links it as "Riverton City
  General Plan / Land Use Map"); there is no separately-posted narrative general-plan document.
- **MIH element** — **Moderate Income Housing Implementation Plan 2020-2024**
  (`riverton-city-annual-moderate-income-housing-plan-2024.pdf`, 6 pp). The strategies matrix
  (statutory strategy (E)/(F)/(G) × City Goals × Implementation Actions × Timing), linked from
  the Planning page as "the Moderate Income Housing Plan approved by the Riverton City Council".
- **Annual MIH reports 2020 & 2021** — Utah DWS-HCD 899 Annual Moderate-Income Housing
  Reporting Forms (`…report-2020.pdf`, 11/16/2020, 55 pp; `…report-2021.pdf`, 11/15/2021, 55 pp).
  City-published copies of the 10-9a-408 implementation reports.

### State HCD compilations (4 PDFs — Riverton present in ALL of them)
Each statewide compilation is a **local copy** of the sha256-verified files already fetched by
the Bluffdale build from `jobs.utah.gov` on 2026-07-13 (copied, **NOT re-downloaded** — see
CLAUDE.md). Riverton's page range was located in each (bracketed by neighbors Riverdale/Roy) and
extracted to a `text/` sidecar, then grep-verified for **zero neighbor-city bleed**:

| Compilation | Total pp | Riverton (physical) pp | Bracket | Sidecar |
|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | 610–616 (printed 609; printed=physical−1) | Riverdale ← / Roy → p617 | `text/riverton-2023.txt` |
| `24reports.pdf` (RY 2024) | 1030 | 577–583 (content-scan; TOC printed nums exceed physical) | Roy city → p584 | `text/riverton-2024.txt` |
| `25reports.pdf` (RY 2025) | 1303 | 731–740 (printed 728; offset +3) | Riverdale ← / Roy → p741 | `text/riverton-2025.txt` |
| `sb34.pdf` (SB 34 2019–2021) | 199 | 118 | Riverdale p117 / Roy p119 | `text/riverton-sb34-2019-2021.txt` |

**Riverton is present and reporting in every filing year checked** (2020, 2021 city-filed; 2023,
2024, 2025 statewide compilations; 2019–2021 SB 34 progress summary). The absence of a
*standalone per-city report file* on the state site is **expected** (the state publishes only
statewide compilations), NOT a gap. Riverton is **"with a major transit investment corridor"**
(SB 34 summary), 3 required + 3 menu MIH strategies.

## What is NOT available / honest gaps

- **Original October-2019 MIH element PDF** (`…/documents/moderate-income-housing-plan.pdf`) —
  **not recoverable in complete verbatim form.** The live URL now **404s** (superseded by the
  2020-2024 implementation plan). The only Internet-Archive `200` capture (2021-05-18) comes
  from a **Common Crawl WARC that truncates response bodies at exactly 1 MiB**
  (`x-archive-orig-content-length: 1048576`), yielding a corrupt PDF (broken xref/trailer) — not
  a usable original, so it was **not retained**. All other Wayback captures are 301/302
  redirects. Its content is substantially reflected in the 2020/2021 annual reports (which cite
  the Oct-2019 adoption) and the 2020-2024 implementation plan (retained). Logged, not filled.
- **RY 2019 / RY 2022 city-filed annual reports** — the city posts only the 2020, 2021 forms and
  the 2020-2024 implementation plan on the current Planning page; `…report-2022/2023/2024/2025.pdf`
  HEAD-probe to `Content-Length: 0` (not published at those slugs). RY 2022 and later are covered
  by the **state compilations** (23/24/25reports.pdf) instead. Not an honest gap for those years.
- **No separate narrative General Plan document** — the city's General Plan is published as the
  single-page Land Use Map. Not a scraper miss.

## Extraction & verification method

- All 8 raw PDFs are **born-digital** (text layer present; `pdftotext -layout` yields clean text
  — no OCR needed). `extraction_method = pdftotext -layout`, `format = text` for every row.
- City PDFs fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged) — provenance
  in `raw/_fetch_log.jsonl` (HTTP 200, `application/pdf`). The 4 HCD compilations are byte-identical
  local copies (sha256 recorded, original jobs.utah.gov URL + retrieved_utc preserved in the log).
- Corpus screened with `audit-city-data/scripts/screen_corpus.py`: **0 cid/replacement/PUA/
  mojibake/long-token/stub/short/duplicate outliers, 0 dict-ratio outliers, 0 split-word outliers,
  0 weird-char outliers, 0 read errors** across 8 sidecars. The advisory `hyphen_breaks`,
  `repeated_line`, and `ends_mid` flags are expected artifacts of the DWS-HCD web-form report
  layout (repeated field labels, hyphenation) and page-range excerpts — not extraction defects.
- Each state-compilation sidecar was grep-verified to contain "Riverton" and **zero** neighbor-city
  header strings (Riverdale / Roy).
