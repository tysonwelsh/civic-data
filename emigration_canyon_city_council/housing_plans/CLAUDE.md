# housing_plans/ — Emigration Canyon moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Emigration Canyon's **General Plan** and the
state **Moderate Income Housing (MIH)** reporting record. Purely **additive** — no existing
Emigration Canyon dataset was touched. As-of 2026-07-14. **Read `AVAILABILITY.md` first.**

## Bottom line: honest near-empty (expected, valid)
Emigration Canyon (~1,600 pop; metro township 2017-2024 → city 2024-05-01; MSD-administered)
is **below the Utah Code 10-9a-403 "specified municipality" MIH threshold** (a fifth-class
city with population **5,000+** in a first/second/third-class county). It therefore has **no
MIH element, no state MIH annual report, and no HCD compliance letter** — only a **General
Plan** (land-use context). Same pattern as Copperton (~800) and Alta (~380). Absence is
DATA, not a gap to fill.

## Layout
```
raw/    1 indexed General Plan PDF + 4 un-indexed state HCD compilations (absence evidence)
        (+ _fetch_log.jsonl provenance, incl. copy-provenance for the compilations)
text/   1 pdftotext sidecar for the General Plan
index.csv        §9 housing contract header (1 data row: the General Plan)
AVAILABILITY.md  what filed / not filed, how verified, the threshold rationale (READ FIRST)
CLAUDE.md        this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` | `mih_element` | `mih_annual_report` | `compliance_letter`
  (only `general_plan` is present here).
- `date` = General Plan **adoption** date (2022-03-22).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count (81).
- `format` = `text` (born-digital); `extraction_method` = `pdftotext` (plain, no `-layout` —
  the plan is multi-column, so reading-order extraction is cleaner than `-layout`).

## The one indexed doc
- **Emigration Canyon General Plan 2022** — adopted 2022-03-22 (while still a metro township),
  the first and current General Plan since 2017 incorporation. From MSD DocumentCenter
  (`View/252`), discovered via `msd.utah.gov/295/Emigration-Canyon-General-Plan-2022`. Seven
  chapters (Intro, Land Use & Character Areas, Transportation, Economic Development,
  Environment, Resilience & Infrastructure, Community Work Program). **No standalone MIH
  element** — housing appears only within Land Use / Economic Development. A print-layout
  version (`View/254`) and Appendix A-L (`View/253`) also exist on the MSD site; not retained
  (duplicate/supplementary), noted in `AVAILABILITY.md`.

## State HCD compilations — copied, not re-downloaded
Per the build instruction, the four statewide compilations were **copied sha256-verified from
`bluffdale_city_council/housing_plans/raw/`** (byte-identical; no re-download). Their
`_fetch_log.jsonl` entries preserve the **true `jobs.utah.gov` source URLs and the original
bluffdale `retrieved_utc` (2026-07-13)**, tagged `COPIED sha256-verified … NOT re-downloaded`:

| file | true source_url | sha256 (first 12) |
|---|---|---|
| hcd-23reports.pdf | jobs.utah.gov/housing/affordable/moderate/reporting/documents/23reports.pdf | 8e59bb717859 |
| hcd-24reports.pdf | …/documents/24reports.pdf | 53f4f9d9f8a7 |
| hcd-25reports.pdf | …/documents/25reports.pdf | 0b620618f448 |
| hcd-sb34.pdf | …/documents/sb34.pdf | 2712503323c8 |

Each was full-text searched for "Emigration" → **ABSENT in all four** (RY 2023, 2024, 2025,
SB 34 2019-2021). They are **retained un-indexed** (no `index.csv` rows) as **absence
evidence**; extraction was verified working via present neighbor cities (Draper, Cottonwood
Heights, Eagle Mountain, Bountiful). No per-city `text/` sidecar — Emigration has no page
range in any compilation.

## Regenerating / extending
- General Plan fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --name emigration-canyon-general-plan-2022.pdf --referer <MSD page> <DocumentCenter/View/252 URL>`.
- Sidecar: `pdftotext raw/emigration-canyon-general-plan-2022.pdf text/emigration-canyon-general-plan-2022.txt` (no `-layout`).
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- If Emigration Canyon ever crosses 5,000 pop, re-check the MSD site + the next `NNreports.pdf`
  compilation for a newly-filed MIH element / annual report.

## Do not
- Do not fabricate a MIH element/report — sub-threshold non-filing is the correct finding.
- Do not edit any existing Emigration Canyon dataset or the parent README/CLAUDE from here
  (the orchestrator owns the parent docs).
- Do not delete/normalize `raw/` originals (incl. the un-indexed absence-evidence compilations).
