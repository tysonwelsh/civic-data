# summit_county / land_use — SOURCES

Land-use minutes for Summit County's two Planning Commissions. Retrieved 2026-07-20.

## Bodies
- **Snyderville Basin Planning Commission** — AgendaCenter category **CID=5** /
  county page `summitcountyutah.gov/591/Snyderville-Basin-Planning-District`.
- **Eastern Summit County Planning Commission** — AgendaCenter category **CID=6** /
  county page `summitcountyutah.gov/590`.

## Where the documents come from (two portals, spliced by date)

Summit County **migrated its live agendas/minutes off the old CivicEngage "Agenda Center"
to a new Granicus "Meetings and Minutes" portal on 2024-05-15.** Both eras were covered:

1. **AgendaCenter (CivicEngage)** — `provenance=agendacenter`. The pre-migration archive.
   Enumerated via the search endpoint (NOT the default page, which shows only the current
   year): `GET /AgendaCenter/Search/?term=&CIDs=<5|6>&startDate=01/01/<Y>&endDate=12/31/<Y>`,
   looped per calendar year 2015-2024. Minutes links are `ViewFile/Minutes/_<MMDDYYYY>-<id>`
   (the meeting date is embedded in the URL). Files are PDFs (a few are DOCX/scans — see
   below). Snyderville & Eastern both carry minutes here **2015-2023**.
2. **Granicus** — `provenance=granicus`. The post-migration portal. The full clip archive
   was parsed from **one page**: `summitcounty.granicus.com/ViewPublisher.php?view_id=1`
   (CollapsiblePanel per body → meeting rows with `AgendaViewer`/`MinutesViewer`/agenda-
   packet links). Minutes are HTML at
   `MinutesViewer.php?view_id=1&clip_id=<N>&doc_id=<uuid>`. Coverage: **Snyderville
   2022-11-08 → present, Eastern 2023-03-09 → present.** Agenda-packet PDFs (cloudfront)
   feed the `packets/` module.

**Splice rule:** prefer Granicus where a meeting exists in both (structured HTML with inline
agenda-item attachment labels); AgendaCenter fills 2015 → the Granicus start.

## Other channels (not primary here)
- **Utah Public Notice (PMN)** — public body **1503** ("Summit County Community
  Development") carries both PCs' notices + minutes (file URLs
  `utah.gov/pmn/files/<id>.pdf`; a Snyderville minutes example is `1354775.pdf`). PMN is the
  likely recovery channel for the **Snyderville-2021 / Eastern-2022** gaps, but its
  Angular search/sitemap AJAX backend returned "Technical Difficulties" for every scripted
  POST at build time (`search.html`, `searchresult.html`, `list/publicBodiesByName.html`,
  `sitemap/publicbody/1503.html` shows only a ~10-notice rolling window). Deferred as a
  future backfill (needs a working PMN enumeration or a browser session).
- **AgendaCenter agendas** (`ViewFile/Agenda/…`) exist 2015-2024 but are out of scope for
  this minutes corpus; staff-report content is captured in `packets/` from Granicus.

## Dating
The meeting date is the Granicus row date, or the AgendaCenter URL's embedded `MMDDYYYY`.
Both were sanity-checked against the minutes header. Filenames are `<YYYY-MM-DD>_<slug>.md`.

## Extraction
- Granicus HTML: script/style/nav stripped, content region from the "MINUTES / SUMMIT
  COUNTY" header, consecutive duplicate lines collapsed (Granicus repeats each agenda item
  as header + minutes). `extraction=granicus_minutesviewer_html`.
- AgendaCenter PDF: `pypdf` text (`extraction=pypdf_text`). One file (2016-10-25 Snyderville)
  was a **.docx served with a .pdf extension** — recovered via docx XML
  (`extraction=docx_xml`). 14 AgendaCenter files (mostly 2022 Snyderville) are image-only /
  oversize packets-in-the-minutes-slot: text unrecovered, flagged `needs_ocr_image_only`,
  binaries >10MB not stored. **No fabrication — only text the extractor actually produced.**
