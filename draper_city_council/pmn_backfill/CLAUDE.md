# Draper — `pmn_backfill/` (Utah Public Notice cross-check + recovery)

**Source 4 of `expand-city-sources`.** A SEPARATE, review-only dataset that
cross-checks the audited `meeting_minutes/` and `planning_commission/` layers
against the statewide Utah Public Notice repository (`utah.gov/pmn`) and holds
the minutes genuinely missing from the repo. **Additive — it never modifies the
audited layers.** Built 2026-07-13.

## Headline result

**6 meetings recovered (7 raw PDFs — one byte-identical duplicate posting), all
born-digital, all header-verified:**

1. **All three of the repo's broken-Granicus-stub gaps are now recovered** —
   Council **2021-07-20** (full 24-page regular-meeting minutes with roll-call
   grids), PC **2020-12-10**, PC **2024-10-10**. These were logged in
   `minutes_unrecovered.csv` as `doc_unretrievable` (~299-byte Granicus stubs).
2. **Three council meetings Granicus never listed at all** — the August
   **Truth-in-Taxation special sessions**: **2022-08-24** (Council acting as the
   Traverse Ridge SSD governing authority, Res #22-46 certified tax rate),
   **2024-08-14**, **2025-08-13** (separate SL-County and Utah-County tax
   hearings — the two-county city). Draper posts its TnT hearings to PMN only;
   this is a *Granicus listing gap*, systematic by meeting type (August, off the
   1st/3rd-Tuesday cadence, 2022/2024/2025).

**MERGE NOTE — DONE 2026-07-16:** all six meetings were PROMOTED into the
audited layers (`minutes_index.csv` `source=pmn` rows + markdown with
provenance headers + raw-PDF copies + vote extraction with the new trailing
`provenance=pmn_minutes` column, threaded into db/weeks). The stale PC
2024-03-14 unrecovered row was removed (doc was in the index all along), and
the phantom Council 2023-10-15 row was removed (a Sunday; no such meeting on
Granicus or PMN — both hold the real 2023-10-17 minutes). Ordinances
#1494/#1496/#1497 now link high to their 2021-07-20 enacting motions. See
`../VERIFICATION.md` 2026-07-16 addendum; backups in
`_backups/2026-07-16-minutes-promotion/draper/`. This dataset remains the
provenance record for the recovered originals (`raw/`, `text/`, `index.csv`
untouched).

## Method (reproducible, GET-only, polite)

1. Entity discovery: `entities.html?id=3&limit=2000` (govType 3 = Municipality)
   → **Draper = 114**.
2. `publicBodies.html?id=114&limit=2000` → 28 bodies; 9 relevant ones crawled
   (ids in `coverage.md`). Council has TWO ids: **5555** (current) + **379**
   (defunct, 2013–2018); CRA likewise **7261** (current) + **382** (RDA-era).
3. One cumulative GET per body: `notices.html?id=<body>&page=200` returns the
   entire notice history (the list view's "past 6 months" limit applies to
   page 1; the historical search is POST/CSRF — never used).
4. Parse rows (`_parsed_notices.json`): notice id/title/event-date + every
   attachment (file id, filename, type label). **Minutes detection = label
   `(Meeting Minutes)` OR "minutes" in the filename** — labels both under-count
   (herriman lesson) and, here, over-count (a few PC public-hearing handouts
   mislabeled `Meeting Minutes`; each candidate was filename/date-verified).
5. **Exact per-date set-difference** vs the repo `minutes_index.csv` (PMN event
   date = meeting date for this city, confirmed by date-encoded filenames), with
   a ±4-day pass used only for near-miss inspection — the pure ±4d diff MASKS
   real gaps here (it hid PC 2024-03-14 behind a neighboring meeting). Plus a
   per-date doc-count comparison to catch multi-doc days (it surfaced the
   `CC 4.7 Minutes.pdf` attached to the 2020-04-21 notice — already in repo).
6. Fetch the missing dates' PDFs via `polite_fetch.py` (≥1s/host, logged to
   `raw/_fetch_log.jsonl`), verify each PDF's **internal body-name + date
   header** before trusting PMN's label, extract `text/` sidecars with
   `pdftotext -layout` (all born-digital — no OCR), screen with
   `screen_corpus.py` (clean; the flagged duplicate pair is the known
   byte-identical double-posting, `repeated_line` hits are roll-grid/footer
   lines, `ends_mid` advisories are approval footers — tails verified complete).

## Layout / schema

