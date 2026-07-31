# Verification — West Valley City council data repo

> **Addendum (2026-06-24, post-verification):** The public-comments dataset was
> restructured AFTER this verification ran. The 818 rows this report verified were City
> Recorder paraphrases of in-person speakers — **not** genuine public-submitted written
> comments — and were moved to `public_comments/minutes_speaker_log.csv` (819 rows,
> record-notes only). An exhaustive hunt confirmed WVC publishes **no** written/online
> public comments, so `all_comments_clean.csv` is now empty (see
> `public_comments/AVAILABILITY.md`). All other datasets below are unaffected. The original
> per-row provenance findings for those rows still hold; only their classification changed.

**Date:** 2026-06-24
**Verifier:** independent QA agent (did not build the data).
**Method:** adversarial reconciliation — provenance spot-checks back to source minutes,
full programmatic tally consistency, internal election reconciliation, an **external**
race-by-race election cross-check (web), geo/election join cross-check, and weeks regen.
**External sources cross-checked:** WVC certified results (utah.gov PMN / wvc-ut.gov),
Salt Lake County Clerk canvass, Salt Lake Tribune, Deseret News, West Valley Journal,
ABC4, KSL, and the city's official Members page.

---

## Summary table

| Dataset | Status | Rows | Coverage | Notes |
|---|---|---|---|---|
| Minutes | **PASS** | 465 files = 465 index rows | 2020–2026 (May), all 12 months each full year | All on Tuesdays (464) + 1 Fri strategic session. Distinct, dated, real. |
| Votes | **PASS** | 8,908 (8,384 member + 524 tally); 1,747 motions | derived from all 465 minutes | 0 result-string mismatches across 1,223 named roll-calls; 208 contested re-derived; provenance traced. |
| Comments | **PASS** | 818 clean + 53 dropped audit | 2020-01-07 → 2026-05-26 | Per-year counts match docs exactly; 100% `date_normalized`; 0 exact dupes; 5/5 traced to source. |
| Elections | **PASS** | 14 races, 34 cand, 1,479 precinct | 2019/2021/2023/2025 generals | **14/14 winners externally confirmed**; internal sums reconcile exactly. |
| Geo | **PASS** | 71 precincts, 70 mapped | post-2022 map (2023+2025) | All 70 assignments match election by-precinct; offline address test passes. |
| Weeks | **PASS** | 250 bundles | 2020–2026 | Regenerates cleanly (exit 0); 2 spot-checked bundles match canonical exactly. |

**Overall: PASS.** No fabrication found. All datasets reconciled.

---

## Detailed findings

### 1. Minutes — PASS
- **File count == index:** 465 `.md` files on disk == 465 rows in `minutes_index.csv`. Exact.
- **Coverage:** every month Jan–Dec present 2020–2025; 2026 runs Jan–May (through
  2026-05-26), consistent with the 2026-06-24 recon date. No missing stretch.
- **Cadence finding (not a defect):** 222 Regular + 236 Study + 7 other. In 2020–2022 the
  Council met on **most Tuesdays (1st–4th)**, ~40 Regular/yr; by 2025 it settled to the
  2nd/4th-Tuesday cadence (24 Regular). The "2nd & 4th Tuesday" framing in `CLAUDE.md`/
  `recon.md` describes the *current* cadence and **understates** the dense early-period
  schedule — but the extra meetings are genuine, distinct, dated minutes (verified
  2020-01-07/14/21 are three separate meetings), not duplicates.
- **All meetings on Tuesday** (464) except one **Friday** = 2024-02-23 Strategic Planning
  (legitimate special session).
- **Minor provenance gap:** the per-meeting JSON intermediate is missing for the two
  2021-07-06 meetings (463 JSONs for 465 minutes). The votes themselves ARE present and
  correct in `all_votes.csv` (45 rows for that date, including the documented motion-3
  discrepancy), so the canonical table is complete; only the structured intermediate
  wasn't re-emitted. Low impact — flagged for regen hygiene.

### 2. Votes — PASS (provenance + tally both verified)
- **Counts reconcile exactly** to `CLAUDE.md` and `_validation_report.txt`:
  8,908 rows = 8,384 member-vote + 524 tally-only; 1,747 motions = 1,223 named + 524 tally;
  **208 contested** (≥1 Nay/Recuse/Abstain) — independently re-derived, identical.
- **Result-string consistency:** programmatically checked every one of the 1,223 named
  roll-calls — the `A-B` in `result` matches the derived Aye/Nay count in **0 mismatches**.
  Tally-only motions correctly carry blank `member`/`vote` (no guessed voters).
- **Source paths:** all 460 distinct `source` paths exist on disk (resolve relative to
  `meeting_minutes/`).
- **Provenance spot-checks (8 random named motions traced to source text):**
  - 2022-07-12 m2 Ord 22-27 `5-1 Majority`: source roll call shows Fitisemanu Absent,
    Nordfelt No, 5 Yes → exact match.
  - 2021-05-11 m2/m3 Ord 21-23: source has TWO sequential motions — "to deny" (3-3 Failed,
    Lang Absent) and "to continue" (6-0, Lang Absent). The parser correctly **split** them
    and assigned every per-member vote as printed. No vote stolen across motions.
  - Other 6 sampled motions all internally consistent.
