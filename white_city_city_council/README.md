# White City — data repository

A Salt Lake City-style civic-data repository for the **White City** governing body (Salt Lake
County, Utah; ~5,000 pop.), built 2026-07-12 by the `build-city-data-repo` skill and conforming
to the collection-wide standard at `/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with
`scripts/validate_city.py`). Council minutes (as markdown), extracted roll-call votes, a
relational vote db, public-comment availability, municipal election results, and an
address→district tool — all as markdown/CSV. See `CLAUDE.md` for analysis guidance and each
subfolder's own `CLAUDE.md`/`AVAILABILITY.md`; independent QA in `VERIFICATION.md`
(**23 PASS / 2 WARN / 0 FAIL**).

**Data floor: 2017** (full modern history — White City was created as a metro township in 2017;
this is an incorporation edge like Millcreek's 2016, NOT a gap). Earliest published *minutes* are
2018-01-04; 2017 is agenda-only.

## The one fact that governs everything: township → city, mid-record

White City changed its **form of government inside the data window**:

- **2017 → Apr 2024 — White City Metro Township** (Utah SB199 metro-township regime; services via
  the Greater Salt Lake **Municipal Services District**). A **5-member, all-at-large council**; the
  council selects one member as **Chair**, who carries the courtesy title **"Mayor"** (e.g.
  Paulina Flint, "Mayor, Chair"). There was **no separately-elected executive** — the "Mayor" was
  one of the five councilmembers and **voted as a member**.
- **2024-05-01 — CITY** (Utah **HB35 (2024)**), adopting a **mayor–council form**. First
  **directly-elected Mayor** (Allan Perry) + at-large council seats; new council seated **Jan 2026**.

**Net effect: across BOTH eras the voting body is 5 people and the Mayor/Chair VOTES** (max
roll-call tally = **5**). This is the **Millcreek** model, NOT the Taylorsville/South-Jordan
non-voting-mayor form. What changed is the *vote-recording format* (see the three eras below).

> **⚠ Do not confuse with the White City Water Improvement District** — a separate special
> district with its own elected board. The township/city merely rents the Water District's
> building as its meeting venue. Water-district election contests are decoys (excluded).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2018-01-04 → 2026-05-07 | **122 md** (== 122 index) | Streamline CMS (`whitecity.utah.gov`) + Utah PMN body 5805 (**5 recovered minutes promoted 2026-07-16**) | ✅ complete; 110 `text` + **12 `ocr`** (mid/late-2024 image-only scans); **2017 year lost to the PMN blob purge** (20 meetings logged unrecovered) |
| Council votes | 2018–2026 | **653 motions** · **775 vote rows** (**188 named** + 587 tally-only) | extracted from minutes (`extract_votes.py`; `provenance` column: 762 `minutes` / 13 `pmn_minutes`) | ✅ verified; **Chair/Mayor VOTES** (max tally 5); three vote-grammar eras all parse |
| Planning Commission | 2019-01-29 → 2025-05-20 | **22 md** · **106 motions / 106 rows** (1 named Abstain) | **Utah PMN body 5879** (MSD "MEETING MINUTE SUMMARY" docs; promoted from `pmn_backfill/` 2026-07-16) | ✅ **RECOVERED** (supersedes the "honestly empty" verdict); all rows `provenance=pmn_minutes`; series sporadic — 29 noticed dates without minutes logged unrecovered. `planning_commission/CLAUDE.md` |
| Relational db (`db/civic.db`) | 2018–2026 | **759 motions** · **189 votes** · 18 persons · 38 applications · 0 referrals | standard cross-city schema | ✅ reconciles exactly (189 CSV named rows == 189 db votes, 0 dropped); Council + PlanningCommission bodies. `db/SCHEMA.md` |
| Public comments | — | `all_comments_clean.csv` **header-only** | n/a — SUBMIT-ONLY / in-meeting | ⚠ **HONEST-EMPTY** — no published written-comment archive. `public_comments/AVAILABILITY.md` |
| Election results | 2019 → 2025 | **5 races** · candidate + precinct tables | Salt Lake County SOVC (+ raw 2019 re-parse) | ✅ verified; 2019 recovered + cross-checked to the canvass minutes; **2017 & 2021 = genuine no-council-election years** |
| Geo (address→district) | current | **at-large** (no districts); city_boundary + 6 precincts | precinct-derived (no official layer) | ✅ tool + geojson present; White City is all-at-large, so it resolves to one body |
| Weekly bundles | 2018–2026 | **Thursday grid** | derived (`build_weeks.py`) | ✅ regenerable; weekly vote sum 775 == flat (council) total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`meeting_minutes/motions_std.csv` (653 rows) + `planning_commission/motions_std.csv`
(106 rows) and the repo-root `crosswalks/`.

## The three vote-grammar eras (read before any vote-attribution claim)

1. **Narrative-tally (2018–2025).** Mover + seconder named; outcome is a prose tally ("The motion
   passed unanimously"); **no per-member Aye/Nay list**. The parser leaves the members unnamed
   rather than guessing → these are **tally-only rows** (blank `member`/`vote`). A blank member
   list here is a source style, not an extraction miss. This is the bulk of the record (587 of
   775 council rows). The PC dataset shares the ceiling in MSD form ("Commissioners voted
   unanimous in favor" — tally-only placeholders; see `planning_commission/CLAUDE.md`).
2. **Narrative-named-dissent (2020–2022, + one 2024 case).** The printed string is often
   `Pass (unanimous)` / `3-1 Pass`, but a **single named dissenter/abstainer** is recorded
   (Councilmember **Scott Little** casts every 2020–2022 `Nay`/`Abstain`; **Tyler Huish**
   abstains once in 2024). The majority stays honestly **unnamed**. Because a "unanimous" string
   can carry a named non-Aye row, the counted rows do not equal the string tally — this **drives
   the `f.tally` validator WARN (53.6%) by design**, and is verified faithful in `VERIFICATION.md`.
3. **Full named roll call (2026+).** Every motion prints a per-member Aye/Nay and **the Mayor
   votes** (`Mayor Allan Perry — Aye` …). 150 of the 188 council named rows are here.

## Roster (OBSERVED, 10 people)

`meeting_minutes/roster.csv` (observed from named votes + movers/seconders):

| Person | Role across the record |
|---|---|
| **Allan Perry** | Council at-large 2018–2025 → **elected Mayor 2026+** (voting) |
| **Paulina Flint** | **Chair / "Mayor"** (voting), township era 2018–2025; lost the 2025 mayoral race |
| **Linda Price** | Council at-large, 2018 → present (2026 Seat B) |
| **Greg Shelton** | Council at-large 2023+ |
| **Tyler Huish** | Council at-large 2024+ |
| **Neil Mahoney** | Council at-large 2026+ (Mayor Pro-Tem; beat incumbent Cardenaz) |
| **Phillip Cardenaz** | Council at-large 2021–2025 |
| **Scott Little** | Council at-large 2020–2022 (the sole named dissenter of that era; d. 2022) |
| **Kay Dickerson** | Council at-large 2018–2021 |
| **Cody Cutler** | Council at-large 2018–2019 |

Only **6** of the 10 cast a *named* vote (the db `role` table): the four who appear only in the
pre-2026 narrative-tally era (Cutler, Dickerson, Flint, Cardenaz) show up as movers/seconders but
**never in a per-member roll call** — an honest recording limit, not a data miss.

## Known gaps / caveats (all documented, none filled)

- **2017 minutes lost to the PMN blob purge** — the council was seated Jan 2017 and its minutes
  WERE posted to PMN, but the pre-~2019 file blobs are purged (404); earliest minutes on disk are
  2018-01-04. 20 proven-unrecoverable meetings in `meeting_minutes/minutes_unrecovered.csv`.
- **Planning Commission minutes exist ONLY on PMN body 5879 and are sporadic** — 22 meetings
  recovered (2019→2025, promoted 2026-07-16); 29 further noticed PC dates have no minutes
  (`planning_commission/minutes_unrecovered.csv`); 2024–2026 PC meetings mostly cancelled.
  39 PC procedural motions print no outcome (empty `result` = honest NULL, not failure).
- **Public comments submit-only** — honest-empty.
- **Vote-value ceiling:** the council records only `Aye`/`Nay`/`Abstain`; absences appear only as
  narrative prose ("Council Member Dickerson was absent for the vote"), never as a vote row.
- **Elections:** county-administered; only White City council + mayor races. **2019 recovered**
  from the raw SOVC and cross-checked to the canvass minutes. **2017 & 2021 had no White City
  council election** (the at-large seats were on the 2019/2023/2025 cycle).
- **No `roster/` rolling-roster layer yet** — a follow-up via the `update-council-roster` skill.
- **Cross-city:** `result`/`motion_type` are White-City-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Regenerate each layer

- **Council votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then its `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent; prints
  CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Weekly bundles:** `python3 build_weeks.py` (`CITY="White City"`, `MEETING_WEEKDAY=Thursday`).
