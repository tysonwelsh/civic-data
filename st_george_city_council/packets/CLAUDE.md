# packets/ — agenda packets & staff reports (INDEX-ONLY) — as-of 2026-07-02

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning analysis,
alternatives, recommendation) behind each St. George **City Council** and **Planning Commission**
agenda item — the "why" behind a motion in `../meeting_minutes/all_votes.csv` /
`../planning_commission/all_votes.csv`.

## This is a LINK INDEX, not a document store — by deliberate design
> **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **B-no** — the four
> packet-attachment classes (staff reports/memos/DAs/plan amendments) are **not separable** on
> these 224 index-only, image/plat-heavy whole-meeting bundles. See `AVAILABILITY.md`
> § "Primary-document classes".

St. George's Revize CMS bundles each meeting into **one large PDF** (agenda + every staff report +
all exhibits), **10–150 MB each** (median 29 MB; the full 224-packet set = **7.5 GB**). These PDFs
are **image/map/plat-heavy** (site plans, engineering & traffic studies), so they are **not
born-digital text** — converting to markdown is not viable; reading one requires **vision or OCR**.
Per the repo owner's decision (limited disk, low text-conversion value), **we do not store the PDFs
locally**. Instead `index.csv` catalogs all 224 packets with a **live `source_url` and byte size**,
so any specific packet can be fetched on demand.

The retention exception is intentional and scoped to this dataset: the packet PDFs are public and
re-fetchable from `source_url` at any time; `raw/*/_fetch_log.jsonl` retains the provenance
(URL → HTTP status/size/sha256/retrieved_utc) of the 2026-07-02 discovery + the 35 packets that
were briefly fetched during the build. (The normal "retain every raw original" rule still applies
to every *other* dataset in this repo.)

## How an LLM/agent should use this
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type` for same-day Work vs
   Regular). Each row has `source_url`, `size_mb`, and `packet_kind`.
2. To read it, **fetch `source_url`** (public GET; it's a `cms3.revize.com`/`sgcityutah.gov` PDF).
   Check `size_mb` first — some are >100 MB.
3. Extract with **vision or OCR**, not `pdftotext` (image-heavy). Label whatever you produce.
4. To bulk-download (e.g. re-hydrate the dataset): feed the `source_url` column to
   `polite_fetch.py --batch` **without `--max-bytes`** (or a high cap). Budget ~7.5 GB for all 224.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method(=not_retrieved), path, content_length_bytes, size_mb, stored_locally(=no)`
- `packet_kind`: `full_packet` (131 — the real staff-report packet, `/Packets/` or `/Other/`),
  `agenda_packet` (29 — thin agenda-style, `/Agendas/`), `packet` (64 — other/ambiguous folder).
  **Prefer `full_packet` for staff analysis;** thin agendas carry little beyond the item list.
- `format=na` / `stored_locally=no` because nothing is stored; the row is a pointer, not a file.

## Coverage & join
- **224 packets: Council 177 (2022–2025), Planning Commission 47 (2024–2025).** PC packets were not
  posted before 2024 (a city publishing gap, not a scraper miss). 2020–2021 predate Revize packet
  publication. Council packet dates cover **150/163** council vote dates, PC **39/46** (non-matches
  are work/special/canvass meetings with no roll call).
- URLs were **scraped, never guessed** (Revize filename encodings vary wildly: `YYYY.MM.DD`,
  `MM.DD.YYYY`, nested under unrelated folders like `Arts Commission Agendas/City Council/…`).
  Every `source_url` returned HTTP 200 on 2026-07-02 (`raw/_fetch_log.jsonl`).

## Regenerate / refresh
Re-scrape the council + PC "Agendas & Minutes" pages on `sgcityutah.gov` for packet links; rebuild
`index.csv` with the same columns. See `AVAILABILITY.md` for exactly what was checked.
