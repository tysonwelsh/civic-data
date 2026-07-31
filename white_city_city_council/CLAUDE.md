# White City — data repository (analysis guidance)

Canonical datasets about the **White City** governing body (Salt Lake County, Utah; ~5,000 pop.),
modeled on the collection template (taylorsville / south_jordan) and conforming to
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built by
the `build-city-data-repo` skill, 2026-07-12. Independent QA: `VERIFICATION.md`. Data floor
**2017** (incorporation edge, not a gap).

```
meeting_minutes/      Council minutes (markdown) + extracted votes (all_votes.csv, motions_std.csv)
                      + retained raw/ originals + validate_votes.py; 5 PMN-recovered minutes
                      promoted 2026-07-16 (provenance=pmn_minutes)
planning_commission/  POPULATED 2026-07-16 — 22 MSD-minuted PC meetings RECOVERED FROM PMN BODY
                      5879 (2019→2025, 106 motions, all provenance=pmn_minutes) + its own
                      extract_votes.py/CLAUDE.md; residual gaps in minutes_unrecovered.csv
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only / in-meeting)
election_results/     Salt Lake County results filtered to White City council + mayor races
geo/                  precinct boundaries + address→district tool (White City is ALL AT-LARGE)
db/                   relational SQLite (civic.db; build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles (build_weeks.py; MEETING_WEEKDAY = Thursday)
recon.md              source/provenance map (written BEFORE acquisition)
SOURCES.md/sources.csv  per-document provenance index
VERIFICATION.md       independent QA + external election cross-check (validate_city 2026-07-16:
                      23 PASS / 3 WARN / 0 FAIL — the 3rd WARN is the documented provenance column)
fetch_new.py          incremental refresh driver (Streamline year pages + PMN body 5805)
```

## The structural facts that make White City different

1. **Township → City, mid-record.** Governed as **White City Metro Township** 2017 → **CITY
   effective 2024-05-01 (Utah HB35 2024)**, mayor–council form. First directly-elected Mayor
   (Allan Perry) + council seated **Jan 2026**. This is the single most load-bearing fact.
2. **The Chair/Mayor VOTES — in BOTH eras. Max roll-call tally = 5.** Township era: the council
   selects a **Chair** who carries the courtesy title "Mayor" (Paulina Flint) and **votes as one
   of the five members**. City era (2026+): a **directly-elected executive Mayor** (Perry) who
   **also votes** on every roll call. So a `Mayor <Name> — Aye` roll entry is a real voting member,
   and a full roll call tops out at **5** (never 6). This is the **Millcreek** model — NOT the
   Taylorsville / South Jordan non-voting-mayor form. `db/civic.db` `person` includes the mayor;
   `Allan Perry` has 30 votes, most as Mayor in 2026.
3. **Three vote-grammar eras** (all handled by `meeting_minutes/extract_votes.py`):
   - **Narrative-tally (2018–2025)** — mover + seconder + a prose tally, **no per-member list**
     → tally-only rows (blank `member`/`vote`). 587 of 775 council rows. Do NOT infer unnamed Ayes.
   - **Narrative-named-dissent (2020–2022, + one 2024 case)** — a `Pass (unanimous)`/`3-1 Pass`
     string with a **single named dissenter/abstainer** (Scott Little's `Nay`/`Abstain`; Tyler
     Huish `Abstain` 2024); majority honestly unnamed. **This drives the `f.tally` validator
     WARN (53.6%) BY DESIGN** — a "unanimous" string can carry a named non-Aye row, so counted
     rows ≠ string tally. Verified faithful, not a defect.
   - **Full named roll call (2026+)** — per-member Aye/Nay incl. the Mayor. 150 named rows.
4. **OCR seam (2024).** 12 mid/late-2024 minutes were image-only scans, recovered via OCR
   (`minutes_index.csv format=ocr`). Screener + ground-truth found them faithful (preserved source
   typos like "THIS 1S THE TIME" are transcription evidence, not errors). All other minutes are
   born-digital `text`.
5. **Planning Commission: recovered from PMN body 5879 (2026-07-16).** White City's own PC
   (4th-Thursday nominal, cancels often) publishes **no minutes on the city site**, but an
   MSD-minuted series ("MEETING MINUTE SUMMARY", recorder Wendy Gurr — the Kearns-PC document
   family) lives on Utah PMN body 5879: **22 meetings / 106 motions (2019-01-29 → 2025-05-20)**,
   now the `planning_commission/` dataset (`body=PlanningCommission`, every row
   `provenance=pmn_minutes`). MSD narrative-tally ceiling: only mover/seconder (+ 1 named
   abstainer — Weston Millen 2021-05-25, the sole contested motion) are named; 39 procedural
   motions print NO outcome (empty `result` = honest NULL, not failure). Land-use cases key
   OAM/EXP/WVR + `file #`. The series is sporadic: 29 noticed PC dates have no minutes
   (`planning_commission/minutes_unrecovered.csv`); its own CLAUDE.md is authoritative.

## Index + vote schemas are the collection standard

- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per document
  on disk; unrecoverable/agenda-only meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows. `source` = `streamline`; `format` ∈ `text`/`ocr`.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** and the repo-root `crosswalks/`. **Blank `member`/`vote` = tally-only motion**
  (never guessed).
- **Vote-value ceiling:** council records only `Aye`/`Nay`/`Abstain`. No `Absent`/`Recuse`/
  `Excused` values — absences appear only as narrative prose ("…was absent for the vote"). An
  absent value is a *recording* limit, not member behavior.
- Raw originals are retained under `meeting_minutes/raw/` and are never deleted.

## The join key

