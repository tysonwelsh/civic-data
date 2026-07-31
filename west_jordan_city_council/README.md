# West Jordan City Council — data repository

A Salt Lake City-style civic-data repository for the **West Jordan City Council**, built
2026-06 by the `build-city-data-repo` skill. Council minutes, extracted roll-call votes,
genuine public comments, municipal election results, and an address→district tool — all as
markdown/CSV, covering **2020–present**. See `CLAUDE.md` for analysis guidance; independent
QA in `VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 250 meetings (markdown) | PrimeGov (`westjordan.primegov.com`), mostly born-digital text PDFs | ✅ complete; early (≈2020–21) files end in OCR'd scanned signature pages (cosmetic junk only) and 2020-02-12 is OCR throughout — motion/vote text verified clean |
| Roll-call votes | 2020–2026 | 1,157 motions · 5,830 rows · 150 contested | extracted from minutes | ✅ verified (2020–21 recovered in repair; see caveat) |
| Planning Commission | 2020–2026 | 84 meetings · 384 motions · 15 commissioners | PrimeGov (`planning_commission/`) | ✅ verified; **tally-only** (dissent named, no aye list); 36/84 OCR |
| Relational database | 2020–2026 | `db/civic.db` — 4 bodies · 1,163 motions · 7,011 votes · 21 PC→Council referrals | derived from the vote CSVs | ✅ canonical; **start at `db/SCHEMA.md`** |
| Public comments (genuine written) | 2022 | **28** residents' emails (Welby West rezone) | agenda-packet correspondence (`source=agenda_packet`) | ✅ all 120 packets harvested; verdict IN-PACKETS |
| Minutes speaker log (NOT public comments) | 2020–2026 | 239 in-person speakers | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 13 races · 37 candidates · 1,978 precinct rows | Salt Lake County (`slco-election-archive`) | ✅ verified (13/13 winners) |
| Geo (address→district) | current map | 96 precincts → Districts 1–4 | SLCo Vista + city Council_Districts FeatureServer | ✅ tested |
| Weekly bundles | 2020–2026 | 187 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**4 District + 3 At-Large + separately-elected Mayor.** The Mayor (Dirk Burton) does **not**
vote on council motions (council votes are 7-member). Geo maps addresses to Districts 1–4;
at-large + mayor are city-wide. At-large seats fill via one grouped "Vote-for-3" race
(2021, 2025); district seats elect together (2019, 2023).

## Planning Commission + relational database
- **`planning_commission/`** — the appointed land-use body (Planning & Zoning Commission). 84 minutes
  files / **384 motions** / **15 commissioners** (`roster.csv`), with the
  **recommendation-vs-final-action** taxonomy in `result`: *positive/negative recommendation* (forwarded
  to Council) vs *Approved/Denied (Final Action)* (site plans, CUPs, preliminary plats — never reach
  Council). **Caveat — tally-only:** WJ PC minutes print a tally ("passed 6-0") and **never name the
  aye majority**; only named dissent/abstain/recuse + absentees are captured, so `all_votes.csv` has
  **no Aye rows**. 36 of 84 minutes are OCR'd scans; 2020–21 had no standalone PC meetings (only joint
  Council+PC work sessions). See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** — the **canonical, queryable** form of all vote data (**start at `db/SCHEMA.md`**).
  A normalized relational model joining **Council ↔ RDA ↔ MBA ↔ Planning Commission** by real keys.
  Two layers, never conflated: an **exact within-body core** (project keys *resolved from prose* — no
  file number exists — and **body-scoped**, so 0 applications span >1 body) plus a separate,
  **reconstructed + scored cross-body `referral`** layer (21 links, all Council←PlanningCommission;
  8 high / 9 medium / 4 low). Build: `python3 db/build_db.py && python3 db/build_referrals.py`
  (idempotent).

## Expansion datasets (`expand-city-sources`, as-of 2026-07-03)
Six additive source layers beyond the core minutes/votes/comments/elections. Each has its own
`CLAUDE.md` + `AVAILABILITY.md`; all pass `validate_dataset.py`; none modify existing data.

### Agenda packets / staff reports — `packets/` (LINK INDEX)
Staff analysis behind council + PC agenda items, from the **PrimeGov API**
(`ListArchivedMeetings?year=YYYY` → per-meeting `CompiledDocument?meetingTemplateId=`). PrimeGov
bundles each meeting into **one 0.4–330 MB compiled PDF** (agenda + all staff reports + exhibits;
median 13 MB; full 222-set = **7.36 GB**), image/map-heavy → not text-convertible. By owner policy
the PDFs are **not stored**; `index.csv` is a **link index of 222 packets** (Council 122, PC 70,
RDA 21, MBA 9; 2022–2026) with live `source_url` + `size_mb` + `packet_kind`, all HTTP 200 on
2026-07-03. 2023 & 2024 cover 100% of vote dates. **Gap:** West Jordan switched to an in-portal
HTML "Interactive Agenda" (SPA) in mid-2025 → no downloadable packet for those meetings (documented,
not a scraper miss). See `packets/CLAUDE.md` for how to fetch one on demand.

### Moderate-income housing + General Plan — `housing_plans/`
**11 PDFs (~75 MB):** adopted **2023 General Plan** + Future Land Use Map + adoption ordinance
(Ord. 23-10); the **MIH element** (Ord. 20-32, 2020 + a 2026 published copy); the city's **2020**
MIH annual report + accepting resolution; and the **2023/24/25 state HCD compilations** + **SB 34**
(WJ page-ranges sliced, neighbor-bleed verified zero). Post-2020 annual reporting exists only inside
the statewide compilations (expected Utah pattern). The city's "General Plan" nav link points to a
403-blocked amlegal host; the real PDF is on `wp-content`. See `housing_plans/CLAUDE.md`.

### Zoning / land-use ordinances — `ordinances/`
**285-row index** linking ordinance number → adoption date → adopting motion. Code host is a
**Municode SPA** (current-text-only) and PrimeGov exposes no ordinance doc type, so **61
recorder-signed zoning PDFs** (~46 MB, 2021–2025) were pulled from the City Recorder "Adopted
Ordinances" page (`wp-content` signed PDFs). Confidence: **58 `high`** (motion + independent signed
PDF agree), **224 `within_source`** (motion-only), **3 `none`**. Flagged (not fixed): **3 adopted
ordinances — 22-08, 23-08, 24-18 — are not cited in any `all_votes.csv` motion** (likely a
minutes-extraction gap). See `ordinances/CLAUDE.md`.

### Utah Public Notice (PMN) backfill — `pmn_backfill/`
Per-**date** coverage cross-check vs PMN (bodies **395 = Council, 396 = Planning Commission**;
entity 305). **33 meetings recovered** — 5 council + a **28-meeting standalone Planning Commission
run (16 in 2021, 12 in early 2022)** the PrimeGov-sourced repo never held (6 scanned → OCR; all
content-verified). This **contradicts the CLAUDE.md claim that 2020–21 had no standalone PC
meetings** — flagged. Kept separate from the audited `minutes/` layer. 0 still-missing. Coverage
table in `pmn_backfill/coverage.md`.

### Meeting video transcripts — `transcripts/`
**10 ASR YouTube caption tracks** (5 council + 5 PC, Nov 2024–Feb 2025) + a **647-video channel
map** (`channel_videos.csv`) for extension. All automatic (`en-orig`); no manual tracks exist. Key
finding: **West Jordan stopped posting meetings to YouTube after 2025-02-04**, shifting to
**Swagit + the OpenUtah mirror** (which covers the gap but is behind `robots.txt`). Every
`text/<date>_<body>.md` carries an ASR word-error caveat — **not an official record**. Whisper
proposed (post-cutoff budget/Truth-in-Taxation meetings), not run. See `transcripts/AVAILABILITY.md`.

### Campaign-finance disclosures — `campaign_finance/`
**135 filings (~208 MB)** completing elections → members → votes. West Jordan splits filings across
its own **EasyVote portal** (`cityofwestjordanut.easyvotecampaignfinance.com`, public
`viewfinalredactedpdf` endpoint; 2023+) and the **city WordPress site** (2021 + annual/conflict-of-
interest). Not on `disclosures.utah.gov` (state-only) or the county. Joins to elections (2023 8/8,
2021 6/8, 2025 6/11); **2019 is GRAMA-only** (not archived). 7 primary-only candidates flagged as
`election_results` gaps (not edited). Scanned forms OCR'd. See `campaign_finance/CLAUDE.md`.

## Known gaps / caveats
- **Votes are recorded roll-calls only.** West Jordan names individual votes mainly for
  substantive items; routine/consent business often passes without an individually recorded
  motion. So the ~13% Nay rate (150/1,157) is "among recorded roll-calls" and is **not**
  directly comparable to councils (e.g. Provo, SLC) that roll-call every motion.
- **Genuine written comments** are sparse and packet-dependent: residents' emails appear
  only when the clerk bundles "correspondence received" into a Complete Packet — heavily on
  the 2022 Welby West rezone. 2020/2021/2026 have no packets in the portal index; 2023–25
  packets carried only staff/vendor/inter-agency mail. The in-person speaker log (239) is a
  separate artifact, NOT public-submitted comments.
- Elections: county-administered; only West Jordan council+mayor races included. The 2019
  at-large was a one-off single-seat (first strong-mayor election) vs. the grouped Vote-for-3
  in 2021/2025 — documented in `election_results/CLAUDE.md`.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Weekly bundles: `python3 build_weeks.py`.
  Canonical truth = the dataset CSVs (+ each file's `source_url`); raw minutes PDFs are not
  retained (regenerable from `minutes_index.csv`); `weeks/` is derived.

---
*Doc correction 2026-07-02 (audit `_audits/2026-07-02/report.md`, Phase 1.8): the council
minutes "no OCR" claim was wrong — early (≈2020–mid-2021) files end in scanned/OCR'd
signature pages with cosmetic junk, and the 2020-02-12 minutes are an OCR'd scan
throughout ("occmTed", "11 :07"). Motion/roll-call text in those files spot-verified
clean. Same correction applied in `meeting_minutes/CLAUDE.md` and `recon.md`. (The PC
36/84 OCR share was already documented and re-verified against
`planning_commission/minutes_index.csv`.)*

*Repair 2026-07-02 (Phase 1.9): the 2022-06-22 council minutes had been parsed twice
(PrimeGov served the identical PDF under two meeting templates); the duplicate
`2022-06-22_city-council-regular-meeting.md` was removed and votes/db/weeks rebuilt —
counts above reflect the repair. See `VERIFICATION.md` (2026-07-02 addendum) and
`_backups/2026-07-02/west_jordan_city_council/` for originals.*
