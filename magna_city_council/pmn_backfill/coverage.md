# Magna — Utah Public Notice (PMN) minutes backfill & superset verification

**As-of:** 2026-07-14 · **Method:** Source 4 of `expand-city-sources` — GET-only PMN
crawl (cumulative `notices.html?id=<body>&page=500`) → per-date, per-body set-difference
against the audited repo minutes indexes (±4-day tolerance), with content-detection of
every recovered PDF — PLUS the South-Salt-Lake **CivicPlus `ArchivedMinutes` probe**
(angle a). Additive/review-only; the audited `meeting_minutes/`, `planning_commission/`,
`db/`, `weeks/` layers were NOT touched.

## Headline: 13 minutes documents recovered (all from PMN)

- **5 City Council minutes** (body 5803) absent from the repo: 2024-02-13, 2024-02-27,
  2024-11-26, 2026-03-10, 2026-06-09 — real regular-meeting minutes that were simply
  never posted to CivicPlus and were missed by the core PMN harvest.
- **8 Community Reinvestment Agency (CRA) minutes** (body 6925): 2024-11-12, 2025-01-14,
  2025-02-11, 2025-04-08, 2025-05-13, 2025-06-10, 2025-09-23, 2025-11-18 — the repo held
  only 5 CRA dates; this more than triples the CRA record.
- **Planning Commission (body 1559): 0 recoveries — the repo is a complete superset.**
- **CivicPlus `ArchivedMinutes` probe: 0 recoveries — Magna's CivicPlus does not use that
  slot** (details below).

## PMN entity + body discovery (GET-only)

- **Municipality entity:** Magna City = **entity 1323** (govType 3;
  `/pmn/list/entities.html?id=3` → `/pmn/list/publicBodies.html?id=1323`). No separate
  "Magna Metro Township" entity exists — body 5803 spans BOTH the township (2017-2024)
  and city (2024+) eras.
