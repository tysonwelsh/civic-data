# housing_plans/ — build notes

Additive dataset built by `expand-city-sources` **Source 2** (moderate-income housing plans +
annual reports + General Plan) for West Jordan City, Salt Lake County, Utah. As-of **2026-07-03**.

## What's here
- `raw/` — every PDF verbatim + `_fetch_log.jsonl` (polite_fetch provenance: url, status, bytes,
  sha256, retrieved_utc). Includes the **full statewide compilation PDFs** (`state-*reports.pdf`,
  `state-sb34.pdf`) as the raw originals.
- `text/` — extracted sidecars. For the state compilations, **only West Jordan's page range** is
  sliced into `westjordan-<year>.txt` / `westjordan-sb34.txt` (not the whole compilation).
- `index.csv` — 11 rows. Required cols `date,title,source_url,retrieved_date,format,extraction_method`
  + source-specific `doc_type`, `path`, `text_sidecar`, `notes`.
- `AVAILABILITY.md` — coverage, gaps, discovery method, extraction caveats.

## doc_type distribution (index.csv)
- `general_plan` — 3 (2023 General Plan; Ord 23-10 adoption; 2023 Future Land Use Map)
- `mih_element` — 2 (Ord 20-32 / 2020; current published element / 2026-04 upload)
- `mih_annual_report` — 6 (city 2020 report + Res 20-73; state 2023/2024/2025 compilations; SB 34)
- `compliance_letter` — 0 (none published standalone; see AVAILABILITY.md)

## City vs state
- **City site** (`westjordan.utah.gov`): the adopted **2023 General Plan** (+ adoption ordinance +
  FLUM), the **MIH element** (Ord 20-32 / current text), and the **2020** MIH annual report + Res 20-73.
  The "General Plan" nav link points to **amlegal codelibrary (403-blocked)** — the adopted PDF is the
  primary; amlegal not archived.
- **State** (Utah DWS/HCD, `jobs.utah.gov/housing/affordable/moderate/reporting/`): annual
  implementation reports for **2023/2024/2025** live only inside statewide **compilation** PDFs
  (`{23,24,25}reports.pdf`) — WJ sliced out per page range. Plus `sb34.pdf` SB 34 progress summary.

## How the state page ranges were found (reproducible)
1. `pdftotext -layout state-<yy>reports.pdf` → split on form-feed `\f` into pages.
2. Locate the West Jordan **section header** page (`West Jordan city` / `West Jordan\nType of
   Jurisdiction`) and the **next jurisdiction's** header page; WJ range = [WJ header, next header − 1].
3. `pdftotext -layout -f <first> -l <last>` → `text/westjordan-<year>.txt`.
4. **Neighbor-bleed grep** on each sidecar for West Haven / West Point / West Bountiful / West Valley /
   Woods Cross = **0** (only stray in-narrative mentions, no neighboring section owned).
   Page ranges: 2023 pp.1044–1059 · 2024 pp.968–989 · 2025 pp.1224–1248 · sb34 pp.189–191.

Two-column form scrambling under `-layout` means the WJ header sometimes shares its top page with the
prior jurisdiction's tail (≤2 lines) — accepted and noted; the *next* header cleanly bounds the end.

## Linkage to the rest of the repo
- MIH element / annual reports cite **council ordinances/resolutions** (Ord 20-32, Res 20-73, and — in
  the 2025 state compilation — Ords 25-24 / 25-25 June 2025). These join to
  `meeting_minutes/all_votes.csv` and the `db/` motion layer by **adoption date + ordinance/resolution
  number** if a downstream ordinance-linkage pass is run (Source 3).
- The **2023 General Plan / FLUM** is the land-use context for Planning Commission / RDA land-use
  motions already in `planning_commission/` and `db/`.

## Regenerating
- Re-fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw/
  --now <ISO> --referer <page> <url>` (or `--probe <url>`).
- Re-slice a state compilation: `pdftotext -layout -f <first> -l <last> raw/state-<yy>reports.pdf
  text/westjordan-<year>.txt`; re-verify the neighbor-bleed grep.
- Screen: `python3 ../../.claude/skills/audit-city-data/scripts/screen_corpus.py text/`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .`

## Caveats
- **2023 General Plan text** has letter-spacing extraction artifacts (designed layout) — quote from the
  **raw PDF**, not the sidecar. FLUM is image-only.
- State compilation "date" = the report year the state labels (23/24/25 = filings submitted in
  2023/2024/2025). SB 34 date = latest year tracked (2021).
- `city-moderate-income-housing-plan-2026.pdf` date is its **upload** date (2026-04); its content is the
  2020 element narrative, so do not read it as a 2026 re-adoption.
