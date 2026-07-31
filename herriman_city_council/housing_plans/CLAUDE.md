# housing_plans/ — Herriman City (build notes)

Moderate-income housing (MIH) plans + General Plan dataset, built 2026-07-13 by the
`/expand-city-sources` skill (source type 2). §9 contract `index.csv`
(`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`);
raw originals verbatim under `raw/` (+ `_fetch_log.jsonl` for the city/Wayback fetches),
text sidecars under `text/`. 11 index rows: 3 `general_plan`, 2 `mih_element`,
6 `mih_annual_report` (2020, 2021 city-filed; 2023/2024/2025 compilation excerpts;
SB 34 2019–2021), 0 `compliance_letter` (honestly absent — see AVAILABILITY.md).

## The Herriman shape of the MIH story

- **General Plan 2022 "Herriman Next"** (adopted **2022-07-13**) is current; it replaced
  the 2013 **"Herriman 2025" General Plan Amendment** (2025 = the plan's horizon YEAR —
  do not read `2025GPAmend.pdf` as a 2025 document; it is the retained predecessor).
  The GP adopts its elements separately — the MIH element is NOT a GP chapter here
  (unlike Murray).
- The MIH element is a standalone **Moderate Income Housing Plan**: adopted
  **2019-11-13**, then updated under **HB 462** by **Ordinance 2022-38 on 2022-09-28**
  (PC recommended 5-0 on 2022-09-01) — three days before the Utah Code 10-9a-403 Oct 1
  2022 deadline. The 2022 PDF is the signed ordinance + the amended plan (cover reads
  "Adopted November 13, 2019 / Amended September 28, 2022"); 6 strategies A, B, E, F,
  G, K.
- Annual **10-9a-408 implementation reports**: the city posted its own filed forms for
  **2020** and **2021** (DWS-HCD 899), then stopped; **2023/2024/2025** exist only in the
  state's compilation PDFs (2024/2025 filed by Susan Petheram, Senior Planner — FFKR,
  the city's planning consultant). Herriman filed **every year checked**: 2019–2021 (per
  the SB 34 summary) + 2023–2025.

## Acquisition + provenance

- **City documents** (GP 2022, 2030 Land Use Map, 2025GPAmend, MIH Plan 2022, 2021
  report): fetched 2026-07-13 from `herriman.gov/uploads/files/<id>/…` via
  `polite_fetch.py` (browser UA, Referer = `/master-plans`) — see `raw/_fetch_log.jsonl`.
  Discovery was sitemap-first (`sitemap-pages.xml`, 238 URLs) → the `/general-plan` and
  `/master-plans` pages, which carry every plan PDF; no housing-specific page exists.
- **Wayback recoveries** (2019 MIH Plan, 2020 annual report): the originals lived on
  pre-migration `herriman.org/uploads/files/{1239,1242}/…` and **404 on the live site**;
  fetched from the 2021-08-10 Internet Archive captures (`id_` raw form) via
  `polite_fetch.py`. `source_url` in index.csv is the Wayback URL; the original city URL
  is in `notes`.
- **State compilations** (`hcd-23reports.pdf`, `hcd-24reports.pdf`, `hcd-25reports.pdf`,
  `hcd-sb34.pdf`): **local copies from `bluffdale_city_council/housing_plans/raw/`**
  (identical bytes — sha256 verified against bluffdale's `_fetch_log.jsonl`; original
  polite fetch from `jobs.utah.gov` on 2026-07-12), to avoid re-downloading ~25 MB of
  identical statewide PDFs. `source_url` in index.csv is the true jobs.utah.gov origin;
  `retrieved_date=2026-07-12` is the original fetch date. These four files are NOT in
  this dataset's `_fetch_log.jsonl` (that log covers only the Herriman + Wayback fetches).

## Extraction notes / caveats

- All PDFs are born-digital **except the 2022 MIH Plan/Ordinance 2022-38** (`/5826/`), a
  scan with an embedded **Acrobat Paper Capture OCR layer** — `pdftotext` extracts that
  layer. Expect ligature dropouts ("Afordable", "defned") and OCR slips (the roll call
  prints "Sherrie **Ohm**" for Ohrn). Never quote it verbatim without checking the raw
  PDF. The state-filed copy at `herriman.org/uploads/files/3067/` (same filename, still
  live) is the SAME 23-page document with the original Canon-scanner OCR layer — /5826/
  (the current master-plans link, cleaner re-OCR) is the retained copy; diffed page-by-
  page 2026-07-13, text differences are OCR noise only.
- The 2030 Land Use Map sidecar carries legend/label text only; the map is graphical —
  use the raw PDF (vision) for spatial questions.
- **Compilation page ranges are physical (1-based PDF) pages**. Herriman brackets: Heber
  City before, Highland after, all years.
  - **2023** (pp 231–249): no per-city title pages; the TOC's printed numbers are
    physical−1 (TOC "230" = physical 231). Herriman starts **mid-page** on p231;
    `text/herriman-2023.txt` is mechanically trimmed to start at the
    `Herriman`/`Type of Jurisdiction` header (Heber tail removed) — a boundary trim, no
    content edits. Ends clean (Highland tops p250).
  - **2024** (pp 209–223): `Herriman city` header page format; **p223 is a shared
    boundary page** (Herriman's closing lines + the `Highland city` header in parallel
    columns) — `text/herriman-2024.txt` keeps it verbatim, so the last page carries
    Highland-header bleed. The 2024 form layout is two-column and `pdftotext -layout`
    interleaves columns — read for content, not layout fidelity.
  - **2025** (pp 286–302) and **SB 34** (pp 53–54): clean page boundaries, no bleed.
- The 2023 compilation cites Herriman's plan at `herriman.org/uploads/files/3067/…` —
  corroborates the state-filed-copy identity above.
- `screen_corpus.py` (2026-07-13): 11/11 files clean — no garbling/stubs/dict outliers;
  flags investigated benign (repeated lines = the GP's "ADOPTED JULY 13, 2022" running
  footer + repeated HCD form questions; hyphen breaks = ordinary typography in the 2013
  plan; ends-mid = page-footer tails).

## Linkage

- **Ordinance 2022-38 was adopted at the 2022-09-28 council meeting**, which exists in
  `meeting_minutes/all_votes.csv` — but the minutes' motion texts that night are bare
  ("approve", "approve the consent agenda as written") and never print the ordinance
  number, so the date is the join key and the **ordinance's own printed roll call**
  (Palmer, Henderson, Hodges, Ohrn, Shields — TOTALS 5, checked 2026-07-13) is the
  authoritative record of the adoption vote. That roll call is also a source-level
  confirmation of the **mayor-votes** structural fact (see the city CLAUDE.md
  correction). The PC's recommendation IS directly in
  `planning_commission/all_votes.csv`: 2022-09-01 (an off-Wednesday Thursday meeting),
  "recommend approval to City Council of item 5.1 … technical update to the
  Moderate-Income Housing Element of the General Plan".
- No formal linkage columns in this dataset (that's `ordinances/`); dates + the ordinance
  number are in the index for joining.
- Annual-report years join to housing/land-use motions of the same year; the 2024/2025
  reports narrate specific council/PC actions (MDA amendments, ADU tracking since 2021,
  the 12600 South corridor) useful as context for `v_landuse_outcomes` queries.
