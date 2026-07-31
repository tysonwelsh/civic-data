# Town of Alta — data verification

Independent QA of the Town of Alta civic-data repo, built 2026-07-11/12 by the
`build-city-data-repo` skill. Verdict: **PASS on every built dataset, 0 FAIL.**
`scripts/validate_city.py alta_city_council` = **23 PASS / 2 WARN / 0 FAIL** (the 2 WARNs
are the docs written in this pass and a weeks/ staleness flag, both since cleared).

**Read this first — Alta is SPARSE BY DESIGN.** ~380 residents, top of Little Cottonwood
Canyon. The Town Council meets ~monthly (2nd Wednesday, ~12/yr) and the Planning Commission
meets 4th Wednesday **as-needed** (frequently cancelled). Low document counts are the *correct*
record for a town this size, **not** a coverage gap. Every "empty" here (PC 2020–21, public
comments, no cross-body referrals) is an honest zero verified against source.

Method: reconcile the doubly-stored facts (`all_votes.csv` ↔ `minutes_index.csv` ↔ per-meeting
`votes/*.json` ↔ `db/civic.db`) for both bodies; ground-truth 6 random meetings' markdown
against extracted rows (quoting source); confirm the structural claim **the Mayor votes** with a
real roll call; verify the Alta Canyon election exclusion; cross-check the winners against
outside sources; and check coverage against the 2020 floor.

---

## 1. Council — PASS

| Check | Value | Verdict |
|---|---|---|
| Minutes on disk == `minutes_index.csv` rows | 85 == 85 | PASS |
| Per-meeting `votes/*.json` == index | 85 == 85 | PASS |
| Distinct meeting dates (85 docs, one date carries 2 docs) | 84 | PASS |
| `all_votes.csv` data rows | 1,038 | PASS |
| Motions (db, keyed per source file) | **480** | PASS |
| Named-vote motions / tally-only | **168 / 312** | PASS |
| Named member-vote rows (CSV) == db `vote` rows | **726 == 726** (delta +0) | PASS (exact) |
| Named-roll tally vs `result` string agreement | **165/165 = 100.0%** (validator check f) | PASS |
| Roll-call ceiling breaches (>5 voters on a motion) | **0** | PASS |
| Outcome-vs-count inconsistencies | 0 | PASS |
| Date range | **2020-02-12 → 2026-06-17** | PASS (2020 floor) |
| `minutes_unrecovered.csv` | header-only (every PMN council doc recovered) | PASS |

**6 meetings record no formal motions** — verified honest against source: `2021-01-05`,
`2024-01-11`, `2024-03-13`, `2025-01-09`, `2025-04-24`, `2025-09-04` (retreats / strategic-
planning / agenda-only work sessions). These are the 84 distinct index dates minus the 78 with
votes. Not an extraction miss.

The db reconciles exactly: **527 motions** (480 Council + 47 PC) · **726 votes** · 18 `person`
rows · 9 `role` rows. The build aborts if any named CSV row fails to land in `vote`; it did not.

## 2. Planning Commission — PASS

| Check | Value | Verdict |
|---|---|---|
| Minutes == index == JSON | 17 == 17 == 17 | PASS |
| `all_votes.csv` rows / motions | 47 / 47 | PASS |
| Named member rows | **0** (all tally-only unanimous consent — a **source** ceiling, not a loss) | PASS |
| Contested | 0 | PASS |
| Date range | **2022-06-02 → 2025-12-17** | PASS |
| Docs 2020–2021 | **0** | PASS (genuine — see below) |

**PC has NO 2020–2021 minutes — this is an honest gap, not missing data.** Alta's PC is an
as-needed Land Use Authority; it produced no minutes in 2020–2021 (no land-use business before
it). The record is thin (17 docs over 3.5 years) but real, and every recorded PC vote is
narrative "unanimous consent of the commission" → tally-only by source (no per-member roll call
is ever printed). Spot-check (2023-07-18): 6 motions, movers named (Niermeyer, Askins, Nepstad),
every `member` blank, matching the source verbatim.

## 3. THE MAYOR VOTES — CONFIRMED against a real roll call

