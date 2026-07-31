# Millcreek City Council — data repository

A Salt Lake City-style civic-data repository for the **Millcreek City Council**, **Planning
Commission**, and **Community Reinvestment Agency (CRA)** (Salt Lake County, Utah; ~62k pop.),
built 2026-07-06 by the `build-city-data-repo` skill. Council + CRA + PC minutes (as markdown),
extracted roll-call votes, a relational cross-body db, public-comment availability, municipal
election results, and an address→district tool — all as markdown/CSV. See `CLAUDE.md` for
analysis guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA in
`VERIFICATION.md` (PASS on every built dataset, 0 FAIL).

**Millcreek incorporated Dec 28, 2016**, so the record starts 2016-12 (council) / 2017-02
(PC) — the short history is the city's *entire* electoral/legislative life, **not a
2020-floor gap**.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + CRA minutes | 2016-12 → 2026-06 | **372 md** (314 Council + 58 CRA) | CivicPlus AgendaCenter (cat3 Council / cat7 CRA) | ✅ complete; 241 `text` + 131 `scanned` (all OCR-derived); 1 unrecovered (2018-03-20 budget-only) |
| Council + CRA votes | 2016–2026 | **2,257 motions** · **5,580 vote rows** (4,245 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; mayor votes (max tally 5); **named roll-call ~2022+, 2017–2021 tally-only by source** |
| PC minutes | 2017-02 → 2026-05 | **149 md** | CivicPlus AgendaCenter (cat2) | ✅ complete; 113 `pdf-text` + 36 `ocr`; 13 unrecovered logged |
| PC votes | 2017–2026 | **759 motions** · **2,840 vote rows** (2,476 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; named commissioner rolls; PC→Council referral language present |
| Relational db (`db/millcreek.db`) | 2016–2026 | **3,016 motions** · **6,721 votes** · **34 PC/CRA→Council referrals** | standard cross-city schema | ✅ reconciles exactly (6,721 named CSV rows == 6,721 db votes); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md only** | n/a — comments are IN-PACKETS | ⚠ **IN-PACKETS** — verbatim resident letters inside PC packet PDFs; Provo-style harvest is a documented pending follow-up (not honest-empty) |
| Election results | 2016 (founding) → 2025 | **22 races** (17 general + 5 primary) · 69 candidate rows · 1,199 precinct rows | Salt Lake County SOVC (`slco-election-archive` + raw re-parse) | ✅ verified; all 4 unusual findings MATCH outside sources |
| Geo (address→district) | current map | **4 district polygons**; **51 precincts → D1–D4** | Millcreek city ArcGIS (`Millcreek_City_Council_Dist_2022/FeatureServer/2`) | ✅ tool + geojson present; **2022-vintage boundary** |
| Weekly bundles | 2016–2026 | **275 week bundles** | derived (`build_weeks.py`, Monday grid) | ✅ regenerable; weekly vote sum 5,580 == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 2,257 / PC 759 motion rows) and the repo-root `crosswalks/`.

## Council structure — the Mayor VOTES

**Five-member council-mayor form: 4 district members (Districts 1–4) + a separately elected,
citywide Mayor who is a FULL VOTING member** (max council roll-call tally = **5**). No at-large
council seats — the Mayor is the only citywide seat. 4-year staggered terms:
**Cycle A** (Mayor + D1 + D3) — 2016(founding), 2019, 2023, 2027; **Cycle B** (D2 + D4) —
2016(founding short seat), 2017, 2021, 2025.

Current members: Mayor **Cheri Jackson**; D1 **Silvia Catten**, D2 **Thom DeSirant**,
D3 **Nicole Handy**, D4 **Bev Uipi**. **Roster drift to join carefully across years:**
founding mayor **Jeff Silvestrini** (2017–2025); D2 **Dwight Marchant → Thom DeSirant**
(Jan 2022); D3 member **Cheri Jackson → Mayor** and **Nicole Handy → D3**, both by **Nov 2025
council appointment** (see below). Geo maps addresses to Districts 1–4.

### CRA — an in-record body
The Council convenes as the **Millcreek Community Reinvestment Agency** (Utah 17C —
redevelopment/RDA-equivalent): project-area plans/budgets, participation agreements, inter-fund
loans. CRA minutes live in `meeting_minutes/` and every CRA motion is tagged `body=CRA`
(**58 files · 246 motions**); "Board Member <Name>" / "Chair <Name>" are the same
councilmembers / mayor (CRA rolls also cap at 5). There are no separate CRA portal files to acquire.

## Distinctive Millcreek facts (read before quantitative claims)

- **Short history is REAL.** No Millcreek council/PC record exists before 2016 (council) /
  2017 (PC) — the city did not exist. The 2020 floor is fully covered with **no early-year hole**.
- **Named roll-call ~2022+; 2017–2021 tally-only by source.** Early minutes say *"All Council
  Members voted yes"* (no individual names); per-member roll calls begin ~2022. Member-level
  vote analysis is only meaningful **2022→present**. Pre-2022 unanimous motions are recorded as
  tally-only (blank member), never as fabricated votes — a **source property, not a defect**.
- **Elections use RCV in 2021 & 2023** (first-choice counts stored; seat `winner` is the
  final round — 2021 D2 diverges, DeSirant beat first-choice leader Clark).
- **2025 Mayor was APPOINTED, not elected** — council selected Jackson to finish Silvestrini's
  term (Nov 2025). No 2025 mayoral race row (not a gap).
- **2023 Mayor + D1 cancelled-uncontested** — only the incumbent filed; Utah cancelled both
  races. Blank vote fields, no precinct rows, no fabricated counts.
- **Geo layer is 2022-vintage.** The published city district polygons are the **2022–2032
  redistricting** boundary; pre-2022 votes/elections used the original 2016 lines (not
  published) — an address near a moved boundary may mis-assign for pre-2022 questions.

## Public comments — IN-PACKETS (documented follow-up, not honest-empty)
Millcreek publishes **genuine verbatim resident comments**, but only inside the combined
Agenda+Packet PDFs as appendices to PC land-use staff reports (the Provo pattern) — no
standalone comments page or eComment archive. `all_comments_clean.csv` was **deliberately not
built**; a Provo-style page-walk packet harvest is **queued as a pending follow-up**. Full
audit: `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **1 unrecovered council meeting** (2018-03-20 budget work meeting): the published file is a
  budget spreadsheet with no narrative/votes — logged in `meeting_minutes/minutes_unrecovered.csv`,
  raw PDF retained, never stubbed. **13 PC meetings** unrecovered similarly in
  `planning_commission/minutes_unrecovered.csv`.
- **OCR garble throughout.** The AgendaCenter PDFs are scanned / bad-text-layer; extractors
  fuzzy-match garbled names to the roster and the screener confirmed no fabricated data (distinct
  named voters == exactly the roster).
- **Elections:** county-administered; only Millcreek council + mayor races included. 2019 general
  was re-parsed from raw SOVC (the archive normalizer lost 2019 candidate names); 2021 general
  re-parsed from raw (privacy-suppression at the method split). See `election_results/CLAUDE.md`.
- **Cross-city:** `result`/`motion_type` are Millcreek-native — aggregate only via `motions_std.csv`
  + the repo-root `crosswalks/`, never the raw strings.

## Regenerate each layer
- **Council + CRA votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`); to
  re-convert new PC PDFs, `python3 planning_commission/convert.py` (driven by `_pc_links.json`).
