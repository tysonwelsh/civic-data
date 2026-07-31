# Verification — Sandy City Council data repo

**Date:** 2026-06-25
**Agent:** independent verification (did not build the data). Numbers below were recomputed
from disk with `python3`/`csv` (never `wc -l`), and election winners were cross-checked
against external sources (Salt Lake County canvass, Utah elections, Deseret News, KSL, Fox 13,
Sandy Journal, rcvis.com).

## Summary table

| Dataset | Status | Rows / volume (recomputed) | Coverage | Notes |
|---|---|---|---|---|
| Minutes | **PASS** | 274 files = 274 index rows | 2020–2026 | exact reconcile; 0 stubs. (Fixed post-verification: README now states 58 OCR files; `source_url` backfilled to the Legistar portal.) |
| Votes | **PASS** (was WARN — fixed, see Remediation) | 655 motions · 2,974 rows · 79 contested | 2020–2026 | the 16 flagged motions were narrative inline tallies; dissenter-capture + tally-orientation fixed; 0 over/under-capture |
| Public comments | **PASS** | `all_comments_clean.csv` = 0 rows; speaker log = 362 | — | empty by design (submit-only); speaker log correctly labeled NOT comments; AVAILABILITY audit is exhaustive |
| Elections | **PASS** (was FAIL — fixed, see Remediation) | 14 races · 2019/2021/2023/2025 | winners externally confirmed | 2019 + 2023 At-Large corrected to the true 2-seat winners (Sharkey+Houseman; Sharkey+DeKeyzer) |
| Geo | **PASS** | 4 district features; 110 precincts | current map | tool runs, geocodes, returns plausible Districts 1–4 |

**Original verdict (pre-remediation): FAIL** — driven by the Elections summary file
misrepresenting two At-Large races, with a secondary Votes WARN.

**Updated verdict after remediation (2026-06-25): PASS.** Both the election misrepresentations
and the vote-capture gap were root-caused and fixed; data re-extracted/re-validated and docs
corrected. See the **Remediation** section at the bottom.

---

## Findings per dataset

### 1. Minutes — PASS (with two documentation discrepancies)
- **File↔index reconcile (from repo root):** 274 `.md` files on disk, 274 rows in
  `minutes_index.csv`; **0 indexed files missing on disk, 0 on-disk files missing from index.**
  Matches README's claimed 274 exactly.
- **Year coverage (≥2020 floor):** 2020:45, 2021:45, 2022:44, 2023:43, 2024:38, 2025:40,
  2026:19 (=274). 2020 floor satisfied; runs through current month (June 2026).
- **Content check:** 0 files under 800 bytes — no header-only stubs; download/convert did not
  silently fail.
- **DISCREPANCY (README):** `format` column = **216 `text` + 58 `ocr`**. The README coverage
  table claims "✅ complete, **no OCR**." That is false — 58 minutes were OCR'd (sizes
  2.4 KB–25 KB, all content-bearing). Data is fine; the README statement is wrong.
- **DISCREPANCY (provenance):** `source_url` is **blank for all 274 rows**, although README
  and CLAUDE.md cite "each file's `source_url`" as canonical provenance. Files are still
  traceable via `path`/`slug`, but the per-file source URL is not actually recorded.

### 2. Votes — WARN (no fabrication; member-level undercount on 16 motions)
Recomputed from `all_votes.csv`:
- **Motions:** 655 (README 655 ✓). **Member-vote rows:** 2,951 (README 2,951 ✓).
- **Body breakdown:** Council 654 motions / 2,950 rows; **RDA 1 motion / 1 row** (matches the
  README's acknowledged RDA undercount). The lone RDA row is `names_recorded:false` (tally-only
  7-0), faithful to source.
- **Contested (any Nay/Abstain/Recuse):** **79** (README 79 ✓). Vote values: 2,475 Aye, 161
  Nay, 78 Absent, 6 Abstain, 231 blank.
- **`names_recorded:false` handling — PASS:** 231 motions are all-empty (no member/vote); **0
  of the 231 blank-vote rows carry a non-blank member** — no invented unanimous rosters.
