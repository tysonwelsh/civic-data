# Herriman — `pmn_backfill/` (Utah Public Notice cross-check + recovery)

**Source 4 of `expand-city-sources`.** A SEPARATE dataset that cross-checks the
audited `meeting_minutes/` and `planning_commission/` layers against the statewide
Utah Public Notice repository (`utah.gov/pmn`) and holds the minutes genuinely
missing from the repo. Built 2026-07-13.

## ✅ PROMOTED (2026-07-16) — this dataset now FEEDS the audited vote layer
The queued promotion ran 2026-07-16 (+one on 2026-07-20): **67 recovered docs are merged
into `../meeting_minutes/all_votes.csv` (56: 22 council incl. a 2021-01-13 RCCM fetched
during promotion + the 2022-02-09 RCCM recovered by the 2026-07-20 short-doc audit, 5
joint as body=Council, 13 CDRA, 10 HCSEA, 6 HCFSA) and
`../planning_commission/all_votes.csv` (11 PC)** with `provenance=pmn_minutes`, via
each dataset's `extract_backfill_votes.py` (which re-parses `text/*.md` on every
run — do not move/rename them). NOT promoted, permanent sidecars here:
- 2021-01-13 CDRA (dup — the audited 2021-01-13 doc IS those minutes, re-tagged);
- 2023-11-01 PC (stamped "Pending Formal Approval / Draft");
- 2022-04-21 PC (the PMN "Minutes" file is a mislabeled zoning use-table, not minutes);
- both AppealAuthority hearings (no appeals body in the city model — follow-up).

## Headline result — the repo is NOT a PMN superset

**70 minutes documents recovered (33 MB) + 9 proven 2020 cancellations.** Three
findings matter beyond the docs themselves:

1. **The 2020 "COVID cancellations" belief was only half right.** 9 gap dates are
   now PROVEN cancellations (notice proofs in `raw/cancel_*`), but 12 other 2020
   docs (11 council-family + 1 PC) were real meetings whose minutes the repo's
   Wayback-harvested S3 key list never surfaced — including **2020-09-09**, where
   the repo's only doc that day is the CDA minutes and the council minutes were
   absent.
2. **The in-session agency capture claim fails from ~2024 on.** PMN posts standalone
   approved CDRA/HCSEA/HCFSA minutes; the repo's combined council docs for those
   dates contain zero agency-section text (grep-verified). 30 standalone agency
   minutes recovered. `meeting_minutes/CLAUDE.md`'s "in-meeting captures are
   complete" is WRONG for the 2024+ era — a promotion/re-extraction pass is a
   follow-up task.
3. **An entire meeting day (2022-05-11: Council + CDRA + HCSEA) was absent** from
   the repo, plus special meetings (2021-08-09/11/25, 2023-12-15 SCCW), the
   **2023-12-05 Special Board of Canvassers** (election canvass minutes), and the
   only 2 Appeal Authority minutes PMN has ever held.

Per-year × body tables, the full recovered list, and the cancellation table:
`coverage.md`. What exists / doesn't / label-trust caveats: `AVAILABILITY.md`.

## Method (reproducible, GET-only)

1. Entity discovery: `entities.html?id=3` (govType 3 = Municipality) → Herriman
   = **155** → `publicBodies.html?id=155` (17 bodies; 8 crawled).
2. One cumulative GET per body: `notices.html?id=<body>&page=200` returns the
   body's ENTIRE notice history (list view alone shows only 6 months; the
   historical search is POST/CSRF — never used).
3. Parse list HTML → per-notice event date + attachment `(Meeting Minutes)` labels
   **plus a filename scan for `minutes`** (two minutes PDFs are mislabeled
   `(Audio Recording)` — PMN labels under-count).
4. Classify each attachment to its TRUE body from the FILENAME (RCCM/SCCM/SCCW/
   SCCWM/BOC=council · PC/PCM=pc · CDA/CDRA · HCSEA · HCFSA · Joint/CCPC ·
   Appeal), NOT from PMN's body filing (council minutes appear under the PC body
   and vice versa).
5. Per-date set-difference vs `meeting_minutes/minutes_index.csv` /
   `planning_commission/minutes_index.csv` (±4-day tolerance; exact-date for the
   joint body), THEN a per-date doc-COUNT comparison to catch body-level shadowing
   (this caught 2020-09-09 and the 2020-09-30 triple-session day).
6. Fetch every absent doc via `polite_fetch.py` (all 200s), verify each internal
   header/date, convert with `pdftotext -layout`; 4 scanned PC docs OCR'd with
   tesseract at 300 dpi (labeled `tesseract-ocr`). Corpus screened with
   `screen_corpus.py` — all flags investigated benign (vote-grammar repetition,
   footer/signature endings).

## Layout / schema

