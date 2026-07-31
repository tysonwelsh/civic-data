# Herriman City Council — data repository

A Salt Lake City-style civic-data repository for the **Herriman City Council**, its
**in-session agency bodies** (CDRA / HCSEA / HCFSA), and the **Planning Commission** (Salt
Lake County, Utah; ~60k pop.; incorporated 1999), built 2026-07-11 by the
`build-city-data-repo` skill. Council + agency + PC minutes (as markdown), extracted
roll-call votes, a relational cross-body db, public-comment availability, municipal election
results, and an address→district tool — all as markdown/CSV. See `CLAUDE.md` for analysis
guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA + external
election cross-check in `VERIFICATION.md` (PASS on every built dataset, 0 FAIL).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + agency minutes | 2020-01-08 → 2026-05-27 | **180 audited md** + **55 PMN-promoted docs** (in `pmn_backfill/text/`, merged into the vote layer 2026-07-16) | PrimeGov (committeeId 3) + legacy S3 (2020) + Utah PMN (promoted) | ✅ 2 audited agenda-compilation wrong-docs deindexed 2026-07-16 (raw retained); the only remaining true gap is 2020-07-29 joint (see `meeting_minutes/minutes_unrecovered.csv`) |
| Council + agency votes | 2020–2026 | **1,343 motions** · **4,322 vote rows** (3,726 named) | extracted from minutes (`extract_votes.py` + `extract_backfill_votes.py`) | ✅ verified; **MAYOR VOTES** — full council roll = **5** (D1–D4 + Mayor); rows: Council 3,988 · CDRA 152 · HCSEA 95 · HCFSA 87; **`provenance` 14th column** (`minutes` 3,645 / `pmn_minutes` 677) |
| PC minutes | 2020-01-02 → 2026-05-20 | **130 audited md** + **11 PMN-promoted docs** | PrimeGov (committeeId 14) + legacy S3 (2020) + Utah PMN (promoted) | ✅ 2 remaining true gaps in `planning_commission/minutes_unrecovered.csv` (2022-04-21 mislabeled source file; 2023-11-01 draft-only) |
| PC votes | 2020–2026 | **921 motions** (129 recommendations · 321 final actions · 471 procedural per `motions_std.csv` action_class) · **3,642 vote rows** (3,206 named) | extracted from minutes (`extract_votes.py` + `extract_backfill_votes.py`) | ✅ verified; 2020 `Lorin Powell` source typo retained verbatim (5 rows incl. one promoted); `provenance` column as above (272 `pmn_minutes` rows) |
| Relational db (`db/civic.db`) | 2020–2026 | **2,264 motions** · **6,932 votes** · **51 PC→Council referrals** (23 high / 22 med / 6 low) | standard cross-city schema | ✅ reconciles exactly (named CSV rows == db votes); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md + header-only CSV** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — PrimeGov eComment / Request-To-Speak are submission-only; no published written-comment archive |
| Election results | 2007 → 2025 | **38 races** · candidate + precinct tables | Salt Lake County Clerk SOVC (+ raw re-parse) | ✅ verified; **2019/2011/2021 recovered** from raw SOVC; all winners/margins match outside sources |
| Geo (address→district) | current / post-redistricting | **4 districts** (official FeatureServer polygons) · 44 precincts | Herriman GIS FeatureServer | ✅ tool + geojson present; City Hall → District 2 (tested) |
| Weekly bundles | 2020–2026 | derived (`build_weeks.py`, Wednesday grid) | derived | ✅ regenerable; weekly vote sum 3,691 == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 1,343 / PC 921 motion rows) and the repo-root `crosswalks/`.

## Council structure — the Mayor VOTES (max tally 5)
Herriman uses Utah's **six-member council form in which the Mayor is a full voting member**
(the **Millcreek** model — NOT the Taylorsville/South Jordan executive-mayor model where the
mayor is non-voting). Four district councilmembers (D1–D4) **plus the Mayor** all cast
roll-call votes, so a full council roll = **5**. Verified at source across both mayoralties:
Mayor **David Watts** (2020–2021) casts Aye/Nay in the roll (e.g. a decisive Nay on a 3:2
2020-01-08 vote); Mayor **Lorin Palmer** (2022+) likewise (167 and 478 vote rows
respectively). See `VERIFICATION.md` §4 for the quoted roll calls. ⚠ This **corrects**
`recon.md`, which had assumed the Mayor was non-voting (max tally 4).

**Roster of 9 (join carefully):** current — Mayor **Lorin Palmer**, **Jared Henderson**
(D1), **Teddy Hodges** (D2), **Matt Basham** (D3, from 2026), **Terrah Anderson** (D4, from
2025 off-cycle special). Earlier voters in the record — Mayor **David Watts** (2020–2021),
**Clint Smith** (2020–2021), **Sherrie Ohrn** (2020–2025), **Steven Shields** (2020–2025).
**Lorin Palmer also sat on the Planning Commission (2020–2021) before becoming Mayor** — one
`person`, two `role` rows, so a person-level join spans both bodies by design.

### Agency bodies — CDRA / HCSEA / HCFSA
Three district bodies convene around council meetings, published as **separate minutes
docs** and tagged by the `body` column:
- **CDRA** — Community Development & Renewal Agency (152 vote rows / 64 motions)
- **HCSEA** — Herriman City Safety Enforcement Area (95 rows / 39 motions)
- **HCFSA** — Herriman City Fire Service Area (87 rows / 31 motions)

The same officials sit as "Trustee/Board Member/Director" (the mayor as Chair). Most
standalone agency minutes reach the record via Utah PMN (promoted 2026-07-16,
`provenance=pmn_minutes`); a handful came from the portal/S3 at build time.
One retained source anomaly: the 2020-05-27 HCSEA roll prints "Trustee Nicole Martin"
(a 2019-era trustee) though attendance lists Shields — kept verbatim, never corrected.

