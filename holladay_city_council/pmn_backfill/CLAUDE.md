# pmn_backfill/ — Holladay (source 4 of expand-city-sources)

Additive PMN backfill + independent-source recovery for the **Planning Commission
2020/2021/2023 minutes gap**. Built read-only (2026-07-14); **the 27 recovered PC minutes
were PROMOTED into the audited `planning_commission/` layer on 2026-07-16**
(`planning_commission/promote_backfill_minutes.py` — md + raw copies there carry the
`_wayback` suffix, index rows `source=wayback`, vote rows `provenance=wayback_minutes`;
the originals here are retained verbatim and remain the recovery-provenance record).
Start with `coverage.md` (the numbers) and `AVAILABILITY.md` (what was checked / not found).

## Why this dataset exists
Holladay's audited minutes came **from PMN** (council body 388, PC body 389), so PMN is a
superset-verify here, not a new-minutes source. The single real upstream gap: PMN never posted
the **2020, 2021, 2023 Planning Commission minutes** (agendas/packets only). This dataset
confirms that at source via a full 16-body PMN sweep, and recovers what it can of the PC gap
from the city's own channels.

## Entity + body ids (PMN, entity Holladay = 160)
Minutes-bearing: **388 City Council**, **389 Planning Commission**, **791 RDA**. Swept but
minutes-free (agendas/packets/notices only): 390 Board of Adjustments, 392 Design Review Board,
4813 Administrative Appeals, 4823 Arts Council, 6055 Historical Commission, 6211 Tree Committee,
2398 Housing Task Force, 391 Education Task Force, 7341 Adopted Ordinances, 6605 Bids & RFPs,
8423 Elections, 9191 Elections/Board of Canvassers, 9331 LBA (LBA minutes are in-session, tagged
from council docs — none stand alone on PMN).

## Sweep result (see coverage.md for the table)
- **Council 388** — repo is a complete **superset** for 2020+ (PMN adds nothing in-window;
  120 pre-2020 council minutes exist below the floor).
- **PC 389** — gap **confirmed**: PMN minutes only 2022 + 2024–2026 (all already in repo);
  **zero** 2020/2021/2023 minutes.
- **RDA 791** — no gap; the 5 in-floor standalone RDA minutes are already `body=RDA` docs.

## Recovery — 27 PC minutes (2020 H1 + 2021 H1)
Source: the city's former WordPress site `cityofholladay.com/file/<yr>/<mo>/<MMDDYY>-PC-Mtg.pdf`,
retrieved through the **Wayback Machine** (`web.archive.org/web/<ts>id_/<url>`; `polite_fetch.py`
only — `WebFetch` cannot reach Wayback). SuiteOne is 2025+ only; the live Revize Document Center
does not expose older filenames (403 folder listings). All 27 are born-digital
(`pdftotext -layout`, no OCR), header-verified Holladay PC, and **keyed on the internal meeting
date** printed in the PDF — not the filename.

## Build / files
- `raw/pc_<date>_minutes.pdf` (27) + `raw/_fetch_log.jsonl` (sha256/status/bytes per fetch).
- `text/pc_<date>_minutes.txt` — `pdftotext -layout` sidecars. Corpus screen **CLEAN**
  (0 stubs, 0 mojibake/PUA/cid, 0 dict/split-word outliers; the initial `duplicate_bodies`
  flag led to catching the 2020-04-07 mislabel, now removed).
- `index.csv` — §9 `pmn_backfill` contract header
  (`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,`
  `retrieved_date,format,extraction_method`) + two extension columns **`recovery_source`**
  (pmn / suiteone / revize-wordpress-via-wayback) and **`wayback_url`** (the exact snapshot).
  `source=wayback`, `source_url`=the original city URL, `pmn_body_id=389`, `pmn_file_id` blank
  (not from PMN), `format=text`, `extraction_method=pdftotext-layout`.
- `unrecovered.csv` — the **35 still-missing** PC dates with per-date reason + channels checked.
- `hol_pmn_sweep.py` — the sweep parser (reads `_disc/notices_<body>.html`, emits the
  attachment inventory). `_disc/` holds the fetched notice-list HTML + working JSON (throwaway
  discovery cache; the durable provenance is `raw/_fetch_log.jsonl` + `index.csv`).
- `_out_of_scope/` — two retained-but-not-indexed raws (a mislabeled 04-07 dup = the 06-16
  minutes; a Council retreat already covered by the audited council layer). See AVAILABILITY.md.

## Cardinal rules honored
Never fabricated; every gap is logged (`unrecovered.csv`). Raws retained verbatim. Source-faithful
(the 04-07 upload error and the mislabeled Council retreat are documented, not silently dropped or
"fixed"). The original 2026-07-14 build did not touch the audited layers; the 2026-07-16
promotion (see header) moved verified copies into `planning_commission/` with full Wayback
provenance and refreshed the city docs — `cities.db`/`coverage.json` re-federation is the
orchestrator's step.

## 2026-07-17 — final PMN-crosscheck flag verification (3 flags -> 1)

Verified all 3 (fetched the reschedule notice); appended 2 exceptions; re-run (--cached) 3 -> **1**.
- **Recovery lead (1, agenda-grade):** PC 2021-06-30 Planning Commission Meeting/Training (body 389).
- **Exceptions (other x2):** 2023-12-05 'Notice of Potential Quorum' (non-meeting admin notice);
  2026-03-17 PC 'RESCHEDULED' to 2026-03-24 (Caucus Night conflict) — the 2026-03-24 minutes are
  held in repo; no meeting occurred 2026-03-17.
