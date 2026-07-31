# Murray City Council — data repository

A Salt Lake City-style civic-data repository for the **Murray City Municipal Council** and
**Planning Commission** (Salt Lake County, Utah; ~50k pop.; incorporated 1902), built
2026-07-11 by the `build-city-data-repo` skill. Council + PC minutes (as markdown),
extracted roll-call votes, a relational cross-body db, public-comment availability,
municipal election results, and an address→district tool — all as markdown/CSV. See
`CLAUDE.md` for analysis guidance and each subfolder's own `CLAUDE.md`; independent QA in
`VERIFICATION.md` (PASS on every built dataset, 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2020-01-07 → 2026-06-16 | **150 md** (== 150 index) | CivicPlus Archive Center (`Archive.aspx?AMID=31`) + **PMN backfill promotion 2026-07-16** (the 18 TMM-lost 2023 meetings, `source=pmn`) | ✅ complete; all `pdf-text` except 1 OCR; **the 2023 Tyler-TMM portal gap is CLOSED** (17 regular + the net-new 2023-08-21 joint special promoted from `pmn_backfill/`; 2023-07-11 proven CANCELLED) |
| Council votes | 2020–2026 | **755 motions** · **3,323 vote rows** (3,243 named + 80 tally-only) | extracted from minutes (`extract_votes.py`) | ✅ verified; **mayor NON-voting** (max council roll = 5); named roll on legislative items, voice-vote tallies unnamed |
| PC minutes | 2020-01-02 → 2026-05-07 | **120 md** (== 120 index) | CivicPlus Archive Center (`Archive.aspx?AMID=33`) + **PMN backfill promotion 2026-07-16** (59 minutes 2023–2026, `source=pmn`) | ✅ **the PC-ends-2022-11 gap is CLOSED through 2026-05-07**; only 2025-04-17 + 2025-07-17 remain minute-less (`planning_commission/minutes_unrecovered.csv`) |
| PC votes | 2020–2026 | **678 motions** · **2,708 vote rows** (2,437 named + 271 tally-only) | extracted from minutes (`extract_votes.py`) | ✅ verified; **7-member commission** (max roll = 7); voice-vote tallies unnamed |
| Relational db (`db/civic.db`) | 2020–2026 | **1,433 motions** · **5,680 named votes** · **24 PC→Council referrals** | standard cross-city schema | ✅ reconciles with the flat CSVs; see `db/SCHEMA.md`; 28 persons / 268 meetings / 2 bodies |
| Public comments | — | **header-only CSV + AVAILABILITY.md** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — Murray publishes no written-comment archive; comment is in-person / email. `all_comments_clean.csv` is the standard empty header |
| Election results | 2021 · 2023 · 2025 | **15 races** · by-candidate + by-precinct tables | Salt Lake County SOVC (filtered from `salt_lake_county/elections/`) | ✅ every winner + margin cross-checked against outside sources (0 mismatch); 2019 below the 2020 floor |
| Geo (address→district) | current | **53 precincts → Districts 1–5**; official 5-district polygons | Murray FeatureServer + SL County precincts | ✅ `address_to_district.py` tested; official district geometry (not precinct-derived) |
| Weekly bundles | 2020–2026 | derived (`build_weeks.py`, Tuesday grid) | derived | ✅ regenerable; never hand-edited |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 755 / PC 678 motion rows) and the repo-root `crosswalks/`.

## Council structure — the Mayor does NOT vote
Murray uses Utah's **council–mayor (executive-mayor) form:** five district councilmembers
(**D1–D5, no at-large seats**) legislate, and a separately-elected **Mayor is the executive**
who presides over the city but **casts no council vote**. **Max council roll-call tally = 5.**
The **Planning Commission** is a separate **7-member** appointed body (max roll = 7).

**The Hales D5 → Mayor transition (documented, verified):** **Brett Hales was the
District-5 councilmember 2020–2021** (190 recorded votes), then **won the mayoralty in 2021
and took office in 2022** — after which he casts **0** council votes (the executive mayor
does not vote). "Councilmember Hales" (2020–2021) and "Mayor Hales" (2022+) are the **same
person**; his early council votes are legitimate. He was re-elected mayor in 2025.

**Council roster over time** (`meeting_minutes/roster.csv`) — current five: **Paul Pickett
(D1), Pamela Cotter (D2), Clark Bullen (D3, won the 2025 special), Diane Turner (D4), Adam
Hock (D5)**. Earlier members in the record include Dale Cox, Kat Martinez, Rosalba Dominguez
(D3, through Dec 2024), Brett Hales (D5, 2020–2021), and several 2023 appointees (Hrechkosy,
Markham, Rodgers, later Goodman) whom voters replaced — join carefully across years.

## Meeting cadence — the join key
Council meets **Tuesday** (minutes carry the meeting date); the **Planning Commission meets
Thursday**. `build_weeks.py` buckets every record onto the Monday grid (`MEETING_WEEKDAY =
Tuesday`). Elections are point-in-time (Nov, odd years) and are NOT in the weekly bundles —
they join by **person + year + district** (normalize names; election names are UPPER-CASE).

