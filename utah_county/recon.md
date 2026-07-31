# Utah County — source reconnaissance (2026-07-20)

The repo's **second COUNTY entity** (after `salt_lake_county/`) and its first
**3-member Board of Commissioners** county. Utah County (FIPS 49049; registry
`fed_index` 102) is Utah's second-largest county. Governance: **Board of
Commissioners form** — a **3-member elected Board of Commissioners** that is
simultaneously the legislative AND executive body (no separate mayor/manager).
Meets **Wednesdays at 2:00 PM** (historically Tuesdays/other weekdays in the
2015–2019 era) in the Commission Chambers, Room 1400, 100 E Center St, Provo.
Counties are modeled as **modules**, not as big cities.

Members seen in the corpus: **2015–2018** Larry A. Ellertson, William C. Lee,
Greg Graves; **2026** Skyler Beltran (Chair), Brandon B. Gordon, Powers Gardner.
The roster rotates across the decade — resolve voters by full name.

## Legislative — Board of Commissioners — CUSTOM PORTAL, no machine vote API

- **NO Legistar / Granicus / CivicClerk.** The commission runs a bespoke **Next.js**
  portal (`https://commission.utahcounty.gov/`). Unlike Salt Lake County (Legistar
  `EventItemVote`), **there is no structured electronic vote record** — votes exist
  ONLY in the minutes prose. This is a **prose-extraction county**, like the
  non-Legistar cities.
- **CLEAN MACHINE-READABLE HARVEST CHANNEL (discovered 2026-07-20):** the portal's
  own JSON API drives the archive dropdown:
  - `GET /api/meetings/years?type=CM` → every year that has minutes (dropdown lists
    back to 1950; real digital files begin **2015**).
  - `GET /api/meetings/archive?year={YYYY}&type=CM` → array of
    `{filename, file_descr, min_year, min_category, audiofile, audiodescr}` — the full
    minutes-doc catalog for that year (the `month` param is ignored; one call = the
    whole year).
  - The minutes PDF resolves at
    **`https://www.utahcounty.gov/dept/commish/data/minutes/{min_category}/{min_year}/{filename}`**
    (i.e. `.../minutes/CM/2020/12.16.2020CommissionMeetingMinutes.pdf`). The directory
    listing 403s but individual files 200. Verified live.
  - `GET /api/meetings?dateStart=&dateEnd=` returns the **forward-looking AGENDA**
    (planning) structure (`sections`/agenda items, all `status:"Scheduled"`) — it does
    NOT carry vote outcomes, so it is not the vote source. PMN (below) is a fallback
    mirror, not the archive.
- **Utah Public Notice body 2731** (`https://www.utah.gov/pmn/sitemap/publicbody/2731.html`)
  carries only the **most recent ~10 notices** (agenda + Approved Minutes + audio) — good
  for the newest meetings, **NOT a historical archive**. The commission portal API is the
  authoritative back-catalog; PMN is a refresh cross-check.

### THE VOTE-RECORDING CEILING — era-split (decisive finding, confirmed by reading PDFs)

> ⚠ **CORRECTED 2026-07-25 — the era table below is WRONG on two counts** (audit:
> `_audits/2026-07-25/report.md`). It is retained verbatim as the 2026-07-20 recon record;
> the authoritative era table now lives in `utah_county/CLAUDE.md`.
> **(1)** "2017–~2019 = scanned images" is false — **2017 is 100% born-digital** (50/50
> files, pypdf) carrying 499 `AYE: [full names]` blocks across 49 of 50 files, and the db
> records 174 named motions that year. The scanned era begins in 2018 (mixed) / 2019.
> **(2)** "2017 onward is tally-primary … a genuine recording ceiling, not an extraction
> gap" is false — the 2019–2024 OCR minutes print a **full ALL-CAPS named roll**
> (`VOTE: 3-0 / AYE: COMMISSIONER LEE / …`), 1,732 `AYE:` blocks across those six years, of
> which the repo captures **zero**. That is an extraction gap. Genuine tally-only begins
> ~2025 (0 name blocks in 2025–2026).
> Correct framing: **named 2015–2019, tally-primary 2020+, dissent nameable throughout.**

The minutes format — and the vote granularity — **changes twice** across the decade:

| Era | Format | PDF kind | Vote grammar | Ceiling |
|---|---|---|---|---|
| **2015–2016** | `MMDDYY-CommissionMinutes.pdf` | **born-digital** (pypdf text) | *"Commissioner Lee made the motion to… seconded by Commissioner Graves and carried with the following vote: **AYE: [full names] / NAY: [names]**"* | **NAMED roll call** — every member's vote is enumerated. `names_recorded=1`. |
| **2017–~2019** | scanned images | **scanned (OCR needed)** | *"COMMISSIONER GRAVES: MOTION TO APPROVE / COMMISSIONER LEE: SECOND / **ALL IN FAVOR: AYE**"* (all-caps) | **TALLY-ONLY** — mover + seconder named; individual ayes not enumerated. `names_recorded=0`. |
| **~2020–2026** | `MM.DD.YYYY.pdf` | **scanned (OCR needed)** | *"Motion to approve…: Commissioner Gordon / Seconded by: Commissioner Beltran / Vote: **All in favor - Aye** / Result: **Motion passed 2/0**"* | **TALLY-ONLY** — mover + seconder named + numeric tally (e.g. `2/0`); individual ayes not enumerated. `names_recorded=0`. |

