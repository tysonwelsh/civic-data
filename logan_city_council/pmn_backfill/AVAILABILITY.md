# PMN backfill — availability record (Logan)

**As-of:** 2026-07-05 · **Checked by:** expand-city-sources Source 4 (Utah Public Notice / PMN cross-check)

## Result in one line
Logan's audited **Revize** minutes layer is a **complete superset** of what the Utah Public Notice
Website (PMN) carries for **2020–2026**. **Zero genuine minutes gaps** were found for Council, RDA,
or Planning Commission. Three PMN minutes attachments that a naïve notice-date diff flagged were each
verified to be **already-held minutes re-attached to a later notice** — retained in `raw/` for
provenance, **not promoted** into the minutes layer.

## Logan PMN ids (discovered via the global chain, as-of 2026-07-05)
- Government type 3 = Municipality → `/pmn/list/entities.html?id=3&limit=2000` → **Logan entity id = 189**.
- `/pmn/list/publicBodies.html?id=189&limit=2000` → every Logan body + id (full list in `AVAILABILITY`
  table below and in `raw/_bodies_189.html`). The three meeting bodies in scope:

| Body | PMN body id | Notices (full history) | Date span | In-window (2020–26) notices w/ Meeting-Minutes attachment |
|------|------------:|-----------------------:|-----------|--------------------------------------------------------:|
| **Municipal Council** | **494** | 1453 | 2008-04-15 … 2026-07-07 | 151 |
| **Planning Commission** | **487** | 439 | 2001-12-13 … 2026-07-09 | 23 (all ≤2021) |
| **Redevelopment Agency** | **495** | 200 | 2008-05-20 … 2026-06-16 | 43 |

Other Logan bodies enumerated but **out of scope** for a minutes backfill (no repo minutes layer to
diff against): Board of Adjustments 489, Land Use Appeal Board 490, Historic Preservation Committee
488, Planning-adjacent advisory boards (Parks/Rec 485, Light&Power 486, Forestry 493, Library 484,
Fine Arts 496, Neighborhood Council 497), Civil Service Commission 492, Construction Board of Appeals
491, and newer bodies (Citizens Advisory 3473, Renewable Energy & Sustainability 2187, Solid Waste
8649, Regional Wastewater Rate 5307, Water/Wastewater Dept 9353, Golf 1410, Zoo 1409).

### ⚠️ Recon correction
The build recon claimed **RDA = PMN body id 1277** (notice history `noticehistory/79437.html`). That
is **WRONG**: `/pmn/list/notices.html?id=1277` returns the **Salt Lake City** Redevelopment Agency.
Logan's RDA is **body 495** (confirmed: its notices are titled "Redevelopment Agency Meeting", "Logan
Redevelopment Agency Agenda", etc., entity 189). Always resolve ids via the global chain, never from a
hand-noted number.

## Method (GET-only, throttled, logged)
1. **Enumerate** each body's full notice history with the cumulative GET browse endpoint
   `/pmn/list/notices.html?id=<bodyId>&page=300`. `page` is cumulative (each increment appends older
   rows and re-emits the whole list newest-first), so one large page returns the entire history in one
   GET — no POST/CSRF search used. Saturated pages saved as `raw/_notices_<id>_p300.html` (all three
   reach back to 2001–2008, i.e. fully saturated).
2. **Parse** rows → `{notice_id,title,date,attachments:[{file_id,filename,type}]}` with
   `parse_notices.py` → `body_494.json` / `body_487.json` / `body_495.json`. Minutes carry the
   `(Meeting Minutes)` type label; Logan has no separate `(Agenda)` type (agendas are the notice
   itself, attachments typed `Other`/`Public Information Handout`).
3. **Cross-check** (`crosscheck.py`): for each in-window (2020–26) PMN notice bearing a `Meeting
   Minutes` attachment, set-difference its date against the repo minutes index (Council & RDA split by
   `slug` in `meeting_minutes/minutes_index.csv`; PC in `planning_commission/minutes_index.csv`),
   ±4-day tolerance. → `recoverable.json`.
4. **Verify each candidate at the document level** (the step that matters — see caveat) by downloading
   the PDF (`scripts/polite_fetch.py`, browser UA, notice-page Referer, ≥1s throttle,
   `raw/_fetch_log.jsonl`) and reading the actual meeting date printed inside.

## The three flagged candidates — all resolved to already-held minutes
| Notice date | Body | File | Actual minutes date inside | Repo already has it? |
|-------------|------|-----:|----------------------------|----------------------|
| 2020-03-17 (CANCELLED mtg) | Council 494 | 584203.pdf | **March 3, 2020** | yes — `meeting_minutes 2020-03-03` |
| 2020-03-17 (CANCELLED mtg) | RDA 495 | 584229.pdf (md5-identical to 584203) | **March 3, 2020** | yes — `meeting_minutes 2020-03-03` |
| 2026-06-16 | Council 494 | 1447537.pdf | **May 26, 2026** (Budget Workshop) | yes — `meeting_minutes 2026-05-26` |

## What is NOT here (honest gaps / deliberate exclusions)
- **No net-new minutes.** 0 recovered documents were promoted; the repo already carries every
  in-window meeting PMN has minutes for.
- **Pre-2020 PMN minutes** (Council/PC/RDA back to 2001–2008) are below the repo's 2020 data floor —
  enumerated in `body_*.json`, deliberately not downloaded.
- **PMN PC minutes stop after 2021** (last minutes-bearing PC notice is 2021; 2022+ PC notices carry no
  minutes attachment). The repo's PC minutes (from Revize/Community Development) run through 2026 and
  are the authoritative superset.
- **RDA on PMN carries fewer minutes than the repo** (43 in-window vs the repo's 49) — no gap.
- **PMN historical search is POST-only** (`/pmn/searchresult.html`, CSRF) — disallowed by the
  polite-scraper rule; the GET cumulative browse endpoint returned full per-body history, so no coverage
  was lost.
- **Non-meeting bodies** (Board of Adjustments, Land Use Appeal Board, advisory boards) were not
  diffed — the repo has no minutes layer for them to backfill.

## ⚠️ Methodological caveat (notice date ≠ minutes date)
On PMN, the `Meeting Minutes` attachment on a notice is almost always the **prior** meeting's minutes
(the set approved at the noticed meeting), and CANCELLED-meeting notices re-attach the last real
meeting's minutes. A date diff on the **notice** date therefore surfaces false positives. The robust
check is to read the meeting date printed **inside** each candidate PDF and diff *that* against the
repo — which is what was done here for all three candidates. The near-1:1 per-year counts (repo Council
149 vs PMN 151; repo RDA 49 vs PMN 43; repo PC 130 vs PMN 23) independently confirm the repo is the
superset.

## Provenance
Raw bytes + SHA-256 + HTTP status for every fetch: `raw/_fetch_log.jsonl` (written by
`scripts/polite_fetch.py`). Parser + cross-check code: `parse_notices.py`, `crosscheck.py`. Full parsed
notice inventories: `body_494.json` (Council), `body_487.json` (PC), `body_495.json` (RDA). Flagged
candidates: `recoverable.json`.
