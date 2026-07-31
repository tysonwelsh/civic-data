# Lehi City Council — data repository

Canonical datasets about the **Lehi City Council** (Utah County, Utah), modeled on the Salt Lake
City reference repo, plus a derived weekly view. Built by the `build-city-data-repo` skill. Data
floor: **2020**. Independent QA: `VERIFICATION.md` (overall **PASS**).

```
meeting_minutes/   175 council/LBA minutes (markdown, Granicus) + roll-call votes (all_votes.csv)
planning_commission/  160 PC minutes + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                   (the appointed technical land-use body; recommendations vs final actions)
db/                NORMALIZED RELATIONAL DATABASE (db/lehi.db SQLite + table CSVs) joining ALL bodies'
                   votes by real keys + reconstructed PC→Council referrals. Start here: db/SCHEMA.md
public_comments/   all_comments_clean.csv (42 GENUINE written, 2020 only) + minutes_speaker_log.csv
                   (148 in-person paraphrases, NOT comments) + AVAILABILITY.md
election_results/   Utah County results, Lehi mayor + at-large council (RCV 2021 & 2023)
geo/                city boundary + precincts + address->in-city-limits tool (at-large, no districts)
weeks/              DERIVED weekly bundles (build_weeks.py: CITY="Lehi", MEETING_WEEKDAY=Tuesday)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Tuesday — 2nd & 4th)**. Votes + minutes carry the
meeting date; `build_weeks.py` buckets every record onto that weekly grid. Elections are point-in-time
(Nov, odd years) and join by **person + year** (council is at-large — no district key).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (6,147 member-vote rows / 1,253
  motions). Filter `body` for Council (1,245 motions) vs MBA (8). `body=RDA` is 0 by design (see below).
- **Genuine public sentiment**: `public_comments/all_comments_clean.csv` (42 verbatim, 2020 only). Do
  NOT use `minutes_speaker_log.csv` (148 in-person paraphrases) as a comments dataset.
- **Meeting-level**: the `weeks/<tuesday>/` bundle (`summary.md`). **By person**: join
  `election_results/lehi_races.csv` winners ↔ votes. **By geography**: `geo/address_to_district.py`
  → inside/outside city limits + precinct (informational; there are no council districts).

## Council structure
**Mayor + 5 all-at-large councilmembers (0 districts).** The **Mayor does NOT vote except to break a
tie** — exactly 4 recorded tie-break rows (all Mayor Johnson; Mayor Binns none). The extractor
excludes the Mayor from routine vote rows. Meets 2nd & 4th Tuesdays (work sessions 2nd Monday).

## Data notes / caveats
- **Votes**: 1,253 motions / 6,147 rows / 99 contested (post 2026-07-02 dedup — see VERIFICATION.md
  addendum: 8 same-date duplicate Granicus events removed). Three roll-call formats coexist (per-member
  inline `Councilor X, Yes;`; 2025+ `YES:`/`NO:` label blocks; MBA `Vote: Mr./Ms. X`) — all parsed.
  Tally-only/"passed unanimously" motions carry `names_recorded:false` (no guessed members). 2 tally
  mismatches are confirmed **source typos** (printed summary vs. named roll call), flagged not corrected.
- **`body` column** (`Council` / `MBA`; `RDA`=0): Lehi's in-council RDA recesses are **empty**
  (recess→immediate reconvene, no motions), so RDA=0 is honest, not a gap. The Local Building Authority
  meets separately → `body=MBA` (8 motions).
- **Comments**: in-minutes-only — the SpeakUp eComment portal is submit-only; the 42 genuine comments
  are 2020 COVID-era verbatim text published in the minutes. See `public_comments/AVAILABILITY.md`.
- **Elections**: at-large; RCV in 2021 & 2023 (final-round winners); 2023 Astill withdrawal/recount
  handled. All 9 winners externally verified. See `election_results/CLAUDE.md`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. 1,089 motions / 6,219 rows / 140 contested across **160 meetings**.
  Roster (19 appointed commissioners) in `planning_commission/roster.csv` (built from attendee
  headers — no election; cross-checked vs 11 council appointment votes). The `result` string encodes
  the **recommendation-vs-final-action taxonomy**: `Positive/Negative recommendation N:N` (forwarded
  to Council — 661 of them) vs `N:N Approved (Final Action)` (CUP/site-plan/design — never reach
  Council — 428). See `planning_commission/CLAUDE.md`.
- **`db/lehi.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no file number exists in
    Lehi) and **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high) tells you how solid each grouping is.
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — 459 scored links (273 high / 177 medium /
    9 low), all Council←PlanningCommission here (the table also models Council←agency / PC←agency for
    cities with one; Lehi's MBA carries none). The table is keyed
    `(primary_application_id, primary_body, related_application_id, related_body, match_method,
    confidence, …)`. **`high`≈exact (address+subject); `medium` spot-check before quoting; `low`
    flagged.** 68% of council land-use items linked; the rest are honestly unlinked (PC origin pre-2020,
    or council-initiated). Correct mistakes in `db/overrides.csv` / `db/referral_overrides.csv` + rebuild.
  - **Lehi address nuance:** a "shared address" is an approximate **grid intersection**, not a parcel,
    so address-alone is co-location (low), not exact. The PC↔Council join's payoff = the
    technical-vs-political divergence (PC negative rec → Council pass). Use `v_referral_chain` /
    `v_project_timeline`.

## packets/ (additive — agenda packets & staff reports, as-of 2026-07-02)
Built by `expand-city-sources` (Source 1); does NOT touch the audited layers above. The staff
analysis behind **City Council + Planning Commission** agenda items (staff reports, fiscal notes,
zoning/land-use analysis, resolutions, exhibits), **pilot window 2024–2025** (2020–2023 deferred).
Scraped from Granicus **ViewPublisher**: each meeting's agenda PDF embeds hyperlinks to its per-item
Legistar attachments, so the packet = agenda + linked attachments. **112 meetings · 564 files ·
341 MB** in `packets/raw/<date>/` — 112 agendas (56 Council + 56 PC) + 452 staff reports (74 Council
+ 378 PC); 555 text / 9 scanned. Provenance: `packets/index.csv`
(`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path,bytes,clip_id,delivery`),
`extraction_method=none (raw retained)` on the original rows — but the "no text extracted"
state is HISTORICAL: 553 real text sidecars now live in `packets/text/` (mandatory-sidecar
retrofit), and the index carries the 2026-07-16 doc_class columns (see below).
- **Join by `date`+`body`** to `meeting_minutes/all_votes.csv` (Council) / `planning_commission/`
  (PC) and to `db/lehi.db` motions; a staff report's `title` often names the ordinance/resolution or
  applicant to tie it to a specific motion. PC Work Sessions have packets but no minutes (expected).
- **Council staff-report asymmetry** (read `packets/AVAILABILITY.md`): only **5/56** council meetings
  have hyperlinked staff reports vs **45/56** PC — the other 51 council agendas name attachments in
  text but don't link them (portal publishing gap, fixed at the 2025→2026 boundary; not a scraper
  limit). Don't read sparse council `staff_report` rows as sparse council business.
