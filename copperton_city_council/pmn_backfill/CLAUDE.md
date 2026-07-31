# pmn_backfill/ — Copperton (Source 4: Utah Public Notice)

Additive, **review-only** sweep of **Utah Public Notice (PMN)** for minutes absent from the
audited `meeting_minutes/` / `planning_commission/` layers. **Never merged in place.** Built
2026-07-14 per `/expand-city-sources` Source 4.

## Result: 0 gap-fill recoveries — the repo is a COMPLETE SUPERSET of PMN

Both Copperton PMN bodies are already fully represented in the audited layer:

| body | PMN minutes dates | in repo | recovered |
|---|---|---|---|
| **Council** (5831) | 32 | 106 docs (superset) | **0** |
| **Planning Commission** (1560) | 17 real (+1 false pos.) | 17 (superset) | **0** |

The one tangible new artifact is **1 OCR-upgrade LEAD** — see below. This mirrors Magna's
PC finding (complete superset) but here it holds for *both* bodies.

## Files
- `index.csv` — §9 `pmn_backfill` contract header
  (`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,
  retrieved_date,format,extraction_method`) + extras `recovery_source,orig_filename,text_path`
  (matching `magna_city_council/pmn_backfill`). **One row**: the 2025-10-15 OCR-upgrade lead
  (`recovery_source=pmn_ocr_upgrade_lead`). `path`/`text_path` are dataset-relative.
- `raw/` — the one lead PDF verbatim + `_fetch_log.jsonl` (url, bytes, sha256, retrieved_utc)
  from `polite_fetch.py`. Never delete/normalize.
- `text/` — the lead's `pdftotext-layout` sidecar.
- `coverage.md` — full per-body accounting + purge re-confirmation + the minor-gap check +
  the 15-date OCR-upgrade evaluation table.
- `AVAILABILITY.md` — what was checked / exists / stays a gap, as-of date.
- `work/` — intermediate fetched HTML + parsed JSON (re-derivable provenance), and
  `work/probes_ocr/` = the 8 verified-NEGATIVE OCR-upgrade candidate PDFs (duplicate scans,
  not dataset artifacts; kept for the record with their fetch log).
- Helper scripts (this dir, unique-named — never in the shared scratchpad):
  - `copperton_pmn_crawl.py` — cumulative notices-list crawler + attachment parser (per body).
  - `copperton_pmn_setdiff.py` — per-date set-difference of PMN minutes vs the repo indexes
    (filename-date extraction incl. 2-digit-year; ±4d tolerance; separates the logged purge
    gap from genuine misses).
  - `copperton_pmn_buildindex.py` — writes `index.csv` (the single OCR-upgrade lead row).

## The one OCR-upgrade LEAD (2025-10-15) — NOT swapped

`raw/2025-10-15__council__1353103__pmn-borndigital-ocr-upgrade-lead.pdf` is the **DRAFT**
minutes of the 2025-10-15 council meeting, posted on PMN body 5831 (attached to the
2025-11-19 approval notice 1038579). It is **born-digital clean text** (16,436 chars). The
repo currently holds 2025-10-15 only as a **GoDaddy RICOH scan** (`format=ocr`). So the PMN
draft is a clean-text LEAD for improving that date's extraction — but it is the *draft*, not
the approved copy, so it is **cataloged, not swapped**. Promotion (or a vision re-read of the
approved scan) is a deliberate future task.

Every other repo OCR date was evaluated (see `coverage.md`): 6 have no distinct PMN copy or
the PMN copy IS the repo source (same scan); 8 have a PMN copy that is **also scanned** (incl.
the 2024-10-16 / 2026-04-15 "born-digital attachments over a scanned minutes body" trap —
the Magna-2026-03-10 pattern). Only 2025-10-15 is genuinely born-digital.

## PMN discovery (for a future refresh)
- Entity: Copperton = **1353** (govType 3). Bodies: Council **5831**, PC **1560** — the only
  two; **no CRA/RDA**. Decoy (govType 5): **Copperton Improvement District = entity 482**
  (bodies 2497/3013) — water district, **exclude**.
