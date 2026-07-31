# pmn_backfill/ — build method & caveats (Logan)

**Additive dataset.** Built by `expand-city-sources` **Source 4** (Utah Public Notice / PMN
cross-check). **As-of 2026-07-05.** This dataset **NEVER modifies** the audited `meeting_minutes/` or
`planning_commission/` layers — it is a *separate, reviewable* record of what PMN carries versus the
repo's Revize-built minutes.

## Bottom line
**Zero net-new minutes.** Logan's audited Revize minutes layer is a complete superset of PMN for
2020–2026 across Council, RDA, and Planning Commission. See `coverage.md` (per-year tables) and
`AVAILABILITY.md` (ids, method, the three verified-duplicate candidates).

## PMN public-body ids (Logan entity = 189, government type 3 = Municipality)
| Body | PMN body id |
|------|------------:|
| **Municipal Council** | **494** |
| **Planning Commission** | **487** |
| **Redevelopment Agency** | **495** |
| Board of Adjustments | 489 |
| Land Use Appeal Board | 490 |
| Historic Preservation Committee | 488 |
| (advisory: Parks/Rec 485, Light&Power 486, Forestry 493, Library 484, Fine Arts 496, Neighborhood 497; newer: Citizens Advisory 3473, Renewable Energy & Sustainability 2187, Solid Waste 8649, Regional Wastewater Rate 5307, Water/Wastewater Dept 9353, Golf 1410, Zoo 1409) | — |

Discover generically via GET: `/pmn/list/entities.html?id=3&limit=2000` → Logan entity **189** →
`/pmn/list/publicBodies.html?id=189&limit=2000` → every body + id (saved `raw/_bodies_189.html`).
**Recon correction:** the build recon's claim that RDA = body **1277** is WRONG — 1277 is Salt Lake
City's RDA. Logan's RDA is **495**. Always resolve ids via the global chain.

## Method
1. **Enumerate** each body's full history with the cumulative GET browse endpoint
   `/pmn/list/notices.html?id=<bodyId>&page=300` (one GET returns the whole history newest-first;
   all three saturate back to 2001–2008). Saved `raw/_notices_<id>_p300.html`. No POST/CSRF search.
2. **Parse** → `body_494.json` / `body_487.json` / `body_495.json` with `parse_notices.py`. Minutes
   carry the `(Meeting Minutes)` type label. Logan has no separate `(Agenda)` attachment type.
3. **Cross-check** (`crosscheck.py`): per-DATE set-difference of in-window (2020–26) PMN
   minutes-bearing notices against the repo indexes (Council & RDA split by `slug` in
   `meeting_minutes/minutes_index.csv`; PC in `planning_commission/minutes_index.csv`), ±4-day
   tolerance → `recoverable.json` (3 candidates).
4. **Document-level verification** — download each candidate PDF (`scripts/polite_fetch.py`, browser
   UA, notice Referer, throttled, logged to `raw/_fetch_log.jsonl`) and read the meeting date printed
   inside. All 3 were already-held minutes re-attached to a later/cancelled notice.