- **Sampling:** a 4 MB/file attachment cap dropped **163 large exhibits (~3.05 GB, mostly PC plats)**
  — logged with URLs in `packets/dropped_oversize.csv`. Gaps in `packets/unrecovered.csv`
  (2024-07-23 council: no agenda posted). See `packets/CLAUDE.md` for the S3-underscore TLS quirk and
  full scrape method.
- **doc_class layer** (2026-07-16): 272 staff_report classified (2024–25 pilot window only; 2020–23
  packets remain the deferred gap), gates 100%. The 553 packet text sidecars are real — the stale
  "no text corpus" claim was corrected in `packets/CLAUDE.md`.

## housing_plans/ (additive — General Plan + Moderate Income Housing, as-of 2026-07-02)
Built by `expand-city-sources` (Source 2); does NOT touch the audited layers above. Holds Lehi's
current **General Plan** (2022 Final Document + maps), its **Moderate Income Housing Element**
(Utah Code 10-9a-403/408, HB 462; adopted 2017-12-12, updated 2024-05-28) + adopting ordinance, and
the **annual MIH reports** Lehi files with Utah DWS/HCD (statewide compilations 2023/2024/2025, Lehi
pages extracted) + the SB 34 2019–2021 progress summary. Raw PDFs retained in `housing_plans/raw/`;
see `housing_plans/index.csv` (`doc_type` col) + `housing_plans/CLAUDE.md`. The 2024-05-28 MIH element
adoption is joinable to `meeting_minutes/all_votes.csv` by date (PC recommendation 2024-05-09).

