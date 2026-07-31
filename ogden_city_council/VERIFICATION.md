# Verification — Ogden City Council data repo

**Date:** 2026-06-25
**Agent:** independent verification (did not build the data; recomputed all numbers from disk).
**External sources cross-checked:** Standard-Examiner, KSL, KUER, UPR, Utah/Weber County
election results portal, ogdencity.gov election pages (per-race URLs in the election section).

> **NB (2026-07-02):** the counts in the historical sections below (473 minutes / 1,481 motions /
> 4,743 rows / RDA 144 …) predate the **2022 re-carve + re-OCR repair** — see **"Remediation 2
> (2026-07-02)"** at the bottom for what changed and the current totals (504 / 1,506 / 4,992 /
> RDA 111). The "Minutes — PASS" below was also too weak: index↔disk counting could not detect
> the 2022 mis-carved boundaries.

## Summary table

| Dataset | Status | Volume (recomputed) | Coverage | Notes |
|---|---|---|---|---|
| Minutes | **PASS** | 473 files = 473 index rows | 2020–2026, all ≥ 2020 floor | index↔disk exact match; no stubs |
| Votes (counts/roster) | **PASS** | 1,481 motions · 4,743 rows · 1319/144/18 | 2020–2026 | mayor-roster clean; no dups; no stray names; sources exist |
| Votes (named-dissent capture) | **PASS** (was FAIL — fixed 2026-06-25, see Remediation) | 84 contested motions · 151 Nay rows | all years | NAY parser fixed; repro 2021-04-13 RDA m3 now 2-2 Fail |
| Public comments | **PASS** | clean CSV = 0 rows; speaker log = 582 | 2020–2026 | honest SUBMIT-ONLY verdict; speaker log correctly labeled NOT comments |
| Elections | **PASS** | 16 races · 2019/2021/2023/2025 | Weber County | 16/16 winners match external sources; 0 mismatches |
| Geo | **PASS** | 4 district features; tool runs | current map | maps a known Ogden address to a plausible district |
| 2023 RDA/MBA gap disclosure | **PASS** | 2023 RDA=0, MBA=0 | — | honestly disclosed; body totals internally consistent |

**Original verdict (pre-remediation): FAIL** — every dataset reconciled EXCEPT the votes
dataset's named-dissent capture: the "8 contested motions" headline was wrong by ~10× (true
≈ 70–84) because a parser bug dropped line-wrapped `VOTING NO` lists.

**Updated verdict after remediation (2026-06-25): PASS.** The NAY-capture bug was fixed and the
data re-extracted + re-validated (contested motions now **84**, 151 Nay rows, repro case fixed).
See the **Remediation** section at the bottom. All datasets now reconcile.

---

## Findings per dataset

### 1. Minutes — PASS
- `find … -name '*.md'` = **473**; `minutes_index.csv` (csv-aware) = **473**. Matches README's 473.
- Set difference index↔disk = **∅** both directions (every indexed path exists; every file indexed).
- Year coverage: 2020:84, 2021:72, 2022:42, 2023:75, 2024:86, 2025:84, 2026:30 — all ≥ 2020 floor.
- Content check: **0** files < 200 bytes (no header-only stubs / failed conversions).

### 2. Votes
**Counts / structure — PASS (recomputed):**
- Motions (from JSONs, authoritative) = **1,481**; by body **Council 1,319 · RDA 144 · MBA 18** —
  exactly matches README. (A naive CSV dedup gives 1,480/1,318 due to one benign collision: two
  distinct motions both numbered "1" in the 2020-01-07 meeting. Not a defect.)
- `all_votes.csv` rows (csv-aware) = **4,430**; JSON files = **473**.
- Vote distribution: Aye 3,391 · Nay 7 · Absent 92 · Recuse 1 · Abstain 2 · empty 937.
- `names_recorded:false` motions carry exactly one empty member/vote row (937 such rows). OK.
- **0** exact duplicate rows; **0** missing `source` files; **0** stray/unknown member names
  (member set = the 13 real councilmembers implied by the election winners).
