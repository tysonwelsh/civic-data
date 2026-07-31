# Housing Authority (Housing Connect / HACSL) — sources & provenance

**Body:** Board of Commissioners of the **Housing Authority of the County of Salt Lake**
(dba **"Housing Connect"**; legacy acronym **HACSL / HASLC**). A **separately-incorporated
public entity** — NOT part of the Salt Lake County Council's Legistar. Seven commissioners,
each appointed by the Salt Lake County Mayor; the board sets policy and provides fiscal
oversight for county-wide affordable-housing development and management. Regular meetings:
**third Wednesday, 11:30 a.m.**, Bud Bailey Apartments, Bldg C Classroom, 3970 S Main St,
South Salt Lake. Growth relevance: develops/owns/manages affordable housing county-wide
(project-based vouchers, RAD conversions, acquisitions, new construction, MTW plans).

## Minutes source — housingconnect.org (NOT PMN)

The agency posts approved Board minutes as PDFs on its own website. They are not browsable
from a listing page, but are enumerable via the site's **WordPress media REST API**:

```
https://housingconnect.org/wp-json/wp/v2/media?search=minutes&per_page=100&_fields=id,source_url,date
```

Board-of-Commissioners minutes are the PDF items whose filename contains `board`/`commission`
+ `minute`. (The API also returns `.docx` duplicates of many months — skipped; the PDF is
canonical.) `source_url` is stored verbatim per meeting in each md header and in
`minutes_index.csv`. The WordPress media `id` is used as the stable `<id>` in raw filenames.

### Utah Public Notice (PMN) public body 2535 — checked, NO minutes
The task pointed at PMN **public body 2535** ("Housing Authority Board"):
`https://www.utah.gov/pmn/list/notices.html?id=2535&page=300` (full history 2009–2026 in one
GET). It was crawled and audited. For this body PMN carries **only** meeting **agendas**,
**completed board packets**, **public notices**, and **audio recordings** — attachment types
observed are `Audio Recording`, `Other`, `Public Information Handout`. **No attachment is a
standalone approved-minutes document.** PMN is therefore NOT the minutes source here; it is
recorded as a provenance note only. (The same board sits as **HASLC / HAME / HDC** — the
authority and its two instrumentalities, Housing Assistance Management Enterprise and Housing
Development Corporation — in a single joint meeting; the housingconnect.org minutes are the
combined Board-of-Commissioners record.)

## Coverage

- **68** meetings converted to searchable markdown, **2020-01-15 → 2025-11-19** (dense monthly
  cadence; includes special/annual sessions).
- **1 honest gap:** `2021-12-15` — the posted PDF is **image-only** (pypdf extracts 0 chars).
  Raw retained (`raw/2021-12-15_2945_minutes.pdf`); md skipped; logged in `minutes_index.csv`
  with `minutes_status=image-only`. (Re-OCR is a future task — see repo `TODO.md`.)
- Pre-floor minutes (2019, 11 PDFs) exist on the site but are **below the repo 2020 data
  floor** and were not ingested.

## Extraction method

- `build.py` — enumerate (WP API) → download board minutes PDFs to `raw/<date>_<id>_minutes.pdf`
  → `pypdf` text → `minutes/<year>/<date>_housing_authority.md` (front-matter header) →
  `minutes_index.csv`. **Meeting date is parsed from the PDF body**, never the filename:
  several 2025 filenames encode the *finalized/approval* date, not the meeting date
  (e.g. `...JUN-26-Aug-2025.pdf` = the **June 18, 2025** meeting). All dates were cross-checked
  against the in-document header ("… OF THE BOARD OF COMMISSIONERS  <Month D, YYYY>").
- `extract_votes.py` — parses motions from the minutes prose → `all_votes.csv`. See below.

## Vote recording ceiling — **NAMED** (near-unanimous consensus body)

These minutes **name individual voters per motion**. The consistent form (2020–2025):

> "*Commissioner X motioned to approve <subject>, and Commissioner Y seconded the motion. All
> Board members present (Chair …, Vice Chair …, Commissioners …, …, and …) voted in favor.*"

So each motion records **mover, seconder, and a named in-favor roster**; dissent and
abstention are named when they occur (e.g. 2020-06-17: "*Chair Jennifer Johnston abstained …
but the rest of the Board members present (…) voted in favor*"). This is a **named** ceiling,
not tally-only — hence `all_votes.csv` was produced.

`all_votes.csv` (standard 13-col schema; `body=HousingAuthority`; one row per motion × named
member; `source` = the minutes md path):
- **327 motions**, **1,692 named member votes**, over 68 meetings.
- Outcomes: **327 Passed** (0 failed) — a genuine consensus board. Named dissent across six
  years: **0 Nay, 3 Abstain** (all 3 flagged in the file). This is real, not an extraction
  artifact.
- **27 motions are tally-only rows** (`member` blank): the minutes stated the outcome without
  re-listing names for that motion — an honest blank, never back-filled.
- **12 distinct member tokens**: 11 resolved to full names (Christine Nguyen, Erin Litvack,
  Phil Bernal, Gwen White, Spencer Moffat, Kat Johnson, Wendy Leonelli, Mark Johnston,
  Jennifer Johnston, Jamie Ramos, Mike Akerlow) + `Johnston` left surname-only on 2 rows
  where the source gave no first name and **two Johnstons (Mark & Jennifer) served
  concurrently** — deliberately not guessed.

### Vote-extraction caveats (spot-checked, faithful, imperfect on edges)
- Names come verbatim from the minutes. A per-meeting roster (the `PRESENT:` block) resolves
  surname-only references to full names; globally-unambiguous surnames are mapped, ambiguous
  ones (`Johnston`) are left as printed.
- `result` is normalized to `Passed` (all motions carried); `motion_type` is a keyword
  classification (minutes-approval / consent-agenda / resolution / budget / executive-session /
  election-officers / adjourn / other) — a convenience label, not a city-native string.
- Minor known imperfections: on a few procedural motions with **no explicit seconder** the
  parser may borrow the next sentence's seconder; a handful of `title` strings retain OCR
  spacing ("for t he Board to"). These do not affect the member/vote attribution.
- Occasional source typos are preserved verbatim (e.g. a 2022 seconder printed "Johnston"
  where the roster is Kat "Johnson").

## Rebuild

```
python3 salt_lake_county/agencies/housing_authority/build.py          # minutes + index (self-contained)
python3 salt_lake_county/agencies/housing_authority/extract_votes.py  # all_votes.csv
```
Both are idempotent and write only inside this module. (Federation into
`salt_lake_county.db` / `gov.db` is a separate, not-yet-wired step — see CLAUDE.md.)
