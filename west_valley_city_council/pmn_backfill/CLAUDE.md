# pmn_backfill — West Valley City (Utah Public Notice minutes/agenda backfill)

**Additive** dataset built by `/expand-city-sources` (PMN source type). It recovers
meeting **minutes** that exist on the Utah Public Notice site (PMN, `utah.gov/pmn`) but
are **missing from the repo's audited minutes layer**, for four bodies over 2020–2026:
City Council, Redevelopment Agency, Municipal Building Authority, Planning Commission.
PMN is an especially valuable independent check for WVC because the city's OnBase portal
intermittently 403s.

## Cardinal rule for this folder
This dataset **never edits** `meeting_minutes/` or `planning_commission/`. It is a
side-car of documents those layers do not have. The authoritative minutes remain the
OnBase-sourced markdown in the parent layers; consult those first. Use this folder only
to (a) pull a document the main layer lacks, or (b) audit PMN vs OnBase coverage.

## What's here
- `index.csv` — one row per recovered document. Schema (§9 pmn_backfill contract + `status`):
  `date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,`
  `retrieved_date,format,extraction_method,status`. `body` ∈ CC/RDA/MBA/PC.
  `status ∈ {recovered, duplicate-not-promoted, source-unavailable}` — all current rows
  are `recovered`. `format` is `text` for all (clean extractable PDFs; no OCR needed).
  `path` points at the extracted text in `raw/`.
- `raw/` — the original PMN PDFs **and** their `pdftotext -layout` text, byte-verbatim.
  `raw/_fetch_log.jsonl` is the provenance log (url, status, sha256 per fetch).
  `raw/_pmn_meta/` holds the crawl HTML (entities, bodies, per-body notice lists) that
  the gap analysis was derived from.
- `coverage.md` — per-year, per-body set-difference table + the recovered inventory.
- `AVAILABILITY.md` — CONFIRMED PMN entity + body ids (entity 307; CC 398 / RDA 399 /
  MBA 401 / PC 402), file-access URLs, and the PC honest-zero.

## Result (2026-07-06)
**11 minutes recovered:** 8 City Council, 2 RDA, 1 MBA. **PC = honest zero** (PMN
publishes agendas only for the PC — no minutes attachment on any PC notice). See
`coverage.md` for the breakdown; the gaps are the recent post-refresh tail plus
off-cycle Strategic-Planning/Budget-Retreat and Special work sessions the OnBase layer
never captured.

## How to refresh
1. `GET /pmn/list/notices.html?id=<bodyId>&page=300` for 398/399/401/402 (full history
   in one GET despite the "past 6 months" banner). Fetch via
   `.claude/skills/expand-city-sources/scripts/polite_fetch.py` (GET-only, browser UA).
2. Parse each notice's `(Meeting Minutes)` attachments; resolve the **true meeting date**
   from the title/PDF (PMN's `event_date` field is occasionally wrong — see below).
3. Set-difference against repo dates per body (exact / ±1 day on the true date — a wider
   tolerance falsely absorbs near-adjacent real meetings).
4. For each genuine gap, fetch `/pmn/files/<fileId>.pdf`, `pdftotext -layout`, verify the
   internal date, add a `recovered` row. Never modify existing minutes rows.
5. `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py west_valley_city_council/pmn_backfill`

## Gotchas learned here
- **`event_date` ≠ meeting date** (2026-02-20 Day-2 retreat is filed as 2026-02-12).
  Always trust the title/PDF date.
- **Regular and Study meetings file as separate notices** on the same date, so PMN's
  minutes-notice count is ~2× the repo's collapsed date count — the layers are aligned.
- **PC is agenda-only on PMN** — do not expect PC minutes here.
- The `notices.html` "past 6 months" banner is boilerplate; the table is the full history.

## 2026-07-17 — final PMN-crosscheck flag verification (7 flags -> 2)

Verified all 7 (date_mode=exact); appended 5 exceptions; re-run (--cached) 7 -> **2**.
- **Recovery leads (2, count_mismatch):** 2021-09-28 — repo holds the Regular Meeting only; PMN
  also carries the Study Meeting (SM 09.28.2021.pdf) = missing study-meeting minutes;
  2022-02-01 — repo holds RM+SM (2); PMN also carries 'Strategic Plan Minutes 2022.pdf' =
  missing strategic-plan-retreat minutes.
- **Exceptions:** duplicate x1 (2023-09-05 — PMN lists SM 09.05.2023.pdf TWICE; repo already
  holds RM+SM, complete); other x4 (2020-01-01 MBA 'Meetings- 2020' annual schedule; 2021-04-01
  RDA + 2021-04-01 MBA electronic-meeting/anchor-location renewals; 2026-01-05 Oath of Office
  ceremony).


## 2026-07-17 — crosscheck-lead disposition (1 promoted, 1 transcript-not-promoted)

- **2021-09-28 Study Meeting — PROMOTED** into `meeting_minutes/` (SM 09.28.2021.pdf, file
  767025, notice 704753; repo had only the Regular Meeting for that date). Genuine WVC Council
  Study Meeting minutes; +2 tally-only voice-vote motions (approve prior study minutes; convene
  closed session). source=pmn/format=text. Raw+text: `raw/wvc_cc_2021-09-28_study_767025.*`.
- **'Strategic Plan Minutes 2022.pdf' (file 826291) — NOT promoted (wrong class + wrong date).**
  Content-verification shows it is a **verbatim court-reporter TRANSCRIPT** (DepomaxMerit
  Litigation Services, reporter L. Payeur), not minutes, with 0 formal motions; and its true
  internal date is **January 28, 2022** (a two-day 01/28–01/29 strategic-planning retreat), NOT
  the Feb-1 notice date it was filed under. It belongs in the `transcripts/` layer, not the
  structured minutes layer. Retained + catalogued here as `status=recovered-not-promoted`
  (`raw/wvc_cc_2022-01-28_strategic-planning-transcript_826291.*`). Reported as a scope question.
