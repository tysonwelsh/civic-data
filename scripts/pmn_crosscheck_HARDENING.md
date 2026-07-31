# pmn_crosscheck HARDENING log

Systemic findings harden the SHARED engine (`scripts/pmn_crosscheck.py`), never
per-city forks; per-city facts live in each city's `pmn_backfill/pmn_bodies.csv` /
`pmn_exceptions.csv`. The roster_HARDENING.md pattern. Dated entries, newest last.

## 2026-07-17 — pilot round (bluffdale / murray / herriman)

**H-1. Notice-type noise (bluffdale, 68→4 flags).** PMN bodies carry every
public-notice type, not just meetings: requests for bids, notices of quorum,
proclamations, annual meeting schedules, surplus-property notices. Fix:
`agenda_only_gap` fires only for MEETING-shaped notices (`RE_MEETINGISH` gate) and
never for the known non-meeting families (`RE_NOT_MEETING`). `missing_minutes` is
NOT gated — a minutes attachment is its own evidence regardless of title.

**H-2. Wrong PMN event dates (bluffdale "Special Meeting Agenda - May 29, 2020"
filed under event date 2020-04-29).** A date printed in the notice TITLE that the
repo does hold means the PMN event date is wrong, not the repo. Fix: title-date
extraction (`Month DD, YYYY` + `M-D-YYYY` forms) rescues such flags before emission.

**H-3. Singular/variant noise titles (murray).** "2023 Planning Commission Meeting
Schedule" (singular — the first regex only caught the plural) and COVID-era
"Determination of Risk for City Council Meetings" administrative notices. Fix:
`meeting schedule` (covers both numbers) + `determination of risk` added to
`RE_NOT_MEETING`.

**Observed, deliberately NOT engine-hardened (review-gate material, not noise):**
- Redundant council-family postings (bluffdale 373/4905/2803/2781) flag the same
  date once per body — the reviewer sees N rows for one event. Tolerable at pilot
  volumes; revisit (a `(date, repo_datasets)` dedup) if rollout reports drown in it.
- Adjacent-series minutes riding a council body (murray 735: Legislative Breakfast,
  Budget Reviews, City School Coordinating Council) are REAL minutes the repo lacks —
  scope decisions per city, so they belong in the review gate → either recovery leads
  or `pmn_exceptions.csv` rows (kind=not_minutes/other + reason), never regex
  suppression.
- `hearing` stays in `RE_MEETINGISH`: TnT/public-hearing notices with no repo record
  were the draper-specials win, and herriman's pilot surfaced a 2023 TnT hearing
  under HCSEA the same way.

## Pilot verdicts (plan step 2)
- **bluffdale (false-positive test):** 68 noise → 0 noise after H-1/H-2; the 4
  survivors verified as 3 distinct GENUINE leads (2022-08-16 combined mtg,
  2024-09-11 PC hearing month with zero repo PC minutes, 2026-02-11 regular-slot
  council date) — contradicting the dataset's own "2024-26 fully in repo" claim.
  Leads → review, not ingest.
- **murray (recall test):** PASS — recovered-minutes leads the wave missed (Carbon
  Free Power special 2020-04-16, budget-review minutes, CSCC series); the known 2026
  agenda-only recents correctly absorbed by the 60-day window (3 pending).
- **herriman (metadata-noise test):** PASS — 0 false missing_minutes despite
  council↔PC cross-filing (multi-dataset matching absorbs it); 8 review-worthy gaps
  incl. a TnT hearing under HCSEA (the draper pattern).

## 2026-07-17 — rollout round (draper / riverton / millcreek / park_city)

67 flags verified across the 4 cities → **11 genuine recovery leads, 56 exceptions, 0
false LEADS surfaced**. All exceptions are in each city's `pmn_exceptions.csv`; leads are
in the per-city `pmn_backfill/CLAUDE.md` verification sections. Candidates below are
PROPOSED (not yet implemented — owner review gate); sample counts meet the ≥5 bar unless
noted.

**C-1 (PROPOSED). Body-level cancellations invisible to `RE_CANCEL` (≥15 samples:
riverton 9, park_city 5, draper 1).** The dominant `agenda_only_gap` noise family. A
meeting's LIST title stays 'Regular Meeting' / 'Special Meeting' while the notice BODY
says 'has been cancelled' (and, draper PC 2020-03-12, list-title 'POSTPONED' — `RE_CANCEL`
has no 'postpone'). The engine only reads the list HTML, so it can't see these. Proposed
fix: for surviving `agenda_only_gap` candidates only (small N after gating), fetch the
notice page and scan the description for `cancel|postpone|rescheduled|in lieu of` before
emitting. Add 'postpone' to `RE_CANCEL` for the title-level case immediately (cheap).

