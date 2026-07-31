# Verification — Provo (Utah) Municipal Council data repo

> **Addendum (2026-06-24, post-verification):** The public-comments dataset was
> restructured AFTER this report. The 737 rows verified below were clerk paraphrases of
> in-person speakers — **not** genuine public-submitted comments — and were moved to
> `public_comments/minutes_speaker_log.csv`. `all_comments_clean.csv` now holds **81
> genuine written comments** harvested from agenda-packet attachments (residents' own
> emails/letters, 2020–2022); all 138 regular-meeting packets were scanned. 2023+ written
> input lives in the bot-gated OpenGov "Open City Hall" portal (unrecoverable; see
> `public_comments/AVAILABILITY.md`). The 81 were checked for genuineness (staff/vendor/
> applicant senders dropped). All other datasets below are unaffected.

**Verifier:** independent QA agent (did NOT build the data). **Date:** 2026-06-24.
**Method:** adversarial — assume something is wrong until the numbers reconcile. Row
counts done with the Python `csv` module (never `wc -l`). Provenance spot-checks traced
derived rows back to the cited source minutes. Elections cross-checked against sources
*other than* the parsed county files (Ballotpedia/press/provo.gov).

## Summary table

| Dataset | Status | Rows | Coverage | Notes |
|---|---|---|---|---|
| **meeting_minutes** (votes) | **PASS** | 6,365 (6,248 member-vote + 117 tally-only); 1,074 motions; 160 contested | 311 files 2020–2026; 223 meetings carry ≥1 vote | File count = index = JSON = 311. All 8 sampled rows trace verbatim to source. 12 validation flags confirmed genuine. |
| **minutes** (corpus/index) | **PASS** | 311 index rows | 2020:51 2021:52 2022:50 2023:46 2024:49 2025:44 2026:19(partial) | All 311 `path`s exist, unique; 311 `source_url`s. 1 OCR file as documented. |
| **public_comments** | **PASS** | 737 | 2020–2026 (Apr); 97 of 139 Regular Meetings | Per-year counts match docs exactly; 100% `date_normalized`; 0 council/staff leaks; OpenGov 404 documented honestly. |
| **elections** | **PASS** | 26 races, 69 candidates, 1,455 precinct rows | 2019/2021/2023/2025 (primary+general); precinct detail 2021 & 2025 only | **16/16 general winners externally CONFIRMED**, incl. 2025 Judkins-over-Kaufusi upset. 0 winner mismatches. |
| **geo** | **PASS** | 67 precincts → Districts 1–5 | 68 geojson polygons (1 excluded: 25NE10) | geojson↔CSV districts 100% consistent; offline lat/lon tool works; D2/D5 cross-validated vs 2025 results. |
| **weeks** (derived) | **PASS** | 169 bundles | 2020-01 → 2026-05 | Regenerates **byte-identical** from canonical inputs; bundle matches canonical tables filtered to week. |