- **Elections:** `cd election_results && python3 clean_elections.py` (asserts 0 reconciliation
  mismatches).
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent;
  prints CSV↔db reconciliation, exact to 0). Read `db/SCHEMA.md` first.
- **Normalized layer:** `python3 ../scripts/normalize_motions.py --all` (refreshes `motions_std.csv`).
- **Weekly bundles:** `python3 build_weeks.py` (`CITY="Millcreek"`, `MEETING_WEEKDAY=0` → Monday).
  `weeks/` and `db/` are **derived** — regenerate, never hand-edit; rebuild weeks/ after any
  change to the canonical CSVs.

## Keeping it current
`python3 fetch_new.py --probe` lists AgendaCenter Minutes items newer than the index max for
each dataset (council cat3 + CRA cat7; PC cat2) plus a read-only PMN (council body 5741) cross-check;
`--fetch [--dataset …]` downloads new PDFs → `raw/` → markdown (OCR-aware) → `minutes_index.csv`,
then extracts + validates. Rebuild db + motions_std + weeks afterward (the CLI prints the
reminder). Idempotent + resumable.

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/` originals, never
modified). `weeks/` and `db/` are regenerated.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-06)
Six new source layers, each with its own `CLAUDE.md` + `AVAILABILITY.md` and each individually
passing `validate_dataset.py`. **None modify the core minutes/votes/comments/elections layer.**
Join to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **552 documents, INDEX-ONLY** (340 `full_packet` — Council 186 / CRA 54 / PC
  100, 2018–2026 — + 212 thin `agenda_packet`). Millcreek's AgendaCenter serves the combined
  **Agenda + Packet** PDF at the same `docId` as the Minutes view, so **those exact PDFs are
  already retained** in `meeting_minutes/raw/` (979 MB) + `planning_commission/raw/` (499 MB);
  each `full_packet` row points there via `path` (`stored_locally=yes`, 335/340)
  rather than re-storing ~1.2 GB. **PC `full_packet` rows bundle verbatim resident-comment
  letters — this is the IN-PACKETS comment corpus** (`public_comments/` marks it a pending
  Provo-style harvest; this index flags where the letters live, does not extract them). 5
  "Agenda and Packet" items had no combined PDF → `unrecovered.csv`. Join `(date, body[,
  meeting_type])`.
- **`housing_plans/`** — **7 docs**: the **Millcreek Together General Plan** (`View/3193`, 140 pp;
  the **MIH element is embedded** — Ch. 4 + housing appendix, no standalone PDF), the adopting
  **Ordinance 22-44** (2022-09-26, the MIH element of record — **joins the vote layer** at the
  Sept 26 2022 council meeting), the city **Aug-2024 Housing Report**, and the state HCD MIH
  compilations **2023/24/25** (Millcreek page ranges) + the **SB 34 2019–2021** summary (pp.
  81–82). Born-digital (clean, no minutes-corpus OCR garble). Caveats: GP cover reads "Amended
  December 12, 2026" (future-dated placeholder — cite in-text content, not the cover date); 2023
  & 2024 state compilations bleed adjacent **Murray** text into Millcreek's range (2025 + SB 34
  clean). Document dataset, not joined to `db/`.
- **`ordinances/`** — **550 distinct adopted ordinances, 2016-01 → 2026** (`ORD YY-NN`) from the
  **municipalcodeonline.com S3 back-catalog** (bucket `municipalcodeonline.com-new`, us-west-2,
  **path-style**) — a genuine second source per ordinance NUMBER, independent of the minutes.
  525 PDFs stored (857 MB); 25 oversize exhibit bundles index-only. **~39% land-use** (213).
  `match_confidence` **346 high** (number cited in a council motion AND the PDF's own month+year
  match) / **84 medium** (cited but no independent PDF date, or cited on >1 date) / **120 none**
  (no motion cites it — mostly 2016–18 pre-named-vote-seam procedural). **13 cited-but-no-document
  numbers** logged (`citations_without_document.csv`). **⚠ Data-quality flag: Ordinance 17-99 is
  an inauthentic test/template doc** on the code host (John Doe / Jane Doe / Betsy Ross voters, a
  "(joke)" clause, fictitious `U.C.A. 3.4.5`) — flagged in `note`, **exclude from analysis**.
  Join by ordinance number cited in `all_votes.csv` motion/title text.
- **`pmn_backfill/`** — Utah PMN cross-check. **Bodies discovered via the live entity chain**
  (municipality **id=1279** → publicBodies): **City Council 5741 · Planning Commission 5815 ·
  Community Reinvestment Agency 6367** (this run corrected the stale **1031** council id the
  base `fetch_new.py` carried). PMN is **thin** — the city double-posts to AgendaCenter, so the
  repo is a near-total superset. **1 recovered** (2017-11-21 Board of Canvassers general-election
  canvass — seated D2 Marchant / D4 Uipi; tally-only, pre-2022 seam) + **1 dead** (2018-03-20
  budget work meeting — PMN attachment 404, already in `meeting_minutes/minutes_unrecovered.csv`).
- **`transcripts/`** — **92 meeting videos mapped** (58 Council + 34 PC, 2025-01-06 → 2026-06-22),
  **10 ASR caption tracks sampled** (SAMPLE-ONLY by owner policy). **Real meeting video EXISTS** —
  via the third-party mirror **`@UtahRecord`** ("Utah Record — Public Meetings", playlist
  "Millcreek City Meetings"; same operator as the searchable `millcreek.openutah.org` front-end).
  **The city's own YouTube (`@millcreekutah3408`) is PR-only** and has no meeting video. **2025+
  only** — the pre-2025 record is minutes-PDF only. **Whisper NOT run.** ASR is contextual/color
  only, **never authoritative**; the `body` label is the mirror's title (unverified — some
  "CityCouncil" videos are URCA). Join by meeting date.
- **`campaign_finance/`** — **ACQUISITION LAYER ONLY** (raw filings + provenance `index.csv`;
  `extraction_method=none`; 31 born-digital + 10 scanned). **41 filings / 4 cycles**
  (2019/2021/2023/2025), Mayor + Council D1–D4; **2019 recovered from Wayback** (404 on live).
  **39/41 filings (20/22 candidate-cycles) join `election_results`** (normalize UPPER-CASE names
  with `(NON)`/`(NP)`). The 2 non-joins are **appointment artifacts** (`in_election_results=no`):
  **Jackson 2025 Mayor** and **Handy 2025 D3** — both appointed Nov 2025, never elected to those
  seats. Inverse: **2023 Mayor (Silvestrini) + D1 (Catten)** were cancelled-uncontested → no
  campaign → correctly no filing. **Double-count trap — do NOT sum filings** (2021 = one combined
  bundle per candidate; other cycles = interim + summary). Some 2025 filings are **city-redacted**.
  **2016/17 unpublished** (pre-online paper era, in `unrecovered.csv`).
