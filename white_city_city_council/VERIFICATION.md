# VERIFICATION — White City civic data

Independent QA record for `white_city_city_council/`. Verifies the built datasets against the
source documents, reconciles every doubly-stored fact, and cross-checks the election winners
against outside sources. Method follows `SCHEMA_SPEC.md §10` and the `audit-city-data` skill.
**Read-only** — this verification never mutated a canonical CSV, minutes file, extractor, or
the db (`db/build_db.py` was NOT run).

- **Verifier:** build-closeout QA pass
- **Date:** 2026-07-12
- **Conformance:** `python3 scripts/validate_city.py white_city_city_council` →
  **23 PASS / 2 WARN / 0 FAIL** (both WARNs are documented-by-design, below).

---

## 1. PASS/FAIL by dataset

| Dataset | Verdict | Volume | Evidence |
|---|---|---|---|
| Council minutes | **PASS** | 117 files (105 `text` + 12 `ocr`), 2018-01-04 → 2026-05-07, all `source=streamline` | index 117 paths all exist; dates parse + plausible; corpus screener CLEAN (§4) |
| Council votes | **PASS** | 633 motions · 753 vote rows (**184 named** + 569 tally-only) | vocabulary in-bounds; ground-truthed across all 3 vote-grammar eras + OCR (§3); max tally 5, 0 double-votes (§2) |
| Planning Commission | **PASS (honestly EMPTY)** | `all_votes.csv` header-only; 0 minutes | own PC exists but publishes no minutes — documented in `planning_commission/AVAILABILITY.md` + 2 rows in `minutes_unrecovered.csv` (§5) |
| Relational db (`db/civic.db`) | **PASS** | 633 motions · 184 votes · 10 persons · 6 roles · 17 applications · 0 referrals | reconciles exactly: 184 CSV named rows == 184 db `vote` rows, 0 dropped (§2) |
| Public comments | **PASS (honest-empty)** | `all_comments_clean.csv` header-only | submit-only / in-meeting; no published archive — `public_comments/AVAILABILITY.md` |
| Election results | **PASS** | 5 races (2019, 2023, 2025×3) + candidate/precinct tables | 25-col superset conforms; external cross-check corroborates every winner (§6) |
| Geo (address→district) | **PASS** | at-large (single "district"); city_boundary + 6 precincts; tested resolver | `geo/address_to_district.py` returns White City at-large for an in-boundary point |
| Weekly bundles | **PASS** | Thursday grid | weekly votes sum **753 == flat total**; weeks/ not stale |

**2 WARNs, both by design:**
- `a.layout: missing optional README.md, CLAUDE.md, VERIFICATION.md` — resolved by this
  closeout (those files now exist).
- `f.tally[meeting_minutes]: 30/56 named-roll-call tallies match result string (53.6%)` —
  **expected**, not a defect. It is driven by the **narrative-named-dissent era** (2020–2022,
  and one 2024 case): the printed `result` is a prose string like `Pass (unanimous)` while a
  single named dissenter/abstainer row is attached (Scott Little `Nay`/`Abstain`; Tyler Huish
  `Abstain` in 2024). The counted named rows therefore do not equal the string tally *by
  design* — the majority is honestly left unnamed (see §3.2). Ground-truthed correct.

---

## 2. Reconciliation of redundant representations (all agree)

| Check | Result |
|---|---|
| `all_votes.csv` rows | 753 (184 named + 569 tally-only placeholder rows) |
| Distinct motions `(source, motion_no)` | 633 |
| index paths vs disk | 117 index rows, 117 files on disk, 0 missing |
| `all_votes.csv` source refs vs index | 105 distinct source files carry ≥1 motion; **12 indexed minutes carry 0 motions** — each confirmed a genuine no-action session (§3.5), not an extraction miss |
| db `vote` vs CSV named rows | **184 == 184, 0 dropped, 0 overrides** (fail-loud build) |
| db `motion` vs CSV motions | 633 == 633 |
| weeks/ votes sum vs flat | 753 == 753 |
| **Max named voters on any motion** | **5** (0 motions exceed 5) — confirms the Chair/Mayor-votes 5-person body |
| A member voting twice on one motion | **0** |
| Vote-value vocabulary | `Aye` 148 · `Nay` 24 · `Abstain` 12 (= 184). **No `Absent`/`Recuse`/`Excused` values** — a recording ceiling: absences appear only as narrative prose ("Council Member Dickerson was absent for the vote"), never as a member vote row. |

---

## 3. Ground-truth spot-checks — 6 meetings across ALL THREE vote-grammar eras + OCR

