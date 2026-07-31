# Town of Alta — data repository

A Salt Lake City-style civic-data repository for the **Town of Alta Town Council** and
**Planning Commission** (Salt Lake County, Utah; **~380 residents**, top of Little Cottonwood
Canyon; incorporated 1970), built 2026-07-11/12 by the `build-city-data-repo` skill. Council +
PC minutes (as markdown), extracted roll-call votes, a relational cross-body db, public-comment
availability, municipal election results, and a town-boundary geo tool — all as markdown/CSV. See
`CLAUDE.md` for analysis guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA
in `VERIFICATION.md` (PASS on every built dataset, 0 FAIL).

## ⚠ Alta is SPARSE BY DESIGN — read this before any count
Alta is one of Utah's smallest municipalities (~380 people). The **Town Council meets ~monthly**
(2nd Wednesday, ~12/yr) and the **Planning Commission meets 4th Wednesday _as-needed_** (cancelled
whenever it has no business). Low document counts — ~12 council meetings a year, 17 PC meetings in
3.5 years, zero published public comments — are the **correct** record for a town this size, **not**
a coverage gap. Every empty here is an honest zero verified against source.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2020-02-12 → 2026-06-17 | **85 md** (== 85 index) **+ 3 PMN-promoted docs** (2020-05-06, 2020-06-17, 2024-08-14 — in `pmn_backfill/text/`) | Utah PMN (council body 1601; promoted docs recovered label-agnostically 2026-07-13, merged 2026-07-16) | ✅ complete; 49 `pdf-text` + 36 `ocr` (+2 text/1 OCR promoted); **0 unrecovered** (2020 is the floor; town runs since 1970) |
| Council votes | 2020–2026 | **505 motions** · **1,150 vote rows** | extracted from minutes (`extract_votes.py council` + `extract_backfill_votes.py`) | ✅ verified; **MAYOR VOTES** (max roll = 5); named roll calls + tally-only unanimous; **181 named / 324 tally-only** motions; **28 contested**; trailing `provenance` column (`minutes`/`pmn_minutes`) |
| PC minutes | 2022-06-02 → 2025-12-17 | **17 md** (== 17 index) **+ 1 PMN-promoted doc** (2024-04-24) | Utah PMN (PC body 1602) | ✅ complete but for **1 unrecovered** (2023-11-28 — only a DRAFT survives, never promoted; see `planning_commission/minutes_unrecovered.csv`); 4 `pdf-text` + 13 `ocr`; **none 2020–2021** (genuine — as-needed PC produced no minutes) |
| PC votes | 2022–2025 | **49 motions** · 49 rows · **0 named** | extracted from minutes (`extract_votes.py pc` + `extract_backfill_votes.py`) | ✅ verified; **tally-only by source** (narrative "unanimous consent"; no per-member roll call ever printed); 0 contested |
| Relational db (`db/civic.db`) | 2020–2026 | **554 motions** · **829 votes** · **0 referrals** | standard cross-city schema | ✅ reconciles exactly (829 named CSV rows == 829 db votes); referral layer honestly empty (PC too sparse / no shared key); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md + header-only CSV** | n/a — SUBMIT-ONLY | ⚠ **HONEST ZERO** — no published written-comment archive; comment is in-person / paraphrased in minutes |
| Election results | 2021 & 2023 (≥2020 floor) | **3 races** · candidate + precinct tables | Salt Lake County SOVC (canonical county slice) | ✅ verified; **Town-of-Alta contests only** (Alta Canyon rec-district decoys EXCLUDED); winners cross-check to outside sources |
| Geo | current | town boundary + precincts | UGRC `NAME='Alta'` (CountyID 18) | ✅ **at-large → NO council districts**; geo is town-membership only, no address→district tool needed |
| Weekly bundles | 2020–2026 | **85 week bundles** | derived (`build_weeks.py`, Wednesday grid) | ✅ regenerable; weekly vote sum 1,150 == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 505 / PC 49 motion rows) and the repo-root `crosswalks/`.

## Council structure — the Mayor VOTES (Utah Town form)
Alta uses Utah's **Town form of government**: a **Mayor + 4 at-large councilmembers**, all seats
**at-large** (no districts), non-partisan, staggered 4-year terms. **The Mayor is a full voting
member** — every roll call lists the Mayor by name alongside the councilmembers, so a full council
roll call tops out at **5** (Mayor + 4). This differs from Taylorsville / South Jordan (mayor never
votes) and Park City / Riverton (mayor votes only to break ties); it **matches Millcreek** (mayor
votes routinely). Confirmed at source (`VERIFICATION.md §3`):

> ROLL CALL VOTE: **Mayor Bourke — yes,** Councilmember Schilling — yes, Councilmember Morgan —
> yes, Councilmember Byrne — yes, Councilmember Anctil — yes … (2025-04-09, Resolution 2025-R-6)

**Observed roster (9 voters across eras).** Mayor **Roger Bourke** (voting; Mayor 2021→present,
156 votes — top voter); **Elise Morgan** (Mayor Pro Tem, 143); **Carolyn Anctil** (117); **John
Byrne** (112); **Dan Schilling** (99); **Sheridan Davis** (52); **Craig Heimark** (40); and the
earlier **Cliff Curry** (4) & **Harris Sondak** (3, Mayor in 2020). Join by full name (election
names are UPPER-CASE); note **Roger Bourke sat as a councilmember in 2020** before becoming Mayor.

