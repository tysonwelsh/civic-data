# Logan City Council — data repository

Canonical datasets about the **Logan Municipal Council** (Cache County, Utah), modeled on the SLC
reference repo, plus a derived weekly view. Built by `build-city-data-repo`. Data floor: **2020**.
Independent QA: `VERIFICATION.md` (**PASS**).

```
meeting_minutes/   198 minutes (149 Council + 49 RDA, Revize) + roll-call votes (all_votes.csv)
planning_commission/  130 PC minutes (52 OCR) + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                   (appointed technical land-use body; recommendations vs final actions)
db/                NORMALIZED RELATIONAL DATABASE (db/civic.db SQLite + table CSVs) joining ALL bodies'
                   votes by real keys + generalized cross-body referral layer. Start here: db/SCHEMA.md
public_comments/   all_comments_clean.csv (EMPTY) + minutes_speaker_log.csv (633 in-person, NOT comments)
election_results/   Cache County results, Logan mayor + at-large council
geo/                city boundary + 25 precincts + address->in-city-limits tool (at-large)
weeks/              DERIVED weekly bundles (build_weeks.py: CITY="Logan", MEETING_WEEKDAY=Tuesday)
recon.md / VERIFICATION.md
```

## How to analyze
- **Votes**: `meeting_minutes/all_votes.csv` — 789 motions / 2,820 rows. Filter `body` for Council
  (754) vs **RDA (35)**. Per-member roll-calls (`Name: Aye/Nay`); tally-only "carried unanimously"
  → `names_recorded:false`. 28 contested.
- **Two Andersons**: Amy Z. Anderson (council 2021) and Mark A. Anderson (council 2019/2023, Mayor
  2026+) are DISTINCT — don't merge. The Mayor does not vote.
- **No genuine public comments** (in-minutes-only); the 633 `minutes_speaker_log.csv` rows are
  in-person paraphrases, NOT a comments dataset.
- **By person**: join `election_results/logan_races.csv` winners ↔ votes. **By geography**:
  `geo/address_to_district.py` → inside/outside city limits (no districts).

