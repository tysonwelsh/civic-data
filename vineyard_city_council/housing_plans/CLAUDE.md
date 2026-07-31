# housing_plans — Vineyard City General Plan + Moderate Income Housing (MIH) element & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-05.**

## What this is

Vineyard's land-use / housing planning record, from two repositories:
1. **City of Vineyard** (Revize site `vineyardutah.gov`) — the adopted **General Plan** (General Plan
   Update, May 2019), its **Future Land Use Map**, and **Ordinance 2022-17** (2022-09-14), the General
   Plan amendment that updated the **Moderate Income Housing (MIH) element** to align with Utah Code
   10-9a-403 after HB 462.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Vineyard files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus
   the SB 34 2019-2021 progress summary.

## Statutory context

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: strategies (from a statutory menu) giving a "reasonable opportunity" for
  households at **≤ 80% of county AMI** to live in the city.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD. HCD reviews (does not audit) the self-reported data.
- **HB 462 (2022)** strengthened these. Vineyard, built on the former Geneva Steel site around a UTA
  **FrontRunner station** (the Utah City / Downtown Vineyard district), is a fixed-guideway-transit
  city: Ord 2022-17 brought its MIH element into HB 462 compliance, and the city has since pursued an
  **HTRZ** (Housing & Transit Reinvestment Zone) and a **Station Area Plan (SAP)** at the station.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — the **2019 General Plan Update** (151-page born-digital PDF) and its **Future
  Land Use Map** (single-page vector map). The living/codified plan is also online at
  `vineyard.municipalcodeonline.com/book?type=plan` (JS app; no PDF snapshot to retain).
- **mih_element** — **Ordinance 2022-17** (2022-09-14), the GP amendment updating the MIH element to
  10-9a-403. **The MIH element is a General Plan chapter, not a standalone plan** — it first appears
  as the "Moderate Income Housing" chapter of the 2019 GP (printed pp. 98-107) and was updated in
  place by Ord 2022-17.
- **mih_annual_report** — HCD statewide compilations for report years **2023 / 2024 / 2025**
  (Vineyard's filing is a page-range within each — see below).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019-2021** (Vineyard = PDF pp.
  176-177). HCD issues no per-city compliance letter; this is the closest published artifact.

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`.
- City site is **Revize**: the `vineyardutah.gov` sitemap enumerates a `Departmnts/Planning/…`
  document tree served from `cms3.revize.com/revize/vineyard/…`; the GP PDF and Future Land Use Map
  were taken from there via the live `/government/planning.php` page. Ord 2022-17 lives in the
  `municipalcodeonline.com` S3 bucket behind the online codified plan.
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`).

## Extraction

- All city PDFs are **born-digital** (text layer present) → `pdftotext -layout` sidecars in `text/`.
  The Future Land Use Map is a vector map; its sidecar is legend/category labels only.
- State compilations → **Vineyard page-range** sidecars only
  (`text/vineyard-<year>-mih-annual-report.txt`, `text/vineyard-sb34-2019-2021-progress.txt`); full
  compilations retained verbatim in `raw/`.
- `screen_corpus.py` on `text/` → **clean**: 0 cid-artifacts / replacement-chars / PUA-garbled /
  mojibake; only advisory flags (map sidecar short; repeated gov form header/footer lines;
  page-range extracts end mid-form). dict_ratio median 0.78.

## Caveats

- **The MIH element is a General Plan chapter**, updated in place by Ord 2022-17. There is no
  standalone MIH Plan PDF; cite the 2019 GP chapter (pp. 98-107) + Ord 2022-17 (2022-09-14).
- **The current codified General Plan is web-only** (`municipalcodeonline.com`, JS app). The retained
  GP artifact is the 2019 GP PDF; the 2022 MIH amendment is retained as Ord 2022-17.
- **State "annual report" = statewide compilation**, not a standalone Vineyard PDF. Cite the page
  range; the 2023 compilation was trimmed at a bleed boundary and 2024 uses a 2-up layout — the full
  compilation is authoritative (see AVAILABILITY.md).
- **The FrontRunner Station Area Plan is in progress, not adopted** as of 2026-07-05 (per Vineyard's
  2024/2025 state reports) — recorded as a forward gap, not retrieved.
- MIH self-reported data is reviewed, not audited, by HCD — treat figures as the city's self-report.

## Linkage to the rest of the repo

- **Ordinance 2022-17** — Planning Commission public hearing **2022-09-07**, City Council adoption
  **2022-09-14** (Mayor Julie Fullmer): joinable to `planning_commission/` and
  `meeting_minutes/all_votes.csv` by date.
- The state reports reference **Utah City / Downtown Vineyard**, the **FrontRunner HTRZ**, and the
  Station Area Plan — cross-referenceable to the RDA/redevelopment record and Council land-use votes.
