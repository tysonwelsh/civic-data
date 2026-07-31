# ordinances/ — South Jordan adopted ordinances + motion linkage

Additive dataset (expand-city-sources §3). Links each council vote on "Ordinance YYYY-NN"
to the adopted ordinance text. **Purely additive** — nothing in `meeting_minutes/` etc. was
modified. As-of **2026-07-06**.

## What's here
```
raw/ordinances_archive/   52 adopted-ordinance PDFs, 2020-2026 (general series), verbatim
                          from the city code host's S3 bucket (+ _fetch_log.jsonl provenance)
text/                     text sidecars: 5 born-digital (*.txt via pdftotext-layout) +
                          13 OCR (*.ocr.txt, tesseract) for the archived-but-uncited ords
index.csv                 THE dataset — 129 ordinances (2020+), one row per ordinance, with
                          the motion linkage + confidence
archive_backcatalog.csv   raw enumeration of the ENTIRE online back-catalog: 213 ordinances
                          1997-2026 (general series only), s3_key + live source_url + size
build_index.py            regenerates index.csv from archive_backcatalog.csv + all_votes.csv
AVAILABILITY.md           what was checked, what the city does/doesn't publish, gap + defect log
```

## The two ordinance series (critical)
South Jordan runs **two parallel, independent number series**:
- **general** `YYYY-NN` — code text amendments, budgets, appointments, construction standards.
- **zoning/rezone** `YYYY-NN-Z` — site-specific rezones + Title 17 zoning actions.

`2020-10` and `2020-10-Z` are **different ordinances adopted on different dates** — never
collapse the `-Z`. `series` column carries this.

## Source of truth
- **Code host:** `southjordan.municipalcodeonline.com` (Municipal Code Online; AngularJS SPA;
  current codified text also mirrored at `library.municode.com/ut/south_jordan`).
- **Adopted-ordinance back-catalog:** the host stores each adopted ordinance PDF in a
  **publicly-listable S3 bucket**,
  `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/southjordan/ordinances/documents/`.
  Enumerate with `?list-type=2&prefix=southjordan/ordinances/documents/` (paginate the
  continuation token). This bucket carries **only the general series** — **zero `-Z` zoning
  ordinances are posted there.** (The SPA's `bookadmin/ordinance` JSON endpoint is login-gated;
  the S3 listing is the public route.)

## Linkage method (index.csv `match_confidence`)
Join key = ordinance number cited in the motion text of `meeting_minutes/all_votes.csv`
(regex `Ordinance (No.)? YYYY-NN(-Z)?`) ∩ the S3 back-catalog.

| confidence | meaning | source_url | count |
|---|---|---|---|
| **high** | number cited in a council motion **and** an independent adopted PDF exists in the S3 archive | S3 PDF | 39 |
| **within_source** | number cited in a motion but **not** in the S3 archive (all 35 `-Z` rezones + general ords not yet posted). Derived from the motion itself — **NOT independently corroborated.** | minutes doc | 78 |
| **low** | archived ord in-window, number **not** cited in any motion, but its signed-PDF adoption date falls on a recorded council meeting date (date-only; `matched_motion_no` blank) | S3 PDF | 7 |
| **none** | archived ord in-window whose adoption date **predates the minutes floor** (first minutes = 2020-08-18) — a coverage seam, not a miss | S3 PDF | 5 |

`within_source` is the honest label the SKILL prescribes for a motion-derived row: it is `high`
*by construction* (the number comes from the same motion), so it must not be read as an
independent cross-match. **No `medium` rows** — no archived ord matched by date+subject-without-
number, so none was forced.

`adoption_date` (the `date` column) provenance:
- cited rows → the council meeting date of the adopting motion (`all_votes`).
- `low`/`none` rows → the **"PASSED AND ADOPTED ON THIS __ DAY OF __" clause** on the signed
  PDF's signature page. The day+month are **handwritten**; OCR garbled them, so they were
  transcribed by **vision (Read tool)** and hard-coded in `build_index.py:ADOPTED_DATES`
  (traceable to a page image — never fabricated).

## Coverage / storage
- `index.csv` covers the **2020+** minutes window only (129 rows). Pre-2020 ordinances (161)
  can never link to a 2020+ vote, so they live in `archive_backcatalog.csv` **index-only**
  (live `source_url`, not downloaded — a documented raw-retention exception; public + refetchable).
- 47 of the 52 downloaded 2020+ PDFs are **signed image scans** (0 text layer) — `format=scanned`,
  body OCR deferred (titles come from the OCR'd signature block or the motion; full-body OCR is a
  TODO, low value since the linkage is number+date+subject).

## Regenerate
`python3 ordinances/build_index.py` — idempotent; reads `archive_backcatalog.csv` +
`../meeting_minutes/all_votes.csv`. To re-pull the online catalog, re-enumerate the S3 prefix
(above) and rebuild `archive_backcatalog.csv`, then re-run.

## Analysis notes
- **Land-use share:** 58/129 = 45% (`land_use=yes`: all `-Z` + any general amending Title 16
  subdivision / Title 17 zoning / annexation / density / landscaping).
- Cross-body: an `-Z` here is the council's rezone adoption — join to `planning_commission/`
  (PC recommends, council adopts) by File No. / date for the full referral chain.
- Mayor does **not** appear in these roll calls (5 council members named; see recon §2).
