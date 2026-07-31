# Orem City Council — data repository

Canonical datasets about the **Orem City Council** (Utah County — the county's second city),
modeled on the Salt Lake City reference repo, plus a derived weekly view. Built by the
`build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 130 files 2020–2026) + roll-call votes (all_votes.csv)
planning_commission/  114 PC minutes + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                      (the appointed technical land-use body; recommendations vs final actions)
db/                   NORMALIZED RELATIONAL DATABASE (db/civic.db SQLite + table CSVs) joining ALL bodies'
                      votes by real keys + reconstructed PC→Council referrals. Start here: db/SCHEMA.md
public_comments/      all_comments_clean.csv (95 GENUINE written comments, 2020–21 minutes attachments)
                      + minutes_speaker_log.csv (in-person speaker notes, NOT comments) + AVAILABILITY.md
election_results/      Utah County results filtered to Orem council+mayor races
geo/                  city-limits polygon -> in/out-of-city check (council is at-large, no districts)
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Tuesday)**. Votes + minutes carry the
meeting date; genuine comments carry their meeting date. `build_weeks.py` buckets every
record onto that weekly grid. Elections are point-in-time and NOT in the weekly bundles.

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (3,749 member-vote rows) and
  `public_comments/all_comments_clean.csv` (95 genuine written comments). Do NOT use
  `minutes_speaker_log.csv` (122 in-person paraphrases) as comments.
- **Meeting-level / contextual**: the `weeks/<tuesday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/orem_races.csv`) ↔ votes ↔ comments.
- **By geography**: `geo/address_to_district.py` returns in/out of city limits (at-large —
  no districts).

## Council structure
**Mayor + 6 council members, ALL AT-LARGE (no districts)**, nonpartisan, staggered 4-yr terms
(3 council seats up each odd year). **The Mayor is a full voting member** (every yearly roster
is 7 = 6 council + Mayor). Geo resolves an address to in/out of city limits.

## Data notes / caveats
- **Minutes 2020–2026 (130 files).** Sources: Google Drive archive (2020–early 2021) +
  CivicClerk `publishedFiles` (2021+). **68 files (2022–2026) were image-only scans recovered
  via OCR** (`format=ocr` in `minutes_index.csv`) — slightly lower fidelity. Documented gap:
  **Apr–Jun 2021** council meetings predate both sources (absent).
- **Votes**: 566 motions / 3,749 rows; 49 contested (8.7%). Orem records only Aye/Nay in
  prose (no abstain/recuse/absent vote-block wording). See `meeting_minutes/CLAUDE.md`.
- **Comments**: 95 genuine written comments are verbatim resident comments Orem published as
  **attachments to its 2020–2021 electronic-meeting minutes** (`source=minutes_attached_written`).
  CivicClerk's eComment feature is disabled on all events; sampled agenda packets carried no
  correspondence (verdict in `AVAILABILITY.md`). The `minutes_speaker_log.csv` (122 in-person
  speakers, record-notes NOT comments) was built before the OCR repair, so it **undercounts
  in-person speakers from the 68 repaired 2022–2026 meetings** — regenerate it for full coverage.
- **Elections**: 11 races; 2021 & 2025 have precinct detail, 2019 & 2023 are citywide-only
  (Utah County published no precinct SOVC those years). At-large vote-for-3 model.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **562 motions / 2,997 named-vote rows / 34 contested across 114 meetings**
  (501 motions carry a recorded individual roll call; 61 are tally-only summary minutes). Roster (25
  appointed commissioners) in `planning_commission/roster.csv` (built from attendee headers — no
  election). The `result` string encodes the **recommendation-vs-final-action taxonomy**:
  `Positive/Negative recommendation A:N` (forwarded to Council) vs `A:N Approved/Denied (Final Action)`
  (CUP/site-plan/plat the PC disposes itself — never reaches Council). See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no file number exists in
    Orem) and **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high) tells you how solid each grouping is.
    Five bodies present: Council, PlanningCommission, RDA, MBA, SSLD (Special Service Lighting District).
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — 29 scored links (10 high / 17 medium /
    2 low), all Council←PlanningCommission here (the table also models Council←agency / PC←agency for
    cities with one; Orem's RDA/MBA carry none — no shared addresses). Keyed
    `(primary_application_id, primary_body, related_application_id, related_body, match_method,
    confidence, …)`. **`high`≈exact (address+subject); `medium` spot-check before quoting; `low`
    flagged.** 33% of council land-use items linked; the rest are honestly unlinked (Council→PC plat
    sequences the directional gate rejects, or PC origin pre-2020). Correct mistakes in `db/overrides.csv`
    / `db/referral_overrides.csv` + rebuild (idempotent).
  - **Orem address nuance:** a "shared address" is an approximate **grid intersection**, not a parcel,
    so address-alone is co-location (low), not exact. The PC↔Council join's payoff = the
    technical-vs-political divergence (PC negative rec → Council pass, e.g. the Dunn Rezone). Use
    `v_referral_chain` / `v_project_timeline` / `v_member_record`.
- Build: `python3 db/build_db.py && python3 db/build_referrals.py` (run in that order; both print
  `INTEGRITY: OK`). Never hand-edit `db/civic.db` or the `db/tables/` exports — they are derived.

## Analysis guidance
- **Contested votes (any Nay) are the signal** (49 council, 34 PC); `weeks/<tue>/summary.md` surfaces
  council ones. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).
- **No commissioner served on the Council during 2020–2026** (0 person overlap), unlike some peer cities.

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) walks the Google Drive minutes archive
  (keyless `embeddedfolderview` listing) + the CivicClerk calendar and reports minutes newer than
  each dataset's index max; `--fetch [--dataset <name>]` downloads new PDFs (raw retained), converts
  (image-only scans are flagged for OCR, never faked), appends index rows, and runs extract_votes.py
  + validate_votes.py. CivicClerk publishes NO minutes files for Orem — Drive is the source.
- After any fetch, rebuild: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-05)
Six new source layers (portal family: **CivicClerk OData** `oremut.api.civicclerk.com/v1` + Google
Drive archive + PMN); each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify
existing data. Join to `all_votes.csv`/minutes by `date` (+ `body`). Full write-up:
`EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **221 agenda PDFs stored** + **204 full agenda-packets INDEX-ONLY** (`format=na`,
  live `source_url` + `size_mb`; ~5.8 GB catalogued). CivicClerk docs live in `event.publishedFiles[]`
  (the null `minutesFile`/`agendaFile` slots are a red herring); fetch via
  `Meetings/GetMeetingFileStream(fileId,…)`. Council/PC packet-publishing asymmetry logged.
  Pre-CivicClerk 2020–2021H1 packets are in a Google Drive archive (auth POST needed — deferred, see TODO).
- **`housing_plans/`** — 14 docs. **Orem's MIH element is General Plan Chapter 4 §4.4.2, NOT a standalone
  doc** (2023 GP update; 2018 study; 2025 FrontRunner Station Area Plan/HB 462; state 23/24/25 + SB 34).
- **`ordinances/`** — **100 adopted** (51 land-use, Title 22), re-derived 2026-07-19 over the Q3-refresh
  minutes. **Orem minutes never print an ordinance number** → minutes-derived `within_source` backbone
  (92 within_source / **4 medium** / 4 none). orem.gov WP "Ordinance" posts (`O-YYYY-NNNN`, began mid-2026;
  now 3 posts through 2026-07-14) are the independent source — 4 (`O-2026-0014`…`0017`) now cross-match a
  2026-06-23 council motion → `medium` (the dataset's first corroborated tier; no `high` — no signed PDF
  archive). 4 `none` audit signals: 0012/0013 (06-23 consent agenda), 0018/0019 (07-14, beyond vote coverage).
- **`pmn_backfill/`** — **separate** from audited minutes. Entity 229; bodies Council 734 / PC 642 /
  BoA 643 / RDA 893 / MBA 894 / SSLD 895. **38 dates recovered** (was 39 — a mislabeled `2026-06-10`
  MBA folded into 2025-06-10, see pmn_backfill/CLAUDE.md 2026-07-19) — fills the Apr–Jun 2021 Council gap
  and recovers standalone RDA/MBA minutes. **PROMOTED to `meeting_minutes/all_votes.csv`**
  (`provenance='pmn_minutes'`, via `extract_backfill_votes.py`): **11 RDA/MBA meetings / 29 motions** — the
  5 born-digital ones (2026-07-10) plus **7 OCR-recovered net-new meetings / 17 motions (2026-07-19**, the
  image-only `chars=0` scans, tesseract 300 DPI; parser used `lenient=True` for the standalone path only —
  audited council layer byte-identical). **BoA (3 docs) remains OWNER-GATED** (needs new body plumbing).
  The 2 council packet scans (2026-05) are text-retained, not promoted.
- **`transcripts/`** — **ASR** captions, sample-only (owner policy): 10 sampled / 111 videos mapped on
  YouTube "Orem City" @TheCityofOrem. NEVER authoritative. 2020 = 1 video (COVID); PC video stops 2022-09.
- **`campaign_finance/`** — **91 filings, 23 candidates** self-hosted on `orem.gov/wp-content/uploads/`
  (no third-party portal). **100% election join** (28/28 pairs); no discrepancies. **2019 + 2021
  candidate filings confirmed absent** (paper-only at the recorder). Financial line-items live only in
  `text/` sidecars — structured `contributions.csv` is the separate planned derived layer.
