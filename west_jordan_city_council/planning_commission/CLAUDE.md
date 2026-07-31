# planning_commission/ — West Jordan Planning & Zoning Commission votes (2020–2026)

Motions + votes for the **West Jordan Planning Commission** (a.k.a. Planning & Zoning
Commission), modeled on `../meeting_minutes/`. Data floor **2020**.

```
minutes/<year>/<week-monday>/<date>_<slug>.md   84 minutes files (PrimeGov)
minutes_index.csv                               every file + source_url + format(text|ocr)
extract_votes.py                                the extractor (resumable; --force re-runs all)
votes/<year>/<week>/<date>_<slug>.json          84 per-meeting structured votes
all_votes.csv                                   long format, one row per recorded member-vote
roster.csv                                      commissioner, first_seen, last_seen, n_meetings
validate_votes.py                               standalone re-validation (exit 0 = PASS)
votes/_validation_report.txt                    tally-vs-result + off-roster report
```

Run: `python3 extract_votes.py`, then `python3 extract_backfill_votes.py`
(merges the recovered 2021-2022 PC minutes from `../pmn_backfill/`), then
`python3 validate_votes.py`.

**Coverage extended to 2020-01 (2026-07-17); previously to 2021 (2026-07-10).** The
audited minutes start 2022-07-19; `extract_backfill_votes.py` reuses this parser over
the recovered standalone PC minutes and merges them into `all_votes.csv` with a
**`provenance`** column keyed on each `pmn_backfill/index.csv` `source`:
- `minutes` = audited PrimeGov (307 rows).
- `pmn_minutes` = 28 minutes 2021-04-06→2022-07-05 recovered from Utah Public Notice
  (2026-07-10; 44 named motions / 60 dissent-and-absent rows).
- `citysite_minutes` = **27 standalone PC minutes 2020-01-07→2021-03-16** recovered
  2026-07-17 from the **city's own document host** (`assets.westjordan.utah.gov`,
  discovered via the WordPress `wjc/v1/data-meeting` API — the PrimeGov archive never
  held pre-2022 standalone PC meetings, and PMN carried agendas only for this window).
  40 named motions / 57 rows (10 Nay + 47 Absent). This CLOSES the old "2020-21 had no
  standalone PC meetings" gap — the Commission met on a regular biweekly cadence all of
  2020 (only 2020-03-17 was cancelled, COVID-19).

WJ PC is tally-only, so all recovered rows are dissent/absent only (still no aye rows).
Flows through `db/civic.db` `motion.provenance` + `cities.db`. Merged `all_votes.csv` =
424 rows (307 + 60 + 57).

## Body / title
Every JSON carries `body="PlanningCommission"`; every `all_votes.csv` row has
`body=PlanningCommission`, `title="Planning Commission"`. (The PC is NOT the City
Council/RDA/MBA — separate dataset.)

## The West Jordan PC vote format — TALLY-ONLY
This corpus has **no** "the vote was recorded as follows" roll calls and **no** tabular
roll calls (unlike the City Council minutes). Every motion reads:

> `MOTION: Jay Thomas moved to approve the Minutes from February 21, 2023. The motion`
> `was seconded by Trish Hatch and passed 6-0 in favor.`

So motions carry a **tally** ("passed 6-0 in favor", "failed 3-4") with **no per-member
aye list**. The CARDINAL RULE applies: the affirmative majority is never named, so the
**`aye` list is ALWAYS empty** — we record the tally in `result`, never guessed names.

**The ONLY per-member attributions** are on CONTESTED motions, where the minutes name the
DISSENT side:
- `"... passed 5-1 in favor with Jay Thomas casting the negative vote"` → `nay=[Jay Thomas]`
- `"... failed 3-4 with Commissioners X, Y, Z, and W casting the negative votes"` → 4 nays
- `"... with Commissioner Anderson abstaining"` → `abstain=[Jimmy Anderson]`
- `"... with Commissioner Acker opposed"` / `"with Trish Hatch opposed"` → nay
- named ABSENT/EXCUSED members (`"Emily Gonzalez was absent"`, `"X and Y were absent"`)

