# Agenda packets / staff reports — availability (Ogden City)

**Source type 1** of the `expand-city-sources` skill. Additive dataset; does **not** modify any
existing Ogden dataset. **As-of / retrieved: 2026-07-05.** Window: **2020–2026.**

## Portal

- **Vendor:** CivicPlus **CivicEngage** — the **AgendaCenter**. Canonical host
  `https://www.ogdencity.gov/AgendaCenter` (aliases `ut-ogden.civicplus.com` and
  `brand.ogdencity.com` serve byte-identical HTML; `www.ogdencity.com` 301-redirects to `.gov`).
  Minutes live on a **separate DocumentCenter** and are already in `meeting_minutes/` — this
  dataset EXCLUDES them.
- **Enumeration:** the AgendaCenter default landing shows only the current year. Past years were
  swept with the **GET Search endpoint**
  `/AgendaCenter/Search/?term=&CIDs=all&startDate=01/01/<YYYY>&endDate=12/31/<YYYY>` (one call per
  year 2020–2026 — it correctly filters to that year). The returned HTML groups meetings into
  category panels (`id="cat<N>"` / `category-panel-<N>`); each meeting row carries a download link
  `/AgendaCenter/ViewFile/Agenda/_<MMDDYYYY>-<viewid>`. Every ViewFile link appears **twice** in the
  markup (once in the row, once in the Download dropdown) — dedupe on `(MMDDYYYY, viewid)`.

## THE KEY FINDING — Ogden's AgendaCenter has no "packet" document type

The task-expected `/AgendaCenter/ViewFile/AgendaPacket/…` bundle **does not exist for Ogden.**
Across **all 7 years (2020–2026) and all 20 published categories**, there are **zero** `AgendaPacket`
links and **zero** occurrences of the word "Packet" anywhere in the AgendaCenter markup. The only
agenda-side document Ogden posts is the **thin Agenda outline** (`ViewFile/Agenda/…`). There are
**no separate staff reports, fiscal notes, or exhibit attachments on this portal** — the agendas do
not hyperlink attachments (they name them inline, e.g. "(Attachment A)", but the attachments are not
published). Every row in `index.csv` therefore carries `packet_kind=thin_agenda`.

The thin agenda is still substantive land-use content: the PC agenda lists each item with address,
application type (Conditional Use Permit, site plan, rezone), the applicant, and a
**"Recommendation to:"** column (`Final Action` / `City Council` / `Mayor`) — i.e. the PC's
recommendation-vs-final-action routing, per item, before the vote.

## Council-vs-PC asymmetry (the opposite of Lehi — read before analyzing)

**Ogden City Council publishes essentially no agendas on the AgendaCenter.** Only **4** City Council
items exist for the entire 2020–2026 window: three genuine "Agenda and Information" documents in 2020
(2020-01-28, 2020-06-02, 2020-09-15) and one 2024 Annual Meeting Notice. Council agendas are evidently
served through a different channel (not this portal); the council **minutes** already come from the
DocumentCenter (`meeting_minutes/`), and council **votes** are extracted from those minutes.

**Planning Commission is the rich body here:** **162 agenda files across 141 meeting dates**,
2020–2026, effectively continuous. So this dataset is **PC-dominant** — do not read "few Council
rows" as few Council meetings; it is a portal-publishing choice, not a scraper miss.

| Body | Agenda files | Unique dates | Years present |
|---|---|---|---|
| Planning Commission | 162 | 141 | 2020–2026 (20–31/yr) |
| City Council | 4 | 4 | 2020 (3), 2024 (1) |

(Some PC dates carry 2 files — a work-session/field-trip agenda plus the regular agenda, or an
amended repost; both retained, filenames disambiguated by view-id.)

## RDA / MBA — absent from this portal

Ogden's Council also sits as the **Redevelopment Agency (RDA)** and **Municipal Building Authority
(MBA)** (separate minutes in `meeting_minutes/`, `body ∈ {RDA,MBA}`). **Neither has an AgendaCenter
category**, so no RDA/MBA agendas were retrievable here. (The "Ogden Housing Authority" category is a
different body, not the RDA; it is out of scope and was not downloaded.)

