# housing_plans — Ogden City General Plan + Moderate Income Housing (MIH) element & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-05.**

## What this is

Ogden's land-use / housing planning record, from two repositories:
1. **City of Ogden** (CivicPlus site `www.ogdencity.gov`) — the current adopted **General Plan**
   (August 2002, consolidated 2020 update, 847-page PDF) and its **Moderate Income Housing (MIH)
   element**, which is **General Plan Chapter 7 – Housing (amended 2022)**, published as its own PDF.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Ogden files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus
   the SB 34 2019-2021 progress summary.

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies (from a statutory menu) giving a "reasonable opportunity" for
  households at **≤ 80% of county AMI** to live in the city. Ogden's MIH element (GP Ch. 7 sec. G)
  cites this section directly.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD. HCD reviews (does not audit) the self-reported data.
- **HB 462 (2022)** strengthened these and, for cities on a fixed-guideway/major transit corridor
  (Ogden has FrontRunner + planned BRT), pushes **Station Area Plans** and HTRZ tools. Ogden's MIH
  strategies (Actions Taken as of 2022; 2022-2025 timelines) include FrontRunner + BRT station area
  plans and the Make Ogden Downtown Plan implementation ordinance.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — Ogden City General Plan, consolidated 2020 update (`DocumentCenter/View/1031`,
  847 pp). The adopted plan of record. The comprehensive "Plan Ogden" rewrite (`/2809`) is
  in-progress and NOT yet adopted.
- **mih_element** — **General Plan Chapter 7 – Housing (amended 2022)** (`DocumentCenter/View/24462`,
  22 pp), which contains the Moderate Income Housing element + Implementation Plan. This is the file
  Ogden itself cites in its state filings as its "general plan, moderate income housing element."
- **mih_annual_report** — HCD statewide compilations for report years **2023 / 2024 / 2025** (Ogden's
  filing is a page-range within each — see `index.csv`/`AVAILABILITY.md`).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019-2021** (Ogden = PDF pp.
  93-94). HCD issues no per-city compliance letter; this is the closest published artifact.

## Standalone vs. chapter

Ogden's MIH element is a **chapter of the general plan** (Ch. 7 – Housing), published as its own PDF.
There is no separately-numbered stand-alone "Moderate Income Housing Plan" distinct from that
chapter. Both the chapter PDF and the full consolidated General Plan are retained.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance:
  `raw/_fetch_log.jsonl`.
- City site is **CivicPlus** (`www.ogdencity.gov`; `.com` 301→`.gov`): the Housing-Element and
  Plan-Ogden landing pages are JS-rendered and expose no static document links; documents live at
  `DocumentCenter/View/<id>`, discovered via the `/541/City-Plans` page + the direct URL Ogden
  printed in its own 2025 state MIH filing.
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- Both city PDFs are **born-digital** (well above the "chars/page < 100 ⇒ OCR" gate) → full
  `pdftotext -layout` sidecars in `text/`. **No OCR needed** anywhere in this dataset.
- State compilations → **Ogden page-range** sidecars only
  (`text/ogden-<year>-mih-annual-report.txt`, `text/ogden-sb34-2019-2021-progress.txt`); full
  compilations retained verbatim in `raw/`.
- `screen_corpus.py` on `text/` → **clean**: 0 cid-artifacts / PUA-garbled / mojibake / long-tokens;
  only advisory flags (repeated gov header/footer lines; page-range extracts ending mid-sentence; 1
  stray replacement char in the 2.7 MB General Plan sidecar). dict_ratio median 0.76.

## Caveats

- **The MIH element is a general-plan chapter**, not a standalone plan. Treat GP Ch. 7 (`View/24462`)
  as the element of record (amended 2022).
- **State "annual report" = statewide compilation**, not a standalone Ogden PDF. Cite the page range.
- **Compilation layout quirks:** the **2023** compilation splits question/answer across pages (Ogden
  range opens mid-answer); the **2024** compilation is a **two-up merged** layout (two printed page
  numbers + a right-hand generic-instruction column per PDF page). Sidecars are convenience extracts;
  the page range in the full compilation is authoritative. Ogden pages were bracketed against North
  Ogden / South Ogden / Orem to avoid same-name bleed.
- **Source typo preserved:** the 2024 filing lists `brandonrypien@ogdencity.com` (the `.gov` domain
  is used in 2025) — retained verbatim.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.
- The **adopting ordinance (Ord. 2023-8)** for the MIH element is referenced only by a local network
  path in Ogden's filing and is not publicly hosted; its text lives in the municipal code
  (amlegal.com), which is the separate `ordinances` source type's scope.

## Linkage to the rest of the repo

- MIH element amendment (2022) and the Make Ogden Downtown Plan implementation ordinance
  (adopted 2023-03-07, per the 2023 filing) are joinable to `meeting_minutes/all_votes.csv` and
  `planning_commission/` by date.
- Station area plan work (FrontRunner + BRT) referenced in the 2024/2025 filings ties to Ogden's
  ongoing land-use record.
