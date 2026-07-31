# pmn_backfill/ — build method + linkage (Emigration Canyon)

Source 4 (Utah Public Notice backfill) of `/expand-city-sources`. **Additive + separate:**
nothing in `meeting_minutes/` or `planning_commission/` was modified. Read `coverage.md`
(the findings) and `AVAILABILITY.md` (the gaps) first; this file is the how.

## What this dataset is
Emigration Canyon has no city CMS — PMN is the canonical minutes source and the audited
datasets were already built from a full PMN harvest. This run **re-verifies** that harvest
and captures anything it missed. Net result: **1 recovered minutes doc** (PC 2025-11-13,
posted late) + machine-readable proof that (i) the MSD AgendaCenter holds no EC minutes,
(ii) the pre-2018-10 purge is genuine, (iii) the two 0-motion scans have no born-digital
twin. See `index.csv` for the recovered row. **PROMOTED 2026-07-16:** the recovered doc now
also lives in the audited `planning_commission/` layer (index `format=ocr`,
`provenance=pmn_minutes`, +2 motions; its `minutes_unrecovered.csv` row dropped) — this
dataset retains the recovery record + raw/text as acquired.

## `index.csv` schema
SCHEMA_SPEC.md §9 `pmn_backfill` contract header, in order:
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`
then one city extra: **`recovery_source`** (`pmn` | `msd_agendacenter`) — the avenue the
doc was recovered from. `path` is dataset-relative including `raw/`. `format` uses the §9
vocab (`scanned`, not the repo's `ocr` label) so `validate_dataset.py` passes;
`extraction_method` carries `ocr`.

## Bodies / ids
Entity **1317**; bodies **5809** Council, **1562** PC (the only two). Doc store
`https://www.utah.gov/pmn/files/<id>.pdf`; notice pages `/pmn/sitemap/notice/<id>.html`.
Exclude *Emigration Improvement District* (entity 524).

## Method (all crawlers in `_scripts/`, GET-only, ~0.6–0.8 s/host)
1. **`ec_pmn_sweep.py`** — walks `/pmn/list/notices.html?id=<body>&page=N` (cumulative)
   until the notice set stops growing, opens each notice, classifies every attachment
   (minutes / agenda / audio / cancelled / packet / other) and HEAD-probes each
   minutes-labeled file for liveness → `ec_pmn_sweep_<body>.csv`.
2. **`ec_pc_date_recon.py`** — for each LIVE PC minutes file whose id is not already a repo
   file-id, downloads it, reads the meeting date from the PDF body (pdftotext, OCR
   fallback), and buckets DUP (date already in the index) / RECOVERY (date in
   `minutes_unrecovered.csv`) / NEW → `ec_pc_recovery_candidates.csv`. This is how the
   2025-11-13 recovery was isolated from 44 duplicate re-uploads. (Council was checked the
   same way inline — all 14 non-repo live minutes were DUP.)
3. **`ec_msd_enumerate.py`** — the MSD CivicPlus AgendaCenter `ViewFile` endpoint keys only
   on the trailing numeric MID (date prefix ignored), so it sweeps MID 1–195
   (`/AgendaCenter/ViewFile/{Minutes,Agenda}/<MID>`), extracts each doc's body/date →
   `ec_msd_catalog.csv`. Proves no EC council/PC docs are there.

## Extraction of the recovered doc
`raw/2025/2025-11-13_PlanningCommission_Regular_pmn_1363983.pdf` is image-only (7 pp, 0
extractable chars) → `pdftoppm -r 200` + `tesseract` per page →
`text/2025-11-13_PlanningCommission_pmn_1363983.txt` (14 KB). Raw retained verbatim;
`raw/2025/_fetch_log.jsonl` carries url/status/bytes/sha256 from `polite_fetch.py`. OCR
text preserved as-produced (no LLM cleanup). `screen_corpus.py` on `text/` is clean (only
the advisory "ends mid-sentence"; dict_ratio 0.79 — normal for a clean scan OCR).

