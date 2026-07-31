# Agenda packets / staff reports — availability

**Source type 1** of the `expand-city-sources` skill. Additive dataset; does **not** modify any
existing Lehi dataset. **As-of: 2026-07-02** (packets scrape); **primary-document text layer added
2026-07-16** (see below).

## Primary-document text layer (Source 7 — PRIMARY_DOCS_ROLLOUT, 2026-07-16)

Classify-in-place: the 452 `staff_report` attachment rows were classified into the
primary-document `doc_class` taxonomy and the SCHEMA_SPEC §9 pilot columns
(`doc_class, fetch_status, sha256, text_path, text_chars`) populated against the born-digital
text sidecars already on disk (`text/`, 553 files added by the mandatory-sidecar retrofit). No new
fetching; raw PDFs RETAINED.

- **Yield**: `staff_report` **272** (all `fetch_status=ok`, text linked). `member_memo` **0**,
  `plan_amendment` **0**, `development_agreement` **0** — all honest empties (Lehi is all
  at-large with no member memos; GP-amendment substance is report+letter+aerial with no separable
  exhibit; readable DA docs are staff reports, instruments are scanned/unverifiable). **11**
  `needs_ocr` (image-only exhibits — aerials, a purchase order, a DRAFT agreement, scanned
  `*_DA_2` exhibits). **169** unclassified-with-text (non-report exhibits: maps, letters, bylaws,
  agenda-list `pz<date>` attachments, resolutions/ordinances, code tables).
- **Gates**: precision staff_report 100% (n=55); recall 0 misses over the full 169-row
  unclassified sweep. Metrics + boundary decisions in `CLAUDE.md`.
- **Window caveat (honest gap)**: this classification covers the **2024–25 pilot window ONLY** —
  the SAME window as the packets scrape. The **2020–2023** packets are the known **deferred**
  acquisition job (available on `lehi.granicus.com` ViewPublisher, not yet retrieved); classifying
  them is a separate future task, not attempted here.

## Portal

- **Vendor:** Granicus **ViewPublisher** (no Legistar API, no PrimeGov JSON). Host
  `lehi.granicus.com`.
- **One combined table for all bodies:** `https://lehi.granicus.com/ViewPublisher.php?view_id=1`
  (City Council, Work Sessions, Planning Commission, PC Work Sessions, RDA, Local Building
  Authority, budget/joint sessions). Each row carries a `clip_id`; rows were classified to a body
  by the meeting-name string.
- **How a packet is assembled (Lehi-specific — see `CLAUDE.md` for the mechanics):** the "Agenda"
  link (`AgendaViewer.php?clip_id=<id>`) 302-redirects to the **agenda PDF** (an outline listing
  every item with petitioner, resolution/ordinance numbers, and the filenames of its
  attachments). The agenda PDF **embeds hyperlinks** to each item's **staff report / exhibit**
  (Legistar attachment URLs). Those linked attachments are the actual staff analysis. There is no
  single combined "packet" document for Lehi — the packet = agenda PDF + its linked attachments.

## Window covered

**Pilot window: 2024–2025 only** (City Council + Planning Commission, including their Work
Sessions). Earlier years (**2020–2023 are available on the same portal and are deferred**, not
absent) and 2026 are out of scope for this pilot. RDA and Local Building Authority bodies were
**not** retrieved (out of scope for this source run).

Coverage retrieved (unique meetings with an agenda): **112**
| Year | City Council | Planning Commission |
|---|---|---|
| 2024 | 32 | 30 |
| 2025 | 24 | 26 |

## What was retrieved

- **112 agenda PDFs** (one per meeting) — 56 Council + 56 PC. All born-digital text.
- **452 staff-report / exhibit attachments** linked from those agendas — 74 Council + 378 PC.
- **564 files total, 340.9 MB.** Formats: **555 text** (born-digital, have an embedded font
  layer), **9 scanned** (raster image PDFs with no font layer — would need OCR; listed in
  `index.csv` with `format=scanned`).
- Per-file provenance (URL, HTTP status, bytes, **sha256**, retrieved_utc) is in
  `raw/<date>/_fetch_log.jsonl`.

## Asymmetry to know before analyzing (important)

Staff reports are hyperlinked from the agenda PDF **only for meetings whose agenda was published
through Granicus's Legistar-linked pipeline.** In 2024–2025 that pipeline was standard for
**Planning Commission** but only intermittent for **City Council**:

- **Planning Commission — 45 of 56 meetings** have ≥1 linked staff report (378 attachments). PC
  packets are effectively complete.
- **City Council — only 5 of 56 meetings** have linked staff reports (74 attachments). The other
  **51 council agendas name their attachments in text** (e.g. "Res 2025-27.docx", petitioner,
  resolution number) **but do not hyperlink them**, so the individual council staff reports are
  **not retrievable through the portal** for those meetings. This is a portal-publishing gap, not
  a scraper limitation (verified: those agenda PDFs contain zero embedded attachment URLs). Lehi
  moved council agendas onto the Legistar-linked pipeline at the **2025→2026 boundary**, so 2026
  council packets (out of this pilot's window) would carry full staff reports.

The council **agenda outline itself is still high value** (every item, petitioner,
resolution/ordinance number, and the attachment filenames) and is retained for all 56 council
meetings.

## What was intentionally dropped (sampling — logged, recoverable)

Full raw volume for 2024–2025 attachments was **~3.3 GB**. To keep the pilot tractable, a
**per-file size cap of 4 MB** was applied to staff-report attachments (agendas were never capped).
Files over 4 MB are **large graphical exhibits** (subdivision plats, engineering/traffic studies,
full draft plan documents) — not narrative staff analysis.

- **163 attachments dropped (≈3.05 GB): 161 PC + 2 Council.** Every dropped file is logged with
  its date, body, filename, **source URL, and byte size** in **`dropped_oversize.csv`** — re-fetch
  any of them by URL to lift the cap later.

## Genuine gaps (not sampling)

Recorded in `unrecovered.csv`:
- **2024-07-23 City Council Regular Meeting** — no agenda was posted on the portal (AgendaViewer
  returns an empty redirect). True missing item.
- **2024-12-12 Planning Commission** — a duplicate ViewPublisher row with no `clip_id`; the
  meeting itself **is** covered under `clip_id 742` (not a content gap; logged for transparency).

## How this was checked

Fetched `ViewPublisher.php?view_id=1` (838 KB HTML), parsed the combined table with
BeautifulSoup, classified all 590 rows by body, filtered to 2024–2025 Council + PC, resolved each
agenda redirect, extracted embedded attachment URLs from each agenda PDF, HEAD-sized all 610
unique attachments, then downloaded agendas + all attachments ≤4 MB through the bundled polite
fetcher. See `CLAUDE.md` for exact method.
