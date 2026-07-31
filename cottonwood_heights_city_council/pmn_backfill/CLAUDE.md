# pmn_backfill/ — Cottonwood Heights (Utah Public Notice cross-check + recoveries)

A **full-history, all-body Utah Public Notice (`utah.gov/pmn`) sweep** of Cottonwood Heights
(entity **111**), diffed against the repo's already-unioned minutes to find what the original
build missed — plus the recovered files for those dates. **Additive and separate**: it never
touches `meeting_minutes/` or `planning_commission/`. Built by `/expand-city-sources` (source 4).

```
raw/                     16 recovered minutes PDFs, verbatim (+ _fetch_log.jsonl provenance)
text/                    pdftotext -layout sidecars (one per raw PDF)
index.csv                §9 pmn_backfill contract header (+ orig_filename)
coverage.md              per-year × body × source diff table + separate-body inventory
AVAILABILITY.md          what was checked, recovered, and deliberately left (scope boundary)
chpmn_parse.py           notices_<body>.html -> _work/attachments_all.csv (filename-based minutes detect)
chpmn_diff.py            classify by filename + per-date diff vs repo council/PC indexes
chpmn_build.py           select the genuine-gap recover set -> _work/recover_manifest.csv
chpmn_index.py           recover_manifest.csv -> index.csv
_work/                   scratch (fetched notices HTML, attachments CSV, manifest, fetch batch)
```

## Why this is (correctly) a near-empty result
Cottonwood Heights' core minutes were **already a portal (CivicEngage) ∪ PMN union** — the
original build resolved **council body 2147** and **PC body 2148** and backfilled 2020–2024 from
PMN. This dataset is the *cross-check*: sweep **every** body, detect minutes by **filename** (not
the mislabeled PMN type labels), classify each doc so cross-filed docs diff against the right body,
and diff on **meeting date** (±4d), not per-year counts.

**Findings:**
- **Council session (2147): a complete superset — 0 genuine gaps 2020+.** In-session CDRA has no
  separate PMN body (it rides inside the council minutes).
- **Planning Commission (2148): 1 genuine missing meeting — 2022-07-06** PC Work Meeting.
- **Administrative Hearings (3287): 15 missing 2020–2023 sessions.** The repo's PC dataset scope
  includes admin-hearing-officer minutes (`body=PlanningCommission, slug=administrative-hearing`);
  it only had 2024+ before. These carry **no roll-call votes** (0-motion land-use hearings).
- **16 docs recovered total**, all born-digital (`format=text`).

## Body ids (entity 111)
`2147` City Council · `2148` Planning Commission · `2150` Architectural Review Commission ·
`3085` Board of Adjustments · `3287` Administrative Hearings · `7091` Appeals Hearing Officer ·
`6511`/`9027`/`9035`/`8699`/`9491` (agenda/notice-only — 0 minutes).

## Separate-body inventory (NOT recovered)
`2150` **ARC** (13 in-window minutes dates 2020–2023) and `7091` **Appeals Hearing Officer**
(9 in-window dates) are real bodies the repo does not model — inventoried in `coverage.md` as
candidate future datasets, out of this backfill's council/PC scope. `3085` **BOA** minutes are all
pre-2018 (below the 2020 floor).

