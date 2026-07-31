# Kearns — Utah Public Notice (PMN) minutes backfill & superset verification

**As-of:** 2026-07-13 · **Method:** Source 4 of `expand-city-sources` — GET-only PMN
crawl (cumulative `notices.html?id=<body>&page=N`) → per-date, per-body set-difference
against the repo minutes indexes, with content-detection of every recovered PDF.

**Headline: 3 minutes documents recovered.**
- **2 Kearns Community Reinvestment Agency (CRA) minutes** — the previously-empty CRA
  body is now lit up (was **0 rows** — "a real honest gap" per the repo CLAUDE.md).
- **1 Planning Commission minutes (2019-04-08)** — a genuine recovery surfaced by the
  superset verification: it WAS on PMN all along but was mis-logged as unrecovered
  because its filename (`190408_KearnsTPC_Approved.pdf`) lacks the "Minutes" token the
  original build's filter keyed on (the **filename-not-label** lesson).

## PMN entity + body discovery (GET-only)

- **Municipality entity:** Kearns = **entity id 1321** (govType 3 = Municipality;
  `/pmn/list/entities.html?id=3` → `/pmn/list/publicBodies.html?id=1321`).
- **All Kearns public bodies** (entity 1321):

  | pmn_body_id | Body | Notices | Minutes docs on PMN | In scope |
  |---|---|---|---|---|
  | **5823** | Kearns Council | 255 | 138 meeting-dates | yes (already harvested) |
  | **1561** | Kearns Planning Commission (MSD-staffed) | 289 | 44 meeting-dates | yes (already harvested) |
  | **9273** | **Kearns Community Reinvestment Agency (CRA)** | 12 | **2 minutes docs** | **yes — RECOVERED here** |
  | 9553 | Kearns Community Committee | 6 | 0 (audio + handouts only) | no — advisory board, no minutes, out of scope |

- **Every govType swept for Kearns-named entities** (the "sweep-every-body + decoy"
  lesson). The only Kearns entity outside the Municipality is
  **Kearns Improvement District (entity 584, govType 5 = local/special district = the
  WATER district)** — a documented decoy, NOT a council/CRA/RDA body; excluded. No
  Kearns entity exists in govTypes 1/2/4/6/7/8. There is **no separate township-era
  RDA/CRA body** — the CRA (9273) is a city-era body first noticed 2025-07-14.

## CRA (body 9273) — full accounting (recovered = 2)

The CRA convenes in-recess before the City Council (city era only). Its PMN body holds
12 notices, of which only **3 meetings actually convened** and only **2 have minutes**:

| CRA meeting | Notice | Status | Minutes | Recovered |
|---|---|---|---|---|
| 2025-07-14 | 1010455 | **HELD** | APPROVED (file 1320109, **scanned→OCR**) | **✓** |
| 2025-08-11 | 1014499 | CANCELED (notice + cancellation PDF 1306841) | — | n/a |
| 2025-09-08 | 1020981 / 1079351 | **HELD** | DRAFT (file 1430807, born-digital) | **✓** |
| 2025-10-14 | 1029829 | CANCELED (cancellation PDF 1335803) | — | n/a |
| 2025-12-08 | 1043735 | CANCELED (cancellation PDF 1362055) | — | n/a |
| 2026-02-09 | 1058117 | CANCELED (cancellation PDF 1388449) | — | n/a |
| 2026-03-09 | 1064593 | CANCELED (cancellation PDF 1401729) | — | n/a |
| 2026-04-13 | 1072201 | CANCELED (cancellation PDF 1416859) | — | n/a |
| 2026-05-11 | 1079351 | **HELD** (audio 1432587) | not yet posted (only prior-mtg DRAFT attached) | pending |

