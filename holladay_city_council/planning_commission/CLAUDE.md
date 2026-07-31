# planning_commission/ — Holladay Planning Commission vote pipeline

Turns **71 PC minutes** (2020-01-07 → 2026-04-28) into structured motions + votes. TWO
source channels, distinguished per-doc by `minutes_index.csv` `source` and per-vote-row by
the trailing **`provenance`** column in `all_votes.csv`:
- **`source=pmn` / `provenance=minutes`** — 44 docs (2022-03 → 2026-04), the audited PMN
  spine (public body 389, `utah.gov/pmn/files/<id>.pdf`, born-digital).
- **`source=wayback` / `provenance=wayback_minutes`** — **27 docs (2020-01→09 + 2021-01→06)
  recovered from the city's FORMER WordPress site `cityofholladay.com` via the Wayback
  Machine** (PMN never received them) and promoted into this audited layer 2026-07-16 by
  `promote_backfill_minutes.py`. Identity-verified (in-body date == keyed date, PC header,
  sha-unique, minutes-approval chain intact, no draft markers); each md header records the
  exact Wayback snapshot URL. Filter `provenance='minutes'` for a PMN-audited-only cut.

Holladay has its OWN Planning Commission (not the county's); it forwards zoning /
text-amendment / General-Plan recommendations to the City Council.

## Structure — a **7-member** commission (Chair + up to 6 commissioners)
Unlike the 6-max council roll, PC named rolls top out at **7**. No mayor.
`validate_votes.py` uses `MAX_ROLL=7` here.

⚠ **TWO REAL PEOPLE NAMED LAYTON.** Chris Layton serves from 2020 (the data floor);
Howard Layton joins 2020-08; both sit together 2020-08 → 2021-06 and again in 2022
(Chair Howard + Commissioner Chris). When one roll contains BOTH, rows keep the printed
first name (`Chris Layton` / `Howard Layton` — 39+39 rows in 2020–21). When only ONE
Layton is in a roll the row is the bare surname `Layton` per the surname-keyed convention —
resolve those by that meeting's ATTENDANCE header: 2020-01→08 and 2021-05-18/2021-06-15 =
Chris; 2021-02-23 = Howard. Never merge or dedup them (T3.1 Tier-A, 2026-07-12).

⚠ **"Howard Lloyd" is NOT a real commissioner** — the 2021-02-23 first roll (the 4-to-1
Viewmont Street rezone) prints "Commissioner Howard Lloyd-Aye", a clerk conflation of
**Howard Layton** (that meeting's attendance is exactly Bradshaw, Howard Layton, Lloyd,
Mackin, Ricks; the roll otherwise omits Layton; every other roll that night prints
"Commissioner Howard Layton-Aye"). Kept VERBATIM per cardinal rule 2 (ogden-STEPHENS
precedent) — 1 vote row / 1 db person; treat it as Howard Layton in analysis.

## What's here
- `minutes/<year>/<week-monday>/<date>_planning-commission_<pmnFileId|wayback>.md` — 71
  files. PC meets **Tuesday** (modal; a few 2024 meetings ran other weekdays — the folder
  is keyed on that week's Monday regardless).
- `raw/` (44 PMN + 27 `_wayback` PDFs; originals also retained in `../pmn_backfill/raw/`),
  `minutes_index.csv` (`source` = pmn|wayback), `extract_votes.py`, `validate_votes.py`,
  `screen_corpus.py`, `promote_backfill_minutes.py` (the 2026-07-16 promotion, idempotent),
  `roster.csv` (OBSERVED), `all_votes.csv` (13-col standard + documented trailing
  `provenance`). **Validator PASS; screen CLEAN.**
- `minutes_unrecovered.csv` — **62 honest gaps.** ⚠ Holladay posts PC minutes to PMN only
  intermittently; the 2020/2021/2023 sets never reached PMN. The 27 Wayback-recoverable
  docs are now IN this layer; the rest (2020 H2, 2021 H2, all of 2023, the mis-uploaded
  2020-04-07, + recent pending) were never recoverably published on ANY channel
  (PMN / Wayback / live Revize / SuiteOne — see `../pmn_backfill/unrecovered.csv`).

## Vote grammar
All eras use the named-roll trigger `Vote on motion:` — modern surname rolls
(`Commissioner X-Aye; ...`), the early-2022 and the 2020–21 FULL-NAME variant
(`Vote on motion: Chris Layton-Aye, Ann Mackin-Aye, ..., Chair Marianne Ricks-Nay.`).
Two 2020 wayback docs print a clerk-typo period (`Vote on motion. Troy Holbrook-Aye, ...`)
— handled by a guarded ROLL_TRIGGER alternative that requires a Name-Vote token in the
same sentence (0 false hits corpus-wide). Consent/procedural motions (`unanimous consent
of the Commission`) → `names_recorded:false`. Spelling variants folded
(Vilchinski→Vilchinsky, Bank→Banks). A motion amended before any vote carries no roll and
no result — the vote sits on the amending motion (source-faithful, e.g. 2020-01-21 #4).

**328 motions, 1,262 vote rows (1,138 named), 26 contested motions** (11 from the PMN era,
15 from the 2020–21 recovered era — incl. a 3-to-3 failed CUP and two 2020 Weyburn Retreat
split votes). Prose word-form results ("The motion passed 5-to-1.") stay verbatim in
`result`; use `motions_std.csv` for standardized outcome/tallies.
