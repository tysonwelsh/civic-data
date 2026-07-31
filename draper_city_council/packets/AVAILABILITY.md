# packets/ — availability, size math, and mode decision

**As-of: 2026-07-13.** Window checked: **2020-01-01 → 2026-07-13** (the repo's Draper floor
to the build date). Portal: `https://draper.granicus.com/ViewPublisher.php?view_id=1` (all
bodies in one table; enumerated in full — 1,437 listing rows, 340 in-scope past meetings
across Council / Planning Commission / RDA / MBA / CRA).

## What exists (and where it came from)

Draper publishes packet material through **three vendor eras** (detail in `CLAUDE.md`):

1. **NovusAgenda era (2020-04 → 2023-08):** no bundled packet. The agenda resolves to a
   NovusAgenda MeetingView page; each substantive item has a CoverSheet (HTML staff memo,
   often thin) with PDF attachments (staff reports, resolutions, exhibits).
2. **DocumentViewer era (Jan–Mar 2020 + most RDA/MBA/CRA meetings):** a Novus-generated
   agenda PDF whose broken `file:///` URIs still leak the Novus item ids — same per-item
   flow as era 1. (This is why RDA/MBA/CRA packets were recoverable at all.)
3. **Granicus/Legistar era (2023-09 → present):** an agenda-outline PDF embedding links to
   per-item **staff memos** (~60 KB born-digital text: analysis, findings for approval AND
   denial, PC-recommendation language), each linking its **exhibits** on Legistar S3.
   ALSO a bundled whole-meeting **"Agenda Packet"** PDF per meeting (8–36 MB).

## Retrieved (2026-07-13)

**index.csv: 4,721 rows** — 4,207 stored on disk (**1.62 GB** under `raw/`), 514 index-only.

| packet_kind | stored | index-only | note |
|---|---|---|---|
| agenda | 339 | 0 | 190 text PDF, 149 HTML (Novus MeetingView) |
| staff_report | 1,821 | 0 | 785 text PDF memos + 1,032 HTML coversheets + 4 scanned |
| exhibit | 2,047 | 380 | stored: 1,897 text + 150 scanned; index-only: 373 oversize + 7 dead links |
| full_packet | 0 | 134 | bundled PDFs, HEAD-sized, **index-only by design** |

Per body: Council 2,939 rows / PlanningCommission 1,594 / CRA 103 / RDA 54 / MBA 31.
Coverage window of rows: **2020-01-09 → 2026-07-09**. Every in-scope year × body has
content; Council 145/153 and PC 145/147 meetings have stored staff content (the remainder
have an agenda but no linked items — typically retreats, canvass, or training-only
agendas). Meeting-date joins: **148/152 Council packet dates match a `meeting_minutes`
date exactly; 141/146 PC dates match** (packets exist for a few work/special meetings that
have no adopted minutes, and vice versa — publication asymmetry, not a scraper miss).

**Text sidecars: 3,591** under `text/` (2,698 `pdftotext -layout` + 893 HTML tag-strip);
**324 stored PDFs are image-only** (scanned plats/letters — no sidecar, logged honestly in
`text/_extraction_log.csv`; OCR/vision is the documented path). Corpus screened with
`screen_corpus.py`: 0 CID/PUA/mojibake artifacts; 22 files carry source-side replacement
chars; 1 exhibit (`2024-12-12 …Radnet_EXTENSION_REQUEST`) has a broken embedded font
encoding at source (Caesar-shifted glyphs) — kept verbatim, do not "fix" it.

## Primary-document text layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

Classify-in-place over the 4,248 attachment rows (nothing re-fetched — sidecars already on
disk). **922 rows classified**: `staff_report` 895, `plan_amendment` 18,
`development_agreement` 9, `member_memo` 0 (honest empty). Splits by fetch_status:

| doc_class | ok (text) | needs_ocr | index-only |
|---|---|---|---|
| staff_report | 893 | 2 | 0 |
| plan_amendment | 18 | 0 | 0 |
| development_agreement | 9 | 0 | 0 |
| **total** | **920** | **2** | **0** |

