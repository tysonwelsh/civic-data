# Holladay City Council — data repository

A Salt Lake City-style civic-data repository for the **Holladay City Council** (with in-session
**Redevelopment Agency** and **Local Building Authority** sessions) and **Planning Commission**
(Salt Lake County, Utah; ~30k pop.; incorporated **1999**), built 2026-07-12 by the
`build-city-data-repo` skill. Council + RDA + LBA + PC minutes (as markdown), extracted roll-call
votes, a relational cross-body db, public-comment availability, municipal election results, and an
address→district tool — all as markdown/CSV. See `CLAUDE.md` for analysis guidance and each
subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA in `VERIFICATION.md` (**20 PASS / 5 WARN /
0 FAIL**, 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + RDA + LBA minutes | 2020-01-08 → 2026-04-16 | **152 md** (== 152 index) | Utah PMN (public body **388**) | ✅ complete; born-digital `pdf-text` (0 OCR); 25 honestly unrecovered (retreats / not-yet-posted 2026) |
| Council + RDA + LBA votes | 2020–2026 | **702 motions** (678 Council · 21 RDA · 3 LBA) · **2,475 vote rows** (2,173 named) | extracted (`extract_votes.py`) | ✅ verified; **mayor VOTES** (max roll 6); 6 contested; 365 mayor rows |
| PC minutes | 2020-01-07 → 2026-04-28 | **71 md** (== 71 index) | Utah PMN (body **389**, 44 docs) + **27 Wayback-recovered** (former WordPress site; promoted 2026-07-16) | ✅ complete for posted years; **62 unrecovered** (2020 H2 / 2021 H2 / 2023 + a few pending — upstream gap) |
| PC votes | 2020–2026 | **328 motions** · **1,262 vote rows** (1,138 named) | extracted (`extract_votes.py`; `provenance` column: `minutes` / `wayback_minutes`) | ✅ verified; **7-member** commission (roll ≤ 7); 26 contested |
| Relational db (`db/civic.db`) | 2020–2026 | **1,030 motions** · **3,311 votes** · **5 Council←PC referrals** (all medium) | standard cross-city schema | ✅ CSV−db named-row delta +0; see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md only** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — no published written-comment archive; emailed comments read aloud + paraphrased inline |
| Election results | 2007 → 2025 | **34 races** · candidate + precinct tables | Salt Lake County SOVC (canonical county normalization) | ✅ verified; 2019 recovered, 2021 de-suppressed; 2021/2023/2025 winners match outside sources |
| Geo (address→district) | current (as amended 2022) | **5 official district polygons**; 30 precincts | Holladay ArcGIS Hub layer (NOT precinct-derived) | ✅ tool + geojson; City Hall → District 1 |
| Weekly bundles | 2020–2026 | week bundles on the Monday grid | derived (`build_weeks.py`) | ✅ regenerable; weekly vote sum 2,475 == flat total |

`result` is city-verbatim and `vote` is normalized to the controlled vocabulary; cross-city
comparison goes through `motions_std.csv` and the repo-root `crosswalks/`.

## Council structure — the Mayor VOTES (max roll = 6)
**Council–Manager form:** five district councilmembers (D1–D5) legislate alongside a
**separately-elected, voting Mayor**; an appointed **City Manager** is the executive. A full named
council roll tops out at **6** (`… Mayor Dahle-Aye`) — **365** mayor vote-rows. (Contrast:
Taylorsville/South Jordan mayors do NOT vote, roll of 5; Holladay matches Millcreek's voting
mayor.) The **Planning Commission** has no mayor and is a **7-member** body.

**Roster turned over at the Jan-2026 seating** (analysis must be date-aware):

| Seat | Through 2025 | From Jan-2026 |
|---|---|---|
| Mayor (citywide) | Robert **Dahle** | Paul **Fotheringham** |
| District 1 | Ty **Brewer** | David **Sundwall** |
| District 3 | Paul **Fotheringham** | Natalie **Bradley** |

Continuing: **Durham** (D2), **Quinn** (D4), **Gray** (D5). Non-partisan, 4-year staggered terms:
**Cycle A** (Mayor + D1 + D3) on 2009/13/17/21/**25**; **Cycle B** (D2/D4/D5) on 2007/11/15/**19**/23.

### RDA + LBA — in-record bodies
The Council recesses and reconvenes as the **Redevelopment Agency** (`body=RDA`, 21 motions / 60
rows) and the **Local Building Authority** (`body=LBA`, 3 motions / 12 rows) inside its minutes.
No separate RDA/LBA portal exists; the same councilmembers appear as Board Members / Chair.

## Distinctive Holladay facts (read before quantitative claims)
- **PMN is the spine, born-digital throughout.** Council body **388**, PC body **389**;
  `utah.gov/pmn/files/<id>.pdf`. Zero OCR; the corpus screen is CLEAN on both bodies.
- **Prose `result` strings, not tallies.** "…adopted by a unanimous vote." The numeric-tally
  validator check matches 0 by design; standardized outcomes live in `motions_std.csv`
  (Pass 856 / Fail 7 / Continued 5 / Died 1). Use those for aggregation.
- **Vote values normalized.** 2022+ minutes print some rolls as `-Yes/-No`; those are mapped to
  **Aye/Nay** (SCHEMA_SPEC §4). `all_votes.csv` carries **zero** `Yes`/`No`.
- **Narrative-tally on unanimous-consent motions** — the source prints no per-member names, so
  `member`/`vote` are honestly blank (302 council + 124 PC rows). Named rolls appear on
  substantive and contested motions.
- **PC PMN gap is upstream, not a scraper miss.** Holladay posts PC minutes to PMN only
  intermittently: **2020, 2021, and 2023 PC minutes were never posted** as Meeting-Minutes
  attachments. **27 of them (2020-01→09 + 2021-01→06) were recovered from the city's former
  WordPress site via the Wayback Machine and promoted into the audited layer 2026-07-16**
  (`provenance=wayback_minutes` in `all_votes.csv`); the remaining **62 rows** in
  `planning_commission/minutes_unrecovered.csv` (2020 H2, 2021 H2, all of 2023, + a few
  2024–26 pending) were never recoverably published on any channel.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.
- **Geo is Holladay's OWN official layer** (unlike the precinct-derived Taylorsville/South Jordan).

## Known gaps / caveats
- **Council: 25 unrecovered** (annual planning retreats that produce no minutes, a few work
  meetings, and 2026 meetings whose minutes are pending approval) — logged in
  `meeting_minutes/minutes_unrecovered.csv`, never stubbed.
- **PC: 62 unrecovered** — the residue of the 2020/2021/2023 PMN publishing gap above after
  the 27-doc Wayback recovery (2020 H2 · 2021 H2 · all 19 of 2023 · 9 recent pending).
- **Elections:** county-administered; only Holladay council + mayor races. **2019** general
  recovered from the raw SOVC; **2021** re-parsed for precinct-suppression. Election-night news
  vote counts differ from the certified SOVC totals used here (winners/margins agree).
- **10 duplicate PC vote rows** (member Layton, six 2022 meetings) collapse in the db's UNIQUE — a
  dedup follow-up is queued in the repo-root `TODO.md`.
- **Cross-city:** `result`/`motion_type` are Holladay-native — aggregate only via `motions_std.csv`
  + the repo-root `crosswalks/`.

## Regenerate each layer
```
python3 meeting_minutes/extract_votes.py     # + planning_commission/extract_votes.py
python3 meeting_minutes/validate_votes.py    # + planning_commission/validate_votes.py  (regenerates roster.csv)
python3 db/build_db.py && python3 db/build_referrals.py
python3 build_weeks.py
python3 scripts/validate_city.py holladay_city_council   # from the repo root
python3 fetch_new.py --probe                 # check PMN 388/389 for new meetings
```

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **78 packets STORED (953 MB)** from SuiteOne, Council 36 / PC 29 / RDA 7 /
  LBA 6; SuiteOne shallow (2025+), older is an honest gap.
- **`housing_plans/`** — **11 rows**: 2025 Holladay Horizons GP + MIH element (Appendix F / Ch. 5
  / Res 2025-02), 2016 prior plan, city + 4 state reports (reporting every year).
- **`ordinances/`** — **123 adopted (39 land-use)**; only 21 independent PDFs online → 102
  within_source. PMN 388 is NOT an ordinance archive here.
- **`pmn_backfill/`** — council is a complete PMN superset; **27 of the 62 missing PC minutes
  recovered** (2020-01→09 + 2021-01→06) from the former WordPress site via Wayback — **promoted
  into `planning_commission/` 2026-07-16** (`promote_backfill_minutes.py`;
  `provenance=wayback_minutes`); 35 still-missing logged in `pmn_backfill/unrecovered.csv`
  (2020 H2 · 2021 H2 · all of 2023 · the mis-uploaded 2020-04-07 — unrecoverable on any channel).
- **`transcripts/`** — SuiteOne is the current (2025+) video host (75 videos, caption-less) +
  6 genuine 2020–21 YouTube meetings (ASR). Honest 2021–2024 video gap.
- **`campaign_finance/`** — **52 filings, 2021/2023/2025 complete** (40 CF + 12 COI); acquisition
  layer; corroborates the 2025 3-way mayoral primary.
