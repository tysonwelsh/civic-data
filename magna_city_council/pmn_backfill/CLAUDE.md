# pmn_backfill/ — Magna (Source 4: Utah Public Notice)

Additive backfill of minutes recovered from **Utah Public Notice (PMN)** that are absent
from the audited `meeting_minutes/` / `planning_commission/` layers. Built 2026-07-14 per
`/expand-city-sources` Source 4. **PROMOTED into the vote layer 2026-07-16** (12 of 13
docs, `provenance=pmn_minutes` — see "Promotion" below; the raw/text files stay here and
are what the promoted vote rows' `source` points at). The 2025-11-18 CRA DRAFT remains
review-only.

## What's here (20 recovered minutes documents — all from PMN)

| body | count | dates |
|---|---|---|
| **Council** (body 5803) | 5 | 2024-02-13, 2024-02-27, 2024-11-26, 2026-03-10, 2026-06-09 |
| **Council — COVID-era regular** (body 5803) | 4 | 2020-08-11, 2020-08-25, 2020-09-08, 2020-10-27 *(added 2026-07-17 wave-2 — see that note below; 16 motions promoted)* |
| **Council — special workshop** (body 5803) | 3 | 2022-11-29, 2023-02-23, 2023-03-23 *(added 2026-07-17; 0 motions — see the 2026-07-17 note below)* |
| **CRA** (body 6925) | 8 | 2024-11-12, 2025-01-14, 2025-02-11, 2025-04-08, 2025-05-13, 2025-06-10, 2025-09-23, 2025-11-18 |

The **CRA (Community Reinvestment Agency, body 6925)** record more than triples (repo had
5 CRA dates; +8 here). The CRA convenes in-recess with the Council; tally-style votes
("Board Member <Name>"), same as `meeting_minutes/` body=CRA.

## Files
- `raw/` — the 13 source PDFs verbatim + `_fetch_log.jsonl` (url, bytes, sha256,
  retrieved_utc) from `polite_fetch.py`. Never delete/normalize.
- `text/` — extraction sidecars, one per raw, labeled by method in `index.csv`.
- `index.csv` — §9 `pmn_backfill` contract header
  (`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,
  pmn_file_id,retrieved_date,format,extraction_method`) + extras
  `recovery_source,orig_filename,text_path`. `path`/`text_path` are dataset-relative.
  `recovery_source` = `pmn` for all 13 (the CivicPlus `civicplus_archived` angle yielded
  nothing — see below).
- `coverage.md` — full per-body accounting + purge-gap verification + the CivicPlus probe.
- `AVAILABILITY.md` — what was checked / exists / stays a gap, as-of date.
- `work/` — intermediate fetched HTML + parsed JSON (provenance; re-derivable).
- Helper scripts (this dir, unique-named — never in the shared scratchpad):
  - `magna_pmn_crawl.py` — cumulative notices-list crawler + attachment parser (per body).
  - `magna_pmn_setdiff.py` — per-date set-difference of PMN minutes vs the repo indexes
    (filename-date extraction incl. 2-digit-year; ±4d tolerance).
  - `magna_pmn_extract.py` — pdftotext-layout + tesseract-OCR fallback + content-detection.
  - `magna_pmn_buildindex.py` — writes `index.csv` (notice_id/orig_filename machine-pulled).
  - `magna_civicplus_sweep.py` — CivicPlus AgendaCenter `Search` GET sweep (angle a).

## PMN discovery (for a future refresh)
- Entity: Magna City = **1323** (govType 3). Bodies: Council **5803**, PC **1559**,
  **CRA 6925**, Administrative Hearings 6379 (no minutes), Traffic Safety 9537 (no
  notices). Decoys (govType 5): Magna Water District **602**, Mosquito Abatement **601** —
  exclude. No separate metro-township entity — 5803 spans both eras.
- Crawl each body with cumulative `notices.html?id=<body>&page=500` (one GET = full
  history; the "past 6 months" banner is boilerplate). Minutes usually attach to a LATER
  meeting's approval notice → parse the meeting date from the **filename** (`MM-DD-YYYY`
  or 2-digit `MM-DD-YY`), not the notice's event date. **PMN type labels are unreliable**
  (a CRA "Minutes - DRAFT.pdf" was tagged "Public Information Handout") — key off filename
  + content, and exclude `... (No Minutes).pdf` agenda bundles.
- Fetch files from **`https://www.utah.gov/pmn/files/<id>.pdf`** — the `pmn.utah.gov` host
  redirects to the PMN home HTML.

