# pmn_backfill/ — South Salt Lake gap-recovery dataset

Additive `expand-city-sources` **source 4 (PMN backfill)** dataset for South Salt Lake. Built
2026-07-13. ✅ **PROMOTED 2026-07-16:** 119 of the 130 recoveries were verified and merged into
the audited `meeting_minutes/` + `planning_commission/` layers by **`promote_to_audited.py`**
(this directory) — FULL promotion (markdown + raw + index rows, `source=agendacenter`,
`provenance=agendacenter_minutes` in all_votes.csv), not just a vote merge. The script embeds
the content-verified body/kind classification (portal labels were wrong for ~45 docs — most
"WM"-labelled council files are REGULAR-meeting minutes; 2025-02-12's "RDA" file is council)
and the 11 REJECTS (2 agenda packets, 9 content-duplicates of audited meetings) with reasons.
This dataset remains the recovery-provenance record; its `index.csv` still describes the
RECOVERY (original slot labels/kinds), not the promoted classification — plus the
machine-readable verification that the rest of the coverage cliff is real.

## Headline
For South Salt Lake, source 4 is mostly **verification + an independent-source probe** (the core
minutes already came FROM PMN). Two results:
1. **The PMN cliff is real** — a full filename+content re-sweep of every SSL PMN body confirms the
   core missed no in-scope recorded minutes on Utah Public Notice (the only PMN minutes it skipped
   are 2014–2017, before the 2020 floor; the `>22 MB`-capped council/RDA files are genuine agendas;
   the capped PC files were already recovered).
2. **The cliff is partly fillable from the city's own AgendaCenter** — the hidden
   `ArchivedMinutes` slot (via each doc's `PreviousVersions` page) holds genuine recorded
   roll-call minutes even when the visible `Minutes` slot serves the agenda packet. **130 recorded
   minutes (2022–2026) recovered**, filling 104 of the core's agenda-only dates + adding 26 dates
   the core never listed (incl. 9 **2022 PC** minutes → refutes "PC minutes begin 2023-01-19").

Read `coverage.md` for the quantified matrix and `AVAILABILITY.md` for what was checked.

## Layout
```
raw/<year>/<slug>_<viewid>.pdf   retained AgendaCenter minutes PDFs (verbatim) + _fetch_log.jsonl
text/<slug>.txt                  pdftotext -layout sidecar, trimmed to the minutes header
index.csv                        SCHEMA_SPEC §9 pmn_backfill contract + recovery_source
coverage.md / AVAILABILITY.md    the coverage story + what-was-checked
work/                            build + verification scripts and their JSON outputs (provenance)
```

## index.csv schema
SCHEMA_SPEC §9 `pmn_backfill` contract header exactly, then one extra column:
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method` **+ `recovery_source`**.
- `source` = `agendacenter` (recoveries are from the city portal, not PMN); `notice_url`,
  `pmn_body_id`, `pmn_file_id` are **blank by design** (not a PMN attachment).
- `source_url` = `https://sslc.gov/AgendaCenter/ViewFile/{ArchivedMinutes|Minutes}/_<MMDDYYYY>-<id>`.
- `body` ∈ Council / RDA / PlanningCommission; `slug` = `<date>_<council|rda|pc>_<kind>`
  (`kind` ∈ RC/WM/SM/PC/BoC, detected from the document header).
- `format=text` (born-digital), `extraction_method=pdftotext -layout`.
- `recovery_source` ∈ `agendacenter_archivedminutes` (113) / `agendacenter_minutes` (17).

## How the recovery works (the SSL ballgame)
The AgendaCenter listing exposes only `Agenda` + `Minutes` slots; the `Minutes` slot is usually the
**agenda packet** (recon-verified). The **recorded minutes hide in `ArchivedMinutes`**, a previous
version of the Minutes doc. `work/ssl_agendacenter_sweep.py`:
- `--enumerate`: parse the saved live listings for every `Minutes` doc, GET each doc's
  `…/AgendaCenter/PreviousVersions/_<date>-<id>`, collect `ArchivedMinutes` ids → `ac_candidates.json`.
- `--check`: download each candidate (HEAD-skip `Minutes` packets `>12 MB`; always fetch
  `ArchivedMinutes`), `pdftotext -layout`, and **content-detect** recorded-minutes grammar
  (`Roll Call Vote:` / `Voice Vote:`, or `MINUTES OF MEETING HELD` + motion, or MEMBERS-PRESENT +
  motion without an agenda banner). Resumable via `ac_results.jsonl`. → `ac_results.json`.
`build_backfill.py` consolidates the genuine-minutes hits, classifies body+kind, dedups to one file
per `(date,body,kind)` (preferring the version with the most recorded-vote content, then the pure
`ArchivedMinutes` doc), keeps only rows **not already** in `meeting_minutes/`+`planning_commission/`
indexes, copies raw → `raw/`, writes trimmed `text/` sidecars, and emits `index.csv`.

Content-detection is mandatory: an SSL "Minutes"-labelled file is frequently an agenda. Every
recovered file was verified to contain real recorded votes (council/RDA `Name: Yes/No` roll calls;
PC `Commissioner <Name> – Aye` / "the vote was unanimous"). Corpus screen: **CLEAN**.

## Verification scripts (work/)
- `ssl_pmn_crawl.py` → `ssl_pmn_all_attachments.json` — every attachment on every SSL PMN body.
- `ssl_check_capped.py` — content-checks the `>22 MB` PMN files the core's size cap skipped
  (result: council/RDA all agendas; PC all already-recovered).
- `ssl_agendacenter_sweep.py` — the AgendaCenter enumerate+check described above.
- JSON outputs are retained as provenance; the bulky PDF download caches were deleted after the
  raws were copied into `raw/` (re-derivable by re-running).

## Linkage / how to use
Rows join to the existing datasets by `date` + `body` (+ `kind` — but note the audited layer's
kind is the CONTENT-verified one, which differs from this index's slot-label kind for ~45 docs;
`promote_to_audited.py` holds the mapping). **The promotion happened 2026-07-16**: the audited
copies live under each dataset's `minutes/` with `source=agendacenter`, and their votes are in
all_votes.csv with `provenance=agendacenter_minutes`. Treat THIS dataset as the read-only
recovery record; analysis should use the audited layers. Re-running `promote_to_audited.py` is
idempotent (already-indexed slugs are skipped).

## PMN cross-check verification — 2026-07-17
`scripts/pmn_crosscheck.py south_salt_lake` emitted **122 flags** (77 `missing_minutes`,
45 `agenda_only_gap`; 0 count_mismatch/new_body). Flag-verification pass (READ-ONLY vs
datasets; only `pmn_exceptions.csv` written):

- **Bucket crosswalk vs COVERAGE.md residual + `minutes_unrecovered.csv`:** bucket (a)
  documented-residual = 108 (75 council/RDA `missing_minutes`, all `known_unrecovered`,
  "Meeting Minutes"-slot short-form `YYYY.M.D RC/WM/RDA.pdf`; 33 PC 2020-2021
  `agenda_only_gap` = the genuinely-unpublished PC gap); bucket (b) not-in-ledger = 14
  (12 PC 2022 `agenda_only_gap` — PC `minutes_unrecovered.csv` starts 2023 — + 2 PC
  `missing_minutes` carrying SSL's `_Final` recorded-minutes naming); bucket (c) = 0.
- **Content sample (15 docs, ≥12 required), all AGENDA/agenda-packet — pathology
  CONFIRMED, 0 real minutes in bucket (a):** 2020-01-08 RC (20MB packet), 2020-01-08 RDA,
  2020-03-23 SM, 2021-06-09 RC, 2021-11-16 BoC, 2022-03-23 RDA, 2022-08-09 TT, 2022-12-14
  WM (18MB packet), **2023-02-22 "RC Minutes.pdf"/"WM Minutes.pdf" → content is "AMENDED
  REGULAR MEETING AGENDA"** (the filename-lies case), 2023-03-22 RC, 2023-12-06 BoC,
  2024-08-21 SM, 2024-09-11 "Work Meeting Agenda"; + PC agendas 2022-12-01, 2020-01-10.
- **Recovery leads: 1.** **2024-07-18 PC** (PMN file 1152427, notice 927292) is a GENUINE
  recorded-minutes doc the repo lacks — "Planning Commission Regular Meeting Minutes...
  no meeting held, no quorum" (0 motions; re-noticed to 2024-08-01). Content-detection keyed
  on vote grammar missed it (no votes), so the backfill logged it agenda-only. This
  contradicts this dataset's headline claim that the PMN re-sweep "missed no in-scope
  recorded minutes on PMN" — one no-quorum minutes record slipped through. Left un-suppressed
  so it re-surfaces for the review gate.
- **The other `_Final` candidate is NOT minutes:** 2025-12-04 PC (file 1378255) is named
  `…Mtg_Final_.pdf` but is a 136-page/57MB WORK MEETING agenda packet (page-1 verified).
- **Exceptions written: 121** — 76 `not_minutes` (agenda/packet in the Meeting-Minutes slot,
  incl. 2024-08-21 & 2025-12-04 PC) + 45 `other` (PC agenda/notice-only dates, no minutes on
  any channel).
- **Re-run** `python3 scripts/pmn_crosscheck.py south_salt_lake --cached` → **1 flag
  (the 2024-07-18 lead), 121 suppressed, 9 pending-adoption.**

## Rules honored
Additive only; every raw retained (`raw/` + `_fetch_log.jsonl` with per-file sha256); §9 contract
header (validated — `expand-city-sources/scripts/validate_dataset.py` PASSES); no fabrication (the
216 residual agenda-only dates stay honest gaps); polite GET-only fetching. Parent `README.md` /
`CLAUDE.md`, `sources.csv`, `cities.db`, `coverage.json`, `TODO.md` were **not** modified.
