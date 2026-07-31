# South Jordan City Council — data repository

A Salt Lake City-style civic-data repository for the **South Jordan City Council** and
**Planning Commission** (Salt Lake County, Utah; ~80k pop.), built 2026-07-06 by the
`build-city-data-repo` skill. Council + PC minutes (as markdown), extracted roll-call
votes, a relational cross-body db, public-comment availability, municipal election
results, and an address→district tool — all as markdown/CSV, covering **2020–present**.
See `CLAUDE.md` for analysis guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`;
independent QA in `VERIFICATION.md` (19 PASS / 3 WARN / 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2020-08 → 2026 | 243 meetings (markdown) | CivicPlus ArchiveCenter (227) + Utah PMN 2020 backfill (16) | ✅ complete (born-digital `pdf-text`); 2020 Jan–Jul gap logged |
| Council votes | 2020–2026 | 1,029 motions · 1,448 vote rows · 14 contested (757 named rows) | extracted from minutes (`extract_votes.py`) | ✅ verified; tie-break + 2 clerk errors stored faithfully |
| PC minutes | 2020 → 2026 | 125 meetings (markdown) | CivicPlus ArchiveCenter (105) + Utah PMN (20) | ✅ complete; 3 un-minuted 2020 e-meetings logged |
| PC votes | 2020–2026 | 730 motions (205 final-action · 95 recommendation) · 797 rows · 18 contested (353 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; names dissenters/absentees only (source style) |
| Relational db (`db/south_jordan.db`) | 2020–2026 | 1,759 motions · 1,110 votes · 13 PC→Council referrals | standard cross-city schema | ✅ reconciles exactly to CSVs; see `db/SCHEMA.md` |
| Public comments | — | **0 published** | n/a — submit-only city | ⚠️ SUBMIT-ONLY (see below + `public_comments/AVAILABILITY.md`) |
| Election results | 2007–2025 (odd years) | 41 races (30 general + 11 primary) · 111 candidate rows · 2,062 precinct rows | Salt Lake County SOVC (`slco-election-archive`) | ✅ verified; all sampled winners match outside sources |
| Geo (address→district) | current map | 5 district polygons; 68 precincts → Districts 1–5 | city ArcGIS `Voting/MapServer/2` | ✅ tool + geojson present |
| Weekly bundles | 2020–2026 | 128 week bundles | derived (`build_weeks.py`) | ✅ regenerable; sums to flat totals |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 1,029 / PC 730 rows) and the repo-root `crosswalks/`.

## Council structure

**Six-member council form: 5 district council members (Districts 1–5) + a separately
elected Mayor.** No at-large seats (the Mayor is the only citywide seat). Terms are 4-year
staggered: **Cycle A** (Mayor + District 3 + District 5) elects 2009/2013/2017/2021/2025;
**Cycle B** (Districts 1, 2, 4) elects 2007/2011/2015/2019/2023.

Current members: Mayor **Dawn R. Ramsey**; D1 **Patrick Harris**, D2 **Kathie L. Johnson**,
D3 **Don Shelton**, D4 **Tamara Zander**, D5 **Jason McGuire** (D2's **Brad Marlor** held
the seat 2020–2023 before Johnson won it in 2023 — Marlor votes 2020–2023, Johnson from
2024). Geo maps addresses to Districts 1–5.

### The Mayor vote — non-voting except one recorded tie-break
Although the statutory six-member form makes the Mayor a full council member, **every
recorded tally is `N-0`/`N-M` counting only the 5 district members** — the Mayor presides
and does **not** appear in the roll-call count on ordinary motions (max ordinary tally = 5).
The **single exception is a genuine statutory tie-break**: on **2025-06-17** (Ordinance
2025-09), with the council split 2-2 (Shelton/Johnson Yes, Harris/McGuire No, Zander
absent), **Mayor Ramsey cast the deciding Yes for a 3-2 pass**. That is the only motion
where the source itself records the Mayor voting; it is stored verbatim (all six voters,
incl. `Dawn R. Ramsey | Aye`) and flagged in `meeting_minutes/votes/_validation_report.txt`
as the sole 6th-voter / mayor-vote event. See `meeting_minutes/CLAUDE.md`.

### RDA / MBA — in-meeting bodies
South Jordan's council sits **in-session** as the **Redevelopment Agency (RDA)** and the
**Municipal Building Authority (MBA)**: it recesses the Council, convenes the RDA/MBA
inside the same meeting (often via a "Combined City Council & Redevelopment Agency"
minutes doc), acts, then reconvenes. The vote extractor walks those brackets and tags each
motion `body ∈ {Council, RDA, MBA}` in `all_votes.csv` — **1,007 Council · 21 RDA · 1 MBA**
motions. There are **no separate RDA/MBA minutes files** to acquire (unlike Ogden); the
in-meeting captures are the complete published record.

## Public comments — SUBMIT-ONLY (honest gap)
South Jordan publishes **no archive of genuine written/online public comments**. Written
comment is accepted only **by email to the City Recorder** (Anna Crookston,
`acrookston@sjc.utah.gov`, by 3:00 p.m. meeting day) or **in person** (3-minute limit) —
neither is published. No eComment / Open City Hall / Speak-Up portal, no "correspondence
received" archive, and the Municode agenda packets carry no forwarded-email section
(verified). So `all_comments_clean.csv` was **not built** — an honest empty result, not a
processing miss. In-person speakers are named + paraphrased inside the minutes (a
meeting-record *speaker log*, **not** public-submitted comments). Full audit:
`public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **2020 Jan–Jul council gap (honestly logged).** No portal retains pre-Aug-2020 SJ council
  minutes (CivicPlus archive starts 2021; Municode 2022; Utah PMN 2020-08-04). Coverage
  begins **2020-08-18**; the Jan–Jul span and the 2020-08-04 agenda-only meeting are in
  `meeting_minutes/minutes_unrecovered.csv` — never as stub rows.
