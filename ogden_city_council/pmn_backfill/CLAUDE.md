# ogden_city_council/pmn_backfill — how to use this dataset

**Additive** Utah Public Notice (PMN) backfill of meeting minutes that are **missing**
from Ogden's audited `meeting_minutes/` and `planning_commission/` layers, built
2026-07-05. It is kept SEPARATE and NEVER hand-edited into the audited layer.

## What is here
- **The target recovery:** the known repo gap was RDA/MBA minutes for 2022–2023 (never
  acquired). This dataset recovers the **7 Redevelopment Agency (RDA) 2023 minutes** that
  PMN holds, plus 2 bonus 2020 MBA and 1 bonus 2024-04-23 RDA minutes — **10 net-new
  minutes total**. See `coverage.md` for the gap table, `AVAILABILITY.md` for confirmed
  PMN entity/body ids and the crawl method.
- 2022 RDA/MBA and 2023 MBA minutes are **not on PMN** (only budget/hearing notices) —
  recorded as honest gaps, not fabricated.

## Files
- `index.csv` — one row per recovered meeting. Superset of `meeting_minutes/minutes_index.csv`
  columns plus `body` (RDA/MBA), `raw_path`, `notice_url`, `extraction_method`, `status`,
  `retrieved_date`. `path` → extracted markdown (dataset-relative); `raw_path` → retained PDF.
- `minutes/*.md` — extracted text (`pdftotext -layout`) with a provenance header.
- `text/*.txt` — the raw `pdftotext` output (pre-markdown).
- `raw/*.pdf` — retained source PDFs. `raw/_fetch_log.jsonl` — polite-fetch provenance.
  `raw/_crawl/*.html` — the PMN crawl pages (entities/bodies/notices) for reproducibility.