## pmn_backfill/ (additive — Utah Public Notice cross-check, as-of 2026-07-02)
Built by `expand-city-sources` (Source 4); does NOT touch the audited minutes layers. Cross-checks
the Granicus-built minutes against the **Utah Public Notice Website** (PMN) — council body **2512**,
Planning Commission body **2651**. PMN's full per-body notice history was pulled via its GET
cumulative browse endpoint (`/pmn/list/notices.html?id=<body>&page=200`; NOT the POST search).
**The repo is the superset for 2020-present** — a per-**date** set-difference (not raw counts; PMN
minutes attachments are sparse) found exactly **6** meeting dates PMN carried that the repo lacked,
**all recovered** into `pmn_backfill/index.csv` + `raw/`+`text/` (born-digital, `pdftotext -layout`):
3 council (2020-02-04 WS, 2020-08-04 joint WS, **2021-07-13 regular meeting** — a genuinely missing
2nd-Tuesday regular session with full roll-call votes) + 3 PC 2025 work sessions. **0 in-scope PMN
minutes remain unrecovered.** Pre-2020 PMN minutes (127 council/10 PC) are below the 2020 floor →
enumerated, not downloaded. Rows join by meeting date; kept SEPARATE for deliberate review (never
folded into `meeting_minutes/`). See `pmn_backfill/coverage.md` + `CLAUDE.md`.

## transcripts/ (additive — meeting-video transcripts, as-of 2026-07-02)
Built by `expand-city-sources` (Source 5); does NOT touch the audited layers above. Lehi posts
meeting **video** on YouTube ("Lehi City Public Meetings" channel
`UCvdXq4ki7K9EU0FWLtTKCIw`; also on Granicus MediaPlayer), and OpenUtah
(`https://lehi.openutah.org/`) publishes **AI-generated (ASR-quality) transcripts** — "AI-generated
content may contain errors." The dataset is an honest **video→date map** (12 sample council/PC
meetings, 2025–2026) in `transcripts/index.csv`; `date`+`body` join to
`meeting_minutes/`/`planning_commission/` votes. **Caption backfill 2026-07-20: 2 of 12 recovered**
(`yt-dlp` now installed) — the two 2026 meetings still public on YouTube (2026-05-26 Council
`GMYzejWyA2U`; 2026-05-28 PC `ajch_vFR84k`): English auto-caption VTT in
`transcripts/raw/<date>.en-orig.vtt`, cleaned `transcripts/text/<date>.md` sidecar, index rows
`format=caption`; PC row spot-checked against 2026-05-28 minutes (matches). **The other 10 (all
2025) are a genuine gap** — those videos are no longer public on YouTube (gone from both official
channels' uploads/playlists, no search hit) and OpenUtah exposes no per-video id (transcript behind
a `robots.txt`-disallowed `/api/`); ledgered in `transcripts/unrecovered.csv`. All recovered text is
ASR, **NOT the official record** — the clerk's minutes remain authoritative. See
`transcripts/AVAILABILITY.md` + `transcripts/CLAUDE.md`.