## Linkage
The recovered PC 2025-11-13 row corresponds to the `planning_commission/minutes_unrecovered.csv`
entry of the same date (agenda notice 1032655; the late-posted minutes file itself rode
notice 1040893). **DONE 2026-07-16:** promoted into `planning_commission/` —
`minutes/2025/2025-11-13/…_1363983.md` (`format=ocr`), raw PDF copied to
`planning_commission/raw/2025/`, unrecovered row dropped, `extract_votes.py --force` +
`validate_votes.py` re-run (PASS; +2 tally-only motions, `provenance=pmn_minutes` via the
new trailing 14th column), derived layers rebuilt. The doc is a scan — the OCR-quality
caveat the parent CLAUDE notes for image-only minutes applies (e.g. the clerk's "2nd by:"
seconder label OCR'd as "2™4 by:" and is not parsed — seconders stay honestly blank).

## Re-running
Idempotent and read-only against PMN/MSD. `validate_dataset.py <this dir>` must PASS.
Do NOT edit the audited layers, `sources.csv`, `cities.db`, or parent docs from here.


## 2026-07-17 — PMN cross-check flag verification (26 flags -> 24)
Verified every crosscheck_flags row against cache + repo indexes; 2 exceptions added.
PMN is EC's ONLY source, so a PMN-noticed meeting missing from the repo is a strong lead.
- **Exceptions (2):** 'Land Use Hearing Officer' (Walsh Appeal 2019-03-06) foreign
  quasi-judicial body riding PC(1562); 'Unified Fire Authority - Notice of Public
  Hearing' (2025-02-18) foreign entity notice under Council(5809) -> both kind=other.
- **Recovery leads (20), remain flagged:**
  - 3 missing_minutes = actual council [Meeting Minutes] PDFs the repo lacks, filename
    date == event date: 2021-01-28 (n654183), 2021-02-25 (n660423), 2023-01-24 (n808281,
    .docx). HIGH value (PMN is the only source).
  - 17 agenda_only: heavy 2020 COVID council cluster (2020-05-28, 06-18, 06-25, 07-16,
    08-27, 09-24, 10-12, 10-29, 11-10 — repo council 2020 has only 04-23 + 11-17; some
    audio-backed, four are bare notices), plus 2019-07-25, 2021-03-25, 2021-04-20,
    2023-04-19, 2023-09-26, 2024-12-17, 2025-08-20 & 2026-02-23 (specials). All
    agenda/audio-grade — meeting held, minutes may not exist anywhere (EC narrative-tally).
- **Hardening candidate (4 residual flags):** filename-date-rescue — 2023-02-16 (attaches
  Dec + Jan12 PC minutes, both in repo; the 02-16 mtg is audio-only & correctly stays in
  minutes_unrecovered), 2024-05-28 (03-26-24 minutes, in repo), 2024-08-27 (02-22 + 04-23
  drafts, in repo), 2025-09-23 (08-26 draft in repo + an explicit "No Minutes" agenda).
  The engine's ku=yes "recovery lead" note on these is a FALSE POSITIVE.
- Re-run (`--cached`): **24 flags** (17 agenda_only + 7 missing_minutes), 2 suppressed.

## 2026-07-17 — 3 council missing_minutes leads RECOVERED + PROMOTED
The 3 township-era council `missing_minutes` leads above were fetched, content-verified, and
**promoted directly into the audited `meeting_minutes/` layer** (not staged here — the EC-PC
precedent: EC has no CMS, so PMN recoveries go straight into the audited PMN-sourced layer,
`provenance=pmn_minutes`):
- **2021-01-28** (file 692675) — real minutes; header year-typo "2020" (true date confirmed
  by the Dec-17-2020-minutes approval motion + notice + Thursday weekday). 1 motion.
- **2021-02-25** (file 717575) — real minutes; 6 motions incl. a NEW contested 4-1 (Bowen Nay).
- **2023-01-24** (docx file 950381) — real minutes; the notice's PDF twin (935045) is the
  AGENDA (rejected). 1 motion. Fetch the `.docx` with a `.docx` URL (the `.pdf` URL 404s).
Net into `meeting_minutes/all_votes.csv`: **+8 vote rows** (motions 288→296, contested 5→6);
provenance column added. See `../meeting_minutes/CLAUDE.md`. These docs' raw/text live in the
audited `meeting_minutes/raw/` — NOT duplicated into this dataset (which keeps its Source-4
re-verification scope: the 1 PC 2025-11-13 recovery). Remaining missing_minutes leads: the PC
2023-02-16 (audio-only, correctly unrecovered) + council 2025-09-23 (DRAFT + a No-Minutes
agenda) stay flagged / genuine gaps.