- Body totals sum correctly: RDA 10+33+51+41+9 = 144; MBA 9+9 = 18; Council = 1,319.

**CRITICAL mayor-roster check — PASS (no leak):**
- **Caldwell never appears as a voter in any year.** ✓ (Mayor 2020–2023.)
- **Nadolski votes 2020, 2021, 2022, 2023** (council chair) and **is absent 2024, 2025, 2026**
  (Mayor from 2024-01-02). ✓ Exactly the required behavior — excluded per-year via roster, not
  globally by name.
- Per-year rosters are clean 7-member sets with plausible transition-year overlaps (Stephens→Richey
  2022; the 2026 January handover shows old members Blair/Choberka with 1 vote each + new members).

**Named-dissent capture — FAIL (systemic):**
- The parser captured a recorded **Nay** in only **4 files** (8 contested motions, 7 nay rows).
- Re-scanning all minutes for `VOTING NO – <member list>` (excluding "NONE"), the **source
  contains genuine recorded NAY member-lists in ~76 roll-calls across 58 meetings** — spanning
  every year, both born-digital and OCR'd, Council and RDA. The parser dropped the overwhelming
  majority, recording those motions as unanimous / tally-only or with truncated tallies.
- **Confirmed by reading source** (not regex artifacts):
  - `2021-04-13` RDA m3: source roll-call (lines 442–444) = AYE Hyer, Nadolski, Stephens, White,
    Blair; **NO – Choberka, Lopez** (Nadolski noted absent). Data recorded **2-0 Pass**, AYE =
    {Hyer, Stephens}, Nadolski=Absent, and **dropped both Nay votes** and two Aye members.
    The `result` (2-0) is wrong and the contested motion is invisible.
  - `2024-04-09` (born-digital) line 155: `VOTING NO – COUNCIL MEMBERS CHOBERKA, HYER, AND VICE
    CHAIR [WHITE]` — not captured.
  - `2025-09-16` line 155: `VOTING NO – COUNCIL MEMBER RICHEY [AND CHAIR WHITE]` — not captured.
  - `2024-10-01` RDA line 220: `VOTING NO – BOARD MEMBERS BLAIR, CHOBERKA, [HYER, WHITE]` — not captured.
- **Likely root cause:** the NAY branch only fires for a subset of formats. The missed cases
  predominantly use an en-dash (`VOTING NO –`, 36 of 63 genuine nays) and/or place the NO-list
  after a line break; the hyphen/inline cases were captured. This is precisely the
  "phrasing-variant bug" the verification standards warn about, and it hides inside motions that
  end up flagged unanimous rather than `names_recorded:false`.
- **Positive control (capture works for unanimous):** `2023-01-03` OCR'd m3/m5 correctly record
  all 7 ayes as 7-0 Pass; `2020-08-18` Lopez-Nay and `2026-02-03` Lundell/Washington-Nay are
  captured. So AYE capture and *some* NAY formats work — the defect is specific to the
  unhandled NAY-list variants.
- **Impact:** the README/CLAUDE "8 contested" figure and the "contested votes are the signal"
  analytical promise are materially wrong; many motions carry an incorrect `result` and incomplete
  per-member tallies. Top-line counts (rows, body split, roster) remain correct.

### 3. Public comments — PASS
- `all_comments_clean.csv` = **0** data rows (header-only). Consistent with the SUBMIT-ONLY verdict.
- `minutes_speaker_log.csv` = **582** rows, explicitly labeled NOT public comments (in-person
  clerk paraphrases). README/CLAUDE/AVAILABILITY all keep this distinction.
- `AVAILABILITY.md` documents an exhaustive 6-avenue search (dedicated page, minutes, agenda
  packets, eComment portals, records archive, email/phone) and a GRAMA path — not a one-page glance.
- Minor: AVAILABILITY.md says "581" rows in two places while the CSV/README say **582** (off-by-one).

