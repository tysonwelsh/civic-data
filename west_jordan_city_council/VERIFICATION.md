# Verification — West Jordan, Utah council data repo

> **Addendum (2026-07-02, audit-driven repair — duplicate 2022-06-22 council minutes):** The
> repo-wide audit (Phase 1.9) confirmed one document defect, now repaired (originals in
> `_backups/2026-07-02/west_jordan_city_council/`):
> **2022-06-22 double-parse** — PrimeGov published the SAME council-minutes PDF under two
> meeting templates (`CompiledDocument?meetingTemplateId=268` and `=737`; both fetched
> 2026-07-02 and byte-identical, md5 `f241766c1cd63601ed2105c9a7816b08`), so the build
> parsed one meeting twice: `2022-06-22_city-council-meeting.md` and
> `2022-06-22_city-council-regular-meeting.md` had byte-identical bodies (body md5
> `a27b37c045662c3d835d394ebbfae6c5`; they differed only in the injected `#` title line).
> Kept `2022-06-22_city-council-meeting.md` — the document titles itself "MINUTES OF THE
> CITY OF WEST JORDAN / CITY COUNCIL MEETING" — and removed the regular-meeting duplicate
> file + its `minutes_index.csv` row + its vote JSON. The same date's separate work-session,
> RDA, and MBA minutes are distinct documents/meetings and were untouched.
> **Vote-table delta:** `all_votes.csv` 6,783 → **6,705** rows (−78, exactly the duplicate
> meeting's 12 named motions × their member rows; every remaining row verified identical
> field-for-field to the pre-repair file). Motions incl. tally-only 1,353 → 1,334 (Council
> 1,176 → 1,157); contested Council 153 → 150. `votes/_validation_report.txt` regenerated —
> same 6 flagged motions (all pre-documented source typos), 0 new.
> `db/civic.db` rebuilt (267 meetings · 293 applications · 1,163 motions · 7,011 votes ·
> INTEGRITY OK; motion count −12, vote count −78). **Referrals reproduce link-for-link:**
> all 21 links (8 high / 9 medium / 4 low) carry identical (primary app_key, related
> app_key, method, confidence, shared_address, gap) before/after; only 4 `subject_score`
> values moved ±0.001 (IDF weights shift as the duplicate's 2 singleton applications leave
> the corpus). `db/referral_overrides.csv` is empty — no id remap needed. `weeks/`
> regenerated (187 bundles; only the 2022-06-28 bundle + index changed). Corpus screener:
> `duplicate_bodies 0/321`. Counts corrected in `README.md`, `CLAUDE.md`,
> `meeting_minutes/CLAUDE.md`, and `db/SCHEMA.md`.

> **Addendum (2026-06-25, post-verification fix → now PASS):** The PARTIAL verdict below was
> driven by a vote-extraction bug. It has been **fixed and re-run**: the parser now falls
> back to the tabular roll-call form, recovering **all of 2021 (0→861 rows)** and most of
> 2020 (272→1,022) — `all_votes.csv` went **3,536 → 5,908 rows** (1,176 motions, 153
> contested). Also fixed: the "Sophie Bennett" → **Rob Bennett** name (16 rows), page-break/
> form-feed name-drops, and the missing `votes/_validation_report.txt` (now written). The 5
> remaining tally mismatches are all verified source clerical typos, parsed verbatim and left
> flagged (none invented). All other datasets passed clean in the original review (13/13
> election winners externally confirmed, no fabrication). Counts in the docs reflect the fix.

**Verifier:** independent verification agent (did not build the data)
**Date:** 2026-06-25
**Method:** adversarial. CSV rows counted with the Python `csv` module (never `wc -l`).
Provenance spot-checked back to source minutes/packets; vote tallies re-derived from the
committed per-meeting JSONs; elections cross-checked against external sources
(official Utah election-results API, West Jordan city newsroom/council pages, West Jordan
Journal, Salt Lake Tribune); weeks regenerated in a temp copy.

---

## Summary table

