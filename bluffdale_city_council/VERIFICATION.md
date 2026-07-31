# VERIFICATION — Bluffdale City Council data repository

Independent QA of the built repo (2026-07-12). Method: reconcile every
doubly-stored fact (index ↔ disk ↔ JSON ↔ flat CSV ↔ db ↔ weeks), ground-truth
motions against the source minutes text (quoted below), confirm the vote ceilings,
and cross-check the election winners against outside sources. `result`/`motion`/
minutes/extractor were **not** mutated.

**Repo verdict: PASS.** `scripts/validate_city.py bluffdale_city_council` =
**23 PASS / 2 WARN / 0 FAIL**. Every dataset reconciles exactly; the two WARNs are
the standard non-blocking coverage notes (no expansion layers; PC not in weeks).

## PASS/FAIL by dataset

| Dataset | Verdict | Evidence |
|---|---|---|
| Council minutes | **PASS** | 166 index rows == 166 md on disk == 166 raw; format 137 text / 29 ocr; 0 missing, 0 disk-only; corpus screen CLEAN (0 stubs) |
| Council votes | **PASS** | 971 motions / 2,996 rows; JSON motion count 971 == CSV distinct 971; 143 vote-source files all in index; off-roster 0; printed-vs-counted mism 0; ceiling PASS |
| PC minutes | **PASS** | 91 index == 91 md == 91 raw; format 68 text / 23 ocr; corpus screen CLEAN |
| PC votes | **PASS*** | 308 motions / 1,275 rows; JSON 308 == CSV 308; off-roster 0. *validator `CEILING <=5` FAILs by design (PC seats 6–7 — see below); 1 known OCR-garbled tally (2025-10-15 m4), faithful |
| Relational db | **PASS** | 1,279 motions (Council 872 + PC 308 + RDA 77 + LBA 22); **3,793 db votes == 3,793 named CSV rows** (2,538 council + 1,255 PC); provenance all `minutes` |
| Weeks | **PASS** | 136 bundles + index.md; weekly council-body vote sum **2,996 == flat council total**; PC not bundled (shared `weeks_lib.py` design, matches peers) |
| Elections | **PASS** | 25 races (17 general + 8 primary), 25-col schema; winners match outside sources exactly (below) |
| Geo | **PASS** | boundary (2 county slices unioned) + 15 precincts; City Hall → in-Bluffdale/At-Large; SLC control → outside |
| Public comments | **PASS (honest-empty)** | submit-only email, not read/posted; `all_comments_clean.csv` header-only by design |
| Federation | **PASS** | `cities.db` carries bluffdale (1,279 motions); 27 distinct city/entity codes present |

## Reconciliation — all_votes ↔ index ↔ JSON, both bodies
- **Council:** index 166 = md-on-disk 166 = raw 166. `all_votes.csv` 2,996 rows /
  971 distinct `(source,motion_no)`; body split Council 2,612 / RDA 300 / LBA 84.
  Per-meeting JSON (`votes/**/*.json`) sums to **971 motions == CSV** ✓. All 143
  distinct vote-source paths exist in the index ✓.
- **PC:** index 91 = md 91 = raw 91. `all_votes.csv` 1,275 rows / 308 distinct
  motions; JSON sums to **308 == CSV** ✓. All 90 vote-source paths in index ✓.
- **db:** 3,793 `vote` rows == 2,538 (council named) + 1,255 (PC named) counted
  from the flat CSVs — **exact, 0 dropped**. Motion total 1,279 == 971 + 308 ✓.

## Vote-ceiling confirmation
- **Pure `Council` body caps at 5 members** — the ONLY motions with 6 named voters
  are the **2 mayoral tie-breaks** (2022-11-09 m4, 2025-05-14 m4). No other Council
  motion exceeds 5. ✓
- **RDA/LBA cap at 6** — the Mayor (Chair) legitimately appears as a 6th voter in
  named RDA/LBA rolls (e.g. 2020-06-10 RDA m8 names 5 members + Mayor Derk
  Timothy). Exercised and correct. ✓
- **PC caps at the board size (6–7), not 5** — `validate_votes.py`'s generic
  `<=5` ceiling FAILs for the PC; this is a threshold artifact (the `<=5` rule is
  the Council rule). The single >5 PC roll is **2020-12-02 m1 (6 voters)** — a real
  full board, verified. ✓
- **Off-roster names: 0** in both bodies. **Printed-vs-counted mismatches: 0
  council / 1 PC** (the known 2025-10-15 garble). ✓

## Ground-truth spot-checks (source text quoted; extractor never mutated)

1. **Council mayoral tie-break — 2022-11-09 m4** (`council_2022-11-09_1135.md`).
   Source (verbatim): *"Vote on Motion: Council Member Kallas-Aye; Council Member
   Crockett-Nay; Council Member Hales-Nay; Council Member Gaston-Aye; **Mayor
   Hall-Aye. The motion passed 3-to-2.**"* Extract: 5 named rows (Kallas/Gaston
   Aye, Crockett/Hales Nay, **Natalie Hall Aye**), result `The motion passed
   3-to-2`. **MATCH** — Mayor breaks a 2-2 tie. ✓

2. **Council mayoral tie-break — 2025-05-14 m4** (`council_2025-05-14_1621.md`).
   Source: *"Vote on Motion: Council Member Wilding-Yes, … Council Member
   Aston-Yes, **Mayor Hall-Yes. The motion passed 4-to-2.**"* Extract: 6 named rows
   incl. **Natalie Hall Aye**, result `The motion passed 4-to-2`. **MATCH.** ✓
   (Note: a distinct motion 3 in the same file "passed 3-to-2" with 5 council
   members and no mayor — the extractor correctly kept them separate.)