## ⚠️ The critical pitfall: notice date ≠ minutes date
A PMN notice's `Meeting Minutes` attachment is almost always the **prior** meeting's minutes (approved
at the noticed meeting); CANCELLED-meeting notices re-attach the last real meeting's minutes. Diffing on
the **notice** date yields false positives. Always confirm by the meeting date printed **inside** the
PDF. Here that turned all 3 flags into non-gaps:
- 2020-03-17 CANCELLED notices (Council 584203 + RDA 584229, byte-identical) → March 3 2020 minutes → repo has `2020-03-03`.
- 2026-06-16 notice (Council 1447537) → May 26 2026 Budget Workshop minutes → repo has `2026-05-26`.

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,notice_date,status,note`
(the §9 pmn_backfill contract + `notice_date,status,note` extras). The 3 rows are the
verified-duplicate downloads, all `status=duplicate-not-promoted`; `date` = the actual meeting date the
document is for (the already-held repo date), `path` = the extracted text sidecar under `text/`, raw PDF
under `raw/`. **No row represents a gap-fill** — this is an honest empty recovery with full provenance.

## Files
`raw/` recovered PDFs + browse/entity HTML + `_fetch_log.jsonl`; `text/` extracted sidecars
(`pdftotext -layout`, born-digital, screener-clean); `body_*.json` full parsed notice inventories;
`recoverable.json` flagged candidates; `parse_notices.py` / `crosscheck.py` build code;
`index.csv` / `coverage.md` / `AVAILABILITY.md` / this file.

## Do NOT
- Do not date-template PMN file URLs (ids are opaque) or POST to `/pmn/searchresult.html` (CSRF, and
  against the polite-scraper rule — the GET browse endpoint returns full history).
- Do not treat a PMN notice date as its minutes' meeting date.
- Do not promote the 3 duplicate rows into `meeting_minutes/` — they add nothing the repo lacks.

## 2026-07-17 — crosscheck flag verification (20 → 18)

Verified all 20 `crosscheck_flags.csv` flags. 2 new exceptions appended; re-run: **18 flags**
(all agenda_only_gap; 4 suppressed, 5 pending-adoption). The broader engine's agenda_only_gap
class is consistent with this dataset's "0 net-new MINUTES" finding — PMN carries only
AGENDAS (no minutes attachments) for these special-meeting dates.

**Exceptions (2):**
- `2021-06-15 / 487` **draft** — attachment `DRAFT Minutes 21June1.pdf` is DRAFT
  (non-authoritative) minutes embedded in an RDA agenda/packet notice filed under PC body
  487; repo PC is a superset (approved 2021-06-10 / 06-24 held).
- `2024-04-22 / 494` **other** — "Announcement of a Public Hearing regarding the Transfer of
  Money from an Enterprise Fund…" is a statutory hearing-ANNOUNCEMENT notice, not a meeting;
  council meets 1st/3rd Tuesdays (2024-04-16 held), 04-22 is a Monday.

**Recovery leads (18 agenda-grade — reported, NOT ingested; PMN has agenda only, so
recoverability of minutes is uncertain — reviewer checks Revize):**
- 2020–2023 **budget-workshop** dates the repo lacks (2020-05-26, 2021-05-11, 2021-05-25,
  2022-05-10, 2022-05-24, 2023-05-23). NOTE the repo DOES store budget workshops as their own
  dated council entries from 2025+ (e.g. 2025-05-13, 2025-05-27), so these earlier ones are
  genuine gaps.
- 2024-08-01 **Truth-In-Taxation** meeting (repo has 2025-08-07 TnT, not 2024).
- 2020-09-10 Joint Meeting with Nibley City Council; 2020-10-13 Council Interim Appointment.
- PC meeting agendas: 2022-06-30, 2024-06-13, 2024-07-25, 2025-08-28, 2025-11-18, 2026-04-23.

**Hardening candidate:** the RDA body-495 budget-workshop flags (2020-05-26, 2021-05-25,
2022-05-10) are exact duplicates of the council body-494 flag on the same date (RDA rides the
council doc — the "redundant council-family postings" the HARDENING pilot flagged as
tolerable). If cross-city rollout reports drown in these, add a `(date, repo_datasets)` dedup.
Kept as-is here (paired leads).

## 2026-07-17 (wave-2) — the 16 agenda-grade leads RESOLVED

Probed the Revize CMS council/PC minutes listings **and** the PMN notice attachments for all
16 flags. **Result: zero net-new minutes — every flag is a genuine agenda-only gap or a wrong-body
false positive. Nothing to promote; vote layer unchanged.**

- **Revize CMS** publishes budget-workshop / Truth-in-Taxation minutes **only from 2025 onward**
  (`25May13/25May27 Budget Workshop`, `25August7 Truth In Taxation`, `26May12/26May26 Budget
  Workshop`). No minutes file exists on Revize for any 2020–2024 workshop/TnT/special date, nor
  for the flagged PC dates (regular 1st/3rd-Tue council + 2nd/4th-Thu PC meetings are all present).
- **PMN** carries only AGENDAS / packets / notices / resolutions for these dates — no `(Meeting
  Minutes)`-type attachment. Three bare-date-named council files that *could* have been minutes were
  downloaded and **verified in-body** as posted meeting AGENDAS (signed in advance by the City
  Recorder), not minutes: `2020May26 Budget Workshop.pdf` (603115), `2022May24 Budget Workshop.pdf`
  (850774), `2024August1 Truth In Taxation Meeting.pdf` (1147986). Label was honest.
- **One wrong-body false positive:** 2022-06-30 / body 487 → attachment `LUAB Agenda 06-30-22.pdf`
  (865607) verified in-body as a **Land Use Appeal Board** meeting (LUAB 22-001 Evans Family
  Remodel), not a Planning Commission meeting. Repo tracks Council/RDA/PC only → not a PC gap.

Dispositions:
- **12 genuine council/RDA gaps** (9 dates, 3 with paired RDA) → `meeting_minutes/minutes_unrecovered.csv`
  (created this pass): 2020-05-26, 2020-09-10, 2020-10-13, 2021-05-11, 2021-05-25, 2022-05-10,
  2022-05-24, 2023-05-23, 2024-08-01.
- **3 genuine PC gaps** → `planning_commission/minutes_unrecovered.csv`: 2024-06-13, 2025-08-28,
  2025-11-18 (the last a General Plan Joint Workshop).
- **1 wrong-body false positive** → exception ledger only: 2022-06-30 (LUAB).
- All 16 appended to `pmn_exceptions.csv` (kinds `agenda_only` ×15, `other` ×1) so future
  crosscheck runs suppress them.

**Budget workshops / TnT / GP workshops are agenda-driven presentation+Q&A sessions that
historically produced no published minutes and (per the agendas) no formal roll-call votes — so
zero motions/votes would be recoverable even if minuted.** These are honest gaps, not extraction
misses.

**Follow-up (report-only):** the city clearly kept *some* record of the 2020 Council Interim
Appointment (candidate selected a new member) and the 2024-08-01 Truth-in-Taxation resolutions
(Res 24-24 / 24-25 adopted) — those adoption votes appear in a later regular-meeting minutes set if
at all. A GRAMA request to the Logan City Recorder is the only remaining channel for the
2020–2023 workshop / interim / TnT minutes themselves (draft text below).