## Distinctive Herriman facts (read before quantitative claims)
- **The Mayor votes** — the single most important structural fact (see above). Do **not**
  read a `Mayor <Name>` roll entry as a presiding non-voter.
- **Two-portal minutes.** PrimeGov (2021-01→present) + a 2020 backfill from the city's
  **legacy AWS S3 agenda bucket** — PrimeGov does not retain 2020. Both are real minutes; the
  `source` column distinguishes them (`primegov` / `s3-legacy`).
- **Named + tally-only mix.** Most motions print a full named roll (Mayor + members); short
  procedural motions print `all voted aye` (tally-only, one placeholder row, member blank —
  honest, not a miss).
- **2020 `Lorin Powell` source typo** — 4 PC rows conflate two real 2020 seat-holders (Andy
  Powell + Lorin Palmer). Retained verbatim, never guess-merged.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **2020 interior date gaps** were believed to be COVID-era cancellations (portal 403s).
  ⚠ **CORRECTION (2026-07-13): only half right** — 9 gaps are PROVEN cancellations (proof
  notices in `pmn_backfill/`), and 12 were real meetings. ✅ **PROMOTED (2026-07-16)**:
  the recovered minutes are merged into the vote layer (`provenance=pmn_minutes`); each
  dataset now has a `minutes_unrecovered.csv` for the remaining true gaps (2020-07-29
  joint; PC 2022-04-21 + 2023-11-01).
- **Standalone CDRA/HCSEA/HCFSA minutes were ABSENT from the combined council docs**
  (systemically from ~2024) — recovered via PMN and ✅ **promoted 2026-07-16** under their
  own `body` values. Two Appeal Authority minutes (2025-02-20, 2026-06-09) remain
  catalogued in `pmn_backfill/` only — no appeals body exists in the city model yet.
- **Wrong-doc repairs (2026-07-16):** the portal doc indexed as the 2021-01-13 "City
  Council Meeting" is actually the CDRA minutes (re-tagged `body=CDRA`; the real RCCM
  minutes were fetched from PMN and promoted); two 2021-10-13 PrimeGov compiled docs were
  agenda compilations, one of which embedded the FULL 2021-08-11 minutes and had produced
  18 wrong-dated motions — both deindexed (raw PDFs retained), the motions now correctly
  dated 2021-08-11 via the promoted PMN doc.
- **24 zero-motion minutes docs** (special/closed-session/adjournment-only meetings) are
  indexed but correctly carry no votes and no db `meeting` row.
- **Elections:** county-administered; only Herriman council + mayor races. **2019/2011/2021**
  recovered from the raw SOVC; **2025 D4 is an off-cycle 2-year short-term special** (Terrah
  Anderson), flagged in `note`.
- **Geo is current/post-redistricting vintage** (official FeatureServer) — a pre-redistricting
  address near a moved boundary may mis-assign. See `geo/CLAUDE.md`.
- **Cross-city:** `result`/`motion_type` are Herriman-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **372 packets INDEX-ONLY** (Council 190 / PC 121 / agencies 53 / Joint 8;
  2020→2026; 11.43 GiB probed, not stored; live URLs + sizes). 2020 packets found on the
  legacy S3 bucket (32 indexed).
- **`housing_plans/`** — **11 docs**: 2022 "Herriman Next" General Plan, MIH 2019 (Wayback)
  + 2022 (+ signed Ord 2022-38), city 2020/2021 annual reports, state compilations 2023–25
  + SB 34.
- **`ordinances/`** — **274 ordinances (194 in-window, 130 land-use)**: MunicipalCodeOnline
  S3 full texts (111 PDFs) + 190 PMN Recorder notices. Linkage 125 high / 42 within_source.
- **`pmn_backfill/`** — **71 minutes recovered + 9 proven 2020 cancellations** (see Known
  gaps corrections above). ✅ **66 docs promoted into the vote layer 2026-07-16**
  (`provenance=pmn_minutes`); not promoted: 1 duplicate, 1 draft, 1 mislabeled file,
  2 Appeal Authority docs (no body in the model).
- **`transcripts/`** — **677 YouTube meeting videos mapped** (2017-11→2026-07), ASR captions
  on all; 10 samples fetched; 41 no-minutes videos identified.
- **`campaign_finance/`** — **50 filings, 2021/2023/2025** (2021+2023 Wayback-only);
  acquisition layer. Flags a 2021 mayoral primary missing from the election record.

## Regenerate each layer
- **Council + agency votes:** `python3 meeting_minutes/extract_votes.py` then
  `python3 meeting_minutes/extract_backfill_votes.py` (REQUIRED — merges the promoted
  PMN docs; skipping it drops the `pmn_minutes` rows), then `validate_votes.py`.
- **PC votes:** `python3 planning_commission/extract_votes.py` then
  `python3 planning_commission/extract_backfill_votes.py`, then `validate_votes.py`.
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Geo:** `cd geo && python3 build_geo.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`MEETING_WEEKDAY = Wednesday`). `weeks/` and
  `db/` are **derived** — regenerate, never hand-edit; rebuild weeks/ after any change to the
  canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` lists PrimeGov items newer than the index max for each dataset
(council committeeId 3, PC committeeId 14), excluding dates already indexed; `--fetch`
downloads new docs → `raw/` → markdown → `minutes_index.csv`, then extracts + validates.
Rebuild db + motions_std + weeks afterward. Idempotent + resumable.

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated. Provenance map: `recon.md`, `SOURCES.md`,
`sources.csv`.
