# Town of Alta — data repository

Canonical datasets about the Town of Alta Town Council and Planning Commission, modeled on the
Salt Lake City reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built by
the `build-city-data-repo` skill. Data floor: **2020** (Alta incorporated **1970** — full modern
history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).

**⚠ Alta is SPARSE BY DESIGN** — ~380 residents, top of Little Cottonwood Canyon. The Council
meets ~monthly (2nd Wednesday, ~12/yr) and the PC meets 4th Wednesday **as-needed** (often
cancelled). Low document counts are the *correct* record for a town this small, **not** a gap.

```
meeting_minutes/      Town Council minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + votes/ JSON intermediate
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md + header-only all_comments_clean.csv — comments are
                      HONEST-EMPTY (submit-only: in-person, paraphrased in minutes; none archived)
election_results/     Salt Lake County SOVC results filtered to Town-of-Alta council+mayor races
geo/                  town boundary + precincts (AT-LARGE town — no council districts, no
                      address->district tool; the layer is town-membership only)
db/                   relational SQLite civic.db (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together (Wednesday grid)
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday = 2)
fetch_new.py          incremental refresh driver (Utah PMN bodies 1601/1602; --probe default)
recon.md              map of this city's data sources (provenance) — portal vendor, URL patterns,
                      and the honest-gap record; written BEFORE acquisition
SOURCES.md/sources.csv  per-document provenance index (regenerate: build_sources_index.py alta)
VERIFICATION.md       independent QA + external election cross-check (23 PASS / 0 FAIL)
```

## The structural facts that make Alta different
1. **The MAYOR VOTES (Utah Town form; max roll = 5).** Alta uses Utah's **Town** form: a **Mayor +
   4 at-large councilmembers**, all seats **at-large** (no districts), non-partisan, staggered
   4-year terms. The **Mayor is an ordinary voting member** — every roll call lists the Mayor by
   name alongside the four councilmembers, so a full council roll call tops out at **5** (Mayor +
   4). There is **no tie-break special-casing** — the Mayor's vote is a plain `vote` row. This
   differs from **Taylorsville / South Jordan** (mayor never votes) and **Park City / Riverton**
   (mayor votes only to break ties); it **matches Millcreek** (mayor votes routinely). Confirmed at
   source: `ROLL CALL VOTE: Mayor Bourke — yes, Councilmember Schilling — yes, …` (2025-04-09).
   `db/civic.db`: Roger Bourke = 155 votes; Elise Morgan (167) is the top voter overall
   (post-promotion 2026-07-16; +9 named Aye rows from the 2026-07-19 line-wrap
   tally-recovery). See `meeting_minutes/CLAUDE.md`.
2. **Two mayors AND two Bourkes in span (corrected 2026-07-12, T3.1(a)).** **Harris Sondak**
   was Mayor **2020–2021**; **Roger Bourke** is Mayor **2022→present** (elected Nov 2021
   uncontested; he was a **Planning Commissioner**, not a councilmember, before). The 2020–21
   **councilmember Bourke is MARGARET Bourke** — a different person. The extractor resolves
   names **per meeting file** (PRESENT block full names beat the corpus-modal roster), so
   "Council Member Bourke"/"Mayor Sondak" in 2020–21 minutes land on Margaret Bourke / Harris
   Sondak, never on Roger. Observed roster of **10** voters: R. Bourke, M. Bourke, Morgan
   (Mayor Pro Tem), Anctil, Byrne, Schilling, Davis, Heimark, Curry, Sondak. **Join by full
   name** (election names are UPPER-CASE).
3. **The BUDGET COMMITTEE is a separate body inside the same minutes PDF (2026-07-29).**
   Mayor + 2 councilmembers + the **staff Treasurer** — its meeting is minuted ahead of the
   council's in one document. **7 motions** carry `body=BudgetCommittee` (2022-04-13 →
   2023-06-07). Before the body walk these were `Council`, which recorded Treasurer **Craig
   Heimark** as a 2022 council voter; his Council service really begins **2026-01-14**.
   Filter `body='Council'` for true council votes. See `meeting_minutes/CLAUDE.md`.
   ⚠ Also documented there: the **2024-02-14 "Councilmember Davis" roll call is a clerk
   error in the approved source minutes** (Davis left the council 2024-01-10) — retained
   verbatim, never repaired.