**Overall: PASS.** No fabrication found. Two trivial documentation-prose drifts noted
below (do not affect data). One unverifiable build-report sub-claim noted (the "18
meetings have no minutes" figure isn't recorded on disk).

---

## Findings per dataset

### 1. Votes (`meeting_minutes/all_votes.csv`) — PASS
- **Counts reconcile exactly.** csv-module count = **6,365 total rows** = 6,248
  member-vote (`member` non-empty) + 117 tally-only (`member` empty). **1,074 distinct
  motions** = 957 named roll-calls + 117 tally-only. **160 contested** (≥1 Nay/Abstain/
  Recuse). Vote values: Aye 5,535 · Nay 390 · Absent 319 · Abstain 4 · (blank) 117.
  Every figure matches `meeting_minutes/CLAUDE.md`.
- **Provenance / no fabrication.** 8 random named motions traced to their `source` file.
  Three verified line-by-line in the minutes:
  - `2020-03-10` m2 → minutes say *"approved 5:2 with Councilors Ellsworth, Fillmore,
    Handley, Hoban, and Sewell in favor. Councilors Harding and Shipley were opposed"* —
    matches CSV (Harding+Shipley = Nay).
  - `2020-09-15` m1 → *"approved 6:0 … Councilor Fillmore was excused"* — CSV shows
    Fillmore = Absent. Correct.
  - All **223** distinct `source` paths exist on disk; **0 missing**.
- **Tally consistency / validation flags.** The report lists exactly **12 mismatches of
  1,074**, matching the claim. Two spot-verified as genuine source issues, names kept
  verbatim (never auto-corrected):
  - `2023-05-02` m6: minutes literally print *"approved 5:0"* yet list all 7 councilors
    in favor — a **source typo**; the parser mapped the 7 printed names. ✔
  - `2025-11-18` Board of Canvassers: minutes print *"8:0 with Board Members Kaufusi,
    Bogdin, … and Whipple in favor"* — Mayor **Kaufusi is the 8th voter**, intentionally
    unmapped to the council roster, so 7 council names recorded. ✔
- **Tally-only motions** correctly carry empty `member`/`vote` (one row per motion) and
  trace to unanimous-consent / work-session votes that list no individual names.
- **Roster sanity.** Exactly **13 distinct voters** across the corpus, all real Provo
  councilmembers; **7 per year**, with transitions matching the election stagger
  (MacKay/Whipple appear 2022 after 2021; Bogdin/Christensen/Garrett appear 2024 after
  2023; Whitlock appears 2026 after 2025). **No Mayor (Kaufusi) and no staff** appear as
  council voters. ✔

### 2. Minutes corpus & index — PASS
- **311 `.md` files = 311 `minutes_index.csv` rows = 311 per-meeting JSONs.** No drift.
- All 311 `path` values exist on disk, all unique; all 311 have `source_url` (306 have
  `packet_url`). Single vendor `onbase`; single `pdf-ocr` file (`2022-01-18`) as
  documented.
- **Coverage** is plausible for a 1st/3rd-Tuesday cadence with paired Work Session +
  Regular Meeting: ~50/yr 2020–2025, 19 in partial 2026. 139 Regular Meetings, 152 Work
  Sessions, plus retreats/town-halls/canvassers.

### 3. Public comments — PASS
- **737 rows**, single source `in_person_minutes`. Per-year counts (120/95/107/72/165/
  125/53) match `public_comments/CLAUDE.md` **exactly**. `date_normalized` 100% populated;
  dates in range 2020-01-07 → 2026-04-28.
- **0 council/staff surname leaks** into `contact_name` (independently re-checked).
  All 97 `source_file` paths exist. 3 sampled comments verified verbatim in source minutes
  (incl. the preserved *"reflective pain"* clerk typo — faithful, not fabricated).
- **OpenGov gap documented honestly.** `raw/opengov_fetch_attempts.txt` + saved
  `opengov_provout_portal_RESPONSE_404.html` evidence the decommissioned portal. Comments
  are clerk third-person paraphrases (clearly caveated), not verbatim resident text.
- *Minor note:* `all_comments_dropped.csv` exists but is **empty (0 rows)**. The audit
  file is present per spec; nothing was dropped to log. Not a defect, but worth knowing
  the drop-audit is a no-op here.

### 4. Geo — PASS
- **67 precincts → Districts 1–5** (D1:19 D2:14 D3:11 D4:13 D5:10 — matches `geo/CLAUDE.md`).
  All CSV precincts present among the 68 geojson polygons; the 1 extra (`25NE10`, no
  council district) is correctly excluded.
- geojson `COUNCIL_DISTRICT` vs CSV `district`: **0 real mismatches** (apparent diffs were
  cosmetic float `1.0` vs `1`).
- `address_to_district.py` offline path works: `40.2338,-111.6585 → 25PR46 → District 5`;
  an out-of-Provo point → None. ✔
- Honesty: D1/D3/D4 rest on the city GIS map only (no precinct election data those
  odd-year-B cycles); D2/D5 additionally cross-validated against 2025 precinct results.
  Clearly documented; nothing fabricated.

### 5. Weeks (derived) — PASS
- **169 bundles.** Re-ran `build_weeks.py` against the canonical inputs in an isolated
  scratch copy: rebuilt 169 weeks and the week `votes.csv`, `comments.csv`, and
  `index.csv` came back **byte-identical** to the committed files (diff clean).
- Spot-check week ending **2024-03-05**: canonical `all_votes.csv` bucketed to that week =
  **33 rows** = week `votes.csv` 33 rows; comments **3 = 3**. Bucketing logic sound.

---

## External election cross-check (race-by-race)

Verified **general-election winners** against sources OTHER than the parsed county files.
**16/16 winners CONFIRMED, 0 mismatches.**

| Cycle | Race | Winner (repo) | External verdict | Source |
|---|---|---|---|---|
| 2025 | **Mayor** | **Marsha Judkins** def. incumbent **Kaufusi** (8703–8280, ~422) | **CONFIRMED — the upset.** Sworn in 2026-01-06, "first west-side mayor." | SLTrib; Daily Herald; BYU Universe |
| 2025 | Council D2 | Jeff Whitlock (over Petersen, mgn 205) | CONFIRMED (margin 205 exact) | BYU Universe |
| 2025 | Council D5 | Rachel Whipple (over Blackburn) | CONFIRMED (winner; opponent not named in press) | BYU Universe |
| 2025 | Citywide I | Katrice MacKay (over Shin) | CONFIRMED (winner; opponent not named in press) | BYU Universe |
| 2023 | Citywide II | Gary Garrett 5,801 over McKay R. Jensen 5,435 (mgn 366) | CONFIRMED — exact counts | Daily Herald; county PDF |
| 2023 | Council D1 | Craig Christensen 2,315 over Stan Jensen 1,532 | CONFIRMED — exact | Daily Herald |
| 2023 | Council D3 | Becky Bogdin 1,409 over David Lewis 894 | CONFIRMED — exact | Daily Herald |
| 2023 | Council D4 | Travis Hoban (unopposed, 100%) | CONFIRMED | Daily Herald |
| 2021 | Mayor | Michelle Kaufusi 10,752 over Dudley 3,674 | CONFIRMED — exact | KSL; county PDF |
| 2021 | Citywide I | Katrice MacKay 7,501 over Skabelund 6,165 | CONFIRMED — exact | KSL; county PDF |
| 2021 | Council D2 | George Handley (unopposed) | CONFIRMED | KSL |
| 2021 | Council D5 | Rachel Whipple over Coy Porter | CONFIRMED (winner) | KSL |
| 2019 | Council D1 | Bill Fillmore (unopposed) | CONFIRMED | BYU Universe |
| 2019 | Council D3 | Shannon Ellsworth over Robin Roberts | CONFIRMED | BYU Universe |
| 2019 | Council D4 | Travis Hoban over Valerie Paxman | CONFIRMED | BYU Universe |
| 2019 | Citywide II | David Shipley over Janae Moss | CONFIRMED | BYU Universe |

**Two trivial count differences — both expected, neither a real mismatch:**
- 2025 Mayor: repo has Kaufusi 8,280 (margin 423); some press/certified tallies show
  8,281 (margin 422). This is the documented small-precinct suppression/redaction
  difference — the repo's `election_results/CLAUDE.md` already flags it.
- 2019 D4: repo 2,625 (official canvass) vs BYU 2,601 (election-night unofficial). Normal
  unofficial→official drift.

**Roster cross-check.** The general-election winners imply the current (Jan 2026) council
— MacKay (CW I), Garrett (CW II), Christensen (D1), Whitlock (D2), Bogdin (D3), Hoban (D4),
Whipple (D5), Mayor Judkins — which **matches provo.gov** and **matches the members
casting votes in `all_votes.csv`** after name normalization. ✔

---

## Gaps & recommendations

1. **Documentation prose drift (cosmetic, data correct).**
   - `meeting_minutes/CLAUDE.md` says "222 of 311 meetings hold ≥1 recorded vote… other
     89." Actual on disk: **223 with votes / 88 empty** (223+88=311). The data (223
     meetings in `all_votes.csv`) is right; only the prose is off by one.
   - The task brief's "**18 meetings have no minutes (cancelled/not-yet-approved)**" figure
     is **not recorded anywhere on disk** (recon.md / CLAUDE.md). It's a build-agent
     report claim I could not independently confirm — recommend writing the cancelled/
     pending list into recon.md so the gap is auditable. *(Does not affect any dataset's
     PASS — the 311 retrieved files are all real and indexed.)*
