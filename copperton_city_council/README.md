# Town of Copperton — data repository

A Salt Lake City–style civic-data repository for the **Town of Copperton** Council and its
(mostly-cancelled) **Planning Commission** — Salt Lake County, Utah; **~800 residents** — built
by the `build-city-data-repo` skill (2026-07-12). Council + PC minutes (as markdown), extracted
roll-call votes, a relational cross-body db, public-comment availability, municipal election
results, and an address→body geo tool — all as markdown/CSV. See `CLAUDE.md` for analysis
guidance and each subfolder's own `CLAUDE.md`/`SCHEMA.md`; independent QA in `VERIFICATION.md`
(PASS on every built dataset, 0 FAIL); the audit trail is in `_audits/`.

## The one structural fact to know first: a metro-township → town seam

Copperton incorporated as a **metro township on 2017-01-01** and **converted to a Town
(Utah town form, H.B. 35) on 2024-05-01**. The governing body changed form mid-record but the
**roll-call ceiling did not**: the presiding officer — the council-elected **"Mayor/Chair"** in
the township era and the **separately-elected Mayor** (Sean Clayton) in the town era — **VOTES
and is counted in every tally, so the maximum roll-call tally is 5 in BOTH eras**. This differs
from Taylorsville/South Jordan (mayor does NOT vote) and matches Millcreek (mayor votes, tally
includes the mayor). Key the roster off the **meeting date**, not a single "current council."

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | 2018-07-18 → 2026-05-20 | **106 md** (== 106 index) | GoDaddy town site (2023+) + Utah PMN body 5831 (≤2022) | ✅ complete for what survives; **91 `text` + 14 `ocr` + 1 `text+ocr`**; **29 meetings honestly unrecovered (2017-02 → 2018-06 — see gap below)** |
| Council votes | 2018–2026 | **431 motions · 458 vote rows** (44 named member rows) | extracted from minutes (`extract_votes.py`) | ✅ verified; **narrative-tally** — unanimous majorities honestly UNNAMED, only ~10 contested/named-abstention motions carry per-member rows; **Mayor/Chair votes (max tally 5, both eras)** |
| PC minutes | 2019-03-12 → 2025-07-02 | **18 md** (== 18 index) | Utah PMN body 1560 (MSD-staffed) | ✅ complete; all `text`; **thin by design** — most scheduled PC meetings are CANCELLED |
| PC votes | 2019–2025 | **57 motions · 57 vote rows** (3 named) | extracted from minutes | ✅ verified; uniformly consensus, mover-only/tally-only, no seconder field, no mayor; 3 named Breinholt abstentions |
| Relational db (`db/civic.db`) | 2018–2026 | **488 motions · 44 votes · 2 referrals** (medium) | standard cross-body schema | ✅ reconciles exactly (44 named CSV rows == 44 db votes; 488 motions == 431+57); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md only** | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — no published written-comment archive; `all_comments_clean.csv` header-only by design |
| Election results | 2017 / 2021 / 2023 | **6 council races** (+ candidate/precinct tables) | Salt Lake County SOVC (`slco-election-archive`) | ✅ verified; at-large seats A–E; **2019 absent** (county archive drop) + **2025 first-Mayor race unopposed/untabulated** (documented gaps) |
| Geo (address→body) | current | **1 town polygon · 1 precinct** | UGRC `UtahMunicipalBoundaries` (COUNTYNBR 18) | ✅ tool + geojson present; **at-large, no districts** — the whole town is one body |
| Weekly bundles | 2018–2026 | **105 week bundles** | derived (`build_weeks.py`, Wednesday grid) | ✅ regenerable; weekly vote sum == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 431 / PC 57 motion rows) and the repo-root `crosswalks/`.

## The honest gap: council 2017-02 → 2018-06 (29 meetings, verified genuine 404-purge)

The town's first ~18 months of council meetings (**2017-02-15 → 2018-06-20, 29 meetings**) are
**unrecoverable** and logged in `meeting_minutes/minutes_unrecovered.csv`, never stubbed:

