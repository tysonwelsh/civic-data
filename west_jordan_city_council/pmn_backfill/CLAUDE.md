# pmn_backfill — Utah Public Notice (PMN) gap recovery

**Additive, un-merged dataset.** Meeting minutes recovered from the Utah Public Notice
Website (`https://www.utah.gov/pmn/`) that fill genuine **date-level gaps** in the audited
`meeting_minutes/` and `planning_commission/` layers. **Never hand-edit those layers** — this
directory is a staging area the user merges deliberately.

**As-of:** 2026-07-17 (city_website PC 2020–21 recovery); originally 2026-07-03. Built by
`expand-city-sources` SOURCE 4.

## PMN body ids (global, not per-city sequential)
Discovered GET-only: `/pmn/list/entities.html?id=3&limit=2000` (govType 3 = Municipality) →
West Jordan **entity id 305** → `/pmn/list/publicBodies.html?id=305&limit=2000`:

| Body | PMN id | crawled here |
|------|-------:|:---:|
| **City Council** | **395** | yes |
| **Planning Commission** | **396** | yes |
| Board of Adjustment | 397 | no |
| Redevelopment Agency (RDA) | 996 | no |
| Municipal Building Authority (MBA) | 997 | no |
| Fairway Estates Special Service Rec. District | 998 | no (its truth-in-taxation minutes post under body 395) |
| Taxing Entity Committee | 1129 | no |

## Method
1. **Crawl (cumulative GET):** `/pmn/list/notices.html?id=<body>&page=300` returns the body's
   entire notice history in one request (the list view's "past 6 months" banner is cosmetic;
   the historical *search* is POST/CSRF and is avoided). Council → 1,543 notices back to 2012;
   PC → 653 back to 2008. Saved to `raw/*_notices.html` provenance is in the scratch crawl.
2. **Filter** attachment labels to `(Meeting Minutes)` for meeting years 2020+ (also seen:
   `Public Information Handout` = agenda/packet, `Other`, `Audio Recording`).
3. **Set-difference by DATE**, ±4-day tolerance, against `minutes_index.csv` dates (per body).
   Per-year *counts* are not used to find gaps (PMN posts sporadically; repo is a superset for
   2023+). See `coverage.md`.
4. **Content-verify every candidate BEFORE recovery** — PMN labels/filenames can be wrong.
   Each file must show: correct body name in the header (`WEST JORDAN … CITY COUNCIL` /
   `WEST JORDAN PLANNING AND ZONING COMMISSION`), an internal "HELD `<date>`" matching the
   notice date, and MOTION/vote text. All 33 passed.
5. **Fetch** via `scripts/polite_fetch.py --out pmn_backfill/raw/ --now 2026-07-03T00:00:00Z`
   (provenance in `raw/_fetch_log.jsonl`). Attachment URLs are `/pmn/files/<FILE_ID>.pdf`
   (opaque ids — crawl notice pages, cannot template by date).
6. **Extract:** born-digital → `pdftotext -layout` (format `text`); scanned/image PDFs → Tesseract
   OCR at 300 dpi (format `scanned`, 6 PC files). Text sidecars in `text/`. `screen_corpus.py`
   run on all 33: no cid/replacement/mojibake/dict-ratio outliers; only benign layout flags
   (hyphen breaks, repeated header/footer lines). OCR files pass dict_ratio cleanly.