4. **PMN is the acquisition route.** The town's `/meetings/` page (a **Juniper** WordPress CMS on a
   `*.utah.gov` subdomain) renders doc links **client-side** (a JS search app; `wp-json`/
   `admin-ajax` 404), so it cannot be scraped. All minutes here were enumerated from **Utah Public
   Notice (PMN)** — council body **1601**, PC body **1602**, doc pattern
   `utah.gov/pmn/files/<id>.pdf`. Mixed born-digital + scanned (`format` = `pdf-text` / `ocr`).
5. **PC is a sparse, tally-only Land Use Authority.** Alta's Planning Commission (4th Wednesday,
   as-needed) is the town's Land Use Authority + General Plan author; the Mayor sits **ex
   officio**. It produced **no minutes in 2020–2021** (honest gap — no business) and every recorded
   PC vote is narrative "unanimous consent" → **tally-only** (0 named member rows — a source
   ceiling). A blank PC roster is source style, not an extraction miss.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per document
  on disk; unrecoverable meetings live in `minutes_unrecovered.csv` (council header-only; **PC has
  1 row** — the 2023-11-28 meeting whose only surviving copy is a DRAFT, see below), never as
  stub/wrong-doc rows. `source = pmn`; `format ∈ pdf-text/ocr`.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ a documented trailing 14th `provenance` column since 2026-07-16** (`minutes` = audited
  docs; `pmn_minutes` = the 4 PMN-promoted label-misfiled recoveries, merged by each dataset's
  `extract_backfill_votes.py` — run it LAST after any `extract_votes.py`/`validate_votes.py`
  re-run or the pmn rows drop out; the promoted docs live in `pmn_backfill/text/`, which is what
  their `source` paths point at);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root `crosswalks/`.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Wednesday** — 2nd Wednesday, monthly; the PC
meets 4th Wednesday as-needed). Votes + minutes carry the meeting date. `build_weeks.py` buckets
every record onto the Monday grid (`MEETING_WEEKDAY = 2`). Elections are point-in-time (Nov, odd
years) and are NOT in the weekly bundles — they join by **person + year** (at-large, so no
district; normalize names — election names are UPPER-CASE).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. On a unanimous council motion with
  a `VOTE: All in favor` style the members are honestly **unnamed** (one tally-only placeholder
  row); named per-member rolls appear on roll-call and in-favor/against motions. **All** PC motions
  are tally-only. Do NOT read a blank member list as missing extraction.
- **Relational / cross-body** (member records; any PC→Council link): `db/civic.db` — read
  `db/SCHEMA.md` first; start from views `v_member_record`, `v_project_timeline`, `v_contested`.
  **The `referral` layer is empty (0 links) by design** — the PC is tiny and shares no land-use
  case key with the ordinance/resolution-keyed council; that is honest, not a bug.