- **Sources index:** `python3 ../scripts/build_sources_index.py white_city`.

`weeks/` and `db/` are **derived** — regenerate, never hand-edit; rebuild `weeks/` after any change
to the canonical CSVs. Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/`
originals, never modified).

## Keeping it current

`python3 fetch_new.py --probe` lists Streamline year-page documents newer than the index max
(browser-UA; the site is behind a Cloudfront CDN and serves a browser UA), plus a read-only Utah
PMN body-5805 cross-check; `--fetch` downloads new minutes → `raw/` → markdown (OCR-aware) →
`minutes_index.csv`, then extracts + validates. Rebuild db + weeks afterward.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers (own CLAUDE.md/AVAILABILITY.md; all validate PASS).
✅ 2026-07-16: pmn_backfill's recoveries were PROMOTED into the core — 22 PC minutes now populate
`planning_commission/` and 5 council minutes are merged into `meeting_minutes/` (provenance=pmn_minutes).
- **`packets/`** — 99 STORED (574 MB), Council 92 + PC 7, 2018→2026 (township + city eras).
- **`housing_plans/`** — 8 rows; 2022 GP + MIH plan (MSD-hosted); reports every state year.
- **`ordinances/`** — 136 instruments (28 ord + 108 res, 13 land-use) from MunicipalCodeOnline S3;
  95 high-linkage.
- **`pmn_backfill/`** — 5 council + 22 PC minutes recovered (**both promoted into the core
  2026-07-16**); 2017 council year lost to the PMN purge.
- **`transcripts/`** — audio-first: 13 MP3/M4A recordings (2025+), 0 captions, Whisper candidates.
- **`campaign_finance/`** — 2025 cycle complete (18 reports + 10 COI); 2023 township an honest gap.
