# packets/ — agenda packets & staff reports (Taylorsville)

Additive dataset built by the `expand-city-sources` skill (source #1). **Does not modify any
existing dataset.** Read `AVAILABILITY.md` first — the headline is a publishing gap.

## One-line verdict
Taylorsville publishes packets on three dedicated **current-cycle-only** pages
(council-packet / planning-commission-packet / rda-board-packet); **no historical packet
archive exists.** For 2020→present, packets/staff reports are effectively unrecoverable
(honest gap). What is on disk is a **dated snapshot of the current (June–July 2026) cycle**.

> **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **C** — the four
> packet-attachment classes (staff reports/memos/DAs/plan amendments) **cannot be built**
> (7-doc current-cycle snapshot only; no historical archive; Wayback recovery logged in TODO).
> Class 3 (GP text) is already complete in `housing_plans/`. See `AVAILABILITY.md`
> § "Primary-document classes".

## Source & method
- **Portal:** CivicPlus / CivicEngage Central, `https://www.taylorsvilleut.gov`. Site is
  behind an Akamai edge that **403s bare bots** — every fetch used `scripts/polite_fetch.py`
  (browser UA), GET-only, throttled. Raw bytes + provenance in `raw/<date>/_fetch_log.jsonl`.
- **Discovery:** the three packet pages are CivicEngage "Document Folder Box" widgets, each
  bound to one document-center folder holding only the current cycle (verified: 1 council /
  2 PC / 4 RDA docs on 2026-07-06). No year-folder (`-folder-<N>`) archive, no pagination.
- **Doc URL pattern:** `/home/showpublisheddocument/<docId>/<versionToken>`.
- **NOT packets:** the Agendas-&-Minutes year folders (2008→2026) hold Agendas | Minutes |
  Audio — the archived *agendas* are thin 1–2 pg outlines (scanned or born-digital), not
  staff-report bundles. Confirmed by size/page probes (see AVAILABILITY.md).

## Files
- `raw/<date>/` — 7 originals verbatim (~11.6 MB) + `_fetch_log.jsonl` per date.
  Note `11987_..._resolution_26-03.docx`: the server delivered a Word `.docx` (not a PDF);
  extension corrected on disk, `_fetch_log.jsonl` records the original download event + sha256.
- `index.csv` — one row per stored document.
- `AVAILABILITY.md` — the gap record (what exists, what doesn't, how verified).
- `unrecovered.csv` — the historical-packet gap, per body, with a Wayback recovery lead.

## index.csv schema
Required minimum (`date,title,source_url,retrieved_date,format,extraction_method`) plus:
- `body` ∈ `Council` / `RDA` / `PlanningCommission` (matches `all_votes.csv` body labels).
- `meeting_type` — disambiguates same-day docs (here all `regular`).
- `packet_kind` ∈ `agenda` / `staff_report` / `resolution` / `cancellation`.
- `path` — dataset-relative, **including `raw/`** (validator requirement).
- `stored_locally` — `yes` for all rows (small snapshot; stored, not index-only).
- `size_mb` — file size on disk.
- `format` ∈ the shared vocab; `text` = born-digital (PDF or DOCX), `scanned` = image PDF.

## Linkage to votes
Join `date` (+ `body`, `meeting_type`) to `meeting_minutes/all_votes.csv` (Council/RDA) and
`planning_commission/all_votes.csv` (PC). In this snapshot only the **2026-06-03** date matches
an existing meeting (a `body=Council` meeting — note `body=RDA` vote rows exist only 2021–2022,
so the 2026 RDA budget vote is not separately extracted); **PC 2026-06-09** post-dates the last
PC vote extraction (2026-04-28) and **Council 2026-07-01** was cancelled. See AVAILABILITY.md
"Join coverage".

## Refresh
No archive to backfill. To keep the snapshot current, re-fetch the three packet pages, harvest
the `showpublisheddocument` links, and store any new-cycle docs under a new `raw/<date>/`.
Because the source is current-cycle-only, periodic capture is the ONLY way to accumulate a
packet history over time (each run adds that cycle; gaps between runs are permanent).

## Validate
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py taylorsville_city_council/packets`
→ PASS.