These are **partial roll calls**: `names_recorded=true` when ≥1 per-member VOTE
(nay/abstain/recuse) is attributed; the empty `aye` list is expected. Member capture is
restricted to the **outcome sentence** (the ~450 chars after the tally) so later
discussion ("...not opposed to it...") never leaks in as a vote.

`all_votes.csv` therefore contains only **Nay / Abstain / Recuse / Absent** rows (no Aye
rows) — 307 audited rows + 117 recovered (`pmn_minutes`/`citysite_minutes`) = 424 rows.
Aggregate analysis should treat the recorded set as "contested-motion dissents +
attendance", not a full roll call.

## `result` encoding — recommendation vs final action (machine-detectable)
WJ PC **forwards recommendations** to the City Council on rezones / general-plan
amendments / annexations etc., but takes **final action** on site plans, CUPs, temporary
use permits, and preliminary subdivision plats. Encoded EXACTLY:

| class | `result` string | `action_class` field | detection rule |
|-------|-----------------|----------------------|----------------|
| recommendation | `Positive recommendation N:N` / `Negative recommendation N:N` | `pc_recommendation` | motion text has `recommend`, or `forward … (recommendation|council)` |
| final action | `N:N Approved (Final Action)` / `N:N Denied (Final Action)` | `pc_final_action` | not a recommendation, not procedural |
| procedural | `N:N Pass` (or `N:N Fail`) | `procedural` | minutes / nominate / elect / appoint / adjourn / recess / continue / table / postpone / move-the-item-to-date / agenda / schedule |

`N:N` is the printed `ayes:nays` tally. **A FAILED motion is oriented by OUTCOME**: a
failed *approve* → `Denied (Final Action)`; a failed *positive recommendation* →
`Negative recommendation` (e.g. 2023-11-14 Cottages at Parker Place "failed 3-4" →
`Negative recommendation 3:4`). Direction words (`positive`/`negative`,
`approve`/`deny`/`denial`) come from the motion wording.
Rare no-number forms: `Pass (unanimous)`, `Failed (no second)`.

Notes on the rule:
- It keys on the **motion wording**, not a topic taxonomy. WJ takes **final action on
  preliminary subdivision plats** (the motion says "approve", not "forward"), so those are
  `pc_final_action` even though subdivisions ultimately reach Council — matches the
  substring rule and WJ practice.
- `"moving forward"` is excluded from the `forward` trigger (idiom, not a recommendation).
- A motion to **table … as recommended by staff** is procedural (deferral verb wins over
  the incidental "recommended").
- Counts: 119 recommendations, 143 final actions, 123 procedural (385 total).

## OCR-affected meetings
**36 of 84 files are `format=ocr`** (2024-02-20 → 2025-07-15, plus some 2025 early-year),
re-OCR'd from scanned PDFs. (The task brief said 29; the delivered `minutes_index.csv`
actually marks 36 — trust the index.) OCR quirks handled: em/en-dashes and spaced tallies
(`"passed 6- 0 in favor"`) normalized; name variants folded (`Ammon Alien`→Allen,
`Emily Gonzales`→Gonzalez, `Matt Quiney`→Quinney). The expected `7-O` (letter-O for zero)
artifact did **not** occur in this corpus. **OCR parse quality is on par with born-digital**
(0 tally mismatches in both; OCR meetings averaged 5.5 motions/mtg vs 3.9 for text only
because the 2024 OCR era simply had busier agendas).

## Joint sessions & work sessions (no PC votes)
- **4 joint City Council + PC work sessions** (2020-09-29, 2021-03-31, 2021-08-31,
  2022-08-30) are discussion-only — the only formal motion in any of them is a Council
  adjournment moved by a Council member, which is **skipped** (PC body only; movers that
  normalize to council-only names — Jacob, Green, Lamb, McConnehey, Pack, Whitelock,
  Worthen — are excluded). They produce empty-vote JSONs.
