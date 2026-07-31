# pmn_backfill/ — Utah Public Notice recovery for Murray's two big minutes gaps

**ADDITIVE dataset (built 2026-07-13) — PROMOTED 2026-07-16.** The 77 `status=recovered`
docs (18 council + 59 PC) were promoted into the audited `meeting_minutes/` and
`planning_commission/` layers (index `source=pmn`; raw PDFs copied keeping these basenames;
votes re-extracted; db/weeks/motions_std rebuilt; validate_city 0 FAIL). This folder REMAINS
the acquisition/provenance record: the fetch log (`raw/_fetch_log.jsonl` with sha256s), the
2023-07-11 **cancellation notice**, and the two negative probes live only here and must not
be deleted. The three non-`recovered` rows were deliberately NOT promoted.

## What this recovers
1. **The 2023 council Tyler-TMM gap — CLOSED.** 17 approved 2023 City Council meeting
   minutes (every date in `meeting_minutes/minutes_unrecovered.csv` except 2023-07-11,
   which PMN proves was **cancelled** — the official cancellation notice is retained and
   indexed) + a **net-new 2023-08-21 Special Council Meeting** (joint with Millcreek,
   Murray North Station) that neither the index nor the unrecovered log knew about.
2. **The PC-minutes-end-2022-11 gap — CLOSED through 2026-05-07.** 59 Planning
   Commission minutes 2023-01-05 → 2026-05-07. Remaining PC holes are honest:
   cancellations (officially noticed), 2025-04-17 and 2025-07-17 (minutes not on PMN —
   see AVAILABILITY.md), and 4 recent 2026 agenda-only dates.
3. Two probes that returned honest negatives, retained for the record: the PMN copy of
   the repo's only OCR council file (2022-06-21) is **also image-only** (upgrade
   rejected), and PMN's "2025.07.17 PC Meeting Minutes.pdf" is **actually the agenda**
   (`status=pmn-mislabeled-agenda`).

## Layout
```
raw/        80 PDFs verbatim as fetched (+ _fetch_log.jsonl — url/status/bytes/sha256
            per file). Names: council_<date>_<pmn_file_id>.pdf, pc_<date>_<pmn_file_id>.pdf.
minutes/    one markdown per document: provenance header (notice URL, file id, PMN
            attachment name, format, honest NOTEs) + pdftotext -layout text, verbatim.
index.csv   §9 pmn_backfill contract (date,year,title,slug,body,path,source,source_url,
            notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method)
            + extras: text_path,status,pmn_event_date,orig_fname,chars,note.
coverage.md per year × body: repo count, PMN count, recovered, cancelled, still-missing.
AVAILABILITY.md  discovery chain, body-id table, honest gaps, not-fetched inventory.
```
`status` vocab: `recovered` (77) · `cancellation-notice` (1) ·
`upgrade-candidate-rejected` (1) · `pmn-mislabeled-agenda` (1).
`body` ∈ `Council` (20) / `PlanningCommission` (60). `path` = the raw PDF;
`text_path` = the markdown.

## Build method (reproducible)
- PMN entity 213 (Murray) → bodies **735 Municipal Council**, **983 Planning and Zoning
  Commission** (+ 987/6863/977 inventoried only). One cumulative list GET per body
  (`/pmn/list/notices.html?id=<body>&page=200` — returns the full history), attachment
  labels parsed from the list HTML, then a per-meeting-date set-difference (±4 days)
  against both repo `minutes_index.csv` files and the unrecovered log.
- Where a date offered several `(Meeting Minutes)` attachments, the file whose name says
  "Minutes" (preferring "(Updated)", avoiding "Agenda") was taken; alternates were left
  on PMN (notice_url reaches them).
- All fetches through `polite_fetch.py` (≥1s/host). Extraction: `pdftotext -layout`
  (79 born-digital docs; 1 image-only scan left unextracted, see status).

## Content verification (why you can trust the dates)
- **2023 council minutes print no machine-readable date header** (the date sits in an
  image letterhead), so every 2023 council doc was verified by its internal
  **minutes-approval chain** (e.g. the 10-17 doc approves the 09-19 and 10-03 minutes;
  the 04-18 doc approves 03-21; 05-16 approves 04-18 + 05-02) plus rosters (Markham/
  Hrechkosy/Dominguez = the 2023 council) and "next scheduled meeting" lines. All 18
  chain-verified. Note the approval lag varies (one or two meetings) — that is the
  clerk's pattern, not a dating error.
- **2023-07-18 gotcha:** its PMN notice (845954) carries a mis-entered event date of
  2023-06-18; the attachment is the July 18 minutes (verified in text). `index.csv`
  keys every row by the TRUE meeting date; `pmn_event_date` preserves PMN's value.
