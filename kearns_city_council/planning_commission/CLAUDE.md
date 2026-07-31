# planning_commission/ — Kearns Planning Commission

Planning Commission minutes (markdown) + extracted votes. **Kearns's own PC, but
MSD-administered** — minuted by Greater Salt Lake **MSD Planning & Development**
("MEETING MINUTE SUMMARY" letterhead, recorder Wendy Gurr). Source: **Utah PMN body
1561**. Same schemas as `meeting_minutes/` (`body=PlanningCommission`).

## Counts (2026-07-16, after the 2019-04-08 promotion)
44 minutes docs · **199 motions** · 2019-03-11 → 2026-06-01 · all born-digital text
(clean; screeners flag zero outliers on every detector). `all_votes.csv` carries a
documented trailing 14th `provenance` column since 2026-07-16 (`minutes` = audited
primary, 197 rows; `pmn_minutes` = PMN-recovered promoted doc, 2 rows — the
2019-04-08 meeting below).

## What makes the PC dataset distinct
- **Land-use cases key `OAM<YYYY>-<NNNNNN>`** (e.g. `OAM2021-000388`) — captured in
  the motion text; this is the cross-body **referral bridge** to the Council (the PC
  issues recommendations "to the Kearns … Council"). See `../db/SCHEMA.md`.
- **Vote style = tally.** Tabular attendance grid, then "Motion by Commissioner X /
  Commissioners voted unanimously in favor." Named individual votes appear only for
  abstentions (4 abstain rows total). Commissioners are often recorded **surname-only**
  (Taylor, Nelson, Hatch, Koester, Wellman, Thomas) — this is how MSD minutes name
  them, not a loss.
- **Meets 1st Monday** (some months cancelled); the Council meets 2nd Monday.

## Honest gap — 2017-2018 (GENUINE, unlike the council 2017-2023 gap)
`minutes_unrecovered.csv` logs 2017-2018 PC meetings as agenda/packet-only, with
approved minutes beginning **2019-03**. The 2026-07-12 audit **confirmed this is
genuine**: 2/2 sampled 2017-2018 PC notices carry Agenda + Packet only, NO "Meeting
Minutes" attachment. So this PC gap is an honest absence — do NOT conflate it with the
COUNCIL 2017-2023 gap, which IS recoverable on PMN (see `../meeting_minutes/CLAUDE.md`).

### 2019-04-08 — FALSE unrecovered row, corrected 2026-07-16
The 2019-04-08 meeting was previously a row in `minutes_unrecovered.csv` — that row
was **FALSE**: the approved minutes WERE on PMN (file 502755, notice 525027) but the
filename `190408_KearnsTPC_Approved.pdf` lacked the "Minutes" token the harvester
keyed on. The doc was recovered by the 2026-07-13 `../pmn_backfill/` build (verified:
MSD letterhead, in-body date, "approved on June 10, 2019"), promoted into this
dataset 2026-07-16 (`provenance=pmn_minutes`, 2 motions incl. the recommendation of
file #30882 — the PF/PI public-facilities zones — to the Township Council), and the
false unrecovered row was **removed** (24 → 23 rows; backup of the pre-removal file in
`_backups/2026-07-16-minutes-promotion/kearns/`). The remaining 23 rows are believed
genuine.

## Minor data-quality note
The `person` layer has a single typo variant — `Thomes` (1 row, 2025-03-03) is
Commissioner **Gray Thomas** (67+ rows). Cosmetic; fold on the next db rebuild.
