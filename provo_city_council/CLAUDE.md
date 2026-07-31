# Provo City Council — data repository

Canonical datasets about the **Provo Municipal Council**, modeled on the Salt Lake City
reference repo, plus a derived weekly view unifying minutes + votes + comments. Built by
the `build-city-data-repo` skill. Data floor: **2020**.

```
meeting_minutes/      council minutes (markdown, 311 files 2020–2026) + roll-call votes (all_votes.csv)
planning_commission/  PC minutes + votes (all_votes.csv, body=PlanningCommission) + roster.csv
                      (the appointed land-use body; recommendations vs final actions — 2025+ ONLY)
db/                   NORMALIZED RELATIONAL DATABASE (db/civic.db SQLite + table CSVs) joining ALL
                      bodies' votes by real keys + reconstructed Council←RDA referrals. Start: db/SCHEMA.md
public_comments/      all_comments_clean.csv (81 GENUINE written comments from agenda packets)
                      + minutes_speaker_log.csv (in-person speaker notes, NOT comments) + AVAILABILITY.md
election_results/     Utah County results filtered to Provo council+mayor races
geo/                  precinct boundaries + address/point -> council district tool
weeks/                DERIVED weekly bundles tying comments + minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday)
recon.md              map of this city's data sources (provenance)
VERIFICATION.md       independent QA + external election cross-check
```

## The join key
Everything keys to the **council meeting weekday (Tuesday)**. Votes + minutes carry the
meeting date; comments carry their meeting date. `build_weeks.py` buckets every record onto
that weekly grid. Elections are point-in-time (Nov, odd years), NOT in the weekly bundles —
they join by **person + year + district** (normalize names first).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: `meeting_minutes/all_votes.csv` (6,255 member-vote rows) and
  `public_comments/all_comments_clean.csv` (**81 genuine written comments**, source=agenda_packet,
  2020–2022). Do NOT use `minutes_speaker_log.csv` (738 clerk paraphrases) as comments.
- **Meeting-level / contextual**: the `weeks/<tuesday>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/provo_races.csv`) ↔ votes ↔ comments.
- **By geography**: `geo/address_to_district.py` resolves an address to Districts 1–5.

## Council structure
**5 District seats + 2 Citywide (at-large) + separately-elected Mayor.** The Mayor does NOT
vote on council motions (so council votes are 7-member); Citywide members represent everyone.
Geo maps addresses to Districts 1–5 only. Seats are staggered: Cycle A (Citywide I, D2, D5,
Mayor) elected 2021/2025; Cycle B (Citywide II, D1, D3, D4) elected 2019/2023.

## Data notes / caveats
- **Votes**: 1,074 motions; 957 named roll-calls + 117 tally-only (unanimous-consent / most
  work-session votes, recorded `names_recorded:false`, no guessed members). 162 contested.
  12 validation flags are genuine source inconsistencies (printed-tally-vs-names typos,
  Board-of-Canvassers meetings where the Mayor is an 8th voter) — kept verbatim, see
  `meeting_minutes/CLAUDE.md`. One minutes file (2022-01-18) was OCR'd.
- **Comments**: `all_comments_clean.csv` holds **81 genuine public-submitted written
  comments** (residents' own emails/letters bundled into agenda packets, `source=agenda_packet`,
  concentrated on 2020–2021 land-use items; 2022=2; none 2023+). From 2023 on, written input
  moved to the OpenGov "Open City Hall" portal, which is **bot-gated and was never archived**
  (the documented coverage ceiling — see `public_comments/AVAILABILITY.md`). The clerk's
  in-meeting paraphrases of in-person speakers are kept separately in
  `minutes_speaker_log.csv` (738 rows) — meeting-record notes, NOT public-submitted comments.
- **Elections**: 2021 & 2025 have precinct detail; 2019 & 2023 are citywide-only (the county
  published no precinct SOVC those years). Districts 1/3/4 geo derives from the city's GIS
  layer (no precinct election data for those odd-year-B seats).
- **weeks/ is derived** — `python3 build_weeks.py`; never hand-edit.

