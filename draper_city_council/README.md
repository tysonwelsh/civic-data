# Draper City Council — data repository

A Salt Lake City-style civic-data repository for the **Draper City Council** and **Planning
Commission** (Draper straddles **Salt Lake** (primary) and **Utah** counties, Utah; ~51k pop.;
incorporated 1978), built 2026-07-11 by the `build-city-data-repo` skill. Council + PC minutes (as
markdown), extracted roll-call votes, a relational cross-body db, public-comment availability,
municipal election results, and an address→membership tool — all as markdown/CSV. See `CLAUDE.md`
for analysis guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA in
`VERIFICATION.md` (PASS on every built dataset, 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2020-01-14 → 2026-06-09 | **155 md** (== 155 index) | Granicus (`draper.granicus.com`, MinutesViewer) + **4 PMN promotions** (`source=pmn`, 2026-07-16) | ✅ complete; **all 155 `text`** (born-digital PDFs); **Recap-vs-Minutes trap resolved** — kept full Minutes, dropped every tally-only Recap; 1 recap-only-pending |
| Council votes | 2020–2026 | **882 motions** · **3,848 vote rows** (3,719 named) | extracted from minutes (`extract_votes.py`; `provenance` column: 43 rows `pmn_minutes`) | ✅ verified; **Mayor NON-voting** (max tally 5) except **1 tie-break** (2024-10-15); named `Yes/No/Absent` grids; 15 contested |
| PC minutes | 2020-01-09 → 2026-05-28 | **143 md** (== 143 index) | Granicus (same portal) + **2 PMN promotions** (2026-07-16) | ✅ complete; all 143 `text`; 3 pending-adoption |
| PC votes | 2020–2026 | **911 motions** · **4,301 vote rows** (4,082 named) | extracted from minutes (`extract_votes.py`; 89 rows `pmn_minutes`) | ✅ verified; **very active land-use body**, **214 contested**; case numbers `YYYY-NNNN-TYPE` (185+ distinct) |
| Relational db (`db/civic.db`) | 2020–2026 | **1,793 motions** · **7,801 votes** · **5 PC→Council referrals** (all medium) | standard cross-body schema | ✅ reconciles exactly (7,801 named CSV rows == 7,801 db votes; 229 contested); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md + header-only CSV** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — no published written-comment archive; comment is in-person / email (`public.comment@draper.ut.us`). `all_comments_clean.csv` is header-only by design |
| Election results | 2007 → 2025 | **23 races** · candidate + precinct tables | Salt Lake County SOVC (+ 2019 & 2025 raw re-parse) | ✅ verified; **all AT-LARGE**; 2019 general + 2021 general recovered; **2025 re-parsed** (upstream county long-file bug); winners match outside sources |
| Geo (address→membership) | current | **33 precincts** (two-county union) + city boundary | UGRC (SL CountyID 18 + Utah CountyID 25) | ✅ tool + geojson present; **NO districts** — returns Draper membership + "At-Large" |
| Weekly bundles | 2020–2026 | **151 week bundles** | derived (`build_weeks.py`, Monday grid) | ✅ regenerable; weekly vote sum 3,848 == flat **Council** total (PC not bucketed — collection convention) |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 882 / PC 911 motion rows) and the repo-root `crosswalks/`.

## Council structure — 5 AT-LARGE seats + a NON-voting Mayor
Draper uses Utah's **council–mayor (executive-mayor) form**: **five councilmembers, ALL elected
AT-LARGE — there are NO districts**, plus a **separately-elected Mayor** who is the executive and
**casts no council vote**. A full council roll-call therefore tops out at **5**. **Mayor Troy K.
Walker** appears in **exactly one** vote row in the entire corpus — the **2024-10-15** tie-break on
**Ordinance #1625** (`3-2 Pass`), where he broke a 2-2 split among the five members (recorded as a
plain `Aye`, not a special note field). This differs from Millcreek (mayor votes on every roll) and
matches South Jordan / Taylorsville (mayor uncounted), but Draper is **all at-large** — unlike those
districted councils.

**Roster observed across eras (join by full name):** Green, Johnson, T. Lowery, F. Lowry, Vawdrey,
Roberts, Dahlin (Dahlin won a new 2-year seat in 2025, replacing Vawdrey). Mayor **Troy Walker**
throughout (elected 2013, re-elected 2017/2021/2025). Terms are 4-year staggered, non-partisan;
council races are multi-winner "vote-for-N" fields (top N vote-getters seat the N open seats).

## Distinctive Draper facts (read before quantitative claims)
- **Granicus Recap-vs-Minutes trap.** Recent meetings publish BOTH a tally-only 1-page **Recap** and
  the full **Minutes** behind a JS document selector. The build kept the full Minutes (named
  roll-call grids) and dropped every Recap; verified that **no tally-only Recap slipped into the
  index** and that the recap-only 2026-07-07 meeting is withheld, not stubbed (`VERIFICATION.md` §4).
- **PC is the busy, contested body.** The Planning Commission (Thursday) runs a heavy land-use
  docket — **214 contested** motions vs the Council's 15 — and keys items to case numbers
  `YYYY-NNNN-TYPE` (`USE`/`SUB`/`MA`/`VAR`/`SP`). Its named `Yes/No/Abstained/Not-Participating/Absent`
  grid parses cleanly; Final Action vs Positive Recommendation is preserved in `result`.
