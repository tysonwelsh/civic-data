# Cottonwood Heights City Council — data repository

Canonical datasets about the Cottonwood Heights City Council (with its in-session **Community
Development & Renewal Agency, CDRA**) and Planning Commission, modeled on the Salt Lake City
reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built by
the `build-city-data-repo` skill. Data floor: **2020** (Cottonwood Heights incorporated
**2005** — full modern history exists; 2020 is a normal floor, not an incorporation edge like
Millcreek).

```
meeting_minutes/      Council + CDRA minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only: eComment /
                      emailed / in-person; no published written-comment archive) — the
                      all_comments_clean.csv is intentionally header-only
election_results/     Salt Lake County SOVC filtered to Cottonwood Heights council+mayor races
geo/                  OFFICIAL 4-district boundaries (city GIS) + address/point -> district tool
db/                   relational SQLite (db/civic.db; build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together (LINK, not copy)
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday = 1)
fetch_minutes.py      original FULL acquisition driver (portal ∪ PMN) — DESTRUCTIVE: it
                      REGENERATES minutes_index.csv from a live harvest. GUARDED since
                      2026-07-19 (refuses without --force-full-rebuild; backs up first).
fetch_new.py          incremental refresh: read-only --probe (default) + APPEND-ONLY
                      --ingest (the routine refresh step; portal + PMN 2147/2148)
recon.md              provenance map — written BEFORE acquisition (portal vendor, URL patterns,
                      the honest-gap record, the browser-header requirement)
SOURCES.md/sources.csv  per-document source index (URL, local path, extraction method)
VERIFICATION.md       independent QA + external election cross-check (REQUIRED)
_audits/              graded audit reports (audit-city-data skill)
```

## The structural facts that make Cottonwood Heights different
1. **The MAYOR VOTES (max council roll = 5).** Cottonwood Heights is a **four-district council +
   a separately-elected Mayor who is a full voting member** of the council. A complete roll call
   tops out at **5** (4 district members + the Mayor), **never 6**. This is the *opposite* of
   Taylorsville / South Jordan (mayor non-voting, 5 districts) — **do NOT copy their
   denominator**. Confirmed against real contested roll calls (`VERIFICATION.md` §A2). The three
   mayors in the record each appear as voting members: **Michael Peterson** (2020–2021), **Mike
   Weichers** (2022–2025), **Gay Lynn Bennion** (2026–) — 533 mayor vote rows. There are **no
   >5-voter council motions** anywhere in the data (swept — the ceiling holds).
2. **In-session CDRA.** The Council recesses in-meeting as the **Community Development & Renewal
   Agency** board; its open votes are tagged **`body=CDRA`** in the council CSV (**70 motions /
   128 rows** across 41 meetings) and are a distinct `body` in `db/civic.db`. "Board Member
   <Name>" = the councilmembers/mayor. No separate CDRA portal files exist to acquire.
3. **Mid-term appointment seam (not a gap).** **Matt Holton first votes 2023-05-16** while
   **Douglas Petersen's last vote is 2023-04-04** — Holton filled the **District 1 vacancy**
   (sworn in late May 2023) and then won the November 2023 D1 general. The April→May handoff is a
   real roster change, not missing data.
