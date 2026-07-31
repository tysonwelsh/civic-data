# Sandy City Council — data repository

A Salt Lake City-style civic-data repository for the **Sandy City Council** (Salt Lake
County, Utah), built 2026-06 by the `build-city-data-repo` skill. Council minutes, extracted
roll-call votes, public-comment availability, municipal election results, and an
address→district tool — all as markdown/CSV, covering **2020–present**. See `CLAUDE.md` for
analysis guidance; independent QA in `VERIFICATION.md`.

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 274 meetings (markdown) | Granicus **Legistar** (`sandyutah.legistar.com`) | ✅ complete (153 text · 63 PUA-decoded · 58 OCR) |
| Roll-call votes | 2020–2026 | 833 motions · 3,975 rows · 131 contested | extracted from minutes | ✅ verified (re-extracted 2026-07-02) |
| Planning Commission votes | 2020–2026 | 554 motions · 4,431 rows · 43 contested | **Legistar API** EventItemVote (exact; no PC minutes exist) | ✅ structured source |
| Relational db (`db/sandy.db`) | 2020–2026 | 1,387 motions · 8,109 votes · 116 PC→Council referrals | standard cross-city schema + `legistar_*` extension layer | ✅ conformant (2026-07-02, plan 2.6); see `db/SCHEMA.md` |
| Public comments (genuine written) | — | **0 published** | n/a — submit-only city | ⚠️ verdict SUBMIT-ONLY (see below) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 362 in-person speakers | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 14 races · 47 candidates · 2,811 precinct rows | Salt Lake County (`slco-election-archive`) | ✅ verified |
| Geo (address→district) | current map | precincts → Districts 1–4 | SLCo Vista + city Council_Districts | ✅ tested |
| Weekly bundles | 2020–2026 | 264 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Council–Mayor (strong-mayor) form. 4 District + 3 At-Large = 7 council members.** The
**sitting Mayor does NOT vote** on council motions (max tally is 7). Note: **Monica Zoltanski
was the District 4 councilmember in 2020–2021** (she cast 170 votes then) **before being elected
Mayor (took office Jan 2022)** — so her name legitimately appears in 2020–21 tallies; as Mayor
(2022+) she does not vote on council motions. (Her 4 Mayor-era rows — 2023-12-06 ×2 Excused,
2025-08-26, 2025-11-18 — are all **Board of Municipal Canvassers** canvass actions where the
minutes themselves list the Mayor; faithful captures.) **Scott Earl** held the vacated District
4 seat by appointment from Jan 2022 until Houseman won it in the 2023 election. The Council
elects its own Chair (Cyndi Sharkey), who presides. Geo maps
addresses to Districts 1–4; at-large + mayor are city-wide. The 3 at-large seats are staggered
**2+1**: two seats elect together (2019, 2023) and one elects alone (2021, 2025).

## Public comments — SUBMIT-ONLY (honest gap)
Sandy publishes **no archive of genuine written/online public comments**. The public is
directed to **email `CitizenComment@sandy.utah.gov`** (read into the record, not published).
A Granicus eComment/SpeakUp portal (`sandyutah.granicusideas.com`) was **briefly active in
2020–2021** (per-item "Click here to eComment" links survive in those minutes) but is now
dormant, with **no publicly visible or exportable submissions** from either era; Legistar marks
eComment "Not available." So `all_comments_clean.csv` is intentionally **empty** — an honest
gap, not a processing miss. In-person speaker paraphrases (362) live in
`minutes_speaker_log.csv` and are **not** public-submitted comments. Full audit:
`public_comments/AVAILABILITY.md`.

