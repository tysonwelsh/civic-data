# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-03

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning
analysis, alternatives, staff recommendation) behind each West Jordan **City Council**,
**RDA**, **MBA**, and **Planning Commission** agenda item — the "why" behind a motion in
`../meeting_minutes/all_votes.csv` (body Council/RDA/MBA) and
`../planning_commission/all_votes.csv` (body PlanningCommission).

> **Primary-document classes (doc_class rollout, 2026-07-16): honest no.** The four
> attachment-borne classes (`staff_report`/`member_memo`/`plan_amendment`/
> `development_agreement`) are **not separable for this PrimeGov portal** (it explicitly
> exposes no per-item staff reports; 222 whole-meeting INDEX-ONLY bundles; the 2025+ SPA era
> has no downloadable packet at all). Nothing fetched/classified/section-cut. See
> `AVAILABILITY.md` § Primary-document classes.

## PrimeGov document model (what the API exposes)
West Jordan runs **PrimeGov** (`westjordan.primegov.com`). The archive API returns, per
meeting, a `documentList` of typed documents:

```
GET https://westjordan.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY
  -> [ { id (meetingId), dateTime, title, documentList:[ {templateId, templateName, ...} ] } ]
```

`templateName` distinguishes the document type: **Agenda / HTML Agenda / HTML Interactive
Agenda** (the agenda), **Minutes**, and — the packet — one of **Complete Packet /
Meeting Materials / Packet / RDA Meeting Materials / MBA Meeting Materials**. There is
**exactly one bundled packet per meeting; PrimeGov does NOT expose separable per-agenda-item
staff-report PDFs.** The packet is a single compiled whole-meeting PDF (agenda + all staff
reports + all exhibits).

**Download URL (stable):**
```
GET https://westjordan.primegov.com/Public/CompiledDocument?meetingTemplateId=<templateId>
```
where `<templateId>` is the packet document's `templateId` (NOT its `id`, NOT the
meetingId). This **302-redirects to a time-limited Azure blob**
`https://pgwest.blob.core.windows.net/westjordan/Meetings/<meetingId>/<file>.pdf?<SAS>`.
The **SAS token expires ~2 days** — always fetch via the `CompiledDocument` URL (it mints a
fresh SAS each call), never cache a blob URL. Send a browser User-Agent (`polite_fetch.py`
does). This is the same endpoint family the minutes use.

## This is a LINK INDEX, not a document store — by deliberate design
The bundled packets are **large and image/map/plat-heavy**: min 0.4 MB, **median 12.8 MB**,
max 330 MB; the full 222-packet set = **7.36 GB**. They are **not born-digital text** — a
packet is site plans, engineering/traffic studies, and scanned exhibits, so converting to
markdown is not viable and reading one requires **vision or OCR**, not `pdftotext`. Per the
repo owner's disk-constrained decision (same as St. George), **the PDFs are not stored
locally.** `index.csv` catalogs all 222 packets with a live `source_url` + byte size so any
one can be fetched on demand.

The retention exception is intentional and scoped to this dataset: the packet PDFs are
public and re-fetchable from `source_url` at any time; **no packet body was ever downloaded**
— sizes come from HTTP `Content-Length` on a streaming GET (headers only). `raw/_fetch_log.jsonl`
retains the provenance of every probe (URL → status / content-type / bytes / final blob URL /
retrieved_utc, 2026-07-03). (The normal "retain every raw original" rule still applies to
every *other* dataset in this repo.)

## How an LLM/agent should use this
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type` for same-day Work
   vs Regular — e.g. 2022-07-13 has both a Council `regular` and a Council `work` packet).
2. To read it, **fetch `source_url`** (public GET, browser UA, follow the 302). Check
   `size_mb` first — some are >100 MB.
3. Extract with **vision or OCR**, not `pdftotext` (image-heavy). Label whatever you produce.
4. To bulk-download (re-hydrate the dataset): feed the `source_url` column to
   `polite_fetch.py --batch` **without `--max-bytes`**. Budget ~7.4 GB for all 222.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method(=not_retrieved), path, template_name, meeting_id, content_length_bytes,
size_mb, stored_locally(=no), probe_status`
- `body` ∈ `Council` (122) / `PlanningCommission` (70) / `RDA` (21) / `MBA` (9). Council +
  RDA + MBA together = the "council" side (the council sitting as itself / redevelopment /
  building authority); their votes are all in `../meeting_minutes/all_votes.csv`.
- `meeting_type` ∈ `regular` / `work` (Committee of the Whole / work sessions) / `special`.
  Part of the join key so same-day Work vs Regular packets stay distinct.
- `packet_kind` = `full_packet` for all rows — every WJ packet is the bundled whole-meeting
  compiled PDF (there is no thin agenda-only packet variant among these). `template_name`
  preserves the exact PrimeGov type (Complete Packet 70 · Meeting Materials 100 · Packet 32 ·
  RDA Meeting Materials 12 · MBA Meeting Materials 6 · Meeting Materials_Amended 2).
- `format=na` / `stored_locally=no` because nothing is stored; the row is a pointer.

## Coverage & join
- **222 packets: Council 122 · RDA 21 · MBA 9 · Planning Commission 70**, spanning
  **2022–2026** (bulk 2022–2025). Join by `date` (+ `body`, `meeting_type`) to
  `all_votes.csv`/minutes.
- **2023 & 2024 = 100% packet coverage of recorded vote dates for both Council and PC**
  (Council 25/25 + 23/23; PC 13/13 + 15/15). Packet date matches vote date exactly.
- **Documented gaps** (all real WJ publishing patterns — see `AVAILABILITY.md`):
  - **2020–2021: no packets** (PrimeGov packet publication began 2022; these meetings have
    only agenda + minutes).
  - **Mid-2025 → 2026: format shift.** WJ moved to an in-portal **HTML Interactive Agenda**
    (SPA-rendered) and stopped compiling a downloadable packet PDF for 72 council-family
    meetings — `CompiledDocument` returns `PublishedDocumentError` and no stable per-item
    attachment URL exists. 2025 PC still published Complete Packets (fully covered); 2026 PC
    reverted to agenda-only.

## Regenerate / refresh
Re-pull `ListArchivedMeetings?year=YYYY` for 2022+, re-classify council-family + PC meetings
(`title` string → body/meeting_type), pick each meeting's packet `documentList` entry, and
re-probe `/Public/CompiledDocument?meetingTemplateId=<templateId>` for Content-Length.
Rebuild `index.csv` with the same columns. See `AVAILABILITY.md` for the full method + gap
log. If WJ later exposes a compiled-packet or attachment endpoint for the interactive-agenda
meetings, backfill 2025 H2–2026.