## Verification results (see coverage.md for detail)
- **PC 1559 superset CONFIRMED** — repo holds all 80 recoverable PMN PC minutes; 0 missing.
- **Council 5803** — 5 genuine recoveries; the 36-meeting **2017/early-2018 purge VERIFIED
  genuine** (the only 2 surviving listing references, files 329391/329393, are themselves
  404-purged; the other 34 have no attachment). `minutes_unrecovered.csv` stands unchanged.
- **CRA 6925** — 8 recoveries (7 approved + 1 draft); repo's 2024-10-22 CivicPlus CRA has
  no PMN-6925 counterpart (that body's minutes begin 2024-11-12).
- **CivicPlus `ArchivedMinutes` probe — mechanism not used by Magna.** All 99 CivicPlus
  Minutes-slot dates 2022–2026 fall within a repo date; `ArchivedMinutes` never appears in
  a Search listing; `PreviousVersions` (10 dates, incl. the PMN-sourced wrong-doc dates)
  exposes only `ArchivedAgenda`. 0 CivicPlus recoveries.

## Extraction notes
- 9 recoveries are scanned image PDFs → OCR'd with `tesseract` (`format=scanned`,
  `extraction_method=tesseract-ocr`); 4 are born-digital (`pdftotext-layout`).
- **2026-03-10** is a trap: pdftotext returned 2.3k chars — but only from an embedded
  D.R. Horton plat/map exhibit page; the 10-page minutes body is scanned images. Forced
  OCR yields the real minutes (24.6k chars, quorum roster + motions). Recorded as scanned.
- Corpus screen (`audit-city-data/scripts/screen_corpus.py text`): **0 dict/split/weird
  outliers** across all 13 (repeated-line / ends-mid flags are advisory OCR artifacts).

## Promotion — ✅ DONE 2026-07-16 (12 of 13 docs)
`meeting_minutes/extract_backfill_votes.py` parses the text sidecars with the audited
`extract_votes.parse_meeting(...)` grammar and merges into `meeting_minutes/all_votes.csv`
with a trailing `provenance=pmn_minutes` column (`source` = `pmn_backfill/text/…`):
**51 motions / 51 rows — Council 32 (5 docs) + CRA 19 (7 docs)**; db/motions_std/weeks
rebuilt; validate_city 0 FAIL. Run order after any re-extraction:
`extract_votes.py` THEN `extract_backfill_votes.py`.
- **NOT promoted: the 2025-11-18 CRA doc** — stamped "**DRAFT MINUTES – UNAPPROVED**";
  it stays a review-only sidecar here (its 4 motions are visible in `text/` but are not
  in the vote layer; re-check PMN for an approved version on a future refresh).
- Date verification: the 2025-01-14 CRA doc's OCR page header misprints "JANUARY 14,
  2024" — its adjourn motion, attest block ("approved on February 11, 2025") and the
  2025-02-11 doc's approval motion all confirm **2025-01-14**. The 2024-11-12 CRA doc's
  attest line says "City Council Meeting Minutes" (clerk template slip); content is CRA.
- Grammar additions made in the audited extractor during promotion (backed up first):
  "passed BY A unanimous vote" + bare "vote was unanimous." recognized as unanimous
  results, and `Paerce→Pierce` OCR garble — plus a trailing-pipe OCR cleanup applied to
  these sidecars only (in extract_backfill_votes.py). Without them, 5 motions were
  silently dropped and one audited motion (2022-12-13 m15) carried a false
  "No result recorded".

## Rules honored
Additive only; existing datasets untouched; raws retained; nothing fabricated (both the
council purge gap and the PC 2017-2018 gap stay gaps); polite GET-only. Parent
`README.md`/`CLAUDE.md`, `sources.csv`, `cities.db`, `coverage.json`, `TODO.md` are owned
by the orchestrator — not edited here.


## 2026-07-17 — PMN cross-check flag verification (26 flags -> 21)
Verified every crosscheck_flags row against cache + repo indexes; 5 exceptions added.
- **Exceptions (5):** 4 foreign bodies riding PC(1559)'s notice list (Metro Township
  Mayor's Meeting 2020-07-16 & 2021-10-26, GP Steering Committee 2020-10-29, Land Use
  Hearing Officer 2021-07-21 = out-of-scope body 6379) -> kind=other; 1 CANCELLED CRA
  meeting 2026-02-10 (cancellation was only in the attachment filename, not the title,
  so RE_CANCEL missed it) -> kind=other.
