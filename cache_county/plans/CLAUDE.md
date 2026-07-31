# cache_county/plans — how to use this module

The **governing planning documents** for Cache County, as a **searchable plain-text
corpus** for growth / housing / development questions. Self-contained: raw PDFs,
extracted text, and a manifest. Nothing here feeds gov.db/cities.db — a document layer.

## Layout

- `raw/<stem>.pdf` — source PDF (all 6 are <=33MB, so all stored; none link-only).
- `text/<stem>.txt` — pypdf-extracted plain text of every PDF. **The searchable layer.**
- `index.csv` — the manifest:
  `doc_type,title,adopted_date,jurisdiction,path,text_path,format,source_url,notes`.
  `path`/`text_path` are blank for the one link-only (StoryMap) row.
- `SOURCES.md` — provenance, publishers, honest gaps.

## Which document for which question

- **Current countywide growth vision:** **Cache County General Plan (2023)** — adopted
  2023-02-28 via the *Imagine Cache* process; supersedes the 1998 plan. Published as a
  **web StoryMap only** (`format=storymap`, link-only, NO text sidecar) — open the
  `source_url` to read it; it is not grep-able here.
- **Prior/superseded general plan (full text):** **Countywide Comprehensive Plan (1998)**
  — 346 pp, the statutory general plan in force 1998–2023; grep `text/comp_plan_1998.txt`.
- **Moderate-income / affordable housing obligations & strategies:** **MIH Plan — 2019
  Update (2023 Amendment)** — the current statutory MIH element.
- **Natural-resource / public-lands planning:** **Resource Management Plan (CRMP, 2017)**.
- **Regional (bi-state) growth scenarios:** **Envision Cache Valley — Final Report**.
- **Corridor / small-area land use:** **Cache Valley South Corridor Plan**.
- **Trails / active transportation:** **Trails & Active Transportation Master Plan (2017)**.

## doc_type vocabulary

`general_plan`, `moderate_income_housing`, `resource_management_plan`, `regional_vision`,
`small_area_plan`, `transportation_plan`. (Open set — extend for new types.)

## Cardinal rules (inherited from repo root)

- **Never fabricate.** Uncertain adoption dates are left **blank** with the year signals
  noted (Envision Cache Valley, South Corridor Plan) rather than asserted. `index.csv`
  lists only documents actually retrieved (or, for the StoryMap, verified live).
- **Text is derived; PDFs/URLs are canonical.** Regenerate a `text/` file by re-running
  pypdf on the `raw/` PDF.
- Publisher is **cachecounty.gov** (Development Services / CPDO / Zoning) for all PDFs;
  the 2023 General Plan lives on **storymaps.arcgis.com**.

## Scope note

Growth/housing-relevant county plans are the target and are complete for the
currently-adopted set. The 2023 General Plan being **StoryMap-only** is the one honest
text-coverage gap (no PDF exists to extract). Township/municipal plans belong to the
member cities, not this county module. Small-area studies beyond the South Corridor Plan
are a logged follow-up (SOURCES.md).
