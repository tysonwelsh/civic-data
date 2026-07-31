# West Jordan City Council — data repository

Canonical datasets about the **West Jordan City Council**, modeled on the Salt Lake City
reference repo, plus a derived weekly view unifying minutes + votes + comments. Built by
the `build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 250 files 2020–2026) + roll-call votes (all_votes.csv)
planning_commission/  PC minutes (84 files) + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                      (the appointed land-use body; recommendation-vs-final-action; TALLY-ONLY votes)
db/                   NORMALIZED RELATIONAL DATABASE (db/civic.db SQLite + table CSVs) joining ALL bodies'
                      votes by real keys + reconstructed PC→Council referrals. Start here: db/SCHEMA.md
public_comments/      all_comments_clean.csv (28 GENUINE written comments from agenda packets)
                      + minutes_speaker_log.csv (in-person speaker notes, NOT comments) + AVAILABILITY.md
election_results/     Salt Lake County results filtered to West Jordan council+mayor races
geo/                  precinct boundaries + address/point -> council district tool (Districts 1–4)
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Tuesday)**. Votes + minutes carry the
meeting date; genuine comments carry their meeting date. `build_weeks.py` buckets every
record onto that weekly grid. Elections are point-in-time (Nov, odd years), NOT in the
weekly bundles — they join by **person + year + district** (normalize names first).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (5,830 council member-vote rows) and
  `public_comments/all_comments_clean.csv` (28 genuine written comments). Do NOT use
  `minutes_speaker_log.csv` (239 in-person paraphrases) as comments.
- **Meeting-level / contextual**: the `weeks/<tuesday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/west_jordan_races.csv`) ↔ votes ↔ comments.
- **By geography**: `geo/address_to_district.py` resolves an address to Districts 1–4.

## Council structure
**4 District seats + 3 At-Large + separately-elected Mayor.** The **Mayor (Dirk Burton)
does NOT vote** on council motions (council votes are 7-member). At-large + mayor are
city-wide; geo maps addresses to Districts 1–4. At-large seats fill via a single grouped
"Vote-for-3" race (2021, 2025); district seats elect together (2019, 2023).

## Data notes / caveats
- **Votes**: 1,158 motions / 5,830 member-vote rows (council). West Jordan records named roll-calls
  ("the vote was recorded as follows") mainly for substantive items — routine/consent
  business often passes without an individually recorded motion — so the recorded set
  skews toward contested items (≈13% draw a Nay). Treat the contested *rate* as "among
  recorded roll-calls," not directly comparable to councils that roll-call everything.
  Tally-only/unanimous-without-names motions carry `names_recorded:false` (no guessed
  members). See `meeting_minutes/CLAUDE.md`.
- **Comments**: genuine written comments are forwarded resident emails bundled in PrimeGov
  "Complete Packet" PDFs (verdict IN-PACKETS); the 28 captured are the 2022 Welby West
  rezone campaign (2023–25 packets carried only staff/vendor/inter-agency mail; 2020/2021/
  2026 have no packets). See `public_comments/AVAILABILITY.md`. In-person speakers are in
  `minutes_speaker_log.csv` (record notes, not public-submitted comments).
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — same schema as council; every row
  `body=PlanningCommission`. The appointed land-use body: **84 meetings / 384 motions / 15
  commissioners** (`planning_commission/roster.csv`). The `result` string encodes the
  **recommendation-vs-final-action taxonomy**: *Positive/Negative recommendation N:N* (forwarded to
  Council) vs *N:N Approved/Denied (Final Action)* (site plans, CUPs, preliminary plats — never reach
  Council). **TALLY-ONLY caveat:** WJ PC minutes print a tally ("passed 6-0") and **never name the aye
  majority**, so `all_votes.csv` has **no Aye rows** — only named dissent/abstain/recuse + absentees.
  36/84 minutes are OCR'd scans. **The old "2020–21 had no standalone PC meetings" claim is
  RETIRED (2026-07-17):** the Commission met biweekly all of 2020; those minutes were never in
  the PrimeGov archive but were recovered from the city's own doc host (see `pmn_backfill/` +
  `provenance='citysite_minutes'`). See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no file number exists in
    WJ) and **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high) tells you how solid each grouping
    is. Bodies in the DB: **Council 835 · RDA 88 · MBA 37 · PlanningCommission 203 motions** (the
    council sits as RDA/MBA — modeled as distinct bodies).
  - *Because PC votes are tally-only, the per-body CSV emits only named rows* — so the DB holds the
    **203** PC motions that name ≥1 member (of the **384** in the PC subtree). PC within-body vote rows
    are **dissent + absentee only** (no aye); that's honest, not a gap.
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — 21 scored links (8 high / 9 medium /
    4 low), all Council←PlanningCommission here (the table also models Council←agency / PC←agency; WJ's
    RDA/MBA carry none — 0 shared addresses). Keyed `(primary_application_id, primary_body,
    related_application_id, related_body, match_method, confidence, …)`. **`high`≈exact
    (address+subject); `medium` spot-check before quoting; `low` flagged.** 12% of council land-use
    items linked (a floor — tally-only PC depresses recall); the rest are honestly unlinked. Correct
    mistakes in `db/overrides.csv` / `db/referral_overrides.csv` + rebuild
    (`python3 db/build_db.py && python3 db/build_referrals.py`).
  - **WJ address nuance:** a "shared address" is an approximate **grid intersection / block address**,
    not a parcel, so address-alone is co-location (low). The payoff = the technical-vs-political view
    (PC recommendation → Council decision). Use `v_referral_chain` / `v_project_timeline`.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-03)
Six new source layers; each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify
existing data. Join everything to `all_votes.csv`/minutes by `date` (+ `body`).

- **`packets/` (LINK INDEX)** — PrimeGov `CompiledDocument` packets, **bundled one-PDF-per-meeting**
  (like Revize), 0.4–330 MB, image/map-heavy → **not stored**; `index.csv` (222 rows) is a pointer
  table (`source_url`, `size_mb`, `packet_kind`, `format=na`, `stored_locally=no`). To read one:
  fetch `source_url`, use **vision/OCR**. Covers Council/PC/RDA/MBA 2022–2026; mid-2025+ meetings
  moved to a non-downloadable HTML Interactive Agenda (gap). `body` column lets you filter to Council.
- **`housing_plans/`** — adopted **2023 General Plan** + FLUM + Ord. 23-10; MIH element (Ord. 20-32
  2020 + 2026 copy); 2020 city annual report; state 2023/24/25 compilations + SB 34 (WJ pages sliced).
  Policy layer behind land-use votes.
- **`ordinances/`** — Ordinance # → adoption date → adopting motion. **64 `high`** (motion +
  independent recorder-signed PDF agree), **226 `within_source`** (motion-derived, NOT corroborated
  — treat as suggestive), **3 `none`** (293 rows total). 67 signed PDFs on disk (63 zoning + 4
  non-zoning from the 2026-07-19 26-26..33 backfill). **Audit signal:** 3 signed
  adopted ordinances (22-08/23-08/24-18) have no motion in `all_votes.csv` — minutes-extraction gap.
- **`pmn_backfill/`** — coverage cross-check + recovery, **separate** from the audited minutes (do
  not treat as canonical without review). Bodies 395/396. **60 recovered**: 33 from Utah Public
  Notice (`source=pmn`) incl. a 28-meeting 2021–22 PC run, **plus 27 standalone 2020-01→2021-03 PC
  minutes recovered 2026-07-17 from the city doc host** (`source=city_website`,
  `assets.westjordan.utah.gov`, via the WordPress `wjc/v1/data-meeting` API; PMN had agendas only).
  Together these close the "no standalone PC 2020–21" gap entirely. Content-verify before promoting
  any row. `pmn_exceptions.csv` records 2 COVID-cancelled dates (PC 2020-03-17, Council 2020-03-25).
- **`transcripts/`** — **ASR** YouTube captions (10; `en-orig`), NEVER an authoritative record.
  647-video map in `channel_videos.csv`. **YouTube coverage ends 2025-02-04** (city → Swagit/OpenUtah
  after). PC + council both present. 2024 budget/TnT meetings are the top Whisper candidates (not run).
- **`campaign_finance/`** — 135 filings; **EasyVote portal** (2023+) + city WordPress (2021 + annual/
  COI). Assign cycle/office by **document year**, not EasyVote's current-seat `officename` (mis-joins
  multi-run candidates). 2019 = GRAMA-only. 7 primary-only candidates flag `election_results` gaps.

## Analysis guidance
- **Contested votes (any Nay/Abstain/Recuse) are the signal** (148 council, 25 PC); `weeks/<tue>/summary.md`
  surfaces council ones. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).
- **1 person served on both Council and PC** (Kent Shelton — commissioner 2020–2023 [present at the 2020-01-07 PC
  meeting per the 2026-07-17 citysite recovery; the "2022–23" span predated that backfill], then elected 2024+);
  unified by name in the DB `person`/`role` tables — profile with `v_member_record`.

## Refreshing (incremental updates — added 2026-07-02, plan 3.3)
- `python3 fetch_new.py --probe` — read-only: reports meetings on the PrimeGov portal newer
  than each `minutes_index.csv` max date (writes `refresh_probe.json`; nothing downloaded).
- `python3 fetch_new.py --fetch [--dataset meeting_minutes|planning_commission]` — downloads new
  minutes PDFs to `<dataset>/raw/`, converts to markdown, appends index rows (+ `fetch_log.csv`
  provenance), then runs that dataset's `extract_votes.py` + `validate_votes.py`.
- After a fetch, rebuild derived layers: `python3 db/build_db.py && python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` from the repo root.
