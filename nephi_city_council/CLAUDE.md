# Nephi City Council — data repository

Canonical datasets about the **Nephi City Council** (Juab County, Utah) — a small rural county seat
(~6,500) — modeled on the Salt Lake City reference repo, plus a derived weekly view. Built by the
`build-city-data-repo` skill. Data floor: **2020**. Independent QA: `VERIFICATION.md`.

```
meeting_minutes/   243 council minutes (markdown, CivicPlus) + extracted motions (all_votes.csv)
public_comments/   all_comments_clean.csv (EMPTY — none published) + minutes_speaker_log.csv
                   (116 in-person speakers, NOT comments) + AVAILABILITY.md
election_results/   Juab County results, Nephi mayor + at-large council (2019/21 unofficial)
geo/                city boundary + 5 precincts + address->in-city-limits tool (at-large, no districts)
weeks/              DERIVED weekly bundles (build_weeks.py: CITY="Nephi", MEETING_WEEKDAY=Tuesday)
recon.md / VERIFICATION.md
```

## The join key
Everything keys to the **council meeting weekday (Tuesday — 1st & 3rd)**. Motions + minutes carry the
meeting date; `build_weeks.py` buckets every record onto that weekly grid. Elections join by
**person + year** (at-large — no district key).

## How to analyze
- **Motions / time-series**: `meeting_minutes/all_votes.csv` (1,170 rows / 979 motions). NOTE Nephi
  records votes as **narrative** ("passed unanimously") — only 51 motions name individual voters, so
  most rows are tally-only (`names_recorded:false`, mover/seconder present, no per-member Aye/Nay).
  Use the `result` + `mover`/`seconder` for most; per-member analysis is only possible on the 46
  named motions + the 22 contested ones.
- **Contested votes** (the signal): 22 motions with a named dissent — overwhelmingly land-use /
  development (plats, rezones, subdivisions, annexations), concentrated in 2020–2021 and driven
  largely by one councilmember (Kent Jones). Two mayoral tie-breaks (2020 beer license; 2021
  biennial budget); one outright failure (2020-03-03 ordinance, 2-3).
- **No genuine public comments** (in-minutes-only); do NOT use `minutes_speaker_log.csv` (116
  in-person paraphrases) as a comments dataset.
- **By person**: join `election_results/nephi_races.csv` winners ↔ motions. **By geography**:
  `geo/address_to_district.py` → inside/outside city limits (no districts).

## Council structure
**Mayor + 5 all-at-large councilmembers (0 districts).** The **Mayor does NOT vote except to break a
tie** (2 tie-breaks in the record). 4-year staggered terms. Meets 1st & 3rd Tuesdays. Two distinct
**Worwood**s — Skip F. (council 2021) vs Travis L. (council 2023+) — keep separate.

## Data notes / caveats
- **`body`**: `Council` (default) / `CRA` (Community Reinvestment Agency). No separate RDA. The CRA
  is modeled as a **`body=` value inside `meeting_minutes/`** (the slc/holladay/millcreek pattern), not
  a separate dataset — Nephi's CRA meets rarely and folds into the council-meeting minutes stream. The
  audited layer holds **1 CRA motion** (2021-07-27 interlocal agreement, AgendaCenter minutes). PMN body
  **5737** was harvested in full 2026-07-19 (10 notices 2016–2023; `pmn_backfill/cra.json`) and recovers
  **nothing new within the 2020 floor**: the 2021-07-27 minutes are already in-repo, and the **2023-12-19
  CRA meeting is agenda-only** (minutes 404 on every channel — logged in
  `meeting_minutes/minutes_unrecovered.csv`; agenda in `packets/`). Pre-floor CRA history (2016–2019) is
  enumerated but not promoted (its only live PMN attachment is a 2019 meeting-schedule doc; the 2017-12-19
  minutes doc is a 404/purge).
- **2024-10-01 is an honest minutes GAP, not a missing meeting** (fixed 2026-07-31). The
  AgendaCenter Minutes slot `_10012024-346` is a **city mis-upload** serving the **2024-09-17**
  minutes verbatim; it had been ingested as a separate meeting, duplicating 10 motions. The
  phantom 2024-10-01 meeting was removed and the real (agendized, later-approved) 2024-10-01
  council meeting is ledgered in `meeting_minutes/minutes_unrecovered.csv` — no minutes document
  exists on AgendaCenter or PMN. `fetch_new.py` skips that slot (`KNOWN_MISUPLOAD_URLS`).
