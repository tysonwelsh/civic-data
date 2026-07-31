# summit_county / packets — land-use agenda packets & staff reports

Additive dataset: the Summit County Planning Commissions' **agenda-packet PDFs** (each a
meeting's concatenated **staff reports** + attachments) as a **text-only corpus** with the
SCHEMA_SPEC §9 primary-document `doc_class` columns from day one. Built by
`build_packets.py` from the **Granicus** portal (the cloudfront agenda-packet links parsed
off `ViewPublisher.php?view_id=1`). **As-of 2026-07-20.**

## §9 link-not-mirror decision (why no binaries)
Agenda packets are born-digital but **bulky (7-20 MB each, 35-433 pp)** and total ~1.8 GB.
Per SCHEMA_SPEC §9's sanctioned text-layer pattern, each packet is **fetched, sha256'd, its
text extracted to a sidecar, and the binary DISCARDED** (public + re-fetchable via
`source_url`; the sha256 + fetch log is the provenance). `stored_locally=no`, `path` blank —
`text_path` is the searchable artifact.

## Layout
```
packets/
  index.csv   122 rows (65 Snyderville + 57 Eastern agenda packets, 2022/2023-2026)
  text/       118 text sidecars (<date>_<body_slug>_packet.txt); median ~116k chars
  build_packets.py
  CLAUDE.md
```
No `raw/` binaries by design (see above).

## index.csv columns
`date, body, body_slug, packet_kind, title, clip_id, path, text_path, format, source_url,
stored_locally` + the §9 pilot columns `doc_class, fetch_status, sha256, text_chars`.
- `packet_kind` = `agenda_packet` (the full meeting packet; individual per-item staff
  reports are not separately downloadable from Granicus — they live inside the packet).
- `doc_class` = **`staff_report`** for every row — these are land-use PC packets whose
  substance is the county planner staff reports (CUP / rezone / plat / subdivision / SPA /
  MPD / low-impact-permit / code & general-plan-amendment analyses).
- `fetch_status` (§9 CLOSED vocab): `ok` (118, text extracted) | `needs_ocr` (4 — image-only
  packets, no text; sha256 retained, re-fetchable). `sha256` = the fetched binary's hash.
- `clip_id` = the Granicus clip; joins to `land_use/` minutes for the same meeting on
  `(body_slug, date)`.

## Coverage & honest boundaries
- **Granicus-era only (Snyderville 2022-11+, Eastern 2023-03+).** Pre-migration (2015-2024)
  staff reports were hyperlinked from AgendaCenter agendas as individual `DocumentCenter/View`
  PDFs — a future pass could harvest those; this build did not (AgendaCenter is agenda-only
  and its per-item links require parsing each agenda PDF).
- 4 `needs_ocr` packets are honest image-only gaps, not extraction failures.
- Federation: `text_path` → `fts_packet`; `doc_class` → `document.doc_class` (orchestrator-
  side; not run here). This dataset never edits `db/`, `land_use/`, or `development/`.