Plus 3 schedule/calendar notices (1050501, 1014483, 1014485) — no meeting content.
Both recovered CRA minutes were **content-verified** as genuine ("CITY OF KEARNS CRA
MEETING MINUTES", BOARD MEMBERS PRESENT roster, motions). The 2025-07-14 APPROVED copy
is a **scanned image PDF** (pdftotext yields ~6 chars) → OCR'd with `tesseract`
(labeled `format=scanned`, `extraction_method=tesseract-ocr`); the 2025-09-08 DRAFT is
born-digital clean text. The CRA uses **tally-style** votes like the Council
(mover + seconder + numeric tally; dissent/abstain named).

## Council (body 5823) — superset CONFIRMED; purge-gap VERIFIED genuine

Set-difference of all 138 PMN council "Meeting Minutes" meeting-dates vs the repo's
116 `minutes_index.csv` dates (±4-day tolerance):

- **Repo is a complete superset of PMN's recoverable council minutes.** The only PMN
  council minutes NOT on disk are the **25 township meetings 2017-01-18 → 2018-06-11**
  — exactly the documented purge gap. **No new council recoveries.**
- **Purge VERIFIED (probed all 25 minutes file objects + Wayback):** every one of the
  25 meetings has a `(Meeting Minutes)`-labeled PDF still LINKED on its notice page
  (file ids **285127 → 413299**, all below the live-era floor), proving minutes were
  published — but every file blob now returns **HTTP 404** (315-byte error stub,
  `Content-Type: text/html`), while live controls (459651 = 2018-07-09, 1445065 =
  2026-05-11) return `200 application/pdf`. **Zero Internet Archive captures** for the
  sampled purged ids (285127, 301195, 360589, 406479, 413299). → The gap is a genuine
  **PMN file-store purge** (pre-~mid-2018 uploads), recoverable only if PMN restores
  the blobs. The existing `meeting_minutes/minutes_unrecovered.csv` reasons are
  **accurate** and stand unchanged.
- The other 16 documented council gaps (7 agenda+audio-only, 9 not-yet-posted) were
  re-confirmed present as such on PMN and are genuine — not recovered (no minutes exist).

## Planning Commission (body 1561) — superset confirmed EXCEPT one recovery

Set-difference of all 44 PMN PC minutes meeting-dates vs the repo's 43
`minutes_index.csv` dates:

- **1 genuine recovery: 2019-04-08** (Kearns Metro Township PC; file 502755,
  `190408_KearnsTPC_Approved.pdf`, approved 2019-06-10) — real MSD "MEETING MINUTE
  SUMMARY" born-digital minutes, absent from the repo and currently listed in
  `planning_commission/minutes_unrecovered.csv` as "genuinely absent." **That row is
  in fact recoverable and is recovered here.** (Do NOT hand-edit the audited
  `minutes_unrecovered.csv` — flagged for the orchestrator to reconcile on promotion.)
- **7 generically-named PC minutes** ("November minutes.pdf", "March minutes.pdf",
  "February minutes.pdf", etc.) attached to a LATER meeting's notice were each resolved
  by content/context to a meeting **already on disk** (draft copies of an
  already-approved meeting — e.g. "November minutes.pdf" on the 2025-12-01 notice = the
  2025-11-03 meeting the repo already holds). **Not new recoveries.**
- **The PC 2017-2018 gap IS genuine** (confirmed): MSD's approved-minutes PDFs on PMN
  body 1561 begin **2019-03-11**; the 2017-2018 PC notices carry agendas/packets/audio
  only, no minutes document. Stands unchanged.
- **One pre-floor find (out of scope, not recovered):** a `Feb minutes.pdf` (file
  725941) is a real **2016-02-08** Kearns *Township* PC meeting summary — below the
  repo's **2017 data floor** (township took effect 2017-01-01). Documented, not
  ingested.

## Bottom line

| Body | PMN minutes | On disk (audited) | Recovered here | Still-missing |
|---|---|---|---|---|
| CRA (9273) | 2 | 0 | **2** | 0 (1 meeting's minutes not yet posted) |
| Council (5823) | 138 dates | 116 dates (superset) | 0 | 25 purged (404) + 7 no-minutes + 9 not-yet-posted |
| PC (1561) | 44 dates | 43 dates | **1** (2019-04-08) | PC 2017-2018 (no minutes published) |
| **Total recovered** | | | **3** | |

Do **not** merge into `meeting_minutes/` / `planning_commission/` in place — this is a
review dataset. Promotion into the audited layer (incl. reconciling the PC 2019-04-08
`unrecovered.csv` row and extracting the CRA/PC votes) is a separate, deliberate task
for the orchestrator/TODO.