| dataset | status | rows | coverage | notes |
|---|---|---|---|---|
| minutes (`minutes_index.csv` + .md) | **PASS** | 251 index = 251 on disk | 2020–2026, all PrimeGov, all `source_url` present | 250 pdf-text + 1 docx-text; index↔disk paths reconcile 1:1 |
| votes (`all_votes.csv`) | **PARTIAL** | 3,536 member-votes / 522 named motions | only 103 of 251 meetings yield member-votes; **2021 = 0** | **Silent gap: all 27 of 2021's meetings + some 2020 meetings have named tabular roll-calls in source that were NOT extracted (~850+ recoverable member-votes lost).** No fabrication; captured rows are accurate. 3 minor data defects (below). |
| genuine_comments (`all_comments_clean.csv`) | **PASS** | 28 | 2022 only (Welby West rezone); `source=agenda_packet` 100% | 4/4 spot-checks found verbatim in retained raw packet PDF; 0 minutes-paraphrase leaks; `date_normalized` 100% populated |
| speaker_log (`minutes_speaker_log.csv`) | **PASS** | 238 | 2020–2026 | clearly labeled "NOT public-submitted comments"; each row traces to a minutes .md; properly separate from clean comments |
| elections (`wjordan_*.csv`) | **PASS** | 13 races / 37 cand / 1,978 precinct | 2019/2021/2023/2025 | every winner externally confirmed; precinct sums reconcile to candidate totals (0/37 mismatch); at-large seat-3 margins (326, 79) exact |
| geo (`precinct_to_district.csv` + geojson) | **PASS** | 96 precincts / 95 polygons / 4 districts | current (2023) map | true EPSG:4326 lon/lat confirmed; D1=25 D2=21 D3=27 D4=23 matches docs |
| weeks (`weeks/`) | **PASS** | 186 bundles + index | 2020–2026 | regenerates cleanly (186, 0 conflict-copies); spot-check bundle == canonical filtered to week (identical) |

**Overall: PARTIAL** — driven entirely by the 2021 vote-extraction gap. Everything that is
present reconciles to source with **no fabrication detected**.

---

## Findings per dataset

### Minutes — PASS
- `minutes_index.csv` = **251 rows** (csv module); **251** `.md` files on disk. All 251
  index `path` values exist on disk; 0 orphans either direction.
- Per-year on disk == per-year in index: 2020=35, 2021=27, 2022=42, 2023=39, 2024=40,
  2025=48, 2026=20.
- All 251 rows: `source=primegov`, a valid `http` `source_url` (regenerable — raw PDFs not
  retained, as documented). 120 rows carry a `packet_url` (= the 120 packets the comment
  harvest scanned). Formats: 250 `pdf-text`, 1 `docx-text`.
- Bodies: "City Council Meeting/Regular Meeting" plus "Committee of the Whole" study
  sessions and a few joint work sessions — all legitimately council body.
- Coverage is plausible for 2nd/4th-Tuesday cadence across 2020–2026; 2026 partial
  (year in progress) is expected, not a gap.

### Votes — PARTIAL (one material gap + 3 minor defects; no fabrication)
- **Counts reconcile internally.** `all_votes.csv` = **3,536** member-vote rows / **522**
  distinct named motions. Summing member-votes across all 251 committed JSONs = **3,536**,
  522 named motions — `all_votes.csv` is a faithful projection of the JSONs.
- **Vote-value distribution:** Aye 3,183 · Nay 176 · Absent 172 · Abstain 4 · Recuse 1.
- **Mayor Burton:** never appears as a voter (confirmed by scan). Council = 7 voting
  members; rosters per term match election winners.
- **Roster (13 names) is clean and plausible** — Jacob, Whitelock, Green, Bloom, Lamb,
  Shelton, Bedore, McConnehey, Pack, Worthen, Harris, Wignall, + "Bennett". By-year sets
  track the elected council correctly.
- **Provenance spot-check (8 random rows): all 8 PASS.** Each member/vote/result was found
  verbatim in the cited `source` minutes file. Examples verified line-for-line:
  - 2023-11-01 m1 Whitelock=Aye, 6-0 (Eli Mitchell Way renaming) ✓
  - 2024-04-10 m2 Shelton=Absent, 6-0 (Ord 24-19, ABSENT: Kent Shelton) ✓
  - 2026-03-24 m2 Lamb=Aye, 6-0 (Res 26-007) ✓
  - 2020-05-13 m3 Pack=Yes, 7-0 (Res 20-29, roll call) ✓
