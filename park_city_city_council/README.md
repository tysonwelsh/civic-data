# Park City Council — data repository

A Salt Lake City-style civic-data repository for the **Park City Council** (Summit County, Utah) —
a resort/redevelopment town — built 2026-06 by the `build-city-data-repo` skill. Council minutes,
extracted roll-call votes (incl. RDA & Housing Authority), **genuine published written public
comments**, election results, and an in-city-limits geo tool — all as markdown/CSV, covering
**2020–present**. See `CLAUDE.md` for analysis guidance; independent QA in `VERIFICATION.md` (PASS).

## Coverage

| Dataset | Coverage | Volume | Source | Status |
|---|---|---|---|---|
| Meeting minutes | 2020–2026 | 238 meetings (markdown) | CivicClerk OData (`parkcityut.api.civicclerk.com`), born-digital | ✅ complete, no OCR |
| Roll-call votes | 2020–2026 | 1,557 motions · 7,753 rows · 98 contested | extracted from minutes | ✅ verified (re-extracted 2026-07-02) |
| — by body | | Council 1,493 · **RDA 46 · HA 18** (motions) | in-council Redevelopment Agency + Housing Authority recesses | ✅ `body` column |
| **Public comments (genuine written)** | 2020–2026 | **459 published** (433 verbatim eComment/email in minutes + 26 agenda-packet correspondence) | transcribed verbatim | ✅ **PUBLISHED** (rare!) |
| Minutes speaker log (NOT public comments) | 2020–2026 | 1,055 in-person speakers | clerk paraphrases | ℹ️ `public_comments/minutes_speaker_log.csv` |
| Election results | 2019, 2021, 2023, 2025 | 11 races · 56 candidates · 308 precinct rows | Park City (self-administered) | ✅ verified (winners confirmed) |
| Geo (in-city-limits) | current | city polygon + 13 precincts | UGRC (CountyID 22) | ✅ at-large — no districts |
| Weekly bundles | 2020–2026 | 203 weeks | derived (`build_weeks.py`; rebuilt 2026-07-02 — summaries now include the 459 public comments) | ✅ regenerable |
| **Planning Commission** (pilot) | 2020–2026 | 160 meetings · 602 motions · 790 rows · 30 contested | CivicClerk (cat 27) → `planning_commission/` | ✅ verified (158 recommendations + 120 PC-final actions) |
| **Relational database** | all bodies | normalized SQLite: body·person·meeting·application·motion·vote + 100 cross-body **referrals** | `db/build_db.py` + `db/build_referrals.py` → `db/parkcity.db` | ✅ PK/FK/constraints; EXACT body-scoped core + reconstructed scored referral layer — start at `db/SCHEMA.md` |
| PC↔Council project crosswalk (legacy) | 2020–2026 | 47 projects | heuristic text-join | ⚠️ `planning_commission/project_timeline.csv` — superseded by `db/` `v_referral_chain` / `v_project_timeline` |

## Council structure
**Mayor + 5 all-at-large councilmembers (0 districts; council-manager form).** The **Mayor does NOT
vote except to break a tie** — exactly **2** recorded tie-breaks (Beerman 2020-06-25, Ord 2020-31
Huntsman Estates plat, 2-3 Fail; Worel 2024-08-22, Res 16-2024, 2-3 Fail). Councilmembers who
later became mayor (Worel → mayor 2022–25; Dickey → mayor 2026) vote only in their council years.
Council meets **Thursdays**. Geo is in-city-limits (no districts).

## Public comments — PUBLISHED (the standout in this collection)
Unlike most Utah cities (submit-only / in-minutes-only), **Park City publishes genuine
written/online public comments verbatim**: eComment submissions and emails read into the record are
transcribed word-for-word, in quotes, by name, inside the council minutes (`Jane Doe eComment: "…"`).
`all_comments_clean.csv` holds **459** of these — **433** quoted verbatim in the minutes plus **26**
forwarded resident emails from CivicClerk agenda-packet correspondence (2020–2026), every row traced
to source (3 cross-source duplicates dropped). These are kept strictly separate from the **1,055**
in-person speaker paraphrases in `minutes_speaker_log.csv`. Verdict + method:
`public_comments/AVAILABILITY.md`.

## RDA & Housing Authority (in-council recesses)
Park City runs its **Redevelopment Agency** (Main Street + Lower Park Avenue project areas) and a
**Housing Authority** as in-council recesses; the extractor tags those motions `body=RDA` (46) and
`body=HA` (18) — the "follow the money" / affordable-housing subsets. Filter `body=Council` (1,493)
for council-only analysis.

## Elections (self-administered, at-large)
**Park City self-administers its municipal elections** (Summit County defers); source =
`parkcity.gov` certified canvass PDFs. 11 races for 2019/2021/2023/2025, at-large vote-for-N, **no
RCV**. Headline: the **2025 mayoral race was decided by a 7-vote recount** — Ryan Dickey 1,706 def.
Jack Rubin 1,699 (recount confirmed identical). Winners externally confirmed. See
`election_results/CLAUDE.md`.

