# Bluffdale City Council — data repository

Canonical datasets about the Bluffdale City Council (with **in-session RDA and
LBA** boards) and Planning Commission, modeled on the Salt Lake City reference
repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with
`scripts/validate_city.py`). Built by the `build-city-data-repo` skill. Data
floor: **2020**.

```
meeting_minutes/      Council + in-session RDA + LBA minutes (markdown) + extracted
                      votes (all_votes.csv, motions_std.csv) + retained raw/ originals
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only email;
                      not read, not posted) — no all_comments_clean.csv rows by design
election_results/     Salt Lake County SOVC filtered to Bluffdale council+mayor races
geo/                  municipal boundary + address/point -> in-city? (AT-LARGE, two-county)
roster/               rolling council-roster (who-served-when; 15 tenures, built 2026-07-12;
                      roster/CLAUDE.md is authoritative — incl. the 2019 vote-for-3
                      winner-marking defect + the Crockett unexpired-special finding)
db/                   relational SQLite civic.db (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying council minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday = 2)
convert_minutes.py    build-time raw PDF/.docx -> markdown converter (+ rebuilds indexes)
fetch_new.py          incremental refresh driver (CivicPlus AgendaCenter CID=2/3)
recon.md              map of this city's data sources (provenance) — the honest-gap record
SOURCES.md            per-dataset source catalog (companion to sources.csv)
VERIFICATION.md       independent QA + external election cross-check (REQUIRED)
_audits/              dated audit reports (audit-city-data skill)
```

## The structural facts that make Bluffdale different
1. **Mayor + 5 AT-LARGE council seats — no districts.** Every Bluffdale address
   is represented by the same six officials; there is no ward/district geometry
   and no "which district?" question (see `geo/CLAUDE.md`).
2. **The Mayor does NOT vote in the pure Council body — EXCEPT tie-breaks.** An
   ordinary `Council` roll caps at **5**. The Mayor casts a Council vote only on a
   genuine **tie-break/recorded event — exactly 2 in the corpus**: **2022-11-09**
   (Mayor Hall breaks a 2-2 tie → 3-2) and **2025-05-14** (→ 4-2). Both are
   faithful, both surfaced by the validator. Mayor **Derk Timothy** (2020–2021) →
   **Natalie Hall** (2022+).
3. **RDA + LBA convene in-session — and there the Mayor VOTES as Chair.** The
   Council adjourns/reconvenes as the **Redevelopment Agency (RDA, 77 motions)**
   and **Local Building Authority (LBA, 22 motions)** inside the SAME combined
   minutes PDF; `extract_votes.py` walks the section headers and tags each motion
   `body ∈ Council / RDA / LBA`. In RDA/LBA the presiding **Mayor is a voting
   Chair**, so those named rolls cap at **6**. No separate RDA/LBA portal exists.
4. **CivicPlus AgendaCenter + a partial-OCR seam.** Minutes come from the
   CivicPlus/CivicEngage AgendaCenter (`bluffdale.gov`, CID=2 council / CID=3 PC):
   a mix of born-digital text PDFs, 2 Word `.docx`, and scanned image PDFs.
   **Only 29 of 166 council + 23 of 91 PC files needed OCR** (`format=ocr`,
   concentrated 2023–2026); the 2020–2021 record is born-digital text.
5. **Two counties.** Bluffdale straddles **Salt Lake (populated)** and **Utah
   (Camp Williams / unpopulated)** counties. Salt Lake County administers and
   reports ALL Bluffdale elections; there is no separate Utah-County race.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one
  row per document on disk (`source=civicplus`; `format` ∈ `text`/`ocr`).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes
  through `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the
  repo-root `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.
- **Never fabricate:** a blank `member` on a tally-only motion = the source
  printed no per-member roll (honest, not missing extraction).

## The join key
Everything keys to the **council meeting weekday (Wednesday)**. `build_weeks.py`
buckets every council/RDA/LBA record onto that week's **Monday** grid
(`MEETING_WEEKDAY = 2`). **PC records are NOT in the weekly bundles** (the shared
`weeks_lib.py` buckets only the council-meeting datasets — matching every peer
city); the PC joins on its own date. Elections are point-in-time (Nov, odd years)
and are NOT in the weekly bundles — they join by **person + year** (at-large;
normalize names — election names are UPPER-CASE with `(NP)` suffixes).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables —
  `meeting_minutes/all_votes.csv` (+ `motions_std.csv`, 971 rows) and
  `planning_commission/all_votes.csv` (+ `motions_std.csv`, 308 rows). Remember
  the tally-only style: a blank member list on a unanimous motion is a source
  style, not an extraction miss.
- **Relational / cross-body** (PC recommendation → council outcome; RDA/LBA
  co-actions; member records): `db/civic.db` — read `db/SCHEMA.md` first; start
  from views `v_referral_chain`, `v_project_timeline`, `v_member_record`,
  `v_contested`. The `referral` layer is reconstructed + scored and was
  **precision-audited link-by-link on 2026-07-31**: 269 links → **62** (18 high /
  41 med / 3 low), all verified against the source minutes. The untuned layer was
  only **9.5% precise in its high tier** — 171 of 189 high links were
  meeting-notice boilerplate joined on CITY HALL's own address (`2222 W 14400 S`),
  an artifact of `motion_no=1` motion-text header bleed. Tuning lives in
  `db/referral_overrides.csv` (365 evidence-cited `suppress` rows).
  **Read `db/CLAUDE.md` before quoting or re-tuning a chain.**