- **Utah PMN retention purge.** PMN body 5831 still lists every one of these meetings as a
  notice (proving the meetings happened), and each meeting's *agenda* notice references a minutes
  PDF file-ID — but **every one of those attachment file-IDs returns HTTP 404** (a 315-byte error
  page). PMN removed all attachments older than ~mid-2018; even the meeting audio (`.mp3`/`.wav`)
  is gone. This was **independently re-verified on 2026-07-12** (VERIFICATION.md §Gap): 40+ of the
  purged file-IDs all 404, while three control files the repo *did* recover (459667, 459671,
  522659) return HTTP 200 real PDFs — so the download method works and the purge is genuine, **not
  a missed harvest**.
- **Not on the town site either.** The GoDaddy town site's Agendas-&-Minutes year folders only go
  back to **2023**.

The earliest surviving minutes document is **2018-07-18** (PMN file 459667). Everything from that
date forward is present. Later minor gaps (Sep-2025 & Dec-2025 minutes not posted; June-2026 not
yet posted) are also logged, never fabricated.

## Layout

```
meeting_minutes/      Council minutes (markdown + provenance header) + all_votes.csv +
                      motions_std.csv + per-meeting votes/*.json + roster.csv + retained raw/
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — HONEST-EMPTY (submit-only); no all_comments_clean.csv data
election_results/     Salt Lake County SOVC filtered to Copperton council races (2017/2021/2023)
geo/                  town boundary polygon + address→body tool (at-large; no districts)
db/                   relational SQLite (civic.db; build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together (Wednesday grid)
build_weeks.py        regenerates weeks/     ·     fetch_new.py  incremental refresh driver
recon.md / SOURCES.md / sources.csv   provenance map + machine-readable source index
VERIFICATION.md       independent QA + external cross-checks (Clayton, the 404 gap)
_audits/              graded audit reports
```

## Distinctive facts (read before any quantitative claim)

- **Narrative-tally minutes — unanimous majorities are honestly UNNAMED.** A council motion names
  the **mover + seconder** and records a collective outcome ("The motion passed unanimously") or a
  numeric tally ("**vote was 5-0, unanimous in favor**"). Per-member rows exist for only **~10
  council motions** (contested 3-2 splits on the 2020 UFA agreement; the 2023 0-4 tax-rate
  rejection; named abstentions) — everything else is tally-only (`member`/`vote` blank). A blank
  member list is the **source format**, not missing extraction. PC is uniformly consensus and
  mover-only (no seconder ever printed).
- **Mayor/Chair votes in both eras.** e.g. 2020-03-18 (township era) "**Mayor Clayton voted 'Nay'**"
  in a 5-member roll; 2025-07-16 (town era) a 5-0 tally with Mayor Clayton presiding and counted.
  Do NOT treat a 5-tally as incomplete.
- **OCR seam.** 14 town-era (2024-H2 → 2025) council minutes are RICOH scans (`format=ocr`); text
  is clean (proper names intact) and screens with 0 anomalies. Recon expected all born-digital;
  the OCR reality is documented in `meeting_minutes/CLAUDE.md`.
- **Tiny, sparse city.** ~11–12 council meetings/year; the PC barely meets. Thin is honest — no
  meetings were fabricated to fill cadence.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-14)
Six additive source layers (own CLAUDE.md/AVAILABILITY.md; all validate PASS; core untouched).
- **`packets/`** — 305 STORED (400 MB), Council 229 / PC 76; packet floor 2019 (purge later than minutes).
  doc_class (2026-07-16): 6 MSD land-use staff reports classified (whole-class verified).
- **`housing_plans/`** — near-empty (correct): 2020 GP w/ embedded housing element; below state threshold.
- **`ordinances/`** — 129 instruments (67 ord + 62 res, 24 land-use) from MunicipalCodeOnline S3.
- **`pmn_backfill/`** — 0 recoveries (complete superset); 1 OCR-upgrade lead; 2017-18 purge genuine.
- **`transcripts/`** — audio-only: 160 PMN MP3s (120 live / 40 purged), 0 captions.
- **`campaign_finance/`** — 25 rows (19 township 2016–2021 + 6 COI); confirms the missing 2019 cycle.
