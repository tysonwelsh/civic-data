# Riverton City Council — data repository

A Salt Lake City-style civic-data repository for the **Riverton City Council** and **Planning
Commission** (Salt Lake County, Utah; ~45k pop.; incorporated 1997), built 2026-07-12 by the
`build-city-data-repo` skill. Council + PC minutes (as markdown), extracted roll-call votes, a
relational cross-body db, public-comment availability, municipal election results, and an
address→district tool — all as markdown/CSV. See `CLAUDE.md` for analysis guidance and each
subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA in `VERIFICATION.md` (PASS on every
built dataset, 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2020-02-18 → 2026-06-02 | **128 md** (== 128 index) | Utah PMN (born-digital text) mirroring Granicus | ✅ complete; 128 `text` (no OCR); 0 unrecovered; + 5 recovered meetings live in `pmn_backfill/` (votes promoted 2026-07-16, `provenance=pmn_minutes`) |
| Council votes | 2020–2026 | **885 motions** (851 audited + 34 `pmn_minutes`) · **3,751 vote rows** (3,617 named) | extracted from minutes (`extract_votes.py` + `extract_backfill_votes.py`) | ✅ verified; **Mayor NON-voting except tie-breaks** (max roll = 5); 751 named roll calls + 134 tally-only |
| PC minutes | 2020-01-23 → 2026-06-11 | **119 md** (== 119 index) | Utah PMN / Granicus (body 5473) | ✅ complete; 119 `text`; 0 unrecovered; + 2 recovered meetings live in `pmn_backfill/` (votes promoted 2026-07-16) |
| PC votes | 2020–2026 | **682 motions** (672 audited + 10 `pmn_minutes`) · **1,308 vote rows** (751 named) | extracted from minutes (`extract_votes.py` + `extract_backfill_votes.py`) | ✅ verified; **named roll call ONLY on divided votes** (127) — 548 unanimous honestly unnamed + 7 died-for-lack-of-second |
| Relational db (`db/civic.db`) | 2020–2026 | **1,567 motions** · **4,370 votes** · **59 PC→Council referrals** (24 high / 22 med / 13 low) | standard cross-body schema | ✅ reconciles exactly (4,370 named CSV rows == 4,370 db votes); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md + header-only CSV** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — no published written-comment archive (in-person / Granicus eComment / emailed to recorder, none archived). `all_comments_clean.csv` is header-only by design |
| Election results | 2007 → 2025 | **39 races** (30 general + 9 primary) · candidate + precinct tables | Salt Lake County SOVC (canonical slice + raw 2019/2021 re-parse) | ✅ verified; 2019 gap + 2021 privacy-suppression RECOVERED; winners match outside sources |
| Geo (address→district) | current (2022+) + pre-2022 vintage | **35 precincts → Districts 1–5**; official district layer + prior-plan layer | Riverton official district FeatureServer + pre-2022 layer | ✅ tool + geojson present; tested (City Hall → D5) |
| Weekly bundles | 2020–2026 | **133 week bundles** | derived (`build_weeks.py`, Tuesday grid) | ✅ regenerable; weekly vote sum 3,751 == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 885 / PC 682 motion rows) and the repo-root `crosswalks/`.

## Council structure — the Mayor does NOT vote (except tie-breaks) — the Park City model
**Six-member council form:** five district councilmembers (**D1–D5**) legislate; a
separately-elected **Mayor** chairs the council and is chief executive but **casts no vote on
ordinary motions** — the Mayor votes only to **break a tie**, on hiring/firing the city manager,
or on amending the powers of the mayor's office (city's own language). **Max ordinary council
roll-call tally = 5.** This is the **Park City model** (mayoral tie-break stored as a marked
vote value), not Millcreek (mayor votes routinely) and not Taylorsville (mayor never votes).

**The one tie-break in the record: 2025-12-16.** On Resolution No. 25-62 (removal of the skate
facility) the council split **2–2** (McDougal + Pierucci Aye; Buroker + McCay Nay) and **Mayor
Trent Staggs broke the tie voting yes**. Captured verbatim in the flat CSV as
`result = "Passed (Mayor tie-break)"` + a `Trent Staggs | Aye (Mayor tie-break)` vote row;
**normalized to a plain `Aye` in `db/civic.db`** (verbatim never overwritten). See
`VERIFICATION.md` §3.

**Roster (join carefully across 2022–2026 turnover):** current council (2026) — **Andy Pierucci**
(D1), **Troy McDougal** (D2), **Alexander Johnson** (D3), **Shannon Smith** (D4), **Spencer
Haymond** (D5), **Mayor Tish Buroker**. Earlier voting members in the record: **Sheldon Stewart**
(D1, 2020→2022, → Pierucci), **Claude Wells** (D5, 2020→2023, → Haymond), **Tawnee McCay**
(D3, → Mayor candidate 2025), **Tish Buroker** (D4, councilmember → Mayor Jan 2026), and
**Trent Staggs** (councilmember → Mayor 2017–2025). 4-year staggered non-partisan terms:
**Mayor + D3 + D4** on 2009/2013/2017/2021/2025; **D1/D2/D5** on 2007/2011/2015/2019/2023.