- **The 3 documented "Unanimous-over-dissent" source discrepancies** verified at source:
  - 2023-01-24 m5 Res 23-03: source roll call shows **Harmon "No"** while minutes printed
    "Unanimous." → CSV honestly recorded `6-1 Unanimous Pass` with Harmon=Nay. The
    verbatim "Unanimous" word is preserved for audit. This is correct, transparent handling
    of an official clerical error — **not** fabrication.
- **Vote tokens** clean: Aye/Nay/Absent/Recuse + blank-for-tally. No Abstain used (fine).
- **Member set:** exactly the 10 expected canonical names, no strays/misspellings.

### 3. Roster sanity — PASS
- `_roster_by_year.json` is a stable 7 members/year. Transitions match the election
  stagger: Bigelow(Mayor)+Buhler(D2) 2020–21 → Lang(Mayor)+Harmon(D2)+Whetstone(D3) 2022;
  Fitisemanu(D4) → Wood(D4) at 2025.
- **Vote-casters vs election winners:** every caster is either a 2019–2025 winner OR a
  pre-2020 incumbent seated before the data floor (Ron Bigelow = Mayor, Steve Buhler = D2 —
  correctly *not* in the captured 2019+ cycles). "William Whetstone" (votes) == "Will
  Whetstone" (ballot) — same person. No fabricated councilmember.
- *Minor doc drift:* roster JSON places Fitisemanu through **2024** and Wood from **2025**,
  while `meeting_minutes/CLAUDE.md` says "Fitisemanu 2020–2023 / Wood 2024+". The roster
  JSON (driven by who actually appears in roll calls) is authoritative; Wood was seated via
  the Jan-2025 D4 vacancy appointment (see election note below). Cosmetic only.

### 4. Comments — PASS
- 818 clean rows; per-year counts (55/114/144/134/195/134/42) match `CLAUDE.md` exactly.
- `date_normalized` 100% populated; range 2020-01-07 → 2026-05-26 (in range).
- `source` = `in_person_minutes` for all 818; `has_attachment` = False for all (consistent
  with "no separate written-comment portal").
- All `source_file` paths exist on disk; **0 exact duplicates** (date+name+comment).
- **Dropped-rows audit exists** (`all_comments_dropped.csv`, 53 rows) and matches documented
  reasons: official_or_staff 39, official_continuation 8, no_comments_procedural 3,
  empty_placeholder 2, orphan_continuation 1.
- **Provenance (5 random named comments traced to source):** Lenore Gonzalez (2023-03-28),
  DJ Heslington (2021-11-23), Kesa Vakapuna (2023-07-18), Jim Vesock (2025-03-25 &
  2020-11-10) — speaker name AND a distinctive phrase appear verbatim in the cited minutes
  in all 5. No fabrication.

### 5. Elections — PASS (internal + external)
- **Internal reconciliation (0 problems):** for all 14 races, the `is_winner` candidate ==
  `winner`, winner_votes match, `total_votes` == sum of candidate votes, runner-up == 2nd-
  rank candidate, and `margin_votes` == winner−runner-up. **Every** per-precinct sum equals
  its candidate total (0 mismatches across 1,479 precinct rows).
- **External cross-check: 14 of 14 winners CONFIRMED** (see race-by-race table below).
- Implied roster matches vote-casters and the city's current Members page.

### 6. Geo — PASS
- 71 precinct polygons (WVC-prefixed = GIS join key), 70 mapped to districts
  (D1:15, D2:19, D3:14, D4:22), source years 2023+2025. CRS84 (= true EPSG:4326).
- **Cross-check:** all 70 precinct→district assignments match the election by-precinct
  district contests exactly (0 mismatches) — the map is derived from, and consistent with,
  the election source of truth.
- **Offline address test:** City Hall 40.6942,-111.9581 → WVC027 → District 2, matching the
  documented verified-test table. (Address geocoding requires internet; the lat/lon path is
  offline and passes.)

### 7. Weeks — PASS
- `python3 build_weeks.py` runs clean (exit 0): "Built 250 week bundles … comments 216 |
  votes 246 | minutes 250."
- The repo had a **stale macOS-style `index 2.csv`/`index 2.md` duplicate** (byte-identical
  to `index.csv`) and 251 dated folders; the deterministic regen produced a clean **250**
  bundles matching `index.csv` (250 rows) and removed the stray copies. No data lost.
- **Two bundles spot-checked vs canonical, both exact:**
  - 2026-02-10: votes 44==44, comments 4==4.
  - 2023-04-11 (random): votes 30==30, comments 6==6.

---

## External election cross-check (race by race)

All 14 WVC races independently confirmed against a source **other than** the parsed file.
Percentages match to within rounding wherever a line-item figure was available; where only
raw counts/news reporting were found, the **winner** is firmly confirmed.

