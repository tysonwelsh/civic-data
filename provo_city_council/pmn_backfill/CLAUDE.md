# pmn_backfill — build method, linkage, caveats

**Additive, separate dataset.** A per-date cross-check of this repo's Provo meeting-minutes
coverage against the Utah Public Notice website (PMN, `https://www.utah.gov/pmn/`), plus the
minutes/action-records PMN has that the repo lacked. Built by `expand-city-sources` SOURCE 4.
**Never modifies** the audited `meeting_minutes/` or `planning_commission/` layers — merge
deliberately if wanted. As-of **2026-07-03**.

## Layout
```
raw/                 390 PMN PDFs verbatim (+ _fetch_log.jsonl provenance) — all born-digital text
text/                pdftotext -layout sidecars, one per raw PDF
index.csv            390 rows — one per recovered PMN file
coverage.md          per-year repo vs PMN vs recovered vs still-missing (council + PC)
AVAILABILITY.md      what was checked, what exists, honest gaps
discovery/           crawl provenance: raw notice HTML, parsed.json, manifest, batch, coverage_data.json
CLAUDE.md            this file
```

## PMN body ids (confirmed, not guessed)
Discovery chain (GET-only): `list/entities.html?id=3&limit=2000` (govType 3 = Municipality)
→ Provo **entity id 244** → `list/publicBodies.html?id=244&limit=2000` (all 28 bodies + ids).
- **Provo Municipal Council = 1600** (matches recon)
- **Provo City Planning Commission = 1662**
- Redevelopment Agency Governing Board = 2318 (crawled for context; = Council-as-RDA, no unique gap)

## How the crawl worked (reproduce)
PMN's list view claims "only past 6 months," and historical *search* is POST/CSRF (can't
polite-GET). Escape hatch used: **`/pmn/list/notices.html?id=<body>&page=500` is cumulative** —
one GET returns the body's ENTIRE notice history. Parse `<tr>` rows → notice id, event date,
and each `/pmn/files/<FILE_ID>.pdf` attachment with its label. Provo's attachment labels are
**full filenames** (e.g. `Council Meeting - Minutes - 5-12-2026 …pdf`, `Item 1 ROA - PC
06.24.26.pdf`), NOT the parenthetical `(Meeting Minutes)`/`(Agenda)` labels the SKILL assumes —
categorize by filename keyword (`minute`→MINUTES, `summary`→SUMMARY, `roa`/`report of action`
→ROA, `agenda`, `packet`, `notice`).

## Cross-check method
Per-DATE set-difference (NOT per-year counts — PMN attaches minutes sporadically), ±4-day
tolerance for posted-vs-meeting-date offset, against `meeting_minutes/minutes_index.csv` (council)
and `planning_commission/minutes_index.csv` (PC). A PMN date with a minutes-equivalent
attachment not matched within ±4d of any repo date = a recovery candidate.

Minutes-equivalent = `Minutes`/`Summary` for council; `Report of Action` for PC (the PC's
official per-item action record — structured, vote-bearing: `On a vote of N:0 …`, `Motion By`,
`Votes in Favor of Motion: <names>`).