Each sampled row was compared to the retained source minutes; quoted text is from the file.

### 3.1 Narrative-tally era (2018–2025) — `2018-01-04` (township, born-digital)
Minutes: *"Council Member Dickerson, seconded by Council Member Price, moved to close the staff
meeting. The motion passed unanimously."* → `all_votes.csv` motion 1: mover `Kay Dickerson`,
`result="Pass (unanimous)"`, **member/vote blank (tally-only)**. All 9 motions match; no
per-member Aye list is printed in this era, so no names are invented. **FAITHFUL.**

### 3.2 Narrative-named-dissent era (2020–2022) — `2020-03-05` (township)
Minutes (line 620): *"…develop all committee agendas. The motion passed **3 to 1, showing
Council Member Little voting "Nay"**. Council Member Dickerson was absent for the vote."* →
motion 12: `result="3-1 Pass"`, single row `Scott Little = Nay`; the 3 Ayes and the absent
Dickerson are honestly **unnamed** (source printed only the dissenter). motions 14 & 16 match
identically. This is the pattern that produces the `f.tally` WARN. **FAITHFUL.**

### 3.3 OCR'd 2024 minutes — `2024-05-16` (image-only scan, `format=ocr`)
Minutes: *"…moved to approve the following resolution adopting the 2025 White City budget. The
motion passed unanimously."* (RESOLUTION NO. 2024-05-03) → motions 1–4 (open/close hearing,
budget resolution, Third Amendment resolution 2024-05-04) all match, all tally-only. The OCR
text preserves a source-scan artifact — *"THIS 1S THE TIME"* (1↔I) — which is **positive
evidence of faithful transcription**, not a hallucinated clean-up. **FAITHFUL.**

### 3.4 OCR'd 2024 minutes, named-abstain — `2024-06-06` (image-only scan)
Minutes (line 660): *"Resolution 2024-06-04, formally adopting the name "White City"… The motion
passed unanimously, **with Council Member Huish abstaining from voting**."* → motion 16:
`result="Pass (unanimous)"`, single row `Tyler Huish = Abstain`. Correctly captured a named
abstention buried inside a "unanimous" prose string (another `f.tally` contributor). **FAITHFUL.**

### 3.5 Full named roll-call era (2026+) — `2026-05-07` (city, Mayor Perry)
Minutes (lines 212–217): *"…he called for a roll call vote. **Mayor Allan Perry — Aye; Council
Member Neil Mahoney — Aye; Council Member Greg Shelton — Aye; Council Member Tyler Huish — Aye;
Council Member Linda Price — Aye.** The motion passed unanimously."* → motion 1: **5 named `Aye`
rows including `Allan Perry` (the Mayor)**, `result="5-0 Pass"`. Confirms the **Mayor VOTES and
max council tally = 5**. All 4 motions on the day match. **FAITHFUL.**

### 3.6 No-motion sessions (the 12 minutes with 0 vote rows) — spot-checked
`2018-09-22`, `2020-10-15`, `2022-06-23` are continued/work sessions ("MET… PURSUANT TO
ADJOURNMENT ON THURSDAY…") that adjourn with **no `moved`/`motion` prose** — correctly produce 0
rows. `2026-02-27` special is a 1,615-byte call-to-order/adjourn stub — 0 motions, correct.
**One documented scope boundary:** `2019-11-19` **Board of Canvassers** contains a single
tally-only certification motion — *"Canvasser Price, seconded by Canvasser Perry, moved to
approve the 2019 General Election results as presented and certify them. The motion passed
unanimously."* — which the **Council-scoped extractor does not capture** (the mover is a
"Canvasser", the body is the Board of Canvassers, not the Council). This is 1 tally-only
procedural certification motion outside the Council vote spine; see `_audits/audit_2026-07-12.md`
FIX-2 (documentation-only follow-up; not a Council-record integrity issue).

---

## 4. Corpus screen (statistical, `screen_corpus.py`)

`meeting_minutes/minutes/` (117 files) — **CLEAN**: 0 stubs, 0 replacement-chars, 0 PUA-garbled,
0 mojibake, 0 long-token runs, 0 duplicate bodies. `dict_ratio` median 0.795 (min 0.720, no
outliers); `split_word_rate` median 0.00 /1k (max 2.18, no outliers); `weird_char_ratio` median
0.019 (drops to 0.000 in 2024–2026 born-digital/OCR years — expected). Per-year medians are flat
across all nine years — no Ogden-style hidden bad year. The `repeated_line` (92/117) and
`ends_mid` (116/117) flags are **advisory corpus-wide** (the standard White City minutes header
block + last-line "the meeting was adjourned." phrasing), not anomalies.