## Known gaps / caveats
- **PUA decode repair (2026-07-02).** 63 minutes (2021-08 → 2023-11) were originally stored
  as Unicode Private-Use-Area garble — the source PDFs for that span have a broken font
  ToUnicode cmap (verified against the retained `meeting_minutes/raw/` PDFs). They were
  mechanically decoded (−0xF000 per char), verified against the raw PDFs, and the votes
  re-extracted: motions 655 → 833, member-vote rows 2,974 → 3,975, contested 79 → 131
  (2022/2023 had been nearly vote-empty). These files carry `format=text_pua_decoded` in
  `minutes_index.csv`. Details: `meeting_minutes/CLAUDE.md`; originals in `_backups/2026-07-02/`.
- **Votes are recorded roll-calls only.** Sandy names individual votes mainly for substantive
  items; routine/consent business often passes without an individually recorded motion. So the
  ~16% contested rate (131/833) is "among recorded roll-calls" and is not directly comparable to
  councils that roll-call every motion. Tally-only/unanimous-without-names motions carry
  `names_recorded:false` (no guessed members).
- **Narrative-tally motions.** Some motions are recorded only as a sentence — e.g. *"the motion
  failed by a vote of 5-2 with X, Y opposed"* — naming **only the dissenters**, not the majority.
  For these the parser captures the tally + every named dissenter and orients the count by the
  pass/fail outcome (a failed "5-2" = 5 against, 2 for); the ayes stay **unnamed**
  (`names_recorded:false`) rather than guessing which members made up the majority.
- **Provenance granularity.** `minutes_index.csv` `source_url` points at the Sandy Legistar
  portal (`Calendar.aspx`), where each meeting is retrievable **by date** — per-meeting
  deep-links were not retained at acquisition (regenerable by re-scraping the Legistar calendar).
- **RDA — no separate minutes (verified).** `body=RDA` has only 1 vote, and that is essentially
  complete: Sandy's Redevelopment Agency does **not** publish separate minutes. A 2026 follow-up
  confirmed Legistar exposes only 5 bodies (no RDA/CDRA) and all 391 published minutes are City
  Council minutes. The RDA Board convenes **inside** City Council meetings (the council recesses,
  "convenes a meeting of the Sandy City Redevelopment Agency," usually in **closed session**, then
  reconvenes) — the extractor detects those brackets and tags any open RDA vote `body=RDA`, but
  Sandy's RDA almost always acts in closed session, so there is little public RDA roll-call to
  capture. Not an acquisition gap.
- Elections: county-administered; only Sandy council + mayor races included.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · PC votes:
  `python3 planning_commission/build_from_legistar.py` · Database:
  `python3 db/build_db.py && python3 db/build_referrals.py` (idempotent; prints CSV↔db
  reconciliation — council votes are minutes-primary, the measured decision is in
  `db/SCHEMA.md`) · Weekly bundles: `python3 build_weeks.py`
  (`CITY="Sandy"`, `MEETING_WEEKDAY=Tuesday`). Canonical truth = the dataset CSVs (+ the
  Legistar portal `source_url`, see provenance note above); the 274 raw source PDFs **are
  retained** under `meeting_minutes/raw/` (never modified); `weeks/` is derived.

## Expansion datasets (additive, 2026-07-05)
Six additional source layers built from the **Granicus Legistar Web API**, each fully
documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 462 agenda PDFs + 6,446 staff-report/exhibit attachments catalogued with
  live URLs (index-only, ~14.9 GB on the portal). The staff analysis behind each agenda item.
- **`housing_plans/`** — moderate-income-housing element, biennial report, and state housing
  compilations (the current General Plan is a web/ArcGIS product with no PDF).
- **`ordinances/`** — 170 ordinance matters (87 adopted, 65 land-use), each linked to the
  council vote that passed it.
- **`pmn_backfill/`** — 8 meetings recovered from Utah Public Notice (6 Council + 2 RDA)
  that were missing from the repo.
- **`transcripts/`** — 79 auto-generated (ASR) caption tracks from meeting videos (2025+;
  the video archive doesn't go earlier). Not an official record.
- **`campaign_finance/`** — 83 candidate disclosure filings (2021/2023/2025) from the
  EasyVote portal, joined to election results.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
