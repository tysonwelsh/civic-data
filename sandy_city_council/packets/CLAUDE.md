# packets/ — Sandy City agenda packets & staff reports (Legistar API)

Additive dataset: meeting **agenda PDFs** (stored) + a full catalog of **matter attachments**
(staff reports, budget presentations, plats, maps, correspondence, exhibits — index-only) +
**extracted TEXT of the four primary-document classes** (2026-07-16 pilot, see below).
Built from the Granicus **Legistar Web API**, not HTML scraping. Read `AVAILABILITY.md` for the
coverage table, counts, and the store-vs-index size math. **As-of 2026-07-16.**

## Layout
```
packets/
  index.csv          6,908 rows: 462 agenda rows (stored) + 6,446 attachment rows (index-only)
  raw/
    <date>_<body>/   one dir per meeting, e.g. raw/2024-04-23_council/
      <NNNN>_A_..._Meeting_Agenda.pdf   the stored EventAgendaFile (born-digital text)
    _fetch_log.jsonl provenance: one JSONL line per polite_fetch attempt (url,status,bytes,sha256,...)
  text/
    <NNNN>_..._Agenda.txt   extracted agenda text (1 per stored agenda)
    attachments/            extracted TEXT of classified attachments (767 files, 2026-07-16)
    _fetch_log.jsonl        provenance of the attachment fetch→extract→discard run
  classify_attachments.py   deterministic doc_class classifier (rerunnable; see below)
  fetch_extract_text.py     fetch → pdftotext/textutil → sha256 → DISCARD-binary pipeline
  AVAILABILITY.md    what was checked, coverage, gaps, storage decision
  CLAUDE.md          this file
```
`<body>` ∈ `council` (138) | `planning_commission` (140) | `board_of_adjustment` (139).
Matter attachment BINARIES are **not** on disk — fetch them live from the `source_url` in
index.csv; classified attachments have their extracted text under `text/attachments/`.

## index.csv columns
`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format,
extraction_method, path, matter_id, size_mb, stored_locally` + the 2026-07-16 pilot
extension columns `doc_class, fetch_status, sha256, text_path, text_chars`
- `packet_kind` ∈ `agenda` (the meeting agenda PDF) | `staff_report_or_exhibit` (a matter attachment).
- `format`: `text` for stored agenda PDFs (born-digital text layer); `na` for index-only attachments.
- `stored_locally`: `yes` (agenda, on disk at `path`) | `no` (attachment — describes the BINARY;
  attachment text may still exist at `text_path`).
- `path`: dataset-relative INCLUDING `raw/` (e.g. `raw/2024-04-23_council/1877_A_..._Agenda.pdf`).
- `matter_id`: Legistar MatterId — rejoin an attachment to its matter / other meetings via the API.
- `size_mb`: measured via HEAD Content-Length (blank = host returned no length).
- `meeting_type`: best-effort from `EventComment` (regular/work_session/special/cancelled) — see caveat below.
- `doc_class` (attachments only): `staff_report` | `member_memo` | `plan_amendment` |
  `development_agreement` | blank = **honestly unclassified** (out of pilot scope, never
  force-bucketed). Assigned by `classify_attachments.py`.
- `fetch_status` (classified rows only): `ok` (text extracted) | `needs_ocr` (fetched, no
  usable text layer — honest OCR floor, no text file written) | `404` (dead URL — dated
  honest gap, see `text/_fetch_log.jsonl`) | blank (not attempted / not classified).
- `sha256`: hash of the fetched binary (provenance — the binary itself is DISCARDED by design).
- `text_path` / `text_chars`: extracted-text sidecar (dataset-relative) and its size.

## Primary-document text layer (PRIMARY_DOCS_PILOT, 2026-07-16)

The 6,446 attachments were classified into four content-bearing classes and those classes'
text extracted (fetch → extract → discard binary; ~25 MB of text vs a ~2.3 GB binary
counterfactual for the classified set, ~14.9 GB for the full corpus):

| doc_class | rows | ok | needs_ocr | 404 | what it is |
|---|---|---|---|---|---|
| staff_report | 739 | 721 | 0 | 18 | land-use staff reports (rezone/CUP/subdivision/plat/annexation/site-plan/GPA/Title-21 code amendments; incl. "PC Report" variants) |
| member_memo | 131 | 123 | 0 | 8 | council-member proposal memos + amendment/redline text (the Sharkey class) |
| plan_amendment | 19 | 19 | 0 | 0 | GP / land-use-map amendment exhibits (proposed elements, Exhibit A plans) |
| development_agreement | 0 | — | — | — | **EMPTY for Sandy 2020–26** — no DA/MDA instruments ride the packet corpus (verified; only 2 briefing/discussion items mention DAs) |