### 4. Elections — PASS (16/16 winners externally confirmed, 0 mismatches)
- File has **16 races** across **2019, 2021, 2023, 2025**, Weber County (Ogden council + mayor).
- The roster implied by the winners matches the members casting votes in `all_votes.csv`
  (Caldwell mayor through 2023; Nadolski wins 2023 mayor, stops voting 2024 — reconciles).
- Vote-count differences vs. some news figures are election-night-unofficial vs. certified-canvass
  (winner + percentage match within rounding); not discrepancies.

### 5. Geo — PASS
- `council_districts.geojson` has **4** features (DISTRICT 1–4).
- `python3 address_to_district.py "2549 Washington Blvd, Ogden, UT 84401"` runs and returns
  **precinct OGD21 → Council District 1** (plausible downtown-Ogden district).
- Minor: the script's docstring example annotates that same address as "district 2"; the live run
  returns 1. Cosmetic doc inconsistency, not a functional failure.

### 6. 2023 RDA/MBA gap — PASS (honestly disclosed + internally consistent)
- 2023 has **0 RDA and 0 MBA** motions; the slug breakdown confirms **no separate RDA/MBA minutes
  files exist for 2020–2023** (RDA/MBA-as-separate-meetings appear only 2024–2026; the 2021/2022
  RDA motions come from in-meeting "acting as the Redevelopment Agency" transitions).
- This is prominently disclosed in README and `meeting_minutes/CLAUDE.md` (DocCenter ids 29548 /
  29549, ~20–25 RDA + ~5–8 MBA missing). Counts are internally consistent (totals sum to 144/18).
- Minor: the disclosure frames the gap as "2023," but 2020 also has zero RDA capture; broadly fair.

---

## External election cross-check (race-by-race)

| Year | Office | CSV winner | External winner | Match | Source |
|---|---|---|---|---|---|
| 2019 | Mayor | Mike Caldwell (57.47%) | Caldwell, 3rd term, def. Castillo (~58%) | ✅ | standard.net 2019-11-05 |
| 2019 | Council D2 | Richard Hyer (unopposed) | Hyer on ballot, no challenger | ✅ | standard.net 2019-11-05 |
| 2019 | Council D4 | Ben Nadolski (unopposed) | Nadolski on ballot, no challenger | ✅ | standard.net 2019-11-05 |
| 2019 | Council At-Large C | Luis Lopez (unopposed) | Lopez on ballot, no challenger | ✅ | standard.net 2019-11-05 |
| 2021 | Council D1 | Angela Choberka (64.1%) | Choberka 738 (64.23%) def. Gooch 411 | ✅ | standard.net 2021-11-02 |
| 2021 | Council D3 | Ken Richey (51.61%) | Richey 1,226 (51.56%) def. Martinez 1,152 | ✅ | standard.net 2021-11-02 |
| 2021 | Council At-Large A | Marcia White | White (winner) def. Gladwell | ✅ | standard.net / ksl 2021 |
| 2021 | Council At-Large B | Bart Blair (54.27%) | Blair 4,579 (54.25%) def. Benitez 3,862 | ✅ | standard.net 2021-11-02 |
| 2023 | Mayor | Ben Nadolski (54.36%) | Nadolski 6,258 (54.27%) def. Knuth 5,274 | ✅ | KUER / standard.net 2023-11-22 |
| 2023 | Council D2 | Richard Hyer (unopposed) | Hyer re-elected (incumbent, unopposed) | ✅* | ogdencity.gov 2023 / roster |
| 2023 | Council D4 | Dave Graf (52.68%) | Graf 2,465 (52.68%) def. Van Wagoner 2,214 | ✅ | standard.net 2023-11-22 |
| 2023 | Council At-Large C | Shaun Myers (59.3%) | Myers 6,855 (59.30%) def. Andersen 4,705 | ✅ | standard.net 2023-11-22 |
| 2025 | Council D1 | Flor Lopez (60.12%) | Flor Lopez 1,108 (60.12%) def. Reyneveld 735 | ✅ | standard.net 2025-11-06 |
| 2025 | Council D3 | Ken R. Richey (52.15%) | Richey 1,792 (52.14%) def. Satow 1,645 | ✅ | standard.net 2025-11-06 |
| 2025 | Council At-Large A | Alicia Washington (56.63%) | Washington 6,431 (56.63%) def. White 4,926 | ✅ | standard.net 2025-11-06 |
| 2025 | Council At-Large B | Kevin Lundell (60.24%) | Lundell 6,870 (60.23%) def. Blair 4,536 | ✅ | standard.net 2025-11-06 |

