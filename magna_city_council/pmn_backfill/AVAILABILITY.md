# pmn_backfill/ — what was checked, what exists, what stays a gap

**As-of:** 2026-07-14 · Source 4 (Utah Public Notice backfill) of `expand-city-sources`.
Polite GET-only. Additive; built review-only 2026-07-14, then **promoted into the vote
layer 2026-07-16** (12 of 13 docs, `provenance=pmn_minutes`; the 2025-11-18 CRA DRAFT
stays review-only) — see `CLAUDE.md`.

## What was checked
- **PMN entity discovery** for Magna across **all govTypes** (1–8). Municipality entity
  **1323** (Magna City) holds every governance body; the only other Magna entities are
  govType-5 special districts (**Magna Water District 602**, **Magna Mosquito Abatement
  601**) — documented decoys, excluded.
- **Every Magna public body crawled** via the cumulative
  `notices.html?id=<body>&page=500` GET: Council **5803** (430 notices), Planning
  Commission **1559** (309), CRA **6925** (26), Administrative Hearings **6379** (5),
  Traffic Safety **9537** (0). Minutes detected by **filename + content**, not the
  (unreliable) PMN type label — Magna's CRA draft-minutes were mislabeled "Public
  Information Handout".
- **Per-date set-difference** of every body's PMN minutes vs the audited repo indexes
  (`meeting_minutes/minutes_index.csv` for Council/CRA/Canvassers,
  `planning_commission/minutes_index.csv` for PC), ±4-day tolerance.
- **CivicPlus AgendaCenter `ArchivedMinutes` probe** (angle a): all 99 council/CRA
  Minutes-slot dates 2022–2026 enumerated via the GET `Search` endpoint; `PreviousVersions`
  probed on 10 dates.
- **Liveness-probed** all 13 recovery candidates + 4 purged controls + 2 live controls.

## What exists / was recovered
- **13 minutes documents recovered, all from PMN** (5 Council body 5803, 8 CRA body
  6925) — see `index.csv` and `coverage.md`. Every recovered file was content-verified as
  genuine minutes; 9 scanned image PDFs were OCR'd (`tesseract`, labeled `format=scanned`),
  4 are born-digital text. Corpus screen (`screen_corpus.py`): **0 outliers** on all three
  metrics.

## What stays a gap (verified, NOT recovered — do not fabricate)
- **Council 2017 + Jan–Jun 2018 (36 meetings)** — a genuine PMN file-store purge. Only 2
  of the 36 (2017-08-01, 2017-08-15) even survive as listing references (files 329391 /
  329393 on the 2017-09-19 notice); both blobs return HTTP 404, exactly like the ids
  already in `meeting_minutes/minutes_unrecovered.csv`. The other 34 have no attachment
  anywhere. Stays unrecoverable.
- **Planning Commission 2017–2018 (57 meetings)** — agenda/audio only; MSD published no
  minutes PDF for the township-era PC (body 1559 minutes begin 2019-03-14). Genuine
  publishing gap.
- **CivicPlus `ArchivedMinutes`** — the slot is **unused** on Magna's AgendaCenter (only
  `ArchivedAgenda` prior-versions exist); no recorded minutes hide there. 0 recoveries.
- **Administrative Hearings (6379)** — Land-Use Hearing Officer agendas/packets + one
  Mayor's meeting; **no minutes** ever posted; not a legislative body. Out of scope.
- **CRA 2024-10-22** — held by the repo (CivicPlus); PMN body 6925 carries no minutes for
  it (its minutes record begins 2024-11-12). Not a gap in this dataset.

## Rules honored
Additive only; existing datasets untouched; every raw retained (`raw/` +
`_fetch_log.jsonl` with per-file sha256); nothing fabricated (both the council purge gap
and the PC 2017–2018 gap stay gaps); polite GET-only. Parent `README.md`/`CLAUDE.md`,
`sources.csv`, `cities.db`, `coverage.json`, `TODO.md` are owned by the orchestrator and
were not edited here.
