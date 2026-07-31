# Copperton — Utah Public Notice (PMN) minutes backfill & superset verification

**As-of:** 2026-07-14 · **Method:** Source 4 of `expand-city-sources` — GET-only PMN
crawl (cumulative `notices.html?id=<body>&page=500`) → per-date, per-body set-difference
against the audited repo minutes indexes (±4-day tolerance), with content-detection of
every candidate PDF, PLUS a purge re-probe (angle b) and an OCR-upgrade evaluation
(angle c). Additive/review-only; the audited `meeting_minutes/`, `planning_commission/`,
`db/`, `weeks/` layers were NOT touched.

## Headline: 0 gap-fill recoveries; the repo is a COMPLETE SUPERSET of both PMN bodies

- **Council (body 5831): 0 recoveries.** All 32 PMN council minutes meeting-dates already
  exist in the repo's 106-doc council index. Nothing missing.
- **Planning Commission (body 1560): 0 recoveries — complete superset.** All 17 real PMN
  PC minutes meeting-dates are in the repo's 17-date PC index. The one apparent "extra"
  PMN date (2025-07-02) is a FALSE POSITIVE (see below), not a gap.
- **1 OCR-upgrade LEAD found** (2025-10-15 council; born-digital PMN DRAFT of a date the
  repo holds only as a GoDaddy RICOH scan) — cataloged in `index.csv`, NOT swapped.
- **2017-02 → 2018-06 purge (29 meetings) RE-CONFIRMED genuine** (angle b, below).
- **Minor logged gaps (Sep-2025, Dec-2025, June-2026) RE-CONFIRMED unfillable** — PMN has
  agenda-only notices for those dates, no minutes.

## PMN entity + body discovery (GET-only)

- **Municipality entity:** Copperton = **entity 1353** (govType 3;
  `/pmn/list/entities.html?id=3` → `/pmn/list/publicBodies.html?id=1353`).
