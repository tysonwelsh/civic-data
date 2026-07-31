# Verification — Vineyard, Utah council data repo

> **Addendum (2026-07-19, speaker-log re-derivation — closes the 2026-07-02 deferral):**
> The 2026-07-02 note below flagged that `public_comments/minutes_speaker_log.csv` (210
> rows) had NOT been re-derived after the recovered documents. `extract_speaker_log.py`
> (deterministic; globs `meeting_minutes/minutes/*/*/*.md`) was re-run over the **full
> current 172-file corpus**: **210 → 283 data rows** (backup:
> `_backups/2026-07-19-pv-tierb-low/vineyard-speaker/`). The extractor is deterministic —
> **0 pre-existing rows changed value**. The additions are +76 rows across 18 meeting dates
> that entered the minutes tree AFTER the last (138-file) speaker-log run — i.e., the log
> was stale relative to the whole corpus, not just the Phase-1.3 recoveries. Of the four
> Phase-1.3 repairs:
> - **2023-08-30** (recovered stub → text): **+4** speakers (Alison Felshaw, Daria Evans,
>   Emma Moss, Randy Gray) — captured, spot-verified verbatim to source.
> - **2020-06-24** (recovered real minutes): **0** rows — the PUBLIC COMMENTS section is
>   genuinely "Hearing none, she closed the public session." Correct honest zero.
> - **2020-09-23** (recovered stub → OCR): **0** rows — its PUBLIC COMMENTS section names
>   one in-person speaker ("*Resident and Alternate Planning Commissioner Amber Rasmussen
>   explained…*"), but the deterministic patterns miss it: the compound "Resident and
>   Alternate Planning Commissioner …" prefix breaks the anchored `Resident NAME` pattern
>   and "explained" is not in the verb allow-list. Capturing it would need a name-anywhere
>   pattern with real false-positive risk (a redesign, not a re-run), so the extractor's
>   design was left intact and this is logged as an **honest residual recall gap** (TODO).
>   The later "emailed comments read into the record" (Dean Stonehocker et al.) sit in a
>   downstream hearing section, outside the single PUBLIC COMMENTS block the extractor
>   scans — also by design.
> - **PC 2023-06-21** (recovered): out of scope — the council speaker-log extractor never
>   reads `planning_commission/`.
> - **3 rows removed**, all legitimately: the byte-identical 2024-04-10 budget-planning
>   work-session file deleted in the 2026-07-02 dedup (item #3) took its 3 duplicate
>   speaker rows with it; those same 3 speakers (Daria Evans, Karen Cornelious, Kim
>   Cornelous) remain under the kept `2024-04-10_city-council-meeting.md`. No speaker was
>   lost — the old log had double-counted them.
> **RDA scope:** the extractor already scans the 9 audited-tree RDA-board `.md` files, but
> they yield **0** public-comment speakers (development-agency sessions, no resident comment
> period). The **20 net-new RDA minutes ingested 2026-07-19** live in `pmn_backfill/text/`
> (`.txt`, `provenance='pmn_minutes'`) — a **separate, non-audited corpus the extractor does
> not read by design**; left alone. No derived layer consumes the speaker log (neither
> `build_weeks.py` nor `db/`), so nothing downstream needed rebuilding.
> `scripts/validate_city.py vineyard_city_council/`: **25 PASS / 1 WARN / 0 FAIL** (the WARN
> is the pre-existing documented `provenance` column).

> **Addendum (2026-07-02, audit-driven repairs — wrong/duplicate/stub minutes):** The
> repo-wide audit (`_audits/2026-07-02/report.md`) confirmed 4 document defects, all now
> repaired (originals in `_backups/2026-07-02/vineyard_city_council/`):
> 1. **2020-06-24 council minutes were the WRONG document** — CivicClerk event 533's only
>    Minutes attachment (fileId 877, named "636m-February 26, 2020 CC Final Minutes") is a
>    city-side mis-upload: its body was byte-identical to the 2020-02-26 minutes, so Feb 26's
>    5 motions / 25 vote rows were double-counted under June 24. The **real June 24, 2020
>    minutes were recovered from the Utah Public Notice Website**
>    (https://www.utah.gov/pmn/files/618419.pdf, 15 pp, text layer) → 18 motions / 90 rows.
> 2. **Two header-only stub files** (0-char body; CivicClerk `plainText` was empty at build
>    time) replaced with the real minutes from the source PDFs: **2020-09-23** (fileId 905,
>    scanned copier PDF → OCR pdftoppm 300dpi + tesseract, `format=ocr`) → 10 motions /
>    50 rows; **2023-08-30** (fileId 1345, text-layer PDF → `pdftotext -layout`) → 9 motions
>    / 45 rows.
> 3. **2024-04-10 double-parse** — the city attached one byte-identical combined minutes PDF
>    to BOTH CivicClerk events (1624 regular meeting / 1628 budget planning session; PDFs
>    md5-identical), so the extractor parsed it twice (10 motions / 46 rows duplicated).
>    Kept once as `2024-04-10_city-council-meeting.md` (the document titles itself "MINUTES
>    OF A REGULAR CITY COUNCIL MEETING" and contains the WORK SESSION content); the
>    budget-planning duplicate file + index row removed.
> 4. **Planning Commission 2023-06-21 was a copy of 2023-06-07** — CivicClerk event 815's
>    only Minutes attachment (fileId 1316) is named "924m-6.7.23 PC final meeting minutes"
>    (another city-side mis-upload). The **real June 21, 2023 PC minutes were recovered from
>    PMN** (https://www.utah.gov/pmn/files/1214475.pdf) → 2 motions / 8 rows (4 ayes each;
>    old duplicate contributed 10 rows). Two extractor accommodations, verified corpus-safe
>    (all other rows byte-identical before/after): the clerk-typo `MOTION.` header
>    (rewritten to `Motion:` only when followed by a Mixed-Case name on the same line) and
>    `OSTER`→Ostler in `VARIANTS`.
> **Vote-table deltas:** council `all_votes.csv` 5,126 → **5,240** rows (−71 duplicate/wrong
> rows, +185 rows from the three recovered documents), motions 1,033 → 1,076 (incl.
> tally-only); PC `all_votes.csv` 1,619 → **1,617** rows (−10 dup, +8 real). All unaffected
> rows verified byte-identical pre/post. `validate_votes.py`: council — same 2 documented
> SOURCE-typo tally flags (2024-05-08, 2025-08-26), 0 new; PC — PASS, 0 flags.
> `db/civic.db` rebuilt (1,417 motions · 6,857 votes · INTEGRITY OK; referrals unchanged at
> 9 links) and `weeks/` regenerated (150 bundles). The three conflicting meeting-count doc
> claims (README 173 / CLAUDE.md 138 / meeting_minutes/CLAUDE.md 165) were reconciled to the
> true post-repair count: **172 minutes files (163 council + 9 RDA board)**.
> Note: `public_comments/minutes_speaker_log.csv` (210 rows) was NOT re-derived; the three
> recovered documents contain public-comment paraphrases (2020-09-23 includes emailed
> comments read into the record) not yet reflected there.

> **Addendum (2026-06-25, post-verification fix):** The PARTIAL verdict's material defect was
> fixed and re-run: `extract_votes.py` now recognizes the `COUNCILMEMBERS X, Y, Z VOTED IN
> FAVOR` phrasing (+ case-insensitive `MOTION:` headers), recovering **~160 Aye rows** —
> `all_votes.csv` went **4,435 → 4,599 rows** (949 motions, 41 contested). The doc claim that
> "Mayor Stratton casts votes" was **corrected, not back-filled**: the 2026 clerk never names
> the mayor in any roll-call run, so Stratton legitimately has 0 vote rows (prior Mayor
> Fullmer is named and has 868); inventing his votes would violate the no-fabrication rule.
> Elections (7/7 winners), comments, and weeks passed clean in the original review. The
> 2024-05-08 "FOUR TO ONE" remains a flagged source typo.

**Verifier:** independent adversarial QA agent (did not build the data).
**Date:** 2026-06-25.
**Method:** all CSV row counts via the Python `csv` module (never `wc -l`); votes traced
to source minutes on disk; elections cross-checked against sources *other than* the parsed
files (Ballotpedia, Daily Herald, KSL/Deseret, Utah County official PDF, rcvis); `weeks/`
regenerated from canonical and a bundle diffed against the canonical table.

## Summary table

| Dataset | Status | Rows (csv module) | Coverage | Notes |
|---|---|---|---|---|
| **meeting_minutes (files)** | **PASS** | 138 .md on disk == 138 in `minutes_index.csv` | 2020–2026; 29-meeting gap logged & genuinely absent | Gap is legitimate (>30 MB image-only packets). |
| **votes (`all_votes.csv`)** | **PARTIAL** | 4,435 member-vote rows; 944 motions (902 with named rows) | 2020–2026 | Provenance clean, contested=41 ✓, but a **systematic "VOTED IN FAVOR" parse gap** drops affirmative voters on ~24 motions (mostly 2026); **Mayor Stratton casts 0 votes** despite docs claiming he votes. |
| **comments (`all_comments_clean.csv`)** | **PASS** | 0 (header-only, by design) | n/a | SUBMIT-ONLY verdict documented & substantiated; speaker log separate + labeled. |
| **elections** | **PASS** | 7 races / 37 candidate rows / 128 precinct rows | 2019/21/23 RCV + 2025 plurality | Every winner externally confirmed; no fabrication; documented modeling sound. |
| **geo** | **PARTIAL** | city polygon (1) + precincts | at-large, no districts | Correct design; **precinct-count doc conflict (8 vs 9)** between geo and election CLAUDE.md. |
| **weeks (derived)** | **PASS** | 129 week dirs (+index.{md,csv}) | 2020–2026 | Regenerates cleanly; spot-checked bundle == canonical filtered to week; no iCloud conflict copies. |

---

## Findings per dataset

### 1. Meeting minutes — PASS
- **138** `.md` files on disk == **138** rows in `minutes_index.csv` (csv-module count). Exact match.
- All **121** distinct `source` paths referenced by `all_votes.csv` exist on disk (0 missing).
- **29 unrecovered meetings** in `minutes_unrecovered.csv` are **genuinely absent** — checked each date against the `minutes/` tree: **0 of 29** are secretly present/faked. Each row carries event_id, fileId, size (40–258 MB), and reason (image-only packet, not downloaded per disk rule).
- **Coverage by year** (recovered / unrecovered / total-known):
  2020 23/0/23 · 2021 25/0/25 · 2022 25/0/25 · 2023 26/1/27 · **2024 12/12/24** · 2025 18/7/25 · 2026 9/9/18.
  The gap is concentrated in 2024 (50% of that year's meetings are image-only packets) and 2026. This is *not retrieved because unrecoverable* (legitimate), distinct from *not retrieved* (a defect) — well documented.
- **2 OCR files**: `2026-04-14` parses cleanly (3 motions, all 5-0, councilmembers named, tally-consistent — verified); `2026-04-21` is a work session with 0 votes (correct).

### 2. Votes — PARTIAL (one real defect + one false doc claim)
**What reconciles:**
- 4,435 member-vote rows; 944 motions across 138 meetings (matches `validate_votes.py`).
- **Provenance: 8/8 random rows fully verified** — source file exists AND the member surname AND the mover appear in the cited minutes. No fabricated member, date, motion, mover, or vote found.
- **Member set is clean** (14 surnames, all real Vineyard councilmembers; no stray/misspelled names): Cameron, Clawson, Earnest, Flake, Fullmer, Holdaway, Judd, Lauret, McCumber, Nair, Rasmussen, Sifuentes, Welsh, Wood.
- **Contested motions (any Nay/Abstain/Recuse) = 41** — re-derived independently, matches the documented ~41.
- **Mayor Fullmer is a voting member** — appears casting Aye and Nay (incl. dissents) throughout 2020–2025. Confirmed.
- **2024-05-08 m8 mismatch is a genuine SOURCE typo** — verified against source lines 437–438: only 4 members present (Rasmussen excused), named roll is 3 Yes + 1 No (Holdaway), yet the clerk wrote "CARRIED FOUR TO ONE" — impossible with 4 voters. The extractor correctly stored 3-1; the document's "FOUR TO ONE" is wrong. Not a parse error.
- **Roster vs election winners matches** every cycle (2019 Welsh+Flake → 2022–23; 2021 Sifuentes+Rasmussen → 2022–23; 2023 Holdaway+Cameron → 2024; 2025 McCumber/Wood/Lauret+Nair+Holdaway → 2026).
- **Tally-only motions**: 51 motions are `names_recorded=false`; 42 have **no member-vote rows** in `all_votes.csv` (structurally correct — a long/one-row-per-member format yields 0 rows for a motion with no named members). The build brief's phrase "tally-only motions have empty members" is loose wording; in practice they simply produce no rows. Not a defect by itself.

**DEFECT — "VOTED IN FAVOR" affirmative votes silently dropped:**
- The extractor recognizes "VOTED AYE/YES" but **not** the phrasing **"…COUNCILMEMBERS X, Y, Z VOTED IN FAVOR."** This phrasing appears in **6 files / 27 occurrences**, all 2024+ (`2024-06-14`, `2026-01-14`, `2026-01-27`, `2026-02-24`, `2026-03-31`, `2026-04-28`).
- Effect: **~24 motions** whose source names the affirmative voters lost those voters in `all_votes.csv`. Most fell into the `names_recorded=false` bucket (so they produce **zero** rows); `2026-02-24` is the clearest illustration — all 8 motions read "COUNCILMEMBERS NAIR, WOOD, LAURET, AND MCCUMBER VOTED IN FAVOR. … PASSED FOUR (4) TO ZERO (0)" in the source, but `all_votes.csv` records **only `Holdaway = Absent`** for each — the four Yes votes are missing.
- This is silent under-recording: the result string still says `4-0 Pass`, so the motion count and contested count are unaffected, but **member-level 2026 affirmative votes are materially incomplete**. The build's own `validate_votes.py` did **not** catch it because those motions are flagged `names_recorded=false`, which exempts them from the tally-vs-name check.
- **Recommendation:** add "VOTED IN FAVOR" (and likely "IN SUPPORT", "VOTED IN THE AFFIRMATIVE") to the affirmative-verb list in `extract_votes.py`, re-run, and re-validate. Expect ~24 motions to flip to `names_recorded=true` and ~80–100 Aye rows to appear (incl., importantly, **Mayor Stratton's votes**).

**FALSE DOC CLAIM — "Mayor Stratton casts votes":**
- `meeting_minutes/CLAUDE.md`, the root `CLAUDE.md`, and the build brief assert "both Fullmer and Stratton cast votes." **Stratton has 0 vote rows in `all_votes.csv`.** This is a direct consequence of the parse gap above (the 2026 meetings where Stratton-as-mayor would appear are exactly the under-parsed "VOTED IN FAVOR" meetings) plus the 2026-04-14 OCR motions being 5-0 of the five *councilmembers* (mayor not in those particular votes). Until the parser is fixed, the "Stratton votes" claim is unsupported by the data. The **Mayor+4→Mayor+5 growth** is partially visible (5 distinct councilmembers in 2026 vs 4 in prior years) but cannot show "6 voters" because the mayor's votes are missing.

### 3. Public comments — PASS
- `all_comments_clean.csv` is **legitimately 0 rows** (header-only). `AVAILABILITY.md` documents an exhaustive SUBMIT-ONLY hunt: city page (no archive), CivicClerk eComment (`publicCommentsEnabled` false on all 393 events; submission-only API entity sets return 404), agenda packets (only clerk paraphrases of in-person speakers), correspondence archive (none). Verdict substantiated.
- `all_comments_dropped.csv` = 0 rows (nothing ingested → nothing dropped). Correct.
- `minutes_speaker_log.csv` = **210 data rows** (csv-module read returns 211 because a `#` header-note line on row 1 is misread as the header; documented). Properly **labeled** as clerk paraphrases / meeting-record notes, kept strictly separate from `all_comments_clean.csv`. Correct.

### 4. Coverage vs the 2020 floor — covered above
Minutes span 2020–2026. Missing = 29 logged unrecoverable image-only packets (NOT "not retrieved"). No silent truncation: the gap, the OCR files, and the zero-vote meetings are all enumerated in `meeting_minutes/CLAUDE.md`.

### 5. Geo — PARTIAL
- Design is correct: Vineyard is **at-large, no districts**; `address_to_district.py` is an in-city-limits test (degenerate district map, not fabricated). City polygon fetched by FIPS=80420; precincts by spatial intersect (CountyID=25). CRS is genuine EPSG:4326.
- **Doc conflict (flag):** `geo/CLAUDE.md` says **9** precincts (`25VI01`–`25VI09`) from the live spatial intersect; `election_results/CLAUDE.md` and the precinct CSV say **8** precincts (`25VI01`–`25VI08`). Both can be internally true (a 9th precinct overlaps the city boundary but cast no Vineyard council votes in 2025), but the two CLAUDE.md files disagree on the count without cross-referencing each other. Not a data-integrity failure; reconcile the wording. (I did not run the live ArcGIS query or the geocoder — network-dependent — so the precinct geometry itself is **not independently re-verified**; marked PARTIAL on that basis.)

### 6. Weeks — PASS
- `python3 build_weeks.py` regenerates cleanly: "Built 129 week bundles" (comments 0, vote weeks 117, minutes weeks 129). Directory holds **129** date-named week dirs + `index.csv` + `index.md` = 131 entries; **no iCloud conflict-copies** (no `"… N"` suffixed twins).
- Spot-check: `weeks/2022-07-13/votes.csv` filtered to 2022-07-13 == `all_votes.csv` filtered to 2022-07-13 **exactly** (50 rows, identical (motion_no, member, vote) sets, 0 diff).

---

## External election cross-check (race-by-race)

All winners confirmed against a source **other than** the parsed rcvis/EV files. **0 winner mismatches.**

| Race | Repo winner(s) | External source | Match |
|---|---|---|---|
| **2019 Council** (2 seats, RCV) | Cristy Welsh (R6) + G. Tyce Flake (R5) | **Ballotpedia** "City elections in Vineyard, Utah (2019)" — RCV, 2 at-large seats, 7 candidates, Welsh R6 & Flake R5 | ✅ (incl. RCV electing Welsh despite she led first-choice — both non-trivial RCV winners modeled correctly) |
| **2021 Mayor** (RCV, single-winner) | Julie Fullmer 1,329 / 86.64% (R1 majority) | **KSL** 2021 results (winner Fullmer; reports 1,259 R1 — a different canvass snapshot, winner identical) | ✅ winner; ⚠ vote-total snapshot differs (docs flag the 597/57/38 vs 1,329/132/73 issue; repo uses the larger rcvis figures — defensible) |
| **2021 Council** (2 seats, RCV) | Mardi Sifuentes + Amber Rasmussen | **KSL** — Sifuentes & Rasmussen win their seats | ✅ |
| **2023 Council** (2 seats, RCV) | Jacob Holdaway + Sara Cameron | **Utah County / Daily Herald** — certified Dec 13 2023, Holdaway & Cameron | ✅ |
| **2025 Mayor** (plurality) | Zack Stratton 1,417 / 54.71% over Sifuentes 1,173 | **Daily Herald** "Making it official…" + Utah County OFFICIAL PDF — Stratton 1,417 | ✅ (pct 54.71 vs Herald's 54.13 — denominator/rounding, winner & raw votes identical) |
| **2025 Council general** (Vote-for-3) | McCumber 1,460, Wood 1,389, Lauret 1,348 | **Daily Herald** + Utah County OFFICIAL PDF — same three; McCumber drew 2-yr term by lot | ✅ |
| **2025 Council primary** (top 6 advance) | Wood, McCumber, Nair, Lauret, Rhoton, Clawson advance | Enhanced Voting portal (parsed) + city 2025 election page | ✅ (top-6 advance logic correct) |

- **Roster implied by elections == members casting votes** in `all_votes.csv` for every year (verified in §2). After case normalization, the elected slate matches the voters.
- **Races expected vs captured:** all 4 cycles (2019/21/23/25) present. The only stated gap is **no per-precinct breakdown for the RCV years (2019/21/23)** — citywide-only, an inherent rcvis/RCV-pilot limitation, documented; precinct CSV is 2025-only. Legitimate.

---

## Gaps & recommendations

1. **FIX (votes, real defect):** Teach `extract_votes.py` the **"VOTED IN FAVOR"** affirmative phrasing (also check "IN SUPPORT", "IN THE AFFIRMATIVE"). ~24 motions across 6 files (all 2024+) currently drop their named Yes voters — including **all of Mayor Stratton's 2026 votes**. Re-run extract + validate after the fix.
2. **CORRECT THE DOCS (votes):** Until the parser is fixed, remove/soften the "Mayor Stratton casts votes" claim in root `CLAUDE.md` and `meeting_minutes/CLAUDE.md` — Stratton currently has **0** vote rows.
3. **HARDEN VALIDATION:** `validate_votes.py` exempts `names_recorded=false` motions from the tally check, which is exactly why the "VOTED IN FAVOR" loss went unnoticed. Add a check that flags any motion whose `result` is a non-zero `N-M` while `names_recorded=false` **and** the source contains an affirmative-vote verb — that would have surfaced this.
4. **RECONCILE (geo doc):** geo says 9 precincts, election_results says 8. State the reason for the difference (boundary-overlap vs vote-casting) in both files, or align them.
5. **NOT INDEPENDENTLY RE-VERIFIED (PARTIAL scope):** the geo precinct geometry / city polygon (live ArcGIS) and the geocoder were not re-queried (network); the 2021 Mayor vote-total snapshot discrepancy is documented but unreconciled to a certified Utah County SOVC (none located for RCV years). None of these is a fabrication; they bound what "PASS" can mean.

**No fabrication found.** Every sampled vote traces to a real source document with the named member and mover present; every election winner is corroborated by an outside source; the 29-meeting gap is real and logged, not faked. The single material data defect is *under-recording* (dropped "VOTED IN FAVOR" affirmatives), not invention.

```json
{"overall":"PARTIAL","by_dataset":{"minutes":"PASS","votes":"PARTIAL","comments":"PASS","elections":"PASS","geo":"PARTIAL","weeks":"PASS"},"fabrication_found":false,"election_crosscheck":{"races_checked":7,"mismatches":[]},"key_findings":["138 minutes files == minutes_index.csv; all 121 vote source paths exist; 29 unrecovered meetings genuinely absent (0 faked)","Provenance 8/8 random vote rows verified to source (member+mover present); member set clean; no fabrication","DEFECT: extract_votes.py does not parse 'VOTED IN FAVOR' phrasing -> ~24 motions across 6 files (2024+) silently drop their named affirmative voters; e.g. 2026-02-24 records only Holdaway=Absent for 8 motions stated 4-0","FALSE DOC CLAIM: Mayor Stratton has 0 vote rows in all_votes.csv despite CLAUDE.md/brief asserting he votes (caused by the parse gap)","Contested motions re-derived = 41 (matches docs); Mayor Fullmer confirmed as voting member; 2024-05-08 'FOUR TO ONE' confirmed a genuine source typo (named roll is 3-1)","All 7 election races externally cross-checked (Ballotpedia/Daily Herald/KSL/Utah County PDF) -> 0 winner mismatches; roster matches voters every year","Comments legitimately 0 rows (SUBMIT-ONLY substantiated); speaker log 210 rows, labeled, kept separate","weeks/ regenerates cleanly (129 bundles); spot-checked bundle == canonical; no iCloud conflict copies"],"gaps":["FIX extract_votes.py to recognize 'VOTED IN FAVOR'/'IN SUPPORT' (~24 motions, incl. all Stratton 2026 votes)","Correct docs claiming Stratton votes until parser fixed","Harden validate_votes.py to flag non-zero N-M results that have names_recorded=false but an affirmative verb in source","Reconcile precinct-count doc conflict: geo says 9, election_results says 8","Geo ArcGIS geometry + geocoder not re-queried (network); 2021 Mayor vote-total snapshot unreconciled to a certified RCV-year SOVC"]}
```

**2026-07-02 (3.1) council-vote validation:** bespoke `meeting_minutes/validate_votes.py` re-run — 1,076 motions, 2 numeric tally mismatches (both documented SOURCE clerk errors: 2024-05-08 m8, 2025-08-26 m3), 0 unparsed results, 22 tally-only; shared-template checks (schema/dates, motion-group convention, double votes, tally-vs-counted with the 2 knowns config-documented): 0 hard failures, 0 unexplained mismatches.

**Addendum (2026-07-31, duplicate-ingest date-collision wave — PC 2023-04-05 ↔ 2023-04-19):**
A repo-wide collision screen flagged Planning Commission 2023-04-05 and 2023-04-19 as carrying
an identical 10-motion set (similarity 0.994). Verified at source: this is the **same city-side
mis-upload defect as item #4 of the 2026-07-02 addendum**, a second instance the earlier audit
missed. Evidence:
1. Both markdown bodies are the **same document** — in-body header on each reads "REGULAR
   MEETING OF THE VINEYARD PLANNING COMMISSION, **Wednesday April 5, 2023**"; the only textual
   differences are leading whitespace, the footer "Final" vs "Draft", and the signature block
   ("CERTIFIED CORRECT BY … Planner" vs "Certified BY … Planning Tech").
2. The CivicClerk source file NAMES both say 4.5.23 — event **787 / fileId 1275**
   `896m-4.5.23 PC final meeting minutes` (the certified FINAL) and event **792 / fileId 1281**
   `901m-4.5.23 PC final  meeting minutes` (the DRAFT). Re-queried live 2026-07-31:
   `GET /v1/Events?$filter=startDateTime ge 2023-04-15…` returns event 792 (2023-04-19,
   "Planning Commission - Public Hearing") with exactly two published files — agenda 1280
   `901a-4.19.23 PC Meeting Agenda with Attachments` and minutes 1281 (the April 5 doc). The
   city never posted the real April 19 minutes.
3. **2023-04-05 is the real date of the recorded content** (also the date the 4/5 minutes were
   certified on: "Certified correct ON: April 19, 2023" — i.e. approved at the 4/19 meeting).
4. **An April 19, 2023 PC meeting nevertheless occurred**: it was agendaed (fileId 1280) and the
   2023-12-06 PC minutes approve "**4.1 Approval of the April 19, 2023 PC Meeting Minutes**" as a
   consent item. Its minutes are therefore MISSING, not nonexistent → ledgered in
   `planning_commission/minutes_unrecovered.csv` (16 rows). Unlike the 2023-06-21 case, PMN is
   **not** a recovery channel here: the repo's body-531 harvest holds only 2015–2018 +
   2024-02-07 (2019–2023 blobs purged), and the live PMN body-531 sitemap lists 2026 only.

**Action:** phantom `planning_commission/minutes/2023/2023-04-17/` (+ its votes JSON) deleted, its
`minutes_index.csv` row removed, a `minutes_unrecovered.csv` row added. No parser change was
warranted — the ingest date came from the CivicClerk event date, which is correct for event 792;
the defect is the city's attachment, so there is no date-parse bug to harden.
**Deltas (expected-rows-only, diffed at (source,date,body,motion_no,member,vote) — never by id):**
PC `all_votes.csv` 1,617 → **1,583** rows (−34, ALL dated 2023-04-19; **0 added**, every other row
byte-identical); PC motions 375 → **365**; `motions_std.csv` 362 → **352**; `db/civic.db`
meetings 290 → **289**, motions 1,620 → **1,610** (−10), votes 7,840 → **7,806** (−34),
applications unchanged at 310, referral links unchanged at 15; `weeks/` regenerated, **163 bundles,
byte-identical** (weeks/ is council+RDA only — PC is not bucketed). `validate_votes.py` PASS (0
flags); `scripts/validate_entity.py vineyard` **25 PASS / 1 WARN / 0 FAIL** (the WARN is the
pre-existing documented `provenance` column). Re-running the collision screen inside
`db/civic.db` leaves **one** identical-signature pair — RDA 2024-08-28 ↔ 2025-06-11, both a single
boilerplate "APPROVE THE CONSENT ITEM AS PRESENTED / Carried unanimously" motion from two distinct,
md5-different minutes documents: a genuine coincidence, **not** a duplicate ingest, no action taken.
Originals in `_backups/2026-07-31-g8/vineyard_city_council/`. gov.db re-federation is the
coordinator's step (validator reports it STALE by exactly −1 meeting / −10 motions / −34 votes).
