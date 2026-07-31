# Vineyard City Council — data repository

A Salt Lake City-style civic-data repository for the **Vineyard City Council** (Utah County),
built 2026-06 by the `build-city-data-repo` skill. Council minutes, extracted roll-call
votes, municipal election results, and an in-city-limits geo tool — all as markdown/CSV,
covering **2020–present**. See `CLAUDE.md` for analysis guidance; QA in `VERIFICATION.md`.
Vineyard is a young, fast-growing city, so some recent-year minutes are image-only packets
that couldn't be text-extracted (documented below).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 172 meetings (markdown: 163 council + 9 RDA board) | CivicClerk OData API (text + OCR) + PMN fallback | ✅ 26 "image-only packet" meetings recovered via text-layer `pdftotext`; only **3 unrecoverable** (corrupt media-wrapper files, see `minutes_unrecovered.csv`). 2026-07-02 repair: 3 wrong/stub docs replaced with the real minutes, 1 double-indexed combined doc deduplicated (see `VERIFICATION.md`) |
| Roll-call votes | 2020–2026 | 1,076 motions · 5,240 rows · 51 contested | extracted from minutes | ✅ verified |
| — by body | | Council 5,165 · **RDA 75** | 9 separate RDA board meetings (8 OCR'd) | ✅ `body` column |
| Public comments (genuine written) | — | **0 — not published** (email-only) | n/a | ⚠️ SUBMIT-ONLY (see `public_comments/AVAILABILITY.md`) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 283 in-person speakers | clerk paraphrases in minutes | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 7 races · 37 candidates · 128 precinct rows | Utah County — RCV + plurality | ✅ verified (winners cross-checked) |
| Geo (in-city-limits) | current | city polygon + 9 precincts | UGRC (FIPS 80420 / CountyID 25) | ✅ at-large — no districts |
| Weekly bundles | 2020–2026 | 150 weeks | derived (`build_weeks.py`) | ✅ regenerable |

## Council structure
**Mayor + at-large council, NO districts** — Mayor+4 council through 2025, growing to
**Mayor+5 in 2026** (2024 Prop 10). Mayor Fullmer (2020–2025) was named in roll-calls and
voted (988 rows); from 2026 the clerk names only the councilmembers in roll-call runs, so
Mayor Stratton presides but isn't captured as a named voter (0 rows — not back-filled).
Because there are no districts, the geo tool resolves an address to in/out of city limits.

## Notable: ranked-choice voting
Vineyard used **RCV in 2019, 2021, and 2023** (Utah County's RCV pilot) before reverting to
plurality in 2025. RCV results come from rcvis.com round-by-round tabulations and are
**citywide only** (no precinct breakdown published); `is_winner` reflects the actual
final-round seat winners, not first-choice rank. 2025 plurality (vote-for-3 council) has
precinct detail. The 2021 mayoral figures were corrected to the authoritative rcvis tally
(Fullmer 1,329) over an erroneous web summary. Details in `election_results/CLAUDE.md`.

## Planning Commission + relational database (cross-body analysis)
A second governing body now lives alongside the council in **`planning_commission/`** (same vote
schema; every row `body=PlanningCommission`) — the appointed technical land-use filter that forwards
*recommendations* to the council and takes its own *final actions* (CUP/site-plan that never reach the
council). `db/civic.db` is the **canonical, queryable** form (start at **`db/SCHEMA.md`**) joining
**Planning Commission ↔ City Council ↔ RDA** votes by real keys. Built in two layers, never conflated:
- *Within-body core is EXACT* — project keys **resolved from prose** and **body-scoped** (`0
  applications span >1 body`). Vineyard's **ALL-CAPS, name-poor minutes** defeat the named-project
  extractor, so almost every application is a `singleton`(high) (one motion = one application);
  `name`(medium) barely fires. Totals: 3 bodies · 130 applications · 1,417 motions · 6,857 votes.
  Motions by body: Council 1,040 · PlanningCommission 362 · RDA 15. PC stages: 56 recommendations
  (55 positive / 1 negative) + 306 final actions.
- *Cross-body `referral` is RECONSTRUCTED + scored + GENERALIZED* (`primary_body←related_body`, covering
  Council←PC / Council←RDA / PC←RDA). Vineyard is small and high-consensus, so the layer is small and
  honest: **9 links, all medium/subject, all Council←PlanningCommission** (RDA shares no linkable text →
  0 agency links); 7 of 37 council land-use items linked. Spot-check `medium` before quoting; query via
  `v_referral_chain` / `v_project_timeline`. Build: `python3 db/build_db.py && python3 db/build_referrals.py`.

## Known gaps / caveats
- **Minutes recovery (2024–26 gap years):** of the 29 meetings once logged as "image-only
  packet, unrecoverable," **26 actually carried a text layer** and were recovered locally via
  `pdftotext -layout` (see `meeting_minutes/recover_packets.py`). The remaining **3** (2025-12-10,
  2026-03-10, 2026-05-19) are genuinely unrecoverable — their CivicClerk minutes file is a
  corrupt, truncated `_exppdf.pdf` wrapper containing meeting audio (no document text), broken
  identically on CivicClerk and Utah PMN. Listed in `meeting_minutes/minutes_unrecovered.csv`.
- **RDA minutes:** the 8 separate RDA board meetings added this round were scanned image-only
  PDFs recovered via true OCR (pdftoppm 300dpi + tesseract); their per-member roll-calls are
  lower-fidelity than the born-digital council minutes (tally/result reliable; name lists less so).
- **No published written public comments** — Vineyard takes written comment by email to the
  City Recorder only; nothing is published. `all_comments_clean.csv` is empty; the in-person
  speaker log (283) is a separate, clearly-labeled artifact.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Elections:
  `python3 election_results/clean_elections.py` · Weekly bundles: `python3 build_weeks.py`.
  Raw minutes PDFs are not retained (regenerable from `minutes_index.csv`); `weeks/` is derived.

## Expansion datasets (additive, 2026-07-05)
Six additional source layers (CivicClerk API + Utah Public Notice + YouTube), each documented in
its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 926 agenda + agenda-packet documents catalogued with live URLs (index-only,
  ~7.2 GB on the portal).
- **`housing_plans/`** — the 2019 General Plan (with its Moderate-Income-Housing chapter, updated by
  Ordinance 2022-17) and the state housing compilations.
- **`ordinances/`** — 84 adopted ordinances (18 land-use), linked to the adopting motions.
- **`pmn_backfill/`** — 59 meetings recovered from Utah Public Notice, almost all **Redevelopment
  Agency** minutes the core repo never had.
- **`transcripts/`** — 10 sampled ASR caption tracks + a 47-video map; meeting video exists only for
  the 2019–2020 COVID livestream window. Not an official record.
- **`campaign_finance/`** — 59 candidate disclosure filings (2015–2025), self-hosted (older cycles
  recovered from the Internet Archive); joined 100% to election results for in-scope years.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
