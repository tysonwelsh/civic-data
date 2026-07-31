# Midvale City Council — data repository

A Salt Lake City-style civic-data repository for the **Midvale City Council**, its in-session
**Redevelopment Agency (RDA)**, and the **Planning & Zoning Commission** (Salt Lake County,
Utah; ~36k pop.; incorporated 1909), built 2026-07-12 by the `build-city-data-repo` skill.
Council + RDA + PC minutes (as markdown), extracted roll-call votes, a relational cross-body
db, public-comment availability, municipal election results, and an address→district tool —
all as markdown/CSV. See `CLAUDE.md` for analysis guidance and each subfolder's own
`CLAUDE.md`/`SCHEMA.md`; independent QA in `VERIFICATION.md` (PASS on every built dataset,
0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + RDA minutes | 2020-01-07 → 2026-06-16 | **148 md** (== 148 index) **+ 25 PMN-promoted docs** (in `pmn_backfill/text/`, merged 2026-07-16) | Revize Document Center (recorder agendas-&-minutes landing) + Utah Public Notice recovery | ✅ complete; 119 `text` + **29 `ocr`** (**2020–2021 minutes are scanned image PDFs → OCR**); **1 unrecovered** (2023-01-17 RDA session's own minutes, logged) |
| Council + RDA + MBA votes | 2020–2026 | **1,513 motions** · **4,735 vote rows** (Council 4,442 + **RDA 280** + **MBA 13**) | extracted from minutes (`extract_votes.py` + `extract_backfill_votes.py`) | ✅ verified; **named tabular roll calls**; **mayor votes ONLY on ties** (max ordinary roll = 5); trailing **`provenance`** column (`minutes` audited / `pmn_minutes` recovered) |
| PC minutes | 2020-01-08 → 2026-06-24 | **103 md** (== 103 index) | Revize Document Center (Planning & Zoning Commission landing) | ✅ complete; 87 `text` + 16 `ocr`; **1 unrecovered** (2024-08-28 corrupt scan, logged) |
| PC votes | 2020–2026 | **669 motions** · **1,994 vote rows** | extracted from minutes (`extract_votes.py`) | ✅ verified; named/voice/tabular rolls (P&Z seats up to 7) |
| Relational db (`db/civic.db`) | 2020–2026 | **2,186 motions** · **5,752 votes** · **113 referrals** (42 high / 53 med / 18 low) | standard cross-body schema | ✅ reconciles exactly (5,752 named CSV rows == 5,752 db votes, by body); `motion.provenance` = `minutes` (2,007) / `pmn_minutes` (179); see `db/SCHEMA.md` |
| Public comments | — | **header-only CSV** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — Midvale publishes no written-comment archive; see `public_comments/AVAILABILITY.md` |
| Election results | 2007 → 2025 | **39 races** · candidate + precinct tables | Salt Lake County SOVC (2019 recovered from raw SOVC) | ✅ verified; all winners match outside sources (`VERIFICATION.md`) |
| Geo (address→district) | current 5-district plan | **5 districts + 38 precincts** | official City_Council_Districts FeatureServer (ArcGIS) | ✅ tool + geojson; resolver tested (City Hall → D5) |
| Weekly bundles | 2020–2026 | **156 week bundles** | derived (`build_weeks.py`, Tuesday grid) | ✅ regenerable; PMN-promoted weeks list votes whose minutes text lives in `pmn_backfill/text/` |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council + PC motion rows) and the repo-root `crosswalks/`.

## Council structure — six-member form, the Mayor votes ONLY on ties
Midvale uses Utah's **six-member council form**: **five district councilmembers (D1–D5)**
legislate, and a separately-elected **Mayor presides and votes only to break a tie**. A full
council roll-call therefore tops out at **5**. In the entire record the Mayor appears in
**exactly one** vote row — **Mayor Robert Hale**'s tie-break on 2020-05-05 (a 2–2 split the
minutes record as "passed 3-2" after his Aye). Contrast Taylorsville/South Jordan (mayor
never votes) and Millcreek (mayor is a full 5th voter).

**Current roster (Jan 2026):** D1 **Bonnie Billings**, D2 **Paul Glover**, D3 **Heidi
Robinson**, D4 **Bryant Brown**, D5 **Denece Mikolash**, Mayor **Dustin Gettel**.

