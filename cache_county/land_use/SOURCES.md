# cache_county / land_use — SOURCES & provenance

## Source of record

**Cache County Planning Commission**, unincorporated Cache County land-use body.
Meets the **first Thursday** of the month (occasional special/second meetings).

- **Primary source:** the county website meeting archive,
  `https://www.cachecounty.gov/pz/planningcommission.html`. The page carries a
  year-selector; each year loads at `?year=<YYYY>` (2009–2026 available) with a table of
  Date / Agenda / Media Packet / Minutes / Listen / Watch. Minutes PDFs live under
  `assets/meetings/planningcommission/<year>/[Mm]inutes/…` (2026's newest under
  `assets/meetings/…`). Naming is inconsistent (`PC1_January_Final.pdf`,
  `PC07_11 July 24_final.pdf`, `01. January Minutes - Final.pdf`, …) so the harvest
  reads the table cell-by-cell (Minutes = 4th cell) rather than guessing URLs.
- **Recovery channel (not yet pulled):** Utah Public Notice (pmn.utah.gov) **body 1479**
  also carries Cache County PC notices/minutes 2009–2026 — the avenue for recovering the
  14 `NoMinutesPosted` gaps below. Logged, not executed (county site is comprehensive at
  ~90% of held meetings).

## Retrieval method (2026-07-20)

1. Fetched `planningcommission.html?year=YYYY` for 2015–2026, parsed each year's meeting
   table → `date, agenda_href, minutes_href, cancelled_flag`.
2. Downloaded every `minutes_href` (floor **2015-01-01**): **123 files** — 121 born-digital
   PDF + 2 `.docx` (2015-04-09, 2017-07-06). Zero image-only/OCR scans; all extract clean
   with `pypdf` / `python-docx`.
3. Wrote one markdown per meeting (front-matter + extracted text) and `minutes_index.csv`.

Regenerate a `text` body: re-run pypdf on the `raw/` file. Regenerate the vote CSVs:
`python3 build_votes.py`.

## Dating

Meeting date is the archive-table date (ISO `YYYY-MM-DD`), cross-checked against the
minutes header. Filenames are NOT reliable for dates (e.g. `PC1_4 Jan 23.pdf` sits in the
2024 folder) — the table date governs.

## Coverage & honest gaps

- **123 meetings with minutes**, 2015-01-08 … 2026-03-05.
- **14 held meetings, no minutes on the county site** (`minutes_status=NoMinutesPosted`;
  agenda exists): 2015-12-03, 2016-04-07, 2018-04-05, 2018-08-02, 2019-05-02, 2020-04-02,
  2020-08-06, 2020-10-01, 2021-07-29, 2022-01-06, 2022-11-03, 2024-04-04, 2024-12-05,
  2025-05-01. Source gaps, not extraction failures — recoverable via PMN body 1479.
- **4 recent 2026 meetings** minutes not yet posted (`PendingApproval`): 2026-04-02,
  2026-05-21, 2026-06-04, 2026-07-09.
- **2026-05-07 cancelled** (county posted a `*_cancelled` agenda) — omitted as a
  non-meeting.
- **Agendas / media packets / audio / video** exist on the site but are out of scope for
  this minutes-text module.

## Recording ceiling (see VOTES_README.md)

Tally-primary in the 2015→2024-10 era (numeric counts only, dissenters unnamed); fully
named ("Ayes:/Nays:") from 2024-11-07. A source characteristic, not an extraction limit.
