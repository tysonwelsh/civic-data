# South Salt Lake City Council — data repository

A Salt Lake City-style civic-data repository for the **South Salt Lake City Council**,
**Redevelopment Agency (RDA)**, and **Planning Commission** (Salt Lake County, Utah; ~26k
pop.; incorporated 1938), built 2026-07-12 by the `build-city-data-repo` skill. Council + RDA
+ PC minutes (as markdown), extracted roll-call votes, a relational cross-body db,
public-comment availability, municipal election results, and an address→district tool — all
as markdown/CSV. See `CLAUDE.md` for analysis guidance and each subfolder's own
`CLAUDE.md`/`SCHEMA.md`; independent QA in `VERIFICATION.md` (PASS on every built dataset, 0
FAIL); the coverage story in `COVERAGE.md`. Data floor: **2020** (SSL is an old city; 2020 is
a normal floor, not an incorporation edge).

## ⚠ The headline: SSL rarely publishes recorded council minutes (an HONEST gap)

South Salt Lake's minutes publication is label-hostile on both portals (REVISED 2026-07-16).
The PMN **"Meeting Minutes" attachment slot is unreliable: it very often serves the AGENDA
PACKET** (a 10–100 MB PDF headed "REGULAR MEETING AGENDA", no roll call) *even when the file
is labelled `… RC Minutes.pdf`*. The CivicPlus AgendaCenter's visible *Minutes* slot serves
the packet too — but its hidden **`ArchivedMinutes` previous-version slot holds genuine
recorded roll-call minutes**: the 2026-07-13 `pmn_backfill/` sweep recovered 130 of them, and
on **2026-07-16 119 verified docs (2022–2026) were promoted into the audited layer** (Council
75 / RDA 29 / PC 15; the other 11 were agenda packets or duplicates of audited meetings).
Every candidate is **content-detected and content-classified** — portal labels lie (most
recovered "work meeting" files are regular-meeting minutes).

**Net effect: council regulars are covered 2020–early-2021 AND 2022-09 → 2026-06; recorded PC
minutes begin 2022-01-20** (2020–2021 PC genuinely unpublished). The honest residual — **221**
agenda-only meetings, dominated by council WORK meetings (117) plus mid-2021→mid-2022 council
regulars and 19 RDA dates — is logged in each dataset's `minutes_unrecovered.csv`. It is a
publication gap at the city, **not** a scraper miss. Vote rows carry a `provenance` column
(`minutes` = PMN-harvested; `agendacenter_minutes` = the promoted recoveries). Read
`COVERAGE.md` before any quantitative claim.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| **Council minutes** | 2020 → 2026 | **95 md** (RC 87 / WM 4 / SM 3 / TT 1; 75 promoted 2026-07-16) | PMN body **1295** + AgendaCenter `ArchivedMinutes` | ✅ complete for what SSL published; **178 agenda-only dates logged unrecovered** (117 of them work meetings). born-digital `pdf-text` |
| **RDA minutes** | 2020 → 2026 | **43 md** (29 promoted) | PMN body **1296** + AgendaCenter | ✅ RDA board = the 7 councilmembers; 19 agenda-only/no-action dates logged unrecovered |
| **PC minutes** | **2022-01-20** → 2026 | **60 md** (PC 54 / WM 6; 15 promoted) | PMN body **1297** + AgendaCenter | ✅ **2020–2021 never published** (honest gap; 2022 WAS published — on the AgendaCenter); 17 later gaps logged |
| **Council + RDA votes** | 2020–2026 | **680 motions** (555 Council + 125 RDA) · **4,606 vote rows** | extracted from minutes (`extract_votes.py`) | ✅ verified; **mayor NON-voting** (max tally 7, 0 mayor rows); `result` is the SYNTHESIZED `<aye>-<nay> Pass\|Fail` (SSL prints none); `provenance` column separates PMN-era vs promoted docs |
| **PC votes** | 2022–2026 | **286 motions** · **1,652 vote rows** | extracted from minutes (`extract_votes.py`) | ✅ verified; `Commissioner <Name> – Aye;` grammar; up to 8 seats; tally-only motions honest (`names_recorded:false`) |
| **Relational db (`db/civic.db`)** | 2020–2026 | **966 motions** · **6,253 votes** · **43 referrals** | standard cross-city schema | ✅ reconciles exactly (6,253 named CSV rows == 6,253 db votes, delta 0); referral layer restored by the promotion (40 Council←RDA + 3 Council←PC, all medium) |
| **Public comments** | — | **AVAILABILITY.md only** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — no published written-comment archive (in-person / Zoom / connect line). `all_comments_clean.csv` header-only |
| **Election results** | 2007 → 2025 | **52 races** · candidate + precinct tables | Salt Lake County SOVC | ✅ verified; **2011 & 2019 re-parsed** from raw SOVC; 2021 recovered from privacy-suppression; 2025 At-Large 2-yr special flagged |
| **Geo (address→district)** | current / post-2020 | **5 official district polygons** | SSL's OWN ArcGIS FeatureServer | ✅ tool + geojson present; At-Large (2) + Mayor are city-wide (no polygon) |
| **Weekly bundles** | 2020–2026 | derived (`build_weeks.py`, Wednesday grid) | derived | ✅ regenerable; weekly council/RDA vote sum 985 == flat total |