**C-2 (PROPOSED). Annual meeting-schedule postings evade `RE_NOT_MEETING` (10 samples:
millcreek 6, park_city 4).** Titles: 'Planning Commission Meetings Schedule 2020',
'City Council Regular Meetings Schedule 2022', 'Annual Notice of Regular Meetings',
'2025 Regular Meetings' — plural 'Meetings Schedule' (regex has singular 'meeting
schedule') and/or synthetic Jan-1 / full-year event spans. Proposed: extend
`RE_NOT_MEETING` with `meetings?\s+schedule`, `annual\s+(notice|meeting)`,
`\d{4}\s+regular\s+meetings`; optionally treat an event date of Jan-1 spanning ~a full
year as a schedule posting.

**C-3 (WATCH — 1 sample, below bar). `RE_MINUTES_FNAME=r'minut'` substring FP.** draper
PC 2024-11-21 counted 'PC 11.21 13081 S. Minuteman Project.pdf' as minutes ('Minute' in
'Minuteman'). A correctness bug in the count_mismatch/minutes detector. Proposed when it
recurs: require a word boundary or `minutes` (plural) in the filename, or exclude tokens
like 'minuteman'. Logged as `not_minutes` exception meanwhile.

**C-4 (PER-CITY CONFIG, not engine — 10 samples: millcreek 5, park_city 3, draper 2).**
Foreign-body cross-filing: meetings ride one body's notice list but the repo files their
minutes under a different dataset — park_city joint CC+PC meetings ride PC 1860 (minutes
in `meeting_minutes`); draper PC public-hearing notices ride council 5555; early-era
(2017) millcreek council + Mayor meetings ride PC 5815. The engine already supports
`;`-joined `repo_datasets`; a multi-dataset match would auto-absorb these. Left as
explicit `pmn_exceptions.csv` rows this round (auditable; avoids the masking risk of
widening a body's `repo_datasets` — a review-gate call per SHARED-engine discipline).

## 2026-07-17 — orchestrator ADJUDICATION (post-verification, all 31 cities)

**APPLIED to the engine** (evidence-backed ≥5 samples, or correctness-grade):
- **Attachment-filename-date rescue** (17 instances / 7 cities): a missing_minutes
  flag whose minutes-attachment filenames ALL encode repo-held (or pre-floor) dates
  is a prior meeting's minutes riding a later approval notice → suppressed.
  Month-name-only filenames stay review-gate by design (not extractable).
- `RE_CANCEL` += `postpone`; cancellation now also detected in ATTACHMENT filenames
  (magna 2026-02-10, copperton 2022-01-11).
- `RE_NOT_MEETING` += potential-quorum, plural/variant meeting-schedules,
  annual-notice, meeting-rescheduled, oath-of-office-ceremony,
  anchor-location-renewal, budget-notice, disposition-of-real-property families.
- `RE_MINUTES_FNAME` word-boundary fix (`minutes?\b` — the "Minuteman Project" bug,
  C-3) + a document-extension gate (an .mp3 under a minutes label is not a record).

**DEFERRED, with reasons:**
- Notice-body fetch for body-level cancellations (C-1 full form): adds per-flag
  fetch cost; the ≥15 current instances are ledgered; revisit after a refresh cycle
  shows recurrence.
- count_mismatch combined-doc suppression: REJECTED as an engine change — ogden's 9
  count_mismatches were GENUINE finds (the reverse-combined pattern); SLC's 21
  architecture-noise cases are correctly ledgered per city. Suppressing the class
  would have hidden real recoveries.
- `repo_datasets` widening for foreign-body cross-filing (C-4): stays a per-city
  review-gate call (masking risk).
- Site-tour/work-session-tour notices (sandy): too meeting-shaped to regex-suppress.
- The SSL no-quorum minutes misread is an INGESTION-side detector gap
  (pmn_backfill promotion tooling), not this engine — queued in TODO.

**Post-hardening steady state (--all --cached, 2026-07-17): 640 → 317 flags** — the
residual IS the verified genuine-leads inventory (park_city + sandy clean; SSL 1;
biggest: CH 44, WJ 29, murray 28, lehi 28 — all verified real coverage holes). These
persist by design until recovered or ledgered; the consolidated leads record lives in
TODO.md + each city's pmn_backfill/CLAUDE.md verification section.

## Rollout verdicts (2026-07-17)
- **park_city:** 14 → 0 leads (all exceptions) — CONFIRMS the CivicClerk superset claim.
- **millcreek:** 17 → 3 leads (2017 PC work sessions + a 2019 council special); the rest
  are cross-filing / schedules / a field-trip / a wrong-year event date.
- **riverton:** 18 → 6 genuine agenda-grade leads (real held meetings the PMN+Granicus
  harvest missed) + 12 body-level cancellations — contradicts its '0 still-missing' claim.
- **draper:** 18 → 2 leads (2020 council retreat + a 2020-09-01 council meeting) + 16
  exceptions (11 benign count_mismatch families + 5 hearing-notice/postponed/cross-file).

## Q3-2026 post-refresh hardening (2026-07-19)
- **RE_CANCEL += 'reschedul'** — the "Meeting Rescheduled" notice family (st_george ×5) is a
  non-meeting the same way a cancellation is.
- **Notice-body/description cancellation check** — before emitting an `agenda_only_gap`, the
  engine now fetches the notice DETAIL page(s) (≤3 per would-be flag; cached; polite — cost is
  a handful of requests per city since flags are rare) and scans the tag-stripped page text
  with RE_CANCEL. Root cause: cancellations frequently live ONLY in body prose or the
  description field (6 confirmations: taylorsville 2020-02-11, logan, midvale ×3, west_jordan
  COVID ×2, riverton, nephi 2024-07-10/2025-07-09 description-field). Reported as
  "auto-suppressed as cancelled (notice-body/description text)" in the report.
- **Cross-body (date, dataset-set) dedup** — a date already flagged by a sibling body mapping
  to the SAME repo_datasets is not re-flagged (logan's RDA body duplicated every council-body
  date — the RDA rides the same combined doc). Counted under suppressed.
- **nephi config**: council body 1788 `repo_datasets` widened to
  `meeting_minutes;planning_commission` — PC notices are cross-filed under the council body
  (3 confirmed instances); the multi-dataset mapping was already supported by the engine.
- Regression: nephi/logan/st_george/taylorsville/cottonwood_heights re-run `--cached` → all
  0 flags, no new classes, suppression counts stable.
