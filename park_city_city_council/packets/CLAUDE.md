# park_city_city_council/packets — how to use this dataset

Additive dataset of Park City **agenda + agenda-packet (staff-report) PDFs** for City
Council, Planning Commission, and the Historic Preservation Board, harvested from the
CivicClerk (CivicPlus) OData API. Additive only — it never modifies `meeting_minutes/`,
`planning_commission/`, or any other dataset. **Read `AVAILABILITY.md` first** for coverage,
the storage decision, size math, and honest gaps.

> **Primary-document classes (doc_class rollout, 2026-07-16): honest no.** The four
> attachment-borne classes (`staff_report`/`member_memo`/`plan_amendment`/
> `development_agreement`) are **not separable for this CivicClerk portal** — 468
> INDEX-ONLY agenda_packets (~30 GB) whose titles are meeting names; the 474 stored thin
> agendas already have `text/` sidecars serving FTS. Nothing fetched/classified/section-cut
> (pre-2023 PC-doc shortfall is a separate known gap). See `AVAILABILITY.md` §
> Primary-document classes.

## What's here

- `index.csv` — one row per **document** (not per event). **942 rows: 474 Agendas + 468
  Agenda Packets.** Minutes are excluded (they live in `meeting_minutes/` /
  `planning_commission/`, and Park City minutes embed the full packet anyway).
- `raw/<date>/<body>_e<eventid>_agenda.pdf` — the **474 stored Agenda PDFs** (52 MB total,
  all born-digital text). Agenda Packets are **index-only** (30 GB corpus — see the
  AVAILABILITY size math): their rows have `stored_locally=no`, empty `path`, a live
  `source_url`, and a probed `size_mb`.
- `raw/_fetch_log.jsonl` — one consolidated JSONL line per fetch: `mode=download` for the
  stored agendas (status, bytes) and `mode=size_probe` for the packets (`content_length`).
  The provenance record.

## index.csv columns

`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,`
`extraction_method,path,event_id,file_id,size_mb,stored_locally`

- `date` — event date `YYYY-MM-DD` (from CivicClerk `eventDate`; naive local date).
- `body` — `Council` | `PlanningCommission` | `HistoricPreservationBoard`. **Joins to
  `meeting_minutes/all_votes.csv` (body=Council) and `planning_commission/all_votes.csv`
  by `date` + `body`** — every Council (203/203) and PC (112/112) vote-date 2020+ has a
  match. HPB has no vote dataset.
- `title` / `meeting_type` — verbatim CivicClerk `eventName` (e.g. `City Council`,
  `City Council Meeting`, `Special City Council Meeting`, `Joint City Council and County
  Council Meeting`, `Planning Commission`, `Historic Preservation Board`). City-faithful;
  not normalized.
- `packet_kind` — `agenda` (short outline PDF) | `agenda_packet` (full staff-report bundle).
- `event_id` — CivicClerk event id; keys the download function and disambiguates the one
  Council date with two same-body events (2023-01-24).
- `file_id` — CivicClerk `publishedFiles[].fileId`; the download key.
- `source_url` — `…/Meetings/GetMeetingFileStream(fileId=<file_id>,plainText=false)`; live
  and stable for every row whether stored or not. Swap `plainText=true` for clean text.
- `size_mb` — measured bytes (on-disk for agendas; probed Content-Length for packets).
- `format` — `text` for the stored born-digital agendas; `na` for index-only packet rows.
- `stored_locally` — `yes` (agendas) | `no` (packets). `path` set iff `yes`.
- `extraction_method` — `civicclerk_odata`.

## How the harvest worked (repro / refresh)

1. Page **all** events, unbounded, following `@odata.nextLink` (never `$top` — it is a hard
   cap that silently truncates): `GET /v1/Events?$orderby=startDateTime`. Filter in code to
   `categoryName` ∈ {City Council, Planning Commission, Historic Preservation Board} and
   `eventDate` in 2020–2026.
2. Each event's inline `publishedFiles[]` gives `{fileId,type,name}`. Keep `Agenda` +
   `Agenda Packet`; skip `Minutes`/`Notice`.
3. Download / size a file: `GET …/v1/Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)`.
   Agendas are downloaded (small); packets are size-probed only (streamed GET, body unread).

To refresh: re-page events, diff `file_id` against `index.csv`, download new Agendas, probe
+ append rows for new Packets. Idempotent by `file_id` (the harvest skips agendas already on
disk and packets already probed).

## CivicClerk / OData quirks (worth promoting to the skill)

- **`EventCategories` returns null `name` for every category** — the human names live on
  each **Event** as `categoryName` / `eventCategoryName`. Map categories by reading events,
  not the categories entity. (City Council = categoryId 26.)
- **`publishedFiles[]` is already inline** in the default Event projection.
  **`$expand=publishedFiles` → HTTP 400** (don't expand it). The null
  `agendaFile`/`minutesFile` scalar slots are NOT the documents.
- **`publishedFiles[].url`** is a portal-relative stream path (`stream/PARKCITYUT/<uuid>.pdf`)
  that resolves to the SPA shell, not the PDF — ignore it; download by `fileId` via
  `Meetings/GetMeetingFileStream(fileId=…,plainText=false)`.
- **HEAD → 405 and Range is ignored** (server returns 200 + full body). Size a file without
  downloading it via a **streamed GET** that reads `Content-Length` and never consumes the body.
- **No `$top`.** The Events collection reaches back to **1995** (2,250 events total); page
  purely via `@odata.nextLink` (page size 15).
- **Agendas are tiny born-digital outlines (~110 KB)** like Orem; **Agenda Packets are
  enormous** (avg 66 MB, max 450 MB — a resort city's image-heavy staff reports) → a ~30 GB
  packet corpus, which is why packets are index-only.

## Cardinal rules honored

Never fabricated: events with no published agenda PDF are recorded as honest zeros in
AVAILABILITY.md (66 date-groups; all real meetings with video/minutes), not filled.
City-faithful values (`meeting_type`, `body`) are verbatim. Bulky packets are index-only
with live URLs and probed sizes, never silently dropped. Minutes were not duplicated. No
existing dataset was touched.
