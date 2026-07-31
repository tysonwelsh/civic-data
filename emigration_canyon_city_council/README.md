# Emigration Canyon — civic data repository

A Salt Lake City-style civic-data repository for the **Emigration Canyon City Council** and
**Planning Commission** (Salt Lake County, Utah; ~1,600 residents — a narrow canyon community
east of Salt Lake City). Council + PC meeting minutes (as markdown), extracted roll-call
votes, municipal election results, a single-polygon boundary tool, and a relational db — all
as markdown/CSV. Provenance is in `recon.md`; analysis guidance in `CLAUDE.md` and each
subfolder's own `CLAUDE.md`; independent QA in `VERIFICATION.md` (**PASS** on every built
dataset). Conforms to the collection standard `../SCHEMA_SPEC.md`
(`python3 ../scripts/validate_city.py emigration_canyon_city_council` → **21 PASS / 4 WARN /
0 FAIL**). **Data floor: 2017.**

## The one structural fact: a FORM CHANGE, one 5-member body
Emigration Canyon incorporated as an **Emigration Canyon Metro Township (2017-01-01)** and
converted to a **CITY (2024-05-01, H.B. 35)**. It is the **same 5-member, all-at-large council
throughout** — one member is peer-selected **Mayor**, who **PRESIDES AND VOTES** (the
**Millcreek pattern** — mayor is counted in the 5, **max tally = 5**), NOT an executive
non-voting mayor. The presiding mayor changed by era: **Joe Smolka** (township) → **David
Brems** (city). Do not treat the two eras as two entities; the vintage is carried per-document
(`**Era:** Metro Township | City`) and in the meeting titles.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council minutes | **2018-10-25** → 2026-06 | **86 md** (== 86 index) | Utah PMN body **5809** | ✅ 79 `pdf-text` + **7 `ocr`**; **⚠ pre-2018-10 gap** (see below); 14 unrecovered |
| Council votes | 2018–2026 | **288 motions** · 3 named-dissent rows | `extract_votes.py` (deterministic) | ✅ narrative-tally; **mayor VOTES, max 5**; unanimous majorities honestly unnamed; **3 contested** (2021-08-24, 2021-12-14, 2023-10-24) |
| PC minutes | **2018-11-15** → 2026-06 | **60 md** (== 60 index) | Utah PMN body **1562** | ✅ 59 `pdf-text` (screens pristine) + 1 `ocr` (2025-11-13, promoted from `pmn_backfill/` 2026-07-16); 73 unrecovered (mostly 2017–18 purge) |
| PC votes | 2018–2026 | **141 motions** · 3 named-dissent rows | `extract_votes.py` | ✅ structured `Motion/Motion by/Vote` grammar; recommending body (`Land-Use/Recommendation`); **3 contested**; trailing `provenance` col (`minutes` \| `pmn_minutes`) |
| Elections | 2017 / 2023 / 2025 | **4 races** + candidate & precinct tables | Salt Lake County SOVC | ✅ winners/margins cross-checked to SLCo official + city site; Improvement-District & MSD decoys excluded; **no council contest 2019/2021** (real, staggered seats) |
| Geo | current | **1 polygon**, 1 precinct (EMG001) | UGRC UtahMunicipalBoundaries (CountyID 18) | ✅ **single-polygon point-in-polygon** — all-at-large, **no districts** |
| Public comments | — | **header-only** + `AVAILABILITY.md` | n/a — submit-only | ⚠ **HONEST-EMPTY** — city publishes no written-comment archive; comment is in-person |
| Relational db (`db/civic.db`) | 2018–2026 | **427 motions** (288 + 139) · **6 votes** · 0 referrals | standard schema | ✅ reconciles exactly (see `db/SCHEMA.md`) |
| Weekly bundles | 2018–2026 | **79 bundles** | `build_weeks.py` (Tuesday grid) | ✅ weekly vote sum 288 == flat total |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` and the repo-root `crosswalks/`.

## ⚠ Known gaps & caveats (read before quantitative claims)

- **Pre-2018-10 coverage is genuinely absent (upstream PMN purge).** Notices exist back to
  **2017** (council) / **2008** (PC), but Utah PMN **purged the underlying file store for
  2017 and scattered 2018–19**: every `/pmn/files/<id>` for those meetings now returns a
  315-byte **404**, while files from **2018-10 onward download normally** (verified live
  2026-07-12 — see `VERIFICATION.md §4`). The purge boundary sits at file-id ≈ 450000
  (~July 2018), a **collection-wide PMN file-rot characteristic** independently documented for
  Kearns. This is an **honest gap** — logged in each `minutes_unrecovered.csv`
  (**council 14 · PC 73** — the PC 2025-11-13 row was satisfied 2026-07-16 by the promoted
  late-posted minutes), never stubbed or fabricated. The **MSD AgendaCenter** secondary
  mirror is the documented backfill avenue (a `TODO`). *Distinct from the Kearns "false gap":
  there the files were harvestable; here they are truly purged.*
- **7 council docs are scanned OCR** (`format=ocr`; raw PDF retained). OCR is faithful (footer
  garble is cosmetic). **2 of the 7 yielded 0 motions** — **2024-02-22** and **2025-01-28** —
  because those meetings were **discussion-only sessions with no formal motion** (a Community
  Council reorganization and an animal-services/fire presentation), **not** a fabrication and
  not a scan that destroyed a vote. A born-digital re-fetch is a `TODO` to confirm. (The other
  5 OCR docs extracted normally, e.g. 2024-07-30 = 5 motions.)
- **Narrative-tally council minutes — unanimous majorities are honestly UNNAMED.** Motions
  record mover + seconder + a printed tally ("vote was 5-0, unanimous in favor"); only named
  dissenters get a member row. A blank `member` on a unanimous motion is source style, not
  missing extraction. The entire attributed-dissent record is **6 rows** (3 council + 3 PC).
- **Elections:** county-administered, all at-large. **No council contest ran in 2019 or 2021**
  (staggered seats not up / Improvement-District only) — real, not a missing scrape. The 2015
  vote was an **incorporation referendum**, not a council seat. Names normalize UPPER-CASE
  (`ROBERTO PINON` → Robert Pinon).
- **Comments are honest-empty (submit-only)** — see `public_comments/AVAILABILITY.md`.
- **Geo has no districts** (all at-large) — the tool answers "is this address in Emigration
  Canyon," not address→district.
- **db `referral` layer is empty (0 links)** — a genuine characteristic of a tiny, terse,
  ordinance-keyed record with no cross-body case-number bridge (see `db/SCHEMA.md`).

## Layout
```
meeting_minutes/       Council minutes (markdown) + all_votes.csv + motions_std.csv +
                       raw/ PMN originals + extract_votes.py + validate_votes.py
