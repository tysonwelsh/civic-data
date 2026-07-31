# Cache County — source reconnaissance (2026-07-20)

The MID-tier county entity in civic-data (fed_index 104, FIPS 49005). Cache County contains
**logan** (the repo's Cache-Valley city). This maps the county's own legislative /
growth / development records. Governance: **Council–Executive form** — a **7-member
elected County Council** (legislative) + a **separately elected County Executive**
(currently **David Zook**; formerly Craig Buttars) who is the executive and **does NOT
vote**. So a full council roll tallies to **7**. Meets ~**2nd & 4th Tuesdays** in Logan.

The centerpiece of this build is the **legislative NAMED roll-call vote layer** — in the
born-digital era Cache County prints **every member's Aye/Nay on every motion, including
unanimous ones**, which is *richer than Salt Lake County's own minutes* (SLCo minutes are
tally-only; only its Legistar API names unanimous votes).

## Legislative — County Council (self-hosted CMS) ✅ primary source found

- **Platform: self-hosted CMS** at `https://cachecounty.gov` (NOT Legistar, NOT a hosted
  vendor). Landing: `https://cachecounty.gov/countycouncil/countycouncil.html`.
- **Documents** live under `https://cachecounty.gov/assets/meetings/countycouncil/<year>/`
  in three sibling folders — `Minutes/`, `Agendas/`, `Media/` (media packets). A few
  2015–2019 files sit loosely under `assets/meetings/` or use lowercase `minutes/`.
- **Enumeration:** the landing page has a year `<select>` (options **2011–2026** + an
  **Archive**). Selecting a year navigates to `countycouncil.html?year=<YYYY>`, which the
  server renders with that year's full meeting table (Minutes/Agenda/Media links) inline.
  **Directory listings 403; individual files fetch by exact filename.** Filenames are
  **wildly irregular** ("01-11-22 APPROVED.pdf", "Cache County Minutes 02.10.2026 -
  Final.pdf", "cache-county-minutes-01.14.2025-(approved-and-combined).pdf", "Combined
  Final 01-27-2026 Meeting Minutes.pdf") — they MUST be scraped from the year pages, never
  guessed. Utah PMN mirrors also exist (e.g. `utah.gov/pmn/files/<id>.pdf`) as a fallback.
- **Inventory harvested (this build, floor 2015-01-01):** **312 unique Minutes PDFs**
  across 2015–2026 (2015:25, 2016:24, 2017:24, 2018:24, 2019:26, 2020:24, 2021:28,
  2022:36, 2023:31, 2024:28, 2025:25, 2026:17 partial). Includes Council regular meetings,
  Council **Workshops** (often vote-less), **Board of Canvassers** (council sitting as
  canvassers), and county **Service Area No. 1** governing-body minutes (all appear on the
  council page; body tagged from the filename).

## THE VOTE RECORDING CEILING — two distinct eras (verified from PDF text/OCR)

**Era A — born-digital NAMED roll calls (≈2021 → 2026): the centerpiece.** Recent minutes
are born-digital and print a **full named roll call on every motion, unanimous included**.
Grammar (verbatim, from `2025/Minutes/...01.14.2025...pdf`):

> Action: Motion made by Councilmember Kathryn Beus to approve the amended agenda; seconded
> by Councilmember Nolan Gunnell
> Motion passes.
> Aye: 7 David Erickson, Barbara Tidwell, Kathryn Beus, Nolan Gunnell, Sandi Goodlander,
> Keegan Garrity, Mark Hurd
> Nay: 0

and a genuinely divided vote from the same document:

> Action: 1:37:26 Vote for Kathryn Beus as Vice Chair
> Aye: 4, Kathryn Beus, Sandi Goodlander, Keegan Garrity, Mark Hurd
> Nay: 3 Barbara Tidwell, Nolan Gunnell, David Erickson
> Motion Passes

Structure: an `Action:` line (optionally prefixed with a video timecode like `1:37:26`)
carrying `Motion made by <mover> ... ; seconded by <seconder>` (seconder can be "None");
a verbatim result line (`Motion passes.` / `Motion Passes` / `Motion Fails`); then
`Aye: N <names>`, `Nay: N <names>`, and optionally `Absent: N <names>` / `Abstain: <names>`.
Name lists are comma-separated and **wrap across physical lines** (must be joined up to the
next label). Minor born-digital spacing quirks occur ("Good lander", missing commas) — NOT
OCR. This layer is HIGH confidence.

**Era B — scanned, TALLY-ONLY narrative (2015 → ≈early 2021): recording ceiling.** Older
minutes are **image-only scans** and use a narrative tally grammar (verified via tesseract
OCR of `2017/minutes/01-10-2017...pdf` and `2020/...07-14-2020...pdf`):

> ACTION: Motion by Vice Chair Erickson to approve the agenda as written. White seconded the
> motion. The vote was unanimous, 5-0. Potter & Zilles absent.

Here the **mover + seconder are named and a tally is printed ("5-0", "6-0") with absentees
sometimes named, but individual members are NOT enumerated** unless a division is called —
a true recording ceiling (cf. nephi / west_jordan PC), compounded by OCR noise. This layer
is LOW confidence and honestly **tally-only** (`names_recorded=0`); it is never silently
trusted as a named roll.

## OCR seam ledger (per-document density measured; boundary is a document property)

| year | status | note |
|---|---|---|
| 2015–2020 | **SCANNED / OCR** | image-only (≈1 text-char/page via pdftotext); tally-only grammar |
| 2021 | **MIXED** | early meetings still scanned (e.g. `01-05-21` is a 22 MB image PDF); named born-digital begins mid-year |
| 2022–2026 | **BORN-DIGITAL** | rich text; full named roll calls |

Detection is per-document (pdftotext char-density; <~300 chars/page ⇒ scanned → tesseract
OCR, `ocr: true` in front-matter, extraction confidence downgraded). Many scanned files are
very large (up to ~190 pages / 22 MB) because they **bundle the media packet** after the
minutes body. tesseract is available locally; ocrmypdf/pytesseract are not.

## Depth below the 2015 floor (noted for future backfill — NOT harvested here)

- **Year pages 2011–2014** are available via the same `?year=` mechanism (born pattern
  identical to 2015–2020: scanned, tally-only).
- **Archive page** `https://cachecounty.gov/countycouncil/minutes-archive.html` holds
  **396 PDFs for 1995–2010** under `assets/meetings/countycouncil/archive-minutes/<year>/`
  (e.g. `2010/01-12-10.pdf`). All pre-floor; queued for a backfill pass in the closing/TODO.

## Bodies & other modules

- **legislative/** (this agent) — County Council + Workshops + Board of Canvassers +
  Service Area No. 1, from the CMS minutes. Votes prose-extracted (named 2021+, tally-only
  2015–2020).
- **land_use/ · plans/ · ordinances/ · gis/ · elections/ · projections/** — owned by other
  agents / the closing pass (Cache County Planning Commission for unincorporated land use,
  county General Plan, adopted ordinances, GIS catalog, the county Clerk election canvass,
  Gardner/GOPB projections). NOT in scope here.

## Module status

| module | source | status |
|---|---|---|
| `legislative/` | cachecounty.gov CMS minutes (2015+) | 🔨 harvest → extract (named 2021+) → db |
| `land_use/` etc. | other agents | ⬜ separate |