\* 2023 D2 (Hyer, unopposed, 100%) confirmed by incumbency/roster continuity rather than a distinct
external vote tally; consistent with the unopposed-incumbent pattern and his continued voting record.

**Result: 16/16 winners match external sources. 0 winner mismatches. 0 margin discrepancies beyond
unofficial-vs-canvass rounding.** Mayor timeline confirmed: Caldwell through 2023; Nadolski elected
2023, took office Jan 2024.

---

## Mayor-roster check result
**PASS — no leak.** Caldwell appears as a voter 0 times in any year. Nadolski votes 2020–2023 and is
absent as a voter 2024–2026. Exactly as required.

## Discrepancies found
1. **(FAIL, votes)** Named-dissent capture systematically drops `VOTING NO – <members>` roll-calls:
   ~76 genuine NAY roll-calls across 58 meetings in source vs. 8 contested motions captured.
   At least one (2021-04-13 RDA m3) also has a wrong `result` (2-0 vs ~4-2). Headline "8 contested"
   is wrong (~10× undercount).
2. (Minor) AVAILABILITY.md says speaker-log = 581; actual = 582.
3. (Minor) `address_to_district.py` docstring says 2549 Washington Blvd → district 2; live run → 1.

## Gaps & recommendations
- **Fix the NAY parser branch** (handle en-dash `–`, line-broken NO-lists, and RDA "Board Members …"
  in the dissent capture), re-run `extract_votes.py` + `validate_votes.py`, and recompute the
  contested count before re-asserting "✅ verified." Add a guard test: count source `VOTING NO – <name>`
  occurrences and assert the captured Nay count is in the same ballpark.
- Acquire the 2023 RDA (DocCenter 29548) / MBA (29549) compilations to close the disclosed gap.
- Reconcile the 581/582 and docstring-district cosmetic mismatches.

---

## Remediation (2026-06-25, post-verification)

The single FAIL finding — systematic under-capture of named dissents — was root-caused and fixed.

**Root cause.** `meeting_minutes/extract_votes.py` → `parse_named_rollcall` captured the
`VOTING NO` member list with `[^\n]{0,200}`, which cannot span a line wrap. Ogden's clerk
routinely wraps the dissent onto its own line (`… CHAIR BLAIR.\nVOTING NO-\nCOUNCIL MEMBER
CHOBERKA.`), so every line-wrapped NO list was silently dropped — and the combined AYE+NO regex
sometimes also truncated the AYE list on the same blocks.

**Fix.** Rewrote `parse_named_rollcall` to capture the AYE and NO segments **independently**,
each spanning line breaks (`[\s\S]`): AYE runs from `VOTING AYE[-:]` to the next `VOTING NO` /
blank line; NO runs from `VOTING NO[-:]` to the first sentence-ending period. Kept the
`(?<!ALL\s)` lookbehind + blank-line bound that prevent signature-block / mayor leakage.

