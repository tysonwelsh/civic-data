# pmn_backfill — availability record

**Checked:** 2026-07-13, Utah Public Notice website (`utah.gov/pmn`), GET-only
(cumulative `notices.html?id=<body>&page=200`; the POST/CSRF historical search was
never used). **2026-07-16:** promotion executed (see `CLAUDE.md` §PROMOTED) — 66
docs merged into the audited vote layer with `provenance=pmn_minutes`; one
additional doc fetched (2021-01-13 RCCM minutes, file 690779 — the repo's portal
doc for that date turned out to be the CDRA minutes mistitled), bringing the
recovered-minutes count to **71**.

## What exists on PMN for Herriman (entity id 155)

- Eight bodies crawled (City Council 1155, Planning Commission 1151, CDRA 2256,
  HCSEA 6239, HCFSA 7553, Appeals Authority 1171, Joint CC/PC 1251, Public Hearings
  1287). Full body inventory and per-year tables: `coverage.md`.
- **2,307 notices, 356 unique minutes attachments in the 2020+ window; 70 were
  absent from the repo and are recovered here** (20 council, 13 PC, 5 joint, 14
  CDRA, 10 HCSEA, 6 HCFSA, 2 Appeal Authority). 9 cancellation notices retained as
  proof for 2020 gap dates.
- PMN also carries **meeting audio recordings** (388 council + 363 PC attachments,
  `.mp3`) and agenda-packet "Public Information Handout" PDFs — out of scope for
  this dataset, but they exist (relevant to a future `transcripts/` source: the
  2020-07-29 joint meeting, whose minutes were never posted, HAS audio on notice
  618815).

## What does NOT exist (honest gaps)

- **2020-07-29 Joint CC/PC work meeting minutes** — meeting held (audio + packet on
  PMN), minutes never posted anywhere found. Unrecoverable as text.
- **2020-07-22, 2020-11-25, 2020-12-23** — expected 2nd/4th-Wednesday council slots
  with NO PMN notice of any kind; consistent with no meeting scheduled. Not stubbed.
- **Proven cancellations** (2020): PC 01-16, 03-19, 12-17; Joint 04-29, 12-30;
  Council work 09-16, 10-21, 12-16; Council 11-11 rescheduled → 11-18. Proof pages
  in `raw/cancel_*`, catalogued in `index.csv`.
- **Appeals Authority Board** has only 2 minutes documents ever on PMN (2025-02-20,
  2026-06-09, both recovered); its other 14 notices are agendas/hearing notices
  with no minutes. The repo has no appeals dataset — these 2 docs are the entire
  known public minutes record for that body.
- **Public Hearings and Notices body (1287)**: 764 notices, zero minutes
  attachments — a notice board, not a minutes source.

## Below the data floor

PMN holds Herriman minutes back to **2008-07** (council ≈ 148 and PC ≈ 145
minutes attachments pre-2020, plus CDRA from 2009 and HCSEA from 2018). The repo's
data floor is 2020 by design, so these were inventoried (raw list HTML retained)
but not fetched. If the floor ever moves earlier, PMN is a viable primary source
for 2008–2019.

## Label-trust caveats (verified instances)

- Two minutes PDFs are mislabeled `(Audio Recording)` on PMN: 2025-09-10 RCCM
  (already in repo) and 2022-06-29 Joint (recovered). Filename scanning is required;
  PMN attachment-type labels alone under-count minutes.
- Council minutes can be filed under the PC body id (2021-03-24 RCCM) and Appeal
  Authority minutes under the PC body id (2026-06-09). Classification must come
  from the document/filename, not the PMN body.
- The 2025-02-20 Appeal Authority document is headed "PUBLIC MEETING AGENDA" but its
  body is narrative minutes ("The following are the minutes of … Mr. Church called
  the meeting to order at 2:07 p.m.") — kept as minutes, quirk noted.