- **3 PC work sessions** (2026-03-17, 2026-04-07, 2026-05-19, slug
  `planning-commission-work-session`) are also discussion-only (0 motions). NOTE: the
  delivered `minutes_index.csv` had a bug — the second row of each 2026 dual-meeting date
  pointed at the `-meeting.md` file twice instead of the `-work-session.md` file (which
  existed on disk but was unreferenced). **Fixed** here: those rows now reference the
  `-work-session.md` files with slug `planning-commission-work-session`. The `-meeting.md`
  files on those 3 dates are themselves work-session minutes (near-duplicate scrapes) and
  also carry 0 motions.

## Roster (appointed; no election)
15 distinct commissioners, reconstructed from `PRESENT:` / `COMMISSION:` / `Commissioners:`
attendance headers (wrap-aware; the present roster is the first sentence — "… Jimmy
Anderson. Emily Gonzalez was excused." correctly excludes the excused member).
`first_seen`/`last_seen` are extended to any role appearance (mover/seconder/named
dissent/absent) so a member who was *absent* at their final meetings still spans to that
date; `n_meetings` counts PRESENT appearances only.

**Regenerated over the full merged span (2026-07-19).** `extract_votes.py` builds
roster.csv from the AUDITED minutes only (earliest 2020-09-29); it did NOT see the recovered
2020-01→2022-07 standalone PC minutes, so after the 2026-07-17 backfill merge the roster's
`first_seen`/`n_meetings` were stale and `validate_votes.py` flagged 66 out-of-range rows.
`extract_backfill_votes.py` now **folds the recovered meetings' attendance + role
appearances into roster.csv** (same logic as `extract_votes.py`, 0 date-overlap with the
audited index → no double-count). Effect: the seven 2020–21 commissioners now span from
2020-01-07 (was 2020-09-29) with correct `n_meetings` (e.g. Trish Hatch 58→109, Kent Shelton
27→76, Jay Thomas 72→126). All spans are backed by PRESENT/attendance headers in the
recovered primary minutes — no fabrication. `all_votes.csv` is byte-identical (the 117
recovered vote rows were untouched); only roster.csv changed.

**Cross-checked against the City Council's appointment votes**
(`../meeting_minutes/all_votes.csv`, `motion_type=Appointment`): every roster member has a
matching council "advice and consent" appointment/reappointment resolution. This confirms
two name folds: **Jimmy Anderson = James Anderson** (Res. 24-044, 2024-12-18) and
**Catherine Richardson = Catherine Paquette-Richardson** (Res. 23-010, 2023-04-12).
Spelling note: PC minutes write **Corbin England**; the council appointment writes
**Corban England** (same person; kept as "Corbin England" per the PC source).

## Validation — PASS
`validate_votes.py` (updated 2026-07-19 to know the merged/backfilled file): schema OK
(13 standard cols + the documented optional `provenance`), body/title constants OK, **0
off-roster / 0 out-of-range** across all 424 rows (after the roster regeneration above),
JSON↔CSV reconcile — the votes/ JSON dir is the AUDITED layer only, so it reconciles
against the audited CSV rows (**307 == 307**) with the **117 recovered** backfill rows
counted separately (they have no JSON of their own; see `extract_backfill_votes.py`) — all
`result` strings well-formed, **0 tally mismatches** (named nays fit the printed tally; no
fabricated ayes). See `votes/_validation_report.txt`. Repo-authoritative
`../../scripts/validate_city.py west_jordan_city_council/` is likewise **0 FAIL**.

## Conventions
- Tally-only motions never get guessed member names (`names_recorded=false`, empty lists).
- `motion_type`: Land-Use/Zoning, Appointment, Procedural/Administrative, Other (the four
  that occur for PC business).
- Resumable: `extract_votes.py` skips existing JSONs unless `--force`.
