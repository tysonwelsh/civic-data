# pmn_backfill — Vineyard Utah Public Notice minutes/agenda backfill

**Additive dataset. Never edit the audited minutes layer.** This directory recovers
meeting DATES that exist on the Utah Public Notice Website (PMN) but are MISSING from
the repo's minutes indexes (`meeting_minutes/minutes_index.csv`,
`planning_commission/minutes_index.csv`). It never modifies those files or their
`minutes/` markdown.

## What's here

- `raw/` — every recovered original, verbatim, named `<BODY>_<bodyId>_<fileId>.<ext>`
  (BODY ∈ CC/PC/RDA). `raw/_fetch_log.jsonl` is the provenance log (one JSONL line per
  fetch: url, status, bytes, sha256, retrieved_utc).
- `text/` — extracted plain text per recovered PDF (screening/reading copy).
- `index.csv` — one row per recovered/candidate document. Superset of the
  `minutes_index.csv` schema plus `body`, `extraction_method`, `path`,
  `internal_meeting_date` (date printed INSIDE the PDF), `notice_dates`, `status`.
- `coverage.md` — per-year gap table (repo vs PMN vs recovered vs still-missing), per body.
- `AVAILABILITY.md` — confirmed PMN entity id (294) + body ids, and the crawl method.

## The one rule that matters here

**Notice Event Date ≠ the meeting date of its minutes attachment.** PMN files minutes
against the *following* meeting's notice, and cancelled-meeting notices re-attach the
prior real minutes. So recoveries are keyed on `internal_meeting_date` (read from the
PDF), deduped by that date per body — NOT on the notice date. `status` values:
- `recovered` — genuinely missing from the repo; promoted here.
- `duplicate-not-promoted` — internal date already covered by the repo (or by another
  recovered row); kept for provenance, not a new meeting.
- `oversize-not-fetched` — PMN attachment exceeded the 8 MB fetch cap; logged as
  available, body not stored. **All 38 (28 RDA + 10 CC) were resolved 2026-07-19** —
  the RDA family is now fetched uncapped (see the 2026-07-19 section); the surviving
  status value applies only to the 10 CC docs still deferred.

## Scope

Window 2014–2026. Repo minutes begin 2020, so the real recovery is the pre-2020 tail
(CC 2015–2019, PC 2015–2018) plus the Redevelopment Agency (body 2598), which the repo
has no layer for at all. 2020–2026 is essentially a repo superset — near-zero CC/PC
gaps there (any hits are notice-date-pitfall false positives, verified by internal
date).

## Rebuild

Not a generated layer — one-shot recovery, as-of 2026-07-05. To refresh, re-walk the
chain in `AVAILABILITY.md`, re-fetch via `scripts/.../polite_fetch.py` (GET-only,
throttled, browser UA), re-diff against the current `minutes_index.csv` files. Validate
with `.claude/skills/expand-city-sources/scripts/validate_dataset.py`.

## 2026-07-17 — final PMN-crosscheck flag verification (8 flags -> 5)

Verified all 8; appended 3 exceptions; re-run (--cached) 8 -> **5**. None were the oversize
deferred-RDA-minutes family (all 8 are agenda_only_gap council/PC notices with NO minutes attachment).
- **Recovery leads (5, agenda-grade):** PC 2020-01-31; council specials 2021-09-15, 2023-12-18,
  2025-11-18; council regular 2025-11-12.
- **Exceptions (other x3):** 2024-06-20 + 2024-07-18 Town Hall Meetings (informal, non-minuted);
  2024-09-17 Town Hall 'Postponed' (verified via notice: postponed to date TBD, did not occur).

## 2026-07-19 — the 28 oversize-deferred RDA minutes fetched uncapped (20 promoted)

TODO "Vineyard follow-up (a)" residue. The 2026-07-05 run skipped 28 in-window RDA docs on
an 8 MB cap; re-fetched each uncapped from `https://www.utah.gov/pmn/files/<fileId>.pdf`
(politely throttled, browser UA), into `raw/RDA_2598_<fileId>.pdf` (13–101 MB — the size is
embedded exhibits; the minutes pages themselves are born-digital text, no OCR needed).
Full per-doc disposition ledger: **`oversize_rda_ledger.csv`**.
- **All 28 still live on PMN** (HTTP 200, application/pdf) — no purge.
- **20 verified net-new standalone RDA board minutes** — in-body header confirms a Vineyard
  Redevelopment Agency Board Meeting for the labeled date (dates 2021-01-13 … 2024-06-26;
  1140605/2023-12-27 is a real RDA *Special Session*). `status='recovered'`, promoted via
  `meeting_minutes/extract_backfill_votes.py` (`provenance='pmn_minutes'`).
- **8 not promoted (`duplicate-not-promoted`, not re-fetched):** 7 dates already carry
  audited primary RDA minutes (2024-08-28, 2025-01-29/02-12/04-30/05-28/06-11/06-25); 1
  (2021-01-27, fileId 1192525) already recovered as `pmn_minutes` from fileId 690583.
- **Deltas** (additions-only, proven at row/motion/motions_std level; 0 removed, 0 changed):
  RDA dates 47→67, RDA motions 147→218 (+71), RDA member-vote rows 706→1058 (+352). db
  reconciles exactly; `validate_city` 25 PASS / 1 WARN (documented `provenance` col) / 0 FAIL.

## 2026-07-17 (wave-2) — the 5 agenda-grade leads resolved (0 recovered)

Probed each lead on CivicClerk (`vineyardut.api.civicclerk.com/v1/Events`) + PMN notice page +
`/pmn/files/<id>`; verified in-body. **No real recorded minutes exist for any of the 5** — none
were recoverable.
- **2 cancelled -> exception ledger:** CC 2021-09-15 (notice 702677 body 'This notice has been
  cancelled'; CivicClerk 'Special Session - Cancelled') and CC 2023-12-18 (notice 961587 'This
  notice has been cancelled'). Meetings did not occur.
- **1 notice-date artifact -> exception ledger:** PC 2020-01-31 (notice 585187 Start Date 01-31
  carries ONLY the 2020-02-05 PC agenda, file 570323; no 01-31 event on CivicClerk; the 2020-02-05
  minutes are already in the repo, fileId 824). No separate 01-31 meeting.
- **2 genuine held-but-unpublished gaps -> meeting_minutes/minutes_unrecovered.csv:** CC 2025-11-12
  (regular, event 1203) and CC 2025-11-18 (special, event 1385). Both HELD (not cancelled) but only
  Agenda/Agenda-Packet published on both channels — no Minutes file anywhere. GRAMA the two minutes
  files (see wave-2 report). These are the residual coverage hole in the Nov–Dec 2025 council run
  (which also holds the corrupt 2025-12-10 wrapper).
