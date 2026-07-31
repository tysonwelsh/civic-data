# housing_plans/ — Midvale moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Midvale City's **General Plan** + its **Moderate
Income Housing (MIH) element** and the **state HCD annual reporting** record (Utah Code
10-9a-403/408, HB 462 2022). Purely **additive** — no existing Midvale dataset was touched.
As-of **2026-07-13**. Read `AVAILABILITY.md` first for the coverage/gap record.

## Layout
```
raw/    8 born-digital PDFs verbatim (+ _fetch_log.jsonl provenance)
        4 city docs (fetched) + 4 state compilations (copied sha256-verified from bluffdale)
text/   pdftotext -layout sidecars: 4 city docs + 4 state-compilation Midvale excerpts
index.csv         §9 housing contract header (8 rows)
AVAILABILITY.md   what filed / not filed, how verified (READ THIS FIRST)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` | `mih_element` | `mih_annual_report` | `compliance_letter`.
  (Midvale has no `compliance_letter` — the city publishes none; see AVAILABILITY.md.)
- `date` = adoption date (city docs) / filing-or-report year (state reports).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc city PDFs; for the state compilations it is Midvale's
  **physical page range within the compilation** (the raw file is the full statewide PDF).
- `repository` = "Midvale City (midvale.utah.gov Revize Document Center)" or
  "Utah DWS HCD (jobs.utah.gov)".

## Two source families
1. **City** (`midvale.utah.gov`, Revize CMS → `cms1files.revize.com/midvale/…`). Discovered via
   the community-development landing → `redevelopment_agency/housing/housing_plan.php` (the MIH
   element) and `community_development/planning_and_zoning/master_plans_and_studies.php` (the
   General Plan + 2019 Housing Plan). The 2022 MIH Element was adopted by the **RDA Board as a
   General Plan amendment on 2022-09-20**, and lives as a standalone element PDF (the 2016 General
   Plan predates HB 462). Revize URL quirks: encode `%20`/`%26`; master-plans bare filenames
   resolve at the **site root**, not a Master-Plans folder; filenames truncate to ~25 chars.
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. There is **no
   per-city file**; Midvale's excerpt lives inside each. The four compilations were **copied
   sha256-verified** from `bluffdale_city_council/housing_plans/raw/` (shared statewide files —
   NOT re-downloaded); `source_url`/`retrieved_date` record the true jobs.utah.gov origin, and the
   `_fetch_log.jsonl` entries carry a copy note. Page ranges were located by identity-block /
   header content-scan (see the per-year quirk table in AVAILABILITY.md) and extracted to
   `text/midvale-<year>.txt`, grep-verified for zero neighbor-city bleed.

## Key facts
- **Midvale is present and reporting in every state year checked** (RY 2023/2024/2025 + SB 34
  2019–2021) — it is well above the reporting threshold. Major Transit Investment Corridor = YES
  (TRAX); 6 of 24 MIH strategies selected, including a station-area plan (strategy Q / HTRZ).
- All 8 PDFs are **born-digital text** (`pdftotext -layout`, `format=text`).
- Two published copies of the 2022 MIH element (`Genera` = city-linked; `for We` = website variant)
  are the **same adoption**, retained both. The 2019 Housing Plan's RDA-folder copy
  (`…Adopt.pdf`) is **byte-identical** to the master-plans copy — fetched once.

## Regenerating / extending
- City raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --batch <urls.csv>`.
- Sidecars: `pdftotext -layout raw/<f>.pdf text/<f>.txt`; state excerpts use `-f <start> -l <end>`
  with the physical ranges in `index.csv` `pages`.
- Screen: `python3 ../../.claude/skills/audit-city-data/scripts/screen_corpus.py text`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: "the city publishes no annual-report copy / compliance letter; it files with
  the state" is the correct finding, not a gap to fill.
- Do not edit any existing Midvale dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals or re-download the shared state compilations.
