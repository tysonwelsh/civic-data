# housing_plans — availability & verification (Bluffdale)

**As of:** 2026-07-12. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing Bluffdale dataset was modified.

## What was checked

Two source families, per the skill:

1. **City** (`bluffdale.gov`, CivicPlus/CivicEngage). Discovered by crawling
   `https://www.bluffdale.gov/sitemap.xml` (NOT stale search-result URLs), then navigating the
   dedicated **Moderate Income Housing** page (`/878/Moderate-Income-Housing`), the
   **Master Plans** page (`/218/Master-Plans`, holds the General Plan), and the **Planning**
   page (`/268/Planning`). Docs are CivicEngage `/DocumentCenter/View/<id>` links.
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. The annual reports are
   **statewide compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`), plus the
   `sb34.pdf` SB 34 Municipal Progress Summaries (2019–2021).

## What was FILED / retrieved (11 index rows, 11 raw PDFs)

### City documents (7 PDFs)
- **General Plan** — adopted **June 8, 2022** (`View/5049`, 486 pp). Current land-use context.
- **MIH Element (2022)** — the HB 462 element, adopted **in its entirety** as the official MIH
  Element of the General Plan by **Ordinance 2022-15** on **2022-09-14** (`View/5099`, 19 pp),
  with the adopting ordinance itself (`View/8521`, 8 pp).
- **MIH Element (2022 — AMENDED)** — adopted by **Ordinance 2023-04** on **2023-01-25**
  (`View/5393`, 18 pp), plus the longer final adopted package "MIH Report — 2022 AMENDED —
  Ordinance 2023-04" (`View/5394`, 27 pp).
- **2024 annual MIH report** — city-filed copy of the 10-9a-408 implementation report
  (`View/6981`, 8 pp).
- **2025 Notice of Compliance** — HCD letter (July 15 2025) finding the 2025 report compliant
  (`View/8677`, 1 pp).

**Form of the MIH element:** Bluffdale's MIH element is a **General Plan chapter adopted by a
standalone ordinance** — BOTH a standalone element PDF (View/5099, View/5393/5394) AND its
adopting ordinances (2022-15, 2023-04) exist and are captured. It is not buried only inside the
486-page General Plan PDF.

### State HCD compilations (4 PDFs — Bluffdale present in ALL of them)
Each statewide compilation was downloaded verbatim; Bluffdale's alphabetical page range was
located (bracketed by the next city, **Bountiful**) and extracted to a `text/` sidecar, then
**grep-verified for zero neighbor-city bleed** (no American Fork / Bountiful / Brigham text):

| Compilation | Total pp | Bluffdale (physical) pp | Sidecar |
|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | 28–37 (printed 27–36) | `text/bluffdale-2023.txt` |
| `24reports.pdf` (RY 2024) | 1030 | 27–32 | `text/bluffdale-2024.txt` |
| `25reports.pdf` (RY 2025) | 1303 | 30–38 | `text/bluffdale-2025.txt` |
| `sb34.pdf` (SB 34 2019–2021) | 199 | 6–7 | `text/bluffdale-sb34-2019-2021.txt` |

**Bluffdale is present and compliant in every filing year checked** (2023, 2024, 2025 annual
reports + the 2019–2021 SB 34 progress summary). The absence of a *standalone per-city report
file* on the state site is **expected** (the state publishes only statewide compilations), NOT
a gap. City = "without a fixed guideway transit station"; three MIH strategies accepted (matches
the 2025 compliance letter).

## What is NOT filed / not applicable

- **No standalone per-city PDF on the state HCD site** — expected; the state publishes only the
  statewide compilations. Not a gap.
- **No 2022 (RY 2022) annual-report compilation** was linked on the current HCD index; the
  earliest annual compilation offered is `23reports.pdf`. The SB 34 summary covers the 2019–2021
  window. No honest gap: HB 462 annual reporting under the current form begins with RY 2023.
- The `State-Code-Housing-Requirements` PDF on the Planning page (`View/5290`) is a copy of the
  Utah statute text (10-9a-403/408), not a Bluffdale plan/report — deliberately **not** indexed
  (out of scope for `doc_type` vocab; it is reference material, not a city document).

## Extraction & verification method

- All 11 raw PDFs are **born-digital** (text layer present; `pdftotext -layout` yields clean
  text — the council-minutes OCR seam does NOT apply to these documents). `extraction_method =
  pdftotext -layout`, `format = text` for every row.
- Every raw byte fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged);
  provenance in `raw/_fetch_log.jsonl` (all HTTP 200, `application/pdf`).
- Corpus screened with `audit-city-data/scripts/screen_corpus.py`: **0 dict-ratio outliers,
  0 split-word outliers, 0 weird-char outliers, 0 read errors** across 11 sidecars. The
  advisory `ends_mid` / `repeated_line` flags are expected artifacts of the HCD web-form report
  layout (repeated field labels), not extraction defects.
- State-compilation page ranges verified two ways: TOC printed page numbers AND physical-page
  probing (printed→physical offset +1 in 23reports confirmed by the printed page number at page
  foot); each sidecar grep-verified to contain "Bluffdale" and **zero** neighbor-city strings.

## Provenance note (do not "fix")

The `24reports.pdf` Bluffdale excerpt is the **state-published** copy of the same annual report
whose **city-filed** copy is `View/6981` (`bluffdale-mih-report-23-24.pdf`). Both are retained as
distinct artifacts (city vs state publication of one report) — this is intentional, not a
duplicate to prune.
