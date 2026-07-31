# ordinances/ — availability record (as of 2026-07-13)

## What exists, where it was checked

**276 adopted ordinances indexed, #1344 (2018-08-07) → #1726 (2026-07-07); 272 in the
repo's 2020+ analytical window; 168 land-use (167 in 2020+).** Adoption-year counts:
2018:1 · 2019:3 · 2020:44 · 2021:42 · 2022:46 · 2023:20 (real — the council simply
adopted fewer; several 2023 proposals were denied) · 2024:32 · 2025:59 · 2026:29 (YTD).

1. **Utah Public Notice (PMN) — the primary independent record.** Draper entity **114**,
   **City Council body 5555** (the Recorder posts adoption notices under the Council
   body, NOT under the "City Recorder" body 9205, which holds only 6 election notices;
   the defunct council body 379 (2008–2018) has no adoption notices). Crawled the full
   cumulative list (`notices.html?id=5555&page=400`, 1,050 notices): **226 ordinance
   notices = 219 adoption notices + 7 pre-adoption public-hearing notices** (hearing
   notices catalogued in `pmn_notices.csv`, excluded from index rows). All 226 notice
   pages retained in `raw/pmn/notice_<id>.html`; **202 of 203 PDF attachments fetched**
   (38 MB) — the attachments are the Recorder's **1-page adoption-summary notice**
   (born-digital; 7 scanned → OCR), NOT the full signed ordinance text, except a
   handful of longer docs (e.g. #1488, #1493, #1523 are multi-page scans).
2. **Council minutes backbone** (`../meeting_minutes/all_votes.csv`, read-only) —
   Draper motions cite ordinance numbers richly ("moved to approve Ordinance #1625"),
   including plural forms ("Ordinances #1709, #1710, and #1711"). Used for motion
   linkage and as the ONLY witness for the 69 `within_source` rows.
3. **City news mirror** — `draperutah.gov/news/news-post/notice-of-ordinance-adoption-*`
   pages mirror a SUBSET of the PMN notices (spot-checked; not separately fetched —
   PMN is the more complete series).

## What does NOT exist / is not retrievable

- **No full-ordinance-text archive online.** The codified code lives on **American
  Legal** (`codelibrary.amlegal.com/codes/draperut` — 403 bot-protected,
  current-consolidated-text only; recorded, not mirrored). Full signed ordinances are
  "on file at the Draper City Recorder's Office" per every notice.
- **Tyler Content Manager records portal**
  (`drapercityut.contentmanager.tylerapp.com/tylercm/web/` — the city's "Search Online
  Records" link) is a JS SPA whose Document Search requires session/POST; **no
  anonymous GET API found** (probed 2026-07-13). A manual browser search there is the
  lead for full signed ordinance PDFs if ever needed.
- **PMN adoption notices before 2018-08 do not exist** (the practice started with
  #1344, the South Mountain CRA ordinance). The pre-2018 back-catalog (#1–#1343) is
  not online anywhere found.
- **2020 PMN gap:** ZERO adoption notices were posted in calendar 2020 and only ~22
  from May 2021 on — the Recorder resumed regular posting mid-2021. Ordinances
  adopted 2020 → mid-2021 are therefore witnessed **only by the council minutes**
  (the bulk of the 69 `within_source` rows).
- **One PMN attachment purged:** notice 482883 (#1344, 2018) links
  `pmn/files/421867.pdf` which 404s (logged in `raw/pmn/_fetch_log.jsonl`); the row
  falls back to the notice HTML.

## Known series holes (see `unrecovered.csv`, 44 rows)

- **22 numbers in #1410–#1726 witnessed nowhere** (no notice, no motion) — e.g. the
  1414–1461 cluster sits in the 2020–21 no-notice era where consent-agenda or
  unnumbered motions can hide an adoption; others may be unassigned/withdrawn numbers.
- **2 cited-only** (#1531, #1619): motions CONTINUE them, no approving motion and no
  notice — adoption unwitnessed.
- **20 denied** (#1448 … #1677): proposed ordinances denied by council motion — never
  adopted, listed for series completeness only. (#1517/#1518 denied 2021-12-14 5-0;
  #1562 denied 4-1 2022-12-06 — the PC-repo side of those items still exists.)
- **#1580 special case:** never noticed and never cited by a council motion, but its
  existence is proven by the #1582 notice ("amending Ordinance #1580 regarding
  prohibiting the discharge of fireworks") — a hole with an external witness.

## Notices that independently witness LOST minutes

The 2021-07-20 council meeting's minutes are unrecoverable (broken Granicus doc — see
`../meeting_minutes/minutes_unrecovered.csv`); PMN notices for **#1494, #1496, #1497**
(all stated adopted 2021-07-20) prove that meeting enacted at least three ordinances.
Likewise **#1726** (adopted 2026-07-07) falls on the recap-only meeting whose full
minutes are pending adoption. These rows carry `match_confidence=none` with the
explanation in `linkage_note` — the notice is the only witness.

## Documented Recorder errors found in this build (all handled with overrides,
sources kept verbatim — see build_index.py)

1. **#1514→#1520 renumbering** (notice 723375): the 2021-12-14 zoning-map ordinance
   was "erroneously numbered" #1514 (already used on 2021-11-16) and corrected to
   #1520 by the Recorder. The minutes motion prints 1514 → CITE_REMAPS; row medium.
2. **#1625 notice body mis-copy** (notice 947383): headline/attachment say #1625, but
   the body prints #1624 and "September 17, 2024". The subject ("vacating a city
   Right-of-Way … 984 E. Rosefield Lane") is CORRECT for #1625 (matches the
   2024-10-15 minutes agenda 7.a verbatim — the 3-2 mayoral tie-break vote). Row
   capped medium.
3. **Two wrong-PDF uploads:** notice 785825 (#1556) carries #1555's PDF; notice
   1007201 (#1661) carries #1662's PDF (byte-identical bodies). Rows point at the
   (correct) notice HTML; the mis-uploaded raws are retained.
4. **Posting-date-as-adoption-date artifacts** (7 rows: #1569, #1654–#1659): the
   notice states the Wednesday posting date as the adoption date; no council meeting
   that day; the Tuesday motion citing the number fixes the true date
   (POSTED_DATE_RULE, linkage_note records both dates).
5. **Duplicate notices:** 13 ordinances were noticed twice (e.g. #1688–#1691,
   #1716/#1717 re-posted 2026-05; #1545/#1549/#1564 double-posted) — one row each,
   secondary notice ids in `linkage_note`; #1682's notice attaches the same PDF twice.

## Verification performed

- Ground-truth sample (2026-07-13): #1495 (fireworks, 2021-06-23 m1 5-0), #1536
  (South Field Ditch easement vacation, 2022-04-19 m5 5-0), #1707 (Highland boundary
  ZMA, 2026-03-03 m3 4-0) — notice PDF text, stated adoption date, and council motion
  agree exactly on number/date/subject in all three.
- `screen_corpus.py` over `text/`: 0 stubs/mojibake/read-errors; 26 short files are
  genuine 1-paragraph notices; 10 duplicate bodies fully explained (5 pairs above);
  OCR-quality flags confined to the 7 labeled scanned files.
- The one **3-2 tie-break row (#1625)** reconciles with the city CLAUDE.md's
  documented mayoral tie-break (2024-10-15, motion 3).
