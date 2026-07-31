# housing_plans/ — Town of Alta moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Alta's **General Plan** and its **(legacy, embedded)
moderate-income-housing element**, plus the checked-and-absent **state HCD reporting** record.
Purely **additive** — no existing Alta dataset was touched. As-of 2026-07-13.

**READ `AVAILABILITY.md` FIRST.** This is a **near-empty-by-design** dataset: a ~380-person resort
town that has a General Plan MIH element but is **below the population threshold** for modern state
MIH annual reporting, so it is **absent from every state HCD compilation**. That absence is the
correct, honest finding — not a gap.

## Layout
```
raw/    1 town General Plan PDF (born-digital) + 4 state HCD compilation PDFs (copied,
        sha256-verified, UN-INDEXED — reference evidence for the "Alta absent" finding)
        + _fetch_log.jsonl provenance
text/   pdftotext -layout sidecar of the General Plan (1 file)
index.csv         §9 housing contract header (2 rows, both -> the one General Plan PDF)
AVAILABILITY.md   what was checked, per-year state presence/absence, exemption reasoning (READ FIRST)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` used here: `general_plan`, `mih_element`. (No `mih_annual_report` / `compliance_letter`
  rows — Alta files none; see AVAILABILITY.md.)
- **Both rows point at the SAME raw PDF** (`raw/alta-general-plan-2016.pdf`): Alta's MIH element is
  **Section 3.18** of the General Plan, not a standalone file. `pages` = 38 for the whole plan,
  13 for the element's printed page. **Do NOT double-count these as two documents/files.**
- `path` is dataset-relative including `raw/` (linter requirement); `format=text`.

## The two source families

1. **Town of Alta** (`townofalta.utah.gov`, Juniper WordPress CMS; docs in GCS bucket
   `juniper-media-library` tenant 130). The `/meetings/` app is unscrapable JS, but the static
   `/planning-commission/` and `/general-plan-studies/` pages carry **direct GCS PDF links**. The
   current **General Plan (Updated 2016)** was retrieved there; it embeds the MIH element as
   Section 3.18 (cites the pre-2019 statute "Title 10 ch. 9 pt. 307"; frames MIH as **employee
   housing** under the 1989 zoning ordinance). No standalone MIH plan or affordable-housing study
   exists among the town's ~25 special plans/studies.
2. **State HCD** (Utah DWS, `jobs.utah.gov`) — the four statewide compilations
   `{23,24,25}reports.pdf` + `sb34.pdf` were **copied sha256-verified from
   `bluffdale_city_council/housing_plans/raw/`** (not re-downloaded; provenance + true
   `jobs.utah.gov` URLs + original retrieval timestamps recorded in `raw/_fetch_log.jsonl` with a
   `copied_from` note). **Town of Alta is present in NONE** (TOCs run Alpine → American Fork →
   Bluffdale; SB34 order 1.ALPINE 2.AMERICAN FORK 3.BLUFFDALE). Hence no `text/alta-*.txt` sidecar
   and no annual-report index rows. The compilation PDFs are kept **un-indexed in `raw/`** so the
   absence is independently re-verifiable from this folder.

## Key facts
- Alta **HAS** a moderate-income-housing element (legacy, embedded General Plan Section 3.18) — but
  publishes/files **NO** modern (HB462 / 10-9a-408) standalone element, annual report, or HCD
  compliance letter. It is **below the state MIH population-reporting threshold** (~380 pop).
- The General Plan PDF is **born-digital text** (`pdftotext -layout`, `format=text`); the
  council-minutes OCR seam does NOT apply here.
- Only whole-word "Alta" hit in the compilations is **"Alta View"** (a Sandy school), not the town;
  no "Alta Canyon" content either.

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --name <f>.pdf <URL>`.
- Sidecar: `pdftotext -layout raw/alta-general-plan-2016.pdf text/alta-general-plan-2016.txt`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- On a future refresh, re-check the `/planning-commission/` + `/general-plan-studies/` pages for a
  NEW General Plan / a first HB462 MIH element, and re-grep any newer `NNreports.pdf` compilation
  for a first "Town of Alta" entry (would appear if the town ever crosses the reporting threshold).
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate an annual report / compliance letter — Alta files none; the absence is the record.
- Do not double-count the two index rows as two files (same raw PDF; the element is a plan section).
- Do not edit any existing Alta dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals, including the un-indexed state-compilation evidence PDFs.
