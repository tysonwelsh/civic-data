# pmn_backfill/ — build method & caveats

**Additive dataset.** Built by `expand-city-sources` **Source 4** (Utah Public Notice / PMN
cross-check). **As-of 2026-07-02.** This dataset **NEVER modifies** the audited
`meeting_minutes/` or `planning_commission/` layers — it is a *separate, reviewable* backfill of
minutes those Granicus-built layers were missing, so the user can merge deliberately.

## Why separate from the audited minutes layer
The repo's canonical minutes come from **Granicus** and have been independently QA'd
(`VERIFICATION.md`). PMN (Utah Public Notice Website) is a **different publisher** with different
document versions and sparse minutes coverage. Mixing PMN-sourced files into the audited layer
in place would break that provenance chain. Instead, recovered minutes live here with their own
`index.csv`, their own raw originals, and a full fetch log. Promote rows into the main layer only
after review.

## PMN public-body ids (Lehi entity = 184, government type 3 = Municipality)
| Body | PMN id |
|------|-------:|
| City Council | **2512** |
| Planning Commission | **2651** |
| RDA | 3315 |
| Local Building Authority | 7881 |
| Board of Adjustments | 2661 |
| Appeal Authority | 5645 |
| (advisory: Parks/Trails/Trees 2829, Historic Preservation 3879, Library Board 3701, Trails 2643, PARC 7645, Elections 9347) | — |

Discover these generically via GET: `/pmn/list/entities.html?id=3&limit=2000` → find the city's
entity id (Lehi=184) → `/pmn/list/publicBodies.html?id=184&limit=2000` → lists every body + id.
(Body ids are assigned globally, NOT sequentially per city — do not guess by proximity to 2512.)

## Method
1. **Enumerate** each body's full notice history with the GET browse endpoint
   `/pmn/list/notices.html?id=<bodyId>&page=<N>`. `page` is **cumulative** (each +1 appends ~5
   older notices and re-emits the whole list newest-first), so one large page (200) returns the
   entire history. Saturated pages saved as `raw/_notices_<id>_p200.html`.
   - Council 2512: 981 notices (2009-10-27 … 2026-06-09).
   - PC 2651: 565 notices (2010-02-04 … 2026-07-09).
2. **Parse** rows to `{notice_id, title, date, time, attachments:[{file_id, filename, type}]}`
   with `parse_notices.py` → `council.json`, `pc.json`. Minutes carry the `(Meeting Minutes)` type.
3. **Cross-check** (`crosscheck.py`): for each PMN meeting with a `Meeting Minutes` attachment,
   set-difference its date against the repo minutes index (±4-day tolerance, to absorb the repo's
   meeting-date vs posted-date offset). In-scope (≥2020) misses = the recovery list.
4. **Download** each missing minutes PDF from `https://www.utah.gov/pmn/files/<file_id>.pdf`
   (attachments have **opaque numeric ids** — must be crawled from notice/list pages, never
   templated by date) via `scripts/polite_fetch.py` (browser UA, notice-page Referer, ≥1s throttle,
   logged to `raw/_fetch_log.jsonl`).
