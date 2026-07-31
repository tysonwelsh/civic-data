# PMN backfill — coverage (Emigration Canyon)

**As-of:** 2026-07-14. **Source 4 (PMN backfill) of `/expand-city-sources`.**
Purpose: fill documented minutes gaps in the audited `meeting_minutes/` +
`planning_commission/` datasets without touching them, and RE-VERIFY the honest gaps
those datasets already record. Scope: the two Emigration Canyon PMN bodies only.

## Entity / bodies (confirmed)
- **PMN entity:** Emigration Canyon = **1317** (govType 3, Municipality;
  `/pmn/list/entities.html?id=3`).
- **Public bodies (all of them):** **5809** Emigration Canyon Council · **1562**
  Emigration Canyon Planning Commission (`/pmn/list/publicBodies.html?id=1317`). No RDA /
  no third body exists.
- **Decoy excluded:** *Emigration Improvement District* = a SEPARATE PMN entity **524**
  (govType 5, special district — sewer/water; own elected board). Not swept.

## Recovered this run

| body | date | meeting | pmn_file_id | notice | format | why it was missing |
|---|---|---|---|---|---|---|
| PlanningCommission | **2025-11-13** | EC Planning Commission | 1363983 | 1040893 | scanned→ocr | minutes were posted LATE (attached to a later notice as "November minutes.pdf") after the original harvest; was logged in `planning_commission/minutes_unrecovered.csv` as "no approved-minutes doc recovered". |

**1 minutes doc recovered** (PC). It is an image-only scan (7 pp); OCR sidecar in
`text/`. Council: **0** recovered (nothing was missing).

## (a) MSD AgendaCenter 2017-gap hunt — HEADLINE: 0 Emigration Canyon minutes exist there

The recon + CLAUDE named `msd.utah.gov/AgendaCenter` as "the documented backfill avenue"
for the purged 2017 (+ scattered 2018–19) EC minutes. **It is not one.** The MSD CivicPlus
AgendaCenter `ViewFile` endpoint keys purely on a global meeting-id (MID); the
`_MMDDYYYY-` prefix is cosmetic (`/AgendaCenter/ViewFile/Minutes/<MID>` alone returns the
file). I enumerated the **entire** document set — **MID 1–189** (190+ = 404) — and
classified every one by governing body:

| body on the MSD AgendaCenter | minutes docs |
|---|---|
| MSD **Board of Trustees** | 110 (+32 image-only, sampled = all Board of Trustees) |
| Magna | 39 |
| White City | 5 |
| Kearns | 4 |
| Copperton | 2 |
| **Emigration Canyon Council or PC** | **0** |

The only 3 MIDs whose text mentions "Emigration Canyon" (18, 110, 112) are **MSD Board of
Trustees** meetings that merely list an Emigration Canyon representative in attendance
(verified titles: "BOARD OF TRUSTEES … GREATER SALT LAKE MSD"). The MSD **DocumentCenter**
Emigration Canyon folder (Index/51) holds only *long-range-planning study* PDFs (e.g.
"Emigration Canyon Technical Assessment"), **no meeting minutes**.

⇒ **The purged 2017 (council 2017-01-04; PC 2017-01-12 … 2017-12-14, 14 dates) and the
scattered pre-2018-10 minutes cannot be recovered from MSD. The gap stays a genuine gap.**
Note several of those 2017 PC "meetings" were CANCELLED — their PMN notices attach
`YYMMDD_EmigrationTPC_Cancelled.pdf`, i.e. no minutes ever existed.

## (b) PMN sweep + purge re-confirm

Full-history notice walk of both bodies (`/pmn/list/notices.html?id=<body>&page=N`,
cumulative; each notice page opened, every `/pmn/files/<id>` attachment classified):

| body | notices swept | attachments | live minutes-labeled | live minutes NOT already a repo file_id | of those: dup-by-date / genuine recovery |
|---|---|---|---|---|---|
| 5809 Council | 211 | 618 | 40 | 14 | 14 dup / **0** |
| 1562 PC | 268 | 588 | 104 | 45 | 44 dup / **1** (2025-11-13) |

The repo is a **superset by meeting-date** of every LIVE PMN minutes doc. The non-repo
live file-ids are re-uploads / alternate versions of dates the repo already holds
(Approved-vs-Draft, Workshop/Board-of-Canvassers companions, "Minute Attachments" exhibit
packets, and the recurring PMN habit of re-attaching a prior month's minutes to the next
meeting's notice for approval — a new file-id, same meeting).

**Purge re-confirmed (genuine):** every pre-2018-10 file-id is a 315-byte 404 stub, while
the repo's floor file downloads:

| probed pmn_file_id | meeting (label) | HTTP |
|---|---|---|
| 269375 / 276101 / 284177 | PC 2017-01-12 / 02-16 / 03-16 (all `…_Cancelled.pdf`) | **404** |
| 282733 / 287825 / 358927 / 376797 | Council 01-11-17 / 02-07-17 / 10-03-17 / 12-20-17 | **404** |
| 406461 / 439745 | Council 01-02-18 / 06-28-18 (pre-boundary) | **404** |
| **459655** | Council **2018-10-25** (repo floor) | **200** ✓ |

The purge boundary sits at file-id ≈ 450000 (~mid-2018), exactly as `fetch_new.py`
documents. Recovered coverage therefore begins 2018-10-25 (council) / 2018-11-15 (PC).

## (c) OCR-upgrade catalog (leads — none resolvable)

The 2 audited council scans that yielded 0 extractable motions were checked for a
born-digital replacement on PMN and MSD AgendaCenter. **None exists** — each is published
only as an image-only scan:

| audited date | audited pmn_file_id | pages / extractable chars | born-digital copy found? |
|---|---|---|---|
| 2024-02-22 (Regular) | 1163111 | 4 pp / 0 | No. Only "02-22-2024 Approved Minutes.pdf" (this scan). The other 2024-02-22 file (1161751) is the *Special* meeting, already born-digital in the repo. |
| 2025-01-28 (Regular) | 1254241 | 18 pp / 0 | No. Only version; companion 1254243 is a "Minute Attachments" exhibit packet, not minutes text. |

MSD AgendaCenter holds no EC docs (see (a)), so it offers no upgrade either. These remain
image-only scans — an upstream publication limit, not an extraction failure. (The one doc
recovered this run, PC 2025-11-13 / 1363983, is likewise image-only; it is stored
`format=scanned`, `extraction_method=ocr`.)

## Provenance artifacts (in `_scripts/`)
- `ec_pmn_sweep_5809.csv`, `ec_pmn_sweep_1562.csv` — every notice attachment, classified,
  with the minutes-liveness probe.
- `ec_pc_recovery_candidates.csv` — each non-repo live PC minutes file, dated from its
  content and bucketed DUP / RECOVERY.
- `ec_msd_catalog.csv` — all 189 MSD AgendaCenter MIDs, classified by body.
- `ec_pmn_sweep.py`, `ec_pc_date_recon.py`, `ec_msd_enumerate.py` — the GET-only crawlers.
