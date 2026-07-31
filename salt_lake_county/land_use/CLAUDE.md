# salt_lake_county / land_use — how to use this module

County land-use minutes as a searchable text corpus, for growth/housing/development
research. This is the **LAND_USE** module of the `salt_lake_county/` entity (the
`legislative/` module holds the County Council; this holds the Planning Commissions).

## What's here

- `minutes/<year>/<date>_planning_commission.md` — Salt Lake County Planning Commission
  (unincorporated county + metro townships).
- `minutes/<year>/<date>_mountainous_planning_commission.md` — Mountainous Planning
  District Planning Commission (canyons / mountain areas). **Two separate bodies** — see
  SOURCES.md. Filter on the `body` front-matter field or the filename slug.
- `raw/<date>_<pmnfileid>_minutes.pdf` — the born-digital source PDF for each md.
- `minutes_index.csv` — one row per meeting: `date, body, md_path, source_url,
  minutes_status, note`. `md_path` is relative to `salt_lake_county/` (the federation
  loader reads it). `source_url` is the PMN file URL. All rows are `Approved` minutes.
- `SOURCES.md` — provenance, enumeration method, dating rules.

## Coverage (retrieved 2026-07-11)

| Body | Meetings w/ minutes | Range | Cancelled meetings | Held, no minutes posted |
|---|---|---|---|---|
| Planning Commission | 61 | 2020-01-15 … 2026-03-11 | 17 | 8 |
| Mountainous Planning District PC | 35 | 2020-01-02 … 2026-03-19 | 41 | 4 |

**Total: 96 meetings, 96 markdown files, 97 raw PDFs. Every PDF is born-digital
(clean pypdf text); zero OCR/image-only.** (⚠ **corrected 2026-07-31**, was 62 PC / 97
meetings — see "One meeting, two PMN postings" below. Raw PDFs exceed meetings by one
because the 2024-12-11 meeting has both its draft and its approved posting retained.)

Per-year meetings-with-minutes:
- Planning Commission: 2020=11, 2021=12, 2022=11, 2023=11, 2024=9, 2025=6, 2026=1
- Mountainous PDPC: 2020=8, 2021=9, 2022=4, 2023=4, 2024=5, 2025=4, 2026=1

## Honest gaps (never fabricate to fill these)

- **Recent minutes lag.** Minutes are posted only after the *next* meeting approves them,
  so the newest 1–2 held meetings have no approved minutes yet (Planning Commission
  2026-06-10, 2026-07-15; MPDPC 2026-07-16). Not a defect — pending approval.
- **Older held meetings with no minutes on PMN** (source gap, not an extraction failure):
  Planning Commission 2021-08-19, 2021-11-04, 2022-07-13, 2022-09-14, 2024-02-14,
  2024-04-10; MPDPC 2021-07-01, 2022-09-01, 2023-12-21. The notices exist; PMN carries no
  minutes PDF for them.
- **Cancelled meetings** (17 PC + 41 MPDPC) are real "no meeting" records, not gaps —
  they carry no minutes by definition and are omitted from the index. MPDPC in particular
  cancels frequently (it only convenes when the mountain district has business).
- **Agendas / packets / staff reports / audio** exist on PMN but are out of scope here
  (this module is the minutes text corpus only).

## One meeting, two PMN postings — the 2024-12-10 phantom (fixed 2026-07-31)

PMN carried the **same** Planning Commission meeting twice: a pre-approval posting
(file `1240211`) and the approved posting (file `1250791`, stamped "Meeting minutes
approved on March 26, 2025"). The two were dated differently because the SOURCES.md
dating rule falls back to the minutes **header text** when no `YYMMDD` filename prefix
is present — and the clerk's header carries a **typo**, "Wednesday, December 10, 2024".
December 10, 2024 was a **Tuesday**; **December 11 was the Wednesday**, and the
2025-03-26 minutes approve "the **December 11, 2024** Planning Commission Meeting
Minutes." The real date is **2024-12-11**. The `2024-12-10` markdown + index row were
therefore removed (4 phantom motions, 0 votes — the meeting is tally-only); the raw
draft PDF is retained as `raw/2024-12-11_1240211_minutes.pdf`. **No meeting occurred on
2024-12-10**, so nothing is now missing. When both postings of one meeting are present,
prefer the approved one, but note the pypdf superscript artifact `build_votes.py`
now repairs (`rejoin_split_second`): the approved copy splits `2nd by:` across two lines.

## Cardinal rules (repo-wide)

- Never fabricate minutes text or dates. If a meeting has no minutes, it's absent — that
  absence is the honest datum (see gaps above), don't infer content.
- `raw/` PDFs and the extracted markdown are the canonical layer; regenerate derived
  layers, don't hand-edit these.
- Source of record for minutes is **pmn.utah.gov body 712**; the county website hosts
  agendas only.
