# housing_plans — availability & verification (Holladay)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing Holladay dataset was modified.

## What was checked

Two source families, per the skill:

1. **City** (`holladayut.gov`, **Revize** CMS; static files served from
   `cms3.revize.com/revize/cityofholladay/Document Center/…`, reachable via the canonical
   `holladayut.gov/Document Center/…` URLs which 302 to the Revize host). Discovered by
   navigating the **General Plan** page
   (`/departments/community_development/planning_division/general__plan.php`), the
   **Moderate Income Housing Plan** page
   (`/departments/economic_development/housing/accessory_dwelling_units_-_adu_s.php`), the
   **Housing & Community Resources** index, and the **Moderate Income Housing** page.
   `cityofholladay.com` 301-redirects to `holladayut.gov`, but its **legacy `/file/2023/02/…`
   PDFs are gone (404 on the migrated CMS)** — the current Document Center paths were used.
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. The annual reports are
   **statewide compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`), plus the
   `sb34.pdf` SB 34 Municipal Progress Summaries (2019–2021). Holladay is **above the state
   reporting threshold → present in every compilation.**

## What was retrieved (11 index rows, 11 raw PDFs)

### City documents (7 PDFs)
- **General Plan 2025 ("Holladay Horizons")** — the current adopted plan (`120 pp`,
  `Holladay General Plan 2025_APPROVED.pdf`). Adopted **November 2025** per the Holladay
  Journal (2026-02-02); the APPROVED PDF was re-posted Feb 2026. Acknowledgments list the
  2025 pre-Jan-2026 council (Mayor Dahle).
- **General Plan 2025 Appendices** (`73 pp`) — appendices A–F; **Appendix F IS the current
  Moderate-Income Housing element** (Utah Code 10-9a-403). Bundled with A: Required GP Element
  Matrix, B: Glossary, C: Engagement Summary, D: Implementation Summary Table, E: Small Area
  Plans.
- **General Plan 2016-2031** (`90 pp`, PMN file 1329487) — the prior plan, adopted **July 14
  2016** (Feb-2023 refresh; internal title `General Plan_currentFeb2023`). Land-use/MIH context
  for the RY2023 filing. The city's own linked `General-Plan_currentFeb2023.pdf` now 404s → the
  PMN copy was captured instead.
- **Chapter 5: Moderate Income Housing — 2019 Update Summary** (`18 pp`, PMN file 532759) —
  MIH element/SB 34 update to the 2016 plan (references the 2010 plan reviewed 2013 & 2016 and
  an Oct-2017 MIH Review Report). Historical.
- **Chapter 5: Moderate Income Housing Plan (amended through March 2024)** (`14 pp`) — the
  city's **currently-posted standalone MIH element** (header: *Amended Sept 2022, *Amended Feb
  2023, *Amended March 2024).
- **Resolution No. 2025-02** (`14 pp`, **scanned/image-only → OCR**) — the signed resolution
  **PASSED AND APPROVED 20 March 2025** amending the MIH Plan (Exhibit A = the amended plan).
  Surfaces the adopting instrument the plan page did not otherwise name. (Cf. the skill's CH
  note about the state PDF's "Link to Plan/Ordinance" fields — here the adopting doc was found
  on the city's own housing page.)
- **2024 Moderate Income Housing Report — city-filed copy** (`23 pp`) — Holladay's 10-9a-408
  annual implementation report (RY Aug 2023–Jul 2024; submitted **2024-08-01**; preparer Ann
  Frances Garcia). Distinct artifact from the state-published copy (see below).

### State HCD compilations (4 PDFs — Holladay present in ALL, page ranges bleed-verified)
Each statewide compilation was **copied sha256-verified from
`bluffdale_city_council/housing_plans/raw/`** (the identical statewide files — NOT
re-downloaded; original `jobs.utah.gov` `source_url` + original 2026-07-13 retrieved date
recorded in `index.csv` and `raw/_fetch_log.jsonl`). Holladay's alphabetical page range was
located (bracketed by the next city, **Hooper**) and extracted to a `text/` sidecar, then
grep-verified for zero neighbor-city header bleed:

| Compilation | Total pp | Holladay (physical) pp | Boundary | Sidecar |
|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | 256–263 (printed 255–262) | Hooper p264 | `text/holladay-2023.txt` |
| `24reports.pdf` (RY 2024) | 1030 | 230–250 | Hooper p251 | `text/holladay-2024.txt` |
| `25reports.pdf` (RY 2025) | 1303 | 312–326 (printed 309) | Hooper p327 | `text/holladay-2025.txt` |
| `sb34.pdf` (SB 34 2019–2021) | 199 | 57 (single page) | Hooper p58 | `text/holladay-sb34-2019-2021.txt` |

**Per-year TOC quirks (resolved):** 2023 has no title pages so printed = physical − 1;
**2024's TOC printed page numbers are ~2× physical (Holladay printed 458 → physical 230)**, so
the range was **content-scanned** for the `Holladay city` header, not TOC-derived; 2025's
offset was ~+3. Holladay is **summary #26** in SB 34 (County: Salt Lake, 3 required items).

**Holladay is present and reporting in every filing year checked** (RY 2023, 2024, 2025 annual
reports + the 2019–2021 SB 34 progress summary). The absence of a *standalone per-city report
file* on the state site is **expected** (the state publishes only statewide compilations), NOT a
gap.

## What is NOT filed / not applicable

- **No standalone HCD "Notice of Compliance" letter** was found posted by the city (Bluffdale
  had one; Holladay does not appear to post one). The city posts its MIH Plan, its adopting
  resolution, and the city-filed annual report, but **no compliance_letter row** — recorded as
  an honest absence, not fabricated.
- **No standalone per-city PDF on the state HCD site** — expected; only the statewide
  compilations exist there.
- **Legacy `cityofholladay.com/file/2023/02/…` PDFs are 404** (CMS migration to Revize dropped
  them). The equivalent current documents were captured from the live Revize Document Center and
  from PMN. Not a gap.
- **RY 2022 / earlier annual compilations** are not offered on the current HCD index (earliest
  is `23reports.pdf`); the SB 34 summary covers 2019–2021. HB 462 annual reporting begins RY 2023.

## Extraction & verification method

- 10 of 11 raw PDFs are **born-digital** (`pdftotext -layout`, `format=text`). The lone
  exception is **Resolution 2025-02** (image-only scan, no font layer) → `format=scanned`,
  `extraction_method=ocr (tesseract 5.5.0, 200dpi)`; the OCR sidecar is labeled and may carry
  OCR artifacts.
- City raws fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged) —
  provenance in `raw/_fetch_log.jsonl` (7 live fetches, all HTTP 200 `application/pdf`, via the
  `holladayut.gov`→`cms3.revize.com` redirect). The 4 state compilations carry appended
  copy-provenance records in the same log (sha256 + true `jobs.utah.gov` URL + original retrieved
  time), flagged `note: copied sha256-verified from bluffdale`.
- Corpus screened with `audit-city-data/scripts/screen_corpus.py` (11 sidecars): **0
  cid/replacement/PUA/mojibake/stub/read-error/dict-ratio/split-word outliers.** The advisory
  `repeated_line`/`ends_mid` flags are expected artifacts of the HCD web-form layout (repeated
  field labels) and multi-page/section cuts; the single `weird_char` flag on the 2016 plan is
  benign Word non-breaking hyphens (`‐`, e.g. "in‐depth"), not garble.
- Each state sidecar grep-verified to contain "Holladay" and **zero** neighbor-city headers
  (`Hooper city` / `Highland city` / `Herriman city` = 0).

## Provenance note (do not "fix")

The `24reports.pdf` Holladay excerpt is the **state-published** copy of the same annual report
whose **city-filed** copy is `holladay-2024-mih-annual-report-city.pdf` (submitted 2024-08-01).
Both are retained as distinct artifacts (city vs state publication of one report) — intentional,
not a duplicate to prune.