## Provenance / method
Every PMN CC/RDA/MBA notice is filed under the **combined body id 6587** ("City Council,
Redevelopment Agency, Municipal Building Authority"); the separate RDA(321)/MBA(322)/CC(320)
pages only show ~6 months. PC lives under 340. Ogden entity = 225. Fetched with
`scripts/../polite_fetch.py` (GET-only, browser UA, logged). Each meeting date was read
INSIDE the PDF and matched its filename.

## Status vocabulary (`status` column)
- `recovered` — net-new minutes verified and added (all 10 rows here).
- `duplicate-not-promoted` / `source-unavailable` — reserved; none in this build.

## IMPORTANT — promotion
All 10 rows are **net-new RDA/MBA minutes flagged for promotion review** into the audited
`meeting_minutes/` layer (populate its `body` column; re-run vote extraction / db build).
Do NOT edit the audited layer from here — promotion is a separate, reviewed step. See
repo `TODO.md`.

## Regenerate / extend
Re-crawl: fetch `notices.html?id=6587&page=300` (CC/RDA/MBA) and `?id=340` (PC), parse
`(Meeting Minutes)`-labelled `/pmn/files/<id>.pdf` attachments, diff `(body,date)` against
the two repo indexes, fetch the misses. Scratchpad parser/differ used for this build are
transient; the retained `raw/_crawl/` HTML lets the diff be reproduced exactly.

## 2026-07-17 — crosscheck flag verification (18 → 15)

Verified all 18 `crosscheck_flags.csv` flags. 3 exceptions appended; re-run: **15 flags**
(agenda_only_gap 6, count_mismatch 9; 3 suppressed, 5 pending-adoption).

**count_mismatch (9) — ALL genuine recovery leads (the reverse-combined pattern).** Ogden
files CC + Joint Work Session (JWS) + RDA + MBA (+ occasional "CS") as SEPARATE per-body
minutes on one night; the audited `meeting_minutes/` layer kept only one doc per night and
dropped siblings. The engine diffs PMN against the AUDITED index only, so:
- `2020-05-12` (repo has CC; PMN adds MBA + Joint Work Session) — MBA already sits in this
  dataset's `index.csv` pending promotion; JWS still net-new.
- `2023-01-17` (repo CC; PMN adds JWS + RDA special) — RDA-special already in `index.csv`
  pending promotion; JWS net-new.
- `2023-10-03 / -10-17 / -11-14` (repo CC; PMN adds JWS each) — net-new JWS.
- `2024-01-09` (repo has JWS; PMN adds regular CC) — net-new CC.
- `2024-03-12` (repo CC+RDA; PMN adds a JWS; file `03-12-21 JWS.pdf` has a year-typo look —
  neither 2021-03-12 nor a 2024-03-12 JWS is in the audited repo, so recoverable either way).
- `2024-03-26` (repo JWS+CC; PMN adds `CS`) — net-new.
- `2025-01-07` (repo WS; PMN adds regular CC) — net-new CC; note ord 2025-01 already flagged
  (first 2025 council meeting un-ingested) in the parent CLAUDE.
None are false positives — every "extra" file is a real per-body minutes doc the audited
layer lacks. Confirmed vs the documented 2022-RDA/2023-MBA not-on-PMN gap: none of these
touch that era; they are 2020/2023/2024/2025 sibling-session gaps.

**agenda_only_gap exceptions (3):** `2025-01-01/6587`, `2025-01-01/340`, `2026-01-01/340` —
all "Annual Meeting Notice" dated Jan 1 (yearly organizational/schedule notice, not a
meeting). kind=other.

**agenda_only_gap leads (6):** 2020-07-28, 2022-01-18, 2022-10-25 (6587 "Meeting Agenda");
2020-11-04 (6587 hearing); 2024-05-01 (6587 Annual Action Plan / CDBG hearing — low
confidence); 2020-10-07 (340 PC public hearing). Agenda-grade → review gate.

## 2026-07-17 — reverse-combined sibling recovery + Council vote integration

Acted on the 9 `count_mismatch` leads verified above. Fetched, content-verified (all
born-digital, none DRAFT, dates confirmed inside each PDF), and recovered **9 net-new
reverse-combined sibling minutes** the audited per-night doc dropped — now rows 11–19 of
`index.csv` (`status=recovered`, `body=Council`, `retrieved_date=2026-07-17`,
`raw/` + `text/` + `minutes/` all written, `raw/_fetch_log.jsonl` logged):

| date | kind | file | notes |
|------|------|------|-------|
| 2020-05-12 | Joint Work Session | 659305 | sibling of the audited CC + the recovered MBA |
| 2023-01-17 | Joint Work Session | 1085453 | sibling of the audited CC + the recovered RDA-special |
| 2023-10-03 | Joint Work Session | 1072283 | |
| 2023-10-17 | Joint Work Session | 1072401 | |
| 2023-11-14 | Joint Work Session | 1072405 | |
| 2024-01-09 | **City Council Special Meeting** | 1085587 (.doc) | **has votes** (repo had only the JWS) |
| 2024-03-12 | Joint Work Session | 1121761 | PMN filename "03-12-21 JWS.pdf" is a year TYPO — the doc is dated March 12, **2024** |
| 2024-03-26 | Closed Session | 1115647 | |
| 2025-01-07 | **City Council Regular Meeting** | 1236969 | **has votes** (repo had only the WS; the "first-2025-meeting un-ingested" flag) |

The 5 JWS + 1 CS parse to **zero motions** (work/closed sessions) — documentary-only
recoveries. The **2 Council meetings carry real roll calls**, so `extract_backfill_votes.py`
was extended (2026-07-17) to also integrate `body=Council` recovered docs, deduping on the
recovered **slug** (Council siblings share `(body,date)` with the audited per-night doc; RDA/MBA
keep the exact `(body,date)` dedup, unchanged). Result in `meeting_minutes/all_votes.csv`:
**+44 `pmn_minutes` rows** (153 → 197), all from the 2 CC docs — 2024-01-09 special (7 motions,
incl. a **5-1 contested**, Choberka Nay; White absent) and 2025-01-07 regular (7 motions, three
7-0 roll calls). Zero audited (`minutes`) rows changed; `validate_votes.py` clean (contested
87 → 99). Derived layers (db/weeks) NOT rebuilt this pass — `validate_city.py` shows the expected
`i.weeks` staleness FAIL (weekly 5145 vs flat 5189, delta = exactly the 44 new rows).

The two "pending-promotion" docs called out in the task (2020-05-12 MBA, 2023-01-17 RDA-special)
were already `status=recovered` and already integrated (`pmn_minutes`) by the pre-existing
RDA/MBA path — verified present, no action needed.

**Hardening candidates:**
- "Annual Meeting Notice" / "annual meeting" (title, no minutes) is a recurring non-meeting
  family (ogden ×3) that slips past `RE_NOT_MEETING` (H-3 only added "meeting schedule").
  Consider adding it to `RE_NOT_MEETING`. Gate on absence of a minutes attachment.
- Minor: count_mismatch on 6587 conflates already-recovered-pending-promotion sibling
  minutes (in this dataset's `index.csv`) with net-new gaps, because the engine diffs only
  the audited index. Optional: also consult `pmn_backfill/index.csv`. Low priority — the
  flag is legitimate until promotion.
