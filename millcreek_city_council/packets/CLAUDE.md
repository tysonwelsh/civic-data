# packets/ — agenda packets & staff reports (INDEX-ONLY / join layer) — as-of 2026-07-06

Built by `expand-city-sources` (Source 1). The staff analysis (fiscal notes, zoning analysis,
alternatives, recommendation) behind each Millcreek **City Council**, **CRA**, and **Planning
Commission** agenda item — the "why" behind a motion in `../meeting_minutes/all_votes.csv` /
`../planning_commission/all_votes.csv`.

## This is a LINK + JOIN INDEX, not a second document store — by deliberate design
Millcreek's AgendaCenter posts the combined **Agenda + Packet** PDF (4–8 MB, up to ~35 MB) at the
`ViewFile/Minutes/_<MMDDYYYY>-<docId>` path (CivicPlus shares one `docId` across the Agenda and
Minutes "views"; the bare `ViewFile/Agenda/_…` path is only a ~35 KB agenda outline). **Those exact
combined PDFs are already retained** in `../meeting_minutes/raw/` (979 MB) and
`../planning_commission/raw/` (499 MB) — they are the source of the minutes text. Re-downloading
would duplicate ~1.2 GB, so this dataset does not re-store them: each `full_packet` row carries a
`path` pointing at the sibling raw file already on disk (`stored_locally=yes`, 335 of
340). The retention rule is satisfied because the raw bytes ARE in the repo. See `AVAILABILITY.md`
for the full rationale + the documented exception for the thin agendas.

## Enumeration (regenerable)
`POST https://www.millcreekut.gov/AgendaCenter/UpdateCategoryList` with form
`{year: <YYYY>, catID: <c>}`, browser UA + `Referer: …/AgendaCenter`, `X-Requested-With:
XMLHttpRequest`. **catID 3 = City Council, 7 = CRA, 2 = Planning Commission.** Walk years
2016→2026; per year the response HTML lists every meeting row. Parse each row's primary agenda
anchor `<a id="<MMDDYYYY>-<docId>" … href="…/ViewFile/Agenda/_…">TITLE (PDF)</a>` and classify by
TITLE:
- **`full_packet`** — title contains "Agenda and Packet" (the combined staff packet). `source_url`
  = the `ViewFile/Minutes/_…` path (that is where the combined PDF is served).
- **`agenda_packet`** — any other agenda title ("… Agenda", "Special Meeting Agenda", "Notice and
  Agenda"). Thin; `source_url` = the bare `ViewFile/Agenda/_…` path.
- Pure "… Notice" and "… Cancellation" rows are **excluded** (not packets; counts in
  `AVAILABILITY.md`).
Sizes came from `HEAD` (Content-Length) on the 2026-07-06 probe; `full_packet` sizes were read
from the retained sibling raw files. Provenance for all 834 discovered docs (incl. excluded
notices/cancellations): `raw/_fetch_log.jsonl`.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format(=na),
extraction_method(=not_extracted…), path, docid, content_length_bytes, size_mb, stored_locally,
note`
- **Join key:** `date` + `body` (+ `meeting_type` for same-day Work/Regular/Special) → the sibling
  `all_votes.csv`. `body` ∈ `Council` / `CRA` / `PlanningCommission` (matches the vote tables'
  bodies; PC votes live in `../planning_commission/`).
- `meeting_type` ∈ `regular` / `work` / `special` / `hearing` (derived from the title).
- `format=na` (this layer performs no extraction; the combined PDFs are OCR-grade — see the city
  `CLAUDE.md` OCR caveat — and read via the sibling minutes datasets or on-demand OCR/vision).
- `path` — relative to the city dir, points into `meeting_minutes/raw/` or
  `planning_commission/raw/` for stored full packets (empty when `stored_locally=no`). It is **not**
  named `path` on purpose (the validator's `path`-existence check assumes dataset-local paths;
  these point at a sibling dataset).

## PC packets carry the IN-PACKETS resident-comment corpus — flagged, not extracted
Planning Commission `full_packet` rows bundle verbatim resident-comment letters (Provo pattern) —
the same corpus `../public_comments/AVAILABILITY.md` marks as a *pending* page-walk harvest. This
index **flags where they live; it does not extract them.** Do not read this dataset as delivering
the comment corpus.

## Coverage (see AVAILABILITY.md for the tables)
340 `full_packet` (Council 186 / CRA 54 / PC 100, 2018–2026) + 212 thin `agenda_packet`. Every
distinct vote date has ≥1 agenda document; the full-packet gap is the pre-2018 agenda-only era.
5 "Agenda and Packet"-titled items had no combined PDF posted → `unrecovered.csv`.

## Regenerate / refresh
Re-run the `UpdateCategoryList` walk (catIDs 3/7/2, years to current) and rebuild `index.csv` with
the same columns + classification. New full packets arrive with the meeting_minutes / PC harvest
(`../fetch_new.py --fetch`), so keep `path` in sync with the sibling raw dirs.

## Primary-document classes
Assessed 2026-07-16 (doc_class rollout) — **not separable** for this portal (the stored
"packets" are minutes-grade OCR via the sibling minutes raw; low net-new text beyond minutes
FTS). The PC-packet resident-comment letters stay a separate pending `public_comments` harvest.
See `AVAILABILITY.md` § "Primary-document classes (doc_class rollout, 2026-07-16)".