- **Recovery leads (19), remain flagged:**
  - 3 missing_minutes = genuine special-workshop COUNCIL minutes on PMN the repo lacks,
    filename date == event date, [Meeting Minutes] label confirmed in cache:
    2022-11-29 (n796515), 2023-02-23 (n814393), 2023-03-23 (n818785). HIGH value.
  - 16 agenda_only: the Aug-Dec 2020 township-council COVID cluster (2020-08-25, 09-08,
    09-22, 10-13, 10-27, 11-24, 12-08, 12-15 — repo council jumps 2020-07-14 -> 11-10 ->
    2021-01-12; several have audio/agenda only, minutes likely never posted) contradicts
    the "full 2018+ history" framing; 2022-08-16 & 2024-06-18 special mtgs; 2024-09-24
    regular 4th-Tue meeting; 2025-09-09 (Ord 2025-O-14 mtg); 2 low-conf PC dates
    (2019-09-12 amended agenda, 2019-12-12 — magna PC is a documented complete superset,
    so minutes likely never existed); 2 CRA agency gaps HELD (2024-12-10, 2026-05-12 —
    CRA body 6925 was never probed by fetch_new; real agency leads).
- **Hardening candidate (2 residual flags):** filename-date-rescue — 2020-03-10 (files
  02-11 + 02-25 minutes) & 2020-08-11 (07-14 minutes); the minutes attachments are for
  PRIOR meetings already in repo, riding a later approval notice. See report below.
- Re-run (`--cached`): **21 flags** (16 agenda_only + 5 missing_minutes), 5 suppressed.

## 2026-07-17 — 3 council missing_minutes leads RECOVERED (catalog only; 0 vote rows)
The 3 township-era **SPECIAL WORKSHOP** council leads above were fetched, content-verified as
genuine born-digital [Meeting Minutes], and added to this dataset (`slug=council-special-workshop`,
`format=text`, `extraction_method=pdftotext-layout`, `recovery_source=pmn`) — index now **16 docs**:
- **2022-11-29** (file 950413, notice 796515) — Title 18/19 zoning code-review workshop.
- **2023-02-23** (file 960533, notice 814393) — Title 18/19 zoning/subdivision code review.
- **2023-03-23** (file 1106061, notice 818785) — Title 18/19 code review. In-body narrative
  misprints "March **28**" (a Tuesday); header "March 23" (a Thursday) + filename + notice +
  weekday confirm the **true date 2023-03-23**.
These are pure study/workshop sessions — **NO motions, NO votes** (only narrative "the meeting
was adjourned"). `extract_backfill_votes.py` lists all 3 as **zero-motion docs → 0 rows merged**;
`meeting_minutes/all_votes.csv` is byte-unchanged (still 1,017 rows / 972 motions). They fill the
coverage record honestly (the meetings existed) without fabricating any vote. `validate_dataset.py`
PASS.

## 2026-07-17 (wave-2) — Aug–Dec 2020 COVID council cluster + CRA agency probe
Worked the crosscheck's residual leads (the Aug–Dec 2020 township-council COVID cluster + the
two CRA agency dates fetch_new had never probed). PMN body 5803 + 6925 re-probed; every doc
in-body-date verified.

**RECOVERED — 4 COVID-era regular council minutes → PROMOTED (16 motions, `pmn_minutes`):**
- **2020-08-11** (file 636165) & **2020-08-25** (file 636167) — standalone minutes posted as
  approval items 6.1/6.2 on the 2020-09-08 council notice (n627445). Born-digital.
- **2020-09-08** (minutes pp47–60 of the 2020-09-22 council packet "Backup Docs Combined.pdf",
  file 640412, n630052) & **2020-10-27** (minutes pp60–67 of the 2020-11-24 packet
  "Backup documents combined.pdf", file 661255, n642347) — the minutes exist ONLY embedded in
  the *next* meeting's approval packet; the full packet is retained verbatim as raw and the
  text sidecar is the minutes page-range. All four are township-era, voting Chair-"Mayor" Peay
  presiding; the 09-08 Prokopis/Peel conflict-of-interest declarations are captured in motion
  text but the source prints "passed unanimously" (no recusal vote recorded — faithful, not a miss).
  `all_votes.csv` 1,017→1,033 rows / 972→988 motions; db/motions_std/weeks rebuilt; validate_city 0 FAIL.

