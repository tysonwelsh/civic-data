# Ogden — Utah Public Notice (PMN) availability (confirmed as-of 2026-07-05)

Source: Utah.gov Public Notice Website (`https://www.utah.gov/pmn/`). Discovered via the
GLOBAL chain (never guessed): `entities.html?id=3` → Ogden → `publicBodies.html?id=225`.

## Confirmed entity + body ids

| Thing | id | notes |
|---|---|---|
| **Ogden** (entity) | **225** | not "Ogden Valley City" (6307), not "North Ogden" (221) |
| City Council | 320 | individual body page shows only ~last 6 months |
| **Redevelopment Agency** | **321** | individual body page shows only ~last 6 months |
| **Municipal Building Authority** | **322** | individual body page shows only ~last 6 months |
| Planning Commission | 340 | full history 2008–2026 on its notices page |
| **City Council, Redevelopment Agency, Municipal Building Authority** (combined) | **6587** | **full history 2013–2026** — this is where Ogden actually files CC/RDA/MBA notices |

### Key discovery — where the RDA/MBA minutes actually live
Ogden does **not** post CC/RDA/MBA minutes under the separate `321`/`322`/`320` bodies
(those pages honor PMN's "only notices from the past 6 months" cap and return almost
nothing). Every historical City-Council, Redevelopment-Agency and Municipal-Building-
Authority notice — with its meeting-minutes PDF attachment — is filed under the **combined
body 6587**, whose notices page returns the full 2013–2026 history in one GET
(`notices.html?id=6587&page=300`, ~1 MB, 1541 notice rows, 290 "Meeting Minutes"-labelled
attachments). Planning Commission (340) likewise returns full history directly.

## Notice / attachment structure
Each notice is a table row: title link (`/pmn/sitemap/notice/<id>.html`), an **event
date**, and 0+ attachments (`/pmn/files/<fileId>.pdf` + a type label in parentheses).
The event date on the RDA/MBA/PC minutes notices equals the meeting date; every fetched
PDF's internal "Minutes of the … meeting held on <date>" line was confirmed to match its
filename date (±0 days here).

## Lessons observed on this crawl
- **(a) Blob purge:** none hit — all 10 targeted `/pmn/files/*.pdf` returned HTTP 200.
  (The individual-body 6-month cap, not blob purge, is what hides older items.)
- **(b) type label ≠ doc type:** the single 2022 attachment labelled "Meeting Minutes"
  (`09-06-22 Packet.pdf`) is an agenda packet, not minutes — excluded.
- **(c) `.doc` attachments:** some 2019/2023 CC minutes are Word `.doc`, not PDF (only
  affects already-held CC dates; not fetched).

## What PMN holds vs. does NOT hold (RDA/MBA target window)
- **2023 RDA minutes: 7 present** (individual PDFs) → all net-new, recovered.
- **2020 MBA minutes: 2 present** → net-new, recovered.
- **2022 RDA minutes: NONE** on PMN — only budget/hearing *notices* (labelled "Other"),
  no minutes attachment. Honest gap: not published to PMN.
- **2022 MBA minutes: NONE** on PMN (budget notices only).
- **2023 MBA minutes: NONE** on PMN (bond/hearing notices only).
- Out-of-window bonus (2019: 7 CC/WS + 3 RDA minutes) exists on PMN but is **outside the
  2020–2026 scope** and was not fetched.

Crawl HTML retained under `raw/_crawl/` for full reproducibility.
