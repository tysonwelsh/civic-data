# Vineyard City Council — data repository

Canonical datasets about the **Vineyard City Council** (Utah County — a fast-growing city
on the east shore of Utah Lake), modeled on the Salt Lake City reference repo, plus a
derived weekly view. Built by the `build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 172 files 2020–2026 incl. 9 RDA board) + roll-call votes (all_votes.csv)
public_comments/      all_comments_clean.csv (EMPTY — written comments are email-only, not published)
                      + minutes_speaker_log.csv (in-person speaker notes, NOT comments) + AVAILABILITY.md
election_results/      Utah County results — RCV (2019/21/23) + plurality (2025)
geo/                  city-limits polygon -> in/out-of-city check (council is at-large, no districts)
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday, modal)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Wednesday, modal — meeting days vary)**.
Votes + minutes carry the meeting date. `build_weeks.py` buckets every record onto that
weekly grid. Elections are point-in-time and NOT in the weekly bundles.

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (5,240 member-vote rows).
  There is **no** public-comments dataset (Vineyard publishes none — email-only); the
  in-person `public_comments/minutes_speaker_log.csv` (283 rows) is record-notes, not
  public-submitted comments.
- **Meeting-level / contextual**: the `weeks/<wed>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/vineyard_races.csv`) ↔ votes.
- **By geography**: `geo/address_to_district.py` returns in/out of city limits (at-large —
  no districts).

## Council structure
**Mayor + at-large councilmembers, NO districts.** Mayor+4 council 2020–2025, growing to
**Mayor+5 from 2026** (2024 ballot Prop 10). **Mayor Fullmer (2020–2025) was named in
roll-calls and voted** (988 rows, incl. dissents). From 2026, the clerk records only the
councilmembers by name in roll-call runs, so **Mayor Stratton presides but is not captured
as a named voter** (0 vote rows — he is present via attendance; not back-filled, as the
minutes never name him in a vote). So the per-meeting voter count is 5 (2020–25) and 5
named councilmembers in 2026.

## Data notes / caveats
- **Minutes 2020–2026, with a documented gap**: 172 recovered (26 of the original 29
  "image-only packet" meetings carried a text layer and were recovered locally); only
  **3 meetings unrecoverable** (corrupt media-wrapper minutes files — listed in
  `meeting_minutes/minutes_unrecovered.csv`). 3 files are OCR (2020-09-23 + two 2026).
- **Votes**: 1,076 motions / 5,240 rows; 51 contested (4.7% — a high-consensus council). A
  post-build repair added the `VOTED IN FAVOR` phrasing (recovered ~160 Aye rows incl. Mayor
  Fullmer's). The one validation flag (2024-05-08) is a clerk tally typo, not a parse error.
  Tally-only motions carry `names_recorded:false`.
- **Elections — two methods**: 2019/2021/2023 used **ranked-choice voting** (rcvis.com
  round data; citywide only — no precinct splits); 2025 reverted to **plurality vote-for-N**
  (precinct detail). `is_winner` reflects actual RCV seat winners, not first-choice rank.
  See `election_results/CLAUDE.md`.
- **Comments**: Vineyard does NOT publish written comments (email-only to the City Recorder;
  `publicCommentsEnabled` false on all council events). `all_comments_clean.csv` is empty by
  design; see `public_comments/AVAILABILITY.md`. In-person speakers → `minutes_speaker_log.csv`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission` (the appointed technical land-use filter). The `result` string encodes the
  **recommendation-vs-final-action taxonomy**: recommendations forwarded to Council vs final actions
  (CUP/site-plan that never reach Council).
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys **resolved from prose** and **body-scoped** — `0
    applications span >1 body`. Vineyard's **ALL-CAPS, name-poor minutes** mean almost every
    application is a `singleton`(high); the `name`(medium, heuristic) tier barely fires (just 2 motions).
    3 bodies · 310 applications · 1,610 motions · 7,806 votes. Motions: Council 1,040 · PC 352 · RDA 218
    (RDA 15 council-embedded + 203 promoted standalone RDA-board minutes; provenance='pmn_minutes').
    PC stages: 53 recommendations (52 positive / 1 negative) + 299 final actions.
    (2026-07-31: −10 motions / −34 votes — the phantom PC 2023-04-19 duplicate removed, see
    `planning_commission/CLAUDE.md` + `VERIFICATION.md`.)
  - *Cross-body `referral` is RECONSTRUCTED + scored + GENERALIZED* — keyed `primary_body←related_body`
    (covers Council←PC / Council←RDA / PC←RDA). Small, high-consensus town → **9 links, all
    medium/subject, all Council←PlanningCommission** (RDA shares no linkable text → 0 agency links);
    7 of 37 council land-use items linked, the rest honestly unlinked. **`medium` spot-check before
    quoting.** Use `v_referral_chain` / `v_project_timeline`; correct mistakes in `db/overrides.csv` /
    `db/referral_overrides.csv` and rebuild (idempotent).

## Analysis guidance
- **Contested votes (any Nay/Abstain) are the signal**; `weeks/<wed>/summary.md` surfaces
  them. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) reports CivicClerk meetings newer than each
  dataset's `minutes_index.csv` max date; `--fetch [--dataset <name>]` downloads new minutes
  (plainText stream; original PDF retained under `<dataset>/raw/`), appends index rows, and runs
  extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
- After any fetch, rebuild derived layers: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-05)
Six new source layers (portal family: **CivicClerk OData** `vineyardut.api.civicclerk.com/v1` + PMN +
YouTube); each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify existing data. Join to
`all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **926 rows INDEX-ONLY** (Council 432, PC 336, RDA 158): 807 agendas + 119 packets, ~7.2 GB
  catalogued. Fetch via `Meetings/GetMeetingFileStream(fileId,…)`. NOTE: CivicClerk `$top` is a hard result
  cap (silent truncation) — page unbounded `Events`.
- **`housing_plans/`** — 2019 General Plan + Future Land Use Map; **MIH element = GP chapter, updated by
  Ord 2022-17** (2022-09-14); state 23/24/25 + SB 34. FrontRunner Station Area Plan still in progress.
- **`ordinances/`** — **84 ordinances** (18 land-use). Minutes cite numbers → within_source backbone (79);
  **4 high** (signed PDFs from PMN). Code host `municipalcodeonline.com` (JS-gated). Ord 2021-12 flagged
  missing from `all_votes.csv`.
- **`pmn_backfill/`** — **separate** from audited minutes. Entity 294; Council 530 / PC 531 / **RDA 2598**.
  **79 RDA dates recovered** (59 in the 2026-07-05 run + **20 oversize-deferred RDA minutes fetched uncapped
  2026-07-19**, TODO follow-up (a); all promoted with `provenance='pmn_minutes'`). PMN purges old blobs
  (198/296 listed minutes 404). The remaining `oversize-not-fetched` docs are 10 CC-body packets only;
  per-doc RDA dispositions in `pmn_backfill/oversize_rda_ledger.csv`.
- **`transcripts/`** — **ASR** captions, sample-only (owner policy): 10 sampled / 47 videos mapped on YouTube
  "Vineyard City". NEVER authoritative. **Video exists only 2019-09 → 2020-12** (COVID livestream era).
- **`campaign_finance/`** — **59 filings** (2015–2025), self-hosted (legacy via Wayback). **100% in-scope
  election join**; extends named coverage 2 cycles below the 2019 floor. **2023 cycle unrecoverable** (purged;
  election winners still known); 2025 general candidates filed no finance statements. Line-items live only in
  `text/` sidecars — structured `contributions.csv` is the separate planned derived layer.