So **2015–2016 is a NAMED body; 2017 onward is tally-primary** (mover/seconder named,
a numeric or "all in favor" tally, dissent named only when a division occurs). This is
a genuine recording ceiling, not an extraction gap — identical in kind to nephi /
west_jordan PC / cottonwood_heights. Most business is a **Consent Agenda** ("Approved on
Consent") batch-adopted with no roll — honestly tally-only. On the born-digital 2015–2016
minutes even routine items print `AYE: <all three names> / NAY: None`.

**Key consequence:** all minutes 2017-01 onward are **image-only scans requiring OCR**
(pdftoppm 200dpi + tesseract; OCR quality on these clean scans is high — mover/seconder/
result lines extract cleanly). 2015–2016 are born-digital (pypdf). Provenance records
which channel produced each doc (`minutes` = born-digital primary, `ocr_scan` = OCR'd).

### Attachments & multi-part docs (harvest hygiene)

The archive interleaves **exhibit attachments** with the minutes: `*ATTACH*.pdf`,
`.pptx`, `.jpg`, `.png` (presentations, MOUs, maps submitted with an item). These are
NOT minutes and are **excluded** from the corpus (heavy in 2015–2018). Some meetings'
minutes are **split into parts** (`…Part1..Part7.pdf`, `…SheriffPart1/2`) or a **combined**
special file (2021 `03.18+03.22 combined`) — parts of one date are **concatenated** into a
single minutes markdown. Date is parsed from `file_descr` ("June 24, 2026, Commission
Meeting Minutes"), filename `MMDDYY`/`MM.DD.YYYY` as fallback.

### Bodies in this module

- **Board of Commissioners** — regular + `SPECIAL` commission meetings (the voting body).
- **Commission Work Session** — work sessions + department **Budget Work Sessions**
  (deliberative/briefing; rarely carry motions — mostly discussion, honestly few/zero
  votes). Kept in the same `legislative/` module as a second body.

## Data floor & deeper-than-floor availability

- **Build floor: 2015-01-01** (this build). The API's digital archive **begins 2015**;
  the `years` endpoint lists placeholder years back to 1950 but no files resolve before
  2015 (spot-checked). So 2015 is effectively the digital floor — **no meaningful
  pre-2015 backfill is queueable** from this portal (paper-era only).
- Full inventory 2015–2026: **659 archive docs** → after excluding attachments/exhibits,
  ~**300+ distinct commission-meeting minutes** + work-session/budget-session minutes.

## Agencies — VERIFY (see agencies/README.md)

Utah County's General Plan references a **Housing Authority of Utah County (HAUC)**.
Unlike Salt Lake County's Housing Connect (its own rich portal), HAUC's minutes
publication is thin/unverified. The county has **no RDA/MBA** in the commission portal
(the 3-member board acts directly; there is no separate redevelopment agency body in the
archive). Agencies are documented honestly in `agencies/README.md` — build only what
actually publishes minutes.

## Other modules (owned by sibling agents — not this agent)

`land_use/` (County Planning Commission), `elections/` (County Clerk canvass), `plans/`,
`projections/`, `gis/`, `ordinances/`, `development/` are built by parallel agents. This
agent (CORE) owns `legislative/`, `agencies/`, and `db/`.

## Module status (this agent) — BUILT

| module | source | result |
|---|---|---|
| `legislative/` | commission.utahcounty.gov archive API + PDF minutes | **495 minutes docs** 2015-01-06→2026-05 (Board of Commissioners 469 + Commission Work Session 26); 228 born-digital, 267 OCR |
| `agencies/` | Housing Authority of Utah County (housinguc.org) | **26 board minutes** 2023-12→2026-03 (born-digital, tally-only). No RDA/MBA exists — see agencies/README.md |
| `db/` | prose-extraction staging → utah_county.db (standard 8-table schema) | **521 meetings, 10,016 motions (822 named / 9,194 tally), 2,383 votes, 39 persons, 3 bodies, 31 contested**; FK 0, integrity ok |

### Extraction pipeline (db/, all idempotent, PC-append-safe — max motion_id 10,016)

1. `fetch_legislative.py` — archive API → PDFs → markdown (pypdf born-digital / tesseract OCR
   at 200dpi, pages parallel) + provenance front-matter. `UC_Y0`/`UC_Y1` env vars scope years.
2. `fetch_agencies.py` — HAUC own-site minutes → markdown.
3. `build_catalog.py` — rebuilds `minutes_index.csv` + `minutes/_catalog.csv` from on-disk
   front-matter (avoids slow end-of-run 404 retry backoff).
4. `extract_votes.py` — era-aware prose extraction (anchor on the result line; `relineate()`
   splits dense single-line OCR; window-bounded mover/seconder; named AYE:/NAY: blocks →
   vote rows) → `db/staging/{meetings,motions,votes}.csv`.
5. `build_db.py` — staging → `utah_county.db` (8-table schema; unifies surname mover/seconder
   with the full name from named votes).

### Honest gaps (server-side 404 / mislabeled archive rows — never fabricated)

- **2021-06-02**, **2022-08-15** commission minutes: listed in the archive but the PDF 404s
  (unpublished / withdrawn) — genuine gaps.
- **2024/01.31.2023.pdf**: a mislabeled archive row (wrong category+date) that 404s.
- **Pre-2015**: the digital archive begins 2015; the `years` endpoint lists placeholder years
  to 1950 but nothing resolves before 2015 — paper-era, not queueable here.
- **HAUC pre-2023-12**: not published online (GRAMA-request backfill queueable).
- **Work-session budget books**: some are 100+ page scanned department budget presentations —
  OCR'd and searchable but carry ~zero motions by nature (13 motions across 26 work sessions).
