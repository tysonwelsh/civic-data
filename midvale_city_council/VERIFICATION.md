# Midvale City — data verification

Independent QA of the Midvale City Council / RDA / Planning-Commission repo, run
**2026-07-12** against the built artifacts (flat CSVs, per-meeting JSON, minutes
markdown, `db/civic.db`, elections). Method: reconcile every doubly-stored fact
(`all_votes.csv` ⇄ `minutes_index.csv` ⇄ per-meeting `votes/*.json` ⇄ `db/civic.db`),
ground-truth a random sample of extracted rows against the source minutes (including an
OCR'd 2020–2021 council doc and an RDA-tagged motion), confirm the mayor-votes-only-on-ties
ceiling and the Gettel council→mayor transition, check date coverage against the 2020 floor,
and cross-check election winners against outside sources with a browser UA. **No canonical
CSV or minutes file was mutated.**

> ⚠ **Counts below the 2026-07-12/07-16 sections predate the 2026-07-31 phantom-meeting
> removal** (4 misdated documents, −16 motions / −62 flat vote rows / −4 meetings). Current
> totals and the full evidence are in **Addendum 2026-07-31** at the end of this file; the
> earlier sections are kept verbatim as dated audit records.

Grades: **PASS** = reconciles / matches source. Documented defects are listed and were
verified to be already logged in the root `TODO.md`, not new findings.

---

## Summary scorecard

| Dataset | Grade | One-line basis |
|---|---|---|
| Council + RDA votes | **PASS** | 151 index docs ⇄ 4,019 CSV rows ⇄ JSON; body split Council 3,896 + RDA 123; named-roll spot-checks correct |
| Planning Commission votes | **PASS** | 103 index docs (1 unrecoverable, logged) ⇄ 1,994 CSV rows; 669 motions |
| Mayor tie-break ceiling | **PASS** | Max ordinary council roll = 5; the one mayoral vote in the record (Hale, 2020-05-05) is a genuine 2–2 tie-break |
| Gettel council→mayor transition | **PASS** | Votes as councilmember through 2024-12-10; appointed mayor Jan 2025; confirmed by outside sources |
| OCR 2020–2021 council docs | **PASS (with OCR seam)** | 30 council + 16 PC `format=ocr`; sampled OCR doc reconciles; minor OCR name-garble quantified |
| RDA in-session body | **PASS** | `body=RDA` motions are real in-meeting recesses; source quoted |
| `db/civic.db` reconciliation | **PASS** | 5,086 named CSV vote rows == 5,086 db `vote` rows, exact by body |
| Elections cross-check | **PASS** | 2021 / 2023 / 2025 winners match Midvale Journal / KSL / Salt Lake Tribune |
| Date coverage vs 2020 floor | **PASS** | Council 2020-01-07 → 2026-06-16; PC 2020-01-08 → 2026-06-24 |
| Public comments | **PASS (honest-empty)** | Submit-only; `all_comments_clean.csv` is header-only by design |

**Verdict: SHIP.** One low-severity documented defect (a same-day cross-document duplicate
roll call) and one OCR-era `result`-string mis-tally, both below, neither blocking.

---

## (a) Council + RDA votes — PASS

- `meeting_minutes/minutes_index.csv`: **151** documents (150 distinct dates; 2025-08-19
  carries two docs — see defect D1), `format`: **121 text + 30 ocr**.
- `meeting_minutes/all_votes.csv`: **4,019** rows over **1,347** distinct motions.
  Body split: **Council 3,896 + RDA 123** rows. Every vote-row date is present in the index
  (0 orphans). Per-meeting `votes/*.json` intermediates present and consistent.
- **8 indexed council meetings carry 0 votes** — all genuinely vote-less sessions (budget
  retreats/meetings, legislative breakfasts, one procedural regular): 2020-04-14, 2021-04-15,
  2022-03-31, 2022-12-01, 2023-11-30, 2024-01-16, 2024-12-11, 2025-12-11. Not extraction
  misses.
- Named-roll spot-checks (source markdown ⇄ CSV), all correct:
  - **2021-01-05** (OCR council doc, `CC Minutes 152021.pdf`): header block intact
    (`Format: ocr`, Revize source URL, raw pointer); roll calls parse cleanly despite garbled
    body text (e.g. "The voting was as follows: Council Member Quinn Sperry Aye … Council
    Member Heidi Robinson Aye … The motion passed unanimously").
  - **RDA-tagged motion 2021-11-16 m9** — source: "Consider Ordinance No. 2021-O-22 An
    Ordinance Approving and Adopting the Amendments made to the Project Area Plans for the
    Bingham Junction RDA, Jordan Bluffs RDA, and Main Street CDA"; CSV records it under
    `body=RDA`, `5-0 Pass`. The Council recesses in-session into the Redevelopment Agency and
    reconvenes — a real second body in one minutes doc, correctly walked.

## (b) Planning Commission votes — PASS

- `planning_commission/minutes_index.csv`: **103** documents (**87 text + 16 ocr**);
  `all_votes.csv`: **1,994** rows / **669** motions, all `body=PlanningCommission`.
- **1 unrecoverable meeting** logged honestly, not stubbed:
  `planning_commission/minutes_unrecovered.csv` = **2024-08-28** (corrupt/blank source scan).
- PC roll sizes range 2–7 (the P&Z Commission seats up to 7 members) — **not** subject to the
  council mayor-ceiling. Spot-checks of named/tabular rolls reconcile.

## (c) Mayor-votes-only-on-ties ceiling — PASS

- Midvale uses Utah's **six-member council form**: 5 district members legislate; the Mayor
  presides and **votes only to break a tie**. Max ordinary council roll = **5**.
- Roll-size distribution over all council motions: **{5:603, 4:70, 3:16, 2:6, 1:1}** plus a
  single **10** — the 10 is the known duplicate (D1), not a 6th voter.
- **The one mayoral vote in the entire record is a genuine tie-break.** 2020-05-05 m14, source
  verbatim: a 2–2 split (Sperry Aye, Glover Aye, Robinson No, Gettel No, Brown Absent) then
  "**Mayor Robert Hale … Aye. Mayor Hale voted to break the tie vote. The motion passed 3-2
  in favor.**" Robert Hale (Mayor 2018–2021) appears in **exactly one** vote row, on this
  motion. This is the ceiling working as designed.
  - **Defect D2 (result-string only):** the CSV/db `result` for this motion reads
    **"2-2 Fail"** (the pre-tie-break tally), whereas the source's stated outcome after the
    mayoral tie-break is **"passed 3-2."** The six member-level vote rows are correct
    (including Hale's Aye); only the derived tally string / pass-flag is wrong. This is an
    OCR-era extraction edge (the extractor summed the roll before the mayor's tie-breaker).
    Low severity, single motion — flagged for a `db/vote_overrides.csv` correction (see
    Issues). Not fixed in place per the no-mutation rule.

## (d) Gettel council→mayor transition — PASS

The roster genuinely changes across a council→mayor transition, and the vote data models it
correctly:

- **Dustin Gettel** votes as a **councilmember (D5)** from 2020-01-07 through **2024-12-10**
  (458 rows) — legitimate councilmember votes.
- From **2025-01-07**, D5 is **Denece Mikolash** (200 rows, 2025→2026); Gettel casts **no**
  councilmember votes after 2024.
- Outside sources explain and confirm the seam: Mayor **Marcus Stevenson** (elected 2021)
  **abruptly resigned**; the Council **appointed Councilman Gettel as mayor** (sworn in
  2025-01-03, per Midvale Journal), vacating D5; **Mikolash was appointed to D5 on 2025-01-07**
  and then **won the seat outright in Nov 2025**; **Gettel won the 2025 mayoral election**
  (60.89%). "Mayor Stevenson" is the 2022–2024 mayor. This matches the "council→mayor" pattern
  the build brief flagged (cf. Herriman's Hales).
- Gettel never appears as a 6th voter or in a mayoral role in the vote rows — consistent with
  the tie-break ceiling.

## (e) OCR 2020–2021 seam — PASS (documented limitation)

- **30 council + 16 PC** documents are `format=ocr` (2020–2021 council minutes are scanned
  image PDFs; a handful of later scans too). 2022+ is born-digital text; 2020 also has 9
  born-digital `.docx` originals.
- The OCR is good enough that roll calls parse, but it leaves a small residue of **garbled
  member-name variants** in the OCR-era rows: `Dustin Geftel`, `Dustin Gette`, `Oustin
  Gettel`, `Pau! Glover`, and two OCR line-bleed artifacts (`Paul Glover Aye Council Member
  Quinn Sperry`, `Quinn Sperry Aye Council Member Paul Glover`) — **~13 of 3,366 named council
  rows (~0.4%)**; the db likewise carries `Hale called` / `Paul Gettel` person artifacts.
  These are OCR-seam noise, not fabrication; canonical names dominate. Documented here and in
  `meeting_minutes/CLAUDE.md`; a future OCR-name-normalization pass or PMN born-digital
  upgrade would clear them.

## (f) `db/civic.db` — PASS (exact reconciliation)

- Named CSV vote rows == db `vote` rows, **exact by body**:
  Council **3,256**, RDA **110**, PlanningCommission **1,720** → **5,086 == 5,086**.
- `motion` **2,020** (council_vote 1,316 · pc_final_action 465 · pc_recommendation 204 ·
  rda_vote 35); `meeting` 265; `person` 47; `referral` 101 (**40 high / 44 medium / 17 low**).
- **The known duplicate collapses correctly at the motion level.** 2025-08-19 consent motion
  `motion_id 1122` has **exactly 5** votes (not 10); **0** person appears twice within any
  motion. See `db/SCHEMA.md`.

## (g) Elections cross-check — PASS (browser UA, outside sources)

`election_results/midvale_races.csv` winners vs independent reporting/canvass:

| Year | Race | File winner | Outside source | Match |
|---|---|---|---|---|
| 2021 | Mayor | MARCUS STEVENSON (RCV final) | Midvale Journal, ABC4 — Stevenson defeats incumbent Hale | ✅ |
| 2021 | Council D5 | DUSTIN GETTEL | Midvale Journal (Gettel over Wayne Sharp) | ✅ |
| 2021 | Council D4 | BRYANT S. BROWN (unopposed) | Midvale Journal (Brown re-elected) | ✅ |
| 2023 | Council D1 | BONNIE BILLINGS | SL Tribune voter guide; she is a sitting member | ✅ |
| 2023 | Council D3 | HEIDI ROBINSON | sitting member | ✅ |
| 2025 | Mayor | DUSTIN GETTEL (60.89%) | SL Tribune / Midvale Journal (Gettel ~62% over Boyer, Fair) | ✅ |
| 2025 | Council D5 | DENECE MIKOLASH | Midvale Journal (Mikolash v. Jamie Steverson) | ✅ |
| 2025 | Council D4 | BRYANT BROWN | Midvale Journal | ✅ |

- **RCV note carried correctly:** 2021 Mayor and 2023 D3 are RCV pilot years — the file's
  `winner_pct`/`margin` are **first-choice** (round 1), and the `note` column says so; the
  `winner` is the canvassed **RCV-final** winner (Stevenson 2021, Robinson 2023). No
  mis-statement.
- **2019 general** (Sperry D1 / Glover D2 / Robinson D3) was recovered from the raw SOVC and
  is present. A **2023 bond question** is intentionally excluded from the council/mayor races
  file (documented in SOURCES.md).

## (h) Date coverage vs the 2020 floor — PASS

Council **2020-01-07 → 2026-06-16** (years 2020–2026 all populated, 472–670 vote rows each);
PC **2020-01-08 → 2026-06-24**. Midvale incorporated 1909, so 2020 is a normal analysis floor,
not an incorporation edge. No interior year gaps.

## (i) Public comments — PASS (honest-empty)

Midvale publishes no standalone written-comment archive; public comment is in-person /
submit-only. `public_comments/all_comments_clean.csv` is **header-only by design**; the
verdict is documented in `public_comments/AVAILABILITY.md` and `public_comments/CLAUDE.md`.
A legitimate honest zero, not a gap.

---

## Documented defects (already in root `TODO.md` — not new finds)

- **D1 — one duplicated roll-call motion (low severity).** 2025-08-19 carries **two indexed
  minutes docs** — the *City Council Regular Meeting* and the *City Council Truth In Taxation*
  meeting — and **both print the same 5-0 "Approve the Consent Agenda" roll call**, so the flat
  CSV holds it from both files (**10 rows for 5 people**). The **outcome is correct** and the
  db represents each source meeting separately with a clean 5-vote roll (`motion_id 1122` = 5
  votes; no within-motion person duplicate). Fix (deferred): dedup identical (member,vote)
  across same-day duplicate source docs in the extractor, re-extract. 1 of ~675 council
  motions affected.

## Issues surfaced by this audit (for the fix queue)

- **D2 — mayoral-tie-break `result` mis-tally (2020-05-05 m14).** `result`="2-2 Fail" but the
  source states the motion **passed 3-2** after Mayor Hale's tie-break; member rows are
  correct. Recommend a `db/vote_overrides.csv` (or extractor) correction so the derived
  tally/pass-flag matches the source; add to root `TODO.md`.
- **OCR name-garble residue (~13 council rows).** Fold the OCR-era variants
  (`Geftel`/`Gette`/`Oustin Gettel`/`Pau! Glover` + two line-bleed strings) into the canonical
  name map on the next OCR-normalization or PMN born-digital upgrade.

*Addenda convention: append dated notes below whenever the data is repaired or re-audited.*

---

## Addendum 2026-07-16 — PMN minutes promotion (pmn_backfill → vote layer)

**What:** the 25 PMN-recovered docs (14 council-session dates the Revize portal genuinely
lacked, incl. the 2024 Feb/Mar/May/Jun cluster and the recurring 3rd-Tuesday January
meetings) were promoted into `meeting_minutes/all_votes.csv` with a documented trailing
**`provenance`** column (`minutes` audited / `pmn_minutes` recovered). Driver:
`meeting_minutes/extract_backfill_votes.py` (sidecar-merge pattern per
ogden/vineyard/orem/south_jordan/herriman); standalone RDA/MBA docs parsed with an
agency-roles regex variant ("Board Member"/"Chair"). Backups of every modified canonical
file: `_backups/2026-07-16-minutes-promotion/midvale/`.

**Identity verification (every doc):** internal meeting-date/title headers checked against
the PMN label; recorder "Approved this …" blocks confirm all are APPROVED minutes (no
drafts); all 14 dates confirmed absent from `minutes_index.csv`; recovered CC docs contain
no embedded in-session RDA sections (no double-ingest with the standalone RDA companions);
an automatic (date, body) collision guard aborts on any overlap with audited meetings.

**One PMN label lie found and corrected:** the doc filed as "RDA Minutes 1-17-2023" contains
the 2023-01-17 RDA *agenda* + the minutes **of the 2022-12-06 RDA meeting** (page headers
"December 6, 2022"; approval "this 17th day of January, 2023"; content = Resolutions
2022-15/16/17RDA). Merged under date=2022-12-06 (the audited 2022-12-06 CC doc holds only
Council motions — no overlap). The 2023-01-17 RDA session's own minutes are logged in
`meeting_minutes/minutes_unrecovered.csv` (the one remaining council-family gap).

**Result:** +179 motions / +549 vote rows, purely additive (row-level diff on
(source,date,body,motion_no,member,vote): 0 removed, 549 added; canonical rows byte-stable
apart from the new provenance column). By body: Council +125 motions (379 rows), RDA +49
(157 rows; standalone board docs — the audited layer had only the 35 in-session captures),
MBA +5 (13 rows; NEW body). Contested motions 40 → 43 named-dissent (db `v_contested`
52 → 55). db: 2,020 → 2,199 motions / 5,802 votes (reconciles exactly); referrals
102 → 114 (42 high / 54 medium / 18 low). `validate_city.py`: **25 PASS / 1 WARN
(documented provenance extension) / 0 FAIL**.

**Ground-truth spot-checks (9 motions, all bodies, OCR docs included):** 2020-01-21 CC m3
(OCR; 5-0 ERA resolution), 2020-01-21 RDA m2 (OCR), 2021-01-19 CC m3 (OCR), 2022-01-18 CC
m2, 2022-12-06 RDA m2 (the date-override doc), 2024-05-07 MBA m4, 2024-05-07 CC m9 (4-1,
Glover Nay), 2024-05-21 CC m3 (3-2 deny — see anomaly below), 2025-06-03 RDA m4 (2025
roster incl. Mikolash; Gettel correctly absent as Mayor). All rolls/names/tallies match the
source text verbatim; every named-roll tally equals its result string (0 mismatches); no
oversize rolls; the excused-member and page-break-split rolls (2024-08-06 RDA) parse
correctly. The three staff-recommendation "MOTION:" agenda artifacts (2021-01-19,
2023-06-20 ×2) are correctly skipped — the real votes on those items are captured.

**Source anomalies retained verbatim (never edited):**
- 2024-05-21 CC m3: the minutes print "The motion passed 3-1 in favor" over a 5-name
  3-2 roll (Robinson + Brown No) — clerk tally typo; `result`="3-2 Pass" derives from the
  roll per the audited convention.
- 2024-05-07 MBA doc: stale "May 2, 2023" page running header (meeting verified 2024-05-07).
- 2020-01-21 CC m3: OCR broke the seconder line ("SECONDED by Council : Member Dustin
  Gettel") → seconder honestly blank, never guessed.

**Name repairs (documented channel only):** three recovered-doc mover/seconder garbles the
fuzzy canon could not fold were added to `extract_votes.py` `NAME_ALIASES`
("Paul GIover"→Paul Glover, "Gluinn Sperry"→Quinn Sperry, page-break "Bonnie"→Bonnie
Billings); db `person` table is unchanged vs pre-promotion (34, zero artifacts). Roster:
same 7 members, +463 named rows reconcile exactly; Gettel's council tenure still ends
2024-12-10 (no mayor-era leak).

---

## Addendum 2026-07-31 — four PHANTOM meetings removed (separator-less filename misparse)

**Defect.** Midvale's Revize Document Center files many minutes under a *separator-less*
date run — `CC Minutes 11723001.pdf`, `CC Minutes 1182022001.pdf`, `CC Minutes 1212020.pdf`,
`11123 Approved PC Minutes.pdf`. Every such run reads two ways (`11723` = **1-17-23** or
11-7-23). The 2026-07-12 build read four of them the wrong way, creating **phantom meetings**
whose motions/votes double-counted the real session:

| phantom date (removed) | true meeting (in-body header) | source file | where the real meeting still lives |
|---|---|---|---|
| Council 2020-12-01 | **2020-01-21** — "January 21, 2020 … the 21st day of January 2020" | `CC Minutes 1212020.pdf` | `pmn_backfill` promotion, PMN file 572397 `CC Minutes 1-21-2020.pdf` (`provenance=pmn_minutes`; a superset — it also carries that night's RDA session) |
| Council 2022-11-08 | **2022-01-18** — "JANUARY 18,2022 … the 18th day of January 2022" | `CC Minutes 1182022001.pdf` | PMN file 810853 `CC Minutes 1-18-2022001.pdf` |
| Council 2023-11-07 | **2023-01-17** — "JANUARY 17,2023 … the 17th day of January 2023" | `CC Minutes 11723001.pdf` | PMN file 941597 `CC Minutes 1-17-23001.pdf` |
| PC 2023-11-01 | **2023-01-11** — "11th Day of January 2023" | `11123 Approved PC Minutes.pdf` | the SAME PDF, already indexed correctly at `minutes/2023/2023-01-09/2023-01-11_planning-commission-regular-meeting.md` |

The PMN filenames are the hyphenated form of the identical Revize filenames, which
independently fixes the intended reading. Motion sets at the phantom dates were exact
subsets of the true dates' (identical motion text, movers, rolls) — **nothing was lost**.

**No real meeting was vacated.** Utah Public Notice (the statutory channel; entity 201,
bodies 753 Council / 754 Planning Commission) notices no session on any of the four dates:
Council Nov–Dec 2020 = 11-10, 11-17, 12-08; Nov 2022 = 11-01, 11-15; Nov 2023 = 11-14 (the
2023-11-07 regular slot moved a week — 2022-11-08 and 2023-11-07 were municipal **Election
Days**); PC Nov 2023 = 11-08 only (it meets 2nd & 4th Wednesday). **No rows were added to
either `minutes_unrecovered.csv`** — there is no gap to ledger.

**Delta (expected-rows-only).** Row-signature diff on
`(source, date, body, motion_no, member, vote)`: council **53 removed / 0 added**
(2020-12-01 ×21, 2022-11-08 ×16, 2023-11-07 ×16), PC **9 removed / 0 added** (2023-11-01);
**every removed row is on a phantom date, no other row changed**. `motions_std.csv`: 13 + 3
rows removed, all four phantom source files, 0 added. `db/civic.db`: meeting 291→287 (−4),
motion 2,202→2,186 (−16), vote 5,810→5,752 (−58; the 4-row gap vs the flat count is the four
tally-only adjournment rows, which carry no named member), application 490→487 (−3),
referral 114→113 (−1). `weeks/`: 159→156 bundles (only the three phantom-only weeks
2020-12-01, 2022-11-08, 2023-11-07 disappear; PC 2023-11-08 keeps its bundle at 2023-11-14).
`validate_entity.py midvale`: **25 PASS / 1 WARN (the documented `provenance` extension) /
0 FAIL**, db reconciles exactly (5,752 == 5,752).

**Collision no longer reproduces.** The same-signature/different-date detector
(≥0.90 motion-text similarity, same body, ≥2 motions) finds **4 collisions at ratio 1.000 in
the pre-fix db and 0 in the rebuilt db** across all 2,186 motions.

**Retained originals.** Raw files are never deleted: the four PDFs moved to
`meeting_minutes/raw/_misdated/` and `planning_commission/raw/_misdated/`, each with a README
recording the misparse. They are deliberately out of the top level of `raw/` because
`convert_minutes.py` rebuilds `minutes_index.csv` from a flat listing of `raw/` — a
wrong-dated file left there would re-create the phantom on any re-convert.

**Root cause fixed in `fetch_new.py` (so a refresh cannot re-create them).** The driver
now **never guesses** a filename date: `_date_candidates()` enumerates every calendar-valid
reading (leading-year YYYYMMDD/YYMMDD and leading-month M|MM + D|DD + YY|YYYY), strips
Revize's `001` re-upload suffix, and honours the year folder in the URL; when more than one
reading survives, the row is flagged `date_ambiguous` and `fetch()` resolves the date from
the **document's own header block** (`_date_from_text`, first 1,800 chars only, so a later
"approve the minutes of December 14, 2022" can never re-date the doc), renaming the raw file
to match. If the document confirms no candidate, the file is left **RAW-ONLY and reported**
rather than indexed under a guess. A single-candidate filename whose header disagrees emits
a `WARN` for hand review. The parser was also taught the space-separated forms
(`12-11- 2024`, `0928 22`) the old one dropped.

**Regression check of the whole index:** all 251 indexed documents re-parsed — **239 resolve
to exactly their indexed date, 12 are correctly flagged ambiguous (the truth is always among
the candidates), 0 misparse.** Each of those 12 was then re-verified against its own header
date and **all 12 are correctly dated** — the four phantoms were the complete set.

## Addendum 2026-07-31 (debt wave) — two DEBT items: died-motion outcome + the Erickson/Erikson person split

Two triage items were worked. Both premises were checked at the primary source first; one
held in substance but not in mechanism, the other **inverted** (the filed cause was wrong and
the fix moved to a different layer).

### (1) Died motion recorded as **Pass** — FIXED at the extractor (2 motions)

Triage filed this as "died-motion **substitute roll**", i.e. the roll call of a following
motion mis-attached to the motion that died, with `names_recorded=1`. **That mechanism is
not what happened.** The affected motion carries **no roll at all** (`names_recorded=0`,
0 vote rows) — verified in the pre-fix db and in `gov.db` (motion_id 220000114, `nv=0`).
The real defect was narrower and purely in the RESULT string:

*Council 2020-06-30 m3* (`meeting_minutes/minutes/2020/2020-06-29/2020-06-30_city-council-regular-meeting.md`,
line 580) prints, verbatim:

> MOTION: Council Member Bryant Brown MOVED to Approve Resolution No. 2020-R-27 ... **The
> motion died for a lack of a second.**

`extract_votes.py`'s `motion_result` regex knew `passed|carried|approved|adopted|failed|
denied|defeated|did not pass/carry` but **not `died`**, so `outcome` stayed `None` and
`result_string()` fell through to its default `"Recorded (voice vote)"` — asserting a voice
vote that never happened. `db_build_lib.outcome_of()` then read that string, found no
carriage word and no tally, and hit its final `return "Pass"` — recording the **exact
inverse** of what the minutes say. `motions_std.csv` had it right (`outcome='died'`, via
normalize_motions' `+text-died` text rule), which is how the disagreement surfaced.

The same blind spot hit one PC motion with the sibling phrasing: *PC 2020-09-09 m7*
(line 857, Commissioner Erickson's Midvale Mills rezone-to-approve motion) prints **"The
motion failed for lack of a second."** That one landed on `Fail` rather than `Pass` (the
word "failed" was matched), but still asserted `"Fail (voice vote)"`. The **substitute** in
this file is real and was already handled correctly: the next motion (Anderson's
recommend-**not**-approve, m8) carries its own roll and its own 3-1 tally — no roll was ever
mis-attached.

**Fix (extractor, both copies):** a module-level `NO_SECOND_RX` in
`meeting_minutes/extract_votes.py` and `planning_commission/extract_votes.py` matching
`motion (was) died/dies/failed/fails for (a) lack of a second`, `motion died`,
`received no second`, `did not receive a second`. It applies **only when
`names_recorded` is false**, so a stray phrase in post-vote discussion can never overwrite a
real tally. `result_string()` now emits **`"Died (no second)"`** — the collection-wide string
already used by white_city / riverton / sandy / taylorsville / magna / st_george, which
`db_build_lib.outcome_of()` maps to `outcome='Died'` and `normalize_motions.py` to
`outcome='died'` (rule `died-no-second`). Module level, so
`extract_backfill_votes.py` (which re-uses `ev.parse_motions` with an agency-roles RX
variant) inherits it; no PMN doc contains the phrasing, so that layer is unchanged.

**Delta (proved at the stable key (source_file, date, body, motion_no, member, vote)):**
2 cells in the flat CSVs (`result`), 2 motion rows in the db (`outcome`, `result_raw`),
2 rows in `motions_std.csv` (PC also `outcome fail→died`; both lose the false
`vote_mode='voice'`). **0 rows added, 0 removed, 0 vote values changed.**

### (2) Erickson / Erikson — PREMISE FAILED at the extractor; merged in the db person layer

Triage listed 975 `Erickson` vs 18 `Erikson` rows in `planning_commission/all_votes.csv` and
two `person` rows in `gov.db` for one commissioner. The two-persons finding is **real**
(pre-fix `person_id` 15 `Erickson`, 267 vote rows / 113 mover, and 18 `Erikson`, 13 vote rows
/ 1 mover). The **"extraction typo" premise is false.**

**Verified at the primary source, not the markdown:** the three affected documents are
Midvale's own **born-digital** Revize PDFs (`minutes_index.csv` `format=text`; no OCR) —
`planning_commission/raw/2022-08-10_`, `2022-09-14_`, `2022-09-28_planning-commission-regular-meeting.pdf`.
`pdftotext -layout` on the PDFs prints, in the same document:

```
                                    Candice Erickson          <- roll of members
          Commissioner Erickson            Present            <- attendance
                      Commissioner Erikson                  Yes   <- roll-call cell
```

**The city misspells its own commissioner inside the roll-call cells.** The flat CSV is
therefore **city-faithful and was NOT edited** (cardinal rule 2).

**Same-person proof:** (a) only one Eri\*son has ever sat on the Midvale P&Z Commission —
111 printed occurrences of `Candice Erickson`, no other first name, 1,018 `Erickson` vs 14
`Erikson` across the whole PC corpus; (b) the two spellings **never co-occur as two vote
rows on one motion** (0 of 660 PC motions) — and on 2022-08-10 m4 the mover is printed
`Erikson` while a voter in the same roll block is printed `Erickson`; (c) all 14 `Erikson`
mentions fall inside Erickson's continuous 2020–2026 service. (A 15th variant, `Chair
Ericson` on 2023-12-13, was already absorbed by the extractor's edit-distance-2 canonical
map; `Erikson` survived only because it recurs often enough to become its own anchor.)

**Fix (db person-resolution layer):** new **`db/person_aliases.csv`** — the same file name and
`raw_name,canonical_name,evidence` header the cache_county / utah_county / wfrc_mpo builders
already use for this exact class of correction. Midvale's `db/build_db.py` is a thin driver
over the shared `scripts/db_build_lib.py`, which has no alias slot; rather than touch the
shared library it now **wraps `db_build_lib.norm_person`** — the single funnel every
member/mover/seconder string passes through in `read_motions()`. Aliasing at `norm_person`
(not at `person_key`) also canonicalizes the DISPLAY name, so `person.full_name` is
`Erickson` by decision rather than by sort order. Canonical form is the **surname-only**
`Erickson`, matching Midvale's PC convention (its minutes print surnames in roll cells, so
every PC person row is surname-only: Anderson / Snow / Tippetts / Liedtke); promoting this
one row to `Candice Erickson` would have broken that.

**Delta:** `person` **34 → 33**, `role` 32 → 31, 13 vote rows re-keyed from person 18 to
person 15 (**vote values identical**), 1 motion's `mover_person_id` re-pointed
(2022-08-10 m4). `motion` 2,186 and `vote` 5,752 counts unchanged. Erickson's db record is
now 280 votes / 114 moves / 116 seconds.

*(Not fixed here, not in scope: 8 seconder-parse artifacts remain as their own person rows —
`Erickson with all`, `Anderson with all`, `Costello Chair Pro`, `QS`, etc. — each with 0
votes and 0 moves. They are a seconder-regex over-capture, a distinct defect.)*

### Rebuild + verification

`extract_votes.py --force` (both datasets) → `extract_backfill_votes.py` →
`scripts/normalize_motions.py midvale` → `db/build_db.py` → `db/build_referrals.py` →
`build_weeks.py`. Referral layer re-derived identically (**113 links: 42 high / 53 medium /
18 low**). `validate_entity.py midvale`: **25 PASS / 1 WARN (the documented `provenance`
extension) / 0 FAIL**; db reconciles exactly (5,752 == 5,752).

**weeks/ regression cleared.** The shared `scripts/weeks_lib.py` was repaired the same day;
before this rebuild **13 bundles printed `Meetings: 0`** despite carrying votes (the
PMN-promoted dates, whose minutes live in `pmn_backfill/` and are deliberately absent from
`minutes_index.csv`): 2020-01-21, 2021-01-19, 2022-01-18, 2023-01-17, 2023-06-20, 2024-02-20,
2024-02-27, 2024-03-12, 2024-05-07, 2024-05-21, 2024-06-18, 2024-08-06, 2025-06-03. After the
rebuild **0 bundles print `Meetings: 0`** and each of the 13 now names its PMN source
documents. 2023-04-04 also gained the 2023-03-30 budget-retreat doc (the honest zero-motion
recovery) as a second listed meeting. 156 bundles built; weekly vote sum 4,735 == flat total.

`gov.db` is left STALE on purpose — one federation run closes the whole wave.