## Distinctive Riverton facts (read before quantitative claims)
- **Mayor non-voting except tie-breaks (Park City model).** Max ordinary tally 5; the single
  tie-break (2025-12-16) is the only `Aye (Mayor tie-break)` value (a documented vocabulary
  extension → the one non-FAIL vote-value WARN).
- **Two-portal acquisition — Granicus mirrored on Utah PMN.** The city runs a **Granicus**
  meeting archive (`rivertoncity.granicus.com`), cross-posted to **Utah Public Notice**
  (`utah.gov/pmn`, PC/council body **5473**). All minutes were acquired from **PMN** (`source=pmn`)
  as clean **born-digital text PDFs — no OCR anywhere in the corpus.** The city's own Revize CMS
  lists dates only.
- **PC names members ONLY on divided votes.** The Planning Commission prints a full named roll
  call on **divided** votes (127 motions, fully attributed) and "unanimous consent" (no names) on
  unanimous ones (548 placeholders, incl. the 10 promoted `pmn_minutes` motions) — the honest
  tally-only convention. A blank member list on a
  unanimous PC motion is source style, not an extraction miss. 7 PC motions **died for lack of a
  second** (recorded with no members).
- **D3 ↔ D4 renumbered at the 2022 redistricting (Ordinance 22-07).** The election record labels
  **McCay = D3** and **Buroker = D4** (2017 & 2021); current GIS/roster label them the opposite.
  The pre-2022 GIS layer corroborates the election record. Person↔district joins **across 2022**
  must join on **person identity**, never the bare district number (D1/D2/D5 unaffected). See
  `election_results/CLAUDE.md`.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **0 unrecovered meetings** in either body — the PMN mirror is complete for the 2020 floor
  onward. **One PC index date (2020-06-09) is a genuine no-action discussion meeting** (no
  motions), so 119 PC index meetings → 118 with votes — a truthful no-vote meeting, not a drop.
- **7 additional meetings recovered via `pmn_backfill/` (2026-07-13) and promoted into the
  vote layer (2026-07-16)**: council 2020-01-07/-01-21/-02-04 (Word-era, predating the audited
  series), 2023-09-05/-11-07 + PC 2023-11-09 (Granicus-only — PMN never carried those minutes),
  and PC 2026-06-25. Their votes carry `provenance=pmn_minutes`; the minutes files stay in
  `pmn_backfill/` (`source=pmn_backfill/text/…`), not in the audited `minutes/` trees.
- **Elections:** county-administered; only Riverton council + mayor races. **2019 general +
  primary** (D1/D2/D5) and the **2021 general** (D3/D4/Mayor) were **recovered from the raw SOVC**
  — 2019 was absent from the canonical slice (sheet named `RIV Council N`, no `RIVERTON` string)
  and 2021 was privacy-suppressed at the method split (McCay D3 read 0 → recovered to 863). Mind
  the **D3↔D4 renumber** above.
- **Geo** has an **official** current district FeatureServer (35 precincts → D1–D5) **plus** a
  retained **pre-2022** layer for cross-2022 questions; see `geo/CLAUDE.md`.
- **Cross-city:** `result`/`motion_type` are Riverton-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **3,015 rows STORED (1.80 GB)**: 295 agenda outlines + 561 staff reports +
  1,757 exhibits, 2,490 sidecars (+ 402 index-only). Granicus, 3 delivery eras. Council 139 /
  PC 127 / RDA 29. doc_class (2026-07-16): 530 classified (522 staff_report / 8 development_agreement).
- **`housing_plans/`** — **8 rows**: General Plan (single-page land-use map), 2020–2024 MIH
  Implementation Plan, city + state annual reports. 2019 MIH element unrecovered (Wayback trunc).
- **`ordinances/`** — **155 ordinances (111 land-use)** from PMN adoption notices; linkage
  58 high / 93 within_source (adoption-PDF practice starts 2023).
- **`pmn_backfill/`** — **7 minutes recovered** via the Granicus-vs-repo independent diff
  (3 were meetings PMN never carried); both core bodies now complete-superset.
- **`transcripts/`** — 652 Granicus clips catalogued but caption-less; Utah Record mirror
  doesn't carry Riverton; in-scope window is Whisper-only.
- **`campaign_finance/`** — **60 filings, 2021/2023/2025, complete**; city + state folders
  merged for full coverage. Acquisition layer.

## Regenerate each layer
- **Council votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Weekly bundles:** `python3 build_weeks.py` (Tuesday grid). `weeks/` and `db/` are **derived**
  — regenerate, never hand-edit; rebuild weeks/ after any change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py` probes the portal for meetings newer than the index max in each dataset
(council 1st & 3rd Tuesday; PC 2nd & 4th Thursday), fetches originals into `raw/`, converts to
markdown, extracts, validates, and rebuilds the derived layers. Acquisition is via the Utah PMN
mirror (born-digital text; body 5473) with the Granicus archive as fallback. Uses a browser UA.

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated.
