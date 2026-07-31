# St. George City Council — data repository

A Salt Lake City-style civic-data repository for the **St. George, Utah City Council**
(Washington County — NOT St. George, Louisiana), built 2026-06-24 by the
`build-city-data-repo` skill. Council minutes, extracted roll-call votes, genuine public
comments, municipal election results, and an in-city-limits geo tool — all as markdown/CSV,
covering **2020–present**. See `CLAUDE.md` for analysis guidance and each subfolder's
`CLAUDE.md` for build details. Independent QA in `VERIFICATION.md` (**PASS**; 7 races
externally cross-checked, no fabrication).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 305 meetings (markdown) | Revize (2022–26) + Utah PMN live API (2020–21) | ✅ every month covered, no OCR; 1 unrecoverable (2025-10-09 work meeting — city published the wrong PDF; see `meeting_minutes/minutes_unrecovered.csv`) |
| Roll-call votes | 2020–2026 | 1,760 motions · 8,312 rows · 85 contested | extracted from minutes | ✅ verified (2 documented source quirks) |
| Planning Commission votes | 2020–2026 | **132 meetings · 1,006 motions · 6,250 rows · 16 commissioners** | PC minutes (Revize 2024+ / Utah PMN 2020–23) | ✅ recommendation-vs-final-action taxonomy |
| Relational database | 2020–2026 | **db/civic.db** — all bodies joined by real keys + 117 PC→Council referrals | derived from the vote CSVs | ✅ INTEGRITY OK, idempotent |
| Public comments (genuine written) | 2023–2026 | **136** residents' submissions | city `public_comments.php` (JotForm/email PDFs) | ✅ all 53 published files captured; no pre-2023 archive exists |
| Minutes speaker log (NOT public comments) | 2022–2026 | 132 in-person speakers | "Link to comments by resident: <timestamp>" pointers in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` — record notes only |
| Election results | 2019, 2021, 2023, 2025 | 11 races · 6,720 precinct rows | Washington County Clerk | ✅ verified (winners cross-checked) |
| Geo (in-city-limits) | current | city-limits polygon + 79 precincts | UGRC municipal boundary (CountyID 27) | ✅ at-large — no districts |
| Weekly bundles | 2020–2026 | 248 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Mayor + 5 council members, ALL AT-LARGE (0 districts)**, 4-year staggered terms,
council-manager form. Elections are "vote-for-N" multi-winner fields (top N win the N open
seats). Because there are no districts, the geo tool resolves an address to **in / out of
city limits** rather than a district.

## Planning Commission + relational database (cross-body analysis)
- **`planning_commission/`** — roll-call votes of the appointed land-use body (the technical
  recommender to Council). **132 meetings · 1,006 motions · 6,250 member-vote rows · 16
  commissioners**; same 13-column schema as the Council file, every row `body=PlanningCommission`.
  The `result` string encodes the **recommendation-vs-final-action taxonomy**: items
  *recommended/forwarded* to Council (674) vs CUP/site-plan/hillside items the PC takes **final
  action** on (never reach Council). Roster is reconstructed from attendee headers (appointed, no
  elections) and cross-checked against Council appointment votes. See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the **canonical queryable form** — prefer it for any cross-body or
  project-level question (the flat CSVs have no keys). **Read `db/SCHEMA.md` first.** Two layers,
  never conflated: an **EXACT within-body core** (project keys resolved from prose, body-scoped —
  *0 applications span >1 body*) and a **RECONSTRUCTED + scored cross-body `referral` layer**
  (**117 PC→Council links: 15 high / 92 medium / 10 low**; `high`≈exact, `medium` spot-check, `low`
  flagged). 5 bodies · 63 persons · 1,545 applications · 2,765 motions · 14,559 votes. Build (idempotent):
  ```
  python3 db/build_db.py          # within-body exact core
  python3 db/build_referrals.py   # cross-body referral layer (run AFTER)
  ```

## Public comments — what's here
- `all_comments_clean.csv` = **136 genuine public-submitted written comments** — residents'
  own JotForm/email submissions published on the city's public-comments page (2023–2026).
  All 53 published comment files were captured; each was spot-checked to a real resident.
- **No pre-2023 written-comment archive exists** — the city only began publishing written
  comment in 2023 (`AVAILABILITY.md`). Before that, only in-person comment exists.
- `minutes_speaker_log.csv` (132 rows) = the minutes' "Link to comments by resident"
  pointers (speaker name + topic + video timestamp, 2022–26) — **meeting-record notes, NOT
  public-submitted comments**, kept separate. 2020–21 in-person comment is recorded
  narratively within the minutes themselves and is not separately parsed.
- Spoken-comment **video transcription** is a possible future source (deliberately deferred).

## Agenda packets / staff reports — `packets/` (LINK INDEX)
Additive dataset (built by `expand-city-sources`, Source 1; as-of 2026-07-02). The staff analysis
behind council + Planning Commission agenda items, keyed by **(date, body, meeting_type)** to join
`meeting_minutes/`/`planning_commission/` votes. St. George's Revize CMS serves each meeting as
**one bundled 10–150 MB PDF** (agenda + all staff reports + exhibits), heavy with **maps/plats/site
plans** — not text-convertible (vision/OCR only) and 7.5 GB for the full set. By owner decision the
PDFs are **NOT stored locally**; instead `index.csv` is a **link index of all 224 packets** (Council
2022–2025, PC 2024–2025), each row carrying a live `source_url` + `size_mb` + `packet_kind`
(`full_packet` vs thin `agenda_packet`) so any specific packet can be fetched on demand — every URL
verified HTTP 200 on 2026-07-02. See `packets/CLAUDE.md` for how an LLM should fetch/read one.

## Moderate-income housing + General Plan — `housing_plans/`
Additive dataset (built by `expand-city-sources`, Source 2; as-of 2026-07-02). The policy
layer behind land-use votes: Utah Code 10-9a-403/408 (SB 34 / HB 462) require an MIH element
in the general plan plus annual state implementation reports. **7 index rows, all
born-digital, ~90 MB raw:**
- **General Plan** — St. George's current General Plan is an interactive **web** plan (no PDF);
  index + 7 chapter pages captured as HTML in `raw/general_plan_web/`. Plus the **2040 Downtown
  Area Plan** PDF (37 pp).
- **MIH element** — the **2022 Moderate Income Housing Plan** (29-pp PDF): affordability
  analysis, zoning environment, estimated MIH need, and the required STRATEGIES section.
- **Annual reports** — Utah HCD publishes **statewide compilation PDFs**, not per-city files;
  St. George's block was bracketed out of each (FY2023 pp.820–833, FY2024 pp.782–794, FY2025
  pp.953–971) plus the **SB 34** progress summary (pp.151–152), into `text/stgeorge-*.txt`.
  Nuance: "St. George" sorts before "Summit County" — sidecars were de-contaminated of Summit
  bleed. See `housing_plans/CLAUDE.md` + `AVAILABILITY.md`.
- **doc text (2026-07-16):** 8 text sidecars extracted from the stored GP HTML web-plan (was
  html-only, unsearchable). See `housing_plans/CLAUDE.md`.

## Zoning / land-use ordinances — `ordinances/`
Additive dataset (Source 3; as-of 2026-07-02). An adopted-ordinance index linked to the council
motions that passed them. The codified-code host (`stgeorge.municipal.codes`, Sterling) is
**403 bot-protected**, so the index is built from **Recorder-certified "Notice of Ordinance
Adoption" PDFs** (posted 2024-10+, a source independent of the minutes) plus ordinance numbers
cited in council motions. **252 rows · 35 raw PDFs** (incl. the full Title 10 zoning text,
recovered from PMN); ~99% land-use. Linkage confidence: **118 `high`** (number confirmed by BOTH
a Recorder notice AND a motion — genuine cross-match), **91 `within_source`** (motion-only,
high-by-construction, not corroborated), **39 `medium`** (notice+date, consent-calendar), **4
`none`**. 2020–2022 actions predate the city's ordinance-numbering scheme. See
`ordinances/CLAUDE.md`.

## Utah Public Notice (PMN) backfill — `pmn_backfill/`
Additive dataset (Source 4; as-of 2026-07-02). A per-**date** coverage cross-check of council +
PC minutes against the state PMN repository (bodies **241 = Council, 242 = Planning Commission**;
St. George entity 277). The repo is largely a superset, but **20 documents / 17 meeting dates
were recovered** — mostly 2022–2025 work/joint council meetings the city site never surfaced,
plus a few 2020–21 & 2023 PC minutes. Kept **separate** from the audited `minutes/` layer for
deliberate review, never merged in place. One genuine gap remains (PC 2023-05-23 minutes never
posted to PMN). Per-year table in `pmn_backfill/coverage.md`.

## Meeting video transcripts — `transcripts/`
Additive dataset (Source 5; as-of 2026-07-02). **Automatic (ASR) YouTube caption tracks** of
council meetings — the deliberation the clerk's minutes summarize away. **10 transcripts
retrieved (~106k words); 37 meetings logged as uncaptioned** (`unrecovered.csv`). Council video
spans **two channels** (a "Community Education" gov-access channel handing off to the city's own
channel); ASR captions are a per-video lottery with a **near-total 2023–2024 gap**; Planning
Commission is not on video. Every `text/<date>.md` is headed with an ASR word-error caveat —
**not an official record**. Whisper transcription of the 2024 gap is *proposed, not run*. See
`transcripts/AVAILABILITY.md`.

## Campaign-finance disclosures (`campaign_finance/`) — additive, as-of 2026-07-02
Built by `expand-city-sources` (Source 6). Municipal **campaign-finance reports** for
St. George candidates (Mayor + Council, all at-large), completing the
**elections → members → votes** chain. **104 index rows across 14 scanned packet PDFs**,
cycles **2021, 2023, 2025**; `validate_dataset.py` PASS.
- Filed with the **City Recorder** (Utah Code 10-3-208 — municipal, not county/state).
  The city posts **combined per-deadline PDF packets** (all candidates scanned into one
  file); we split each into one `index.csv` row per candidate.
- **Sources:** 2023 + 2025 packets are **live** on `sgcityutah.gov` (elections page +
  the dedicated `city_manager_s_office/campaign_financials...` page); the **2021** packets
  were **recovered from the Internet Archive** (retired `sgcity.org` domain).
- **Format:** all scanned state forms → **OCR (tesseract)** sidecars in `text/`
  (error-prone; **no amounts transcribed** — raw PDF is the record).
- **Join:** `candidate` is the verbatim UPPER-CASE `election_results` spelling —
  **all 40 distinct (year, candidate) pairs join exactly.** Every 2021/2023/2025 roster
  candidate has ≥1 filing.
- **2019 = gap:** no 2019 filings survive on the live site or in Wayback (exhaustively
  searched); the city migrated CMS and the Archive never crawled them. See
  `campaign_finance/AVAILABILITY.md` + `CLAUDE.md`.

## Known gaps / caveats
- 2020–21 minutes render vote headers inline (normalized for parsing) and use bare-surname
  member names (verified real). Elections cover the city's council+mayor races only
  (other Washington County municipalities excluded); certified county totals are used (they
  differ slightly from election-night news figures — the normal canvass gap).

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Weekly bundles: `python3 build_weeks.py`.
  Canonical truth = `*/raw/` + dataset CSVs; `weeks/` is derived and safe to regenerate.
