# Provo City Council — data repository

A Salt Lake City-style civic-data repository for the **Provo Municipal Council**, built
2026-06-24 by the `build-city-data-repo` skill. Council minutes, extracted roll-call votes,
genuine public comments, municipal election results, and an address→district tool — all as
markdown/CSV, covering **2020–present**. See `CLAUDE.md` for how to analyze it and each
subfolder's `CLAUDE.md` for build details. Independent QA in `VERIFICATION.md` (**PASS**;
16/16 election winners externally confirmed).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 311 meetings (markdown) | Hyland OnBase (`agendas.provo.gov`), text-layer PDFs | ✅ 18 meetings cancelled/not-yet-approved (no minutes) |
| Roll-call votes | 2020–2026 | 1,074 motions · 6,365 rows · 160 contested (Council 1,015 + RDA 59) | extracted from minutes | ✅ verified |
| Planning Commission votes | **2025–2026 only** | 102 motions · 673 rows · 26 meetings · 22 contested · 12 commissioners | AgendaCenter consolidated PC minutes | ⚠️ `planning_commission/` — 2020–2024 not published (source gap) |
| Relational database | 2020–2026 | 3 bodies · 425 apps · 1,176 motions · 6,920 votes + 12 reconstructed Council←RDA referrals | derived from the vote CSVs | ✅ `db/civic.db` — start at `db/SCHEMA.md` |
| Public comments (genuine written) | 2020–2022 | **81** residents' emails/letters | agenda-packet attachments (`source=agenda_packet`) | ✅ packets fully harvested; 2023+ via gated OpenGov portal (unrecoverable) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 738 in-person speakers | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` — record notes only |
| Election results | 2019, 2021, 2023, 2025 | 26 races · 69 candidates · 1,455 precinct rows | Utah County (`vote.utahcounty.gov`) | ✅ verified (16/16 winners) |
| Geo (address→district) | current map | 67 precincts → Districts 1–5 | Provo City GIS + election precincts | ✅ tested |
| Weekly bundles | 2020–2026 | 183 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**5 District seats + 2 Citywide (at-large) + separately-elected Mayor.** The Mayor does NOT
vote on council motions (council votes are 7-member). Geo maps addresses to Districts 1–5;
Citywide members represent everyone. Seats stagger: Cycle A (Citywide I, D2, D5, Mayor)
elected 2021/2025; Cycle B (Citywide II, D1, D3, D4) elected 2019/2023.

## Planning Commission + relational database
- **`planning_commission/`** holds the appointed land-use body's roll-call votes (same 13-column
  schema, `body=PlanningCommission`): 102 motions across 26 meetings, with the `result` string
  distinguishing **advisory recommendations to the Municipal Council** from **PC final actions**.
  **PC data is 2025+ only** — Provo published no PC minutes for 2020–2024 (a documented city source
  gap; see `planning_commission/CLAUDE.md` and `planning_commission/minutes_unrecovered.csv`).
- **`db/civic.db`** is the **canonical, queryable** form — a normalized SQLite model joining Council,
  RDA, and Planning Commission votes by real keys, plus a separate **reconstructed cross-body
  referral** layer. **Start at `db/SCHEMA.md`.** Two layers: the within-body core is **exact**
  (project keys resolved from prose, body-scoped — `0 apps span >1 body`); the cross-body `referral`
  layer is **reconstructed, scored, and overridable** (`12` links, all **medium**, all **Council←RDA**
  — the RDA/CRA project-area matters the Council ratifies; there are no PC→Council links yet because
  the PC record only begins in 2025). Build: `python3 db/build_db.py` then
  `python3 db/build_referrals.py`.

## Public comments — what's here and the ceiling
- `all_comments_clean.csv` = **81 genuine public-submitted written comments** — residents'
  own emails/letters bundled into council agenda packets, concentrated on 2020–2021
  land-use fights (2022=2, none 2023+). All 138 regular-meeting packets were harvested.
- **The ceiling:** from ~2023 Provo's written public input moved to the **OpenGov "Open
  City Hall"** portal, which cloaks bots to HTTP 404 and whose statement bodies were never
  archived by Wayback — so it's not retrievable without an interactive browser session.
  Documented in `public_comments/AVAILABILITY.md`.
- `minutes_speaker_log.csv` (738 rows) holds the clerk's in-meeting paraphrases of in-person
  speakers — **meeting-record notes, NOT public-submitted comments** — kept separate by design.

## Expansion datasets (`expand-city-sources`, as-of 2026-07-03)
Six additive source layers beyond the core minutes/votes/comments/elections. Each has its own
`CLAUDE.md` + `AVAILABILITY.md`; all pass `validate_dataset.py`; none modify existing data.

