# planning_commission/ — White City Planning Commission

Planning Commission minutes (markdown) + extracted votes. **White City's own PC, but
MSD-administered** — minuted by Greater Salt Lake **MSD Planning & Development Services**
("MEETING MINUTE SUMMARY" letterhead, recorder Wendy Gurr; the Kearns-PC document family).
Source: **Utah PMN body 5879 ONLY** (the city's Streamline site publishes no PC minutes) —
recovered via `../pmn_backfill/` and promoted 2026-07-16. Same schemas as
`../meeting_minutes/` (`body=PlanningCommission`) **plus the trailing `provenance` column:
every row is `pmn_minutes`** (there is no Streamline-published PC minutes source at all).

## Counts (2026-07-16)
22 minutes docs · **106 motions / 106 vote rows** · 2019-01-29 → 2025-05-20 · all
born-digital text. 8 observed commissioners (`roster.csv`). **1 contested motion**
(Weston Millen Abstain, 2021-05-25 minutes approval) — the only named vote row.

## The recording ceiling (respect it)
- **MSD narrative-tally style**: a motion prints mover + seconder + a prose vote line
  ("Commissioners voted unanimous(ly) in favor (of commissioners present)"), never a
  per-member roll. **67 motions carry a printed outcome; all passed.** A unanimous roll
  emits ONE placeholder row (blank `member`/`vote`) — a source limit, not member behavior.
- **39 motions have an EMPTY `result`** — honest NULL, two classes: (a) inline procedural
  motions (hearing open/close, adjourn, business-meeting transitions) for which the clerk
  never prints an outcome; (b) one 2019-06-25 block whose Motion by:/2nd by:/Vote: fields
  the clerk left blank. **An empty result is "no outcome printed", NOT a failure.**
  (`motions_std.csv` classifies these `outcome=unknown` — PC outcome coverage is 63.2%
  by source design.)
- Commissioners are resolved to **full names** from the in-document attendance grids
  (e.g. `Millen` → Weston Millen). "**Hunsaker**" is a recurring clerk spelling of
  **Christopher Huntzinger** (the same documents' attendance grids list only Huntzinger)
  — folded by the extractor's alias table, documented here.

## What makes the PC dataset distinct
- **Land-use cases key `OAM<YYYY>-<NNNNNN>`** (MSD case numbers; also `EXP`/`WVR` keys
  and 2019-era SLCo `file #NNNNN` numbers) — captured verbatim in the motion text; this
  is the cross-body **referral bridge** to the Council (the PC "recommends … to the
  White City (Metro Township) Council"). The current `db/build_referrals.py` run links
  0 PC→Council pairs (conservative subject matcher; the Council side adopts by
  resolution/ordinance number) — treat PC recommendations as findable by OAM key +
  subject, not by the referral table.
- 20 Land-Use/Zoning motions: IADU ordinance (OAM2021-000272), floodplain ordinance
  (OAM2021-000347), MIH plan amendments, HB476/Title 18 subdivision compliance
  (OAM2024-001257), land-use fee schedule (OAM2025-001375), landscape-contractor-yard
  text amendment (OAM2025-001340), special exceptions (EXP…), a fence waiver (WVR…).
- Meets ~monthly on paper, but **cancels often** (2024–2026 notices are mostly
  `*_Cancelled.pdf`) and the minutes series is **sporadic** — see `AVAILABILITY.md` +
  `minutes_unrecovered.csv` (29 noticed dates with no minutes ever posted).

## Regenerate
`python3 extract_votes.py [--force]` then `python3 validate_votes.py` (from this
directory; PASS required). Then rebuild `../db/`, `../weeks/`, and
`scripts/normalize_motions.py white_city`. Canonical truth = these CSVs + the minutes
markdown + `raw/` originals (+ `../pmn_backfill/raw/` fetch provenance); never
hand-edit — corrections go through documented override files.
