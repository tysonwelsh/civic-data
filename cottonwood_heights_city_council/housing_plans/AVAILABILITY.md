# housing_plans — availability & verification (Cottonwood Heights)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing Cottonwood Heights dataset was modified.

## What was checked

Two source families, per the skill:

1. **City** (`cottonwoodheights.utah.gov`, Granicus / CivicPlus CivicEngage Central). The site
   403s a bare bot or bare browser UA behind an Akamai-style edge — every fetch used
   `scripts/polite_fetch.py` (browser UA + Accept/Accept-Language/Sec-Fetch-Mode), which the
   recon documents. Discovered by crawling `https://www.cottonwoodheights.utah.gov/sitemap.xml`
   → `sitemap-page-1.xml`, then navigating **Community Development → Adopted & Special Plans**
   (`/city-services/community-development/adopted-and-special-plans`) and **General Plan Update**
   (`/city-services/community-development/general-plan-update`). Docs are CivicEngage
   `/home/showpublisheddocument/<id>/<token>` links (harvested from the page anchors — not
   guessed). Two adopting-resolution scans (docs 10101, 6888) were located via the city's own
   URLs cited **inside the state compilation reports**.
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. The annual reports are
   **statewide compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`) plus the
   `sb34.pdf` SB 34 Municipal Progress Summaries (2019–2021). These four compilation PDFs were
   **NOT re-downloaded** — they are byte-identical to the copies already in
   `bluffdale_city_council/housing_plans/raw/` and were copied in after a **sha256 match**
   (all four verified). The `raw/_fetch_log.jsonl` provenance lines (true `jobs.utah.gov` URL +
   original `retrieved_utc`) were carried over unchanged.

## What was FILED / retrieved (12 index rows, 12 raw PDFs)

### City documents (8 PDFs)
- **General Plan** — adopted **Jan 14, 2005** (`doc 294`, 200 pp, born-digital). Land-use
  context; the city's 2025 state filing points to **General Plan §7.4 Affordability Analysis**
  as its MIH element location.
- **MIH element — 2019 base plan** — "Affordable Housing Report", **Nov 8, 2019** (`doc 5532`,
  38 pp, GSBS Consulting).
- **MIH element — 2022 amendment** — born-digital "Affordable Housing Report, December 2022
  amendment" (`doc 6828`, 46 pp), the "Link to Plan" in CH's 2023 state filing, **adopted by
  Resolution 2023-02** (effective **3 Jan 2023**). Its **signed/adopted scan** (`doc 6888`,
  48 pp, image-only → tesseract OCR) is the "Link to Ordinance or Resolution" in that filing.
- **MIH element — 2025 five-year update** — **Resolution 2025-51** (deposited **1 July 2025**),
  approving the year-five updated plan for state submission (PC hearing + unanimous
  recommendation **4 June 2025**) (`doc 10101`, 2 pp, image-only → tesseract OCR). Only the
  2-page resolution is published at this doc id; the plan itself is annexed.
- **Annual reports** — city-labeled **2020 report** (`doc 4283`, 36 pp, Nov 17 2020), **2021
  report** (`doc 5534`, 9 pp, GSBS), **2022 report** (`doc 6555`, 10 pp, GSBS) — the
  10-9a-408 implementation reports.

### State HCD compilations (4 PDFs — CH present and located in ALL of them)
Each statewide compilation's Cottonwood Heights alphabetical page range was located (bracketed
by the next city, **Draper**) and extracted to a `text/` sidecar, then grep-verified for zero
neighbor-city bleed:

| Compilation | Total pp | CH (physical) pp | Locate method | Sidecar |
|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | **128–137** | standalone header "Cottonwood Heights" p128; "Draper" p138 | `text/cottonwood_heights-2023.txt` |
| `24reports.pdf` (RY 2024) | 1030 | **116–125** | content-scan (TOC prints 230, exceeds physical); "Cottonwood Heights city" p116, "Draper city" p126 | `text/cottonwood_heights-2024.txt` |
| `25reports.pdf` (RY 2025) | 1303 | **162–174** | content-scan (TOC prints 159, offset +3); "Cottonwood Heights city" p162, "Draper city" p175 | `text/cottonwood_heights-2025.txt` |
| `sb34.pdf` (SB 34 2019–2021) | 199 | **27–28** | CH = summary #13; "COTTONWOOD HEIGHTS, CITY" p27, "DRAPER, CITY" p29 | `text/cottonwood_heights-sb34-2019-2021.txt` |

**Cottonwood Heights is present in every state filing year checked** (RY 2023, 2024, 2025 annual
reports + the 2019–2021 SB 34 progress summary). CH = "without a fixed guideway transit station".
The absence of a *standalone per-city report file* on the state site is **expected** (the state
publishes only statewide compilations), NOT a gap.

## What is NOT filed / not applicable

- **No HCD "Notice of Compliance" letter published on the city site.** Bluffdale posts its HCD
  compliance letters (`compliance_letter`); no equivalent CH-posted letter surfaced on the
  adopted-and-special-plans or general-plan-update pages. Recorded here as an honest absence —
  **no `compliance_letter` row**; not fabricated. (The compliance determination lives inside the
  state compilations' processing, not as a separate CH document.)
- **No standalone per-city PDF on the state HCD site** — expected; the state publishes only the
  statewide compilations. Not a gap.
- **No RY 2022 annual-report compilation** is linked on the current HCD index; the earliest
  annual compilation offered is `23reports.pdf`. The SB 34 summary covers 2019–2021. HB 462
  annual reporting under the current form begins with RY 2023. (CH's own city-posted `2022
  report`, doc 6555, is retained separately above.)

## Extraction & verification method

- **Born-digital PDFs (10 of 12 raw files)** → `pdftotext -layout`, `format = text`. The six city
  born-digital docs plus the four state compilations all carry a clean text layer.
- **Two city PDFs are image-only** (`doc 6888` the 2023-02 signed scan, `doc 10101` the 2025-51
  resolution) → `format = scanned`, `extraction_method = tesseract OCR`; full-document OCR
  sidecars in `text/`. OCR at 200 dpi; a few near-blank pages in 6888 produce empty page blocks
  (honest, not an error).
- Every city raw byte fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged);
  provenance in `raw/_fetch_log.jsonl` (all HTTP 200, `application/pdf`). The four state
  compilations were copied sha256-verified from bluffdale (not re-fetched) with their original
  `jobs.utah.gov` provenance lines carried over.
- Corpus screened with `audit-city-data/scripts/screen_corpus.py` (12 sidecars): **0** hard
  outliers in every category — `cid_artifacts`, `replacement_chars`, `PUA_garbled`, `mojibake`,
  `long_tokens`, `stub`, `short`, `duplicate_bodies`, `dict_ratio_outlier`, `split_word_outlier`,
  `weird_char_outlier`, `read_errors`. The advisory `hyphen_breaks` / `repeated_line` / `ends_mid`
  flags are expected artifacts of the plan-report / HCD web-form layout and the OCR docs (lowest
  dict-ratio 0.702 is the OCR'd 6888 — acceptable), not extraction defects.
- State-compilation page ranges verified by locating the standalone Cottonwood Heights report
  header and the next city (Draper) header; each sidecar grep-verified to contain "Cottonwood"
  and **zero** Draper/Clinton neighbor-header strings.

## Provenance note (do not "fix")

The four `hcd-*.pdf` state compilations are **byte-identical** (sha256-verified) to the copies in
`bluffdale_city_council/housing_plans/raw/`. They are shared statewide PDFs, so this is a
deliberate de-duplicated copy, not a re-download; the `source_url` and `retrieved_date` remain the
true `jobs.utah.gov` values / original retrieval. Do not delete or "re-fetch" them.