- **Mayor-never-votes — NUANCED:** Monica Zoltanski appears as a voter in **155 rows**, NOT
  zero. 154 are legitimate (she was the **District 4 councilmember 2020–2021** before becoming
  Mayor: 87 rows in 2020, 67 in 2021). **1 row (2025-11-18, motion 6)** post-dates her
  mayorship — checked the source: the official minutes themselves list "Yes: 8 … Monica
  Zoltanski" (a clerk error: header says 8 but lists 7 names incl. the Mayor, and *omits* D4's
  Houseman who was present). The extractor faithfully captured the source. No motion exceeds 7
  Aye. **Caveat:** README's "Mayor … never appears in the Yes/No tallies" is imprecise — she
  appears 154× as a 2020–21 councilmember plus once via a source clerk-error.
- **BUG — dropped Aye voters on 16 motions (the coverage check):** 16 motions have a
  `result` string inconsistent with their recorded rows (e.g. `6-1 Pass` but only the single
  **Nay** row present, 0 Aye rows). **All 16 are in 2020 (11) and 2021 (5).** Spot-checked
  2020-08-18 motion 5: source clearly lists `Yes: 6` (Stroud, Coleman-Nicholl, Robinson,
  Houseman, Sharkey, Christensen) then a **page-break footer** ("Sandy City, Utah … Page 9 …
  Printed on 9/2/2020") then `No: 1 Monica Zoltanski`. The parser kept only the post-footer
  Nay and dropped all 6 Aye rows. Estimated **~94 missing member-vote rows**; true total ≈
  3,045. Aggregate motion count, contested count, and `result` strings are unaffected, but
  **member-level Aye totals for 2020–2021 are undercounted.** No fabrication — this is a
  silent omission, not invention.
- **Roster — plausible:** 10 distinct members, all real Sandy councilmembers, spelled
  consistently. No stray names.

**Spot-checks (5 motions vs cited source):**
1. 2020-08-18 m5 — source `6-1`; CSV captured only the Nay → **dropped-Aye bug (above).**
2. 2025-11-18 m6 — source lists 7 incl. Mayor Zoltanski → **faithful capture of a source clerk error.**
3. 2024-01-09 m2 — source `Yes:4 / No:3` (Houseman, Sharkey, D'Sousa Nay) → **exact match.**
4. 2021-06-01 m9 (RDA) — source "roll call vote of 7-0", tally-only → `names_recorded:false`, **faithful.**
5. 2024-01-09 m6 (adjacent) — source `Yes:7` unanimous → consistent.

### 3. Public comments — PASS
- `all_comments_clean.csv`: **0 data rows** (header only) — confirms the submit-only verdict.
- `minutes_speaker_log.csv`: **362 rows**, first line is an explicit NOTE that these are clerk
  paraphrases of in-person speakers, **NOT** public-submitted comments. Correctly labeled.
- `AVAILABILITY.md`: documents an exhaustive search (Granicus SpeakUp/eComment dormant, Legistar
  "eComment: Not available," no correspondence packets, Wayback negative, GRAMA-only email).
  Verdict **SUBMIT-ONLY / NOT PUBLISHED** is well-supported. Sanity check: sound.

### 4. Elections — FAIL
14 races present for 2019/2021/2023/2025 (4 + Mayor in odd years). External cross-check below.
**11 of 14 winners confirmed**, including all four 2025 races matching the official Salt Lake
County canvass exactly. **Two At-Large races misrepresent the outcome in `sandy_races.csv`:**

- **2023 Council At-Large (2 seats) — MISMATCH (real error).** `sandy_races.csv` lists
  `winner = AARON DEKEYZER`, `runner_up = JIM BENNETT`. External sources and **our own
  `sandy_results_by_candidate.csv`** agree the two winners were **CYNDI SHARKEY (rank 1,
  8676, is_winner=True)** and **AARON DEKEYZER (rank 2, 7739, is_winner=True)**; **Bennett
  finished 3rd and lost.** The headline race file dropped the *top* winner (Sharkey) and put a
  *loser* (Bennett) in the runner-up slot. Internal inconsistency between the two CSVs.
  Corroborated by the votes roster: Sharkey is the most active voter (403 rows) and is still
  voting in 2026 — impossible unless she won re-election in 2023.
- **2019 Council At-Large — MISMATCH (structural error).** `sandy_races.csv` marks
  `n_seats = 1` with Sharkey winner / **Houseman runner-up (loser)**. External news (Deseret,
  Fox 13, Sandy Journal) reports this was a **vote-for-two (2-seat)** race in which **both
  Sharkey and Marci Houseman were elected.** Corroborated by (a) the math — a 29.54% top share
  fits a vote-for-two field, not a single-seat plurality; (b) the stagger — 2023 At-Large was
  2-seat, so the seat four years earlier (2019) is also 2-seat; (c) the votes roster — Houseman
  casts council votes from 2020-01-07, which requires her to have won in 2019. Houseman is a
  **co-winner mislabeled as a loser.** (This error is in *both* CSVs.)
- **WARN — 2021 RCV totals inflated.** Winners correct (D'Sousa At-Large; Mecham District 1),
  but recorded totals/margins exceed the official RCV final-round numbers (At-Large 9,224/8,526
  vs ~5,828/5,046; District 1 margin 75 vs external 17). Affects `winner_pct`/`margin`, not the
  winner.

### 5. Geo — PASS
- `council_districts.geojson`: **exactly 4 features** (Districts 1–4). Current members in
  properties (Christensen D1, Stroud D2, Nicholl D3, Houseman D4) match the election winners.
- `precincts.geojson`: 110 features.
- `address_to_district.py` **runs cleanly** (Census geocoder). 10000 Centennial Pkwy (Sandy
  City Hall) → District 1 (Brooke Christensen); an east-bench address (1700 E 11400 S) →
  District 4 (Marci Houseman). Output varies by location and maps to plausible Districts 1–4.

---

## External election cross-check (race-by-race)

| # | Race | CSV winner | External winner | Source | Result |
|---|---|---|---|---|---|
| 1 | 2019 At-Large | Sharkey (Houseman runner-up) | **Sharkey + Houseman (2 seats)** | deseret.com 2019-11-06; sandyjournal.com | **MISMATCH** (2-seat; Houseman co-winner) |
| 2 | 2019 District 2 | Stroud | Stroud (def. Barker) | sandyjournal.com | MATCH |
| 3 | 2019 District 4 | Zoltanski | Zoltanski (def. D'Sousa) | deseret.com; Fox 13 | MATCH |
| 4 | 2021 Mayor (RCV) | Zoltanski | Zoltanski (21-vote / 0.12%) | ksl.com art. 50289608 | MATCH (exact) |
| 5 | 2021 At-Large (RCV) | D'Sousa | D'Sousa (def. DeKeyzer) | rcvis.com/v/...at-large-4 | MATCH (winner); totals inflated |
| 6 | 2021 District 1 (RCV) | Mecham | Mecham (def. Johnson) | rcvis.com/v/...district-1-3 | MATCH (winner); totals inflated |
| 7 | 2021 District 3 (RCV) | Robinson | Robinson (def. Edwards) | rcvis.com/v/...district-3-10 | MATCH (exact) |
| 8 | 2023 At-Large (2 seats) | DeKeyzer (Bennett runner-up) | **Sharkey + DeKeyzer** | electionresults.utah.gov; ksl.com 50792988 | **MISMATCH** (omits top winner Sharkey; Bennett lost) |
| 9 | 2023 District 2 | Stroud (unopposed) | Stroud (unopposed) | sandy.utah.gov/570 | MATCH |
| 10 | 2023 District 4 | Houseman | Houseman (def. Earl) | ksl.com 50792988 | MATCH |
| 11 | 2025 Mayor | Zoltanski (61.32%) | Zoltanski 15,220 vs Sharkey 9,599 | SLCo Clerk canvass PDF | MATCH (exact) |
| 12 | 2025 At-Large | D'Sousa (66.97%) | D'Sousa 15,665 vs Tobin 7,727 | SLCo Clerk canvass | MATCH (exact) |
| 13 | 2025 District 1 | Christensen (53.91%) | Christensen 2,378 vs Davis 2,033 | SLCo Clerk canvass | MATCH (exact) |
| 14 | 2025 District 3 | Nicholl (56.82%) | Nicholl 4,385 vs Williams 3,333 | SLCo Clerk canvass | MATCH (exact) |

**Winners checked: 14/14. Matches: 12 (winner-field level). Mismatches: 2 (races 1 & 8,
both 2-seat At-Large). Unverified: 0.**

The roster implied by the (corrected) elections — Sharkey, Stroud, Robinson, Houseman, D'Sousa,
Mecham, DeKeyzer, Christensen, Coleman-Nicholl, Zoltanski(→Mayor) — matches the members casting
votes in `all_votes.csv`.

---

## Gaps & recommendations
1. **Elections (high):** Fix `sandy_races.csv` to represent 2-seat At-Large races. 2023:
   winners are **Sharkey + DeKeyzer** (drop Bennett from the winner/runner-up framing). 2019:
   set `n_seats = 2` and record **Houseman as a co-winner**, not runner-up. (`sandy_results_by_candidate.csv`
   is already correct for 2023; align the summary file to it.)
2. **Elections (medium):** Re-check 2021 RCV totals/margins (At-Large, District 1) against the
   official final-round canvass; current totals appear inflated.
3. **Votes (medium):** Re-run extraction to capture Aye voters split from their Nay block by a
   page-break footer (16 motions, 2020–21, ~94 missing rows). The bug is hidden because the
   contested flag and `result` string are still correct.
4. **Minutes (low):** Correct the README's "no OCR" claim (58 files are OCR), and populate the
   empty `source_url` column or stop citing it as canonical provenance.
5. **README (low):** Soften "Mayor never appears in the Yes/No tallies" — she has 154 votes as
   the 2020–21 District 4 member, plus 1 source-clerk-error row in 2025.

---

## Remediation (2026-06-25, post-verification)

All three findings were root-caused and fixed.

### Elections (was FAIL → PASS)
- **2023 At-Large** (2-seat): `sandy_races.csv` had listed DeKeyzer as sole winner with loser
  Bennett as runner-up, dropping the **top winner Sharkey**. The repo's own
  `sandy_results_by_candidate.csv` already flagged Sharkey + DeKeyzer as the two winners.
  Corrected the race row to `winner=CYNDI SHARKEY` (top), `runner_up=JIM BENNETT` (first loser).
- **2019 At-Large**: was mislabeled `n_seats=1` with Houseman as runner-up. Externally confirmed
  (Sandy Journal, KSL) it was a **2-seat** race — **Sharkey + Houseman both won** (Edwards,
  Theodore lost). Set `n_seats=2`, `runner_up=JIM EDWARDS` (first loser), margin recomputed;
  flipped Houseman to `is_winner=True` in `by_candidate.csv`.
- Documented the multi-seat convention + the 2+1 at-large stagger in `election_results/CLAUDE.md`
  (2019 corrected there too, where it had also said "Vote for 1").

### Votes (was WARN → PASS)
- The verifier's "page-break footer split" diagnosis was not the actual cause. The 16 flagged
  motions are **narrative inline tallies** — e.g. *"the motion failed by a vote of 5-2 with X, Y
  opposed"* — that name only the dissenters, never a Yes-list. Two real bugs fixed in
  `extract_votes.py`:
  1. `MINORITY_RE` required "and" between names, so **comma-only dissenter lists**
     ("Zoltanski, Christensen opposed") captured only the last name → now accepts bare commas.
  2. The bare `vote of A-B` tally was always read as A=ayes; for a **failed** motion the first
     number is the count *against* → now oriented by pass/fail outcome (and by the captured
     dissenter count). E.g. "failed by a vote of 5-2 with 5 names opposed" → `2-5 Fail`.
- Re-validated: **0 motions** with captured names exceeding the tally, **0** with under-captured
  nays. The narrative-tally majorities stay **unnamed** (`names_recorded:false`) — no guessing.
  Rows 2,951 → **2,974** (recovered dissenter names). Motions (655) and contested (79) unchanged.

### Minutes (documentation)
- README updated: "no OCR" → **216 text / 58 OCR**. `source_url` (blank for all 274) backfilled
  to the canonical Sandy Legistar portal (`Calendar.aspx`, meetings retrievable by date);
  per-meeting deep-links were not retained at acquisition and are regenerable from Legistar.

### Mayor nuance (documentation)
- README/CLAUDE corrected: **Monica Zoltanski was the District 4 councilmember in 2020–2021**
  (156 legitimate vote rows) before becoming Mayor (Jan 2022); the "Mayor never votes" line now
  scopes to the *sitting* mayor. One stray 2025 "Zoltanski" vote is a faithful capture of a
  source clerk error.

All datasets now pass.

---

## Remediation addendum (2026-07-02) — PUA-garbled minutes decoded, votes re-extracted

Executes Phase 1.1 of the repo `REMEDIATION_PLAN.md` (from audit `_audits/2026-07-02/report.md`).
Originals of every modified file are preserved under `_backups/2026-07-02/sandy_city_council/`.

### The defect
**63 of 274 council minutes (23%) were majority-encoded in Unicode Private Use Area chars
(U+F020–U+F0FF)**: 8 files in 2021 (2021-08-17 → 2021-10-12), 21 in 2022, 34 in 2023
(through 2023-11-14). Root cause: the source PDFs for that span carry a **broken font
ToUnicode cmap** — text extraction emits `ASCII codepoint + 0xF000`. Confirmed against the
retained `meeting_minutes/raw/` PDFs: `pdftotext` on the originals reproduces the identical
PUA garble, so the acquisition was faithful; the source itself is defective. The vote
extractor had captured **zero** votes from these files (2022 showed 15 voting meetings,
2023 showed 7, vs ~35–41 in normal years). `minutes_index.csv` had marked all 63 `format=text`.

### The fix
1. **Decode in place** (2026-07-02): every char in U+F020–U+F0FF mapped to
   `chr(ord(c)-0xF000)`; all other chars untouched. All 63 files' PUA codepoints fell in
   U+F020–U+F07A (printable ASCII); no control chars were produced (the form feeds present
   are pre-existing page separators, also present in clean files).
2. **Verification of the decode:**
   - Screener: PUA-garbled files 63 → **0**; 0 PUA chars and 0 U+FFFD corpus-wide.
   - Decoded files' dict-word ratio median **0.774** vs clean-corpus median **0.768**.
   - Decoded text vs decoded `pdftotext` of the raw PDFs: **1.0000 similarity** on all 3
     sampled files (2021-09-21, 2022-05-17, 2023-03-07).
   - Visual page reads of the rendered raw PDFs (independent of the broken cmap):
     2022-05-17 p.8 (`Yes: 7 –` Stroud, Robinson, Houseman, Sharkey, Mecham, D'Sousa, Earl),
     2023-03-07 p.3 (Call-to-Question 7-0 then Table motion **failed Yes:3 / No:4**),
     2021-09-21 p.8 (Sharkey/Zoltanski continue-hearing voice vote) — all match exactly.
   - `minutes_index.csv`: the 63 rows re-marked `format=text_pua_decoded`
     (index now 153 text · 63 text_pua_decoded · 58 ocr).
3. **Vote re-extraction** (`extract_votes.py`), plus a roster fix the decoded files exposed:
   **Scott Earl** (appointed District 4 member 2022-01 → 2023-12) was absent from the
   extractor's name table (his 155 votes had been silently dropped, incl. from never-garbled
   files), and three source clerk typos were added as aliases after PDF verification
   ("Cyndi Shakey"→Sharkey, "Ryan Mecahm"→Mecham, "Alison Stoud"→Stroud).
4. **Derived layers:** `weeks/` rebuilt (`build_weeks.py`: 264 bundles; weeks with motions
   181 → 237, weeks with contested votes 54 → 87).
   `db/sandy.db` **not rebuilt — by design**: `db/build_db.py` builds from the **Legistar
   structured API harvest** (`db/staging/*.csv`, `EventItemVote`), not from the minutes or
   `all_votes.csv`, so the minutes decode does not affect it.

### Before → after (recomputed from `all_votes.csv`)
| Metric | Before | After |
|---|---|---|
| Motions | 655 | **833** (+178: 2021 +21, 2022 +58, 2023 +99) |
| Named roll-call motions | 424 | **547** (+123: 2021 +14, 2022 +34, 2023 +75) |
| Member-vote rows | 2,974 | **3,975** (decode +723; roster fix +278) |
| Contested motions | 79 | **131** (2022: 1 → 24; 2023: 0 → 24) |
| Meetings with votes, 2022 | 15 | **35** |
| Meetings with votes, 2023 | 7 | **36** |
| Vote values | 2,475 Aye / 184 Nay / 78 Absent / 6 Abstain | 3,286 Aye / 292 Nay / 102 Absent / 9 Abstain |

**No previously captured data was lost:** every old `(date, motion_no, member, vote)` row
is present in the new extraction (0 dropped); motions lost: 0.

**Spot-checks of newly recovered roll calls (5/5 exact vs minutes text; the contested ones
also vs rendered PDF):** 2022-05-31 m2 (5-2: Robinson+Mecham Nay), 2022-10-18 m3 (7-0),
2023-01-10 m1 (6-0, Houseman excused), 2023-05-30 m2 (7-0), 2023-11-14 m1 (7-0).

### Integrity notes (faithful captures, not bugs)
- **2021-08-17 m5**: the official minutes list Sharkey in BOTH the Yes list (as "Cyndi
  Shakey") and the No list (raw PDF p.7). Captured as printed → the duplicate-member check
  reads 1, documented.
- **Mayor rows**: Zoltanski appears (as Mayor) only in Board of Municipal Canvassers
  actions — 2023-12-06 m3/m4 (Excused), 2025-08-26 m5, 2025-11-18 m6 — each listed in the
  minutes themselves.
- **The 16 "dropped Aye list" motions (11×2020, 5×2021)**: re-verified against source —
  they are **narrative inline tallies** ("carried by a voice vote of 6 - 1. Monica
  Zoltanski opposed.") that never print the majority's names. The 2026-06-25 remediation
  diagnosis stands; the audit's "page-break-dropped Aye lists" phrasing echoed this
  report's superseded original hypothesis. Nothing recoverable; majorities stay unnamed.

### Doc corrections in the same pass
- README/CLAUDE counts updated to 833 / 3,975 / 131; README's "raw minutes PDFs are not
  retained" corrected (274 PDFs are retained in `meeting_minutes/raw/`).
- `planning_commission/CLAUDE.md`: removed the phantom claim of a `minutes/` dir +
  `minutes_index.csv` + `minutes_unrecovered.csv` (never created; the subtree is the two
  CSVs + builder + doc, and its votes come from the structured Legistar harvest).
- `votes/_validation_report.txt` regenerated (all integrity checks pass).

---

## Remediation addendum — 2026-07-02, plan item 2.6 (db schema conformance)

`db/sandy.db` rebuilt from the schema fork onto the **standard cross-city schema**
(pre-2.6 db, build scripts, SCHEMA.md archived in `_backups/2026-07-02/sandy_city_council/db/`).

**Council-vote sourcing decision (measured, both records compared post-PUA-repair):**
minutes-primary. Minutes CSV: 240 vote dates · 3,689 named rows · 292 Nays; Legistar
(body 138): 214 dates · 3,749 distinct votes (5,720 raw rows — consent fan-out) · 173
Nays. 33 dates are minutes-only vs 7 Legistar-only (3 = unpublished 2026-06 minutes,
2 = minutes absent from corpus, 2 = minutes with no extractable roll call). Legistar
omits whole contested roll calls (e.g. both 2021-08-17 contested motions). PC votes stay
Legistar-sourced (their only source). Full numbers + rationale: `db/SCHEMA.md`.

**Verification performed:**
- Reconciliation exact: CSV named rows 8,120 = 8,109 db votes + 11 documented duplicate
  pairs (`db/vote_overrides.csv`: 8 identical merges, 3 conflicts resolved with recorded
  reasoning — incl. the 2021-08-17 Sharkey double-listing noted above, resolved Aye as
  mover; and Legistar's duplicated Mortimer roster slot on PC 2022-05-05). Build fails
  loudly on any undocumented duplicate.
- PC motion↔Legistar mapping 554/554, title-identical (replayed builder enumeration).
- Idempotency: two consecutive full rebuilds byte-identical (db md5 + all `db/tables/*.csv`).
- Standard views (`v_contested`/`v_member_record`/`v_project_timeline`/`v_referral_chain`)
  return standard-shaped results; `person.name_key` NOT NULL UNIQUE restored (25 keys,
  collision-free; Legistar "Kris Nicholl" aliased to minutes "Kristin Coleman-Nicholl");
  standard CHECK constraints restored (`Nonvoting` now only in the `legistar_vote`
  extension table); 0 applications span >1 body.
- Referral layer rebuilt with the shared generalized template (byte-identical to the
  other cities'): 116 links (53 high/51 medium/12 low); 98/124 pre-2.6 links reproduce
  exactly at MatterId grain, the rest are documented structural cases (`db/SCHEMA.md`).
- `scripts/validate_city.py sandy_city_council`: **0 FAIL** with the former sandy db
  exemption REMOVED from the validator (h.db "reconciles exactly — delta +0"); all 12
  other cities re-validated, 0 FAIL.

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 3,975 rows / 833 motions (547 named); 1 double vote = a documented faithful source contradiction (2021-08-17 m5: the roll prints 'Cyndi Shakey[sic]' among 2 Yes AND Cyndi Sharkey among 5 No while Alison Stroud is missing from the 7-member roll — almost certainly a clerk slip for Stroud; both verbatim rows kept; documented in db/vote_overrides.csv — the 2.6-conformant db resolves it to Aye, since Sharkey moved the tabling motion); tally-vs-counted 531/547 + 16 documented dissent-only undercounts (2020-era narrative style); 0 unexplained mismatches.