### Planning Commission — an as-needed Land Use Authority
Alta's PC is the town's **Land Use Authority** + General Plan author; the Mayor sits **ex
officio**. It meets 4th Wednesday **only when it has business** → a thin but real record (17 docs,
2022-06 → 2025-12; **none 2020–2021**). Every PC vote is narrative "unanimous consent" →
**tally-only** (no per-member roll call is ever printed — a source ceiling, not an extraction
loss). Land-use actions (e.g. the 2022-06-02 Wyssen Towers conditional-use permit) are captured
as `Land-Use/Zoning` / `Ordinance` motions.

## Distinctive Alta facts (read before quantitative claims)
- **Sparse cadence is correct.** ~12 council meetings/yr; PC meets only when it has business. Do
  not read low counts as gaps.
- **The Mayor votes (max roll 5).** A `Mayor <Name> — yes` roll entry is a counted vote, not a
  tie-break. Roger Bourke has 153 vote rows (Elise Morgan, 165, is the top voter).
- **Two mayors AND two Bourkes in span** (corrected 2026-07-12, T3.1(a)). Harris Sondak was
  Mayor **2020–2021**; Roger Bourke is Mayor **2022→present** (he was a Planning Commissioner
  before, never a councilmember). The 2020–21 **councilmember Bourke is MARGARET Bourke** — a
  different person. Both mayors vote; join by full name.
- **PC is tally-only + often cancelled.** 0 named PC member rows and no 2020–2021 PC minutes are
  both honest.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.
- **Elections exclude the Alta Canyon decoys.** The `ALTA CANYON REC …` special-service-district
  contests are a different entity and are correctly excluded (`VERIFICATION.md §4`).
- **6 council meetings record no formal motions** (retreats / strategic-planning / agenda-only
  work sessions) — verified honest, not extraction misses.

## Known gaps / caveats
- **No unrecovered council meetings** (`meeting_minutes/minutes_unrecovered.csv` is
  header-only). **One unrecovered PC meeting record**: 2023-11-28 — PMN holds only a
  pre-approval **DRAFT** (watermarked; authored before its pre-printed approval date), kept as a
  `pmn_backfill/` sidecar and never promoted; see `planning_commission/minutes_unrecovered.csv`.
- **PC 2020–2021 is genuinely empty** (as-needed body produced no minutes) — not a scraper miss.
- **Elections:** county-administered; in-scope (≥2020) = 2021 (council + mayor) & 2023 (council).
  The **2021 candidate tallies were privacy-suppressed** by the county (turnout below the privacy
  floor for a ~380-person town) — winners are marked external/unofficial with the outside
  cross-check embedded in `alta_races.csv`; 2023 tallies are county-certified.
- **Geo is town-membership only** — Alta elects at-large, so there are no council districts and no
  address→district tool (the standard geo layer degenerates to "is this address in Town of Alta?").
- **Cross-city:** `result`/`motion_type` are Alta-native — aggregate only via `motions_std.csv` +
  the repo-root `crosswalks/`, never the raw strings.
- **3 cosmetic malformed `db/person` rows** (mover-text artifacts, 0 votes each) — see
  `VERIFICATION.md §8`; they do not affect the exact 726==726 vote reconciliation.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`). For a
~380-pop town these ran RICHER than expected — honest-empty was overturned on CF + transcripts.
- **`packets/`** — **847 PDFs STORED (969 MB)**, Council 778 / PC 69, 2020→2026 (Alta unbundled
  its packet until mid-2025, so earlier years have more files). PMN bodies 1601/1602. doc_class
  (2026-07-16): 11 land-use staff reports classified (whole-class verified; corpus is ~90% budget/admin).
- **`housing_plans/`** — **near-empty by design (correct)**: General Plan + embedded legacy MIH
  element; Alta is below the state reporting threshold (absent from all HCD compilations).
- **`ordinances/`** — **50 rows (44 PDFs, 10 land-use)** from the static `/ordinances-resolutions/`
  page; linkage 40 high / 6 within_source / 4 none.
- **`pmn_backfill/`** — **5 minutes recovered** (label-mislabeled / cross-body-misfiled — NOT a
  pure superset even for a PMN-sourced town); sparse gaps proven via cancellation notices.
- **`transcripts/`** — 172 YouTube meeting videos (ASR captions on all) + 348 SoundCloud audio
  tracks back to 2013 (Whisper leads).
- **`campaign_finance/`** — **36 filings, 2021/2023/2025, complete**. FLAG: the 2025 general is
  documented in finance but absent from `election_results/` (extends the "Heimark won" note).

## Regenerate each layer
- **Council votes:** `python3 meeting_minutes/extract_votes.py council` (then `validate_votes.py council`).
- **PC votes:** `python3 planning_commission/extract_votes.py pc` (then `validate_votes.py pc`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent; prints
  CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (Wednesday grid). `weeks/` and `db/` are
  **derived** — regenerate, never hand-edit; rebuild `weeks/` after any change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` (default, read-only) lists Utah PMN items newer than the index max
for each dataset (council body **1601**, PC body **1602**), excluding dates already indexed.
`--fetch [--dataset meeting_minutes|planning_commission]` downloads new minutes PDFs → `raw/` →
markdown (OCR-aware) → `minutes_index.csv`, then runs the dataset's `extract_votes.py` +
`validate_votes.py`. Rebuild db + motions_std + weeks afterward (the CLI prints the reminder).
Idempotent + resumable; uses a browser UA (no bot-403 seen on PMN). Verified live 2026-07-12
(probe: 0 new for both bodies).

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated.