**DEAD — 5 COVID-era council dates → `meeting_minutes/minutes_unrecovered.csv`:** 2020-09-22,
2020-10-13, 2020-11-24, 2020-12-08, 2020-12-15. Agenda (and audio) posted on PMN but NO minutes
document ever posted — not on the meeting notice, not carried as an approval item in any later
packet (traced the 09-22 → 01-12-2021 chain incl. the 2020-11-10 "Total packet" and the
01-26-2021 packet; the 12-08 file is an agenda, 01-12-21.pdf is the 01-12-2021 minutes). Genuine
publish gaps, not fabricated. (08-11/08-25/09-08/10-27 minutes ride *other* meetings' notices,
which is why the crosscheck's per-notice setdiff missed them.)

**CRA body 6925 (never probed by fetch_new before) — verified, ledgered in `pmn_exceptions.csv`:**
- **2024-12-10 CANCELLED** (n959665 body says "Meeting has been cancelled"; only an agenda
  attachment — confirmed genuine vs the un-cancelled 2024-11-12 control notice) → `kind=other`.
- **2026-05-12 agenda-only** — meeting held, minutes NOT yet posted to PMN (not even DRAFT on the
  2026-06-09 CRA notice); pending approval → `kind=agenda_only`, re-check next refresh.
- **fetch_new.py EXTENDED** (city-local file) to probe CRA body **6925** (`_cra_probe`,
  compares against CRA dates in all_votes/index/exceptions). The probe additionally surfaced
  2026-03-10 & 2026-04-14 (both CANCELLED), 2026-06-09 (agenda-only, minutes pending), and a
  2026-01-13 filename false-positive — all four ledgered so `--probe` now returns CRA "none".

## 2026-07-19 (lm-wave) — the 6 lower-confidence flags INDEPENDENTLY RE-VERIFIED (all DEAD)

The wave-2/Q3 "lower-confidence flags" (4 council specials + 2 PC 2019 — deferred at wave-2, then
dispositioned by the Q3 refresh) were **independently re-verified at source** (cached PMN crawl
`work/parsed_5803.json`/`parsed_1559.json` — today's data — plus a live GET of the 2022-08-16 doc
body). **All 6 confirmed DEAD** (meeting noticed/held, minutes NEVER published) — already correctly
carried in the respective `minutes_unrecovered.csv`; **no data change**. A full-attachment scan of
BOTH bodies (in-body/filename, not just the meeting's own notice) found **zero minutes** for any of
the six (minutes ride a later approval notice here, so this is the decisive test):

| date | body | attachments found | disposition |
|---|---|---|---|
| 2022-08-16 | Council special workshop | "Magna 8-16-22 Special Workshop.pdf" + CC Packet — the .pdf is the **PUBLIC-NOTICE AGENDA** (live-fetched & read: "PUBLIC NOTICE IS HEREBY GIVEN…will hold a special workshop on the 16th day of August 2022"), NOT minutes | DEAD (agenda/packet only) — first of the Title 18/19 workshop series whose 3 later sessions' minutes WERE recovered |
| 2024-06-18 | Council special | audio + agenda + packet | DEAD (held, no minutes) |
| 2024-09-24 | Council regular (4th-Tue) | audio + agenda + packet | DEAD (held, no minutes) |
| 2025-09-09 | Council regular (Ord 2025-O-14) | audio + agenda(+supporting) | DEAD (held, no minutes) |
| 2019-09-12 | PC | "190912_MagnaTPC_Agenda AMENDED.pdf" only (next mtg 2019-09-26 minutes exist, not 09-12) | DEAD (amended agenda only) |
| 2019-12-12 | PC | agenda + packet only (a foreign Mayor's-Meeting rides the same date) | DEAD (agenda/packet only) |

None are cancellations or false-positives (so none belong in `pmn_exceptions.csv`); all 4 council
+ both PC are held-but-unminuted publish gaps = correct `minutes_unrecovered.csv` rows. The 4
council dates carry PMN audio → Whisper leads (owner-gated, out of scope).

## 2026-07-17 (wave-2) — 2025-11-18 CRA draft watch (TODO): STILL DRAFT-ONLY
Re-checked PMN body 6925 for an APPROVED copy of the 2025-11-18 CRA minutes (current best copy is
the unpromoted DRAFT sidecar). The 11-18-2025 CRA minutes appear only as **DRAFT** (on the
2025-12-09 CRA notice n1043807); they were never posted APPROVED, and the next CRA notice
(2026-01-27, n1054727) does not carry them. **Outcome: still draft-only as of 2026-07-17** — the
sidecar stays unpromoted (`pmn_exceptions.csv` `verified_date` bumped to 2026-07-17).