- **Two-county straddle; SL County runs the whole election.** Draper spans Salt Lake (primary) and
  Utah counties; `geo/precincts.geojson` is a **two-county union** (CountyID 18 + 25). **Salt Lake
  County administers the entire city election**, so all races are on the SL County SOVC.
- **2025 election re-parse (upstream county bug).** The canonical Salt Lake County long file
  **undercounts** 2025 Draper (it dropped Utah-vintage `25DR0N` precinct labels); Draper's 2025 races
  here are **re-parsed from the raw SOVC** and reconcile to the certified totals (and to KSL/*Draper
  Journal* exactly). See `SOURCES.md` and `TODO.md`.
- **2021 was Ranked-Choice Voting** (Draper's RCV pilot). The row stores first-choice tallies; the
  winner is correct but `winner_pct` is a first-choice share, not the RCV final — treat like Millcreek.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **PROMOTED 2026-07-16:** the 3 former broken-Granicus-stub gaps (Council **2021-07-20**, PC
  **2020-12-10**, PC **2024-10-10**) and the **3 August Truth-in-Taxation specials Granicus never
  listed** (2022-08-24, 2024-08-14, 2025-08-13) are now IN the audited layers — `minutes_index.csv`
  `source=pmn`, vote rows tagged `provenance=pmn_minutes` (new trailing column). The former
  Council **2023-10-15** unrecovered row was a **phantom** (a Sunday; no such meeting on Granicus
  or PMN — both hold the real 2023-10-17 minutes, long indexed) and the PC **2024-03-14** row was
  **stale** (doc in the index) — both removed. Remaining honest gaps: Council 2026-07-07
  (recap-only-pending) + PC 2026-06-11/06-25/07-09 (pending adoption), in the respective
  `minutes_unrecovered.csv`. See `VERIFICATION.md` 2026-07-16 addendum.
- **One logged extraction miss:** the **2025-08-26 Board of Canvassers** meeting has a named
  roll-call grid (Resolution #25-42, ceremonial canvass) the extractor did not capture — 1 motion,
  no legislative impact; queued in `TODO.md` (`VERIFICATION.md` §7).
- **Elections:** county-administered; only Draper council + mayor races. 2019 general + 2021 general
  recovered from raw SOVC; 2025 re-parsed (§ above). 2021 is RCV; 2025 council is a **2-year
  unexpired/short term** (Dahlin), flagged in `note`.
- **Geo has NO districts** — Draper is all at-large. The tool returns Draper membership + "At-Large";
  boundaries are the current two-county union. See `geo/CLAUDE.md`.
- **Cross-city:** `result`/`motion_type` are Draper-native — aggregate only via `motions_std.csv` +
  the repo-root `crosswalks/`, never the raw strings.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **4,721 rows STORED (1.62 GB)**: 339 agendas + 1,821 staff reports +
  2,047 exhibits on disk with 3,591 text sidecars (373 oversize exhibits + 134 bundled
  full_packets index-only). Council 2,939 / PC 1,594 / agencies 188; 2020→2026.
  doc_class (2026-07-16): 922 classified (895 staff_report / 18 plan_amendment / 9 development_agreement), 676 text-linked + 243 index-only.
- **`housing_plans/`** — **12 rows**: 2019 General Plan, MIH via Ord #1561 (2022) + GP Ch.4
  via Ord #1623 (2024), annual reports 2020–2025 (Wayback recoveries; 2021 unrecovered).
- **`ordinances/`** — **276 ordinances (#1344→#1726, 168 land-use)** from PMN Recorder
  notices; linkage **182 high** / 69 within_source / 5 none — #1494/#1496/#1497 resolved to
  their 2021-07-20 enacting motions (high) by the 2026-07-16 minutes promotion.
- **`pmn_backfill/`** — **6 meetings recovered** incl. the 2021-07-20 stub-gap and 3 August
  Truth-in-Taxation specials never listed on Granicus. **PROMOTED into the audited layers
  2026-07-16** (`source=pmn` index rows, `provenance=pmn_minutes` vote rows).
- **`transcripts/`** — Granicus video-complete (1,426 clips mapped) but caption-less;
  third-party mirror covers 2026 only (25 meetings, 10 samples fetched). Whisper proposed.
- **`campaign_finance/`** — **125 filings 2011–2025** via the guest-GET-able Tyler EagleWeb
  portal (sole source for the 2023 cycle); acquisition layer. Flags: 2025 canceled race
  corroborated; 2019 primary was scheduled then not held.

## Regenerate each layer
- **Council votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent; prints
  CSV↔db reconciliation). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`MEETING_WEEKDAY=1` → council Tuesday grid). `weeks/`
  and `db/` are **derived** — regenerate, never hand-edit; rebuild `weeks/` after any change to the
  canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` lists Granicus MinutesViewer items newer than the index max for each
dataset (council + PC), excluding dates already indexed or in `minutes_unrecovered.csv`; `--fetch`
downloads new docs → `raw/` → markdown → `minutes_index.csv`, then extracts + validates. Rebuild db +
motions_std + weeks afterward. **When resolving a recent meeting, keep the full Minutes and drop the
Recap** (the trap above). Uses a browser UA (the Granicus host 403s bare bots).

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never modified).
`weeks/` and `db/` are regenerated.
