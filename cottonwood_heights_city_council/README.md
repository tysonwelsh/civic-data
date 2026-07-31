# Cottonwood Heights City Council — data repository

A Salt Lake City-style civic-data repository for the **Cottonwood Heights City Council** (with
its in-session **Community Development & Renewal Agency, CDRA**) and **Planning Commission**
(Salt Lake County, Utah; ~34k pop.; incorporated **2005**), built 2026-07-12 by the
`build-city-data-repo` skill. Council + CDRA + PC minutes (as markdown), extracted roll-call
votes, a relational cross-body db, public-comment availability, municipal election results, and
an address→district tool — all as markdown/CSV. See `CLAUDE.md` for analysis guidance and each
subfolder's own `CLAUDE.md`; independent QA in `VERIFICATION.md` (PASS on every built dataset,
0 FAIL) and the audit in `_audits/audit_2026-07-12.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Council + CDRA minutes | 2020-01-06 → 2026-06-16 | **181 md** (== 181 index) | CivicEngage Central portal **∪ Utah PMN** (council body 2147) | ✅ complete; 180 `pdf-text` + 1 `docx-text`; born-digital, no OCR |
| Council + CDRA votes | 2020–2026 | **1,145 motions** (1,075 Council + 70 CDRA) · **3,209 vote rows** (2,633 named) | extracted from minutes (`meeting_minutes/extract_votes.py`) | ✅ verified; **mayor VOTES** (max roll = 5: 4 districts + mayor); named-roll + narrative-tally both parse |
| PC minutes | 2020-01-08 → 2026-02-04 | **78 md** (== 78 index; incl. 21 admin-hearing) | CivicEngage Central portal **∪ Utah PMN** (PC body 2148 + Admin Hearings 3287) | ✅ complete; 77 `pdf-text` + 1 `docx-text`; born-digital, no OCR; 16 PMN-backfill docs promoted 2026-07-16 (`provenance=pmn_minutes`) |
| PC votes | 2020–2026 | **263 motions** · **700 vote rows** (521 named) | extracted from minutes (`extract_votes.py`) | ✅ verified; named-inline rolls; admin-hearing sessions carry no roll-call votes (legit 0-motion files) |
| Relational db (`db/civic.db`) | 2020–2026 | **1,408 motions** · **3,154 votes** · bodies Council/CDRA/PlanningCommission | standard cross-city schema | ✅ reconciles exactly (3,154 named CSV rows == 3,154 db votes); see `db/SCHEMA.md` |
| Public comments | — | **AVAILABILITY.md** + header-only CSV | n/a — SUBMIT-ONLY | ⚠ **HONEST-EMPTY** — eComment/emailed/in-person only; no published written-comment archive |
| Election results | 2009 → 2025 | **28 races** · candidate + precinct tables | Salt Lake County SOVC | ✅ verified; 2011/2019 recovered, 2021 de-suppressed; winners match outside sources |
| Geo (address→district) | current 4-district | **precincts → Districts 1–4**; district polygons | official city GIS (`gis.chcity.org`) | ✅ tool + geojson present; City Hall → D3 (tested) |
| Weekly bundles | 2020–2026 | **163 week bundles** | derived (`build_weeks.py`, Tuesday grid) | ✅ regenerable; weekly vote sum 3,237 == council flat total; minutes LINKED not copied |

`result` and `motion_type` are city-verbatim; cross-city comparison goes through
`meeting_minutes/motions_std.csv` and the repo-root `crosswalks/`.

## Council structure — the Mayor VOTES (max roll = 5)
Cottonwood Heights is a **four-district council + a separately-elected Mayor who is a full
voting member** of the council. A complete roll call therefore tops out at **5** (4 district
members + the Mayor), **never 6** — the *opposite* of Taylorsville/South Jordan (mayor
non-voting, max 5 districts) and unlike Millcreek (mayor votes as a 5th *council* seat, no
separate district). Confirmed against real contested roll calls (`VERIFICATION.md` §A2). The
three mayors in the record — **Michael Peterson** (2020–2021), **Mike Weichers** (2022–2025),
**Gay Lynn Bennion** (2026–) — each appear as voting members (533 mayor vote rows total).

**Roster of 11 (observed in the vote record; join carefully across years):**

| Member | Role | Vote-record span |
|---|---|---|
| Michael Peterson | Mayor (voting) | 2020-01-07 → 2021-12-14 |
| Mike Weichers | Mayor (voting) | 2022-01-04 → 2025-11-18 |
| Gay Lynn Bennion | Mayor (voting) | 2026-01-06 → present |
| Scott Bracken | Council | 2020-01-07 → 2023-12-05 |
| Douglas Petersen | Council (D1) | 2020-01-07 → 2023-04-04 |
| Matt Holton | Council (D1) | **2023-05-16** → present |
| Christine Mikell | Council | 2020-01-07 → 2021-12-14 |
| Tali Bruce | Council | 2020-01-07 → 2021-10-19 |
| Shawn E. Newell | Council (D3) | 2022-01-04 → present |
| Ellen Birrell | Council (D4) | 2022-01-04 → present |
| Suzanne Hyland | Council (D2) | 2024-01-02 → present |

⚠ **Mid-term appointment (a genuine roster seam, not a gap):** **Matt Holton first votes
2023-05-16** while **Douglas Petersen's last vote is 2023-04-04** — Holton was appointed to fill
the **District 1 vacancy** (sworn in late May 2023, per the *Cottonwood Heights Journal*) and
then won the **November 2023** D1 general. Do not read the April→May handoff as missing data.

### CDRA — an in-record body
The Council recesses in-session as the **Community Development & Renewal Agency (CDRA)** board
(chair + "Board Member <Name>" = the same councilmembers/mayor). CDRA open votes live in
`meeting_minutes/all_votes.csv` tagged **`body=CDRA`** (70 motions / 128 rows across 41
meetings); in `db/civic.db` they are a distinct `body`. There are no separate CDRA portal files
to acquire.

## Distinctive Cottonwood Heights facts (read before quantitative claims)
- **Portal + PMN union (decayed-window backfill).** The Granicus/CivicEngage portal retains only
  a rolling ~5-year window and it has **decayed** (the 2022 column is down to 4 docs), so
  **2020–2024 was backfilled from Utah Public Notice** (council body 2147 / PC 2148). On a
  `(date, meeting-type)` collision the born-digital portal doc wins (`source=civicplus`); else
  PMN (`source=pmn`). 94 of 181 council docs (and 60 of 78 PC docs, incl. the 16 promoted
  2026-07-16 from `pmn_backfill/` — Admin Hearings body 3287 + one missed PC doc) came from
  PMN; the rest from the portal. A few minutes are served as **.docx** (1 council + 1 PC), converted via
  `word/document.xml`.
- **Born-digital corpus — no OCR.** Every minutes file is a text-layer PDF or .docx; the corpus
  screener found **0** dictionary/split-word/encoding outliers across both bodies (all years
  stable). There is no OCR seam to caveat.
- **Faithful source clerk errors are retained verbatim (never "corrected").** Three council
  tally strings disagree with their own named rolls and are kept as-is: **2023-11-21** (Ord 405
  lists 4 members but the clerk printed "passed 4-to-1") and **2026-05-19 ×2** (Ord 464: the
  clerk **duplicated "Hyland" as a phantom "Highland"**, printing "4-to-2"). The extractor
  records only the real members (roll stays ≤5; the phantom was dropped), and the verbatim
  `result` string is preserved. See `VERIFICATION.md` §A3.
- **Named-roll city.** Most Cottonwood Heights motions print a full "Vote on Motion: Member-Aye;
  …" roll, so named coverage is high (2,658 of 3,237 council rows named). Unanimous-consent
  procedural motions (adjourn/open-closed) are the blank-member rows — a source style, not a
  miss.

## public_comments — HONEST-EMPTY (submit-only)
Cottonwood Heights accepts comment via an **eComment** web form, **email to the City Recorder**,
and **in person** — but publishes **no archive** of the submitted written/eComment comments.
The only public record of a comment is the clerk's paraphrase of in-person/hearing speakers in
the minutes (meeting-record speaker notes, **not** written comments). `all_comments_clean.csv`
is intentionally **header-only**; the SUBMIT-ONLY verdict is documented in
`public_comments/AVAILABILITY.md`. A legitimate honest zero, not a gap (compare the 6 honest-zero
comment cities in `SCHEMA_SPEC.md`; substantive comment archives exist only in SLC + Park City).

## Elections — recoveries + a de-suppression
**28 races, 2009–2025** (Salt Lake County SOVC). The **2011** and **2019** district generals were
**recovered** from the raw SOVC (sheets keyed `Cottonwood Hts Council N` / `COT Council N`,
missed by a `COTTONWOOD HEIGHTS` filter); the **2021** general was **re-parsed** past the SOVC's
privacy-suppressed method-split rows (per-precinct Total sub-rows are unsuppressed). Parks & Rec
and Improvement-District board races are **excluded** (not city-council/mayor). Winners
cross-checked against outside sources (KSL, Utah News Dispatch, *Cottonwood Heights Journal*,
Utah election-results portal) in `VERIFICATION.md` §A5 — including the **Weichers → Bennion**
mayoral turnover (2025).

## Geo — OFFICIAL 4-district layer
Unlike the precinct-derived cities, Cottonwood Heights' four council-district boundaries come
from the **official city GIS** (`gis.chcity.org`). `geo/address_to_district.py` resolves an
address/point to **District 1–4** plus the citywide Mayor (`--latlon` point-in-polygon works
offline; address-geocode mode needs network). City Hall (2277 E Bengal Blvd) → **District 3**
(tested).

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` (Tuesday grid, `meeting_weekday=1`) ·
`python3 db/build_db.py && python3 db/build_referrals.py`. Canonical sources of truth are the
dataset folders (flat CSVs + minutes markdown + retained `raw/`); never edit files under
`weeks/` or the .db. As of the collection standard, weeks bundles **LINK** the canonical
minutes (relative path in `summary.md`), never copy them. Rebuild weeks/ after ANY change to the
canonical CSVs.

