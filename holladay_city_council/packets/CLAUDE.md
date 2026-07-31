# Holladay packets — build method, linkage, caveats

Additive dataset (expand-city-sources source 1). **Whole-meeting agenda packets** (agenda +
staff reports + exhibits) for Holladay **City Council / Planning Commission / RDA / LBA**, from
the city-native **SuiteOne** portal. Purely additive — no existing dataset was touched.

- **Mode: STORED.** All 78 packets on disk under `raw/<date>/`, born-digital text sidecars under
  `text/`. 909 MB raw + 49 MB text; total Content-Length 952.9 MB, inside the ~1.45 GB budget.
- **Window: 2025-01-02 → 2026-09-01** (SuiteOne's full depth; upcoming 2026 packets post ahead).
- **Floor is real:** no agenda-packet archive exists before 2025 on SuiteOne, Revize, or Wayback
  — see `AVAILABILITY.md`. Not a scraper miss.

## Build pipeline (idempotent; re-runnable)
1. `GET https://holladayut.suiteonemedia.com/` → save the server-rendered Recent-Events HTML.
2. `python3 parse_suiteone_events_holladay.py <saved.html> > events_inscope.tsv`
   — parses each `<tr>` into (date, body, eventid, apid, aid, mid). Body classification:
   title contains `planning commission`→PlanningCommission, `local building authority`/`lba`→LBA,
   `rda board`→RDA, `& rda`/`council`/`legislative`→Council. In-scope = Council/PC/RDA/LBA only.
3. `python3 fetch_packets_holladay.py` — GETs each event's Agenda Packet
   (`/event/GetAgendaPacketFile/Packet?apid=<apid>`, Referer the event page) via the shared
   `polite_fetch.save()` into `raw/<date>/<body>_e<eventid>_packet.pdf`, with a per-date
   `_fetch_log.jsonl` (url/status/bytes/sha256/retrieved_utc) and a running BUDGET guard that
   would flip remaining packets to index-only past 1.45 GB (never triggered). → `fetch_results.tsv`.
4. `python3 build_packets_index_holladay.py` → `index.csv` (see schema below).
5. `python3 ../../scripts/extract_packet_text.py holladay` — `pdftotext -layout` → `text/<stem>.txt`
   for every born-digital PDF (78/78 extracted; log at `text/_extraction_log.csv`).
6. `python3 build_packets_index_holladay.py --with-extraction` — reconciles `format` /
   `extraction_method` from the extraction log (all `text` / `pdftotext -layout`).
7. `python3 ../../.claude/skills/audit-city-data/scripts/screen_corpus.py text` — corpus QC.

## index.csv schema (SCHEMA_SPEC §9 packets contract + city extras)
Contract prefix (exact, in order):
`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path`
City extras AFTER the contract columns: `apid,eventid,size_mb,stored_locally`.
- `title` — verbatim SuiteOne event title.
- `body` ∈ Council / PlanningCommission / RDA / LBA — joins to `meeting_minutes/all_votes.csv`
  (Council/RDA/LBA) and `planning_commission/all_votes.csv` (PlanningCommission) on `date`.
- `meeting_type` ∈ regular / work / special (derived from the title; most are regular).
- `packet_kind` = `full_packet` (SuiteOne "Agenda Packet" = whole-meeting bundle).
- `source_url` — the live `GetAgendaPacketFile/Packet?apid=` URL (re-fetchable).
- `format` = `text` for all (born-digital); `extraction_method` = `pdftotext -layout`.
- `path` — dataset-relative **including** `raw/` (e.g. `raw/2025-01-07/PlanningCommission_e2852_packet.pdf`).

## Linkage
Join packets to votes/minutes by `date` + `body`. Holladay meets Thursday (Council) /
modal-Tuesday (PC); one packet per meeting event. 28/36 Council and 13/29 PC packet dates match
a recorded vote date — unmatched are recent/upcoming 2026 meetings whose minutes have not yet
posted to PMN, or meetings with no roll-call vote. Do not force a match.

## SuiteOne portal caveats (verified 2026-07-13)
- **HEAD → 404** and **Range ignored** on the packet route: `--size-only` cannot size these; a
  full GET is the only way to learn Content-Length (sizing was folded into the store pass).
- Both `.../Packet?apid=N` and `.../Agenda%20Packet?apid=N` return the same PDF (label cosmetic).
- The portal's date/keyword search is **POST-only** (`/Home/GetRecentEvents`); GET-only harvest
  relies on the unfiltered landing dump, which already reaches SuiteOne's true 2025 floor.
- **Never hand-edit** `index.csv`/`fetch_results.tsv`/`events_inscope.tsv` — regenerate via the
  scripts above. Raw PDFs and `_fetch_log.jsonl` are never modified or deleted.

## Refresh
Re-run steps 1–7. `fetch_packets_holladay.py` re-downloads (idempotent by filename); to fetch
only new events, diff new `events_inscope.tsv` apids against `index.csv`.

## Primary-document classes
Assessed 2026-07-16 (doc_class rollout) — **not section-cut** for this SuiteOne portal (COUNCIL
STAFF REPORT banner anchors only, no TOC; owner decision). Full-packet text sidecars already
serve FTS. See `AVAILABILITY.md` § "Primary-document classes (doc_class rollout, 2026-07-16)".
