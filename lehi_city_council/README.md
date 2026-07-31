# Lehi City Council — data repository

A Salt Lake City-style civic-data repository for the **Lehi City Council** (Utah County, Utah),
built 2026-06 by the `build-city-data-repo` skill. Council/agency minutes, extracted roll-call
votes, genuine public comments, municipal election results, and an in-city-limits geo tool — all
as markdown/CSV, covering **2020–present**. See `CLAUDE.md` for analysis guidance; independent QA
in `VERIFICATION.md` (overall **PASS**).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 175 meetings (markdown) | Granicus (`lehi.granicus.com`), born-digital text PDFs | ✅ complete (166 Council + 9 Building Authority) |
| Roll-call votes | 2020–2026 | 1,253 motions · 6,147 rows · 99 contested | extracted from minutes | ✅ verified (PASS) |
| — by body | | Council 1,245 motions / 6,107 rows · **MBA 8 / 40** | Council + Local Building Authority | ✅ `body` column |
| **Planning Commission** | 2020–2026 | **160 meetings · 1,089 motions · 6,219 rows · 140 contested** | Granicus (same portal) | ✅ `planning_commission/` (body=PlanningCommission) |
| — PC stages | | 661 recommendations (616+/45−) · 428 final actions | recommendation vs final-action taxonomy | ✅ 19 commissioners (appointed) |
| **Relational database** | 2020–2026 | 2,342 motions · 12,362 votes · **459 PC→Council referrals** | derived from the vote CSVs | ✅ `db/lehi.db` + `db/tables/*.csv` — start at `db/SCHEMA.md` |
| Public comments (genuine written) | 2020 | **42** verbatim resident comments | published inside 2020 COVID-era minutes | ✅ in-minutes-only (see below) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 148 in-person speakers | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 9 races · 58 candidates · 1,688 precinct rows | Utah County (RCV 2021 & 2023) | ✅ verified (9/9 winners externally confirmed) |
| Geo (in-city-limits) | current | city polygon + 55 precincts | UGRC (CountyID 25) | ✅ at-large — no districts |
| Weekly bundles | 2020–2026 | 165 weeks | derived (`build_weeks.py`) | ✅ regenerable |
| **Agenda packets / staff reports** | **2024–2025 (pilot)** | **112 meetings · 564 files · 341 MB** (112 agendas + 452 staff reports) | Granicus ViewPublisher agendas + linked Legistar attachments | ✅ `packets/` (Council + PC; earlier years deferred) |

## Council structure
**Mayor + 5 all-at-large councilmembers (0 districts).** The **Mayor does NOT vote** except to
break a tie — there are exactly **4 recorded Mayor tie-break votes** in the corpus (all Mayor
Johnson; Mayor Binns has none). 4-year staggered terms; council meets **2nd & 4th Tuesdays**
(work sessions 2nd Monday). Because the council is at-large, geo is an **in-city-limits**
point-in-polygon tool, not a district mapper (numbered ballot seats are NOT geographic districts).

## RDA / development
Lehi runs Redevelopment Agency business as an **in-council recess**, but — unlike Provo — those
recesses are **empty/back-to-back** (recess → immediate reconvene) with **no motions taken inside**,
and any substantive RDA record lives in a separate system not on this portal. So **`body=RDA` is 0
by design** (an honest finding, not a gap). The **Local Building Authority** (MBA) does meet
separately and is captured: `body=MBA` (8 motions).

## Planning Commission + relational database (the cross-body deliverable)
`planning_commission/` is a parallel dataset for Lehi's **second governing body** — the appointed
technical land-use filter — mirroring `meeting_minutes/` exactly (same vote schema; every row
`body=PlanningCommission`). 160 meetings, 1,089 motions, **19 commissioners** (roster reconstructed
from the minutes' attendee headers — there is no election to cross-check; cross-sourced against 11
Council *appointment* votes). PC motions are split into **recommendations forwarded to Council**
(661; 616 positive / 45 negative) vs **final actions** (428 — CUP/site-plan/design-review that never
reach Council).

