# packets/ — availability & gap log (as-of 2026-07-06)

What was checked, what West Valley City publishes, and what it doesn't. Built by
`expand-city-sources` Source 1. Portal: Hyland **OnBase "Agenda Online"**, self-hosted at
`https://ob.wvc-ut.gov/OnBaseAgendaOnline/`.

## Method (what was checked)
The OnBase `Meetings/Search` endpoint (GET, `dropid=11` date-range) was run **live per year
2020–2026 for every meeting-type group** in the portal's dropdown (see CLAUDE.md table):
Council (mtids 109,110,111), Planning Commission (103,104), RDA (114,115), MBA/Building
Authority (106,107), Board of Adjustment (101,102), Housing Authority (112,113), Strategic
Planning (116). Each meeting's `documentType=1` (**Agenda**) `DownloadFile` href was parsed
from the result HTML, rewritten to `DownloadFileBytes`, and **fully downloaded** (cookie
primed at `www.wvc-ut.gov/105/Agendas-Minutes`, browser UA, `Referer` set, ~1 s throttle).
`documentType=2` (Minutes) hrefs were **excluded** — minutes already live in
`../meeting_minutes/`. Every fetch is logged in `raw/_fetch_log.jsonl` (url, status, bytes,
sha256, retrieved_utc). All returned `200 application/pdf` `%PDF` — **0 fetch failures.**

## What exists — 965 agenda packets, STORED LOCALLY
WVC OnBase exposes **one thin, born-digital AGENDA PDF per meeting** (4–10 pp, the item
outline with `Z-`/`PUD-`/`GPZ-` case numbers, ordinances, resolutions) — **not** a compiled
staff-report bundle. Each is ~60–170 KB and `pdftotext`-extractable. The whole corpus is
**~117 MB**, so — unlike the multi-GB compiled-bundle OnBase cities (Provo, index-only) —
**every packet is stored** under `raw/<year>/`.

| Year | Council | PlanningCommission | RDA | MBA | BoardOfAdj | HousingAuth | Strategic | Total |
|------|--------:|-------------------:|----:|----:|-----------:|------------:|----------:|------:|
| 2020 | 93 | 44 | 14 | 5 | 5 | 7 | 1 | 169 |
| 2021 | 88 | 44 | 10 | 3 | 6 | 3 | 1 | 155 |
| 2022 | 90 | 45 | 7 | 6 | 5 | 3 | 1 | 157 |
| 2023 | 90 | 44 | 6 | 8 | 4 | 4 | 0 | 156 |
| 2024 | 83 | 42 | 7 | 3 | 5 | 5 | 0 | 145 |
| 2025 | 51 | 44 | 9 | 5 | 2 | 5 | 1 | 117 |
| 2026 | 26 | 24 | 6 | 4 | 4 | 0 | 2 | 66 |
| **Total** | **521** | **287** | **59** | **34** | **31** | **27** | **6** | **965** |

(Council 2025–26 counts are lower than 2020–24 because 2020–23 posted a separate Study +
Regular agenda most weeks; recent years consolidate. Not a scraper gap — the Study/Regular
split is preserved in `meeting_type`.)

## Size math
All 965 packets downloaded and measured on disk (no estimation needed — HEAD gives no
Content-Length, so each was GET-sized directly). Per-body mean packet size ≈ 0.06–0.14 MB
(PC/Board-of-Adjustment agendas run smallest ~60–100 KB; Council/RDA/MBA/Housing ~130 KB).
**Corpus total ≈ 117 MB** — well under the ~400 MB store/index threshold, so **store-all**
is the correct mode (contrast Provo's ≈16 GB compiled-bundle set → index-only). See
`raw/_fetch_log.jsonl` for exact per-file byte counts and sha256.

## Coverage vs recorded votes (the join)
Packet date = meeting date, exact match. **100% of recorded vote dates carry a packet, all
four voting bodies:**
- **Council 247/247** vote dates (`../meeting_minutes/all_votes.csv`, body Council).
- **RDA 56/56** (`../meeting_minutes/all_votes.csv`, body RDA).
- **MBA 29/29** (`../meeting_minutes/all_votes.csv`, body MBA).
- **PlanningCommission 134/134** (`../planning_commission/all_votes.csv`).

Many packet dates have **no** recorded vote (Council 16, RDA 3, MBA 5, PC 153) — Study
meetings and no-action agendas that produced no motion. Expected; the packet still scopes
the items discussed.

## Gaps (verified, with cause)
1. **No staff-report bundles anywhere on WVC OnBase.** `documentType=1` is the agenda only;
   `documentType=2` is minutes; `documentType=3` (summary) returns "Document unavailable".
   The fiscal/zoning staff analysis behind an item is **not published** on this portal —
   an honest publishing ceiling, not a scraper miss. `packet_kind=agenda` flags every row.
2. **No standalone RDA/MBA/PC portal split needed** — all bodies share the one OnBase portal
   and are separated by `mtids` / `body`. RDA + MBA meetings are real and populated (matching
   the repo's separate RDA/MBA vote records).
3. Every enumerated `documentType=1` link resolved to a real PDF; **no cancelled/empty
   meetings and no fetch failures** (`_fetch_log.jsonl`: 0 non-PDF, 0 non-200).

## Not applicable / not done
- **Download-the-small-reports / cap-the-exhibits branch:** N/A — there are no separable
  staff reports or exhibits; the agenda is the only document.
- **PMN fallback (public body 398):** not needed — OnBase served every packet cleanly with
  the cookie+UA+DownloadFileBytes method; kept in reserve for future refreshes if the portal
  starts 403-ing.
- **OCR:** N/A — all packets are born-digital text.

## Regenerate / refresh
See `CLAUDE.md § Regenerate`. Re-enumerate per year+mtid via `Meetings/Search`, exclude
`documentType=2`, rewrite `DownloadFile`→`DownloadFileBytes`, GET with cookie+Referer,
store to `raw/<year>/`, rebuild `index.csv` with measured sizes. The downloader is resumable
(skips PDFs already on disk).

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket C** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) are **HONEST ZEROS** — a hard publishing ceiling, not a scraper
miss. No fetch, no classification was performed.

The OnBase "Agenda Online" portal serves born-digital **thin AGENDAS only** — **965** of them,
all stored locally with `pdftotext` text sidecars. No staff-report / packet / memo / development-
agreement / plan-amendment document layer exists on the portal: `documentType=3` (summary)
returns "Document unavailable" (the known Gap #1 above), and `documentType=1` is the agenda,
`documentType=2` the minutes. The agenda item lists (`Z-`/`PUD-`/`GPZ-` case numbers, ordinances,
resolutions) are agenda-item-level content, not primary documents.

**Class 3 (General Plan text) is being handled separately** as the full multi-chapter GP text
extraction under `housing_plans/` (the componentized-web-product GP; class-3 addendum) —
referenced here, not duplicated in this dataset.
