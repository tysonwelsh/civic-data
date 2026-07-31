# housing_plans/ — Draper moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Draper's **General Plan** + **MIH element**
(Utah Code 10-9a-403, HB 462 2022) + **annual 10-9a-408 reports**, city- and state-side.
Purely **additive** — no existing Draper dataset was touched. As-of 2026-07-13.

## Layout
```
raw/    10 born-digital PDFs verbatim (+ _fetch_log.jsonl provenance incl. Wayback + copy records)
text/   12 pdftotext -layout sidecars (whole docs + page-range excerpts)
index.csv         §9 housing contract header (12 rows)
AVAILABILITY.md   what exists / what doesn't, per-year state-compilation table (READ FIRST)
unrecovered.csv   the 2021 annual report (genuinely unrecoverable — see row)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` ∈ `general_plan` | `mih_element` | `mih_annual_report` (no
  `compliance_letter` — Draper posts none; see AVAILABILITY.md).
- `pages` = whole-PDF page count, or the **physical page range** for excerpt rows
  (state compilations AND the two `mih_element` rows — see below).
- Two rows deliberately share a `path` with another row: Draper publishes **no
  standalone MIH-element PDF**, so the `mih_element` rows are page-range excerpts of
  retained raws (the 2022 report's Appendix A, pp 13–42; the General Plan's Chapter 4,
  pp 20–27), each with its own text sidecar.

## Three source families
1. **City, live** (`draperutah.gov`, custom Azure-edge CMS; media items at
   `/media/<hash>/<slug>.pdf` — hashes are unguessable, discover via pages/sitemap, and
   the CMS keeps **only the newest** MIH report online). General Plan + 2025 report.
2. **City, Wayback-recovered** — the 2020/2022/2023/2024 annual reports died in the
   CivicPlus→custom-CMS migration; recovered via CDX prefix scans of
   `draperutah.gov/DocumentCenter/` and `/media/` (capture timestamps in row notes;
   fetches in `raw/_fetch_log.jsonl` with the `web.archive.org/web/<ts>id_/` URL).
   **Gotcha:** some Wayback captures are payload-truncated at exactly **1 MiB** —
   always check `%%EOF` and prefer a later capture (the 2024 report needed this; the
   2021 report died on it — both captures truncated → `unrecovered.csv`).
3. **State HCD** (`jobs.utah.gov` compilations `{23,24,25}reports.pdf` + `sb34.pdf`) —
   **NOT re-downloaded**: byte-identical local copies of
   `bluffdale_city_council/housing_plans/raw/hcd-*.pdf` (sha256-verified against
   bluffdale's `_fetch_log.jsonl`; copy records appended to this dataset's fetch log
   with the true jobs.utah.gov `source_url` and the original 2026-07-12 retrieval).
   Draper page ranges bracketed by the alphabetical neighbors (Cottonwood Heights ←
   Draper → Eagle Mountain); per-year layout quirks (2023 shared pages, 2024 2-up
   column interleave) documented in row notes + AVAILABILITY.md.

## Key facts
- **MIH element = General Plan Housing chapter**, adopted by **Ordinance #1561
  (2022-09-20)** and amended by **Ordinance #1623 (2024-09-17**, strategy E added / L
  removed per the 2025 state filing**)** — both enacting votes are in
  `meeting_minutes/all_votes.csv` (4-0 each; 1561 with Green absent).
- Draper is **present in every state filing year**: SB 34 (2019–21) + 2023/2024/2025.
- All 10 raw PDFs are born-digital text (`format=text`, `pdftotext -layout`); corpus
  screened clean (hyphen/repeated-line flags = justified text + form boilerplate).
- The General Plan retained here is the **current amended edition** (adoption
  2019-11-19, amendments table through Dec 2025); superseded editions live in Wayback
  only (see AVAILABILITY.md).

## Regenerating / extending
- City fetches + Wayback recoveries: `scripts/polite_fetch.py` (see `raw/_fetch_log.jsonl`).
- Excerpt sidecars: `pdftotext -layout -f <start> -l <end> raw/<file>.pdf text/<name>.txt`.
- Screen: `python3 .claude/skills/audit-city-data/scripts/screen_corpus.py text/`.
- Validate: `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- Feeds `cities.db` `document`/`fts_*` on the next `scripts/build_cities_db.py` run
  (NOT run by this build — out of scope).

## Do not
- Do not fabricate: no compliance letter and no 2021 report are honest findings.
- Do not edit any existing Draper dataset or the parent README/CLAUDE from here.
- Do not delete/normalize `raw/` originals; the truncated-capture lesson says verify
  `%%EOF` on anything Wayback-sourced before trusting it.