## ordinances/ (additive — adopted ordinance index + motion linkage, as-of 2026-07-02)
Built by `expand-city-sources` (Source 3); does NOT touch the audited layers above. Lehi publishes
**no online full-text ordinance archive** — the codified code is on **American Legal**
(`codelibrary.amlegal.com/codes/lehiut`, bot-protected 403), only **current-year** Recorder "Notice of
Ordinance Adoption and Summary" PDFs are posted, and full texts are "on file at the Recorder's Office."
So the dataset is a **derived index**: 334 council motions (2020–2026) cite an ordinance number in
their text, yielding **313 unique adopted ordinances** (`ordinances/index.csv`), **284 (91%) land-use**
(zone changes 91, Development Code text amendments 115, general-plan 45, area-plan 22, subdivision,
annexation, design standards). Each row maps `ordinance_no`→`adoption_date`→the adopting motion in
`meeting_minutes/all_votes.csv` (`matched_motion_date`+`matched_motion_no`, and `minutes_source`).
**Linkage confidence: 295 high / 17 medium / 1 none** — high = number+date both in one motion event
(within-source join, since the index is derived from the motions); medium = number cited across >1
meeting date (continued/renumbered — spot-check) or the notice-only impact-fee ord matched by
subject+date; none = #2026-04 Noise (adopted 2026-02-10, beyond vote coverage — no match, not forced).
Only the two 2026 notice PDFs were downloadable (`ordinances/raw/`, cross-validate the 2026 rows).
See `ordinances/CLAUDE.md` (linkage detail) + `ordinances/AVAILABILITY.md` (host + gap record).

## campaign_finance/ (additive — candidate financial disclosures, as-of 2026-07-02)
Built by `expand-city-sources` (Source 6); does NOT touch the audited layers above. **134 municipal
campaign financial statements** filed by Lehi **Mayor + City Council** candidates for **2019/2021/
2023/2025** (27/20/36/51). **Lehi hosts its own disclosure** — `disclosures.utah.gov` merely
redirects to the city page; the county posts county/state (not municipal) filings. 2025 from the live
city page (`/media/` PDFs); **2019/2021/2023 recovered from the Wayback Machine** (the legacy
`…/campaign-finance-disclosures/` page + its `/wp-content/uploads/` PDFs now 404 after a CMS
migration). Raw PDFs verbatim in `campaign_finance/raw/<year>/`; `campaign_finance/index.csv` carries
`office`/`election_year`/`filing_type=statement`/`reporting_period`/`matched_election_candidate`/
`join_confidence`. **Completes elections→members→votes:** joins `election_results` by **person+year**
(case-fold; finance is mixed-case vs "Councilor X" in minutes) — **all 12 general-election winners
have ≥1 filing**. Caveats: `date` is a period proxy (upload-path month, or election year for 2025);
**no dollar amounts transcribed** (read the raw PDF); `unrecovered.csv` = 12 missing 2023 PDFs
(never archived, 404 live; no candidate fully missing). Also flags a **2019 primary** the recovered
page reveals but `election_results/CLAUDE.md` says didn't happen — documented, NOT fixed here. See
`campaign_finance/CLAUDE.md` + `AVAILABILITY.md`.

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) reports Granicus ViewPublisher rows newer than
  each index; `--fetch [--dataset meeting_minutes|planning_commission]` downloads new minutes PDFs to
  `<dataset>/raw/`, converts to markdown, appends `minutes_index.csv` (+ `fetch_log.csv`), and runs
  extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
- After a fetch, rebuild: `python3 db/build_db.py` + `db/build_referrals.py`, `python3 build_weeks.py`,
  `python3 ../scripts/normalize_motions.py --all`. Note 2026-07-02: Lehi had posted no council minutes after
  2026-01-27 (19 meetings unposted on the portal) — the staleness is city-side; re-probe periodically.

## Analysis guidance
- **Contested votes (any Nay/Abstain/Recuse) are the signal** (99 council, 140 PC); `weeks/<tue>/summary.md`
  surfaces council ones. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).
- Mayor tie-breaks (4) are the rare high-drama moments — worth examining individually.
- **8 people served on both Council and PC** (commissioners later elected) — unified by name in the DB
  `person`/`role` tables; profile a career across both bodies with `v_member_record`.
