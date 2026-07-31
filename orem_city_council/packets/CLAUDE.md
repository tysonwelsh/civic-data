# orem_city_council/packets — how to use this dataset

Additive dataset of Orem **agenda + agenda-packet (staff-report) PDFs** for City Council,
Planning Commission, and Board of Adjustments, harvested from the CivicClerk OData API.
Additive only — it never modifies `meeting_minutes/`, `planning_commission/`, or any other
dataset. Read `AVAILABILITY.md` first for coverage, the storage decision, and gaps.

> **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **B-no** — the four
> packet-attachment classes (staff reports/memos/DAs/plan amendments) are **not separable** on
> this index-only CivicClerk portal. See `AVAILABILITY.md` § "Primary-document classes".

## What's here

- `index.csv` — one row per **document** (not per event). 425 rows: 221 Agendas + 204
  Agenda Packets. Minutes are excluded (they live in `meeting_minutes/`).
- `raw/<date>/<body>_e<eventid>_<kind>.pdf` — the **221 stored Agenda PDFs** (36 MB).
  Agenda Packets are **index-only** (too bulky; see AVAILABILITY size math) — their rows
  have `stored_locally=no`, empty `path`, and a live `source_url`.
- `raw/_fetch_log.jsonl` — one JSONL line per download attempt (url, status, bytes,
  sha256, content_type, final_url, retrieved_utc). The provenance record.

## index.csv columns

`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,`
`extraction_method,path,event_id,size_mb,stored_locally`

- `date` — event date `YYYY-MM-DD` (from the CivicClerk `eventDate`; naive local date).
- `body` — `Council` | `PlanningCommission` | `BoardOfAdjustment`. **Joins to
  `meeting_minutes/all_votes.csv` (`body=Council`) and `planning_commission/all_votes.csv`
  (`body=PlanningCommission`) by `date` + `body`.**
- `meeting_type` — verbatim CivicClerk `eventName` (e.g. `City Council Meeting`,
  `City Council Work Session`, `Special City Council Meeting`). City-faithful; not normalized.
- `packet_kind` — `agenda` (short outline PDF) | `agenda_packet` (full staff-report bundle).
- `event_id` — CivicClerk event id. Disambiguates the 2 dates with two same-body events
  (Council `2022-01-11`, PC `2023-08-02`) and keys the download function.
- `source_url` — `…/Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)`; live and
  stable for every row whether stored or not.
- `size_mb` — measured Content-Length (stored + index-only rows alike).
- `stored_locally` — `yes` (agendas) | `no` (packets). `path` set iff `yes`.
- `format` — `text` for stored born-digital agendas; `na` for index-only packet rows.
- `extraction_method` — `civicclerk_odata`.

## How the harvest worked (repro / refresh)

1. Enumerate events per category via OData, paging `@odata.nextLink`:
   `Events?$filter=categoryName eq 'City Council'&$top=400` (URL-encode the space; do NOT
   pair `$select` with `$orderby … asc` → HTTP 500). Categories: `City Council` (122),
   `Planning Commission` (117), `Board of Adjustments` (7).
2. Each event's `publishedFiles[]` gives `{fileId,type,name}`. Keep `Agenda` + `Agenda
   Packet`; skip `Minutes`.
3. Download a file: `GET …/v1/Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)`.
   All downloads go through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`.

To refresh: re-enumerate, diff `event_id`+`fileId` against `index.csv`, fetch new Agendas,
append index rows for new packets. Idempotent by fileId.

## CivicClerk / OData quirks (for the next CivicClerk city — worth promoting to the skill)

- **`minutesFile.fileName` / `agendaFile.fileName` are null for every event.** The real
  documents are in `publishedFiles[]`, NOT those legacy file slots. Do not conclude "no
  documents" from the null slots.
- **Download is a bound-function-on-the-collection call**: `Meetings/GetMeetingFileStream(
  fileId=…,plainText=false)` works (200 PDF). The forms that DON'T:
  `Events(<id>)/GetEventFileStream(…)` → 404; `Events/GetEventFileStream(…)` → 500;
  `GetEventFile(fileId,fileType)` (no binding) → 404; the `publishedFiles[].url`
  (`stream/OREMUT/<uuid>.pdf`) is a portal-relative path that resolves to the SPA shell,
  not the PDF — ignore it and use `fileId` instead.
- **HEAD returns 405** and **Range is ignored** (server replies 200 with full body). To
  size a file without downloading it, issue a streamed GET and read `Content-Length` from
  the response headers without consuming the body.
- Live `…/event/<id>/files` portal pages are JS-only — enumerate via the API, never WebFetch them.
- Page size is 15; always follow `@odata.nextLink` (`$skiptoken`) — a bare `$top=400`
  still paginates.

## Cardinal rules honored

Never fabricated: events with no published PDF are recorded as honest zeros in
AVAILABILITY.md, not filled. City-faithful values (`meeting_type`, `body`) are verbatim.
Bulky packets are index-only with live URLs, never silently dropped. Minutes were not
duplicated. No existing dataset was touched.
