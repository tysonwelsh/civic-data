# housing_plans — Park City General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, `public_comments/`, etc. **As-of 2026-07-05.**

## What this is

Park City's land-use / housing planning record, from two repositories:
1. **City of Park City** (Revize CMS site `parkcity.gov`) — the adopted **2025 General Plan**
   (comprehensive update, adopted 2025-09-25) + Citizen's Summary + Appendix; the standalone
   **Five-Year Moderate Income Housing Plan (MIHP)** that is adopted *as the Housing Element of the
   General Plan* (2022 original + 2023 Amended + 2025 Update, with the signed adopting resolutions
   17-2022 and 02-2023); and the underlying **2020 Housing Assessment and Plan** + **2021 Addendum**,
   plus Park City's own copy of its **2020 annual MIH report form** to the state.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Park City files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus
   the SB 34 2019–2021 progress summary.

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies giving a "reasonable opportunity" for households at **≤ 80% of
  county AMI** to live in the city. Park City satisfies this with a **standalone Five-Year MIHP**
  adopted as the Housing Element.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD (posted to the city website; the 2020 form is retained here).
- **HB 462 (2022)** strengthened these. Park City (a resort town with a large deed-restricted
  affordable/workforce-housing program) sets a workforce-housing goal (house **15%** of the city
  workforce) in the 2025 General Plan.

## MIH: standalone plan AND a GP chapter (important)

Park City's MIH element is **both**: a **standalone "Five-Year Moderate Income Housing Plan"**
adopted as the Housing Element of the General Plan, **and** an embedded **"Moderate Income Housing"
chapter (p.30) inside the adopted 2025 General Plan**. When quoting "the MIH element," specify which
artifact. The **current standalone element of record** is the **Amended 2022 Five-Year MIHP**
(Res 02-2023, 2023-01-24), refreshed by the **2025 Update** (Res 12-2025).

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — the adopted **2025 General Plan** + Citizen's Summary + Appendix (adopted 2025-09-25).
- **mih_element** — the standalone **Five-Year MIHP** (2022 original / 2023 Amended / 2025 Update), the
  two signed adopting resolutions (**17-2022**, **02-2023**), and the **2020 Housing Assessment & Plan**
  + **2021 Addendum** (the needs-assessment basis of the element).
- **mih_annual_report** — Park City's **2020 state report form** (city copy) + HCD statewide
  compilations for report years **2023 / 2024 / 2025** (Park City's filing is a page-range within each).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019–2021** (Park City = jurisdiction
  #51, PDF p.97). HCD issues no per-city compliance letter; this is the closest published artifact.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- **City site is Revize** (`webspace=parkcityut`), **not CivicPlus.** The `showpublisheddocument/<id>/<ticks>`
  and `showdocument?id=<id>` deep links **404 sitewide** to non-browser clients (verified). Documents
  were retrieved from the **static file tree** `https://www.parkcity.gov/Documents/<section>/<File>.pdf`,
  discovered by crawling the working `.php` content pages
  (`/community/affordable_housing/moderate_income_housing_plan.php`,
  `/services/planning/general_plan_comprehensive_update.php`) and reading their `/Documents/`-rooted
  hrefs. Full routing audit: `AVAILABILITY.md`.
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- All city PDFs are **born-digital** (text layer present, incl. the two signed resolutions) → full
  `pdftotext -layout` sidecars in `text/`. **EXCEPT** `state-housing-report-form-2020.pdf`, which is
  **scanned** (no text layer) → **OCR via tesseract** (`format=scanned`, sidecar labeled).
- State compilations → **Park City page-range** sidecars only
  (`text/park-city-<year>-mih-annual-report.txt`, `text/park-city-sb34-2019-2021-progress.txt`); full
  compilations retained verbatim in `raw/`.
- Corpus garbling screen on `text/` → **clean**: 0 `(cid:NNN)` / 0 replacement chars / 0 PUA across
  all 14 born-digital + state sidecars; the OCR sidecar is legible.

## Caveats

- **State "annual report" = statewide compilation**, not a standalone Park City PDF. Cite the page range;
  the full compilation is authoritative. The **2024 compilation is TWO-UP** (each PDF page = 2 printed
  report pages) — watch adjacent-column bleed; the 2023/2025 are 1-up.
- **The 2014 General Plan is NOT in this dataset** — its only routes are the dead
  `showdocument`/`showpublisheddocument` deep links (verified 404). It is superseded by the adopted 2025
  GP (retrieved). See `AVAILABILITY.md`.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- **Resolution 17-2022** — Planning Commission public hearing **2022-08-24**, City Council **2022-09-01**:
  joinable to `planning_commission/` and `meeting_minutes/all_votes.csv` by date.
- **Resolution 02-2023** — City Council **2023-01-24** (Amended MIHP): joinable to
  `meeting_minutes/all_votes.csv` by date.
- **2025 General Plan** adoption **2025-09-25** (Park City meets **Thursday**): joinable to Council votes.
- **2025 MIHP Update** — Housing Resolution **12-2025**, adopted **2025-06-12**.