**Re-validated result** (`votes/_validation_report.txt`, re-run):
- Contested motions: **8 → 84** (matches the verifier's independent ≈70–84 estimate).
- Nay rows: 7 → **151**; total member-vote rows 4,430 → **4,743** (recovered ayes too).
- Motion counts unchanged: **1,481 total · Council 1,319 · RDA 144 · MBA 18** (no structural drift).
- Mayor-roster check still clean (Caldwell never votes; Nadolski votes 2020–23, absent 2024–26).
- Repro case **2021-04-13 RDA m3**: was `2-0 Pass` (both nays dropped) → now `2-2 Fail | NAY:
  Choberka, Lopez`.
- Remaining 4 tally/result mismatches are all year-boundary compilation artifacts (benign).

README/CLAUDE headline numbers updated to match. Votes dataset now passes.

---

## Remediation 2 (2026-07-02) — 2022 re-carve + re-OCR (audit finding, Phase 1.2)

The repo-wide audit (`_audits/2026-07-02/report.md`) found the 2026-06-25 verification had
missed a 2022-specific defect (this file's own "Minutes — PASS" relied on index↔disk counts,
which cannot catch mis-carved boundaries):

**Root cause.** The 2022 yearly compilation (`raw/minutes/compilation_CC_2022.pdf`) is a
*scan* whose garbled embedded OCR layer (Acrobat Paper Capture, stray-space rate ~226/10k
tokens — `bou levard`, `Counci I members`, `HY ER`) was used as-is, and the carve boundaries
were wrong (files ran across meeting starts; e.g. the old `2022-01-04_city-council-meeting.md`
contained three meetings; the old `2022-12-06_city-council-meeting.md` was actually the closed
session). Effects: only 30 of 38 meeting dates carved; 47% of 2022 named roll calls captured
≤5 of 7 voters; ~33 Council motions mis-tagged `body=RDA` via boundary bleed past "acting as
the Redevelopment Agency" openings. Docs wrongly blamed 2023 (which was always clean) and
claimed council coverage complete.

**Fix (from the retained raw PDF; raw/ untouched).** Re-rendered all 296 pages at 300 dpi
(`pdftoppm`), re-OCR'd with tesseract 5.5, re-carved on the meeting-opening paragraphs,
cross-checked every page's running header against its carved meeting (**0 mismatches**;
67 horizontal-rule OCR-noise lines dropped, logged). Re-ran `extract_votes.py`,
`validate_votes.py`, `db/build_db.py`, `db/build_referrals.py` (referral overrides re-bound —
they pin application_ids, which shifted), `build_weeks.py`. Originals in `_backups/2026-07-02/`.

**Verified results:**
- 2022 files 42 → **73**; meeting dates 30 → **38** (recovered: 01-04 work session, 01-11 work
  + special, 02-03, 03-01 joint work + factfinding + regular, 04-05 work session, 05-10, 05-31,
  06-07 work session, 07-12 ×2, 08-02 special, 08-23 joint work, 09-06 work session, 09-20 ×2,
  09-21, 10-11 closed, 10-18 work session, 11-15 joint work + regular, 12-13 ×2). Nothing in
  the compilation was left unrecovered; no illegible pages.
- Corpus screener (`screen_corpus.py`): 2022 `med_split` **24.335 → 0.000**, `med_dict`
  0.692 → 0.769 — now indistinguishable from the born-digital years.
- 2022 votes: named roll calls 66 → **95**; ≤5-of-7-voter share **41% → 12%**, and each of the
  remaining 11 matches an "Excused:" attendance line in the minutes (genuine absences).
  Known-bad repro cases fixed: 2022-01-04 Resolution 2022-1 denial now **6-1** (Blair Nay, six
  Ayes incl. Richey — was 5-1) and Joint Resolution 2022-2 now **7-0** (was 6-0).
- Totals: 1,481 → **1,506 motions**; 4,743 → **4,992 member-vote rows**; contested 84 → **87**;
  Council 1,319 → **1,377**; RDA 144 → **111** (the 33 mis-tagged 2022 "RDA" motions were
  Council motions — e.g. a Trails Network appointment — and are now correctly `body=Council`;
  2022, like 2023, has 0 genuine RDA/MBA motions because those separate meeting sets were
  never acquired). **Non-2022 vote rows byte-identical before/after** (verified).
- Mayor-roster check still clean. New validation flags: the Jan 2022 chair/vice-chair election
  roll calls print departed member STEPHENS — a clerk typo in the source scan (visually
  confirmed on p10), preserved verbatim per the never-normalize rule.
