# Verification — Orem, Utah council data repo

> **Addendum (2026-07-02, audit-driven repair — PC 2025-10-15 minutes were the WRONG document):**
> The repo-wide audit flagged `planning_commission/minutes/2025/2025-10-13/2025-10-15_planning-commission-meeting.md`
> and the 2025-11-05 PC minutes as duplicate bodies (byte-identical except the injected `#` title
> line; the shared body self-states "Planning Commission minutes for November 5, 2025").
> **Verified at source:** CivicClerk event 1416 (10-15-2025 Planning Commission)'s only Minutes
> attachment, fileId=1005 "Approved Minutes"
> (`https://oremut.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=1005,plainText=false)`),
> is **byte-identical to the 11-05 event 1468's fileId=1006** (both md5
> `382a9836e7015764fd6f3cb3ee35bf3b`, 5-pp text PDF) — a city-side mis-upload, so the 2025-11-05
> file is correct and the 10-15 file was a duplicate of it. The **real 10-15-2025 minutes are
> published nowhere findable**: Utah Public Notice notice 1027529 ("10.15.2025 Planning
> Commission") carries only the agenda, packet, hearing notice, and three signed resolutions
> (PC-2025-0044/45/46); the legacy `exe.orem.org/minutes.aspx` archive is dead; the Drive archive
> ends early 2021. The meeting demonstrably happened (the 11-05 minutes approve "Minutes for the
> 10-15-2025 Planning Commission Meeting"), so per the no-fabrication rule the wrong file + its
> `minutes_index.csv` row were **removed** and the meeting logged in
> `planning_commission/minutes_unrecovered.csv` (now 17 rows) with the evidence. Original files in
> `_backups/2026-07-02/orem_city_council/`.
> **Impact (both files parsed as format-C tally-only, 0 member rows):** PC `all_votes.csv`
> **2,997 → 2,997 rows, byte-identical** pre/post re-run (`roster.csv` also byte-identical);
> PC meetings 115 → **114**, motions 567 → **562** (−5 duplicated tally-only motions:
> recommendations 115→113, final actions 223→221, procedural 229→228). `validate_votes.py`:
> ALL CHECKS PASS. `db/civic.db` rebuilt — **all 8 table exports byte-identical** (1,067 motions ·
> 6,746 votes; the 5 duplicate motions were tally-only and never entered the db), **29 referral
> links reproduce exactly** under stable app_keys (override ids 52/222 unchanged — no remap
> needed); `weeks/` regenerated (128 bundles, unchanged). Docs refreshed: README, CLAUDE.md,
> planning_commission/CLAUDE.md, planning_commission/report.json. Corpus screener now reports
> **0 duplicate bodies**.

> **Addendum (2026-06-25, post-verification fix → now PASS):** The PARTIAL verdict's three
> OCR-related defects were fixed and re-run: 2026-03-10 m4 (stray-period label artifact had
> dropped 4 Aye votes → now correctly `4-3 Pass`), 2024-12-10 m4 (a broken OCR outcome cue
> had merged two roll-calls → now split into the two real motions), and the garbled OCR
> names (`Tom Macdonals`→Macdonald, `Jenn'gale`→Jenn Gale, bogus `Mr` dropped — 12→0 bad-name
> rows). `all_votes.csv` is now **3,749 rows / 566 motions / 49 contested, 0 validation
> mismatches**. The stale `meeting_minutes/CLAUDE.md` and `public_comments/CLAUDE.md` counts
> were refreshed. All other datasets passed clean in the original review (6/6 election winners
> externally confirmed, no fabrication; 0 stub files). Earlier this build also recovered the
> 68 image-only-scan minutes via OCR (votes 1,703→3,749). Documented legitimate gaps remain:
> Apr–Jun 2021 minutes absent; 2019/2023 elections citywide-only.

**Verifier:** independent adversarial QA agent (did not build the data).
**Date:** 2026-06-25.
**Method:** csv-module row counts (never `wc -l`); provenance spot-checks back to source
minutes; tally re-derivation on all 565 motions; named-vote coverage per year/member;
stub detection on all 130 minutes; external election cross-check against Daily Herald,
KSL, Ballotpedia + Utah County certified data; weeks/ regeneration + bundle reconciliation.
**External sources cross-checked:** heraldextra.com (Daily Herald), ksl.com, ballotpedia.org,
electionresults.utah.gov (Utah County certified canvass).

---

## Summary table

| Dataset | Status | Rows | Coverage | Notes |
|---|---|---|---|---|
| Minutes (markdown) | **PASS** | 130 files = 130 index rows | 2020–2026, documented Apr–Jun 2021 gap | 0 header-only stubs; all 68 OCR files have real body text (min 3.7 KB, median 24 KB) |
| Votes (`all_votes.csv`) | **PARTIAL** | 3,736 member-vote rows / 565 motions / 48 contested | every year 2020–2026 has votes | All 126 source paths exist; tallies consistent; **but 4 OCR-parse defects found** (see below) |
| Genuine comments | **PASS** | 95 | 9 meetings, 2020-07-14 → 2021-03-23 | all `minutes_attached_written`; verbatim verified; no paraphrase leak; 100% `date_normalized` |
| Speaker log | **PASS** | 121 | 2020–2026 (undercounts 2022–26, documented) | header note present; correctly separated from comments |
| Elections | **PASS** | 11 races / 75 candidate rows / 2,063 precinct rows | 2019/21/23/25; precinct detail 2021+2025 | all 4 general cycles externally cross-checked, **0 mismatches** |
| Geo | **PASS** | 1 city polygon + 57 precincts | at-large, no districts | in/out check verified (Orem center INSIDE, Provo OUTSIDE) |
| Weeks (derived) | **PASS** | 128 bundles | — | regenerates clean, no iCloud conflict-copies, bundles reconcile to canonical |

**Overall: PARTIAL** — no fabrication, all headline numbers reconcile, elections fully
externally verified. Downgraded from PASS only because the vote extractor has a small cluster
of OCR-related parse defects (4 affected motions / ~17 of 3,736 rows = 0.45%), all of which
**silently DROP or mangle real votes** rather than invent them. These are correctable by a
parser fix + re-run; none affects provenance or the election cross-check.

---

## Findings per dataset

### Minutes — PASS
- 130 `.md` files on disk == 130 rows in `minutes_index.csv`. Format split: **68 `ocr` / 62
  `text`** (matches the brief; the OCR repair did happen).
- **No header-only stubs remain.** Every file has >200 body chars; smallest OCR file is
  3,726 bytes, median 24 KB. The 68 OCR files contain real roll-call prose.
  > NOTE: `meeting_minutes/CLAUDE.md` is **STALE** — it still describes "68 content-empty
  > stubs / 62 content files / 255 motions / 1703 vote rows" (the pre-OCR state). The actual
  > on-disk data is the post-OCR rebuild (3,736 rows / 565 motions). Recommend updating that
  > CLAUDE.md so its reported counts match reality.
- Coverage by year: 2020 (20, all 12 months), 2021 (16; **Apr/May/Jun absent — confirmed
  documented gap**), 2022 (23), 2023 (22), 2024 (23; no Nov), 2025 (17; no Oct), 2026 (9;
  through May — expected for a June-2026 build). The 2024-Nov and 2025-Oct single-month
  absences are minor and plausibly no-meeting/holiday months (not flagged as defects, but
  not independently confirmed as "no meeting held").

### Votes — PARTIAL (no fabrication; 4 OCR-parse defects)
- **3,736 rows / 565 motions** (csv-module count) — matches the brief exactly.
- Vote values are **only {Aye, Nay}** — consistent with the "Orem records no abstain/recuse"
  claim.
- **Tally consistency:** all 48 contested motions re-derived; every `result` string matches
  its parsed aye/nay counts. Only **1** structural anomaly (a duplicate-member row, see below).
- **Mayor is a voter:** present in the aye/nay lists every year (Brunst 2020–21, Young
  2022–25, McCandless 2026). Confirmed.
- **Roster = 7 every year** after name normalization (see defect #2/#3 below — raw data shows
  a phantom "8th member" in 2022/2024/2025 caused by mis-spelled names, not extra people).
- **Provenance spot-check (8 random motions, incl. OCR'd 2023/2024/2026):** all 8 match the
  source minutes' "Those voting" clauses exactly — e.g. 2023-08-01 #4 (7-0), 2022-01-25 #7
  (Amber Pope appointment), 2024-05-14 #10 (SSLD resolution), 2026-02-24 #2 (consent),
  2020-08-11 #3 (Sunset Heights). **No fabricated members, dates, motions, or votes found.**
- **Every year has votes** (2020: 557, 2021: 401, 2022: 868, 2023: 615, 2024: 576, 2025: 528,
  2026: 191) — no whole year is missing roll-calls.

**The 4 defects (all on OCR'd files; all DROP/mangle real votes, none invents):**
1. **`2026-03-10` motion 4 recorded as `0-3 Pass`** — the source says *"Those voting yes:.
   Karen McCandless, Chris Killpack, Jenn Gale and Quinn Mecham. Those voting no: LaNae
   Millett, Crystal Muhlestein and Jeff Lambson"* → should be **4-3 Pass**. The OCR artifact
   `Those voting yes:.` (stray period) broke the aye-list parse, so **all 4 aye votes were
   silently dropped**. The 3 recorded nays are correct.
2. **`2024-12-10` motion 4 has duplicate members** (Spencer & Millett each appear as both
   Aye and Nay). The source has **two consecutive motions** on the same PD54/22-5-3 zoning
   item (a 3-4 Fail then a 5-2 Pass); the parser **merged them into one** motion, conflating
   the two roll-calls. The split is mishandled on this OCR file.
3. **`Tom Macdonals`** (10 rows, 2024-02 → 2024-03) — OCR typo of **Tom Macdonald** not caught
   by the `CANON` normalizer.
4. **`Jenn'gale`** (1 row, 2025-03-25) — OCR mangling of **Jenn Gale**; and **`Mr`** (1 row,
   2022-10-11) — the parser captured the title from *"Those voting nay: Mr. Macdonald"* as the
   surname instead of resolving it to **Tom Macdonald**.
- Net impact: ~17 of 3,736 rows wrong, plus 4 dropped aye votes on the 2026-03-10 motion.
  All correctable by extending `CANON` / fixing the `Those voting yes:.` and dual-motion
  regexes, then re-running `extract_votes.py`. **None is fabrication** — every wrong value
  traces to a real member under a bad spelling or a real motion mis-split.

### Genuine comments — PASS
- **95 rows**, all `source=minutes_attached_written`, all 2020 (54) / 2021 (41), 9 distinct
  meeting dates within the stated 2020-07-14 → 2021-03-23 window. `date_normalized` 100%
  populated.
- **Spot-check (4 random):** Jason Dodge (2020-07-14), Annya Becerra (2021-02-23), Erik
  Schaumann (2021-02-09), Jason Gifford (2020-07-14) — all 4 found verbatim in their cited
  source minutes (the Schaumann text is correctly re-stitched across a page-footer break, as
  documented).
- **No in-person paraphrase leaked:** scanned for clerk-paraphrase markers; the only 2 hits
  are residents quoting "stated" inside their own first-person letters (false positives).
  58/95 open in first person — consistent with genuine submitted letters.
- `all_comments_dropped.csv` = 4 rows (developers/agents in business capacity), each with a
  `_drop_reason`. Audit trail intact.

### Speaker log — PASS
- **121 rows** (csv-module, excluding the `#` header note). Brief says 122 / public_comments
  CLAUDE.md says 60 — the CLAUDE.md is stale; 121 is the on-disk reality and is in line with
  the brief's "~122." Header note *"MEETING-RECORD NOTES, NOT public-submitted comments"* is
  present. Correctly kept separate from the clean CSV. Known 2022–26 undercount is documented.

### Elections — PASS (external cross-check, 0 mismatches)
- **11 races / 75 candidate rows / 2,063 precinct rows** (precinct detail for 2021 + 2025
  only; 2019 + 2023 citywide-only — documented PDF-rollup gap).
- Elected roster implied by the winners **matches who casts votes** in `all_votes.csv` for
  every year (after normalizing Millet/Millett, Macdonald, Jenn Gale). Cohort stagger checks
  out (2017/2019/2021/2023/2025 cohorts seat the right people each year).
- See race-by-race table below.

### Geo — PASS
- 1 city-limits MultiPolygon (`NAME=Orem`, Utah County). 57 precincts `25OR01…25OR59`
  (documented gaps at 55/56). Offline lat/lon tool: Orem center (40.2969, -111.6946) →
  **INSIDE** (precinct 25OR30); Provo (40.2338, -111.6585) → **OUTSIDE**. At-large / no
  districts correctly modeled (no fabricated district map).

### Weeks — PASS
- `python3 build_weeks.py` regenerates **128 bundles** with no error. No iCloud conflict-copies
  found anywhere in the repo. Reported breakdown: 9 comment-weeks, 125 vote-weeks, 128
  minutes-weeks.
- **Bundle reconciliation:** `weeks/2025-01-14/votes.csv` = 35 rows == canonical filtered to
  2025-01-14 (35). `weeks/2020-07-14/comments.csv` = 39 == canonical 2020-07-14 comments (39).

---

## External election cross-check (race-by-race)

| Year | Office | Repo winners (certified totals) | External source | Match |
|---|---|---|---|---|
| 2019 | Council (vote-for-3) | Peterson 9,858 · Lambson 7,995 · Lauret 6,740 | KSL / Deseret News (2019 official), Ballotpedia | ✅ exact |
| 2021 | Mayor | David A. Young 9,647 (def. Jim Evans 6,688) | Utah County 2021 General PDF, Ballotpedia | ✅ exact |
| 2021 | Council (vote-for-3) | Millett 11,482 · Spencer 10,444 · Macdonald 7,672 | Utah County 2021 General results | ✅ exact |
| 2023 | Council (vote-for-3) | Lambson 9,098 · Gale 8,606 · Killpack 8,457 | Daily Herald ("Lambson, Gale, Killpack lead…") + KSL | ✅ exact |
| 2025 | Mayor | Karen McCandless 9,574 (def. Dave Young 9,056) | Daily Herald (certified) + KSL; Ballotpedia lists McCandless as mayor | ✅ winner + certified totals match |
| 2025 | Council (vote-for-3) | Mecham 9,474 · Muhlestein 9,102 · Millett 9,077 | Daily Herald (certified) + electionresults.utah.gov | ✅ exact |

- **6 general-election contests checked, 0 mismatches.** (Primaries not externally re-checked
  individually; they are county-source-derived and the generals — the seating events — all
  verify.)
- **2025 night-vs-certified caveat (documented & handled correctly):** election-NIGHT
  unofficial tallies had Mortimer/Moulton ahead of Millett/Spencer; the repo correctly uses
  the **certified county SOVC** that seats Muhlestein & Millett. The Daily Herald's
  early-tally numbers (8,078 / 7,467 for mayor) differ from the certified 9,574 / 9,056 — the
  repo uses certified, which is the correct choice.

---

## Gaps & recommendations

1. **FIX the 4 OCR-parse vote defects** (votes = PARTIAL until done):
   - Add `Macdonals→Tom Macdonald` and `Jenn'gale→Jenn Gale` to `CANON` in `extract_votes.py`.
   - Handle `Those voting nay: Mr. Macdonald` (title-only short form) so it resolves to the
     surname (the `Mr` row).
   - Handle the `Those voting yes:.` (trailing-punctuation) OCR variant so 2026-03-10 motion 4
     captures its 4 ayes → `4-3 Pass`.
   - Split the dual-motion block on 2024-12-10 (PD54/22-5-3) so the 3-4 Fail and 5-2 Pass are
     separate motions, removing the duplicate-member rows.
   - Re-run `extract_votes.py` and `build_weeks.py`.
2. **Update stale CLAUDE.md counts:** `meeting_minutes/CLAUDE.md` still reports the pre-OCR
   numbers (255 motions / 1703 rows / 68 stubs). `public_comments/CLAUDE.md` says "60"
   speaker-log rows (actual: 121). These docs should be refreshed to match the on-disk data.
3. **Comment `source_file` paths are absolute** (`/Users/tysonwelsh/Desktop/...`) in
   `all_comments_clean.csv`, unlike the repo-relative `source` in `all_votes.csv`. Minor
   portability nit; consider normalizing to repo-relative.
   *RESOLVED 2026-07-02 (REMEDIATION_PLAN 3.4):* the stale absolute prefix was stripped
   from `all_comments_clean.csv` (95 rows), `all_comments_dropped.csv`,
   `minutes_speaker_log.csv`, and the 9 `weeks/*/comments.csv` copies — `source_file` is
   now repo-relative (`meeting_minutes/minutes/...`); all referenced files verified on
   disk. Originals in `_backups/2026-07-02/`.
4. **Documented gaps confirmed legitimate, not retrieval failures:** Apr–Jun 2021 minutes
   (predate both sources), 2019/2023 election precinct data (county published PDF rollups
   only), and the speaker-log 2022–26 undercount. 2024-Nov / 2025-Oct single-month minutes
   absences were not independently confirmed as "no meeting held" — low priority but worth a
   one-line note.

---

## Verdict

**No fabrication.** Every spot-checked vote, comment, and election winner traces to a real
source and matches it; all derived counts (3,736 votes / 565 motions / 95 comments / 121
speaker notes / 11 races / 128 weeks) reconcile; all 6 general-election winners are confirmed
against independent outside sources with zero mismatches; the at-large roster of 7 (Mayor
included) holds every year. The repo is **PARTIAL overall** solely because the vote extractor
has 4 small OCR-related parse defects that drop/mangle ~0.45% of vote rows (correctable by a
parser fix + re-run), and two CLAUDE.md docs carry stale pre-OCR counts.

```json
{"overall":"PARTIAL","by_dataset":{"minutes":"PASS","votes":"PARTIAL","genuine_comments":"PASS","speaker_log":"PASS","elections":"PASS","geo":"PASS","weeks":"PASS"},"fabrication_found":false,"election_crosscheck":{"races_checked":6,"mismatches":[]},"key_findings":["3,736 vote rows / 565 motions / 48 contested all tally-consistent; 8 random motions (incl OCR'd 2023/2024/2026) verified verbatim to source — no fabrication","All 130 minutes have real body text incl. all 68 OCR files (min 3.7KB) — zero header-only stubs remain","4 OCR-parse defects in votes: 2026-03-10 #4 dropped 4 ayes (recorded 0-3 instead of 4-3); 2024-12-10 #4 merged two motions causing duplicate-member rows; 'Tom Macdonals'(10), 'Jenn'gale'(1), 'Mr'(1) un-normalized OCR names — all real members/motions, none fabricated","Mayor votes every year; roster = exactly 7 each year after name normalization; matches elected cohorts","All 6 general-election winners externally confirmed (Daily Herald/KSL/Ballotpedia/Utah County certified) with 0 mismatches; certified-vs-election-night 2025 handled correctly","95 genuine comments all minutes_attached_written 2020-21, 4 spot-checked verbatim, no in-person paraphrase leak; speaker log (121) correctly separated","Weeks regenerate clean (128 bundles, no conflict-copies); spot-checked bundles reconcile to canonical exactly","meeting_minutes/CLAUDE.md (255 motions/1703 rows/68 stubs) and public_comments/CLAUDE.md (60 speaker rows) carry STALE pre-OCR counts"],"gaps":["Apr–Jun 2021 minutes absent (documented; predate both sources)","2019 & 2023 election precinct data PDF-rollup only (documented; citywide totals complete & externally verified)","2024-Nov and 2025-Oct single-month minutes absences not independently confirmed as no-meeting months","comment source_file paths are absolute not repo-relative (portability nit)"]}
```

**2026-07-02 (3.1) council-vote validation:** shared validator installed as `meeting_minutes/validate_votes.py` and run — 3,749 rows / 566 motions (all named); 0 schema/date/vocab defects, 0 malformed groups, 0 double votes; tally-vs-counted 566/566; 0 unexplained mismatches.
