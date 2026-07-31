# housing_plans — Millcreek General Plan + Moderate Income Housing (MIH) element & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-06.**

## What this is

Millcreek's land-use / housing planning record, from two repositories:
1. **City of Millcreek** (CivicPlus site `millcreekut.gov`; documents at `/DocumentCenter/View/<id>`) —
   the adopted **Millcreek Together General Plan** (the MIH element is embedded in it), the adopting
   **Ordinance 22-44** (the MIH element of record), and Millcreek's own **Aug-2024 Housing Report**.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Millcreek files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus
   the SB 34 2019–2021 progress summary.

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies (from a statutory menu) giving a "realistic opportunity" for
  households at **≤ 80% of county AMI**. Millcreek is within 1/2 mi of **two fixed-guideway transit
  stations**, so it commits to the **6+-strategy** tier (priority-funding qualification).
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD. HCD reviews (does not audit) the self-reported data.
- **HB 462 (2022)** strengthened these; Millcreek's response was **Ordinance 22-44** (Sept 26, 2022),
  which amended the MIH element of the General Plan to add strategies + an implementation plan.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — **Millcreek Together General Plan** (`View/3193`, 140 pp). Adopted Feb 2019;
  slug-labeled "Sep 2022"; living document (see caveats). **The MIH element lives inside it**
  (Chapter 4 + housing appendix); there is **no separate standalone MIH-element PDF**.
- **mih_element** — **Ordinance 22-44** (2022-09-26, 53 pp) — the ordinance body + adopted MIH
  strategies/implementation-plan exhibit. This is Millcreek's MIH element of record.
- **mih_annual_report** — the **Aug-2024 Millcreek Housing Report** (city copy) + HCD statewide
  compilations for report years **2023 / 2024 / 2025** (Millcreek's filing is a page-range within
  each — see below).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019–2021** (Millcreek = PDF pp.
  81–82). HCD issues no per-city compliance letter; this is the closest published artifact.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- City documents discovered by **sitemap crawl + the Planning & Zoning page `/151`** (the "Plans and
  Policies" / "Affordable Housing" nav pages carry no plan documents). Ordinance 22-44 came from
  **Utah Public Notice** (`utah.gov/pmn/files/893155.pdf`).
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- All city PDFs are **born-digital** (text layer present, incl. the "signed" Ord 22-44) → full
  `pdftotext -layout` sidecars in `text/`.
- State compilations → **Millcreek page-range** sidecars only
  (`text/millcreek-<year>-mih-annual-report.txt`, `text/millcreek-sb34-2019-2021-progress.txt`);
  full compilations retained verbatim in `raw/`.
- Page ranges (verified by header brackets): 2023 pp.413–429, 2024 pp.399–413, 2025 pp.507–521,
  SB34 pp.81–82.
- `screen_corpus.py` on `text/` → **clean**: 0 cid-artifacts / replacement-chars / PUA-garbled /
  mojibake / long-tokens; dict_ratio median 0.75; only advisory flags. These housing PDFs are
  born-digital and do NOT carry the OCR garble that afflicts the city's *minutes* corpus.

## Caveats

- **No standalone MIH element.** The MIH element is embedded in the General Plan (Ch. 4 + appendix);
  its authoritative, self-contained form is **Ordinance 22-44** — treat that as the element PDF.
- **General Plan cover date anomaly.** `View/3193`'s cover text reads **"Amended December 12, 2026"**
  (future-dated — a likely source typo/placeholder), while the body references 2023 station-area
  plans. The URL serves the **living/current** GP, not a frozen 2022 snapshot. Cite in-text content;
  do not over-trust the cover date.
- **State "annual report" = statewide compilation**, not a standalone Millcreek PDF. Cite the page
  range.
- **Compilation layout bleed (2023 & 2024).** Those compilations use a merged/2-up column layout, so
  adjacent **Murray** (and some Salt Lake County / South Salt Lake) text bleeds into Millcreek's page
  range (2023: ~16 Murray mentions; 2024: ~22). **2025 and SB 34 are clean.** The sidecars are
  convenience extracts; the full compilation is authoritative. (Note: some South Salt Lake references
  in Millcreek's own report are genuine — the Meadowbrook/Millcreek-TRAX joint station-area plans.)
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- **Ordinance 22-44** (2022-09-26) is joinable to `meeting_minutes/all_votes.csv` by date (Council
  adopted it in the Sept 26, 2022 regular meeting) and, upstream, to a Planning Commission
  recommendation in `planning_commission/`.
- Annual reports reference Millcreek land-use actions (ADU-ordinance easing, reduced parking rates,
  Affordable Housing Incentives adopted Apr 2025, station-area-plan work) that appear as council/PC
  motions in the minutes — join by date/subject.
- **Ordinance 24-48** (a 2024 rezone) was checked and **excluded** (not a housing-plan doc) — see
  `AVAILABILITY.md`.