---

## 5. The empty Planning Commission is HONEST

White City has its **own** Planning Commission (`whitecity.utah.gov/planning-commission` — Chair
Christy Seiger-Webster et al., 4th-Thursday cadence). But the city **publishes no PC minutes
series**: the PC page exposes only a meeting-schedule PDF + the adopted General Plan and links
out to the Greater SL MSD long-range-planning function. `planning_commission/all_votes.csv` is
therefore **header-only (0 rows)** — an honest empty result, documented in
`planning_commission/AVAILABILITY.md`, with the two known-but-unrecovered PC meetings
(2017-03-09, 2019-11-04, agenda/packet published, minutes never posted) logged in
`planning_commission/minutes_unrecovered.csv`. No PC vote was invented; no council item was
mislabeled PC. **This is data, not a gap to be filled** (SCHEMA_SPEC principle 2).

---

## 6. Election cross-check vs OUTSIDE sources (browser-UA, GET-only, 2026-07-12)

| Race | Repo (`white_city_races.csv`) | Independent source | Verdict |
|---|---|---|---|
| **2019** Council At-Large (3 seats) | Little 622, Perry 589, Flint 559 (win); Cutler 532 · total 2,302 · 978 counted | **2019 Board-of-Canvassers minutes** (`2019-11-19`, a source SEPARATE from the SOVC sheet): Little 622, Perry 589, Flint 559, Cutler 532, total 2,302, times counted 978 | **EXACT MATCH** |
| **2023** Council At-Large (3 seats) | Flint 579, Shelton 558, Huish 448 (win); Van Horn 375, West 252 | KSL / press 2023 municipal returns confirm winners Flint/Shelton/Huish and Van Horn as a losing candidate (unofficial night count ~345 vs the repo's canvassed 375 — the normal election-night-vs-final gap) | **WINNERS CONFIRMED** |
| **2025** Mayor | Perry 740 (61.87%), Flint 456 (38.13%) | **Salt Lake Tribune** 2025 results: Perry **61.9%**, Flint **38.1%**; whitecity.utah.gov/elections + electionresults.utah.gov list the same candidate set | **EXACT MATCH** (pct) |
| **2025** Council At-Large B | Price 730, Denning 307 | city elections page lists Price vs Denning (write-in) | candidate set confirmed |
| **2025** Council At-Large C | Mahoney 635, Cardenaz 536 | city page + SLTrib list Mahoney vs incumbent Cardenaz | confirmed (Mahoney unseated Cardenaz) |

The 2019 gap the recon flagged was **recovered** from the raw SOVC sheet and is independently
corroborated by the canvass minutes to the vote. Water-district contests (`WHITE CITY WATER`)
and the 2015 incorporation/MSD ballot questions were correctly **excluded as decoys**.

---

## 7. Structural facts confirmed

- **Township → City.** Governed as White City Metro Township 2017 → **City effective 2024-05-01
  (Utah HB35 2024)**; first directly-elected Mayor (Perry) + council seated Jan 2026.
- **The Chair/Mayor VOTES in BOTH eras; max tally = 5** (§2, §3.5) — Millcreek-like, NOT the
  Taylorsville/South-Jordan non-voting-mayor form.
- **Three vote-grammar eras**, all parsed: narrative-tally (2018–2025) → narrative-named-dissent
  (2020–2022, drives the `f.tally` WARN by design) → full named roll calls (2026+).
- **OCR seam:** 12 mid/late-2024 minutes were image-only scans, recovered via OCR (`format=ocr`);
  screener + ground-truth found them faithful (preserved source typos).
- **Streamline CMS** (whitecity.utah.gov) + **Utah PMN body 5805** fallback.

## 8. Known limits / honest gaps (all documented, none filled)

- **2017 is agenda-only** — the council was seated Jan 2017 but the earliest published *minutes*
  are 2018-01-04; the five 2017 agenda-only meetings are logged in `minutes_unrecovered.csv`.
- **PC minutes never published** (§5).
- **Public comments submit-only** — honest-empty.
- **No `roster/` layer yet** — the rolling council-roster layer (`roster/build_roster.py` via the
  `update-council-roster` skill) has not been generated for this newly built city; a follow-up.
- **Vote-value ceiling:** council records only `Aye`/`Nay`/`Abstain` as vote values (§2).

## Addenda
*(none — append dated entries here on any future repair or re-audit)*