- **Meeting-level / contextual**: the `weeks/<Monday-week>/` bundle (start with
  `summary.md`); `weeks/index.md` lists every week.
- **By member**: join election winners (`election_results/`) ↔ votes (person +
  year; at-large).
- **By geography**: `geo/address_to_district.py` resolves an address to
  in-Bluffdale? + the citywide at-large roster (no district returned).

## public_comments — HONEST-EMPTY (submit-only)
Bluffdale accepts written comment only by advance email to
`councilmeetingcomment@bluffdale.gov` (older `.com`); every 2022–2025 agenda
states emailed comments are **submitted to Council but NOT read at the meeting**,
and the city posts **no archive**. `all_comments_clean.csv` is written
**header-only** by design. Treat as a legitimate honest zero, not a gap. See
`public_comments/AVAILABILITY.md`.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown +
retained `raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after
ANY change to the canonical CSVs. **`build_db.py` drops+rebuilds the referral
table** — read the .db for analysis, don't rebuild it unless you mean to. Each
subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default; read-only) lists AgendaCenter Minutes
items newer than the index max for each dataset (council = CID=2, incl. the
in-session RDA/LBA in the same doc; PC = CID=3). `--fetch [--dataset
meeting_minutes|planning_commission]` downloads new docs → `raw/` → markdown
(OCR-aware, `> Source:`/`> Body:`/`> Format:` header byte-compatible with
`convert_minutes.py`) → `minutes_index.csv`, then runs the dataset's
`extract_votes.py` + `validate_votes.py`. Rebuild db + motions_std + weeks
afterward (the CLI prints the reminder). Idempotent + resumable. The CivicPlus
portal serves only browser-like UAs — the script uses a browser UA.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the
  signal** (db `v_contested` = 99 motions); `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see each subfolder's
  `CLAUDE.md`); standardized categories in `motions_std.csv`.
- **Elections:** 25 races 2007–2025. **2019 was recovered** from raw SOVC (a
  canonical-file gap); **2021 was the Utah RCV pilot** (2-seat ranked-choice —
  winners **Aston + Crockett** from the canvass, NOT first-choice rank; Mayor Hall
  won). A 2023-primary triplication was de-duped; Proposition #13 (a ballot
  measure) is excluded. See `election_results/CLAUDE.md`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`,
  `SOURCES.md`, and `VERIFICATION.md` — read those before quantitative claims
  (especially the tally-only unnamed-majority style, the RDA/LBA in-session bodies,
  and the 2023–2026 partial-OCR seam).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join to `all_votes.csv`/minutes by `date` (+ `body`).
- **`packets/`** — **217 full staff-report packets INDEX-ONLY** (132 Council + 85 PC, 2020→2026;
  2.85 GB of bundled whole-meeting PDFs → not stored; live URLs + HEAD-probed sizes). On this
  CivicEngage AgendaCenter the packet rides under the `Agenda` doc-type, identified by "PACKET"
  in the title. Highest-value layer (the *why* behind each vote).
- **`housing_plans/`** — **11 docs**: 2022 General Plan + the **standalone MIH element**
  (Ord. 2022-15, amended by 2023-04) + 2024 annual report + 2025 HCD compliance letter + state
  HCD compilations (2023/24/25 + SB 34, Bluffdale present each year, page ranges bleed-verified).
- **`ordinances/`** — **150 adopted (2020+), 69 land-use.** 68 `high` (Municipal Code Online S3
  archive PDF + a motion), 75 `within_source` (motion-derived only — NOT corroborated), 3
  `medium`, 4 `none` (dates source-verified from the signed PDFs; 2 are land-use adoptions whose
  minutes motion omitted the number → **extraction leads**).
- **`pmn_backfill/`** — PMN entity **87**, council body **373**. Near-complete superset of
  PMN's minutes holdings, BUT the 2026-07-17 cross-check found **2 genuine gaps** (NOT a
  superset for these): the **2022-08-16** (combined CC/LBA/RDA) and **2026-02-11** (CC/RDA)
  Council meetings were HELD and their minutes formally approved (2022-09-14 / 2026-02-25
  consent items) yet the approved minutes are unpublished on every sanctioned channel
  (AgendaCenter serves only the Agenda; Minutes ViewFile 404; no ArchiveCenter; PMN agenda+
  packet only). Logged in `meeting_minutes/minutes_unrecovered.csv` + `GRAMA_request_draft.md`.
  Also: 1 PMN-mislabeled "minutes" (a construction-open-house quorum notice) catalogued as a
  mislabel. **The "2024–2026 fully in repo" claim is corrected — 2026-02-11 is a real hole.**
- **`transcripts/`** — meeting video is on **CivicClerk** (no YouTube), **0 captions** on any
  sanctioned path → 15 videos catalogued `unrecovered`; Whisper proposed, not run.
- **`campaign_finance/`** — **106 filings, 2017–2025, 100% election-join** (99 high / 7 medium);
  city-self-hosted. **ACQUISITION LAYER only** (no dollar extraction yet → not in `cities.db`
  until the structured layer is built; the raw index is the on-disk record).

## Rolling roster (`roster/`, as-of 2026-07-13)
Built + independently audited (`roster/AUDIT.md`, PASS). **15 tenures** (5 at-large council +
mayor). Audit proved the **2019 council contest was vote-for-3** from the raw SOVC → the
elections `N_SEATS` was corrected 2→3 (Mark Hales `is_winner` fixed). Federated in `cities.db`
(`term`/`v_council_current`). `roster/CLAUDE.md` is authoritative.
