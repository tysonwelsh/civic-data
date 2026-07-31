# West Valley City Council — data repository

A Salt Lake City-style civic-data repository for the **West Valley City Council**, built
2026-06-24 by the `build-city-data-repo` skill. Council minutes, extracted roll-call votes,
public comments, municipal election results, and an address→district tool — all as
markdown/CSV, covering **2020–present**. See `CLAUDE.md` for how to analyze it and each
subfolder's `CLAUDE.md` for build details. Independent QA in `VERIFICATION.md` (**PASS**,
no fabrication, 14/14 election winners externally confirmed).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 550 meetings (markdown) | Hyland OnBase (`ob.wvc-ut.gov`), text-layer PDFs | ✅ complete (465 Council + 85 RDA/MBA), no OCR |
| Roll-call votes | 2020–2026 | 1,942 motions · 9,655 member-vote rows · 220 contested | extracted from minutes | ✅ verified |
| — by body | | Council 1,747 / 8,908 · **RDA 132 / 534** · **MBA 63 / 213** (motions / rows) | separate OnBase RDA + MBA meetings | ✅ `body` column |
| Planning Commission votes | 2020–2026 | 606 motions · 3,022 named rows + 119 tally-only · 263 meeting files (128 study = no votes) · 57 contested · 13 commissioners | OnBase PC minutes | ✅ `planning_commission/` (`body=PlanningCommission`) |
| Relational database | 2020–2026 | 4 bodies · 559 apps · 2,548 motions · 12,055 votes + 31 reconstructed PC→Council referrals | derived from the vote CSVs | ✅ `db/civic.db` — start at `db/SCHEMA.md` |
| Public comments (genuine written/online) | — | **0 — none published online** | n/a | ⚠️ WVC publishes no written-comment dataset (see `public_comments/AVAILABILITY.md`) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 818 in-person speakers · 216 meetings | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` — meeting-record notes only |
| Election results | 2019, 2021, 2023, 2025 | 14 races · 34 candidates · 1,479 precinct rows | Salt Lake County (`slco-election-archive`) | ✅ verified (14/14 winners) |
| Geo (address→district) | current map | 70 precincts → Districts 1–4 | SLCo Vista precincts + election data | ✅ tested |
| Weekly bundles | 2020–2026 | 251 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
Mayor + 2 At-Large + 4 District seats = **7 voting members** (the Mayor votes). At-Large and
Mayor are city-wide; the geo tool maps addresses to Districts 1–4.

## Planning Commission + relational database
- **`planning_commission/`** holds the appointed land-use body's roll-call votes (same 13-column
  schema, `body=PlanningCommission`): 606 motions across 263 meeting files, of which **128
  discussion-only study meetings carry no votes**. The `result` string distinguishes
  **recommendations forwarded to the Council** from **PC final actions** (CUP/site-plan/design).
- **`db/civic.db`** is the **canonical, queryable** form — a normalized SQLite model joining Council,
  Planning Commission, RDA, and MBA votes by real keys, plus a separate **reconstructed PC→Council
  referral** layer. **Start at `db/SCHEMA.md`.** Two layers: the within-body core is **exact**
  (project keys resolved from prose, body-scoped — `0 apps span >1 body`); the cross-body `referral`
  layer is **reconstructed, scored, and overridable** (`31` links — `11` hand-verified
  exact-case-number `high` + `20` flagged `low`; only 2% of Council items link, honestly thin because
  WVC describes items by case number, not project name). Build:
  `python3 db/build_db.py` then `python3 db/build_referrals.py`.

## Known gaps / caveats
- **No genuine written/online public comments exist for WVC.** The city takes public
  comment **in person only** and publishes no written-comment dataset (verified
  exhaustively — see `public_comments/AVAILABILITY.md`). So `all_comments_clean.csv` is
  empty. The City Recorder's third-person paraphrases of in-person speakers are kept
  separately in `public_comments/minutes_speaker_log.csv` (818 rows) — these are
  **meeting-record notes, NOT public-submitted comments**, and are excluded from the
  comments dataset by design. (Two COVID-era emailed comments were read verbatim into 2020
  minutes; documented in AVAILABILITY.md, not extracted.)
- **524 tally-only voice votes** record the outcome but not per-member names (the minutes
  didn't list them); stored with `names_recorded:false`, members never guessed.
- 3 motions where the minutes printed "Unanimous" over a roll call that showed dissent —
  the truthful per-member roll call is retained (see `meeting_minutes/CLAUDE.md`).
- Elections are county-administered; only West Valley City council+mayor races are included.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` (resumable; `--force` to rebuild)
- Planning Commission votes: `python3 planning_commission/extract_votes.py`
- Relational database: `python3 db/build_db.py` then `python3 db/build_referrals.py` (idempotent)
- Speaker log: `python3 public_comments/extract_comments.py` (builds `minutes_speaker_log.csv`
  from minutes — these are record notes, not public comments; the genuine comments CSV stays empty)
- Elections: `python3 election_results/build_wvc_elections.py`
- Weekly bundles: `python3 build_weeks.py`

Canonical sources of truth are the markdown minutes and the dataset CSVs. **Known gap:
original source PDFs were NOT retained** — the `*/raw/` directories are empty except
`election_results/raw/` (the minutes PDFs were most plausibly lost in the iCloud
dataless-stub incident noted in `meeting_minutes/CLAUDE.md`). Every minutes PDF remains
re-fetchable via the `source_url` column of `minutes_index.csv` (OnBase: replace
`DownloadFile` with `DownloadFileBytes` in the URL — spot-verified live 2026-07-02).
`weeks/` is derived and safe to delete/regenerate.

---
*Doc corrections 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): the
"canonical sources of truth are the raw downloads under `*/raw/`" claim was false — those
dirs are empty (PDFs not retained); replaced with an honest known-gap note plus the
verified re-fetch path. Speaker log 819 → 818 rows (measured: 818 data rows after the
6-line comment header). Weekly bundles 250 → 251 (measured: 251 week dirs in `weeks/`).*

## Expansion datasets (additive, 2026-07-06)
Six additional source layers (Hyland OnBase + CivicPlus Archive Center + Utah Public Notice +
YouTube), each documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 965 meeting agendas across all bodies (Council/PC/RDA/MBA + advisory), stored
  locally; OnBase publishes no bundled staff-report packets.
- **`housing_plans/`** — the standalone 2025 Moderate-Income Housing Plan and the state compilations.
  Completed 2026-07-16: all 12 Vision West 2035 GP chapters now have text sidecars (11 fetched; Ch 11 the lone PDF); 5 appendix plans catalogued out-of-scope.
- **`ordinances/`** — 324 adopted ordinances (254 land-use), most matched to the adopting motion,
  with land-use case numbers captured; 95 corroborated by signed PDFs.
- **`pmn_backfill/`** — 11 meetings recovered from Utah Public Notice, incl. off-cycle budget retreats.
- **`transcripts/`** — a 1,133-video map of meeting recordings + 10 sampled ASR caption tracks (YouTube).
- **`campaign_finance/`** — 105 candidate disclosure filings (2019–2025), self-hosted by the city.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
