# Bluffdale — `pmn_backfill/` (Utah Public Notice cross-check + recovery)

**Source 4 of `expand-city-sources`.** A SEPARATE, review-only dataset that cross-checks
the audited `meeting_minutes/` and `planning_commission/` layers against the statewide
Utah Public Notice repository (`utah.gov/pmn`) and holds any minutes genuinely missing
from the repo. **Additive — it never modifies the audited layers.** Built 2026-07-12.

## Headline result

**The Bluffdale repo is a near-complete superset of PMN's minutes holdings — but NOT a
total superset.** The 2026-07-17 wave-2 cross-check confirmed **2 genuine gaps** (see the
2026-07-17 addendum below and `crosscheck_flags.csv`): the **2022-08-16** and **2026-02-11**
Council meetings were HELD with minutes formally approved, yet those minutes are unpublished
on every sanctioned channel. Both are now logged in
`../meeting_minutes/minutes_unrecovered.csv` with a drafted GRAMA request
(`GRAMA_request_draft.md`). Aside from those two, the CivicPlus/CivicEngage city portal
(`bluffdale.gov`) carries the full 2020-floor record and PMN is only a thin mirror.
**Correction:** the earlier "0 genuine gaps" / "2024–2026 minutes … fully in the repo"
claims are superseded — 2026-02-11 is a real 2026 hole.

## What PMN holds for Bluffdale

- **Entity id 87** (`utah.gov/pmn/list/publicBodies.html?id=87`).
- Minutes-bearing bodies crawled (GET-only, cumulative `notices.html?id=<body>&page=300`):
  - **Council family** (the RDA/LBA/joint-PC sessions convene *in-session* inside one
    combined minutes PDF, which PMN posts redundantly under all four ids):
    **373** City Council · **4905** City Council & LBA · **2803** City Council & PC ·
    **2781** City Council & RDA Board.
  - **PC:** **374** Planning Commission (body **8955**, inactive PC & Board of Adjustments,
    holds 0 notices).
- PMN attaches minutes only through early 2024 (agendas continue after); 2024–2026 minutes
  live solely on the city portal — mostly in the repo, EXCEPT the confirmed **2026-02-11**
  gap (agenda posted, approved minutes never published; see `minutes_unrecovered.csv`).

## Method (reproducible, GET-only)

1. Discover entity id via `entities.html?id=3` (govType 3 = Municipality) → Bluffdale = 87.
2. `publicBodies.html?id=87` → enumerate all 16 bodies + global ids (see `coverage.md`).
3. For each council-/PC-family body, one cumulative GET
   `notices.html?id=<body>&page=300` returns the body's entire notice history
   (the historical *search* is POST/CSRF — never used; `polite_fetch.py` is GET-only).
4. Parse the list HTML for each notice's event date + attachment `(Meeting Minutes)` labels
   → PMN minutes-date set per family.
5. **Per-date set-difference** against `meeting_minutes/minutes_index.csv` /
   `planning_commission/minutes_index.csv` (±4-day posted-vs-meeting tolerance) — NOT
   per-year counts.
6. For any non-match: fetch the PDF, VERIFY its internal body-name header + date before
   trusting PMN's label.

## The one catalogued row (`index.csv`)

`2023-11-14` — PMN notice 872517 / file 1047617, labeled `(Meeting Minutes)` but actually a
**NOTICE OF QUORUM** for the "14400 South Construction Open House" ("NO OFFICIAL CITY
BUSINESS … no vote or action will be taken", Utah Code §52-4-203(7)). Internal header
("BLUFFDALE CITY COUNCIL") and date verified. **Not deliberative minutes** — PMN mislabeled
the attachment type. Retained for provenance; it is not a recovered meeting and not a gap.
Its presence keeps `index.csv` non-empty with full machine-readable provenance.

## Layout / schema

```
raw/
  _disc_entities.html         entity list (govType 3) — provenance
  _disc_bodies.html           Bluffdale bodies (entity 87)
  _notices_<bodyid>_*.html     cumulative notice history per crawled body
  pmn_council_2023-11-14_quorum_1047617.pdf   the one verified non-minutes item
  _fetch_log.jsonl            polite_fetch provenance (url/status/bytes/sha256/utc)
index.csv                     §9 pmn_backfill contract header (14 cols)
coverage.md                   per-year / per-body coverage tables + the mislabel writeup
CLAUDE.md                     this file
```

`index.csv` columns (SCHEMA_SPEC §9 `pmn_backfill` contract):
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`.
`path` is dataset-relative including `raw/`. `source=pmn`. `notice_url` = the PMN notice
page; `source_url` = the direct file; `pmn_body_id`/`pmn_file_id` = PMN's opaque ids.

## Caveats / rules honored

- **GET-only, polite** (`scripts/polite_fetch.py`, ≥1s/host); no POST, no CSRF search.
- **Raw retained** verbatim (discovery HTML + the fetched PDF + `_fetch_log.jsonl`).
- **Never fabricated:** a 0-recovery result is a real, complete finding — the repo simply
  already has everything PMN does.
- **Do NOT merge** into `meeting_minutes/` or `planning_commission/`. This is a review
  artifact only.
- Not loaded into `cities.db` by this run (`build_cities_db.py` not run per task scope).

## 2026-07-17 — final PMN-crosscheck deep flag verification (4 flags -> 2)

Deep-verified all 4 (fetched each notice detail); appended 2 exceptions; re-run (--cached) 4 -> **2**.
Refines the orchestrator's earlier '3 genuine leads': 2 distinct genuine leads, the PC 2024-09-11
flag is NOT a gap, and one 2022-08-16 row was a redundant sibling.
- **Recovery leads (2, agenda-grade, real meetings — NOT cancelled/rescheduled per notice text):**
  2022-08-16 (body 373) combined Council/LBA/RDA meeting (agenda+packet posted, no minutes; repo
  lacks — contradicts the dataset's '2024-26 fully in repo' claim); 2026-02-11 (body 373) regular
  Council & RDA meeting (agenda+packet, no minutes).
- **Exceptions:** duplicate x1 (2022-08-16 body 4905 = redundant LBA/RDA sibling posting of the
  same combined meeting); wrong_date x1 (2024-09-11 body 374 = a combined newspaper hearing notice
  bundling PC hearing 2024-08-21 [held: pc_2024-08-21_1466] and CC meeting 2024-09-11 [held:
  council_2024-09-11_1481] — both already in repo).