- **Meeting-level / contextual**: the `weeks/<Wednesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes on **person + year** (at-large;
  mind the two-mayor turnover — Sondak 2020 → Bourke 2021, Bourke a councilmember in 2020).
- **By geography**: Alta is **at-large** — there is no address→district tool. `geo/` resolves only
  town-boundary membership (UGRC `NAME='Alta'`, CountyID 18).

## Elections — Town-of-Alta only; exclude the Alta Canyon decoys
- **3 in-scope races (≥2020):** 2021 `Town of Alta Council At-Large` + `Town of Alta Mayor`, and
  2023 `Town of Alta Council At-Large`. Filtered from the canonical Salt Lake County slice.
- **⚠ EXCLUDE the `ALTA CANYON REC …` contests** — the Alta Canyon Recreation Special Service
  District (a Sandy/Cottonwood-Heights rec district) is **NOT** the Town of Alta. `alta_races.csv`
  contains **0** canyon rows (verified).
- **2021 tallies were privacy-suppressed then RECOVERED 2026-07-19.** The county originally
  suppressed every tally (turnout below the privacy floor for a ~380-person town); the upstream
  family-C Total-recovery fix released each precinct's un-suppressed `Total` sub-row, so the
  numeric votes are now **filled from the county's own Totals** (Council: **Byrne 73 & Anctil 59**
  won, **Margaret Bourke 53** did not; Mayor **Roger Bourke 85**, uncontested). The In-Person/
  Vote-By-Mail method split stays county-suppressed. The recovered counts agree with the prior
  external cross-check (which had lower unofficial estimates). 2023 tallies are county-certified
  (Morgan & Schilling won). All
  cross-checked against outside sources in `VERIFICATION.md §5`.

## public_comments — HONEST-EMPTY (submit-only)
Alta publishes **no** written-comment archive. Comment is taken in-person at meetings (also
streamed on YouTube / SoundCloud) and paraphrased inline in the minutes by the clerk —
**meeting-record speaker notes, NOT genuine written comments**, so they do not populate
`all_comments_clean.csv` (header-only by design). Treat as a legitimate honest zero. See
`public_comments/AVAILABILITY.md` + `public_comments/CLAUDE.md`. Do NOT re-mine minutes speaker
paraphrase into the comments CSV.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`. Canonical
sources of truth are the dataset folders (flat CSVs + minutes markdown + retained `raw/`); never
edit files under `weeks/` or the .db. Rebuild `weeks/` after ANY change to the canonical CSVs.
Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default, read-only) lists Utah PMN items newer than the index max
for each dataset (council body **1601**, PC body **1602**), excluding dates already indexed.
`--fetch [--dataset meeting_minutes|planning_commission]` downloads each new date's minutes PDF →
`raw/`, converts OCR-aware → markdown → `minutes_index.csv`, then runs the dataset's
`extract_votes.py <arg>` + `validate_votes.py <arg>`. Rebuild db + motions_std + weeks afterward
(the CLI prints the reminder). Idempotent + resumable; browser UA (no bot-403 on PMN). A probe that
returns nothing for a quiet month is **correct** (sparse cadence), not a failure.

## Analysis guidance
- Alta is a **very high-consensus** council — **contested votes (any Nay/Abstain) are the signal**
  (db `v_contested` = **28** motions: 24 after the 2026-07-12 T3.1(a) narrative-grammar recovery —
  the 2021 Sondak-era council was far more divided than the pre-fix data showed: 13 true motion
  FAILURES incl. 3-2 budget-amendment splits — **+4 from the 2026-07-16 PMN promotion**, incl.
  the 2020-05-06 resort-tax-increase FAILURE 1-2 and two 3-1 splits on the 2020-06-17 UFSA
  boundary + final budget); `summary.md` surfaces them per week. 26 deferred/
  restated motions carry result `RECORDED (no vote line)` with **NULL outcome** (honestly
  unknown — the operative vote lives on the restated/amended/called-question row), never a
  default Pass.