2. **Precinct-level elections only for 2021 & 2025** (odd-year-A: Mayor, Citywide I, D2,
   D5). 2019 & 2023 are citywide-only because the county published no precinct SOVC CSV
   those cycles. Consequently **Districts 1/3/4 geo has no precinct-election
   corroboration** and relies on the city GIS map. Honestly documented; flagged as a known
   limitation, not a defect.
3. **Public comments are in-person clerk paraphrases only.** Typed written comment (OpenGov
   "Open City Hall", portal `provout`) is unavailable (decommissioned/404, evidence saved);
   agenda-packet written-correspondence attachments (documentType=5) were not harvested.
   Both gaps documented. A future pass could fetch packet PDFs to add written comments.
4. **Empty drop-audit.** `public_comments/all_comments_dropped.csv` is present but 0 rows —
   fine, but means the cleaning pass logged no removals to inspect.
5. **OCR file** (`2022-01-18`) is lower fidelity; parsed cleanly (6 motions) but flagged.

---

## Bottom line

Every dataset reconciles. Row counts are exact, every `source`/`source_file`/`path` exists
on disk, sampled votes and comments appear verbatim in the cited minutes, the 12 vote
validation flags are genuine source artifacts kept verbatim (not parse errors), the roster
matches election winners with no Mayor/staff contamination, **all 16 general-election
winners are externally confirmed (including the 2025 Judkins-over-Kaufusi upset)**, geo is
internally consistent with a working offline lookup, and `weeks/` regenerates
byte-identically. **No fabrication, no silent truncation.** The only items short of
"fully proven" are a build-report meeting-gap figure not recorded on disk and an off-by-one
in one prose summary — both documentation, not data.

