# Kearns pmn_backfill — availability & verification log

**As-of:** 2026-07-13 · Source 4 (Utah Public Notice / PMN) of `expand-city-sources`.
Polite, GET-only crawl via `scripts/polite_fetch.py` (browser UA, ≥1s/host). No POST,
no auth, no bypassing. All raw originals retained in `raw/` with `_fetch_log.jsonl`
(url, bytes, sha256, retrieved_utc).

## What was checked

- **PMN entity discovery.** govType-3 (Municipality) entities list → Kearns =
  **entity 1321** → `publicBodies.html?id=1321` lists all four Kearns bodies:
  Council **5823**, Planning Commission **1561**, **Community Reinvestment Agency
  (CRA) 9273**, Community Committee 9553.
- **Every govType (1,2,4,5,6,7,8) swept for "Kearns"** to find any CRA/RDA/council
  body filed elsewhere and to identify decoys. Only extra hit: **Kearns Improvement
  District (entity 584, govType 5)** — the water special-district decoy (excluded).
  No township-era RDA/CRA body exists; CRA 9273 is a city-era body (first notice
  2025-07-14).
- **Cumulative notice crawl** of bodies 5823 (255 notices), 1561 (289), 9273 (12),
  9553 (6) via `notices.html?id=<body>&page=500` — full history in one GET each.
- **Per-date, per-body set-difference** of PMN "Meeting Minutes" attachments (meeting
  date parsed from the FILENAME, not the notice date — minutes attach to the NEXT
  meeting's notice) against the repo `minutes_index.csv` files, ±4-day tolerance.
- **Content-detection** of every candidate PDF (real minutes vs agenda/packet/audio)
  and **404-probing** of the 25 purged council file objects + Internet Archive CDX
  checks.

## What EXISTS and was recovered (3 docs)

- **CRA 2025-07-14** approved minutes (scanned → OCR) and **CRA 2025-09-08** draft
  minutes (born-digital) — body **9273**, previously 0 rows in the repo.
- **PC 2019-04-08** approved minutes (born-digital) — body **1561**; genuine recovery
  (was mis-logged unrecovered; filename lacked the "Minutes" token).

## What does NOT exist / stays a gap (verified, not fabricated)

- **25 council meetings 2017-01-18 → 2018-06-11** — minutes WERE published (notice
  pages still link a `(Meeting Minutes)` PDF, file ids 285127–413299) but the file
  blobs are **PURGED**: every one returns **HTTP 404** (315-byte `text/html` stub);
  live-era controls return `200 application/pdf`; **zero Wayback captures**. Genuine
  PMN file-store purge — the audited `meeting_minutes/minutes_unrecovered.csv` is
  accurate and unchanged. Recoverable only if PMN restores the pre-mid-2018 blobs.
- **7 council meetings** (agenda + MP3 only) and **9 recent council meetings**
  (minutes not yet approved/posted) — re-confirmed; no minutes to recover.
- **PC 2017–2018** — genuinely no minutes (MSD approved-minutes PDFs begin 2019-03-11;
  earlier notices carry agendas/packets/audio only). Gap stands.
- **CRA cancellations** — 5 CRA meetings (2025-08-11, 10-14, 12-08; 2026-02-09, 03-09,
  04-13) were CANCELED (cancellation PDFs on their notices; documented in `coverage.md`
  by file id). The 2026-05-11 CRA meeting was held but its minutes are not yet posted.
- **2016-02-08 Township PC** minutes (file 725941) exist on PMN but are **below the
  2017 data floor** — documented, not ingested.
- **Kearns Community Committee (9553)** — advisory board; posts audio + handouts, no
  minutes documents. Out of scope.

## Extraction

- Born-digital PDFs → `pdftotext -layout` (`extraction_method=pdftotext-layout`,
  `format=text`). Scanned PDF (CRA 2025-07-14) → `tesseract` OCR via `pdftoppm -r 300`
  (`extraction_method=tesseract-ocr`, `format=scanned`). OCR output NOT written to
  /tmp; sidecar lives in `text/`. `screen_corpus.py` run on `text/` — clean
  (dict_ratio ~0.79, no anomaly flags).

## Do not

Do not merge into the audited `meeting_minutes/` / `planning_commission/` layers in
place, and do not hand-edit `planning_commission/minutes_unrecovered.csv` (the
2019-04-08 recovery is flagged for the orchestrator/TODO to reconcile on promotion).