- **Index-only follow-up wave (2026-07-17):** the 243 classified rows that were index-only
  after the 2026-07-16 rollout (all oversize >4 MB exhibits the build's 4 MB cap had dropped;
  all present in `dropped_oversize.csv`) were fetched politely (~1 req/s), text-extracted, and
  their binaries DISCARDED under the SCHEMA_SPEC §9 discard-binary exception. **2.74 GB fetched
  → 204 MB text stored** — retaining the binaries would ~triple exhibit disk for content already
  duplicated inside each meeting's era-C `full_packet` URL. Outcome: **241 ok** new `text/`
  sidecars + **2 needs_ocr**; **0 404, 0 auth-wall** (every classified oversize URL still live).
  The discard rows keep `stored=no`, `path` blank, `bytes` = fetched size, `sha256` of the
  fetched binary, and a `text/` sidecar (`format=text`; `needs_ocr` rows `format=scanned`,
  `text_path` blank). 10 sidecars sample-verified against re-fetched PDFs (sha256 + byte-
  identical text). **No classified row is index-only any longer.**
- **2 `needs_ocr` staff reports**: an 18-page image-only PDF re-published on 2022-08-16 &
  2022-10-04 Council (same sha256) — an honest OCR floor. The binary was discarded (18.6 MB;
  disproportionate), sha256 + `source_url` retained; queued with the repo-wide vision pass.
- Classifier + gate metrics + boundary decisions: see `CLAUDE.md` → "Primary-document text
  layer". Gates PASS (staff_report precision 50/50 random + 0 false-pos in the full 75-row
  heuristic channel, recall 0/100 miss; plan_amendment 18/18; development_agreement 9/9).
- The 1,032 `novus_coversheet` thin era-A/B HTML coversheets are **excluded by design**
  (boilerplate; the analysis rides the attached exhibit, which is classified).

## Size math and the mode decision

- **Bundled full packets (era 3): 134 files, 2.96 GB total (avg ~22 MB).** They duplicate
  the memos + exhibits already fetched item-by-item, so storing them would nearly triple
  disk for no new text → **INDEX-ONLY** (`stored=no`, `format=na`, live `source_url`,
  `bytes` = HEAD Content-Length). This is the documented exception to "retain every raw
  original" (public, re-fetchable; `raw/*/_fetch_log.jsonl` retains provenance).
- **Per-item attachments: 4 MB cap** (skill default). **373 oversize attachments (1.97 GB
  known sizes) were NOT downloaded** — each is in `dropped_oversize.csv` with a live URL.
  These skew to PC staff reports with embedded maps/plats (5–23 MB) and "all public
  comment" compilations; for era-3 meetings the same content is inside the meeting's
  `full_packet` URL. Raising the cap and re-fetching from `dropped_oversize.csv` is the
  documented recovery path.
- Stored total landed at **1.62 GB** (vs the ~1.5 GB planning budget — accepted overage
  ~8%, dominated by era-3 exhibits ≤4 MB).

## Gaps (honest, verified)

- **2024-07-16 CRA:** the portal row has **no Agenda and no Agenda Packet link** at all →
  `unrecovered.csv`. Sole such meeting in scope.
- **7 era-3 exhibit links are dead at source** (Legistar S3 404 — e.g. two 2025-06-17
  resolutions, a 2023-12-06 election summary): index rows kept with `stored=no`,
  `format=na`. The memos citing them are stored; era-3 `full_packet` URLs contain them.
- **CRA 2024 (3 meetings) & MBA 2024 (1 meeting):** agendas stored but no per-item
  attachments were linked by the city — publishing gap, not a scrape miss.
- **RDA has no meetings after 2021, MBA none after 2024** on the portal — the bodies
  simply stopped meeting/posting; not a gap.
- **Recap-only newest meetings** are a minutes-layer issue, not packets; agendas/memos for
  2026 meetings through 2026-07-09 are present.
- **Out of scope, exists on the same portal:** Historic Preservation Commission (24
  bundled packets), Tree Committee (9), Special Event Arena Committee (6), and other minor
  bodies also carry Agenda Packet links — not cataloged here (Council/PC/RDA/MBA/CRA only).

## Sampling / verification

- All three eras ground-truthed before the bulk run (2025-01-07 Council, 2022-06-23 PC,
  2020-04-07 RDA) — memo/exhibit chains and Novus item/attachment chains verified against
  the live portal, including a contested-item memo citing the PC's 4-1 recommendation.
- 340/340 in-scope meetings processed, 0 crawl errors; every fetch logged in the date
  folder's `_fetch_log.jsonl` (url, status, bytes, sha256, retrieved_utc).
