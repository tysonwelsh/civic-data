# pmn_backfill — Millcreek (expand-city-sources §4)

Utah Public Notice (PMN, `utah.gov/pmn`) minutes backfill for Millcreek. **Additive and
separate** from the audited minutes layer — it is a date-level gap-check plus the few files
PMN holds that the repo lacked. The `meeting_minutes/` and `planning_commission/` layers were
**not modified**.

## Layout
```
raw/2017/2017-11-21_Board_of_Canvassers_Minutes.pdf   recovered original (verbatim) + _fetch_log.jsonl
raw/2018/_fetch_log.jsonl                             provenance of the dead-404 attempt (no PDF)
raw/_discovery/                                       entity/body/notices list HTML (crawl provenance)
text/2017-11-21_Board_of_Canvassers.txt              OCR sidecar (tesseract) of the recovered scan
index.csv                                            recovered minutes (1 row) — schema below
unrecovered.csv                                       verified-dead PMN attachment (2018-03-20)
coverage.md                                           per-body per-year repo/PMN/recovered/missing table
AVAILABILITY.md                                       what was checked + honest gaps
```

## How the bodies were found (do not hardcode ids)
GET-only entity chain, per skill §4:
1. `list/entities.html?id=3&limit=2000` (govType 3 = Municipality) → **Millcreek = `id=1279`**.
2. `list/publicBodies.html?id=1279&limit=2000` → 12 bodies. Relevant:
   **City Council 5741 · Planning Commission 5815 · Community Reinvestment Agency 6367.**
3. Per body, one cumulative GET `list/notices.html?id=<body>&page=300` returns the entire
   notice history; filter rows whose attachment label is `(Meeting Minutes)`.

> The city's `fetch_new.py` refers to PMN "body 1031" for the council — that id is **stale**;
> the live chain resolves the council to **5741**. Use 5741.

## Cross-check logic
Per-**date** set-difference (not per-year counts), ±4-day tolerance for meeting-vs-posting
offset. PMN minutes dates vs `meeting_minutes/minutes_index.csv` (Council + CRA bodies) and
`planning_commission/minutes_index.csv` (PC body). Every repo match was exact-date; tolerance
masked nothing. Result: repo is a near-total superset — 1 recoverable council gap, 1 dead file.

