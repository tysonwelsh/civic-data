# PMN backfill — coverage cross-check (Sandy City)

**As-of:** 2026-07-05 · **Source:** Utah Public Notice Website (PMN), `https://www.utah.gov/pmn/`
**Sandy PMN entity id:** **260** (government type 3 = Municipality)
**Sandy PMN public-body ids:** City Council = **464**, Planning Commission = **466**,
Redevelopment Agency = **465**, Board of Adjustments = **467** (full list in `AVAILABILITY.md`).
**Scope:** repo data floor is **2020** (window 2020–2026); PMN documents dated before 2020 are
enumerated for context but are **out of scope** and not treated as gaps.

## Bottom line

The repo's council `meeting_minutes/` layer (built from **Legistar**) is the **superset** for
2020–present. A per-**DATE** set-difference (not a raw count comparison, ±4-day tolerance) found
**8 meeting dates** with PMN documents the repo lacked. **All 8 recovered** into `raw/` + `text/`
+ `index.csv`: **6 City Council** minutes dates and **2 Redevelopment Agency** minutes dates.
After recovery, **0 in-scope PMN minutes remain unrecovered**.

Two numbers matter and differ:
- **Per-year counts** below show PMN council notices *carrying* a minutes attachment ≥ repo minutes
  most years — but PMN posts Draft **and** Final minutes as *separate notices*, so that column
  double-counts dates and is NOT the gap signal.
- **Per-DATE set difference** is the real test: which specific meeting dates does PMN have and the
  repo not? That produced the 8 recovered items.

## How PMN was enumerated (GET-only, polite)

PMN's historical **search** is a **POST/CSRF** endpoint (`/pmn/searchresult.html`) — disallowed by
the polite-scraper rule and unsupported by `scripts/polite_fetch.py`. Instead the **GET** browse
endpoint `/pmn/list/notices.html?id=<bodyId>&page=<N>` was used. `page` is **cumulative** (each
increment appends ~5 older notices and re-emits the whole list newest-first), so one large page
(`page=300`) returns each body's **entire** notice history in one GET. Saturation (raw HTML in
`raw/_notices_<id>_p300.html`):
- Council 464 → **1,588 notices**, 2014-10-28 … 2026-07-07.
- Planning Commission 466 → **928 notices**, 2008-04-10 … 2026-07-02.
- Redevelopment Agency 465 → **90 notices**, 2008-04-25 … 2023-08-22.
- Board of Adjustments 467 → **28 notices**, 2008-05-02 … 2025-12-11.

Attachment **type labels** were parsed from the list HTML. On Sandy notices, minutes carry the
`(Meeting Minutes)` label; agendas/hearing notices carry `(Other)`.

## City Council (body 464) — diffed vs `meeting_minutes/minutes_index.csv`

| Year | Repo minutes | PMN notices w/ minutes attached | Per-date gaps repo lacked (recovered) |
|------|-------------:|--------------------------------:|:--------------------------------------|
| 2020 | 45 | 46 | 0 |
| 2021 | 45 | 54 | 0 |
| 2022 | 44 | 81 | 0 |
| 2023 | 43 | 84 | **2** (10-17 Final; 11-07 Draft) |
| 2024 | 38 | 44 | 0 |
| 2025 | 40 | 76 | 0 |
| 2026 | 19 | 41 | **4** (04-28 Approved; 06-09, 06-16, 06-23 Draft) |
| **Total (2020+)** | **274** | **426** | **6 recovered** |
| pre-2020 (out of scope) | 0 | 174 | — |

The 2 in-2023 gaps (10-17, 11-07) sit between meetings the repo *does* hold (10-03/10-10/10-24 and
11-14/11-28) — genuine single-meeting holes in the Legistar harvest. The 4 in-2026 gaps are all
past the repo's latest Legistar minutes (2026-06-02), i.e. the newest meetings not yet ingested.

