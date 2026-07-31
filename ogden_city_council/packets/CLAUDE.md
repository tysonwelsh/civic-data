# packets/ — agenda documents (Ogden City) — build & linkage

Additive dataset built by `expand-city-sources` (Source 1), as-of **2026-07-05**. The agenda
outlines behind Ogden **Planning Commission** and **City Council** meetings, keyed by meeting date so
they join to the existing minutes/votes. Window **2020–2026**. Does **not** modify any existing
dataset.

> **Read `AVAILABILITY.md` first.** Two structural facts shape everything here:
> 1. **Ogden's AgendaCenter has no packet/staff-report layer** — only the thin **Agenda** PDF exists
>    (`packet_kind=thin_agenda` on every row). No exhibits/attachments are published on the portal.
> 2. **This dataset is Planning-Commission-dominant.** City Council posts almost nothing on the
>    AgendaCenter (4 items total); PC posts richly (162). This is the *reverse* of Lehi's asymmetry.
> 3. **Primary-document classes (doc_class rollout, 2026-07-16):** Bucket **C** — the four
>    packet-attachment classes are **HONEST ZEROS** (no staff-report/packet layer exists); the 166
>    thin agendas ARE the corpus. See `AVAILABILITY.md` § "Primary-document classes". A `text/`
>    sidecar layer (164 extracted / 2 scanned-zero-char) was added by a later retrofit — the
>    "no text corpus" wording is corrected below + in `AVAILABILITY.md` § "Corpus screen".

## Layout

```
packets/
  raw/
    PlanningCommission/<YYYY-MM-DD>_<viewid>.pdf   162 agenda PDFs
    Council/<YYYY-MM-DD>_<viewid>.pdf              4 agenda PDFs
    <body>/_fetch_log.jsonl                        provenance per file (url,status,bytes,sha256,retrieved_utc)
  index.csv                                        one row per agenda PDF
  AVAILABILITY.md                                  portal, the no-packet finding, asymmetry, size math, gaps
  CLAUDE.md                                        this file
```

## index.csv columns

`date, title, body, meeting_type, packet_kind, source_url, retrieved_date, format,
extraction_method, path, size_mb, stored_locally, bytes`

- **date** — meeting date (`YYYY-MM-DD`), the join key.
- **title** — the agenda's own title text as posted on the portal.
- **body** — `Council` or `PlanningCommission`.
- **meeting_type** — heuristic from the title (`Regular` / `WorkSession` / `Annual` / `Special`);
  most PC rows are `Regular`. Advisory only.
- **packet_kind** — always **`thin_agenda`** (Ogden publishes no bundled packet or staff reports; the
  agenda outline is the only artifact — see AVAILABILITY.md).
- **source_url** — the stable `/AgendaCenter/ViewFile/Agenda/_<MMDDYYYY>-<viewid>` link (portal-facing;
  re-fetchable).
- **format** — `text` (born-digital, embedded font layer) or `scanned` (raster, needs OCR — 2 files:
  2026-01-01 & 2026-05-20 PC). Classified with `pdffonts`.
- **extraction_method** — `none (raw retained)` in `index.csv` (original-build value, not
  rewritten). NOTE: a `text/` sidecar layer was added later by the mandatory-sidecar retrofit
  (164 extracted + `_extraction_log.csv`; 2 scanned files 0-char) — see the Caveats note below
  and `AVAILABILITY.md` "Corpus screen". For anything not covered, extract with
  `pdftotext -layout` (OCR the 2 scanned rows first).
- **path** — repo-relative path to the raw file. **size_mb / bytes** — file size on disk.
  **stored_locally** — always `yes` (19 MB total; nothing capped or index-only).

## How to join to minutes / votes

Join on **`date`** (+ `body`):

