# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-13

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning analysis,
alternatives, recommendation) behind each Midvale **City Council** (incl. in-session **RDA**) and
**Planning & Zoning Commission** agenda item — the "why" behind a motion in
`../meeting_minutes/all_votes.csv` / `../planning_commission/all_votes.csv`.

## This is a LINK INDEX, not a document store — by deliberate design
Midvale's Revize CMS bundles each meeting into **one whole-meeting PDF** (agenda + every staff
report + all exhibits). These are **image/map/plat-heavy** (site plans, engineering studies), so
they are **not born-digital text** — `pdftotext` is not viable; reading one requires **vision or
OCR**. The live 110-packet set totals **2.78 GB** (median 14.8 MB; max 171 MB), which **exceeds the
~1.5 GB disk budget**, so per the skill's Revize/CivicPlus branch we **do not store the PDFs**.
Instead `index.csv` catalogs all 117 packets (2020+) with a live `source_url` + byte size, so any
specific packet can be fetched on demand.

The retention exception is intentional and scoped to this dataset: the packet PDFs are public and
re-fetchable from `source_url`; `raw/_fetch_log.jsonl` retains the provenance of the two scraped
landing pages. (The normal "retain every raw original" rule still applies to every *other* dataset.)

## How an LLM/agent should use this
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type` for the one same-day
   duplicate). Each live row has `source_url`, `size_mb`, `content_length_bytes`.
2. To read it, **fetch `source_url`** (public GET; Revize `midvale.utah.gov` Document Center PDF).
   Check `size_mb` first — some exceed 100 MB.
3. Extract with **vision or OCR**, not `pdftotext` (image-heavy). Label whatever you produce.
4. **Skip rows flagged** `not_retrieved (dead link …)` — those 7 URLs 404 on the city's own site.

## index.csv columns
SCHEMA_SPEC §9 packets contract header, then three INDEX-ONLY extras (St. George convention):
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method, path(blank), content_length_bytes, size_mb, stored_locally(=no)`
- `body` ∈ `Council` (67 live; includes in-session RDA items — Midvale's RDA has no separate
  packet stream) / `PC` (43 live). Sorted newest-first within body.
- `meeting_type` ∈ `regular` (default) / `truth_in_taxation` (the 2025-08-19 same-day second
  packet) — derived from the filename label; `special`/`work_session` reserved if a filename says so.
- `packet_kind = full_packet` for all rows (every doc is a whole-meeting "CC/PC Packet" bundle;
  the smallest ~0.3 MB ones are thin but still named/filed as the meeting packet).
- `format = na`, `path` blank, `stored_locally = no` because nothing is stored — each row is a
  pointer, not a file. Dead-link rows also carry blank `content_length_bytes`/`size_mb`.

## Coverage & join (see AVAILABILITY.md for the full table)
- **117 packets: Council 69 (2020–2026), PC 48 (2021–2026); 110 live + 7 dead-link.**
- Sparse before 2024 (city publishing ramp), dense 2024+. Both bodies publish whole-meeting
  packets — no council-vs-PC asymmetry in kind.
- **Join key `(date, body [, meeting_type])`** to `../meeting_minutes/all_votes.csv` (body
  Council/RDA) and `../planning_commission/all_votes.csv` (body PlanningCommission → this dataset's
  `PC`). Council packet dates cover 57/66 council vote dates; PC 41/43.
- **7 dead links** are the city's own broken bare-relative links (verified 404); catalogued and
  flagged, never fabricated. Full list in `AVAILABILITY.md`.

## URLs were scraped, never guessed
Revize filename encodings vary wildly (`CC Packet 7-7-2026.pdf`, `2025.04.23 PC Packet.pdf`,
`PC Packet  10122022.pdf`, `Final CC Packet 11-15-2022.pdf`) and the folder alternates
`.../<year>/Packets/`, `.../<year>/Packet/` (2024 PC), or directly `.../<year>/` (early-2026 PC).
Every path was harvested from the two landing pages and **URL-encoded** (spaces `%20`, literal
`&` `%26`) — an un-encoded path returns curl code 000. The optional `?t=<token>` cache-buster is
dropped. Bare-relative links (the `<base href>` quirk) were resolved by trying the canonical
Document Center candidates; the 7 that 404 everywhere are logged as dead.

## Regenerate / refresh
```
python3 build_packets_index_midvale.py   # harvest links from raw/*.html -> _harvest.json
python3 probe_sizes_midvale.py           # HEAD Content-Length each URL   -> _probed.json
python3 write_index_midvale.py           # emit index.csv
```
Re-fetch the two landing pages first with `polite_fetch.py` if refreshing (council recorder
agendas-&-minutes page; PC planning-&-zoning-commission page). See `AVAILABILITY.md` for exactly
what was checked.

## Primary-document classes
Assessed 2026-07-16 (doc_class rollout) — **not separable / honest no** (117 index-only packets
are image/map-heavy, vision/OCR-only; 7 dead links already recorded). Not fetched. See
`AVAILABILITY.md` § "Primary-document classes (doc_class rollout, 2026-07-16)".