## Planning Commission (body 466) — diffed vs `planning_commission/all_votes.csv` dates

| Year | Repo coverage (Legistar votes) | PMN notices w/ minutes attached | Recovered |
|------|-------------------------------:|--------------------------------:|:----------|
| 2020–2026 | 115 meeting-dates | **0** | 0 |

**PMN carries ZERO Planning Commission meeting-minutes for Sandy** — every PC attachment is a
project-specific public-hearing `(Other)` notice or an agenda, never `(Meeting Minutes)`. The repo
also has **no PC minutes files** on disk (PC data is built from the Legistar API — see
`planning_commission/CLAUDE.md`). So PMN adds no recoverable PC minutes. The single in-scope PC
*agenda* on PMN (2021-03-18, file 696569) is for a meeting the repo **already** covers via Legistar
votes, so it is not a missing date and was not pulled. **This zero is DATA, not a failure.**

## Redevelopment Agency (body 465) — no repo RDA-minutes layer exists

| Year | Repo RDA minutes | PMN notices w/ minutes attached | Recovered |
|------|-----------------:|--------------------------------:|:----------|
| 2022 | 0 | 1 notice (2 minutes files) | **2** |
| other 2020+ | 0 | 0 | 0 |

The repo has **no standalone RDA minutes** anywhere (only 1 RDA vote row exists). PMN's lone
in-scope RDA-minutes notice is dated **2022-06-28** but *attaches minutes for two earlier RDA
meetings* — **2022-05-17** and **2022-06-07** (the classic "minutes approved at a later meeting"
pattern; the meeting date is taken from the PDF/filename, not the notice date). Both recovered.
RDA meets the same evenings as the Council; the recovered RDA minutes are distinct RDA-body
documents, additive to the repo.

## Board of Adjustments (body 467)

28 notices total (2008–2025), **0 with a `(Meeting Minutes)` attachment**, 0 recoverable. Recorded
for completeness; the repo carries no BoA minutes layer.

## Recovered items (see `index.csv`)

| date | body | title | format | PMN file | notice |
|------|------|-------|--------|---------:|-------:|
| 2023-10-17 | Council | Final Minutes | scanned/OCR | 1038131 | 867651 |
| 2023-11-07 | Council | Draft Minutes | scanned/OCR | 1050973 | 874231 |
| 2026-04-28 | Council | Approved Minutes | scanned/OCR | 1442703 | 1085677 |
| 2026-06-09 | Council | Draft Minutes | scanned/OCR | 1454105 | 1091471 |
| 2026-06-16 | Council | Draft Minutes | scanned/OCR | 1454715 | 1091795 |
| 2026-06-23 | Council | Draft Minutes | scanned/OCR | 1455001 | 1091869 |
| 2022-05-17 | RDA | Minutes | text | 865737 | 766179 |
| 2022-06-07 | RDA | Minutes | text | 865739 | 766179 |

The 6 council PDFs are **image-scanned** (or PUA-font-broken for 2023-10-17) — recovered via
tesseract OCR (pdftoppm 300 dpi); the 2 RDA PDFs are born-digital (clean `pdftotext -layout`).
Corpus screener clean (only advisory page-footer endings and repeated roll-call template lines).

## What remains genuinely missing / out of scope

- **Nothing in-scope remains unrecovered.** Every PMN minutes attachment dated 2020-01-01+ that the
  repo lacked is now in `index.csv`.
- **2023-11-07 Final minutes** (PMN file 1052569) is a **0-byte broken upload** on PMN — the
  **Draft** version (file 1050973) was recovered instead, and logged as broken in `_fetch_log.jsonl`.
- **Pre-2020 PMN council minutes (174 notices)** are below the repo's 2020 floor — enumerated in
  `raw/_notices_464_p300.html` / `council.json`, deliberately not downloaded.
- **PC has no minutes on PMN at all** (see above) — an honest coverage zero.