- **All Copperton public bodies** (entity 1353) — exactly two, both in scope:

  | pmn_body_id | Body | Notices | PMN minutes meeting-dates | In scope |
  |---|---|---|---|---|
  | **5831** | Copperton Council | 207 | 32 | yes (repo superset; 0 recovered) |
  | **1560** | Copperton Planning Commission (MSD-staffed) | 253 | 17 real (+1 false pos.) | yes (complete superset; 0 recovered) |

  There is **no CRA/RDA/agency body** for Copperton (unlike Magna's body 6925) — the
  township/town has never run a Community Reinvestment Agency on PMN.
- **All govTypes swept** for Copperton-named entities (the sweep-all-bodies + decoy
  lesson). The only Copperton entity outside the Municipality is **govType 5 (special
  district) entity 482 = Copperton Improvement District** (bodies 2497 Board of Directors +
  3013 Public Hearing) — the **water-district DECOY, EXCLUDED** per task. No Copperton
  entity exists in govTypes 1/2/4/6/7/8.
- Files fetched from **`https://www.utah.gov/pmn/files/<id>.pdf`** (not `pmn.utah.gov`).

## Per-body, per-year accounting

### Council (body 5831) — 0 recoveries
Set-difference of all 32 PMN council minutes meeting-dates vs the repo's 106 council dates
(±4d): **0 genuinely missing, 0 falling in the logged purge gap.** PMN is the *enumerable
mirror* the core harvest already used for the ≤2022 era; the town's GoDaddy site supplies
2023+; every recoverable PMN minutes date is already indexed. 74 repo council dates have no
PMN minutes counterpart (they came from GoDaddy) — expected, not a gap.

| Era | Repo council docs | PMN minutes dates | Recovered here |
|---|---|---|---|
| 2017-02 → 2018-06 (purge) | 0 (logged unrecoverable) | 0 surviving | 0 (purge genuine — angle b) |
| 2018-07 → 2022 | present (PMN-sourced) | present | 0 |
| 2023 → 2026 | present (GoDaddy + PMN) | present | 0 |

### Planning Commission (body 1560) — 0 recoveries, complete superset
Set-difference of the PMN PC minutes meeting-dates vs the repo's 17 PC dates: **exact
match after removing one false positive.** The repo already holds every recoverable PC
minutes doc on PMN.

- **FALSE POSITIVE — 2025-07-02 / file 1292781 "May minutes.pdf":** this attachment
  (labeled "Meeting Minutes" on the 2025-07-02 PC notice 1004465) is the **May 13, 2025**
  PC minutes ("COPPERTON PLANNING COMMISSION MEETING — Tuesday, May 13, 2025"), being
  approved at the July meeting. The repo already holds 2025-05-13 (from file 1360575, a
  later-posted copy of the same meeting). The set-diff flagged 2025-07-02 only because the
  filename carries no date, so the notice's event date was used as a fallback. NOT a new
  meeting → NOT a recovery.
- **The 2025-07-02 PC meeting itself was held** (agenda + public-hearing notice + a
  "Copperton Parking Revisions 2025 PC Combined Staff Report" are attached) but **its own
  minutes were never posted** — every subsequent 2025 PC notice (Aug–Dec) is a cancellation
  placeholder with no minutes. An honest source-side gap, nothing to recover.
- The PC 2008–2018 notices on body 1560 carry agendas/cancellations only — no minutes docs
  (consistent with "most PC meetings cancelled"). Earliest recoverable PC minutes: 2019-03.

## Angle (b) — 2017-02 → 2018-06 purge RE-CONFIRMED genuine

All 33 purge-era council notices (2017-02-15 → 2018-06-20) still LIST a "Meeting Minutes"
attachment, but with a distinct, newly-surfaced band of file-IDs (315659…413295) — none of
which had been captured in `minutes_unrecovered.csv` (which used filename candidates). A
sample of **9 spanning the entire window** was HEAD/GET-probed 2026-07-14; **all 9 return a
315-byte `text/html` stub (HTTP 404)**, while **3 live controls return real PDFs**:

| file_id | meeting | probe result |
|---|---|---|
| 315659 | 2017-02-15 (earliest) | 315 B text/html — **404** |
| 315663 | 2017-03-01 | 315 B text/html — **404** |
| 316412 | 2017-06-07 | 315 B text/html — **404** |
| 338077 | 2017-08-02 | 315 B text/html — **404** |
| 353273 | 2017-07-19 | 315 B text/html — **404** |
| 363379 | 2017-12-06 | 315 B text/html — **404** |
| 380907 | 2018-01-17 | 315 B text/html — **404** |
| 406451 | 2018-02-21 | 315 B text/html — **404** |
| 413287 | 2018-06-20 (last purged) | 315 B text/html — **404** |
| **459667** | 2018-07-18 (control, survives) | 82,351 B application/pdf — **200** |
| **459671** | 2018-08-15 (control) | 78,480 B application/pdf — **200** |
| **522659** | 2019-01-16 (control) | 187,514 B application/pdf — **200** |

The file-store boundary sits exactly at the mid-2018 retention cliff: everything below is
gone, everything from 2018-07-18 on survives. This corroborates the 2026-07-12 verification
with a fresh, independent set of file-IDs. **The purge is a genuine PMN retention purge; the
29 rows in `meeting_minutes/minutes_unrecovered.csv` stand unchanged.** (Wayback CDX for a
purged id timed out on this run — the direct-probe evidence is conclusive on its own; a
Wayback pass is noted in the parent TODO as optional.)

## Minor logged gaps (Sep-2025, Dec-2025, June-2026) — RE-CONFIRMED unfillable

The core repo logs three minor recent council gaps. PMN was checked date-by-date:

| Gap | PMN council notice(s) | Minutes on PMN? |
|---|---|---|
| Sep-2025 | 2025-09-17 (notices 1029187, 1023399); 2025-08-29 special | **none** (agenda-only) |
| Dec-2025 | 2025-12-09 (Rio Tinto special), 2025-12-17 (notices 1043835/1047843/1046087) | **none** (only prior-month DRAFTs attached) |
| June-2026 | 2026-06-17 (notices 1090327/1089253/1086995) | **none** (only the May FINAL DRAFT attached) |

PMN has the notices (the meetings happened) but **no minutes document** for any of the
three — the same honest "meeting exists, minutes don't" condition already recorded. PMN
cannot fill these. Nothing recovered.

## Angle (c) — OCR-upgrade catalog (born-digital PMN copies of the repo's RICOH scans)

The repo holds **15 town-era minutes as `ocr`/`text+ocr`** (RICOH scans). For each, PMN was
checked for a distinct born-digital copy. Result: **1 genuine born-digital lead; 8 checked
negative; 6 not evaluable (PMN copy IS the repo's source, or none exists).**

| repo date | repo src / fmt | PMN copy | PMN body text | verdict |
|---|---|---|---|---|
| **2025-10-15** | godaddy / ocr | **1353103 (DRAFT)** | **born-digital, 16,436 chars** | **OCR-UPGRADE LEAD → index.csv** |
| 2024-10-16 | godaddy / ocr | 1423359 (102 pp) | body scanned; 125k chars are born-digital *attachments* only | NOT an upgrade (attachment trap) |
| 2025-01-15 | godaddy / ocr | 1235687 | 0 chars — also scanned | not an upgrade |
| 2025-02-19 | godaddy / ocr | 1254253 | 0 chars — also scanned | not an upgrade |
| 2025-04-16 | godaddy / ocr | 1276705 | 0 chars — also scanned | not an upgrade |
| 2025-07-16 | godaddy / ocr | 1313165 | 0 chars — also scanned | not an upgrade |
| 2025-11-19 | godaddy / ocr | 1370221 | 0 chars — also scanned | not an upgrade |
| 2026-05-20 | godaddy / ocr | 1451567 | 0 chars — also scanned | not an upgrade |
| 2026-04-15 | godaddy / text+ocr | 1447749 (15 pp) | body scanned; thin text tail = attachments | not an upgrade |
| 2025-03-19 | godaddy / ocr | (none — notice 980970 has no minutes) | — | no PMN copy |
| 2024-03-20 | pmn / ocr | 1184255 (= repo source) | scanned | same file, no alternate |
| 2024-06-19 | pmn / ocr | 1172995 (= repo source) | scanned | same file |
| 2024-07-17 | pmn / ocr | 1221481 (= repo source) | scanned | same file |
| 2024-08-21 | pmn / ocr | 1221483 (= repo source) | scanned | same file |
| 2024-09-18 | pmn / ocr | 1221501 (= repo source) | scanned | same file |

**The one lead (2025-10-15)** is retained in `raw/` + cataloged in `index.csv`
(`recovery_source=pmn_ocr_upgrade_lead`). It is the **DRAFT** minutes; the repo's approved
copy for that date is the GoDaddy scan. It is a clean-text LEAD only — **not swapped** into
the audited layer. The 8 verified-negative candidate PDFs are retained under
`work/probes_ocr/` with their `raw/_fetch_log.jsonl` provenance (they are duplicate scans,
not dataset artifacts).

## Bottom line

| Body | PMN minutes | In repo (audited) | Recovered here | Still-missing |
|---|---|---|---|---|
| Council (5831) | 32 dates | 106 dates (superset) | **0** | 29 purged 2017-02→2018-06 (404); Sep/Dec-2025 + Jun-2026 (no minutes published) |
| PC (1560) | 17 dates (+1 false pos.) | 17 dates (superset) | **0** | 2025-07-02 held but minutes never posted |
| OCR-upgrade leads | — | — | **1 lead (2025-10-15, not swapped)** | — |

Do **not** merge into the audited layers in place. This is a review dataset; any promotion
(and the 2025-10-15 OCR re-read) is a separate, deliberate task for the orchestrator/TODO.