`db/` is a **normalized SQLite database** (`db/lehi.db` + `db/tables/*.csv`) that joins
**Planning Commission ↔ City Council ↔ Building Authority** votes by real keys. It is built in two
layers that are **never conflated** (start at **`db/SCHEMA.md`**):
- **Within-body core** (`build_db.py`) — EXACT. Lehi's Granicus prose has no agenda/matter key and
  no file number, so each land-use motion's project key is **resolved from prose** (Park City model):
  `override > name > singleton`, body-scoped (a Council and a PC "Holbrook Farms" stay distinct).
- **Cross-body referral layer** (`build_referrals.py`, run after) — RECONSTRUCTED + scored +
  overridable, and **generalized** (a `primary_body`←`related_body` pair covering Council←PC and, for
  cities with one, Council←agency / PC←agency). Lehi shares **no key across bodies**, so the "Council
  decided what the PC first recommended" relationship is rebuilt by record linkage: full **grid
  address** + IDF **subject** on distinctive project names, gated so the PC must precede the Council.
  **459 links** (273 high / 177 medium / 9 low), all Council←PlanningCommission (Lehi's MBA carries
  none); **68% of Council land-use items linked**, the rest correctly **unlinked** (mostly items whose
  PC origin predates the 2020 floor, plus council-initiated policy).