4. **Portal ∪ PMN union with a decayed-window backfill.** Minutes come from a **Granicus /
   CivicEngage Central** portal whose rolling window **decayed** (the 2022 portal column is down
   to 4 docs), so **2020–2024 was backfilled from Utah Public Notice** (council body **2147** /
   PC body **2148**). On a `(date, meeting-type)` collision the born-digital portal doc wins
   (`source=civicplus`); else PMN (`source=pmn`) — incl. the 16 pmn_backfill docs promoted
   2026-07-16. **2026-07-17 (wave 2): 20 delisted-but-live portal docs recovered via
   Wayback-archived LISTING anchors** (the CMS still serves them by ID — `source=civicplus`;
   closed the 2024-02→10 PC hole + 2022 stragglers) **+ 1 Wayback-bytes council doc**
   (2020-10-06, `source=wayback`/`provenance=wayback_minutes`). Dec-2022 council (12-06,
   12-13) and 8 PC/AH dates are published NOWHERE (CMS-purged, never archived) — honest
   gaps in each `minutes_unrecovered.csv`, GRAMA-only. A few minutes are **.docx**
   (1 council + 1 PC). **The corpus is born-digital — no OCR seam.**

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows. `source` ∈ `civicplus` (portal) / `pmn`; `format` ∈ `pdf-text`/`docx-text`.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `body` ∈ `Council`/`CDRA` (council file) or `PlanningCommission` (PC file). **The PC file
  carries the documented trailing 14th `provenance` column** since 2026-07-16 (`minutes` =
  audited primary; `pmn_minutes` = the 6 motions of the promoted 2022-07-06 PC doc — see
  `planning_commission/CLAUDE.md`); **the council file gained the same trailing 14th
  `provenance` column 2026-07-17** (the 2022-01-25 Council Retreat, first council doc
  PMN-promoted; its 1 adjourn row = `pmn_minutes`; **`wayback_minutes`** = the 2020-10-06
  council doc whose bytes come from the Internet Archive capture of the city's own
  showpublisheddocument URL — 2026-07-17 wave-2 recovery). `result` and
  `motion_type` are city-verbatim — **cross-city comparison goes through
  `meeting_minutes/motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the
  repo-root `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Council meets **Tuesday** (1st & 3rd); the **PC meets Wednesday**. `build_weeks.py` buckets
every council record onto the weekly grid (`meeting_weekday=1`, Tuesday). Elections are
point-in-time (Nov, odd years) and are NOT in the weekly bundles — they join by **person + year
+ district** (normalize names first; election names are UPPER-CASE, some non-partisan suffixes).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (Council + CDRA, `+ motions_std.csv`) and `planning_commission/all_votes.csv`. Cottonwood
  Heights is a **named-roll** city — most motions print "Vote on Motion: Member-Aye; …", so
  named coverage is high (2,633 of 3,209 council rows named). The blank-member rows are
  **unanimous-consent procedural** motions (adjourn / open-closed session) — a source style, not
  an extraction miss; do not read them as lost names.
- **Relational / cross-body** (PC recommendation → council outcome; CDRA co-actions; member
  records): `db/civic.db` — read `db/SCHEMA.md` first; start from views `v_referral_chain`,
  `v_project_timeline`, `v_member_record`, `v_contested`. The `referral` layer is currently
  **empty (0 links)** — Cottonwood Heights' terse ordinance/resolution-keyed council minutes cite
  no PC case numbers, so no cross-body link cleared threshold (an honest empty, documented in
  `db/SCHEMA.md`).
- **Meeting-level / contextual**: the `weeks/<Tuesday-week>/` bundle (start with `summary.md`;
  it LINKS the canonical minutes, does not copy them).
- **By member**: join election winners (`election_results/`) ↔ votes. Mind the roster drift —
  **Petersen → Holton (D1, mid-2023)**, and the mayor turnover **Peterson → Weichers → Bennion**.
- **By geography**: `geo/address_to_district.py` resolves an address/point to District 1–4 (the
  Mayor is citywide, always returned alongside).

## Faithful source clerk errors — retained verbatim, never "corrected"
Three council tally strings disagree with their own named rolls; per the cardinal rules the
verbatim `result` is preserved and the extractor records only the real members:
- **2023-11-21** — Ordinance 405 names 4 members (Holton, Newell, Birrell, Bracken) but the
  clerk printed "**passed 4-to-1**" (a 5-vote tally over 4 listed voters).
- **2026-05-19 ×2** — Ordinance 464: the clerk **duplicated "Hyland" as a phantom "Highland"**,
  printing "**failed 4-to-2**". The extractor kept the 5 real members (Birrell, Newell, Hyland,
  Holton, Mayor Bennion) and **dropped the phantom** (roll stays ≤5); the "4-to-2" string is
  retained. See `VERIFICATION.md` §A3.

