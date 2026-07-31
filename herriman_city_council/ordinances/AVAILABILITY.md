# ordinances/ — what was checked, what exists, what doesn't

As-of **2026-07-13** (build date; all URLs verified live that day).

## Where Herriman's adopted ordinances live (checked in this order)

1. **City site (`herriman.gov`)** — the "Ordinances and Code" page and the City
   Recorder page link ONLY to the codifier (below); the Public Notices page has a
   "Recently Approved Ordinances" section that carries **text-only** notices (no
   PDFs, current items only — one budget notice at build time). **No ordinance PDF
   archive on the city site.** Sitemap crawled; no other ordinance page exists.
2. **Codifier: Municipal Code Online** —
   `https://herriman.municipalcodeonline.com/book?type=ordinances` (the "City Code"
   link in the site nav). An Angular SPA whose XHR layer (`/book/expand`,
   `/book/content`) returns **"Unauthorized Access" to non-browser clients**, and
   whose `/docs` grid for the ordinances book lists zero documents. Consolidated
   current text only. **Recorded as the code host, NOT mirrored** (the skill's
   standing rule for bot-gated codifiers).
3. **Municipal Code Online public S3 archive — the full-text source.** The codifier's
   backing bucket allows anonymous listing:
   `s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/?list-type=2&prefix=herriman/ordinances/`
   → **133 keys / 111 distinct signed adopted-ordinance PDFs, 2018→2026** (multi-upload
   numbers deduped to the latest upload; every key recorded in
   `archive_backcatalog.csv`). Filenames carry the zoning case number
   (`ORD 2021-31_Z2021-45_…`). ~91% are wet-signature scans (tesseract OCR sidecars);
   10 born-digital. Same source that served Bluffdale (also an MCO city).
4. **Utah Public Notice (PMN), entity 155** — bodies **1287 "Public Hearings and
   Notices"** (the Recorder channel, 764 notices) and **1155 "City Council"**.
   **190 distinct ordinance-adoption notices, 2014→2026** (deduped across both
   bodies; catalog in `pmn_notices.csv`), each retained verbatim as
   `raw/pmn/notice_<id>.html`. Unlike Murray (body 7321), Herriman's PMN notices are
   **HTML summary notices with NO PDF attachments** — they give ordinance number +
   adoption-meeting date + a one-sentence subject, not the full text.
5. **Legacy S3 bucket `herriman-agendas` (us-west-1)** — Wayback CDX enumeration of
   all 167 archived keys shows **agendas/minutes folders only; no ordinance folders**.
   Dead end for this dataset.
6. **PrimeGov (`herriman.primegov.com`)** — meeting `documentList` types are only
   Agenda / Minutes / Packet / Notice of Cancellation. No ordinance documents.

## What the dataset holds

- **274 distinct ordinances** indexed (2014-25 → 2026-14; adoption window
  2014-06-12 → 2026-06-18). **2020+ (the repo's vote floor): 194 ordinances**, of
  which **130 land-use**.
- Full signed text: **111** (raw/archive PDFs; 101 OCR + 10 born-digital sidecars).
- Notice-summary only: **121** (PMN HTML rows, no full text anywhere online).
- Motion-derived only (`within_source`): **42** — witnessed solely by the citing
  council motion; no independent document found.
- Linkage (2020+): **125 high / 6 medium / 9 low / 42 within_source / 12 none**.
  Pre-2020's 80 rows are all `none` (below the minutes/vote floor — indexed for the
  back-catalog, not linkable).

## Honest gaps

- **Pre-2018 full texts**: the MCO archive starts 2018. 2014/2017 exist as notices
  only; **2015–2016 have nothing anywhere** (no PMN notices those years — a Recorder
  posting gap, not proof no ordinances passed).
- **PMN notice coverage is uneven** (e.g. 2023: only 6 notices vs 19 ordinances
  witnessed) and the **MCO archive is selective** (mostly code/zoning amendments;
  budget/tax and one-off ordinances often never get a PDF there).
- **12 series holes 2020+** (`unrecovered.csv`): numbers never witnessed in any
  source (2020-04/06/18/30, 2021-02, 2022-12, 2023-01/11, 2024-06, 2025-06,
  2026-12/13). May be unassigned/failed numbers or unpublished ordinances; the
  2026 pair may simply postdate this build.
- **2026-14** (final budget, adopted 2026-06-18 per the Recorder) postdates the
  repo's minutes coverage (ends 2026-05-27) — `none` until the minutes layer
  catches up.

## Leads surfaced for OTHER datasets (nothing existing was modified)

- **Missing council minutes proven by Recorder notices — RESOLVED (2026-07-16).**
  Adoption notices stated meetings were held on **2020-03-25, 2020-05-13,
  2020-10-14, 2020-12-09, 2021-08-11, 2022-03-23, 2022-05-11** with no minutes in
  `../meeting_minutes/`. All seven dates' minutes were PMN-recovered
  (`../pmn_backfill/`) and promoted into the vote layer 2026-07-16
  (`provenance=pmn_minutes`); the corresponding ordinance rows re-linked (most now
  `high`). The Recorder-notice completeness oracle worked exactly as designed.
- ~~**2021-17/18/20 double-witness ambiguity**: noticed as adopted 2021-08-11, but
  identical-subject motions passed 2021-10-13 — unresolvable without the 8/11
  minutes; the three rows are held at `medium` with notes.~~ **RESOLVED
  (2026-07-16, minutes promotion):** the recovered 2021-08-11 minutes (PMN file
  770437, promoted with `provenance=pmn_minutes`) contain the adopting motions with
  full named roll calls — the "2021-10-13 identical-subject motions" were the FULL
  2021-08-11 minutes embedded as an approval attachment inside the (now-deindexed)
  2021-10-13 agenda-compilation doc, mis-dated by the extractor. All five
  ordinances **2021-17…2021-21 now link `high` to their true 2021-08-11 motions**
  (2021-19/21 additionally recovered by healing the source's dropped-verb motion
  lead-ins). The Recorder-noticed adoption date was correct all along.
- **Recorder/minutes numbering typos** (all documented as overrides in
  `build_index.py`, sources kept verbatim): notice 675239 prints 2021-10 for the
  fireworks ordinance that the motion adopts as 2021-11; notice 819153 prints
  2022-06 for the annexation adopted as 2023-06; notice 796087 prints only zoning
  case Z2022-116 (= ORD 2022-40); notices 846044/846052/846056 print "July 12,
  2022" for the 2023-07-12 meeting; notice 1080729 prints "May 14, 2026" for the
  2026-05-13 meeting; minutes motions 2025-08-13 #14 and 2023-04-12 #3 print
  2025-18 / 2023-05 for what the signed PDFs show are 2025-17 / 2023-08.

## Corpus screen

`screen_corpus.py` run 2026-07-13 over `text/` (301 files): no stubs, no
duplicates, no read errors. Outliers investigated, all benign: 2018-26 dict-ratio
(a use-table of short codes), 2019-20 (mathematical-italic Unicode in an impact-fee
formula exhibit, born-digital), 2023-08 (8 replacement chars in signature-scrawl
OCR), notice hyphenation ("meet-ing", "Her-riman" — the Recorder's own line-break
style, preserved verbatim).
