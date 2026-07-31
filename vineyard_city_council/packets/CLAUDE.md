# vineyard_city_council/packets — how to use this dataset

Additive dataset of Vineyard **agenda + agenda-packet (staff-report) documents** for City
Council (incl. the 2014-era *Town Council*), Planning Commission, and the Redevelopment
Agency (RDA) board, harvested from the CivicClerk (CivicPlus) OData API. Additive only — it
never modifies `meeting_minutes/`, `planning_commission/`, or any other dataset. Read
`AVAILABILITY.md` first for coverage, the storage decision, and gaps.

> **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **B-no** — the four
> packet-attachment classes (staff reports/memos/DAs/plan amendments) are **not separable** here
> (all 926 rows index-only, no text layer). See `AVAILABILITY.md` § "Primary-document classes".

## What's here

- `index.csv` — one row per **document** (not per event). **926 rows**: 807 Agendas + 119
  Agenda Packets, across 3 bodies. Minutes are excluded (they live in `meeting_minutes/`
  and `planning_commission/`).
- `raw/_fetch_log.jsonl` — one JSONL line per document: the **size-probe** provenance
  (url, event_id, file_id, body, probed `content_length`). This dataset is **INDEX-ONLY**
  (see AVAILABILITY size math — the corpus is ~7.2 GB, ~18× the local-store budget), so no
  document bodies are stored; `raw/` holds only this log.

## index.csv columns

`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,`
`extraction_method,path,event_id,file_id,size_mb,stored_locally`

- `date` — event date `YYYY-MM-DD` (from CivicClerk `eventDate`; naive local date).
- `title` / `meeting_type` — verbatim CivicClerk `eventName` (e.g. `City Council Meeting`,
  `Planning Commission Regular Meeting Agenda`, `Town Council Meeting - Regular Agenda`,
  `Redevelopment Agency Board Meeting`). City-faithful; not normalized. Both columns carry
  the same string (min-schema `title` + explicit `meeting_type`).
- `body` — `Council` | `PlanningCommission` | `RDA`. **Joins to the vote datasets by
  `date` + `body`:** Council + RDA → `meeting_minutes/all_votes.csv`; PlanningCommission →
  `planning_commission/all_votes.csv`. (2014-era "Town Council" events are `body=Council`.)
- `packet_kind` — `agenda` (the published Agenda; in Vineyard this bundles attachments and
  averages ~5 MB) | `agenda_packet` (the full staff-report bundle).
- `event_id` — CivicClerk event id; keys the download function and disambiguates events.
- `file_id` — CivicClerk file id; the argument to the download function.
- `source_url` — `…/Meetings/GetMeetingFileStream(fileId=<id>,plainText=false)`; live and
  stable for every row. Append `plainText=true` instead for clean extracted text.
- `size_mb` — measured Content-Length where a probe captured it; **blank where unknown**
  (probe was not exhaustive — all packets but one are sized; agendas are partially sized).
- `stored_locally` — `no` for every row (index-only). `path` is empty for every row.
- `format` — `na` for every row (nothing stored → no text/scanned determination made).
- `extraction_method` — `civicclerk_odata`.

## How the harvest worked (repro / refresh)

1. Enumerate ALL events via OData, following `@odata.nextLink` to the end (page size 15;
   `$top` is a hard cap that truncates — do not rely on it). 1,441 events across 15
   categories; keep `categoryName` ∈ {`City Council`, `Planning Commission`,
   `Redevelopment Agency`}, past events only.
2. Each event's `publishedFiles[]` gives `{fileId,type,name}`. Keep `Agenda` +
   `Agenda Packet`; skip `Minutes` (already in the minutes datasets).
3. Size each file with a streamed GET reading `Content-Length` without consuming the body
   (HEAD → 405; Range ignored). Corpus ≈ 7.2 GB ⇒ INDEX-ONLY.

To refresh: re-enumerate, diff `(event_id,file_id)` against `index.csv`, append rows for
new documents. Idempotent by `file_id`.

## CivicClerk / OData quirks (Vineyard-specific — beyond the Orem set, worth promoting)

- **`$top=N` is a hard result cap, not a page size.** `Events?$top=100` returns exactly 100
  and NO `@odata.nextLink` — silently truncating the tail (we first got only 100 of 1,441,
  cut off at 2024). Always page from an unbounded `Events` and follow every `nextLink`.
- **"Agenda" files are NOT tiny outlines here.** Unlike Orem (0.1 MB born-digital Agenda
  outlines), Vineyard bundles attachments into the Agenda file → avg **5.17 MB**, max
  59.9 MB. So even the Agenda layer is too large to store under budget; both layers are
  index-only. Don't assume "Agenda = small" for a new CivicClerk city — probe first.
- **The 2014-era body is labelled `Town Council` in `eventName`** but sits under
  `categoryName = 'City Council'` — one continuous body. Mapped to `body=Council`.
- Everything else matches the verified Orem CivicClerk recipe: documents live in
  `publishedFiles[]` (the `agendaFile`/`minutesFile` scalar slots are null);
  download via `Meetings/GetMeetingFileStream(fileId=…,plainText=false)`; HEAD → 405 and
  Range is ignored (size via a streamed GET); the `publishedFiles[].url` stream path
  resolves to the SPA shell, not the PDF — use `fileId`.

## Cardinal rules honored

Never fabricated: cancelled/test events and the 2 real meetings with no agenda PDF are
recorded as honest zeros in AVAILABILITY.md, not filled. City-faithful values
(`meeting_type`, `body`) are verbatim. The bulky corpus is index-only with a live
`source_url` on every row — nothing silently capped or dropped. Minutes were not
duplicated. No existing dataset was touched.