## Keeping it current
`python3 fetch_new.py` (default `--probe`, read-only) lists meeting dates newer than each
`minutes_index.csv` max — probing BOTH the CivicEngage portal AND **PMN bodies 2147 (council) /
2148 (PC)** — using the same browser header set the acquisition used (the site 403s bare bots).
`--fetch` delegates to `fetch_minutes.py` for the idempotent download + re-index; rebuild the
derived layers afterward (extract_votes → db → build_weeks → `scripts/build_cities_db.py`).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six additive source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all
`validate_dataset.py` PASS; none modify the core datasets. Join by `date` (+ `body`).
- **`packets/`** — **52 packets STORED (471.6 MB)**, Council 20 / PC 32; narrow rolling window
  (council 2025-08+, PC 2024-11+; older GRAMA-only). Section-cut (2026-07-16): 17 sections cut from
  the 12 appendix-TOC council packets (16 staff_report + 1 general_plan); PC + 2026-03+ council not separable.
- **`housing_plans/`** — **12 rows**: 2005 General Plan, 4 MIH-element docs, 3 city annual
  reports + 4 state excerpts (CH present all years).
- **`ordinances/`** — **128 adopted (40 land-use)** from MunicipalCodeOnline S3 ∪ PMN body 2147;
  linkage 86 high (verified) / 36 within_source. Excludes the failed Ord 464.
- **`pmn_backfill/`** — council is a complete superset; sweeping sibling bodies recovered **16
  docs** (15 Administrative Hearings 2020–2023 + 1 PC meeting); flagged an unmodeled
  Architectural Review Commission.
- **`transcripts/`** — **511 city-YouTube meeting videos 2018-08→2026-07** (incl. 32 in-session
  CDRA), 100% ASR captions, 10 samples fetched.
- **`campaign_finance/`** — **86 filings, 2021/2023/2025 complete**; acquisition layer. Flags a
  2019 D1 primary absent from the election record.