Alta uses Utah's **Town form**: the Mayor is an ordinary voting member. A full council roll call
tops out at **5** (Mayor + 4 at-large councilmembers). Quoted from the source minutes
(`meeting_minutes/minutes/2025/2025-04-07/2025-04-09_2025_4_9_town_council_meeting_minutes_approved.md`,
Resolution 2025-R-6 appointing Paul Moxley to the Planning Commission):

> **MOTION:** Dan Schilling motioned to approve Resolution 2025-R-6. Elise Morgan seconded.
> **ROLL CALL VOTE: Mayor Bourke — yes,** Councilmember Schilling — yes, Councilmember Morgan —
> yes, Councilmember Byrne — yes, Councilmember Anctil — yes, Resolution 2025-R-6 … was
> unanimously approved.

That is a **5-member roll call in which Mayor Bourke casts a counted vote** — not a tie-break.
Corroborated on a **contested** motion (`2022-10-12`, Resolution 2022-R-18 fee schedule):

> **VOTE:** The Mayor, Carolyn Anctil, and Sheridan Davis voted I in favor. John Byrne and Elise
> Morgan voted nay. Resolution 2022-R-18 as amended passes 3:2.

The extracted `all_votes.csv` mirrors this exactly (motion 3, 2022-10-12: John Byrne = Nay, Elise
Morgan = Nay, `result = APPROVED (3-2)`; the Mayor is on the prevailing side). Across the corpus
**Roger Bourke has 156 member-vote rows** (the top voter), max roll size = **5**, **0** ceiling
breaches. The Mayor is a full voter, confirmed. (Mayor turnover: **Harris Sondak** was Mayor in
2020; **Roger Bourke** from 2021 — Bourke sat as a councilmember in 2020. Both mayors vote, so
tallies are unaffected.)

## 4. Alta Canyon exclusion — CONFIRMED

`grep -i canyon election_results/*.csv` → **0 rows.** `election_results/alta_races.csv` contains
**only genuine Town-of-Alta contests**: 2021 `Town of Alta Council At-Large` + `Town of Alta
Mayor`, and 2023 `Town of Alta Council At-Large`. The **Alta Canyon Recreation Special Service
District** contests (`ALTA CANYON REC …`, a Sandy/Cottonwood-Heights-area rec district, NOT the
Town of Alta) are correctly excluded. PASS.

## 5. Election cross-check (outside sources, browser-UA, 2026-07-12)

| Contest | Repo record | Outside source | Verdict |
|---|---|---|---|
| 2021 Mayor | ROGER BOURKE (uncontested after Harris Sondak withdrew; ~60) | Deseret News / ABC4 / town canvass: Bourke unopposed, ~60 | ✅ match |
| 2021 Council At-Large (2 seats) | Winners **JOHN BYRNE (~53) & CAROLYN ANCTIL (~45)**; Margaret E. Bourke (~36) did **not** win | Web search of 2021 results: John Byrne 53, Carolyn Anctil 45, Margaret Bourke 36 (loser) | ✅ exact |
| 2023 Council At-Large (2 seats) | Winners **ELISE MORGAN (66) & DAN SCHILLING (51)**; runner-up SHERIDAN J. DAVIS (42) | KSL / state results: Morgan & Schilling win, Davis 3rd | ✅ winner set + order match |

**Note on suppressed 2021 tallies (honest).** The Salt Lake County SOVC **suppressed** the 2021
Alta candidate tallies (turnout below the privacy floor for a ~380-person town). `alta_races.csv`
therefore leaves the 2021 vote counts blank and marks the winners **external/unofficial** in its
`note` column, with the exact external cross-check embedded. The 2023 tallies were published and
are county-certified. Vote-count minor variances seen in some news snippets (e.g. 55/40/39 vs the
certified 66/51/42 for 2023) are election-night-vs-final differences; the **winner set and order
match**. The town's own current-officers page (Bourke, Anctil, Byrne, Morgan, Schilling)
corroborates the roster.

## 6. Coverage vs the 2020 floor

- **Council:** 2020-02-12 → 2026-06-17, continuous ~monthly cadence. Alta has operated since 1970;
  2020 is a normal collection floor (minutes exist earlier but are out of scope). No unrecovered
  council meetings.