- **needs_ocr → 0 (vision pass, 2026-07-17)**: the 96 classified scanned-packet rows that
  had no text layer (93 staff_report + 3 member_memo, the 2020–22 scanned era) were
  transcribed via **Read-tool Claude Vision at 150 dpi** over **sha256-verified re-fetches**
  (96 docs / 980 pages), flipped to `fetch_status='ok'` with `extraction_method='claude_vision'`
  and a `text_path`/`text_chars`. So `ok` now folds two channels — 628+93 staff_report and
  120+3 member_memo (query `extraction_method` to separate). Imagery pages (plats, photometric
  plans, aerials, site photos) carry honest inline `[map/plat … — no text]` markers with any
  legible title-block/table text captured; source typos are preserved verbatim (never
  normalized). Provenance in `text/attachments/` sidecars + `text/_fetch_log.jsonl`.

- **Classifier**: `classify_attachments.py` — deterministic title-token rules + the
  `matter_id` → `db/sandy.db legistar_matter` (matter_type/title) join for land-use scoping.
  Quality gates (2026-07-16, random samples ground-truthed against live PDFs): precision
  staff_report 100% (n=50), member_memo 98% (n=52), plan_amendment 100% (n=15 of 19 + 4
  oversize desk-verified); recall — 0 misses in a 100-row unclassified sample after token
  iteration, plus exhaustive sweeps of all unclassified 'report'/'agreement' titles.
- **Boundary decisions (documented, not bugs)**: staff-authored memos NOT titled "staff
  report" (e.g. "Commercial Parking Memo") are out of `staff_report`; presentations,
  vicinity maps, notices, PC minutes, signed ordinances/resolutions are excluded from
  `plan_amendment` (ordinances live in `ordinances/`); RDA participation/interlocal
  agreements are NOT development agreements.
- **needs_ocr is now 0 among classified rows** (was 96, concentrated in the 2020–22
  scanned-packet era — the "Staff report, map and documents" scans). Those were resolved by
  the 2026-07-17 Claude Vision pass (see the table note above): fetched+hashed, then
  transcribed at 150 dpi and written to `text/attachments/` sidecars. A future scanned batch
  would land here as `needs_ocr` (fetched+hashed, no text file) until a vision pass clears it.
- **26 dead attachment URLs (404)** as of 2026-07-16 — Legistar link rot; dated in
  `text/_fetch_log.jsonl`.
- Reruns are idempotent: `python3 classify_attachments.py` (rewrites doc_class only);
  `python3 fetch_extract_text.py` (processes only classified rows with blank fetch_status).

## Build method (how to regenerate)
All via the Legistar Web API base `https://webapi.legistar.com/v1/sandyutah/` (browser UA):
1. **Events** per body: `GET /events?$filter=EventBodyId eq {138|139|140|173} and EventDate ge
   datetime'2020-01-01' and EventDate le datetime'2026-12-31'&$orderby=EventDate`
   → `EventId`, `EventDate`, `EventAgendaFile` (the agenda PDF URL), `EventComment`.
2. **Event items** per event: `GET /events/{EventId}/eventitems?AgendaNote=1&MinutesNote=1`
   → each item's `EventItemMatterId`.
3. **Matter attachments** per matter: `GET /matters/{MatterId}/attachments`
   → `MatterAttachmentName` + `MatterAttachmentHyperlink` (the file URL).
4. **Download** the agenda PDFs with `scripts/polite_fetch.py` (GET-only, ≥1 s/host, logs to
   `raw/_fetch_log.jsonl`). Attachments are HEAD-probed for size only, then indexed (not downloaded).
Files live on `sandyutah.legistar1.com/sandyutah/{meetings,attachments}/...`; attachment URLs are
opaque `attachments/<guid>.pdf`, so `index.csv` carries the human `MatterAttachmentName` as `title`.

## Storage decision (why attachments are index-only)
Agenda PDFs total 61.9 MB (462 files, median ~130 KB) → **stored**. Matter attachments total
**~14.9 GB**; even the ≤4 MB subset is **4.08 GB**, 10× the ~400 MB dataset ceiling → **index-only**.
No silent cap: all 6,446 attachments are catalogued with live URLs + measured sizes. See AVAILABILITY.md.

## Linkage to the rest of the repo
- **By meeting date → votes/minutes:** `index.csv.date` joins `meeting_minutes/all_votes.csv.date`
  and `meeting_minutes/minutes_index.csv.date` on the council Tuesday (and PC/BoA meeting dates).
  `body="City Council"` ↔ council votes; `body="Planning Commission"` ↔
  `planning_commission/all_votes.csv`.
- **By matter → db:** `matter_id` is the Legistar MatterId; Sandy's `db/sandy.db` retains the full
  Legistar harvest in `legistar_*` extension tables — `matter_id` is the join to the packet/staff
  report behind a vote or referral.
- This dataset never regenerates or edits `meeting_minutes/`, `planning_commission/`, `db/`, or
  `weeks/`; it is read-only relative to them.

## Caveats
- **`meeting_type` is best-effort** (from `EventComment`; Legistar does not structurally tag work
  sessions — some are labeled `regular`). Not authoritative.
- **Attachments keyed to earliest referencing meeting** — a recurring matter (e.g. two readings)
  is indexed once, under its first appearance; use `matter_id` to find its other events.
- **339 attachments lack `size_mb`** (no Content-Length on HEAD) — indexed anyway.
- **Community Development (173)** body has zero events 2020–26 (honest empty); **Board of
  Adjustment** convened only 9 times. Both are real, not gaps.
