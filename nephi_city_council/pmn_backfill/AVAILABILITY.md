# PMN backfill — availability record (Nephi City)

**As-of:** 2026-07-05 · **Checked by:** expand-city-sources Source 4 (PMN cross-check)

## Confirmed PMN identifiers (Nephi)

Resolved via the global chain, not guessed:
`/pmn/list/entities.html?id=3&limit=2000` (govType 3 = Municipality) → **Nephi entity id = 216**
→ `/pmn/list/publicBodies.html?id=216&limit=2000` → every Nephi public body:

| Public body | PMN body id | In scope? |
|---|---|---|
| **Nephi City Council** | **1788** | yes (cross-checked) |
| **Nephi City Planning Commission** | **1869** | yes (cross-checked) |
| Nephi City Community Reinvestment Agency (CRA) | 5737 | no — repo has no RDA/CRA body (verified) |
| Nephi City Local Building Authority (LBA) | 6527 | no — out of Source-4 scope |
| Nephi City Public Library | 1868 | no — not a legislative body |

## What was checked

- PMN full notice history for the two in-scope bodies, via the GET cumulative browse
  endpoint `/pmn/list/notices.html?id=<bodyId>&page=300` (`page` is cumulative — one high
  page returns the body's entire history):
  - **City Council — body 1788** — 1,242 notices parsed, **89** carrying a `(Meeting Minutes)` attachment.
  - **Planning Commission — body 1869** — 270 notices parsed, **22** minutes attachments (20 minutes-bearing notices).
- Each notice's attachments were parsed for the `(Meeting Minutes)` type label; every
  minutes-bearing meeting date (2020+) was set-differenced against the repo's audited
  minutes indexes (`meeting_minutes/minutes_index.csv`, `planning_commission/minutes_index.csv`),
  tolerance ±4 days. Then the **meeting date printed inside each candidate PDF** was read to
  confirm the true date (notice date ≠ minutes date — see below).

## What was recovered

- **9 born-digital minutes PDFs** dated in the repo's 2020–2026 scope existed on PMN but not
  in the repo (8 City Council, 1 Planning Commission). **All 9 downloaded** (`raw/`), extracted
  (`text/`, `pdftotext -layout`, screener-clean, no OCR needed) and indexed (`index.csv`).
- **0 fetch failures / 0 purged (404) attachments** — every listed `/pmn/files/<id>.pdf`
  returned HTTP 200. After recovery, **0 in-scope PMN minutes remain unrecovered.**
- These fill genuine holes in the audited layer: the repo's council minutes jump
  2025-10-14 → 2025-11-18 and are sparse across early 2026; PC had no Aug-2021 minutes.

## Lessons that shaped the counts (documented for the next city)

- **Notice date ≠ meeting date.** PMN posts the minutes attachment on a *later* meeting's
  agenda notice. Example: notice 1035255 dated **2025-11-04** carries `CM 10-21-25.pdf`,
  which is the **2025-10-21** council meeting. Every recovered date in `index.csv` is the
  date printed *inside* the PDF, not the notice date.
- **Notice title ≠ document type.** Two notices titled "…Agenda" (2026-02-03, 2026-02-10)
  actually attach approved **minutes** documents. Type was confirmed by reading each PDF.
- **No purge observed here** (unlike prior cities where older `/pmn/files/` blobs 404). All
  9 Nephi attachments were still live as of 2026-07-05.

## What is NOT here (honest gaps / deliberate exclusions)

- **Pre-2020 PMN minutes** (47 council, 6 PC minutes-bearing notices) — below the repo's
  2020 data floor; enumerated in `council.json`/`pc.json` but deliberately not downloaded.
- **PMN historical *search* is POST-only** (`/pmn/searchresult.html`, CSRF-protected) —
  disallowed by the polite-scraper rule. Enumeration used the **GET** cumulative browse
  endpoint, which returns each body's complete history, so no coverage was lost.
- **CRA (5737)** — **now harvested in full (2026-07-19)**; see the CRA section in this dir's
  `CLAUDE.md` and `cra.json`. 10 notices 2016–2023; 0 new minutes within the 2020 floor (2021-07-27
  already in-repo, 2023-12-19 agenda-only → `meeting_minutes/minutes_unrecovered.csv`). **LBA (6527),
  Public Library (1868)** remain not cross-checked (LBA out of scope; Library is not a legislative body).
- **PMN is a pre-meeting NOTICE service, not a minutes archive.** Minutes attach to only a
  minority of notices, concentrated in the 2025–2026 era for Nephi; the authoritative
  minutes source for this repo remains **CivicPlus** (`nephi.utah.gov/AgendaCenter`). PMN's
  role here is a gap-filler, which yielded 9 items.

## Provenance

Raw bytes + SHA-256 + HTTP status for every fetch are in `raw/_fetch_log.jsonl`
(written by `scripts/polite_fetch.py`). Parser: `parse_notices.py`. Full parsed notice
inventories: `council.json`, `pc.json`. Set-difference result: `recoverable.json`.
