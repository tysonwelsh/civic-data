# housing_plans — West Valley City General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-06.**

## What this is

West Valley City's land-use / housing planning record, from two repositories:
1. **City of West Valley City** (CivicPlus site `www.wvc-ut.gov`) — the adopted **General Plan**
   (web-chapter-delivered; landing `/450` + Chapter 7 Housing `/2176`) and its statutory
   **Moderate Income Housing (MIH) Element** — the **2025 Moderate Income Housing Plan**, a standalone
   22-page PDF published as a General Plan appendix (`DocumentCenter/View/23733`).
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports** WVC
   files with the state, as published in HCD's statewide compilations (report years 2023/2024/2025),
   plus the SB 34 2019–2021 progress summary (`compliance_letter` proxy).

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies (statutory menu) giving a "realistic opportunity" for households
  at **≤ 80% of county AMI**. WVC has a fixed-guideway transit station (**West Valley Central /
  Fairbourne Station**), so it must adopt the **station-area-plan strategy (Strategy U)** and extra
  transit-related strategies.
- **Utah Code § 10-9a-408** — each municipality files an **annual MIH implementation report** with
  HCD. HCD reviews (does not audit) the self-reported data.
- **HB 462 (2022)** strengthened these (station area plans / HTRZ tools for transit cities).
- **SB 34 (2019)** — earlier MIH-plan mandate; HCD's 2019–2021 progress summary is retained here.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — the **complete 12-chapter GP** ("Vision West 2035 General Plan") plus the
  **landing / components page** (`/450`). The GP is **web-chapter-delivered; no consolidated GP PDF
  exists** ("Contact our office for a PDF General Plan"). Every chapter retained as its own raw +
  `.txt` sidecar (see index.csv):
  - **11 chapters are CivicPlus web pages** (`/2166`–`/2182`): Ch 1 Introduction, 2 Administration,
    3 Land Use, 4 Economic Development, 5 Urban Design, 6 Existing Neighborhoods, 7 Housing,
    8 Community Facilities, 9 Parks/Rec/Culture, 10 Transportation, 12 Definitions — `format=html`,
    `extraction_method=html-strip` (html.parser tag-strip; nav chrome retained; source text incl.
    curly quotes preserved verbatim, no cleanup).
  - **Ch 11 Implementation is the ONE chapter served as a born-digital PDF** (Adobe InDesign,
    `DocumentCenter/View/23727`, 16 pp) — `format=text`, `pdftotext -layout` (~3.8k chars/pg, no OCR).
    It holds the Actions Summary Table consolidating every chapter's goals/actions.
  - **Class-3 GP-text addendum (2026-07-16):** the prior build extracted only Ch 7 Housing + the
    landing; the other 11 chapters were fetched/extracted in this pass (primary-documents rollout).
    The 5 GP *appendix* plans (Active Transportation, Major Street Plan, Fairbourne Station Vision,
    Station Area Plans, Water Use & Preservation) remain OUT of scope — separate non-MIH appendix
    documents, catalogued in AVAILABILITY.md, not ingested here. The MIH Plan appendix IS ingested
    (as `mih_element`, below).
- **mih_element** — the **2025 Moderate Income Housing Plan** (standalone born-digital PDF appendix,
  22 pp). The MIH element of record.
- **mih_annual_report** — HCD statewide compilations for report years **2023 / 2024 / 2025** (WVC's
  filing is a page-range within each — see below).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019–2021** (WVC = PDF pp.
  193–196). HCD issues no per-city compliance letter; this is the closest published artifact.

## Standalone vs. chapter

**MIH is a STANDALONE plan** (the 22-page 2025 PDF appendix) *and* the GP separately has a Housing
chapter (Ch 7). The Housing chapter text says the MIH Plan "is included as an appendix to this General
Plan." Use the **2025 MIH Plan PDF** as the statutory element; the web Housing chapter is the GP's
narrative housing element (older 2011–2014-vintage data).

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- City site is **CivicPlus**: GP core is JS-rendered web chapters; appendix PDFs live at
  `/DocumentCenter/View/<id>/…` and were discovered by sitemap crawl + link extraction from `/450`.
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- **MIH Plan PDF** is born-digital (Acrobat PDFMaker; text layer) → full `pdftotext -layout` sidecar.
  58k chars / 22 pp (~2.7k chars/page ≫ the 100-chars/page OCR floor — no OCR needed).
- **GP HTML** (landing + all 10 remaining web chapters) → tag-stripped `.txt` sidecars
  (`extraction_method=html-strip`; html.parser, entities decoded, UTF-8 preserved verbatim). Chapter
  numbering (1-1, 3-1, 8-1 …) verified present in every sidecar. **Ch 11 Implementation** is instead a
  born-digital PDF → `pdftotext -layout`. `screen_corpus.py` on `text/` (18 files, 2026-07-16): 0
  cid/replacement/PUA/mojibake/long-token/dict outliers; only advisory `ends_mid` (HTML/page-range
  extracts) + `repeated_line` (state templates). dict_ratio median 0.78.
- **State compilations** → **WVC page-range** sidecars only (`text/west-valley-city-<year>.txt`,
  `text/west-valley-city-sb34-2019-2021.txt`); full compilations retained verbatim in `raw/`.
- `screen_corpus.py` on `text/` → **clean**: 0 cid-artifacts / replacement-chars / PUA-garbled /
  mojibake / long-tokens across all 7 files; only advisory flags (repeated gov form-header lines in the
  state templates; page-range/HTML extracts end mid-content). dict_ratio median 0.77.

## Caveats

- **No consolidated General Plan PDF** — the GP is web chapters + appendix PDFs. Retained GP artifacts
  are the landing HTML + **all 12 chapters** (11 web-page chapters + the Implementation PDF). The 5
  non-MIH appendix plans are catalogued but not ingested (see AVAILABILITY.md).
- **State "annual report" = statewide compilation**, not a standalone WVC PDF. Cite the page range;
  the compilation is authoritative, the sidecar is a convenience extract.
- **Disambiguation:** in the alphabetical compilations WVC sorts **after West Point, before White
  City** (cluster: West Jordan → West Point → West Valley → White City). Ranges were pinned by
  per-page jurisdiction-mention counts; sidecars verified free of adjacent-city bleed. See
  `AVAILABILITY.md`.
- **Vintage:** appendix docs are labeled "2025 General Plan"; a comprehensive GP update is in progress
  (2025 start, **2027** completion per the 2025 state report). The core GP chapters predate it.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- The **2025 MIH Plan** references the **Fairbourne Station Vision** (West Valley Central station),
  RM-zone density steering, and 2021 internal-ADU allowances — joinable to `meeting_minutes/` and
  `planning_commission/` land-use actions by topic/date.
- The 2025 state report's adoption-resolution and MIH-element links are `sharepoint.com` **personal**
  URLs (auth-gated) — not fetchable; recorded as a gap, not retrieved.