planning_commission/   SAME schemas for the Planning Commission (body=PlanningCommission)
election_results/      Salt Lake County results filtered to Emigration Canyon council races
geo/                   single-polygon boundary + point-in-polygon tool (no districts)
public_comments/       AVAILABILITY.md — honest-empty (no all_comments_clean.csv content)
db/                    relational SQLite (build_db.py + build_referrals.py; read db/SCHEMA.md)
weeks/                 DERIVED weekly bundles (build_weeks.py, MEETING_WEEKDAY = Tuesday)
recon.md               source map (Utah PMN, no city CMS) — written BEFORE acquisition
fetch_new.py           incremental PMN refresh probe (bodies 5809 / 1562)
VERIFICATION.md        independent QA + external election cross-check
_audits/               dated audit reports
```

## Source: Utah Public Notice (PMN), not a city CMS
There is **no city document portal**. The canonical, re-fetchable source is **Utah PMN**:
**Council = body 5809**, **Planning Commission = body 1562**. Minutes are born-digital,
DocuSign-signed PDFs at `https://www.utah.gov/pmn/files/<fileId>.pdf` (non-guessable ids).
Administrative services (recorder Diana Baun, engineering, legal) are provided by the Greater
Salt Lake **Municipal Services District (MSD)**. **⚠ Do not confuse with the Emigration Canyon
Improvement District** (sewer/water; its own elected board — excluded everywhere).

## Regenerate each layer (derived layers are regenerated, never hand-edited)
- **Council votes:** `cd meeting_minutes && python3 extract_votes.py && python3 validate_votes.py`
- **PC votes:** `cd planning_commission && python3 extract_votes.py && python3 validate_votes.py`
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent)
- **Weekly bundles:** `python3 build_weeks.py` (Tuesday grid)
- **Conformance:** `python3 ../scripts/validate_city.py emigration_canyon_city_council`

## Keeping it current
`python3 fetch_new.py` (read-only) probes PMN bodies **5809** (council) / **1562** (PC) for
notices newer than the index max, lists their "Meeting Minutes" attachments not yet on disk,
and re-confirms the verified pre-2018-10 purge (so a refresh never re-flags it as recoverable).
Downloads/carving are a separate reviewed step. Canonical truth = the flat CSVs + minutes
markdown (+ retained `raw/` originals); `weeks/` and `db/` are regenerated.
