# housing_plans — Sandy City General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-16** (2026-07-16:
PRIMARY_DOCS_PILOT class-3 expansion — the full general-plan TEXT corpus, +28 index rows; built
2026-07-05).

## What this is

Sandy's land-use / housing planning record, from two repositories:
1. **City of Sandy** (CivicPlus site `sandy.utah.gov`) — the current adopted **General Plan**
   (comprehensive update adopted 2025-01-07, delivered as an interactive ArcGIS web plan), the
   PDF-form **Moderate Income Housing (MIH) Element** (General Plan Chapter 10, Sept 2022) + the
   ordinance revising its Implementation Plan (Ord 23-01, 2023), and Sandy's **2017 Biennial MIH
   Report**.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Sandy files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus
   the SB 34 2019–2021 progress summary.

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies (from a statutory menu) giving a "reasonable opportunity" for
  households at **≤ 80% of county AMI** to live in the city.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD. HCD reviews (does not audit) the self-reported data.
- **HB 462 (2022)** strengthened these and, for cities with fixed-guideway transit (Sandy has TRAX +
  the planned S-Line/BRT areas), pushes **Station Area Plans** and HTRZ tools. Sandy's 2025 General
  Plan bundles a **new MIH Element + five station area plans** (adopted 2025-01-07).

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter` /
`small_area_plan` (added 2026-07-16 for the standalone 2019 Stadium Village Master Plan).

- **general_plan** — BOTH GP eras, full text corpus since 2026-07-16:
  1. **Pre-2025 chaptered GP** (the plan of record until 2025-01-07): Chapters 1–9 + Index of
     Appendices, recovered from CivicPlus assets whose page listing survives only in the
     2024-04-20 Wayback capture of `/798` (the city replaced the page after adoption). A
     patchwork by design — chapter adoption dates run 1979→2022 (Ch.7 Housing revised Sept 2022
     via Ord 22-10; the council-exhibit form of that revision is also captured). Ch.10 (MIH)
     was already held.
  2. **Pace of Progress: Sandy City General Plan 2050** (adopted 2025-01-07, Ord 25-01):
     Sections 1–7 + Appendix A (the five Station Area Plans) + Appendix B (NAC plans) from the
     Legistar council-review attachments — the **draft-of-record family**: Ord 25-01 adopts "the
     draft dated 10/21/2024" as amended by its Exhibit B (the signed ordinance with amendment
     exhibits lives in `ordinances/raw/ordinances/2025-01-07_25-01.pdf`). Sections 1–2 are the
     8-29-2024 pre-PC-amendment version; 3–7 + appendices carry no draft banner. PLUS the
     city-published **adopted-form Section 2 | Livability** PDF (the city's own "Link to Plan"
     for the current MIH element in its 2025 state filing). **Section 7 pages T19–T41 are the
     land-use designation/mix tables.** The `/798` landing HTML + four ArcGIS JSON captures
     (reduced fidelity, see Caveats) round out the web product's record. **Section 8
     (Resiliency & Sustainability + implementation strategies) is an honest gap** — see
     AVAILABILITY.md.
- **mih_element** — General Plan **Chapter 10 – Moderate Income Housing** (Sept 2022; the last PDF
  MIH element) + **Ordinance 23-01** (2023-01-31) revising its Implementation Plan.
- **mih_annual_report** — the **2017 Biennial MIH Report** (city copy) + HCD statewide compilations
  for report years **2023 / 2024 / 2025** (Sandy's filing is a page-range within each — see below).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019–2021** (Sandy = PDF pp.
  134–135). HCD issues no per-city compliance letter; this is the closest published artifact.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- City site is **CivicPlus**: pages are JS-rendered and expose no static document links; documents
  live at `content.civicplus.com/api/assets/<guid>` and were discovered by sitemap crawl + targeted
  search, then confirmed by probing each asset's `Content-Disposition` filename. The old
  `sandy.utah.gov/home/showdocument?id=…` DocumentCenter is dead (302 → `/home`).
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- All city PDFs are **born-digital** (text layer present, incl. the "signed" Ord 23-01) → full
  `pdftotext -layout` sidecars in `text/`.
- **Chapters 3, 6, 9 of the pre-2025 GP have a broken Identity-H toUnicode cmap** (every glyph
  maps 29 code points low — the known Sandy garble family from the minutes remediation). Their
  sidecars are the verified **+29 decode** (`extraction_method=pdftotext-layout+cmap-shift-decode`;
  glyph-space = \x03→space, pdftotext layout spaces untouched); screen_corpus reports 0 artifacts.
- ArcGIS captures are raw REST JSON (`format=json`, `extraction_method=arcgis-rest-api`) — kept
  verbatim in `raw/`, no sidecars.
- State compilations → **Sandy page-range** sidecars only (`text/sandy-<year>-mih-annual-report.txt`,
  `text/sandy-sb34-2019-2021-progress.txt`); full compilations retained verbatim in `raw/`.
- `screen_corpus.py` on `text/` → **clean**: 0 cid-artifacts / replacement-chars / PUA-garbled /
  mojibake; only advisory flags (repeated gov header/footer/table lines; page-range extracts end
  mid-sentence). dict_ratio median 0.76.

## Caveats

- **The "web-only" 2025 GP is now substantially captured in PDF/text form** (2026-07-16 revision
  of the earlier "no PDF exists" finding): the narrative text lives in the Legistar draft-of-record
  sections + the adopted Ord 25-01 (with amendment exhibits) + the city-published adopted-form
  Section 2 PDF. What remains genuinely web-only: **Section 8** (never attached to any packet;
  its host `sandypaceofprogress.org` is dead) and the **interactive Future Land Use Map** (the
  ArcGIS product exposes geometry + designation labels only — the four `arcgis-*.json` rows are
  flagged REDUCED-FIDELITY, and the org hosts no StoryMap/Hub narrative for the plan).
- **The current MIH element** is the GP 2050 Livability section: use
  `text/gp2050-section-2-livability-current.txt` (the city's own "Link to Plan" in its 2025 state
  filing). The Sept-2022 Chapter 10 PDF (+ the 1.31.23 amended element) remains the pre-2025
  element of record.
- **Version honesty for GP 2050 sections:** Sections 1–2 drafts = 8-29-2024 pre-PC-amendment
  version; the adopted text = the 10/21/2024 draft AS AMENDED by Ord 25-01 Exhibit B (Stroud §2,
  Houseman §5, Sharkey §7, Dekeyzer §4+8, D'Sousa §7–8 — amendment PDFs are packet attachments,
  exhibits also inside the signed ordinance). Quote draft text as draft text.
- **State "annual report" = statewide compilation**, not a standalone Sandy PDF. Cite the page range.
- **Compilation layout interleaving:** the 2023/2024 compilations use a merged/2-up column layout, so
  adjacent Salt Lake County (Sandy's county) and Santa Clara column text bleeds into Sandy's page
  range. The sidecars are convenience extracts; the full compilation is authoritative.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- **Ord 23-01** — Planning Commission positive-recommendation hearing **2023-01-19**, City Council
  **2023-01-31**: joinable to `planning_commission/` and `meeting_minutes/all_votes.csv` by date.
- The 2025 General Plan adoption (**2025-01-07**) and its station area plans are joinable to Council
  votes by date; MIH strategies reference **The Cairns / Historic Sandy / Stadium Village** station
  areas and HTRZ tools noted in the state reports.
- PMN files for Holladay/Plain City/Murray were checked and **excluded** (not Sandy) — see
  `AVAILABILITY.md`.
