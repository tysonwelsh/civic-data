# pmn_backfill/ — build method & caveats (Sandy City)

**Additive dataset.** Built by `expand-city-sources` **Source 4** (Utah Public Notice / PMN
cross-check). **As-of 2026-07-05.** This dataset **NEVER modifies** the audited `meeting_minutes/`
or `planning_commission/` layers — it is a *separate, reviewable* backfill of minutes those
Legistar-built layers were missing, so the user can merge deliberately after review.

## Why separate from the audited minutes layer
The repo's canonical minutes come from **Legistar** and have been QA'd (`VERIFICATION.md`). PMN is a
**different publisher** with different document versions (draft/final/approved) and sparse minutes
coverage. Folding PMN files into the audited layer in place would break that provenance chain.
Recovered minutes live here with their own `index.csv`, raw originals, and a full fetch log.
**Promote rows into the main layer only after review** (e.g. the 2 in-2023 council holes could be
parsed for votes; the 4 in-2026 council minutes are simply newer than the last Legistar ingest).

## Sandy PMN ids (discover generically — ids are GLOBAL, never guess by proximity)
`/pmn/list/entities.html?id=3&limit=2000` → Sandy **entity = 260** →
`/pmn/list/publicBodies.html?id=260&limit=2000` → bodies:
**City Council = 464 · Planning Commission = 466 · Redevelopment Agency = 465 · Board of
Adjustments = 467** (advisory bodies listed in `AVAILABILITY.md`).

## Method
1. **Enumerate** each body's full notice history with the GET browse endpoint
   `/pmn/list/notices.html?id=<bodyId>&page=300`. `page` is **cumulative** (each +1 appends ~5
   older notices and re-emits the whole list newest-first), so one large page returns the entire
   history via ONE GET. Saturated HTML saved as `raw/_notices_<id>_p300.html`.
2. **Parse** rows → `{notice_id,title,date,time,attachments:[{file_id,filename,type}]}` with
   `parse_notices.py` → `council.json` / `pc.json` / `rda.json` / `boa.json`. Minutes carry the
   `(Meeting Minutes)` type label; agendas/hearing notices carry `(Other)`.
3. **Cross-check by DATE, not count** (`crosscheck.py`): for each PMN notice bearing a
   `Meeting Minutes` attachment, set-difference its meeting date against the repo's coverage,
   **±4-day tolerance** (absorbs the meeting-vs-posted offset). In-scope (≥2020) misses = the
   recovery list (`recoverable.json`). Baselines diffed against:
   - **Council** → `meeting_minutes/minutes_index.csv` (274 Legistar minutes).
   - **PC** → `planning_commission/all_votes.csv` distinct dates (repo has **no** PC minutes files;
     PC is Legistar-API-built — so any PMN PC minutes would be pure gain… but PMN has **none**).
   - **RDA** → nothing (repo has no RDA minutes layer), so all in-scope PMN RDA minutes are gains.
4. **Download** each missing PDF from `https://www.utah.gov/pmn/files/<file_id>.pdf` (attachment ids
   are **opaque** — must be crawled from list/notice pages, NEVER templated by date) via
   `scripts/polite_fetch.py` (browser UA, per-notice Referer, ≥1s throttle → `raw/_fetch_log.jsonl`).
5. **Extract** → `text/`. Born-digital PDFs use `pdftotext -layout` (the 2 RDA files). Image-scanned
   PDFs — and 2023-10-17, whose text layer is **PUA-font-garbled** (the known Sandy encoding defect;
   `pdftotext` yields private-use-area junk with zero readable keywords) — use **tesseract OCR**
   (`pdftoppm -r 300 -png` → `tesseract stdout`). Screened clean with
   `audit-city-data/scripts/screen_corpus.py text` (only advisory footer-endings and repeated
   roll-call template lines remain).

## Date-diff logic — the two critical gotchas
- **Draft vs Final are separate PMN notices on the same date.** Per-year *counts* of minutes-bearing
  notices therefore double-count meetings and are NOT the gap signal — only the per-DATE
  set-difference is. When both exist for a recovered date, prefer **Final/Approved** over Draft
  (2023-10-17 = Final; 2026-04-28 = Approved). Fallback to Draft if Final is broken
  (**2023-11-07 Final = PMN file 1052569 = 0 bytes**, so its Draft was taken).
- **Minutes can be attached to a LATER notice.** The RDA notice dated 2022-06-28 attaches minutes
  for the **2022-05-17** and **2022-06-07** RDA meetings. The true meeting date comes from the
  PDF/filename, not the notice date. (Council minutes notices, by contrast, are dated ON their
  meeting date with the date in the title — so keying on notice date is valid for council.)

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,text_path`
(the §9 pmn_backfill contract — minutes-index cols + `body`, PMN provenance, `retrieved_date`,
`extraction_method` — plus a `text_path` extra).
- `path` = dataset-relative **raw PDF** (`raw/…pdf`, the retained original); `text_path` = the
  extracted sidecar under `text/`.
- `source` = `pmn`; `retrieved_date` = `2026-07-05`; `format` ∈ {`text` (born-digital),
  `scanned` (OCR)}. `body` ∈ {`Council`, `RDA`}.
- `source_url` = the fetched PMN file PDF; `notice_url` = the human-viewable notice page.

## Coverage result (see coverage.md)
Legistar-built repo is the **superset** for council 2020+. **8 in-scope meeting dates** existed on
PMN but not the repo — **all recovered**: 6 council (2 in-2023 holes, 4 in-2026 past the last
ingest) + 2 RDA (2022-05-17, 2022-06-07). **PC minutes do not exist on PMN for Sandy** (honest
zero). **0 in-scope PMN minutes remain unrecovered.**

## Do NOT
- Do not date-template PMN file URLs (ids are opaque) or POST to `/pmn/searchresult.html` (CSRF,
  and against the polite rule — the GET browse endpoint already returns full history).
- Do not edit `meeting_minutes/` or `planning_commission/` to fold these in silently.
- Do not treat PMN's missing PC minutes as an extraction failure — it is a real coverage gap (data).

## 2026-07-17 — final PMN-crosscheck flag verification (7 flags -> 0, CLEAN)

Verified all 7 body-464 council flags; appended 7 exceptions; re-run (--cached) 7 -> **0**.
None were RDA-465 closed sessions; all were council TOURS / work sessions / a revised-agenda dup:
- other x6: 2022-07-12 (joint Cairns tour work session), 2022-09-27 (Parks facilities tour),
  2022-11-01 (mobile tour), 2023-04-25 (off-site tour), 2024-09-03 (off-site tour) — site
  tours produce no minutes; 2020-01-14 (noticed then not minuted — authoritative Legistar
  holds 01-07/01-21/01-28, not 01-14; PMN agenda-only, not a minutes gap).
- wrong_date x1: 2020-01-13 = 'Revised January 14, 2020 Agenda' (same meeting as 01-14).
No recovery leads.