## Planning Commission (pilot)
A second governing body lives alongside the council in **`planning_commission/`** (same structure as
`meeting_minutes/`): **160 PC meetings, 602 motions** (2020–2026, CivicClerk categoryId 27, Wednesdays),
with a 14-commissioner roster reconstructed from the minutes (appointed body — no elections). All rows
carry `body=PlanningCommission`. The PC is the **technical land-use filter**; the council is the
**political body** — and they diverge: the PC forwards a *recommendation* (positive/negative) on
plats/MPDs/rezones that the council then votes on, **plus 120 PC-final actions** (CUPs, design review,
steep-slope) that never reach the council at all.

**Trace a project across both bodies** with the **relational database** (`db/parkcity.db`; start at
`db/SCHEMA.md`). Two layers, never conflated: an EXACT, **body-scoped** within-body core (a Council and
a PC "Founder's Place" are distinct applications) plus a reconstructed, scored, **generalized**
`referral` layer — **100 cross-body links** keyed `primary_body←related_body`: Council←PlanningCommission
95, plus Council←HA 3 / Council←RDA 1 / PC←HA 1 (47 high / 30 medium / 23 low). Query it via
`v_referral_chain` / `v_project_timeline`. Example — *Founders Place*: PC unanimous positive
recommendation → Council **fails 2-3**, then passes 4-1 (the fight was affordable-housing *policy* at
council, not land-use). Because RDA/HA titles are boilerplate vs terse ordinance titles, the marquee
agency links (Founder's Place, Sommet Blanc, Studio Crossing, Argent) are carried by
`db/referral_overrides.csv`. The legacy heuristic `planning_commission/project_timeline.csv` is
**superseded** by the DB. See `db/SCHEMA.md` and `planning_commission/CLAUDE.md`.

> Note: the PC subtree is a **pilot** and is **not yet folded into `weeks/`** (which remains
> council-only); the relational `db/` is the cross-body link.

## Regenerate
- Votes: `python3 meeting_minutes/extract_votes.py` · Weekly bundles: `python3 build_weeks.py`
  (`CITY="Park City"`, `MEETING_WEEKDAY=Thursday`). Canonical truth = the dataset CSVs (+ each file's
  CivicClerk `source_url`); raw PDFs not retained; `weeks/` is derived.
- Planning Commission: `python3 planning_commission/extract_votes.py` ·
  Project crosswalk: `python3 planning_commission/build_project_timeline.py`.

## Repairs (2026-07-02)
Post-audit remediation (`_audits/2026-07-02/report.md`, Phase 1.6):
- **Extraction**: `RESULT:`/vote-label regexes made case-sensitive — removed **10 spurious motions**
  (lowercase prose wraps like a public comment's `result: https://www.orlando.gov/...` and roll-call
  attendance "Excused" cells misread as vote blocks; each verified against source). 1,567 → **1,557**
  motions; each removed "motion" individually confirmed as non-motion text.
- **db**: the vote build no longer silently drops rows on the `(motion_id, person_id)` UNIQUE
  constraint. Both **mayoral tie-break votes** are now in `parkcity.db` (`vote.note='Mayor tie-break'`),
  and the 9 source clerk errors (member listed in both AYES and NAYS/ABSTAIN) are resolved explicitly
  via `db/vote_overrides.csv`; any uncovered conflict fails the build. The flat `all_votes.csv` stays
  verbatim/city-faithful.
- **weeks/** rebuilt (summaries previously all said "Public comments: 0"; the 459 comments now appear).
- Originals of every modified file: `_backups/2026-07-02/park_city_city_council/`.

## Expansion datasets (additive, 2026-07-05)
Six additional source layers (CivicClerk API + Revize document tree + Municode + Utah Public
Notice), each documented in its own folder and in `EXPAND_SOURCES_REPORT.md`. None modify the core data.

- **`packets/`** — 942 agenda + agenda-packet documents (agendas stored; the large packets catalogued
  with live URLs, ~30 GB on the portal).
- **`housing_plans/`** — Park City's Five-Year Moderate-Income Housing Plan and the 2025 General Plan
  housing chapter (its deed-restricted affordable-housing program).
- **`ordinances/`** — 260 adopted ordinances (160 land-use), most matched to the adopting vote via a
  public archive of signed ordinance PDFs.
- **`pmn_backfill/`** — 2 recent council meetings recovered from Utah Public Notice (the Redevelopment
  Agency turned out to meet inside council, so no separate RDA minutes exist).
- **`transcripts/`** — a 194-video map of meeting recordings; Park City posts video but publishes no
  captions, so there are no transcripts to extract (Whisper is a proposed future option).
- **`campaign_finance/`** — 126 candidate disclosure filings (2017–2025), self-hosted by the city,
  joined 89% to election results.

The per-file source/citation index (`sources.csv` + `SOURCES.md`) covers all of the above.