```json
{"overall":"PASS","by_dataset":{"minutes":"PASS","votes":"PASS","comments":"PASS","elections":"PASS","geo":"PASS","weeks":"PASS"},"fabrication_found":false,"election_crosscheck":{"races_checked":16,"mismatches":[]},"key_findings":["Vote counts reconcile exactly: 6,365 rows = 6,248 member-vote + 117 tally-only; 1,074 motions; 160 contested; 311 files = 311 index = 311 JSON","All 8 sampled votes + 3 sampled comments trace verbatim to cited source minutes; all 223 vote source paths and all 97 comment source_files exist on disk","12 validation flags confirmed genuine source artifacts (printed-tally-vs-names typos; Board-of-Canvassers Mayor-as-8th-voter), names kept verbatim — not parse errors","13 distinct voters, 7/year, transitions match election stagger; no Mayor/staff counted as council voters","16/16 general-election winners externally CONFIRMED incl. 2025 Judkins-over-Kaufusi mayoral upset; current roster matches provo.gov and the voting record","weeks/ regenerates byte-identical from canonical inputs and matches canonical tables filtered to a sampled week","public comments: 737 rows, per-year counts match docs, 100% date_normalized, 0 council/staff leaks, OpenGov 404 gap documented with saved evidence","geo: 67 precincts -> Districts 1-5, geojson<->CSV 100% consistent, offline address tool works"],"gaps":["Build-report '18 meetings have no minutes' figure is not recorded on disk (recon/CLAUDE) — could not independently verify; recommend logging the cancelled/pending list","Prose off-by-one in meeting_minutes/CLAUDE.md (says 222/89; disk shows 223/88) — data correct, prose wrong","Precinct-level elections exist only for 2021 & 2025 (odd-year-A); 2019 & 2023 citywide-only, so geo Districts 1/3/4 rely on city GIS map with no precinct-election corroboration","Public comments are in-person clerk paraphrases only; OpenGov typed comments (404/decommissioned) and agenda-packet written correspondence (docType=5) not harvested","all_comments_dropped.csv present but empty (0 logged removals)"]}
```