### The Gettel council→mayor transition (join carefully)
**Dustin Gettel** votes as **councilmember (D5)** 2020-01-07 → 2024-12-10, then — after Mayor
**Marcus Stevenson** (elected 2021) resigned — was **appointed mayor** (sworn in 2025-01-03)
and **won the 2025 mayoral election** (60.89%). **Denece Mikolash** was appointed to the
vacated D5 seat 2025-01-07 and then won it outright in Nov 2025. So Gettel's 2020–2024 votes
are legitimate councilmember votes; "Mayor Stevenson" is the 2022–2024 mayor; the current
mayor is Gettel (cf. Herriman's Hales council→mayor pattern). Other early members: **Quinn
Sperry** (D1, 2020–2023) and **Robert Hale** (Mayor 2018–2021, one tie-break row).

### RDA and MBA — the `body` column (two capture modes since 2026-07-16)
The Council **recesses in-session into the Redevelopment Agency board** and reconvenes; the
audited Revize minutes capture those votes as CC-doc motions tagged **`body=RDA`**. The city
ALSO files **standalone RDA board minutes** (and one **MBA** doc, `body=MBA`) that were never
on Revize — PMN-recovered and promoted 2026-07-16 with `provenance=pmn_minutes` ("Board
Member"/"Chair" roles; the Mayor presides as Chair, non-voting). Totals: **RDA 84 motions /
280 vote rows · MBA 5 motions / 13 rows.** The same councilmembers sit as the board.

## Distinctive Midvale facts (read before quantitative claims)
- **2020–2021 OCR seam.** The 2020–2021 council minutes (and a few later scans) are scanned
  image PDFs recovered via OCR (**30 council + 16 PC** files `format=ocr`; 2022+ born-digital;
  2020 has 9 `.docx` originals). OCR is good enough that roll calls parse, but ~0.4% of
  OCR-era council rows carry garbled name variants (`Geftel`/`Oustin Gettel`/`Pau! Glover`) —
  a known limitation, not fabrication (`VERIFICATION.md` §e).
- **Named tabular roll calls (high quality).** Unlike the narrative-tally councils, Midvale
  prints a per-member roll block, so most motions carry named Aye/Nay/Absent rows.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.
- **RCV pilot years.** 2021 Mayor and 2023 D3 are ranked-choice; the races file's
  `winner_pct`/`margin` are **first-choice** round-1 values (flagged in `note`), while `winner`
  is the canvassed RCV-final winner.

## Known gaps / caveats
- **1 unrecovered PC meeting** — **2024-08-28** (corrupt/blank source scan), logged in
  `planning_commission/minutes_unrecovered.csv`, never stubbed.
- **1 unrecovered RDA session** — **2023-01-17** (verified held; the PMN doc labeled "RDA
  Minutes 1-17-2023" actually contains the **2022-12-06** RDA minutes, promoted under their
  true date). Logged in `meeting_minutes/minutes_unrecovered.csv`.
- **1 documented duplicate motion** — 2025-08-19 has two same-day minutes docs (Regular +
  Truth-In-Taxation) that both print the same 5-0 consent roll call → 10 CSV rows for 5 people
  (outcome correct; the db collapses to 5). Logged in root `TODO.md` and `VERIFICATION.md`
  (D1).
- **Elections:** county-administered; only Midvale council + mayor races. **2019 recovered**
  from the raw SOVC; a **2023 bond question** is excluded from the races file.
- **Cross-city:** `result`/`motion_type` are Midvale-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **117 rows INDEX-ONLY** (110 live / 2.78 GB whole-meeting Revize bundles,
  over budget); Council 69 / PC 48; 7 dead links from the city's `<base href>` quirk.
- **`housing_plans/`** — **8 rows**: 2016 General Plan, 2019 Housing Plan + 2022 MIH Element,
  state compilation excerpts 2023–25 + SB34 (Midvale present all years).
- **`ordinances/`** — **263 rows (256 signed PDFs, 182 land-use)** from Midvale's OWN Document
  Center archive (2012–2026); linkage 107 high (0 false) / 144 none (119 pre-floor). OCR
  `O→0`/`.`-separator citation variants handled.
- **`pmn_backfill/`** — **14 genuine missing council-session dates recovered** (25 docs incl. a
  2024 cluster) via the independent PMN cross-check; PC has 0 gaps; 2020-21 scans non-upgradeable.
  ✅ **PROMOTED 2026-07-16**: 24 docs merged into `meeting_minutes/all_votes.csv` with
  `provenance=pmn_minutes` (179 motions; driver `meeting_minutes/extract_backfill_votes.py`);
  the 2023-03-30 budget retreat has no motions (honest zero); one PMN label lie corrected
  (the "1-17-2023" RDA doc is the 2022-12-06 RDA minutes).
- **`transcripts/`** — 258 city-YouTube meeting videos (2020-04→2026-07, 100% ASR captions);
  10 samples fetched; Utah Record mirror carries 0 Midvale.
- **`campaign_finance/`** — **84 filings, 2017–2025, complete roster coverage, zero
  election-record discrepancies**; acquisition layer.

## Regenerate each layer
- **Council + RDA votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation). Read `db/SCHEMA.md` first.
- **Weekly bundles:** `python3 build_weeks.py` (`city_name='Midvale'`, `meeting_weekday=1` →
  council meets 1st & 3rd **Tuesday**). `weeks/` and `db/` are **derived** — regenerate, never
  hand-edit; rebuild weeks/ after any change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` lists Revize Document Center minutes newer than each dataset's
index max (council recorder agendas-&-minutes landing; PC Planning & Zoning landing),
excluding dates already indexed or in `minutes_unrecovered.csv`; `--fetch [--dataset …]`
downloads new docs → `raw/` → markdown (OCR-aware) → `minutes_index.csv`, then extracts +
validates. Rebuild db + weeks afterward (the CLI prints the reminder). Idempotent + resumable;
uses a browser UA (the Document Center paths are space/`&`-encoded).

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated.