- Every doc was screened for agenda-vs-minutes content (motion language present /
  "Notice of Meeting and Agenda" header absent); the single failure is the honestly
  labeled 2025-07-17 agenda.
- `screen_corpus.py` was run over `minutes/` — see the audit trail in the repo report
  for outliers investigated.

## Cautions for whoever promotes this
- **Do not blind-merge.** Promotion means: move/convert into each dataset's
  `minutes/<year>/<week>/` convention, extend `minutes_index.csv`, delete the matching
  `minutes_unrecovered.csv` rows (17 recovered + 1 cancelled), re-run `extract_votes.py`
  + `validate_votes.py`, then rebuild motions_std/db/weeks and murray's docs
  (README/CLAUDE counts are now stale by exactly this dataset).
- The 2023 council minutes are the **approved** versions (titles embed the approval
  date) — vote grammar matches era A ("prose roll call", full names) per
  `meeting_minutes/CLAUDE.md`.
- The 2023-08-21 special meeting has **no motions** (joint discussion session) — expect
  zero votes from it.
- PC 2023+ minutes are born-digital and use the same voice-vote + roll-call grammars as
  the audited 2022 PC files.
- The cancellation-notice row (2023-07-11) and the two negative probes must NOT become
  minutes rows in the audited layer — they are provenance/gap documentation.

## Crosscheck verification note — 2026-07-17 (pmn_crosscheck flag review)
All 30 flags from `scripts/pmn_crosscheck.py murray` triaged. Wrote 1 row to
`pmn_exceptions.csv` (re-run: 30 → **29** flags, 1 suppressed, 3 pending-adoption):
- **wrong_date** 2025-09-25 — notice 1022504 filed the **2025-09-16** council minutes under
  PMN event date 2025-09-25 (attachment "September 16, 2025 Council Meeting minutes.pdf");
  the true 2025-09-16 meeting is already in `meeting_minutes/`. Cache-confirmed.
The remaining 29 (25 missing_minutes + 4 agenda_only) are LEFT VISIBLE — the pilot analysis
holds: body 735 carries the council's adjacent-series minutes the audited layer lacks. All
are **recovery leads**, none are noise:
- **Clean council-body recovery leads (minutes on PMN):** Budget & Finance Committee / Budget
  Reviews / Budget Meetings / Budget Reconciliation (2020-02-04, 2020-05-11/12, 2021-01-26,
  2021-05-05/06/07, 2022-05-11, 2023-04-25/26); Council workshops & specials — Carbon Free
  Power Project special 2020-04-16, Mixed-Use Workshop 2021-06-29, MCCD Walking Tour
  2021-10-29, Property Tax Town Hall 2022-07-13, Committee of the Whole 2022-11-15, Council
  Initiatives Workshop 2023-02-15, Short-Term Rentals Workshop 2024-08-27, Council Workshop
  2025-07-28, Council Workshop 2026-02-05. **2026-02-03**: the regular council meeting was
  CANCELLED (notice 1055579, no attachment) but a **Committee of the Whole was held** with
  minutes (notice 1055573, file 1399765.pdf) — a real COW lead, cache-confirmed.
- **Leads-with-scope-question (joint/informal bodies — NOT auto-excepted, council
  participates so not clearly out of municipal-governance scope):** City School Coordinating
  Council (2020-10-14, 2021-01-13, 2021-04-14, 2021-10-13 + agenda-only 2022-01-26,
  2022-04-13) and Legislative Breakfast 2020-01-14.
- **PC agenda-only gaps:** 2025-09-18 (3rd-Thu regular slot missing between 09-04 and 10-02)
  and 2026-02-05 — verify on PMN/CivicPlus; CivicPlus AMID=33 ends 2022-11-17, so likely
  genuine no-minutes gaps. Council coverage is current (repo through 2026-06-16).

## Crosscheck-lead RECOVERY — 2026-07-17 (20 council-body meetings PROMOTED; 5 owner-gated)
Fetched the 25 body-735 leads (file ids resolved from `list/notices.html?id=735`; all GET-
logged to `raw/_fetch_log.jsonl` with sha256, `promotion_kind`, `recovery_batch=2026-07-17-
pmn-leads`), content-verified each (pdftotext -layout; every one is FINAL/approved minutes —
past-tense narrative + adjournment + clerk sign-off; no drafts, no agenda-header mislabels,
correct body/date; the "NOTICE OF MEETING" template banner on some budget docs is followed by
"The Council met as the Budget & Finance Committee…" = minutes). **20 council-body meetings
PROMOTED** into `../meeting_minutes/` (`source=pmn`, raw copied to `../meeting_minutes/raw/
council_<date>_<fid>.pdf`, provenance headers embedded). Re-run `pmn_crosscheck.py murray
--cached`: **29 → 8 flags** (the 20 cleared; residual = the 5 owner-gated below + 2 CSCC
agenda-only + 1 PC agenda-only). Vote impact: **+2 motions / +2 rows**, both CoW tally-only
4-0 (2022-11-15, 2026-02-03); the other 18 are discussion-only sessions with zero recorded
motions (verified — no roll-call/voice-vote language; expected for budget reviews/workshops/
town halls/the walking tour/the CFPP special study session).

