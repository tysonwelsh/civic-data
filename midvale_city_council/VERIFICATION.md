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