- **PC 2020:** three early-COVID electronic meetings (2020-04-14, 2020-04-28, 2020-08-11)
  were noticed on PMN with no minutes ever posted — in
  `planning_commission/minutes_unrecovered.csv`.
- **Narrative-tally votes — majorities honestly unnamed.** The clerk records votes as a
  narrative tally (`"Roll Call Vote was 5-0, unanimous in favor."`), never a per-name
  roll-call block, so the winning **majority is never named**; only dissenters and
  absentees are (Sandy-style). Unanimous motions carry `names_recorded:false` (no invented
  Aye names). `f.tally` validator WARNs (council 43.2%, PC 0.0% full-roster match) are this
  documented source style, not a parse loss. See `meeting_minutes/CLAUDE.md` +
  `planning_commission/CLAUDE.md`.
- **Two clerk errors retained verbatim + flagged** (never silently corrected): council
  **2025-08-19 m7** (`result`="4-1 Pass" but only 3 Aye + 1 Nay named) and PC **2022-10-11
  m4** (`"4-0, no votes made by Commissioner Bevans and Chair Hollist"` — tally contradicts
  the named nays). Both surface in the datasets' validation reports; corrections belong in
  documented override files, never in-place edits.
- **One documented minutes mis-upload.** CivicPlus ADID-232 served the *Study* minutes in
  the *Regular* slot for 2021-10-19; the true regular minutes were recovered via PMN
  (`utah.gov/pmn/files/784439.pdf`). The orphan PDF is retained in `raw/` (not indexed) —
  244 raw PDFs vs 243 indexed. See `meeting_minutes/CLAUDE.md`.
- **Elections:** county-administered; only South Jordan council + mayor races included. The
  archive's `normalize_sovc.py` missed SJ's 2011 general (skipped) and 2019 general (`SJD
  Council N` sheet coding never matched a `%SOUTH JORDAN%` filter) — both re-parsed from
  raw SOVC here (`election_results/CLAUDE.md`). No SJ 2019 primary was held (true
  no-contest, not a gap).

## Regenerate each layer
- **Council votes:** `python3 meeting_minutes/extract_votes.py` (then
  `meeting_minutes/validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then
  `planning_commission/validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes
  `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`CITY="South Jordan"`, `MEETING_WEEKDAY=1`
  → Tuesday). `weeks/` and `db/` are **derived** — regenerate, never hand-edit; rebuild
  weeks/ after any change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` (default; read-only) lists CivicPlus ArchiveCenter items
newer than the index max for each dataset (council list /484, PC list /486);
`--fetch [--dataset meeting_minutes|planning_commission]` downloads the new PDFs → `raw/` →
markdown → `minutes_index.csv`, then runs `extract_votes.py` + `validate_votes.py`. Rebuild
db + motions_std + weeks afterward (the CLI prints the reminder). The PC-only mirror is
`planning_commission/fetch_new.py`. Idempotent + resumable (skips docs already on disk).

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated.

## Expansion datasets (additive, 2026-07-06)
Six additional source layers built by `expand-city-sources`, each fully documented in its
own folder and in `EXPAND_SOURCES_REPORT.md`. **None modify the core minutes/votes/comments
layer.** Join to `all_votes.csv`/minutes by `date` (+ `body`).

- **`packets/`** — 169 whole-meeting agenda packets (Council 87 + PC 82, 2022–2026)
  catalogued **INDEX-ONLY** with live URLs + exact byte sizes (5.32 GB on the Municode
  portal, too large to store). The staff analysis behind each agenda item.
- **`housing_plans/`** — 6 docs: the 2020 General Plan, the 2025 Moderate-Income-Housing
  element (General Plan Appendix A), the state 2023/24/25 MIH compilations + the SB 34
  summary.
- **`ordinances/`** — 129 adopted ordinances (2020+) linked to the council vote that passed
  each (39 high-confidence + 78 within-source + 7 low + 5 pre-floor); 45% land-use. Two
  parallel number series (general `YYYY-NN` + zoning `YYYY-NN-Z`). Full 213-doc back-catalog
  1997–2026 indexed.
- **`pmn_backfill/`** — 13 council-minutes docs (8 dates) recovered from Utah Public Notice,
  filling most of the previously-unrecoverable **2020 Jan–Jul** gap plus a 2023 budget
  meeting. Kept separate; **merging into the audited minutes layer is a deliberate follow-up**
  (contradicts 2 `minutes_unrecovered.csv` rows).
- **`transcripts/`** — 125 YouTube videos mapped, 10 ASR caption tracks sampled. **Honest
  gap:** South Jordan posts meeting **audio + minutes**, not meeting *video* — the YouTube
  channel is PR-only, so there is no deliberation-transcript corpus (Whisper-over-audio is the
  future route). Not an official record.
- **`campaign_finance/`** — 46 candidate disclosure filings / 14 candidates (2019–2025),
  100% joined to election results; 42 scanned. Acquisition layer only (dollar structuring
  deferred; do not sum filings until then).