- **PC:** 2022-06 → 2025-12, **none 2020–2021** (genuine — the as-needed PC produced no minutes
  then). Thin but complete against PMN body 1602.
- **Public comments:** honest zero — Alta publishes no written-comment archive (submit-only /
  in-person; paraphrased inline in minutes). `all_comments_clean.csv` is header-only by design.
  See `public_comments/AVAILABILITY.md`.
- **Geo:** at-large town → **no council districts**; the geo layer is town-boundary membership
  only (UGRC `NAME='Alta'`, CountyID 18). No address→district tool is needed or claimed.

## 7. Ground-truth spot-checks (markdown ↔ extracted rows)

| Meeting | Source says | `all_votes.csv` says | Verdict |
|---|---|---|---|
| 2025-04-09 R-2025-R-6 | 5-member roll, all yes incl. Mayor Bourke | motion 1, Roger Bourke = Aye, APPROVED | ✅ |
| 2022-10-12 noise ord. 2022-O-5 | "Carolyn Anctil voted nay" (4-1) | motion 2, Anctil = Nay, APPROVED (4-1) | ✅ |
| 2022-10-12 fee sched. 2022-R-18 | Byrne + Morgan nay, "passes 3:2"; parser takes MAIN vote not AMENDMENT VOTE | motion 3, Byrne = Nay, Morgan = Nay, APPROVED (3-2) | ✅ |
| 2020-02-12 (first meeting) | Resolution + consent + adjourn | 3 motions, types match | ✅ |
| 2023-07-18 (PC) | 6 narrative unanimous-consent motions | 6 tally-only rows, movers named, members blank | ✅ |
| 2026-05-13 | multiple named roll calls | rows present, ≤5 voters each | ✅ |

## 8. Known minor issues (non-blocking; do NOT affect vote reconciliation)

- **~~3 malformed `db/person` rows~~ — RESOLVED (2026-07-19).** The earlier
  mover/seconder text artifacts (`Contract. He`, `Council. Davis`, `Was`, from garbled
  lines like the OCR'd 2020-02-12 "Council. Member Davis. moved") no longer mint phantom
  persons: the extractor's `known_member` roster-guard + STOP-word set now rejects any
  mover/seconder that does not resolve to a harvested council name (verified — 2020-02-12
  now extracts mover `Sheridan Davis` / seconder `Margaret Bourke`). `db/person` holds
  **16 clean names, 0 junk rows** (confirmed at rebuild). The real council voters in `role`
  match `meeting_minutes/roster.csv`.
- **`db/referral` = 0 links.** Correct: the PC is tiny (47 motions, mostly CUPs) and Alta's
  council motions are resolution/ordinance-keyed with no shared land-use case key, so there is no
  reconstructable PC→Council referral. An honest empty, not a build failure.
- **21 council motions labelled `RECORDED (no vote line)`** — parliamentary main-motions whose
  vote is cast later via a "called the question" / amendment sequence. Faithful to source, not a
  miss.
- **36 council + 13 PC minutes are `format=ocr`** (image-only scans); the rest are born-digital
  `pdf-text`. The corpus screener flagged image-only files for OCR and found no fabricated names.

## 9. Validator + derived layers

`scripts/validate_city.py alta_city_council` → **23 PASS / 0 FAIL** (checks a–m: layout, 13-col
schema both bodies, vocabulary, index integrity, source resolution, tally match 165/165, std
contract, db exact reconciliation 726==726, weeks sum 1038==flat, validate_votes clean,
crosswalks complete, elections 25-col superset). `weeks/` was regenerated in this pass (82
bundles; vote weeks sum 1,038 == flat total). `weeks/` and `db/` are DERIVED — regenerate with
`build_weeks.py` / `db/build_db.py`, never hand-edit.

```
Verdict: PASS — every built dataset reconciles; the Mayor votes (max roll 5) is confirmed at
source; the Alta Canyon decoys are excluded; winners cross-check to outside sources; and the
sparse cadence + PC 2020–21 emptiness + honest-zero comments are correct for a ~380-resident town.
```
