# housing_plans/ — Kearns moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Kearns's **General Plan** + its **Moderate Income
Housing (MIH) element/plan** and adopting resolution (Utah Code 10-9a-403/408, HB 462 2022), plus
the **state HCD annual reporting** record. Purely **additive** — no existing Kearns dataset was
touched, and the parent `README.md`/`CLAUDE.md` are the orchestrator's to edit, not this folder's.
As-of 2026-07-13.

## Headline
Kearns is **NOT honest-empty and NOT below the reporting threshold.** It has a standalone adopted
MIH Plan (2022, corrected by Resolution 2023-01-02) and **files a 10-9a-408 report under its own
name every state year checked** (SB 34 2019–2021, RY 2023/2024/2025). Planning is **staffed by the
Greater Salt Lake MSD**, so the plan/resolution/General Plan live on `msd.utah.gov` (the city site
`kearns.utah.gov` is Cloudflare-blocked), but the **entity of record in the state compilations is
"Kearns" / "Kearns, Metro Township"** — it is not absorbed under an MSD umbrella entry. See
`AVAILABILITY.md` (READ FIRST) for the per-year presence table.

## Layout
```
raw/    8 PDFs: 4 fetched here from msd.utah.gov (General Plan + MIH Plan + adopting Resolution
        + Resilience/Infrastructure GP element) + 4 sha256-verified COPIES of the shared
        statewide HCD compilations (+ _fetch_log.jsonl, incl. copy-provenance rows)
text/   8 sidecars: 4 city/MSD docs + 4 state-compilation Kearns excerpts
index.csv             §9 housing contract header (8 rows)
AVAILABILITY.md       per-year presence + threshold/MSD-reporting status (READ THIS FIRST)
kearns_hcd_pagerange.py   in-folder helper: scan an HCD compilation for Kearns pages + extract sidecar
CLAUDE.md             this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` (2 — the 2020 GP + its Resilience/Infrastructure element) |
  `mih_element` (2 — the 2022 MIH Plan + adopting Resolution 2023-01-02) | `mih_annual_report`
  (4 — RY 2023/2024/2025 + SB 34 2019–2021). No `compliance_letter` (none published — honest
  absence, same as White City).
- `date` = adoption date (city/MSD docs) / filing-or-report year (state reports).
- `path` is dataset-relative **including `raw/`** (linter requirement).
- `pages` = PDF page count for whole-doc PDFs; for the state compilations it is Kearns's
  **physical (1-based) page range within the compilation** (the raw file is the full statewide PDF).
- `format` = `text` for all 8 rows (every doc is born-digital).

## Two source families
1. **MSD (CivicPlus).** Kearns's planning is **GSL-MSD-staffed**, so the housing/general-plan docs
   live on `msd.utah.gov/DocumentCenter/View/<id>/…`, discovered via the MSD **City-of-Kearns**
   page (`msd.utah.gov/239/City-of-Kearns` → `View/273` GP, `View/442` MIH Plan, `View/270`
   Resilience element). The **adopting/correcting instrument** (`View/738`, Resolution 2023-01-02)
   was found via the state reports' "Link to Ordinance or Resolution" field. The city site
   `kearns.utah.gov` is Cloudflare-blocked and was not used (not needed).
2. **State HCD** — statewide compilation PDFs `{23,24,25}reports.pdf` + `sb34.pdf`. No per-city
   file; Kearns's excerpt lives inside each compilation, bracketed by **Kaysville** (before) and
   **Layton** (after) and extracted to `text/kearns-<year>.txt` (bleed-verified: 0 neighbor
   strings).

## Provenance of the state HCD compilations (do NOT re-download)
The 4 `hcd-*.pdf` in `raw/` are **byte-identical sha256-verified copies** of
`bluffdale_city_council/housing_plans/raw/{hcd-23reports,hcd-24reports,hcd-25reports,hcd-sb34}.pdf`
(shared statewide PDFs, one per state, not city-specific). sha256:
- `hcd-23reports.pdf` 8e59bb71…e8ac · `hcd-24reports.pdf` 53f4f9d9…e38f
- `hcd-25reports.pdf` 0b620618…bd01 · `hcd-sb34.pdf` 27125033…e2e00
`raw/_fetch_log.jsonl` carries copy-provenance rows for these 4 with the **true**
`jobs.utah.gov/housing/affordable/moderate/reporting/documents/…` source URL and the original
bluffdale retrieval timestamps (2026-07-13). The `index.csv` `source_url` is the authoritative
jobs.utah.gov URL, re-fetchable.

## Key facts
- Kearns **present + reporting in every state year** (SB 34 2019–2021, RY 2023/2024/2025).
- The **MIH Plan (2022)** was "amended September 27th, 2022" (before the Oct 1 2022 HB 462
  deadline); **Resolution 2023-01-02** (9 Jan 2023) then inserts a statutory strategy option
  verbatim to secure HB 462 priority-funding consideration (DWS flagged the cite-not-quote defect
  22 Nov 2022 but had already found the plan compliant). Both are the metro-township-era Council.
- All 8 PDFs are **born-digital text** — the Kearns council-minutes OCR seam does NOT apply here.
- The 2020 **General Plan** keeps the MIH element **separate** (a standalone 2022 plan), unlike
  cities that embed it as a GP appendix.
- Filers of the state annual reports are GSL-MSD Long Range Planners (Morgan Julian 2024, Bianca
  Paulino 2025) — reported under "Kearns," not an MSD umbrella entity.

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --name <f> <url>`.
- State excerpts: `python3 kearns_hcd_pagerange.py raw/hcd-<yy>reports.pdf`  (scan/report the
  `kearns`-mention pages), then `python3 kearns_hcd_pagerange.py raw/hcd-<yy>reports.pdf
  text/kearns-<year>.txt <start0> <end0>` with the explicit 0-based range (bracket by
  Kaysville/Layton; verify 0 neighbor bleed). NOTE macOS has no `timeout` — do not wrap tools in one.
- Sidecars for born-digital docs: `pdftotext -layout raw/<f>.pdf text/<f>.txt`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next `scripts/build_cities_db.py`
  run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate: the MSD-hosted plan/resolution and MSD-staffed-but-filed-under-Kearns reports
  are the correct findings — not gaps to fill; the missing compliance letter is an honest absence.
- Do not edit any existing Kearns dataset or the parent README/CLAUDE from this folder.
- Do not re-download the HCD compilations (copy from bluffdale); do not delete/normalize `raw/`
  originals.