| date | notice | file id | meeting | motions |
|---|---|---|---|---|
| 2020-02-04 | 585155 | 590883 | Budget & Finance Cmte Mid-Year Reviews FY19-20 | 0 |
| 2020-04-16 | 599485 | 606773 | Special Meeting — Carbon Free Power Project (COVID electronic) | 0 |
| 2020-05-11 | 602795 | 622739 | Budget & Finance Cmte FY20-21 | 0 |
| 2020-05-12 | 602797 | 622741 | Budget & Finance Cmte FY20-21 | 0 |
| 2021-01-26 | 653187 | 692437 | Budget & Finance Cmte Mid-Year Review FY20-21 | 0 |
| 2021-05-05 | 674109 | 730887 | Budget & Finance Cmte FY21-22 | 0 |
| 2021-05-06 | 674117 | 730901 | Budget & Finance Cmte FY21-22 | 0 |
| 2021-05-07 | 674123 | 730905 | Budget & Finance Cmte Reconciliation FY21-22 | 0 |
| 2021-06-29 | 686441 | 752835 | Mixed-Use Workshop | 0 |
| 2021-10-29 | 712297 | 790511 | MCCD Walking Tour (Urban Design; noticed council outing, labeled Minutes) | 0 |
| 2022-05-11 | 754365 | 970997 | Budget & Finance Cmte Budget Contingency FY22-23 | 0 |
| 2022-07-13 | 767637 | 883555 | Property Tax Town Hall | 0 |
| 2022-11-15 | 793391 | 919661 | Committee of the Whole | 1 (tally 4-0) |
| 2023-02-15 | 812861 | 958011 | Council Initiatives Workshop | 0 |
| 2023-04-25 | 827353 | 979363 | Budget & Finance Cmte Budget Reviews FY23-24 | 0 |
| 2023-04-26 | 827355 | 979365 | Budget & Finance Cmte Budget Reviews FY23-24 | 0 |
| 2024-08-27 | 935465 | 1177295 | Short-Term Rentals Workshop | 0 |
| 2025-07-28 | 1011545 | 1317653 | City Council Workshop | 0 |
| 2026-02-03 | 1055573 | 1399765 | Committee of the Whole (regular council mtg was cancelled — notice 1055579) | 1 (tally 4-0) |
| 2026-02-05 | 1056367 | 1399801 | City Council Workshop | 0 |

**OWNER-GATED — verified genuine, NOT promoted (report-only; left as visible crosscheck
leads pending an owner scope decision):** the **City-School Coordinating Council** (a joint
Murray-councilmembers + Murray-School-Board body; PMN body 8101 cross-filed under 735) —
minutes 2020-10-14 (fid 709825), 2021-01-13 (709821), 2021-04-14 (770529), 2021-10-13
(809023), plus agenda-only 2022-01-26 & 2022-04-13 — and the annual **Legislative Breakfast**
2020-01-14 (fid 581539, joint council+administration). All confirmed genuine `-Minutes-`
docs; their PDFs are retained in `raw/` (prefixes `cscc_`/`legbreakfast_`) but they are NOT
municipal-council-vote records, so no vote extraction and no minutes_index promotion. These
remain in `crosscheck_flags.csv` by design until the owner rules on joint-body scope.

## Scope ruling — CSCC + Legislative Breakfast (owner, 2026-07-17)

The **City-School Coordinating Council series** (4 verified minutes 2020-10-14 /
2021-01-13 / 2021-04-14 / 2021-10-13 + 2 agenda-only dates 2022-01-26 / 2022-04-13)
and the **2020-01-14 Legislative Breakfast** are **OUT OF SCOPE** for the municipal
minutes layer (adjacent joint bodies/events, not Murray Municipal Council business).
The verified PDFs remain retained in `raw/` (`cscc_` / `legbreakfast_` prefixes) as
catalogued out-of-scope material — recoverable if scope ever expands. All 7 dates are
ledgered in `pmn_exceptions.csv` (kind=other); the crosscheck no longer flags them.
Residual murray flag count after this ruling: 1 (the genuine 2026-02-05 PC
agenda-only lead).
