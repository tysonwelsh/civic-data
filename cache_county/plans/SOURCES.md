# cache_county/plans — SOURCES & provenance

## Publishers

- **cachecounty.gov** — Development Services (`/devserv/`), the Community & Planning
  Development Office (`/cpdo/`, Long Range Planning), and Zoning (`/pz/`). Hosts every PDF
  in this module.
- **storymaps.arcgis.com** — the 2023 General Plan is published here as an interactive
  web StoryMap (no PDF equivalent).

## Documents (retrieved 2026-07-20)

| stem / row | source_url | pages | notes |
|---|---|---|---|
| `comp_plan_1998` | cachecounty.gov/assets/department/zoning/generalplan/COMPLETE_CacheCountyCompPlan_1998.pdf | 346 | prior statutory general plan |
| Cache County General Plan (2023) | storymaps.arcgis.com/stories/4b0f00edf47a4665992fb12bb5835fde | — | **StoryMap, link-only**; adopted 2023-02-28 |
| `mihp_2019update_2023amendment` | cachecounty.gov/assets/department/devserv/CacheCo_MIHP%202023%20Amendment.pdf | 37 | current MIH plan (2019 Update, 2023 Amendment) |
| `resource_management_plan_2017` | cachecounty.gov/assets/department/devserv/DraftCacheCountyCRMP.pdf | 123 | CRMP; county-hosted file filename-labeled "Draft" |
| `envision_cache_valley_final` | cachecounty.gov/assets/department/cpdo/Envision%20Cache/ECV%20Final%20Report.pdf | 60 | bi-state regional vision |
| `cache_valley_south_corridor_plan` | cachecounty.gov/assets/department/devserv/zCWP/Cache Valley South Corridor Plan.pdf | 49 | small-area corridor plan |
| `trails_active_transport_master_plan_2017draft` | cachecounty.gov/assets/department/trails/pdf/CCTATMP_Nov17_DRAFT.pdf | 93 | active-transportation master plan (2017 draft) |

All PDFs are born-digital and extract clean text with pypdf (no OCR needed). All are
<=33MB so all are stored in `raw/` (repo policy link-only threshold is 50MB).

## Retrieval method

Discovered via `cachecounty.gov/pz/current/general-plan.html`, `/cpdo/long-range-planning/`,
`/devserv/`, and targeted search. The 1998 plan and 2023 GP StoryMap are the general-plan
page's canonical links; the MIHP, CRMP, corridor, trails, and Envision reports were found
on the Development Services / CPDO document trees.

Regenerate text: `python3 -c "from pypdf import PdfReader; open('text/<stem>.txt','w').write('\n'.join((p.extract_text() or '') for p in PdfReader('raw/<stem>.pdf').pages))"`

## Honest gaps

- **The current General Plan (2023) has NO extractable text here** — it is a web StoryMap
  only; the county publishes no PDF. Cataloged link-only; open `source_url` to read it.
- The CRMP is the **county-hosted file labeled "Draft"** in its filename (the general-plan
  page lists the 2017 RMP as Approved; the county's downloadable file retains the draft
  filename). Text is complete (123 pp).
- **Uncertain dates left blank** rather than fabricated: Envision Cache Valley (references
  data through ~2009–2010) and the South Corridor Plan (~2010).
- Township/municipal general plans are out of scope (they belong to member-city repos).
  Additional small-area/community studies beyond the South Corridor Plan are a logged
  follow-up, not yet ingested.