## Content verification (every candidate)
Each recovered file was verified after extraction: correct body-name header
(`Provo Municipal Council` / `Provo City Planning Commission`) + internal meeting date +
motion/vote or Report-of-Action structure. All 390 extracted as real text (0 scanned/OCR).
`screen_corpus.py`: 0 cid/mojibake/stub/dict/split-word outliers; the flags it did raise are
benign (2 byte-identical source re-posts; `ends_mid`/`repeated_line` are advisory formatting).

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,doc_kind,pmn_label`
— the §9 pmn_backfill contract + classification extras (`body`
∈ MunicipalCouncil/PlanningCommission; `doc_kind`; `pmn_label` = verbatim PMN filename).
- `path` is dataset-relative including `raw/` (validator requirement).
- `format` = `text` for all rows (born-digital); `extraction_method` = `pdftotext-layout`.
- `doc_kind` ∈ `minutes` (8 council), `roa` (381 PC action records), `roa_supporting`
  (1 code-section exhibit under an item label), `roa_duplicate` (2 byte-identical re-posts).
  Filter `roa_duplicate`/`roa_supporting` out before treating rows as distinct action records.
- **One row per PMN file.** For PC, a meeting date spans several per-item ROA rows (no single
  consolidated PC minutes doc exists on PMN, unlike the repo's 2025+ AgendaCenter PC minutes).

## Linkage to existing layers (if merged)
- Council rows join to `meeting_minutes/` by `date` (all 8 are special meetings — retreats/
  joint sessions — not on the regular-Tuesday grid; label them as such in any weekly view).
- PC rows join to `planning_commission/` by `date`. These are the **2020–2024 PC backlog** the
  repo documents as a source gap (`planning_commission/minutes_unrecovered.csv`); the ROA text
  carries the same recommendation-vs-final-action + roll-call structure the 2025+ PC minutes do.
  **INTEGRATED 2026-07-10:** `planning_commission/extract_roa_votes.py` now parses these ROAs
  (grouped by date) into the structured `all_votes.csv` with `provenance='pmn_roa'`, writing the
  concatenated per-meeting source to `pmn_backfill/roa/<date>_pc-roa.md`. The recovered PC record
  (2020-2024) is therefore live in `db/civic.db` + `cities.db`; re-run that script after any
  pmn_backfill PC refresh. (Council `minutes` rows here remain un-merged — still special/joint
  sessions off the regular grid.)

## Reproduce
```
# discovery
polite_fetch.py "https://www.utah.gov/pmn/list/entities.html?id=3&limit=2000"   # -> Provo entity 244
polite_fetch.py "https://www.utah.gov/pmn/list/publicBodies.html?id=244&limit=2000"  # -> body ids
for b in 1600 1662 2318; do polite_fetch.py "https://www.utah.gov/pmn/list/notices.html?id=$b&page=500"; done
# fetch recoveries (batch of /pmn/files/<fid>.pdf), extract pdftotext -layout, screen_corpus.py
```
Retrieval clock was frozen with `--now 2026-07-03T00:00:00Z`.

## 2026-07-17 — final PMN-crosscheck flag verification (3 flags -> 3, all leads)

Verified all 3; 0 exceptions (all genuine); re-run (--cached) 3 -> **3**.
- **Recovery leads (3):** 2024-07-23 (body 1600) Joint Meeting with Provo Library Board —
  a real minutes .docx exists (filename 7-23-2024), repo has 07-16 regular+work but not 07-23
  — STRONG lead; 2023-04-27 Joint Meeting with Provo School District (agenda-grade);
  2023-10-11 Joint Meeting with Planning Commission (agenda-grade). All are Municipal Council
  joint meetings the OnBase harvest lacks.


## 2026-07-17 — crosscheck-lead disposition (1 promoted, 2 agenda-only)

- **2024-07-23 Joint Meeting with Provo Library Board — PROMOTED** into `meeting_minutes/`
  (minutes .docx, file 1220417, notice 928386). SCOPE-CHECKED: header is 'PROVO MUNICIPAL
  COUNCIL / Joint Meeting with Provo Library Board Minutes', roll call is the Council + Mayor
  (Council Chair MacKay conducting) — a noticed Provo Council meeting conducting Provo business
  (library governance/funding), NOT the Library Board's own meeting. It is presentation-only
  (Items 1-4) and records NO motion → 0 vote rows (honest; the meeting held no votes).
  source=pmn/format=text; raw+text catalogued here (doc_kind=minutes).
- **2023-04-27 (Joint w/ Provo School District) & 2023-10-11 (Joint w/ Planning Commission) —
  NOT promoted (agenda-only).** Notices 828467 / 863095 carry ONLY agenda PDFs, no minutes.
  Honest gaps; reported. (The 2023-10-11 PC-joint question is moot — no minutes doc exists.)