## index.csv schema
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method,sha256`
— the §9 pmn_backfill contract (the standard minutes 8-col set plus `body`, PMN provenance
`notice_url,pmn_body_id,pmn_file_id`, `retrieved_date`, and `extraction_method`) plus a
`sha256` extra. `path` is dataset-relative including `raw/`. `source=pmn`.
`format=scanned` (image PDF); `extraction_method=ocr-tesseract`.

## Recovered / unrecovered
- **Recovered (1) — PROMOTED into the audited layer 2026-07-20:** 2017-11-21 Board of
  Canvassers general-election canvass (seated D2 Marchant, D4 Uipi). Scanned → tesseract OCR
  sidecar. Tally-only roll call (pre-2022 seam). **Now merged into `meeting_minutes/`** as
  `minutes/2017/2017-11-21/2017-11-21_board-of-canvassers-general-election-returns.md`
  (`minutes_index.csv` row `source=pmn`, `source_url` = the PMN file URL — the collection's
  PMN-promotion convention, cf. murray's 38 `source=pmn` rows). `extract_votes.py` emits its
  **2 tally-only motions** (Other + Procedural/Administrative, both `Pass (unanimous)`, blank
  member/vote) — identical shape to the already-audited 2019-11-19 canvass precedent. Identity
  cross-confirmed: the 2019-12-16 council minutes formally ADOPT the "Board of Canvassers
  November 21, 2017 Meeting Minutes" (Item 5.1). This `pmn_backfill/` copy is retained as the
  raw provenance record.
- **Unrecovered (1):** 2018-03-20 CC Budget Work Meeting — PMN attachment 404 (dead), also a
  budget-spreadsheet-only doc on AgendaCenter. Logged in `unrecovered.csv` and already in
  `meeting_minutes/minutes_unrecovered.csv`.

## Provenance / politeness
All fetches via `scripts/polite_fetch.py` (browser UA, ≥1s/host, logged). Every attempt —
including the 404 — is in `raw/*/_fetch_log.jsonl`. GET-only; the POST/CSRF PMN search and the
6-month list view were avoided per the polite rule.

## Validate
`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py millcreek_city_council/pmn_backfill`
→ PASS.


## 2026-07-20 — PMN born-digital OCR-upgrade probe → NEGATIVE (no upgrades available)

Tested the standing "Millcreek + Taylorsville: PMN born-digital minutes upgrade" TODO for the
**millcreek half** (taylorsville's was closed 2026-07-12 with 6 promotions). Method: enumerate
every OCR/scanned repo minutes file (106 council `format=scanned` dates + 36 PC `format=ocr`
dates), map each to its PMN minutes attachment via the cached notices HTML (`_crosscheck/cache/`),
fetch each PMN PDF, and measure its text layer (`pdffonts` + `pdftotext` char density). Full
per-date inventory: **`ocr_upgrade_probe.csv`** (binaries discarded per SCHEMA_SPEC §9).

**Result — 0 genuine upgrades.** Verdicts across 142 date-probes: **92 scanned** (PMN copy is a
scanned image, same as or worse than the repo — no text layer), **38 now-404** (the old
2017–2018 PMN file ids listed in the cached notices have since been purged/rotated off
`utah.gov/pmn` — no PMN copy served anymore), **10 no-PMN** (no minutes attachment for that
date), **2 "born-digital"** — both of which are **cross-body false positives, NOT upgrades**:
- `1186547` (CC 1-9-24 Minutes, born-digital) ≡ repo Council file `...759.md`, which is
  **already `format=text`** (byte-equivalent: 61832 vs 61834 chars, same source typos incl.
  "cornrnent"). The genuinely-scanned repo file that date is the *CRA* one (`...760.md`), whose
  same-body PMN copy (`1075413`/`1075559`) is a 3-page scanned image.
- `1122567` (CRA 2-26-24 Minutes, born-digital) ≡ repo CRA file `...778.md`, **already
  `format=text`** (2561 ≡ 2561 chars). The scanned repo file that date is the *Council* one
  (`...777.md`), whose same-body PMN copy (`1108193`) is a scanned image.

**Conclusion:** Millcreek's city posts the **same generation of each document (per body) to both
AgendaCenter and PMN** — where the repo file is a scan, PMN's same-body copy is also a scan (or a
purged 404). PMN holds a born-digital copy only for meetings/bodies the repo **already** carries
as clean text. This is the flip side of the `pmn_backfill` core finding ("city double-posts →
repo is a near-total superset") and the opposite of Taylorsville (whose RICOH scans DID have
born-digital PMN twins). The scanned-repo OCR text stands as the best available source. (Residual,
not chased at [low] priority: whether any of the 38 now-404 2017–18 minutes were re-posted
born-digital under new file ids.)

## 2026-07-17 — crosscheck flag verification (17 flags → 3 leads, 14 exceptions)

Verified every 2026-07-17 crosscheck flag (cached list HTML + repo indexes across BOTH
datasets + throttled per-notice GETs). Re-run after appending exceptions: **3 flags**
(15 suppressed, incl. the pre-existing 2018-03-20 dead-link row).

**Recovery leads (3, agenda-grade — real meetings, agendas on PMN, no minutes on PMN,
absent from repo). All are work/special meetings that may never have had formal minutes —
verify before promoting:**
- **PC 2017-04-04** — Planning Commission Special Working Meeting (commercial-zones C-1/C-2/C-3 rewrite work session).
- **PC 2017-08-08** — Planning Commission Special Work Meeting (manufacturing-zones / fence / R-M ordinance drafts).
- **Council 2019-05-01** — City Council SPECIAL public meeting (street/boundary matter; distinct from the same-day Holladay/Millcreek joint open-house & hearings). Repo has 05-13/05-20/05-28.

**Exceptions written (14), by kind:**
- `other` ×13: **foreign-body cross-filing under PC body 5815** — 2017-01-23 (council mtg), 2017-03-27 (City Council Zoning Meeting), 2017-05-08 (City Council Meeting) all held by repo under `meeting_minutes`; 2017-04-14 + 2017-06-02 = Mayor's-Meeting administrative postings (body 5949); 2019-09-03 (field trip to SLC Council work session + press conference — no Millcreek minutes); 2021-12-27 (regular meeting held 12-20 in lieu, repo has 12-20); and 6 **annual meeting-schedule** postings (5741/5815/6367 × 2020-01-01 & 2022-01-01).
- `wrong_date` ×1: 2023-01-04 — PMN event date wrong by a year; notice body says 'Thursday, 4 January 2024', repo holds council 2024-01-04.

**Hardening candidates:** (1) 'Meetings Schedule 2020' / 'Regular Meetings Schedule 2022'
evade `RE_NOT_MEETING` (regex has singular 'meeting schedule'; titles use plural
'Meetings Schedule') — add `meetings? schedule` / `schedule \d{4}`. (2) Early-era (2017)
Millcreek posted council + Mayor meetings under the PC body 5815 (foreign-body).