## Council structure
**Mayor + 5 all-at-large (0 districts).** Separately-elected **Mayor does NOT vote** (veto). Meets
1st & 3rd Tuesdays. The RDA convenes as a same-night recess (own roll-calls) → `body=RDA`.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **549 motions across 130 meetings**; roster of **15 appointed
  commissioners** in `planning_commission/roster.csv` (built from attendee headers — no election).
  The `result` string encodes the **recommendation-vs-final-action taxonomy**: `Positive/Negative
  recommendation` (forwarded to Council — **112**, of which 86 Positive / 26 Negative) vs final
  actions (design review / CUP / subdivision — never reach Council — **437**). **52 of the 130 PC
  minutes are scanned OCR**, so a fraction of PC parsing is noisier than the born-digital council set.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no file number exists in
    Logan) and **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high). All 7 `name` apps are PC; all 51
    Council land-use apps are `singleton` (council motion text is bare, e.g. "adopt Ordinance NN-NN as
    presented").
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — keyed `(primary_application_id,
    primary_body, related_application_id, related_body, match_method, confidence, …)`, modeling
    Council←PC, Council←RDA and PC←RDA. **Logan's layer is honestly EMPTY (0 links):** the only
    candidate matches were boilerplate-only Council←RDA pairs (shared token "presented", now stopworded
    so they no longer form); no real PC→Council signal exists because council/RDA motion text lacks
    project identity. To add genuine links, hand-author `link` rows from the minutes + rerun
    `build_referrals.py`.
  - **Logan address nuance:** a "shared address" is an approximate **grid intersection**, not a parcel
    (co-location only); only 1 application carries a parseable address, so the signal is inert here.
  - Build: `python3 db/build_db.py` then `python3 db/build_referrals.py` (idempotent; INTEGRITY OK).
    Use `v_referral_chain` / `v_project_timeline` / `v_member_record`. **6 people sit on both Council
    and RDA** (the RDA board *is* the Council) — unified by name in `person`/`role`.

## Data notes
- **`body`**: `Council` / `RDA`. RDA = the Logan Redevelopment Agency recess segments (split into
  their own `redevelopment-agency-meeting` files).
- **Elections**: at-large, no RCV; Logan self-administered 2019/2021 (county took over 2023); 2023
  ran under a Cache County integrity investigation + recount (certified figures used; winners
  unchanged). See `election_results/CLAUDE.md`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Known bugs / manual repairs
- **2026-07-02 — council/RDA split boundary bug (manually repaired).** The acquisition-time
  splitter that cut same-night RDA recesses into their own files (script not retained in this repo;
  see `meeting_minutes/extract_votes.py` docstring) mis-assigned the document tail for the
  2026-05-12 budget workshop ("26May12 Budget Workshop.pdf"): the RDA file ended mid-sentence at
  "…Redevelopment Agency adjourned at" while the closing "7:55 p.m.", the "Teresa Harris, City
  Recorder" signature, and the page-20 footer were left in the council file. Repaired manually on
  2026-07-02 by moving those 10 lines from
  `meeting_minutes/minutes/2026/2026-05-11/2026-05-12_city-council-meeting.md` to
  `…/2026-05-12_redevelopment-agency-meeting.md` (verified verbatim against the source PDF), then
  rerunning `build_weeks.py`. Backups: `../_backups/2026-07-02/`. If other split files end
  mid-sentence, suspect the same off-by-tail boundary bug.

## Refreshing (incremental updates — Phase 3.3)

- `python3 fetch_new.py --probe` (default; read-only) reports minutes newer than each index's max
  date on the two Revize listing pages (council `minutes.php`, PC comdev `minutes.php`);
  `--fetch [--dataset <name>]` downloads them into `<dataset>/raw/`, converts, appends index rows,
  and runs extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
- CAVEAT: new council PDFs may embed an RDA tail — review/split before extraction (see the
  fetch_new.py header and "Known bugs" above).
- After any fetch, rebuild: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-05)
Six new source layers (portal family: **Revize static CMS**, no API — files on `cms9files.revize.com/loganut/`;
+ PMN + YouTube); each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify existing
data. Join to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **1,124 rows INDEX-ONLY** (Council 1,096, RDA 28): 222 agendas, **867 separated
  staff-report PDFs**, 11 proclamations, 24 notices. Unlike St. George's bundled packets, Logan serves
  per-item staff reports. Live `source_url` + partial `size_mb`; `stored_locally=no`.
  - **doc_class layer + THE fetch→extract→discard run** (2026-07-16): 213 classified (staff_report
    207 / plan_amendment 6), 48 ok / 165 needs_ocr / 0 404s; 818 MB fetched→discarded, 2.7 MB text
    kept. **needs_ocr cleared 2026-07-17 by the repo-wide vision pass** (all 165 rows now `ok`,
    `extraction_method='claude_vision'`: sha256-verified re-fetch → 150 dpi render → Read-tool
    verbatim transcription; imagery pages carry honest inline markers) — see packets/CLAUDE.md.
- **`housing_plans/`** — **Logan 2045 General Plan (2026)** + a **standalone 2022 MIH Plan (Res 22-46)**
  and the GP-embedded element; 2018 biennial; state 23/24/25 + SB 34.
- **`ordinances/`** — **496 items** (167 ord + 329 res; 143 land-use). **Independent archive** — City
  Recorder `ordinances.php`/`resolutions.php` (signed PDFs) — so **461 rows are `high`** (two-source
  corroborated), 11 within_source, 24 none. 3 land-use ords flagged missing from `all_votes.csv`.
- **`pmn_backfill/`** — **honest zero** (repo minutes are a complete superset of PMN every in-window
  year). Entity 189; Council 494 / PC 487 / RDA 495 (the recon's RDA=1277 was wrong — that's SLC's).
- **`transcripts/`** — **ASR** captions, sample-only (owner policy): 10 sampled / 155 videos mapped on
  YouTube "City of Logan" (`/streams` tab). NEVER authoritative. Hard 2020 video gap.
- **`campaign_finance/`** — **45 filings** (13 candidates) from the city recorder election page.
  **100% election join.** 2025 complete; 2021 via Wayback; **2023 provably unrecoverable**; 2019 never
  published. 2021 winner Ernesto López published no statement (flagged). Line-items live only in `text/`
  sidecars — structured `contributions.csv` is the separate planned derived layer.
