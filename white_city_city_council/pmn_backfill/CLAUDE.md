# White City — `pmn_backfill/` (Utah Public Notice recovery)

Additive dataset (source type 4 of `/expand-city-sources`) recovering minutes from Utah
Public Notice (`utah.gov/pmn`) that the audited layers miss. **Never modifies
`meeting_minutes/`, `planning_commission/`, or any other dataset** — it is a separate,
review-then-merge staging area. Built 2026-07-13.

## Why this dataset matters for White City
1. **It lights up the empty Planning Commission dataset.** `planning_commission/` in the
   core repo is header-only (honest empty — White City's Streamline site publishes no PC
   minutes). But **PMN body 5879 (White City Planning Commission) carries a real PC minutes
   series** — 22 meetings recovered here (2019–2025), the first PC roll-call/recommendation
   content in the repo. These are `body=PlanningCommission` rows.
2. It fills 5 genuine **council** minutes gaps (2019–2023) and documents the
   **unrecoverable 2017 council year** (PMN blob purge).

## Layout
- `raw/` — every fetched PDF verbatim + `_fetch_log.jsonl` (polite_fetch provenance).
  Draft duplicates of an already-approved meeting are kept as `*_draft.pdf` (retained, not
  separately indexed).
- `text/` — `pdftotext -layout` sidecars (one OCR'd — see below). Screened with
  `screen_corpus.py`.
- `index.csv` — the SCHEMA_SPEC §9 `pmn_backfill` contract header
  (`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,
  retrieved_date,format,extraction_method`) + extras `recovery_source,doc_type,text_path`.
- `unrecovered.csv` — meetings PMN proves happened but whose minutes files 404 (purged).
- `coverage.md` / `AVAILABILITY.md` — coverage tables + what was checked.
- `_disco/` — retained discovery artifacts (entity/body/notice-list HTML, batch manifests).
- `wc_pmn_parse.py` — the notice-list HTML parser (unique-named helper for this dataset).

## Bodies + method
- PMN entity **1325 = White City**; bodies **5805 = Council**, **5879 = Planning
  Commission**. Decoys excluded: entity 840 (Water Improvement District), 1345 (Greater SL
  MSD). Full history via the cumulative `notices.html?id=<body>&page=300` GET.
- **Council cross-check:** per-DATE set-difference of PMN "Meeting Minutes" attachments vs
  `../meeting_minutes/minutes_index.csv`. Meeting date is parsed from the **filename**
  (`MM-DD-YY`), not the notice event date (minutes are often posted under the *next*
  meeting's notice). Recovered only dates absent from the repo.
- **PC recovery:** all of body 5879's minutes-labeled attachments (net-new; core PC is
  empty). "Month minutes.pdf" files are **drafts** presented for approval at a later
  meeting — their true meeting date was read from the document body; each is a duplicate of
  an `…MinutesApproved.pdf` for the same date, so indexed once (approved variant) with the
  draft retained in `raw/`.
- **GPSC:** `WC GPSC MeetingReport …` files are General Plan Steering Committee summaries
  (a General-Plan drafting sub-body, no roll-call motions) → `body=GPSC`,
  `doc_type=meeting_report`. Kept distinct from PC minutes so PC counts are not inflated.

## `body` values here
`Council` (5), `PlanningCommission` (22), `GPSC` (4). This is the ONLY place in the repo
where a `PlanningCommission` White City row exists.

## Extraction / quality
- 30/31 born-digital → `pdftotext -layout`. One GPSC report (2021-02-23, file 690347) had a
  **corrupt embedded text layer** (pdftotext/pymupdf returned garbage); recovered by
  **tesseract OCR** → `format=scanned`, `extraction_method=ocr (tesseract; embedded text
  layer corrupt)`. All other rows `format=text`.
- `screen_corpus.py` outliers are benign: minutes ending mid-sentence (advisory) and
  weird-char flags from the MSD letterhead bullets/en-dashes; the one real anomaly (690347)
  was the corrupt file, resolved by OCR.

## Merge status — PROMOTED 2026-07-16 ✅
Both minutes classes were promoted into the audited core (backups in
`_backups/2026-07-16-minutes-promotion/white_city/`):
- The **5 council minutes** → `../meeting_minutes/` (markdown + index rows `source=pmn`,
  re-extracted by the audited council extractor): +13 motions, `provenance=pmn_minutes`
  (2022-08-18 is a genuine zero-motion MIH work session).
- The **22 PC minutes** → `../planning_commission/` (a NEW populated dataset with its own
  MSD-grammar `extract_votes.py`): 106 motions, all `provenance=pmn_minutes`.
The 4 GPSC meeting reports remain HERE only (a sub-body with no roll-call motions —
deliberately not counted as PC minutes). This dataset stays the acquisition-provenance
record (raw PDFs, fetch log, notice URLs, discovery HTML); the audited copies live in the
core datasets.

## Regenerate / re-probe
`python3 wc_pmn_parse.py _disco/notices_5805.html _disco/notices_5879.html` re-parses the
notice lists. Re-fetch a body's history with
`polite_fetch.py --out _disco --name notices_<body>.html
"https://www.utah.gov/pmn/list/notices.html?id=<body>&page=300"`.

## 2026-07-17 — final PMN-crosscheck flag verification (7 flags -> 4)

Verified all 7 flags; appended 3 exceptions; re-run (--cached) 7 -> **4** flags.
- **Recovery leads (4, all agenda-grade, township council body 5805, no PMN minutes):**
  2018-08-17 (Notice of Meeting Location Change — meeting existed), 2020-04-02 (Agenda),
  2021-05-11 (Agenda), 2025-05-13 (FY2026 final-budget public hearing).
- **Exceptions:** wrong_date x2 (2023-02-23 'July minutes.pdf' = held 2022-07-28 PC min /
  file 959163; 2025-06-24 'May minutes.pdf' = held 2025-05-20 PC min / file 1290609 —
  filename month-name rescue family; each PC date's OWN minutes stay in unrecovered);
  other x1 (2021-12-02 'Budget Notice' = statutory availability notice, non-meeting).

## 2026-07-17 (wave2) — the 4 agenda-grade leads verified, all -> exceptions (4 flags -> 0)

Probed each flag at BOTH sources (PMN notice body + Streamline `/meetings-archive`). None
yields a recoverable minutes file, and none is a genuine held-meeting minutes gap — all 4
are false-positive flags (misparsed notice-posting dates or cancelled meetings), appended to
`pmn_exceptions.csv`. Crosscheck re-run (--cached): **0 flags, 8 suppressed**.
- **2018-08-17** (`wrong_date`) — notice 481949 is a *meeting-location-change* handout ADDED
  2018-08-17 for the **2018-09-06** regular meeting; not a meeting held on 08-17. The
  2018-09-06 meeting is already tracked in `meeting_minutes/minutes_unrecovered.csv` (purge).
- **2020-04-02** (`cancelled`) — notice 595725 is an explicit COVID **cancellation**; no
  meeting held. Streamline archive has no 4/2/20 doc.
- **2021-05-11** (`cancelled`) — notice 675389 (special/electronic) reads *"This notice has
  been cancelled"*; the special meeting did not occur. Regular 2021-05-06 is in the repo;
  Streamline archive has no 5/11/21 doc.
- **2025-05-13** (`wrong_date`) — notice 994685 is a *public-hearing notice* (FY2026 final
  budget) posted ~05-13 for the **2025-06-05** meeting, whose minutes ARE in the repo.
No rows added to `minutes_unrecovered.csv` (adding cancelled/non-meeting dates would fabricate
meetings that never occurred); no votes/promotions; no GRAMA warranted (cancelled meetings
produce no minutes, notice-posting dates are not meetings).