- **PC agendas ↔ `planning_commission/all_votes.csv` / `minutes_index.csv`** (`body=PlanningCommission`).
  The PC agenda set was a **superset** of the repo's PC vote coverage (141 agenda dates vs 65 PC
  vote-dates when written; 71 agenda dates then had no minutes in the repo). **2026-07-19: the
  2020-2023 PC minutes gap was closed** (63 meetings recovered — see
  `planning_commission/CLAUDE.md`), so nearly every PC agenda date now has minutes. CAVEAT found
  during that recovery: the item labeled "Ogden City Planning Commission Meeting Agenda" for
  **2020-08-26** (`raw/PlanningCommission/2020-08-26_1013.pdf`) is in-body a **Board of Zoning
  Adjustment** agenda — the AgendaCenter category label lies; verify agenda identity in-body
  before treating a PC-labeled date as a PC meeting.
- **Council agendas ↔ `meeting_minutes/all_votes.csv`** (`body=Council`). Only 4 Council agendas
  exist; 2 line up with a council vote-date (2020-01-28, 2020-06-02).
- **db/civic.db** keys motions by date too; a PC agenda's item list (address + application type +
  "Recommendation to:" routing) helps tie an agenda item to a specific motion/application.

Ogden council structure still applies downstream: the **Mayor does not vote**; PC issues
recommendations (to Council/Mayor) vs final actions — the agenda's "Recommendation to:" column names
that routing per item.

## Scrape method (CivicPlus AgendaCenter, Ogden specifics)

1. For each year 2020–2026, GET
   `https://www.ogdencity.gov/AgendaCenter/Search/?term=&CIDs=all&startDate=01/01/<YYYY>&endDate=12/31/<YYYY>`
   (browser UA). The default landing shows only the current year; this Search endpoint returns a full
   year's rows across all categories.
2. Split the HTML on `<div class="listing listingCollapse noHeader" id="cat<N>">`; the panel header
   `category-panel-<N>">…</h2>` gives the body name. Keep **cat9 = City Council**, **cat2 = Planning
   Commission**.
3. In each panel, match `ViewFile/Agenda/_(\d{8})-(\d+)"…>(title)</a>`. **Dedupe on
   `(MMDDYYYY, viewid)`** — every link appears twice (row + Download dropdown).
4. Download each agenda through `polite_fetch.py`'s `save()` (browser UA,
   `Referer: …/AgendaCenter`, 1.0 s throttle, retry/backoff, `_fetch_log.jsonl` per file). No size cap
   was needed (files are 60–180 KB). Classify `format` with `pdffonts` after download.

## Caveats

- **No packet/attachment layer exists** — see AVAILABILITY.md. Do not expect staff reports; the
  agendas name attachments inline ("(Attachment A)") but Ogden does not publish them on the portal.
- **Council near-absence is a portal choice, not a gap in council business** — council agendas are
  served elsewhere; use `meeting_minutes/` for council substance.
- **RDA / MBA agendas are not on the AgendaCenter** (no category) — absent by portal design.
- **A text layer DOES exist (corrected 2026-07-16).** The original build produced no text and
  set `extraction_method=none`; the later **mandatory-sidecar retrofit** then extracted `text/`
  sidecars — **164 extracted + `text/_extraction_log.csv`**, with the 2 scanned files
  (2026-01-01, 2026-05-20) yielding **0 chars** (scanned-zero-char). So the real state is
  **164 extracted / 2 scanned-zero-char**, not "no corpus." (The `index.csv`
  `extraction_method` column still reads `none` from the original build — not rewritten; raw
  PDFs remain retained.) See `AVAILABILITY.md` "Corpus screen".
- **Other land-use bodies (Board of Zoning Adjustment 61, Landmarks Commission 78, …) publish thin
  agendas on the same portal** but are out of this dataset's Council+PC scope — enumerated in
  AVAILABILITY.md for a future expansion (re-run the sweep with their `catN`).
- **Rebuild:** re-run the per-year Search sweep (method above); the portal has no API, so a markup
  change would require updating the category/row parser.
