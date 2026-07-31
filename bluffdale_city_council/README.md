# Bluffdale City Council — data repository

A Salt Lake City-style civic-data repository for the **Bluffdale City Council**
(with its in-session **Redevelopment Agency (RDA)** and **Local Building Authority
(LBA)** boards) and **Planning Commission** (Salt Lake County, Utah — the city
also holds an unpopulated Utah-County / Camp Williams slice), built 2026-07-12 by
the `build-city-data-repo` skill. Council + RDA + LBA + PC minutes (as markdown),
extracted roll-call votes, a relational cross-body db, public-comment
availability, municipal election results, and an address→in-city tool — all as
markdown/CSV. See `CLAUDE.md` for analysis guidance and each subfolder's own
`CLAUDE.md`/`SCHEMA.md`; independent QA in `VERIFICATION.md` and `_audits/`.

Bluffdale is a **Mayor + 5 at-large council** city (no districts). Validation:
`python3 scripts/validate_city.py bluffdale_city_council` → **23 PASS / 2 WARN /
0 FAIL**.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + RDA + LBA minutes | 2020-01-06 → 2026-06-24 | **166 md** (== 166 index) | CivicPlus/CivicEngage AgendaCenter (CID=2) | ✅ complete; 137 `text` (incl. 2 .docx) + 29 `ocr` (2023–2026 scans) |
| Council + RDA + LBA votes | 2020–2026 | **971 motions** (Council 872 · RDA 77 · LBA 22) · **2,996 vote rows** (2,538 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; **Mayor non-voting in Council (max 5) except 2 tie-breaks**; **votes as Chair in RDA/LBA (max 6)**; 458 tally-only motions honestly unnamed |
| PC minutes | 2020-01-08 → 2026-06-03 | **91 md** (== 91 index) | CivicPlus/CivicEngage AgendaCenter (CID=3) | ✅ complete; 68 `text` + 23 `ocr`; 0 unrecovered |
| PC votes | 2020–2026 | **308 motions** (126 recommendations · 182 final actions) · **1,275 vote rows** (1,255 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; board of ~6–7 commissioners; **1 known OCR-garbled tally** (2025-10-15 m4, printed 4-2 vs counted 3-1) surfaced honestly, not patched |
| Relational db (`db/civic.db`) | 2020–2026 | **1,279 motions** · **3,793 votes** · **269 PC/agency→Council referrals** (189 high / 69 med / 11 low) | standard cross-city schema | ✅ reconciles exactly (3,793 named CSV rows == 3,793 db votes); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md only** | n/a — SUBMIT-ONLY email | ⚠ **HONEST-EMPTY** — emailed comments not read/posted; no archive. `all_comments_clean.csv` header-only by design |
| Election results | 2007 → 2025 | **25 races** (17 general + 8 primary) · candidate + precinct tables | Salt Lake County SOVC | ✅ verified; **2019 gap RECOVERED**; **2021 = Utah RCV pilot**; all winners match outside sources |
| Geo (address→in-city) | current | municipal boundary (2 county slices, unioned) + 15 precincts | UGRC boundary/precinct FeatureServers | ✅ tool + geojson present; **AT-LARGE — no districts**; two-county footprint |
| Weekly bundles | 2020–2026 | **136 week bundles** | derived (`build_weeks.py`, Wednesday → Monday grid) | ✅ regenerable; weekly council vote sum 2,996 == flat council total (PC not bundled, by design) |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`motions_std.csv` (council 971 / PC 308 motion rows) and the repo-root `crosswalks/`.

## Council structure — Mayor + 5 at-large; Mayor votes only to break ties
Bluffdale uses a **six-member mayor–council form**: a **Mayor** elected citywide +
**5 Council Members, ALL at-large** (no districts). 4-year staggered, non-partisan
terms. The **Mayor presides but does NOT vote** on ordinary Council motions — a
normal Council tally caps at **5**. The Mayor casts a Council vote only on a
genuine **tie-break** (2, below). In the **in-session RDA and LBA boards** the
Mayor is the **voting Chair**, so those named rolls cap at **6**.

Mayor **Derk Timothy** (2020–2021) → **Natalie Hall** (2022→present). At-large
members across the window: **Wendy Aston, Traci Crockett, Dave Kallas, Jeff
Gaston, Mark Hales, Alan Lord, Steve Austin, Greg Wilding** (+ **Mackey Smith**
seated Jan 2026). Current council (2026): Hall (Mayor) · Aston, Smith (2026–2029)
· Austin, Lord, Wilding (2024–2027).

### The 2 recorded mayoral Council votes (tie-breaks)
- **2022-11-09 motion 4** (Ordinance 2022-18, ADU text amendment): *"Kallas-Aye;
  Crockett-Nay; Hales-Nay; Gaston-Aye; **Mayor Hall-Aye. The motion passed
  3-to-2**"* — Hall breaks a 2-2 council tie.
- **2025-05-14 motion 4**: *"… Aston-Yes, **Mayor Hall-Yes. The motion passed
  4-to-2**"* — a recorded 6th mayoral vote.

### RDA + LBA — in-record boards, not separate portals
The Council convenes as the **Redevelopment Agency** (`body=RDA`, 77 motions) and
**Local Building Authority** (`body=LBA`, 22 motions) inside the same combined
minutes doc; the same members appear, and the **Mayor votes as Chair**. There are
no separate RDA/LBA portal files to acquire.

## Distinctive Bluffdale facts (read before quantitative claims)
- **Tally-only majorities are honestly UNNAMED.** Many motions record mover +
  seconder + a narrative outcome ("passed with the unanimous consent of the
  Council"); the parser leaves ayes unnamed rather than guessing. Named per-member
  rows appear on contested motions and on named inline rolls. A blank member list
  on a unanimous motion is a source style, not an extraction miss.
- **Partial-OCR seam (2023–2026).** Bluffdale moved some later minutes to scanned
  production → 29 council + 23 PC files are `format=ocr` (born-digital text before
  that). OCR is clean; the corpus screener found **0 stubs** and no fabricated
  names.
- **PC ceiling is 6–7, not 5.** The Planning Commission seats ~6–7 commissioners;
  `validate_votes.py`'s generic `<=5` ceiling FAILs for the PC by design (that
  threshold is the *Council* rule). The one PC 6-voter roll (2020-12-02 m1) is a
  legitimate full board.
- **Comments are honest-empty (submit-only)** — see
  `public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **Public comments** are submit-only email, not read or posted — an honest zero,
  not a gap.
- **Elections:** county-administered; only Bluffdale council + mayor races. **2019
  re-parsed from the raw SOVC** (canonical file had dropped it). **2021 council is
  RCV first-choice only** — winners are the two RCV winners (**Aston + Crockett**),
  NOT a first-choice top-2 read; **Mayor Hall** won 2021. A 2023-primary
  triplication was de-duped; **Proposition #13** (2023 ballot measure) is excluded.
- **Geo is at-large / two-county** — no district geometry; the tool answers
  in-city? only. The Utah-County (Camp Williams) slice is unpopulated.
- **1 known OCR-garbled PC tally** (2025-10-15 m4) — kept verbatim, counted roll
  3-1 retained; the only printed-vs-counted mismatch in the repo.
- **Cross-city:** `result`/`motion_type` are Bluffdale-native — aggregate only via
  `motions_std.csv` + the repo-root `crosswalks/`, never the raw strings.

## Regenerate each layer
- **Council votes:** `python3 meeting_minutes/extract_votes.py` (then `validate_votes.py`).
- **PC votes:** `python3 planning_commission/extract_votes.py` (then `validate_votes.py`).
- **Elections:** `cd election_results && python3 clean_elections.py`.
- **Relational db:** `python3 db/build_db.py && python3 db/build_referrals.py`
  (idempotent; **drops+rebuilds the referral table**). Read `db/SCHEMA.md` first.
- **Weekly bundles:** `python3 build_weeks.py` (`MEETING_WEEKDAY=2` → Wednesday).
  `weeks/` and `db/` are **derived** — regenerate, never hand-edit.

## Keeping it current
`python3 fetch_new.py --probe` lists AgendaCenter Minutes items newer than the
index max for each dataset (council CID=2, incl. in-session RDA/LBA; PC CID=3);
`--fetch [--dataset …]` downloads new docs → `raw/` → markdown (OCR-aware) →
`minutes_index.csv`, then extracts + validates. Rebuild db + motions_std + weeks
afterward (the CLI prints the reminder). Idempotent + resumable. The CivicPlus
portal serves only browser-like UAs — the script uses a browser UA.

Canonical truth = the dataset CSVs + minutes markdown (+ retained `raw/`
originals, never modified). `weeks/` and `db/` are regenerated. This is a **core**
build; the `expand-city-sources` and `roster/` layers are not yet built (see the
repo-root `TODO.md`).