| Race | Claimed winner (%) | External confirmation | Source | Result |
|---|---|---|---|---|
| 2019 At-Large | Don Christensen (56.66%) | confirmed winner | Deseret News 2019 tallies; WVC certified | **MATCH** |
| 2019 District 1 | Tom Huynh (65.64%) | Huynh over Tavo | Deseret News 2019 | **MATCH** |
| 2019 District 3 | Karen Lang (70.32%) | Lang over Lynch | Deseret News 2019 | **MATCH** |
| 2021 Mayor | Karen Lang (58.54%) | Lang 58.54% vs Buhler 41.46% | Salt Lake Tribune | **MATCH** |
| 2021 At-Large | Lars Nordfelt (59.59%) | Nordfelt 59.59% vs Vesock | Deseret News 2021 | **MATCH** |
| 2021 District 2 | Scott Harmon (59.39%) | Harmon ~59% vs Bell | West Valley Journal | **MATCH** |
| 2021 District 4 | Jake Fitisemanu Jr (53.45%) | Fitisemanu 53.45% vs Curtis | Salt Lake Tribune | **MATCH** |
| 2023 At-Large | Don Christensen (58.41%) | Christensen 6,703 (58.41%) | SL County canvass; KSL | **MATCH** |
| 2023 District 1 | Tom Huynh (54.52%) | Huynh ~55% vs Lefevre | West Valley Journal | **MATCH** |
| 2023 District 3 | Will Whetstone (56.57%) | Whetstone ~57% vs Roggenbuck | West Valley Journal | **MATCH** |
| 2025 Mayor | Karen Lang (75.40%) | Lang 8,866 (75.4%) vs Hesleph 2,892 | WVC certified (PMN) | **MATCH** |
| 2025 At-Large | Lars Nordfelt (54.82%) | Nordfelt 6,333 vs Roggenbuck 5,052 | WVC certified; ABC4 | **MATCH** |
| 2025 District 2 | Scott L. Harmon (61.53%) | Harmon 2,202 (61.5%) vs George | WVC certified | **MATCH** |
| 2025 District 4 | Cindy Wood (63.51%) | Wood 2,231 (63.5%) vs Amosa | WVC certified | **MATCH** |

**Current council roster (2026)** confirmed on the city's official Members page
(wvc-ut.gov/97/Members): Mayor Lang; At-Large Nordfelt + Christensen; D1 Huynh; D2 Harmon;
D3 Whetstone; D4 Wood — exact match to the repo's implied roster.

**2025 At-Large "coin toss / runoff" — RESOLVED as a non-issue.** Nordfelt won the November
2025 At-Large *general election* outright (6,333–5,052, ~10 pts); there was no tie, coin
toss, or runoff. The coin-toss reporting refers to the separate **January 2025 City Council
appointment** to fill the **District 4 vacancy** left by Jake Fitisemanu (who resigned to
join the Utah House) — a council vote, not a public election. The repo's
`election_results/CLAUDE.md` already documents this correctly. This also explains why Cindy
Wood (D4) first appears voting in early 2025 before winning the Nov-2025 general: she was
the Jan-2025 appointee, then elected.

---

## Gaps & recommendations

1. **(Low) Two missing per-meeting JSONs** for 2021-07-06 (Regular + Study). The votes are
   present and correct in `all_votes.csv`; re-run `extract_votes.py --force` to re-emit the
   intermediates so the JSON count (463) equals the minutes count (465).
2. **(Cosmetic) Stale weeks index duplicates removed.** `index 2.csv`/`index 2.md` were
   byte-identical leftovers; the regen cleaned them. Treat `weeks/` as fully derived — never
   hand-edit, always regenerate.
3. **(Doc) Cadence wording.** `recon.md`/`CLAUDE.md` say "2nd & 4th Tuesday." True for the
   recent period only; 2020–2022 met on most Tuesdays (~40 Regular/yr). Consider a one-line
   note so the ~465 count isn't mistaken for over-collection.
4. **(Doc) Roster year boundary.** `meeting_minutes/CLAUDE.md` says Fitisemanu "2020–2023 /
   Wood 2024+"; the roll-call-driven roster JSON shows the handoff at the **2025** boundary
   (Wood seated via Jan-2025 D4 appointment). Align the prose with the JSON.
5. **(Scope, documented) Public comments are Recorder paraphrases**, in-person only, no
   written/eComment channel exists for WVC — already disclosed; not a gap, just a usage
   caveat (don't quote as verbatim).
6. **No fabrication detected** in any spot-check (votes or comments), and no stray/invented
   members, dates, or motions surfaced.

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 9,655 rows / 1,942 motions (1,320 named, 622 tally-only); 0 schema/date/vocab defects, 0 malformed groups, 0 double votes; tally-vs-counted 1,320/1,320; 0 unexplained mismatches. weeks/ regenerated (mtime staleness only; 9,655 weekly vote rows unchanged, sums verified).