## 2026-07-02 addendum — duplicate member-vote adjudication (plan item 3.1 prep)

The repo validator flagged 1 duplicate `(source, motion_no, date, member)` pair in
`meeting_minutes/all_votes.csv`: 2022-02-15 m2 (school-board-district map), **George
Handley Aye+Nay**. Source check: **faithful clerk contradiction** — the minutes'
vote sentence contradicts itself: "The motion was approved 5:2 with Councilors
Ellsworth, Fillmore, Handley, MacKay, and Shipley in favor. Councilor Handley opposed,
and Councilor Whipple abstained from voting." Handley *seconded* this motion and voted
against the competing substitute; the lone "opposed" name is a clerk slip (plausibly for
Chair Hoban, mover of the failed substitute — the only member otherwise unaccounted).
Disposition: CSV keeps both verbatim rows; the db resolves to **Aye** via the new
`db/vote_overrides.csv` (fail-loud in `db/build_db.py`; see db/SCHEMA.md). db rebuilt:
1,176 motions · 6,920 votes (= 6,921 named rows − 1 merge) · 12 referrals unchanged.
Validator h.db: PASS ("+ 1 documented overrides").

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 6,365 rows / 1,074 motions (957 named); 1 double vote, documented (Handley 2022-02-15, db/vote_overrides.csv); tally-vs-counted 869/957 strict + 86 documented dissent-only-naming undercounts (source style) + 2 known quirks (2022-11-01 m5: extractor missed the 'Opposed were Shipley, Hoban and Ellsworth' phrasing — 3 Nay rows absent, **FIXED in the 3.5 pass below**; 2023-05-02 m6: clerk prints 'approved 5:0' while naming 7 in favor incl. two excused members — kept verbatim); failed-motion tallies are printed prevailing-side-first (verified against source, accepted as the city's style); 0 unexplained mismatches, 0 hard failures.

**2026-07-02 (3.5) extractor fix — inverted "Opposed were …" phrasing:** the 3.1-logged
extraction gap is fixed. Root cause: `parse_vote_text` assigned each run of member names to
the *next following* cue word (Provo's usual "Councilors A, B in favor" order), so names
printed *after* a cue — "Opposed were Shipley, Hoban and Ellsworth" — were never scanned.
The extractor now detects the inverted form (cue immediately followed by "were"/"was"),
captures the name run after the cue bounded by the next cue / sentence end, and advances
past it so no adjacent cue can re-bucket the same names. Corpus-wide grep (council + PC
minutes, unfiltered `(cue) (were|was)` scan): exactly **2** instances of the class exist —
2022-11-01 m5 and 2022-12-13 m10 — both verified verbatim against source. Re-extraction
(`--force`) changed ONLY those two motions: **+7 Nay rows** (m5: Shipley, Hoban, Ellsworth;
m10: Handley, Fillmore, MacKay, Hoban — "Opposed were Chair Handley, Councilors Fillmore,
MacKay, and Hoban", a 4:3 fail whose 3 in-favor names were already captured), no row removed
or altered; both `result` strings unchanged (printed tallies). Totals: 6,365 → 6,372 CSV rows
(member rows 6,248 → 6,255), contested 160 → 162; motions/named/tally-only unchanged
(1,074/957/117). motions_std.csv byte-identical. db rebuilt fail-loud: 1,176 motions ·
6,927 votes (= 6,928 named rows − 1 documented Handley merge) · 12 referrals unchanged;
weeks/ rebuilt (183 bundles, new Nays verified in 2022-11-01 and 2022-12-13 bundles).
Validators re-run: `validate_votes.py` — tally 871/957 strict (+2), dissent-only
undercounts 86 → 85 (m10 moved to strict), known quirks 2 → 1 (only the 2023-05-02 m6
source contradiction remains), 0 unexplained, 0 hard failures; `validate_city.py` —
21 PASS / 2 WARN (pre-existing documented packet_url extension) / **0 FAIL**, h.db
reconciles exactly. Originals in `_backups/2026-07-02/provo_city_council/` (`.pre-3.5`
suffix where an earlier-phase backup already existed).