- Two clerk-typo meeting dates resolved by running header + stated weekday and visually
  confirmed against the scan: 2022-03-01 regular meeting (opening prints "March 1, 2021") and
  2022-06-07 work session (opening prints "June 2, 2022"; the old carve had misdated it
  2022-06-02 and mistyped it a regular meeting).
- Derived layers rebuilt: `db/civic.db` (316 meetings, 1,923 motions, 5,758 votes, 259 apps;
  integrity OK) and `weeks/` (246 → 255 bundles). Referrals: 2 → **1** (the Franklin Street
  PC→Council link, high; the former RDA "address co-location" link sat on mis-tagged motions
  and correctly disappeared).

## 2026-07-02 addendum — duplicate member-vote adjudication (plan item 3.1 prep)

The repo validator flagged 3 duplicate `(source, motion_no, date, member)` pairs in
`meeting_minutes/all_votes.csv`, all contradictory Aye+Nay. Source check: all three are
**faithful clerk contradictions** — the roll-call "VOTING AYE" line is the full-roster
boilerplate *including* the dissenter, while a deliberate "VOTING NO" line names them:

- 2021-04-27 m6 (Ord. 2021-19): Aye list includes **Nadolski** AND "VOTING NO- COUNCIL
  MEMBER NADOLSKI"; narrative: "Council member Nadolski provided an explanation of his
  opposing vote." True tally 6-1.
- 2021-07-13 m7 (street-name ordinance): Aye line lists all 7 members AND "VOTING NO -
  COUNCIL MEMBER CHOBERKA AND VICE CHAIR WIDTE[=WHITE]" (9 votes from 7 members);
  Choberka's No is explained in the narrative. True tally 5-2 (**Choberka**, **White**).

Disposition: CSV keeps both verbatim rows per pair (city-faithful); the db's single-vote
grain resolves each to **Nay** via the new `db/vote_overrides.csv`, applied fail-loud by
`db/build_db.py` (park_city pattern; see db/SCHEMA.md). db rebuilt: 1,923 motions · 5,758
votes (= 5,761 named CSV rows − 3 override merges) · referrals unchanged. Validator
h.db: PASS ("+ 3 documented overrides").

**2026-07-02 (3.1) council-vote validation:** bespoke `meeting_minutes/validate_votes.py` re-run (report under `meeting_minutes/votes/`); shared-template checks: 4,992 rows / 1,506 motions (615 named, 891 tally-only — OCR-era narrative style); 0 schema/date/vocab defects, 0 malformed groups; 3 double-vote pairs all documented in `db/vote_overrides.csv`, 0 undocumented; tally-vs-counted 615/615; 0 unexplained mismatches.

## Remediation 3 (2026-07-02, plan item 3.5) — agenda-subject enrichment of adoption motions