`result` and `motion_type` are city-native; cross-city comparison goes through
`motions_std.csv` (Council/RDA 680 / PC 286 motion rows) and the repo-root `crosswalks/`.

## Council structure — strong-mayor, the Mayor does NOT vote
**Council–Mayor (strong-mayor) form:** a **7-member council = 5 geographic districts (1–5) +
2 At-Large seats**, plus a separately-elected **executive Mayor** who runs the administration
and **casts no council vote**. The council **elects its own Chair** (currently **Sharla Bynum,
D3**) to preside. **Max council/RDA roll-call tally = 7**; **Mayor Cherie Wood** appears in
**0** vote rows (she presents items to the council but never votes) and is absent from the db
`person` table — verified against a real 2026-06-10 roll call.

**Roster evolves 2020 → 2026** (observed per document, nothing hard-coded). The 2020 council
(Bynum, deWolfe, Thomas, Huff, Mila, Pinkney, Siwik) is a different seven from the 2026 council
(Glad, Thomas, Bynum, Mitchell, Jones, Williams, deWolfe). ⚠ **D1 and D5 are mid-term
appointees in 2026** — the *elected* 2023 winners were **Huff (D1)** and **Sanchez (D5)**; the
*serving* 2026 members are **Glad (D1)** and **Jones (D5)** (see `election_results/CLAUDE.md`
and `geo/CLAUDE.md`). Join by person carefully across years.

### RDA — a separate PMN body, same board
The Council convenes as the **South Salt Lake RDA** (PMN body 1296, same Wednesday, 6:15 p.m.);
the board is the seven councilmembers, the Mayor is the non-voting Executive Director. RDA open
votes live in `meeting_minutes/` tagged `body=RDA` (125 motions since the 2026-07-16
promotion). 19 RDA dates remain agenda-only/no-action (honest source limit).

## Distinctive facts (read before quantitative claims)
- **The (residual) coverage cliff is still the dominant fact** — see the headline. A missing
  council WORK meeting, a mid-2021→mid-2022 regular, or a 2020–2021 PC meeting is an
  agenda-packet gap (recorded minutes not posted anywhere), logged in
  `minutes_unrecovered.csv`, never stubbed.
- **`result` is SYNTHESIZED.** SSL prints no result string, so `result` = the computed
  `<aye>-<nay> Pass|Fail` from the roll (abstains/absents excluded from the count). It is
  derived from the recorded votes, not invented; `validate_city.py` confirms 100% tally match.
- **Named per-member roll calls throughout** (`names_recorded` almost always true) — unlike the
  narrative-tally cities, SSL prints every voter. The two council formats are **Roll Call
  Vote** and **Voice Vote**, both listing all 7 members `Name: Yes/No/Not Present`.
- **PC vote grammar differs** — `Commissioner <Name> – Aye;` with a `Vote:` header; a few
  procedural PC motions are tally-only (`The motion passed with the unanimous consent`),
  captured with a single placeholder row and no fabricated members.