- **Elections**: at-large, no RCV. **2019 & 2021 are unofficial** (Juab's portal only goes back to
  2023; sourced from news archives) — winners solid, exact totals caveated. See `election_results/CLAUDE.md`.
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **331 motions across 70 recovered meetings (63 produced a motion)**;
  roster of **13 appointed commissioners** in `planning_commission/roster.csv` (built from attendee
  headers — no election). The `result` string encodes the **recommendation-vs-final-action taxonomy**:
  recommendations forwarded to Council (**93 Positive / 2 Negative**) vs final actions
  (CUP/site-plan/concept — **236**, never reach Council). **Same narrative-vote caveat:** only 12 of
  331 PC motions name individual voters; the rest are tally-only. See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** (no file number exists in
    Nephi) and **body-scoped** — `0 applications span >1 body` by design. `motion.app_match_method` ∈
    `name`(medium, heuristic) / `singleton`(high) / `override`(high) tells you how solid each grouping
    is. Build totals: **3 bodies · 24 persons · 267 meetings · 229 applications · 1,319 motions · 288
    votes · 18 referrals** (motions: Council 978 · PC 340 · CRA 1).
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — **18 scored links (all medium / subject),
    all Council←PlanningCommission here** (the table also models Council←CRA / PC←CRA for cities with an
    agency; Nephi's single CRA action carries none). Keyed `(primary_application_id, primary_body,
    related_application_id, related_body, match_method, confidence, …)`. **`high`≈exact (address+
    subject); `medium` spot-check before quoting; `low` flagged.** **9% of council land-use items
    linked** — small city → few referrals is honest, not a gap; the rest are correctly unlinked
    (budget/procedural with no land-use counterpart). 2 false positives suppressed in
    `db/referral_overrides.csv`. Correct mistakes there / in `db/overrides.csv` + rebuild.
  - **Nephi is address-poor:** only 1 council + 3 PC apps carry a parsable address and 0 are shared, so
    every link is subject-based (title-token agreement), never address. Use `v_referral_chain` /
    `v_project_timeline`.
  - Build (idempotent): `python3 db/build_db.py` then `python3 db/build_referrals.py` (run AFTER).
- **Narrative voting limits the DB's `vote`/`role` tables** (288 member-votes; 9 PC roles vs 13-person
  roster) — this is the source's nature. Per-member analysis only on the 64 named motions; everything
  else uses mover/seconder + outcome.

## Refreshing (incremental updates — Phase 3.3)

- `python3 fetch_new.py --probe` (default; read-only) reports new AgendaCenter minutes vs the
  indexes for both datasets; `--fetch [--dataset <name>]` downloads them (raw PDFs retained in
  `<dataset>/raw/`), converts, appends index rows, and runs extract_votes.py + validate_votes.py.
  Probe results land in `refresh_probe.json`. PC minutes post months after agendas — 0 new is normal.
- After any fetch, rebuild derived layers: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, and `python3 ../scripts/normalize_motions.py --all` (motions_std).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-05)
Six new source layers (portal family: **CivicPlus CivicEngage `/AgendaCenter`** + PMN + YouTube); each has
its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify existing data. Join to `all_votes.csv`/
minutes by `date` (+ `body`). Full write-up: `EXPAND_SOURCES_REPORT.md`.

- **`packets/`** — **328 agendas STORED** (Council 254, PC 72, **CRA 2**; 12 MB). AgendaCenter has no separate
  packet doc-type, so "packet" = the agenda document. Small enough to store locally.
- **`housing_plans/`** — MIH = **General Plan Element 6 (chapter)**, not standalone. **Nephi is EXEMPT** from
  §10-9a-408 state annual reporting (below the pop threshold) → genuinely absent from state compilations.
- **`ordinances/`** — **103 numbers** (99 adopted, 71 land-use). **Date-as-number** (`Ordinance MM-DD-YYYY`)
  → within_source 91 / **high 5** (PMN-corroborated) / none 7 (was 11 before the 2026-07-20 vote-extractor
  recovery). Of the 4 flagged land-use adoptions: 06-20-2023 + 05-20-2025 now linked; 05-18-2021 (tabled
  by consensus) + 07-12-2022 (adopted 2022-07-19, number-date≠meeting-date) are honest/linkage gaps.
- **`pmn_backfill/`** — **separate** from audited minutes. Entity 216; Council 1788 / PC 1869 (**CRA 5737**).
  **9 recovered** (8 Council + 1 PC) filling late-2025/early-2026 holes; no purge (all files live).
- **`transcripts/`** — **ASR** captions, 4 retrieved / 13-video map. A **new @NephiCity channel began
  streaming May 2026**; everything earlier has no video. NEVER authoritative.
- **`campaign_finance/`** — **27 filings / 43 rows** (all 4 cycles), handwritten scans self-hosted on the city
  DocumentCenter. **92% election join.** Flagged a likely 2023 council primary absent from
  `election_results` — **CONFIRMED + added 2026-07-20**: a real **Sept-5-2023** primary (9 candidates,
  Vote-For-3, top-6 advanced) is now in `election_results` from the OFFICIAL Juab County canvass PDF
  (CF filers "Vanessa Goode"/"Carolyn Louise" = GOATES/FORD, both eliminated).
  Line-items live only in `text/` sidecars — structured `contributions.csv` is the separate planned layer.

**Note:** the **CRA (Community Reinvestment Agency) body** is now built (2026-07-19). It is a `body=CRA`
value inside `meeting_minutes/` (1 audited motion, 2021-07-27), with PMN body **5737** harvested in full
(`pmn_backfill/cra.json`) and the one within-floor gap (2023-12-19, agenda-only) ledgered in
`meeting_minutes/minutes_unrecovered.csv`. See the `body` note under "Data notes / caveats" above.
