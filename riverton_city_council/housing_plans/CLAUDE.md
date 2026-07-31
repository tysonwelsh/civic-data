# housing_plans/ — Riverton City (build + linkage notes)

**Source type 2** (moderate-income housing plans + general plan) of the `expand-city-sources`
skill. Additive dataset; built 2026-07-13. Nothing in any existing Riverton dataset was touched.

## Contents (8 index rows, 8 raw PDFs)

- **general_plan** (1) — `raw/riverton-general-plan.pdf`: the city's General Plan published as a
  single-page Land Use Element map (amended 2020-08-18, revision 2022-03-08). Land-use context.
- **mih_element** (1) — `raw/riverton-city-annual-moderate-income-housing-plan-2024.pdf`: the
  Moderate Income Housing **Implementation Plan 2020-2024** (strategies matrix approved by the
  City Council). This is the current substance of the MIH element of the General Plan.
- **mih_annual_report** (6):
  - City-filed DWS-HCD 899 forms: `…report-2020.pdf` (RY 2020), `…report-2021.pdf` (RY 2021).
  - State statewide-compilation excerpts: `hcd-23reports.pdf`, `hcd-24reports.pdf`,
    `hcd-25reports.pdf` (annual RY 2023/2024/2025), `hcd-sb34.pdf` (SB 34 progress summary
    2019-2021). Whole compilations retained; Riverton's page range recorded in `index.csv.pages`
    and extracted to a `text/riverton-<year>.txt` sidecar.
- **compliance_letter** (0) — Riverton does not post a standalone HCD Notice-of-Compliance letter
  (unlike Bluffdale). Not indexed; not an honest gap (the state publishes only compilations here).

## State-compilation provenance — LOCAL COPIES (do not re-download)

`hcd-23reports.pdf`, `hcd-24reports.pdf`, `hcd-25reports.pdf`, `hcd-sb34.pdf` were **copied**
from `bluffdale_city_council/housing_plans/raw/` — they are the identical statewide PDFs (one
file serves every city). Each was **sha256-verified byte-identical** to Bluffdale's copy before
use:

| File | sha256 | true source_url |
|---|---|---|
| hcd-23reports.pdf | 8e59bb71…e01e8ac | jobs.utah.gov/…/reporting/documents/23reports.pdf |
| hcd-24reports.pdf | 53f4f9d9…241ae38f | jobs.utah.gov/…/reporting/documents/24reports.pdf |
| hcd-25reports.pdf | 0b620618…41bd6b01 | jobs.utah.gov/…/reporting/documents/25reports.pdf |
| hcd-sb34.pdf | 27125033…a163e2e00 | jobs.utah.gov/…/reporting/documents/sb34.pdf |

`raw/_fetch_log.jsonl` carries the **original** jobs.utah.gov fetch record (url, sha256,
`retrieved_utc` 2026-07-13T03:31Z — Bluffdale's fetch) plus a `note` marking each as a local copy.
`index.csv` `source_url` is the true jobs.utah.gov URL; `retrieved_date` is 2026-07-13.

## Page-range location method (state compilations)

Riverton falls alphabetically between **Riverdale** and **Roy**. Ranges were pinned by
`pdftotext` per-page scan and bracketed by the neighbor city headers:

- **2023** (`23reports.pdf`, 1109 pp): no per-city title pages; TOC printed page = physical − 1.
  Riverton TOC printed 609 → **physical 610–616** (Roy printed 616 = physical 617).
- **2024** (`24reports.pdf`, 1030 pp): `'<City> city'` section headers, 2-col interleave; TOC
  printed numbers (Riverton 1152) **exceed the 1030 physical page count**, so located by content
  scan → **physical 577–583** (`Roy city` header on physical 584).
- **2025** (`25reports.pdf`, 1303 pp): TOC printed 728 → **physical 731–740** (offset +3; Roy at
  physical 741).
- **sb34** (`sb34.pdf`, 199 pp): `RIVERTON, CITY` on **physical page 118** only (Riverdale p117,
  Roy p119).

Each sidecar was grep-verified: contains "Riverton", **zero** Riverdale/Roy header bleed.

## Extraction

- Every raw PDF is born-digital → `pdftotext -layout`, `format=text`. No OCR / vision needed.
- `screen_corpus.py` on `text/`: clean (0 dict/split/weird-char/read-error outliers). Advisory
  `hyphen_breaks` / `repeated_line` / `ends_mid` flags are expected DWS-HCD web-form + excerpt
  artifacts, not defects.

## Linkage to the rest of the repo

- Not motion-linked (housing plans have no §9 motion-linkage columns — that is the ordinances
  dataset). The `document` catalog in `cities.db` picks up these rows via `index.csv` on the next
  `scripts/build_cities_db.py` run (NOT run by this build, per instructions).
- The MIH strategies here explain land-use motions in `meeting_minutes/all_votes.csv` (Western
  Commercial District Plan, 12600 South Redevelopment Area, ADU ordinances, Redwood Rd corridor).
- Adoption facts (element last adopted **October 2019**; Mayor Trent Staggs; preparer Jason
  Lethbridge, Development Services Director) come straight from the annual-report forms.

## Honest gaps (see AVAILABILITY.md)

- **Oct-2019 original MIH element PDF**: live URL 404s; only Wayback 200 is a Common-Crawl
  1-MiB-truncated corrupt partial → not retained. Superseded by the 2020-2024 implementation plan.
- **RY 2019 / RY 2022 city-filed forms**: not posted at the city (probe `Content-Length: 0`);
  RY 2022+ covered by the state compilations instead.
