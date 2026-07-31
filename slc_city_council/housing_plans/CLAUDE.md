# housing_plans — Salt Lake City General Plan + moderate-income housing plans & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `public_comments/`, `db/`, etc. **As-of 2026-07-05.**

## What this is

SLC's land-use / housing planning record, from two repositories:
1. **City of Salt Lake City** (`slc.gov` / `slcdocs.com`) — the adopted **General Plan**
   (Plan Salt Lake, 2015), and SLC's **standalone five-year housing plans**: **Growing SLC
   2018-2022** (adopted 2017, Ord. 71 of 2017) and its current successor **Housing SLC 2023-2027**,
   plus the **Thriving in Place** anti-displacement strategy (2023) and the city's **2021 annual MIH
   report** copies.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   SLC files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus the
   SB 34 2019-2021 progress summary.

## SLC structural quirk (important)

Unlike smaller cities that fold a "Moderate Income Housing Element" into a numbered general-plan
chapter, **SLC keeps its MIH element as a separate standalone housing plan.** Plan Salt Lake (the
general plan) is a 50-page vision/principles document; the moderate-income-housing element of record
is **Growing SLC 2018-2022 → Housing SLC 2023-2027** (both filed under Planning > General Plans >
Housing). Do not expect an MIH chapter inside Plan Salt Lake — there isn't one (see AVAILABILITY.md).

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — Plan Salt Lake (adopted 2015-12-01).
- **mih_element** — Growing SLC 2018-2022 (full-with-attachments) + its signed adopting Ordinance
  No. 71 of 2017; **Housing SLC 2023-2027** (current); **Thriving in Place** anti-displacement
  strategy (2023).
- **mih_annual_report** — city-published SLC 2021 annual MIH report (form + narrative) + HCD
  statewide compilations for report years **2023 / 2024 / 2025** (SLC's filing is a page-range within
  each — see below).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019-2021** (SLC = fitz pp.
  122-131). HCD issues no per-city compliance letter; this is the closest published artifact.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- City docs discovered from the Planning Division `citywide-plans` page + the Growing SLC page, then
  fetched from `slcdocs.com` / `slc.gov/hand/...` upload paths. Some newer slugs
  (`/can/housingplan`, `/housingstability/838-2/`) 404 — the citywide-plans page is the durable index.
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- City PDFs are **born-digital** (text layer present) → full `pdftotext -layout` sidecars in `text/`.
- **Exception — the signed Growing SLC ordinance is an image-only scan** (no text layer) → OCR'd with
  `tesseract --psm 6` at 300 dpi; sidecar labeled `format=scanned`, `extraction_method=tesseract-ocr`.
- State compilations → **SLC page-range** sidecars only (`text/slc-<year>-mih-annual-report.txt`,
  `text/slc-sb34-2019-2021-progress.txt`) via PyMuPDF page extraction; full compilations retained
  verbatim in `raw/`. Page ranges are **fitz 0-based indices** (recorded in `index.csv` `notes`).
- Manual corpus screen: 0 replacement-chars / cid-artifacts / mojibake across `text/`; wordlike
  ratio 0.95-0.99. (repo's `screen_corpus.py` is not present in this checkout.)

## Caveats

- **The MIH element is a standalone plan, not a GP chapter** (see quirk above).
- **`Ordinance No17-2019` filename ≠ document:** the signed ordinance's server filename says
  `No17-2019`, but it is **Ordinance No. 71 of 2017** (adopted 2017-12-12). Source filename preserved
  verbatim; the true number is in `index.csv`.
- **State "annual report" = statewide compilation**, not a standalone SLC PDF. Cite the fitz page
  range; the full compilation in `raw/` is authoritative. Adjacent Salt Lake **County** follows SLC
  alphabetically, so header bleed is possible at range edges.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- **Growing SLC Ordinance 71 of 2017** — Planning Commission positive recommendation **2017-04-26**,
  Council adoption **2017-12-12**: joinable to `planning_commission/` and
  `meeting_minutes/all_votes.csv` by date.
- **Thriving in Place** — Planning Commission hearing **2023-07-26**, Council adoption **2023-10-17**:
  joinable by date.
- **Housing SLC 2023-2027** effective July 2023; the state 2023/2024/2025 reports narrate its and the
  RDA / Community Reinvestment Agency's implementation actions — cross-reference to Council/RDA votes
  (SLC council reconvenes in-session as the RDA; see the city CLAUDE.md).