- **All Magna public bodies** (entity 1323):

  | pmn_body_id | Body | Notices | Minutes on PMN | In scope |
  |---|---|---|---|---|
  | **5803** | Magna Council | 430 | 61 meeting-dates | yes (core-harvested; 5 recovered here) |
  | **1559** | Magna Planning Commission (MSD-staffed) | 309 | 80 meeting-dates | yes (complete superset) |
  | **6925** | **Community Reinvestment Agency of Magna (CRA)** | 26 | 12 minutes docs | **yes — 8 recovered here** |
  | 6379 | Administrative Hearings (Land-Use Hearing Officer + a Mayor's mtg) | 5 | 0 (agendas/packets only) | no — no minutes; not a legislative body |
  | 9537 | Magna Traffic Safety Committee | 0 | 0 | no — no notices posted |

- **Every govType swept for Magna-named entities** (the sweep-all-bodies + decoy lesson).
  The only Magna entities outside the Municipality are both **govType 5 (special
  districts)** and are documented **DECOYS, excluded**: **602 Magna Water District** and
  **601 Magna Mosquito Abatement District**. No Magna entity exists in govTypes 1/2/4/6/7/8.

## Council (body 5803) — 5 recoveries; purge-gap VERIFIED genuine

Set-difference of all 61 PMN council minutes meeting-dates vs the repo's 166 council +
canvassers dates (±4d):

- **5 genuine recoveries** (approved minutes; not on CivicPlus, missed by the core PMN
  pull): **2024-02-13, 2024-02-27** (a Feb-2024 pair between the repo's 2024-01-23 and
  2024-03-12), **2024-11-26** (7.3 MB, born-digital, with plat attachments), **2026-03-10**
  (a text cover page over **scanned** minutes images → OCR'd), **2026-06-09** (scanned →
  OCR'd; newer than the repo's 2026-05-26 floor).
- **Purge gap (2017 + Jan–Jun 2018, 36 meetings) re-VERIFIED genuine.** Across all 430
  council notices, **only 2** pre-floor minutes attachments survive in any listing —
  2017-08-01 (file **329391**) and 2017-08-15 (file **329393**), both re-attached to the
  2017-09-19 approval notice (418125). **Both file blobs now return HTTP 404** (315-byte
  `text/html` stub), identical to the purged ids already in
  `meeting_minutes/minutes_unrecovered.csv` (338095, 338097, 281765, 413347 — all probed,
  all 404) and unlike live controls (459615, 1461255 = 200 `application/pdf`). The other
  34 purged meetings have **no surviving attachment anywhere on PMN.** → The purge is a
  genuine PMN file-store purge; the existing `minutes_unrecovered.csv` reasons stand
  unchanged. **No 2017/2018 recovery.**

## CRA (body 6925) — full accounting (recovered = 8)

The CRA (Community Reinvestment Agency) convenes in-recess before/with the City Council.
Body 6925 holds **12 minutes documents**; the repo previously held **5 CRA dates**
(2024-10-22 + 2025-07-08 + 2025-10-14 + 2025-12-09 + 2026-01-27):

| Coverage | Dates |
|---|---|
| On PMN **and** already in repo (4) | 2025-07-08, 2025-10-14, 2025-12-09, 2026-01-27 |
| **Recovered here (8)** | 2024-11-12, 2025-01-14, 2025-02-11, 2025-04-08, 2025-05-13, 2025-06-10, 2025-09-23, 2025-11-18 |
| Repo-only, no PMN-6925 minutes (1) | 2024-10-22 (CivicPlus-sourced; PMN body 6925's minutes begin 2024-11-12) |

7 of the 8 recovered CRA minutes are `APPROVED`; 2025-11-18 is the posted `DRAFT` (no
approved copy yet). 5 are scanned image PDFs (`format=scanned`, `tesseract-ocr`); 3 are
born-digital (`pdftotext-layout`). All 8 content-verified as genuine CRA minutes
(mover + seconder + tally grammar, "Board Member" roster) — not agendas.

## Planning Commission (body 1559) — complete superset, 0 recoveries

Set-difference of all 80 PMN PC minutes meeting-dates vs the repo's 80
`planning_commission/minutes_index.csv` dates: **exact match, 0 missing.** The repo
already holds every recoverable PC minutes doc on PMN. The **PC 2017–2018 gap (57
meetings, agenda/audio only)** stands: body 1559's earliest minutes document is
2019-03-14; the 2017–2018 township-era PC / General-Plan-Steering notices carry agendas
and audio but no minutes PDF. Genuine publishing gap at the source.

## CivicPlus `ArchivedMinutes` probe (angle a) — mechanism not used by Magna

The SSL lesson: on a CivicPlus AgendaCenter, recorded minutes can hide in an
`ArchivedMinutes` slot (via each Minutes doc's `PreviousVersions` page) while the visible
Minutes slot serves a packet/draft. **Checked and refuted for Magna:**

- The `AgendaCenter/Search?term=&CIDs=3&startDate=…&endDate=…` endpoint is **GET-accessible**
  (no POST needed) — enumerated **all 99 council/CRA Minutes-slot dates 2022–2026**. Every
  one is within ±4 days of a repo date → **CivicPlus adds no dates the repo lacks.**
- **`ArchivedMinutes` never appears** in any Search listing (0 across 5 years).
- **`PreviousVersions` probed on 10 dates** — including the wrong-doc dates where the core
  deliberately used PMN instead of CivicPlus (2025-03-11, 2025-04-08, 2025-09-23,
  2025-10-28, 2026-03-10, 2026-06-09, …). Every one exposes only **`ArchivedAgenda`**
  (prior agenda drafts), **never `ArchivedMinutes`.** Magna's CivicPlus instance simply
  does not retain recorded minutes as archived versions — the real minutes for those dates
  live only on PMN (which the core used, and which this backfill completes).

## Bottom line

| Body | PMN minutes | In repo (audited) | Recovered here | Still-missing |
|---|---|---|---|---|
| Council (5803) | 61 dates | 166 dates (superset) | **5** | 36 purged 2017-01→2018-06 (404) |
| CRA (6925) | 12 | 5 dates (4 overlap) | **8** | 0 (1 draft-only awaiting approval) |
| PC (1559) | 80 dates | 80 dates | 0 | PC 2017-2018 (no minutes published) |
| CivicPlus ArchivedMinutes | — | — | 0 | n/a (slot unused) |
| **Total recovered** | | | **13** | |

**PROMOTED 2026-07-16** — 12 of the 13 docs (5 Council + 7 approved CRA) were merged into
`meeting_minutes/all_votes.csv` with `provenance=pmn_minutes` via
`meeting_minutes/extract_backfill_votes.py` (51 motions; db/motions_std/weeks rebuilt;
the raw/text files stay HERE and are what the vote rows' `source` paths point at). The
2025-11-18 CRA doc is stamped "DRAFT MINUTES – UNAPPROVED" and remains review-only —
nothing else in this dataset is merged in place. See `CLAUDE.md` "Promotion".