5. **Extract** `pdftotext -layout` → `text/`. All 6 are born-digital, `extraction_method` =
   `pdftotext -layout`. Ran `audit-city-data/scripts/screen_corpus.py text` — clean (only advisory
   `ends_mid` = page-footer endings, and one `repeated_line` = repeated roll-call template lines).

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`
(the §9 pmn_backfill contract — the repo's minutes schema plus `notice_url,pmn_body_id,pmn_file_id`
PMN provenance; `body` blank where not recorded).
- `source` = `pmn`; `retrieved_date` = `2026-07-02`; `format` = `text`.
- `source_url` = the PMN file PDF (the fetched bytes); `notice_url` = the human-viewable notice page.
- `path` = repo-relative text sidecar; the raw PDF is `raw/<same basename>.pdf`.

## Coverage result (see coverage.md)
The Granicus-built repo is the **superset** for 2020-present (more minutes than PMN carries every
in-scope year). Only **6** meeting **dates** existed on PMN but not the repo — all recovered:
3 council (2020-02-04 WS, 2020-08-04 joint WS, **2021-07-13 regular meeting**) and 3 PC 2025 work
sessions (03-06, 08-07, 09-04). **0 in-scope PMN minutes remain unrecovered.** Pre-2020 PMN minutes
(127 council / 10 PC) are out of scope (below the 2020 floor) and left un-downloaded but enumerated.

## Join back to the repo
Recovered rows join to the existing datasets by **meeting date** (same key as
`meeting_minutes/all_votes.csv` and the weekly grid). The 2021-07-13 council minutes contain full
roll-call votes in the standard template and could be parsed into votes if promoted.

## Do NOT
- Do not date-template PMN file URLs (ids are opaque) or POST to `/pmn/searchresult.html`
  (CSRF, and against the polite-scraper rule — the GET browse endpoint already returns full history).
- Do not edit `meeting_minutes/` or `planning_commission/` to fold these in silently.

## Crosscheck verification note — 2026-07-17 (pmn_crosscheck flag review)
All 32 flags from `scripts/pmn_crosscheck.py lehi` triaged. Wrote 4 rows to
`pmn_exceptions.csv` (re-run: 32 → **28** flags, 4 suppressed, 1 pending-adoption):
- **mislabel** 2022-02-17 (Parks/Trails/Trees advisory) + 2025-05-22 (PARC advisory) —
  advisory bodies (2829/7645, out of Source-4 scope) posted under Council body 2512.
- **mislabel** 2026-04-14 — RDA agenda posted under 2512 (RDA is body 3315; RDA=0 by design).
- **not_minutes** 2026-05-12 — statutory "NOTICE OF PROPOSED DISPOSITION OF REAL PROPERTY".
The remaining 28 are honest gaps/leads, NOT noise, left visible:
- **2 STRONG recovery leads (missing_minutes)** — PC Work Session minutes on PMN the repo
  lacks: 2026-03-05 ("03.05.26 PC Minutes.pdf") + 2026-05-07 ("05.07.26 PC Minutes.pdf").
- **8 council 2026 agenda-only dates** (2026-02-05/02-09/02-10/03-09/03-10/04-13/04-28/05-11):
  the KNOWN city-side staleness — Lehi posted no council minutes after 2026-01-27 (see the
  parent CLAUDE "Refreshing" note; 19 meetings unposted). Agenda-only on PMN too → NOT
  recoverable now; honest pending-publication gaps, not a repo fetch miss.
- **~10 older council/PC work sessions, joint meetings & specials** (agenda-only): Lehi
  publishes standalone work-session minutes only rarely (1 in the whole index) — likely
  never-published, but left as leads-with-scope-question.
- **3 annexation/boundary public-hearing NOTICES under council** (2020-03-17/2021-11-23/
  2022-03-31): hearings ride a regular council meeting; deliberately NOT suppressed (irregular
  COVID-era cadence — review-gate decides if any is a genuinely missing meeting).
Weak hardening candidate reported to engine owner: add "disposition of real property" to
`RE_NOT_MEETING` — only 1 instance across the 3 cities verified this round (below the
≥5-sample bar), handled per-city via the not_minutes exception above.

### 2026-07-17 — 2 PC Work Session recoveries (the STRONG missing_minutes leads)
Fetched, content-verified, and added the 2 PC Work Session minutes flagged above (now rows
7–8 of `index.csv`, `source=pmn`, `pmn_body_id=2651`, `retrieved_date=2026-07-17`; raw PDFs in
`raw/pc_2026-*_work-session.pdf`, text sidecars in `text/`, fetch logged):
- **2026-03-05** (file 1458781) — header/footer print "March 5, **2025**" but that is a CLERK
  YEAR-TYPO: "Thursday, March 5" is a Thursday only in 2026, the minutes are "Approved: March 26,
  2026", and the PMN filename is "03.05.26 PC Minutes.pdf". True date **2026-03-05**.
- **2026-05-07** (file 1458743) — "Thursday, May 7, 2026", approved June 11, 2026. Clean.

Both are genuine approved minutes (NOT drafts). Neither carries a substantive vote — only a
tally-only adjournment ("moved to adjourn … passed unanimously"). Kept in `pmn_backfill/`
**exactly like the 3 existing 2025 PC Work Session recoveries** (2025-03-06 / 08-07 / 09-04):
Lehi's audited `planning_commission/` layer is regular-meetings-only (0 work sessions), and no
PMN PC-work-session recovery has ever been folded into it, so promoting these two there would
break that convention and inject a never-present meeting type for no vote gain. `validate_city.py
lehi` = 26 PASS / 0 WARN / 0 FAIL. (If a later decision DOES want work sessions in the audited
PC corpus, promote all five together for consistency.)
