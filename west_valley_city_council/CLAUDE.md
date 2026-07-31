# West Valley City Council — data repository

Canonical datasets about the West Valley City Council, modeled on the Salt Lake City
reference repo, plus a derived weekly view unifying minutes + votes + comments. Built by
the `build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 465 files 2020–2026) + roll-call votes (all_votes.csv)
planning_commission/  PC minutes + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                      (the appointed technical land-use body; recommendations vs final actions)
db/                   NORMALIZED RELATIONAL DATABASE (db/civic.db SQLite + table CSVs) joining ALL
                      bodies' votes by real keys + reconstructed PC→Council referrals. Start: db/SCHEMA.md
public_comments/      all_comments_clean.csv (EMPTY — WVC publishes no written comments) +
                      minutes_speaker_log.csv (in-person speaker record-notes, NOT comments) + AVAILABILITY.md
election_results/     Salt Lake County results filtered to West Valley City council+mayor races
geo/                  precinct boundaries + address/point -> council district tool
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday)
recon.md              map of this city's data sources (provenance)
VERIFICATION.md       independent QA + external election cross-check
```

## The join key
Everything keys to the **council meeting weekday (Tuesday)**. WVC nominally meets the 2nd
& 4th Tuesdays, but in 2020–2022 it met most Tuesdays (~40 Regular meetings/yr) — those
extra meetings are genuine, distinct, dated records, not duplicates. Votes + minutes carry
the meeting date; comments carry their meeting date. `build_weeks.py` buckets
every record onto that weekly grid. Elections are point-in-time (Nov, odd years), NOT in
the weekly bundles — they join by **person + year + district** (normalize names first).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat table `meeting_minutes/all_votes.csv`
  (8,908 member-vote rows). There is **no** public-comments dataset (WVC publishes none);
  `public_comments/minutes_speaker_log.csv` (818 rows) lists in-person speakers from the
  minutes but is record-notes, not public-submitted comments — use with that caveat.
- **Meeting-level / contextual**: the `weeks/<tuesday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/west_valley_races.csv`) ↔ votes ↔ comments.
- **By geography**: `geo/address_to_district.py` resolves an address to its district.

## Council structure
Mayor + 2 At-Large + 4 District seats = 7 voting members (Mayor votes). At-Large and Mayor
are city-wide; geo maps addresses to Districts 1–4 only.

## Data notes / caveats
- **Votes**: 1,747 motions; 1,223 named roll-calls + 524 tally-only voice votes (the latter
  recorded with `names_recorded:false`, no guessed members). 208 contested. 3 motions where
  the minutes printed "Unanimous" over a dissenting roll call — the truthful per-member roll
  call was retained (see `meeting_minutes/CLAUDE.md`).
- **Comments**: WVC publishes no genuine written/online public comments (in-person comment
  only) — `all_comments_clean.csv` is intentionally empty; see `public_comments/AVAILABILITY.md`.
  The City Recorder's paraphrases of in-person speakers are in `minutes_speaker_log.csv`
  (record notes, NOT public-submitted comments).
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit. Canonical sources of
  truth are the dataset folders.
- Coverage seams + verification results: see `README.md` and `VERIFICATION.md`.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **604 motions** (2,991 named member-vote rows + 121 tally-only) across
  **264 meeting files** — but **129 discussion-only study meetings hold no votes** (study sessions are
  deliberative; the action votes happen at the regular meeting two days later). 57 contested. Roster of
  **13 appointed commissioners** in `planning_commission/roster.csv`. The `result` string encodes the
  **recommendation-vs-final-action taxonomy** (legislative items → Council vs PC final actions on
  CUP/site-plan/design); classification keys off the **case-number prefix** since WVC minutes describe
  items by case number, not project name. See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** and **body-scoped** —
    `0 applications span >1 body` by design. Because WVC items are **case-numbered, not named**, the
    resolver lands almost everything in `singleton` (high, exact identity): **551 singleton · only 8
    name (medium, heuristic).** `motion.app_match_method` tells you how solid each grouping is.
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — **31 scored links (11 high / 0 medium /
    20 low), all Council←PlanningCommission**. The table also models Council←agency / PC←agency, but
    WVC's **separately-meeting RDA (132 motions) and MBA (63 motions)** are finance/lease bodies that
    carry **0 land-use referrals**. Keyed `(primary_application_id, primary_body,
    related_application_id, related_body, match_method, confidence, …)`.
  - **This is deliberately THIN, like Logan.** WVC minutes give case numbers + few addresses, the two
    bodies use different case-number series, and the PC vote record is sparse — so the trustworthy links
    are **11 hand-verified exact-case-number overrides** (`high`), the auto-linker adds only flagged
    `PUD`-token co-occurrence (`low`, do not quote), and the 4 auto-`medium` false positives were
    **suppressed** (precision over recall). **Only 2% of Council items link; the rest are honestly
    unlinked.** Correct mistakes in `db/overrides.csv` / `db/referral_overrides.csv` + rebuild
    (`python3 db/build_db.py` then `python3 db/build_referrals.py`).
  - **Person overlap is mostly hats, not careers:** 9 of the 10 multi-body people are the Council
    sitting as the **RDA/MBA boards** (same individuals). Only **Cindy Wood** spans the appointed PC
    and the elected Council. Use `v_referral_chain` / `v_project_timeline` / `v_member_record`.

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) reports OnBase (ob.wvc-ut.gov) minutes newer
  than each index (council incl. RDA/MBA, and PC); `--fetch [--dataset meeting_minutes|planning_commission]`
  downloads new PDFs to `<dataset>/raw/`, converts to markdown, appends `minutes_index.csv`
  (+ `fetch_log.csv`), and runs extract_votes.py + validate_votes.py. Results in `refresh_probe.json`.