## index.csv schema (§9 pmn_backfill contract)
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method` + `orig_filename`.
`path` is dataset-relative including `raw/`. `body=PlanningCommission`; `slug ∈
{planning-commission, administrative-hearing}`; `pmn_body_id ∈ {2148, 3287}`; `format=text`;
`extraction_method=pdftotext-layout`.

## Merging — ✅ PERFORMED 2026-07-16
All 16 docs were folded into the audited PC layer exactly as prescribed: re-slugged into
`planning_commission/minutes/<year>/<week>/<date>_<slug>.md`, indexed (`source=pmn`,
`format=pdf-text`), raws copied to `planning_commission/raw/pmn_<date>_<slug>.pdf`
(sha256-verified), re-extracted (`extract_votes.py --force`), and the city derived layers
rebuilt (motions_std / db / referrals / weeks / sources). Vote rows from the promoted docs
carry **`provenance=pmn_minutes`** (documented trailing 14th column; the doc set lives in
`PROMOTED_PMN_BACKFILL` in `planning_commission/extract_votes.py`). Net delta: **+6 motions /
+12 vote rows**, all from the 2022-07-06 PC doc (one combined work+business meeting PDF); the
15 admin hearings are legit 0-motion. The 2023-03-01 doc's in-body header-year "2022" is a
clerk typo (true date 2023-03-01 — footer + CUP-23-xxx cases + weekday). This dataset's own
files are retained unchanged as the recovery record.

## Cross-check flag verification — 2026-07-17 (pmn_crosscheck.py)
The mandatory-refresh `scripts/pmn_crosscheck.py cottonwood_heights` run emitted **48 flags**
(41 agenda_only_gap + 7 missing_minutes). Every flag was verified → **4 suppressed to
`pmn_exceptions.csv`, 44 remain as live recovery leads** (39 agenda_only + 5 missing_minutes).

**Headline finding — the "Council: complete superset, 0 gaps 2020+" claim above is
CONTRADICTED for the PC/Council series.** The cross-check surfaced substantial GENUINE
meeting gaps the portal∪PMN union missed, chiefly a full **PC hole across 2024-02→2024-10**
(the repo PC index jumps 2024-01-17 → 2024-11-06; PMN carries agendas for 10 monthly PC
meetings + the paired Administrative Hearings in between), plus **Dec-2022 council**
(11-15 → 2023-01-03), scattered PC first-Wed dates (2020-02-05, 2021-02-03/06-02/07-07,
2022-10-19/12-07), a **2020-10-06 council** meeting, joint PC/CC work sessions
(2022-07-20, 2025-12-02), and **Oct–Dec 2025 + 2026 PC** dates. These are agenda-grade
(PMN holds only agendas, no minutes) — meetings are confirmed noticed; minutes are NOT on
PMN and must be sought on the city CivicEngage archive / via GRAMA. Escalated as a coverage
gap (the dataset's superset claim should be scoped to "through ~2023" for PC).

**5 missing_minutes recovery leads (PMN holds real minutes the repo lacks):**
2021-01-27 Admin Hearing (verified: "012721 CH Admin Hearing.pdf" = approved minutes),
2021-03-03 PC ("030321 CHPC - Approved Minutes.docx"), 2022-01-25 Council Retreat
("012522 CHCC Retreat-APPROVED.pdf"), 2022-12-07 Admin Hearing ("120722 - Approved
Minutes.pdf"), and **2023-03-08 PC** (verified: "030823 CHPC Mtg Approved Minutes.docx" +
agenda + packet + CUP-23-002 — a full business meeting, likely carries votes).

**4 exceptions written:** 2021-10-20 PC (wrong_date — attached minutes are the 2021-10-06
admin hearing already in repo), 2023-02-16 Council (not_minutes — file is an agenda),
2024-04-25 (other — town-hall attendance/quorum notice), 2025-04-21 (other — Monday
annexation public-hearing notice, not a meeting date). Re-run: **48 → 44 flags, 4 suppressed.**

### Promotion of the 5 missing_minutes leads — ✅ PERFORMED 2026-07-17
All 5 fetched from PMN (polite, ≥2s), content-verified against the source PDF/.docx, and
promoted into the audited layer (`source=pmn`; raws retained under each dataset's `raw/` as
`pmn_<date>_<slug>.{pdf,docx}`; fetch provenance appended to the dataset `raw/_fetch_log.jsonl`):
- **2021-03-03 PC** (docx, file 707327) → `planning_commission/` — Work + Business meeting;
  named roll SPL-21-002 + 3 unanimous-consent motions. ⚠ **The SPL-21-002 roll is printed as
  bare "Firstname Lastname-Aye" with NO role prefix, so `PAIR_RE` (which requires
  Commissioner/Chair/Council-Member) captured only "Chair Chris Coutts" (1 of 7 ayes)** — a
  pre-existing parser-format limitation, not a data error (outcome "Passed unanimously" correct;
  full roll preserved in the minutes text/FTS). Queued as a corpus-wide follow-up.
- **2023-03-08 PC** (docx, file 970227) → `planning_commission/` — Work + Business meeting;
  full named roll (6) on the CUP-23-002 TABLE motion + unanimous-consent motions, all captured.
- **2021-01-27 & 2022-12-07 Administrative Hearings** (pdf, files 684411/924987) →
  `planning_commission/` (`slug=administrative-hearing`) — legit **0-motion** hearing-officer
  decisions (Michael Johnson "moves to APPROVE" his own decisions, no roll/result).
- **2022-01-25 Council Retreat** (pdf, file 828275) → `meeting_minutes/` — consensus/direction
  retreat; 1 unanimous-consent adjourn motion only (blank-member procedural).

Blank "Minutes Approved: ___" signature lines on the two docx PC files are NOT a draft signal —
29 of 57 already-audited PC minutes leave that field blank (verified). All content-verified as
genuine approved minutes with matching dates/weekdays (no drafts, no agenda mislabels).
**Vote rows from all 5 carry `provenance=pmn_minutes`.** The council `all_votes.csv` gained its
first-ever trailing 14th `provenance` column here (the first council doc PMN-promoted). Extractors
re-run (`extract_votes.py --force` both datasets); `validate_votes.py` clean (PC tally_mismatch=0;
council tally_mismatch=3 = the 3 pre-existing documented clerk errors, unchanged). Net delta:
**PC +15 vote rows (0-motion admin hearings aside) / council +1 row.** Backups:
`_backups/2026-07-17-pmn-leads-recovery/cottonwood_heights/`. Derived layers (motions_std / db /
weeks / cities.db) intentionally NOT rebuilt — deferred to the orchestrator's single federation.

## Reproduce
`python3 chpmn_parse.py && python3 chpmn_diff.py && python3 chpmn_build.py` then fetch
`_work/fetch_batch.txt` via `polite_fetch.py --batch`, `pdftotext -layout` each raw into `text/`,
and `python3 chpmn_index.py`. Notices are refetched with the cumulative
`https://www.utah.gov/pmn/list/notices.html?id=<body>&page=200` GET.