## Known gaps / caveats (read before quantitative claims)
- **The 2023 council Tyler-TMM gap is CLOSED (promoted 2026-07-16).** All 18 previously
  missing 2023 meetings (17 regular + the net-new 2023-08-21 joint special with Millcreek)
  were recovered from Utah Public Notice (`pmn_backfill/`, identity-verified born-digital)
  and are now IN the audited `meeting_minutes/` layer (`source=pmn` in the index).
  **2023-07-11 was CANCELLED** (official PMN cancellation notice retained in
  `pmn_backfill/`) — a non-meeting, not a gap. `meeting_minutes/minutes_unrecovered.csv`
  is now header-only. See `VERIFICATION.md` §(c) + the 2026-07-16 addendum.
- **The PC-minutes-end-2022-11 gap is CLOSED through 2026-05-07 (promoted 2026-07-16).**
  59 PC minutes 2023–2026 promoted from PMN. The only remaining minute-less PC meetings are
  **2025-04-17** (no minutes ever published) and **2025-07-17** (PMN's "Meeting Minutes"
  attachment is actually the agenda) — logged in `planning_commission/minutes_unrecovered.csv`;
  4 recent 2026 dates (02-05, 05-21, 06-18, 07-02) were agenda-only as of the 2026-07-13
  retrieval (minutes post after approval). Other no-minutes PC dates 2023–2025 are
  officially-noticed cancellations (see `pmn_backfill/coverage.md`).
- **Tally-only voice votes are unnamed by design** — a "Voice vote taken, all 'Ayes.'"
  motion records mover + seconder + tally, not each Aye; the extractor leaves it
  `names_recorded:false` (one blank-member row) rather than guessing. 80 council / 271 PC
  such motions. A blank member list is a source style, not a missing extraction.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.
- **Cross-city:** `result`/`motion_type` are Murray-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md` and a
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **421 agenda packets INDEX-ONLY** (Council+CoW 232 / PC 186, 2020→2026;
  9.39 GB HEAD-probed → not stored; live URLs + exact sizes per row). Includes packets for
  the 18 TMM-lost 2023 council dates. PC packet publishing seam mid-Apr 2023→Jul 2024.
- **`housing_plans/`** — **9 docs**: 2017 General Plan + HB 462 MIH element (Ch. 9) +
  adopting Ordinance 22-29 (2022-09-20, cross-checked to the council motion) + Murray's
  excerpts from the state HCD compilations (2023/24/25 + SB 34). No compliance letter posted.
- **`ordinances/`** — **166 adopted ordinances / 172 PDFs (2021-04→2026-06), 81 land-use**,
  via PMN body 7321 (the on-portal AMID=95 archive is publicly EMPTY). Linkage ceiling is
  `medium` (Murray motions never print ordinance numbers): **145 medium / 21 low / 0 none**
  (distinct ordinances) after the 2026-07-16 minutes promotion — the 2023 enacting motions
  landed and every former `none` row resolved. ~98% Recorder scans → tesseract sidecars (171/172). 2020–Apr 2021
  texts unpublished (54 adopting motions with no recoverable text — honest gap).
- **`pmn_backfill/`** — PMN entity 213 (council body 735, PC 983). **80 docs / 101.9 MB:
  closed BOTH known gaps** — all 18 missing 2023 council meetings + 59 PC minutes 2023–2026.
  **PROMOTED into the audited layers 2026-07-16**; the folder remains the acquisition/
  provenance record (fetch log, cancellation notice, negative probes).
- **`transcripts/`** — YouTube "MURRAY CITY LIVE" (`/streams`): **339 videos mapped
  2019-10→2026-07, ASR captions on every video**; 10 sample VTTs fetched (sample-only
  policy). 86 videos cover the minutes-gap dates — a bulk caption fetch is the proposed
  follow-up.
- **`campaign_finance/`** — **131 filings, 2017–2025 cycles** (39 text / 92 scanned), every
  known candidate covered; 2017 recovered via Wayback. **ACQUISITION LAYER only** (no dollar
  extraction yet). Flags a 2021 municipal primary the election dataset doesn't carry.

## Regenerate each layer
- **Council votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Geo:** `cd geo && python3 build_precinct_district_map.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent).
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`MEETING_WEEKDAY = Tuesday`). `weeks/` and
  `db/` are **derived** — regenerate, never hand-edit; rebuild weeks/ after any change to the
  canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` lists CivicPlus Archive items newer than each dataset's
`minutes_index.csv` max date (council `AMID=31`, PC `AMID=33`); `--fetch [--dataset …]`
downloads new PDFs → `raw/`, converts to markdown, appends `minutes_index.csv`, then runs
that dataset's `extract_votes.py` + `validate_votes.py`. Rebuild db + motions_std + weeks
afterward (the CLI prints the reminder). Idempotent + resumable; uses a browser UA.

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated. Provenance map in `SOURCES.md` / `recon.md`.