- Crawl each body with cumulative `notices.html?id=<body>&page=500` (one GET = full history;
  the "past 6 months" banner is boilerplate). Minutes usually attach to a LATER meeting's
  approval notice → parse the meeting date from the **filename** (`MM-DD-YYYY` or 2-digit
  `MM-DD-YY`), falling back to the notice event date. **PMN type labels are unreliable** (the
  2025-07-02 "May minutes.pdf" was labeled "Meeting Minutes" but is the May-13 meeting).
- Fetch files from **`https://www.utah.gov/pmn/files/<id>.pdf`** — not `pmn.utah.gov`.

## Verification results (detail in coverage.md)
- **Council 5831 & PC 1560 supersets CONFIRMED** — 0 recoverable minutes missing from either.
- **2017-02 → 2018-06 purge RE-CONFIRMED genuine** — 9 purge-era file-IDs sampled across the
  full window all 404 (315-byte stub); 3 controls 200. `minutes_unrecovered.csv` stands.
- **Minor gaps (Sep-2025 / Dec-2025 / June-2026) RE-CONFIRMED unfillable** — PMN notices
  exist, minutes documents do not.
- **Corpus screen** (`audit-city-data/scripts/screen_corpus.py text`): 0 dict/split/weird
  outliers on the one sidecar (repeated-line / ends-mid flags are advisory).

## Rules honored
Additive only; existing datasets untouched; raws retained; nothing fabricated (both the
council purge gap and the minor 2025/2026 gaps stay gaps; the OCR lead is a lead, not a
swap); polite GET-only. Parent `README.md`/`CLAUDE.md`, `sources.csv`, `cities.db`,
`coverage.json`, `TODO.md` are owned by the orchestrator — not edited here.

## 2026-07-17 — final PMN-crosscheck flag verification (8 flags -> 6)

Verified all 8 against the 2017 floor / 2017-02..2018-06 purge gap; appended 2 exceptions;
re-run (--cached) 8 -> **6**.
- **Recovery leads (6, agenda-grade, all post-purge):** council 2018-10-17, 2018-12-19 (public
  hearing), 2023-10-03, 2024-11-20, 2024-12-06 (public hearing), 2025-12-09 (special meeting).
- **Exceptions:** other x1 (2022-01-11 PC CANCELLED — 'no agenda items', cancellation carried
  in attachment 220111_CoppertonPC_Cancelled.pdf); wrong_date x1 (2025-12-17 '11-19-2025 ...
  DRAFT.pdf' = draft of already-held 2025-11-19 APPROVED council minutes — filename-date rescue).

## 2026-07-17 (wave2) — the 6 recovery leads VERIFIED: 0 recoveries, all DEAD (honest gaps)

Fresh re-crawl of council body 5831 (207 notices, through 2026-07-15) + direct probe of the
GoDaddy town-site year pages (2023/2024/2025 `-agendas-%26-minutes` — download links use the
nested `blobby/go/07a53a68…/downloads/<uuid>/<filename>` pattern). **No minutes document exists on
either portal for any of the 6 dates.** Each meeting/hearing genuinely occurred (PMN notice; audio
for 3 of them) but its minutes were never published — the ~800-pop town's honest publication
ceiling, not a harvest miss. All 6 promoted to `meeting_minutes/minutes_unrecovered.csv`
(2018-10-17, 2018-12-19, 2023-10-03, 2024-11-20, 2024-12-06, 2025-12-09); per-date disposition in
`crosscheck_flags.csv` (all `known_unrecovered=yes`) and the table in `crosscheck_report.md`.
Nature: 3 regular 3rd-Wed council meetings (2 audio-only, pre-GoDaddy 2018 era), 1 Metro Township
worksession, 1 standalone public hearing, 1 special meeting (Rio Tinto donation). No votes were
recoverable. GRAMA text for the town recorder drafted in the wave report (owner-gated).
