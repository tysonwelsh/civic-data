# South Jordan City Council — data repository

Canonical datasets about the South Jordan City Council and Planning Commission, modeled on
the Salt Lake City reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`).
Built by the `build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + fetch_new.py refresh
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      public comments cleaned to a flat table — OR AVAILABILITY.md if unpublished
election_results/     Salt Lake County results filtered to South Jordan council+mayor races
geo/                  precinct boundaries + address/point -> council district tool
db/                   relational SQLite (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday = 1)
recon.md              map of this city's data sources (provenance) — written by the recon
                      agent BEFORE acquisition; records portal vendor, URL patterns, and
                      what does/doesn't exist (the honest-gap record starts here)
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; extended
                      with dated addenda whenever the data is repaired or re-audited)
```

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root
  `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday** (Tuesday). Votes + minutes
carry the meeting date; comments (if any) carry their date. `build_weeks.py` buckets every
record onto that weekly grid. Elections are point-in-time (Nov, odd years) and are NOT in
the weekly bundles — they join by **person + year + district** (normalize names first).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables —
  `meeting_minutes/all_votes.csv` (+ `motions_std.csv`) and
  `public_comments/all_comments_clean.csv`.
- **Relational / cross-body** (PC recommendation → council outcome, member records):
  `db/` (core tables are exact; the `referral` layer is reconstructed + scored — respect
  its confidence column).
- **Meeting-level / contextual**: the `weeks/<date>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes ↔ comments.
- **By geography**: `geo/address_to_district.py` resolves an address to its district.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders; never edit files under `weeks/` or
the .db. Rebuild weeks/ after ANY change to the canonical CSVs. Each subfolder has its
own CLAUDE.md with build details.

## Keeping it current
`meeting_minutes/fetch_new.py` (and the PC equivalent) probes the portal for events newer
than `max(date)` in `minutes_index.csv`, fetches originals into `raw/`, extracts,
validates, and rebuilds the derived layers.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain) are the signal**;
  `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see `meeting_minutes/CLAUDE.md`);
  standardized categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and
  `VERIFICATION.md` — read those before quantitative claims.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers, each with its own `CLAUDE.md` + `AVAILABILITY.md` and each passing
`validate_dataset.py`. **None modify the core minutes/votes/comments/elections layer.** Join
to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **169 whole-meeting agenda packets INDEX-ONLY** (Council 87 + PC 82,
  2022–2026) from the **Municode Meetings** portal (`southjordan-ut.municodemeetings.com`,
  an **HTTP/2-only** host). Municode bundles each meeting into one PDF (agenda + all staff
  reports + exhibits), median 19.8 MB up to 195 MB (5.32 GB total) — too large to store, so
  `index.csv` catalogs all 169 with live `source_url` + exact byte size + `packet_uid`;
  fetch on demand. `body ∈ Council/PlanningCommission`; `meeting_type` regular 166 / study 2
  / canvassers 1. Join `(date, body[, meeting_type])`: Council packets cover 82/100 of 2022+
  council vote dates, PC 80/82. **2020–2021 predate Municode packet publication** (verified
  zero-result, not a scraper miss).
- **`housing_plans/`** — **6 docs**: the **2020 General Plan** (dated by PDF CreationDate — no
  adoption date printed), the **2025 MIH element** (Zions study; it is General Plan
  **Appendix A** — the two are one plan), and the state DWS/HCD **2023/24/25** MIH
  compilations + the **SB 34** summary (state reports are one statewide PDF/year — South
  Jordan lives in per-city page ranges recorded in `AVAILABILITY.md`). City docs from
  `sjc.utah.gov` DocumentCenter; state from `jobs.utah.gov` HCD. Document dataset, not joined
  to `db/`.
- **`ordinances/`** — **129 adopted ordinances (2020+)**, one row each, linked to the council
  motion that passed it. Confidence **39 high** (motion-cited + independent S3 PDF) / **78
  within_source** (motion-derived, incl. all 35 `-Z` rezones — `high` by construction, NOT an
  independent cross-match) / **7 low** (date-only) / **5 none** (pre-minutes-floor). **45%
  land-use** (58/129). **Two independent number series** — general `YYYY-NN` and zoning/rezone
  `YYYY-NN-Z`; never collapse the `-Z`. Source: `southjordan.municipalcodeonline.com`'s public
  **S3 bucket** (general series only — **zero `-Z` posted there**). Full **213-doc back-catalog
  1997–2026** enumerated index-only in `archive_backcatalog.csv`; 52 general-series PDFs
  downloaded (47 signed scans, OCR deferred). `adopted` dates on `low`/`none` rows read by
  **vision** from the handwritten signature-page clause (traceable to a page image).
- **`pmn_backfill/`** — **separate** from the audited minutes. SJ PMN entity 269; bodies
  Council 1031 / PC 1032 / RDA 3901 / MBA 5015 / BoA 1033. **13 docs across 8 dates recovered**,
  **all City Council** — filling the previously-unrecoverable **2020 Jan–Jul** gap (the base
  build's 6-month PMN list view is why it missed them) plus a 2023-01-24 budget meeting. RDA/MBA
  and PC 2020+ have **no genuine standalone gap** (their PMN docs are *Combined* meetings already
  on disk). **These recoveries contradict 2 rows of `meeting_minutes/minutes_unrecovered.csv`** —
  left in place per instructions; **merging into the canonical minutes layer is a deliberate
  user follow-up** (see `coverage.md` §Reconciliation).
- **`transcripts/`** — **SAMPLE-ONLY by owner policy.** Maps South Jordan's YouTube presence
  (**125 available videos**) + retrieves **10 ASR caption tracks**. **Honest gap:** SJ does
  **not** post council/PC meeting *video* — the official channel is PR/promotional; meetings
  exist as **audio + minutes** elsewhere (OpenUtah has 60 transcribed). So this is NOT a
  deliberation-transcript corpus and has **no join** to votes. ASR is never authoritative.
  Whisper-over-city-audio (or OpenUtah reuse) is the future route to real transcripts.
- **`campaign_finance/`** — **ACQUISITION LAYER ONLY** (raw filings + provenance index; no
  dollar extraction yet). **46 filings / 14 candidates**, 2019–2025 (Mayor + 5 district seats).
  **100% of filers join `election_results/south_jordan_races.csv`** (candidate + year +
  district; election names are UPPER-CASE — normalize). 42 scanned / 4 text; 2019 recovered
  from **Wayback** (live URLs 404). **Do NOT sum filings into cycle totals** — cumulative-vs-
  incremental is unknown until the structured step, and **3 superseded 2023 uploads**
  (ids 5135/5148/5149) must never be counted as extra filings.