- After a fetch, rebuild: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, `python3 ../scripts/normalize_motions.py --all`.

## Analysis guidance
- High-consensus council — **contested votes (any Nay/Abstain/Recuse) are the signal**;
  `weeks/<tue>/summary.md` surfaces them. Motion types use the fixed 12-category taxonomy
  (`meeting_minutes/CLAUDE.md`).

---
*Data correction 2026-07-31 (duplicate-ingest wave): two PHANTOM Planning Commission
meetings — **2024-07-10** and **2025-04-16** — were removed. OnBase serves the wrong
meeting's PDF under those two document slots (the 2024-04-10 and 2025-04-23 minutes
respectively), so their motions were double-counted. Both meetings really happened, so
both are now ledgered in `planning_commission/minutes_unrecovered.csv`, and
`fetch_new.py` quarantines the two slots. Net: PC 614→604 motions, db 2,577→2,567
motions / 12,154→12,122 votes. Details: `planning_commission/CLAUDE.md`.*

*Doc correction 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): speaker-log
row count 819 → 818 (measured from `public_comments/minutes_speaker_log.csv`).*

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers (**Hyland OnBase** `ob.wvc-ut.gov` + CivicPlus **Archive Center** + PMN + YouTube);
each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify existing data. Join to
`all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **965 agendas STORED** (Council/PC/RDA/MBA/BoA/HousingAuth/StrategicPlanning; 126 MB).
  OnBase serves thin born-digital agendas, not bundled packets (`documentType=3` unavailable). 100% vote-date join.
- **`housing_plans/`** — **standalone 2025 MIH Plan** (GP appendix); web-delivered GP; state 23/24/25 + SB 34.
  - **completed** (2026-07-16): all 12 Vision West 2035 GP chapters now have text sidecars (11
    fetched; Ch 11 is the lone PDF); 5 appendix plans catalogued out-of-scope — see housing_plans/CLAUDE.md.
- **`ordinances/`** — **329 adopted** (**258 land-use**). **97 high** (CivicPlus Archive Center signed PDFs) /
  223 within_source / 9 none. **164 rows carry a land-use `case_no`** (GPZ/Z/SMI/PUD). 9 ords missing from votes
  (motions cite the application/consent-bundle number, not the ordinance number). 26-26..30 backfilled
  2026-07-19 (26-26/26-27 were **denied** — motion-to-deny passed 4-1, indexed like the other 30+
  denied-motion `within_source` rows; 26-28/26-29 signed PDFs; 26-30 consent-agenda adoption = `none`).
- **`pmn_backfill/`** — Entity 307; Council 398 / RDA 399 / MBA 401 / PC 402. **11 recovered** (8 CC + 2 RDA + 1
  MBA), incl. off-cycle budget-retreat work sessions OnBase never carried. PC = honest zero.
- **`transcripts/`** — **ASR** captions, 10 sampled / 1,133 videos mapped (WVCTV YouTube, `/streams`+`/videos`).
- **`campaign_finance/`** — **105 filings** (2019/21/23/25) self-hosted on the CivicPlus Archive Center. 96% of
  modern general candidates filed; **2023 D3 winner Whetstone filed none** (gap). Structured layer: use
  `scripts/campaign_finance/cycle_totals.py` when built (never sum `filing_totals` — one row per filing).