- Motion types: city-native taxonomy in `all_votes.csv` (see each subfolder `CLAUDE.md`);
  standardized categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and `VERIFICATION.md` —
  read those before quantitative claims (especially the **Mayor-votes / max-roll-5** structure, the
  sparse ~12-meetings/yr cadence, the tally-only PC + empty 2020–21, and the at-large geo).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`). Alta's small-town sources ran
RICHER than recon predicted — the honest-empty expectation was overturned on CF + transcripts.
- **`packets/`** — **847 PDFs STORED (969 MB)** enumerated from PMN bodies 1601/1602 (the
  Juniper /meetings/ app is JS-only). Council 778 / PC 69; 2020→2026. Alta UNBUNDLED its
  packet until mid-2025 (agenda + per-item handouts; single "Meeting Packet" only from
  2023-06 council / 2024-12 PC) — so earlier years carry MORE files. 829 text sidecars.
  PMN type-labels are unreliable (agendas/packets mislabeled "Meeting Minutes") — classify
  by FILENAME. Only 3 honest packet gaps (special/no-packet meetings).
  - **doc_class layer** (2026-07-16): 11 land-use staff reports classified (whole-class verified;
    the corpus is ~90% budget/admin, so the small count is honest) — see packets/CLAUDE.md.
- **`housing_plans/`** — **2 rows, 1 PDF (near-empty by design, correct)**: the General Plan
  (2005/2013/2016) + its embedded **legacy MIH element** (§3.18, cites the pre-2019 statute,
  framed as ski-resort employee housing — NOT an HB462 standalone). Alta is ABSENT from all
  4 state HCD compilations (below the population reporting threshold — effectively exempt;
  compilations retained un-indexed as absence-evidence). No annual report / compliance letter.
- **`ordinances/`** — **50 rows (44 PDFs, 2021-O-1→2026-O-12; 10 land-use)** from the town's
  STATIC `/ordinances-resolutions/` page (GCS-hosted; PMN buries everything under generic
  "Public Information Handout" so it's not an ordinance source here). Linkage **40 high** / 6
  within_source / 4 none. Note: 2024+ minutes write the series with a DIGIT-zero (`2024-0-4`),
  not letter-O. Code host: American Legal (403 bot-gated, not mirrored). Pre-2021 unlocated.
- **`pmn_backfill/`** — PMN entity **72** (council 1601, PC 1602, Budget Cmte 8621 [= the
  "Capital Committee" category], Land Use Appeal Authority 1603). **NOT a pure superset: 5
  minutes recovered** — the original harvest filtered on the `(Meeting Minutes)` label, but
  these were posted under a `Public Information Handout` label or MISFILED under the wrong body
  (a 2024 council meeting under the PC body id). Lesson: cross-check on the meeting date in the
  FILENAME and sweep every body. Sparse 2020–21 PC gap proven real via cancellation notices.
  ✅ **PROMOTED (2026-07-16): 4 of the 5** merged into the vote layer with
  `provenance=pmn_minutes` (council 2020-05-06 + 2020-06-17 + the PC-misfiled 2024-08-14, all
  in-body-verified APPROVED; PC 2024-04-24, approved unamended per the audited 2024-05-22
  minutes) — 22 council + 2 PC motions incl. 4 contested. **NOT promoted:** PC 2023-11-28 —
  DRAFT watermark, PDF authored 4 days before its pre-printed approval date; stays a sidecar,
  logged in `planning_commission/minutes_unrecovered.csv`.
- **`transcripts/`** — YouTube `@townofalta2175` (172 meeting videos, 2020-04→2026-07, ASR
  captions on ALL — the audio-first "no captions" guess was wrong; 14 samples fetched) +
  SoundCloud `townofalta` (348 audio tracks back to 2013 — Whisper leads, none run). Utah
  Record mirror carries 0 Alta.
- **`campaign_finance/`** — **36 filings, 2021/2023/2025 — complete per ballot roster**
  (county-administered elections require filings even here). 7 text / 29 scanned; acquisition
  only. FLAG: the **2025 general is fully documented in finance but ENTIRELY absent from
  `election_results/alta_races.csv`** (Bourke re-elected Mayor; Anctil + Heimark to Council;
  Byrne + Moxley withdrew — extends the repo's prior "Heimark won 2025" note). Even here the
  2025 mayor took an itemized $2,000 **in-kind contribution from Abundance Political
  Consulting** (a private consulting firm — registry-checked 2026-07-18, no Utah PAC
  registration found; earlier "PAC contribution" paraphrase corrected). Sources:
  disclosures.utah.gov/Municipal
  + the town GCS bucket (enumerable via its S3-style XML `?prefix=130/YYYY/MM/`).