**Problem** (logged in crosswalks/README.md at 2.3): ~500 adoption motions' entire captured
text was a subject-less formula ("ORDINANCE WAS PASSED AND ADOPTED AS OGDEN CITY ORDINANCE
20xx-N AND ORDERED POSTED…", "ORDINANCE 20xx-N WAS ADOPTED", "MOVED THE RESOLUTION BE
ADOPTED…"), leaving them unclassifiable (motion_type_std=Ordinance/Resolution with no
land-use/budget signal). The subject is printed in the same minutes: every introduced
ordinance/resolution gets a statutory long-title reading ("introduced in writing proposed
Ordinance 20xx-N, entitled: 'An ordinance of Ogden City…'") and each item sits under a
mixed-case agenda heading.

**Fix** (extractor-only; minutes/ and raw/ untouched): `meeting_minutes/extract_votes.py`
now pre-scans each document for `…entitled:` long-title blocks and `Proposed
Ordinance/Resolution N` agenda headings, and for motions matching a bare adoption formula
appends the item's **verbatim** source text to the motion field inside an explicit
delimiter — `[ENTITLED: "…"]` (long-title, preferred) or `[AGENDA ITEM: "…"]` (heading
fallback) — matched by ordinance/resolution number (zero-padding/dash/OCR-digit
normalized), or by nearest-preceding introduction of the same kind for the no-number
"MOVED THE RESOLUTION BE ADOPTED" form. Only verbatim source text, never a summary;
subjects >700 chars truncate at a word boundary with a trailing ellipsis. The native
`motion_type` is still computed from the bare motion sentence (clerk-faithful); the JSONs
carry the subject separately (`subject`, `subject_source`).

**Result:** 500 motions enriched (488 ENTITLED / 12 AGENDA ITEM; Council 467 / RDA 28 /
MBA 5; spread 2020–2026: 84/86/82/87/64/84/13). 1 motion left unenriched on purpose:
2025-08-19 prints "ORDINANCE 2025-23 WAS ADOPTED" but the meeting introduced only
2025-26 — a source number mismatch we do not guess across.

**Verification:**
- all_votes.csv: 4,992 rows before and after; 3,287 rows changed, every one motion-column
  only with the old text a strict prefix of the new (checked programmatically, 0 violations).
- All 500 appended subjects verified **verbatim contiguous substrings** of their source
  minutes (whitespace-collapsed, matching the field's existing convention); 11 carry the
  ellipsis truncation marker. 2022 OCR-era subjects (82) checked for garble: median
  non-standard-character rate 0.0%, worst 0.7% (legit § etc.).
- Attachment correctness: all 12 heading-fallback cases reviewed by hand; 15 sampled
  no-number nearest-preceding cases traced to the immediately-preceding introduction
  (incl. two double-formula meetings where each motion got its own item's subject).
- Non-enriched motions: 0 classification changes in motions_std.csv (isolation verified).

**Classification improvement** (`scripts/normalize_motions.py ogden`): 208 of the 500
enriched motions reclassify — 74→Land-Use (52 Rezone, 10 General-Plan-Amendment,
8 Vacation, …), 96→Budget, 14→Interlocal, 8→Contract-Purchase, 6→Appointment,
4→Grant-Funding; 284 legitimately remain Ordinance/Resolution (non-land-use code/fee
amendments per their long titles). Council motion_type_std: Land-Use 1.5%→6.9%, Budget
0.5%→6.5%, Ordinance 26.1%→15.3%. Ogden combined Land-Use 9.3%→13.4% (PC 38.1%
unchanged), closing toward its neighbors (slc 26.0, provo 34.2) with the honest residual
being real routing + the 2022–23 RDA/MBA coverage gap.

**Derived layers rebuilt:** db (1,923 motions · 5,758 votes = 5,761 named rows − 3
documented override merges; INTEGRITY OK) and weeks/ (255 bundles). The id-pinned
`db/referral_overrides.csv` entries were **re-bound** (application ids shift when motion
texts change): Franklin link now 172←245, boilerplate suppress now 147←91. The enriched
text gives the referral subject-matcher real signal: links 1 → **4** (Franklin override +
3 new hand-verified subject links — Adams CRA tax-increment Council↔RDA twin resolutions,
the 2023 Housing Element PC→Council referral, Ogden Bend PC↔RDA). 4 new false-positive
pairs were suppressed with documentation: the matcher's name-anchored path matched shared
mover/seconder SURNAMES (LUNDELL, WASHINGTON-the-member vs Washington Blvd, HYER/MYERS)
plus boilerplate — a pre-existing build_referrals weakness (roster surnames aren't
stripped from subject tokens; RDA adjourn motions count as "applications") that enriched
text exposed; a principled fix (strip roster names, exclude adjourn/procedural agency
motions) is left as a follow-up note, suppress rows carry the intent meanwhile.

**Validators:** bespoke validate_votes.py clean (same 4 pre-existing documented flags:
2 year-boundary artifacts + 2 Jan-2022 STEPHENS clerk typos);
`scripts/validate_city.py ogden_city_council`: **22 PASS / 1 WARN (pre-existing
documented index extension) / 0 FAIL**. Originals in `_backups/2026-07-02/…` with
`.pre-3.5` suffixes (all_votes.csv, extract_votes.py, motions_std.csv, votes/, db/,
weeks/, docs).