### Agenda packets / staff reports — `packets/` (LINK INDEX)
**391 packets indexed** (no PDFs stored — bundled whole-meeting PDFs, image/map-heavy, ~16 GB for
council alone). Provo splits bodies across **two portals**: **Council on Hyland OnBase**
(`agendas.provo.gov`, documentType=5, CSRF+cookie flow — 306 packets) and **Planning Commission on
CivicPlus AgendaCenter** (`provo.gov/AgendaCenter`, `ViewFile/Agenda/<ref>` — 85). 100% vote-date
coverage both bodies. OnBase serves `Transfer-Encoding: chunked` with **no Content-Length**, so
council packet sizes are unknown-by-HEAD (`size_source` column records this); PC sizes measured.
PC packets are thin agenda outlines before mid-2025. See `packets/CLAUDE.md` to fetch one on demand.

### Moderate-income housing + General Plan — `housing_plans/`
**6 PDFs (~33 MB):** the **2023 General Plan**, the **MIH element** (GP Appendix B, 2022–2027 —
not linked on the GP page, found by search), and the **2023/24/25 state HCD compilations** + **SB 34**
(Provo pages bracketed by Providence/Riverdale, zero bleed). Docs are on `www.provo.gov` (CivicPlus
DocumentCenter); the newer `provo.org` domain is bot-gated (403). See `housing_plans/CLAUDE.md`.

### Zoning / land-use ordinances — `ordinances/`
**213-row index** (135 zoning) linking ordinance number → adoption date → adopting motion. Both code
hosts (amlegal, provo.municipal.codes) are 403-blocked, so the authoritative source is **Utah PMN's
Recorder-certified "Notice of Ordinances Approved" `.docx`** (body 1600) — an *independent* list
enabling genuine cross-matches: **34 `high` / 20 `medium` / 126 `within_source` / 33 `none`**.
`adopted_not_in_votes.csv` splits the audit signal into 30 coverage-boundary (minutes published late)
vs **3 genuine** discrepancies. 2023 has no ordinance numbers in the minutes (a real gap). See
`ordinances/CLAUDE.md`.

### Utah Public Notice (PMN) backfill — `pmn_backfill/`
The largest recovery in the repo: **390 documents / 100 meeting-dates (118 MB)**. Bodies **1600 =
Council, 1662 = Planning Commission** (entity 244). Recovered **8 council special/joint meetings**
absent from OnBase, and — critically — the **entire empty 2020–2024 Planning Commission record** as
**per-item "Report of Action" (ROA) PDFs** (the repo held PC only from 2025). 0 still-missing, both
bodies. Kept separate from the audited `minutes/` layer. Coverage table in `pmn_backfill/coverage.md`.

### Meeting video transcripts — `transcripts/`
**10 ASR YouTube caption tracks** + a **740-video channel map** (`channel_videos.csv`) from
`youtube.com/ProvoCityCouncil` (channel `UC1yR7j8igrjxXOR0XsCasfw`), continuous 2014–present (no
off-YouTube cutoff). 100% automatic (`en-orig`), de-duplicated, ASR word-error caveat headed on every
`text/<date>_<body>.md` — **not an official record**. Planning Commission is essentially absent from
the channel (1 video). Whisper proposed for caption-less/high-stakes meetings, not run. See
`transcripts/AVAILABILITY.md`.

### Campaign-finance disclosures — `campaign_finance/`
**41 filings (~50 MB)** completing elections → members → votes. Filed with the **City Recorder** and
posted on the CivicPlus DocumentCenter page (`provo.gov/1001/Election-Documents`) — NOT
`disclosures.utah.gov` (redirect-only) or any EasyVote instance (Provo self-hosts). 2021/2023/2025;
**38/41 join** to `election_results` (3 unmatched = filed-but-withdrew, logged); **2019 is a genuine
city-side gap** (page coverage starts 2021). Scanned forms OCR'd (incl. an upside-down scan). See
`campaign_finance/CLAUDE.md`.

## Known gaps / caveats
- 18 meetings have no minutes (cancelled or not-yet-approved — listed in build notes); one
  2022-01-18 file was OCR'd. 117 tally-only votes carry `names_recorded:false` (no guessed
  members). 12 vote-validation flags are genuine source typos, kept verbatim.
- Elections: 2021 & 2025 have precinct detail; 2019 & 2023 are citywide-only (county
  published no precinct SOVC). Districts 1/3/4 geo derives from the city GIS layer.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · PC votes:
  `python3 planning_commission/extract_votes.py` · Relational database:
  `python3 db/build_db.py` then `python3 db/build_referrals.py` (idempotent) · Packet comments:
  `python3 public_comments/harvest_packets.py` (resumable) · Weekly bundles:
  `python3 build_weeks.py`. Canonical truth = `*/raw/` + dataset CSVs; `weeks/` is derived.