- **All 103 distinct `source` paths in `all_votes.csv` exist on disk** (0 missing).
- **Tally-vs-result consistency:** of 522 named motions, **478 reconcile exactly**; **44
  mismatch**, broken down as:
  - **38 under-counts** — captured fewer names than the tally (e.g. `7-0 Pass` with 5 ayes).
    Root cause: PDF **page-break headers interrupt the YES list** (e.g. 2020-05-13 has
    "...Page 3" mid-list and dash placeholders `Councilmember Green –` that don't parse).
    Captured names are correct; some members silently dropped. Parse-quality, not fabrication.
  - **3 over-counts** — 2024-03-27 m4, 2023-03-08 m8, 2023-12-20 m7. Inspected 2024-03-27:
    the minutes text literally reads "The motion failed 6-1" while listing **1 YES / 6 NO**
    — a **typo in the source minutes**. The extractor faithfully recorded the verbatim
    result string and the correct per-member votes. Source-side, not a build error.
  - **3 "names_recorded but 0 names"** (2025-04-22, 2024-11-20, 2023-09-27) — a second vote
    block in the same motion was truncated; the motion's first block parsed correctly.
- **Contested motions ≈ 100** (any Nay/Abstain, or a Fail) by the extractor's own logic —
  consistent with the documented "~96."

#### Material gap — 2021 (and some 2020) named roll-calls NOT extracted
- **2021 has 27 minutes files, 192 motions in JSON, and 0 named member-votes** in
  `all_votes.csv`. This is **not** because 2021 lacked roll-calls: 23 of 27 files contain
  "The vote was recorded as follows:" followed by a **tabular** roll-call
  (`Council Chair Jacob   Yes`).
- Root cause (confirmed by reading `extract_votes.py`): in `extract_meeting`, when the
  `VOTE_FOLLOWS_RE` ("vote was recorded as follows") lead-in matches, the code calls only
  `parse_named_block` (which expects `YES:`/`NO:` *labels*) and **never falls back to
  `parse_tabular`**. The 2021 minutes put the tabular roll-call *under* that lead-in, so
  every 2021 motion came out `names_recorded:false`. `parse_tabular` itself works on these
  blocks (verified directly).
- **Quantified loss:** running `parse_tabular` over 2021 recovers **122 named motions /
  ~852 member-vote rows** that are missing from `all_votes.csv`. The same defect also drops
  individual 2020 meetings (e.g. 2020-07-08 → 63 recoverable member-votes not captured).
- **Impact:** `all_votes.csv` is missing roughly **850–900+ member-vote rows (~20% more
  than the current 3,536)**, concentrated in 2021. This is a **silent coverage gap** — it is
  documented nowhere in the repo as a known omission; 2021 simply disappears from the votes
  table. It is *not* "not published" (the data is in the retained source) — it is "not
  retrieved by the extractor."
- **Recommendation:** in `extract_meeting`, when the named-block parse under
  `VOTE_FOLLOWS_RE` finds no names, fall back to `parse_tabular(seg)` before giving up; then
  `--force` re-extract. Also handle the dash-placeholder / page-break continuation so the 38
  under-counts recover their dropped names.

#### Minor data defects (no fabrication, but wrong values)
1. **"Sophie Bennett" is a wrong first name.** The 2023 mid-term appointee (5 vote rows) is
   **Robert "Rob" Bennett**, per the minutes ("appointing Robert Bennett to fill the vacancy
   … invited *him* to join them on the dais") and per the 2025 at-large ballot ("ROB
   BENNETT"). `extract_votes.py`'s `NAME_CANON` maps surname `bennett` → "Sophie Bennett";
   no "Sophie" appears anywhere in the source. Surname-based attribution is correct; the
   canonical full name is wrong. **Fix:** `NAME_CANON["bennett"] = "Robert Bennett"`.
2. **`votes/_validation_report.txt` is referenced in `meeting_minutes/CLAUDE.md` but does
   not exist.** Documentation drift — either generate it or drop the reference.
3. The 3 over-count rows reflect **source typos** in the minutes' result strings (above);
   acceptable to keep verbatim, but worth a note for downstream analysts who diff
   `result` against the name lists.

### Genuine comments — PASS
- `all_comments_clean.csv` = **28 rows** (csv module). All `source=agenda_packet`; all 2022
  (27 from 2022-08-10 packet, 1 from 2022-09-14); all the Welby West / Bowman's Arrow rezone
  email campaign, as documented.
- **0 leaks:** no row sourced from a `.md` minutes file; no minutes paraphrase present.
- `date_normalized` **100% populated**.
- **Provenance spot-check (4 random rows): all 4 PASS** — both retained raw packet PDFs
  (`raw/2022-08-10_packet_tid99.pdf`, `raw/2022-09-14_packet_tid308.pdf`) exist; for each
  sampled comment the sender name **and** a ~50-char comment fragment were found verbatim in
  the `pdftotext` of the packet (Chelsea Sheppard, joe burnett, allison sorenson, Walker
  Masuda).
- **Dropped-rows audit exists and reconciles:** `all_comments_dropped.csv` = **445 rows**,
  every row has a `_drop_reason`. Dominant reasons: `recurrent_correspondence_dup` (297) +
  `dup_within_packet` (134) = the documented re-bundling (≈333 raw artifacts →
  28 unique). The rest: official/vendor/internal-domain/no-resident-signal. Nothing silently
  deleted.
- `packets_scanned.csv` = **120 rows**, all `status=ok`, 15 `had_comments=TRUE`,
  Σ`n_comments`=333. Matches AVAILABILITY.md exactly.
- **AVAILABILITY.md verdict = IN-PACKETS** and documents a genuine exhaustive hunt
  (dedicated page, eComment portal, packet attachments, records archive) — not a glance.

### Speaker log — PASS
- `minutes_speaker_log.csv` = **238 rows** (csv module; line 1 is a `#` NOTE banner, real
  column headers on line 2). Header note explicitly: "MEETING-RECORD NOTES, NOT
  public-submitted comments … clerk paraphrases of in-person speakers."
- Each row carries the originating minutes `.md` `source_file`. Dates span **2020-02-26 →
  2026-04-14**; 2021 present (31 rows) — i.e. 2021 meetings *were* processed for speakers,
  underscoring that the 2021 vote gap is an extractor defect, not a missing-source problem.
- Properly separate from `all_comments_clean.csv`; not merged.
- Minor: the banner-as-row-1 means a naive `csv.DictReader` treats the note as the header —
  consumers must skip line 1. Cosmetic.

### Elections — PASS (external cross-check below)
- `west_jordan_races.csv` = **13 rows**; `west_jordan_results_by_candidate.csv` = **37**;
  `west_jordan_results_by_precinct.csv` = **1,978**.
- **Precinct sums reconcile to candidate totals: 0 mismatches / 37 candidate rows.**
- At-large Vote-for-3 modeled correctly: `n_seats=3`, `is_winner=True` for rank ≤ 3;
  seat-deciding margins recorded — 2021 Bloom-over-Lamb **326** (1.3%), 2025 Wignall-over-
  Sotelo **79** (0.24%). Both exact vs external sources.
- **Elected roster ↔ voters:** the members appearing in `all_votes.csv` per term match the
  election winners (Mayor Burton never votes; council = the 7 elected seats).

### Geo — PASS
- `precinct_to_district.csv` = **96 rows** (D1=25, D2=21, D3=27, D4=23; 92 `source_year=2023`
  + 4 `gis` backfill) — matches `geo/CLAUDE.md` exactly.
- `precincts.geojson` = 95 features; sample coordinate `[-112.02, 40.64]` confirms **true
  EPSG:4326** Utah lon/lat (the documented UTM-reprojection was applied). `council_districts.geojson`
  = 4 district polygons. The 96-vs-95 (mail/edge precincts without polygons) is documented.

### Weeks — PASS
- `weeks/` = **186 bundles** + `index.csv` + `index.md`; **0 iCloud conflict-copies**.
- **Clean regeneration:** copied the repo to a temp dir, ran `python3 build_weeks.py` →
  "Built 186 week bundles", 0 conflict-copies, and the regenerated `weeks/2023-10-31/votes.csv`
  is **byte-identical** to the committed one.
- **Bundle == canonical filtered to week:** `weeks/2023-10-31/votes.csv` (49 rows) exactly
  equals `all_votes.csv` filtered to `week_end == 2023-10-31` (49 rows, identical
  date/motion/member/vote tuples). Week key = the Tuesday that *ends* the council week
  (`MEETING_WEEKDAY=1`), correctly bucketing the Wednesday 2023-11-01-dated meeting's votes
  (which carry the 2023-10-25 meeting date) onto the right grid.
- Only 102 of 186 weeks have votes — consistent with the 103 vote-source meetings, and it
  also surfaces the 2021 gap (2021 weeks have minutes but no votes).

---

## External election cross-check (race-by-race)

Sources: **official Utah election-results API** (`electionresults.utah.gov`, Salt Lake
County feed — queried directly for 2023 & 2025), **West Jordan city newsroom / "Your City
Council" page**, **West Jordan Journal**, **Salt Lake Tribune**, **Utah PMN**. Independent
of the parsed SOVC files. The agent's official-API vote totals **matched the repo's figures
exactly** where comparable (e.g. Burton 8,735; Lamb 2,417; Wignall seat-3 margin = 79).

| year | contest | winner(s) in data | external source(s) | verdict |
|---|---|---|---|---|
| 2019 | Mayor | Dirk Burton (def. Jim Riding) | SL Tribune 11/6/2019; WJ Journal | **MATCH** |
| 2019 | At-Large (Vote-for-1) | Kelvin Green (def. Mikey Smith) | WJ Journal (early results + oath 1/2020) | **MATCH** |
| 2019 | District 1 | Chris McConnehey (def. Richards) | WJ Journal | **MATCH** |
| 2019 | District 2 | Melissa Worthen (def. Price) | WJ Journal | **MATCH** |
| 2019 | District 3 | Zach Jacob (def. Martz) | WJ Journal | **MATCH** |
| 2019 | District 4 | David Pack | WJ Journal oath article; Utah PMN | **MATCH** |
| 2021 | At-Large (Vote-for-3) | Whitelock, Green, Bloom (4th = Chad Lamb) | WJ City **2021 certified canvass** | **MATCH** (4th = Lamb, +326 confirmed) |
| 2023 | Mayor | Dirk Burton (def. Whitelock) | **official Utah API** 8,735 v 5,710 | **MATCH** |
| 2023 | District 1 | Chad Lamb (def. Rulon Green) | official Utah API 2,417 v 1,328 | **MATCH** |
| 2023 | District 2 | Bob Bedore (def. Gary Leany) | official Utah API 2,026 v 1,714 | **MATCH** |
| 2023 | District 3 | Zach Jacob (def. Sterling Morris) | official Utah API 1,913 v 994 | **MATCH** |
| 2023 | District 4 | Kent Shelton (def. David Pack) | official Utah API 2,207 v 1,652 | **MATCH** |
| 2025 | At-Large (Vote-for-3) | Whitelock, Harris, Wignall (4th = Sergio Sotelo) | **official Utah API** + WJ newsroom Dec 2025 | **MATCH** (seat-3 margin = 79 exact) |

- **Current council (2026):** Mayor **Burton**; D1 **Lamb**, D2 **Bedore** (Chair), D3
  **Jacob**, D4 **Shelton**; At-Large **Harris**, **Whitelock**, **Wignall** — matches the
  official "Your City Council" page and `all_votes.csv` 2026 roster. **MATCH.**
- **Mayor-does-not-vote confirmed externally:** West Jordan adopted the council-mayor
  ("strong mayor") form in 2017 (SL Tribune 11/24/2017). Under Utah Code Title 10 Ch. 3b the
  mayor is the executive, not a member of the legislative council, and does not vote — exactly
  how the data models it (Burton absent from all 3,536 vote rows).
- **No winner mismatches, no off-by-more-than-rounding margins, no missing modern race.**
- **Caveat:** 2019 predates the live state tabulator (API ~2021+), so 2019 rests on
  concurring news sources (WJ Journal + SL Tribune) rather than a government API — well
  corroborated but not canvass-API-confirmed. The 2025 API snapshot showed `isWinner=null`
  (tabulator never flagged winners) at 80/94 units, but the city's December newsroom post and
  the sworn-in council confirm the same three winners — settled, not merely leading.

---

## Gaps & recommendations (priority order)

1. **[Material] Recover 2021 (and stray 2020) named votes.** ~850–900 member-vote rows are
   missing because `extract_meeting` doesn't fall back to `parse_tabular` under the
   "vote was recorded as follows" lead-in. Fix the fallback, `--force` re-extract, rebuild
   `all_votes.csv` and `weeks/`. Until fixed, treat any "votes by year" or "votes by member"
   analysis as **missing 2021 entirely** — this is currently undocumented.
2. **[Minor] Fix the "Sophie Bennett" → "Robert Bennett" name mapping** (5 rows) in
   `NAME_CANON`.
3. **[Minor] Page-break / dash-placeholder name drops** cause 38 named motions to under-count
   their YES list. Stitch continuation lines across "Page N" headers and parse the dash
   placeholders, or at minimum flag motions where `len(aye)+len(nay) != tally`.
4. **[Cosmetic] `votes/_validation_report.txt`** referenced in CLAUDE.md is absent — generate
   it or remove the reference. Consider documenting the 3 source-typo result strings.
5. **[Doc] Note the 2021 vote gap explicitly** in `meeting_minutes/CLAUDE.md` until #1 is
   fixed, so the absence isn't mistaken for "2021 had no recorded votes."

No fabrication was found in any dataset: every spot-checked vote, comment, winner, and roster
member traces to a real source document, and every count reconciles. The single reason votes
is PARTIAL rather than PASS is the undocumented 2021 extraction gap.

---

```json
{"overall":"PARTIAL","by_dataset":{"minutes":"PASS","votes":"PARTIAL","genuine_comments":"PASS","speaker_log":"PASS","elections":"PASS","geo":"PASS","weeks":"PASS"},"fabrication_found":false,"election_crosscheck":{"races_checked":13,"mismatches":[]},"key_findings":["All 13 election winners externally confirmed (official Utah API for 2023/2025, news+canvass for 2019/2021); at-large seat-3 margins 326 and 79 exact; Mayor Burton correctly excluded from all 3,536 votes.","8/8 vote rows and 4/4 comments spot-checked to source with zero fabrication; all source paths exist on disk; counts reconcile (votes 3,536/522, comments 28, dropped 445).","MATERIAL GAP: 2021 has 27 minutes + 192 motions but 0 member-votes in all_votes.csv — the extractor never falls back to parse_tabular under the 'vote was recorded as follows' lead-in, silently dropping ~850-900 recoverable 2021/2020 member-vote rows (undocumented).","Data defect: appointed member recorded as 'Sophie Bennett'; source and 2025 ballot show it is Robert/Rob Bennett (5 rows).","44/522 named motions have tally-vs-result mismatches: 38 page-break under-counts, 3 source-typo result strings, 3 truncated second blocks — parse-quality, not fabrication.","Comments are genuine-only (28 agenda-packet rezone emails, 0 minutes leaks, verbatim in retained packet PDFs); speaker log (238) properly separated and labeled.","weeks/ regenerates clean (186 bundles, 0 conflict-copies); spot-check bundle byte-identical to canonical filtered to week. Precinct sums reconcile to county totals 0/37."],"gaps":["2021 named roll-call votes (and some 2020) not extracted — fix parse_tabular fallback and re-run; ~850-900 member-votes recoverable","Name-canon error: 'Sophie Bennett' should be 'Robert Bennett'","38 motions under-count members due to PDF page-break/dash-placeholder drops","votes/_validation_report.txt referenced in CLAUDE.md but missing","2019 election winners corroborated by news only (predates live state tabulator), not a government API"]}
```

## 2026-07-02 addendum — duplicate member-vote adjudication (plan item 3.1 prep)

The repo validator flagged 1 duplicate `(source, motion_no, date, member)` pair in
`meeting_minutes/all_votes.csv`: 2023-03-08 m8 (postpone Resolution 23-013), **Kelvin
Green Aye+Nay**. Source check: **faithful clerk contradiction** — the "Yes:" list is the
full 7-name roster boilerplate (including a bare "Green") while "No: Kelvin Green" is
explicit and the printed tally "The motion passed 6-1" confirms exactly one No.
Disposition: CSV keeps both verbatim rows; the db resolves to **Nay** via the new
`db/vote_overrides.csv` (fail-loud in `db/build_db.py`; see db/SCHEMA.md). db rebuilt:
1,163 motions · 7,011 votes (= 7,012 named rows − 1 merge) · 21 referrals unchanged.
Validator h.db: PASS ("+ 1 documented overrides").

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 6,705 rows / 960 motions (all named); 1 double vote, documented (Green 2023-03-08, db/vote_overrides.csv); tally-vs-counted 956/960 with 1 mismatch explained by that documented contradiction + 3 known quirks verified against source (2021-03-10 m4 'passed 7-0' with a recorded Jacob No; 2025-01-28 RDA m1: printed roll puts all six on the NO: line yet 'passed 6-0'; 2023-12-20 m7: double adjourn motion — the 3-3 tied roll paired with the second motion's '5-1 Pass', logged extraction quirk **→ FIXED in the 3.5 pass below**); failed tallies prevailing-side-first accepted (verified); 0 unexplained mismatches, 0 hard failures.

**2026-07-02 (3.5) extractor fix — 2023-12-20 double-adjourn roll/result mis-pairing (was "logged extraction quirk", now FIXED).**
Root cause (two gaps in `meeting_minutes/extract_votes.py`): (1) the narrative motion
anchor matched only "moved to|made a motion", so the source's "Council Member Jacob
**made a second motion** to adjourn" never started its own block — both adjourn motions
landed in one block; (2) `parse_result` had no "tied" vocabulary, so the only parseable
result in that block was the second motion's "(5-1)", which then paired with the FIRST
motion's printed roll. Fix (class-wide, no hardcoded dates): motion-anchor phrase is now
`made a(nother)? (\w+ )?motion` (shared by the anchor, mover, and motion-text regexes)
and `motion tied N-N` parses as a Fail (a tie does not carry).
- Before: one motion m7 "to adjourn the meeting", result `5-1 Pass`, with the 3-Aye/3-Nay roll.
- After: m7 = first adjourn (Bennett/Pack), result `3-3 Fail`, roll verbatim (Aye Bloom,
  Bennett, Pack; Nay Green, Jacob, McConnehey); new m8 = second adjourn (Jacob/Bloom),
  result `5-1 Pass`, `names_recorded:false` (narrative-only — the minutes name no roll;
  McConnehey's dissent is narrative and NOT converted to a row, never invent).
- Diff scope verified: `all_votes.csv` 6,705 rows before and after; exactly 41 rows changed
  in 6 motions — the 6 m7 rows (result only) + 35 rows in 5 sibling motions of the same
  phrasing class ("made a substitute motion", each verified against its `MOTION:` source
  line) that now carry the mover and the clean verbatim motion clause: 2022-05-11 m2
  (Green), 2022-06-08 m3 (Pack), 2022-12-21 m9 (Bloom), 2024-01-24 m3 (Green, "SUBSTITUTE"),
  2025-07-08 m2 (Jacob). 7 vote JSONs changed (those 5 + 2023-12-20 + 2021-08-25, whose
  substitute motion is tally-only so JSON-only). Corpus-wide check: 8 "made a <qualifier>
  motion" occurrences (nothing else matches the new phrase); "tied" appears only in
  2023-12-20. 2021-10-13's narrative substitute stays inside its original `MOTION:` block
  (single roll/result — no mis-pairing; noted, unchanged).
- motions_std re-run: 2023-12-20 m7 outcome pass→fail / tally 5-1→3-3; 2022-06-08 m3
  action_class final-action→procedural (it is a TABLE motion — correct).
- Rebuilds: db fail-loud reconciliation exact (7,012 named rows = 7,011 + 1 documented
  Green override; INTEGRITY OK), referrals unchanged (21), weeks rebuilt (187 bundles).
  `validate_votes.py`: tally 957/960, 2 known quirks remain (both faithful source typos),
  0 unexplained, 0 hard failures. `scripts/validate_city.py`: 21 PASS / 2 WARN
  (pre-existing documented) / **0 FAIL**. Originals in `_backups/2026-07-02/` (`.pre-3.5`
  suffixes where earlier-phase backups existed).
