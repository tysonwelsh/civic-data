# PMN backfill coverage — Millcreek

Cross-check of the Utah Public Notice (PMN, `utah.gov/pmn`) minutes holdings against the
already-acquired minutes layer, by **meeting DATE** (±4-day tolerance for meeting-date vs
posted-date offset), as of **2026-07-06**.

## PMN bodies discovered (via the entity chain, NOT guessed)

`entities.html?id=3` (Municipality) → **Millcreek entity `id=1279`** →
`publicBodies.html?id=1279` lists 12 bodies. The three relevant to the minutes layer:

| Body | PMN body id | Notices (total) | With `(Meeting Minutes)` | PMN minutes date range |
|---|---|---|---|---|
| **City Council** | **5741** | 554 | 298 | 2017-01-09 → 2026-05-26 |
| **Planning Commission** | **5815** | 433 | 145 | 2017-02-15 → 2026-05-20 |
| **Community Reinvestment Agency (CRA)** | **6367** | 142 | 59 | 2018-05-14 → 2026-06-08 |

(Other Millcreek PMN bodies not in scope: Board of Canvassers 7495, Envision Committee 5861,
Historic Preservation Commission 7681, Land Use Hearing Officer 5885, Mayor 5949, Millcreek
Community Foundation 7931, Millcreek Recorder 5837, Planning Director 8167, Tax Entity
Committee 6513.) Note the single 2017 canvass minute recovered below was actually filed under
the **City Council** PMN body (5741), not the Board of Canvassers body.

> **Note on the id discrepancy:** the city `CLAUDE.md`/`fetch_new.py` refers to PMN "Millcreek
> City Council body 1031". The live entity chain (2026-07-06) resolves City Council to
> **5741**. 1031 does not appear in Millcreek's current publicBodies list; treat **5741** as
> authoritative for the council body going forward.

## Cross-check result: the repo minutes layer is a near-total superset of PMN

The existing `meeting_minutes/` (Council + CRA) and `planning_commission/` layers already
hold a minutes document (or a logged unrecovered/agenda row) for **every PMN minutes date but
one recoverable gap**. PMN attaches minutes sporadically, so the repo is the superset — as
expected. Every "present" match below is an **exact-date** match; the ±4-day tolerance masked
nothing.

### City Council body (5741) — checked vs `meeting_minutes/minutes_index.csv`

| Year | Repo minutes rows | PMN minutes | Missing from repo |
|---|---|---|---|
| 2016 | 5 | 0 | 0 |
| 2017 | 47 | 39 | **1** → 2017-11-21 (recovered ✔) |
| 2018 | 30 | 30 | **1** → 2018-03-20 (PMN file dead 404 — unrecovered) |
| 2019 | 36 | 36 | 0 |
| 2020 | 35 | 35 | 0 |
| 2021 | 32 | 32 | 0 |
| 2022 | 30 | 30 | 0 |
| 2023 | 25 | 24 | 0 |
| 2024 | 30 | 29 | 0 |
| 2025 | 26 | 26 | 0 |
| 2026 | 12 | 11 | 0 |

### CRA body (6367) — checked vs `meeting_minutes/minutes_index.csv`

Every one of the 59 PMN CRA minutes dates (2018–2026) matches an existing repo date.
**0 missing** in every year. (CRA minutes live in `meeting_minutes/`, `body=CRA`.)

### Planning Commission body (5815) — checked vs `planning_commission/minutes_index.csv`

Every one of the 142 PMN PC minutes dates (2017–2026) matches an existing repo date.
**0 missing** in every year.

## Recovered (1 meeting)

- **2017-11-21 — Millcreek Board of Canvassers, General Election Returns Canvass**
  (`raw/2017/2017-11-21_Board_of_Canvassers_Minutes.pdf`, 252 KB, scanned image PDF →
  OCR'd with tesseract → `text/2017-11-21_Board_of_Canvassers.txt`). A special 4:00 p.m.
  meeting of the council-sitting-as-Board-of-Canvassers that certified the Nov 2017 general
  election and seated **Dwight Marchant (District 2, 1,734 votes)** and **Bev Uipi
  (District 4, 3,930 votes)**. Filed under the City Council PMN body; absent from the repo
  minutes layer. Tally-only roll call ("All Council Members voted yes"), consistent with the
  pre-2022 tally-only seam documented in the city `CLAUDE.md`.

## Still missing (1 meeting — verified dead at source)

- **2018-03-20 — City Council Budget Work Meeting.** PMN notice `453049` lists a
  `CC 3-20-18 Work Meeting Minutes.pdf` attachment, but that file (and the notice's
  Handouts.pdf) both return **HTTP 404** on `utah.gov/pmn` — a dead PMN attachment. Already
  logged in `meeting_minutes/minutes_unrecovered.csv` (the AgendaCenter version is a budget
  spreadsheet only, no narrative minutes/votes). Unrecoverable from either source. See
  `unrecovered.csv`.

## Method notes

- Bodies discovered via the GET-only entity chain (never guessed by id proximity).
- Full notice history pulled via the cumulative single-GET `notices.html?id=<body>&page=300`
  (the "past 6 months" list view and the POST/CSRF search were avoided per the polite-GET rule).
- All fetches through `scripts/polite_fetch.py`; discovery HTML retained under
  `raw/_discovery/` and every attempt (incl. the 404s) logged to `raw/*/_fetch_log.jsonl`.
- The existing minutes layer was **not modified** — this is a separate, reviewable dataset.