```
raw/
  _disc_entities.html            entity list (govType 3) — provenance
  _disc_bodies.html              Herriman bodies (entity 155)
  _notices_<bodyid>.html         cumulative notice history per crawled body (8)
  pmn_<body>_<date>_<fileid>.pdf the 70 recovered minutes
  cancel_<date>_notice_<id>.html the 9 cancellation-proof notice pages
  cancel_2020-04-29_594755.pdf   the one posted cancellation PDF
  _fetch_log.jsonl               polite_fetch provenance (url/status/bytes/sha256/utc)
text/pmn_*.md                    markdown per recovered doc (provenance header;
                                 extraction method labeled per file)
index.csv                        §9 pmn_backfill contract (14 cols) + text_path extra
coverage.md · AVAILABILITY.md · CLAUDE.md
```

`index.csv` contract columns:
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`
(+ `text_path` extra). `path` is dataset-relative including `raw/`. `source=pmn`.
`body` ∈ Council / PlanningCommission / JointCC-PC / CDRA / HCSEA / HCFSA /
AppealAuthority. `format` ∈ `text` (66) / `scanned` (4, OCR) / `html` (9 proofs);
cancellation rows have empty `extraction_method` (nothing extracted — the notice
page itself is the proof).

## Caveats / rules honored

- **GET-only, polite** (`polite_fetch.py`, ≥1s/host); raws retained verbatim;
  nothing fabricated — every gap is documented, not filled.
- **OCR files preserve source errors** (e.g. the 2023-01-04 PC scan's header year
  misprint) — do not "clean" them.
- ~~Do NOT merge into the audited layers in place.~~ **DONE 2026-07-16** via the
  provenance-tagged merge pattern (ogden/vineyard/orem/south_jordan precedent):
  votes merged with `provenance=pmn_minutes`; the docs stay HERE (they are not
  copied into `minutes/`; `all_votes.csv` `source` paths point into this dataset).
  One extra doc was fetched during promotion (2021-01-13 RCCM, file 690779 —
  logged in `raw/_fetch_log.jsonl` and `index.csv`), so the index now holds **71**
  recovered minutes + the 9/10 cancellation-proof rows.
- Not loaded into `cities.db` by this run (`build_cities_db.py` out of task scope).
- Below-floor PMN history (2008–2019, ~300 minutes docs) inventoried but not
  fetched — see `AVAILABILITY.md`.

## 2026-07-17 — final PMN-crosscheck flag verification (8 flags -> 6)

Verified all 8; appended 2 exceptions; re-run (--cached) 8 -> **6**.
- **Recovery leads (6, agenda-grade):** 2022-07-27 joint CC/PC work meeting (body 1251);
  2023-06-30 council public hearing (body 1155); 2023-07-19 HCSEA Truth-in-Taxation hearing
  (body 6239 — draper TnT pattern, real; PC met same day as a separate body); 2023-08-15 CDRA
  public hearing (body 2256); 2024-08-21 'Planning Commision Work Meeting' [sic] (body 1151);
  2025-08-20 HCSEA TnT hearing (body 6239; PC met same day separately). Recovery target for the
  special-district hearings is the one combined in-session council meeting for that date.
- **Exceptions (duplicate x2):** 2023-06-30 CDRA (2256) = sibling posting of the 2023-06-30
  council hearing; 2025-08-20 HCFSA (7553) = sibling posting of the 2025-08-20 HCSEA meeting
  (herriman runs CDRA/HCSEA/HCFSA in-session).

## 2026-07-17 (wave-2) — all 6 residual leads verified & CLOSED (0 open flags)

Each of the 6 `agenda_only_gap` leads was a PMN **notice-posting date**, not a meeting date.
Verified against the PrimeGov `ListArchivedMeetings` API (authoritative committee/minutes
oracle: council cid=3, PC cid=14, CDRA cid=4, HCFSA cid=8, HCSEA/"Truth in Taxation" cid=9)
plus the PMN notice pages and the crawled body-notice HTML. `crosscheck_flags.csv` is now
header-only. Resolutions:
- **4 → `pmn_exceptions.csv`:** 2022-07-27 joint (CANCELLED, PMN 770663 + PrimeGov cancellation
  doc); 2024-08-21 PC (CANCELLED, PMN 933874 — a site field trip, no meeting); 2023-06-30
  council (notice for the FY2024 budget hearing HELD at the in-repo 2023-07-12 council mtg,
  R33-2023); 2025-08-20 HCSEA (notice for the FY2026 budget hearing HELD at the in-repo
  2025-08-27 council mtg — repo already has 2025-08-27 HCSEA(7)+HCFSA(12) votes).
- **2 → `../meeting_minutes/minutes_unrecovered.csv` (genuine held-but-unpublished):**
  HCSEA Truth-in-Taxation hearing **2023-08-22** (PrimeGov cid=9 Agenda+Packet, no Minutes;
  PMN 6239 has no 2023_08_22 minutes attachment) and CDRA budget hearing **2023-08-23**
  (PrimeGov cid=4 Agenda+Packet, no Minutes; PMN 2256 has 2023_08_23 Packet only). Both held
  (no cancellation), minutes never posted on any channel. **No promotable minutes** were found
  for any lead → the vote layer is UNCHANGED (no re-extract / backfill / db / weeks rebuild).
- **Follow-up (report-only):** HCFSA 2023-08-23 (cid=8) is the same held-but-unminuted case as
  the CDRA hearing that day but was not one of the 6 flags — a candidate for the same GRAMA.