## What was retrieved / storage decision

- **166 agenda PDFs · 19.04 MB total**, stored locally under `packets/raw/<body>/`.
- **Formats:** 164 `text` (born-digital, have an embedded font layer — classified with `pdffonts`),
  **2 `scanned`** (raster, no font layer → would need OCR: `2026-01-01` PC Annual Meeting Notice and
  `2026-05-20` PC Meeting).
- **Storage mode = STORE LOCALLY, not index-only.** The disk-lesson expectation of multi-hundred-page
  bundles did not materialize *because Ogden posts no packet bundles* — the thin agendas are 60–180 KB
  each (1–2 pages). Size math: 166 files × ~115 KB ≈ **19 MB**, far under the ~400 MB index-only
  threshold, so all raw originals are retained on disk. Per-file provenance (URL, HTTP status, bytes,
  **sha256**, retrieved_utc) is in `raw/<body>/_fetch_log.jsonl` (166 lines; 166 ok / 0 fail).

## Other bodies available but OUT OF SCOPE (enumerated, not downloaded)

The same AgendaCenter also publishes thin agendas for land-use-adjacent bodies not in this dataset's
scope (Council + PC). Counts (unique meetings, 2020–2026), recorded for a future expansion run:
**Board of Zoning Adjustment 61**, **Ogden Landmarks Commission 78**, Sustainability Committee 74,
Ogden City Arts 78, plus ~10 other advisory committees. Re-run the enumeration above with the
relevant `catN` to add them.

## Genuine gaps (not sampling)

None to record: every enumerated Council + PC agenda downloaded successfully (0 failures), and there
was **no** capping/dropping (everything fit on disk). The honest gaps are structural and described
above: (a) Council agendas are absent from this portal, (b) RDA/MBA have no AgendaCenter category,
(c) no staff-report/attachment layer exists to retrieve.

## Corpus screen

**Text layer (corrected 2026-07-16).** The original build set `extraction_method=none (raw
retained)` and this section claimed "no text corpus was produced." That is now stale: the later
**mandatory-sidecar retrofit** extracted per-document text into `text/` — **164 extracted**
sidecars + `text/_extraction_log.csv` (166 rows), with the **2 scanned files** (2026-01-01 and
2026-05-20 PC) yielding **0 chars** (logged `status=error`, i.e. scanned-zero-char; they still
need OCR). So the real state is **164 extracted / 2 scanned-zero-char**, not "none". History
note: the raw PDFs remain the primary deliverable and are all retained; the index rows still
read `extraction_method=none` from the original build (not rewritten here). Extract lazily with
`pdftotext -layout` for any not covered, and OCR the 2 scanned files first.

## How this was checked / rebuild

Fetched `/AgendaCenter/Search/?…` once per year 2020–2026 (browser UA), parsed category panels with a
regex over the `catN` blocks, deduped Council + PC rows on `(date, view-id)`, then downloaded every
agenda through `.claude/skills/expand-city-sources/scripts/polite_fetch.py` (`save()`: browser UA,
`Referer: https://www.ogdencity.gov/AgendaCenter`, 1.0 s throttle, retry/backoff, one
`_fetch_log.jsonl` line per file). To rebuild: repeat the per-year Search sweep; the portal has no
API, so a markup change to the AgendaCenter category/row structure would require updating the parser.

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket C** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) are **HONEST ZEROS** for all four — Ogden's AgendaCenter
publishes **no** staff reports or packets at all. No fetch, no classification was performed.

This was verified at build (see "THE KEY FINDING" above): across all 7 years (2020–2026) and
all 20 published categories there are **zero** `AgendaPacket` types and zero occurrences of the
word "Packet" — the only agenda-side document Ogden posts is the thin **Agenda** outline. The
**166 stored thin agendas ARE the corpus**, and their value is **agenda-item-level** (per-item
address, application type, and the "Recommendation to:" routing), **not** primary-document
content. Class 3 (General Plan text) is independent — Ogden's MIH element is General Plan
Chapter 7, tracked in `housing_plans/`.