```
raw/
  _disc_entities.html          PMN municipality list (govType 3) — provenance
  _disc_bodies.html            Draper's 28 bodies (entity 114)
  _notices_<bodyid>_p200.html  cumulative notice history per crawled body (9)
  _parsed_notices.json         parsed intermediate (notice rows + attachments)
  pmn_council_*.pdf, pmn_pc_*.pdf   the 7 recovered originals, verbatim
  _fetch_log.jsonl             polite_fetch provenance (url/status/bytes/sha256/utc)
text/                          pdftotext -layout sidecars (7, born-digital)
index.csv                      §9 pmn_backfill contract header (14 cols) + `note` extra
coverage.md                    per-year × per-body tables, unrecovered-log cross-check,
                               separate-bodies (RDA/MBA/CRA/HPC/ZA) PMN inventory
AVAILABILITY.md                what was checked / exists / doesn't, as of 2026-07-13
```

`index.csv` columns (SCHEMA_SPEC §9 contract, city extra `note` after):
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,note`.
`path` is dataset-relative including `raw/`; `source=pmn`; `body` ∈
`Council`/`PlanningCommission` (repo vocabulary); the 2024-08-14 duplicate has
its own row (its `note` says which file is primary).

## Caveats

- **The 2025-08-13 clerk header typo is preserved verbatim** — the minutes say
  "TUESDAY, AUGUST 13, 2025" but that date was a Wednesday (PMN event date +
  filename both 8-13). Never "corrected".
- **2024-08-14 exists twice on PMN** (notices 929679 + 932411), byte-identical
  (sha256 `98823bda…`). Both raws retained; analyze one.
- Separate Granicus bodies (RDA 60 / MBA 29 / CRA 25 / HPC 152 / ZA 57 minutes
  docs on Granicus) were **inventoried on PMN only, not fetched** — Granicus is
  the richer source if they're ever built as core datasets.
- **Promotion happened 2026-07-16** (see MERGE NOTE). This dataset itself was
  not modified by the promotion — it remains the verbatim recovery record.
- Not loaded into `cities.db` by this run (`build_cities_db.py` out of scope).


## 2026-07-17 — crosscheck flag verification (18 flags → 2 leads, 16 exceptions)

Verified every 2026-07-17 crosscheck flag (cached list HTML + repo indexes + throttled
per-notice GETs for content). Re-run after appending exceptions: **2 flags** (16 suppressed).

**Recovery leads (2, agenda-grade — PMN carries only agendas, repo lacks the date):**
- **Council 2020-02-28** — 2-day CITY COUNCIL PLANNING RETREAT (St. George, Hyatt Place, Feb 28–29 2020); real council meeting the repo lacks. Minutes may not exist for a retreat — verify at the city CMS/Granicus before promoting.
- **Council 2020-09-01** — Notice of Public Hearing before the City Council on 2020-09-01 (2020 Q3 Bulk Text Amendment); Sept 1 2020 is a first-Tuesday council slot; repo has 09-15/09-22 but not 09-01. Genuine gap — check Granicus for the 09-01 minutes.

**Exceptions written (16), by kind:**
- 11 `count_mismatch` (all benign — repo holds exactly 1 authoritative minutes doc/date):
  `mislabel` ×5 (recap/agenda/packet/staff-report categorized `(Meeting Minutes)`:
  2020-12-08, 2025-08-19, 2025-09-02, 2025-12-11, 2026-03-12); `duplicate` ×3 (same
  minutes posted 2–3× under one/other filename: 2024-07-11, 2024-10-24, 2025-02-13);
  `draft` ×1 (2026-02-17 DRAFT alongside approved); `not_minutes` ×1 (2024-11-21 — the
  'Minuteman Project' handout caught by the `minut` filename regex, ENGINE substring FP);
  `other` ×1 (2020-04-21 — prior 4-07 minutes attached for adoption, repo holds both).
- 5 `agenda_only_gap`: `other` ×3 (2020-03-12 PC POSTPONED; 2021-07-08 + 2022-02-24 =
  PC public-hearing notices posted under **council body 5555**, repo holds PC 07-08/02-24 —
  foreign-body cross-filing; 2025-02-10 hearing notice posted on a Monday non-meeting day);
  `wrong_date` ×1 (2021-06-15 event date wrong, hearing held 2021-06-24 which repo holds).

**Hardening candidates (see engine notes below):** (1) `RE_MINUTES_FNAME=r'minut'`
false-matches 'Minuteman' → gate on word-boundary or exclude known project-name tokens.
(2) `RE_CANCEL` misses title 'POSTPONED' (draper PC 2020-03-12). (3) PC public-hearing
notices ride the council body 5555 (foreign-body); a multi-dataset match on 5555
(meeting_minutes;planning_commission) would absorb them.