3. **In-session RDA — 2020-02-26 m7** (`council_2020-02-26_725.md`). Source:
   *"**Mayor Timothy moved** to adopt a Resolution approving and adopting the
   Community Reinvestment Project Area Plan for the Jordan Crossing Community
   Reinvestment Project Area. Wendy Aston seconded the motion. The motion passed
   with the unanimous consent of the **RDA Board**."* Extract: `body=RDA`, mover
   `Timothy`, result `…unanimous consent of the RDA Board`, tally-only (no named
   roll). **MATCH.** ✓

4. **In-session LBA — 2020-02-26 m6** (same file). Extract: `body=LBA`, result
   `The motion passed with the unanimous consent of the LBA Board`, motion text
   opens on the *"LOCAL BUILDING AUTHORITY ('LBA') … BOARD MEETING"* header.
   Body-tag correct; tally-only. **MATCH.** ✓

5. **OCR'd council doc — 2023-05-24** (`council_2023-05-24_1205.md`). Header:
   *"Format: ocr (tesseract-ocr)"*; body carries characteristic clean-scan garble
   (*"BLUFFDALE CITY a Mayor Natalie Hall … Councilmember Wendy Aston …"*).
   Confirms the OCR provenance label is honest and the scan seam is 2023+, not
   2020–21 (the 2020–21 council docs are born-digital `text`). ✓ *(NB: the build
   note referenced "an OCR'd 2020–21 council doc"; the council OCR set is actually
   2023–2026 — corrected here. Immaterial to counts.)*

6. **PC known OCR-garbled tally — 2025-10-15 m4** (`pc_2025-10-15_1706.md`).
   `result` string = `"The motion passed 4- 28 ~—to-1"` (OCR garble); named roll
   counted **3-1** (Woodruff/Flynn/Swanson Aye, **Griffis Nay**). The garbled
   result is kept **verbatim** and the 3-1 roll retained — surfaced honestly, NOT
   patched. Confirmed the **only** printed-vs-counted mismatch in the repo. ✓

7. **Random unflagged council motion — 2024-07-16 m2** (`council_2024-07-16_1452.md`,
   a Special Meeting). Result `The motion passed unanimously`; 4 named Aye (Aston,
   Wilding, Crockett, Lord — 4 of 5 present). Faithful. ✓

8. **RDA named 6-voter roll — 2020-06-10 m8** (`council_2020-06-10_776.md`).
   Named: Aston, Kallas, Gaston, Hales, Crockett + **Derk Timothy (Mayor)** — all
   Aye. Confirms the Mayor-votes-as-Chair ceiling of 6 in RDA. ✓

## External election cross-check (browser-UA fetches + web search, 2026-07-12)

Cross-checked against Deseret News, KSL, Salt Lake Tribune, the Salt Lake County
Clerk canvass, RCVis, and the city's own roster (March 2026 *Bluffdale Times*):

- **Mayor Natalie Hall** — won **2021** (RCV; Deseret: Hall won the mayoral race
  over former Fire Chief John Roberts, ~76%; repo has Hall 2,497 vs Roberts 806)
  and remains Mayor **2026** (Bluffdale Times: *"Mayor: Natalie Hall"*). Repo
  2025 figures (Hall 1,993 vs Pavlakis 1,927) match SLTrib/KSL. ✓
- **2021 = the Utah RCV pilot.** Deseret confirms Bluffdale was among the 23 Utah
  cities that used ranked-choice voting in 2021; RCVis hosts Bluffdale's 2021
  "Council At-Large" RCV rounds. Both **Wendy W. Aston** and **Traci Crockett** —
  the two repo winners — were the incumbents contesting the two 4-year seats, and
  both won. (Seat-1/seat-2 ordering is a sequential-RCV nuance; both are winners.
  The repo stores first-choice totals with the RCV caveat in `note`.) ✓
- **2023 council** (3 seats): official Salt Lake County canvass (utah.gov PMN
  `988699.pdf`) lists **Steve Austin, Gregory D. Wilding, Alan W. Lord** among the
  filed candidates; the repo has them as the 3 winners (Mark Hales first loser by
  10). All three are the current 2024–2027 councilmembers. ✓
- **2025 council** (2 seats): **Wendy Aston + Mackey Smith** win — both confirmed
  as sitting council members in the March 2026 *Bluffdale Times* roster (Austin,
  Lord, Smith, Wilding + Aston). ✓

No election discrepancy found; the built winners match every outside source.

## WARNs / notes (non-blocking)
- **W1 — no expansion layers.** This is a core build; the six `expand-city-sources`
  datasets and the `roster/` layer are not present (queued in the repo-root
  `TODO.md`). Not a defect.
- **W2 — PC not in weekly bundles.** By design (shared `weeks_lib.py` buckets only
  council-meeting datasets — identical to Taylorsville/South Jordan). PC joins on
  its own date.
- **Advisory — LBA stage sub-tag.** In `db/civic.db` the 22 LBA motions carry
  `stage='mba_vote'` (MBA stage bucket reused for the LBA); the `body` split
  (Council/RDA/LBA) is correct. Filter LBA by `body_id`, not by stage.
- **Advisory — referral layer is large** (269 links, 189 high). `high` is
  reliable; spot-check `medium`/`low` before quoting a cross-body chain.