## public_comments — HONEST-EMPTY (submit-only)
Cottonwood Heights accepts comment via an **eComment** web form, **email to the City Recorder**,
and **in person**, but publishes **no archive** of the submitted written/eComment comments. The
only public record is the clerk's paraphrase of in-person/hearing speakers in the minutes
(meeting-record notes, **not** written comments). `all_comments_clean.csv` is intentionally
**header-only**; the SUBMIT-ONLY verdict is in `public_comments/AVAILABILITY.md`. A legitimate
honest zero (compare the 6 honest-zero comment cities in `SCHEMA_SPEC.md`).

## Elections — recoveries + a de-suppression
**28 races, 2009–2025.** The **2011** and **2019** district generals were **recovered** from the
raw SOVC (sheets keyed `Cottonwood Hts Council N` / `COT Council N`, missed by a `COTTONWOOD
HEIGHTS` filter); the **2021** general was **re-parsed** past the SOVC privacy-suppressed
method-split rows. Parks & Rec and Improvement-District board races are **excluded**. Winners are
cross-checked against outside sources in `VERIFICATION.md` §A5 (incl. the 2025 **Weichers →
Bennion** mayoral turnover).

## Geo — OFFICIAL 4-district layer
Cottonwood Heights' four council-district boundaries come from the **official city GIS**
(`gis.chcity.org`) — not precinct-derived. `geo/address_to_district.py` resolves an address/point
to District 1–4 plus the citywide Mayor (`--latlon` point-in-polygon works offline; address mode
needs network). City Hall (2277 E Bengal Blvd) → District 3 (tested). See `geo/CLAUDE.md`.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`. Canonical
sources of truth are the dataset folders (flat CSVs + minutes markdown + retained `raw/`); never
edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the canonical CSVs. Each
subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current — the refresh path is APPEND-ONLY
`python3 fetch_new.py` (default `--probe`, read-only) lists meeting dates newer than each
`minutes_index.csv` max, probing BOTH the CivicEngage portal AND **PMN bodies 2147 (council) /
2148 (PC)** with the browser header set the site requires (it 403s bare bots behind an
Akamai-style edge).

**Routine refresh = `python3 fetch_new.py --ingest` (APPEND-ONLY).** It diffs the live
portal+PMN harvest against the EXISTING index **by target on-disk path**, fetches ONLY
genuinely-new docs, converts + gates them, and **APPENDS** rows (via
`../scripts/refresh_lib.py::append_index_rows`) — it never regenerates or drops a row. It
honors the **removal ledger** (`_removed_duplicates/`): a candidate whose target basename
was deliberately removed is NEVER re-added, and a file on disk but absent from the index
(a curated/recovered row) is LEFT UNTOUCHED. Rebuild the derived layers only when it added
docs (`extract_votes.py` both → `db/build_db.py` + `build_referrals.py` → `build_weeks.py`
→ `../scripts/normalize_motions.py` → `../scripts/build_cities_db.py`).

**`--fetch` is the OLD DESTRUCTIVE full re-acquisition — do NOT use it as a refresh step.**
It regenerates `minutes_index.csv` from a fresh live harvest, so it DROPS every on-disk row
the current listing no longer serves (the 2020-10-06 `wayback` council doc, the 33 PMN
admin-hearing PC rows, delisted-portal + PMN-window-excluded rows) and RESURRECTS
deliberately-removed duplicates. **INCIDENT 2026-07-19:** it dropped 3 council + 39 PC
recovered index rows and resurrected the removed 2024-01-02 duplicate (repaired from the
federated `document` table). It is now GUARDED: `--fetch` (or `fetch_minutes.py` directly)
REFUSES without `--force-full-rebuild`, prints a loud warning naming the incident, and
writes a timestamped index backup under `_backups/` before proceeding. Reserve it for a
deliberate, reviewed full rebuild — never routine maintenance.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Absent) are the signal**
  (`db` `v_contested`); `summary.md` surfaces them per week. Vote values observed: Aye, Nay,
  Abstain, Absent.
- Motion types: city-native taxonomy in `all_votes.csv`; standardized categories in
  `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, `VERIFICATION.md`, and
  `_audits/` — read those before quantitative claims (especially the mayor-votes max-5 ceiling,
  the in-session CDRA body, the portal∪PMN union, and the three retained clerk-error tallies).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`). Portal fetches need a FULL browser
header set (the CivicEngage edge 403s bare UAs) — `polite_fetch.py` sends them.
- **`packets/`** — **52 packets STORED (471.6 MB, born-digital)**, Council 20 / PC 32 (incl. 10
  Administrative Hearing). The Packet column is a MUCH narrower rolling window than Minutes —
  council packets only from 2025-08, PC from 2024-11; older is GRAMA-only (honest portal-retention
  limit, and PMN is NOT a packet fallback). All 52 text sidecars.
  - **packet SECTION-CUT layer** (2026-07-16): 17 sections cut from the 12 appendix-TOC council
    packets (16 staff_report + 1 general_plan), whole-class verified; PC + 2026-03+ council not
    separable (no TOC) — see packets/CLAUDE.md.
- **`housing_plans/`** — **12 rows**: 2005 General Plan, 4 MIH-element docs (2019 base, 2022
  amendment + signed Res 2023-02, the 2025 year-five Res 2025-51 — the two resolutions were
  image-only scans found ONLY via the URLs the city cited inside the state compilation PDFs),
  3 city annual reports + 4 state excerpts. CH present all state years. No compliance letter.
- **`ordinances/`** — **128 adopted (Ord 336→467 + one `2024-58`; 40 land-use)** from the
  MunicipalCodeOnline public S3 bucket (39 PDFs) ∪ PMN council body 2147 attachments (82) = 121
  raws (104 tesseract OCR — Recorder signed scans). Linkage **86 high** (all verified — 0
  mismatches) / 36 within_source / 5 none / 1 low. Handled CH's -A/-D draft/denial convention
  (adopted -D = enacted denial) and correctly EXCLUDED the failed Ord 464 (phantom-"Highland"
  clerk error) + a mislabeled "Ordinance 2024-09" that's actually a resolution. Code host
  MunicipalCodeOnline (SPA auth-gated, S3 backing bucket anonymous-listable).
- **`pmn_backfill/`** — PMN entity **111** (council 2147, PC 2148, Admin Hearings 3287,
  Architectural Review 2150, + others). Council is a COMPLETE SUPERSET (0 gaps — the core
  portal∪PMN union already had it), but sweeping every body surfaced **16 recoverable docs**:
  15 Administrative Hearings sessions 2020–2023 + 1 missed PC doc (2022-07-06 — one combined
  work + business meeting PDF). ✅ **PROMOTED 2026-07-16**: all 16 merged into
  `planning_commission/` (`slug=administrative-hearing` extended backward; vote rows tagged
  `provenance=pmn_minutes` — +6 motions / +12 rows, all from 2022-07-06; admin hearings are
  legit 0-motion officer decisions). Inventory finding: an **Architectural Review
  Commission (13 in-window minutes) the repo doesn't model** — a live design-review land-use
  body. Filenames truncate in anchor text but are full in the `aria-label`.
- **`transcripts/`** — city YouTube channel `@CottonwoodHeights` (`UCcOhqM97RmMrEpUz_6L84Cw`):
  **511 meeting videos 2018-08→2026-07** (Council 372 / PC 93 / CDRA 32 in-session / Joint 2 /
  ARC 12), 100% ASR captions, 10 samples fetched. A CivicEngage document-CMS city with
  YouTube-only video + no portal videoUrl — the video→date map came from titles + a
  release_timestamp probe. Utah Record mirror carries 0 CH.
- **`campaign_finance/`** — **86 filings, 2021/2023/2025 complete per ballot roster** (+ bonus
  2017/2019). 31 text / 55 scanned; acquisition only. FLAG: the filings prove a **2019 D1
  primary** (Petersen, Case, McHugh) that `election_results/CLAUDE.md` says didn't happen and
  McHugh is absent from `races.csv` — reconciliation lead. Also the 2023 D2 3rd primary
  candidate (Bracken). State `disclosures.utah.gov/municipal` folder again held cycles the city
  page dropped (third SLCo city with that pattern).