- **A faithful source typo is retained:** the PC roster carries both `Oliva Spencer` and
  `Olivia Spencer` (one meeting's clerk typo) as a near-duplicate, not merged.
- **Corpus is CLEAN** — born-digital `pdftotext` (no OCR); the statistical screener found 0
  dict/split-word/weird-char outliers on either body; exhibit tails were trimmed.

## Known gaps / caveats
- **Residual coverage cliff** (above): 178 council + 19 RDA + 24 PC agenda-only dates logged
  unrecovered (221 total; 8 genuine 2022 PC dates added 2026-07-17 after a ledger cross-check);
  PC 2020–2021 never published. All honest, verified, never stubbed.
- **db referral layer is thin on the PC side** (43 links: 40 Council←RDA, 3 Council←PC, all
  `medium` subject-matches) — 2020–2021 PC minutes don't exist. See `db/SCHEMA.md`.
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.
- **Elections:** county-administered; only SSL council + mayor races. **2011 & 2019 re-parsed**
  from the raw SOVC (the archive normalizer keyed off sheet names that omitted the city string);
  **2021** re-parsed to undo privacy-suppression. **2025 At-Large (2-Year Term) is an off-cycle
  special** (Pinkney → county council → deWolfe appointed then won it), flagged in `note`.
- **Geo is current/post-2020-census vintage** — SSL's own official layer; pre-2022 addresses
  near a moved boundary may mis-assign.
- **Cross-city:** `result`/`motion_type` are SSL-native — aggregate only via `motions_std.csv`
  + the repo-root `crosswalks/`, never the raw strings.

## Regenerate each layer
- **Council + RDA votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`MEETING_WEEKDAY = Wednesday`). `weeks/` and
  `db/` are **derived** — regenerate, never hand-edit; rebuild weeks/ after any change to the
  canonical CSVs.
- **Full re-harvest** (rare): `python3 .harvest/harvest_minutes.py {council|rda|pc}` then
  `python3 .harvest/build_index.py`.

## Keeping it current
`python3 fetch_new.py --probe` (default, read-only) lists PMN meeting dates newer than the
per-dataset index max for **council (body 1295)**, **rda (1296)** and **pc (1297)**, excluding
dates already indexed or logged unrecovered; writes `refresh_probe.json`. `--fetch [--stream
council|rda|pc]` downloads each new date's candidate PDF(s) → `raw/`, **content-detects** the
minutes doc vs an agenda packet (the whole SSL ballgame), writes markdown + provenance header
→ `minutes_index.csv` (or logs the gap in `minutes_unrecovered.csv`), then extracts +
validates. Rebuild db + motions_std + weeks + `cities.db` afterward (the CLI prints the
reminder). Idempotent + resumable.

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated. Federated into the repo-root `cities.db`
(`build_cities_db.py`) as `city='south_salt_lake'` — 966 motions, 52 election races.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
✅ **The `pmn_backfill/` recovery was promoted into the audited layer 2026-07-16** — of the 130
recovered minutes, 119 verified docs were promoted (Council 75 / RDA 29 / PC 15;
`pmn_backfill/promote_to_audited.py` carries the classification + reject reasons) and
COVERAGE.md was rewritten. The 2022 PC recovery refuted the "no 2022 PC minutes" claim.
- **`packets/`** — **429 packets INDEX-ONLY (3.37 GB)**, Council 197 / PC 116 / RDA 50 / CRB 66;
  the deferred AgendaCenter-packets layer (use `?packet=true`).
- **`housing_plans/`** — **8 rows**: 2021 General Plan 2040, 2016 + 2023 MIH plans, 4 state excerpts.
- **`ordinances/`** — **114 rows (100 Municode-enumerated, 39 land-use)** via the Municode NEXT
  API disposition table; linkage thin (SSL cites by subject; coverage cliff).
- **`pmn_backfill/`** — **130 recorded minutes recovered** from the AgendaCenter ArchivedMinutes
  slot (119 promoted 2026-07-16, see ✅); PMN itself confirmed no in-scope misses. 221 meetings
  still agenda-only.
- **`transcripts/`** — 269 YouTube meeting videos, 100% ASR captions; covers the cliff years.
- **`campaign_finance/`** — **68 filings, 2021/2023/2025 complete**; acquisition layer; flags a
  3-way 2021 mayoral primary.