## Planning Commission + the relational database (cross-body analysis)
- **`planning_commission/all_votes.csv`** — identical schema to council; every row
  `body=PlanningCommission`. **102 motions** (673 member-vote rows) across **26 meetings** · 22
  contested · **12 commissioners** (`roster.csv`). The `result` string encodes the
  **recommendation-vs-final-action taxonomy** (legislative items → an advisory recommendation to the
  Municipal Council; administrative items → the PC's own final action), read from each consolidated
  minutes' *Report of Action*. **IMPORTANT — PC data is 2025+ ONLY** (2025-02-26 → 2026-06-10):
  Provo published no PC minutes for 2020–2024 (a documented city **source gap**, not a parser gap —
  `planning_commission/minutes_unrecovered.csv`). See `planning_commission/CLAUDE.md`.
- **`db/civic.db`** is the canonical queryable form — **prefer it for any cross-body or project-level
  question** (the flat CSVs have no keys). Read **`db/SCHEMA.md`** first. Two layers, never conflated:
  - *Within-body core is EXACT*; project keys are **resolved from prose** and **body-scoped** —
    `0 applications span >1 body` by design. `motion.app_match_method` ∈ `name`(medium, heuristic, 29) /
    `singleton`(high, 399) / `override`(high) tells you how solid each grouping is.
  - *Cross-body `referral` is RECONSTRUCTED + GENERALIZED* — **12 scored links, all medium, all
    Council←RDA** (the RDA/CRA project-area and tax-increment matters the Council ratifies). The table
    also models Council←PC / PC←agency, but there are **0 Council←PC links** here: the PC record is
    **2025+ only** and too short/recent to have produced a subject-matchable Council pair yet. Keyed
    `(primary_application_id, primary_body, related_application_id, related_body, match_method,
    confidence, …)`.
  - **All 12 links are `medium` (subject-only, no address) — spot-check before quoting.** The dominant
    failure mode is **project-area boilerplate** (near-identical interlocal-agreement language across
    different CRAs, e.g. a *Riverwoods* RDA resolution matching a *Center Street* Council ordinance);
    the audited false positives are suppressed in `db/referral_overrides.csv` (precision over recall).
    Only 3% of Council items link; the rest are honestly unlinked. Correct mistakes in
    `db/overrides.csv` / `db/referral_overrides.csv` + rebuild (`python3 db/build_db.py` then
    `python3 db/build_referrals.py`).
  - **Person overlap is mostly hats, not careers:** 12 of the 13 multi-body people are the Council
    sitting as the **RDA board** (same individuals). Only **Jeff Whitlock** also served on the Planning
    Commission. Use `v_referral_chain` / `v_project_timeline` / `v_member_record`.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-03)
Six new source layers; each has its own `CLAUDE.md`. All `validate_dataset.py` PASS; none modify
existing data. Join to `all_votes.csv`/minutes by `date` (+ `body`).

- **`packets/` (LINK INDEX)** — 391 packets, **not stored** (bundled whole-meeting PDFs, ~16 GB
  council). **Two portals:** Council = OnBase `agendas.provo.gov` (documentType=5, CSRF+cookie +
  `DownloadFileBytes`); PC = CivicPlus AgendaCenter (`ViewFile/Agenda/<ref>`). To read one: fetch
  `source_url`, use **vision/OCR**. OnBase gives **no Content-Length** (chunked) → council `size_mb`
  is null (`size_source` column flags it); PC sizes measured. 100% vote-date coverage.
- **`housing_plans/`** — 2023 General Plan + MIH element (GP Appendix B) + state 2023/24/25
  compilations + SB 34. Policy layer behind land-use votes. Docs on `provo.gov` (`provo.org` is 403).
- **`ordinances/`** — Ordinance # → adoption date → adopting motion. **PMN "Notice of Ordinances
  Approved" (body 1600, .docx) is the independent corroborator** → 34 `high` / 20 `medium` / 126
  `within_source` (motion-only, NOT corroborated) / 33 `none`. `adopted_not_in_votes.csv`: 3 genuine
  discrepancies (rest are late-published-minutes lag). 2023 minutes cite no ordinance numbers (gap).
  Join on `(year, int(seq))` — numbering is inconsistently zero-padded.
- **`pmn_backfill/`** — **separate** from the audited minutes (don't treat as canonical without
  review). Bodies 1600/1662. **390 docs recovered** incl. the **whole 2020–2024 PC record** the repo
  lacked, as per-item **ROA** PDFs (`doc_kind` ∈ minutes/summary/roa/roa_supporting/roa_duplicate —
  classify out the duplicates before counting). Content-verified.
- **`transcripts/`** — **ASR** YouTube captions (10; `en-orig`), NEVER authoritative. 740-video map
  in `channel_videos.csv`, continuous 2014+. PC not on YouTube (1 video). 2024 budget/Truth-in-Taxation
  are the top Whisper candidates (not run).
- **`campaign_finance/`** — 41 filings from `provo.gov/1001/Election-Documents` (City Recorder,
  CivicPlus DocumentCenter). Assign cycle/office by **section + roster**, not DocumentCenter View-id
  (non-monotonic) or chronology. 38/41 join; 3 filed-but-withdrew; **2019 gap**. No EasyVote instance.

## Refreshing (incremental updates — Phase 3.3)
- `python3 fetch_new.py --probe` (default; read-only) reports minutes newer than each index —
  council from OnBase (agendas.provo.gov), PC from the CivicPlus AgendaCenter;
  `--fetch [--dataset meeting_minutes|planning_commission]` downloads new PDFs to `<dataset>/raw/`,
  converts to markdown, appends `minutes_index.csv` (+ `fetch_log.csv`), and runs
  extract_votes.py + validate_votes.py. Probe results land in `refresh_probe.json`.
- After a fetch, rebuild: `python3 db/build_db.py` + `python3 db/build_referrals.py`,
  `python3 build_weeks.py`, `python3 ../scripts/normalize_motions.py --all`. OnBase publishes council
  minutes weeks late (link commented out until approved) — probe notes list the pending dates.

## Analysis guidance
- **Contested votes (any Nay/Abstain/Recuse) are the signal**; `weeks/<tue>/summary.md`
  surfaces them. Motion types use the fixed 12-category taxonomy (`meeting_minutes/CLAUDE.md`).
