# pmn_backfill/ — build method & caveats

**Additive dataset.** Built by `expand-city-sources` **Source 4** (Utah Public Notice / PMN
cross-check). **As-of 2026-07-05.** This dataset **NEVER modifies** the audited `meeting_minutes/`
or `planning_commission/` layers — it is a *separate, reviewable* backfill of minutes those
CivicClerk-built layers were missing, so the user can merge deliberately.

## Why separate from the audited minutes layer
The repo's canonical minutes come from **CivicClerk** and have been independently QA'd
(`../VERIFICATION.md`). PMN is a **different publisher**. Mixing PMN-sourced files into the audited
layer in place would break that provenance chain. Recovered minutes live here with their own
`index.csv`, raw originals, and fetch log. Promote rows into the main layer only after review.

## PMN ids (Park City entity = 233, government type 3 = Municipality) — CONFIRMED 2026-07-05
| Body | PMN id |
|------|-------:|
| City Council | **653** |
| Planning Commission | **1860** |
| **Redevelopment Agency (RDA)** | **654** |
| Housing Authority | 657 · Municipal Building Authority | 655 |
| Historic Preservation Board | 659 · Board of Adjustment | 4645 |

Discover generically via GET: `/pmn/list/entities.html?id=3&limit=2000` → Park City = 233 →
`/pmn/list/publicBodies.html?id=233&limit=2000` → every body + id (full list in `AVAILABILITY.md`).

## Method
1. **Enumerate** each body's full notice history with the GET browse endpoint
   `/pmn/list/notices.html?id=<bodyId>&page=300` (cumulative — one high page = entire history).
   Saturated pages: `raw/_notices_<id>_p300.html`.
2. **Parse** rows → `{notice_id,title,date,time,attachments:[{file_id,filename,type}]}` with
   `parse_notices.py` → `council.json` / `pc.json` / `rda.json`. Minutes carry `(Meeting Minutes)`.
3. **Cross-check** (`crosscheck.py`): per-**date** set difference of each body's minutes-bearing
   notices vs the repo minutes index (±4-day tolerance). RDA has no repo minutes layer, so it is
   diffed for coincidence with council dates. In-scope (≥2020) misses = the recovery list.
4. **Download** each missing minutes PDF from `https://www.utah.gov/pmn/files/<file_id>.pdf`
   (opaque numeric ids — crawled, never date-templated) via `scripts/polite_fetch.py` (browser UA,
   notice-page Referer, ≥1.5s throttle, logged to `raw/_fetch_log.jsonl`). PC minutes embed full
   packets (one RDA file was 79 MB) — do not `--max-bytes` cap.
5. **Read the meeting date INSIDE each PDF** before counting (notice date ≠ meeting date; notice
   title ≠ doc type). All matched here.
6. **Extract** `pdftotext -layout` → `text/`. All born-digital; `screen_corpus.py` clean (only
   advisory footer/roll-call-template flags).

## Result (see coverage.md, AVAILABILITY.md)
The CivicClerk-built repo is the **superset** for 2020–present.
- **City Council (653):** 2 net-new minutes recovered — **2026-06-04**, **2026-06-11** (newer than
  the repo's last, 2026-05-22). `status=recovered`.
- **Planning Commission (1860):** 0 gaps.
- **Redevelopment Agency (654) — the high-value check, honest ZERO:** all 14 in-scope "RDA"
  Meeting-Minutes attachments are **re-postings of the combined City Council minutes** (each header
  `CITY COUNCIL MINUTES <date>`, with the in-council RDA recess) for a date the repo already holds.
  **No standalone RDA minutes exist on PMN** → nothing to promote as a new body layer. Retained +
  indexed `status=duplicate-not-promoted`. The repo's `body=RDA` rows already model the RDA.
- **0 source-unavailable (404-purged).**

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,`
`retrieved_date,format,extraction_method,raw_path,status,note` (repo minutes schema + provenance + gap flags).
`path`/`raw_path` are repo-relative; `source=pmn`; `format=text`; `status` ∈
`recovered` / `duplicate-not-promoted`.

## Join back to the repo
The 2 recovered council rows join by **meeting date** to `meeting_minutes/all_votes.csv` and the
weekly grid; both contain full roll-call votes in the standard template and could be parsed if
promoted. The 14 RDA duplicates share the meeting date of an existing repo council minutes file.

## Do NOT
- Do not date-template PMN file URLs (ids are opaque) or POST to `/pmn/searchresult.html` (CSRF;
  the GET browse endpoint already returns full history).
- Do not treat PMN body 654 attachments as standalone RDA minutes — verified to be combined council
  minutes.
- Do not edit `meeting_minutes/` or `planning_commission/` to fold these in silently.


## 2026-07-17 — crosscheck flag verification (14 flags → 0 leads, 14 exceptions)

Verified every 2026-07-17 crosscheck flag (cached list HTML + repo indexes across council
AND PC datasets + throttled per-notice GETs). Re-run after appending exceptions: **0 flags
— clean** (14 suppressed). CONFIRMS the CivicClerk repo is a genuine superset for 2020+;
zero recovery leads.

**Exceptions written (14), by kind — all `other` except one `wrong_date`:**
- **Body-level CANCELLATIONS** (5; RE_CANCEL reads only the list title, which stayed
  'Regular/Special Meeting' while the body said cancelled): Council 2020-03-26, 2021-01-14;
  PC 2021-12-22, 2022-01-19, 2022-11-23.
- **Annual meeting-schedule postings** (4, synthetic Jan-1 / full-year event dates):
  Council 653 2020-01-01, RDA 654 2020-01-01, PC 1860 2025-01-01, PC 1860 2026-01-01.
- **JOINT City Council + Planning Commission meetings riding the PC body 1860** but filed
  in `meeting_minutes` (council dataset) — cross-filing (3): 2022-03-15, 2025-08-18,
  2026-02-03. Repo holds all three under council.
- **Non-meeting / no-business** (1): Council 2020-05-08 (majority attended a sanitizer
  distribution, 'No City business conducted').
- `wrong_date` (1): Council 2020-06-03 — 'Public Hearing' event date 06-03 but body states
  the hearing is held 2020-06-18, which repo holds.

**Hardening candidates:** (1) body-cancellations + (2) annual-schedule postings dominate
(9 of 14) — see engine notes. (3) Joint CC+PC meetings ride PC body 1860 but file under
council → a multi-dataset match (`planning_commission;meeting_minutes`) on 1860 absorbs them.
