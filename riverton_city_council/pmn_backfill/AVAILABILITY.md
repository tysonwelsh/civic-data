# pmn_backfill/ — availability & holdings (Riverton City)

**As-of:** 2026-07-13. GET-only, polite (`scripts/polite_fetch.py`). No POST, no auth.

## PMN entity & body ids (discovered this run)

- **Utah Public Notice entity:** Riverton = **id 251** (govType 3 = Municipality;
  `/pmn/list/entities.html?id=3&limit=2000` → `/pmn/list/publicBodies.html?id=251`).
- **All 12 Riverton public bodies on PMN:**

  | PMN body id | Body | notice-dates | minutes-doc dates | minutes range |
  |---|---|---|---|---|
  | **889** | **City Council** (core) | 566 | 275 | 2013-07-16 .. 2026-06-02 |
  | **5473** | **Planning Commission** (core) | 228 | 177 | 2016-04-28 .. 2026-06-25 |
  | 1101 | Redevelopment Agency | 128 | 66 | 2010-07-16 .. 2026-05-05 |
  | 6161 | Riverton Law Enforcement Service Area | 62 | 55 | 2017-10-24 .. 2026-06-02 |
  | 7153 | Riverton Fire Service Area | 32 | 29 | 2020-10-16 .. 2026-06-02 |
  | 3415 | Board of Canvassers | 11 | 3 | 2017-11-21 .. 2019-11-19 |
  | 6233 | Historic Preservation Commission | 13 | 3 | 2024-12-05 .. 2025-06-05 |
  | 5701 | Riverton Historic Preservation Commission (legacy id) | 17 | 2 | 2016-10-13 .. 2016-11-09 |
  | 1102 | Board of Equalization | 12 | 1 | 2017-11-14 |
  | 1098 | Purchasing | 226 | 0 | — (bids/RFPs, no minutes) |
  | 1099 | Miscellaneous | 35 | 0 | — |
  | 1100 | Board of Adjustments | 24 | 0 | — (agendas only; body rarely convenes) |

  Ids are globally assigned, not sequential per city (as the SKILL warns). Discovered via
  the entity→publicBodies chain, not guessed.

## Granicus archive (independent source)

- `https://rivertoncity.granicus.com/ViewPublisher.php?view_id=1` — one publisher, all bodies.
  Full server-rendered table = **599 minutes links**, 2015-09 .. 2026-06. The table groups
  rows by meeting-name string; the same body appears under several historical labels (e.g.
  `City Council` / `City Council Meeting` / `Regular City Council Meeting` / `Work Session &
  City Council Meeting`; `Planning Commission` / `Planning Commission Meeting`).
- Minutes doc chain (vendor note, see CLAUDE.md): `MinutesViewer.php` → an HTML/gview wrapper
  that embeds the real PDF at `DocumentViewer.php?file=rivertoncity_<hash>.pdf&view=1`. The
  2015–early-2020 era instead serves the raw Word `.doc/.docx` or a generated-HTML minutes page.
- Granicus **minutes** holdings by body (deduped dates): Planning Commission 197, City Council
  ~192, Redevelopment Agency 60, Fire Service Area Board 31, Law Enforcement Service Area 58,
  Historic Preservation Commission 3, Board of Equalization 4, Board of Canvassers 3.

## Bodies OUTSIDE the core repo (inventory only — NOT recovered)

The repo's audited datasets cover only **City Council** (`meeting_minutes/`) and **Planning
Commission** (`planning_commission/`). The following bodies publish minutes on PMN and/or
Granicus but are **not** part of the core repo, so per the task they are inventoried here and
**not** recovered into `pmn_backfill/`:

- **Redevelopment Agency (RDA)** — a **separate** meeting body in Riverton (PMN 1101 /
  Granicus "Redevelopment Agency"), **not** an in-session recess of the Council (unlike some
  cities). 66 minutes on PMN (2010→2026-05-05), 60 on Granicus. A candidate for a future
  dedicated RDA dataset; left untouched here.
- **Riverton Law Enforcement Service Area (RLESA)** — PMN 6161, 55 minutes (2017→2026-06).
- **Riverton Fire Service Area (RFSA)** — PMN 7153, 29 minutes (2020→2026-06).
- **Historic Preservation Commission** — PMN 6233 (+ legacy 5701); sparse, ~5 minutes total.
- **Board of Equalization** — PMN 1102; 1 minutes doc.
- **Board of Canvassers** — PMN 3415; 3 minutes docs (election canvasses).
- **Board of Adjustments** — PMN 1100; agendas only, no minutes located.
- **Purchasing / Miscellaneous** — bids, RFPs, quorum notices; no meeting minutes.

## What was recovered (core bodies)

7 meetings, all born-digital (no OCR): 5 City Council + 2 Planning Commission. See `index.csv`
and `coverage.md`. Post-recovery **still-missing = 0** for both core bodies, every year within
the 2020 floor — the audited repo plus this backfill is a complete superset of PMN∪Granicus.

- **Council, from PMN:** 2020-01-07, 2020-01-21, 2020-02-04 (Word `.docx/.doc`; the repo's
  audited council series begins 2020-02-18).
- **Council, from Granicus (PMN carried no minutes):** 2023-09-05, 2023-11-07.
- **PC, from Granicus (PMN carried no minutes):** 2023-11-09.
- **PC, from PMN:** 2026-06-25 (posted after the last repo PC harvest of 2026-06-11; also on
  Granicus).

## Method / limitations

- Diff key = meeting **date**, ±4-day tolerance (posted-date vs meeting-date offset). Riverton
  minutes are posted on the meeting date, so most matches were exact.
- The Granicus RSS `mode=minutes` feed returns only the most recent **100** items
  (2024-05-21→2026-06-25); the full-range enumeration used the ViewPublisher HTML table instead.
- These recovered files are a **separate, reviewable dataset** — they are NOT merged into the
  audited `meeting_minutes/` or `planning_commission/` layers, and no votes were extracted from
  them. Merging them into the audited vote pipeline is a deliberate follow-up.