- **The payoff:** trace a development end-to-end and see where the technical body and the political
  body diverge — e.g. PC *negative* recommendations that the Council approved anyway. Build:
  `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent).

## Public comments — in-minutes-only (honest finding)
Lehi's Granicus **SpeakUp eComment** portal (`lehi.granicusideas.com`) is **submit-only** — submitted
text is never publicly displayed or archived (verified). The only genuine *published* written
comments are the **42 verbatim resident comments preserved in the 2020 COVID-era minutes** (the
Dancing Moose daycare and Bull River Road rezoning fights), in `all_comments_clean.csv`. From 2021
on, minutes only paraphrase in-person speakers → those 148 entries live in `minutes_speaker_log.csv`
and are **not** public-submitted comments. Full audit: `public_comments/AVAILABILITY.md`.

## Elections (Utah County, at-large)
9 races for 2019/2021/2023/2025 (no mayor race in 2019/2023 — mayor is on the 2017/2021/2025 cycle).
**RCV in 2021 and 2023**, plurality in 2019/2025; for multi-seat at-large, `lehi_races.csv` lists the
top vote-getter as `winner` and the first loser as `runner_up`, with **all** winners flagged
`is_winner=True` in `lehi_results_by_candidate.csv`. The **2023 race had a mid-count withdrawal
(Corey Astill) + recount** — Astill is `is_winner=False` and Glade advanced in his place. Winners
(certified, all externally confirmed): 2019 Council = Albrecht, Southwick, Koivisto; 2021 Mayor =
Mark Johnson, Council = Condie, Hancock; 2023 Council = Stallings, Albrecht, Newall; 2025 Mayor =
Paul Binns, Council = Harrison, Freeman.

## Known gaps (honest)
- **Repair 2026-07-02 (duplicate Granicus events):** 8 same-date meeting pairs (6 council, 2 PC)
  each had ONE minutes document attached to TWO consecutive Granicus events (Pre/Regular,
  Oath/Regular, etc.) — verified md5-identical at source — so their votes were double-counted.
  One file per pair removed (originals in `_backups/2026-07-02/`); votes/db/weeks rebuilt. The
  2024-06-18 clip673/clip698 pair is two REAL distinct meetings and was kept. Full record:
  `VERIFICATION.md` (2026-07-02 addendum).
- **1 scanned-image minutes** (2024-07-30 joint work session, no text layer) and **3 server-side-broken
  Granicus docs** were not retrievable — logged, not fabricated.
- 2019 election precinct breakdown: only a suppressed countywide PDF exists → citywide totals used.
- 2021/2023 RCV rounds + the 2023 primary are citywide only (rcvis publishes no per-precinct rounds).
- 2 vote tally mismatches are confirmed **source typos** (printed summary vs. the named roll call);
  names kept verbatim, flagged not corrected.

## packets/ — agenda packets & staff reports (additive; as-of 2026-07-02)
Source 1 of `expand-city-sources` (additive; audited layers untouched) — the staff analysis behind
Council + Planning Commission agenda items, keyed by meeting date. **Pilot window 2024–2025**
(2020–2023 available on the same portal, **deferred**). Retrieved via Granicus **ViewPublisher**:
each meeting's agenda PDF (`AgendaViewer.php?clip_id=…`) is an outline that **embeds hyperlinks** to
its per-item staff reports/exhibits (Legistar attachments) — the packet = agenda + linked
attachments. **564 files / 341 MB** in `packets/raw/<date>/` (+ `_fetch_log.jsonl`, sha256 per file):
**112 agendas** (56 Council + 56 PC) + **452 staff reports** (74 Council + 378 PC); 555 born-digital
text, 9 image-scan. Provenance in `packets/index.csv` (`doc_type` ∈ `agenda`/`staff_report`;
`format`, `path`, `bytes`, `clip_id`, `delivery`). Joins to minutes/votes by **`date`+`body`** (52/53
council dates match `meeting_minutes` exactly; PC Work Sessions have packets but no minutes).
- **Asymmetry (important):** PC packets are effectively complete (**45/56 meetings** carry staff
  reports), but only **5/56 council meetings** do — the other 51 council agendas *name* their
  attachments in text but don't hyperlink them, so those council staff PDFs aren't portal-retrievable
  for 2024–2025 (Lehi moved council onto the linked pipeline at the 2025→2026 boundary). Not a
  scraper limit — a publishing gap.
- **Sampling:** a 4 MB/file cap on attachments dropped **163 large exhibits (~3.05 GB, mostly PC
  plats/studies)** — all logged with source URLs in `packets/dropped_oversize.csv` (re-fetch to lift).
  Genuine gap: **2024-07-23 council** (no agenda posted). See `packets/AVAILABILITY.md` + `CLAUDE.md`.
- **doc_class (2026-07-16):** 272 staff_report classified (2024–25 pilot window only; 2020–23 deferred);
  the 553 packet text sidecars are real (the stale "no text corpus" note was corrected).

## housing_plans/ — General Plan + Moderate Income Housing (additive; as-of 2026-07-02)
Land-use / housing planning record, built by `expand-city-sources` (Source 2). **9 raw PDFs (~35 MB)**
retained in `housing_plans/raw/` (+ `_fetch_log.jsonl`); Lehi-specific text sidecars in
`housing_plans/text/`; provenance in `housing_plans/index.csv` (`doc_type` ∈
`general_plan`/`mih_element`/`mih_annual_report`/`compliance_letter`).
- **City (lehi-ut.gov):** current **General Plan** (2022 Final Document, 136 pp) + Land Use Map + Max
  Density Map; **Moderate Income Housing Element** (adopted 2017-12-12, **updated 2024-05-28** per
  HB 462 / Utah Code 10-9a-403 & 408) + its signed adopting ordinance.
- **State (Utah DWS/HCD):** Lehi's **annual MIH implementation reports** as published in HCD's
  statewide compilations for **2023 / 2024 / 2025** (Lehi's page range extracted per year) + the
  **SB 34 Municipal Progress Summaries 2019–2021** (Lehi #35) as the compliance proxy.
- **Gaps:** HCD publishes no standalone per-city report PDF (the compilation is the record) and no
  per-city compliance letter; General Plan pre-adoption drafts deferred. See
  `housing_plans/AVAILABILITY.md` and `housing_plans/CLAUDE.md`. The 2024-05-28 MIH adoption joins to
  `meeting_minutes/all_votes.csv` by date.

## transcripts/ (additive — meeting-video transcripts)
Source 5 of `expand-city-sources` (additive; audited layers untouched). Lehi meeting **video** is on
YouTube ("Lehi City Public Meetings", channel `UCvdXq4ki7K9EU0FWLtTKCIw`) and Granicus MediaPlayer;
**AI/ASR transcripts** exist at OpenUtah (`https://lehi.openutah.org/`, ~87 of 115 meetings, 2025–present).
**No transcript text was recovered** — `yt-dlp` (the clean caption path) is not installed here, and
OpenUtah's transcript text sits behind a `robots.txt`-disallowed `/api/` (not scraped). Ships as an
honest **video→date map** of 12 sample council/PC meetings in `transcripts/index.csv` +
`transcripts/unrecovered.csv`; all captions would be **ASR — expect word errors; NOT an official
record**. High-value meetings proposed for Whisper are in `transcripts/AVAILABILITY.md`. See
`transcripts/CLAUDE.md`.