## 2026-07-17 (wave 2) — agenda-grade flag RESOLUTIONS
The escalated coverage holes are dispositioned:
- **2024-02→10 PC hole: CLOSED** — all 9 PC meetings + paired Admin Hearings recovered LIVE
  from the CMS (delisted from the listing page but still served by document ID; anchors came
  from Wayback captures of the listing — `pmn_backfill/work/wayback_ch_anchors*.json`).
  +2022-03-09 AH, 2022-10-19 PC (new contested 5-to-1), 2022-07-20 joint WS (in-body a
  COUNCIL work session → filed in meeting_minutes/, the 2025-10-21 precedent), and
  2020-10-06 council (Wayback bytes, provenance=wayback_minutes).
- **Dec-2022 council (12-06, 12-13): GENUINE GAP** — absent from the live portal (window
  reaches 2022-06-21), absent from every Wayback capture (incl. 2023-05-13), PMN agenda-only
  → meeting_minutes/minutes_unrecovered.csv, GRAMA-only.
- **8 PC/AH dates purged + never archived** (2020-02-05, 2020-03-12, 2020-08-12, 2021-02-03,
  2021-02-17, 2021-06-02, 2021-07-07, 2021-10-20) → planning_commission/minutes_unrecovered.csv.
- **2019 PC/AH minutes exist on Wayback** (anchors captured in work/wayback_ch_anchors2.json)
  but sit below the 2020 data floor — available if the floor is ever lowered.