## Two recovery channels (the `source` column)
- **`source=pmn`** (33 files, 2026-07-03) — Utah Public Notice attachments (method above).
- **`source=city_website`** (27 files, 2026-07-17) — standalone PC minutes 2020-01-07→
  2021-03-16 pulled from the **city's own document host** `assets.westjordan.utah.gov/ugd/…`.
  PrimeGov's `ListArchivedMeetings` never held pre-2022 standalone PC meetings and PMN
  carried **agendas only** for this window, so neither prior channel had them. The live map
  date→PDF is the WordPress custom REST route `GET /wp-json/wjc/v1/data-meeting/<post_id>`
  (each meeting post's `docs` HTML lists Agenda/Video/**Minutes** links). All 27 in-body
  verified (header `PLANNING AND ZONING COMMISSION HELD <date>`, matching date, MOTION text,
  born-digital, not agendas/drafts). For these rows `pmn_body_id` is blank and `pmn_file_id`
  holds the host file hash (`a31809_<hex>`, also the raw/text filename token).

## Files
- `raw/` — 60 minutes PDFs verbatim + `_fetch_log.jsonl` (city_website entries carry
  `source` + `wp_post_id`).
- `text/` — extraction sidecars (60 `.txt`).
- `index.csv` — one row per recovered file. Schema:
  `date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`.
  `path` includes `raw/`. `source_url` = the PDF; for `source=pmn`, `notice_url` = the PMN
  notice page and `pmn_body_id` ∈ {395 council, 396 PC}; for `source=city_website`,
  `notice_url` = the `wjc/v1/data-meeting` API URL.
- `pmn_exceptions.csv` — crosscheck false-positive ledger. Holds the 2 COVID-cancelled
  dates (PC 2020-03-17 / Council 2020-03-25) whose PMN notices carry the body banner
  "This notice has been cancelled." (the engine only reads notice *titles*, so it flagged
  them as agenda_only gaps; suppressed here — no meeting was held, no minutes exist).
- `coverage.md` — PRIMARY deliverable: per-year repo vs PMN vs recovered vs missing, both bodies.
- `AVAILABILITY.md` — what was checked, what exists, what does not.

## What was recovered (60; 0 still missing)
- **Council (5, `pmn`):** 2022-01-03 & 2024-01-03 Oath-of-Office ceremonies; 2024-08-13 Fairway
  Estates SSD Truth-in-Taxation hearing; 2026-06-09 City Council Meeting + Committee of the Whole
  (newer than the last repo fetch, 2026-05-26).
- **Planning Commission (28, `pmn`):** the standalone 2021 (16) + Jan–Jul 2022 (12) regular-meeting
  run the PrimeGov-sourced repo never held.
- **Planning Commission (27, `city_website`, added 2026-07-17):** the standalone 2020-01-07→
  2021-03-16 biweekly run, from the city doc host (see the two-channel section). Only 2020-03-17
  is absent — cancelled (COVID-19), logged in `pmn_exceptions.csv`. Together with the 2021–22 run
  this fully closes the "no standalone PC 2020–21" gap.

## Why separate (do NOT auto-merge)
- The audited `meeting_minutes/`/`planning_commission/` layers, `all_votes.csv`, `db/`, and
  `weeks/` are derived and reconciled. Injecting rows here would silently change vote tallies,
  referral links, and weekly bundles. Merge is a deliberate, reviewed step.
- **PC caveat if merged:** these PC minutes print a tally then name the majority in some years
  (unlike the repo's tally-only 2022+ PC minutes). If merged, re-run `planning_commission/
  extract_votes.py` and re-audit — do not assume the existing tally-only extraction rules apply.
- **Body-id nuance:** 2024-08-13 is legally a Fairway Estates SSD hearing (body 998) posted under
  the Council body (395); classify carefully if merging.

## Reproduce
```
# body discovery
polite_fetch.py --out <t> "https://www.utah.gov/pmn/list/entities.html?id=3&limit=2000"   # -> WJ id 305
polite_fetch.py --out <t> "https://www.utah.gov/pmn/list/publicBodies.html?id=305&limit=2000"
# full history
polite_fetch.py --out <t> "https://www.utah.gov/pmn/list/notices.html?id=395&page=300"    # council
polite_fetch.py --out <t> "https://www.utah.gov/pmn/list/notices.html?id=396&page=300"    # PC
# then parse (Meeting Minutes) labels, date set-diff vs minutes_index.csv, content-verify, fetch.
```

## Crosscheck verification note — 2026-07-17 (pmn_crosscheck flag review → RESOLVED)
All 29 flags from `scripts/pmn_crosscheck.py west_jordan` triaged and **now cleared**
(re-run: **0 flags, 2 suppressed, 8 pending-adoption**).
- **The newly-crawled RDA 996 + MBA 997 produced ZERO false positives** — all their meeting
  dates are already council minutes dates (in-session), correctly cleared by the engine.
- **Headline finding — 28 standalone PC (body 396) agenda-only gaps, 2020-01-07 → 2021-03-16.**
  PMN carried **agendas only** for them; the repo `planning_commission/` held only 2020-09-29 +
  2021-03-31 for the era. RESOLUTION (wave-2, 2026-07-17):
  - **27 of 28 RECOVERED** from the city doc host as `source=city_website` (see above) and
    promoted into `index.csv` — which the crosscheck's `repo_dates()` counts as repo-has,
    clearing the flags. The Commission met biweekly through all of 2020, disproving the old
    "no standalone PC 2020-21" claim.
  - **1 NOT a gap — PC 2020-03-17** was **cancelled** (COVID-19; notice 593197 body banner
    "This notice has been cancelled."; no WordPress meeting post). Logged in
    `pmn_exceptions.csv` (kind=other), not `minutes_unrecovered.csv` (no meeting occurred).
- **1 council (395) — 2020-03-25 "Public Hearing Notice" — also cancelled** (notice 593943
  same banner). Logged in `pmn_exceptions.csv`.
Engine note: the cancellation banner lives in the notice BODY, not the title, so
`RE_CANCEL` (title/filename-only) could not catch these two — a possible future hardening
(scan the notice body for "has been cancelled"); left as report-only, not changed here.
