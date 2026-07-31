# packets/ — agenda packets (STORED LOCALLY, born-digital text) — as-of 2026-07-06

Built by `expand-city-sources` (Source 1). One **agenda document per meeting** for every
West Valley City public body published on the city's Hyland **OnBase "Agenda Online"**
portal — the item list behind each motion in `../meeting_minutes/all_votes.csv` (bodies
Council / RDA / MBA) and `../planning_commission/all_votes.csv` (body PlanningCommission).
Join by `date` (+ `body`; add `meeting_type` to separate same-day Study vs Regular).

> **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **C** — the four
> packet-attachment classes (staff reports/memos/DAs/plan amendments) are **HONEST ZEROS**
> (OnBase serves thin agendas only; `documentType=3` unavailable). Class 3 (full GP text) is
> handled separately in `housing_plans/`. See `AVAILABILITY.md` § "Primary-document classes".

## What WVC actually publishes (READ THIS FIRST)
WVC OnBase serves, per meeting, a **thin born-digital AGENDA PDF** (`documentType=1`) —
4–10 pages of the item outline (call to order, recognitions, public-comment period, the
numbered agenda items with case numbers `Z-`/`PUD-`/`GPZ-`, ordinances/resolutions). It is
**NOT** a compiled staff-report bundle: there are no fiscal notes, no zoning analyses, no
exhibits attached. Every packet is **~60–170 KB, extractable with `pdftotext`** (not
scanned, no OCR needed). Hence `packet_kind=agenda` for every row and `format=text`.
This is the honest ceiling of what the portal exposes — the "staff reports" branch of the
skill does not apply because WVC does not post them here (see AVAILABILITY.md).

Because the whole corpus is only **~117 MB**, it is **STORED LOCALLY** in full (unlike
Provo/St. George/West Jordan, whose OnBase packets were multi-GB compiled bundles → index-
only). `raw/<year>/<onbase_filename>.pdf` holds every packet; `index.csv` is the catalog.

## Access method (OnBase quirks — reuse for refresh)
1. **Cookie prime.** `GET https://www.wvc-ut.gov/105/Agendas-Minutes` with a browser
   User-Agent first (the city site 301-redirects and mints the session; `ob.wvc-ut.gov`
   can 403 a bare/non-browser UA).
2. **Enumerate** per year + body via the Search endpoint (GET, no POST/CSRF needed here —
   simpler than Provo's OnBase):
   `GET https://ob.wvc-ut.gov/OnBaseAgendaOnline/Meetings/Search?dropid=11&mtids=<IDs>&dropsv=01/01/YYYY%2000:00:00&dropev=12/31/YYYY%2000:00:00`
   with `Referer: .../Meetings/Search` + the cookie. The result HTML carries, per meeting,
   the full `Documents/DownloadFile/<Type>_<meetingId>_Agenda_<M>_<D>_<Y>_<time>.pdf?documentType=1&meetingId=<id>`
   href (and a `documentType=2` Minutes href — **EXCLUDE**; minutes are already in
   `../meeting_minutes/`). Filenames are self-describing (type, meetingId, date).
3. **Download** — the **`DownloadFile` URL returns a "Downloading, Please wait…" HTML
   interstitial, not the PDF.** Rewrite `DownloadFile` → **`DownloadFileBytes`** (same
   path, same query) and GET with the cookie + Referer → `application/pdf`, `%PDF`. This is
   the identical DownloadFile→DownloadFileBytes trick used for Provo's OnBase.
4. **No cheap size.** HEAD returns `302` and GET on `DownloadFile` gives the interstitial,
   so there is no Content-Length to probe — but the bodies are tiny, so we just GET each.
   `size_mb` in the index is the **measured on-disk byte size** of the stored PDF.

### Meeting-type IDs (`mtids`) — the full portal dropdown
| Body (index `body`) | mtids | dropdown labels |
|---|---|---|
| Council | 109,110,111 | City Council Regular / Special / Study |
| PlanningCommission | 103,104 | Planning Commission Meeting / Study |
| RDA | 114,115 | Redevelopment Agency Regular / Special |
| MBA | 106,107 | Building Authority Regular / Special |
| BoardOfAdjustment | 101,102 | Board of Adjustment Meeting / Study |
| HousingAuthority | 112,113 | Housing Authority Regular / Special |
| StrategicPlanning | 116 | Strategic Planning Meeting |

Council + PlanningCommission + RDA + MBA carry recorded votes elsewhere in the repo. Board
of Adjustment, Housing Authority, and Strategic Planning are also published here and are
retained (additive, no vote record to join) — `body` distinguishes them.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format,
extraction_method, path, meeting_id, size_mb, stored_locally`
- `body` ∈ Council / PlanningCommission / RDA / MBA / BoardOfAdjustment / HousingAuthority /
  StrategicPlanning. Council/RDA/MBA votes → `../meeting_minutes/all_votes.csv`; PC votes →
  `../planning_commission/all_votes.csv`.
- `meeting_type` ∈ regular / study / special (from the mtid / title). Part of the join key
  so a same-day Study and Regular meeting stay distinct.
- `packet_kind` = `agenda` for every row (WVC posts the agenda only; no staff-report bundle).
- `meeting_id` = OnBase numeric `meetingId` (also embedded in the filename + source_url).
- `source_url` = the **`DownloadFileBytes`** URL (fetch-ready with cookie+Referer).
- `format` = `text` (born-digital; `pdftotext` works). `extraction_method` = `pdftotext`.
- `size_mb` = measured on-disk MB. `stored_locally` = `yes`. `path` = repo-relative
  `raw/<year>/<filename>`.

## Coverage & join (see AVAILABILITY.md for the year table)
- **965 agenda packets, 2020–2026, stored locally (~117 MB).**
- **100% of every recorded vote date has a packet, all four voting bodies:** Council
  247/247, RDA 56/56, MBA 29/29, PlanningCommission 134/134. Packet date = meeting date,
  exact match.

## Regenerate / refresh
Re-run the three-step method above per year 2020–present for each mtid group; parse
`documentType=1` `DownloadFile` hrefs from the Search HTML; rewrite to `DownloadFileBytes`;
GET with cookie+Referer; store to `raw/<year>/`; rebuild `index.csv` (measured sizes).
Scratchpad scripts used for the initial build: `wvc_enum.py` (enumerate) + `wvc_download.py`
(fetch, resumable — skips PDFs already on disk) + `wvc_index.py` (index). `raw/_fetch_log.jsonl`
is the provenance log (one JSON line per fetch: url, status, bytes, sha256, retrieved_utc).