## ordinances/ (additive — adopted ordinance index + motion linkage)
Source 3 of `expand-city-sources` (additive; audited layers untouched). Lehi publishes **no online
full-text ordinance archive** (codified code is on American Legal `codelibrary.amlegal.com/codes/lehiut`,
bot-protected; only current-year Recorder "Notice of Ordinance Adoption" PDFs are online; full texts are
"on file at the Recorder's Office"). So `ordinances/index.csv` is a **derived index** built from the
council minutes: 334 motions (2020–2026) cite an ordinance number → **313 unique adopted ordinances,
284 (91%) land-use** (zone changes, Development Code text amendments, general-plan/area-plan amendments,
subdivision, annexation, design standards). Each ordinance maps to its adopting **motion** in
`meeting_minutes/all_votes.csv` — **confidence 295 high / 17 medium / 1 none** (never forced). The two
downloadable 2026 notice PDFs are retained in `ordinances/raw/`. See `ordinances/CLAUDE.md` +
`ordinances/AVAILABILITY.md`.

## pmn_backfill/ (additive — Utah Public Notice cross-check + recovered minutes)
Source 4 of `expand-city-sources` (additive; audited layers untouched). Cross-checks the repo's
Granicus-built minutes against the **Utah Public Notice Website** (PMN, `utah.gov/pmn`) — council
body **2512**, Planning Commission body **2651** (also found: RDA 3315, LBA 7881, Board of Adjustments
2661). Enumerated each body's full notice history via PMN's **GET** cumulative browse endpoint
(`/pmn/list/notices.html?id=<body>&page=200`; council 981 notices 2009→2026, PC 565 notices 2010→2026).
**Finding: the Granicus repo is the superset** for 2020-present — it holds more approved minutes than
PMN carries in every in-scope year (PMN attaches minutes to only ~26% of council / ~5% of PC notices).
A per-**date** set-difference found exactly **6** meeting dates PMN had that the repo lacked; **all 6
recovered** (born-digital, `pdftotext -layout`, screener-clean) into `pmn_backfill/raw|text` +
`pmn_backfill/index.csv`: 3 council (2020-02-04 WS, 2020-08-04 joint WS, **2021-07-13 regular meeting**)
+ 3 PC 2025 work sessions. **0 in-scope PMN minutes remain unrecovered**; pre-2020 PMN minutes
(127 council/10 PC) are below the 2020 floor and left un-downloaded but enumerated. Kept a *separate*
dataset (not merged into the audited layer). See `pmn_backfill/coverage.md` + `CLAUDE.md`.

## campaign_finance/ (additive — candidate financial disclosures)
Source 6 of `expand-city-sources` (additive; audited layers untouched). **134 municipal campaign
financial statements** filed by Lehi **Mayor + City Council** candidates for **2019, 2021, 2023,
2025** (2019: 27 / 2021: 20 / 2023: 36 / 2025: 51). **Lehi runs its OWN disclosure** — the state
site `disclosures.utah.gov` only **redirects** to the city page, and Utah County posts county/state
(not municipal) filings. 2025 came from the live city page (`…/elections/financial-disclosures/`,
`/media/` PDFs); **2019/2021/2023 were recovered from the Wayback Machine** because the legacy page
(`…/campaign-finance-disclosures/`, `/wp-content/uploads/` PDFs) now **404s** after a CMS migration.
Raw PDFs verbatim in `campaign_finance/raw/<year>/` (+ `_fetch_log.jsonl`); provenance in
`campaign_finance/index.csv` (`filing_type`, `office`, `election_year`, `matched_election_candidate`,
`join_confidence`, `reporting_period`, `amended`). Joins to `election_results` by **person + year** —
**all 12 general-election winners have ≥1 filing**. `unrecovered.csv` logs **12 missing 2023 report
PDFs** (never archived + 404 live; no candidate fully missing). **No dollar amounts transcribed** —
read the raw PDF. Also flags a **2019 primary** the recovered page reveals but `election_results`
omits (documented, not fixed). See `campaign_finance/CLAUDE.md` + `AVAILABILITY.md`.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Validation: `python3 meeting_minutes/validate_votes.py`
  · Weekly bundles: `python3 build_weeks.py` (`CITY="Lehi"`, `MEETING_WEEKDAY=Tuesday`). Canonical
  truth = the dataset CSVs (+ each file's Granicus `source_url`); raw PDFs are not retained
  (regenerable from `minutes_index.csv`); `weeks/` is derived.