Everything keys to the **council meeting weekday (Thursday** — roughly monthly, 1st Thursday
regular + mid-month specials/canvasses). `build_weeks.py` buckets records onto the Thursday grid.
Elections are point-in-time (Nov, odd years) and join by **person + year** (all at-large — no
district; normalize names — election names are UPPER-CASE).

## Which artifact for which question

- **Aggregates / time series** (votes by member/year, contested rate): the flat CSVs
  `meeting_minutes/all_votes.csv` + `planning_commission/all_votes.csv` (+ each dataset's
  `motions_std.csv` for normalized outcome/tallies/type; PC outcome coverage is 63.2% —
  39 procedural motions honestly print no outcome).
- **Project-level / member record**: `db/civic.db` — read `db/SCHEMA.md` first; views
  `v_project_timeline`, `v_member_record`, `v_contested`. (Two bodies since 2026-07-16;
  `v_referral_chain` is still empty — the conservative matcher links 0 PC→Council pairs, so
  trace PC recommendations by OAM/EXP/WVR case key + subject instead.)
- **Meeting-level context**: `weeks/<week-ending-Thursday>/summary.md` → `votes.csv`.
- **Contested votes** are the signal: `v_contested` / any `Nay`/`Abstain` row. In 2020–2022 nearly
  all dissent is **Scott Little**; join by full name.
- **Elections**: `election_results/white_city_races.csv` (25-col superset). Join winners to votes on
  **person + year** (at-large). Water-district contests are decoys — already excluded.

## Cross-city cautions

- `result`/`motion_type` are White-City-native — never aggregate the raw strings across cities;
  use `motions_std.csv` + `crosswalks/`.
- Respect the **tally-only ceiling** (587/775 council rows carry no member) and the **Aye/Nay/Abstain-only**
  vote ceiling. The 53.6% `f.tally` match is the named-dissent-in-unanimous-string pattern, not
  corruption.
- **Only 6 of 10 roster members ever cast a named vote** (the 4 pre-2026-only members appear only
  as movers/seconders) — a per-member-vote query will honestly under-count the tally-only era.

## Tooling / regeneration

`python3 meeting_minutes/extract_votes.py` + `python3 planning_commission/extract_votes.py`
(votes) · `python3 db/build_db.py && python3 db/build_referrals.py` (db; prints exact
reconciliation) · `python3 build_weeks.py` (weeks) ·
`python3 fetch_new.py --probe` (refresh probe). `weeks/` + `db/` are derived — regenerate, never
hand-edit. Corrections go through documented override files, never in-place edits to the flat CSVs.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`).

✅ **PLANNING COMMISSION PROMOTION COMPLETE (2026-07-16):** the 22 PC minutes recovered by
`pmn_backfill/` (PMN body 5879) are now the populated `planning_commission/` dataset (106
motions, provenance=pmn_minutes), and the 5 recovered council minutes are merged into
`meeting_minutes/` (13 motions, provenance=pmn_minutes). 7 PC packets remain in `packets/`.

- **`packets/`** — **99 packets STORED (574 MB, all born-digital)** from the Streamline site
  (`/files/<hash>/`; harvest the `aria-label` date key on year pages, span text on
  `/meetings-archive`). Council 92 + **PC 7** (bonus — only structured PC source docs); 2018→2026
  across the township + city eras (`era` column). Packet publishing starts late-2019.
- **`housing_plans/`** — **8 rows**: 2022 General Plan (MIH as Appendix C), the standalone 2022
  MIH Plan + adopting ord 22-09-01 (both on `msd.utah.gov` — MSD-staffed planning), + 4 state
  excerpts. **White City reports under its own name every state year** ("Metro Township" pre-2024,
  "White City" after) — above the practical floor, NOT absorbed under an MSD umbrella.
- **`ordinances/`** — **136 adopted instruments (28 ordinances + 108 resolutions, 2017–2025; 13
  land-use)** from the **MunicipalCodeOnline S3 bucket** (`municipalcodeonline.com-new/whitecity/`
  — a clean scriptable source; code not-yet-fully-codified post-HB35). Linkage **95 high** / 7
  medium / 34 none / 0 within_source (every row has an independent PDF). 102/142 sidecars are
  tesseract OCR (the copies are mostly scans). Excluded a **Copperton-authored ordinance
  mis-filed in White City's bucket** (shared-MSD hazard — screen by authoring caption). ~68
  minute-cited numbers have no posted PDF (concentrated in the not-yet-codified 2026 run).
- **`pmn_backfill/`** — PMN entity **1325** (council **5805**, **PC 5879** [newly found]). **5
  missing council minutes + 22 net-new PC minutes + 4 GP Steering Committee reports recovered**
  (see ⚠ above). Honest residual: the entire **2017 council year (18 meetings) is lost to the
  pre-~2019 PMN blob purge** (same purge that hit kearns/magna/copperton — notices prove the
  meetings, the minutes are gone). PMN body discovery must sweep ALL govTypes (the PC body sat
  next to the water-district decoy).
- **`transcripts/`** — AUDIO-FIRST, ZERO captions: no video/YouTube/mirror; **13 per-meeting
  MP3/M4A recordings (2025-07→2026-06, ~1.34 GB)** on the Streamline site (audio is a mid-2025+
  practice). All flagged Whisper-candidates — highest value the 2025 narrative-tally meetings
  where minutes record no per-member roll, so the audio is the only who-said-what record.
- **`campaign_finance/`** — **2025 city-era cycle COMPLETE per ballot roster** (18 money reports,
  all 6 candidates × 3-report series, + 10 COI); 2023 township + earlier are honest gaps (nothing
  published). 13 text / 15 scanned; acquisition only. The metro-township entities are ENTIRELY
  ABSENT from `disclosures.utah.gov/Municipal` — filings live only on the city's own Streamline
  `/elections` page (COIs on a separate `/conflict-of-interest-disclosures` page).
